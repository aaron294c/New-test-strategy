# Percentile-Based Stop-Loss Design Framework

## Executive Summary

This document defines the adaptive stop-loss placement methodology using percentile-based historical analysis. The framework determines appropriate stop-loss levels by analyzing historical price movements relative to entry percentiles, ensuring statistically justified risk management.

---

## 1. Core Concept

### 1.1 Percentile-to-Stop Mapping Philosophy

**Principle**: Stop-loss placement should be based on historical probability of adverse price movement from a given entry percentile.

```
Entry at 10th percentile (oversold) → Historical analysis of lowest dips
Entry at 90th percentile (overbought) → Historical analysis of highest peaks
```

**Goal**: Place stops beyond normal retracement range, validated by historical data.

---

## 2. Historical Percentile Analysis

### 2.1 Data Collection Requirements

```python
def collect_percentile_history(symbol, lookback_days=365, timeframe='1d'):
    """
    Collect historical price movements after percentile entries.

    Args:
        symbol: Trading instrument
        lookback_days: Historical window (365 days recommended)
        timeframe: Data granularity

    Returns:
        DataFrame with percentile entry data
    """
    historical_data = []

    for date in get_trading_days(lookback_days):
        # Calculate RSI percentile for this date
        rsi_percentile = calculate_rsi_percentile(symbol, date, lookback=365)

        # Track subsequent price movement
        entry_price = get_close_price(symbol, date)

        # Measure lowest low in next N days
        future_lows = []
        for days_ahead in range(1, 21):  # 20-day forward window
            future_date = date + timedelta(days=days_ahead)
            low_price = get_low_price(symbol, future_date)

            pct_decline = (low_price - entry_price) / entry_price
            future_lows.append({
                'days_ahead': days_ahead,
                'pct_decline': pct_decline,
                'low_price': low_price
            })

        historical_data.append({
            'date': date,
            'entry_percentile': rsi_percentile,
            'entry_price': entry_price,
            'future_lows': future_lows,
            'worst_decline': min(fl['pct_decline'] for fl in future_lows)
        })

    return pd.DataFrame(historical_data)
```

### 2.2 Percentile Grouping

Group historical data into percentile buckets:

```python
def group_by_percentile_buckets(historical_data, bucket_size=10):
    """
    Group entries by percentile buckets (0-10, 10-20, etc.).

    Returns:
        Dict of {percentile_range: [entries]}
    """
    buckets = {}

    for i in range(0, 100, bucket_size):
        bucket_key = f"{i}-{i+bucket_size}"

        # Filter entries in this percentile range
        bucket_data = historical_data[
            (historical_data['entry_percentile'] >= i) &
            (historical_data['entry_percentile'] < i + bucket_size)
        ]

        buckets[bucket_key] = bucket_data

    return buckets
```

---

## 3. Stop-Loss Calculation Methodology

### 3.1 Statistical Stop Placement

Use percentile distribution of historical declines:

```python
def calculate_stop_loss_percentile_based(
    entry_percentile,
    historical_data,
    confidence_level=0.90,
    days_horizon=10
):
    """
    Calculate stop-loss based on historical percentile distribution.

    Args:
        entry_percentile: Current entry percentile (0-100)
        historical_data: Historical decline data
        confidence_level: Confidence level for stop (90% = 10th percentile of declines)
        days_horizon: Time horizon for adverse movement

    Returns:
        Stop-loss percentage (negative value)
    """
    # Get bucket for this entry percentile
    bucket_start = (entry_percentile // 10) * 10
    bucket_key = f"{bucket_start}-{bucket_start + 10}"

    # Filter historical entries in this bucket
    bucket_data = historical_data[
        (historical_data['entry_percentile'] >= bucket_start) &
        (historical_data['entry_percentile'] < bucket_start + 10)
    ]

    if len(bucket_data) < 20:
        # Insufficient data, use conservative default
        return -0.05  # 5% stop-loss

    # Extract worst declines within days_horizon
    declines = []
    for _, row in bucket_data.iterrows():
        future_lows = row['future_lows']
        relevant_lows = [fl['pct_decline'] for fl in future_lows
                         if fl['days_ahead'] <= days_horizon]

        if relevant_lows:
            declines.append(min(relevant_lows))

    # Calculate percentile of declines
    # confidence_level=0.90 means 90% of historical declines were less severe
    stop_loss_pct = np.percentile(declines, (1 - confidence_level) * 100)

    # Add buffer (e.g., 20% additional room)
    buffer_factor = 1.20
    stop_loss_buffered = stop_loss_pct * buffer_factor

    # Cap at reasonable limits
    max_stop = -0.10  # 10% max stop
    min_stop = -0.02  # 2% min stop

    stop_loss_final = max(max_stop, min(min_stop, stop_loss_buffered))

    return stop_loss_final
```

### 3.2 Volatility-Adjusted Stops

Adjust for current market volatility:

```python
def adjust_stop_for_volatility(
    base_stop,
    current_atr,
    baseline_atr,
    max_adjustment=1.5
):
    """
    Adjust stop-loss for current volatility vs historical baseline.

    Args:
        base_stop: Base stop-loss from percentile analysis
        current_atr: Current ATR (Average True Range)
        baseline_atr: Historical baseline ATR
        max_adjustment: Maximum adjustment factor

    Returns:
        Volatility-adjusted stop-loss
    """
    volatility_ratio = current_atr / baseline_atr

    # Widen stops in high volatility, tighten in low volatility
    adjustment_factor = min(volatility_ratio, max_adjustment)

    adjusted_stop = base_stop * adjustment_factor

    return adjusted_stop
```

### 3.3 Time-Based Stop Evolution

Stops can tighten as trade matures:

```python
def calculate_time_based_stop(
    initial_stop,
    days_in_trade,
    target_profit_level,
    current_profit
):
    """
    Tighten stop-loss as trade progresses.

    Args:
        initial_stop: Initial stop-loss percentage
        days_in_trade: Days since entry
        target_profit_level: Target profit (e.g., 0.10 for 10%)
        current_profit: Current unrealized profit

    Returns:
        Time-adjusted stop-loss
    """
    # After 5 days, start tightening
    if days_in_trade < 5:
        return initial_stop

    # Calculate profit progress
    profit_progress = current_profit / target_profit_level if target_profit_level > 0 else 0

    # Tighten stop proportionally
    # 50% profit → move stop to breakeven
    # 75% profit → move stop to +3%
    # 100% profit → move stop to +5%

    if profit_progress >= 1.0:
        # At target, protect 50% of profit
        new_stop = current_profit * 0.5
    elif profit_progress >= 0.75:
        # 75% to target, protect 25% of profit
        new_stop = current_profit * 0.25
    elif profit_progress >= 0.50:
        # 50% to target, move to breakeven
        new_stop = 0.0
    else:
        # Less than 50%, keep initial stop
        new_stop = initial_stop

    # Never widen stops
    return max(new_stop, initial_stop)
```

---

## 4. Percentile-Specific Stop Logic

### 4.1 Oversold Entries (Percentile 0-20)

```python
def calculate_oversold_stop(entry_percentile, historical_data):
    """
    Stop-loss for oversold entries (mean reversion trades).

    Strategy: Wider stops, expecting bounce from support.
    """
    # Use 85% confidence (allow for deeper dips)
    base_stop = calculate_stop_loss_percentile_based(
        entry_percentile,
        historical_data,
        confidence_level=0.85,  # Lower confidence = wider stop
        days_horizon=10
    )

    # Oversold entries need room for capitulation
    buffer_factor = 1.3  # 30% additional buffer

    return base_stop * buffer_factor
```

### 4.2 Mid-Range Entries (Percentile 30-70)

```python
def calculate_midrange_stop(entry_percentile, historical_data):
    """
    Stop-loss for mid-range entries (trend-following trades).

    Strategy: Moderate stops, respecting trend support.
    """
    # Use 90% confidence (standard)
    base_stop = calculate_stop_loss_percentile_based(
        entry_percentile,
        historical_data,
        confidence_level=0.90,
        days_horizon=10
    )

    # Standard buffer
    buffer_factor = 1.2  # 20% additional buffer

    return base_stop * buffer_factor
```

### 4.3 Overbought Entries (Percentile 80-100)

```python
def calculate_overbought_stop(entry_percentile, historical_data):
    """
    Stop-loss for overbought entries (momentum/breakout trades).

    Strategy: Tighter stops, quick invalidation if momentum fails.
    """
    # Use 92% confidence (tighter stops)
    base_stop = calculate_stop_loss_percentile_based(
        entry_percentile,
        historical_data,
        confidence_level=0.92,  # Higher confidence = tighter stop
        days_horizon=7  # Shorter horizon
    )

    # Minimal buffer for momentum trades
    buffer_factor = 1.1  # 10% additional buffer

    return base_stop * buffer_factor
```

---

## 5. Multi-Timeframe Stop Integration

### 5.1 Hierarchical Stop Selection

```python
def select_hierarchical_stop(entry_percentile, historical_data_by_tf):
    """
    Select stop-loss considering multiple timeframes.

    Args:
        entry_percentile: Entry percentile on primary timeframe
        historical_data_by_tf: Dict of {timeframe: historical_data}

    Returns:
        Final stop-loss percentage
    """
    stops = {}

    # Calculate stop for each timeframe
    for timeframe, data in historical_data_by_tf.items():
        stops[timeframe] = calculate_stop_loss_percentile_based(
            entry_percentile,
            data,
            confidence_level=0.90
        )

    # Use widest stop (most conservative)
    # Protects against whipsaws on lower timeframes
    final_stop = min(stops.values())  # Most negative = widest

    return final_stop
```

### 5.2 Timeframe-Specific Adjustments

```python
def adjust_stop_by_timeframe(base_stop, timeframe):
    """
    Adjust stop-loss based on timeframe characteristics.

    Args:
        base_stop: Base stop-loss from percentile analysis
        timeframe: Trading timeframe (1h, 4h, 1d, etc.)

    Returns:
        Timeframe-adjusted stop-loss
    """
    TIMEFRAME_MULTIPLIERS = {
        '1h': 0.7,   # Tighter stops for intraday
        '4h': 0.85,  # Moderate stops
        '1d': 1.0,   # Full stops for daily
        '1w': 1.2    # Wider stops for weekly
    }

    multiplier = TIMEFRAME_MULTIPLIERS.get(timeframe, 1.0)

    return base_stop * multiplier
```

---

## 6. Dynamic Stop-Loss Adjustment

### 6.1 Trailing Stop Logic

```python
def calculate_trailing_stop(
    entry_price,
    current_price,
    highest_price,
    initial_stop_pct,
    trail_activation=0.05,  # Start trailing at 5% profit
    trail_distance=0.03     # Trail 3% below high
):
    """
    Calculate trailing stop-loss.

    Args:
        entry_price: Entry price
        current_price: Current market price
        highest_price: Highest price since entry
        initial_stop_pct: Initial stop-loss percentage
        trail_activation: Profit level to activate trailing
        trail_distance: Distance to trail below high

    Returns:
        Current stop-loss price
    """
    # Initial stop price
    initial_stop_price = entry_price * (1 + initial_stop_pct)

    # Current profit
    current_profit = (current_price - entry_price) / entry_price

    if current_profit < trail_activation:
        # Not profitable enough to trail
        return initial_stop_price

    # Calculate trailing stop
    trailing_stop_price = highest_price * (1 - trail_distance)

    # Use higher of initial or trailing stop (never widen)
    final_stop_price = max(initial_stop_price, trailing_stop_price)

    return final_stop_price
```

### 6.2 Support-Based Stop Adjustment

```python
def adjust_stop_to_support(
    calculated_stop,
    entry_price,
    support_levels,
    min_distance=0.01  # Minimum 1% below support
):
    """
    Adjust stop-loss to sit below nearest support level.

    Args:
        calculated_stop: Stop-loss from percentile calculation
        entry_price: Entry price
        support_levels: List of support price levels
        min_distance: Minimum distance below support

    Returns:
        Support-adjusted stop-loss percentage
    """
    # Find nearest support below entry
    supports_below = [s for s in support_levels if s < entry_price]

    if not supports_below:
        return calculated_stop

    nearest_support = max(supports_below)

    # Calculate stop below support
    support_stop = nearest_support * (1 - min_distance)
    support_stop_pct = (support_stop - entry_price) / entry_price

    # Use wider of calculated or support-based stop
    # (Never tighten stop to support if calculated is already wider)
    final_stop = min(calculated_stop, support_stop_pct)

    return final_stop
```

---

## 7. Stop-Loss Validation

### 7.1 Historical Effectiveness Testing

```python
def validate_stop_effectiveness(
    stop_loss_pct,
    entry_percentile,
    historical_data,
    min_survival_rate=0.85
):
    """
    Validate stop-loss would have avoided excessive whipsaws.

    Args:
        stop_loss_pct: Proposed stop-loss percentage
        entry_percentile: Entry percentile
        historical_data: Historical price data
        min_survival_rate: Minimum acceptable survival rate (85%)

    Returns:
        Validation result with metrics
    """
    bucket_data = filter_percentile_bucket(entry_percentile, historical_data)

    stopped_out = 0
    survived = 0

    for _, row in bucket_data.iterrows():
        worst_decline = row['worst_decline']

        if worst_decline < stop_loss_pct:
            stopped_out += 1
        else:
            survived += 1

    total = stopped_out + survived
    survival_rate = survived / total if total > 0 else 0

    is_valid = survival_rate >= min_survival_rate

    return {
        'is_valid': is_valid,
        'survival_rate': survival_rate,
        'stopped_out': stopped_out,
        'survived': survived,
        'total_trades': total
    }
```

### 7.2 Risk-Reward Compatibility

```python
def validate_rr_compatibility(
    stop_loss_pct,
    target_profit_pct,
    min_rr_ratio=2.0
):
    """
    Ensure stop-loss is compatible with target profit for desired RR.

    Args:
        stop_loss_pct: Proposed stop-loss (negative)
        target_profit_pct: Target profit (positive)
        min_rr_ratio: Minimum risk-reward ratio (2.0 standard)

    Returns:
        Validation result
    """
    actual_rr = abs(target_profit_pct / stop_loss_pct)

    is_valid = actual_rr >= min_rr_ratio

    return {
        'is_valid': is_valid,
        'actual_rr': actual_rr,
        'required_rr': min_rr_ratio,
        'stop_loss_pct': stop_loss_pct,
        'target_profit_pct': target_profit_pct
    }
```

---

## 8. Implementation Example

### 8.1 Complete Stop-Loss Calculation

```python
def calculate_final_stop_loss(
    symbol,
    entry_percentile,
    entry_price,
    timeframe='1d',
    lookback_days=365
):
    """
    Complete stop-loss calculation with all adjustments.

    Returns:
        Dict with stop-loss details
    """
    # 1. Collect historical data
    historical_data = collect_percentile_history(
        symbol,
        lookback_days,
        timeframe
    )

    # 2. Calculate base stop from percentile
    base_stop = calculate_stop_loss_percentile_based(
        entry_percentile,
        historical_data,
        confidence_level=0.90,
        days_horizon=10
    )

    # 3. Adjust for volatility
    current_atr = get_current_atr(symbol, timeframe, period=14)
    baseline_atr = get_baseline_atr(historical_data)

    volatility_adjusted_stop = adjust_stop_for_volatility(
        base_stop,
        current_atr,
        baseline_atr
    )

    # 4. Apply timeframe adjustment
    timeframe_adjusted_stop = adjust_stop_by_timeframe(
        volatility_adjusted_stop,
        timeframe
    )

    # 5. Check support levels
    support_levels = identify_support_levels(symbol, timeframe)

    final_stop = adjust_stop_to_support(
        timeframe_adjusted_stop,
        entry_price,
        support_levels
    )

    # 6. Validate
    validation = validate_stop_effectiveness(
        final_stop,
        entry_percentile,
        historical_data
    )

    rr_validation = validate_rr_compatibility(
        final_stop,
        target_profit_pct=0.10,  # Example 10% target
        min_rr_ratio=2.0
    )

    # 7. Calculate stop price
    stop_price = entry_price * (1 + final_stop)

    return {
        'symbol': symbol,
        'entry_percentile': entry_percentile,
        'entry_price': entry_price,
        'stop_loss_pct': final_stop,
        'stop_price': stop_price,
        'base_stop': base_stop,
        'adjustments': {
            'volatility': volatility_adjusted_stop - base_stop,
            'timeframe': timeframe_adjusted_stop - volatility_adjusted_stop,
            'support': final_stop - timeframe_adjusted_stop
        },
        'validation': validation,
        'rr_validation': rr_validation,
        'current_atr': current_atr,
        'baseline_atr': baseline_atr
    }
```

---

## 9. Monitoring & Alerts

### 9.1 Stop Hit Analysis

```python
def analyze_stop_hits(trade_history):
    """
    Analyze historical stop-loss hits to improve methodology.

    Returns:
        Analysis metrics
    """
    stop_hits = [t for t in trade_history if t['exit_reason'] == 'stop_loss']

    total_stops = len(stop_hits)

    # Categorize stop hits
    premature_stops = []  # Stopped, then rallied to target
    justified_stops = []  # Stopped, continued adverse

    for trade in stop_hits:
        # Check if price rallied back after stop
        post_stop_high = get_high_after_stop(trade, days=10)

        if post_stop_high >= trade['target_price']:
            premature_stops.append(trade)
        else:
            justified_stops.append(trade)

    return {
        'total_stops': total_stops,
        'premature_stops': len(premature_stops),
        'justified_stops': len(justified_stops),
        'premature_rate': len(premature_stops) / total_stops if total_stops > 0 else 0,
        'avg_loss_on_stop': np.mean([t['loss_pct'] for t in stop_hits])
    }
```

---

## 10. Advanced Features

### 10.1 Machine Learning Stop Optimization

```python
def ml_optimize_stops(historical_data, features):
    """
    Use ML to optimize stop placement based on multiple features.

    Features:
        - Entry percentile
        - ATR
        - Volatility regime
        - Market phase (bull/bear)
        - Sector momentum

    Returns:
        Optimized stop-loss model
    """
    from sklearn.ensemble import RandomForestRegressor

    # Prepare training data
    X = prepare_features(historical_data, features)
    y = historical_data['optimal_stop']  # Backtested optimal stops

    # Train model
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42
    )

    model.fit(X, y)

    return model
```

### 10.2 Adaptive Stop Tightening

```python
def adaptive_stop_tightening(
    trade,
    current_price,
    volatility_regime,
    days_in_trade
):
    """
    Adaptively tighten stops based on multiple factors.

    Rules:
        - Volatility expansion → widen stops
        - Volatility contraction → tighten stops
        - Time decay → gradually tighten
        - Profit milestone → lock in gains
    """
    base_stop = trade['initial_stop']

    # Volatility adjustment
    if volatility_regime == 'expanding':
        vol_factor = 1.2
    elif volatility_regime == 'contracting':
        vol_factor = 0.9
    else:
        vol_factor = 1.0

    # Time decay factor
    time_factor = 1.0 - (days_in_trade / 30) * 0.2  # Tighten 20% over 30 days

    # Combined adjustment
    adjusted_stop = base_stop * vol_factor * time_factor

    # Apply trailing logic
    trailing_stop = calculate_trailing_stop(
        trade['entry_price'],
        current_price,
        trade['highest_price'],
        adjusted_stop
    )

    return max(adjusted_stop, trailing_stop)
```

---

## 11. Output Format

### 11.1 Stop-Loss Specification

```json
{
  "symbol": "BTCUSD",
  "entry_percentile": 15,
  "entry_price": 42500,
  "entry_date": "2025-11-05",
  "stop_loss": {
    "percentage": -0.045,
    "price": 40588,
    "type": "percentile_based",
    "confidence_level": 0.90,
    "validation": {
      "historical_survival_rate": 0.87,
      "total_historical_trades": 45,
      "risk_reward_ratio": 2.67
    }
  },
  "adjustments": {
    "base_stop": -0.038,
    "volatility_adjustment": -0.005,
    "timeframe_adjustment": 0,
    "support_adjustment": -0.002
  },
  "trailing_parameters": {
    "activation_profit": 0.05,
    "trail_distance": 0.03,
    "current_trailing_stop": null
  },
  "market_context": {
    "current_atr": 1850,
    "baseline_atr": 1620,
    "volatility_regime": "normal",
    "nearest_support": 40200
  }
}
```

---

## 12. References

1. Kaufman, P. - "Trading Systems and Methods" (adaptive stops)
2. Elder, A. - "The New Trading for a Living" (stop-loss psychology)
3. Pardo, R. - "Design, Testing, and Optimization of Trading Systems" (statistical validation)
4. Aronson, D. - "Evidence-Based Technical Analysis" (percentile analysis)

---

## Revision History

- **v1.0** (2025-11-05): Initial percentile-based stop-loss framework
- Document Owner: Analyst Agent (Hive Mind Collective)
