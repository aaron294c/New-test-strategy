#!/usr/bin/env python3
"""Check current vega values from yfinance."""
import sys
sys.path.insert(0, '.')

from leaps_analyzer import fetch_spx_options
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

print("\n" + "=" * 60)
print("CURRENT YFINANCE LEAPS DATA")
print("=" * 60)

options = fetch_spx_options(180, 365, False)

if not options:
    print("\n[ERROR] No options returned")
    sys.exit(1)

print(f"\nTotal LEAPS fetched: {len(options)}")

# Analyze by delta ranges
deep_itm = [opt for opt in options if opt['delta'] > 0.85]
atm = [opt for opt in options if 0.45 <= opt['delta'] <= 0.55]
all_options = options

print(f"Deep ITM (delta > 0.85): {len(deep_itm)}")
print(f"ATM (delta 0.45-0.55): {len(atm)}")

# Show deep ITM vega values
if deep_itm:
    print("\n" + "-" * 60)
    print("DEEP ITM OPTIONS (delta > 0.85):")
    print("-" * 60)
    for i, opt in enumerate(deep_itm[:10]):
        print(f"{i+1}. Strike: ${opt['strike']:.0f}")
        print(f"   Delta: {opt['delta']:.4f}")
        print(f"   Vega: {opt['vega']:.4f}")
        print(f"   IV: {opt['implied_volatility']*100:.1f}%")
        print(f"   Expiration: {opt['expiration']}")
        print()

    avg_vega_deep = sum(opt['vega'] for opt in deep_itm) / len(deep_itm)
    print(f"Average Vega (Deep ITM): {avg_vega_deep:.4f}")

# Show ATM vega values
if atm:
    print("\n" + "-" * 60)
    print("ATM OPTIONS (delta 0.45-0.55):")
    print("-" * 60)
    for i, opt in enumerate(atm[:5]):
        print(f"{i+1}. Strike: ${opt['strike']:.0f}")
        print(f"   Delta: {opt['delta']:.4f}")
        print(f"   Vega: {opt['vega']:.4f}")
        print(f"   IV: {opt['implied_volatility']*100:.1f}%")
        print()

    avg_vega_atm = sum(opt['vega'] for opt in atm) / len(atm)
    print(f"Average Vega (ATM): {avg_vega_atm:.4f}")

print("\n" + "=" * 60)
print("VEGA INTERPRETATION:")
print("=" * 60)
print("Vega = Change in option price for 1% change in IV")
print("Deep ITM: Typically 0.02-0.15 (low vega)")
print("ATM: Typically 0.20-0.40 (high vega)")
print("\nNote: Some sources report vega in dollars per 1 percentage")
print("point IV change, which would be 100x these values.")
print("=" * 60)
