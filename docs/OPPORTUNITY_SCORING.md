# Opportunity Scoring System

## Overview

The LEAPS scanner now includes an **Opportunity Score** that ranks options from **BEST** (100) to **WORST** (0) based on volatility value.

## How It Works

The Opportunity Score combines three key metrics to identify the **best** times to buy LEAPS options:

### Scoring Components (Total: 100 points)

**1. Vega Score (35 points max)**
- Rewards **LOW vega** (less volatility exposure)
- Deep ITM options have low vega = stable pricing

| Vega Range | Score | Rating |
|-----------|-------|--------|
| ≤ 0.05 | 35 | Excellent - very low vega |
| 0.05-0.10 | 30 | Good - low vega |
| 0.10-0.15 | 20 | Acceptable - moderate vega |
| 0.15-0.25 | 10 | Fair - higher vega (ATM range) |
| > 0.25 | 0 | Poor - too high vega |

**2. IV Rank Score (40 points max)**
- Rewards **LOW IV rank** (cheap volatility)
- Best opportunities when IV is below its typical range

| IV Rank | Score | Rating | Badge Color |
|---------|-------|--------|-------------|
| < 0.20 | 40 | Excellent - very cheap volatility | 🟢 Green |
| 0.20-0.30 | 35 | Good - cheap volatility | 🟢 Green |
| 0.30-0.50 | 20 | Acceptable - fair volatility | 🟡 Yellow |
| 0.50-0.70 | 10 | Poor - expensive volatility | 🔴 Red |
| > 0.70 | 0 | Avoid - very expensive volatility | 🔴 Red |

**3. IV Percentile Score (25 points max)**
- Rewards **LOW IV percentile** (below average IV)
- Better to buy when IV is lower than usual

| IV Percentile | Score | Rating |
|--------------|-------|--------|
| < 20% | 25 | Excellent - very low IV |
| 20-30% | 20 | Good - low IV |
| 30-50% | 12 | Acceptable - moderate IV |
| 50-70% | 5 | Poor - high IV |
| > 70% | 0 | Avoid - very high IV |

## Score Interpretation

| Opportunity Score | Badge Color | Meaning |
|------------------|-------------|---------|
| **75-100** | 🟢 Green | **BEST OPPORTUNITY** - Low vega + cheap volatility |
| **50-74** | 🟡 Yellow | **FAIR OPPORTUNITY** - Moderate conditions |
| **0-49** | 🔴 Red | **POOR OPPORTUNITY** - High vega or expensive volatility |

## Examples

### Example 1: BEST Opportunity (Score: 90)
```
Vega: 0.05         → 35 points
IV Rank: 0.25      → 35 points
IV Percentile: 25% → 20 points
─────────────────────────────────
Total: 90/100 🟢 GREEN

Analysis: Deep ITM option with low vega during cheap volatility period
Recommendation: EXCELLENT buying opportunity
```

### Example 2: FAIR Opportunity (Score: 62)
```
Vega: 0.12         → 20 points
IV Rank: 0.45      → 20 points
IV Percentile: 55% → 12 points
─────────────────────────────────
Total: 52/100 🟡 YELLOW

Analysis: Moderate vega with fair volatility
Recommendation: Acceptable, but not ideal
```

### Example 3: POOR Opportunity (Score: 15)
```
Vega: 0.28         → 0 points
IV Rank: 0.75      → 0 points
IV Percentile: 85% → 5 points
─────────────────────────────────
Total: 5/100 🔴 RED

Analysis: High vega during expensive volatility period
Recommendation: AVOID - wait for better entry
```

## How to Use

### In the Scanner:

1. **Rank By dropdown:** Select "Opportunity Score (Best to Worst)"
   - This becomes the default ranking method
   - Shows top opportunities first

2. **Table Display:**
   - Two score columns shown side-by-side:
     - **Opportunity** - Volatility value (this guide)
     - **Quality** - Liquidity/spread quality

3. **Color Coding:**
   - Green badge (≥75): Best opportunities
   - Yellow badge (50-74): Fair opportunities
   - Red badge (<50): Poor opportunities

### For Deep ITM LEAPS:

**Target Settings:**
```
Delta: 0.85 - 0.98
Max Vega: 0.10
Max IV Rank: 0.30
IV Percentile: 0 - 40%
Rank By: Opportunity Score

Result: Top 10 deep ITM options with best volatility value
```

**Expected Scores:**
- Excellent: 80-100 (low vega + cheap IV)
- Good: 65-79 (low vega + fair IV)
- Poor: <65 (high vega or expensive IV)

### For ATM LEAPS:

**Target Settings:**
```
Delta: 0.45 - 0.60
Min Vega: 0.15
Max IV Rank: 0.40
IV Percentile: 0 - 50%
Rank By: Opportunity Score

Result: Top 10 ATM options with best volatility value
```

**Expected Scores:**
- Excellent: 65-85 (moderate vega + cheap IV)
- Good: 45-64 (moderate vega + fair IV)
- Poor: <45 (high vega or expensive IV)

## Trading Strategy

### BEST Times to Buy (Green Score):
✅ Opportunity Score ≥ 75
✅ Low vega (stable pricing)
✅ Low IV rank (cheap volatility)
✅ Low IV percentile (below average IV)

**Action:** Buy LEAPS confidently - you're getting good value

### WAIT for Better Entry (Red Score):
❌ Opportunity Score < 50
❌ High vega (volatile pricing)
❌ High IV rank (expensive volatility)
❌ High IV percentile (elevated IV)

**Action:** Wait for IV to drop - avoid overpaying for volatility

## Key Differences from Quality Score

| Metric | Opportunity Score | Quality Score |
|--------|------------------|---------------|
| **Focus** | Volatility value | Liquidity quality |
| **Measures** | Vega + IV rank + IV percentile | Volume + OI + spread + delta |
| **Best for** | Finding cheap volatility | Finding liquid options |
| **Use when** | Entering new positions | Any time |

**Recommendation:** Use **Opportunity Score** for best entry timing!

## Summary

The Opportunity Score answers: **"Is NOW a good time to buy this LEAPS option?"**

- **High score (green):** Great time - cheap volatility
- **Medium score (yellow):** Okay time - fair volatility
- **Low score (red):** Bad time - expensive volatility

**Always prefer green scores for new positions!**
