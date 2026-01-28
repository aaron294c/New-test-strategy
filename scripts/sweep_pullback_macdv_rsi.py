#!/usr/bin/env python3
"""
Parameter sweep for the Pullback-in-trend idea using MACD-V + RSI-MA percentiles.

This follows the "percentile mapping tab" style more closely:
- Entry defines a conditional sample set.
- Forward returns are measured at fixed horizons (D3/D7/D14/D21) from entry day close to close.
- No dynamic exits here (separate from trade simulation).

Entry (base):
  macdv_val >= macdv_min (default 50)  AND  rsi_pct <= rsi_entry_max

Optional filters:
  - rsi_cross: only count first day crossing below threshold
  - hist_negative: require macdv_hist < 0 at entry (pullback vs signal)
  - hist_rising: require macdv_hist > macdv_hist[t-1] at entry (pullback ending)
  - not_risk: exclude macdv_color == 'blue' (|macdv|>=150 extreme)

Outputs:
- Aggregate (signal-weighted) win rate and mean/median return at D3/D7/D14/D21
- Per-ticker stats for the best parameter sets
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

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


def calculate_rsi_ma_and_percentile(
    close: pd.Series,
    rsi_length: int = 14,
    ma_length: int = 14,
    percentile_lookback: int = 252,
) -> Tuple[pd.Series, pd.Series]:
    log_returns = np.log(close / close.shift(1)).fillna(0)
    delta = log_returns.diff()

    gains = delta.where(delta > 0, 0.0)
    losses = -delta.where(delta < 0, 0.0)
    avg_gains = gains.ewm(alpha=1 / rsi_length, adjust=False).mean()
    avg_losses = losses.ewm(alpha=1 / rsi_length, adjust=False).mean()
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(50)

    rsi_ma = rsi.ewm(span=ma_length, adjust=False).mean()

    def rolling_percentile_rank(window: pd.Series) -> float:
        current_value = window.iloc[-1]
        below_count = (window.iloc[:-1] < current_value).sum()
        return (below_count / (len(window) - 1)) * 100

    rsi_pct = rsi_ma.rolling(window=percentile_lookback, min_periods=percentile_lookback).apply(
        rolling_percentile_rank, raw=False
    )

    return rsi_ma, rsi_pct


def calculate_macdv(daily_ohlc: pd.DataFrame) -> pd.DataFrame:
    df = daily_ohlc.rename(
        columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}
    ).copy()
    calc = MACDVCalculator()
    out = calc.calculate_macdv(df, source_col="close")
    return out[["macdv_val", "macdv_signal", "macdv_hist", "macdv_color", "macdv_trend"]]


@dataclass(frozen=True)
class Stats:
    n: int
    mean: float
    median: float
    win_rate: float


def _stats(returns: List[float]) -> Stats:
    if not returns:
        return Stats(n=0, mean=float("nan"), median=float("nan"), win_rate=float("nan"))
    arr = np.asarray(returns, dtype=float)
    return Stats(
        n=int(arr.size),
        mean=float(arr.mean()),
        median=float(np.median(arr)),
        win_rate=float((arr > 0).mean() * 100),
    )


def forward_returns_from_entries(df: pd.DataFrame, entry_mask: pd.Series, horizons: Iterable[int]) -> Dict[int, List[float]]:
    closes = df["Close"].to_numpy(dtype=float)
    idxs = np.flatnonzero(entry_mask.to_numpy(dtype=bool))
    out: Dict[int, List[float]] = {h: [] for h in horizons}

    n = len(df)
    for i in idxs:
        entry_price = closes[i]
        if not np.isfinite(entry_price) or entry_price <= 0:
            continue
        for h in horizons:
            j = i + h
            if j >= n:
                continue
            ret = (closes[j] / entry_price - 1.0) * 100.0
            out[h].append(float(ret))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", default="10y")
    ap.add_argument("--pct-lookback", type=int, default=252)
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--detail", action="store_true", help="Print per-ticker stats for the top row")
    args = ap.parse_args()

    tickers = ["AAPL", "NVDA", "GOOGL", "MSFT", "META", "QQQ", "SPY", "BRK-B", "AMZN"]

    data_by_ticker: Dict[str, pd.DataFrame] = {}
    for t in tickers:
        yahoo = resolve_yahoo_symbol(t)
        df = _download_daily_ohlc(yahoo, period=args.period)
        macdv = calculate_macdv(df)
        rsi_ma, rsi_pct = calculate_rsi_ma_and_percentile(df["Close"], percentile_lookback=args.pct_lookback)

        work = df.copy()
        work = work.join(macdv, how="left")
        work["rsi_ma"] = rsi_ma
        work["rsi_pct"] = rsi_pct
        work = work.dropna(subset=["macdv_val", "macdv_hist", "macdv_color", "rsi_pct", "Close"]).copy()
        data_by_ticker[t] = work

    rsi_entry_thresholds = [5.0, 10.0, 15.0]
    macdv_mins = [50.0, 75.0, 100.0]
    toggles = [
        # (rsi_cross, hist_negative, hist_rising, not_risk)
        (False, False, False, False),
        (True, False, False, False),
        (True, True, False, False),
        (True, True, True, False),
        (True, True, True, True),
        (False, True, True, True),
    ]

    rows = []

    for rsi_thr in rsi_entry_thresholds:
        for macdv_min in macdv_mins:
            for rsi_cross, hist_neg, hist_rise, not_risk in toggles:
                all_forward: Dict[int, List[float]] = {h: [] for h in HORIZONS}
                per_ticker_counts: Dict[str, int] = {}

                for t, df in data_by_ticker.items():
                    entry = df["macdv_val"] >= macdv_min
                    entry &= df["rsi_pct"] <= rsi_thr

                    if rsi_cross:
                        entry &= df["rsi_pct"].shift(1) > rsi_thr
                    if hist_neg:
                        entry &= df["macdv_hist"] < 0
                    if hist_rise:
                        entry &= df["macdv_hist"] > df["macdv_hist"].shift(1)
                    if not_risk:
                        entry &= df["macdv_color"] != "blue"

                    entry = entry.fillna(False)
                    per_ticker_counts[t] = int(entry.sum())

                    fwd = forward_returns_from_entries(df, entry, HORIZONS)
                    for h in HORIZONS:
                        all_forward[h].extend(fwd[h])

                s7 = _stats(all_forward[7])
                s3 = _stats(all_forward[3])
                s14 = _stats(all_forward[14])
                s21 = _stats(all_forward[21])

                rows.append(
                    {
                        "rsi_thr": rsi_thr,
                        "macdv_min": macdv_min,
                        "rsi_cross": rsi_cross,
                        "hist_neg": hist_neg,
                        "hist_rise": hist_rise,
                        "not_risk": not_risk,
                        "D7_n": s7.n,
                        "D7_mean": s7.mean,
                        "D7_median": s7.median,
                        "D7_win": s7.win_rate,
                        "D3_win": s3.win_rate,
                        "D14_win": s14.win_rate,
                        "D21_win": s21.win_rate,
                        "min_ticker_events": min(per_ticker_counts.values()) if per_ticker_counts else 0,
                    }
                )

    result = pd.DataFrame(rows)
    # Prefer higher win-rate, then higher mean return, but keep at least some sample size.
    result = result[result["D7_n"] >= 80].copy()
    result = result.sort_values(["D7_win", "D7_mean"], ascending=[False, False]).head(args.top)

    print(f"pct_lookback={args.pct_lookback} period={args.period}")
    print("Top parameter sets (aggregate, signal-weighted; forward close-to-close returns):")
    print(
        result[
            [
                "rsi_thr",
                "macdv_min",
                "rsi_cross",
                "hist_neg",
                "hist_rise",
                "not_risk",
                "D7_n",
                "D7_mean",
                "D7_median",
                "D7_win",
            ]
        ].to_string(index=False, justify="left", float_format=lambda x: f"{x:.3f}")
    )

    if args.detail and not result.empty:
        top = result.iloc[0].to_dict()
        rsi_thr = float(top["rsi_thr"])
        macdv_min = float(top["macdv_min"])
        rsi_cross = bool(top["rsi_cross"])
        hist_neg = bool(top["hist_neg"])
        hist_rise = bool(top["hist_rise"])
        not_risk = bool(top["not_risk"])

        print("\nPer-ticker for top row:")
        print(
            f"params: rsi_thr<={rsi_thr} macdv_min>={macdv_min} "
            f"rsi_cross={rsi_cross} hist_neg={hist_neg} hist_rise={hist_rise} not_risk={not_risk}"
        )
        print("ticker, horizon, trades, mean%, median%, win_rate%")

        for t, df in data_by_ticker.items():
            entry = df["macdv_val"] >= macdv_min
            entry &= df["rsi_pct"] <= rsi_thr
            if rsi_cross:
                entry &= df["rsi_pct"].shift(1) > rsi_thr
            if hist_neg:
                entry &= df["macdv_hist"] < 0
            if hist_rise:
                entry &= df["macdv_hist"] > df["macdv_hist"].shift(1)
            if not_risk:
                entry &= df["macdv_color"] != "blue"
            entry = entry.fillna(False)

            fwd = forward_returns_from_entries(df, entry, HORIZONS)
            for h in HORIZONS:
                s = _stats(fwd[h])
                print(f"{t}, D{h}, {s.n}, {s.mean:.3f}, {s.median:.3f}, {s.win_rate:.1f}")


if __name__ == "__main__":
    main()
