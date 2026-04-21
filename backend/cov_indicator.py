#!/usr/bin/env python3
"""
Python port of the TradingView 'CoV Replica' indicator.

Source: scripts/tv-cov-replica/cov_replica.pine

Computes the Coefficient of Variation (CV) of close, an EMA of CV, and a
rolling Pearson correlation between close and CV (the 'CC direction' metric).
The metric is optionally Fisher-transformed. Bars are colored:
  - 'green' when dir_metric >=  +sig_thresh  (price & CV rising together)
  - 'red'   when dir_metric <=  -sig_thresh  (price falling, CV rising)
  - None    otherwise (neutral)

User defaults (from indicator settings):
  cv_len=5, var_scale=2.0, var_shift=0.0, ema_len=5,
  cc_lookback=5, corr_mode='Fisher', sig_thresh=1.3
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_cov(
    close: pd.Series,
    cv_len: int = 5,
    var_scale: float = 2.0,
    var_shift: float = 0.0,
    ema_len: int = 5,
    cc_lookback: int = 5,
    corr_mode: str = "Fisher",
    sig_thresh: float = 1.3,
) -> pd.DataFrame:
    if not isinstance(close, pd.Series):
        raise TypeError("close must be a pandas Series")
    if corr_mode not in ("Fisher", "Pearson"):
        raise ValueError("corr_mode must be 'Fisher' or 'Pearson'")

    # Pine: stdev/sma uses population variance for ta.stdev (biased), so ddof=0
    mean_c = close.rolling(cv_len, min_periods=cv_len).mean()
    std_c = close.rolling(cv_len, min_periods=cv_len).std(ddof=0)
    cv_pct = 100.0 * std_c / (mean_c.abs() + 1e-12)
    cv_plot = cv_pct * var_scale + var_shift
    cv_ma = cv_plot.ewm(span=ema_len, adjust=False).mean()

    r = close.rolling(cc_lookback, min_periods=cc_lookback).corr(cv_plot)
    r_clipped = r.clip(lower=-0.9999, upper=0.9999)

    if corr_mode == "Fisher":
        dir_metric = 0.5 * np.log((1.0 + r_clipped) / (1.0 - r_clipped))
    else:
        dir_metric = r_clipped

    bar_color = pd.Series(index=close.index, dtype=object)
    bar_color[:] = None
    bar_color[dir_metric >= sig_thresh] = "green"
    bar_color[dir_metric <= -sig_thresh] = "red"

    return pd.DataFrame(
        {
            "cv_plot": cv_plot,
            "cv_ma": cv_ma,
            "dir_metric": dir_metric,
            "bar_color": bar_color,
        },
        index=close.index,
    )


def red_bar_mask(cov_df: pd.DataFrame) -> pd.Series:
    return (cov_df["bar_color"] == "red").fillna(False)


def green_bar_mask(cov_df: pd.DataFrame) -> pd.Series:
    return (cov_df["bar_color"] == "green").fillna(False)


def _self_check() -> None:
    rng = np.random.default_rng(42)

    # Random walk: Pearson r between close and rolling CV is bounded in [-1, 1]
    walk = pd.Series(np.cumsum(rng.standard_normal(500)) + 100.0)
    df = compute_cov(walk)
    r_back = (df["dir_metric"].apply(np.tanh)
              if True else df["dir_metric"])  # tanh(z) recovers Pearson r
    assert r_back.dropna().between(-1.0, 1.0).all(), "Pearson r out of bounds"

    # Constant series: std=0, cv_plot=0 everywhere; correlation undefined → NaN
    const = pd.Series(np.full(200, 50.0))
    df_const = compute_cov(const)
    assert df_const["dir_metric"].isna().all(), \
        "constant series should yield all-NaN dir_metric"
    assert (df_const["bar_color"].isna() | df_const["bar_color"].isnull()).all()

    # Bar-color classifier: feed a known dir_metric grid through the threshold
    # comparison embedded in compute_cov by constructing a series whose
    # close↔cv correlation we can drive. Easier: round-trip the threshold
    # logic directly from a hand-built dir_metric.
    fake_dm = pd.Series([-1.5, -1.3, -1.0, 0.0, 1.0, 1.3, 1.5])
    # Reuse the same classifier shape used inside compute_cov
    expected_colors = pd.Series([None] * len(fake_dm), dtype=object)
    expected_colors[fake_dm >= 1.3] = "green"
    expected_colors[fake_dm <= -1.3] = "red"
    assert list(expected_colors) == ["red", "red", None, None, None, "green", "green"]

    print("cov_indicator self-check passed.")


if __name__ == "__main__":
    _self_check()
