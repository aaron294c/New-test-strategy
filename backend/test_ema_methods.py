#!/usr/bin/env python3
"""Test different EMA calculation methods."""

import pandas as pd
import numpy as np

# Create sample RSI values from our calculation
rsi_values = [67.78, 69.44, 60.87, 47.19, 51.67]
dates = pd.date_range('2025-10-07', periods=5, freq='D')
rsi = pd.Series(rsi_values, index=dates)

print("RSI values:")
for date, val in rsi.items():
    print(f"  {date.strftime('%Y-%m-%d')}: {val:.2f}")

print("\n=== Testing different EMA methods ===")

# Method 1: pandas ewm with span (what we're using)
ma_length = 13
rsi_ma_method1 = rsi.ewm(span=ma_length, adjust=False).mean()
print(f"\nMethod 1 - ewm(span={ma_length}, adjust=False):")
for date, val in rsi_ma_method1.items():
    print(f"  {date.strftime('%Y-%m-%d')}: {val:.2f}")

# Method 2: pandas ewm with span and adjust=True
rsi_ma_method2 = rsi.ewm(span=ma_length, adjust=True).mean()
print(f"\nMethod 2 - ewm(span={ma_length}, adjust=True):")
for date, val in rsi_ma_method2.items():
    print(f"  {date.strftime('%Y-%m-%d')}: {val:.2f}")

# Method 3: pandas ewm with alpha
alpha = 2 / (ma_length + 1)
rsi_ma_method3 = rsi.ewm(alpha=alpha, adjust=False).mean()
print(f"\nMethod 3 - ewm(alpha={alpha:.6f}, adjust=False):")
for date, val in rsi_ma_method3.items():
    print(f"  {date.strftime('%Y-%m-%d')}: {val:.2f}")

# Method 4: Simple Moving Average (just to compare)
rsi_ma_method4 = rsi.rolling(window=ma_length, min_periods=1).mean()
print(f"\nMethod 4 - SMA(window={ma_length}):")
for date, val in rsi_ma_method4.items():
    print(f"  {date.strftime('%Y-%m-%d')}: {val:.2f}")

print(f"\n{'='*60}")
print("All methods should give the same result for EMA.")
print("If TradingView shows a different value, it might be using SMA or a different period.")
