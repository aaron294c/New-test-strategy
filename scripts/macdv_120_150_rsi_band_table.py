#!/usr/bin/env python3
"""
Generate a per-ticker table for MACD-V in [120,150) split by RSI-MA percentile bands.

Bands requested:
  <5, 5-10, 10-15, 15-20, 20-30, 30-40, 40-50

Metrics per cell:
  n, win%, mean%, median% at a fixed forward horizon (default D7), close-to-close.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "backend"))

from macdv_calculator import MACDVCalculator  # noqa: E402
from ticker_utils import resolve_yahoo_symbol  # noqa: E402


DEFAULT_TICKERS = ["AAPL", "NVDA", "GOOGL", "MSFT", "META", "QQQ", "SPY", "BRK-B", "AMZN"]
RSI_BANDS: List[Tuple[float, float, str]] = [
    (0, 5, "<5"),
    (5, 10, "5-10"),
    (10, 15, "10-15"),
    (15, 20, "15-20"),
    (20, 30, "20-30"),
    (30, 40, "30-40"),
    (40, 50, "40-50"),
    (50, 60, "50-60"),
    (60, 70, "60-70"),
    (70, 80, "70-80"),
    (80, 90, "80-90"),
    (90, 100, "90-100"),
]


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


@dataclass(frozen=True)
class Stats:
    n: int
    win: float
    mean: float
    median: float


def _stats(returns: List[float]) -> Stats:
    if not returns:
        return Stats(n=0, win=float("nan"), mean=float("nan"), median=float("nan"))
    arr = np.asarray(returns, dtype=float)
    return Stats(
        n=int(arr.size),
        win=float((arr > 0).mean() * 100),
        mean=float(arr.mean()),
        median=float(np.median(arr)),
    )


def forward_returns(df: pd.DataFrame, entry: pd.Series, horizon: int) -> List[float]:
    closes = df["Close"].to_numpy(dtype=float)
    idxs = np.flatnonzero(entry.to_numpy(dtype=bool))
    out: List[float] = []
    n = len(df)
    for i in idxs:
        j = i + horizon
        if j >= n:
            continue
        entry_price = closes[i]
        if not np.isfinite(entry_price) or entry_price <= 0:
            continue
        out.append(float((closes[j] / entry_price - 1.0) * 100.0))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", default=",".join(DEFAULT_TICKERS))
    ap.add_argument("--period", default="10y")
    ap.add_argument("--pct-lookback", type=int, default=252)
    ap.add_argument("--horizon", type=int, default=7)
    ap.add_argument("--out", default="docs/MACDV_120_150_RSI_BANDS_TABLE_D7.md")
    args = ap.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]

    per_ticker: Dict[str, Dict[str, Stats]] = {t: {} for t in tickers}
    aggregate_returns: Dict[str, List[float]] = {label: [] for _, _, label in RSI_BANDS}

    for t in tickers:
        yahoo = resolve_yahoo_symbol(t)
        df = _download_daily_ohlc(yahoo, period=args.period)
        macdv_val = calculate_macdv_val(df)
        rsi_pct = calculate_rsi_ma_percentile(df["Close"], percentile_lookback=args.pct_lookback)

        work = df.copy()
        work["macdv_val"] = macdv_val
        work["rsi_pct"] = rsi_pct
        work = work.dropna(subset=["macdv_val", "rsi_pct", "Close"]).copy()

        in_macd = (work["macdv_val"] >= 120) & (work["macdv_val"] < 150)

        for rlo, rhi, label in RSI_BANDS:
            in_band = (work["rsi_pct"] >= rlo) & (work["rsi_pct"] < rhi)
            entry = (in_macd & in_band).fillna(False)
            rets = forward_returns(work, entry, args.horizon)
            per_ticker[t][label] = _stats(rets)
            aggregate_returns[label].extend(rets)

    # Build markdown table
    band_labels = [b[2] for b in RSI_BANDS]
    headers = ["ticker"] + band_labels
    lines: List[str] = []
    lines.append("# MACD-V 120–150 × RSI-MA Percentile Bands (D7)")
    lines.append("")
    lines.append(f"Run date: 2026-01-28")
    lines.append("")
    lines.append("All results are close-to-close forward returns at D7.")
    lines.append("")
    lines.append("## Summary (Aggregate)")
    lines.append("This checks whether performance degrades when RSI-MA percentile is above 50 within MACD-V 120–150.")
    lines.append("")
    agg_stats = {label: _stats(aggregate_returns[label]) for label in band_labels}
    below_50 = sum((aggregate_returns[lbl] for lbl in band_labels if lbl in {"<5","5-10","10-15","15-20","20-30","30-40","40-50"}), [])
    at_or_above_50 = sum((aggregate_returns[lbl] for lbl in band_labels if lbl in {"50-60","60-70","70-80","80-90","90-100"}), [])
    s_lo = _stats(below_50)
    s_hi = _stats(at_or_above_50)
    lines.append(f"- RSI<50 (all bands below 50): n={s_lo.n}, win={s_lo.win:.1f}%, mean={s_lo.mean:.2f}%, median={s_lo.median:.2f}%")
    lines.append(f"- RSI≥50 (bands 50-100): n={s_hi.n}, win={s_hi.win:.1f}%, mean={s_hi.mean:.2f}%, median={s_hi.median:.2f}%")
    lines.append("")
    lines.append("Interpretation: if RSI≥50 shows lower win/mean than RSI<50 here, you're likely paying for less 'pullback' (more mixed follow-through / mean reversion). This is an observation, not proof of causality.")
    lines.append("")

    def add_table(title: str, cell_fn) -> None:
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        # Aggregate row first
        agg_row = ["ALL"]
        for label in band_labels:
            agg_row.append(cell_fn(agg_stats[label]))
        lines.append("| " + " | ".join(agg_row) + " |")
        for t in tickers:
            row = [t]
            for label in band_labels:
                row.append(cell_fn(per_ticker[t][label]))
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")

    add_table("Sample Size (n)", lambda s: str(s.n))
    add_table("Win Rate (%)", lambda s: "—" if s.n == 0 else f"{s.win:.1f}")
    add_table("Mean Return (%)", lambda s: "—" if s.n == 0 else f"{s.mean:.2f}")
    add_table("Median Return (%)", lambda s: "—" if s.n == 0 else f"{s.median:.2f}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
