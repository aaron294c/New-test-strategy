#!/usr/bin/env python3
"""
VIX Analysis Module for LEAPS Options Scanner

Provides VIX data fetching and LEAPS strategy determination based on
current volatility environment.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_vix_data() -> Dict:
    """
    Fetch current VIX level and 252-day historical data.

    Returns:
        dict: {
            "current": float - Current VIX level
            "percentile": int - Percentile rank (0-100) vs 252-day history
            "history": list - Last 252 days of VIX levels
            "timestamp": str - ISO format timestamp
        }

    Raises:
        Exception: If VIX data cannot be fetched
    """
    try:
        logger.info("Fetching VIX data from yfinance...")

        # Fetch VIX data (ticker: ^VIX)
        vix_ticker = yf.Ticker("^VIX")

        # Get 1 year of history to ensure we have 252 trading days
        vix_history = vix_ticker.history(period="1y")

        if vix_history.empty:
            raise ValueError("No VIX data returned from yfinance")

        # Extract close prices
        vix_values = vix_history['Close'].values
        current_vix = float(vix_values[-1])

        # Calculate percentile rank (what % of historical values are below current)
        percentile = int(np.sum(vix_values < current_vix) / len(vix_values) * 100)

        logger.info(f"VIX fetched: {current_vix:.2f} (P{percentile})")

        return {
            "current": round(current_vix, 2),
            "percentile": percentile,
            "history": [round(float(v), 2) for v in vix_values[-252:]],  # Last 252 days
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error fetching VIX data: {e}")
        # Return default values on error
        return {
            "current": 18.0,
            "percentile": 50,
            "history": [],
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


def determine_leaps_strategy(vix_level: float, vix_percentile: int) -> Dict:
    """
    Determine optimal LEAPS strategy based on VIX environment.

    Strategy Logic:
    - VIX < 15: ATM LEAPS (cheap vega, maximum leverage)
    - VIX 15-20: Moderate ITM (balanced approach)
    - VIX > 20: Deep ITM (vega protection essential)

    Args:
        vix_level: Current VIX level
        vix_percentile: VIX percentile rank (0-100)

    Returns:
        dict: {
            "strategy": str - Strategy name
            "delta_range": [float, float] - Recommended delta range
            "extrinsic_pct_max": int - Maximum extrinsic value %
            "strike_depth_pct": [int, int] - Strike depth % ITM range
            "rationale": str - Strategy explanation
            "vega_exposure": str - Vega risk assessment
        }
    """

    if vix_level < 15:
        # Low VIX environment: ATM LEAPS
        strategy = {
            "strategy": "ATM",
            "strategy_full": "At-The-Money LEAPS",
            "delta_range": [0.45, 0.60],
            "extrinsic_pct_max": 35,
            "strike_depth_pct": [-5, 5],  # ATM ±5%
            "vega_range": [0.18, 0.25],
            "rationale": (
                "Low VIX environment - vega is cheap and likely to expand. "
                "ATM options provide maximum leverage and benefit from IV expansion. "
                "Target delta 0.50-0.55 for optimal risk/reward."
            ),
            "vega_exposure": "HIGH - Vega works FOR you as IV expands",
            "key_filters": [
                "VIX Percentile < 30 (currently P{})".format(vix_percentile),
                "Delta: 0.50-0.55 ideal",
                "Vega: 0.18-0.25 (want exposure)",
                "Strike: 95-105% of spot price"
            ]
        }

    elif 15 <= vix_level <= 20:
        # Moderate VIX: Moderate ITM
        strategy = {
            "strategy": "MODERATE_ITM",
            "strategy_full": "Moderately In-The-Money LEAPS",
            "delta_range": [0.75, 0.85],
            "extrinsic_pct_max": 20,
            "strike_depth_pct": [10, 20],  # 10-20% ITM
            "vega_range": [0.08, 0.15],
            "rationale": (
                "Moderate VIX environment - balanced approach. "
                "Moderately ITM options reduce vega exposure while maintaining leverage. "
                "Target delta 0.75-0.80 for good directional exposure with protection."
            ),
            "vega_exposure": "MODERATE - Balanced vega/theta exposure",
            "key_filters": [
                "Delta: 0.75-0.80 ideal",
                "Extrinsic %: 10-20%",
                "Vega: 0.08-0.15",
                "Strike: 10-20% ITM"
            ]
        }

    else:  # vix_level > 20
        # High VIX: Deep ITM for vega protection
        strategy = {
            "strategy": "DEEP_ITM",
            "strategy_full": "Deep In-The-Money LEAPS",
            "delta_range": [0.85, 0.98],
            "extrinsic_pct_max": 10,
            "strike_depth_pct": [15, 30],  # 15-30% ITM
            "vega_range": [0.02, 0.08],
            "rationale": (
                "High VIX environment - vega protection essential. "
                "Deep ITM options minimize vega exposure and act like stock. "
                "Target delta >0.90 and extrinsic <10% to avoid IV crush."
            ),
            "vega_exposure": "LOW - Vega-proof, immune to IV crush",
            "key_filters": [
                "Delta: >0.90 ideal (0.85-0.98)",
                "Extrinsic %: <10% (ideally <8%)",
                "Vega: <0.08 (ideally <0.05)",
                "Strike: 15-25% ITM minimum"
            ]
        }

    # Add VIX context to all strategies
    strategy["vix_context"] = _get_vix_context(vix_level, vix_percentile)

    return strategy


def _get_vix_context(vix_level: float, vix_percentile: int) -> Dict:
    """
    Provide contextual information about current VIX level.

    Args:
        vix_level: Current VIX level
        vix_percentile: VIX percentile rank

    Returns:
        dict: VIX context information
    """
    if vix_level < 12:
        environment = "EXTREMELY_LOW"
        description = "Extreme complacency - rare buying opportunity for vega"
    elif vix_level < 15:
        environment = "LOW"
        description = "Low volatility - favorable for ATM LEAPS"
    elif vix_level < 20:
        environment = "NORMAL"
        description = "Normal volatility - balanced approach recommended"
    elif vix_level < 30:
        environment = "ELEVATED"
        description = "Elevated volatility - protect against vega"
    else:
        environment = "HIGH"
        description = "High volatility - deep ITM essential"

    return {
        "environment": environment,
        "description": description,
        "percentile_context": _get_percentile_context(vix_percentile)
    }


def _get_percentile_context(percentile: int) -> str:
    """Get percentile rank context."""
    if percentile < 20:
        return "Bottom quintile - historically cheap vega"
    elif percentile < 40:
        return "Below median - relatively cheap vega"
    elif percentile < 60:
        return "Near median - neutral volatility regime"
    elif percentile < 80:
        return "Above median - elevated volatility"
    else:
        return "Top quintile - expensive vega, protect yourself"


# Example usage for testing
if __name__ == "__main__":
    print("Testing VIX Analyzer...")
    print("=" * 60)

    # Fetch VIX data
    vix_data = fetch_vix_data()
    print(f"\nCurrent VIX: {vix_data['current']}")
    print(f"Percentile: P{vix_data['percentile']}")
    print(f"Timestamp: {vix_data['timestamp']}")

    # Determine strategy
    strategy = determine_leaps_strategy(vix_data['current'], vix_data['percentile'])
    print(f"\nRecommended Strategy: {strategy['strategy_full']}")
    print(f"Delta Range: {strategy['delta_range']}")
    print(f"Max Extrinsic %: {strategy['extrinsic_pct_max']}%")
    print(f"Strike Depth: {strategy['strike_depth_pct']}% ITM")
    print(f"\nRationale: {strategy['rationale']}")
    print(f"\nVega Exposure: {strategy['vega_exposure']}")
    print("\nKey Filters:")
    for filter_rule in strategy['key_filters']:
        print(f"  - {filter_rule}")
