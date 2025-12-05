#!/usr/bin/env python3
"""
Generate complete 4H and Daily statistics for NFLX (Netflix)
following the exact pattern used for GLD and SLV
"""

import numpy as np
import pandas as pd
from enhanced_mtf_analyzer import EnhancedMultiTimeframeAnalyzer
from dataclasses import dataclass
from typing import Dict
import json


@dataclass
class BinStatistics:
    """Statistics for a single percentile bin"""
    bin_range: str
    mean: float
    median: float
    std: float
    sample_size: int
    se: float
    t_score: float
    percentile_5th: float
    percentile_95th: float
    upside: float
    downside: float


def calculate_bin_statistics(data: pd.DataFrame, percentiles: pd.Series, prices: pd.Series,
                            bin_ranges: list, horizon_days: int = 6) -> Dict[str, BinStatistics]:
    """
    Calculate statistics for each percentile bin at a given horizon.

    For 4H data: horizon_days = 24 (approximately 1 day forward)
    For Daily data: horizon_days = 7 (1 week forward)
    """
    bin_stats = {}

    for bin_min, bin_max, label in bin_ranges:
        # Filter data for this bin
        mask = (percentiles >= bin_min) & (percentiles < bin_max)
        bin_indices = percentiles[mask].index

        # Calculate forward returns
        forward_returns = []
        for idx in bin_indices:
            try:
                # Find this timestamp in the data
                idx_loc = data.index.get_indexer([idx], method='nearest')[0]
                if idx_loc + horizon_days < len(data):
                    current_price = prices.iloc[idx_loc]
                    future_price = prices.iloc[idx_loc + horizon_days]
                    ret = (future_price / current_price - 1) * 100
                    forward_returns.append(ret)
            except:
                continue

        if len(forward_returns) < 5:  # Skip bins with too few samples
            continue

        returns = np.array(forward_returns)

        # Calculate statistics
        mean_return = np.mean(returns)
        median_return = np.median(returns)
        std_return = np.std(returns, ddof=1)
        n = len(returns)
        se = std_return / np.sqrt(n)
        t_score = mean_return / se if se > 0 else 0

        # Percentiles
        pct_5 = np.percentile(returns, 5)
        pct_95 = np.percentile(returns, 95)

        # Upside/Downside
        positive_returns = returns[returns > 0]
        negative_returns = returns[returns < 0]
        upside = np.mean(positive_returns) if len(positive_returns) > 0 else 0
        downside = np.mean(negative_returns) if len(negative_returns) > 0 else 0

        bin_stats[label] = BinStatistics(
            bin_range=label,
            mean=round(mean_return, 2),
            median=round(median_return, 2),
            std=round(std_return, 2),
            sample_size=n,
            se=round(se, 2),
            t_score=round(t_score, 2),
            percentile_5th=round(pct_5, 2),
            percentile_95th=round(pct_95, 2),
            upside=round(upside, 2),
            downside=round(downside, 2)
        )

    return bin_stats


def analyze_stock_personality(bin_stats_4h: Dict, bin_stats_daily: Dict, ticker: str) -> Dict:
    """Analyze stock personality based on bin statistics"""

    # Check mean reversion characteristics
    oversold_bins_4h = [bin_stats_4h.get('0-5'), bin_stats_4h.get('5-15'), bin_stats_4h.get('15-25')]
    overbought_bins_4h = [bin_stats_4h.get('75-85'), bin_stats_4h.get('85-95'), bin_stats_4h.get('95-100')]

    oversold_mean_4h = np.mean([b.mean for b in oversold_bins_4h if b is not None])
    overbought_mean_4h = np.mean([b.mean for b in overbought_bins_4h if b is not None])

    # Daily
    oversold_bins_daily = [bin_stats_daily.get('0-5'), bin_stats_daily.get('5-15'), bin_stats_daily.get('15-25')]
    overbought_bins_daily = [bin_stats_daily.get('75-85'), bin_stats_daily.get('85-95'), bin_stats_daily.get('95-100')]

    oversold_mean_daily = np.mean([b.mean for b in oversold_bins_daily if b is not None])
    overbought_mean_daily = np.mean([b.mean for b in overbought_bins_daily if b is not None])

    # Determine personality
    is_mean_reverter = (oversold_mean_4h > overbought_mean_4h) and (oversold_mean_daily > overbought_mean_daily)
    is_momentum = (oversold_mean_4h < overbought_mean_4h) or (oversold_mean_daily < overbought_mean_daily)

    # Calculate average volatility (std)
    avg_std_4h = np.mean([b.std for b in bin_stats_4h.values()])
    avg_std_daily = np.mean([b.std for b in bin_stats_daily.values()])

    if avg_std_daily > 5:
        volatility = "High"
    elif avg_std_daily > 3:
        volatility = "Medium"
    else:
        volatility = "Low"

    # Find best 4H bin (highest mean with significant t-score)
    best_4h_bin = None
    best_4h_t_score = 0
    best_4h_mean = 0
    for label, stats in bin_stats_4h.items():
        if abs(stats.t_score) > abs(best_4h_t_score):
            best_4h_bin = label
            best_4h_t_score = stats.t_score
            best_4h_mean = stats.mean

    # Tradeable zones (where t-score >= 2.0)
    tradeable_4h_zones = [label for label, stats in bin_stats_4h.items() if abs(stats.t_score) >= 2.0]
    dead_zones_4h = [label for label, stats in bin_stats_4h.items() if abs(stats.t_score) < 1.5]

    # NFLX-specific personality determination
    if ticker == 'NFLX':
        # Netflix is known for earnings-driven volatility and momentum characteristics
        if is_momentum and volatility == "High":
            personality = "High Volatility Momentum - Earnings Driven"
        elif is_momentum:
            personality = "Momentum / Trending"
        elif is_mean_reverter:
            personality = "Mean Reverter with High Volatility"
        else:
            personality = "Mixed Behavior - Event Driven"
    else:
        personality = "Mean Reverter" if is_mean_reverter else "Momentum / Trending"

    # Reliability ratings
    strong_4h_signals = len([s for s in bin_stats_4h.values() if abs(s.t_score) >= 2.0])
    strong_daily_signals = len([s for s in bin_stats_daily.values() if abs(s.t_score) >= 2.0])

    reliability_4h = "High" if strong_4h_signals >= 3 else "Medium" if strong_4h_signals >= 2 else "Low"
    reliability_daily = "High" if strong_daily_signals >= 4 else "Medium" if strong_daily_signals >= 2 else "Low"

    # Ease rating (1-10)
    ease_rating = min(10, strong_4h_signals + strong_daily_signals)

    return {
        'personality': personality,
        'is_mean_reverter': is_mean_reverter,
        'is_momentum': is_momentum,
        'volatility_level': volatility,
        'reliability_4h': reliability_4h,
        'reliability_daily': reliability_daily,
        'tradeable_4h_zones': tradeable_4h_zones,
        'dead_zones_4h': dead_zones_4h,
        'best_4h_bin': best_4h_bin,
        'best_4h_t_score': round(best_4h_t_score, 2),
        'best_4h_mean': round(best_4h_mean, 2),
        'ease_rating': ease_rating,
        'oversold_mean_4h': round(oversold_mean_4h, 2),
        'overbought_mean_4h': round(overbought_mean_4h, 2),
        'oversold_mean_daily': round(oversold_mean_daily, 2),
        'overbought_mean_daily': round(overbought_mean_daily, 2),
        'avg_std_4h': round(avg_std_4h, 2),
        'avg_std_daily': round(avg_std_daily, 2)
    }


def generate_guidance(personality_data: Dict, ticker: str) -> Dict:
    """Generate trading guidance based on personality"""

    if ticker == 'NFLX':
        name = "Netflix Inc."

        # Determine entry based on personality
        if personality_data['is_momentum']:
            entry = "Enter LONG when percentile > 75 (momentum plays). NFLX shows strong momentum characteristics. Watch for earnings catalysts."
        else:
            entry = "Enter LONG when percentile < 25 (oversold). Exit on strength above 75th percentile."

        # Determine avoid zones based on dead zones
        avoid_zones = personality_data.get('dead_zones_4h', [])
        if avoid_zones:
            avoid = f"Avoid trading in {', '.join(avoid_zones)} ranges - weak signals. Exercise extreme caution around earnings dates (high volatility)."
        else:
            avoid = "Exercise extreme caution around earnings dates (high volatility). Avoid trading 2 days before and 2 days after earnings."

        # Special notes based on volatility and personality
        special_notes = []
        if personality_data['volatility_level'] == "High":
            special_notes.append("NFLX is highly volatile (avg daily std > 5%)")

        if personality_data['is_momentum']:
            special_notes.append("Strong momentum characteristics - trends can persist")

        if personality_data['ease_rating'] < 5:
            special_notes.append("Moderate difficulty - requires careful timing")

        special_notes.append("Earnings-driven stock with unpredictable reactions to quarterly reports")
        special_notes.append("Best for experienced traders comfortable with high volatility")
        special_notes.append("Consider position sizing due to large price swings")

        if personality_data.get('tradeable_4h_zones'):
            special_notes.append(f"Best 4H trading zones: {', '.join(personality_data['tradeable_4h_zones'])}")

        special = " ".join(special_notes)
    else:
        name = ticker
        entry = "Trade based on extreme percentiles"
        avoid = "Middle ranges"
        special = "N/A"

    return {
        'name': name,
        'entry': entry,
        'avoid': avoid,
        'special_notes': special
    }


def main():
    """Generate statistics for NFLX"""

    ticker = 'NFLX'
    bin_ranges = [
        (0, 5, '0-5'),
        (5, 15, '5-15'),
        (15, 25, '15-25'),
        (25, 50, '25-50'),
        (50, 75, '50-75'),
        (75, 85, '75-85'),
        (85, 95, '85-95'),
        (95, 100, '95-100')
    ]

    print(f"\n{'='*80}")
    print(f"Generating statistics for {ticker}")
    print(f"{'='*80}\n")

    # Initialize analyzer
    print("Initializing analyzer with 1095 days of data...")
    analyzer = EnhancedMultiTimeframeAnalyzer(ticker, lookback_days=1095)

    # Calculate 4H statistics (24 hours forward ≈ 1 day)
    print("Calculating 4H statistics (24-hour horizon)...")
    bin_stats_4h = calculate_bin_statistics(
        analyzer.hourly_data,
        analyzer.hourly_4h_percentiles,
        analyzer.hourly_data['Close'],
        bin_ranges,
        horizon_days=24  # 24 hours forward ≈ 1 day
    )

    # Calculate Daily statistics (7 days forward ≈ 1 week)
    print("Calculating Daily statistics (7-day horizon)...")
    bin_stats_daily = calculate_bin_statistics(
        analyzer.daily_data,
        analyzer.daily_percentiles,
        analyzer.daily_data['Close'],
        bin_ranges,
        horizon_days=7
    )

    # Analyze personality
    print("Analyzing stock personality...")
    personality = analyze_stock_personality(bin_stats_4h, bin_stats_daily, ticker)

    # Generate guidance
    print("Generating trading guidance...")
    guidance = generate_guidance(personality, ticker)

    # Print summary
    print(f"\n{ticker} Summary:")
    print(f"  Personality: {personality['personality']}")
    print(f"  Volatility: {personality['volatility_level']} (4H: {personality['avg_std_4h']}%, Daily: {personality['avg_std_daily']}%)")
    print(f"  Reliability (4H): {personality['reliability_4h']}")
    print(f"  Reliability (Daily): {personality['reliability_daily']}")
    print(f"  Best 4H Bin: {personality['best_4h_bin']} (t={personality['best_4h_t_score']}, mean={personality['best_4h_mean']}%)")
    print(f"  Ease Rating: {personality['ease_rating']}/10")
    print(f"  Is Mean Reverter: {personality['is_mean_reverter']}")
    print(f"  Is Momentum: {personality['is_momentum']}")

    print(f"\n  4H Statistics:")
    for label, stats in bin_stats_4h.items():
        sig = "✅✅✅" if abs(stats.t_score) >= 4 else "✅✅" if abs(stats.t_score) >= 3 else "✅" if abs(stats.t_score) >= 2 else "⚠️" if abs(stats.t_score) >= 1.5 else "❌"
        print(f"    {label:8s}: mean={stats.mean:+6.2f}%, t={stats.t_score:+5.2f}, n={stats.sample_size:3d}, std={stats.std:5.2f}% {sig}")

    print(f"\n  Daily Statistics:")
    for label, stats in bin_stats_daily.items():
        sig = "✅✅✅" if abs(stats.t_score) >= 4 else "✅✅" if abs(stats.t_score) >= 3 else "✅" if abs(stats.t_score) >= 2 else "⚠️" if abs(stats.t_score) >= 1.5 else "❌"
        print(f"    {label:8s}: mean={stats.mean:+6.2f}%, t={stats.t_score:+5.2f}, n={stats.sample_size:3d}, std={stats.std:5.2f}% {sig}")

    print(f"\n  Trading Guidance:")
    print(f"    Entry: {guidance['entry']}")
    print(f"    Avoid: {guidance['avoid']}")
    print(f"    Special Notes: {guidance['special_notes']}")

    # Store results
    results = {
        ticker: {
            'ticker': ticker,
            'name': guidance['name'],
            'personality': personality,
            'guidance': guidance,
            'bin_stats_4h': {label: vars(stats) for label, stats in bin_stats_4h.items()},
            'bin_stats_daily': {label: vars(stats) for label, stats in bin_stats_daily.items()}
        }
    }

    # Save to JSON (convert booleans to strings)
    output_file = '/workspaces/New-test-strategy/backend/nflx_statistics.json'

    # Convert booleans in personality data
    p = results[ticker]['personality']
    p['is_mean_reverter'] = str(p['is_mean_reverter'])
    p['is_momentum'] = str(p['is_momentum'])

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*80}")
    print(f"✓ Statistics saved to: {output_file}")
    print(f"{'='*80}\n")

    # Generate Python code for stock_statistics.py
    print("\n" + "="*80)
    print("PYTHON CODE TO ADD TO stock_statistics.py:")
    print("="*80 + "\n")

    data = results[ticker]

    print(f"# ============================================")
    print(f"# {data['name']} ({ticker}) DATA")
    print(f"# ============================================\n")

    # 4H data
    print(f"{ticker}_4H_DATA = {{")
    for label, stats in data['bin_stats_4h'].items():
        print(f'    "{label}": BinStatistics("{label}", {stats["mean"]}, {stats["median"]}, {stats["std"]}, {stats["sample_size"]}, {stats["se"]}, {stats["t_score"]}, {stats["percentile_5th"]}, {stats["percentile_95th"]}, {stats["upside"]}, {stats["downside"]}),')
    print("}\n")

    # Daily data
    print(f"{ticker}_DAILY_DATA = {{")
    for label, stats in data['bin_stats_daily'].items():
        print(f'    "{label}": BinStatistics("{label}", {stats["mean"]}, {stats["median"]}, {stats["std"]}, {stats["sample_size"]}, {stats["se"]}, {stats["t_score"]}, {stats["percentile_5th"]}, {stats["percentile_95th"]}, {stats["upside"]}, {stats["downside"]}),')
    print("}\n")

    # Generate STOCK_METADATA entry
    print("# Add to STOCK_METADATA dictionary:\n")
    p = data['personality']
    g = data['guidance']

    print(f'    "{ticker}": {{')
    print(f'        "ticker": "{ticker}",')
    print(f'        "name": "{g["name"]}",')
    print(f'        "personality": "{p["personality"]}",')
    print(f'        "reliability_4h": "{p["reliability_4h"]}",')
    print(f'        "reliability_daily": "{p["reliability_daily"]}",')
    print(f'        "tradeable_4h_zones": {p["tradeable_4h_zones"]},')
    print(f'        "dead_zones_4h": {p["dead_zones_4h"]},')
    print(f'        "best_4h_bin": "{p["best_4h_bin"]}",')
    print(f'        "best_4h_t_score": {p["best_4h_t_score"]},')
    print(f'        "ease_rating": {p["ease_rating"]},')
    print(f'        "characteristics": {{')
    print(f'            "is_mean_reverter": {str(p["is_mean_reverter"]).lower()},')
    print(f'            "is_momentum": {str(p["is_momentum"]).lower()},')
    print(f'            "volatility_level": "{p["volatility_level"]}"')
    print(f'        }},')
    print(f'        "guidance": {{')
    print(f'            "entry": "{g["entry"]}",')
    print(f'            "avoid": "{g["avoid"]}",')
    print(f'            "special_notes": "{g["special_notes"]}"')
    print(f'        }}')
    print(f'    }},')
    print()


if __name__ == '__main__':
    main()
