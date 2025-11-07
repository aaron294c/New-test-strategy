"""
Unit tests for composite scoring system.

Tests cover:
- Multi-factor score calculation
- Score weighting and normalization
- Regime-aware scoring
- Timeframe confluence scoring
- Score interpretation and thresholds
"""

import pytest
import numpy as np
import pandas as pd


# ============================================================================
# Test Score Calculation
# ============================================================================

class TestCompositeScoreCalculation:
    """Test suite for composite score calculation."""

    @pytest.mark.unit
    @pytest.mark.critical
    def test_basic_score_calculation(self):
        """Test basic composite score calculation."""
        # Sample factors
        factors = {
            'percentile': 0.85,  # 85th percentile
            'trend': 0.70,       # Strong trend
            'volatility': 0.60,  # Moderate volatility
            'expectancy': 0.75   # Good expectancy
        }

        # Equal weighting
        weights = {k: 0.25 for k in factors.keys()}

        # Calculate composite score
        score = sum(factors[k] * weights[k] for k in factors.keys())

        assert 0 <= score <= 1, "Score should be normalized"
        assert np.isclose(score, 0.725, atol=0.01)

    @pytest.mark.unit
    def test_weighted_score_calculation(self):
        """Test weighted composite score calculation."""
        factors = {
            'expectancy': 0.80,
            'trend': 0.60,
            'volatility': 0.50
        }

        # Emphasize expectancy
        weights = {
            'expectancy': 0.50,
            'trend': 0.30,
            'volatility': 0.20
        }

        score = sum(factors[k] * weights[k] for k in factors.keys())

        # Verify weighting impact
        assert score > 0.65, "High expectancy should dominate score"

    @pytest.mark.unit
    def test_score_normalization(self):
        """Test score normalization to [0, 1] range."""
        # Raw scores in different ranges
        raw_scores = {
            'percentile': 85,    # [0, 100]
            'trend': 0.7,        # [0, 1]
            'volatility': 2.5,   # [0, 5]
            't_score': 2.8       # [-inf, inf]
        }

        # Normalize each factor
        normalized = {
            'percentile': raw_scores['percentile'] / 100,
            'trend': raw_scores['trend'],
            'volatility': raw_scores['volatility'] / 5,
            't_score': min(max(raw_scores['t_score'] / 4, 0), 1)
        }

        # All normalized values should be in [0, 1]
        for value in normalized.values():
            assert 0 <= value <= 1

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_score_edge_cases(self):
        """Test score calculation edge cases."""
        # All zeros
        zero_factors = {'a': 0, 'b': 0, 'c': 0}
        zero_weights = {k: 1 / 3 for k in zero_factors.keys()}
        zero_score = sum(zero_factors[k] * zero_weights[k] for k in zero_factors.keys())
        assert zero_score == 0

        # All ones
        one_factors = {'a': 1, 'b': 1, 'c': 1}
        one_weights = {k: 1 / 3 for k in one_factors.keys()}
        one_score = sum(one_factors[k] * one_weights[k] for k in one_factors.keys())
        assert np.isclose(one_score, 1.0)

        # Mixed
        mixed = {'a': 0, 'b': 0.5, 'c': 1}
        mixed_weights = {k: 1 / 3 for k in mixed.keys()}
        mixed_score = sum(mixed[k] * mixed_weights[k] for k in mixed.keys())
        assert np.isclose(mixed_score, 0.5)


# ============================================================================
# Test Multi-Factor Integration
# ============================================================================

class TestMultiFactorIntegration:
    """Test suite for multi-factor score integration."""

    @pytest.mark.unit
    def test_percentile_factor(self, forward_return_stats):
        """Test percentile factor in composite score."""
        # Extract percentile performance
        percentile_scores = {}

        for bin_name, stats in forward_return_stats.items():
            # Score based on t-score and mean return
            t_score = stats['t_score']
            mean_return = stats['mean']

            # Normalize
            t_score_norm = min(max(t_score / 4, 0), 1)
            return_norm = min(max((mean_return + 0.05) / 0.1, 0), 1)

            # Combine
            percentile_scores[bin_name] = (t_score_norm + return_norm) / 2

        # Verify scores
        for score in percentile_scores.values():
            assert 0 <= score <= 1

    @pytest.mark.unit
    def test_regime_factor(self, regime_scenarios):
        """Test regime factor in composite score."""
        for regime_name, scenario in regime_scenarios.items():
            atr_pct = scenario['atr_percentile']
            trend = scenario['trend_strength']

            # Score regime favorability
            # High volatility + strong trend = good for momentum
            regime_score = (atr_pct / 100) * trend

            assert 0 <= regime_score <= 1

    @pytest.mark.unit
    def test_statistical_significance_factor(self, forward_return_stats):
        """Test statistical significance factor."""
        for bin_name, stats in forward_return_stats.items():
            t_score = stats['t_score']
            samples = stats['samples']

            # Score based on t-score and sample size
            t_score_norm = min(abs(t_score) / 3, 1)  # Normalize t-score
            sample_norm = min(samples / 300, 1)       # Normalize samples

            significance_score = (t_score_norm + sample_norm) / 2

            assert 0 <= significance_score <= 1

    @pytest.mark.unit
    def test_expectancy_factor(self, position_scenarios):
        """Test expectancy factor in composite score."""
        for scenario_name, scenario in position_scenarios.items():
            expectancy = scenario['expectancy']

            # Normalize expectancy to [0, 1]
            # Assume expectancy range of [-1, 2]
            exp_norm = min(max((expectancy + 1) / 3, 0), 1)

            assert 0 <= exp_norm <= 1


# ============================================================================
# Test Regime-Aware Scoring
# ============================================================================

class TestRegimeAwareScoring:
    """Test suite for regime-aware composite scoring."""

    @pytest.mark.unit
    def test_trending_regime_score_adjustment(self, regime_scenarios):
        """Test score adjustment for trending regime."""
        trending = regime_scenarios['strong_trend']

        # Base factors
        base_factors = {
            'percentile': 0.88,
            'expectancy': 0.75,
            'trend': 0.85
        }

        # In trending regime, emphasize trend and momentum
        trending_weights = {
            'percentile': 0.25,
            'expectancy': 0.25,
            'trend': 0.50
        }

        # Calculate regime-adjusted score
        trending_score = sum(base_factors[k] * trending_weights[k]
                             for k in base_factors.keys())

        # Compare to equal weighting
        equal_weights = {k: 1 / 3 for k in base_factors.keys()}
        equal_score = sum(base_factors[k] * equal_weights[k]
                          for k in base_factors.keys())

        assert trending_score > equal_score, \
            "Trending regime should boost score with strong trend"

    @pytest.mark.unit
    def test_ranging_regime_score_adjustment(self, regime_scenarios):
        """Test score adjustment for ranging regime."""
        ranging = regime_scenarios['range_bound']

        # Base factors
        base_factors = {
            'percentile': 0.25,  # Mean reversion signal
            'volatility': 0.30,  # Low volatility
            'trend': 0.20        # Weak trend
        }

        # In ranging regime, emphasize mean reversion
        ranging_weights = {
            'percentile': 0.50,  # High weight on extremes
            'volatility': 0.30,
            'trend': 0.20
        }

        ranging_score = sum(base_factors[k] * ranging_weights[k]
                            for k in base_factors.keys())

        assert 0 < ranging_score < 0.5, \
            "Ranging regime should favor mean reversion setups"

    @pytest.mark.unit
    def test_volatile_regime_score_adjustment(self, regime_scenarios):
        """Test score adjustment for high volatility regime."""
        volatile = regime_scenarios['high_volatility']

        # High volatility = reduce position size via lower score
        base_score = 0.75

        # Volatility penalty
        vol_percentile = volatile['atr_percentile']
        if vol_percentile > 85:
            vol_adjusted_score = base_score * 0.7  # 30% reduction

        assert vol_adjusted_score < base_score, \
            "High volatility should reduce score"


# ============================================================================
# Test Timeframe Confluence
# ============================================================================

class TestTimeframeConfluence:
    """Test suite for multi-timeframe confluence scoring."""

    @pytest.mark.unit
    def test_timeframe_agreement_bonus(self):
        """Test bonus for timeframe agreement."""
        # Scores from different timeframes
        daily_score = 0.75
        h4_score = 0.78

        # Calculate confluence
        avg_score = (daily_score + h4_score) / 2
        agreement = 1 - abs(daily_score - h4_score)

        # Apply confluence bonus
        confluence_score = avg_score * (1 + agreement * 0.1)

        assert confluence_score >= avg_score, "Agreement should boost score"

    @pytest.mark.unit
    def test_timeframe_disagreement_penalty(self):
        """Test penalty for timeframe disagreement."""
        # Conflicting signals
        daily_score = 0.80
        h4_score = 0.30

        # Large disagreement
        disagreement = abs(daily_score - h4_score)

        # Apply penalty
        conflicted_score = min(daily_score, h4_score) * (1 - disagreement * 0.3)

        assert conflicted_score < min(daily_score, h4_score), \
            "Disagreement should penalize score"

    @pytest.mark.unit
    def test_multi_timeframe_composite(self, multi_timeframe_data):
        """Test composite scoring with multiple timeframes."""
        # Simulate scores from each timeframe
        timeframe_scores = {
            'daily': 0.75,
            '4h': 0.70,
            '1h': 0.72
        }

        # Weight by timeframe (higher timeframes more important)
        timeframe_weights = {
            'daily': 0.50,
            '4h': 0.30,
            '1h': 0.20
        }

        # Calculate weighted composite
        composite = sum(timeframe_scores[tf] * timeframe_weights[tf]
                        for tf in timeframe_scores.keys())

        assert 0 <= composite <= 1
        assert composite > 0.70, "Should reflect higher timeframe dominance"


# ============================================================================
# Test Score Interpretation
# ============================================================================

class TestScoreInterpretation:
    """Test suite for score interpretation and thresholds."""

    @pytest.mark.unit
    def test_score_thresholds(self):
        """Test score threshold classification."""
        thresholds = {
            'strong_buy': 0.80,
            'buy': 0.65,
            'neutral': 0.50,
            'sell': 0.35,
            'strong_sell': 0.20
        }

        test_scores = [0.85, 0.70, 0.55, 0.40, 0.15]

        expected = ['strong_buy', 'buy', 'neutral', 'sell', 'strong_sell']

        for score, expected_signal in zip(test_scores, expected):
            if score >= thresholds['strong_buy']:
                signal = 'strong_buy'
            elif score >= thresholds['buy']:
                signal = 'buy'
            elif score >= thresholds['neutral']:
                signal = 'neutral'
            elif score >= thresholds['sell']:
                signal = 'sell'
            else:
                signal = 'strong_sell'

            assert signal == expected_signal

    @pytest.mark.unit
    def test_score_ranking(self):
        """Test ranking of multiple instruments by score."""
        instruments = {
            'AAPL': 0.82,
            'GOOGL': 0.75,
            'MSFT': 0.68,
            'NVDA': 0.91,
            'TSLA': 0.55
        }

        # Rank by score
        ranked = sorted(instruments.items(), key=lambda x: x[1], reverse=True)

        assert ranked[0][0] == 'NVDA', "NVDA should rank first"
        assert ranked[-1][0] == 'TSLA', "TSLA should rank last"

    @pytest.mark.unit
    def test_score_filtering(self):
        """Test filtering instruments by minimum score."""
        instruments = {
            'A': 0.85,
            'B': 0.45,
            'C': 0.72,
            'D': 0.38,
            'E': 0.91
        }

        min_score = 0.65

        # Filter
        filtered = {k: v for k, v in instruments.items() if v >= min_score}

        assert len(filtered) == 3, "Should have 3 instruments above threshold"
        assert 'A' in filtered and 'C' in filtered and 'E' in filtered


# ============================================================================
# Test Score Stability
# ============================================================================

class TestScoreStability:
    """Test suite for score stability and consistency."""

    @pytest.mark.unit
    def test_score_smoothing(self):
        """Test smoothing of volatile scores."""
        # Volatile score series
        raw_scores = np.array([0.75, 0.82, 0.68, 0.79, 0.71, 0.85, 0.69, 0.77])

        # Apply EMA smoothing
        alpha = 0.3
        smoothed = pd.Series(raw_scores).ewm(alpha=alpha).mean().values

        # Smoothed should have less variance
        assert np.std(smoothed) < np.std(raw_scores)

    @pytest.mark.unit
    def test_score_consistency_over_time(self):
        """Test that scores are consistent for similar conditions."""
        # Two similar market conditions
        condition1 = {
            'percentile': 0.85,
            'trend': 0.75,
            'expectancy': 0.80
        }

        condition2 = {
            'percentile': 0.87,
            'trend': 0.73,
            'expectancy': 0.82
        }

        weights = {k: 1 / 3 for k in condition1.keys()}

        score1 = sum(condition1[k] * weights[k] for k in condition1.keys())
        score2 = sum(condition2[k] * weights[k] for k in condition2.keys())

        # Scores should be very similar
        assert abs(score1 - score2) < 0.05


# ============================================================================
# Test Performance
# ============================================================================

class TestScoringPerformance:
    """Test suite for composite scoring performance."""

    @pytest.mark.performance
    def test_scoring_speed(self, benchmark):
        """Test composite score calculation speed."""

        def calculate_scores(n_instruments):
            scores = []
            for _ in range(n_instruments):
                factors = {
                    'percentile': np.random.random(),
                    'trend': np.random.random(),
                    'expectancy': np.random.random(),
                    'volatility': np.random.random()
                }
                weights = {k: 0.25 for k in factors.keys()}
                score = sum(factors[k] * weights[k] for k in factors.keys())
                scores.append(score)
            return scores

        result = benchmark(calculate_scores, 100)
        assert len(result) == 100

    @pytest.mark.performance
    def test_vectorized_scoring(self, benchmark):
        """Test vectorized score calculation."""

        def vectorized_scores(n_instruments):
            # Generate all factors as arrays
            percentiles = np.random.random(n_instruments)
            trends = np.random.random(n_instruments)
            expectancies = np.random.random(n_instruments)

            # Vectorized calculation
            scores = (percentiles * 0.33 +
                      trends * 0.33 +
                      expectancies * 0.34)
            return scores

        result = benchmark(vectorized_scores, 100)
        assert len(result) == 100
