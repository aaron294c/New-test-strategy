"""
Pytest configuration and fixtures for trading framework tests.

This module provides shared fixtures, test utilities, and configuration
for comprehensive testing of the trading framework components.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import sys
import os

# Add backend to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))


# ============================================================================
# Test Configuration
# ============================================================================

@pytest.fixture(scope="session")
def test_config():
    """Global test configuration."""
    return {
        'random_seed': 42,
        'min_samples': 30,
        'confidence_level': 0.95,
        'statistical_threshold': 0.05,
        'coverage_target': 0.90
    }


# ============================================================================
# Market Data Fixtures
# ============================================================================

@pytest.fixture
def sample_price_data():
    """Generate sample price data for testing."""
    np.random.seed(42)
    dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='1H')

    # Generate realistic price series with trend and volatility
    n = len(dates)
    trend = np.linspace(100, 150, n)
    noise = np.random.normal(0, 2, n)
    momentum = np.cumsum(np.random.normal(0, 0.5, n))

    prices = trend + noise + momentum
    prices = np.maximum(prices, 1)  # Ensure positive prices

    return pd.DataFrame({
        'timestamp': dates,
        'open': prices + np.random.uniform(-1, 1, n),
        'high': prices + np.random.uniform(0, 2, n),
        'low': prices - np.random.uniform(0, 2, n),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, n)
    })


@pytest.fixture
def trending_market_data():
    """Generate trending market scenario."""
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='4H')
    n = len(dates)

    # Strong uptrend
    trend = np.linspace(100, 200, n)
    noise = np.random.normal(0, 3, n)

    prices = trend + noise

    return pd.DataFrame({
        'timestamp': dates,
        'close': prices,
        'high': prices + np.abs(np.random.normal(0, 2, n)),
        'low': prices - np.abs(np.random.normal(0, 2, n)),
        'volume': np.random.randint(5000000, 15000000, n)
    })


@pytest.fixture
def ranging_market_data():
    """Generate ranging/sideways market scenario."""
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='4H')
    n = len(dates)

    # Sideways movement
    base_price = 100
    noise = np.random.normal(0, 5, n)

    prices = base_price + noise

    return pd.DataFrame({
        'timestamp': dates,
        'close': prices,
        'high': prices + np.abs(np.random.normal(0, 2, n)),
        'low': prices - np.abs(np.random.normal(0, 2, n)),
        'volume': np.random.randint(3000000, 8000000, n)
    })


@pytest.fixture
def volatile_market_data():
    """Generate high volatility market scenario."""
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='4H')
    n = len(dates)

    # High volatility with mean reversion
    prices = 100 + np.cumsum(np.random.normal(0, 5, n))

    return pd.DataFrame({
        'timestamp': dates,
        'close': prices,
        'high': prices + np.abs(np.random.normal(0, 8, n)),
        'low': prices - np.abs(np.random.normal(0, 8, n)),
        'volume': np.random.randint(10000000, 30000000, n)
    })


# ============================================================================
# Statistical Fixtures
# ============================================================================

@pytest.fixture
def percentile_bins():
    """Standard percentile bins used across the framework."""
    return [
        (0, 5), (5, 15), (15, 25), (25, 50),
        (50, 75), (75, 85), (85, 95), (95, 100)
    ]


@pytest.fixture
def sample_returns_distribution():
    """Generate sample returns distribution."""
    np.random.seed(42)

    # Create realistic return distribution
    # Mix of normal and fat-tailed returns
    normal_returns = np.random.normal(0, 0.01, 8000)
    fat_tail_returns = np.random.standard_t(df=3, size=2000) * 0.02

    returns = np.concatenate([normal_returns, fat_tail_returns])
    np.random.shuffle(returns)

    return returns


@pytest.fixture
def forward_return_stats():
    """Sample forward return statistics by percentile bin."""
    return {
        '0-5': {'mean': 0.025, 'std': 0.015, 'samples': 150, 't_score': 2.5},
        '5-15': {'mean': 0.018, 'std': 0.012, 'samples': 300, 't_score': 2.1},
        '15-25': {'mean': 0.012, 'std': 0.011, 'samples': 300, 't_score': 1.8},
        '25-50': {'mean': 0.005, 'std': 0.010, 'samples': 750, 't_score': 0.9},
        '50-75': {'mean': -0.003, 'std': 0.010, 'samples': 750, 't_score': -0.5},
        '75-85': {'mean': -0.008, 'std': 0.012, 'samples': 300, 't_score': -1.2},
        '85-95': {'mean': -0.015, 'std': 0.014, 'samples': 300, 't_score': -1.9},
        '95-100': {'mean': -0.022, 'std': 0.018, 'samples': 150, 't_score': -2.3}
    }


# ============================================================================
# Regime Detection Fixtures
# ============================================================================

@pytest.fixture
def regime_scenarios():
    """Various market regime scenarios for testing."""
    return {
        'strong_trend': {
            'atr_percentile': 85,
            'rsi': 72,
            'trend_strength': 0.85,
            'expected_regime': 'trending'
        },
        'range_bound': {
            'atr_percentile': 45,
            'rsi': 50,
            'trend_strength': 0.3,
            'expected_regime': 'ranging'
        },
        'high_volatility': {
            'atr_percentile': 95,
            'rsi': 65,
            'trend_strength': 0.5,
            'expected_regime': 'volatile'
        },
        'low_volatility': {
            'atr_percentile': 15,
            'rsi': 48,
            'trend_strength': 0.2,
            'expected_regime': 'quiet'
        }
    }


# ============================================================================
# Risk Management Fixtures
# ============================================================================

@pytest.fixture
def portfolio_config():
    """Sample portfolio configuration."""
    return {
        'total_capital': 100000,
        'max_position_size': 0.10,
        'max_portfolio_heat': 0.20,
        'min_expectancy': 0.5,
        'max_correlation': 0.7
    }


@pytest.fixture
def position_scenarios():
    """Sample position scenarios for testing."""
    return {
        'high_conviction': {
            'expectancy': 1.5,
            'win_rate': 0.65,
            'avg_win': 0.025,
            'avg_loss': -0.012,
            't_score': 3.2
        },
        'medium_conviction': {
            'expectancy': 0.8,
            'win_rate': 0.58,
            'avg_win': 0.018,
            'avg_loss': -0.011,
            't_score': 2.1
        },
        'low_conviction': {
            'expectancy': 0.3,
            'win_rate': 0.52,
            'avg_win': 0.012,
            'avg_loss': -0.010,
            't_score': 1.2
        }
    }


# ============================================================================
# Multi-Timeframe Fixtures
# ============================================================================

@pytest.fixture
def multi_timeframe_data():
    """Generate aligned multi-timeframe data."""
    np.random.seed(42)

    # Daily data
    daily_dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    daily_prices = 100 + np.cumsum(np.random.normal(0, 1, len(daily_dates)))

    # 4H data (aligned with daily)
    h4_dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='4H')
    h4_prices = 100 + np.cumsum(np.random.normal(0, 0.5, len(h4_dates)))

    return {
        'daily': pd.DataFrame({
            'timestamp': daily_dates,
            'close': daily_prices,
            'high': daily_prices + np.random.uniform(0, 2, len(daily_dates)),
            'low': daily_prices - np.random.uniform(0, 2, len(daily_dates)),
        }),
        '4h': pd.DataFrame({
            'timestamp': h4_dates,
            'close': h4_prices,
            'high': h4_prices + np.random.uniform(0, 1, len(h4_dates)),
            'low': h4_prices - np.random.uniform(0, 1, len(h4_dates)),
        })
    }


# ============================================================================
# Validation Utilities
# ============================================================================

@pytest.fixture
def statistical_validators():
    """Statistical validation utilities."""
    class Validators:
        @staticmethod
        def validate_t_score(mean, std, n, expected_t=None):
            """Validate t-score calculation."""
            if n < 2:
                return False
            se = std / np.sqrt(n)
            t = mean / se if se > 0 else 0
            if expected_t is not None:
                return abs(t - expected_t) < 0.01
            return True

        @staticmethod
        def validate_percentile_bins(data, bins):
            """Validate percentile bin assignments."""
            percentiles = np.percentile(data, [b[1] for b in bins[:-1]] + [100])
            for i, (lower, upper) in enumerate(bins):
                if i < len(percentiles) - 1:
                    assert percentiles[i] <= percentiles[i + 1]
            return True

        @staticmethod
        def validate_expectancy(win_rate, avg_win, avg_loss):
            """Validate expectancy calculation."""
            expected = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
            return expected

    return Validators()


# ============================================================================
# Mock Data Helpers
# ============================================================================

@pytest.fixture
def mock_api_response():
    """Mock API response for integration testing."""
    return {
        'AAPL': {
            '4H': {
                '85-95': {
                    'mean': 0.015,
                    'median': 0.012,
                    'std': 0.008,
                    'samples': 250,
                    't_score': 2.8
                }
            },
            'metadata': {
                'personality': 'Balanced Growth',
                'volatility': 'Medium',
                'ease_rating': 7
            }
        }
    }


# ============================================================================
# Test Utilities
# ============================================================================

class TestHelpers:
    """Helper methods for testing."""

    @staticmethod
    def assert_valid_probability(value):
        """Assert value is a valid probability."""
        assert 0 <= value <= 1, f"Invalid probability: {value}"

    @staticmethod
    def assert_valid_percentile(value):
        """Assert value is a valid percentile."""
        assert 0 <= value <= 100, f"Invalid percentile: {value}"

    @staticmethod
    def assert_statistical_significance(t_score, threshold=1.96):
        """Assert statistical significance at 95% confidence."""
        assert abs(t_score) >= threshold, f"Not statistically significant: {t_score}"

    @staticmethod
    def generate_price_series(n_periods, start_price=100, volatility=0.02):
        """Generate realistic price series."""
        np.random.seed(42)
        returns = np.random.normal(0, volatility, n_periods)
        prices = start_price * np.exp(np.cumsum(returns))
        return prices


@pytest.fixture
def test_helpers():
    """Provide test helper utilities."""
    return TestHelpers()
