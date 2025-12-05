# RSI-MA Performance Analytics Dashboard - Feature Mapping

## Overview
This document maps the Python script features to the web dashboard tabs, confirming that all data displayed is real and calculated from historical backtesting.

---

## Tab 1: RSI Indicator
**Python equivalent**: N/A (New visualization feature)

**What it shows**:
- Real-time RSI and RSI-MA values from ticker data
- Historical percentile ranks over time
- Percentile threshold lines (5%, 15%, 25%, 50%, 75%, 85%, 95%)

**Data source**: `enhanced_backtester.py` → `get_rsi_percentile_timeseries()` method

---

## Tab 2: Performance Matrix
**Python equivalent**: Main matrix output in `print_enhanced_results()`

### Heatmap View
Shows the same data as your Python script's matrix table:
- **Rows**: 20 percentile ranges (0-5%, 5-10%, ..., 95-100%)
- **Columns**: Days D1-D21
- **Values**: Expected CUMULATIVE returns (%)
- **Hover info**: Sample size, confidence level, success rate, P25-P75 range

### Enhanced Table View
Exactly matches your Python output with additional rows:

| Row | Python Output Line | Description |
|-----|-------------------|-------------|
| Main Matrix | `"Percentile │ D1 │ D2 │ ..."` | Expected cumulative returns by percentile/day |
| Win Rate % | `"Win Rate %"` row | Overall profit vs loss percentage for each day |
| Ret Dist % | `"Ret Dist %"` row | Median ± std dev in percentage terms |
| 68% Ret Rng | `"68% Ret Rng"` row | ±1 standard deviation range |
| 95% Ret Rng | `"95% Ret Rng"` row | ±2 standard deviation range |

**Data source**:
- `thresholdData.performance_matrix` - from `build_enhanced_matrix()`
- `thresholdData.win_rates` - from `calculate_overall_win_rates()`
- `thresholdData.return_distributions` - from `calculate_return_distribution()`

---

## Tab 3: Return Analysis
**Python equivalent**: Return distribution statistics

**What it shows**:
- **Median return line**: Green solid line tracking median returns D1-D21
- **68% confidence band**: ±1 standard deviation (light green shaded area)
- **95% confidence band**: ±2 standard deviations (lighter green shaded area)
- **Benchmark comparison**: Market benchmark returns (blue dotted line)

**Corresponds to Python output**:
```python
# From print_enhanced_results():
"Ret Dist %":  median±std
"68% Ret Rng": minus_1sd ~ plus_1sd
"95% Ret Rng": minus_2sd ~ plus_2sd
```

**Data source**: `thresholdData.return_distributions` - calculated in `calculate_return_distribution()`

---

## Tab 4: Strategy & Rules ⭐ NEW
**Python equivalent**: Multiple sections from `print_enhanced_results()`

### Trend Significance Analysis
Matches Python output section: `"📈 TREND SIGNIFICANCE ANALYSIS"`

Shows:
- **Trend Direction**: Upward/Downward with statistical confidence
- **Statistical Confidence**: Very High/High/Moderate/Low based on p-value
- **Correlation**: Pearson correlation coefficient
- **P-Value**: Statistical significance value
- **Peak Return Day**: Day with highest median return
- **Peak Return**: Maximum return percentage
- **Exit Timing Strategy**: Early vs late comparison significance

**Data source**: `thresholdData.trend_analysis` - from `analyze_return_trend_significance()`

### Percentile Movement Patterns
Matches Python output section: `"🎯 PERCENTILE MOVEMENT PATTERNS"`

Shows:
- **Reversion Risk**: Low/Moderate/High categorization
- **Typical Peak Percentile**: Median peak percentile reached
- **Reversion Magnitude**: Points declined from peak
- **Final Percentile**: Where percentiles typically end up
- **Complete Failure Rate**: % falling below 20th percentile

**Data source**: `thresholdData.percentile_movements.reversion_analysis` - from `analyze_percentile_movements()`

### Strategic Trade Management ⭐ NEW
Matches Python output section: `"⚡ STRATEGIC TRADE MANAGEMENT"`

Shows:
- **Primary Strategy (High Confidence)**: Rules with strong statistical backing
- **Secondary Considerations (Medium Confidence)**: Additional risk management factors
- **Rule Types**:
  - Exit Timing: When to exit based on return peaks
  - Trend Following: Hold recommendations for strong trends
  - Early Exit Signal: Profit-taking triggers
  - Reversion Protection: Trailing stop recommendations

**Data source**: `thresholdData.trade_management_rules` - from `generate_trade_management_rules()`

### Overall Strategy Recommendation
Matches Python logic:
```python
if declining_after_peak and reversion_risk_pts > 10:
    "DEFENSIVE: Returns peak early with high reversion risk - exit at peak"
elif trend_strength > 0.7 and reversion_risk_pts < 10:
    "AGGRESSIVE: Strong trend with low reversion risk - use trailing stops"
else:
    "MODERATE: Exit near return peak to avoid decline"
```

---

## Tab 5: Optimal Exit
**Python equivalent**: `"OPTIMAL EXIT STRATEGY"` section from Python script

**What it shows**:

### Optimal Exit Strategy
- **Recommended Exit Day**: Day with highest return efficiency (return per day)
- **Efficiency**: Return per day percentage
- **Target Return**: Total expected return at optimal day

### Exit Target Details
Shows the percentile range that delivers the target return:
- **Target Percentile Range**: e.g., "45-50%"
- **Expected Return**: Actual return for that range/day
- **Success Rate**: Historical win rate
- **Sample Size**: Number of historical trades
- **Confidence Level**: VH/H/M/L/VL based on sample size

### Efficiency Rankings
Top 5 days ranked by return efficiency (return per day), matching Python output.

### Statistical Trend Analysis
All trend statistics:
- Trend direction and strength
- Correlation coefficient and p-value
- Peak day and return
- Early vs late significance

### Risk Summary
All risk metrics from backtest:
- Median drawdown
- P90 drawdown (worst 10%)
- Max consecutive losses
- Recovery rate and median recovery days

**Data source**:
- `thresholdData.optimal_exit_strategy` - from `calculate_optimal_exit_strategy()`
- `thresholdData.risk_metrics` - from `calculate_risk_metrics()`
- `thresholdData.trend_analysis` - from `analyze_return_trend_significance()`

---

## Data Flow Confirmation

```
1. User selects ticker (e.g., AAPL) and threshold (e.g., ≤5%)
   ↓
2. Frontend calls: GET /api/backtest/AAPL
   ↓
3. Backend runs: EnhancedPerformanceMatrixBacktester.analyze_ticker("AAPL")
   ↓
4. Backend calculates (all real data):
   - Performance matrix (D1-D21, 20 percentile ranges)
   - Win rates per day
   - Return distributions (median, std, confidence intervals)
   - Percentile movements and reversion analysis
   - Trend significance (Pearson correlation, Mann-Whitney U test)
   - Trade management rules (based on observed patterns)
   - Optimal exit strategy (return efficiency analysis)
   - Risk metrics (drawdowns, recovery, consecutive losses)
   ↓
5. Frontend receives JSON with ALL calculated data
   ↓
6. Each tab visualizes different aspects of the same backtest results
```

---

## Key Differences from Python Script

### What's the Same:
✅ All calculations are identical
✅ All statistical tests are the same
✅ All data structures match
✅ All percentile ranges (D1-D21)
✅ Trade management rules generation
✅ Optimal exit strategy

### What's Enhanced in Web Dashboard:
✅ Interactive heatmap visualization
✅ Real-time data updates
✅ Multiple tickers selectable
✅ Hover tooltips with detailed info
✅ Confidence bands visualization
✅ Color-coded risk levels
✅ Organized into logical tabs
✅ Responsive design

---

## Verification Steps

To verify all data is real and matches your Python script:

1. **Run backend**:
   ```bash
   cd backend
   python enhanced_backtester.py
   ```

2. **Compare output** with dashboard data:
   - Performance Matrix values should match
   - Win rates should match
   - Return distributions should match
   - Trend analysis should match
   - Trade rules should match
   - Optimal exit should match

3. **Check API endpoint**:
   ```bash
   curl http://localhost:8000/api/backtest/AAPL
   ```
   You'll see the same data structure that feeds all tabs.

---

## Summary

**ALL DATA IS REAL AND CALCULATED FROM HISTORICAL BACKTESTING**

- ✅ No placeholder data
- ✅ No mock data
- ✅ All metrics calculated from actual ticker prices
- ✅ All statistical tests performed on real returns
- ✅ All trade rules generated from observed patterns
- ✅ All confidence levels based on sample sizes

The dashboard is a visualization layer on top of your Python script's calculations, making the same data more accessible and interactive.
