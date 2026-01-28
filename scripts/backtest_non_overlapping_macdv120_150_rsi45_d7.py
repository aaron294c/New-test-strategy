#!/usr/bin/env python3
"""
Non-overlapping backtest for the exact rule:

  Entry (long): MACD-V in [120,150) AND RSI-MA percentile <= 45
  Exit: fixed horizon D7 (close-to-close)

"Non-overlapping" means: once an entry triggers, we ignore any further entry
signals for that ticker until the trade has exited (7 trading days later).

Data: daily OHLC via yfinance (auto_adjust=True).
Indicators:
- MACD-V from repo implementation (ATR-normalized MACD).
- RSI-MA percentile per repo website definition: RSI(14 Wilder) on diff(log returns),
  then EMA(14), then rolling percentile rank with lookback (default 252).
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "backend"))

from macdv_calculator import MACDVCalculator  # noqa: E402
from ticker_utils import resolve_yahoo_symbol  # noqa: E402


DEFAULT_TICKERS = ["AAPL", "NVDA", "GOOGL", "MSFT", "META", "QQQ", "SPY", "BRK-B", "AMZN"]


def _ensure_yfinance_cache_dir() -> None:
    cache_dir = Path(os.getenv("YFINANCE_CACHE_DIR") or (Path(os.getenv("TMPDIR", "/tmp")) / "py-yfinance"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    try:
        yf.set_tz_cache_location(str(cache_dir))
    except Exception:
        pass


def _download_daily_ohlc(symbol: str, period: str) -> pd.DataFrame:
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
    df = df.dropna(subset=["Open", "High", "Low", "Close"]).copy()
    if df.empty:
        raise RuntimeError(f"{symbol}: no rows returned (network blocked or ticker invalid)")
    return df


def calculate_rsi_ma_percentile(close: pd.Series, percentile_lookback: int = 252) -> pd.Series:
    log_returns = np.log(close / close.shift(1)).fillna(0)
    delta = log_returns.diff()

    gains = delta.where(delta > 0, 0.0)
    losses = -delta.where(delta < 0, 0.0)
    avg_gains = gains.ewm(alpha=1 / 14, adjust=False).mean()
    avg_losses = losses.ewm(alpha=1 / 14, adjust=False).mean()
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(50)

    rsi_ma = rsi.ewm(span=14, adjust=False).mean()

    def rolling_percentile_rank(window: pd.Series) -> float:
        current_value = window.iloc[-1]
        below_count = (window.iloc[:-1] < current_value).sum()
        return (below_count / (len(window) - 1)) * 100

    return rsi_ma.rolling(window=percentile_lookback, min_periods=percentile_lookback).apply(
        rolling_percentile_rank, raw=False
    )


def calculate_macdv_val(daily_ohlc: pd.DataFrame) -> pd.Series:
    df = daily_ohlc.rename(
        columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}
    ).copy()
    calc = MACDVCalculator()
    out = calc.calculate_macdv(df, source_col="close")
    return out["macdv_val"]


def non_overlapping_entries(signal: np.ndarray, horizon: int) -> List[int]:
    """
    Return entry indices for non-overlapping trades with fixed holding horizon.
    If you enter at i, next entry can be at i + horizon + 1 at earliest.
    """
    idxs: List[int] = []
    i = 0
    n = int(signal.size)
    while i < n:
        if signal[i]:
            idxs.append(i)
            i += horizon + 1
        else:
            i += 1
    return idxs


@dataclass(frozen=True)
class Stats:
    trades: int
    win_rate: float
    mean: float
    median: float


def _stats(returns: List[float]) -> Stats:
    if not returns:
        return Stats(trades=0, win_rate=float("nan"), mean=float("nan"), median=float("nan"))
    arr = np.asarray(returns, dtype=float)
    return Stats(
        trades=int(arr.size),
        win_rate=float((arr > 0).mean() * 100),
        mean=float(arr.mean()),
        median=float(np.median(arr)),
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", default=",".join(DEFAULT_TICKERS))
    ap.add_argument("--period", default="10y")
    ap.add_argument("--pct-lookback", type=int, default=252)
    ap.add_argument("--horizon", type=int, default=7)
    ap.add_argument("--out", default="docs/NON_OVERLAP_MACDV120_150_RSI45_D7.md")
    args = ap.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    horizon = int(args.horizon)

    per_ticker: Dict[str, Stats] = {}
    all_returns: List[float] = []

    for t in tickers:
        yahoo = resolve_yahoo_symbol(t)
        df = _download_daily_ohlc(yahoo, period=args.period)
        macdv_val = calculate_macdv_val(df)
        rsi_pct = calculate_rsi_ma_percentile(df["Close"], percentile_lookback=args.pct_lookback)

        work = df.copy()
        work["macdv_val"] = macdv_val
        work["rsi_pct"] = rsi_pct
        work = work.dropna(subset=["macdv_val", "rsi_pct", "Close"]).copy()
        work.reset_index(drop=True, inplace=True)

        sig = (work["macdv_val"] >= 120) & (work["macdv_val"] < 150) & (work["rsi_pct"] <= 45)
        sig = sig.fillna(False).to_numpy(dtype=bool)

        closes = work["Close"].to_numpy(dtype=float)
        entries = non_overlapping_entries(sig, horizon=horizon)

        rets: List[float] = []
        for i in entries:
            j = i + horizon
            if j >= len(closes):
                continue
            entry_px = closes[i]
            exit_px = closes[j]
            rets.append(float((exit_px / entry_px - 1.0) * 100.0))

        per_ticker[t] = _stats(rets)
        all_returns.extend(rets)

    agg = _stats(all_returns)

    lines: List[str] = []
    lines.append("# Non-Overlapping Backtest: MACD-V 120–150 & RSI%≤45 (D7)")
    lines.append("")
    lines.append(f"Run date: 2026-01-28")
    lines.append("")
    lines.append("## What 'non-overlapping' means")
    lines.append("- One active trade at a time per ticker.")
    lines.append(f"- If a signal triggers on day t, you enter at that close and exit at close t+{horizon}.")
    lines.append("- Any additional signals during the holding window are ignored.")
    lines.append("")
    lines.append("## Results")
    lines.append("Cell format: trades | win% | mean% | median%")
    lines.append("")
    lines.append("| ticker | trades | win% | mean% | median% |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    lines.append(f"| ALL | {agg.trades} | {agg.win_rate:.1f} | {agg.mean:.2f} | {agg.median:.2f} |")
    for t in tickers:
        s = per_ticker[t]
        lines.append(f"| {t} | {s.trades} | {s.win_rate:.1f} | {s.mean:.2f} | {s.median:.2f} |")
    lines.append("")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

