#!/usr/bin/env python3
"""Check current RSI-MA for AAPL with latest data."""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# Fetch AAPL data with different periods
ticker = "AAPL"
print(f"Checking {ticker} RSI-MA calculation...")
print(f"Current time: {datetime.now()}")

# Try to get the most recent data
stock = yf.Ticker(ticker)

# Get 1 year of data
data = stock.history(period="1y", interval="1d")

if data.empty:
    print("Failed to fetch data")
    exit(1)

print(f"\nFetched {len(data)} data points")
print(f"Date range: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
print(f"Last update: {data.index[-1]}")

prices = data['Close']

# Show last 5 close prices
print("\nLast 5 close prices:")
for i in range(-5, 0):
    date = prices.index[i]
    print(f"  {date.strftime('%Y-%m-%d')}: ${prices.iloc[i]:.2f}")

# Calculate RSI using TradingView method
print("\n=== Calculating RSI-MA (TradingView method) ===")

# Step 1: Price changes
changes = prices.diff()

# Step 2: Gains and losses
gains = changes.where(changes > 0, 0)
losses = -changes.where(changes < 0, 0)

# Step 3: RMA (Wilder's smoothing)
rsi_length = 14
avg_gains = gains.ewm(alpha=1/rsi_length, adjust=False).mean()
avg_losses = losses.ewm(alpha=1/rsi_length, adjust=False).mean()

# Step 4: RSI
rs = avg_gains / avg_losses
rsi = 100 - (100 / (1 + rs))
rsi = rsi.replace([np.inf, -np.inf], np.nan)
rsi.loc[avg_losses == 0] = 100
rsi.loc[avg_gains == 0] = 0
rsi = rsi.fillna(50)

# Step 5: EMA to RSI
ma_length = 13
rsi_ma = rsi.ewm(span=ma_length, adjust=False).mean()

# Show last 5 values
print("\nLast 5 RSI and RSI-MA values:")
for i in range(-5, 0):
    date = rsi.index[i]
    print(f"  {date.strftime('%Y-%m-%d')}: RSI={rsi.iloc[i]:.2f}, RSI-MA={rsi_ma.iloc[i]:.2f}")

print(f"\n{'='*60}")
print(f"CURRENT RSI-MA VALUE: {rsi_ma.iloc[-1]:.2f}")
print(f"Your TradingView value: 48.48")
print(f"Difference: {abs(rsi_ma.iloc[-1] - 48.48):.2f}")
print(f"{'='*60}")

# Also try fetching with 1-hour interval to see if there's intraday data
print("\n\nTrying to fetch intraday data (1 hour interval, last 5 days)...")
intraday = stock.history(period="5d", interval="1h")
if not intraday.empty:
    print(f"Last intraday update: {intraday.index[-1]}")
    print(f"Last intraday close: ${intraday['Close'].iloc[-1]:.2f}")
