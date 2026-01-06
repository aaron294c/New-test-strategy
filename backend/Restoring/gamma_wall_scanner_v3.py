#!/usr/bin/env python3
"""
Enhanced Gamma Wall Scanner v7.1 - Extended Symbols
===================================================

This Python script generates the exact data format needed for the Pine Script.
Run this regularly to update the Pine Script data sources.

Key Features:
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
    'AAPL', 'NVDA', 'MSFT', 'AMZN', 'GOOGL', 'GOOG', 'META', 'TSLA', 'NFLX', 'AMD', 'CRM', 'ADBE', 'ORCL',
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

SWING_DAYS = 14
LONG_DAYS = 30  
QUARTERLY_DAYS = 90
RISK_FREE_RATE = 0.045
MAX_WORKERS = 8  # Increased for more symbols

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
        """
        Calculate weighted put wall using multiple methods for better accuracy.
        
        Returns:
            Tuple of (max_gex_wall, weighted_centroid_wall, cumulative_threshold_wall)
        """
        try:
            if puts_gex.empty:
                return current_price * 0.95, current_price * 0.95, current_price * 0.95
            
            # Filter to strikes below current price (actual support)
            support_strikes = puts_gex[puts_gex.index < current_price]
            if support_strikes.empty:
                support_strikes = puts_gex
            
            # Method 1: Max GEX (original) - strike with highest absolute exposure
            max_gex_wall = support_strikes.abs().idxmax()
            
            # Method 2: Weighted Centroid - center of mass of put GEX
            abs_gex = support_strikes.abs()
            total_gex = abs_gex.sum()
            if total_gex > 0:
                weighted_centroid = (abs_gex * abs_gex.index).sum() / total_gex
            else:
                weighted_centroid = max_gex_wall
            
            # Method 3: Cumulative Threshold - where X% of support GEX accumulates
            sorted_gex = abs_gex.sort_index(ascending=False)  # Start from current price down
            cumsum = sorted_gex.cumsum()
            threshold_value = total_gex * threshold_pct
            
            # Find strike where cumulative GEX exceeds threshold
            threshold_strikes = cumsum[cumsum >= threshold_value]
            if not threshold_strikes.empty:
                cumulative_threshold_wall = threshold_strikes.index[-1]  # Lowest strike meeting threshold
            else:
                cumulative_threshold_wall = max_gex_wall
            
            return max_gex_wall, weighted_centroid, cumulative_threshold_wall
            
        except Exception as e:
            logger.warning(f"Weighted put wall calculation error: {e}")
            return current_price * 0.95, current_price * 0.95, current_price * 0.95
    
    def calculate_max_pain(self, calls: pd.DataFrame, puts: pd.DataFrame) -> float:
        """
        Calculate true max pain - the strike where option holders lose the most.
        This is DIFFERENT from gamma flip.
        """
        try:
            all_strikes = calls.index.union(puts.index)
            pain_values = {}
            
            for strike in all_strikes:
                # Calculate ITM value for calls if price expires at this strike
                call_pain = 0
                for k in calls.index:
                    if k < strike:  # Call is ITM
                        oi = calls.loc[k, 'openInterest'] if 'openInterest' in calls.columns else 0
                        call_pain += (strike - k) * oi * 100
                
                # Calculate ITM value for puts if price expires at this strike
                put_pain = 0
                for k in puts.index:
                    if k > strike:  # Put is ITM
                        oi = puts.loc[k, 'openInterest'] if 'openInterest' in puts.columns else 0
                        put_pain += (k - strike) * oi * 100
                
                pain_values[strike] = call_pain + put_pain
            
            # Max pain is strike that MINIMIZES total option value (maximum loss for holders)
            if pain_values:
                max_pain_strike = min(pain_values, key=pain_values.get)
                return max_pain_strike
            
            return (all_strikes.min() + all_strikes.max()) / 2
            
        except Exception as e:
            logger.warning(f"Max pain calculation error: {e}")
            return 0
    
    def calculate_risk_distances(self, current_price: float, levels: Dict) -> Dict:
        """
        Calculate percentage distances from current price to all key levels.
        This is what your Pine Script needs for the Risk Distance tab.
        """
        distances = {}
        
        for level_name, level_price in levels.items():
            if level_price and level_price > 0:
                # Positive = price is ABOVE the level (for puts = cushion)
                # Negative = price is BELOW the level (for calls = cushion)
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
    """Process a single symbol and return comprehensive data with per-timeframe IVs"""
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
        
        # Find best expirations for each timeframe
        swing_exp, swing_dte = find_best_expiration(options_dates, SWING_DAYS)
        long_exp, long_dte = find_best_expiration(options_dates, LONG_DAYS)
        quarterly_exp, quarterly_dte = find_best_expiration(options_dates, QUARTERLY_DAYS)
        
        if not all([swing_exp, long_exp, quarterly_exp]):
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
        swing_calls_gex = pd.Series()  # For gamma flip calculation
        swing_puts_gex = pd.Series()   # For gamma flip calculation
        
        for tf_name, (exp_date, dte) in [
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
                
                # Adjust liquidity filters based on symbol category
                if category == 'INDEX':
                    # Indices typically have higher volume/OI requirements
                    min_volume = 100
                    min_oi = 200
                elif category == 'ETF':
                    # QQQ has excellent liquidity
                    min_volume = 50
                    min_oi = 100
                elif category in ['ENERGY', 'FINANCIAL', 'CONSUMER']:
                    # Traditional sectors may have lower liquidity
                    min_volume = 10
                    min_oi = 25
                else:
                    # Tech stocks (original requirements)
                    min_volume = 20
                    min_oi = 50
                
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
                
                # Adjust IV bounds based on symbol category
                if category == 'INDEX':
                    timeframe_iv = max(0.05, min(1.5, timeframe_iv))  # Indices moderate IV
                elif category == 'ETF':
                    timeframe_iv = max(0.03, min(1.0, timeframe_iv))  # QQQ typically lower IV
                elif category in ['ENERGY', 'FINANCIAL']:
                    timeframe_iv = max(0.10, min(1.5, timeframe_iv))  # Traditional sectors can be volatile
                elif category == 'CONSUMER':
                    timeframe_iv = max(0.08, min(1.2, timeframe_iv))  # Consumer stocks moderate
                else:
                    timeframe_iv = max(0.05, min(2.0, timeframe_iv))  # Tech stocks
                
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
                
                # Store swing data for gamma flip calculation
                if tf_name == 'swing':
                    swing_calls_gex = calls_gex.copy()
                    swing_puts_gex = puts_gex.copy()
                
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
                prefix = {'swing': 'st', 'long': 'lt', 'quarterly': 'q'}[tf_name]
                
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
                
                results.update({
                    f'{prefix}_put_wall': put_wall_strike or 0,
                    f'{prefix}_call_wall': call_wall_strike or 0,
                    f'{prefix}_put_strength': put_strength,
                    f'{prefix}_call_strength': call_strength,
                    f'{prefix}_put_gex': put_gex_millions,
                    f'{prefix}_call_gex': call_gex_millions,
                    f'{prefix}_iv': timeframe_iv * 100,  # Each timeframe gets its own IV!
                    f'{prefix}_dte': dte
                })
                
            except Exception as e:
                logger.warning(f"Failed to process {tf_name} for {symbol}: {e}")
                continue
        
        # Calculate swing-specific metrics using SWING timeframe IV
        if 'swing' in all_timeframe_data:
            swing_data = all_timeframe_data['swing']
            swing_iv_decimal = swing_data['iv_percent'] / 100  # Convert back to decimal
            swing_T = swing_data['dte'] / 365.0
            
            # Calculate standard deviation moves using swing IV
            base_move = current_price * swing_iv_decimal * np.sqrt(swing_T)
            
            results.update({
                'lower_1sd': current_price - base_move,
                'upper_1sd': current_price + base_move,
                'lower_1_5sd': current_price - base_move * 1.5,
                'upper_1_5sd': current_price + base_move * 1.5,
                'lower_2sd': current_price - base_move * 2.0,
                'upper_2sd': current_price + base_move * 2.0,
            })
            
            # Calculate REAL gamma flip point
            gamma_flip = calculator.calculate_gamma_flip(swing_calls_gex, swing_puts_gex, current_price)
            results['gamma_flip'] = gamma_flip
            
            # Calculate market metrics from swing data
            total_call_oi = sum([v.get('call_wall', 0) for v in all_timeframe_data.values() if v.get('call_wall')])
            total_put_oi = sum([v.get('put_wall', 0) for v in all_timeframe_data.values() if v.get('put_wall')])
            cp_ratio = total_call_oi / total_put_oi if total_put_oi > 0 else 2.0
            
            results.update({
                'swing_iv': swing_data['iv_percent'],  # Swing-specific IV
                'cp_ratio': cp_ratio,
                'activity_score': min(5.0, len(all_timeframe_data)),  # Based on available timeframes
                'trend': 0.0  # Could be enhanced with price trend analysis
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error processing {symbol}: {e}")
        return None

def format_for_pine_script(data: Dict) -> str:
    """Format data exactly as Pine Script expects (36 fields)"""
    
    # Pine Script expects exactly these 36 fields
    fields = [
        data.get('st_put_wall', 0),           # 0
        data.get('st_call_wall', 0),          # 1  
        data.get('lt_put_wall', 0),           # 2
        data.get('lt_call_wall', 0),          # 3
        data.get('lower_1sd', 0),             # 4
        data.get('upper_1sd', 0),             # 5
        data.get('st_put_wall', 0),           # 6 (gamma support - duplicate)
        data.get('st_call_wall', 0),          # 7 (gamma resistance - duplicate)
        data.get('gamma_flip', data.get('current_price', 0)), # 8 - Real gamma flip calculation
        data.get('swing_iv', 25.0),           # 9 - Swing timeframe IV
        data.get('cp_ratio', 2.0),            # 10
        data.get('trend', 0.0),               # 11
        data.get('activity_score', 3.0),      # 12
        data.get('st_put_wall', 0),           # 13 (duplicate)
        data.get('st_call_wall', 0),          # 14 (duplicate)
        data.get('lower_1_5sd', 0),           # 15
        data.get('upper_1_5sd', 0),           # 16
        data.get('lower_2sd', 0),             # 17
        data.get('upper_2sd', 0),             # 18
        data.get('q_put_wall', 0),            # 19
        data.get('q_call_wall', 0),           # 20
        data.get('st_put_strength', 0),       # 21
        data.get('st_call_strength', 0),      # 22
        data.get('lt_put_strength', 0),       # 23
        data.get('lt_call_strength', 0),      # 24
        data.get('q_put_strength', 0),        # 25
        data.get('q_call_strength', 0),       # 26
        data.get('st_dte', 14),               # 27
        data.get('lt_dte', 30),               # 28
        data.get('q_dte', 90),                # 29
        data.get('st_put_gex', 0.0),          # 30
        data.get('st_call_gex', 0.0),         # 31
        data.get('lt_put_gex', 0.0),          # 32
        data.get('lt_call_gex', 0.0),         # 33
        data.get('q_put_gex', 0.0),           # 34
        data.get('q_call_gex', 0.0),          # 35
    ]
    
    # Format each field appropriately
    formatted = []
    for i, field in enumerate(fields):
        if i == 9:  # IV percentage - this will now be different for each timeframe in labels
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
    print(f"Enhanced Gamma Wall Scanner v7.1 - Extended Symbols")
    print(f"="*90)
    print(f"Scan started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Market Regime: {regime} (VIX: {vix:.1f})")
    print(f"Processing {len(SYMBOLS)} symbols (Tech, Indices, ETF, Energy, Financial, Consumer)...")
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
                result = future.result(timeout=60)  # Increased timeout for ETFs
                if result:
                    results.append(result)
                    st_put = result.get('st_put_wall', 0)
                    st_call = result.get('st_call_wall', 0)
                    st_iv = result.get('st_iv', 0)
                    lt_iv = result.get('lt_iv', 0)
                    gf = result.get('gamma_flip', result['current_price'])
                    display_name = result.get('display_name', symbol)
                    category = result.get('category', '')
                    
                    print(f"✓ {display_name:12} ({category:6}): ${result['current_price']:>7.2f} | "
                          f"ST: ${st_put:>6.0f}-${st_call:>6.0f} | "
                          f"IV: {st_iv:>3.0f}%/{lt_iv:>3.0f}% | GF: ${gf:>7.0f}")
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
    print("// Updated data with working symbols (Tech, Indices, ETF, Energy, Financial)")
    print("// Includes ^SPX (working!), QQQ (NDX proxy), ^GDAXI (DAX), ^FTSE, CVX, XOM")
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
    print(f"SCAN COMPLETED")
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
    
    print(f"\nKey improvements in v7.1:")
    print(f"- Fixed NDX issue: Using QQQ (excellent options liquidity) as NDX proxy")
    print(f"- Added international indices: ^GDAXI (DAX), ^FTSE (FTSE 100)")
    print(f"- Kept working symbols: ^SPX, CVX, XOM, JPM, BAC, DIS, INTC")
    print(f"- Now includes {len(SYMBOLS)} symbols with better liquidity coverage")
    print(f"- Category-specific liquidity filters and IV bounds for indices")
    print(f"- Enhanced error handling and removed problematic symbols")
    print(f"- Direct index symbols instead of ETF proxies")
    print(f"- Ready to paste into Pine Script with extended coverage!")
    print("="*90)

if __name__ == "__main__":
    main()