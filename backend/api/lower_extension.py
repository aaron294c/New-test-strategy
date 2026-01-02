"""
Lower Extension Distance API
Provides calculation functions for lower extension metrics
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path to import ticker_utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from ticker_utils import resolve_yahoo_symbol

router = APIRouter(prefix="/api/lower-extension", tags=["Lower Extension"])


def calculate_mbad_levels(ticker: str, length: int = 30, lookback_days: int = 30):
    """Calculate MBAD (Moving Baseline Adaptive Detection) levels with comprehensive metrics."""
    try:
        symbol = resolve_yahoo_symbol(ticker)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days + length)

        data = yf.download(
            symbol, start=start_date, end=end_date, progress=False, timeout=10
        )

        if data.empty:
            raise ValueError(f"No data available for {ticker}")

        close = data["Close"]
        ma = close.rolling(window=length).mean()
        std = close.rolling(window=length).std()

        lower_1 = ma - (std * 1.0)
        lower_2 = ma - (std * 2.0)
        lower_3 = ma - (std * 3.0)

        current_price = float(close.iloc[-1])
        lower_ext_value = float(lower_1.iloc[-1])

        # Calculate comprehensive metrics for frontend
        pct_dist_lower_ext = ((current_price - lower_ext_value) / lower_ext_value) * 100
        is_below_lower_ext = pct_dist_lower_ext < 0
        abs_pct_dist_lower_ext = abs(pct_dist_lower_ext)

        # Calculate 30-day lookback metrics
        recent_data = close.tail(min(30, len(close)))
        pct_dists = []
        breach_count = 0

        for i in range(len(recent_data)):
            if i >= length:  # Only calculate when we have enough data for MA
                hist_ma = recent_data.iloc[max(0, i - length):i + 1].mean()
                hist_std = recent_data.iloc[max(0, i - length):i + 1].std()
                hist_lower = hist_ma - hist_std

                if pd.notna(hist_lower) and hist_lower > 0:
                    hist_price = recent_data.iloc[i]
                    dist = ((hist_price - hist_lower) / hist_lower) * 100
                    pct_dists.append(dist)
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
            for idx, price in recent_data.items()
        ]

        return {
            "symbol": ticker,
            "ticker": ticker,  # Keep both for compatibility
            "price": current_price,
            "current_price": current_price,  # Keep both for compatibility
            "lower_ext": lower_ext_value,
            "ma_baseline": float(ma.iloc[-1]),
            "levels": {
                "lower_1sd": lower_ext_value,
                "lower_2sd": float(lower_2.iloc[-1]),
                "lower_3sd": float(lower_3.iloc[-1]),
            },
            "all_levels": {
                "lower_1sd": lower_ext_value,
                "lower_2sd": float(lower_2.iloc[-1]),
                "lower_3sd": float(lower_3.iloc[-1]),
            },
            "distance_from_baseline": float(
                (current_price - ma.iloc[-1]) / ma.iloc[-1] * 100
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
    return calculate_mbad_levels(ticker.upper(), length, lookback_days)


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
