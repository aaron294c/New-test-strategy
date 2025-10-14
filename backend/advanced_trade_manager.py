#!/usr/bin/env python3
"""
Advanced Trade Management System

Implements sophisticated exit strategies based on:
1. Temporal Percentile Curves - how percentile evolves over time
2. Multi-timeframe Coherence - daily + 4h alignment
3. Volatility-Normalized Displacement - ATR-based trailing stops
4. State Machine for Trade Lifecycle
5. Conditional Expectancy Calculations
6. Dynamic Exposure Management

Inspired by AI-driven trade management framework for optimal hold/exit decisions.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import yfinance as yf
from scipy import stats


class TradeState(Enum):
    """Trade lifecycle states."""
    REBOUND_INITIATION = "rebound_initiation"
    MOMENTUM_ESTABLISHMENT = "momentum_establishment"
    ACCELERATION = "acceleration"
    DISTRIBUTION = "distribution"
    REVERSAL = "reversal"


@dataclass
class VolatilityMetrics:
    """Volatility-based metrics for trailing stops."""
    atr: float  # Average True Range
    atr_multiplier: float  # Multiplier for trailing stop
    normalized_displacement: float  # Distance in σ units
    volatility_regime: str  # 'low', 'normal', 'high'

    def to_dict(self):
        return asdict(self)


@dataclass
class ExitPressure:
    """Exit pressure signal combining multiple factors."""
    overall_pressure: float  # 0-100, higher = stronger exit signal
    percentile_velocity_component: float
    time_decay_component: float
    divergence_component: float
    volatility_component: float
    confidence: float  # 0-1

    def to_dict(self):
        return asdict(self)


@dataclass
class TradeStateInfo:
    """Current trade state information."""
    current_state: TradeState
    state_probability: float  # Confidence in state classification
    days_in_state: int
    transition_probabilities: Dict[TradeState, float]

    def to_dict(self):
        return {
            'current_state': self.current_state.value,
            'state_probability': self.state_probability,
            'days_in_state': self.days_in_state,
            'transition_probabilities': {k.value: v for k, v in self.transition_probabilities.items()}
        }


@dataclass
class ExposureRecommendation:
    """Dynamic exposure recommendation."""
    recommended_exposure: float  # 0-100%
    action: str  # 'hold', 'reduce_25', 'reduce_50', 'reduce_75', 'exit_all'
    confidence_score: float  # Multi-factor confidence
    expected_return_if_hold: float
    expected_return_if_exit: float
    optimal_action: str  # Based on expectancy

    def to_dict(self):
        return asdict(self)


class AdvancedTradeManager:
    """
    Advanced Trade Management Engine

    Implements sophisticated exit logic based on:
    - Temporal percentile evolution
    - Multi-timeframe analysis
    - Volatility regimes
    - State-based transitions
    - Conditional expectancy
    """

    def __init__(self,
                 historical_data: pd.DataFrame,
                 rsi_ma_percentiles: pd.Series,
                 entry_idx: int,
                 entry_percentile: float,
                 entry_price: float,
                 lookback_period: int = 500):
        """
        Initialize trade manager.

        Args:
            historical_data: Full OHLCV data
            rsi_ma_percentiles: RSI-MA percentile series
            entry_idx: Index where trade entered
            entry_percentile: Entry percentile value
            entry_price: Entry price
            lookback_period: Lookback for calculations
        """
        self.data = historical_data
        self.percentiles = rsi_ma_percentiles
        self.entry_idx = entry_idx
        self.entry_percentile = entry_percentile
        self.entry_price = entry_price
        self.lookback = lookback_period

        # Calculate ATR for volatility metrics
        self.atr_series = self._calculate_atr()

        # Pre-calculate volatility regime history
        self.volatility_regimes = self._classify_volatility_regimes()

    def _calculate_atr(self, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high = self.data['High']
        low = self.data['Low']
        close = self.data['Close']

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr

    def _classify_volatility_regimes(self) -> pd.Series:
        """
        Classify each day into volatility regime.

        Returns:
            Series with 'low', 'normal', 'high' classifications
        """
        # Calculate rolling volatility (20-day)
        returns = np.log(self.data['Close'] / self.data['Close'].shift(1))
        rolling_vol = returns.rolling(window=20).std() * np.sqrt(252) * 100  # Annualized

        # Historical percentiles for regime classification
        vol_20th = rolling_vol.quantile(0.20)
        vol_80th = rolling_vol.quantile(0.80)

        regimes = pd.Series(index=rolling_vol.index, dtype='object')
        regimes[rolling_vol <= vol_20th] = 'low'
        regimes[(rolling_vol > vol_20th) & (rolling_vol < vol_80th)] = 'normal'
        regimes[rolling_vol >= vol_80th] = 'high'

        return regimes.fillna('normal')

    def calculate_volatility_metrics(self, current_idx: int) -> VolatilityMetrics:
        """
        Calculate ATR-based volatility metrics for current position.

        Args:
            current_idx: Current day index

        Returns:
            VolatilityMetrics with ATR, displacement, regime info
        """
        if current_idx >= len(self.atr_series):
            current_idx = len(self.atr_series) - 1

        current_atr = self.atr_series.iloc[current_idx]
        current_price = self.data['Close'].iloc[current_idx]

        # Handle NaN values in ATR
        if pd.isna(current_atr) or current_atr == 0:
            # Use a default ATR based on recent price range if ATR is not available
            recent_data = self.data.iloc[max(0, current_idx-20):current_idx+1]
            if len(recent_data) > 0:
                current_atr = (recent_data['High'] - recent_data['Low']).mean()
            else:
                current_atr = current_price * 0.02  # 2% of price as fallback

        # Calculate normalized displacement from entry
        price_move = current_price - self.entry_price
        atr_displacement = price_move / current_atr if current_atr > 0 else 0

        # Volatility regime
        regime = self.volatility_regimes.iloc[current_idx]

        # ATR multiplier based on regime
        multipliers = {'low': 1.5, 'normal': 2.0, 'high': 2.5}
        atr_mult = multipliers.get(regime, 2.0)

        return VolatilityMetrics(
            atr=float(current_atr),
            atr_multiplier=atr_mult,
            normalized_displacement=float(atr_displacement),
            volatility_regime=str(regime)
        )

    def calculate_percentile_velocity(self, current_idx: int, window: int = 3) -> float:
        """
        Calculate percentile velocity (rate of change).

        Δp/Δt over recent window.

        Args:
            current_idx: Current day index
            window: Lookback window for velocity

        Returns:
            Percentile velocity (points per day)
        """
        if current_idx < self.entry_idx + window:
            return 0.0

        start_idx = current_idx - window
        start_percentile = self.percentiles.iloc[start_idx]
        end_percentile = self.percentiles.iloc[current_idx]

        velocity = (end_percentile - start_percentile) / window
        return velocity

    def calculate_time_decay(self, days_since_entry: int, max_hold_days: int = 21) -> float:
        """
        Calculate time decay factor.

        Edge decays over time even if price doesn't reverse.

        Args:
            days_since_entry: Days since trade entry
            max_hold_days: Maximum intended hold period

        Returns:
            Time decay factor (0-1, higher = more decay)
        """
        if days_since_entry <= 0:
            return 0.0

        # Exponential decay model
        decay_rate = 1.0 / max_hold_days
        time_decay = 1.0 - np.exp(-decay_rate * days_since_entry)

        return time_decay

    def detect_multi_timeframe_divergence(self, current_idx: int) -> float:
        """
        Detect divergence between daily and shorter timeframe.

        In production, this would fetch 4h data. Here we approximate
        using intraday momentum proxies.

        Args:
            current_idx: Current day index

        Returns:
            Divergence score (0-1, higher = more divergence)
        """
        # Approximate intraday momentum using:
        # 1. Daily close position within range
        # 2. Recent 3-day momentum vs longer 7-day momentum

        if current_idx < 7:
            return 0.0

        # Close position in daily range (0 = low, 1 = high)
        high = self.data['High'].iloc[current_idx]
        low = self.data['Low'].iloc[current_idx]
        close = self.data['Close'].iloc[current_idx]

        if high - low > 0:
            close_position = (close - low) / (high - low)
        else:
            close_position = 0.5

        # Short-term momentum (3 days)
        short_ret = (self.data['Close'].iloc[current_idx] /
                     self.data['Close'].iloc[current_idx-3] - 1)

        # Medium-term momentum (7 days)
        medium_ret = (self.data['Close'].iloc[current_idx] /
                      self.data['Close'].iloc[current_idx-7] - 1)

        # Divergence occurs when short-term weakens vs medium-term
        if medium_ret > 0:
            momentum_ratio = short_ret / (medium_ret + 1e-6)
            # If short-term < medium-term, divergence increases
            divergence = max(0, 1.0 - momentum_ratio)
        else:
            divergence = 0.0

        # Combine with close position
        # If close near low of day + momentum weakening = divergence
        divergence_score = (1.0 - close_position) * 0.5 + divergence * 0.5

        return np.clip(divergence_score, 0, 1)

    def calculate_exit_pressure(self,
                               current_idx: int,
                               days_since_entry: int) -> ExitPressure:
        """
        Calculate comprehensive exit pressure.

        Implements: ExitPressure = f(p(t), Δp/Δt, t, divergence, σ_regime)

        Args:
            current_idx: Current day index
            days_since_entry: Days since entry

        Returns:
            ExitPressure with detailed breakdown
        """
        current_percentile = self.percentiles.iloc[current_idx]

        # 1. Percentile velocity component
        velocity = self.calculate_percentile_velocity(current_idx)
        # Rapid rise = exhaustion signal
        velocity_pressure = np.clip(velocity / 5.0, 0, 1) * 25  # 0-25 points

        # 2. Time decay component
        time_decay = self.calculate_time_decay(days_since_entry)
        time_pressure = time_decay * 20  # 0-20 points

        # 3. Divergence component
        divergence = self.detect_multi_timeframe_divergence(current_idx)
        divergence_pressure = divergence * 25  # 0-25 points

        # 4. Volatility component
        vol_metrics = self.calculate_volatility_metrics(current_idx)
        # High vol regime increases exit pressure
        vol_pressure_map = {'low': 5, 'normal': 15, 'high': 30}
        vol_pressure = vol_pressure_map.get(vol_metrics.volatility_regime, 15)

        # 5. Absolute percentile level
        # If already at high percentile, add pressure
        percentile_level_pressure = max(0, (current_percentile - 50) / 2.0)  # 0-25

        # Total exit pressure (0-100)
        total_pressure = (velocity_pressure +
                         time_pressure +
                         divergence_pressure +
                         percentile_level_pressure * 0.5)

        # Confidence based on data quality
        confidence = min(1.0, days_since_entry / 5.0)  # More confident after more days

        return ExitPressure(
            overall_pressure=np.clip(total_pressure, 0, 100),
            percentile_velocity_component=velocity_pressure,
            time_decay_component=time_pressure,
            divergence_component=divergence_pressure,
            volatility_component=vol_pressure,
            confidence=confidence
        )

    def classify_trade_state(self,
                            current_idx: int,
                            days_since_entry: int) -> TradeStateInfo:
        """
        Classify current trade into lifecycle state.

        States:
        - REBOUND_INITIATION: Immediate bounce (D1-D3)
        - MOMENTUM_ESTABLISHMENT: Sustained rise (D3-D7)
        - ACCELERATION: Rapid percentile climb (high velocity)
        - DISTRIBUTION: Stall, divergence present
        - REVERSAL: Percentile declining

        Args:
            current_idx: Current day index
            days_since_entry: Days since entry

        Returns:
            TradeStateInfo with state and transition probabilities
        """
        current_percentile = self.percentiles.iloc[current_idx]
        percentile_change = current_percentile - self.entry_percentile
        velocity = self.calculate_percentile_velocity(current_idx)
        divergence = self.detect_multi_timeframe_divergence(current_idx)

        # State classification logic
        if days_since_entry <= 3:
            if percentile_change > 5:
                state = TradeState.REBOUND_INITIATION
                prob = 0.8
            else:
                state = TradeState.REBOUND_INITIATION
                prob = 0.6

        elif days_since_entry <= 7:
            if velocity > 2.0 and percentile_change > 10:
                state = TradeState.ACCELERATION
                prob = 0.75
            elif percentile_change > 0:
                state = TradeState.MOMENTUM_ESTABLISHMENT
                prob = 0.7
            else:
                state = TradeState.DISTRIBUTION
                prob = 0.6

        else:  # After D7
            if velocity < -1.0:
                state = TradeState.REVERSAL
                prob = 0.8
            elif divergence > 0.6:
                state = TradeState.DISTRIBUTION
                prob = 0.75
            elif velocity > 3.0:
                state = TradeState.ACCELERATION
                prob = 0.7
            else:
                state = TradeState.MOMENTUM_ESTABLISHMENT
                prob = 0.65

        # Calculate transition probabilities (simplified model)
        transitions = self._calculate_transition_probabilities(state, velocity, divergence)

        return TradeStateInfo(
            current_state=state,
            state_probability=prob,
            days_in_state=1,  # Simplified
            transition_probabilities=transitions
        )

    def _calculate_transition_probabilities(self,
                                           current_state: TradeState,
                                           velocity: float,
                                           divergence: float) -> Dict[TradeState, float]:
        """Calculate probability of transitioning to each state."""

        # Base transition matrix (simplified)
        if current_state == TradeState.REBOUND_INITIATION:
            probs = {
                TradeState.MOMENTUM_ESTABLISHMENT: 0.6,
                TradeState.ACCELERATION: 0.2,
                TradeState.DISTRIBUTION: 0.15,
                TradeState.REVERSAL: 0.05
            }
        elif current_state == TradeState.MOMENTUM_ESTABLISHMENT:
            probs = {
                TradeState.MOMENTUM_ESTABLISHMENT: 0.4,
                TradeState.ACCELERATION: 0.3,
                TradeState.DISTRIBUTION: 0.2,
                TradeState.REVERSAL: 0.1
            }
        elif current_state == TradeState.ACCELERATION:
            probs = {
                TradeState.ACCELERATION: 0.2,
                TradeState.DISTRIBUTION: 0.5,
                TradeState.REVERSAL: 0.25,
                TradeState.MOMENTUM_ESTABLISHMENT: 0.05
            }
        elif current_state == TradeState.DISTRIBUTION:
            probs = {
                TradeState.DISTRIBUTION: 0.3,
                TradeState.REVERSAL: 0.5,
                TradeState.MOMENTUM_ESTABLISHMENT: 0.15,
                TradeState.ACCELERATION: 0.05
            }
        else:  # REVERSAL
            probs = {
                TradeState.REVERSAL: 0.7,
                TradeState.DISTRIBUTION: 0.2,
                TradeState.REBOUND_INITIATION: 0.1
            }

        return probs

    def calculate_conditional_expectancy(self,
                                        current_idx: int,
                                        days_since_entry: int,
                                        historical_events: List[Dict]) -> Tuple[float, float]:
        """
        Calculate expected return for:
        1. Holding N more days
        2. Exiting now

        Based on historical similar situations.

        Args:
            current_idx: Current day index
            days_since_entry: Days since entry
            historical_events: List of historical trade events

        Returns:
            (expected_return_if_hold, expected_return_if_exit)
        """
        current_percentile = self.percentiles.iloc[current_idx]
        current_price = self.data['Close'].iloc[current_idx]
        current_return = (current_price / self.entry_price - 1) * 100

        # Find similar historical situations
        similar_returns = []

        for event in historical_events:
            if days_since_entry not in event['progression']:
                continue

            hist_percentile = event['progression'][days_since_entry]['percentile']

            # Check if similar percentile level (±10 points)
            if abs(hist_percentile - current_percentile) <= 10:
                # Look at return from this day to end of holding period
                max_day = max(event['progression'].keys())

                if max_day > days_since_entry:
                    future_return = (event['progression'][max_day]['cumulative_return_pct'] -
                                   event['progression'][days_since_entry]['cumulative_return_pct'])
                    similar_returns.append(future_return)

        # Expected return if hold
        if similar_returns and len(similar_returns) >= 5:
            expected_hold_return = np.median(similar_returns)
        else:
            # Default to small positive expectancy if insufficient data
            expected_hold_return = 0.5

        # Expected return if exit now
        expected_exit_return = current_return

        return expected_hold_return, expected_exit_return

    def generate_exposure_recommendation(self,
                                         current_idx: int,
                                         days_since_entry: int,
                                         historical_events: List[Dict]) -> ExposureRecommendation:
        """
        Generate dynamic exposure recommendation.

        Exposure(t) = g(confidence(t), ExitPressure(t))

        Args:
            current_idx: Current day index
            days_since_entry: Days since entry
            historical_events: Historical trade events for expectancy

        Returns:
            ExposureRecommendation with action and confidence
        """
        # Calculate components
        exit_pressure = self.calculate_exit_pressure(current_idx, days_since_entry)
        state_info = self.classify_trade_state(current_idx, days_since_entry)
        vol_metrics = self.calculate_volatility_metrics(current_idx)

        expected_hold, expected_exit = self.calculate_conditional_expectancy(
            current_idx, days_since_entry, historical_events
        )

        # Calculate confidence score (multi-factor)
        # High confidence when:
        # - Low divergence
        # - Clear state classification
        # - Normal volatility regime

        divergence = self.detect_multi_timeframe_divergence(current_idx)

        confidence_factors = [
            1.0 - divergence,  # Low divergence = high confidence
            state_info.state_probability,  # Clear state = high confidence
            1.0 if vol_metrics.volatility_regime == 'normal' else 0.5,  # Normal vol = high confidence
            exit_pressure.confidence  # Exit pressure confidence
        ]

        confidence_score = np.mean(confidence_factors)

        # Calculate recommended exposure
        # Base exposure = 100%
        # Reduced by exit pressure and low confidence

        base_exposure = 100.0
        pressure_reduction = exit_pressure.overall_pressure * 0.5  # Max 50% reduction from pressure
        confidence_boost = confidence_score * 20  # Up to +20% if high confidence

        recommended_exposure = base_exposure - pressure_reduction + confidence_boost
        recommended_exposure = np.clip(recommended_exposure, 0, 100)

        # Determine action
        if recommended_exposure >= 90:
            action = 'hold'
        elif recommended_exposure >= 65:
            action = 'reduce_25'
        elif recommended_exposure >= 40:
            action = 'reduce_50'
        elif recommended_exposure >= 15:
            action = 'reduce_75'
        else:
            action = 'exit_all'

        # Optimal action based on expectancy
        if expected_hold > expected_exit + 1.0:  # Hold if >1% better
            optimal_action = 'hold'
        elif expected_exit > expected_hold + 1.0:
            optimal_action = 'exit_all'
        else:
            optimal_action = 'reduce_50'  # Partial exit if unclear

        return ExposureRecommendation(
            recommended_exposure=recommended_exposure,
            action=action,
            confidence_score=confidence_score,
            expected_return_if_hold=expected_hold,
            expected_return_if_exit=expected_exit,
            optimal_action=optimal_action
        )

    def calculate_trailing_stop_level(self,
                                      current_idx: int,
                                      days_since_entry: int) -> float:
        """
        Calculate adaptive ATR-based trailing stop.

        Stop becomes tighter as trade matures.

        Args:
            current_idx: Current day index
            days_since_entry: Days since entry

        Returns:
            Stop loss price level
        """
        vol_metrics = self.calculate_volatility_metrics(current_idx)
        current_price = self.data['Close'].iloc[current_idx]

        # ATR multiplier decreases with trade age (tighter stops over time)
        age_factor = 1.0 - (days_since_entry / 21.0) * 0.3  # Max 30% reduction
        adjusted_multiplier = vol_metrics.atr_multiplier * max(age_factor, 0.7)

        # Stop level
        stop_distance = vol_metrics.atr * adjusted_multiplier
        stop_level = current_price - stop_distance

        # Never below entry price (move to breakeven after profitable)
        if current_price > self.entry_price:
            stop_level = max(stop_level, self.entry_price)

        return stop_level


def _convert_numpy_types(obj):
    """
    Recursively convert NumPy types to Python native types for JSON serialization.
    """
    if isinstance(obj, dict):
        return {key: _convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_convert_numpy_types(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return _convert_numpy_types(obj.tolist())
    elif isinstance(obj, (pd.Timestamp, pd.DatetimeIndex)):
        return obj.isoformat()
    else:
        return obj


def simulate_trade_with_advanced_management(
    historical_data: pd.DataFrame,
    rsi_ma_percentiles: pd.Series,
    entry_idx: int,
    entry_percentile: float,
    entry_price: float,
    historical_events: List[Dict],
    max_hold_days: int = 21
) -> Dict:
    """
    Simulate a single trade using advanced management.

    Returns detailed day-by-day analysis.
    """
    manager = AdvancedTradeManager(
        historical_data=historical_data,
        rsi_ma_percentiles=rsi_ma_percentiles,
        entry_idx=entry_idx,
        entry_percentile=entry_percentile,
        entry_price=entry_price
    )

    simulation_results = []

    for day in range(1, min(max_hold_days + 1, len(historical_data) - entry_idx)):
        current_idx = entry_idx + day

        # Calculate all metrics
        exit_pressure = manager.calculate_exit_pressure(current_idx, day)
        state_info = manager.classify_trade_state(current_idx, day)
        exposure_rec = manager.generate_exposure_recommendation(
            current_idx, day, historical_events
        )
        trailing_stop = manager.calculate_trailing_stop_level(current_idx, day)
        vol_metrics = manager.calculate_volatility_metrics(current_idx)

        current_price = historical_data['Close'].iloc[current_idx]
        current_percentile = rsi_ma_percentiles.iloc[current_idx]
        current_return = (current_price / entry_price - 1) * 100

        day_result = {
            'day': int(day),
            'date': str(historical_data.index[current_idx]),
            'price': float(current_price),
            'percentile': float(current_percentile),
            'return_pct': float(current_return),
            'exit_pressure': exit_pressure.to_dict(),
            'trade_state': state_info.to_dict(),
            'exposure_recommendation': exposure_rec.to_dict(),
            'trailing_stop': float(trailing_stop),
            'volatility_metrics': vol_metrics.to_dict(),
            'triggered_stop': bool(current_price <= trailing_stop),
            'triggered_exit_signal': bool(exposure_rec.action in ['reduce_75', 'exit_all'])
        }

        simulation_results.append(day_result)

        # Exit if stop hit
        if current_price <= trailing_stop:
            break

    result = {
        'entry_price': float(entry_price),
        'entry_percentile': float(entry_percentile),
        'entry_date': str(historical_data.index[entry_idx]),
        'daily_analysis': simulation_results,
        'total_days_held': int(len(simulation_results)),
        'final_return': float(simulation_results[-1]['return_pct']) if simulation_results else 0.0
    }

    # Convert all nested numpy types
    return _convert_numpy_types(result)
