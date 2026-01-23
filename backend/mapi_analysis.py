"""
MAPI Analysis & Optimization Module

Backtests MAPI signals to find optimal entry thresholds for:
- Composite score percentile
- EDR percentile
- ESV percentile

Target metrics:
- Win rate > 65%
- Return expectancy > 1% over 7 days
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from mapi_calculator import MAPICalculator
import yfinance as yf
from datetime import datetime, timedelta


@dataclass
class BacktestResult:
    """Results from backtesting a specific threshold combination"""
    composite_threshold: float
    edr_threshold: float
    esv_threshold: Optional[float]
    total_trades: int
    winning_trades: int
    win_rate: float
    avg_return: float
    avg_winning_return: float
    avg_losing_return: float
    return_expectancy: float  # win_rate * avg_win + (1-win_rate) * avg_loss
    sharpe_ratio: float
    max_drawdown: float


@dataclass
class MAPISignal:
    """Current MAPI signal for a symbol"""
    symbol: str
    date: str
    price: float
    composite_score: float
    composite_percentile: float
    edr_percentile: float
    esv_percentile: float
    regime: str
    adx: float
    distance_to_ema20_pct: float
    entry_signal: bool
    days_since_last_signal: int
    historical_win_rate: float
    historical_avg_return: float
    sample_size: int


class MAPIAnalyzer:
    """Analyze and optimize MAPI entry thresholds"""

    def __init__(self, calculator: Optional[MAPICalculator] = None):
        self.calculator = calculator or MAPICalculator()

    def backtest_entry_threshold(
        self,
        df: pd.DataFrame,
        composite_threshold: float,
        edr_threshold: float,
        esv_threshold: Optional[float] = None,
        holding_period: int = 7,
        require_momentum: bool = True,
    ) -> BacktestResult:
        """
        Backtest a specific entry threshold combination

        Args:
            df: DataFrame with OHLCV data
            composite_threshold: Composite percentile threshold (e.g., 35)
            edr_threshold: EDR percentile threshold (e.g., 20)
            esv_threshold: Optional ESV percentile threshold
            holding_period: Days to hold position
            require_momentum: Require ADX > 25 (momentum regime)
        """
        mapi = self.calculator.calculate_mapi(df)

        # Entry conditions
        composite_entry = mapi['composite_percentile_rank'] >= composite_threshold
        edr_entry = mapi['edr_percentile'] >= edr_threshold
        price_above_ema = df['close'] > mapi['ema20']

        entry_signal = composite_entry & edr_entry & price_above_ema

        # Optional ESV filter
        if esv_threshold is not None:
            entry_signal = entry_signal & (mapi['esv_percentile'] >= esv_threshold)

        # Momentum regime filter
        if require_momentum:
            entry_signal = entry_signal & (mapi['adx'] > 25)

        # Calculate returns for each entry
        trades = []
        for i in range(len(df) - holding_period):
            if entry_signal.iloc[i]:
                entry_price = df['close'].iloc[i]
                exit_idx = min(i + holding_period, len(df) - 1)
                exit_price = df['close'].iloc[exit_idx]
                pct_return = ((exit_price - entry_price) / entry_price) * 100
                trades.append(pct_return)

        if not trades:
            return BacktestResult(
                composite_threshold=composite_threshold,
                edr_threshold=edr_threshold,
                esv_threshold=esv_threshold,
                total_trades=0,
                winning_trades=0,
                win_rate=0.0,
                avg_return=0.0,
                avg_winning_return=0.0,
                avg_losing_return=0.0,
                return_expectancy=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
            )

        trades_array = np.array(trades)
        winning_trades = trades_array[trades_array > 0]
        losing_trades = trades_array[trades_array <= 0]

        win_rate = len(winning_trades) / len(trades_array)
        avg_return = trades_array.mean()
        avg_winning = winning_trades.mean() if len(winning_trades) > 0 else 0.0
        avg_losing = losing_trades.mean() if len(losing_trades) > 0 else 0.0

        # Return expectancy
        expectancy = (win_rate * avg_winning) + ((1 - win_rate) * avg_losing)

        # Sharpe ratio (annualized)
        returns_std = trades_array.std()
        sharpe = (avg_return / returns_std) * np.sqrt(252 / holding_period) if returns_std > 0 else 0.0

        # Max drawdown
        cumulative = np.cumsum(trades_array)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        max_dd = abs(drawdown.min()) if len(drawdown) > 0 else 0.0

        return BacktestResult(
            composite_threshold=composite_threshold,
            edr_threshold=edr_threshold,
            esv_threshold=esv_threshold,
            total_trades=len(trades_array),
            winning_trades=len(winning_trades),
            win_rate=win_rate,
            avg_return=avg_return,
            avg_winning_return=avg_winning,
            avg_losing_return=avg_losing,
            return_expectancy=expectancy,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
        )

    def optimize_thresholds(
        self,
        df: pd.DataFrame,
        composite_range: Tuple[float, float] = (30, 70),
        edr_range: Tuple[float, float] = (10, 60),
        holding_period: int = 7,
        min_win_rate: float = 0.65,
        min_expectancy: float = 1.0,
    ) -> List[BacktestResult]:
        """
        Grid search to find optimal thresholds

        Returns list of BacktestResults that meet criteria, sorted by return expectancy
        """
        results = []

        # Grid search
        for composite in range(int(composite_range[0]), int(composite_range[1]) + 1, 5):
            for edr in range(int(edr_range[0]), int(edr_range[1]) + 1, 5):
                result = self.backtest_entry_threshold(
                    df=df,
                    composite_threshold=composite,
                    edr_threshold=edr,
                    holding_period=holding_period,
                    require_momentum=True,
                )

                # Filter by criteria
                if (
                    result.total_trades >= 20
                    and result.win_rate >= min_win_rate
                    and result.return_expectancy >= min_expectancy
                ):
                    results.append(result)

        # Sort by return expectancy
        results.sort(key=lambda x: x.return_expectancy, reverse=True)
        return results

    def get_current_signal(
        self,
        symbol: str,
        composite_threshold: float = 35,
        edr_threshold: float = 20,
    ) -> Optional[MAPISignal]:
        """Get current MAPI signal for a symbol"""
        try:
            # Download data
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1y", interval="1d")

            if df.empty:
                return None

            # Prepare data
            df.columns = df.columns.str.lower()
            df = df[['open', 'high', 'low', 'close', 'volume']].copy()

            # Calculate MAPI
            mapi = self.calculator.calculate_mapi(df)
            current = self.calculator.get_current_signal(df)

            # Entry signal
            entry_signal = (
                current['composite_percentile_rank'] >= composite_threshold
                and current['edr_percentile'] >= edr_threshold
                and current['close'] > current['ema20']
                and current['adx'] > 25  # Momentum regime
            )

            # Days since last signal
            signal_days = self._days_since_last_signal(mapi, composite_threshold, edr_threshold)

            # Historical performance
            backtest = self.backtest_entry_threshold(
                df=df,
                composite_threshold=composite_threshold,
                edr_threshold=edr_threshold,
                holding_period=7,
            )

            return MAPISignal(
                symbol=symbol,
                date=str(df.index[-1].date()),
                price=current['close'],
                composite_score=current['composite_score'],
                composite_percentile=current['composite_percentile_rank'],
                edr_percentile=current['edr_percentile'],
                esv_percentile=current['esv_percentile'],
                regime=current['regime'],
                adx=current['adx'],
                distance_to_ema20_pct=current['distance_to_ema20_pct'],
                entry_signal=entry_signal,
                days_since_last_signal=signal_days,
                historical_win_rate=backtest.win_rate,
                historical_avg_return=backtest.avg_return,
                sample_size=backtest.total_trades,
            )

        except Exception as e:
            print(f"Error processing {symbol}: {e}")
            return None

    def _days_since_last_signal(
        self,
        mapi: Dict,
        composite_threshold: float,
        edr_threshold: float,
    ) -> int:
        """Calculate days since last entry signal"""
        composite_signals = mapi['composite_percentile_rank'] >= composite_threshold
        edr_signals = mapi['edr_percentile'] >= edr_threshold
        combined = composite_signals & edr_signals

        if combined.sum() == 0:
            return 999

        last_signal_idx = combined[::-1].idxmax()
        days_ago = len(combined) - combined.index.get_loc(last_signal_idx) - 1
        return days_ago

    def scan_market(
        self,
        symbols: List[str],
        composite_threshold: float = 35,
        edr_threshold: float = 20,
    ) -> List[MAPISignal]:
        """
        Scan market for MAPI entry opportunities

        Args:
            symbols: List of ticker symbols
            composite_threshold: Composite percentile threshold
            edr_threshold: EDR percentile threshold

        Returns:
            List of MAPISignal objects, sorted by composite percentile
        """
        signals = []
        for symbol in symbols:
            signal = self.get_current_signal(symbol, composite_threshold, edr_threshold)
            if signal:
                signals.append(signal)

        # Sort by composite percentile (ascending - lower = better entry)
        signals.sort(key=lambda x: x.composite_percentile)
        return signals
