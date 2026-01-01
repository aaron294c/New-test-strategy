#!/usr/bin/env python3
"""
Tradier Options API Integration

Provides accurate options data with calculated Greeks from Tradier's API.
Free sandbox account: https://developer.tradier.com/getting_started
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

logger = logging.getLogger(__name__)

# Tradier API Configuration
TRADIER_API_BASE = "https://sandbox.tradier.com/v1"  # Sandbox (free)
# For production: "https://api.tradier.com/v1"

# Get API key from environment or use sandbox default
TRADIER_API_KEY = os.getenv('TRADIER_API_KEY', 'Bearer YOUR_SANDBOX_TOKEN')

HEADERS = {
    'Authorization': TRADIER_API_KEY,
    'Accept': 'application/json'
}


def get_tradier_api_key() -> str:
    """
    Get Tradier API key from environment or provide instructions.

    Free Sandbox Setup:
    1. Go to https://developer.tradier.com/user/sign_up
    2. Create free sandbox account
    3. Get your sandbox token from https://developer.tradier.com/user/settings
    4. Set environment variable: TRADIER_API_KEY=Bearer YOUR_SANDBOX_TOKEN
    """
    api_key = os.getenv('TRADIER_API_KEY')

    if not api_key or api_key == 'Bearer YOUR_SANDBOX_TOKEN':
        logger.warning("""
        ═══════════════════════════════════════════════════════════════
        TRADIER API KEY NOT CONFIGURED
        ═══════════════════════════════════════════════════════════════

        To get accurate Greeks and IV data, set up free Tradier sandbox:

        1. Sign up: https://developer.tradier.com/user/sign_up
        2. Get sandbox token: https://developer.tradier.com/user/settings
        3. Set environment variable:

           Windows: set TRADIER_API_KEY=Bearer YOUR_SANDBOX_TOKEN
           Linux/Mac: export TRADIER_API_KEY=Bearer YOUR_SANDBOX_TOKEN

        Then restart the backend.
        ═══════════════════════════════════════════════════════════════
        """)
        return None

    return api_key


def fetch_options_chain(symbol: str, expiration: str) -> Optional[List[Dict]]:
    """
    Fetch options chain for a specific expiration from Tradier.

    Args:
        symbol: Stock symbol (e.g., "SPY")
        expiration: Expiration date in YYYY-MM-DD format

    Returns:
        List of option contracts with Greeks, or None if failed
    """
    api_key = get_tradier_api_key()
    if not api_key:
        return None

    try:
        url = f"{TRADIER_API_BASE}/markets/options/chains"
        params = {
            'symbol': symbol,
            'expiration': expiration,
            'greeks': 'true'  # Include Greeks in response
        }

        response = requests.get(url, headers={'Authorization': api_key, 'Accept': 'application/json'}, params=params)
        response.raise_for_status()

        data = response.json()

        if 'options' not in data or 'option' not in data['options']:
            logger.warning(f"No options data returned for {symbol} {expiration}")
            return None

        options = data['options']['option']

        # Convert to list if single option
        if isinstance(options, dict):
            options = [options]

        logger.info(f"Fetched {len(options)} options for {symbol} {expiration}")
        return options

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Tradier options chain: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching Tradier options: {e}")
        return None


def fetch_leaps_options(symbol: str = "SPY", min_days: int = 180, max_days: int = 730) -> List[Dict]:
    """
    Fetch LEAPS options (6-24 months) with accurate Greeks from Tradier.

    Args:
        symbol: Stock symbol (default "SPY")
        min_days: Minimum days to expiration (default 180 = 6 months)
        max_days: Maximum days to expiration (default 730 = 24 months)

    Returns:
        List of LEAPS options with calculated Greeks
    """
    api_key = get_tradier_api_key()
    if not api_key:
        logger.error("Cannot fetch LEAPS without Tradier API key")
        return []

    try:
        # First, get available expirations
        url = f"{TRADIER_API_BASE}/markets/options/expirations"
        params = {'symbol': symbol, 'includeAllRoots': 'true'}

        response = requests.get(url, headers={'Authorization': api_key, 'Accept': 'application/json'}, params=params)
        response.raise_for_status()

        data = response.json()

        if 'expirations' not in data or 'date' not in data['expirations']:
            logger.error(f"No expirations found for {symbol}")
            return []

        expirations = data['expirations']['date']
        if isinstance(expirations, str):
            expirations = [expirations]

        # Filter for LEAPS expirations (6-24 months out)
        today = datetime.now()
        leaps_expirations = []

        for exp_str in expirations:
            exp_date = datetime.strptime(exp_str, '%Y-%m-%d')
            days_to_exp = (exp_date - today).days

            if min_days <= days_to_exp <= max_days:
                leaps_expirations.append(exp_str)

        logger.info(f"Found {len(leaps_expirations)} LEAPS expirations for {symbol}")

        # Fetch options chains for each LEAPS expiration
        all_options = []

        for expiration in leaps_expirations[:5]:  # Limit to 5 expirations to avoid rate limits
            options = fetch_options_chain(symbol, expiration)
            if options:
                # Filter for calls only
                calls = [opt for opt in options if opt.get('option_type') == 'call']
                all_options.extend(calls)

        logger.info(f"Total LEAPS options fetched: {len(all_options)}")
        return all_options

    except Exception as e:
        logger.error(f"Error fetching LEAPS options: {e}")
        return []


def parse_tradier_option(option: Dict, current_price: float) -> Dict:
    """
    Parse Tradier option data into our standard format.

    Args:
        option: Raw option data from Tradier API
        current_price: Current stock price

    Returns:
        Parsed option data with Greeks
    """
    try:
        strike = float(option['strike'])
        premium = float(option.get('last', option.get('bid', 0)))

        # Calculate intrinsic and extrinsic
        intrinsic = max(0, current_price - strike)
        extrinsic = premium - intrinsic
        extrinsic_pct = (extrinsic / premium * 100) if premium > 0 else 0

        # Get Greeks from Tradier (already calculated!)
        greeks = option.get('greeks', {})

        return {
            'symbol': option['symbol'],
            'strike': strike,
            'expiration': option['expiration_date'],
            'days_to_expiration': int(option.get('expiration_days', 0)),
            'years_to_expiration': round(int(option.get('expiration_days', 0)) / 365.25, 2),
            'current_price': current_price,
            'premium': premium,
            'bid': float(option.get('bid', 0)),
            'ask': float(option.get('ask', 0)),
            'bid_ask_spread': float(option.get('ask', 0)) - float(option.get('bid', 0)),
            'bid_ask_spread_pct': ((float(option.get('ask', 0)) - float(option.get('bid', 0))) / premium * 100) if premium > 0 else 0,
            'volume': int(option.get('volume', 0)),
            'open_interest': int(option.get('open_interest', 0)),
            'implied_volatility': float(greeks.get('smv_vol', 0)),  # Tradier's calculated IV
            'intrinsic_value': intrinsic,
            'extrinsic_value': extrinsic,
            'extrinsic_pct': extrinsic_pct,
            'strike_pct': ((strike / current_price - 1) * 100),
            # REAL GREEKS FROM TRADIER (already calculated!)
            'delta': float(greeks.get('delta', 0)),
            'gamma': float(greeks.get('gamma', 0)),
            'vega': float(greeks.get('vega', 0)),
            'theta': float(greeks.get('theta', 0)),
            'rho': float(greeks.get('rho', 0)),
        }

    except Exception as e:
        logger.error(f"Error parsing Tradier option: {e}")
        return None


if __name__ == "__main__":
    # Test the Tradier API integration
    logging.basicConfig(level=logging.INFO)

    print("Testing Tradier API integration...")
    print("=" * 60)

    # Check if API key is configured
    api_key = get_tradier_api_key()

    if api_key and api_key != 'Bearer YOUR_SANDBOX_TOKEN':
        print("✓ Tradier API key found")

        # Fetch some LEAPS options
        options = fetch_leaps_options("SPY", min_days=180, max_days=365)

        if options:
            print(f"\n✓ Fetched {len(options)} LEAPS options")
            print("\nSample option with real Greeks:")

            # Get current SPY price
            import yfinance as yf
            spy = yf.Ticker("SPY")
            current_price = spy.history(period="1d")['Close'].iloc[-1]

            # Parse first option
            parsed = parse_tradier_option(options[0], current_price)
            if parsed:
                print(f"\nStrike: ${parsed['strike']:.2f}")
                print(f"Delta: {parsed['delta']:.4f}")
                print(f"Gamma: {parsed['gamma']:.6f}")
                print(f"Vega: {parsed['vega']:.4f}")
                print(f"Theta: {parsed['theta']:.4f}")
                print(f"IV: {parsed['implied_volatility']:.4f}")
        else:
            print("✗ No options data returned")
    else:
        print("\n✗ Tradier API key not configured")
        print("Follow instructions above to set up free sandbox account")
