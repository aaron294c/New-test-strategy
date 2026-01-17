"""
Lower Extension Distance API
Provides calculation functions for lower extension metrics
"""

import asyncio
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Optional, Tuple
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path
from starlette.concurrency import run_in_threadpool

# Add parent directory to path to import ticker_utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from ticker_utils import resolve_yahoo_symbol

router = APIRouter(prefix="/api/lower-extension", tags=["Lower Extension"])

_METRICS_CACHE_TTL_SECONDS = 300
_METRICS_CACHE: dict[tuple[str, int, int], tuple[float, dict]] = {}


def _cache_get(ticker: str, length: int, lookback_days: int) -> dict | None:
    key = (ticker, int(length), int(lookback_days))
    entry = _METRICS_CACHE.get(key)
    if not entry:
        return None
    ts, payload = entry
    if (time.time() - ts) > _METRICS_CACHE_TTL_SECONDS:
        _METRICS_CACHE.pop(key, None)
        return None
    return payload


def _cache_set(ticker: str, length: int, lookback_days: int, payload: dict) -> None:
    key = (ticker, int(length), int(lookback_days))
    _METRICS_CACHE[key] = (time.time(), payload)


def get_or_calculate_mbad_levels(ticker: str, length: int = 30, lookback_days: int = 30) -> dict:
    cached = _cache_get(ticker, length, lookback_days)
    if cached is not None:
        return cached
    payload = calculate_mbad_levels(ticker, length, lookback_days)
    _cache_set(ticker, length, lookback_days, payload)
    return payload


class LowerExtensionBatchRequest(BaseModel):
    tickers: list[str] = Field(..., min_length=1, max_length=200)
    length: int = 30
    lookback_days: int = 30


def _round_to_tick(value: float, tick_size: float = 0.01) -> float:
    if tick_size <= 0:
        return float(value)
    return float(np.round(value / tick_size) * tick_size)


def _weighted_moments(
    src_current_to_past: np.ndarray, weights: np.ndarray
) -> Tuple[float, float, float, float, float, float]:
    """
    PineScript-compatible weighted moments.
    Inputs are ordered current->past to mirror src[i] access in PineScript loops.
    """
    weights = np.asarray(weights, dtype=float)
    src = np.asarray(src_current_to_past, dtype=float)

    if src.size == 0 or weights.size != src.size:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    sum_w = float(np.sum(weights))
    if not np.isfinite(sum_w) or sum_w <= 0:
        # Fallback to unweighted moments if inferred-volume weights collapse to zero
        weights = np.ones_like(src, dtype=float)
        sum_w = float(src.size)

    mean = float(np.sum(src * weights) / sum_w)
    diffs = src - mean

    m2 = float(np.sum((diffs**2) * weights) / sum_w)
    dev = float(np.sqrt(max(m2, 0.0)))

    if not np.isfinite(dev) or dev <= 0:
        return mean, 0.0, 0.0, 0.0, 0.0, 0.0

    m3 = float(np.sum((diffs**3) * weights) / sum_w)
    m4 = float(np.sum((diffs**4) * weights) / sum_w)
    m5 = float(np.sum((diffs**5) * weights) / sum_w)
    m6 = float(np.sum((diffs**6) * weights) / sum_w)

    dev2 = dev * dev
    dev3 = dev2 * dev
    dev4 = dev2 * dev2
    dev5 = dev4 * dev
    dev6 = dev3 * dev3

    skew = float(m3 / dev3)
    kurt = float(m4 / dev4)
    hskew = float(m5 / dev5)
    hkurt = float(m6 / dev6)
    return mean, dev, skew, kurt, hskew, hkurt


def _mbad_levels_for_index(
    data: pd.DataFrame,
    idx: int,
    length: int,
    *,
    time_weighting: bool = True,
    inferred_volume_weighting: bool = True,
    tick_size: float = 0.01,
) -> Dict[str, float]:
    """
    Compute MBAD levels for a specific bar index, matching the provided PineScript.
    Uses source=close and weights: (len-i) * abs(close[i]-open[i]) by default.
    """
    window = data.iloc[idx - length + 1 : idx + 1]
    close_window = window["Close"].to_numpy(dtype=float)
    open_window = window["Open"].to_numpy(dtype=float)

    # Convert to PineScript indexing: element 0 is "current bar" within the window
    close_curr_to_past = close_window[::-1]
    open_curr_to_past = open_window[::-1]

    time_w = (np.arange(length, 0, -1, dtype=float) if time_weighting else 1.0)
    iv_w = (
        np.abs(close_curr_to_past - open_curr_to_past)
        if inferred_volume_weighting
        else 1.0
    )
    weights = time_w * iv_w

    mean, dev, skew, kurt, hskew, hkurt = _weighted_moments(close_curr_to_past, weights)

    # PineScript MBAD levels
    lim_lower = _round_to_tick(mean - dev * hkurt + dev * hskew, tick_size)
    ext_lower = _round_to_tick(mean - dev * kurt + dev * skew, tick_size)
    dev_lower = _round_to_tick(mean - dev, tick_size)
    dev_lower2 = _round_to_tick(mean - 2 * dev, tick_size)
    basis = _round_to_tick(mean, tick_size)
    dev_upper = _round_to_tick(mean + dev, tick_size)
    ext_upper = _round_to_tick(mean + dev * kurt + dev * skew, tick_size)
    lim_upper = _round_to_tick(mean + dev * hkurt + dev * hskew, tick_size)

    close_val = float(data["Close"].iloc[idx])
    zscore = float((close_val - mean) / dev) if dev > 0 else 0.0

    return {
        "lim_lower": lim_lower,
        "ext_lower": ext_lower,
        "dev_lower": dev_lower,
        "dev_lower2": dev_lower2,
        "basis": basis,
        "dev_upper": dev_upper,
        "ext_upper": ext_upper,
        "lim_upper": lim_upper,
        "zscore": zscore,
    }


def calculate_mbad_levels(ticker: str, length: int = 30, lookback_days: int = 30):
    """Calculate MBAD levels and signed distance-to-lower-extension metrics (PineScript-aligned)."""
    try:
        symbol = resolve_yahoo_symbol(ticker)
        end_date = datetime.now()
        # Calendar-day padding so we reliably get enough trading bars for `length`
        padding_days = int((lookback_days + length) * 2) + 10
        start_date = end_date - timedelta(days=padding_days)

        data = yf.download(
            symbol, start=start_date, end=end_date, progress=False, timeout=10
        )

        if data.empty:
            raise ValueError(f"No data available for {ticker}")

        # Flatten yfinance MultiIndex columns if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [c[0] for c in data.columns]

        data = data.dropna(subset=["Open", "Close"]).copy()
        if len(data) < length:
            # Some symbols (new listings, illiquid products) may not have enough bars yet.
            # Prefer returning a best-effort MBAD level rather than a hard failure.
            if len(data) < 5:
                raise ValueError(
                    f"Insufficient bars for MBAD: have {len(data)}, need {length}"
                )
            length = len(data)

        # MBAD settings requested: source=close, interpretation=mean reversion (levels unaffected)
        tick_size = 0.01
        current_idx = len(data) - 1
        current_levels = _mbad_levels_for_index(
            data, current_idx, length, tick_size=tick_size
        )

        current_price = float(data["Close"].iloc[-1])
        lower_ext_value = float(current_levels["ext_lower"])
        basis_value = float(current_levels["basis"])

        # Calculate comprehensive metrics for frontend
        pct_dist_lower_ext = (
            ((current_price - lower_ext_value) / lower_ext_value) * 100
            if lower_ext_value != 0
            else 0.0
        )
        is_below_lower_ext = pct_dist_lower_ext < 0
        abs_pct_dist_lower_ext = abs(pct_dist_lower_ext)

        # Calculate lookback metrics using each day's MBAD ext_lower (not a static 1σ band)
        lookback_rows = min(int(lookback_days), len(data))
        recent_data = data.tail(lookback_rows)
        pct_dists = []
        breach_count = 0

        start_i = len(data) - lookback_rows
        for i in range(start_i, len(data)):
            if i < length - 1:
                continue
            hist_levels = _mbad_levels_for_index(data, i, length, tick_size=tick_size)
            hist_lower_ext = float(hist_levels["ext_lower"])
            if not np.isfinite(hist_lower_ext) or hist_lower_ext == 0:
                continue
            hist_price = float(data["Close"].iloc[i])
            dist = ((hist_price - hist_lower_ext) / hist_lower_ext) * 100
            pct_dists.append(float(dist))
            if dist < 0:
                breach_count += 1

        min_pct_dist_30d = min(pct_dists) if pct_dists else 0
        median_abs_pct_dist_30d = np.median([abs(d) for d in pct_dists]) if pct_dists else 0
        breach_rate_30d = breach_count / len(pct_dists) if pct_dists else 0

        # Check if recently breached (last 5 points)
        recent_breached = any(d < 0 for d in pct_dists[-5:]) if len(pct_dists) >= 5 else False

        # Proximity score (0-1, normalized by 5% threshold)
        proximity_score_30d = max(0, min(1, 1 - (median_abs_pct_dist_30d / 5.0)))

        # Historical prices for last 30 days
        historical_prices = [
            {
                "timestamp": idx.isoformat(),
                "price": float(price)
            }
            for idx, price in recent_data["Close"].items()
        ]

        return {
            "symbol": ticker,
            "ticker": ticker,  # Keep both for compatibility
            "price": current_price,
            "current_price": current_price,  # Keep both for compatibility
            "lower_ext": lower_ext_value,
            "ma_baseline": basis_value,
            "levels": {
                # Preferred MBAD names (used by MBADIndicatorPage)
                "lim_lower": float(current_levels["lim_lower"]),
                "ext_lower": lower_ext_value,
                "dev_lower": float(current_levels["dev_lower"]),
                "dev_lower2": float(current_levels["dev_lower2"]),
                "basis": basis_value,
                "dev_upper": float(current_levels["dev_upper"]),
                "ext_upper": float(current_levels["ext_upper"]),
                "lim_upper": float(current_levels["lim_upper"]),
                # Back-compat aliases (legacy frontend keys)
                "lower_1sd": lower_ext_value,
            },
            "all_levels": {
                "lim_lower": float(current_levels["lim_lower"]),
                "ext_lower": lower_ext_value,
                "dev_lower": float(current_levels["dev_lower"]),
                "dev_lower2": float(current_levels["dev_lower2"]),
                "basis": basis_value,
                "dev_upper": float(current_levels["dev_upper"]),
                "ext_upper": float(current_levels["ext_upper"]),
                "lim_upper": float(current_levels["lim_upper"]),
                "zscore": float(current_levels["zscore"]),
                "lower_1sd": lower_ext_value,
            },
            "distance_from_baseline": float(
                ((current_price - basis_value) / basis_value) * 100 if basis_value != 0 else 0.0
            ),
            # Comprehensive metrics for frontend
            "pct_dist_lower_ext": round(pct_dist_lower_ext, 2),
            "is_below_lower_ext": is_below_lower_ext,
            "abs_pct_dist_lower_ext": round(abs_pct_dist_lower_ext, 2),
            "min_pct_dist_30d": round(min_pct_dist_30d, 2),
            "median_abs_pct_dist_30d": round(median_abs_pct_dist_30d, 2),
            "breach_count_30d": breach_count,
            "breach_rate_30d": round(breach_rate_30d, 4),
            "recent_breached": recent_breached,
            "proximity_score_30d": round(proximity_score_30d, 3),
            "historical_prices": historical_prices,
            "timestamp": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/metrics/{ticker}")
async def get_lower_extension_metrics(
    ticker: str, length: int = 30, lookback_days: int = 30
):
    """Get lower extension MBAD metrics for a ticker."""
    return await run_in_threadpool(get_or_calculate_mbad_levels, ticker.upper(), length, lookback_days)


@router.post("/metrics-batch")
async def get_lower_extension_metrics_batch(req: LowerExtensionBatchRequest):
    """
    Get lower extension MBAD metrics for multiple tickers.

    This reduces frontend fan-out (N requests) and applies a bounded concurrency
    limit so yfinance calls are less likely to timeout or get rate-limited.
    """

    tickers = [t.strip().upper() for t in req.tickers if t and t.strip()]
    if not tickers:
        raise HTTPException(status_code=400, detail="No tickers provided")

    sem = asyncio.Semaphore(4)
    results: dict[str, dict] = {}
    errors: dict[str, str] = {}

    async def work(ticker: str) -> None:
        async with sem:
            try:
                results[ticker] = await run_in_threadpool(
                    get_or_calculate_mbad_levels, ticker, req.length, req.lookback_days
                )
            except HTTPException as exc:
                errors[ticker] = str(exc.detail)
            except Exception as exc:
                errors[ticker] = str(exc)

    await asyncio.gather(*(work(t) for t in tickers))

    return {
        "results": results,
        "errors": errors,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/candles/{ticker}")
async def get_lower_extension_candles(
    ticker: str, days: int = 60  # Changed from 365 to 60 for faster loading
):
    """Get historical OHLC candle data with MBAD bands."""
    try:
        symbol = resolve_yahoo_symbol(ticker.upper())
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 30)  # Extra for MA calculation

        data = yf.download(
            symbol, start=start_date, end=end_date, progress=False, timeout=15
        )

        if data.empty:
            raise HTTPException(status_code=404, detail=f"No data for {ticker}")

        close = data["Close"]
        ma = close.rolling(window=30).mean()
        std = close.rolling(window=30).std()

        # Prepare response (limit to requested days)
        data_trimmed = data.tail(days)

        candles = []
        for idx, row in data_trimmed.iterrows():
            # Get MA and STD values safely
            try:
                ma_val = ma.loc[idx]
                std_val = std.loc[idx]

                # Handle MultiIndex or Series result
                if hasattr(ma_val, 'iloc'):
                    ma_val = ma_val.iloc[0]
                if hasattr(std_val, 'iloc'):
                    std_val = std_val.iloc[0]

                ma_float = float(ma_val) if not pd.isna(ma_val) else None
                std_float = float(std_val) if not pd.isna(std_val) else None
            except (KeyError, IndexError):
                ma_float = None
                std_float = None

            candles.append(
                {
                    # Back-compat: some pages expect `time`, older code used `date`
                    "time": idx.strftime("%Y-%m-%d"),
                    "date": idx.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                    "ma": ma_float,
                    "lower_1sd": float(ma_float - std_float) if (ma_float and std_float) else None,
                    "lower_2sd": float(ma_float - 2 * std_float) if (ma_float and std_float) else None,
                }
            )

        return {
            "ticker": ticker,
            "candles": candles,
            "count": len(candles),
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
