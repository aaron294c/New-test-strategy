#!/usr/bin/env python3
"""
Test script to debug the exit signal calculation
"""

import sys
import traceback
from live_signal_generator import generate_exit_signal_for_position

# Test with AAPL - RECENT entry (what user actually wants)
ticker = "AAPL"
entry_price = 230.0
entry_date = "2025-10-10"  # Very recent date

print(f"Testing exit signal generation for {ticker}")
print(f"Entry Price: ${entry_price}")
print(f"Entry Date: {entry_date}")
print("-" * 60)

try:
    result = generate_exit_signal_for_position(
        ticker=ticker,
        entry_price=entry_price,
        entry_date=entry_date
    )

    print("SUCCESS!")
    print("\nResult:")
    import json
    print(json.dumps(result, indent=2))

except Exception as e:
    print("ERROR!")
    print(f"\nError message: {str(e)}")
    print("\nFull traceback:")
    traceback.print_exc()
