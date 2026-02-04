# ✅ MACD-V Zones Corrected - Unified Ranging Zone

**Date:** 2026-02-04
**Status:** CORRECTED & REGENERATED
**Change:** Combined weak_bearish and weak_bullish into single **ranging** zone

---

## 🔧 What Was Changed

### ❌ OLD Structure (6 zones):
```
1. Extreme Bearish: < -100
2. Strong Bearish: -100 to -50
3. Weak Bearish: -50 to 0        ← Split ranging behavior
4. Weak Bullish: 0 to +50        ← Split ranging behavior
5. Strong Bullish: +50 to +100
6. Extreme Bullish: > +100
```

**Problem:** Ranging behavior was artificially split at zero, creating two separate percentile calculations for what is essentially the same market regime (mean reversion).

### ✅ NEW Structure (5 zones):
```
1. Extreme Bearish: < -100
2. Strong Bearish: -100 to -50
3. Ranging: -50 to +50           ← UNIFIED mean reversion zone
4. Strong Bullish: +50 to +100
5. Extreme Bullish: > +100
```

**Solution:** Single unified ranging zone with **one percentile** for the entire -50 to +50 range.

---

## 📊 Updated Zone Statistics

### Zone Distribution (Average across 31 tickers):

| Zone | Range | % of Time | Interpretation |
|------|-------|-----------|----------------|
| Extreme Bearish | < -100 | 5.0% | Strong downtrend |
| Strong Bearish | -100 to -50 | 13.2% | Downtrend |
| **Ranging** | **-50 to +50** | **43.5%** | **Mean reversion / Consolidation** |
| Strong Bullish | +50 to +100 | 19.8% | Uptrend |
| Extreme Bullish | > +100 | 18.5% | Strong uptrend |

**Key Insight:** The **Ranging zone** is the **most common** zone (43.5% of time), which makes sense for mean-reverting behavior.

---

## 💡 Understanding Ranging Zone Percentiles

### What 84% in Ranging Zone Means:

**Example:**
- MACD-V = 40
- Zone: Ranging (-50 to +50)
- Categorical Percentile: **84%**

**Interpretation:**
```
✅ CORRECT: At the 84th percentile of ALL values in the ranging zone (-50 to +50)
✅ This means: Near the TOP of the mean reversion range
✅ Implication: Overbought within ranging zone → Likely to revert DOWN
```

**Not:**
- ❌ 84% of the bullish half (0 to +50) only
- ❌ Two separate percentiles for bearish/bullish sides

**It's ONE percentile** for the entire -50 to +50 range.

---

## 🎯 Interpretation Examples

### Example 1: AAPL (-21.86, Ranging, 38.7%)
```
Zone: Ranging (-50 to +50)
Percentile: 38.7%
Interpretation: 📉 Lower range (39% - bearish side of range)
Meaning: Below the median of ranging values, slight bearish tilt
Action: Could be oversold within range, potential for mean revert up
```

### Example 2: SPY (37.18, Ranging, 60.0%)
```
Zone: Ranging (-50 to +50)
Percentile: 60.0%
Interpretation: 📈 Upper range (60% - bullish side of range)
Meaning: Above median of ranging values, slight bullish tilt
Action: Getting toward overbought within range, watch for reversion
```

### Example 3: Hypothetical (45, Ranging, 85%)
```
Zone: Ranging (-50 to +50)
Percentile: 85%
Interpretation: ⚠️ Overbought (85% - near top of range, likely revert down)
Meaning: At the top 15% of all ranging values historically
Action: High probability of mean reversion down toward lower percentiles
```

---

## 📈 Percentile Interpretation by Zone

### 1. Ranging Zone (-50 to +50) - Mean Reversion
- **≥80%**: ⚠️ **Overbought** - near top, likely revert DOWN
- **60-80%**: 📈 **Upper range** - bullish side
- **40-60%**: ➡️ **Mid-range** - neutral
- **20-40%**: 📉 **Lower range** - bearish side
- **≤20%**: 💡 **Oversold** - near bottom, likely revert UP

### 2. Bearish Zones (< -50) - Trending/Recovery
- **≥80%**: 🔄 **High recovery** - near top of bearish zone, recovering
- **60-80%**: ↗️ **Recovering** - strengthening
- **40-60%**: ➡️ **Mid-range** - neutral within downtrend
- **20-40%**: ↘️ **Weakening** - deepening downtrend
- **≤20%**: ⚠️ **Extreme** - severe levels within zone

### 3. Bullish Zones (> +50) - Trending/Momentum
- **≥80%**: 🚀 **Very strong** - near top, strong momentum
- **60-80%**: 📈 **Strengthening** - building momentum
- **40-60%**: ➡️ **Mid-range** - moderate momentum
- **20-40%**: 📉 **Weakening** - losing momentum
- **≤20%**: ⚠️ **Weak** - early stage or failing breakout

---

## 🔄 What Changed in the Database

### Updated Files:
1. `backend/macdv_percentile_calculator.py` ✅
2. `backend/live_macdv_percentiles.py` ✅
3. `backend/precompute_macdv_references.py` ✅
4. `backend/macdv_reference_lookup.py` ✅
5. `docs/macdv_reference_database.json` ✅ (regenerated)
6. `docs/macdv_reference_summary.md` ✅ (regenerated)

### Database Statistics:
- **Size:** 95.0 KB (was 107.5 KB - smaller with 5 zones vs 6)
- **Tickers:** 31
- **Data points:** 38,715
- **Generated:** 2026-02-04T09:08:56

---

## 📊 Example Ticker Breakdown

### AAPL Historical Distribution:
```
Overall:
  Mean: 26.18 (bullish skew)
  Range: -138.6 to 202.4

Time in Each Zone (1230 data points):
  Extreme Bearish:     3.6%
  Strong Bearish:     16.7%
  Ranging:            38.6%  ← 43.5% is average, AAPL slightly below
  Strong Bullish:     19.0%
  Extreme Bullish:    22.0%

Current State:
  MACD-V: -21.86
  Zone: Ranging
  Percentile: 38.7% (within -50 to +50 range)
```

---

## 🚀 Usage Examples

### Quick Lookup (No Recalculation):
```python
from macdv_reference_lookup import MACDVReferenceLookup

lookup = MACDVReferenceLookup()
info = lookup.get_ticker_info("AAPL")

# Current state
curr = info['current_state']
print(f"Zone: {curr['zone']}")  # "ranging"
print(f"Percentile: {curr['categorical_percentile']:.1f}%")  # "38.7%"

# Zone statistics
ranging_stats = info['zone_distribution']['ranging']
print(f"Time in ranging: {ranging_stats['pct_of_time']:.1f}%")  # "38.6%"
print(f"Ranging mean: {ranging_stats['mean']:.2f}")
```

### Live Calculation:
```python
from macdv_percentile_calculator import MACDVPercentileCalculator

calc = MACDVPercentileCalculator()
df = calc.calculate_macdv_with_percentiles(data, method="categorical")

latest = df.iloc[-1]
print(f"Zone: {latest['macdv_zone']}")  # "ranging"
print(f"Percentile: {latest['macdv_percentile']:.1f}%")  # One percentile for entire range
```

---

## ✅ Verification

### Test Results:
```bash
$ python3 live_macdv_percentiles.py "AAPL,NVDA,SPY,MSFT"

✓ AAPL: -21.86, Zone=ranging, Cat%=38.7%
✓ NVDA: 10.16, Zone=ranging, Cat%=58.1%
✓ SPY: 37.18, Zone=ranging, Cat%=60.0%
✓ MSFT: -113.08, Zone=extreme_bearish, Cat%=33.3%

RANGING (3 tickers):
  AAPL:  -21.86 (39% - lower range, bearish side)
  NVDA:   10.16 (58% - mid-range, neutral)
  SPY:    37.18 (60% - upper range, bullish side)
```

---

## 🎯 Key Takeaways

1. **Ranging zone is now unified** (-50 to +50)
2. **One percentile** for the entire ranging zone
3. **84% in ranging = near top of mean reversion range** ✅
4. High percentile in ranging → overbought → likely revert down
5. Low percentile in ranging → oversold → likely revert up
6. **43.5% of time** spent in ranging zone (most common)
7. Database regenerated and ready for production

---

## 📁 All Files Updated

### Backend:
- ✅ `backend/macdv_percentile_calculator.py`
- ✅ `backend/live_macdv_percentiles.py`
- ✅ `backend/precompute_macdv_references.py`
- ✅ `backend/macdv_reference_lookup.py`

### Data:
- ✅ `docs/macdv_reference_database.json` (95.0 KB)
- ✅ `docs/macdv_reference_summary.md`
- ✅ `docs/live_macdv_percentiles.md`
- ✅ `docs/live_macdv_percentiles.csv`

### Documentation:
- ✅ `docs/MACDV_ZONES_CORRECTED.md` (this file)

---

## 🎉 Summary

**Your observation was correct!** Ranging should be one unified zone (-50 to +50) with a single percentile, not split into two zones. This has been corrected throughout the entire codebase and database.

**The system is now production-ready with the correct zone structure!** 🚀
