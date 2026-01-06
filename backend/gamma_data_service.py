#!/usr/bin/env python3
"""
Gamma Data Service v1.0
========================
Centralized service for gamma wall data with multi-method calculations.
Connects the scanner output to the frontend API.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
import logging

# Import the scanner
import sys
sys.path.insert(0, str(Path(__file__).parent))

from Restoring.enhanced_gamma_scanner_weekly import (
    GammaWallCalculator,
    process_symbol,
    get_market_regime,
    SYMBOLS,
    PUT_WALL_WEIGHTS,
    MAX_DISTANCE_BY_CATEGORY
)

logger = logging.getLogger(__name__)

# Cache file location
CACHE_DIR = Path(__file__).parent / 'cache'
GAMMA_CACHE_FILE = CACHE_DIR / 'gamma_walls_cache.json'

def ensure_cache_dir():
    """Ensure cache directory exists."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def load_cached_data() -> Optional[Dict]:
    """Load cached gamma data if available and fresh."""
    try:
        if GAMMA_CACHE_FILE.exists():
            with open(GAMMA_CACHE_FILE, 'r') as f:
                data = json.load(f)
                # Check if cache is less than 1 hour old
                cache_time = datetime.fromisoformat(data.get('timestamp', '2000-01-01'))
                age_hours = (datetime.now() - cache_time).total_seconds() / 3600
                if age_hours < 1:
                    logger.info(f"Using cached gamma data ({age_hours:.1f} hours old)")
                    return data
    except Exception as e:
        logger.warning(f"Failed to load cache: {e}")
    return None

def save_to_cache(data: Dict):
    """Save gamma data to cache."""
    try:
        ensure_cache_dir()
        with open(GAMMA_CACHE_FILE, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Saved gamma data to cache")
    except Exception as e:
        logger.error(f"Failed to save cache: {e}")

def scan_all_symbols(force_refresh: bool = False) -> Dict:
    """Scan all symbols and return comprehensive gamma data."""
    
    # Check cache first
    if not force_refresh:
        cached = load_cached_data()
        if cached:
            return cached
    
    logger.info("Running full gamma scan...")
    calculator = GammaWallCalculator()
    regime, vix = get_market_regime()
    
    results = {}
    
    for symbol in SYMBOLS:
        try:
            result = process_symbol(symbol, calculator)
            if result:
                # Transform to frontend-friendly format
                symbol_key = result.get('display_name', symbol).replace('^', '')
                
                results[symbol_key] = {
                    'symbol': symbol_key,
                    'current_price': result['current_price'],
                    'timestamp': result['timestamp'],
                    
                    # Put walls with all methods
                    'st_put_wall': result.get('st_put_wall', 0),
                    'lt_put_wall': result.get('lt_put_wall', 0),
                    'q_put_wall': result.get('q_put_wall', 0),
                    'wk_put_wall': result.get('wk_put_wall', 0),
                    
                    # Individual methods for ST
                    'st_put_wall_maxgex': result.get('st_put_wall_maxgex', 0),
                    'st_put_wall_centroid': result.get('st_put_wall_centroid', 0),
                    'st_put_wall_cumulative': result.get('st_put_wall_cumulative', 0),
                    
                    # Call walls
                    'st_call_wall': result.get('st_call_wall', 0),
                    'lt_call_wall': result.get('lt_call_wall', 0),
                    'q_call_wall': result.get('q_call_wall', 0),
                    
                    # Gamma flip
                    'gamma_flip': result.get('gamma_flip', result['current_price']),
                    
                    # SD levels
                    'lower_1sd': result.get('lower_1sd', 0),
                    'upper_1sd': result.get('upper_1sd', 0),
                    'lower_2sd': result.get('lower_2sd', 0),
                    'upper_2sd': result.get('upper_2sd', 0),
                    
                    # Metadata
                    'category': result.get('category', 'TECH'),
                    'put_wall_methods': result.get('put_wall_methods', {}),
                }
                
                logger.info(f"Processed {symbol_key}: ST Put = ${result.get('st_put_wall', 0):.0f}")
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
    
    # Build final response
    response = {
        'timestamp': datetime.now().isoformat(),
        'market_regime': regime,
        'vix': vix,
        'weights': PUT_WALL_WEIGHTS,
        'max_distances': MAX_DISTANCE_BY_CATEGORY,
        'symbols': results
    }
    
    # Save to cache
    save_to_cache(response)
    
    return response

def get_symbol_risk_distance(symbol: str) -> Optional[Dict]:
    """Get risk distance data for a single symbol."""
    data = scan_all_symbols()
    
    # Normalize symbol name
    symbol_clean = symbol.upper().replace('^', '')
    
    if symbol_clean not in data.get('symbols', {}):
        return None
    
    symbol_data = data['symbols'][symbol_clean]
    current_price = symbol_data['current_price']
    
    def calc_distance(level):
        if level and level > 0:
            return round(((current_price - level) / current_price) * 100, 2)
        return 0
    
    def get_direction(distance):
        return "ABOVE" if distance > 0 else "BELOW"
    
    # Build risk distance response
    return {
        'symbol': symbol_clean,
        'current_price': current_price,
        'timestamp': symbol_data['timestamp'],
        
        'levels': {
            'st_put': {
                'price': symbol_data['st_put_wall'],
                'distance_pct': calc_distance(symbol_data['st_put_wall']),
                'direction': get_direction(calc_distance(symbol_data['st_put_wall']))
            },
            'lt_put': {
                'price': symbol_data['lt_put_wall'],
                'distance_pct': calc_distance(symbol_data['lt_put_wall']),
                'direction': get_direction(calc_distance(symbol_data['lt_put_wall']))
            },
            'q_put': {
                'price': symbol_data['q_put_wall'],
                'distance_pct': calc_distance(symbol_data['q_put_wall']),
                'direction': get_direction(calc_distance(symbol_data['q_put_wall']))
            },
            'gamma_flip': {
                'price': symbol_data['gamma_flip'],
                'distance_pct': calc_distance(symbol_data['gamma_flip']),
                'direction': get_direction(calc_distance(symbol_data['gamma_flip']))
            }
        },
        
        # Individual methods for comparison
        'st_put_methods': {
            'max_gex': symbol_data.get('st_put_wall_maxgex', 0),
            'centroid': symbol_data.get('st_put_wall_centroid', 0),
            'cumulative': symbol_data.get('st_put_wall_cumulative', 0),
            'weighted_combo': symbol_data.get('st_put_wall', 0)
        }
    }

def refresh_and_get_all() -> Dict:
    """Force refresh and return all data."""
    return scan_all_symbols(force_refresh=True)

# CLI for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true', help='Force refresh cache')
    parser.add_argument('--symbol', type=str, help='Get data for specific symbol')
    args = parser.parse_args()
    
    if args.refresh:
        print("Forcing refresh...")
        data = refresh_and_get_all()
    else:
        data = scan_all_symbols()
    
    if args.symbol:
        risk_data = get_symbol_risk_distance(args.symbol)
        if risk_data:
            print(json.dumps(risk_data, indent=2))
        else:
            print(f"No data for {args.symbol}")
    else:
        # Print summary
        print(f"\nGamma Wall Data Summary")
        print(f"{'='*60}")
        print(f"Timestamp: {data['timestamp']}")
        print(f"Market Regime: {data['market_regime']} (VIX: {data['vix']:.1f})")
        print(f"Weights: {data['weights']}")
        print()
        
        for symbol, sdata in data.get('symbols', {}).items():
            price = sdata['current_price']
            st_put = sdata['st_put_wall']
            st_dist = ((price - st_put) / price) * 100 if st_put else 0
            
            print(f"{symbol:12} ${price:>8.2f} | ST Put: ${st_put:>8.0f} ({st_dist:+.1f}%)")
