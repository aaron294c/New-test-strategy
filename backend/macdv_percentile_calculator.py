"""
MACD-V Percentile Calculator

Extends MACD-V with categorical percentile ranks calculated within market regime zones.
Similar to RSI-MA percentiles but respects MACD-V's inherent zone structure.

Zone Structure:
- Extreme Bearish: < -100
- Strong Bearish: -100 to -50
- Ranging: -50 to +50 (unified mean-reversion zone)
- Strong Bullish: +50 to +100
- Extreme Bullish: > +100
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    from macdv_calculator import MACDVCalculator
except ModuleNotFoundError:
    from backend.macdv_calculator import MACDVCalculator  # type: ignore


class MACDVPercentileCalculator(MACDVCalculator):
    """
    MACD-V calculator with categorical percentile functionality.

    Calculates percentile ranks within market regime zones for better
    relative positioning analysis.
    """

    # Zone definitions for categorical percentiles
    ZONES = [
        ("extreme_bearish", -float('inf'), -100),
        ("strong_bearish", -100, -50),
        ("ranging", -50, 50),  # Unified ranging zone
        ("strong_bullish", 50, 100),
        ("extreme_bullish", 100, float('inf')),
    ]

    def __init__(
        self,
        fast_length: int = 12,
        slow_length: int = 26,
        signal_length: int = 9,
        atr_length: int = 26,
        percentile_lookback: int = 252  # 1 year for percentile calculation
    ):
        super().__init__(fast_length, slow_length, signal_length, atr_length)
        self.percentile_lookback = percentile_lookback

    def calculate_percentile_ranks(
        self,
        macdv_series: pd.Series,
        method: str = "categorical"
    ) -> pd.Series:
        """
        Calculate percentile ranks for MACD-V values.

        Args:
            macdv_series: Series of MACD-V values
            method: "categorical" (within zones), "global" (all values), or "asymmetric"

        Returns:
            Series of percentile ranks (0-100)
        """
        if method == "categorical":
            return self._calculate_categorical_percentiles(macdv_series)
        elif method == "global":
            return self._calculate_global_percentiles(macdv_series)
        elif method == "asymmetric":
            return self._calculate_asymmetric_percentiles(macdv_series)
        else:
            raise ValueError(f"Unknown method: {method}. Use 'categorical', 'global', or 'asymmetric'")

    def _calculate_categorical_percentiles(self, macdv_series: pd.Series) -> pd.Series:
        """
        Calculate percentiles within each market regime zone.

        This is the RECOMMENDED method as it respects the natural structure
        of MACD-V zones while providing relative positioning.
        """
        percentile_series = pd.Series(index=macdv_series.index, dtype=float)

        for zone_name, zone_min, zone_max in self.ZONES:
            # Get values in this zone
            zone_mask = (macdv_series >= zone_min) & (macdv_series < zone_max)
            zone_indices = macdv_series.index[zone_mask]

            if len(zone_indices) == 0:
                continue

            # Calculate rolling percentile within this zone
            for idx in zone_indices:
                # Get lookback window
                window_start = max(0, macdv_series.index.get_loc(idx) - self.percentile_lookback)
                window_data = macdv_series.iloc[window_start:macdv_series.index.get_loc(idx) + 1]

                # Filter to values in the same zone
                window_zone_data = window_data[(window_data >= zone_min) & (window_data < zone_max)]

                if len(window_zone_data) < 2:
                    percentile_series.loc[idx] = 50.0  # Default to neutral if insufficient data
                    continue

                # Calculate percentile rank
                current_val = macdv_series.loc[idx]
                pct_rank = (window_zone_data < current_val).sum() / len(window_zone_data) * 100
                percentile_series.loc[idx] = round(pct_rank, 2)

        return percentile_series

    def _calculate_global_percentiles(self, macdv_series: pd.Series) -> pd.Series:
        """
        Calculate percentiles across all MACD-V values (simpler approach).

        This treats all values equally regardless of zone, which may be
        less meaningful but is simpler to interpret.
        """
        percentile_series = pd.Series(index=macdv_series.index, dtype=float)

        for i in range(len(macdv_series)):
            # Get lookback window
            window_start = max(0, i - self.percentile_lookback)
            window_data = macdv_series.iloc[window_start:i + 1]

            if len(window_data) < 2:
                percentile_series.iloc[i] = 50.0
                continue

            # Calculate percentile rank
            current_val = macdv_series.iloc[i]
            pct_rank = (window_data < current_val).sum() / len(window_data) * 100
            percentile_series.iloc[i] = round(pct_rank, 2)

        return percentile_series

    def _calculate_asymmetric_percentiles(self, macdv_series: pd.Series) -> pd.Series:
        """
        Calculate percentiles separately for bullish and bearish regimes.

        This captures directional bias but is more complex.
        """
        percentile_series = pd.Series(index=macdv_series.index, dtype=float)

        # Bullish regime: >= 0
        bullish_mask = macdv_series >= 0
        if bullish_mask.any():
            bullish_data = macdv_series[bullish_mask]
            for idx in bullish_data.index:
                window_start = max(0, macdv_series.index.get_loc(idx) - self.percentile_lookback)
                window_data = macdv_series.iloc[window_start:macdv_series.index.get_loc(idx) + 1]
                window_bullish = window_data[window_data >= 0]

                if len(window_bullish) < 2:
                    percentile_series.loc[idx] = 50.0
                    continue

                current_val = macdv_series.loc[idx]
                pct_rank = (window_bullish < current_val).sum() / len(window_bullish) * 100
                percentile_series.loc[idx] = round(pct_rank, 2)

        # Bearish regime: < 0
        bearish_mask = macdv_series < 0
        if bearish_mask.any():
            bearish_data = macdv_series[bearish_mask]
            for idx in bearish_data.index:
                window_start = max(0, macdv_series.index.get_loc(idx) - self.percentile_lookback)
                window_data = macdv_series.iloc[window_start:macdv_series.index.get_loc(idx) + 1]
                window_bearish = window_data[window_data < 0]

                if len(window_bearish) < 2:
                    percentile_series.loc[idx] = 50.0
                    continue

                current_val = macdv_series.loc[idx]
                pct_rank = (window_bearish < current_val).sum() / len(window_bearish) * 100
                percentile_series.loc[idx] = round(pct_rank, 2)

        return percentile_series

    def calculate_macdv_with_percentiles(
        self,
        data: pd.DataFrame,
        method: str = "categorical",
        source_col: str = 'close'
    ) -> pd.DataFrame:
        """
        Calculate MACD-V with percentile ranks.

        Args:
            data: DataFrame with OHLC data
            method: Percentile calculation method
            source_col: Column to use as source

        Returns:
            DataFrame with MACD-V columns and percentile ranks:
            - macdv_val: MACD-V value
            - macdv_signal: Signal line
            - macdv_hist: Histogram
            - macdv_color: Color classification
            - macdv_trend: Trend classification
            - macdv_percentile: Percentile rank (0-100)
            - macdv_zone: Zone classification
        """
        # Calculate base MACD-V
        df = self.calculate_macdv(data, source_col)

        # Calculate percentile ranks
        df['macdv_percentile'] = self.calculate_percentile_ranks(df['macdv_val'], method=method)

        # Add zone classification
        df['macdv_zone'] = self._classify_zone(df['macdv_val'])

        return df

    def _classify_zone(self, macdv_series: pd.Series) -> pd.Series:
        """Classify MACD-V values into zones."""
        zones = pd.Series('unknown', index=macdv_series.index)

        for zone_name, zone_min, zone_max in self.ZONES:
            mask = (macdv_series >= zone_min) & (macdv_series < zone_max)
            zones[mask] = zone_name

        return zones

    def get_zone_statistics(
        self,
        data: pd.DataFrame,
        method: str = "categorical"
    ) -> Dict[str, Dict[str, float]]:
        """
        Get statistical breakdown by zone.

        Args:
            data: DataFrame with OHLC data
            method: Percentile calculation method

        Returns:
            Dictionary with statistics for each zone
        """
        df = self.calculate_macdv_with_percentiles(data, method=method)

        stats = {}
        for zone_name, zone_min, zone_max in self.ZONES:
            zone_data = df[(df['macdv_val'] >= zone_min) & (df['macdv_val'] < zone_max)]

            if len(zone_data) == 0:
                stats[zone_name] = {
                    'count': 0,
                    'pct_of_total': 0.0,
                    'avg_percentile': np.nan,
                    'min_val': np.nan,
                    'max_val': np.nan,
                    'avg_val': np.nan
                }
                continue

            stats[zone_name] = {
                'count': int(len(zone_data)),
                'pct_of_total': float(len(zone_data) / len(df) * 100),
                'avg_percentile': float(zone_data['macdv_percentile'].mean()),
                'min_val': float(zone_data['macdv_val'].min()),
                'max_val': float(zone_data['macdv_val'].max()),
                'avg_val': float(zone_data['macdv_val'].mean())
            }

        return stats

    def prepare_chart_data(
        self,
        data: pd.DataFrame,
        method: str = "categorical"
    ) -> Dict:
        """
        Prepare chart data with percentiles.

        Args:
            data: DataFrame with OHLC data
            method: Percentile calculation method

        Returns:
            Dictionary with chart data including percentiles
        """
        df = self.calculate_macdv_with_percentiles(data, method=method)

        # Get base chart data
        chart_data = super().prepare_chart_data(df)

        # Add percentile data
        chart_data['macdv_percentile'] = df['macdv_percentile'].replace({np.nan: None}).tolist()
        chart_data['macdv_zone'] = df['macdv_zone'].tolist()
        chart_data['current']['macdv_percentile'] = float(df['macdv_percentile'].iloc[-1]) \
            if pd.notna(df['macdv_percentile'].iloc[-1]) else None
        chart_data['current']['macdv_zone'] = str(df['macdv_zone'].iloc[-1])

        # Add zone statistics
        chart_data['zone_stats'] = self.get_zone_statistics(data, method=method)
        chart_data['percentile_method'] = method
        chart_data['percentile_lookback'] = self.percentile_lookback

        return chart_data


def get_macdv_percentile_chart_data(
    ticker: str,
    days: int = 252,
    method: str = "categorical"
) -> Dict:
    """
    Get MACD-V chart data with percentiles for a single ticker.

    Args:
        ticker: Ticker symbol
        days: Number of days of historical data
        method: Percentile calculation method ("categorical", "global", or "asymmetric")

    Returns:
        Dictionary with chart data including percentiles
    """
    import yfinance as yf

    try:
        # Fetch data
        df = yf.download(
            ticker,
            period=f'{days}d',
            interval='1d',
            progress=False,
            auto_adjust=True
        )

        if df.empty:
            return {
                'success': False,
                'error': f'No data available for {ticker}'
            }

        # Fix column names
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0].lower() if isinstance(col, tuple) else str(col).lower()
                         for col in df.columns]
        else:
            df.columns = [str(c).lower() for c in df.columns]

        # Calculate MACD-V with percentiles
        calculator = MACDVPercentileCalculator(
            fast_length=12,
            slow_length=26,
            signal_length=9,
            atr_length=26,
            percentile_lookback=252
        )
        chart_data = calculator.prepare_chart_data(df, method=method)

        return {
            'success': True,
            'ticker': ticker,
            'chart_data': chart_data
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'ticker': ticker
        }
