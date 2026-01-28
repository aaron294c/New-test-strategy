"""
MACD-V (MACD Volatility-Normalized) Calculator
Pine Script v6 implementation in Python

Calculates MACD normalized by ATR volatility for better cross-asset/regime comparison.
Includes dashboard mode with multi-timeframe analysis across multiple symbols.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
from pathlib import Path

class MACDVCalculator:
    """
    MACD-V Calculator following the Pine Script v6 implementation.

    Key features:
    - Volatility-normalized MACD using ATR(26)
    - Multi-timeframe support (M, W, D, 4H, 1H)
    - Dashboard mode with all swing framework tickers
    - Zone-based signal classification
    """

    def __init__(
        self,
        fast_length: int = 12,
        slow_length: int = 26,
        signal_length: int = 9,
        atr_length: int = 26
    ):
        self.fast_length = fast_length
        self.slow_length = slow_length
        self.signal_length = signal_length
        self.atr_length = atr_length

    def calculate_macdv(
        self,
        data: pd.DataFrame,
        source_col: str = 'close'
    ) -> pd.DataFrame:
        """
        Calculate MACD-V indicator.

        Args:
            data: DataFrame with OHLC data
            source_col: Column to use as source (default: 'close')

        Returns:
            DataFrame with MACD-V columns added:
            - macdv_val: MACD-V value (normalized by ATR)
            - macdv_signal: Signal line
            - macdv_hist: Histogram
            - macdv_color: Color classification
            - macdv_trend: Trend classification
        """
        df = data.copy()

        # Calculate EMAs
        fast_ma = df[source_col].ewm(span=self.fast_length, adjust=False).mean()
        slow_ma = df[source_col].ewm(span=self.slow_length, adjust=False).mean()

        # Calculate ATR for volatility normalization
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift(1))
        low_close = abs(df['low'] - df['close'].shift(1))
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=self.atr_length).mean()

        # Calculate MACD-V (normalized by ATR, scaled to %)
        macd_raw = fast_ma - slow_ma
        df['macdv_val'] = (macd_raw / atr * 100).round(2)

        # Signal line (EMA of MACD-V)
        df['macdv_signal'] = df['macdv_val'].ewm(span=self.signal_length, adjust=False).mean().round(2)

        # Histogram
        df['macdv_hist'] = (df['macdv_val'] - df['macdv_signal']).round(2)

        # Ranging detection (50 > val > -50 for 19+ bars)
        in_range = (df['macdv_val'] > -50) & (df['macdv_val'] < 50)
        in_range_shifted = in_range.shift(1).fillna(False)
        in_range_change = in_range & ~in_range_shifted

        # Count bars since last range entry
        bars_since_range = pd.Series(0, index=df.index)
        current_count = 0
        for i in range(len(df)):
            if in_range.iloc[i]:
                current_count += 1
            else:
                current_count = 0
            bars_since_range.iloc[i] = current_count

        # Color classification
        df['macdv_color'] = 'gray'  # default

        # Ranging (gray) - in range for 19+ bars
        ranging_mask = in_range & (bars_since_range >= 19)
        df.loc[ranging_mask, 'macdv_color'] = 'gray'

        # Risk (blue) - extreme values
        risk_up_mask = (df['macdv_val'] >= 150) & (df['macdv_val'] > df['macdv_signal'])
        risk_down_mask = (df['macdv_val'] <= -150) & (df['macdv_val'] < df['macdv_signal'])
        df.loc[risk_up_mask | risk_down_mask, 'macdv_color'] = 'blue'

        # Rallying (green-dark) - 150 > val >= 50 and rising
        rallying_mask = (df['macdv_val'] >= 50) & (df['macdv_val'] < 150) & (df['macdv_val'] > df['macdv_signal'])
        df.loc[rallying_mask, 'macdv_color'] = '#0d6b57'

        # Rebounding (green) - 50 > val > -150 and rising
        rebounding_mask = (df['macdv_val'] > -150) & (df['macdv_val'] < 50) & (df['macdv_val'] > df['macdv_signal'])
        df.loc[rebounding_mask, 'macdv_color'] = 'green'

        # Retracing (orange) - val > -50 and falling
        retracing_mask = (df['macdv_val'] > -50) & (df['macdv_val'] < df['macdv_signal'])
        df.loc[retracing_mask, 'macdv_color'] = 'orange'

        # Reversing (red) - -50 >= val > -150 and falling
        reversing_mask = (df['macdv_val'] > -150) & (df['macdv_val'] <= -50) & (df['macdv_val'] < df['macdv_signal'])
        df.loc[reversing_mask, 'macdv_color'] = 'red'

        # Trend classification
        df['macdv_trend'] = 'Neutral'
        df.loc[df['macdv_val'] > 50, 'macdv_trend'] = 'Bullish'
        df.loc[df['macdv_val'] < -50, 'macdv_trend'] = 'Bearish'
        df.loc[ranging_mask, 'macdv_trend'] = 'Ranging'

        return df

    def get_dashboard_data(
        self,
        symbols: List[str],
        timeframes: List[str] = ['1mo', '1wk', '1d', '1h', '4h']
    ) -> Dict:
        """
        Get MACD-V dashboard data for multiple symbols and timeframes.

        Args:
            symbols: List of ticker symbols
            timeframes: List of timeframes (yfinance intervals)

        Returns:
            Dictionary with dashboard data structure
        """
        dashboard = {
            'timestamp': datetime.now().isoformat(),
            'symbols': {},
            'timeframes': timeframes
        }

        for symbol in symbols:
            try:
                symbol_data = {}

                for tf in timeframes:
                    # Fetch data for this timeframe
                    period = self._get_period_for_interval(tf)
                    df = yf.download(
                        symbol,
                        period=period,
                        interval=tf,
                        progress=False,
                        auto_adjust=True
                    )

                    if df.empty:
                        continue

                    # Ensure column names are lowercase and handle multi-index columns from yfinance
                    if isinstance(df.columns, pd.MultiIndex):
                        # For multi-index, take the first level
                        df.columns = [col[0].lower() if isinstance(col, tuple) else str(col).lower() for col in df.columns]
                    else:
                        # For regular index, just convert to lowercase
                        df.columns = [str(c).lower() for c in df.columns]

                    # Calculate MACD-V
                    df = self.calculate_macdv(df)

                    # Get latest values
                    latest = df.iloc[-1]

                    symbol_data[tf] = {
                        'macdv_val': float(latest['macdv_val']) if pd.notna(latest['macdv_val']) else None,
                        'macdv_signal': float(latest['macdv_signal']) if pd.notna(latest['macdv_signal']) else None,
                        'macdv_hist': float(latest['macdv_hist']) if pd.notna(latest['macdv_hist']) else None,
                        'macdv_color': str(latest['macdv_color']),
                        'macdv_trend': str(latest['macdv_trend']),
                        'close': float(latest['close']) if pd.notna(latest['close']) else None
                    }

                dashboard['symbols'][symbol] = symbol_data

            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
                dashboard['symbols'][symbol] = {'error': str(e)}

        return dashboard

    def _get_period_for_interval(self, interval: str) -> str:
        """Get appropriate period for a given interval."""
        interval_map = {
            '1mo': '5y',
            '1wk': '2y',
            '1d': '1y',
            '4h': '60d',
            '1h': '60d'
        }
        return interval_map.get(interval, '1y')

    def prepare_chart_data(self, data: pd.DataFrame) -> Dict:
        """
        Prepare chart data in the format expected by the frontend.

        Args:
            data: DataFrame with MACD-V calculations

        Returns:
            Dictionary with chart data
        """
        df = data.copy()

        # Ensure we have calculated MACD-V
        if 'macdv_val' not in df.columns:
            df = self.calculate_macdv(df)

        # Convert to chart format, replacing NaN with None for JSON compliance
        chart_data = {
            'dates': df.index.strftime('%Y-%m-%d').tolist(),
            'open': df['open'].replace({np.nan: None}).tolist(),
            'high': df['high'].replace({np.nan: None}).tolist(),
            'low': df['low'].replace({np.nan: None}).tolist(),
            'close': df['close'].replace({np.nan: None}).tolist(),
            'macdv_val': df['macdv_val'].replace({np.nan: None}).tolist(),
            'macdv_signal': df['macdv_signal'].replace({np.nan: None}).tolist(),
            'macdv_hist': df['macdv_hist'].replace({np.nan: None}).tolist(),
            'macdv_color': df['macdv_color'].tolist(),
            'macdv_trend': df['macdv_trend'].tolist(),
            'current': {
                'macdv_val': float(df['macdv_val'].iloc[-1]) if pd.notna(df['macdv_val'].iloc[-1]) else None,
                'macdv_signal': float(df['macdv_signal'].iloc[-1]) if pd.notna(df['macdv_signal'].iloc[-1]) else None,
                'macdv_hist': float(df['macdv_hist'].iloc[-1]) if pd.notna(df['macdv_hist'].iloc[-1]) else None,
                'macdv_color': str(df['macdv_color'].iloc[-1]),
                'macdv_trend': str(df['macdv_trend'].iloc[-1]),
                'close': float(df['close'].iloc[-1]) if pd.notna(df['close'].iloc[-1]) else None,
                'timestamp': df.index[-1].isoformat() if hasattr(df.index[-1], 'isoformat') else str(df.index[-1])
            },
            'thresholds': {
                'strong_momentum': 50,
                'risk_up': 150,
                'risk_down': -150,
                'ranging_up': 50,
                'ranging_down': -50
            }
        }

        return chart_data


def get_macdv_chart_data(ticker: str, days: int = 252) -> Dict:
    """
    Get MACD-V chart data for a single ticker.

    Args:
        ticker: Ticker symbol
        days: Number of days of historical data

    Returns:
        Dictionary with chart data
    """
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

        # Ensure column names are lowercase and handle multi-index columns from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            # For multi-index, take the first level (e.g., ('Close', 'AAPL') -> 'Close')
            df.columns = [col[0].lower() if isinstance(col, tuple) else str(col).lower() for col in df.columns]
        else:
            # For regular index, just convert to lowercase
            df.columns = [str(c).lower() for c in df.columns]

        # Calculate MACD-V
        calculator = MACDVCalculator()
        chart_data = calculator.prepare_chart_data(df)

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


# Swing framework tickers (using valid Yahoo Finance symbols)
SWING_FRAMEWORK_TICKERS = [
    'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'QQQ', 'SPY',
    'GLD', 'SLV', 'TSLA', 'NFLX', 'BRK-B', 'WMT', 'UNH', 'AVGO',
    'LLY', 'TSM', 'ORCL', 'OXY', 'XOM', 'CVX', 'JPM', 'BAC',
    'ES=F', 'NQ=F', 'BTC-USD', '^VIX', 'DX-Y.NYB', '^TNX', 'XLI'
]
