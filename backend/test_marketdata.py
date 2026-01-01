#!/usr/bin/env python3
"""
Test MarketData.app API integration with provided token.
"""
import os
import sys
import logging

# Set the API key directly for this test
os.environ['MARKETDATA_API_KEY'] = 'Xp6qdnbAOcXkoGxq7njOz3aT4xsILsqC'

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

print("=" * 60)
print("Testing MarketData.app API Integration")
print("=" * 60)

try:
    from marketdata_options import fetch_leaps_with_greeks_marketdata, get_marketdata_api_key

    # Verify API key
    api_key = get_marketdata_api_key()
    if api_key:
        print(f"[OK] API Key configured (length: {len(api_key)})")
    else:
        print("[ERROR] API Key not found")
        sys.exit(1)

    print("\nFetching LEAPS options from MarketData.app...")
    print("(This may take 1-2 minutes due to rate limits)\n")

    # Fetch options
    options = fetch_leaps_with_greeks_marketdata("SPY", min_days=180, max_days=365)

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    if options:
        print(f"\n[SUCCESS] Fetched {len(options)} LEAPS options with REAL Greeks!\n")

        # Show first few options with vega values
        print("Sample Options (showing vega values):\n")
        for i, opt in enumerate(options[:5]):
            print(f"{i+1}. Strike: ${opt['strike']:.2f}")
            print(f"   Delta: {opt['delta']:.4f}")
            print(f"   Vega: {opt['vega']:.4f} (expected 0.02-0.15 for deep ITM)")
            print(f"   Theta: {opt['theta']:.4f}")
            print(f"   IV: {opt['implied_volatility']:.4f}")
            print(f"   Expiration: {opt['expiration']}")
            print()

        # Check if vega is in expected range
        deep_itm_options = [opt for opt in options if opt['delta'] > 0.85]
        if deep_itm_options:
            avg_vega = sum(opt['vega'] for opt in deep_itm_options) / len(deep_itm_options)
            print(f"Deep ITM Options (delta > 0.85): {len(deep_itm_options)}")
            print(f"Average Vega: {avg_vega:.4f}")

            if 0.02 <= avg_vega <= 0.15:
                print("[OK] Vega values are CORRECT for deep ITM options!")
            else:
                print("[WARNING] Vega values may be outside expected range (0.02-0.15)")

    else:
        print("\n[ERROR] No options returned from MarketData.app")
        print("This could mean:")
        print("  - Invalid API key")
        print("  - Rate limit exceeded")
        print("  - No data available for SPY LEAPS")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
