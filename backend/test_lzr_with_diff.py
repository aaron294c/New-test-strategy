#!/usr/bin/env python3
"""Test LzR with diff() method like the working script."""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

def test_lzr_variants_with_diff(ticker, expected_rsi_ma):
    """Test different ways of applying the working diff() method."""
    stock = yf.Ticker(ticker)
    data = stock.history(period="1y", interval="1d")

    if data.empty:
        return None

    close_price = data['Close']

    print(f"\n{ticker}:")
    print("="*70)

    results = []

    # Method 1: Original working method (for reference)
    daily_returns = close_price.pct_change().fillna(0)
    delta = daily_returns.diff()
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    avg_gains = gains.ewm(alpha=1/14, adjust=False).mean()
    avg_losses = losses.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(50)
    rsi_ma = rsi.ewm(span=14, adjust=False).mean()

    diff = abs(rsi_ma.iloc[-1] - expected_rsi_ma)
    results.append(('Working method: pct_change -> diff -> RSI -> EMA', rsi_ma.iloc[-1], diff))

    # Method 2: LzR then diff (like working method)
    log_returns = np.log(close_price / close_price.shift(1))
    lookback = 30
    rolling_mean = log_returns.rolling(window=lookback, min_periods=lookback).mean()
    rolling_std = log_returns.rolling(window=lookback, min_periods=lookback).std()
    z_scores = (log_returns - rolling_mean) / rolling_std
    z_scores = z_scores.fillna(0)
    lzr = z_scores.ewm(span=7, adjust=False).mean()

    # Apply diff() to LzR
    delta_lzr = lzr.diff()
    gains = delta_lzr.where(delta_lzr > 0, 0)
    losses = -delta_lzr.where(delta_lzr < 0, 0)
    avg_gains = gains.ewm(alpha=1/14, adjust=False).mean()
    avg_losses = losses.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(50)
    rsi_ma = rsi.ewm(span=14, adjust=False).mean()

    diff = abs(rsi_ma.iloc[-1] - expected_rsi_ma)
    results.append(('LzR -> diff() -> RSI -> EMA', rsi_ma.iloc[-1], diff))

    # Method 3: Direct RSI on LzR (what I implemented)
    gains = lzr.where(lzr > 0, 0)
    losses = -lzr.where(lzr < 0, 0)
    avg_gains = gains.ewm(alpha=1/14, adjust=False).mean()
    avg_losses = losses.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.replace([np.inf, -np.inf], np.nan)
    rsi.loc[avg_losses == 0] = 100
    rsi.loc[avg_gains == 0] = 0
    rsi = rsi.fillna(50)
    rsi_ma = rsi.ewm(span=14, adjust=False).mean()

    diff = abs(rsi_ma.iloc[-1] - expected_rsi_ma)
    results.append(('Direct RSI on LzR -> EMA (current implementation)', rsi_ma.iloc[-1], diff))

    # Method 4: Log returns -> diff (no z-score)
    log_returns = np.log(close_price / close_price.shift(1)).fillna(0)
    delta_log = log_returns.diff()
    gains = delta_log.where(delta_log > 0, 0)
    losses = -delta_log.where(delta_log < 0, 0)
    avg_gains = gains.ewm(alpha=1/14, adjust=False).mean()
    avg_losses = losses.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(50)
    rsi_ma = rsi.ewm(span=14, adjust=False).mean()

    diff = abs(rsi_ma.iloc[-1] - expected_rsi_ma)
    results.append(('Log returns -> diff -> RSI -> EMA', rsi_ma.iloc[-1], diff))

    # Sort by difference
    results.sort(key=lambda x: x[2])

    # Print results
    for name, value, diff in results:
        marker = ' *** MATCH ***' if diff < 0.5 else (' ** CLOSE **' if diff < 1.0 else '')
        print(f'  {name:<55} {value:7.2f}  (diff: {diff:5.2f}){marker}')

    return results

# Test with AAPL and MSFT
print("="*80)
print("TESTING LzR WITH diff() METHOD")
print("="*80)
print(f"Current time: {datetime.now()}\n")

aapl_results = test_lzr_variants_with_diff('AAPL', 48.60)  # Mid-range of 47.82-49.37
msft_results = test_lzr_variants_with_diff('MSFT', 49.54)

print("\n" + "="*80)
print("BEST MATCHES:")
print("="*80)

if aapl_results:
    best = aapl_results[0]
    print(f'\nAAPL: {best[0]} = {best[1]:.2f} (target: 48.60, diff: {best[2]:.2f})')

if msft_results:
    best = msft_results[0]
    print(f'MSFT: {best[0]} = {best[1]:.2f} (target: 49.54, diff: {best[2]:.2f})')

print('\n' + "="*80)
