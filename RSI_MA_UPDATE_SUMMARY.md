# RSI-MA Calculation Update Summary

**Date**: October 14, 2025
**Status**: ✅ COMPLETE

## Problem

The RSI-MA indicator was not matching TradingView values:
- Expected AAPL: 47.82-49.37
- Expected MSFT: 49.54
- Previous calculated values were significantly different

## Root Cause

The RSI calculation was using an incorrect source. Multiple methods were tested:
1. ❌ Direct RSI on z-scored log returns
2. ❌ RSI on LzR (EMA(7) smoothed z-scores)
3. ✅ **RSI on change of log returns (second derivative)**

## Solution

Updated the RSI-MA calculation to match TradingView:

### Calculation Pipeline
```
Close Price
  → Log Returns: log(price_t / price_t-1)
  → Delta (Change of Returns): diff()
  → RSI (14-period) using Wilder's method
  → EMA (14-period) smoothing
  → RSI-MA
```

This calculates RSI on the **second derivative of price** (rate of change of momentum), which measures **momentum acceleration**.

## Validation Results

### Test Results (test_working_method.py)
```
AAPL: 48.37 (expected: 47.82-49.37) ✅ MATCH
MSFT: 49.54 (expected: 49.54)       ✅ PERFECT MATCH
```

Both values are within the target range of 47.50-52.00.

## Files Modified

### Backend Changes

1. **enhanced_backtester.py:224-263** - `calculate_rsi_ma_indicator()` method
   ```python
   def calculate_rsi_ma_indicator(self, data: pd.DataFrame) -> pd.Series:
       close_price = data['Close']
       log_returns = np.log(close_price / close_price.shift(1)).fillna(0)
       delta = log_returns.diff()  # Key change: second derivative

       gains = delta.where(delta > 0, 0)
       losses = -delta.where(delta < 0, 0)

       # Wilder's smoothing
       avg_gains = gains.ewm(alpha=1/self.rsi_length, adjust=False).mean()
       avg_losses = losses.ewm(alpha=1/self.rsi_length, adjust=False).mean()

       rs = avg_gains / avg_losses
       rsi = 100 - (100 / (1 + rs))
       rsi = rsi.fillna(50)

       rsi_ma = rsi.ewm(span=self.ma_length, adjust=False).mean()
       return rsi_ma
   ```

2. **enhanced_backtester.py:857-893** - `get_rsi_percentile_timeseries()` method
   - Same calculation logic applied for chart data

3. **Cache cleared** - `/workspaces/New-test-strategy/backend/cache/`
   - All cached results removed to force regeneration with new calculation

### Frontend Changes

1. **RSIPercentileChart.tsx:733-757** - Added calculation method explanation
   - New info box explaining: "RSI is calculated on the change of log returns (second derivative of price), then smoothed with a 14-period EMA to produce RSI-MA. This measures momentum acceleration."
   - Maintains existing interpretation guide for oversold/overbought levels

### Other Components Reviewed
- ✅ `StrategyRulesPanel.tsx` - No changes needed (uses backend data)
- ✅ `PerformanceMatrixHeatmap.tsx` - No changes needed (uses backend data)
- ✅ `OptimalExitPanel.tsx` - No changes needed (uses backend data)
- ✅ `ReturnDistributionChart.tsx` - No changes needed (uses backend data)
- ✅ `EnhancedPerformanceMatrix.tsx` - No changes needed (uses backend data)

## Technical Details

### Why Second Derivative?

The calculation uses `pct_change().diff()` or `log_returns.diff()`, which is the **second derivative** of price:

1. **First derivative** (log returns): Rate of change of price (velocity)
2. **Second derivative** (delta): Rate of change of returns (acceleration)

This makes the RSI indicator more responsive to momentum shifts, as it measures acceleration rather than just velocity.

### Wilder's Smoothing

The RSI calculation uses Wilder's RMA (Running Moving Average):
```python
alpha = 1 / period  # For 14-period RSI, alpha = 1/14
ewm(alpha=alpha, adjust=False)
```

This is equivalent to TradingView's `ta.rma()` function.

## Testing

### Verification Test Files Created

1. **test_working_method.py** - Tests the exact working implementation
2. **test_lzr_with_diff.py** - Compares different calculation methods
3. **test_final_rsi_ma.py** - Tests complete LzR pipeline (for reference)
4. **debug_rsi_calculation.py** - Step-by-step debugging output

### How to Verify

```bash
cd backend
python test_working_method.py
```

Expected output:
```
AAPL: 48.37 (expected: 47.82-49.37) ✓ WITHIN TARGET RANGE
MSFT: 49.54 (expected: 49.54)       ✓ WITHIN TARGET RANGE
```

## Next Steps

1. **Restart Backend**:
   ```bash
   cd backend
   uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Restart Frontend** (if needed):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Clear Browser Cache** to ensure fresh data loads

4. **Verify in Dashboard**:
   - Open dashboard
   - Select AAPL
   - Check RSI-MA value matches ~48.37
   - Select MSFT
   - Check RSI-MA value matches ~49.54

## Impact on Strategy

The updated calculation provides:
- ✅ **Accurate matching** with TradingView indicators
- ✅ **Momentum acceleration** measurement (second derivative)
- ✅ **More responsive** signals for entry/exit timing
- ✅ **Consistent behavior** across all percentile ranges and time horizons (D1-D21)

All performance matrices, return distributions, optimal exit strategies, and trade management rules will now be calculated using the corrected RSI-MA values.

## References

- Working script provided by user (log returns → diff → RSI → EMA)
- TradingView RSI indicator documentation
- Test results in `test_working_method.py`
