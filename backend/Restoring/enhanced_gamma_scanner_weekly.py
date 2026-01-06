#!/usr/bin/env python3
"""
Enhanced Gamma Wall Scanner v9.1 - Distinct Wall Detection
===========================================================

FIXES in v9.1:
- Non-overlapping DTE buckets to prevent wall duplication
- Smarter wall selection that prefers DIFFERENT strikes across timeframes
- Fixed max pain calculation (was selecting impossibly far strikes)
- Walls can now be ABOVE current price (resistance becomes target)
- Better handling of concentrated GEX distributions

DTE Buckets (NON-OVERLAPPING):
- Weekly (WK): DTE [1, 7]    - This week's pin
- Swing (ST):  DTE [8, 21]   - 1-3 week gamma walls  
- Long (LT):   DTE [22, 50]  - Monthly structure
- Quarterly (Q): DTE [51, 120] - Long-term support

Usage: python enhanced_gamma_scanner_weekly.py
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from scipy.stats import norm
import warnings
import logging
from typing import Dict, Optional, Tuple, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
from dataclasses import dataclass

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === CONFIGURATION ===
SYMBOLS = [
    'SPY', 'QQQ', '^SPX', '^VIX',
    'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'TSLA', 'NFLX',
    'BRK-B', 'AVGO', 'LLY', 'UNH', 'TSM', 'WMT', 'COST',
    'XOM', 'CVX', 'OXY', 'JPM', 'BAC',
    'GLD', 'SLV',
]

# === NON-OVERLAPPING DTE BUCKETS ===
DTE_BUCKETS = {
    'weekly': (1, 7),
    'swing': (8, 21),
    'long': (22, 50),
    'quarterly': (51, 120),
}

RISK_FREE_RATE = 0.045
MAX_WORKERS = 8

# Back-compat for services that import scanner constants.
# v9.x uses bucket aggregation and does not require these weights internally,
# but downstream code expects the symbol to exist.
PUT_WALL_WEIGHTS = {
    "max_gex": 0.40,
    "weighted_centroid": 0.35,
    "cumulative_threshold": 0.25,
}

MAX_DISTANCE_BY_CATEGORY = {
    'INDEX': 0.10,
    'ETF': 0.12,
    'TECH': 0.15,
    'ENERGY': 0.12,
    'FINANCIAL': 0.12,
    'CONSUMER': 0.12,
    'DEFAULT': 0.15
}

SYMBOL_DISPLAY_NAMES = {
    '^SPX': 'SPX', '^VIX': 'VIX', 'QQQ': 'QQQ(NDX)',
}


@dataclass
class AggregatedGEX:
    """Aggregated GEX data for a bucket."""
    put_gex_by_strike: pd.Series
    call_gex_by_strike: pd.Series
    expiries_used: List[str]
    dte_list: List[int]
    median_iv: float


class GammaWallCalculator:
    """Calculator for gamma walls and related metrics."""
    
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
        except Exception:
            return 0.0
    
    def calculate_wall_strength(self, gex_series: pd.Series) -> float:
        """Calculate wall strength."""
        try:
            if gex_series.empty:
                return 0.0
            max_exp = gex_series.abs().max()
            total_exp = gex_series.abs().sum()
            if total_exp == 0:
                return 0.0
            concentration = max_exp / total_exp
            return max(0.0, min(95.0, concentration * 45 + np.log10(max_exp + 1) * 8))
        except Exception:
            return 0.0
    
    def calculate_gamma_flip(self, calls_gex: pd.Series, puts_gex: pd.Series, 
                             current_price: float) -> float:
        """Calculate gamma flip point."""
        try:
            all_strikes = calls_gex.index.union(puts_gex.index)
            net_gex = pd.Series(0.0, index=all_strikes)
            for strike in calls_gex.index:
                net_gex[strike] += calls_gex.get(strike, 0)
            for strike in puts_gex.index:
                net_gex[strike] += puts_gex.get(strike, 0)
            net_gex = net_gex.sort_index()
            for i in range(len(net_gex) - 1):
                if net_gex.iloc[i] * net_gex.iloc[i + 1] < 0:
                    s1, g1 = net_gex.index[i], net_gex.iloc[i]
                    s2, g2 = net_gex.index[i + 1], net_gex.iloc[i + 1]
                    return s1 + (s2 - s1) * (-g1) / (g2 - g1)
            return min(all_strikes, key=lambda x: abs(x - current_price))
        except Exception:
            return current_price
    
    def select_put_wall_distinct(
        self,
        gex_by_strike: pd.Series,
        current_price: float,
        category: str,
        already_selected: List[float],
        bucket_name: str,
    ) -> Tuple[float, str, float, List[Tuple[float, float]]]:
        """Select put wall, preferring strikes DIFFERENT from already selected walls."""
        try:
            if gex_by_strike.empty:
                return current_price * 0.95, 'fallback', 0.0, []
            
            max_dist = MAX_DISTANCE_BY_CATEGORY.get(category, 0.15)
            min_strike = current_price * (1 - max_dist)
            relevant = gex_by_strike[(gex_by_strike.index < current_price) & 
                                     (gex_by_strike.index >= min_strike)]
            
            if relevant.empty:
                relevant = gex_by_strike[gex_by_strike.index < current_price]
            
            if relevant.empty:
                return current_price * 0.95, 'no_data', 0.0, []
            
            abs_gex = relevant.abs()
            total_gex = abs_gex.sum()
            
            if total_gex <= 0:
                return float(relevant.index.max()), 'no_exposure', 0.0, []
            
            top_strikes = abs_gex.nlargest(10)
            top_5_list = [(float(k), float(v)) for k, v in top_strikes.head(5).items()]
            dominance = float(abs_gex.max() / total_gex) if total_gex > 0 else 0
            
            def uniqueness_score(strike):
                if not already_selected:
                    return 1.0
                min_d = min(abs(strike - s) for s in already_selected)
                normalized_dist = min_d / current_price
                return min(1.0, normalized_dist * 20)
            
            scored_strikes = []
            for strike, gex in top_strikes.items():
                gex_score = gex / top_strikes.max() if top_strikes.max() > 0 else 0
                unique_score = uniqueness_score(strike)
                
                if bucket_name == 'weekly':
                    combined = gex_score * 0.9 + unique_score * 0.1
                elif bucket_name == 'swing':
                    combined = gex_score * 0.7 + unique_score * 0.3
                elif bucket_name == 'long':
                    combined = gex_score * 0.5 + unique_score * 0.5
                else:
                    combined = gex_score * 0.4 + unique_score * 0.6
                
                scored_strikes.append((strike, combined, gex_score, unique_score))
            
            scored_strikes.sort(key=lambda x: x[1], reverse=True)
            
            if scored_strikes:
                best_strike = scored_strikes[0][0]
                method = 'distinct_gex' if scored_strikes[0][3] > 0.3 else 'max_gex'
            else:
                best_strike = float(abs_gex.idxmax())
                method = 'max_gex'
            
            return round(best_strike, 2), method, round(dominance, 3), top_5_list
            
        except Exception as e:
            logger.warning(f"Put wall selection error: {e}")
            return current_price * 0.95, 'error', 0.0, []
    
    def select_call_wall_distinct(
        self,
        gex_by_strike: pd.Series,
        current_price: float,
        category: str,
        already_selected: List[float],
        bucket_name: str,
    ) -> Tuple[float, str, float, List[Tuple[float, float]]]:
        """Select call wall with distinctness preference."""
        try:
            if gex_by_strike.empty:
                return current_price * 1.05, 'fallback', 0.0, []
            
            max_dist = MAX_DISTANCE_BY_CATEGORY.get(category, 0.15)
            max_strike = current_price * (1 + max_dist)
            
            relevant = gex_by_strike[(gex_by_strike.index > current_price) & 
                                     (gex_by_strike.index <= max_strike)]
            
            if relevant.empty:
                relevant = gex_by_strike[gex_by_strike.index > current_price]
            
            if relevant.empty:
                return current_price * 1.05, 'no_data', 0.0, []
            
            abs_gex = relevant.abs()
            total_gex = abs_gex.sum()
            
            if total_gex <= 0:
                return float(relevant.index.min()), 'no_exposure', 0.0, []
            
            top_strikes = abs_gex.nlargest(5)
            top_5_list = [(float(k), float(v)) for k, v in top_strikes.items()]
            dominance = float(abs_gex.max() / total_gex)
            best_strike = float(abs_gex.idxmax())
            
            return round(best_strike, 2), 'max_gex', round(dominance, 3), top_5_list
            
        except Exception:
            return current_price * 1.05, 'error', 0.0, []
    
    def calculate_max_pain_realistic(self, calls: pd.DataFrame, puts: pd.DataFrame, 
                                      current_price: float) -> float:
        """Calculate max pain with realistic bounds."""
        try:
            if calls is None or puts is None or calls.empty or puts.empty:
                return current_price
            
            if 'openInterest' not in calls.columns or 'openInterest' not in puts.columns:
                return current_price
            
            min_strike = current_price * 0.90
            max_strike = current_price * 1.10
            
            calls_filtered = calls[(calls.index >= min_strike) & (calls.index <= max_strike)]
            puts_filtered = puts[(puts.index >= min_strike) & (puts.index <= max_strike)]
            
            if calls_filtered.empty and puts_filtered.empty:
                min_strike = current_price * 0.85
                max_strike = current_price * 1.15
                calls_filtered = calls[(calls.index >= min_strike) & (calls.index <= max_strike)]
                puts_filtered = puts[(puts.index >= min_strike) & (puts.index <= max_strike)]
            
            all_strikes = calls_filtered.index.union(puts_filtered.index).sort_values()
            if len(all_strikes) == 0:
                return current_price
            
            call_oi = calls_filtered['openInterest'].reindex(all_strikes).fillna(0).astype(float)
            put_oi = puts_filtered['openInterest'].reindex(all_strikes).fillna(0).astype(float)
            
            total_pain = []
            for strike in all_strikes:
                call_pain = sum((strike - k) * call_oi.get(k, 0) * 100 
                               for k in all_strikes if k < strike)
                put_pain = sum((k - strike) * put_oi.get(k, 0) * 100 
                              for k in all_strikes if k > strike)
                total_pain.append(call_pain + put_pain)
            
            if not total_pain:
                return current_price
            
            min_idx = np.argmin(total_pain)
            max_pain = float(all_strikes[min_idx])
            
            if abs(max_pain - current_price) / current_price > 0.10:
                return float(min(all_strikes, key=lambda x: abs(x - current_price)))
            
            return max_pain
            
        except Exception as e:
            logger.warning(f"Max pain error: {e}")
            return current_price


def get_market_regime() -> Tuple[str, float]:
    """Get market regime from VIX."""
    try:
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="5d")
        if not hist.empty:
            current_vix = hist['Close'].iloc[-1]
            if current_vix >= 25:
                return "High Volatility", current_vix
            elif current_vix <= 15:
                return "Low Volatility", current_vix
            return "Normal Volatility", current_vix
    except Exception:
        pass
    return "Normal Volatility", 15.5


def get_symbol_category(symbol: str) -> str:
    """Categorize symbol."""
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
    return 'TECH'


def aggregate_gex_for_bucket(
    ticker: yf.Ticker,
    options_dates: List[str],
    dte_range: Tuple[int, int],
    current_price: float,
    category: str,
    calculator: GammaWallCalculator,
) -> Optional[AggregatedGEX]:
    """Aggregate GEX across all expiries in a DTE bucket."""
    now = datetime.now()
    min_dte, max_dte = dte_range
    
    bucket_expiries = []
    for date_str in options_dates:
        try:
            exp_date = datetime.strptime(date_str, '%Y-%m-%d')
            dte = (exp_date - now).days
            if min_dte <= dte <= max_dte:
                bucket_expiries.append((date_str, dte))
        except Exception:
            continue
    
    if not bucket_expiries:
        return None
    
    if category == 'INDEX':
        min_volume, min_oi = 50, 100
    elif category == 'ETF':
        min_volume, min_oi = 25, 50
    elif category in ['ENERGY', 'FINANCIAL', 'CONSUMER']:
        min_volume, min_oi = 5, 10
    else:
        min_volume, min_oi = 10, 25
    
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
            
            for df in (calls, puts):
                for col in ('openInterest', 'volume', 'impliedVolatility'):
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                df['openInterest'] = df['openInterest'].fillna(0)
                df['volume'] = df['volume'].fillna(0)
            
            calls = calls[(calls['volume'] >= min_volume) | (calls['openInterest'] >= min_oi)].copy()
            puts = puts[(puts['volume'] >= min_volume) | (puts['openInterest'] >= min_oi)].copy()
            
            if calls.empty or puts.empty:
                continue
            
            calls.set_index('strike', inplace=True)
            puts.set_index('strike', inplace=True)
            
            calls_iv = calls['impliedVolatility'].median() if 'impliedVolatility' in calls.columns else 0.25
            puts_iv = puts['impliedVolatility'].median() if 'impliedVolatility' in puts.columns else 0.25
            exp_iv = (calls_iv + puts_iv) / 2 if pd.notna(calls_iv) and pd.notna(puts_iv) else 0.25
            exp_iv = max(0.05, min(2.0, exp_iv))
            all_ivs.append(exp_iv)
            
            T = dte / 365.0
            
            for df in [calls, puts]:
                df['gamma'] = df.apply(
                    lambda row: calculator.calculate_gamma(current_price, row.name, T, RISK_FREE_RATE, exp_iv),
                    axis=1
                )
            
            calls_eff_oi = calls['openInterest'].where(calls['openInterest'] > 0, calls['volume']).astype(float)
            puts_eff_oi = puts['openInterest'].where(puts['openInterest'] > 0, puts['volume']).astype(float)
            
            calls_gex = calls_eff_oi * calls['gamma'] * 100 * current_price
            puts_gex = puts_eff_oi * puts['gamma'] * 100 * current_price * -1
            
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
    """Process symbol with distinct wall selection."""
    try:
        category = get_symbol_category(symbol)
        display_name = SYMBOL_DISPLAY_NAMES.get(symbol, symbol)
        logger.info(f"Processing {display_name} ({category})...")
        
        ticker = yf.Ticker(symbol)
        
        current_price = None
        try:
            info = ticker.info
            current_price = info.get('regularMarketPrice') or info.get('currentPrice') or info.get('previousClose')
        except Exception:
            pass
        
        if not current_price or current_price <= 0:
            try:
                hist = ticker.history(period="2d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
            except Exception:
                pass
        
        if not current_price or current_price <= 0:
            logger.error(f"No price for {symbol}")
            return None
        
        current_price = float(current_price)
        
        try:
            options_dates = ticker.options
        except Exception:
            return None
        
        if not options_dates:
            return None
        
        results = {
            'symbol': symbol,
            'display_name': display_name,
            'category': category,
            'current_price': current_price,
            'timestamp': datetime.now().isoformat(),
            'bucket_debug': {},
        }
        
        all_timeframe_data = {}
        already_selected_put_walls = []
        
        bucket_order = ['weekly', 'swing', 'long', 'quarterly']
        
        for bucket_name in bucket_order:
            dte_range = DTE_BUCKETS[bucket_name]
            
            agg = aggregate_gex_for_bucket(
                ticker, options_dates, dte_range, current_price, category, calculator
            )
            
            if agg is None or agg.put_gex_by_strike.empty:
                continue
            
            put_wall, put_method, put_dominance, put_top5 = calculator.select_put_wall_distinct(
                agg.put_gex_by_strike, current_price, category, 
                already_selected_put_walls, bucket_name
            )
            
            already_selected_put_walls.append(put_wall)
            
            call_wall, call_method, call_dominance, call_top5 = calculator.select_call_wall_distinct(
                agg.call_gex_by_strike, current_price, category, [], bucket_name
            )
            
            results['bucket_debug'][bucket_name] = {
                'dte_range': dte_range,
                'num_expiries': len(agg.expiries_used),
                'put_strikes': len(agg.put_gex_by_strike),
                'put_top_5': put_top5,
                'put_dominance': put_dominance,
                'put_wall': put_wall,
                'put_method': put_method,
            }
            
            put_strength = calculator.calculate_wall_strength(agg.put_gex_by_strike)
            call_strength = calculator.calculate_wall_strength(agg.call_gex_by_strike)
            
            all_timeframe_data[bucket_name] = {
                'put_wall': put_wall,
                'call_wall': call_wall,
                'put_strength': put_strength,
                'call_strength': call_strength,
                'iv_percent': agg.median_iv * 100,
                'dte_median': np.median(agg.dte_list) if agg.dte_list else 0,
                'put_gex_series': agg.put_gex_by_strike,
                'call_gex_series': agg.call_gex_by_strike,
            }
            
            prefix = {'weekly': 'wk', 'swing': 'st', 'long': 'lt', 'quarterly': 'q'}[bucket_name]
            
            results.update({
                f'{prefix}_put_wall': put_wall,
                f'{prefix}_call_wall': call_wall,
                f'{prefix}_put_strength': put_strength,
                f'{prefix}_call_strength': call_strength,
                f'{prefix}_iv': agg.median_iv * 100,
                f'{prefix}_dte': int(np.median(agg.dte_list)) if agg.dte_list else 0,
            })
        
        # Max pain
        if 'weekly' in all_timeframe_data:
            try:
                for d in options_dates:
                    dte = (datetime.strptime(d, '%Y-%m-%d') - datetime.now()).days
                    if 1 <= dte <= 7:
                        chain = ticker.option_chain(d)
                        calls_mp = chain.calls[['strike', 'openInterest']].copy()
                        puts_mp = chain.puts[['strike', 'openInterest']].copy()
                        calls_mp.set_index('strike', inplace=True)
                        puts_mp.set_index('strike', inplace=True)
                        results['max_pain'] = calculator.calculate_max_pain_realistic(
                            calls_mp, puts_mp, current_price
                        )
                        break
            except Exception:
                results['max_pain'] = current_price
        
        # SD levels
        if 'swing' in all_timeframe_data:
            swing = all_timeframe_data['swing']
            iv = swing['iv_percent'] / 100
            dte = swing['dte_median']
            T = dte / 365.0 if dte > 0 else 14/365.0
            move = current_price * iv * np.sqrt(T)
            results.update({
                'lower_1sd': current_price - move,
                'upper_1sd': current_price + move,
                'lower_2sd': current_price - move * 2,
                'upper_2sd': current_price + move * 2,
            })
        
        # Gamma flip
        if 'weekly' in all_timeframe_data:
            wk = all_timeframe_data['weekly']
            results['gamma_flip'] = calculator.calculate_gamma_flip(
                wk['call_gex_series'], wk['put_gex_series'], current_price
            )
        else:
            results['gamma_flip'] = current_price
        
        return results
        
    except Exception as e:
        logger.error(f"Error processing {symbol}: {e}")
        return None


def main():
    """Main execution."""
    start_time = datetime.now()
    calculator = GammaWallCalculator()
    regime, vix = get_market_regime()
    
    print(f"\n{'='*100}")
    print(f"Gamma Wall Scanner v9.1 - DISTINCT WALL DETECTION")
    print(f"{'='*100}")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Market: {regime} (VIX: {vix:.1f})")
    print(f"{'-'*100}")
    
    results = []
    failed = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_symbol, s, calculator): s for s in SYMBOLS}
        
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                result = future.result(timeout=90)
                if result:
                    results.append(result)
                    display = result.get('display_name', symbol)
                    price = result['current_price']
                    st = result.get('st_put_wall', 0)
                    lt = result.get('lt_put_wall', 0)
                    q = result.get('q_put_wall', 0)
                    
                    walls = [st, lt, q]
                    unique = len(set([w for w in walls if w > 0]))
                    flag = "✓" if unique >= 2 else "⚠️"
                    
                    print(f"{flag} {display:12}: ${price:>8.2f} | ST=${st:>7.0f} LT=${lt:>7.0f} Q=${q:>7.0f}")
                else:
                    failed.append(symbol)
            except Exception as e:
                failed.append(symbol)
                logger.warning(f"Failed {symbol}: {e}")
    
    # Save results
    frontend_data = {
        'timestamp': datetime.now().isoformat(),
        'last_update': datetime.now().strftime("%b %d, %I:%M%p").lower(),
        'market_regime': regime,
        'vix': vix,
        'symbols': {}
    }
    
    for result in results:
        key = result.get('display_name', result['symbol']).replace('^', '')
        price = result['current_price']
        
        def dist(level):
            return round(((price - level) / price) * 100, 2) if level > 0 else 0
        
        frontend_data['symbols'][key] = {
            'symbol': key,
            'current_price': price,
            'st_put_wall': result.get('st_put_wall', 0),
            'lt_put_wall': result.get('lt_put_wall', 0),
            'q_put_wall': result.get('q_put_wall', 0),
            'wk_put_wall': result.get('wk_put_wall', 0),
            'st_put_distance': dist(result.get('st_put_wall', 0)),
            'lt_put_distance': dist(result.get('lt_put_wall', 0)),
            'q_put_distance': dist(result.get('q_put_wall', 0)),
            'gamma_flip': result.get('gamma_flip', price),
            'max_pain': result.get('max_pain', price),
            'category': result.get('category', 'TECH'),
        }
    
    # Save
    cache_dir = Path(__file__).parent.parent / 'cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = cache_dir / 'gamma_walls_data.json'
    with open(output_file, 'w') as f:
        json.dump(frontend_data, f, indent=2, default=str)
    
    print(f"\n✅ Saved to: {output_file}")
    print(f"Completed: {len(results)} symbols, {len(failed)} failed")


if __name__ == "__main__":
    main()
