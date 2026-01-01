#!/usr/bin/env python3
"""Debug RSI calculation step-by-step to verify correctness."""

import pandas as pd
import numpy as np
import yfinance as yf

def debug_rsi_calculation(ticker):
    """Debug each step of RSI-MA calculation."""
    stock = yf.Ticker(ticker)
    data = stock.history(period="1y", interval="1d")

    if data.empty:
        return None

    close_price = data['Close']

    print(f"\n{ticker} Debug:")
    print("="*70)

    # Step 1: Log returns
    log_returns = np.log(close_price / close_price.shift(1))
    print(f"\nStep 1 - Last 5 log returns:")
    print(log_returns.tail(5))

    # Step 2: Z-scores
    lookback = 30
    rolling_mean = log_returns.rolling(window=lookback, min_periods=lookback).mean()
    rolling_std = log_returns.rolling(window=lookback, min_periods=lookback).std()
    z_scores = (log_returns - rolling_mean) / rolling_std
    z_scores = z_scores.fillna(0)

    print(f"\nStep 2 - Last 5 z-scores:")
    print(z_scores.tail(5))

    # Step 3: EMA(7) smoothing → LzR
    lzr = z_scores.ewm(span=7, adjust=False).mean()

    print(f"\nStep 3 - Last 5 LzR values (EMA7-smoothed z-scores):")
    print(lzr.tail(5))
    print(f"Last LzR: {lzr.iloc[-1]:+.4f}")

    # Step 4: RSI on LzR
    rsi_length = 14
    gains = lzr.where(lzr > 0, 0)
    losses = -lzr.where(lzr < 0, 0)

    print(f"\nStep 4a - Last 5 gains from LzR:")
    print(gains.tail(5))
    print(f"\nStep 4b - Last 5 losses from LzR:")
    print(losses.tail(5))

    avg_gains = gains.ewm(alpha=1/rsi_length, adjust=False).mean()
    avg_losses = losses.ewm(alpha=1/rsi_length, adjust=False).mean()

    print(f"\nStep 4c - Last avg_gain: {avg_gains.iloc[-1]:.6f}")
    print(f"Step 4d - Last avg_loss: {avg_losses.iloc[-1]:.6f}")

    rs = avg_gains / avg_losses
    print(f"Step 4e - Last RS: {rs.iloc[-1]:.4f}")

    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.replace([np.inf, -np.inf], np.nan)
    rsi.loc[avg_losses == 0] = 100
    rsi.loc[avg_gains == 0] = 0
    rsi = rsi.fillna(50)

    print(f"\nStep 4f - Last 5 RSI values:")
    print(rsi.tail(5))
    print(f"Last RSI: {rsi.iloc[-1]:.2f}")

    # Step 5: EMA(14) on RSI
    ma_length = 14
    rsi_ma = rsi.ewm(span=ma_length, adjust=False).mean()

    print(f"\nStep 5 - Last 5 RSI-MA values:")
    print(rsi_ma.tail(5))
    print(f"Last RSI-MA: {rsi_ma.iloc[-1]:.2f}")

    return {
        'lzr': lzr.iloc[-1],
        'rsi': rsi.iloc[-1],
        'rsi_ma': rsi_ma.iloc[-1],
        'avg_gains': avg_gains.iloc[-1],
        'avg_losses': avg_losses.iloc[-1]
    }

# Test with AAPL and MSFT
print("="*80)
print("DEBUGGING RSI CALCULATION STEP-BY-STEP")
print("="*80)

aapl_result = debug_rsi_calculation("AAPL")
msft_result = debug_rsi_calculation("MSFT")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

if aapl_result:
    print(f"\nAAPL:")
    print(f"  LzR: {aapl_result['lzr']:+.4f} (expected: -0.634)")
    print(f"  Avg Gains: {aapl_result['avg_gains']:.6f}")
    print(f"  Avg Losses: {aapl_result['avg_losses']:.6f}")
    print(f"  RSI: {aapl_result['rsi']:.2f}")
    print(f"  RSI-MA: {aapl_result['rsi_ma']:.2f} (expected: 47.82-49.37)")

if msft_result:
    print(f"\nMSFT:")
    print(f"  LzR: {msft_result['lzr']:+.4f} (expected: -0.234)")
    print(f"  Avg Gains: {msft_result['avg_gains']:.6f}")
    print(f"  Avg Losses: {msft_result['avg_losses']:.6f}")
    print(f"  RSI: {msft_result['rsi']:.2f}")
    print(f"  RSI-MA: {msft_result['rsi_ma']:.2f} (expected: 49.54)")

print("\n" + "="*80)
