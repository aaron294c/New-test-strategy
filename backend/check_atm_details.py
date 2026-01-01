#!/usr/bin/env python3
"""Check exact values for ATM options."""
import sys
sys.path.insert(0, '.')

from leaps_analyzer import fetch_spx_options

print("Fetching LEAPS options...")
opts = fetch_spx_options(180, 365, False)

# Check ATM (delta 0.45-0.60)
atm = [o for o in opts if 0.45 <= o.get('delta', 0) <= 0.60]
print(f"\nFound {len(atm)} ATM options (delta 0.45-0.60):\n")

for i, o in enumerate(atm, 1):
    print(f"{i}. Strike ${o['strike']:.0f}")
    print(f"   Delta: {o['delta']:.3f}")
    print(f"   Volume: {o['volume']}")
    print(f"   OI: {o['open_interest']}")
    print(f"   Spread: {o['bid_ask_spread_pct']:.2f}%")
    print()
