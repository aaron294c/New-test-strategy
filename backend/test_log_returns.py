#!/usr/bin/env python3
"""Test RSI-MA using log returns as the source."""

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

print("="*70)
print("RSI-MA Calculation Comparison")
print("="*70)
print(f"\nLast 5 close prices:")
for i in range(-5, 0):
    print(f"  {prices.index[i].strftime('%Y-%m-%d')}: ${prices.iloc[i]:.2f}")

rsi_length = 14
ma_length = 14

# ===== METHOD 1: Absolute price changes (current method) =====
print(f"\n{'='*70}")
print("METHOD 1: Absolute Price Changes (prices.diff())")
print(f"{'='*70}")

changes1 = prices.diff()
gains1 = changes1.where(changes1 > 0, 0)
losses1 = -changes1.where(changes1 < 0, 0)

avg_gains1 = gains1.ewm(alpha=1/rsi_length, adjust=False).mean()
avg_losses1 = losses1.ewm(alpha=1/rsi_length, adjust=False).mean()

rs1 = avg_gains1 / avg_losses1
rsi1 = 100 - (100 / (1 + rs1))
rsi1 = rsi1.replace([np.inf, -np.inf], np.nan)
rsi1.loc[avg_losses1 == 0] = 100
rsi1.loc[avg_gains1 == 0] = 0
rsi1 = rsi1.fillna(50)

rsi_ma1 = rsi1.ewm(span=ma_length, adjust=False).mean()

print("\nLast 5 values:")
for i in range(-5, 0):
    date = prices.index[i]
    print(f"  {date.strftime('%Y-%m-%d')}: RSI={rsi1.iloc[i]:.2f}, RSI-MA={rsi_ma1.iloc[i]:.2f}")

# ===== METHOD 2: Log returns =====
print(f"\n{'='*70}")
print("METHOD 2: Log Returns (np.log(price/prev_price))")
print(f"{'='*70}")

# Calculate log returns
log_returns = np.log(prices / prices.shift(1))
log_returns = log_returns.fillna(0)

# Separate gains and losses
gains2 = log_returns.where(log_returns > 0, 0)
losses2 = -log_returns.where(log_returns < 0, 0)

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
    date = prices.index[i]
    print(f"  {date.strftime('%Y-%m-%d')}: RSI={rsi2.iloc[i]:.2f}, RSI-MA={rsi_ma2.iloc[i]:.2f}")

# ===== METHOD 3: Percentage returns =====
print(f"\n{'='*70}")
print("METHOD 3: Percentage Returns (prices.pct_change() * 100)")
print(f"{'='*70}")

pct_returns = prices.pct_change() * 100
pct_returns = pct_returns.fillna(0)

gains3 = pct_returns.where(pct_returns > 0, 0)
losses3 = -pct_returns.where(pct_returns < 0, 0)

avg_gains3 = gains3.ewm(alpha=1/rsi_length, adjust=False).mean()
avg_losses3 = losses3.ewm(alpha=1/rsi_length, adjust=False).mean()

rs3 = avg_gains3 / avg_losses3
rsi3 = 100 - (100 / (1 + rs3))
rsi3 = rsi3.replace([np.inf, -np.inf], np.nan)
rsi3.loc[avg_losses3 == 0] = 100
rsi3.loc[avg_gains3 == 0] = 0
rsi3 = rsi3.fillna(50)

rsi_ma3 = rsi3.ewm(span=ma_length, adjust=False).mean()

print("\nLast 5 values:")
for i in range(-5, 0):
    date = prices.index[i]
    print(f"  {date.strftime('%Y-%m-%d')}: RSI={rsi3.iloc[i]:.2f}, RSI-MA={rsi_ma3.iloc[i]:.2f}")

# ===== COMPARISON =====
print(f"\n{'='*70}")
print("COMPARISON - RSI-MA on 2025-10-13")
print(f"{'='*70}")
print(f"Method 1 (Absolute changes): {rsi_ma1.iloc[-1]:.2f}")
print(f"Method 2 (Log returns):      {rsi_ma2.iloc[-1]:.2f}")
print(f"Method 3 (Percentage):       {rsi_ma3.iloc[-1]:.2f}")
print(f"\nYour TradingView value:      48.48")
print(f"\nDifference from TradingView:")
print(f"  Method 1: {abs(rsi_ma1.iloc[-1] - 48.48):.2f}")
print(f"  Method 2: {abs(rsi_ma2.iloc[-1] - 48.48):.2f}")
print(f"  Method 3: {abs(rsi_ma3.iloc[-1] - 48.48):.2f}")

closest = min(
    ('Absolute changes', abs(rsi_ma1.iloc[-1] - 48.48)),
    ('Log returns', abs(rsi_ma2.iloc[-1] - 48.48)),
    ('Percentage returns', abs(rsi_ma3.iloc[-1] - 48.48)),
    key=lambda x: x[1]
)

print(f"\n✓ Closest method: {closest[0]} (diff: {closest[1]:.2f})")

# Show detailed comparison for last 10 days
print(f"\n{'='*70}")
print("DETAILED COMPARISON - Last 10 Days")
print(f"{'='*70}")
print(f"\n{'Date':<12} {'Price':>8} {'Abs RSI-MA':>11} {'Log RSI-MA':>11} {'Pct RSI-MA':>11}")
print(f"{'-'*12} {'-'*8} {'-'*11} {'-'*11} {'-'*11}")
for i in range(-10, 0):
    date = prices.index[i]
    print(f"{date.strftime('%Y-%m-%d'):<12} ${prices.iloc[i]:>7.2f} "
          f"{rsi_ma1.iloc[i]:>11.2f} {rsi_ma2.iloc[i]:>11.2f} {rsi_ma3.iloc[i]:>11.2f}")

print(f"\n{'='*70}")
print("ANALYSIS")
print(f"{'='*70}")
print("\nLog returns make sense when:")
print("  ✓ You want symmetric treatment of gains/losses")
print("  ✓ You're comparing assets with different price levels")
print("  ✓ You want to analyze geometric returns")
print("\nFor RSI specifically:")
print("  • Traditional RSI uses absolute price changes")
print("  • Log returns normalize by price level")
print("  • All three methods show similar patterns but different magnitudes")
print("\nStandard TradingView RSI uses: Absolute price changes (ta.change(close))")
