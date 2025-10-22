#!/usr/bin/env python3
"""
Gold (XAUUSD) and Silver (XAGUSD) Percentile Forward Mapping Analysis

Analyze whether gold and silver exhibit directional bias similar to equities.
Focus on day 7 predictions but also compute day 3 and day 14.
"""

import sys
sys.path.append('/workspaces/New-test-strategy/backend')

from percentile_forward_mapping import run_percentile_forward_analysis
import json

def analyze_directional_bias(result, ticker):
    """
    Analyze whether there is directional bias and positive predictive value.

    Focus on:
    1. Does high RSI percentile predict negative returns?
    2. Does low RSI percentile predict positive returns?
    3. What's the hit rate for day 7 predictions?
    4. Is there statistical significance in the directional bias?
    """
    print(f"\n{'='*80}")
    print(f"DIRECTIONAL BIAS ANALYSIS: {ticker}")
    print(f"{'='*80}\n")

    # Extract bin stats
    bin_stats = result['bin_stats']

    print("1. PERCENTILE BIN → FORWARD RETURN MAPPING (Day 7 Focus)")
    print("-" * 80)

    bias_score = 0
    total_bins = len(bin_stats)

    for bin_idx in sorted(bin_stats.keys()):
        stats = bin_stats[bin_idx]
        label = stats['bin_label']
        count = stats['count']

        # Day 7 returns (primary focus)
        mean_7d = stats['mean_return_7d']
        median_7d = stats['median_return_7d']

        # Day 3 and 14 for comparison
        mean_3d = stats['mean_return_3d']
        mean_14d = stats['mean_return_14d']

        # Determine if directional bias exists
        pct_min = stats['bin_min']
        pct_max = stats['bin_max']

        # Expected bias: low percentile → positive returns, high percentile → negative returns
        if pct_max <= 25 and mean_7d > 0:
            bias_indicator = "✅ BULLISH BIAS (oversold → positive)"
            bias_score += 1
        elif pct_min >= 75 and mean_7d < 0:
            bias_indicator = "✅ BEARISH BIAS (overbought → negative)"
            bias_score += 1
        elif pct_min >= 75 and mean_7d > 0:
            bias_indicator = "❌ REVERSE BIAS (overbought → positive)"
        elif pct_max <= 25 and mean_7d < 0:
            bias_indicator = "❌ REVERSE BIAS (oversold → negative)"
        else:
            bias_indicator = "⚪ NEUTRAL (no strong bias)"

        print(f"  {label:10s} (n={count:4d}): "
              f"3d={mean_3d:+6.2f}%, 7d={mean_7d:+6.2f}%, 14d={mean_14d:+6.2f}%  {bias_indicator}")

    print(f"\n  Directional Bias Score: {bias_score}/{total_bins} bins show expected bias")

    # Analyze extreme bins specifically
    print("\n2. EXTREME PERCENTILE ANALYSIS (Key for Trading)")
    print("-" * 80)

    # Find oversold bins (0-25 percentile)
    oversold_returns_7d = []
    oversold_count = 0
    for bin_idx, stats in bin_stats.items():
        if stats['bin_max'] <= 25:
            oversold_returns_7d.append(stats['mean_return_7d'])
            oversold_count += stats['count']

    # Find overbought bins (75-100 percentile)
    overbought_returns_7d = []
    overbought_count = 0
    for bin_idx, stats in bin_stats.items():
        if stats['bin_min'] >= 75:
            overbought_returns_7d.append(stats['mean_return_7d'])
            overbought_count += stats['count']

    avg_oversold_7d = sum(oversold_returns_7d) / len(oversold_returns_7d) if oversold_returns_7d else 0
    avg_overbought_7d = sum(overbought_returns_7d) / len(overbought_returns_7d) if overbought_returns_7d else 0

    print(f"  Oversold (0-25%ile):  Avg 7d Return = {avg_oversold_7d:+.2f}% (n={oversold_count})")
    print(f"  Overbought (75-100%ile): Avg 7d Return = {avg_overbought_7d:+.2f}% (n={overbought_count})")

    spread = avg_oversold_7d - avg_overbought_7d
    print(f"  Spread (Oversold - Overbought): {spread:+.2f}%")

    if spread > 0.5:
        print(f"  ✅ STRONG MEAN REVERSION: Oversold outperforms overbought by {spread:.2f}%")
    elif spread < -0.5:
        print(f"  ❌ MOMENTUM REGIME: Overbought continues outperforming by {abs(spread):.2f}%")
    else:
        print(f"  ⚪ WEAK SIGNAL: Spread too small for reliable trading")

    # Analyze forecast accuracy
    print("\n3. FORECAST ACCURACY METRICS (Day 7)")
    print("-" * 80)

    metrics = result.get('accuracy_metrics', {})
    metrics_7d = metrics.get('7d', {})

    if metrics_7d:
        hit_rate = metrics_7d.get('hit_rate', 0)
        sharpe = metrics_7d.get('sharpe', 0)
        correlation = metrics_7d.get('correlation', 0)
        mae = metrics_7d.get('mae', 0)

        print(f"  Hit Rate (Directional Accuracy): {hit_rate:.1f}%")
        print(f"  Sharpe Ratio: {sharpe:.2f}")
        print(f"  Correlation (Actual vs Predicted): {correlation:.3f}")
        print(f"  Mean Absolute Error: {mae:.2f}%")

        if hit_rate > 55:
            print(f"  ✅ POSITIVE PREDICTIVE VALUE: Hit rate > 55%")
        elif hit_rate > 50:
            print(f"  ⚪ WEAK PREDICTIVE VALUE: Hit rate marginally above random")
        else:
            print(f"  ❌ NO PREDICTIVE VALUE: Hit rate <= 50%")
    else:
        print("  ⚠️  No backtest metrics available")

    # Overall conclusion
    print("\n4. CONCLUSION")
    print("-" * 80)

    has_directional_bias = bias_score >= total_bins * 0.6  # 60% of bins show expected bias
    has_extreme_signal = abs(spread) > 0.5
    has_predictive_power = metrics_7d and metrics_7d.get('hit_rate', 0) > 52

    if has_directional_bias and has_extreme_signal and has_predictive_power:
        print(f"  ✅ {ticker} EXHIBITS DIRECTIONAL BIAS WITH PREDICTIVE VALUE")
        print(f"     - {bias_score}/{total_bins} bins show expected mean reversion")
        print(f"     - Oversold/Overbought spread: {spread:+.2f}%")
        print(f"     - Hit rate: {metrics_7d.get('hit_rate', 0):.1f}%")
        print(f"     → SUITABLE FOR RSI-MA PERCENTILE TRADING STRATEGY")
    elif has_directional_bias or has_extreme_signal:
        print(f"  ⚪ {ticker} SHOWS PARTIAL DIRECTIONAL BIAS")
        print(f"     - Some evidence of mean reversion but weaker than equities")
        print(f"     - May work with additional filters or in specific regimes")
        print(f"     → USE WITH CAUTION")
    else:
        print(f"  ❌ {ticker} DOES NOT EXHIBIT RELIABLE DIRECTIONAL BIAS")
        print(f"     - RSI-MA percentile is not a strong predictor")
        print(f"     - Consider alternative indicators for this asset")
        print(f"     → NOT RECOMMENDED FOR THIS STRATEGY")

    return {
        'ticker': ticker,
        'bias_score': bias_score,
        'total_bins': total_bins,
        'oversold_avg_7d': avg_oversold_7d,
        'overbought_avg_7d': avg_overbought_7d,
        'spread_7d': spread,
        'hit_rate_7d': metrics_7d.get('hit_rate', 0) if metrics_7d else 0,
        'sharpe_7d': metrics_7d.get('sharpe', 0) if metrics_7d else 0,
        'has_directional_bias': has_directional_bias,
        'has_predictive_power': has_predictive_power
    }


def main():
    """Run analysis for gold and silver."""

    # Using ETFs for better data availability: GLD (gold), SLV (silver)
    # Alternative: GC=F (gold futures), SI=F (silver futures)
    tickers = ['GLD', 'SLV']  # Gold ETF, Silver ETF
    ticker_names = {'GLD': 'Gold (GLD ETF)', 'SLV': 'Silver (SLV ETF)'}
    results_summary = []

    for ticker in tickers:
        print(f"\n{'#'*80}")
        print(f"# ANALYZING {ticker_names.get(ticker, ticker)}")
        print(f"{'#'*80}\n")

        try:
            # Run the full percentile forward mapping analysis
            result = run_percentile_forward_analysis(ticker, lookback_days=1095)

            # Analyze directional bias
            bias_analysis = analyze_directional_bias(result, ticker)
            results_summary.append(bias_analysis)

            # Save detailed results to JSON (with date conversion)
            output_file = f'/workspaces/New-test-strategy/backend/cache/{ticker}_percentile_forward.json'

            # Convert timestamps to strings for JSON serialization
            import pandas as pd
            def convert_timestamps(obj):
                if isinstance(obj, pd.Timestamp):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {k: convert_timestamps(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_timestamps(item) for item in obj]
                return obj

            result_serializable = convert_timestamps(result)

            with open(output_file, 'w') as f:
                json.dump(result_serializable, f, indent=2)
            print(f"\n  ✓ Detailed results saved to: {output_file}")

        except Exception as e:
            print(f"  ❌ ERROR analyzing {ticker}: {str(e)}")
            import traceback
            traceback.print_exc()

    # Final comparison
    print(f"\n{'='*80}")
    print("COMPARATIVE SUMMARY: GOLD vs SILVER")
    print(f"{'='*80}\n")

    print(f"{'Asset':<10s} {'Bias Score':<15s} {'Spread 7d':<15s} {'Hit Rate':<15s} {'Sharpe':<15s} {'Suitable?':<10s}")
    print("-" * 80)

    for summary in results_summary:
        ticker = summary['ticker']
        bias_str = f"{summary['bias_score']}/{summary['total_bins']}"
        spread_str = f"{summary['spread_7d']:+.2f}%"
        hit_str = f"{summary['hit_rate_7d']:.1f}%"
        sharpe_str = f"{summary['sharpe_7d']:.2f}"
        suitable = "✅ YES" if summary['has_directional_bias'] and summary['has_predictive_power'] else "❌ NO"

        print(f"{ticker:<10s} {bias_str:<15s} {spread_str:<15s} {hit_str:<15s} {sharpe_str:<15s} {suitable:<10s}")

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)


if __name__ == '__main__':
    main()
