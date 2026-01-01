# Market Regime Detection Framework - Technical Specification

## Executive Summary

This specification defines a comprehensive market regime detection system that classifies market conditions as **momentum-dominated** or **mean-reverting**. The framework enables adaptive strategy deployment based on statistical regime identification across multiple timeframes.

## 1. Theoretical Framework

### 1.1 Core Premise

Markets oscillate between two fundamental regimes:

1. **Momentum Regime** (Trending):
   - Directional persistence
   - Serial correlation in returns
   - Breakout strategies outperform
   - Higher percentile ranks predict continued movement

2. **Mean-Reversion Regime** (Range-bound):
   - Price oscillation around equilibrium
   - Negative serial correlation
   - Counter-trend strategies outperform
   - Extreme percentile ranks predict reversals

### 1.2 Regime Classification Methodology

#### Primary Indicators:

| Indicator | Momentum Signal | Mean-Reversion Signal | Threshold |
|-----------|----------------|----------------------|-----------|
| **ADX (Average Directional Index)** | ADX > 25 | ADX < 20 | 20-25 transition zone |
| **Hurst Exponent** | H > 0.55 | H < 0.45 | 0.50 random walk |
| **Autocorrelation (Lag 1)** | ρ₁ > 0.15 | ρ₁ < -0.15 | [-0.15, 0.15] neutral |
| **Variance Ratio** | VR > 1.2 | VR < 0.8 | 1.0 = random walk |
| **Percentile Behavior** | High → Higher | High → Lower | Statistical validation |

## 2. Statistical Indicators & Implementation

### 2.1 Average Directional Index (ADX)

**Purpose**: Measures trend strength (not direction)

**Calculation**:
```python
def calculate_adx(high, low, close, period=14):
    """
    ADX measures trend strength

    Interpretation:
    - ADX > 25: Strong trend (momentum regime likely)
    - ADX < 20: Weak trend (mean-reversion likely)
    - 20-25: Transitional zone
    """
    # 1. Calculate True Range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # 2. Calculate Directional Movement
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

    # 3. Smooth and calculate directional indicators
    atr = tr.rolling(period).mean()
    plus_di = 100 * (pd.Series(plus_dm).rolling(period).mean() / atr)
    minus_di = 100 * (pd.Series(minus_dm).rolling(period).mean() / atr)

    # 4. Calculate ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(period).mean()

    return adx, plus_di, minus_di
```

**Regime Classification**:
- **ADX > 25**: Strong trend → Momentum regime
- **ADX 20-25**: Moderate trend → Mixed regime
- **ADX < 20**: Weak trend → Mean-reversion regime

**Multi-Timeframe Integration**:
- Daily ADX: Primary regime classifier
- 4H ADX: Intraday regime validation
- Confluence: Both timeframes must agree for high-confidence classification

### 2.2 Hurst Exponent

**Purpose**: Measures time series memory and trend persistence

**Calculation**:
```python
def calculate_hurst_exponent(prices, lags=range(2, 100)):
    """
    Hurst Exponent via R/S analysis

    Interpretation:
    - H > 0.55: Persistent (trending/momentum)
    - H = 0.50: Random walk
    - H < 0.45: Anti-persistent (mean-reverting)
    """
    from scipy.stats import linregress

    # Calculate log returns
    log_returns = np.log(prices / prices.shift(1)).dropna()

    # R/S analysis
    tau = []
    rs = []

    for lag in lags:
        # Divide into subseries of length lag
        num_subseries = len(log_returns) // lag

        rs_values = []
        for i in range(num_subseries):
            subseries = log_returns[i*lag:(i+1)*lag]

            # Calculate mean-adjusted cumulative deviate
            mean_return = subseries.mean()
            cumsum = (subseries - mean_return).cumsum()

            # Calculate range
            R = cumsum.max() - cumsum.min()

            # Calculate standard deviation
            S = subseries.std()

            if S > 0:
                rs_values.append(R / S)

        tau.append(lag)
        rs.append(np.mean(rs_values))

    # Hurst = slope of log(R/S) vs log(tau)
    log_tau = np.log(tau)
    log_rs = np.log(rs)

    slope, intercept, r_value, p_value, std_err = linregress(log_tau, log_rs)

    return slope  # This is the Hurst exponent
```

**Regime Classification**:
- **H > 0.55**: Persistent trends → Momentum regime
- **H 0.45-0.55**: Neutral → Mixed regime
- **H < 0.45**: Anti-persistent → Mean-reversion regime

**Rolling Window**: Calculate over 100-200 bar windows for stability

### 2.3 Autocorrelation Analysis

**Purpose**: Detects serial dependence in returns

**Calculation**:
```python
def calculate_autocorrelation(returns, max_lag=10):
    """
    Autocorrelation function for return series

    Interpretation:
    - ρ₁ > 0.15: Positive momentum
    - ρ₁ ∈ [-0.15, 0.15]: No serial correlation
    - ρ₁ < -0.15: Mean-reversion
    """
    from statsmodels.tsa.stattools import acf

    # Calculate autocorrelation function
    acf_values = acf(returns, nlags=max_lag, fft=True)

    # Focus on lag-1 for regime detection
    lag1_corr = acf_values[1]

    # Ljung-Box test for significance
    from statsmodels.stats.diagnostic import acorr_ljungbox
    lb_test = acorr_ljungbox(returns, lags=[1], return_df=True)

    return {
        'lag1_correlation': lag1_corr,
        'ljung_box_stat': lb_test['lb_stat'].iloc[0],
        'p_value': lb_test['lb_pvalue'].iloc[0],
        'significant': lb_test['lb_pvalue'].iloc[0] < 0.05
    }
```

**Regime Classification**:
- **ρ₁ > 0.15** (and significant): Momentum regime
- **ρ₁ ∈ [-0.15, 0.15]**: Neutral regime
- **ρ₁ < -0.15** (and significant): Mean-reversion regime

**Window Selection**: 50-100 bars for stable estimates

### 2.4 Variance Ratio Test

**Purpose**: Tests random walk hypothesis

**Calculation**:
```python
def variance_ratio_test(prices, lags=[2, 4, 8, 16]):
    """
    Lo-MacKinlay Variance Ratio Test

    Interpretation:
    - VR > 1.2: Positive autocorrelation (momentum)
    - VR ≈ 1.0: Random walk
    - VR < 0.8: Negative autocorrelation (mean-reversion)
    """
    log_returns = np.log(prices / prices.shift(1)).dropna()

    # 1-period variance
    var_1 = log_returns.var()

    variance_ratios = {}

    for lag in lags:
        # q-period returns
        q_returns = log_returns.rolling(lag).sum().dropna()

        # q-period variance
        var_q = q_returns.var()

        # Variance ratio
        vr = var_q / (lag * var_1)

        # Test statistic (under heteroskedasticity)
        n = len(log_returns)
        theta = sum([((n - k) / n)**2 for k in range(1, lag)]) * (2 * (lag - 1)) / lag

        var_vr = theta / n
        test_stat = (vr - 1) / np.sqrt(var_vr)

        # P-value (two-tailed)
        from scipy.stats import norm
        p_value = 2 * (1 - norm.cdf(abs(test_stat)))

        variance_ratios[lag] = {
            'vr': vr,
            'test_stat': test_stat,
            'p_value': p_value,
            'significant': p_value < 0.05
        }

    return variance_ratios
```

**Regime Classification**:
- **VR > 1.2** (significant): Momentum regime
- **VR 0.8-1.2**: Neutral regime
- **VR < 0.8** (significant): Mean-reversion regime

### 2.5 Regime-Conditional Percentile Behavior

**Purpose**: Empirical validation using existing percentile framework

**Methodology**:
```python
def analyze_percentile_behavior_by_regime(
    percentiles: pd.Series,
    forward_returns: pd.Series,
    regime_labels: pd.Series
):
    """
    Analyze how percentile ranks predict future returns
    in different regimes

    Key Question:
    - Momentum regime: High %ile → Higher returns?
    - Mean-reversion regime: High %ile → Lower returns?
    """
    results = {}

    for regime in ['momentum', 'mean_reversion']:
        regime_mask = regime_labels == regime

        # Bin percentiles
        percentile_bins = [0, 20, 40, 60, 80, 100]
        bin_labels = ['0-20', '20-40', '40-60', '60-80', '80-100']

        binned = pd.cut(
            percentiles[regime_mask],
            bins=percentile_bins,
            labels=bin_labels
        )

        # Calculate average forward returns by bin
        bin_performance = {}
        for bin_label in bin_labels:
            bin_mask = binned == bin_label
            returns_in_bin = forward_returns[regime_mask][bin_mask]

            bin_performance[bin_label] = {
                'mean_return': returns_in_bin.mean(),
                'median_return': returns_in_bin.median(),
                'std': returns_in_bin.std(),
                'sample_size': len(returns_in_bin),
                't_stat': returns_in_bin.mean() / (returns_in_bin.std() / np.sqrt(len(returns_in_bin)))
            }

        results[regime] = bin_performance

    return results
```

**Expected Patterns**:

**Momentum Regime**:
- Percentile 80-100 → Positive forward returns (trend continuation)
- Percentile 0-20 → Negative forward returns (downtrend continues)
- **Strategy**: Buy high percentiles, avoid low percentiles

**Mean-Reversion Regime**:
- Percentile 80-100 → Negative forward returns (overbought reversal)
- Percentile 0-20 → Positive forward returns (oversold bounce)
- **Strategy**: Buy low percentiles, avoid high percentiles

## 3. Multi-Timeframe Regime Coherence

### 3.1 Coherence Score

**Purpose**: Measure agreement between daily and 4H regime classifications

**Calculation**:
```python
def calculate_regime_coherence(
    daily_regime: str,
    hourly_4h_regime: str,
    confidence_daily: float,
    confidence_4h: float
) -> Dict:
    """
    Calculate multi-timeframe regime coherence

    Coherence Score = Agreement × (Conf_Daily × Conf_4H)

    Returns:
        - coherence_score: 0-1 (1 = perfect agreement, high confidence)
        - classification: 'high', 'medium', 'low' coherence
        - recommended_action: Trade or wait
    """
    # Check agreement
    agreement = 1.0 if daily_regime == hourly_4h_regime else 0.0

    # Combined confidence
    combined_confidence = confidence_daily * confidence_4h

    # Coherence score
    coherence_score = agreement * combined_confidence

    # Classification
    if coherence_score >= 0.7:
        classification = 'high'
        action = 'trade_with_confidence'
    elif coherence_score >= 0.4:
        classification = 'medium'
        action = 'trade_cautiously'
    else:
        classification = 'low'
        action = 'wait_for_clarity'

    return {
        'coherence_score': coherence_score,
        'classification': classification,
        'recommended_action': action,
        'daily_regime': daily_regime,
        'hourly_4h_regime': hourly_4h_regime,
        'agreement': agreement == 1.0
    }
```

### 3.2 Regime Transition Detection

**Purpose**: Identify regime changes in real-time

**Methodology**:
```python
def detect_regime_transition(
    historical_regimes: pd.Series,
    current_regime: str,
    lookback: int = 20
) -> Dict:
    """
    Detect recent regime transitions

    Signals:
    - Regime shift: Previous N bars != current regime
    - Transition stability: How long in new regime
    - False signal rate: Regime oscillation frequency
    """
    recent_regimes = historical_regimes[-lookback:]

    # Count regime occurrences in recent history
    regime_counts = recent_regimes.value_counts()
    dominant_regime = regime_counts.index[0]
    stability = regime_counts.iloc[0] / lookback

    # Detect transition
    previous_regime = historical_regimes.iloc[-2]
    is_transition = previous_regime != current_regime

    # Bars since transition
    bars_in_regime = 0
    for i in range(len(historical_regimes) - 1, -1, -1):
        if historical_regimes.iloc[i] == current_regime:
            bars_in_regime += 1
        else:
            break

    # Oscillation detection (regime flipping)
    regime_changes = (historical_regimes != historical_regimes.shift(1)).sum()
    oscillation_rate = regime_changes / len(historical_regimes)

    return {
        'current_regime': current_regime,
        'is_recent_transition': is_transition,
        'bars_in_current_regime': bars_in_regime,
        'regime_stability': stability,
        'oscillation_rate': oscillation_rate,
        'high_oscillation': oscillation_rate > 0.3  # >30% flipping
    }
```

## 4. Regime-Based Strategy Performance Assessment

### 4.1 Conditional Performance Metrics

**Purpose**: Quantify strategy edge in each regime

**Framework**:
```python
class RegimePerformanceAnalyzer:
    """
    Analyze strategy performance conditional on regime
    """

    def analyze_strategy_by_regime(
        self,
        trades: List[Dict],
        regime_history: pd.Series
    ) -> Dict:
        """
        Calculate regime-conditional performance

        Metrics:
        - Win rate by regime
        - Average return by regime
        - Sharpe ratio by regime
        - Max drawdown by regime
        """
        results = {
            'momentum': {'trades': [], 'returns': []},
            'mean_reversion': {'trades': [], 'returns': []},
            'neutral': {'trades': [], 'returns': []}
        }

        for trade in trades:
            entry_date = trade['entry_date']
            exit_date = trade['exit_date']
            trade_return = trade['return_pct']

            # Determine dominant regime during trade
            trade_regimes = regime_history[entry_date:exit_date]
            dominant_regime = trade_regimes.mode()[0]

            results[dominant_regime]['trades'].append(trade)
            results[dominant_regime]['returns'].append(trade_return)

        # Calculate metrics for each regime
        metrics = {}
        for regime, data in results.items():
            returns = np.array(data['returns'])

            if len(returns) == 0:
                continue

            metrics[regime] = {
                'sample_size': len(returns),
                'win_rate': (returns > 0).sum() / len(returns) * 100,
                'avg_return': returns.mean(),
                'median_return': np.median(returns),
                'std_return': returns.std(),
                'sharpe': returns.mean() / returns.std() if returns.std() > 0 else 0,
                'max_return': returns.max(),
                'max_loss': returns.min(),
                'total_return': returns.sum()
            }

        return metrics
```

### 4.2 Regime-Adaptive Deployment Logic

**Decision Framework**:

```python
def should_deploy_strategy(
    current_regime: str,
    regime_confidence: float,
    coherence_score: float,
    strategy_type: str,  # 'momentum' or 'mean_reversion'
    historical_performance: Dict
) -> Dict:
    """
    Decide whether to deploy strategy given current regime

    Rules:
    1. Momentum strategy → Only deploy in momentum regime
    2. Mean-reversion strategy → Only deploy in mean-reversion regime
    3. Require minimum coherence score (0.6+)
    4. Historical edge must be positive in target regime
    """
    # Rule 1: Regime alignment
    regime_aligned = current_regime == strategy_type

    # Rule 2: Coherence requirement
    sufficient_coherence = coherence_score >= 0.6

    # Rule 3: Historical edge
    regime_performance = historical_performance.get(current_regime, {})
    positive_edge = regime_performance.get('avg_return', 0) > 0.5  # >0.5% avg return

    # Rule 4: Statistical significance
    sample_size = regime_performance.get('sample_size', 0)
    sufficient_data = sample_size >= 30

    # Combined decision
    deploy = (
        regime_aligned and
        sufficient_coherence and
        positive_edge and
        sufficient_data
    )

    # Confidence level
    if deploy:
        confidence_factors = [
            regime_confidence,
            coherence_score,
            min(regime_performance.get('win_rate', 0) / 100, 1.0)
        ]
        deployment_confidence = np.mean(confidence_factors)
    else:
        deployment_confidence = 0.0

    return {
        'deploy': deploy,
        'confidence': deployment_confidence,
        'regime_aligned': regime_aligned,
        'sufficient_coherence': sufficient_coherence,
        'positive_edge': positive_edge,
        'sufficient_data': sufficient_data,
        'reason': _generate_deployment_reason(
            deploy, regime_aligned, sufficient_coherence, positive_edge, sufficient_data
        )
    }

def _generate_deployment_reason(deploy, aligned, coherence, edge, data):
    """Generate human-readable deployment reason"""
    if deploy:
        return "All criteria met - deploy with confidence"

    issues = []
    if not aligned:
        issues.append("regime misalignment")
    if not coherence:
        issues.append("low coherence")
    if not edge:
        issues.append("no historical edge")
    if not data:
        issues.append("insufficient data")

    return f"Cannot deploy: {', '.join(issues)}"
```

## 5. Integration with Existing Framework

### 5.1 Mapping to Stock Metadata

**Enhancement to `stock_statistics.py`**:

```python
@dataclass
class StockMetadata:
    # ... existing fields ...

    # NEW: Regime characteristics
    primary_regime: str  # 'momentum' or 'mean_reversion'
    regime_stability: float  # 0-1, how stable regime classification is
    regime_performance: Dict[str, float]  # Performance by regime

    # NEW: Multi-timeframe regime analysis
    daily_regime_stats: Dict
    hourly_4h_regime_stats: Dict
    coherence_average: float  # Average coherence score
```

**Example Enhancement for TSLA**:
```python
TSLA_METADATA = StockMetadata(
    # ... existing fields ...
    primary_regime='momentum',
    regime_stability=0.78,
    regime_performance={
        'momentum': 2.5,  # avg return in momentum regime
        'mean_reversion': -0.8  # avg return in mean-reversion
    },
    daily_regime_stats={
        'adx_avg': 28.5,
        'hurst_avg': 0.62,
        'autocorr_lag1': 0.22
    },
    hourly_4h_regime_stats={
        'adx_avg': 24.1,
        'hurst_avg': 0.58,
        'autocorr_lag1': 0.18
    },
    coherence_average=0.72  # High daily/4H agreement
)
```

### 5.2 Entry Signal Modification

**Current Logic**:
```python
# Existing: Entry when Daily high %ile, 4H low %ile (divergence)
if daily_percentile > 75 and hourly_4h_percentile < 35:
    enter_trade()
```

**Enhanced with Regime Detection**:
```python
def generate_entry_signal(
    daily_percentile: float,
    hourly_4h_percentile: float,
    current_regime: str,
    coherence_score: float,
    stock_metadata: StockMetadata
) -> Dict:
    """
    Enhanced entry signal with regime awareness
    """
    # Original divergence signal
    divergence = abs(daily_percentile - hourly_4h_percentile)
    has_divergence = divergence > 25

    # Regime validation
    regime_aligned = current_regime == stock_metadata.primary_regime

    # Strategy selection based on regime
    if current_regime == 'mean_reversion':
        # Original strategy works in mean-reversion regime
        entry_condition = (
            daily_percentile > 75 and
            hourly_4h_percentile < 35 and
            has_divergence and
            coherence_score > 0.6
        )
        strategy = 'divergence_mean_reversion'

    elif current_regime == 'momentum':
        # Modified for momentum: Enter on breakout confirmation
        entry_condition = (
            daily_percentile > 75 and
            hourly_4h_percentile > 60 and  # BOTH high (aligned momentum)
            coherence_score > 0.7
        )
        strategy = 'aligned_momentum'

    else:
        # Neutral regime - use strict criteria
        entry_condition = (
            has_divergence and
            coherence_score > 0.75 and
            regime_aligned
        )
        strategy = 'high_confidence_only'

    return {
        'entry_signal': entry_condition,
        'strategy': strategy,
        'regime': current_regime,
        'divergence': divergence,
        'coherence_score': coherence_score
    }
```

## 6. Recommended Implementation Architecture

### 6.1 Module Structure

```
src/framework/regime-detection/
├── __init__.py
├── indicators/
│   ├── adx.py              # ADX calculation
│   ├── hurst.py            # Hurst exponent
│   ├── autocorrelation.py  # ACF analysis
│   └── variance_ratio.py   # VR test
├── classifiers/
│   ├── regime_classifier.py  # Main classifier
│   └── confidence.py         # Confidence scoring
├── coherence/
│   ├── multi_timeframe.py    # MTF coherence
│   └── transition_detection.py
├── performance/
│   ├── regime_performance.py # Performance analysis
│   └── adaptive_deployment.py
└── integration/
    ├── signal_enhancement.py  # Entry/exit enhancement
    └── stock_metadata.py      # Metadata extension
```

### 6.2 Data Requirements

**Input Data**:
- Daily OHLCV (minimum 500 bars for Hurst calculation)
- 4H OHLCV (minimum 500 bars)
- Existing RSI-MA percentiles (daily and 4H)

**Output Data**:
- Regime classification (momentum/mean-reversion/neutral)
- Confidence score (0-1)
- Indicator values (ADX, Hurst, ρ₁, VR)
- Coherence metrics
- Deployment recommendations

## 7. Validation & Testing

### 7.1 Backtesting Protocol

1. **Historical Regime Classification**:
   - Classify each historical day into regime
   - Measure regime persistence (median duration)
   - Identify false signals (oscillation rate)

2. **Strategy Performance by Regime**:
   - Separate trades by entry regime
   - Calculate regime-conditional returns
   - Validate hypothesis: Strategy performs better in aligned regime

3. **Coherence Validation**:
   - Track coherence score at each trade entry
   - Correlate coherence with trade outcome
   - Validate: Higher coherence → better performance

### 7.2 Success Metrics

**Regime Detection Quality**:
- Regime stability: >70% of bars maintain regime for 5+ days
- Oscillation rate: <20% regime flips within 3 days
- Coherence: Daily-4H agreement >65%

**Strategy Performance**:
- Mean-reversion strategy in MR regime: >2% avg return
- Momentum strategy in momentum regime: >2% avg return
- Wrong-regime deployment: <0.5% avg return (near zero)

## 8. Future Enhancements

### 8.1 Machine Learning Integration

- **Random Forest**: Classify regimes using multiple indicators
- **Hidden Markov Models**: Detect regime transitions probabilistically
- **LSTM Networks**: Predict regime persistence

### 8.2 Additional Indicators

- **Entropy**: Market randomness measure
- **Fractal Dimension**: Complexity of price path
- **Regime-Switching Models**: Formal statistical framework

## 9. References & Literature

1. **Wilder, J. W. (1978)**. *New Concepts in Technical Trading Systems*. Trend Research. (ADX)

2. **Hurst, H. E. (1951)**. "Long-term storage capacity of reservoirs." *Transactions of the American Society of Civil Engineers*, 116, 770-799.

3. **Lo, A. W., & MacKinlay, A. C. (1988)**. "Stock market prices do not follow random walks: Evidence from a simple specification test." *The Review of Financial Studies*, 1(1), 41-66.

4. **Ljung, G. M., & Box, G. E. (1978)**. "On a measure of lack of fit in time series models." *Biometrika*, 65(2), 297-303.

5. **Fama, E. F., & French, K. R. (1988)**. "Permanent and temporary components of stock prices." *Journal of Political Economy*, 96(2), 246-273.

6. **Jegadeesh, N., & Titman, S. (1993)**. "Returns to buying winners and selling losers: Implications for stock market efficiency." *The Journal of Finance*, 48(1), 65-91.

7. **Hamilton, J. D. (1989)**. "A new approach to the economic analysis of nonstationary time series and the business cycle." *Econometrica*, 57(2), 357-384. (Regime-switching models)

---

**Document Status**: Draft v1.0
**Last Updated**: 2025-11-05
**Author**: Research Agent (Hive Mind Swarm)
**Review Status**: Pending collective consensus
