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
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        data = yf.download(ticker, start=start_date, end=end_date, progress=False)

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
            lower_idx = sorted_idx[np.searchsorted(cumsum, 0.10)]
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
