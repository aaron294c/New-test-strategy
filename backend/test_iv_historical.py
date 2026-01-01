#!/usr/bin/env python3
"""Test real IV rank/percentile calculation from VIX history."""
import sys
sys.path.insert(0, '.')

from leaps_analyzer import calculate_iv_rank_percentile

# Test with typical deep ITM LEAPS IV values
test_cases = [
    ("Low IV", 0.168),    # 16.8%
    ("Moderate IV", 0.225),  # 22.5%
    ("Elevated IV", 0.300),  # 30.0%
]

print("Testing IV Rank/Percentile with real VIX historical data...\n")

for name, iv in test_cases:
    rank, percentile = calculate_iv_rank_percentile("SPY", iv)
    print(f"{name} (IV={iv*100:.1f}%):")
    print(f"  IV Rank: {rank:.3f} ({rank*100:.1f}%)")
    print(f"  IV Percentile: {percentile:.1f}%")

    # They should be DIFFERENT now!
    if abs(rank * 100 - percentile) < 1:
        print(f"  ⚠️  WARNING: Rank and Percentile are too similar!")
    else:
        print(f"  ✓ Rank and Percentile differ (as expected)")
    print()

print("=" * 60)
print("If you see actual VIX ranges printed above, it's working!")
print("If you see fallback warnings, VIX data fetch failed.")
print("=" * 60)
