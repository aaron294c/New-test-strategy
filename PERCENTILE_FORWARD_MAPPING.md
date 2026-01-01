# Percentile Forward Mapping Framework

## Overview

This framework implements **prospective extrapolation** from RSI-MA percentiles to expected forward returns. It answers the key question: **"Given the current RSI-MA percentile, what return can I expect over the next N days?"**

## Purpose

Your RSI-MA indicator is the "source of truth" summarizing return state via percentiles. This framework builds on that foundation to:

1. **Map percentile → expected forward % change** using multiple statistical methods
2. **Quantify uncertainty** with confidence intervals and tail risk estimates
3. **Validate predictions** with out-of-sample rolling window backtesting
4. **Evaluate forecast quality** with metrics like Hit Rate, Sharpe Ratio, Information Ratio

## Architecture

### Core Components

```
percentile_forward_mapping.py (backend)
├── PercentileForwardMapper         # Main analysis class
├── PercentileBinStats              # Empirical bin statistics
├── TransitionMatrix                # Markov chain for percentile evolution
├── RegressionForecast              # Linear/Polynomial/Quantile regression
├── KernelForecast                  # Nonparametric smoothing
└── ForwardReturnPrediction         # Comprehensive ensemble prediction

PercentileForwardMapper.tsx (frontend)
└── Visualization component with tabs:
    ├── Empirical Bin Mapping
    ├── Transition Matrices
    ├── Model Comparison
    ├── Backtest Accuracy
    └── Predicted vs Actual
```

## Methods Implemented

### 1. Empirical Conditional Expectation (Bin-based Lookup)

**Most robust, simplest method.**

- **How it works:** For each percentile bin (0-5, 5-15, ..., 95-100), compute:
  - Mean forward return: E[R_{t+h} | p_t ∈ bin]
  - Median, Std, 5th/95th percentiles
  - Upside potential (mean of positive returns)
  - Downside risk (std of negative returns)

- **When to use:** Default method. High interpretability, no overfitting risk.

- **Example:**
  - Current percentile: 85%ile (bin 85-95)
  - Historical mean 1d return for this bin: +0.23%
  - → Expected 1d return: +0.23%

**Code location:** `percentile_forward_mapping.py:257` (`calculate_empirical_bin_stats`)

### 2. Transition Matrix (Markov Chain)

**Accounts for percentile evolution over time.**

- **How it works:**
  1. Build transition matrix P[i,j] = Pr(percentile moves from bin i to bin j in h days)
  2. Weight each future bin's expected return by transition probability
  3. Sum: E[R_{t+h}] = Σ_j P[current_bin, j] × E[R | bin_j]

- **When to use:** When percentiles exhibit structured evolution patterns (trending, mean-reverting).

- **Advantage over empirical:** Captures dynamics, not just static mapping.

**Code location:** `percentile_forward_mapping.py:351` (`build_transition_matrix`)

### 3. Regression Models

**Continuous mapping from percentile → return.**

#### Linear Regression
- R_{t+h} = β₀ + β₁ × p_t + ε
- Captures linear relationship
- Provides R², MAE for model fit assessment

#### Polynomial Regression
- R_{t+h} = β₀ + β₁ × p_t + β₂ × p_t² + ε
- Captures nonlinear (U-shape or inverted U)
- Useful if extremes behave differently than mid-range

#### Quantile Regression
- Estimates conditional **quantiles** not just mean
- q = 0.5 → median prediction
- q = 0.05 → downside risk (5th percentile)
- q = 0.95 → upside potential (95th percentile)

**When to use:**
- Linear/Poly: Quick continuous forecast
- Quantile: Model tail risk explicitly

**Code location:** `percentile_forward_mapping.py:441` (`fit_regression_models`)

### 4. Kernel Smoothing (Nadaraya-Watson)

**Nonparametric, local weighted average.**

- **How it works:**
  - E[R | p] = Σ K((p_i - p)/h) × R_i / Σ K((p_i - p)/h)
  - Gaussian kernel weights nearby observations more heavily
  - Bandwidth h controls smoothness

- **When to use:** No functional form assumption. Flexible, smooth predictions.

- **Advantage:** Adapts to local data patterns without global model.

**Code location:** `percentile_forward_mapping.py:472` (`kernel_forecast`)

### 5. Ensemble (Average of All Methods)

**Recommended for final predictions.**

- **How it works:** Average forecasts from all methods (empirical, Markov, linear, poly, quantile, kernel)
- **Benefit:** Reduces overfitting, combines strengths of each approach
- **Principle:** Ensemble generally outperforms individual models in out-of-sample tests

**Code location:** `percentile_forward_mapping.py:520` (`predict_forward_returns`)

## Backtesting Framework

### Rolling Window Out-of-Sample Testing

**Critical for avoiding lookahead bias.**

**Protocol:**
1. Train on past 252 days (1 year)
2. Predict next 21 days (1 month)
3. Roll forward, repeat
4. Never test on training data

**Evaluation Metrics:**
- **MAE (Mean Absolute Error):** Average prediction error magnitude
- **RMSE:** Penalizes large errors more heavily
- **Hit Rate:** % of correct directional predictions (> 52% = edge)
- **Sharpe Ratio:** Risk-adjusted return of trading strategy (> 1.0 = good)
- **Information Ratio:** Excess return over naive long-only (> 0.5 = outperformance)
- **Correlation:** Linear relationship between predicted and actual (> 0.3 = meaningful)

**Code location:** `percentile_forward_mapping.py:580` (`rolling_window_backtest`)

## Usage

### Backend (Python)

```python
from percentile_forward_mapping import run_percentile_forward_analysis

# Run complete analysis
result = run_percentile_forward_analysis('AAPL', lookback_days=1095)

# Access predictions
current_percentile = result['current_percentile']
forecast_1d = result['prediction']['ensemble_forecast_1d']
forecast_5d = result['prediction']['ensemble_forecast_5d']

# Access accuracy metrics
hit_rate = result['accuracy_metrics']['1d']['hit_rate']
sharpe = result['accuracy_metrics']['1d']['sharpe']

# Check if model has edge
if hit_rate > 55 and sharpe > 1:
    print("✅ Strong predictive power - Safe to trade")
else:
    print("⚠️ Weak predictive power - Use with caution")
```

### Frontend (React)

```tsx
import PercentileForwardMapper from './components/PercentileForwardMapper';

<PercentileForwardMapper ticker="AAPL" />
```

## Interpreting Results

### What Does "Expected Return" Mean?

**Empirical Bin Mean:**
- Historical average return when percentile was in this bin
- Example: "0-5 bin: -0.04%" means on average, when RSI-MA was at 0-5th percentile, the 1-day forward return was -0.04%

**Ensemble Forecast:**
- Average of all methods (empirical, Markov, regression, kernel)
- More robust than any single method
- Use this as your primary prediction

### Confidence Assessment

**High Confidence Criteria:**
✅ Hit Rate > 55% (better than random)
✅ Sharpe Ratio > 1.0 (good risk-adjusted returns)
✅ Sample Size > 50 in current bin
✅ Correlation > 0.3 between predictions and actuals

**Low Confidence Indicators:**
❌ Hit Rate < 52% (no edge)
❌ Sharpe Ratio < 0.5 (poor risk-adjusted returns)
❌ Sample Size < 20 in current bin
❌ Correlation < 0.1 (predictions not meaningful)

### Risk Metrics

**5th Percentile (Downside Risk):**
- Worst-case scenario (5% of time, return is worse than this)
- Example: "5th percentile = -2.5%" means 5% chance of losing more than 2.5%

**95th Percentile (Upside Potential):**
- Best-case scenario (5% of time, return is better than this)
- Example: "95th percentile = +3.2%" means 5% chance of gaining more than 3.2%

**Downside Risk (Std of Negative Returns):**
- Volatility when signal fails
- Lower is better (less painful losses)

## Integration with Existing System

### Consistency with position_manager.py

The framework uses **EXACT same RSI-MA calculation:**

```python
# Position Manager, Enhanced MTF Analyzer, AND Percentile Forward Mapper
# ALL use identical calculation:

# Step 1: Log returns
log_returns = np.log(close / close.shift(1)).fillna(0)

# Step 2: Change of returns (second derivative)
delta = log_returns.diff()

# Step 3: RSI on delta (Wilder's method)
gains = delta.where(delta > 0, 0)
losses = -delta.where(delta < 0, 0)
avg_gains = gains.ewm(alpha=1/14, adjust=False).mean()
avg_losses = losses.ewm(alpha=1/14, adjust=False).mean()
rs = avg_gains / avg_losses
rsi = 100 - (100 / (1 + rs))

# Step 4: EMA on RSI
rsi_ma = rsi.ewm(span=14, adjust=False).mean()
```

### Data Flow

```
RSI Indicator Tab (Source of Truth)
  ↓
Enhanced MTF Analyzer (Divergence Analysis)
  ↓
Percentile Forward Mapper (Prospective Extrapolation)
  ↓
Position Manager (Trade Recommendations)
```

## Advanced Features

### Bootstrap Confidence Intervals

**Not yet implemented, but planned:**

```python
# Resample historical data with replacement
# Recalculate bin stats 1000 times
# Compute 95% CI from distribution
```

### Nonstationarity Detection

**Detect regime changes:**
- Compare recent window vs full history
- Test for structural breaks
- Adjust predictions for current regime

### Multi-Asset Ensemble

**Aggregate predictions across correlated assets:**
- Predict AAPL return using AAPL + MSFT + GOOGL percentiles
- Weight by correlation, improve signal-to-noise

## Performance Optimization

### Caching Strategy

Computed models are cached:
- `self.bin_lookup`: Empirical stats
- `self.transition_matrices`: Markov chains
- `self.regression_models`: Fitted regressions

Recompute only when new data arrives.

### Computational Complexity

- Empirical: O(n) - single pass through data
- Transition Matrix: O(n × k²) - k = # bins
- Regression: O(n × d²) - d = # features
- Kernel: O(n) per prediction
- Backtest: O(n × m) - m = # rolling windows

**Typical runtime:** 5-10 seconds for 1095 days of data

## Validation & Testing

### Unit Tests

```bash
cd backend
python test_percentile_forward.py
```

### Expected Output

```
✓ Dataset: 833 observations
✓ Computed stats for 8 bins
✓ Transition matrix (sample sizes: 833 total)
✓ Fitted 15 models
✓ Backtest: 11760 predictions

1d Horizon:
  MAE:              1.15%
  RMSE:             1.72%
  Hit Rate:         52.5%
  Sharpe Ratio:     0.07
  Information Ratio: -0.49
  Correlation:      -0.072
```

### Interpretation Thresholds

**Strong Model (Trade Confidently):**
- Hit Rate > 55%
- Sharpe > 1.0
- Correlation > 0.3

**Moderate Model (Use with Caution):**
- Hit Rate 52-55%
- Sharpe 0.5-1.0
- Correlation 0.1-0.3

**Weak Model (Do Not Trade):**
- Hit Rate < 52%
- Sharpe < 0.5
- Correlation < 0.1

## API Endpoints (To Be Implemented)

### GET /api/percentile-forward/{ticker}

**Request:**
```bash
curl http://localhost:8000/api/percentile-forward/AAPL
```

**Response:**
```json
{
  "ticker": "AAPL",
  "current_percentile": 34.1,
  "current_rsi_ma": 49.66,
  "prediction": {
    "ensemble_forecast_1d": 0.07,
    "ensemble_forecast_5d": 0.57,
    "ensemble_forecast_10d": 1.14,
    "empirical_bin_stats": {
      "bin_label": "25-50",
      "mean_return_1d": 0.00,
      "pct_5_return_1d": -2.15,
      "pct_95_return_1d": 2.18
    },
    "markov_forecast_1d": 0.08,
    "linear_regression": {
      "forecast_1d": 0.08,
      "r_squared": 0.000,
      "confidence_interval_95": [-1.15, 1.31]
    }
  },
  "accuracy_metrics": {
    "1d": {
      "mae": 1.15,
      "hit_rate": 52.5,
      "sharpe": 0.07,
      "information_ratio": -0.49
    }
  }
}
```

## Future Enhancements

1. **Time-Varying Models:** Adapt to regime changes (bull/bear markets)
2. **Multi-Asset Signals:** Use cross-asset correlations for prediction
3. **Option Pricing Integration:** Convert percentile → IV → option strategies
4. **Real-Time Updates:** Streaming data with incremental model updates
5. **Monte Carlo Simulation:** Full return distribution, not just point estimates

## References

### Mathematical Foundations

1. **Empirical CDF:** Kaplan-Meier estimator for nonparametric distribution
2. **Markov Chains:** Transition probability estimation from time series
3. **Quantile Regression:** Koenker & Bassett (1978) - asymmetric loss function
4. **Kernel Smoothing:** Nadaraya-Watson estimator for conditional expectation
5. **Bootstrap:** Efron (1979) - resampling for confidence intervals

### Code References

- `backend/percentile_forward_mapping.py:172-205` - RSI-MA calculation (EXACT match)
- `backend/percentile_forward_mapping.py:257-319` - Empirical bin stats
- `backend/percentile_forward_mapping.py:351-408` - Transition matrix
- `backend/percentile_forward_mapping.py:441-470` - Regression models
- `backend/percentile_forward_mapping.py:520-576` - Ensemble prediction
- `backend/percentile_forward_mapping.py:580-635` - Rolling backtest

## Support

For questions or issues, please check:
1. This documentation
2. Inline code comments in `percentile_forward_mapping.py`
3. Test script: `test_percentile_forward.py`
4. Component example: `PercentileForwardMapper.tsx`

---

**Version:** 1.0
**Last Updated:** 2025-01-17
**Author:** Claude Code (Anthropic)
