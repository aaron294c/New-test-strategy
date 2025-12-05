#!/usr/bin/env python3
"""Debug RSI-MA calculation step-by-step to match TradingView."""

import pandas as pd
import numpy as np
from enhanced_backtester import EnhancedPerformanceMatrixBacktester

# Create backtester
backtester = EnhancedPerformanceMatrixBacktester(
    tickers=['AAPL'],
    rsi_length=14,
    ma_length=13,
    lookback_period=500
)

# Fetch data
print('Fetching AAPL data...')
data = backtester.fetch_data('AAPL')

if data.empty:
    print('Failed to fetch data')
    exit(1)

print(f'\nFetched {len(data)} data points')
print(f'Date range: {data.index[0].strftime("%Y-%m-%d")} to {data.index[-1].strftime("%Y-%m-%d")}')

prices = data['Close']

# Step 1: Calculate price changes (ta.change(close) in TradingView)
print('\n=== Step 1: Calculate price changes ===')
changes = prices.diff()
print('\nLast 5 price changes:')
for date, value in changes.tail(5).items():
    idx = prices.index.get_loc(date)
    if idx > 0:
        prev_price = prices.iloc[idx-1]
        curr_price = prices.iloc[idx]
        print(f'  {date.strftime("%Y-%m-%d")}: ${prev_price:.2f} -> ${curr_price:.2f} = ${value:.2f}')

# Step 2: Separate gains and losses
print('\n=== Step 2: Separate gains and losses ===')
gains = changes.where(changes > 0, 0)
losses = -changes.where(changes < 0, 0)
print('\nLast 5 gains/losses:')
for i in range(-5, 0):
    date = changes.index[i]
    print(f'  {date.strftime("%Y-%m-%d")}: gain=${gains.iloc[i]:.2f}, loss=${losses.iloc[i]:.2f}')

# Step 3: Apply RMA (Wilder's smoothing)
print('\n=== Step 3: Apply RMA (Wilder\'s smoothing) ===')
print(f'Alpha = 1/{14} = {1/14:.6f}')
avg_gains = gains.ewm(alpha=1/14, adjust=False).mean()
avg_losses = losses.ewm(alpha=1/14, adjust=False).mean()
print('\nLast 5 average gains/losses:')
for i in range(-5, 0):
    date = changes.index[i]
    print(f'  {date.strftime("%Y-%m-%d")}: avg_gain=${avg_gains.iloc[i]:.2f}, avg_loss=${avg_losses.iloc[i]:.2f}')

# Step 4: Calculate RSI
print('\n=== Step 4: Calculate RSI ===')
rs = avg_gains / avg_losses
rsi = 100 - (100 / (1 + rs))
rsi = rsi.replace([np.inf, -np.inf], np.nan)
rsi.loc[avg_losses == 0] = 100
rsi.loc[avg_gains == 0] = 0
rsi = rsi.fillna(50)
print('\nLast 5 RSI values:')
for i in range(-5, 0):
    date = rsi.index[i]
    print(f'  {date.strftime("%Y-%m-%d")}: {rsi.iloc[i]:.2f}')

# Step 5: Apply EMA to RSI
print('\n=== Step 5: Apply EMA (span=13) to RSI ===')
rsi_ma = rsi.ewm(span=13, adjust=False).mean()
print('\nLast 10 RSI-MA values:')
for i in range(-10, 0):
    date = rsi_ma.index[i]
    print(f'  {date.strftime("%Y-%m-%d")}: RSI={rsi.iloc[i]:.2f}, RSI-MA={rsi_ma.iloc[i]:.2f}')

print(f'\n=== FINAL RESULT ===')
print(f'Most recent RSI-MA: {rsi_ma.iloc[-1]:.2f}')
print(f'Expected from TradingView: 48.48')
print(f'Difference: {abs(rsi_ma.iloc[-1] - 48.48):.2f}')
