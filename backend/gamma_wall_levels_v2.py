#!/usr/bin/env python3
"""
Gamma Wall Level Calculations (v2)
=================================

PineScript-inspired deterministic helpers for:
- ST/LT/Q wall selection (multi-method + distinctness)
- Max pain (dynamic strike window + optional gamma weighting)

This module is intentionally dependency-light and is used by the scanner that
writes `backend/cache/gamma_walls_data.json`, which is consumed by the website's
Risk Distance tab via `/api/gamma-data/scanner-json`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Literal, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.stats import norm


WallSide = Literal["put", "call"]


DEFAULT_WALL_WEIGHTS = {
    "max_gex": 0.40,
    "weighted_centroid": 0.35,
    "cumulative_threshold": 0.25,
}


@dataclass(frozen=True)
class WallSelection:
    wall: float
    method_used: str
    dominance: float
    top_5: List[Tuple[float, float]]
    max_gex: float
    centroid: float
    cumulative: float


def _finite_series(series: pd.Series) -> pd.Series:
    if series is None or series.empty:
        return pd.Series(dtype=float)
    s = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    try:
        s.index = pd.to_numeric(s.index, errors="coerce")
    except Exception:
        pass
    s = s[~pd.isna(s.index)]
    s = s.sort_index()
    return s.astype(float)


def _nearest_strike(target: float, strikes: Sequence[float]) -> float:
    return float(min(strikes, key=lambda k: abs(float(k) - target)))


def calculate_gamma(S: float, K: float, T: float, r: float, sigma: float) -> float:
    try:
        if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
            return 0.0
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        g = norm.pdf(d1) / (S * sigma * np.sqrt(T))
        return float(g) if np.isfinite(g) else 0.0
    except Exception:
        return 0.0


def calculate_wall_strength(gex_series: pd.Series) -> float:
    s = _finite_series(gex_series)
    if s.empty:
        return 0.0
    abs_gex = s.abs()
    total = float(abs_gex.sum())
    if total <= 0:
        return 0.0
    max_exp = float(abs_gex.max())
    concentration = max_exp / total
    strength = concentration * 45.0 + np.log10(max_exp + 1.0) * 8.0
    return float(max(0.0, min(95.0, strength)))


def _compute_methods(
    gex_by_strike: pd.Series,
    current_price: float,
    *,
    max_dist_pct: float,
    weights: dict,
    cumulative_threshold_pct: float,
) -> Tuple[dict, float, List[Tuple[float, float]]]:
    s = _finite_series(gex_by_strike)
    if s.empty or current_price <= 0:
        return (
            {"max_gex": current_price, "centroid": current_price, "cumulative": current_price, "weighted": current_price},
            0.0,
            [],
        )

    min_strike = current_price * (1.0 - max_dist_pct)
    max_strike = current_price * (1.0 + max_dist_pct)
    window = s[(s.index >= min_strike) & (s.index <= max_strike)]
    if window.empty:
        window = s

    abs_gex = window.abs()
    total = float(abs_gex.sum())
    if total <= 0:
        return (
            {"max_gex": float(window.index.min()), "centroid": float(window.index.min()), "cumulative": float(window.index.min()), "weighted": float(window.index.min())},
            0.0,
            [],
        )

    dominance = float(abs_gex.max() / total)
    top_5 = [(float(k), float(v)) for k, v in abs_gex.nlargest(5).items()]

    max_gex_strike = float(abs_gex.idxmax())

    centroid_target = float((abs_gex * abs_gex.index).sum() / total)
    centroid_strike = _nearest_strike(centroid_target, abs_gex.index.to_list())

    # Cumulative threshold: accumulate from closest-to-price outward.
    by_proximity = abs_gex.copy()
    by_proximity.index = by_proximity.index.astype(float)
    by_proximity = by_proximity.sort_index(key=lambda idx: np.abs(idx - current_price))
    cumsum = by_proximity.cumsum()
    threshold_val = total * float(cumulative_threshold_pct)
    above = cumsum[cumsum >= threshold_val]
    cumulative_strike = float(above.index[0]) if not above.empty else max_gex_strike

    weighted_target = (
        float(weights.get("max_gex", 0.0)) * max_gex_strike
        + float(weights.get("weighted_centroid", 0.0)) * centroid_strike
        + float(weights.get("cumulative_threshold", 0.0)) * cumulative_strike
    )
    weighted_strike = _nearest_strike(weighted_target, abs_gex.index.to_list())

    return (
        {
            "max_gex": max_gex_strike,
            "centroid": float(centroid_strike),
            "cumulative": float(cumulative_strike),
            "weighted": float(weighted_strike),
        },
        dominance,
        top_5,
    )


def select_wall_level(
    gex_by_strike: pd.Series,
    current_price: float,
    *,
    side: WallSide,
    bucket_name: str,
    max_dist_pct: float,
    already_selected: Optional[Sequence[float]] = None,
    min_separation_pct: float = 0.003,
    weights: Optional[dict] = None,
    cumulative_threshold_pct: float = 0.7,
    allow_outside_price_side: bool = True,
) -> WallSelection:
    """
    Select a wall strike with PineScript-style multi-method computation, then enforce
    distinctness across buckets (primarily for put walls).
    """
    weights = weights or DEFAULT_WALL_WEIGHTS
    already_selected = list(already_selected or [])

    s = _finite_series(gex_by_strike)
    if s.empty or current_price <= 0:
        fallback = current_price * (0.95 if side == "put" else 1.05)
        return WallSelection(
            wall=float(fallback),
            method_used="fallback",
            dominance=0.0,
            top_5=[],
            max_gex=float(fallback),
            centroid=float(fallback),
            cumulative=float(fallback),
        )

    # Optional constraint: for puts prefer below, for calls prefer above.
    if not allow_outside_price_side:
        if side == "put":
            s = s[s.index < current_price] if not s[s.index < current_price].empty else s
        else:
            s = s[s.index > current_price] if not s[s.index > current_price].empty else s

    methods, dominance, top_5 = _compute_methods(
        s,
        current_price,
        max_dist_pct=max_dist_pct,
        weights=weights,
        cumulative_threshold_pct=cumulative_threshold_pct,
    )

    primary = float(methods["weighted"])

    # If we need distinctness and the primary is too close, pick an alternate from top strikes.
    abs_gex = _finite_series(s).abs()
    if abs_gex.empty:
        return WallSelection(primary, "weighted", dominance, top_5, methods["max_gex"], methods["centroid"], methods["cumulative"])

    min_sep_abs = float(min_separation_pct) * float(current_price)

    def too_close(strike: float) -> bool:
        return any(abs(float(strike) - float(prev)) <= min_sep_abs for prev in already_selected)

    if already_selected and too_close(primary):
        # Score candidates: combine magnitude + uniqueness; regime by bucket.
        top_candidates = abs_gex.nlargest(12)
        if not top_candidates.empty:
            gex_max = float(top_candidates.max()) or 1.0

            def uniqueness_score(strike: float) -> float:
                if not already_selected:
                    return 1.0
                min_d = min(abs(float(strike) - float(prev)) for prev in already_selected)
                return float(min(1.0, (min_d / current_price) * 20.0))

            def proximity_score(strike: float) -> float:
                # Prefer closer to spot (scaled to window).
                window = max_dist_pct * current_price
                if window <= 0:
                    return 0.0
                return float(max(0.0, 1.0 - (abs(float(strike) - current_price) / window)))

            if bucket_name == "weekly":
                w_gex, w_unique, w_prox = 0.85, 0.10, 0.05
            elif bucket_name == "swing":
                w_gex, w_unique, w_prox = 0.70, 0.20, 0.10
            elif bucket_name == "long":
                w_gex, w_unique, w_prox = 0.55, 0.35, 0.10
            else:
                w_gex, w_unique, w_prox = 0.45, 0.45, 0.10

            ranked: List[Tuple[float, float]] = []
            for strike, gex_val in top_candidates.items():
                gs = float(gex_val) / gex_max
                us = uniqueness_score(float(strike))
                ps = proximity_score(float(strike))
                ranked.append((float(strike), w_gex * gs + w_unique * us + w_prox * ps))
            ranked.sort(key=lambda x: x[1], reverse=True)

            for strike, _ in ranked:
                if not too_close(strike):
                    return WallSelection(
                        wall=float(strike),
                        method_used="distinct_weighted",
                        dominance=dominance,
                        top_5=top_5,
                        max_gex=float(methods["max_gex"]),
                        centroid=float(methods["centroid"]),
                        cumulative=float(methods["cumulative"]),
                    )

    return WallSelection(
        wall=float(primary),
        method_used="weighted",
        dominance=dominance,
        top_5=top_5,
        max_gex=float(methods["max_gex"]),
        centroid=float(methods["centroid"]),
        cumulative=float(methods["cumulative"]),
    )


def calculate_max_pain_level(
    calls: pd.DataFrame,
    puts: pd.DataFrame,
    current_price: float,
    *,
    dte: int,
    risk_free_rate: float = 0.045,
    dealer_bias_factor: float = 0.65,
    use_gamma_weighted_oi: bool = True,
    min_strikes: int = 12,
) -> float:
    """
    True max pain: strike minimizing intrinsic value paid to option holders at expiry.
    Uses a dynamic strike window sized from IV (if present), with optional gamma weighting.
    """
    if current_price <= 0:
        return float(current_price)

    if calls is None or puts is None or calls.empty or puts.empty:
        return float(current_price)

    calls = calls.copy()
    puts = puts.copy()

    for df in (calls, puts):
        if "strike" in df.columns:
            df.set_index("strike", inplace=True)
        df.index = pd.to_numeric(df.index, errors="coerce")
        df.dropna(axis=0, subset=[], inplace=True)

    if calls.index.hasnans:
        calls = calls[~calls.index.isna()]
    if puts.index.hasnans:
        puts = puts[~puts.index.isna()]

    all_strikes = calls.index.union(puts.index).astype(float).sort_values()
    if len(all_strikes) == 0:
        return float(current_price)

    iv_calls = float(pd.to_numeric(calls.get("impliedVolatility"), errors="coerce").median()) if "impliedVolatility" in calls.columns else np.nan
    iv_puts = float(pd.to_numeric(puts.get("impliedVolatility"), errors="coerce").median()) if "impliedVolatility" in puts.columns else np.nan
    iv = np.nanmean([iv_calls, iv_puts])
    if not np.isfinite(iv) or iv <= 0:
        iv = 0.25

    iv_pct = iv * 100.0
    vol_factor = 0.20 if iv_pct > 40 else 0.15 if iv_pct > 25 else 0.12
    strike_range = current_price * vol_factor

    def choose_window(range_mult: float) -> pd.Index:
        mn = current_price - strike_range * range_mult
        mx = current_price + strike_range * range_mult
        return all_strikes[(all_strikes >= mn) & (all_strikes <= mx)]

    window = choose_window(1.0)
    if len(window) < min_strikes:
        window = choose_window(1.5)
    if len(window) < min_strikes:
        window = all_strikes

    def effective_oi(df: pd.DataFrame) -> pd.Series:
        oi = pd.to_numeric(df.get("openInterest"), errors="coerce").fillna(0.0).astype(float) if "openInterest" in df.columns else pd.Series(0.0, index=df.index)
        vol = pd.to_numeric(df.get("volume"), errors="coerce").fillna(0.0).astype(float) if "volume" in df.columns else pd.Series(0.0, index=df.index)
        # Prefer OI; fallback to volume when OI is missing/zero.
        eff = oi.where(oi > 0, vol)
        return eff.reindex(window).fillna(0.0).astype(float)

    call_oi = effective_oi(calls)
    put_oi = effective_oi(puts)

    # Dealer bias: calls scaled up (dealers short), puts scaled down (dealers long bias).
    dealer_bias_factor = float(dealer_bias_factor) if dealer_bias_factor > 0 else 0.65
    call_oi = call_oi * (1.0 / dealer_bias_factor)
    put_oi = put_oi * dealer_bias_factor

    if use_gamma_weighted_oi:
        T = max(1, int(dte)) / 365.0
        gamma = pd.Series(
            [calculate_gamma(current_price, float(k), T, risk_free_rate, float(iv)) for k in window],
            index=window,
            dtype=float,
        )
        gmax = float(gamma.max()) if float(gamma.max()) > 0 else 0.0
        if gmax > 0:
            gamma_norm = gamma / gmax
            weight = 1.0 + gamma_norm
            call_oi = call_oi * weight
            put_oi = put_oi * weight

    strikes = np.array(window, dtype=float)
    call_w = call_oi.to_numpy(dtype=float) * 100.0
    put_w = put_oi.to_numpy(dtype=float) * 100.0

    # Precompute cumulative sums for vectorized pain calculation.
    call_cum = np.cumsum(call_w)
    call_cum_k = np.cumsum(call_w * strikes)
    put_cum = np.cumsum(put_w)
    put_cum_k = np.cumsum(put_w * strikes)

    total_call = call_cum[-1] if len(call_cum) else 0.0
    total_call_k = call_cum_k[-1] if len(call_cum_k) else 0.0
    total_put = put_cum[-1] if len(put_cum) else 0.0
    total_put_k = put_cum_k[-1] if len(put_cum_k) else 0.0

    # For each candidate strike s:
    # call pain = s*sum(call_w for k<s) - sum(k*call_w for k<s)
    # put pain  = sum(k*put_w for k>s) - s*sum(put_w for k>s)
    call_left = np.concatenate(([0.0], call_cum[:-1]))
    call_left_k = np.concatenate(([0.0], call_cum_k[:-1]))
    call_pain = strikes * call_left - call_left_k

    put_right = total_put - put_cum
    put_right_k = total_put_k - put_cum_k
    put_pain = put_right_k - strikes * put_right

    total_pain = call_pain + put_pain
    if not np.isfinite(total_pain).any():
        return float(current_price)

    best_idx = int(np.nanargmin(total_pain))
    best = float(strikes[best_idx])

    # Guardrail: if best is very far, pick nearest strike to spot.
    if abs(best - current_price) / current_price > 0.20:
        best = float(min(strikes, key=lambda x: abs(float(x) - current_price)))

    return best

