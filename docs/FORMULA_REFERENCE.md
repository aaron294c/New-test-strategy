# Formula Reference Guide

Quick reference for all expectancy formulas with concrete examples.

---

## Per-Trade Definitions

### Trade Definition
```
Entry: When RSI-MA percentile ≤ 15% (0-5% or 5-15% bins)
Exit: When percentile ≥ 50% OR stop hit OR max hold (21 days)
Return: (ExitPrice - EntryPrice) / EntryPrice
```

---

## Basic Metrics (7-day lookback)

### Win Rate (7d)
```
W = # trades with return > 0 / N total trades

Example: 13 wins out of 20 trades
W = 13 / 20 = 0.65 = 65%
```

### Average Gain (7d)
```
G = Σ(positive returns) / # winning trades

Example: Returns = [+3.2%, +4.1%, +2.8%]
G = (3.2 + 4.1 + 2.8) / 3 = 3.37%
```

### Average Loss (7d)
```
L = |Σ(negative returns)| / # losing trades

Example: Returns = [-1.5%, -2.1%, -1.8%]
L = |(−1.5 − 2.1 − 1.8)| / 3 = 1.80%
```

### Expectancy Per Trade (7d)
```
E_trade = W · G − (1 − W) · L

Example: W=0.65, G=3.37%, L=1.80%
E_trade = 0.65 × 3.37 − 0.35 × 1.80
        = 2.19 − 0.63
        = +1.56% per trade
```

---

## Time-Normalized Metrics

### Average Holding Days (7d)
```
H = Σ(holding_days) / N trades

Example: Holdings = [7, 9, 6, 8, 10] days
H = (7 + 9 + 6 + 8 + 10) / 5 = 8 days
```

### Expectancy Per Day (7d)
```
E_per_day = E_trade / H

Example: E_trade = +1.56%, H = 8 days
E_per_day = 1.56 / 8 = +0.195% per day

This means you expect +0.195% return for each day you hold the position.
```

**Why This Matters:**
- Stock A: E_trade = +2.0% in 14 days → E_per_day = +0.143%/day
- Stock B: E_trade = +1.5% in 7 days → E_per_day = +0.214%/day
- **Stock B is better** despite lower per-trade expectancy!

---

## Risk-Adjusted Metrics

### Stop Distance (ATR-based)
```
Stop Distance = Avg(std_dev from entry bins) × ATR_multiplier

Example: Bin stds = [4.2%, 3.8%, 5.1%], multiplier = 2.0
Avg std = (4.2 + 3.8 + 5.1) / 3 = 4.37%
Stop Distance = 4.37 × 2.0 = 8.74%
```

### Expectancy Per 1% Risk
```
E_per_1%_risk = E_trade / Stop_Distance_%

Example: E_trade = +1.56%, Stop = 8.74%
E_per_1%_risk = 1.56 / 8.74 = +0.178%

This means you get +0.178% expected return per 1% you risk.
```

### Risk Per Trade
```
Risk_per_trade = Position_size × Stop_Distance

Example: $10,000 position, 8.74% stop
Risk = $10,000 × 0.0874 = $874
```

---

## Statistical Confidence

### Wilson Score Interval (Win Rate CI)

For win rate W from n trades, 95% confidence interval:

```
z = 1.96 (for 95% confidence)
center = (W + z²/(2n)) / (1 + z²/n)
margin = z × √[(W(1−W)/n + z²/(4n²))] / (1 + z²/n)

Lower = center − margin
Upper = center + margin

Example: 13 wins out of 20 trades (W = 0.65)
center = (0.65 + 3.84/40) / 1.192 = 0.627
margin = 1.96 × √[(0.65×0.35/20 + 0.96/1600)] / 1.192 = 0.195

CI = [0.432, 0.822] = [43.2%, 82.2%]

Interpretation: We're 95% confident the true win rate is between 43.2% and 82.2%
```

### Bootstrap CI (Expectancy CI)

10,000 iterations of resampling with replacement:

```
For i = 1 to 10,000:
  1. Resample n trades with replacement
  2. Calculate E_trade for this sample
  3. Store result

Sort all 10,000 expectancies
Lower = 2.5th percentile (250th value)
Upper = 97.5th percentile (9,750th value)

Example: E_trade = +1.56%
Bootstrap results sorted: [−0.2%, ..., +1.56%, ..., +3.1%]
CI = [+0.82%, +2.48%]

Interpretation: We're 95% confident the true expectancy is between +0.82% and +2.48%
```

### Confidence Score (0-1)
```
CI_confidence = max(0, 1 − CI_width / |E_trade|)
sample_confidence = min(1.0, n / 30)

Confidence = 0.7 × CI_confidence + 0.3 × sample_confidence

Example: E_trade = +1.56%, CI = [+0.82%, +2.48%], n = 18
CI_width = 2.48 − 0.82 = 1.66
CI_confidence = 1 − 1.66/1.56 = 0 (capped at 0)
sample_confidence = 18 / 30 = 0.60

Confidence = 0.7 × 0 + 0.3 × 0.60 = 0.18 = 18%

(Note: Wide CI reduces confidence)
```

---

## Holding Period Analysis

### Optimal Holding Day
```
For each day d from 1 to 30:
  Calculate mean return for all trades held ≥ d days

optimal_day = day with maximum mean return

Example:
Day 1: +0.5%  Day 5: +1.8%  Day 9: +2.1%
Day 2: +1.0%  Day 6: +2.0%  Day 10: +2.2%  ← Maximum
Day 3: +1.3%  Day 7: +2.1%  Day 11: +2.1%
Day 4: +1.5%  Day 8: +2.1%  Day 12: +2.0%

Optimal = Day 10
```

### Diminishing Returns Day
```
For each day d starting from 2:
  marginal_gain[d] = return[d] − return[d−1]

  If marginal_gain[d] < 0.10 × marginal_gain[d−1]:
    diminishing_day = d
    break

Example:
Day 7→8: +0.3% gain
Day 8→9: +0.2% gain
Day 9→10: +0.1% gain ← 0.1 < 0.10 × 0.2 = FALSE
Day 10→11: +0.02% gain ← 0.02 < 0.10 × 0.1 = TRUE

Diminishing Returns Day = 11
```

---

## Composite Scoring

### Component Normalization

**Expectancy Normalization:**
```
E_norm = (E_per_day + 1%) / 2%

Assumes E_per_day ranges from −1% to +1%
Maps to 0-1 scale

Example: E_per_day = +0.195%
E_norm = (0.195 + 1.0) / 2.0 = 0.598
```

**Confidence Normalization:**
```
C_norm = confidence_score (already 0-1)

Example: confidence = 0.825
C_norm = 0.825
```

**Percentile Normalization:**
```
If current_percentile ≤ 50:
  P_norm = 1 − (current_percentile / 50)
Else:
  P_norm = 0

Example: percentile = 10%
P_norm = 1 − (10 / 50) = 0.80
```

### Final Composite Score

```
α₁ = 0.60 (expectancy weight)
α₂ = 0.25 (confidence weight)
α₃ = 0.15 (percentile weight)

Composite = α₁ × E_norm + α₂ × C_norm + α₃ × P_norm

Example:
E_norm = 0.598, C_norm = 0.825, P_norm = 0.80

Expectancy_contribution = 0.60 × 0.598 = 0.359 (35.9%)
Confidence_contribution = 0.25 × 0.825 = 0.206 (20.6%)
Percentile_contribution = 0.15 × 0.80 = 0.120 (12.0%)

Composite Score = 0.685 (68.5%)
```

**Interpretation:**
> "This stock ranks high because:
> - Expectancy contributes 35.9% (60% weight × 0.598 normalized value)
> - Confidence contributes 20.6% (25% weight × 0.825 normalized value)
> - Percentile extremeness contributes 12.0% (15% weight × 0.80 normalized value)
> - Total ranking score: 68.5%"

---

## Capital Allocation

### Proportional Allocation

```
For top 5 stocks by composite score:

Total_scores = Σ(composite_scores of top 5)
Allocation_pct[i] = composite_score[i] / Total_scores
Allocation_amount[i] = Total_capital × Allocation_pct[i]

Example: $100,000 total capital, top 5 scores = [0.685, 0.621, 0.587, 0.543, 0.501]
Total_scores = 2.937

Stock 1: 0.685 / 2.937 = 23.3% → $23,300
Stock 2: 0.621 / 2.937 = 21.2% → $21,200
Stock 3: 0.587 / 2.937 = 20.0% → $20,000
Stock 4: 0.543 / 2.937 = 18.5% → $18,500
Stock 5: 0.501 / 2.937 = 17.1% → $17,100
Total: 100.1% ≈ $100,100 (rounding)
```

### Risk Amount
```
Risk_amount[i] = Allocation[i] × Stop_Distance_%

Example: Stock 1
Allocation = $23,300, Stop = 8.74%
Risk = $23,300 × 0.0874 = $2,036
```

### Expected Return
```
Expected_return = E_per_day × Optimal_holding_days

Example: E_per_day = +0.195%, Optimal = 10 days
Expected = 0.195 × 10 = +1.95%

On $23,300 position: $23,300 × 0.0195 = $454 expected profit
```

---

## Regime Conditional

### Separate Expectancy Calculation

```
Filter trades by regime:
  mean_reversion_trades = trades where regime = 'mean_reversion'
  momentum_trades = trades where regime = 'momentum'

Calculate expectancy for each:
  E_MR = W_MR × G_MR − (1 − W_MR) × L_MR
  E_Mom = W_Mom × G_Mom − (1 − W_Mom) × L_Mom

Example:
Mean Reversion: 10 trades, W=0.70, G=3.8%, L=1.5%
E_MR = 0.70 × 3.8 − 0.30 × 1.5 = 2.66 − 0.45 = +2.21%

Momentum: 8 trades, W=0.625, G=3.1%, L=2.0%
E_Mom = 0.625 × 3.1 − 0.375 × 2.0 = 1.94 − 0.75 = +1.19%

Interpretation: Strategy works better in mean reversion (+2.21%) than momentum (+1.19%)
```

---

## Complete Example

### NVDA at 10th Percentile

**Input Data:**
- 18 simulated trades from bin statistics
- 13 wins, 5 losses
- Winning returns: [+2.8%, +3.9%, +3.2%, +4.5%, +2.1%, +3.7%, +4.2%, +3.0%, +2.9%, +3.5%, +4.0%, +3.1%, +2.7%]
- Losing returns: [−1.8%, −2.1%, −1.5%, −2.3%, −1.9%]
- Holding days: [7, 9, 6, 8, 10, 7, 8, 9, 7, 6, 8, 9, 7, 10, 9, 8, 7, 8]
- Avg std from entry bins: 4.37%

**Calculations:**

1. **Win Rate**:
   - W = 13 / 18 = 0.722 = 72.2%
   - Wilson CI = [52.7%, 86.5%]

2. **Avg Win/Loss**:
   - G = (2.8+3.9+3.2+4.5+2.1+3.7+4.2+3.0+2.9+3.5+4.0+3.1+2.7) / 13 = 3.35%
   - L = |(-1.8-2.1-1.5-2.3-1.9)| / 5 = 1.92%

3. **Expectancy Per Trade**:
   - E_trade = 0.722 × 3.35 − 0.278 × 1.92
   - E_trade = 2.42 − 0.53 = +1.89%
   - Bootstrap CI = [+0.95%, +2.98%]

4. **Holding Period**:
   - H = (7+9+6+8+10+7+8+9+7+6+8+9+7+10+9+8+7+8) / 18 = 7.94 days

5. **Expectancy Per Day**:
   - E_per_day = 1.89 / 7.94 = +0.238% per day

6. **Stop Distance**:
   - Stop = 4.37 × 2.0 = 8.74%

7. **E per 1% Risk**:
   - E_per_1%_risk = 1.89 / 8.74 = +0.216%

8. **Confidence**:
   - CI_width = 2.98 − 0.95 = 2.03
   - CI_confidence = 1 − 2.03/1.89 = 0 (wide CI)
   - sample_confidence = 18 / 30 = 0.60
   - Confidence = 0.7 × 0 + 0.3 × 0.60 = 18%

9. **Composite Score**:
   - E_norm = (0.238 + 1.0) / 2.0 = 0.619
   - C_norm = 0.18
   - P_norm = 1 − (10 / 50) = 0.80
   - E_contrib = 0.60 × 0.619 = 0.371 (37.1%)
   - C_contrib = 0.25 × 0.18 = 0.045 (4.5%)
   - P_contrib = 0.15 × 0.80 = 0.120 (12.0%)
   - **Composite = 0.536 (53.6%)**

**Result Summary:**
- Rank: #2 (moderate composite due to low confidence from wide CI)
- Primary driver: Expectancy (37.1% contribution)
- Strategy applicable: YES (+1.89% per trade in mean reversion zones)

---

**All formulas with time frame labels and concrete examples! ✅**
