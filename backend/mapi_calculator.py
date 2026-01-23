"""
MAPI (Momentum-Adapted Percentile Indicator) Calculator

Designed for momentum stocks (AAPL, TSLA, AVGO, NFLX) as an alternative to RSI-MA.
Uses EMA distance and slope velocity with percentile framework.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional


class MAPICalculator:
    """
    Momentum-Adapted Percentile Indicator (MAPI)

    Components:
    1. EDR (EMA Distance Ratio) - Price distance from EMA normalized by ATR
    2. ESV (EMA Slope Velocity) - Rate of change of EMA
    3. Composite Momentum Score - Weighted combination with percentiles
    """

    def __init__(
        self,
        ema_period: int = 20,
        ema_slope_period: int = 5,
        atr_period: int = 14,
        edr_lookback: int = 60,
        esv_lookback: int = 90,
        composite_rsi_length: int = 14,
        composite_ma_length: int = 14,
        composite_percentile_lookback: int = 252,
    ):
        self.ema_period = ema_period
        self.ema_slope_period = ema_slope_period
        self.atr_period = atr_period
        self.edr_lookback = edr_lookback
        self.esv_lookback = esv_lookback
        self.composite_rsi_length = composite_rsi_length
        self.composite_ma_length = composite_ma_length
        self.composite_percentile_lookback = composite_percentile_lookback

    def calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Average True Range"""
        high = df['high']
        low = df['low']
        close = df['close']

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(span=self.atr_period, adjust=False).mean()

        return atr

    def calculate_edr(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate EMA Distance Ratio (EDR)

        Returns:
            edr: Raw EDR values
            ema20: EMA(20) values for reference
        """
        close = df['close']
        ema20 = close.ewm(span=self.ema_period, adjust=False).mean()
        atr = self.calculate_atr(df)

        # Normalize distance by ATR to account for volatility
        edr = (close - ema20) / atr

        return edr, ema20

    def calculate_esv(self, ema: pd.Series) -> pd.Series:
        """
        Calculate EMA Slope Velocity (ESV)

        Measures rate of change of EMA itself
        """
        ema_change = ema - ema.shift(self.ema_slope_period)
        esv = (ema_change / ema.shift(self.ema_slope_period)) * 100

        return esv

    def calculate_percentile_rank(self, series: pd.Series, lookback: int) -> pd.Series:
        """Calculate rolling percentile rank using vectorized operations for performance"""
        import numpy as np

        percentiles = pd.Series(index=series.index, dtype=float)
        values = series.values

        for i in range(len(series)):
            start_idx = max(0, i - lookback + 1)
            window = values[start_idx:i+1]

            if len(window) < 2:
                percentiles.iloc[i] = 50.0
            else:
                rank = np.sum(window[:-1] < window[-1])
                percentiles.iloc[i] = (rank / (len(window) - 1)) * 100

        return percentiles

    def calculate_rsi(self, series: pd.Series, length: int) -> pd.Series:
        """
        Wilder-style RSI on an arbitrary series (commonly a diff/return series).

        RSI is centered around 50 when gains ~= losses, which is why RSI-MA on
        changes of log returns often clusters near ~50.
        """
        gains = series.where(series > 0, 0.0)
        losses = -series.where(series < 0, 0.0)

        avg_gains = gains.ewm(alpha=1 / length, adjust=False).mean()
        avg_losses = losses.ewm(alpha=1 / length, adjust=False).mean()

        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50.0)

    def calculate_composite_raw_score(
        self,
        edr: pd.Series,
        esv: pd.Series,
        edr_weight: float = 0.6,
        esv_weight: float = 0.4,
    ) -> pd.Series:
        """
        Two-step, RSI-MA-like composite:
        1) Take changes (diffs) of component series (mean-reverting around 0)
        2) Apply RSI + EMA smoothing to get a raw oscillator that clusters near 50
        """
        edr_delta = edr.diff().fillna(0.0)
        esv_delta = esv.diff().fillna(0.0)

        edr_rsi = self.calculate_rsi(edr_delta, self.composite_rsi_length)
        esv_rsi = self.calculate_rsi(esv_delta, self.composite_rsi_length)

        composite = (edr_rsi * edr_weight) + (esv_rsi * esv_weight)
        composite_smoothed = composite.ewm(span=self.composite_ma_length, adjust=False).mean()
        return composite_smoothed

    def calculate_composite_score(
        self,
        edr_percentile: pd.Series,
        esv_percentile: pd.Series,
        edr_weight: float = 0.6,
        esv_weight: float = 0.4
    ) -> pd.Series:
        """
        Calculate Composite Momentum Score

        Combines EDR and ESV percentiles with weights
        """
        composite = (edr_percentile * edr_weight) + (esv_percentile * esv_weight)
        return composite

    def detect_ema_bounce(
        self,
        df: pd.DataFrame,
        edr: pd.Series,
        ema20: pd.Series,
        composite_score: pd.Series,
        esv_percentile: pd.Series
    ) -> pd.Series:
        """
        Detect EMA bounce opportunities

        Conditions:
        1. Price touches or slightly penetrates EMA(20)
        2. Composite Score drops to 30-45% (pullback)
        3. ESV > 40% (trend still intact)
        4. Price bounces back above 50% composite
        """
        close = df['close']

        # Distance to EMA as percentage
        distance_to_ema = abs((close - ema20) / ema20) * 100

        # Detect touch (within 1% of EMA)
        ema_touch = distance_to_ema < 1.0

        # Pullback in composite score (30-45%)
        pullback_zone = (composite_score >= 30) & (composite_score <= 45)

        # Trend still intact (ESV > 40%)
        trend_intact = esv_percentile > 40

        # Price bouncing (composite recovering)
        composite_rising = composite_score > composite_score.shift(1)

        # Combine conditions
        bounce_signal = ema_touch & pullback_zone & trend_intact & composite_rising

        return bounce_signal

    def calculate_regime(self, df: pd.DataFrame, adx_period: int = 14) -> pd.Series:
        """
        Calculate ADX for regime detection

        ADX > 25 = Momentum
        ADX < 20 = Mean Reversion
        """
        high = df['high']
        low = df['low']
        close = df['close']

        # Calculate +DM and -DM
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low

        plus_dm = pd.Series(0.0, index=df.index)
        minus_dm = pd.Series(0.0, index=df.index)

        plus_dm[(up_move > down_move) & (up_move > 0)] = up_move
        minus_dm[(down_move > up_move) & (down_move > 0)] = down_move

        # Calculate ATR
        atr = self.calculate_atr(df)

        # Smooth DM
        plus_dm_smooth = plus_dm.ewm(span=adx_period, adjust=False).mean()
        minus_dm_smooth = minus_dm.ewm(span=adx_period, adjust=False).mean()

        # Calculate +DI and -DI
        plus_di = 100 * (plus_dm_smooth / atr)
        minus_di = 100 * (minus_dm_smooth / atr)

        # Calculate DX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)

        # Calculate ADX
        adx = dx.ewm(span=adx_period, adjust=False).mean()

        return adx

    def calculate_mapi(self, df: pd.DataFrame) -> Dict:
        """
        Calculate complete MAPI indicator

        Returns dict with all components and signals
        """
        # Calculate base components
        edr, ema20 = self.calculate_edr(df)
        esv = self.calculate_esv(ema20)

        # Calculate percentile ranks
        edr_percentile = self.calculate_percentile_rank(edr, self.edr_lookback)
        esv_percentile = self.calculate_percentile_rank(esv, self.esv_lookback)

        # Composite (raw) score centered near ~50 (RSI-MA-like)
        composite_score = self.calculate_composite_raw_score(edr, esv)

        # Percentile rank of the raw composite (used for signals/thresholds)
        composite_percentile_rank = self.calculate_percentile_rank(
            composite_score, self.composite_percentile_lookback
        )

        # EMA bounce detection
        bounce_signal = self.detect_ema_bounce(
            df, edr, ema20, composite_percentile_rank, esv_percentile
        )

        # Regime detection
        adx = self.calculate_regime(df)
        regime = pd.Series('Neutral', index=df.index)
        regime[adx > 25] = 'Momentum'
        regime[adx < 20] = 'Mean Reversion'

        # Entry signals
        strong_momentum_entry = (
            (composite_percentile_rank > 65) &
            (df['close'] > ema20) &
            (esv_percentile > 50)
        )

        pullback_entry = bounce_signal

        # Exit signal
        exit_signal = composite_percentile_rank < 40

        # EMA(50) for additional reference
        ema50 = df['close'].ewm(span=50, adjust=False).mean()

        return {
            'edr': edr,
            'edr_percentile': edr_percentile,
            'esv': esv,
            'esv_percentile': esv_percentile,
            'composite_score': composite_score,
            'composite_percentile_rank': composite_percentile_rank,
            'ema20': ema20,
            'ema50': ema50,
            'adx': adx,
            'regime': regime,
            'strong_momentum_entry': strong_momentum_entry,
            'pullback_entry': pullback_entry,
            'exit_signal': exit_signal,
            'bounce_signal': bounce_signal
        }

    def get_current_signal(self, df: pd.DataFrame) -> Dict:
        """Get current MAPI values and signals for latest bar"""
        mapi = self.calculate_mapi(df)

        latest_idx = df.index[-1]

        return {
            'date': latest_idx,
            'close': float(df['close'].iloc[-1]),
            'composite_score': float(mapi['composite_score'].iloc[-1]),
            'composite_percentile_rank': float(mapi['composite_percentile_rank'].iloc[-1]),
            'edr_percentile': float(mapi['edr_percentile'].iloc[-1]),
            'esv_percentile': float(mapi['esv_percentile'].iloc[-1]),
            'ema20': float(mapi['ema20'].iloc[-1]),
            'ema50': float(mapi['ema50'].iloc[-1]),
            'adx': float(mapi['adx'].iloc[-1]),
            'regime': str(mapi['regime'].iloc[-1]),
            'strong_momentum_entry': bool(mapi['strong_momentum_entry'].iloc[-1]),
            'pullback_entry': bool(mapi['pullback_entry'].iloc[-1]),
            'exit_signal': bool(mapi['exit_signal'].iloc[-1]),
            'distance_to_ema20_pct': float(((df['close'].iloc[-1] - mapi['ema20'].iloc[-1]) / mapi['ema20'].iloc[-1]) * 100)
        }


def prepare_mapi_chart_data(df: pd.DataFrame, calculator: MAPICalculator, days: int = 252) -> Dict:
    """
    Prepare MAPI data for frontend chart display

    Args:
        df: DataFrame with OHLC data
        calculator: MAPICalculator instance
        days: Number of days to return

    Returns:
        Dict with chart data and current signals
    """
    # Calculate MAPI
    mapi = calculator.calculate_mapi(df)

    # Get last N days
    df_recent = df.tail(days).copy()

    # Prepare chart arrays
    dates = [str(d.date()) if hasattr(d, 'date') else str(d) for d in df_recent.index]

    valid_composite = mapi['composite_score'].dropna()
    composite_thresholds_raw = {
        # These are raw composite values at the percentile cutoffs used by the strategy
        'p30': float(np.percentile(valid_composite, 30)) if len(valid_composite) else 50.0,
        'p40': float(np.percentile(valid_composite, 40)) if len(valid_composite) else 50.0,
        'p45': float(np.percentile(valid_composite, 45)) if len(valid_composite) else 50.0,
        'p50': float(np.percentile(valid_composite, 50)) if len(valid_composite) else 50.0,
        'p65': float(np.percentile(valid_composite, 65)) if len(valid_composite) else 50.0,
    }

    result = {
        'dates': dates,
        'open': df_recent['open'].tolist() if 'open' in df_recent.columns else df_recent['close'].tolist(),
        'high': df_recent['high'].tolist() if 'high' in df_recent.columns else df_recent['close'].tolist(),
        'low': df_recent['low'].tolist() if 'low' in df_recent.columns else df_recent['close'].tolist(),
        'close': df_recent['close'].tolist(),
        'composite_score': mapi['composite_score'].tail(days).tolist(),
        'composite_percentile_rank': mapi['composite_percentile_rank'].tail(days).tolist(),
        'edr_percentile': mapi['edr_percentile'].tail(days).tolist(),
        'esv_percentile': mapi['esv_percentile'].tail(days).tolist(),
        'ema20': mapi['ema20'].tail(days).tolist(),
        'ema50': mapi['ema50'].tail(days).tolist(),
        'adx': mapi['adx'].tail(days).tolist(),
        'regime': mapi['regime'].tail(days).tolist(),
        'strong_momentum_signals': mapi['strong_momentum_entry'].tail(days).tolist(),
        'pullback_signals': mapi['pullback_entry'].tail(days).tolist(),
        'exit_signals': mapi['exit_signal'].tail(days).tolist(),

        # Current values
        'current': calculator.get_current_signal(df),

        # Percentile thresholds for reference
        'thresholds': {
            'strong_momentum': 65,
            'pullback_zone_low': 30,
            'pullback_zone_high': 45,
            'exit_threshold': 40,
            'adx_momentum': 25,
            'adx_mean_reversion': 20
        },
        # Raw composite values at the same percentile cutoffs (RSI-MA-style horizontal lines)
        'composite_thresholds_raw': composite_thresholds_raw,
    }

    return result
