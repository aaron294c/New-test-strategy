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

# Initialize FastAPI app
app = FastAPI(
    title="RSI-MA Performance Analytics API",
    description="Backend API for RSI-MA trading strategy analysis",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache directory for results
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Default tickers
DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "QQQ", "SPY"]

# ============================================================================
# Request/Response Models
# ============================================================================

class BacktestRequest(BaseModel):
    tickers: List[str] = Field(default=DEFAULT_TICKERS, description="List of ticker symbols")
    lookback_period: int = Field(default=500, ge=100, le=1000)
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
            lookback_period=500,
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
            lookback_period=500,
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
            lookback_period=500,
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
            lookback_period=500,
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
            lookback_period=500,
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
            lookback_period=500,
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

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    print("\n" + "="*60)
    print("RSI-MA Performance Analytics API")
    print("="*60)
    print(f"Cache directory: {os.path.abspath(CACHE_DIR)}")
    print(f"Default tickers: {', '.join(DEFAULT_TICKERS)}")
    print("="*60 + "\n")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
