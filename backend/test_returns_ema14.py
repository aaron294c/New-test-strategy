#!/usr/bin/env python3
"""Test RSI on percentage returns with EMA(14) - the NEW implementation."""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

def calculate_rsi_ma_returns_ema14(ticker):
    """Calculate RSI-MA: Returns -> RSI(14) -> EMA(14)."""
    stock = yf.Ticker(ticker)
    data = stock.history(period="1y", interval="1d")

    if data.empty:
        return None

    close_price = data['Close']

    # Step 1: Calculate percentage returns
    returns = close_price.pct_change() * 100

    # Step 2: Apply RSI to percentage returns
    rsi_length = 14
    gains = returns.where(returns > 0, 0)
    losses = -returns.where(returns < 0, 0)

    # Wilder's smoothing (RMA)
    avg_gains = gains.ewm(alpha=1/rsi_length, adjust=False).mean()
    avg_losses = losses.ewm(alpha=1/rsi_length, adjust=False).mean()

    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.replace([np.inf, -np.inf], np.nan)
    rsi.loc[avg_losses == 0] = 100
    rsi.loc[avg_gains == 0] = 0
    rsi = rsi.fillna(50)

    # Step 3: Apply EMA(14) to RSI
    ma_length = 14
    rsi_ma = rsi.ewm(span=ma_length, adjust=False).mean()

    return data.index[-1], data['Close'].iloc[-1], rsi_ma.iloc[-1]

# Test with AAPL and MSFT
print("="*80)
print("RSI ON PERCENTAGE RETURNS + EMA(14) TEST")
print("="*80)
print("Method: Close -> Returns (%) -> RSI (14) -> EMA (14)")
print(f"Current time: {datetime.now()}\n")

tickers = ["AAPL", "MSFT"]
expected_values = {
    "AAPL": (47.82, 49.37),
    "MSFT": (49.54, 49.54)
}

results = {}

for ticker in tickers:
    print(f"\n{ticker}:")
    print("-" * 70)

    try:
        last_date, last_close, rsi_ma = calculate_rsi_ma_returns_ema14(ticker)

        if rsi_ma is not None:
            results[ticker] = rsi_ma

            print(f"  Last update: {last_date.strftime('%Y-%m-%d')}")
            print(f"  Last close:  ${last_close:.2f}")
            print(f"  RSI-MA (Returns + EMA14): {rsi_ma:.2f}")

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
                    print(f"    Gap: {min(abs(rsi_ma - 47.50), abs(rsi_ma - 52.00)):.2f} points")
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
    all_in_range = all(47.50 <= v <= 52.00 for v in results.values())
    if all_in_range:
        print("✓ ALL VALUES ARE WITHIN EXPECTED RANGE (47.50-52.00)")
    else:
        print("✗ SOME VALUES ARE OUTSIDE EXPECTED RANGE")
        for ticker, value in results.items():
            if not (47.50 <= value <= 52.00):
                print(f"  - {ticker}: {value:.2f}")

    print("\nValues calculated:")
    for ticker, value in results.items():
        print(f"  {ticker}: {value:.2f}")
else:
    print("ERROR: No results calculated")
print("="*80)
