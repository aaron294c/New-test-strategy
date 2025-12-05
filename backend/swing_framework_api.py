"""
Swing Framework API - Real Historical Trade Data

Provides comprehensive data for all tickers including REAL historical trades
from backtesting, not simulated/fake data.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from scipy.stats import norm
import pandas as pd
from enhanced_backtester import EnhancedPerformanceMatrixBacktester
from stock_statistics import (
    STOCK_METADATA,
    NVDA_4H_DATA, NVDA_DAILY_DATA,
    MSFT_4H_DATA, MSFT_DAILY_DATA,
    GOOGL_4H_DATA, GOOGL_DAILY_DATA,
    AAPL_4H_DATA, AAPL_DAILY_DATA,
    TSLA_4H_DATA, TSLA_DAILY_DATA,
    NFLX_4H_DATA, NFLX_DAILY_DATA
)
from percentile_forward_4h import fetch_4h_data, calculate_rsi_ma_4h

router = APIRouter(prefix="/api/swing-framework", tags=["swing-framework"])

# In-memory cache for backtest cohort statistics
# Avoids re-running expensive backtests on every current-state request
_cohort_stats_cache: Dict = {}
_cache_timestamp: datetime | None = None
_cache_ttl_seconds = 3600  # 1 hour TTL


def convert_bins_to_dict(bin_data: Dict) -> Dict:
    """Convert BinStatistics objects to dictionaries"""
    result = {}
    for bin_range, stats in bin_data.items():
        result[bin_range] = {
            "bin_range": bin_range,
            "mean": float(stats.mean),
            "std": float(stats.std),
            "median": float(stats.median),
            "sample_size": int(stats.sample_size),
            "t_score": float(stats.t_score),
            "is_significant": bool(stats.is_significant),
            "significance_level": str(stats.significance_level.name) if hasattr(stats.significance_level, 'name') else str(stats.significance_level),
            "upside": float(stats.upside),
            "downside": float(stats.downside),
            "percentile_5th": float(stats.percentile_5th),
            "percentile_95th": float(stats.percentile_95th),
            "confidence_interval_95": [float(stats.confidence_interval_95[0]), float(stats.confidence_interval_95[1])],
            "se": float(stats.se)
        }
    return result


# Mapping of available 4H bin statistics for quick lookup
FOUR_H_BIN_MAP: Dict[str, Dict] = {
    "NVDA": NVDA_4H_DATA,
    "MSFT": MSFT_4H_DATA,
    "GOOGL": GOOGL_4H_DATA,
    "AAPL": AAPL_4H_DATA,
    "TSLA": TSLA_4H_DATA,
    "NFLX": NFLX_4H_DATA,
}

FOUR_H_DEFAULT_HOLDING_DAYS = 4.0  # Approximate 4H holding horizon (in days) for expectancy display


def estimate_win_rate_from_bin(mean: float, std: float) -> float:
    """Approximate win rate from bin statistics using a normal assumption."""
    if std <= 0:
        return 1.0 if mean > 0 else 0.0
    try:
        return float(norm.sf(0, loc=mean, scale=std))
    except Exception:
        return 0.5


def bin_to_cohort_stats(bin_stats) -> Dict[str, float]:
    """Convert BinStatistics to cohort stats compatible with live expectancy."""
    return {
        "count": int(bin_stats.sample_size),
        "win_rate": estimate_win_rate_from_bin(float(bin_stats.mean), float(bin_stats.std)),
        "avg_return": float(bin_stats.mean),
        "avg_holding_days": FOUR_H_DEFAULT_HOLDING_DAYS
    }


def combine_bins(bin_stats_list: List) -> Optional[Dict[str, float]]:
    """Combine multiple BinStatistics entries into weighted cohort stats."""
    if not bin_stats_list:
        return None

    total_samples = sum(b.sample_size for b in bin_stats_list)
    if total_samples == 0:
        return None

    weighted_return = sum(float(b.mean) * b.sample_size for b in bin_stats_list) / total_samples
    weighted_win_rate = sum(
        estimate_win_rate_from_bin(float(b.mean), float(b.std)) * b.sample_size for b in bin_stats_list
    ) / total_samples

    return {
        "count": int(total_samples),
        "win_rate": float(weighted_win_rate),
        "avg_return": float(weighted_return),
        "avg_holding_days": FOUR_H_DEFAULT_HOLDING_DAYS
    }


def get_4h_cohort_stats_from_bins(ticker: str) -> Optional[Dict[str, Dict[str, float]]]:
    """Build cohort stats from pre-computed 4H bin data when available."""
    bin_data = FOUR_H_BIN_MAP.get(ticker)
    if not bin_data:
        return None

    cohort_stats = {
        "cohort_extreme_low": bin_to_cohort_stats(bin_data["0-5"]) if "0-5" in bin_data else None,
        "cohort_low": bin_to_cohort_stats(bin_data["5-15"]) if "5-15" in bin_data else None,
        "cohort_medium_low": bin_to_cohort_stats(bin_data["15-25"]) if "15-25" in bin_data else None,
        "cohort_medium": bin_to_cohort_stats(bin_data["25-50"]) if "25-50" in bin_data else None,
        "cohort_medium_high": bin_to_cohort_stats(bin_data["50-75"]) if "50-75" in bin_data else None,
        "cohort_high": bin_to_cohort_stats(bin_data["75-85"]) if "75-85" in bin_data else None,
        "cohort_extreme_high": combine_bins([b for k, b in bin_data.items() if k in ["85-95", "95-100"]])
    }

    cohort_all_bins = [b for b in bin_data.values() if getattr(b, "sample_size", 0) > 0]
    cohort_stats["cohort_all"] = combine_bins(cohort_all_bins)

    return cohort_stats


def get_percentile_cohort(percentile: float) -> tuple[str, str]:
    """Map percentile to cohort identifier and human-readable zone label."""
    if percentile <= 5.0:
        return "extreme_low", "≤5th percentile (Extreme Low)"
    if percentile <= 15.0:
        return "low", "5-15th percentile (Low)"
    if percentile <= 30.0:
        return "medium_low", "15-30th percentile (Medium Low)"
    if percentile <= 50.0:
        return "medium", "30-50th percentile (Medium)"
    if percentile <= 70.0:
        return "medium_high", "50-70th percentile (Medium High)"
    if percentile <= 85.0:
        return "high", "70-85th percentile (High)"
    return "extreme_high", "85-100th percentile (Extreme High)"


def compute_4h_cohort_stats_from_data(
    backtester: EnhancedPerformanceMatrixBacktester,
    data_frame: pd.DataFrame,
    percentile_ranks: pd.Series
) -> Dict[str, Dict[str, float]]:
    """Compute cohort stats directly from 4H data as a fallback when bin data is unavailable."""
    entry_events = backtester.find_entry_events_enhanced(
        percentile_ranks,
        data_frame['Close'],
        threshold=100.0
    )

    trades: List[Dict] = []
    for event in entry_events:
        entry_date = event['entry_date']
        if entry_date not in data_frame.index:
            continue

        entry_idx = data_frame.index.get_loc(entry_date)
        exit_idx, _ = find_exit_point(
            data_frame,
            percentile_ranks,
            entry_idx,
            max_days=21,
            exit_percentile=50.0,
            stop_loss_pct=2.0
        )

        exit_date = data_frame.index[exit_idx]
        exit_price = data_frame.iloc[exit_idx]['Close']
        entry_price = event['entry_price']
        entry_pct = float(event['entry_percentile'])
        percentile_cohort, _ = get_percentile_cohort(entry_pct)

        holding_days = max((exit_date - entry_date).total_seconds() / 86400, 0.1)

        trades.append({
            "entry_date": entry_date.strftime("%Y-%m-%d %H:%M") if hasattr(entry_date, "strftime") else str(entry_date),
            "exit_date": exit_date.strftime("%Y-%m-%d %H:%M") if hasattr(exit_date, "strftime") else str(exit_date),
            "entry_price": float(entry_price),
            "exit_price": float(exit_price),
            "entry_percentile": entry_pct,
            "exit_percentile": float(percentile_ranks.iloc[exit_idx]),
            "holding_days": holding_days,
            "return_pct": float((exit_price - entry_price) / entry_price * 100),
            "regime": "mean_reversion" if entry_pct <= 50.0 else "momentum",
            "percentile_cohort": percentile_cohort
        })

    # Build cohort buckets
    cohorts: Dict[str, List[Dict]] = {
        "extreme_low": [],
        "low": [],
        "medium_low": [],
        "medium": [],
        "medium_high": [],
        "high": [],
        "extreme_high": []
    }

    for trade in trades:
        cohort = trade.get("percentile_cohort")
        if cohort in cohorts:
            cohorts[cohort].append(trade)

    # Helper to convert list of trades to stats
    def stats_for(trade_list: List[Dict]) -> Optional[Dict[str, float]]:
        if not trade_list:
            return None
        agg = calculate_backtest_stats(trade_list)
        return {
            "count": agg.get("total_trades", 0),
            "win_rate": agg.get("win_rate", 0.0),
            "avg_return": agg.get("avg_return", 0.0),
            "avg_holding_days": agg.get("avg_holding_days", FOUR_H_DEFAULT_HOLDING_DAYS)
        }

    all_stats = calculate_backtest_stats(trades)
    return {
        "cohort_extreme_low": stats_for(cohorts["extreme_low"]),
        "cohort_low": stats_for(cohorts["low"]),
        "cohort_medium_low": stats_for(cohorts["medium_low"]),
        "cohort_medium": stats_for(cohorts["medium"]),
        "cohort_medium_high": stats_for(cohorts["medium_high"]),
        "cohort_high": stats_for(cohorts["high"]),
        "cohort_extreme_high": stats_for(cohorts["extreme_high"]),
        "cohort_all": {
            "count": all_stats.get("total_trades", 0),
            "win_rate": all_stats.get("win_rate", 0.0),
            "avg_return": all_stats.get("avg_return", 0.0),
            "avg_holding_days": all_stats.get("avg_holding_days", FOUR_H_DEFAULT_HOLDING_DAYS)
        }
    }


def find_exit_point(
    data: pd.DataFrame,
    percentiles: pd.Series,
    entry_idx: int,
    max_days: int = 21,
    exit_percentile: float = 50.0,
    stop_loss_pct: float = 2.0
) -> tuple:
    """
    Find actual exit point from real historical data

    Returns: (exit_idx, exit_reason)
    exit_reason: 'target', 'stop_loss', 'max_days', 'end_of_data'
    """
    entry_price = data.iloc[entry_idx]['Close']

    for i in range(1, max_days + 1):
        exit_idx = entry_idx + i

        if exit_idx >= len(data):
            return entry_idx + i - 1, 'end_of_data'

        exit_price = data.iloc[exit_idx]['Close']
        return_pct = (exit_price - entry_price) / entry_price * 100

        # Check stop loss
        if return_pct <= -stop_loss_pct:
            return exit_idx, 'stop_loss'

        # Check target (percentile >= 50%)
        if percentiles.iloc[exit_idx] >= exit_percentile:
            return exit_idx, 'target'

    # Max holding period reached
    return entry_idx + max_days, 'max_days'


async def get_cached_cohort_stats() -> Dict:
    """
    Get cohort statistics from cache or compute if cache is stale/empty
    Returns: Dict[ticker] = {cohort_extreme_low: {...}, cohort_low: {...}}
    """
    global _cohort_stats_cache, _cache_timestamp

    # Check if cache is valid
    now = datetime.now(timezone.utc)
    cache_valid = (
        _cache_timestamp is not None
        and (now - _cache_timestamp).total_seconds() < _cache_ttl_seconds
        and _cohort_stats_cache
    )

    if cache_valid:
        print(f"  Using cached cohort stats (age: {(now - _cache_timestamp).total_seconds():.0f}s)")
        return _cohort_stats_cache

    # Cache miss or stale - fetch full backtest data
    print("  Cache miss - fetching fresh cohort statistics...")
    all_data = await get_swing_framework_data()

    # Extract ALL cohort stats (all percentile ranges)
    cohort_stats = {}
    for ticker, ticker_data in all_data['tickers'].items():
        backtest_stats = ticker_data.get('backtest_stats', {})
        cohort_stats[ticker] = {
            'cohort_extreme_low': backtest_stats.get('cohort_extreme_low'),
            'cohort_low': backtest_stats.get('cohort_low'),
            'cohort_medium_low': backtest_stats.get('cohort_medium_low'),
            'cohort_medium': backtest_stats.get('cohort_medium'),
            'cohort_medium_high': backtest_stats.get('cohort_medium_high'),
            'cohort_high': backtest_stats.get('cohort_high'),
            'cohort_extreme_high': backtest_stats.get('cohort_extreme_high'),
            'cohort_all': backtest_stats.get('cohort_all'),
            'metadata': ticker_data.get('metadata', {})
        }

    # Update cache
    _cohort_stats_cache = cohort_stats
    _cache_timestamp = now
    print(f"  ✓ Cached cohort stats for {len(cohort_stats)} tickers")

    return cohort_stats


def calculate_backtest_stats(trades: List[Dict]) -> Dict:
    """Calculate aggregate statistics from trade list with RSI-MA cohort breakdown"""
    if not trades:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "avg_return": 0.0,
            "avg_holding_days": 0.0,
            "total_return": 0.0
        }

    wins = [t for t in trades if t['return_pct'] > 0]
    losses = [t for t in trades if t['return_pct'] < 0]

    total_return = sum(t['return_pct'] for t in trades)

    # RSI-MA Cohort Analysis - All percentile ranges
    extreme_low_trades = [t for t in trades if t.get('percentile_cohort') == 'extreme_low']  # 0-5%
    low_trades = [t for t in trades if t.get('percentile_cohort') == 'low']  # 5-15%

    # Additional cohorts for all percentile ranges
    def get_cohort_for_percentile(pct):
        """Determine cohort based on entry percentile"""
        if pct <= 5.0:
            return 'extreme_low'
        elif pct <= 15.0:
            return 'low'
        elif pct <= 30.0:
            return 'medium_low'
        elif pct <= 50.0:
            return 'medium'
        elif pct <= 70.0:
            return 'medium_high'
        elif pct <= 85.0:
            return 'high'
        else:
            return 'extreme_high'

    # Categorize all trades into cohorts
    cohort_trades = {}
    for t in trades:
        cohort = t.get('percentile_cohort')
        if not cohort and 'entry_percentile' in t:
            cohort = get_cohort_for_percentile(t['entry_percentile'])
        if cohort:
            if cohort not in cohort_trades:
                cohort_trades[cohort] = []
            cohort_trades[cohort].append(t)

    def cohort_stats(cohort_trades_list):
        if not cohort_trades_list:
            return None
        cohort_wins = [t for t in cohort_trades_list if t['return_pct'] > 0]
        return {
            "count": len(cohort_trades_list),
            "win_rate": len(cohort_wins) / len(cohort_trades_list),
            "avg_return": sum(t['return_pct'] for t in cohort_trades_list) / len(cohort_trades_list),
            "avg_holding_days": sum(t['holding_days'] for t in cohort_trades_list) / len(cohort_trades_list)
        }

    return {
        "total_trades": len(trades),
        "win_rate": len(wins) / len(trades) if trades else 0.0,
        "avg_return": total_return / len(trades) if trades else 0.0,
        "avg_win": sum(t['return_pct'] for t in wins) / len(wins) if wins else 0.0,
        "avg_loss": sum(t['return_pct'] for t in losses) / len(losses) if losses else 0.0,
        "avg_holding_days": sum(t['holding_days'] for t in trades) / len(trades) if trades else 0.0,
        "total_return": total_return,
        "max_return": max(t['return_pct'] for t in trades) if trades else 0.0,
        "min_return": min(t['return_pct'] for t in trades) if trades else 0.0,
        # RSI-MA Percentile Cohort Breakdown - All ranges
        "cohort_extreme_low": cohort_stats(cohort_trades.get('extreme_low', [])),  # 0-5%
        "cohort_low": cohort_stats(cohort_trades.get('low', [])),  # 5-15%
        "cohort_medium_low": cohort_stats(cohort_trades.get('medium_low', [])),  # 15-30%
        "cohort_medium": cohort_stats(cohort_trades.get('medium', [])),  # 30-50%
        "cohort_medium_high": cohort_stats(cohort_trades.get('medium_high', [])),  # 50-70%
        "cohort_high": cohort_stats(cohort_trades.get('high', [])),  # 70-85%
        "cohort_extreme_high": cohort_stats(cohort_trades.get('extreme_high', [])),  # 85-100%
        "cohort_all": cohort_stats(trades)  # Fallback - all trades
    }


@router.get("/all-tickers")
async def get_swing_framework_data():
    """
    Get comprehensive data for all tickers including REAL historical trades

    Returns:
    - Stock metadata
    - Bin statistics (4H and Daily)
    - REAL historical trades from backtesting (not simulated!)
    - Aggregate statistics
    """

    # Include both stocks and market indices
    tickers = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "GOOGL", "TSLA", "NFLX", "AMZN"]
    results = {}

    bin_data_map = {
        "NVDA": (NVDA_4H_DATA, NVDA_DAILY_DATA),
        "MSFT": (MSFT_4H_DATA, MSFT_DAILY_DATA),
        "GOOGL": (GOOGL_4H_DATA, GOOGL_DAILY_DATA),
        "AAPL": (AAPL_4H_DATA, AAPL_DAILY_DATA),
        "TSLA": (TSLA_4H_DATA, TSLA_DAILY_DATA),
        "NFLX": (NFLX_4H_DATA, NFLX_DAILY_DATA),
        # Indices and stocks without pre-computed bin data - will use real-time calculation
        "SPY": (None, None),
        "QQQ": (None, None),
        "AMZN": (None, None)
    }

    for ticker in tickers:
        try:
            print(f"Processing {ticker}...")

            # Get metadata
            metadata = STOCK_METADATA.get(ticker)
            if not metadata:
                print(f"  No metadata for {ticker}, skipping")
                continue

            # Get bin statistics (optional for indices - they compute dynamically)
            bins_4h, bins_daily = bin_data_map.get(ticker, (None, None))
            # For indices like SPY/QQQ, bins_4h will be None - they don't need pre-computed bin data
            # Individual stocks use pre-computed bin data for efficiency

            # Initialize backtester with REAL historical data
            try:
                backtester = EnhancedPerformanceMatrixBacktester(
                    tickers=[ticker],
                    lookback_period=500,
                    rsi_length=14,
                    ma_length=14,
                    max_horizon=21
                )

                # Fetch REAL historical price data
                data = backtester.fetch_data(ticker)
                if data.empty:
                    print(f"  No price data for {ticker}, using static bins only")
                    historical_trades = []
                else:
                    # Calculate RSI-MA indicator
                    indicator = backtester.calculate_rsi_ma_indicator(data)
                    percentile_ranks = backtester.calculate_percentile_ranks(indicator)

                    # Find REAL entry events across ALL percentile ranges (not just 0-15%)
                    entry_events = backtester.find_entry_events_enhanced(
                        percentile_ranks,
                        data['Close'],
                        threshold=100.0  # Capture ALL percentiles (0-100%)
                    )

                    print(f"  Found {len(entry_events)} total entry events across all percentiles")

                    # Separate into ALL percentile cohorts for comprehensive analysis
                    cohort_events = {
                        'extreme_low': [e for e in entry_events if e['entry_percentile'] <= 5.0],
                        'low': [e for e in entry_events if 5.0 < e['entry_percentile'] <= 15.0],
                        'medium_low': [e for e in entry_events if 15.0 < e['entry_percentile'] <= 30.0],
                        'medium': [e for e in entry_events if 30.0 < e['entry_percentile'] <= 50.0],
                        'medium_high': [e for e in entry_events if 50.0 < e['entry_percentile'] <= 70.0],
                        'high': [e for e in entry_events if 70.0 < e['entry_percentile'] <= 85.0],
                        'extreme_high': [e for e in entry_events if 85.0 < e['entry_percentile'] <= 100.0]
                    }

                    for cohort_name, events in cohort_events.items():
                        print(f"    {cohort_name}: {len(events)} events")

                    # Use ALL events - no artificial sampling
                    # Each cohort will have its natural sample size based on historical frequency
                    sampled_events = entry_events

                    print(f"  Using ALL {len(sampled_events)} trades across all percentile ranges (natural distribution)")

                    # Generate REAL trades from historical data
                    historical_trades = []
                    for event in sampled_events:
                        entry_date = event['entry_date']
                        entry_idx = data.index.get_loc(entry_date)

                        # Find actual exit point from REAL data
                        exit_idx, exit_reason = find_exit_point(
                            data,
                            percentile_ranks,
                            entry_idx,
                            max_days=21,
                            exit_percentile=50.0,
                            stop_loss_pct=2.0
                        )

                        exit_date = data.index[exit_idx]
                        exit_price = data.iloc[exit_idx]['Close']
                        exit_percentile = percentile_ranks.iloc[exit_idx]

                        # Determine percentile cohort for RSI-MA tracking (ALL ranges)
                        entry_pct = float(event['entry_percentile'])
                        if entry_pct <= 5.0:
                            cohort = "extreme_low"
                        elif entry_pct <= 15.0:
                            cohort = "low"
                        elif entry_pct <= 30.0:
                            cohort = "medium_low"
                        elif entry_pct <= 50.0:
                            cohort = "medium"
                        elif entry_pct <= 70.0:
                            cohort = "medium_high"
                        elif entry_pct <= 85.0:
                            cohort = "high"
                        else:
                            cohort = "extreme_high"

                        trade = {
                            "entry_date": entry_date.strftime("%Y-%m-%d") if hasattr(entry_date, 'strftime') else str(entry_date),
                            "exit_date": exit_date.strftime("%Y-%m-%d") if hasattr(exit_date, 'strftime') else str(exit_date),
                            "entry_price": float(event['entry_price']),
                            "exit_price": float(exit_price),
                            "entry_percentile": entry_pct,
                            "exit_percentile": float(exit_percentile),
                            "holding_days": int((exit_date - entry_date).days) if hasattr((exit_date - entry_date), 'days') else 1,
                            "return_pct": float((exit_price - event['entry_price']) / event['entry_price'] * 100),
                            "regime": "mean_reversion" if metadata.is_mean_reverter else "momentum",
                            "exit_reason": exit_reason,
                            "percentile_cohort": cohort  # Track which RSI-MA cohort
                        }
                        historical_trades.append(trade)

                    print(f"  Generated {len(historical_trades)} real trades")

            except Exception as e:
                print(f"  Error running backtest for {ticker}: {e}")
                historical_trades = []

            # Compile response
            results[ticker] = {
                "metadata": {
                    "ticker": metadata.ticker,
                    "name": metadata.name,
                    "personality": metadata.personality,
                    "reliability_4h": metadata.reliability_4h,
                    "reliability_daily": metadata.reliability_daily,
                    "tradeable_4h_zones": metadata.tradeable_4h_zones,
                    "dead_zones_4h": metadata.dead_zones_4h,
                    "best_4h_bin": metadata.best_4h_bin,
                    "best_4h_t_score": float(metadata.best_4h_t_score),
                    "ease_rating": int(metadata.ease_rating),
                    "is_mean_reverter": metadata.is_mean_reverter,
                    "is_momentum": metadata.is_momentum,
                    "volatility_level": metadata.volatility_level,
                    "entry_guidance": metadata.entry_guidance,
                    "avoid_guidance": metadata.avoid_guidance,
                    "special_notes": metadata.special_notes
                },
                "bins_4h": convert_bins_to_dict(bins_4h) if bins_4h else {},
                "bins_daily": convert_bins_to_dict(bins_daily) if bins_daily else {},
                "historical_trades": historical_trades,
                "backtest_stats": calculate_backtest_stats(historical_trades)
            }

            print(f"  ✓ {ticker} complete")

        except Exception as e:
            print(f"  Error processing {ticker}: {e}")
            import traceback
            traceback.print_exc()
            continue

    if not results:
        raise HTTPException(status_code=500, detail="Failed to process any tickers")

    return {
        "snapshot_timestamp": datetime.now(timezone.utc).isoformat(),
        "tickers": results,
        "summary": {
            "total_tickers": len(results),
            "tickers_with_trades": sum(1 for t in results.values() if t['historical_trades']),
            "total_trades": sum(len(t['historical_trades']) for t in results.values())
        }
    }


@router.get("/current-state-indices")
async def get_current_indices_state():
    """
    Get CURRENT RSI-MA percentile and live risk-adjusted expectancy for SPY and QQQ
    Shows real-time buy opportunities for market indices based on current market state

    OPTIMIZED: Uses cached cohort statistics, only fetches current percentiles
    Separate endpoint to allow modular dashboard views comparing "Stocks vs SPY vs QQQ"
    """
    indices = ["SPY", "QQQ"]

    # Get cached cohort stats (fast - uses cache after first call)
    print("Fetching indices cohort statistics...")
    cohort_stats_cache = await get_cached_cohort_stats()
    print("✓ Indices cohort stats ready")

    current_states = []

    # Fetch current percentiles for indices
    print("Fetching current percentiles for SPY and QQQ...")
    for ticker in indices:
        try:
            # Get cached cohort data for this index
            ticker_cohort_data = cohort_stats_cache.get(ticker, {})
            if not ticker_cohort_data:
                print(f"  No cohort data for {ticker}, skipping")
                continue

            metadata_dict = ticker_cohort_data.get('metadata', {})

            # Initialize backtester ONLY to get current percentile (fast)
            backtester = EnhancedPerformanceMatrixBacktester(
                tickers=[ticker],
                lookback_period=500,
                rsi_length=14,
                ma_length=14,
                max_horizon=21
            )

            # Fetch latest data (uses yfinance cache)
            data = backtester.fetch_data(ticker)
            if data.empty:
                continue

            # Calculate current RSI-MA indicator and percentile (fast operation)
            indicator = backtester.calculate_rsi_ma_indicator(data)
            percentile_ranks = backtester.calculate_percentile_ranks(indicator)

            # Get MOST RECENT (current) percentile
            current_percentile = float(percentile_ranks.iloc[-1])
            current_price = float(data['Close'].iloc[-1])
            current_date = data.index[-1].strftime("%Y-%m-%d")

            # Get metadata for regime
            metadata = STOCK_METADATA.get(ticker)
            if not metadata:
                continue

            regime = "mean_reversion" if metadata.is_mean_reverter else "momentum"

            # Determine entry zone and expected performance from historical data
            in_extreme_low = current_percentile <= 5.0
            in_low = 5.0 < current_percentile <= 15.0
            in_entry_zone = in_extreme_low or in_low

            # Determine percentile cohort for all ranges
            if current_percentile <= 5.0:
                percentile_cohort = "extreme_low"
                zone_label = "≤5th percentile (Extreme Low)"
            elif current_percentile <= 15.0:
                percentile_cohort = "low"
                zone_label = "5-15th percentile (Low)"
            elif current_percentile <= 30.0:
                percentile_cohort = "medium_low"
                zone_label = "15-30th percentile (Medium Low)"
            elif current_percentile <= 50.0:
                percentile_cohort = "medium"
                zone_label = "30-50th percentile (Medium)"
            elif current_percentile <= 70.0:
                percentile_cohort = "medium_high"
                zone_label = "50-70th percentile (Medium High)"
            elif current_percentile <= 85.0:
                percentile_cohort = "high"
                zone_label = "70-85th percentile (High)"
            else:
                percentile_cohort = "extreme_high"
                zone_label = "85-100th percentile (Extreme High)"

            # Get historical cohort performance from CACHE for ALL cohorts
            cohort_performance = ticker_cohort_data.get(f'cohort_{percentile_cohort}')

            # Fallback to 'cohort_all' if specific cohort has no data
            if not cohort_performance:
                cohort_performance = ticker_cohort_data.get('cohort_all')

            # Calculate live risk-adjusted expectancy (ALWAYS show data, even if not in entry zone)
            if cohort_performance:
                expected_win_rate = cohort_performance['win_rate']
                expected_return = cohort_performance['avg_return']
                expected_holding_days = cohort_performance['avg_holding_days']
                expected_return_per_day = expected_return / expected_holding_days if expected_holding_days > 0 else 0

                # Simple risk-adjusted expectancy (return / volatility proxy)
                volatility_multiplier = {"Low": 1.0, "Medium": 1.5, "High": 2.0}.get(metadata.volatility_level, 1.5)
                risk_adjusted_expectancy = expected_return / volatility_multiplier

                live_expectancy = {
                    "expected_win_rate": expected_win_rate,
                    "expected_return_pct": expected_return,
                    "expected_holding_days": expected_holding_days,
                    "expected_return_per_day_pct": expected_return_per_day,
                    "risk_adjusted_expectancy_pct": risk_adjusted_expectancy,
                    "sample_size": cohort_performance['count']
                }
            else:
                # No data for this cohort - return zeros
                live_expectancy = {
                    "expected_win_rate": 0.0,
                    "expected_return_pct": 0.0,
                    "expected_holding_days": 0.0,
                    "expected_return_per_day_pct": 0.0,
                    "risk_adjusted_expectancy_pct": 0.0,
                    "sample_size": 0
                }

            current_states.append({
                "ticker": ticker,
                "name": metadata.name,
                "current_date": current_date,
                "current_price": current_price,
                "current_percentile": current_percentile,
                "percentile_cohort": percentile_cohort,
                "zone_label": zone_label,
                "in_entry_zone": in_entry_zone,
                "regime": regime,
                "is_mean_reverter": metadata.is_mean_reverter,
                "is_momentum": metadata.is_momentum,
                "volatility_level": metadata.volatility_level,
                "live_expectancy": live_expectancy  # Expected performance if entering NOW
            })

        except Exception as e:
            print(f"  Error getting current state for {ticker}: {e}")
            continue

    # Sort by current percentile (lowest first = best buy opportunities)
    current_states.sort(key=lambda x: x['current_percentile'])

    print(f"✓ Indices market state ready: {len(current_states)} indices processed")

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "market_state": current_states,
        "summary": {
            "total_tickers": len(current_states),
            "in_entry_zone": sum(1 for s in current_states if s['in_entry_zone']),
            "extreme_low_opportunities": sum(1 for s in current_states if s['percentile_cohort'] == 'extreme_low'),
            "low_opportunities": sum(1 for s in current_states if s['percentile_cohort'] == 'low')
        }
    }


@router.get("/current-state")
async def get_current_market_state():
    """
    Get CURRENT RSI-MA percentile and live risk-adjusted expectancy for all tickers (stocks + indices)
    Shows real-time buy opportunities based on current market state

    Now includes SPY and QQQ market indices integrated into the same list as stocks

    OPTIMIZED: Uses cached cohort statistics, only fetches current percentiles
    """
    tickers = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "GOOGL", "TSLA", "NFLX", "AMZN"]

    # Get cached cohort stats (fast - uses cache after first call)
    print("Fetching cohort statistics...")
    cohort_stats_cache = await get_cached_cohort_stats()
    print("✓ Cohort stats ready")

    current_states = []

    # Parallel processing: fetch current percentiles for all tickers
    print("Fetching current percentiles...")
    for ticker in tickers:
        try:
            # Get cached cohort data for this ticker
            ticker_cohort_data = cohort_stats_cache.get(ticker, {})
            if not ticker_cohort_data:
                print(f"  No cohort data for {ticker}, skipping")
                continue

            metadata_dict = ticker_cohort_data.get('metadata', {})

            # Initialize backtester ONLY to get current percentile (fast)
            backtester = EnhancedPerformanceMatrixBacktester(
                tickers=[ticker],
                lookback_period=500,
                rsi_length=14,
                ma_length=14,
                max_horizon=21
            )

            # Fetch latest data (uses yfinance cache)
            data = backtester.fetch_data(ticker)
            if data.empty:
                continue

            # Calculate current RSI-MA indicator and percentile (fast operation)
            indicator = backtester.calculate_rsi_ma_indicator(data)
            percentile_ranks = backtester.calculate_percentile_ranks(indicator)

            # Get MOST RECENT (current) percentile
            current_percentile = float(percentile_ranks.iloc[-1])
            current_price = float(data['Close'].iloc[-1])
            current_date = data.index[-1].strftime("%Y-%m-%d")

            # Get metadata for regime
            metadata = STOCK_METADATA.get(ticker)
            if not metadata:
                continue

            regime = "mean_reversion" if metadata.is_mean_reverter else "momentum"

            # Determine entry zone and expected performance from historical data
            in_extreme_low = current_percentile <= 5.0
            in_low = 5.0 < current_percentile <= 15.0
            in_entry_zone = in_extreme_low or in_low

            # Determine percentile cohort for all ranges
            if current_percentile <= 5.0:
                percentile_cohort = "extreme_low"
                zone_label = "≤5th percentile (Extreme Low)"
            elif current_percentile <= 15.0:
                percentile_cohort = "low"
                zone_label = "5-15th percentile (Low)"
            elif current_percentile <= 30.0:
                percentile_cohort = "medium_low"
                zone_label = "15-30th percentile (Medium Low)"
            elif current_percentile <= 50.0:
                percentile_cohort = "medium"
                zone_label = "30-50th percentile (Medium)"
            elif current_percentile <= 70.0:
                percentile_cohort = "medium_high"
                zone_label = "50-70th percentile (Medium High)"
            elif current_percentile <= 85.0:
                percentile_cohort = "high"
                zone_label = "70-85th percentile (High)"
            else:
                percentile_cohort = "extreme_high"
                zone_label = "85-100th percentile (Extreme High)"

            # Get historical cohort performance from CACHE for ALL cohorts
            cohort_performance = ticker_cohort_data.get(f'cohort_{percentile_cohort}')

            # Fallback to 'cohort_all' if specific cohort has no data
            if not cohort_performance:
                cohort_performance = ticker_cohort_data.get('cohort_all')

            # Calculate live risk-adjusted expectancy (ALWAYS show data, even if not in entry zone)
            if cohort_performance:
                expected_win_rate = cohort_performance['win_rate']
                expected_return = cohort_performance['avg_return']
                expected_holding_days = cohort_performance['avg_holding_days']
                expected_return_per_day = expected_return / expected_holding_days if expected_holding_days > 0 else 0

                # Simple risk-adjusted expectancy (return / volatility proxy)
                volatility_multiplier = {"Low": 1.0, "Medium": 1.5, "High": 2.0}.get(metadata.volatility_level, 1.5)
                risk_adjusted_expectancy = expected_return / volatility_multiplier

                live_expectancy = {
                    "expected_win_rate": expected_win_rate,
                    "expected_return_pct": expected_return,
                    "expected_holding_days": expected_holding_days,
                    "expected_return_per_day_pct": expected_return_per_day,
                    "risk_adjusted_expectancy_pct": risk_adjusted_expectancy,
                    "sample_size": cohort_performance['count']
                }
            else:
                # No data for this cohort - return zeros
                live_expectancy = {
                    "expected_win_rate": 0.0,
                    "expected_return_pct": 0.0,
                    "expected_holding_days": 0.0,
                    "expected_return_per_day_pct": 0.0,
                    "risk_adjusted_expectancy_pct": 0.0,
                    "sample_size": 0
                }

            current_states.append({
                "ticker": ticker,
                "name": metadata.name,
                "current_date": current_date,
                "current_price": current_price,
                "current_percentile": current_percentile,
                "percentile_cohort": percentile_cohort,
                "zone_label": zone_label,
                "in_entry_zone": in_entry_zone,
                "regime": regime,
                "is_mean_reverter": metadata.is_mean_reverter,
                "is_momentum": metadata.is_momentum,
                "volatility_level": metadata.volatility_level,
                "live_expectancy": live_expectancy  # Expected performance if entering NOW
            })

        except Exception as e:
            print(f"  Error getting current state for {ticker}: {e}")
            continue

    # Sort by current percentile (lowest first = best buy opportunities)
    current_states.sort(key=lambda x: x['current_percentile'])

    print(f"✓ Current market state ready: {len(current_states)} tickers processed")

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "market_state": current_states,
        "summary": {
            "total_tickers": len(current_states),
            "in_entry_zone": sum(1 for s in current_states if s['in_entry_zone']),
            "extreme_low_opportunities": sum(1 for s in current_states if s['percentile_cohort'] == 'extreme_low'),
            "low_opportunities": sum(1 for s in current_states if s['percentile_cohort'] == 'low')
        }
    }


@router.get("/current-state-4h")
async def get_current_market_state_4h():
    """
    Get CURRENT RSI-MA percentile and live expectancy for the 4-hour timeframe.
    Uses pre-computed 4H bin statistics when available and falls back to on-the-fly
    cohort calculations from 4H price data.
    """
    tickers = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "GOOGL", "TSLA", "NFLX", "AMZN"]
    current_states = []

    print("Fetching 4H current percentiles...")
    # Daily cohort cache as a final fallback if 4H data is unavailable
    daily_cohort_cache = await get_cached_cohort_stats()

    for ticker in tickers:
        try:
            metadata = STOCK_METADATA.get(ticker)
            if not metadata:
                print(f"  No metadata for {ticker}, skipping")
                continue

            data_for_current = None
            data_source = "4h"

            backtester = EnhancedPerformanceMatrixBacktester(
                tickers=[ticker],
                lookback_period=252,  # 4H: use ~42 days of bars so percentile ranks fill
                rsi_length=14,
                ma_length=14,
                max_horizon=21
            )

            try:
                data_for_current = fetch_4h_data(ticker, lookback_days=365)
                if data_for_current.empty:
                    raise ValueError("empty 4H data")
            except Exception as e:
                print(f"  4H data fetch failed for {ticker}: {e}. Falling back to daily data.")
                data_source = "daily_fallback"
                data_for_current = backtester.fetch_data(ticker)
                if data_for_current.empty:
                    print(f"  Fallback daily data also empty for {ticker}, skipping")
                    continue

            indicator = calculate_rsi_ma_4h(data_for_current) if data_source == "4h" else backtester.calculate_rsi_ma_indicator(data_for_current)
            percentile_ranks = backtester.calculate_percentile_ranks(indicator)
            valid_percentiles = percentile_ranks.dropna()

            if valid_percentiles.empty:
                print(f"  Insufficient {data_source} percentile data for {ticker}, skipping")
                continue

            current_percentile = float(valid_percentiles.iloc[-1])
            current_price = float(data_for_current['Close'].iloc[-1])
            current_date = data_for_current.index[-1].strftime("%Y-%m-%d %H:%M")

            percentile_cohort, zone_label = get_percentile_cohort(current_percentile)
            in_entry_zone = percentile_cohort in ["extreme_low", "low"]
            regime = "mean_reversion" if metadata.is_mean_reverter else "momentum"

            # Prefer pre-computed 4H bin stats; fall back to derived stats from raw data
            cohort_stats = get_4h_cohort_stats_from_bins(ticker)
            if not cohort_stats and data_source == "4h":
                cohort_stats = compute_4h_cohort_stats_from_data(backtester, data_for_current, percentile_ranks)
            if not cohort_stats and data_source == "daily_fallback":
                # Use daily cohort cache so we still render data if 4H fetch failed
                cohort_stats = daily_cohort_cache.get(ticker, {})

            cohort_performance = cohort_stats.get(f'cohort_{percentile_cohort}') if cohort_stats else None
            if not cohort_performance and cohort_stats:
                cohort_performance = cohort_stats.get('cohort_all')

            if cohort_performance:
                expected_win_rate = cohort_performance.get('win_rate', 0.0)
                expected_return = cohort_performance.get('avg_return', 0.0)
                expected_holding_days = cohort_performance.get('avg_holding_days', FOUR_H_DEFAULT_HOLDING_DAYS)
                expected_return_per_day = expected_return / expected_holding_days if expected_holding_days > 0 else 0

                volatility_multiplier = {"Low": 1.0, "Medium": 1.5, "High": 2.0}.get(metadata.volatility_level, 1.5)
                risk_adjusted_expectancy = expected_return / volatility_multiplier

                live_expectancy = {
                    "expected_win_rate": expected_win_rate,
                    "expected_return_pct": expected_return,
                    "expected_holding_days": expected_holding_days,
                    "expected_return_per_day_pct": expected_return_per_day,
                    "risk_adjusted_expectancy_pct": risk_adjusted_expectancy,
                    "sample_size": cohort_performance.get('count', 0)
                }
            else:
                live_expectancy = {
                    "expected_win_rate": 0.0,
                    "expected_return_pct": 0.0,
                    "expected_holding_days": FOUR_H_DEFAULT_HOLDING_DAYS,
                    "expected_return_per_day_pct": 0.0,
                    "risk_adjusted_expectancy_pct": 0.0,
                    "sample_size": 0
                }

            current_states.append({
                "ticker": ticker,
                "name": metadata.name,
                "current_date": current_date,
                "current_price": current_price,
                "current_percentile": current_percentile,
                "percentile_cohort": percentile_cohort,
                "zone_label": zone_label,
                "in_entry_zone": in_entry_zone,
                "regime": regime,
                "is_mean_reverter": metadata.is_mean_reverter,
                "is_momentum": metadata.is_momentum,
                "volatility_level": metadata.volatility_level,
                "live_expectancy": live_expectancy,
                "data_source": data_source
            })

        except Exception as e:
            print(f"  Error getting 4H state for {ticker}: {e}")
            continue

    current_states.sort(key=lambda x: x['current_percentile'])
    print(f"✓ 4H market state ready: {len(current_states)} tickers processed")

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "timeframe": "4h",
        "market_state": current_states,
        "summary": {
            "total_tickers": len(current_states),
            "in_entry_zone": sum(1 for s in current_states if s['in_entry_zone']),
            "extreme_low_opportunities": sum(1 for s in current_states if s['percentile_cohort'] == 'extreme_low'),
            "low_opportunities": sum(1 for s in current_states if s['percentile_cohort'] == 'low')
        }
    }


@router.get("/{ticker}")
async def get_ticker_data(ticker: str):
    """Get data for a single ticker"""
    ticker = ticker.upper()

    # Call the main endpoint and filter
    all_data = await get_swing_framework_data()

    if ticker not in all_data['tickers']:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found")

    return {
        "snapshot_timestamp": all_data['snapshot_timestamp'],
        "ticker": ticker,
        "data": all_data['tickers'][ticker]
    }
