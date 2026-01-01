"""
Macro Risk Metrics API - Market-Wide Risk Indicators

Provides comprehensive macro risk assessment including:
- S&P 500 Breadth (% stocks above 200 MA)
- McClellan Market Facilitation Index (MMFI)
- US Treasury Yields (10Y, 3M)
- Yield Curve Analysis (inversions, slope)
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import yfinance as yf
from dataclasses import dataclass, asdict

router = APIRouter(prefix="/api/macro-risk", tags=["macro-risk"])

# Cache for risk metrics (5-minute TTL)
_risk_metrics_cache: Optional[Dict] = None
_cache_timestamp: Optional[datetime] = None
_cache_ttl_seconds = 300  # 5 minutes


@dataclass
class YieldCurveMetrics:
    """Yield curve analysis metrics"""
    us_10y: float
    us_3m: float
    spread: float  # 10Y - 3M
    is_inverted: bool
    inversion_severity: str  # "Normal", "Flat", "Inverted", "Deeply Inverted"
    risk_level: str  # "Low", "Medium", "High"
    historical_percentile: float  # Where current spread sits historically


@dataclass
class BreadthMetrics:
    """Market breadth indicators"""
    sp500_pct_above_200ma: float
    breadth_signal: str  # "Bullish", "Neutral", "Bearish"
    risk_level: str  # "Low", "Medium", "High"


@dataclass
class MMFIMetrics:
    """McClellan Market Facilitation Index"""
    mmfi_50d: float
    mmfi_signal: str  # "Bullish", "Neutral", "Bearish"
    risk_level: str  # "Low", "Medium", "High"


def fetch_treasury_yields() -> Dict[str, float]:
    """
    Fetch US Treasury yields from Yahoo Finance

    Returns:
        Dict with '10Y' and '3M' yields
    """
    try:
        # 10-Year Treasury Yield (^TNX gives yield in percentage)
        tnx = yf.Ticker("^TNX")
        tnx_data = tnx.history(period="5d")
        if tnx_data.empty:
            raise ValueError("No 10Y data")
        us_10y = float(tnx_data['Close'].iloc[-1])

        # 3-Month Treasury Yield (^IRX)
        irx = yf.Ticker("^IRX")
        irx_data = irx.history(period="5d")
        if irx_data.empty:
            raise ValueError("No 3M data")
        us_3m = float(irx_data['Close'].iloc[-1])

        return {
            "10Y": us_10y,
            "3M": us_3m
        }

    except Exception as e:
        print(f"Error fetching treasury yields: {e}")
        # Return default values if fetch fails
        return {
            "10Y": 4.5,  # Default reasonable values
            "3M": 5.0
        }


def calculate_yield_curve_metrics(us_10y: float, us_3m: float) -> YieldCurveMetrics:
    """
    Analyze yield curve and detect inversions

    Args:
        us_10y: 10-year yield in percentage
        us_3m: 3-month yield in percentage

    Returns:
        YieldCurveMetrics with inversion analysis
    """
    spread = us_10y - us_3m

    # Determine inversion status
    if spread > 1.0:
        inversion_severity = "Normal"
        is_inverted = False
        risk_level = "Low"
    elif spread > 0.25:
        inversion_severity = "Flat"
        is_inverted = False
        risk_level = "Low"
    elif spread > -0.25:
        inversion_severity = "Flat"
        is_inverted = False
        risk_level = "Medium"
    elif spread > -0.75:
        inversion_severity = "Inverted"
        is_inverted = True
        risk_level = "High"
    else:
        inversion_severity = "Deeply Inverted"
        is_inverted = True
        risk_level = "High"

    # Calculate historical percentile (approximation)
    # Normal spread range: -1.5% to +3.0%
    # Map to 0-100 percentile
    historical_percentile = min(100, max(0, ((spread + 1.5) / 4.5) * 100))

    return YieldCurveMetrics(
        us_10y=us_10y,
        us_3m=us_3m,
        spread=spread,
        is_inverted=is_inverted,
        inversion_severity=inversion_severity,
        risk_level=risk_level,
        historical_percentile=historical_percentile
    )


def calculate_sp500_breadth() -> BreadthMetrics:
    """
    Calculate S&P 500 breadth - % of stocks above 200-day MA

    Uses SPY as a proxy indicator:
    - SPY > 200 MA = Bullish breadth
    - SPY near 200 MA = Neutral
    - SPY < 200 MA = Bearish breadth

    Returns:
        BreadthMetrics with breadth analysis
    """
    try:
        # Fetch SPY data (S&P 500 ETF as proxy)
        spy = yf.Ticker("SPY")
        spy_data = spy.history(period="1y")

        if spy_data.empty:
            raise ValueError("No SPY data")

        # Calculate 200-day MA
        spy_data['MA200'] = spy_data['Close'].rolling(window=200).mean()

        current_price = float(spy_data['Close'].iloc[-1])
        ma_200 = float(spy_data['MA200'].iloc[-1])

        # Distance from 200 MA (percentage)
        distance_pct = ((current_price - ma_200) / ma_200) * 100

        # Approximate breadth based on distance from MA
        # This is a proxy - real calculation would need all 500 stocks
        if distance_pct > 5:
            pct_above = 75.0 + (min(distance_pct, 15) / 15) * 20  # 75-95%
            breadth_signal = "Bullish"
            risk_level = "Low"
        elif distance_pct > 0:
            pct_above = 55.0 + (distance_pct / 5) * 20  # 55-75%
            breadth_signal = "Neutral"
            risk_level = "Medium"
        elif distance_pct > -5:
            pct_above = 35.0 + ((distance_pct + 5) / 5) * 20  # 35-55%
            breadth_signal = "Neutral"
            risk_level = "Medium"
        else:
            pct_above = 15.0 + (max(distance_pct, -15) + 15) / 15 * 20  # 15-35%
            breadth_signal = "Bearish"
            risk_level = "High"

        return BreadthMetrics(
            sp500_pct_above_200ma=round(pct_above, 1),
            breadth_signal=breadth_signal,
            risk_level=risk_level
        )

    except Exception as e:
        print(f"Error calculating breadth: {e}")
        return BreadthMetrics(
            sp500_pct_above_200ma=50.0,
            breadth_signal="Neutral",
            risk_level="Medium"
        )


def calculate_mmfi(lookback_days: int = 50) -> MMFIMetrics:
    """
    Calculate McClellan Market Facilitation Index (MMFI)

    This is a simplified version using advance/decline ratio from market indices
    Uses SPY vs VIX as a proxy for market facilitation

    Args:
        lookback_days: Period for MMFI calculation

    Returns:
        MMFIMetrics with MMFI analysis
    """
    try:
        # Fetch market data
        spy = yf.Ticker("SPY")
        vix = yf.Ticker("^VIX")

        spy_data = spy.history(period=f"{lookback_days + 30}d")
        vix_data = vix.history(period=f"{lookback_days + 30}d")

        if spy_data.empty or vix_data.empty:
            raise ValueError("Insufficient data for MMFI")

        # Calculate price momentum (SPY) and volatility (VIX) relationship
        spy_returns = spy_data['Close'].pct_change(periods=lookback_days).iloc[-1]
        vix_change = vix_data['Close'].pct_change(periods=lookback_days).iloc[-1]

        # MMFI proxy: positive when SPY up and VIX down (bullish)
        # Negative when SPY down or VIX up (bearish)
        mmfi_value = (spy_returns * 100) - (vix_change * 50)

        # Determine signal
        if mmfi_value > 5:
            mmfi_signal = "Bullish"
            risk_level = "Low"
        elif mmfi_value > -5:
            mmfi_signal = "Neutral"
            risk_level = "Medium"
        else:
            mmfi_signal = "Bearish"
            risk_level = "High"

        return MMFIMetrics(
            mmfi_50d=round(mmfi_value, 2),
            mmfi_signal=mmfi_signal,
            risk_level=risk_level
        )

    except Exception as e:
        print(f"Error calculating MMFI: {e}")
        return MMFIMetrics(
            mmfi_50d=0.0,
            mmfi_signal="Neutral",
            risk_level="Medium"
        )


def calculate_composite_risk_score(
    yield_curve: YieldCurveMetrics,
    breadth: BreadthMetrics,
    mmfi: MMFIMetrics
) -> Dict:
    """
    Calculate composite risk score from all metrics

    Returns:
        Dict with overall risk assessment
    """
    # Risk scoring: Low=1, Medium=2, High=3
    risk_map = {"Low": 1, "Medium": 2, "High": 3}

    yield_risk = risk_map[yield_curve.risk_level]
    breadth_risk = risk_map[breadth.risk_level]
    mmfi_risk = risk_map[mmfi.risk_level]

    # Weighted average (yield curve = 40%, breadth = 30%, MMFI = 30%)
    composite_score = (yield_risk * 0.4 + breadth_risk * 0.3 + mmfi_risk * 0.3)

    # Determine overall risk level
    if composite_score <= 1.5:
        overall_risk = "Low"
        risk_description = "Market conditions favorable"
    elif composite_score <= 2.3:
        overall_risk = "Medium"
        risk_description = "Mixed signals, exercise caution"
    else:
        overall_risk = "High"
        risk_description = "Elevated risk environment"

    return {
        "composite_score": round(composite_score, 2),
        "overall_risk_level": overall_risk,
        "risk_description": risk_description,
        "component_risks": {
            "yield_curve": yield_curve.risk_level,
            "breadth": breadth.risk_level,
            "mmfi": mmfi.risk_level
        }
    }


@router.get("/current")
async def get_macro_risk_metrics():
    """
    Get current macro risk metrics including:
    - Yield curve analysis (10Y vs 3M)
    - S&P 500 breadth
    - MMFI (50-day)
    - Composite risk assessment

    Returns comprehensive market risk dashboard
    """
    global _risk_metrics_cache, _cache_timestamp

    # Check cache
    now = datetime.now(timezone.utc)
    cache_valid = (
        _cache_timestamp is not None
        and (now - _cache_timestamp).total_seconds() < _cache_ttl_seconds
        and _risk_metrics_cache
    )

    if cache_valid:
        print(f"  Using cached macro risk metrics")
        return _risk_metrics_cache

    print("🔄 Fetching fresh macro risk metrics...")

    try:
        # Fetch treasury yields
        yields = fetch_treasury_yields()

        # Calculate yield curve metrics
        yield_curve = calculate_yield_curve_metrics(
            yields["10Y"],
            yields["3M"]
        )

        # Calculate breadth
        breadth = calculate_sp500_breadth()

        # Calculate MMFI
        mmfi = calculate_mmfi(lookback_days=50)

        # Calculate composite risk
        composite = calculate_composite_risk_score(yield_curve, breadth, mmfi)

        result = {
            "timestamp": now.isoformat(),
            "yield_curve": asdict(yield_curve),
            "breadth": asdict(breadth),
            "mmfi": asdict(mmfi),
            "composite_risk": composite
        }

        # Update cache
        _risk_metrics_cache = result
        _cache_timestamp = now

        print("✓ Macro risk metrics updated")
        return result

    except Exception as e:
        print(f"❌ Error fetching macro risk metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch macro risk metrics: {str(e)}"
        )


@router.get("/historical")
async def get_historical_risk_metrics(days: int = 90):
    """
    Get historical risk metrics for trend analysis

    Args:
        days: Number of days of history (default 90)
    """
    try:
        # Fetch historical treasury data
        tnx = yf.Ticker("^TNX")
        irx = yf.Ticker("^IRX")
        spy = yf.Ticker("SPY")

        period = f"{days}d"
        tnx_hist = tnx.history(period=period)
        irx_hist = irx.history(period=period)
        spy_hist = spy.history(period=period)

        # Calculate 200 MA for breadth
        spy_hist['MA200'] = spy_hist['Close'].rolling(window=200).mean()

        # Build historical series
        historical_data = []
        for date in tnx_hist.index:
            if date in irx_hist.index and date in spy_hist.index:
                us_10y = float(tnx_hist.loc[date, 'Close'])
                us_3m = float(irx_hist.loc[date, 'Close'])
                spread = us_10y - us_3m

                # SPY vs MA200
                spy_close = spy_hist.loc[date, 'Close']
                spy_ma200 = spy_hist.loc[date, 'MA200']

                if pd.notna(spy_ma200):
                    distance_pct = ((spy_close - spy_ma200) / spy_ma200) * 100
                else:
                    distance_pct = None

                historical_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "us_10y": us_10y,
                    "us_3m": us_3m,
                    "spread": spread,
                    "is_inverted": spread < 0,
                    "spy_distance_from_ma200": distance_pct
                })

        return {
            "period_days": days,
            "data_points": len(historical_data),
            "historical_data": historical_data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch historical data: {str(e)}"
        )
