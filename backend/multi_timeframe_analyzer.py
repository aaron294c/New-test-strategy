#!/usr/bin/env python3
"""
Multi-Timeframe Divergence Analyzer

Analyzes divergence/convergence between daily and 4-hourly RSI-MA
to identify:
1. Overextension signals (divergence = reversal opportunity)
2. Pullback reentry points (convergence after divergence)
3. Profit-taking zones (divergence at extremes)

Uses mean reversion principles to quantify edge.
"""

import numpy as np
import pandas as pd
import yfinance as yf
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


@dataclass
class DivergenceEvent:
    """Multi-timeframe divergence event."""
    date: str
    daily_percentile: float
    hourly_4h_percentile: float
    divergence_pct: float  # Percentage difference
    divergence_type: str  # 'bullish_divergence', 'bearish_divergence', 'convergence'
    signal_strength: str  # 'weak', 'moderate', 'strong', 'extreme'
    daily_price: float
    forward_returns: Dict[str, float]  # Returns at D1, D3, D5, D7, D14, D21


@dataclass
class MultiTimeframeAnalysis:
    """Complete multi-timeframe analysis results."""
    ticker: str
    analysis_date: str

    # Current state
    current_daily_percentile: float
    current_4h_percentile: float
    current_divergence_pct: float
    current_signal: str

    # Historical patterns
    divergence_events: List[DivergenceEvent]

    # Statistics by divergence type
    divergence_stats: Dict[str, Dict]

    # Optimal thresholds
    optimal_thresholds: Dict[str, float]

    # Actionable signals
    current_recommendation: Dict[str, any]


class MultiTimeframeAnalyzer:
    """
    Analyze divergence/convergence between daily and 4-hourly RSI-MA.

    Key concepts:
    - Divergence: Daily and 4H percentiles differ significantly
      - Bearish divergence: Daily >> 4H (overextended, potential reversal)
      - Bullish divergence: 4H >> Daily (pullback complete, reentry)
    - Convergence: Daily and 4H align (confirming trend)
    """

    def __init__(self,
                 ticker: str,
                 lookback_days: int = 500,
                 rsi_length: int = 14,
                 ma_length: int = 14):
        """
        Initialize analyzer.

        Args:
            ticker: Stock ticker
            lookback_days: Historical data period
            rsi_length: RSI calculation period
            ma_length: MA calculation period
        """
        self.ticker = ticker.upper()
        self.lookback_days = lookback_days
        self.rsi_length = rsi_length
        self.ma_length = ma_length

        # Fetch multi-timeframe data
        self.daily_data = self._fetch_data(interval='1d', period=f'{lookback_days}d')
        self.hourly_4h_data = self._fetch_data(interval='1h', period='730d')  # ~2 years of hourly

        # Calculate RSI-MA for both timeframes
        self.daily_rsi_ma = self._calculate_rsi_ma(self.daily_data)
        self.hourly_4h_rsi_ma = self._calculate_rsi_ma_from_hourly(self.hourly_4h_data)

        # Calculate percentile ranks
        self.daily_percentiles = self._calculate_percentile_ranks(self.daily_rsi_ma)
        self.hourly_4h_percentiles = self._calculate_percentile_ranks(self.hourly_4h_rsi_ma)

    def _fetch_data(self, interval: str, period: str) -> pd.DataFrame:
        """Fetch OHLCV data."""
        ticker_obj = yf.Ticker(self.ticker)
        data = ticker_obj.history(interval=interval, period=period)

        if data.empty:
            raise ValueError(f"Could not fetch {interval} data for {self.ticker}")

        print(f"Successfully fetched {len(data)} {interval} data points for {self.ticker}")
        return data

    def _calculate_rsi_ma(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate RSI-MA indicator matching TradingView implementation.

        Pipeline (MUST match enhanced_backtester.py):
        1. Calculate log returns from Close price
        2. Calculate change of returns (diff)
        3. Apply RSI (14-period) using Wilder's method
        4. Apply EMA (14-period) to RSI

        Settings:
        - Source: Change of log returns (second derivative of price)
        - RSI Length: 14
        - MA Type: EMA
        - MA Length: 14
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
        Calculate 4H RSI-MA by resampling hourly data to 4H bars.
        Then forward-fill to daily to handle weekends/gaps.
        """
        # Resample to 4H bars
        data_4h = hourly_data.resample('4h').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()

        # Calculate RSI-MA on 4H data (same method as daily)
        rsi_ma_4h = self._calculate_rsi_ma(data_4h)

        # Resample to daily frequency
        # Use 'last' to get the last 4H value of each day
        # Then forward-fill to handle weekends/holidays
        rsi_ma_daily_aligned = rsi_ma_4h.resample('1D').last().ffill()

        return rsi_ma_daily_aligned

    def _calculate_percentile_ranks(self, indicator: pd.Series,
                                   window: int = 252) -> pd.Series:
        """Calculate rolling percentile ranks."""
        percentile_ranks = indicator.rolling(window=window).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100,
            raw=False
        )
        return percentile_ranks

    def calculate_divergence_series(self) -> pd.DataFrame:
        """
        Calculate divergence series between daily and 4H percentiles.

        Returns:
            DataFrame with daily_pct, 4h_pct, divergence_pct, signal_type
        """
        # Align the two timeframes (both indexed by date)
        df = pd.DataFrame({
            'daily_pct': self.daily_percentiles,
            '4h_pct': self.hourly_4h_percentiles
        }).dropna()

        # Calculate divergence percentage
        # Positive = Daily > 4H
        # Negative = 4H > Daily
        df['divergence_pct'] = df['daily_pct'] - df['4h_pct']

        # Classify divergence type MORE SPECIFICALLY
        df['signal_type'] = 'convergence'  # Default
        df['divergence_category'] = 'none'

        # TYPE A: Daily oversold (low) but 4H overbought (high)
        # Example: Daily 25%, 4H 75% = divergence_pct = -50%
        # Interpretation: 4H got ahead of daily, likely to pull back
        # This is "4H overextension" - take profits on 4H spike
        mask_4h_overextended = (df['divergence_pct'] < -15) & (df['daily_pct'] < 50)
        df.loc[mask_4h_overextended, 'divergence_category'] = '4h_overextended'
        df.loc[(df['divergence_pct'] < -15) & (df['daily_pct'] < 50), 'signal_type'] = '4h_overextended_weak'
        df.loc[(df['divergence_pct'] < -25) & (df['daily_pct'] < 50), 'signal_type'] = '4h_overextended_moderate'
        df.loc[(df['divergence_pct'] < -35) & (df['daily_pct'] < 50), 'signal_type'] = '4h_overextended_strong'

        # TYPE B: Daily oversold (low) and 4H also oversold (aligned low)
        # Example: Daily 25%, 4H 30% = divergence_pct = -5%
        # Interpretation: Both oversold, aligned for bounce
        # This is "bullish convergence" - reentry point
        mask_bullish_convergence = (df['divergence_pct'].abs() < 15) & (df['daily_pct'] < 30)
        df.loc[mask_bullish_convergence, 'divergence_category'] = 'bullish_convergence'
        df.loc[mask_bullish_convergence, 'signal_type'] = 'bullish_convergence'

        # TYPE C: Daily overbought (high) but 4H lagging (lower)
        # Example: Daily 75%, 4H 40% = divergence_pct = +35%
        # Interpretation: Daily overextended, 4H showing weakness
        # This is "daily overextension" - reversal likely
        mask_daily_overextended = (df['divergence_pct'] > 15) & (df['daily_pct'] > 50)
        df.loc[mask_daily_overextended, 'divergence_category'] = 'daily_overextended'
        df.loc[(df['divergence_pct'] > 15) & (df['daily_pct'] > 50), 'signal_type'] = 'daily_overextended_weak'
        df.loc[(df['divergence_pct'] > 25) & (df['daily_pct'] > 50), 'signal_type'] = 'daily_overextended_moderate'
        df.loc[(df['divergence_pct'] > 35) & (df['daily_pct'] > 50), 'signal_type'] = 'daily_overextended_strong'

        # TYPE D: Daily overbought (high) and 4H also overbought (aligned high)
        # Example: Daily 75%, 4H 70% = divergence_pct = +5%
        # Interpretation: Both overbought, aligned for reversal
        # This is "bearish convergence" - exit point
        mask_bearish_convergence = (df['divergence_pct'].abs() < 15) & (df['daily_pct'] > 70)
        df.loc[mask_bearish_convergence, 'divergence_category'] = 'bearish_convergence'
        df.loc[mask_bearish_convergence, 'signal_type'] = 'bearish_convergence'

        # Add price data
        df['price'] = self.daily_data['Close']

        return df

    def backtest_divergence_signals(self,
                                   min_divergence_pct: float = 10.0,
                                   forward_days: List[int] = [1, 3, 5, 7, 14, 21]) -> List[DivergenceEvent]:
        """
        Backtest divergence signals to measure forward returns.

        Now captures ALL significant divergence events and categorizes them
        into the 4 NEW categories for proper backtesting.

        Args:
            min_divergence_pct: Minimum absolute divergence (lowered to 10 to capture more events)
            forward_days: Days to measure forward returns

        Returns:
            List of DivergenceEvent with forward returns and category assignment
        """
        div_series = self.calculate_divergence_series()
        events = []

        for i in range(len(div_series) - max(forward_days)):
            row = div_series.iloc[i]

            # Get the category from the divergence series
            category = row['divergence_category']

            # Only include events that fall into one of the 4 categories
            # (skip 'none' category)
            if category == 'none':
                continue

            abs_div = abs(row['divergence_pct'])

            # Determine divergence type and strength using NEW logic
            if category == '4h_overextended':
                div_type = '4h_overextended'
                if abs_div > 35:
                    strength = 'strong'
                elif abs_div > 25:
                    strength = 'moderate'
                else:
                    strength = 'weak'
            elif category == 'bullish_convergence':
                div_type = 'bullish_convergence'
                strength = 'convergence'
            elif category == 'daily_overextended':
                div_type = 'daily_overextended'
                if abs_div > 35:
                    strength = 'strong'
                elif abs_div > 25:
                    strength = 'moderate'
                else:
                    strength = 'weak'
            elif category == 'bearish_convergence':
                div_type = 'bearish_convergence'
                strength = 'convergence'
            else:
                # Skip events without clear category
                continue

            # Calculate forward returns
            entry_price = row['price']
            forward_returns = {}

            for days in forward_days:
                if i + days < len(div_series):
                    future_price = div_series.iloc[i + days]['price']
                    ret = (future_price / entry_price - 1) * 100
                    forward_returns[f'D{days}'] = float(ret)

            # Create event
            event = DivergenceEvent(
                date=div_series.index[i].strftime('%Y-%m-%d'),
                daily_percentile=float(row['daily_pct']),
                hourly_4h_percentile=float(row['4h_pct']),
                divergence_pct=float(row['divergence_pct']),
                divergence_type=div_type,  # Now uses NEW category
                signal_strength=strength,
                daily_price=float(entry_price),
                forward_returns=forward_returns
            )

            events.append(event)

        return events

    def analyze_divergence_patterns(self, events: List[DivergenceEvent]) -> Dict:
        """
        Analyze patterns in divergence events using the 4 NEW categories.

        Events are already categorized by backtest_divergence_signals(),
        so we just need to group them and calculate statistics.
        """
        stats = {}

        # Group by the NEW categories (events are already categorized)
        for category in ['4h_overextended', 'bullish_convergence', 'daily_overextended', 'bearish_convergence']:
            cat_events = [e for e in events if e.divergence_type == category]

            if cat_events:
                # Determine expectation based on category
                if category == '4h_overextended':
                    expectation = 'negative_returns'  # 4H pulls back toward daily
                elif category == 'bullish_convergence':
                    expectation = 'positive_returns'  # Both low, bounce
                elif category == 'daily_overextended':
                    expectation = 'negative_returns'  # Daily reverses
                elif category == 'bearish_convergence':
                    expectation = 'negative_returns'  # Both high, reversal
                else:
                    expectation = 'any'

                stats[category] = self._calculate_event_statistics(
                    cat_events,
                    expectation=expectation
                )

        return stats

    def _calculate_event_statistics(self, events: List[DivergenceEvent],
                                    expectation: str) -> Dict:
        """Calculate statistics for a group of events."""
        if not events:
            return {}

        stats = {
            'count': len(events),
            'avg_divergence_pct': np.mean([e.divergence_pct for e in events]),
            'avg_daily_percentile': np.mean([e.daily_percentile for e in events]),
            'avg_4h_percentile': np.mean([e.hourly_4h_percentile for e in events])
        }

        # Calculate average forward returns
        forward_return_keys = list(events[0].forward_returns.keys())
        for key in forward_return_keys:
            returns = [e.forward_returns[key] for e in events if key in e.forward_returns]
            if returns:
                stats[f'avg_return_{key}'] = np.mean(returns)
                stats[f'median_return_{key}'] = np.median(returns)
                stats[f'win_rate_{key}'] = sum(1 for r in returns if r > 0) / len(returns) * 100
                stats[f'max_return_{key}'] = max(returns)
                stats[f'min_return_{key}'] = min(returns)

                # Mean reversion effectiveness
                if expectation == 'negative_returns':
                    # For bearish divergence, we expect negative returns (mean reversion down)
                    stats[f'mean_reversion_rate_{key}'] = sum(1 for r in returns if r < 0) / len(returns) * 100
                elif expectation == 'positive_returns':
                    # For bullish divergence, we expect positive returns (bounce)
                    stats[f'mean_reversion_rate_{key}'] = sum(1 for r in returns if r > 0) / len(returns) * 100

        return stats

    def find_optimal_thresholds(self, events: List[DivergenceEvent]) -> Dict[str, float]:
        """
        Find optimal divergence thresholds that maximize edge.

        Tests various thresholds and finds which produces best risk-adjusted returns.
        """
        thresholds_to_test = [10, 15, 20, 25, 30, 35, 40, 45, 50]

        best_bearish_threshold = None
        best_bearish_sharpe = -999

        best_bullish_threshold = None
        best_bullish_sharpe = -999

        for threshold in thresholds_to_test:
            # Test bearish divergence threshold
            bearish_filtered = [e for e in events
                              if e.divergence_type == 'bearish_divergence'
                              and abs(e.divergence_pct) >= threshold]

            if len(bearish_filtered) >= 20:  # Need enough samples
                returns_d7 = [e.forward_returns.get('D7', 0) for e in bearish_filtered]
                # For bearish, we want negative returns (so negate them for Sharpe)
                neg_returns = [-r for r in returns_d7]
                sharpe = np.mean(neg_returns) / (np.std(neg_returns) + 1e-6)

                if sharpe > best_bearish_sharpe:
                    best_bearish_sharpe = sharpe
                    best_bearish_threshold = threshold

            # Test bullish divergence threshold
            bullish_filtered = [e for e in events
                              if e.divergence_type == 'bullish_divergence'
                              and abs(e.divergence_pct) >= threshold]

            if len(bullish_filtered) >= 20:
                returns_d7 = [e.forward_returns.get('D7', 0) for e in bullish_filtered]
                sharpe = np.mean(returns_d7) / (np.std(returns_d7) + 1e-6)

                if sharpe > best_bullish_sharpe:
                    best_bullish_sharpe = sharpe
                    best_bullish_threshold = threshold

        return {
            'bearish_divergence_threshold': best_bearish_threshold or 25,
            'bullish_divergence_threshold': best_bullish_threshold or 25,
            'bearish_sharpe': best_bearish_sharpe,
            'bullish_sharpe': best_bullish_sharpe
        }

    def generate_current_recommendation(self) -> Dict:
        """
        Generate actionable recommendation based on current divergence state.

        Uses the 4 NEW categories based on mean reversion logic:
        1. 4H Overextended (Daily low, 4H high) → Take profits
        2. Bullish Convergence (Both low) → Re-entry
        3. Daily Overextended (Daily high, 4H low) → Reversal
        4. Bearish Convergence (Both high) → Exit
        """
        # Get current state
        current_daily = float(self.daily_percentiles.iloc[-1])
        current_4h = float(self.hourly_4h_percentiles.iloc[-1])
        current_div = current_daily - current_4h
        current_price = float(self.daily_data['Close'].iloc[-1])

        recommendation = {
            'current_daily_percentile': current_daily,
            'current_4h_percentile': current_4h,
            'divergence_pct': current_div,
            'current_price': current_price,
            'signal': 'neutral',
            'action': 'wait',
            'reasoning': [],
            'category': 'none'
        }

        # TYPE A: 4H Overextended (Daily low, 4H high)
        # Negative divergence + Daily < 50
        if current_div < -15 and current_daily < 50:
            recommendation['category'] = '4h_overextended'
            if current_div < -35:
                recommendation['signal'] = '4h_overextended_strong'
                recommendation['action'] = 'take_profit_75_percent'
                recommendation['reasoning'].append(f"STRONG 4H overextension: 4H at {current_4h:.1f}%, Daily only {current_daily:.1f}%")
                recommendation['reasoning'].append(f"4H is {abs(current_div):.1f}% ahead of daily - high probability pullback")
                recommendation['reasoning'].append("Mean reversion: 4H likely to retrace toward daily levels")
            elif current_div < -25:
                recommendation['signal'] = '4h_overextended_moderate'
                recommendation['action'] = 'take_profit_50_percent'
                recommendation['reasoning'].append(f"Moderate 4H overextension: 4H at {current_4h:.1f}%, Daily at {current_daily:.1f}%")
                recommendation['reasoning'].append(f"4H is {abs(current_div):.1f}% ahead - consider taking partial profits")
            else:
                recommendation['signal'] = '4h_overextended_weak'
                recommendation['action'] = 'take_profit_25_percent'
                recommendation['reasoning'].append(f"4H showing early overextension vs Daily")
                recommendation['reasoning'].append(f"Consider scaling out of positions")

        # TYPE B: Bullish Convergence (Both low, aligned)
        elif abs(current_div) < 15 and current_daily < 30:
            recommendation['category'] = 'bullish_convergence'
            recommendation['signal'] = 'bullish_convergence'
            recommendation['action'] = 'buy_or_add_position'
            recommendation['reasoning'].append(f"Both Daily ({current_daily:.1f}%) and 4H ({current_4h:.1f}%) oversold and aligned")
            recommendation['reasoning'].append("Convergence at low levels suggests bounce opportunity")
            recommendation['reasoning'].append("Mean reversion: Both timeframes aligned for upward move")

        # TYPE C: Daily Overextended (Daily high, 4H low)
        # Positive divergence + Daily > 50
        elif current_div > 15 and current_daily > 50:
            recommendation['category'] = 'daily_overextended'
            if current_div > 35:
                recommendation['signal'] = 'daily_overextended_strong'
                recommendation['action'] = 'exit_or_short'
                recommendation['reasoning'].append(f"STRONG Daily overextension: Daily at {current_daily:.1f}%, 4H only {current_4h:.1f}%")
                recommendation['reasoning'].append(f"Daily is {current_div:.1f}% ahead but 4H not confirming - reversal likely")
                recommendation['reasoning'].append("Mean reversion: Daily likely to pull back, 4H showing weakness")
            elif current_div > 25:
                recommendation['signal'] = 'daily_overextended_moderate'
                recommendation['action'] = 'reduce_exposure_50_percent'
                recommendation['reasoning'].append(f"Moderate Daily overextension: Daily at {current_daily:.1f}%, 4H at {current_4h:.1f}%")
                recommendation['reasoning'].append(f"Daily running ahead without 4H confirmation")
            else:
                recommendation['signal'] = 'daily_overextended_weak'
                recommendation['action'] = 'tighten_stops'
                recommendation['reasoning'].append(f"Daily showing early signs of overextension")
                recommendation['reasoning'].append(f"Monitor for reversal signals")

        # TYPE D: Bearish Convergence (Both high, aligned)
        elif abs(current_div) < 15 and current_daily > 70:
            recommendation['category'] = 'bearish_convergence'
            recommendation['signal'] = 'bearish_convergence'
            recommendation['action'] = 'exit_all_or_short'
            recommendation['reasoning'].append(f"Both Daily ({current_daily:.1f}%) and 4H ({current_4h:.1f}%) overbought and aligned")
            recommendation['reasoning'].append("Convergence at high levels suggests reversal imminent")
            recommendation['reasoning'].append("Mean reversion: Both timeframes aligned for downward move")

        # NEUTRAL: Low divergence, mid-range
        else:
            recommendation['signal'] = 'neutral'
            recommendation['action'] = 'hold_or_wait'
            recommendation['reasoning'].append(f"Daily at {current_daily:.1f}%, 4H at {current_4h:.1f}% (divergence {current_div:+.1f}%)")
            recommendation['reasoning'].append("No clear divergence signal - wait for better setup")

        return recommendation

    def run_complete_analysis(self) -> MultiTimeframeAnalysis:
        """
        Run complete multi-timeframe divergence analysis.

        Returns:
            Complete analysis with backtested results and recommendations
        """
        print(f"\nRunning multi-timeframe analysis for {self.ticker}...")

        # Backtest divergence signals
        events = self.backtest_divergence_signals()
        print(f"Found {len(events)} divergence events")

        # Analyze patterns
        stats = self.analyze_divergence_patterns(events)

        # Find optimal thresholds
        optimal_thresholds = self.find_optimal_thresholds(events)

        # Generate current recommendation
        current_rec = self.generate_current_recommendation()

        # Get current state
        current_daily = float(self.daily_percentiles.iloc[-1])
        current_4h = float(self.hourly_4h_percentiles.iloc[-1])
        current_div = current_daily - current_4h

        analysis = MultiTimeframeAnalysis(
            ticker=self.ticker,
            analysis_date=datetime.now().isoformat(),
            current_daily_percentile=current_daily,
            current_4h_percentile=current_4h,
            current_divergence_pct=current_div,
            current_signal=current_rec['signal'],
            divergence_events=[asdict(e) for e in events],
            divergence_stats=stats,
            optimal_thresholds=optimal_thresholds,
            current_recommendation=current_rec
        )

        return analysis


def _convert_nan_to_none(obj):
    """Convert NaN values to None for JSON serialization."""
    if isinstance(obj, dict):
        return {key: _convert_nan_to_none(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_convert_nan_to_none(item) for item in obj]
    elif isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    else:
        return obj


def run_multi_timeframe_analysis(ticker: str) -> Dict:
    """
    Convenience function to run complete multi-timeframe analysis.

    Args:
        ticker: Stock ticker

    Returns:
        Dictionary with complete analysis results
    """
    analyzer = MultiTimeframeAnalyzer(ticker)
    analysis = analyzer.run_complete_analysis()

    result = asdict(analysis)

    # Clean NaN values for JSON serialization
    result = _convert_nan_to_none(result)

    return result
