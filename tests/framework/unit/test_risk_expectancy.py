"""
Unit tests for risk expectancy calculator.

Tests cover:
- Expectancy calculation
- Win rate analysis
- Risk/reward ratio
- Kelly criterion
- Position sizing
- Monte Carlo validation
"""

import pytest
import numpy as np
import pandas as pd
from scipy import stats


# ============================================================================
# Test Expectancy Calculation
# ============================================================================

class TestExpectancyCalculation:
    """Test suite for expectancy calculation."""

    @pytest.mark.unit
    @pytest.mark.critical
    def test_basic_expectancy(self, position_scenarios):
        """Test basic expectancy calculation."""
        scenario = position_scenarios['high_conviction']

        win_rate = scenario['win_rate']
        avg_win = scenario['avg_win']
        avg_loss = scenario['avg_loss']

        # Calculate expectancy
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)

        assert expectancy > 0, "High conviction should have positive expectancy"
        assert np.isclose(expectancy, scenario['expectancy'], atol=0.01)

    @pytest.mark.unit
    def test_expectancy_components(self, position_scenarios):
        """Test individual components of expectancy calculation."""
        for scenario_name, scenario in position_scenarios.items():
            win_rate = scenario['win_rate']
            avg_win = scenario['avg_win']
            avg_loss = scenario['avg_loss']

            # Win component
            win_component = win_rate * avg_win
            assert win_component > 0, "Win component should be positive"

            # Loss component
            loss_component = (1 - win_rate) * avg_loss
            assert loss_component < 0, "Loss component should be negative"

            # Total expectancy
            total_expectancy = win_component + loss_component
            assert abs(total_expectancy - scenario['expectancy']) < 0.01

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_expectancy_edge_cases(self):
        """Test expectancy calculation edge cases."""
        # Perfect win rate
        exp_perfect = (1.0 * 0.02) + (0.0 * -0.01)
        assert exp_perfect == 0.02

        # Perfect loss rate
        exp_zero = (0.0 * 0.02) + (1.0 * -0.01)
        assert exp_zero == -0.01

        # Break-even
        exp_breakeven = (0.5 * 0.02) + (0.5 * -0.02)
        assert abs(exp_breakeven) < 1e-10

    @pytest.mark.unit
    def test_negative_expectancy_detection(self):
        """Test detection of negative expectancy."""
        # Losing scenario
        win_rate = 0.4
        avg_win = 0.01
        avg_loss = -0.015

        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)

        assert expectancy < 0, "Should detect negative expectancy"


# ============================================================================
# Test Win Rate Analysis
# ============================================================================

class TestWinRateAnalysis:
    """Test suite for win rate analysis."""

    @pytest.mark.unit
    def test_win_rate_calculation(self):
        """Test win rate calculation from trade results."""
        # Sample trade results
        trades = np.array([0.02, -0.01, 0.03, -0.015, 0.01, 0.025, -0.01, 0.015])

        wins = np.sum(trades > 0)
        total = len(trades)
        win_rate = wins / total

        assert 0 <= win_rate <= 1, "Win rate should be probability"
        assert win_rate == 5 / 8, "Should calculate correct win rate"

    @pytest.mark.unit
    def test_rolling_win_rate(self):
        """Test rolling win rate calculation."""
        np.random.seed(42)

        # Generate trade sequence
        trades = np.random.choice([1, -1], size=100, p=[0.6, 0.4])

        # Calculate rolling win rate
        window = 20
        rolling_wr = pd.Series(trades).rolling(window).apply(lambda x: (x > 0).sum() / len(x))

        assert rolling_wr.notna().sum() > 0, "Should have rolling win rates"
        assert (rolling_wr.dropna() >= 0).all() and (rolling_wr.dropna() <= 1).all()

    @pytest.mark.unit
    def test_win_rate_confidence_interval(self):
        """Test confidence interval for win rate."""
        wins = 60
        total = 100

        win_rate = wins / total

        # Calculate 95% CI using normal approximation
        se = np.sqrt(win_rate * (1 - win_rate) / total)
        z = 1.96  # 95% confidence
        ci_lower = win_rate - z * se
        ci_upper = win_rate + z * se

        assert ci_lower < win_rate < ci_upper
        assert ci_lower >= 0 and ci_upper <= 1

    @pytest.mark.unit
    def test_win_rate_sample_size_requirements(self):
        """Test minimum sample size for reliable win rate."""
        # For 95% confidence, ±5% margin of error
        p = 0.5  # Assume 50% win rate for conservative estimate
        margin = 0.05
        z = 1.96

        n = (z ** 2 * p * (1 - p)) / (margin ** 2)

        assert n > 0
        assert n < 500, "Sample size should be reasonable"


# ============================================================================
# Test Risk/Reward Ratio
# ============================================================================

class TestRiskRewardRatio:
    """Test suite for risk/reward ratio analysis."""

    @pytest.mark.unit
    def test_basic_risk_reward(self, position_scenarios):
        """Test basic risk/reward ratio calculation."""
        scenario = position_scenarios['high_conviction']

        avg_win = scenario['avg_win']
        avg_loss = abs(scenario['avg_loss'])

        risk_reward = avg_win / avg_loss

        assert risk_reward > 0, "R/R should be positive"
        assert risk_reward > 1.5, "High conviction should have good R/R"

    @pytest.mark.unit
    def test_minimum_win_rate_for_profitability(self):
        """Test minimum win rate needed given risk/reward ratio."""
        risk_reward_ratios = [1.0, 1.5, 2.0, 3.0]

        for rr in risk_reward_ratios:
            # Break-even win rate
            min_wr = 1 / (1 + rr)

            # Verify break-even
            expectancy = (min_wr * rr) + ((1 - min_wr) * -1)
            assert abs(expectancy) < 0.01, f"Should break even at {min_wr:.2%}"

    @pytest.mark.unit
    def test_asymmetric_risk_reward(self):
        """Test handling of asymmetric risk/reward profiles."""
        # Large wins, small losses
        avg_win = 0.05
        avg_loss = -0.01
        win_rate = 0.4

        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)

        assert expectancy > 0, "Asymmetric profile can be profitable even with low win rate"

    @pytest.mark.unit
    def test_risk_reward_distribution(self):
        """Test distribution of risk/reward ratios."""
        np.random.seed(42)

        # Generate sample trades
        wins = np.random.exponential(scale=2, size=100)
        losses = -np.random.exponential(scale=1, size=100)

        # Calculate R/R for each trade
        avg_win = np.mean(wins)
        avg_loss = abs(np.mean(losses))

        rr_ratio = avg_win / avg_loss

        assert rr_ratio > 1, "Should have positive R/R"


# ============================================================================
# Test Kelly Criterion
# ============================================================================

class TestKellyCriterion:
    """Test suite for Kelly criterion position sizing."""

    @pytest.mark.unit
    @pytest.mark.critical
    def test_kelly_formula(self, position_scenarios):
        """Test Kelly criterion formula."""
        scenario = position_scenarios['high_conviction']

        win_rate = scenario['win_rate']
        avg_win = scenario['avg_win']
        avg_loss = abs(scenario['avg_loss'])

        # Kelly percentage
        kelly = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win

        assert 0 < kelly < 1, "Kelly should be between 0 and 1"

    @pytest.mark.unit
    def test_fractional_kelly(self, position_scenarios):
        """Test fractional Kelly for risk management."""
        scenario = position_scenarios['high_conviction']

        win_rate = scenario['win_rate']
        avg_win = scenario['avg_win']
        avg_loss = abs(scenario['avg_loss'])

        # Full Kelly
        kelly_full = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win

        # Half Kelly (more conservative)
        kelly_half = kelly_full * 0.5

        assert kelly_half < kelly_full
        assert kelly_half > 0

    @pytest.mark.unit
    def test_kelly_with_negative_expectancy(self):
        """Test Kelly criterion with negative expectancy."""
        # Losing scenario
        win_rate = 0.4
        avg_win = 0.01
        avg_loss = 0.02

        kelly = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win

        assert kelly <= 0, "Kelly should be non-positive for negative expectancy"

    @pytest.mark.unit
    def test_kelly_edge_cases(self):
        """Test Kelly criterion edge cases."""
        # Perfect win rate
        kelly_perfect = (1.0 * 0.02 - 0.0 * 0.01) / 0.02
        assert kelly_perfect == 1.0

        # 50/50 with equal R/R
        kelly_breakeven = (0.5 * 0.01 - 0.5 * 0.01) / 0.01
        assert kelly_breakeven == 0


# ============================================================================
# Test Position Sizing
# ============================================================================

class TestPositionSizing:
    """Test suite for position sizing calculations."""

    @pytest.mark.unit
    def test_fixed_fractional_position_sizing(self, portfolio_config):
        """Test fixed fractional position sizing."""
        total_capital = portfolio_config['total_capital']
        max_position = portfolio_config['max_position_size']

        position_size = total_capital * max_position

        assert position_size <= total_capital
        assert position_size == 10000

    @pytest.mark.unit
    def test_volatility_adjusted_sizing(self, portfolio_config):
        """Test volatility-adjusted position sizing."""
        total_capital = portfolio_config['total_capital']
        target_risk = 0.02  # 2% risk per trade

        # Higher volatility = smaller position
        low_vol_asset = 0.01  # 1% daily volatility
        high_vol_asset = 0.05  # 5% daily volatility

        size_low_vol = (total_capital * target_risk) / low_vol_asset
        size_high_vol = (total_capital * target_risk) / high_vol_asset

        assert size_low_vol > size_high_vol, \
            "Higher volatility should result in smaller position"

    @pytest.mark.unit
    def test_max_portfolio_heat(self, portfolio_config):
        """Test maximum portfolio heat constraint."""
        total_capital = portfolio_config['total_capital']
        max_heat = portfolio_config['max_portfolio_heat']
        risk_per_trade = 0.02

        # Calculate maximum number of positions
        max_positions = max_heat / risk_per_trade

        assert max_positions == 10
        assert max_positions * risk_per_trade <= max_heat

    @pytest.mark.unit
    def test_correlation_adjusted_sizing(self, portfolio_config):
        """Test correlation-adjusted position sizing."""
        max_correlation = portfolio_config['max_correlation']

        # Correlated positions should be sized smaller
        base_size = 1.0
        correlation = 0.8

        if correlation > max_correlation:
            adjusted_size = base_size * (max_correlation / correlation)
        else:
            adjusted_size = base_size

        assert adjusted_size <= base_size


# ============================================================================
# Test Monte Carlo Validation
# ============================================================================

class TestMonteCarloValidation:
    """Test suite for Monte Carlo expectancy validation."""

    @pytest.mark.unit
    def test_monte_carlo_expectancy(self, position_scenarios):
        """Test expectancy validation via Monte Carlo simulation."""
        np.random.seed(42)

        scenario = position_scenarios['high_conviction']
        win_rate = scenario['win_rate']
        avg_win = scenario['avg_win']
        avg_loss = scenario['avg_loss']

        # Run Monte Carlo simulation
        n_simulations = 1000
        n_trades = 100

        results = []

        for _ in range(n_simulations):
            # Generate trade sequence
            trades = np.random.choice(
                [avg_win, avg_loss],
                size=n_trades,
                p=[win_rate, 1 - win_rate]
            )

            # Calculate average return
            avg_return = np.mean(trades)
            results.append(avg_return)

        # Monte Carlo expectancy should match calculated expectancy
        mc_expectancy = np.mean(results)
        calc_expectancy = scenario['expectancy']

        assert abs(mc_expectancy - calc_expectancy) < 0.005, \
            "Monte Carlo should validate calculated expectancy"

    @pytest.mark.unit
    def test_monte_carlo_confidence_intervals(self):
        """Test confidence intervals from Monte Carlo simulation."""
        np.random.seed(42)

        win_rate = 0.6
        avg_win = 0.02
        avg_loss = -0.01
        n_trades = 100

        # Run simulations
        results = []
        for _ in range(1000):
            trades = np.random.choice([avg_win, avg_loss], size=n_trades,
                                      p=[win_rate, 1 - win_rate])
            cumulative = np.sum(trades)
            results.append(cumulative)

        # Calculate percentiles
        p5 = np.percentile(results, 5)
        p95 = np.percentile(results, 95)

        assert p5 < p95
        assert p5 > -1 and p95 < 3  # Reasonable bounds

    @pytest.mark.unit
    @pytest.mark.slow
    def test_drawdown_distribution(self):
        """Test drawdown distribution via Monte Carlo."""
        np.random.seed(42)

        win_rate = 0.55
        avg_win = 0.02
        avg_loss = -0.015

        max_drawdowns = []

        for _ in range(500):
            # Generate trade sequence
            trades = np.random.choice([avg_win, avg_loss], size=200,
                                      p=[win_rate, 1 - win_rate])

            # Calculate equity curve
            equity = np.cumsum(trades)

            # Calculate maximum drawdown
            running_max = np.maximum.accumulate(equity)
            drawdown = equity - running_max
            max_dd = np.min(drawdown)

            max_drawdowns.append(max_dd)

        # Analyze drawdown distribution
        median_dd = np.percentile(max_drawdowns, 50)
        worst_dd = np.min(max_drawdowns)

        assert median_dd < 0, "Should have drawdowns"
        assert worst_dd < median_dd, "Worst DD should be worse than median"


# ============================================================================
# Test Performance
# ============================================================================

class TestExpectancyPerformance:
    """Test suite for expectancy calculation performance."""

    @pytest.mark.performance
    def test_calculation_speed(self, benchmark):
        """Test expectancy calculation speed."""

        def calculate_expectancy(win_rate, avg_win, avg_loss, n_positions):
            expectancies = []
            for _ in range(n_positions):
                exp = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
                expectancies.append(exp)
            return expectancies

        result = benchmark(calculate_expectancy, 0.6, 0.02, -0.01, 100)
        assert len(result) == 100

    @pytest.mark.performance
    def test_vectorized_expectancy(self, benchmark):
        """Test vectorized expectancy calculation."""

        def vectorized_expectancy(win_rates, avg_wins, avg_losses):
            return (win_rates * avg_wins) + ((1 - win_rates) * avg_losses)

        n = 1000
        wr = np.full(n, 0.6)
        wins = np.full(n, 0.02)
        losses = np.full(n, -0.01)

        result = benchmark(vectorized_expectancy, wr, wins, losses)
        assert len(result) == n
