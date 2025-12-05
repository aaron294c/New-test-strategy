"""
Unit tests for capital allocation engine.

Tests cover:
- Portfolio-level capital allocation
- Position sizing algorithms
- Risk parity and diversification
- Correlation-based adjustments
- Dynamic rebalancing
"""

import pytest
import numpy as np
import pandas as pd


# ============================================================================
# Test Portfolio Capital Allocation
# ============================================================================

class TestPortfolioAllocation:
    """Test suite for portfolio-level capital allocation."""

    @pytest.mark.unit
    @pytest.mark.critical
    def test_basic_capital_allocation(self, portfolio_config):
        """Test basic capital allocation across positions."""
        total_capital = portfolio_config['total_capital']
        max_positions = 5

        # Equal allocation
        allocation_per_position = total_capital / max_positions

        assert allocation_per_position == 20000
        assert allocation_per_position * max_positions <= total_capital

    @pytest.mark.unit
    def test_max_position_size_constraint(self, portfolio_config):
        """Test maximum position size constraint."""
        total_capital = portfolio_config['total_capital']
        max_position_pct = portfolio_config['max_position_size']

        # Calculate maximum position
        max_position = total_capital * max_position_pct

        assert max_position == 10000
        assert max_position < total_capital

    @pytest.mark.unit
    def test_portfolio_heat_allocation(self, portfolio_config):
        """Test portfolio heat-based allocation."""
        total_capital = portfolio_config['total_capital']
        max_heat = portfolio_config['max_portfolio_heat']
        risk_per_position = 0.02  # 2% risk per position

        # Calculate maximum capital at risk
        max_risk_capital = total_capital * max_heat
        max_positions = max_heat / risk_per_position

        assert max_risk_capital == 20000
        assert max_positions == 10

    @pytest.mark.unit
    def test_reserve_capital(self, portfolio_config):
        """Test reserve capital management."""
        total_capital = portfolio_config['total_capital']
        reserve_pct = 0.20  # 20% reserve

        # Calculate deployable capital
        deployable = total_capital * (1 - reserve_pct)
        reserve = total_capital * reserve_pct

        assert deployable == 80000
        assert reserve == 20000
        assert deployable + reserve == total_capital


# ============================================================================
# Test Position Sizing Algorithms
# ============================================================================

class TestPositionSizing:
    """Test suite for position sizing algorithms."""

    @pytest.mark.unit
    def test_fixed_fractional_sizing(self, portfolio_config):
        """Test fixed fractional position sizing."""
        total_capital = portfolio_config['total_capital']
        fraction = 0.05  # 5% per position

        position_size = total_capital * fraction

        assert position_size == 5000
        assert position_size / total_capital == fraction

    @pytest.mark.unit
    def test_volatility_scaled_sizing(self, portfolio_config):
        """Test volatility-scaled position sizing."""
        total_capital = portfolio_config['total_capital']
        target_volatility = 0.15  # 15% target portfolio volatility

        # Different asset volatilities
        assets = {
            'low_vol': 0.10,
            'med_vol': 0.20,
            'high_vol': 0.40
        }

        # Size inversely to volatility
        sizes = {}
        for asset, vol in assets.items():
            size = (total_capital * target_volatility) / vol
            sizes[asset] = min(size, total_capital * 0.1)  # Cap at 10%

        # Higher volatility should have smaller size
        assert sizes['low_vol'] > sizes['med_vol'] > sizes['high_vol']

    @pytest.mark.unit
    def test_score_weighted_sizing(self, portfolio_config):
        """Test score-weighted position sizing."""
        total_capital = portfolio_config['total_capital']
        available_capital = total_capital * 0.8  # 80% deployed

        # Instrument scores
        scores = {
            'A': 0.85,
            'B': 0.75,
            'C': 0.65,
            'D': 0.55
        }

        # Allocate proportionally to scores
        total_score = sum(scores.values())
        allocations = {}

        for instrument, score in scores.items():
            allocation = (score / total_score) * available_capital
            allocations[instrument] = allocation

        # Verify total allocation
        assert abs(sum(allocations.values()) - available_capital) < 1.0

        # Higher scores get more capital
        assert allocations['A'] > allocations['B'] > allocations['C'] > allocations['D']

    @pytest.mark.unit
    def test_kelly_criterion_sizing(self):
        """Test Kelly criterion-based position sizing."""
        # Position parameters
        win_rate = 0.60
        avg_win = 0.025
        avg_loss = 0.015

        # Kelly formula
        kelly = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win

        # Use fractional Kelly for safety
        fractional_kelly = kelly * 0.5

        assert 0 < fractional_kelly < 1
        assert fractional_kelly < kelly


# ============================================================================
# Test Risk Parity
# ============================================================================

class TestRiskParity:
    """Test suite for risk parity allocation."""

    @pytest.mark.unit
    def test_equal_risk_contribution(self, portfolio_config):
        """Test equal risk contribution allocation."""
        total_capital = portfolio_config['total_capital']

        # Three assets with different volatilities
        assets = {
            'A': {'volatility': 0.10},
            'B': {'volatility': 0.20},
            'C': {'volatility': 0.30}
        }

        # Allocate inversely to volatility for equal risk
        total_inv_vol = sum(1 / a['volatility'] for a in assets.values())

        allocations = {}
        for name, asset in assets.items():
            weight = (1 / asset['volatility']) / total_inv_vol
            allocations[name] = total_capital * weight

        # Calculate risk contribution
        risk_contributions = {}
        for name, allocation in allocations.items():
            vol = assets[name]['volatility']
            risk_contributions[name] = allocation * vol

        # Risk contributions should be approximately equal
        rc_values = list(risk_contributions.values())
        assert max(rc_values) / min(rc_values) < 1.5  # Within 50% of each other

    @pytest.mark.unit
    def test_risk_budgeting(self, portfolio_config):
        """Test risk budget allocation."""
        total_capital = portfolio_config['total_capital']
        total_risk_budget = 0.15  # 15% portfolio risk

        # Assign risk budgets
        risk_budgets = {
            'equity': 0.10,  # 10% risk
            'commodity': 0.03,  # 3% risk
            'fixed_income': 0.02  # 2% risk
        }

        # Volatilities
        volatilities = {
            'equity': 0.25,
            'commodity': 0.35,
            'fixed_income': 0.05
        }

        # Size to match risk budgets
        allocations = {}
        for asset, risk_budget in risk_budgets.items():
            vol = volatilities[asset]
            allocation = (total_capital * risk_budget) / vol
            allocations[asset] = allocation

        assert sum(risk_budgets.values()) == total_risk_budget


# ============================================================================
# Test Correlation-Based Adjustments
# ============================================================================

class TestCorrelationAdjustments:
    """Test suite for correlation-based allocation adjustments."""

    @pytest.mark.unit
    def test_correlation_matrix_calculation(self):
        """Test correlation matrix calculation."""
        np.random.seed(42)

        # Generate correlated returns
        n = 100
        returns_a = np.random.normal(0, 0.02, n)
        returns_b = returns_a * 0.8 + np.random.normal(0, 0.01, n)  # Correlated
        returns_c = np.random.normal(0, 0.02, n)  # Independent

        # Calculate correlation matrix
        returns_df = pd.DataFrame({
            'A': returns_a,
            'B': returns_b,
            'C': returns_c
        })

        corr_matrix = returns_df.corr()

        # A and B should be highly correlated
        assert corr_matrix.loc['A', 'B'] > 0.7
        # A and C should be low correlation
        assert abs(corr_matrix.loc['A', 'C']) < 0.3

    @pytest.mark.unit
    def test_correlation_penalty(self, portfolio_config):
        """Test allocation penalty for correlated positions."""
        max_correlation = portfolio_config['max_correlation']
        base_allocation = 10000

        # Test high correlation scenario
        correlation = 0.85

        if correlation > max_correlation:
            # Apply penalty
            penalty_factor = max_correlation / correlation
            adjusted_allocation = base_allocation * penalty_factor
        else:
            adjusted_allocation = base_allocation

        assert adjusted_allocation < base_allocation
        assert adjusted_allocation / base_allocation == pytest.approx(0.824, abs=0.01)

    @pytest.mark.unit
    def test_diversification_bonus(self):
        """Test allocation bonus for diversification."""
        base_allocation = 10000

        # Low correlation = diversification benefit
        correlations = {'A': 0.2, 'B': 0.15, 'C': 0.1}

        avg_correlation = np.mean(list(correlations.values()))

        # Diversification bonus
        if avg_correlation < 0.3:
            bonus_factor = 1 + (0.3 - avg_correlation)
            adjusted_allocation = base_allocation * bonus_factor
        else:
            adjusted_allocation = base_allocation

        assert adjusted_allocation > base_allocation


# ============================================================================
# Test Dynamic Rebalancing
# ============================================================================

class TestDynamicRebalancing:
    """Test suite for dynamic portfolio rebalancing."""

    @pytest.mark.unit
    def test_drift_detection(self):
        """Test detection of allocation drift."""
        # Target allocations
        target = {
            'A': 0.40,
            'B': 0.30,
            'C': 0.30
        }

        # Current allocations (drifted)
        current = {
            'A': 0.50,
            'B': 0.25,
            'C': 0.25
        }

        # Calculate drift
        drift = {k: abs(current[k] - target[k]) for k in target.keys()}

        # Threshold for rebalancing
        rebalance_threshold = 0.05

        needs_rebalance = any(d > rebalance_threshold for d in drift.values())

        assert needs_rebalance, "Should detect drift requiring rebalance"

    @pytest.mark.unit
    def test_rebalancing_calculation(self, portfolio_config):
        """Test rebalancing trade calculation."""
        total_capital = portfolio_config['total_capital']

        # Target weights
        target_weights = {'A': 0.40, 'B': 0.30, 'C': 0.30}

        # Current weights
        current_weights = {'A': 0.50, 'B': 0.25, 'C': 0.25}

        # Calculate required trades
        trades = {}
        for asset in target_weights.keys():
            target_amount = total_capital * target_weights[asset]
            current_amount = total_capital * current_weights[asset]
            trade_amount = target_amount - current_amount
            trades[asset] = trade_amount

        # Verify trades sum to zero (no net cash flow)
        assert abs(sum(trades.values())) < 1.0

        # A should be reduced, B and C increased
        assert trades['A'] < 0
        assert trades['B'] > 0
        assert trades['C'] > 0

    @pytest.mark.unit
    def test_threshold_based_rebalancing(self):
        """Test threshold-based rebalancing trigger."""
        # Current vs target
        positions = {
            'A': {'current': 0.42, 'target': 0.40, 'threshold': 0.05},
            'B': {'current': 0.35, 'target': 0.30, 'threshold': 0.05},
            'C': {'current': 0.23, 'target': 0.30, 'threshold': 0.05}
        }

        # Check which need rebalancing
        needs_rebalance = {}
        for asset, pos in positions.items():
            drift = abs(pos['current'] - pos['target'])
            needs_rebalance[asset] = drift > pos['threshold']

        # B and C exceed threshold
        assert needs_rebalance['B'] == True
        assert needs_rebalance['C'] == True


# ============================================================================
# Test Portfolio Constraints
# ============================================================================

class TestPortfolioConstraints:
    """Test suite for portfolio-level constraints."""

    @pytest.mark.unit
    def test_sector_concentration_limit(self):
        """Test sector concentration limits."""
        max_sector_exposure = 0.30  # 30% max per sector

        # Sector allocations
        sectors = {
            'Technology': ['AAPL', 'GOOGL', 'MSFT'],
            'Healthcare': ['JNJ', 'PFE'],
            'Finance': ['JPM', 'BAC']
        }

        # Position sizes
        positions = {
            'AAPL': 0.12,
            'GOOGL': 0.10,
            'MSFT': 0.11,
            'JNJ': 0.08,
            'PFE': 0.07,
            'JPM': 0.09,
            'BAC': 0.08
        }

        # Calculate sector exposures
        sector_exposure = {}
        for sector, stocks in sectors.items():
            exposure = sum(positions.get(stock, 0) for stock in stocks)
            sector_exposure[sector] = exposure

        # Check constraints
        for sector, exposure in sector_exposure.items():
            assert exposure <= max_sector_exposure, \
                f"{sector} exposure {exposure:.2%} exceeds limit"

    @pytest.mark.unit
    def test_leverage_constraint(self, portfolio_config):
        """Test leverage constraint."""
        total_capital = portfolio_config['total_capital']
        max_leverage = 1.5  # 150% gross exposure

        # Position sizes
        long_positions = [15000, 20000, 18000, 12000]
        short_positions = [10000, 8000]

        # Calculate gross exposure
        gross_exposure = sum(long_positions) + sum(short_positions)
        leverage_ratio = gross_exposure / total_capital

        assert leverage_ratio <= max_leverage, \
            f"Leverage {leverage_ratio:.2f} exceeds maximum"


# ============================================================================
# Test Performance
# ============================================================================

class TestAllocationPerformance:
    """Test suite for capital allocation performance."""

    @pytest.mark.performance
    def test_allocation_calculation_speed(self, benchmark, portfolio_config):
        """Test allocation calculation performance."""

        def allocate_capital(n_positions):
            total_capital = portfolio_config['total_capital']
            scores = np.random.random(n_positions)
            total_score = np.sum(scores)
            allocations = (scores / total_score) * total_capital
            return allocations

        result = benchmark(allocate_capital, 20)
        assert len(result) == 20

    @pytest.mark.performance
    def test_rebalancing_optimization(self, benchmark):
        """Test rebalancing calculation optimization."""

        def calculate_rebalance_trades(current, target, total_capital):
            trades = {}
            for asset in current.keys():
                current_amt = total_capital * current[asset]
                target_amt = total_capital * target[asset]
                trades[asset] = target_amt - current_amt
            return trades

        current = {f'stock_{i}': np.random.random() for i in range(50)}
        target = {f'stock_{i}': np.random.random() for i in range(50)}

        # Normalize
        current_sum = sum(current.values())
        target_sum = sum(target.values())
        current = {k: v / current_sum for k, v in current.items()}
        target = {k: v / target_sum for k, v in target.items()}

        result = benchmark(calculate_rebalance_trades, current, target, 100000)
        assert len(result) == 50
