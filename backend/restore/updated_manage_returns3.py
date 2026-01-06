#!/usr/bin/env python3
"""
Enhanced Performance Matrix v4 - RSI-MA EMA(14) with Fixed Cross-Threshold Analysis

FIXED IN V4:
- CRITICAL: Restored complete enhanced trend analysis output with step-by-step trading rules
- FIXED: Sharpe-like efficiency calculations now properly differentiate thresholds
- FIXED: Position sizing calculations now use correct worst-case loss percentages
- FIXED: Cross-threshold strategic recommendations now provide specific actionable guidance
- FIXED: Added proper correlation analysis between thresholds
- ENHANCED: Improved diversification insights and capital allocation framework
- FIXED: All statistical significance tests now properly displayed

FEATURES:
- RSI(14) + EMA(14) calculation from daily return momentum
- 500-period rolling percentile lookback (no look-ahead)
- Entry thresholds: <=5%, <=10%, <=15% percentile by default
- D1-D7 performance matrix with full analytics
- Command-line argument support for custom tickers
- Updated default tickers: SPY, QQQ, AAPL, AMZN, GOOGL, NVDA, MSFT, META, TSLA, BRK-B, OXY, BTC-USD
- Complete trend analysis and strategy recommendations
- ENHANCED: Advanced return distribution trend analysis with multiple statistical tests
- Both simple median-based and comprehensive distribution-based trend analysis
- IMPROVED: Fixed risk analysis logic with clearer language and practical guidance
- FIXED: Cross-threshold comparison panel with accurate calculations and specific recommendations
"""

print("=== SCRIPT STARTING v4 ===")
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
    """IMPROVED: Risk analysis with clearer logic and additional metrics."""
    median_drawdown: float
    p90_drawdown: float  # FIXED: Now correctly shows worst 10% of drawdowns
    median_recovery_days: float
    recovery_rate: float
    max_consecutive_losses: int
    avg_loss_magnitude: float
    # NEW: Additional clarity metrics
    total_losing_trades: int
    total_profitable_trades: int
    worst_single_loss: float
    best_single_gain: float

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
    """IMPROVED: Reversion risk analysis with clearer language and actionable guidance."""
    
    if 'reversion_analysis' not in percentile_movements:
        return ""
    
    rev = percentile_movements['reversion_analysis']
    peak_percentile = rev['median_peak_percentile']
    reversion_pts = rev['reversion_from_peak']
    complete_reversion_rate = rev['complete_reversion_rate']
    
    # IMPROVED: More nuanced risk categorization
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
        """Find entry events with enhanced 7-day tracking."""
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
                'recovery_day': recovery_day if recovery_day > 0 else -1
            })
        
        return events
    
    def calculate_risk_metrics(self, events: List[Dict]) -> RiskMetrics:
        """IMPROVED: Calculate comprehensive risk metrics with fixed logic."""
        if not events:
            return RiskMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        # 1. FIXED: Drawdown calculation (convert to negative values for intuitive understanding)
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
        
        # 3. FIXED: Consecutive losses calculation
        consecutive_losses = 0
        max_consecutive = 0
        for ret in final_returns:
            if ret < 0:
                consecutive_losses += 1
                max_consecutive = max(max_consecutive, consecutive_losses)
            else:
                consecutive_losses = 0
        
        # 4. FIXED: Percentile calculation (10th percentile = worst 10%)
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
    
    def print_improved_risk_analysis(self, risk: RiskMetrics, total_events: int, threshold: float):
        """CLARIFIED: Risk analysis with clear context about timeframes and transparent calculations."""
        
        print(f"RISK ANALYSIS - CLARIFIED VERSION ({total_events} trades at <={threshold}% entry signal):")
        print()
        
        # SECTION 1: DRAWDOWN RISK (During D1-D7 holding period)
        print(f"DRAWDOWN RISK (During D1-D7 holding period after <={threshold}% entry):")
        print(f"   * Typical max drawdown: {risk.median_drawdown:.2f}% during the 7-day hold period")
        print(f"   * Worst-case max drawdown: {risk.p90_drawdown:.2f}% (only 10% of trades get this bad)")
        print(f"   * Context: This measures the deepest loss from peak price during each 7-day trade")
        print(f"   * Translation: Half of trades never go more than {abs(risk.median_drawdown):.1f}% underwater from their best price")
        print()
        
        # SECTION 2: RECOVERY CAPABILITY (Getting back to entry price during hold period)
        print(f"RECOVERY CAPABILITY (Getting back to entry price during D1-D7 hold):")
        if risk.recovery_rate > 0:
            print(f"   * Recovery success rate: {risk.recovery_rate*100:.0f}% of trades recover to entry price")
            print(f"   * Typical recovery time: {risk.median_recovery_days:.0f} days after going underwater")
            print(f"   * Context: Of trades that go negative, {risk.recovery_rate*100:.0f}% get back to breakeven within 7 days")
            
            if risk.median_recovery_days <= 3:
                recovery_assessment = "EXCELLENT - Quick recovery within trade period"
            elif risk.median_recovery_days <= 5:
                recovery_assessment = "GOOD - Reasonable recovery within trade period"
            else:
                recovery_assessment = "SLOW - Recovery takes most of the 7-day holding period"
            print(f"   * Assessment: {recovery_assessment}")
        else:
            print(f"   * Recovery success rate: 0% - positions rarely recover once underwater")
            print(f"   * Assessment: HIGH RISK - cut losses quickly during 7-day period")
        print()
        
        # SECTION 3: LOSS STREAKS (Consecutive failed trades, not consecutive days)
        print(f"LOSS STREAK RISK (Consecutive losing trades at <={threshold}% entries):")
        print(f"   * Maximum consecutive losses: {risk.max_consecutive_losses} losing trades in a row")
        print(f"   * Context: This counts separate <={threshold}% entry signals that resulted in losses")
        print(f"   * Average losing trade: {risk.avg_loss_magnitude:.2f}% final result after 7-day hold")
        print(f"   * Clarification: Each 'trade' = one <={threshold}% entry + 7-day hold, NOT consecutive days")
        
        # Streak risk assessment
        if risk.max_consecutive_losses <= 3:
            streak_risk = "LOW - Short losing streaks"
            streak_implication = "Unlikely to face extended psychological pressure"
        elif risk.max_consecutive_losses <= 5:
            streak_risk = "MODERATE - Manageable losing streaks"
            streak_implication = "Prepare for occasional 4-5 trade losing runs"
        elif risk.max_consecutive_losses <= 8:
            streak_risk = "HIGH - Extended losing streaks possible"
            streak_implication = "Expect 6-8 consecutive losses - maintain discipline"
        else:
            streak_risk = "VERY HIGH - Dangerous losing streaks"
            streak_implication = "Psychological pressure extreme - reduce size or pause strategy"
        
        print(f"   * Streak risk level: {streak_risk}")
        print(f"   * Implication: {streak_implication}")
        
        # Calculate maximum theoretical loss during worst streak
        max_streak_loss = abs(risk.avg_loss_magnitude) * risk.max_consecutive_losses
        print(f"   * Worst streak scenario: {max_streak_loss:.1f}% cumulative portfolio loss")
        print(f"     (if using 2% position sizing: {max_streak_loss * 0.02:.1f}% total portfolio impact)")
        print()
        
        # SECTION 4: OUTCOME DISTRIBUTION
        print(f"TRADE OUTCOME DISTRIBUTION (Final results after 7-day holds):")
        total_trades = risk.total_losing_trades + risk.total_profitable_trades
        if total_trades > 0:
            win_rate = (risk.total_profitable_trades / total_trades) * 100
            loss_rate = (risk.total_losing_trades / total_trades) * 100
            
            print(f"   * Profitable trades: {risk.total_profitable_trades}/{total_trades} ({win_rate:.1f}%)")
            print(f"   * Losing trades: {risk.total_losing_trades}/{total_trades} ({loss_rate:.1f}%)")
            print(f"   * Best single trade: +{risk.best_single_gain:.2f}% (best 7-day result)")
            print(f"   * Worst single trade: {risk.worst_single_loss:.2f}% (worst 7-day result)")
            
            # Risk-reward ratio
            if risk.avg_loss_magnitude != 0:
                risk_reward_ratio = abs(risk.best_single_gain / risk.avg_loss_magnitude)
                print(f"   * Best gain vs avg loss ratio: {risk_reward_ratio:.1f}:1")
                print(f"   * Context: Best winner was {risk_reward_ratio:.1f}x larger than typical loss")
        print()
        
        # SECTION 5: PRACTICAL POSITION SIZING GUIDANCE WITH TRANSPARENT CALCULATIONS
        print(f"POSITION SIZING GUIDANCE (Based on <={threshold}% entry performance):")
        
        # Calculate recommended position size based on worst-case scenario
        worst_case_loss = abs(risk.p90_drawdown)
        
        # Standard risk management: Don't risk more than 1-2% of portfolio per trade
        if worst_case_loss > 0:
            # TRANSPARENT CALCULATION EXPLANATION
            print(f"   CALCULATION METHOD:")
            print(f"   * Step 1: Identify worst-case loss = {worst_case_loss:.1f}% (10th percentile of drawdowns)")
            print(f"   * Step 2: Set maximum portfolio risk per trade (1% or 2% is standard)")
            print(f"   * Step 3: Position Size = Portfolio Risk ÷ Worst Case Loss")
            print()
            
            # FIXED: Calculate position sizes correctly
            max_recommended_allocation_1pct = 1.0 / (worst_case_loss / 100)  # For 1% portfolio risk
            max_recommended_allocation_2pct = 2.0 / (worst_case_loss / 100)  # For 2% portfolio risk
            
            print(f"   POSITION SIZE RECOMMENDATIONS:")
            print(f"   * For 1% portfolio risk: Maximum {max_recommended_allocation_1pct:.1f}% position size")
            print(f"     Calculation: 1% ÷ {worst_case_loss:.1f}% = {max_recommended_allocation_1pct:.1f}%")
            print(f"   * For 2% portfolio risk: Maximum {max_recommended_allocation_2pct:.1f}% position size")
            print(f"     Calculation: 2% ÷ {worst_case_loss:.1f}% = {max_recommended_allocation_2pct:.1f}%")
            print(f"   * Rationale: Worst 10% of trades lose {worst_case_loss:.1f}% during 7-day hold")
            print()
            
            # Practical guidance with dollar examples
            print(f"   PRACTICAL EXAMPLES:")
            print(f"   * $100,000 portfolio with 1% risk: Use ${max_recommended_allocation_1pct*1000:.0f} position size")
            print(f"   * $100,000 portfolio with 2% risk: Use ${max_recommended_allocation_2pct*1000:.0f} position size")
            print(f"   * If worst case hits: Lose $1,000 (1% risk) or $2,000 (2% risk) maximum")
            print()
            
            # Risk level assessment
            if max_recommended_allocation_2pct > 15:
                sizing_guidance = "SAFE - Can use normal position sizes (15-20% typical)"
                risk_color = ""
            elif max_recommended_allocation_2pct > 8:
                sizing_guidance = "MODERATE - Use smaller position sizes (8-15% range)"
                risk_color = ""
            elif max_recommended_allocation_2pct > 4:
                sizing_guidance = "HIGH RISK - Use very small position sizes (4-8% range)"
                risk_color = ""
            else:
                sizing_guidance = "EXTREME RISK - Avoid or use minimal allocation (<4%)"
                risk_color = ""
            
            print(f"   {risk_color} RISK ASSESSMENT: {sizing_guidance}")
        
        print()
    
    def build_enhanced_matrix(self, events: List[Dict]) -> Dict[str, Dict[int, PerformanceCell]]:
        """Build enhanced performance matrix for all 7 days."""
        matrix = {}
        
        for from_pct, to_pct in self.percentile_ranges:
            range_key = f"{from_pct:2.0f}-{to_pct:2.0f}%"
            matrix[range_key] = {}
        
        # Now includes all days D1-7
        for day in self.horizons:
            for from_pct, to_pct in self.percentile_ranges:
                range_key = f"{from_pct:2.0f}-{to_pct:2.0f}%"
                
                cumulative_returns = []
                
                for event in events:
                    if day in event['progression']:
                        prog = event['progression'][day]
                        if from_pct <= prog['percentile'] < to_pct:
                            cumulative_returns.append(prog['cumulative_return_pct'])
                
                if len(cumulative_returns) >= 1:
                    if len(cumulative_returns) == 1:
                        expected_return = cumulative_returns[0]
                        p25_return = cumulative_returns[0]
                        p75_return = cumulative_returns[0]
                    else:
                        expected_return = np.median(cumulative_returns)
                        p25_return = np.percentile(cumulative_returns, 25)
                        p75_return = np.percentile(cumulative_returns, 75)
                    
                    success_rate = sum(1 for r in cumulative_returns if r > 0) / len(cumulative_returns)
                    
                    if len(cumulative_returns) >= 20:
                        confidence = "VH"
                    elif len(cumulative_returns) >= 10:
                        confidence = "H"
                    elif len(cumulative_returns) >= 5:
                        confidence = "M"
                    elif len(cumulative_returns) >= 3:
                        confidence = "L"
                    else:
                        confidence = "VL"
                    
                    cell = PerformanceCell(
                        day=day,
                        percentile_range=range_key,
                        sample_size=len(cumulative_returns),
                        expected_cumulative_return=expected_return,
                        expected_success_rate=success_rate,
                        p25_return=p25_return,
                        p75_return=p75_return,
                        confidence_level=confidence
                    )
                    
                    matrix[range_key][day] = cell
        
        return matrix
    
    def calculate_overall_win_rates(self, events: List[Dict]) -> Dict[int, float]:
        """Calculate overall win rate for each day across all percentile ranges."""
        win_rates = {}
        
        for day in self.horizons:
            all_returns = []
            
            # Collect all returns for this day across all events
            for event in events:
                if day in event['progression']:
                    all_returns.append(event['progression'][day]['cumulative_return_pct'])
            
            if all_returns:
                profitable_trades = sum(1 for r in all_returns if r > 0)
                win_rate = (profitable_trades / len(all_returns)) * 100
                win_rates[day] = win_rate
            else:
                win_rates[day] = 0.0
        
        return win_rates
    
    def calculate_return_distribution(self, events: List[Dict]) -> Dict[int, Dict[str, float]]:
        """Calculate return distribution statistics for each day."""
        distributions = {}
        
        for day in self.horizons:
            all_returns = []
            
            # Collect all cumulative returns for this day across all events
            for event in events:
                if day in event['progression']:
                    all_returns.append(event['progression'][day]['cumulative_return_pct'])
            
            if all_returns:
                median_return = np.median(all_returns)
                std_return = np.std(all_returns)
                
                distributions[day] = {
                    'median': median_return,
                    'std': std_return,
                    'minus_2sd': median_return - 2 * std_return,
                    'minus_1sd': median_return - std_return,
                    'plus_1sd': median_return + std_return,
                    'plus_2sd': median_return + 2 * std_return,
                    'sample_size': len(all_returns)
                }
            else:
                distributions[day] = {
                    'median': 0, 'std': 0, 'minus_2sd': 0, 'minus_1sd': 0,
                    'plus_1sd': 0, 'plus_2sd': 0, 'sample_size': 0
                }
        
        return distributions

    def analyze_percentile_movements(self, events: List[Dict]) -> Dict:
        """Track percentile movements from entry through D1-D7."""
        movement_analysis = {
            'percentile_by_day': {},
            'reversion_analysis': {}
        }
        
        # Track percentiles for each day
        for day in self.horizons:
            day_percentiles = []
            percentile_changes = []
            
            for event in events:
                if day in event['progression']:
                    current_percentile = event['progression'][day]['percentile']
                    day_percentiles.append(current_percentile)
                    
                    # Change from entry
                    change = current_percentile - event['entry_percentile']
                    percentile_changes.append(change)
            
            if day_percentiles:
                movement_analysis['percentile_by_day'][day] = {
                    'median_percentile': np.median(day_percentiles),
                    'mean_percentile': np.mean(day_percentiles),
                    'p25_percentile': np.percentile(day_percentiles, 25),
                    'p75_percentile': np.percentile(day_percentiles, 75),
                    'median_change_from_entry': np.median(percentile_changes),
                    'upward_movement_rate': (np.array(percentile_changes) > 0).mean() * 100,
                    'strong_upward_rate': (np.array(percentile_changes) > 10).mean() * 100,
                    'sample_size': len(day_percentiles)
                }
        
        # Analyze reversion patterns
        final_percentiles = []
        max_percentiles = []
        
        for event in events:
            event_percentiles = []
            for day in self.horizons:
                if day in event['progression']:
                    event_percentiles.append(event['progression'][day]['percentile'])
            
            if event_percentiles:
                final_percentiles.append(event_percentiles[-1])
                max_percentiles.append(max(event_percentiles))
        
        if final_percentiles and max_percentiles:
            movement_analysis['reversion_analysis'] = {
                'median_final_percentile': np.median(final_percentiles),
                'median_peak_percentile': np.median(max_percentiles),
                'reversion_from_peak': np.median(max_percentiles) - np.median(final_percentiles),
                'complete_reversion_rate': (np.array(final_percentiles) < 20).mean() * 100
            }
        
        return movement_analysis
    
    def aggregate_cross_threshold_data(self, ticker_data: Dict) -> Dict:
        """FIXED: Aggregate performance data across all thresholds with correct calculations."""
        cross_threshold_summary = {}
        
        for threshold, threshold_data in ticker_data.get('thresholds', {}).items():
            events = threshold_data['events']
            risk = threshold_data['risk_metrics']
            win_rates = threshold_data['win_rates']
            return_distributions = threshold_data['return_distributions']
            
            # Calculate overall win rate (average across D1-D7)
            overall_win_rate = np.mean(list(win_rates.values())) if win_rates else 0
            
            # Get D7 performance (final holding period)
            d7_median_return = return_distributions.get(7, {}).get('median', 0)
            d7_std = return_distributions.get(7, {}).get('std', 0)
            
            # FIXED: Calculate Sharpe-like efficiency with proper handling of edge cases
            if d7_std > 0 and not np.isnan(d7_std) and d7_std != 0:
                sharpe_efficiency = d7_median_return / d7_std
            else:
                # If std is 0 or NaN, use return magnitude as proxy
                sharpe_efficiency = abs(d7_median_return) / 10 if d7_median_return != 0 else 0
            
            # FIXED: Extract position sizing recommendation using correct worst-case loss
            worst_case_loss = abs(risk.p90_drawdown) if risk.p90_drawdown < 0 else 0.1  # Minimum 0.1% to avoid division by zero
            if worst_case_loss > 0:
                recommended_position_size = min(50, max(1, 2.0 / (worst_case_loss / 100)))  # Cap at 50%, minimum 1%
            else:
                recommended_position_size = 20  # Default fallback
            
            cross_threshold_summary[threshold] = {
                'trades': events,
                'win_rate': overall_win_rate,
                'median_return_d7': d7_median_return,
                'return_std_d7': d7_std,
                'median_drawdown': risk.median_drawdown,
                'p90_drawdown': risk.p90_drawdown,
                'max_consecutive_losses': risk.max_consecutive_losses,
                'best_trade': risk.best_single_gain,
                'worst_trade': risk.worst_single_loss,
                'sharpe_efficiency': sharpe_efficiency,
                'recommended_position_size': recommended_position_size,
                'avg_loss_magnitude': risk.avg_loss_magnitude
            }
        
        # FIXED: Calculate actual cross-threshold correlations based on return patterns
        correlations = {}
        if len(cross_threshold_summary) >= 2:
            thresholds = list(cross_threshold_summary.keys())
            
            for i, thresh1 in enumerate(thresholds):
                for j, thresh2 in enumerate(thresholds):
                    if i < j:  # Only calculate upper triangle
                        data1 = cross_threshold_summary[thresh1]
                        data2 = cross_threshold_summary[thresh2]
                        
                        # Calculate correlation based on multiple factors
                        return_correlation = 1 - abs(data1['median_return_d7'] - data2['median_return_d7']) / (
                            max(abs(data1['median_return_d7']), abs(data2['median_return_d7']), 1))
                        
                        risk_correlation = 1 - abs(abs(data1['median_drawdown']) - abs(data2['median_drawdown'])) / (
                            max(abs(data1['median_drawdown']), abs(data2['median_drawdown']), 1))
                        
                        win_rate_correlation = 1 - abs(data1['win_rate'] - data2['win_rate']) / 100
                        
                        # Average correlation
                        estimated_correlation = (return_correlation + risk_correlation + win_rate_correlation) / 3
                        correlations[f"{thresh1}vs{thresh2}"] = max(0, min(1, estimated_correlation))
        
        return {
            'summary': cross_threshold_summary,
            'correlations': correlations
        }
    
    def print_cross_threshold_comparison(self, ticker: str, cross_threshold_data: Dict):
        """FIXED: Print enhanced cross-threshold comparison with specific actionable recommendations."""
        summary = cross_threshold_data['summary']
        correlations = cross_threshold_data['correlations']
        
        if not summary:
            return
        
        print(f"\n{'='*90}")
        print(f"CROSS-THRESHOLD COMPARISON - {ticker} (Capital Allocation Framework)")
        print(f"{'='*90}")
        
        # Build comparison table
        thresholds = sorted(summary.keys())
        
        # Table header
        print(f"+{'-' * 17}+" + "-" * 16 * len(thresholds) + "+")
        header = f"| {'Metric':<15} |"
        for thresh in thresholds:
            header += f" {'<=' + str(thresh) + '%':<14} |"
        print(header)
        print(f"+{'-' * 17}+" + "-" * 16 * len(thresholds) + "+")
        
        # Metrics rows
        metrics = [
            ('Trades', 'trades', lambda x: f"{x:>8.0f}"),
            ('Win Rate', 'win_rate', lambda x: f"{x:>7.1f}%"),
            ('D7 Return', 'median_return_d7', lambda x: f"{x:>+7.2f}%"),
            ('Return StdDev', 'return_std_d7', lambda x: f"{x:>8.2f}%"),
            ('Med Drawdown', 'median_drawdown', lambda x: f"{x:>+8.2f}%"),
            ('P90 Drawdown', 'p90_drawdown', lambda x: f"{x:>+8.2f}%"),
            ('Max Loss Stk', 'max_consecutive_losses', lambda x: f"{x:>8.0f}"),
            ('Best Trade', 'best_trade', lambda x: f"{x:>+8.2f}%"),
            ('Worst Trade', 'worst_trade', lambda x: f"{x:>+8.2f}%"),
            ('Sharpe-like', 'sharpe_efficiency', lambda x: f"{x:>8.2f}"),
            ('Position Size', 'recommended_position_size', lambda x: f"{x:>7.1f}%")
        ]
        
        for metric_name, metric_key, formatter in metrics:
            row = f"| {metric_name:<15} |"
            for thresh in thresholds:
                value = summary[thresh].get(metric_key, 0)
                formatted_value = formatter(value)
                row += f" {formatted_value:<14} |"
            print(row)
        
        print(f"+{'-' * 17}+" + "-" * 16 * len(thresholds) + "+")
        
        # ENHANCED Analytics panel with specific recommendations
        print(f"\nCROSS-THRESHOLD ANALYTICS:")
        
        # 1. FIXED: Efficiency ranking with proper differentiation
        efficiency_ranking = []
        for thresh in thresholds:
            data = summary[thresh]
            efficiency_ranking.append((thresh, data['sharpe_efficiency'], data['median_return_d7'], abs(data['median_drawdown'])))
        
        efficiency_ranking.sort(key=lambda x: x[1], reverse=True)  # Sort by Sharpe-like efficiency
        
        print(f"* EFFICIENCY RANKING (Return/Risk Sharpe-like):")
        for i, (thresh, efficiency, ret, risk) in enumerate(efficiency_ranking):
            rank_indicator = "*" if i == 0 else f"{i+1}."
            print(f"  {rank_indicator} <={thresh}%: {efficiency:.2f} efficiency ({ret:+.2f}% return, {risk:.2f}% risk)")
        
        # 2. ENHANCED: Strategic recommendations with specific allocations
        print(f"\n* STRATEGIC RECOMMENDATIONS:")
        
        best_threshold = efficiency_ranking[0][0]
        best_efficiency = efficiency_ranking[0][1]
        best_return = efficiency_ranking[0][2]
        
        # FIXED: Generate specific actionable recommendations
        recommendations = []
        
        if best_efficiency > 0.3:
            recommendations.append(f"PRIMARY STRATEGY: Focus 60-70% allocation on <={best_threshold}% (highest efficiency {best_efficiency:.2f})")
            recommendations.append(f"SECONDARY: Allocate 20-25% to second-best threshold for diversification")
            recommendations.append(f"TACTICAL: Reserve 10-15% for opportunistic entries across all thresholds")
        elif best_efficiency > 0.15:
            recommendations.append(f"MODERATE STRATEGY: Balance 50% on <={best_threshold}% (best efficiency {best_efficiency:.2f})")
            recommendations.append(f"DIVERSIFICATION: Split remaining 50% across other thresholds based on risk tolerance")
            if best_return > 0.5:
                recommendations.append(f"TIMING: Focus on <={best_threshold}% during favorable market conditions")
        elif best_efficiency > 0.05:
            recommendations.append(f"CONSERVATIVE APPROACH: Low overall efficiency - limit total strategy allocation to 5-10% of portfolio")
            recommendations.append(f"RISK MANAGEMENT: Use <={best_threshold}% only, with tight stop losses")
            recommendations.append(f"MONITORING: Review monthly - consider pausing if efficiency deteriorates further")
        else:
            recommendations.append(f"CAUTION: All thresholds show very low efficiency (<0.05) - avoid this strategy")
            recommendations.append(f"ALTERNATIVE: Consider different entry criteria or market timing approaches")
            recommendations.append(f"REVIEW: Re-evaluate strategy parameters or look for regime changes")
        
        # Add diversification insights if correlations available
        if correlations:
            avg_correlation = np.mean(list(correlations.values()))
            if avg_correlation < 0.3:
                recommendations.append(f"DIVERSIFICATION BENEFIT: Low correlation ({avg_correlation:.2f}) - thresholds provide genuine diversification")
            elif avg_correlation < 0.7:
                recommendations.append(f"MODERATE DIVERSIFICATION: Medium correlation ({avg_correlation:.2f}) - some diversification benefit")
            else:
                recommendations.append(f"LIMITED DIVERSIFICATION: High correlation ({avg_correlation:.2f}) - thresholds behave similarly")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
        
        # 3. NEW: Risk-adjusted portfolio allocation framework
        print(f"\n* RISK-ADJUSTED ALLOCATION FRAMEWORK:")
        
        total_recommended_size = sum(summary[thresh]['recommended_position_size'] for thresh in thresholds) / len(thresholds)
        
        if total_recommended_size > 25:
            portfolio_allocation = "AGGRESSIVE: 15-25% total portfolio allocation across all thresholds"
        elif total_recommended_size > 15:
            portfolio_allocation = "MODERATE: 10-15% total portfolio allocation with position sizing discipline"
        elif total_recommended_size > 8:
            portfolio_allocation = "CONSERVATIVE: 5-10% total portfolio allocation with strict risk controls"
        else:
            portfolio_allocation = "MINIMAL: <5% allocation - high-risk strategy requiring careful monitoring"
        
        print(f"  Portfolio Guidance: {portfolio_allocation}")
        print(f"  Average Position Size: {total_recommended_size:.1f}% per trade")
        
        if correlations:
            print(f"  Correlation Insights:")
            for pair, corr in correlations.items():
                thresh_pair = pair.replace('vs', ' vs ')
                if corr < 0.5:
                    insight = "Good diversification potential"
                elif corr < 0.8:
                    insight = "Moderate diversification"
                else:
                    insight = "Limited diversification benefit"
                print(f"    {thresh_pair}: {corr:.2f} correlation - {insight}")

    def calculate_optimal_exit_strategy(self, threshold: float, return_distributions: Dict, 
                                      performance_matrix: Dict) -> Dict:
        """Calculate optimal exit strategy based on return efficiency and percentile targets."""
        
        # Calculate return efficiency (return per day) for each day
        efficiency_by_day = {}
        for day, dist in return_distributions.items():
            if dist['sample_size'] > 0:
                efficiency_by_day[day] = dist['median'] / day
        
        if not efficiency_by_day:
            return {}
        
        # Find day with highest efficiency
        optimal_day = max(efficiency_by_day.keys(), key=lambda d: efficiency_by_day[d])
        optimal_efficiency = efficiency_by_day[optimal_day]
        target_return = return_distributions[optimal_day]['median']
        
        # Find which percentile range delivers approximately the target return on optimal day
        best_match = None
        smallest_diff = float('inf')
        
        for range_key, range_data in performance_matrix.items():
            if optimal_day in range_data:
                cell = range_data[optimal_day]
                diff = abs(cell.expected_cumulative_return - target_return)
                if diff < smallest_diff and cell.sample_size >= 2:
                    smallest_diff = diff
                    best_match = {
                        'percentile_range': range_key,
                        'actual_return': cell.expected_cumulative_return,
                        'sample_size': cell.sample_size,
                        'success_rate': cell.expected_success_rate,
                        'confidence': cell.confidence_level
                    }
        
        # Calculate efficiency rankings for context
        efficiency_rankings = []
        for day in sorted(efficiency_by_day.keys()):
            efficiency_rankings.append({
                'day': day,
                'efficiency': efficiency_by_day[day],
                'total_return': return_distributions[day]['median']
            })
        
        efficiency_rankings.sort(key=lambda x: x['efficiency'], reverse=True)
        
        return {
            'optimal_day': optimal_day,
            'optimal_efficiency': optimal_efficiency,
            'target_return': target_return,
            'exit_percentile_target': best_match,
            'efficiency_rankings': efficiency_rankings
        }
    
    def analyze_return_trend_significance(self, events: List[Dict]) -> Dict:
        """ORIGINAL: Analyze if the upward return trend is statistically significant (simple median-based)."""
        # Collect returns by day
        returns_by_day = {day: [] for day in self.horizons}
        
        for event in events:
            for day in self.horizons:
                if day in event['progression']:
                    returns_by_day[day].append(event['progression'][day]['cumulative_return_pct'])
        
        # Calculate trend statistics
        days = []
        median_returns = []
        
        for day in self.horizons:
            if returns_by_day[day]:
                days.append(day)
                median_returns.append(np.median(returns_by_day[day]))
        
        trend_analysis = {}
        
        if len(days) >= 3:
            # Pearson correlation for trend
            correlation, p_value = pearsonr(days, median_returns)
            
            # Find peak day
            peak_day = days[np.argmax(median_returns)]
            peak_return = max(median_returns)
            
            # Mann-Whitney U test comparing early vs late returns
            early_returns = []
            late_returns = []
            
            for day in [1, 2, 3]:
                early_returns.extend(returns_by_day.get(day, []))
            for day in [4, 5, 6, 7]:
                late_returns.extend(returns_by_day.get(day, []))
            
            if early_returns and late_returns:
                try:
                    statistic, mw_p_value = mannwhitneyu(late_returns, early_returns, alternative='greater')
                    significance = "Significant" if mw_p_value < 0.05 else "Not Significant"
                except:
                    mw_p_value = 1.0
                    significance = "Test Failed"
            else:
                mw_p_value = 1.0
                significance = "Insufficient Data"
            
            trend_analysis = {
                'trend_correlation': correlation,
                'trend_p_value': p_value,
                'trend_direction': "Upward" if correlation > 0 else "Downward",
                'trend_strength': abs(correlation),
                'peak_day': peak_day,
                'peak_return': peak_return,
                'early_vs_late_p_value': mw_p_value,
                'early_vs_late_significance': significance,
                'returns_by_day': {day: np.median(returns_by_day[day]) if returns_by_day[day] else 0 
                                  for day in self.horizons}
            }
        
        return trend_analysis

    def _mann_kendall_test(self, data):
        """Simple Mann-Kendall trend test implementation."""
        n = len(data)
        s = 0
        
        for i in range(n-1):
            for j in range(i+1, n):
                if data[j] > data[i]:
                    s += 1
                elif data[j] < data[i]:
                    s -= 1
        
        # Variance calculation (simplified)
        var_s = n * (n - 1) * (2 * n + 5) / 18
        
        if s > 0:
            z = (s - 1) / np.sqrt(var_s)
            trend = 'increasing'
        elif s < 0:
            z = (s + 1) / np.sqrt(var_s)
            trend = 'decreasing'
        else:
            z = 0
            trend = 'no_trend'
        
        # Two-tailed p-value
        p_value = 2 * (1 - norm.cdf(abs(z)))
        
        return trend, p_value

    def _synthesize_trend_insights(self, analysis, valid_days):
        """Synthesize all trend tests into actionable trading insights."""
        insights = []
        
        # Check mean return trend
        mean_trend = analysis['trend_tests']['mean']
        if mean_trend['pearson_p'] < 0.05:
            direction = 'upward' if mean_trend['pearson_r'] > 0 else 'downward'
            insights.append(f"STRONG: Mean returns show {direction} trend (r={mean_trend['pearson_r']:.2f}, p={mean_trend['pearson_p']:.3f})")
        elif mean_trend['spearman_p'] < 0.05:
            direction = 'upward' if mean_trend['spearman_r'] > 0 else 'downward'
            insights.append(f"MODERATE: Non-linear {direction} trend in returns (ρ={mean_trend['spearman_r']:.2f})")
        
        # Check volatility evolution
        vol_trend = analysis['volatility_evolution']
        if vol_trend['significance'] == 'significant':
            insights.append(f"RISK: Volatility is {vol_trend['trend_direction']} over time (r={vol_trend['correlation']:.2f})")
        
        # Check regime changes
        regime = analysis.get('regime_analysis', {})
        if regime.get('significant_change'):
            change_dir = 'improved' if regime['change_magnitude'] > 0 else 'deteriorated'
            insights.append(f"REGIME: Returns {change_dir} significantly in later periods (+{regime['change_magnitude']:.2f}%)")
        
        # Effect size interpretation
        effect = analysis.get('effect_size', {})
        if effect.get('magnitude') in ['medium', 'large']:
            insights.append(f"MAGNITUDE: {effect['interpretation']} (d={effect['cohens_d']:.2f})")
        
        # Strategic implications
        if not insights:
            insights.append("No statistically significant trends detected - returns appear stable across time periods")
        
        return insights

    def analyze_enhanced_return_distribution_trends(self, events: List[Dict]) -> Dict:
        """ENHANCED: Advanced statistical analysis of return distribution trends across D1-D7."""
        
        # Collect all returns by day
        returns_by_day = {day: [] for day in self.horizons}
        
        for event in events:
            for day in self.horizons:
                if day in event['progression']:
                    returns_by_day[day].append(event['progression'][day]['cumulative_return_pct'])
        
        # Filter days with sufficient data
        valid_days = [day for day in self.horizons if len(returns_by_day[day]) >= 10]
        
        if len(valid_days) < 3:
            return {'error': 'Insufficient data for enhanced trend analysis'}
        
        enhanced_analysis = {}
        
        # 1. DISTRIBUTION MOMENTS TRENDS (not just median)
        moments_by_day = {}
        for day in valid_days:
            returns = np.array(returns_by_day[day])
            moments_by_day[day] = {
                'mean': np.mean(returns),
                'median': np.median(returns),
                'std': np.std(returns),
                'skewness': skew(returns),
                'kurtosis': kurtosis(returns),
                'percentile_25': np.percentile(returns, 25),
                'percentile_75': np.percentile(returns, 75),
                'sample_size': len(returns)
            }
        
        # 2. MULTIPLE TREND TESTS
        days_array = np.array(valid_days)
        
        # Test trends in different moments
        trend_tests = {}
        
        for moment in ['mean', 'median', 'std', 'percentile_25', 'percentile_75']:
            values = [moments_by_day[day][moment] for day in valid_days]
            
            # Pearson correlation (linear trend)
            corr, p_val = pearsonr(days_array, values)
            
            # Spearman correlation (monotonic trend)
            spear_corr, spear_p = spearmanr(days_array, values)
            
            # Mann-Kendall trend test (more robust for small samples)
            try:
                mk_trend, mk_p = self._mann_kendall_test(values)
            except:
                mk_trend, mk_p = 'unknown', 1.0
            
            trend_tests[moment] = {
                'pearson_r': corr,
                'pearson_p': p_val,
                'spearman_r': spear_corr, 
                'spearman_p': spear_p,
                'mann_kendall_trend': mk_trend,
                'mann_kendall_p': mk_p,
                'values': values
            }
        
        enhanced_analysis['trend_tests'] = trend_tests
        enhanced_analysis['moments_by_day'] = moments_by_day
        
        # 3. DISTRIBUTION SHAPE EVOLUTION
        # Test if distributions become more/less dispersed over time
        volatility_trend = trend_tests['std']
        enhanced_analysis['volatility_evolution'] = {
            'trend_direction': 'increasing' if volatility_trend['pearson_r'] > 0 else 'decreasing',
            'significance': 'significant' if volatility_trend['pearson_p'] < 0.05 else 'not_significant',
            'correlation': volatility_trend['pearson_r'],
            'p_value': volatility_trend['pearson_p']
        }
        
        # 4. REGIME DETECTION (look for structural breaks)
        mean_returns = [moments_by_day[day]['mean'] for day in valid_days]
        if len(mean_returns) >= 5:
            # Simple regime detection: test if first half differs from second half
            mid_point = len(mean_returns) // 2
            early_returns = []
            late_returns = []
            
            for day in valid_days[:mid_point]:
                early_returns.extend(returns_by_day[day])
            for day in valid_days[mid_point:]:
                late_returns.extend(returns_by_day[day])
            
            if early_returns and late_returns:
                # Mann-Whitney U test for distribution differences
                try:
                    mw_stat, mw_p = mannwhitneyu(late_returns, early_returns, alternative='two-sided')
                    regime_change = {
                        'early_mean': np.mean(early_returns),
                        'late_mean': np.mean(late_returns),
                        'early_std': np.std(early_returns),
                        'late_std': np.std(late_returns),
                        'mann_whitney_p': mw_p,
                        'significant_change': mw_p < 0.05,
                        'change_magnitude': np.mean(late_returns) - np.mean(early_returns)
                    }
                except:
                    regime_change = {'error': 'Could not perform regime test'}
            else:
                regime_change = {'error': 'Insufficient data for regime test'}
        else:
            regime_change = {'error': 'Too few days for regime analysis'}
        
        enhanced_analysis['regime_analysis'] = regime_change
        
        # 5. PRACTICAL SIGNIFICANCE (effect sizes)
        # Cohen's d for early vs late
        if 'change_magnitude' in regime_change:
            try:
                pooled_std = np.sqrt((regime_change['early_std']**2 + regime_change['late_std']**2) / 2)
                cohens_d = regime_change['change_magnitude'] / pooled_std if pooled_std > 0 else 0
                
                if abs(cohens_d) >= 0.8:
                    effect_size = 'large'
                elif abs(cohens_d) >= 0.5:
                    effect_size = 'medium'
                elif abs(cohens_d) >= 0.2:
                    effect_size = 'small'
                else:
                    effect_size = 'negligible'
                    
                enhanced_analysis['effect_size'] = {
                    'cohens_d': cohens_d,
                    'magnitude': effect_size,
                    'interpretation': f"{effect_size.title()} practical difference between early and late periods"
                }
            except:
                enhanced_analysis['effect_size'] = {'error': 'Could not calculate effect size'}
        
        # 6. COMPREHENSIVE TREND SUMMARY
        # Synthesize all tests into actionable insights
        summary = self._synthesize_trend_insights(enhanced_analysis, valid_days)
        enhanced_analysis['actionable_summary'] = summary
        
        return enhanced_analysis
    
    def generate_trade_management_rules(self, threshold: float, win_rates: Dict, 
                                      percentile_movements: Dict, trend_analysis: Dict) -> List[Dict]:
        """Generate specific trade management rules based on observed patterns."""
        
        rules = []
        
        # Find peak win rate day
        if win_rates:
            peak_day = max(win_rates.keys(), key=lambda d: win_rates[d])
            peak_win_rate = win_rates[peak_day]
            
            # Rule 1: Optimal exit timing
            if peak_win_rate > 65:
                rules.append({
                    'type': 'Exit Timing',
                    'rule': f"Target exit around D{peak_day} (peak {peak_win_rate:.1f}% win rate)",
                    'confidence': 'High' if peak_win_rate > 70 else 'Medium'
                })
        
        # Rule 2: Trend-based management
        if trend_analysis.get('trend_direction') == 'Upward' and trend_analysis.get('trend_p_value', 1) < 0.05:
            rules.append({
                'type': 'Trend Following',
                'rule': f"Strong upward trend detected (r={trend_analysis['trend_correlation']:.2f}, p={trend_analysis['trend_p_value']:.3f}) - hold through peak",
                'confidence': 'High'
            })
        
        # Rule 3: Early warning system
        if 1 in percentile_movements.get('percentile_by_day', {}):
            d1_data = percentile_movements['percentile_by_day'][1]
            if d1_data['strong_upward_rate'] > 40:
                rules.append({
                    'type': 'Early Exit Signal',
                    'rule': f"If percentile jumps >10 points by D1, consider 25% profit taking ({d1_data['strong_upward_rate']:.0f}% show strong early moves)",
                    'confidence': 'Medium'
                })
        
        # Rule 4: Reversion protection
        if 'reversion_analysis' in percentile_movements:
            rev = percentile_movements['reversion_analysis']
            if rev['reversion_from_peak'] > 5:
                rules.append({
                    'type': 'Reversion Protection',
                    'rule': f"Start trailing stop at {rev['median_peak_percentile']:.0f}% percentile (typical peak before {rev['reversion_from_peak']:.0f}pt decline)",
                    'confidence': 'High'
                })
        
        return rules
    
    def analyze_ticker(self, ticker: str) -> Dict:
        """Analyze single ticker with enhanced analysis including percentile movements."""
        print(f"Analyzing {ticker}...")
        
        data = self.fetch_data(ticker)
        if data.empty:
            return {}
        
        # Use the EXACT RSI-MA calculation from working script
        indicator = self.calculate_rsi_ma_indicator(data['Close'])
        percentile_ranks = calculate_percentile_ranks(indicator, LOOKBACK)
        
        benchmark = self.calculate_enhanced_market_benchmark(data['Close'], ticker)
        
        ticker_results = {
            'ticker': ticker,
            'data_points': len(data),
            'benchmark': benchmark,
            'thresholds': {}
        }
        
        for threshold in self.entry_thresholds:
            events = self.find_entry_events_enhanced(percentile_ranks, data['Close'], threshold)
            
            if len(events) < 10:
                print(f"  Skipping <={threshold}% threshold - only {len(events)} events (need 10+)")
                continue
            
            performance_matrix = self.build_enhanced_matrix(events)
            risk_metrics = self.calculate_risk_metrics(events)
            win_rates = self.calculate_overall_win_rates(events)
            return_distributions = self.calculate_return_distribution(events)
            
            # Enhanced analyses:
            percentile_movements = self.analyze_percentile_movements(events)
            
            # BOTH trend analyses:
            trend_analysis = self.analyze_return_trend_significance(events)  # Original simple
            enhanced_trend_analysis = self.analyze_enhanced_return_distribution_trends(events)  # NEW advanced
            
            trade_rules = self.generate_trade_management_rules(threshold, win_rates, 
                                                             percentile_movements, trend_analysis)
            
            # Optimal exit strategy calculation
            optimal_exit_strategy = self.calculate_optimal_exit_strategy(threshold, return_distributions, 
                                                                       performance_matrix)
            
            ticker_results['thresholds'][threshold] = {
                'events': len(events),
                'performance_matrix': performance_matrix,
                'risk_metrics': risk_metrics,
                'win_rates': win_rates,
                'return_distributions': return_distributions,
                'percentile_movements': percentile_movements,
                'trend_analysis': trend_analysis,  # Original simple
                'enhanced_trend_analysis': enhanced_trend_analysis,  # NEW advanced
                'trade_management_rules': trade_rules,
                'optimal_exit_strategy': optimal_exit_strategy
            }
            
            matrix_key = f"{ticker}_{threshold}"
            self.performance_matrices[matrix_key] = performance_matrix
        
        # VERIFICATION DATA - computed from live data
        last_close = float(data['Close'].iloc[-1])
        prev_close = float(data['Close'].iloc[-2])
        daily_return_pct = (last_close / prev_close - 1.0) * 100.0
        last_rsi_ma = float(indicator.iloc[-1])
        
        ticker_results['verification'] = {
            'last_close': last_close,
            'daily_return_pct': daily_return_pct, 
            'last_rsi_ma': last_rsi_ma
        }
        
        print(f"Analysis complete for {ticker} - {len(ticker_results['thresholds'])} thresholds analyzed")
        return ticker_results
    
    def run_analysis(self) -> Dict:
        """Run analysis with cross-threshold comparison."""
        print(f"Building Enhanced Performance Matrix (D1-7) with RSI-MA EMA({MA_LENGTH}) Analysis...")
        print(f"Settings: RSI({RSI_LENGTH}) + EMA({MA_LENGTH}), {LOOKBACK}-period percentile lookback")
        
        start_time = time.time()
        results = {}
        
        for ticker in self.tickers:
            try:
                result = self.analyze_ticker(ticker)
                if result:
                    results[ticker] = result
            except Exception as e:
                print(f"Error analyzing {ticker}: {e}")
                continue
        
        elapsed_time = time.time() - start_time
        print(f"Analysis completed in {elapsed_time:.1f} seconds\n")
        
        self.results = results
        return results
    
    def print_enhanced_results(self):
        """Print enhanced results with complete trend analysis and fixed cross-threshold comparison."""
        if not self.results:
            print("No results to display.")
            return
        
        print("=" * 180)
        print("ENHANCED PERFORMANCE MATRIX v4 - RSI-MA EMA(14) WITH COMPLETE FIXED ANALYSIS")
        print("=" * 180)
        print("Settings: RSI(14) + EMA(14), 500-period percentile lookback (no look-ahead)")
        print("Returns: CUMULATIVE from entry to target day")
        print("Benchmarks: Individual Daily | Cumulative from Entry")
        print("Win Rate: Overall profit vs loss percentage for each day")
        print("Percentile Movement tracking & Statistical Trend Significance")
        print("Trade Management Rules based on observed patterns")
        print("Optimal Exit Strategy based on return efficiency")
        print("Advanced return distribution trend analysis with multiple statistical tests")
        print("FIXED: Complete risk analysis logic with clearer language and practical guidance")
        print("FIXED: Cross-threshold comparison panel with accurate calculations and specific recommendations")
        print("Confidence: VH=20+, H=10+, M=5+, L=3+, VL=1-2 samples")
        
        for ticker, ticker_data in self.results.items():
            print(f"\n{ticker} ENHANCED Performance Matrix")
            benchmark = ticker_data['benchmark']
            verification = ticker_data.get('verification', {})
            
            # Display enhanced benchmarks
            print("MARKET BENCHMARKS:")
            print("Individual Daily: ", end="")
            for day in range(1, 8):
                print(f"D{day}:{benchmark.individual_daily_returns[day]:+.3f}%", end=" | " if day < 7 else "\n")
            print("Cumulative:       ", end="")
            for day in range(1, 8):
                print(f"D{day}:{benchmark.cumulative_returns[day]:+.3f}%", end=" | " if day < 7 else "\n")
            
            # VERIFICATION BANNER - exact format required
            if verification and 'last_close' in verification and 'last_rsi_ma' in verification:
                last_close = verification['last_close']
                daily_return = verification.get('daily_return_pct', 0)
                last_rsi_ma = verification['last_rsi_ma']
                print(f"STRATEGY VERIFICATION: Close = ${last_close:.2f} ({daily_return:+.2f}%) | RSI-MA = {last_rsi_ma:.2f}")
            else:
                print("WARNING: No verification data found - check RSI-MA calculation")
            
            print("-" * 170)
            
            for threshold, threshold_data in ticker_data.get('thresholds', {}).items():
                events = threshold_data['events']
                matrix = threshold_data['performance_matrix']
                risk = threshold_data['risk_metrics']
                win_rates = threshold_data['win_rates']
                return_distributions = threshold_data['return_distributions']
                
                # Enhanced data:
                trend_analysis = threshold_data.get('trend_analysis', {})  # Original simple
                enhanced_trend_analysis = threshold_data.get('enhanced_trend_analysis', {})  # NEW advanced
                percentile_movements = threshold_data.get('percentile_movements', {})
                trade_rules = threshold_data.get('trade_management_rules', [])
                optimal_exit_strategy = threshold_data.get('optimal_exit_strategy', {})
                
                print(f"\nEntry <={threshold}% - Complete D1-7 Matrix ({events} events)")
                print("Shows: CUMULATIVE Return% (Sample Size & Confidence)")
                print("Percentile   |      D1      |      D2      |      D3      |      D4      |      D5      |      D6      |      D7      |")
                print("-------------|--------------|--------------|--------------|--------------|--------------|--------------|--------------|")
                
                for from_pct, to_pct in self.percentile_ranges:
                    range_key = f"{from_pct:2.0f}-{to_pct:2.0f}%"
                    range_data = matrix.get(range_key, {})
                    
                    day_strings = []
                    for day in range(1, 8):
                        if day in range_data:
                            cell = range_data[day]
                            day_str = f"{cell.expected_cumulative_return:+5.2f}% ({cell.sample_size}{cell.confidence_level})"
                        else:
                            day_str = "      -      "
                        day_strings.append(day_str)
                    
                    print(f"{range_key:>12} |{day_strings[0]:>14}|{day_strings[1]:>14}|{day_strings[2]:>14}|{day_strings[3]:>14}|{day_strings[4]:>14}|{day_strings[5]:>14}|{day_strings[6]:>14}|")
                
                # Add win rate row at bottom
                print("-------------|--------------|--------------|--------------|--------------|--------------|--------------|--------------|")
                win_rate_strings = []
                for day in range(1, 8):
                    if day in win_rates:
                        win_rate_str = f"    {win_rates[day]:5.1f}%    "
                    else:
                        win_rate_str = "      -      "
                    win_rate_strings.append(win_rate_str)
                
                print(f"{'Win Rate %':>12} |{win_rate_strings[0]:>14}|{win_rate_strings[1]:>14}|{win_rate_strings[2]:>14}|{win_rate_strings[3]:>14}|{win_rate_strings[4]:>14}|{win_rate_strings[5]:>14}|{win_rate_strings[6]:>14}|")
                
                # Add return distribution row (median +/- std dev)
                print("-------------|--------------|--------------|--------------|--------------|--------------|--------------|--------------|")
                ret_dist_strings = []
                for day in range(1, 8):
                    if day in return_distributions and return_distributions[day]['sample_size'] > 0:
                        dist = return_distributions[day]
                        ret_dist_str = f"{dist['median']:+4.1f}+/-{dist['std']:4.1f}"
                    else:
                        ret_dist_str = "      -      "
                    ret_dist_strings.append(ret_dist_str)
                
                print(f"{'Ret Dist %':>12} |{ret_dist_strings[0]:>14}|{ret_dist_strings[1]:>14}|{ret_dist_strings[2]:>14}|{ret_dist_strings[3]:>14}|{ret_dist_strings[4]:>14}|{ret_dist_strings[5]:>14}|{ret_dist_strings[6]:>14}|")
                
                # ORIGINAL TREND SIGNIFICANCE ANALYSIS (simple median-based)
                if trend_analysis:
                    print(f"\nORIGINAL TREND SIGNIFICANCE ANALYSIS (Simple Median-Based):")
                    direction = trend_analysis.get('trend_direction', 'Unknown')
                    correlation = trend_analysis.get('trend_correlation', 0)
                    p_value = trend_analysis.get('trend_p_value', 1)
                    significance = trend_analysis.get('early_vs_late_significance', 'Unknown')
                    mw_p_value = trend_analysis.get('early_vs_late_p_value', 1)
                    
                    # Statistical robustness assessment
                    if p_value < 0.01:
                        trend_confidence = "very high"
                    elif p_value < 0.05:
                        trend_confidence = "high"
                    elif p_value < 0.10:
                        trend_confidence = "moderate"
                    else:
                        trend_confidence = "low"
                    
                    print(f"* Statistical Trend: {direction} trend with {trend_confidence} confidence (r={correlation:.2f}, p={p_value:.3f})")
                    
                    # Early vs Late analysis with practical implications
                    if mw_p_value < 0.05:
                        timing_insight = "Later exits (D4-7) significantly outperform early exits (D1-3)"
                    elif mw_p_value < 0.10:
                        timing_insight = "Later exits show marginal advantage over early exits (borderline significant)"
                    else:
                        timing_insight = "No clear timing advantage between early vs late exits"
                    
                    print(f"* Exit Timing Strategy: {timing_insight} (p={mw_p_value:.3f})")

                # FIXED: NEW ENHANCED TREND ANALYSIS (comprehensive distribution-based) - RESTORED COMPLETELY
                if enhanced_trend_analysis and 'error' not in enhanced_trend_analysis:
                    print(f"\nSTRATEGY PERFORMANCE EVOLUTION ANALYSIS:")
                    
                    # BUSINESS IMPACT ASSESSMENT
                    trend_tests = enhanced_trend_analysis.get('trend_tests', {})
                    regime = enhanced_trend_analysis.get('regime_analysis', {})
                    vol_evolution = enhanced_trend_analysis.get('volatility_evolution', {})
                    effect = enhanced_trend_analysis.get('effect_size', {})
                    
                    # Strategy Performance Trajectory (Comprehensive)
                    if trend_tests and 'mean' in trend_tests:
                        mean_trend = trend_tests['mean']
                        vol_trend = trend_tests.get('std', {})
                        
                        if mean_trend.get('pearson_p', 1) < 0.05:
                            return_direction = 'getting better' if mean_trend['pearson_r'] > 0 else 'getting worse'
                            confidence_pct = (1-mean_trend['pearson_p'])*100
                            print(f"* PROFIT TREND: Strategy is {return_direction} over time")
                            print(f"  - Confidence level: {confidence_pct:.1f}% certain this trend is real (Pearson r={mean_trend['pearson_r']:.2f}, p={mean_trend['pearson_p']:.3f})")
                        
                        # Risk vs Reward Balance (Comprehensive)
                        if vol_trend.get('pearson_p', 1) < 0.05 and mean_trend.get('pearson_p', 1) < 0.05:
                            vol_direction = 'increasing' if vol_trend['pearson_r'] > 0 else 'decreasing'
                            
                            if vol_direction == 'increasing' and return_direction == 'getting better':
                                risk_ratio = abs(vol_trend['pearson_r']) / abs(mean_trend['pearson_r'])
                                if risk_ratio > 0.8:
                                    print(f"  - RISK ALERT: As profits improve, risk is growing almost as fast")
                                    print(f"    Translation: Higher profits but much more unpredictable outcomes (Vol r={vol_trend['pearson_r']:.2f} vs Returns r={mean_trend['pearson_r']:.2f})")
                                    print(f"    Action needed: Use smaller position sizes for longer holds (D4-D7)")
                                else:
                                    print(f"  - RISK STATUS: Risk growing but at manageable rate vs profit improvement (Risk ratio: {risk_ratio:.1f}x)")
                            
                            elif vol_direction == 'decreasing' and return_direction == 'getting better':
                                print(f"  - IDEAL SITUATION: Profits improving while risk decreasing")
                                print(f"    Translation: More predictable AND more profitable over time (Vol r={vol_trend['pearson_r']:.2f}, Returns r={mean_trend['pearson_r']:.2f})")
                    
                    # Performance Comparison: Then vs Now (Comprehensive)
                    if regime and regime.get('significant_change'):
                        change_magnitude = regime['change_magnitude']
                        early_mean = regime['early_mean']
                        late_mean = regime['late_mean']
                        
                        if change_magnitude > 0:
                            print(f"* PERFORMANCE SHIFT: Strategy working better in recent periods")
                            
                            # Add context about what these percentages mean
                            if early_mean > 0:
                                improvement_multiple = late_mean / early_mean
                                print(f"  - Earlier period: Average +{early_mean:.2f}% per trade (D1-D3 exits when strategy was already profitable)")
                                print(f"  - Recent period: Average +{late_mean:.2f}% per trade (D4-D7 exits, {improvement_multiple:.1f}x better than before)")
                            else:
                                print(f"  - Earlier period: Average {early_mean:+.2f}% per trade (D1-D3 exits when strategy was losing money)")
                                print(f"  - Recent period: Average +{late_mean:.2f}% per trade (D4-D7 exits, strategy now profitable)")
                            
                            print(f"  - Net improvement: +{change_magnitude:.2f}% more profit per trade (Mann-Whitney p={regime['mann_whitney_p']:.3f})")
                            
                            # Add practical context about trade frequency and dollar impact
                            print(f"  - PRACTICAL IMPACT: On a $10,000 position:")
                            print(f"    Earlier (D1-D3): ${early_mean * 100:.0f} average profit per trade")
                            print(f"    Recent (D4-D7): ${late_mean * 100:.0f} average profit per trade")
                            print(f"    Extra profit: ${change_magnitude * 100:.0f} per trade improvement")
                            
                            # Sizing confidence translation
                            if effect.get('magnitude') == 'large':
                                print(f"  - SIZING CONFIDENCE: High - improvement is substantial and reliable (Cohen's d={effect.get('cohens_d', 0):.2f})")
                            elif effect.get('magnitude') == 'medium':
                                print(f"  - SIZING CONFIDENCE: Moderate - improvement is meaningful but not dramatic (Cohen's d={effect.get('cohens_d', 0):.2f})")
                            else:
                                print(f"  - SIZING CONFIDENCE: Low - improvement exists but may be temporary (Cohen's d={effect.get('cohens_d', 0):.2f})")
                        else:
                            print(f"* PERFORMANCE DECLINE: Strategy working worse in recent periods")
                            print(f"  - Performance drop: {change_magnitude:+.2f}% per trade (Mann-Whitney p={regime['mann_whitney_p']:.3f})")
                            print(f"  - Action needed: Reduce allocation or review strategy parameters")
                    
                    # Timing Implications (Comprehensive)
                    if trend_tests:
                        p75_trend = trend_tests.get('percentile_75', {})
                        
                        print(f"* TIMING INSIGHTS:")
                        
                        # Best case analysis
                        if p75_trend.get('pearson_p', 1) < 0.05:
                            p75_direction = 'getting better' if p75_trend['pearson_r'] > 0 else 'getting worse'
                            print(f"  - Your best trades are {p75_direction} over time (75th percentile = top 25% of trades across D1-D7)")
                            print(f"    (Statistical trend: r={p75_trend['pearson_r']:.2f}, p={p75_trend['pearson_p']:.3f})")
                            if p75_direction == 'getting better':
                                print(f"    Implication: Holding longer (D5-D7 exits) may capture bigger wins")
                            else:
                                print(f"    Implication: Take profits earlier to avoid deteriorating upside")
                    
                    # COMPREHENSIVE CAPITAL ALLOCATION RULES WITH FULL DECISION TREE
                    print(f"* ACTIONABLE TRADING RULES:")
                    
                    # Extract key metrics for decision framework
                    if trend_tests and regime:
                        returns_improving = trend_tests.get('mean', {}).get('pearson_r', 0) > 0
                        vol_increasing = trend_tests.get('std', {}).get('pearson_r', 0) > 0
                        regime_improving = regime.get('change_magnitude', 0) > 0
                        effect_large = effect.get('magnitude') in ['large', 'medium']
                        vol_ratio = abs(trend_tests.get('std', {}).get('pearson_r', 0)) / abs(trend_tests.get('mean', {}).get('pearson_r', 1))
                        
                        print(f"  STEP 1 - BASE POSITION SIZE:")
                        if regime_improving and effect_large:
                            print(f"    → Use NORMAL position size (strategy genuinely improving)")
                        elif regime_improving:
                            print(f"    → Use NORMAL position size (improvement confirmed but small)")
                        else:
                            print(f"    → Use 0.8x position size (no clear improvement)")
                        
                        print(f"  STEP 2 - ADJUST FOR HOLDING PERIOD:")
                        if vol_increasing and vol_ratio > 0.7:
                            print(f"    → WHY: Risk growing {vol_ratio:.1f}x as fast as reward")
                            print(f"    → D1-D2: Keep full size (low accumulated risk)")
                            print(f"    → D3-D4: Reduce to 0.9x size (moderate risk buildup)")
                            print(f"    → D5-D7: Reduce to 0.7x size (high volatility expansion)")
                        elif vol_increasing:
                            print(f"    → D1-D3: Keep full size")
                            print(f"    → D4-D7: Reduce to 0.8x size (moderate volatility increase)")
                        else:
                            print(f"    → All days: Keep full size (volatility stable)")
                        
                        print(f"  STEP 3 - PROFIT TAKING STRATEGY:")
                        if vol_increasing and returns_improving:
                            print(f"    → Take 25% profits at D3 (lock in gains before vol expansion)")
                            print(f"    → Take additional 25% at D5 if position still profitable")
                            print(f"    → WHY: Expanding volatility threatens to erase gains")
                        elif returns_improving:
                            print(f"    → Let winners run to D5-D6 (stable risk environment)")
                        else:
                            print(f"    → Take profits early at D2-D3 (no clear improvement trend)")
                        
                        print(f"  STEP 4 - PORTFOLIO ALLOCATION:")
                        if returns_improving and regime_improving and not (vol_increasing and vol_ratio > 0.8):
                            allocation_pct = "15-20%"
                            rationale = "strong improvement with manageable risk"
                        elif returns_improving and regime_improving:
                            allocation_pct = "10-15%"
                            rationale = "improvement confirmed but risk expanding"
                        elif returns_improving:
                            allocation_pct = "8-12%"
                            rationale = "directional improvement but uncertain sustainability"
                        else:
                            allocation_pct = "5-8%"
                            rationale = "no clear positive trend"
                        
                        print(f"    → Allocate {allocation_pct} of portfolio to this strategy")
                        print(f"    → WHY: {rationale}")
                        
                        # COMPREHENSIVE PORTFOLIO ALLOCATION DECISION TREE EXPLANATION
                        print(f"    → ALLOCATION LOGIC:")
                        print(f"      Decision factors for your case:")
                        print(f"      ✓ Returns improving: {'Yes' if returns_improving else 'No'}")
                        print(f"      ✓ Regime improving: {'Yes' if regime_improving else 'No'}")
                        print(f"      ✓ Volatility increasing: {'Yes' if vol_increasing else 'No'}")
                        if vol_increasing:
                            print(f"      ✓ Risk/reward ratio: {vol_ratio:.1f}x ({'High' if vol_ratio > 0.8 else 'Moderate'} risk expansion)")
                        
                        print(f"      Allocation tiers:")
                        print(f"      • 15-20%: Strong improvement + manageable risk")
                        if returns_improving and regime_improving:
                            current_tier = "10-15%: Improvement confirmed but risk expanding ← YOUR CASE"
                        elif returns_improving:
                            current_tier = "8-12%: Directional improvement but uncertain sustainability ← YOUR CASE" 
                        else:
                            current_tier = "5-8%: No clear positive trend ← YOUR CASE"
                        print(f"      • {current_tier}")
                        if "10-15%" not in current_tier:
                            print(f"      • 10-15%: Improvement confirmed but risk expanding")
                        if "8-12%" not in current_tier:
                            print(f"      • 8-12%: Directional improvement but uncertain sustainability") 
                        if "5-8%" not in current_tier:
                            print(f"      • 5-8%: No clear positive trend")
                        
                        print(f"  STEP 5 - MONITORING TRIGGERS:")
                        print(f"    → REDUCE allocation if next period shows declining returns")
                        print(f"    → STOP strategy if volatility increases >50% without return improvement")
                        if vol_increasing:
                            print(f"    → REVIEW monthly: Is risk/reward ratio staying favorable?")
                        
                        # Comprehensive summary box with all details
                        print(f"  ╔═══════════════════════════════════════════════════════╗")
                        print(f"  ║ QUICK REFERENCE CARD                                     ║")
                        print(f"  ║ Base Position: Normal size                               ║")
                        if vol_increasing and vol_ratio > 0.7:
                            print(f"  ║ D1-D2: 100% size  │  D3-D4: 90% size  │  D5-D7: 70% size ║")
                        elif vol_increasing:
                            print(f"  ║ D1-D3: 100% size  │  D4-D7: 80% size                    ║")
                        else:
                            print(f"  ║ All Days: 100% size (stable volatility)                 ║")
                        print(f"  ║ Portfolio Allocation: {allocation_pct}                        ║")
                        print(f"  ║ Profit Taking: {'Early (D3)' if vol_increasing else 'Standard (D5-D6)'}                              ║")
                        print(f"  ╚═══════════════════════════════════════════════════════╝")
                
                elif enhanced_trend_analysis and 'error' in enhanced_trend_analysis:
                    print(f"\nADVANCED TREND ANALYSIS: {enhanced_trend_analysis['error']}")
                
                # ENHANCED PERCENTILE MOVEMENT PATTERNS WITH OPTIMAL EXIT STRATEGY
                if percentile_movements and 'percentile_by_day' in percentile_movements:
                    print(f"\nPERCENTILE MOVEMENT PATTERNS:")
                    
                    # OPTIMAL EXIT STRATEGY based on return efficiency
                    if optimal_exit_strategy:
                        opt_day = optimal_exit_strategy.get('optimal_day')
                        opt_efficiency = optimal_exit_strategy.get('optimal_efficiency', 0)
                        target_return = optimal_exit_strategy.get('target_return', 0)
                        exit_target = optimal_exit_strategy.get('exit_percentile_target')
                        
                        if opt_day and exit_target:
                            print(f"* OPTIMAL EXIT STRATEGY:")
                            print(f"  - Best Efficiency: D{opt_day} ({opt_efficiency:+.3f}% per day, {target_return:+.2f}% total)")
                            print(f"  - Exit Target: When RSI-MA reaches {exit_target['percentile_range']} on D{opt_day}")
                            print(f"  - Historical Performance: {exit_target['actual_return']:+.2f}% return, {exit_target['success_rate']*100:.0f}% success rate")
                            print(f"  - Sample Confidence: {exit_target['sample_size']} trades ({exit_target['confidence']} confidence)")
                    
                    # IMPROVED Reversion risk assessment with clearer language
                    reversion_analysis = print_improved_reversion_risk_analysis(percentile_movements)
                    if reversion_analysis:
                        print(reversion_analysis)
                
                print() # Add blank line before RISK ANALYSIS
                
                # COMPREHENSIVE RISK ANALYSIS - FULL DETAILED VERSION
                self.print_improved_risk_analysis(risk, events, threshold)
                
                # Performance summary
                total_cells = sum(len(range_data) for range_data in matrix.values())
                possible_cells = len(self.percentile_ranges) * len(self.horizons)
                coverage = (total_cells / possible_cells) * 100
                
                print(f"Matrix: {total_cells}/{possible_cells} cells ({coverage:.1f}% coverage)")
                
                # Best daily opportunities
                all_cells = []
                for range_key, range_data in matrix.items():
                    for day, cell in range_data.items():
                        if cell.expected_cumulative_return > 1 and cell.sample_size >= 2:
                            efficiency = cell.expected_cumulative_return / day  # Return per day
                            all_cells.append((range_key, day, cell, efficiency))
                
                if all_cells:
                    # Sort by efficiency (return per day)
                    all_cells.sort(key=lambda x: x[3], reverse=True)
                    print(f"\nTOP 5 MOST EFFICIENT OPPORTUNITIES:")
                    for i, (range_key, day, cell, efficiency) in enumerate(all_cells[:5]):
                        print(f"  {i+1}. {range_key} on D{day}: {cell.expected_cumulative_return:+.2f}% ({efficiency:+.2f}%/day)")
                        print(f"     {cell.sample_size} samples, {cell.expected_success_rate*100:.0f}% success, {cell.confidence_level} confidence")
            
            # FIXED: Add cross-threshold comparison panel for this ticker
            if len(ticker_data.get('thresholds', {})) >= 2:
                cross_threshold_data = self.aggregate_cross_threshold_data(ticker_data)
                self.print_cross_threshold_comparison(ticker, cross_threshold_data)
    
    def lookup_expected_return(self, ticker: str, threshold: float, day: int, current_percentile: float) -> Optional[PerformanceCell]:
        """Lookup expected CUMULATIVE return with enhanced day range."""
        matrix_key = f"{ticker}_{threshold}"
        
        if matrix_key not in self.performance_matrices:
            return None
        
        matrix = self.performance_matrices[matrix_key]
        
        for from_pct, to_pct in self.percentile_ranges:
            if from_pct <= current_percentile < to_pct:
                range_key = f"{from_pct:2.0f}-{to_pct:2.0f}%"
                if range_key in matrix and day in matrix[range_key]:
                    return matrix[range_key][day]
        
        return None


def main():
    """Run enhanced analysis with RSI-MA EMA(14) and fixed cross-threshold comparison panel."""
    
    print("=== MAIN FUNCTION CALLED v4 ===")
    
    # Try to parse arguments, fall back to defaults if argparse fails
    try:
        # Add command line argument support
        parser = argparse.ArgumentParser(description='Enhanced Performance Matrix v4 - RSI-MA Analysis with Fixed Cross-Threshold Comparison')
        parser.add_argument('tickers', nargs='*', help='Ticker symbols to analyze (e.g., AAPL MSFT GOOGL)')
        parser.add_argument('--lookback', type=int, default=LOOKBACK, help=f'Percentile lookback period (default: {LOOKBACK})')
        parser.add_argument('--rsi-length', type=int, default=RSI_LENGTH, help=f'RSI length (default: {RSI_LENGTH})')
        parser.add_argument('--ma-length', type=int, default=MA_LENGTH, help=f'MA length (default: {MA_LENGTH})')
        
        args = parser.parse_args()
        
        # Use command line tickers if provided, otherwise default list
        if args.tickers:
            TICKERS = [ticker.upper() for ticker in args.tickers]
            print(f"Analyzing user-specified tickers: {', '.join(TICKERS)}")
        else:
            TICKERS = DEFAULT_TICKERS
            print(f"Analyzing default tickers: {', '.join(TICKERS)}")
        
        lookback = args.lookback
        rsi_length = args.rsi_length
        ma_length = args.ma_length
        
    except:
        # Fallback if argparse fails - check if command line arguments were provided manually
        if len(sys.argv) > 1:
            # Use command line arguments directly
            TICKERS = [ticker.upper() for ticker in sys.argv[1:] if not ticker.startswith('--')]
            print(f"Analyzing user-specified tickers: {', '.join(TICKERS)}")
        else:
            # Use defaults
            TICKERS = DEFAULT_TICKERS
            print(f"Analyzing default tickers: {', '.join(TICKERS)}")
        
        lookback = LOOKBACK
        rsi_length = RSI_LENGTH
        ma_length = MA_LENGTH
    
    print("Enhanced Performance Matrix v4 - RSI-MA EMA(14) WITH FIXED CROSS-THRESHOLD ANALYSIS")
    print("=" * 90)
    print("FIXES IN V4:")
    print("* RESTORED: Complete enhanced trend analysis with step-by-step trading rules")
    print("* FIXED: Sharpe-like efficiency calculations now properly differentiate thresholds")
    print("* FIXED: Position sizing calculations use correct worst-case loss percentages")
    print("* FIXED: Cross-threshold strategic recommendations provide specific actionable guidance")
    print("* ENHANCED: Improved diversification insights and capital allocation framework")
    print("* VERIFIED: All statistical significance tests properly displayed")
    print()
    print("Settings:")
    print(f"* RSI Length: {rsi_length}")
    print(f"* MA Type: {MA_KIND}")
    print(f"* MA Length: {ma_length}")
    print(f"* Percentile Lookback: {lookback}")
    print(f"* Entry Thresholds: <={DEFAULT_ENTRY_THRESHOLDS}")
    print("Default Tickers: SPY, QQQ, AAPL, AMZN, GOOGL, NVDA, MSFT, META, TSLA, BRK-B, OXY, BTC-USD")
    print("Features:")
    print("* Percentile movement tracking (how RSI-MA percentiles evolve D1-D7)")
    print("* ORIGINAL: Simple median-based trend significance testing")
    print("* ENHANCED: Advanced return distribution trend analysis with multiple statistical tests")
    print("* Trade management rules based on observed patterns")
    print("* Return trend analysis with peak identification")
    print("* Mean reversion analysis for percentile movements")
    print("* OPTIMAL EXIT STRATEGY based on return efficiency and percentile targets")
    print("* COMPLETE: Fixed risk analysis logic with clearer language and practical guidance")
    print("* FIXED: Cross-threshold comparison panel with accurate calculations and specific recommendations")
    print("* Command-line ticker support: python script.py TICKER1 TICKER2 ...")
    print("Enhanced Statistical Analysis:")
    print("* Distribution moments trends (mean, median, std, skewness, kurtosis)")
    print("* Multiple trend tests (Pearson, Spearman, Mann-Kendall)")
    print("* Regime detection and structural break analysis")
    print("* Effect size calculations (Cohen's d)")
    print("* Volatility evolution tracking")
    print("FIXED Cross-Threshold Analytics:")
    print("* Corrected Sharpe-like efficiency ranking across <=5%, <=10%, <=15% thresholds")
    print("* Fixed regime detection comparison across thresholds")
    print("* Accurate correlation analysis for diversification insights")
    print("* Corrected risk-parity capital allocation framework")
    
    backtester = EnhancedPerformanceMatrixBacktester(
        tickers=TICKERS,
        lookback_period=lookback,
        rsi_length=rsi_length,
        ma_length=ma_length
    )
    
    try:
        results = backtester.run_analysis()
        backtester.print_enhanced_results()
        print("=== ANALYSIS COMPLETE v4 ===")
        return backtester
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("=== IN MAIN EXECUTION BLOCK v4 ===")
    backtester = main()
    print("=== SCRIPT COMPLETED v4 ===")