#!/usr/bin/env python3
"""
Quick test to verify SPY and QQQ appear in current-state endpoint
"""
import asyncio
import sys

async def test_spy_qqq():
    print("Testing SPY and QQQ integration...\n")

    # Import after path is set
    from swing_framework_api import get_current_market_state

    try:
        result = await get_current_market_state()

        market_state = result.get('market_state', [])
        tickers_found = [s['ticker'] for s in market_state]

        print(f"✅ Endpoint returned {len(market_state)} tickers")
        print(f"   Tickers: {', '.join(tickers_found)}\n")

        # Check for SPY
        spy = next((s for s in market_state if s['ticker'] == 'SPY'), None)
        if spy:
            print(f"✅ SPY FOUND:")
            print(f"   Current Percentile: {spy['current_percentile']:.1f}%")
            print(f"   Price: ${spy['current_price']:.2f}")
            print(f"   In Entry Zone: {spy['in_entry_zone']}")
        else:
            print(f"❌ SPY NOT FOUND")
            return False

        # Check for QQQ
        qqq = next((s for s in market_state if s['ticker'] == 'QQQ'), None)
        if qqq:
            print(f"\n✅ QQQ FOUND:")
            print(f"   Current Percentile: {qqq['current_percentile']:.1f}%")
            print(f"   Price: ${qqq['current_price']:.2f}")
            print(f"   In Entry Zone: {qqq['in_entry_zone']}")
        else:
            print(f"❌ QQQ NOT FOUND")
            return False

        print(f"\n✅ SUCCESS: Both SPY and QQQ integrated successfully")
        print(f"   Total entries in table: {len(market_state)}")
        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_spy_qqq())
    sys.exit(0 if success else 1)
