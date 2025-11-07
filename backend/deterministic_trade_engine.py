"""
Deterministic Trade Construction Engine

Enforces strict, identical rules for trade generation across all views.
Prevents overlapping signals, handles re-entry suppression, and ensures
exit precedence is deterministic.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from enum import Enum


class ExitReason(Enum):
    """Exit reason enumeration"""
    TARGET_HIT = "target_hit"           # Reached 50th percentile target
    STOP_LOSS = "stop_loss"             # Hit stop loss
    MAX_HOLDING = "max_holding"         # Max holding period reached
    DEAD_ZONE = "dead_zone"             # Moved into dead zone (>50%)
    END_OF_DATA = "end_of_data"         # Data ended while position open


@dataclass
class TradeSignal:
    """Raw entry signal before trade construction"""
    ticker: str
    entry_date: str
    entry_price: float
    entry_percentile: float
    entry_bin: str
    regime: str
    signal_strength: float


@dataclass
class Trade:
    """Constructed trade with entry and exit"""
    ticker: str
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    entry_percentile: float
    exit_percentile: float
    entry_bin: str
    regime: str
    holding_days: int
    return_pct: float
    exit_reason: ExitReason
    stop_loss_pct: float

    def to_dict(self) -> Dict:
        return {
            "ticker": self.ticker,
            "entry_date": self.entry_date,
            "exit_date": self.exit_date,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "entry_percentile": self.entry_percentile,
            "exit_percentile": self.exit_percentile,
            "entry_bin": self.entry_bin,
            "regime": self.regime,
            "holding_days": self.holding_days,
            "return_pct": self.return_pct,
            "exit_reason": self.exit_reason.value,
            "stop_loss_pct": self.stop_loss_pct
        }


@dataclass
class Position:
    """Active position tracking"""
    ticker: str
    entry_date: str
    entry_price: float
    entry_percentile: float
    entry_bin: str
    regime: str
    stop_loss_pct: float
    max_holding_days: int


class DeterministicTradeEngine:
    """
    Deterministic trade construction engine.

    Rules:
    1. No overlapping positions for same ticker
    2. No re-entry on same day after exit
    3. Exit conditions checked in strict order: stop loss, target, max holding
    4. Chronological processing only
    """

    def __init__(
        self,
        allow_overlapping: bool = False,
        allow_same_day_reentry: bool = False,
        max_holding_days: int = 21,
        exit_threshold_percentile: float = 50.0,
        dead_zone_threshold: float = 50.0
    ):
        self.allow_overlapping = allow_overlapping
        self.allow_same_day_reentry = allow_same_day_reentry
        self.max_holding_days = max_holding_days
        self.exit_threshold = exit_threshold_percentile
        self.dead_zone_threshold = dead_zone_threshold

    def construct_trades(
        self,
        signals: List[TradeSignal],
        price_data: Dict[str, Dict[str, float]],  # {ticker: {date: price}}
        percentile_data: Dict[str, Dict[str, float]],  # {ticker: {date: percentile}}
        stop_losses: Dict[str, float]  # {ticker: stop_loss_pct}
    ) -> List[Trade]:
        """
        Construct trades from signals using deterministic rules.

        Parameters:
            signals: List of entry signals (must be chronologically sorted)
            price_data: Price history for exit calculations
            percentile_data: Percentile history for exit conditions
            stop_losses: Stop loss percentage for each ticker

        Returns:
            List of completed trades
        """

        # Group signals by ticker
        signals_by_ticker: Dict[str, List[TradeSignal]] = {}
        for signal in signals:
            if signal.ticker not in signals_by_ticker:
                signals_by_ticker[signal.ticker] = []
            signals_by_ticker[signal.ticker].append(signal)

        # Process each ticker independently
        all_trades = []
        for ticker, ticker_signals in signals_by_ticker.items():
            ticker_trades = self._construct_ticker_trades(
                ticker,
                ticker_signals,
                price_data.get(ticker, {}),
                percentile_data.get(ticker, {}),
                stop_losses.get(ticker, 0.05)  # Default 5% stop
            )
            all_trades.extend(ticker_trades)

        # Sort trades by entry date
        all_trades.sort(key=lambda t: t.entry_date)

        return all_trades

    def _construct_ticker_trades(
        self,
        ticker: str,
        signals: List[TradeSignal],
        prices: Dict[str, float],
        percentiles: Dict[str, float],
        stop_loss_pct: float
    ) -> List[Trade]:
        """Construct trades for a single ticker"""

        trades = []
        position: Optional[Position] = None
        last_exit_date: Optional[str] = None

        # Sort signals chronologically
        sorted_signals = sorted(signals, key=lambda s: s.entry_date)

        for signal in sorted_signals:
            # Rule: If position active, check exit conditions first
            if position is not None:
                exit_result = self._check_exit_conditions(
                    position,
                    signal.entry_date,
                    prices,
                    percentiles
                )

                if exit_result is not None:
                    # Close position
                    trade = exit_result
                    trades.append(trade)
                    last_exit_date = trade.exit_date
                    position = None

            # Rule: Check if we can enter a new position
            if position is None:
                # Rule: No same-day re-entry
                if not self.allow_same_day_reentry and last_exit_date == signal.entry_date:
                    continue

                # Rule: No overlapping positions (already enforced by position=None check)

                # Enter new position
                position = Position(
                    ticker=ticker,
                    entry_date=signal.entry_date,
                    entry_price=signal.entry_price,
                    entry_percentile=signal.entry_percentile,
                    entry_bin=signal.entry_bin,
                    regime=signal.regime,
                    stop_loss_pct=stop_loss_pct,
                    max_holding_days=self.max_holding_days
                )

        # Close any remaining open position at end of data
        if position is not None:
            # Find last available date
            last_date = max(prices.keys())
            exit_trade = Trade(
                ticker=position.ticker,
                entry_date=position.entry_date,
                exit_date=last_date,
                entry_price=position.entry_price,
                exit_price=prices[last_date],
                entry_percentile=position.entry_percentile,
                exit_percentile=percentiles.get(last_date, 50.0),
                entry_bin=position.entry_bin,
                regime=position.regime,
                holding_days=self._calculate_holding_days(position.entry_date, last_date),
                return_pct=(prices[last_date] - position.entry_price) / position.entry_price * 100,
                exit_reason=ExitReason.END_OF_DATA,
                stop_loss_pct=position.stop_loss_pct
            )
            trades.append(exit_trade)

        return trades

    def _check_exit_conditions(
        self,
        position: Position,
        current_date: str,
        prices: Dict[str, float],
        percentiles: Dict[str, float]
    ) -> Optional[Trade]:
        """
        Check exit conditions in strict order:
        1. Stop loss
        2. Target hit (exit threshold)
        3. Dead zone (>50% percentile)
        4. Max holding period
        """

        if current_date not in prices:
            return None

        current_price = prices[current_date]
        current_percentile = percentiles.get(current_date, 50.0)
        holding_days = self._calculate_holding_days(position.entry_date, current_date)
        return_pct = (current_price - position.entry_price) / position.entry_price * 100

        # 1. Check stop loss
        if return_pct <= -position.stop_loss_pct:
            return Trade(
                ticker=position.ticker,
                entry_date=position.entry_date,
                exit_date=current_date,
                entry_price=position.entry_price,
                exit_price=current_price,
                entry_percentile=position.entry_percentile,
                exit_percentile=current_percentile,
                entry_bin=position.entry_bin,
                regime=position.regime,
                holding_days=holding_days,
                return_pct=return_pct,
                exit_reason=ExitReason.STOP_LOSS,
                stop_loss_pct=position.stop_loss_pct
            )

        # 2. Check target hit
        if current_percentile >= self.exit_threshold:
            return Trade(
                ticker=position.ticker,
                entry_date=position.entry_date,
                exit_date=current_date,
                entry_price=position.entry_price,
                exit_price=current_price,
                entry_percentile=position.entry_percentile,
                exit_percentile=current_percentile,
                entry_bin=position.entry_bin,
                regime=position.regime,
                holding_days=holding_days,
                return_pct=return_pct,
                exit_reason=ExitReason.TARGET_HIT,
                stop_loss_pct=position.stop_loss_pct
            )

        # 3. Check dead zone
        if current_percentile > self.dead_zone_threshold:
            return Trade(
                ticker=position.ticker,
                entry_date=position.entry_date,
                exit_date=current_date,
                entry_price=position.entry_price,
                exit_price=current_price,
                entry_percentile=position.entry_percentile,
                exit_percentile=current_percentile,
                entry_bin=position.entry_bin,
                regime=position.regime,
                holding_days=holding_days,
                return_pct=return_pct,
                exit_reason=ExitReason.DEAD_ZONE,
                stop_loss_pct=position.stop_loss_pct
            )

        # 4. Check max holding
        if holding_days >= position.max_holding_days:
            return Trade(
                ticker=position.ticker,
                entry_date=position.entry_date,
                exit_date=current_date,
                entry_price=position.entry_price,
                exit_price=current_price,
                entry_percentile=position.entry_percentile,
                exit_percentile=current_percentile,
                entry_bin=position.entry_bin,
                regime=position.regime,
                holding_days=holding_days,
                return_pct=return_pct,
                exit_reason=ExitReason.MAX_HOLDING,
                stop_loss_pct=position.stop_loss_pct
            )

        return None

    def _calculate_holding_days(self, entry_date: str, exit_date: str) -> int:
        """Calculate holding days between two dates"""
        try:
            entry = datetime.strptime(entry_date, "%Y-%m-%d")
            exit = datetime.strptime(exit_date, "%Y-%m-%d")
            return (exit - entry).days
        except:
            return 1  # Fallback

    def deduplicate_signals(self, signals: List[TradeSignal]) -> List[TradeSignal]:
        """
        Deduplicate overlapping signals per ticker per regime.
        Keep only the earliest signal per ticker per day.
        """
        seen: Dict[Tuple[str, str], TradeSignal] = {}  # (ticker, date) -> signal

        for signal in sorted(signals, key=lambda s: s.entry_date):
            key = (signal.ticker, signal.entry_date)

            if key not in seen:
                seen[key] = signal
            else:
                # If duplicate on same day, keep stronger signal
                if signal.signal_strength > seen[key].signal_strength:
                    seen[key] = signal

        return list(seen.values())
