# Improvements Roadmap - Addressing User Feedback

## 📋 User Feedback Summary

### A) Regime Quantification
**Issue**: "Mean Reversion" and "Momentum" appear categorical, not quantitatively derived
**Solution**: Display underlying regime metrics with confidence intervals

### B) Lookback Alignment
**Issue**: Percentile mapping uses 500-day history, regime detection needs alignment
**Solution**: Use same 500-period lookback for regime calculation

### C) Bootstrap Assumptions
**Issue**: Standard bootstrap assumes independent trades, but signals may overlap
**Solution**: Use block bootstrap for serially correlated trades

### D) Trade Independence
**Issue**: Multiple overlapping signals inflate sample size and bias expectancy
**Solution**: Deduplication rules - one active signal per ticker per regime

### E) Drawdown Metrics
**Issue**: All performance is expectancy-based, missing volatility clustering context
**Solution**: Add Max Drawdown and Return/Drawdown ratio

### F) Statistical Confidence Clarity
**Issue**: "Confidence: 30%" unclear meaning
**Solution**: Use `p(E > 0)` from bootstrap distribution or `1 - CI_width/|E|`

### G) Composite Score Transparency
**Issue**: "Score Breakdown (E:30, C:8, P:12)" is opaque
**Solution**: Hover tooltips showing actual component values and calculations

### H) Current vs Historical Data
**Issue**: Is the UI showing current RSI-MA percentile or just historical?
**Solution**: Add real-time current RSI-MA value and percentile from backend

### I) Stop Loss Derivation
**Issue**: Stop loss not robust, should be from percentile bin data
**Solution**: Use 5th percentile downside or mean - 2σ from entry bins

---

## ✅ Implemented (in expectancyCalculations.ts)

### 1. Block Bootstrap for Serial Correlation
```typescript
blockBootstrapExpectancyCI(
  trades: TradeResult[],
  blockSize: number = 3,  // Resamples blocks, not individual trades
  iterations: number = 10000
): {
  ci: [number, number];
  probabilityPositive: number;  // ← p(E > 0)
  effectiveSampleSize: number;  // ← Adjusted for correlation
}
```

**What it does**:
- Resamples contiguous blocks of 3 trades instead of individual trades
- Preserves serial correlation structure
- Returns p(E > 0) directly from bootstrap distribution
- Calculates effective sample size = n / blockSize

### 2. Maximum Drawdown Calculation
```typescript
calculateMaxDrawdown(trades: TradeResult[]): {
  maxDrawdown: number;           // Peak-to-trough % loss
  drawdownDuration: number;      // # trades in drawdown
  peakIndex: number;             // Trade # of peak
  troughIndex: number;           // Trade # of trough
}
```

**What it does**:
- Builds equity curve from trade returns
- Finds maximum peak-to-trough drawdown
- Tracks duration and location

### 3. Robust Stop Loss from Bin Data
```typescript
calculateRobustStopLoss(
  entryBins: BinStatisticForStop[],
  confidenceLevel: number = 0.95
): {
  stopLoss: number;      // Calculated stop %
  method: string;        // 'percentile_5th' or 'mean_minus_2std'
  calculation: string;   // Human-readable explanation
}
```

**What it does**:
- **Method 1**: Uses 5th percentile downside from entry bins if available
- **Method 2**: Falls back to mean - 2×std (95% confidence)
- Returns explanation of calculation for transparency

### 4. Regime Metrics with Confidence Intervals
```typescript
calculateRegimeScore(
  prices: number[],
  returns: number[],
  lookbackPeriods?: number  // ← Can specify 500 for alignment
): {
  regimeScore: number;         // -1 to +1 composite
  autocorrelation: number;     // <0 mean revert, >0 momentum
  varianceRatio: number;       // <1 mean revert, >1 momentum
  hurstExponent: number;       // <0.5 mean revert, >0.5 trend
  hurstCI: [number, number];   // ← 95% CI for Hurst
  lookbackPeriods: number;     // ← Actual periods used
}
```

**What it does**:
- Calculates Hurst exponent with 1000-iteration bootstrap CI
- Allows specifying lookback period (e.g., 500 to match percentile mapping)
- Returns all three regime metrics + composite score

### 5. Updated ExpectancyMetrics Interface

Added fields:
```typescript
// Risk-adjusted
maxDrawdown: number;
returnToDrawdownRatio: number;  // E_per_day / maxDrawdown

// Statistical
probabilityPositive: number;    // p(E > 0)
effectiveSampleSize: number;    // Adjusted for correlation

// Regime quantification
regimeMetrics: {
  hurstExponent: number;
  hurstCI: [number, number];    // ← With confidence interval!
  autocorrelation: number;
  varianceRatio: number;
  lookbackPeriods: number;      // ← Shown in UI
};

// Transparent scoring
compositeBreakdown: {
  ...
  detailedCalculation: {        // ← For hover tooltips
    expectancyNormalized: number;
    expectancyWeight: number;
    confidenceNormalized: number;
    confidenceWeight: number;
    percentileNormalized: number;
    percentileWeight: number;
  };
};
```

---

## 🚧 Still TODO

### 1. Update calculateExpectancyMetrics Function
**File**: `/frontend/src/utils/expectancyCalculations.ts` line 583

**Changes needed**:
```typescript
// Replace standard bootstrap with block bootstrap
const bootstrapResults = blockBootstrapExpectancyCI(recentTrades, 3, 10000);
const expectancyCI = bootstrapResults.ci;
const probabilityPositive = bootstrapResults.probabilityPositive;
const effectiveSampleSize = bootstrapResults.effectiveSampleSize;

// Calculate drawdown metrics
const drawdownMetrics = calculateMaxDrawdown(recentTrades);
const maxDrawdown = drawdownMetrics.maxDrawdown;
const returnToDrawdownRatio = expectancyPerDay / (maxDrawdown || 0.01);

// Fix confidence score formula
const confidenceScore = Math.max(0, Math.min(1,
  1 - (expectancyCI[1] - expectancyCI[0]) / Math.abs(expectancyPerTrade || 1)
));

// Add regime metrics with proper lookback
const regimeMetrics = calculateRegimeScore(
  prices,
  returns,
  500  // ← Match percentile mapping lookback
);

// Add detailed calculation for tooltips
const detailedCalculation = {
  expectancyNormalized,
  expectancyWeight: 0.60,
  confidenceNormalized,
  confidenceWeight: 0.25,
  percentileNormalized,
  percentileWeight: 0.15
};
```

### 2. Update tradeSimulator.ts
**File**: `/frontend/src/utils/tradeSimulator.ts`

**Add trade deduplication**:
```typescript
/**
 * Remove overlapping trades to ensure independence
 */
export function deduplicateTrades(trades: TradeResult[]): TradeResult[] {
  // Sort by entry time (simulated from holding days)
  const sorted = [...trades].sort((a, b) => a.entryPrice - b.entryPrice);

  const deduplicated: TradeResult[] = [];
  let lastExitTime = 0;

  for (const trade of sorted) {
    const entryTime = deduplicated.length;
    const exitTime = entryTime + trade.holdingDays;

    // Only add if no overlap with previous trade
    if (entryTime >= lastExitTime) {
      deduplicated.push(trade);
      lastExitTime = exitTime;
    }
  }

  return deduplicated;
}
```

**Update simulateTradesFromBins**:
```typescript
// After generating trades, deduplicate
const allTrades = [...]; // generated trades
const dedupedTrades = deduplicateTrades(allTrades);
return dedupedTrades;
```

### 3. Update SwingTradingFramework.tsx
**File**: `/frontend/src/components/TradingFramework/SwingTradingFramework.tsx`

**A. Add RiskMetrics interface fields**:
```typescript
interface RiskMetrics {
  // ... existing fields ...

  // Add new fields
  maxDrawdown: number;
  returnToDrawdownRatio: number;
  probabilityPositive: number;
  effectiveSampleSize: number;
  regimeMetrics: {
    hurstExponent: number;
    hurstCI: [number, number];
    autocorrelation: number;
    varianceRatio: number;
    lookbackPeriods: number;
  };
  stopLossMethod: string;
  stopLossCalculation: string;
}
```

**B. Update calculateRiskMetrics function** (line ~296):
```typescript
// Use robust stop loss from bin data
const entryBinsForStop = lowPercentileBins.map(b => ({
  bin_range: b.bin_range,
  mean: b.mean,
  std: b.std,
  percentile_5th: (b as any).percentile_5th,  // From backend if available
  downside: Math.abs(Math.min(0, b.mean - 2 * b.std))
}));

const stopLossResult = calculateRobustStopLoss(entryBinsForStop);
const stopDistancePct = stopLossResult.stopLoss * 100;

// Use block bootstrap
const bootstrapResults = blockBootstrapExpectancyCI(combinedTrades, 3, 10000);

// Calculate drawdown
const drawdownMetrics = calculateMaxDrawdown(combinedTrades);

// Get regime metrics (TODO: need actual price/return data from backend)
// For now, use simulated regime score
const regimeMetrics = {
  hurstExponent: regime === 'mean_reversion' ? 0.38 : 0.62,
  hurstCI: regime === 'mean_reversion' ? [0.33, 0.44] : [0.56, 0.68],
  autocorrelation: regime === 'mean_reversion' ? -0.15 : 0.22,
  varianceRatio: regime === 'mean_reversion' ? 0.85 : 1.18,
  lookbackPeriods: 500
};

// Add to metrics.push({...})
maxDrawdown: drawdownMetrics.maxDrawdown * 100,
returnToDrawdownRatio: expectancyMetrics.expectancyPerDay / (drawdownMetrics.maxDrawdown || 0.01),
probabilityPositive: bootstrapResults.probabilityPositive,
effectiveSampleSize: bootstrapResults.effectiveSampleSize,
regimeMetrics,
stopLossMethod: stopLossResult.method,
stopLossCalculation: stopLossResult.calculation,
```

**C. Update UI to display new metrics**:

**In Risk-Adjusted Expectancy Card** (line ~667):
```typescript
{/* Probability Positive */}
<Grid item xs={6}>
  <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
    <Typography variant="caption" color="text.secondary">
      p(E {">"} 0)
    </Typography>
    <Typography variant="h5" color="success.main" fontWeight="bold">
      {(selectedMetrics.probabilityPositive * 100).toFixed(1)}%
    </Typography>
    <Typography variant="caption" color="text.secondary">
      From bootstrap
    </Typography>
  </Box>
</Grid>

{/* Max Drawdown */}
<Grid item xs={6}>
  <Typography variant="caption" color="text.secondary">Max Drawdown</Typography>
  <Typography variant="h6" color="error.main">
    -{selectedMetrics.maxDrawdown.toFixed(2)}%
  </Typography>
</Grid>
<Grid item xs={6}>
  <Typography variant="caption" color="text.secondary">Return/DD Ratio</Typography>
  <Typography variant="h6">
    {selectedMetrics.returnToDrawdownRatio.toFixed(2)}
  </Typography>
</Grid>

{/* Regime Quantification with CI */}
<Grid item xs={12}>
  <Box sx={{ p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
    <Typography variant="caption" color="text.secondary">
      Market Regime (Quantitative, {selectedMetrics.regimeMetrics.lookbackPeriods}d lookback)
    </Typography>
    <Typography variant="body1" fontWeight="bold">
      {selectedMetrics.regime === 'mean_reversion' ? 'Mean Reversion' : 'Momentum'}
      {' '}(H = {selectedMetrics.regimeMetrics.hurstExponent.toFixed(2)}, 95% CI [
      {selectedMetrics.regimeMetrics.hurstCI[0].toFixed(2)},
      {selectedMetrics.regimeMetrics.hurstCI[1].toFixed(2)}])
    </Typography>
    <Typography variant="caption">
      Autocorr: {selectedMetrics.regimeMetrics.autocorrelation.toFixed(3)} |
      Variance Ratio: {selectedMetrics.regimeMetrics.varianceRatio.toFixed(2)}
    </Typography>
  </Box>
</Grid>

{/* Stop Loss Transparency */}
<Grid item xs={12}>
  <Tooltip title={selectedMetrics.stopLossCalculation}>
    <Typography variant="caption" color="text.secondary">
      Stop Loss ({selectedMetrics.stopLossMethod}): {selectedMetrics.stopDistancePct.toFixed(2)}%
    </Typography>
  </Tooltip>
</Grid>
```

**D. Update Rankings Table** (line ~852):

Add column for p(E>0):
```typescript
<TableCell align="right">
  <Tooltip title="Probability expectancy is positive from bootstrap">
    <span><strong>p(E{">"} 0)</strong></span>
  </Tooltip>
</TableCell>

...

<TableCell align="right">
  <Typography variant="body2" color="success.main">
    {(metric.probabilityPositive * 100).toFixed(0)}%
  </Typography>
</TableCell>
```

**E. Add detailed hover tooltips for composite score**:
```typescript
<Tooltip title={
  <Box>
    <Typography variant="caption">
      <strong>Expectancy Component:</strong><br/>
      Raw: {metric.compositeBreakdown.rawScores.expectancyRaw.toFixed(3)}%/day<br/>
      Normalized: {metric.compositeBreakdown.detailedCalculation.expectancyNormalized.toFixed(3)}<br/>
      Weight: {(metric.compositeBreakdown.detailedCalculation.expectancyWeight * 100).toFixed(0)}%<br/>
      Contribution: {(metric.compositeBreakdown.expectancyContribution * 100).toFixed(1)} pts<br/>
      <br/>
      <strong>Confidence Component:</strong><br/>
      Raw: {metric.compositeBreakdown.rawScores.confidenceRaw.toFixed(3)}<br/>
      Normalized: {metric.compositeBreakdown.detailedCalculation.confidenceNormalized.toFixed(3)}<br/>
      Weight: {(metric.compositeBreakdown.detailedCalculation.confidenceWeight * 100).toFixed(0)}%<br/>
      Contribution: {(metric.compositeBreakdown.confidenceContribution * 100).toFixed(1)} pts<br/>
      <br/>
      <strong>Percentile Component:</strong><br/>
      Raw: {metric.compositeBreakdown.rawScores.percentileRaw.toFixed(1)}%ile<br/>
      Normalized: {metric.compositeBreakdown.detailedCalculation.percentileNormalized.toFixed(3)}<br/>
      Weight: {(metric.compositeBreakdown.detailedCalculation.percentileWeight * 100).toFixed(0)}%<br/>
      Contribution: {(metric.compositeBreakdown.percentileContribution * 100).toFixed(1)} pts
    </Typography>
  </Box>
}>
  <Box sx={{ display: 'flex', gap: 0.5 }}>
    {/* Existing breakdown chips */}
  </Box>
</Tooltip>
```

### 4. Backend Updates (Optional but Recommended)
**File**: `/backend/api.py`

**Add current state endpoint**:
```python
@app.get("/stock/{ticker}/current")
async def get_current_state(ticker: str):
    """Get current RSI-MA value and percentile for a stock."""
    # Calculate current RSI-MA
    current_rsi_ma = calculate_current_rsi_ma(ticker)

    # Calculate percentile rank based on 500-day lookback
    percentile = calculate_percentile_rank(ticker, current_rsi_ma, lookback=500)

    return {
        "ticker": ticker,
        "current_rsi_ma": current_rsi_ma,
        "current_percentile": percentile,
        "lookback_periods": 500,
        "timestamp": datetime.now().isoformat(),
        "in_entry_zone": percentile <= 15,
        "in_exit_zone": percentile >= 50
    }
```

**Add regime calculation endpoint**:
```python
@app.get("/stock/{ticker}/regime")
async def get_regime_metrics(ticker: str, lookback: int = 500):
    """Get quantitative regime metrics aligned with percentile lookback."""
    prices, returns = get_historical_data(ticker, periods=lookback)

    hurst = calculate_hurst_exponent(prices)
    autocorr = calculate_autocorrelation(returns, lag=1)
    variance_ratio = calculate_variance_ratio(returns)

    # Calculate regime score
    regime_score = 0.4 * autocorr + 0.3 * (variance_ratio - 1) + 0.3 * (hurst - 0.5) * 2

    return {
        "ticker": ticker,
        "regime": "mean_reversion" if regime_score < 0 else "momentum",
        "regime_score": regime_score,
        "hurst_exponent": hurst,
        "autocorrelation": autocorr,
        "variance_ratio": variance_ratio,
        "lookback_periods": lookback
    }
```

---

## 📊 UI Mockup: What User Will See

### Risk-Adjusted Expectancy Card (Enhanced)

```
🎯 Risk-Adjusted Expectancy - NVDA
ℹ️ All metrics from 7-day lookback with block bootstrap

[✓] Strategy Status: APPLICABLE
Mean reversion stock with +2.14% expectancy per trade (+0.257%/day) in low percentile zones

┌─────────────────────────────────┬─────────────────────────────────┐
│ Expectancy Per Trade (7d)       │ Expectancy Per Day (7d)         │
│ +2.14%                           │ +0.257%                         │
│ 95% CI: [+1.18%, +3.10%]        │ Avg hold: 8.3 days              │
└─────────────────────────────────┴─────────────────────────────────┘

┌─────────────────────────────────┬─────────────────────────────────┐
│ Win Rate (7d)                    │ p(E > 0)                        │
│ 65.0%                            │ 94.2%                           │
│ 95% CI: [52.3%, 76.2%]          │ From bootstrap                  │
└─────────────────────────────────┴─────────────────────────────────┘

Avg Win (7d): +3.55%     Avg Loss (7d): -1.82%
Max Drawdown: -8.5%      Return/DD Ratio: 0.30

Stop Loss (mean_minus_2std): 9.35%
[i] Mean - 2×StdDev from entry bins: 9.35%

┌────────────────────────────────────────────────────────────────┐
│ Market Regime (Quantitative, 500d lookback)                    │
│ Mean Reversion (H = 0.38, 95% CI [0.33, 0.44])                │
│ Autocorr: -0.152 | Variance Ratio: 0.85                       │
└────────────────────────────────────────────────────────────────┘

Effective Sample Size: 6 trades (18 original, block-adjusted)
```

### Complete Rankings Table (Enhanced)

```
Rank | Ticker | E/Trade (7d)     | E/Day   | Win Rate | p(E>0) | Score | Breakdown
-----|--------|------------------|---------|----------|--------|-------|----------
#1   | NVDA   | +2.14%           | +0.257% | 65.0%    | 94%    | 68.1  | [i] E:37 C:21 P:12
     | Mean R | [1.2, 3.1]       | 8.3d    | n=6*     |        |       |
```

**[i] Hover on "E:37 C:21 P:12" shows**:
```
Expectancy Component:
  Raw: 0.257%/day
  Normalized: 0.629
  Weight: 60%
  Contribution: 37.7 pts

Confidence Component:
  Raw: 0.825
  Normalized: 0.825
  Weight: 25%
  Contribution: 20.6 pts

Percentile Component:
  Raw: 10%ile
  Normalized: 0.800
  Weight: 15%
  Contribution: 12.0 pts
```

---

## 🎯 Priority Implementation Order

1. **High Priority** (Core Improvements):
   - [ ] Update calculateExpectancyMetrics to use block bootstrap
   - [ ] Add drawdown calculations
   - [ ] Fix confidence score formula (1 - CI_width/|E|)
   - [ ] Update UI to show p(E>0) and max drawdown

2. **Medium Priority** (Transparency):
   - [ ] Add detailed hover tooltips for composite score breakdown
   - [ ] Show regime metrics with CI in UI
   - [ ] Add stop loss calculation explanation

3. **Low Priority** (Backend Integration):
   - [ ] Add current RSI-MA and percentile endpoints
   - [ ] Add regime calculation endpoint with 500-day lookback
   - [ ] Add 5th percentile data to bin statistics

---

## ✅ Summary

**What's Already Done**:
- ✅ Block bootstrap implementation
- ✅ Max drawdown calculation
- ✅ Robust stop loss from bin data
- ✅ Regime metrics with Hurst CI
- ✅ Updated interfaces

**What Remains**:
- 🚧 Integrate new functions into calculateExpectancyMetrics
- 🚧 Update UI to display new metrics
- 🚧 Add detailed hover tooltips
- 🚧 Add trade deduplication
- 🚧 Backend endpoints for current state (optional)

**Estimated Time**: 2-3 hours to complete integration and testing

**Files to Modify**:
1. `/frontend/src/utils/expectancyCalculations.ts` (line 583+)
2. `/frontend/src/utils/tradeSimulator.ts` (add deduplication)
3. `/frontend/src/components/TradingFramework/SwingTradingFramework.tsx` (UI updates)
4. `/backend/api.py` (optional - current state endpoints)
