"""
MAPI Historical Analysis

Provides empirical "percentile → forward return" mapping for MAPI's composite percentile rank,
plus basic backtest statistics for MAPI signals.

This is intentionally simpler than the RSI-MA Percentile Forward Mapping framework: it focuses on
answering "does MAPI work historically?" with transparent bin/zone statistics.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from enhanced_backtester import EnhancedPerformanceMatrixBacktester
from mapi_calculator import MAPICalculator


_DEFAULT_BINS: List[Tuple[float, float, str]] = [
    (0, 5, "0-5"),
    (5, 15, "5-15"),
    (15, 25, "15-25"),
    (25, 50, "25-50"),
    (50, 75, "50-75"),
    (75, 85, "75-85"),
    (85, 95, "85-95"),
    (95, 100, "95-100"),
]


def _to_float(v) -> Optional[float]:
    try:
        if v is None:
            return None
        if isinstance(v, (np.floating, np.integer)):
            v = v.item()
        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            return None
        return float(v)
    except Exception:
        return None


def _safe_stats(values: pd.Series) -> Dict[str, Optional[float]]:
    values = pd.to_numeric(values, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if values.empty:
        return {
            "mean": None,
            "median": None,
            "std": None,
            "win_rate": None,
            "pct_5": None,
            "pct_95": None,
        }
    arr = values.to_numpy(dtype=float)
    wins = float(np.mean(arr > 0)) * 100.0
    return {
        "mean": _to_float(np.mean(arr)),
        "median": _to_float(np.median(arr)),
        "std": _to_float(np.std(arr, ddof=0)),
        "win_rate": _to_float(wins),
        "pct_5": _to_float(np.percentile(arr, 5)),
        "pct_95": _to_float(np.percentile(arr, 95)),
    }


def _assign_bin(percentile: float, bins: List[Tuple[float, float, str]]) -> int:
    for i, (pmin, pmax, _label) in enumerate(bins):
        if pmin <= percentile < pmax:
            return i
    return len(bins) - 1


@dataclass(frozen=True)
class MAPIBinStats:
    bin_label: str
    bin_min: float
    bin_max: float
    count: int
    horizons: Dict[str, Dict[str, Optional[float]]]  # {"3d": {mean, win_rate, ...}, ...}


def compute_mapi_historical_from_df(
    df: pd.DataFrame,
    *,
    lookback_days: int = 1095,
    horizons: List[int] | None = None,
    require_momentum: bool = False,
    adx_threshold: float = 25.0,
    bins: List[Tuple[float, float, str]] | None = None,
    calculator: MAPICalculator | None = None,
) -> Dict:
    """
    Compute MAPI historical mapping + simple backtest stats from an OHLC dataframe.

    Args:
        df: OHLC dataframe with lowercase columns: open/high/low/close (volume optional).
        lookback_days: number of most recent rows to use (after indicator warmup).
        horizons: forward horizons in bars (daily bars assumed); default [3, 7, 14, 21].
        require_momentum: if True, only include rows where ADX > adx_threshold.
        adx_threshold: ADX threshold for momentum regime filter.
        bins: percentile bin definitions.
        calculator: optional MAPICalculator instance.
    """
    if horizons is None:
        horizons = [3, 7, 14, 21]
    if bins is None:
        bins = _DEFAULT_BINS
    if calculator is None:
        calculator = MAPICalculator(
            ema_period=20,
            ema_slope_period=5,
            atr_period=14,
            edr_lookback=60,
            esv_lookback=90,
        )

    if df is None or df.empty:
        raise ValueError("Empty dataframe")

    df = df.copy()
    df.columns = [c.lower() for c in df.columns]
    for col in ("open", "high", "low", "close"):
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Compute MAPI values on full history, then tail for analysis.
    mapi = calculator.calculate_mapi(df)
    df = df.tail(lookback_days).copy()

    analysis = pd.DataFrame(index=df.index)
    analysis["close"] = pd.to_numeric(df["close"], errors="coerce")
    analysis["composite_percentile"] = pd.to_numeric(mapi["composite_percentile_rank"].reindex(df.index), errors="coerce")
    analysis["composite_raw"] = pd.to_numeric(mapi["composite_score"].reindex(df.index), errors="coerce")
    analysis["edr_percentile"] = pd.to_numeric(mapi["edr_percentile"].reindex(df.index), errors="coerce")
    analysis["esv_percentile"] = pd.to_numeric(mapi["esv_percentile"].reindex(df.index), errors="coerce")
    analysis["adx"] = pd.to_numeric(mapi["adx"].reindex(df.index), errors="coerce")
    analysis["regime"] = mapi["regime"].reindex(df.index).astype(str)
    analysis["strong_momentum_entry"] = mapi["strong_momentum_entry"].reindex(df.index).astype(bool)
    analysis["pullback_entry"] = mapi["pullback_entry"].reindex(df.index).astype(bool)
    analysis["exit_signal"] = mapi["exit_signal"].reindex(df.index).astype(bool)

    for h in horizons:
        analysis[f"fwd_return_{h}d"] = (analysis["close"].shift(-h) / analysis["close"] - 1.0) * 100.0

    # Base validity filter: need percentile + close, and at least the max horizon forward return.
    max_h = max(horizons) if horizons else 0
    valid = analysis["close"].notna() & analysis["composite_percentile"].notna()
    if max_h > 0:
        valid = valid & analysis[f"fwd_return_{max_h}d"].notna()

    if require_momentum:
        valid = valid & (analysis["adx"] > adx_threshold)

    analysis = analysis.loc[valid].copy()
    if analysis.empty:
        raise ValueError("No valid rows after filtering (try require_momentum=false or lower lookback_days)")

    # Percentile bins
    bin_index = analysis["composite_percentile"].apply(lambda p: _assign_bin(float(p), bins))
    analysis["bin_idx"] = bin_index.astype(int)

    bin_stats: List[MAPIBinStats] = []
    for i, (pmin, pmax, label) in enumerate(bins):
        subset = analysis.loc[analysis["bin_idx"] == i]
        horizon_stats: Dict[str, Dict[str, Optional[float]]] = {}
        for h in horizons:
            horizon_stats[f"{h}d"] = _safe_stats(subset[f"fwd_return_{h}d"])
        bin_stats.append(
            MAPIBinStats(
                bin_label=label,
                bin_min=float(pmin),
                bin_max=float(pmax),
                count=int(len(subset)),
                horizons=horizon_stats,
            )
        )

    def zone_mask(pmin: float, pmax: float) -> pd.Series:
        if pmax >= 100:
            return (analysis["composite_percentile"] >= pmin) & (analysis["composite_percentile"] <= pmax)
        return (analysis["composite_percentile"] >= pmin) & (analysis["composite_percentile"] < pmax)

    def zone_stats(pmin: float, pmax: float) -> Dict:
        subset = analysis.loc[zone_mask(pmin, pmax)]
        out = {"pct_min": float(pmin), "pct_max": float(pmax), "count": int(len(subset))}
        for h in horizons:
            s = _safe_stats(subset[f"fwd_return_{h}d"])
            out[f"mean_return_{h}d"] = s["mean"]
            out[f"win_rate_{h}d"] = s["win_rate"]
            out[f"pct_5_return_{h}d"] = s["pct_5"]
            out[f"pct_95_return_{h}d"] = s["pct_95"]
        return out

    zones = {
        "extreme_low": zone_stats(0, 20),
        "low": zone_stats(20, 35),
        "pullback_zone": zone_stats(30, 45),
        "neutral": zone_stats(40, 65),
        "strong_momentum": zone_stats(65, 100),
        "all": zone_stats(0, 100),
    }

    def signal_stats(signal_col: str) -> Dict:
        subset = analysis.loc[analysis[signal_col]]
        out = {"count": int(len(subset))}
        for h in horizons:
            s = _safe_stats(subset[f"fwd_return_{h}d"])
            out[f"mean_return_{h}d"] = s["mean"]
            out[f"win_rate_{h}d"] = s["win_rate"]
        return out

    signals = {
        "strong_momentum_entry": signal_stats("strong_momentum_entry"),
        "pullback_entry": signal_stats("pullback_entry"),
        "exit_signal": signal_stats("exit_signal"),
    }

    latest = analysis.iloc[-1]
    current_state = {
        "date": str(latest.name.date()) if hasattr(latest.name, "date") else str(latest.name),
        "close": _to_float(latest["close"]),
        "composite_percentile": _to_float(latest["composite_percentile"]),
        "composite_raw": _to_float(latest["composite_raw"]),
        "edr_percentile": _to_float(latest["edr_percentile"]),
        "esv_percentile": _to_float(latest["esv_percentile"]),
        "adx": _to_float(latest["adx"]),
        "regime": str(latest["regime"]),
    }

    return {
        "lookback_days": int(lookback_days),
        "horizons": [int(h) for h in horizons],
        "require_momentum": bool(require_momentum),
        "adx_threshold": float(adx_threshold),
        "bin_definitions": [{"min": b[0], "max": b[1], "label": b[2]} for b in bins],
        "bin_stats": [asdict(b) for b in bin_stats],
        "zone_stats": zones,
        "signal_stats": signals,
        "current_state": current_state,
        "sample_size": int(len(analysis)),
    }


def run_mapi_historical_analysis(
    ticker: str,
    *,
    lookback_days: int = 1095,
    horizons: List[int] | None = None,
    require_momentum: bool = False,
    adx_threshold: float = 25.0,
) -> Dict:
    """
    Fetch data for ticker (daily) and compute historical analysis.
    """
    ticker_upper = ticker.upper()

    backtester = EnhancedPerformanceMatrixBacktester(
        tickers=[ticker_upper],
        lookback_period=252,
        rsi_length=14,
        ma_length=14,
        max_horizon=21,
    )
    df = backtester.fetch_data(ticker_upper, period="5y")
    if df is None or df.empty:
        raise ValueError(f"Could not fetch data for {ticker_upper}")

    df.columns = [c.lower() for c in df.columns]
    df = df[[c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]].copy()

    analysis = compute_mapi_historical_from_df(
        df,
        lookback_days=lookback_days,
        horizons=horizons,
        require_momentum=require_momentum,
        adx_threshold=adx_threshold,
    )
    analysis["ticker"] = ticker_upper
    return analysis

