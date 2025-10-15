"""
Position Management Framework - Dynamic Sizing Based on Divergence Analysis

This module analyzes historical divergence-convergence patterns to generate
concrete, actionable position management recommendations.

Key Questions Answered:
1. When should I take partial profits during a divergence?
2. How much should I take (25%, 50%, 75%, 100%)?
3. What divergence gap threshold triggers action?
4. When should I re-enter after convergence?
5. Are these thresholds ticker-specific?
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta


@dataclass
class DivergenceEvent:
    """Single divergence event with outcome tracking."""
    date: str
    daily_pct: float
    hourly_4h_pct: float
    divergence_gap: float  # abs(daily - 4h)
    divergence_direction: str  # '4h_overextended' or 'daily_overextended'

    # Outcome metrics
    return_if_held_7d: float
    return_if_held_14d: float
    max_drawdown_during_period: float
    max_upside_during_period: float
    time_to_convergence_hours: Optional[int]
    price_at_divergence: float


@dataclass
class PositionAction:
    """Recommended position action with rationale."""
    action_type: str  # 'TAKE_PROFIT', 'ADD_POSITION', 'HOLD', 'EXIT_ALL', 'REDUCE'
    position_change_pct: float  # How much to reduce/add (0-100%)
    confidence: float  # 0-100% based on sample size and win rate
    rationale: str

    # Supporting data
    historical_sample_size: int
    avg_return_if_action_taken: float
    avg_return_if_held: float
    win_rate: float
    max_risk: float
    max_reward: float


@dataclass
class ReEntrySignal:
    """Signal for when to re-enter position after taking profits."""
    should_reenter: bool
    reentry_size_pct: float  # 0-100% of original position
    convergence_level_current: float  # Current divergence gap
    convergence_threshold: float  # Trigger point for re-entry
    estimated_time_to_signal: Optional[int]  # Hours until re-entry if trending
    confidence: float


class PositionManager:
    """
    Analyzes divergence patterns to generate position management recommendations.
    """

    def __init__(self, ticker: str, rsi_length: int = 14, ma_length: int = 14):
        self.ticker = ticker.upper()
        self.rsi_length = rsi_length
        self.ma_length = ma_length

        # Fetch data using EXACT same approach as multi_timeframe_analyzer
        self.daily_data = self._fetch_data('1d', period='500d')
        self.hourly_data = self._fetch_data('1h', period='730d')  # 2 years of hourly

        # Calculate RSI-MA using EXACT same method
        self.daily_rsi_ma = self._calculate_rsi_ma(self.daily_data)
        self.hourly_4h_rsi_ma = self._calculate_rsi_ma_from_hourly(self.hourly_data)

        # Calculate percentile ranks using EXACT same method
        self.daily_percentiles = self._calculate_percentile_ranks(self.daily_rsi_ma)
        self.hourly_4h_percentiles = self._calculate_percentile_ranks(self.hourly_4h_rsi_ma)

    def _fetch_data(self, interval: str, period: str) -> pd.DataFrame:
        """Fetch OHLCV data - EXACT same as multi_timeframe_analyzer."""
        ticker_obj = yf.Ticker(self.ticker)
        data = ticker_obj.history(interval=interval, period=period)

        if data.empty:
            raise ValueError(f"Could not fetch {interval} data for {self.ticker}")

        return data

    def _calculate_rsi_ma(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate RSI-MA indicator - EXACT same as multi_timeframe_analyzer.

        Pipeline:
        1. Calculate log returns from Close price
        2. Calculate change of returns (diff)
        3. Apply RSI (14-period) using Wilder's method
        4. Apply EMA (14-period) to RSI
        """
        close_price = data['Close']

        # Step 1: Calculate log returns
        log_returns = np.log(close_price / close_price.shift(1)).fillna(0)

        # Step 2: Calculate change of returns (second derivative)
        delta = log_returns.diff()

        # Step 3: Apply RSI to delta
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)

        # Wilder's smoothing (RMA)
        avg_gains = gains.ewm(alpha=1/self.rsi_length, adjust=False).mean()
        avg_losses = losses.ewm(alpha=1/self.rsi_length, adjust=False).mean()

        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.fillna(50)

        # Step 4: Apply EMA to RSI
        rsi_ma = rsi.ewm(span=self.ma_length, adjust=False).mean()

        return rsi_ma

    def _calculate_rsi_ma_from_hourly(self, hourly_data: pd.DataFrame) -> pd.Series:
        """
        Calculate 4H RSI-MA - EXACT same as multi_timeframe_analyzer.
        Resample hourly to 4H bars, then align to daily.
        """
        # Resample to 4H bars
        data_4h = hourly_data.resample('4h').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()

        # Calculate RSI-MA on 4H data
        rsi_ma_4h = self._calculate_rsi_ma(data_4h)

        # Resample to daily frequency and forward-fill
        rsi_ma_daily_aligned = rsi_ma_4h.resample('1D').last().ffill()

        return rsi_ma_daily_aligned

    def _calculate_percentile_ranks(self, indicator: pd.Series, window: int = 252) -> pd.Series:
        """Calculate rolling percentile ranks - EXACT same as multi_timeframe_analyzer."""
        percentile_ranks = indicator.rolling(window=window).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100,
            raw=False
        )
        return percentile_ranks

    def analyze_divergence_outcomes(self) -> pd.DataFrame:
        """
        Analyze all historical divergence events and their outcomes.
        Uses EXACT same divergence calculation as multi_timeframe_analyzer.

        Returns DataFrame with:
        - divergence_pct (daily - 4h, signed)
        - divergence_category (4h_overextended, bullish_convergence, etc.)
        - return_if_held_7d
        - return_if_held_14d
        - max_drawdown
        - max_upside
        - time_to_convergence
        """
        # Align the two timeframes (both indexed by date)
        df = pd.DataFrame({
            'daily_pct': self.daily_percentiles,
            '4h_pct': self.hourly_4h_percentiles
        }).dropna()

        # Calculate divergence percentage - EXACT same as multi_timeframe_analyzer
        # Positive = Daily > 4H
        # Negative = 4H > Daily
        df['divergence_pct'] = df['daily_pct'] - df['4h_pct']
        df['divergence_gap'] = abs(df['divergence_pct'])

        # Classify divergence using EXACT same logic as multi_timeframe_analyzer
        df['divergence_category'] = 'none'

        # TYPE A: 4H Overextended (Daily low, 4H high)
        mask_4h_overextended = (df['divergence_pct'] < -15) & (df['daily_pct'] < 50)
        df.loc[mask_4h_overextended, 'divergence_category'] = '4h_overextended'

        # TYPE B: Bullish Convergence (Both low, aligned)
        mask_bullish_convergence = (df['divergence_gap'] < 15) & (df['daily_pct'] < 30)
        df.loc[mask_bullish_convergence, 'divergence_category'] = 'bullish_convergence'

        # TYPE C: Daily Overextended (Daily high, 4H low)
        mask_daily_overextended = (df['divergence_pct'] > 15) & (df['daily_pct'] > 50)
        df.loc[mask_daily_overextended, 'divergence_category'] = 'daily_overextended'

        # TYPE D: Bearish Convergence (Both high, aligned)
        mask_bearish_convergence = (df['divergence_gap'] < 15) & (df['daily_pct'] > 70)
        df.loc[mask_bearish_convergence, 'divergence_category'] = 'bearish_convergence'

        # Add price data
        df['Close'] = self.daily_data['Close']

        # Calculate forward returns and risk metrics
        df['return_7d'] = (df['Close'].shift(-7) - df['Close']) / df['Close'] * 100
        df['return_14d'] = (df['Close'].shift(-14) - df['Close']) / df['Close'] * 100

        # Calculate max drawdown and upside in next 14 days
        def calc_max_metrics(idx, dataframe, periods=14):
            if idx + periods >= len(dataframe):
                return None, None

            future_prices = dataframe['Close'].iloc[idx:idx+periods]
            current_price = dataframe['Close'].iloc[idx]

            max_dd = ((future_prices.min() - current_price) / current_price * 100)
            max_up = ((future_prices.max() - current_price) / current_price * 100)

            return max_dd, max_up

        max_metrics = [calc_max_metrics(i, df) for i in range(len(df))]
        df['max_drawdown_14d'] = [m[0] if m else None for m in max_metrics]
        df['max_upside_14d'] = [m[1] if m else None for m in max_metrics]

        # Calculate time to convergence (when gap < 10%)
        def calc_time_to_convergence(idx, dataframe):
            if dataframe['divergence_gap'].iloc[idx] < 10:
                return 0

            for i in range(idx + 1, min(idx + 60, len(dataframe))):  # Look forward max 60 days
                if dataframe['divergence_gap'].iloc[i] < 10:
                    return (i - idx)  # Days to convergence

            return None  # Didn't converge in 60 days

        df['time_to_convergence_days'] = [calc_time_to_convergence(i, df)
                                          for i in range(len(df))]

        return df.dropna()

    def get_profit_taking_rules(self, analysis_df: pd.DataFrame) -> Dict[str, Dict]:
        """
        Analyze optimal profit-taking thresholds based on divergence magnitude.

        Returns rules like:
        {
            'gap_15_25': {
                'take_profit_pct': 25,
                'rationale': '...',
                'stats': {...}
            },
            'gap_25_40': {...}
        }
        """
        if analysis_df.empty:
            return {}

        # Focus on 4H overextension (most common profit-taking scenario)
        diverged_4h = analysis_df[analysis_df['divergence_category'] == '4h_overextended'].copy()

        rules = {}

        # Define gap ranges to analyze
        gap_ranges = [
            (15, 25, '15-25%', 25),   # Small gap → 25% profit take
            (25, 40, '25-40%', 50),   # Medium gap → 50% profit take
            (40, 60, '40-60%', 75),   # Large gap → 75% profit take
            (60, 100, '60%+', 100),   # Extreme gap → 100% exit
        ]

        for min_gap, max_gap, label, suggested_take_pct in gap_ranges:
            subset = diverged_4h[
                (diverged_4h['divergence_gap'] >= min_gap) &
                (diverged_4h['divergence_gap'] < max_gap)
            ]

            if len(subset) < 3:  # Need minimum sample
                continue

            # Analyze what happened if you held vs took profit
            avg_return_7d = subset['return_7d'].mean()
            avg_return_14d = subset['return_14d'].mean()
            avg_max_dd = subset['max_drawdown_14d'].mean()
            avg_max_up = subset['max_upside_14d'].mean()

            # Win rate (positive return after 7 days)
            win_rate = (subset['return_7d'] > 0).sum() / len(subset) * 100

            # Calculate optimal take profit %
            # If avg return is negative and max drawdown is large → take more profit
            # If avg return is positive but volatile → take partial
            if avg_return_7d < -2 and avg_max_dd < -5:
                optimal_take_pct = 100  # Exit completely
            elif avg_return_7d < 0 and win_rate < 50:
                optimal_take_pct = 75  # Take most off
            elif avg_return_7d > 0 and win_rate > 60:
                optimal_take_pct = 25  # Small trim
            else:
                optimal_take_pct = suggested_take_pct

            # Build rationale
            rationale_parts = []
            if avg_return_7d < 0:
                rationale_parts.append(f"Avg 7d return: {avg_return_7d:.1f}% (negative)")
            else:
                rationale_parts.append(f"Avg 7d return: {avg_return_7d:.1f}% (positive)")

            rationale_parts.append(f"Win rate: {win_rate:.0f}%")
            rationale_parts.append(f"Avg max drawdown: {avg_max_dd:.1f}%")

            if avg_max_up > 5:
                rationale_parts.append(f"BUT avg max upside: +{avg_max_up:.1f}% (keep some exposure)")

            rules[f'gap_{label}'] = {
                'min_divergence_gap': min_gap,
                'max_divergence_gap': max_gap,
                'take_profit_pct': optimal_take_pct,
                'rationale': ' | '.join(rationale_parts),
                'stats': {
                    'sample_size': len(subset),
                    'avg_return_7d': round(avg_return_7d, 2),
                    'avg_return_14d': round(avg_return_14d, 2),
                    'win_rate': round(win_rate, 1),
                    'avg_max_drawdown': round(avg_max_dd, 2),
                    'avg_max_upside': round(avg_max_up, 2),
                    'avg_time_to_convergence_days': round(subset['time_to_convergence_days'].mean(), 1)
                }
            }

        return rules

    def get_reentry_rules(self, analysis_df: pd.DataFrame) -> Dict[str, Dict]:
        """
        Analyze when to re-enter position after taking profits.

        Returns rules for different convergence scenarios.
        """
        if analysis_df.empty:
            return {}

        # Analyze convergence events (when gap closes from large to small)
        convergence_events = []

        for i in range(len(analysis_df) - 1):
            current_gap = analysis_df['divergence_gap'].iloc[i]
            next_gap = analysis_df['divergence_gap'].iloc[i + 1]

            # Detect convergence: gap was large (>25%), now smaller (<15%)
            if current_gap > 25 and next_gap < 15:
                future_return_7d = analysis_df['return_7d'].iloc[i + 1]
                future_return_14d = analysis_df['return_14d'].iloc[i + 1]

                convergence_events.append({
                    'convergence_gap': next_gap,
                    'return_7d': future_return_7d,
                    'return_14d': future_return_14d,
                    'daily_pct': analysis_df['daily_pct'].iloc[i + 1],
                    'hourly_4h_pct': analysis_df['4h_pct'].iloc[i + 1]
                })

        if not convergence_events:
            return {}

        conv_df = pd.DataFrame(convergence_events)

        # Analyze different convergence scenarios
        rules = {}

        # Scenario 1: Convergence in oversold zone (both < 30%)
        oversold_conv = conv_df[
            (conv_df['daily_pct'] < 30) & (conv_df['hourly_4h_pct'] < 30)
        ]

        if len(oversold_conv) >= 3:
            rules['convergence_oversold'] = {
                'condition': 'Gap < 15% AND both Daily < 30% AND 4H < 30%',
                'action': 'Re-enter 75-100% of original position',
                'rationale': f"Strong buy signal. Avg 7d return: {oversold_conv['return_7d'].mean():.1f}%",
                'stats': {
                    'sample_size': len(oversold_conv),
                    'avg_return_7d': round(oversold_conv['return_7d'].mean(), 2),
                    'win_rate': round((oversold_conv['return_7d'] > 0).sum() / len(oversold_conv) * 100, 1)
                }
            }

        # Scenario 2: Convergence in neutral zone (both 30-70%)
        neutral_conv = conv_df[
            (conv_df['daily_pct'].between(30, 70)) &
            (conv_df['hourly_4h_pct'].between(30, 70))
        ]

        if len(neutral_conv) >= 3:
            rules['convergence_neutral'] = {
                'condition': 'Gap < 15% AND both Daily 30-70% AND 4H 30-70%',
                'action': 'Re-enter 25-50% of original position',
                'rationale': f"Moderate signal. Avg 7d return: {neutral_conv['return_7d'].mean():.1f}%",
                'stats': {
                    'sample_size': len(neutral_conv),
                    'avg_return_7d': round(neutral_conv['return_7d'].mean(), 2),
                    'win_rate': round((neutral_conv['return_7d'] > 0).sum() / len(neutral_conv) * 100, 1)
                }
            }

        # Scenario 3: Convergence in overbought zone (both > 70%)
        overbought_conv = conv_df[
            (conv_df['daily_pct'] > 70) & (conv_df['hourly_4h_pct'] > 70)
        ]

        if len(overbought_conv) >= 3:
            rules['convergence_overbought'] = {
                'condition': 'Gap < 15% AND both Daily > 70% AND 4H > 70%',
                'action': 'Stay out or short',
                'rationale': f"Bearish signal. Avg 7d return: {overbought_conv['return_7d'].mean():.1f}%",
                'stats': {
                    'sample_size': len(overbought_conv),
                    'avg_return_7d': round(overbought_conv['return_7d'].mean(), 2),
                    'win_rate': round((overbought_conv['return_7d'] > 0).sum() / len(overbought_conv) * 100, 1)
                }
            }

        return rules

    def get_current_recommendation(self) -> Dict:
        """
        Get current position management recommendation based on latest data.
        Uses EXACT same calculation as multi_timeframe_analyzer.
        """
        # Get latest percentile values - EXACT same approach
        latest_daily_pct = float(self.daily_percentiles.iloc[-1])
        latest_4h_pct = float(self.hourly_4h_percentiles.iloc[-1])

        # Calculate divergence - EXACT same as multi_timeframe_analyzer
        # Positive = Daily > 4H, Negative = 4H > Daily
        latest_divergence = latest_daily_pct - latest_4h_pct
        latest_gap = abs(latest_divergence)

        # Analyze historical patterns
        analysis_df = self.analyze_divergence_outcomes()
        profit_rules = self.get_profit_taking_rules(analysis_df)
        reentry_rules = self.get_reentry_rules(analysis_df)

        # Determine current state - EXACT same logic as multi_timeframe_analyzer
        if latest_divergence < -15 and latest_daily_pct < 50:
            divergence_state = '4h_overextended'
        elif latest_gap < 15 and latest_daily_pct < 30:
            divergence_state = 'bullish_convergence'
        elif latest_divergence > 15 and latest_daily_pct > 50:
            divergence_state = 'daily_overextended'
        elif latest_gap < 15 and latest_daily_pct > 70:
            divergence_state = 'bearish_convergence'
        else:
            divergence_state = 'aligned'

        # Find matching rule
        action = None
        matched_rule = None

        if divergence_state == '4h_overextended':
            for rule_name, rule in profit_rules.items():
                if rule['min_divergence_gap'] <= latest_gap < rule['max_divergence_gap']:
                    matched_rule = rule
                    action = PositionAction(
                        action_type='TAKE_PROFIT',
                        position_change_pct=rule['take_profit_pct'],
                        confidence=min(100, rule['stats']['sample_size'] * 10),  # More samples = higher confidence
                        rationale=rule['rationale'],
                        historical_sample_size=rule['stats']['sample_size'],
                        avg_return_if_action_taken=rule['stats']['avg_return_7d'] * (100 - rule['take_profit_pct']) / 100,
                        avg_return_if_held=rule['stats']['avg_return_7d'],
                        win_rate=rule['stats']['win_rate'],
                        max_risk=rule['stats']['avg_max_drawdown'],
                        max_reward=rule['stats']['avg_max_upside']
                    )
                    break

        elif divergence_state == 'bullish_convergence':
            # Re-entry signal - both oversold and aligned
            if 'convergence_oversold' in reentry_rules:
                rule = reentry_rules['convergence_oversold']
                action = PositionAction(
                    action_type='ADD_POSITION',
                    position_change_pct=75,
                    confidence=min(100, rule['stats']['sample_size'] * 10),
                    rationale=rule['rationale'],
                    historical_sample_size=rule['stats']['sample_size'],
                    avg_return_if_action_taken=rule['stats']['avg_return_7d'],
                    avg_return_if_held=0,  # No position currently
                    win_rate=rule['stats']['win_rate'],
                    max_risk=-10,  # Estimate
                    max_reward=15   # Estimate
                )

        if action is None:
            action = PositionAction(
                action_type='HOLD',
                position_change_pct=0,
                confidence=50,
                rationale='No clear signal based on historical patterns',
                historical_sample_size=0,
                avg_return_if_action_taken=0,
                avg_return_if_held=0,
                win_rate=50,
                max_risk=-5,
                max_reward=5
            )

        return {
            'ticker': self.ticker,
            'current_state': {
                'daily_percentile': round(latest_daily_pct, 1),
                'hourly_4h_percentile': round(latest_4h_pct, 1),
                'divergence_gap': round(latest_gap, 1),
                'divergence_state': divergence_state
            },
            'recommendation': {
                'action': action.action_type,
                'position_change_pct': action.position_change_pct,
                'confidence': round(action.confidence, 0),
                'rationale': action.rationale,
                'expected_return_if_action': round(action.avg_return_if_action_taken, 2),
                'expected_return_if_hold': round(action.avg_return_if_held, 2),
                'win_rate': round(action.win_rate, 1),
                'max_risk': round(action.max_risk, 2),
                'max_reward': round(action.max_reward, 2),
                'sample_size': action.historical_sample_size
            },
            'profit_taking_rules': profit_rules,
            'reentry_rules': reentry_rules
        }


def get_position_management(ticker: str) -> Dict:
    """
    Main function to get position management recommendations for a ticker.
    """
    manager = PositionManager(ticker)
    return manager.get_current_recommendation()
