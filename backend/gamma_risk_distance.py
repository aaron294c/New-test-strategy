#!/usr/bin/env python3
"""
Gamma Risk Distance Calculator v1.0
====================================

Unified module for calculating risk distances to gamma walls, max pain, and weighted support levels.
Provides accurate data for the frontend Risk Distance tab.

Key Features:
- Weighted put wall calculations (3 methods)
- True max pain calculation (different from gamma flip)
- Risk distance percentages for all levels
- Pine Script compatible output
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from scipy.stats import norm
import warnings
import logging
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
WEEKLY_DAYS = 7
SWING_DAYS = 14
LONG_DAYS = 30
QUARTERLY_DAYS = 90
RISK_FREE_RATE = 0.045


@dataclass
class RiskDistanceLevel:
    """Single risk distance level with all relevant metrics."""
    name: str
    price: float
    distance_pct: float
    distance_pts: float
    strength: float
    timeframe: str
    level_type: str  # 'support', 'resistance', 'neutral'


@dataclass
class MaxPainData:
    """Max pain calculation results."""
    strike: float
    distance_pct: float
    distance_pts: float
    total_pain_value: float
    call_pain: float
    put_pain: float
    timeframe: str


@dataclass
class WeightedWallData:
    """Weighted put/call wall data with multiple calculation methods."""
    max_gex_wall: float
    weighted_centroid: float
    cumulative_threshold: float
    recommended_wall: float  # Best method for this symbol
    method_used: str
    confidence: str


@dataclass
class SymbolRiskProfile:
    """Complete risk distance profile for a symbol."""
    symbol: str
    current_price: float
    timestamp: str
    
    # Put walls by timeframe
    weekly_put_wall: RiskDistanceLevel
    swing_put_wall: RiskDistanceLevel
    long_put_wall: RiskDistanceLevel
    quarterly_put_wall: RiskDistanceLevel
    
    # Call walls by timeframe
    weekly_call_wall: RiskDistanceLevel
    swing_call_wall: RiskDistanceLevel
    long_call_wall: RiskDistanceLevel
    quarterly_call_wall: RiskDistanceLevel
    
    # Max pain by timeframe
    weekly_max_pain: MaxPainData
    swing_max_pain: MaxPainData
    long_max_pain: MaxPainData
    quarterly_max_pain: MaxPainData
    
    # Weighted walls (enhanced accuracy)
    weighted_put_walls: WeightedWallData
    weighted_call_walls: WeightedWallData
    
    # Gamma flip
    gamma_flip: float
    gamma_flip_distance_pct: float
    
    # Standard deviation levels
    lower_1sd: float
    upper_1sd: float
    lower_2sd: float
    upper_2sd: float
    
    # Summary metrics
    nearest_support_pct: float
    nearest_resistance_pct: float
    risk_reward_ratio: float
    position_in_range: str  # 'near_support', 'mid_range', 'near_resistance'


class GammaRiskCalculator:
    """Enhanced gamma calculator with weighted wall methods and max pain."""
    
    def __init__(self):
        self.errors = []
    
    def calculate_gamma(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate Black-Scholes gamma."""
        try:
            if any(x <= 0 for x in [S, K, T]) or sigma <= 0:
                return 0.0
            d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
            return gamma if not (np.isnan(gamma) or np.isinf(gamma)) else 0.0
        except:
            return 0.0
    
    def calculate_wall_strength(self, gex_series: pd.Series) -> float:
        """Calculate wall strength: concentration * 45 + log10(exposure) * 8."""
        try:
            if gex_series.empty:
                return 0.0
            max_exposure = gex_series.abs().max()
            total_exposure = gex_series.abs().sum()
            if total_exposure == 0:
                return 0.0
            concentration = max_exposure / total_exposure
            log_exposure = np.log10(max_exposure + 1)
            strength = concentration * 45 + log_exposure * 8
            return max(0.0, min(95.0, strength))
        except:
            return 0.0
    
    def calculate_weighted_wall(self, gex_series: pd.Series, current_price: float, 
                                 is_put: bool = True, threshold_pct: float = 0.7) -> WeightedWallData:
        """
        Calculate weighted wall using multiple methods.
        
        Methods:
        1. Max GEX: Strike with highest absolute gamma exposure
        2. Weighted Centroid: Center of mass of GEX distribution
        3. Cumulative Threshold: Strike where X% of GEX accumulates
        """
        try:
            if gex_series.empty:
                default = current_price * (0.95 if is_put else 1.05)
                return WeightedWallData(default, default, default, default, 'fallback', 'low')
            
            # Filter to relevant strikes
            if is_put:
                relevant_strikes = gex_series[gex_series.index < current_price]
            else:
                relevant_strikes = gex_series[gex_series.index > current_price]
            
            if relevant_strikes.empty:
                relevant_strikes = gex_series
            
            abs_gex = relevant_strikes.abs()
            total_gex = abs_gex.sum()
            
            # Method 1: Max GEX
            max_gex_wall = abs_gex.idxmax()
            
            # Method 2: Weighted Centroid
            if total_gex > 0:
                weighted_centroid = (abs_gex * abs_gex.index).sum() / total_gex
            else:
                weighted_centroid = max_gex_wall
            
            # Method 3: Cumulative Threshold
            if is_put:
                sorted_gex = abs_gex.sort_index(ascending=False)
            else:
                sorted_gex = abs_gex.sort_index(ascending=True)
            
            cumsum = sorted_gex.cumsum()
            threshold_value = total_gex * threshold_pct
            threshold_strikes = cumsum[cumsum >= threshold_value]
            
            if not threshold_strikes.empty:
                cumulative_threshold = threshold_strikes.index[-1] if is_put else threshold_strikes.index[0]
            else:
                cumulative_threshold = max_gex_wall
            
            # Determine best method based on GEX distribution
            gex_concentration = abs_gex.max() / total_gex if total_gex > 0 else 0
            
            if gex_concentration > 0.5:
                # High concentration - max GEX is reliable
                recommended = max_gex_wall
                method = 'max_gex'
                confidence = 'high'
            elif gex_concentration > 0.3:
                # Moderate concentration - use weighted centroid
                recommended = weighted_centroid
                method = 'weighted_centroid'
                confidence = 'medium'
            else:
                # Dispersed GEX - use cumulative threshold
                recommended = cumulative_threshold
                method = 'cumulative_threshold'
                confidence = 'medium'
            
            return WeightedWallData(
                max_gex_wall=max_gex_wall,
                weighted_centroid=weighted_centroid,
                cumulative_threshold=cumulative_threshold,
                recommended_wall=recommended,
                method_used=method,
                confidence=confidence
            )
            
        except Exception as e:
            logger.warning(f"Weighted wall error: {e}")
            default = current_price * (0.95 if is_put else 1.05)
            return WeightedWallData(default, default, default, default, 'error', 'low')
    
    def calculate_max_pain(self, calls: pd.DataFrame, puts: pd.DataFrame, 
                           current_price: float, timeframe: str) -> MaxPainData:
        """
        Calculate true max pain - the strike where option holders lose the most.
        This is DIFFERENT from gamma flip.
        """
        try:
            all_strikes = calls.index.union(puts.index)
            pain_values = {}
            call_pain_by_strike = {}
            put_pain_by_strike = {}
            
            for strike in all_strikes:
                # ITM call value if price expires at this strike
                call_pain = 0
                for k in calls.index:
                    if k < strike:  # Call is ITM
                        oi = calls.loc[k, 'openInterest'] if 'openInterest' in calls.columns else 0
                        call_pain += (strike - k) * oi * 100
                
                # ITM put value if price expires at this strike
                put_pain = 0
                for k in puts.index:
                    if k > strike:  # Put is ITM
                        oi = puts.loc[k, 'openInterest'] if 'openInterest' in puts.columns else 0
                        put_pain += (k - strike) * oi * 100
                
                pain_values[strike] = call_pain + put_pain
                call_pain_by_strike[strike] = call_pain
                put_pain_by_strike[strike] = put_pain
            
            if pain_values:
                max_pain_strike = min(pain_values, key=pain_values.get)
                total_pain = pain_values[max_pain_strike]
                
                distance_pct = ((current_price - max_pain_strike) / current_price) * 100
                distance_pts = current_price - max_pain_strike
                
                return MaxPainData(
                    strike=max_pain_strike,
                    distance_pct=round(distance_pct, 2),
                    distance_pts=round(distance_pts, 2),
                    total_pain_value=total_pain,
                    call_pain=call_pain_by_strike.get(max_pain_strike, 0),
                    put_pain=put_pain_by_strike.get(max_pain_strike, 0),
                    timeframe=timeframe
                )
            
            return MaxPainData(current_price, 0, 0, 0, 0, 0, timeframe)
            
        except Exception as e:
            logger.warning(f"Max pain error: {e}")
            return MaxPainData(current_price, 0, 0, 0, 0, 0, timeframe)
    
    def calculate_gamma_flip(self, calls_gex: pd.Series, puts_gex: pd.Series, 
                              current_price: float) -> float:
        """Calculate gamma flip point where net GEX crosses zero."""
        try:
            all_strikes = calls_gex.index.union(puts_gex.index)
            net_gex = pd.Series(0.0, index=all_strikes)
            
            for strike in calls_gex.index:
                if strike in net_gex.index:
                    net_gex[strike] += calls_gex[strike]
            
            for strike in puts_gex.index:
                if strike in net_gex.index:
                    net_gex[strike] += puts_gex[strike]
            
            net_gex = net_gex.sort_index()
            
            for i in range(len(net_gex) - 1):
                if net_gex.iloc[i] * net_gex.iloc[i + 1] < 0:
                    strike1, gex1 = net_gex.index[i], net_gex.iloc[i]
                    strike2, gex2 = net_gex.index[i + 1], net_gex.iloc[i + 1]
                    gamma_flip = strike1 + (strike2 - strike1) * (-gex1) / (gex2 - gex1)
                    return gamma_flip
            
            return min(all_strikes, key=lambda x: abs(x - current_price))
            
        except Exception as e:
            logger.warning(f"Gamma flip error: {e}")
            return current_price
    
    def calculate_risk_distance(self, current_price: float, level_price: float) -> Tuple[float, float]:
        """Calculate distance percentage and points from current price to level."""
        if level_price <= 0:
            return 0.0, 0.0
        distance_pct = ((current_price - level_price) / current_price) * 100
        distance_pts = current_price - level_price
        return round(distance_pct, 2), round(distance_pts, 2)


def find_best_expiration(options_dates: List[str], target_days: int) -> Tuple[Optional[str], int]:
    """Find the best expiration date for target days."""
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
    
    best = min(valid_dates, key=lambda x: abs(x[1] - target_days))
    return best[0], best[1]


def process_symbol_risk_distance(symbol: str) -> Optional[Dict]:
    """Process a symbol and return complete risk distance profile."""
    calculator = GammaRiskCalculator()
    
    try:
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
        except:
            return None
        
        if not options_dates:
            return None
        
        # Find expirations for each timeframe
        timeframes = {
            'weekly': (WEEKLY_DAYS, 'wk'),
            'swing': (SWING_DAYS, 'st'),
            'long': (LONG_DAYS, 'lt'),
            'quarterly': (QUARTERLY_DAYS, 'q')
        }
        
        result = {
            'symbol': symbol,
            'current_price': current_price,
            'timestamp': datetime.now().isoformat(),
            'put_walls': {},
            'call_walls': {},
            'max_pain': {},
            'weighted_walls': {},
            'risk_distances': {},
            'gamma_flip': None,
            'sd_levels': {},
            'summary': {}
        }
        
        all_puts_gex = {}
        all_calls_gex = {}
        
        for tf_name, (target_days, prefix) in timeframes.items():
            exp_date, dte = find_best_expiration(options_dates, target_days)
            if not exp_date:
                continue
            
            try:
                chain = ticker.option_chain(exp_date)
                calls = chain.calls.copy()
                puts = chain.puts.copy()
                
                if calls.empty or puts.empty:
                    continue
                
                # Filter for liquid options
                calls = calls[(calls['volume'].fillna(0) >= 10) | (calls['openInterest'] >= 25)].copy()
                puts = puts[(puts['volume'].fillna(0) >= 10) | (puts['openInterest'] >= 25)].copy()
                
                if calls.empty or puts.empty:
                    continue
                
                calls.set_index('strike', inplace=True)
                puts.set_index('strike', inplace=True)
                
                # Calculate IV
                calls_iv = calls['impliedVolatility'].median()
                puts_iv = puts['impliedVolatility'].median()
                timeframe_iv = (calls_iv + puts_iv) / 2 if pd.notna(calls_iv) and pd.notna(puts_iv) else 0.25
                timeframe_iv = max(0.05, min(2.0, timeframe_iv))
                
                T = dte / 365.0
                
                # Calculate gamma for each option
                for df in [calls, puts]:
                    df['gamma'] = df.apply(
                        lambda row: calculator.calculate_gamma(current_price, row.name, T, RISK_FREE_RATE, timeframe_iv),
                        axis=1
                    )
                
                # Calculate GEX
                calls_gex = calls['openInterest'] * calls['gamma'] * 100 * current_price
                puts_gex = puts['openInterest'] * puts['gamma'] * 100 * current_price * -1
                
                all_puts_gex[tf_name] = puts_gex
                all_calls_gex[tf_name] = calls_gex
                
                # Find walls
                put_wall_strike = puts_gex.abs().idxmax() if not puts_gex.empty else current_price * 0.95
                call_wall_strike = calls_gex.abs().idxmax() if not calls_gex.empty else current_price * 1.05
                
                put_strength = calculator.calculate_wall_strength(puts_gex)
                call_strength = calculator.calculate_wall_strength(calls_gex)
                
                put_dist_pct, put_dist_pts = calculator.calculate_risk_distance(current_price, put_wall_strike)
                call_dist_pct, call_dist_pts = calculator.calculate_risk_distance(current_price, call_wall_strike)
                
                # Store put wall
                result['put_walls'][tf_name] = {
                    'strike': put_wall_strike,
                    'distance_pct': put_dist_pct,
                    'distance_pts': put_dist_pts,
                    'strength': put_strength,
                    'dte': dte
                }
                
                # Store call wall
                result['call_walls'][tf_name] = {
                    'strike': call_wall_strike,
                    'distance_pct': call_dist_pct,
                    'distance_pts': call_dist_pts,
                    'strength': call_strength,
                    'dte': dte
                }
                
                # Calculate max pain
                max_pain = calculator.calculate_max_pain(calls, puts, current_price, tf_name)
                result['max_pain'][tf_name] = asdict(max_pain)
                
                # Calculate weighted walls for swing timeframe
                if tf_name == 'swing':
                    weighted_put = calculator.calculate_weighted_wall(puts_gex, current_price, is_put=True)
                    weighted_call = calculator.calculate_weighted_wall(calls_gex, current_price, is_put=False)
                    
                    result['weighted_walls']['put'] = asdict(weighted_put)
                    result['weighted_walls']['call'] = asdict(weighted_call)
                    
                    # Calculate SD levels using swing IV
                    base_move = current_price * timeframe_iv * np.sqrt(T)
                    result['sd_levels'] = {
                        'lower_1sd': round(current_price - base_move, 2),
                        'upper_1sd': round(current_price + base_move, 2),
                        'lower_1_5sd': round(current_price - base_move * 1.5, 2),
                        'upper_1_5sd': round(current_price + base_move * 1.5, 2),
                        'lower_2sd': round(current_price - base_move * 2, 2),
                        'upper_2sd': round(current_price + base_move * 2, 2),
                        'iv_used': round(timeframe_iv * 100, 1),
                        'dte': dte
                    }
                    
                    # Calculate gamma flip
                    gamma_flip = calculator.calculate_gamma_flip(calls_gex, puts_gex, current_price)
                    gf_dist_pct, gf_dist_pts = calculator.calculate_risk_distance(current_price, gamma_flip)
                    result['gamma_flip'] = {
                        'strike': gamma_flip,
                        'distance_pct': gf_dist_pct,
                        'distance_pts': gf_dist_pts
                    }
                
            except Exception as e:
                logger.warning(f"Error processing {tf_name} for {symbol}: {e}")
                continue
        
        # Calculate summary metrics
        if result['put_walls'] and result['call_walls']:
            # Find nearest support (closest put wall above current position)
            put_distances = [v['distance_pct'] for v in result['put_walls'].values()]
            call_distances = [v['distance_pct'] for v in result['call_walls'].values()]
            
            nearest_support = min(put_distances) if put_distances else 0
            nearest_resistance = max(call_distances) if call_distances else 0
            
            # Position in range
            if nearest_support < 2:
                position = 'near_support'
            elif abs(nearest_resistance) < 2:
                position = 'near_resistance'
            else:
                position = 'mid_range'
            
            # Risk/reward ratio
            if nearest_resistance != 0:
                rr_ratio = abs(nearest_support / nearest_resistance)
            else:
                rr_ratio = 1.0
            
            result['summary'] = {
                'nearest_support_pct': nearest_support,
                'nearest_resistance_pct': nearest_resistance,
                'risk_reward_ratio': round(rr_ratio, 2),
                'position_in_range': position,
                'recommendation': get_position_recommendation(position, rr_ratio, nearest_support)
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing {symbol}: {e}")
        return None


def get_position_recommendation(position: str, rr_ratio: float, support_distance: float) -> str:
    """Generate position recommendation based on risk metrics."""
    if position == 'near_support':
        if support_distance < 1:
            return "CAUTION: Very close to support - tight stop required"
        return "FAVORABLE: Near support with limited downside"
    elif position == 'near_resistance':
        return "CAUTION: Near resistance - consider taking profits"
    else:
        if rr_ratio > 1.5:
            return "FAVORABLE: Good risk/reward ratio"
        elif rr_ratio < 0.5:
            return "UNFAVORABLE: Poor risk/reward ratio"
        return "NEUTRAL: Balanced risk/reward"


def get_risk_distance_data(symbols: List[str]) -> Dict:
    """Get risk distance data for multiple symbols."""
    results = {}
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_symbol = {
            executor.submit(process_symbol_risk_distance, symbol): symbol
            for symbol in symbols
        }
        
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                result = future.result(timeout=60)
                if result:
                    results[symbol] = result
            except Exception as e:
                logger.error(f"Error getting risk distance for {symbol}: {e}")
    
    return results


# API endpoint function for FastAPI
def get_symbol_risk_distances(symbol: str) -> Optional[Dict]:
    """API endpoint to get risk distances for a single symbol."""
    return process_symbol_risk_distance(symbol)


if __name__ == "__main__":
    # Test with a few symbols
    test_symbols = ['AAPL', 'NVDA', 'SPY']
    
    for symbol in test_symbols:
        print(f"\n{'='*60}")
        print(f"Risk Distance Analysis: {symbol}")
        print('='*60)
        
        data = process_symbol_risk_distance(symbol)
        
        if data:
            print(f"Current Price: ${data['current_price']:.2f}")
            print(f"\nPut Walls (Support Levels):")
            for tf, wall in data['put_walls'].items():
                print(f"  {tf:10}: ${wall['strike']:.2f} ({wall['distance_pct']:+.2f}%) - Strength: {wall['strength']:.1f}")
            
            print(f"\nMax Pain Levels:")
            for tf, mp in data['max_pain'].items():
                print(f"  {tf:10}: ${mp['strike']:.2f} ({mp['distance_pct']:+.2f}%)")
            
            if data['weighted_walls']:
                print(f"\nWeighted Put Wall Analysis:")
                wp = data['weighted_walls'].get('put', {})
                print(f"  Max GEX:     ${wp.get('max_gex_wall', 0):.2f}")
                print(f"  Centroid:    ${wp.get('weighted_centroid', 0):.2f}")
                print(f"  Cumulative:  ${wp.get('cumulative_threshold', 0):.2f}")
                print(f"  Recommended: ${wp.get('recommended_wall', 0):.2f} ({wp.get('method_used', 'N/A')})")
            
            if data['summary']:
                print(f"\nSummary:")
                print(f"  Position: {data['summary']['position_in_range']}")
                print(f"  Risk/Reward: {data['summary']['risk_reward_ratio']:.2f}")
                print(f"  Recommendation: {data['summary']['recommendation']}")
        else:
            print("Failed to get data")
