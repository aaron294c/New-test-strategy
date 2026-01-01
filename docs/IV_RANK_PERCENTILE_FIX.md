# IV Rank & IV Percentile - Fixed Alignment

## The Problem You Discovered

**Great catch!** You noticed the discrepancy:

```
Option: Strike $581
IV Rank: 0.04 (4th percentile - very cheap)
IV Percentile: 30% (30th percentile)

These don't match! ❌
```

**What was happening:**
- IV Rank used linear interpolation: (IV - 15%) / (60% - 15%)
- IV Percentile used fixed buckets:
  - 15-20% IV → 30th percentile
  - 20-25% IV → 50th percentile
  - etc.

**The issue:** Two different calculation methods gave conflicting signals!

---

## The Fix

**Now aligned perfectly:**

```python
# IV Rank (0-1 scale)
iv_rank = (current_iv - 15%) / (60% - 15%)

# IV Percentile (0-100 scale) - NOW ALIGNED
iv_percentile = iv_rank × 100
```

**Result:** IV rank and percentile now use the **exact same calculation**!

---

## What You'll See After Restart

### Before (Misaligned):
```
Option 1:
  Raw IV: 16.8%
  IV Rank: 0.04 (very cheap)
  IV Percentile: 30% (????)
  → Confusing! Doesn't match!
```

### After (Aligned):
```
Option 1:
  Raw IV: 16.8%
  IV Rank: 0.04 (very cheap)
  IV Percentile: 4% (very cheap)
  → Perfect alignment! ✓
```

---

## New IV Column Added

You can now see the **raw IV value** that drives the rank and percentile:

**Table columns (in order):**
1. Vega
2. Vega Risk (badge)
3. **IV** ← NEW! Raw implied volatility
4. IV Rank (0-1 scale)
5. IV Percentile (0-100 scale, now aligned)

**Example interpretation:**
```
Raw IV: 18.2%
IV Rank: 0.07 (calculated as (18.2 - 15) / 45 = 0.07)
IV Percentile: 7% (calculated as 0.07 × 100 = 7%)

All three tell the same story: Volatility is very cheap! ✓
```

---

## Understanding the Scale

**IV Rank = 0-1 scale (where 0 = cheapest, 1 = most expensive):**
```
0.00 - 0.20  →  Very cheap (green)
0.20 - 0.30  →  Cheap (green)
0.30 - 0.60  →  Fair/elevated (yellow)
0.60 - 1.00  →  Expensive (red)
```

**IV Percentile = 0-100% scale (same as rank × 100):**
```
0% - 20%    →  Very cheap (green)
20% - 30%   →  Cheap (green)
30% - 60%   →  Fair/elevated (yellow)
60% - 100%  →  Expensive (red)
```

**Raw IV = The actual implied volatility percentage:**
```
≤ 15%       →  Extremely low (crisis lows)
15% - 20%   →  Low (typical calm market)
20% - 25%   →  Average
25% - 35%   →  Elevated
35% - 60%   →  High (crisis levels)
> 60%       →  Extreme (rare)
```

---

## How to Use All Three Together

### Example 1: Very Cheap Volatility
```
Raw IV: 16.5%
IV Rank: 0.03
IV Percentile: 3%

Interpretation:
- Raw IV tells you: IV is near typical lows (16.5% vs 15% floor)
- IV Rank tells you: On 0-1 scale, you're at 0.03 (very cheap)
- IV Percentile tells you: You're at 3rd percentile (very cheap)
All three aligned perfectly! ✓
```

### Example 2: Moderately Cheap Volatility
```
Raw IV: 22.5%
IV Rank: 0.17
IV Percentile: 17%

Interpretation:
- Raw IV tells you: IV is in average range (22.5%)
- IV Rank tells you: On 0-1 scale, you're at 0.17 (cheap)
- IV Percentile tells you: You're at 17th percentile (cheap)
All three aligned! ✓
```

### Example 3: Expensive Volatility (AVOID)
```
Raw IV: 42.0%
IV Rank: 0.60
IV Percentile: 60%

Interpretation:
- Raw IV tells you: IV is elevated (42% vs 35% typical high)
- IV Rank tells you: On 0-1 scale, you're at 0.60 (expensive)
- IV Percentile tells you: You're at 60th percentile (expensive)
All three say: AVOID! ✓
```

---

## Expected Values for Your Deep ITM Options

Based on typical market conditions, your options should show:

**If IV is around 16-18% (cheap):**
```
Raw IV: 16.8%
IV Rank: 0.04
IV Percentile: 4%
Vega Risk: Orange "High Vega + Cheap IV" ✓
```

**If IV is around 22-24% (moderate):**
```
Raw IV: 22.5%
IV Rank: 0.17
IV Percentile: 17%
Vega Risk: Orange "High Vega + Cheap IV" ✓
```

**Both are acceptable entry conditions** (orange badge).

---

## Why This Fix Matters

**Before the fix:**
- User sees IV Rank 0.04 (very cheap) but IV Percentile 30% (fair)
- Confusing mixed signals
- Hard to trust the data

**After the fix:**
- User sees IV Rank 0.04 and IV Percentile 4%
- Clear, consistent message: "Volatility is very cheap"
- Plus raw IV shows the actual value (16.8%)
- All three metrics tell the same story ✓

---

## Summary

**What changed:**
1. ✅ Added **Raw IV column** to see actual implied volatility
2. ✅ Fixed **IV Percentile** to align perfectly with IV Rank
3. ✅ Now IV Percentile = IV Rank × 100 (same calculation)

**Result:**
- No more confusing discrepancies
- All three metrics (Raw IV, IV Rank, IV Percentile) tell the same story
- Easier to make informed decisions

**After restart, you'll see:**
```
Vega | Vega Risk | IV    | IV Rank | IV %ile
-----|-----------|-------|---------|--------
0.45 | Orange    | 16.8% | 0.04    | 4%      ✓ Aligned!
0.65 | Orange    | 18.2% | 0.07    | 7%      ✓ Aligned!
0.65 | Orange    | 17.5% | 0.06    | 6%      ✓ Aligned!
```

Much clearer! 🎯
