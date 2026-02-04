#!/usr/bin/env python3
"""
Live MACD-V Percentiles Calculator

Calculates current MACD-V values with categorical and asymmetric percentiles
for the live market state table.

Output includes:
- Current MACD-V value
- Zone classification
- Categorical percentile (within zone)
- Asymmetric percentile (within bull/bear regime)
- Interpretation
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
from typing import Dict, List, Tuple

try:
    from macdv_percentile_calculator import MACDVPercentileCalculator
except ModuleNotFoundError:
    from backend.macdv_percentile_calculator import MACDVPercentileCalculator  # type: ignore


# Tickers from your live table
LIVE_TICKERS = [
    "SLV", "MSFT", "NVDA", "BTC-USD", "NFLX", "UNH", "LLY",
    "QQQ", "NQ=F", "SPY", "AAPL", "GOOGL", "META", "AMZN",
    "BRK-B", "WMT", "AVGO", "TSM", "ORCL", "OXY", "XOM",
    "CVX", "JPM", "BAC", "ES=F", "^VIX", "DX-Y.NYB", "^TNX", "XLI"
]


def get_zone_description(zone: str) -> Tuple[str, str]:
    """Get human-readable zone description and regime."""
    zone_info = {
        "extreme_bearish": ("< -100", "Strong Downtrend"),
        "strong_bearish": ("-100 to -50", "Downtrend"),
        "ranging": ("-50 to +50", "Mean Reversion / Consolidation"),
        "strong_bullish": ("+50 to +100", "Uptrend"),
        "extreme_bullish": ("> +100", "Strong Uptrend"),
    }
    return zone_info.get(zone, ("Unknown", "Unknown"))


def interpret_percentile(zone: str, percentile: float) -> str:
    """
    Interpret what the percentile means in context of the zone.

    Higher percentile in bearish zones = recovering (bullish)
    Higher percentile in ranging zone = overbought (mean revert down)
    Higher percentile in bullish zones = strengthening (bullish)
    """
    if zone == "ranging":
        # In ranging zone, high percentile = overbought, low = oversold
        if percentile >= 80:
            return f"⚠️ Overbought ({percentile:.0f}% - near top of range, likely revert down)"
        elif percentile >= 60:
            return f"📈 Upper range ({percentile:.0f}% - bullish side of range)"
        elif percentile >= 40:
            return f"➡️ Mid-range ({percentile:.0f}% - neutral)"
        elif percentile >= 20:
            return f"📉 Lower range ({percentile:.0f}% - bearish side of range)"
        else:
            return f"💡 Oversold ({percentile:.0f}% - near bottom of range, likely revert up)"

    elif "bearish" in zone:
        # In bearish zones, high percentile = recovering (less bearish)
        if percentile >= 80:
            return f"🔄 High recovery ({percentile:.0f}% - near top of {zone} zone)"
        elif percentile >= 60:
            return f"↗️ Recovering ({percentile:.0f}% within {zone} zone)"
        elif percentile >= 40:
            return f"➡️ Mid-range ({percentile:.0f}% within {zone} zone)"
        elif percentile >= 20:
            return f"↘️ Weakening ({percentile:.0f}% within {zone} zone)"
        else:
            return f"⚠️ Near bottom ({percentile:.0f}% - extreme within {zone} zone)"

    elif "bullish" in zone:
        # In bullish zones, high percentile = strengthening (more bullish)
        if percentile >= 80:
            return f"🚀 Very strong ({percentile:.0f}% - near top of {zone} zone)"
        elif percentile >= 60:
            return f"📈 Strengthening ({percentile:.0f}% within {zone} zone)"
        elif percentile >= 40:
            return f"➡️ Mid-range ({percentile:.0f}% within {zone} zone)"
        elif percentile >= 20:
            return f"📉 Weakening ({percentile:.0f}% within {zone} zone)"
        else:
            return f"⚠️ Near bottom ({percentile:.0f}% - weak within {zone} zone)"

    else:
        return f"➡️ {percentile:.0f}% within zone"


def calculate_live_macdv_percentiles(
    tickers: List[str] = None,
    period: str = "1y",
    percentile_lookback: int = 252
) -> pd.DataFrame:
    """
    Calculate live MACD-V percentiles for given tickers.

    Returns DataFrame with columns:
    - Ticker
    - MACD-V Value
    - Zone
    - Zone Range
    - Regime
    - Categorical %ile (within zone)
    - Asymmetric %ile (within bull/bear)
    - Interpretation
    """
    if tickers is None:
        tickers = LIVE_TICKERS

    calculator = MACDVPercentileCalculator(
        fast_length=12,
        slow_length=26,
        signal_length=9,
        atr_length=26,
        percentile_lookback=percentile_lookback
    )

    results = []

    print(f"Fetching data and calculating percentiles for {len(tickers)} tickers...")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    for ticker in tickers:
        try:
            # Fetch data
            df = yf.download(
                ticker,
                period=period,
                interval="1d",
                progress=False,
                auto_adjust=True
            )

            if df.empty or len(df) < 100:
                print(f"⚠️  {ticker}: Insufficient data")
                continue

            # Fix column names
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0].lower() if isinstance(col, tuple) else str(col).lower()
                             for col in df.columns]
            else:
                df.columns = [str(c).lower() for c in df.columns]

            # Calculate MACD-V with both methods
            df_cat = calculator.calculate_macdv_with_percentiles(df, method="categorical")
            df_asym = calculator.calculate_macdv_with_percentiles(df, method="asymmetric")

            # Get latest values
            latest_cat = df_cat.iloc[-1]
            latest_asym = df_asym.iloc[-1]

            macdv_val = latest_cat['macdv_val']
            zone = latest_cat['macdv_zone']
            cat_percentile = latest_cat['macdv_percentile']
            asym_percentile = latest_asym['macdv_percentile']

            # Get zone description
            zone_range, regime = get_zone_description(zone)

            # Get interpretation
            interpretation = interpret_percentile(zone, cat_percentile)

            results.append({
                'Ticker': ticker,
                'MACD-V': round(macdv_val, 2),
                'Zone': zone.replace('_', ' ').title(),
                'Zone Range': zone_range,
                'Regime': regime,
                'Cat %ile': round(cat_percentile, 1),
                'Asym %ile': round(asym_percentile, 1),
                'Interpretation': interpretation,
                'Last Update': df.index[-1].strftime('%Y-%m-%d')
            })

            print(f"✓ {ticker:10s}: MACD-V={macdv_val:7.2f}, Zone={zone:20s}, Cat%={cat_percentile:5.1f}%")

        except Exception as e:
            print(f"✗ {ticker:10s}: Error - {str(e)}")
            continue

    if not results:
        print("\n⚠️  No data collected")
        return pd.DataFrame()

    df_results = pd.DataFrame(results)

    # Sort by MACD-V value (most bearish to most bullish)
    df_results = df_results.sort_values('MACD-V', ascending=True).reset_index(drop=True)

    return df_results


def print_formatted_table(df: pd.DataFrame) -> None:
    """Print formatted table with MACD-V percentiles."""

    print("\n" + "="*120)
    print("LIVE MARKET STATE - MACD-V WITH PERCENTILES")
    print("="*120)
    print(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total tickers: {len(df)}")

    # Group by zone
    zones_order = [
        "Extreme Bearish",
        "Strong Bearish",
        "Ranging",
        "Strong Bullish",
        "Extreme Bullish"
    ]

    for zone in zones_order:
        zone_data = df[df['Zone'] == zone]
        if len(zone_data) == 0:
            continue

        print(f"\n{'─'*120}")
        print(f"📊 {zone.upper()} ({len(zone_data)} tickers)")
        print(f"{'─'*120}")

        # Print header
        print(f"{'Ticker':<10} {'MACD-V':>8} {'Zone Range':>15} {'Cat %ile':>10} {'Asym %ile':>10} {'Interpretation':<50}")
        print(f"{'─'*10} {'─'*8} {'─'*15} {'─'*10} {'─'*10} {'─'*50}")

        for _, row in zone_data.iterrows():
            print(f"{row['Ticker']:<10} {row['MACD-V']:8.2f} {row['Zone Range']:>15} "
                  f"{row['Cat %ile']:9.1f}% {row['Asym %ile']:9.1f}% {row['Interpretation']:<50}")

    # Summary statistics
    print(f"\n{'='*120}")
    print("SUMMARY STATISTICS")
    print(f"{'='*120}")

    zone_summary = df.groupby('Zone').agg({
        'Ticker': 'count',
        'MACD-V': ['mean', 'min', 'max'],
        'Cat %ile': 'mean'
    }).round(2)

    print("\nBy Zone:")
    print(zone_summary)

    # Highlight extreme percentiles
    print(f"\n{'─'*120}")
    print("🔍 EXTREME POSITIONS (≥80th or ≤20th percentile within zone)")
    print(f"{'─'*120}")

    extreme_high = df[df['Cat %ile'] >= 80].sort_values('Cat %ile', ascending=False)
    extreme_low = df[df['Cat %ile'] <= 20].sort_values('Cat %ile', ascending=True)

    if len(extreme_high) > 0:
        print("\n📈 High Percentile (≥80%) - Strength within zone:")
        for _, row in extreme_high.iterrows():
            print(f"  {row['Ticker']:10s}: {row['MACD-V']:7.2f} ({row['Cat %ile']:.1f}% in {row['Zone']}) - {row['Interpretation']}")

    if len(extreme_low) > 0:
        print("\n📉 Low Percentile (≤20%) - Weakness within zone:")
        for _, row in extreme_low.iterrows():
            print(f"  {row['Ticker']:10s}: {row['MACD-V']:7.2f} ({row['Cat %ile']:.1f}% in {row['Zone']}) - {row['Interpretation']}")


def generate_markdown_table(df: pd.DataFrame) -> str:
    """Generate markdown table for documentation."""

    md = f"# Live MACD-V Percentiles\n\n"
    md += f"**Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md += f"**Total Tickers:** {len(df)}\n\n"

    md += "## Complete Table\n\n"
    md += "| Ticker | MACD-V | Zone | Range | Cat %ile | Asym %ile | Interpretation |\n"
    md += "|--------|--------|------|-------|----------|-----------|----------------|\n"

    for _, row in df.iterrows():
        md += f"| {row['Ticker']} | {row['MACD-V']:.2f} | {row['Zone']} | {row['Zone Range']} | "
        md += f"{row['Cat %ile']:.1f}% | {row['Asym %ile']:.1f}% | {row['Interpretation']} |\n"

    # Add explanation section
    md += "\n## Understanding the Percentiles\n\n"
    md += "### Categorical Percentile (Cat %ile)\n"
    md += "- Calculated **within the current zone** (e.g., within strong_bullish zone)\n"
    md += "- Shows relative position within that specific market regime\n"
    md += "- Example: 84% in ranging zone = at 84th percentile of ranging values (near top of range)\n\n"

    md += "**In Bearish Zones:**\n"
    md += "- High percentile (≥80%) = Near top of zone = Recovering / Less bearish\n"
    md += "- Low percentile (≤20%) = Near bottom of zone = Deepening / More bearish\n\n"

    md += "**In Bullish Zones:**\n"
    md += "- High percentile (≥80%) = Near top of zone = Strong / More bullish\n"
    md += "- Low percentile (≤20%) = Near bottom of zone = Weak / Less bullish\n\n"

    md += "### Asymmetric Percentile (Asym %ile)\n"
    md += "- Calculated separately for bullish (≥0) and bearish (<0) regimes\n"
    md += "- Shows relative position within the directional regime\n"
    md += "- Useful for directional comparison independent of zone\n\n"

    md += "## Zone Definitions\n\n"
    md += "| Zone | Range | Regime | Typical Market Condition |\n"
    md += "|------|-------|--------|-------------------------|\n"
    md += "| Extreme Bearish | < -100 | Strong Downtrend | Severe selling pressure |\n"
    md += "| Strong Bearish | -100 to -50 | Downtrend | Clear downward momentum |\n"
    md += "| Ranging | -50 to +50 | Mean Reversion | Consolidation, no clear trend |\n"
    md += "| Strong Bullish | +50 to +100 | Uptrend | Clear upward momentum |\n"
    md += "| Extreme Bullish | > +100 | Strong Uptrend | Extreme buying pressure |\n\n"

    return md


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Parse command line arguments
    tickers = None
    if len(sys.argv) > 1:
        tickers = sys.argv[1].split(',')

    # Calculate percentiles
    df_results = calculate_live_macdv_percentiles(tickers=tickers)

    if df_results.empty:
        print("No results to display")
        sys.exit(1)

    # Print formatted table
    print_formatted_table(df_results)

    # Generate markdown
    markdown = generate_markdown_table(df_results)

    # Save to file
    output_dir = Path(__file__).parent.parent / "docs"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "live_macdv_percentiles.md"
    with open(output_file, "w") as f:
        f.write(markdown)

    print(f"\n{'='*120}")
    print(f"✓ Markdown table saved to: {output_file}")
    print(f"{'='*120}")

    # Also save CSV
    csv_file = output_dir / "live_macdv_percentiles.csv"
    df_results.to_csv(csv_file, index=False)
    print(f"✓ CSV data saved to: {csv_file}")
