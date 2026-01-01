#!/usr/bin/env python3
"""Test RSI-MA with both absolute price changes and percentage returns."""

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
print(f"Last 5 close prices:")
for i in range(-5, 0):
    print(f"  {prices.index[i].strftime('%Y-%m-%d')}: ${prices.iloc[i]:.2f}")

# ===== METHOD 1: Absolute price changes (what we're currently using) =====
print(f"\n{'='*60}")
print("METHOD 1: Absolute Price Changes (prices.diff())")
print(f"{'='*60}")

changes1 = prices.diff()
gains1 = changes1.where(changes1 > 0, 0)
losses1 = -changes1.where(changes1 < 0, 0)

rsi_length = 14
avg_gains1 = gains1.ewm(alpha=1/rsi_length, adjust=False).mean()
avg_losses1 = losses1.ewm(alpha=1/rsi_length, adjust=False).mean()

rs1 = avg_gains1 / avg_losses1
rsi1 = 100 - (100 / (1 + rs1))
rsi1 = rsi1.replace([np.inf, -np.inf], np.nan)
rsi1.loc[avg_losses1 == 0] = 100
rsi1.loc[avg_gains1 == 0] = 0
rsi1 = rsi1.fillna(50)

ma_length = 13
rsi_ma1 = rsi1.ewm(span=ma_length, adjust=False).mean()

print("\nLast 5 values:")
for i in range(-5, 0):
    print(f"  {rsi1.index[i].strftime('%Y-%m-%d')}: RSI={rsi1.iloc[i]:.2f}, RSI-MA={rsi_ma1.iloc[i]:.2f}")

# ===== METHOD 2: Percentage returns (alternative interpretation) =====
print(f"\n{'='*60}")
print("METHOD 2: Percentage Returns (prices.pct_change() * 100)")
print(f"{'='*60}")

changes2 = prices.pct_change() * 100  # Convert to percentage
changes2 = changes2.fillna(0)
gains2 = changes2.where(changes2 > 0, 0)
losses2 = -changes2.where(changes2 < 0, 0)

avg_gains2 = gains2.ewm(alpha=1/rsi_length, adjust=False).mean()
avg_losses2 = losses2.ewm(alpha=1/rsi_length, adjust=False).mean()

rs2 = avg_gains2 / avg_losses2
rsi2 = 100 - (100 / (1 + rs2))
rsi2 = rsi2.replace([np.inf, -np.inf], np.nan)
rsi2.loc[avg_losses2 == 0] = 100
rsi2.loc[avg_gains2 == 0] = 0
rsi2 = rsi2.fillna(50)

rsi_ma2 = rsi2.ewm(span=ma_length, adjust=False).mean()

print("\nLast 5 values:")
for i in range(-5, 0):
    print(f"  {rsi2.index[i].strftime('%Y-%m-%d')}: RSI={rsi2.iloc[i]:.2f}, RSI-MA={rsi_ma2.iloc[i]:.2f}")

# ===== COMPARISON =====
print(f"\n{'='*60}")
print("COMPARISON")
print(f"{'='*60}")
print(f"Current RSI-MA (Method 1 - Absolute): {rsi_ma1.iloc[-1]:.2f}")
print(f"Current RSI-MA (Method 2 - Percentage): {rsi_ma2.iloc[-1]:.2f}")
print(f"Your TradingView value: 48.48")
print(f"\nDifference Method 1: {abs(rsi_ma1.iloc[-1] - 48.48):.2f}")
print(f"Difference Method 2: {abs(rsi_ma2.iloc[-1] - 48.48):.2f}")

if abs(rsi_ma2.iloc[-1] - 48.48) < abs(rsi_ma1.iloc[-1] - 48.48):
    print("\n✓ Method 2 (Percentage Returns) is closer!")
else:
    print("\n✓ Method 1 (Absolute Changes) is closer!")
