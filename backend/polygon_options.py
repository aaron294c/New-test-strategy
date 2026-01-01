#!/usr/bin/env python3
"""
Polygon.io Options API Integration

Provides accurate options data with calculated Greeks from Polygon.io.
Free tier: 5 requests/minute
Sign up: https://polygon.io/
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import time

logger = logging.getLogger(__name__)

# Polygon API Configuration
POLYGON_API_BASE = "https://api.polygon.io"
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY', '')


def get_polygon_api_key() -> str:
    """
    Get Polygon API key from environment.

    Free Setup:
    1. Go to https://polygon.io/
    2. Sign up for free account (no credit card required)
    3. Get your API key from dashboard
    4. Set environment variable: POLYGON_API_KEY=your_key_here
    """
    api_key = os.getenv('POLYGON_API_KEY')

    if not api_key:
        logger.warning("""
        ═══════════════════════════════════════════════════════════════
        POLYGON API KEY NOT CONFIGURED
        ═══════════════════════════════════════════════════════════════

        To get accurate Greeks and IV data:

        1. Sign up FREE: https://polygon.io/
        2. Get API key from dashboard
        3. Set environment variable:

           Windows: setx POLYGON_API_KEY your_key_here
           Linux/Mac: export POLYGON_API_KEY=your_key_here

        Then restart the backend.

        Free tier: 5 API calls/minute (perfect for LEAPS scanning)
        ═══════════════════════════════════════════════════════════════
        """)
        return None

    return api_key


def fetch_options_snapshot(ticker: str, contract: str) -> Optional[Dict]:
    """
    Fetch single option snapshot with Greeks from Polygon.

    Args:
        ticker: Underlying ticker (e.g., "SPY")
        contract: Option contract symbol (e.g., "O:SPY251219C00500000")

    Returns:
        Option data with Greeks, or None if failed
    """
    api_key = get_polygon_api_key()
    if not api_key:
        return None

    try:
        url = f"{POLYGON_API_BASE}/v3/snapshot/options/{ticker}/{contract}"
        params = {'apiKey': api_key}

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 429:
            logger.warning("Polygon rate limit hit, waiting...")
            time.sleep(12)  # Wait 12 seconds for rate limit reset
            response = requests.get(url, params=params, timeout=10)

        response.raise_for_status()
        data = response.json()

        if 'results' in data:
            return data['results']

        return None

    except Exception as e:
        logger.error(f"Error fetching Polygon option snapshot: {e}")
        return None


def fetch_options_chain_polygon(ticker: str, expiration_date: str) -> List[Dict]:
    """
    Fetch options chain for specific expiration from Polygon.

    Args:
        ticker: Underlying ticker (e.g., "SPY")
        expiration_date: Expiration in YYYY-MM-DD format

    Returns:
        List of option contracts
    """
    api_key = get_polygon_api_key()
    if not api_key:
        return []

    try:
        # Get options contracts
        url = f"{POLYGON_API_BASE}/v3/reference/options/contracts"

        params = {
            'underlying_ticker': ticker,
            'expiration_date': expiration_date,
            'contract_type': 'call',
            'limit': 1000,
            'apiKey': api_key
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 429:
            logger.warning("Polygon rate limit hit, waiting...")
            time.sleep(12)
            response = requests.get(url, params=params, timeout=10)

        response.raise_for_status()
        data = response.json()

        if 'results' in data:
            return data['results']

        return []

    except Exception as e:
        logger.error(f"Error fetching Polygon options chain: {e}")
        return []


def fetch_leaps_with_greeks(ticker: str = "SPY", min_days: int = 180, max_days: int = 730) -> List[Dict]:
    """
    Fetch LEAPS options with Greeks from Polygon.io.

    Args:
        ticker: Stock ticker (default "SPY")
        min_days: Minimum days to expiration
        max_days: Maximum days to expiration

    Returns:
        List of options with Greeks
    """
    api_key = get_polygon_api_key()
    if not api_key:
        return []

    try:
        # Get stock price first
        url = f"{POLYGON_API_BASE}/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}"
        params = {'apiKey': api_key}

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        stock_data = response.json()
        current_price = stock_data.get('ticker', {}).get('lastTrade', {}).get('p', 0)

        if not current_price:
            logger.error("Could not get current stock price from Polygon")
            return []

        logger.info(f"Current {ticker} price: ${current_price:.2f}")

        # Generate LEAPS expiration dates to check
        today = datetime.now()
        expirations_to_check = []

        # Check monthly options (3rd Friday of each month)
        for months_ahead in range(6, 25):  # 6 to 24 months
            target_date = today + timedelta(days=30 * months_ahead)

            # Find 3rd Friday of that month
            year = target_date.year
            month = target_date.month

            # First day of month
            first_day = datetime(year, month, 1)
            # First Friday
            days_until_friday = (4 - first_day.weekday()) % 7
            first_friday = first_day + timedelta(days=days_until_friday)
            # Third Friday
            third_friday = first_friday + timedelta(days=14)

            exp_str = third_friday.strftime('%Y-%m-%d')
            days_to_exp = (third_friday - today).days

            if min_days <= days_to_exp <= max_days:
                expirations_to_check.append(exp_str)

        logger.info(f"Checking {len(expirations_to_check)} potential LEAPS expirations")

        # Fetch options for each expiration (limit to 3 to avoid rate limits)
        all_leaps = []

        for exp_date in expirations_to_check[:3]:
            logger.info(f"Fetching options for {exp_date}...")

            # Get contracts list
            contracts = fetch_options_chain_polygon(ticker, exp_date)

            if not contracts:
                logger.warning(f"No contracts found for {exp_date}")
                continue

            logger.info(f"Found {len(contracts)} contracts for {exp_date}")

            # For each contract, get snapshot with Greeks (limit to prevent rate limits)
            # Focus on ITM and ATM strikes
            filtered_contracts = []
            for contract in contracts:
                strike = contract.get('strike_price', 0)
                if strike > 0:
                    # Only get options within ±30% of current price
                    strike_pct = abs((strike - current_price) / current_price)
                    if strike_pct <= 0.30:
                        filtered_contracts.append(contract)

            logger.info(f"Filtered to {len(filtered_contracts)} contracts near ATM")

            # Get snapshots with Greeks (limit to 20 to avoid rate limits)
            for i, contract in enumerate(filtered_contracts[:20]):
                if i > 0 and i % 5 == 0:
                    # Rate limit: 5 requests per minute for free tier
                    logger.info(f"Rate limit pause (processed {i} contracts)...")
                    time.sleep(12)  # Wait 12 seconds

                ticker_symbol = contract.get('ticker', '')
                if not ticker_symbol:
                    continue

                snapshot = fetch_options_snapshot(ticker, ticker_symbol)

                if snapshot:
                    parsed = parse_polygon_option(snapshot, contract, current_price, exp_date)
                    if parsed:
                        all_leaps.append(parsed)

            # Pause between expirations
            if expirations_to_check.index(exp_date) < len(expirations_to_check) - 1:
                time.sleep(12)

        logger.info(f"Total LEAPS fetched from Polygon: {len(all_leaps)}")
        return all_leaps

    except Exception as e:
        logger.error(f"Error fetching LEAPS from Polygon: {e}")
        import traceback
        traceback.print_exc()
        return []


def parse_polygon_option(snapshot: Dict, contract: Dict, current_price: float, expiration: str) -> Optional[Dict]:
    """
    Parse Polygon option data into standard format.

    Args:
        snapshot: Option snapshot data with Greeks
        contract: Contract details
        current_price: Current stock price
        expiration: Expiration date

    Returns:
        Parsed option data
    """
    try:
        strike = float(contract.get('strike_price', 0))

        # Get Greeks from snapshot
        greeks = snapshot.get('greeks', {})
        details = snapshot.get('details', {})
        day = snapshot.get('day', {})
        last_quote = snapshot.get('last_quote', {})

        # Premium from last trade or mid price
        last_price = details.get('last_price', 0)
        bid = last_quote.get('bid', 0)
        ask = last_quote.get('ask', 0)
        premium = last_price if last_price > 0 else (bid + ask) / 2 if bid and ask else 0

        if premium <= 0:
            return None

        # Calculate days to expiration
        exp_date = datetime.strptime(expiration, '%Y-%m-%d')
        days_to_exp = (exp_date - datetime.now()).days

        # Calculate intrinsic and extrinsic
        intrinsic = max(0, current_price - strike)
        extrinsic = premium - intrinsic
        extrinsic_pct = (extrinsic / premium * 100) if premium > 0 else 0

        return {
            'symbol': contract.get('ticker', ''),
            'strike': strike,
            'expiration': expiration,
            'days_to_expiration': days_to_exp,
            'years_to_expiration': round(days_to_exp / 365.25, 2),
            'current_price': current_price,
            'premium': premium,
            'bid': float(bid) if bid else 0,
            'ask': float(ask) if ask else 0,
            'bid_ask_spread': float(ask - bid) if ask and bid else 0,
            'bid_ask_spread_pct': ((ask - bid) / premium * 100) if premium > 0 and ask and bid else 0,
            'volume': int(day.get('volume', 0)),
            'open_interest': int(details.get('open_interest', 0)),
            'implied_volatility': float(greeks.get('implied_volatility', 0)) if greeks.get('implied_volatility') else 0,
            'intrinsic_value': intrinsic,
            'extrinsic_value': extrinsic,
            'extrinsic_pct': extrinsic_pct,
            'strike_pct': ((strike / current_price - 1) * 100),
            # REAL GREEKS FROM POLYGON
            'delta': float(greeks.get('delta', 0)),
            'gamma': float(greeks.get('gamma', 0)),
            'vega': float(greeks.get('vega', 0)),
            'theta': float(greeks.get('theta', 0)),
            'rho': float(greeks.get('rho', 0)),
        }

    except Exception as e:
        logger.error(f"Error parsing Polygon option: {e}")
        return None


if __name__ == "__main__":
    # Test Polygon integration
    logging.basicConfig(level=logging.INFO)

    print("Testing Polygon.io API integration...")
    print("=" * 60)

    api_key = get_polygon_api_key()

    if api_key:
        print("✓ Polygon API key found")
        print("\nFetching LEAPS options (this may take 1-2 minutes due to rate limits)...")

        options = fetch_leaps_with_greeks("SPY", min_days=180, max_days=365)

        if options:
            print(f"\n✓ Fetched {len(options)} LEAPS with real Greeks")

            if options:
                print("\nSample option:")
                opt = options[0]
                print(f"Strike: ${opt['strike']:.2f}")
                print(f"Delta: {opt['delta']:.4f}")
                print(f"Vega: {opt['vega']:.4f}")
                print(f"IV: {opt['implied_volatility']:.4f}")
        else:
            print("✗ No options returned")
    else:
        print("✗ Polygon API key not configured")
