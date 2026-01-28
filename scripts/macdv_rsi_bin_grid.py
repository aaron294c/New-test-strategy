#!/usr/bin/env python3
"""
MACD-V × RSI-MA percentile bin grid (mapping-style backtest).

Goal: find *more frequent* pullback opportunities by loosening MACD-V strength
and RSI-MA percentile thresholds, and summarize:
- count (n events)
- win rate (% of forward returns > 0)
- mean return (%)
- median return (%)
- frequency (events per ticker-year)

Methodology matches the "Percentile Mapping" style:
- Each signal day is an independent "event" (not 1-position-at-a-time).
- Forward return is close-to-close at a fixed horizon (default D7).

Universe default:
  AAPL, NVDA, GOOGL, MSFT, META, QQQ, SPY, BRK-B, AMZN
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

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
    return out[["macdv_val", "macdv_hist", "macdv_color", "macdv_trend"]]


@dataclass(frozen=True)
class CellStats:
    n: int
    win_rate: float
    mean: float
    median: float
    events_per_ticker_year: float


def _stats(returns: List[float], total_ticker_years: float) -> CellStats:
    if not returns or total_ticker_years <= 0:
        return CellStats(n=0, win_rate=float("nan"), mean=float("nan"), median=float("nan"), events_per_ticker_year=0.0)
    arr = np.asarray(returns, dtype=float)
    return CellStats(
        n=int(arr.size),
        win_rate=float((arr > 0).mean() * 100),
        mean=float(arr.mean()),
        median=float(np.median(arr)),
        events_per_ticker_year=float(arr.size / total_ticker_years),
    )


def forward_returns(df: pd.DataFrame, entry_mask: pd.Series, horizon: int) -> List[float]:
    closes = df["Close"].to_numpy(dtype=float)
    idxs = np.flatnonzero(entry_mask.to_numpy(dtype=bool))
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


def parse_bins(spec: str) -> List[Tuple[float, float]]:
    """
    Example: "50-60,60-70,70-80" -> [(50,60),(60,70),(70,80)]
    """
    bins: List[Tuple[float, float]] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        lo_s, hi_s = part.split("-", 1)
        bins.append((float(lo_s), float(hi_s)))
    return bins

def parse_single_bin(spec: str) -> Tuple[float, float]:
    s = spec.strip()
    if s.endswith("+"):
        lo = float(s[:-1])
        return (lo, 1_000_000.0)
    lo_s, hi_s = s.split("-", 1)
    return (float(lo_s), float(hi_s))

def _bin_contains(bins: Sequence[Tuple[float, float]], target: Tuple[float, float]) -> bool:
    for lo, hi in bins:
        if abs(lo - target[0]) < 1e-9 and abs(hi - target[1]) < 1e-9:
            return True
    return False


def format_grid_markdown(
    bins: Sequence[Tuple[float, float]],
    thresholds: Sequence[float],
    cells: Dict[Tuple[Tuple[float, float], float], CellStats],
    horizon: int,
) -> str:
    headers = ["MACD-V bin"]
    for thr in thresholds:
        headers.append(f"RSI%≤{thr}: n / win / mean / median / evts(ty)")

    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for lo, hi in bins:
        row = [f"{lo:.0f}-{hi:.0f}"]
        for thr in thresholds:
            s = cells[((lo, hi), thr)]
            if s.n == 0:
                row.append("0 / — / — / — / 0.00")
            else:
                row.append(
                    f"{s.n} / {s.win_rate:.1f}% / {s.mean:.2f}% / {s.median:.2f}% / {s.events_per_ticker_year:.2f}"
                )
        lines.append("| " + " | ".join(row) + " |")

    lines.append("")
    lines.append(f"Notes: evts(ty)=events per ticker-year (events / Σ_tickers (bars/252)). Horizon=D{horizon}.")
    return "\n".join(lines)

def format_long_markdown(
    bins: Sequence[Tuple[float, float]],
    thresholds: Sequence[float],
    cells: Dict[Tuple[Tuple[float, float], float], CellStats],
) -> str:
    lines: List[str] = []
    lines.append("| MACD-V bin | RSI% threshold | n | win% | mean% | median% | evts/ticker-year |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for lo, hi in bins:
        bin_label = f"{lo:.0f}-{hi:.0f}" if hi < 1_000_000 else f"{lo:.0f}+"
        for thr in thresholds:
            s = cells[((lo, hi), thr)]
            if s.n == 0:
                lines.append(f"| {bin_label} | ≤{thr:.0f} | 0 | — | — | — | 0.00 |")
            else:
                lines.append(
                    f"| {bin_label} | ≤{thr:.0f} | {s.n} | {s.win_rate:.1f} | {s.mean:.2f} | {s.median:.2f} | {s.events_per_ticker_year:.2f} |"
                )
    return "\n".join(lines)

def _cell_label(bin_lo: float, bin_hi: float, thr: float) -> str:
    hi_label = f"{bin_hi:.0f}" if bin_hi < 1_000_000 else "150+"
    if bin_hi >= 1_000_000:
        return f"MACD-V {bin_lo:.0f}+ & RSI%≤{thr:.0f}"
    return f"MACD-V {bin_lo:.0f}-{hi_label} & RSI%≤{thr:.0f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", default=",".join(DEFAULT_TICKERS))
    ap.add_argument("--period", default="10y")
    ap.add_argument("--pct-lookback", type=int, default=252)
    ap.add_argument("--horizon", type=int, default=7)
    ap.add_argument("--rsi-thresholds", default="5,10,15")
    ap.add_argument("--bins", default="50-60,60-70,70-80,80-90,90-100,100-110,110-120,120-130,130-140,140-150,150-1000000")
    ap.add_argument("--out", default="")
    ap.add_argument("--format", choices=["grid", "long"], default="grid")
    ap.add_argument("--top-cells", type=int, default=8, help="Include top aggregate cells by D7 win-rate/mean")
    ap.add_argument("--min-n", type=int, default=50, help="Minimum aggregate sample size to consider in top-cells ranking")
    ap.add_argument("--per-ticker", action="store_true", help="Include per-ticker best cells")
    ap.add_argument("--min-n-ticker", type=int, default=8, help="Minimum per-ticker sample size for per-ticker best")
    ap.add_argument("--target-evts", type=float, default=0.0, help="Target events per ticker-year (0 disables)")
    ap.add_argument("--target-win", type=float, default=0.0, help="Target win rate percent (0 disables)")
    ap.add_argument("--target-mean", type=float, default=0.0, help="Target mean return percent (0 disables)")
    ap.add_argument("--target-top", type=int, default=12, help="How many closest-to-target rows to show")
    ap.add_argument("--target-min-evts", type=float, default=0.0, help="Minimum events/ticker-year for target shortlist")
    ap.add_argument("--focus-bin", default="", help="If set, print per-ticker stats for this MACD-V bin (e.g. '120-150' or '150+')")
    ap.add_argument("--focus-rsi", type=float, default=0.0, help="If focus-bin set, RSI percentile threshold (e.g. 45 for RSI%<=45)")
    ap.add_argument("--focus-rsi-bands", default="", help="If set, analyze RSI percentile ranges within focus-bin, e.g. '0-10,10-20,50-60,60-70,70-80,80-90,90-100'")
    args = ap.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    thresholds = [float(x.strip()) for x in args.rsi_thresholds.split(",") if x.strip()]
    bins = parse_bins(args.bins)

    data_by_ticker: Dict[str, pd.DataFrame] = {}
    ticker_years: Dict[str, float] = {}

    for t in tickers:
        yahoo = resolve_yahoo_symbol(t)
        df = _download_daily_ohlc(yahoo, period=args.period)
        macdv = calculate_macdv(df)
        _, rsi_pct = calculate_rsi_ma_and_percentile(df["Close"], percentile_lookback=args.pct_lookback)

        work = df.copy()
        work = work.join(macdv, how="left")
        work["rsi_pct"] = rsi_pct
        work = work.dropna(subset=["macdv_val", "rsi_pct", "Close"]).copy()
        data_by_ticker[t] = work
        ticker_years[t] = len(work) / 252.0

    total_ticker_years = float(sum(ticker_years.values()))

    cells: Dict[Tuple[Tuple[float, float], float], CellStats] = {}
    per_ticker_cells: Dict[str, Dict[Tuple[Tuple[float, float], float], CellStats]] = {t: {} for t in tickers}
    for lo, hi in bins:
        for thr in thresholds:
            all_returns: List[float] = []
            for _, df in data_by_ticker.items():
                entry = (df["macdv_val"] >= lo) & (df["macdv_val"] < hi) & (df["rsi_pct"] <= thr)
                entry = entry.fillna(False)
                all_returns.extend(forward_returns(df, entry, args.horizon))
            cells[((lo, hi), thr)] = _stats(all_returns, total_ticker_years)

            for t, df in data_by_ticker.items():
                entry_t = (df["macdv_val"] >= lo) & (df["macdv_val"] < hi) & (df["rsi_pct"] <= thr)
                entry_t = entry_t.fillna(False)
                rets_t = forward_returns(df, entry_t, args.horizon)
                per_ticker_cells[t][((lo, hi), thr)] = _stats(rets_t, ticker_years[t])

    md = []
    md.append("# MACD-V × RSI-MA Percentile Grid (Fixed Forward Returns)")
    md.append("")
    md.append(f"Run date: 2026-01-28")
    md.append("")
    md.append("## Setup")
    md.append(f"- Universe: `{', '.join(tickers)}`")
    md.append(f"- Data: daily OHLC via `yfinance`, period={args.period}")
    md.append(f"- RSI-MA percentile lookback: {args.pct_lookback} bars")
    md.append(f"- Horizon: D{args.horizon} close-to-close forward return")
    md.append(f"- Total ticker-years analyzed (after warmup): {total_ticker_years:.2f}")
    md.append("")
    md.append("## Grid")
    md.append("")
    if args.format == "grid":
        md.append(format_grid_markdown(bins, thresholds, cells, args.horizon))
    else:
        md.append(format_long_markdown(bins, thresholds, cells))
    md.append("")

    if args.top_cells > 0:
        ranked = []
        for (bin_lo, bin_hi), thr in cells:
            s = cells[((bin_lo, bin_hi), thr)]
            if s.n < args.min_n:
                continue
            ranked.append((s.win_rate, s.mean, s.median, s.n, s.events_per_ticker_year, bin_lo, bin_hi, thr))

        ranked.sort(key=lambda x: (x[0], x[1], x[3]), reverse=True)
        md.append("## Best Setups (Aggregate)")
        md.append(f"Ranked by win rate, then mean return. Filter: n ≥ {args.min_n}.")
        md.append("")
        md.append("| setup | n | win% | mean% | median% | evts/ticker-year |")
        md.append("| --- | ---: | ---: | ---: | ---: | ---: |")
        for row in ranked[: args.top_cells]:
            win, mean, median, n, evts_ty, bin_lo, bin_hi, thr = row
            md.append(
                f"| {_cell_label(bin_lo, bin_hi, thr)} | {n} | {win:.1f} | {mean:.2f} | {median:.2f} | {evts_ty:.2f} |"
            )
        md.append("")

    if args.target_evts > 0 and args.target_win > 0 and args.target_mean > 0:
        scored = []
        for (bin_lo, bin_hi), thr in cells:
            s = cells[((bin_lo, bin_hi), thr)]
            if s.n == 0:
                continue
            if args.target_min_evts > 0 and s.events_per_ticker_year < args.target_min_evts:
                continue

            evts_score = abs(s.events_per_ticker_year - args.target_evts) / max(args.target_evts, 1e-9)
            win_score = abs(s.win_rate - args.target_win) / 10.0
            mean_score = abs(s.mean - args.target_mean) / max(args.target_mean, 1e-9)
            score = evts_score + win_score + mean_score
            scored.append((score, s.win_rate, s.mean, s.median, s.n, s.events_per_ticker_year, bin_lo, bin_hi, thr))

        scored.sort(key=lambda x: x[0])
        md.append("## Closest To Target (Aggregate)")
        md.append(
            f"Target: {args.target_evts:.1f} evts/ticker-year, {args.target_win:.1f}% win, {args.target_mean:.2f}% mean. "
            f"Filter: evts/ticker-year ≥ {args.target_min_evts:.2f}."
        )
        md.append("")
        md.append("| setup | score | n | win% | mean% | median% | evts/ticker-year |")
        md.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
        for row in scored[: args.target_top]:
            score, win, mean, median, n, evts_ty, bin_lo, bin_hi, thr = row
            md.append(
                f"| {_cell_label(bin_lo, bin_hi, thr)} | {score:.3f} | {n} | {win:.1f} | {mean:.2f} | {median:.2f} | {evts_ty:.2f} |"
            )
        md.append("")

    if args.per_ticker:
        md.append("## Best Setups (Per Ticker)")
        md.append(f"Best cell per ticker, ranked by win rate then mean. Filter: n ≥ {args.min_n_ticker}.")
        md.append("")
        md.append("| ticker | setup | n | win% | mean% | median% | evts/ticker-year |")
        md.append("| --- | --- | ---: | ---: | ---: | ---: | ---: |")

        for t in tickers:
            candidates = []
            for (bin_lo, bin_hi), thr in per_ticker_cells[t]:
                s = per_ticker_cells[t][((bin_lo, bin_hi), thr)]
                if s.n < args.min_n_ticker:
                    continue
                candidates.append((s.win_rate, s.mean, s.median, s.n, s.events_per_ticker_year, bin_lo, bin_hi, thr))
            if not candidates:
                md.append(f"| {t} | (no cell met min n) | 0 | — | — | — | 0.00 |")
                continue
            candidates.sort(key=lambda x: (x[0], x[1], x[3]), reverse=True)
            win, mean, median, n, evts_ty, bin_lo, bin_hi, thr = candidates[0]
            md.append(
                f"| {t} | {_cell_label(bin_lo, bin_hi, thr)} | {n} | {win:.1f} | {mean:.2f} | {median:.2f} | {evts_ty:.2f} |"
            )
        md.append("")

    if args.focus_bin and args.focus_rsi > 0:
        focus_bin = parse_single_bin(args.focus_bin)
        if not _bin_contains(bins, focus_bin):
            md.append("## Focus Cell (Per Ticker)")
            md.append(f"Requested focus bin {args.focus_bin} not present in --bins; add it and rerun.")
            md.append("")
        elif args.focus_rsi not in thresholds:
            md.append("## Focus Cell (Per Ticker)")
            md.append(f"Requested focus RSI {args.focus_rsi} not present in --rsi-thresholds; add it and rerun.")
            md.append("")
        else:
            lo, hi = focus_bin
            thr = float(args.focus_rsi)
            md.append("## Focus Cell (Per Ticker)")
            md.append(f"Cell: {_cell_label(lo, hi, thr)} (Horizon=D{args.horizon})")
            md.append("")
            md.append("| ticker | n | win% | mean% | median% | evts/ticker-year |")
            md.append("| --- | ---: | ---: | ---: | ---: | ---: |")
            for t in tickers:
                s = per_ticker_cells[t][((lo, hi), thr)]
                if s.n == 0:
                    md.append(f"| {t} | 0 | — | — | — | 0.00 |")
                else:
                    md.append(f"| {t} | {s.n} | {s.win_rate:.1f} | {s.mean:.2f} | {s.median:.2f} | {s.events_per_ticker_year:.2f} |")
            md.append("")

    if args.focus_bin and args.focus_rsi_bands:
        focus_bin = parse_single_bin(args.focus_bin)
        if not _bin_contains(bins, focus_bin):
            md.append("## Focus RSI Bands (Aggregate + Per Ticker)")
            md.append(f"Requested focus bin {args.focus_bin} not present in --bins; add it and rerun.")
            md.append("")
        else:
            rsi_bands = parse_bins(args.focus_rsi_bands)
            lo, hi = focus_bin
            md.append("## Focus RSI Bands (MACD-V Band Slice)")
            md.append(f"MACD-V bin: {lo:.0f}-{hi:.0f} (Horizon=D{args.horizon})")
            md.append("")
            md.append("Aggregate across tickers (signal-weighted):")
            md.append("")
            md.append("| RSI percentile band | n | win% | mean% | median% | evts/ticker-year |")
            md.append("| --- | ---: | ---: | ---: | ---: | ---: |")

            for rlo, rhi in rsi_bands:
                all_rets: List[float] = []
                for _, df in data_by_ticker.items():
                    entry = (df["macdv_val"] >= lo) & (df["macdv_val"] < hi) & (df["rsi_pct"] >= rlo) & (df["rsi_pct"] < rhi)
                    entry = entry.fillna(False)
                    all_rets.extend(forward_returns(df, entry, args.horizon))
                s = _stats(all_rets, total_ticker_years)
                band_label = f"{rlo:.0f}-{rhi:.0f}"
                if s.n == 0:
                    md.append(f"| {band_label} | 0 | — | — | — | 0.00 |")
                else:
                    md.append(f"| {band_label} | {s.n} | {s.win_rate:.1f} | {s.mean:.2f} | {s.median:.2f} | {s.events_per_ticker_year:.2f} |")

            md.append("")
            md.append("Per-ticker (events per ticker-year uses that ticker's available bars):")
            md.append("")
            md.append("| ticker | RSI band | n | win% | mean% | median% | evts/ticker-year |")
            md.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")

            for t in tickers:
                df = data_by_ticker[t]
                for rlo, rhi in rsi_bands:
                    entry = (df["macdv_val"] >= lo) & (df["macdv_val"] < hi) & (df["rsi_pct"] >= rlo) & (df["rsi_pct"] < rhi)
                    entry = entry.fillna(False)
                    rets = forward_returns(df, entry, args.horizon)
                    s = _stats(rets, ticker_years[t])
                    band_label = f"{rlo:.0f}-{rhi:.0f}"
                    if s.n == 0:
                        md.append(f"| {t} | {band_label} | 0 | — | — | — | 0.00 |")
                    else:
                        md.append(f"| {t} | {band_label} | {s.n} | {s.win_rate:.1f} | {s.mean:.2f} | {s.median:.2f} | {s.events_per_ticker_year:.2f} |")

            md.append("")

    out = "\n".join(md)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(out, encoding="utf-8")
    else:
        print(out)


if __name__ == "__main__":
    main()
