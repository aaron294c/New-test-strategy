#!/usr/bin/env python3
"""Test different ways of applying RSI to LzR values."""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

def calculate_lzr(close_price):
    """Calculate LzR: log returns -> z-score -> EMA(7)."""
    log_returns = np.log(close_price / close_price.shift(1))

    lookback = 30
    rolling_mean = log_returns.rolling(window=lookback, min_periods=lookback).mean()
    rolling_std = log_returns.rolling(window=lookback, min_periods=lookback).std()
    z_scores = (log_returns - rolling_mean) / rolling_std
    z_scores = z_scores.fillna(0)

    lzr = z_scores.ewm(span=7, adjust=False).mean()
    return lzr

def test_rsi_variants(ticker, target_rsi_ma):
    """Test different RSI calculation variants on LzR."""
    stock = yf.Ticker(ticker)
    data = stock.history(period="1y", interval="1d")

    if data.empty:
        return None

    close_price = data['Close']
    lzr = calculate_lzr(close_price)

    print(f"\n{ticker}:")
    print("="*70)
    print(f"Last LzR value: {lzr.iloc[-1]:+.4f}")
    print(f"Target RSI-MA: {target_rsi_ma}")
    print()

    results = []

    # Variant 1: Standard RSI on LzR, then EMA(14)
    rsi_length = 14
    gains = lzr.where(lzr > 0, 0)
    losses = -lzr.where(lzr < 0, 0)
    avg_gains = gains.ewm(alpha=1/rsi_length, adjust=False).mean()
    avg_losses = losses.ewm(alpha=1/rsi_length, adjust=False).mean()
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.replace([np.inf, -np.inf], np.nan)
    rsi.loc[avg_losses == 0] = 100
    rsi.loc[avg_gains == 0] = 0
    rsi = rsi.fillna(50)
    rsi_ma = rsi.ewm(span=14, adjust=False).mean()

    diff = abs(rsi_ma.iloc[-1] - target_rsi_ma)
    results.append(('Standard RSI(14) -> EMA(14)', rsi_ma.iloc[-1], diff))

    # Variant 2: RSI with different MA length
    for ma_len in [5, 7, 10, 12]:
        rsi_ma_var = rsi.ewm(span=ma_len, adjust=False).mean()
        diff = abs(rsi_ma_var.iloc[-1] - target_rsi_ma)
        results.append((f'Standard RSI(14) -> EMA({ma_len})', rsi_ma_var.iloc[-1], diff))

    # Variant 3: Different RSI lengths
    for rsi_len in [7, 10, 21]:
        gains = lzr.where(lzr > 0, 0)
        losses = -lzr.where(lzr < 0, 0)
        avg_gains = gains.ewm(alpha=1/rsi_len, adjust=False).mean()
        avg_losses = losses.ewm(alpha=1/rsi_len, adjust=False).mean()
        rs = avg_gains / avg_losses
        rsi_var = 100 - (100 / (1 + rs))
        rsi_var = rsi_var.replace([np.inf, -np.inf], np.nan)
        rsi_var.loc[avg_losses == 0] = 100
        rsi_var.loc[avg_gains == 0] = 0
        rsi_var = rsi_var.fillna(50)
        rsi_ma_var = rsi_var.ewm(span=14, adjust=False).mean()
        diff = abs(rsi_ma_var.iloc[-1] - target_rsi_ma)
        results.append((f'RSI({rsi_len}) -> EMA(14)', rsi_ma_var.iloc[-1], diff))

    # Variant 4: SMA instead of EMA for final smoothing
    rsi_sma = rsi.rolling(window=14).mean()
    diff = abs(rsi_sma.iloc[-1] - target_rsi_ma)
    results.append(('Standard RSI(14) -> SMA(14)', rsi_sma.iloc[-1], diff))

    # Variant 5: No final smoothing (just RSI)
    diff = abs(rsi.iloc[-1] - target_rsi_ma)
    results.append(('RSI(14) only (no MA)', rsi.iloc[-1], diff))

    # Variant 6: VAR smoothing (from previous tests)
    def var_func(source, length=5):
        valpha = 2 / (length + 1)
        var_values = np.zeros(len(source))
        var_values[0] = source.iloc[0] if not pd.isna(source.iloc[0]) else 50.0

        for i in range(1, len(source)):
            start_idx = max(0, i - 9)
            vud1 = 0.0
            vdd1 = 0.0

            for j in range(start_idx + 1, i + 1):
                if not pd.isna(source.iloc[j]) and not pd.isna(source.iloc[j-1]):
                    if source.iloc[j] > source.iloc[j-1]:
                        vud1 += source.iloc[j] - source.iloc[j-1]
                    elif source.iloc[j] < source.iloc[j-1]:
                        vdd1 += source.iloc[j-1] - source.iloc[j]

            if vud1 + vdd1 == 0:
                vcmo = 0
            else:
                vcmo = (vud1 - vdd1) / (vud1 + vdd1)

            alpha_abs_cmo = valpha * abs(vcmo)
            if pd.isna(source.iloc[i]):
                var_values[i] = var_values[i-1]
            else:
                var_values[i] = alpha_abs_cmo * source.iloc[i] + (1 - alpha_abs_cmo) * var_values[i-1]

        return pd.Series(var_values, index=source.index)

    rsi_var = var_func(rsi, length=5)
    diff = abs(rsi_var.iloc[-1] - target_rsi_ma)
    results.append(('RSI(14) -> VAR(5)', rsi_var.iloc[-1], diff))

    # Sort by difference
    results.sort(key=lambda x: x[2])

    # Print results
    for name, value, diff in results:
        marker = ' *** CLOSE MATCH ***' if diff < 1.0 else (' ** GOOD **' if diff < 2.0 else '')
        print(f'  {name:<35} {value:7.2f}  (diff: {diff:5.2f}){marker}')

    return results

# Test with AAPL and MSFT
print("="*80)
print("TESTING RSI VARIANTS ON LzR VALUES")
print("="*80)
print(f"Current time: {datetime.now()}\n")

aapl_results = test_rsi_variants('AAPL', 48.60)  # Mid-range of 47.82-49.37
msft_results = test_rsi_variants('MSFT', 49.54)

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
