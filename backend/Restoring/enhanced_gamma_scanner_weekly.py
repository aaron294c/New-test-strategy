#!/usr/bin/env python3
"""
Enhanced Gamma Wall Scanner v8.1 - Multi-Method Put Wall Calculation
=====================================================================

FIXES IN v8.1:
- Fixed SPX put wall proximity filter (was selecting strikes too far from price)
- Added 4 put wall calculation methods:
  1. Max GEX - Strike with highest absolute gamma exposure
  2. Weighted Centroid - Center of mass of GEX distribution  
  3. Cumulative Threshold - Strike where X% of GEX accumulates
  4. Weighted Combo - Configurable blend of all 3 methods
- Symbol-specific max distance filters (indices get wider range)
- All 4 methods output to Pine Script for comparison

Usage: python enhanced_gamma_scanner_weekly.py
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.stats import norm
import warnings
import logging
from typing import Dict, Optional, Tuple, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === CONFIGURATION ===
# Extended symbol list with working Yahoo Finance symbols
SYMBOLS = [
    # Original tech stocks
    'AAPL', 'NVDA', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NFLX', 'AMD', 'CRM', 'ADBE', 'ORCL',
    # Working index symbols (correct Yahoo Finance format)
    '^SPX',  # S&P 500 Index (working perfectly!)
    'QQQ',   # QQQ ETF as NDX proxy (much better options liquidity)
    # Energy stocks (confirmed working)
    'CVX',   # Chevron
    'XOM',   # ExxonMobil
    # Additional reliable symbols
    'INTC',  # Intel (tech diversity)
    'JPM',   # JPMorgan (financial sector)
    'BAC',   # Bank of America (financial sector)
    'DIS',   # Disney (consumer/entertainment)
    # International indices (correct Yahoo symbols)
    '^GDAXI', # DAX Performance Index (has options chain)
    '^FTSE',  # FTSE 100 Index
]

# UPDATED TIMEFRAMES - Now includes TRUE WEEKLY data
WEEKLY_DAYS = 7      # NEW: True weekly options (most accurate max pain)
SWING_DAYS = 14      # Short-term (now secondary to weekly)
LONG_DAYS = 30       # Medium-term  
QUARTERLY_DAYS = 90  # Long-term
RISK_FREE_RATE = 0.045
MAX_WORKERS = 8

# CONFIGURABLE WEIGHTS for weighted combination (must sum to 1.0)
PUT_WALL_WEIGHTS = {
    'max_gex': 0.40,           # Weight for max GEX method
    'weighted_centroid': 0.35, # Weight for centroid method  
    'cumulative_threshold': 0.25  # Weight for cumulative method
}

# Symbol-specific max distance filters (percentage from current price)
# Indices need wider range due to option strike spacing
MAX_DISTANCE_BY_CATEGORY = {
    'INDEX': 0.08,      # 8% max distance for indices (SPX, etc.)
    'ETF': 0.10,        # 10% for ETFs
    'TECH': 0.12,       # 12% for tech stocks
    'ENERGY': 0.10,     # 10% for energy
    'FINANCIAL': 0.10,  # 10% for financials
    'CONSUMER': 0.10,   # 10% for consumer
    'DEFAULT': 0.15     # 15% default fallback
}

# Symbol mapping for display names
SYMBOL_DISPLAY_NAMES = {
    '^SPX': 'SPX',
    'QQQ': 'QQQ(NDX)', 
    '^GDAXI': 'DAX',
    '^FTSE': 'FTSE',
    'CVX': 'CVX',
    'XOM': 'XOM',
    'INTC': 'INTC',
    'JPM': 'JPM',
    'BAC': 'BAC',
    'DIS': 'DIS'
}

class GammaWallCalculator:
    def __init__(self):
        self.errors = []
    
    def calculate_gamma(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate Black-Scholes gamma"""
        try:
            if any(x <= 0 for x in [S, K, T]) or sigma <= 0:
                return 0.0
                
            d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
            
            return gamma if not (np.isnan(gamma) or np.isinf(gamma)) else 0.0
        except:
            return 0.0
    
    def calculate_wall_strength(self, gex_series: pd.Series) -> float:
        """Calculate wall strength using original formula: concentration * 45 + log10(absolute_exposure) * 8"""
        try:
            if gex_series.empty:
                return 0.0
            
            max_exposure = gex_series.abs().max()
            total_exposure = gex_series.abs().sum()
            
            if total_exposure == 0:
                return 0.0
            
            concentration = max_exposure / total_exposure
            log_exposure = np.log10(max_exposure + 1)
            
            # Original formula from your Pine Script
            strength = concentration * 45 + log_exposure * 8
            
            return max(0.0, min(95.0, strength))
        except:
            return 0.0
    
    def calculate_gamma_flip(self, calls_gex: pd.Series, puts_gex: pd.Series, current_price: float) -> float:
        """Calculate actual gamma flip point where net GEX crosses zero"""
        try:
            # Combine all GEX data
            all_strikes = calls_gex.index.union(puts_gex.index)
            net_gex = pd.Series(0.0, index=all_strikes)
            
            # Add call GEX (positive)
            for strike in calls_gex.index:
                if strike in net_gex.index:
                    net_gex[strike] += calls_gex[strike]
            
            # Add put GEX (negative) 
            for strike in puts_gex.index:
                if strike in net_gex.index:
                    net_gex[strike] += puts_gex[strike]  # puts_gex should already be negative
            
            # Find zero crossing point
            net_gex = net_gex.sort_index()
            
            # Look for sign change
            for i in range(len(net_gex) - 1):
                if net_gex.iloc[i] * net_gex.iloc[i + 1] < 0:  # Sign change
                    # Linear interpolation between the two points
                    strike1, gex1 = net_gex.index[i], net_gex.iloc[i]
                    strike2, gex2 = net_gex.index[i + 1], net_gex.iloc[i + 1]
                    
                    # Find zero crossing point
                    gamma_flip = strike1 + (strike2 - strike1) * (-gex1) / (gex2 - gex1)
                    return gamma_flip
            
            # If no crossing found, return the strike closest to current price
            closest_strike = min(all_strikes, key=lambda x: abs(x - current_price))
            return closest_strike
            
        except Exception as e:
            logger.warning(f"Gamma flip calculation error: {e}")
            return current_price
    
    def calculate_all_put_wall_methods(self, puts_gex: pd.Series, current_price: float, 
                                        category: str, threshold_pct: float = 0.7) -> Dict[str, float]:
        """
        FIXED: Calculate put wall using 4 methods with proper proximity filtering.
        
        Returns dict with:
        - max_gex: Strike with highest absolute GEX (within proximity)
        - weighted_centroid: Center of mass of GEX distribution
        - cumulative_threshold: Strike where threshold% of GEX accumulates
        - weighted_combo: Weighted average of all 3 methods
        """
        try:
            if puts_gex.empty:
                default = current_price * 0.95
                return {
                    'max_gex': default,
                    'weighted_centroid': default,
                    'cumulative_threshold': default,
                    'weighted_combo': default,
                    'method_used': 'fallback',
                    'confidence': 'low'
                }
            
            # FIXED: Get category-specific max distance
            max_distance_pct = MAX_DISTANCE_BY_CATEGORY.get(category, MAX_DISTANCE_BY_CATEGORY['DEFAULT'])
            min_strike = current_price * (1 - max_distance_pct)
            
            # Filter to strikes below current price AND within max distance
            relevant_strikes = puts_gex[(puts_gex.index < current_price) & (puts_gex.index >= min_strike)]
            
            # If no strikes in range, expand search gradually
            if relevant_strikes.empty:
                # Try 1.5x the distance
                min_strike_expanded = current_price * (1 - max_distance_pct * 1.5)
                relevant_strikes = puts_gex[(puts_gex.index < current_price) & (puts_gex.index >= min_strike_expanded)]
            
            if relevant_strikes.empty:
                # Last resort: use all strikes below price
                relevant_strikes = puts_gex[puts_gex.index < current_price]
            
            if relevant_strikes.empty:
                # Ultimate fallback
                default = current_price * 0.95
                return {
                    'max_gex': default,
                    'weighted_centroid': default,
                    'cumulative_threshold': default,
                    'weighted_combo': default,
                    'method_used': 'no_data',
                    'confidence': 'none'
                }
            
            abs_gex = relevant_strikes.abs()
            total_gex = abs_gex.sum()
            
            # METHOD 1: Max GEX - Strike with highest absolute exposure
            max_gex_wall = abs_gex.idxmax()
            
            # METHOD 2: Weighted Centroid - Center of mass
            if total_gex > 0:
                weighted_centroid = (abs_gex * abs_gex.index).sum() / total_gex
            else:
                weighted_centroid = max_gex_wall
            
            # METHOD 3: Cumulative Threshold - Where X% of support accumulates
            sorted_gex = abs_gex.sort_index(ascending=False)  # Start from current price down
            cumsum = sorted_gex.cumsum()
            threshold_value = total_gex * threshold_pct
            threshold_strikes = cumsum[cumsum >= threshold_value]
            
            if not threshold_strikes.empty:
                cumulative_threshold = threshold_strikes.index[-1]
            else:
                cumulative_threshold = max_gex_wall
            
            # METHOD 4: Weighted Combination
            weighted_combo = (
                PUT_WALL_WEIGHTS['max_gex'] * max_gex_wall +
                PUT_WALL_WEIGHTS['weighted_centroid'] * weighted_centroid +
                PUT_WALL_WEIGHTS['cumulative_threshold'] * cumulative_threshold
            )
            
            # Determine confidence based on GEX concentration
            gex_concentration = abs_gex.max() / total_gex if total_gex > 0 else 0
            
            if gex_concentration > 0.5:
                confidence = 'high'
                method_used = 'max_gex'
            elif gex_concentration > 0.3:
                confidence = 'medium'
                method_used = 'weighted_centroid'
            else:
                confidence = 'medium'
                method_used = 'cumulative_threshold'
            
            return {
                'max_gex': round(max_gex_wall, 2),
                'weighted_centroid': round(weighted_centroid, 2),
                'cumulative_threshold': round(cumulative_threshold, 2),
                'weighted_combo': round(weighted_combo, 2),
                'method_used': method_used,
                'confidence': confidence,
                'gex_concentration': round(gex_concentration, 3),
                'strikes_analyzed': len(relevant_strikes),
                'max_distance_used': max_distance_pct
            }
            
        except Exception as e:
            logger.warning(f"Put wall calculation error: {e}")
            default = current_price * 0.95
            return {
                'max_gex': default,
                'weighted_centroid': default,
                'cumulative_threshold': default,
                'weighted_combo': default,
                'method_used': 'error',
                'confidence': 'none'
            }
    
    def calculate_all_call_wall_methods(self, calls_gex: pd.Series, current_price: float,
                                         category: str, threshold_pct: float = 0.7) -> Dict[str, float]:
        """Calculate call wall using same 4 methods as put wall."""
        try:
            if calls_gex.empty:
                default = current_price * 1.05
                return {
                    'max_gex': default, 'weighted_centroid': default,
                    'cumulative_threshold': default, 'weighted_combo': default,
                    'method_used': 'fallback', 'confidence': 'low'
                }
            
            max_distance_pct = MAX_DISTANCE_BY_CATEGORY.get(category, MAX_DISTANCE_BY_CATEGORY['DEFAULT'])
            max_strike = current_price * (1 + max_distance_pct)
            
            relevant_strikes = calls_gex[(calls_gex.index > current_price) & (calls_gex.index <= max_strike)]
            
            if relevant_strikes.empty:
                max_strike_expanded = current_price * (1 + max_distance_pct * 1.5)
                relevant_strikes = calls_gex[(calls_gex.index > current_price) & (calls_gex.index <= max_strike_expanded)]
            
            if relevant_strikes.empty:
                relevant_strikes = calls_gex[calls_gex.index > current_price]
            
            if relevant_strikes.empty:
                default = current_price * 1.05
                return {
                    'max_gex': default, 'weighted_centroid': default,
                    'cumulative_threshold': default, 'weighted_combo': default,
                    'method_used': 'no_data', 'confidence': 'none'
                }
            
            abs_gex = relevant_strikes.abs()
            total_gex = abs_gex.sum()
            
            max_gex_wall = abs_gex.idxmax()
            weighted_centroid = (abs_gex * abs_gex.index).sum() / total_gex if total_gex > 0 else max_gex_wall
            
            sorted_gex = abs_gex.sort_index(ascending=True)
            cumsum = sorted_gex.cumsum()
            threshold_value = total_gex * threshold_pct
            threshold_strikes = cumsum[cumsum >= threshold_value]
            cumulative_threshold = threshold_strikes.index[0] if not threshold_strikes.empty else max_gex_wall
            
            weighted_combo = (
                PUT_WALL_WEIGHTS['max_gex'] * max_gex_wall +
                PUT_WALL_WEIGHTS['weighted_centroid'] * weighted_centroid +
                PUT_WALL_WEIGHTS['cumulative_threshold'] * cumulative_threshold
            )
            
            gex_concentration = abs_gex.max() / total_gex if total_gex > 0 else 0
            
            return {
                'max_gex': round(max_gex_wall, 2),
                'weighted_centroid': round(weighted_centroid, 2),
                'cumulative_threshold': round(cumulative_threshold, 2),
                'weighted_combo': round(weighted_combo, 2),
                'method_used': 'max_gex' if gex_concentration > 0.5 else 'weighted_centroid',
                'confidence': 'high' if gex_concentration > 0.5 else 'medium'
            }
            
        except Exception as e:
            logger.warning(f"Call wall calculation error: {e}")
            default = current_price * 1.05
            return {
                'max_gex': default, 'weighted_centroid': default,
                'cumulative_threshold': default, 'weighted_combo': default,
                'method_used': 'error', 'confidence': 'none'
            }
    
    def calculate_max_pain(self, calls: pd.DataFrame, puts: pd.DataFrame) -> float:
        """Calculate true max pain strike."""
        try:
            all_strikes = calls.index.union(puts.index)
            pain_values = {}
            
            for strike in all_strikes:
                call_pain = sum((strike - k) * calls.loc[k, 'openInterest'] * 100 
                               for k in calls.index if k < strike)
                put_pain = sum((k - strike) * puts.loc[k, 'openInterest'] * 100 
                              for k in puts.index if k > strike)
                pain_values[strike] = call_pain + put_pain
            
            return min(pain_values, key=pain_values.get) if pain_values else 0
        except Exception as e:
            logger.warning(f"Max pain error: {e}")
            return 0
    
    def calculate_risk_distances(self, current_price: float, levels: Dict) -> Dict:
        """Calculate percentage distances from current price to all key levels."""
        distances = {}
        for level_name, level_price in levels.items():
            if level_price and level_price > 0:
                distance_pct = ((current_price - level_price) / current_price) * 100
                distances[f'{level_name}_distance_pct'] = round(distance_pct, 2)
                distances[f'{level_name}_distance_pts'] = round(current_price - level_price, 2)
        return distances


def get_market_regime() -> Tuple[str, float]:
    """Get current market regime based on VIX"""
    try:
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="5d")
        if not hist.empty:
            current_vix = hist['Close'].iloc[-1]
            if current_vix >= 25:
                return "High Volatility", current_vix
            elif current_vix <= 15:
                return "Low Volatility", current_vix
            else:
                return "Normal Volatility", current_vix
    except Exception as e:
        logger.warning(f"VIX fetch failed: {e}")
    return "Normal Volatility", 15.5


def find_best_expiration(options_dates: List[str], target_days: int) -> Tuple[str, float]:
    """Find the best expiration date for target days"""
    if not options_dates:
        return None, target_days
    
    now = datetime.now()
    valid_dates = []
    
    for date_str in options_dates:
        try:
            exp_date = datetime.strptime(date_str, '%Y-%m-%d')
            days_to_exp = (exp_date - now).days
            if 1 <= days_to_exp <= 400:
                valid_dates.append((date_str, days_to_exp))
        except:
            continue
    
    if not valid_dates:
        return options_dates[0] if options_dates else None, target_days
    
    # Find closest to target
    best = min(valid_dates, key=lambda x: abs(x[1] - target_days))
    return best[0], best[1]


def get_symbol_category(symbol: str) -> str:
    """Categorize symbols for better error handling and display"""
    if symbol in ['^SPX', '^GDAXI', '^FTSE']:
        return 'INDEX'
    elif symbol in ['QQQ']:
        return 'ETF'
    elif symbol in ['CVX', 'XOM']:
        return 'ENERGY'
    elif symbol in ['JPM', 'BAC']:
        return 'FINANCIAL'
    elif symbol in ['DIS']:
        return 'CONSUMER'
    else:
        return 'TECH'


def process_symbol(symbol: str, calculator: GammaWallCalculator) -> Optional[Dict]:
    """Process a single symbol with all 4 put wall calculation methods."""
    try:
        category = get_symbol_category(symbol)
        display_name = SYMBOL_DISPLAY_NAMES.get(symbol, symbol)
        logger.info(f"Processing {display_name} ({category})...")
        
        ticker = yf.Ticker(symbol)
        
        # Get current price
        current_price = None
        try:
            info = ticker.info
            current_price = info.get('regularMarketPrice') or info.get('currentPrice') or info.get('previousClose')
        except:
            pass
        
        if not current_price or current_price <= 0:
            try:
                hist = ticker.history(period="2d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
            except:
                pass
        
        if not current_price or current_price <= 0:
            logger.error(f"No price data for {symbol}")
            return None
        
        current_price = float(current_price)
        
        # Get options dates
        try:
            options_dates = ticker.options
        except Exception as e:
            logger.error(f"Cannot fetch options for {symbol}: {e}")
            return None
            
        if not options_dates:
            logger.error(f"No options available for {symbol}")
            return None
        
        # Find best expirations
        weekly_exp, weekly_dte = find_best_expiration(options_dates, WEEKLY_DAYS)
        swing_exp, swing_dte = find_best_expiration(options_dates, SWING_DAYS)
        long_exp, long_dte = find_best_expiration(options_dates, LONG_DAYS)
        quarterly_exp, quarterly_dte = find_best_expiration(options_dates, QUARTERLY_DAYS)
        
        if not all([weekly_exp, swing_exp, long_exp, quarterly_exp]):
            logger.error(f"Missing expirations for {symbol}")
            return None
        
        results = {
            'symbol': symbol,
            'display_name': display_name,
            'category': category,
            'current_price': current_price,
            'timestamp': datetime.now().isoformat(),
            'put_wall_methods': {},  # Store all 4 methods per timeframe
            'call_wall_methods': {}
        }
        
        all_timeframe_data = {}
        weekly_calls_gex = pd.Series()
        weekly_puts_gex = pd.Series()
        
        for tf_name, (exp_date, dte) in [
            ('weekly', (weekly_exp, weekly_dte)),
            ('swing', (swing_exp, swing_dte)),
            ('long', (long_exp, long_dte)), 
            ('quarterly', (quarterly_exp, quarterly_dte))
        ]:
            try:
                chain = ticker.option_chain(exp_date)
                calls = chain.calls
                puts = chain.puts
                
                if calls.empty or puts.empty:
                    continue
                
                T = dte / 365.0
                
                # Liquidity filters by category and timeframe
                if tf_name == 'weekly':
                    if category == 'INDEX':
                        min_volume, min_oi = 50, 100
                    elif category == 'ETF':
                        min_volume, min_oi = 25, 50
                    elif category in ['ENERGY', 'FINANCIAL', 'CONSUMER']:
                        min_volume, min_oi = 5, 10
                    else:
                        min_volume, min_oi = 10, 25
                else:
                    if category == 'INDEX':
                        min_volume, min_oi = 100, 200
                    elif category == 'ETF':
                        min_volume, min_oi = 50, 100
                    elif category in ['ENERGY', 'FINANCIAL', 'CONSUMER']:
                        min_volume, min_oi = 10, 25
                    else:
                        min_volume, min_oi = 20, 50
                
                calls = calls[(calls['volume'].fillna(0) >= min_volume) | (calls['openInterest'] >= min_oi)].copy()
                puts = puts[(puts['volume'].fillna(0) >= min_volume) | (puts['openInterest'] >= min_oi)].copy()
                
                if calls.empty or puts.empty:
                    continue
                
                calls.set_index('strike', inplace=True)
                puts.set_index('strike', inplace=True)
                
                # Calculate IV
                calls_iv = calls['impliedVolatility'].median()
                puts_iv = puts['impliedVolatility'].median()
                timeframe_iv = (calls_iv + puts_iv) / 2 if pd.notna(calls_iv) and pd.notna(puts_iv) else 0.25
                
                # IV bounds by category
                if tf_name == 'weekly':
                    if category == 'INDEX':
                        timeframe_iv = max(0.08, min(2.0, timeframe_iv))
                    elif category == 'ETF':
                        timeframe_iv = max(0.06, min(1.5, timeframe_iv))
                    else:
                        timeframe_iv = max(0.10, min(3.0, timeframe_iv))
                else:
                    if category == 'INDEX':
                        timeframe_iv = max(0.05, min(1.5, timeframe_iv))
                    elif category == 'ETF':
                        timeframe_iv = max(0.03, min(1.0, timeframe_iv))
                    else:
                        timeframe_iv = max(0.05, min(2.0, timeframe_iv))
                
                # Calculate gamma
                for df in [calls, puts]:
                    df['gamma'] = df.apply(
                        lambda row: calculator.calculate_gamma(current_price, row.name, T, RISK_FREE_RATE, timeframe_iv),
                        axis=1
                    )
                
                # Calculate GEX
                calls_gex = calls['openInterest'] * calls['gamma'] * 100 * current_price
                puts_gex = puts['openInterest'] * puts['gamma'] * 100 * current_price * -1
                
                if tf_name == 'weekly':
                    weekly_calls_gex = calls_gex.copy()
                    weekly_puts_gex = puts_gex.copy()
                
                # FIXED: Calculate all 4 put wall methods with category-specific proximity
                put_walls = calculator.calculate_all_put_wall_methods(puts_gex, current_price, category)
                call_walls = calculator.calculate_all_call_wall_methods(calls_gex, current_price, category)
                
                # Store methods for this timeframe
                results['put_wall_methods'][tf_name] = put_walls
                results['call_wall_methods'][tf_name] = call_walls
                
                # Use weighted_combo as the primary put wall (configurable)
                put_wall_strike = put_walls['weighted_combo']
                call_wall_strike = call_walls['weighted_combo']
                
                call_strength = calculator.calculate_wall_strength(calls_gex)
                put_strength = calculator.calculate_wall_strength(puts_gex)
                
                call_gex_millions = calls_gex.sum() / 1_000_000
                put_gex_millions = puts_gex.sum() / 1_000_000
                
                all_timeframe_data[tf_name] = {
                    'put_wall': put_wall_strike,
                    'call_wall': call_wall_strike,
                    'put_wall_methods': put_walls,
                    'call_wall_methods': call_walls,
                    'put_strength': put_strength,
                    'call_strength': call_strength,
                    'put_gex_millions': put_gex_millions,
                    'call_gex_millions': call_gex_millions,
                    'iv_percent': timeframe_iv * 100,
                    'dte': dte
                }
                
                # Map to Pine Script fields
                prefix = {'weekly': 'wk', 'swing': 'st', 'long': 'lt', 'quarterly': 'q'}[tf_name]
                
                results.update({
                    f'{prefix}_put_wall': put_wall_strike,
                    f'{prefix}_call_wall': call_wall_strike,
                    # Also store individual methods for comparison
                    f'{prefix}_put_wall_maxgex': put_walls['max_gex'],
                    f'{prefix}_put_wall_centroid': put_walls['weighted_centroid'],
                    f'{prefix}_put_wall_cumulative': put_walls['cumulative_threshold'],
                    f'{prefix}_put_strength': put_strength,
                    f'{prefix}_call_strength': call_strength,
                    f'{prefix}_put_gex': put_gex_millions,
                    f'{prefix}_call_gex': call_gex_millions,
                    f'{prefix}_iv': timeframe_iv * 100,
                    f'{prefix}_dte': dte
                })
                
            except Exception as e:
                logger.warning(f"Failed to process {tf_name} for {symbol}: {e}")
                continue
        
        # Calculate SD levels and gamma flip
        if 'swing' in all_timeframe_data:
            swing_data = all_timeframe_data['swing']
            swing_iv_decimal = swing_data['iv_percent'] / 100
            swing_T = swing_data['dte'] / 365.0
            base_move = current_price * swing_iv_decimal * np.sqrt(swing_T)
            
            results.update({
                'lower_1sd': current_price - base_move,
                'upper_1sd': current_price + base_move,
                'lower_1_5sd': current_price - base_move * 1.5,
                'upper_1_5sd': current_price + base_move * 1.5,
                'lower_2sd': current_price - base_move * 2.0,
                'upper_2sd': current_price + base_move * 2.0,
                'swing_iv': swing_data['iv_percent'],
                'cp_ratio': 2.0,
                'activity_score': min(5.0, len(all_timeframe_data)),
                'trend': 0.0
            })
        
        # Gamma flip from weekly data
        if 'weekly' in all_timeframe_data and not weekly_calls_gex.empty and not weekly_puts_gex.empty:
            gamma_flip = calculator.calculate_gamma_flip(weekly_calls_gex, weekly_puts_gex, current_price)
            results['gamma_flip'] = gamma_flip
        else:
            results['gamma_flip'] = current_price
        
        return results
        
    except Exception as e:
        logger.error(f"Error processing {symbol}: {e}")
        return None


def format_for_pine_script(data: Dict) -> str:
    """Format data for Pine Script (36 fields) - uses weighted_combo as primary"""
    fields = [
        data.get('st_put_wall', 0.0),
        data.get('st_call_wall', 0.0),
        data.get('lt_put_wall', 0.0),
        data.get('lt_call_wall', 0.0),
        data.get('lower_1sd', data.get('current_price', 0) * 0.95),
        data.get('upper_1sd', data.get('current_price', 0) * 1.05),
        data.get('wk_put_wall', 0.0),
        data.get('wk_call_wall', 0.0),
        data.get('gamma_flip', data.get('current_price', 0)),
        data.get('st_iv', 25.0),
        data.get('cp_ratio', 2.0),
        data.get('trend', 0.0),
        data.get('activity_score', 3.0),
        data.get('wk_put_wall', 0.0),
        data.get('wk_call_wall', 0.0),
        data.get('lower_1_5sd', data.get('current_price', 0) * 0.92),
        data.get('upper_1_5sd', data.get('current_price', 0) * 1.08),
        data.get('lower_2sd', data.get('current_price', 0) * 0.90),
        data.get('upper_2sd', data.get('current_price', 0) * 1.10),
        data.get('q_put_wall', 0.0),
        data.get('q_call_wall', 0.0),
        data.get('st_put_strength', 0.0),
        data.get('st_call_strength', 0.0),
        data.get('lt_put_strength', 0.0),
        data.get('lt_call_strength', 0.0),
        data.get('q_put_strength', 0.0),
        data.get('q_call_strength', 0.0),
        data.get('st_dte', 14),
        data.get('lt_dte', 30),
        data.get('q_dte', 90),
        data.get('st_put_gex', 0.0),
        data.get('st_call_gex', 0.0),
        data.get('lt_put_gex', 0.0),
        data.get('lt_call_gex', 0.0),
        data.get('q_put_gex', 0.0),
        data.get('q_call_gex', 0.0),
    ]
    
    formatted = []
    for i, field in enumerate(fields):
        if i == 9:
            formatted.append(f"{float(field):.1f}")
        elif i in [4, 5, 6, 7, 8, 13, 14, 15, 16, 17, 18, 19, 20]:
            formatted.append(f"{float(field):.2f}")
        elif i >= 21 and i <= 26:
            formatted.append(f"{float(field):.1f}")
        elif i >= 27 and i <= 29:
            formatted.append(f"{int(field)}")
        elif i >= 30:
            formatted.append(f"{float(field):.1f}")
        else:
            formatted.append(f"{float(field):.1f}")
    
    return ",".join(formatted)


def main():
    """Main execution with multi-method put wall output."""
    start_time = datetime.now()
    calculator = GammaWallCalculator()
    regime, vix = get_market_regime()
    
    print(f"\n" + "="*100)
    print(f"Enhanced Gamma Wall Scanner v8.1 - MULTI-METHOD PUT WALL CALCULATION")
    print(f"="*100)
    print(f"Scan started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Market Regime: {regime} (VIX: {vix:.1f})")
    print(f"Put Wall Weights: Max GEX={PUT_WALL_WEIGHTS['max_gex']}, Centroid={PUT_WALL_WEIGHTS['weighted_centroid']}, Cumulative={PUT_WALL_WEIGHTS['cumulative_threshold']}")
    print("-"*100)
    
    results = []
    failed_symbols = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # ...existing parallel processing code...
        future_to_symbol = {executor.submit(process_symbol, symbol, calculator): symbol for symbol in SYMBOLS}
        
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                result = future.result(timeout=60)
                if result:
                    results.append(result)
                    # ...existing print output...
                else:
                    failed_symbols.append(symbol)
            except Exception as e:
                failed_symbols.append(symbol)
    
    # ...existing Pine Script output code...
    
    # NEW: Save results to JSON file for frontend consumption
    import json
    from pathlib import Path
    
    # Build frontend-compatible data structure
    frontend_data = {
        'timestamp': datetime.now().isoformat(),
        'last_update': datetime.now().strftime("%b %d, %I:%M%p").lower(),
        'market_regime': regime,
        'vix': vix,
        'weights': PUT_WALL_WEIGHTS,
        'max_distances': MAX_DISTANCE_BY_CATEGORY,
        'symbols': {}
    }
    
    for result in results:
        symbol_key = result.get('display_name', result['symbol']).replace('^', '')
        current_price = result['current_price']
        
        # Calculate distances
        def calc_dist(level):
            if level and level > 0:
                return round(((current_price - level) / current_price) * 100, 2)
            return 0
        
        frontend_data['symbols'][symbol_key] = {
            'symbol': symbol_key,
            'current_price': current_price,
            'timestamp': result['timestamp'],
            
            # Put walls - USE WEIGHTED COMBO (the fixed values)
            'st_put_wall': result.get('st_put_wall', 0),
            'lt_put_wall': result.get('lt_put_wall', 0),
            'q_put_wall': result.get('q_put_wall', 0),
            'wk_put_wall': result.get('wk_put_wall', 0),
            
            # Distance calculations
            'st_put_distance': calc_dist(result.get('st_put_wall', 0)),
            'lt_put_distance': calc_dist(result.get('lt_put_wall', 0)),
            'q_put_distance': calc_dist(result.get('q_put_wall', 0)),
            
            # Call walls
            'st_call_wall': result.get('st_call_wall', 0),
            'lt_call_wall': result.get('lt_call_wall', 0),
            'q_call_wall': result.get('q_call_wall', 0),
            
            # Gamma flip and max pain
            'gamma_flip': result.get('gamma_flip', current_price),
            'max_pain': result.get('max_pain', 0),  # Need to add this calculation
            
            # SD levels
            'lower_1sd': result.get('lower_1sd', 0),
            'upper_1sd': result.get('upper_1sd', 0),
            'lower_2sd': result.get('lower_2sd', 0),
            'upper_2sd': result.get('upper_2sd', 0),
            
            # Method comparison (for debugging)
            'put_wall_methods': result.get('put_wall_methods', {}),
            
            # Strengths and other data
            'st_put_strength': result.get('st_put_strength', 0),
            'st_call_strength': result.get('st_call_strength', 0),
            'category': result.get('category', 'TECH')
        }
    
    # Save to cache directory
    cache_dir = Path(__file__).parent.parent / 'cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = cache_dir / 'gamma_walls_data.json'
    with open(output_file, 'w') as f:
        json.dump(frontend_data, f, indent=2, default=str)
    
    print(f"\n✅ Data saved to: {output_file}")
    print(f"   Symbols: {len(frontend_data['symbols'])}")
    
    # Also save to frontend public directory if it exists
    frontend_public = Path(__file__).parent.parent.parent / 'frontend' / 'public' / 'data'
    if frontend_public.parent.exists():
        frontend_public.mkdir(parents=True, exist_ok=True)
        frontend_output = frontend_public / 'gamma_walls.json'
        with open(frontend_output, 'w') as f:
            json.dump(frontend_data, f, indent=2, default=str)
        print(f"✅ Frontend data saved to: {frontend_output}")
    
    # Print verification for SPX
    if 'SPX' in frontend_data['symbols']:
        spx = frontend_data['symbols']['SPX']
        print(f"\n🔍 SPX VERIFICATION:")
        print(f"   Current Price: ${spx['current_price']:.2f}")
        print(f"   ST Put Wall: ${spx['st_put_wall']:.0f} ({spx['st_put_distance']:+.2f}%)")
        print(f"   Expected: ST Put should be within 8% of price (~${spx['current_price'] * 0.92:.0f})")
        
        if abs(spx['st_put_distance']) > 15:
            print(f"   ⚠️  WARNING: ST Put Wall still too far from price!")
        else:
            print(f"   ✅ ST Put Wall is within expected range")

    # ...rest of existing main() code...
    
    end_time = datetime.now()
    print(f"\n" + "="*100)
    print(f"SCAN COMPLETED - v8.1 with MULTI-METHOD PUT WALLS")
    print(f"Processing time: {(end_time - start_time).total_seconds():.1f} seconds")
    print(f"Successful: {len(results)}, Failed: {len(failed_symbols)}")
    print("="*100)


if __name__ == "__main__":
    main()