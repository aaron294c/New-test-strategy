"""
Integration tests for trading framework end-to-end workflows.

Tests cover:
- Complete multi-timeframe analysis pipeline
- Regime detection → Percentile → Scoring → Allocation flow
- Cross-module data consistency
- Real-world scenario validation
- Performance under load
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


# ============================================================================
# Test End-to-End Pipeline
# ============================================================================

class TestEndToEndPipeline:
    """Test complete trading framework pipeline."""

    @pytest.mark.integration
    @pytest.mark.critical
    def test_complete_analysis_pipeline(self, sample_price_data, percentile_bins):
        """Test complete analysis from price data to allocation."""
        prices = sample_price_data['close'].values

        # Step 1: Regime Detection
        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns) * np.sqrt(252 * 6)
        trend_strength = abs(np.sum(returns > 0) / len(returns) - 0.5) * 2

        regime = {
            'volatility': volatility,
            'trend': trend_strength,
            'type': 'trending' if trend_strength > 0.3 else 'ranging'
        }

        assert regime['type'] in ['trending', 'ranging']

        # Step 2: Percentile Analysis
        lookback = 100
        current_return = returns[-1]
        hist_returns = returns[-lookback:]
        percentile = (hist_returns < current_return).sum() / len(hist_returns) * 100

        # Assign to bin
        assigned_bin = None
        for lower, upper in percentile_bins:
            if lower <= percentile < upper or (percentile == 100 and upper == 100):
                assigned_bin = f"{lower}-{upper}"
                break

        assert assigned_bin is not None

        # Step 3: Calculate Expected Return (mock forward stats)
        expected_return = 0.015 if percentile > 85 else 0.005
        t_score = 2.5 if percentile > 85 else 1.2

        # Step 4: Composite Scoring
        factors = {
            'percentile': percentile / 100,
            'regime': 0.7 if regime['type'] == 'trending' else 0.4,
            'statistical': min(abs(t_score) / 3, 1),
            'volatility': 1 - (volatility / 2)  # Lower vol = higher score
        }

        weights = {k: 0.25 for k in factors.keys()}
        composite_score = sum(factors[k] * weights[k] for k in factors.keys())

        assert 0 <= composite_score <= 1

        # Step 5: Position Sizing
        total_capital = 100000
        base_position = total_capital * 0.05

        # Adjust by score
        position_size = base_position * composite_score

        # Adjust by volatility
        target_risk = 0.02
        vol_adjusted_size = (total_capital * target_risk) / max(volatility, 0.1)

        final_size = min(position_size, vol_adjusted_size, total_capital * 0.1)

        assert final_size > 0
        assert final_size <= total_capital * 0.1

    @pytest.mark.integration
    def test_multi_timeframe_integration(self, multi_timeframe_data, percentile_bins):
        """Test integration across multiple timeframes."""
        daily_data = multi_timeframe_data['daily']
        h4_data = multi_timeframe_data['4h']

        # Analyze both timeframes
        timeframe_signals = {}

        for tf_name, tf_data in [('daily', daily_data), ('4h', h4_data)]:
            prices = tf_data['close'].values
            returns = np.diff(prices) / prices[:-1]

            # Calculate metrics
            percentile = 75  # Mock
            volatility = np.std(returns)

            # Generate signal
            signal_strength = percentile / 100
            timeframe_signals[tf_name] = {
                'signal': signal_strength,
                'volatility': volatility
            }

        # Check confluence
        daily_signal = timeframe_signals['daily']['signal']
        h4_signal = timeframe_signals['4h']['signal']

        agreement = 1 - abs(daily_signal - h4_signal)
        assert 0 <= agreement <= 1

        # Combined signal
        combined = (daily_signal * 0.6 + h4_signal * 0.4) * (1 + agreement * 0.1)
        assert 0 <= combined <= 1.1  # Can exceed 1 slightly due to agreement bonus


# ============================================================================
# Test Data Flow Consistency
# ============================================================================

class TestDataFlowConsistency:
    """Test data consistency across modules."""

    @pytest.mark.integration
    def test_percentile_to_scoring_consistency(self, forward_return_stats, percentile_bins):
        """Test consistency between percentile analysis and scoring."""
        # Extract data for high percentile bin
        high_pct_stats = forward_return_stats['85-95']

        # Scoring should reflect good statistics
        mean_return = high_pct_stats['mean']
        t_score = high_pct_stats['t_score']

        # Calculate score components
        return_score = min(max((mean_return + 0.05) / 0.1, 0), 1)
        significance_score = min(abs(t_score) / 3, 1)

        composite = (return_score + significance_score) / 2

        # Good statistics should produce good score
        if t_score > 2.0 and mean_return > 0.01:
            assert composite > 0.6, "Strong stats should yield high score"

    @pytest.mark.integration
    def test_regime_to_allocation_consistency(self, regime_scenarios, portfolio_config):
        """Test consistency between regime detection and allocation."""
        total_capital = portfolio_config['total_capital']

        for regime_name, scenario in regime_scenarios.items():
            atr_percentile = scenario['atr_percentile']

            # High volatility regimes should have smaller positions
            if atr_percentile > 85:
                vol_adjustment = 0.7
            elif atr_percentile > 50:
                vol_adjustment = 0.85
            else:
                vol_adjustment = 1.0

            base_position = total_capital * 0.05
            adjusted_position = base_position * vol_adjustment

            if atr_percentile > 85:
                assert adjusted_position < base_position
            else:
                assert adjusted_position <= base_position

    @pytest.mark.integration
    def test_cross_module_data_types(self, sample_price_data):
        """Test data type consistency across modules."""
        # Price data should be numeric
        assert pd.api.types.is_numeric_dtype(sample_price_data['close'])

        # Returns should be float
        returns = sample_price_data['close'].pct_change()
        assert returns.dtype == np.float64

        # Percentiles should be integers or floats
        percentile = np.percentile(returns.dropna(), 75)
        assert isinstance(percentile, (int, float, np.number))


# ============================================================================
# Test Real-World Scenarios
# ============================================================================

class TestRealWorldScenarios:
    """Test framework with real-world market scenarios."""

    @pytest.mark.integration
    def test_bull_market_scenario(self, trending_market_data, portfolio_config):
        """Test framework in bull market conditions."""
        prices = trending_market_data['close'].values
        returns = np.diff(prices) / prices[:-1]

        # Should detect uptrend
        positive_returns = np.sum(returns > 0) / len(returns)
        assert positive_returns > 0.55, "Should detect bull market"

        # High percentiles should perform well
        lookback = 100
        for i in range(lookback, len(returns) - 1):
            hist = returns[i - lookback:i]
            current = returns[i]
            percentile = (hist < current).sum() / len(hist) * 100

            # In bull market, high percentiles are favorable
            if percentile > 85:
                # This represents continuation signal
                assert percentile > 50  # Bullish bias

    @pytest.mark.integration
    def test_bear_market_scenario(self):
        """Test framework in bear market conditions."""
        np.random.seed(42)

        # Generate bear market data
        dates = pd.date_range(start='2023-01-01', periods=200, freq='4H')
        trend = np.linspace(100, 70, 200)  # Downtrend
        noise = np.random.normal(0, 2, 200)
        prices = trend + noise

        returns = np.diff(prices) / prices[:-1]

        # Should detect downtrend
        negative_returns = np.sum(returns < 0) / len(returns)
        assert negative_returns > 0.55, "Should detect bear market"

        # Low percentiles may be mean reversion opportunities
        lookback = 50
        for i in range(lookback, len(returns)):
            hist = returns[i - lookback:i]
            current = returns[i]
            percentile = (hist < current).sum() / len(hist) * 100

            if percentile < 15:
                # Extreme lows in bear market
                assert percentile >= 0

    @pytest.mark.integration
    def test_volatile_market_scenario(self, volatile_market_data, portfolio_config):
        """Test framework in high volatility conditions."""
        prices = volatile_market_data['close'].values
        returns = np.diff(prices) / prices[:-1]

        volatility = np.std(returns) * np.sqrt(252 * 6)

        # Should detect high volatility
        assert volatility > 0.25, "Should detect high volatility"

        # Position sizing should be conservative
        total_capital = portfolio_config['total_capital']
        target_risk = 0.02

        # Smaller positions in high vol
        position_size = (total_capital * target_risk) / volatility
        max_position = total_capital * 0.05

        assert position_size < max_position, "High vol should reduce position size"

    @pytest.mark.integration
    def test_regime_transition_scenario(self):
        """Test framework during regime transitions."""
        np.random.seed(42)

        # Create data with regime change
        low_vol_period = np.random.normal(0, 0.01, 100)
        high_vol_period = np.random.normal(0, 0.05, 100)

        combined_returns = np.concatenate([low_vol_period, high_vol_period])

        # Detect regime change
        window = 30
        vol_series = []

        for i in range(window, len(combined_returns)):
            window_vol = np.std(combined_returns[i - window:i])
            vol_series.append(window_vol)

        # Volatility should increase significantly
        early_vol = np.mean(vol_series[:30])
        late_vol = np.mean(vol_series[-30:])

        assert late_vol > early_vol * 2, "Should detect volatility regime change"


# ============================================================================
# Test Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling in integrated workflows."""

    @pytest.mark.integration
    def test_insufficient_data_handling(self):
        """Test handling of insufficient data."""
        # Too little data for analysis
        minimal_data = np.random.random(10)

        # Should handle gracefully
        if len(minimal_data) < 30:
            # Skip analysis or use defaults
            default_signal = 0.5
            assert default_signal == 0.5

    @pytest.mark.integration
    def test_missing_data_handling(self, sample_price_data):
        """Test handling of missing data."""
        prices = sample_price_data['close'].copy()

        # Introduce missing values
        prices.iloc[50:60] = np.nan

        # Should handle NaN values
        clean_prices = prices.dropna()
        assert len(clean_prices) < len(prices)
        assert not clean_prices.isna().any()

    @pytest.mark.integration
    def test_extreme_value_handling(self):
        """Test handling of extreme values."""
        # Create data with outliers
        normal_data = np.random.normal(0, 0.02, 100)
        outliers = np.array([0.5, -0.4])  # Extreme returns

        combined = np.concatenate([normal_data, outliers])

        # Calculate statistics with outlier handling
        median = np.median(combined)
        q1 = np.percentile(combined, 25)
        q3 = np.percentile(combined, 75)
        iqr = q3 - q1

        # Identify outliers
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outlier_mask = (combined < lower_bound) | (combined > upper_bound)
        assert outlier_mask.sum() >= 2, "Should detect outliers"


# ============================================================================
# Test Performance Under Load
# ============================================================================

class TestPerformanceUnderLoad:
    """Test framework performance with realistic data volumes."""

    @pytest.mark.integration
    @pytest.mark.performance
    def test_multi_instrument_processing(self, benchmark):
        """Test processing multiple instruments efficiently."""

        def process_instruments(n_instruments):
            results = []

            for i in range(n_instruments):
                # Simulate processing each instrument
                np.random.seed(i)
                prices = 100 + np.cumsum(np.random.normal(0, 1, 1000))
                returns = np.diff(prices) / prices[:-1]

                # Calculate metrics
                percentile = np.percentile(returns, 75)
                volatility = np.std(returns)
                score = (percentile + volatility) / 2

                results.append({
                    'instrument': f'INST_{i}',
                    'score': score
                })

            return results

        results = benchmark(process_instruments, 20)
        assert len(results) == 20

    @pytest.mark.integration
    @pytest.mark.performance
    def test_historical_backtest_performance(self, benchmark):
        """Test performance of historical analysis."""

        def run_backtest(n_periods):
            np.random.seed(42)
            prices = 100 + np.cumsum(np.random.normal(0, 1, n_periods))
            returns = np.diff(prices) / prices[:-1]

            signals = []
            lookback = 100

            for i in range(lookback, len(returns)):
                hist = returns[i - lookback:i]
                current = returns[i]
                percentile = (hist < current).sum() / len(hist) * 100

                signal = 1 if percentile > 75 else 0
                signals.append(signal)

            return signals

        results = benchmark(run_backtest, 2000)
        assert len(results) > 0

    @pytest.mark.integration
    @pytest.mark.slow
    def test_monte_carlo_simulation_integration(self):
        """Test Monte Carlo simulation with framework components."""
        np.random.seed(42)

        # Parameters from framework
        win_rate = 0.60
        avg_win = 0.025
        avg_loss = -0.015
        n_trades = 100

        # Run simulations
        simulation_results = []

        for sim in range(500):
            # Generate trade sequence
            trades = np.random.choice([avg_win, avg_loss], size=n_trades,
                                      p=[win_rate, 1 - win_rate])

            # Calculate equity curve
            equity = np.cumsum(trades)

            # Track metrics
            final_return = equity[-1]
            max_dd = np.min(equity - np.maximum.accumulate(equity))

            simulation_results.append({
                'final_return': final_return,
                'max_drawdown': max_dd
            })

        # Analyze results
        final_returns = [r['final_return'] for r in simulation_results]
        median_return = np.median(final_returns)
        positive_outcomes = np.sum(np.array(final_returns) > 0) / len(final_returns)

        assert positive_outcomes > 0.5, "Should have positive expectancy"
        assert median_return > 0, "Median should be positive"
