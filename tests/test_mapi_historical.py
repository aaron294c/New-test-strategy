#!/usr/bin/env python3
"""
MAPI Historical Analysis Test (offline, deterministic)

Validates the structure and basic invariants of the empirical percentile → forward return mapping.
"""

import sys
from pathlib import Path

BACKEND_DIR = (Path(__file__).resolve().parents[1] / "backend").as_posix()
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import numpy as np
import pandas as pd

from mapi_historical import compute_mapi_historical_from_df


def _synthetic_ohlc(days: int = 420, seed: int = 13) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=days, freq="B")

    rets = rng.normal(loc=0.0002, scale=0.012, size=len(dates))
    close = 100 * np.exp(np.cumsum(rets))

    open_ = np.roll(close, 1)
    open_[0] = close[0]
    high = np.maximum(open_, close) * (1 + rng.uniform(0.0005, 0.01, size=len(dates)))
    low = np.minimum(open_, close) * (1 - rng.uniform(0.0005, 0.01, size=len(dates)))
    volume = rng.integers(1_000_000, 5_000_000, size=len(dates))

    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=dates,
    )


def test_mapi_historical_structure():
    df = _synthetic_ohlc()
    out = compute_mapi_historical_from_df(df, lookback_days=300, require_momentum=False)

    assert "bin_stats" in out
    assert "zone_stats" in out
    assert "signal_stats" in out
    assert "sample_size" in out

    assert isinstance(out["bin_stats"], list)
    assert len(out["bin_stats"]) == 8  # default bins

    horizons = out["horizons"]
    assert 7 in horizons

    # "all" zone should match sample size by construction
    assert out["zone_stats"]["all"]["count"] == out["sample_size"]

    # Bin counts should sum to sample size
    assert sum(int(b["count"]) for b in out["bin_stats"]) == out["sample_size"]

    # Horizon stats exist per bin
    for b in out["bin_stats"]:
        for h in horizons:
            assert f"{h}d" in b["horizons"]
            assert "mean" in b["horizons"][f"{h}d"]
            assert "win_rate" in b["horizons"][f"{h}d"]

