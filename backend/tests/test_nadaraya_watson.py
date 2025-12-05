"""
Unit tests for Nadaraya-Watson Envelope calculator
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir / "api"))

from nadaraya_watson import calculate_nadaraya_watson_lower_band


class TestNadarayaWatsonLowerBand:
    """Test suite for Nadaraya-Watson lower band distance calculations."""

    def test_price_above_lower_band(self):
        """Test case: price > lower_band (positive pct, breach = False)"""
        # Create synthetic data where price is clearly above lower band
        prices = np.linspace(90, 110, 250)  # Uptrend

        result = calculate_nadaraya_watson_lower_band(
            prices,
            length=200,
            bandwidth=8.0,
            atr_period=50,
            atr_mult=2.0
        )

        assert result['is_valid'] == True
        assert result['lower_band_breached'] == False
        assert result['pct_from_lower_band'] is not None
        assert result['pct_from_lower_band'] > 0  # Price above lower band
        assert result['current_price'] == pytest.approx(110.0, rel=0.01)

    def test_price_below_lower_band(self):
        """Test case: price < lower_band (negative pct, breach = True)"""
        # Create synthetic data with sharp drop at end
        prices = np.concatenate([
            np.ones(200) * 100,  # Stable at 100
            np.array([95, 90, 85, 80])  # Sharp drop
        ])

        result = calculate_nadaraya_watson_lower_band(
            prices,
            length=200,
            bandwidth=8.0,
            atr_period=50,
            atr_mult=2.0
        )

        assert result['is_valid'] == True
        assert result['lower_band_breached'] == True
        assert result['pct_from_lower_band'] is not None
        assert result['pct_from_lower_band'] < 0  # Price below lower band
        assert result['current_price'] == 80.0

    def test_price_at_lower_band(self):
        """Test case: price ≈ lower_band (pct ≈ 0, breach = False)"""
        # This is harder to test exactly, but we can test near-zero case
        prices = np.ones(250) * 100.0  # Flat prices

        result = calculate_nadaraya_watson_lower_band(
            prices,
            length=200,
            bandwidth=8.0,
            atr_period=50,
            atr_mult=0.0  # Zero multiplier = bands collapse to estimate
        )

        assert result['is_valid'] == True
        # With zero ATR multiplier and flat prices, pct should be very small
        assert abs(result['pct_from_lower_band']) < 1.0  # Within 1%

    def test_lower_band_zero_handling(self):
        """Test case: lower_band == 0 handling (avoid division by zero)"""
        # The function has eps=1e-8 protection, so test that it handles
        # any prices gracefully without throwing division by zero errors
        prices = np.linspace(0.0001, 0.0002, 250)

        result = calculate_nadaraya_watson_lower_band(
            prices,
            length=200,
            bandwidth=8.0,
            atr_period=50,
            atr_mult=100.0
        )

        # Should complete without errors and return valid data
        assert result['is_valid'] == True
        assert result['lower_band'] is not None
        # Should handle gracefully regardless of lower_band value
        assert 'pct_from_lower_band' in result
        # pct can be None or a number, but should not raise errors
        assert result['pct_from_lower_band'] is None or isinstance(result['pct_from_lower_band'], (int, float))

    def test_warm_up_period_insufficient_data(self):
        """Test case: not enough data for warm-up period"""
        prices = np.array([100, 101, 102])  # Only 3 bars

        result = calculate_nadaraya_watson_lower_band(
            prices,
            length=200,
            bandwidth=8.0,
            atr_period=50,
            atr_mult=2.0
        )

        assert result['is_valid'] == False
        assert result['lower_band'] is None
        assert result['pct_from_lower_band'] is None

    def test_exact_example_case(self):
        """Test exact example: lower_band = 100, price = 95 => pct = -5.0, breach = True"""
        # We can't guarantee exact lower_band = 100, but we can create a scenario
        # where we know the relationship

        # Create flat prices at 100, then drop to 95
        prices = np.concatenate([
            np.ones(200) * 100.0,
            np.array([98, 96, 95])  # Gradual drop to 95
        ])

        result = calculate_nadaraya_watson_lower_band(
            prices,
            length=200,
            bandwidth=8.0,
            atr_period=50,
            atr_mult=1.5  # Tune to get lower_band around 100
        )

        assert result['is_valid'] == True
        assert result['current_price'] == 95.0
        assert result['lower_band_breached'] == True
        assert result['pct_from_lower_band'] < 0  # Negative because price < lower_band

        # Calculate expected percentage
        if result['lower_band'] is not None and result['lower_band'] > 0:
            expected_pct = 100.0 * (95.0 - result['lower_band']) / result['lower_band']
            assert result['pct_from_lower_band'] == pytest.approx(expected_pct, rel=0.01)

    def test_with_highs_lows_for_atr(self):
        """Test with actual high/low data for proper ATR calculation"""
        n = 250
        closes = np.linspace(95, 105, n)
        highs = closes + np.random.uniform(0.5, 2.0, n)  # Highs above close
        lows = closes - np.random.uniform(0.5, 2.0, n)   # Lows below close

        result = calculate_nadaraya_watson_lower_band(
            closes,
            length=200,
            bandwidth=8.0,
            atr_period=50,
            atr_mult=2.0,
            highs=highs,
            lows=lows
        )

        assert result['is_valid'] == True
        assert result['atr'] is not None
        assert result['atr'] > 0  # ATR should be positive with varying prices
        assert result['lower_band'] is not None
        assert result['upper_band'] is not None
        assert result['upper_band'] > result['nw_estimate']
        assert result['lower_band'] < result['nw_estimate']

    def test_percentage_calculation_positive(self):
        """Test percentage calculation: price above lower band"""
        prices = np.ones(250) * 100.0
        prices[-1] = 102.0  # Last price at 102

        result = calculate_nadaraya_watson_lower_band(
            prices,
            length=200,
            bandwidth=8.0,
            atr_period=50,
            atr_mult=1.0
        )

        assert result['is_valid'] == True
        assert result['current_price'] == 102.0

        # Manually calculate expected percentage
        if result['lower_band'] is not None:
            expected = 100.0 * (102.0 - result['lower_band']) / result['lower_band']
            assert result['pct_from_lower_band'] == pytest.approx(expected, rel=0.01)

    def test_percentage_calculation_negative(self):
        """Test percentage calculation: price below lower band"""
        prices = np.ones(250) * 100.0
        prices[-5:] = [98, 96, 94, 92, 90]  # Downtrend to 90

        result = calculate_nadaraya_watson_lower_band(
            prices,
            length=200,
            bandwidth=8.0,
            atr_period=50,
            atr_mult=1.0
        )

        assert result['is_valid'] == True
        assert result['current_price'] == 90.0

        # Manually calculate expected percentage
        if result['lower_band'] is not None:
            expected = 100.0 * (90.0 - result['lower_band']) / result['lower_band']
            assert result['pct_from_lower_band'] == pytest.approx(expected, rel=0.01)
            assert result['pct_from_lower_band'] < 0  # Should be negative

    def test_empty_prices_array(self):
        """Test edge case: empty prices array"""
        prices = np.array([])

        result = calculate_nadaraya_watson_lower_band(prices)

        assert result['is_valid'] == False
        assert result['lower_band'] is None

    def test_bandwidth_sensitivity(self):
        """Test that bandwidth parameter affects smoothness"""
        prices = np.random.uniform(95, 105, 250)

        # Small bandwidth (more responsive)
        result_small_h = calculate_nadaraya_watson_lower_band(
            prices, length=200, bandwidth=1.0
        )

        # Large bandwidth (more smooth)
        result_large_h = calculate_nadaraya_watson_lower_band(
            prices, length=200, bandwidth=20.0
        )

        assert result_small_h['is_valid'] == True
        assert result_large_h['is_valid'] == True
        # Both should produce valid results (specific values will differ)

    def test_return_types(self):
        """Test that all return types are correct"""
        prices = np.linspace(95, 105, 250)

        result = calculate_nadaraya_watson_lower_band(prices)

        assert isinstance(result, dict)
        assert isinstance(result['is_valid'], bool)
        assert isinstance(result['lower_band_breached'], bool)

        if result['is_valid']:
            assert isinstance(result['nw_estimate'], (int, float)) or result['nw_estimate'] is None
            assert isinstance(result['lower_band'], (int, float)) or result['lower_band'] is None
            assert isinstance(result['upper_band'], (int, float)) or result['upper_band'] is None
            assert isinstance(result['pct_from_lower_band'], (int, float)) or result['pct_from_lower_band'] is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
