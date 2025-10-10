#!/usr/bin/env python3
"""
Monte Carlo Simulation Engine for RSI-MA Strategy

Based on First Passage Time methodology (inspired by TradingView indicator)
Provides forward-looking probability distributions for:
- Percentile movement paths
- Expected return distributions
- Exit timing optimization
- First passage times to target percentiles
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import json

@dataclass
class SimulationParameters:
    """Parameters for Monte Carlo simulation."""
    drift: float
    volatility: float
    current_percentile: float
    current_price: float
    num_simulations: int
    max_periods: int
    
    def to_dict(self):
        return asdict(self)

@dataclass
class FirstPassageResults:
    """Results from first passage time analysis."""
    target_percentile: float
    median_days: float
    p25_days: float
    p75_days: float
    probability: float  # Probability of reaching target within max_periods
    
    def to_dict(self):
        return asdict(self)

class MonteCarloSimulator:
    """
    Forward-looking Monte Carlo simulation for RSI-MA strategy.
    Based on First Passage Time methodology.
    """
    
    def __init__(self, 
                 ticker: str,
                 current_rsi_ma_percentile: float,
                 current_price: float,
                 historical_percentile_data: pd.Series,
                 historical_price_data: pd.Series,
                 num_simulations: int = 1000,
                 max_periods: int = 21):
        """
        Initialize Monte Carlo simulator.
        
        Args:
            ticker: Stock ticker symbol
            current_rsi_ma_percentile: Current RSI-MA percentile rank (0-100)
            current_price: Current stock price
            historical_percentile_data: Historical RSI-MA percentile values
            historical_price_data: Historical price data
            num_simulations: Number of Monte Carlo paths to simulate
            max_periods: Maximum number of periods to simulate (days)
        """
        self.ticker = ticker
        self.current_percentile = current_rsi_ma_percentile
        self.current_price = current_price
        self.num_simulations = num_simulations
        self.max_periods = max_periods
        
        # Calculate drift and volatility from historical data
        self.params = self.calculate_parameters(
            historical_percentile_data, 
            historical_price_data
        )
        
        # Storage for simulation results
        self.simulation_paths = []
        self.price_paths = []
        
    def calculate_parameters(self, 
                            percentile_series: pd.Series,
                            price_series: pd.Series) -> SimulationParameters:
        """
        Calculate drift and volatility from historical data.
        
        For percentile movements: Use arithmetic changes
        For price movements: Use log returns
        """
        # Percentile drift and volatility
        percentile_changes = percentile_series.diff().dropna()
        percentile_drift = percentile_changes.mean()
        percentile_volatility = percentile_changes.std()
        
        # Price drift and volatility (for return simulations)
        price_returns = np.log(price_series / price_series.shift(1)).dropna()
        price_drift = price_returns.mean()
        price_volatility = price_returns.std()
        
        print(f"\n{self.ticker} Simulation Parameters:")
        print(f"  Percentile Drift: {percentile_drift:.4f}/day")
        print(f"  Percentile Volatility: {percentile_volatility:.4f}")
        print(f"  Price Drift: {price_drift:.6f}/day ({price_drift * 252 * 100:.2f}% annualized)")
        print(f"  Price Volatility: {price_volatility:.6f}/day ({price_volatility * np.sqrt(252) * 100:.2f}% annualized)")
        
        return SimulationParameters(
            drift=percentile_drift,
            volatility=percentile_volatility,
            current_percentile=self.current_percentile,
            current_price=self.current_price,
            num_simulations=self.num_simulations,
            max_periods=self.max_periods
        )
    
    def run_simulations(self) -> Dict:
        """
        Run Monte Carlo simulations for percentile and price movements.
        
        Returns:
            Dictionary containing:
            - percentile_paths: All simulated percentile paths
            - price_paths: All simulated price paths
            - percentile_statistics: Statistics by day
            - return_statistics: Return statistics by day
        """
        print(f"\nRunning {self.num_simulations} Monte Carlo simulations for {self.ticker}...")
        
        percentile_by_day = {day: [] for day in range(0, self.max_periods + 1)}
        returns_by_day = {day: [] for day in range(1, self.max_periods + 1)}
        
        self.simulation_paths = []
        self.price_paths = []
        
        for sim in range(self.num_simulations):
            current_percentile = self.current_percentile
            current_price = self.current_price
            
            sim_percentile_path = [current_percentile]
            sim_price_path = [current_price]
            
            for day in range(1, self.max_periods + 1):
                # Simulate percentile movement (arithmetic)
                z_percentile = np.random.standard_normal()
                percentile_change = self.params.drift + self.params.volatility * z_percentile
                current_percentile = current_percentile + percentile_change
                
                # Bound percentiles to 0-100 range
                current_percentile = max(0, min(100, current_percentile))
                
                # Simulate price movement (geometric Brownian motion)
                z_price = np.random.standard_normal()
                # Using actual price drift/vol would require separate calculation
                # For now, keep it simple with percentile-based simulation
                
                sim_percentile_path.append(current_percentile)
                percentile_by_day[day].append(current_percentile)
            
            self.simulation_paths.append(sim_percentile_path)
        
        # Calculate statistics by day
        percentile_statistics = {}
        for day in range(0, self.max_periods + 1):
            if percentile_by_day[day]:
                values = np.array(percentile_by_day[day])
                percentile_statistics[day] = {
                    'median': np.median(values),
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'p10': np.percentile(values, 10),
                    'p25': np.percentile(values, 25),
                    'p75': np.percentile(values, 75),
                    'p90': np.percentile(values, 90),
                    'min': np.min(values),
                    'max': np.max(values)
                }
        
        print(f"✓ Completed {self.num_simulations} simulations")
        
        return {
            'percentile_paths': self.simulation_paths,
            'percentile_statistics': percentile_statistics,
            'parameters': self.params.to_dict()
        }
    
    def calculate_first_passage_times(self, 
                                     target_percentiles: List[float] = [25, 50, 75, 90]) -> Dict[float, FirstPassageResults]:
        """
        Calculate expected time to reach target percentile levels.
        Similar to First Passage Time indicator from TradingView.
        
        Args:
            target_percentiles: List of target percentile levels to analyze
            
        Returns:
            Dictionary mapping target percentile to FirstPassageResults
        """
        print(f"\nCalculating First Passage Times for {self.ticker}...")
        print(f"  Targets: {target_percentiles}")
        print(f"  Current percentile: {self.current_percentile:.1f}")
        
        # Only analyze targets above current percentile (upward movement)
        viable_targets = [t for t in target_percentiles if t > self.current_percentile]
        
        if not viable_targets:
            print(f"  No viable targets (all below current percentile)")
            return {}
        
        passage_times = {target: [] for target in viable_targets}
        
        # Run simulations
        for sim in range(self.num_simulations):
            current_percentile = self.current_percentile
            hit_targets = set()
            
            for day in range(1, self.max_periods + 1):
                # Simulate percentile movement
                z = np.random.standard_normal()
                change = self.params.drift + self.params.volatility * z
                current_percentile = current_percentile + change
                current_percentile = max(0, min(100, current_percentile))
                
                # Check if we've hit any target percentiles
                for target in viable_targets:
                    if target not in hit_targets and current_percentile >= target:
                        passage_times[target].append(day)
                        hit_targets.add(target)
        
        # Calculate statistics
        results = {}
        for target, times in passage_times.items():
            if times:
                results[target] = FirstPassageResults(
                    target_percentile=target,
                    median_days=float(np.median(times)),
                    p25_days=float(np.percentile(times, 25)),
                    p75_days=float(np.percentile(times, 75)),
                    probability=len(times) / self.num_simulations * 100
                )
                
                print(f"  {target}th percentile: "
                      f"median {results[target].median_days:.1f} days, "
                      f"prob {results[target].probability:.1f}%")
            else:
                print(f"  {target}th percentile: Never reached")
        
        return results
    
    def calculate_exit_timing_distribution(self, 
                                          profit_target_pct: float = 5.0,
                                          percentile_exit_threshold: float = 50) -> Dict:
        """
        Calculate distribution of optimal exit times based on:
        1. Reaching profit target
        2. Percentile crossing threshold (mean reversion signal)
        
        Returns:
            Statistics on when to exit based on different criteria
        """
        print(f"\nCalculating Exit Timing Distribution...")
        print(f"  Profit target: {profit_target_pct}%")
        print(f"  Percentile exit threshold: {percentile_exit_threshold}")
        
        profit_target_days = []
        percentile_exit_days = []
        combined_exit_days = []
        
        for sim in range(self.num_simulations):
            current_percentile = self.current_percentile
            profit_hit_day = None
            percentile_hit_day = None
            
            for day in range(1, self.max_periods + 1):
                # Simulate percentile movement
                z = np.random.standard_normal()
                change = self.params.drift + self.params.volatility * z
                current_percentile = current_percentile + change
                current_percentile = max(0, min(100, current_percentile))
                
                # Check percentile exit
                if percentile_hit_day is None and current_percentile >= percentile_exit_threshold:
                    percentile_hit_day = day
                    percentile_exit_days.append(day)
                
                # For combined strategy: exit at first of either condition
                if profit_hit_day is None and percentile_hit_day is None:
                    if percentile_hit_day is not None:
                        combined_exit_days.append(day)
        
        results = {
            'percentile_exit': {
                'median_days': float(np.median(percentile_exit_days)) if percentile_exit_days else None,
                'p25_days': float(np.percentile(percentile_exit_days, 25)) if percentile_exit_days else None,
                'p75_days': float(np.percentile(percentile_exit_days, 75)) if percentile_exit_days else None,
                'probability': len(percentile_exit_days) / self.num_simulations * 100,
                'sample_size': len(percentile_exit_days)
            }
        }
        
        if percentile_exit_days:
            print(f"  Percentile exit ({percentile_exit_threshold}): "
                  f"median {results['percentile_exit']['median_days']:.1f} days, "
                  f"prob {results['percentile_exit']['probability']:.1f}%")
        
        return results
    
    def generate_fan_chart_data(self, 
                               confidence_intervals: List[int] = [50, 68, 95]) -> Dict:
        """
        Generate fan chart data showing percentile paths with confidence bands.
        
        Args:
            confidence_intervals: List of confidence intervals to calculate (e.g., [50, 68, 95])
            
        Returns:
            Dictionary with median path and confidence bands for each day
        """
        if not self.simulation_paths:
            self.run_simulations()
        
        fan_chart = {
            'days': list(range(0, self.max_periods + 1)),
            'median': [],
            'bands': {ci: {'lower': [], 'upper': []} for ci in confidence_intervals}
        }
        
        for day in range(0, self.max_periods + 1):
            day_values = [path[day] for path in self.simulation_paths if day < len(path)]
            
            if day_values:
                fan_chart['median'].append(float(np.median(day_values)))
                
                for ci in confidence_intervals:
                    lower_pct = (100 - ci) / 2
                    upper_pct = 100 - lower_pct
                    
                    fan_chart['bands'][ci]['lower'].append(float(np.percentile(day_values, lower_pct)))
                    fan_chart['bands'][ci]['upper'].append(float(np.percentile(day_values, upper_pct)))
        
        return fan_chart
    
    def export_results(self, filename: str = None):
        """Export simulation results to JSON."""
        if filename is None:
            filename = f"monte_carlo_{self.ticker}.json"
        
        results = {
            'ticker': self.ticker,
            'parameters': self.params.to_dict(),
            'simulation_summary': {
                'num_simulations': self.num_simulations,
                'max_periods': self.max_periods
            }
        }
        
        # Add simulation results if available
        if self.simulation_paths:
            sim_results = self.run_simulations()
            results['percentile_statistics'] = sim_results['percentile_statistics']
        
        # Add first passage times
        fpt_results = self.calculate_first_passage_times()
        results['first_passage_times'] = {
            str(k): v.to_dict() for k, v in fpt_results.items()
        }
        
        # Add fan chart data
        results['fan_chart'] = self.generate_fan_chart_data()
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ Results exported to {filename}")
        return results


def run_monte_carlo_for_ticker(ticker: str,
                               current_percentile: float,
                               current_price: float,
                               historical_data: pd.DataFrame,
                               num_simulations: int = 1000) -> Dict:
    """
    Convenience function to run Monte Carlo simulation for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        current_percentile: Current RSI-MA percentile
        current_price: Current stock price
        historical_data: DataFrame with historical price and percentile data
        num_simulations: Number of simulations to run
        
    Returns:
        Dictionary of simulation results
    """
    # Assume historical_data has 'rsi_ma_percentile' and 'Close' columns
    simulator = MonteCarloSimulator(
        ticker=ticker,
        current_rsi_ma_percentile=current_percentile,
        current_price=current_price,
        historical_percentile_data=historical_data['rsi_ma_percentile'],
        historical_price_data=historical_data['Close'],
        num_simulations=num_simulations,
        max_periods=21
    )
    
    # Run full simulation suite
    sim_results = simulator.run_simulations()
    fpt_results = simulator.calculate_first_passage_times()
    exit_timing = simulator.calculate_exit_timing_distribution()
    fan_chart = simulator.generate_fan_chart_data()
    
    return {
        'simulation_results': sim_results,
        'first_passage_times': {str(k): v.to_dict() for k, v in fpt_results.items()},
        'exit_timing': exit_timing,
        'fan_chart': fan_chart,
        'parameters': simulator.params.to_dict()
    }


if __name__ == "__main__":
    # Example usage
    print("Monte Carlo Simulator Module")
    print("Import this module to use in your backtesting pipeline")
