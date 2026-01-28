#!/usr/bin/env python3
"""
Backtest two MACD-V + RSI-MA percentile strategies on daily data.

Strategies (long-only):
1) Pullback-in-trend:
   Entry: macdv_trend == 'Bullish' AND rsi_pct <= 15
   Exit:  rsi_pct >= 50 OR macdv_trend in {'Neutral', 'Ranging'}
2) Range reversion:
   Entry: macdv_trend == 'Ranging' AND rsi_pct <= 5
   Exit:  rsi_pct >= 75

For each entry event, compute realized return with a horizon cap at D3/D7/D14/D21:
exit_day = min(first_exit_signal_day, entry_day + horizon)
return = (Close[exit_day] / Close[entry_day]) - 1

Notes:
- Assumes signals and fills at the same day's Close (close-to-close).
- Uses the repo's MACD-V implementation (ATR-normalized MACD) and the website's
  RSI-MA definition (RSI on delta of log returns, then EMA smoothing).
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "backend"))

from macdv_calculator import MACDVCalculator  # noqa: E402
from ticker_utils import resolve_yahoo_symbol  # noqa: E402


HORIZONS = [3, 7, 14, 21]


def _ensure_yfinance_cache_dir() -> None:
    cache_dir = Path(os.getenv("YFINANCE_CACHE_DIR") or (Path(os.getenv("TMPDIR", "/tmp")) / "py-yfinance"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    try:
        yf.set_tz_cache_location(str(cache_dir))
    except Exception:
        pass


def _download_daily_ohlc(symbol: str, period: str = "10y") -> pd.DataFrame:
    _ensure_yfinance_cache_dir()

    df = yf.download(
        symbol,
        period=period,
        interval="1d",
        progress=False,
        auto_adjust=True,
        group_by="column",
        threads=False,
    )

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]

    df = df.rename(columns={c: c.strip() for c in df.columns})
    required = {"Open", "High", "Low", "Close"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"{symbol}: missing columns {sorted(missing)}")

    df = df.dropna(subset=["Open", "High", "Low", "Close"]).copy()
    if df.empty:
        raise RuntimeError(f"{symbol}: no rows returned (network blocked or ticker invalid)")

    return df


def calculate_rsi_ma_and_percentile(
    close: pd.Series,
    rsi_length: int = 14,
    ma_length: int = 14,
    percentile_lookback: int = 252,
) -> Tuple[pd.Series, pd.Series]:
    # Step 1: log returns
    log_returns = np.log(close / close.shift(1)).fillna(0)

    # Step 2: change of returns (second derivative)
    delta = log_returns.diff()

    # Step 3: RSI on delta (Wilder)
    gains = delta.where(delta > 0, 0.0)
    losses = -delta.where(delta < 0, 0.0)
    avg_gains = gains.ewm(alpha=1 / rsi_length, adjust=False).mean()
    avg_losses = losses.ewm(alpha=1 / rsi_length, adjust=False).mean()
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(50)

    # Step 4: EMA smoothing
    rsi_ma = rsi.ewm(span=ma_length, adjust=False).mean()

    # Rolling percentile rank of RSI-MA (0..100)
    def rolling_percentile_rank(window: pd.Series) -> float:
        current_value = window.iloc[-1]
        below_count = (window.iloc[:-1] < current_value).sum()
        return (below_count / (len(window) - 1)) * 100

    rsi_pct = rsi_ma.rolling(window=percentile_lookback, min_periods=percentile_lookback).apply(
        rolling_percentile_rank, raw=False
    )

    return rsi_ma, rsi_pct


def calculate_macdv_trend(daily_ohlc: pd.DataFrame) -> pd.Series:
    df = daily_ohlc.rename(
        columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}
    ).copy()

    calc = MACDVCalculator()
    out = calc.calculate_macdv(df, source_col="close")
    return out["macdv_trend"]


@dataclass(frozen=True)
class HorizonStats:
    trades: int
    mean_return_pct: float
    median_return_pct: float
    win_rate_pct: float


def _compute_stats(returns_pct: List[float]) -> HorizonStats:
    if not returns_pct:
        return HorizonStats(trades=0, mean_return_pct=float("nan"), median_return_pct=float("nan"), win_rate_pct=float("nan"))

    arr = np.array(returns_pct, dtype=float)
    return HorizonStats(
        trades=int(arr.size),
        mean_return_pct=float(np.mean(arr)),
        median_return_pct=float(np.median(arr)),
        win_rate_pct=float(np.mean(arr > 0) * 100),
    )


def backtest_event_style(
    df: pd.DataFrame,
    entry_condition: Callable[[pd.DataFrame, int], bool],
    exit_condition: Callable[[pd.DataFrame, int], bool],
    horizons: Iterable[int],
) -> Dict[int, List[float]]:
    closes = df["Close"].to_numpy(dtype=float)
    out: Dict[int, List[float]] = {h: [] for h in horizons}

    n = len(df)
    for entry_idx in range(n):
        if not entry_condition(df, entry_idx):
            continue

        entry_price = closes[entry_idx]
        if not np.isfinite(entry_price) or entry_price <= 0:
            continue

        for h in horizons:
            max_exit_idx = entry_idx + h
            if max_exit_idx >= n:
                continue

            chosen_exit_idx = max_exit_idx
            for i in range(entry_idx + 1, max_exit_idx + 1):
                if exit_condition(df, i):
                    chosen_exit_idx = i
                    break

            exit_price = closes[chosen_exit_idx]
            ret = (exit_price / entry_price - 1.0) * 100.0
            out[h].append(float(ret))

    return out


def main() -> None:
    tickers = ["AAPL", "NVDA", "GOOGL", "MSFT", "META", "QQQ", "SPY", "BRK-B", "AMZN"]

    pullback_returns: Dict[str, Dict[int, List[float]]] = {}
    range_returns: Dict[str, Dict[int, List[float]]] = {}

    for t in tickers:
        yahoo = resolve_yahoo_symbol(t)
        df = _download_daily_ohlc(yahoo, period="10y")

        macdv_trend = calculate_macdv_trend(df)
        rsi_ma, rsi_pct = calculate_rsi_ma_and_percentile(df["Close"], percentile_lookback=252)

        work = df.copy()
        work["macdv_trend"] = macdv_trend
        work["rsi_ma"] = rsi_ma
        work["rsi_pct"] = rsi_pct

        # Drop rows before percentiles are available
        work = work.dropna(subset=["macdv_trend", "rsi_pct", "Close"]).copy()
        work.reset_index(drop=True, inplace=True)

        def pullback_entry(d: pd.DataFrame, i: int) -> bool:
            return d.at[i, "macdv_trend"] == "Bullish" and float(d.at[i, "rsi_pct"]) <= 15.0

        def pullback_exit(d: pd.DataFrame, i: int) -> bool:
            return float(d.at[i, "rsi_pct"]) >= 50.0 or d.at[i, "macdv_trend"] in {"Neutral", "Ranging"}

        def range_entry(d: pd.DataFrame, i: int) -> bool:
            return d.at[i, "macdv_trend"] == "Ranging" and float(d.at[i, "rsi_pct"]) <= 5.0

        def range_exit(d: pd.DataFrame, i: int) -> bool:
            return float(d.at[i, "rsi_pct"]) >= 75.0

        pullback_returns[t] = backtest_event_style(work, pullback_entry, pullback_exit, HORIZONS)

        range_returns[t] = backtest_event_style(work, range_entry, range_exit, HORIZONS)

    def print_table(title: str, returns: Dict[str, Dict[int, List[float]]]) -> None:
        print("\n" + title)
        print("ticker, horizon, trades, mean%, median%, win_rate%")
        for ticker in returns:
            for h in HORIZONS:
                s = _compute_stats(returns[ticker][h])
                print(f"{ticker}, D{h}, {s.trades}, {s.mean_return_pct:.3f}, {s.median_return_pct:.3f}, {s.win_rate_pct:.1f}")

        # Aggregate across all tickers (signal-weighted)
        print("\naggregate (signal-weighted)")
        for h in HORIZONS:
            all_returns: List[float] = []
            for ticker in returns:
                all_returns.extend(returns[ticker][h])
            s = _compute_stats(all_returns)
            print(f"ALL, D{h}, {s.trades}, {s.mean_return_pct:.3f}, {s.median_return_pct:.3f}, {s.win_rate_pct:.1f}")

    print_table("Pullback-in-trend (Bullish + RSI<=15; exit RSI>=50 or macdv!=Bullish)", pullback_returns)
    print_table("Range reversion (Ranging + RSI<=5; exit RSI>=75)", range_returns)


if __name__ == "__main__":
    main()
