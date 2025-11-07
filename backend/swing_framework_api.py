"""
Swing Framework API - Real Historical Trade Data

Provides comprehensive data for all tickers including REAL historical trades
from backtesting, not simulated/fake data.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from typing import Dict, List, Any
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

    # Extract just the cohort stats we need
    cohort_stats = {}
    for ticker, ticker_data in all_data['tickers'].items():
        backtest_stats = ticker_data.get('backtest_stats', {})
        cohort_stats[ticker] = {
            'cohort_extreme_low': backtest_stats.get('cohort_extreme_low'),
            'cohort_low': backtest_stats.get('cohort_low'),
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

    # RSI-MA Cohort Analysis
    extreme_low_trades = [t for t in trades if t.get('percentile_cohort') == 'extreme_low']
    low_trades = [t for t in trades if t.get('percentile_cohort') == 'low']

    def cohort_stats(cohort_trades):
        if not cohort_trades:
            return None
        cohort_wins = [t for t in cohort_trades if t['return_pct'] > 0]
        return {
            "count": len(cohort_trades),
            "win_rate": len(cohort_wins) / len(cohort_trades),
            "avg_return": sum(t['return_pct'] for t in cohort_trades) / len(cohort_trades),
            "avg_holding_days": sum(t['holding_days'] for t in cohort_trades) / len(cohort_trades)
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
        # RSI-MA Percentile Cohort Breakdown
        "cohort_extreme_low": cohort_stats(extreme_low_trades),  # ≤5th percentile
        "cohort_low": cohort_stats(low_trades)  # 5-15th percentile
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
    tickers = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "GOOGL", "TSLA", "NFLX"]
    results = {}

    bin_data_map = {
        "NVDA": (NVDA_4H_DATA, NVDA_DAILY_DATA),
        "MSFT": (MSFT_4H_DATA, MSFT_DAILY_DATA),
        "GOOGL": (GOOGL_4H_DATA, GOOGL_DAILY_DATA),
        "AAPL": (AAPL_4H_DATA, AAPL_DAILY_DATA),
        "TSLA": (TSLA_4H_DATA, TSLA_DAILY_DATA),
        "NFLX": (NFLX_4H_DATA, NFLX_DAILY_DATA),
        # Indices don't have pre-computed bin data - will use real-time calculation
        "SPY": (None, None),
        "QQQ": (None, None)
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

                    # Find REAL entry events at low percentiles (0-15%)
                    entry_events = backtester.find_entry_events_enhanced(
                        percentile_ranks,
                        data['Close'],
                        threshold=15.0  # 0-15% entry zone
                    )

                    print(f"  Found {len(entry_events)} total entry events")

                    # Separate into percentile cohorts for RSI-MA analysis
                    extreme_low_events = [e for e in entry_events if e['entry_percentile'] <= 5.0]
                    low_events = [e for e in entry_events if 5.0 < e['entry_percentile'] <= 15.0]

                    print(f"    ≤5th percentile: {len(extreme_low_events)} events")
                    print(f"    5-15th percentile: {len(low_events)} events")

                    # Target ~150 total trades with balanced sampling from both cohorts
                    # Take more from the cohort with more data, but maintain representation
                    target_total = 150

                    if len(entry_events) <= target_total:
                        # Use all available events
                        sampled_events = entry_events
                    else:
                        # Sample proportionally from both cohorts
                        extreme_sample_size = min(len(extreme_low_events), target_total // 2)
                        low_sample_size = min(len(low_events), target_total - extreme_sample_size)

                        # Take most recent events from each cohort
                        sampled_extreme = extreme_low_events[-extreme_sample_size:] if extreme_sample_size > 0 else []
                        sampled_low = low_events[-low_sample_size:] if low_sample_size > 0 else []

                        sampled_events = sampled_extreme + sampled_low

                    print(f"  Sampling {len(sampled_events)} trades for analysis")

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

                        # Determine percentile cohort for RSI-MA tracking
                        entry_pct = float(event['entry_percentile'])
                        if entry_pct <= 5.0:
                            cohort = "extreme_low"  # ≤5th percentile
                        elif entry_pct <= 15.0:
                            cohort = "low"  # 5-15th percentile
                        else:
                            cohort = "other"  # Shouldn't happen with threshold=15

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

            # Get historical performance for this percentile range
            if in_extreme_low:
                percentile_cohort = "extreme_low"
                zone_label = "≤5th percentile (Extreme Low)"
            elif in_low:
                percentile_cohort = "low"
                zone_label = "5-15th percentile (Low)"
            else:
                percentile_cohort = "none"
                zone_label = f"{current_percentile:.1f}th percentile (Not in entry zone)"

            # Get historical cohort performance from CACHE (fast!)
            cohort_stats = {
                'cohort_extreme_low': ticker_cohort_data.get('cohort_extreme_low'),
                'cohort_low': ticker_cohort_data.get('cohort_low')
            }

            # Extract expected performance for current cohort
            if in_extreme_low:
                cohort_performance = cohort_stats.get('cohort_extreme_low')
            elif in_low:
                cohort_performance = cohort_stats.get('cohort_low')
            else:
                cohort_performance = None

            # Calculate live risk-adjusted expectancy
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
                live_expectancy = None

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
    tickers = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "GOOGL", "TSLA", "NFLX"]

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

            # Get historical performance for this percentile range
            if in_extreme_low:
                percentile_cohort = "extreme_low"
                zone_label = "≤5th percentile (Extreme Low)"
            elif in_low:
                percentile_cohort = "low"
                zone_label = "5-15th percentile (Low)"
            else:
                percentile_cohort = "none"
                zone_label = f"{current_percentile:.1f}th percentile (Not in entry zone)"

            # Get historical cohort performance from CACHE (fast!)
            cohort_stats = {
                'cohort_extreme_low': ticker_cohort_data.get('cohort_extreme_low'),
                'cohort_low': ticker_cohort_data.get('cohort_low')
            }

            # Extract expected performance for current cohort
            if in_extreme_low:
                cohort_performance = cohort_stats.get('cohort_extreme_low')
            elif in_low:
                cohort_performance = cohort_stats.get('cohort_low')
            else:
                cohort_performance = None

            # Calculate live risk-adjusted expectancy
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
                live_expectancy = None

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
