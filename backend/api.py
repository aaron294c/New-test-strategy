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
    ma_length: int = Field(default=14, ge=5, le=50)
    max_horizon: int = Field(default=21, ge=7, le=30)

class MonteCarloRequest(BaseModel):
    num_simulations: int = Field(default=1000, ge=100, le=5000)
    max_periods: int = Field(default=21, ge=10, le=50)
    target_percentiles: List[float] = Field(default=[5, 15, 25, 50, 75, 85, 95])

class PerformanceMatrixRequest(BaseModel):
    ticker: str
    threshold: float = Field(default=5.0, ge=1.0, le=20.0)

class TickerComparisonRequest(BaseModel):
    tickers: List[str] = Field(min_items=1, max_items=5)
    threshold: float = Field(default=5.0)

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
            "ticker_comparison": "/api/compare"
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
        current_percentile = float(percentile_ranks.iloc[-1]) if not pd.isna(percentile_ranks.iloc[-1]) else 50.0
        current_price = float(data['Close'].iloc[-1])
        current_rsi_ma = float(indicator.iloc[-1]) if not pd.isna(indicator.iloc[-1]) else 50.0
        
        # Prepare historical data
        historical_df = pd.DataFrame({
            'Close': data['Close'],
            'rsi_ma_percentile': percentile_ranks
        }).dropna()
        
        # Run Monte Carlo simulation with custom target percentiles
        target_percentiles = request.target_percentiles if hasattr(request, 'target_percentiles') and request.target_percentiles else [5, 15, 25, 50, 75, 85, 95]
        
        mc_results = run_monte_carlo_for_ticker(
            ticker=ticker,
            current_percentile=current_percentile,
            current_price=current_price,
            historical_data=historical_df,
            num_simulations=request.num_simulations,
            target_percentiles=target_percentiles
        )
        
        # Flatten the structure to match frontend expectations
        return {
            "ticker": ticker,
            "current_percentile": current_percentile,
            "current_price": current_price,
            "simulation_results": mc_results.get('simulation_results', {}),
            "first_passage_times": mc_results.get('first_passage_times', {}),
            "exit_timing": mc_results.get('exit_timing', {}),
            "fan_chart": mc_results.get('fan_chart', {}),
            "parameters": {
                "drift": mc_results.get('parameters', {}).get('drift', 0),
                "volatility": mc_results.get('parameters', {}).get('volatility', 0),
                "current_percentile": current_percentile,
                "current_price": current_rsi_ma,
                "num_simulations": request.num_simulations,
                "max_periods": request.max_periods if hasattr(request, 'max_periods') else 21
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        import traceback
        error_detail = f"Monte Carlo Error: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)

@app.get("/api/rsi-chart/{ticker}")
async def get_rsi_percentile_chart(ticker: str, days: int = 252):
    """
    Get RSI and RSI-MA time series data with percentile levels for chart visualization.
    Returns historical RSI, RSI-MA, percentile rank, and percentile thresholds.
    """
    ticker = ticker.upper()
    
    try:
        # Create backtester instance
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
        
        # Calculate RSI and percentiles
        indicator = backtester.calculate_rsi_ma_indicator(data['Close'])
        percentile_ranks = backtester.calculate_percentile_ranks(indicator)
        
        # Get last N days
        last_days = min(days, len(data))
        dates = data.index[-last_days:].strftime('%Y-%m-%d').tolist()
        
        # Calculate RSI directly (for plotting)
        prices = data['Close']
        delta = prices.diff()
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        avg_gains = gains.ewm(span=backtester.rsi_length, adjust=False).mean()
        avg_losses = losses.ewm(span=backtester.rsi_length, adjust=False).mean()
        
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.fillna(50)
        
        # Calculate percentile thresholds from full historical data
        valid_rsi_ma = indicator.dropna()
        percentiles = {
            'p5': float(np.percentile(valid_rsi_ma, 5)),
            'p15': float(np.percentile(valid_rsi_ma, 15)),
            'p25': float(np.percentile(valid_rsi_ma, 25)),
            'p50': float(np.percentile(valid_rsi_ma, 50)),
            'p75': float(np.percentile(valid_rsi_ma, 75)),
            'p85': float(np.percentile(valid_rsi_ma, 85)),
            'p95': float(np.percentile(valid_rsi_ma, 95))
        }
        
        # Build chart data
        chart_data = {
            'dates': dates,
            'rsi': rsi.iloc[-last_days:].fillna(50).tolist(),
            'rsi_ma': indicator.iloc[-last_days:].fillna(50).tolist(),
            'percentile_rank': percentile_ranks.iloc[-last_days:].fillna(50).tolist(),
            'percentile_thresholds': percentiles,
            'current_rsi': float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0,
            'current_rsi_ma': float(indicator.iloc[-1]) if not pd.isna(indicator.iloc[-1]) else 50.0,
            'current_percentile': float(percentile_ranks.iloc[-1]) if not pd.isna(percentile_ranks.iloc[-1]) else 50.0
        }
        
        return {
            "ticker": ticker,
            "chart_data": chart_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RSI Chart Error: {str(e)}")

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

# ============================================================================
# Startup Event
# ============================================================================

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
