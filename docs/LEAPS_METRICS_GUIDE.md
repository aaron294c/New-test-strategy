# LEAPS Metrics Guide

## Understanding Your Results

### Current Opportunity Scores (52, 45, 40)

Your DEEP_ITM options are scoring **YELLOW (50-74)** because they have **higher vega than ideal**:

**Why This Matters:**
- Vega 0.450 = option price changes by $0.45 for each 1% IV change
- For a $111 option, this is 0.4% price sensitivity to volatility
- **Deep ITM options should have vega < 0.10 for GREEN scores (75-100)**

### Your Current Top Options Analysis

**Option: Strike $581 (Score: 52)**
```
Premium: $111.40
Delta: 0.957
Vega: 0.450 (TOO HIGH for deep ITM)
IV Rank: 0.04 (EXCELLENT - very cheap volatility)
IV Percentile: 30% (GOOD - below average)

Scoring Breakdown:
✗ Vega: 0.450 > 0.25 → 0 points (needs vega ≤ 0.05 for 35 pts)
✓ IV Rank: 0.04 < 0.20 → 40 points (excellent!)
✓ IV Percentile: 30% → 12 points (acceptable)
─────────────────────────────
Total: 52/100 (YELLOW - Fair opportunity)

Interpretation: Great IV conditions but too much volatility exposure
```

## New Metrics Added (Backend Only - Frontend Update Needed)

### 1. Leverage Factor
**Formula:** `(Delta × Spot Price) / Premium`

**What it means:** Stock exposure per dollar invested

**Example:**
```
Strike $581: Delta 0.957, Spot $690.31, Premium $111.40
Leverage = (0.957 × $690.31) / $111.40 = 5.93x

You get $5.93 of stock exposure per $1 invested
```

**Interpretation:**
- Higher = more leverage (riskier, more potential)
- Deep ITM: Typically 5-7x
- ATM: Typically 10-15x

### 2. Vega Efficiency
**Formula:** `(Vega / Premium) × 100`

**What it means:** Volatility exposure per dollar invested

**Example:**
```
Strike $581: Vega 0.450, Premium $111.40
Vega Efficiency = (0.450 / $111.40) × 100 = 0.404%

For each $100 invested, you have $0.40 vega exposure
```

**Interpretation:**
- **Lower is better** for deep ITM LEAPS
- Target: < 0.15% for stable deep ITM positions
- > 0.40% = high volatility risk

### 3. Cost Basis
**Formula:** `Premium / Delta`

**What it means:** Effective cost per share of exposure

**Example:**
```
Strike $581: Premium $111.40, Delta 0.957
Cost Basis = $111.40 / 0.957 = $116.39 per share

You're paying $116.39 per share of effective exposure
vs. $690.31 to buy the stock directly
```

**Interpretation:**
- Lower = more efficient stock replacement
- Deep ITM: Typically $115-$125 per share
- Compare to current stock price: $690.31

### 4. ROI on 10% Stock Move
**Formula:** `(Delta × Spot × 0.10) / Premium × 100`

**What it means:** Return if stock moves up 10%

**Example:**
```
Strike $581: Delta 0.957, Spot $690.31, Premium $111.40
ROI = (0.957 × $690.31 × 0.10) / $111.40 × 100 = 59.3%

If SPY rises 10%, option gains ~59.3%
```

**Interpretation:**
- Deep ITM: 50-65% return on 10% stock move
- ATM: 100-150% return on 10% stock move
- Higher delta = closer to 1:1 with stock

## What You Should Look For

### For BEST Deep ITM LEAPS (Score 75-100):

**Required Filters:**
```
Delta: 0.85 - 0.98
Max Vega: 0.10 (CRITICAL!)
Max IV Rank: 0.30
Max IV Percentile: 40%
Max Extrinsic: 10%
```

**Expected Metrics:**
```
Opportunity Score: 75-100 (GREEN)
Leverage Factor: 5-7x
Vega Efficiency: < 0.15%
Cost Basis: $115-$125 per share
ROI on 10% move: 50-65%
```

**Why Vega < 0.10 Matters:**
- Vega 0.10 = $0.10 price change per 1% IV change
- On $110 premium, that's only 0.09% volatility exposure
- **This makes the option trade like stock, not like an option**

### Current Market Reality

Your results show **NO options with vega < 0.10** are available right now. This means:

1. **Not an ideal time to enter deep ITM LEAPS** (high vega environment)
2. **Wait for lower vega** or accept YELLOW scores (fair opportunities)
3. **Consider ATM LEAPS instead** (naturally have higher vega, but better opportunity scores)

## IV Rank & IV Percentile Verification

### How They're Calculated

**IV Rank (0-1 scale):**
```
Typical SPY LEAPS IV Range: 15% - 60%

0.0 = IV ≤ 15% (historical lows, very cheap)
0.5 = IV = 37.5% (mid-range)
1.0 = IV ≥ 60% (crisis levels, very expensive)

Your options showing 0.04-0.18 = EXCELLENT (cheap volatility)
```

**IV Percentile (0-100%):**
```
Simplified percentile based on IV level:

IV ≤ 15%    → 10th percentile (very low)
IV 15-20%   → 30th percentile (low)
IV 20-25%   → 50th percentile (average)
IV 25-30%   → 70th percentile (elevated)
IV > 40%    → 95th percentile (very high)

Your options showing 30-50% = GOOD (below to at average)
```

**✓ These calculations are reasonable** for current market conditions.

## Recommended Actions

### Option 1: Wait for Better Vega (IDEAL)
Add max_vega filter and wait for opportunities:
```
Strategy: DEEP_ITM
Delta: 0.85 - 0.98
Max Vega: 0.10
Max IV Rank: 0.30

Expected Results: 0-2 options (rare but excellent)
```

### Option 2: Accept Current Market (FAIR)
Use current options with vega 0.45-0.65:
```
Strategy: DEEP_ITM
Delta: 0.85 - 0.98
Max Vega: 0.70
Max IV Rank: 0.30

Expected Results: 5-10 options (fair opportunities)
Scores: 40-60 (YELLOW)
```

### Option 3: Consider ATM Instead (ALTERNATIVE)
ATM LEAPS naturally have higher vega but better opportunity scores:
```
Strategy: ATM
Delta: 0.45 - 0.60
Max IV Rank: 0.30

Expected Results: 1-3 options
Higher leverage, higher returns, more risk
```

## Summary

### Yes, These ARE the Best 9 Options Available

Based on opportunity scoring:
- ✓ Ranked correctly by opportunity score
- ✓ Lowest available vega for deep ITM
- ✓ Excellent IV rank (0.04-0.18)
- ✓ Good IV percentile (30-50%)

### The Problem: Market Conditions

- **No deep ITM options with vega < 0.10 exist right now**
- Current market has elevated vega across all strikes
- Your options are "best available" but not "ideal conditions"

### Additional Filters to Consider

1. **Max Vega: 0.50** - Tighten vega requirement
2. **Max Vega Efficiency: 0.30%** - Limit volatility exposure per dollar
3. **Min Leverage Factor: 5.5** - Ensure adequate leverage
4. **Max Cost Basis: $120** - Cap effective cost per share

### Next Steps

1. **Check new metrics** after frontend update (leverage, vega efficiency, etc.)
2. **Set vega filter to 0.50** to eliminate worst vega options
3. **Monitor daily** for vega < 0.10 opportunities (GREEN scores)
4. **Consider waiting** if you want optimal entry (score 75+)
