#!/usr/bin/env python3
"""Test the corrected RSI-MA calculation with MA length 18."""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

def calculate_rsi_ma(ticker, ma_length=18):
    """Calculate RSI-MA with the enhanced method."""
    stock = yf.Ticker(ticker)
    data = stock.history(period="1y", interval="1d")

    if data.empty:
        return None, None

    # Step 1: Calculate Mean Price from OHLC
    op = data['Open']
    hi = data['High']
    lo = data['Low']
    cl = data['Close']
    hl2 = (hi + lo) / 2

    bar_nt = (op * 1 + hi * 2 + lo * 2 + cl * 3 + hl2 * 2 + hl2 * 2) / 12
    bar_up = (op * 1 + hi * 4 + lo * 2 + cl * 5 + hl2 * 3 + hl2 * 3) / 18
    bar_dn = (op * 1 + hi * 2 + lo * 4 + cl * 5 + hl2 * 3 + hl2 * 3) / 18

    hc = np.abs(hi - cl)
    lc = np.abs(lo - cl)

    mean_price = pd.Series(index=data.index, dtype=float)
    for i in range(len(data)):
        if cl.iloc[i] > op.iloc[i]:
            mean_price.iloc[i] = bar_up.iloc[i]
        elif cl.iloc[i] < op.iloc[i]:
            mean_price.iloc[i] = bar_dn.iloc[i]
        else:
            if hc.iloc[i] < lc.iloc[i]:
                mean_price.iloc[i] = bar_up.iloc[i]
            elif hc.iloc[i] > lc.iloc[i]:
                mean_price.iloc[i] = bar_dn.iloc[i]
            else:
                mean_price.iloc[i] = bar_nt.iloc[i]

    # Step 2: Calculate returns
    returns = mean_price.pct_change()

    # Step 3: Standardize with z-scores
    lookback = 30
    rolling_mean = returns.rolling(window=lookback, min_periods=lookback).mean()
    rolling_std = returns.rolling(window=lookback, min_periods=lookback).std()
    z_scores = (returns - rolling_mean) / rolling_std
    z_scores = z_scores.fillna(0)

    # Step 4: Apply RSI
    rsi_length = 14
    z_gains = z_scores.where(z_scores > 0, 0)
    z_losses = -z_scores.where(z_scores < 0, 0)

    avg_gains = z_gains.ewm(alpha=1/rsi_length, adjust=False).mean()
    avg_losses = z_losses.ewm(alpha=1/rsi_length, adjust=False).mean()

    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.replace([np.inf, -np.inf], np.nan)
    rsi.loc[avg_losses == 0] = 100
    rsi.loc[avg_gains == 0] = 0
    rsi = rsi.fillna(50)

    # Step 5: Apply EMA to RSI
    rsi_ma = rsi.ewm(span=ma_length, adjust=False).mean()

    last_date = data.index[-1]
    last_close = data['Close'].iloc[-1]
    last_rsi_ma = rsi_ma.iloc[-1]

    return last_date, last_close, last_rsi_ma

# Test with AAPL and MSFT
print("="*80)
print("CORRECTED RSI-MA CALCULATION TEST (MA Length = 18)")
print("="*80)
print(f"Current time: {datetime.now()}\n")

tickers = ["AAPL", "MSFT"]
expected_values = {
    "AAPL": (47.82, 49.37),  # Expected range
    "MSFT": (49.54, 49.54)   # Expected value
}

for ticker in tickers:
    print(f"\n{ticker}:")
    print("-" * 60)

    try:
        last_date, last_close, rsi_ma = calculate_rsi_ma(ticker, ma_length=18)

        if rsi_ma is not None:
            print(f"  Last update: {last_date.strftime('%Y-%m-%d')}")
            print(f"  Last close:  ${last_close:.2f}")
            print(f"  RSI-MA:      {rsi_ma:.2f}")

            if ticker in expected_values:
                exp_min, exp_max = expected_values[ticker]
                diff_min = abs(rsi_ma - exp_min)
                diff_max = abs(rsi_ma - exp_max)

                print(f"\n  Expected range: {exp_min:.2f} - {exp_max:.2f}")
                print(f"  Difference from {exp_min:.2f}: {diff_min:.2f}")
                print(f"  Difference from {exp_max:.2f}: {diff_max:.2f}")

                # Check if within acceptable range (47.50-52.00)
                if 47.50 <= rsi_ma <= 52.00:
                    print(f"  ✓ WITHIN EXPECTED RANGE (47.50-52.00)")
                else:
                    print(f"  ✗ OUTSIDE EXPECTED RANGE (47.50-52.00)")
        else:
            print(f"  ERROR: Could not calculate RSI-MA")

    except Exception as e:
        print(f"  ERROR: {e}")

print("\n" + "="*80)
print("SUMMARY:")
print("="*80)
print("The RSI-MA values should be roughly between 47.50 and 52.00")
print("If values are outside this range, further calibration may be needed.")
print("="*80)
