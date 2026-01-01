#!/usr/bin/env python3
"""Test MarketData.app API with simple request."""
import requests

token = 'Xp6qdnbAOcXkoGxq7njOz3aT4xsILsqC'

print("Testing MarketData.app API...")
print("=" * 60)

# Try with token in URL path (some APIs use this)
urls_to_test = [
    f"https://api.marketdata.app/v1/stocks/quotes/SPY/?token={token}",
    f"https://api.marketdata.app/v1/stocks/quotes/SPY?token={token}",
    f"https://api.marketdata.app/stocks/quotes/SPY/?token={token}",
]

for url in urls_to_test:
    print(f"\nTrying: {url[:80]}...")
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("[SUCCESS] API Response:")
            print(data)
            break
        else:
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

print("\n" + "=" * 60)
