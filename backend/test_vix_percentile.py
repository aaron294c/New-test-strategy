#!/usr/bin/env python3
"""Test VIX percentile calculation to understand the discrepancy."""
import sys
sys.path.insert(0, '.')

import yfinance as yf
import numpy as np

# Fetch VIX data
vix = yf.Ticker("^VIX")
hist = vix.history(period="1y")
vix_values = hist['Close'].values

print(f"VIX 52-week statistics:")
print(f"  Min: {vix_values.min():.1f}%")
print(f"  Max: {vix_values.max():.1f}%")
print(f"  Mean: {vix_values.mean():.1f}%")
print(f"  Median: {np.median(vix_values):.1f}%")
print(f"  Total days: {len(vix_values)}")
print()

# Test with actual option IVs from user's data
test_ivs = [19.3, 20.4, 20.2, 24.2, 24.6]

for iv in test_ivs:
    # Calculate IV Rank
    iv_rank = (iv - vix_values.min()) / (vix_values.max() - vix_values.min())

    # Calculate IV Percentile
    days_below = (vix_values < iv).sum()
    iv_percentile = (days_below / len(vix_values)) * 100

    print(f"IV = {iv}%:")
    print(f"  IV Rank: {iv_rank:.3f} ({iv_rank*100:.1f}%)")
    print(f"  IV Percentile: {iv_percentile:.1f}% ({days_below}/{len(vix_values)} days below)")
    print()
