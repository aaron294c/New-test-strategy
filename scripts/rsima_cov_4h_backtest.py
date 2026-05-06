#!/usr/bin/env python3
"""
RSI-MA + CoV Cross-Timeframe Backtest — SPY & QQQ

Compares five entry strategies at the RSI-MA <5th-percentile trigger:

  A   Daily RSI-MA < 5th pct                         (baseline, no COV)
  B   Daily RSI-MA < 5th pct + daily COV red         (existing strategy)
  C   Daily RSI-MA < 5th pct + 4H COV red            (early: daily trigger, 4H COV)
  C2  Daily RSI-MA < 5th pct + 4H COV just-turned-red ("shifting": first red 4H bar)
  D   4H RSI-MA < 5th pct   + 4H COV red            (pure 4H strategy)

Forward horizons (trading bars from entry):
  A/B/C/C2  D1, D5, D10, D21  (daily bars)
  D         3, 6, 8, 12, 34   (4H bars ≈ 12h, 24h, 32h, 48h, ~21 trading days)

Output: JSON → backend/cache/rsima_cov_4h_{TICKER}.json + printed table
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

# ── path setup ───────────────────────────────────────────────────────────────
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "backend"))

from cov_indicator import compute_cov, red_bar_mask  # noqa: E402
from enhanced_backtester import EnhancedPerformanceMatrixBacktester  # noqa: E402

# ── constants ────────────────────────────────────────────────────────────────
TICKERS        = ["SPY", "QQQ"]
THRESHOLD_5    = 5.0
THRESHOLD_10   = 10.0
THRESHOLD_15   = 15.0
THRESHOLD      = THRESHOLD_5  # default used by helpers
LOOKBACK_DAILY = 252          # 1 trading year (daily bars)
LOOKBACK_4H    = 504          # 1 trading year of half-day bars: 252 days × 2 bars/day
DAILY_HORIZONS = [1, 5, 10, 21]
# Half-day bar horizons: 2 bars = 1 trading day
# 3=12h, 6=24h, 10=D5(5 days×2bars), 12=48h, 42=D21(21 days×2bars)
H4_HORIZONS    = [3, 6, 10, 12, 42]
CACHE_DIR      = REPO / "backend" / "cache"


# ─────────────────────────────────────────────────────────────────────────────
# Indicator helpers
# ─────────────────────────────────────────────────────────────────────────────

def calc_rsi_ma(close: pd.Series, rsi_len: int = 14, ma_len: int = 14) -> pd.Series:
    """Identical pipeline to EnhancedPerformanceMatrixBacktester.calculate_rsi_ma_indicator."""
    log_ret = np.log(close / close.shift(1)).fillna(0)
    delta   = log_ret.diff()
    gains   = delta.where(delta > 0, 0)
    losses  = -delta.where(delta < 0, 0)
    avg_g   = gains.ewm(alpha=1 / rsi_len, adjust=False).mean()
    avg_l   = losses.ewm(alpha=1 / rsi_len, adjust=False).mean()
    rs      = avg_g / avg_l
    rsi     = (100 - 100 / (1 + rs)).fillna(50)
    return rsi.ewm(span=ma_len, adjust=False).mean()


def calc_percentile(series: pd.Series, lookback: int) -> np.ndarray:
    """Rolling percentile rank (0–100).  Uses numpy loop for speed."""
    vals = series.values.astype(float)
    n    = len(vals)
    out  = np.full(n, np.nan)
    for i in range(lookback - 1, n):
        window = vals[i - lookback + 1 : i + 1]
        if np.any(np.isnan(window)):
            continue
        current = window[-1]
        below   = np.sum(window[:-1] < current)
        out[i]  = below / (lookback - 1) * 100
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Data fetch
# ─────────────────────────────────────────────────────────────────────────────

def fetch_daily(ticker: str) -> pd.DataFrame:
    bt = EnhancedPerformanceMatrixBacktester(
        tickers=[ticker], lookback_period=LOOKBACK_DAILY
    )
    return bt.fetch_data(ticker, period="5y")


def fetch_half_day(ticker: str, lookback_days: int = 720) -> pd.DataFrame:
    """
    Build 2 half-day bars per trading day — matching TradingView's '4H' for US equities.

    TradingView splits the regular session (9:30am–4:00pm ET) at 1:30pm:
      AM bar : 9:30am – 1:30pm ET  (4 clock hours)
      PM bar : 1:30pm – 4:00pm ET  (2.5h; TV closes the bar at session end)

    The old resample('4h') bucketed on calendar boundaries (8am / 12pm ET),
    which mixed pre-market bars into the morning candle and split the day at
    the wrong point. This function produces clean, session-aligned bars only.
    """
    end   = datetime.now()
    start = end - timedelta(days=lookback_days)
    obj   = yf.Ticker(ticker)
    h1    = obj.history(start=start, end=end, interval="1h")
    if h1.empty:
        raise ValueError(f"No 1H data for {ticker}")

    # Convert to Eastern Time so hour comparisons are unambiguous
    idx = pd.DatetimeIndex(h1.index)
    idx = idx.tz_localize(None).tz_localize("UTC").tz_convert("America/New_York") \
          if idx.tz is None else idx.tz_convert("America/New_York")
    h1.index = idx

    # Keep only regular market hours: 9:30am–3:59pm ET
    h, m = idx.hour, idx.minute
    in_session = ((h > 9) | ((h == 9) & (m >= 30))) & (h < 16)
    h1 = h1[in_session].copy()
    if h1.empty:
        raise ValueError(f"No regular-session data for {ticker}")

    idx2 = h1.index
    # AM = before 1:30pm ET, PM = 1:30pm onwards
    is_am = (idx2.hour < 13) | ((idx2.hour == 13) & (idx2.minute < 30))
    h1["_date"]    = idx2.date
    h1["_session"] = np.where(is_am, "AM", "PM")

    bars = (
        h1.groupby(["_date", "_session"], sort=True)
        .agg(Open=("Open", "first"), High=("High", "max"),
             Low=("Low", "min"),   Close=("Close", "last"),
             Volume=("Volume", "sum"))
        .reset_index()
    )

    # Canonical timestamps: AM → date 09:30 ET, PM → date 13:30 ET
    ts = (pd.to_datetime(bars["_date"].astype(str))
          + bars["_session"].map({"AM": pd.Timedelta("9h30m"),
                                  "PM": pd.Timedelta("13h30m")}))
    bars.index = ts.dt.tz_localize("America/New_York")
    bars = bars.drop(columns=["_date", "_session"]).sort_index()

    days = len(bars["Close"].resample("1D").last().dropna())
    print(f"  Half-day bars: {len(bars)}  ({len(bars)/2/252:.1f} yr, "
          f"{len(bars)/max(days,1):.2f} bars/trading-day)")
    return bars


# ─────────────────────────────────────────────────────────────────────────────
# Alignment helpers
# ─────────────────────────────────────────────────────────────────────────────

def _strip_tz_and_normalize(dt_index) -> pd.DatetimeIndex:
    """Return midnight date index with no timezone info."""
    return pd.DatetimeIndex(dt_index).tz_localize(None).normalize()


def align_h4_to_daily(h4_bool: pd.Series, daily_index,
                      method: str = "last") -> np.ndarray:
    """
    Map half-day boolean signals onto the daily index.

    method="last" → end-of-day state  (use for "is COV currently red?")
    method="any"  → True if ANY bar on that date fired  (use for "did COV shift today?")
    """
    h4_dates   = _strip_tz_and_normalize(h4_bool.index)
    h4_by_date = pd.Series(h4_bool.values, index=h4_dates, dtype=bool)
    grp        = h4_by_date.groupby(level=0)
    h4_daily   = grp.last() if method == "last" else grp.any()

    daily_dates = _strip_tz_and_normalize(daily_index)
    aligned = h4_daily.reindex(daily_dates, fill_value=False).fillna(False)
    return aligned.values.astype(bool)


# ─────────────────────────────────────────────────────────────────────────────
# Entry finding & forward-return stats
# ─────────────────────────────────────────────────────────────────────────────

def find_entries(pct_arr: np.ndarray,
                 mask_arr: Optional[np.ndarray] = None,
                 threshold: float = THRESHOLD_5) -> List[int]:
    """Integer positions where pct <= threshold [and mask is True]."""
    entries = []
    for i, p in enumerate(pct_arr):
        if np.isnan(p) or p > threshold:
            continue
        if mask_arr is not None and not bool(mask_arr[i]):
            continue
        entries.append(i)
    return entries


def find_ladder_entries(h4_jtr_arr: np.ndarray,
                        h4_dates_naive: List,
                        daily_pct_lookup: Dict,
                        daily_threshold: float = THRESHOLD_10) -> List[int]:
    """
    Option 2 — Ladder strategy entries (half-day bar positions).

    Alert : daily RSI-MA percentile <= daily_threshold  (watch mode)
    Entry : the first half-day COV bar that turns red while alert is active

    Returns integer positions into the h4 price series so forward returns
    are tracked in half-day bars from the actual intraday entry point.
    """
    entries = []
    for i, jtr in enumerate(h4_jtr_arr):
        if not bool(jtr):
            continue
        dpct = daily_pct_lookup.get(h4_dates_naive[i], np.nan)
        if not np.isnan(dpct) and dpct <= daily_threshold:
            entries.append(i)
    return entries


def forward_stats(entry_idxs: List[int],
                  prices: np.ndarray,
                  horizons: List[int]) -> Dict:
    bucket: Dict[int, list] = {h: [] for h in horizons}
    for idx in entry_idxs:
        ep = prices[idx]
        for h in horizons:
            j = idx + h
            if j < len(prices):
                bucket[h].append(np.log(prices[j] / ep) * 100)

    out = {}
    for h in horizons:
        arr = np.array(bucket[h])
        if len(arr) == 0:
            out[h] = {"n": 0, "winrate": None, "median": None,
                      "mean": None, "p25": None, "p75": None}
        else:
            out[h] = {
                "n":       int(len(arr)),
                "winrate": float(round(100 * (arr > 0).mean(), 1)),
                "median":  float(round(float(np.median(arr)), 3)),
                "mean":    float(round(float(arr.mean()), 3)),
                "p25":     float(round(float(np.percentile(arr, 25)), 3)),
                "p75":     float(round(float(np.percentile(arr, 75)), 3)),
            }
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Per-ticker runner
# ─────────────────────────────────────────────────────────────────────────────

def run_ticker(ticker: str) -> Dict:
    print(f"\n{'='*60}\n{ticker}\n{'='*60}")

    # ── Daily data + indicators ──────────────────────────────────────────────
    daily = fetch_daily(ticker)
    if daily.empty or len(daily) < LOOKBACK_DAILY + 30:
        print(f"  Insufficient daily data ({len(daily)} bars) — skipped")
        return {}

    daily_close = daily["Close"]
    daily_rsi_ma = calc_rsi_ma(daily_close)
    daily_pct    = calc_percentile(daily_rsi_ma, LOOKBACK_DAILY)
    daily_prices = daily_close.values.astype(float)

    # Daily COV (for strategy B)
    daily_cov     = compute_cov(daily_close)
    daily_red_arr = (daily_cov["bar_color"] == "red").fillna(False).values.astype(bool)

    # ── 4H data + indicators ─────────────────────────────────────────────────
    print(f"  Fetching half-day bars (TradingView 4H) …")
    try:
        h4 = fetch_half_day(ticker, lookback_days=720)
        h4_ok = len(h4) >= LOOKBACK_4H + 30
        if not h4_ok:
            print(f"  Only {len(h4)} half-day bars — need {LOOKBACK_4H + 30} for percentile")
    except Exception as e:
        print(f"  Half-day fetch failed: {e}")
        h4_ok = False

    if h4_ok:
        h4_close   = h4["Close"]
        h4_cov     = compute_cov(h4_close)
        h4_red_raw = (h4_cov["bar_color"] == "red").fillna(False)

        # "Just turned red" = current is red AND previous was NOT red
        prev_red = h4_red_raw.shift(1, fill_value=False).fillna(False)
        h4_jtr_raw = h4_red_raw & ~prev_red

        # Align half-day signals to daily index
        # "red" → end-of-day state; "just turned red" → any bar on that date
        h4_red_for_daily = align_h4_to_daily(h4_red_raw, daily["Close"].index, method="last")
        h4_jtr_for_daily = align_h4_to_daily(h4_jtr_raw, daily["Close"].index, method="any")

        # Pure 4H indicators
        h4_rsi_ma    = calc_rsi_ma(h4_close)
        h4_pct       = calc_percentile(h4_rsi_ma, LOOKBACK_4H)
        h4_prices    = h4_close.values.astype(float)
        h4_red_arr   = h4_red_raw.values.astype(bool)
    else:
        h4_red_for_daily = np.zeros(len(daily), dtype=bool)
        h4_jtr_for_daily = np.zeros(len(daily), dtype=bool)
        h4_pct = np.full(1, np.nan)
        h4_prices  = np.array([])
        h4_red_arr = np.array([], dtype=bool)

    # ── Build daily-pct lookup keyed on naive date (for ladder) ─────────────
    daily_dates_naive = list(_strip_tz_and_normalize(daily["Close"].index))
    daily_pct_lookup  = dict(zip(daily_dates_naive, daily_pct))

    # ── 4H date list (naive) for ladder ──────────────────────────────────────
    h4_dates_naive = (list(_strip_tz_and_normalize(h4.index))
                      if h4_ok else [])

    # ── Entry sets — 5th percentile (original) ───────────────────────────────
    entries_A  = find_entries(daily_pct, threshold=THRESHOLD_5)
    entries_B  = find_entries(daily_pct, mask_arr=daily_red_arr,     threshold=THRESHOLD_5)
    entries_C  = find_entries(daily_pct, mask_arr=h4_red_for_daily,  threshold=THRESHOLD_5)
    entries_C2 = find_entries(daily_pct, mask_arr=h4_jtr_for_daily,  threshold=THRESHOLD_5)
    entries_D5 = find_entries(h4_pct,   mask_arr=h4_red_arr,         threshold=THRESHOLD_5) if h4_ok else []

    # ── Entry sets — 10th percentile ─────────────────────────────────────────
    entries_A10  = find_entries(daily_pct, threshold=THRESHOLD_10)
    entries_C10  = find_entries(daily_pct, mask_arr=h4_red_for_daily, threshold=THRESHOLD_10)
    entries_D10  = find_entries(h4_pct,   mask_arr=h4_red_arr,        threshold=THRESHOLD_10) if h4_ok else []

    # ── Entry sets — 15th percentile ─────────────────────────────────────────
    entries_A15  = find_entries(daily_pct, threshold=THRESHOLD_15)
    entries_C15  = find_entries(daily_pct, mask_arr=h4_red_for_daily, threshold=THRESHOLD_15)
    entries_D15  = find_entries(h4_pct,   mask_arr=h4_red_arr,        threshold=THRESHOLD_15) if h4_ok else []

    # ── Entry sets — Ladder ───────────────────────────────────────────────────
    h4_jtr_arr = h4_jtr_raw.values.astype(bool) if h4_ok else np.array([], dtype=bool)
    entries_E   = find_ladder_entries(h4_jtr_arr, h4_dates_naive, daily_pct_lookup,
                                      daily_threshold=THRESHOLD_10) if h4_ok else []
    entries_E5  = find_ladder_entries(h4_jtr_arr, h4_dates_naive, daily_pct_lookup,
                                      daily_threshold=THRESHOLD_5)  if h4_ok else []

    print(f"  5th  →  A={len(entries_A)}  C={len(entries_C)}  D={len(entries_D5)}")
    print(f"  10th →  A={len(entries_A10)}  C={len(entries_C10)}  D={len(entries_D10)}")
    print(f"  15th →  A={len(entries_A15)}  C={len(entries_C15)}  D={len(entries_D15)}")
    print(f"  Ladder → E(10th)={len(entries_E)}  E5(5th)={len(entries_E5)}")

    # ── Forward-return stats ─────────────────────────────────────────────────
    stats_A   = forward_stats(entries_A,   daily_prices, DAILY_HORIZONS)
    stats_B   = forward_stats(entries_B,   daily_prices, DAILY_HORIZONS)
    stats_C   = forward_stats(entries_C,   daily_prices, DAILY_HORIZONS)
    stats_C2  = forward_stats(entries_C2,  daily_prices, DAILY_HORIZONS)
    stats_D5  = forward_stats(entries_D5,  h4_prices, H4_HORIZONS) if h4_ok else {}

    stats_A10 = forward_stats(entries_A10, daily_prices, DAILY_HORIZONS)
    stats_C10 = forward_stats(entries_C10, daily_prices, DAILY_HORIZONS)
    stats_D10 = forward_stats(entries_D10, h4_prices, H4_HORIZONS) if h4_ok else {}

    stats_A15 = forward_stats(entries_A15, daily_prices, DAILY_HORIZONS)
    stats_C15 = forward_stats(entries_C15, daily_prices, DAILY_HORIZONS)
    stats_D15 = forward_stats(entries_D15, h4_prices, H4_HORIZONS) if h4_ok else {}

    stats_E   = forward_stats(entries_E,   h4_prices, H4_HORIZONS) if h4_ok else {}
    stats_E5  = forward_stats(entries_E5,  h4_prices, H4_HORIZONS) if h4_ok else {}

    result = {
        "ticker":     ticker,
        "daily_bars": int(len(daily)),
        "h4_bars":    int(len(h4)) if h4_ok else 0,
        "strategies_5th": {
            "A_daily_rsima_only":          {"entries": len(entries_A),   "stats": stats_A,  "horizons": "daily"},
            "B_daily_rsima_daily_cov":     {"entries": len(entries_B),   "stats": stats_B,  "horizons": "daily"},
            "C_daily_rsima_4h_cov_red":    {"entries": len(entries_C),   "stats": stats_C,  "horizons": "daily"},
            "C2_daily_rsima_4h_cov_shift": {"entries": len(entries_C2),  "stats": stats_C2, "horizons": "daily"},
            "D_4h_rsima_4h_cov_red":       {"entries": len(entries_D5),  "stats": stats_D5, "horizons": "4h_bars"},
        },
        "strategies_10th": {
            "A_daily_rsima_only":          {"entries": len(entries_A10), "stats": stats_A10, "horizons": "daily"},
            "C_daily_rsima_4h_cov_red":    {"entries": len(entries_C10), "stats": stats_C10, "horizons": "daily"},
            "D_4h_rsima_4h_cov_red":       {"entries": len(entries_D10), "stats": stats_D10, "horizons": "4h_bars"},
        },
        "strategies_15th": {
            "A_daily_rsima_only":          {"entries": len(entries_A15), "stats": stats_A15, "horizons": "daily"},
            "C_daily_rsima_4h_cov_red":    {"entries": len(entries_C15), "stats": stats_C15, "horizons": "daily"},
            "D_4h_rsima_4h_cov_red":       {"entries": len(entries_D15), "stats": stats_D15, "horizons": "4h_bars"},
        },
        "strategies_ladder": {
            "E_ladder_10th_alert":  {"entries": len(entries_E),  "stats": stats_E,  "horizons": "4h_bars"},
            "E5_ladder_5th_alert":  {"entries": len(entries_E5), "stats": stats_E5, "horizons": "4h_bars"},
        },
        "horizon_labels": {
            "daily":   {str(h): f"D{h}"                                for h in DAILY_HORIZONS},
            "4h_bars": {str(h): lbl for h, lbl in {3:"12h",6:"24h",10:"D5",12:"48h",42:"D21"}.items()},
        },
    }
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Pretty-print
# ─────────────────────────────────────────────────────────────────────────────

def _fmt(v, spec="{:+.2f}") -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return spec.format(v)


def _h4_block(label: str, s: Dict, h4_labels: Dict) -> None:
    st = s["stats"]
    n  = s["entries"]
    print(f"\n  {label}  —  {n} entries  (half-day bars from entry)")
    if n == 0:
        print(f"  (no entries)")
        return
    print(f"  {'Horizon':<8}  {'n':>4}  {'Win%':>6}  {'Median%':>8}  {'Mean%':>8}  {'P25%':>7}  {'P75%':>7}")
    print(f"  {'-'*8}  {'----':>4}  {'-'*6}  {'-'*8}  {'-'*8}  {'-'*7}  {'-'*7}")
    for h in H4_HORIZONS:
        row = st.get(h, {})
        lbl = h4_labels.get(h, f"{h}b")
        print(f"  {lbl:<8}  {row.get('n',0):>4}  "
              f"{_fmt(row.get('winrate'), '{:.1f}'):>6}  "
              f"{_fmt(row.get('median'),  '{:+.2f}'):>8}  "
              f"{_fmt(row.get('mean'),    '{:+.2f}'):>8}  "
              f"{_fmt(row.get('p25'),     '{:+.2f}'):>7}  "
              f"{_fmt(row.get('p75'),     '{:+.2f}'):>7}")


def _daily_block(rows: List[tuple]) -> None:
    print(f"\n  {'Strategy':<38}  {'n':>4}  {'D5 WR%':>7}  {'D10 WR%':>8}  "
          f"{'D21 WR%':>8}  {'D5 med%':>8}  {'D21 med%':>9}")
    print(f"  {'-'*38}  {'----':>4}  {'-'*7}  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*9}")
    for name, s in rows:
        st = s["stats"]
        n  = s["entries"]
        def wr(h):  return _fmt(st.get(h, {}).get("winrate"), "{:.1f}")
        def med(h): return _fmt(st.get(h, {}).get("median"),  "{:+.2f}")
        print(f"  {name:<38}  {n:>4}  {wr(5):>7}  {wr(10):>8}  {wr(21):>8}  {med(5):>8}  {med(21):>9}")


def _threshold_sweep(r: Dict, strategy_key: str, h4_labels: Dict) -> None:
    """Print a 3-row comparison across <5 / <10 / <15 for one strategy."""
    is_h4 = r["strategies_5th"][strategy_key]["horizons"] == "4h_bars"
    horizons = H4_HORIZONS if is_h4 else DAILY_HORIZONS

    # Header
    if is_h4:
        cols = [h4_labels[h] for h in horizons]
        print(f"\n  {'Threshold':<10}  {'n':>4}  " +
              "  ".join(f"{'WR '+c:>8}" for c in cols) +
              "  " + "  ".join(f"{'med '+c:>8}" for c in cols))
        print(f"  {'-'*10}  {'----':>4}  " +
              "  ".join(f"{'--------':>8}" for _ in cols) +
              "  " + "  ".join(f"{'--------':>8}" for _ in cols))
    else:
        print(f"\n  {'Threshold':<10}  {'n':>4}  {'D5 WR%':>7}  {'D10 WR%':>8}  "
              f"{'D21 WR%':>8}  {'D5 med%':>8}  {'D21 med%':>9}")
        print(f"  {'-'*10}  {'----':>4}  {'-'*7}  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*9}")

    for label, key in [("<5th", "strategies_5th"), ("<10th", "strategies_10th"), ("<15th", "strategies_15th")]:
        s  = r[key][strategy_key]
        st = s["stats"]
        n  = s["entries"]
        if is_h4:
            wrs  = "  ".join(f"{_fmt(st.get(h,{}).get('winrate'), '{:.1f}'):>8}" for h in horizons)
            meds = "  ".join(f"{_fmt(st.get(h,{}).get('median'),  '{:+.2f}'):>8}" for h in horizons)
            print(f"  {label:<10}  {n:>4}  {wrs}  {meds}")
        else:
            def wr(h):  return _fmt(st.get(h, {}).get("winrate"), "{:.1f}")
            def med(h): return _fmt(st.get(h, {}).get("median"),  "{:+.2f}")
            print(f"  {label:<10}  {n:>4}  {wr(5):>7}  {wr(10):>8}  {wr(21):>8}  {med(5):>8}  {med(21):>9}")


def print_results(results: List[Dict]) -> None:
    h4_labels = {3: "12h", 6: "24h", 10: "D5", 12: "48h", 42: "D21"}

    for r in results:
        if not r:
            continue
        t = r["ticker"]
        print(f"\n{'━'*72}")
        print(f"  {t}  |  {r['daily_bars']} daily bars  |  {r['h4_bars']} half-day bars")
        print(f"{'━'*72}")

        s5  = r["strategies_5th"]
        s10 = r["strategies_10th"]
        s15 = r["strategies_15th"]
        sl  = r["strategies_ladder"]

        # ── Strategy A: daily RSI-MA only (reference baseline) ───────────────
        print(f"\n  [A] Daily RSI-MA only — threshold sweep")
        _threshold_sweep(r, "A_daily_rsima_only", h4_labels)

        # ── Strategy C: daily RSI-MA + 4H COV red ────────────────────────────
        print(f"\n  [C] Daily RSI-MA + 4H COV red — threshold sweep")
        _threshold_sweep(r, "C_daily_rsima_4h_cov_red", h4_labels)

        # ── Strategy D: 4H RSI-MA + 4H COV red (KEY) ─────────────────────────
        print(f"\n  [D] 4H RSI-MA + 4H COV red — threshold sweep  ← primary strategy")
        _threshold_sweep(r, "D_4h_rsima_4h_cov_red", h4_labels)

        # ── 5th pct detail block for reference ────────────────────────────────
        print(f"\n  [D@5 detail]")
        _h4_block("D@5", s5["D_4h_rsima_4h_cov_red"], h4_labels)
        print(f"\n  [D@10 detail]")
        _h4_block("D@10", s10["D_4h_rsima_4h_cov_red"], h4_labels)
        print(f"\n  [D@15 detail]")
        _h4_block("D@15", s15["D_4h_rsima_4h_cov_red"], h4_labels)

        # ── Ladder ────────────────────────────────────────────────────────────
        print(f"\n  [Ladder] Daily alert → 4H COV first-red entry")
        _h4_block("E  (10th alert)", sl["E_ladder_10th_alert"], h4_labels)
        _h4_block("E5 (5th alert)",  sl["E5_ladder_5th_alert"], h4_labels)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    all_results = []

    for ticker in TICKERS:
        try:
            result = run_ticker(ticker)
            if result:
                all_results.append(result)
                out = CACHE_DIR / f"rsima_cov_4h_{ticker}.json"
                out.write_text(json.dumps(result, indent=2, default=str))
                print(f"  Saved → {out.name}")
        except Exception as e:
            print(f"  ERROR on {ticker}: {e}")
            import traceback; traceback.print_exc()

    print_results(all_results)
    print(f"\nDone in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
