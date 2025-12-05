#!/usr/bin/env python3
"""Compare simple RSI (price changes) vs z-score RSI."""

import pandas as pd
import numpy as np
import yfinance as yf

# Fetch AAPL data
ticker = "AAPL"
stock = yf.Ticker(ticker)
data = stock.history(period="1y", interval="1d")

print(f"Comparing RSI calculation methods for {ticker}")
print(f"Last close: ${data['Close'].iloc[-1]:.2f} on {data.index[-1].strftime('%Y-%m-%d')}\n")

# Calculate Mean Price
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

print("="*80)
print("METHOD 1: Simple Price Changes (TradingView default)")
print("="*80)

# Method 1: Simple price changes
price_changes = mean_price.diff()
gains_simple = price_changes.where(price_changes > 0, 0)
losses_simple = -price_changes.where(price_changes < 0, 0)

rsi_length = 14
avg_gains_simple = gains_simple.ewm(alpha=1/rsi_length, adjust=False).mean()
avg_losses_simple = losses_simple.ewm(alpha=1/rsi_length, adjust=False).mean()

rs_simple = avg_gains_simple / avg_losses_simple
rsi_simple = 100 - (100 / (1 + rs_simple))
rsi_simple = rsi_simple.replace([np.inf, -np.inf], np.nan)
rsi_simple.loc[avg_losses_simple == 0] = 100
rsi_simple.loc[avg_gains_simple == 0] = 0
rsi_simple = rsi_simple.fillna(50)

print(f"RSI (simple): {rsi_simple.iloc[-1]:.2f}\n")

# Test different MA lengths
print("MA Length  |  RSI-MA  | Diff from 49.37 | Diff from 47.82")
print("-"*70)
for ma_length in [10, 11, 12, 13, 14, 15, 16, 17, 18]:
    rsi_ma_simple = rsi_simple.ewm(span=ma_length, adjust=False).mean()
    diff_4937 = abs(rsi_ma_simple.iloc[-1] - 49.37)
    diff_4782 = abs(rsi_ma_simple.iloc[-1] - 47.82)
    marker = " *** MATCH ***" if (diff_4937 < 0.5 or diff_4782 < 0.5) else ""
    print(f"    {ma_length:2d}     |  {rsi_ma_simple.iloc[-1]:6.2f}  |      {diff_4937:5.2f}      |      {diff_4782:5.2f}{marker}")

print("\n" + "="*80)
print("METHOD 2: Z-Score Standardization (Current Enhanced Method)")
print("="*80)

# Method 2: Z-scores
returns = mean_price.pct_change()
lookback = 30
rolling_mean = returns.rolling(window=lookback, min_periods=lookback).mean()
rolling_std = returns.rolling(window=lookback, min_periods=lookback).std()
z_scores = (returns - rolling_mean) / rolling_std
z_scores = z_scores.fillna(0)

z_gains = z_scores.where(z_scores > 0, 0)
z_losses = -z_scores.where(z_scores < 0, 0)

avg_gains_z = z_gains.ewm(alpha=1/rsi_length, adjust=False).mean()
avg_losses_z = z_losses.ewm(alpha=1/rsi_length, adjust=False).mean()

rs_z = avg_gains_z / avg_losses_z
rsi_z = 100 - (100 / (1 + rs_z))
rsi_z = rsi_z.replace([np.inf, -np.inf], np.nan)
rsi_z.loc[avg_losses_z == 0] = 100
rsi_z.loc[avg_gains_z == 0] = 0
rsi_z = rsi_z.fillna(50)

print(f"RSI (z-score): {rsi_z.iloc[-1]:.2f}\n")

# Test different MA lengths
print("MA Length  |  RSI-MA  | Diff from 49.37 | Diff from 47.82")
print("-"*70)
for ma_length in [10, 11, 12, 13, 14, 15, 16, 17, 18]:
    rsi_ma_z = rsi_z.ewm(span=ma_length, adjust=False).mean()
    diff_4937 = abs(rsi_ma_z.iloc[-1] - 49.37)
    diff_4782 = abs(rsi_ma_z.iloc[-1] - 47.82)
    marker = " *** MATCH ***" if (diff_4937 < 0.5 or diff_4782 < 0.5) else ""
    print(f"    {ma_length:2d}     |  {rsi_ma_z.iloc[-1]:6.2f}  |      {diff_4937:5.2f}      |      {diff_4782:5.2f}{marker}")

print("\n" + "="*80)
print("RECOMMENDATION:")
print("="*80)
print("Expected TradingView values: 49.37 or 47.82")
print("\nWhich method gives a closer match?")
