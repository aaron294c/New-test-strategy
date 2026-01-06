#!/usr/bin/env python3
"""
Enhanced Gamma Wall Scanner v9.0 - Bucket-Based Aggregation
============================================================

MAJOR FIX in v9.0:
- Replaced single-expiry selection with DTE bucket aggregation
- ST/LT/Q now computed from distinct DTE windows, reducing duplicates
- Aggregates GEX across all expiries in each bucket before wall selection
- Comprehensive debug output showing expiries included and top strikes

DTE Buckets:
- Weekly (WK): DTE [1, 10]   - Near-term pin levels
- Swing (ST):  DTE [7, 21]   - 2-3 week gamma walls  
- Long (LT):   DTE [22, 45]  - Monthly structure
- Quarterly (Q): DTE [60, 120] - Long-term support

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
import json
from pathlib import Path
from dataclasses import dataclass, field

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === CONFIGURATION ===
# Extended symbol list with working Yahoo Finance symbols
SYMBOLS = [
    # Align with Live Market State tickers (swing_framework_api.py current-state list)
    'SPY',
    'QQQ',    # display as QQQ(NDX)
    '^SPX',   # S&P 500 Index (kept for SPX wall accuracy)
    '^VIX',   # VIX (may not have options via Yahoo; safe to attempt)

    # Mega-cap / core equities
    'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'TSLA', 'NFLX',
    'BRK-B', 'AVGO', 'LLY', 'UNH', 'TSM', 'WMT', 'COST',

    # Energy / Financial
    'XOM', 'CVX', 'OXY', 'JPM', 'BAC',

    # Liquid ETFs / proxies used in market state
    'GLD', 'SLV',
]

# === DTE BUCKET DEFINITIONS ===
# Each bucket is (min_dte, max_dte) - expiries in this range are aggregated
DTE_BUCKETS = {
    'weekly': (1, 10),      # Near-term pin levels (0DTE to ~1.5 weeks)
    'swing': (7, 21),       # Swing trading (1-3 weeks) - overlaps weekly intentionally
    'long': (22, 45),       # Monthly structure (3-6 weeks)
    'quarterly': (60, 120), # Quarterly support (2-4 months)
}

RISK_FREE_RATE = 0.045
MAX_WORKERS = 8

# Weights for weighted combination method
PUT_WALL_WEIGHTS = {
    'max_gex': 0.50,
    'weighted_centroid': 0.30,
    'cumulative_threshold': 0.20
}

# Category-specific max distance from spot
MAX_DISTANCE_BY_CATEGORY = {
    'INDEX': 0.08,
    'ETF': 0.10,
    'TECH': 0.12,
    'ENERGY': 0.10,
    'FINANCIAL': 0.10,
    'CONSUMER': 0.10,
    'DEFAULT': 0.15
}

# Symbol mapping for display names
SYMBOL_DISPLAY_NAMES = {
    '^SPX': 'SPX',
    '^VIX': 'VIX',
    'QQQ': 'QQQ(NDX)',
}


@dataclass
class BucketDebugInfo:
    """Debug information for a single timeframe bucket."""
    bucket_name: str
    dte_range: Tuple[int, int]
    expiries_included: List[str]
    dte_list: List[int]
    total_strikes: int
    strikes_after_filter: int
    top_5_strikes: List[Tuple[float, float]]  # (strike, abs_gex)
    dominance_ratio: float  # top_strike_gex / total_gex
    selected_wall: float
    selection_method: str


@dataclass
class AggregatedGEX:
    """Aggregated GEX data for a bucket."""
    put_gex_by_strike: pd.Series
    call_gex_by_strike: pd.Series
    expiries_used: List[str]
    dte_list: List[int]
    median_iv: float


class GammaWallCalculator:
    def __init__(self):
        self.errors = []
    
    def calculate_gamma(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate Black-Scholes gamma."""
        try:
            if any(x <= 0 for x in [S, K, T]) or sigma <= 0:
                return 0.0
            d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
            return gamma if np.isfinite(gamma) else 0.0
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
            return max(0.0, min(95.0, concentration * 45 + log_exposure * 8))
        except:
            return 0.0
    
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
                    return strike1 + (strike2 - strike1) * (-gex1) / (gex2 - gex1)
            
            return min(all_strikes, key=lambda x: abs(x - current_price))
        except:
            return current_price
    
    def select_wall_from_aggregated_gex(
        self,
        gex_by_strike: pd.Series,
        current_price: float,
        category: str,
        is_put: bool = True,
    ) -> Tuple[float, str, float, List[Tuple[float, float]]]:
        """
        Select wall strike from aggregated GEX distribution.
        
        Returns: (wall_strike, method_used, dominance_ratio, top_5_strikes)
        """
        try:
            if gex_by_strike.empty:
                default = current_price * (0.95 if is_put else 1.05)
                return default, 'fallback', 0.0, []
            
            # Apply proximity filter
            max_dist = MAX_DISTANCE_BY_CATEGORY.get(category, MAX_DISTANCE_BY_CATEGORY['DEFAULT'])
            
            if is_put:
                min_strike = current_price * (1 - max_dist)
                relevant = gex_by_strike[(gex_by_strike.index < current_price) & 
                                         (gex_by_strike.index >= min_strike)]
            else:
                max_strike = current_price * (1 + max_dist)
                relevant = gex_by_strike[(gex_by_strike.index > current_price) & 
                                         (gex_by_strike.index <= max_strike)]
            
            # Expand if empty
            if relevant.empty:
                if is_put:
                    min_strike_exp = current_price * (1 - max_dist * 1.5)
                    relevant = gex_by_strike[(gex_by_strike.index < current_price) & 
                                             (gex_by_strike.index >= min_strike_exp)]
                else:
                    max_strike_exp = current_price * (1 + max_dist * 1.5)
                    relevant = gex_by_strike[(gex_by_strike.index > current_price) & 
                                             (gex_by_strike.index <= max_strike_exp)]
            
            if relevant.empty:
                if is_put:
                    relevant = gex_by_strike[gex_by_strike.index < current_price]
                else:
                    relevant = gex_by_strike[gex_by_strike.index > current_price]
            
            if relevant.empty:
                default = current_price * (0.95 if is_put else 1.05)
                return default, 'no_data', 0.0, []
            
            abs_gex = relevant.abs()
            total_gex = abs_gex.sum()
            
            if total_gex <= 0 or not np.isfinite(total_gex):
                nearest = float(relevant.index.max() if is_put else relevant.index.min())
                return nearest, 'no_exposure', 0.0, []
            
            # Get top 5 strikes
            top_5 = abs_gex.nlargest(5)
            top_5_list = [(float(k), float(v)) for k, v in top_5.items()]
            
            # Calculate dominance ratio
            dominance_ratio = float(abs_gex.max() / total_gex) if total_gex > 0 else 0
            
            # Method 1: Max GEX
            max_gex_wall = float(abs_gex.idxmax())
            
            # Method 2: Weighted centroid
            weighted_centroid = float((abs_gex * abs_gex.index).sum() / total_gex)
            
            # Method 3: Cumulative threshold (70%)
            if is_put:
                sorted_gex = abs_gex.sort_index(ascending=False)
            else:
                sorted_gex = abs_gex.sort_index(ascending=True)
            cumsum = sorted_gex.cumsum()
            threshold_strikes = cumsum[cumsum >= total_gex * 0.7]
            if not threshold_strikes.empty:
                cumulative_wall = float(threshold_strikes.index[-1] if is_put else threshold_strikes.index[0])
            else:
                cumulative_wall = max_gex_wall
            
            # Determine method based on dominance
            if dominance_ratio > 0.4:
                # Strong concentration - use max GEX
                wall = max_gex_wall
                method = 'max_gex'
            elif dominance_ratio > 0.2:
                # Moderate - use weighted combo
                wall = (PUT_WALL_WEIGHTS['max_gex'] * max_gex_wall +
                       PUT_WALL_WEIGHTS['weighted_centroid'] * weighted_centroid +
                       PUT_WALL_WEIGHTS['cumulative_threshold'] * cumulative_wall)
                method = 'weighted_combo'
            else:
                # Diffuse - use centroid
                wall = weighted_centroid
                method = 'centroid'
            
            return round(wall, 2), method, round(dominance_ratio, 3), top_5_list
            
        except Exception as e:
            logger.warning(f"Wall selection error: {e}")
            default = current_price * (0.95 if is_put else 1.05)
            return default, 'error', 0.0, []
    
    def calculate_max_pain(self, calls: pd.DataFrame, puts: pd.DataFrame) -> float:
        """Calculate max pain strike."""
        try:
            if calls is None or puts is None or calls.empty or puts.empty:
                return 0
            if 'openInterest' not in calls.columns or 'openInterest' not in puts.columns:
                return 0

            all_strikes = calls.index.union(puts.index).sort_values()
            if len(all_strikes) == 0:
                return 0

            call_oi = calls['openInterest'].reindex(all_strikes).fillna(0).astype(float)
            put_oi = puts['openInterest'].reindex(all_strikes).fillna(0).astype(float)
            strikes = all_strikes.astype(float)

            total_pain = []
            for strike in strikes:
                call_pain = sum((strike - k) * call_oi[k] * 100 for k in strikes if k < strike)
                put_pain = sum((k - strike) * put_oi[k] * 100 for k in strikes if k > strike)
                total_pain.append(call_pain + put_pain)

            min_idx = np.argmin(total_pain)
            return float(strikes[min_idx])
        except Exception as e:
            logger.warning(f"Max pain error: {e}")
            return 0


def get_market_regime() -> Tuple[str, float]:
    """Get current market regime based on VIX."""
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
    except:
        pass
    return "Normal Volatility", 15.5


def get_symbol_category(symbol: str) -> str:
    """Categorize symbols."""
    if symbol in ['^SPX', '^VIX']:
        return 'INDEX'
    elif symbol in ['QQQ', 'SPY', 'GLD', 'SLV']:
        return 'ETF'
    elif symbol in ['CVX', 'XOM', 'OXY']:
        return 'ENERGY'
    elif symbol in ['JPM', 'BAC']:
        return 'FINANCIAL'
    elif symbol in ['WMT', 'COST']:
        return 'CONSUMER'
    else:
        return 'TECH'


def aggregate_gex_for_bucket(
    ticker: yf.Ticker,
    options_dates: List[str],
    dte_range: Tuple[int, int],
    current_price: float,
    category: str,
    calculator: GammaWallCalculator,
) -> Optional[AggregatedGEX]:
    """
    Aggregate GEX across all expiries in a DTE bucket.
    
    This is the core fix: instead of picking one expiry, we sum GEX across
    all expiries in the bucket to get a more stable wall signal.
    """
    now = datetime.now()
    min_dte, max_dte = dte_range
    
    # Find all expiries in the bucket
    bucket_expiries = []
    for date_str in options_dates:
        try:
            exp_date = datetime.strptime(date_str, '%Y-%m-%d')
            dte = (exp_date - now).days
            if min_dte <= dte <= max_dte:
                bucket_expiries.append((date_str, dte))
        except:
            continue
    
    if not bucket_expiries:
        return None
    
    # Liquidity filters by category
    if category == 'INDEX':
        min_volume, min_oi = 50, 100
    elif category == 'ETF':
        min_volume, min_oi = 25, 50
    elif category in ['ENERGY', 'FINANCIAL', 'CONSUMER']:
        min_volume, min_oi = 5, 10
    else:
        min_volume, min_oi = 10, 25
    
    # Aggregate GEX across all expiries
    all_put_gex = {}
    all_call_gex = {}
    all_ivs = []
    expiries_used = []
    dte_list = []
    
    for exp_date, dte in bucket_expiries:
        try:
            chain = ticker.option_chain(exp_date)
            calls = chain.calls.copy()
            puts = chain.puts.copy()
            
            if calls.empty or puts.empty:
                continue
            
            # Normalize numeric columns
            for df in (calls, puts):
                for col in ('openInterest', 'volume', 'impliedVolatility'):
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                df['openInterest'] = df['openInterest'].fillna(0)
                df['volume'] = df['volume'].fillna(0)
            
            # Apply liquidity filter
            calls = calls[(calls['volume'] >= min_volume) | (calls['openInterest'] >= min_oi)].copy()
            puts = puts[(puts['volume'] >= min_volume) | (puts['openInterest'] >= min_oi)].copy()
            
            if calls.empty or puts.empty:
                continue
            
            calls.set_index('strike', inplace=True)
            puts.set_index('strike', inplace=True)
            
            # Calculate IV for this expiry
            calls_iv = calls['impliedVolatility'].median() if 'impliedVolatility' in calls.columns else 0.25
            puts_iv = puts['impliedVolatility'].median() if 'impliedVolatility' in puts.columns else 0.25
            exp_iv = (calls_iv + puts_iv) / 2 if pd.notna(calls_iv) and pd.notna(puts_iv) else 0.25
            exp_iv = max(0.05, min(2.0, exp_iv))
            all_ivs.append(exp_iv)
            
            T = dte / 365.0
            
            # Calculate gamma for each option
            for df in [calls, puts]:
                df['gamma'] = df.apply(
                    lambda row: calculator.calculate_gamma(current_price, row.name, T, RISK_FREE_RATE, exp_iv),
                    axis=1
                )
            
            # Calculate GEX - use OI, fall back to volume if OI is zero
            calls_eff_oi = calls['openInterest'].where(calls['openInterest'] > 0, calls['volume']).astype(float)
            puts_eff_oi = puts['openInterest'].where(puts['openInterest'] > 0, puts['volume']).astype(float)
            
            calls_gex = calls_eff_oi * calls['gamma'] * 100 * current_price
            puts_gex = puts_eff_oi * puts['gamma'] * 100 * current_price * -1
            
            # Aggregate into bucket totals
            for strike, gex in puts_gex.items():
                if np.isfinite(gex):
                    all_put_gex[strike] = all_put_gex.get(strike, 0) + gex
            
            for strike, gex in calls_gex.items():
                if np.isfinite(gex):
                    all_call_gex[strike] = all_call_gex.get(strike, 0) + gex
            
            expiries_used.append(exp_date)
            dte_list.append(dte)
            
        except Exception as e:
            logger.debug(f"Failed to process expiry {exp_date}: {e}")
            continue
    
    if not all_put_gex and not all_call_gex:
        return None
    
    return AggregatedGEX(
        put_gex_by_strike=pd.Series(all_put_gex).sort_index(),
        call_gex_by_strike=pd.Series(all_call_gex).sort_index(),
        expiries_used=expiries_used,
        dte_list=dte_list,
        median_iv=np.median(all_ivs) if all_ivs else 0.25
    )


def process_symbol(symbol: str, calculator: GammaWallCalculator) -> Optional[Dict]:
    """Process a single symbol using bucket-based aggregation."""
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
        
        results = {
            'symbol': symbol,
            'display_name': display_name,
            'category': category,
            'current_price': current_price,
            'timestamp': datetime.now().isoformat(),
            'bucket_debug': {},  # Debug info for each bucket
        }
        
        all_timeframe_data = {}
        
        # Process each bucket
        for bucket_name, dte_range in DTE_BUCKETS.items():
            agg = aggregate_gex_for_bucket(
                ticker, options_dates, dte_range, current_price, category, calculator
            )
            
            if agg is None or agg.put_gex_by_strike.empty:
                logger.warning(f"No data for {symbol} bucket {bucket_name}")
                continue
            
            # Select put wall from aggregated distribution
            put_wall, put_method, put_dominance, put_top5 = calculator.select_wall_from_aggregated_gex(
                agg.put_gex_by_strike, current_price, category, is_put=True
            )
            
            # Select call wall
            call_wall, call_method, call_dominance, call_top5 = calculator.select_wall_from_aggregated_gex(
                agg.call_gex_by_strike, current_price, category, is_put=False
            )
            
            # Store debug info
            results['bucket_debug'][bucket_name] = {
                'dte_range': dte_range,
                'expiries_included': agg.expiries_used,
                'dte_list': agg.dte_list,
                'num_expiries': len(agg.expiries_used),
                'put_strikes_analyzed': len(agg.put_gex_by_strike),
                'put_top_5': put_top5,
                'put_dominance_ratio': put_dominance,
                'put_wall': put_wall,
                'put_method': put_method,
                'call_wall': call_wall,
                'call_method': call_method,
                'median_iv': round(agg.median_iv * 100, 1),
            }
            
            # Calculate wall strengths
            put_strength = calculator.calculate_wall_strength(agg.put_gex_by_strike)
            call_strength = calculator.calculate_wall_strength(agg.call_gex_by_strike)
            
            # Calculate GEX totals
            put_gex_millions = agg.put_gex_by_strike.sum() / 1_000_000
            call_gex_millions = agg.call_gex_by_strike.sum() / 1_000_000
            
            all_timeframe_data[bucket_name] = {
                'put_wall': put_wall,
                'call_wall': call_wall,
                'put_strength': put_strength,
                'call_strength': call_strength,
                'put_gex_millions': put_gex_millions,
                'call_gex_millions': call_gex_millions,
                'iv_percent': agg.median_iv * 100,
                'dte_median': np.median(agg.dte_list) if agg.dte_list else 0,
                'put_gex_series': agg.put_gex_by_strike,
                'call_gex_series': agg.call_gex_by_strike,
            }
            
            # Map to output fields
            prefix = {'weekly': 'wk', 'swing': 'st', 'long': 'lt', 'quarterly': 'q'}[bucket_name]
            
            results.update({
                f'{prefix}_put_wall': put_wall,
                f'{prefix}_call_wall': call_wall,
                f'{prefix}_put_strength': put_strength,
                f'{prefix}_call_strength': call_strength,
                f'{prefix}_put_gex': put_gex_millions,
                f'{prefix}_call_gex': call_gex_millions,
                f'{prefix}_iv': agg.median_iv * 100,
                f'{prefix}_dte': int(np.median(agg.dte_list)) if agg.dte_list else 0,
            })
        
        # Calculate max pain from weekly bucket
        if 'weekly' in all_timeframe_data:
            # Get first expiry in weekly bucket for max pain
            try:
                for exp_date, dte in [(d, (datetime.strptime(d, '%Y-%m-%d') - datetime.now()).days) 
                                       for d in options_dates]:
                    if 1 <= dte <= 10:
                        chain = ticker.option_chain(exp_date)
                        calls_mp = chain.calls[['strike', 'openInterest']].copy()
                        puts_mp = chain.puts[['strike', 'openInterest']].copy()
                        calls_mp.set_index('strike', inplace=True)
                        puts_mp.set_index('strike', inplace=True)
                        results['max_pain'] = calculator.calculate_max_pain(calls_mp, puts_mp)
                        break
            except:
                results['max_pain'] = 0
        
        # Calculate SD levels from swing data
        if 'swing' in all_timeframe_data:
            swing_data = all_timeframe_data['swing']
            swing_iv = swing_data['iv_percent'] / 100
            swing_dte = swing_data['dte_median']
            T = swing_dte / 365.0 if swing_dte > 0 else 14/365.0
            base_move = current_price * swing_iv * np.sqrt(T)
            
            results.update({
                'lower_1sd': current_price - base_move,
                'upper_1sd': current_price + base_move,
                'lower_1_5sd': current_price - base_move * 1.5,
                'upper_1_5sd': current_price + base_move * 1.5,
                'lower_2sd': current_price - base_move * 2.0,
                'upper_2sd': current_price + base_move * 2.0,
                'swing_iv': swing_data['iv_percent'],
            })
        
        # Calculate gamma flip from weekly data
        if 'weekly' in all_timeframe_data:
            wk = all_timeframe_data['weekly']
            gamma_flip = calculator.calculate_gamma_flip(
                wk['call_gex_series'], wk['put_gex_series'], current_price
            )
            results['gamma_flip'] = gamma_flip
        else:
            results['gamma_flip'] = current_price
        
        return results
        
    except Exception as e:
        logger.error(f"Error processing {symbol}: {e}")
        return None


def format_for_pine_script(data: Dict) -> str:
    """Format data for Pine Script (36 fields)."""
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
        2.0,  # cp_ratio placeholder
        0.0,  # trend placeholder
        3.0,  # activity_score placeholder
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
    """Main execution with bucket-based aggregation."""
    start_time = datetime.now()
    calculator = GammaWallCalculator()
    regime, vix = get_market_regime()
    
    print(f"\n{'='*100}")
    print(f"Enhanced Gamma Wall Scanner v9.0 - BUCKET-BASED AGGREGATION")
    print(f"{'='*100}")
    print(f"Scan started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Market Regime: {regime} (VIX: {vix:.1f})")
    print(f"\nDTE Buckets:")
    for name, (min_dte, max_dte) in DTE_BUCKETS.items():
        print(f"  {name.upper():10}: DTE [{min_dte:3}, {max_dte:3}]")
    print(f"{'-'*100}")
    
    results = []
    failed_symbols = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_symbol = {executor.submit(process_symbol, s, calculator): s for s in SYMBOLS}
        
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                result = future.result(timeout=90)
                if result:
                    results.append(result)
                    
                    # Print summary with debug info
                    display = result.get('display_name', symbol)
                    price = result['current_price']
                    
                    st = result.get('st_put_wall', 0)
                    lt = result.get('lt_put_wall', 0)
                    q = result.get('q_put_wall', 0)
                    
                    # Check for duplicates
                    walls = [st, lt, q]
                    unique_walls = len(set([w for w in walls if w > 0]))
                    dup_flag = "⚠️DUP" if unique_walls < len([w for w in walls if w > 0]) else "✓"
                    
                    print(f"{dup_flag} {display:12}: ${price:>8.2f} | "
                          f"ST=${st:>7.0f} LT=${lt:>7.0f} Q=${q:>7.0f}")
                    
                    # Print bucket debug for first few symbols
                    if len(results) <= 3:
                        for bucket, debug in result.get('bucket_debug', {}).items():
                            print(f"     {bucket.upper():8}: {debug['num_expiries']} expiries, "
                                  f"{debug['put_strikes_analyzed']} strikes, "
                                  f"dom={debug['put_dominance_ratio']:.2f}, "
                                  f"method={debug['put_method']}")
                else:
                    failed_symbols.append(symbol)
            except Exception as e:
                failed_symbols.append(symbol)
                print(f"✗ {symbol}: {str(e)[:50]}")
    
    # Save results
    frontend_data = {
        'timestamp': datetime.now().isoformat(),
        'last_update': datetime.now().strftime("%b %d, %I:%M%p").lower(),
        'market_regime': regime,
        'vix': vix,
        'dte_buckets': {k: list(v) for k, v in DTE_BUCKETS.items()},
        'symbols': {}
    }
    
    for result in results:
        symbol_key = result.get('display_name', result['symbol']).replace('^', '')
        price = result['current_price']
        
        def calc_dist(level):
            return round(((price - level) / price) * 100, 2) if level > 0 else 0
        
        frontend_data['symbols'][symbol_key] = {
            'symbol': symbol_key,
            'current_price': price,
            'timestamp': result['timestamp'],
            'st_put_wall': result.get('st_put_wall', 0),
            'lt_put_wall': result.get('lt_put_wall', 0),
            'q_put_wall': result.get('q_put_wall', 0),
            'wk_put_wall': result.get('wk_put_wall', 0),
            'st_put_distance': calc_dist(result.get('st_put_wall', 0)),
            'lt_put_distance': calc_dist(result.get('lt_put_wall', 0)),
            'q_put_distance': calc_dist(result.get('q_put_wall', 0)),
            'st_call_wall': result.get('st_call_wall', 0),
            'lt_call_wall': result.get('lt_call_wall', 0),
            'q_call_wall': result.get('q_call_wall', 0),
            'gamma_flip': result.get('gamma_flip', price),
            'max_pain': result.get('max_pain', 0),
            'lower_1sd': result.get('lower_1sd', 0),
            'upper_1sd': result.get('upper_1sd', 0),
            'bucket_debug': result.get('bucket_debug', {}),
            'category': result.get('category', 'TECH'),
        }
    
    # Save to cache
    cache_dir = Path(__file__).parent.parent / 'cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = cache_dir / 'gamma_walls_data.json'
    with open(output_file, 'w') as f:
        json.dump(frontend_data, f, indent=2, default=str)
    
    print(f"\n✅ Data saved to: {output_file}")
    
    # Verification
    if 'SPX' in frontend_data['symbols']:
        spx = frontend_data['symbols']['SPX']
        print(f"\n🔍 SPX VERIFICATION:")
        print(f"   Price: ${spx['current_price']:.2f}")
        print(f"   ST Put: ${spx['st_put_wall']:.0f} ({spx['st_put_distance']:+.2f}%)")
        print(f"   LT Put: ${spx['lt_put_wall']:.0f} ({spx['lt_put_distance']:+.2f}%)")
        print(f"   Q Put:  ${spx['q_put_wall']:.0f} ({spx['q_put_distance']:+.2f}%)")
        
        # Check if walls are distinct
        walls = [spx['st_put_wall'], spx['lt_put_wall'], spx['q_put_wall']]
        unique = len(set([w for w in walls if w > 0]))
        if unique == 3:
            print(f"   ✅ All 3 walls are distinct!")
        else:
            print(f"   ⚠️ Only {unique}/3 unique walls")
    
    print(f"\n{'='*100}")
    print(f"SCAN COMPLETED - v9.0 BUCKET AGGREGATION")
    print(f"Time: {(datetime.now() - start_time).total_seconds():.1f}s")
    print(f"Success: {len(results)}, Failed: {len(failed_symbols)}")
    print(f"{'='*100}")


if __name__ == "__main__":
    main()
