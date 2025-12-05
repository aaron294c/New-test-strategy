#!/usr/bin/env python3
"""
Test GOOGL divergence to verify if percentiles are calculated correctly
"""

import yfinance as yf
import pandas as pd
import numpy as np

ticker = "GOOGL"

# Fetch daily data
ticker_obj = yf.Ticker(ticker)
daily_data = ticker_obj.history(interval='1d', period='500d')

print(f"=== DAILY DATA ===")
print(f"Fetched {len(daily_data)} daily data points")
print(f"Latest daily close: ${daily_data['Close'].iloc[-1]:.2f}")

# Calculate daily RSI-MA using CORRECT method from RSI indicator tab
rsi_length = 14
ma_length = 14

close = daily_data['Close']

# Step 1: Log returns
log_returns = np.log(close / close.shift(1)).fillna(0)

# Step 2: Change of returns (second derivative)
delta = log_returns.diff()

# Step 3: RSI on delta
gains = delta.where(delta > 0, 0)
losses = -delta.where(delta < 0, 0)

avg_gains = gains.ewm(alpha=1/rsi_length, adjust=False).mean()
avg_losses = losses.ewm(alpha=1/rsi_length, adjust=False).mean()

rs = avg_gains / avg_losses
rsi = 100 - (100 / (1 + rs))
rsi = rsi.fillna(50)

# Step 4: EMA smoothing
rsi_ma_daily = rsi.ewm(span=ma_length, adjust=False).mean()

print(f"\nLatest DAILY RSI-MA: {rsi_ma_daily.iloc[-1]:.2f}")
print(f"Last 5 daily RSI-MA values:")
print(rsi_ma_daily.tail(5))

# Calculate daily percentile
daily_percentiles = rsi_ma_daily.rolling(window=252).apply(
    lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100,
    raw=False
)
print(f"\nLatest DAILY Percentile: {daily_percentiles.iloc[-1]:.2f}%")

# Fetch hourly and calculate 4H
hourly_data = ticker_obj.history(interval='1h', period='730d')

print(f"\n=== 4-HOURLY DATA ===")
print(f"Fetched {len(hourly_data)} hourly data points")

# Resample to 4H
data_4h = hourly_data.resample('4h').agg({
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
}).dropna()

print(f"4H bars: {len(data_4h)}")
print(f"Latest 4H close: ${data_4h['Close'].iloc[-1]:.2f}")

# Calculate 4H RSI-MA using CORRECT method
close_4h = data_4h['Close']

# Step 1: Log returns
log_returns_4h = np.log(close_4h / close_4h.shift(1)).fillna(0)

# Step 2: Change of returns
delta_4h = log_returns_4h.diff()

# Step 3: RSI on delta
gains_4h = delta_4h.where(delta_4h > 0, 0)
losses_4h = -delta_4h.where(delta_4h < 0, 0)

avg_gains_4h = gains_4h.ewm(alpha=1/rsi_length, adjust=False).mean()
avg_losses_4h = losses_4h.ewm(alpha=1/rsi_length, adjust=False).mean()

rs_4h = avg_gains_4h / avg_losses_4h
rsi_4h = 100 - (100 / (1 + rs_4h))
rsi_4h = rsi_4h.fillna(50)

# Step 4: EMA smoothing
rsi_ma_4h = rsi_4h.ewm(span=ma_length, adjust=False).mean()

print(f"\nLatest 4H RSI-MA: {rsi_ma_4h.iloc[-1]:.2f}")
print(f"Last 5 4H RSI-MA values:")
print(rsi_ma_4h.tail(5))

# Align to daily
rsi_ma_4h_daily = rsi_ma_4h.resample('1D').last().ffill()

# Calculate 4H percentile
percentile_4h_daily = rsi_ma_4h_daily.rolling(window=252).apply(
    lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100,
    raw=False
)

print(f"\nLatest 4H Percentile (daily-aligned): {percentile_4h_daily.iloc[-1]:.2f}%")

print(f"\n=== COMPARISON ===")
print(f"Daily RSI-MA: {rsi_ma_daily.iloc[-1]:.2f} (Percentile: {daily_percentiles.iloc[-1]:.2f}%)")
print(f"4H RSI-MA: {rsi_ma_4h.iloc[-1]:.2f} (Percentile: {percentile_4h_daily.iloc[-1]:.2f}%)")

print(f"\n*** INTERPRETATION ***")
if rsi_ma_daily.iloc[-1] > rsi_ma_4h.iloc[-1]:
    print(f"Daily RSI-MA ({rsi_ma_daily.iloc[-1]:.2f}) is HIGHER than 4H RSI-MA ({rsi_ma_4h.iloc[-1]:.2f})")
    print("This means: Daily is MORE overbought than 4H")
else:
    print(f"4H RSI-MA ({rsi_ma_4h.iloc[-1]:.2f}) is HIGHER than Daily RSI-MA ({rsi_ma_daily.iloc[-1]:.2f})")
    print("This means: 4H is MORE overbought than Daily")
