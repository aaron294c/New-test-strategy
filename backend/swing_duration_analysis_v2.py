"""
SWING Duration-in-Low-Percentile Analysis (v2 - Clean Implementation)

Answers the core question: How long do trades stay in low percentile zones?

For winners vs losers at 7-day outcome:
- Time spent ≤ 5%, ≤ 10%, ≤ 15% percentile after entry
- Time until percentile escapes above threshold
- Time until price first becomes profitable
- Ticker-specific bounce characteristics
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

from enhanced_backtester import EnhancedPerformanceMatrixBacktester


@dataclass
class TradeOutcome:
    """Single trade outcome with duration metrics."""
    entry_date: str
    entry_percentile: float
    is_winner: bool  # True if Day-7 return > 0
    time_to_first_profit_days: Optional[int]  # Days until price > entry

    # Per-threshold duration metrics
    days_below_5pct: int
    days_below_10pct: int
    days_below_15pct: int

    escape_day_5pct: Optional[int]
    escape_day_10pct: Optional[int]
    escape_day_15pct: Optional[int]


def _calculate_time_to_first_profit(progression: Dict[int, Dict]) -> Optional[int]:
    """Return first day where cumulative return > 0."""
    for day in sorted(progression.keys()):
        if progression[day]["cumulative_return_pct"] > 0:
            return day
    return None


def _calculate_days_below_threshold(progression: Dict[int, Dict], threshold: float) -> tuple[int, Optional[int]]:
    """
    Count consecutive days where percentile ≤ threshold, starting from Day 1.

    Returns:
        (days_below, escape_day)
        - days_below: number of consecutive days at or below threshold
        - escape_day: first day percentile rose above threshold (None if never escaped)
    """
    days_below = 0
    escape_day = None

    for day in sorted(progression.keys()):
        pct = progression[day].get("percentile")
        if pd.isna(pct):
            break  # Stop if we hit missing data

        if pct <= threshold:
            days_below += 1
        else:
            escape_day = day
            break

    return days_below, escape_day


def analyze_swing_duration_v2(
    ticker: str,
    entry_threshold: float = 5.0,
    use_sample_data: bool = False
) -> Dict:
    """
    Clean implementation of SWING duration analysis.

    Measures how long trades remain in low percentile zones (≤5%, ≤10%, ≤15%)
    and compares winners vs losers.

    Args:
        ticker: Stock symbol
        entry_threshold: Maximum entry percentile (default 5%)
        use_sample_data: Use sample data instead of live fetch

    Returns:
        Dict with winner/loser duration metrics and ticker profile
    """
    # Initialize backtester
    backtester = EnhancedPerformanceMatrixBacktester([ticker], max_horizon=21)

    # Fetch data
    data = backtester.fetch_data(ticker, use_sample_data=use_sample_data)
    if data.empty and not use_sample_data:
        data = backtester.fetch_data(ticker, use_sample_data=True)
        data_source = "sample"
    elif use_sample_data:
        data_source = "sample"
    else:
        data_source = "live"

    if data.empty:
        raise ValueError(f"No data for {ticker}")

    # Calculate RSI-MA and percentiles
    rsi_ma = backtester.calculate_rsi_ma_indicator(data)
    percentile_ranks = backtester.calculate_percentile_ranks(rsi_ma)

    # Find entry events at the specified threshold
    entry_events = backtester.find_entry_events_enhanced(
        percentile_ranks, data["Close"], threshold=entry_threshold
    )

    # Process each event
    trades: List[TradeOutcome] = []

    for event in entry_events:
        progression = event.get("progression", {})
        if not progression:
            continue

        # Classify winner/loser based on Day-7 return
        day7_return = None
        if 7 in progression:
            day7_return = progression[7]["cumulative_return_pct"]
        elif progression:
            last_day = max(progression.keys())
            day7_return = progression[last_day]["cumulative_return_pct"]

        if day7_return is None:
            continue

        is_winner = day7_return > 0

        # Calculate duration metrics
        time_to_profit = _calculate_time_to_first_profit(progression)

        days_5, escape_5 = _calculate_days_below_threshold(progression, 5.0)
        days_10, escape_10 = _calculate_days_below_threshold(progression, 10.0)
        days_15, escape_15 = _calculate_days_below_threshold(progression, 15.0)

        # Create trade outcome
        entry_date = event.get("entry_date")
        entry_date_str = entry_date.strftime("%Y-%m-%d") if hasattr(entry_date, "strftime") else str(entry_date)

        trades.append(TradeOutcome(
            entry_date=entry_date_str,
            entry_percentile=float(event.get("entry_percentile", 0)),
            is_winner=is_winner,
            time_to_first_profit_days=time_to_profit,
            days_below_5pct=days_5,
            days_below_10pct=days_10,
            days_below_15pct=days_15,
            escape_day_5pct=escape_5,
            escape_day_10pct=escape_10,
            escape_day_15pct=escape_15,
        ))

    # Separate winners and losers
    winners = [t for t in trades if t.is_winner]
    losers = [t for t in trades if not t.is_winner]

    # Aggregate statistics
    def get_stats(trades_list: List[TradeOutcome], threshold_pct: int) -> Dict:
        """Calculate aggregate statistics for a threshold."""
        if not trades_list:
            return {
                "sample_size": 0,
                "avg_days_in_low": None,
                "median_days_in_low": None,
                "p25_days": None,
                "p75_days": None,
                "avg_escape_time": None,
                "escape_rate": None,
                "avg_time_to_profit": None,
                "median_time_to_profit": None,
            }

        # Get the appropriate field based on threshold
        if threshold_pct == 5:
            days_in_low = [t.days_below_5pct for t in trades_list]
            escape_days = [t.escape_day_5pct for t in trades_list if t.escape_day_5pct is not None]
        elif threshold_pct == 10:
            days_in_low = [t.days_below_10pct for t in trades_list]
            escape_days = [t.escape_day_10pct for t in trades_list if t.escape_day_10pct is not None]
        else:  # 15
            days_in_low = [t.days_below_15pct for t in trades_list]
            escape_days = [t.escape_day_15pct for t in trades_list if t.escape_day_15pct is not None]

        profit_days = [t.time_to_first_profit_days for t in trades_list if t.time_to_first_profit_days is not None]

        return {
            "sample_size": len(trades_list),
            "avg_days_in_low": float(np.mean(days_in_low)) if days_in_low else None,
            "median_days_in_low": float(np.median(days_in_low)) if days_in_low else None,
            "p25_days": float(np.percentile(days_in_low, 25)) if days_in_low else None,
            "p75_days": float(np.percentile(days_in_low, 75)) if days_in_low else None,
            "avg_escape_time": float(np.mean(escape_days)) if escape_days else None,
            "escape_rate": float(len(escape_days) / len(trades_list)) if trades_list else None,
            "avg_time_to_profit": float(np.mean(profit_days)) if profit_days else None,
            "median_time_to_profit": float(np.median(profit_days)) if profit_days else None,
        }

    # Calculate for each threshold
    results = {
        "ticker": ticker.upper(),
        "entry_threshold": float(entry_threshold),
        "sample_size": len(trades),
        "data_source": data_source,

        "winners": {
            "count": len(winners),
            "threshold_5pct": get_stats(winners, 5),
            "threshold_10pct": get_stats(winners, 10),
            "threshold_15pct": get_stats(winners, 15),
        },

        "losers": {
            "count": len(losers),
            "threshold_5pct": get_stats(losers, 5),
            "threshold_10pct": get_stats(losers, 10),
            "threshold_15pct": get_stats(losers, 15),
        },
    }

    # Winner vs Loser comparison (using 5% threshold as baseline)
    winner_days_5 = [t.days_below_5pct for t in winners]
    loser_days_5 = [t.days_below_5pct for t in losers]

    p_value = None
    if len(winner_days_5) >= 2 and len(loser_days_5) >= 2:
        try:
            _, p_value = mannwhitneyu(winner_days_5, loser_days_5, alternative="two-sided")
            p_value = float(p_value)
        except:
            pass

    results["comparison"] = {
        "statistical_significance_p": p_value,
        "predictive_value": "high" if p_value and p_value < 0.05 else "inconclusive",
        "winner_vs_loser_ratio_5pct": (
            float(np.mean(winner_days_5) / np.mean(loser_days_5))
            if winner_days_5 and loser_days_5 and np.mean(loser_days_5) != 0
            else None
        ),
    }

    # Ticker bounce profile
    winner_escape_5 = [t.escape_day_5pct for t in winners if t.escape_day_5pct is not None]
    median_escape = float(np.median(winner_escape_5)) if winner_escape_5 else None

    if median_escape is None:
        bounce_profile = "unknown"
    elif median_escape <= 2:
        bounce_profile = "fast_bouncer"
    elif median_escape <= 4:
        bounce_profile = "balanced"
    else:
        bounce_profile = "slow_bouncer"

    results["ticker_profile"] = {
        "bounce_speed": bounce_profile,
        "median_escape_time_winners": median_escape,
        "recommendation": (
            "Bounces quickly, monitor intraday" if bounce_profile == "fast_bouncer"
            else "Balanced behavior; use 3-4 day patience window" if bounce_profile == "balanced"
            else "Requires patience (>4 days) before typical bounce"
        ),
    }

    return results
