"""
Unit tests for percentile logic engine.

Tests cover:
- Percentile calculation accuracy
- Bin assignment logic
- Forward return analysis
- Statistical significance testing
- Edge cases and boundary conditions
"""

import pytest
import numpy as np
import pandas as pd
from scipy import stats


# ============================================================================
# Test Percentile Calculation
# ============================================================================

class TestPercentileCalculation:
    """Test suite for percentile calculation logic."""

    @pytest.mark.unit
    @pytest.mark.critical
    def test_basic_percentile_calculation(self, sample_returns_distribution):
        """Test basic percentile calculation."""
        returns = sample_returns_distribution

        # Calculate percentiles
        p25 = np.percentile(returns, 25)
        p50 = np.percentile(returns, 50)
        p75 = np.percentile(returns, 75)

        assert p25 < p50 < p75, "Percentiles should be ordered"
        assert np.isclose(p50, np.median(returns)), "50th percentile is median"

    @pytest.mark.unit
    def test_percentile_interpolation(self):
        """Test percentile interpolation methods."""
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

        # Different interpolation methods
        linear = np.percentile(data, 50, method='linear')
        lower = np.percentile(data, 50, method='lower')
        higher = np.percentile(data, 50, method='higher')

        assert lower <= linear <= higher, "Interpolation should be bounded"

    @pytest.mark.unit
    def test_percentile_rank_calculation(self, sample_returns_distribution):
        """Test percentile rank calculation."""
        returns = sample_returns_distribution

        # Calculate percentile rank for specific value
        test_value = 0.01
        rank = (returns < test_value).sum() / len(returns) * 100

        assert 0 <= rank <= 100, "Percentile rank should be in [0, 100]"

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_percentile_edge_cases(self):
        """Test percentile calculation edge cases."""
        # Single value
        single = np.array([5.0])
        assert np.percentile(single, 50) == 5.0

        # All same values
        constant = np.ones(100)
        assert np.percentile(constant, 25) == 1.0
        assert np.percentile(constant, 75) == 1.0

        # Empty array handling
        with pytest.raises((ValueError, IndexError)):
            np.percentile(np.array([]), 50)


# ============================================================================
# Test Bin Assignment
# ============================================================================

class TestBinAssignment:
    """Test suite for percentile bin assignment logic."""

    @pytest.mark.unit
    @pytest.mark.critical
    def test_standard_bin_assignment(self, percentile_bins):
        """Test assignment to standard percentile bins."""
        # Test values at bin boundaries
        test_cases = [
            (2.5, '0-5'),
            (10, '5-15'),
            (20, '15-25'),
            (40, '25-50'),
            (60, '50-75'),
            (80, '75-85'),
            (90, '85-95'),
            (97.5, '95-100')
        ]

        for percentile, expected_bin in test_cases:
            # Find matching bin
            for lower, upper in percentile_bins:
                if lower <= percentile < upper:
                    bin_name = f"{lower}-{upper}"
                    break
            else:
                # Handle 100th percentile
                if percentile == 100:
                    bin_name = "95-100"

            # Verify bin assignment
            assert expected_bin in bin_name or bin_name in expected_bin, \
                f"Percentile {percentile} should be in bin {expected_bin}"

    @pytest.mark.unit
    def test_bin_coverage(self, percentile_bins):
        """Test that bins cover full range without gaps."""
        sorted_bins = sorted(percentile_bins)

        # Check no gaps
        for i in range(len(sorted_bins) - 1):
            current_upper = sorted_bins[i][1]
            next_lower = sorted_bins[i + 1][0]
            assert current_upper == next_lower, \
                f"Gap between bins: {current_upper} and {next_lower}"

        # Check full coverage
        assert sorted_bins[0][0] == 0, "Should start at 0"
        assert sorted_bins[-1][1] == 100, "Should end at 100"

    @pytest.mark.unit
    def test_bin_distribution(self, sample_returns_distribution, percentile_bins):
        """Test distribution of values across bins."""
        returns = sample_returns_distribution

        # Assign each return to a bin
        bin_counts = {f"{lower}-{upper}": 0 for lower, upper in percentile_bins}

        for ret in returns:
            percentile = (returns < ret).sum() / len(returns) * 100

            for lower, upper in percentile_bins:
                if lower <= percentile < upper or (percentile == 100 and upper == 100):
                    bin_name = f"{lower}-{upper}"
                    bin_counts[bin_name] += 1
                    break

        # Verify all returns were assigned
        total_assigned = sum(bin_counts.values())
        assert total_assigned == len(returns), \
            "All returns should be assigned to bins"

    @pytest.mark.unit
    def test_boundary_value_assignment(self, percentile_bins):
        """Test assignment of boundary values."""
        # Test exact boundary values
        boundaries = [0, 5, 15, 25, 50, 75, 85, 95, 100]

        for boundary in boundaries:
            assigned = False
            for lower, upper in percentile_bins:
                if lower <= boundary < upper or (boundary == 100 and upper == 100):
                    assigned = True
                    break

            assert assigned, f"Boundary {boundary} should be assigned to a bin"


# ============================================================================
# Test Forward Return Analysis
# ============================================================================

class TestForwardReturnAnalysis:
    """Test suite for forward return analysis."""

    @pytest.mark.unit
    def test_forward_return_calculation(self, sample_price_data):
        """Test forward return calculation."""
        prices = sample_price_data['close'].values

        # Calculate 1-period forward returns
        forward_returns = (prices[1:] - prices[:-1]) / prices[:-1]

        assert len(forward_returns) == len(prices) - 1
        assert not np.isnan(forward_returns).any()

    @pytest.mark.unit
    def test_forward_return_statistics(self, forward_return_stats):
        """Test forward return statistics by bin."""
        for bin_name, stats in forward_return_stats.items():
            # Verify required fields
            assert 'mean' in stats
            assert 'std' in stats
            assert 'samples' in stats
            assert 't_score' in stats

            # Verify values are reasonable
            assert stats['samples'] > 0
            assert stats['std'] >= 0
            assert -1 < stats['mean'] < 1  # Returns should be reasonable

    @pytest.mark.unit
    def test_forward_return_by_percentile(self, sample_price_data, percentile_bins):
        """Test forward return analysis by percentile bin."""
        prices = sample_price_data['close'].values
        returns = np.diff(prices) / prices[:-1]

        # Calculate percentile ranks
        lookback = 100
        forward_horizon = 1

        results = {}

        for i in range(lookback, len(prices) - forward_horizon):
            # Historical window
            hist_window = returns[i - lookback:i]

            # Current return percentile
            current_ret = returns[i]
            percentile = (hist_window < current_ret).sum() / len(hist_window) * 100

            # Forward return
            forward_ret = (prices[i + forward_horizon] - prices[i]) / prices[i]

            # Assign to bin
            for lower, upper in percentile_bins:
                if lower <= percentile < upper or (percentile == 100 and upper == 100):
                    bin_name = f"{lower}-{upper}"
                    if bin_name not in results:
                        results[bin_name] = []
                    results[bin_name].append(forward_ret)
                    break

        # Verify all bins have data
        assert len(results) > 0, "Should have forward returns"

    @pytest.mark.unit
    def test_multi_period_forward_returns(self, sample_price_data):
        """Test multi-period forward return calculation."""
        prices = sample_price_data['close'].values

        # Calculate returns for different forward horizons
        horizons = [1, 5, 20]

        for h in horizons:
            if len(prices) > h:
                forward_returns = (prices[h:] - prices[:-h]) / prices[:-h]
                assert len(forward_returns) == len(prices) - h
                assert not np.isnan(forward_returns).any()


# ============================================================================
# Test Statistical Significance
# ============================================================================

class TestStatisticalSignificance:
    """Test suite for statistical significance testing."""

    @pytest.mark.unit
    @pytest.mark.critical
    def test_t_score_calculation(self, forward_return_stats, statistical_validators):
        """Test t-score calculation for forward returns."""
        for bin_name, bin_stats in forward_return_stats.items():
            mean = bin_stats['mean']
            std = bin_stats['std']
            n = bin_stats['samples']
            expected_t = bin_stats['t_score']

            # Calculate t-score
            if n > 1 and std > 0:
                se = std / np.sqrt(n)
                calculated_t = mean / se

                # Verify calculation
                assert np.isclose(calculated_t, expected_t, atol=0.1), \
                    f"T-score mismatch for {bin_name}"

    @pytest.mark.unit
    def test_confidence_intervals(self, forward_return_stats):
        """Test confidence interval calculation."""
        for bin_name, bin_stats in forward_return_stats.items():
            mean = bin_stats['mean']
            std = bin_stats['std']
            n = bin_stats['samples']

            if n > 1:
                # 95% confidence interval
                se = std / np.sqrt(n)
                t_critical = stats.t.ppf(0.975, n - 1)
                margin = t_critical * se

                ci_lower = mean - margin
                ci_upper = mean + margin

                assert ci_lower < mean < ci_upper, \
                    "Mean should be within confidence interval"

    @pytest.mark.unit
    def test_sample_size_requirements(self, forward_return_stats, test_config):
        """Test minimum sample size requirements."""
        min_samples = test_config['min_samples']

        for bin_name, bin_stats in forward_return_stats.items():
            n = bin_stats['samples']

            if n >= min_samples:
                # Should be able to calculate valid statistics
                assert bin_stats['std'] >= 0
                assert not np.isnan(bin_stats['mean'])

    @pytest.mark.unit
    def test_statistical_power(self):
        """Test statistical power calculation."""
        # Sample size needed to detect effect with 80% power
        effect_size = 0.5  # Cohen's d
        alpha = 0.05
        power = 0.80

        # Simplified power calculation
        from scipy.stats import norm

        z_alpha = norm.ppf(1 - alpha / 2)
        z_beta = norm.ppf(power)

        n_required = 2 * ((z_alpha + z_beta) / effect_size) ** 2

        assert n_required > 0, "Required sample size should be positive"
        assert n_required < 1000, "Sample size should be reasonable"


# ============================================================================
# Test Percentile Stability
# ============================================================================

class TestPercentileStability:
    """Test suite for percentile stability and consistency."""

    @pytest.mark.unit
    def test_rolling_percentile_stability(self, sample_price_data):
        """Test stability of rolling percentile calculations."""
        returns = sample_price_data['close'].pct_change().dropna()

        window = 100
        percentile_series = []

        for i in range(window, len(returns)):
            hist = returns[i - window:i]
            current = returns.iloc[i]
            pct = (hist < current).sum() / len(hist) * 100
            percentile_series.append(pct)

        percentile_series = np.array(percentile_series)

        # Percentiles should vary but not too erratically
        pct_changes = np.diff(percentile_series)
        assert np.std(pct_changes) < 30, "Percentiles should be relatively stable"

    @pytest.mark.unit
    def test_lookback_period_sensitivity(self, sample_returns_distribution):
        """Test sensitivity to lookback period."""
        returns = sample_returns_distribution

        lookbacks = [50, 100, 200, 500]
        test_value = 0.01

        percentiles = []
        for lookback in lookbacks:
            if len(returns) >= lookback:
                window = returns[-lookback:]
                pct = (window < test_value).sum() / len(window) * 100
                percentiles.append(pct)

        # Percentiles should converge with longer lookbacks
        if len(percentiles) > 1:
            pct_range = max(percentiles) - min(percentiles)
            assert pct_range < 20, "Percentiles should converge"


# ============================================================================
# Test Performance
# ============================================================================

class TestPercentilePerformance:
    """Test suite for percentile calculation performance."""

    @pytest.mark.performance
    def test_calculation_speed(self, sample_returns_distribution, benchmark):
        """Test percentile calculation speed."""
        returns = sample_returns_distribution

        def calculate_percentiles(data):
            return np.percentile(data, [25, 50, 75, 95])

        result = benchmark(calculate_percentiles, returns)
        assert len(result) == 4

    @pytest.mark.performance
    def test_vectorized_bin_assignment(self, sample_returns_distribution, benchmark):
        """Test vectorized bin assignment performance."""
        returns = sample_returns_distribution

        def assign_bins(data):
            percentiles = np.percentile(data, range(0, 101, 5))
            return np.digitize(data, percentiles)

        result = benchmark(assign_bins, returns)
        assert len(result) == len(returns)
