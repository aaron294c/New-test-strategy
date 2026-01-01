"""
Duration-in-Low-Percentile Analysis for the SWING framework.

This module measures how long trades remain in low percentile zones (≤5%, ≤10%, ≤15%)
after entry, how quickly they escape those zones, and when they first become
profitable. It separates winners vs losers using a 7-day outcome and surfaces
ticker-specific bounce characteristics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

from enhanced_backtester import EnhancedPerformanceMatrixBacktester


# ---------------------------------------------------------------------------
# Helper data structures
# ---------------------------------------------------------------------------

@dataclass
class EventDurationSnapshot:
    """Per-trade duration characteristics for a given entry."""

    entry_date: str
    entry_percentile: float
    is_winner: Optional[bool]
    time_to_first_profit: Optional[int]
    durations: Dict[float, Dict[str, Optional[float]]]


# ---------------------------------------------------------------------------
# Core calculation helpers
# ---------------------------------------------------------------------------

def _basic_stats(values: Sequence[float]) -> Dict[str, Optional[float]]:
    """Return mean/median/p25/p75 for a numeric list."""
    if not values:
        return {"avg": None, "median": None, "p25": None, "p75": None}

    arr = np.array(values, dtype=float)
    return {
        "avg": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "p25": float(np.percentile(arr, 25)),
        "p75": float(np.percentile(arr, 75)),
    }


def _classify_outcome(progression: Dict[int, Dict], outcome_day: int = 7) -> Optional[bool]:
    """Classify winner/loser based on outcome_day cumulative return."""
    if not progression:
        return None

    if outcome_day in progression:
        return progression[outcome_day]["cumulative_return_pct"] > 0

    last_day = max(progression.keys())
    if last_day is None:
        return None
    return progression[last_day]["cumulative_return_pct"] > 0


def _time_to_first_profit(progression: Dict[int, Dict]) -> Optional[int]:
    """Return the first day cumulative return turns positive."""
    for day in sorted(progression.keys()):
        if progression[day]["cumulative_return_pct"] > 0:
            return day
    return None


def _duration_in_low_zone(
    progression: Dict[int, Dict], threshold: float, entry_percentile: float
) -> Tuple[int, Optional[int]]:
    """
    Count consecutive days spent at/below the percentile threshold until escape.

    Only counts if entry_percentile was <= threshold. Otherwise returns (0, None).

    Returns:
    - days_in_low: number of consecutive days <= threshold AFTER entry
    - escape_day: first day percentile rose above threshold (None if never escaped)
    """
    # If entry was above threshold, this trade never qualified for this threshold
    if entry_percentile > threshold:
        return 0, None

    days_in_low = 0
    escape_day: Optional[int] = None

    for day in sorted(progression.keys()):
        percentile = progression[day].get("percentile")
        if pd.isna(percentile):
            continue

        if percentile <= threshold:
            days_in_low += 1
            continue

        escape_day = day
        break

    return days_in_low, escape_day


def _aggregate_group(
    events: List[EventDurationSnapshot], threshold: float
) -> Dict[str, Optional[float]]:
    """Aggregate duration metrics for a group of events at a given threshold."""
    time_in_low = [
        e.durations.get(threshold, {}).get("days_in_low")
        for e in events
        if e.durations.get(threshold, {}).get("days_in_low") is not None
    ]
    escape_days = [
        e.durations.get(threshold, {}).get("escape_day")
        for e in events
        if e.durations.get(threshold, {}).get("escape_day") is not None
    ]
    time_to_profit = [e.time_to_first_profit for e in events if e.time_to_first_profit is not None]

    stats = _basic_stats(time_in_low)
    stats.update(
        {
            "escape_time_avg": float(np.mean(escape_days)) if escape_days else None,
            "escape_rate": float(len(escape_days) / len(events)) if events else None,
            "time_to_first_profit_avg": float(np.mean(time_to_profit)) if time_to_profit else None,
            "time_to_first_profit_median": float(np.median(time_to_profit)) if time_to_profit else None,
            "sample_size": len(events),
        }
    )
    return stats


def _winner_loser_significance(
    winner_samples: List[float], loser_samples: List[float]
) -> Optional[float]:
    """Return Mann-Whitney p-value comparing winner vs loser durations."""
    if len(winner_samples) < 2 or len(loser_samples) < 2:
        return None
    try:
        _, p_value = mannwhitneyu(winner_samples, loser_samples, alternative="two-sided")
        return float(p_value)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_duration_in_low_percentiles(
    ticker: str, threshold: float = 5.0, use_sample_data: bool = False
) -> Dict:
    """
    Analyze time spent in low percentile zones for SWING signals.

    Returns duration metrics for winners vs losers plus ticker-specific
    bounce characteristics.
    """
    # Track standard thresholds plus any caller-provided value
    thresholds_to_track = sorted({5.0, 10.0, 15.0, float(threshold)})
    max_threshold = max(thresholds_to_track)

    backtester = EnhancedPerformanceMatrixBacktester([ticker], max_horizon=21)
    data_source = "live"
    data = backtester.fetch_data(ticker, use_sample_data=use_sample_data)

    if data.empty and not use_sample_data:
        # If live fetch failed, try sample data as fallback
        data = backtester.fetch_data(ticker, use_sample_data=True)
        data_source = "sample" if not data.empty else "live"
    elif use_sample_data:
        data_source = "sample"

    if data.empty:
        raise ValueError(f"No data returned for {ticker} (both live and sample fetch empty)")

    rsi_ma = backtester.calculate_rsi_ma_indicator(data)
    percentile_ranks = backtester.calculate_percentile_ranks(rsi_ma)

    # Collect all entries up to the widest threshold, then filter per threshold later
    entry_events = backtester.find_entry_events_enhanced(
        percentile_ranks, data["Close"], threshold=max_threshold
    )

    print(f"Found {len(entry_events)} total entry events for {ticker}")

    duration_snapshots: List[EventDurationSnapshot] = []
    for idx, event in enumerate(entry_events):
        progression = event.get("progression", {})
        outcome = _classify_outcome(progression, outcome_day=7)
        time_to_profit = _time_to_first_profit(progression)

        # DEBUG: First 5 events
        if idx < 5:
            day7_return = progression.get(7, {}).get("cumulative_return_pct", "N/A")
            print(f"Event {idx}: entry_pct={event.get('entry_percentile', 0):.1f}%, day7_return={day7_return}, outcome={outcome}")

        entry_pct = float(event.get("entry_percentile", 0))

        per_threshold: Dict[float, Dict[str, Optional[float]]] = {}
        for th in thresholds_to_track:
            days_in_low, escape_day = _duration_in_low_zone(progression, th, entry_pct)
            per_threshold[th] = {
                "days_in_low": days_in_low,
                "escape_day": escape_day,
            }

        entry_date = event.get("entry_date")
        entry_date_str = (
            entry_date.strftime("%Y-%m-%d") if hasattr(entry_date, "strftime") else str(entry_date)
        )
        duration_snapshots.append(
            EventDurationSnapshot(
                entry_date=entry_date_str,
                entry_percentile=entry_pct,
                is_winner=bool(outcome) if outcome is not None else None,
                time_to_first_profit=time_to_profit,
                durations=per_threshold,
            )
        )

    # Filter events at the caller's base threshold (default 5%)
    scoped_events = [e for e in duration_snapshots if e.entry_percentile <= threshold]
    winners = [e for e in scoped_events if e.is_winner]
    losers = [e for e in scoped_events if e.is_winner is False]

    # DEBUG: Detailed analysis for winners vs losers
    print(f"\n=== DETAILED DEBUG: {ticker} at threshold={threshold}% ===")
    print(f"Scoped events: {len(scoped_events)}, Winners: {len(winners)}, Losers: {len(losers)}")

    if winners:
        print(f"\nFirst 3 WINNERS:")
        for i, w in enumerate(winners[:3]):
            days_low = w.durations.get(threshold, {}).get("days_in_low")
            escape = w.durations.get(threshold, {}).get("escape_day")
            print(f"  [{i+1}] entry={w.entry_percentile:.1f}%, days_in_low={days_low}, escape_day={escape}, profit_day={w.time_to_first_profit}")

    if losers:
        print(f"\nFirst 3 LOSERS:")
        for i, l in enumerate(losers[:3]):
            days_low = l.durations.get(threshold, {}).get("days_in_low")
            escape = l.durations.get(threshold, {}).get("escape_day")
            print(f"  [{i+1}] entry={l.entry_percentile:.1f}%, days_in_low={days_low}, escape_day={escape}, profit_day={l.time_to_first_profit}")

    # Winner vs loser time-in-low comparison at the base threshold
    winner_time_low = [
        e.durations[threshold]["days_in_low"]
        for e in winners
        if e.durations.get(threshold, {}).get("days_in_low") is not None
    ]
    loser_time_low = [
        e.durations[threshold]["days_in_low"]
        for e in losers
        if e.durations.get(threshold, {}).get("days_in_low") is not None
    ]

    # DEBUG: Show the actual values being aggregated
    print(f"\nWinner days_in_low ALL: {winner_time_low}")
    print(f"Loser days_in_low ALL: {loser_time_low}")
    print(f"Winner avg: {np.mean(winner_time_low) if winner_time_low else None}")
    print(f"Loser avg: {np.mean(loser_time_low) if loser_time_low else None}")
    print(f"Winner sum: {sum(winner_time_low)}, count: {len(winner_time_low)}")
    print(f"Loser sum: {sum(loser_time_low)}, count: {len(loser_time_low)}")

    p_value = _winner_loser_significance(winner_time_low, loser_time_low)

    per_threshold_summary: Dict[str, Dict[str, Optional[float]]] = {}
    for th in thresholds_to_track:
        key = f"{th:g}"  # normalize (5.0 -> "5")
        # Filter events where entry_percentile <= th (events that would trigger at this threshold)
        threshold_events = [e for e in duration_snapshots if e.entry_percentile <= th]
        per_threshold_summary[key] = _aggregate_group(threshold_events, th)

    # Build ticker bounce profile heuristics
    median_escape = _basic_stats(winner_time_low).get("median")
    if median_escape is None:
        bounce_profile = "unknown"
    elif median_escape <= 2:
        bounce_profile = "fast_bouncer"
    elif median_escape <= 4:
        bounce_profile = "balanced"
    else:
        bounce_profile = "slow_bouncer"

    stagnation_rate = (
        float(
            sum(1 for e in losers if e.durations[threshold]["escape_day"] is None)
            / len(losers)
        )
        if losers
        else None
    )

    return {
        "ticker": ticker.upper(),
        "threshold": float(threshold),
        "sample_size": len(scoped_events),
        "thresholds_tracked": thresholds_to_track,
        "winners": _aggregate_group(winners, threshold),
        "losers": _aggregate_group(losers, threshold),
        "comparison": {
            "winner_vs_loser_ratio": float(np.mean(winner_time_low) / np.mean(loser_time_low))
            if winner_time_low and loser_time_low and np.mean(loser_time_low) != 0
            else None,
            "stagnation_rate": stagnation_rate,
            "statistical_significance_p": p_value,
            "predictive_value": "high" if p_value is not None and p_value < 0.05 else "inconclusive",
        },
        "per_threshold": per_threshold_summary,
        "ticker_profile": {
            "bounce_speed": bounce_profile,
            "median_escape_time_winners": median_escape,
            "median_time_to_first_profit": _aggregate_group(scoped_events, threshold).get(
                "time_to_first_profit_median"
            ),
            "recommendation": (
                "Requires patience (>4 days) before typical bounce"
                if bounce_profile == "slow_bouncer"
                else "Bounces quickly, monitor intraday"
                if bounce_profile == "fast_bouncer"
                else "Balanced behavior; use 3-4 day patience window"
            ),
        },
        "metadata": {
            "max_horizon": backtester.max_horizon,
            "outcome_day": 7,
            "event_count_all_thresholds": len(duration_snapshots),
            "data_source": data_source,
        },
        "raw_events": _sanitize_raw_events(scoped_events),
    }


def _sanitize_raw_events(events: List[EventDurationSnapshot]) -> List[Dict]:
    """Convert numpy types to native Python for JSON serialization."""
    sanitized = []
    for e in events:
        durations: Dict[float, Dict[str, Optional[int]]] = {}
        for th, vals in e.durations.items():
            durations[float(th)] = {
                "days_in_low": int(vals.get("days_in_low")) if vals.get("days_in_low") is not None else None,
                "escape_day": int(vals.get("escape_day")) if vals.get("escape_day") is not None else None,
            }

        sanitized.append(
            {
                "entry_date": e.entry_date,
                "entry_percentile": float(e.entry_percentile),
                "is_winner": bool(e.is_winner) if e.is_winner is not None else None,
                "time_to_first_profit": int(e.time_to_first_profit) if e.time_to_first_profit is not None else None,
                "durations": durations,
            }
        )
    return sanitized
