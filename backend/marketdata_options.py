#!/usr/bin/env python3
"""
MarketData.app Options API Integration

Free tier includes Greeks!
- 100 API calls/day (free)
- Includes delta, gamma, theta, vega, rho
- Real-time IV data

Sign up: https://www.marketdata.app/
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import time

logger = logging.getLogger(__name__)

# MarketData API Configuration
MARKETDATA_API_BASE = "https://api.marketdata.app/v1"
MARKETDATA_API_KEY = os.getenv('MARKETDATA_API_KEY', '')


def get_marketdata_api_key() -> str:
    """
    Get MarketData API key from environment.

    Free Setup (includes Greeks!):
    1. Go to https://www.marketdata.app/
    2. Sign up for FREE account (100 calls/day)
    3. Get API token from dashboard
    4. Set: MARKETDATA_API_KEY=your_token
    """
    api_key = os.getenv('MARKETDATA_API_KEY')

    if not api_key:
        logger.warning("""
        ═══════════════════════════════════════════════════════════════
        MARKETDATA API KEY NOT CONFIGURED
        ═══════════════════════════════════════════════════════════════

        MarketData.app provides GREEKS in FREE tier!

        1. Sign up FREE: https://www.marketdata.app/
        2. Get API token from dashboard
        3. Set environment variable:

           Windows: setx MARKETDATA_API_KEY your_token_here
           Linux/Mac: export MARKETDATA_API_KEY=your_token_here

        Free tier: 100 API calls/day (includes Greeks!)
        ═══════════════════════════════════════════════════════════════
        """)
        return None

    return api_key


def fetch_option_quote(symbol: str, expiration: str, strike: float, option_type: str = "call") -> Optional[Dict]:
    """
    Fetch single option quote with Greeks from MarketData.

    Args:
        symbol: Underlying symbol (e.g., "SPY")
        expiration: Expiration date YYYY-MM-DD
        strike: Strike price
        option_type: "call" or "put"

    Returns:
        Option data with Greeks
    """
    api_key = get_marketdata_api_key()
    if not api_key:
        return None

    try:
        # Format option symbol: SYMBOL{YYMMDD}{C/P}{strike*1000}
        exp_date = datetime.strptime(expiration, '%Y-%m-%d')
        exp_str = exp_date.strftime('%y%m%d')
        cp = 'C' if option_type.lower() == 'call' else 'P'
        strike_str = f"{int(strike * 1000):08d}"

        option_symbol = f"{symbol}{exp_str}{cp}{strike_str}"

        url = f"{MARKETDATA_API_BASE}/options/quotes/{option_symbol}/"

        headers = {
            'Authorization': f'Token {api_key}'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 429:
            logger.warning("MarketData rate limit, waiting...")
            time.sleep(2)
            response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 404:
            return None  # Option not found

        response.raise_for_status()
        data = response.json()

        if data.get('s') == 'ok':
            return data

        return None

    except Exception as e:
        logger.debug(f"Error fetching MarketData quote for {option_symbol}: {e}")
        return None


def fetch_options_expirations(symbol: str) -> List[str]:
    """
    Get available option expirations for a symbol.

    Args:
        symbol: Stock symbol

    Returns:
        List of expiration dates (YYYY-MM-DD)
    """
    api_key = get_marketdata_api_key()
    if not api_key:
        return []

    try:
        url = f"{MARKETDATA_API_BASE}/options/expirations/{symbol}/"
        headers = {'Authorization': f'Token {api_key}'}

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get('s') == 'ok' and 'expirations' in data:
            expirations = data['expirations']
            # Convert from Unix timestamp to YYYY-MM-DD
            exp_dates = []
            for ts in expirations:
                date_obj = datetime.fromtimestamp(ts)
                exp_dates.append(date_obj.strftime('%Y-%m-%d'))
            return exp_dates

        return []

    except Exception as e:
        logger.error(f"Error fetching expirations: {e}")
        return []


def fetch_options_chain(symbol: str, expiration: str) -> List[Dict]:
    """
    Fetch options chain for specific expiration.

    Args:
        symbol: Stock symbol
        expiration: Expiration date YYYY-MM-DD

    Returns:
        List of strikes available
    """
    api_key = get_marketdata_api_key()
    if not api_key:
        return []

    try:
        url = f"{MARKETDATA_API_BASE}/options/chain/{symbol}/"
        headers = {'Authorization': f'Token {api_key}'}
        params = {
            'expiration': expiration,
            'side': 'call'
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get('s') == 'ok':
            return data.get('optionChain', [])

        return []

    except Exception as e:
        logger.error(f"Error fetching chain: {e}")
        return []


def fetch_leaps_with_greeks_marketdata(symbol: str = "SPY", min_days: int = 180, max_days: int = 730) -> List[Dict]:
    """
    Fetch LEAPS options with real Greeks from MarketData.app.

    Args:
        symbol: Stock symbol (default "SPY")
        min_days: Minimum days to expiration
        max_days: Maximum days to expiration

    Returns:
        List of LEAPS with Greeks
    """
    api_key = get_marketdata_api_key()
    if not api_key:
        return []

    try:
        # Get current stock price
        url = f"{MARKETDATA_API_BASE}/stocks/quotes/{symbol}/"
        headers = {'Authorization': f'Token {api_key}'}

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        stock_data = response.json()
        current_price = stock_data.get('last', [0])[0] if stock_data.get('s') == 'ok' else 0

        if not current_price:
            logger.error("Could not get current stock price")
            return []

        logger.info(f"Current {symbol} price: ${current_price:.2f}")

        # Get expirations
        expirations = fetch_options_expirations(symbol)

        if not expirations:
            logger.error("No expirations found")
            return []

        # Filter for LEAPS
        today = datetime.now()
        leaps_expirations = []

        for exp_str in expirations:
            exp_date = datetime.strptime(exp_str, '%Y-%m-%d')
            days_to_exp = (exp_date - today).days

            if min_days <= days_to_exp <= max_days:
                leaps_expirations.append(exp_str)

        logger.info(f"Found {len(leaps_expirations)} LEAPS expirations")

        # Fetch options for each expiration
        all_leaps = []
        api_calls = 0
        max_calls = 50  # Stay under daily limit

        for exp in leaps_expirations[:3]:  # Limit to 3 expirations
            logger.info(f"Fetching {exp}...")

            # Get chain to know available strikes
            chain = fetch_options_chain(symbol, exp)
            api_calls += 1

            if not chain or api_calls >= max_calls:
                break

            # Filter strikes near current price (±30%)
            strikes_to_fetch = []
            for item in chain:
                strike = item.get('strike')
                if strike:
                    pct_diff = abs((strike - current_price) / current_price)
                    if pct_diff <= 0.30:  # Within ±30%
                        strikes_to_fetch.append(strike)

            logger.info(f"  {len(strikes_to_fetch)} strikes near money")

            # Fetch quotes with Greeks (limit to avoid hitting daily limit)
            for strike in strikes_to_fetch[:15]:  # Max 15 per expiration
                if api_calls >= max_calls:
                    logger.warning("Approaching API call limit, stopping")
                    break

                quote = fetch_option_quote(symbol, exp, strike, "call")
                api_calls += 1

                if quote:
                    parsed = parse_marketdata_option(quote, current_price, exp, strike)
                    if parsed:
                        all_leaps.append(parsed)

                time.sleep(0.1)  # Small delay to be nice to API

        logger.info(f"Fetched {len(all_leaps)} LEAPS with Greeks (used {api_calls} API calls)")
        return all_leaps

    except Exception as e:
        logger.error(f"Error fetching LEAPS: {e}")
        import traceback
        traceback.print_exc()
        return []


def parse_marketdata_option(quote: Dict, current_price: float, expiration: str, strike: float) -> Optional[Dict]:
    """
    Parse MarketData option quote into standard format.

    Args:
        quote: Raw quote data from MarketData
        current_price: Current stock price
        expiration: Expiration date
        strike: Strike price

    Returns:
        Parsed option data with Greeks
    """
    try:
        # Extract data from response (MarketData returns arrays)
        bid = quote.get('bid', [0])[0] if quote.get('bid') else 0
        ask = quote.get('ask', [0])[0] if quote.get('ask') else 0
        last = quote.get('last', [0])[0] if quote.get('last') else 0

        premium = last if last > 0 else (bid + ask) / 2 if bid and ask else 0

        if premium <= 0:
            return None

        # Greeks from MarketData
        delta = quote.get('delta', [0])[0] if quote.get('delta') else 0
        gamma = quote.get('gamma', [0])[0] if quote.get('gamma') else 0
        theta = quote.get('theta', [0])[0] if quote.get('theta') else 0
        vega = quote.get('vega', [0])[0] if quote.get('vega') else 0
        rho = quote.get('rho', [0])[0] if quote.get('rho') else 0
        iv = quote.get('iv', [0])[0] if quote.get('iv') else 0

        # Calculate days to expiration
        exp_date = datetime.strptime(expiration, '%Y-%m-%d')
        days_to_exp = (exp_date - datetime.now()).days

        # Calculate intrinsic and extrinsic
        intrinsic = max(0, current_price - strike)
        extrinsic = premium - intrinsic
        extrinsic_pct = (extrinsic / premium * 100) if premium > 0 else 0

        volume = quote.get('volume', [0])[0] if quote.get('volume') else 0
        oi = quote.get('openInterest', [0])[0] if quote.get('openInterest') else 0

        return {
            'symbol': quote.get('optionSymbol', [''])[0],
            'strike': strike,
            'expiration': expiration,
            'days_to_expiration': days_to_exp,
            'years_to_expiration': round(days_to_exp / 365.25, 2),
            'current_price': current_price,
            'premium': premium,
            'bid': bid,
            'ask': ask,
            'bid_ask_spread': ask - bid if ask and bid else 0,
            'bid_ask_spread_pct': ((ask - bid) / premium * 100) if premium > 0 and ask and bid else 0,
            'volume': int(volume),
            'open_interest': int(oi),
            'implied_volatility': iv,
            'intrinsic_value': intrinsic,
            'extrinsic_value': extrinsic,
            'extrinsic_pct': extrinsic_pct,
            'strike_pct': ((strike / current_price - 1) * 100),
            # REAL GREEKS FROM MARKETDATA
            'delta': delta,
            'gamma': gamma,
            'vega': vega,
            'theta': theta,
            'rho': rho,
        }

    except Exception as e:
        logger.error(f"Error parsing MarketData option: {e}")
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Testing MarketData.app API...")
    print("=" * 60)

    api_key = get_marketdata_api_key()

    if api_key:
        print("✓ MarketData API key found")
        print("\nFetching LEAPS with Greeks...")

        options = fetch_leaps_with_greeks_marketdata("SPY", 180, 365)

        if options:
            print(f"\n✓ Fetched {len(options)} LEAPS with REAL GREEKS")

            print("\nSample option:")
            opt = options[0]
            print(f"Strike: ${opt['strike']:.2f}")
            print(f"Delta: {opt['delta']:.4f}")
            print(f"Vega: {opt['vega']:.4f}")
            print(f"Theta: {opt['theta']:.4f}")
            print(f"IV: {opt['implied_volatility']:.4f}")
        else:
            print("✗ No options returned")
    else:
        print("✗ API key not configured")
