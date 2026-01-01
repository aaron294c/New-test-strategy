#!/usr/bin/env python3
"""Verify that relaxed filters work for both deep ITM and ATM."""
import sys
sys.path.insert(0, '.')

from leaps_analyzer import fetch_spx_options

print("Fetching LEAPS options...")
opts = fetch_spx_options(180, 365, False)

print(f"\nTotal LEAPS options: {len(opts)}")

# Check Deep ITM (delta 0.85-0.98)
deep_itm = [o for o in opts if 0.85 <= o.get('delta', 0) <= 0.98]
print(f"\n=== DEEP ITM (delta 0.85-0.98): {len(deep_itm)} options ===")

if deep_itm:
    # New relaxed filters: volume >= 1 only (no OI requirement)
    passing_deep = [o for o in deep_itm
                    if o.get('volume', 0) >= 1
                    and o.get('bid_ask_spread_pct', 100) <= 10]

    print(f"Passing NEW relaxed filters (vol>=1, spread<=10%): {len(passing_deep)}")

    if passing_deep:
        print(f"\nSample deep ITM options:")
        for i, o in enumerate(passing_deep[:3], 1):
            print(f"\n{i}. Strike ${o['strike']:.0f}")
            print(f"   Delta: {o['delta']:.3f}")
            print(f"   Volume: {o['volume']}")
            print(f"   OI: {o['open_interest']}")
            print(f"   Spread: {o['bid_ask_spread_pct']:.2f}%")

# Check ATM (delta 0.45-0.60)
atm = [o for o in opts if 0.45 <= o.get('delta', 0) <= 0.60]
print(f"\n=== ATM (delta 0.45-0.60): {len(atm)} options ===")

if atm:
    # New relaxed filters: volume >= 5 only (no OI requirement)
    passing_atm = [o for o in atm
                   if o.get('volume', 0) >= 5
                   and o.get('bid_ask_spread_pct', 100) <= 10]

    print(f"Passing NEW relaxed filters (vol>=5, spread<=10%): {len(passing_atm)}")

    if passing_atm:
        print(f"\nSample ATM options:")
        for i, o in enumerate(passing_atm[:3], 1):
            print(f"\n{i}. Strike ${o['strike']:.0f}")
            print(f"   Delta: {o['delta']:.3f}")
            print(f"   Volume: {o['volume']}")
            print(f"   OI: {o['open_interest']}")
            print(f"   Spread: {o['bid_ask_spread_pct']:.2f}%")

# Check Moderate ITM (delta 0.75-0.85)
moderate = [o for o in opts if 0.75 <= o.get('delta', 0) <= 0.85]
print(f"\n=== MODERATE ITM (delta 0.75-0.85): {len(moderate)} options ===")

if moderate:
    # Same as ATM: volume >= 5 only (no OI requirement)
    passing_mod = [o for o in moderate
                   if o.get('volume', 0) >= 5
                   and o.get('bid_ask_spread_pct', 100) <= 10]

    print(f"Passing NEW relaxed filters (vol>=5, spread<=10%): {len(passing_mod)}")

print("\n" + "="*60)
print("SUMMARY:")
print("="*60)
print(f"Deep ITM: {len(passing_deep) if deep_itm else 0} options pass new filters")
print(f"ATM: {len(passing_atm) if atm else 0} options pass new filters")
print(f"Moderate ITM: {len(passing_mod) if moderate else 0} options pass new filters")
print("="*60)
