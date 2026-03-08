#!/usr/bin/env python3
"""Test MiniMax 2.5 API setup via OpenRouter"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_minimax_openrouter():
    """Test connection to MiniMax 2.5 via OpenRouter"""

    api_key = os.getenv('OPENROUTER_API_KEY')

    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in .env.local")
        return False

    print(f"✓ API Key configured")

    # OpenRouter endpoint
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "MiniMax Test"
    }

    payload = {
        "model": "minimax/minimax-01",
        "max_tokens": 256,
        "messages": [
            {
                "role": "user",
                "content": "Say 'Hello from MiniMax!' briefly."
            }
        ]
    }

    print(f"✓ Base URL: {url}")
    print("✓ Model: minimax/minimax-01")
    print("\n📡 Testing MiniMax 2.5 connection via OpenRouter...")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            print("✅ Connection successful!")
            print(f"\nResponse:\n{data['choices'][0]['message']['content']}")
            return True
        else:
            print(f"❌ Connection failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_minimax_openrouter()
