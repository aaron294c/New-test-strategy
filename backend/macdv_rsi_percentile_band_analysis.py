"""
Enhanced MACD-V × RSI-MA Band Analysis with Dual Percentiles

This extends the existing MACD-V/RSI-MA band analysis to include:
1. MACD-V categorical percentiles (within zones)
2. RSI-MA percentiles (global)
3. Multi-dimensional band analysis using both percentiles

Provides more granular signal detection by considering:
- Absolute MACD-V level (zone)
- Relative MACD-V strength (percentile within zone)
- Relative RSI-MA level (percentile)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

try:
    from enhanced_backtester import EnhancedPerformanceMatrixBacktester
    from macdv_percentile_calculator import MACDVPercentileCalculator
except ModuleNotFoundError:
    from backend.enhanced_backtester import EnhancedPerformanceMatrixBacktester  # type: ignore
    from backend.macdv_percentile_calculator import MACDVPercentileCalculator  # type: ignore


DEFAULT_UNIVERSE = ["AAPL", "NVDA", "GOOGL", "MSFT", "META", "QQQ", "SPY", "BRK-B", "AMZN"]


# Multi-dimensional band definitions
# Each band specifies conditions for both MACD-V and RSI-MA
PERCENTILE_BANDS = [
    # Zone + MACD-V percentile + RSI-MA percentile
    {
        "name": "extreme_bullish_overbought",
        "macdv_zone": "extreme_bullish",
        "macdv_pct_range": (70, 100),
        "rsi_pct_range": (80, 100),
    },
    {
        "name": "strong_bullish_high_rsi",
        "macdv_zone": "strong_bullish",
        "macdv_pct_range": (60, 100),
        "rsi_pct_range": (70, 100),
    },
    {
        "name": "strong_bullish_low_rsi",
        "macdv_zone": "strong_bullish",
        "macdv_pct_range": (60, 100),
        "rsi_pct_range": (0, 30),
    },
    {
        "name": "weak_bullish_oversold",
        "macdv_zone": "weak_bullish",
        "macdv_pct_range": (0, 40),
        "rsi_pct_range": (0, 20),
    },
    {
        "name": "weak_bearish_oversold",
        "macdv_zone": "weak_bearish",
        "macdv_pct_range": (60, 100),  # High within weak bearish (recovering)
        "rsi_pct_range": (0, 20),
    },
    {
        "name": "strong_bearish_oversold",
        "macdv_zone": "strong_bearish",
        "macdv_pct_range": (70, 100),  # High within strong bearish (recovering)
        "rsi_pct_range": (0, 30),
    },
]


@dataclass(frozen=True)
class ReturnStats:
    n: int
    win_rate: float
    mean: float
    median: float
    sharpe: float = np.nan

    def to_dict(self) -> Dict:
        return {
            "n": int(self.n),
            "win_rate": float(self.win_rate) if np.isfinite(self.win_rate) else None,
            "mean": float(self.mean) if np.isfinite(self.mean) else None,
            "median": float(self.median) if np.isfinite(self.median) else None,
            "sharpe": float(self.sharpe) if np.isfinite(self.sharpe) else None,
        }


def _stats(returns: List[float]) -> ReturnStats:
    if not returns:
        return ReturnStats(n=0, win_rate=np.nan, mean=np.nan, median=np.nan, sharpe=np.nan)
    arr = np.asarray(returns, dtype=float)
    mean_ret = arr.mean()
    std_ret = arr.std()
    sharpe = (mean_ret / std_ret) if std_ret > 0 else np.nan
    return ReturnStats(
        n=int(arr.size),
        win_rate=float((arr > 0).mean() * 100),
        mean=float(mean_ret),
        median=float(np.median(arr)),
        sharpe=float(sharpe),
    )


def _forward_returns(close: pd.Series, entry_mask: pd.Series, horizon: int) -> List[float]:
    closes = close.to_numpy(dtype=float)
    idxs = np.flatnonzero(entry_mask.to_numpy(dtype=bool))
    out: List[float] = []
    n = len(closes)
    for i in idxs:
        j = i + horizon
        if j >= n:
            continue
        entry_px = closes[i]
        exit_px = closes[j]
        if not np.isfinite(entry_px) or entry_px <= 0 or not np.isfinite(exit_px):
            continue
        out.append(float((exit_px / entry_px - 1.0) * 100.0))
    return out


def run_dual_percentile_band_analysis(
    tickers: List[str] | None = None,
    period: str = "5y",
    pct_lookback: int = 252,
    horizon: int = 7,
    macdv_method: str = "categorical",
) -> Dict:
    """
    Run band analysis using both MACD-V and RSI-MA percentiles.

    Args:
        tickers: List of tickers to analyze
        period: Historical period to fetch
        pct_lookback: Lookback period for percentile calculation
        horizon: Forward return horizon in days
        macdv_method: MACD-V percentile method ("categorical", "global", "asymmetric")

    Returns:
        Dictionary with band analysis results
    """
    universe = [t.strip().upper() for t in (tickers or DEFAULT_UNIVERSE) if t and t.strip()]
    if not universe:
        universe = DEFAULT_UNIVERSE[:]

    # Initialize calculators
    macdv_calc = MACDVPercentileCalculator(
        fast_length=12,
        slow_length=26,
        signal_length=9,
        atr_length=26,
        percentile_lookback=pct_lookback
    )

    rsi_backtester = EnhancedPerformanceMatrixBacktester(
        tickers=universe,
        lookback_period=pct_lookback,
        rsi_length=14,
        ma_length=14,
        max_horizon=max(21, horizon),
    )

    # Results storage
    band_results: Dict[str, Dict[str, Dict]] = {}
    all_returns_by_band: Dict[str, List[float]] = {band['name']: [] for band in PERCENTILE_BANDS}

    for ticker in universe:
        print(f"Analyzing {ticker}...")

        # Fetch data
        data = rsi_backtester.fetch_data(ticker, period=period)
        if data is None or getattr(data, "empty", True):
            continue

        # Normalize column names to lowercase for MACD-V calculator
        data_lower = data.copy()
        data_lower.columns = [c.lower() for c in data_lower.columns]

        # Calculate MACD-V with percentiles
        df = macdv_calc.calculate_macdv_with_percentiles(data_lower, method=macdv_method)

        # Calculate RSI-MA with percentiles
        rsi_ma = rsi_backtester.calculate_rsi_ma_indicator(data)
        rsi_pct = rsi_backtester.calculate_percentile_ranks(rsi_ma)

        # Combine into working dataframe
        work = df.copy()
        work["rsi_percentile"] = rsi_pct
        work = work.dropna(subset=["close", "macdv_val", "macdv_percentile",
                                    "macdv_zone", "rsi_percentile"]).copy()
        work.reset_index(drop=True, inplace=True)

        close = work["close"]

        # Analyze each band
        ticker_results = {}
        for band_config in PERCENTILE_BANDS:
            band_name = band_config["name"]

            # Create mask for this band
            mask = (
                (work["macdv_zone"] == band_config["macdv_zone"]) &
                (work["macdv_percentile"] >= band_config["macdv_pct_range"][0]) &
                (work["macdv_percentile"] < band_config["macdv_pct_range"][1]) &
                (work["rsi_percentile"] >= band_config["rsi_pct_range"][0]) &
                (work["rsi_percentile"] < band_config["rsi_pct_range"][1])
            )

            # Calculate forward returns
            returns = _forward_returns(close, mask, horizon=horizon)

            # Store statistics
            stats = _stats(returns)
            ticker_results[band_name] = stats.to_dict()
            all_returns_by_band[band_name].extend(returns)

        band_results[ticker] = ticker_results

    # Calculate aggregate statistics for each band
    band_summary = {}
    for band_config in PERCENTILE_BANDS:
        band_name = band_config["name"]
        all_returns = all_returns_by_band[band_name]
        stats = _stats(all_returns)

        band_summary[band_name] = {
            "config": band_config,
            "stats": stats.to_dict(),
        }

    return {
        "params": {
            "tickers": universe,
            "period": period,
            "pct_lookback": pct_lookback,
            "horizon": horizon,
            "macdv_method": macdv_method,
            "macdv_params": {
                "fast_length": 12,
                "slow_length": 26,
                "signal_length": 9,
                "atr_length": 26,
            },
        },
        "bands": PERCENTILE_BANDS,
        "band_summary": band_summary,
        "by_ticker": band_results,
    }


def print_band_analysis_results(results: Dict) -> None:
    """Print formatted results of dual percentile band analysis."""

    print("="*100)
    print("MACD-V × RSI-MA DUAL PERCENTILE BAND ANALYSIS")
    print("="*100)

    params = results["params"]
    print(f"\nParameters:")
    print(f"  Tickers: {', '.join(params['tickers'])}")
    print(f"  Period: {params['period']}")
    print(f"  Horizon: {params['horizon']} days")
    print(f"  MACD-V Method: {params['macdv_method']}")

    print(f"\n{'='*100}")
    print("AGGREGATE RESULTS BY BAND")
    print(f"{'='*100}")

    # Sort bands by mean return
    sorted_bands = sorted(
        results["band_summary"].items(),
        key=lambda x: x[1]["stats"]["mean"] if x[1]["stats"]["mean"] is not None else -999,
        reverse=True
    )

    print(f"\n{'Band Name':<35} {'N':>6} {'Win%':>7} {'Mean%':>8} {'Median%':>8} {'Sharpe':>8}")
    print(f"{'-'*35} {'-'*6} {'-'*7} {'-'*8} {'-'*8} {'-'*8}")

    for band_name, band_data in sorted_bands:
        stats = band_data["stats"]
        config = band_data["config"]

        if stats["n"] == 0:
            continue

        print(f"{band_name:<35} {stats['n']:6d} {stats['win_rate']:6.1f}% "
              f"{stats['mean']:7.2f}% {stats['median']:7.2f}% "
              f"{stats['sharpe']:7.2f}")

        # Print band configuration
        print(f"  └─ MACD-V: {config['macdv_zone']} "
              f"({config['macdv_pct_range'][0]}-{config['macdv_pct_range'][1]}%), "
              f"RSI-MA: {config['rsi_pct_range'][0]}-{config['rsi_pct_range'][1]}%")

    print(f"\n{'='*100}")
    print("TOP 3 BEST PERFORMING BANDS")
    print(f"{'='*100}")

    for i, (band_name, band_data) in enumerate(sorted_bands[:3], 1):
        stats = band_data["stats"]
        config = band_data["config"]

        if stats["n"] == 0:
            continue

        print(f"\n#{i}. {band_name.upper()}")
        print(f"  Signals: {stats['n']}")
        print(f"  Win Rate: {stats['win_rate']:.1f}%")
        print(f"  Mean Return: {stats['mean']:.2f}%")
        print(f"  Median Return: {stats['median']:.2f}%")
        print(f"  Sharpe Ratio: {stats['sharpe']:.2f}")
        print(f"  Configuration:")
        print(f"    - MACD-V Zone: {config['macdv_zone']}")
        print(f"    - MACD-V Percentile: {config['macdv_pct_range'][0]}-{config['macdv_pct_range'][1]}%")
        print(f"    - RSI-MA Percentile: {config['rsi_pct_range'][0]}-{config['rsi_pct_range'][1]}%")

    print(f"\n{'='*100}")


if __name__ == "__main__":
    import sys

    # Parse command line arguments
    tickers = None
    if len(sys.argv) > 1:
        tickers = sys.argv[1].split(',')

    print("Running dual percentile band analysis...")
    print("This may take a few minutes...\n")

    results = run_dual_percentile_band_analysis(
        tickers=tickers,
        period="5y",
        pct_lookback=252,
        horizon=7,
        macdv_method="categorical"
    )

    print_band_analysis_results(results)

    # Save results
    import json
    from pathlib import Path

    output_dir = Path(__file__).parent.parent / "docs"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "macdv_rsi_dual_percentile_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Results saved to: {output_file}")
