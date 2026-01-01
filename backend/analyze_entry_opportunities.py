#!/usr/bin/env python3
"""Analyze how often Excellent/Good entry opportunities occurred in the past year."""
import sys
sys.path.insert(0, '.')

import yfinance as yf
import numpy as np
from datetime import datetime, timedelta

# Fetch VIX data for the past year
print("Fetching VIX historical data for the past year...\n")
vix = yf.Ticker("^VIX")
hist = vix.history(period="1y")

if hist.empty:
    print("ERROR: Could not fetch VIX data")
    sys.exit(1)

vix_values = hist['Close'].values
total_days = len(vix_values)

print(f"{'='*70}")
print(f"VIX ANALYSIS - PAST YEAR ({total_days} trading days)")
print(f"{'='*70}\n")

# Calculate statistics
vix_min = vix_values.min()
vix_max = vix_values.max()
vix_mean = vix_values.mean()
vix_median = np.median(vix_values)
vix_current = vix_values[-1]

print(f"VIX Statistics:")
print(f"  Minimum:       {vix_min:.1f}%")
print(f"  Maximum:       {vix_max:.1f}%")
print(f"  Mean:          {vix_mean:.1f}%")
print(f"  Median:        {vix_median:.1f}%")
print(f"  Current:       {vix_current:.1f}%")
print(f"  Range:         {vix_max - vix_min:.1f}%")
print()

# Analyze Entry Quality opportunities
print(f"{'='*70}")
print(f"ENTRY QUALITY OPPORTUNITIES ANALYSIS")
print(f"{'='*70}\n")

# For each day, calculate what the IV Percentile would have been
# (This simulates looking back from each day)
results = {
    'excellent': [],  # IV Percentile < 30%
    'good': [],       # IV Percentile 30-50%
    'fair': [],       # IV Percentile 50-70%
    'wait': []        # IV Percentile > 70%
}

for i in range(30, total_days):  # Start at day 30 to have enough history
    # Use 30-day rolling window for percentile calculation
    window = vix_values[i-30:i]
    current_vix = vix_values[i]

    # Calculate percentile: % of days in window where VIX was below current
    days_below = (window < current_vix).sum()
    percentile = (days_below / len(window)) * 100

    if percentile < 30:
        results['excellent'].append((i, current_vix, percentile))
    elif percentile < 50:
        results['good'].append((i, current_vix, percentile))
    elif percentile < 70:
        results['fair'].append((i, current_vix, percentile))
    else:
        results['wait'].append((i, current_vix, percentile))

total_analyzed = sum(len(v) for v in results.values())

print(f"Entry Quality Distribution (based on 30-day rolling percentile):")
print(f"{'='*70}")
print(f"  [GREEN] Excellent Entry (IV %ile < 30%):  {len(results['excellent']):3d} days ({len(results['excellent'])/total_analyzed*100:5.1f}%)")
print(f"  [YELLOW] Good/Fair Entry (IV %ile 30-70%): {len(results['good']) + len(results['fair']):3d} days ({(len(results['good']) + len(results['fair']))/total_analyzed*100:5.1f}%)")
print(f"  [RED] Wait for Better (IV %ile > 70%):  {len(results['wait']):3d} days ({len(results['wait'])/total_analyzed*100:5.1f}%)")
print(f"{'='*70}\n")

# Calculate using full year percentile (more restrictive)
print(f"Full Year Percentile Analysis:")
print(f"{'='*70}")

excellent_full = 0
good_full = 0
fair_full = 0
wait_full = 0

for i, vix_val in enumerate(vix_values):
    days_below = (vix_values < vix_val).sum()
    percentile = (days_below / total_days) * 100

    if percentile < 30:
        excellent_full += 1
    elif percentile < 50:
        good_full += 1
    elif percentile < 70:
        fair_full += 1
    else:
        wait_full += 1

print(f"  [GREEN] Excellent Entry (IV %ile < 30%):  {excellent_full:3d} days ({excellent_full/total_days*100:5.1f}%)")
print(f"  [YELLOW] Good/Fair Entry (IV %ile 30-70%): {good_full + fair_full:3d} days ({(good_full + fair_full)/total_days*100:5.1f}%)")
print(f"  [RED] Wait for Better (IV %ile > 70%):  {wait_full:3d} days ({wait_full/total_days*100:5.1f}%)")
print(f"{'='*70}\n")

# Recommendations
print(f"{'='*70}")
print(f"RECOMMENDATIONS")
print(f"{'='*70}\n")

excellent_pct = excellent_full / total_days * 100
good_fair_pct = (good_full + fair_full) / total_days * 100

if excellent_pct < 20:
    print(f"WARNING: CURRENT CRITERIA IS RESTRICTIVE")
    print(f"   - Excellent entries only {excellent_pct:.1f}% of days")
    print(f"   - You'd be waiting most of the time")
    print()
    print(f"SUGGESTED ADJUSTMENT:")
    print(f"   - Change 'Excellent' threshold from 30% to 40%")
    print(f"   - This would increase opportunities to ~{(vix_values < np.percentile(vix_values, 40)).sum()/total_days*100:.1f}% of days")
    print()
elif excellent_pct > 40:
    print(f"OK: CURRENT CRITERIA IS BALANCED")
    print(f"  - Excellent entries {excellent_pct:.1f}% of days")
    print(f"  - Good mix of opportunities vs selectivity")
    print()
else:
    print(f"OK: CURRENT CRITERIA SEEMS REASONABLE")
    print(f"  - Excellent entries {excellent_pct:.1f}% of days")
    print(f"  - Provides selectivity while allowing regular opportunities")
    print()

print(f"{'='*70}")
