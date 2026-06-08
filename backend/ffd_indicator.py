"""
Canonical Fractional-Differencing (FFD) normalization pipeline.

This is the single source of truth for the FFD<40 confluence signal validated
across this project's backtests (see docs/SIGNAL_METRICS_REFERENCE.md, "FFD <
40 as a Confluence Gate"): a 0-100 normalized score where readings below ~40
mark a statistically distinct, lower-volatility regime that — for a specific
16-name cohort — measurably raises EV / Sortino on top of "Signal A" entries.

Extracted from scripts/cluster_dca_ffd_confluence.py (and replicated across
~9 other backtest scripts) so live handlers and new backtests share one
validated implementation rather than drifting copies.

    fd_weights = build_fd_weights(FD_D, FD_THRESH, FD_MAXWIN)
    norm       = compute_ffd_norm(close, fd_weights, len(fd_weights))
    latest     = float(norm.iloc[-1])   # 0-100 reading for "right now"
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Validated constants — do not change without re-running the reference backtests.
FD_D, FD_THRESH, FD_MAXWIN = 0.3, 0.01, 30
Z_LEN, Z_CLIP              = 100, 4.0

# The empirically-validated "confluence" threshold used throughout this project.
FFD_CONFLUENCE_MAX = 40.0


def build_fd_weights(d: float = FD_D, thresh: float = FD_THRESH, maxL: int = FD_MAXWIN) -> np.ndarray:
    """Fixed-width fractional-differencing weights, truncated once |w_k| < thresh."""
    w = [1.0]
    for k in range(1, maxL):
        w_k = -w[k - 1] * (d - k + 1.0) / k
        if abs(w_k) < thresh:
            break
        w.append(w_k)
    return np.array(w)


def frac_diff_series(src: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Apply the FFD weights via convolution; bars before warmup are NaN."""
    L = len(weights)
    conv = np.convolve(src, weights, mode="full")[:len(src)]
    out = np.full(len(src), np.nan)
    out[L - 1:] = conv[L - 1:]
    return out


def compute_ffd_norm(close: pd.Series, fd_weights: np.ndarray, fd_warmup: int) -> pd.Series:
    """
    Fractionally-differenced close, rolling-Z-scored over Z_LEN bars and
    squashed through a logistic into a 0-100 band (Z_CLIP controls slope).

    Bars before the fd_warmup point fall back to raw close (matches the
    validated backtest behaviour); bars before the rolling window fills are NaN.
    """
    close_np = close.values.astype(float)
    fd_raw   = frac_diff_series(close_np, fd_weights)
    fd_val   = np.where(np.arange(len(close_np)) >= fd_warmup, fd_raw, close_np)
    s        = pd.Series(fd_val, index=close.index)
    rmean    = s.rolling(Z_LEN, min_periods=Z_LEN).mean()
    rstd     = s.rolling(Z_LEN, min_periods=Z_LEN).std(ddof=1)
    safe_std = rstd.clip(lower=0.0001)
    z        = (s - rmean) / safe_std
    norm     = 100.0 / (1.0 + np.exp(-z / (Z_CLIP / 2.0)))
    norm[rmean.isna() | rstd.isna()] = np.nan
    return norm


def latest_ffd_value(close: pd.Series) -> float | None:
    """Convenience: 0-100 FFD reading for the most recent bar, or None if not yet stable."""
    fd_weights = build_fd_weights()
    norm = compute_ffd_norm(close, fd_weights, len(fd_weights))
    if norm.empty or pd.isna(norm.iloc[-1]):
        return None
    return float(norm.iloc[-1])
