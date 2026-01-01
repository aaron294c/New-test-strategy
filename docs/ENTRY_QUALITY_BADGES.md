# Entry Quality Badge System

## Overview

The **Entry Quality** badge tells you **WHEN to buy** LEAPS options based on a combination of IV Percentile and Vega. This is the most actionable metric for timing your entries.

## The Badge System

### 🟢 Excellent Entry
**Criteria:**
- IV Percentile < 30% (volatility is cheaper than 70% of historical days)
- Vega < 0.15 (very low volatility exposure - stock-like)

**What it means:**
- **This is the IDEAL time to buy!**
- Volatility is cheap historically
- Option behaves like stock (minimal vega risk)
- These opportunities are rare - act quickly when you see them

**Example:**
```
IV Percentile: 25% (75% of days had higher IV)
Vega: 0.12 (very stock-like)
Entry Quality: 🟢 Excellent Entry
```

---

### 🟢 Good Entry
**Criteria:**
- IV Percentile < 30% (cheap volatility)
- Vega 0.15-0.30 (moderate volatility exposure)

**What it means:**
- **Good buying opportunity**
- Volatility is cheap historically
- Some vega exposure, but acceptable
- These are strong entry points

**Example:**
```
IV Percentile: 28% (72% of days had higher IV)
Vega: 0.22 (moderate vega)
Entry Quality: 🟢 Good Entry
```

---

### 🟡 Fair Entry
**Criteria:**
- IV Percentile 30-60% (moderate volatility)
- Vega < 0.30 (low to moderate volatility exposure)

**What it means:**
- **Acceptable entry point, not ideal**
- Volatility is around median levels
- You're not getting a great deal on IV
- Consider waiting for better conditions if not urgent

**Example:**
```
IV Percentile: 45% (55% of days had higher IV)
Vega: 0.25 (acceptable vega)
Entry Quality: 🟡 Fair Entry
```

---

### 🟠 Caution
**Criteria:**
- IV Percentile 30-60% (moderate volatility)
- Vega 0.30-0.50 (higher volatility exposure)

**What it means:**
- **Consider waiting for better conditions**
- Volatility is not cheap
- Higher vega exposure increases risk
- Only buy if you have a strong directional conviction

**Example:**
```
IV Percentile: 55% (only 45% of days had higher IV)
Vega: 0.38 (higher vega)
Entry Quality: 🟠 Caution
```

---

### 🔴 Wait for Better
**Criteria:**
- IV Percentile > 60% (expensive volatility) OR
- Vega > 0.50 (very high volatility exposure)

**What it means:**
- **NOT a good time to buy - wait!**
- Volatility is more expensive than usual
- You're overpaying for the option
- High vega means more risk from IV changes
- **Patient traders wait for green badges**

**Example:**
```
IV Percentile: 72% (only 28% of days had higher IV)
Vega: 0.65 (very high vega)
Entry Quality: 🔴 Wait for Better
```

---

## How to Use This System

### For Long-Term LEAPS Investors:
1. **Only buy on 🟢 Excellent or 🟢 Good entries**
   - Wait for IV percentile < 30%
   - These entries have the best risk/reward

2. **Consider 🟡 Fair entries only if:**
   - You have strong directional conviction
   - You're willing to accept higher IV cost
   - You're averaging into a position

3. **AVOID 🔴 Wait for Better entries**
   - You're overpaying for volatility
   - Better opportunities will come
   - Patience is rewarded

### Real-World Scenarios:

**Scenario 1: Market Calm (VIX ~15%)**
```
Most deep ITM options will show:
Entry Quality: 🟢 Excellent Entry
IV Percentile: 15-25%
Vega: 0.10-0.20

Action: GREAT buying opportunity!
```

**Scenario 2: Market Elevated (VIX ~22%)**
```
Most deep ITM options will show:
Entry Quality: 🟡 Fair Entry
IV Percentile: 45-55%
Vega: 0.25-0.35

Action: Acceptable, but not ideal. Consider waiting.
```

**Scenario 3: Recent Volatility Spike (VIX was 30%, now 20%)**
```
Most deep ITM options will show:
Entry Quality: 🔴 Wait for Better
IV Percentile: 70-85% (20% is high relative to recent calm)
Vega: 0.30-0.60

Action: WAIT! IV needs to drop more first.
```

---

## Comparison with Other Metrics

### Entry Quality vs Opportunity Score:
- **Opportunity Score**: Measures how good the option characteristics are
- **Entry Quality**: Tells you WHEN to buy based on market conditions

You want BOTH:
- High Opportunity Score (40+) = Good option characteristics
- Green Entry Quality (Excellent/Good) = Good timing to buy

### Entry Quality vs Vega Risk:
- **Vega Risk**: Shows volatility exposure relative to IV rank
- **Entry Quality**: Shows when to buy based on IV percentile

They complement each other:
- Vega Risk = "What volatility exposure am I taking?"
- Entry Quality = "Is this a good time to take that exposure?"

---

## Current Market Reality (As of your screenshot):

**Your current options show:**
```
Entry Quality: 🔴 Wait for Better
IV Percentile: 72-89% (expensive!)
Vega: 0.30-0.80 (high!)

This means: The current market is NOT a good entry point.
VIX spent most of 2024 at 14-18%, but options are priced at 19-25%.
```

**What to do:**
1. Monitor the market daily
2. Wait for IV percentile to drop below 50%
3. Ideally wait for IV percentile below 30% (🟢 badges)
4. Set alerts for when green badges appear

---

## Summary

**The Entry Quality badge answers one critical question:**
### "Should I buy NOW, or WAIT for better conditions?"

- 🟢 **Green badges** = Buy NOW
- 🟡 **Yellow badges** = Buy only if necessary
- 🔴 **Red badges** = WAIT for better conditions

**Remember:** Patient traders who wait for green badges get better entries and better long-term returns. Don't chase red badge entries!
