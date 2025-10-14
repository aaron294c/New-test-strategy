#!/usr/bin/env python3
"""
Live Trading Signal Generator

Applies historical analysis to current market conditions to generate
actionable trading signals in real-time.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enhanced_backtester import EnhancedPerformanceMatrixBacktester
from advanced_trade_manager import AdvancedTradeManager, _convert_numpy_types


@dataclass
class EntrySignal:
    """Real-time entry signal."""
    ticker: str
    current_price: float
    current_percentile: float
    signal_strength: str  # 'strong_buy', 'buy', 'neutral', 'avoid'
    confidence: float  # 0-1
    expected_return_7d: float
    expected_return_14d: float
    expected_return_21d: float
    win_rate_historical: float
    recommended_entry_size: float  # 0-100%
    reasoning: List[str]
    risk_factors: List[str]

    def to_dict(self):
        return asdict(self)


@dataclass
class ExitSignal:
    """Real-time exit signal for existing position."""
    ticker: str
    entry_price: float
    entry_date: str
    current_price: float
    current_return: float
    days_held: int
    exit_pressure: float  # 0-100
    recommended_action: str  # 'hold', 'reduce_25', 'reduce_50', 'reduce_75', 'exit_all'
    urgency: str  # 'low', 'medium', 'high', 'critical'
    expected_return_if_hold_7d: float
    expected_return_if_exit_now: float
    trailing_stop: float
    reasoning: List[str]

    def to_dict(self):
        return asdict(self)


class LiveSignalGenerator:
    """
    Generate actionable trading signals from current market data.
    """

    def __init__(self, ticker: str, lookback_period: int = 500):
        """
        Initialize signal generator.

        Args:
            ticker: Stock ticker symbol
            lookback_period: Historical data period for analysis
        """
        self.ticker = ticker.upper()
        self.lookback = lookback_period

        # Fetch and prepare data
        self.backtester = EnhancedPerformanceMatrixBacktester(
            tickers=[self.ticker],
            lookback_period=lookback_period,
            rsi_length=14,
            ma_length=14,
            max_horizon=21
        )

        self.data = self.backtester.fetch_data(self.ticker)
        if self.data.empty:
            raise ValueError(f"Could not fetch data for {self.ticker}")

        self.indicator = self.backtester.calculate_rsi_ma_indicator(self.data)
        self.percentiles = self.backtester.calculate_percentile_ranks(self.indicator)

        # Calculate historical entry events for context
        self.entry_events_5 = self.backtester.find_entry_events_enhanced(
            self.percentiles, self.data['Close'], 5.0
        )
        self.entry_events_10 = self.backtester.find_entry_events_enhanced(
            self.percentiles, self.data['Close'], 10.0
        )
        self.entry_events_15 = self.backtester.find_entry_events_enhanced(
            self.percentiles, self.data['Close'], 15.0
        )

    def generate_entry_signal(self) -> EntrySignal:
        """
        Generate entry signal for current market conditions.

        Returns:
            EntrySignal with actionable recommendation
        """
        # Current market state
        current_price = float(self.data['Close'].iloc[-1])
        current_percentile = float(self.percentiles.iloc[-1])
        current_date = self.data.index[-1]

        # Determine signal strength based on percentile thresholds
        reasoning = []
        risk_factors = []

        if current_percentile <= 5:
            signal_strength = 'strong_buy'
            confidence = 0.85
            entry_size = 100
            reasoning.append(f"Percentile at {current_percentile:.1f}% - historically top 5% entry zone")
            reasoning.append(f"Historical 5% entries: {len(self.entry_events_5)} trades analyzed")
        elif current_percentile <= 10:
            signal_strength = 'buy'
            confidence = 0.75
            entry_size = 75
            reasoning.append(f"Percentile at {current_percentile:.1f}% - good entry zone (top 10%)")
            reasoning.append(f"Historical 10% entries: {len(self.entry_events_10)} trades analyzed")
        elif current_percentile <= 15:
            signal_strength = 'buy'
            confidence = 0.65
            entry_size = 50
            reasoning.append(f"Percentile at {current_percentile:.1f}% - acceptable entry (top 15%)")
            reasoning.append(f"Historical 15% entries: {len(self.entry_events_15)} trades analyzed")
        elif current_percentile <= 25:
            signal_strength = 'neutral'
            confidence = 0.50
            entry_size = 25
            reasoning.append(f"Percentile at {current_percentile:.1f}% - edge diminishing")
            risk_factors.append("Not in optimal entry zone - wait for pullback")
        else:
            signal_strength = 'avoid'
            confidence = 0.30
            entry_size = 0
            reasoning.append(f"Percentile at {current_percentile:.1f}% - outside entry criteria")
            risk_factors.append("Too high in percentile range - risk of reversal elevated")

        # Calculate expected returns from historical data
        expected_7d, expected_14d, expected_21d, win_rate = self._calculate_expected_returns(
            current_percentile
        )

        # Add recent momentum check
        momentum_3d = (current_price / float(self.data['Close'].iloc[-4]) - 1) * 100
        if momentum_3d < -3:
            reasoning.append(f"3-day momentum: {momentum_3d:.1f}% - recent weakness")
        elif momentum_3d > 3:
            risk_factors.append(f"3-day momentum: +{momentum_3d:.1f}% - rapid rise, wait for consolidation")

        # Check volatility regime
        returns = np.log(self.data['Close'] / self.data['Close'].shift(1))
        current_vol = float(returns.tail(20).std() * np.sqrt(252) * 100)
        historical_vol_median = float(returns.rolling(20).std().quantile(0.5) * np.sqrt(252) * 100)

        if current_vol > historical_vol_median * 1.5:
            risk_factors.append(f"Elevated volatility: {current_vol:.1f}% annualized (median: {historical_vol_median:.1f}%)")
            entry_size = max(0, entry_size - 25)  # Reduce size in high vol

        # Add recent performance context
        if len(self.entry_events_5) > 0:
            recent_events = [e for e in self.entry_events_5
                           if pd.Timestamp(e['entry_date']) > current_date - timedelta(days=90)]
            if recent_events:
                # Calculate max return from progression
                recent_returns = []
                for e in recent_events:
                    if e['progression']:
                        max_day = max(e['progression'].keys())
                        recent_returns.append(e['progression'][max_day]['cumulative_return_pct'])

                if recent_returns:
                    avg_recent_return = np.mean(recent_returns)
                    reasoning.append(f"Recent 90-day similar entries: {len(recent_events)} trades, avg return: {avg_recent_return:.1f}%")

        return EntrySignal(
            ticker=self.ticker,
            current_price=current_price,
            current_percentile=current_percentile,
            signal_strength=signal_strength,
            confidence=confidence,
            expected_return_7d=expected_7d,
            expected_return_14d=expected_14d,
            expected_return_21d=expected_21d,
            win_rate_historical=win_rate,
            recommended_entry_size=entry_size,
            reasoning=reasoning,
            risk_factors=risk_factors
        )

    def generate_exit_signal(self,
                            entry_price: float,
                            entry_date_str: str) -> ExitSignal:
        """
        Generate exit signal for existing position.

        This is FORWARD LOOKING - you input when you entered, and we tell you
        what to do NOW based on current market conditions.

        Args:
            entry_price: Price at which position was entered
            entry_date_str: Entry date (ISO format string)

        Returns:
            ExitSignal with actionable recommendation
        """
        # Parse entry date
        try:
            entry_date = pd.Timestamp(entry_date_str)
        except Exception as e:
            raise ValueError(f"Invalid entry date format: {entry_date_str}. Expected ISO format (YYYY-MM-DD)")

        # Current state (TODAY - most recent data we have)
        current_idx = len(self.data) - 1
        current_date = self.data.index[current_idx]
        current_price = float(self.data['Close'].iloc[current_idx])

        # Ensure timezone compatibility for date comparison
        # If data index is timezone-aware, make entry_date timezone-aware too
        if hasattr(current_date, 'tz') and current_date.tz is not None:
            # Data has timezone, localize entry_date to match
            if entry_date.tz is None:
                entry_date = entry_date.tz_localize(current_date.tz)
        else:
            # Data is timezone-naive, ensure entry_date is too
            if entry_date.tz is not None:
                entry_date = entry_date.tz_localize(None)

        # Calculate days held (from entry to now)
        days_held = (current_date - entry_date).days

        # Validate that entry was in the past
        if days_held < 0:
            raise ValueError(f"Entry date {entry_date_str} is in the future. Please provide a past entry date.")

        if days_held == 0:
            raise ValueError(f"Entry date {entry_date_str} is today. Need at least 1 day to analyze position.")

        # Calculate current return based on entry price
        current_return = (current_price / entry_price - 1) * 100

        # Find the entry index in historical data (or closest date)
        # This is used for percentile lookback, not for future projection
        try:
            entry_idx = self.data.index.get_indexer([entry_date], method='nearest')[0]
        except Exception as e:
            # If we can't find the exact date, estimate based on current position
            # This handles weekend/holiday entries
            entry_idx = max(0, current_idx - days_held)

        # Ensure entry_idx is valid and before current
        entry_idx = max(0, min(entry_idx, current_idx - 1))

        # Use advanced trade manager to calculate exit pressure
        manager = AdvancedTradeManager(
            historical_data=self.data,
            rsi_ma_percentiles=self.percentiles,
            entry_idx=entry_idx,
            entry_percentile=float(self.percentiles.iloc[entry_idx]),
            entry_price=entry_price
        )

        exit_pressure_obj = manager.calculate_exit_pressure(current_idx, days_held)
        exit_pressure = float(exit_pressure_obj.overall_pressure)

        # Get exposure recommendation
        exposure_rec = manager.generate_exposure_recommendation(
            current_idx, days_held, self.entry_events_5 + self.entry_events_10
        )

        recommended_action = exposure_rec.action

        # Calculate trailing stop
        trailing_stop = float(manager.calculate_trailing_stop_level(current_idx, days_held))

        # Determine urgency
        if exit_pressure >= 80 or current_price <= trailing_stop:
            urgency = 'critical'
        elif exit_pressure >= 70:
            urgency = 'high'
        elif exit_pressure >= 50:
            urgency = 'medium'
        else:
            urgency = 'low'

        # Build reasoning
        reasoning = []
        reasoning.append(f"Current return: {current_return:+.1f}% after {days_held} days")
        reasoning.append(f"Exit pressure: {exit_pressure:.0f}/100")

        # Break down pressure components
        reasoning.append(f"  • Velocity: {exit_pressure_obj.percentile_velocity_component:.0f}/25 pts")
        reasoning.append(f"  • Time decay: {exit_pressure_obj.time_decay_component:.0f}/20 pts")
        reasoning.append(f"  • Divergence: {exit_pressure_obj.divergence_component:.0f}/25 pts")
        reasoning.append(f"  • Volatility: {exit_pressure_obj.volatility_component:.0f}/30 pts")

        # Add trade state
        state_info = manager.classify_trade_state(current_idx, days_held)
        reasoning.append(f"Trade state: {state_info.current_state.value.replace('_', ' ').title()}")

        # Expectancy comparison
        expected_hold = float(exposure_rec.expected_return_if_hold)
        expected_exit = float(exposure_rec.expected_return_if_exit)

        if expected_hold > expected_exit + 1:
            reasoning.append(f"Expected return if hold 7 more days: +{expected_hold:.1f}%")
        else:
            reasoning.append(f"Expected return if hold vs exit now: {expected_hold:.1f}% vs {expected_exit:.1f}%")

        # Stop level context
        stop_distance = ((current_price - trailing_stop) / current_price) * 100
        reasoning.append(f"Trailing stop: ${trailing_stop:.2f} ({stop_distance:.1f}% below current)")

        return ExitSignal(
            ticker=self.ticker,
            entry_price=entry_price,
            entry_date=entry_date_str,
            current_price=current_price,
            current_return=current_return,
            days_held=days_held,
            exit_pressure=exit_pressure,
            recommended_action=recommended_action,
            urgency=urgency,
            expected_return_if_hold_7d=expected_hold,
            expected_return_if_exit_now=expected_exit,
            trailing_stop=trailing_stop,
            reasoning=reasoning
        )

    def _calculate_expected_returns(self, current_percentile: float) -> tuple:
        """
        Calculate expected returns based on similar historical entry conditions.

        Returns:
            (expected_7d, expected_14d, expected_21d, win_rate)
        """
        # Find relevant historical events
        if current_percentile <= 5:
            events = self.entry_events_5
        elif current_percentile <= 10:
            events = self.entry_events_10
        elif current_percentile <= 15:
            events = self.entry_events_15
        else:
            events = self.entry_events_5 + self.entry_events_10 + self.entry_events_15

        if not events:
            return 0.0, 0.0, 0.0, 0.0

        # Calculate metrics from historical events
        returns_7d = []
        returns_14d = []
        returns_21d = []

        for event in events:
            prog = event['progression']
            if 7 in prog:
                returns_7d.append(prog[7]['cumulative_return_pct'])
            if 14 in prog:
                returns_14d.append(prog[14]['cumulative_return_pct'])
            if 21 in prog:
                returns_21d.append(prog[21]['cumulative_return_pct'])

        expected_7d = float(np.median(returns_7d)) if returns_7d else 0.0
        expected_14d = float(np.median(returns_14d)) if returns_14d else 0.0
        expected_21d = float(np.median(returns_21d)) if returns_21d else 0.0

        # Calculate win rate (any positive return at D21)
        wins = sum(1 for r in returns_21d if r > 0)
        win_rate = wins / len(returns_21d) if returns_21d else 0.0

        return expected_7d, expected_14d, expected_21d, win_rate


def generate_live_signals(ticker: str) -> Dict:
    """
    Generate all live signals for a ticker.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dictionary with entry signal and market context
    """
    generator = LiveSignalGenerator(ticker)

    entry_signal = generator.generate_entry_signal()

    # Get current market context
    current_price = float(generator.data['Close'].iloc[-1])
    price_52w_high = float(generator.data['Close'].tail(252).max())
    price_52w_low = float(generator.data['Close'].tail(252).min())

    distance_from_high = ((current_price - price_52w_high) / price_52w_high) * 100
    distance_from_low = ((current_price - price_52w_low) / price_52w_low) * 100

    result = {
        'ticker': ticker,
        'timestamp': datetime.now().isoformat(),
        'entry_signal': entry_signal.to_dict(),
        'market_context': {
            'current_price': current_price,
            '52w_high': price_52w_high,
            '52w_low': price_52w_low,
            'distance_from_52w_high_pct': distance_from_high,
            'distance_from_52w_low_pct': distance_from_low
        }
    }

    return _convert_numpy_types(result)


def generate_exit_signal_for_position(ticker: str,
                                      entry_price: float,
                                      entry_date: str) -> Dict:
    """
    Generate exit signal for an existing position.

    Args:
        ticker: Stock ticker symbol
        entry_price: Entry price
        entry_date: Entry date (ISO format)

    Returns:
        Dictionary with exit signal
    """
    generator = LiveSignalGenerator(ticker)

    exit_signal = generator.generate_exit_signal(entry_price, entry_date)

    result = {
        'ticker': ticker,
        'timestamp': datetime.now().isoformat(),
        'exit_signal': exit_signal.to_dict()
    }

    return _convert_numpy_types(result)
