# Composite Scoring System for Instrument Ranking

## Executive Summary

This document defines the composite scoring methodology for ranking trading instruments across multiple timeframes and market conditions. The system combines risk-adjusted expectancy, win rates, loss profiles, and stop-loss appropriateness into a unified score for capital allocation prioritization.

---

## 1. Composite Score Formula

### 1.1 Primary Formula

```
Composite_Score = w1 × RAE_Score + w2 × WR_Score + w3 × Loss_Score + w4 × SL_Score
```

Where:
- `RAE_Score` = Risk-Adjusted Expectancy score (0-100)
- `WR_Score` = Win Rate score (0-100)
- `Loss_Score` = Average Loss score (0-100, inverted)
- `SL_Score` = Stop-Loss appropriateness score (0-100)
- `w1, w2, w3, w4` = Component weights (sum to 1.0)

### 1.2 Recommended Weights

Based on importance hierarchy:

```python
WEIGHTS = {
    'rae': 0.45,      # 45% - Primary driver of profitability
    'win_rate': 0.25, # 25% - Consistency indicator
    'avg_loss': 0.15, # 15% - Risk control
    'stop_loss': 0.15 # 15% - Risk management quality
}
```

**Rationale**:
- RAE dominates as it directly predicts profit
- Win rate provides psychological/operational stability
- Loss metrics ensure risk is controlled
- Stop-loss quality validates risk management

---

## 2. Component Score Calculations

### 2.1 RAE Score (0-100)

Normalize risk-adjusted expectancy to 0-100 scale:

```python
def calculate_rae_score(rae, rae_min=-0.10, rae_max=0.30):
    """
    Map RAE to 0-100 scale with non-linear transformation.

    Args:
        rae: Risk-adjusted expectancy (-1.0 to 1.0 theoretical)
        rae_min: Minimum expected RAE (default -10%)
        rae_max: Maximum expected RAE (default 30%)
    """
    # Clamp to valid range
    rae_clamped = max(rae_min, min(rae, rae_max))

    # Linear normalization
    score_linear = ((rae_clamped - rae_min) / (rae_max - rae_min)) * 100

    # Apply sigmoid transformation for non-linearity
    # Emphasize high RAE, penalize negative RAE
    score = 100 / (1 + exp(-0.1 * (score_linear - 50)))

    return max(0, min(100, score))
```

**Thresholds**:
- `RAE < 0`: Score < 50 (poor)
- `RAE = 0.05`: Score ≈ 55 (marginal)
- `RAE = 0.15`: Score ≈ 75 (good)
- `RAE ≥ 0.25`: Score ≥ 90 (excellent)

### 2.2 Win Rate Score (0-100)

```python
def calculate_wr_score(win_rate, min_wr=0.30, max_wr=0.80):
    """
    Map win rate to 0-100 scale.

    Args:
        win_rate: Historical win rate (0.0 to 1.0)
        min_wr: Minimum acceptable win rate (30%)
        max_wr: Maximum realistic win rate (80%)
    """
    # Clamp to valid range
    wr_clamped = max(min_wr, min(win_rate, max_wr))

    # Linear normalization
    score = ((wr_clamped - min_wr) / (max_wr - min_wr)) * 100

    return max(0, min(100, score))
```

**Thresholds**:
- `WR < 40%`: Score < 20 (requires high RR)
- `WR = 50%`: Score = 40 (average)
- `WR = 60%`: Score = 60 (good)
- `WR ≥ 70%`: Score ≥ 80 (excellent)

### 2.3 Average Loss Score (0-100, Inverted)

Lower average losses yield higher scores:

```python
def calculate_loss_score(avg_loss, min_loss=0.02, max_loss=0.10):
    """
    Map average loss to 0-100 scale (inverted).

    Args:
        avg_loss: Average loss percentage (0.0 to 1.0)
        min_loss: Best-case loss (2%)
        max_loss: Worst-case loss (10%)
    """
    # Clamp to valid range
    loss_clamped = max(min_loss, min(avg_loss, max_loss))

    # Inverted normalization (lower loss = higher score)
    score = (1 - ((loss_clamped - min_loss) / (max_loss - min_loss))) * 100

    return max(0, min(100, score))
```

**Thresholds**:
- `Avg_Loss ≥ 8%`: Score ≤ 25 (high risk)
- `Avg_Loss = 5%`: Score ≈ 60 (acceptable)
- `Avg_Loss ≤ 3%`: Score ≥ 85 (excellent)

### 2.4 Stop-Loss Appropriateness Score (0-100)

Based on percentile-justified stop placement:

```python
def calculate_sl_score(entry_percentile, stop_loss_pct, historical_data):
    """
    Score stop-loss placement based on historical justification.

    Args:
        entry_percentile: Entry percentile (0-100)
        stop_loss_pct: Proposed stop-loss percentage
        historical_data: Historical price movements
    """
    # Get historical percentile distribution
    historical_low = get_historical_percentile_low(
        entry_percentile,
        historical_data,
        lookback_days=365
    )

    # Calculate optimal stop-loss range
    optimal_stop = abs(historical_low)
    tolerance = 0.25  # 25% tolerance

    min_stop = optimal_stop * (1 - tolerance)
    max_stop = optimal_stop * (1 + tolerance)

    # Score based on proximity to optimal
    if min_stop <= stop_loss_pct <= max_stop:
        # Within optimal range
        deviation = abs(stop_loss_pct - optimal_stop) / optimal_stop
        score = 100 * (1 - deviation)
    elif stop_loss_pct < min_stop:
        # Too tight (higher risk of premature stops)
        score = 50 * (stop_loss_pct / min_stop)
    else:
        # Too wide (excessive risk)
        score = 50 * (max_stop / stop_loss_pct)

    return max(0, min(100, score))
```

**Evaluation Criteria**:
- Historical percentile justification
- Volatility-adjusted appropriateness
- Risk-reward optimization

---

## 3. Multi-Timeframe Score Aggregation

### 3.1 Timeframe Weighting

Different timeframes carry different weights:

```python
TIMEFRAME_WEIGHTS = {
    '1h': 0.15,   # Short-term tactical
    '4h': 0.30,   # Primary decision timeframe
    '1d': 0.40,   # Strategic positioning
    '1w': 0.15    # Trend confirmation
}
```

### 3.2 Aggregated Composite Score

```python
def calculate_aggregate_score(scores_by_timeframe):
    """
    Aggregate scores across multiple timeframes.

    Args:
        scores_by_timeframe: Dict of {timeframe: composite_score}

    Returns:
        Weighted aggregate score (0-100)
    """
    aggregate_score = 0

    for timeframe, score in scores_by_timeframe.items():
        weight = TIMEFRAME_WEIGHTS.get(timeframe, 0)
        aggregate_score += score * weight

    return aggregate_score
```

### 3.3 Timeframe Consistency Bonus

Reward instruments with consistent scores across timeframes:

```python
def calculate_consistency_bonus(scores_by_timeframe):
    """
    Bonus for multi-timeframe alignment.

    Returns:
        Bonus multiplier (1.0 to 1.15)
    """
    scores = list(scores_by_timeframe.values())

    if len(scores) < 2:
        return 1.0

    # Calculate coefficient of variation
    mean_score = sum(scores) / len(scores)
    std_score = (sum((s - mean_score)**2 for s in scores) / len(scores))**0.5
    cv = std_score / mean_score if mean_score > 0 else 1.0

    # Lower CV = higher bonus
    # CV < 0.1 = 15% bonus, CV > 0.3 = no bonus
    bonus = 1.0 + max(0, (0.3 - cv) / 0.3) * 0.15

    return min(1.15, max(1.0, bonus))
```

### 3.4 Final Multi-Timeframe Score

```python
def calculate_final_score(scores_by_timeframe):
    """
    Calculate final composite score with consistency bonus.
    """
    aggregate = calculate_aggregate_score(scores_by_timeframe)
    consistency_bonus = calculate_consistency_bonus(scores_by_timeframe)

    final_score = aggregate * consistency_bonus

    return min(100, final_score)
```

---

## 4. Instrument Ranking Methodology

### 4.1 Ranking Algorithm

```python
def rank_instruments(instruments_data):
    """
    Rank instruments by composite score.

    Args:
        instruments_data: List of dicts with instrument metrics

    Returns:
        Sorted list of instruments with ranks and scores
    """
    ranked = []

    for instrument in instruments_data:
        # Calculate component scores
        rae_score = calculate_rae_score(instrument['rae'])
        wr_score = calculate_wr_score(instrument['win_rate'])
        loss_score = calculate_loss_score(instrument['avg_loss'])
        sl_score = calculate_sl_score(
            instrument['entry_percentile'],
            instrument['stop_loss'],
            instrument['historical_data']
        )

        # Composite score
        composite = (
            WEIGHTS['rae'] * rae_score +
            WEIGHTS['win_rate'] * wr_score +
            WEIGHTS['avg_loss'] * loss_score +
            WEIGHTS['stop_loss'] * sl_score
        )

        ranked.append({
            'symbol': instrument['symbol'],
            'composite_score': composite,
            'rae_score': rae_score,
            'wr_score': wr_score,
            'loss_score': loss_score,
            'sl_score': sl_score
        })

    # Sort descending by composite score
    ranked.sort(key=lambda x: x['composite_score'], reverse=True)

    # Add rank
    for i, item in enumerate(ranked):
        item['rank'] = i + 1

    return ranked
```

### 4.2 Filtering Criteria

Before ranking, apply minimum thresholds:

```python
def filter_valid_instruments(instruments_data):
    """
    Filter instruments meeting minimum criteria.
    """
    MIN_RAE = 0.05        # 5% positive expectancy
    MIN_WIN_RATE = 0.40   # 40% win rate
    MAX_AVG_LOSS = 0.08   # 8% max average loss
    MIN_SAMPLE_SIZE = 30  # Minimum historical trades

    valid = []

    for instrument in instruments_data:
        if (instrument['rae'] >= MIN_RAE and
            instrument['win_rate'] >= MIN_WIN_RATE and
            instrument['avg_loss'] <= MAX_AVG_LOSS and
            instrument['sample_size'] >= MIN_SAMPLE_SIZE):
            valid.append(instrument)

    return valid
```

---

## 5. Capital Allocation Logic

### 5.1 Score-Based Allocation

Allocate capital proportional to composite scores:

```python
def allocate_capital(ranked_instruments, total_capital, max_positions=10):
    """
    Allocate capital based on composite scores.

    Args:
        ranked_instruments: Sorted list of instruments
        total_capital: Total available capital
        max_positions: Maximum concurrent positions

    Returns:
        Dict of {symbol: allocated_capital}
    """
    # Take top N instruments
    top_instruments = ranked_instruments[:max_positions]

    # Calculate total score
    total_score = sum(inst['composite_score'] for inst in top_instruments)

    # Allocate proportionally
    allocations = {}

    for instrument in top_instruments:
        weight = instrument['composite_score'] / total_score
        allocation = total_capital * weight

        allocations[instrument['symbol']] = {
            'capital': allocation,
            'weight': weight,
            'composite_score': instrument['composite_score'],
            'rank': instrument['rank']
        }

    return allocations
```

### 5.2 Risk-Adjusted Position Sizing

Integrate Kelly Criterion:

```python
def calculate_position_size(allocation, rae, win_rate, avg_loss):
    """
    Calculate position size using Kelly Criterion.

    Args:
        allocation: Allocated capital for instrument
        rae: Risk-adjusted expectancy
        win_rate: Historical win rate
        avg_loss: Average loss percentage

    Returns:
        Position size in units
    """
    # Kelly fraction
    rr = calculate_risk_reward(rae, win_rate, avg_loss)
    kelly_fraction = (win_rate * rr - (1 - win_rate)) / rr

    # Apply fractional Kelly (25% Kelly for safety)
    conservative_fraction = kelly_fraction * 0.25

    # Cap at 5% of allocation per trade
    max_fraction = 0.05
    final_fraction = min(conservative_fraction, max_fraction)

    # Position size
    risk_amount = allocation * final_fraction
    position_size = risk_amount / avg_loss

    return position_size
```

---

## 6. Score Normalization

### 6.1 Z-Score Normalization

For statistical comparability:

```python
def normalize_scores_zscore(scores):
    """
    Normalize scores using Z-score method.

    Returns:
        Normalized scores (mean=0, std=1)
    """
    mean = sum(scores) / len(scores)
    variance = sum((s - mean)**2 for s in scores) / len(scores)
    std = variance ** 0.5

    if std == 0:
        return [0] * len(scores)

    normalized = [(s - mean) / std for s in scores]

    return normalized
```

### 6.2 Min-Max Normalization

For 0-100 scaling:

```python
def normalize_scores_minmax(scores, target_min=0, target_max=100):
    """
    Normalize scores to target range.
    """
    min_score = min(scores)
    max_score = max(scores)

    if max_score == min_score:
        return [target_min] * len(scores)

    normalized = [
        target_min + ((s - min_score) / (max_score - min_score)) * (target_max - target_min)
        for s in scores
    ]

    return normalized
```

---

## 7. Dynamic Weight Adjustment

### 7.1 Market Regime Adaptation

Adjust weights based on market conditions:

```python
def adjust_weights_by_regime(market_regime):
    """
    Adapt component weights to market regime.

    Args:
        market_regime: 'trending', 'choppy', or 'neutral'

    Returns:
        Adjusted weights dict
    """
    if market_regime == 'trending':
        # Favor higher RAE in trends
        return {
            'rae': 0.50,
            'win_rate': 0.20,
            'avg_loss': 0.15,
            'stop_loss': 0.15
        }
    elif market_regime == 'choppy':
        # Favor win rate and tight stops in chop
        return {
            'rae': 0.35,
            'win_rate': 0.35,
            'avg_loss': 0.15,
            'stop_loss': 0.15
        }
    else:  # neutral
        # Balanced default
        return {
            'rae': 0.45,
            'win_rate': 0.25,
            'avg_loss': 0.15,
            'stop_loss': 0.15
        }
```

### 7.2 Performance-Based Tuning

Optimize weights based on backtest performance:

```python
def optimize_weights(historical_performance, metric='sharpe_ratio'):
    """
    Optimize component weights using grid search.

    Args:
        historical_performance: DataFrame with performance metrics
        metric: Optimization target (sharpe_ratio, total_return, etc.)

    Returns:
        Optimal weights dict
    """
    from itertools import product

    # Grid search space
    weight_grid = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]

    best_weights = None
    best_metric = -float('inf')

    # Search all valid combinations (sum to 1.0)
    for w1, w2, w3, w4 in product(weight_grid, repeat=4):
        if abs(w1 + w2 + w3 + w4 - 1.0) < 0.01:  # Tolerance
            weights = {'rae': w1, 'win_rate': w2, 'avg_loss': w3, 'stop_loss': w4}

            # Simulate with these weights
            performance = simulate_with_weights(weights, historical_performance)

            if performance[metric] > best_metric:
                best_metric = performance[metric]
                best_weights = weights

    return best_weights
```

---

## 8. Validation & Backtesting

### 8.1 Walk-Forward Optimization

```python
def walk_forward_validation(data, train_period=252, test_period=63):
    """
    Validate scoring system with walk-forward analysis.

    Args:
        data: Historical data
        train_period: Training window (days)
        test_period: Testing window (days)

    Returns:
        Performance metrics across all test periods
    """
    results = []

    for start in range(0, len(data) - train_period - test_period, test_period):
        # Training window
        train_data = data[start:start + train_period]

        # Optimize weights on training data
        weights = optimize_weights(train_data)

        # Test window
        test_data = data[start + train_period:start + train_period + test_period]

        # Apply weights to test period
        performance = simulate_with_weights(weights, test_data)

        results.append({
            'train_start': start,
            'test_start': start + train_period,
            'weights': weights,
            'performance': performance
        })

    return results
```

### 8.2 Monte Carlo Simulation

```python
def monte_carlo_validation(ranked_instruments, n_simulations=1000):
    """
    Validate ranking stability with Monte Carlo simulation.

    Returns:
        Ranking stability metrics
    """
    rank_distributions = {inst['symbol']: [] for inst in ranked_instruments}

    for _ in range(n_simulations):
        # Add noise to scores
        noisy_instruments = []

        for inst in ranked_instruments:
            noise = random.gauss(0, 5)  # 5-point standard deviation
            noisy_score = inst['composite_score'] + noise

            noisy_instruments.append({
                'symbol': inst['symbol'],
                'composite_score': max(0, min(100, noisy_score))
            })

        # Re-rank
        noisy_instruments.sort(key=lambda x: x['composite_score'], reverse=True)

        # Record ranks
        for i, inst in enumerate(noisy_instruments):
            rank_distributions[inst['symbol']].append(i + 1)

    # Calculate stability metrics
    stability = {}

    for symbol, ranks in rank_distributions.items():
        stability[symbol] = {
            'mean_rank': sum(ranks) / len(ranks),
            'std_rank': (sum((r - sum(ranks)/len(ranks))**2 for r in ranks) / len(ranks))**0.5,
            'rank_range': (min(ranks), max(ranks))
        }

    return stability
```

---

## 9. Output Format

### 9.1 Ranked Instrument Output

```json
{
  "timestamp": "2025-11-05T21:30:00Z",
  "market_regime": "trending",
  "total_instruments": 50,
  "qualified_instruments": 23,
  "top_ranked": [
    {
      "rank": 1,
      "symbol": "BTCUSD",
      "composite_score": 87.3,
      "components": {
        "rae_score": 92.1,
        "win_rate_score": 78.5,
        "avg_loss_score": 85.0,
        "stop_loss_score": 88.9
      },
      "metrics": {
        "rae": 0.18,
        "win_rate": 0.64,
        "avg_loss": 0.035,
        "risk_reward": 2.8
      },
      "allocation": {
        "capital": 15000,
        "weight": 0.12,
        "position_size": 0.42
      }
    },
    {
      "rank": 2,
      "symbol": "ETHUSD",
      "composite_score": 82.7,
      "...": "..."
    }
  ]
}
```

---

## 10. Monitoring & Alerts

### 10.1 Score Degradation Detection

```python
def detect_score_degradation(current_scores, historical_scores, threshold=0.15):
    """
    Alert if composite scores degrade significantly.

    Args:
        current_scores: Dict of current instrument scores
        historical_scores: Historical average scores
        threshold: Degradation threshold (15%)

    Returns:
        List of degraded instruments
    """
    degraded = []

    for symbol, current_score in current_scores.items():
        historical_avg = historical_scores.get(symbol, current_score)

        degradation = (historical_avg - current_score) / historical_avg

        if degradation > threshold:
            degraded.append({
                'symbol': symbol,
                'current_score': current_score,
                'historical_avg': historical_avg,
                'degradation_pct': degradation * 100
            })

    return degraded
```

---

## 11. References

1. Markowitz, H. - "Portfolio Selection" (Modern Portfolio Theory)
2. Sharpe, W. - "Capital Asset Prices" (Risk-adjusted returns)
3. Faber, M. - "A Quantitative Approach to Tactical Asset Allocation"
4. Pardo, R. - "The Evaluation and Optimization of Trading Strategies"

---

## Revision History

- **v1.0** (2025-11-05): Initial scoring framework design
- Document Owner: Analyst Agent (Hive Mind Collective)
