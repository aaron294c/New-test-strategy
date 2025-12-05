#!/usr/bin/env python3
"""Test all possible RSI-MA calculation methods to find the matching one."""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

def test_rsi_ma_methods(ticker):
    """Test different calculation methods."""
    stock = yf.Ticker(ticker)
    data = stock.history(period="1y", interval="1d")

    if data.empty:
        return None

    print(f"\n{'='*80}")
    print(f"{ticker} - Testing Different RSI-MA Calculation Methods")
    print(f"Last close: ${data['Close'].iloc[-1]:.2f} on {data.index[-1].strftime('%Y-%m-%d')}")
    print(f"{'='*80}\n")

    results = {}

    # Prepare different price sources
    close_price = data['Close']

    # Mean Price (OHLC-weighted)
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

    # HLC3 (typical price)
    hlc3_price = (hi + lo + cl) / 3

    # Test configurations
    configs = [
        ("Close + Simple Changes", close_price, "simple", False),
        ("Close + Z-Scores", close_price, "zscore", False),
        ("Close + Pct Returns", close_price, "pct", False),
        ("Mean Price + Simple Changes", mean_price, "simple", False),
        ("Mean Price + Z-Scores", mean_price, "zscore", False),
        ("Mean Price + Pct Returns", mean_price, "pct", False),
        ("HLC3 + Simple Changes", hlc3_price, "simple", False),
        ("HLC3 + Z-Scores", hlc3_price, "zscore", False),
        ("HLC3 + Pct Returns", hlc3_price, "pct", False),
    ]

    for name, price_source, transform_type, _ in configs:
        try:
            # Calculate source data
            if transform_type == "simple":
                source = price_source.diff()
            elif transform_type == "pct":
                source = price_source.pct_change()
            elif transform_type == "zscore":
                returns = price_source.pct_change()
                lookback = 30
                rolling_mean = returns.rolling(window=lookback, min_periods=lookback).mean()
                rolling_std = returns.rolling(window=lookback, min_periods=lookback).std()
                source = (returns - rolling_mean) / rolling_std
                source = source.fillna(0)

            # Calculate RSI
            rsi_length = 14
            gains = source.where(source > 0, 0)
            losses = -source.where(source < 0, 0)

            avg_gains = gains.ewm(alpha=1/rsi_length, adjust=False).mean()
            avg_losses = losses.ewm(alpha=1/rsi_length, adjust=False).mean()

            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))
            rsi = rsi.replace([np.inf, -np.inf], np.nan)
            rsi.loc[avg_losses == 0] = 100
            rsi.loc[avg_gains == 0] = 0
            rsi = rsi.fillna(50)

            # Apply EMA with MA Length 14
            ma_length = 14
            rsi_ma = rsi.ewm(span=ma_length, adjust=False).mean()

            results[name] = rsi_ma.iloc[-1]

        except Exception as e:
            results[name] = f"ERROR: {e}"

    # Print results
    print(f"{'Method':<40} | RSI-MA")
    print("-" * 60)
    for method, value in results.items():
        if isinstance(value, float):
            print(f"{method:<40} | {value:6.2f}")
        else:
            print(f"{method:<40} | {value}")

    return results

# Test AAPL and MSFT
print("\n" + "="*80)
print("COMPREHENSIVE RSI-MA METHOD TESTING")
print("="*80)
print(f"Current time: {datetime.now()}")

expected_values = {
    "AAPL": (47.82, 49.37),
    "MSFT": (49.54, 49.54)
}

for ticker in ["AAPL", "MSFT"]:
    results = test_rsi_ma_methods(ticker)

    if results and ticker in expected_values:
        exp_min, exp_max = expected_values[ticker]
        print(f"\n{'='*80}")
        print(f"{ticker} - Expected range: {exp_min:.2f} - {exp_max:.2f}")
        print(f"{'='*80}")
        print(f"{'Method':<40} | Diff from {exp_min:.2f} | Diff from {exp_max:.2f}")
        print("-" * 80)

        for method, value in results.items():
            if isinstance(value, float):
                diff_min = abs(value - exp_min)
                diff_max = abs(value - exp_max)
                marker = " *** CLOSE MATCH ***" if (diff_min < 2.0 or diff_max < 2.0) else ""
                print(f"{method:<40} | {diff_min:12.2f} | {diff_max:12.2f}{marker}")

print("\n" + "="*80)
