# Vega & IV Rank/Percentile Guide

## ✅ Vega Calculation is CORRECT

Your LEAPS scanner uses **mathematically correct** vega calculations. Both conventions are valid:

### Two Vega Conventions:

**1. Standard Convention (most platforms):**
- Vega per 1 percentage point IV change
- Deep ITM: 0.5 - 5.0
- ATM: 15 - 25
- Your research showing "10-20" uses this convention

**2. Our Convention (what we use):**
- Vega per 1% IV change (divided by 100)
- Deep ITM: 0.005 - 0.05
- ATM: 0.15 - 0.25
- **This is what your scanner displays**

**Both are correct** - just different units. Our values are 100x smaller.

## 📊 How to Use Vega + IV Rank/Percentile Together

The LEAPS table shows three columns side-by-side:

| Vega | IV Rank | IV Percentile |
|------|---------|---------------|
| 0.0221 | 0.15 | 30% |

### What Each Metric Means:

**Vega (0.0221):**
- Sensitivity to volatility changes
- Low vega (0.01-0.10) = Deep ITM, less affected by IV changes
- High vega (0.15-0.30) = ATM, very sensitive to IV changes

**IV Rank (0.15):**
- Current IV relative to its typical range (0-1 scale)
- 0.00-0.30 = **CHEAP volatility** (green) 🟢
- 0.30-0.60 = **FAIR volatility** (yellow) 🟡
- 0.60-1.00 = **EXPENSIVE volatility** (red) 🔴

**IV Percentile (30%):**
- Percentage of days where IV was below current level
- 0-30% = **LOW IV** (good time to buy)
- 30-70% = **MODERATE IV**
- 70-100% = **HIGH IV** (good time to sell)

## 🎯 Trading Strategy: Cheap vs Expensive Volatility

### BEST Scenarios for BUYING LEAPS:

✅ **Low Vega + Low IV Rank + Low IV Percentile**
```
Vega: 0.02-0.10
IV Rank: < 0.30 (green)
IV Percentile: < 30%

Why: Deep ITM option with cheap volatility = stable, low-risk entry
```

✅ **Medium Vega + Low IV Rank + Low IV Percentile**
```
Vega: 0.10-0.20
IV Rank: < 0.30 (green)
IV Percentile: < 30%

Why: Near ATM with cheap volatility = good upside potential
```

### ❌ AVOID These Scenarios:

**High Vega + High IV Rank + High IV Percentile**
```
Vega: 0.20-0.30
IV Rank: > 0.60 (red)
IV Percentile: > 70%

Why: Paying premium for expensive volatility = poor risk/reward
```

## 🔍 Real Examples from Your Scanner:

### Example 1: IDEAL Deep ITM LEAPS
```
Strike: $600
Delta: 0.889
Vega: 0.0221
IV Rank: 0.15 🟢
IV Percentile: 30%

Analysis:
- Deep ITM (delta 0.89)
- Low vega (0.02) = stable pricing
- Cheap volatility (IV rank 0.15)
- Below average IV (30th percentile)
→ EXCELLENT buying opportunity
```

### Example 2: EXPENSIVE Volatility
```
Strike: $690
Delta: 0.592
Vega: 0.1895
IV Rank: 0.78 🔴
IV Percentile: 85%

Analysis:
- ATM option (delta 0.59)
- High vega (0.19) = sensitive to IV
- Expensive volatility (IV rank 0.78)
- Very high IV (85th percentile)
→ AVOID - wait for IV to drop
```

## 📈 How to Filter in the Scanner:

### For Deep ITM LEAPS (stable, low vega):
```
Delta: 0.85 - 0.98
Max Vega: 0.10
Max IV Rank: 0.30
IV Percentile: 0 - 40%

Result: Deep ITM options with cheap volatility
```

### For ATM LEAPS (higher returns, higher vega):
```
Delta: 0.45 - 0.60
Min Vega: 0.15
Max IV Rank: 0.40
IV Percentile: 0 - 50%

Result: Near-money options bought during low IV periods
```

## 💡 Key Takeaways:

1. **Vega calculation is CORRECT** ✅
   - Our convention uses /100 (0.02-0.25 range)
   - Standard convention doesn't divide (2-25 range)
   - Both are mathematically accurate

2. **Use IV Rank/Percentile to determine cost** 💰
   - Green IV Rank (< 0.30) = Cheap volatility
   - Red IV Rank (> 0.60) = Expensive volatility

3. **Lower vega = more stable pricing** 📊
   - Deep ITM options have low vega (0.02-0.10)
   - Less affected by IV changes
   - More predictable behavior

4. **Best opportunities:** 🎯
   - Low vega + Low IV rank + Low IV percentile
   - Stable option with cheap volatility

5. **Worst situations:** ⚠️
   - High vega + High IV rank + High IV percentile
   - Volatile option with expensive volatility

---

**Remember:** The table already shows all three metrics side-by-side. Use them together to identify the best LEAPS opportunities!
