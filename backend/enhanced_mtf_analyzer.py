#!/usr/bin/env python3
"""
Enhanced Multi-Timeframe Divergence Analyzer with Intraday Tracking

Key improvements:
1. Multiple time horizons: 1-3×4H bars, 1D-2D, 7D
2. Three intraday checkpoints: morning, midday, close
3. Divergence event lifecycle tracking
4. Convergence decay modeling
5. Take vs Hold analysis with actionable insights
"""

import numpy as np
import pandas as pd
import yfinance as yf
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from scipy import stats


@dataclass
class IntradayCheckpoint:
    """Single intraday checkpoint measurement."""
    checkpoint_time: str  # 'morning', 'midday', 'close'
    bar_index: int  # Which 4H bar (0=first, 5=last of day)
    daily_percentile: float
    hourly_4h_percentile: float
    divergence_pct: float
    price: float


@dataclass
class DivergenceLifecycle:
    """Complete lifecycle of a divergence event."""
    trigger_date: str
    trigger_checkpoint: IntradayCheckpoint

    # Trigger conditions
    initial_gap: float
    gap_category: str  # 'small' (15-25%), 'medium' (25-35%), 'large' (35%+)

    # Intraday outcomes (1-6 × 4H bars)
    returns_4h: Dict[int, float]  # Key: bar count (1-6), Value: return %

    # Daily outcomes (1-7 days)
    returns_daily: Dict[int, float]  # Key: day count, Value: return %

    # Convergence tracking
    convergence_bar: Optional[int]  # Which 4H bar converged (None if didn't)
    convergence_day: Optional[int]  # Which day converged
    time_to_convergence_hours: Optional[float]

    # Overshoot tracking
    max_gap_expansion: float  # Did gap widen before closing?
    max_gap_bar: int  # When did max gap occur?

    # Action outcomes
    take_profit_outcome: Dict[str, float]  # If exited at various checkpoints
    hold_outcome: Dict[str, float]  # If held through period

    # Re-entry opportunity
    reentry_bar: Optional[int]  # When did re-entry signal occur?
    reentry_return: Optional[float]  # Return from re-entry point


@dataclass
class MultiHorizonOutcome:
    """Compare outcomes across multiple time horizons."""
    horizon_label: str  # '1×4H', '2×4H', '1D', '2D', etc.
    take_profit_return: float
    hold_return: float
    delta: float  # Benefit of taking action
    sample_size: int
    win_rate: float


@dataclass
class SignalQuality:
    """Signal quality metrics based on historical performance."""
    hit_rate: float  # % of times signal was profitable
    avg_return: float
    sharpe_ratio: float
    max_drawdown: float
    consistency_score: float  # 0-100


@dataclass
class VolatilityContext:
    """Current market volatility context."""
    current_atr: float
    historical_atr_percentile: float  # Where current ATR ranks
    volatility_regime: str  # 'low', 'normal', 'high', 'extreme'


@dataclass
class DivergenceDecayModel:
    """Statistical model of divergence decay (convergence speed)."""
    avg_decay_rate_per_4h: float  # % gap reduction per 4H bar
    median_time_to_convergence_hours: float
    convergence_probability_24h: float  # % that converge within 24h
    convergence_probability_48h: float
    convergence_probability_by_gap_size: Dict[str, float]  # By gap category


@dataclass
class ReentryOpportunity:
    """Re-entry signal after taking profits."""
    reentry_bar: int  # Which 4H bar after exit
    reentry_date: str
    gap_at_reentry: float  # Divergence gap when re-entry triggered
    daily_percentile_at_reentry: float
    hourly_4h_percentile_at_reentry: float
    reentry_price: float
    forward_return_1d: float  # Return 1 day after re-entry
    forward_return_3d: float  # Return 3 days after re-entry
    triggered_because: str  # Reason for re-entry signal


@dataclass
class VolatilityAwareMetrics:
    """Performance metrics segmented by volatility regime."""
    regime: str  # 'low', 'normal', 'high', 'extreme'
    sample_size: int
    avg_intraday_edge: float  # 3×4H advantage
    optimal_exit_horizon: str  # Best horizon for this regime
    hit_rate: float
    avg_return: float
    recommended_action: str  # More/less aggressive based on regime


@dataclass
class RegimeFilteredGapAnalysis:
    """Detailed analysis of specific gap size in specific volatility regime."""
    gap_range: str  # e.g., '30-35%'
    regime: str  # 'low', 'normal', 'high', 'extreme'
    sample_size: int

    # Absolute returns (not deltas)
    avg_return_1x4h: float
    avg_return_2x4h: float
    avg_return_3x4h: float
    avg_return_1d: float
    avg_return_2d: float

    # Win rates
    win_rate_1x4h: float
    win_rate_2x4h: float
    win_rate_3x4h: float
    win_rate_1d: float
    win_rate_2d: float

    # Best performance
    best_horizon: str
    best_avg_return: float
    best_win_rate: float

    # Expectancy (edge after costs)
    expectancy_2x4h: float  # Primary focus
    avg_win_size: float
    avg_loss_size: float
    win_loss_ratio: float


@dataclass
class ReentryBreakdown:
    """Re-entry performance by gap size and regime."""
    gap_category: str  # 'small', 'medium', 'large'
    regime: str
    sample_size: int
    reentry_rate: float  # % that generate re-entry
    avg_time_to_reentry: float  # hours
    avg_reentry_return: float  # return from re-entry point
    reentry_success_rate: float  # % of re-entries that are profitable
    reentry_expectancy: float  # (success_rate × avg_win) - (fail_rate × avg_loss)


@dataclass
class TradeRecommendation:
    """Actionable trade recommendation based on analysis."""
    setup_name: str  # e.g., "30-35% Gap in Normal Volatility"
    trade_signal: bool  # True = tradeable, False = skip
    confidence: str  # 'high', 'medium', 'low'

    # Entry
    gap_range: str
    regime_filter: str  # Required volatility regime

    # Exit
    recommended_exit: str  # e.g., '2×4H'
    expected_return: float
    win_rate: float
    expectancy: float

    # Risk
    sample_size: int
    max_consecutive_losses: int
    recommended_position_size: float  # % of capital

    # Reasoning
    reason_tradeable: str
    risks: List[str]


class EnhancedMultiTimeframeAnalyzer:
    """
    Enhanced analyzer with intraday tracking and lifecycle modeling.
    """

    def __init__(self,
                 ticker: str,
                 lookback_days: int = 1095,  # Increased to 1095 (3 years) for maximum sample size
                 rsi_length: int = 14,
                 ma_length: int = 14):
        """
        Initialize Enhanced Multi-Timeframe Analyzer.

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
            lookback_days: Days of historical data to analyze (NOW 3 YEARS for statistical validity)
            rsi_length: RSI calculation period (14 bars standard)
            ma_length: Moving average smoothing period (14 bars standard)

        Key Terminology:
            - 1×4H, 2×4H, 3×4H: Represents 4-hour bar intervals (4h, 8h, 12h)
            - Gap/Divergence: Absolute difference between Daily and 4H percentiles
            - Convergence: Gap closing below 15% threshold
            - R: Risk unit (not used in this implementation - notation is time-based)

        Sample Size Target:
            - 3 years of data should yield 500-800 divergence events
            - 30-35% gaps: target 80-120 events (up from 52)
            - 35%+ gaps: target 50-80 events (up from 38)
        """
        self.ticker = ticker.upper()
        self.lookback_days = lookback_days
        self.rsi_length = rsi_length
        self.ma_length = ma_length

        # Fetch data
        print(f"\nFetching data for {self.ticker}...")
        self.daily_data = self._fetch_data(interval='1d', period=f'{lookback_days}d')
        # Fetch hourly data (Yahoo Finance limits 1h data to 730 days max)
        hourly_period = min(730, lookback_days)
        self.hourly_data = self._fetch_data(interval='1h', period=f'{hourly_period}d')

        # Calculate indicators
        print("Calculating indicators...")
        self.daily_rsi_ma = self._calculate_rsi_ma(self.daily_data)
        self.hourly_4h_df = self._calculate_4h_rsi_ma(self.hourly_data)

        # Calculate percentiles
        self.daily_percentiles = self._calculate_percentile_ranks(self.daily_rsi_ma)
        self.hourly_4h_percentiles = self._calculate_percentile_ranks(self.hourly_4h_df['rsi_ma'])

        # Calculate ATR for volatility context
        self.daily_atr = self._calculate_atr(self.daily_data)

    def _fetch_data(self, interval: str, period: str) -> pd.DataFrame:
        """Fetch OHLCV data."""
        ticker_obj = yf.Ticker(self.ticker)
        data = ticker_obj.history(interval=interval, period=period)
        if data.empty:
            raise ValueError(f"Could not fetch {interval} data for {self.ticker}")
        print(f"  ✓ Fetched {len(data)} {interval} bars")
        return data

    def _calculate_rsi_ma(self, data: pd.DataFrame) -> pd.Series:
        """Calculate RSI-MA indicator (matching TradingView implementation)."""
        close_price = data['Close']

        # Log returns
        log_returns = np.log(close_price / close_price.shift(1)).fillna(0)

        # Change of returns (second derivative)
        delta = log_returns.diff()

        # RSI on delta
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)

        avg_gains = gains.ewm(alpha=1/self.rsi_length, adjust=False).mean()
        avg_losses = losses.ewm(alpha=1/self.rsi_length, adjust=False).mean()

        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.fillna(50)

        # EMA on RSI
        rsi_ma = rsi.ewm(span=self.ma_length, adjust=False).mean()

        return rsi_ma

    def _calculate_4h_rsi_ma(self, hourly_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate 4H RSI-MA, keeping ALL 4H bars (not just daily closes).
        This allows us to track intraday checkpoints.
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

        return pd.DataFrame({
            'rsi_ma': rsi_ma_4h,
            'close': data_4h['Close'],
            'high': data_4h['High'],
            'low': data_4h['Low'],
        })

    def _calculate_percentile_ranks(self, indicator: pd.Series, window: int = 252) -> pd.Series:
        """Calculate rolling percentile ranks."""
        percentile_ranks = indicator.rolling(window=window).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100,
            raw=False
        )
        return percentile_ranks

    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high = data['High']
        low = data['Low']
        close = data['Close']

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(span=period, adjust=False).mean()

        return atr

    def _get_intraday_checkpoints(self, date: pd.Timestamp) -> List[IntradayCheckpoint]:
        """
        Get three intraday checkpoints for a given date.

        Checkpoints:
        - Morning: 2nd 4H bar (around 10-11am)
        - Midday: 4th 4H bar (around 2-3pm)
        - Close: 6th 4H bar (end of day)
        """
        date_str = date.strftime('%Y-%m-%d')

        # Get all 4H bars for this date
        day_4h_bars = self.hourly_4h_df[date_str:date_str]

        if len(day_4h_bars) == 0:
            return []

        # Get daily percentile for this date
        if date not in self.daily_percentiles.index:
            return []
        daily_pct = float(self.daily_percentiles.loc[date])

        checkpoints = []

        # Define checkpoint indices (0-indexed)
        checkpoint_configs = [
            ('morning', 1),  # 2nd bar
            ('midday', 3),   # 4th bar
            ('close', -1),   # Last bar
        ]

        for cp_name, cp_idx in checkpoint_configs:
            if cp_idx == -1:
                cp_idx = len(day_4h_bars) - 1

            if cp_idx < len(day_4h_bars):
                bar = day_4h_bars.iloc[cp_idx]
                bar_date = day_4h_bars.index[cp_idx]

                # Get 4H percentile - handle potential duplicate indices
                if bar_date in self.hourly_4h_percentiles.index:
                    hourly_pct_vals = self.hourly_4h_percentiles.loc[bar_date]
                    # If multiple values for same timestamp, take the last one
                    if isinstance(hourly_pct_vals, pd.Series):
                        hourly_pct = float(hourly_pct_vals.iloc[-1])
                    else:
                        hourly_pct = float(hourly_pct_vals)

                    div_pct = daily_pct - hourly_pct

                    checkpoint = IntradayCheckpoint(
                        checkpoint_time=cp_name,
                        bar_index=cp_idx,
                        daily_percentile=daily_pct,
                        hourly_4h_percentile=hourly_pct,
                        divergence_pct=div_pct,
                        price=float(bar['close'])
                    )
                    checkpoints.append(checkpoint)

        return checkpoints

    def _calculate_forward_4h_returns(self,
                                      entry_date: pd.Timestamp,
                                      entry_price: float,
                                      num_bars: int = 6) -> Dict[int, float]:
        """Calculate returns for next N × 4H bars."""
        returns_4h = {}

        # Find entry bar in 4H data
        entry_4h_idx = self.hourly_4h_df.index.get_indexer([entry_date], method='ffill')[0]

        for i in range(1, num_bars + 1):
            future_idx = entry_4h_idx + i
            if future_idx < len(self.hourly_4h_df):
                future_price = self.hourly_4h_df.iloc[future_idx]['close']
                ret = (future_price / entry_price - 1) * 100
                returns_4h[i] = float(ret)

        return returns_4h

    def _calculate_forward_daily_returns(self,
                                         entry_date: pd.Timestamp,
                                         entry_price: float,
                                         num_days: int = 7) -> Dict[int, float]:
        """Calculate returns for next N days."""
        returns_daily = {}

        # Find entry date in daily data
        entry_daily_idx = self.daily_data.index.get_indexer([entry_date], method='ffill')[0]

        for i in range(1, num_days + 1):
            future_idx = entry_daily_idx + i
            if future_idx < len(self.daily_data):
                future_price = self.daily_data.iloc[future_idx]['Close']
                ret = (future_price / entry_price - 1) * 100
                returns_daily[i] = float(ret)

        return returns_daily

    def _find_convergence(self,
                         entry_date: pd.Timestamp,
                         initial_gap: float,
                         max_bars: int = 24) -> Tuple[Optional[int], Optional[float]]:
        """
        Find when divergence converges (gap closes to <15%).

        CONVERGENCE DEFINITION:
        - Initial gap (e.g., 25%) closes to below 15% threshold
        - Measured as absolute difference between Daily and 4H percentiles
        - Example: Daily=75%, 4H=50% (25% gap) → Daily=60%, 4H=50% (10% gap) = CONVERGED

        TIME HORIZON:
        - Looks forward up to 24 × 4H bars (96 hours = 4 days)
        - Returns bar index and hours elapsed when convergence occurs
        - Returns (None, None) if convergence doesn't occur within window

        Returns:
            (convergence_bar, time_to_convergence_hours)
        """
        # Find entry bar
        entry_4h_idx = self.hourly_4h_df.index.get_indexer([entry_date], method='ffill')[0]

        convergence_threshold = 15.0  # Gap must close below 15% to be considered converged

        for i in range(1, max_bars + 1):
            future_idx = entry_4h_idx + i
            if future_idx >= len(self.hourly_4h_df):
                break

            future_date = self.hourly_4h_df.index[future_idx]

            # Get daily and 4H percentiles at this point - use string matching for timezone
            future_daily_date_str = future_date.strftime('%Y-%m-%d')
            matching_daily_dates = [d for d in self.daily_percentiles.index if d.strftime('%Y-%m-%d') == future_daily_date_str]

            if not matching_daily_dates:
                continue

            daily_pct = self.daily_percentiles.loc[matching_daily_dates[0]]

            # Handle potential duplicate indices
            if future_date in self.hourly_4h_percentiles.index:
                hourly_pct_vals = self.hourly_4h_percentiles.loc[future_date]
                if isinstance(hourly_pct_vals, pd.Series):
                    hourly_pct = hourly_pct_vals.iloc[-1]
                else:
                    hourly_pct = hourly_pct_vals
            else:
                continue

            current_gap = abs(daily_pct - hourly_pct)

            if current_gap < convergence_threshold:
                time_hours = i * 4  # Each bar is 4 hours
                return (i, float(time_hours))

        return (None, None)

    def _track_gap_expansion(self,
                            entry_date: pd.Timestamp,
                            initial_gap: float,
                            max_bars: int = 12) -> Tuple[float, int]:
        """
        Track if divergence gap expands before closing.

        Returns:
            (max_gap_expansion, max_gap_bar)
        """
        entry_4h_idx = self.hourly_4h_df.index.get_indexer([entry_date], method='ffill')[0]

        max_gap = abs(initial_gap)
        max_gap_bar = 0

        for i in range(1, max_bars + 1):
            future_idx = entry_4h_idx + i
            if future_idx >= len(self.hourly_4h_df):
                break

            future_date = self.hourly_4h_df.index[future_idx]

            # Use string matching for timezone-aware indices
            future_daily_date_str = future_date.strftime('%Y-%m-%d')
            matching_daily_dates = [d for d in self.daily_percentiles.index if d.strftime('%Y-%m-%d') == future_daily_date_str]

            if not matching_daily_dates:
                continue

            daily_pct = self.daily_percentiles.loc[matching_daily_dates[0]]

            # Handle potential duplicate indices
            if future_date in self.hourly_4h_percentiles.index:
                hourly_pct_vals = self.hourly_4h_percentiles.loc[future_date]
                if isinstance(hourly_pct_vals, pd.Series):
                    hourly_pct = hourly_pct_vals.iloc[-1]
                else:
                    hourly_pct = hourly_pct_vals
            else:
                continue

            current_gap = abs(daily_pct - hourly_pct)

            if current_gap > max_gap:
                max_gap = current_gap
                max_gap_bar = i

        return (float(max_gap), max_gap_bar)

    def _find_reentry_opportunity(self,
                                  entry_date: pd.Timestamp,
                                  initial_gap: float,
                                  entry_price: float,
                                  max_bars: int = 12,
                                  relaxed: bool = True) -> Tuple[Optional[int], Optional[float]]:
        """
        Find re-entry opportunity after taking profits.

        RE-ENTRY LOGIC (RELAXED THRESHOLDS FOR BETTER SIGNAL DETECTION):

        Conditions (all must be met):
        1. Wait minimum 12 hours (3 × 4H bars) after initial exit
        2. Gap converged below 15% (from initial trigger level, e.g., 25% → 12%)
        3. Both Daily AND 4H percentiles below 35th percentile (oversold condition)
        4. Measure expected return 1 day forward from re-entry point

        THRESHOLD COMPARISON:
        Relaxed (default):  Gap < 15%, Percentiles < 35%
        Strict (optional):  Gap < 10%, Percentiles < 30%

        RATIONALE:
        - Relaxed thresholds increase signal frequency while maintaining quality
        - Gap below 15% indicates divergence is resolving (convergence)
        - Both timeframes oversold (< 35%) suggests renewed upside potential

        EXPECTED RETURN:
        - Calculated as: (Price_1d_after_reentry - Reentry_price) / Reentry_price * 100
        - Measures whether re-entering after convergence provides edge

        Args:
            entry_date: Original signal entry date
            initial_gap: Original divergence gap size at trigger
            entry_price: Price at original entry
            max_bars: Maximum bars forward to search for re-entry (default 12 = 48 hours)
            relaxed: If True, use relaxed thresholds (15%, 35%)
                    If False, use strict thresholds (10%, 30%)

        Returns:
            (reentry_bar, reentry_expected_return) or (None, None) if no re-entry found
        """
        entry_4h_idx = self.hourly_4h_df.index.get_indexer([entry_date], method='ffill')[0]

        # Set thresholds based on mode
        gap_threshold = 15.0 if relaxed else 10.0          # Convergence threshold
        percentile_threshold = 35.0 if relaxed else 30.0   # Oversold threshold

        for i in range(3, max_bars + 1):  # Start from 3rd bar (12 hours after exit)
            future_idx = entry_4h_idx + i
            if future_idx >= len(self.hourly_4h_df):
                break

            future_date = self.hourly_4h_df.index[future_idx]

            # Use string matching for timezone-aware indices
            future_daily_date_str = future_date.strftime('%Y-%m-%d')
            matching_daily_dates = [d for d in self.daily_percentiles.index if d.strftime('%Y-%m-%d') == future_daily_date_str]

            if not matching_daily_dates:
                continue

            future_daily_date = matching_daily_dates[0]
            daily_pct = self.daily_percentiles.loc[future_daily_date]

            # Handle potential duplicate indices
            if future_date in self.hourly_4h_percentiles.index:
                hourly_pct_vals = self.hourly_4h_percentiles.loc[future_date]
                if isinstance(hourly_pct_vals, pd.Series):
                    hourly_pct = hourly_pct_vals.iloc[-1]
                else:
                    hourly_pct = hourly_pct_vals
            else:
                continue

            current_gap = abs(daily_pct - hourly_pct)

            # Re-entry condition 1: Gap converging
            if current_gap >= gap_threshold:
                continue

            # Re-entry condition 2: Both oversold
            if daily_pct >= percentile_threshold or hourly_pct >= percentile_threshold:
                continue

            # Found re-entry opportunity!
            # Calculate expected return from this re-entry point
            reentry_price = self.hourly_4h_df.iloc[future_idx]['close']

            # Look 1 day forward from re-entry
            reentry_daily_idx = self.daily_data.index.get_indexer([future_daily_date], method='ffill')[0]
            if reentry_daily_idx + 1 < len(self.daily_data):
                future_price_1d = self.daily_data.iloc[reentry_daily_idx + 1]['Close']
                expected_return = (future_price_1d / reentry_price - 1) * 100
                return (i, float(expected_return))

        return (None, None)

    def backtest_with_lifecycle_tracking(self,
                                        min_divergence_pct: float = 15.0) -> List[DivergenceLifecycle]:
        """
        Backtest divergence events with full lifecycle tracking.

        This is the core improvement: we now track what happens
        at 1×4H, 2×4H, 3×4H intervals, not just daily outcomes.
        """
        print(f"\n🔬 Backtesting with lifecycle tracking (min divergence: {min_divergence_pct}%)...")

        lifecycles = []

        # Find first valid date (where percentiles are not NaN)
        first_valid_idx = self.daily_percentiles.first_valid_index()
        if first_valid_idx is None:
            print("  ⚠️  No valid percentile data available!")
            return lifecycles

        first_valid_pos = self.daily_data.index.get_loc(first_valid_idx)

        # Iterate through daily data (starting from first valid percentile)
        for i in range(first_valid_pos, len(self.daily_data) - 30):  # Leave buffer for forward returns
            date = self.daily_data.index[i]

            # Get intraday checkpoints for this date
            checkpoints = self._get_intraday_checkpoints(date)

            if not checkpoints:
                continue

            # Check each checkpoint for divergence signals
            for checkpoint in checkpoints:
                abs_div = abs(checkpoint.divergence_pct)

                if abs_div < min_divergence_pct:
                    continue

                # Categorize gap size
                if abs_div >= 35:
                    gap_category = 'large'
                elif abs_div >= 25:
                    gap_category = 'medium'
                else:
                    gap_category = 'small'

                # Calculate forward returns (intraday)
                returns_4h = self._calculate_forward_4h_returns(
                    date, checkpoint.price, num_bars=6
                )

                # Calculate forward returns (daily)
                returns_daily = self._calculate_forward_daily_returns(
                    date, checkpoint.price, num_days=7
                )

                # Find convergence
                convergence_bar, time_to_convergence = self._find_convergence(
                    date, checkpoint.divergence_pct
                )

                # Determine convergence day
                convergence_day = None
                if convergence_bar:
                    convergence_day = (convergence_bar // 6) + 1  # 6 bars per day

                # Track gap expansion
                max_gap, max_gap_bar = self._track_gap_expansion(
                    date, checkpoint.divergence_pct
                )

                # Calculate take profit vs hold outcomes
                take_profit_outcome = {
                    '1x4h': returns_4h.get(1, 0),
                    '2x4h': returns_4h.get(2, 0),
                    '3x4h': returns_4h.get(3, 0),
                }

                hold_outcome = {
                    '1d': returns_daily.get(1, 0),
                    '2d': returns_daily.get(2, 0),
                    '7d': returns_daily.get(7, 0),
                }

                # Track re-entry opportunity
                reentry_bar, reentry_return = self._find_reentry_opportunity(
                    date, checkpoint.divergence_pct, checkpoint.price
                )

                # Create lifecycle object
                lifecycle = DivergenceLifecycle(
                    trigger_date=date.strftime('%Y-%m-%d'),
                    trigger_checkpoint=checkpoint,
                    initial_gap=abs_div,
                    gap_category=gap_category,
                    returns_4h=returns_4h,
                    returns_daily=returns_daily,
                    convergence_bar=convergence_bar,
                    convergence_day=convergence_day,
                    time_to_convergence_hours=time_to_convergence,
                    max_gap_expansion=max_gap,
                    max_gap_bar=max_gap_bar,
                    take_profit_outcome=take_profit_outcome,
                    hold_outcome=hold_outcome,
                    reentry_bar=reentry_bar,
                    reentry_return=reentry_return
                )

                lifecycles.append(lifecycle)

        print(f"  ✓ Found {len(lifecycles)} divergence lifecycle events")
        return lifecycles

    def analyze_multi_horizon_outcomes(self,
                                      lifecycles: List[DivergenceLifecycle]) -> List[MultiHorizonOutcome]:
        """
        Analyze "Take vs Hold" across multiple time horizons.

        OBJECTIVE:
        Determine whether taking profits early (intraday) provides better returns
        than holding through longer periods.

        KEY QUESTION:
        Should I exit at 1×4H (4 hours) or hold through 1D (24 hours)?

        HORIZON DEFINITIONS:
        - 1×4H: Exit after 4 hours vs. hold to 1 day
        - 2×4H: Exit after 8 hours vs. hold to 1 day
        - 3×4H: Exit after 12 hours vs. hold to 1 day (PRIMARY METRIC)
        - 1D:   Hold 1 day vs. hold to 2 days
        - 2D:   Hold 2 days vs. hold to 7 days

        DELTA (EDGE) CALCULATION:
        Delta = Avg(Take Profit Return) - Avg(Hold Return)
        - Positive delta: Taking profits early is better
        - Negative delta: Holding longer is better

        EXAMPLE:
        If 3×4H shows delta of +0.56%:
        - Average return at 12 hours: +0.78%
        - Average return at 24 hours: +0.22%
        - Edge of taking profits at 12h: +0.56% better

        This validates intraday profit-taking strategy!
        """
        print("\n📊 Analyzing multi-horizon outcomes (Take vs Hold)...")

        horizons = [
            ('1×4H', 'take_profit_outcome', '1x4h', 'hold_outcome', '1d'),
            ('2×4H', 'take_profit_outcome', '2x4h', 'hold_outcome', '1d'),
            ('3×4H', 'take_profit_outcome', '3x4h', 'hold_outcome', '1d'),  # PRIMARY METRIC
            ('1D', 'hold_outcome', '1d', 'hold_outcome', '2d'),
            ('2D', 'hold_outcome', '2d', 'hold_outcome', '7d'),
        ]

        outcomes = []

        for horizon_label, take_dict, take_key, hold_dict, hold_key in horizons:
            take_returns = []
            hold_returns = []

            for lc in lifecycles:
                take_dict_obj = getattr(lc, take_dict)
                hold_dict_obj = getattr(lc, hold_dict)

                take_ret = take_dict_obj.get(take_key, None)
                hold_ret = hold_dict_obj.get(hold_key, None)

                if take_ret is not None and hold_ret is not None:
                    take_returns.append(take_ret)
                    hold_returns.append(hold_ret)

            if take_returns and hold_returns:
                avg_take = np.mean(take_returns)
                avg_hold = np.mean(hold_returns)
                delta = avg_take - avg_hold

                win_rate = sum(1 for r in take_returns if r > 0) / len(take_returns) * 100

                outcome = MultiHorizonOutcome(
                    horizon_label=horizon_label,
                    take_profit_return=float(avg_take),
                    hold_return=float(avg_hold),
                    delta=float(delta),
                    sample_size=len(take_returns),
                    win_rate=float(win_rate)
                )
                outcomes.append(outcome)

                print(f"  {horizon_label:8s}: Take={avg_take:+.2f}% vs Hold={avg_hold:+.2f}% (Δ={delta:+.2f}%, n={len(take_returns)})")

        return outcomes

    def calculate_signal_quality(self, lifecycles: List[DivergenceLifecycle]) -> SignalQuality:
        """Calculate signal quality metrics."""
        if not lifecycles:
            return SignalQuality(0, 0, 0, 0, 0)

        # Use 1D returns for quality assessment
        returns = [lc.returns_daily.get(1, 0) for lc in lifecycles if 1 in lc.returns_daily]

        if not returns:
            return SignalQuality(0, 0, 0, 0, 0)

        hit_rate = sum(1 for r in returns if r > 0) / len(returns) * 100
        avg_return = np.mean(returns)
        sharpe = avg_return / (np.std(returns) + 1e-6)

        # Calculate max drawdown
        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        max_dd = np.min(drawdown) if len(drawdown) > 0 else 0

        # Consistency score (based on hit rate and Sharpe)
        consistency = min(100, (hit_rate + abs(sharpe) * 10))

        return SignalQuality(
            hit_rate=float(hit_rate),
            avg_return=float(avg_return),
            sharpe_ratio=float(sharpe),
            max_drawdown=float(max_dd),
            consistency_score=float(consistency)
        )

    def calculate_volatility_context(self) -> VolatilityContext:
        """Calculate current volatility context."""
        current_atr = float(self.daily_atr.iloc[-1])

        # Calculate ATR percentile
        atr_percentile = float(
            self.daily_atr.rank(pct=True).iloc[-1] * 100
        )

        # Determine regime
        if atr_percentile > 90:
            regime = 'extreme'
        elif atr_percentile > 70:
            regime = 'high'
        elif atr_percentile < 30:
            regime = 'low'
        else:
            regime = 'normal'

        return VolatilityContext(
            current_atr=current_atr,
            historical_atr_percentile=atr_percentile,
            volatility_regime=regime
        )

    def calculate_decay_model(self, lifecycles: List[DivergenceLifecycle]) -> DivergenceDecayModel:
        """
        Calculate divergence decay model (how fast gaps close).

        This answers: How quickly do divergences typically resolve?
        """
        print("\n📉 Calculating divergence decay model...")

        # Filter lifecycles that converged
        converged = [lc for lc in lifecycles if lc.time_to_convergence_hours is not None]

        if not converged:
            return DivergenceDecayModel(0, 0, 0, 0, {})

        # Calculate decay rates (gap reduction per 4H bar)
        decay_rates = []
        for lc in converged:
            if lc.convergence_bar and lc.convergence_bar > 0:
                initial_gap = lc.initial_gap
                bars_to_converge = lc.convergence_bar
                # Assume gap goes from initial_gap to ~0 over convergence_bar periods
                decay_rate = initial_gap / bars_to_converge
                decay_rates.append(decay_rate)

        avg_decay_rate = float(np.mean(decay_rates)) if decay_rates else 0.0
        # Ensure no NaN values
        if np.isnan(avg_decay_rate):
            avg_decay_rate = 0.0

        # Median time to convergence
        convergence_times = [lc.time_to_convergence_hours for lc in converged]
        median_time = float(np.median(convergence_times)) if convergence_times else 0.0
        if np.isnan(median_time):
            median_time = 0.0

        # Convergence probabilities
        total_lifecycles = len(lifecycles)
        converged_24h = sum(1 for lc in lifecycles
                           if lc.time_to_convergence_hours and lc.time_to_convergence_hours <= 24)
        converged_48h = sum(1 for lc in lifecycles
                           if lc.time_to_convergence_hours and lc.time_to_convergence_hours <= 48)

        prob_24h = (converged_24h / total_lifecycles * 100) if total_lifecycles > 0 else 0
        prob_48h = (converged_48h / total_lifecycles * 100) if total_lifecycles > 0 else 0

        # Convergence by gap size
        prob_by_gap = {}
        for gap_cat in ['small', 'medium', 'large']:
            cat_lcs = [lc for lc in lifecycles if lc.gap_category == gap_cat]
            if cat_lcs:
                cat_converged = sum(1 for lc in cat_lcs if lc.convergence_bar is not None)
                prob_by_gap[gap_cat] = (cat_converged / len(cat_lcs) * 100)
            else:
                prob_by_gap[gap_cat] = 0

        print(f"  Decay rate: {avg_decay_rate:.2f}% per 4H bar")
        print(f"  Median convergence time: {median_time:.1f} hours")
        print(f"  Convergence probability (24h): {prob_24h:.1f}%")
        print(f"  Convergence probability (48h): {prob_48h:.1f}%")
        print(f"  By gap size: Small={prob_by_gap['small']:.1f}%, Med={prob_by_gap['medium']:.1f}%, Large={prob_by_gap['large']:.1f}%")

        return DivergenceDecayModel(
            avg_decay_rate_per_4h=float(avg_decay_rate),
            median_time_to_convergence_hours=float(median_time),
            convergence_probability_24h=float(prob_24h),
            convergence_probability_48h=float(prob_48h),
            convergence_probability_by_gap_size=prob_by_gap
        )

    def analyze_reentry_opportunities(self, lifecycles: List[DivergenceLifecycle]) -> Dict:
        """
        Analyze re-entry opportunities across all lifecycle events.

        Returns statistics on:
        - % of events that generate re-entry signals
        - Average time to re-entry (in 4H bars)
        - Expected return from re-entry
        - Success rate of re-entries
        """
        print("\n🔄 Analyzing re-entry opportunities...")

        reentries = [lc for lc in lifecycles if lc.reentry_bar is not None]

        if not reentries:
            return {
                'reentry_rate': 0,
                'avg_time_to_reentry_hours': 0,
                'avg_expected_return': 0,
                'success_rate': 0,
                'sample_size': 0
            }

        reentry_rate = len(reentries) / len(lifecycles) * 100
        avg_time_bars = np.mean([lc.reentry_bar for lc in reentries])
        avg_time_hours = avg_time_bars * 4

        returns = [lc.reentry_return for lc in reentries if lc.reentry_return is not None]
        avg_return = np.mean(returns) if returns else 0
        success_rate = sum(1 for r in returns if r > 0) / len(returns) * 100 if returns else 0

        print(f"  Re-entry rate: {reentry_rate:.1f}% ({len(reentries)} / {len(lifecycles)} events)")
        print(f"  Avg time to re-entry: {avg_time_hours:.1f} hours ({avg_time_bars:.1f} bars)")
        print(f"  Avg expected return: {avg_return:+.2f}%")
        print(f"  Success rate: {success_rate:.1f}%")

        return {
            'reentry_rate': float(reentry_rate),
            'avg_time_to_reentry_hours': float(avg_time_hours),
            'avg_expected_return': float(avg_return),
            'success_rate': float(success_rate),
            'sample_size': len(reentries)
        }

    def generate_timeline_chart_data(self, lifecycles: List[DivergenceLifecycle], num_events: int = 50) -> List[Dict]:
        """
        Generate timeline chart data showing 4H vs Daily evolution around events.

        Shows -2 bars to +6 bars around each divergence trigger.

        Returns list of events with timeline data for charting.
        """
        print(f"\n📈 Generating timeline chart data for {num_events} events...")

        # Take most recent events
        recent_events = lifecycles[-num_events:] if len(lifecycles) > num_events else lifecycles

        timeline_data = []

        for lc in recent_events:
            # Get the trigger checkpoint
            trigger_cp = lc.trigger_checkpoint

            # Build timeline from -2 to +6 bars
            timeline = {
                'trigger_date': lc.trigger_date,
                'initial_gap': lc.initial_gap,
                'gap_category': lc.gap_category,
                'bars': []
            }

            # We only have forward data, so we'll focus on 0 to +6
            for bar_offset in range(0, 7):
                if bar_offset == 0:
                    # Trigger point
                    timeline['bars'].append({
                        'bar_offset': 0,
                        'label': 'Trigger',
                        'daily_pct': trigger_cp.daily_percentile,
                        '4h_pct': trigger_cp.hourly_4h_percentile,
                        'gap': trigger_cp.divergence_pct,
                        'price_return': 0.0
                    })
                else:
                    # Forward bars
                    if bar_offset in lc.returns_4h:
                        timeline['bars'].append({
                            'bar_offset': bar_offset,
                            'label': f'+{bar_offset}×4H',
                            'price_return': lc.returns_4h[bar_offset]
                        })

            timeline_data.append(timeline)

        print(f"  ✓ Generated {len(timeline_data)} timeline events")
        return timeline_data

    def generate_heatmap_data(self, lifecycles: List[DivergenceLifecycle]) -> Dict:
        """
        Generate Take vs Hold benefit heatmap data.

        PURPOSE:
        Shows how intraday edge varies by divergence gap size and time horizon.
        Particularly useful for understanding large gap (35%+) behavior.

        DIMENSIONS:
        - Y-axis (Rows): Gap size buckets (15-20%, 20-25%, 25-30%, 30-35%, 35%+)
        - X-axis (Columns): Time horizons (1×4H, 2×4H, 3×4H, 1D, 2D)
        - Cell Value: Delta (Take Profit return - Hold return)
        - Cell Color: Green (positive edge), Red (negative edge)

        GAP SIZE DEFINITION:
        Gap = |Daily Percentile - 4H Percentile|
        Example: Daily=75%, 4H=40% → Gap=35% (LARGE)

        LARGE GAP BEHAVIOR (35%+):
        - User specifically interested in large gaps
        - Hypothesis: Larger gaps may show different convergence patterns
        - May take longer to converge (see convergence_by_volatility metrics)
        - Heatmap shows if large gaps benefit more from early exits or holding

        CELL INTERPRETATION:
        - Positive delta (green): Taking profits at this horizon is better
        - Negative delta (red): Holding longer is better
        - Sample size (n=X): Number of historical events in this cell

        Example Reading:
        Gap 35%+, Horizon 3×4H, Delta +0.8%, n=45
        → For gaps >35%, exiting at 12 hours provides +0.8% better return
           than holding to 24 hours, based on 45 historical events
        """
        print("\n🎨 Generating Take vs Hold heatmap data...")

        # Define gap size buckets
        gap_buckets = [
            ('15-20%', 15, 20),   # Small gaps
            ('20-25%', 20, 25),   # Small-medium gaps
            ('25-30%', 25, 30),   # Medium gaps
            ('30-35%', 30, 35),   # Medium-large gaps
            ('35%+', 35, 999)     # LARGE gaps (user interest focus)
        ]

        # Define time horizons
        horizons = [
            ('1×4H', 'returns_4h', 1, 'returns_daily', 1),
            ('2×4H', 'returns_4h', 2, 'returns_daily', 1),
            ('3×4H', 'returns_4h', 3, 'returns_daily', 1),
            ('1D', 'returns_daily', 1, 'returns_daily', 2),
            ('2D', 'returns_daily', 2, 'returns_daily', 7)
        ]

        heatmap_matrix = []

        for gap_label, gap_min, gap_max in gap_buckets:
            row = {'gap_range': gap_label, 'horizons': []}

            # Filter lifecycles in this gap range
            gap_lcs = [lc for lc in lifecycles if gap_min <= lc.initial_gap < gap_max]

            for horizon_label, take_dict, take_key, hold_dict, hold_key in horizons:
                take_returns = []
                hold_returns = []

                for lc in gap_lcs:
                    take_data = getattr(lc, take_dict, {})
                    hold_data = getattr(lc, hold_dict, {})

                    if take_key in take_data and hold_key in hold_data:
                        take_returns.append(take_data[take_key])
                        hold_returns.append(hold_data[hold_key])

                if take_returns and hold_returns:
                    avg_take = np.mean(take_returns)
                    avg_hold = np.mean(hold_returns)
                    delta = avg_take - avg_hold
                    sample_size = len(take_returns)
                else:
                    avg_take = 0
                    avg_hold = 0
                    delta = 0
                    sample_size = 0

                row['horizons'].append({
                    'horizon': horizon_label,
                    'take_return': float(avg_take),
                    'hold_return': float(avg_hold),
                    'delta': float(delta),
                    'sample_size': sample_size
                })

            heatmap_matrix.append(row)

        print(f"  ✓ Generated {len(heatmap_matrix)} × {len(horizons)} heatmap matrix")
        return {
            'matrix': heatmap_matrix,
            'gap_buckets': [label for label, _, _ in gap_buckets],
            'horizons': [label for label, *_ in horizons]
        }

    def analyze_by_volatility_regime(self, lifecycles: List[DivergenceLifecycle]) -> List[VolatilityAwareMetrics]:
        """
        Analyze performance by volatility regime.

        Shows how intraday edge varies by market volatility.
        """
        print("\n🌡️  Analyzing performance by volatility regime...")

        # Get ATR at each event
        regime_lifecycles = {
            'low': [],
            'normal': [],
            'high': [],
            'extreme': []
        }

        for lc in lifecycles:
            # Get date of lifecycle event - convert string to date
            event_date_str = lc.trigger_date

            # Find matching date in daily_data
            matching_dates = [d for d in self.daily_data.index if d.strftime('%Y-%m-%d') == event_date_str]

            if not matching_dates:
                continue

            event_date = matching_dates[0]
            event_idx = self.daily_data.index.get_loc(event_date)

            if event_idx >= len(self.daily_atr):
                continue

            # Get ATR percentile at this event
            atr_value = self.daily_atr.iloc[event_idx]
            atr_percentile = self.daily_atr.iloc[:event_idx+1].rank(pct=True).iloc[-1] * 100

            # Classify regime
            if atr_percentile > 90:
                regime = 'extreme'
            elif atr_percentile > 70:
                regime = 'high'
            elif atr_percentile < 30:
                regime = 'low'
            else:
                regime = 'normal'

            regime_lifecycles[regime].append(lc)

        # Calculate metrics for each regime
        metrics = []

        for regime, lcs in regime_lifecycles.items():
            if not lcs:
                continue

            # Calculate intraday edge (3×4H)
            edges_3x4h = []
            for lc in lcs:
                if 3 in lc.returns_4h and 1 in lc.returns_daily:
                    edge = lc.returns_4h[3] - lc.returns_daily[1]
                    edges_3x4h.append(edge)

            avg_edge = np.mean(edges_3x4h) if edges_3x4h else 0

            # Find optimal exit horizon for this regime
            horizon_performance = {}
            for horizon_idx in [1, 2, 3]:
                if horizon_idx in lc.returns_4h:
                    rets = [lc.returns_4h.get(horizon_idx, 0) for lc in lcs if horizon_idx in lc.returns_4h]
                    if rets:
                        horizon_performance[f'{horizon_idx}×4H'] = np.mean(rets)

            optimal_horizon = max(horizon_performance, key=horizon_performance.get) if horizon_performance else '3×4H'

            # Hit rate
            returns_1d = [lc.returns_daily.get(1, 0) for lc in lcs if 1 in lc.returns_daily]
            hit_rate = sum(1 for r in returns_1d if r > 0) / len(returns_1d) * 100 if returns_1d else 0
            avg_return = np.mean(returns_1d) if returns_1d else 0

            # Recommendation
            if avg_edge > 0.5:
                action = 'Very aggressive - strong intraday edge'
            elif avg_edge > 0.3:
                action = 'Aggressive - take profits early'
            elif avg_edge > 0:
                action = 'Moderate - slight intraday edge'
            else:
                action = 'Conservative - hold longer'

            metric = VolatilityAwareMetrics(
                regime=regime,
                sample_size=len(lcs),
                avg_intraday_edge=float(avg_edge),
                optimal_exit_horizon=optimal_horizon,
                hit_rate=float(hit_rate),
                avg_return=float(avg_return),
                recommended_action=action
            )
            metrics.append(metric)

            print(f"  {regime.upper():8s}: n={len(lcs):3d} | Edge={avg_edge:+.2f}% | Best={optimal_horizon} | {action}")

        return metrics

    def calculate_convergence_by_volatility(self, lifecycles: List[DivergenceLifecycle]) -> Dict:
        """
        Calculate convergence probability by volatility regime.

        Tests if high volatility leads to faster convergence.
        """
        print("\n📉 Analyzing convergence by volatility regime...")

        regime_convergence = {
            'low': {'converged': 0, 'total': 0, 'avg_time': []},
            'normal': {'converged': 0, 'total': 0, 'avg_time': []},
            'high': {'converged': 0, 'total': 0, 'avg_time': []},
            'extreme': {'converged': 0, 'total': 0, 'avg_time': []}
        }

        for lc in lifecycles:
            event_date_str = lc.trigger_date

            # Find matching date in daily_data
            matching_dates = [d for d in self.daily_data.index if d.strftime('%Y-%m-%d') == event_date_str]

            if not matching_dates:
                continue

            event_date = matching_dates[0]
            event_idx = self.daily_data.index.get_loc(event_date)

            if event_idx >= len(self.daily_atr):
                continue

            # Get ATR percentile
            atr_percentile = self.daily_atr.iloc[:event_idx+1].rank(pct=True).iloc[-1] * 100

            # Classify regime
            if atr_percentile > 90:
                regime = 'extreme'
            elif atr_percentile > 70:
                regime = 'high'
            elif atr_percentile < 30:
                regime = 'low'
            else:
                regime = 'normal'

            regime_convergence[regime]['total'] += 1

            if lc.convergence_bar is not None:
                regime_convergence[regime]['converged'] += 1
                if lc.time_to_convergence_hours:
                    regime_convergence[regime]['avg_time'].append(lc.time_to_convergence_hours)

        # Calculate stats
        results = {}
        for regime, data in regime_convergence.items():
            if data['total'] > 0:
                conv_rate = (data['converged'] / data['total']) * 100
                avg_time = np.mean(data['avg_time']) if data['avg_time'] else 0

                results[regime] = {
                    'convergence_rate': float(conv_rate),
                    'avg_convergence_time_hours': float(avg_time),
                    'sample_size': data['total']
                }

                print(f"  {regime.upper():8s}: {conv_rate:.1f}% converge (avg {avg_time:.1f}h) | n={data['total']}")
            else:
                results[regime] = {
                    'convergence_rate': 0.0,
                    'avg_convergence_time_hours': 0.0,
                    'sample_size': 0
                }

        return results

    def analyze_regime_filtered_gaps(self, lifecycles: List[DivergenceLifecycle]) -> List[RegimeFilteredGapAnalysis]:
        """
        Analyze specific gap sizes in specific volatility regimes.

        This is the KEY analysis for finding tradeable setups.
        Shows ABSOLUTE returns (not just deltas) by gap size and regime.
        """
        print("\n🎯 Analyzing regime-filtered gap performance...")

        gap_buckets = [
            ('15-20%', 15, 20),
            ('20-25%', 20, 25),
            ('25-30%', 25, 30),
            ('30-35%', 30, 35),
            ('35%+', 35, 999)
        ]

        regimes = ['low', 'normal', 'high', 'extreme']

        results = []

        for gap_label, gap_min, gap_max in gap_buckets:
            for regime in regimes:
                # Filter lifecycles by gap size and regime
                filtered_lcs = []
                for lc in lifecycles:
                    if not (gap_min <= lc.initial_gap < gap_max):
                        continue

                    # Get regime for this event
                    event_date_str = lc.trigger_date
                    matching_dates = [d for d in self.daily_data.index if d.strftime('%Y-%m-%d') == event_date_str]
                    if not matching_dates:
                        continue

                    event_date = matching_dates[0]
                    event_idx = self.daily_data.index.get_loc(event_date)
                    if event_idx >= len(self.daily_atr):
                        continue

                    atr_percentile = self.daily_atr.iloc[:event_idx+1].rank(pct=True).iloc[-1] * 100

                    if atr_percentile > 90:
                        lc_regime = 'extreme'
                    elif atr_percentile > 70:
                        lc_regime = 'high'
                    elif atr_percentile < 30:
                        lc_regime = 'low'
                    else:
                        lc_regime = 'normal'

                    if lc_regime == regime:
                        filtered_lcs.append(lc)

                if len(filtered_lcs) < 5:  # Skip if too few samples
                    continue

                # Calculate absolute returns for each horizon
                horizons = {
                    '1x4h': 1,
                    '2x4h': 2,
                    '3x4h': 3,
                    '1d': 1,
                    '2d': 2
                }

                returns_1x4h = [lc.returns_4h.get(1, 0) for lc in filtered_lcs if 1 in lc.returns_4h]
                returns_2x4h = [lc.returns_4h.get(2, 0) for lc in filtered_lcs if 2 in lc.returns_4h]
                returns_3x4h = [lc.returns_4h.get(3, 0) for lc in filtered_lcs if 3 in lc.returns_4h]
                returns_1d = [lc.returns_daily.get(1, 0) for lc in filtered_lcs if 1 in lc.returns_daily]
                returns_2d = [lc.returns_daily.get(2, 0) for lc in filtered_lcs if 2 in lc.returns_daily]

                avg_return_1x4h = np.mean(returns_1x4h) if returns_1x4h else 0
                avg_return_2x4h = np.mean(returns_2x4h) if returns_2x4h else 0
                avg_return_3x4h = np.mean(returns_3x4h) if returns_3x4h else 0
                avg_return_1d = np.mean(returns_1d) if returns_1d else 0
                avg_return_2d = np.mean(returns_2d) if returns_2d else 0

                win_rate_1x4h = (sum(1 for r in returns_1x4h if r > 0) / len(returns_1x4h) * 100) if returns_1x4h else 0
                win_rate_2x4h = (sum(1 for r in returns_2x4h if r > 0) / len(returns_2x4h) * 100) if returns_2x4h else 0
                win_rate_3x4h = (sum(1 for r in returns_3x4h if r > 0) / len(returns_3x4h) * 100) if returns_3x4h else 0
                win_rate_1d = (sum(1 for r in returns_1d if r > 0) / len(returns_1d) * 100) if returns_1d else 0
                win_rate_2d = (sum(1 for r in returns_2d if r > 0) / len(returns_2d) * 100) if returns_2d else 0

                # Find best horizon
                horizon_performance = {
                    '1×4H': avg_return_1x4h,
                    '2×4H': avg_return_2x4h,
                    '3×4H': avg_return_3x4h,
                    '1D': avg_return_1d,
                    '2D': avg_return_2d
                }
                best_horizon = max(horizon_performance, key=horizon_performance.get)
                best_avg_return = horizon_performance[best_horizon]

                horizon_win_rates = {
                    '1×4H': win_rate_1x4h,
                    '2×4H': win_rate_2x4h,
                    '3×4H': win_rate_3x4h,
                    '1D': win_rate_1d,
                    '2D': win_rate_2d
                }
                best_win_rate = horizon_win_rates[best_horizon]

                # Calculate expectancy for 2×4H (primary focus)
                wins_2x4h = [r for r in returns_2x4h if r > 0]
                losses_2x4h = [r for r in returns_2x4h if r <= 0]

                avg_win_size = np.mean(wins_2x4h) if wins_2x4h else 0
                avg_loss_size = abs(np.mean(losses_2x4h)) if losses_2x4h else 0
                win_loss_ratio = avg_win_size / avg_loss_size if avg_loss_size > 0 else 0

                expectancy_2x4h = (win_rate_2x4h / 100 * avg_win_size) - ((100 - win_rate_2x4h) / 100 * avg_loss_size)

                analysis = RegimeFilteredGapAnalysis(
                    gap_range=gap_label,
                    regime=regime,
                    sample_size=len(filtered_lcs),
                    avg_return_1x4h=float(avg_return_1x4h),
                    avg_return_2x4h=float(avg_return_2x4h),
                    avg_return_3x4h=float(avg_return_3x4h),
                    avg_return_1d=float(avg_return_1d),
                    avg_return_2d=float(avg_return_2d),
                    win_rate_1x4h=float(win_rate_1x4h),
                    win_rate_2x4h=float(win_rate_2x4h),
                    win_rate_3x4h=float(win_rate_3x4h),
                    win_rate_1d=float(win_rate_1d),
                    win_rate_2d=float(win_rate_2d),
                    best_horizon=best_horizon,
                    best_avg_return=float(best_avg_return),
                    best_win_rate=float(best_win_rate),
                    expectancy_2x4h=float(expectancy_2x4h),
                    avg_win_size=float(avg_win_size),
                    avg_loss_size=float(avg_loss_size),
                    win_loss_ratio=float(win_loss_ratio)
                )

                results.append(analysis)

                if expectancy_2x4h > 0.2:  # Significant positive expectancy
                    print(f"  ⭐ {gap_label} in {regime.upper()}: "
                          f"2×4HReturn={avg_return_2x4h:+.2f}%, "
                          f"WinRate={win_rate_2x4h:.1f}%, "
                          f"Expectancy={expectancy_2x4h:+.2f}%, "
                          f"n={len(filtered_lcs)}")

        return results

    def analyze_reentry_by_gap_and_regime(self, lifecycles: List[DivergenceLifecycle]) -> List[ReentryBreakdown]:
        """
        Break down re-entry performance by gap size and volatility regime.
        """
        print("\n🔄 Analyzing re-entry performance by gap & regime...")

        gap_categories = ['small', 'medium', 'large']
        regimes = ['low', 'normal', 'high', 'extreme']

        results = []

        for gap_cat in gap_categories:
            for regime in regimes:
                # Filter lifecycles
                filtered_lcs = []
                for lc in lifecycles:
                    if lc.gap_category != gap_cat:
                        continue

                    # Get regime
                    event_date_str = lc.trigger_date
                    matching_dates = [d for d in self.daily_data.index if d.strftime('%Y-%m-%d') == event_date_str]
                    if not matching_dates:
                        continue

                    event_date = matching_dates[0]
                    event_idx = self.daily_data.index.get_loc(event_date)
                    if event_idx >= len(self.daily_atr):
                        continue

                    atr_percentile = self.daily_atr.iloc[:event_idx+1].rank(pct=True).iloc[-1] * 100

                    if atr_percentile > 90:
                        lc_regime = 'extreme'
                    elif atr_percentile > 70:
                        lc_regime = 'high'
                    elif atr_percentile < 30:
                        lc_regime = 'low'
                    else:
                        lc_regime = 'normal'

                    if lc_regime == regime:
                        filtered_lcs.append(lc)

                if len(filtered_lcs) < 5:
                    continue

                # Calculate re-entry metrics
                reentries = [lc for lc in filtered_lcs if lc.reentry_bar is not None]

                if not reentries:
                    continue

                reentry_rate = len(reentries) / len(filtered_lcs) * 100
                avg_time_to_reentry = np.mean([lc.reentry_bar * 4 for lc in reentries])  # Convert bars to hours

                reentry_returns = [lc.reentry_return for lc in reentries if lc.reentry_return is not None]
                avg_reentry_return = np.mean(reentry_returns) if reentry_returns else 0
                reentry_success_rate = (sum(1 for r in reentry_returns if r > 0) / len(reentry_returns) * 100) if reentry_returns else 0

                # Calculate expectancy
                wins = [r for r in reentry_returns if r > 0]
                losses = [r for r in reentry_returns if r <= 0]

                avg_win = np.mean(wins) if wins else 0
                avg_loss = abs(np.mean(losses)) if losses else 0

                reentry_expectancy = (reentry_success_rate / 100 * avg_win) - ((100 - reentry_success_rate) / 100 * avg_loss)

                breakdown = ReentryBreakdown(
                    gap_category=gap_cat,
                    regime=regime,
                    sample_size=len(filtered_lcs),
                    reentry_rate=float(reentry_rate),
                    avg_time_to_reentry=float(avg_time_to_reentry),
                    avg_reentry_return=float(avg_reentry_return),
                    reentry_success_rate=float(reentry_success_rate),
                    reentry_expectancy=float(reentry_expectancy)
                )

                results.append(breakdown)

                if reentry_expectancy > 0.2:
                    print(f"  ⭐ {gap_cat.upper()} in {regime.upper()}: "
                          f"ReentryRate={reentry_rate:.1f}%, "
                          f"Return={avg_reentry_return:+.2f}%, "
                          f"Expectancy={reentry_expectancy:+.2f}%, "
                          f"n={len(filtered_lcs)}")

        return results

    def generate_trade_recommendations(self,
                                      regime_analyses: List[RegimeFilteredGapAnalysis],
                                      reentry_analyses: List[ReentryBreakdown],
                                      current_regime: str) -> List[TradeRecommendation]:
        """
        Generate actionable trade recommendations based on comprehensive analysis.
        """
        print("\n📋 Generating trade recommendations...")

        recommendations = []

        # Criteria for tradeable setup
        MIN_EXPECTANCY = 0.15  # 0.15% per trade minimum
        MIN_WIN_RATE = 52.0  # 52% minimum
        MIN_SAMPLE_SIZE = 20  # At least 20 historical events
        HIGH_CONFIDENCE_SAMPLE = 50  # 50+ for high confidence

        for analysis in regime_analyses:
            # Check if this setup meets criteria
            is_tradeable = (
                analysis.expectancy_2x4h >= MIN_EXPECTANCY and
                analysis.win_rate_2x4h >= MIN_WIN_RATE and
                analysis.sample_size >= MIN_SAMPLE_SIZE and
                analysis.avg_return_2x4h > 0  # Must be profitable in absolute terms
            )

            # Determine confidence
            if analysis.sample_size >= HIGH_CONFIDENCE_SAMPLE and analysis.expectancy_2x4h >= 0.3:
                confidence = 'high'
            elif analysis.sample_size >= MIN_SAMPLE_SIZE and analysis.expectancy_2x4h >= 0.2:
                confidence = 'medium'
            else:
                confidence = 'low'

            # Calculate max consecutive losses (rough estimate)
            # Clamp win rate to prevent log(0) or log(1) errors
            clamped_win_rate = max(1.0, min(99.0, analysis.win_rate_2x4h))
            if clamped_win_rate >= 99.0:
                max_consec_losses = 1  # Nearly guaranteed wins
            elif clamped_win_rate <= 1.0:
                max_consec_losses = 50  # Cap at reasonable maximum for very low win rates
            else:
                max_consec_losses = int(np.ceil(-np.log(0.01) / np.log(1 - clamped_win_rate / 100)))

            # Position sizing (Kelly Criterion simplified)
            edge = analysis.expectancy_2x4h / 100
            kelly_fraction = edge / (analysis.avg_loss_size / 100) if analysis.avg_loss_size > 0 else 0
            recommended_position = min(kelly_fraction * 0.5, 0.10) * 100  # Half Kelly, max 10%

            # Build reasoning
            if is_tradeable:
                reason = (f"Positive expectancy (+{analysis.expectancy_2x4h:.2f}%), "
                         f"good win rate ({analysis.win_rate_2x4h:.1f}%), "
                         f"and profitable absolute return (+{analysis.avg_return_2x4h:.2f}%)")
            else:
                reason = "Does not meet minimum criteria for trading"

            # Identify risks
            risks = []
            if analysis.sample_size < HIGH_CONFIDENCE_SAMPLE:
                risks.append(f"Small sample size (n={analysis.sample_size}, prefer 50+)")
            if analysis.win_rate_2x4h < 55:
                risks.append(f"Win rate below 55% ({analysis.win_rate_2x4h:.1f}%)")
            if analysis.avg_return_2x4h < 0.3:
                risks.append(f"Low absolute return ({analysis.avg_return_2x4h:.2f}%)")
            if analysis.regime != current_regime:
                risks.append(f"Setup is for {analysis.regime.upper()} vol, current is {current_regime.upper()}")

            rec = TradeRecommendation(
                setup_name=f"{analysis.gap_range} Gap in {analysis.regime.upper()} Volatility",
                trade_signal=is_tradeable,
                confidence=confidence,
                gap_range=analysis.gap_range,
                regime_filter=analysis.regime,
                recommended_exit='2×4H',
                expected_return=analysis.avg_return_2x4h,
                win_rate=analysis.win_rate_2x4h,
                expectancy=analysis.expectancy_2x4h,
                sample_size=analysis.sample_size,
                max_consecutive_losses=max_consec_losses,
                recommended_position_size=recommended_position,
                reason_tradeable=reason,
                risks=risks
            )

            recommendations.append(rec)

            if is_tradeable and confidence in ['high', 'medium']:
                print(f"  ✅ TRADEABLE: {rec.setup_name}")
                print(f"     Exit: {rec.recommended_exit}, Return: {rec.expected_return:+.2f}%, "
                      f"WinRate: {rec.win_rate:.1f}%, Expectancy: {rec.expectancy:+.2f}%")
                print(f"     Confidence: {confidence.upper()}, Position Size: {rec.recommended_position_size:.1f}%")

        return recommendations


def _scrub_nans(obj):
    """Recursively replace NaN and Inf values with 0 or None for JSON compliance."""
    import math

    if isinstance(obj, dict):
        return {k: _scrub_nans(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_scrub_nans(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
        return obj
    else:
        return obj


def run_enhanced_analysis(ticker: str) -> Dict:
    """Run complete enhanced multi-timeframe analysis."""
    analyzer = EnhancedMultiTimeframeAnalyzer(ticker)

    # Run lifecycle backtest
    lifecycles = analyzer.backtest_with_lifecycle_tracking(min_divergence_pct=15.0)

    # Analyze outcomes
    multi_horizon_outcomes = analyzer.analyze_multi_horizon_outcomes(lifecycles)

    # Calculate quality metrics
    signal_quality = analyzer.calculate_signal_quality(lifecycles)
    volatility_context = analyzer.calculate_volatility_context()
    decay_model = analyzer.calculate_decay_model(lifecycles)
    reentry_analysis = analyzer.analyze_reentry_opportunities(lifecycles)

    # NEW: Volatility-aware analysis
    volatility_metrics = analyzer.analyze_by_volatility_regime(lifecycles)
    convergence_by_volatility = analyzer.calculate_convergence_by_volatility(lifecycles)

    # NEW: Advanced regime-filtered analysis
    regime_filtered_gaps = analyzer.analyze_regime_filtered_gaps(lifecycles)
    reentry_breakdown = analyzer.analyze_reentry_by_gap_and_regime(lifecycles)
    trade_recommendations = analyzer.generate_trade_recommendations(
        regime_filtered_gaps,
        reentry_breakdown,
        volatility_context.volatility_regime
    )

    # Generate visualization data
    timeline_data = analyzer.generate_timeline_chart_data(lifecycles, num_events=50)
    heatmap_data = analyzer.generate_heatmap_data(lifecycles)

    result = {
        'ticker': ticker,
        'analysis_date': datetime.now().isoformat(),
        'lifecycles': [asdict(lc) for lc in lifecycles[-100:]],  # Return last 100 for performance
        'multi_horizon_outcomes': [asdict(o) for o in multi_horizon_outcomes],
        'signal_quality': asdict(signal_quality),
        'volatility_context': asdict(volatility_context),
        'decay_model': asdict(decay_model),
        'reentry_analysis': reentry_analysis,
        'volatility_aware_metrics': [asdict(m) for m in volatility_metrics],
        'convergence_by_volatility': convergence_by_volatility,
        'timeline_chart_data': timeline_data,
        'heatmap_data': heatmap_data,
        # NEW: Advanced analysis
        'regime_filtered_gaps': [asdict(r) for r in regime_filtered_gaps],
        'reentry_breakdown': [asdict(r) for r in reentry_breakdown],
        'trade_recommendations': [asdict(r) for r in trade_recommendations],
    }

    # Scrub any NaN or Inf values for JSON compliance
    result = _scrub_nans(result)

    return result


if __name__ == '__main__':
    # Test run
    result = run_enhanced_analysis('AAPL')

    print("\n" + "="*80)
    print("ENHANCED MULTI-TIMEFRAME ANALYSIS COMPLETE")
    print("="*80)
    print(f"\nSignal Quality:")
    print(f"  Hit Rate: {result['signal_quality']['hit_rate']:.1f}%")
    print(f"  Avg Return: {result['signal_quality']['avg_return']:+.2f}%")
    print(f"  Sharpe: {result['signal_quality']['sharpe_ratio']:.2f}")
    print(f"  Consistency: {result['signal_quality']['consistency_score']:.0f}/100")

    print(f"\nVolatility Context:")
    print(f"  Current ATR: ${result['volatility_context']['current_atr']:.2f}")
    print(f"  ATR Percentile: {result['volatility_context']['historical_atr_percentile']:.1f}%")
    print(f"  Regime: {result['volatility_context']['volatility_regime'].upper()}")

    print(f"\nDecay Model:")
    print(f"  Avg Decay: {result['decay_model']['avg_decay_rate_per_4h']:.2f}% per 4H bar")
    print(f"  Median Convergence: {result['decay_model']['median_time_to_convergence_hours']:.1f} hours")
    print(f"  24H Convergence Prob: {result['decay_model']['convergence_probability_24h']:.1f}%")
    print(f"  48H Convergence Prob: {result['decay_model']['convergence_probability_48h']:.1f}%")

    print(f"\nRe-entry Analysis (RELAXED THRESHOLDS - gap<15%, both<35%):")
    print(f"  Re-entry Rate: {result['reentry_analysis']['reentry_rate']:.1f}%")
    print(f"  Avg Time to Re-entry: {result['reentry_analysis']['avg_time_to_reentry_hours']:.1f} hours")
    print(f"  Expected Return: {result['reentry_analysis']['avg_expected_return']:+.2f}%")
    print(f"  Success Rate: {result['reentry_analysis']['success_rate']:.1f}%")

    print(f"\n🌡️  Volatility-Aware Recommendations:")
    for metric in result['volatility_aware_metrics']:
        print(f"  {metric['regime'].upper():8s}: {metric['recommended_action']}")
        print(f"           Edge={metric['avg_intraday_edge']:+.2f}% | Best Exit={metric['optimal_exit_horizon']}")

    print(f"\n📉 Convergence by Volatility Regime:")
    for regime, data in result['convergence_by_volatility'].items():
        print(f"  {regime.upper():8s}: {data['convergence_rate']:.1f}% converge in {data['avg_convergence_time_hours']:.1f}h (n={data['sample_size']})")
