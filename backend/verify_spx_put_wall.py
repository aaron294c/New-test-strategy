#!/usr/bin/env python3
"""Quick verification of SPX put wall calculation."""

import sys
sys.path.insert(0, 'Restoring')

from enhanced_gamma_scanner_weekly import (
    GammaWallCalculator, 
    process_symbol,
    MAX_DISTANCE_BY_CATEGORY,
    PUT_WALL_WEIGHTS
)

def verify_spx():
    print("="*60)
    print("SPX PUT WALL VERIFICATION")
    print("="*60)
    
    print(f"\nConfiguration:")
    print(f"  MAX_DISTANCE_BY_CATEGORY['INDEX'] = {MAX_DISTANCE_BY_CATEGORY.get('INDEX', 'NOT SET')}")
    print(f"  PUT_WALL_WEIGHTS = {PUT_WALL_WEIGHTS}")
    
    calculator = GammaWallCalculator()
    
    print(f"\nProcessing SPX...")
    result = process_symbol('^SPX', calculator)
    
    if not result:
        print("ERROR: Failed to process SPX")
        return
    
    current_price = result['current_price']
    print(f"\nResults:")
    print(f"  Current Price: ${current_price:.2f}")
    
    # Check all put wall methods
    put_methods = result.get('put_wall_methods', {}).get('swing', {})
    if put_methods:
        print(f"\n  SWING (14-day) PUT WALL METHODS:")
        for method, value in put_methods.items():
            if isinstance(value, (int, float)):
                distance = ((current_price - value) / current_price) * 100
                print(f"    {method}: ${value:.0f} ({distance:+.2f}%)")
    
    # Final values
    st_put = result.get('st_put_wall', 0)
    st_put_dist = ((current_price - st_put) / current_price) * 100
    
    print(f"\n  FINAL ST PUT WALL: ${st_put:.0f} ({st_put_dist:+.2f}%)")
    
    # Validation
    expected_max_distance = MAX_DISTANCE_BY_CATEGORY.get('INDEX', 0.08) * 100
    
    if abs(st_put_dist) > expected_max_distance * 1.5:
        print(f"\n  ⚠️ WARNING: ST Put Wall is {abs(st_put_dist):.1f}% from price!")
        print(f"     Expected: within {expected_max_distance:.1f}% (INDEX category)")
        print(f"     This suggests the proximity filter is NOT being applied!")
    else:
        print(f"\n  ✅ ST Put Wall is within expected range ({expected_max_distance:.1f}%)")

if __name__ == "__main__":
    verify_spx()
