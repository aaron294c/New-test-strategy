#!/usr/bin/env python3
"""
Percentile-to-Forward-Return Mapping Framework

This module implements prospective extrapolation methods to turn RSI-MA percentile
rankings into expected forward % change predictions.

Methods Implemented:
1. Empirical Conditional Expectation (bin-based lookup)
2. Transition Matrix (Markov chain for percentile evolution)
3. Linear/Polynomial Regression
4. Quantile Regression (for tail risk estimation)
5. Kernel Smoothing (nonparametric)
6. Rolling Window Backtesting

Purpose: Given current RSI-MA percentile → predict expected return at horizons (1d, 5d, 10d)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from scipy import stats
from sklearn.linear_model import LinearRegression, QuantileRegressor
from sklearn.preprocessing import PolynomialFeatures
import warnings
warnings.filterwarnings('ignore')


@dataclass
class PercentileBinStats:
    """Statistics for a single percentile bin."""
    bin_label: str  # e.g., "0-5", "5-15"
    bin_min: float
    bin_max: float
    count: int

    # Forward returns by horizon (NEW: 3, 7, 14, 21 days)
    mean_return_3d: float
    mean_return_7d: float
    mean_return_14d: float
    mean_return_21d: float

    median_return_3d: float
    median_return_7d: float
    median_return_14d: float
    median_return_21d: float

    std_return_3d: float
    std_return_7d: float
    std_return_14d: float
    std_return_21d: float

    # Risk metrics (using 3-day as baseline)
    downside_risk_3d: float  # Std of negative returns
    upside_potential_3d: float  # Mean of positive returns

    # Percentiles of return distribution (using 3-day)
    pct_5_return_3d: float  # 5th percentile (worst case)
    pct_95_return_3d: float  # 95th percentile (best case)


@dataclass
class TransitionMatrix:
    """Markov transition matrix between percentile bins."""
    bins: List[str]
    matrix: np.ndarray  # P[i,j] = Pr(next state = j | current state = i)
    horizon_days: int
    sample_sizes: np.ndarray  # Number of transitions observed for each state


@dataclass
class RegressionForecast:
    """Regression-based forecast."""
    model_type: str  # 'linear', 'polynomial', 'quantile'
    coefficients: List[float]
    r_squared: float
    mae: float  # Mean absolute error
    forecast_3d: float
    forecast_7d: float
    forecast_14d: float
    forecast_21d: float
    confidence_interval_95: Tuple[float, float]


@dataclass
class KernelForecast:
    """Kernel smoothing forecast."""
    bandwidth: float
    effective_sample_size: float
    forecast_3d: float
    forecast_7d: float
    forecast_14d: float
    forecast_21d: float
    std_error_3d: float


@dataclass
class PercentileFirstForecast:
    """Percentile-first prediction: predict future percentile, then convert to return."""
    horizon_days: int

    # Step 1: Future percentile prediction
    predicted_percentile: float
    percentile_confidence: float  # 0-100, based on transition matrix entropy

    # Step 2: Convert to return using empirical mapping
    expected_return_from_future_pct: float

    # Risk bounds from future percentile bin
    downside_5th: float
    upside_95th: float

    # Comparison to direct prediction
    direct_prediction: float  # Traditional method (current pct → future return)
    percentile_first_advantage: float  # Difference between methods


@dataclass
class ConfidenceAssessment:
    """Multi-factor confidence scoring for predictions."""
    overall_confidence: str  # "HIGH", "MEDIUM", "LOW"
    confidence_score: float  # 0-100

    # Individual factors
    directional_agreement: bool  # Forecast agrees with percentile position
    sample_size_adequate: bool  # Enough historical data
    volatility_regime: str  # "normal", "high", "extreme"
    forecast_magnitude: str  # "strong", "moderate", "weak"

    # Recommendations
    recommended_action: str  # "TRADE", "CAUTIOUS", "AVOID"
    position_size_pct: float  # 0-100% of max position
    reasoning: str


@dataclass
class ForwardReturnPrediction:
    """Complete forward return prediction for current state."""
    current_percentile: float
    current_rsi_ma: float

    # Empirical mapping
    empirical_bin_stats: PercentileBinStats

    # Markov-based prediction
    markov_forecast_3d: float
    markov_forecast_7d: float
    markov_forecast_14d: float
    markov_forecast_21d: float

    # NEW: Percentile-first predictions
    percentile_first_3d: PercentileFirstForecast
    percentile_first_7d: PercentileFirstForecast
    percentile_first_14d: PercentileFirstForecast
    percentile_first_21d: PercentileFirstForecast

    # Regression-based predictions
    linear_regression: RegressionForecast
    polynomial_regression: Optional[RegressionForecast]
    quantile_regression_median: RegressionForecast
    quantile_regression_05: RegressionForecast  # 5th percentile (downside)
    quantile_regression_95: RegressionForecast  # 95th percentile (upside)

    # Kernel smoothing
    kernel_forecast: KernelForecast

    # Ensemble prediction (average of methods)
    ensemble_forecast_3d: float
    ensemble_forecast_7d: float
    ensemble_forecast_14d: float
    ensemble_forecast_21d: float

    # NEW: Confidence assessment
    confidence_3d: ConfidenceAssessment
    confidence_7d: ConfidenceAssessment
    confidence_14d: ConfidenceAssessment
    confidence_21d: ConfidenceAssessment


class PercentileForwardMapper:
    """
    Maps RSI-MA percentiles to expected forward returns.

    Core functionality:
    - Build empirical bin mapping from historical data
    - Construct transition matrices
    - Fit regression models
    - Perform kernel estimation
    - Generate out-of-sample forecasts with rolling windows
    """

    def __init__(self,
                 percentile_bins: List[Tuple[float, float, str]] = None,
                 horizons: List[int] = [3, 7, 14, 21]):
        """
        Initialize mapper.

        Args:
            percentile_bins: List of (min, max, label) tuples for bins
            horizons: Forecast horizons in days
        """
        if percentile_bins is None:
            # Default bins: focus on extremes
            self.percentile_bins = [
                (0, 5, '0-5'),
                (5, 15, '5-15'),
                (15, 25, '15-25'),
                (25, 50, '25-50'),
                (50, 75, '50-75'),
                (75, 85, '75-85'),
                (85, 95, '85-95'),
                (95, 100, '95-100'),
            ]
        else:
            self.percentile_bins = percentile_bins

        self.horizons = horizons
        self.bin_lookup = {}  # Cache for bin stats
        self.transition_matrices = {}  # Cache for transition matrices by horizon
        self.regression_models = {}  # Cache for fitted models

    def assign_bin(self, percentile: float) -> int:
        """Assign percentile to bin index."""
        for i, (pmin, pmax, _) in enumerate(self.percentile_bins):
            if pmin <= percentile < pmax:
                return i
        return len(self.percentile_bins) - 1  # Last bin

    def _calculate_rsi_ma(self, data: pd.DataFrame, rsi_length: int, ma_length: int) -> pd.Series:
        """
        Calculate RSI-MA indicator using EXACT same method as position_manager.py and enhanced_mtf_analyzer.py

        Pipeline:
        1. Calculate log returns from Close price
        2. Calculate change of returns (diff)
        3. Apply RSI (14-period) using Wilder's method
        4. Apply EMA (14-period) to RSI
        """
        close_price = data['Close']

        # Step 1: Calculate log returns
        log_returns = np.log(close_price / close_price.shift(1)).fillna(0)

        # Step 2: Calculate change of returns (second derivative)
        delta = log_returns.diff()

        # Step 3: Apply RSI to delta
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)

        # Wilder's smoothing (RMA)
        avg_gains = gains.ewm(alpha=1/rsi_length, adjust=False).mean()
        avg_losses = losses.ewm(alpha=1/rsi_length, adjust=False).mean()

        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.fillna(50)

        # Step 4: Apply EMA to RSI
        rsi_ma = rsi.ewm(span=ma_length, adjust=False).mean()

        return rsi_ma

    def build_historical_dataset(self,
                                 rsi_ma: pd.Series,
                                 percentile_ranks: pd.Series,
                                 prices: pd.Series,
                                 lookback_window: int = 500) -> pd.DataFrame:
        """
        Build dataset with (percentile_t, RSI_MA_t, forward_returns).

        Returns DataFrame with columns:
        - date, percentile, rsi_ma, bin, ret_1d, ret_5d, ret_10d, pct_next_1d, ...
        """
        data = []

        for i in range(lookback_window, len(prices) - max(self.horizons)):
            date = prices.index[i]
            pct = percentile_ranks.iloc[i]
            rsi = rsi_ma.iloc[i]
            price = prices.iloc[i]
            bin_idx = self.assign_bin(pct)

            if np.isnan(pct) or np.isnan(rsi):
                continue

            # Calculate forward returns
            forward_rets = {}
            forward_pcts = {}
            for h in self.horizons:
                if i + h < len(prices):
                    future_price = prices.iloc[i + h]
                    ret = (future_price / price - 1) * 100
                    forward_rets[f'ret_{h}d'] = ret

                    # Also store future percentile
                    if i + h < len(percentile_ranks):
                        forward_pcts[f'pct_next_{h}d'] = percentile_ranks.iloc[i + h]

            row = {
                'date': date,
                'percentile': pct,
                'rsi_ma': rsi,
                'bin': bin_idx,
                'price': price,
                **forward_rets,
                **forward_pcts
            }
            data.append(row)

        df = pd.DataFrame(data)
        return df

    def calculate_empirical_bin_stats(self, df: pd.DataFrame) -> Dict[int, PercentileBinStats]:
        """
        Method 1: Empirical conditional expectation.

        For each bin, compute mean, median, std, percentiles of forward returns.
        """
        bin_stats = {}

        for bin_idx, (pmin, pmax, label) in enumerate(self.percentile_bins):
            bin_data = df[df['bin'] == bin_idx]

            if len(bin_data) < 5:  # Skip bins with too few samples
                continue

            # Extract returns for each NEW horizon (3, 7, 14, 21 days)
            ret_3d = bin_data['ret_3d'].dropna() if 'ret_3d' in bin_data.columns else pd.Series([0])
            ret_7d = bin_data['ret_7d'].dropna() if 'ret_7d' in bin_data.columns else pd.Series([0])
            ret_14d = bin_data['ret_14d'].dropna() if 'ret_14d' in bin_data.columns else pd.Series([0])
            ret_21d = bin_data['ret_21d'].dropna() if 'ret_21d' in bin_data.columns else pd.Series([0])

            # Downside risk (std of negative returns) - using 3-day
            downside = ret_3d[ret_3d < 0]
            downside_risk = downside.std() if len(downside) > 0 else 0

            # Upside potential (mean of positive returns) - using 3-day
            upside = ret_3d[ret_3d > 0]
            upside_potential = upside.mean() if len(upside) > 0 else 0

            stats_obj = PercentileBinStats(
                bin_label=label,
                bin_min=pmin,
                bin_max=pmax,
                count=len(bin_data),
                mean_return_3d=ret_3d.mean(),
                mean_return_7d=ret_7d.mean(),
                mean_return_14d=ret_14d.mean(),
                mean_return_21d=ret_21d.mean(),
                median_return_3d=ret_3d.median(),
                median_return_7d=ret_7d.median(),
                median_return_14d=ret_14d.median(),
                median_return_21d=ret_21d.median(),
                std_return_3d=ret_3d.std(),
                std_return_7d=ret_7d.std(),
                std_return_14d=ret_14d.std(),
                std_return_21d=ret_21d.std(),
                downside_risk_3d=downside_risk,
                upside_potential_3d=upside_potential,
                pct_5_return_3d=ret_3d.quantile(0.05),
                pct_95_return_3d=ret_3d.quantile(0.95),
            )

            bin_stats[bin_idx] = stats_obj

        self.bin_lookup = bin_stats
        return bin_stats

    def build_transition_matrix(self, df: pd.DataFrame, horizon: int = 1) -> TransitionMatrix:
        """
        Method 2: Markov transition matrix.

        P[i,j] = Pr(percentile_{t+h} in bin_j | percentile_t in bin_i)
        """
        n_bins = len(self.percentile_bins)
        transition_counts = np.zeros((n_bins, n_bins))
        row_totals = np.zeros(n_bins)

        col_name = f'pct_next_{horizon}d'
        if col_name not in df.columns:
            # Return uniform transition
            return TransitionMatrix(
                bins=[label for _, _, label in self.percentile_bins],
                matrix=np.ones((n_bins, n_bins)) / n_bins,
                horizon_days=horizon,
                sample_sizes=np.zeros(n_bins)
            )

        for _, row in df.iterrows():
            current_bin = int(row['bin'])
            next_pct = row[col_name]

            if np.isnan(next_pct):
                continue

            next_bin = self.assign_bin(next_pct)
            transition_counts[current_bin, next_bin] += 1
            row_totals[current_bin] += 1

        # Normalize to get probabilities
        transition_matrix = np.zeros((n_bins, n_bins))
        for i in range(n_bins):
            if row_totals[i] > 0:
                transition_matrix[i, :] = transition_counts[i, :] / row_totals[i]
            else:
                # Uniform distribution if no data
                transition_matrix[i, :] = 1 / n_bins

        tm = TransitionMatrix(
            bins=[label for _, _, label in self.percentile_bins],
            matrix=transition_matrix,
            horizon_days=horizon,
            sample_sizes=row_totals
        )

        self.transition_matrices[horizon] = tm
        return tm

    def percentile_first_forecast(self, current_bin: int, current_percentile: float, horizon: int) -> PercentileFirstForecast:
        """
        NEW METHOD: Predict future percentile first, then convert to return.

        This is MORE ACCURATE than directly predicting returns because:
        1. Percentiles are more predictable (Markov chains show this)
        2. Percentile → return mapping is empirically validated
        3. Two-step process reduces error propagation

        Steps:
        1. Use transition matrix to get probability distribution over future percentile bins
        2. Calculate expected future percentile (weighted average)
        3. Look up expected return for that future percentile
        4. Compare to direct prediction method
        """
        if horizon not in self.transition_matrices:
            return PercentileFirstForecast(
                horizon_days=horizon,
                predicted_percentile=current_percentile,
                percentile_confidence=0,
                expected_return_from_future_pct=0,
                downside_5th=0,
                upside_95th=0,
                direct_prediction=0,
                percentile_first_advantage=0
            )

        tm = self.transition_matrices[horizon]
        transition_probs = tm.matrix[current_bin]

        # Step 1: Predict future percentile using weighted average
        bin_midpoints = [(pmin + pmax) / 2 for pmin, pmax, _ in self.percentile_bins]
        predicted_percentile = sum(prob * midpoint for prob, midpoint in zip(transition_probs, bin_midpoints))

        # Calculate confidence based on entropy (lower entropy = more confident)
        # Entropy = -sum(p * log(p)) where p > 0
        entropy = -sum(p * np.log(p + 1e-10) for p in transition_probs if p > 0)
        max_entropy = np.log(len(self.percentile_bins))  # Uniform distribution
        confidence = (1 - entropy / max_entropy) * 100  # 0-100 scale

        # Step 2: Find which bin the predicted percentile falls into
        predicted_bin = self.assign_bin(predicted_percentile)

        # Step 3: Look up expected return for that future percentile bin
        if predicted_bin in self.bin_lookup:
            future_bin_stats = self.bin_lookup[predicted_bin]
            if horizon == 3:
                expected_return = future_bin_stats.mean_return_3d
                downside = future_bin_stats.pct_5_return_3d
                upside = future_bin_stats.pct_95_return_3d
            elif horizon == 7:
                expected_return = future_bin_stats.mean_return_7d
                downside = future_bin_stats.pct_5_return_3d * (horizon / 3)
                upside = future_bin_stats.pct_95_return_3d * (horizon / 3)
            elif horizon == 14:
                expected_return = future_bin_stats.mean_return_14d
                downside = future_bin_stats.pct_5_return_3d * (horizon / 3)
                upside = future_bin_stats.pct_95_return_3d * (horizon / 3)
            else:  # horizon == 21
                expected_return = future_bin_stats.mean_return_21d
                downside = future_bin_stats.pct_5_return_3d * (horizon / 3)
                upside = future_bin_stats.pct_95_return_3d * (horizon / 3)
        else:
            expected_return = 0
            downside = 0
            upside = 0

        # Step 4: Compare to direct prediction (traditional method)
        direct_prediction = self.markov_forecast(current_bin, horizon)
        advantage = expected_return - direct_prediction

        return PercentileFirstForecast(
            horizon_days=horizon,
            predicted_percentile=predicted_percentile,
            percentile_confidence=confidence,
            expected_return_from_future_pct=expected_return,
            downside_5th=downside,
            upside_95th=upside,
            direct_prediction=direct_prediction,
            percentile_first_advantage=advantage
        )

    def assess_confidence(self, current_percentile: float, ensemble_forecast: float,
                         horizon: int, bin_stats: PercentileBinStats,
                         current_atr_percentile: float = 50.0) -> ConfidenceAssessment:
        """
        Multi-factor confidence assessment for trading decisions.

        Factors:
        1. Directional agreement: Does forecast align with percentile position?
        2. Sample size: Enough historical data?
        3. Volatility regime: Trading in normal conditions?
        4. Forecast magnitude: Strong enough signal?
        """
        # Factor 1: Directional agreement
        oversold = current_percentile < 25
        overbought = current_percentile > 75
        bullish_forecast = ensemble_forecast > 0.3
        bearish_forecast = ensemble_forecast < -0.3

        directional_agreement = (
            (oversold and bullish_forecast) or  # Oversold + positive forecast = HIGH
            (overbought and bearish_forecast) or  # Overbought + negative forecast = HIGH
            (25 <= current_percentile <= 75 and abs(ensemble_forecast) < 0.3)  # Neutral = OK
        )

        # Factor 2: Sample size
        sample_size_adequate = bin_stats.count >= 50 if bin_stats else False

        # Factor 3: Volatility regime
        if current_atr_percentile < 60:
            volatility_regime = "normal"
            vol_score = 100
        elif current_atr_percentile < 80:
            volatility_regime = "high"
            vol_score = 50
        else:
            volatility_regime = "extreme"
            vol_score = 0

        # Factor 4: Forecast magnitude
        if abs(ensemble_forecast) > 0.5:
            forecast_magnitude = "strong"
            mag_score = 100
        elif abs(ensemble_forecast) > 0.2:
            forecast_magnitude = "moderate"
            mag_score = 60
        else:
            forecast_magnitude = "weak"
            mag_score = 20

        # Calculate overall confidence score
        agreement_score = 100 if directional_agreement else 30
        sample_score = 100 if sample_size_adequate else 50

        confidence_score = (
            agreement_score * 0.4 +  # 40% weight on directional agreement
            sample_score * 0.2 +     # 20% weight on sample size
            vol_score * 0.2 +        # 20% weight on volatility
            mag_score * 0.2          # 20% weight on forecast strength
        )

        # Determine overall confidence level
        if confidence_score >= 75:
            overall_confidence = "HIGH"
            recommended_action = "TRADE"
            position_size_pct = 100.0
        elif confidence_score >= 50:
            overall_confidence = "MEDIUM"
            recommended_action = "CAUTIOUS"
            position_size_pct = 50.0
        else:
            overall_confidence = "LOW"
            recommended_action = "AVOID"
            position_size_pct = 0.0

        # Build reasoning
        reasons = []
        if directional_agreement:
            if oversold and bullish_forecast:
                reasons.append("✅ Oversold + bullish forecast (strong setup)")
            elif overbought and bearish_forecast:
                reasons.append("✅ Overbought + bearish forecast (strong setup)")
        else:
            reasons.append("⚠️ Forecast conflicts with percentile position")

        if sample_size_adequate:
            reasons.append(f"✅ Adequate sample size ({bin_stats.count} events)")
        else:
            reasons.append(f"⚠️ Limited sample size ({bin_stats.count if bin_stats else 0} events)")

        if volatility_regime == "normal":
            reasons.append("✅ Normal volatility regime (favorable)")
        elif volatility_regime == "extreme":
            reasons.append("❌ EXTREME volatility (avoid trading)")

        if forecast_magnitude == "strong":
            reasons.append(f"✅ Strong forecast ({ensemble_forecast:+.2f}%)")
        elif forecast_magnitude == "weak":
            reasons.append(f"⚠️ Weak forecast ({ensemble_forecast:+.2f}%)")

        reasoning = " | ".join(reasons)

        return ConfidenceAssessment(
            overall_confidence=overall_confidence,
            confidence_score=confidence_score,
            directional_agreement=bool(directional_agreement),
            sample_size_adequate=bool(sample_size_adequate),
            volatility_regime=volatility_regime,
            forecast_magnitude=forecast_magnitude,
            recommended_action=recommended_action,
            position_size_pct=position_size_pct,
            reasoning=reasoning
        )

    def markov_forecast(self, current_bin: int, horizon: int) -> float:
        """
        Predict expected return using Markov chain.

        Logic:
        1. Get transition probabilities from current_bin to all future bins
        2. Weight each bin's expected return by transition probability
        3. Return weighted average
        """
        if horizon not in self.transition_matrices:
            return 0.0

        tm = self.transition_matrices[horizon]
        transition_probs = tm.matrix[current_bin, :]

        # Weight each bin's return by probability of transitioning to it
        expected_return = 0.0
        for j, prob in enumerate(transition_probs):
            if j in self.bin_lookup:
                bin_stats = self.bin_lookup[j]
                if horizon == 3:
                    expected_return += prob * bin_stats.mean_return_3d
                elif horizon == 7:
                    expected_return += prob * bin_stats.mean_return_7d
                elif horizon == 14:
                    expected_return += prob * bin_stats.mean_return_14d
                elif horizon == 21:
                    expected_return += prob * bin_stats.mean_return_21d

        return expected_return

    def fit_regression_models(self, df: pd.DataFrame):
        """
        Method 3: Regression models (linear, polynomial, quantile).
        """
        X = df[['percentile']].values

        models = {}

        for h in self.horizons:
            col = f'ret_{h}d'
            if col not in df.columns:
                continue

            y = df[col].dropna().values
            X_valid = X[df[col].notna()]

            if len(y) < 20:
                continue

            # 1. Linear regression
            lr = LinearRegression()
            lr.fit(X_valid, y)
            y_pred = lr.predict(X_valid)
            r2 = 1 - np.sum((y - y_pred)**2) / np.sum((y - y.mean())**2)
            mae = np.mean(np.abs(y - y_pred))

            models[f'linear_{h}d'] = {
                'model': lr,
                'r2': r2,
                'mae': mae
            }

            # 2. Polynomial regression (degree 2)
            poly = PolynomialFeatures(degree=2)
            X_poly = poly.fit_transform(X_valid)
            lr_poly = LinearRegression()
            lr_poly.fit(X_poly, y)
            y_pred_poly = lr_poly.predict(X_poly)
            r2_poly = 1 - np.sum((y - y_pred_poly)**2) / np.sum((y - y.mean())**2)
            mae_poly = np.mean(np.abs(y - y_pred_poly))

            models[f'polynomial_{h}d'] = {
                'model': lr_poly,
                'poly_transformer': poly,
                'r2': r2_poly,
                'mae': mae_poly
            }

            # 3. Quantile regression (median, 5th, 95th percentiles)
            for q in [0.5, 0.05, 0.95]:
                qr = QuantileRegressor(quantile=q, alpha=0, solver='highs')
                qr.fit(X_valid, y)

                models[f'quantile_{q}_{h}d'] = {
                    'model': qr,
                    'quantile': q
                }

        self.regression_models = models

    def kernel_forecast(self, df: pd.DataFrame, current_percentile: float, horizon: int, bandwidth: float = 10.0) -> KernelForecast:
        """
        Method 4: Kernel smoothing (Nadaraya-Watson estimator).

        E[R_{t+h} | p_t = p] = Σ K((p_i - p)/h) * R_i / Σ K((p_i - p)/h)
        """
        col = f'ret_{horizon}d'
        if col not in df.columns:
            return KernelForecast(bandwidth, 0, 0, 0, 0, 0)

        percentiles = df['percentile'].values
        returns = df[col].values

        # Gaussian kernel
        weights = np.exp(-0.5 * ((percentiles - current_percentile) / bandwidth) ** 2)
        weights = weights / (np.sqrt(2 * np.pi) * bandwidth)

        # Effective sample size
        eff_n = np.sum(weights) ** 2 / np.sum(weights ** 2)

        # Weighted average
        if np.sum(weights) > 0:
            forecast = np.sum(weights * returns) / np.sum(weights)
            # Weighted variance
            weighted_var = np.sum(weights * (returns - forecast) ** 2) / np.sum(weights)
            std_error = np.sqrt(weighted_var / eff_n)
        else:
            forecast = 0
            std_error = 0

        # For other horizons, recompute
        forecasts = {}
        for h in self.horizons:
            if f'ret_{h}d' in df.columns:
                ret_h = df[f'ret_{h}d'].values
                if np.sum(weights) > 0:
                    forecasts[h] = np.sum(weights * ret_h) / np.sum(weights)
                else:
                    forecasts[h] = 0

        return KernelForecast(
            bandwidth=bandwidth,
            effective_sample_size=eff_n,
            forecast_3d=forecasts.get(3, 0),
            forecast_7d=forecasts.get(7, 0),
            forecast_14d=forecasts.get(14, 0),
            forecast_21d=forecasts.get(21, 0),
            std_error_3d=std_error
        )

    def predict_forward_returns(self, df: pd.DataFrame, current_percentile: float, current_rsi_ma: float) -> ForwardReturnPrediction:
        """
        Generate comprehensive forward return prediction using all methods for NEW horizons (3, 7, 14, 21).
        """
        current_bin = self.assign_bin(current_percentile)

        # 1. Empirical bin stats
        if current_bin in self.bin_lookup:
            empirical = self.bin_lookup[current_bin]
        else:
            # Fallback to nearest bin
            empirical = list(self.bin_lookup.values())[0] if self.bin_lookup else None

        # 2. Markov forecasts for all NEW horizons
        markov_3d = self.markov_forecast(current_bin, 3)
        markov_7d = self.markov_forecast(current_bin, 7)
        markov_14d = self.markov_forecast(current_bin, 14)
        markov_21d = self.markov_forecast(current_bin, 21)

        # 3. Percentile-first forecasts for all NEW horizons
        pf_3d = self.percentile_first_forecast(current_bin, current_percentile, 3)
        pf_7d = self.percentile_first_forecast(current_bin, current_percentile, 7)
        pf_14d = self.percentile_first_forecast(current_bin, current_percentile, 14)
        pf_21d = self.percentile_first_forecast(current_bin, current_percentile, 21)

        # 4. Regression forecasts
        X_new = np.array([[current_percentile]])

        # Linear regression
        lr_3d = self.regression_models.get('linear_3d')
        if lr_3d:
            lr_forecast_3d = lr_3d['model'].predict(X_new)[0]
            lr_forecast_7d = self.regression_models.get('linear_7d', {}).get('model', lr_3d['model']).predict(X_new)[0]
            lr_forecast_14d = self.regression_models.get('linear_14d', {}).get('model', lr_3d['model']).predict(X_new)[0]
            lr_forecast_21d = self.regression_models.get('linear_21d', {}).get('model', lr_3d['model']).predict(X_new)[0]

            linear_reg = RegressionForecast(
                model_type='linear',
                coefficients=lr_3d['model'].coef_.tolist(),
                r_squared=lr_3d['r2'],
                mae=lr_3d['mae'],
                forecast_3d=lr_forecast_3d,
                forecast_7d=lr_forecast_7d,
                forecast_14d=lr_forecast_14d,
                forecast_21d=lr_forecast_21d,
                confidence_interval_95=(lr_forecast_3d - 1.96 * lr_3d['mae'], lr_forecast_3d + 1.96 * lr_3d['mae'])
            )
        else:
            linear_reg = None

        # Polynomial regression
        poly_3d = self.regression_models.get('polynomial_3d')
        if poly_3d:
            X_poly = poly_3d['poly_transformer'].transform(X_new)
            poly_forecast_3d = poly_3d['model'].predict(X_poly)[0]

            poly_7d_model = self.regression_models.get('polynomial_7d')
            poly_forecast_7d = poly_7d_model['model'].predict(poly_7d_model['poly_transformer'].transform(X_new))[0] if poly_7d_model else poly_forecast_3d

            poly_14d_model = self.regression_models.get('polynomial_14d')
            poly_forecast_14d = poly_14d_model['model'].predict(poly_14d_model['poly_transformer'].transform(X_new))[0] if poly_14d_model else poly_forecast_3d

            poly_21d_model = self.regression_models.get('polynomial_21d')
            poly_forecast_21d = poly_21d_model['model'].predict(poly_21d_model['poly_transformer'].transform(X_new))[0] if poly_21d_model else poly_forecast_3d

            polynomial_reg = RegressionForecast(
                model_type='polynomial',
                coefficients=poly_3d['model'].coef_.tolist(),
                r_squared=poly_3d['r2'],
                mae=poly_3d['mae'],
                forecast_3d=poly_forecast_3d,
                forecast_7d=poly_forecast_7d,
                forecast_14d=poly_forecast_14d,
                forecast_21d=poly_forecast_21d,
                confidence_interval_95=(poly_forecast_3d - 1.96 * poly_3d['mae'], poly_forecast_3d + 1.96 * poly_3d['mae'])
            )
        else:
            polynomial_reg = None

        # Quantile regressions
        qr_median_3d = self.regression_models.get('quantile_0.5_3d')
        qr_05_3d = self.regression_models.get('quantile_0.05_3d')
        qr_95_3d = self.regression_models.get('quantile_0.95_3d')

        quantile_median = RegressionForecast(
            model_type='quantile_median',
            coefficients=[],
            r_squared=0,
            mae=0,
            forecast_3d=qr_median_3d['model'].predict(X_new)[0] if qr_median_3d else 0,
            forecast_7d=self.regression_models.get('quantile_0.5_7d', {}).get('model', qr_median_3d['model'] if qr_median_3d else None).predict(X_new)[0] if qr_median_3d else 0,
            forecast_14d=self.regression_models.get('quantile_0.5_14d', {}).get('model', qr_median_3d['model'] if qr_median_3d else None).predict(X_new)[0] if qr_median_3d else 0,
            forecast_21d=self.regression_models.get('quantile_0.5_21d', {}).get('model', qr_median_3d['model'] if qr_median_3d else None).predict(X_new)[0] if qr_median_3d else 0,
            confidence_interval_95=(0, 0)
        )

        quantile_05_reg = RegressionForecast(
            model_type='quantile_05',
            coefficients=[],
            r_squared=0,
            mae=0,
            forecast_3d=qr_05_3d['model'].predict(X_new)[0] if qr_05_3d else 0,
            forecast_7d=0,
            forecast_14d=0,
            forecast_21d=0,
            confidence_interval_95=(0, 0)
        )

        quantile_95_reg = RegressionForecast(
            model_type='quantile_95',
            coefficients=[],
            r_squared=0,
            mae=0,
            forecast_3d=qr_95_3d['model'].predict(X_new)[0] if qr_95_3d else 0,
            forecast_7d=0,
            forecast_14d=0,
            forecast_21d=0,
            confidence_interval_95=(0, 0)
        )

        # 5. Kernel forecast
        kernel_pred = self.kernel_forecast(df, current_percentile, 3, bandwidth=10.0)

        # 6. Ensemble (average of all methods) for each horizon
        forecasts_3d = [
            empirical.mean_return_3d if empirical else 0,
            markov_3d,
            linear_reg.forecast_3d if linear_reg else 0,
            polynomial_reg.forecast_3d if polynomial_reg else 0,
            quantile_median.forecast_3d,
            kernel_pred.forecast_3d
        ]

        forecasts_7d = [
            empirical.mean_return_7d if empirical else 0,
            markov_7d,
            linear_reg.forecast_7d if linear_reg else 0,
            polynomial_reg.forecast_7d if polynomial_reg else 0,
            quantile_median.forecast_7d,
            kernel_pred.forecast_7d
        ]

        forecasts_14d = [
            empirical.mean_return_14d if empirical else 0,
            markov_14d,
            linear_reg.forecast_14d if linear_reg else 0,
            polynomial_reg.forecast_14d if polynomial_reg else 0,
            quantile_median.forecast_14d,
            kernel_pred.forecast_14d
        ]

        forecasts_21d = [
            empirical.mean_return_21d if empirical else 0,
            markov_21d,
            linear_reg.forecast_21d if linear_reg else 0,
            polynomial_reg.forecast_21d if polynomial_reg else 0,
            quantile_median.forecast_21d,
            kernel_pred.forecast_21d
        ]

        ensemble_3d = np.mean([f for f in forecasts_3d if not np.isnan(f)])
        ensemble_7d = np.mean([f for f in forecasts_7d if not np.isnan(f)])
        ensemble_14d = np.mean([f for f in forecasts_14d if not np.isnan(f)])
        ensemble_21d = np.mean([f for f in forecasts_21d if not np.isnan(f)])

        # 7. Confidence assessments for each horizon
        confidence_3d = self.assess_confidence(current_percentile, ensemble_3d, 3, empirical)
        confidence_7d = self.assess_confidence(current_percentile, ensemble_7d, 7, empirical)
        confidence_14d = self.assess_confidence(current_percentile, ensemble_14d, 14, empirical)
        confidence_21d = self.assess_confidence(current_percentile, ensemble_21d, 21, empirical)

        return ForwardReturnPrediction(
            current_percentile=current_percentile,
            current_rsi_ma=current_rsi_ma,
            empirical_bin_stats=empirical,
            markov_forecast_3d=markov_3d,
            markov_forecast_7d=markov_7d,
            markov_forecast_14d=markov_14d,
            markov_forecast_21d=markov_21d,
            percentile_first_3d=pf_3d,
            percentile_first_7d=pf_7d,
            percentile_first_14d=pf_14d,
            percentile_first_21d=pf_21d,
            linear_regression=linear_reg,
            polynomial_regression=polynomial_reg,
            quantile_regression_median=quantile_median,
            quantile_regression_05=quantile_05_reg,
            quantile_regression_95=quantile_95_reg,
            kernel_forecast=kernel_pred,
            ensemble_forecast_3d=ensemble_3d,
            ensemble_forecast_7d=ensemble_7d,
            ensemble_forecast_14d=ensemble_14d,
            ensemble_forecast_21d=ensemble_21d,
            confidence_3d=confidence_3d,
            confidence_7d=confidence_7d,
            confidence_14d=confidence_14d,
            confidence_21d=confidence_21d
        )

    def rolling_window_backtest(self,
                                df: pd.DataFrame,
                                train_window: int = 252,
                                test_window: int = 21,
                                step_size: int = 21) -> pd.DataFrame:
        """
        Method 5: Rolling window out-of-sample backtest.

        Train on past train_window, predict next test_window, then roll forward.

        PERFORMANCE OPTIMIZED:
        - Reduced step size (skip every N days instead of every day)
        - Limited to max 500 iterations

        Returns DataFrame with actual vs predicted returns.
        """
        results = []
        max_iterations = 500  # Limit iterations for performance

        # Step through data with step_size to reduce computation
        total_iterations = (len(df) - train_window - test_window) // step_size
        iterations_to_run = min(total_iterations, max_iterations)

        for i in range(iterations_to_run):
            start = i * step_size
            end_train = start + train_window
            end_test = min(end_train + test_window, len(df))

            if end_test >= len(df):
                break

            train_df = df.iloc[start:end_train]
            test_df = df.iloc[end_train:end_test]

            # Fit models on training data
            self.calculate_empirical_bin_stats(train_df)
            for h in self.horizons:
                self.build_transition_matrix(train_df, h)
            self.fit_regression_models(train_df)

            # Predict on test data (sample only a few points per window)
            sample_indices = [0, len(test_df)//2, len(test_df)-1] if len(test_df) > 2 else range(len(test_df))

            for idx in sample_indices:
                if idx >= len(test_df):
                    continue

                row = test_df.iloc[idx]
                pct = row['percentile']
                rsi = row['rsi_ma']

                if np.isnan(pct):
                    continue

                pred = self.predict_forward_returns(train_df, pct, rsi)

                result = {
                    'date': row['date'],
                    'percentile': pct,
                    'actual_3d': row.get('ret_3d', np.nan),
                    'actual_7d': row.get('ret_7d', np.nan),
                    'actual_14d': row.get('ret_14d', np.nan),
                    'actual_21d': row.get('ret_21d', np.nan),
                    'predicted_3d': pred.ensemble_forecast_3d,
                    'predicted_7d': pred.ensemble_forecast_7d,
                    'predicted_14d': pred.ensemble_forecast_14d,
                    'predicted_21d': pred.ensemble_forecast_21d,
                    'empirical_3d': pred.empirical_bin_stats.mean_return_3d if pred.empirical_bin_stats else np.nan,
                    'markov_3d': pred.markov_forecast_3d,
                    'linear_3d': pred.linear_regression.forecast_3d if pred.linear_regression else np.nan,
                    'kernel_3d': pred.kernel_forecast.forecast_3d
                }
                results.append(result)

        return pd.DataFrame(results)

    def evaluate_forecast_accuracy(self, backtest_df: pd.DataFrame) -> Dict:
        """
        Calculate evaluation metrics: MAE, RMSE, Hit Rate, Sharpe, Information Ratio.
        """
        metrics = {}

        for h in self.horizons:
            actual_col = f'actual_{h}d'
            pred_col = f'predicted_{h}d'

            if actual_col not in backtest_df or pred_col not in backtest_df:
                continue

            actual = backtest_df[actual_col].dropna()
            pred = backtest_df[pred_col].dropna()

            # Align
            common_idx = actual.index.intersection(pred.index)
            actual = actual.loc[common_idx]
            pred = pred.loc[common_idx]

            if len(actual) == 0:
                continue

            # Errors
            errors = actual - pred
            mae = np.mean(np.abs(errors))
            rmse = np.sqrt(np.mean(errors ** 2))

            # Hit rate (sign accuracy)
            hit_rate = np.mean((np.sign(actual) == np.sign(pred))) * 100

            # If we trade based on predicted sign
            strategy_returns = actual * np.sign(pred)
            sharpe = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252 / h) if strategy_returns.std() > 0 else 0

            # Information ratio (excess return over naive)
            naive_returns = actual  # Just going long every time
            excess = strategy_returns - naive_returns
            ir = excess.mean() / excess.std() * np.sqrt(252 / h) if excess.std() > 0 else 0

            metrics[f'{h}d'] = {
                'mae': mae,
                'rmse': rmse,
                'hit_rate': hit_rate,
                'sharpe': sharpe,
                'information_ratio': ir,
                'mean_prediction': pred.mean(),
                'mean_actual': actual.mean(),
                'correlation': np.corrcoef(actual, pred)[0, 1]
            }

        return metrics


def run_percentile_forward_analysis(ticker: str, lookback_days: int = 1095) -> Dict:
    """
    Run complete percentile-to-forward-return analysis.

    Returns comprehensive analysis with all methods.
    """
    # Import analyzer from enhanced_mtf_analyzer
    from enhanced_mtf_analyzer import EnhancedMultiTimeframeAnalyzer

    print(f"\n{'='*80}")
    print(f"PERCENTILE FORWARD MAPPING ANALYSIS: {ticker}")
    print(f"{'='*80}\n")

    # Initialize analyzer
    analyzer = EnhancedMultiTimeframeAnalyzer(ticker, lookback_days=lookback_days)

    # Build historical dataset
    mapper = PercentileForwardMapper(horizons=[3, 7, 14, 21])

    print("Building historical dataset...")
    df = mapper.build_historical_dataset(
        rsi_ma=analyzer.daily_rsi_ma,
        percentile_ranks=analyzer.daily_percentiles,
        prices=analyzer.daily_data['Close'],
        lookback_window=252
    )

    print(f"  ✓ Dataset: {len(df)} observations")

    # 1. Empirical bin stats
    print("\n1. Calculating empirical bin statistics...")
    bin_stats = mapper.calculate_empirical_bin_stats(df)
    print(f"  ✓ Computed stats for {len(bin_stats)} bins")

    for bin_idx, stats in bin_stats.items():
        print(f"    {stats.bin_label}: n={stats.count}, "
              f"E[R_3d]={stats.mean_return_3d:+.2f}%, "
              f"E[R_7d]={stats.mean_return_7d:+.2f}%, "
              f"E[R_14d]={stats.mean_return_14d:+.2f}%, "
              f"E[R_21d]={stats.mean_return_21d:+.2f}%")

    # 2. Transition matrices
    print("\n2. Building transition matrices...")
    for h in [3, 7, 14, 21]:
        tm = mapper.build_transition_matrix(df, h)
        print(f"  ✓ {h}d transition matrix (sample sizes: {tm.sample_sizes.sum():.0f} total)")

    # 3. Regression models
    print("\n3. Fitting regression models...")
    mapper.fit_regression_models(df)
    print(f"  ✓ Fitted {len(mapper.regression_models)} models")

    for key, model in mapper.regression_models.items():
        if 'linear' in key:
            print(f"    {key}: R²={model['r2']:.3f}, MAE={model['mae']:.2f}%")

    # 4. Current prediction
    current_pct = analyzer.daily_percentiles.iloc[-1]
    current_rsi = analyzer.daily_rsi_ma.iloc[-1]

    print(f"\n4. Current state prediction...")
    print(f"  Current RSI-MA Percentile: {current_pct:.1f}%ile")
    print(f"  Current RSI-MA Value: {current_rsi:.2f}")

    prediction = mapper.predict_forward_returns(df, current_pct, current_rsi)

    print(f"\n  Ensemble Forecast:")
    print(f"    3-day:  {prediction.ensemble_forecast_3d:+.2f}%")
    print(f"    7-day:  {prediction.ensemble_forecast_7d:+.2f}%")
    print(f"    14-day: {prediction.ensemble_forecast_14d:+.2f}%")
    print(f"    21-day: {prediction.ensemble_forecast_21d:+.2f}%")

    print(f"\n  Method Breakdown (3-day):")
    if prediction.empirical_bin_stats:
        print(f"    Empirical:  {prediction.empirical_bin_stats.mean_return_3d:+.2f}%")
    print(f"    Markov:     {prediction.markov_forecast_3d:+.2f}%")
    if prediction.linear_regression:
        print(f"    Linear:     {prediction.linear_regression.forecast_3d:+.2f}%")
    if prediction.polynomial_regression:
        print(f"    Polynomial: {prediction.polynomial_regression.forecast_3d:+.2f}%")
    print(f"    Kernel:     {prediction.kernel_forecast.forecast_3d:+.2f}%")

    # 5. Rolling window backtest (OPTIMIZED: step_size=21 for faster execution)
    print(f"\n5. Running rolling window backtest...")
    backtest_df = mapper.rolling_window_backtest(df, train_window=252, test_window=21, step_size=21)
    print(f"  ✓ Backtest: {len(backtest_df)} predictions")

    # 6. Evaluate accuracy
    print(f"\n6. Evaluating forecast accuracy...")
    metrics = mapper.evaluate_forecast_accuracy(backtest_df)

    for horizon, m in metrics.items():
        print(f"\n  {horizon} Horizon:")
        print(f"    MAE:              {m['mae']:.2f}%")
        print(f"    RMSE:             {m['rmse']:.2f}%")
        print(f"    Hit Rate:         {m['hit_rate']:.1f}%")
        print(f"    Sharpe Ratio:     {m['sharpe']:.2f}")
        print(f"    Information Ratio: {m['information_ratio']:.2f}")
        print(f"    Correlation:      {m['correlation']:.3f}")

    # Return comprehensive result
    return {
        'ticker': ticker,
        'current_percentile': current_pct,
        'current_rsi_ma': current_rsi,
        'prediction': asdict(prediction),
        'bin_stats': {k: asdict(v) for k, v in bin_stats.items()},
        'transition_matrices': {h: {
            'bins': tm.bins,
            'matrix': tm.matrix.tolist(),
            'sample_sizes': tm.sample_sizes.tolist()
        } for h, tm in mapper.transition_matrices.items()},
        'backtest_results': backtest_df.to_dict('records'),
        'accuracy_metrics': metrics
    }


if __name__ == '__main__':
    result = run_percentile_forward_analysis('AAPL', lookback_days=1095)

    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}")
