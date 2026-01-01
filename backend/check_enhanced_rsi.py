#!/usr/bin/env python3
"""Check current RSI-MA using the ENHANCED method (Mean Price + Z-scores)."""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# Fetch AAPL data
ticker = "AAPL"
print(f"Checking {ticker} RSI-MA calculation (ENHANCED METHOD)...")
print(f"Current time: {datetime.now()}")

stock = yf.Ticker(ticker)
data = stock.history(period="1y", interval="1d")

if data.empty:
    print("Failed to fetch data")
    exit(1)

print(f"\nFetched {len(data)} data points")
print(f"Date range: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
print(f"Last update: {data.index[-1]}")

# Show last 5 close prices
print("\nLast 5 OHLC:")
for i in range(-5, 0):
    date = data.index[i]
    print(f"  {date.strftime('%Y-%m-%d')}: O=${data['Open'].iloc[i]:.2f} H=${data['High'].iloc[i]:.2f} L=${data['Low'].iloc[i]:.2f} C=${data['Close'].iloc[i]:.2f}")

print("\n=== Calculating RSI-MA (ENHANCED METHOD: Mean Price + Z-Scores) ===")

# Step 1: Calculate Mean Price from OHLC
op = data['Open']
hi = data['High']
lo = data['Low']
cl = data['Close']
hl2 = (hi + lo) / 2

# Calculate three bar types
bar_nt = (op * 1 + hi * 2 + lo * 2 + cl * 3 + hl2 * 2 + hl2 * 2) / 12
bar_up = (op * 1 + hi * 4 + lo * 2 + cl * 5 + hl2 * 3 + hl2 * 3) / 18
bar_dn = (op * 1 + hi * 2 + lo * 4 + cl * 5 + hl2 * 3 + hl2 * 3) / 18

# Calculate distances
hc = np.abs(hi - cl)
lc = np.abs(lo - cl)

# Select appropriate mean price based on bar direction
mean_price = pd.Series(index=data.index, dtype=float)
for i in range(len(data)):
    if cl.iloc[i] > op.iloc[i]:
        # Bullish bar
        mean_price.iloc[i] = bar_up.iloc[i]
    elif cl.iloc[i] < op.iloc[i]:
        # Bearish bar
        mean_price.iloc[i] = bar_dn.iloc[i]
    else:  # Doji
        if hc.iloc[i] < lc.iloc[i]:
            mean_price.iloc[i] = bar_up.iloc[i]
        elif hc.iloc[i] > lc.iloc[i]:
            mean_price.iloc[i] = bar_dn.iloc[i]
        else:
            mean_price.iloc[i] = bar_nt.iloc[i]

print("\nLast 5 Mean Prices:")
for i in range(-5, 0):
    date = mean_price.index[i]
    print(f"  {date.strftime('%Y-%m-%d')}: ${mean_price.iloc[i]:.2f}")

# Step 2: Calculate returns from Mean Price
returns = mean_price.pct_change()

# Step 3: Standardize with z-scores (30-day lookback)
lookback = 30
rolling_mean = returns.rolling(window=lookback, min_periods=lookback).mean()
rolling_std = returns.rolling(window=lookback, min_periods=lookback).std()
z_scores = (returns - rolling_mean) / rolling_std
z_scores = z_scores.fillna(0)

print("\nLast 5 Z-Scores:")
for i in range(-5, 0):
    date = z_scores.index[i]
    print(f"  {date.strftime('%Y-%m-%d')}: {z_scores.iloc[i]:.4f}")

# Step 4: Apply RSI to z-scores
rsi_length = 14
z_gains = z_scores.where(z_scores > 0, 0)
z_losses = -z_scores.where(z_scores < 0, 0)

# Wilder's smoothing (RMA)
avg_gains = z_gains.ewm(alpha=1/rsi_length, adjust=False).mean()
avg_losses = z_losses.ewm(alpha=1/rsi_length, adjust=False).mean()

# Calculate RSI
rs = avg_gains / avg_losses
rsi = 100 - (100 / (1 + rs))
rsi = rsi.replace([np.inf, -np.inf], np.nan)
rsi.loc[avg_losses == 0] = 100
rsi.loc[avg_gains == 0] = 0
rsi = rsi.fillna(50)

print("\nLast 5 RSI values (from z-scores):")
for i in range(-5, 0):
    date = rsi.index[i]
    print(f"  {date.strftime('%Y-%m-%d')}: {rsi.iloc[i]:.2f}")

# Step 5: Apply EMA to RSI
ma_length = 14
rsi_ma = rsi.ewm(span=ma_length, adjust=False).mean()

print("\nLast 5 RSI-MA values:")
for i in range(-5, 0):
    date = rsi_ma.index[i]
    print(f"  {date.strftime('%Y-%m-%d')}: {rsi_ma.iloc[i]:.2f}")

print(f"\n{'='*60}")
print(f"CURRENT RSI-MA VALUE (ENHANCED): {rsi_ma.iloc[-1]:.2f}")
print(f"Your expected values: 49.37 or 47.82")
print(f"Difference from 49.37: {abs(rsi_ma.iloc[-1] - 49.37):.2f}")
print(f"Difference from 47.82: {abs(rsi_ma.iloc[-1] - 47.82):.2f}")
print(f"{'='*60}")
