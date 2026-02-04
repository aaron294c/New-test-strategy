#!/usr/bin/env python3
"""
MACD-V Reference Lookup Utility

Fast lookup utility for MACD-V percentiles and reference data.
Loads precomputed reference database without recalculation.

Usage:
    from macdv_reference_lookup import MACDVReferenceLookup

    lookup = MACDVReferenceLookup()
    info = lookup.get_ticker_info("AAPL")
    print(f"AAPL Mean MACD-V: {info['mean']:.2f}")
    print(f"Current: {info['current']['macdv_val']:.2f} ({info['current']['categorical_percentile']:.1f}%)")
"""

import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime


class MACDVReferenceLookup:
    """
    Fast lookup for precomputed MACD-V reference data.
    """

    def __init__(self, reference_file: Optional[str] = None):
        """
        Initialize lookup with reference database.

        Args:
            reference_file: Path to reference JSON file. If None, uses default location.
        """
        if reference_file is None:
            # Default location
            reference_file = Path(__file__).parent.parent / "docs" / "macdv_reference_database.json"

        self.reference_file = Path(reference_file)

        if not self.reference_file.exists():
            raise FileNotFoundError(
                f"Reference database not found: {self.reference_file}\n"
                f"Run 'python3 precompute_macdv_references.py' to generate it."
            )

        # Load reference database
        with open(self.reference_file, 'r') as f:
            self.database = json.load(f)

        self.metadata = self.database['metadata']
        self.ticker_data = self.database['ticker_data']
        self.aggregate_stats = self.database['aggregate_stats']

    def get_ticker_info(self, ticker: str) -> Optional[Dict]:
        """
        Get complete reference info for a ticker.

        Returns:
            Dictionary with all reference data, or None if ticker not found.
        """
        return self.ticker_data.get(ticker)

    def get_ticker_distribution(self, ticker: str) -> Optional[Dict]:
        """Get overall distribution statistics for a ticker."""
        info = self.get_ticker_info(ticker)
        return info['overall_distribution'] if info else None

    def get_ticker_zone_stats(self, ticker: str, zone: str) -> Optional[Dict]:
        """
        Get zone-specific statistics for a ticker.

        Args:
            ticker: Ticker symbol
            zone: Zone name (e.g., "strong_bullish")

        Returns:
            Zone statistics or None
        """
        info = self.get_ticker_info(ticker)
        if info:
            return info['zone_distribution'].get(zone)
        return None

    def get_current_state(self, ticker: str) -> Optional[Dict]:
        """Get current MACD-V state for a ticker (from last calculation)."""
        info = self.get_ticker_info(ticker)
        return info['current_state'] if info else None

    def get_percentile_interpretation(
        self,
        ticker: str,
        macdv_val: float,
        zone: str,
        cat_percentile: float
    ) -> str:
        """
        Generate human-readable interpretation of MACD-V percentile.

        Args:
            ticker: Ticker symbol
            macdv_val: Current MACD-V value
            zone: Current zone
            cat_percentile: Categorical percentile

        Returns:
            Interpretation string
        """
        zone_label = zone.replace('_', ' ').title()

        # Historical context
        dist = self.get_ticker_distribution(ticker)
        if dist:
            hist_pct = (
                sum(1 for _ in range(int(dist['count']))
                    if macdv_val > dist['mean'])
                / dist['count'] * 100
            )

        # Interpretation based on zone and percentile
        if "bearish" in zone:
            if cat_percentile >= 80:
                strength = "🔄 Strong recovery"
                detail = f"near top of {zone_label} zone"
            elif cat_percentile >= 60:
                strength = "↗️ Recovering"
                detail = f"within {zone_label} zone"
            elif cat_percentile >= 40:
                strength = "➡️ Mid-range"
                detail = f"within {zone_label} zone"
            elif cat_percentile >= 20:
                strength = "↘️ Weakening"
                detail = f"within {zone_label} zone"
            else:
                strength = "⚠️ Extreme weakness"
                detail = f"near bottom of {zone_label} zone"

        elif "bullish" in zone:
            if cat_percentile >= 80:
                strength = "🚀 Very strong"
                detail = f"near top of {zone_label} zone"
            elif cat_percentile >= 60:
                strength = "📈 Strengthening"
                detail = f"within {zone_label} zone"
            elif cat_percentile >= 40:
                strength = "➡️ Mid-range"
                detail = f"within {zone_label} zone"
            elif cat_percentile >= 20:
                strength = "📉 Weakening"
                detail = f"within {zone_label} zone"
            else:
                strength = "⚠️ Near bottom"
                detail = f"weak within {zone_label} zone"
        else:
            strength = "➡️"
            detail = f"{cat_percentile:.0f}% within zone"

        return f"{strength} - {detail}"

    def list_available_tickers(self) -> List[str]:
        """Get list of all available tickers in reference database."""
        return sorted(self.ticker_data.keys())

    def get_metadata(self) -> Dict:
        """Get metadata about the reference database."""
        return self.metadata

    def is_stale(self, max_age_days: int = 7) -> bool:
        """
        Check if reference database is stale.

        Args:
            max_age_days: Maximum age in days before considered stale

        Returns:
            True if database is older than max_age_days
        """
        generated_at = datetime.fromisoformat(self.metadata['generated_at'])
        age = (datetime.now() - generated_at).days
        return age > max_age_days

    def get_comparison_context(self, ticker: str, macdv_val: float) -> Dict:
        """
        Get contextual comparison for a MACD-V value.

        Returns:
            Dictionary with comparison context:
            - percentile_vs_history: Where this value ranks historically
            - distance_from_mean: How far from historical mean
            - zone: Current zone
            - typical_for_zone: Whether this is typical for the zone
        """
        dist = self.get_ticker_distribution(ticker)
        if not dist:
            return {}

        # Calculate percentile vs all history
        percentiles = dist['percentiles']
        global_pct = None
        for pct_val, threshold in sorted(percentiles.items()):
            if macdv_val <= threshold:
                global_pct = pct_val
                break
        if global_pct is None:
            global_pct = 99

        # Distance from mean in standard deviations
        z_score = (macdv_val - dist['mean']) / dist['std']

        # Determine zone
        if macdv_val < -100:
            zone = "extreme_bearish"
        elif macdv_val < -50:
            zone = "strong_bearish"
        elif macdv_val < 50:
            zone = "ranging"
        elif macdv_val < 100:
            zone = "strong_bullish"
        else:
            zone = "extreme_bullish"

        info = self.get_ticker_info(ticker)
        zone_stats = info['zone_distribution'].get(zone, {})
        pct_time_in_zone = zone_stats.get('pct_of_time', 0)

        return {
            'global_percentile': float(global_pct),
            'z_score': float(z_score),
            'distance_from_mean': float(macdv_val - dist['mean']),
            'zone': zone,
            'zone_label': zone.replace('_', ' ').title(),
            'typical_time_in_zone_pct': float(pct_time_in_zone),
            'is_extreme': abs(z_score) > 2.0,
            'is_typical_zone': pct_time_in_zone > 15.0
        }

    def format_ticker_summary(self, ticker: str) -> str:
        """Generate formatted summary for a ticker."""
        info = self.get_ticker_info(ticker)
        if not info:
            return f"{ticker}: No data available"

        dist = info['overall_distribution']
        curr = info['current_state']
        zone_stats = info['zone_distribution']

        summary = f"""
{ticker} - MACD-V Reference Summary
{'='*60}
Historical Distribution ({info['data_points']} data points):
  Mean:   {dist['mean']:7.2f}
  Median: {dist['median']:7.2f}
  Std:    {dist['std']:7.2f}
  Range:  {dist['min']:.1f} to {dist['max']:.1f}

Current State (as of {curr['last_date']}):
  Value:       {curr['macdv_val']:7.2f}
  Zone:        {curr['zone'].replace('_', ' ').title()}
  Percentile:  {curr['categorical_percentile']:.1f}% (within zone)

Time in Each Zone:
"""
        for zone_name in ["extreme_bearish", "strong_bearish", "ranging",
                          "strong_bullish", "extreme_bullish"]:
            zone_data = zone_stats.get(zone_name, {})
            pct_time = zone_data.get('pct_of_time', 0)
            if pct_time > 0:
                zone_label = zone_name.replace('_', ' ').title()
                summary += f"  {zone_label:20s}: {pct_time:5.1f}%\n"

        return summary


# Example usage and testing
if __name__ == "__main__":
    import sys

    lookup = MACDVReferenceLookup()

    print("="*80)
    print("MACD-V REFERENCE LOOKUP - QUICK TEST")
    print("="*80)

    # Show metadata
    meta = lookup.get_metadata()
    print(f"\nDatabase Info:")
    print(f"  Generated: {meta['generated_at']}")
    print(f"  Tickers: {meta['successful']}")
    print(f"  Period: {meta['period']}")

    if lookup.is_stale():
        print(f"  ⚠️  Database is stale (>7 days old)")
    else:
        print(f"  ✓ Database is current")

    # Test with specific ticker or show all
    test_ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"

    if test_ticker == "all":
        print(f"\nAvailable tickers: {', '.join(lookup.list_available_tickers())}")
    else:
        print(f"\n{lookup.format_ticker_summary(test_ticker)}")

        # Show comparison context
        curr = lookup.get_current_state(test_ticker)
        if curr and curr['macdv_val']:
            context = lookup.get_comparison_context(test_ticker, curr['macdv_val'])
            print(f"\nComparison Context:")
            print(f"  Global percentile: {context['global_percentile']:.0f}%")
            print(f"  Z-score: {context['z_score']:.2f}")
            print(f"  Distance from mean: {context['distance_from_mean']:.2f}")
            print(f"  Zone: {context['zone_label']}")
            if context['is_extreme']:
                print(f"  ⚠️  EXTREME value (|z| > 2.0)")

    print("\n" + "="*80)
