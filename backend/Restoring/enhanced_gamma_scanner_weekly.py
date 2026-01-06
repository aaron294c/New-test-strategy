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
    'weekly': (1, 7),       # This week only
    'swing': (8, 21),       # Next 1-3 weeks (NO overlap with weekly)
    'long': (22, 50),       # Monthly (NO overlap with swing)
    'quarterly': (51, 120), # Quarterly (NO overlap with long)
}

RISK_FREE_RATE = 0.045
MAX_WORKERS = 8

# Category-specific max distance from spot (for filtering)
MAX_DISTANCE_BY_CATEGORY = {
    'INDEX': 0.10,      # 10% for indices
    'ETF': 0.12,        # 12% for ETFs
    'TECH': 0.15,       # 15% for tech stocks
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
        except:
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
        except:
            return current_price
    
    def select_put_wall_distinct(
        self,
        gex_by_strike: pd.Series,
        current_price: float,
        category: str,
        already_selected: List[float],
        bucket_name: str,
    ) -> Tuple[float, str, float, List[Tuple[float, float]]]:
        """
        Select put wall, preferring strikes DIFFERENT from already selected walls.
        Also allows walls that are "magnets" - potential support levels.
        """
        try:
            if gex_by_strike.empty:
                return current_price * 0.95, 'fallback', 0.0, []
            
            max_dist = MAX_DISTANCE_BY_CATEGORY.get(category, 0.15)
            
            # For puts, look at strikes BELOW current price
            min_strike = current_price * (1 - max_dist)
            relevant = gex_by_strike[(gex_by_strike.index < current_price) & 
                                     (gex_by_strike.index >= min_strike)]
            
            # Expand if empty
            if relevant.empty:
                relevant = gex_by_strike[gex_by_strike.index < current_price]
            
            if relevant.empty:
                return current_price * 0.95, 'no_data', 0.0, []
            
            abs_gex = relevant.abs()
            total_gex = abs_gex.sum()
            
            if total_gex <= 0:
                return float(relevant.index.max()), 'no_exposure', 0.0, []
            
            # Get top strikes by GEX
            top_strikes = abs_gex.nlargest(10)
            top_5_list = [(float(k), float(v)) for k, v in top_strikes.head(5).items()]
            
            # Calculate dominance
            dominance = float(abs_gex.max() / total_gex) if total_gex > 0 else 0
            
            # DISTINCT SELECTION: Prefer strikes NOT already selected
            # Calculate "uniqueness penalty" for each strike
            def uniqueness_score(strike):
                """Higher score = more unique (farther from already selected)"""
                if not already_selected:
                    return 1.0
                min_dist = min(abs(strike - s) for s in already_selected)
                # Normalize by price (so $5 difference means more for a $50 stock than $500)
                normalized_dist = min_dist / current_price
                return min(1.0, normalized_dist * 20)  # 5% difference = full score
            
            # Score each strike: GEX weight * uniqueness
            scored_strikes = []
            for strike, gex in top_strikes.items():
                gex_score = gex / top_strikes.max() if top_strikes.max() > 0 else 0
                unique_score = uniqueness_score(strike)
                
                # Combined score: prefer high GEX but also uniqueness
                # Weight uniqueness more for later buckets
                if bucket_name == 'weekly':
                    combined = gex_score * 0.9 + unique_score * 0.1
                elif bucket_name == 'swing':
                    combined = gex_score * 0.7 + unique_score * 0.3
                elif bucket_name == 'long':
                    combined = gex_score * 0.5 + unique_score * 0.5
                else:  # quarterly
                    combined = gex_score * 0.4 + unique_score * 0.6
                
                scored_strikes.append((strike, combined, gex_score, unique_score))
            
            # Sort by combined score
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
            
            # Simple max GEX for calls (less critical to differentiate)
            best_strike = float(abs_gex.idxmax())
            
            return round(best_strike, 2), 'max_gex', round(dominance, 3), top_5_list
            
        except:
            return current_price * 1.05, 'error', 0.0, []
    
    def calculate_max_pain_realistic(self, calls: pd.DataFrame, puts: pd.DataFrame, 
                                      current_price: float) -> float:
        """
        FIXED: Calculate max pain with realistic bounds (within 5% of spot for weekly).
        Max pain should be NEAR current price, not 50%+ away.
        """
        try:
            if calls is None or puts is None or calls.empty or puts.empty:
                return current_price
            
            if 'openInterest' not in calls.columns or 'openInterest' not in puts.columns:
                return current_price
            
            # Limit to strikes within 10% of current price for realistic max pain
            min_strike = current_price * 0.90
            max_strike = current_price * 1.10
            
            calls_filtered = calls[(calls.index >= min_strike) & (calls.index <= max_strike)]
            puts_filtered = puts[(puts.index >= min_strike) & (puts.index <= max_strike)]
            
            if calls_filtered.empty and puts_filtered.empty:
                # Fallback to wider range
                min_strike = current_price * 0.85
                max_strike = current_price * 1.15
                calls_filtered = calls[(calls.index >= min_strike) & (calls.index <= max_strike)]
                puts_filtered = puts[(puts.index >= min_strike) & (puts.index <= max_strike)]
           