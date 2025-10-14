#!/usr/bin/env python3
"""
Percentile Threshold Analyzer

Analyzes historical RSI-MA percentile combinations to find optimal thresholds
for each of the 4 divergence categories.

Outputs a clear decision matrix:
IF Daily=X% AND 4H=Y% THEN Action (with historical win rate)
"""

import numpy as np
import pandas as pd
from multi_timeframe_analyzer import MultiTimeframeAnalyzer
from typing import Dict, List, Tuple
import json


class PercentileThresholdAnalyzer:
    """
    Analyzes historical percentile combinations to determine optimal thresholds.

    For each of the 4 categories, finds:
    - What percentile ranges define the category
    - What forward returns were observed
    - What the optimal action is
    """

    def __init__(self, ticker: str):
        """Initialize with a ticker and run multi-timeframe analysis."""
        self.ticker = ticker
        self.analyzer = MultiTimeframeAnalyzer(ticker)

        # Get the divergence series with all historical data
        self.div_series = self.analyzer.calculate_divergence_series()

        # Get backtested events
        self.events = self.analyzer.backtest_divergence_signals()

    def analyze_percentile_distributions(self) -> Dict:
        """
        Analyze the distribution of percentiles for each category.

        Returns:
            Statistics showing percentile ranges for each category
        """
        results = {
            'daily_overall': {
                'min': float(self.div_series['daily_pct'].min()),
                'p10': float(self.div_series['daily_pct'].quantile(0.10)),
                'p25': float(self.div_series['daily_pct'].quantile(0.25)),
                'median': float(self.div_series['daily_pct'].median()),
                'p75': float(self.div_series['daily_pct'].quantile(0.75)),
                'p90': float(self.div_series['daily_pct'].quantile(0.90)),
                'max': float(self.div_series['daily_pct'].max())
            },
            '4h_overall': {
                'min': float(self.div_series['4h_pct'].min()),
                'p10': float(self.div_series['4h_pct'].quantile(0.10)),
                'p25': float(self.div_series['4h_pct'].quantile(0.25)),
                'median': float(self.div_series['4h_pct'].median()),
                'p75': float(self.div_series['4h_pct'].quantile(0.75)),
                'p90': float(self.div_series['4h_pct'].quantile(0.90)),
                'max': float(self.div_series['4h_pct'].max())
            },
            'by_category': {}
        }

        # Analyze each category
        for category in ['4h_overextended', 'bullish_convergence',
                        'daily_overextended', 'bearish_convergence']:
            cat_data = self.div_series[self.div_series['divergence_category'] == category]

            if len(cat_data) > 0:
                results['by_category'][category] = {
                    'count': len(cat_data),
                    'daily_range': {
                        'min': float(cat_data['daily_pct'].min()),
                        'p10': float(cat_data['daily_pct'].quantile(0.10)),
                        'p25': float(cat_data['daily_pct'].quantile(0.25)),
                        'median': float(cat_data['daily_pct'].median()),
                        'p75': float(cat_data['daily_pct'].quantile(0.75)),
                        'p90': float(cat_data['daily_pct'].quantile(0.90)),
                        'max': float(cat_data['daily_pct'].max())
                    },
                    '4h_range': {
                        'min': float(cat_data['4h_pct'].min()),
                        'p10': float(cat_data['4h_pct'].quantile(0.10)),
                        'p25': float(cat_data['4h_pct'].quantile(0.25)),
                        'median': float(cat_data['4h_pct'].median()),
                        'p75': float(cat_data['4h_pct'].quantile(0.75)),
                        'p90': float(cat_data['4h_pct'].quantile(0.90)),
                        'max': float(cat_data['4h_pct'].max())
                    },
                    'divergence_range': {
                        'min': float(cat_data['divergence_pct'].min()),
                        'p10': float(cat_data['divergence_pct'].quantile(0.10)),
                        'p25': float(cat_data['divergence_pct'].quantile(0.25)),
                        'median': float(cat_data['divergence_pct'].median()),
                        'p75': float(cat_data['divergence_pct'].quantile(0.75)),
                        'p90': float(cat_data['divergence_pct'].quantile(0.90)),
                        'max': float(cat_data['divergence_pct'].max())
                    }
                }

        return results

    def create_percentile_grid_analysis(self,
                                       daily_bins: List[Tuple[float, float]] = None,
                                       h4_bins: List[Tuple[float, float]] = None) -> pd.DataFrame:
        """
        Create a grid analysis showing performance for different percentile combinations.

        Args:
            daily_bins: List of (min, max) tuples for daily percentile ranges
            h4_bins: List of (min, max) tuples for 4H percentile ranges

        Returns:
            DataFrame with grid analysis
        """
        if daily_bins is None:
            daily_bins = [
                (0, 20),    # Very oversold
                (20, 30),   # Oversold
                (30, 40),   # Slightly oversold
                (40, 60),   # Neutral
                (60, 70),   # Slightly overbought
                (70, 80),   # Overbought
                (80, 100)   # Very overbought
            ]

        if h4_bins is None:
            h4_bins = [
                (0, 20),    # Very oversold
                (20, 30),   # Oversold
                (30, 40),   # Slightly oversold
                (40, 60),   # Neutral
                (60, 70),   # Slightly overbought
                (70, 80),   # Overbought
                (80, 100)   # Very overbought
            ]

        results = []

        for daily_min, daily_max in daily_bins:
            for h4_min, h4_max in h4_bins:
                # Filter events in this range
                matching_events = [
                    e for e in self.events
                    if daily_min <= e.daily_percentile < daily_max
                    and h4_min <= e.hourly_4h_percentile < h4_max
                ]

                if len(matching_events) >= 3:  # Need at least 3 events
                    # Calculate statistics
                    avg_div = np.mean([e.divergence_pct for e in matching_events])

                    # Get most common category
                    categories = [e.divergence_type for e in matching_events]
                    most_common_cat = max(set(categories), key=categories.count)
                    cat_pct = categories.count(most_common_cat) / len(categories) * 100

                    # Calculate forward returns
                    returns_d1 = [e.forward_returns.get('D1', 0) for e in matching_events]
                    returns_d3 = [e.forward_returns.get('D3', 0) for e in matching_events]
                    returns_d7 = [e.forward_returns.get('D7', 0) for e in matching_events]
                    returns_d14 = [e.forward_returns.get('D14', 0) for e in matching_events]

                    results.append({
                        'daily_range': f'{daily_min}-{daily_max}%',
                        '4h_range': f'{h4_min}-{h4_max}%',
                        'count': len(matching_events),
                        'avg_divergence': round(avg_div, 1),
                        'primary_category': most_common_cat,
                        'category_confidence': round(cat_pct, 1),
                        'avg_return_d1': round(np.mean(returns_d1), 2),
                        'avg_return_d3': round(np.mean(returns_d3), 2),
                        'avg_return_d7': round(np.mean(returns_d7), 2),
                        'avg_return_d14': round(np.mean(returns_d14), 2),
                        'win_rate_d7': round(sum(1 for r in returns_d7 if r > 0) / len(returns_d7) * 100, 1),
                        'best_return_d7': round(max(returns_d7), 2),
                        'worst_return_d7': round(min(returns_d7), 2)
                    })

        return pd.DataFrame(results)

    def find_optimal_thresholds_by_category(self) -> Dict:
        """
        For each category, find the optimal percentile thresholds that maximize edge.

        Tests various threshold combinations and finds which produces best returns.
        """
        results = {}

        # Category 1: 4H Overextended (Daily < X, 4H > Y, Divergence < Z)
        # Expected: Negative returns (4H pulls back)
        category_events = [e for e in self.events if e.divergence_type == '4h_overextended']
        if len(category_events) >= 10:
            results['4h_overextended'] = self._optimize_thresholds(
                category_events,
                category_name='4h_overextended',
                expectation='negative'
            )

        # Category 2: Bullish Convergence (Both < X, |Divergence| < Y)
        # Expected: Positive returns (bounce)
        category_events = [e for e in self.events if e.divergence_type == 'bullish_convergence']
        if len(category_events) >= 10:
            results['bullish_convergence'] = self._optimize_thresholds(
                category_events,
                category_name='bullish_convergence',
                expectation='positive'
            )

        # Category 3: Daily Overextended (Daily > X, 4H < Y, Divergence > Z)
        # Expected: Negative returns (daily reverses)
        category_events = [e for e in self.events if e.divergence_type == 'daily_overextended']
        if len(category_events) >= 10:
            results['daily_overextended'] = self._optimize_thresholds(
                category_events,
                category_name='daily_overextended',
                expectation='negative'
            )

        # Category 4: Bearish Convergence (Both > X, |Divergence| < Y)
        # Expected: Negative returns (reversal)
        category_events = [e for e in self.events if e.divergence_type == 'bearish_convergence']
        if len(category_events) >= 10:
            results['bearish_convergence'] = self._optimize_thresholds(
                category_events,
                category_name='bearish_convergence',
                expectation='negative'
            )

        return results

    def _optimize_thresholds(self, events, category_name: str, expectation: str) -> Dict:
        """
        Optimize thresholds for a specific category.

        Tests different strength thresholds (weak/moderate/strong) based on
        divergence magnitude and finds which produces best risk-adjusted returns.
        """
        if len(events) == 0:
            return {}

        # Get percentile statistics
        daily_percentiles = [e.daily_percentile for e in events]
        h4_percentiles = [e.hourly_4h_percentile for e in events]
        divergences = [abs(e.divergence_pct) for e in events]

        # Test different divergence thresholds for strength classification
        div_thresholds_to_test = [
            (15, 25, 35),  # weak, moderate, strong
            (20, 30, 40),
            (20, 35, 50),
            (15, 30, 45)
        ]

        best_threshold_set = None
        best_sharpe = -999
        best_performance = {}

        for weak_thresh, mod_thresh, strong_thresh in div_thresholds_to_test:
            # Classify events by strength
            weak_events = [e for e in events if abs(e.divergence_pct) < mod_thresh]
            moderate_events = [e for e in events if mod_thresh <= abs(e.divergence_pct) < strong_thresh]
            strong_events = [e for e in events if abs(e.divergence_pct) >= strong_thresh]

            # Calculate performance for each strength level
            performance = {}
            for strength, strength_events in [('weak', weak_events),
                                             ('moderate', moderate_events),
                                             ('strong', strong_events)]:
                if len(strength_events) >= 5:
                    returns_d7 = [e.forward_returns.get('D7', 0) for e in strength_events]

                    # Flip returns if expecting negative
                    if expectation == 'negative':
                        returns_d7 = [-r for r in returns_d7]

                    avg_return = np.mean(returns_d7)
                    std_return = np.std(returns_d7)
                    sharpe = avg_return / (std_return + 1e-6)

                    performance[strength] = {
                        'count': len(strength_events),
                        'avg_return_d7': round(avg_return if expectation == 'positive' else -avg_return, 2),
                        'sharpe': round(sharpe, 2),
                        'win_rate': round(sum(1 for r in returns_d7 if r > 0) / len(returns_d7) * 100, 1)
                    }

            # Calculate overall Sharpe (weighted by strong signals)
            if 'strong' in performance:
                overall_sharpe = performance['strong']['sharpe']

                if overall_sharpe > best_sharpe:
                    best_sharpe = overall_sharpe
                    best_threshold_set = (weak_thresh, mod_thresh, strong_thresh)
                    best_performance = performance

        # Calculate optimal percentile ranges
        result = {
            'count': len(events),
            'daily_percentile_range': {
                'min': round(min(daily_percentiles), 1),
                'p25': round(np.percentile(daily_percentiles, 25), 1),
                'median': round(np.median(daily_percentiles), 1),
                'p75': round(np.percentile(daily_percentiles, 75), 1),
                'max': round(max(daily_percentiles), 1)
            },
            '4h_percentile_range': {
                'min': round(min(h4_percentiles), 1),
                'p25': round(np.percentile(h4_percentiles, 25), 1),
                'median': round(np.median(h4_percentiles), 1),
                'p75': round(np.percentile(h4_percentiles, 75), 1),
                'max': round(max(h4_percentiles), 1)
            },
            'divergence_range': {
                'min': round(min(divergences), 1),
                'p25': round(np.percentile(divergences, 25), 1),
                'median': round(np.median(divergences), 1),
                'p75': round(np.percentile(divergences, 75), 1),
                'max': round(max(divergences), 1)
            },
            'optimal_thresholds': {
                'weak_threshold': best_threshold_set[0] if best_threshold_set else None,
                'moderate_threshold': best_threshold_set[1] if best_threshold_set else None,
                'strong_threshold': best_threshold_set[2] if best_threshold_set else None
            },
            'performance_by_strength': best_performance,
            'expectation': expectation
        }

        return result

    def generate_decision_matrix(self) -> pd.DataFrame:
        """
        Generate a clear decision matrix:
        IF Daily=X% AND 4H=Y% THEN Action (with historical performance)
        """
        rows = []

        # Define specific combinations to test
        scenarios = [
            # 4H Overextended scenarios
            {'daily': (0, 30), '4h': (70, 100), 'expected_category': '4h_overextended'},
            {'daily': (0, 40), '4h': (60, 100), 'expected_category': '4h_overextended'},
            {'daily': (30, 50), '4h': (70, 100), 'expected_category': '4h_overextended'},

            # Bullish Convergence scenarios
            {'daily': (0, 20), '4h': (0, 20), 'expected_category': 'bullish_convergence'},
            {'daily': (0, 30), '4h': (0, 30), 'expected_category': 'bullish_convergence'},
            {'daily': (20, 30), '4h': (20, 35), 'expected_category': 'bullish_convergence'},

            # Daily Overextended scenarios
            {'daily': (70, 100), '4h': (0, 30), 'expected_category': 'daily_overextended'},
            {'daily': (60, 100), '4h': (0, 40), 'expected_category': 'daily_overextended'},
            {'daily': (70, 100), '4h': (30, 50), 'expected_category': 'daily_overextended'},

            # Bearish Convergence scenarios
            {'daily': (70, 100), '4h': (70, 100), 'expected_category': 'bearish_convergence'},
            {'daily': (75, 100), '4h': (75, 100), 'expected_category': 'bearish_convergence'},
            {'daily': (80, 100), '4h': (70, 100), 'expected_category': 'bearish_convergence'},
        ]

        for scenario in scenarios:
            daily_min, daily_max = scenario['daily']
            h4_min, h4_max = scenario['4h']
            expected_cat = scenario['expected_category']

            # Filter events
            matching_events = [
                e for e in self.events
                if daily_min <= e.daily_percentile < daily_max
                and h4_min <= e.hourly_4h_percentile < h4_max
            ]

            if len(matching_events) >= 3:
                # Calculate statistics
                returns_d7 = [e.forward_returns.get('D7', 0) for e in matching_events]
                returns_d14 = [e.forward_returns.get('D14', 0) for e in matching_events]

                avg_div = np.mean([e.divergence_pct for e in matching_events])

                # Determine action based on expected category
                if expected_cat == '4h_overextended':
                    if abs(avg_div) > 35:
                        action = 'Take Profit 75%'
                    elif abs(avg_div) > 25:
                        action = 'Take Profit 50%'
                    else:
                        action = 'Take Profit 25%'
                elif expected_cat == 'bullish_convergence':
                    action = 'Buy/Add Position'
                elif expected_cat == 'daily_overextended':
                    if abs(avg_div) > 35:
                        action = 'Exit/Short'
                    elif abs(avg_div) > 25:
                        action = 'Reduce 50%'
                    else:
                        action = 'Tighten Stops'
                elif expected_cat == 'bearish_convergence':
                    action = 'Exit All/Short'
                else:
                    action = 'Hold'

                rows.append({
                    'Daily_Range': f'{daily_min}-{daily_max}%',
                    '4H_Range': f'{h4_min}-{h4_max}%',
                    'Avg_Divergence': round(avg_div, 1),
                    'Category': expected_cat,
                    'Recommended_Action': action,
                    'Sample_Size': len(matching_events),
                    'Avg_Return_D7': round(np.mean(returns_d7), 2),
                    'Avg_Return_D14': round(np.mean(returns_d14), 2),
                    'Win_Rate_D7': round(sum(1 for r in returns_d7 if r > 0) / len(returns_d7) * 100, 1),
                    'Best_Return_D7': round(max(returns_d7), 2),
                    'Worst_Return_D7': round(min(returns_d7), 2)
                })

        return pd.DataFrame(rows)


def run_percentile_threshold_analysis(ticker: str = 'GOOGL'):
    """
    Run complete percentile threshold analysis.

    Generates:
    1. Percentile distribution statistics
    2. Grid analysis of all combinations
    3. Optimal thresholds for each category
    4. Decision matrix
    """
    print(f"\n{'='*80}")
    print(f"PERCENTILE THRESHOLD ANALYSIS: {ticker}")
    print(f"{'='*80}\n")

    analyzer = PercentileThresholdAnalyzer(ticker)

    # 1. Analyze percentile distributions
    print("1. PERCENTILE DISTRIBUTIONS BY CATEGORY")
    print("-" * 80)
    distributions = analyzer.analyze_percentile_distributions()

    print("\nOverall Daily Percentile Distribution:")
    for key, value in distributions['daily_overall'].items():
        print(f"  {key}: {value:.1f}%")

    print("\nOverall 4H Percentile Distribution:")
    for key, value in distributions['4h_overall'].items():
        print(f"  {key}: {value:.1f}%")

    print("\nBy Category:")
    for category, stats in distributions['by_category'].items():
        print(f"\n  {category.upper().replace('_', ' ')} (n={stats['count']}):")
        print(f"    Daily Range: {stats['daily_range']['min']:.1f}% - {stats['daily_range']['max']:.1f}% (median: {stats['daily_range']['median']:.1f}%)")
        print(f"    4H Range: {stats['4h_range']['min']:.1f}% - {stats['4h_range']['max']:.1f}% (median: {stats['4h_range']['median']:.1f}%)")
        print(f"    Divergence Range: {stats['divergence_range']['min']:.1f}% - {stats['divergence_range']['max']:.1f}% (median: {stats['divergence_range']['median']:.1f}%)")

    # 2. Find optimal thresholds
    print("\n\n2. OPTIMAL THRESHOLDS BY CATEGORY")
    print("-" * 80)
    optimal_thresholds = analyzer.find_optimal_thresholds_by_category()

    for category, thresholds in optimal_thresholds.items():
        print(f"\n{category.upper().replace('_', ' ')}:")
        print(f"  Sample Size: {thresholds['count']} events")
        print(f"  Expectation: {thresholds['expectation'].upper()} returns")
        print(f"\n  Typical Percentile Ranges:")
        print(f"    Daily: {thresholds['daily_percentile_range']['p25']:.1f}% - {thresholds['daily_percentile_range']['p75']:.1f}% (median: {thresholds['daily_percentile_range']['median']:.1f}%)")
        print(f"    4H: {thresholds['4h_percentile_range']['p25']:.1f}% - {thresholds['4h_percentile_range']['p75']:.1f}% (median: {thresholds['4h_percentile_range']['median']:.1f}%)")
        print(f"    Divergence: {thresholds['divergence_range']['p25']:.1f}% - {thresholds['divergence_range']['p75']:.1f}% (median: {thresholds['divergence_range']['median']:.1f}%)")

        if thresholds['optimal_thresholds']['weak_threshold']:
            print(f"\n  Optimal Strength Thresholds:")
            print(f"    Weak: < {thresholds['optimal_thresholds']['moderate_threshold']}% divergence")
            print(f"    Moderate: {thresholds['optimal_thresholds']['moderate_threshold']}% - {thresholds['optimal_thresholds']['strong_threshold']}% divergence")
            print(f"    Strong: > {thresholds['optimal_thresholds']['strong_threshold']}% divergence")

        if thresholds['performance_by_strength']:
            print(f"\n  Performance by Strength:")
            for strength, perf in thresholds['performance_by_strength'].items():
                print(f"    {strength.capitalize()}: {perf['avg_return_d7']:+.2f}% avg D7 return, {perf['win_rate']:.1f}% win rate (n={perf['count']}, Sharpe={perf['sharpe']:.2f})")

    # 3. Generate decision matrix
    print("\n\n3. DECISION MATRIX")
    print("-" * 80)
    decision_matrix = analyzer.generate_decision_matrix()

    # Group by category
    for category in ['4h_overextended', 'bullish_convergence', 'daily_overextended', 'bearish_convergence']:
        cat_data = decision_matrix[decision_matrix['Category'] == category]
        if len(cat_data) > 0:
            print(f"\n{category.upper().replace('_', ' ')}:")
            print(cat_data.to_string(index=False))

    # 4. Create grid analysis
    print("\n\n4. PERCENTILE GRID ANALYSIS (Top 20 combinations by sample size)")
    print("-" * 80)
    grid = analyzer.create_percentile_grid_analysis()
    grid_sorted = grid.sort_values('count', ascending=False).head(20)
    print(grid_sorted.to_string(index=False))

    # Save results to file
    output_file = f'/workspaces/New-test-strategy/backend/{ticker}_PERCENTILE_THRESHOLDS.json'
    results = {
        'ticker': ticker,
        'analysis_date': pd.Timestamp.now().isoformat(),
        'distributions': distributions,
        'optimal_thresholds': optimal_thresholds,
        'decision_matrix': decision_matrix.to_dict(orient='records'),
        'grid_analysis': grid.to_dict(orient='records')
    }

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n\nResults saved to: {output_file}")

    return results


if __name__ == '__main__':
    run_percentile_threshold_analysis('GOOGL')
