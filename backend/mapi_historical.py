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

    # Current state should reflect the latest bar (not the last valid forward-return row).
    try:
        current_state = calculator.get_current_signal(df)
    except Exception:
        current_state = None

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

    if current_state is None:
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
    else:
        current_state = {
            "date": str(current_state.get("date")),
            "close": _to_float(current_state.get("close")),
            "composite_percentile": _to_float(current_state.get("composite_percentile_rank")),
            "composite_raw": _to_float(current_state.get("composite_score")),
            "edr_percentile": _to_float(current_state.get("edr_percentile")),
            "esv_percentile": _to_float(current_state.get("esv_percentile")),
            "adx": _to_float(current_state.get("adx")),
            "regime": str(current_state.get("regime")),
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


def run_mapi_basket_historical_analysis(
    tickers: List[str],
    *,
    lookback_days: int = 1095,
    horizons: List[int] | None = None,
    require_momentum: bool = False,
    adx_threshold: float = 25.0,
) -> Dict:
    """
    Basket version of MAPI historical analysis.

    Computes:
    - Per-ticker summaries
    - Pooled (all-rows) bin/zone/signal stats across tickers
    - Breadth relationships (cross-sectional MAPI vs forward basket returns)
    """
    if horizons is None:
        horizons = [3, 7, 14, 21]
    tickers_upper = [t.strip().upper() for t in tickers if t and t.strip()]
    if not tickers_upper:
        raise ValueError("No tickers provided")

    calculator = MAPICalculator(
        ema_period=20,
        ema_slope_period=5,
        atr_period=14,
        edr_lookback=60,
        esv_lookback=90,
    )

    per_ticker: List[Dict] = []
    pooled_rows: List[pd.DataFrame] = []
    current_states: List[Dict] = []

    for t in tickers_upper:
        backtester = EnhancedPerformanceMatrixBacktester(
            tickers=[t],
            lookback_period=252,
            rsi_length=14,
            ma_length=14,
            max_horizon=21,
        )
        df = backtester.fetch_data(t, period="5y")
        if df is None or df.empty:
            continue

        df.columns = [c.lower() for c in df.columns]
        df = df[[c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]].copy()

        # Per-ticker summary (reuses single-ticker routine)
        one = compute_mapi_historical_from_df(
            df,
            lookback_days=lookback_days,
            horizons=horizons,
            require_momentum=require_momentum,
            adx_threshold=adx_threshold,
            calculator=calculator,
        )
        one["ticker"] = t
        per_ticker.append(one)

        # Build pooled row-level frame for breadth/relationships.
        mapi = calculator.calculate_mapi(df)
        df_tail = df.tail(lookback_days).copy()
        a = pd.DataFrame(index=df_tail.index)
        a["ticker"] = t
        a["close"] = pd.to_numeric(df_tail["close"], errors="coerce")
        a["composite_percentile"] = pd.to_numeric(mapi["composite_percentile_rank"].reindex(df_tail.index), errors="coerce")
        a["adx"] = pd.to_numeric(mapi["adx"].reindex(df_tail.index), errors="coerce")
        a["strong_momentum_entry"] = mapi["strong_momentum_entry"].reindex(df_tail.index).astype(bool)
        a["pullback_entry"] = mapi["pullback_entry"].reindex(df_tail.index).astype(bool)
        a["exit_signal"] = mapi["exit_signal"].reindex(df_tail.index).astype(bool)

        for h in horizons:
            a[f"fwd_return_{h}d"] = (a["close"].shift(-h) / a["close"] - 1.0) * 100.0

        max_h = max(horizons) if horizons else 0
        valid = a["close"].notna() & a["composite_percentile"].notna()
        if max_h > 0:
            valid = valid & a[f"fwd_return_{max_h}d"].notna()
        if require_momentum:
            valid = valid & (a["adx"] > adx_threshold)
        a = a.loc[valid].copy()
        pooled_rows.append(a)

        # Current state for basket breadth (latest bar)
        try:
            cs = calculator.get_current_signal(df_tail)
            current_states.append(
                {
                    "ticker": t,
                    "date": str(cs.get("date")),
                    "close": _to_float(cs.get("close")),
                    "composite_percentile": _to_float(cs.get("composite_percentile_rank")),
                    "composite_raw": _to_float(cs.get("composite_score")),
                    "adx": _to_float(cs.get("adx")),
                    "regime": str(cs.get("regime")),
                    "strong_momentum_entry": bool(cs.get("strong_momentum_entry")),
                    "pullback_entry": bool(cs.get("pullback_entry")),
                    "exit_signal": bool(cs.get("exit_signal")),
                }
            )
        except Exception:
            pass

    if not pooled_rows:
        raise ValueError("Could not fetch any data for the requested tickers")

    pooled = pd.concat(pooled_rows, axis=0).sort_index()

    # --- pooled (all-rows) bin/zone/signal stats without recomputing indicators ---
    bins = _DEFAULT_BINS
    max_h = max(horizons) if horizons else 0
    pooled_valid = pooled["close"].notna() & pooled["composite_percentile"].notna()
    if max_h > 0:
        pooled_valid = pooled_valid & pooled[f"fwd_return_{max_h}d"].notna()
    pooled = pooled.loc[pooled_valid].copy()

    pooled["bin_idx"] = pooled["composite_percentile"].apply(lambda p: _assign_bin(float(p), bins)).astype(int)

    pooled_bin_stats: List[MAPIBinStats] = []
    for i, (pmin, pmax, label) in enumerate(bins):
        subset = pooled.loc[pooled["bin_idx"] == i]
        horizon_stats: Dict[str, Dict[str, Optional[float]]] = {}
        for h in horizons:
            horizon_stats[f"{h}d"] = _safe_stats(subset[f"fwd_return_{h}d"])
        pooled_bin_stats.append(
            MAPIBinStats(
                bin_label=label,
                bin_min=float(pmin),
                bin_max=float(pmax),
                count=int(len(subset)),
                horizons=horizon_stats,
            )
        )

    def _zone_mask(df_: pd.DataFrame, pmin: float, pmax: float) -> pd.Series:
        if pmax >= 100:
            return (df_["composite_percentile"] >= pmin) & (df_["composite_percentile"] <= pmax)
        return (df_["composite_percentile"] >= pmin) & (df_["composite_percentile"] < pmax)

    def _zone_stats(df_: pd.DataFrame, pmin: float, pmax: float) -> Dict:
        subset = df_.loc[_zone_mask(df_, pmin, pmax)]
        out = {"pct_min": float(pmin), "pct_max": float(pmax), "count": int(len(subset))}
        for h in horizons:
            s = _safe_stats(subset[f"fwd_return_{h}d"])
            out[f"mean_return_{h}d"] = s["mean"]
            out[f"win_rate_{h}d"] = s["win_rate"]
            out[f"pct_5_return_{h}d"] = s["pct_5"]
            out[f"pct_95_return_{h}d"] = s["pct_95"]
        return out

    pooled_zone_stats = {
        "extreme_low": _zone_stats(pooled, 0, 20),
        "low": _zone_stats(pooled, 20, 35),
        "pullback_zone": _zone_stats(pooled, 30, 45),
        "neutral": _zone_stats(pooled, 40, 65),
        "strong_momentum": _zone_stats(pooled, 65, 100),
        "all": _zone_stats(pooled, 0, 100),
    }

    def _signal_stats(df_: pd.DataFrame, col: str) -> Dict:
        subset = df_.loc[df_[col]]
        out = {"count": int(len(subset))}
        for h in horizons:
            s = _safe_stats(subset[f"fwd_return_{h}d"])
            out[f"mean_return_{h}d"] = s["mean"]
            out[f"win_rate_{h}d"] = s["win_rate"]
        return out

    pooled_signal_stats = {
        "strong_momentum_entry": _signal_stats(pooled, "strong_momentum_entry"),
        "pullback_entry": _signal_stats(pooled, "pullback_entry"),
        "exit_signal": _signal_stats(pooled, "exit_signal"),
    }

    # --- breadth relationships (cross-sectional metrics by date) ---
    breadth = pooled.copy()
    breadth = breadth.reset_index()
    date_col = breadth.columns[0]
    breadth = breadth.rename(columns={date_col: "date"})
    breadth["date"] = pd.to_datetime(breadth["date"]).dt.date.astype(str)

    def _pct(cond: pd.Series) -> float:
        return float(np.mean(cond)) * 100.0 if len(cond) else 0.0

    agg_rows = []
    for date, grp in breadth.groupby("date"):
        row = {
            "date": date,
            "n": int(len(grp)),
            "mean_composite_percentile": _to_float(grp["composite_percentile"].mean()),
            "pct_extreme_low": _to_float(_pct(grp["composite_percentile"] <= 20)),
            "pct_low": _to_float(_pct((grp["composite_percentile"] > 20) & (grp["composite_percentile"] <= 35))),
            "pct_strong": _to_float(_pct(grp["composite_percentile"] >= 65)),
            "strong_signals": int(grp["strong_momentum_entry"].sum()),
            "pullback_signals": int(grp["pullback_entry"].sum()),
            "exit_signals": int(grp["exit_signal"].sum()),
        }
        for h in horizons:
            row[f"basket_fwd_return_{h}d"] = _to_float(grp[f"fwd_return_{h}d"].mean())
        agg_rows.append(row)

    breadth_df = pd.DataFrame(agg_rows)

    # --- cross-sectional "scanner-style" strategy tests (pick/average across tickers by date) ---
    def _strategy_from_daily_rows(daily_rows: List[Dict]) -> Dict:
        df_ = pd.DataFrame(daily_rows)
        out = {"days": int(len(df_))}
        for h in horizons:
            s = _safe_stats(pd.to_numeric(df_.get(f"fwd_return_{h}d"), errors="coerce"))
            out[f"mean_return_{h}d"] = s["mean"]
            out[f"win_rate_{h}d"] = s["win_rate"]
        return out

    min_pick_rows: List[Dict] = []
    low_pick_rows: List[Dict] = []
    low_equal_rows: List[Dict] = []

    for date, grp in breadth.groupby("date"):
        grp = grp.copy()
        grp["composite_percentile"] = pd.to_numeric(grp["composite_percentile"], errors="coerce")
        grp = grp.dropna(subset=["composite_percentile"])
        if grp.empty:
            continue

        # 1) Pick the single lowest composite-percentile ticker each day
        pick = grp.sort_values("composite_percentile", ascending=True).iloc[0]
        min_pick_rows.append(
            {"date": date, "ticker": pick.get("ticker"), **{f"fwd_return_{h}d": pick.get(f"fwd_return_{h}d") for h in horizons}}
        )

        # 2) Pick the lowest ticker within the "Low" zone (20–35). Skip if none.
        low_grp = grp.loc[(grp["composite_percentile"] > 20) & (grp["composite_percentile"] <= 35)]
        if not low_grp.empty:
            pick2 = low_grp.sort_values("composite_percentile", ascending=True).iloc[0]
            low_pick_rows.append(
                {"date": date, "ticker": pick2.get("ticker"), **{f"fwd_return_{h}d": pick2.get(f"fwd_return_{h}d") for h in horizons}}
            )

            # 3) Equal-weight all tickers in Low zone that day
            row3 = {"date": date, "n": int(len(low_grp))}
            for h in horizons:
                row3[f"fwd_return_{h}d"] = _to_float(pd.to_numeric(low_grp[f"fwd_return_{h}d"], errors="coerce").mean())
            low_equal_rows.append(row3)

    cross_sectional_strategies = {
        "min_percentile_pick": _strategy_from_daily_rows(min_pick_rows),
        "low_zone_min_pick": _strategy_from_daily_rows(low_pick_rows),
        "low_zone_equal_weight": _strategy_from_daily_rows(low_equal_rows),
    }

    relationships: Dict[str, Dict[str, Optional[float] | Dict[str, Optional[float]]]] = {}
    for h in horizons:
        y = pd.to_numeric(breadth_df[f"basket_fwd_return_{h}d"], errors="coerce")
        x_mean = pd.to_numeric(breadth_df["mean_composite_percentile"], errors="coerce")
        x_low = pd.to_numeric(breadth_df["pct_low"], errors="coerce")
        x_strong = pd.to_numeric(breadth_df["pct_strong"], errors="coerce")
        x_extreme = pd.to_numeric(breadth_df["pct_extreme_low"], errors="coerce")

        def corr(a: pd.Series, b: pd.Series) -> Optional[float]:
            dfc = pd.concat([a, b], axis=1).dropna()
            if len(dfc) < 30:
                return None
            return _to_float(dfc.iloc[:, 0].corr(dfc.iloc[:, 1]))

        relationships[f"{h}d"] = {
            "corr_mean_percentile": corr(x_mean, y),
            "corr_pct_low": corr(x_low, y),
            "corr_pct_strong": corr(x_strong, y),
            "corr_pct_extreme_low": corr(x_extreme, y),
        }

    # Summary for "today" breadth using current_states
    breadth_now = None
    if current_states:
        cs_df = pd.DataFrame(current_states)
        breadth_now = {
            "n": int(len(cs_df)),
            "mean_composite_percentile": _to_float(cs_df["composite_percentile"].mean()),
            "pct_extreme_low": _to_float(float(np.mean(cs_df["composite_percentile"] <= 20)) * 100.0),
            "pct_low": _to_float(float(np.mean((cs_df["composite_percentile"] > 20) & (cs_df["composite_percentile"] <= 35))) * 100.0),
            "pct_strong": _to_float(float(np.mean(cs_df["composite_percentile"] >= 65)) * 100.0),
            "strong_signals": int(cs_df["strong_momentum_entry"].sum()) if "strong_momentum_entry" in cs_df.columns else 0,
            "pullback_signals": int(cs_df["pullback_entry"].sum()) if "pullback_entry" in cs_df.columns else 0,
            "exit_signals": int(cs_df["exit_signal"].sum()) if "exit_signal" in cs_df.columns else 0,
        }

    # Replace placeholder pooled_summary
    pooled_summary = {
        "lookback_days": int(lookback_days),
        "horizons": [int(h) for h in horizons],
        "require_momentum": bool(require_momentum),
        "adx_threshold": float(adx_threshold),
        "bin_definitions": [{"min": b[0], "max": b[1], "label": b[2]} for b in bins],
        "bin_stats": [asdict(b) for b in pooled_bin_stats],
        "zone_stats": pooled_zone_stats,
        "signal_stats": pooled_signal_stats,
        "sample_size": int(len(pooled)),
    }

    return {
        "tickers": tickers_upper,
        "pooled": pooled_summary,
        "per_ticker": per_ticker,
        "breadth_now": breadth_now,
        "breadth_relationships": relationships,
        "cross_sectional_strategies": cross_sectional_strategies,
        "current_states": current_states,
    }
