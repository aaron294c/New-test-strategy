"""
Lower Extension Distance API
Provides calculation functions for lower extension metrics
"""

from datetime import datetime, timedelta
import numpy as np
from typing import List, Dict, Optional


def calculate_mbad_levels(prices: np.ndarray, opens: np.ndarray = None,
                          length: int = 256,
                          time_weighting: bool = True,
                          iv_weighting: bool = True,
                          ticker: str = "") -> Dict:
    """
    Calculate MBAD (Mean-Based Asymmetric Distribution) levels
    This EXACTLY replicates the TradingView MBAD indicator logic from MBAD.md

    Args:
        prices: Array of CLOSE price data (most recent last)
        opens: Array of OPEN price data (for IV weighting, optional)
        length: Lookback length for calculations (default: 256)
        time_weighting: Apply time-based weighting (default: True)
        iv_weighting: Apply inferred volume weighting (default: True)

    Returns:
        Dictionary with all MBAD levels including ext_lower (blue line)
    """
    if len(prices) < length:
        length = len(prices)

    # Prepare data array (reversed to match Pine Script indexing: [0] = most recent)
    # Pine Script uses src[i] where i=0 is current bar, i=1 is previous, etc.
    data = prices[-length:][::-1]  # Reverse so [0] = most recent

    # Initialize weights array
    weights = np.ones(length)

    # Calculate weights exactly as Pine Script line 85:
    # weight = (time_ ? (len - i) : 1) * (iv ? math.abs(close[i] - open[i]) : 1)
    for i in range(length):
        # Time weighting: (len - i) means most recent gets highest weight
        time_weight = (length - i) if time_weighting else 1

        # IV weighting: abs(close[i] - open[i])
        iv_weight = 1
        if iv_weighting and opens is not None and len(opens) >= length:
            opens_data = opens[-length:][::-1]  # Also reverse opens
            iv_weight = abs(data[i] - opens_data[i])

        weights[i] = time_weight * iv_weight

    # Calculate weighted moments (exactly as Pine Script lines 46-75)
    # First pass: calculate sum of weights and weighted mean
    sum_w = 0.0
    sum_m1 = 0.0
    for i in range(length):
        weight = weights[i]
        sum_w += weight
        sum_m1 += data[i] * weight
    
    mean = sum_m1 / sum_w

    # Second pass for higher moments
    sum_m2 = 0.0
    sum_m3 = 0.0
    sum_m4 = 0.0
    sum_m5 = 0.0
    sum_m6 = 0.0

    for i in range(length):
        diff = data[i] - mean
        weight = weights[i]
        sum_m2 += np.power(diff, 2) * weight
        sum_m3 += np.power(diff, 3) * weight
        sum_m4 += np.power(diff, 4) * weight
        sum_m5 += np.power(diff, 5) * weight
        sum_m6 += np.power(diff, 6) * weight

    # Calculate moments (lines 70-74)
    dev = np.sqrt(sum_m2 / sum_w)
    skew = sum_m3 / sum_w / np.power(dev, 3)
    kurt = sum_m4 / sum_w / np.power(dev, 4)
    hskew = sum_m5 / sum_w / np.power(dev, 5)  # Higher skew
    hkurt = sum_m6 / sum_w / np.power(dev, 6)  # Higher kurtosis

    # Calculate MBAD levels (lines 97-104)
    # NOTE: TradingView uses math.round_to_mintick() which rounds to instrument tick size
    # For stocks, this is typically $0.01
    lim_lower = mean - dev * hkurt + dev * hskew
    ext_lower = mean - dev * kurt + dev * skew  # BLUE LOWER EXTENSION (line 98)
    dev_lower = mean - dev
    dev_lower2 = mean - 2 * dev
    basis = mean
    dev_upper = mean + dev
    ext_upper = mean + dev * kurt + dev * skew
    lim_upper = mean + dev * hkurt + dev * hskew

    return {
        'lim_lower': round(lim_lower, 2),
        'ext_lower': round(ext_lower, 2),  # BLUE LOWER EXTENSION LINE
        'dev_lower': round(dev_lower, 2),
        'dev_lower2': round(dev_lower2, 2),
        'basis': round(basis, 2),
        'dev_upper': round(dev_upper, 2),
        'ext_upper': round(ext_upper, 2),
        'lim_upper': round(lim_upper, 2),
        'mean': round(mean, 2),
        'dev': round(dev, 2),
        'skew': round(skew, 3),
        'kurt': round(kurt, 3)
    }
