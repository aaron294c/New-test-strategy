#!/usr/bin/env python3
"""
Test MACD-V Percentile Calculator

Demonstrates the three percentile calculation methods:
1. Categorical (RECOMMENDED): Percentiles within each zone
2. Global: Single percentile across all values
3. Asymmetric: Separate percentiles for bullish/bearish
"""

import pandas as pd
import numpy as np
import yfinance as yf
from macdv_percentile_calculator import MACDVPercentileCalculator


def test_all_methods(ticker: str = "AAPL", days: int = 365):
    """Test all three percentile calculation methods."""

    print("="*80)
    print(f"MACD-V PERCENTILE CALCULATOR TEST - {ticker}")
    print("="*80)

    # Fetch data
    print(f"\nFetching {days} days of data for {ticker}...")
    df = yf.download(ticker, period=f"{days}d", interval="1d", progress=False, auto_adjust=True)

    if df.empty:
        print("Failed to fetch data")
        return

    # Fix column names
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0].lower() if isinstance(col, tuple) else str(col).lower()
                     for col in df.columns]
    else:
        df.columns = [str(c).lower() for c in df.columns]

    print(f"✓ Fetched {len(df)} data points")
    print(f"  Date range: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")

    # Initialize calculator
    calculator = MACDVPercentileCalculator(
        fast_length=12,
        slow_length=26,
        signal_length=9,
        atr_length=26,
        percentile_lookback=252
    )

    # Test all three methods
    methods = ["categorical", "global", "asymmetric"]
    results = {}

    for method in methods:
        print(f"\n{'='*80}")
        print(f"METHOD: {method.upper()}")
        print(f"{'='*80}")

        df_calc = calculator.calculate_macdv_with_percentiles(df, method=method)
        results[method] = df_calc

        # Show latest values
        latest = df_calc.iloc[-1]
        print(f"\nLatest Values ({latest.name.strftime('%Y-%m-%d')}):")
        print(f"  MACD-V Value:      {latest['macdv_val']:7.2f}")
        print(f"  MACD-V Signal:     {latest['macdv_signal']:7.2f}")
        print(f"  MACD-V Histogram:  {latest['macdv_hist']:7.2f}")
        print(f"  Zone:              {latest['macdv_zone']}")
        print(f"  Percentile:        {latest['macdv_percentile']:.2f}%")
        print(f"  Color:             {latest['macdv_color']}")
        print(f"  Trend:             {latest['macdv_trend']}")

        # Show last 10 values
        print(f"\nLast 10 Values:")
        print(f"{'Date':<12} {'MACD-V':>8} {'Percentile':>11} {'Zone':<20}")
        print(f"{'-'*12} {'-'*8} {'-'*11} {'-'*20}")
        for i in range(-10, 0):
            row = df_calc.iloc[i]
            date_str = row.name.strftime('%Y-%m-%d')
            print(f"{date_str:<12} {row['macdv_val']:8.2f} {row['macdv_percentile']:10.2f}% {row['macdv_zone']:<20}")

        # Get zone statistics
        zone_stats = calculator.get_zone_statistics(df, method=method)

        print(f"\nZone Distribution:")
        print(f"{'Zone':<20} {'Count':>6} {'% of Total':>10} {'Avg Val':>10} {'Avg Pctl':>10}")
        print(f"{'-'*20} {'-'*6} {'-'*10} {'-'*10} {'-'*10}")
        for zone_name, stats in zone_stats.items():
            if stats['count'] > 0:
                print(f"{zone_name:<20} {stats['count']:6d} {stats['pct_of_total']:9.2f}% "
                      f"{stats['avg_val']:10.2f} {stats['avg_percentile']:10.2f}")

    # Compare methods
    print(f"\n{'='*80}")
    print("METHOD COMPARISON (Last 5 Values)")
    print(f"{'='*80}")

    print(f"\n{'Date':<12} {'MACD-V':>8} {'Categorical':>12} {'Global':>12} {'Asymmetric':>12}")
    print(f"{'-'*12} {'-'*8} {'-'*12} {'-'*12} {'-'*12}")
    for i in range(-5, 0):
        date_str = df.index[i].strftime('%Y-%m-%d')
        macdv_val = results['categorical'].iloc[i]['macdv_val']
        cat_pct = results['categorical'].iloc[i]['macdv_percentile']
        glo_pct = results['global'].iloc[i]['macdv_percentile']
        asy_pct = results['asymmetric'].iloc[i]['macdv_percentile']
        print(f"{date_str:<12} {macdv_val:8.2f} {cat_pct:11.2f}% {glo_pct:11.2f}% {asy_pct:11.2f}%")

    print(f"\n{'='*80}")
    print("INTERPRETATION GUIDE")
    print(f"{'='*80}")

    print("""
1. CATEGORICAL (RECOMMENDED):
   - Percentile is calculated within the current zone
   - Example: MACD-V = 75, Zone = strong_bullish (50-100)
   - 80th percentile means it's in the top 20% of values in the 50-100 zone
   - Useful for: Understanding relative strength within the current regime

2. GLOBAL (SIMPLER):
   - Percentile is calculated across all MACD-V values
   - Example: MACD-V = 75
   - 80th percentile means it's higher than 80% of all historical values
   - Useful for: Quick assessment of extreme levels

3. ASYMMETRIC (COMPLEX):
   - Separate percentiles for bullish (≥0) and bearish (<0) regimes
   - Example: MACD-V = 75 (bullish regime)
   - 60th percentile means it's higher than 60% of bullish values
   - Useful for: Directional analysis with regime awareness
    """)

    print(f"\n{'='*80}")
    print("RECOMMENDATION")
    print(f"{'='*80}")
    print("""
Use CATEGORICAL method because:
✓ Respects the natural zone structure of MACD-V
✓ Provides relative positioning within each market regime
✓ More meaningful than global percentiles for ranging vs trending analysis
✓ Combines absolute level (zone) with relative strength (percentile)

Example interpretation:
- MACD-V = 75 (zone: strong_bullish, 50-100)
- Percentile = 80%
- Meaning: "Strong bullish momentum (50-100 zone), and in the top 20%
           of that zone historically"
    """)


if __name__ == "__main__":
    import sys

    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 365

    test_all_methods(ticker, days)
