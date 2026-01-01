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
from ticker_utils import resolve_yahoo_symbol

router = APIRouter(prefix="/api/lower-extension", tags=["Lower Extension"])


def calculate_mbad_levels(ticker: str, length: int = 30, lookback_days: int = 30):
    """
    Calculate MBAD (Moving Baseline Adaptive Detection) levels.

    Returns lower extension bands based on moving average deviation.
    """
    try:
        # Resolve symbol
        symbol = resolve_yahoo_symbol(ticker)

        # Fetch data with timeout
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days + length)

        try:
            data = yf.download(
                symbol, start=start_date, end=end_date, progress=False, timeout=10
            )
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Data fetch timeout for {ticker}. Try again or use cached results.",
            )

        if data.empty:
            raise ValueError(f"No data available for {ticker}")

        close = data["Close"]

        # Calculate moving average baseline
        ma = close.rolling(window=length).mean()
        std = close.rolling(window=length).std()

        # MBAD levels (adaptive standard deviation bands)
        lower_1 = ma - (std * 1.0)
        lower_2 = ma - (std * 2.0)
        lower_3 = ma - (std * 3.0)

        current_price = float(close.iloc[-1])

        return {
            "ticker": ticker,
            "current_price": current_price,
            "ma_baseline": float(ma.iloc[-1]),
            "levels": {
                "lower_1sd": float(lower_1.iloc[-1]),
                "lower_2sd": float(lower_2.iloc[-1]),
                "lower_3sd": float(lower_3.iloc[-1]),
            },
            "distance_from_baseline": float(
                (current_price - ma.iloc[-1]) / ma.iloc[-1] * 100
            ),
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


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
        # Resolve symbol
        symbol = resolve_yahoo_symbol(ticker.upper())

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 30)  # Extra for MA calculation

        try:
            data = yf.download(
                symbol, start=start_date, end=end_date, progress=False, timeout=15
            )
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Data fetch timeout for {ticker}. Service may be rate-limited.",
            )

        if data.empty:
            raise HTTPException(status_code=404, detail=f"No data for {ticker}")

        # Calculate MBAD bands
        close = data["Close"]
        ma = close.rolling(window=30).mean()
        std = close.rolling(window=30).std()

        # Prepare response (limit to requested days)
        data_trimmed = data.tail(days)

        candles = []
        for idx, row in data_trimmed.iterrows():
            candles.append(
                {
                    "date": idx.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                    "ma": float(ma.loc[idx]) if not pd.isna(ma.loc[idx]) else None,
                    "lower_1sd": float(ma.loc[idx] - std.loc[idx])
                    if not pd.isna(ma.loc[idx])
                    else None,
                    "lower_2sd": float(ma.loc[idx] - 2 * std.loc[idx])
                    if not pd.isna(ma.loc[idx])
                    else None,
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
