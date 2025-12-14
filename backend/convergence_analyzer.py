#!/usr/bin/env python3
"""
Divergence-Convergence Framework Analyzer

Analyzes time-to-convergence following overextension events between
daily and 4-hour RSI-MA percentiles.

IMPORTANT:
This module now uses `MultiTimeframeAnalyzer` (the same logic behind the
Multi-Timeframe Divergence UI) as its source of truth for:
- RSI-MA calculation pipeline
- Daily vs 4H percentile lookback alignment (252 daily bars vs ~410 4H bars)
- Divergence sign convention (Daily - 4H)

Core Concept:
- Convergence Event: Both percentiles moving toward alignment (small divergence)
- Overextension Event: One timeframe deviates significantly from the other
- Mid-Cycle Analysis: Quantify oscillating divergence between entry/exit signals

Key Metrics:
- Average time to convergence after overextension
- Direction impact (4H > daily vs. 4H < daily)
- Magnitude correlation with convergence time
- Stability window estimation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import timedelta

from multi_timeframe_analyzer import MultiTimeframeAnalyzer

@dataclass
class OverextensionEvent:
    """Single overextension event with convergence tracking."""
    date: str
    daily_percentile: float
    hourly_4h_percentile: float
    divergence_pct: float
    divergence_direction: str  # '4h_high' or '4h_low'
    price_at_overextension: float

    # Convergence metrics
    time_to_convergence_hours: Optional[int] = None
    converged_within_window: bool = False
    convergence_date: Optional[str] = None
    price_at_convergence: Optional[float] = None
    return_during_convergence: float = 0.0

    # Path characteristics
    max_divergence_during_convergence: float = 0.0
    oscillation_count: int = 0  # Number of direction changes


@dataclass
class ConvergenceStatistics:
    """Statistical summary of convergence patterns."""

    # Overall statistics
    total_overextension_events: int
    events_that_converged: int
    convergence_rate: float

    # Time-to-convergence
    median_hours_to_convergence: float
    mean_hours_to_convergence: float
    p25_hours: float
    p75_hours: float

    # By direction
    convergence_stats_by_direction: Dict[str, Dict]

    # By magnitude
    convergence_stats_by_magnitude: Dict[str, Dict]

    # Stability window
    stability_window_hours: Tuple[float, float]  # (min, max) for 80% of events

    # Predictive insights
    correlation_magnitude_vs_time: float
    optimal_divergence_threshold: float


class ConvergenceAnalyzer:
    """
    Analyzes convergence patterns between daily and 4-hour RSI-MA percentiles.
    """

    def __init__(self,
                 ticker: str,
                 convergence_threshold: float = 10.0,
                 overextension_threshold: float = 25.0,
                 max_convergence_window_hours: int = 168):  # 1 week
        """
        Initialize convergence analyzer.

        Args:
            ticker: Stock ticker symbol
            convergence_threshold: Divergence % below which is considered "converged"
            overextension_threshold: Divergence % above which is "overextended"
            max_convergence_window_hours: Maximum time to look for convergence
        """
        self.ticker = ticker
        self.convergence_threshold = convergence_threshold
        self.overextension_threshold = overextension_threshold
        self.max_window = max_convergence_window_hours

        # Source-of-truth aligned daily + 4H percentiles (same as multi-timeframe divergence UI)
        self.mtf = MultiTimeframeAnalyzer(self.ticker)
        self.daily_percentiles = self.mtf.daily_percentiles
        self.percentiles_4h = self.mtf.percentiles_4h
        self.data_4h = self.mtf.data_4h

        # Align timeframes on 4H bars (convergence analysis needs intraday resolution)
        self.aligned_data = self._align_timeframes_on_4h()

    def _daily_percentile_for_timestamp(self, ts: pd.Timestamp) -> Optional[float]:
        """Get the latest available daily percentile for the timestamp's date."""
        if self.daily_percentiles is None or self.daily_percentiles.empty:
            return None
        key = pd.Timestamp(ts.date())
        try:
            if key in self.daily_percentiles.index:
                value = self.daily_percentiles.loc[key]
                return float(value) if pd.notna(value) else None
            # Fallback: last daily value on/preceding this date
            prior = self.daily_percentiles.loc[:key].dropna()
            if prior.empty:
                return None
            return float(prior.iloc[-1])
        except Exception:
            return None

    def _align_timeframes_on_4h(self) -> pd.DataFrame:
        """
        Build an intraday (4H bar) aligned table:
        - daily_percentile: daily RSI-MA percentile for that date
        - 4h_percentile: 4H RSI-MA percentile at that bar
        - divergence_pct: Daily - 4H (matches MultiTimeframeAnalyzer convention)
        """
        aligned: List[Dict] = []

        if self.percentiles_4h is None or self.percentiles_4h.empty:
            return pd.DataFrame(aligned)

        for ts, pct_4h in self.percentiles_4h.dropna().items():
            daily_pct = self._daily_percentile_for_timestamp(pd.Timestamp(ts))
            if daily_pct is None or pd.isna(pct_4h):
                continue

            if ts not in self.data_4h.index:
                continue

            price = self.data_4h.loc[ts, "Close"]
            if pd.isna(price):
                continue

            divergence = float(daily_pct - float(pct_4h))
            aligned.append({
                "datetime": pd.Timestamp(ts),
                "date": pd.Timestamp(ts).date(),
                "daily_percentile": float(daily_pct),
                "4h_percentile": float(pct_4h),
                "divergence_pct": divergence,
                "price": float(price),
            })

        return pd.DataFrame(aligned)

    def detect_overextension_events(self) -> List[OverextensionEvent]:
        """
        Detect overextension events where divergence exceeds threshold.
        """
        events = []

        for i in range(len(self.aligned_data)):
            row = self.aligned_data.iloc[i]

            abs_divergence = abs(row['divergence_pct'])

            if abs_divergence >= self.overextension_threshold:
                # Divergence convention: Daily - 4H
                # Negative divergence => 4H above daily ("4h_high")
                direction = '4h_high' if row['divergence_pct'] < 0 else '4h_low'

                event = OverextensionEvent(
                    date=row['datetime'].strftime('%Y-%m-%d %H:%M'),
                    daily_percentile=row['daily_percentile'],
                    hourly_4h_percentile=row['4h_percentile'],
                    divergence_pct=row['divergence_pct'],
                    divergence_direction=direction,
                    price_at_overextension=row['price']
                )

                # Look forward for convergence
                self._track_convergence(event, i)

                events.append(event)

        return events

    def _track_convergence(self, event: OverextensionEvent, start_idx: int):
        """
        Track forward from overextension event to find convergence.
        """
        max_bars = self.max_window // 4  # 4-hour bars

        max_div = abs(event.divergence_pct)
        oscillations = 0
        prev_sign = np.sign(event.divergence_pct)

        for offset in range(1, min(max_bars, len(self.aligned_data) - start_idx)):
            future_row = self.aligned_data.iloc[start_idx + offset]

            current_divergence = future_row['divergence_pct']
            abs_div = abs(current_divergence)

            # Track max divergence
            if abs_div > max_div:
                max_div = abs_div

            # Track oscillations (sign changes)
            current_sign = np.sign(current_divergence)
            if current_sign != prev_sign and current_sign != 0:
                oscillations += 1
            prev_sign = current_sign

            # Check for convergence
            if abs_div <= self.convergence_threshold:
                hours_elapsed = offset * 4

                event.time_to_convergence_hours = hours_elapsed
                event.converged_within_window = True
                event.convergence_date = future_row['datetime'].strftime('%Y-%m-%d %H:%M')
                event.price_at_convergence = future_row['price']
                event.return_during_convergence = (
                    (future_row['price'] - event.price_at_overextension) /
                    event.price_at_overextension * 100
                )
                event.max_divergence_during_convergence = max_div
                event.oscillation_count = oscillations

                break

    def calculate_convergence_statistics(self, events: List[OverextensionEvent]) -> ConvergenceStatistics:
        """
        Calculate statistical summary of convergence patterns.
        """
        if not events:
            return ConvergenceStatistics(
                total_overextension_events=0,
                events_that_converged=0,
                convergence_rate=0.0,
                median_hours_to_convergence=0.0,
                mean_hours_to_convergence=0.0,
                p25_hours=0.0,
                p75_hours=0.0,
                convergence_stats_by_direction={},
                convergence_stats_by_magnitude={},
                stability_window_hours=(0.0, 0.0),
                correlation_magnitude_vs_time=0.0,
                optimal_divergence_threshold=0.0
            )

        converged_events = [e for e in events if e.converged_within_window]
        convergence_rate = len(converged_events) / len(events)

        # Time statistics
        times = [e.time_to_convergence_hours for e in converged_events]

        if times:
            median_time = np.median(times)
            mean_time = np.mean(times)
            p25 = np.percentile(times, 25)
            p75 = np.percentile(times, 75)

            # Stability window (10th to 90th percentile)
            p10 = np.percentile(times, 10)
            p90 = np.percentile(times, 90)
            stability_window = (p10, p90)
        else:
            median_time = mean_time = p25 = p75 = 0.0
            stability_window = (0.0, 0.0)

        # By direction
        direction_stats = {}
        for direction in ['4h_high', '4h_low']:
            dir_events = [e for e in converged_events if e.divergence_direction == direction]
            if dir_events:
                dir_times = [e.time_to_convergence_hours for e in dir_events]
                direction_stats[direction] = {
                    'count': len(dir_events),
                    'convergence_rate': len(dir_events) / len([e for e in events if e.divergence_direction == direction]),
                    'median_hours': np.median(dir_times),
                    'mean_hours': np.mean(dir_times)
                }

        # By magnitude (bins)
        magnitude_stats = {}
        magnitude_bins = [(25, 35), (35, 50), (50, 75), (75, 100)]

        for min_mag, max_mag in magnitude_bins:
            mag_events = [e for e in converged_events
                         if min_mag <= abs(e.divergence_pct) < max_mag]
            if mag_events:
                mag_times = [e.time_to_convergence_hours for e in mag_events]
                magnitude_stats[f"{min_mag}-{max_mag}%"] = {
                    'count': len(mag_events),
                    'median_hours': np.median(mag_times),
                    'mean_hours': np.mean(mag_times)
                }

        # Correlation between magnitude and time
        if converged_events:
            magnitudes = [abs(e.divergence_pct) for e in converged_events]
            conv_times = [e.time_to_convergence_hours for e in converged_events]

            if len(magnitudes) > 1:
                correlation = np.corrcoef(magnitudes, conv_times)[0, 1]
            else:
                correlation = 0.0
        else:
            correlation = 0.0

        return ConvergenceStatistics(
            total_overextension_events=len(events),
            events_that_converged=len(converged_events),
            convergence_rate=convergence_rate,
            median_hours_to_convergence=median_time,
            mean_hours_to_convergence=mean_time,
            p25_hours=p25,
            p75_hours=p75,
            convergence_stats_by_direction=direction_stats,
            convergence_stats_by_magnitude=magnitude_stats,
            stability_window_hours=stability_window,
            correlation_magnitude_vs_time=correlation,
            optimal_divergence_threshold=self.overextension_threshold
        )

    def generate_convergence_prediction(self, current_divergence: float,
                                       direction: str) -> Dict:
        """
        Predict convergence time for current market state.

        Args:
            current_divergence: Current divergence percentage
            direction: '4h_high' or '4h_low'

        Returns:
            Prediction with estimated convergence time and confidence
        """
        events = self.detect_overextension_events()
        stats = self.calculate_convergence_statistics(events)

        # Find similar historical events
        similar_events = [
            e for e in events
            if e.converged_within_window
            and e.divergence_direction == direction
            and abs(abs(e.divergence_pct) - abs(current_divergence)) < 15
        ]

        if similar_events:
            similar_times = [e.time_to_convergence_hours for e in similar_events]
            predicted_hours = np.median(similar_times)
            confidence = min(len(similar_events) / 10, 1.0)  # Max confidence at 10+ events
        else:
            # Fallback to direction average
            if direction in stats.convergence_stats_by_direction:
                predicted_hours = stats.convergence_stats_by_direction[direction]['median_hours']
                confidence = 0.5
            else:
                predicted_hours = stats.median_hours_to_convergence
                confidence = 0.3

        return {
            'predicted_hours_to_convergence': predicted_hours,
            'confidence': confidence,
            'similar_historical_events': len(similar_events),
            'convergence_probability': stats.convergence_rate,
            'stability_window_hours': stats.stability_window_hours,
            'expected_oscillations': int(np.mean([e.oscillation_count for e in similar_events])) if similar_events else 0
        }

    def run_full_analysis(self) -> Dict:
        """
        Run complete convergence analysis.
        """
        events = self.detect_overextension_events()
        stats = self.calculate_convergence_statistics(events)

        # Current state analysis
        if len(self.aligned_data) > 0:
            current_row = self.aligned_data.iloc[-1]
            current_divergence = current_row['divergence_pct']
            current_direction = '4h_high' if current_divergence < 0 else '4h_low'

            is_overextended = abs(current_divergence) >= self.overextension_threshold

            if is_overextended:
                prediction = self.generate_convergence_prediction(
                    current_divergence, current_direction
                )
            else:
                prediction = None
        else:
            current_divergence = 0
            current_direction = 'neutral'
            is_overextended = False
            prediction = None

        return {
            'ticker': self.ticker,
            'analysis_parameters': {
                'convergence_threshold': self.convergence_threshold,
                'overextension_threshold': self.overextension_threshold,
                'max_convergence_window_hours': self.max_window
            },
            'current_state': {
                'current_divergence_pct': float(current_divergence) if current_divergence is not None else 0,
                'direction': current_direction,
                'is_overextended': is_overextended,
                'prediction': prediction
            },
            'historical_statistics': asdict(stats),
            'overextension_events': [asdict(e) for e in events[-20:]],  # Last 20 events
            'insights': self._generate_insights(stats, events)
        }

    def _generate_insights(self, stats: ConvergenceStatistics,
                          events: List[OverextensionEvent]) -> List[str]:
        """Generate actionable insights from convergence analysis."""
        insights = []

        # Convergence rate insight
        if stats.convergence_rate > 0.8:
            insights.append(
                f"High convergence reliability: {stats.convergence_rate*100:.1f}% of overextension events converge within {self.max_window} hours"
            )
        elif stats.convergence_rate < 0.5:
            insights.append(
                f"Low convergence rate: Only {stats.convergence_rate*100:.1f}% converge. Consider using longer timeframes or different thresholds"
            )

        # Time window insight
        if stats.median_hours_to_convergence > 0:
            insights.append(
                f"Typical convergence time: {stats.median_hours_to_convergence:.0f} hours (median), with 50% occurring between {stats.p25_hours:.0f}-{stats.p75_hours:.0f} hours"
            )

        # Direction asymmetry
        if '4h_high' in stats.convergence_stats_by_direction and '4h_low' in stats.convergence_stats_by_direction:
            high_time = stats.convergence_stats_by_direction['4h_high']['median_hours']
            low_time = stats.convergence_stats_by_direction['4h_low']['median_hours']

            if high_time > low_time * 1.3:
                insights.append(
                    f"4H-high overextensions take longer to converge ({high_time:.0f}h) vs 4H-low ({low_time:.0f}h)"
                )
            elif low_time > high_time * 1.3:
                insights.append(
                    f"4H-low overextensions take longer to converge ({low_time:.0f}h) vs 4H-high ({high_time:.0f}h)"
                )

        # Magnitude correlation
        if abs(stats.correlation_magnitude_vs_time) > 0.3:
            if stats.correlation_magnitude_vs_time > 0:
                insights.append(
                    f"Larger divergences take longer to converge (correlation: {stats.correlation_magnitude_vs_time:.2f})"
                )
            else:
                insights.append(
                    f"Larger divergences converge faster (correlation: {stats.correlation_magnitude_vs_time:.2f})"
                )

        return insights


def analyze_convergence_for_ticker(ticker: str) -> Dict:
    """
    Main function to analyze convergence patterns for a ticker.
    """
    analyzer = ConvergenceAnalyzer(
        ticker=ticker,
        convergence_threshold=10.0,
        overextension_threshold=25.0,
        max_convergence_window_hours=168
    )

    return analyzer.run_full_analysis()


if __name__ == "__main__":
    # Example usage
    result = analyze_convergence_for_ticker("AAPL")

    import json
    print(json.dumps(result, indent=2, default=str))
