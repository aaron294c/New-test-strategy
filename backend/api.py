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
import os
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import json
import os
from datetime import datetime
import pandas as pd
import numpy as np

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

# CORS middleware for React frontend (allow all in dev, configurable via ALLOWED_ORIGINS)
raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

# If wildcard or app.github.dev, rely on regex to catch Codespaces subdomains
allow_all_regex = r"https://.*\.app\.github\.dev"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allowed_origins == ["*"] else allowed_origins,
    allow_origin_regex=allow_all_regex,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and add Swing Framework router (REAL historical trade data)
try:
    from swing_framework_api import router as swing_framework_router
    app.include_router(swing_framework_router)
    print("✓ Swing Framework API registered (REAL trade data)")
except Exception as e:
    print(f"⚠️  Could not load Swing Framework API: {e}")

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
    app.include_router(gamma_router)
    print("✓ Gamma Wall Scanner API registered")
except Exception as e:
    print(f"⚠️  Could not load Gamma Scanner API: {e}")

# Import and add Price Fetcher router
try:
    import sys
    from pathlib import Path
    api_dir = Path(__file__).parent / "api"
    if str(api_dir) not in sys.path:
        sys.path.insert(0, str(api_dir))

    from price_fetcher import router as price_router
    app.include_router(price_router)
    print("✓ Price Fetcher API registered")
except Exception as e:
    print(f"⚠️  Could not load Price Fetcher API: {e}")

# Import and add Lower Extension API
try:
    import sys
    from pathlib import Path
    api_lower_ext_dir = Path(__file__).parent / "api"
    if str(api_lower_ext_dir) not in sys.path:
        sys.path.insert(0, str(api_lower_ext_dir))

    from lower_extension import calculate_mbad_levels
    from nadaraya_watson import calculate_nadaraya_watson_lower_band
    print("✓ Lower Extension API module loaded")
    print("✓ Nadaraya-Watson Envelope API module loaded")
except Exception as e:
    print(f"⚠️  Could not load indicator APIs: {e}")

# Cache directory for results
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Default tickers
DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "QQQ", "SPY", "GLD", "SLV", "BRK-B"]

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
            "trade_simulation": "/api/trade-simulation/{ticker}"
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

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
async def get_multi_timeframe_analysis(ticker: str):
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
        analysis = run_multi_timeframe_analysis(ticker)

        return {
            "ticker": ticker,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }

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
async def get_enhanced_multi_timeframe_analysis(ticker: str):
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
        analysis = run_enhanced_analysis(ticker)

        return {
            "ticker": ticker,
            "enhanced_analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }

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

def clean_nan_values(obj):
    """Recursively replace NaN and inf values with None for JSON serialization."""
    import math
    if isinstance(obj, dict):
        return {k: clean_nan_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_values(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    return obj

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

        # Clean NaN values before serialization
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


# ============================================================================
# Multi-Timeframe Trading Guide Endpoints
# ============================================================================

# Helper function to get stock data
def get_stock_data(ticker: str, timeframe: str):
    """Get data for a specific stock and timeframe."""
    # Normalize timeframe to lowercase
    timeframe = timeframe.lower()

    data_map = {
        "NVDA": {"4h": NVDA_4H_DATA, "daily": NVDA_DAILY_DATA},
        "MSFT": {"4h": MSFT_4H_DATA, "daily": MSFT_DAILY_DATA},
        "GOOGL": {"4h": GOOGL_4H_DATA, "daily": GOOGL_DAILY_DATA},
        "AAPL": {"4h": AAPL_4H_DATA, "daily": AAPL_DAILY_DATA},
        "GLD": {"4h": GLD_4H_DATA, "daily": GLD_DAILY_DATA},
        "SLV": {"4h": SLV_4H_DATA, "daily": SLV_DAILY_DATA},
        "TSLA": {"4h": TSLA_4H_DATA, "daily": TSLA_DAILY_DATA},
        "NFLX": {"4h": NFLX_4H_DATA, "daily": NFLX_DAILY_DATA},
        "BRK-B": {"4h": BRKB_4H_DATA, "daily": BRKB_DAILY_DATA},
        "WMT": {"4h": WMT_4H_DATA, "daily": WMT_DAILY_DATA},
        "UNH": {"4h": UNH_4H_DATA, "daily": UNH_DAILY_DATA},
        "AVGO": {"4h": AVGO_4H_DATA, "daily": AVGO_DAILY_DATA},
        "LLY": {"4h": LLY_4H_DATA, "daily": LLY_DAILY_DATA},
        "TSM": {"4h": TSM_4H_DATA, "daily": TSM_DAILY_DATA},
        "ORCL": {"4h": ORCL_4H_DATA, "daily": ORCL_DAILY_DATA},
        "OXY": {"4h": OXY_4H_DATA, "daily": OXY_DAILY_DATA}
    }

    if ticker not in data_map:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    if timeframe not in ["4h", "daily"]:
        raise HTTPException(status_code=400, detail="Timeframe must be '4h' or 'daily'")

    return data_map[ticker][timeframe]

class TradingRecommendationRequest(BaseModel):
    ticker: str
    current_4h_bin: str
    current_daily_bin: str

@app.get("/stocks")
async def get_stocks():
    """Get all available stocks with metadata."""
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

@app.get("/stock/{ticker}")
async def get_stock(ticker: str):
    """Get detailed metadata for a specific stock."""
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
            "is_momentum": not meta.is_mean_reverter,
            "volatility_level": meta.volatility_level
        },
        "guidance": {
            "entry": meta.entry_guidance,
            "avoid": meta.avoid_guidance,
            "special_notes": meta.special_notes
        }
    }

@app.get("/bins/{ticker}/{timeframe}")
async def get_bins(ticker: str, timeframe: str):
    """Get all percentile bins for a stock and timeframe with enriched trading guidance."""
    # Normalize timeframe to lowercase
    timeframe = timeframe.lower()
    data = get_stock_data(ticker, timeframe)

    # Get stock metadata for context
    if ticker not in STOCK_METADATA:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    meta = STOCK_METADATA[ticker]

    # Helper function to determine action for a bin
    def get_bin_action(bin_range: str, mean: float, t_score: float, is_significant: bool) -> str:
        if not is_significant:
            return "Avoid - weak signal"

        if mean > 1.5 and is_significant:
            return "Enter Long"
        elif mean > 0.5 and is_significant:
            return "Add to position"
        elif mean < -1.5 and is_significant:
            return "Trim/Avoid"
        elif mean < 0:
            return "Avoid"
        else:
            return "Wait for better entry"

    # Helper function to get signal strength emoji
    def get_signal_strength(t_score: float) -> str:
        t = abs(t_score)
        if t >= 4.0:
            return "✅✅✅"
        elif t >= 3.0:
            return "✅✅"
        elif t >= 2.0:
            return "✅"
        elif t >= 1.5:
            return "⚠️"
        else:
            return "❌"

    # Helper function to get position size guidance
    def get_position_size_guidance(t_score: float, mean: float) -> str:
        t = abs(t_score)
        if t >= 3.0 and abs(mean) >= 2.0:
            return "Large (50-70%)"
        elif t >= 2.0 and abs(mean) >= 1.0:
            return "Medium (30-50%)"
        elif t >= 2.0:
            return "Small (10-30%)"
        else:
            return "None (wait)"

    return {
        bin_range: {
            "bin_range": stats.bin_range,
            "mean": stats.mean,
            "median": stats.median,
            "std": stats.std,
            "sample_size": stats.sample_size,
            "se": stats.se,
            "t_score": stats.t_score,
            "is_significant": stats.is_significant,
            "percentile_5th": stats.percentile_5th,
            "percentile_95th": stats.percentile_95th,
            "upside": stats.upside,
            "downside": stats.downside,
            "action": get_bin_action(bin_range, stats.mean, stats.t_score, stats.is_significant),
            "signal_strength": get_signal_strength(stats.t_score),
            "position_size_guidance": get_position_size_guidance(stats.t_score, stats.mean)
        }
        for bin_range, stats in data.items()
    }

@app.post("/recommendation")
async def get_recommendation(request: TradingRecommendationRequest):
    """Get trading recommendation based on current bins."""
    ticker = request.ticker
    current_4h_bin = request.current_4h_bin
    current_daily_bin = request.current_daily_bin

    if ticker not in STOCK_METADATA:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    # Get data
    fourh_data = get_stock_data(ticker, "4h")
    daily_data = get_stock_data(ticker, "daily")
    meta = STOCK_METADATA[ticker]

    # Get bin statistics
    if current_4h_bin not in fourh_data:
        raise HTTPException(status_code=400, detail=f"Invalid 4H bin: {current_4h_bin}")
    if current_daily_bin not in daily_data:
        raise HTTPException(status_code=400, detail=f"Invalid Daily bin: {current_daily_bin}")

    fourh_stats = fourh_data[current_4h_bin]
    daily_stats = daily_data[current_daily_bin]

    # Calculate position size
    position_size, confidence = calculate_position_size(
        daily_stats.t_score,
        fourh_stats.t_score
    )

    # Determine action
    if daily_stats.is_significant and fourh_stats.is_significant:
        if daily_stats.mean > 0 and fourh_stats.mean > 0:
            action = "ENTER"
        elif daily_stats.mean < 0 or fourh_stats.mean < 0:
            action = "AVOID"
        else:
            action = "WAIT"
    elif daily_stats.is_significant and daily_stats.mean > 0:
        action = "WAIT_FOR_4H_DIP"
    else:
        action = "NO_TRADE"

    # Build guidance
    signal_strength_daily = "✅✅✅" if abs(daily_stats.t_score) >= 3 else "✅✅" if abs(daily_stats.t_score) >= 2 else "⚠️"
    signal_strength_4h = "✅✅✅" if abs(fourh_stats.t_score) >= 3 else "✅✅" if abs(fourh_stats.t_score) >= 2 else "⚠️"

    guidance = f"{'✅' if daily_stats.is_significant else '❌'} Daily 7d signal is {'significant' if daily_stats.is_significant else 'not significant'} (t={daily_stats.t_score:.2f}): {daily_stats.mean:+.2f}% expected. "
    guidance += f"{'✅' if fourh_stats.is_significant else '❌'} 4H signal is {'significant' if fourh_stats.is_significant else 'not significant'} (t={fourh_stats.t_score:.2f}): {fourh_stats.mean:+.2f}% expected (48h). "
    guidance += f"📊 {meta.personality}: {meta.special_notes}"

    return {
        "ticker": ticker,
        "stock_name": meta.name,
        "personality": meta.personality,
        "current_4h_bin": current_4h_bin,
        "current_daily_bin": current_daily_bin,
        "fourh_mean": fourh_stats.mean,
        "fourh_t_score": fourh_stats.t_score,
        "fourh_is_significant": fourh_stats.is_significant,
        "fourh_signal_strength": signal_strength_4h,
        "daily_mean": daily_stats.mean,
        "daily_t_score": daily_stats.t_score,
        "daily_is_significant": daily_stats.is_significant,
        "daily_signal_strength": signal_strength_daily,
        "recommended_action": action,
        "position_size": position_size,
        "confidence": confidence,
        "detailed_guidance": guidance,
        "stop_loss_5th_percentile": fourh_stats.percentile_5th,
        "upside_95th_percentile": fourh_stats.percentile_95th
    }

def calculate_position_size(daily_t: float, fourh_t: float) -> tuple[int, str]:
    """Calculate position size based on t-scores."""
    # Normalize t-scores to 0-2 scale
    daily_score = min(max(daily_t / 2.0, 0), 2)
    fourh_score = min(max(fourh_t / 2.0, 0), 2)

    # Combined scoring
    if daily_score >= 1.5:  # Daily t >= 3.0
        if fourh_score >= 1.5:  # 4H t >= 3.0
            return 70, "VERY HIGH"
        elif fourh_score >= 1.0:  # 4H t >= 2.0
            return 50, "HIGH"
        else:
            return 30, "MEDIUM"
    elif daily_score >= 1.0:  # Daily t >= 2.0
        if fourh_score >= 1.5:
            return 50, "HIGH"
        elif fourh_score >= 1.0:
            return 40, "MEDIUM-HIGH"
        else:
            return 20, "MEDIUM"
    else:
        return 0, "NO POSITION"

@app.get("/position-calculator")
async def position_calculator(daily_t: float, fourh_t: float):
    """Calculate position size based on t-scores."""
    position, confidence = calculate_position_size(daily_t, fourh_t)

    return {
        "daily_t_score": daily_t,
        "fourh_t_score": fourh_t,
        "position_size": position,
        "confidence": confidence,
        "explanation": f"Daily t={daily_t:.2f}, 4H t={fourh_t:.2f} → {confidence} confidence → {position}% position"
    }

@app.get("/comparison")
async def compare_stocks(bin_4h: str = "25-50", bin_daily: str = "25-50"):
    """Compare all stocks at the same percentile bins."""
    results = []

    for ticker in ["NVDA", "MSFT", "GOOGL", "AAPL", "GLD", "SLV", "TSLA", "NFLX", "BRK-B", "WMT", "UNH", "AVGO", "LLY", "TSM", "ORCL", "OXY"]:
        try:
            fourh_data = get_stock_data(ticker, "4h")
            daily_data = get_stock_data(ticker, "daily")
            meta = STOCK_METADATA[ticker]

            fourh_stats = fourh_data.get(bin_4h)
            daily_stats = daily_data.get(bin_daily)

            if fourh_stats and daily_stats:
                position, confidence = calculate_position_size(
                    daily_stats.t_score,
                    fourh_stats.t_score
                )

                results.append({
                    "ticker": ticker,
                    "name": meta.name,
                    "personality": meta.personality,
                    "fourh_mean": fourh_stats.mean,
                    "fourh_t": fourh_stats.t_score,
                    "daily_mean": daily_stats.mean,
                    "daily_t": daily_stats.t_score,
                    "position_size": position,
                    "confidence": confidence,
                    "ease_rating": meta.ease_rating
                })
        except Exception as e:
            continue

    # Sort by position size
    results.sort(key=lambda x: x["position_size"], reverse=True)

    return {
        "bin_4h": bin_4h,
        "bin_daily": bin_daily,
        "stocks": results
    }

@app.get("/trade-management/{ticker}")
async def get_trade_management_rules(ticker: str):
    """Get dynamic trade management rules for a specific stock."""
    if ticker not in STOCK_METADATA:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    fourh_data = get_stock_data(ticker, "4h")
    meta = STOCK_METADATA[ticker]

    # Analyze all bins to determine best ADD zones
    add_rules = []
    trim_rules = []
    exit_rules = []

    bin_order = ["0-5", "5-15", "15-25", "25-50", "50-75", "75-85", "85-95", "95-100"]

    for bin_range in bin_order:
        stats = fourh_data.get(bin_range)
        if not stats:
            continue

        # ADD rules (significant positive expected returns)
        if stats.is_significant and stats.mean > 0:
            position, confidence = calculate_position_size(3.0, stats.t_score)  # Assume strong daily signal

            if stats.t_score >= 4.0:
                intensity = "⚡⚡ AGGRESSIVE ADD"
            elif stats.t_score >= 3.0:
                intensity = "⚡ STRONG ADD"
            elif stats.t_score >= 2.0:
                intensity = "✅ ADD"
            else:
                continue

            add_rules.append({
                "bin": bin_range + "%",
                "intensity": intensity,
                "max_position": position,
                "expected_return": stats.mean,
                "t_score": stats.t_score,
                "confidence": confidence,
                "stop_loss": stats.percentile_5th,
                "upside": stats.percentile_95th
            })

        # TRIM rules (high percentiles - take profits)
        if bin_range in ["75-85", "85-95", "95-100"]:
            if bin_range == "75-85":
                trim_pct = 25
                action = "⚠️ TRIM"
            elif bin_range == "85-95":
                trim_pct = 50
                action = "⚠️⚠️ TRIM"
            else:  # 95-100
                trim_pct = 100
                action = "🛑 EXIT"

            trim_rules.append({
                "bin": bin_range + "%",
                "action": action,
                "trim_percentage": trim_pct,
                "reason": "Taking profits at high percentile"
            })

        # EXIT rules (significantly bearish bins)
        if stats.is_significant and stats.mean < -0.5:
            exit_rules.append({
                "bin": bin_range + "%",
                "action": "❌ IMMEDIATE EXIT",
                "expected_return": stats.mean,
                "t_score": stats.t_score,
                "reason": f"Bearish signal: {stats.mean:.2f}% expected with t={stats.t_score:.2f}"
            })

    # Calculate dynamic stop loss (worst 5th percentile from tradeable bins)
    tradeable_bins_data = [fourh_data[b] for b in meta.tradeable_4h_zones if b in fourh_data]
    stop_loss_values = [b.percentile_5th for b in tradeable_bins_data if b.percentile_5th is not None]
    dynamic_stop_loss = min(stop_loss_values) if stop_loss_values else -3.0

    return {
        "ticker": ticker,
        "stock_name": meta.name,
        "personality": meta.personality,
        "add_rules": add_rules,
        "trim_rules": trim_rules,
        "exit_rules": exit_rules,
        "stop_loss_guidance": {
            "dynamic_stop_loss": round(dynamic_stop_loss, 2),
            "recommended_stop": max(dynamic_stop_loss, -3.5),  # Cap at -3.5%
            "explanation": f"Based on 5th percentile of tradeable bins. Protects against {abs(dynamic_stop_loss):.1f}% downside."
        },
        "time_management": {
            "hold_period": "7 days (Daily timeframe)",
            "early_exit_trigger": "Target hit in < 5 days",
            "daily_monitoring": "Check 4H percentile daily for ADD/TRIM opportunities"
        }
    }

# ============================================================================
# Lower Extension Distance API Endpoints
# ============================================================================

@app.get("/api/lower-extension/metrics/{ticker}")
async def get_lower_extension_metrics(ticker: str, length: int = 256, lookback_days: int = 30):
    """
    Get lower extension distance metrics for a ticker

    Computes signed percent distance to blue lower extension line
    with 30-day lookback breach metrics
    """
    try:
        # Fetch REAL data using backtester
        backtester = EnhancedPerformanceMatrixBacktester(
            tickers=[ticker],
            lookback_period=max(500, length + lookback_days + 50),
            rsi_length=14,
            ma_length=14,
            max_horizon=21
        )

        # Get real price data from yfinance
        data = backtester.fetch_data(ticker)
        if data is None or len(data) == 0:
            raise HTTPException(status_code=404, detail=f"Could not fetch data for {ticker}")

        # Get close and open prices for IV weighting
        close_prices = data['Close'].values
        open_prices = data['Open'].values
        if len(close_prices) < length:
            raise HTTPException(status_code=400, detail=f"Insufficient data for {ticker} (need {length} points, got {len(close_prices)})")

        # Current price
        current_price = float(close_prices[-1])

        # Generate historical prices for the last lookback_days
        historical_prices = []
        for i in range(lookback_days, 0, -1):
            if len(close_prices) > i:
                idx = len(close_prices) - i - 1
                price = float(close_prices[idx])
                date = data.index[idx]
                historical_prices.append({
                    'timestamp': date.isoformat() if hasattr(date, 'isoformat') else str(date),
                    'price': round(price, 2)
                })

        # Calculate MBAD levels using enough historical data with IV weighting
        all_close_prices = close_prices[-length-lookback_days:]
        all_open_prices = open_prices[-length-lookback_days:]
        levels = calculate_mbad_levels(all_close_prices, opens=all_open_prices, length=length, ticker=ticker)

        lower_ext = levels['ext_lower']

        # Calculate metrics
        pct_dist_lower_ext = round(((current_price - lower_ext) / lower_ext) * 100, 2)
        is_below_lower_ext = bool(pct_dist_lower_ext < 0)
        abs_pct_dist_lower_ext = round(abs(pct_dist_lower_ext), 2)

        # 30-day metrics
        pct_dists = [((p['price'] - lower_ext) / lower_ext) * 100 for p in historical_prices]
        min_pct_dist_30d = round(min(pct_dists), 2)
        median_abs_pct_dist_30d = round(float(np.median(np.abs(pct_dists))), 2)
        breach_count_30d = int(sum(1 for d in pct_dists if d < 0))
        breach_rate_30d = round(breach_count_30d / len(pct_dists), 4)
        recent_breached = bool(any(d < 0 for d in pct_dists[-5:]))

        # Proximity score
        proximity_threshold = 5.0
        proximity_score_30d = max(0, min(1, 1 - (median_abs_pct_dist_30d / proximity_threshold)))
        proximity_score_30d = round(proximity_score_30d, 3)

        return {
            'symbol': ticker.upper(),
            'price': current_price,
            'lower_ext': lower_ext,
            'pct_dist_lower_ext': pct_dist_lower_ext,
            'is_below_lower_ext': is_below_lower_ext,
            'abs_pct_dist_lower_ext': abs_pct_dist_lower_ext,
            'min_pct_dist_30d': min_pct_dist_30d,
            'median_abs_pct_dist_30d': median_abs_pct_dist_30d,
            'breach_count_30d': breach_count_30d,
            'breach_rate_30d': breach_rate_30d,
            'recent_breached': recent_breached,
            'proximity_score_30d': proximity_score_30d,
            'last_update': datetime.now().strftime('%b %d, %I:%M%p').lower(),
            'historical_prices': historical_prices,
            'all_levels': levels
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/lower-extension/candles/{ticker}")
async def get_candle_data(ticker: str, days: int = 60):
    """Get candlestick data for chart visualization"""
    try:
        # Fetch REAL data using backtester
        backtester = EnhancedPerformanceMatrixBacktester(
            tickers=[ticker],
            lookback_period=max(500, days + 100),
            rsi_length=14,
            ma_length=14,
            max_horizon=21
        )

        # Get real OHLC data from yfinance
        data = backtester.fetch_data(ticker)
        if data is None or len(data) == 0:
            raise HTTPException(status_code=404, detail=f"Could not fetch data for {ticker}")

        # Get last N days of OHLC data
        recent_data = data.tail(days)

        candles = []
        for idx in recent_data.index:
            row = recent_data.loc[idx]
            candles.append({
                'time': idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx),
                'open': round(float(row['Open']), 2),
                'high': round(float(row['High']), 2),
                'low': round(float(row['Low']), 2),
                'close': round(float(row['Close']), 2)
            })

        return {'symbol': ticker.upper(), 'candles': candles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Nadaraya-Watson Envelope API
# ============================================================================

@app.get("/api/nadaraya-watson/metrics/{ticker}")
async def get_nadaraya_watson_metrics(
    ticker: str,
    length: int = 200,
    bandwidth: float = 8.0,
    atr_period: int = 50,
    atr_mult: float = 2.0
):
    """
    Get Nadaraya-Watson Envelope lower band metrics for a symbol.

    Args:
        ticker: Stock/index symbol
        length: Window size for kernel regression (default: 200, max: 500, min: 20)
        bandwidth: Kernel bandwidth parameter h (default: 8.0)
        atr_period: Period for ATR calculation (default: 50)
        atr_mult: ATR multiplier for envelope width (default: 2.0)

    Returns:
        JSON with NW estimate, bands, breach status, and distance metrics
    """
    try:
        # Fetch REAL data using backtester
        backtester = EnhancedPerformanceMatrixBacktester(
            tickers=[ticker],
            lookback_period=max(500, length + atr_period + 50),
            rsi_length=14,
            ma_length=14,
            max_horizon=21
        )

        # Get real price data from yfinance
        data = backtester.fetch_data(ticker)
        if data is None or len(data) == 0:
            raise HTTPException(status_code=404, detail=f"Could not fetch data for {ticker}")

        # Get OHLC data
        close_prices = data['Close'].values
        high_prices = data['High'].values
        low_prices = data['Low'].values

        if len(close_prices) < max(length, atr_period):
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for {ticker} (need {max(length, atr_period)} points, got {len(close_prices)})"
            )

        # Calculate Nadaraya-Watson lower band
        result = calculate_nadaraya_watson_lower_band(
            close_prices,
            length=length,
            bandwidth=bandwidth,
            atr_period=atr_period,
            atr_mult=atr_mult,
            highs=high_prices,
            lows=low_prices
        )

        if not result['is_valid']:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough data to calculate Nadaraya-Watson for {ticker}"
            )

        # Add symbol and timestamp
        result['symbol'] = ticker.upper()
        result['last_update'] = datetime.now().strftime('%b %d, %I:%M%p').lower()

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    print("\n" + "="*60)
    print("RSI-MA Performance Analytics API")
    print("Multi-Timeframe Trading Guide Enabled")
    print("="*60)
    print(f"Cache directory: {os.path.abspath(CACHE_DIR)}")
    print(f"Default tickers: {', '.join(DEFAULT_TICKERS)}")
    print(f"Trading Guide stocks: NVDA, MSFT, GOOGL, AAPL, GLD, SLV, TSLA, NFLX, BRK-B, WMT, UNH, AVGO, LLY, TSM, ORCL, OXY")
    print("="*60 + "\n")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
