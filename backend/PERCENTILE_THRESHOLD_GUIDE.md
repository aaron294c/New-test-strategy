# Percentile Threshold Guide

## Overview

This document explains how to use the **Percentile Threshold Analysis** to make data-driven trading decisions based on historical RSI-MA percentile combinations for Daily and 4-Hourly timeframes.

## What This Analysis Shows

The analysis answers the critical question:

> **"IF Daily RSI-MA is at X% AND 4H RSI-MA is at Y%, what should I do based on historical performance?"**

## The 4 Divergence Categories

### 1. **4H Overextended** (Daily Low, 4H High)

**Condition:**
- Daily RSI-MA percentile < 50%
- 4H RSI-MA percentile > Daily
- Divergence < -15% (negative, meaning 4H ahead)

**What This Means:**
- The 4-hourly timeframe has spiked up while daily is still low
- 4H is "overextended" relative to daily
- Likely to pull back toward daily levels (mean reversion)

**Historical Performance (GOOGL Example):**
- Sample Size: 26 events
- Typical Daily Range: 19-42% (median 31.5%)
- Typical 4H Range: 49-74% (median 56.2%)
- Typical Divergence: -23% to -32% (median -27.4%)

**Action:**
- **Weak** (divergence -15% to -25%): Take 25% profit
- **Moderate** (divergence -25% to -35%): Take 50% profit
- **Strong** (divergence > -35%): Take 75% profit

**Example:**
```
Daily: 30%
4H: 75%
Divergence: -45%
Action: TAKE 75% PROFIT - Strong 4H overextension
```

---

### 2. **Bullish Convergence** (Both Low)

**Condition:**
- Daily RSI-MA percentile < 30%
- 4H RSI-MA percentile < 30%
- Divergence between -15% and +15% (aligned)

**What This Means:**
- Both timeframes are oversold and aligned
- Convergence at low levels = bounce opportunity
- Mean reversion to the upside expected

**Historical Performance (GOOGL Example):**
- Sample Size: 56 events
- Typical Daily Range: 9-20% (median 15.9%)
- Typical 4H Range: 9-24% (median 16.3%)
- Average D7 Return: **+2.76%**
- Win Rate D7: **74.4%**

**Action:**
- **BUY or ADD to position**

**Example:**
```
Daily: 15%
4H: 14%
Divergence: +1%
Action: BUY/ADD - Both oversold and aligned, bounce expected
Average Expected Return (D7): +2.76%
```

---

### 3. **Daily Overextended** (Daily High, 4H Low)

**Condition:**
- Daily RSI-MA percentile > 50%
- 4H RSI-MA percentile < Daily
- Divergence > +15% (positive, meaning Daily ahead)

**What This Means:**
- Daily timeframe is elevated but 4H is not confirming
- Daily is "overextended" without 4H support
- Reversal likely (mean reversion down)

**Historical Performance (GOOGL Example):**
- Sample Size: 46 events
- Typical Daily Range: 61-84% (median 76.4%)
- Typical 4H Range: 38-58% (median 48.2%)
- Optimal Thresholds:
  - Weak: < 25% divergence
  - Moderate: 25-35% divergence
  - Strong: > 35% divergence

**Action:**
- **Weak** (divergence +15% to +25%): Tighten stops
- **Moderate** (divergence +25% to +35%): Reduce 50%
- **Strong** (divergence > +35%): Exit or Short

**Example:**
```
Daily: 75%
4H: 35%
Divergence: +40%
Action: EXIT OR SHORT - Strong daily overextension
```

---

### 4. **Bearish Convergence** (Both High)

**Condition:**
- Daily RSI-MA percentile > 70%
- 4H RSI-MA percentile > 70%
- Divergence between -15% and +15% (aligned)

**What This Means:**
- Both timeframes are overbought and aligned
- Convergence at high levels = reversal imminent
- Mean reversion down expected

**Historical Performance (GOOGL Example):**
- Sample Size: 45 events
- Typical Daily Range: 77-96% (median 86.1%)
- Typical 4H Range: 79-93% (median 86.5%)

**Action:**
- **EXIT ALL or SHORT**

**Example:**
```
Daily: 86%
4H: 87%
Divergence: -1%
Action: EXIT ALL/SHORT - Both overbought and aligned, reversal likely
```

---

## How to Use This Analysis

### Step 1: Check Current Percentiles

Look at the current Daily and 4H RSI-MA percentiles for your ticker.

### Step 2: Identify Category

Determine which of the 4 categories the current state falls into:

- Daily < 50% + 4H > Daily + Div < -15% → **4H Overextended**
- Daily < 30% + 4H < 30% + |Div| < 15% → **Bullish Convergence**
- Daily > 50% + 4H < Daily + Div > +15% → **Daily Overextended**
- Daily > 70% + 4H > 70% + |Div| < 15% → **Bearish Convergence**

### Step 3: Check Divergence Strength

Look at the magnitude of divergence to determine strength (weak/moderate/strong).

### Step 4: Take Action

Follow the recommended action based on the category and strength.

### Step 5: Monitor

Use the Decision Matrix to see historical performance for similar setups.

---

## Decision Matrix Examples (GOOGL)

### Bullish Convergence Examples

| Daily Range | 4H Range | Avg Div | Sample Size | Avg D7 Return | Win Rate D7 |
|-------------|----------|---------|-------------|---------------|-------------|
| 0-20%       | 0-20%    | +1.4%   | 28          | **+3.21%**    | **71.4%**   |
| 0-30%       | 0-30%    | -1.0%   | 43          | **+2.76%**    | **74.4%**   |
| 20-30%      | 20-35%   | -2.0%   | 8           | +0.53%        | 50.0%       |

**Insight:** The tighter the convergence at low levels, the better the returns. Daily 0-20% + 4H 0-20% has 71.4% win rate with +3.21% avg return.

### 4H Overextended Example

| Daily Range | 4H Range | Avg Div | Sample Size | Avg D7 Return | Win Rate D7 |
|-------------|----------|---------|-------------|---------------|-------------|
| 30-50%      | 70-100%  | -32.1%  | 6           | +0.35%        | 33.3%       |

**Insight:** When daily is mid-range (30-50%) but 4H spikes to 70-100%, there's -32% divergence. This is a take-profit signal.

### Daily Overextended Examples

| Daily Range | 4H Range | Avg Div | Sample Size | Avg D7 Return | Win Rate D7 |
|-------------|----------|---------|-------------|---------------|-------------|
| 60-100%     | 0-40%    | +38.8%  | 5           | +3.25%        | 80.0%       |
| 70-100%     | 30-50%   | +34.2%  | 10          | +0.84%        | 60.0%       |

**Insight:** When daily is elevated (60-100%) but 4H is lagging (0-40%), divergence is extreme (+38.8%). This is a reversal signal.

### Bearish Convergence Examples

| Daily Range | 4H Range | Avg Div | Sample Size | Avg D7 Return | Win Rate D7 |
|-------------|----------|---------|-------------|---------------|-------------|
| 70-100%     | 70-100%  | +0.1%   | 41          | +1.12%        | 61.0%       |
| 75-100%     | 75-100%  | +0.2%   | 32          | -0.40%        | 53.1%       |
| 80-100%     | 70-100%  | +2.9%   | 27          | +0.20%        | 55.6%       |

**Insight:** When both are extremely overbought (75-100% each), average returns turn negative (-0.40%), signaling exit.

---

## Grid Analysis - Top Performing Combinations

The grid shows **all tested combinations** ranked by sample size. Here are the most significant:

### Best Long Setups (Highest Positive Returns)

1. **Daily 0-20% + 4H 0-20%**: +3.21% avg D7, 71.4% win rate (n=28)
2. **Daily 0-30% + 4H 0-30%**: +2.76% avg D7, 74.4% win rate (n=43)
3. **Daily 70-80% + 4H 70-80%**: +7.16% avg D7, 100% win rate (n=6) ⚠️ Small sample

### Best Short/Exit Signals

1. **Daily 75-100% + 4H 75-100%**: -0.40% avg D7, 53.1% win rate (n=32)
2. **Daily 80-100% + 4H 60-70%**: -1.77% avg D7, 14.3% win rate (n=7)

---

## Key Insights

### 1. Convergence at Extremes is Powerful

- **Low convergence** (both 0-30%): 74.4% win rate, +2.76% avg return
- **High convergence** (both 75-100%): Negative returns, exit signal

### 2. Divergence Magnitude Matters

- **Strong divergence** (>35%): Highest conviction signals
- **Weak divergence** (<15%): Less reliable, monitor

### 3. Sample Size Reliability

- **High confidence**: n > 20
- **Moderate confidence**: n = 10-20
- **Low confidence**: n < 10 (use with caution)

### 4. Mean Reversion is Real

- 4H Overextended → 4H pulls back
- Daily Overextended → Daily reverses
- Convergence at extremes → Reversal

---

## How to Access This Analysis

### Via API

```bash
GET http://localhost:8000/api/percentile-thresholds/{ticker}
```

Returns:
- Percentile distributions by category
- Optimal thresholds for each category
- Decision matrix
- Grid analysis

### Via Frontend

1. Navigate to **Multi-Timeframe Divergence** tab
2. Click on **📊 Percentile Thresholds** sub-tab
3. View the complete analysis with visual tables

---

## Example Trading Workflow

### Scenario: Checking GOOGL

1. **Get Current State**
   - Daily: 25%
   - 4H: 18%
   - Divergence: +7%

2. **Identify Category**
   - Both < 30% ✓
   - |Divergence| < 15% ✓
   - Category: **Bullish Convergence**

3. **Check Historical Performance**
   - Daily 20-30% + 4H 20-35%: +0.53% avg D7, 50% win rate (n=8)
   - Daily 0-30% + 4H 0-30%: +2.76% avg D7, 74.4% win rate (n=43)

4. **Action**
   - **BUY/ADD**: Both oversold and aligned
   - Expected D7 Return: +2.76%
   - Win Probability: 74.4%

5. **Monitor**
   - Watch for 4H to rise above daily (would become 4H Overextended → take profit)
   - Watch for both to rise above 70% (would become Bearish Convergence → exit)

---

## Notes

- All percentiles are **rolling 252-day percentile ranks**
- Forward returns are calculated from the signal day (D0 = entry)
- D7 = 7 days after entry, D14 = 14 days, etc.
- Win rate = % of events with positive return at that horizon
- Mean reversion rate = % of events that moved in expected direction

---

## Next Steps

1. **Run the analysis** for your ticker of interest
2. **Monitor current percentiles** in real-time via the Live Signals tab
3. **Use the Decision Matrix** to look up similar historical setups
4. **Execute trades** based on category + strength + historical performance
5. **Track results** and refine thresholds over time

---

## Credits

Generated by `percentile_threshold_analyzer.py`
