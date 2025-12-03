"""
SWING Duration Analysis - Intraday (4H Resolution)

Uses 4-hour bars to capture intraday bounce behavior that daily data misses.
Measures duration in HOURS, not days, for more precise timing.

Key improvement: Includes entry bar (hour 0) in progression tracking.
"""

from __future__ import annotations

import math
import os
import tempfile
from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path

BAR_INTERVAL_HOURS = 4  # Default 4H bars for intraday progression
MARKET_HOURS_PER_DAY = 6.5  # US market hours (9:30 AM - 4:00 PM)
BARS_PER_TRADING_DAY = MARKET_HOURS_PER_DAY / BAR_INTERVAL_HOURS  # ~1.625 bars/day
MAX_TRADING_DAYS = 7  # Cap horizon to a 1-week trading window (not 24h*7 calendar hours)
DEFAULT_INTRADAY_HORIZON_HOURS = int(math.ceil(MAX_TRADING_DAYS * MARKET_HOURS_PER_DAY))
MIN_BARS_PER_DAY_FALLBACK = 1.5  # Guardrail if inference fails


def _generate_sample_intraday_data(
    ticker: str,
    days: int = 60,
    interval_hours: int = BAR_INTERVAL_HOURS
) -> pd.DataFrame:
    """
    Create synthetic intraday OHLCV data when live fetch fails (e.g., Yahoo blocked).

    Uses a simple drift + noise process and aligns bars on regular interval_hours steps.
    """
    np.random.seed(hash(ticker) % 2**32)
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=days)

    freq = f"{interval_hours}H"
    idx = pd.date_range(start=start_dt, end=end_dt, freq=freq)
    idx = idx[idx.dayofweek < 5]  # Weekdays only

    base_price_map = {
        "AAPL": 150,
        "MSFT": 300,
        "GOOGL": 120,
        "AMZN": 140,
        "META": 300,
        "NVDA": 400,
        "QQQ": 350,
        "SPY": 420,
    }
    base_price = base_price_map.get(ticker.upper(), 100)

    # Drift + noise; smaller per-bar volatility for intraday
    returns = np.random.randn(len(idx)) * 0.002  # ~0.2% per bar
    trend = np.linspace(0, 0.05, len(idx)) / len(idx)
    cycle = np.sin(np.linspace(0, 4 * np.pi, len(idx))) * 0.001
    returns = returns + trend + cycle

    multipliers = np.exp(np.cumsum(returns))
    close = base_price * multipliers

    data = pd.DataFrame(
        {
            "Open": close * (1 + np.random.randn(len(idx)) * 0.0005),
            "High": close * (1 + np.abs(np.random.randn(len(idx))) * 0.0015),
            "Low": close * (1 - np.abs(np.random.randn(len(idx))) * 0.0015),
            "Close": close,
            "Volume": np.random.randint(5_000_000, 25_000_000, len(idx)),
        },
        index=idx,
    )
    data["High"] = data[["Open", "High", "Close"]].max(axis=1)
    data["Low"] = data[["Open", "Low", "Close"]].min(axis=1)
    return data

@dataclass
class IntradayTradeOutcome:
    """Single trade outcome with hourly duration metrics."""
    entry_datetime: str
    entry_percentile: float
    is_winner: bool  # True if ~1-week trading return > 0

    # Hours-based metrics (4H bars = 4, 8, 12, 16, 20 hours etc.)
    hours_below_5pct: int
    hours_below_10pct: int
    hours_below_15pct: int

    escape_hour_5pct: Optional[int]
    escape_hour_10pct: Optional[int]
    escape_hour_15pct: Optional[int]

    hours_to_first_profit: Optional[int]


def fetch_intraday_data(
    ticker: str,
    period: str = "60d",
    interval: str = "4h",
    use_sample_data: bool = False,
) -> pd.DataFrame:
    """
    Fetch intraday data for ticker.

    Args:
        ticker: Stock symbol
        period: Historical period (max 60d for 4h intervals)
        interval: Bar interval (1h, 2h, 4h)

    Returns:
        DataFrame with OHLCV data
    """
    def _configure_yf_cache(dir_path: Path) -> None:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            os.environ["YFINANCE_CACHE_DIR"] = str(dir_path)
            os.environ.setdefault("XDG_CACHE_HOME", str(dir_path))
            import yfinance.shared as yf_shared  # type: ignore
            if hasattr(yf_shared, "_CACHE_DIR"):
                yf_shared._CACHE_DIR = str(dir_path)
            if hasattr(yf, "set_tz_cache_location"):
                try:
                    yf.set_tz_cache_location(str(dir_path))
                except Exception:
                    pass
        except Exception:
            pass

    def _download_with_cache_guard(symbol: str, *, cache_dir: Path) -> pd.DataFrame:
        _configure_yf_cache(cache_dir)
        try:
            return yf.download(symbol, period=period, interval=interval, progress=False)
        except Exception as e:
            # yfinance sometimes fails with sqlite "readonly database" in read-only home dirs.
            if "readonly" in str(e).lower() and "database" in str(e).lower():
                tmp_cache = Path(tempfile.mkdtemp(prefix="yf_cache_"))
                _configure_yf_cache(tmp_cache)
                return yf.download(symbol, period=period, interval=interval, progress=False)
            raise

    if use_sample_data:
        data = _generate_sample_intraday_data(ticker)
        data.attrs["data_source"] = "sample_intraday"
        return data

    fallback_reason = None
    try:
        cache_dir = Path("/tmp/yfinance_cache")
        data = _download_with_cache_guard(ticker, cache_dir=cache_dir)
        if data.empty:
            raise ValueError(f"No intraday data for {ticker}")
        data.attrs["data_source"] = "live_intraday"
        return data
    except Exception as e:
        fallback_reason = str(e)
        print(f"⚠️  Intraday fetch failed for {ticker} ({e}); falling back to sample intraday data")
        try:
            data = _generate_sample_intraday_data(ticker)
            data.attrs["data_source"] = "sample_intraday"
            data.attrs["fallback_reason"] = fallback_reason
            return data
        except Exception as e2:
            raise ValueError(f"Failed to fetch intraday data for {ticker}: {e}; sample generation error: {e2}")


def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate RSI indicator."""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_ma(data: pd.DataFrame, period: int = 50) -> pd.Series:
    """Calculate moving average."""
    return data['Close'].rolling(window=period).mean()


def calculate_rsi_ma_divergence(rsi: pd.Series, ma: pd.Series, close: pd.Series) -> pd.Series:
    """
    Calculate RSI-MA divergence indicator.

    Positive when price < MA and RSI is oversold (buy signal).
    """
    price_below_ma = close < ma
    rsi_oversold = rsi < 50

    # Simple divergence: price below MA + low RSI
    divergence = price_below_ma.astype(int) * (50 - rsi)
    return divergence


def calculate_percentile_ranks(series: pd.Series, window: int = 500) -> pd.Series:
    """Calculate rolling percentile ranks."""
    def percentile_rank(x):
        if len(x) < 2:
            return np.nan
        return (x < x.iloc[-1]).sum() / len(x) * 100

    return series.rolling(window=window, min_periods=50).apply(percentile_rank, raw=False)


def _infer_interval_hours(index: pd.Index, default: float = BAR_INTERVAL_HOURS) -> float:
    """Infer bar interval from the index; fallback to default if ambiguous."""
    try:
        diffs = pd.Series(index).diff().dropna().dt.total_seconds() / 3600.0
        if not diffs.empty:
            median_diff = diffs.median()
            if median_diff > 0:
                return float(median_diff)
    except Exception:
        pass
    return float(default)


def _estimate_bars_per_trading_day(index: pd.Index) -> float:
    """
    Estimate bars per trading day from the datetime index.

    Yahoo's 4H data often includes pre/after-hours bars (≈6 bars/day).
    Sample data also produces ~6 bars/day. Use median across days to reduce noise.
    """
    try:
        dates = pd.to_datetime(index).normalize()
        counts = pd.Series(dates).value_counts()
        if not counts.empty:
            return float(counts.median())
    except Exception:
        pass
    return float(MIN_BARS_PER_DAY_FALLBACK)


def find_intraday_entry_events(
    percentile_ranks: pd.Series,
    prices: pd.Series,
    threshold: float,
    max_horizon_hours: int = DEFAULT_INTRADAY_HORIZON_HOURS,  # trading hours horizon
    interval_hours: float = BAR_INTERVAL_HOURS,
) -> List[Dict]:
    """
    Find entry events at intraday resolution.

    Args:
        percentile_ranks: Percentile series
        prices: Price series
        threshold: Entry threshold (e.g., 5.0 for ≤5%)
        max_horizon_hours: Maximum holding period in hours

    Returns:
        List of entry events with hourly progression
    """
    events = []

    # Convert to hourly index (4H bars = 4 hours each)
    interval_hours = float(interval_hours or BAR_INTERVAL_HOURS)
    max_bars = math.ceil(max_horizon_hours / interval_hours)  # Use trading hours, not 24h calendar

    for i in range(len(percentile_ranks) - 1):
        pct_raw = percentile_ranks.iloc[i]
        if isinstance(pct_raw, (pd.Series, pd.DataFrame, np.ndarray)):
            if np.size(pct_raw) != 1:
                continue
            pct = float(np.array(pct_raw).squeeze())
        else:
            pct = pct_raw

        if pd.isna(pct) or float(pct) > float(threshold):
            continue

        # Don't analyze if we're too close to the end
        if i + max_bars >= len(prices):
            continue

        entry_price = prices.iloc[i]
        entry_time = percentile_ranks.index[i]

        # Track progression in hours
        progression = {}

        for bar_offset in range(1, max_bars + 1):
            idx = i + bar_offset
            if idx >= len(prices):
                break

            hours_elapsed = bar_offset * interval_hours
            current_price = prices.iloc[idx]
            current_pct = percentile_ranks.iloc[idx]

            if pd.isna(current_pct):
                break

            cumulative_return = (current_price - entry_price) / entry_price * 100

            progression[hours_elapsed] = {
                'percentile': float(current_pct),
                'cumulative_return_pct': float(cumulative_return),
                'price': float(current_price),
            }

        if progression:
            events.append({
                'entry_datetime': entry_time,
                'entry_price': float(entry_price),
                'entry_percentile': float(pct),
                'progression': progression,
            })

    return events


def _calculate_hours_below_threshold(
    progression: Dict[int, Dict],
    threshold: float,
    entry_percentile: float,
) -> tuple[int, Optional[int]]:
    """
    Count consecutive hours where percentile ≤ threshold.

    Returns:
        (hours_below, escape_hour)
    """
    if entry_percentile > threshold:
        return 0, None

    hours_below = 0
    escape_hour = None
    sorted_hours = sorted(progression.keys())
    # Infer the bar interval from progression keys (first gap or first key)
    if len(sorted_hours) >= 2:
        interval_hours = sorted_hours[0] if sorted_hours[0] > 0 else sorted_hours[1] - sorted_hours[0]
    elif sorted_hours:
        interval_hours = sorted_hours[0]
    else:
        interval_hours = BAR_INTERVAL_HOURS

    for hour in sorted_hours:
        pct = progression[hour].get("percentile")
        if pd.isna(pct):
            break

        if pct <= threshold:
            hours_below += interval_hours
        else:
            escape_hour = hour
            break

    return hours_below, escape_hour


def _calculate_hours_to_first_profit(progression: Dict[int, Dict]) -> Optional[int]:
    """Return first hour where cumulative return > 0."""
    for hour in sorted(progression.keys()):
        if progression[hour]["cumulative_return_pct"] > 0:
            return hour
    return None


def analyze_swing_duration_intraday(
    ticker: str,
    entry_threshold: float = 5.0,
    period: str = "60d",
    interval: str = "4h",
    use_sample_data: bool = False,
) -> Dict:
    """
    Analyze SWING duration with INTRADAY resolution (hours).

    Args:
        ticker: Stock symbol
        entry_threshold: Entry percentile threshold
        period: Historical period for analysis
        interval: Bar interval (4h recommended)

    Returns:
        Dict with hourly duration metrics
    """
    # Fetch intraday data
    data = fetch_intraday_data(ticker, period=period, interval=interval, use_sample_data=use_sample_data)

    # Calculate indicators
    rsi = calculate_rsi(data)
    ma = calculate_ma(data)
    divergence = calculate_rsi_ma_divergence(rsi, ma, data['Close'])
    percentile_ranks = calculate_percentile_ranks(divergence)

    # Track multiple thresholds
    thresholds_to_track = sorted({5.0, 10.0, 15.0, float(entry_threshold)})
    max_threshold = max(thresholds_to_track)
    interval_hours_inferred = _infer_interval_hours(data.index, default=BAR_INTERVAL_HOURS)
    bars_per_day_est = _estimate_bars_per_trading_day(data.index)
    bars_per_day_est = max(bars_per_day_est, MIN_BARS_PER_DAY_FALLBACK)

    # Clamp bars/day to a small cushion over market hours so we stay in a true
    # trading-week window (avoid 140h+ horizons). ~20% padding tolerates slight
    # pre/post inclusion without blowing up the horizon.
    baseline_bars_per_day = MARKET_HOURS_PER_DAY / interval_hours_inferred  # ~1.625 for 4H
    bars_per_day_effective = min(bars_per_day_est, baseline_bars_per_day * 1.2)

    horizon_bars = math.ceil(MAX_TRADING_DAYS * bars_per_day_effective)
    intraday_horizon_hours = int(math.ceil(horizon_bars * interval_hours_inferred))
    intraday_horizon_hours_rounded = math.ceil(intraday_horizon_hours / interval_hours_inferred) * interval_hours_inferred
    min_hours_for_partial_outcome = int(math.ceil(5 * bars_per_day_effective * interval_hours_inferred))  # Require ~5 trading days for partial

    # Find entry events up to the widest threshold so higher thresholds get data
    entry_events = find_intraday_entry_events(
        percentile_ranks,
        data['Close'],
        threshold=max_threshold,
        max_horizon_hours=intraday_horizon_hours,
        interval_hours=interval_hours_inferred,
    )

    # Process events
    trades: List[IntradayTradeOutcome] = []

    for event in entry_events:
        progression = event.get("progression", {})
        if not progression:
            continue

        # Classify winner/loser based on 7 TRADING-day return (~46 hours, rounded to bar boundary)
        outcome_hour = intraday_horizon_hours_rounded
        day7_return = None

        if outcome_hour in progression:
            day7_return = progression[outcome_hour]["cumulative_return_pct"]
        elif progression:
            # Use last available hour
            last_hour = max(progression.keys())
            if last_hour >= min_hours_for_partial_outcome:  # At least 5 trading days of bars
                day7_return = progression[last_hour]["cumulative_return_pct"]

        if day7_return is None:
            continue

        is_winner = day7_return > 0

        # Calculate hourly metrics
        entry_pct = float(event.get("entry_percentile", 0))

        hours_5, escape_5 = _calculate_hours_below_threshold(progression, 5.0, entry_pct)
        hours_10, escape_10 = _calculate_hours_below_threshold(progression, 10.0, entry_pct)
        hours_15, escape_15 = _calculate_hours_below_threshold(progression, 15.0, entry_pct)
        hours_to_profit = _calculate_hours_to_first_profit(progression)

        entry_dt = event.get("entry_datetime")
        entry_dt_str = entry_dt.strftime("%Y-%m-%d %H:%M") if hasattr(entry_dt, "strftime") else str(entry_dt)

        trades.append(IntradayTradeOutcome(
            entry_datetime=entry_dt_str,
            entry_percentile=entry_pct,
            is_winner=is_winner,
            hours_below_5pct=hours_5,
            hours_below_10pct=hours_10,
            hours_below_15pct=hours_15,
            escape_hour_5pct=escape_5,
            escape_hour_10pct=escape_10,
            escape_hour_15pct=escape_15,
            hours_to_first_profit=hours_to_profit,
        ))

    # Scoped trades at caller threshold
    scoped_trades = [t for t in trades if t.entry_percentile <= entry_threshold]
    winners_base = [t for t in scoped_trades if t.is_winner]
    losers_base = [t for t in scoped_trades if not t.is_winner]

    # Threshold-specific pools (for multi-threshold stats)
    winners_by_threshold = {
        th: [t for t in trades if t.is_winner and t.entry_percentile <= th]
        for th in thresholds_to_track
    }
    losers_by_threshold = {
        th: [t for t in trades if not t.is_winner and t.entry_percentile <= th]
        for th in thresholds_to_track
    }

    # Aggregate statistics (in hours)
    def get_hourly_stats(trades_list: List[IntradayTradeOutcome], threshold_pct: int) -> Dict:
        if not trades_list:
            return {
                "sample_size": 0,
                "avg_hours_in_low": None,
                "median_hours_in_low": None,
                "median_hours_in_low_uncapped": None,
                "avg_hours_in_low_uncapped": None,
                "censored_at_horizon_count": 0,
                "avg_escape_time_hours": None,
                "escape_rate": None,
                "avg_hours_to_profit": None,
                "median_hours_to_profit": None,
            }

        # Get appropriate field
        if threshold_pct == 5:
            hours_in_low = [t.hours_below_5pct for t in trades_list if t.hours_below_5pct is not None]
            escape_hours = [t.escape_hour_5pct for t in trades_list if t.escape_hour_5pct is not None]
        elif threshold_pct == 10:
            hours_in_low = [t.hours_below_10pct for t in trades_list if t.hours_below_10pct is not None]
            escape_hours = [t.escape_hour_10pct for t in trades_list if t.escape_hour_10pct is not None]
        else:  # 15
            hours_in_low = [t.hours_below_15pct for t in trades_list if t.hours_below_15pct is not None]
            escape_hours = [t.escape_hour_15pct for t in trades_list if t.escape_hour_15pct is not None]

        profit_hours = [t.hours_to_first_profit for t in trades_list if t.hours_to_first_profit is not None]

        # Flag trades that never escaped and thus hit the analysis horizon (right-censored)
        horizon = intraday_horizon_hours_rounded
        censored_mask = []
        if threshold_pct == 5:
            censored_mask = [
                t.escape_hour_5pct is None and t.hours_below_5pct is not None and t.hours_below_5pct >= horizon
                for t in trades_list
            ]
        elif threshold_pct == 10:
            censored_mask = [
                t.escape_hour_10pct is None and t.hours_below_10pct is not None and t.hours_below_10pct >= horizon
                for t in trades_list
            ]
        else:
            censored_mask = [
                t.escape_hour_15pct is None and t.hours_below_15pct is not None and t.hours_below_15pct >= horizon
                for t in trades_list
            ]

        uncapped_hours = [hrs for hrs, capped in zip(hours_in_low, censored_mask) if not capped]
        uncapped_avg = float(np.mean(uncapped_hours)) if uncapped_hours else None

        return {
            "sample_size": len(trades_list),
            "avg_hours_in_low": float(np.mean(hours_in_low)) if hours_in_low else None,
            "median_hours_in_low": float(np.median(hours_in_low)) if hours_in_low else None,
            "median_hours_in_low_uncapped": float(np.median(uncapped_hours)) if uncapped_hours else None,
            "avg_hours_in_low_uncapped": uncapped_avg,
            "censored_at_horizon_count": int(sum(censored_mask)),
            "avg_escape_time_hours": float(np.mean(escape_hours)) if escape_hours else None,
            "escape_rate": float(len(escape_hours) / len(trades_list)) if trades_list else None,
            "avg_hours_to_profit": float(np.mean(profit_hours)) if profit_hours else None,
            "median_hours_to_profit": float(np.median(profit_hours)) if profit_hours else None,
        }

    # Calculate for each threshold
    results = {
        "ticker": ticker.upper(),
        "entry_threshold": float(entry_threshold),
        "sample_size": len(scoped_trades),
        "data_source": data.attrs.get("data_source", "intraday_4h"),
        "fallback_reason": data.attrs.get("fallback_reason"),
        "interval": interval,
        "period_analyzed": period,
        "duration_unit": "hours",
        "duration_granularity": "intraday",
        "bar_interval_hours": interval_hours_inferred,
        "max_horizon_hours": intraday_horizon_hours_rounded,
        "max_horizon_trading_days": MAX_TRADING_DAYS,
        "max_horizon_bars": horizon_bars,
        "bars_per_trading_day_est": bars_per_day_est,
        "bars_per_trading_day_effective": bars_per_day_effective,
        "thresholds_tracked": thresholds_to_track,

        "winners": {
            "count": len(winners_base),
            "threshold_5pct": get_hourly_stats(winners_by_threshold.get(5.0, []), 5),
            "threshold_10pct": get_hourly_stats(winners_by_threshold.get(10.0, []), 10),
            "threshold_15pct": get_hourly_stats(winners_by_threshold.get(15.0, []), 15),
        },

        "losers": {
            "count": len(losers_base),
            "threshold_5pct": get_hourly_stats(losers_by_threshold.get(5.0, []), 5),
            "threshold_10pct": get_hourly_stats(losers_by_threshold.get(10.0, []), 10),
            "threshold_15pct": get_hourly_stats(losers_by_threshold.get(15.0, []), 15),
        },
    }

    # Winner vs Loser comparison
    winner_hours_5 = [t.hours_below_5pct for t in winners_base]
    loser_hours_5 = [t.hours_below_5pct for t in losers_base]

    p_value = None
    if len(winner_hours_5) >= 2 and len(loser_hours_5) >= 2:
        try:
            _, p_value = mannwhitneyu(winner_hours_5, loser_hours_5, alternative="two-sided")
            p_value = float(p_value)
        except:
            pass

    results["comparison"] = {
        "statistical_significance_p": p_value,
        "predictive_value": "high" if p_value and p_value < 0.05 else "inconclusive",
        "winner_vs_loser_ratio_5pct": (
            float(np.mean(winner_hours_5) / np.mean(loser_hours_5))
            if winner_hours_5 and loser_hours_5 and np.mean(loser_hours_5) != 0
            else None
        ),
    }

    # Ticker profile (convert hours to trading days for proper classification)
    # CRITICAL: 4H bars during market hours = ~1.625 bars/day (6.5 market hrs / 4 hrs)
    # So hours to trading days = hours / 6.5 (NOT hours / 24!)
    winner_escape_5 = [t.escape_hour_5pct for t in winners_base if t.escape_hour_5pct is not None]
    median_escape_hours = float(np.median(winner_escape_5)) if winner_escape_5 else None
    # Convert to TRADING days (using market hours)
    median_escape_days = median_escape_hours / MARKET_HOURS_PER_DAY if median_escape_hours else None

    if median_escape_days is None:
        bounce_profile = "unknown"
    elif median_escape_days <= 0.77:  # ≤ 5 hours (~1.25 4H bars)
        bounce_profile = "ultra_fast_bouncer"
    elif median_escape_days <= 1.54:  # ≤ 10 hours (~2.5 4H bars, ~1 trading day)
        bounce_profile = "fast_bouncer"
    elif median_escape_days <= 3.08:  # ≤ 20 hours (~5 4H bars, ~2 trading days)
        bounce_profile = "balanced"
    else:
        bounce_profile = "slow_bouncer"

    results["ticker_profile"] = {
        "bounce_speed": bounce_profile,
        "median_escape_hours_winners": median_escape_hours,
        "median_escape_days_winners": median_escape_days,  # This is NOW in TRADING days
        "median_escape_time_winners": median_escape_hours,  # Alias for compatibility with daily view
        "duration_unit": "hours",
        "market_hours_per_day": MARKET_HOURS_PER_DAY,
        "bars_per_trading_day": BARS_PER_TRADING_DAY,
        "recommendation": (
            "Ultra-fast intraday bouncer - monitor every 4 hours (escapes <1 trading day)" if bounce_profile == "ultra_fast_bouncer"
            else "Fast bouncer - typically escapes within 1.5 trading days" if bounce_profile == "fast_bouncer"
            else "Balanced - 1.5-3 trading day patience window recommended" if bounce_profile == "balanced"
            else "Slow bouncer - requires 3+ trading days patience"
        ),
    }

    return results
