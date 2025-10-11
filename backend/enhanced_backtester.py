#!/usr/bin/env python3
"""
Enhanced Performance Matrix Backtester - Extended to D1-D21

Key Features:
- Extended horizon from D1-D7 to D1-D21
- Percentile movement tracking throughout holding period
- Statistical trend significance testing
- Optimal exit strategy calculation based on return efficiency
- Comprehensive risk metrics
"""

import yfinance as yf
import pandas as pd
import numpy as np
import warnings
from datetime import datetime, timedelta
from typing import Tuple, Dict, List, Optional
import time
from dataclasses import dataclass, asdict
from scipy.stats import mannwhitneyu, pearsonr
import json

warnings.filterwarnings('ignore')

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
    
    def to_dict(self):
        return asdict(self)

@dataclass
class EnhancedMarketBenchmark:
    """Enhanced market benchmark with individual and cumulative returns."""
    ticker: str
    individual_daily_returns: Dict[int, float]
    cumulative_returns: Dict[int, float]
    volatility: float
    
    def to_dict(self):
        return asdict(self)

@dataclass
class RiskMetrics:
    """Risk analysis for the threshold."""
    median_drawdown: float
    p90_drawdown: float
    median_recovery_days: float
    recovery_rate: float
    max_consecutive_losses: int
    avg_loss_magnitude: float
    
    def to_dict(self):
        return asdict(self)

class EnhancedPerformanceMatrixBacktester:
    def __init__(self, 
                 tickers: List[str],
                 lookback_period: int = 500,
                 rsi_length: int = 14,
                 ma_length: int = 14,
                 max_horizon: int = 21):
        """Initialize enhanced backtester with configurable horizon."""
        self.tickers = tickers
        self.lookback_period = lookback_period
        self.rsi_length = rsi_length
        self.ma_length = ma_length
        
        # EXTENDED HORIZONS - Now supports D1-D21 (configurable)
        self.horizons = list(range(1, max_horizon + 1))
        self.max_horizon = max_horizon
        self.entry_thresholds = [5.0, 10.0, 15.0]
        
        # Complete percentile ranges (20 buckets)
        self.percentile_ranges = [
            (0, 5), (5, 10), (10, 15), (15, 20), (20, 25), (25, 30),
            (30, 35), (35, 40), (40, 45), (45, 50), (50, 55), (55, 60),
            (60, 65), (65, 70), (70, 75), (75, 80), (80, 85), (85, 90),
            (90, 95), (95, 100)
        ]
        
        self.results = {}
        self.performance_matrices = {}
    
    def fetch_data(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        """Fetch ticker data with robust error handling."""
        try:
            time.sleep(0.5)  # Rate limiting
            
            # Add user agent to bypass Yahoo Finance blocking
            import requests
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            stock = yf.Ticker(ticker, session=session)
            data = stock.history(period=period, auto_adjust=True, prepost=True)
            
            if data.empty:
                print(f"Retrying {ticker} with different parameters...")
                data = stock.history(period="2y", auto_adjust=True)
                
            if data.empty:
                print(f"Second retry for {ticker}...")
                data = stock.history(period="1y")
            
            if data.empty:
                print(f"Failed to fetch data for {ticker}")
                return pd.DataFrame()
                
            data = data.dropna()
            
            if len(data) < 100:
                print(f"Warning: {ticker} has only {len(data)} data points")
                
            print(f"Successfully fetched {len(data)} data points for {ticker}")
            return data
            
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            try:
                # Add user agent for download method too
                import requests
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                data = yf.download(ticker, period="2y", progress=False, session=session)
                if not data.empty:
                    print(f"Success with yf.download for {ticker}: {len(data)} points")
                    return data
            except Exception as e2:
                print(f"Final error for {ticker}: {e2}")
            return pd.DataFrame()
    
    def calculate_rsi_ma_indicator(self, prices: pd.Series) -> pd.Series:
        """Calculate RSI-MA indicator (14-period RSI with 14-period EMA)."""
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
    
    def calculate_percentile_ranks(self, indicator: pd.Series) -> pd.Series:
        """Calculate rolling percentile ranks (500-period lookback)."""
        def rolling_percentile_rank(window):
            if len(window) < self.lookback_period:
                return np.nan
            current_value = window.iloc[-1]
            below_count = (window.iloc[:-1] < current_value).sum()
            return (below_count / (len(window) - 1)) * 100
        
        return indicator.rolling(
            window=self.lookback_period, 
            min_periods=self.lookback_period
        ).apply(rolling_percentile_rank)
    
    def calculate_enhanced_market_benchmark(self, prices: pd.Series, ticker: str) -> EnhancedMarketBenchmark:
        """Calculate enhanced market benchmark for D1-D21."""
        log_returns = np.log(prices / prices.shift(1)).fillna(0)
        
        # Individual daily returns
        individual_returns = {}
        individual_returns[1] = np.mean(log_returns.dropna()) * 100
        
        for day in range(2, self.max_horizon + 1):
            day_to_day_returns = []
            for i in range(day, len(prices)):
                if i - 1 >= 0:
                    day_return = np.log(prices.iloc[i] / prices.iloc[i-1])
                    day_to_day_returns.append(day_return)
            individual_returns[day] = np.mean(day_to_day_returns) * 100 if day_to_day_returns else 0
        
        # Cumulative returns from entry
        cumulative_returns = {}
        for day in range(1, self.max_horizon + 1):
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
        """Track progression for D1-D21 with risk metrics."""
        entry_price = prices.iloc[entry_idx]
        progression = {}
        
        max_drawdown = 0.0
        recovery_day = -1
        peak_price = entry_price
        
        # Track all days D1 through max_horizon
        for day in range(1, self.max_horizon + 1):
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
                
            # Cumulative return from entry
            cumulative_return = np.log(current_price / entry_price)
            
            # Individual daily return
            if day == 1:
                individual_return = cumulative_return
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
        """Find entry events with D1-D21 tracking."""
        events = []
        
        for i, (date, percentile) in enumerate(percentile_ranks.items()):
            if pd.isna(percentile) or percentile > threshold:
                continue
            
            if i + self.max_horizon >= len(prices):
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
        """Calculate comprehensive risk metrics."""
        if not events:
            return RiskMetrics(0, 0, 0, 0, 0, 0)
        
        drawdowns = [e['max_drawdown_pct'] for e in events]
        recovery_times = [e['recovery_day'] for e in events if e['recovery_day'] > 0]
        
        # Calculate final returns for loss analysis
        final_returns = []
        for event in events:
            if self.max_horizon in event['progression']:
                final_returns.append(event['progression'][self.max_horizon]['cumulative_return_pct'])
            elif event['progression']:
                last_day = max(event['progression'].keys())
                final_returns.append(event['progression'][last_day]['cumulative_return_pct'])
        
        losing_trades = [r for r in final_returns if r < 0]
        
        # Find consecutive losses
        consecutive_losses = 0
        max_consecutive = 0
        for ret in final_returns:
            if ret < 0:
                consecutive_losses += 1
                max_consecutive = max(max_consecutive, consecutive_losses)
            else:
                consecutive_losses = 0
        
        return RiskMetrics(
            median_drawdown=np.median(drawdowns) if drawdowns else 0,
            p90_drawdown=np.percentile(drawdowns, 90) if drawdowns else 0,
            median_recovery_days=np.median(recovery_times) if recovery_times else 0,
            recovery_rate=len(recovery_times) / len(events) if events else 0,
            max_consecutive_losses=max_consecutive,
            avg_loss_magnitude=np.mean(losing_trades) if losing_trades else 0
        )
    
    def build_enhanced_matrix(self, events: List[Dict]) -> Dict[str, Dict[int, PerformanceCell]]:
        """Build enhanced performance matrix for D1-D21."""
        matrix = {}
        
        for from_pct, to_pct in self.percentile_ranges:
            range_key = f"{from_pct:2.0f}-{to_pct:2.0f}%"
            matrix[range_key] = {}
        
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
        """Calculate overall win rate for each day."""
        win_rates = {}
        
        for day in self.horizons:
            all_returns = []
            
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
        """Track percentile movements from entry through D1-D21."""
        movement_analysis = {
            'percentile_by_day': {},
            'reversion_analysis': {}
        }
        
        for day in self.horizons:
            day_percentiles = []
            percentile_changes = []
            
            for event in events:
                if day in event['progression']:
                    current_percentile = event['progression'][day]['percentile']
                    day_percentiles.append(current_percentile)
                    
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
    
    def calculate_optimal_exit_strategy(self, threshold: float, return_distributions: Dict, 
                                      performance_matrix: Dict) -> Dict:
        """Calculate optimal exit strategy based on return efficiency."""
        
        efficiency_by_day = {}
        for day, dist in return_distributions.items():
            if dist['sample_size'] > 0:
                efficiency_by_day[day] = dist['median'] / day
        
        if not efficiency_by_day:
            return {}
        
        optimal_day = max(efficiency_by_day.keys(), key=lambda d: efficiency_by_day[d])
        optimal_efficiency = efficiency_by_day[optimal_day]
        target_return = return_distributions[optimal_day]['median']
        
        # Find percentile range for target return
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
            'efficiency_rankings': efficiency_rankings[:10]  # Top 10
        }
    
    def analyze_return_trend_significance(self, events: List[Dict]) -> Dict:
        """Analyze statistical significance of return trends."""
        returns_by_day = {day: [] for day in self.horizons}
        
        for event in events:
            for day in self.horizons:
                if day in event['progression']:
                    returns_by_day[day].append(event['progression'][day]['cumulative_return_pct'])
        
        days = []
        median_returns = []
        
        for day in self.horizons:
            if returns_by_day[day]:
                days.append(day)
                median_returns.append(np.median(returns_by_day[day]))
        
        trend_analysis = {}
        
        if len(days) >= 3:
            correlation, p_value = pearsonr(days, median_returns)
            
            peak_day = days[np.argmax(median_returns)]
            peak_return = max(median_returns)
            
            # Split into early/middle/late periods for D21
            early_cutoff = self.max_horizon // 3
            late_cutoff = 2 * self.max_horizon // 3
            
            early_returns = []
            late_returns = []
            
            for day in range(1, early_cutoff + 1):
                early_returns.extend(returns_by_day.get(day, []))
            for day in range(late_cutoff + 1, self.max_horizon + 1):
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
    
    def analyze_ticker(self, ticker: str) -> Dict:
        """Analyze single ticker with full D1-D21 analysis."""
        print(f"\n{'='*60}")
        print(f"Analyzing {ticker}...")
        print(f"{'='*60}")
        
        data = self.fetch_data(ticker)
        if data.empty:
            return {}
        
        indicator = self.calculate_rsi_ma_indicator(data['Close'])
        percentile_ranks = self.calculate_percentile_ranks(indicator)
        
        benchmark = self.calculate_enhanced_market_benchmark(data['Close'], ticker)
        
        ticker_results = {
            'ticker': ticker,
            'data_points': len(data),
            'benchmark': benchmark.to_dict(),
            'thresholds': {}
        }
        
        for threshold in self.entry_thresholds:
            print(f"\nProcessing threshold {threshold}%...")
            events = self.find_entry_events_enhanced(percentile_ranks, data['Close'], threshold)
            
            if len(events) < 10:
                print(f"  Insufficient events: {len(events)} (need 10+)")
                continue
            
            print(f"  Found {len(events)} entry events")
            
            performance_matrix = self.build_enhanced_matrix(events)
            risk_metrics = self.calculate_risk_metrics(events)
            win_rates = self.calculate_overall_win_rates(events)
            return_distributions = self.calculate_return_distribution(events)
            percentile_movements = self.analyze_percentile_movements(events)
            trend_analysis = self.analyze_return_trend_significance(events)
            optimal_exit_strategy = self.calculate_optimal_exit_strategy(
                threshold, return_distributions, performance_matrix)
            
            # Convert matrix cells to dicts for JSON serialization
            matrix_dict = {}
            for range_key, range_data in performance_matrix.items():
                matrix_dict[range_key] = {
                    day: cell.to_dict() for day, cell in range_data.items()
                }
            
            ticker_results['thresholds'][threshold] = {
                'events': len(events),
                'performance_matrix': matrix_dict,
                'risk_metrics': risk_metrics.to_dict(),
                'win_rates': win_rates,
                'return_distributions': return_distributions,
                'percentile_movements': percentile_movements,
                'trend_analysis': trend_analysis,
                'optimal_exit_strategy': optimal_exit_strategy
            }
            
            matrix_key = f"{ticker}_{threshold}"
            self.performance_matrices[matrix_key] = performance_matrix
        
        # Verification data
        last_close = data['Close'].iloc[-1]
        prev_close = data['Close'].iloc[-2] 
        daily_return_pct = ((last_close - prev_close) / prev_close) * 100
        last_rsi_ma = indicator.iloc[-1]
        
        ticker_results['verification'] = {
            'last_close': last_close,
            'daily_return_pct': daily_return_pct, 
            'last_rsi_ma': last_rsi_ma
        }
        
        return ticker_results
    
    def get_rsi_percentile_timeseries(self, ticker: str, days: int = 252) -> Dict:
        """
        Get RSI, RSI-MA, and percentile data for chart visualization.
        Returns last N days of data for plotting.
        """
        if ticker not in self.results:
            return {}
        
        data = self.results[ticker]['data']
        prices = data['Close']
        
        # Calculate RSI
        daily_returns = prices.pct_change().fillna(0)
        delta = daily_returns.diff()
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        avg_gains = gains.ewm(alpha=1/self.rsi_length, adjust=False).mean()
        avg_losses = losses.ewm(alpha=1/self.rsi_length, adjust=False).mean()
        
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.fillna(50)
        
        # Calculate RSI-MA
        rsi_ma = rsi.ewm(span=self.ma_length, adjust=False).mean()
        
        # Calculate percentile ranks
        percentile_ranks = self.calculate_percentile_ranks(rsi_ma)
        
        # Get last N days
        last_days = min(days, len(data))
        dates = data.index[-last_days:].strftime('%Y-%m-%d').tolist()
        
        # Calculate percentile thresholds from full historical data
        valid_rsi_ma = rsi_ma.dropna()
        percentiles = {
            'p5': float(np.percentile(valid_rsi_ma, 5)),
            'p15': float(np.percentile(valid_rsi_ma, 15)),
            'p25': float(np.percentile(valid_rsi_ma, 25)),
            'p50': float(np.percentile(valid_rsi_ma, 50)),
            'p75': float(np.percentile(valid_rsi_ma, 75)),
            'p85': float(np.percentile(valid_rsi_ma, 85)),
            'p95': float(np.percentile(valid_rsi_ma, 95))
        }
        
        # Build time series data
        return {
            'dates': dates,
            'rsi': rsi.iloc[-last_days:].fillna(50).tolist(),
            'rsi_ma': rsi_ma.iloc[-last_days:].fillna(50).tolist(),
            'percentile_rank': percentile_ranks.iloc[-last_days:].fillna(50).tolist(),
            'percentile_thresholds': percentiles,
            'current_rsi': float(rsi.iloc[-1]),
            'current_rsi_ma': float(rsi_ma.iloc[-1]),
            'current_percentile': float(percentile_ranks.iloc[-1]) if not pd.isna(percentile_ranks.iloc[-1]) else 50.0
        }
    
    def run_analysis(self) -> Dict:
        """Run full analysis across all tickers."""
        print(f"\n{'='*80}")
        print(f"ENHANCED PERFORMANCE MATRIX BACKTESTER - D1-D{self.max_horizon}")
        print(f"{'='*80}")
        print(f"Analyzing {len(self.tickers)} tickers: {', '.join(self.tickers)}")
        print(f"Entry thresholds: {', '.join(str(t) + '%' for t in self.entry_thresholds)}")
        print(f"Holding period: D1 through D{self.max_horizon}")
        print(f"{'='*80}\n")
        
        start_time = time.time()
        results = {}
        
        for ticker in self.tickers:
            try:
                result = self.analyze_ticker(ticker)
                if result:
                    results[ticker] = result
            except Exception as e:
                print(f"Error analyzing {ticker}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        elapsed_time = time.time() - start_time
        print(f"\n{'='*80}")
        print(f"Analysis completed in {elapsed_time:.1f} seconds")
        print(f"Successfully analyzed {len(results)} tickers")
        print(f"{'='*80}\n")
        
        self.results = results
        return results
    
    def export_to_json(self, filename: str = "backtest_results.json"):
        """Export results to JSON file."""
        if not self.results:
            print("No results to export")
            return
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"Results exported to {filename}")
    
    def print_summary(self):
        """Print summary of results."""
        if not self.results:
            print("No results to display")
            return
        
        print(f"\n{'='*80}")
        print(f"BACKTEST SUMMARY - D1-D{self.max_horizon}")
        print(f"{'='*80}\n")
        
        for ticker, ticker_data in self.results.items():
            print(f"\n{ticker}:")
            print(f"  Data points: {ticker_data['data_points']}")
            
            for threshold, threshold_data in ticker_data.get('thresholds', {}).items():
                events = threshold_data['events']
                risk = threshold_data['risk_metrics']
                optimal_exit = threshold_data.get('optimal_exit_strategy', {})
                
                print(f"\n  Threshold ≤{threshold}% ({events} events):")
                print(f"    Risk: {risk['median_drawdown']:+.2f}% median DD, {risk['p90_drawdown']:+.2f}% P90 DD")
                
                if optimal_exit and 'optimal_day' in optimal_exit:
                    opt_day = optimal_exit['optimal_day']
                    opt_ret = optimal_exit['target_return']
                    opt_eff = optimal_exit['optimal_efficiency']
                    print(f"    Optimal Exit: D{opt_day} ({opt_ret:+.2f}% return, {opt_eff:+.3f}%/day efficiency)")


def main():
    """Main execution function."""
    
    # Default top tickers
    TOP_TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "QQQ", "SPY"]
    
    # Create backtester with D1-D21 horizon
    backtester = EnhancedPerformanceMatrixBacktester(
        tickers=TOP_TICKERS,
        lookback_period=500,
        rsi_length=14,
        ma_length=14,
        max_horizon=21  # Extended to D21
    )
    
    try:
        # Run analysis
        results = backtester.run_analysis()
        
        # Export results
        backtester.export_to_json("backtest_d1_d21_results.json")
        
        # Print summary
        backtester.print_summary()
        
        return backtester
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    backtester = main()
