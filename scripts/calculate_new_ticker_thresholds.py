#!/usr/bin/env python3
"""
Calculate P85/P95 thresholds for newly added tickers.

This script uses MultiTimeframeAnalyzer to compute real thresholds
from historical data instead of using placeholder values.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from multi_timeframe_analyzer import MultiTimeframeAnalyzer
import json


def calculate_thresholds(ticker: str):
    """Calculate P85/P95 thresholds for a ticker."""
    print(f"\n{'='*60}")
    print(f"Calculating thresholds for {ticker}")
    print(f"{'='*60}")

    try:
        # Initialize analyzer
        analyzer = MultiTimeframeAnalyzer(ticker)

        # Calculate divergence series
        divergence_series = analyzer.calculate_divergence_series()

        # Get optimal thresholds
        thresholds = analyzer.find_optimal_thresholds(divergence_series)

        # Extract key values
        print(f"\n{ticker} Thresholds:")
        print(f"  Bearish Divergence Threshold (Pos P85): {thresholds['bearish_divergence_threshold']}")
        print(f"  Bullish Divergence Threshold (Neg P85): {thresholds['bullish_divergence_threshold']}")
        print(f"  Absolute P85: {thresholds['dislocation_abs_p85']}")
        print(f"  Absolute P95: {thresholds['dislocation_abs_p95']}")
        print(f"  Positive P85: {thresholds['dislocation_positive_p85']}")
        print(f"  Negative P85: {thresholds['dislocation_negative_p85']}")
        print(f"\n  Sample Info:")
        print(f"    Days: {thresholds['dislocation_sample']['n_days']}")
        print(f"    Date Range: {thresholds['dislocation_sample']['start_date']} to {thresholds['dislocation_sample']['end_date']}")

        return {
            ticker: {
                'bearish_threshold': thresholds['bearish_divergence_threshold'],
                'bullish_threshold': thresholds['bullish_divergence_threshold'],
                'abs_p85': round(thresholds['dislocation_abs_p85'], 2) if thresholds['dislocation_abs_p85'] is not None else None,
                'abs_p95': round(thresholds['dislocation_abs_p95'], 2) if thresholds['dislocation_abs_p95'] is not None else None,
                'pos_p85': round(thresholds['dislocation_positive_p85'], 2) if thresholds['dislocation_positive_p85'] is not None else None,
                'neg_p85': round(thresholds['dislocation_negative_p85'], 2) if thresholds['dislocation_negative_p85'] is not None else None,
                'sample_days': thresholds['dislocation_sample']['n_days'],
                'date_range': f"{thresholds['dislocation_sample']['start_date']} to {thresholds['dislocation_sample']['end_date']}"
            }
        }

    except Exception as e:
        print(f"\n❌ Error calculating thresholds for {ticker}: {e}")
        import traceback
        traceback.print_exc()
        return {ticker: {'error': str(e)}}


def main():
    """Calculate thresholds for all new tickers."""

    # All newly added tickers that need real P85/P95 calculations
    new_tickers = [
        # Energy
        'XOM', 'CVX', 'OXY',
        # Financial
        'JPM', 'BAC',
        # Healthcare
        'LLY', 'UNH',
        # Tech
        'TSM',
        # Retail
        'WMT', 'COST',
        # Commodities
        'GLD', 'SLV',
        # Forex & Bonds
        'USDGBP', 'US10'
    ]

    all_results = {}

    for ticker in new_tickers:
        result = calculate_thresholds(ticker)
        all_results.update(result)

    # Save to JSON file
    output_file = '/workspaces/New-test-strategy/scripts/new_ticker_thresholds.json'
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n{'='*60}")
    print(f"✅ Results saved to {output_file}")
    print(f"{'='*60}")

    # Print summary
    print("\n📊 THRESHOLD SUMMARY")
    print(f"{'='*60}")
    print(f"{'Ticker':<10} {'Abs P85':<10} {'Abs P95':<10} {'Bearish':<10} {'Bullish':<10}")
    print(f"{'-'*60}")

    for ticker, data in all_results.items():
        if 'error' in data:
            print(f"{ticker:<10} ERROR: {data['error']}")
        else:
            abs_p85 = data['abs_p85'] if data['abs_p85'] is not None else 'N/A'
            abs_p95 = data['abs_p95'] if data['abs_p95'] is not None else 'N/A'
            bearish = data['bearish_threshold']
            bullish = data['bullish_threshold']
            print(f"{ticker:<10} {str(abs_p85):<10} {str(abs_p95):<10} {bearish:<10} {bullish:<10}")


if __name__ == "__main__":
    main()
