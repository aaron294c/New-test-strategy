#!/usr/bin/env python3
"""
Mean Price Calculator - matches TradingView indicator exactly.

This calculates a weighted mean price based on OHLC data:
- bar_nt: Neutral bar (equal weighting)
- bar_up: Upward bias (more weight on highs)
- bar_dn: Downward bias (more weight on lows)

Selection logic:
- If close > open: use bar_up
- If close < open: use bar_dn
- If close == open: compare high-close vs low-close distance
"""

import pandas as pd
import numpy as np
import yfinance as yf

def calculate_mean_price(data, robust=False):
    """
    Calculate mean price matching TradingView formula exactly.

    Parameters:
    - data: DataFrame with Open, High, Low, Close columns
    - robust: If True, always use bar_nt (neutral). Default False.

    Returns:
    - Series of mean prices
    """
    op = data['Open']
    hi = data['High']
    lo = data['Low']
    cl = data['Close']
    bt = (hi + lo) / 2  # hl2
    st = (hi + lo) / 2  # hl2

    # Calculate the three bar types
    bar_nt = (op * 1 + hi * 2 + lo * 2 + cl * 3 + bt * 2 + st * 2) / 12
    bar_up = (op * 1 + hi * 4 + lo * 2 + cl * 5 + bt * 3 + st * 3) / 18
    bar_dn = (op * 1 + hi * 2 + lo * 4 + cl * 5 + bt * 3 + st * 3) / 18

    if robust:
        return bar_nt

    # Calculate distances
    hc = np.abs(hi - cl)
    lc = np.abs(lo - cl)

    # Select appropriate mean price based on bar direction
    mean_price = pd.Series(index=data.index, dtype=float)

    for i in range(len(data)):
        if cl.iloc[i] > op.iloc[i]:
            # Bullish bar - use upward bias
            mean_price.iloc[i] = bar_up.iloc[i]
        elif cl.iloc[i] < op.iloc[i]:
            # Bearish bar - use downward bias
            mean_price.iloc[i] = bar_dn.iloc[i]
        else:  # cl == op (doji)
            if hc.iloc[i] < lc.iloc[i]:
                # Upper shadow shorter - use upward bias
                mean_price.iloc[i] = bar_up.iloc[i]
            elif hc.iloc[i] > lc.iloc[i]:
                # Lower shadow shorter - use downward bias
                mean_price.iloc[i] = bar_dn.iloc[i]
            else:  # hc == lc (perfect symmetry)
                # Neutral
                mean_price.iloc[i] = bar_nt.iloc[i]

    return mean_price

# Test with AAPL data
if __name__ == "__main__":
    ticker = "AAPL"
    stock = yf.Ticker(ticker)
    data = stock.history(period="1y", interval="1d")

    if data.empty:
        print("Failed to fetch data")
        exit(1)

    print("="*70)
    print("Mean Price Calculation (TradingView Formula)")
    print("="*70)

    # Calculate mean price
    mean_price = calculate_mean_price(data, robust=False)

    print(f"\nLast 10 days comparison:")
    print(f"{'Date':<12} {'Open':>8} {'High':>8} {'Low':>8} {'Close':>8} {'MeanPrice':>10} {'Type':>8}")
    print(f"{'-'*12} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*10} {'-'*8}")

    for i in range(-10, 0):
        date = data.index[i]
        op = data['Open'].iloc[i]
        hi = data['High'].iloc[i]
        lo = data['Low'].iloc[i]
        cl = data['Close'].iloc[i]
        mp = mean_price.iloc[i]

        # Determine bar type
        if cl > op:
            bar_type = "Bullish"
        elif cl < op:
            bar_type = "Bearish"
        else:
            bar_type = "Doji"

        print(f"{date.strftime('%Y-%m-%d'):<12} ${op:>7.2f} ${hi:>7.2f} ${lo:>7.2f} ${cl:>7.2f} ${mp:>9.2f} {bar_type:>8}")

    # Compare mean_price vs close
    print(f"\n{'='*70}")
    print("Mean Price vs Close Price")
    print(f"{'='*70}")

    last_close = data['Close'].iloc[-1]
    last_mean = mean_price.iloc[-1]
    diff = last_mean - last_close
    diff_pct = (diff / last_close) * 100

    print(f"Last Close Price:  ${last_close:.2f}")
    print(f"Last Mean Price:   ${last_mean:.2f}")
    print(f"Difference:        ${diff:+.2f} ({diff_pct:+.2f}%)")

    # Show statistics
    print(f"\n{'='*70}")
    print("Statistics")
    print(f"{'='*70}")

    differences = mean_price - data['Close']
    print(f"Mean difference:   ${differences.mean():.2f}")
    print(f"Std deviation:     ${differences.std():.2f}")
    print(f"Max difference:    ${differences.max():.2f}")
    print(f"Min difference:    ${differences.min():.2f}")
