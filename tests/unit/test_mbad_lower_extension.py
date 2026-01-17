import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend/api"))

import lower_extension  # noqa: E402


def _round_to_tick(value: float, tick: float = 0.01) -> float:
    return float(np.round(value / tick) * tick)


def test_ext_lower_matches_pinescript_formula_for_simple_window():
    # Window (past -> current)
    df = pd.DataFrame(
        {
            "Open": [5.0, 6.0, 7.0, 8.0, 9.0],
            "Close": [6.0, 7.0, 8.0, 9.0, 10.0],
        }
    )

    levels = lower_extension._mbad_levels_for_index(df, idx=4, length=5, tick_size=0.01)

    # PineScript indexing uses current->past
    src = np.array([10.0, 9.0, 8.0, 7.0, 6.0], dtype=float)
    open_ = np.array([9.0, 8.0, 7.0, 6.0, 5.0], dtype=float)
    time_w = np.array([5, 4, 3, 2, 1], dtype=float)
    iv_w = np.abs(src - open_)
    weights = time_w * iv_w

    mean, dev, skew, kurt, hskew, hkurt = lower_extension._weighted_moments(src, weights)
    expected_ext_lower = _round_to_tick(mean - dev * kurt + dev * skew, 0.01)

    assert levels["ext_lower"] == expected_ext_lower


def test_ext_lower_is_mean_when_dev_is_zero():
    # Constant prices => dev=0 => ext_lower=basis=mean
    df = pd.DataFrame(
        {
            "Open": [99.0] * 6,
            "Close": [100.0] * 6,
        }
    )

    levels = lower_extension._mbad_levels_for_index(df, idx=5, length=5, tick_size=0.01)
    assert levels["ext_lower"] == levels["basis"] == 100.0

