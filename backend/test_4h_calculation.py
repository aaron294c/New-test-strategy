#!/usr/bin/env python3
"""
Test 4H RSI-MA calculation to debug why it's producing NaN
"""

import yfinance as yf
import pandas as pd
import numpy as np

ticker = "AAPL"

# Fetch hourly data
ticker_obj = yf.Ticker(ticker)
hourly_data = ticker_obj.history(interval='1h', period='730d')

print(f"Fetched {len(hourly_data)} hourly data points")
print(f"Date range: {hourly_data.index[0]} to {hourly_data.index[-1]}")
print(f"\nLast 5 hourly data points:")
print(hourly_data.tail())

# Resample to 4H
data_4h = hourly_data.resample('4H').agg({
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
}).dropna()

print(f"\n4H data: {len(data_4h)} points")
print(f"Date range: {data_4h.index[0]} to {data_4h.index[-1]}")
print(f"\nLast 5 4H data points:")
print(data_4h.tail())

# Calculate RSI-MA on 4H
rsi_length = 14
ma_length = 14

close = data_4h['Close']
delta = close.diff()
gain = delta.where(delta > 0, 0.0)
loss = -delta.where(delta < 0, 0.0)

avg_gain = gain.rolling(window=rsi_length).mean()
avg_loss = loss.rolling(window=rsi_length).mean()

rs = avg_gain / avg_loss
rsi = 100 - (100 / (1 + rs))
rsi_ma = rsi.rolling(window=ma_length).mean()

print(f"\n4H RSI-MA: {len(rsi_ma.dropna())} valid points")
print(f"\nLast 10 4H RSI-MA values:")
print(rsi_ma.tail(10))

# Resample to daily
rsi_ma_daily = rsi_ma.resample('1D').last()

print(f"\nDaily-aligned 4H RSI-MA: {len(rsi_ma_daily.dropna())} valid points")
print(f"\nLast 10 daily-aligned values:")
print(rsi_ma_daily.tail(10))

# Check for NaN in recent data
recent = rsi_ma_daily.tail(30)
nan_count = recent.isna().sum()
print(f"\nNaN count in last 30 days: {nan_count}")
