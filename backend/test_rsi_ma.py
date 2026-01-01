#!/usr/bin/env python3
"""Test RSI-MA calculation against TradingView."""

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

if not data.empty:
    print(f'Fetched {len(data)} data points')
    print(f'Date range: {data.index[0]} to {data.index[-1]}')

    # Calculate RSI-MA
    print('\nCalculating RSI-MA...')
    rsi_ma = backtester.calculate_rsi_ma_indicator(data['Close'])

    # Show last 5 values with dates
    print('\nLast 5 RSI-MA values:')
    for date, value in rsi_ma.tail(5).items():
        print(f'  {date.strftime("%Y-%m-%d")}: {value:.2f}')

    # Show the most recent value
    print(f'\nMost recent RSI-MA value: {rsi_ma.iloc[-1]:.2f}')
    print(f'Expected value from TradingView: 48.48')
    print(f'Difference: {abs(rsi_ma.iloc[-1] - 48.48):.2f}')

    # Also show last close price and daily return
    print(f'\nLast close price: ${data["Close"].iloc[-1]:.2f}')
    print(f'Previous close: ${data["Close"].iloc[-2]:.2f}')
    daily_change = data["Close"].iloc[-1] - data["Close"].iloc[-2]
    daily_pct = (daily_change / data["Close"].iloc[-2]) * 100
    print(f'Daily change: ${daily_change:.2f} ({daily_pct:+.2f}%)')
else:
    print('Failed to fetch data')
