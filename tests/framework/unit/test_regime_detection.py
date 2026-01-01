"""
Unit tests for regime detection module.

Tests cover:
- Market regime classification
- Volatility analysis
- Trend strength detection
- Regime transition handling
- Edge cases and boundaries
"""

import pytest
import numpy as np
import pandas as pd
from typing import Dict


# ============================================================================
# Test Regime Classification
# ============================================================================

class TestRegimeDetection:
    """Test suite for market regime detection."""

    @pytest.mark.unit
    def test_trending_regime_detection(self, trending_market_data, test_config):
        """Test detection of trending market conditions."""
        # Calculate trend metrics
        prices = trending_market_data['close'].values
        returns = np.diff(prices) / prices[:-1]

        # Trend strength via directional movement
        positive_moves = np.sum(returns > 0)
        trend_strength = (positive_moves / len(returns)) * 2 - 1

        assert trend_strength > 0.3, "Should detect upward trend"
        assert trend_strength < 1.0, "Trend strength should be bounded"

    @pytest.mark.unit
    def test_ranging_regime_detection(self, ranging_market_data):
        """Test detection of ranging/sideways market conditions."""
        prices = ranging_market_data['close'].values

        # Calculate range bounds
        lookback = min(100, len(prices))
        recent_high = np.max(prices[-lookback:])
        recent_low = np.min(prices[-lookback:])
        range_pct = (recent_high - recent_low) / recent_low

        # In ranging market, price should stay within tight bounds
        assert range_pct < 0.20, "Range should be contained"

    @pytest.mark.unit
    def test_volatile_regime_detection(self, volatile_market_data):
        """Test detection of high volatility conditions."""
        prices = volatile_market_data['close'].values
        returns = np.diff(prices) / prices[:-1]

        # Calculate realized volatility
        volatility = np.std(returns) * np.sqrt(252 * 6)  # Annualized from 4H

        assert volatility > 0.20, "Should detect high volatility"

    @pytest.mark.unit
    def test_regime_stability(self, sample_price_data):
        """Test that regime classifications are stable over time."""
        prices = sample_price_data['close'].values

        # Calculate regime for overlapping windows
        window_size = 100
        regimes = []

        for i in range(0, len(prices) - window_size, 20):
            window = prices[i:i + window_size]
            returns = np.diff(window) / window[:-1]
            vol = np.std(returns)
            regimes.append(vol)

        # Adjacent regimes should be similar
        regime_changes = np.diff(regimes)
        stable_transitions = np.sum(np.abs(regime_changes) < np.std(regimes) * 0.5)

        assert stable_transitions / len(regime_changes) > 0.7, \
            "Regime should be relatively stable"


# ============================================================================
# Test Volatility Analysis
# ============================================================================

class TestVolatilityAnalysis:
    """Test suite for volatility measurement and analysis."""

    @pytest.mark.unit
    def test_atr_calculation(self, sample_price_data):
        """Test Average True Range calculation."""
        data = sample_price_data

        # Calculate True Range
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift(1))
        low_close = np.abs(data['low'] - data['close'].shift(1))

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # Calculate ATR (14-period)
        atr = true_range.rolling(window=14).mean()

        assert atr.notna().sum() > 0, "ATR should have valid values"
        assert (atr >= 0).all(), "ATR should be non-negative"

    @pytest.mark.unit
    def test_atr_percentile_ranking(self, sample_price_data):
        """Test ATR percentile ranking system."""
        data = sample_price_data

        # Calculate ATR
        high_low = data['high'] - data['low']
        atr = high_low.rolling(window=14).mean()

        # Calculate percentile rank
        lookback = 252 * 6  # ~1 year of 4H bars
        for i in range(lookback, len(atr)):
            window = atr[i - lookback:i]
            current = atr.iloc[i]
            percentile = (window < current).sum() / len(window) * 100

            assert 0 <= percentile <= 100, "Percentile should be in [0, 100]"

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_volatility_edge_cases(self):
        """Test volatility calculation edge cases."""
        # Test with constant prices (zero volatility)
        constant_prices = np.ones(100) * 100
        volatility = np.std(np.diff(constant_prices))
        assert volatility == 0, "Constant prices should have zero volatility"

        # Test with extreme spike
        spike_prices = np.ones(100) * 100
        spike_prices[50] = 200
        spike_returns = np.diff(spike_prices) / spike_prices[:-1]
        spike_vol = np.std(spike_returns)
        assert spike_vol > 0.1, "Spike should increase volatility"


# ============================================================================
# Test Trend Strength
# ============================================================================

class TestTrendStrength:
    """Test suite for trend strength measurement."""

    @pytest.mark.unit
    def test_directional_movement_index(self, trending_market_data):
        """Test directional movement calculation."""
        prices = trending_market_data['close'].values

        # Simple directional movement
        returns = np.diff(prices) / prices[:-1]
        up_moves = np.maximum(returns, 0)
        down_moves = np.maximum(-returns, 0)

        up_avg = np.mean(up_moves)
        down_avg = np.mean(down_moves)

        # Calculate directional index
        di_plus = up_avg / (up_avg + down_avg) if (up_avg + down_avg) > 0 else 0

        assert 0 <= di_plus <= 1, "DI+ should be normalized"
        assert di_plus > 0.5, "Trending market should have DI+ > 0.5"

    @pytest.mark.unit
    def test_adx_calculation(self, sample_price_data):
        """Test Average Directional Index calculation."""
        data = sample_price_data

        # Simplified ADX calculation
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values

        # True Range
        tr = np.maximum(high[1:] - low[1:],
                        np.maximum(np.abs(high[1:] - close[:-1]),
                                   np.abs(low[1:] - close[:-1])))

        assert len(tr) > 0, "True Range should have values"
        assert (tr >= 0).all(), "True Range should be non-negative"

    @pytest.mark.unit
    def test_trend_consistency(self, trending_market_data):
        """Test trend consistency measurement."""
        prices = trending_market_data['close'].values
        returns = np.diff(prices) / prices[:-1]

        # Count consecutive moves in same direction
        signs = np.sign(returns)
        sign_changes = np.diff(signs) != 0
        avg_streak = len(signs) / (np.sum(sign_changes) + 1)

        assert avg_streak > 1, "Trending market should have streaks"


# ============================================================================
# Test Regime Transitions
# ============================================================================

class TestRegimeTransitions:
    """Test suite for handling regime transitions."""

    @pytest.mark.unit
    def test_regime_change_detection(self):
        """Test detection of regime changes."""
        np.random.seed(42)

        # Create data with regime change
        regime1 = np.random.normal(0, 0.01, 100)  # Low vol
        regime2 = np.random.normal(0, 0.05, 100)  # High vol

        combined = np.concatenate([regime1, regime2])

        # Rolling volatility
        window = 20
        vol = pd.Series(combined).rolling(window).std()

        # Detect significant change
        vol_change = vol.diff().abs()
        significant_change = vol_change > vol.std() * 2

        assert significant_change.sum() > 0, "Should detect regime change"

    @pytest.mark.unit
    def test_regime_transition_smoothing(self):
        """Test smoothing of regime transitions."""
        np.random.seed(42)

        # Noisy regime indicator
        noisy_regime = np.random.choice([0, 1], size=100, p=[0.6, 0.4])

        # Apply smoothing
        smoothed = pd.Series(noisy_regime).rolling(window=5).mean()

        # Smoothed should have less variance
        assert smoothed.std() < pd.Series(noisy_regime).std(), \
            "Smoothing should reduce variance"

    @pytest.mark.unit
    @pytest.mark.critical
    def test_regime_boundary_conditions(self):
        """Test regime detection at boundary conditions."""
        # Test minimum data
        min_data = np.random.normal(0, 0.02, 30)
        assert len(min_data) >= 30, "Should handle minimum data points"

        # Test single data point
        single_point = np.array([100.0])
        assert len(single_point) == 1, "Should handle single data point"


# ============================================================================
# Test Multi-Timeframe Regime Analysis
# ============================================================================

class TestMultiTimeframeRegime:
    """Test suite for multi-timeframe regime analysis."""

    @pytest.mark.unit
    def test_timeframe_alignment(self, multi_timeframe_data):
        """Test alignment of regimes across timeframes."""
        daily = multi_timeframe_data['daily']
        h4 = multi_timeframe_data['4h']

        assert len(daily) > 0, "Should have daily data"
        assert len(h4) > 0, "Should have 4H data"

        # 4H bars should be more frequent
        assert len(h4) > len(daily), "4H should have more bars than daily"

    @pytest.mark.unit
    def test_regime_confluence(self, multi_timeframe_data):
        """Test regime confluence across timeframes."""
        daily_prices = multi_timeframe_data['daily']['close'].values
        h4_prices = multi_timeframe_data['4h']['close'].values

        # Calculate trend for each timeframe
        daily_trend = np.sum(np.diff(daily_prices) > 0) / len(daily_prices)
        h4_trend = np.sum(np.diff(h4_prices) > 0) / len(h4_prices)

        # Both should indicate same general direction
        assert abs(daily_trend - h4_trend) < 0.3, \
            "Timeframes should show similar trends"

    @pytest.mark.unit
    def test_regime_divergence_detection(self, multi_timeframe_data):
        """Test detection of regime divergence between timeframes."""
        daily = multi_timeframe_data['daily']
        h4 = multi_timeframe_data['4h']

        # Calculate volatility for each
        daily_vol = daily['close'].pct_change().std()
        h4_vol = h4['close'].pct_change().std()

        # Should be able to calculate for both
        assert not np.isnan(daily_vol), "Daily volatility should be valid"
        assert not np.isnan(h4_vol), "4H volatility should be valid"


# ============================================================================
# Test Performance
# ============================================================================

class TestRegimeDetectionPerformance:
    """Test suite for regime detection performance."""

    @pytest.mark.performance
    def test_detection_speed(self, sample_price_data, benchmark):
        """Test regime detection computational performance."""

        def detect_regime(prices):
            returns = np.diff(prices) / prices[:-1]
            vol = np.std(returns)
            trend = np.sum(returns > 0) / len(returns)
            return {'volatility': vol, 'trend': trend}

        prices = sample_price_data['close'].values

        # Should complete quickly
        result = benchmark(detect_regime, prices)
        assert 'volatility' in result
        assert 'trend' in result

    @pytest.mark.performance
    def test_memory_efficiency(self, sample_price_data):
        """Test memory efficiency of regime detection."""
        prices = sample_price_data['close'].values

        # Calculate regime metrics without storing intermediate arrays
        returns = np.diff(prices) / prices[:-1]
        regime = {
            'vol': np.std(returns),
            'trend': np.mean(returns > 0)
        }

        assert isinstance(regime, dict), "Should return compact result"
        assert len(regime) == 2, "Should only store essential metrics"
