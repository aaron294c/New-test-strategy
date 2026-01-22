#!/usr/bin/env python3
"""
FastAPI Backend for RSI-MA Performance Analytics Dashboard

Endpoints:
- /api/backtest/{ticker} - Get backtest results for a ticker
- /api/backtest/batch - Run backtest for multiple tickers
- /api/monte-carlo/{ticker} - Get Monte Carlo simulation results
- /api/performance-matrix/{ticker}/{threshold} - Get performance matrix
- /api/optimal-exit/{ticker}/{threshold} - Get optimal exit strategy
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import asyncio
import os
import time
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import json
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from pathlib import Path

from enhanced_backtester import EnhancedPerformanceMatrixBacktester
from monte_carlo_simulator import MonteCarloSimulator, run_monte_carlo_for_ticker
from advanced_backtest_runner import AdvancedBacktestRunner, run_advanced_backtest
from live_signal_generator import generate_live_signals, generate_exit_signal_for_position
from multi_timeframe_analyzer import run_multi_timeframe_analysis
from percentile_threshold_analyzer import PercentileThresholdAnalyzer
from convergence_analyzer import analyze_convergence_for_ticker
from position_manager import get_position_management
from enhanced_mtf_analyzer import run_enhanced_analysis
from percentile_forward_mapping import run_percentile_forward_analysis
from swing_duration_analysis_v2 import analyze_swing_duration_v2
from swing_duration_intraday import analyze_swing_duration_intraday
from mapi_calculator import MAPICalculator, prepare_mapi_chart_data
from stock_statistics import (
    STOCK_METADATA,
    NVDA_4H_DATA, NVDA_DAILY_DATA,
    MSFT_4H_DATA, MSFT_DAILY_DATA,
    GOOGL_4H_DATA, GOOGL_DAILY_DATA,
    AAPL_4H_DATA, AAPL_DAILY_DATA,
    GLD_4H_DATA, GLD_DAILY_DATA,
    SLV_4H_DATA, SLV_DAILY_DATA,
    TSLA_4H_DATA, TSLA_DAILY_DATA,
    NFLX_4H_DATA, NFLX_DAILY_DATA,
    BRKB_4H_DATA, BRKB_DAILY_DATA,
    WMT_4H_DATA, WMT_DAILY_DATA,
    UNH_4H_DATA, UNH_DAILY_DATA,
    AVGO_4H_DATA, AVGO_DAILY_DATA,
    LLY_4H_DATA, LLY_DAILY_DATA,
    TSM_4H_DATA, TSM_DAILY_DATA,
    ORCL_4H_DATA, ORCL_DAILY_DATA,
    OXY_4H_DATA, OXY_DAILY_DATA
)

# Initialize FastAPI app
app = FastAPI(
    title="RSI-MA Performance Analytics API",
    description="Backend API for RSI-MA trading strategy analysis",
    version="1.0.0"
)

# CORS middleware for React frontend
# Allow both frontend domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://rsi-ma-frontend.onrender.com",
        "https://new-test-strategy.vercel.app",
        "https://new-test-strategy.onrender.com",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Compress large JSON responses (matrices/series) to reduce transfer + parse time.
app.add_middleware(GZipMiddleware, minimum_size=1024)

# Import and add Swing Framework router (REAL historical trade data)
try:
    from swing_framework_api import router as swing_framework_router
    app.include_router(swing_framework_router)
    print("[OK] Swing Framework API registered (REAL trade data)")
except Exception as e:
    print(f"[WARN] Could not load Swing Framework API: {e}")

# Import and add Macro Risk Metrics router
try:
    from macro_risk_metrics import router as macro_risk_router
    app.include_router(macro_risk_router)
    print("[OK] Macro Risk Metrics API registered (Yield Curve, Breadth, MMFI)")
except Exception as e:
    print(f"[WARN] Could not load Macro Risk Metrics API: {e}")

# Import and add Gamma Scanner router
try:
    import sys
    from pathlib import Path
    # Add gamma directory to path directly
    gamma_dir = Path(__file__).parent / "api" / "gamma"
    if str(gamma_dir) not in sys.path:
        sys.path.insert(0, str(gamma_dir))

    # Import directly from gamma_endpoint module
    from gamma_endpoint import router as gamma_router
    app.include_router(gamma_router, prefix="/api")  # Add /api prefix here
    print("[OK] Gamma Wall Scanner API registered")
except Exception as e:
    print(f"[WARN] Could not load Gamma Scanner API: {e}")

# Import and add Price Fetcher router
try:
    import sys
    from pathlib import Path
    api_dir = Path(__file__).parent / "api"
    if str(api_dir) not in sys.path:
        sys.path.insert(0, str(api_dir))

    from price_fetcher import router as price_router
    app.include_router(price_router)
    print("[OK] Price Fetcher API registered")
except Exception as e:
    print(f"[WARN] Could not load Price Fetcher API: {e}")

# Import and add Daily Trend Scanner router
try:
    import sys
    from pathlib import Path
    api_dir = Path(__file__).parent / "api"
    if str(api_dir) not in sys.path:
        sys.path.insert(0, str(api_dir))

    from daily_trend_scanner import router as daily_trend_router
    app.include_router(daily_trend_router)
    print("[OK] Daily Trend Scanner API registered (/api/daily-trend/*)")
except Exception as e:
    print(f"[WARN] Could not load Daily Trend Scanner API: {e}")

# Import and add Lower Extension API
try:
    import sys
    from pathlib import Path
    api_dir = Path(__file__).parent / "api"
    if str(api_dir) not in sys.path:
        sys.path.insert(0, str(api_dir))

    from lower_extension import router as lower_extension_router
    app.include_router(lower_extension_router)
    print("[OK] Lower Extension API registered (/api/lower-extension/*)")
except Exception as e:
    print(f"[WARN] Could not load Lower Extension API: {e}")

# Import and add Nadaraya-Watson API
try:
    from nadaraya_watson import router as nw_router
    app.include_router(nw_router)
    print("[OK] Nadaraya-Watson API registered (/api/nadaraya-watson/*)")
except Exception as e:
    print(f"[WARN] Could not load Nadaraya-Watson API: {e}")

# Import and add Multi-Timeframe router
try:
    from multi_timeframe_api import router as mtf_router
    app.include_router(mtf_router)
    print("[OK] Multi-Timeframe API registered (/stock, /bins, /trade-management)")
except Exception as e:
    print(f"[WARN] Could not load Multi-Timeframe API: {e}")

# Import and add Snapshot API router
try:
    from snapshot_api_endpoints import router as snapshot_router
    app.include_router(snapshot_router)
    print("[OK] Snapshot API registered (/api/snapshot/*)")
except Exception as e:
    print(f"[WARN] Could not load Snapshot API: {e}")

# Cache directory for results
# - Local dev: keep using `./cache`
# - Serverless (e.g. Vercel): use a writable temp directory
default_cache_dir = Path("cache")
if os.getenv("VERCEL"):
    default_cache_dir = Path(os.getenv("TMPDIR", "/tmp")) / "rsi_ma_cache"

CACHE_DIR = os.getenv("CACHE_DIR", str(default_cache_dir))
os.makedirs(CACHE_DIR, exist_ok=True)

# Default tickers
DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "QQQ", "SPY", "GLD", "SLV", "BRK-B", "AVGO", "XOM", "CVX", "JPM", "BAC", "LLY", "UNH", "OXY", "TSM", "WMT", "COST", "USDGBP", "US10"]

# ============================================================================
# Multi-timeframe response caching (performance)
# ============================================================================

_MTF_STATIC_SNAPSHOT_DIR = Path(__file__).resolve().parent / "static_snapshots" / "multi_timeframe"

_MTF_CACHE_TTL_SECONDS = int(os.getenv("MTF_CACHE_TTL_SECONDS", "900"))  # 15 minutes
_ENHANCED_MTF_CACHE_TTL_SECONDS = int(os.getenv("ENHANCED_MTF_CACHE_TTL_SECONDS", "1800"))  # 30 minutes

_mtf_cache: Dict[str, Dict] = {}
_mtf_cache_timestamp: Dict[str, float] = {}
_mtf_cache_locks: Dict[str, asyncio.Lock] = {}
_mtf_cache_locks_guard = asyncio.Lock()


def _cache_key(*parts: str) -> str:
    return ":".join(part.strip().lower() for part in parts if part is not None)


def _file_safe_slug(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in value.upper())


def _is_time_fresh(timestamp: float | None, ttl_seconds: int) -> bool:
    if timestamp is None:
        return False
    return (time.time() - timestamp) < ttl_seconds


def _load_static_snapshot(filename: str, env_var: str) -> Dict | None:
    if os.getenv(env_var, "1").lower() in {"0", "false", "no"}:
        return None

    path = _MTF_STATIC_SNAPSHOT_DIR / filename
    if not path.exists():
        return None

    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        if isinstance(payload, dict):
            return payload
    except Exception as e:
        print(f"[WARN] Failed to load static snapshot {path}: {e}")
    return None


def _read_disk_cache(path: str, ttl_seconds: int) -> Dict | None:
    try:
        stat = os.stat(path)
    except FileNotFoundError:
        return None
    except Exception:
        return None

    if (time.time() - stat.st_mtime) > ttl_seconds:
        return None

    try:
        with open(path, "r", encoding="utf-8") as file:
            payload = json.load(file)
        if isinstance(payload, dict):
            return payload
    except Exception:
        return None
    return None


def _write_disk_cache(path: str, payload: Dict) -> None:
    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(payload, file)
            file.write("\n")
    except Exception:
        return


async def _get_cache_lock(key: str) -> asyncio.Lock:
    async with _mtf_cache_locks_guard:
        lock = _mtf_cache_locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            _mtf_cache_locks[key] = lock
        return lock

# ============================================================================
# Request/Response Models
# ============================================================================

class BacktestRequest(BaseModel):
    tickers: List[str] = Field(default=DEFAULT_TICKERS, description="List of ticker symbols")
    lookback_period: int = Field(default=252, ge=100, le=1000)
    rsi_length: int = Field(default=14, ge=5, le=50)
    ma_length: int = Field(default=14, ge=5, le=50)  # TradingView setting
    max_horizon: int = Field(default=21, ge=7, le=30)

class MonteCarloRequest(BaseModel):
    ticker: str
    num_simulations: int = Field(default=1000, ge=100, le=5000)
    max_periods: int = Field(default=21, ge=10, le=50)
    target_percentiles: List[float] = Field(default=[25, 50, 75, 90])

class PerformanceMatrixRequest(BaseModel):
    ticker: str
    threshold: float = Field(default=5.0, ge=1.0, le=20.0)

class TickerComparisonRequest(BaseModel):
    tickers: List[str] = Field(min_items=1, max_items=5)
    threshold: float = Field(default=5.0)

class AdvancedBacktestRequest(BaseModel):
    ticker: str
    threshold: float = Field(default=5.0)
    max_hold_days: int = Field(default=21, ge=7, le=30)

class ExitSignalRequest(BaseModel):
    ticker: str
    entry_price: float
    entry_date: str  # ISO format

# ============================================================================
# Helper Functions
# ============================================================================

def get_cache_filename(ticker: str, threshold: Optional[float] = None) -> str:
    """Generate cache filename for results."""
    if threshold:
        return os.path.join(CACHE_DIR, f"{ticker}_{threshold}_results.json")
    return os.path.join(CACHE_DIR, f"{ticker}_backtest.json")

def load_cached_results(ticker: str, threshold: Optional[float] = None, max_age_hours: int = 24) -> Optional[Dict]:
    """Load cached results if they exist and are recent."""
    cache_file = get_cache_filename(ticker, threshold)
    
    if not os.path.exists(cache_file):
        return None
    
    # Check file age
    file_age = datetime.now().timestamp() - os.path.getmtime(cache_file)
    if file_age > max_age_hours * 3600:
        return None
    
    try:
        with open(cache_file, 'r') as f:
            return json.load(f)
    except:
        return None

def save_cached_results(ticker: str, results: Dict, threshold: Optional[float] = None):
    """Save results to cache."""
    cache_file = get_cache_filename(ticker, threshold)
    with open(cache_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "RSI-MA Performance Analytics API",
        "version": "1.0.0",
        "endpoints": {
            "backtest": "/api/backtest/{ticker}",
            "batch_backtest": "/api/backtest/batch",
            "monte_carlo": "/api/monte-carlo/{ticker}",
            "performance_matrix": "/api/performance-matrix/{ticker}/{threshold}",
            "optimal_exit": "/api/optimal-exit/{ticker}/{threshold}",
            "ticker_comparison": "/api/compare",
            "advanced_backtest": "/api/advanced-backtest",
            "trade_simulation": "/api/trade-simulation/{ticker}",
            "leaps_vix_strategy": "/api/leaps/vix-strategy"
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/api/mapi-chart/{ticker}")
async def get_mapi_chart(ticker: str, days: int = 252):
    """
    Get MAPI (Momentum-Adapted Percentile Indicator) chart data

    MAPI is designed for momentum stocks and uses:
    - EDR (EMA Distance Ratio) - Price distance from EMA normalized by ATR
    - ESV (EMA Slope Velocity) - Rate of change of EMA
    - Composite Momentum Score - Weighted combination with percentiles

    Args:
        ticker: Stock symbol (e.g., 'AAPL', 'TSLA')
        days: Number of days to return (default: 252)

    Returns:
        Chart data with MAPI components, signals, and current values
    """
    try:
        ticker_upper = ticker.upper()

        # Get daily data for the ticker
        data_map = {
            'NVDA': NVDA_DAILY_DATA,
            'MSFT': MSFT_DAILY_DATA,
            'GOOGL': GOOGL_DAILY_DATA,
            'AAPL': AAPL_DAILY_DATA,
            'GLD': GLD_DAILY_DATA,
            'SLV': SLV_DAILY_DATA,
            'TSLA': TSLA_DAILY_DATA,
            'NFLX': NFLX_DAILY_DATA,
            'BRK-B': BRKB_DAILY_DATA,
            'WMT': WMT_DAILY_DATA,
            'UNH': UNH_DAILY_DATA,
            'AVGO': AVGO_DAILY_DATA,
            'LLY': LLY_DAILY_DATA,
            'TSM': TSM_DAILY_DATA,
            'ORCL': ORCL_DAILY_DATA,
            'OXY': OXY_DAILY_DATA
        }

        if ticker_upper not in data_map:
            raise HTTPException(
                status_code=404,
                detail=f"Ticker {ticker_upper} not found. Available: {list(data_map.keys())}"
            )

        df = data_map[ticker_upper].copy()

        # Rename columns to lowercase for consistency
        df.columns = [col.lower() for col in df.columns]

        # Initialize MAPI calculator
        calculator = MAPICalculator(
            ema_period=20,
            ema_slope_period=5,
            atr_period=14,
            edr_lookback=60,
            esv_lookback=90
        )

        # Prepare chart data
        chart_data = prepare_mapi_chart_data(df, calculator, days)

        return {
            "success": True,
            "ticker": ticker_upper,
            "chart_data": chart_data,
            "metadata": {
                "ema_period": 20,
                "ema_slope_period": 5,
                "atr_period": 14,
                "edr_lookback": 60,
                "esv_lookback": 90
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error calculating MAPI for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/leaps/vix-strategy")
async def get_leaps_vix_strategy():
    """
    Get current VIX level and recommended LEAPS strategy.

    Returns VIX data and strategy recommendations based on current volatility environment:
    - VIX < 15: ATM LEAPS strategy (cheap vega, maximum leverage)
    - VIX 15-20: Moderate ITM strategy (balanced approach)
    - VIX > 20: Deep ITM strategy (vega protection essential)

    Returns:
        dict: {
            "vix_current": Current VIX level
            "vix_percentile": VIX percentile rank (0-100)
            "strategy": Strategy name (ATM, MODERATE_ITM, DEEP_ITM)
            "strategy_full": Full strategy description
            "recommendations": {
                "delta_range": Recommended delta range
                "extrinsic_pct_max": Maximum extrinsic value %
                "strike_depth_pct": Strike depth % ITM range
                "vega_range": Recommended vega range
            }
            "rationale": Strategy explanation
            "vega_exposure": Vega risk assessment
            "key_filters": List of key filtering criteria
            "vix_context": VIX environment context
            "timestamp": ISO format timestamp
        }
    """
    try:
        from vix_analyzer import fetch_vix_data, determine_leaps_strategy

        # Fetch current VIX data
        vix_data = fetch_vix_data()

        # Determine optimal LEAPS strategy
        strategy = determine_leaps_strategy(
            vix_data["current"],
            vix_data["percentile"]
        )

        return {
            "vix_current": vix_data["current"],
            "vix_percentile": vix_data["percentile"],
            "strategy": strategy["strategy"],
            "strategy_full": strategy["strategy_full"],
            "recommendations": {
                "delta_range": strategy["delta_range"],
                "extrinsic_pct_max": strategy["extrinsic_pct_max"],
                "strike_depth_pct": strategy["strike_depth_pct"],
                "vega_range": strategy["vega_range"]
            },
            "rationale": strategy["rationale"],
            "vega_exposure": strategy["vega_exposure"],
            "key_filters": strategy["key_filters"],
            "vix_context": strategy["vix_context"],
            "timestamp": vix_data["timestamp"],
            "error": vix_data.get("error")  # Include error if VIX fetch failed
        }

    except Exception as e:
        logger.error(f"Error in LEAPS VIX strategy endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch LEAPS strategy: {str(e)}")

@app.get("/api/leaps/opportunities")
async def get_leaps_opportunities(
    strategy: Optional[str] = None,
    min_delta: Optional[float] = None,
    max_delta: Optional[float] = None,
    max_extrinsic: Optional[float] = None,
    min_strike: Optional[float] = None,
    max_strike: Optional[float] = None,
    min_vega: Optional[float] = None,
    max_vega: Optional[float] = None,
    max_iv_rank: Optional[float] = None,
    min_iv_percentile: Optional[float] = None,
    max_iv_percentile: Optional[float] = None,
    rank_by: Optional[str] = 'quality_score',
    top_n: int = 10,
    use_sample: bool = False
):
    """
    Get top LEAPS opportunities based on current VIX strategy or custom filters.

    Query Parameters:
        strategy: Strategy name (ATM, MODERATE_ITM, DEEP_ITM) - uses preset filters
        min_delta: Minimum delta (overrides strategy default)
        max_delta: Maximum delta (overrides strategy default)
        max_extrinsic: Maximum extrinsic % (overrides strategy default)
        min_strike: Minimum strike price
        max_strike: Maximum strike price
        min_vega: Minimum vega
        max_vega: Maximum vega
        max_iv_rank: Maximum IV rank (0-1)
        min_iv_percentile: Minimum IV percentile (0-100)
        max_iv_percentile: Maximum IV percentile (0-100)
        rank_by: Ranking method (quality_score, delta, vega, iv_rank, premium)
        top_n: Number of top opportunities to return (default 10)
        use_sample: Force use of sample data (for testing)

    Returns:
        dict: {
            'current_price': Current SPY price
            'strategy_used': Strategy name or 'custom'
            'filter_criteria': Applied filters
            'total_options': Total LEAPS options found
            'filtered_options': Options matching criteria
            'top_opportunities': List of top N options ranked by specified method
            'timestamp': Analysis timestamp
            'data_source': 'live' or 'sample'
        }
    """
    try:
        from vix_analyzer import fetch_vix_data, determine_leaps_strategy
        from leaps_analyzer import fetch_spx_options, filter_leaps_by_strategy, _calculate_quality_score, _calculate_opportunity_score

        # Fetch all LEAPS options (only real data unless use_sample=true)
        all_options = fetch_spx_options(use_sample=use_sample)

        # Determine data source
        if use_sample:
            data_source = 'sample'
        elif len(all_options) == 0:
            # No data available - return error response
            raise HTTPException(
                status_code=503,
                detail="Unable to fetch live options data. Please try again later."
            )
        else:
            data_source = 'live'

        current_price = all_options[0]['current_price'] if all_options else 0

        # Determine strategy if not provided
        if not strategy:
            vix_data = fetch_vix_data()
            strategy_info = determine_leaps_strategy(vix_data["current"], vix_data["percentile"])
            strategy = strategy_info["strategy"]
            if not min_delta:
                min_delta, max_delta = strategy_info["delta_range"]
            if not max_extrinsic:
                max_extrinsic = strategy_info["extrinsic_pct_max"]
        else:
            # Use strategy defaults if not overridden
            if strategy == "ATM":
                if not min_delta: min_delta, max_delta = 0.45, 0.60
                if not max_extrinsic: max_extrinsic = 35
            elif strategy == "MODERATE_ITM":
                if not min_delta: min_delta, max_delta = 0.75, 0.85
                if not max_extrinsic: max_extrinsic = 20
            else:  # DEEP_ITM
                if not min_delta: min_delta, max_delta = 0.85, 0.98
                if not max_extrinsic: max_extrinsic = 10

        # Set defaults for optional filters
        if min_delta is None: min_delta = 0.3
        if max_delta is None: max_delta = 0.99
        if max_extrinsic is None: max_extrinsic = 50

        # Apply all filters
        filtered = []
        for opt in all_options:
            # Delta filter
            if not (min_delta <= opt['delta'] <= max_delta):
                continue

            # Extrinsic filter
            if opt['extrinsic_pct'] > max_extrinsic:
                continue

            # Strike filter
            if min_strike and opt['strike'] < min_strike:
                continue
            if max_strike and opt['strike'] > max_strike:
                continue

            # Vega filter
            if min_vega and opt['vega'] < min_vega:
                continue
            if max_vega and opt['vega'] > max_vega:
                continue

            # IV Rank filter
            if max_iv_rank and opt['iv_rank'] > max_iv_rank:
                continue

            # IV Percentile filter
            if min_iv_percentile and opt['iv_percentile'] < min_iv_percentile:
                continue
            if max_iv_percentile and opt['iv_percentile'] > max_iv_percentile:
                continue

            # Relaxed liquidity filters for LEAPS (they naturally have lower volume/OI)
            # LEAPS are long-dated options with inherently lower liquidity than short-term options
            is_deep_itm = opt.get('delta', 0) >= 0.80

            if is_deep_itm:
                # Very relaxed filters for deep ITM (trade like stock)
                # Require minimal volume OR open interest (not both)
                if opt['volume'] < 1:
                    continue
            else:
                # Relaxed filters for ATM/moderate ITM LEAPS
                # Require decent volume (OI can be 0 for newly listed strikes)
                if opt['volume'] < 5:
                    continue

            # Bid-ask spread filter (same for all)
            if opt['bid_ask_spread_pct'] > 10:  # Relaxed from 5% to 10%
                continue

            # Calculate quality score and opportunity score for this option
            opt['quality_score'] = _calculate_quality_score(opt, strategy or 'custom')
            opt['opportunity_score'] = _calculate_opportunity_score(opt)

            # Calculate additional useful metrics
            premium = opt['premium']
            delta = opt['delta']
            vega = opt['vega']

            # Leverage Factor: (Delta × Spot Price) / Premium
            # Higher = more stock exposure per dollar invested
            opt['leverage_factor'] = round((delta * current_price) / premium if premium > 0 else 0, 2)

            # Vega Efficiency: Vega / Premium × 100
            # Lower = less volatility exposure per dollar invested (better for deep ITM)
            opt['vega_efficiency'] = round((vega / premium * 100) if premium > 0 else 0, 3)

            # Cost Basis: Premium / Delta
            # Effective cost per share of exposure (lower is better)
            opt['cost_basis'] = round(premium / delta if delta > 0 else 0, 2)

            # ROI if Stock Moves 10%
            # Estimated return if underlying moves 10% up
            opt['roi_10pct_move'] = round((delta * current_price * 0.10) / premium * 100 if premium > 0 else 0, 1)

            # Entry Quality Assessment - tells you WHEN to buy
            iv_percentile = opt.get('iv_percentile', 50)

            if iv_percentile < 30 and vega < 0.15:
                opt['entry_quality'] = 'excellent'
                opt['entry_quality_label'] = 'Excellent Entry'
                opt['entry_quality_description'] = 'Low IV + Low vega - Ideal buying opportunity!'
            elif iv_percentile < 30 and vega < 0.30:
                opt['entry_quality'] = 'good'
                opt['entry_quality_label'] = 'Good Entry'
                opt['entry_quality_description'] = 'Low IV but moderate vega - Good buying opportunity'
            elif iv_percentile < 60 and vega < 0.30:
                opt['entry_quality'] = 'fair'
                opt['entry_quality_label'] = 'Fair Entry'
                opt['entry_quality_description'] = 'Moderate IV and vega - Acceptable entry point'
            elif iv_percentile < 60 and vega < 0.50:
                opt['entry_quality'] = 'caution'
                opt['entry_quality_label'] = 'Caution'
                opt['entry_quality_description'] = 'Moderate IV but higher vega - Consider waiting'
            else:
                opt['entry_quality'] = 'wait'
                opt['entry_quality_label'] = 'Wait for Better'
                opt['entry_quality_description'] = 'High IV percentile or high vega - Wait for better conditions'

            filtered.append(opt)

        # Rank/sort by specified method
        reverse = True  # Most metrics are "higher is better"
        if rank_by == 'iv_rank':
            reverse = False  # Lower IV rank is better (cheaper vega)
        elif rank_by == 'premium':
            reverse = False  # Lower premium for same characteristics

        if rank_by in ['quality_score', 'opportunity_score', 'delta', 'vega', 'iv_rank', 'premium']:
            filtered.sort(key=lambda x: x.get(rank_by, 0), reverse=reverse)
        else:
            # Default to opportunity score (best volatility value)
            filtered.sort(key=lambda x: x.get('opportunity_score', 0), reverse=True)

        result = {
            'current_price': current_price,
            'strategy_used': strategy or 'custom',
            'filter_criteria': {
                'delta_range': [min_delta, max_delta],
                'extrinsic_max': max_extrinsic,
                'strike_range': [min_strike, max_strike] if min_strike or max_strike else None,
                'vega_range': [min_vega, max_vega] if min_vega or max_vega else None,
                'iv_rank_max': max_iv_rank,
                'iv_percentile_range': [min_iv_percentile, max_iv_percentile] if min_iv_percentile or max_iv_percentile else None,
                'rank_by': rank_by
            },
            'total_options': len(all_options),
            'filtered_options': len(filtered),
            'top_opportunities': filtered[:top_n],
            'timestamp': datetime.now().isoformat(),
            'data_source': data_source
        }

        return result

    except Exception as e:
        logger.error(f"Error in LEAPS opportunities endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch LEAPS opportunities: {str(e)}")

@app.get("/api/leaps/backtest")
async def get_leaps_backtest(years: int = 5):
    """
    Get LEAPS performance backtest across VIX regimes.

    Query Parameters:
        years: Number of years to backtest (default 5, max 10)

    Returns:
        dict: {
            'regimes': Performance by VIX regime (LOW, MODERATE, HIGH)
            'overall': Overall performance metrics
            'current_vix': Current VIX level
            'timestamp': Analysis timestamp
        }
    """
    try:
        from leaps_backtester import backtest_vix_regimes, get_regime_recommendations

        # Limit years to reasonable range
        years = min(max(years, 1), 10)

        # Run backtest
        results = backtest_vix_regimes(years=years)

        # Get recommendations
        recommendations = get_regime_recommendations(results)
        results['recommendations'] = recommendations

        return results

    except Exception as e:
        logger.error(f"Error in LEAPS backtest endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run backtest: {str(e)}")

@app.get("/api/leaps/alerts")
async def get_leaps_alerts():
    """
    Get current LEAPS trading alerts and notifications.

    Returns:
        dict: {
            'alerts': List of active alerts
            'vix_alerts': VIX-specific alerts
            'opportunity_alerts': High-quality opportunity alerts
            'regime_change_alert': Alert if VIX regime recently changed
            'timestamp': Alert generation time
        }
    """
    try:
        from vix_analyzer import fetch_vix_data, determine_leaps_strategy
        from leaps_analyzer import fetch_spx_options, filter_leaps_by_strategy
        from leaps_backtester import backtest_vix_regimes

        # Fetch current data
        vix_data = fetch_vix_data()
        strategy = determine_leaps_strategy(vix_data["current"], vix_data["percentile"])

        alerts = []
        vix_alerts = []
        opportunity_alerts = []
        regime_change_alert = None

        # VIX percentile alerts
        percentile = vix_data["percentile"]
        vix_level = vix_data["current"]

        if percentile < 10:
            vix_alerts.append({
                'severity': 'HIGH',
                'type': 'VIX_EXTREME_LOW',
                'title': 'VIX at Extreme Lows',
                'message': f'VIX at {vix_level:.2f} (P{percentile}) - Historically cheap vega. '
                          f'Strong buying opportunity for ATM LEAPS.',
                'action': 'Consider aggressive ATM LEAPS positions'
            })
        elif percentile > 90:
            vix_alerts.append({
                'severity': 'HIGH',
                'type': 'VIX_EXTREME_HIGH',
                'title': 'VIX at Extreme Highs',
                'message': f'VIX at {vix_level:.2f} (P{percentile}) - Expensive vega environment. '
                          f'Use Deep ITM protection.',
                'action': 'Only Deep ITM (delta >0.90) positions recommended'
            })

        # VIX level thresholds
        if vix_level < 12:
            vix_alerts.append({
                'severity': 'MEDIUM',
                'type': 'VIX_COMPLACENCY',
                'title': 'Complacency Alert',
                'message': f'VIX below 12 signals extreme complacency. Rare buying opportunity.',
                'action': 'Maximum vega exposure via ATM LEAPS'
            })
        elif vix_level > 30:
            vix_alerts.append({
                'severity': 'MEDIUM',
                'type': 'VIX_PANIC',
                'title': 'Panic Levels',
                'message': f'VIX above 30 indicates market stress. Extreme caution required.',
                'action': 'Wait for VIX normalization or use Deep ITM only'
            })

        # Opportunity alerts (simplified - would check actual options)
        if strategy["strategy"] == "ATM" and percentile < 30:
            opportunity_alerts.append({
                'severity': 'HIGH',
                'type': 'OPTIMAL_ENTRY',
                'title': 'Optimal ATM Entry Conditions',
                'message': 'Low VIX + Low percentile = Ideal conditions for ATM LEAPS',
                'action': 'Search for ATM LEAPS with delta 0.50-0.55'
            })

        # Regime change detection (simplified)
        if 14 < vix_level < 16:
            regime_change_alert = {
                'severity': 'MEDIUM',
                'type': 'REGIME_TRANSITION',
                'title': 'Potential Regime Transition',
                'message': 'VIX near 15 threshold - monitor for regime change',
                'action': 'Be prepared to adjust strategy if VIX crosses 15'
            }
        elif 19 < vix_level < 21:
            regime_change_alert = {
                'severity': 'MEDIUM',
                'type': 'REGIME_TRANSITION',
                'title': 'Potential Regime Transition',
                'message': 'VIX near 20 threshold - monitor for regime change',
                'action': 'Be prepared to adjust from Moderate ITM to Deep ITM if VIX rises'
            }

        # Combine all alerts
        all_alerts = vix_alerts + opportunity_alerts
        if regime_change_alert:
            all_alerts.append(regime_change_alert)

        return {
            'alerts': all_alerts,
            'alert_count': len(all_alerts),
            'vix_alerts': vix_alerts,
            'opportunity_alerts': opportunity_alerts,
            'regime_change_alert': regime_change_alert,
            'current_vix': vix_level,
            'current_percentile': percentile,
            'current_strategy': strategy["strategy"],
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in LEAPS alerts endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate alerts: {str(e)}")

@app.post("/api/backtest/batch")
async def run_batch_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """
    Run backtest for multiple tickers.
    Returns job ID for tracking progress.
    """
    try:
        # Create backtester
        backtester = EnhancedPerformanceMatrixBacktester(
            tickers=request.tickers,
            lookback_period=request.lookback_period,
            rsi_length=request.rsi_length,
            ma_length=request.ma_length,
            max_horizon=request.max_horizon
        )
        
        # Run analysis
        results = backtester.run_analysis()
        
        # Cache results for each ticker
        for ticker in request.tickers:
            if ticker in results:
                save_cached_results(ticker, results[ticker])
        
        return {
            "status": "completed",
            "tickers": list(results.keys()),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/backtest/{ticker}")
async def get_backtest_results(ticker: str, force_refresh: bool = False):
    """
    Get backtest results for a single ticker.
    Uses cache if available and recent.
    """
    ticker = ticker.upper()
    
    # Check cache first
    if not force_refresh:
        cached = load_cached_results(ticker)
        if cached:
            return {
                "ticker": ticker,
                "source": "cache",
                "data": cached,
                "timestamp": datetime.now().isoformat()
            }
    
    # Run fresh backtest
    try:
        backtester = EnhancedPerformanceMatrixBacktester(
            tickers=[ticker],
            lookback_period=252,
            rsi_length=14,
            ma_length=14,
            max_horizon=21
        )

        results = backtester.run_analysis()
        
        if ticker not in results:
            raise HTTPException(status_code=404, detail=f"No results for {ticker}")
        
        # Cache results
        save_cached_results(ticker, results[ticker])
        
        return {
            "ticker": ticker,
            "source": "fresh",
            "data": results[ticker],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/performance-matrix/{ticker}/{threshold}")
async def get_performance_matrix(ticker: str, threshold: float):
    """
    Get performance matrix for a specific ticker and threshold.
    Returns the D1-D21 matrix with all percentile ranges.
    """
    ticker = ticker.upper()
    
    # Try to get from backtest results
    backtest_data = load_cached_results(ticker)
    
    if not backtest_data:
        # Run fresh backtest
        backtest_response = await get_backtest_results(ticker)
        backtest_data = backtest_response["data"]
    
    # Extract matrix for the threshold
    if "thresholds" not in backtest_data:
        raise HTTPException(status_code=404, detail=f"No threshold data for {ticker}")
    
    threshold_data = backtest_data["thresholds"].get(str(threshold))
    if not threshold_data:
        raise HTTPException(status_code=404, detail=f"No data for threshold {threshold}%")
    
    return {
        "ticker": ticker,
        "threshold": threshold,
        "matrix": threshold_data["performance_matrix"],
        "events": threshold_data["events"],
        "win_rates": threshold_data["win_rates"],
        "return_distributions": threshold_data["return_distributions"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/optimal-exit/{ticker}/{threshold}")
async def get_optimal_exit_strategy(ticker: str, threshold: float):
    """
    Get optimal exit strategy for a ticker at a given threshold.
    Includes return efficiency analysis and recommended exit day.
    """
    ticker = ticker.upper()
    
    backtest_data = load_cached_results(ticker)
    
    if not backtest_data:
        backtest_response = await get_backtest_results(ticker)
        backtest_data = backtest_response["data"]
    
    threshold_data = backtest_data["thresholds"].get(str(threshold))
    if not threshold_data:
        raise HTTPException(status_code=404, detail=f"No data for threshold {threshold}%")
    
    return {
        "ticker": ticker,
        "threshold": threshold,
        "optimal_exit_strategy": threshold_data.get("optimal_exit_strategy", {}),
        "risk_metrics": threshold_data.get("risk_metrics", {}),
        "trend_analysis": threshold_data.get("trend_analysis", {}),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/monte-carlo/{ticker}")
async def run_monte_carlo_simulation(ticker: str, request: MonteCarloRequest):
    """
    Run Monte Carlo simulation for a ticker.
    Provides forward-looking probability distributions.
    """
    ticker = ticker.upper()
    
    try:
        # Get historical data for the ticker
        backtester = EnhancedPerformanceMatrixBacktester(
            tickers=[ticker],
            lookback_period=252,
            rsi_length=14,
            ma_length=14,
            max_horizon=21
        )

        # Fetch data
        data = backtester.fetch_data(ticker)
        if data.empty:
            raise HTTPException(status_code=404, detail=f"Could not fetch data for {ticker}")
        
        # Calculate RSI-MA and percentiles
        indicator = backtester.calculate_rsi_ma_indicator(data['Close'])
        percentile_ranks = backtester.calculate_percentile_ranks(indicator)
        
        # Get current values
        current_percentile = percentile_ranks.iloc[-1]
        current_price = data['Close'].iloc[-1]
        
        # Prepare historical data
        historical_df = pd.DataFrame({
            'Close': data['Close'],
            'rsi_ma_percentile': percentile_ranks
        }).dropna()
        
        # Run Monte Carlo simulation
        mc_results = run_monte_carlo_for_ticker(
            ticker=ticker,
            current_percentile=current_percentile,
            current_price=current_price,
            historical_data=historical_df,
            num_simulations=request.num_simulations
        )
        
        return {
            "ticker": ticker,
            "current_percentile": float(current_percentile),
            "current_price": float(current_price),
            "simulation_results": mc_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rsi-chart/{ticker}")
async def get_rsi_percentile_chart(ticker: str, days: int = None):
    """
    Get RSI and RSI-MA time series data with percentile levels for chart visualization.
    Returns historical RSI, RSI-MA, percentile rank, and percentile thresholds.
    By default, returns ALL available data up to current day.
    """
    ticker = ticker.upper()

    try:
        # Get backtest results (this ensures we have the data analyzed)
        backtest_data = load_cached_results(ticker)

        if not backtest_data:
            backtest_response = await get_backtest_results(ticker)
            backtest_data = backtest_response["data"]

        # Create backtester instance to access the new method
        backtester = EnhancedPerformanceMatrixBacktester(
            tickers=[ticker],
            lookback_period=252,
            rsi_length=14,
            ma_length=14,
            max_horizon=21
        )

        # Fetch and analyze data (store in backtester.results)
        data = backtester.fetch_data(ticker)
        if data.empty:
            raise HTTPException(status_code=404, detail=f"Could not fetch data for {ticker}")

        # Store data in results (needed by get_rsi_percentile_timeseries)
        backtester.results[ticker] = {'data': data}

        # Get time series data - if days is None, use all available data
        if days is None:
            days = len(data)

        chart_data = backtester.get_rsi_percentile_timeseries(ticker, days)

        if not chart_data:
            raise HTTPException(status_code=404, detail=f"Could not generate chart data for {ticker}")

        return {
            "ticker": ticker,
            "chart_data": chart_data,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/compare")
async def compare_tickers(request: TickerComparisonRequest):
    """
    Compare multiple tickers side-by-side.
    Returns key metrics for comparison.
    """
    comparison_data = {}
    
    for ticker in request.tickers:
        ticker = ticker.upper()
        
        try:
            backtest_data = load_cached_results(ticker)
            
            if not backtest_data:
                backtest_response = await get_backtest_results(ticker)
                backtest_data = backtest_response["data"]
            
            threshold_data = backtest_data["thresholds"].get(str(request.threshold))
            
            if threshold_data:
                # Extract key comparison metrics
                comparison_data[ticker] = {
                    "events": threshold_data["events"],
                    "risk_metrics": threshold_data["risk_metrics"],
                    "optimal_exit": threshold_data.get("optimal_exit_strategy", {}),
                    "win_rates": threshold_data["win_rates"],
                    "benchmark": backtest_data.get("benchmark", {})
                }
        except:
            comparison_data[ticker] = {"error": "Failed to fetch data"}
    
    return {
        "threshold": request.threshold,
        "tickers": request.tickers,
        "comparison": comparison_data,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/tickers")
async def get_available_tickers():
    """Get list of available tickers with cached results."""
    cached_tickers = []

    for filename in os.listdir(CACHE_DIR):
        if filename.endswith("_backtest.json"):
            ticker = filename.replace("_backtest.json", "")
            cached_tickers.append(ticker)

    return {
        "default_tickers": DEFAULT_TICKERS,
        "cached_tickers": sorted(cached_tickers),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/advanced-backtest")
async def run_advanced_backtest_endpoint(request: AdvancedBacktestRequest):
    """
    Run advanced backtest comparing multiple exit strategies.

    Returns comprehensive comparison of:
    - Buy and hold
    - Fixed day exits (D3, D5, D7, etc.)
    - ATR trailing stop
    - Exit pressure based
    - Conditional expectancy based
    """
    ticker = request.ticker.upper()

    try:
        # Get historical data and entry events
        backtester = EnhancedPerformanceMatrixBacktester(
            tickers=[ticker],
            lookback_period=252,
            rsi_length=14,
            ma_length=14,
            max_horizon=request.max_hold_days
        )

        data = backtester.fetch_data(ticker)
        if data.empty:
            raise HTTPException(status_code=404, detail=f"Could not fetch data for {ticker}")

        indicator = backtester.calculate_rsi_ma_indicator(data)
        percentile_ranks = backtester.calculate_percentile_ranks(indicator)

        # Find entry events for the threshold
        entry_events = backtester.find_entry_events_enhanced(
            percentile_ranks, data['Close'], request.threshold
        )

        if len(entry_events) < 10:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient entry events ({len(entry_events)}) for threshold {request.threshold}%"
            )

        # Run advanced backtest
        runner = AdvancedBacktestRunner(
            historical_data=data,
            rsi_ma_percentiles=percentile_ranks,
            entry_events=entry_events,
            max_hold_days=request.max_hold_days
        )

        comparison = runner.run_comprehensive_comparison()
        optimal_curve = runner.generate_optimal_exit_curve()

        return {
            "ticker": ticker,
            "threshold": request.threshold,
            "max_hold_days": request.max_hold_days,
            "entry_events_count": len(entry_events),
            "strategy_comparison": comparison.to_dict(),
            "optimal_exit_curve": optimal_curve,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trade-simulation/{ticker}")
async def simulate_trade_with_management(
    ticker: str,
    entry_percentile: float = 5.0,
    days_to_simulate: int = 21
):
    """
    Simulate a single trade with advanced trade management.

    Shows day-by-day:
    - Exit pressure
    - Trade state
    - Exposure recommendations
    - Trailing stop levels
    - Volatility metrics
    """
    ticker = ticker.upper()

    try:
        # Get historical data
        backtester = EnhancedPerformanceMatrixBacktester(
            tickers=[ticker],
            lookback_period=252,
            rsi_length=14,
            ma_length=14,
            max_horizon=days_to_simulate
        )

        data = backtester.fetch_data(ticker)
        if data.empty:
            raise HTTPException(status_code=404, detail=f"Could not fetch data for {ticker}")

        indicator = backtester.calculate_rsi_ma_indicator(data)
        percentile_ranks = backtester.calculate_percentile_ranks(indicator)

        # Find a recent entry event at the target percentile
        entry_events = backtester.find_entry_events_enhanced(
            percentile_ranks, data['Close'], entry_percentile
        )

        if not entry_events:
            raise HTTPException(
                status_code=404,
                detail=f"No entry events found at {entry_percentile}% threshold"
            )

        # Use the most recent entry event
        recent_event = entry_events[-1]
        entry_date = recent_event['entry_date']
        entry_idx = data.index.get_loc(entry_date)

        # Import simulation function
        from advanced_trade_manager import simulate_trade_with_advanced_management

        simulation = simulate_trade_with_advanced_management(
            historical_data=data,
            rsi_ma_percentiles=percentile_ranks,
            entry_idx=entry_idx,
            entry_percentile=recent_event['entry_percentile'],
            entry_price=recent_event['entry_price'],
            historical_events=entry_events,
            max_hold_days=days_to_simulate
        )

        return {
            "ticker": ticker,
            "simulation": simulation,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/available-dates/{ticker}")
async def get_available_dates(ticker: str):
    """
    Get the date range of available data for a ticker.

    Returns start and end dates in ISO format.
    """
    ticker = ticker.upper()

    try:
        backtester = EnhancedPerformanceMatrixBacktester(
            tickers=[ticker],
            lookback_period=252,
            rsi_length=14,
            ma_length=14,
            max_horizon=21
        )

        data = backtester.fetch_data(ticker)
        if data.empty:
            raise HTTPException(status_code=404, detail=f"No data available for {ticker}")

        return {
            "ticker": ticker,
            "start_date": data.index[0].strftime('%Y-%m-%d'),
            "end_date": data.index[-1].strftime('%Y-%m-%d'),
            "total_days": len(data)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/live-signal/{ticker}")
async def get_live_entry_signal(ticker: str):
    """
    Get real-time entry signal for a ticker based on current market conditions.

    Applies historical analysis to present moment:
    - Current percentile position
    - Signal strength (strong_buy, buy, neutral, avoid)
    - Expected returns (7d, 14d, 21d)
    - Recommended position size
    - Detailed reasoning and risk factors

    Returns actionable "what to do NOW" recommendation.
    """
    ticker = ticker.upper()

    try:
        signals = generate_live_signals(ticker)
        return signals

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/exit-signal")
async def get_live_exit_signal(request: ExitSignalRequest):
    """
    Get real-time exit signal for an existing position.

    Args:
        ticker: Stock ticker
        entry_price: Price at which position was entered
        entry_date: Entry date (ISO format)

    Returns:
        - Current exit pressure (0-100)
        - Recommended action (hold, reduce_25, reduce_50, reduce_75, exit_all)
        - Urgency level (low, medium, high, critical)
        - Expected returns if hold vs exit
        - Trailing stop level
        - Detailed reasoning
    """
    ticker = request.ticker.upper()

    try:
        signals = generate_exit_signal_for_position(
            ticker=ticker,
            entry_price=request.entry_price,
            entry_date=request.entry_date
        )
        return signals

    except Exception as e:
        import traceback
        print(f"Error in /api/exit-signal for {ticker}:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/multi-timeframe/{ticker}")
async def get_multi_timeframe_analysis(ticker: str, force_refresh: bool = False):
    """
    Get multi-timeframe divergence analysis between daily and 4-hourly RSI-MA.

    Analyzes:
    - Divergence/convergence patterns between daily and 4H timeframes
    - Mean reversion opportunities (bearish/bullish divergence)
    - Optimal divergence thresholds for reversals
    - Forward-tested returns for each divergence type
    - Current actionable signals (profit-taking, re-entry, hold)

    Returns:
        - Current divergence state and recommendation
        - Historical divergence events with forward returns
        - Statistics by divergence type and strength
        - Optimal thresholds for trading
        - Visual data for charting
    """
    ticker = ticker.upper()

    try:
        cache_key = _cache_key("mtf", ticker)
        cache_file = os.path.join(CACHE_DIR, f"mtf_{_file_safe_slug(ticker)}.json")

        if not force_refresh:
            static_payload = _load_static_snapshot(
                f"multi-timeframe-{_file_safe_slug(ticker)}.json",
                env_var="MTF_STATIC_SNAPSHOTS",
            )
            if static_payload is not None:
                return static_payload

            disk_payload = _read_disk_cache(cache_file, ttl_seconds=_MTF_CACHE_TTL_SECONDS)
            if disk_payload is not None:
                return disk_payload

            if _is_time_fresh(_mtf_cache_timestamp.get(cache_key), _MTF_CACHE_TTL_SECONDS):
                cached = _mtf_cache.get(cache_key)
                if cached is not None:
                    return cached

        lock = await _get_cache_lock(cache_key)
        async with lock:
            if not force_refresh and _is_time_fresh(_mtf_cache_timestamp.get(cache_key), _MTF_CACHE_TTL_SECONDS):
                cached = _mtf_cache.get(cache_key)
                if cached is not None:
                    return cached

            analysis = await asyncio.to_thread(run_multi_timeframe_analysis, ticker)
            payload = {
                "ticker": ticker,
                "analysis": analysis,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            _mtf_cache[cache_key] = payload
            _mtf_cache_timestamp[cache_key] = time.time()
            _write_disk_cache(cache_file, payload)
            return payload

    except Exception as e:
        import traceback
        print(f"Error in /api/multi-timeframe for {ticker}:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/swing-duration/{ticker}")
async def get_swing_duration_analysis(
    ticker: str,
    threshold: float = 5.0,
    use_sample_data: bool = False,
    timeframe: str = "daily"
):
    """
    Get duration-in-low-percentile analysis for SWING signals (V2 - Clean Implementation).

    Returns comprehensive duration metrics with actionable insights.
    Uses LIVE data by default for real-time trading decisions.
    """
    ticker = ticker.upper()
    try:
        mode = (timeframe or "daily").lower()

        if mode in {"intraday", "intraday_4h", "4h", "hourly", "hours"}:
            try:
                result = analyze_swing_duration_intraday(
                    ticker,
                    entry_threshold=threshold,
                    use_sample_data=use_sample_data,
                )
                result["duration_unit"] = result.get("duration_unit", "hours")
                result["duration_granularity"] = result.get("duration_granularity", "intraday")
                return result
            except ValueError as err:
                # Retry with synthetic intraday data before falling back to daily
                try:
                    result = analyze_swing_duration_intraday(
                        ticker,
                        entry_threshold=threshold,
                        use_sample_data=True,
                    )
                    result["duration_unit"] = result.get("duration_unit", "hours")
                    result["duration_granularity"] = "intraday_sample"
                    result["fallback_reason"] = str(err)
                    result["data_source"] = f"intraday_sample_{result.get('data_source', 'sample')}"
                    return result
                except ValueError as err2:
                    # Network/caching issues are common in Codespaces; fall back to daily so the UI stays usable
                    fallback = analyze_swing_duration_v2(
                        ticker,
                        entry_threshold=threshold,
                        use_sample_data=True,
                    )
                    fallback["duration_unit"] = fallback.get("duration_unit", "days")
                    fallback["duration_granularity"] = "daily_fallback"
                    fallback["fallback_reason"] = f"{err} / {err2}"
                    fallback["data_source"] = f"intraday_fallback_{fallback.get('data_source', 'sample')}"
                    return fallback
        else:
            result = analyze_swing_duration_v2(
                ticker,
                entry_threshold=threshold,
                use_sample_data=use_sample_data,
            )
            # Annotate unit so the UI can label correctly
            result["duration_unit"] = result.get("duration_unit", "days")
            result["duration_granularity"] = result.get("duration_granularity", "daily")
            return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        print(f"Error in /api/swing-duration for {ticker}:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Startup Event
# ============================================================================

@app.get("/api/percentile-thresholds/{ticker}")
async def get_percentile_threshold_analysis(ticker: str):
    """
    Get percentile threshold analysis for a ticker.

    Returns specific percentile thresholds for each of the 4 divergence categories:
    1. 4H Overextended (Daily low, 4H high) - Take profits
    2. Bullish Convergence (Both low) - Buy/add position
    3. Daily Overextended (Daily high, 4H low) - Reduce/exit
    4. Bearish Convergence (Both high) - Exit/short

    Includes:
    - Percentile distributions by category
    - Optimal thresholds for each category
    - Decision matrix: IF Daily=X% AND 4H=Y% THEN Action
    - Performance statistics for each percentile range combination
    - Grid analysis of all combinations
    """
    ticker = ticker.upper()

    try:
        analyzer = PercentileThresholdAnalyzer(ticker)

        # Get all analyses
        distributions = analyzer.analyze_percentile_distributions()
        optimal_thresholds = analyzer.find_optimal_thresholds_by_category()
        decision_matrix = analyzer.generate_decision_matrix()
        grid = analyzer.create_percentile_grid_analysis()

        return {
            "ticker": ticker,
            "distributions": distributions,
            "optimal_thresholds": optimal_thresholds,
            "decision_matrix": decision_matrix.to_dict(orient='records'),
            "grid_analysis": grid.to_dict(orient='records'),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        import traceback
        print(f"Error in /api/percentile-thresholds for {ticker}:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/convergence-analysis/{ticker}")
async def get_convergence_analysis(ticker: str):
    """
    Get divergence-convergence framework analysis for a ticker.

    Analyzes time-to-convergence following overextension events between
    daily and 4-hour RSI-MA percentiles.

    Returns:
        - Current divergence state and prediction
        - Historical overextension events
        - Convergence statistics (time, direction, magnitude)
        - Predictive model for convergence timing
        - Actionable insights
    """
    ticker = ticker.upper()

    try:
        analysis = analyze_convergence_for_ticker(ticker)

        return {
            "ticker": ticker,
            "convergence_analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        import traceback
        print(f"Error in /api/convergence-analysis for {ticker}:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/position-management/{ticker}")
async def get_position_management_recommendation(ticker: str):
    """
    Get concrete position management recommendations based on divergence analysis.

    This endpoint answers:
    1. Should I take partial profits? How much (25%, 50%, 75%, 100%)?
    2. What divergence gap triggers action?
    3. When should I re-enter after taking profits?
    4. What convergence threshold signals re-entry?

    Returns ticker-specific, data-driven action points with:
    - Current position recommendation (TAKE_PROFIT, ADD_POSITION, HOLD, EXIT_ALL)
    - Exact position change % based on divergence magnitude
    - Confidence level from historical sample size
    - Expected returns if action taken vs if held
    - Profit-taking rules by divergence gap range
    - Re-entry rules by convergence scenario
    """
    ticker = ticker.upper()

    try:
        recommendation = get_position_management(ticker)

        return {
            "ticker": ticker,
            "position_management": recommendation,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        import traceback
        print(f"Error in /api/position-management for {ticker}:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/enhanced-mtf/{ticker}")
async def get_enhanced_multi_timeframe_analysis(ticker: str, force_refresh: bool = False):
    """
    Get enhanced multi-timeframe divergence analysis with intraday tracking.

    **NEW FEATURES**:
    - Intraday checkpoint analysis (morning, midday, close)
    - Multi-horizon outcomes: 1×4H, 2×4H, 3×4H, 1D, 2D, 7D
    - Divergence lifecycle tracking (trigger → convergence)
    - Take vs Hold comparison across all horizons
    - Signal quality metrics (hit rate, Sharpe, consistency)
    - Volatility context (current ATR regime)
    - Divergence decay model (convergence probabilities)

    **KEY INSIGHT**: Exit divergence signals within 8-12 hours (3×4H) provides
    +0.46% to +0.56% edge over holding through 1D.

    Returns:
        - Full divergence lifecycle events (679 events for AAPL)
        - Multi-horizon outcomes matrix (Take vs Hold deltas)
        - Signal quality (hit rate, Sharpe ratio, consistency score)
        - Volatility context (ATR percentile, regime)
        - Decay model (convergence probability by time and gap size)
    """
    ticker = ticker.upper()

    try:
        cache_key = _cache_key("enhanced_mtf", ticker)
        cache_file = os.path.join(CACHE_DIR, f"enhanced_mtf_{_file_safe_slug(ticker)}.json")

        if not force_refresh:
            static_payload = _load_static_snapshot(
                f"enhanced-mtf-{_file_safe_slug(ticker)}.json",
                env_var="ENHANCED_MTF_STATIC_SNAPSHOTS",
            )
            if static_payload is not None:
                return static_payload

            disk_payload = _read_disk_cache(cache_file, ttl_seconds=_ENHANCED_MTF_CACHE_TTL_SECONDS)
            if disk_payload is not None:
                return disk_payload

            if _is_time_fresh(_mtf_cache_timestamp.get(cache_key), _ENHANCED_MTF_CACHE_TTL_SECONDS):
                cached = _mtf_cache.get(cache_key)
                if cached is not None:
                    return cached

        lock = await _get_cache_lock(cache_key)
        async with lock:
            if not force_refresh and _is_time_fresh(_mtf_cache_timestamp.get(cache_key), _ENHANCED_MTF_CACHE_TTL_SECONDS):
                cached = _mtf_cache.get(cache_key)
                if cached is not None:
                    return cached

            analysis = await asyncio.to_thread(run_enhanced_analysis, ticker)
            payload = {
                "ticker": ticker,
                "enhanced_analysis": analysis,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            _mtf_cache[cache_key] = payload
            _mtf_cache_timestamp[cache_key] = time.time()
            _write_disk_cache(cache_file, payload)
            return payload

    except Exception as e:
        import traceback
        print(f"Error in /api/enhanced-mtf for {ticker}:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/percentile-forward/{ticker}")
async def get_percentile_forward_mapping(ticker: str, force_refresh: bool = False):
    """
    Get percentile-to-forward-return mapping analysis for a ticker.

    **PROSPECTIVE EXTRAPOLATION FRAMEWORK**

    Turns RSI-MA percentile rankings into expected forward % change predictions using:

    **Methods Implemented:**
    1. **Empirical Conditional Expectation** - Bin-based lookup (E[Return | Percentile Bin])
    2. **Transition Matrix (Markov Chain)** - Percentile evolution probabilities
    3. **Regression Models** - Linear, Polynomial, Quantile regression
    4. **Kernel Smoothing** - Nonparametric Nadaraya-Watson estimator
    5. **Ensemble Average** - Combines all methods (recommended)

    **Backtesting:**
    - Rolling window out-of-sample testing (train 252 days, test 21 days)
    - Evaluation metrics: MAE, RMSE, Hit Rate, Sharpe, Information Ratio
    - Confidence assessment: Strong model = Hit Rate > 55%, Sharpe > 1.0

    **Returns:**
    - Current percentile and RSI-MA value
    - Forward return forecasts (1d, 5d, 10d) from all methods
    - Empirical bin statistics (mean, median, std, 5th/95th percentiles)
    - Transition matrices for percentile evolution
    - Backtest accuracy metrics (out-of-sample performance)
    - Trading recommendation based on model strength

    **Use Cases:**
    - "What return can I expect given current 34th percentile?"
    - "How reliable are these predictions? (Hit rate, Sharpe)"
    - "What's the downside risk? (5th percentile return)"
    - "Which forecasting method is most accurate for this ticker?"

    **Example Response:**
    ```json
    {
      "current_percentile": 34.1,
      "prediction": {
        "ensemble_forecast_1d": 0.07,
        "empirical_bin_stats": {
          "mean_return_1d": 0.00,
          "pct_5_return_1d": -2.15,
          "pct_95_return_1d": 2.18
        }
      },
      "accuracy_metrics": {
        "1d": {
          "hit_rate": 52.5,
          "sharpe": 0.07,
          "mae": 1.15
        }
      }
    }
    ```
    """
    ticker = ticker.upper()

    try:
        # Check cache first for performance (24-hour cache)
        cache_file = os.path.join(CACHE_DIR, f"{ticker}_percentile_forward.json")

        if not force_refresh and os.path.exists(cache_file):
            file_age = datetime.now().timestamp() - os.path.getmtime(cache_file)
            if file_age < 24 * 3600:  # 24 hours
                with open(cache_file, 'r') as f:
                    cached_result = json.load(f)
                    cached_result['cached'] = True
                    cached_result['cache_age_hours'] = file_age / 3600
                    return cached_result

        # Run comprehensive percentile forward mapping analysis
        analysis = run_percentile_forward_analysis(ticker, lookback_days=1095)

        result = {
            "ticker": ticker,
            "current_state": {
                "current_percentile": float(analysis['current_percentile']),
                "current_rsi_ma": float(analysis['current_rsi_ma'])
            },
            "prediction": analysis['prediction'],
            "bin_stats": analysis['bin_stats'],
            "transition_matrices": analysis['transition_matrices'],
            "backtest_results": analysis['backtest_results'][-50:],  # Only last 50 for performance
            "accuracy_metrics": analysis['accuracy_metrics'],
            "model_bin_mappings": analysis.get('model_bin_mappings', {}),  # NEW: Full spectrum mappings
            "timestamp": datetime.now().isoformat(),
            "cached": False
        }

        # Save to cache
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)

        return result

    except Exception as e:
        import traceback
        print(f"Error in /api/percentile-forward for {ticker}:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/percentile-forward-4h/{ticker}")
async def get_percentile_forward_mapping_4h(ticker: str, force_refresh: bool = False):
    """
    Get 4-HOUR percentile-to-forward-return mapping analysis for a ticker.

    **4-HOUR TIMEFRAME VERSION**

    Identical methodology to daily Percentile Forward Mapping, but using:
    - 4-hour OHLC candles
    - Horizons: 12h (3 bars), 24h (6 bars), 36h (9 bars), 48h (12 bars)
    - Same model suite: Empirical, Markov, Linear, Polynomial, Quantile, Kernel

    **Returns:**
    - Current 4H percentile and RSI-MA value
    - Forward return forecasts (12h, 24h, 36h, 48h) from all methods
    - Empirical bin statistics for 4H data
    - Transition matrices for 4H percentile evolution
    - Backtest accuracy metrics (out-of-sample performance)
    - Trading recommendation based on model strength

    **Example Response:**
    ```json
    {
      "ticker": "AAPL",
      "timeframe": "4H",
      "horizon_labels": ["12h", "24h", "36h", "48h"],
      "current_percentile": 45.2,
      "prediction": {
        "ensemble_forecast_3d": 0.12,  // 12h forecast
        "ensemble_forecast_7d": 0.25,  // 24h forecast
        "ensemble_forecast_14d": 0.38, // 36h forecast
        "ensemble_forecast_21d": 0.51  // 48h forecast
      }
    }
    ```
    """
    ticker = ticker.upper()

    try:
        # Import the 4H analysis function
        from percentile_forward_4h import run_percentile_forward_analysis_4h

        # Check cache first for performance (24-hour cache)
        cache_file = os.path.join(CACHE_DIR, f"{ticker}_percentile_forward_4h.json")

        if not force_refresh and os.path.exists(cache_file):
            file_age = datetime.now().timestamp() - os.path.getmtime(cache_file)
            if file_age < 24 * 3600:  # 24 hours
                with open(cache_file, 'r') as f:
                    cached_result = json.load(f)
                    cached_result['cached'] = True
                    cached_result['cache_age_hours'] = file_age / 3600
                    return cached_result

        # Run comprehensive 4H percentile forward mapping analysis
        analysis = run_percentile_forward_analysis_4h(ticker, lookback_days=365)

        result = {
            "ticker": ticker,
            "timeframe": "4H",
            "horizon_labels": analysis['horizon_labels'],
            "horizon_bars": analysis['horizon_bars'],
            "current_state": {
                "current_percentile": float(analysis['current_percentile']),
                "current_rsi_ma": float(analysis['current_rsi_ma'])
            },
            "prediction": analysis['prediction'],
            "bin_stats": analysis['bin_stats'],
            "transition_matrices": analysis['transition_matrices'],
            "backtest_results": analysis['backtest_results'][-50:],  # Only last 50 for performance
            "accuracy_metrics": analysis['accuracy_metrics'],
            "model_bin_mappings": analysis.get('model_bin_mappings', {}),
            "timestamp": datetime.now().isoformat(),
            "cached": False
        }
        import traceback
        # Clean NaN values before serializationError in /api/percentile-forward-4h for {ticker}:")
        result = clean_nan_values(result)

        # Save to cache
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)

        return result

    except Exception as e:
        import traceback
        print(f"Error in /api/percentile-forward-4h for {ticker}:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Use v2 calculator with PineScript-inspired calculations
from gamma_risk_distance_v2 import get_symbol_risk_distances, get_risk_distance_data

@app.get("/api/risk-distance/{symbol}")
async def get_risk_distance(symbol: str):
    """Get comprehensive risk distance data for a symbol."""
    try:
        data = get_symbol_risk_distances(symbol.upper())
        if data:
            return {"status": "success", "data": data}
        return {"status": "error", "message": f"No data available for {symbol}"}
    except Exception as e:
        logger.error(f"Error fetching risk distance for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/risk-distance/batch")
async def get_batch_risk_distances(request: dict):
    """Get risk distance data for multiple symbols."""
    try:
        symbols = request.get("symbols", [])
        if not symbols:
            return {"status": "error", "message": "No symbols provided"}
        
        data = get_risk_distance_data(symbols)
        return {"status": "success", "data": data, "count": len(data)}
    except Exception as e:
        logger.error(f"Error fetching batch risk distances: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/risk-distance/{symbol}/summary")
async def get_risk_distance_summary(symbol: str):
    """Get condensed risk distance summary for quick display."""
    try:
        data = get_symbol_risk_distances(symbol.upper())
        if not data:
            return {"status": "error", "message": f"No data available for {symbol}"}
        
        # Extract key metrics for summary view (v2 enhanced)
        summary = {
            "symbol": symbol.upper(),
            "current_price": data["current_price"],
            "timestamp": data["timestamp"],

            # Nearest support/resistance with GEX values
            "nearest_support": {
                "level": data["put_walls"].get("swing", {}).get("strike", 0),
                "distance_pct": data["put_walls"].get("swing", {}).get("distance_pct", 0),
                "strength": data["put_walls"].get("swing", {}).get("strength", 0),
                "gex_value": data["put_walls"].get("swing", {}).get("gex_value", 0)
            },
            "nearest_resistance": {
                "level": data["call_walls"].get("swing", {}).get("strike", 0),
                "distance_pct": data["call_walls"].get("swing", {}).get("distance_pct", 0),
                "strength": data["call_walls"].get("swing", {}).get("strength", 0),
                "gex_value": data["call_walls"].get("swing", {}).get("gex_value", 0)
            },

            # Max pain with pin risk assessment
            "max_pain": {
                "weekly": {
                    "strike": data["max_pain"].get("weekly", {}).get("strike", 0),
                    "distance_pct": data["max_pain"].get("weekly", {}).get("distance_pct", 0),
                    "pin_risk": data["max_pain"].get("weekly", {}).get("pin_risk", "LOW")
                },
                "swing": {
                    "strike": data["max_pain"].get("swing", {}).get("strike", 0),
                    "distance_pct": data["max_pain"].get("swing", {}).get("distance_pct", 0),
                    "pin_risk": data["max_pain"].get("swing", {}).get("pin_risk", "LOW")
                },
                "long": {
                    "strike": data["max_pain"].get("long", {}).get("strike", 0),
                    "distance_pct": data["max_pain"].get("long", {}).get("distance_pct", 0),
                    "pin_risk": data["max_pain"].get("long", {}).get("pin_risk", "LOW")
                },
                "quarterly": {
                    "strike": data["max_pain"].get("quarterly", {}).get("strike", 0),
                    "distance_pct": data["max_pain"].get("quarterly", {}).get("distance_pct", 0),
                    "pin_risk": data["max_pain"].get("quarterly", {}).get("pin_risk", "LOW")
                }
            },

            # Gamma flip with context
            "gamma_flip": {
                "strike": data.get("gamma_flip", {}).get("strike", 0),
                "distance_pct": data.get("gamma_flip", {}).get("distance_pct", 0),
                "net_gex_above": data.get("gamma_flip", {}).get("net_gex_above", 0),
                "net_gex_below": data.get("gamma_flip", {}).get("net_gex_below", 0)
            },

            # Weighted recommendations with confidence
            "weighted_support": {
                "recommended_wall": data.get("weighted_walls", {}).get("put", {}).get("recommended_wall", 0),
                "method_used": data.get("weighted_walls", {}).get("put", {}).get("method_used", ""),
                "confidence": data.get("weighted_walls", {}).get("put", {}).get("confidence", "low")
            },
            "weighted_resistance": {
                "recommended_wall": data.get("weighted_walls", {}).get("call", {}).get("recommended_wall", 0),
                "method_used": data.get("weighted_walls", {}).get("call", {}).get("method_used", ""),
                "confidence": data.get("weighted_walls", {}).get("call", {}).get("confidence", "low")
            },

            # Market regime (v2 feature)
            "regime": data.get("regime", {}).get("regime", "Normal Volatility"),
            "vix": data.get("regime", {}).get("vix_value", 16.0),

            # SD levels for expected move
            "sd_levels": data.get("sd_levels", {}),

            # Summary
            "position": data.get("summary", {}).get("position_in_range", "unknown"),
            "risk_reward": data.get("summary", {}).get("risk_reward_ratio", 1.0),
            "recommendation": data.get("summary", {}).get("recommendation", "")
        }
        
        return {"status": "success", "data": summary}
    except Exception as e:
        logger.error(f"Error fetching risk distance summary for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Add at the top with other imports
from gamma_data_service import (
    scan_all_symbols, 
    get_symbol_risk_distance, 
    refresh_and_get_all
)

# Add these endpoints (place after existing routes)

@app.get("/api/gamma/all")
async def get_all_gamma_data(refresh: bool = False):
    """Get gamma wall data for all symbols."""
    try:
        if refresh:
            data = refresh_and_get_all()
        else:
            data = scan_all_symbols()
        return {"status": "success", "data": data}
    except Exception as e:
        logger.error(f"Error fetching gamma data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gamma/{symbol}")
async def get_symbol_gamma(symbol: str):
    """Get gamma wall data for a specific symbol."""
    try:
        data = get_symbol_risk_distance(symbol)
        if data:
            return {"status": "success", "data": data}
        return {"status": "error", "message": f"No data for {symbol}"}
    except Exception as e:
        logger.error(f"Error fetching gamma for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gamma/data")
async def get_gamma_data():
    """Get cached gamma wall data from scanner output."""
    try:
        # Try multiple locations for the data file
        possible_paths = [
            Path(__file__).parent / 'cache' / 'gamma_walls_data.json',
            Path(__file__).parent / 'Restoring' / 'cache' / 'gamma_walls_data.json',
        ]
        
        for data_file in possible_paths:
            if data_file.exists():
                with open(data_file, 'r') as f:
                    data = json.load(f)
                return {"status": "success", "data": data}
        
        # If no cached data, return error with instructions
        return {
            "status": "error", 
            "message": "No cached gamma data found. Run enhanced_gamma_scanner_weekly.py first.",
            "data": None
        }
    except Exception as e:
        logger.error(f"Error loading gamma data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/gamma/refresh")
async def refresh_gamma_data():
    """Trigger a fresh gamma scan."""
    try:
        import subprocess
        import sys
        
        scanner_path = Path(__file__).parent / 'Restoring' / 'enhanced_gamma_scanner_weekly.py'
        
        if not scanner_path.exists():
            return {"status": "error", "message": f"Scanner not found at {scanner_path}"}
        
        # Run the scanner
        result = subprocess.run(
            [sys.executable, str(scanner_path)],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            return {"status": "success", "message": "Gamma scan completed", "output": result.stdout[-500:]}
        else:
            return {"status": "error", "message": result.stderr[-500:]}
            
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Scan timed out after 120 seconds"}
    except Exception as e:
        logger.error(f"Error running gamma scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))
