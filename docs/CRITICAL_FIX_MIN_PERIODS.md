# CRITICAL FIX: min_periods Must Equal window

## The Bug

**File:** `backend/swing_duration_intraday.py` line 248

**Previous code:**
```python
return series.rolling(window=window, min_periods=min(50, window // 2)).apply(percentile_rank, raw=False)
```

With `window=410`, this calculated `min_periods=min(50, 205) = 50`

## Why This Was CRITICALLY Wrong

### The Problem

The `min_periods` parameter determines **when percentile calculation starts**:

- **With `min_periods=50`**: Percentile calculation began after only 50 bars
  - At bar 100: percentile uses 100-bar lookback (NOT 410!)
  - At bar 200: percentile uses 200-bar lookback (NOT 410!)
  - At bar 410: percentile uses 410-bar lookback ✓

- **With `min_periods=410`**: Percentile calculation begins ONLY after 410 bars
  - First 410 bars: percentile = NaN (no calculation)
  - At bar 411+: percentile ALWAYS uses exactly 410-bar lookback ✓✓✓

### Impact on Sample Sizes

**Before fix (min_periods=50):**
- Total bars available: 1,453
- Valid percentile bars: 1,453 - 50 = **1,403 bars** ❌
- **BUT** only the last ~1,000 bars had the correct 410-bar lookback!
- Early ~400 bars had WRONG percentiles (using 50-400 bar lookback)

**After fix (min_periods=410):**
- Total bars available: 1,453
- Valid percentile bars: 1,453 - 410 = **1,043 bars** ✓
- **ALL** 1,043 bars have CORRECT percentiles (using 410-bar lookback)

## Why Sample Sizes Were Small

With the old code:
1. Early entry events (bars 50-410) had **invalid percentiles**
2. These used 50-400 bar lookbacks instead of the required 410 bars
3. **These entry events should NOT have been included!**
4. Removing them reduces sample size, BUT the remaining samples are **CORRECT**

## The Fix

**Updated code:**
```python
# CRITICAL: min_periods MUST equal window to ensure consistent lookback period
# Setting min_periods < window would calculate percentiles with insufficient data,
# breaking the alignment with daily timeframe (252 days = 410 bars for 4H)
return series.rolling(window=window, min_periods=window).apply(percentile_rank, raw=False)
```

## Expected Outcome

### Sample Size Changes

You should see:
- ✅ **Smaller but CORRECT sample sizes** - Only using entry events with valid 410-bar percentiles
- ✅ **Consistent percentile values** - Every percentile uses exactly 410 bars = 252 trading days
- ✅ **Matching Forward Mapping tab** - Same percentile calculation methodology

### Data Availability

With 730 days of 4H data from Yahoo Finance:
- **Total bars fetched**: ~1,453 bars
- **Percentile window**: 410 bars (required lookback)
- **Valid percentile data**: 1,453 - 410 = **1,043 bars**
- **Usable time period**: ~641 trading days of valid percentile data

### Why This Matters

The whole point of using **410 bars** is to match the **252 trading days** used by daily percentile calculation:

- **Daily**: 252 bars = 252 trading days
- **4H**: 410 bars = 252 trading days (252 × 1.625 candles/day)

If we allow percentiles to be calculated with fewer than 410 bars, we're **NOT** looking back 252 trading days, which defeats the entire purpose of the fix!

## Verification

Compare these two scenarios for the same stock at the same timestamp:

**Scenario 1 (WRONG - min_periods=50):**
- Entry at bar 200 with percentile 3.5%
- Percentile calculated using only 200 bars (~123 days lookback) ❌
- Not comparable to daily (which uses 252 days) ❌

**Scenario 2 (CORRECT - min_periods=410):**
- Entry at bar 411 with percentile 3.5%
- Percentile calculated using exactly 410 bars (252 days lookback) ✓
- Directly comparable to daily (which uses 252 days) ✓

## Bottom Line

**Smaller sample sizes are EXPECTED and CORRECT** after this fix because:

1. We're removing early invalid entry events (bars 50-410)
2. We're ensuring EVERY entry event uses a valid 410-bar percentile
3. We're maintaining consistency with the daily 252-day lookback period

This is **data quality over quantity** - better to have fewer samples that are all calculated correctly than more samples where some are wrong!
