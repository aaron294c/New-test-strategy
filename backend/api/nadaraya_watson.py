"""
Nadaraya-Watson Envelope Calculator
Implements the Nadaraya-Watson kernel regression with ATR-based envelope bands.

Formula:
- nw_estimate = Σ(price[i] * weight[i]) / Σ(weight[i])
- weight[i] = exp(-(i^2) / (2 * h^2))
- lower_band = nw_estimate - (ATR(atr_period) * atr_mult)
- pct_from_lower_band = 100 * (price - lower_band) / lower_band
- lower_band_breached = price < lower_band
"""

import numpy as np
from typing import Dict, Optional, Tuple


def calculate_nadaraya_watson_lower_band(
    prices: np.ndarray,
    length: int = 200,
    bandwidth: float = 8.0,
    atr_period: int = 50,
    atr_mult: float = 2.0,
    highs: Optional[np.ndarray] = None,
    lows: Optional[np.ndarray] = None
) -> Dict:
    """
    Calculate Nadaraya-Watson Envelope lower band and distance metrics.

    This function implements the Nadaraya-Watson kernel regression estimator
    with an ATR-based envelope to create support/resistance bands.

    Args:
        prices: Array of close prices (most recent last)
        length: Window size for kernel regression (default: 200, max: 500, min: 20)
        bandwidth: Kernel bandwidth parameter h (default: 8.0, min: 0.1)
        atr_period: Period for ATR calculation (default: 50, min: 10)
        atr_mult: ATR multiplier for envelope width (default: 2.0, min: 0.1)
        highs: Array of high prices (optional, for ATR calculation)
        lows: Array of low prices (optional, for ATR calculation)

    Returns:
        Dictionary containing:
            - nw_estimate: Nadaraya-Watson regression estimate
            - lower_band: Lower envelope band (nw_estimate - ATR * mult)
            - upper_band: Upper envelope band (nw_estimate + ATR * mult)
            - lower_band_breached: Boolean, True if price < lower_band
            - pct_from_lower_band: Percentage distance from lower band
            - atr: Current ATR value
            - is_valid: Boolean, True if calculation is valid (warm-up complete)

    Edge Cases:
        - If length > len(prices), uses all available data
        - If lower_band is zero or near-zero, uses eps=1e-8 to avoid division by zero
        - If not enough data for warm-up, returns is_valid=False
        - If highs/lows not provided, estimates ATR from close prices only

    Example:
        >>> prices = np.array([95, 97, 98, 100, 102])
        >>> result = calculate_nadaraya_watson_lower_band(prices, length=5)
        >>> result['lower_band_breached']  # True if current price < lower_band
        >>> result['pct_from_lower_band']  # e.g., -5.0 if 5% below lower band
    """

    # Validate inputs
    if len(prices) == 0:
        return _empty_result()

    # Ensure we have enough data for warm-up
    min_bars = max(length, atr_period) + 1
    if len(prices) < min_bars:
        return _empty_result(is_valid=False)

    # Get current price (most recent)
    current_price = float(prices[-1])

    # Calculate Gaussian kernel weights
    # weight[i] = exp(-(i^2) / (2 * h^2))
    weights = np.zeros(length)
    for i in range(length):
        weights[i] = np.exp(-(i ** 2) / (2 * bandwidth ** 2))

    # Get the most recent 'length' prices
    window_prices = prices[-length:] if len(prices) >= length else prices
    actual_length = len(window_prices)

    # Calculate Nadaraya-Watson estimate
    # nw_estimate = Σ(price[i] * weight[i]) / Σ(weight[i])
    # Note: prices are indexed from oldest to newest, so we reverse to match Pine Script indexing
    reversed_prices = window_prices[::-1]  # [0] = most recent

    nw_sum = 0.0
    weight_sum = 0.0
    for i in range(actual_length):
        w = weights[i] if i < len(weights) else weights[-1]
        nw_sum += reversed_prices[i] * w
        weight_sum += w

    nw_estimate = nw_sum / weight_sum if weight_sum > 0 else current_price

    # Calculate ATR for envelope
    atr = _calculate_atr(prices, atr_period, highs, lows)

    # Calculate envelope bands
    volatility = atr * atr_mult
    upper_band = nw_estimate + volatility
    lower_band = nw_estimate - volatility

    # Calculate distance metrics
    # Use epsilon to avoid division by zero
    eps = 1e-8
    if abs(lower_band) < eps:
        pct_from_lower_band = None
        lower_band_breached = current_price < lower_band
    else:
        pct_from_lower_band = 100.0 * (current_price - lower_band) / lower_band
        lower_band_breached = current_price < lower_band

    return {
        'nw_estimate': round(nw_estimate, 2),
        'lower_band': round(lower_band, 2),
        'upper_band': round(upper_band, 2),
        'lower_band_breached': bool(lower_band_breached),
        'pct_from_lower_band': round(pct_from_lower_band, 2) if pct_from_lower_band is not None else None,
        'atr': round(atr, 2),
        'current_price': round(current_price, 2),
        'is_valid': True
    }


def _calculate_atr(
    prices: np.ndarray,
    period: int,
    highs: Optional[np.ndarray] = None,
    lows: Optional[np.ndarray] = None
) -> float:
    """
    Calculate Average True Range (ATR).

    If highs/lows are provided, uses true range calculation.
    Otherwise, estimates from close prices only.

    Args:
        prices: Close prices
        period: ATR period
        highs: High prices (optional)
        lows: Low prices (optional)

    Returns:
        ATR value
    """
    if len(prices) < period + 1:
        # Not enough data, return simple volatility estimate
        return np.std(prices) if len(prices) > 1 else 0.0

    if highs is not None and lows is not None and len(highs) == len(prices) and len(lows) == len(prices):
        # True range calculation
        true_ranges = []
        for i in range(1, len(prices)):
            tr = max(
                highs[i] - lows[i],  # High - Low
                abs(highs[i] - prices[i-1]),  # High - Previous Close
                abs(lows[i] - prices[i-1])   # Low - Previous Close
            )
            true_ranges.append(tr)

        # Calculate ATR as simple moving average of true ranges
        true_ranges = np.array(true_ranges)
        if len(true_ranges) >= period:
            atr = np.mean(true_ranges[-period:])
        else:
            atr = np.mean(true_ranges)
    else:
        # Estimate from close prices only (absolute price changes)
        price_changes = np.abs(np.diff(prices))
        if len(price_changes) >= period:
            atr = np.mean(price_changes[-period:])
        else:
            atr = np.mean(price_changes) if len(price_changes) > 0 else 0.0

    return float(atr)


def _empty_result(is_valid: bool = False) -> Dict:
    """Return empty result for edge cases."""
    return {
        'nw_estimate': None,
        'lower_band': None,
        'upper_band': None,
        'lower_band_breached': False,
        'pct_from_lower_band': None,
        'atr': None,
        'current_price': None,
        'is_valid': is_valid
    }
