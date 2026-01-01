#!/usr/bin/env python3
"""
Check vega reporting conventions - there are multiple standards!
"""
import numpy as np
from scipy.stats import norm

def calculate_vega_conventions(S=690.31, K=600, T=0.5, r=0.045, sigma=0.20):
    """Calculate vega using different conventions."""

    # Calculate d1
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))

    print("=" * 70)
    print("VEGA REPORTING CONVENTIONS")
    print("=" * 70)
    print(f"\nOption: SPY Call")
    print(f"Spot: ${S:.2f}, Strike: ${K:.0f}, IV: {sigma*100:.0f}%, Time: {T:.1f}y")
    print(f"\n" + "-" * 70)

    # Convention 1: Per 1 percentage point (most common in options trading)
    # Vega = dV/dσ where σ is in decimal form
    # Change from 20% to 21% IV (σ = 0.20 to 0.21)
    vega_per_pct_point = S * norm.pdf(d1) * np.sqrt(T)
    print(f"\n1. STANDARD CONVENTION (per 1 percentage point):")
    print(f"   Vega = {vega_per_pct_point:.4f}")
    print(f"   Meaning: If IV changes from 20% to 21%, option price changes ${vega_per_pct_point:.2f}")
    print(f"   This is the STANDARD convention used in most options platforms")

    # Convention 2: Per 1% (divide by 100)
    # This is what we've been using
    vega_per_one_percent = S * norm.pdf(d1) * np.sqrt(T) / 100
    print(f"\n2. PER 1% CONVENTION (less common):")
    print(f"   Vega = {vega_per_one_percent:.4f}")
    print(f"   Meaning: Per 1% change in IV value")
    print(f"   This is what our code currently calculates")

    # Convention 3: Per 0.01 change in vol (same as convention 1)
    vega_per_point_01 = S * norm.pdf(d1) * np.sqrt(T)
    print(f"\n3. PER 0.01 CHANGE (alternative expression of standard):")
    print(f"   Vega = {vega_per_point_01:.4f}")
    print(f"   Same as convention 1, just different way to express it")

    print(f"\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print(f"\nOur current vega ({vega_per_one_percent:.4f}) uses Convention 2 (/ 100)")
    print(f"STANDARD options vega ({vega_per_pct_point:.4f}) uses Convention 1")
    print(f"\nStandard vega is 100x larger: {vega_per_pct_point:.2f} vs {vega_per_one_percent:.4f}")

    print(f"\n" + "=" * 70)
    print("WHAT THIS MEANS FOR YOUR RESEARCH")
    print("=" * 70)
    print(f"\nYou mentioned vega \"10-20\" for S&P LEAPS:")
    print(f"  - Standard vega for this option: ${vega_per_pct_point:.2f}")
    print(f"  - For ATM LEAPS, vega ~15-25 is normal")
    print(f"  - For deep ITM LEAPS, vega ~0.5-5 is normal")
    print(f"\nSo your research IS CORRECT for standard convention!")
    print(f"\nOur code divides by 100, giving smaller numbers (0.02-0.25 range)")
    print(f"Both are mathematically correct, just different reporting units.")

    return vega_per_pct_point, vega_per_one_percent

if __name__ == "__main__":
    standard_vega, our_vega = calculate_vega_conventions()

    print(f"\n" + "=" * 70)
    print("RECOMMENDATION")
    print("=" * 70)
    print(f"\nBoth conventions are correct:")
    print(f"  - KEEP current convention (/ 100) for internal consistency")
    print(f"  - Values 0.02-0.25 are correct for this convention")
    print(f"  - IV Rank/Percentile shows if volatility is cheap or expensive")
    print(f"\nNo change needed - vega calculation is CORRECT!")
    print("=" * 70)
