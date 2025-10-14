#!/usr/bin/env python3
"""Test Ehlers filters and other transformations with given parameters."""

import pandas as pd
import numpy as np
import yfinance as yf

def ehlers_super_smoother(data, period):
    """Ehlers Super Smoother filter."""
    a1 = np.exp(-1.414 * np.pi / period)
    b1 = 2 * a1 * np.cos(1.414 * np.pi / period)
    c2 = b1
    c3 = -a1 * a1
    c1 = 1 - c2 - c3

    result = np.zeros(len(data))
    result[0] = data.iloc[0] if not pd.isna(data.iloc[0]) else 0
    result[1] = data.iloc[1] if not pd.isna(data.iloc[1]) else 0

    for i in range(2, len(data)):
        if pd.isna(data.iloc[i]):
            result[i] = result[i-1]
        else:
            result[i] = c1 * (data.iloc[i] + data.iloc[i-1]) / 2 + c2 * result[i-1] + c3 * result[i-2]

    return pd.Series(result, index=data.index)

def test_transformations(ticker, target, ma_period=7, phase=50, power=2, lookback=30):
    stock = yf.Ticker(ticker)
    data = stock.history(period='1y', interval='1d')

    close_price = data['Close']
    log_returns = np.log(close_price / close_price.shift(1))

    print(f'\n{ticker} - Target: {target}')
    print('=' * 70)

    results = []

    # Test 1: Standard z-score with EMA smoothing
    rolling_mean = log_returns.rolling(window=lookback).mean()
    rolling_std = log_returns.rolling(window=lookback).std()
    z_standard = (log_returns - rolling_mean) / rolling_std
    z_ema = z_standard.ewm(span=ma_period, adjust=False).mean()

    diff = abs(z_ema.iloc[-1] - target)
    results.append(('Standard z-score -> EMA(7)', z_ema.iloc[-1], diff))

    # Test 2: EMA of returns, then z-score
    ema_returns = log_returns.ewm(span=ma_period, adjust=False).mean()
    rolling_mean = ema_returns.rolling(window=lookback).mean()
    rolling_std = ema_returns.rolling(window=lookback).std()
    z_ema_returns = (ema_returns.iloc[-1] - rolling_mean.iloc[-1]) / rolling_std.iloc[-1]

    diff = abs(z_ema_returns - target)
    results.append(('EMA(7) of returns -> z-score', z_ema_returns, diff))

    # Test 3: Z-score, then inverse EMA
    z_inverse_ema = -z_standard.ewm(span=ma_period, adjust=False).mean()

    diff = abs(z_inverse_ema.iloc[-1] - target)
    results.append(('Inverse (z-score -> EMA(7))', z_inverse_ema.iloc[-1], diff))

    # Test 4: Power transformation
    log_returns_powered = np.sign(log_returns) * np.abs(log_returns) ** power
    rolling_mean = log_returns_powered.rolling(window=lookback).mean()
    rolling_std = log_returns_powered.rolling(window=lookback).std()
    z_powered = (log_returns_powered.iloc[-1] - rolling_mean.iloc[-1]) / rolling_std.iloc[-1]

    diff = abs(z_powered - target)
    results.append((f'Power({power}) transform -> z-score', z_powered, diff))

    # Test 5: Ehlers Super Smoother
    try:
        smoothed = ehlers_super_smoother(log_returns.fillna(0), ma_period)
        rolling_mean = smoothed.rolling(window=lookback).mean()
        rolling_std = smoothed.rolling(window=lookback).std()
        z_smooth = (smoothed.iloc[-1] - rolling_mean.iloc[-1]) / rolling_std.iloc[-1]

        diff = abs(z_smooth - target)
        results.append(('Ehlers Super Smoother -> z-score', z_smooth, diff))
    except:
        pass

    # Test 6: Momentum-based (mean of deviations)
    rolling_mean = log_returns.rolling(window=lookback).mean()
    rolling_std = log_returns.rolling(window=lookback).std()
    deviations = log_returns - rolling_mean
    momentum = deviations.rolling(window=ma_period).mean()
    z_momentum = momentum.iloc[-1] / rolling_std.iloc[-1]

    diff = abs(z_momentum - target) if not np.isnan(z_momentum) else float('inf')
    results.append(('Momentum (rolling deviation MA) / std', z_momentum, diff))

    # Test 7: Inverse momentum
    z_inv_momentum = -z_momentum
    diff = abs(z_inv_momentum - target) if not np.isnan(z_inv_momentum) else float('inf')
    results.append(('INVERSE Momentum', z_inv_momentum, diff))

    # Sort by difference
    results.sort(key=lambda x: x[2])

    # Print results
    for name, value, diff in results:
        marker = ' *** CLOSE MATCH ***' if diff < 0.15 else (' ** MATCH **' if diff < 0.3 else '')
        print(f'  {name:<45} {value:+7.4f}  (diff: {diff:.4f}){marker}')

    return results

print('='*80)
print('TESTING VARIOUS TRANSFORMATIONS WITH YOUR PARAMETERS')
print('Parameters: MA=7, Phase=50, Power=2, Lookback=30')
print('='*80)

aapl_results = test_transformations('AAPL', -0.634, ma_period=7, phase=50, power=2, lookback=30)
msft_results = test_transformations('MSFT', -0.234, ma_period=7, phase=50, power=2, lookback=30)

print('\n' + '='*80)
print('BEST MATCHES:')
print('='*80)

if aapl_results:
    print(f'\nAAPL: {aapl_results[0][0]} = {aapl_results[0][1]:+.4f} (target: -0.634, diff: {aapl_results[0][2]:.4f})')

if msft_results:
    print(f'MSFT: {msft_results[0][0]} = {msft_results[0][1]:+.4f} (target: -0.234, diff: {msft_results[0][2]:.4f})')

print('\n' + '='*80)
