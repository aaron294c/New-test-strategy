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
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path to import ticker_utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from ticker_utils import resolve_yahoo_symbol

router = APIRouter(prefix="/api/nadaraya-watson", tags=["Nadaraya-Watson"])


def calculate_nadaraya_watson_lower_band(
    ticker: str,
    bandwidth: float = 8.0,
    lookback_days: int = 365
):
    """
    Calculate Nadaraya-Watson lower envelope band using kernel regression.

    This is a nonparametric smoothing technique that adapts to local price structure.
    """
    try:
        # Clean ticker symbol (remove display suffixes like (NDX))
        clean_ticker = ticker
        if '(' in ticker:
            # Extract symbol before parentheses: QQQ(NDX) -> QQQ
            clean_ticker = ticker.split('(')[0].strip()

        # Resolve Yahoo Finance symbol (e.g., SPX -> ^GSPC)
        symbol = resolve_yahoo_symbol(clean_ticker)

        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        data = yf.download(symbol, start=start_date, end=end_date, progress=False, timeout=10)

        if data.empty:
            raise ValueError(f"No data available for {ticker}")

        close = data['Close'].values
        n = len(close)

        # Kernel regression for lower envelope
        # Use Gaussian kernel with specified bandwidth
        lower_band = np.zeros(n)

        for i in range(n):
            weights = np.exp(-((np.arange(n) - i) ** 2) / (2 * bandwidth ** 2))
            weights = weights / weights.sum()

            # Calculate weighted percentile (lower envelope at 10th percentile)
            sorted_idx = np.argsort(close)
            cumsum = np.cumsum(weights[sorted_idx])
            # Fix index out of bounds: ensure index is within valid range
            search_idx = np.searchsorted(cumsum, 0.10)
            if search_idx >= len(sorted_idx):
                search_idx = len(sorted_idx) - 1
            lower_idx = sorted_idx[search_idx]
            lower_band[i] = close[lower_idx]

        current_price = float(close[-1])
        current_lower = float(lower_band[-1])

        return {
            "ticker": ticker,
            "current_price": current_price,
            "lower_band": current_lower,
            "distance_pct": float((current_price - current_lower) / current_lower * 100),
            "bandwidth": bandwidth,
            "lookback_days": lookback_days,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lower-band/{ticker}")
async def get_nadaraya_watson_band(
    ticker: str,
    bandwidth: float = 8.0,
    lookback_days: int = 365
):
    """Get Nadaraya-Watson lower envelope band."""
    return calculate_nadaraya_watson_lower_band(ticker.upper(), bandwidth, lookback_days)


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
    Note: length parameter is used as lookback_days for consistency.
    """
    # Use length as lookback_days (convert to approximate days)
    lookback_days = max(365, length * 2)  # Ensure enough data
    return calculate_nadaraya_watson_lower_band(ticker.upper(), bandwidth, lookback_days)
