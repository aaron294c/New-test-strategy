#!/usr/bin/env python3
"""
Precompute MACD-V Reference Distributions

This script calculates and stores historical MACD-V distribution statistics
for each ticker individually. The results are saved to a JSON file that can
be loaded quickly without recalculation on each page refresh.

For each ticker, we store:
- Overall distribution statistics (min, max, mean, median, std, percentiles)
- Zone-specific statistics (how much time in each zone, typical ranges)
- Reference data for percentile calculations

This allows the frontend to show:
- "AAPL MACD-V is at 75.3 (67th percentile in strong_bullish zone)"
- "Historically, AAPL spends 23% of time in strong_bullish zone"
- "Current value is at the 85th percentile of all AAPL MACD-V values"
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
from typing import Dict, List
import json
from pathlib import Path

try:
    from macdv_percentile_calculator import MACDVPercentileCalculator
except ModuleNotFoundError:
    from backend.macdv_percentile_calculator import MACDVPercentileCalculator  # type: ignore


# All tickers from your live table
ALL_TICKERS = [
    "SLV", "MSFT", "NVDA", "BTC-USD", "NFLX", "UNH", "LLY",
    "QQQ", "NQ=F", "SPY", "AAPL", "GOOGL", "META", "AMZN",
    "BRK-B", "WMT", "AVGO", "TSM", "ORCL", "OXY", "XOM",
    "CVX", "JPM", "BAC", "ES=F", "^VIX", "DX-Y.NYB", "^TNX", "XLI", "TSLA", "GLD",
    # Additional tickers present in the Swing Framework live table
    "COST",
    "CNX1.L", "CSP1.L", "IGLS.L",
    "USDGBP=X",
]


def calculate_ticker_reference(
    ticker: str,
    period: str = "5y",
    percentile_lookback: int = 252
) -> Dict:
    """
    Calculate complete reference statistics for a single ticker.

    Returns comprehensive statistics including:
    - Overall distribution
    - Zone-specific distributions
    - Percentile reference points
    """
    try:
        # Fetch data
        print(f"Processing {ticker}...", end=" ", flush=True)
        df = yf.download(
            ticker,
            period=period,
            interval="1d",
            progress=False,
            auto_adjust=True
        )

        if df.empty or len(df) < 100:
            print(f"❌ Insufficient data")
            return None

        # Fix column names
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0].lower() if isinstance(col, tuple) else str(col).lower()
                         for col in df.columns]
        else:
            df.columns = [str(c).lower() for c in df.columns]

        # Calculate MACD-V with categorical percentiles
        calculator = MACDVPercentileCalculator(
            fast_length=12,
            slow_length=26,
            signal_length=9,
            atr_length=26,
            percentile_lookback=percentile_lookback
        )
        df_result = calculator.calculate_macdv_with_percentiles(df, method="categorical")

        # Remove NaN values
        macdv_series = df_result['macdv_val'].dropna()

        if len(macdv_series) < 50:
            print(f"❌ Insufficient valid data")
            return None

        # Overall distribution statistics
        overall_stats = {
            "count": int(len(macdv_series)),
            "min": float(macdv_series.min()),
            "max": float(macdv_series.max()),
            "mean": float(macdv_series.mean()),
            "median": float(macdv_series.median()),
            "std": float(macdv_series.std()),
            "percentiles": {
                int(p): float(np.percentile(macdv_series, p))
                for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]
            }
        }

        # Calculate zone statistics
        zone_stats = {}
        for zone_name, zone_min, zone_max in calculator.ZONES:
            zone_data = macdv_series[(macdv_series >= zone_min) & (macdv_series < zone_max)]

            if len(zone_data) == 0:
                zone_stats[zone_name] = {
                    "count": 0,
                    "pct_of_time": 0.0,
                    "min": None,
                    "max": None,
                    "mean": None,
                    "median": None
                }
                continue

            zone_stats[zone_name] = {
                "count": int(len(zone_data)),
                "pct_of_time": float(len(zone_data) / len(macdv_series) * 100),
                "min": float(zone_data.min()),
                "max": float(zone_data.max()),
                "mean": float(zone_data.mean()),
                "median": float(zone_data.median()),
                "percentiles": {
                    int(p): float(np.percentile(zone_data, p))
                    for p in [10, 25, 50, 75, 90]
                }
            }

        # Key ranges
        ranges_pct = {
            "within_150": float(((macdv_series >= -150) & (macdv_series <= 150)).sum() / len(macdv_series) * 100),
            "within_100": float(((macdv_series >= -100) & (macdv_series <= 100)).sum() / len(macdv_series) * 100),
            "within_50": float(((macdv_series >= -50) & (macdv_series <= 50)).sum() / len(macdv_series) * 100),
        }

        # Current state (latest value)
        latest = df_result.iloc[-1]
        current_state = {
            "macdv_val": float(latest['macdv_val']) if pd.notna(latest['macdv_val']) else None,
            "zone": str(latest['macdv_zone']),
            "categorical_percentile": float(latest['macdv_percentile']) if pd.notna(latest['macdv_percentile']) else None,
            "last_date": df.index[-1].strftime('%Y-%m-%d')
        }

        result = {
            "ticker": ticker,
            "period": period,
            "data_points": len(macdv_series),
            "date_range": {
                "start": df.index[0].strftime('%Y-%m-%d'),
                "end": df.index[-1].strftime('%Y-%m-%d')
            },
            "overall_distribution": overall_stats,
            "zone_distribution": zone_stats,
            "key_ranges_pct": ranges_pct,
            "current_state": current_state,
            "calculation_timestamp": datetime.now().isoformat()
        }

        print(f"✓ ({len(macdv_series)} points)")
        return result

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def generate_reference_database(
    tickers: List[str] = None,
    period: str = "5y",
    percentile_lookback: int = 252
) -> Dict:
    """
    Generate complete reference database for all tickers.

    Returns dictionary with:
    - metadata (generation time, parameters)
    - ticker_data (reference stats for each ticker)
    - aggregate_stats (combined statistics)
    """
    if tickers is None:
        tickers = ALL_TICKERS

    print("="*80)
    print("GENERATING MACD-V REFERENCE DATABASE")
    print("="*80)
    print(f"Tickers: {len(tickers)}")
    print(f"Period: {period}")
    print(f"Percentile lookback: {percentile_lookback}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()

    ticker_data = {}
    successful = 0
    failed = 0

    for ticker in tickers:
        result = calculate_ticker_reference(ticker, period, percentile_lookback)
        if result is not None:
            ticker_data[ticker] = result
            successful += 1
        else:
            failed += 1

    # Calculate aggregate statistics across all tickers
    all_means = [data['overall_distribution']['mean'] for data in ticker_data.values()]
    all_stds = [data['overall_distribution']['std'] for data in ticker_data.values()]

    aggregate_stats = {
        "total_tickers": len(ticker_data),
        "total_data_points": sum(data['data_points'] for data in ticker_data.values()),
        "mean_of_means": float(np.mean(all_means)),
        "mean_of_stds": float(np.mean(all_stds)),
        "bullish_skew_count": sum(1 for mean in all_means if mean > 0),
        "bearish_skew_count": sum(1 for mean in all_means if mean < 0),
    }

    database = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "period": period,
            "percentile_lookback": percentile_lookback,
            "total_tickers_attempted": len(tickers),
            "successful": successful,
            "failed": failed,
            "version": "1.0"
        },
        "aggregate_stats": aggregate_stats,
        "ticker_data": ticker_data
    }

    print()
    print("="*80)
    print(f"✓ Successfully processed: {successful}/{len(tickers)} tickers")
    if failed > 0:
        print(f"✗ Failed: {failed} tickers")
    print(f"✓ Total data points: {aggregate_stats['total_data_points']:,}")
    print("="*80)

    return database


def generate_summary_report(database: Dict) -> str:
    """Generate markdown summary report of the reference database."""

    md = "# MACD-V Reference Database Summary\n\n"
    md += f"**Generated:** {database['metadata']['generated_at']}\n\n"
    md += f"**Period:** {database['metadata']['period']}\n\n"
    md += f"**Tickers:** {database['metadata']['successful']} tickers\n\n"

    md += "## Aggregate Statistics\n\n"
    agg = database['aggregate_stats']
    md += f"- Total data points: {agg['total_data_points']:,}\n"
    md += f"- Mean of means: {agg['mean_of_means']:.2f}\n"
    md += f"- Tickers with bullish skew: {agg['bullish_skew_count']}\n"
    md += f"- Tickers with bearish skew: {agg['bearish_skew_count']}\n\n"

    md += "## Individual Ticker Statistics\n\n"
    md += "| Ticker | Data Points | Mean | Std | Median | Range | Current Zone | Cat %ile |\n"
    md += "|--------|-------------|------|-----|--------|-------|--------------|----------|\n"

    for ticker, data in sorted(database['ticker_data'].items()):
        dist = data['overall_distribution']
        curr = data['current_state']
        cat_pct = curr['categorical_percentile']
        cat_pct_str = f"{cat_pct:.1f}%" if cat_pct is not None else "N/A"

        md += f"| {ticker} | {data['data_points']} | {dist['mean']:.2f} | {dist['std']:.2f} | "
        md += f"{dist['median']:.2f} | {dist['min']:.1f} to {dist['max']:.1f} | "
        md += f"{curr['zone'].replace('_', ' ').title()} | {cat_pct_str} |\n"

    md += "\n## Zone Distribution (Average across tickers)\n\n"

    # Calculate average zone distribution
    zone_names = ["extreme_bearish", "strong_bearish", "ranging",
                  "strong_bullish", "extreme_bullish"]

    md += "| Zone | Avg % of Time | Interpretation |\n"
    md += "|------|---------------|----------------|\n"

    for zone_name in zone_names:
        pcts = [data['zone_distribution'][zone_name]['pct_of_time']
                for data in database['ticker_data'].values()
                if data['zone_distribution'][zone_name]['count'] > 0]

        if pcts:
            avg_pct = np.mean(pcts)
            zone_label = zone_name.replace('_', ' ').title()
            md += f"| {zone_label} | {avg_pct:.1f}% | "

            if "bearish" in zone_name:
                md += "Downtrend/Recovery zone |\n"
            elif "bullish" in zone_name:
                md += "Uptrend/Momentum zone |\n"
            else:
                md += "Neutral |\n"

    md += "\n## Key Ranges (Average across tickers)\n\n"

    within_150 = np.mean([data['key_ranges_pct']['within_150']
                          for data in database['ticker_data'].values()])
    within_100 = np.mean([data['key_ranges_pct']['within_100']
                          for data in database['ticker_data'].values()])
    within_50 = np.mean([data['key_ranges_pct']['within_50']
                         for data in database['ticker_data'].values()])

    md += f"- Within ±150: {within_150:.1f}%\n"
    md += f"- Within ±100: {within_100:.1f}%\n"
    md += f"- Within ±50: {within_50:.1f}%\n\n"

    return md


if __name__ == "__main__":
    import sys

    # Parse command line arguments
    tickers = None
    if len(sys.argv) > 1 and sys.argv[1] != "all":
        tickers = sys.argv[1].split(',')

    # Generate reference database
    database = generate_reference_database(tickers=tickers, period="5y")

    # Save to JSON
    output_dir = Path(__file__).parent.parent / "docs"
    output_dir.mkdir(exist_ok=True)

    json_file = output_dir / "macdv_reference_database.json"
    with open(json_file, "w") as f:
        json.dump(database, f, indent=2)

    print(f"\n✓ Reference database saved to: {json_file}")
    print(f"  File size: {json_file.stat().st_size / 1024:.1f} KB")

    # Generate and save summary report
    summary = generate_summary_report(database)
    summary_file = output_dir / "macdv_reference_summary.md"
    with open(summary_file, "w") as f:
        f.write(summary)

    print(f"✓ Summary report saved to: {summary_file}")
    print()
    print("="*80)
    print("DONE! Reference database is ready for use.")
    print("="*80)
    print("\nThis file can now be loaded quickly without recalculation.")
    print("Use it to show percentiles for any ticker without recomputing.")
