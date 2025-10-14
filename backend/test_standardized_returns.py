#!/usr/bin/env python3
"""
Test RSI-MA using standardized returns (z-scores) as the source.

This approach:
1. Calculate rolling returns over a lookback period (30 days)
2. Standardize using z-scores (subtract mean, divide by std dev)
3. Apply RSI calculation to these standardized values
4. Apply EMA smoothing
"""

import pandas as pd
import numpy as np
import yfinance as yf

# Fetch AAPL data
ticker = "AAPL"
stock = yf.Ticker(ticker)
data = stock.history(period="2y", interval="1d")

if data.empty:
    print("Failed to fetch data")
    exit(1)

prices = data['Close']

print("="*70)
print("RSI-MA with Standardized Returns (Z-Score Approach)")
print("="*70)
print(f"\nSettings:")
print(f"  - Lookback period: 30 days")
print(f"  - Standardization: Z-scores (mean=0, std=1)")
print(f"  - RSI Length: 14")
print(f"  - MA Length: 14")

print(f"\nLast 5 close prices:")
for i in range(-5, 0):
    print(f"  {prices.index[i].strftime('%Y-%m-%d')}: ${prices.iloc[i]:.2f}")

# Method 1: Standard RSI (for comparison)
print(f"\n{'='*70}")
print("METHOD 1: Standard RSI (Absolute Price Changes)")
print(f"{'='*70}")

changes = prices.diff()
gains = changes.where(changes > 0, 0)
losses = -changes.where(changes < 0, 0)

rsi_length = 14
ma_length = 14

avg_gains = gains.ewm(alpha=1/rsi_length, adjust=False).mean()
avg_losses = losses.ewm(alpha=1/rsi_length, adjust=False).mean()

rs = avg_gains / avg_losses
rsi_standard = 100 - (100 / (1 + rs))
rsi_standard = rsi_standard.replace([np.inf, -np.inf], np.nan)
rsi_standard.loc[avg_losses == 0] = 100
rsi_standard.loc[avg_gains == 0] = 0
rsi_standard = rsi_standard.fillna(50)

rsi_ma_standard = rsi_standard.ewm(span=ma_length, adjust=False).mean()

print("\nLast 5 values:")
for i in range(-5, 0):
    date = prices.index[i]
    print(f"  {date.strftime('%Y-%m-%d')}: RSI={rsi_standard.iloc[i]:.2f}, RSI-MA={rsi_ma_standard.iloc[i]:.2f}")

# Method 2: Z-Score on daily returns
print(f"\n{'='*70}")
print("METHOD 2: RSI on Z-Scored Daily Returns (30-day lookback)")
print(f"{'='*70}")

lookback = 30

# Calculate daily returns
daily_returns = prices.pct_change()

# Calculate rolling z-scores
rolling_mean = daily_returns.rolling(window=lookback, min_periods=lookback).mean()
rolling_std = daily_returns.rolling(window=lookback, min_periods=lookback).std()

z_scores = (daily_returns - rolling_mean) / rolling_std
z_scores = z_scores.fillna(0)

print(f"\nExample z-scores (last 10 days):")
for i in range(-10, 0):
    date = prices.index[i]
    ret = daily_returns.iloc[i] * 100 if not pd.isna(daily_returns.iloc[i]) else 0
    z = z_scores.iloc[i]
    print(f"  {date.strftime('%Y-%m-%d')}: return={ret:+.2f}%, z-score={z:+.2f}")

# Apply RSI to z-scores
z_gains = z_scores.where(z_scores > 0, 0)
z_losses = -z_scores.where(z_scores < 0, 0)

avg_z_gains = z_gains.ewm(alpha=1/rsi_length, adjust=False).mean()
avg_z_losses = z_losses.ewm(alpha=1/rsi_length, adjust=False).mean()

rs_z = avg_z_gains / avg_z_losses
rsi_z = 100 - (100 / (1 + rs_z))
rsi_z = rsi_z.replace([np.inf, -np.inf], np.nan)
rsi_z.loc[avg_z_losses == 0] = 100
rsi_z.loc[avg_z_gains == 0] = 0
rsi_z = rsi_z.fillna(50)

rsi_ma_z = rsi_z.ewm(span=ma_length, adjust=False).mean()

print("\nLast 5 RSI values on z-scores:")
for i in range(-5, 0):
    date = prices.index[i]
    print(f"  {date.strftime('%Y-%m-%d')}: RSI={rsi_z.iloc[i]:.2f}, RSI-MA={rsi_ma_z.iloc[i]:.2f}")

# Method 3: Z-Score on cumulative returns (rolling 30-day)
print(f"\n{'='*70}")
print("METHOD 3: RSI on Z-Scored 30-Day Cumulative Returns")
print(f"{'='*70}")

# Calculate 30-day cumulative returns
cumulative_returns = (prices / prices.shift(lookback) - 1)

# Z-score the cumulative returns
cum_mean = cumulative_returns.rolling(window=lookback, min_periods=lookback).mean()
cum_std = cumulative_returns.rolling(window=lookback, min_periods=lookback).std()

z_cumulative = (cumulative_returns - cum_mean) / cum_std
z_cumulative = z_cumulative.fillna(0)

print(f"\nExample z-scores on 30-day returns (last 5 days):")
for i in range(-5, 0):
    date = prices.index[i]
    cum_ret = cumulative_returns.iloc[i] * 100 if not pd.isna(cumulative_returns.iloc[i]) else 0
    z = z_cumulative.iloc[i]
    print(f"  {date.strftime('%Y-%m-%d')}: 30d_return={cum_ret:+.2f}%, z-score={z:+.2f}")

# Calculate changes in z-scores
z_cum_changes = z_cumulative.diff()
z_cum_gains = z_cum_changes.where(z_cum_changes > 0, 0)
z_cum_losses = -z_cum_changes.where(z_cum_changes < 0, 0)

avg_z_cum_gains = z_cum_gains.ewm(alpha=1/rsi_length, adjust=False).mean()
avg_z_cum_losses = z_cum_losses.ewm(alpha=1/rsi_length, adjust=False).mean()

rs_z_cum = avg_z_cum_gains / avg_z_cum_losses
rsi_z_cum = 100 - (100 / (1 + rs_z_cum))
rsi_z_cum = rsi_z_cum.replace([np.inf, -np.inf], np.nan)
rsi_z_cum.loc[avg_z_cum_losses == 0] = 100
rsi_z_cum.loc[avg_z_cum_gains == 0] = 0
rsi_z_cum = rsi_z_cum.fillna(50)

rsi_ma_z_cum = rsi_z_cum.ewm(span=ma_length, adjust=False).mean()

print("\nLast 5 RSI values on z-scored cumulative returns:")
for i in range(-5, 0):
    date = prices.index[i]
    print(f"  {date.strftime('%Y-%m-%d')}: RSI={rsi_z_cum.iloc[i]:.2f}, RSI-MA={rsi_ma_z_cum.iloc[i]:.2f}")

# Method 4: Direct percentile ranking of standardized returns
print(f"\n{'='*70}")
print("METHOD 4: Percentile Rank of Standardized Returns (500-period)")
print(f"{'='*70}")

# Calculate percentile rank of z-scores over 500-period lookback
percentile_lookback = 500

def rolling_percentile_rank(window):
    if len(window) < percentile_lookback:
        return np.nan
    current_value = window.iloc[-1]
    below_count = (window.iloc[:-1] < current_value).sum()
    return (below_count / (len(window) - 1)) * 100

percentile_ranks = z_scores.rolling(
    window=percentile_lookback,
    min_periods=percentile_lookback
).apply(rolling_percentile_rank)

# Apply EMA to percentile ranks
percentile_ma = percentile_ranks.ewm(span=ma_length, adjust=False).mean()

print("\nLast 5 percentile values:")
for i in range(-5, 0):
    date = prices.index[i]
    if not pd.isna(percentile_ranks.iloc[i]):
        print(f"  {date.strftime('%Y-%m-%d')}: Percentile={percentile_ranks.iloc[i]:.2f}, EMA={percentile_ma.iloc[i]:.2f}")

# ===== COMPARISON =====
print(f"\n{'='*70}")
print("COMPARISON - All Methods on 2025-10-13")
print(f"{'='*70}")
print(f"Method 1 (Standard RSI-MA):           {rsi_ma_standard.iloc[-1]:.2f}")
print(f"Method 2 (Z-Score Daily Returns):     {rsi_ma_z.iloc[-1]:.2f}")
print(f"Method 3 (Z-Score 30d Cum Returns):   {rsi_ma_z_cum.iloc[-1]:.2f}")
if not pd.isna(percentile_ma.iloc[-1]):
    print(f"Method 4 (Percentile of Z-Scores):    {percentile_ma.iloc[-1]:.2f}")
else:
    print(f"Method 4 (Percentile of Z-Scores):    N/A (need more data)")

print(f"\nYour TradingView value:               48.48")

print(f"\nDifferences from TradingView:")
print(f"  Method 1: {abs(rsi_ma_standard.iloc[-1] - 48.48):.2f}")
print(f"  Method 2: {abs(rsi_ma_z.iloc[-1] - 48.48):.2f}")
print(f"  Method 3: {abs(rsi_ma_z_cum.iloc[-1] - 48.48):.2f}")
if not pd.isna(percentile_ma.iloc[-1]):
    print(f"  Method 4: {abs(percentile_ma.iloc[-1] - 48.48):.2f}")

closest = min(
    ('Standard', abs(rsi_ma_standard.iloc[-1] - 48.48)),
    ('Z-Score Daily', abs(rsi_ma_z.iloc[-1] - 48.48)),
    ('Z-Score Cumulative', abs(rsi_ma_z_cum.iloc[-1] - 48.48)),
    key=lambda x: x[1]
)

print(f"\n✓ Closest method: {closest[0]} (diff: {closest[1]:.2f})")

print(f"\n{'='*70}")
print("SUMMARY")
print(f"{'='*70}")
print("\nStandardizing returns with z-scores:")
print("  ✓ Normalizes for volatility regimes")
print("  ✓ Makes returns comparable across different volatility periods")
print("  ✓ Good for regime-switching strategies")
print("\nIf TradingView uses this approach, the indicator would be:")
print("  'RSI of Standardized Returns' rather than 'RSI of Price Changes'")
