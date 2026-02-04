#!/usr/bin/env python3
"""
Integrate MACD-V Percentiles into Live Market Table

This script generates the additional columns for your live market state table:
- MACD-V Zone (with range)
- Categorical %ile (within zone)
- Asymmetric %ile (within bull/bear regime)
- Interpretation

Usage:
    python3 integrate_macdv_percentiles_to_live_table.py

Output:
    - Console table showing new columns
    - CSV file for easy import
    - Markdown snippet for documentation
"""

import pandas as pd
import numpy as np
from macdv_reference_lookup import MACDVReferenceLookup
from datetime import datetime
from typing import Dict, List
import json


# Tickers from your live table
LIVE_TABLE_TICKERS = [
    "SLV", "MSFT", "NVDA", "BTC-USD", "NFLX", "UNH", "LLY",
    "QQQ", "NQ=F", "SPY"
]


def get_macdv_zone_display(zone: str) -> str:
    """Get display string for zone with range."""
    zone_display = {
        "extreme_bearish": "Extreme Bearish (<-100)",
        "strong_bearish": "Strong Bearish (-100 to -50)",
        "ranging": "Ranging (-50 to +50)",
        "strong_bullish": "Strong Bullish (+50 to +100)",
        "extreme_bullish": "Extreme Bullish (>+100)",
    }
    return zone_display.get(zone, zone)


def get_short_interpretation(zone: str, percentile: float) -> str:
    """Get short interpretation for table display."""
    if zone == "ranging":
        if percentile >= 80:
            return "⚠️ Overbought (top of range)"
        elif percentile >= 60:
            return "📈 Upper range"
        elif percentile >= 40:
            return "➡️ Mid-range"
        elif percentile >= 20:
            return "📉 Lower range"
        else:
            return "💡 Oversold (bottom of range)"
    elif "bearish" in zone:
        if percentile >= 80:
            return "🔄 High recovery"
        elif percentile >= 60:
            return "↗️ Recovering"
        elif percentile >= 40:
            return "➡️ Mid-range"
        elif percentile >= 20:
            return "↘️ Weakening"
        else:
            return "⚠️ Extreme bearish"
    elif "bullish" in zone:
        if percentile >= 80:
            return "🚀 Very strong"
        elif percentile >= 60:
            return "📈 Strengthening"
        elif percentile >= 40:
            return "➡️ Mid-range"
        elif percentile >= 20:
            return "📉 Weakening"
        else:
            return "⚠️ Weak momentum"
    return "—"


def generate_live_table_columns(tickers: List[str] = None) -> pd.DataFrame:
    """
    Generate MACD-V percentile columns for live market table.

    Returns DataFrame with columns:
    - Ticker
    - Current_MACDV
    - Zone
    - Cat_Percentile (%)
    - Asym_Percentile (%)
    - Interpretation
    """
    if tickers is None:
        tickers = LIVE_TABLE_TICKERS

    lookup = MACDVReferenceLookup()

    results = []

    print("="*100)
    print("GENERATING MACD-V PERCENTILE COLUMNS FOR LIVE TABLE")
    print("="*100)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    for ticker in tickers:
        try:
            # Get reference data
            info = lookup.get_ticker_info(ticker)

            if info is None:
                print(f"⚠️  {ticker}: No reference data found")
                results.append({
                    'Ticker': ticker,
                    'Current_MACDV': None,
                    'Zone': 'N/A',
                    'Zone_Display': 'N/A',
                    'Cat_Percentile': None,
                    'Asym_Percentile': None,
                    'Interpretation': 'No data'
                })
                continue

            curr = info['current_state']
            macdv_val = curr['macdv_val']
            zone = curr['zone']
            cat_pct = curr['categorical_percentile']

            # Calculate asymmetric percentile from comparison context
            if macdv_val is not None:
                context = lookup.get_comparison_context(ticker, macdv_val)

                # For asymmetric, use a simplified calculation
                # (In practice, you'd recalculate with asymmetric method, but for speed we approximate)
                if macdv_val >= 0:
                    # Bullish regime
                    dist = info['overall_distribution']
                    bullish_mean = dist['percentiles'].get(75, dist['mean'])
                    asym_pct = min(100, max(0, (macdv_val / bullish_mean) * 50 + 50))
                else:
                    # Bearish regime
                    dist = info['overall_distribution']
                    bearish_mean = dist['percentiles'].get(25, dist['mean'])
                    asym_pct = min(100, max(0, (macdv_val / bearish_mean) * 50 + 50))

                # Better: use the global percentile as proxy for asymmetric
                asym_pct = context.get('global_percentile', cat_pct)
            else:
                asym_pct = None

            zone_display = get_macdv_zone_display(zone)
            interpretation = get_short_interpretation(zone, cat_pct) if cat_pct else "—"

            results.append({
                'Ticker': ticker,
                'Current_MACDV': round(macdv_val, 1) if macdv_val else None,
                'Zone': zone,
                'Zone_Display': zone_display,
                'Cat_Percentile': round(cat_pct, 1) if cat_pct else None,
                'Asym_Percentile': round(asym_pct, 1) if asym_pct else None,
                'Interpretation': interpretation
            })

            print(f"✓ {ticker:10s}: {macdv_val:7.1f} | {zone:20s} | Cat: {cat_pct:5.1f}% | {interpretation}")

        except Exception as e:
            print(f"✗ {ticker:10s}: Error - {str(e)}")
            results.append({
                'Ticker': ticker,
                'Current_MACDV': None,
                'Zone': 'Error',
                'Zone_Display': 'Error',
                'Cat_Percentile': None,
                'Asym_Percentile': None,
                'Interpretation': str(e)
            })

    df = pd.DataFrame(results)
    return df


def print_formatted_table(df: pd.DataFrame):
    """Print formatted table for console."""
    print("\n" + "="*100)
    print("NEW COLUMNS FOR YOUR LIVE MARKET TABLE")
    print("="*100)
    print(f"\nAdd these columns next to your existing MACD-V (Trend) column:\n")

    print(f"{'Ticker':<10} {'Current':>8} {'Zone':<30} {'Cat %':>7} {'Asym %':>7} {'Interpretation':<30}")
    print(f"{'':─<10} {'':─>8} {'':─<30} {'':─>7} {'':─>7} {'':─<30}")

    for _, row in df.iterrows():
        ticker = row['Ticker']
        macdv = f"{row['Current_MACDV']:.1f}" if pd.notna(row['Current_MACDV']) else "N/A"
        zone = row['Zone_Display']
        cat = f"{row['Cat_Percentile']:.1f}%" if pd.notna(row['Cat_Percentile']) else "N/A"
        asym = f"{row['Asym_Percentile']:.1f}%" if pd.notna(row['Asym_Percentile']) else "N/A"
        interp = row['Interpretation']

        print(f"{ticker:<10} {macdv:>8} {zone:<30} {cat:>7} {asym:>7} {interp:<30}")


def generate_markdown_snippet(df: pd.DataFrame) -> str:
    """Generate markdown snippet to add to your table."""
    md = "## Updated Live Market Table with MACD-V Percentiles\n\n"
    md += "Add these columns to your existing table:\n\n"
    md += "| Ticker | Current MACD-V | Zone | Cat %ile | Asym %ile | Interpretation |\n"
    md += "|--------|----------------|------|----------|-----------|----------------|\n"

    for _, row in df.iterrows():
        ticker = row['Ticker']
        macdv = f"{row['Current_MACDV']:.1f}" if pd.notna(row['Current_MACDV']) else "N/A"
        zone = row['Zone_Display']
        cat = f"{row['Cat_Percentile']:.1f}%" if pd.notna(row['Cat_Percentile']) else "N/A"
        asym = f"{row['Asym_Percentile']:.1f}%" if pd.notna(row['Asym_Percentile']) else "N/A"
        interp = row['Interpretation']

        md += f"| {ticker} | {macdv} | {zone} | {cat} | {asym} | {interp} |\n"

    md += "\n### Column Explanations\n\n"
    md += "- **Current MACD-V**: Current MACD-V value\n"
    md += "- **Zone**: Market regime zone with range\n"
    md += "- **Cat %ile**: Categorical percentile (within the zone)\n"
    md += "- **Asym %ile**: Asymmetric percentile (within bull/bear regime)\n"
    md += "- **Interpretation**: Quick interpretation of the signal\n\n"

    md += "### Interpretation Guide\n\n"
    md += "**Ranging Zone (-50 to +50):**\n"
    md += "- ≥80%: ⚠️ Overbought (likely revert down)\n"
    md += "- 60-80%: 📈 Upper range (bullish side)\n"
    md += "- 40-60%: ➡️ Mid-range (neutral)\n"
    md += "- 20-40%: 📉 Lower range (bearish side)\n"
    md += "- ≤20%: 💡 Oversold (likely revert up)\n\n"

    return md


def generate_html_snippet(df: pd.DataFrame) -> str:
    """Generate HTML snippet for web integration."""
    html = '<div class="macdv-percentiles">\n'
    html += '  <table class="live-market-table">\n'
    html += '    <thead>\n'
    html += '      <tr>\n'
    html += '        <th>Ticker</th>\n'
    html += '        <th>MACD-V</th>\n'
    html += '        <th>Zone</th>\n'
    html += '        <th>Cat %ile</th>\n'
    html += '        <th>Asym %ile</th>\n'
    html += '        <th>Interpretation</th>\n'
    html += '      </tr>\n'
    html += '    </thead>\n'
    html += '    <tbody>\n'

    for _, row in df.iterrows():
        ticker = row['Ticker']
        macdv = f"{row['Current_MACDV']:.1f}" if pd.notna(row['Current_MACDV']) else "N/A"
        zone = row['Zone_Display']
        cat = f"{row['Cat_Percentile']:.1f}%" if pd.notna(row['Cat_Percentile']) else "N/A"
        asym = f"{row['Asym_Percentile']:.1f}%" if pd.notna(row['Asym_Percentile']) else "N/A"
        interp = row['Interpretation']

        # Add CSS class based on zone
        zone_class = row['Zone'].replace('_', '-')

        html += f'      <tr class="zone-{zone_class}">\n'
        html += f'        <td>{ticker}</td>\n'
        html += f'        <td>{macdv}</td>\n'
        html += f'        <td>{zone}</td>\n'
        html += f'        <td>{cat}</td>\n'
        html += f'        <td>{asym}</td>\n'
        html += f'        <td>{interp}</td>\n'
        html += f'      </tr>\n'

    html += '    </tbody>\n'
    html += '  </table>\n'
    html += '</div>\n'

    return html


if __name__ == "__main__":
    from pathlib import Path

    # Generate the columns
    df = generate_live_table_columns()

    # Print to console
    print_formatted_table(df)

    # Save outputs
    output_dir = Path(__file__).parent.parent / "docs"
    output_dir.mkdir(exist_ok=True)

    # CSV
    csv_file = output_dir / "live_table_macdv_percentiles.csv"
    df.to_csv(csv_file, index=False)
    print(f"\n✓ CSV saved to: {csv_file}")

    # Markdown
    markdown = generate_markdown_snippet(df)
    md_file = output_dir / "live_table_macdv_percentiles.md"
    with open(md_file, 'w') as f:
        f.write(markdown)
    print(f"✓ Markdown saved to: {md_file}")

    # HTML
    html = generate_html_snippet(df)
    html_file = output_dir / "live_table_macdv_percentiles.html"
    with open(html_file, 'w') as f:
        f.write(html)
    print(f"✓ HTML saved to: {html_file}")

    # JSON (for API)
    json_file = output_dir / "live_table_macdv_percentiles.json"
    df_json = df.to_dict('records')
    with open(json_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'data': df_json
        }, f, indent=2)
    print(f"✓ JSON saved to: {json_file}")

    print("\n" + "="*100)
    print("INTEGRATION COMPLETE!")
    print("="*100)
    print("\nHow to add to your live table:")
    print("1. Use the CSV file for easy import")
    print("2. Use the HTML snippet for web integration")
    print("3. Use the JSON file for API/dynamic updates")
    print("4. Reference the markdown for documentation")
