#!/usr/bin/env python3
"""Direct test of SPX put wall calculation."""

import sys
sys.path.insert(0, '/workspaces/New-test-strategy/backend/Restoring')

from enhanced_gamma_scanner_weekly import (
    GammaWallCalculator, 
    process_symbol,
    MAX_DISTANCE_BY_CATEGORY,
    PUT_WALL_WEIGHTS,
    get_symbol_category
)

def test_spx():
    print("="*70)
    print("SPX PUT WALL CALCULATION TEST")
    print("="*70)
    
    # Check configuration
    print("\nCONFIGURATION:")
    print(f"  MAX_DISTANCE_BY_CATEGORY = {MAX_DISTANCE_BY_CATEGORY}")
    print(f"  PUT_WALL_WEIGHTS = {PUT_WALL_WEIGHTS}")
    print(f"  get_symbol_category('^SPX') = {get_symbol_category('^SPX')}")
    
    # Process SPX
    calculator = GammaWallCalculator()
    print("\nProcessing ^SPX...")
    
    result = process_symbol('^SPX', calculator)
    
    if not result:
        print("ERROR: Failed to process SPX!")
        return
    
    current_price = result['current_price']
    print(f"\nRESULTS:")
    print(f"  Current Price: ${current_price:.2f}")
    
    # Check put wall methods for swing timeframe
    put_methods = result.get('put_wall_methods', {}).get('swing', {})
    
    if put_methods:
        print(f"\n  SWING (14-day) PUT WALL METHODS:")
        for key, value in put_methods.items():
            if isinstance(value, (int, float)):
                dist = ((current_price - value) / current_price) * 100
                print(f"    {key}: ${value:.0f} ({dist:+.2f}%)")
            else:
                print(f"    {key}: {value}")
    else:
        print("\n  WARNING: No put wall methods found!")
    
    # Final values
    st_put = result.get('st_put_wall', 0)
    st_put_dist = ((current_price - st_put) / current_price) * 100
    
    print(f"\n  FINAL ST PUT WALL: ${st_put:.0f} ({st_put_dist:+.2f}%)")
    
    # Validate
    expected_max = MAX_DISTANCE_BY_CATEGORY.get('INDEX', 0.08) * 100
    
    print(f"\n  VALIDATION:")
    print(f"    Expected max distance: {expected_max:.1f}%")
    print(f"    Actual distance: {abs(st_put_dist):.1f}%")
    
    if abs(st_put_dist) > expected_max * 1.5:
        print(f"\n  ⚠️  FAIL: ST Put Wall is {abs(st_put_dist):.1f}% from price!")
        print(f"      Expected: within {expected_max * 1.5:.1f}%")
        print(f"      This suggests the proximity filter is NOT being applied!")
    else:
        print(f"\n  ✅ PASS: ST Put Wall is within expected range")

if __name__ == "__main__":
    test_spx()
