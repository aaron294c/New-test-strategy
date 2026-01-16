#!/usr/bin/env python3
"""
Gamma Risk Distance Calculator v2.0
====================================
REVAMPED calculations inspired by PineScript indicators:
- GEX Options Flow Pro
- Enhanced Gamma Wall Scanner v8.0

Key Improvements:
1. Wall Strength: concentration * 45 + log10(exposure) * 8
2. Consistent distance formula: (level - price) / price * 100
3. True max pain calculation with pain heatmap data
4. Pin risk assessment (HIGH/MEDIUM/LOW)
5. GEX-weighted wall identification
6. Regime-aware strength adjustments
7. Multiple wall calculation methods with confidence scoring
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from scipy.stats import norm
import warnings
import logging
from typing import Dict, Optional, Tuple, List, Any
from dataclasses import dataclass, asdict, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION - Matching PineScript timeframes
# ═══════════════════════════════════════════════════════════════════════════════
SHORTEST_DAYS = 7      # Weekly / Shortest term (0-7 DTE)
SHORT_DAYS = 14        # Swing / Short term (7-14 DTE)
MEDIUM_DAYS = 30       # Long / Medium term (~30 DTE)
LONG_DAYS = 90         # Quarterly / Long term (~90 DTE)
RISK_FREE_RATE = 0.045

# Regime thresholds (from Enhanced Gamma Wall Scanner)
VIX_HIGH_THRESHOLD = 25.0
VIX_LOW_THRESHOLD = 15.0

# Wall strength parameters
CONCENTRATION_WEIGHT = 45
LOG_EXPOSURE_WEIGHT = 8
MIN_STRENGTH = 0.0
MAX_STRENGTH = 95.0

# Pin risk thresholds
PIN_RISK_HIGH_PCT = 2.0
PIN_RISK_MED_PCT = 5.0


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════
@dataclass
class RiskDistanceLevel:
    """Single risk distance level with all metrics (matches frontend type)."""
    strike: float
    distance_pct: float      # Positive = above price, Negative = below price
    distance_pts: float
    strength: float          # 0-95 based on GEX concentration
    dte: int
    gex_value: float = 0.0   # Raw GEX at this strike
    iv_at_strike: float = 0.0


@dataclass
class MaxPainData:
    """Max pain calculation results with pain distribution."""
    strike: float
    distance_pct: float
    distance_pts: float
    total_pain_value: float
    call_pain: float
    put_pain: float
    timeframe: str
    pin_risk: str = "LOW"    # HIGH, MEDIUM, LOW
    pain_ratio: float = 0.0  # call_pain / put_pain


@dataclass
class WeightedWallData:
    """Weighted wall data with multiple calculation methods."""
    max_gex_wall: float
    weighted_centroid: float
    cumulative_threshold: float
    recommended_wall: float
    method_used: str
    confidence: str          # high, medium, low
    gex_concentration: float = 0.0


@dataclass
class GammaFlipData:
    """Gamma flip point data."""
    strike: float
    distance_pct: float
    distance_pts: float
    net_gex_above: float = 0.0   # Net GEX above flip (positive = bullish)
    net_gex_below: float = 0.0   # Net GEX below flip


@dataclass
class SDLevels:
    """Standard deviation levels based on IV."""
    lower_1sd: float
    upper_1sd: float
    lower_1_5sd: float
    upper_1_5sd: float
    lower_2sd: float
    upper_2sd: float
    iv_used: float
    dte: int


@dataclass
class MarketRegime:
    """Market regime detection data."""
    regime: str              # "High Volatility", "Low Volatility", "Normal Volatility"
    vix_value: float
    is_estimated: bool = False
    strength_multiplier: float = 1.0


@dataclass
class SymbolRiskProfile:
    """Complete risk distance profile for a symbol."""
    symbol: str
    current_price: float
    timestamp: str

    # Put walls by timeframe (ST = short-term, LT = long-term, Q = quarterly)
    put_walls: Dict[str, RiskDistanceLevel] = field(default_factory=dict)
    call_walls: Dict[str, RiskDistanceLevel] = field(default_factory=dict)

    # Max pain by timeframe
    max_pain: Dict[str, MaxPainData] = field(default_factory=dict)

    # Weighted walls (enhanced accuracy)
    weighted_walls: Dict[str, WeightedWallData] = field(default_factory=dict)

    # Gamma flip
    gamma_flip: Optional[GammaFlipData] = None

    # SD levels
    sd_levels: Optional[SDLevels] = None

    # Market regime
    regime: Optional[MarketRegime] = None

    # Summary metrics
    summary: Dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# GAMMA RISK CALCULATOR - Core calculation engine
# ═══════════════════════════════════════════════════════════════════════════════
class GammaRiskCalculatorV2:
    """
    Enhanced gamma calculator with PineScript-inspired calculations.

    Key formulas from PineScript:
    - GEX = OpenInterest * Gamma * 100 * CurrentPrice
    - Strength = concentration * 45 + log10(exposure) * 8
    - Distance = (level - price) / price * 100
    """

    def __init__(self, regime: Optional[MarketRegime] = None):
        self.regime = regime or MarketRegime("Normal Volatility", 16.0)
        self.errors: List[str] = []

    # ───────────────────────────────────────────────────────────────────────────
    # BLACK-SCHOLES GAMMA (from Enhanced Gamma Wall Scanner)
    # ───────────────────────────────────────────────────────────────────────────
    def calculate_gamma(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        Calculate Black-Scholes gamma.

        From PineScript bs_gamma_simple:
        d1 = (ln(S/K) + 0.5 * vol^2 * T) / (vol * sqrt(T))
        gamma = exp(-0.5 * d1^2) / (S * vol * sqrt(2 * pi * T))
        """
        try:
            if any(x <= 0 for x in [S, K, T]) or sigma <= 0:
                return 0.0

            d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))

            return gamma if not (np.isnan(gamma) or np.isinf(gamma)) else 0.0
        except Exception as e:
            self.errors.append(f"Gamma calc error: {e}")
            return 0.0

    # ───────────────────────────────────────────────────────────────────────────
    # GEX CALCULATION (from GEX Options Flow Pro)
    # ───────────────────────────────────────────────────────────────────────────
    def calculate_gex(self, open_interest: float, gamma: float,
                      current_price: float, is_put: bool = False) -> float:
        """
        Calculate Gamma Exposure (GEX).

        From PineScript:
        GEX = OpenInterest * Gamma * 100 * Current_Price
        For Puts: multiply by -1
        """
        gex = open_interest * gamma * 100 * current_price
        return gex * -1 if is_put else gex

    # ───────────────────────────────────────────────────────────────────────────
    # WALL STRENGTH (from Enhanced Gamma Wall Scanner)
    # ───────────────────────────────────────────────────────────────────────────
    def calculate_wall_strength(self, gex_series: pd.Series,
                                 apply_regime_adjustment: bool = True) -> float:
        """
        Calculate wall strength using PineScript formula:
        strength = concentration * 45 + log10(exposure) * 8

        Range: 0-95%
        """
        try:
            if gex_series.empty:
                return 0.0

            max_exposure = gex_series.abs().max()
            total_exposure = gex_series.abs().sum()

            if total_exposure == 0:
                return 0.0

            # Concentration: how much of total GEX is at the max strike
            concentration = max_exposure / total_exposure

            # Log exposure: scale the absolute magnitude
            log_exposure = np.log10(max_exposure + 1)

            # Base strength formula from PineScript
            strength = concentration * CONCENTRATION_WEIGHT + log_exposure * LOG_EXPOSURE_WEIGHT

            # Apply regime adjustment if enabled
            if apply_regime_adjustment and self.regime:
                strength *= self.regime.strength_multiplier

            return max(MIN_STRENGTH, min(MAX_STRENGTH, strength))

        except Exception as e:
            self.errors.append(f"Strength calc error: {e}")
            return 0.0

    # ───────────────────────────────────────────────────────────────────────────
    # WEIGHTED WALL CALCULATION (3 methods from PineScript)
    # ───────────────────────────────────────────────────────────────────────────
    def calculate_weighted_wall(self, gex_series: pd.Series, current_price: float,
                                 is_put: bool = True, threshold_pct: float = 0.7) -> WeightedWallData:
        """
        Calculate weighted wall using three methods:

        1. Max GEX: Strike with highest absolute gamma exposure
        2. Weighted Centroid: Center of mass of GEX distribution
        3. Cumulative Threshold: Strike where X% of GEX accumulates

        Selection logic (from Enhanced Gamma Wall Scanner):
        - High concentration (>50%): Use max_gex
        - Moderate (30-50%): Use weighted_centroid
        - Dispersed (<30%): Use cumulative_threshold
        """
        try:
            if gex_series.empty:
                default = current_price * (0.95 if is_put else 1.05)
                return WeightedWallData(default, default, default, default, 'fallback', 'low', 0.0)

            # Filter to relevant strikes (below price for puts, above for calls)
            if is_put:
                relevant = gex_series[gex_series.index < current_price]
            else:
                relevant = gex_series[gex_series.index > current_price]

            if relevant.empty:
                relevant = gex_series

            abs_gex = relevant.abs()
            total_gex = abs_gex.sum()

            if total_gex == 0:
                default = current_price * (0.95 if is_put else 1.05)
                return WeightedWallData(default, default, default, default, 'no_data', 'low', 0.0)

            # Method 1: Max GEX (strike with highest exposure)
            max_gex_wall = float(abs_gex.idxmax())

            # Method 2: Weighted Centroid (center of mass)
            weighted_centroid = float((abs_gex * abs_gex.index).sum() / total_gex)

            # Method 3: Cumulative Threshold
            sorted_gex = abs_gex.sort_index(ascending=not is_put)
            cumsum = sorted_gex.cumsum()
            threshold_value = total_gex * threshold_pct
            threshold_strikes = cumsum[cumsum >= threshold_value]

            if not threshold_strikes.empty:
                cumulative_threshold = float(threshold_strikes.index[-1] if is_put else threshold_strikes.index[0])
            else:
                cumulative_threshold = max_gex_wall

            # Calculate concentration for method selection
            gex_concentration = float(abs_gex.max() / total_gex)

            # Select best method based on concentration (PineScript logic)
            if gex_concentration > 0.5:
                recommended = max_gex_wall
                method = 'max_gex'
                confidence = 'high'
            elif gex_concentration > 0.3:
                recommended = weighted_centroid
                method = 'weighted_centroid'
                confidence = 'medium'
            else:
                recommended = cumulative_threshold
                method = 'cumulative_threshold'
                confidence = 'medium'

            return WeightedWallData(
                max_gex_wall=max_gex_wall,
                weighted_centroid=weighted_centroid,
                cumulative_threshold=cumulative_threshold,
                recommended_wall=recommended,
                method_used=method,
                confidence=confidence,
                gex_concentration=gex_concentration
            )

        except Exception as e:
            self.errors.append(f"Weighted wall error: {e}")
            default = current_price * (0.95 if is_put else 1.05)
            return WeightedWallData(default, default, default, default, 'error', 'low', 0.0)

    # ───────────────────────────────────────────────────────────────────────────
    # MAX PAIN CALCULATION (from both PineScript indicators)
    # ───────────────────────────────────────────────────────────────────────────
    def calculate_max_pain(self, calls: pd.DataFrame, puts: pd.DataFrame,
                           current_price: float, timeframe: str) -> MaxPainData:
        """
        Calculate true max pain - the strike where option holders lose the most.

        From PineScript calculate_max_pain_direct():
        For each test strike:
            total_pain = sum of (ITM call values * OI) + sum of (ITM put values * OI)
        max_pain_strike = strike with minimum total_pain

        Also calculates pin risk based on distance.
        """
        try:
            all_strikes = sorted(set(calls.index.tolist() + puts.index.tolist()))

            if not all_strikes:
                return MaxPainData(current_price, 0, 0, 0, 0, 0, timeframe, "LOW", 1.0)

            pain_values = {}
            call_pain_by_strike = {}
            put_pain_by_strike = {}

            for test_strike in all_strikes:
                call_pain = 0.0
                put_pain = 0.0

                # Calculate call pain: calls ITM when price > strike
                for k in calls.index:
                    if test_strike > k:  # Call is ITM at test_strike
                        oi = calls.loc[k, 'openInterest'] if 'openInterest' in calls.columns else 0
                        if pd.notna(oi) and oi > 0:
                            call_pain += (test_strike - k) * oi * 100

                # Calculate put pain: puts ITM when price < strike
                for k in puts.index:
                    if test_strike < k:  # Put is ITM at test_strike
                        oi = puts.loc[k, 'openInterest'] if 'openInterest' in puts.columns else 0
                        if pd.notna(oi) and oi > 0:
                            put_pain += (k - test_strike) * oi * 100

                pain_values[test_strike] = call_pain + put_pain
                call_pain_by_strike[test_strike] = call_pain
                put_pain_by_strike[test_strike] = put_pain

            if pain_values:
                # Find strike with minimum pain
                max_pain_strike = min(pain_values, key=pain_values.get)
                total_pain = pain_values[max_pain_strike]
                call_p = call_pain_by_strike.get(max_pain_strike, 0)
                put_p = put_pain_by_strike.get(max_pain_strike, 0)

                # Distance calculation (standardized: positive = above price)
                distance_pct = ((max_pain_strike - current_price) / current_price) * 100
                distance_pts = max_pain_strike - current_price

                # Pin risk assessment (from PineScript)
                abs_distance = abs(distance_pct)
                if abs_distance < PIN_RISK_HIGH_PCT:
                    pin_risk = "HIGH"
                elif abs_distance < PIN_RISK_MED_PCT:
                    pin_risk = "MEDIUM"
                else:
                    pin_risk = "LOW"

                # Pain ratio for skew analysis
                pain_ratio = call_p / put_p if put_p > 0 else 1.0

                return MaxPainData(
                    strike=float(max_pain_strike),
                    distance_pct=round(distance_pct, 2),
                    distance_pts=round(distance_pts, 2),
                    total_pain_value=total_pain,
                    call_pain=call_p,
                    put_pain=put_p,
                    timeframe=timeframe,
                    pin_risk=pin_risk,
                    pain_ratio=round(pain_ratio, 2)
                )

            return MaxPainData(current_price, 0, 0, 0, 0, 0, timeframe, "LOW", 1.0)

        except Exception as e:
            self.errors.append(f"Max pain error: {e}")
            return MaxPainData(current_price, 0, 0, 0, 0, 0, timeframe, "LOW", 1.0)

    # ───────────────────────────────────────────────────────────────────────────
    # GAMMA FLIP CALCULATION
    # ───────────────────────────────────────────────────────────────────────────
    def calculate_gamma_flip(self, calls_gex: pd.Series, puts_gex: pd.Series,
                              current_price: float) -> GammaFlipData:
        """
        Calculate gamma flip point where net GEX crosses zero.

        Above gamma flip: Positive GEX (stable, mean-reverting)
        Below gamma flip: Negative GEX (volatile, trending)
        """
        try:
            all_strikes = sorted(set(calls_gex.index.tolist() + puts_gex.index.tolist()))

            if not all_strikes:
                return GammaFlipData(current_price, 0, 0)

            # Calculate net GEX at each strike
            net_gex = pd.Series(0.0, index=all_strikes)

            for strike in calls_gex.index:
                if strike in net_gex.index:
                    net_gex.loc[strike] += calls_gex.loc[strike]

            for strike in puts_gex.index:
                if strike in net_gex.index:
                    net_gex.loc[strike] += puts_gex.loc[strike]

            net_gex = net_gex.sort_index()

            # Find zero crossing (gamma flip)
            gamma_flip = current_price
            for i in range(len(net_gex) - 1):
                if net_gex.iloc[i] * net_gex.iloc[i + 1] < 0:
                    # Linear interpolation to find exact flip point
                    strike1, gex1 = net_gex.index[i], net_gex.iloc[i]
                    strike2, gex2 = net_gex.index[i + 1], net_gex.iloc[i + 1]
                    gamma_flip = strike1 + (strike2 - strike1) * (-gex1) / (gex2 - gex1)
                    break
            else:
                # No zero crossing found, use strike closest to zero
                gamma_flip = float(net_gex.abs().idxmin())

            # Calculate distance
            distance_pct = ((gamma_flip - current_price) / current_price) * 100
            distance_pts = gamma_flip - current_price

            # Calculate net GEX above and below flip
            net_gex_above = float(net_gex[net_gex.index > gamma_flip].sum())
            net_gex_below = float(net_gex[net_gex.index < gamma_flip].sum())

            return GammaFlipData(
                strike=float(gamma_flip),
                distance_pct=round(distance_pct, 2),
                distance_pts=round(distance_pts, 2),
                net_gex_above=net_gex_above,
                net_gex_below=net_gex_below
            )

        except Exception as e:
            self.errors.append(f"Gamma flip error: {e}")
            return GammaFlipData(current_price, 0, 0)

    # ───────────────────────────────────────────────────────────────────────────
    # RISK DISTANCE CALCULATION (standardized)
    # ───────────────────────────────────────────────────────────────────────────
    def calculate_risk_distance(self, current_price: float, level_price: float) -> Tuple[float, float]:
        """
        Calculate distance from current price to level.

        Standardized formula: (level - price) / price * 100
        - Positive = level is above current price (resistance/upside)
        - Negative = level is below current price (support/downside)
        """
        if level_price <= 0 or current_price <= 0:
            return 0.0, 0.0

        distance_pct = ((level_price - current_price) / current_price) * 100
        distance_pts = level_price - current_price

        return round(distance_pct, 2), round(distance_pts, 2)


# ═══════════════════════════════════════════════════════════════════════════════
# MARKET REGIME DETECTION
# ═══════════════════════════════════════════════════════════════════════════════
def get_market_regime() -> MarketRegime:
    """
    Detect market regime using VIX.

    From Enhanced Gamma Wall Scanner:
    - High Volatility: VIX >= 25
    - Low Volatility: VIX <= 15
    - Normal: 15 < VIX < 25
    """
    try:
        vix = yf.Ticker("^VIX")
        vix_data = vix.history(period="2d")

        if not vix_data.empty:
            vix_value = float(vix_data['Close'].iloc[-1])

            if vix_value >= VIX_HIGH_THRESHOLD:
                regime = "High Volatility"
                multiplier = 1.2  # Boost strength in high vol
            elif vix_value <= VIX_LOW_THRESHOLD:
                regime = "Low Volatility"
                multiplier = 0.88  # Reduce strength in low vol
            else:
                regime = "Normal Volatility"
                multiplier = 1.0

            return MarketRegime(regime, vix_value, False, multiplier)

    except Exception as e:
        logger.warning(f"VIX fetch error: {e}")

    # Fallback
    return MarketRegime("Normal Volatility", 16.0, True, 1.0)


# ═══════════════════════════════════════════════════════════════════════════════
# EXPIRATION DATE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
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


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PROCESSING FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════
def process_symbol_risk_distance(symbol: str) -> Optional[Dict]:
    """
    Process a symbol and return complete risk distance profile.

    Returns data compatible with frontend RiskDistanceTab component.
    """
    # Get market regime first
    regime = get_market_regime()
    calculator = GammaRiskCalculatorV2(regime)

    try:
        ticker = yf.Ticker(symbol)

        # ─── Get Current Price ────────────────────────────────────────────────
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
                    current_price = float(hist['Close'].iloc[-1])
            except:
                pass

        if not current_price or current_price <= 0:
            logger.error(f"No price data for {symbol}")
            return None

        current_price = float(current_price)

        # ─── Get Options Dates ────────────────────────────────────────────────
        try:
            options_dates = list(ticker.options)
        except:
            logger.error(f"No options for {symbol}")
            return None

        if not options_dates:
            return None

        # ─── Timeframes (matching PineScript) ─────────────────────────────────
        timeframes = {
            'weekly': (SHORTEST_DAYS, 'wk'),     # Shortest term
            'swing': (SHORT_DAYS, 'st'),          # Short term (ST)
            'long': (MEDIUM_DAYS, 'lt'),          # Long term (LT)
            'quarterly': (LONG_DAYS, 'q')         # Quarterly (Q)
        }

        result = {
            'symbol': symbol,
            'current_price': current_price,
            'timestamp': datetime.now().isoformat(),
            'put_walls': {},
            'call_walls': {},
            'max_pain': {},
            'weighted_walls': {},
            'gamma_flip': None,
            'sd_levels': None,
            'regime': asdict(regime),
            'summary': {}
        }

        all_puts_gex = {}
        all_calls_gex = {}
        swing_iv = 0.25  # Default IV
        swing_dte = 14

        # ─── Process Each Timeframe ───────────────────────────────────────────
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
                timeframe_iv = max(0.05, min(2.0, float(timeframe_iv)))

                T = dte / 365.0

                # ─── Calculate Gamma for Each Option ──────────────────────────
                for df in [calls, puts]:
                    df['gamma'] = df.apply(
                        lambda row: calculator.calculate_gamma(
                            current_price, row.name, T, RISK_FREE_RATE, timeframe_iv
                        ),
                        axis=1
                    )

                # ─── Calculate GEX (from PineScript formula) ──────────────────
                calls_gex = calls['openInterest'] * calls['gamma'] * 100 * current_price
                puts_gex = puts['openInterest'] * puts['gamma'] * 100 * current_price * -1

                all_puts_gex[tf_name] = puts_gex
                all_calls_gex[tf_name] = calls_gex

                # ─── Find Walls ───────────────────────────────────────────────
                # Put wall: strike with highest put GEX below current price
                puts_below = puts_gex[puts_gex.index < current_price]
                if not puts_below.empty:
                    put_wall_strike = float(puts_below.abs().idxmax())
                    put_gex_value = float(puts_below.loc[put_wall_strike])
                else:
                    put_wall_strike = current_price * 0.95
                    put_gex_value = 0.0

                # Call wall: strike with highest call GEX above current price
                calls_above = calls_gex[calls_gex.index > current_price]
                if not calls_above.empty:
                    call_wall_strike = float(calls_above.abs().idxmax())
                    call_gex_value = float(calls_above.loc[call_wall_strike])
                else:
                    call_wall_strike = current_price * 1.05
                    call_gex_value = 0.0

                # Calculate strengths
                put_strength = calculator.calculate_wall_strength(puts_gex)
                call_strength = calculator.calculate_wall_strength(calls_gex)

                # Calculate distances
                put_dist_pct, put_dist_pts = calculator.calculate_risk_distance(current_price, put_wall_strike)
                call_dist_pct, call_dist_pts = calculator.calculate_risk_distance(current_price, call_wall_strike)

                # Store put wall
                result['put_walls'][tf_name] = {
                    'strike': put_wall_strike,
                    'distance_pct': put_dist_pct,
                    'distance_pts': put_dist_pts,
                    'strength': put_strength,
                    'dte': dte,
                    'gex_value': put_gex_value,
                    'iv_at_strike': timeframe_iv * 100
                }

                # Store call wall
                result['call_walls'][tf_name] = {
                    'strike': call_wall_strike,
                    'distance_pct': call_dist_pct,
                    'distance_pts': call_dist_pts,
                    'strength': call_strength,
                    'dte': dte,
                    'gex_value': call_gex_value,
                    'iv_at_strike': timeframe_iv * 100
                }

                # ─── Calculate Max Pain ───────────────────────────────────────
                max_pain = calculator.calculate_max_pain(calls, puts, current_price, tf_name)
                result['max_pain'][tf_name] = asdict(max_pain)

                # ─── Swing timeframe: weighted walls, gamma flip, SD levels ───
                if tf_name == 'swing':
                    swing_iv = timeframe_iv
                    swing_dte = dte

                    # Weighted walls
                    weighted_put = calculator.calculate_weighted_wall(puts_gex, current_price, is_put=True)
                    weighted_call = calculator.calculate_weighted_wall(calls_gex, current_price, is_put=False)

                    result['weighted_walls']['put'] = asdict(weighted_put)
                    result['weighted_walls']['call'] = asdict(weighted_call)

                    # Gamma flip
                    gamma_flip = calculator.calculate_gamma_flip(calls_gex, puts_gex, current_price)
                    result['gamma_flip'] = asdict(gamma_flip)

                    # SD levels
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

            except Exception as e:
                logger.warning(f"Error processing {tf_name} for {symbol}: {e}")
                continue

        # ─── Calculate Summary Metrics ────────────────────────────────────────
        if result['put_walls'] and result['call_walls']:
            # Find nearest support and resistance
            put_distances = [v['distance_pct'] for v in result['put_walls'].values()]
            call_distances = [v['distance_pct'] for v in result['call_walls'].values()]

            # Nearest support (most negative, closest to price from below)
            nearest_support = max(put_distances) if put_distances else -10
            # Nearest resistance (least positive, closest to price from above)
            nearest_resistance = min(call_distances) if call_distances else 10

            # Position in range
            abs_support = abs(nearest_support)
            abs_resistance = abs(nearest_resistance)

            if abs_support < 2:
                position = 'near_support'
            elif abs_resistance < 2:
                position = 'near_resistance'
            else:
                position = 'mid_range'

            # Risk/reward ratio
            if abs_resistance > 0:
                rr_ratio = abs_support / abs_resistance
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
    abs_support = abs(support_distance)

    if position == 'near_support':
        if abs_support < 1:
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


# ═══════════════════════════════════════════════════════════════════════════════
# BATCH PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════
def get_risk_distance_data(symbols: List[str], max_workers: int = 4) -> Dict:
    """Get risk distance data for multiple symbols."""
    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
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


# ═══════════════════════════════════════════════════════════════════════════════
# API FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════
def get_symbol_risk_distances(symbol: str) -> Optional[Dict]:
    """API endpoint to get risk distances for a single symbol."""
    return process_symbol_risk_distance(symbol)


# ═══════════════════════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    test_symbols = ['AAPL', 'NVDA', 'SPY']

    print("\n" + "="*80)
    print("GAMMA RISK DISTANCE CALCULATOR v2.0")
    print("Inspired by PineScript: GEX Options Flow Pro & Enhanced Gamma Wall Scanner")
    print("="*80)

    # Get market regime
    regime = get_market_regime()
    print(f"\nMarket Regime: {regime.regime} (VIX: {regime.vix_value:.1f})")
    print(f"Strength Multiplier: {regime.strength_multiplier:.2f}")

    for symbol in test_symbols:
        print(f"\n{'─'*60}")
        print(f"Risk Distance Analysis: {symbol}")
        print('─'*60)

        data = process_symbol_risk_distance(symbol)

        if data:
            print(f"Current Price: ${data['current_price']:.2f}")

            print(f"\n📊 PUT WALLS (Support Levels):")
            print(f"{'Timeframe':<12} {'Strike':>10} {'Distance':>10} {'Strength':>10} {'DTE':>6}")
            print("-" * 50)
            for tf in ['weekly', 'swing', 'long', 'quarterly']:
                wall = data['put_walls'].get(tf)
                if wall:
                    print(f"{tf:<12} ${wall['strike']:>9.2f} {wall['distance_pct']:>+9.2f}% {wall['strength']:>9.1f}% {wall['dte']:>5}d")

            print(f"\n📊 CALL WALLS (Resistance Levels):")
            print(f"{'Timeframe':<12} {'Strike':>10} {'Distance':>10} {'Strength':>10} {'DTE':>6}")
            print("-" * 50)
            for tf in ['weekly', 'swing', 'long', 'quarterly']:
                wall = data['call_walls'].get(tf)
                if wall:
                    print(f"{tf:<12} ${wall['strike']:>9.2f} {wall['distance_pct']:>+9.2f}% {wall['strength']:>9.1f}% {wall['dte']:>5}d")

            print(f"\n🎯 MAX PAIN LEVELS:")
            print(f"{'Timeframe':<12} {'Strike':>10} {'Distance':>10} {'Pin Risk':>10}")
            print("-" * 45)
            for tf in ['weekly', 'swing', 'long', 'quarterly']:
                mp = data['max_pain'].get(tf)
                if mp:
                    print(f"{tf:<12} ${mp['strike']:>9.2f} {mp['distance_pct']:>+9.2f}% {mp['pin_risk']:>10}")

            if data.get('weighted_walls', {}).get('put'):
                wp = data['weighted_walls']['put']
                print(f"\n🔧 WEIGHTED PUT WALL ANALYSIS:")
                print(f"  Max GEX Method:      ${wp['max_gex_wall']:.2f}")
                print(f"  Weighted Centroid:   ${wp['weighted_centroid']:.2f}")
                print(f"  Cumulative (70%):    ${wp['cumulative_threshold']:.2f}")
                print(f"  ✅ Recommended:      ${wp['recommended_wall']:.2f} ({wp['method_used']}, {wp['confidence']} confidence)")

            if data.get('gamma_flip'):
                gf = data['gamma_flip']
                print(f"\n⚡ GAMMA FLIP:")
                print(f"  Level: ${gf['strike']:.2f} ({gf['distance_pct']:+.2f}%)")

            if data.get('summary'):
                print(f"\n📋 SUMMARY:")
                print(f"  Position: {data['summary']['position_in_range']}")
                print(f"  Risk/Reward: {data['summary']['risk_reward_ratio']:.2f}")
                print(f"  {data['summary']['recommendation']}")
        else:
            print("Failed to get data")

    print("\n" + "="*80)
