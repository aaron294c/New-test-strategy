#!/usr/bin/env python3
"""
LEAPS Options Analyzer Module

Fetches and analyzes SPX LEAPS options based on VIX-driven strategies.
Includes option chain fetching, Greek calculations, and filtering.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from scipy.stats import norm

# Import MarketData.app integration for real Greeks
try:
    from marketdata_options import fetch_leaps_with_greeks_marketdata, get_marketdata_api_key
    MARKETDATA_AVAILABLE = True
except ImportError:
    MARKETDATA_AVAILABLE = False
    logger.warning("MarketData.app module not available")

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BlackScholesGreeks:
    """Calculate option Greeks using Black-Scholes model."""

    @staticmethod
    def calculate_greeks(
        S: float,  # Current stock price
        K: float,  # Strike price
        T: float,  # Time to expiration (years)
        r: float,  # Risk-free rate
        sigma: float,  # Implied volatility
        option_type: str = 'call'
    ) -> Dict[str, float]:
        """
        Calculate option Greeks using Black-Scholes formula.

        Returns:
            dict: {
                'delta': Delta (sensitivity to price)
                'gamma': Gamma (rate of delta change)
                'vega': Vega (sensitivity to volatility)
                'theta': Theta (time decay)
                'rho': Rho (sensitivity to interest rate)
            }
        """
        try:
            if T <= 0:
                return {'delta': 0, 'gamma': 0, 'vega': 0, 'theta': 0, 'rho': 0}

            # Calculate d1 and d2
            d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)

            # Calculate Greeks
            if option_type.lower() == 'call':
                delta = norm.cdf(d1)
                theta = (
                    -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                    - r * K * np.exp(-r * T) * norm.cdf(d2)
                ) / 365
            else:  # put
                delta = norm.cdf(d1) - 1
                theta = (
                    -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                    + r * K * np.exp(-r * T) * norm.cdf(-d2)
                ) / 365

            gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
            vega = S * norm.pdf(d1) * np.sqrt(T) / 100  # Per 1% change
            rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100 if option_type.lower() == 'call' else -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100

            # Debug logging for deep ITM options with unexpectedly high vega
            moneyness = (S - K) / K * 100  # % ITM for calls
            if delta > 0.85 and vega > 0.15:
                logger.debug(f"High vega for deep ITM: Strike=${K:.0f}, Spot=${S:.2f}, Delta={delta:.3f}, Vega={vega:.4f}, IV={sigma*100:.1f}%, T={T:.2f}y, d1={d1:.2f}, pdf(d1)={norm.pdf(d1):.6f}, Moneyness={moneyness:.1f}%ITM")

            return {
                'delta': round(delta, 4),
                'gamma': round(gamma, 6),
                'vega': round(vega, 4),
                'theta': round(theta, 4),
                'rho': round(rho, 4)
            }

        except Exception as e:
            logger.error(f"Error calculating Greeks: {e}")
            return {'delta': 0, 'gamma': 0, 'vega': 0, 'theta': 0, 'rho': 0}


def calculate_iv_rank_percentile(ticker_symbol: str, current_iv: float, atm_iv: Optional[float] = None) -> Tuple[float, float]:
    """
    Calculate IV Rank and IV Percentile using real historical VIX data.

    IV Rank: (Current IV - 52-week Low) / (52-week High - 52-week Low)
    IV Percentile: Percentage of days where IV was BELOW current level

    Uses VIX as proxy for SPY implied volatility (highly correlated).

    Args:
        ticker_symbol: Ticker symbol (e.g., "SPY")
        current_iv: Current implied volatility (as decimal, e.g., 0.20 for 20%)
        atm_iv: ATM IV for this expiration (optional, will estimate if not provided)

    Returns:
        Tuple of (iv_rank, iv_percentile)
    """
    try:
        current_iv_pct = current_iv * 100

        # Fetch historical VIX data (52 weeks = ~252 trading days)
        # VIX represents S&P 500 30-day implied volatility
        # SPY tracks S&P 500, so VIX is excellent proxy for SPY IV
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="1y")  # 1 year of daily data

        if hist.empty or len(hist) < 20:
            logger.warning("Could not fetch VIX historical data, using fallback calculation")
            # Fallback to simple calculation
            iv_rank = max(0, min(1, (current_iv_pct - 15) / 45))
            iv_percentile = iv_rank * 100
            return float(iv_rank), float(iv_percentile)

        # Extract closing VIX values (these are IV percentages)
        vix_values = hist['Close'].values

        # Calculate IV Rank: (Current - Min) / (Max - Min)
        vix_min = float(np.min(vix_values))
        vix_max = float(np.max(vix_values))
        vix_range = vix_max - vix_min

        if vix_range > 0:
            iv_rank = (current_iv_pct - vix_min) / vix_range
        else:
            iv_rank = 0.5

        # Calculate IV Percentile: % of days where IV was BELOW current
        days_below = np.sum(vix_values < current_iv_pct)
        total_days = len(vix_values)
        iv_percentile = (days_below / total_days) * 100

        # Clip to valid ranges
        iv_rank = float(np.clip(iv_rank, 0, 1))
        iv_percentile = float(np.clip(iv_percentile, 0, 100))

        logger.debug(
            f"IV Rank/Percentile (from VIX history): "
            f"IV={current_iv_pct:.1f}%, "
            f"52w Range={vix_min:.1f}-{vix_max:.1f}%, "
            f"Rank={iv_rank:.2f}, "
            f"Percentile={iv_percentile:.0f}% "
            f"({days_below}/{total_days} days below)"
        )

        return iv_rank, iv_percentile

    except Exception as e:
        logger.warning(f"Error calculating IV rank/percentile from VIX: {e}")
        # Safe fallback
        iv_rank = max(0, min(1, (current_iv * 100 - 15) / 45))
        iv_percentile = iv_rank * 100
        return float(iv_rank), float(iv_percentile)


def fetch_spx_options(min_days: int = 180, max_days: int = 730, use_sample: bool = False) -> List[Dict]:
    """
    Fetch SPX options chain filtered for LEAPS (6-24 months).

    Tries MarketData.app API first (real Greeks), falls back to yfinance (calculated Greeks).

    Args:
        min_days: Minimum days to expiration (default 180 = 6 months)
        max_days: Maximum days to expiration (default 730 = 24 months)
        use_sample: Force use of sample data (default False)

    Returns:
        List of option contracts with metadata
    """
    try:
        if use_sample:
            logger.info("Using sample data (forced)")
            return _generate_sample_options(450.0)

        # Try MarketData.app API first (real Greeks in free tier!)
        if MARKETDATA_AVAILABLE:
            api_key = get_marketdata_api_key()
            if api_key:
                logger.info("✓ MarketData API key found")
                logger.info("Using MarketData.app API for accurate Greeks and IV")

                try:
                    marketdata_options = fetch_leaps_with_greeks_marketdata("SPY", min_days, max_days)
                    if marketdata_options and len(marketdata_options) > 0:
                        logger.info(f"✓ Fetched {len(marketdata_options)} LEAPS options from MarketData with real Greeks")
                        return marketdata_options
                    else:
                        logger.warning("MarketData returned no options, falling back to yfinance")
                except Exception as e:
                    logger.warning(f"MarketData API failed: {e}, falling back to yfinance")
            else:
                logger.warning("MarketData API key not configured, falling back to yfinance")

        # Fallback: Use yfinance with calculated Black-Scholes Greeks

        logger.info("Fetching SPX options chain from yfinance (calculated Greeks)...")

        # Use SPY as proxy for SPX (more liquid options data)
        ticker = yf.Ticker("SPY")

        # Get current price
        hist = ticker.history(period="1d")
        if hist.empty:
            logger.warning("No price data available, using sample data")
            return _generate_sample_options(450.0)

        current_price = hist['Close'].iloc[-1]
        logger.info(f"SPY current price: ${current_price:.2f}")

        # Get available expiration dates
        expirations = ticker.options

        if not expirations:
            logger.warning("No options data available")
            return _generate_sample_options(current_price)

        # Filter for LEAPS expirations (6-24 months out)
        today = datetime.now()
        leaps_options = []

        for exp_date_str in expirations:
            exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d')
            days_to_exp = (exp_date - today).days

            if min_days <= days_to_exp <= max_days:
                try:
                    # Get options chain for this expiration
                    opt_chain = ticker.option_chain(exp_date_str)
                    calls = opt_chain.calls

                    # Process each call option
                    for _, row in calls.iterrows():
                        strike = row['strike']

                        # Calculate basic metrics
                        intrinsic = max(0, current_price - strike)
                        premium = (row['bid'] + row['ask']) / 2 if row['bid'] > 0 and row['ask'] > 0 else row['lastPrice']
                        extrinsic = premium - intrinsic
                        extrinsic_pct = (extrinsic / premium * 100) if premium > 0 else 0

                        # Time metrics
                        years_to_exp = days_to_exp / 365.25

                        # Calculate Greeks using Black-Scholes
                        iv = row.get('impliedVolatility', 0.20)  # Default to 20% if missing
                        original_iv = iv

                        # Sanity check: Deep ITM options have unreliable IV due to low volume
                        # For Greeks calculation, use more realistic effective IV
                        moneyness_pct = ((current_price - strike) / strike) * 100

                        if moneyness_pct > 50:  # Very deep ITM (>50%)
                            # These trade like stock - cap IV at 25% max
                            iv = min(iv, 0.25)
                            if iv != original_iv:
                                logger.debug(f"Deep ITM IV cap: Strike=${strike:.0f}, Moneyness={moneyness_pct:.1f}%, Original IV={original_iv*100:.1f}%, Capped to {iv*100:.1f}%")
                        elif moneyness_pct > 35:  # Deep ITM (35-50%)
                            # Cap at 30% for Greeks calculation
                            iv = min(iv, 0.30)
                            if iv != original_iv:
                                logger.debug(f"Deep ITM IV cap: Strike=${strike:.0f}, Moneyness={moneyness_pct:.1f}%, Original IV={original_iv*100:.1f}%, Capped to {iv*100:.1f}%")

                        greeks = BlackScholesGreeks.calculate_greeks(
                            S=current_price,
                            K=strike,
                            T=years_to_exp,
                            r=0.045,  # Current risk-free rate ~4.5%
                            sigma=iv,
                            option_type='call'
                        )

                        # Calculate IV Rank and Percentile
                        iv_rank, iv_percentile = calculate_iv_rank_percentile("SPY", iv)

                        option = {
                            'symbol': f"SPY{exp_date_str.replace('-', '')}C{int(strike*1000):08d}",
                            'strike': float(strike),
                            'expiration': exp_date_str,
                            'days_to_expiration': days_to_exp,
                            'years_to_expiration': round(years_to_exp, 2),
                            'current_price': float(current_price),
                            'premium': float(premium),
                            'bid': float(row['bid']),
                            'ask': float(row['ask']),
                            'bid_ask_spread': float(row['ask'] - row['bid']),
                            'bid_ask_spread_pct': float((row['ask'] - row['bid']) / premium * 100) if premium > 0 else 0,
                            'last_price': float(row['lastPrice']),
                            'volume': int(row['volume']) if pd.notna(row['volume']) else 0,
                            'open_interest': int(row['openInterest']) if pd.notna(row['openInterest']) else 0,
                            'implied_volatility': float(iv),
                            'intrinsic_value': float(intrinsic),
                            'extrinsic_value': float(extrinsic),
                            'extrinsic_pct': float(extrinsic_pct),
                            'strike_pct': float((strike / current_price - 1) * 100),  # % ITM/OTM
                            'iv_rank': float(iv_rank),
                            'iv_percentile': float(iv_percentile),
                            **greeks
                        }

                        leaps_options.append(option)

                except Exception as e:
                    logger.error(f"Error processing expiration {exp_date_str}: {e}")
                    continue

        logger.info(f"Found {len(leaps_options)} LEAPS options")

        # If no options found and not forced sample mode, return empty
        if not leaps_options and not use_sample:
            logger.warning("No LEAPS options found in live data")
            return []

        # If sample data explicitly requested (for testing only)
        if not leaps_options and use_sample:
            logger.warning("No LEAPS options found, generating sample data (testing mode)")
            return _generate_sample_options(current_price)

        return leaps_options

    except Exception as e:
        logger.error(f"Error fetching SPX options: {e}")
        # Only use sample data if explicitly requested
        if use_sample:
            try:
                ticker = yf.Ticker("SPY")
                current_price = ticker.history(period="1d")['Close'].iloc[-1]
            except:
                current_price = 450.0
            logger.warning("Using sample data due to error (testing mode)")
            return _generate_sample_options(current_price)
        else:
            # Return empty list on error - no fake data in production
            logger.error("Failed to fetch live options data, returning empty")
            return []


def _generate_sample_options(current_price: float) -> List[Dict]:
    """Generate sample LEAPS options for testing/demo."""
    logger.info("Generating sample LEAPS options data...")

    sample_options = []
    expirations = [180, 270, 365, 540, 730]  # 6, 9, 12, 18, 24 months
    strike_offsets = [-0.25, -0.20, -0.15, -0.10, -0.05, 0, 0.05, 0.10]  # % from current

    for days in expirations:
        exp_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        years = days / 365.25

        for offset in strike_offsets:
            strike = current_price * (1 + offset)
            intrinsic = max(0, current_price - strike)

            # Estimate premium and IV
            iv = 0.15 + abs(offset) * 0.1  # Higher IV for OTM
            greeks = BlackScholesGreeks.calculate_greeks(
                S=current_price,
                K=strike,
                T=years,
                r=0.045,
                sigma=iv
            )

            # Calculate IV rank and percentile (randomized for sample data)
            iv_rank = np.random.uniform(0.2, 0.8)
            iv_percentile = np.random.uniform(20, 80)

            # Simplified premium calculation
            premium = intrinsic + (current_price * iv * np.sqrt(years) * 0.4)
            extrinsic = premium - intrinsic

            option = {
                'symbol': f"SPY{exp_date.replace('-', '')}C{int(strike*1000):08d}",
                'strike': round(strike, 2),
                'expiration': exp_date,
                'days_to_expiration': days,
                'years_to_expiration': round(years, 2),
                'current_price': current_price,
                'premium': round(premium, 2),
                'bid': round(premium * 0.98, 2),
                'ask': round(premium * 1.02, 2),
                'bid_ask_spread': round(premium * 0.04, 2),
                'bid_ask_spread_pct': 4.0,
                'last_price': round(premium, 2),
                'volume': int(np.random.randint(100, 5000)),
                'open_interest': int(np.random.randint(1000, 50000)),
                'implied_volatility': round(iv, 4),
                'intrinsic_value': round(intrinsic, 2),
                'extrinsic_value': round(extrinsic, 2),
                'extrinsic_pct': round(extrinsic / premium * 100, 2) if premium > 0 else 0,
                'strike_pct': round(offset * 100, 2),
                'iv_rank': round(iv_rank, 3),
                'iv_percentile': round(iv_percentile, 1),
                **greeks
            }

            sample_options.append(option)

    return sample_options


def filter_leaps_by_strategy(
    options: List[Dict],
    strategy: str,
    delta_range: Tuple[float, float],
    extrinsic_max: float,
    vega_range: Optional[Tuple[float, float]] = None
) -> List[Dict]:
    """
    Filter LEAPS options based on strategy criteria.

    Args:
        options: List of option contracts
        strategy: Strategy name (ATM, MODERATE_ITM, DEEP_ITM)
        delta_range: (min_delta, max_delta) tuple
        extrinsic_max: Maximum extrinsic value percentage
        vega_range: Optional (min_vega, max_vega) tuple

    Returns:
        Filtered list of options matching criteria
    """
    filtered = []

    for opt in options:
        # Delta filter
        if not (delta_range[0] <= opt['delta'] <= delta_range[1]):
            continue

        # Extrinsic % filter
        if opt['extrinsic_pct'] > extrinsic_max:
            continue

        # Vega filter (if specified)
        if vega_range and not (vega_range[0] <= opt['vega'] <= vega_range[1]):
            continue

        # Liquidity filters
        if opt['volume'] < 10:  # Minimum daily volume
            continue

        if opt['open_interest'] < 100:  # Minimum open interest
            continue

        if opt['bid_ask_spread_pct'] > 5:  # Max 5% bid-ask spread
            continue

        # Calculate quality score and opportunity score
        opt['quality_score'] = _calculate_quality_score(opt, strategy)
        opt['opportunity_score'] = _calculate_opportunity_score(opt)

        filtered.append(opt)

    # Sort by quality score
    filtered.sort(key=lambda x: x['quality_score'], reverse=True)

    return filtered


def _calculate_quality_score(option: Dict, strategy: str) -> float:
    """
    Calculate quality score for an option (0-100).

    Factors:
    - Delta match to strategy
    - Liquidity (volume, OI)
    - Bid-ask spread
    - Extrinsic value
    """
    score = 100.0

    # Liquidity score (0-30 points)
    volume_score = min(option['volume'] / 1000 * 10, 15)
    oi_score = min(option['open_interest'] / 5000 * 10, 15)

    # Bid-ask spread penalty (0-20 points)
    spread_penalty = option['bid_ask_spread_pct'] * 4

    # Extrinsic value score (0-25 points) - lower is better for ITM strategies
    if strategy in ['MODERATE_ITM', 'DEEP_ITM']:
        extrinsic_score = max(0, 25 - option['extrinsic_pct'])
    else:  # ATM
        extrinsic_score = 15  # Neutral for ATM

    # Delta optimization score (0-25 points)
    if strategy == 'DEEP_ITM':
        delta_score = (option['delta'] - 0.85) * 100 if option['delta'] >= 0.85 else 0
    elif strategy == 'MODERATE_ITM':
        delta_score = 25 - abs(option['delta'] - 0.80) * 100
    else:  # ATM
        delta_score = 25 - abs(option['delta'] - 0.50) * 100

    score = volume_score + oi_score + extrinsic_score + delta_score - spread_penalty

    return max(0, min(100, score))


def _calculate_opportunity_score(option: Dict) -> float:
    """
    Calculate opportunity score (0-100) based on volatility value.

    BEST opportunities have:
    - Low vega (less volatility exposure)
    - Low IV rank (cheap volatility)
    - Low IV percentile (below average IV)

    Higher score = Better opportunity (cheap volatility)
    """
    score = 0.0

    # Vega score (0-35 points) - LOWER is better for deep ITM
    # Deep ITM target: 0.01-0.10, ATM accepts: 0.15-0.25
    vega = option.get('vega', 0.5)
    if vega <= 0.05:
        vega_score = 35  # Excellent - very low vega
    elif vega <= 0.10:
        vega_score = 30  # Good - low vega
    elif vega <= 0.15:
        vega_score = 20  # Acceptable - moderate vega
    elif vega <= 0.25:
        vega_score = 10  # Fair - higher vega (ATM range)
    else:
        vega_score = 0   # Poor - too high vega

    # IV Rank score (0-40 points) - LOWER is better (cheap volatility)
    # Green (< 0.30) = excellent, Yellow (0.30-0.60) = fair, Red (> 0.60) = avoid
    iv_rank = option.get('iv_rank', 0.5)
    if iv_rank < 0.20:
        iv_rank_score = 40  # Excellent - very cheap volatility
    elif iv_rank < 0.30:
        iv_rank_score = 35  # Good - cheap volatility (green zone)
    elif iv_rank < 0.50:
        iv_rank_score = 20  # Acceptable - fair volatility
    elif iv_rank < 0.70:
        iv_rank_score = 10  # Poor - expensive volatility (red zone)
    else:
        iv_rank_score = 0   # Avoid - very expensive volatility

    # IV Percentile score (0-25 points) - LOWER is better
    # < 30% = excellent, 30-50% = good, 50-70% = fair, > 70% = avoid
    iv_percentile = option.get('iv_percentile', 50.0)
    if iv_percentile < 20:
        iv_percentile_score = 25  # Excellent - very low IV
    elif iv_percentile < 30:
        iv_percentile_score = 20  # Good - low IV
    elif iv_percentile < 50:
        iv_percentile_score = 12  # Acceptable - moderate IV
    elif iv_percentile < 70:
        iv_percentile_score = 5   # Poor - high IV
    else:
        iv_percentile_score = 0   # Avoid - very high IV

    score = vega_score + iv_rank_score + iv_percentile_score

    return max(0, min(100, score))


def get_top_leaps_opportunities(
    strategy_name: str,
    delta_range: Tuple[float, float],
    extrinsic_max: float,
    vega_range: Optional[Tuple[float, float]] = None,
    top_n: int = 10
) -> Dict:
    """
    Get top N LEAPS opportunities for a given strategy.

    Returns:
        dict: {
            'current_price': SPY current price
            'total_options': Total options found
            'filtered_options': Options matching criteria
            'top_opportunities': Top N options by quality score
            'timestamp': Analysis timestamp
        }
    """
    # Fetch options
    all_options = fetch_spx_options()

    # Filter by strategy
    filtered = filter_leaps_by_strategy(
        all_options,
        strategy_name,
        delta_range,
        extrinsic_max,
        vega_range
    )

    return {
        'current_price': all_options[0]['current_price'] if all_options else 0,
        'total_options': len(all_options),
        'filtered_options': len(filtered),
        'top_opportunities': filtered[:top_n],
        'timestamp': datetime.now().isoformat()
    }


# Example usage
if __name__ == "__main__":
    print("Testing LEAPS Analyzer...")
    print("=" * 60)

    # Test options fetching
    options = fetch_spx_options()
    print(f"\nTotal LEAPS options found: {len(options)}")

    if options:
        print(f"\nSample option:")
        sample = options[0]
        for key, value in sample.items():
            print(f"  {key}: {value}")

        # Test filtering
        print("\n" + "=" * 60)
        print("Testing Deep ITM filter...")
        filtered = filter_leaps_by_strategy(
            options,
            'DEEP_ITM',
            delta_range=(0.85, 0.98),
            extrinsic_max=10
        )
        print(f"Found {len(filtered)} Deep ITM LEAPS")

        if filtered:
            print("\nTop 3 opportunities:")
            for i, opt in enumerate(filtered[:3], 1):
                print(f"\n{i}. Strike ${opt['strike']:.2f} | Delta {opt['delta']:.3f} | Premium ${opt['premium']:.2f}")
                print(f"   Extrinsic: {opt['extrinsic_pct']:.1f}% | Quality: {opt['quality_score']:.1f}/100")
