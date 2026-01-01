#!/usr/bin/env python3
"""
Complete TradingView method:
1. Calculate Mean Price from OHLC
2. Calculate returns from Mean Price
3. Standardize returns with z-scores (30-day lookback)
4. Apply RSI (14-period) to z-scores
5. Apply EMA (14-period) to RSI
"""

import pandas as pd
import numpy as np
import yfinance as yf
from mean_price_calculator import calculate_mean_price

ticker = "AAPL"
stock = yf.Ticker(ticker)
data = stock.history(period="2y", interval="1d")

if data.empty:
    print("Failed to fetch data")
    exit(1)

print("="*70)
print("COMPLETE TRADINGVIEW METHOD")
print("="*70)
print("\nStep 1: Calculate Mean Price from OHLC")
print("Step 2: Calculate returns from Mean Price")
print("Step 3: Standardize with z-scores (30-day lookback)")
print("Step 4: Apply RSI (14-period) to z-scores")
print("Step 5: Apply EMA (14-period) to RSI")
print("="*70)

# Step 1: Calculate mean price
mean_price = calculate_mean_price(data, robust=False)

print(f"\nLast 5 mean prices:")
for i in range(-5, 0):
    date = data.index[i]
    close = data['Close'].iloc[i]
    mp = mean_price.iloc[i]
    print(f"  {date.strftime('%Y-%m-%d')}: Close=${close:.2f}, MeanPrice=${mp:.2f}")

# Step 2: Calculate returns from mean price
returns = mean_price.pct_change()

print(f"\nLast 5 returns:")
for i in range(-5, 0):
    date = returns.index[i]
    ret = returns.iloc[i] * 100 if not pd.isna(returns.iloc[i]) else 0
    print(f"  {date.strftime('%Y-%m-%d')}: {ret:+.2f}%")

# Step 3: Standardize with z-scores (30-day lookback)
lookback = 30
rolling_mean = returns.rolling(window=lookback, min_periods=lookback).mean()
rolling_std = returns.rolling(window=lookback, min_periods=lookback).std()

z_scores = (returns - rolling_mean) / rolling_std
z_scores = z_scores.fillna(0)

print(f"\nLast 5 z-scores:")
for i in range(-5, 0):
    date = z_scores.index[i]
    z = z_scores.iloc[i]
    ret = returns.iloc[i] * 100 if not pd.isna(returns.iloc[i]) else 0
    print(f"  {date.strftime('%Y-%m-%d')}: return={ret:+.2f}%, z-score={z:+.2f}")

# Step 4: Apply RSI to z-scores
rsi_length = 14
z_gains = z_scores.where(z_scores > 0, 0)
z_losses = -z_scores.where(z_scores < 0, 0)

avg_gains = z_gains.ewm(alpha=1/rsi_length, adjust=False).mean()
avg_losses = z_losses.ewm(alpha=1/rsi_length, adjust=False).mean()

rs = avg_gains / avg_losses
rsi = 100 - (100 / (1 + rs))
rsi = rsi.replace([np.inf, -np.inf], np.nan)
rsi.loc[avg_losses == 0] = 100
rsi.loc[avg_gains == 0] = 0
rsi = rsi.fillna(50)

print(f"\nLast 5 RSI values:")
for i in range(-5, 0):
    date = rsi.index[i]
    print(f"  {date.strftime('%Y-%m-%d')}: {rsi.iloc[i]:.2f}")

# Step 5: Apply EMA to RSI
ma_length = 14
rsi_ma = rsi.ewm(span=ma_length, adjust=False).mean()

print(f"\nLast 10 RSI-MA values:")
for i in range(-10, 0):
    date = rsi_ma.index[i]
    print(f"  {date.strftime('%Y-%m-%d')}: RSI={rsi.iloc[i]:.2f}, RSI-MA={rsi_ma.iloc[i]:.2f}")

# Final result
print(f"\n{'='*70}")
print("FINAL RESULT")
print(f"{'='*70}")
print(f"Date: {data.index[-1].strftime('%Y-%m-%d')}")
print(f"Close Price: ${data['Close'].iloc[-1]:.2f}")
print(f"Mean Price: ${mean_price.iloc[-1]:.2f}")
print(f"Return: {returns.iloc[-1]*100:+.2f}%")
print(f"Z-Score: {z_scores.iloc[-1]:+.2f}")
print(f"RSI: {rsi.iloc[-1]:.2f}")
print(f"RSI-MA: {rsi_ma.iloc[-1]:.2f}")
print(f"\nYour TradingView RSI-MA: 48.48")
print(f"Difference: {abs(rsi_ma.iloc[-1] - 48.48):.2f}")

# Compare with standard method (using close prices)
print(f"\n{'='*70}")
print("COMPARISON: Mean Price vs Close Price as Source")
print(f"{'='*70}")

# Standard method with close prices
close_returns = data['Close'].pct_change()
close_rolling_mean = close_returns.rolling(window=lookback, min_periods=lookback).mean()
close_rolling_std = close_returns.rolling(window=lookback, min_periods=lookback).std()
close_z_scores = (close_returns - close_rolling_mean) / close_rolling_std
close_z_scores = close_z_scores.fillna(0)

close_z_gains = close_z_scores.where(close_z_scores > 0, 0)
close_z_losses = -close_z_scores.where(close_z_scores < 0, 0)

close_avg_gains = close_z_gains.ewm(alpha=1/rsi_length, adjust=False).mean()
close_avg_losses = close_z_losses.ewm(alpha=1/rsi_length, adjust=False).mean()

close_rs = close_avg_gains / close_avg_losses
close_rsi = 100 - (100 / (1 + close_rs))
close_rsi = close_rsi.replace([np.inf, -np.inf], np.nan)
close_rsi.loc[close_avg_losses == 0] = 100
close_rsi.loc[close_avg_gains == 0] = 0
close_rsi = close_rsi.fillna(50)

close_rsi_ma = close_rsi.ewm(span=ma_length, adjust=False).mean()

print(f"\nUsing Mean Price:  RSI-MA = {rsi_ma.iloc[-1]:.2f}")
print(f"Using Close Price: RSI-MA = {close_rsi_ma.iloc[-1]:.2f}")
print(f"TradingView:       RSI-MA = 48.48")
print(f"\nMean Price difference:  {abs(rsi_ma.iloc[-1] - 48.48):.2f}")
print(f"Close Price difference: {abs(close_rsi_ma.iloc[-1] - 48.48):.2f}")

if abs(rsi_ma.iloc[-1] - 48.48) < abs(close_rsi_ma.iloc[-1] - 48.48):
    print("\n✓ Mean Price method is CLOSER to TradingView!")
else:
    print("\n✓ Close Price method is CLOSER to TradingView!")

# Show side-by-side for last 15 days
print(f"\n{'='*70}")
print("SIDE-BY-SIDE COMPARISON (Last 15 Days)")
print(f"{'='*70}")
print(f"\n{'Date':<12} {'MeanPrice':>10} {'ClosePrc':>9} {'MP RSI-MA':>11} {'CP RSI-MA':>11} {'Diff':>6}")
print(f"{'-'*12} {'-'*10} {'-'*9} {'-'*11} {'-'*11} {'-'*6}")
for i in range(-15, 0):
    date = data.index[i]
    print(f"{date.strftime('%Y-%m-%d'):<12} "
          f"${mean_price.iloc[i]:>9.2f} "
          f"${data['Close'].iloc[i]:>8.2f} "
          f"{rsi_ma.iloc[i]:>11.2f} "
          f"{close_rsi_ma.iloc[i]:>11.2f} "
          f"{rsi_ma.iloc[i] - close_rsi_ma.iloc[i]:>+6.2f}")
