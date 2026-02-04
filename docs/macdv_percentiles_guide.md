# MACD-V Percentiles Implementation Guide

## Executive Summary

This guide documents the implementation of **categorical percentiles for MACD-V**, addressing the question: "Should we include percentiles for MACD-V similar to RSI-MA?"

**Answer:** ✅ **Yes, but with a zone-based categorical approach** that respects MACD-V's inherent market regime structure.

---

## Distribution Analysis Results

### Key Findings (2-year analysis, 9 major tickers):

```
Total samples: 4,284 MACD-V values

Basic Statistics:
  Min:    -165.78
  Max:    247.50
  Mean:   34.38 (bullish skew!)
  Median: 34.06
  Std:    73.49

Percentiles:
   1st:  -120.89
   5th:   -89.01
  25th:   -18.31
  50th:    34.06
  75th:    89.28
  95th:   151.43
  99th:   194.87

Key Observations:
✓ 94.58% of values fall within -150 to +150 (your intuition was correct!)
✓ 76.28% of values fall within -100 to +100
✓ 43.88% of values fall within -50 to +50 (ranging zone)
```

### Value Distribution:

| Range | Count | % of Total | Interpretation |
|-------|-------|------------|----------------|
| < -150 | 8 | 0.19% | Extremely bearish (rare) |
| -150 to -100 | 130 | 3.03% | Extreme bearish |
| -100 to -50 | 478 | 11.16% | Strong bearish |
| -50 to 0 | 749 | 17.48% | Weak bearish/ranging |
| 0 to +50 | 1,131 | 26.40% | Weak bullish/ranging |
| +50 to +100 | 910 | 21.24% | Strong bullish |
| +100 to +150 | 654 | 15.27% | Extreme bullish |
| > +150 | 224 | 5.23% | Extremely bullish |

---

## Why Categorical Percentiles?

### Problem with Simple Global Percentiles:
- MACD-V already has **meaningful absolute levels** (the zones: -50, +50, -100, +100, -150, +150)
- A global percentile treats ranging and trending values the same way
- Loses information about the market regime

### Solution: Categorical (Zone-Based) Percentiles:
- Calculate percentile ranks **WITHIN each market regime zone**
- Provides **relative strength within the current regime**
- Combines:
  - **Absolute level** (which zone you're in)
  - **Relative position** (percentile within that zone)

### Zone Structure:

```python
ZONES = [
    ("extreme_bearish", -∞, -100),    # Very rare, severe downtrends
    ("strong_bearish", -100, -50),     # Strong downtrend
    ("weak_bearish", -50, 0),          # Weak downtrend/ranging
    ("weak_bullish", 0, 50),           # Weak uptrend/ranging
    ("strong_bullish", 50, 100),       # Strong uptrend
    ("extreme_bullish", 100, +∞),      # Very strong uptrend
]
```

---

## Implementation

### Basic Usage:

```python
from macdv_percentile_calculator import MACDVPercentileCalculator
import yfinance as yf

# Initialize calculator
calculator = MACDVPercentileCalculator(
    fast_length=12,
    slow_length=26,
    signal_length=9,
    atr_length=26,
    percentile_lookback=252  # 1 year
)

# Fetch data
df = yf.download("AAPL", period="1y", interval="1d")

# Calculate MACD-V with percentiles (categorical method recommended)
result = calculator.calculate_macdv_with_percentiles(df, method="categorical")

# Access results
print(f"MACD-V Value: {result['macdv_val'].iloc[-1]:.2f}")
print(f"Zone: {result['macdv_zone'].iloc[-1]}")
print(f"Percentile: {result['macdv_percentile'].iloc[-1]:.2f}%")
```

### Available Methods:

1. **`"categorical"`** (RECOMMENDED):
   - Percentile within the current zone
   - Example: MACD-V = 75, Zone = strong_bullish (50-100)
   - 80th percentile = top 20% of values in the 50-100 zone historically

2. **`"global"`** (SIMPLER):
   - Percentile across all MACD-V values
   - Example: MACD-V = 75
   - 80th percentile = higher than 80% of all historical values
   - Easier to implement but less regime-aware

3. **`"asymmetric"`** (COMPLEX):
   - Separate percentiles for bullish (≥0) and bearish (<0)
   - Example: MACD-V = 75 (bullish regime)
   - 60th percentile = higher than 60% of bullish values
   - Good for directional analysis

---

## Integration with Band Analysis

### Combining MACD-V Percentiles with RSI-MA Percentiles:

```python
from macdv_percentile_calculator import MACDVPercentileCalculator
from enhanced_backtester import EnhancedPerformanceMatrixBacktester

# Setup
macdv_calc = MACDVPercentileCalculator(percentile_lookback=252)
rsi_backtester = EnhancedPerformanceMatrixBacktester(
    tickers=["AAPL"],
    lookback_period=252
)

# Get data
data = rsi_backtester.fetch_data("AAPL", period="2y")

# Calculate both indicators
df = macdv_calc.calculate_macdv_with_percentiles(data, method="categorical")
rsi_ma = rsi_backtester.calculate_rsi_ma_indicator(data)
rsi_pct = rsi_backtester.calculate_percentile_ranks(rsi_ma)

df['rsi_percentile'] = rsi_pct

# Now you have both percentiles for band analysis
print("Latest signals:")
print(f"MACD-V: {df['macdv_val'].iloc[-1]:.2f} "
      f"({df['macdv_percentile'].iloc[-1]:.1f}% in {df['macdv_zone'].iloc[-1]})")
print(f"RSI-MA: {rsi_ma.iloc[-1]:.2f} "
      f"({rsi_pct.iloc[-1]:.1f}%)")
```

### Example Multi-Dimensional Band Analysis:

```python
# Define multi-dimensional bands
bands = {
    "low_rsi_strong_macdv": {
        "rsi_percentile": (0, 20),      # Low RSI (oversold)
        "macdv_zone": "strong_bullish",  # Strong bullish zone (50-100)
        "macdv_percentile": (60, 100),   # High within that zone
    },
    "high_rsi_extreme_macdv": {
        "rsi_percentile": (80, 100),     # High RSI (overbought)
        "macdv_zone": "extreme_bullish", # Extreme bullish zone (>100)
        "macdv_percentile": (70, 100),   # High within that zone
    }
}

# Apply conditions
for band_name, conditions in bands.items():
    mask = (
        (df['rsi_percentile'] >= conditions['rsi_percentile'][0]) &
        (df['rsi_percentile'] < conditions['rsi_percentile'][1]) &
        (df['macdv_zone'] == conditions['macdv_zone']) &
        (df['macdv_percentile'] >= conditions['macdv_percentile'][0]) &
        (df['macdv_percentile'] < conditions['macdv_percentile'][1])
    )

    signals = df[mask]
    print(f"\n{band_name}: {len(signals)} signals")
```

---

## Interpretation Examples

### Example 1: Categorical Method (Recommended)
```
Current State:
  MACD-V Value: 75.32
  Zone: strong_bullish (50-100)
  Percentile: 82.5%

Interpretation:
"Strong bullish momentum (in the 50-100 zone), and currently in the
top 17.5% of historical values within that zone. This suggests we're
at a relatively high level of bullish momentum even within the strong
bullish regime."
```

### Example 2: Zone Transition
```
Previous State:
  MACD-V: 48.21 (weak_bullish zone, 75th percentile)

Current State:
  MACD-V: 52.18 (strong_bullish zone, 12th percentile)

Interpretation:
"Momentum has strengthened enough to move into the strong_bullish zone,
but we're at the low end of that zone (12th percentile). This is an
early-stage strong bullish signal."
```

### Example 3: Extreme Conditions
```
Current State:
  MACD-V: -125.67
  Zone: extreme_bearish (<-100)
  Percentile: 5th percentile

Interpretation:
"Extreme bearish conditions that are severe even by historical standards
of the extreme_bearish zone. Potentially oversold, but still in a strong
downtrend."
```

---

## API Response Format

### Chart Data with Percentiles:

```json
{
  "success": true,
  "ticker": "AAPL",
  "chart_data": {
    "dates": ["2025-01-01", "2025-01-02", ...],
    "macdv_val": [45.2, 47.8, ...],
    "macdv_percentile": [65.5, 72.3, ...],
    "macdv_zone": ["weak_bullish", "weak_bullish", ...],
    "current": {
      "macdv_val": 47.8,
      "macdv_percentile": 72.3,
      "macdv_zone": "weak_bullish"
    },
    "zone_stats": {
      "weak_bullish": {
        "count": 85,
        "pct_of_total": 23.5,
        "avg_percentile": 49.2,
        "min_val": 0.12,
        "max_val": 49.87,
        "avg_val": 24.35
      },
      "strong_bullish": {
        "count": 72,
        "pct_of_total": 19.9,
        "avg_percentile": 52.8,
        "min_val": 50.03,
        "max_val": 99.95,
        "avg_val": 74.21
      }
    },
    "percentile_method": "categorical",
    "percentile_lookback": 252
  }
}
```

---

## Recommendations

### For Most Use Cases: ✅ Use Categorical Method

**Reasons:**
1. Respects the natural zone structure of MACD-V
2. Provides relative positioning within each market regime
3. More meaningful than global percentiles for regime analysis
4. Combines absolute level (zone) with relative strength (percentile)

### When to Use Global Method:

- You want simplicity over nuance
- You're primarily looking for extreme values across all regimes
- You don't care about regime-specific behavior

### When to Use Asymmetric Method:

- You're specifically analyzing directional bias
- You want to treat bullish and bearish regimes completely separately
- You're building directional strategies

---

## Next Steps

### 1. Integrate into Existing Band Analysis:
   - Extend `macdv_rsi_band_analysis.py` to include MACD-V percentiles
   - Create multi-dimensional bands using both RSI-MA% and MACD-V%

### 2. Create Frontend Tab:
   - Add MACD-V percentile visualization
   - Show zone distribution statistics
   - Display current zone and percentile

### 3. Backtest with Percentiles:
   - Test strategies using MACD-V percentile thresholds
   - Compare performance across different percentile bands
   - Identify optimal entry/exit conditions

---

## Files Created

1. **`backend/macdv_percentile_calculator.py`**
   - Main implementation with all three methods
   - Zone statistics calculation
   - Chart data preparation

2. **`backend/test_macdv_percentiles.py`**
   - Comprehensive test suite
   - Demonstrates all three methods
   - Provides interpretation examples

3. **`docs/macdv_percentiles_guide.md`** (this file)
   - Complete documentation
   - Usage examples
   - Integration guidelines

---

## Conclusion

Yes, you should implement MACD-V percentiles, but with a **categorical (zone-based) approach** rather than simple global percentiles. This respects the inherent structure of MACD-V zones while providing valuable relative positioning information within each regime.

The implementation is now complete and ready to integrate with your existing band analysis system!
