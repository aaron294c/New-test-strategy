#!/usr/bin/env python3
"""Test the working method from user's script."""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

def calculate_rsi_ma_working_method(ticker):
    """
    Calculate RSI-MA using the WORKING method from user's script:
    RSI on change of percentage returns (second derivative of price)
    """
    stock = yf.Ticker(ticker)
    data = stock.history(period="1y", interval="1d")

    if data.empty:
        return None

    prices = data['Close']

    # Working method from user's script
    daily_returns = prices.pct_change().fillna(0)

    delta = daily_returns.diff()
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)

    rsi_length = 14
    avg_gains = gains.ewm(alpha=1/rsi_length, adjust=False).mean()
    avg_losses = losses.ewm(alpha=1/rsi_length, adjust=False).mean()

    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(50)

    ma_length = 14
    rsi_ma = rsi.ewm(span=ma_length, adjust=False).mean()

    return {
        'date': data.index[-1],
        'close': prices.iloc[-1],
        'rsi': rsi.iloc[-1],
        'rsi_ma': rsi_ma.iloc[-1]
    }

# Test with AAPL and MSFT
print("="*80)
print("TESTING WORKING METHOD FROM USER'S SCRIPT")
print("="*80)
print("Method: pct_change() -> diff() -> RSI(14) -> EMA(14)")
print(f"Current time: {datetime.now()}")
print("="*80)

tickers = ["AAPL", "MSFT"]
expected_rsi_ma = {
    "AAPL": (47.82, 49.37),
    "MSFT": (49.54, 49.54)
}

results = {}

for ticker in tickers:
    print(f"\n{ticker}:")
    print("-" * 70)

    try:
        result = calculate_rsi_ma_working_method(ticker)

        if result is not None:
            results[ticker] = result

            print(f"  Last update: {result['date'].strftime('%Y-%m-%d')}")
            print(f"  Last close:  ${result['close']:.2f}")
            print(f"  RSI: {result['rsi']:.2f}")
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
    print("\nRSI-MA values using WORKING method:")
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
