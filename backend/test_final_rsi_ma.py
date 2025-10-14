#!/usr/bin/env python3
"""Test the final RSI-MA implementation with complete LzR pipeline."""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

def calculate_rsi_ma_with_lzr(ticker):
    """
    Calculate RSI-MA using the complete LzR pipeline:
    1. Log returns from Close price
    2. Z-score standardization (30-day lookback)
    3. EMA(7) smoothing of z-scores (produces LzR)
    4. RSI(14) on LzR
    5. EMA(14) on RSI → RSI-MA
    """
    stock = yf.Ticker(ticker)
    data = stock.history(period="1y", interval="1d")

    if data.empty:
        return None

    close_price = data['Close']

    # Step 1: Calculate log returns
    log_returns = np.log(close_price / close_price.shift(1))

    # Step 2: Standardize with z-scores (30-day lookback)
    lookback = 30
    rolling_mean = log_returns.rolling(window=lookback, min_periods=lookback).mean()
    rolling_std = log_returns.rolling(window=lookback, min_periods=lookback).std()
    z_scores = (log_returns - rolling_mean) / rolling_std
    z_scores = z_scores.fillna(0)

    # Step 3: Apply EMA(7) smoothing to z-scores (produces LzR)
    lzr = z_scores.ewm(span=7, adjust=False).mean()

    # Step 4: Apply RSI to LzR (Wilder's method)
    rsi_length = 14
    gains = lzr.where(lzr > 0, 0)
    losses = -lzr.where(lzr < 0, 0)

    # Wilder's smoothing (RMA)
    avg_gains = gains.ewm(alpha=1/rsi_length, adjust=False).mean()
    avg_losses = losses.ewm(alpha=1/rsi_length, adjust=False).mean()

    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.replace([np.inf, -np.inf], np.nan)
    rsi.loc[avg_losses == 0] = 100
    rsi.loc[avg_gains == 0] = 0
    rsi = rsi.fillna(50)

    # Step 5: Apply EMA(14) to RSI
    ma_length = 14
    rsi_ma = rsi.ewm(span=ma_length, adjust=False).mean()

    # Return data including the LzR values
    return {
        'date': data.index[-1],
        'close': close_price.iloc[-1],
        'lzr': lzr.iloc[-1],
        'rsi': rsi.iloc[-1],
        'rsi_ma': rsi_ma.iloc[-1]
    }

# Test with AAPL and MSFT
print("="*80)
print("TESTING FINAL RSI-MA IMPLEMENTATION WITH COMPLETE LzR PIPELINE")
print("="*80)
print("Pipeline:")
print("  1. Log returns from Close price")
print("  2. Z-score standardization (30-day lookback)")
print("  3. EMA(7) smoothing of z-scores → LzR values")
print("  4. RSI(14) on LzR using Wilder's RMA")
print("  5. EMA(14) on RSI → Final RSI-MA")
print(f"\nCurrent time: {datetime.now()}")
print("="*80)

tickers = ["AAPL", "MSFT"]
expected_rsi_ma = {
    "AAPL": (47.82, 49.37),
    "MSFT": (49.54, 49.54)
}

expected_lzr = {
    "AAPL": -0.634,
    "MSFT": -0.234
}

results = {}

for ticker in tickers:
    print(f"\n{ticker}:")
    print("-" * 70)

    try:
        result = calculate_rsi_ma_with_lzr(ticker)

        if result is not None:
            results[ticker] = result

            print(f"  Last update: {result['date'].strftime('%Y-%m-%d')}")
            print(f"  Last close:  ${result['close']:.2f}")
            print(f"\n  LzR (EMA7-smoothed z-score): {result['lzr']:+.4f}")

            if ticker in expected_lzr:
                exp_lzr = expected_lzr[ticker]
                lzr_diff = abs(result['lzr'] - exp_lzr)
                print(f"  Expected LzR: {exp_lzr:+.4f}")
                print(f"  Difference: {lzr_diff:.4f}")

                if lzr_diff < 0.15:
                    print(f"  ✓✓ CLOSE MATCH on LzR")
                elif lzr_diff < 0.3:
                    print(f"  ✓ REASONABLE MATCH on LzR")
                else:
                    print(f"  ⚠ Larger difference on LzR")

            print(f"\n  RSI: {result['rsi']:.2f}")
            print(f"  RSI-MA: {result['rsi_ma']:.2f}")

            if ticker in expected_rsi_ma:
                exp_min, exp_max = expected_rsi_ma[ticker]
                diff_min = abs(result['rsi_ma'] - exp_min)
                diff_max = abs(result['rsi_ma'] - exp_max)

                print(f"\n  Expected RSI-MA range: {exp_min:.2f} - {exp_max:.2f}")
                print(f"  Difference from {exp_min:.2f}: {diff_min:.2f}")
                print(f"  Difference from {exp_max:.2f}: {diff_max:.2f}")

                # Check if within expected range (47.50-52.00)
                if 47.50 <= result['rsi_ma'] <= 52.00:
                    print(f"  ✓ WITHIN TARGET RANGE (47.50-52.00)")
                else:
                    print(f"  ✗ OUTSIDE TARGET RANGE (47.50-52.00)")
                    gap = min(abs(result['rsi_ma'] - 47.50), abs(result['rsi_ma'] - 52.00))
                    print(f"    Gap: {gap:.2f} points")
        else:
            print(f"  ERROR: Could not calculate RSI-MA")

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*80)
print("SUMMARY:")
print("="*80)

if results:
    print("\nLzR values (EMA7-smoothed z-scores):")
    for ticker, result in results.items():
        lzr = result['lzr']
        exp = expected_lzr.get(ticker, 0)
        diff = abs(lzr - exp)
        match_str = "✓✓" if diff < 0.15 else ("✓" if diff < 0.3 else "⚠")
        print(f"  {ticker}: {lzr:+.4f} (expected: {exp:+.4f}, diff: {diff:.4f}) {match_str}")

    print("\nRSI-MA values:")
    all_in_range = all(47.50 <= r['rsi_ma'] <= 52.00 for r in results.values())

    if all_in_range:
        print("✓ ALL VALUES ARE WITHIN TARGET RANGE (47.50-52.00)")
    else:
        print("⚠ SOME VALUES ARE OUTSIDE TARGET RANGE")
        for ticker, result in results.items():
            rsi_ma = result['rsi_ma']
            if not (47.50 <= rsi_ma <= 52.00):
                print(f"  - {ticker}: {rsi_ma:.2f}")

    print("\nCalculated RSI-MA values:")
    for ticker, result in results.items():
        rsi_ma = result['rsi_ma']
        exp_min, exp_max = expected_rsi_ma.get(ticker, (0, 0))
        print(f"  {ticker}: {rsi_ma:.2f} (expected: {exp_min:.2f}-{exp_max:.2f})")
else:
    print("ERROR: No results calculated")

print("="*80)
