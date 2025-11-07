"""
Statistical Validation Framework for Trading System Testing.

This module provides comprehensive statistical validation tools including:
- Distribution analysis and normality testing
- Statistical significance testing
- Backtesting validation
- Out-of-sample testing
- Walk-forward analysis
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Optional
import warnings


class StatisticalValidator:
    """
    Comprehensive statistical validation for trading framework.

    Provides methods for validating statistical assumptions, testing
    significance, and ensuring robustness of trading strategies.
    """

    def __init__(self, confidence_level: float = 0.95):
        """
        Initialize statistical validator.

        Args:
            confidence_level: Confidence level for statistical tests (default: 0.95)
        """
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level

    def test_normality(self, data: np.ndarray) -> Dict:
        """
        Test if data follows normal distribution.

        Args:
            data: Array of returns or other metric

        Returns:
            Dictionary with test results
        """
        # Shapiro-Wilk test
        statistic, p_value = stats.shapiro(data)

        # Jarque-Bera test
        jb_statistic, jb_p_value = stats.jarque_bera(data)

        # Calculate moments
        skewness = stats.skew(data)
        kurtosis = stats.kurtosis(data)

        return {
            'shapiro_statistic': statistic,
            'shapiro_p_value': p_value,
            'is_normal_shapiro': p_value > self.alpha,
            'jarque_bera_statistic': jb_statistic,
            'jarque_bera_p_value': jb_p_value,
            'is_normal_jb': jb_p_value > self.alpha,
            'skewness': skewness,
            'excess_kurtosis': kurtosis,
            'recommendation': self._normality_recommendation(p_value, jb_p_value)
        }

    def _normality_recommendation(self, shapiro_p: float, jb_p: float) -> str:
        """Generate recommendation based on normality tests."""
        if shapiro_p < self.alpha and jb_p < self.alpha:
            return "Data is non-normal. Consider non-parametric methods or transformations."
        elif shapiro_p < self.alpha or jb_p < self.alpha:
            return "Mixed results. Interpret parametric tests with caution."
        else:
            return "Data appears normally distributed. Parametric methods appropriate."

    def test_stationarity(self, data: np.ndarray) -> Dict:
        """
        Test if time series is stationary using ADF test.

        Args:
            data: Time series data

        Returns:
            Dictionary with stationarity test results
        """
        from scipy.stats import linregress

        # Augmented Dickey-Fuller test (simplified version)
        # Calculate first differences
        diff = np.diff(data)

        # Run regression
        y = diff[1:]
        x = data[1:-1]

        if len(y) > 0 and len(x) > 0:
            slope, intercept, r_value, p_value, std_err = linregress(x, y)

            # Calculate test statistic
            t_stat = slope / std_err if std_err > 0 else 0

            return {
                'test_statistic': t_stat,
                'p_value': p_value,
                'is_stationary': abs(t_stat) > 2.0,  # Simplified critical value
                'recommendation': self._stationarity_recommendation(abs(t_stat))
            }
        else:
            return {
                'test_statistic': np.nan,
                'p_value': np.nan,
                'is_stationary': False,
                'recommendation': "Insufficient data for stationarity test."
            }

    def _stationarity_recommendation(self, t_stat: float) -> str:
        """Generate recommendation based on stationarity test."""
        if t_stat > 3.5:
            return "Series is strongly stationary. Safe for time series analysis."
        elif t_stat > 2.0:
            return "Series appears stationary. Proceed with caution."
        else:
            return "Series is non-stationary. Consider differencing or detrending."

    def test_autocorrelation(self, data: np.ndarray, max_lag: int = 20) -> Dict:
        """
        Test for autocorrelation in data.

        Args:
            data: Time series data
            max_lag: Maximum lag to test

        Returns:
            Dictionary with autocorrelation results
        """
        n = len(data)
        mean = np.mean(data)
        variance = np.var(data)

        autocorr = []
        for lag in range(1, min(max_lag + 1, n // 2)):
            c0 = np.sum((data[:-lag] - mean) * (data[lag:] - mean))
            autocorr.append(c0 / (variance * (n - lag)))

        autocorr = np.array(autocorr)

        # Ljung-Box test statistic
        lb_statistic = n * (n + 2) * np.sum(autocorr ** 2 / (n - np.arange(1, len(autocorr) + 1)))

        # Critical value from chi-square distribution
        critical_value = stats.chi2.ppf(self.confidence_level, len(autocorr))

        return {
            'autocorrelations': autocorr,
            'ljung_box_statistic': lb_statistic,
            'critical_value': critical_value,
            'has_autocorrelation': lb_statistic > critical_value,
            'max_abs_autocorr': np.max(np.abs(autocorr)),
            'recommendation': self._autocorr_recommendation(lb_statistic, critical_value)
        }

    def _autocorr_recommendation(self, lb_stat: float, critical: float) -> str:
        """Generate recommendation based on autocorrelation test."""
        if lb_stat > critical * 2:
            return "Strong autocorrelation detected. Model as time series or adjust for clustering."
        elif lb_stat > critical:
            return "Moderate autocorrelation present. Consider adjusting standard errors."
        else:
            return "No significant autocorrelation. Data appears independent."

    def test_heteroskedasticity(self, returns: np.ndarray, prices: np.ndarray) -> Dict:
        """
        Test for heteroskedasticity (non-constant variance).

        Args:
            returns: Return series
            prices: Price series

        Returns:
            Dictionary with heteroskedasticity test results
        """
        # Calculate rolling volatility
        window = min(20, len(returns) // 4)
        rolling_vol = pd.Series(returns).rolling(window).std().dropna()

        # Test if variance is constant
        # Split into two halves
        mid = len(rolling_vol) // 2
        first_half_var = np.var(rolling_vol[:mid])
        second_half_var = np.var(rolling_vol[mid:])

        # F-test
        if second_half_var > 0 and first_half_var > 0:
            f_statistic = max(first_half_var, second_half_var) / min(first_half_var, second_half_var)
            p_value = 1 - stats.f.cdf(f_statistic, mid - 1, len(rolling_vol) - mid - 1)
        else:
            f_statistic = np.nan
            p_value = np.nan

        return {
            'f_statistic': f_statistic,
            'p_value': p_value,
            'has_heteroskedasticity': p_value < self.alpha if not np.isnan(p_value) else False,
            'vol_ratio': max(first_half_var, second_half_var) / min(first_half_var, second_half_var)
                if first_half_var > 0 and second_half_var > 0 else np.nan,
            'recommendation': self._heteroskedasticity_recommendation(p_value)
        }

    def _heteroskedasticity_recommendation(self, p_value: float) -> str:
        """Generate recommendation based on heteroskedasticity test."""
        if np.isnan(p_value):
            return "Insufficient data for heteroskedasticity test."
        elif p_value < 0.01:
            return "Strong heteroskedasticity. Use robust standard errors or GARCH models."
        elif p_value < self.alpha:
            return "Moderate heteroskedasticity present. Consider volatility adjustments."
        else:
            return "Variance appears constant. Standard methods appropriate."

    def validate_forward_returns(self, percentile_bins: List[Tuple[int, int]],
                                  forward_returns: Dict[str, List[float]]) -> Dict:
        """
        Validate forward return statistics for each percentile bin.

        Args:
            percentile_bins: List of (lower, upper) percentile tuples
            forward_returns: Dictionary mapping bin names to lists of forward returns

        Returns:
            Validation results for each bin
        """
        validation_results = {}

        for lower, upper in percentile_bins:
            bin_name = f"{lower}-{upper}"

            if bin_name not in forward_returns or len(forward_returns[bin_name]) < 2:
                validation_results[bin_name] = {
                    'valid': False,
                    'reason': 'Insufficient data'
                }
                continue

            returns = np.array(forward_returns[bin_name])

            # Calculate statistics
            mean = np.mean(returns)
            std = np.std(returns, ddof=1)
            n = len(returns)

            # T-test
            if std > 0:
                t_stat = (mean / (std / np.sqrt(n)))
                p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 1))
            else:
                t_stat = np.nan
                p_value = np.nan

            # Check for sufficient samples
            min_samples = 30
            sufficient_samples = n >= min_samples

            # Check for statistical significance
            statistically_significant = p_value < self.alpha if not np.isnan(p_value) else False

            validation_results[bin_name] = {
                'valid': sufficient_samples and not np.isnan(t_stat),
                'n_samples': n,
                'mean': mean,
                'std': std,
                't_statistic': t_stat,
                'p_value': p_value,
                'sufficient_samples': sufficient_samples,
                'statistically_significant': statistically_significant,
                'recommendation': self._forward_return_recommendation(
                    sufficient_samples, statistically_significant, t_stat
                )
            }

        return validation_results

    def _forward_return_recommendation(self, sufficient: bool, significant: bool,
                                        t_stat: float) -> str:
        """Generate recommendation for forward return validation."""
        if not sufficient:
            return "Insufficient samples. Collect more data before trading."
        elif not significant:
            return "Not statistically significant. Use with caution or increase sample size."
        elif abs(t_stat) > 3.0:
            return "Highly significant edge detected. Monitor for regime changes."
        elif abs(t_stat) > 2.0:
            return "Statistically significant edge. Suitable for trading."
        else:
            return "Marginally significant. Consider additional filters or larger position size."

    def run_bootstrap_validation(self, data: np.ndarray, statistic_func,
                                  n_bootstrap: int = 1000) -> Dict:
        """
        Run bootstrap validation to estimate confidence intervals.

        Args:
            data: Original data
            statistic_func: Function to calculate statistic (e.g., mean, median)
            n_bootstrap: Number of bootstrap samples

        Returns:
            Bootstrap validation results
        """
        bootstrap_stats = []

        for _ in range(n_bootstrap):
            # Resample with replacement
            sample = np.random.choice(data, size=len(data), replace=True)
            stat = statistic_func(sample)
            bootstrap_stats.append(stat)

        bootstrap_stats = np.array(bootstrap_stats)

        # Calculate confidence interval
        ci_lower = np.percentile(bootstrap_stats, (1 - self.confidence_level) / 2 * 100)
        ci_upper = np.percentile(bootstrap_stats, (1 + self.confidence_level) / 2 * 100)

        # Original statistic
        original_stat = statistic_func(data)

        return {
            'original_statistic': original_stat,
            'bootstrap_mean': np.mean(bootstrap_stats),
            'bootstrap_std': np.std(bootstrap_stats),
            'confidence_interval': (ci_lower, ci_upper),
            'bias': np.mean(bootstrap_stats) - original_stat,
            'within_ci': ci_lower <= original_stat <= ci_upper
        }

    def validate_backtest_results(self, trades: List[float],
                                   benchmark_returns: Optional[List[float]] = None) -> Dict:
        """
        Comprehensive validation of backtest results.

        Args:
            trades: List of trade returns
            benchmark_returns: Optional benchmark returns for comparison

        Returns:
            Comprehensive validation metrics
        """
        trades = np.array(trades)

        # Basic statistics
        total_trades = len(trades)
        winning_trades = np.sum(trades > 0)
        losing_trades = np.sum(trades < 0)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        # Return statistics
        avg_win = np.mean(trades[trades > 0]) if winning_trades > 0 else 0
        avg_loss = np.mean(trades[trades < 0]) if losing_trades > 0 else 0

        # Expectancy
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)

        # Sharpe ratio
        sharpe = (np.mean(trades) / np.std(trades)) * np.sqrt(252) if np.std(trades) > 0 else 0

        # Maximum drawdown
        equity = np.cumsum(trades)
        running_max = np.maximum.accumulate(equity)
        drawdown = equity - running_max
        max_drawdown = np.min(drawdown)

        # Statistical tests
        # T-test for mean return
        t_stat, p_value = stats.ttest_1samp(trades, 0)

        results = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'expectancy': expectancy,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            't_statistic': t_stat,
            'p_value': p_value,
            'statistically_significant': p_value < self.alpha,
            'valid_backtest': self._validate_backtest_quality(
                total_trades, expectancy, sharpe, max_drawdown
            )
        }

        # Benchmark comparison if provided
        if benchmark_returns is not None:
            benchmark_returns = np.array(benchmark_returns)
            if len(trades) == len(benchmark_returns):
                excess_returns = trades - benchmark_returns
                info_ratio = (np.mean(excess_returns) / np.std(excess_returns)) * np.sqrt(252) \
                    if np.std(excess_returns) > 0 else 0

                results['information_ratio'] = info_ratio
                results['outperforms_benchmark'] = np.mean(excess_returns) > 0

        return results

    def _validate_backtest_quality(self, n_trades: int, expectancy: float,
                                    sharpe: float, max_dd: float) -> Dict:
        """Validate overall backtest quality."""
        issues = []

        if n_trades < 30:
            issues.append("Insufficient number of trades (< 30)")

        if expectancy <= 0:
            issues.append("Negative or zero expectancy")

        if sharpe < 1.0:
            issues.append("Low Sharpe ratio (< 1.0)")

        if abs(max_dd) > 0.3:
            issues.append("Large maximum drawdown (> 30%)")

        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'quality_score': self._calculate_quality_score(n_trades, expectancy, sharpe, max_dd)
        }

    def _calculate_quality_score(self, n_trades: int, expectancy: float,
                                  sharpe: float, max_dd: float) -> float:
        """Calculate overall backtest quality score (0-100)."""
        score = 0

        # Sample size (max 25 points)
        score += min(n_trades / 100 * 25, 25)

        # Expectancy (max 25 points)
        score += min(max(expectancy * 500, 0), 25)

        # Sharpe ratio (max 25 points)
        score += min(sharpe / 3 * 25, 25)

        # Drawdown (max 25 points)
        score += max(25 + max_dd * 50, 0)  # Penalize drawdown

        return min(score, 100)


# Helper functions for common statistical validations

def validate_percentile_bin_statistics(bin_stats: Dict[str, Dict]) -> Dict:
    """
    Validate statistics for all percentile bins.

    Args:
        bin_stats: Dictionary mapping bin names to statistics

    Returns:
        Validation results
    """
    validator = StatisticalValidator()

    results = {}
    for bin_name, stats in bin_stats.items():
        if 'samples' in stats and stats['samples'] > 0:
            # Check minimum sample size
            min_samples = 30
            sufficient = stats['samples'] >= min_samples

            # Check statistical significance
            t_score = stats.get('t_score', 0)
            significant = abs(t_score) >= 1.96  # 95% confidence

            results[bin_name] = {
                'sufficient_samples': sufficient,
                'statistically_significant': significant,
                'quality': 'good' if sufficient and significant else 'poor'
            }

    return results


def calculate_required_sample_size(effect_size: float, power: float = 0.80,
                                    alpha: float = 0.05) -> int:
    """
    Calculate required sample size for given effect size and power.

    Args:
        effect_size: Expected effect size (Cohen's d)
        power: Desired statistical power
        alpha: Significance level

    Returns:
        Required sample size
    """
    from scipy.stats import norm

    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(power)

    n = 2 * ((z_alpha + z_beta) / effect_size) ** 2

    return int(np.ceil(n))
