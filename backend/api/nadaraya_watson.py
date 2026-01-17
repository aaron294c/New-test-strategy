"""
Nadaraya-Watson Envelope Calculator
Implements the Nadaraya-Watson kernel regression with ATR-based envelope bands.

Formula:
- nw_estimate = Σ(price[i] * weight[i]) / Σ(weight[i])
- weight[i] = exp(-(i^2) / (2 * h^2))
- lower_band = nw_estimate - (ATR(atr_period) * atr_mult)
- pct_from_lower_band = 100 * (price - lower_band) / lower_band
- lower_band_breached = price < lower_band
"""

from fastapi import APIRouter, HTTPException
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple, Union

# Add parent directory to path to import ticker_utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from ticker_utils import resolve_yahoo_symbol

router = APIRouter(prefix="/api/nadaraya-watson", tags=["Nadaraya-Watson"])

_EPS = 1e-8


def _as_np_array(values: Optional[Union[Sequence[float], np.ndarray]]) -> Optional[np.ndarray]:
    if values is None:
        return None
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 1:
        arr = arr.reshape(-1)
    return arr


def _rma(values: np.ndarray, length: int) -> Optional[float]:
    if length <= 0:
        return None
    if values.size < length:
        return None
    seed = float(np.mean(values[:length]))
    rma = seed
    for i in range(length, values.size):
        rma = (rma * (length - 1) + float(values[i])) / length
    return rma


def _atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, length: int) -> Optional[float]:
    if closes.size == 0:
        return None
    if not (highs.size == lows.size == closes.size):
        return None

    tr = np.empty(closes.size, dtype=float)
    tr[0] = float(highs[0] - lows[0])
    prev_close = float(closes[0])
    for i in range(1, closes.size):
        high = float(highs[i])
        low = float(lows[i])
        true_range = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr[i] = true_range
        prev_close = float(closes[i])

    return _rma(tr, length)


def _nw_estimate(closes: np.ndarray, length: int, bandwidth: float) -> Optional[float]:
    if closes.size == 0:
        return None
    if length <= 0 or bandwidth <= 0:
        return None

    k = int(min(length, closes.size))
    idx = np.arange(k, dtype=float)
    weights = np.exp(-(idx**2) / (2.0 * (bandwidth**2)))
    weights_sum = float(np.sum(weights))
    if weights_sum <= 0:
        return None

    window = closes[-k:][::-1]  # most recent first to match PineScript src[i]
    return float(np.dot(window, weights) / weights_sum)


def _download_ohlc(ticker: str, lookback_days: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    import yfinance as yf

    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    data = yf.download(ticker, start=start_date, end=end_date, progress=False, timeout=10)

    if data is None or getattr(data, "empty", True):
        raise ValueError(f"No data available for {ticker}")

    # yfinance can return a MultiIndex column frame; normalize for single-symbol usage
    try:
        import pandas as pd  # noqa: F401

        if hasattr(data, "columns") and getattr(data.columns, "nlevels", 1) > 1:
            data = data.droplevel(0, axis=1)
    except Exception:
        pass

    closes = np.asarray(data["Close"].values, dtype=float)
    highs = np.asarray(data["High"].values, dtype=float)
    lows = np.asarray(data["Low"].values, dtype=float)

    mask = np.isfinite(closes) & np.isfinite(highs) & np.isfinite(lows)
    closes = closes[mask]
    highs = highs[mask]
    lows = lows[mask]

    if closes.size == 0:
        raise ValueError(f"No valid OHLC data for {ticker}")

    return closes, highs, lows


def calculate_nadaraya_watson_lower_band(
    prices_or_ticker: Union[str, Sequence[float], np.ndarray],
    length: int = 200,
    bandwidth: float = 8.0,
    atr_period: int = 50,
    atr_mult: float = 2.0,
    highs: Optional[Union[Sequence[float], np.ndarray]] = None,
    lows: Optional[Union[Sequence[float], np.ndarray]] = None,
    lookback_days: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Calculate the Nadaraya-Watson estimate and ATR envelope for the most recent bar.

    Matches the PineScript logic used by the Risk Distance tab:
    - weights[i] = exp(-(i^2) / (2 * h^2))
    - nw_estimate = sum(src[i] * weights[i]) / sum(weights[i])  (i=0 is current bar)
    - lower_band = nw_estimate - ATR(atr_period) * atr_mult
    """
    closes = None
    symbol = None
    if isinstance(prices_or_ticker, str):
        # Clean display suffixes like QQQ(NDX) -> QQQ
        clean_ticker = prices_or_ticker.split("(")[0].strip()
        symbol = resolve_yahoo_symbol(clean_ticker.upper())

        required_bars = max(int(length), int(atr_period)) + 5
        computed_lookback_days = max(365, int(required_bars * 3))
        closes, highs_arr, lows_arr = _download_ohlc(symbol, lookback_days or computed_lookback_days)
    else:
        closes = _as_np_array(prices_or_ticker)
        highs_arr = _as_np_array(highs) if highs is not None else None
        lows_arr = _as_np_array(lows) if lows is not None else None

        if closes is None:
            raise ValueError("Prices array is missing")
        if highs_arr is None or lows_arr is None:
            highs_arr = closes.copy()
            lows_arr = closes.copy()

    if closes.size == 0:
        return {
            "symbol": symbol,
            "nw_estimate": None,
            "lower_band": None,
            "upper_band": None,
            "lower_band_breached": False,
            "pct_from_lower_band": None,
            "atr": None,
            "current_price": None,
            "is_valid": False,
            "length": int(length),
            "bandwidth": float(bandwidth),
            "atr_period": int(atr_period),
            "atr_mult": float(atr_mult),
            "timestamp": datetime.now().isoformat(),
        }

    # PineScript behavior:
    # - NW estimate uses as many bars as available up to `length`
    # - ATR is `na` until `atr_period` bars exist (Wilder/RMA warmup)
    min_bars = max(int(atr_period), 1)
    current_price = float(closes[-1])
    if closes.size < min_bars:
        return {
            "symbol": symbol,
            "nw_estimate": None,
            "lower_band": None,
            "upper_band": None,
            "lower_band_breached": False,
            "pct_from_lower_band": None,
            "atr": None,
            "current_price": current_price,
            "is_valid": False,
            "length": int(length),
            "bandwidth": float(bandwidth),
            "atr_period": int(atr_period),
            "atr_mult": float(atr_mult),
            "timestamp": datetime.now().isoformat(),
        }

    nw = _nw_estimate(closes, int(length), float(bandwidth))
    atr = _atr(highs_arr, lows_arr, closes, int(atr_period))
    if nw is None or atr is None:
        return {
            "symbol": symbol,
            "nw_estimate": nw,
            "lower_band": None,
            "upper_band": None,
            "lower_band_breached": False,
            "pct_from_lower_band": None,
            "atr": atr,
            "current_price": current_price,
            "is_valid": False,
            "length": int(length),
            "bandwidth": float(bandwidth),
            "atr_period": int(atr_period),
            "atr_mult": float(atr_mult),
            "timestamp": datetime.now().isoformat(),
        }

    envelope = float(atr) * float(atr_mult)
    upper_band = float(nw) + envelope
    lower_band = float(nw) - envelope

    pct_from_lower = None
    if abs(lower_band) > _EPS:
        pct_from_lower = float(100.0 * (current_price - lower_band) / lower_band)

    return {
        "symbol": symbol,
        "nw_estimate": float(nw),
        "lower_band": float(lower_band),
        "upper_band": float(upper_band),
        "lower_band_breached": bool(current_price < lower_band),
        "pct_from_lower_band": pct_from_lower,
        "atr": float(atr),
        "current_price": current_price,
        "is_valid": True,
        "length": int(length),
        "bandwidth": float(bandwidth),
        "atr_period": int(atr_period),
        "atr_mult": float(atr_mult),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/lower-band/{ticker}")
async def get_nadaraya_watson_band(
    ticker: str,
    length: int = 200,
    bandwidth: float = 8.0,
    atr_period: int = 50,
    atr_mult: float = 2.0,
    lookback_days: int = 365,
):
    """Get Nadaraya-Watson lower envelope band (plus metrics) for a ticker."""
    try:
        return calculate_nadaraya_watson_lower_band(
            ticker.upper(),
            length=length,
            bandwidth=bandwidth,
            atr_period=atr_period,
            atr_mult=atr_mult,
            lookback_days=lookback_days,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{ticker}")
async def get_nadaraya_watson_metrics(
    ticker: str,
    length: int = 200,
    bandwidth: float = 8.0,
    atr_period: int = 50,
    atr_mult: float = 2.0
):
    """
    Get Nadaraya-Watson metrics for frontend compatibility.
    """
    try:
        return calculate_nadaraya_watson_lower_band(
            ticker.upper(),
            length=length,
            bandwidth=bandwidth,
            atr_period=atr_period,
            atr_mult=atr_mult,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
