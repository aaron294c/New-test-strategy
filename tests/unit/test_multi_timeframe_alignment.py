import os
import sys

import numpy as np
import pandas as pd


# Allow importing backend modules (repo layout: tests/ vs backend/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))

import multi_timeframe_analyzer as mta  # noqa: E402


def _make_ohlcv(index: pd.DatetimeIndex, *, seed: int, base_price: float = 100.0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    steps = rng.normal(loc=0.0, scale=0.5, size=len(index))
    close = np.maximum(base_price + np.cumsum(steps), 1.0)
    open_ = close + rng.normal(loc=0.0, scale=0.1, size=len(index))
    high = np.maximum(open_, close) + np.abs(rng.normal(loc=0.0, scale=0.2, size=len(index)))
    low = np.minimum(open_, close) - np.abs(rng.normal(loc=0.0, scale=0.2, size=len(index)))
    volume = rng.integers(1_000_000, 5_000_000, size=len(index))

    return pd.DataFrame(
        {
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        },
        index=index,
    )


def test_multi_timeframe_4h_percentiles_use_aligned_window(monkeypatch):
    """
    Regression: multi-timeframe divergence must compute 4H percentiles on 4H bars
    using an aligned lookback (~410 4H bars), not a 252-day window on a daily-resampled
    4H series.

    This test uses only ~70 calendar days of hourly data. The old (incorrect) approach
    would yield NaN for current_4h_percentile (insufficient 252 daily points), while
    the aligned 4H-window approach yields a valid value (>=410 4H bars available).
    """

    daily_index = pd.date_range("2023-01-01", periods=300, freq="1D")
    daily_df = _make_ohlcv(daily_index, seed=1, base_price=120.0)

    end_hour = daily_index[-1] + pd.Timedelta(hours=23)
    # Use <252 days of hourly history so an incorrect "252-day window on daily-resampled 4H"
    # implementation would still fail (insufficient daily points), while the correct
    # 4H-bar percentile window approach succeeds.
    hourly_index = pd.date_range(end=end_hour, periods=200 * 24, freq="1H")
    hourly_df = _make_ohlcv(hourly_index, seed=2, base_price=float(daily_df["Close"].iloc[-70]))

    class FakeTicker:
        def __init__(self, _ticker: str):
            self.ticker = _ticker

        def history(self, *, interval: str, period: str):
            if interval == "1d":
                return daily_df.copy()
            if interval == "1h":
                return hourly_df.copy()
            raise AssertionError(f"Unexpected interval requested: {interval} (period={period})")

    monkeypatch.setattr(mta.yf, "Ticker", FakeTicker)

    analysis = mta.run_multi_timeframe_analysis("FAKE")

    assert analysis["ticker"] == "FAKE"
    assert analysis["current_daily_percentile"] is not None
    assert analysis["current_4h_percentile"] is not None
    assert analysis["current_divergence_pct"] is not None
    assert isinstance(analysis["divergence_events"], list)
    assert "current_recommendation" in analysis
    assert "optimal_thresholds" in analysis
    assert "dislocation_abs_p85" in analysis["optimal_thresholds"]
    assert analysis["optimal_thresholds"]["dislocation_abs_p85"] is not None
    assert "dislocation_stats" in analysis["optimal_thresholds"]
    assert "dislocation_sample" in analysis["optimal_thresholds"]
    assert analysis["optimal_thresholds"]["dislocation_sample"]["n_days"] > 0

    abs_p85 = analysis["optimal_thresholds"]["dislocation_stats"].get("abs_p85")
    assert abs_p85 is not None
    horizons = abs_p85.get("horizons", {})
    assert "D1" in horizons and "D3" in horizons and "D7" in horizons
    assert "delta_median" in horizons["D1"]
    assert "delta_win_rate" in horizons["D1"]
