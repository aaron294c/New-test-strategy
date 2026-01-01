#!/usr/bin/env python3
"""
Advanced Backtest Runner

Integrates AdvancedTradeManager with historical analysis to:
1. Compare buy-and-hold vs managed exits
2. Analyze exit strategy performance
3. Generate optimal exit curves
4. Calculate risk-adjusted returns
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
import json
from advanced_trade_manager import (
    AdvancedTradeManager,
    simulate_trade_with_advanced_management
)


@dataclass
class StrategyPerformance:
    """Performance metrics for a trading strategy."""
    strategy_name: str
    total_trades: int
    avg_return: float
    median_return: float
    win_rate: float
    avg_hold_days: float
    sharpe_ratio: float
    max_drawdown: float
    profit_factor: float  # Gross profit / Gross loss
    expectancy: float  # Avg win * win_rate - Avg loss * loss_rate

    def to_dict(self):
        return asdict(self)


@dataclass
class ExitStrategyComparison:
    """Comparison of different exit strategies."""
    buy_and_hold: StrategyPerformance
    fixed_days: Dict[int, StrategyPerformance]  # Exit at D3, D5, D7, etc.
    trailing_stop_atr: StrategyPerformance
    adaptive_exit_pressure: StrategyPerformance
    conditional_expectancy: StrategyPerformance

    def to_dict(self):
        return {
            'buy_and_hold': self.buy_and_hold.to_dict(),
            'fixed_days': {k: v.to_dict() for k, v in self.fixed_days.items()},
            'trailing_stop_atr': self.trailing_stop_atr.to_dict(),
            'adaptive_exit_pressure': self.adaptive_exit_pressure.to_dict(),
            'conditional_expectancy': self.conditional_expectancy.to_dict()
        }


class AdvancedBacktestRunner:
    """
    Run comprehensive backtests comparing exit strategies.
    """

    def __init__(self,
                 historical_data: pd.DataFrame,
                 rsi_ma_percentiles: pd.Series,
                 entry_events: List[Dict],
                 max_hold_days: int = 21):
        """
        Initialize backtest runner.

        Args:
            historical_data: Full OHLCV data
            rsi_ma_percentiles: RSI-MA percentile series
            entry_events: List of entry events from enhanced_backtester
            max_hold_days: Maximum holding period
        """
        self.data = historical_data
        self.percentiles = rsi_ma_percentiles
        self.entry_events = entry_events
        self.max_hold_days = max_hold_days

    def run_buy_and_hold_strategy(self) -> List[Dict]:
        """
        Baseline: Hold all positions for max_hold_days.

        Returns:
            List of trade results
        """
        results = []

        for event in self.entry_events:
            entry_date = event['entry_date']
            entry_price = event['entry_price']

            # Find entry index
            entry_idx = self.data.index.get_loc(entry_date)

            # Exit at max hold days
            exit_idx = min(entry_idx + self.max_hold_days, len(self.data) - 1)
            exit_price = self.data['Close'].iloc[exit_idx]
            exit_date = self.data.index[exit_idx]

            hold_days = exit_idx - entry_idx
            return_pct = (exit_price / entry_price - 1) * 100

            results.append({
                'entry_date': entry_date,
                'entry_price': entry_price,
                'exit_date': exit_date,
                'exit_price': exit_price,
                'hold_days': hold_days,
                'return_pct': return_pct
            })

        return results

    def run_fixed_day_exit_strategy(self, exit_day: int) -> List[Dict]:
        """
        Exit all positions at a fixed day (D3, D5, D7, etc.).

        Args:
            exit_day: Day to exit (e.g., 3, 5, 7)

        Returns:
            List of trade results
        """
        results = []

        for event in self.entry_events:
            entry_date = event['entry_date']
            entry_price = event['entry_price']

            entry_idx = self.data.index.get_loc(entry_date)

            # Exit at fixed day
            if entry_idx + exit_day < len(self.data):
                exit_idx = entry_idx + exit_day
                exit_price = self.data['Close'].iloc[exit_idx]
                exit_date = self.data.index[exit_idx]

                return_pct = (exit_price / entry_price - 1) * 100

                results.append({
                    'entry_date': entry_date,
                    'entry_price': entry_price,
                    'exit_date': exit_date,
                    'exit_price': exit_price,
                    'hold_days': exit_day,
                    'return_pct': return_pct
                })

        return results

    def run_trailing_stop_strategy(self) -> List[Dict]:
        """
        Exit when ATR-based trailing stop is hit.

        Returns:
            List of trade results
        """
        results = []

        for event in self.entry_events:
            entry_date = event['entry_date']
            entry_price = event['entry_price']
            entry_percentile = event['entry_percentile']

            entry_idx = self.data.index.get_loc(entry_date)

            # Create trade manager
            manager = AdvancedTradeManager(
                historical_data=self.data,
                rsi_ma_percentiles=self.percentiles,
                entry_idx=entry_idx,
                entry_percentile=entry_percentile,
                entry_price=entry_price
            )

            # Simulate with trailing stop
            exit_triggered = False
            exit_day = self.max_hold_days
            exit_price = self.data['Close'].iloc[min(entry_idx + self.max_hold_days, len(self.data) - 1)]

            for day in range(1, self.max_hold_days + 1):
                current_idx = entry_idx + day
                if current_idx >= len(self.data):
                    break

                current_price = self.data['Close'].iloc[current_idx]
                trailing_stop = manager.calculate_trailing_stop_level(current_idx, day)

                if current_price <= trailing_stop:
                    exit_triggered = True
                    exit_day = day
                    exit_price = current_price
                    break

            exit_idx = entry_idx + exit_day
            if exit_idx >= len(self.data):
                exit_idx = len(self.data) - 1

            exit_date = self.data.index[exit_idx]
            return_pct = (exit_price / entry_price - 1) * 100

            results.append({
                'entry_date': entry_date,
                'entry_price': entry_price,
                'exit_date': exit_date,
                'exit_price': exit_price,
                'hold_days': exit_day,
                'return_pct': return_pct,
                'stop_triggered': exit_triggered
            })

        return results

    def run_exit_pressure_strategy(self, pressure_threshold: float = 70) -> List[Dict]:
        """
        Exit when exit pressure exceeds threshold.

        Args:
            pressure_threshold: Exit pressure threshold (0-100)

        Returns:
            List of trade results
        """
        results = []

        for event in self.entry_events:
            entry_date = event['entry_date']
            entry_price = event['entry_price']
            entry_percentile = event['entry_percentile']

            entry_idx = self.data.index.get_loc(entry_date)

            manager = AdvancedTradeManager(
                historical_data=self.data,
                rsi_ma_percentiles=self.percentiles,
                entry_idx=entry_idx,
                entry_percentile=entry_percentile,
                entry_price=entry_price
            )

            exit_triggered = False
            exit_day = self.max_hold_days
            exit_price = self.data['Close'].iloc[min(entry_idx + self.max_hold_days, len(self.data) - 1)]

            for day in range(1, self.max_hold_days + 1):
                current_idx = entry_idx + day
                if current_idx >= len(self.data):
                    break

                exit_pressure = manager.calculate_exit_pressure(current_idx, day)

                if exit_pressure.overall_pressure >= pressure_threshold:
                    exit_triggered = True
                    exit_day = day
                    exit_price = self.data['Close'].iloc[current_idx]
                    break

            exit_idx = entry_idx + exit_day
            if exit_idx >= len(self.data):
                exit_idx = len(self.data) - 1

            exit_date = self.data.index[exit_idx]
            return_pct = (exit_price / entry_price - 1) * 100

            results.append({
                'entry_date': entry_date,
                'entry_price': entry_price,
                'exit_date': exit_date,
                'exit_price': exit_price,
                'hold_days': exit_day,
                'return_pct': return_pct,
                'pressure_triggered': exit_triggered
            })

        return results

    def run_expectancy_based_strategy(self) -> List[Dict]:
        """
        Exit based on conditional expectancy (hold vs exit comparison).

        Returns:
            List of trade results
        """
        results = []

        for event in self.entry_events:
            entry_date = event['entry_date']
            entry_price = event['entry_price']
            entry_percentile = event['entry_percentile']

            entry_idx = self.data.index.get_loc(entry_date)

            manager = AdvancedTradeManager(
                historical_data=self.data,
                rsi_ma_percentiles=self.percentiles,
                entry_idx=entry_idx,
                entry_percentile=entry_percentile,
                entry_price=entry_price
            )

            exit_triggered = False
            exit_day = self.max_hold_days
            exit_price = self.data['Close'].iloc[min(entry_idx + self.max_hold_days, len(self.data) - 1)]

            for day in range(3, self.max_hold_days + 1):  # Start checking after D3
                current_idx = entry_idx + day
                if current_idx >= len(self.data):
                    break

                exposure_rec = manager.generate_exposure_recommendation(
                    current_idx, day, self.entry_events
                )

                # Exit if expectancy favors exit
                if exposure_rec.expected_return_if_exit > exposure_rec.expected_return_if_hold + 0.5:
                    exit_triggered = True
                    exit_day = day
                    exit_price = self.data['Close'].iloc[current_idx]
                    break

            exit_idx = entry_idx + exit_day
            if exit_idx >= len(self.data):
                exit_idx = len(self.data) - 1

            exit_date = self.data.index[exit_idx]
            return_pct = (exit_price / entry_price - 1) * 100

            results.append({
                'entry_date': entry_date,
                'entry_price': entry_price,
                'exit_date': exit_date,
                'exit_price': exit_price,
                'hold_days': exit_day,
                'return_pct': return_pct,
                'expectancy_triggered': exit_triggered
            })

        return results

    def calculate_strategy_metrics(self, trades: List[Dict], strategy_name: str) -> StrategyPerformance:
        """
        Calculate performance metrics for a strategy.

        Args:
            trades: List of trade results
            strategy_name: Name of the strategy

        Returns:
            StrategyPerformance with metrics
        """
        if not trades:
            return StrategyPerformance(
                strategy_name=strategy_name,
                total_trades=0,
                avg_return=0, median_return=0, win_rate=0,
                avg_hold_days=0, sharpe_ratio=0, max_drawdown=0,
                profit_factor=0, expectancy=0
            )

        returns = [t['return_pct'] for t in trades]
        hold_days = [t['hold_days'] for t in trades]

        # Basic stats
        avg_return = np.mean(returns)
        median_return = np.median(returns)
        win_rate = sum(1 for r in returns if r > 0) / len(returns)
        avg_hold_days = np.mean(hold_days)

        # Sharpe ratio (assuming 0% risk-free rate)
        if np.std(returns) > 0:
            sharpe_ratio = avg_return / np.std(returns)
        else:
            sharpe_ratio = 0

        # Max drawdown
        cumulative_returns = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = cumulative_returns - running_max
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0

        # Profit factor
        gross_profit = sum(r for r in returns if r > 0)
        gross_loss = abs(sum(r for r in returns if r < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # Expectancy
        winning_trades = [r for r in returns if r > 0]
        losing_trades = [r for r in returns if r < 0]

        avg_win = np.mean(winning_trades) if winning_trades else 0
        avg_loss = np.mean(losing_trades) if losing_trades else 0
        expectancy = (avg_win * win_rate) + (avg_loss * (1 - win_rate))

        return StrategyPerformance(
            strategy_name=strategy_name,
            total_trades=len(trades),
            avg_return=avg_return,
            median_return=median_return,
            win_rate=win_rate,
            avg_hold_days=avg_hold_days,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            profit_factor=profit_factor,
            expectancy=expectancy
        )

    def run_comprehensive_comparison(self) -> ExitStrategyComparison:
        """
        Run all exit strategies and compare.

        Returns:
            ExitStrategyComparison with all results
        """
        print(f"\n{'='*60}")
        print(f"ADVANCED EXIT STRATEGY COMPARISON")
        print(f"{'='*60}")
        print(f"Total entry events: {len(self.entry_events)}")
        print(f"Max hold days: {self.max_hold_days}")
        print(f"{'='*60}\n")

        # 1. Buy and Hold
        print("Running Buy & Hold strategy...")
        bah_trades = self.run_buy_and_hold_strategy()
        bah_perf = self.calculate_strategy_metrics(bah_trades, "Buy & Hold")
        print(f"  Avg Return: {bah_perf.avg_return:.2f}%, Win Rate: {bah_perf.win_rate*100:.1f}%")

        # 2. Fixed day exits
        print("\nRunning Fixed Day Exit strategies...")
        fixed_day_perfs = {}
        for exit_day in [3, 5, 7, 10, 14, 21]:
            if exit_day <= self.max_hold_days:
                trades = self.run_fixed_day_exit_strategy(exit_day)
                perf = self.calculate_strategy_metrics(trades, f"Exit D{exit_day}")
                fixed_day_perfs[exit_day] = perf
                print(f"  D{exit_day}: Avg Return: {perf.avg_return:.2f}%, Win Rate: {perf.win_rate*100:.1f}%")

        # 3. Trailing stop
        print("\nRunning ATR Trailing Stop strategy...")
        trailing_trades = self.run_trailing_stop_strategy()
        trailing_perf = self.calculate_strategy_metrics(trailing_trades, "ATR Trailing Stop")
        print(f"  Avg Return: {trailing_perf.avg_return:.2f}%, Win Rate: {trailing_perf.win_rate*100:.1f}%")
        print(f"  Avg Hold Days: {trailing_perf.avg_hold_days:.1f}")

        # 4. Exit pressure
        print("\nRunning Exit Pressure strategy...")
        pressure_trades = self.run_exit_pressure_strategy(pressure_threshold=70)
        pressure_perf = self.calculate_strategy_metrics(pressure_trades, "Exit Pressure")
        print(f"  Avg Return: {pressure_perf.avg_return:.2f}%, Win Rate: {pressure_perf.win_rate*100:.1f}%")
        print(f"  Avg Hold Days: {pressure_perf.avg_hold_days:.1f}")

        # 5. Conditional expectancy
        print("\nRunning Conditional Expectancy strategy...")
        expectancy_trades = self.run_expectancy_based_strategy()
        expectancy_perf = self.calculate_strategy_metrics(expectancy_trades, "Conditional Expectancy")
        print(f"  Avg Return: {expectancy_perf.avg_return:.2f}%, Win Rate: {expectancy_perf.win_rate*100:.1f}%")
        print(f"  Avg Hold Days: {expectancy_perf.avg_hold_days:.1f}")

        print(f"\n{'='*60}")
        print("Comparison complete!")
        print(f"{'='*60}\n")

        return ExitStrategyComparison(
            buy_and_hold=bah_perf,
            fixed_days=fixed_day_perfs,
            trailing_stop_atr=trailing_perf,
            adaptive_exit_pressure=pressure_perf,
            conditional_expectancy=expectancy_perf
        )

    def generate_optimal_exit_curve(self) -> Dict:
        """
        Generate optimal exit curve based on backtesting.

        Returns mapping: day -> recommended_action_threshold
        """
        print("\n📊 Generating Optimal Exit Curve...")

        # Analyze performance at each day
        day_analysis = {}

        for day in range(1, self.max_hold_days + 1):
            day_returns = []

            for event in self.entry_events:
                if day in event['progression']:
                    day_returns.append(event['progression'][day]['cumulative_return_pct'])

            if day_returns:
                day_analysis[day] = {
                    'median_return': np.median(day_returns),
                    'mean_return': np.mean(day_returns),
                    'win_rate': sum(1 for r in day_returns if r > 0) / len(day_returns),
                    'sample_size': len(day_returns),
                    'return_efficiency': np.median(day_returns) / day  # Return per day
                }

        # Find optimal exit day (max efficiency)
        if day_analysis:
            optimal_day = max(day_analysis.keys(),
                            key=lambda d: day_analysis[d]['return_efficiency'])

            print(f"  Optimal exit day: D{optimal_day}")
            print(f"  Efficiency: {day_analysis[optimal_day]['return_efficiency']:.3f}%/day")
            print(f"  Median return: {day_analysis[optimal_day]['median_return']:.2f}%")

        return {
            'day_analysis': day_analysis,
            'optimal_day': optimal_day if day_analysis else None
        }

    def export_results(self, comparison: ExitStrategyComparison, filename: str = "advanced_backtest_results.json"):
        """Export comparison results to JSON."""

        results = {
            'strategy_comparison': comparison.to_dict(),
            'optimal_exit_curve': self.generate_optimal_exit_curve()
        }

        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n✓ Results exported to {filename}")

        return results


def run_advanced_backtest(ticker: str,
                          historical_data: pd.DataFrame,
                          rsi_ma_percentiles: pd.Series,
                          entry_events: List[Dict],
                          max_hold_days: int = 21) -> Dict:
    """
    Convenience function to run advanced backtest.

    Args:
        ticker: Stock ticker
        historical_data: OHLCV data
        rsi_ma_percentiles: Percentile series
        entry_events: Entry events from enhanced_backtester
        max_hold_days: Max holding period

    Returns:
        Dictionary with comparison results
    """
    print(f"\n🚀 Running Advanced Backtest for {ticker}")

    runner = AdvancedBacktestRunner(
        historical_data=historical_data,
        rsi_ma_percentiles=rsi_ma_percentiles,
        entry_events=entry_events,
        max_hold_days=max_hold_days
    )

    comparison = runner.run_comprehensive_comparison()
    results = runner.export_results(comparison, f"advanced_backtest_{ticker}.json")

    return results


if __name__ == "__main__":
    print("Advanced Backtest Runner")
    print("Import and use with enhanced_backtester.py data")
