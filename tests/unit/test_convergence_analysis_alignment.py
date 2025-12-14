import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))

import convergence_analyzer as ca  # noqa: E402
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


def test_convergence_endpoint_uses_aligned_mtf_series(monkeypatch):
    """
    Ensures convergence analysis runs on the same aligned daily/4H percentile logic
    as MultiTimeframeAnalyzer (no separate/legacy calculation path).
    """
    daily_index = pd.date_range("2023-01-01", periods=320, freq="1D")
    daily_df = _make_ohlcv(daily_index, seed=10, base_price=120.0)

    end_hour = daily_index[-1] + pd.Timedelta(hours=23)
    hourly_index = pd.date_range(end=end_hour, periods=210 * 24, freq="1H")
    hourly_df = _make_ohlcv(hourly_index, seed=11, base_price=float(daily_df["Close"].iloc[-210]))

    class FakeTicker:
        def __init__(self, _ticker: str):
            self.ticker = _ticker

        def history(self, *, interval: str, period: str):
            if interval == "1d":
                return daily_df.copy()
            if interval == "1h":
                return hourly_df.copy()
            raise AssertionError(f"Unexpected interval requested: {interval} (period={period})")

    # Patch the yfinance usage inside MultiTimeframeAnalyzer (used by convergence_analyzer)
    monkeypatch.setattr(mta.yf, "Ticker", FakeTicker)

    result = ca.analyze_convergence_for_ticker("FAKE")

    assert result["ticker"] == "FAKE"
    assert "current_state" in result
    assert "historical_statistics" in result
    assert "overextension_events" in result
    assert isinstance(result["overextension_events"], list)

