# Risk-Adjusted Expectancy Model

## Executive Summary

This document defines the mathematical framework for calculating risk-adjusted expectancy in the automated trading strategy. The model integrates win probability, potential returns, and risk-adjusted loss magnitudes to provide a robust measure of trade quality.

---

## 1. Core Expectancy Formula

### 1.1 Classical Expectancy

The traditional expectancy formula provides the baseline:

```
E = (P_win × W_avg) - (P_loss × L_avg)
```

Where:
- `E` = Expectancy per trade
- `P_win` = Probability of winning (win rate)
- `W_avg` = Average win magnitude
- `P_loss` = Probability of losing (1 - P_win)
- `L_avg` = Average loss magnitude

### 1.2 Risk-Adjusted Expectancy (RAE)

The risk-adjusted expectancy incorporates stop-loss positioning and historical volatility:

```
RAE = (P_win × W_avg) - (P_loss × L_adj × RF)
```

Where:
- `L_adj` = Risk-adjusted loss magnitude
- `RF` = Risk factor (volatility adjustment)

---

## 2. Risk-Adjusted Loss Calculation

### 2.1 Base Loss Magnitude

The base loss is determined by the stop-loss placement:

```
L_base = Entry_Price × Stop_Loss_Percentage
```

For percentile-based entries:
```
Stop_Loss_Percentage = f(Entry_Percentile, Historical_Volatility)
```

### 2.2 Volatility Adjustment Factor

The risk factor adjusts for market conditions:

```
RF = 1 + (σ_current / σ_baseline - 1) × λ
```

Where:
- `σ_current` = Current volatility (e.g., 20-day ATR)
- `σ_baseline` = Historical baseline volatility
- `λ` = Sensitivity parameter (recommended: 0.5-0.7)

### 2.3 Final Adjusted Loss

```
L_adj = L_base × Volatility_Multiplier
```

Where:
```
Volatility_Multiplier = σ_current / σ_baseline
```

---

## 3. Win Rate Estimation

### 3.1 Historical Win Rate

Based on backtested data for each entry percentile:

```
P_win(p) = Count(Wins | Entry_Percentile = p) / Count(Total_Trades | Entry_Percentile = p)
```

### 3.2 Confidence-Adjusted Win Rate

Apply confidence intervals for statistical robustness:

```
P_win_adj = P_win - (z × SE)
```

Where:
- `z` = Z-score for confidence level (e.g., 1.645 for 95% confidence)
- `SE` = Standard error = sqrt(P_win × (1 - P_win) / n)
- `n` = Sample size

---

## 4. Expected Return Components

### 4.1 Average Win Magnitude

```
W_avg = (Target_Price - Entry_Price) / Entry_Price
```

For multi-target strategies:
```
W_avg = Σ(P_target_i × Return_i)
```

Where `P_target_i` is the probability of hitting target `i`.

### 4.2 Risk-Reward Ratio

```
RR = W_avg / L_adj
```

Minimum threshold: `RR ≥ 2.0` (adjustable based on win rate)

---

## 5. Statistical Foundations

### 5.1 Assumptions

1. **Independent Trades**: Each trade outcome is independent
2. **Stationary Distributions**: Historical patterns remain relevant
3. **Normal Returns**: Win/loss distributions approximate normality (for large samples)

### 5.2 Kelly Criterion Integration

Optimal position sizing based on expectancy:

```
f* = (P_win × RR - P_loss) / RR
```

Where `f*` is the optimal fraction of capital to risk.

### 5.3 Drawdown Probability

Expected maximum drawdown:

```
DD_max ≈ (σ_returns / √E) × √(2 × ln(n))
```

Where:
- `σ_returns` = Standard deviation of returns
- `n` = Number of trades

---

## 6. Implementation Formula

### 6.1 Complete RAE Calculation

```python
def calculate_rae(entry_percentile, historical_data):
    # 1. Estimate win rate
    p_win = estimate_win_rate(entry_percentile, historical_data)
    p_loss = 1 - p_win

    # 2. Calculate average win
    w_avg = calculate_avg_win(entry_percentile, historical_data)

    # 3. Determine stop-loss percentage
    stop_loss_pct = get_stop_loss(entry_percentile, historical_data)

    # 4. Calculate base loss
    l_base = stop_loss_pct

    # 5. Apply volatility adjustment
    current_volatility = get_current_atr()
    baseline_volatility = get_baseline_atr(historical_data)
    volatility_multiplier = current_volatility / baseline_volatility

    # 6. Risk factor
    lambda_param = 0.6
    rf = 1 + (volatility_multiplier - 1) * lambda_param

    # 7. Adjusted loss
    l_adj = l_base * volatility_multiplier

    # 8. RAE calculation
    rae = (p_win * w_avg) - (p_loss * l_adj * rf)

    return rae
```

### 6.2 Confidence Bounds

```python
def calculate_rae_confidence_interval(rae, n_samples, confidence=0.95):
    # Bootstrap or analytical standard error
    se_rae = calculate_standard_error(rae, n_samples)
    z_score = get_z_score(confidence)

    lower_bound = rae - (z_score * se_rae)
    upper_bound = rae + (z_score * se_rae)

    return (lower_bound, rae, upper_bound)
```

---

## 7. Validation Metrics

### 7.1 Backtesting Requirements

- Minimum trades per percentile: `n ≥ 30`
- Out-of-sample testing: 20-30% of data
- Walk-forward analysis: Rolling windows

### 7.2 Performance Metrics

1. **Sharpe Ratio**: `SR = E / σ_returns`
2. **Sortino Ratio**: `SoR = E / σ_downside`
3. **Profit Factor**: `PF = Gross_Wins / Gross_Losses`

### 7.3 Expectancy Thresholds

- **Minimum RAE**: `RAE ≥ 0.05` (5% positive expectancy)
- **Optimal RAE**: `RAE ≥ 0.15` (15%+ for high-quality setups)
- **Risk-Reward**: `RR ≥ 2.0` (minimum 2:1 reward-to-risk)

---

## 8. Adaptive Mechanisms

### 8.1 Dynamic Threshold Adjustment

```python
def adjust_rae_threshold(market_regime):
    base_threshold = 0.05

    if market_regime == 'trending':
        return base_threshold * 0.8  # Lower threshold in trends
    elif market_regime == 'choppy':
        return base_threshold * 1.3  # Higher threshold in chop
    else:
        return base_threshold
```

### 8.2 Regime Detection

Based on ADX, ATR, and trend consistency:
- **Trending**: ADX > 25, consistent directional moves
- **Choppy**: ADX < 20, high volatility without direction
- **Neutral**: Default state

---

## 9. Risk Management Integration

### 9.1 Position Sizing

```
Position_Size = (Account_Size × Risk_Per_Trade) / (Entry_Price × Stop_Loss_Percentage)
```

With RAE adjustment:
```
Position_Size_Adjusted = Position_Size × min(RAE / RAE_baseline, 1.5)
```

Cap at 1.5x to prevent over-leveraging on high-expectancy trades.

### 9.2 Portfolio-Level Expectancy

```
Portfolio_RAE = Σ(Weight_i × RAE_i)
```

Where weights are based on capital allocation to each instrument.

---

## 10. Mathematical Proofs & Derivations

### 10.1 Expectancy Convergence

By the Law of Large Numbers:
```
lim (n→∞) Σ(Returns_i) / n = E[Returns] = RAE
```

### 10.2 Variance of Expectancy

```
Var(E) = P_win × Var(Wins) + P_loss × Var(Losses) + P_win × P_loss × (W_avg + L_avg)²
```

### 10.3 Standard Error

```
SE(E) = √(Var(E) / n)
```

---

## 11. Example Calculation

### Scenario
- Entry Percentile: 10 (oversold)
- Historical Win Rate: 65%
- Average Win: 12%
- Stop-Loss: 4%
- Current ATR: 2.5%
- Baseline ATR: 2.0%

### Step-by-Step

1. **Win/Loss Probabilities**:
   - `P_win = 0.65`
   - `P_loss = 0.35`

2. **Volatility Adjustment**:
   - `Volatility_Multiplier = 2.5 / 2.0 = 1.25`
   - `RF = 1 + (1.25 - 1) × 0.6 = 1.15`

3. **Adjusted Loss**:
   - `L_adj = 0.04 × 1.25 = 0.05` (5%)

4. **RAE Calculation**:
   - `RAE = (0.65 × 0.12) - (0.35 × 0.05 × 1.15)`
   - `RAE = 0.078 - 0.020 = 0.058` (5.8%)

5. **Risk-Reward**:
   - `RR = 0.12 / 0.05 = 2.4`

**Result**: Positive expectancy of 5.8% per trade with 2.4:1 risk-reward ratio.

---

## 12. References & Further Reading

1. Van Tharp - "Trade Your Way to Financial Freedom" (expectancy framework)
2. Kelly, J.L. - "A New Interpretation of Information Rate" (position sizing)
3. Aronson, D. - "Evidence-Based Technical Analysis" (statistical validation)
4. Pardo, R. - "The Evaluation and Optimization of Trading Strategies" (backtesting)

---

## Revision History

- **v1.0** (2025-11-05): Initial framework design
- Document Owner: Analyst Agent (Hive Mind Collective)
