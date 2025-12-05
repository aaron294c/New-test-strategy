#!/usr/bin/env python3
"""Test RSI-MA with MA length = 14."""

import pandas as pd
import numpy as np
import yfinance as yf

# Fetch AAPL data
ticker = "AAPL"
stock = yf.Ticker(ticker)
data = stock.history(period="1y", interval="1d")

if data.empty:
    print("Failed to fetch data")
    exit(1)

prices = data['Close']

print("="*60)
print("RSI-MA Calculation for AAPL")
print("Settings:")
print("  - RSI Length: 14")
print("  - MA Type: EMA")
print("  - MA Length: 14 (UPDATED FROM 13!)")
print("  - Source: Absolute price changes")
print("="*60)

print(f"\nLast 5 close prices:")
for i in range(-5, 0):
    print(f"  {prices.index[i].strftime('%Y-%m-%d')}: ${prices.iloc[i]:.2f}")

# Calculate with MA length = 14
changes = prices.diff()
gains = changes.where(changes > 0, 0)
losses = -changes.where(changes < 0, 0)

rsi_length = 14
avg_gains = gains.ewm(alpha=1/rsi_length, adjust=False).mean()
avg_losses = losses.ewm(alpha=1/rsi_length, adjust=False).mean()

rs = avg_gains / avg_losses
rsi = 100 - (100 / (1 + rs))
rsi = rsi.replace([np.inf, -np.inf], np.nan)
rsi.loc[avg_losses == 0] = 100
rsi.loc[avg_gains == 0] = 0
rsi = rsi.fillna(50)

# MA length = 14 (not 13!)
ma_length = 14
rsi_ma = rsi.ewm(span=ma_length, adjust=False).mean()

print("\nLast 10 RSI and RSI-MA values:")
for i in range(-10, 0):
    date = rsi.index[i]
    print(f"  {date.strftime('%Y-%m-%d')}: RSI={rsi.iloc[i]:.2f}, RSI-MA={rsi_ma.iloc[i]:.2f}")

print(f"\n{'='*60}")
print(f"Date: 2025-10-13")
print(f"Current RSI: {rsi.iloc[-1]:.2f}")
print(f"Current RSI-MA (MA=14): {rsi_ma.iloc[-1]:.2f}")
print(f"Your TradingView RSI-MA: 48.48")
print(f"Difference: {abs(rsi_ma.iloc[-1] - 48.48):.2f}")
print(f"{'='*60}")

# Also test with percentage changes as source
print("\n" + "="*60)
print("Testing with PERCENTAGE CHANGES as source")
print("="*60)

pct_changes = prices.pct_change() * 100
pct_changes = pct_changes.fillna(0)
gains_pct = pct_changes.where(pct_changes > 0, 0)
losses_pct = -pct_changes.where(pct_changes < 0, 0)

avg_gains_pct = gains_pct.ewm(alpha=1/rsi_length, adjust=False).mean()
avg_losses_pct = losses_pct.ewm(alpha=1/rsi_length, adjust=False).mean()

rs_pct = avg_gains_pct / avg_losses_pct
rsi_pct = 100 - (100 / (1 + rs_pct))
rsi_pct = rsi_pct.replace([np.inf, -np.inf], np.nan)
rsi_pct.loc[avg_losses_pct == 0] = 100
rsi_pct.loc[avg_gains_pct == 0] = 0
rsi_pct = rsi_pct.fillna(50)

rsi_ma_pct = rsi_pct.ewm(span=ma_length, adjust=False).mean()

print("\nLast 10 values with PERCENTAGE source:")
for i in range(-10, 0):
    date = rsi_pct.index[i]
    print(f"  {date.strftime('%Y-%m-%d')}: RSI={rsi_pct.iloc[i]:.2f}, RSI-MA={rsi_ma_pct.iloc[i]:.2f}")

print(f"\n{'='*60}")
print(f"Current RSI-MA (MA=14, PCT source): {rsi_ma_pct.iloc[-1]:.2f}")
print(f"Your TradingView RSI-MA: 48.48")
print(f"Difference: {abs(rsi_ma_pct.iloc[-1] - 48.48):.2f}")
print(f"{'='*60}")
