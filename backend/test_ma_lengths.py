#!/usr/bin/env python3
"""Test different MA lengths to match TradingView value."""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# Fetch AAPL data
ticker = "AAPL"
stock = yf.Ticker(ticker)
data = stock.history(period="1y", interval="1d")

print(f"Testing different MA lengths for {ticker}")
print(f"Last close: ${data['Close'].iloc[-1]:.2f} on {data.index[-1].strftime('%Y-%m-%d')}\n")

# Step 1: Calculate Mean Price from OHLC
op = data['Open']
hi = data['High']
lo = data['Low']
cl = data['Close']
hl2 = (hi + lo) / 2

bar_nt = (op * 1 + hi * 2 + lo * 2 + cl * 3 + hl2 * 2 + hl2 * 2) / 12
bar_up = (op * 1 + hi * 4 + lo * 2 + cl * 5 + hl2 * 3 + hl2 * 3) / 18
bar_dn = (op * 1 + hi * 2 + lo * 4 + cl * 5 + hl2 * 3 + hl2 * 3) / 18

hc = np.abs(hi - cl)
lc = np.abs(lo - cl)

mean_price = pd.Series(index=data.index, dtype=float)
for i in range(len(data)):
    if cl.iloc[i] > op.iloc[i]:
        mean_price.iloc[i] = bar_up.iloc[i]
    elif cl.iloc[i] < op.iloc[i]:
        mean_price.iloc[i] = bar_dn.iloc[i]
    else:
        if hc.iloc[i] < lc.iloc[i]:
            mean_price.iloc[i] = bar_up.iloc[i]
        elif hc.iloc[i] > lc.iloc[i]:
            mean_price.iloc[i] = bar_dn.iloc[i]
        else:
            mean_price.iloc[i] = bar_nt.iloc[i]

# Step 2: Calculate returns
returns = mean_price.pct_change()

# Step 3: Standardize with z-scores
lookback = 30
rolling_mean = returns.rolling(window=lookback, min_periods=lookback).mean()
rolling_std = returns.rolling(window=lookback, min_periods=lookback).std()
z_scores = (returns - rolling_mean) / rolling_std
z_scores = z_scores.fillna(0)

# Step 4: Apply RSI
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

print(f"RSI (from z-scores): {rsi.iloc[-1]:.2f}\n")

# Step 5: Test different MA lengths
print("Testing different EMA lengths:")
print("="*70)
for ma_length in [10, 11, 12, 13, 14, 15, 16]:
    rsi_ma = rsi.ewm(span=ma_length, adjust=False).mean()
    diff_4937 = abs(rsi_ma.iloc[-1] - 49.37)
    diff_4782 = abs(rsi_ma.iloc[-1] - 47.82)

    marker = ""
    if diff_4937 < 0.5 or diff_4782 < 0.5:
        marker = " *** CLOSE MATCH ***"

    print(f"MA Length {ma_length:2d}: {rsi_ma.iloc[-1]:6.2f}  "
          f"(diff from 49.37: {diff_4937:5.2f}, diff from 47.82: {diff_4782:5.2f}){marker}")

print("="*70)
print(f"\nExpected TradingView values: 49.37 or 47.82")
