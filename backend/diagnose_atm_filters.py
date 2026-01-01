#!/usr/bin/env python3
"""Diagnose ATM liquidity filters."""
import sys
sys.path.insert(0, '.')

from leaps_analyzer import fetch_spx_options

print("Fetching LEAPS options...")
opts = fetch_spx_options(180, 365, False)

print(f"\nTotal LEAPS options: {len(opts)}")

# Check ATM range (delta 0.45-0.60)
atm = [o for o in opts if 0.45 <= o.get('delta', 0) <= 0.60]
print(f"\nATM (delta 0.45-0.60): {len(atm)} options")

if atm:
    print("\nLiquidity check for ATM:")
    low_volume = [o for o in atm if o.get('volume', 0) < 10]
    low_oi = [o for o in atm if o.get('open_interest', 0) < 100]
    wide_spread = [o for o in atm if o.get('bid_ask_spread_pct', 0) > 10]

    print(f"  Volume < 10: {len(low_volume)} options ({len(low_volume)/len(atm)*100:.1f}%)")
    print(f"  OI < 100: {len(low_oi)} options ({len(low_oi)/len(atm)*100:.1f}%)")
    print(f"  Bid-ask spread > 10%: {len(wide_spread)} options ({len(wide_spread)/len(atm)*100:.1f}%)")

    # Check how many pass ALL filters
    passing = [o for o in atm
               if o.get('volume', 0) >= 10
               and o.get('open_interest', 0) >= 100
               and o.get('bid_ask_spread_pct', 100) <= 10]

    print(f"\n  ATM options passing ALL liquidity filters: {len(passing)} ({len(passing)/len(atm)*100:.1f}%)")

    if passing:
        print(f"\nSample ATM options that pass filters:")
        for i, o in enumerate(passing[:5], 1):
            print(f"\n{i}. Strike ${o['strike']:.0f}")
            print(f"   Delta: {o['delta']:.3f}")
            print(f"   Volume: {o['volume']}")
            print(f"   OI: {o['open_interest']}")
            print(f"   Spread: {o['bid_ask_spread_pct']:.2f}%")
            print(f"   Vega: {o.get('vega', 0):.4f}")
    else:
        print("\n[WARNING] NO ATM options pass the liquidity filters!")

print("\n" + "="*60)
if atm and len([o for o in atm if o.get('volume', 0) >= 10 and o.get('open_interest', 0) >= 100]) > 0:
    print("ATM options do NOT have the same problem as deep ITM.")
    print("They have sufficient volume and OI to pass filters.")
else:
    print("ATM options ALSO have liquidity issues!")
print("="*60)
