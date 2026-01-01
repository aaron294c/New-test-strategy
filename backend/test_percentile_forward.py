#!/usr/bin/env python3
"""
Test script for Percentile Forward Mapping framework

Runs a full analysis to demonstrate:
1. Empirical bin mapping
2. Transition matrices
3. Regression models
4. Backtest accuracy
5. Current prediction

Usage: python test_percentile_forward.py
"""

from percentile_forward_mapping import run_percentile_forward_analysis
import json


if __name__ == '__main__':
    # Test with AAPL
    ticker = 'AAPL'

    print(f"\n{'='*80}")
    print(f"Testing Percentile Forward Mapping Framework: {ticker}")
    print(f"{'='*80}\n")

    # Run analysis
    result = run_percentile_forward_analysis(ticker, lookback_days=1095)

    # Display key results
    print(f"\n{'='*80}")
    print("KEY RESULTS SUMMARY")
    print(f"{'='*80}\n")

    print(f"Current State:")
    print(f"  Percentile: {result['current_percentile']:.1f}%ile")
    print(f"  RSI-MA: {result['current_rsi_ma']:.2f}")

    pred = result['prediction']
    print(f"\nForward Return Forecasts:")
    print(f"  1-Day:  {pred['ensemble_forecast_1d']:+.2f}%")
    print(f"  5-Day:  {pred['ensemble_forecast_5d']:+.2f}%")
    print(f"  10-Day: {pred['ensemble_forecast_10d']:+.2f}%")

    print(f"\nMethod Breakdown (1-day):")
    if pred['empirical_bin_stats']:
        print(f"  Empirical:  {pred['empirical_bin_stats']['mean_return_1d']:+.2f}%")
    print(f"  Markov:     {pred['markov_forecast_1d']:+.2f}%")
    if pred['linear_regression']:
        print(f"  Linear:     {pred['linear_regression']['forecast_1d']:+.2f}%")
    if pred['polynomial_regression']:
        print(f"  Polynomial: {pred['polynomial_regression']['forecast_1d']:+.2f}%")
    print(f"  Kernel:     {pred['kernel_forecast']['forecast_1d']:+.2f}%")

    print(f"\nBacktest Accuracy Metrics:")
    metrics_1d = result['accuracy_metrics'].get('1d', {})
    if metrics_1d:
        print(f"  MAE:         {metrics_1d['mae']:.2f}%")
        print(f"  RMSE:        {metrics_1d['rmse']:.2f}%")
        print(f"  Hit Rate:    {metrics_1d['hit_rate']:.1f}%")
        print(f"  Sharpe:      {metrics_1d['sharpe']:.2f}")
        print(f"  Info Ratio:  {metrics_1d['information_ratio']:.2f}")
        print(f"  Correlation: {metrics_1d['correlation']:.3f}")

    # Trading recommendation
    print(f"\n{'='*80}")
    print("TRADING RECOMMENDATION")
    print(f"{'='*80}\n")

    if metrics_1d:
        if metrics_1d['hit_rate'] > 55 and metrics_1d['sharpe'] > 1:
            print("✅ STRONG PREDICTIVE POWER - Safe to use for trading decisions")
            print(f"\nExpected Edge: {metrics_1d['mean_prediction']:+.2f}% per trade")
            print(f"Win Rate: {metrics_1d['hit_rate']:.1f}% (above random)")
            print(f"Risk-Adjusted Return: Sharpe {metrics_1d['sharpe']:.2f} (good)")
        elif metrics_1d['hit_rate'] > 52 and metrics_1d['sharpe'] > 0.5:
            print("⚠️ MODERATE PREDICTIVE POWER - Use with caution")
            print(f"\nExpected Edge: {metrics_1d['mean_prediction']:+.2f}% per trade")
            print(f"Win Rate: {metrics_1d['hit_rate']:.1f}% (slight edge)")
            print(f"Risk-Adjusted Return: Sharpe {metrics_1d['sharpe']:.2f} (fair)")
            print("\nRecommendation: Combine with other signals for confirmation")
        else:
            print("❌ WEAK PREDICTIVE POWER - Do not trade solely on this signal")
            print(f"\nWin Rate: {metrics_1d['hit_rate']:.1f}% (insufficient)")
            print(f"Sharpe: {metrics_1d['sharpe']:.2f} (too low)")
            print("\nRecommendation: Model needs improvement or ticker is not suitable")

    # Bin statistics
    print(f"\n{'='*80}")
    print("EMPIRICAL BIN STATISTICS")
    print(f"{'='*80}\n")

    print(f"{'Bin':<12} {'Count':>6} {'Mean 1d':>9} {'Median 1d':>10} {'5th %ile':>9} {'95th %ile':>10}")
    print("-" * 72)

    for bin_idx, stats in result['bin_stats'].items():
        print(f"{stats['bin_label']:<12} {stats['count']:>6} "
              f"{stats['mean_return_1d']:>+8.2f}% "
              f"{stats['median_return_1d']:>+9.2f}% "
              f"{stats['pct_5_return_1d']:>+8.2f}% "
              f"{stats['pct_95_return_1d']:>+9.2f}%")

    # Save full results to JSON
    output_file = f'percentile_forward_{ticker.lower()}_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n✓ Full analysis saved to: {output_file}")

    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}\n")
