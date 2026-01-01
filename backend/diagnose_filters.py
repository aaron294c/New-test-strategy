#!/usr/bin/env python3
"""Diagnose why filters are too restrictive."""
import sys
sys.path.insert(0, '.')

from leaps_analyzer import fetch_spx_options

print("Fetching LEAPS options...")
opts = fetch_spx_options(180, 365, False)

print(f"\nTotal LEAPS options: {len(opts)}")

# Check Deep ITM
deep_itm = [o for o in opts if 0.85 <= o.get('delta', 0) <= 0.98]
print(f"Deep ITM (delta 0.85-0.98): {len(deep_itm)}")

# Check extrinsic filter
if deep_itm:
    print("\nExtrinsic % distribution for Deep ITM:")
    extr_values = [o.get('extrinsic_pct', 0) for o in deep_itm]
    extr_values.sort()
    print(f"  Min: {min(extr_values):.1f}%")
    print(f"  25th percentile: {extr_values[len(extr_values)//4]:.1f}%")
    print(f"  Median: {extr_values[len(extr_values)//2]:.1f}%")
    print(f"  75th percentile: {extr_values[3*len(extr_values)//4]:.1f}%")
    print(f"  Max: {max(extr_values):.1f}%")

    extr_10 = [o for o in deep_itm if o.get('extrinsic_pct', 100) <= 10]
    extr_15 = [o for o in deep_itm if o.get('extrinsic_pct', 100) <= 15]
    extr_20 = [o for o in deep_itm if o.get('extrinsic_pct', 100) <= 20]
    extr_35 = [o for o in deep_itm if o.get('extrinsic_pct', 100) <= 35]

    print(f"\nWith max extrinsic filters:")
    print(f"  <=10%: {len(extr_10)} options")
    print(f"  <=15%: {len(extr_15)} options")
    print(f"  <=20%: {len(extr_20)} options")
    print(f"  <=35%: {len(extr_35)} options")

# Check liquidity filters
if deep_itm:
    print(f"\nLiquidity check (before liquidity filters):")
    low_volume = [o for o in deep_itm if o.get('volume', 0) < 10]
    low_oi = [o for o in deep_itm if o.get('open_interest', 0) < 100]
    wide_spread = [o for o in deep_itm if o.get('bid_ask_spread_pct', 0) > 5]

    print(f"  Volume < 10: {len(low_volume)} options would be filtered out")
    print(f"  OI < 100: {len(low_oi)} options would be filtered out")
    print(f"  Bid-ask spread > 5%: {len(wide_spread)} options would be filtered out")

    # Check how many pass ALL filters
    passing = [o for o in deep_itm
               if o.get('volume', 0) >= 10
               and o.get('open_interest', 0) >= 100
               and o.get('bid_ask_spread_pct', 100) <= 5]

    print(f"\n  Options passing ALL liquidity filters: {len(passing)}")

    # Now add extrinsic
    if passing:
        passing_10 = [o for o in passing if o.get('extrinsic_pct', 100) <= 10]
        passing_20 = [o for o in passing if o.get('extrinsic_pct', 100) <= 20]
        passing_35 = [o for o in passing if o.get('extrinsic_pct', 100) <= 35]

        print(f"\n  With liquidity + max extrinsic 10%: {len(passing_10)} options")
        print(f"  With liquidity + max extrinsic 20%: {len(passing_20)} options")
        print(f"  With liquidity + max extrinsic 35%: {len(passing_35)} options")

        if passing_35:
            print(f"\nSample options that pass filters (extrinsic <=35%):")
            for i, o in enumerate(passing_35[:5], 1):
                print(f"\n{i}. Strike ${o['strike']:.0f}")
                print(f"   Delta: {o['delta']:.3f}")
                print(f"   Extrinsic: {o['extrinsic_pct']:.1f}%")
                print(f"   Volume: {o['volume']}")
                print(f"   OI: {o['open_interest']}")
                print(f"   Spread: {o['bid_ask_spread_pct']:.2f}%")
                print(f"   Vega: {o.get('vega', 0):.4f}")
                print(f"   IV Rank: {o.get('iv_rank', 0):.2f}")
                print(f"   Opportunity Score: {o.get('opportunity_score', 0):.0f}")

print("\n" + "="*60)
print("RECOMMENDATION:")
print("="*60)
print("The DEEP_ITM default max extrinsic of 10% is TOO RESTRICTIVE.")
print("Consider changing it to 20-25% for deep ITM LEAPS.")
print("="*60)
