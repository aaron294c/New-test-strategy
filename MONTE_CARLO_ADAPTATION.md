# Monte Carlo Adaptation for RSI-MA Percentile Strategy

## 📊 Overview

This document explains how the Monte Carlo simulation has been specifically tailored for your RSI-MA percentile mean-reversion strategy (not just generic price forecasting).

---

## 🎯 Traditional Monte Carlo vs. Your Strategy

### **Traditional Approach:**
```
Input: Current Price
Simulate: Future PRICES using Geometric Brownian Motion
Output: Price targets, profit/loss distributions
Assumption: Trending behavior (prices drift up/down)
```

### **Your Strategy's Approach:**
```
Input: Current RSI-MA Percentile Rank (0-100)
Simulate: Future PERCENTILE movements
Output: Percentile targets, mean-reversion timing
Assumption: Mean-reverting behavior (extremes revert to median)
```

---

## 🔬 Technical Adaptations

### 1. **Percentile-Based Drift Calculation**
```python
# NOT price drift:
price_drift = mean(log_returns)  # ❌ Wrong for your strategy

# INSTEAD - Percentile drift:
percentile_changes = percentile_series.diff()
percentile_drift = mean(percentile_changes)  # ✅ Correct
```

**Why?** RSI-MA percentiles use **arithmetic changes** (50 → 55 = +5%), not geometric returns. Mean-reverting systems don't compound like prices.

### 2. **Mean-Reverting Volatility**
```python
# Your volatility represents:
volatility = std(percentile_changes)
```

**Key Insight:** When RSI-MA is at 5th percentile:
- **Upward drift dominates** (mean reversion pulls it toward 50th percentile)
- **Downside is bounded** (can't go much below 0)
- This asymmetry is captured in the drift term

### 3. **Target Percentiles = Your Entry/Exit Levels**
```python
target_percentiles = [5, 15, 25, 50, 75, 85, 95]
```

**Why these specific levels?**
- **5th, 15th**: Your entry thresholds (oversold)
- **50th**: Median (mean reversion target)
- **85th, 95th**: Your exit thresholds (overbought)

These aren't arbitrary - they match your backtest thresholds!

### 4. **First Passage Time (FPT) Analysis**
```python
for each simulation:
    for day in 1 to 21:
        if percentile >= target:
            record time_to_target
            break
```

**What it tells you:**
- **Median days to 50th percentile** = Expected mean reversion time
- **Probability of reaching 5th percentile** = Entry opportunity likelihood
- **Probability of reaching 95th percentile** = Exit opportunity likelihood

### 5. **First Hit Rate = Directional Bias**
```python
upside_targets = [50, 75, 85, 95]  # Above current
downside_targets = [5, 15, 25]      # Below current

upside_probability = mean([fpt[t].probability for t in upside_targets])
downside_probability = mean([fpt[t].probability for t in downside_targets])

bias = "bullish" if upside_probability > downside_probability else "bearish"
```

**Example:**
- Current percentile: 12th (oversold)
- Upside probability: 85% (likely to hit 50th before 5th)
- Downside probability: 15% (unlikely to go lower)
- **Bias: BULLISH ↑** (Mean reversion expected)

### 6. **Fan Chart = Confidence Bands**
```python
for each day:
    50% CI = percentile range covering middle 50% of simulations
    68% CI = percentile range covering middle 68% of simulations
    95% CI = percentile range covering middle 95% of simulations
```

**Not shown:** Future prices (which could be anywhere)  
**Instead shown:** Future percentile ranges (bounded 0-100, mean-reverting)

---

## 📈 How Simulation Works Step-by-Step

### **Initialization**
```python
current_percentile = 12.5  # Example: Oversold condition
drift = +0.2               # Calculated from historical percentile changes
volatility = 3.5           # Standard deviation of percentile changes
```

### **Each Simulation Path (1000x)**
```python
percentile = 12.5  # Starting point

for day in 1 to 21:
    # Random walk with drift
    random_shock = random_normal(0, 1)
    change = drift + (volatility × random_shock)
    
    percentile = percentile + change
    percentile = max(0, min(100, percentile))  # Bounded [0, 100]
    
    # Check if any target hit
    if percentile >= 50:
        first_passage_time[50] = day
```

### **Aggregation Across All Simulations**
```python
# For 50th percentile target:
times = [12, 8, 15, 11, 9, ...]  # 1000 values

median_time = median(times) = 10.5 days
probability = (times with values / 1000) × 100 = 92%
```

---

## 🎨 Visualization Mapping

### **Fan Chart Colors**
```
95% CI (lightest) ─────┐
68% CI (medium)   ─────┤  All possible paths
50% CI (darker)   ─────┘
Median (thick line) ───── Most likely path
```

**Interpretation:**
- **Narrow bands** = High confidence in mean reversion
- **Wide bands** = Uncertain/volatile percentile movement
- **Upward sloping median** = Bullish bias
- **Downward sloping median** = Bearish bias

### **First Passage Cards**
Each card shows:
```
┌─────────────────────┐
│ 50th Percentile     │ ← Target
│ 10.5 days           │ ← Median time to reach
│ 92%                 │ ← Probability of reaching in 21 days
│ Range: 7-14 days    │ ← 25th-75th percentile range
└─────────────────────┘
```

**Color coding:**
- 🟢 Green border: Entry zones (≤15th percentile)
- 🔴 Red border: Exit zones (≥85th percentile)
- ⚪ Gray border: Neutral zones

---

## 💡 Strategic Use Cases

### **Scenario 1: Currently at 8th Percentile (Deep Oversold)**
```
Monte Carlo shows:
- 50th percentile: 8.2 days (95% probability)
- 75th percentile: 12.1 days (78% probability)
- Directional Bias: BULLISH ↑ (88% upside)
```

**Action:** Strong entry signal - high probability of mean reversion

### **Scenario 2: Currently at 92nd Percentile (Overbought)**
```
Monte Carlo shows:
- 50th percentile: 9.5 days (91% probability)
- 25th percentile: 15.3 days (65% probability)
- Directional Bias: BEARISH ↓ (82% downside)
```

**Action:** Exit signal - likely to revert downward

### **Scenario 3: Currently at 48th Percentile (Neutral)**
```
Monte Carlo shows:
- 75th percentile: 11.2 days (48% probability)
- 25th percentile: 10.8 days (52% probability)
- Directional Bias: NEUTRAL ↔ (50/50 split)
```

**Action:** Wait for better entry/exit setup

---

## 🔍 Key Differences from Price-Based Monte Carlo

| Aspect | Price Monte Carlo | Your Percentile Monte Carlo |
|--------|------------------|----------------------------|
| **Input** | Current price ($158.32) | Current percentile (12.5%) |
| **Simulation** | Geometric Brownian Motion | Arithmetic random walk |
| **Bounds** | Unbounded (0 to ∞) | Bounded (0 to 100) |
| **Drift Interpretation** | Trend direction | Mean reversion strength |
| **Volatility** | Price volatility | Percentile volatility |
| **Target** | Price levels | Percentile thresholds |
| **Assumption** | Trending/random | Mean-reverting |
| **Output** | Future prices | Time to percentile targets |

---

## 📊 Mathematical Foundation

### **Simulation Equation**
```
P(t+1) = P(t) + μ + σ × ε

Where:
P(t) = Percentile rank at time t
μ = Historical drift (mean percentile change per day)
σ = Historical volatility (std dev of percentile changes)
ε ~ N(0,1) = Random normal shock
```

**Bounded by:**
```
P(t) ∈ [0, 100]
```

### **Why This Works for Mean Reversion**
When current percentile is low (e.g., 10):
- Historical drift μ > 0 (tendency to rise)
- Lower bound at 0 prevents further extreme drops
- **Result:** Asymmetric distribution favoring upside

When current percentile is high (e.g., 90):
- Historical drift μ < 0 (tendency to fall)
- Upper bound at 100 prevents further extreme rises
- **Result:** Asymmetric distribution favoring downside

---

## 🎯 Alignment with Your Strategy

Your strategy's core thesis:
> "When RSI-MA percentile is extremely low (<15%), there's high probability of mean reversion within 21 days"

Monte Carlo validates this by:
1. ✅ Quantifying **median time** to reversion (e.g., 10 days)
2. ✅ Calculating **probability** of reaching target (e.g., 92%)
3. ✅ Showing **confidence bands** around expected path
4. ✅ Providing **directional bias** for current position
5. ✅ Comparing **upside vs downside** probabilities

---

## 🚀 How to Use in Trading

1. **Check Current Position:**
   - Look at RSI-MA chip (⭐ RSI-MA: 12.3)
   - Note percentile (Extreme Low <5%)

2. **Open Monte Carlo Tab:**
   - View Directional Bias card
   - Check First Passage Times for 50th percentile

3. **Make Decision:**
   ```
   If:
   - Current percentile < 15% AND
   - Directional Bias = BULLISH AND
   - 50th percentile probability > 85%
   
   Then:
   - ENTER position
   - Expected mean reversion: ~10 days
   - Target exit: When percentile > 75%
   ```

4. **Monitor Exit:**
   - When position is profitable and percentile > 85%
   - Check if downside probability > 70%
   - If yes, EXIT and take profits

---

## 📚 Summary

**What makes this Monte Carlo special:**
1. ✅ Percentile-based (not price-based)
2. ✅ Mean-reverting (not trending)
3. ✅ Bounded [0,100] (not unbounded)
4. ✅ Aligned with your entry/exit thresholds
5. ✅ Shows TIME to targets (not just probabilities)
6. ✅ Provides actionable directional bias

**It answers:**
- ❓ "How long until mean reversion?" → First Passage Times
- ❓ "Should I enter here?" → Directional Bias
- ❓ "What's the probability of profit?" → Upside Probability %
- ❓ "When should I exit?" → When percentile hits overbought zone with bearish bias

This is a **forward-looking complement** to your backward-looking backtests! 🎯
