#!/usr/bin/env python3
"""
Diagnose why TradingView shows RSI-MA = 48.48 but we're calculating 62.87

Possible reasons:
1. Different date/time (TradingView vs Yahoo Finance)
2. Different price data source
3. Different calculation method
4. Confusion between RSI and RSI-MA
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

ticker = "AAPL"
print(f"{'='*70}")
print(f"DIAGNOSING TRADINGVIEW MISMATCH FOR {ticker}")
print(f"{'='*70}")
print(f"User says TradingView shows RSI-MA = 48.48 on 2025-10-13")
print(f"We're calculating RSI-MA = 62.87 on 2025-10-13")
print(f"{'='*70}\n")

# Fetch data
stock = yf.Ticker(ticker)
data = stock.history(period="2y", interval="1d")

if data.empty:
    print("Failed to fetch data")
    exit(1)

prices = data['Close']
print(f"Data source: Yahoo Finance")
print(f"Total data points: {len(data)}")
print(f"Date range: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")

# Calculate RSI and RSI-MA
changes = prices.diff()
gains = changes.where(changes > 0, 0)
losses = -changes.where(changes < 0, 0)

rsi_length = 14
ma_length = 14

avg_gains = gains.ewm(alpha=1/rsi_length, adjust=False).mean()
avg_losses = losses.ewm(alpha=1/rsi_length, adjust=False).mean()

rs = avg_gains / avg_losses
rsi = 100 - (100 / (1 + rs))
rsi = rsi.replace([np.inf, -np.inf], np.nan)
rsi.loc[avg_losses == 0] = 100
rsi.loc[avg_gains == 0] = 0
rsi = rsi.fillna(50)

rsi_ma = rsi.ewm(span=ma_length, adjust=False).mean()

# Find dates where RSI-MA is close to 48.48
print(f"\n{'='*70}")
print(f"SEARCHING FOR RSI-MA VALUES NEAR 48.48")
print(f"{'='*70}\n")

target = 48.48
tolerance = 1.0

matches = []
for i in range(len(rsi_ma)):
    if abs(rsi_ma.iloc[i] - target) < tolerance:
        matches.append((rsi_ma.index[i], rsi_ma.iloc[i], rsi.iloc[i], prices.iloc[i]))

if matches:
    print(f"Found {len(matches)} dates where RSI-MA is within {tolerance} of {target}:")
    for date, rsi_ma_val, rsi_val, price in matches[-20:]:  # Show last 20
        print(f"  {date.strftime('%Y-%m-%d')}: RSI-MA={rsi_ma_val:.2f}, RSI={rsi_val:.2f}, Price=${price:.2f}")
else:
    print(f"No dates found where RSI-MA is close to {target}")
    print(f"\nLet's check if {target} might be the RSI value (not RSI-MA):")

    rsi_matches = []
    for i in range(len(rsi)):
        if abs(rsi.iloc[i] - target) < tolerance:
            rsi_matches.append((rsi.index[i], rsi.iloc[i], rsi_ma.iloc[i], prices.iloc[i]))

    if rsi_matches:
        print(f"\nFound {len(rsi_matches)} dates where RSI (not RSI-MA) is within {tolerance} of {target}:")
        for date, rsi_val, rsi_ma_val, price in rsi_matches[-10:]:  # Show last 10
            print(f"  {date.strftime('%Y-%m-%d')}: RSI={rsi_val:.2f}, RSI-MA={rsi_ma_val:.2f}, Price=${price:.2f}")

# Show current values
print(f"\n{'='*70}")
print(f"CURRENT VALUES (2025-10-13)")
print(f"{'='*70}")
last_date = prices.index[-1].strftime('%Y-%m-%d')
print(f"Date: {last_date}")
print(f"Close Price: ${prices.iloc[-1]:.2f}")
print(f"RSI: {rsi.iloc[-1]:.2f}")
print(f"RSI-MA: {rsi_ma.iloc[-1]:.2f}")
print(f"\nTradingView value: 48.48")
print(f"Difference: {abs(rsi_ma.iloc[-1] - 48.48):.2f}")

# Check recent price action
print(f"\n{'='*70}")
print(f"RECENT PRICE ACTION (Last 30 days)")
print(f"{'='*70}\n")
print(f"{'Date':<12} {'Close':>8} {'Change':>8} {'RSI':>6} {'RSI-MA':>7}")
print(f"{'-'*12} {'-'*8} {'-'*8} {'-'*6} {'-'*7}")
for i in range(-30, 0):
    date = prices.index[i]
    price = prices.iloc[i]
    if i > -len(prices):
        change = prices.iloc[i] - prices.iloc[i-1]
    else:
        change = 0
    print(f"{date.strftime('%Y-%m-%d'):<12} ${price:>7.2f} ${change:>+7.2f} {rsi.iloc[i]:>6.2f} {rsi_ma.iloc[i]:>7.2f}")

print(f"\n{'='*70}")
print(f"POSSIBLE EXPLANATIONS")
print(f"{'='*70}")
print(f"1. Data source difference: TradingView uses different price data")
print(f"2. Time zone difference: TradingView might be using different closing times")
print(f"3. Real-time vs EOD: TradingView might be showing intraday data")
print(f"4. Indicator confusion: User might be looking at RSI instead of RSI-MA")
print(f"5. Different date: User might be looking at a historical date")
print(f"\nPlease verify in TradingView:")
print(f"  - Which indicator line you're viewing (RSI or RSI-MA?)")
print(f"  - What is the close price shown for 2025-10-13?")
print(f"  - What date is the chart actually showing?")
