# Percentile Window Size Calculation - FINAL CORRECTED

## The Correct Math (NYSE Trading Hours)

### NYSE Trading Hours
- **6.5 hours per trading day** (9:30 AM - 4:00 PM ET)
- NOT 24 hours (this is stocks, not FX/futures)

### Daily Candles
- **1 trading day = 1 candle**
- **252 bars = 252 trading days ≈ 1 year**

### 4-Hour Candles (NYSE hours)
- **1 trading day = 1.625 candles** (6.5 hours ÷ 4 hours = 1.625)
- **To match 252 days**: 252 days × 1.625 candles/day = **409.5 ≈ 410 bars**

## Window Size Summary

| Timeframe | Bars | Time Period | Calculation |
|-----------|------|-------------|-------------|
| **Daily** | 252 bars | 252 trading days (~1 year) | 252 days × 1 candle/day |
| **4H** | 410 bars | 252 trading days (~1 year) | 252 days × 1.625 candles/day |

## Why 1.625 candles/day?

NYSE is open 6.5 hours per day:
- 6.5 hours ÷ 4 hours per candle = **1.625 4H candles per trading day**

## Files Updated

### 1. `/workspaces/New-test-strategy/backend/swing_duration_intraday.py`
**Line 228:**
```python
def calculate_percentile_ranks(series: pd.Series, window: int = 410) -> pd.Series:
    # 410 bars = 252 trading days × 1.625 candles/day
```

### 2. `/workspaces/New-test-strategy/backend/percentile_forward_4h.py`
**Line 112:**
```python
def calculate_percentile_ranks_4h(rsi_ma: pd.Series, lookback_window: int = 410) -> pd.Series:
    # 410 bars = 252 trading days × 1.625 candles/day
```

**Line 169:**
```python
percentiles_4h = calculate_percentile_ranks_4h(rsi_ma_4h, lookback_window=410)
```

**Line 181:**
```python
lookback_window=410  # 410 4H bars = 252 trading days (matches daily timeframe period)
```

## Why This Matters

Both the Duration tab and Percentile Forward Mapping tab now calculate percentiles using **exactly the same historical time period** (252 trading days / ~1 year), ensuring consistent percentile values across both tabs.

This means:
- ✅ "5%ile entry signal" means the same thing in both tabs
- ✅ Current percentile display will match between tabs
- ✅ Historical context is identical (1 year lookback)
- ✅ Percentile is calculated using the same market conditions period
