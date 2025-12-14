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

MARKET_HOURS_PER_DAY = 6.5
FOUR_H_BAR_INTERVAL_HOURS = 4
# Approx 1.625 4H bars per trading day (6.5 market hours / 4H bar)
BARS_PER_TRADING_DAY_4H = MARKET_HOURS_PER_DAY / FOUR_H_BAR_INTERVAL_HOURS

# Percentile windows aligned by time period (≈ 1 trading year)
DAILY_PERCENTILE_WINDOW = 252
FOUR_H_PERCENTILE_WINDOW = int(round(DAILY_PERCENTILE_WINDOW * BARS_PER_TRADING_DAY_4H))  # 410


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
                 lookback_days: int = 730,
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

        # 4H RSI-MA calculated on true 4H bars (from hourly resample)
        self.data_4h, self.rsi_ma_4h = self._calculate_rsi_ma_from_hourly(self.hourly_4h_data)

        # Calculate percentile ranks using comparable lookback periods
        # Daily: 252 daily bars ≈ 1 trading year
        self.daily_percentiles = self._calculate_percentile_ranks(
            self.daily_rsi_ma,
            window=DAILY_PERCENTILE_WINDOW
        )

        # 4H: ~410 4H bars ≈ 252 trading days × 1.625 bars/day
        self.percentiles_4h = self._calculate_percentile_ranks(
            self.rsi_ma_4h,
            window=FOUR_H_PERCENTILE_WINDOW
        )
        # Align to daily (use last 4H value of day, then forward-fill weekends/holidays)
        self.hourly_4h_percentiles = self.percentiles_4h.resample('1D').last().ffill()

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

    def _calculate_rsi_ma_from_hourly(self, hourly_data: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        """
        Calculate 4H RSI-MA by resampling hourly data to 4H bars.

        Note: Percentiles are computed on the 4H bars (not on a daily-resampled series)
        to keep the lookback period comparable to the daily timeframe.
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
        return data_4h, rsi_ma_4h

    def _calculate_percentile_ranks(self, indicator: pd.Series,
                                   window: int = 252) -> pd.Series:
        """
        Calculate rolling percentile ranks (0-100).

        Uses a strict "percent of prior values below current" definition, matching
        the project's RSI-MA percentile logic used elsewhere (framework/duration).
        """

        def rolling_percentile_rank(window_series: pd.Series) -> float:
            if len(window_series) < window:
                return np.nan
            current_value = window_series.iloc[-1]
            below_count = (window_series.iloc[:-1] < current_value).sum()
            denom = max(len(window_series) - 1, 1)
            return float(below_count / denom * 100.0)

        return indicator.rolling(
            window=window,
            min_periods=window
        ).apply(rolling_percentile_rank, raw=False)

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

    def find_optimal_thresholds(self, divergence_series: pd.DataFrame) -> Dict[str, float]:
        """
        Compute per-ticker dislocation thresholds from historical divergence gaps.

        We treat a "dislocation" as the percentile gap between daily and 4H:
          gap = abs(daily_percentile - 4h_percentile)

        For practical usage, the 85th percentile (P85) is a good "significant"
        dislocation threshold and P95 is "extreme". We compute these overall and
        by divergence direction (positive vs negative).

        Notes:
        - This intentionally does NOT optimize on returns (Sharpe), because the
          4-category framework ("4h_overextended", "bullish_convergence",
          "daily_overextended", "bearish_convergence") is the primary signal
          interpretation and we want stable, distribution-based thresholds.
        """
        if divergence_series is None or divergence_series.empty or "divergence_pct" not in divergence_series:
            return {
                "bearish_divergence_threshold": 25,
                "bullish_divergence_threshold": 25,
                "bearish_sharpe": None,
                "bullish_sharpe": None,
                "dislocation_abs_p75": None,
                "dislocation_abs_p85": None,
                "dislocation_abs_p95": None,
                "dislocation_positive_p85": None,
                "dislocation_negative_p85": None,
                "dislocation_stats": {},
                "dislocation_sample": {
                    "n_days": 0,
                    "start_date": None,
                    "end_date": None,
                    "lookback_days_hourly": self.lookback_days,
                    "percentile_windows": {
                        "daily": DAILY_PERCENTILE_WINDOW,
                        "four_h": FOUR_H_PERCENTILE_WINDOW,
                    },
                },
            }

        divergence_values = divergence_series["divergence_pct"].dropna().to_numpy(dtype=float)
        if divergence_values.size == 0:
            return {
                "bearish_divergence_threshold": 25,
                "bullish_divergence_threshold": 25,
                "bearish_sharpe": None,
                "bullish_sharpe": None,
                "dislocation_abs_p75": None,
                "dislocation_abs_p85": None,
                "dislocation_abs_p95": None,
                "dislocation_positive_p85": None,
                "dislocation_negative_p85": None,
                "dislocation_stats": {},
                "dislocation_sample": {
                    "n_days": 0,
                    "start_date": None,
                    "end_date": None,
                    "lookback_days_hourly": self.lookback_days,
                    "percentile_windows": {
                        "daily": DAILY_PERCENTILE_WINDOW,
                        "four_h": FOUR_H_PERCENTILE_WINDOW,
                    },
                },
            }

        abs_gap = np.abs(divergence_values)

        pos_gap = np.abs(divergence_values[divergence_values > 0])
        neg_gap = np.abs(divergence_values[divergence_values < 0])

        def q(arr: np.ndarray, pct: float) -> Optional[float]:
            if arr.size < 30:
                return None
            return float(np.percentile(arr, pct))

        abs_p75 = q(abs_gap, 75)
        abs_p85 = q(abs_gap, 85)
        abs_p95 = q(abs_gap, 95)

        pos_p85 = q(pos_gap, 85)
        neg_p85 = q(neg_gap, 85)

        # Backwards-compatible keys expected by the existing frontend:
        # - "bearish_divergence_threshold" historically meant "positive divergence"
        # - "bullish_divergence_threshold" historically meant "negative divergence"
        # Map those to the direction-specific P85 dislocation levels.
        start_date = None
        end_date = None
        try:
            idx = divergence_series.index
            if len(idx) > 0:
                start_date = pd.Timestamp(idx.min()).strftime("%Y-%m-%d")
                end_date = pd.Timestamp(idx.max()).strftime("%Y-%m-%d")
        except Exception:
            start_date = None
            end_date = None

        thresholds = {
            "bearish_divergence_threshold": int(round(pos_p85)) if pos_p85 is not None else 25,
            "bullish_divergence_threshold": int(round(neg_p85)) if neg_p85 is not None else 25,
            "bearish_sharpe": None,
            "bullish_sharpe": None,
            "dislocation_abs_p75": abs_p75,
            "dislocation_abs_p85": abs_p85,
            "dislocation_abs_p95": abs_p95,
            "dislocation_positive_p85": pos_p85,
            "dislocation_negative_p85": neg_p85,
            "dislocation_sample": {
                "n_days": int(divergence_values.size),
                "start_date": start_date,
                "end_date": end_date,
                "lookback_days_hourly": int(self.lookback_days),
                "percentile_windows": {
                    "daily": DAILY_PERCENTILE_WINDOW,
                    "four_h": FOUR_H_PERCENTILE_WINDOW,
                },
            },
        }

        # Compare outcomes for horizons D1/D3/D7 between "high-gap" vs "low-gap" samples.
        # Uses daily close-to-close forward returns to match the swing framework’s D1/D3/D7 horizons.
        try:
            from scipy.stats import mannwhitneyu  # type: ignore
        except Exception:
            mannwhitneyu = None

        def _forward_returns(price: pd.Series, horizon_days: int) -> pd.Series:
            return (price.shift(-horizon_days) / price - 1.0) * 100.0

        def _stats_for_mask(mask_high: pd.Series, *, base_mask: Optional[pd.Series] = None) -> Dict:
            price = divergence_series.get("price")
            if price is None:
                return {}

            out: Dict[str, Dict] = {}
            for horizon in (1, 3, 7):
                fr = _forward_returns(price, horizon).dropna()
                high_mask = mask_high.reindex(fr.index, fill_value=False)
                if base_mask is not None:
                    base = base_mask.reindex(fr.index, fill_value=False)
                    high = fr[base & high_mask]
                    low = fr[base & ~high_mask]
                else:
                    high = fr[high_mask]
                    low = fr[~high_mask]

                horizon_key = f"D{horizon}"
                if len(high) < 20 or len(low) < 20:
                    out[horizon_key] = {
                        "n_high": int(len(high)),
                        "n_low": int(len(low)),
                        "mean_high": float(high.mean()) if len(high) else None,
                        "mean_low": float(low.mean()) if len(low) else None,
                        "median_high": float(high.median()) if len(high) else None,
                        "median_low": float(low.median()) if len(low) else None,
                        "win_rate_high": float((high > 0).mean() * 100) if len(high) else None,
                        "win_rate_low": float((low > 0).mean() * 100) if len(low) else None,
                        "delta_mean": float(high.mean() - low.mean()) if len(high) and len(low) else None,
                        "delta_median": float(high.median() - low.median()) if len(high) and len(low) else None,
                        "delta_win_rate": float((high > 0).mean() * 100 - (low > 0).mean() * 100) if len(high) and len(low) else None,
                        "p_value_mwu": None,
                    }
                    continue

                p_value = None
                if mannwhitneyu is not None:
                    try:
                        p_value = float(mannwhitneyu(high, low, alternative="two-sided").pvalue)
                    except Exception:
                        p_value = None

                out[horizon_key] = {
                    "n_high": int(len(high)),
                    "n_low": int(len(low)),
                    "mean_high": float(high.mean()),
                    "mean_low": float(low.mean()),
                    "median_high": float(high.median()),
                    "median_low": float(low.median()),
                    "win_rate_high": float((high > 0).mean() * 100),
                    "win_rate_low": float((low > 0).mean() * 100),
                    "delta_mean": float(high.mean() - low.mean()),
                    "delta_median": float(high.median() - low.median()),
                    "delta_win_rate": float((high > 0).mean() * 100 - (low > 0).mean() * 100),
                    "p_value_mwu": p_value,
                }
            return out

        gap_abs = divergence_series["divergence_pct"].abs()
        pos_mask = divergence_series["divergence_pct"] > 0
        neg_mask = divergence_series["divergence_pct"] < 0

        dislocation_stats: Dict[str, Dict] = {}

        if abs_p85 is not None:
            dislocation_stats["abs_p85"] = {
                "threshold": float(abs_p85),
                "horizons": _stats_for_mask(gap_abs >= abs_p85),
            }
        if abs_p95 is not None:
            dislocation_stats["abs_p95"] = {
                "threshold": float(abs_p95),
                "horizons": _stats_for_mask(gap_abs >= abs_p95),
            }
        if pos_p85 is not None:
            dislocation_stats["positive_p85"] = {
                "threshold": float(pos_p85),
                "horizons": _stats_for_mask(gap_abs >= pos_p85, base_mask=pos_mask),
            }
        if neg_p85 is not None:
            dislocation_stats["negative_p85"] = {
                "threshold": float(neg_p85),
                "horizons": _stats_for_mask(gap_abs >= neg_p85, base_mask=neg_mask),
            }

        thresholds["dislocation_stats"] = dislocation_stats
        return thresholds

    def generate_current_recommendation(self, dislocation_thresholds: Optional[Dict] = None) -> Dict:
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
        current_gap = abs(current_div)

        recommendation = {
            'current_daily_percentile': current_daily,
            'current_4h_percentile': current_4h,
            'divergence_pct': current_div,
            'dislocation_gap': current_gap,
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

        # Add per-ticker dislocation context (distribution-based thresholds)
        p85 = None
        p95 = None
        if isinstance(dislocation_thresholds, dict):
            p85 = dislocation_thresholds.get("dislocation_abs_p85")
            p95 = dislocation_thresholds.get("dislocation_abs_p95")

        recommendation["dislocation_p85"] = p85
        recommendation["dislocation_p95"] = p95

        dislocation_level = None
        if isinstance(p85, (int, float)) and isinstance(p95, (int, float)):
            if current_gap >= p95:
                dislocation_level = "extreme"
            elif current_gap >= p85:
                dislocation_level = "significant"
            else:
                dislocation_level = "normal"
            recommendation["reasoning"].append(
                f"Dislocation level: {dislocation_level} (gap {current_gap:.1f}% vs P85 {p85:.1f}%, P95 {p95:.1f}%)"
            )

        recommendation["dislocation_level"] = dislocation_level

        return recommendation

    def run_complete_analysis(self) -> MultiTimeframeAnalysis:
        """
        Run complete multi-timeframe divergence analysis.

        Returns:
            Complete analysis with backtested results and recommendations
        """
        print(f"\nRunning multi-timeframe analysis for {self.ticker}...")

        # Compute divergence series once (used for thresholding)
        divergence_series = self.calculate_divergence_series()

        # Dislocation thresholds (per-ticker)
        optimal_thresholds = self.find_optimal_thresholds(divergence_series)

        # Backtest divergence signals
        events = self.backtest_divergence_signals()
        print(f"Found {len(events)} divergence events")

        # Analyze patterns
        stats = self.analyze_divergence_patterns(events)

        # Generate current recommendation (with per-ticker dislocation thresholds)
        current_rec = self.generate_current_recommendation(optimal_thresholds)

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
