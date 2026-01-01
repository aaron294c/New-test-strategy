"""
Multi-Timeframe Trading API Router
Endpoints for stock metadata, bins, and trading recommendations
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict
from stock_statistics import (
    get_stock_data,
    calculate_position_size,
    get_action_for_4h_bin,
    STOCK_METADATA
)

router = APIRouter(tags=["multi-timeframe"])


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class StockPosition(BaseModel):
    ticker: str
    current_4h_bin: str
    current_daily_bin: str


class TradingRecommendation(BaseModel):
    ticker: str
    stock_name: str
    personality: str

    # Current status
    current_4h_bin: str
    current_daily_bin: str

    # 4H statistics
    fourh_mean: float
    fourh_t_score: float
    fourh_is_significant: bool
    fourh_signal_strength: str

    # Daily statistics
    daily_mean: float
    daily_t_score: float
    daily_is_significant: bool
    daily_signal_strength: str

    # Recommendation
    recommended_action: str
    position_size: str
    confidence: str
    detailed_guidance: str

    # Risk management
    stop_loss_5th_percentile: float
    upside_95th_percentile: float


# ============================================
# ENDPOINTS
# ============================================

@router.get("/stocks")
async def list_stocks():
    """List all available stocks with metadata"""
    return {
        ticker: {
            "name": meta.name,
            "personality": meta.personality,
            "reliability_4h": meta.reliability_4h,
            "reliability_daily": meta.reliability_daily,
            "ease_rating": meta.ease_rating,
            "best_4h_bin": meta.best_4h_bin,
            "best_4h_t_score": meta.best_4h_t_score
        }
        for ticker, meta in STOCK_METADATA.items()
    }


@router.get("/stock/{ticker}")
async def get_stock_info(ticker: str):
    """Get detailed stock metadata"""
    ticker = ticker.upper()
    if ticker not in STOCK_METADATA:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    meta = STOCK_METADATA[ticker]
    return {
        "ticker": meta.ticker,
        "name": meta.name,
        "personality": meta.personality,
        "reliability_4h": meta.reliability_4h,
        "reliability_daily": meta.reliability_daily,
        "tradeable_4h_zones": meta.tradeable_4h_zones,
        "dead_zones_4h": meta.dead_zones_4h,
        "best_4h_bin": meta.best_4h_bin,
        "best_4h_t_score": meta.best_4h_t_score,
        "ease_rating": meta.ease_rating,
        "characteristics": {
            "is_mean_reverter": meta.is_mean_reverter,
            "is_momentum": meta.is_momentum,
            "volatility_level": meta.volatility_level
        },
        "guidance": {
            "entry": meta.entry_guidance,
            "avoid": meta.avoid_guidance,
            "special_notes": meta.special_notes
        }
    }


@router.get("/bins/{ticker}/{timeframe}")
async def get_bin_statistics(ticker: str, timeframe: str):
    """Get all percentile bin statistics for a stock and timeframe"""
    ticker = ticker.upper()
    timeframe = "4H" if timeframe.lower() in ["4h", "4hour", "hourly"] else "Daily"

    try:
        data = get_stock_data(ticker, timeframe)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    bins = []
    for bin_range, stats in data.items():
        action_info = get_action_for_4h_bin(bin_range, stats) if timeframe == "4H" else {
            "action": "See 7d forecast",
            "size": "Based on t-score",
            "color": "info"
        }

        bins.append({
            "bin_range": stats.bin_range,
            "mean": stats.mean,
            "median": stats.median,
            "std": stats.std,
            "sample_size": stats.sample_size,
            "t_score": stats.t_score,
            "is_significant": stats.is_significant,
            "signal_strength": stats.significance_level.value,
            "confidence_interval_95": stats.confidence_interval_95,
            "percentile_5th": stats.percentile_5th,
            "percentile_95th": stats.percentile_95th,
            "upside": stats.upside,
            "downside": stats.downside,
            "action": action_info["action"],
            "position_size_guidance": action_info["size"],
            "action_color": action_info["color"]
        })

    return {
        "ticker": ticker,
        "timeframe": timeframe,
        "horizon": "48h" if timeframe == "4H" else "7d",
        "bins": bins
    }


@router.get("/trade-management/{ticker}")
async def get_trade_management(ticker: str):
    """Get trading rules and position management for ticker"""
    ticker = ticker.upper()
    if ticker not in STOCK_METADATA:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    meta = STOCK_METADATA[ticker]
    return {
        "ticker": ticker,
        "name": meta.name,
        "personality": meta.personality,
        "tradeable_zones": meta.tradeable_4h_zones,
        "dead_zones": meta.dead_zones_4h,
        "entry_guidance": meta.entry_guidance,
        "avoid_guidance": meta.avoid_guidance,
        "special_notes": meta.special_notes,
        "ease_rating": meta.ease_rating
    }


@router.post("/recommendation")
async def get_trading_recommendation(position: StockPosition) -> TradingRecommendation:
    """Get trading recommendation for current position"""
    ticker = position.ticker.upper()

    if ticker not in STOCK_METADATA:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    # Get data
    fourh_data = get_stock_data(ticker, "4H")
    daily_data = get_stock_data(ticker, "Daily")

    # Get current bin stats
    fourh_bin_key = position.current_4h_bin.replace("%", "").replace(" ", "")
    daily_bin_key = position.current_daily_bin.replace("%", "").replace(" ", "")

    if fourh_bin_key not in fourh_data:
        raise HTTPException(status_code=400, detail=f"Invalid 4H bin: {position.current_4h_bin}")
    if daily_bin_key not in daily_data:
        raise HTTPException(status_code=400, detail=f"Invalid Daily bin: {position.current_daily_bin}")

    fourh_stats = fourh_data[fourh_bin_key]
    daily_stats = daily_data[daily_bin_key]

    # Calculate position
    position_calc = calculate_position_size(daily_stats.t_score, fourh_stats.t_score)

    # Generate detailed guidance
    meta = STOCK_METADATA[ticker]
    guidance_parts = []

    # Check Daily first
    if not daily_stats.is_significant:
        guidance_parts.append(f"⚠️ Daily 7d signal is weak (t={daily_stats.t_score:.2f}, need ≥2.0). Consider skipping.")
    else:
        guidance_parts.append(f"✅ Daily 7d signal is significant (t={daily_stats.t_score:.2f}): {'+' if daily_stats.mean > 0 else ''}{daily_stats.mean:.2f}% expected.")

    # Check 4H
    if not fourh_stats.is_significant:
        guidance_parts.append(f"⚠️ 4H signal at {position.current_4h_bin} is not significant (t={fourh_stats.t_score:.2f}).")
        if position.current_4h_bin in meta.dead_zones_4h:
            guidance_parts.append(f"❌ DEAD ZONE: This 4H percentile historically has no predictive power for {ticker}.")
            guidance_parts.append(f"💡 WAIT for 4H to enter: {', '.join(meta.tradeable_4h_zones)}")
        else:
            guidance_parts.append(f"Consider waiting for better 4H entry.")
    else:
        guidance_parts.append(f"✅ 4H signal is significant (t={fourh_stats.t_score:.2f}): {'+' if fourh_stats.mean > 0 else ''}{fourh_stats.mean:.2f}% expected (48h).")

    # Add stock-specific notes
    guidance_parts.append(f"📊 {meta.personality}: {meta.special_notes}")

    detailed_guidance = " ".join(guidance_parts)

    return TradingRecommendation(
        ticker=ticker,
        stock_name=meta.name,
        personality=meta.personality,
        current_4h_bin=position.current_4h_bin,
        current_daily_bin=position.current_daily_bin,
        fourh_mean=fourh_stats.mean,
        fourh_t_score=fourh_stats.t_score,
        fourh_is_significant=fourh_stats.is_significant,
        fourh_signal_strength=fourh_stats.significance_level.value,
        daily_mean=daily_stats.mean,
        daily_t_score=daily_stats.t_score,
        daily_is_significant=daily_stats.is_significant,
        daily_signal_strength=daily_stats.significance_level.value,
        recommended_action=position_calc["action"],
        position_size=position_calc["position"],
        confidence=position_calc["confidence"],
        detailed_guidance=detailed_guidance,
        stop_loss_5th_percentile=fourh_stats.percentile_5th,
        upside_95th_percentile=fourh_stats.percentile_95th
    )


@router.get("/position-calculator")
async def calculate_position(
    daily_t: float = Query(..., description="Daily 7d t-score"),
    fourh_t: float = Query(..., description="4H 48h t-score")
):
    """Calculate position size from t-scores"""
    result = calculate_position_size(daily_t, fourh_t)

    daily_score = min(max(daily_t / 2.0, 0), 2)
    fourh_score = min(max(fourh_t / 2.0, 0), 2)

    return {
        "daily_t_score": daily_t,
        "fourh_t_score": fourh_t,
        "daily_score": round(daily_score, 2),
        "fourh_score": round(fourh_score, 2),
        "recommended_position": result["position"],
        "confidence": result["confidence"],
        "action": result["action"]
    }
