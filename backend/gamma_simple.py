"""
Minimal gamma data fetcher for Telegram /gammawalls and /maxpain commands.

Computes put walls (max OI below current price) and max pain (minimise
total option pain) for each DTE target.  No scipy, no complex dependencies.

Distance formula (PineScript convention):
    dist_pct = (level - price) / price * 100
    Positive → level above price → put wall BREACHED (entry zone)
    Negative → level below price → support intact
"""

from __future__ import annotations

import sys
from datetime import datetime
from typing import Optional

import yfinance as yf


def _best_expiry(option_dates: tuple | list, target_days: int) -> Optional[str]:
    now = datetime.now()
    best, best_diff = None, float("inf")
    for d in option_dates:
        try:
            exp = datetime.strptime(d, "%Y-%m-%d")
            diff = abs((exp - now).days - target_days)
            if diff < best_diff:
                best_diff = diff
                best = d
        except Exception:
            continue
    return best


def _max_pain(puts_oi: dict, calls_oi: dict) -> tuple[float, str]:
    """Return (max_pain_strike, pin_risk)."""
    all_strikes = sorted(set(list(puts_oi) + list(calls_oi)))
    if not all_strikes:
        return 0.0, "LOW"

    min_pain = float("inf")
    mp_strike = all_strikes[len(all_strikes) // 2]

    for test in all_strikes:
        call_pain = sum(
            (test - s) * oi * 100
            for s, oi in calls_oi.items()
            if test > s and oi > 0
        )
        put_pain = sum(
            (s - test) * oi * 100
            for s, oi in puts_oi.items()
            if test < s and oi > 0
        )
        total = call_pain + put_pain
        if total < min_pain:
            min_pain = total
            mp_strike = test

    return float(mp_strike), min_pain


def fetch_gamma_for_symbol(symbol: str) -> Optional[dict]:
    """
    Fetch put walls and max pain for one symbol.

    Returns dict or None.  Raises on unexpected errors so the caller can
    surface the actual error message instead of swallowing it.
    """
    ticker = yf.Ticker(symbol)

    # ── Current price ──────────────────────────────────────────────────────
    price: Optional[float] = None
    try:
        hist = ticker.history(period="2d", auto_adjust=True)
        if not hist.empty:
            price = float(hist["Close"].iloc[-1])
    except Exception as exc:
        raise RuntimeError(f"price fetch failed: {exc}") from exc

    if not price or price <= 0:
        return None

    # ── Options dates ──────────────────────────────────────────────────────
    try:
        option_dates = ticker.options           # may raise on blocked IPs
    except Exception as exc:
        raise RuntimeError(f"options list failed: {exc}") from exc

    if not option_dates:
        return None

    targets = {
        "weekly":    7,
        "swing":    14,   # STPUT
        "long":     30,   # LTPUT
        "quarterly": 90,  # QPUT
    }

    result: dict = {
        "symbol":        symbol,
        "current_price": price,
        "put_walls":     {},
        "max_pain":      {},
    }

    for tf_name, target_days in targets.items():
        exp_date = _best_expiry(option_dates, target_days)
        if not exp_date:
            continue

        try:
            chain = ticker.option_chain(exp_date)
            puts  = chain.puts
            calls = chain.calls
        except Exception as exc:
            print(f"[gamma_simple] {symbol}/{tf_name} chain failed: {exc}",
                  file=sys.stderr)
            continue

        if puts.empty or calls.empty:
            continue

        # ── Put wall: strike with highest total OI across ALL strikes ─────
        # We look at all puts (not just those ≤ price) because the wall can
        # be ABOVE the current price when the market has already fallen through
        # it (breached = positive distance = entry zone signal).
        if not puts.empty:
            pw_idx    = puts["openInterest"].fillna(0).idxmax()
            pw_strike = float(puts.loc[pw_idx, "strike"])
            pw_dist   = (pw_strike - price) / price * 100
            result["put_walls"][tf_name] = {
                "strike":       pw_strike,
                "distance_pct": round(pw_dist, 2),
            }

        # ── Max pain ───────────────────────────────────────────────────────
        puts_oi  = dict(zip(puts["strike"].astype(float),
                            puts["openInterest"].fillna(0)))
        calls_oi = dict(zip(calls["strike"].astype(float),
                            calls["openInterest"].fillna(0)))
        mp_strike, _ = _max_pain(puts_oi, calls_oi)
        if mp_strike > 0:
            mp_dist   = (mp_strike - price) / price * 100
            abs_dist  = abs(mp_dist)
            pin_risk  = ("HIGH"   if abs_dist < 2.0
                         else "MEDIUM" if abs_dist < 5.0
                         else "LOW")
            result["max_pain"][tf_name] = {
                "strike":       mp_strike,
                "distance_pct": round(mp_dist, 2),
                "pin_risk":     pin_risk,
            }

    if not result["put_walls"] and not result["max_pain"]:
        return None

    return result
