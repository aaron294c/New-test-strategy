# 🎯 Live Market State Feature - Complete

## Overview

Added a real-time "Current Market State" component that displays:
- **Live RSI-MA percentiles** for all tickers (updated every 5 minutes)
- **Risk-adjusted expectancy** based on current percentile cohort
- **Buy opportunity signals** highlighting stocks in entry zones
- **Expected performance metrics** if entering at current levels

## 🚀 Features Implemented

### 1. Backend Endpoint: `/api/swing-framework/current-state`

**Location**: `backend/swing_framework_api.py` lines 327-415

**What it does**:
- Fetches latest price data for all tickers
- Calculates current RSI-MA indicator (most recent value)
- Determines current percentile rank (0-100%)
- Identifies percentile cohort (≤5%, 5-15%, or none)
- Retrieves historical cohort performance from backtest data
- Calculates live risk-adjusted expectancy

**Response Structure**:
```json
{
  "timestamp": "2025-11-07T...",
  "market_state": [
    {
      "ticker": "MSFT",
      "name": "Microsoft",
      "current_date": "2025-11-06",
      "current_price": 497.10,
      "current_percentile": 0.40,  // ← LIVE percentile!
      "percentile_cohort": "extreme_low",  // ≤5%
      "zone_label": "≤5th percentile (Extreme Low)",
      "in_entry_zone": true,
      "regime": "mean_reversion",
      "volatility_level": "Medium",
      "live_expectancy": {
        "expected_win_rate": 0.556,  // 55.6%
        "expected_return_pct": 0.770,  // 0.77%
        "expected_holding_days": 6.85,
        "expected_return_per_day_pct": 0.112,  // 0.11%/day
        "risk_adjusted_expectancy_pct": 0.513,  // Adjusted for volatility
        "sample_size": 27  // Based on 27 historical trades in this cohort
      }
    },
    // ... more tickers
  ],
  "summary": {
    "total_tickers": 6,
    "in_entry_zone": 2,
    "extreme_low_opportunities": 1,  // ≤5%
    "low_opportunities": 1  // 5-15%
  }
}
```

### 2. Live Expectancy Calculation

**Formula**:
```python
# 1. Get historical cohort performance
if current_percentile <= 5.0:
    cohort_stats = backtest_stats['cohort_extreme_low']
elif current_percentile <= 15.0:
    cohort_stats = backtest_stats['cohort_low']

# 2. Extract expected metrics
expected_win_rate = cohort_stats['win_rate']
expected_return = cohort_stats['avg_return']
expected_holding_days = cohort_stats['avg_holding_days']

# 3. Risk adjustment (volatility-based)
volatility_multiplier = {
    "Low": 1.0,
    "Medium": 1.5,
    "High": 2.0
}[volatility_level]

risk_adjusted_expectancy = expected_return / volatility_multiplier
```

**Example** (MSFT at 0.4% percentile):
- Historical ≤5% cohort: 55.6% win rate, 0.77% avg return, 6.85 days hold
- Volatility: Medium (1.5x multiplier)
- Risk-adjusted: 0.77% / 1.5 = **0.51% expectancy**

### 3. Frontend Component: CurrentMarketState.tsx

**Location**: `frontend/src/components/TradingFramework/CurrentMarketState.tsx`

**Features**:
- ✅ Auto-refreshes every 5 minutes
- ✅ Color-coded percentiles (green ≤5%, orange 5-15%, gray >15%)
- ✅ Buy signal icons (✓ for extreme low, ⚠ for low)
- ✅ Sortable table showing all tickers
- ✅ Highlighted rows for stocks in entry zones
- ✅ Complete expected performance metrics
- ✅ Tooltip explanations

**Visual Indicators**:
- 🟢 **Green row background**: Stock in entry zone
- ✅ **Green checkmark**: Extreme low (≤5%) - strong buy signal
- ⚠️ **Orange warning**: Low (5-15%) - buy signal
- 🟢 **Green percentile text**: Current ≤5%
- 🟠 **Orange percentile text**: Current 5-15%
- 🔵 **Blue percentile text**: Current 15-30%
- ⚪ **Gray percentile text**: Current >30%

**Table Columns**:
1. **Ticker** - Symbol and current price
2. **Signal** - Buy signal icon (if applicable)
3. **Current %ile** - Live RSI-MA percentile rank
4. **Zone** - Cohort label (≤5%, 5-15%, N/A)
5. **Regime** - Mean reversion or momentum
6. **Expected Win Rate** - From historical cohort
7. **Expected Return** - From historical cohort (per trade and per day)
8. **Risk-Adj. Expectancy** - Volatility-adjusted return
9. **Avg Hold** - Expected holding days
10. **Sample Size** - Number of historical trades in cohort

### 4. Integration

**Location**: `SwingTradingFramework.tsx` line 745

Added at the **top** of the Swing Framework page, above the framework header.

**Auto-refresh**: Component fetches fresh data every 5 minutes to show latest percentiles.

---

## 📊 Current Market Example (2025-11-06)

### MSFT - Strong Buy 🟢

```
Ticker: MSFT (Microsoft)
Current Price: $497.10
Current Percentile: 0.40% ← EXTREME LOW!
Zone: ≤5th percentile
Regime: Mean Reversion
Signal: ✅ Strong Buy

Expected Performance (if entering now):
  Win Rate: 55.6%
  Expected Return: +0.77% per trade
  Return per Day: +0.112%/day
  Risk-Adj. Expectancy: +0.51%
  Avg Hold: 6.9 days
  Sample: n=27 historical trades

Interpretation:
- MSFT at historically extreme low (0.4th percentile)
- Mean reversion stock in deep oversold territory
- Historical trades from ≤5% cohort show 55.6% win rate
- Expected 0.77% return over ~7 days if entering now
- Risk-adjusted for medium volatility: 0.51% expectancy
```

### NVDA - Buy 🟠

```
Ticker: NVDA (NVIDIA)
Current Price: $188.08
Current Percentile: 5.81%
Zone: 5-15th percentile
Regime: Mean Reversion
Signal: ⚠️ Buy

Expected Performance (if entering now):
  Win Rate: 56.8%
  Expected Return: +0.34% per trade
  Return per Day: +0.067%/day
  Risk-Adj. Expectancy: +0.17%
  Avg Hold: 5.1 days
  Sample: n=68 historical trades

Interpretation:
- NVDA in low percentile zone (5.81%)
- Mean reversion stock in oversold territory
- Historical 5-15% cohort shows 56.8% win rate
- Expected 0.34% return over ~5 days
- Risk-adjusted for high volatility: 0.17% expectancy
```

---

## 🎯 How to Use

### Step 1: Navigate to Swing Framework Tab

The "Live Market State" component appears at the top of the Swing Framework page.

### Step 2: Look for Buy Signals

**Strong Buy** (✅):
- Current percentile ≤5%
- Green highlighted row
- High historical win rate (typically 45-60%)
- Positive risk-adjusted expectancy

**Buy** (⚠️):
- Current percentile 5-15%
- Green highlighted row
- Moderate historical win rate
- Positive risk-adjusted expectancy

**Watch** (no icon):
- Current percentile 15-30%
- May be approaching entry zone
- Monitor for further decline

**Neutral** (no icon):
- Current percentile >30%
- Not in entry zone
- Wait for lower percentile

### Step 3: Evaluate Expected Performance

Check the **Live Expectancy** columns:
- **Expected Win Rate**: Historical success rate for this cohort
- **Expected Return**: Average return if entering at this percentile
- **Risk-Adj. Expectancy**: Return adjusted for stock's volatility
- **Avg Hold**: Expected days until 50% percentile exit

### Step 4: Cross-Reference with Historical Rankings

The "Complete Risk-Adjusted Rankings" table below shows long-term performance.

Compare:
- **Current State**: Identifies buy opportunities RIGHT NOW
- **Historical Rankings**: Shows which stocks perform best overall

**Example Decision**:
- MSFT currently at 0.4% percentile (strong buy signal)
- Historical ranking shows MSFT with 50.5% overall win rate
- Extreme low cohort shows 55.6% win rate
- **Action**: Strong buy candidate with positive expectancy

---

## 🧪 Testing

### Test Current State Endpoint

```bash
curl http://localhost:8000/api/swing-framework/current-state | jq '.summary'

# Expected output:
{
  "total_tickers": 6,
  "in_entry_zone": 2,
  "extreme_low_opportunities": 1,
  "low_opportunities": 1
}
```

### Test Specific Ticker

```bash
curl http://localhost:8000/api/swing-framework/current-state | \
  jq '.market_state[] | select(.ticker == "MSFT")'

# Expected: Full state with live_expectancy object
```

### Verify Frontend Display

1. Open Swing Framework tab
2. Component should appear at top
3. Look for:
   - ✅ Chip showing "1 Extreme Low (≤5%)"
   - ⚠️ Chip showing "1 Low (5-15%)"
   - Green highlighted rows for MSFT and NVDA
   - Non-zero percentiles and expectancy values

---

## 🔄 Auto-Refresh Behavior

**Refresh Frequency**: Every 5 minutes

**Why 5 minutes?**
- RSI-MA indicator based on 4H/Daily timeframes
- Current percentile doesn't change drastically minute-to-minute
- Balances freshness with API efficiency

**Manual Refresh**: Page reload fetches latest data immediately

---

## 📈 Risk-Adjusted Expectancy Explained

### Volatility Adjustment

Different stocks have different risk profiles:

**Low Volatility** (multiplier = 1.0):
- Stable, predictable moves
- Full expectancy value
- Example: Utilities, consumer staples

**Medium Volatility** (multiplier = 1.5):
- Moderate price swings
- Expectancy divided by 1.5
- Example: MSFT, GOOGL, AAPL

**High Volatility** (multiplier = 2.0):
- Large price swings
- Expectancy divided by 2.0
- Example: NVDA, TSLA

**Formula**:
```
Risk-Adj. Expectancy = Expected Return / Volatility Multiplier
```

**Example** (MSFT):
- Expected Return: 0.77%
- Volatility: Medium (1.5x)
- Risk-Adj. Expectancy: 0.77% / 1.5 = **0.51%**

**Example** (NVDA):
- Expected Return: 0.34%
- Volatility: High (2.0x)
- Risk-Adj. Expectancy: 0.34% / 2.0 = **0.17%**

### Interpretation

**Positive Risk-Adj. Expectancy** (>0%):
- Expected profit after accounting for volatility risk
- Higher is better
- Typical range: 0.1% to 0.8%

**Zero Risk-Adj. Expectancy** (≈0%):
- Break-even after accounting for risk
- Not attractive for entry

**Negative Risk-Adj. Expectancy** (<0%):
- Expected loss after accounting for risk
- Avoid entry

---

## 🎨 UI/UX Features

### Color Coding

**Percentile Colors**:
- 🟢 Green (≤5%): Strong buy zone
- 🟠 Orange (5-15%): Buy zone
- 🔵 Blue (15-30%): Watch zone
- ⚪ Gray (>30%): Neutral zone

**Expected Return Colors**:
- 🟢 Green: Positive return
- 🔴 Red: Negative return

**Risk-Adj. Expectancy Colors**:
- 🟢 Dark Green (>0.4%): Excellent
- 🟢 Light Green (0.2-0.4%): Good
- 🟠 Orange (0-0.2%): Marginal
- 🔴 Red (<0%): Negative

### Icons

- ✅ **Green Checkmark**: Extreme low (≤5%) - highest priority
- ⚠️ **Orange Warning**: Low (5-15%) - good opportunity
- 📊 **Trending Down**: Extreme low chip indicator
- 📈 **Trending Up**: Low percentile chip indicator
- ℹ️ **Info**: Not in entry zone chip

### Tooltips

- Hover over zone chips for full label
- Hover over "volatility adjustment" link for explanation

---

## 📋 Technical Specifications

### Backend Performance

**Endpoint**: `GET /api/swing-framework/current-state`

**Processing Time**: ~10-20 seconds (fetches yfinance data for 6 tickers)

**Cache Strategy**: Could add caching with 5-minute TTL for production

**Data Freshness**:
- Price data: Latest close (T-1 for intraday)
- Percentile: Calculated from 500-day rolling window
- Cohort stats: From historical backtest (updated on backend restart)

### Frontend Performance

**Component Load**: <1 second (reads from API)

**Re-render**: Only on data change (React state management)

**Memory Usage**: Minimal (small JSON response)

**Auto-refresh**: Every 5 minutes (configurable)

---

## 🚀 Future Enhancements

### Potential Improvements

1. **Intraday Updates**: Fetch current intraday price and calculate live percentile
2. **Price Alerts**: Notify when stocks enter extreme low zones
3. **Historical Chart**: Show percentile over time with entry/exit zones
4. **Position Sizing**: Suggest Kelly criterion-based position sizes
5. **Portfolio View**: Track multiple entries and aggregate expectancy
6. **Compare to Current Holdings**: Show if you should add to existing positions
7. **Mobile Responsive**: Optimize table for mobile devices
8. **Export**: Download current opportunities as CSV

### Easy Wins

**Add Current Percentile to Historical Rankings Table**:
- Show current %ile next to ticker in main rankings
- Highlight tickers currently in entry zones
- Cross-reference current opportunity with historical performance

**Add "Entry Opportunity Score"**:
- Combine current percentile, risk-adj. expectancy, win rate
- Single score (0-100) showing entry quality
- Sort by score to prioritize best opportunities

---

## ✅ Summary

### What Was Added

**Backend** (`swing_framework_api.py`):
- ✅ `/api/swing-framework/current-state` endpoint
- ✅ Live percentile calculation for all tickers
- ✅ Cohort identification (extreme low, low, none)
- ✅ Live expectancy calculation from historical cohort performance
- ✅ Risk adjustment for volatility
- ✅ Summary statistics (opportunities count)

**Frontend** (`CurrentMarketState.tsx`):
- ✅ New component displaying live market state
- ✅ Auto-refresh every 5 minutes
- ✅ Color-coded percentiles and returns
- ✅ Buy signal icons
- ✅ Complete expectancy metrics table
- ✅ Highlighted entry zone opportunities
- ✅ Integrated at top of Swing Framework page

### User Benefits

1. **Real-time visibility**: See current percentiles immediately
2. **Buy signals**: Know which stocks are in entry zones NOW
3. **Expected performance**: Understand expected outcomes before entering
4. **Risk awareness**: See volatility-adjusted expectancy
5. **Data-driven decisions**: Base entries on historical cohort performance
6. **Convenience**: Auto-updates, no manual refreshing needed

---

**Status**: ✅ Complete and Integrated
**Action**: Hard refresh browser to see new Live Market State component
**Location**: Top of Swing Framework page
**Updates**: Every 5 minutes automatically

**Current Buy Opportunities** (as of 2025-11-06):
- 🟢 **MSFT** at 0.4% percentile - Strong buy with 0.51% risk-adj. expectancy
- 🟠 **NVDA** at 5.8% percentile - Buy with 0.17% risk-adj. expectancy
