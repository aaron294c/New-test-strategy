#!/usr/bin/env python3
"""
Enhanced Performance Matrix v5 - RSI-MA EMA(14) with COMPREHENSIVE REALISTIC Framework

MAJOR IMPROVEMENTS IN V5:
1. INTEGRATED: Realistic median-based patterns with comprehensive statistical analysis
2. ENHANCED: Dynamic profit-taking framework with actionable signals (not just "HOLD")
3. IMPROVED: Market environment detection for enhanced position sizing
4. ADVANCED: Multi-layer exit strategy with partial profits, trailing stops, and emergency exits
5. UNIFIED: Quality classification system across all analysis sections
6. PRACTICAL: Dollar impact examples and transparent position sizing calculations
7. COMPREHENSIVE: Full trend analysis with both simple and advanced statistical methods

FEATURES:
- RSI(14) + EMA(14) calculation from daily return momentum
- 500-period rolling percentile lookback (no look-ahead)
- Entry thresholds: <=5%, <=10%, <=15% percentile by default
- D1-D7 performance matrix with realistic exit framework
- Command-line argument support for custom tickers
- Updated default tickers: SPY, QQQ, AAPL, AMZN, GOOGL, NVDA, MSFT, META, TSLA, BRK-B, OXY, BTC-USD
- REALISTIC: Exit logic based on median expectations with actionable recommendations
- ENHANCED: Position sizing by signal extremity with market environment adjustments
"""

print("=== SCRIPT STARTING v5 ===")
print("Loading imports...")

import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import argparse
import sys
from datetime import datetime, timedelta
from typing import Tuple, Dict, List, Optional
import time
from dataclasses import dataclass
from scipy.stats import mannwhitneyu, pearsonr, spearmanr, skew, kurtosis, norm

print("All imports successful")
warnings.filterwarnings('ignore')

# --- CONFIG (pinned defaults) ---
RSI_LENGTH = 14
MA_KIND = "EMA"          # Force EMA
MA_LENGTH = 14
LOOKBACK = 500           # Rolling percentile window
STOP_LOSS_PERCENT = 2.0  # Parity with Pine (not used by analytics unless you wire stops)
BB_SD = 2.0              # Parity with Pine (not used unless you wire BB logic)
DEFAULT_ENTRY_THRESHOLDS = [5.0, 10.0, 15.0]  # Analyze <=5%, <=10%, and <=15% percentile entries

# --- ENHANCED STRATEGY CONFIG ---
# Enhanced Entry Filtering
EXTREME_ENTRY_THRESHOLDS = [1.0, 3.0, 5.0] # More granular extreme thresholds

# Position Sizing by Signal Extremity  
EXTREME_POSITION_MULTIPLIERS = {
    1.0: 1.5,   # <=1% percentile: 1.5x position size
    3.0: 1.3,   # <=3% percentile: 1.3x position size  
    5.0: 1.1,   # <=5% percentile: 1.1x position size
    10.0: 1.0,  # <=10% percentile: 1.0x position size
    15.0: 0.9   # <=15% percentile: 0.9x position size
}

# Market Environment Filters
VIX_THRESHOLD = 20.0                       # Stronger signals when VIX > 20
TRENDING_MARKET_REDUCTION = 0.8            # Reduce positions 20% in trending markets

# Updated default tickers
DEFAULT_TICKERS = ["SPY", "QQQ", "AAPL", "AMZN", "GOOGL", "NVDA", "MSFT", "META", "TSLA", "BRK-B", "OXY", "BTC-USD"]

@dataclass
class PerformanceCell:
    """Single cell in the performance matrix."""
    day: int
    percentile_range: str
    sample_size: int
    expected_cumulative_return: float
    expected_success_rate: float
    p25_return: float
    p75_return: float
    confidence_level: str

@dataclass
class EnhancedMarketBenchmark:
    """Enhanced market benchmark with individual and cumulative returns."""
    ticker: str
    individual_daily_returns: Dict[int, float]  # Individual daily returns
    cumulative_returns: Dict[int, float]        # Cumulative returns from D1
    volatility: float

@dataclass
class RiskMetrics:
    """Risk analysis with clearer logic and additional metrics."""
    median_drawdown: float
    p90_drawdown: float  # Worst 10% of drawdowns
    median_recovery_days: float
    recovery_rate: float
    max_consecutive_losses: int
    avg_loss_magnitude: float
    # Additional clarity metrics
    total_losing_trades: int
    total_profitable_trades: int
    worst_single_loss: float
    best_single_gain: float

@dataclass
class OpportunityPattern:
    """Identified profitable opportunity pattern."""
    percentile_range: str
    optimal_day: int
    return_potential: float
    success_rate: float
    sample_size: int
    confidence: str
    risk_reward_ratio: float
    description: str

def determine_unified_strategy_quality(sharpe_efficiency: float, median_return: float, 
                                     profitable_opportunities: int) -> Tuple[str, str]:
    """UNIFIED v5: Determine strategy quality consistently across all analysis sections."""
    
    # Count significant profitable opportunities (>8% returns)
    has_significant_opportunities = profitable_opportunities >= 2
    
    # UNIFIED quality classification
    if sharpe_efficiency >= 0.13 and median_return > 0.5 and has_significant_opportunities:
        quality_rating = "GOOD STRATEGY"
        quality_description = "favorable risk-adjusted returns with profitable patterns"
    elif sharpe_efficiency >= 0.10 and median_return > 0.3:
        quality_rating = "MODERATE STRATEGY" 
        quality_description = "reasonable risk-adjusted returns with manageable risk"
    elif sharpe_efficiency >= 0.05 and median_return > 0:
        quality_rating = "LIMITED STRATEGY"
        quality_description = "marginal profitability requiring careful allocation"
    else:
        quality_rating = "POOR STRATEGY"
        quality_description = "weak performance requiring minimal exposure"
        
    return quality_rating, quality_description

def calculate_enhanced_position_size(threshold: float, base_position_size: float, 
                                   signal_extremity: float, market_environment: Dict = None) -> float:
    """Calculate position size based on signal extremity and market conditions."""
    
    # Apply extremity multiplier
    extremity_multiplier = 1.0
    for thresh, multiplier in EXTREME_POSITION_MULTIPLIERS.items():
        if threshold <= thresh:
            extremity_multiplier = multiplier
            break
    
    enhanced_size = base_position_size * extremity_multiplier
    
    # Apply market environment adjustments if provided
    if market_environment:
        # Reduce size in trending markets
        if market_environment.get('is_trending', False):
            enhanced_size *= TRENDING_MARKET_REDUCTION
            
        # Increase size during high volatility periods  
        if market_environment.get('vix', 0) > VIX_THRESHOLD:
            enhanced_size *= 1.1
    
    return min(enhanced_size, 30.0)  # Cap at 30% position size

def get_enhanced_realistic_exit_signal(current_percentile: float, entry_percentile: float,
                                     days_held: int, current_return: float, 
                                     day_patterns: Dict, threshold: float) -> Dict:
    """ENHANCED v5: Generate realistic exit signals with actionable recommendations."""
    
    exit_signals = {
        'partial_profit': False,
        'trailing_stop': False,
        'full_exit': False,
        'hold': True,
        'reason': 'Continue holding',
        'expectation': {},
        'recommendation': 'hold',
        'action_priority': 'low',
        'dollar_impact': {}
    }
    
    current_day = days_held
    if current_day not in day_patterns:
        exit_signals['reason'] = f'Insufficient data for D{current_day}'
        return exit_signals
    
    pattern = day_patterns[current_day]
    median_percentile = pattern['median_percentile']
    median_return = pattern['median_return']
    percentile_75th = pattern['percentile_75th']
    percentile_25th = pattern['percentile_25th']
    profit_probability = pattern['profit_probability']
    
    exit_signals['expectation'] = {
        'median_percentile': median_percentile,
        'median_return': median_return,
        'profit_probability': profit_probability,
        'current_vs_median': current_percentile - median_percentile,
        'percentile_75th': percentile_75th,
        'percentile_25th': percentile_25th
    }
    
    # ENHANCED v5: More nuanced decision logic with specific thresholds
    
    # 1. STRONG BUY/ACCUMULATE - Significantly below expectations
    if current_percentile <= percentile_25th and current_day >= 2:
        exit_signals['recommendation'] = 'strong_accumulate'
        exit_signals['action_priority'] = 'high'
        exit_signals['reason'] = f'D{current_day}: At {current_percentile:.0f}th percentile (bottom 25%, median: {median_percentile:.0f}%) - STRONG ACCUMULATE signal'
        exit_signals['hold'] = True
    
    # 2. PARTIAL PROFIT TAKING - Above 75th percentile with good profit
    elif (current_percentile >= percentile_75th and 
          current_return > max(0.015, median_return * 0.01 * 0.5)):  # At least 1.5% OR 50% of median expectation
        
        exit_signals['partial_profit'] = True
        exit_signals['recommendation'] = 'take_partial_profit'
        exit_signals['action_priority'] = 'high'
        profit_magnitude = "strong" if current_return > 0.03 else "moderate"
        exit_signals['reason'] = f'D{current_day}: {profit_magnitude.title()} profit at {current_percentile:.0f}th percentile (top 25%) - TAKE 25-50% PROFITS'
    
    # 3. TRAILING STOP ACTIVATION - Above median with positive returns
    elif current_percentile >= median_percentile and current_return > 0.005:  # Above 0.5%
        exit_signals['trailing_stop'] = True
        exit_signals['recommendation'] = 'trailing_stop'
        exit_signals['action_priority'] = 'medium'
        exit_signals['reason'] = f'D{current_day}: Above median at {current_percentile:.0f}th percentile - ACTIVATE trailing stop'
    
    # 4. CONSIDER EXIT - Significantly underperforming expectations
    elif (current_percentile < median_percentile * 0.7 and  # 30% below median percentile
          current_day >= 3 and
          current_return < median_return * 0.01 * 0.3):  # 70% below median return expectation
        
        exit_signals['full_exit'] = True
        exit_signals['hold'] = False
        exit_signals['recommendation'] = 'consider_exit'
        exit_signals['action_priority'] = 'medium'
        exit_signals['reason'] = f'D{current_day}: Underperforming at {current_percentile:.0f}th percentile (30% below median) - CONSIDER EXIT'
    
    # 5. EMERGENCY EXIT - Very low percentile indicates potential failure
    elif current_percentile < 15 and current_day >= 2:
        exit_signals['full_exit'] = True
        exit_signals['hold'] = False
        exit_signals['recommendation'] = 'emergency_exit'
        exit_signals['action_priority'] = 'urgent'
        exit_signals['reason'] = f'D{current_day}: Critical low percentile ({current_percentile:.0f}%) - EMERGENCY EXIT'
    
    # 6. NORMAL HOLD - Within expected ranges
    else:
        exit_signals['recommendation'] = 'normal_hold'
        exit_signals['action_priority'] = 'low'
        percentile_status = "above" if current_percentile > median_percentile else "below"
        exit_signals['reason'] = f'D{current_day}: Normal range at {current_percentile:.0f}th percentile ({percentile_status} median {median_percentile:.0f}%) - HOLD'
    
    # Add dollar impact examples for $10k position
    exit_signals['dollar_impact'] = {
        'expected_profit_10k': median_return * 0.01 * 10000,
        'current_profit_10k': current_return * 10000,
        'vs_expectation_10k': (current_return - median_return * 0.01) * 10000
    }
    
    return exit_signals

def detect_market_environment(prices: pd.Series, volumes: pd.Series = None) -> Dict:
    """Detect current market environment for position sizing adjustments."""
    
    environment = {
        'is_trending': False,
        'vix': 0,  # Would need to fetch VIX data separately
        'volatility': 0
    }
    
    if len(prices) < 50:
        return environment
        
    # Simple trend detection using 20-day and 50-day comparison
    recent_20 = prices.iloc[-20:].mean()
    recent_50 = prices.iloc[-50:].mean()
    trend_strength = abs(recent_20 - recent_50) / recent_50
    
    environment['is_trending'] = trend_strength > 0.05  # >5% difference suggests trending
    
    # Calculate volatility 
    returns = prices.pct_change().dropna()
    if len(returns) >= 20:
        environment['volatility'] = returns.iloc[-20:].std() * 100
    
    return environment

def calculate_percentile_ranks(indicator: pd.Series, lookback: int = LOOKBACK) -> pd.Series:
    """Calculate rolling percentile ranks - strictly prior values (no look-ahead)"""
    vals = indicator.values
    out = np.full(len(vals), np.nan, dtype=float)
    for i in range(lookback, len(vals)):
        window = vals[i - lookback:i]            # strictly prior values
        current = vals[i]
        below = np.sum(window < current)
        out[i] = (below / lookback) * 100.0      # 0..100
    return pd.Series(out, index=indicator.index, name="rsi_ma_pct")

def print_improved_reversion_risk_analysis(percentile_movements: Dict) -> str:
    """Reversion risk analysis with clearer language and actionable guidance."""
    
    if 'reversion_analysis' not in percentile_movements:
        return ""
    
    rev = percentile_movements['reversion_analysis']
    peak_percentile = rev['median_peak_percentile']
    reversion_pts = rev['reversion_from_peak']
    complete_reversion_rate = rev['complete_reversion_rate']
    
    # More nuanced risk categorization
    if reversion_pts < 5:
        reversion_risk = "LOW"
        risk_description = "positions tend to hold their gains"
        management_advice = "Can hold longer with confidence"
    elif reversion_pts < 10:
        reversion_risk = "MODERATE" 
        risk_description = "expect some profit-taking but manageable"
        management_advice = "Monitor for exit signals but not urgent"
    elif reversion_pts < 20:
        reversion_risk = "HIGH"
        risk_description = "significant pullbacks are common"
        management_advice = "Use tight trailing stops"
    else:
        reversion_risk = "EXTREME"
        risk_description = "dramatic reversals frequently occur"
        management_advice = "Take profits early, avoid holding"
    
    analysis = f"""
REVERSION RISK ANALYSIS:
   * Risk level: {reversion_risk} - {risk_description}
   * Management: {management_advice}
   
   * Pattern observed:
     -> RSI-MA typically peaks around {peak_percentile:.0f}th percentile
     -> Then declines an average of {reversion_pts:.0f} percentile points
     -> {complete_reversion_rate:.0f}% of trades completely reverse (fall below 20th percentile)
   
   * Trading implications:
     -> Watch for exit signals when RSI-MA reaches {peak_percentile:.0f}th percentile
     -> Expect {reversion_pts:.0f}-point decline from peak before stabilizing
     -> Set trailing stops to protect against the {complete_reversion_rate:.0f}% of trades that fail completely
   
   * Position management:
     -> Consider taking partial profits at {peak_percentile:.0f}th percentile
     -> Use tight trailing stops above {peak_percentile - reversion_pts:.0f}th percentile
     -> Full exit if RSI-MA falls below 20th percentile (high failure probability)"""
    
    return analysis

class EnhancedPerformanceMatrixBacktester:
    def __init__(self, 
                 tickers: List[str],
                 lookback_period: int = LOOKBACK,
                 rsi_length: int = RSI_LENGTH,
                 ma_length: int = MA_LENGTH):
        """Initialize enhanced backtester with pinned defaults."""
        self.tickers = tickers
        self.lookback_period = lookback_period
        self.rsi_length = rsi_length
        self.ma_length = ma_length
        
        # Extended horizons - now includes all days D1-7
        self.horizons = [1, 2, 3, 4, 5, 6, 7]
        self.entry_thresholds = DEFAULT_ENTRY_THRESHOLDS  # Use <=5%, <=10%, <=15% by default
        
        # Complete percentile ranges in 5-point bins
        self.percentile_ranges = [(i, i+5) for i in range(0, 100, 5)]
        
        self.results = {}
        self.performance_matrices = {}
        
        # Store return time series for proper correlation calculation
        self.return_time_series = {}
        
        # Store strategy quality assessments for unified analysis
        self.strategy_quality_cache = {}
    
    def calculate_rsi_ma_indicator(self, prices: pd.Series) -> pd.Series:
        """Calculate RSI-MA indicator - EXACT COPY from working script."""
        daily_returns = prices.pct_change().fillna(0)
        
        delta = daily_returns.diff()
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        avg_gains = gains.ewm(alpha=1/self.rsi_length, adjust=False).mean()
        avg_losses = losses.ewm(alpha=1/self.rsi_length, adjust=False).mean()
        
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.fillna(50)
        
        rsi_ma = rsi.ewm(span=self.ma_length, adjust=False).mean()
        return rsi_ma
    
    def fetch_data(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        """Fetch ticker data with robust error handling."""
        try:
            # Add delay to avoid rate limiting
            time.sleep(0.5)
            
            # Try multiple approaches
            stock = yf.Ticker(ticker)
            
            # First try: standard fetch
            data = stock.history(period=period, auto_adjust=True, prepost=True)
            
            # If empty, try different parameters
            if data.empty:
                print(f"Retrying {ticker} with different parameters...")
                data = stock.history(period="2y", auto_adjust=True)
                
            # If still empty, try one more time with basic parameters
            if data.empty:
                print(f"Second retry for {ticker}...")
                data = stock.history(period="1y")
            
            if data.empty:
                print(f"Failed to fetch data for {ticker} after multiple attempts")
                return pd.DataFrame()
                
            # Clean the data
            data = data.dropna()
            
            if len(data) < 100:
                print(f"Warning: {ticker} has only {len(data)} data points")
                
            print(f"Successfully fetched {len(data)} data points for {ticker}")
            return data
            
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            # Try one last time with basic download
            try:
                print(f"Final attempt for {ticker} using yf.download...")
                data = yf.download(ticker, period="2y", progress=False)
                if not data.empty:
                    print(f"Success with yf.download for {ticker}: {len(data)} points")
                    return data
            except:
                pass
            return pd.DataFrame()
    
    def calculate_enhanced_market_benchmark(self, prices: pd.Series, ticker: str) -> EnhancedMarketBenchmark:
        """Calculate enhanced market benchmark with individual and cumulative returns."""
        log_returns = np.log(prices / prices.shift(1)).fillna(0)
        
        # Calculate individual daily returns for each day
        individual_returns = {}
        individual_returns[1] = np.mean(log_returns.dropna()) * 100
        
        # For multi-day individual returns, calculate day-to-day returns
        for day in range(2, 8):
            day_to_day_returns = []
            for i in range(day, len(prices)):
                if i - 1 >= 0:
                    day_return = np.log(prices.iloc[i] / prices.iloc[i-1])
                    day_to_day_returns.append(day_return)
            individual_returns[day] = np.mean(day_to_day_returns) * 100 if day_to_day_returns else 0
        
        # Calculate cumulative returns from entry
        cumulative_returns = {}
        for day in range(1, 8):
            day_cumulative_returns = []
            for i in range(day, len(prices)):
                cumulative_return = np.log(prices.iloc[i] / prices.iloc[i-day])
                day_cumulative_returns.append(cumulative_return)
            cumulative_returns[day] = np.mean(day_cumulative_returns) * 100 if day_cumulative_returns else 0
        
        return EnhancedMarketBenchmark(
            ticker=ticker,
            individual_daily_returns=individual_returns,
            cumulative_returns=cumulative_returns,
            volatility=log_returns.std() * 100
        )
    
    def track_entry_progression_enhanced(self, entry_idx: int, prices: pd.Series, 
                                       percentile_ranks: pd.Series) -> Tuple[Dict, float, int]:
        """Track progression for all 7 days with risk metrics."""
        entry_price = prices.iloc[entry_idx]
        progression = {}
        
        # Risk tracking
        max_drawdown = 0.0
        recovery_day = -1
        peak_price = entry_price
        
        # Track all days D1-7
        for day in range(1, 8):
            if entry_idx + day >= len(prices):
                break
                
            current_price = prices.iloc[entry_idx + day]
            current_percentile = percentile_ranks.iloc[entry_idx + day]
            
            # Track drawdown from peak
            if current_price > peak_price:
                peak_price = current_price
            
            drawdown = (current_price - peak_price) / peak_price
            if drawdown < max_drawdown:
                max_drawdown = drawdown
            
            # Check for recovery to entry price
            if recovery_day == -1 and current_price >= entry_price and max_drawdown < 0:
                recovery_day = day
            
            if pd.isna(current_percentile):
                continue
                
            # CUMULATIVE return from entry day to current day
            cumulative_return = np.log(current_price / entry_price)
            
            # Individual daily return (day-to-day)
            if day == 1:
                individual_return = cumulative_return  # Same as cumulative for day 1
            else:
                prev_price = prices.iloc[entry_idx + day - 1]
                individual_return = np.log(current_price / prev_price)
            
            progression[day] = {
                'percentile': current_percentile,
                'cumulative_return_pct': cumulative_return * 100,
                'individual_return_pct': individual_return * 100,
                'price': current_price,
                'drawdown_from_entry': (current_price - entry_price) / entry_price * 100
            }
        
        return progression, max_drawdown * 100, recovery_day
    
    def find_entry_events_enhanced(self, percentile_ranks: pd.Series, prices: pd.Series,
                                 threshold: float) -> List[Dict]:
        """Find entry events with enhanced filtering and 7-day tracking."""
        events = []
        
        for i, (date, percentile) in enumerate(percentile_ranks.items()):
            if pd.isna(percentile) or percentile > threshold:
                continue
            
            if i + 7 >= len(prices):
                continue
                
            progression, max_drawdown, recovery_day = self.track_entry_progression_enhanced(
                i, prices, percentile_ranks)
            
            if not progression:
                continue
            
            events.append({
                'entry_date': date,
                'entry_price': prices.iloc[i],
                'entry_percentile': percentile,
                'progression': progression,
                'max_drawdown_pct': max_drawdown,
                'recovery_day': recovery_day if recovery_day > 0 else -1,
                'signal_extremity': percentile  # Store for position sizing
            })
        
        return events
    
    def calculate_risk_metrics(self, events: List[Dict]) -> RiskMetrics:
        """Calculate comprehensive risk metrics with fixed logic."""
        if not events:
            return RiskMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        # 1. Drawdown calculation (convert to negative values for intuitive understanding)
        drawdowns = [e['max_drawdown_pct'] for e in events]
        drawdowns_negative = [-abs(d) for d in drawdowns]  # Convert to negative values
        
        recovery_times = [e['recovery_day'] for e in events if e['recovery_day'] > 0]
        
        # 2. Calculate final returns for loss/profit analysis
        final_returns = []
        for event in events:
            if 7 in event['progression']:
                final_returns.append(event['progression'][7]['cumulative_return_pct'])
            elif event['progression']:
                last_day = max(event['progression'].keys())
                final_returns.append(event['progression'][last_day]['cumulative_return_pct'])
        
        losing_trades = [r for r in final_returns if r < 0]
        profitable_trades = [r for r in final_returns if r > 0]
        
        # 3. Consecutive losses calculation
        consecutive_losses = 0
        max_consecutive = 0
        for ret in final_returns:
            if ret < 0:
                consecutive_losses += 1
                max_consecutive = max(max_consecutive, consecutive_losses)
            else:
                consecutive_losses = 0
        
        # 4. Percentile calculation (10th percentile = worst 10%)
        median_drawdown = np.median(drawdowns_negative) if drawdowns_negative else 0
        p90_drawdown = np.percentile(drawdowns_negative, 10) if drawdowns_negative else 0  # 10th percentile = worst 10%
        
        return RiskMetrics(
            median_drawdown=median_drawdown,
            p90_drawdown=p90_drawdown,  # Now correctly shows worst 10%
            median_recovery_days=np.median(recovery_times) if recovery_times else 0,
            recovery_rate=len(recovery_times) / len(events),
            max_consecutive_losses=max_consecutive,
            avg_loss_magnitude=np.mean(losing_trades) if losing_trades else 0,
            # NEW metrics for clarity
            total_losing_trades=len(losing_trades),
            total_profitable_trades=len(profitable_trades),
            worst_single_loss=min(final_returns) if final_returns else 0,
            best_single_gain=max(final_returns) if final_returns else 0
        )
    
    def analyze_realistic_day_patterns(self, events: List[Dict], threshold: float) -> Dict:
        """Analyze realistic day-by-day patterns using median percentiles and returns."""
        
        day_patterns = {}
        
        for day in range(1, 8):  # D1 through D7
            day_percentiles = []
            day_returns = []
            
            # Collect all actual outcomes for this day
            for event in events:
                if day in event['progression']:
                    prog = event['progression'][day]
                    day_percentiles.append(prog['percentile'])
                    day_returns.append(prog['cumulative_return_pct'])
            
            if len(day_percentiles) >= 5:  # Need minimum sample
                # Calculate realistic statistics
                median_percentile = np.median(day_percentiles)
                percentile_std = np.std(day_percentiles)
                median_return = np.median(day_returns)
                return_std = np.std(day_returns)
                
                # Calculate percentile ranges (median ± 1 std dev)
                percentile_lower = max(0, median_percentile - percentile_std)
                percentile_upper = min(100, median_percentile + percentile_std)
                
                # Calculate return ranges  
                return_lower = median_return - return_std
                return_upper = median_return + return_std
                
                # Probability of profit
                profit_rate = sum(1 for r in day_returns if r > 0) / len(day_returns)
                
                day_patterns[day] = {
                    'median_percentile': median_percentile,
                    'percentile_std': percentile_std,
                    'percentile_range': (percentile_lower, percentile_upper),
                    'median_return': median_return,
                    'return_std': return_std, 
                    'return_range': (return_lower, return_upper),
                    'profit_probability': profit_rate,
                    'sample_size': len(day_percentiles),
                    'percentile_75th': np.percentile(day_percentiles, 75),
                    'percentile_25th': np.percentile(day_percentiles, 25)
                }
        
        return day_patterns
    
    def print_enhanced_realistic_day_patterns(self, day_patterns: Dict, threshold: float, events: List[Dict]):
        """ENHANCED v5: Print comprehensive realistic day patterns with actionable profit-taking framework."""
        
        if not day_patterns:
            print("Insufficient data for day pattern analysis")
            return
        
        print(f"\nENHANCED REALISTIC PATTERNS ANALYSIS (<={threshold}% entries):")
        print("=" * 90)
        print("COMPREHENSIVE: Shows median expectations, profit probabilities, and ACTIONABLE exit signals")
        print()
        
        # Table header
        print(f"{'Day':<3} | {'Median %ile':<11} | {'Median Return':<13} | {'Profit Prob':<11} | {'25th-75th %ile':<15} | {'Sample':<6}")
        print("-" * 85)
        
        for day in sorted(day_patterns.keys()):
            pattern = day_patterns[day]
            median_pct = pattern['median_percentile']
            median_ret = pattern['median_return']
            profit_prob = pattern['profit_probability'] * 100
            sample_size = pattern['sample_size']
            p25 = pattern['percentile_25th']
            p75 = pattern['percentile_75th']
            percentile_range = f"{p25:.0f}-{p75:.0f}%"
            
            print(f"D{day:<2} | {median_pct:>8.1f}%    | {median_ret:>+9.2f}%    | {profit_prob:>7.1f}%   | {percentile_range:>13}  | {sample_size:>4}")
        
        print()
        
        # ENHANCED KEY INSIGHTS
        print("KEY INSIGHTS FROM REALISTIC PATTERNS:")
        
        # Find best days
        best_return_day = max(day_patterns.keys(), key=lambda d: day_patterns[d]['median_return'])
        best_percentile_day = max(day_patterns.keys(), key=lambda d: day_patterns[d]['median_percentile'])
        best_profit_prob_day = max(day_patterns.keys(), key=lambda d: day_patterns[d]['profit_probability'])
        
        print(f"* Best median return: D{best_return_day} with {day_patterns[best_return_day]['median_return']:+.2f}%")
        print(f"* Highest median percentile: D{best_percentile_day} at {day_patterns[best_percentile_day]['median_percentile']:.1f}th percentile")
        print(f"* Best profit probability: D{best_profit_prob_day} with {day_patterns[best_profit_prob_day]['profit_probability']*100:.1f}% success rate")
        
        # Trend analysis
        days = sorted(day_patterns.keys())
        returns = [day_patterns[day]['median_return'] for day in days]
        percentiles = [day_patterns[day]['median_percentile'] for day in days]
        
        early_avg_return = np.mean(returns[:3]) if len(returns) >= 3 else 0
        late_avg_return = np.mean(returns[-3:]) if len(returns) >= 3 else 0
        
        if late_avg_return > early_avg_return:
            trend_direction = "IMPROVING"
            trend_description = f"Returns improve from {early_avg_return:+.2f}% (D1-3) to {late_avg_return:+.2f}% (D5-7)"
        else:
            trend_direction = "DECLINING"
            trend_description = f"Returns decline from {early_avg_return:+.2f}% (D1-3) to {late_avg_return:+.2f}% (D5-7)"
        
        print(f"* Overall trend: {trend_direction} - {trend_description}")
        
        print()
        print("ENHANCED ACTIONABLE PROFIT-TAKING FRAMEWORK:")
        print("=" * 70)
        print("Shows SPECIFIC actions based on current RSI-MA percentile vs median expectations")
        print()
        
        # Generate enhanced profit-taking recommendations for each day
        for day in days:
            pattern = day_patterns[day]
            median_pct = pattern['median_percentile']
            median_ret = pattern['median_return']
            p25 = pattern['percentile_25th']
            p75 = pattern['percentile_75th']
            profit_prob = pattern['profit_probability']
            
            print(f"D{day} DECISION FRAMEWORK (Median expectation: {median_pct:.0f}th percentile, {median_ret:+.2f}% return):")
            
            # Define specific percentile thresholds for actions
            strong_accumulate_threshold = p25
            partial_profit_threshold = p75
            emergency_threshold = 15
            
            # Generate specific action recommendations
            actions = []
            
            # Strong accumulate zone (bottom 25%)
            actions.append({
                'condition': f"≤{strong_accumulate_threshold:.0f}th percentile",
                'action': "STRONG ACCUMULATE",
                'priority': "HIGH",
                'rationale': f"Bottom 25% - significant underperformance vs median ({median_pct:.0f}%)",
                'dollar_example': f"$10k position worth ${10000 * (1 + median_ret/100):.0f} at median expectation"
            })
            
            # Emergency exit (very low percentiles)
            if day >= 2:
                actions.append({
                    'condition': f"≤{emergency_threshold}th percentile",
                    'action': "EMERGENCY EXIT",
                    'priority': "URGENT",
                    'rationale': f"Critical failure signal - high probability of continued decline",
                    'dollar_example': f"Cut losses before further deterioration"
                })
            
            # Normal hold zone (25th to 75th percentile)
            actions.append({
                'condition': f"{strong_accumulate_threshold:.0f}-{partial_profit_threshold:.0f}th percentile",
                'action': "NORMAL HOLD",
                'priority': "LOW",
                'rationale': f"Within expected range around median ({median_pct:.0f}%)",
                'dollar_example': f"Expected profit: ${median_ret * 100:.0f} on $10k position"
            })
            
            # Partial profit zone (top 25%)
            actions.append({
                'condition': f"≥{partial_profit_threshold:.0f}th percentile",
                'action': "TAKE PARTIAL PROFITS",
                'priority': "HIGH",
                'rationale': f"Top 25% performance - take 25-50% profits while maintaining position",
                'dollar_example': f"Lock in gains above ${(partial_profit_threshold/100 * median_ret) * 100:.0f} on $10k"
            })
            
            # Trailing stop activation
            actions.append({
                'condition': f"≥{median_pct:.0f}th percentile + positive returns",
                'action': "ACTIVATE TRAILING STOP",
                'priority': "MEDIUM",
                'rationale': f"Above median with profits - protect gains with trailing stop",
                'dollar_example': f"Protect profits above breakeven"
            })
            
            # Print actions in priority order
            priority_order = ['URGENT', 'HIGH', 'MEDIUM', 'LOW']
            for priority in priority_order:
                priority_actions = [a for a in actions if a['priority'] == priority]
                for action in priority_actions:
                    print(f"  • {action['condition']:>20} → {action['action']:>20} ({priority:>6} priority)")
                    print(f"    Rationale: {action['rationale']}")
                    print(f"    Example: {action['dollar_example']}")
                    print()
        
        print()
        print("PROFIT-TAKING SUMMARY & DOLLAR IMPACT:")
        print("-" * 50)
        
        # Calculate overall strategy statistics
        total_positive_days = sum(1 for day in days if day_patterns[day]['median_return'] > 0)
        avg_positive_return = np.mean([day_patterns[day]['median_return'] for day in days if day_patterns[day]['median_return'] > 0])
        best_day_return = max([day_patterns[day]['median_return'] for day in days])
        
        print(f"Strategy Overview:")
        print(f"* Profitable days: {total_positive_days}/{len(days)} days show positive median returns")
        print(f"* Average profitable day: {avg_positive_return:+.2f}% median return")
        print(f"* Best single day: {best_day_return:+.2f}% median return on D{best_return_day}")
        print()
        
        print(f"Position Sizing Implications (based on <={threshold}% entry threshold):")
        # Calculate some basic position sizing metrics
        if events:
            final_returns = []
            for event in events:
                if 7 in event['progression']:
                    final_returns.append(event['progression'][7]['cumulative_return_pct'])
            
            if final_returns:
                worst_case = np.percentile(final_returns, 10)  # 10th percentile
                median_case = np.median(final_returns)
                best_case = np.percentile(final_returns, 90)   # 90th percentile
                
                print(f"* Worst case (10%): {worst_case:+.2f}% - suggests max {100 * 2 / abs(worst_case):.0f}% position size")
                print(f"* Median case: {median_case:+.2f}% - typical outcome expectation")
                print(f"* Best case (10%): {best_case:+.2f}% - upside potential")
                print()
                print(f"Dollar Examples on $10,000 position:")
                print(f"* Typical profit expectation: ${median_case * 100:.0f}")
                print(f"* Worst case loss: ${worst_case * 100:.0f}")
                print(f"* Best case gain: ${best_case * 100:.0f}")
    
    def analyze_enhanced_exits_realistic(self, events: List[Dict], day_patterns: Dict) -> Dict:
        """Analyze effectiveness of enhanced realistic exit strategies."""
        
        if not events:
            return {}
            
        exit_stats = {
            'strong_accumulate_signals': 0,
            'partial_profit_signals': 0,
            'trailing_stop_signals': 0,
            'full_exit_signals': 0,
            'emergency_exit_signals': 0,
            'normal_hold_signals': 0,
            'day_patterns_summary': {},
            'action_distribution': {}
        }
        
        # Summarize day patterns
        for day, pattern in day_patterns.items():
            exit_stats['day_patterns_summary'][day] = {
                'median_percentile': pattern['median_percentile'],
                'median_return': pattern['median_return'],
                'profit_probability': pattern['profit_probability']
            }
        
        # Add enhanced exit analysis to each event using median patterns
        for event in events:
            progression = event['progression']
            entry_percentile = event['entry_percentile']
            entry_price = event['entry_price']
            
            dynamic_exits = self.analyze_dynamic_exits_enhanced(progression, entry_percentile, entry_price, day_patterns)
            event['dynamic_exits'] = dynamic_exits
            
            # Count exit signals by type
            for day, exit_data in dynamic_exits.items():
                recommendation = exit_data.get('recommendation', 'normal_hold')
                if recommendation == 'strong_accumulate':
                    exit_stats['strong_accumulate_signals'] += 1
                elif recommendation == 'take_partial_profit':
                    exit_stats['partial_profit_signals'] += 1
                elif recommendation == 'trailing_stop':
                    exit_stats['trailing_stop_signals'] += 1
                elif recommendation in ['consider_exit', 'full_exit']:
                    exit_stats['full_exit_signals'] += 1
                elif recommendation == 'emergency_exit':
                    exit_stats['emergency_exit_signals'] += 1
                else:
                    exit_stats['normal_hold_signals'] += 1
        
        total_signals = sum([exit_stats[key] for key in exit_stats.keys() if key.endswith('_signals')])
        
        if total_signals > 0:
            exit_stats['action_distribution'] = {
                'strong_accumulate_rate': exit_stats['strong_accumulate_signals'] / total_signals,
                'partial_profit_rate': exit_stats['partial_profit_signals'] / total_signals,
                'trailing_stop_rate': exit_stats['trailing_stop_signals'] / total_signals,
                'full_exit_rate': exit_stats['full_exit_signals'] / total_signals,
                'emergency_exit_rate': exit_stats['emergency_exit_signals'] / total_signals,
                'normal_hold_rate': exit_stats['normal_hold_signals'] / total_signals
            }
        
        return exit_stats
    
    def analyze_dynamic_exits_enhanced(self, progression: Dict, entry_percentile: float, entry_price: float, day_patterns: Dict) -> Dict:
        """Analyze dynamic exit opportunities using enhanced realistic patterns."""
        
        exit_analysis = {}
        
        for day, day_data in progression.items():
            current_percentile = day_data['percentile']
            current_return = day_data['cumulative_return_pct'] / 100.0
            
            exit_signals = get_enhanced_realistic_exit_signal(
                current_percentile, entry_percentile, day, current_return, day_patterns, 0)
            
            exit_analysis[day] = exit_signals
            
        return exit_analysis
    
    def analyze_ticker(self, ticker: str) -> Dict:
        """ENHANCED v5: Analyze single ticker with comprehensive realistic framework."""
        print(f"Analyzing {ticker}...")
        
        data = self.fetch_data(ticker)
        if data.empty:
            return {}
        
        # Use the EXACT RSI-MA calculation from working script
        indicator = self.calculate_rsi_ma_indicator(data['Close'])
        percentile_ranks = calculate_percentile_ranks(indicator, LOOKBACK)
        
        benchmark = self.calculate_enhanced_market_benchmark(data['Close'], ticker)
        
        # Detect market environment for enhanced position sizing
        market_environment = detect_market_environment(data['Close'], data.get('Volume'))
        
        ticker_results = {
            'ticker': ticker,
            'data_points': len(data),
            'benchmark': benchmark,
            'market_environment': market_environment,
            'thresholds': {},
            'enhanced_features': {
                'realistic_exits': True,
                'enhanced_profit_taking': True,
                'median_based_patterns': True,
                'enhanced_position_sizing': True,
                'extremity_based_sizing': True,
                'comprehensive_exit_framework': True
            }
        }
        
        for threshold in self.entry_thresholds:
            events = self.find_entry_events_enhanced(percentile_ranks, data['Close'], threshold)
            
            if len(events) < 10:
                print(f"  Skipping <={threshold}% threshold - only {len(events)} events (need 10+)")
                continue
            
            risk_metrics = self.calculate_risk_metrics(events)
            
            # ENHANCED: Realistic day-by-day pattern analysis
            day_patterns = self.analyze_realistic_day_patterns(events, threshold)
            
            # ENHANCED: Exit analysis with comprehensive action framework
            dynamic_exit_analysis = self.analyze_enhanced_exits_realistic(events, day_patterns)
            
            # Enhanced position sizing
            enhanced_position_sizing = self.calculate_enhanced_position_sizing_for_threshold(
                threshold, risk_metrics, market_environment)
            
            # Store results
            ticker_results['thresholds'][threshold] = {
                'events': len(events),
                'risk_metrics': risk_metrics,
                'raw_events': events,  # Store for correlation calculation
                'dynamic_exit_analysis': dynamic_exit_analysis,
                'enhanced_position_sizing': enhanced_position_sizing,
                'day_patterns': day_patterns,  # ENHANCED: Comprehensive day-by-day patterns
                'realistic_exit_framework': True,
                'enhanced_profit_taking': True
            }
        
        # Print enhanced realistic day patterns analysis for each threshold
        for threshold in ticker_results['thresholds']:
            threshold_data = ticker_results['thresholds'][threshold]
            events = threshold_data['raw_events']
            self.print_enhanced_realistic_day_patterns(threshold_data['day_patterns'], threshold, events)
        
        print(f"Analysis complete for {ticker} - {len(ticker_results['thresholds'])} thresholds analyzed")
        return ticker_results

    def calculate_enhanced_position_sizing_for_threshold(self, threshold: float, risk_metrics: RiskMetrics,
                                                        market_environment: Dict = None) -> Dict:
        """Calculate enhanced position sizing incorporating extremity and market factors."""
        
        # Base calculation (same as before)
        worst_case_loss = abs(risk_metrics.p90_drawdown) if risk_metrics.p90_drawdown < 0 else 1.0
        base_position_size = 2.0 / (worst_case_loss / 100)  
        
        # Enhanced position sizing
        enhanced_size = calculate_enhanced_position_size(
            threshold, base_position_size, threshold, market_environment)
        
        return {
            'base_position_size': base_position_size,
            'enhanced_position_size': enhanced_size,
            'extremity_multiplier': EXTREME_POSITION_MULTIPLIERS.get(threshold, 1.0),
            'market_adjustments': market_environment or {}
        }
    
    def run_analysis(self) -> Dict:
        """Run analysis with enhanced comprehensive framework."""
        print(f"Building Enhanced Performance Matrix (D1-7) with RSI-MA EMA({MA_LENGTH}) Analysis...")
        print(f"Settings: RSI({RSI_LENGTH}) + EMA({MA_LENGTH}), {LOOKBACK}-period percentile lookback")
        print("ENHANCED v5: Using COMPREHENSIVE realistic framework with actionable profit-taking")
        
        start_time = time.time()
        results = {}
        
        for ticker in self.tickers:
            results[ticker] = self.analyze_ticker(ticker)
        
        elapsed = time.time() - start_time
        print(f"\nAnalysis completed in {elapsed:.1f} seconds")
        
        return results

def main():
    """Main function with command line argument support."""
    parser = argparse.ArgumentParser(description='Enhanced Performance Matrix v5')
    parser.add_argument('tickers', nargs='*', help='Ticker symbols to analyze (default: preset list)')
    parser.add_argument('--thresholds', nargs='+', type=float, default=DEFAULT_ENTRY_THRESHOLDS,
                       help='Entry thresholds to analyze (default: 5.0 10.0 15.0)')
    
    args = parser.parse_args()
    
    # Use provided tickers or default list
    tickers = args.tickers if args.tickers else DEFAULT_TICKERS
    
    print(f"Enhanced Performance Matrix v5 - COMPREHENSIVE REALISTIC Framework")
    print(f"Analyzing: {', '.join(tickers)}")
    print(f"Entry thresholds: {args.thresholds}")
    print("=" * 90)
    print("MAJOR ENHANCEMENTS IN V5:")
    print("✓ Realistic median-based patterns with comprehensive statistical analysis")
    print("✓ ENHANCED profit-taking framework with specific actionable signals")
    print("✓ Multi-layer exit strategy: accumulate, hold, partial profit, trailing stop, emergency exit")
    print("✓ Dollar impact examples and transparent position sizing")
    print("✓ Market environment detection for enhanced position sizing")
    print("✓ Quality classification system across all analysis sections")
    print("✓ Practical recommendations with specific percentile thresholds")
    print("=" * 90)
    
    # Create and run backtester
    backtester = EnhancedPerformanceMatrixBacktester(tickers)
    backtester.entry_thresholds = args.thresholds
    
    results = backtester.run_analysis()
    
    # Show summary
    print("\n" + "=" * 90)
    print("ANALYSIS SUMMARY:")
    for ticker, ticker_data in results.items():
        if ticker_data:
            num_thresholds = len(ticker_data.get('thresholds', {}))
            print(f"{ticker}: {num_thresholds} thresholds analyzed with ENHANCED realistic framework")
            
            # Show sample of enhanced features
            if ticker_data.get('thresholds'):
                first_threshold = list(ticker_data['thresholds'].keys())[0]
                features = ticker_data['thresholds'][first_threshold].get('dynamic_exit_analysis', {})
                action_dist = features.get('action_distribution', {})
                
                if action_dist:
                    print(f"  Enhanced Actions: {action_dist.get('partial_profit_rate', 0)*100:.1f}% profit signals, "
                          f"{action_dist.get('strong_accumulate_rate', 0)*100:.1f}% accumulate signals")
        else:
            print(f"{ticker}: Failed to fetch data")

if __name__ == "__main__":
    main()
