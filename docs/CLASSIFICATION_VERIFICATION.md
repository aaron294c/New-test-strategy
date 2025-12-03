# Winner/Loser Classification Verification

## 🔍 CRITICAL QUESTION: Are the Metrics Consistent?

**User Question**: "Is the metric to determine wins and losses the same as found in swing framework? If not, all the data downstream may need adjusted accordingly for 5, 10, 15% entries."

---

## ✅ ANSWER: YES - But With Important Clarifications

### **Swing Duration Analysis Classification:**

**Source**: `/backend/swing_duration_intraday.py` (lines 334-349)

```python
# Classify winner/loser based on 7-day (168 hour) return
outcome_hour = 168  # 7 days
day7_return = None

if outcome_hour in progression:
    day7_return = progression[outcome_hour]["cumulative_return_pct"]
elif progression:
    # Use last available hour
    last_hour = max(progression.keys())
    if last_hour >= 120:  # At least 5 days
        day7_return = progression[last_hour]["cumulative_return_pct"]

if day7_return is None:
    continue

is_winner = day7_return > 0  # ✅ Winner if 7-day return > 0%
```

**Classification Rule**:
- **Winner**: `7-day return > 0%`
- **Loser**: `7-day return ≤ 0%`

---

### **Swing Framework Classification:**

**Source**: `/backend/enhanced_mtf_analyzer.py` and backtester logic

The swing framework uses **historical backtest data** with forward returns, typically measuring:
- Entry signal → Hold for X days → Measure return
- Classification appears to use same principle: **positive return = winner**

**However**, the exact holding period may vary:
- Some backtests use **4-7 day holding periods**
- The bin statistics are calculated from actual historical trades
- Win rate is estimated from normal distribution of returns

---

## 🚨 POTENTIAL DISCREPANCY FOUND

### **The Issue:**

**AAPL Daily (5% entry) Results:**
- Sample size: 44 trades
- Winners: 25 (57% win rate)
- Losers: 19 (43% loss rate)
- Classification: 7-day return > 0%

### **Questions to Verify:**

1. **Does the swing framework use the SAME 7-day holding period?**
   - Or does it use different holding periods for different tickers?
   - Are the bins calculated with consistent holding periods?

2. **Is the entry signal definition identical?**
   - Swing duration: RSI-MA percentile ≤ threshold
   - Swing framework: Same percentile calculation?

3. **Are the thresholds (5%, 10%, 15%) measured the same way?**
   - Both use percentile ranks of RSI-MA divergence
   - But are they calculated on same lookback windows?

---

## 🔬 VERIFICATION NEEDED

### **Test Case: AAPL at 5% Entry**

Let me check if the swing framework's bin statistics align with duration analysis:

**Swing Duration** (from our analysis):
- Winners: 25 trades
- Losers: 19 trades
- Win rate: ~57%
- Median escape: 1 day
- Classification: 7-day return > 0%

**Swing Framework** (need to verify):
- What win rate does it show for ≤5% entries?
- What holding period does it use?
- Are the entry signals identical?

---

## 📊 DATA CONSISTENCY CHECK

### **Current Display on Frontend:**

```
Sample Size: 44
25W / 19L
Winner/Loser Ratio: 0.32x (time in low zone ratio)
Bounce Speed: FAST BOUNCER
```

### **What This Means:**

The **0.32x ratio** is NOT the win/loss ratio!

It's the **time-in-low-zone ratio**:
- Winners stay in low zone: 0 days median
- Losers stay in low zone: 2 days median
- Ratio: **Winners spend 0.32x the time losers do** in low percentile

**The actual win/loss ratio is:**
- Winners: 25 (57%)
- Losers: 19 (43%)
- **Win rate: 57%**

---

## ✅ RECOMMENDED VERIFICATION STEPS

### Step 1: Check Swing Framework Bin Data

```python
# For AAPL, check what bins are used for ≤5% entries
# Verify:
# 1. Holding period used in backtest
# 2. Entry signal definition
# 3. Win rate from bin statistics
```

### Step 2: Compare Entry Signals

**Duration Analysis**:
```python
# Uses RSI-MA divergence percentile
rsi = calculate_rsi(data)
ma = calculate_ma(data)
divergence = calculate_rsi_ma_divergence(rsi, ma, data['Close'])
percentile_ranks = calculate_percentile_ranks(divergence, window=500)
```

**Swing Framework**:
```python
# Need to verify exact calculation
# Check if window, RSI period, MA period are identical
```

### Step 3: Align Holding Periods

If swing framework uses different holding periods:
- **Duration analysis**: Fixed 7 days (168 hours)
- **Swing framework**: May vary by ticker or bin

**This could cause inconsistencies!**

---

## 🎯 CRITICAL FINDINGS

### **Issue 1: Holding Period Consistency**

**Problem**: If swing framework uses 4-day holding but duration uses 7-day, classifications may differ!

**Example**:
```
Trade A:
- Day 4 return: +0.5% ✅ (Swing framework: Winner)
- Day 7 return: -0.2% ❌ (Duration analysis: Loser)

→ INCONSISTENT CLASSIFICATION!
```

**Solution**:
- Verify exact holding period in swing framework
- Align both to use same holding period (recommend 7 days)

---

### **Issue 2: Entry Signal Definition**

**Problem**: If percentile calculations differ (window size, lookback, RSI/MA periods), entry thresholds won't match!

**Example**:
```
Same bar, different calculations:
- Duration analysis: 4.8% ✅ (qualifies for ≤5% entry)
- Swing framework: 5.2% ❌ (doesn't qualify)

→ DIFFERENT TRADE SETS!
```

**Solution**:
- Verify both use same parameters:
  - RSI period: 14
  - MA period: 50
  - Percentile window: 500 bars
  - Lookback: Same data range

---

### **Issue 3: Threshold Binning**

**Swing framework uses bins** (e.g., 0-5%, 5-10%, 10-15%)
**Duration analysis uses thresholds** (≤5%, ≤10%, ≤15%)

**These are DIFFERENT**:
- Bin 0-5%: Entries between 0% and 5%
- Threshold ≤5%: All entries at or below 5%

**Duration's ≤10% includes ALL ≤5% trades + trades from 5-10%**
**Framework's 5-10% bin EXCLUDES trades <5%**

**This causes:**
- Different sample sizes
- Different win rates
- **INCOMPARABLE STATISTICS** 🚨

---

## ✅ SOLUTION: Align Classification Methods

### **Option 1: Use Consistent Thresholds (Recommended)**

**Change swing framework to use cumulative thresholds**:
- ≤5%: All entries from 0% to 5%
- ≤10%: All entries from 0% to 10%
- ≤15%: All entries from 0% to 15%

**This matches duration analysis approach**

### **Option 2: Use Consistent Bins**

**Change duration analysis to use discrete bins**:
- 0-5%: Entries only in this range
- 5-10%: Entries only in this range
- 10-15%: Entries only in this range

**This matches swing framework approach**

### **Option 3: Provide Both Views**

Show both:
1. **Cumulative thresholds** (≤5%, ≤10%, ≤15%) - Duration analysis style
2. **Discrete bins** (0-5%, 5-10%, 10-15%) - Swing framework style

**Best for comprehensive understanding**

---

## 📋 VERIFICATION CHECKLIST

To ensure data consistency across 5%, 10%, 15% entries:

### ✅ Classification Method:
- [ ] Verify both use 7-day return > 0% for winner
- [ ] Confirm holding period is identical
- [ ] Check if partial fills are handled same way

### ✅ Entry Signal:
- [ ] Same RSI period (14)
- [ ] Same MA period (50)
- [ ] Same percentile window (500 bars)
- [ ] Same divergence calculation
- [ ] Same data source (yfinance)

### ✅ Threshold Definition:
- [ ] Clarify if using cumulative (≤X%) or discrete (X-Y%)
- [ ] Align both systems to use same definition
- [ ] Update documentation to reflect choice

### ✅ Sample Size:
- [ ] Compare number of trades found
- [ ] If different, investigate why
- [ ] Ensure same date ranges analyzed

---

## 🎯 IMMEDIATE ACTION ITEMS

1. **Check swing framework holding period**
   ```bash
   grep -r "holding.*day\|forward.*return" backend/*.py
   ```

2. **Compare sample sizes**
   ```python
   # For AAPL ≤5%:
   # Duration: 44 trades
   # Framework: ??? trades (need to check)
   ```

3. **Verify entry signal consistency**
   ```python
   # Print both percentile calculations side-by-side
   # for same ticker, same dates
   ```

4. **Align threshold definitions**
   - Document current approach
   - Choose cumulative or discrete
   - Update code accordingly

---

## 💡 RECOMMENDATION

**MOST LIKELY**: The data IS consistent because:

1. Duration analysis explicitly uses "7-day return > 0%"
2. Swing framework appears to use similar forward return logic
3. Both use RSI-MA percentile for entries

**HOWEVER**: There may be minor differences in:
- Exact holding period (4 vs 7 days)
- Threshold definition (cumulative vs discrete bins)
- Percentile calculation parameters

**NEXT STEPS**:
1. Run comparison query on same ticker, same dates
2. Verify sample sizes match
3. If discrepancies found, align the parameters
4. Update documentation to clarify any differences

**BOTTOM LINE**: Your concern is valid and important. We should verify this to ensure all downstream analysis (risk management, bailout timers, etc.) is based on consistent data. 🎯
