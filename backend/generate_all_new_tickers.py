#!/usr/bin/env python3
"""
Generate complete 4H and Daily statistics for new tickers:
BRK.B, WMT, UNH, AVGO, LLY, TSM, ORCL, OXY
"""

import numpy as np
import pandas as pd
from enhanced_mtf_analyzer import EnhancedMultiTimeframeAnalyzer
from dataclasses import dataclass
from typing import Dict
import json
import sys


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


# Ticker metadata
TICKER_META = {
    'BRK-B': {'name': 'Berkshire Hathaway Inc. Class B'},
    'WMT': {'name': 'Walmart Inc.'},
    'UNH': {'name': 'UnitedHealth Group Inc.'},
    'AVGO': {'name': 'Broadcom Inc.'},
    'LLY': {'name': 'Eli Lilly and Company'},
    'TSM': {'name': 'Taiwan Semiconductor'},
    'ORCL': {'name': 'Oracle Corporation'},
    'OXY': {'name': 'Occidental Petroleum'}
}


def calculate_bin_statistics(data: pd.DataFrame, percentiles: pd.Series, prices: pd.Series,
                            bin_ranges: list, horizon_days: int = 6) -> Dict[str, BinStatistics]:
    """Calculate statistics for each percentile bin at a given horizon."""
    bin_stats = {}

    for bin_min, bin_max, label in bin_ranges:
        mask = (percentiles >= bin_min) & (percentiles < bin_max)
        bin_indices = percentiles[mask].index

        forward_returns = []
        for idx in bin_indices:
            try:
                idx_loc = data.index.get_indexer([idx], method='nearest')[0]
                if idx_loc + horizon_days < len(data):
                    current_price = prices.iloc[idx_loc]
                    future_price = prices.iloc[idx_loc + horizon_days]
                    ret = (future_price / current_price - 1) * 100
                    forward_returns.append(ret)
            except:
                continue

        if len(forward_returns) < 5:
            continue

        returns = np.array(forward_returns)

        mean_return = np.mean(returns)
        median_return = np.median(returns)
        std_return = np.std(returns, ddof=1)
        n = len(returns)
        se = std_return / np.sqrt(n)
        t_score = mean_return / se if se > 0 else 0

        pct_5 = np.percentile(returns, 5)
        pct_95 = np.percentile(returns, 95)

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


def analyze_stock_personality(bin_stats_4h: Dict, bin_stats_daily: Dict) -> Dict:
    """Analyze stock personality based on bin statistics"""

    oversold_bins_4h = [bin_stats_4h.get('0-5'), bin_stats_4h.get('5-15'), bin_stats_4h.get('15-25')]
    overbought_bins_4h = [bin_stats_4h.get('75-85'), bin_stats_4h.get('85-95'), bin_stats_4h.get('95-100')]

    oversold_mean_4h = np.mean([b.mean for b in oversold_bins_4h if b is not None])
    overbought_mean_4h = np.mean([b.mean for b in overbought_bins_4h if b is not None])

    oversold_bins_daily = [bin_stats_daily.get('0-5'), bin_stats_daily.get('5-15'), bin_stats_daily.get('15-25')]
    overbought_bins_daily = [bin_stats_daily.get('75-85'), bin_stats_daily.get('85-95'), bin_stats_daily.get('95-100')]

    oversold_mean_daily = np.mean([b.mean for b in oversold_bins_daily if b is not None])
    overbought_mean_daily = np.mean([b.mean for b in overbought_bins_daily if b is not None])

    is_mean_reverter = (oversold_mean_4h > overbought_mean_4h) and (oversold_mean_daily > overbought_mean_daily)
    is_momentum = not is_mean_reverter

    avg_std_daily = np.mean([b.std for b in bin_stats_daily.values()])

    if avg_std_daily > 5:
        volatility = "High"
    elif avg_std_daily > 3:
        volatility = "Medium"
    else:
        volatility = "Low"

    best_4h_bin = None
    best_4h_t_score = 0
    best_4h_mean = 0
    for label, stats in bin_stats_4h.items():
        if abs(stats.t_score) > abs(best_4h_t_score):
            best_4h_bin = label
            best_4h_t_score = stats.t_score
            best_4h_mean = stats.mean

    tradeable_4h_zones = [label for label, stats in bin_stats_4h.items() if abs(stats.t_score) >= 2.0]
    dead_zones_4h = [label for label, stats in bin_stats_4h.items() if abs(stats.t_score) < 1.5]

    personality = "Momentum Trending" if is_momentum else "Mean Reverter"

    strong_4h_signals = len([s for s in bin_stats_4h.values() if abs(s.t_score) >= 2.0])
    strong_daily_signals = len([s for s in bin_stats_daily.values() if abs(s.t_score) >= 2.0])

    reliability_4h = "High" if strong_4h_signals >= 3 else "Medium" if strong_4h_signals >= 2 else "Low"
    reliability_daily = "High" if strong_daily_signals >= 4 else "Medium" if strong_daily_signals >= 2 else "Low"

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
        'ease_rating': ease_rating
    }


def generate_ticker_stats(ticker: str):
    """Generate statistics for a single ticker"""

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

    try:
        analyzer = EnhancedMultiTimeframeAnalyzer(ticker, lookback_days=1095)

        print("Calculating 4H statistics...")
        bin_stats_4h = calculate_bin_statistics(
            analyzer.hourly_data,
            analyzer.hourly_4h_percentiles,
            analyzer.hourly_data['Close'],
            bin_ranges,
            horizon_days=24
        )

        print("Calculating Daily statistics...")
        bin_stats_daily = calculate_bin_statistics(
            analyzer.daily_data,
            analyzer.daily_percentiles,
            analyzer.daily_data['Close'],
            bin_ranges,
            horizon_days=7
        )

        print("Analyzing stock personality...")
        personality = analyze_stock_personality(bin_stats_4h, bin_stats_daily)

        print(f"\n{ticker} Summary:")
        print(f"  Personality: {personality['personality']}")
        print(f"  Volatility: {personality['volatility_level']}")
        print(f"  Best 4H Bin: {personality['best_4h_bin']} (t={personality['best_4h_t_score']})")
        print(f"  Ease Rating: {personality['ease_rating']}/10")

        return {
            'ticker': ticker,
            'name': TICKER_META[ticker]['name'],
            'personality': personality,
            'bin_stats_4h': {label: vars(stats) for label, stats in bin_stats_4h.items()},
            'bin_stats_daily': {label: vars(stats) for label, stats in bin_stats_daily.items()}
        }

    except Exception as e:
        print(f"ERROR: Failed to generate stats for {ticker}: {e}")
        return None


def generate_python_code(ticker: str, data: Dict):
    """Generate Python code for stock_statistics.py"""

    print(f"\n# ============================================")
    print(f"# {data['name']} ({ticker}) DATA")
    print(f"# ============================================\n")

    # 4H data
    print(f"{ticker.replace('.', '_')}_4H_DATA = {{")
    for label, stats in data['bin_stats_4h'].items():
        print(f'    "{label}": BinStatistics("{label}", {stats["mean"]}, {stats["median"]}, {stats["std"]}, {stats["sample_size"]}, {stats["se"]}, {stats["t_score"]}, {stats["percentile_5th"]}, {stats["percentile_95th"]}, {stats["upside"]}, {stats["downside"]}),')
    print("}\n")

    # Daily data
    print(f"{ticker.replace('.', '_')}_DAILY_DATA = {{")
    for label, stats in data['bin_stats_daily'].items():
        print(f'    "{label}": BinStatistics("{label}", {stats["mean"]}, {stats["median"]}, {stats["std"]}, {stats["sample_size"]}, {stats["se"]}, {stats["t_score"]}, {stats["percentile_5th"]}, {stats["percentile_95th"]}, {stats["upside"]}, {stats["downside"]}),')
    print("}\n")

    # Metadata
    p = data['personality']
    print(f'    "{ticker}": StockMetadata(')
    print(f'        ticker="{ticker}",')
    print(f'        name="{data["name"]}",')
    print(f'        personality="{p["personality"]}",')
    print(f'        reliability_4h="{p["reliability_4h"]}",')
    print(f'        reliability_daily="{p["reliability_daily"]}",')
    print(f'        tradeable_4h_zones={p["tradeable_4h_zones"]},')
    print(f'        dead_zones_4h={p["dead_zones_4h"]},')
    print(f'        best_4h_bin="{p["best_4h_bin"]}",')
    print(f'        best_4h_t_score={p["best_4h_t_score"]},')
    print(f'        ease_rating={p["ease_rating"]},')
    print(f'        is_mean_reverter={str(p["is_mean_reverter"])},')
    print(f'        is_momentum={str(p["is_momentum"])},')
    print(f'        volatility_level="{p["volatility_level"]}",')
    print(f'        entry_guidance="Standard entry rules apply",')
    print(f'        avoid_guidance="Avoid weak signal zones",')
    print(f'        special_notes="Trade based on t-score strength"')
    print(f'    ),')


def main():
    """Generate statistics for all new tickers"""

    tickers = ['BRK-B', 'WMT', 'UNH', 'AVGO', 'LLY', 'TSM', 'ORCL', 'OXY']

    if len(sys.argv) > 1:
        tickers = [sys.argv[1]]

    all_results = {}

    for ticker in tickers:
        result = generate_ticker_stats(ticker)
        if result:
            all_results[ticker] = result

    # Convert booleans to strings for JSON serialization
    for ticker_data in all_results.values():
        p = ticker_data['personality']
        p['is_mean_reverter'] = str(p['is_mean_reverter'])
        p['is_momentum'] = str(p['is_momentum'])

    # Save consolidated JSON
    output_file = '/workspaces/New-test-strategy/backend/new_tickers_statistics.json'
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n{'='*80}")
    print(f"✓ Statistics saved to: {output_file}")
    print(f"{'='*80}\n")

    # Generate Python code
    print("\n" + "="*80)
    print("PYTHON CODE TO ADD TO stock_statistics.py:")
    print("="*80 + "\n")

    for ticker, data in all_results.items():
        generate_python_code(ticker, data)
        print()


if __name__ == '__main__':
    main()
