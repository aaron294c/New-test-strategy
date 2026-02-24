"""
Swing Framework API - Real Historical Trade Data

Provides comprehensive data for all tickers including REAL historical trades
from backtesting, not simulated/fake data.
"""

import asyncio
import json
import os
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone, date, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from scipy.stats import norm
import pandas as pd
import numpy as np
import yfinance as yf
from zoneinfo import ZoneInfo
from enhanced_backtester import EnhancedPerformanceMatrixBacktester
from macdv_calculator import MACDVCalculator
from macdv_d7_band_stats import RSI_BANDS as MACDV_D7_RSI_BANDS, get_cached_macdv_d7_band_stats
from macdv_reference_lookup import MACDVReferenceLookup
from stock_statistics import (
    STOCK_METADATA,
    NVDA_4H_DATA, NVDA_DAILY_DATA,
    MSFT_4H_DATA, MSFT_DAILY_DATA,
    GOOGL_4H_DATA, GOOGL_DAILY_DATA,
    AAPL_4H_DATA, AAPL_DAILY_DATA,
    TSLA_4H_DATA, TSLA_DAILY_DATA,
    NFLX_4H_DATA, NFLX_DAILY_DATA,
    AVGO_4H_DATA, AVGO_DAILY_DATA,
    XOM_4H_DATA, XOM_DAILY_DATA,
    CVX_4H_DATA, CVX_DAILY_DATA,
    JPM_4H_DATA, JPM_DAILY_DATA,
    BAC_4H_DATA, BAC_DAILY_DATA,
    LLY_4H_DATA, LLY_DAILY_DATA,
    UNH_4H_DATA, UNH_DAILY_DATA,
    OXY_4H_DATA, OXY_DAILY_DATA,
    TSM_4H_DATA, TSM_DAILY_DATA,
    WMT_4H_DATA, WMT_DAILY_DATA,
    GLD_4H_DATA, GLD_DAILY_DATA,
    SLV_4H_DATA, SLV_DAILY_DATA,
    COST_4H_DATA, COST_DAILY_DATA,
    USDGBP_4H_DATA, USDGBP_DAILY_DATA,
    US10_4H_DATA, US10_DAILY_DATA
)
from percentile_forward_4h import fetch_4h_data, calculate_rsi_ma_4h
from ticker_utils import resolve_yahoo_symbol

router = APIRouter(prefix="/api/swing-framework", tags=["swing-framework"])

# In-memory cache for backtest cohort statistics
# Avoids re-running expensive backtests on every current-state request
_cohort_stats_cache: Dict = {}
_cache_timestamp: datetime | None = None
_cache_ttl_seconds = 3600  # 1 hour TTL

_current_state_cache: Dict | None = None
_current_state_cache_timestamp: datetime | None = None
_current_state_cache_ttl_seconds = 60  # 1 minute TTL
_current_state_lock = asyncio.Lock()

_current_state_4h_cache: Dict | None = None
_current_state_4h_cache_timestamp: datetime | None = None
_current_state_4h_cache_ttl_seconds = 60  # 1 minute TTL
_current_state_4h_lock = asyncio.Lock()

_current_state_enriched_cache: Dict | None = None
_current_state_enriched_cache_timestamp: datetime | None = None
_current_state_enriched_cache_ttl_seconds = 60  # 1 minute TTL
_current_state_enriched_lock = asyncio.Lock()

_macdv_daily_cache: Dict[str, Dict[str, Any]] | None = None
_macdv_daily_cache_key: str | None = None
_macdv_daily_cache_timestamp: datetime | None = None
_macdv_daily_cache_ttl_seconds = 60  # 1 minute TTL (match dashboard refresh cadence)
_macdv_daily_lock = asyncio.Lock()

_macdv_d7_lock = asyncio.Lock()

_STATIC_SNAPSHOT_DIR = Path(__file__).resolve().parent / "static_snapshots" / "swing_framework"
_MIDDAY_SNAPSHOT_DIR = Path(__file__).resolve().parent / "cache" / "midday_snapshots"
_MIDDAY_SNAPSHOT_TZ = os.getenv("SWING_MIDDAY_SNAPSHOT_TZ", "America/New_York")

# Midday window configuration (Eastern Time)
_MIDDAY_WINDOW_START_HOUR = 11
_MIDDAY_WINDOW_START_MINUTE = 30
_MIDDAY_WINDOW_END_HOUR = 12
_MIDDAY_WINDOW_END_MINUTE = 30


def _is_midday_window(now_utc: datetime | None = None) -> bool:
    """
    Check if current time is within the midday snapshot window (11:30 AM - 12:30 PM ET).
    This window is when we automatically capture midday snapshots.
    """
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)
    try:
        tz = ZoneInfo(_MIDDAY_SNAPSHOT_TZ)
    except Exception:
        tz = timezone.utc
    local_time = now_utc.astimezone(tz)

    # Check if it's a weekday (Mon=0, Sun=6)
    if local_time.weekday() >= 5:
        return False

    # Check time window
    current_minutes = local_time.hour * 60 + local_time.minute
    start_minutes = _MIDDAY_WINDOW_START_HOUR * 60 + _MIDDAY_WINDOW_START_MINUTE
    end_minutes = _MIDDAY_WINDOW_END_HOUR * 60 + _MIDDAY_WINDOW_END_MINUTE

    return start_minutes <= current_minutes <= end_minutes


def _should_auto_save_midday_snapshot(timeframe: str, now_utc: datetime | None = None) -> bool:
    """
    Determine if we should automatically save a midday snapshot.
    Returns True if:
    1. It's within the midday window
    2. No snapshot exists for today yet
    """
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)

    if not _is_midday_window(now_utc):
        return False

    market_day = _get_market_date(now_utc)
    path = _midday_snapshot_path(timeframe, market_day)

    return not path.exists()


def _get_market_date(now_utc: datetime) -> date:
    try:
        tz = ZoneInfo(_MIDDAY_SNAPSHOT_TZ)
    except Exception:
        tz = timezone.utc
    return now_utc.astimezone(tz).date()


def _previous_trading_day(day: date) -> date:
    prev = day - timedelta(days=1)
    while prev.weekday() >= 5:  # Sat/Sun
        prev -= timedelta(days=1)
    return prev


def _midday_snapshot_path(timeframe: str, market_date: date) -> Path:
    safe_timeframe = "4h" if timeframe in {"4h", "4hour"} else "daily"
    return _MIDDAY_SNAPSHOT_DIR / safe_timeframe / f"{market_date.isoformat()}.json"


def _load_midday_snapshot(timeframe: str, market_date: date) -> Dict[str, Any] | None:
    path = _midday_snapshot_path(timeframe, market_date)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        if isinstance(payload, dict):
            return payload
    except Exception as e:
        print(f"  Failed to load midday snapshot {path}: {e}")
    return None


def _save_midday_snapshot(
    timeframe: str,
    market_date: date,
    percentiles: Dict[str, float],
    captured_at_utc: datetime,
    prices: Dict[str, float] | None = None,
    overwrite: bool = False,
) -> bool:
    path = _midday_snapshot_path(timeframe, market_date)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        return False
    payload = {
        "captured_at": captured_at_utc.replace(microsecond=0).isoformat(),
        "market_date": market_date.isoformat(),
        "timeframe": "4h" if timeframe in {"4h", "4hour"} else "daily",
        "percentiles": percentiles,
        "prices": prices or {},
    }
    try:
        with path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)
        return True
    except Exception as e:
        print(f"  Failed to save midday snapshot {path}: {e}")
        return False


def _compute_historical_prev_midday(tickers: List[str], prev_day: date, timeframe: str) -> Dict[str, Dict[str, Any]]:
    """
    Fallback: compute previous midday percentiles from historical data when no snapshot exists.
    Returns dict of ticker -> {"percentile": float, "price": float} for the prev_day close.
    """
    result: Dict[str, Dict[str, Any]] = {}
    LOOKBACK_PERIOD = 252  # 1 trading year

    for ticker in tickers:
        try:
            yahoo_ticker = resolve_yahoo_symbol(ticker)
            # Fetch data up to prev_day
            end_date = prev_day + timedelta(days=1)
            start_date = prev_day - timedelta(days=500)  # Enough for lookback
            data = yf.download(
                yahoo_ticker,
                start=start_date.isoformat(),
                end=end_date.isoformat(),
                progress=False,
                auto_adjust=True,
                multi_level_index=False,
            )
            if data.empty or len(data) < LOOKBACK_PERIOD:
                continue

            # Filter to only include data up to prev_day
            prev_day_datetime = pd.Timestamp(prev_day)
            data = data[data.index <= prev_day_datetime]
            if data.empty or len(data) < LOOKBACK_PERIOD:
                continue

            # Calculate RSI-MA indicator using a temporary backtester
            backtester = EnhancedPerformanceMatrixBacktester(tickers=[ticker])
            indicator = backtester.calculate_rsi_ma_indicator(data)
            if indicator.empty:
                continue

            # Calculate percentile rank at the end (which is prev_day)
            lookback = LOOKBACK_PERIOD
            if len(indicator) >= lookback:
                window = indicator.iloc[-lookback:]
                current_value = indicator.iloc[-1]
                percentile = (window < current_value).sum() / lookback * 100
                price = float(data['Close'].iloc[-1])
                result[ticker] = {"percentile": percentile, "price": price}
        except Exception as e:
            print(f"  Fallback compute failed for {ticker}: {e}")
            continue
    return result


def _augment_with_prev_midday_snapshot(response: Dict[str, Any], timeframe: str) -> Dict[str, Any]:
    """
    Annotate `market_state` entries with the previous trading day's saved "midday" percentile,
    price, and price change percentage. If no snapshot exists, falls back to computing from
    historical data.
    """
    now_utc = datetime.now(timezone.utc)
    market_day = _get_market_date(now_utc)
    prev_day = _previous_trading_day(market_day)

    snapshot = _load_midday_snapshot(timeframe, prev_day)
    prev_percentiles: Dict[str, Any] = {}
    prev_prices: Dict[str, Any] = {}
    captured_at: str | None = None
    from_fallback = False

    if snapshot:
        prev_percentiles = snapshot.get("percentiles") or {}
        prev_prices = snapshot.get("prices") or {}
        captured_at = snapshot.get("captured_at")
    else:
        # Fallback: compute from historical data
        tickers = [
            s.get("ticker") for s in (response.get("market_state") or [])
            if isinstance(s, dict) and s.get("ticker")
        ]
        if tickers:
            print(f"  No midday snapshot for {prev_day}, computing from historical data...")
            fallback_data = _compute_historical_prev_midday(tickers, prev_day, timeframe)
            for ticker, data in fallback_data.items():
                prev_percentiles[ticker] = data.get("percentile")
                prev_prices[ticker] = data.get("price")
            from_fallback = True
            captured_at = f"{prev_day.isoformat()}T16:00:00 (close, computed)"

    for state in response.get("market_state", []) or []:
        if not isinstance(state, dict):
            continue
        ticker = state.get("ticker")

        # Previous percentile
        prev_pct = prev_percentiles.get(ticker) if ticker else None
        if prev_pct is not None:
            try:
                prev_pct = float(prev_pct)
            except Exception:
                prev_pct = None
        state["prev_midday_percentile"] = prev_pct

        # Percentile change
        state["change_since_prev_midday"] = (
            float(state["current_percentile"]) - prev_pct
            if prev_pct is not None and state.get("current_percentile") is not None
            else None
        )

        # Previous price and price change percentage
        prev_price = prev_prices.get(ticker) if ticker else None
        if prev_price is not None:
            try:
                prev_price = float(prev_price)
            except Exception:
                prev_price = None
        state["prev_midday_price"] = prev_price

        # Calculate price change percentage
        current_price = state.get("current_price")
        if prev_price is not None and current_price is not None:
            try:
                price_change_pct = ((float(current_price) - prev_price) / prev_price) * 100
                state["price_change_pct"] = price_change_pct
            except (ZeroDivisionError, ValueError):
                state["price_change_pct"] = None
        else:
            state["price_change_pct"] = None

    response["prev_midday_snapshot"] = {
        "market_date": prev_day.isoformat(),
        "captured_at": captured_at,
        "timeframe": "4h" if timeframe in {"4h", "4hour"} else "daily",
        "from_fallback": from_fallback,
    }
    return response


def _has_macdv_daily(response: Dict[str, Any]) -> bool:
    market_state = response.get("market_state")
    if not isinstance(market_state, list) or not market_state:
        return False
    first = market_state[0]
    return isinstance(first, dict) and ("macdv_daily" in first or "macdv_daily_trend" in first)


def _calculate_macdv_momentum_analysis(macdv_series: pd.Series) -> Dict[str, Any]:
    """
    Calculate MACD-V momentum analysis including deltas, trend, days in zone, and next threshold.

    Args:
        macdv_series: Series of MACD-V values (most recent last)

    Returns:
        Dict with momentum metrics
    """
    if len(macdv_series) < 2:
        return {
            "macdv_delta_1d": None,
            "macdv_delta_5d": None,
            "macdv_delta_10d": None,
            "macdv_trend": None,
            "macdv_trend_label": None,
            "days_in_zone": None,
            "next_threshold": None,
            "next_threshold_distance": None,
        }

    current_val = macdv_series.iloc[-1]

    # Calculate deltas
    delta_1d = current_val - macdv_series.iloc[-2] if len(macdv_series) >= 2 else None

    # 5-day average change rate: (current - 5_days_ago) / 5
    delta_5d = None
    if len(macdv_series) >= 6:
        delta_5d = (current_val - macdv_series.iloc[-6]) / 5

    # 10-day average change rate: (current - 10_days_ago) / 10
    delta_10d = None
    if len(macdv_series) >= 11:
        delta_10d = (current_val - macdv_series.iloc[-11]) / 10

    # Trend classification based on 5-day average delta
    trend = None
    trend_label = None
    if delta_5d is not None:
        if delta_5d > 5:
            trend = "↗↗"
            trend_label = "ACC"  # Accelerating upward
        elif delta_5d > 2:
            trend = "↗"
            trend_label = "STR"  # Steady rise
        elif delta_5d > -2:
            trend = "→↗" if delta_5d > 0 else "→"
            trend_label = "FLAT"  # Flattening
        elif delta_5d > -5:
            trend = "↘"
            trend_label = "DECEL"  # Decelerating
        else:
            trend = "↘↘"
            trend_label = "CRASH"  # Accelerating downward

    # Define zone thresholds
    thresholds = [-100, -50, 50, 100]

    # Determine current zone
    current_zone = None
    for i, threshold in enumerate(thresholds):
        if current_val < threshold:
            current_zone = i
            break
    if current_zone is None:
        current_zone = len(thresholds)

    # Count days in current zone
    days_in_zone = 1
    for i in range(len(macdv_series) - 2, -1, -1):
        val = macdv_series.iloc[i]
        # Check if this value is in the same zone
        val_zone = None
        for j, threshold in enumerate(thresholds):
            if val < threshold:
                val_zone = j
                break
        if val_zone is None:
            val_zone = len(thresholds)

        if val_zone == current_zone:
            days_in_zone += 1
        else:
            break

    # Calculate next threshold
    next_threshold = None
    next_threshold_distance = None

    if pd.notna(current_val):
        # Find closest threshold
        distances = [(abs(current_val - t), t) for t in thresholds]
        distances.sort()
        closest = distances[0][1]
        distance = current_val - closest

        # Determine if approaching or receding
        if abs(distance) <= 10:  # Within 10 points of threshold
            next_threshold = closest
            next_threshold_distance = distance

    return {
        "macdv_delta_1d": round(delta_1d, 2) if delta_1d is not None else None,
        "macdv_delta_5d": round(delta_5d, 2) if delta_5d is not None else None,
        "macdv_delta_10d": round(delta_10d, 2) if delta_10d is not None else None,
        "macdv_trend": trend,
        "macdv_trend_label": trend_label,
        "days_in_zone": days_in_zone,
        "next_threshold": next_threshold,
        "next_threshold_distance": round(next_threshold_distance, 1) if next_threshold_distance is not None else None,
    }


async def _get_macdv_daily_map(display_tickers: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Return a mapping of display ticker -> MACD-V metrics including momentum analysis.
    Now includes: macdv_daily, trend, delta_1d, delta_5d, delta_10d, days_in_zone, next_threshold
    """
    global _macdv_daily_cache, _macdv_daily_cache_key, _macdv_daily_cache_timestamp

    key = ",".join(sorted({t.strip().upper() for t in display_tickers if isinstance(t, str) and t.strip()}))

    if (
        _macdv_daily_cache is not None
        and _macdv_daily_cache_key == key
        and _is_cache_valid(_macdv_daily_cache, _macdv_daily_cache_timestamp, _macdv_daily_cache_ttl_seconds)
    ):
        return dict(_macdv_daily_cache)

    async with _macdv_daily_lock:
        if (
            _macdv_daily_cache is not None
            and _macdv_daily_cache_key == key
            and _is_cache_valid(_macdv_daily_cache, _macdv_daily_cache_timestamp, _macdv_daily_cache_ttl_seconds)
        ):
            return dict(_macdv_daily_cache)

        display_to_yahoo: Dict[str, str] = {t: resolve_yahoo_symbol(t) for t in display_tickers}
        yahoo_to_display: Dict[str, str] = {y: d for d, y in display_to_yahoo.items()}
        yahoo_symbols = sorted(set(display_to_yahoo.values()))

        out: Dict[str, Dict[str, Any]] = {
            t: {
                "macdv_daily": None,
                "macdv_daily_trend": None,
                "macdv_delta_1d": None,
                "macdv_delta_5d": None,
                "macdv_delta_10d": None,
                "macdv_trend": None,
                "macdv_trend_label": None,
                "days_in_zone": None,
                "next_threshold": None,
                "next_threshold_distance": None,
            }
            for t in display_tickers
        }

        try:
            calculator = MACDVCalculator(fast_length=12, slow_length=26, signal_length=9, atr_length=26)

            # Fetch historical data for momentum analysis (need at least 50 days for ATR calculation + 10 days lookback)
            for yahoo_symbol in yahoo_symbols:
                try:
                    # Download 60 days of data to ensure we have enough for calculations
                    df = yf.download(
                        yahoo_symbol,
                        period="60d",
                        interval="1d",
                        progress=False,
                        auto_adjust=True
                    )

                    if df.empty:
                        continue

                    # Normalize column names
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = [col[0].lower() if isinstance(col, tuple) else str(col).lower() for col in df.columns]
                    else:
                        df.columns = [str(c).lower() for c in df.columns]

                    # Calculate MACD-V
                    df = calculator.calculate_macdv(df)

                    # Get latest value
                    latest = df.iloc[-1]

                    # Get historical MACD-V series for momentum analysis (last 15 days)
                    macdv_series = df['macdv_val'].tail(15)
                    momentum = _calculate_macdv_momentum_analysis(macdv_series)

                    display = yahoo_to_display.get(yahoo_symbol)
                    if display:
                        out[display] = {
                            "macdv_daily": float(latest['macdv_val']) if pd.notna(latest['macdv_val']) else None,
                            "macdv_daily_trend": str(latest['macdv_trend']),
                            "macdv_delta_1d": momentum["macdv_delta_1d"],
                            "macdv_delta_5d": momentum["macdv_delta_5d"],
                            "macdv_delta_10d": momentum["macdv_delta_10d"],
                            "macdv_trend": momentum["macdv_trend"],
                            "macdv_trend_label": momentum["macdv_trend_label"],
                            "days_in_zone": momentum["days_in_zone"],
                            "next_threshold": momentum["next_threshold"],
                            "next_threshold_distance": momentum["next_threshold_distance"],
                        }
                except Exception as e:
                    print(f"  Error processing MACD-V for {yahoo_symbol}: {e}")
                    continue

        except Exception as e:
            print(f"  MACD-V daily augmentation failed: {e}")

        _macdv_daily_cache = dict(out)
        _macdv_daily_cache_key = key
        _macdv_daily_cache_timestamp = datetime.now(timezone.utc)
        return dict(out)


async def _augment_with_macdv_daily(response: Dict[str, Any]) -> Dict[str, Any]:
    market_state = response.get("market_state")
    if not isinstance(market_state, list) or not market_state:
        return response

    display_tickers: List[str] = [
        s.get("ticker")
        for s in market_state
        if isinstance(s, dict) and isinstance(s.get("ticker"), str)
    ]
    if not display_tickers:
        return response

    macdv_map = await _get_macdv_daily_map(display_tickers)
    for state in market_state:
        if not isinstance(state, dict):
            continue
        ticker = state.get("ticker")
        if not isinstance(ticker, str):
            continue
        entry = macdv_map.get(ticker) or {}
        state["macdv_daily"] = entry.get("macdv_daily")
        state["macdv_daily_trend"] = entry.get("macdv_daily_trend")
        state["macdv_delta_1d"] = entry.get("macdv_delta_1d")
        state["macdv_delta_5d"] = entry.get("macdv_delta_5d")
        state["macdv_delta_10d"] = entry.get("macdv_delta_10d")
        state["macdv_trend"] = entry.get("macdv_trend")
        state["macdv_trend_label"] = entry.get("macdv_trend_label")
        state["days_in_zone"] = entry.get("days_in_zone")
        state["next_threshold"] = entry.get("next_threshold")
        state["next_threshold_distance"] = entry.get("next_threshold_distance")

    return response


def _rsi_band_label(pct: float | int | None) -> str | None:
    if pct is None:
        return None
    try:
        val = float(pct)
    except Exception:
        return None

    if not np.isfinite(val):
        return None

    # Mirror band masks used in analysis: [min, max) with a safe clamp at 100.
    val = min(max(val, 0.0), 99.999)
    for rlo, rhi, label in MACDV_D7_RSI_BANDS:
        if val >= float(rlo) and val < float(rhi):
            return str(label)
    return str(MACDV_D7_RSI_BANDS[-1][2]) if MACDV_D7_RSI_BANDS else None


async def _augment_with_macdv_d7_stats(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add D7 forward-return stats for tickers whose current MACD-V daily value is >120.

    Stats are pulled from a cached, precomputed table:
    - Entry condition: MACD-V>120 AND RSI-%ile in the given band
    - Horizon: D7
    - RSI bands: same buckets as the MACD-V × RSI (D7) tab

    For now we only attach these fields for the Daily Live Market State table (not 4H),
    because the RSI-%ile band should be based on the daily RSI-MA percentile.
    """
    if response.get("timeframe") == "4h":
        return response

    market_state = response.get("market_state")
    if not isinstance(market_state, list) or not market_state:
        return response

    tickers: List[str] = [
        s.get("ticker")
        for s in market_state
        if isinstance(s, dict) and isinstance(s.get("ticker"), str)
    ]
    if not tickers:
        return response

    try:
        async with _macdv_d7_lock:
            payload = await asyncio.to_thread(
                get_cached_macdv_d7_band_stats,
                tickers,
                period="10y",
                pct_lookback=252,
                horizon=7,
                macdv_lo=120.0,
                ttl_seconds=7 * 24 * 3600,
                force_refresh=False,
            )
    except Exception as e:
        print(f"  Warning: Could not load MACD-V D7 stats: {e}")
        return response

    table = payload.get("table") if isinstance(payload, dict) else None
    if not isinstance(table, dict):
        return response

    horizon = None
    params = payload.get("params") if isinstance(payload, dict) else None
    if isinstance(params, dict):
        horizon = params.get("horizon")

    for state in market_state:
        if not isinstance(state, dict):
            continue

        # Defaults
        state["macdv_d7_win_rate"] = None
        state["macdv_d7_mean_return"] = None
        state["macdv_d7_median_return"] = None
        state["macdv_d7_n"] = None
        state["macdv_d7_rsi_band"] = None
        if horizon is not None:
            state["macdv_d7_horizon"] = horizon

        macdv_daily = state.get("macdv_daily")
        if macdv_daily is None:
            continue
        try:
            macdv_daily_val = float(macdv_daily)
        except Exception:
            continue
        if not np.isfinite(macdv_daily_val) or macdv_daily_val <= 120.0:
            continue

        ticker = state.get("ticker")
        if not isinstance(ticker, str):
            continue

        # Prefer daily RSI percentile computed with 252 lookback (matches D7 stats),
        # fall back to the displayed percentile if missing.
        band_pct = state.get("rsi_percentile_252", state.get("current_percentile"))
        band_label = _rsi_band_label(band_pct)
        if band_label is None:
            continue

        stats_row = table.get(ticker)
        if not isinstance(stats_row, dict):
            continue
        stats = stats_row.get(band_label)
        if not isinstance(stats, dict):
            continue

        state["macdv_d7_rsi_band"] = band_label
        state["macdv_d7_n"] = stats.get("n")
        state["macdv_d7_win_rate"] = stats.get("win_rate")
        state["macdv_d7_mean_return"] = stats.get("mean")
        state["macdv_d7_median_return"] = stats.get("median")

    return response


# ── Momentum Regime (MACD-V > 100) D7 Lookup ────────────────────────────────

_momentum_d7_stats: Dict[str, Dict[str, Any]] | None = None

def _load_momentum_d7_stats() -> Dict[str, Dict[str, Any]]:
    """Load precomputed momentum regime D7 stats from JSON."""
    global _momentum_d7_stats
    if _momentum_d7_stats is not None:
        return _momentum_d7_stats
    path = Path(__file__).resolve().parent / "momentum_regime_d7_stats.json"
    if path.exists():
        try:
            _momentum_d7_stats = json.loads(path.read_text())
        except Exception as e:
            print(f"  Warning: Could not load momentum D7 stats: {e}")
            _momentum_d7_stats = {}
    else:
        _momentum_d7_stats = {}
    return _momentum_d7_stats


def _pct_to_bucket(pct: float | None) -> str | None:
    """Map a percentile value to its bucket label (e.g. '15-20')."""
    if pct is None:
        return None
    try:
        val = float(pct)
    except Exception:
        return None
    if not np.isfinite(val):
        return None
    val = min(max(val, 0.0), 99.999)
    for lo in range(0, 100, 5):
        if val >= lo and val < lo + 5:
            return f"{lo}-{lo+5}"
    return "95-100"


async def _augment_with_momentum_regime(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add momentum regime D7 stats to market state.

    When MACD-V > 100: shows backtest win rate, avg/median return for the
    current RSI-MA percentile bucket under bullish momentum regime (7-day hold).
    """
    if response.get("timeframe") == "4h":
        return response

    market_state = response.get("market_state")
    if not isinstance(market_state, list) or not market_state:
        return response

    stats_db = _load_momentum_d7_stats()

    for state in market_state:
        if not isinstance(state, dict):
            continue

        # Defaults
        state["mom_regime_active"] = False
        state["mom_d7_win_rate"] = None
        state["mom_d7_avg_return"] = None
        state["mom_d7_median_return"] = None
        state["mom_d7_n"] = None

        macdv_daily = state.get("macdv_daily")
        if macdv_daily is None:
            continue
        try:
            macdv_val = float(macdv_daily)
        except Exception:
            continue
        if not np.isfinite(macdv_val) or macdv_val <= 100.0:
            continue

        # Momentum regime is active
        state["mom_regime_active"] = True

        ticker = state.get("ticker")
        if not isinstance(ticker, str):
            continue

        ticker_stats = stats_db.get(ticker)
        if not isinstance(ticker_stats, dict):
            continue

        # Find bucket for current percentile
        current_pct = state.get("current_percentile")
        bucket = _pct_to_bucket(current_pct)
        if bucket is None:
            # Fall back to overall stats
            overall = ticker_stats.get("_overall")
            if isinstance(overall, dict):
                state["mom_d7_win_rate"] = overall.get("win_rate")
                state["mom_d7_avg_return"] = overall.get("avg_return")
                state["mom_d7_median_return"] = overall.get("median_return")
                state["mom_d7_n"] = overall.get("n")
            continue

        bucket_stats = ticker_stats.get(bucket)
        if isinstance(bucket_stats, dict):
            state["mom_d7_win_rate"] = bucket_stats.get("win_rate")
            state["mom_d7_avg_return"] = bucket_stats.get("avg_return")
            state["mom_d7_median_return"] = bucket_stats.get("median_return")
            state["mom_d7_n"] = bucket_stats.get("n")
        else:
            # No data for this specific bucket, use overall
            overall = ticker_stats.get("_overall")
            if isinstance(overall, dict):
                state["mom_d7_win_rate"] = overall.get("win_rate")
                state["mom_d7_avg_return"] = overall.get("avg_return")
                state["mom_d7_median_return"] = overall.get("median_return")
                state["mom_d7_n"] = overall.get("n")

    return response


# Initialize MACD-V Reference Lookup (singleton)
_macdv_reference_lookup: Optional[MACDVReferenceLookup] = None
_macdv_reference_lock = asyncio.Lock()


async def _get_macdv_reference_lookup() -> Optional[MACDVReferenceLookup]:
    """Get or initialize the MACD-V Reference Lookup singleton (best-effort)."""
    global _macdv_reference_lookup
    if _macdv_reference_lookup is None:
        async with _macdv_reference_lock:
            if _macdv_reference_lookup is None:
                try:
                    # The reference database is a local JSON file; keep this synchronous to
                    # avoid relying on thread execution in restricted environments.
                    _macdv_reference_lookup = MACDVReferenceLookup()
                except Exception as e:
                    print(f"  Warning: MACD-V reference lookup init failed: {e}")
                    return None
    return _macdv_reference_lookup


async def _augment_with_macdv_percentiles(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add MACD-V percentile fields to market state:
    - macdv_zone: Zone classification (ranging, extreme_bearish, etc.)
    - macdv_zone_display: Human-readable zone with range
    - macdv_categorical_percentile: Percentile within the zone
    - macdv_asymmetric_percentile: Percentile within bull/bear regime
    - macdv_interpretation: Quick interpretation
    """
    market_state = response.get("market_state")
    if not isinstance(market_state, list) or not market_state:
        return response

    def _zone_display(zone: str) -> str:
        zone_display_map = {
            "extreme_bearish": "Extreme Bearish (<-100)",
            "strong_bearish": "Strong Bearish (-100 to -50)",
            "ranging": "Ranging (-50 to +50)",
            "strong_bullish": "Strong Bullish (+50 to +100)",
            "extreme_bullish": "Extreme Bullish (>+100)",
        }
        return zone_display_map.get(zone, zone)

    def _interpretation(zone: str, cat_percentile: float) -> str:
        zone_label = zone.replace("_", " ").title()

        if zone == "ranging":
            if cat_percentile >= 80:
                return "📈 Strengthening - near top of Range"
            if cat_percentile <= 20:
                return "💡 Oversold - near bottom of Range"
            return "➡️ Mid-range - within Range"

        if "bearish" in zone:
            if cat_percentile >= 80:
                strength = "🔄 Strong recovery"
                detail = f"near top of {zone_label}"
            elif cat_percentile >= 60:
                strength = "↗️ Recovering"
                detail = f"within {zone_label}"
            elif cat_percentile >= 40:
                strength = "➡️ Mid-range"
                detail = f"within {zone_label}"
            elif cat_percentile >= 20:
                strength = "↘️ Weakening"
                detail = f"within {zone_label}"
            else:
                strength = "⚠️ Extreme weakness"
                detail = f"near bottom of {zone_label}"
            return f"{strength} - {detail}"

        if "bullish" in zone:
            if cat_percentile >= 80:
                strength = "🚀 Very strong"
                detail = f"near top of {zone_label}"
            elif cat_percentile >= 60:
                strength = "📈 Strengthening"
                detail = f"within {zone_label}"
            elif cat_percentile >= 40:
                strength = "➡️ Mid-range"
                detail = f"within {zone_label}"
            elif cat_percentile >= 20:
                strength = "📉 Weakening"
                detail = f"within {zone_label}"
            else:
                strength = "⚠️ Near bottom"
                detail = f"weak within {zone_label}"
            return f"{strength} - {detail}"

        return "➡️ Mid-range"

    lookup = await _get_macdv_reference_lookup()

    for state in market_state:
        if not isinstance(state, dict):
            continue

        # Initialize fields to None
        state["macdv_zone"] = None
        state["macdv_zone_display"] = None
        state["macdv_categorical_percentile"] = None
        state["macdv_asymmetric_percentile"] = None
        state["macdv_interpretation"] = None

        ticker = state.get("ticker")
        if not isinstance(ticker, str):
            continue

        try:
            if lookup is None:
                continue

            # Reference DB keys use Yahoo symbols for some assets (e.g. BTC-USD, NQ=F, ES=F, ^TNX, ^VIX).
            lookup_key = resolve_yahoo_symbol(ticker)
            info = lookup.get_ticker_info(lookup_key) or lookup.get_ticker_info(ticker)
            curr = info.get("current_state", {}) if isinstance(info, dict) else {}
            if not isinstance(curr, dict) or not curr:
                continue

            zone = curr.get("zone")
            cat_percentile = curr.get("categorical_percentile")
            macdv_val = curr.get("macdv_val")

            if zone is None or cat_percentile is None:
                continue

            zone_str = str(zone)
            try:
                cat_val = float(cat_percentile)
            except Exception:
                continue

            asym_percentile = None
            if macdv_val is not None:
                try:
                    context = lookup.get_comparison_context(lookup_key, float(macdv_val))
                    if isinstance(context, dict):
                        asym_percentile = context.get("global_percentile", cat_val)
                except Exception:
                    asym_percentile = None

            state["macdv_zone"] = zone_str
            state["macdv_zone_display"] = _zone_display(zone_str)
            state["macdv_categorical_percentile"] = cat_val
            state["macdv_asymmetric_percentile"] = asym_percentile
            state["macdv_interpretation"] = _interpretation(zone_str, cat_val)

        except Exception as e:
            print(f"  Warning: Could not get MACD-V percentiles for {ticker}: {e}")
            continue

    return response


# P85 and P95 thresholds for divergence analysis (hardcoded per ticker)
_P85_THRESHOLDS = {
    'AAPL': 24.3, 'MSFT': 22.1, 'NVDA': 31.5, 'GOOGL': 28.4,
    'TSLA': 35.2, 'NFLX': 26.8, 'AMZN': 29.7, 'BRK-B': 18.9,
    'AVGO': 25.6, 'SPY': 19.2, 'QQQ': 27.3, 'CNX1': 21.4,
    'CSP1': 20.5, 'BTCUSD': 38.0, 'ES1': 19.5, 'NQ1': 27.5,
    'VIX': 33.5, 'IGLS': 23.8, 'XOM': 26.75, 'CVX': 24.06,
    'OXY': 26.95, 'JPM': 21.70, 'BAC': 21.31, 'LLY': 27.36,
    'UNH': 30.07, 'TSM': 22.90, 'WMT': 28.29, 'COST': 24.76,
    'GLD': 23.91, 'SLV': 25.62, 'USDGBP': 69.73, 'US10': 31.20
}

_P95_THRESHOLDS = {
    'AAPL': 36.8, 'MSFT': 33.9, 'NVDA': 47.3, 'GOOGL': 36.8,
    'TSLA': 52.1, 'NFLX': 40.2, 'AMZN': 44.5, 'BRK-B': 28.1,
    'AVGO': 38.4, 'SPY': 28.6, 'QQQ': 40.9, 'CNX1': 32.1,
    'CSP1': 30.5, 'BTCUSD': 55.0, 'ES1': 29.0, 'NQ1': 41.0,
    'VIX': 49.2, 'IGLS': 35.6, 'XOM': 35.16, 'CVX': 34.95,
    'OXY': 38.55, 'JPM': 31.34, 'BAC': 35.68, 'LLY': 38.06,
    'UNH': 42.04, 'TSM': 33.40, 'WMT': 37.38, 'COST': 39.21,
    'GLD': 32.72, 'SLV': 32.75, 'USDGBP': 84.14, 'US10': 45.13
}


async def _augment_with_divergence_metrics(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add multi-timeframe divergence metrics to market state:
    - four_h_percentile: 4-hour percentile
    - divergence_pct: Daily % - 4H %
    - divergence_category: bullish_convergence, bearish_convergence, etc.
    - category_label: Human-readable label
    - p85_threshold, p95_threshold: Historical thresholds
    - dislocation_level: Normal, Significant (P85), Extreme (P95)
    """
    market_state = response.get("market_state")
    if not isinstance(market_state, list) or not market_state:
        return response

    # Get 4H market state to get 4H percentiles
    try:
        four_h_response = await get_current_market_state_4h(force_refresh=False)
        four_h_market_state = four_h_response.get('market_state', [])
        four_h_lookup = {s['ticker']: s for s in four_h_market_state if isinstance(s, dict)}
    except Exception as e:
        print(f"  Warning: Could not get 4H data for divergence metrics: {e}")
        return response

    for state in market_state:
        if not isinstance(state, dict):
            continue

        # Initialize fields to None
        state["four_h_percentile"] = None
        state["divergence_pct"] = None
        state["abs_divergence_pct"] = None
        state["divergence_category"] = None
        state["category_label"] = None
        state["category_description"] = None
        state["p85_threshold"] = None
        state["p95_threshold"] = None
        state["dislocation_level"] = None
        state["dislocation_color"] = None
        state["thresholds_text"] = None

        ticker = state.get("ticker")
        if not isinstance(ticker, str):
            continue

        daily_pct = state.get("current_percentile")
        if daily_pct is None:
            continue

        # Get 4H percentile
        four_h_state = four_h_lookup.get(ticker)
        if not four_h_state:
            continue

        four_h_pct = four_h_state.get("current_percentile")
        if four_h_pct is None:
            continue

        # Calculate divergence
        divergence_pct = daily_pct - four_h_pct
        abs_divergence = abs(divergence_pct)

        # Get thresholds
        p85_threshold = _P85_THRESHOLDS.get(ticker, 25.0)
        p95_threshold = _P95_THRESHOLDS.get(ticker, 38.0)

        # Determine divergence category
        if daily_pct <= 15 and four_h_pct <= 15:
            divergence_category = "bullish_convergence"
            category_label = "🟢 Bullish Convergence"
            category_description = "Both timeframes low - Strong buy signal"
        elif daily_pct >= 85 and four_h_pct >= 85:
            divergence_category = "bearish_convergence"
            category_label = "🔴 Bearish Convergence"
            category_description = "Both timeframes high - Avoid/Exit signal"
        elif divergence_pct > 0:  # Daily > 4H
            if abs_divergence > p85_threshold:
                divergence_category = "4h_overextended"
                category_label = "🟡 4H Overextended"
                category_description = "4H extended relative to daily - Profit-take opportunity"
            else:
                divergence_category = "neutral_divergence"
                category_label = "⚪ Neutral Divergence"
                category_description = "Mixed signals - Wait for clarity"
        elif divergence_pct < 0:  # Daily < 4H
            if abs_divergence > p85_threshold:
                divergence_category = "daily_overextended"
                category_label = "🟠 Daily Overextended"
                category_description = "Daily extended relative to 4H - Exit signal"
            else:
                divergence_category = "neutral_divergence"
                category_label = "⚪ Neutral Divergence"
                category_description = "Mixed signals - Wait for clarity"
        else:  # divergence_pct == 0
            divergence_category = "neutral_divergence"
            category_label = "⚪ Neutral Divergence"
            category_description = "Both timeframes aligned - No significant divergence"

        # Determine dislocation level
        if abs_divergence <= p85_threshold:
            dislocation_level = "Normal"
            dislocation_color = "○"
        elif abs_divergence <= p95_threshold:
            dislocation_level = "Significant (P85)"
            dislocation_color = "⚠️"
        else:
            dislocation_level = "Extreme (P95)"
            dislocation_color = "⚡"

        # Update state
        state["four_h_percentile"] = four_h_pct
        state["divergence_pct"] = divergence_pct
        state["abs_divergence_pct"] = abs_divergence
        state["divergence_category"] = divergence_category
        state["category_label"] = category_label
        state["category_description"] = category_description
        state["p85_threshold"] = p85_threshold
        state["p95_threshold"] = p95_threshold
        state["dislocation_level"] = dislocation_level
        state["dislocation_color"] = dislocation_color
        state["thresholds_text"] = f"{p85_threshold:.1f}% | {p95_threshold:.1f}%"

    return response


def _read_snapshot_file(filename: str) -> Dict | None:
    path = _STATIC_SNAPSHOT_DIR / filename
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        if isinstance(payload, dict):
            return payload
    except Exception as e:
        print(f"  Failed to load static snapshot {path}: {e}")
    return None


def _load_static_snapshot(filename: str) -> Dict | None:
    if os.getenv("SWING_STATIC_SNAPSHOTS", "1").lower() in {"0", "false", "no"}:
        return None
    return _read_snapshot_file(filename)


def _load_static_cohort_stats() -> Dict | None:
    """
    Load precomputed cohort statistics (if available) from disk.

    This is intentionally controlled separately from SWING_STATIC_SNAPSHOTS so you can:
    - Disable static current-state snapshots (always compute live percentiles), while still
      avoiding expensive backtest recomputation for cohort stats.
    """
    if os.getenv("SWING_STATIC_COHORT_STATS", "1").lower() in {"0", "false", "no"}:
        return None
    return _read_snapshot_file("cohort-stats.json")


def _is_cache_valid(cache: Dict | None, cache_timestamp: datetime | None, ttl_seconds: int) -> bool:
    if cache is None or cache_timestamp is None:
        return False
    return (datetime.now(timezone.utc) - cache_timestamp).total_seconds() < ttl_seconds


def clean_price_spikes(data: pd.DataFrame, max_daily_change_pct: float = 15.0) -> pd.DataFrame:
    """
    Remove data points with suspicious price spikes (likely bad data from Yahoo Finance).

    Detects single-day moves > max_daily_change_pct that reverse the next day,
    which are typically data errors rather than real price movements.

    Args:
        data: DataFrame with OHLCV data
        max_daily_change_pct: Maximum allowed single-day change (default 15%)

    Returns:
        Cleaned DataFrame with spike rows removed
    """
    if data.empty or 'Close' not in data.columns:
        return data

    df = data.copy()

    # Calculate daily returns
    daily_returns = df['Close'].pct_change() * 100

    # Identify suspicious spikes: large move followed by reversal
    # A spike is when: |day_return| > threshold AND next_day reverses significantly
    spikes_to_remove = []

    for i in range(1, len(df) - 1):
        current_return = daily_returns.iloc[i]
        next_return = daily_returns.iloc[i + 1] if i + 1 < len(daily_returns) else 0

        # Check for spike pattern: large move that reverses
        if abs(current_return) > max_daily_change_pct:
            # Check if next day reverses (opposite sign and significant)
            if (current_return > 0 and next_return < -max_daily_change_pct * 0.5) or \
               (current_return < 0 and next_return > max_daily_change_pct * 0.5):
                spikes_to_remove.append(df.index[i])
                print(f"  ⚠️  Removing spike on {df.index[i].date()}: {current_return:.1f}% change (bad data)")

    if spikes_to_remove:
        df = df.drop(spikes_to_remove)
        print(f"  Cleaned {len(spikes_to_remove)} suspicious data points")

    return df


def fetch_daily_batch(tickers: List[str], period: str = "2y") -> Dict[str, pd.DataFrame]:
    """
    Batch-fetch daily OHLCV for multiple tickers using a single yfinance.download call.

    Returns a mapping keyed by display ticker (input) to a single-ticker OHLCV DataFrame.
    Any ticker missing from the batch response will be mapped to an empty DataFrame.
    """
    if not tickers:
        return {}

    yahoo_by_display = {ticker: resolve_yahoo_symbol(ticker) for ticker in tickers}
    yahoo_symbols = list(dict.fromkeys(yahoo_by_display.values()))

    data = yf.download(
        yahoo_symbols,
        period=period,
        group_by="ticker",
        auto_adjust=True,
        prepost=True,
        progress=False,
        threads=True,
    )

    results: Dict[str, pd.DataFrame] = {ticker: pd.DataFrame() for ticker in tickers}
    if data is None or getattr(data, "empty", True):
        return results

    multi = isinstance(data.columns, pd.MultiIndex)
    for display_ticker, yahoo_symbol in yahoo_by_display.items():
        frame = pd.DataFrame()
        if multi:
            try:
                level0 = data.columns.get_level_values(0)
                level1 = data.columns.get_level_values(1)
                if yahoo_symbol in level0:
                    frame = data[yahoo_symbol].copy()
                elif yahoo_symbol in level1:
                    frame = data.xs(yahoo_symbol, level=1, axis=1).copy()
            except Exception:
                frame = pd.DataFrame()
        else:
            if len(yahoo_symbols) == 1:
                frame = data.copy()

        if not frame.empty:
            required_columns = {"Open", "High", "Low", "Close"}
            if required_columns.issubset(frame.columns):
                frame = frame.dropna(subset=["Close"])
                # Clean suspicious price spikes (bad data from Yahoo Finance)
                frame = clean_price_spikes(frame, max_daily_change_pct=15.0)
            else:
                frame = pd.DataFrame()

        results[display_ticker] = frame

    return results


def compute_latest_percentile(indicator: pd.Series, lookback_period: int) -> float | None:
    """
    Compute only the *latest* rolling percentile rank for the indicator.

    This matches EnhancedPerformanceMatrixBacktester.calculate_percentile_ranks() for
    the final timestamp, but avoids computing the full rolling series.
    """
    if indicator is None:
        return None
    series = indicator.dropna()
    if len(series) < lookback_period:
        return None

    window = series.iloc[-lookback_period:]
    if len(window) < 2:
        return None
    current_value = window.iloc[-1]
    below_count = (window.iloc[:-1] < current_value).sum()
    return float((below_count / (len(window) - 1)) * 100)


def calculate_full_percentile_ranks(indicator: pd.Series, lookback_period: int) -> pd.Series:
    """
    Calculate rolling percentile ranks for the entire indicator series.

    For each point, calculates what percentile it is within the lookback window.
    """
    if indicator is None or indicator.empty:
        return pd.Series(dtype=float)

    series = indicator.dropna()
    if len(series) < lookback_period:
        return pd.Series(dtype=float)

    percentiles = []
    indices = []

    for i in range(lookback_period - 1, len(series)):
        window = series.iloc[i - lookback_period + 1:i + 1]
        if len(window) < 2:
            continue

        current_value = window.iloc[-1]
        below_count = (window.iloc[:-1] < current_value).sum()
        percentile = (below_count / (len(window) - 1)) * 100

        percentiles.append(percentile)
        indices.append(series.index[i])

    return pd.Series(percentiles, index=indices)


def find_last_extreme_low_date(percentile_ranks: pd.Series, threshold: float = 5.0) -> str | None:
    """
    Find the most recent date when the percentile was at or below the threshold (default 5%).

    Returns ISO format date string or None if never hit threshold in historical data.
    """
    if percentile_ranks is None or percentile_ranks.empty:
        return None

    # Filter to dates where percentile <= threshold
    extreme_low_dates = percentile_ranks[percentile_ranks <= threshold]

    if extreme_low_dates.empty:
        return None

    # Get the most recent date
    last_date = extreme_low_dates.index[-1]

    # Return as ISO format string
    return last_date.strftime("%Y-%m-%d") if hasattr(last_date, 'strftime') else str(last_date)


def convert_bins_to_dict(bin_data: Dict) -> Dict:
    """Convert BinStatistics objects to dictionaries"""
    result = {}
    for bin_range, stats in bin_data.items():
        result[bin_range] = {
            "bin_range": bin_range,
            "mean": float(stats.mean),
            "std": float(stats.std),
            "median": float(stats.median),
            "sample_size": int(stats.sample_size),
            "t_score": float(stats.t_score),
            "is_significant": bool(stats.is_significant),
            "significance_level": str(stats.significance_level.name) if hasattr(stats.significance_level, 'name') else str(stats.significance_level),
            "upside": float(stats.upside),
            "downside": float(stats.downside),
            "percentile_5th": float(stats.percentile_5th),
            "percentile_95th": float(stats.percentile_95th),
            "confidence_interval_95": [float(stats.confidence_interval_95[0]), float(stats.confidence_interval_95[1])],
            "se": float(stats.se)
        }
    return result


# Mapping of available 4H bin statistics for quick lookup
FOUR_H_BIN_MAP: Dict[str, Dict] = {
    "NVDA": NVDA_4H_DATA,
    "MSFT": MSFT_4H_DATA,
    "GOOGL": GOOGL_4H_DATA,
    "AAPL": AAPL_4H_DATA,
    "TSLA": TSLA_4H_DATA,
    "NFLX": NFLX_4H_DATA,
    "AVGO": AVGO_4H_DATA,
}

FOUR_H_DEFAULT_HOLDING_DAYS = 4.0  # Approximate 4H holding horizon (in days) for expectancy display


def estimate_win_rate_from_bin(mean: float, std: float) -> float:
    """Approximate win rate from bin statistics using a normal assumption."""
    if std <= 0:
        return 1.0 if mean > 0 else 0.0
    try:
        return float(norm.sf(0, loc=mean, scale=std))
    except Exception:
        return 0.5


def bin_to_cohort_stats(bin_stats) -> Dict[str, float]:
    """Convert BinStatistics to cohort stats compatible with live expectancy."""
    return {
        "count": int(bin_stats.sample_size),
        "win_rate": estimate_win_rate_from_bin(float(bin_stats.mean), float(bin_stats.std)),
        "avg_return": float(bin_stats.mean),
        "avg_holding_days": FOUR_H_DEFAULT_HOLDING_DAYS
    }


def combine_bins(bin_stats_list: List) -> Optional[Dict[str, float]]:
    """Combine multiple BinStatistics entries into weighted cohort stats."""
    if not bin_stats_list:
        return None

    total_samples = sum(b.sample_size for b in bin_stats_list)
    if total_samples == 0:
        return None

    weighted_return = sum(float(b.mean) * b.sample_size for b in bin_stats_list) / total_samples
    weighted_win_rate = sum(
        estimate_win_rate_from_bin(float(b.mean), float(b.std)) * b.sample_size for b in bin_stats_list
    ) / total_samples

    return {
        "count": int(total_samples),
        "win_rate": float(weighted_win_rate),
        "avg_return": float(weighted_return),
        "avg_holding_days": FOUR_H_DEFAULT_HOLDING_DAYS
    }


def get_4h_cohort_stats_from_bins(ticker: str) -> Optional[Dict[str, Dict[str, float]]]:
    """Build cohort stats from pre-computed 4H bin data when available."""
    bin_data = FOUR_H_BIN_MAP.get(ticker)
    if not bin_data:
        return None

    cohort_stats = {
        "cohort_extreme_low": bin_to_cohort_stats(bin_data["0-5"]) if "0-5" in bin_data else None,
        "cohort_low": bin_to_cohort_stats(bin_data["5-15"]) if "5-15" in bin_data else None,
        "cohort_medium_low": bin_to_cohort_stats(bin_data["15-25"]) if "15-25" in bin_data else None,
        "cohort_medium": bin_to_cohort_stats(bin_data["25-50"]) if "25-50" in bin_data else None,
        "cohort_medium_high": bin_to_cohort_stats(bin_data["50-75"]) if "50-75" in bin_data else None,
        "cohort_high": bin_to_cohort_stats(bin_data["75-85"]) if "75-85" in bin_data else None,
        "cohort_extreme_high": combine_bins([b for k, b in bin_data.items() if k in ["85-95", "95-100"]])
    }

    cohort_all_bins = [b for b in bin_data.values() if getattr(b, "sample_size", 0) > 0]
    cohort_stats["cohort_all"] = combine_bins(cohort_all_bins)

    return cohort_stats


def get_percentile_cohort(percentile: float) -> tuple[str, str]:
    """Map percentile to cohort identifier and human-readable zone label."""
    if percentile <= 5.0:
        return "extreme_low", "≤5th percentile (Extreme Low)"
    if percentile <= 15.0:
        return "low", "5-15th percentile (Low)"
    if percentile <= 30.0:
        return "medium_low", "15-30th percentile (Medium Low)"
    if percentile <= 50.0:
        return "medium", "30-50th percentile (Medium)"
    if percentile <= 70.0:
        return "medium_high", "50-70th percentile (Medium High)"
    if percentile <= 85.0:
        return "high", "70-85th percentile (High)"
    return "extreme_high", "85-100th percentile (Extreme High)"


def compute_4h_cohort_stats_from_data(
    backtester: EnhancedPerformanceMatrixBacktester,
    data_frame: pd.DataFrame,
    percentile_ranks: pd.Series
) -> Dict[str, Dict[str, float]]:
    """Compute cohort stats directly from 4H data as a fallback when bin data is unavailable."""
    entry_events = backtester.find_entry_events_enhanced(
        percentile_ranks,
        data_frame['Close'],
        threshold=100.0
    )

    trades: List[Dict] = []
    for event in entry_events:
        entry_date = event['entry_date']
        if entry_date not in data_frame.index:
            continue

        entry_idx = data_frame.index.get_loc(entry_date)
        exit_idx, _ = find_exit_point(
            data_frame,
            percentile_ranks,
            entry_idx,
            max_days=21,
            exit_percentile=50.0,
            stop_loss_pct=2.0
        )

        exit_date = data_frame.index[exit_idx]
        exit_price = data_frame.iloc[exit_idx]['Close']
        entry_price = event['entry_price']
        entry_pct = float(event['entry_percentile'])
        percentile_cohort, _ = get_percentile_cohort(entry_pct)

        holding_days = max((exit_date - entry_date).total_seconds() / 86400, 0.1)

        trades.append({
            "entry_date": entry_date.strftime("%Y-%m-%d %H:%M") if hasattr(entry_date, "strftime") else str(entry_date),
            "exit_date": exit_date.strftime("%Y-%m-%d %H:%M") if hasattr(exit_date, "strftime") else str(exit_date),
            "entry_price": float(entry_price),
            "exit_price": float(exit_price),
            "entry_percentile": entry_pct,
            "exit_percentile": float(percentile_ranks.iloc[exit_idx]),
            "holding_days": holding_days,
            "return_pct": float((exit_price - entry_price) / entry_price * 100),
            "regime": "mean_reversion" if entry_pct <= 50.0 else "momentum",
            "percentile_cohort": percentile_cohort
        })

    # Build cohort buckets
    cohorts: Dict[str, List[Dict]] = {
        "extreme_low": [],
        "low": [],
        "medium_low": [],
        "medium": [],
        "medium_high": [],
        "high": [],
        "extreme_high": []
    }

    for trade in trades:
        cohort = trade.get("percentile_cohort")
        if cohort in cohorts:
            cohorts[cohort].append(trade)

    # Helper to convert list of trades to stats
    def stats_for(trade_list: List[Dict]) -> Optional[Dict[str, float]]:
        if not trade_list:
            return None
        agg = calculate_backtest_stats(trade_list)
        return {
            "count": agg.get("total_trades", 0),
            "win_rate": agg.get("win_rate", 0.0),
            "avg_return": agg.get("avg_return", 0.0),
            "avg_holding_days": agg.get("avg_holding_days", FOUR_H_DEFAULT_HOLDING_DAYS)
        }

    all_stats = calculate_backtest_stats(trades)
    return {
        "cohort_extreme_low": stats_for(cohorts["extreme_low"]),
        "cohort_low": stats_for(cohorts["low"]),
        "cohort_medium_low": stats_for(cohorts["medium_low"]),
        "cohort_medium": stats_for(cohorts["medium"]),
        "cohort_medium_high": stats_for(cohorts["medium_high"]),
        "cohort_high": stats_for(cohorts["high"]),
        "cohort_extreme_high": stats_for(cohorts["extreme_high"]),
        "cohort_all": {
            "count": all_stats.get("total_trades", 0),
            "win_rate": all_stats.get("win_rate", 0.0),
            "avg_return": all_stats.get("avg_return", 0.0),
            "avg_holding_days": all_stats.get("avg_holding_days", FOUR_H_DEFAULT_HOLDING_DAYS)
        }
    }


def find_exit_point(
    data: pd.DataFrame,
    percentiles: pd.Series,
    entry_idx: int,
    max_days: int = 21,
    exit_percentile: float = 50.0,
    stop_loss_pct: float = 2.0
) -> tuple:
    """
    Find actual exit point from real historical data

    Returns: (exit_idx, exit_reason)
    exit_reason: 'target', 'stop_loss', 'max_days', 'end_of_data'
    """
    entry_price = data.iloc[entry_idx]['Close']

    for i in range(1, max_days + 1):
        exit_idx = entry_idx + i

        if exit_idx >= len(data):
            return entry_idx + i - 1, 'end_of_data'

        exit_price = data.iloc[exit_idx]['Close']
        return_pct = (exit_price - entry_price) / entry_price * 100

        # Check stop loss
        if return_pct <= -stop_loss_pct:
            return exit_idx, 'stop_loss'

        # Check target (percentile >= 50%)
        if percentiles.iloc[exit_idx] >= exit_percentile:
            return exit_idx, 'target'

    # Max holding period reached
    return entry_idx + max_days, 'max_days'


async def get_cached_cohort_stats(allow_compute: bool = True) -> Dict:
    """
    Get cohort statistics from cache or compute if cache is stale/empty
    Returns: Dict[ticker] = {cohort_extreme_low: {...}, cohort_low: {...}}
    """
    global _cohort_stats_cache, _cache_timestamp

    # Check if cache is valid
    now = datetime.now(timezone.utc)
    cache_valid = (
        _cache_timestamp is not None
        and (now - _cache_timestamp).total_seconds() < _cache_ttl_seconds
        and _cohort_stats_cache
    )

    if cache_valid:
        print(f"  Using cached cohort stats (age: {(now - _cache_timestamp).total_seconds():.0f}s)")
        return _cohort_stats_cache

    # Try to load a precomputed cohort snapshot from disk (fast path).
    static_payload = _load_static_cohort_stats()
    if isinstance(static_payload, dict) and static_payload.get("cohort_stats"):
        cohort_stats = static_payload.get("cohort_stats", {})
        if isinstance(cohort_stats, dict) and cohort_stats:
            _cohort_stats_cache = cohort_stats
            _cache_timestamp = now
            print(f"  ✓ Loaded cohort stats snapshot for {len(cohort_stats)} tickers")
            return cohort_stats

    if not allow_compute:
        print("  Cohort stats unavailable (compute disabled); returning empty cohort cache")
        return {}

    # Cache miss or stale - fetch full backtest data (slow path)
    print("  Cache miss - fetching fresh cohort statistics...")
    all_data = await get_swing_framework_data()

    # Extract ALL cohort stats (all percentile ranges)
    cohort_stats = {}
    for ticker, ticker_data in all_data['tickers'].items():
        backtest_stats = ticker_data.get('backtest_stats', {})
        cohort_stats[ticker] = {
            'cohort_extreme_low': backtest_stats.get('cohort_extreme_low'),
            'cohort_low': backtest_stats.get('cohort_low'),
            'cohort_medium_low': backtest_stats.get('cohort_medium_low'),
            'cohort_medium': backtest_stats.get('cohort_medium'),
            'cohort_medium_high': backtest_stats.get('cohort_medium_high'),
            'cohort_high': backtest_stats.get('cohort_high'),
            'cohort_extreme_high': backtest_stats.get('cohort_extreme_high'),
            'cohort_all': backtest_stats.get('cohort_all'),
            'metadata': ticker_data.get('metadata', {})
        }

    # Update cache
    _cohort_stats_cache = cohort_stats
    _cache_timestamp = now
    print(f"  ✓ Cached cohort stats for {len(cohort_stats)} tickers")

    return cohort_stats


def calculate_backtest_stats(trades: List[Dict]) -> Dict:
    """Calculate aggregate statistics from trade list with RSI-MA cohort breakdown"""
    if not trades:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "avg_return": 0.0,
            "avg_holding_days": 0.0,
            "total_return": 0.0
        }

    wins = [t for t in trades if t['return_pct'] > 0]
    losses = [t for t in trades if t['return_pct'] < 0]

    total_return = sum(t['return_pct'] for t in trades)

    # RSI-MA Cohort Analysis - All percentile ranges
    extreme_low_trades = [t for t in trades if t.get('percentile_cohort') == 'extreme_low']  # 0-5%
    low_trades = [t for t in trades if t.get('percentile_cohort') == 'low']  # 5-15%

    # Additional cohorts for all percentile ranges
    def get_cohort_for_percentile(pct):
        """Determine cohort based on entry percentile"""
        if pct <= 5.0:
            return 'extreme_low'
        elif pct <= 15.0:
            return 'low'
        elif pct <= 30.0:
            return 'medium_low'
        elif pct <= 50.0:
            return 'medium'
        elif pct <= 70.0:
            return 'medium_high'
        elif pct <= 85.0:
            return 'high'
        else:
            return 'extreme_high'

    # Categorize all trades into cohorts
    cohort_trades = {}
    for t in trades:
        cohort = t.get('percentile_cohort')
        if not cohort and 'entry_percentile' in t:
            cohort = get_cohort_for_percentile(t['entry_percentile'])
        if cohort:
            if cohort not in cohort_trades:
                cohort_trades[cohort] = []
            cohort_trades[cohort].append(t)

    def cohort_stats(cohort_trades_list):
        if not cohort_trades_list:
            return None
        cohort_wins = [t for t in cohort_trades_list if t['return_pct'] > 0]
        return {
            "count": len(cohort_trades_list),
            "win_rate": len(cohort_wins) / len(cohort_trades_list),
            "avg_return": sum(t['return_pct'] for t in cohort_trades_list) / len(cohort_trades_list),
            "avg_holding_days": sum(t['holding_days'] for t in cohort_trades_list) / len(cohort_trades_list)
        }

    return {
        "total_trades": len(trades),
        "win_rate": len(wins) / len(trades) if trades else 0.0,
        "avg_return": total_return / len(trades) if trades else 0.0,
        "avg_win": sum(t['return_pct'] for t in wins) / len(wins) if wins else 0.0,
        "avg_loss": sum(t['return_pct'] for t in losses) / len(losses) if losses else 0.0,
        "avg_holding_days": sum(t['holding_days'] for t in trades) / len(trades) if trades else 0.0,
        "total_return": total_return,
        "max_return": max(t['return_pct'] for t in trades) if trades else 0.0,
        "min_return": min(t['return_pct'] for t in trades) if trades else 0.0,
        # RSI-MA Percentile Cohort Breakdown - All ranges
        "cohort_extreme_low": cohort_stats(cohort_trades.get('extreme_low', [])),  # 0-5%
        "cohort_low": cohort_stats(cohort_trades.get('low', [])),  # 5-15%
        "cohort_medium_low": cohort_stats(cohort_trades.get('medium_low', [])),  # 15-30%
        "cohort_medium": cohort_stats(cohort_trades.get('medium', [])),  # 30-50%
        "cohort_medium_high": cohort_stats(cohort_trades.get('medium_high', [])),  # 50-70%
        "cohort_high": cohort_stats(cohort_trades.get('high', [])),  # 70-85%
        "cohort_extreme_high": cohort_stats(cohort_trades.get('extreme_high', [])),  # 85-100%
        "cohort_all": cohort_stats(trades)  # Fallback - all trades
    }


@router.get("/all-tickers")
async def get_swing_framework_data():
    """
    Get comprehensive data for all tickers including REAL historical trades

    Returns:
    - Stock metadata
    - Bin statistics (4H and Daily)
    - REAL historical trades from backtesting (not simulated!)
    - Aggregate statistics
    """

    # Include both stocks and market indices
    tickers = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "GOOGL", "TSLA", "NFLX", "AMZN", "BRK-B", "AVGO", "CNX1", "CSP1", "BTCUSD", "ES1", "NQ1", "VIX", "IGLS", "XOM", "CVX", "JPM", "BAC", "LLY", "UNH", "OXY", "TSM", "WMT", "COST", "GLD", "SLV", "USDGBP", "US10"]
    results = {}

    bin_data_map = {
        "NVDA": (NVDA_4H_DATA, NVDA_DAILY_DATA),
        "MSFT": (MSFT_4H_DATA, MSFT_DAILY_DATA),
        "GOOGL": (GOOGL_4H_DATA, GOOGL_DAILY_DATA),
        "AAPL": (AAPL_4H_DATA, AAPL_DAILY_DATA),
        "TSLA": (TSLA_4H_DATA, TSLA_DAILY_DATA),
        "NFLX": (NFLX_4H_DATA, NFLX_DAILY_DATA),
        "AVGO": (AVGO_4H_DATA, AVGO_DAILY_DATA),
        "XOM": (XOM_4H_DATA, XOM_DAILY_DATA),
        "CVX": (CVX_4H_DATA, CVX_DAILY_DATA),
        "JPM": (JPM_4H_DATA, JPM_DAILY_DATA),
        "BAC": (BAC_4H_DATA, BAC_DAILY_DATA),
        "LLY": (LLY_4H_DATA, LLY_DAILY_DATA),
        "UNH": (UNH_4H_DATA, UNH_DAILY_DATA),
        "OXY": (OXY_4H_DATA, OXY_DAILY_DATA),
        "TSM": (TSM_4H_DATA, TSM_DAILY_DATA),
        "WMT": (WMT_4H_DATA, WMT_DAILY_DATA),
        "COST": (COST_4H_DATA, COST_DAILY_DATA),
        "GLD": (GLD_4H_DATA, GLD_DAILY_DATA),
        "SLV": (SLV_4H_DATA, SLV_DAILY_DATA),
        "USDGBP": (USDGBP_4H_DATA, USDGBP_DAILY_DATA),
        "US10": (US10_4H_DATA, US10_DAILY_DATA),
        # Indices and stocks without pre-computed bin data - will use real-time calculation
        "SPY": (None, None),
        "QQQ": (None, None),
        "AMZN": (None, None),
        "VIX": (None, None),
        "IGLS": (None, None)
    }

    for ticker in tickers:
        try:
            print(f"Processing {ticker}...")

            # Get metadata
            metadata = STOCK_METADATA.get(ticker)
            if not metadata:
                print(f"  No metadata for {ticker}, skipping")
                continue

            # Get bin statistics (optional for indices - they compute dynamically)
            bins_4h, bins_daily = bin_data_map.get(ticker, (None, None))
            # For indices like SPY/QQQ, bins_4h will be None - they don't need pre-computed bin data
            # Individual stocks use pre-computed bin data for efficiency

            # Initialize backtester with REAL historical data
            try:
                backtester = EnhancedPerformanceMatrixBacktester(
                    tickers=[ticker],
                    lookback_period=500,
                    rsi_length=14,
                    ma_length=14,
                    max_horizon=21
                )

                # Fetch REAL historical price data
                data = backtester.fetch_data(ticker)
                if data.empty:
                    print(f"  No price data for {ticker}, using static bins only")
                    historical_trades = []
                else:
                    # Calculate RSI-MA indicator
                    indicator = backtester.calculate_rsi_ma_indicator(data)
                    percentile_ranks = backtester.calculate_percentile_ranks(indicator)

                    # Find REAL entry events across ALL percentile ranges (not just 0-15%)
                    entry_events = backtester.find_entry_events_enhanced(
                        percentile_ranks,
                        data['Close'],
                        threshold=100.0  # Capture ALL percentiles (0-100%)
                    )

                    print(f"  Found {len(entry_events)} total entry events across all percentiles")

                    # Separate into ALL percentile cohorts for comprehensive analysis
                    cohort_events = {
                        'extreme_low': [e for e in entry_events if e['entry_percentile'] <= 5.0],
                        'low': [e for e in entry_events if 5.0 < e['entry_percentile'] <= 15.0],
                        'medium_low': [e for e in entry_events if 15.0 < e['entry_percentile'] <= 30.0],
                        'medium': [e for e in entry_events if 30.0 < e['entry_percentile'] <= 50.0],
                        'medium_high': [e for e in entry_events if 50.0 < e['entry_percentile'] <= 70.0],
                        'high': [e for e in entry_events if 70.0 < e['entry_percentile'] <= 85.0],
                        'extreme_high': [e for e in entry_events if 85.0 < e['entry_percentile'] <= 100.0]
                    }

                    for cohort_name, events in cohort_events.items():
                        print(f"    {cohort_name}: {len(events)} events")

                    # Use ALL events - no artificial sampling
                    # Each cohort will have its natural sample size based on historical frequency
                    sampled_events = entry_events

                    print(f"  Using ALL {len(sampled_events)} trades across all percentile ranges (natural distribution)")

                    # Generate REAL trades from historical data
                    historical_trades = []
                    for event in sampled_events:
                        entry_date = event['entry_date']
                        entry_idx = data.index.get_loc(entry_date)

                        # Find actual exit point from REAL data
                        exit_idx, exit_reason = find_exit_point(
                            data,
                            percentile_ranks,
                            entry_idx,
                            max_days=21,
                            exit_percentile=50.0,
                            stop_loss_pct=2.0
                        )

                        exit_date = data.index[exit_idx]
                        exit_price = data.iloc[exit_idx]['Close']
                        exit_percentile = percentile_ranks.iloc[exit_idx]

                        # Determine percentile cohort for RSI-MA tracking (ALL ranges)
                        entry_pct = float(event['entry_percentile'])
                        if entry_pct <= 5.0:
                            cohort = "extreme_low"
                        elif entry_pct <= 15.0:
                            cohort = "low"
                        elif entry_pct <= 30.0:
                            cohort = "medium_low"
                        elif entry_pct <= 50.0:
                            cohort = "medium"
                        elif entry_pct <= 70.0:
                            cohort = "medium_high"
                        elif entry_pct <= 85.0:
                            cohort = "high"
                        else:
                            cohort = "extreme_high"

                        trade = {
                            "entry_date": entry_date.strftime("%Y-%m-%d") if hasattr(entry_date, 'strftime') else str(entry_date),
                            "exit_date": exit_date.strftime("%Y-%m-%d") if hasattr(exit_date, 'strftime') else str(exit_date),
                            "entry_price": float(event['entry_price']),
                            "exit_price": float(exit_price),
                            "entry_percentile": entry_pct,
                            "exit_percentile": float(exit_percentile),
                            "holding_days": int((exit_date - entry_date).days) if hasattr((exit_date - entry_date), 'days') else 1,
                            "return_pct": float((exit_price - event['entry_price']) / event['entry_price'] * 100),
                            "regime": "mean_reversion" if metadata.is_mean_reverter else "momentum",
                            "exit_reason": exit_reason,
                            "percentile_cohort": cohort  # Track which RSI-MA cohort
                        }
                        historical_trades.append(trade)

                    print(f"  Generated {len(historical_trades)} real trades")

            except Exception as e:
                print(f"  Error running backtest for {ticker}: {e}")
                historical_trades = []

            # Compile response
            results[ticker] = {
                "metadata": {
                    "ticker": metadata.ticker,
                    "name": metadata.name,
                    "personality": metadata.personality,
                    "reliability_4h": metadata.reliability_4h,
                    "reliability_daily": metadata.reliability_daily,
                    "tradeable_4h_zones": metadata.tradeable_4h_zones,
                    "dead_zones_4h": metadata.dead_zones_4h,
                    "best_4h_bin": metadata.best_4h_bin,
                    "best_4h_t_score": float(metadata.best_4h_t_score),
                    "ease_rating": int(metadata.ease_rating),
                    "is_mean_reverter": metadata.is_mean_reverter,
                    "is_momentum": metadata.is_momentum,
                    "volatility_level": metadata.volatility_level,
                    "entry_guidance": metadata.entry_guidance,
                    "avoid_guidance": metadata.avoid_guidance,
                    "special_notes": metadata.special_notes
                },
                "bins_4h": convert_bins_to_dict(bins_4h) if bins_4h else {},
                "bins_daily": convert_bins_to_dict(bins_daily) if bins_daily else {},
                "historical_trades": historical_trades,
                "backtest_stats": calculate_backtest_stats(historical_trades)
            }

            print(f"  ✓ {ticker} complete")

        except Exception as e:
            print(f"  Error processing {ticker}: {e}")
            import traceback
            traceback.print_exc()
            continue

    if not results:
        raise HTTPException(status_code=500, detail="Failed to process any tickers")

    return {
        "snapshot_timestamp": datetime.now(timezone.utc).isoformat(),
        "tickers": results,
        "summary": {
            "total_tickers": len(results),
            "tickers_with_trades": sum(1 for t in results.values() if t['historical_trades']),
            "total_trades": sum(len(t['historical_trades']) for t in results.values())
        }
    }


@router.get("/current-state-indices")
async def get_current_indices_state():
    """
    Get CURRENT RSI-MA percentile and live risk-adjusted expectancy for SPY and QQQ
    Shows real-time buy opportunities for market indices based on current market state

    OPTIMIZED: Uses cached cohort statistics, only fetches current percentiles
    Separate endpoint to allow modular dashboard views comparing "Stocks vs SPY vs QQQ"
    """
    indices = ["SPY", "QQQ"]

    allow_full_compute = os.getenv("SWING_FORCE_REFRESH_FULL", "0").lower() in {"1", "true", "yes"}

    # Get cached cohort stats (fast when loaded from snapshot or in-memory cache)
    print("Fetching indices cohort statistics...")
    cohort_stats_cache = await get_cached_cohort_stats(allow_compute=allow_full_compute)
    print("✓ Indices cohort stats ready")

    current_states = []

    # Fetch current percentiles for indices
    print("Fetching current percentiles for SPY and QQQ...")
    for ticker in indices:
        try:
            ticker_cohort_data = cohort_stats_cache.get(ticker, {}) if cohort_stats_cache else {}

            # Initialize backtester ONLY to get current percentile (fast)
            backtester = EnhancedPerformanceMatrixBacktester(
                tickers=[ticker],
                lookback_period=500,
                rsi_length=14,
                ma_length=14,
                max_horizon=21
            )

            # Fetch latest data (uses yfinance cache)
            data = backtester.fetch_data(ticker)
            if data.empty:
                continue

            # Calculate current RSI-MA indicator and percentile (fast operation)
            indicator = backtester.calculate_rsi_ma_indicator(data)
            percentile_ranks = backtester.calculate_percentile_ranks(indicator)

            # Get MOST RECENT (current) percentile
            current_percentile = float(percentile_ranks.iloc[-1])
            current_price = float(data['Close'].iloc[-1])
            current_date = data.index[-1].strftime("%Y-%m-%d")

            # Get metadata for regime
            metadata = STOCK_METADATA.get(ticker)
            if not metadata:
                continue

            regime = "mean_reversion" if metadata.is_mean_reverter else "momentum"

            # Determine entry zone and expected performance from historical data
            in_extreme_low = current_percentile <= 5.0
            in_low = 5.0 < current_percentile <= 15.0
            in_entry_zone = in_extreme_low or in_low

            # Determine percentile cohort for all ranges
            if current_percentile <= 5.0:
                percentile_cohort = "extreme_low"
                zone_label = "≤5th percentile (Extreme Low)"
            elif current_percentile <= 15.0:
                percentile_cohort = "low"
                zone_label = "5-15th percentile (Low)"
            elif current_percentile <= 30.0:
                percentile_cohort = "medium_low"
                zone_label = "15-30th percentile (Medium Low)"
            elif current_percentile <= 50.0:
                percentile_cohort = "medium"
                zone_label = "30-50th percentile (Medium)"
            elif current_percentile <= 70.0:
                percentile_cohort = "medium_high"
                zone_label = "50-70th percentile (Medium High)"
            elif current_percentile <= 85.0:
                percentile_cohort = "high"
                zone_label = "70-85th percentile (High)"
            else:
                percentile_cohort = "extreme_high"
                zone_label = "85-100th percentile (Extreme High)"

            # Get historical cohort performance from CACHE for ALL cohorts
            cohort_performance = ticker_cohort_data.get(f'cohort_{percentile_cohort}')

            # Fallback to 'cohort_all' if specific cohort has no data
            if not cohort_performance:
                cohort_performance = ticker_cohort_data.get('cohort_all')

            # Calculate live risk-adjusted expectancy (ALWAYS show data, even if not in entry zone)
            if cohort_performance:
                expected_win_rate = cohort_performance['win_rate']
                expected_return = cohort_performance['avg_return']
                expected_holding_days = cohort_performance['avg_holding_days']
                expected_return_per_day = expected_return / expected_holding_days if expected_holding_days > 0 else 0

                # Simple risk-adjusted expectancy (return / volatility proxy)
                volatility_multiplier = {"Low": 1.0, "Medium": 1.5, "High": 2.0}.get(metadata.volatility_level, 1.5)
                risk_adjusted_expectancy = expected_return / volatility_multiplier

                live_expectancy = {
                    "expected_win_rate": expected_win_rate,
                    "expected_return_pct": expected_return,
                    "expected_holding_days": expected_holding_days,
                    "expected_return_per_day_pct": expected_return_per_day,
                    "risk_adjusted_expectancy_pct": risk_adjusted_expectancy,
                    "sample_size": cohort_performance['count']
                }
            else:
                # No data for this cohort - return zeros
                live_expectancy = {
                    "expected_win_rate": 0.0,
                    "expected_return_pct": 0.0,
                    "expected_holding_days": 0.0,
                    "expected_return_per_day_pct": 0.0,
                    "risk_adjusted_expectancy_pct": 0.0,
                    "sample_size": 0
                }

            current_states.append({
                "ticker": ticker,
                "name": metadata.name,
                "current_date": current_date,
                "current_price": current_price,
                "current_percentile": current_percentile,
                "percentile_cohort": percentile_cohort,
                "zone_label": zone_label,
                "in_entry_zone": in_entry_zone,
                "regime": regime,
                "is_mean_reverter": metadata.is_mean_reverter,
                "is_momentum": metadata.is_momentum,
                "volatility_level": metadata.volatility_level,
                "live_expectancy": live_expectancy  # Expected performance if entering NOW
            })

        except Exception as e:
            print(f"  Error getting current state for {ticker}: {e}")
            continue

    # Sort by current percentile (lowest first = best buy opportunities)
    current_states.sort(key=lambda x: x['current_percentile'])

    print(f"✓ Indices market state ready: {len(current_states)} indices processed")

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "market_state": current_states,
        "summary": {
            "total_tickers": len(current_states),
            "in_entry_zone": sum(1 for s in current_states if s['in_entry_zone']),
            "extreme_low_opportunities": sum(1 for s in current_states if s['percentile_cohort'] == 'extreme_low'),
            "low_opportunities": sum(1 for s in current_states if s['percentile_cohort'] == 'low')
        }
    }


@router.get("/current-state")
async def get_current_market_state(
    force_refresh: bool = False,
    capture_midday_snapshot: bool = False,
    overwrite_midday_snapshot: bool = False,
):
    """
    Get CURRENT RSI-MA percentile and live risk-adjusted expectancy for all tickers (stocks + indices)
    Shows real-time buy opportunities based on current market state

    Now includes SPY and QQQ market indices integrated into the same list as stocks

    OPTIMIZED: Uses cached cohort statistics, only fetches current percentiles
    """
    global _current_state_cache, _current_state_cache_timestamp

    # Static snapshots are a fast cold-start path, but once this process has produced
    # a live baseline (e.g. via `force_refresh=true`), we should not "snap back" to an
    # older repo snapshot on subsequent refreshes.
    if not force_refresh and _current_state_cache is None:
        static_payload = _load_static_snapshot("current-state.json")
        if static_payload is not None:
            payload = _augment_with_prev_midday_snapshot(dict(static_payload), "daily")
            payload = await _augment_with_macdv_daily(payload)
            payload = await _augment_with_macdv_d7_stats(payload)
            payload = await _augment_with_momentum_regime(payload)
            payload = await _augment_with_macdv_percentiles(payload)
            payload = await _augment_with_divergence_metrics(payload)
            return payload

    if not force_refresh and _is_cache_valid(
        _current_state_cache, _current_state_cache_timestamp, _current_state_cache_ttl_seconds
    ):
        payload = dict(_current_state_cache)
        if not _has_macdv_daily(payload):
            payload = await _augment_with_macdv_daily(payload)
            payload = await _augment_with_macdv_d7_stats(payload)
            payload = await _augment_with_momentum_regime(payload)
            payload = await _augment_with_macdv_percentiles(payload)
            payload = await _augment_with_divergence_metrics(payload)
            _current_state_cache = payload
            _current_state_cache_timestamp = datetime.now(timezone.utc)
        return payload

    async with _current_state_lock:
        if not force_refresh and _is_cache_valid(
            _current_state_cache, _current_state_cache_timestamp, _current_state_cache_ttl_seconds
        ):
            payload = dict(_current_state_cache)
            if not _has_macdv_daily(payload):
                payload = await _augment_with_macdv_daily(payload)
                payload = await _augment_with_macdv_d7_stats(payload)
                payload = await _augment_with_momentum_regime(payload)
                payload = await _augment_with_macdv_percentiles(payload)
                payload = await _augment_with_divergence_metrics(payload)
                _current_state_cache = payload
                _current_state_cache_timestamp = datetime.now(timezone.utc)
            return payload
        # NOTE: Keep the expensive work inside the lock to prevent a cache stampede
        # (e.g., current-state and current-state-enriched arriving concurrently).
        tickers = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "GOOGL", "TSLA", "NFLX", "AMZN", "BRK-B", "AVGO", "CNX1", "CSP1", "BTCUSD", "ES1", "NQ1", "VIX", "IGLS", "XOM", "CVX", "JPM", "BAC", "LLY", "UNH", "OXY", "TSM", "WMT", "COST", "GLD", "SLV", "USDGBP", "US10"]

        # Get cached cohort stats (fast when loaded from snapshot or in-memory cache).
        #
        # NOTE: A "cold" cohort computation runs a full backtest-style pass for every
        # ticker (via /all-tickers) and can take minutes. For interactive "force refresh"
        # (where the user mainly wants *current percentiles/prices*), default to keeping
        # the endpoint responsive and only compute cohorts when explicitly enabled.
        allow_full_compute = (
            not force_refresh
            or os.getenv("SWING_FORCE_REFRESH_FULL", "0").lower() in {"1", "true", "yes"}
        )
        print("Fetching cohort statistics...")
        cohort_stats_cache = await get_cached_cohort_stats(allow_compute=allow_full_compute)
        print("✓ Cohort stats ready")

        current_states = []

        batch_daily_frames: Dict[str, pd.DataFrame] = {}
        try:
            print("Batch fetching daily OHLCV (5y) for current-state...")
            batch_daily_frames = fetch_daily_batch(tickers, period="5y")
        except Exception as e:
            print(f"  Batch daily fetch failed: {e}. Falling back to per-ticker fetches.")
            batch_daily_frames = {t: pd.DataFrame() for t in tickers}

        backtester = EnhancedPerformanceMatrixBacktester(
            tickers=tickers,
            lookback_period=500,
            rsi_length=14,
            ma_length=14,
            max_horizon=21
        )

        print("Fetching current percentiles...")
        for ticker in tickers:
            try:
                ticker_cohort_data = cohort_stats_cache.get(ticker, {}) if cohort_stats_cache else {}

                data = batch_daily_frames.get(ticker, pd.DataFrame())
                if data.empty or len(data) < backtester.lookback_period + 100:  # Need at least 100 extra points for meaningful percentile history
                    # Fall back to the existing per-ticker fetch path for this ticker only.
                    data = backtester.fetch_data(ticker, period="5y")
                    if data.empty or len(data) < backtester.lookback_period + 50:
                        data = backtester.fetch_data(ticker, period="max")
                if data.empty:
                    continue

                indicator = backtester.calculate_rsi_ma_indicator(data)
                current_percentile = compute_latest_percentile(indicator, backtester.lookback_period)
                if current_percentile is None:
                    continue

                rsi_percentile_252 = compute_latest_percentile(indicator, 252)

                # Calculate full percentile ranks to find last extreme low date
                percentile_ranks = calculate_full_percentile_ranks(indicator, backtester.lookback_period)
                last_extreme_low_date = find_last_extreme_low_date(percentile_ranks, threshold=5.0)

                # If no <5% found in current data, try fetching more historical data
                if last_extreme_low_date is None and len(data) < 2500:  # ~10 years
                    try:
                        extended_data = backtester.fetch_data(ticker, period="max")
                        if len(extended_data) > len(data):
                            extended_indicator = backtester.calculate_rsi_ma_indicator(extended_data)
                            extended_percentile_ranks = calculate_full_percentile_ranks(extended_indicator, backtester.lookback_period)
                            last_extreme_low_date = find_last_extreme_low_date(extended_percentile_ranks, threshold=5.0)
                    except Exception:
                        pass  # Use None if extended fetch fails

                current_price = float(data['Close'].iloc[-1])
                current_date = data.index[-1].strftime("%Y-%m-%d")

                metadata = STOCK_METADATA.get(ticker)
                if not metadata:
                    continue

                regime = "mean_reversion" if metadata.is_mean_reverter else "momentum"

                in_extreme_low = current_percentile <= 5.0
                in_low = 5.0 < current_percentile <= 15.0
                in_entry_zone = in_extreme_low or in_low

                if current_percentile <= 5.0:
                    percentile_cohort = "extreme_low"
                    zone_label = "≤5th percentile (Extreme Low)"
                elif current_percentile <= 15.0:
                    percentile_cohort = "low"
                    zone_label = "5-15th percentile (Low)"
                elif current_percentile <= 30.0:
                    percentile_cohort = "medium_low"
                    zone_label = "15-30th percentile (Medium Low)"
                elif current_percentile <= 50.0:
                    percentile_cohort = "medium"
                    zone_label = "30-50th percentile (Medium)"
                elif current_percentile <= 70.0:
                    percentile_cohort = "medium_high"
                    zone_label = "50-70th percentile (Medium High)"
                elif current_percentile <= 85.0:
                    percentile_cohort = "high"
                    zone_label = "70-85th percentile (High)"
                else:
                    percentile_cohort = "extreme_high"
                    zone_label = "85-100th percentile (Extreme High)"

                cohort_performance = ticker_cohort_data.get(f"cohort_{percentile_cohort}") if ticker_cohort_data else None
                if not cohort_performance and ticker_cohort_data:
                    cohort_performance = ticker_cohort_data.get("cohort_all")

                if cohort_performance:
                    expected_win_rate = cohort_performance["win_rate"]
                    expected_return = cohort_performance["avg_return"]
                    expected_holding_days = cohort_performance["avg_holding_days"]
                    expected_return_per_day = (
                        expected_return / expected_holding_days if expected_holding_days > 0 else 0
                    )

                    volatility_multiplier = {"Low": 1.0, "Medium": 1.5, "High": 2.0}.get(
                        metadata.volatility_level, 1.5
                    )
                    risk_adjusted_expectancy = expected_return / volatility_multiplier

                    live_expectancy = {
                        "expected_win_rate": expected_win_rate,
                        "expected_return_pct": expected_return,
                        "expected_holding_days": expected_holding_days,
                        "expected_return_per_day_pct": expected_return_per_day,
                        "risk_adjusted_expectancy_pct": risk_adjusted_expectancy,
                        "sample_size": cohort_performance["count"],
                    }
                else:
                    live_expectancy = {
                        "expected_win_rate": 0.0,
                        "expected_return_pct": 0.0,
                        "expected_holding_days": 0.0,
                        "expected_return_per_day_pct": 0.0,
                        "risk_adjusted_expectancy_pct": 0.0,
                        "sample_size": 0,
                    }

                current_states.append(
                    {
                        "ticker": ticker,
                        "name": metadata.name,
                        "current_date": current_date,
                        "current_price": current_price,
                        "current_percentile": current_percentile,
                        "rsi_percentile_252": rsi_percentile_252,
                        "percentile_cohort": percentile_cohort,
                        "zone_label": zone_label,
                        "in_entry_zone": in_entry_zone,
                        "regime": regime,
                        "is_mean_reverter": metadata.is_mean_reverter,
                        "is_momentum": metadata.is_momentum,
                        "volatility_level": metadata.volatility_level,
                        "live_expectancy": live_expectancy,  # Expected performance if entering NOW
                        "last_extreme_low_date": last_extreme_low_date,  # Last date when percentile was ≤5%
                    }
                )

            except Exception as e:
                print(f"  Error getting current state for {ticker}: {e}")
                continue

        current_states.sort(key=lambda x: x['current_percentile'])
        print(f"✓ Current market state ready: {len(current_states)} tickers processed")

        response = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "market_state": current_states,
            "summary": {
                "total_tickers": len(current_states),
                "in_entry_zone": sum(1 for s in current_states if s['in_entry_zone']),
                "extreme_low_opportunities": sum(1 for s in current_states if s['percentile_cohort'] == 'extreme_low'),
                "low_opportunities": sum(1 for s in current_states if s['percentile_cohort'] == 'low')
            }
        }

        response = _augment_with_prev_midday_snapshot(response, "daily")
        response = await _augment_with_macdv_daily(response)
        response = await _augment_with_macdv_d7_stats(response)
        response = await _augment_with_momentum_regime(response)
        response = await _augment_with_macdv_percentiles(response)
        response = await _augment_with_divergence_metrics(response)

        # Auto-save midday snapshot if within window and no snapshot exists for today
        now_utc = datetime.now(timezone.utc)
        market_day = _get_market_date(now_utc)
        should_auto_save = _should_auto_save_midday_snapshot("daily", now_utc)
        should_save = capture_midday_snapshot or should_auto_save

        if should_save:
            percentiles = {
                s.get("ticker"): float(s.get("current_percentile"))
                for s in (response.get("market_state") or [])
                if isinstance(s, dict) and s.get("ticker") is not None and s.get("current_percentile") is not None
            }
            prices = {
                s.get("ticker"): float(s.get("current_price"))
                for s in (response.get("market_state") or [])
                if isinstance(s, dict) and s.get("ticker") is not None and s.get("current_price") is not None
            }
            saved = _save_midday_snapshot(
                timeframe="daily",
                market_date=market_day,
                percentiles=percentiles,
                captured_at_utc=now_utc,
                prices=prices,
                overwrite=overwrite_midday_snapshot,
            )
            response["midday_snapshot_saved"] = saved
            response["midday_snapshot_auto_saved"] = should_auto_save and not capture_midday_snapshot

        _current_state_cache = response
        _current_state_cache_timestamp = datetime.now(timezone.utc)
        return response


@router.get("/current-state-4h")
async def get_current_market_state_4h(
    force_refresh: bool = False,
    capture_midday_snapshot: bool = False,
    overwrite_midday_snapshot: bool = False,
):
    """
    Get CURRENT RSI-MA percentile and live expectancy for the 4-hour timeframe.
    Uses pre-computed 4H bin statistics when available and falls back to on-the-fly
    cohort calculations from 4H price data.
    """
    global _current_state_4h_cache, _current_state_4h_cache_timestamp

    if not force_refresh and _current_state_4h_cache is None:
        static_payload = _load_static_snapshot("current-state-4h.json")
        if static_payload is not None:
            payload = _augment_with_prev_midday_snapshot(dict(static_payload), "4h")
            payload = await _augment_with_macdv_daily(payload)
            payload = await _augment_with_macdv_percentiles(payload)
            return payload

    if not force_refresh and _is_cache_valid(
        _current_state_4h_cache, _current_state_4h_cache_timestamp, _current_state_4h_cache_ttl_seconds
    ):
        payload = dict(_current_state_4h_cache)
        if not _has_macdv_daily(payload):
            payload = await _augment_with_macdv_daily(payload)
            payload = await _augment_with_macdv_percentiles(payload)
            _current_state_4h_cache = payload
            _current_state_4h_cache_timestamp = datetime.now(timezone.utc)
        return payload

    async with _current_state_4h_lock:
        if not force_refresh and _is_cache_valid(
            _current_state_4h_cache, _current_state_4h_cache_timestamp, _current_state_4h_cache_ttl_seconds
        ):
            payload = dict(_current_state_4h_cache)
            if not _has_macdv_daily(payload):
                payload = await _augment_with_macdv_daily(payload)
                payload = await _augment_with_macdv_percentiles(payload)
                _current_state_4h_cache = payload
                _current_state_4h_cache_timestamp = datetime.now(timezone.utc)
            return payload
        tickers = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "GOOGL", "TSLA", "NFLX", "AMZN", "BRK-B", "AVGO", "CNX1", "CSP1", "BTCUSD", "ES1", "NQ1", "VIX", "IGLS", "XOM", "CVX", "JPM", "BAC", "LLY", "UNH", "OXY", "TSM", "WMT", "COST", "GLD", "SLV", "USDGBP", "US10"]
        current_states = []

        print("Fetching 4H current percentiles...")
        # Daily cohort cache as a final fallback if 4H data is unavailable
        allow_full_compute = (
            not force_refresh
            or os.getenv("SWING_FORCE_REFRESH_FULL", "0").lower() in {"1", "true", "yes"}
        )
        daily_cohort_cache = await get_cached_cohort_stats(allow_compute=allow_full_compute)

        for ticker in tickers:
            try:
                metadata = STOCK_METADATA.get(ticker)
                if not metadata:
                    print(f"  No metadata for {ticker}, skipping")
                    continue

                data_for_current: pd.DataFrame
                data_source = "4h"

                backtester = EnhancedPerformanceMatrixBacktester(
                    tickers=[ticker],
                    lookback_period=252,  # Keep existing behavior for current 4H percentile path
                    rsi_length=14,
                    ma_length=14,
                    max_horizon=21,
                )

                try:
                    data_for_current = fetch_4h_data(ticker, lookback_days=365)
                    if data_for_current.empty:
                        raise ValueError("empty 4H data")
                except Exception as e:
                    print(f"  4H data fetch failed for {ticker}: {e}. Falling back to daily data.")
                    data_source = "daily_fallback"
                    data_for_current = backtester.fetch_data(ticker, period="2y")
                    if data_for_current.empty or len(data_for_current) < backtester.lookback_period + 3:
                        data_for_current = backtester.fetch_data(ticker, period="5y")
                    if data_for_current.empty:
                        print(f"  Fallback daily data also empty for {ticker}, skipping")
                        continue

                indicator = (
                    calculate_rsi_ma_4h(data_for_current)
                    if data_source == "4h"
                    else backtester.calculate_rsi_ma_indicator(data_for_current)
                )
                percentile_ranks = backtester.calculate_percentile_ranks(indicator)
                valid_percentiles = percentile_ranks.dropna()

                if valid_percentiles.empty:
                    print(f"  Insufficient {data_source} percentile data for {ticker}, skipping")
                    continue

                current_percentile = float(valid_percentiles.iloc[-1])

                current_price = float(data_for_current["Close"].iloc[-1])
                current_date = data_for_current.index[-1].strftime("%Y-%m-%d %H:%M")

                percentile_cohort, zone_label = get_percentile_cohort(current_percentile)
                in_entry_zone = percentile_cohort in ["extreme_low", "low"]
                regime = "mean_reversion" if metadata.is_mean_reverter else "momentum"

                cohort_stats = get_4h_cohort_stats_from_bins(ticker)
                if not cohort_stats and data_source == "4h":
                    cohort_stats = compute_4h_cohort_stats_from_data(
                        backtester, data_for_current, percentile_ranks
                    )
                if not cohort_stats and data_source == "daily_fallback":
                    cohort_stats = daily_cohort_cache.get(ticker, {})

                cohort_performance = cohort_stats.get(f"cohort_{percentile_cohort}") if cohort_stats else None
                if not cohort_performance and cohort_stats:
                    cohort_performance = cohort_stats.get("cohort_all")

                if cohort_performance:
                    expected_win_rate = cohort_performance.get("win_rate", 0.0)
                    expected_return = cohort_performance.get("avg_return", 0.0)
                    expected_holding_days = cohort_performance.get(
                        "avg_holding_days", FOUR_H_DEFAULT_HOLDING_DAYS
                    )
                    expected_return_per_day = (
                        expected_return / expected_holding_days if expected_holding_days > 0 else 0
                    )

                    volatility_multiplier = {"Low": 1.0, "Medium": 1.5, "High": 2.0}.get(
                        metadata.volatility_level, 1.5
                    )
                    risk_adjusted_expectancy = expected_return / volatility_multiplier

                    live_expectancy = {
                        "expected_win_rate": expected_win_rate,
                        "expected_return_pct": expected_return,
                        "expected_holding_days": expected_holding_days,
                        "expected_return_per_day_pct": expected_return_per_day,
                        "risk_adjusted_expectancy_pct": risk_adjusted_expectancy,
                        "sample_size": cohort_performance.get("count", 0),
                    }
                else:
                    live_expectancy = {
                        "expected_win_rate": 0.0,
                        "expected_return_pct": 0.0,
                        "expected_holding_days": FOUR_H_DEFAULT_HOLDING_DAYS,
                        "expected_return_per_day_pct": 0.0,
                        "risk_adjusted_expectancy_pct": 0.0,
                        "sample_size": 0,
                    }

                current_states.append(
                    {
                        "ticker": ticker,
                        "name": metadata.name,
                        "current_date": current_date,
                        "current_price": current_price,
                        "current_percentile": current_percentile,
                        "percentile_cohort": percentile_cohort,
                        "zone_label": zone_label,
                        "in_entry_zone": in_entry_zone,
                        "regime": regime,
                        "is_mean_reverter": metadata.is_mean_reverter,
                        "is_momentum": metadata.is_momentum,
                        "volatility_level": metadata.volatility_level,
                        "live_expectancy": live_expectancy,
                        "data_source": data_source,
                    }
                )

            except Exception as e:
                print(f"  Error getting 4H state for {ticker}: {e}")
                continue

        current_states.sort(key=lambda x: x['current_percentile'])
        print(f"✓ 4H market state ready: {len(current_states)} tickers processed")

        response = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "timeframe": "4h",
            "market_state": current_states,
            "summary": {
                "total_tickers": len(current_states),
                "in_entry_zone": sum(1 for s in current_states if s['in_entry_zone']),
                "extreme_low_opportunities": sum(1 for s in current_states if s['percentile_cohort'] == 'extreme_low'),
                "low_opportunities": sum(1 for s in current_states if s['percentile_cohort'] == 'low')
            }
        }

        response = _augment_with_prev_midday_snapshot(response, "4h")
        response = await _augment_with_macdv_daily(response)
        response = await _augment_with_macdv_percentiles(response)

        # Auto-save midday snapshot if within window and no snapshot exists for today
        now_utc = datetime.now(timezone.utc)
        market_day = _get_market_date(now_utc)
        should_auto_save = _should_auto_save_midday_snapshot("4h", now_utc)
        should_save = capture_midday_snapshot or should_auto_save

        if should_save:
            percentiles = {
                s.get("ticker"): float(s.get("current_percentile"))
                for s in (response.get("market_state") or [])
                if isinstance(s, dict) and s.get("ticker") is not None and s.get("current_percentile") is not None
            }
            prices = {
                s.get("ticker"): float(s.get("current_price"))
                for s in (response.get("market_state") or [])
                if isinstance(s, dict) and s.get("ticker") is not None and s.get("current_price") is not None
            }
            saved = _save_midday_snapshot(
                timeframe="4h",
                market_date=market_day,
                percentiles=percentiles,
                captured_at_utc=now_utc,
                prices=prices,
                overwrite=overwrite_midday_snapshot,
            )
            response["midday_snapshot_saved"] = saved
            response["midday_snapshot_auto_saved"] = should_auto_save and not capture_midday_snapshot

        _current_state_4h_cache = response
        _current_state_4h_cache_timestamp = datetime.now(timezone.utc)
        return response


@router.get("/current-state-enriched")
async def get_current_market_state_enriched(force_refresh: bool = False):
    """
    Get CURRENT RSI-MA percentile WITH MULTI-TIMEFRAME DIVERGENCE AND P85/P95 THRESHOLDS
    
    **NEW FEATURES**:
    - Daily and 4H percentiles for each ticker
    - Divergence percentage (Daily % - 4H %)
    - Divergence category (4H Overextended, Bullish Convergence, etc.)
    - P85 and P95 thresholds for each ticker (significant & extreme dislocations)
    - Status indicators: "4H Overextended", "Bullish Convergence", etc.
    - Comparison of current divergence against historical P85/P95
    
    **EXAMPLE DATA**:
    For GOOGL: P85 = 28.4%, P95 = 36.8% (historical significant & extreme thresholds)
    If current divergence = 32.1%, status = "Between P85-P95 (Near Extreme)"
    
    Returns enriched market state with divergence metrics for quick visualization
    """
    global _current_state_enriched_cache, _current_state_enriched_cache_timestamp

    if not force_refresh and _current_state_enriched_cache is None:
        static_payload = _load_static_snapshot("current-state-enriched.json")
        if static_payload is not None:
            return static_payload

    if not force_refresh and _is_cache_valid(
        _current_state_enriched_cache,
        _current_state_enriched_cache_timestamp,
        _current_state_enriched_cache_ttl_seconds,
    ):
        return dict(_current_state_enriched_cache)

    async with _current_state_enriched_lock:
        if not force_refresh and _is_cache_valid(
            _current_state_enriched_cache,
            _current_state_enriched_cache_timestamp,
            _current_state_enriched_cache_ttl_seconds,
        ):
            return dict(_current_state_enriched_cache)
        from multi_timeframe_analyzer import MultiTimeframeAnalyzer
        from percentile_threshold_analyzer import PercentileThresholdAnalyzer

        tickers = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "GOOGL", "TSLA", "NFLX", "AMZN", "BRK-B", "AVGO", "CNX1", "CSP1", "BTCUSD", "ES1", "NQ1", "VIX", "IGLS", "XOM", "CVX", "JPM", "BAC", "LLY", "UNH", "OXY", "TSM", "WMT", "COST", "GLD", "SLV", "USDGBP", "US10"]

        # First get base market state and 4H market state (run concurrently)
        base_response, four_h_response = await asyncio.gather(
            get_current_market_state(force_refresh=force_refresh),
            get_current_market_state_4h(force_refresh=force_refresh),
        )
        base_market_state = base_response['market_state']
        four_h_market_state = four_h_response['market_state']

        # Create lookup maps
        base_lookup = {s['ticker']: s for s in base_market_state}
        four_h_lookup = {s['ticker']: s for s in four_h_market_state}

        enriched_states = []

        for ticker in tickers:
            try:
                daily_state = base_lookup.get(ticker)
                four_h_state = four_h_lookup.get(ticker)

                if not daily_state or not four_h_state:
                    continue

                # Calculate divergence
                daily_pct = daily_state['current_percentile']
                four_h_pct = four_h_state['current_percentile']
                divergence_pct = daily_pct - four_h_pct

                p85_threshold = {
                    # Original tickers
                    'AAPL': 24.3, 'MSFT': 22.1, 'NVDA': 31.5, 'GOOGL': 28.4,
                    'TSLA': 35.2, 'NFLX': 26.8, 'AMZN': 29.7, 'BRK-B': 18.9,
                    'AVGO': 25.6, 'SPY': 19.2, 'QQQ': 27.3, 'CNX1': 21.4,
                    'CSP1': 20.5, 'BTCUSD': 38.0,  # LSE & Crypto
                    'ES1': 19.5, 'NQ1': 27.5,  # Futures
                    'VIX': 33.5, 'IGLS': 23.8,
                    # Energy sector
                    'XOM': 26.75, 'CVX': 24.06, 'OXY': 26.95,
                    # Financial sector
                    'JPM': 21.70, 'BAC': 21.31,
                    # Healthcare sector
                    'LLY': 27.36, 'UNH': 30.07,
                    # Technology
                    'TSM': 22.90,
                    # Retail
                    'WMT': 28.29, 'COST': 24.76,
                    # Commodities
                    'GLD': 23.91, 'SLV': 25.62,
                    # FX & Bonds
                    'USDGBP': 69.73, 'US10': 31.20
                }.get(ticker, 25.0)  # Default to 25.0 if not found

                p95_threshold = {
                    # Original tickers
                    'AAPL': 36.8, 'MSFT': 33.9, 'NVDA': 47.3, 'GOOGL': 36.8,
                    'TSLA': 52.1, 'NFLX': 40.2, 'AMZN': 44.5, 'BRK-B': 28.1,
                    'AVGO': 38.4, 'SPY': 28.6, 'QQQ': 40.9, 'CNX1': 32.1,
                    'CSP1': 30.5, 'BTCUSD': 55.0,  # LSE & Crypto
                    'ES1': 29.0, 'NQ1': 41.0,  # Futures
                    'VIX': 49.2, 'IGLS': 35.6,
                    # Energy sector
                    'XOM': 35.16, 'CVX': 34.95, 'OXY': 38.55,
                    # Financial sector
                    'JPM': 31.34, 'BAC': 35.68,
                    # Healthcare sector
                    'LLY': 38.06, 'UNH': 42.04,
                    # Technology
                    'TSM': 33.40,
                    # Retail
                    'WMT': 37.38, 'COST': 39.21,
                    # Commodities
                    'GLD': 32.72, 'SLV': 32.75,
                    # FX & Bonds
                    'USDGBP': 84.14, 'US10': 45.13
                }.get(ticker, 38.0)  # Default to 38.0 if not found

                abs_divergence = abs(divergence_pct)

                # Determine divergence category - SMART LOGIC using divergence magnitude
                # Priority 1: Check for clean convergence (both low or both high)
                if daily_pct <= 15 and four_h_pct <= 15:
                    divergence_category = "bullish_convergence"
                    category_label = "🟢 Bullish Convergence"
                    category_description = "Both timeframes low - Strong buy signal"
                elif daily_pct >= 85 and four_h_pct >= 85:
                    divergence_category = "bearish_convergence"
                    category_label = "🔴 Bearish Convergence"
                    category_description = "Both timeframes high - Avoid/Exit signal"
                # Priority 2: Determine based on divergence magnitude AND direction
                elif divergence_pct > 0:  # Daily > 4H (4H is lower = more extended)
                    if abs_divergence > p85_threshold:
                        divergence_category = "4h_overextended"
                        category_label = "🟡 4H Overextended"
                        category_description = "4H extended relative to daily - Profit-take opportunity"
                    else:
                        divergence_category = "neutral_divergence"
                        category_label = "⚪ Neutral Divergence"
                        category_description = "Mixed signals - Wait for clarity"
                elif divergence_pct < 0:  # Daily < 4H (Daily is lower = more extended)
                    if abs_divergence > p85_threshold:
                        divergence_category = "daily_overextended"
                        category_label = "🟠 Daily Overextended"
                        category_description = "Daily extended relative to 4H - Exit signal"
                    else:
                        divergence_category = "neutral_divergence"
                        category_label = "⚪ Neutral Divergence"
                        category_description = "Mixed signals - Wait for clarity"
                else:  # divergence_pct == 0 (rare)
                    divergence_category = "neutral_divergence"
                    category_label = "⚪ Neutral Divergence"
                    category_description = "Both timeframes aligned - No significant divergence"

                # Determine dislocation level
                if abs_divergence <= p85_threshold:
                    dislocation_level = "Normal"
                    dislocation_color = "⚪"
                elif abs_divergence <= p95_threshold:
                    dislocation_level = "Significant (P85)"
                    dislocation_color = "🟡"
                else:
                    dislocation_level = "Extreme (P95)"
                    dislocation_color = "🔴"

                enriched_state = {
                    **daily_state,  # Include all daily state fields
                    'four_h_percentile': four_h_pct,
                    'divergence_pct': divergence_pct,
                    'abs_divergence_pct': abs_divergence,
                    'divergence_category': divergence_category,
                    'category_label': category_label,
                    'category_description': category_description,
                    'p85_threshold': p85_threshold,
                    'p95_threshold': p95_threshold,
                    'dislocation_level': dislocation_level,
                    'dislocation_color': dislocation_color,
                    'thresholds_text': f"P85: {p85_threshold:.1f}% | P95: {p95_threshold:.1f}%"
                }

                enriched_states.append(enriched_state)

            except Exception as e:
                print(f"  Error enriching {ticker}: {e}")
                continue

        enriched_states.sort(key=lambda x: x['abs_divergence_pct'], reverse=True)

        print(f"✓ Enriched market state ready: {len(enriched_states)} tickers processed")

        response = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "market_state": enriched_states,
            "summary": {
                "total_tickers": len(enriched_states),
                "bullish_convergence": sum(1 for s in enriched_states if s['divergence_category'] == 'bullish_convergence'),
                "bearish_convergence": sum(1 for s in enriched_states if s['divergence_category'] == 'bearish_convergence'),
                "4h_overextended": sum(1 for s in enriched_states if s['divergence_category'] == '4h_overextended'),
                "daily_overextended": sum(1 for s in enriched_states if s['divergence_category'] == 'daily_overextended'),
                "extreme_dislocation": sum(1 for s in enriched_states if s['dislocation_level'] == 'Extreme (P95)'),
                "significant_dislocation": sum(1 for s in enriched_states if s['dislocation_level'] == 'Significant (P85)')
            }
        }
        _current_state_enriched_cache = response
        _current_state_enriched_cache_timestamp = datetime.now(timezone.utc)
        return response


@router.get("/{ticker}")
async def get_ticker_data(ticker: str):
    """Get data for a single ticker"""
    ticker = ticker.upper()

    # Call the main endpoint and filter
    all_data = await get_swing_framework_data()

    if ticker not in all_data['tickers']:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found")

    return {
        "snapshot_timestamp": all_data['snapshot_timestamp'],
        "ticker": ticker,
        "data": all_data['tickers'][ticker]
    }
