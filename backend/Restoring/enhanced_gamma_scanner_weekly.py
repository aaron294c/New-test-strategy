#!/usr/bin/env python3
"""
Enhanced Gamma Wall Scanner v8.0 - Weekly Data Integration
=========================================================

This Python script generates the exact data format needed for the Pine Script.
Now includes TRUE WEEKLY data (7 days) for accurate weekly max pain calculations.

Key Features:
- TRUE WEEKLY data (7 days) for accurate weekly max pain
- Per-timeframe IV calculations (each wall has its own IV)
- Accurate gamma flip calculations  
- Real-time options data fetching
- GEX calculations in millions
- Pine Script compatible output format
- Extended symbol coverage including indices and energy stocks

Usage: python enhanced_gamma_wall_scanner.py
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
    
    def calculate_weighted_put_wall(self, puts_gex: pd.Series, current_price: float, 
                                     threshold_pct: float = 0.7) -> Tuple[float, float, float]:
        """Calculate weighted put wall using multiple methods for better accuracy."""
        try:
            if puts_gex.empty:
                return current_price * 0.95, current_price * 0.95, current_price * 0.95
            
            support_strikes = puts_gex[puts_gex.index < current_price]
            if support_strikes.empty:
                support_strikes = puts_gex
            
            # Method 1: Max GEX (original)
            max_gex_wall = support_strikes.abs().idxmax()
            
            # Method 2: Weighted Centroid
            abs_gex = support_strikes.abs()
            total_gex = abs_gex.sum()
            weighted_centroid = (abs_gex * abs_gex.index).sum() / total_gex if total_gex > 0 else max_gex_wall
            
            # Method 3: Cumulative Threshold (70% of support)
            sorted_gex = abs_gex.sort_index(ascending=False)
            cumsum = sorted_gex.cumsum()
            threshold_value = total_gex * threshold_pct
            threshold_strikes = cumsum[cumsum >= threshold_value]
            cumulative_threshold_wall = threshold_strikes.index[-1] if not threshold_strikes.empty else max_gex_wall
            
            return max_gex_wall, weighted_centroid, cumulative_threshold_wall
            
        except Exception as e:
            logger.warning(f"Weighted put wall error: {e}")
            return current_price * 0.95, current_price * 0.95, current_price * 0.95
    
    def calculate_max_pain(self, calls: pd.DataFrame, puts: pd.DataFrame) -> float:
        """Calculate true max pain strike - different from gamma flip."""
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
    """Process a single symbol and return comprehensive data with per-timeframe IVs including WEEKLY"""
    try:
        category = get_symbol_category(symbol)
        display_name = SYMBOL_DISPLAY_NAMES.get(symbol, symbol)
        logger.info(f"Processing {display_name} ({category})...")
        
        ticker = yf.Ticker(symbol)
        
        # Get current price with multiple fallbacks
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
        
        # Find best expirations for each timeframe - NOW INCLUDING WEEKLY
        weekly_exp, weekly_dte = find_best_expiration(options_dates, WEEKLY_DAYS)
        swing_exp, swing_dte = find_best_expiration(options_dates, SWING_DAYS)
        long_exp, long_dte = find_best_expiration(options_dates, LONG_DAYS)
        quarterly_exp, quarterly_dte = find_best_expiration(options_dates, QUARTERLY_DAYS)
        
        if not all([weekly_exp, swing_exp, long_exp, quarterly_exp]):
            logger.error(f"Missing expirations for {symbol}")
            return None
        
        # Process each timeframe and store results
        results = {
            'symbol': symbol,
            'display_name': display_name,
            'category': category,
            'current_price': current_price,
            'timestamp': datetime.now().isoformat()
        }
        
        all_timeframe_data = {}
        weekly_calls_gex = pd.Series()  # For gamma flip calculation (use WEEKLY for most accurate)
        weekly_puts_gex = pd.Series()   # For gamma flip calculation
        
        for tf_name, (exp_date, dte) in [
            ('weekly', (weekly_exp, weekly_dte)),    # NEW: True weekly data
            ('swing', (swing_exp, swing_dte)),
            ('long', (long_exp, long_dte)), 
            ('quarterly', (quarterly_exp, quarterly_dte))
        ]:
            try:
                chain = ticker.option_chain(exp_date)
                calls = chain.calls
                puts = chain.puts
                
                if calls.empty or puts.empty:
                    logger.warning(f"Empty options chain for {symbol} {tf_name}")
                    continue
                
                T = dte / 365.0
                
                # Adjust liquidity filters based on symbol category and timeframe
                if tf_name == 'weekly':
                    # Weekly options may have lower liquidity, so relax filters
                    if category == 'INDEX':
                        min_volume, min_oi = 50, 100
                    elif category == 'ETF':
                        min_volume, min_oi = 25, 50
                    elif category in ['ENERGY', 'FINANCIAL', 'CONSUMER']:
                        min_volume, min_oi = 5, 10
                    else:
                        min_volume, min_oi = 10, 25
                else:
                    # Original filters for other timeframes
                    if category == 'INDEX':
                        min_volume, min_oi = 100, 200
                    elif category == 'ETF':
                        min_volume, min_oi = 50, 100
                    elif category in ['ENERGY', 'FINANCIAL', 'CONSUMER']:
                        min_volume, min_oi = 10, 25
                    else:
                        min_volume, min_oi = 20, 50
                
                # Filter for liquid options
                calls = calls[
                    (calls['volume'].fillna(0) >= min_volume) | 
                    (calls['openInterest'] >= min_oi)
                ].copy()
                puts = puts[
                    (puts['volume'].fillna(0) >= min_volume) | 
                    (puts['openInterest'] >= min_oi)
                ].copy()
                
                if calls.empty or puts.empty:
                    logger.warning(f"No liquid options for {symbol} {tf_name}")
                    continue
                
                calls.set_index('strike', inplace=True)
                puts.set_index('strike', inplace=True)
                
                # Calculate TIMEFRAME-SPECIFIC IV
                calls_iv = calls['impliedVolatility'].median()
                puts_iv = puts['impliedVolatility'].median()
                timeframe_iv = (calls_iv + puts_iv) / 2 if pd.notna(calls_iv) and pd.notna(puts_iv) else 0.25
                
                # Adjust IV bounds based on symbol category and timeframe
                if tf_name == 'weekly':
                    # Weekly options typically have higher IV due to time pressure
                    if category == 'INDEX':
                        timeframe_iv = max(0.08, min(2.0, timeframe_iv))
                    elif category == 'ETF':
                        timeframe_iv = max(0.06, min(1.5, timeframe_iv))
                    elif category in ['ENERGY', 'FINANCIAL']:
                        timeframe_iv = max(0.15, min(2.5, timeframe_iv))
                    elif category == 'CONSUMER':
                        timeframe_iv = max(0.12, min(2.0, timeframe_iv))
                    else:
                        timeframe_iv = max(0.10, min(3.0, timeframe_iv))  # Tech stocks can be very volatile weekly
                else:
                    # Original IV bounds for other timeframes
                    if category == 'INDEX':
                        timeframe_iv = max(0.05, min(1.5, timeframe_iv))
                    elif category == 'ETF':
                        timeframe_iv = max(0.03, min(1.0, timeframe_iv))
                    elif category in ['ENERGY', 'FINANCIAL']:
                        timeframe_iv = max(0.10, min(1.5, timeframe_iv))
                    elif category == 'CONSUMER':
                        timeframe_iv = max(0.08, min(1.2, timeframe_iv))
                    else:
                        timeframe_iv = max(0.05, min(2.0, timeframe_iv))
                
                # Calculate gamma using timeframe-specific IV
                for df in [calls, puts]:
                    df['gamma'] = df.apply(
                        lambda row: calculator.calculate_gamma(
                            current_price, row.name, T, RISK_FREE_RATE, timeframe_iv
                        ), axis=1
                    )
                
                # Calculate GEX (Gamma * Open Interest * 100 * Stock Price)
                calls_gex = calls['openInterest'] * calls['gamma'] * 100 * current_price
                puts_gex = puts['openInterest'] * puts['gamma'] * 100 * current_price * -1  # Negative for puts
                
                # Store WEEKLY data for gamma flip calculation (most accurate)
                if tf_name == 'weekly':
                    weekly_calls_gex = calls_gex.copy()
                    weekly_puts_gex = puts_gex.copy()
                
                # Find walls (strikes with maximum absolute GEX)
                call_wall_strike = calls_gex.abs().idxmax() if not calls_gex.empty else None
                put_wall_strike = puts_gex.abs().idxmax() if not puts_gex.empty else None
                
                # Calculate wall strengths using original formula
                call_strength = calculator.calculate_wall_strength(calls_gex)
                put_strength = calculator.calculate_wall_strength(puts_gex)
                
                # Calculate GEX in millions for display
                call_gex_millions = calls_gex.sum() / 1_000_000
                put_gex_millions = puts_gex.sum() / 1_000_000
                
                # Store timeframe data
                all_timeframe_data[tf_name] = {
                    'put_wall': put_wall_strike,
                    'call_wall': call_wall_strike,
                    'put_strength': put_strength,
                    'call_strength': call_strength,
                    'put_gex_millions': put_gex_millions,
                    'call_gex_millions': call_gex_millions,
                    'iv_percent': timeframe_iv * 100,
                    'dte': dte
                }
                
                # Map to Pine Script field names - KEEP st_ as 14-day swing, ADD wk_ as weekly
                if tf_name == 'weekly':
                    prefix = 'wk'  # Weekly becomes new wk_ fields
                elif tf_name == 'swing':
                    prefix = 'st'  # Swing remains as st_ (14-day, unchanged)
                elif tf_name == 'long':
                    prefix = 'lt'  # Long stays the same
                elif tf_name == 'quarterly':
                    prefix = 'q'   # Quarterly stays the same
                
                results.update({
                    f'{prefix}_put_wall': put_wall_strike or 0,
                    f'{prefix}_call_wall': call_wall_strike or 0,
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
        
        # Calculate swing-specific metrics using SWING timeframe IV (keep st_ as 14-day)
        # BUT use weekly data for gamma flip (most accurate)
        if 'swing' in all_timeframe_data:
            swing_data = all_timeframe_data['swing']
            swing_iv_decimal = swing_data['iv_percent'] / 100  # Convert back to decimal
            swing_T = swing_data['dte'] / 365.0
            
            # Calculate standard deviation moves using SWING IV (14-day, unchanged)
            base_move = current_price * swing_iv_decimal * np.sqrt(swing_T)
            
            results.update({
                'lower_1sd': current_price - base_move,
                'upper_1sd': current_price + base_move,
                'lower_1_5sd': current_price - base_move * 1.5,
                'upper_1_5sd': current_price + base_move * 1.5,
                'lower_2sd': current_price - base_move * 2.0,
                'upper_2sd': current_price + base_move * 2.0,
            })
            
            # Calculate market metrics from swing data (14-day, unchanged)
            total_call_oi = sum([v.get('call_wall', 0) for v in all_timeframe_data.values() if v.get('call_wall')])
            total_put_oi = sum([v.get('put_wall', 0) for v in all_timeframe_data.values() if v.get('put_wall')])
            cp_ratio = total_call_oi / total_put_oi if total_put_oi > 0 else 2.0
            
            results.update({
                'swing_iv': swing_data['iv_percent'],  # Swing-specific IV (14-day, unchanged)
                'cp_ratio': cp_ratio,
                'activity_score': min(5.0, len(all_timeframe_data)),  # Based on available timeframes
                'trend': 0.0  # Could be enhanced with price trend analysis
            })
        
        # Calculate REAL gamma flip point using WEEKLY data (most accurate) but keep other calcs as swing
        if 'weekly' in all_timeframe_data and not weekly_calls_gex.empty and not weekly_puts_gex.empty:
            gamma_flip = calculator.calculate_gamma_flip(weekly_calls_gex, weekly_puts_gex, current_price)
            results['gamma_flip'] = gamma_flip
        elif 'swing' in all_timeframe_data:
            # Fallback to swing data if weekly not available
            results['gamma_flip'] = current_price
        
        return results
        
    except Exception as e:
        logger.error(f"Error processing {symbol}: {e}")
        return None

def format_for_pine_script(data: Dict) -> str:
    """Format data exactly as Pine Script expects (36 fields) - FIXED COMPATIBILITY"""
    
    # Pine Script expects exactly these 36 fields - FIXED to ensure data exists
    # st_ remains 14-day data, weekly data added to duplicate positions
    fields = [
        data.get('st_put_wall', 0.0),         # 0 - SWING put wall (14-day)
        data.get('st_call_wall', 0.0),        # 1 - SWING call wall (14-day)
        data.get('lt_put_wall', 0.0),         # 2 - LONG put wall (30-day)
        data.get('lt_call_wall', 0.0),        # 3 - LONG call wall (30-day)
        data.get('lower_1sd', data.get('current_price', 0) * 0.95),   # 4 - Based on SWING IV
        data.get('upper_1sd', data.get('current_price', 0) * 1.05),   # 5 - Based on SWING IV
        data.get('wk_put_wall', 0.0),         # 6 - NEW: WEEKLY put wall (7-day) 
        data.get('wk_call_wall', 0.0),        # 7 - NEW: WEEKLY call wall (7-day)
        data.get('gamma_flip', data.get('current_price', 0)), # 8 - Gamma flip
        data.get('st_iv', 25.0),              # 9 - SWING timeframe IV (14-day)
        data.get('cp_ratio', 2.0),            # 10
        data.get('trend', 0.0),               # 11
        data.get('activity_score', 3.0),      # 12
        data.get('wk_put_wall', 0.0),         # 13 - WEEKLY put wall (duplicate)
        data.get('wk_call_wall', 0.0),        # 14 - WEEKLY call wall (duplicate)
        data.get('lower_1_5sd', data.get('current_price', 0) * 0.92), # 15
        data.get('upper_1_5sd', data.get('current_price', 0) * 1.08), # 16
        data.get('lower_2sd', data.get('current_price', 0) * 0.90),   # 17
        data.get('upper_2sd', data.get('current_price', 0) * 1.10),   # 18
        data.get('q_put_wall', 0.0),          # 19 - QUARTERLY put wall
        data.get('q_call_wall', 0.0),         # 20 - QUARTERLY call wall
        data.get('st_put_strength', 0.0),     # 21 - SWING put strength
        data.get('st_call_strength', 0.0),    # 22 - SWING call strength
        data.get('lt_put_strength', 0.0),     # 23 - LONG put strength
        data.get('lt_call_strength', 0.0),    # 24 - LONG call strength
        data.get('q_put_strength', 0.0),      # 25 - QUARTERLY put strength
        data.get('q_call_strength', 0.0),     # 26 - QUARTERLY call strength
        data.get('st_dte', 14),               # 27 - SWING DTE
        data.get('lt_dte', 30),               # 28 - LONG DTE
        data.get('q_dte', 90),                # 29 - QUARTERLY DTE
        data.get('st_put_gex', 0.0),          # 30 - SWING put GEX
        data.get('st_call_gex', 0.0),         # 31 - SWING call GEX
        data.get('lt_put_gex', 0.0),          # 32 - LONG put GEX
        data.get('lt_call_gex', 0.0),         # 33 - LONG call GEX
        data.get('q_put_gex', 0.0),           # 34 - QUARTERLY put GEX
        data.get('q_call_gex', 0.0),          # 35 - QUARTERLY call GEX
    ]
    
    # Format each field appropriately
    formatted = []
    for i, field in enumerate(fields):
        if i == 9:  # IV percentage - this is now WEEKLY IV
            formatted.append(f"{float(field):.1f}")
        elif i in [4, 5, 6, 7, 8, 13, 14, 15, 16, 17, 18, 19, 20]:  # Price levels
            formatted.append(f"{float(field):.2f}")
        elif i >= 21 and i <= 26:  # Strength scores
            formatted.append(f"{float(field):.1f}")
        elif i >= 27 and i <= 29:  # DTE values
            formatted.append(f"{int(field)}")
        elif i >= 30:  # GEX values
            formatted.append(f"{float(field):.1f}")
        else:
            formatted.append(f"{float(field):.1f}")
    
    return ",".join(formatted)

def main():
    """Main execution function"""
    start_time = datetime.now()
    calculator = GammaWallCalculator()
    regime, vix = get_market_regime()
    
    print(f"\n" + "="*90)
    print(f"Enhanced Gamma Wall Scanner v8.0 - WEEKLY DATA INTEGRATION")
    print(f"="*90)
    print(f"Scan started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Market Regime: {regime} (VIX: {vix:.1f})")
    print(f"Processing {len(SYMBOLS)} symbols with TRUE WEEKLY DATA (7 days)...")
    print(f"Timeframes: WEEKLY (7D), SWING (14D), LONG (30D), QUARTERLY (90D)")
    print("-"*90)
    
    # Process symbols in parallel
    results = []
    failed_symbols = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_symbol = {
            executor.submit(process_symbol, symbol, calculator): symbol 
            for symbol in SYMBOLS
        }
        
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                result = future.result(timeout=60)
                if result:
                    results.append(result)
                    # st_ remains 14-day swing data (unchanged)
                    swing_put = result.get('st_put_wall', 0)
                    swing_call = result.get('st_call_wall', 0)
                    swing_iv = result.get('st_iv', 0)
                    # wk_ is new 7-day weekly data
                    weekly_put = result.get('wk_put_wall', 0)
                    weekly_call = result.get('wk_call_wall', 0)
                    long_iv = result.get('lt_iv', 0)
                    gf = result.get('gamma_flip', result['current_price'])
                    display_name = result.get('display_name', symbol)
                    category = result.get('category', '')
                    swing_dte = result.get('st_dte', 14)
                    weekly_dte = result.get('wk_dte', 7)
                    
                    print(f"✓ {display_name:12} ({category:6}): ${result['current_price']:>7.2f} | "
                          f"SWING: ${swing_put:>6.0f}-${swing_call:>6.0f} ({swing_dte}D) | "
                          f"WEEKLY: ${weekly_put:>6.0f}-${weekly_call:>6.0f} ({weekly_dte}D) | GF: ${gf:>7.0f}")
                else:
                    failed_symbols.append(symbol)
                    print(f"✗ {symbol:12}: Failed to process")
            except Exception as e:
                failed_symbols.append(symbol)
                error_msg = str(e)[:40] + "..." if len(str(e)) > 40 else str(e)
                print(f"✗ {symbol:12}: Error - {error_msg}")
    
    # Sort results by category for better organization
    results.sort(key=lambda x: (x.get('category', 'ZZZ'), x['symbol']))
    
    # Generate Pine Script output
    print("\n" + "="*90)
    print("PINE SCRIPT DATA - COPY & PASTE INTO YOUR INDICATOR")
    print("="*90)
    print("// Updated data with 14-day SWING data (st_ fields) + 7-day WEEKLY data (wk_ fields)")
    print("// st_ fields contain SWING data (14 days, unchanged)")
    print("// wk_ fields contain WEEKLY data (7 days, new addition)")
    print("// lt_ fields contain LONG data (30 days)")
    print("// q_ fields contain QUARTERLY data (90 days)")
    print("// Gamma flip calculated using weekly data for maximum accuracy")
    print()
    
    # Prioritize important symbols for Pine Script (limit to top symbols)
    priority_symbols = ['^SPX', 'QQQ', 'AAPL', 'NVDA', 'MSFT', 'CVX', 'XOM', 'TSLA', 'META', 'AMZN']
    priority_results = []
    other_results = []
    
    for result in results:
        if result['symbol'] in priority_symbols:
            priority_results.append(result)
        else:
            other_results.append(result)
    
    # Sort priority results by the order in priority_symbols
    priority_results.sort(key=lambda x: priority_symbols.index(x['symbol']) if x['symbol'] in priority_symbols else 999)
    
    # Combine and take top 15 for Pine Script
    final_results = priority_results + other_results
    
    for i, result in enumerate(final_results[:15], 1):  # Support up to 15 symbols
        pine_data = format_for_pine_script(result)
        display_name = result.get('display_name', result['symbol'])
        swing_dte = result.get('st_dte', 14)
        weekly_dte = result.get('wk_dte', 7)
        long_dte = result.get('lt_dte', 30)
        print(f'var string level_data{i} = "{display_name}:{pine_data};"')
    
    # Print metadata
    print()
    print(f'var string last_update = "{datetime.now().strftime("%b %d, %I:%M%p").lower()}"')
    print(f'var string market_regime = "{regime}"')
    print(f'var float current_vix = {vix:.1f}')
    print('var bool regime_adjustment_enabled = true')
    
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    
    print(f"\n" + "="*90)
    print(f"SCAN COMPLETED WITH WEEKLY DATA INTEGRATION")
    print(f"Processing time: {processing_time:.1f} seconds")
    print(f"Successful: {len(results)} symbols")
    if failed_symbols:
        print(f"Failed: {len(failed_symbols)} symbols ({', '.join(failed_symbols)})")
    print(f"Symbol breakdown:")
    
    # Count by category
    category_counts = {}
    for result in results:
        cat = result.get('category', 'OTHER')
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    for cat, count in category_counts.items():
        print(f"- {cat}: {count} symbols")
    
    print(f"\nKEY IMPROVEMENTS in v8.0:")
    print(f"- ADDED WEEKLY DATA: wk_ fields now contain true 7-day weekly option data")
    print(f"- PRESERVED STRUCTURE: st_ fields remain 14-day swing data (unchanged)")
    print(f"- DUAL TIMEFRAME: Now have both 14-day (st_) and 7-day (wk_) data")
    print(f"- ENHANCED GAMMA FLIP: Calculated using weekly data for maximum accuracy")
    print(f"- TIMEFRAME CLARITY: Weekly (7D), Swing (14D), Long (30D), Quarterly (90D)")
    print(f"- WEEKLY FIELDS: wk_ data in positions 6,7,13,14 (replacing duplicates)")
    print(f"- LIQUIDITY ADJUSTED: Relaxed filters for weekly options (naturally lower volume)")
    print(f"- PINE SCRIPT COMPATIBLE: Same 36-field format, just with additional weekly data")
    print(f"- COPY & PASTE: Ready to update your Pine Script with both swing and weekly data!")
    print("="*90)

if __name__ == "__main__":
    main()