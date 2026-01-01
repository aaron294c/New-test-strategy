#!/usr/bin/env python3
"""Test different MarketData.app authentication formats."""
import requests
import os

# Set API key
token = 'Xp6qdnbAOcXkoGxq7njOz3aT4xsILsqC'
os.environ['MARKETDATA_API_KEY'] = token

print("Testing MarketData.app authentication formats...")
print("=" * 60)

base_url = "https://api.marketdata.app/v1/stocks/quotes/SPY/"

# Test different auth formats
auth_formats = [
    ("Query parameter", {}, {'token': token}),
    ("Query parameter (apikey)", {}, {'apikey': token}),
    ("Authorization: Token", {'Authorization': f'Token {token}'}, {}),
    ("Authorization: Bearer", {'Authorization': f'Bearer {token}'}, {}),
    ("Authorization: ApiKey", {'Authorization': f'ApiKey {token}'}, {}),
    ("X-API-Key header", {'X-API-Key': token}, {}),
]

for name, headers, params in auth_formats:
    print(f"\nTrying: {name}")
    try:
        response = requests.get(base_url, headers=headers, params=params, timeout=10)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  [SUCCESS] This format works!")
            print(f"  Response: {response.json()}")
            break
        elif response.status_code == 401:
            print(f"  [FAIL] Unauthorized")
        else:
            print(f"  Response: {response.text[:100]}")
    except Exception as e:
        print(f"  [ERROR] {e}")

print("\n" + "=" * 60)
