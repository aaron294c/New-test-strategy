# Frontend Integration Specification: TSLA & NFLX

**Analyst Agent Report**
**Date:** 2025-11-03
**Swarm Task:** TSLA/NFLX Analytics Integration

---

## Executive Summary

This document provides a complete specification for integrating TSLA (Tesla) and NFLX (Netflix) into the RSI-MA Performance Analytics Dashboard frontend. The backend scripts (`generate_tsla_stats.py` and `generate_nflx_stats.py`) have already been created and will generate the required statistical data. This specification details all frontend changes needed to display and interact with TSLA/NFLX data.

---

## 1. Stock Selection Components

### 1.1 Main App Ticker Selector (`frontend/src/App.tsx`)

**Current State:**
- Line 90: `DEFAULT_TICKERS` array hardcodes 10 stocks
- Lines 171-175: Dropdown renders ticker selection
- Line 115: Default selected ticker is 'AAPL'

**Required Changes:**

```typescript
// CHANGE: Line 90
// FROM:
const DEFAULT_TICKERS = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'QQQ', 'SPY', 'GLD', 'SLV'];

// TO:
const DEFAULT_TICKERS = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'QQQ', 'SPY', 'GLD', 'SLV', 'TSLA', 'NFLX'];
```

**Impact:**
- Adds TSLA and NFLX to main ticker dropdown
- No other changes needed - component dynamically maps over array

---

### 1.2 Multi-Timeframe Guide Component (`frontend/src/components/MultiTimeframeGuide.tsx`)

**Current State:**
- Lines 825-836: Hardcoded stock tabs for 6 stocks
- Tab selection uses array index mapping

**Required Changes:**

```typescript
// CHANGE: Lines 825-836
// FROM:
<Tabs
  value={['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'GLD', 'SLV'].indexOf(selectedStock)}
  onChange={(_, newValue) =>
    setSelectedStock(['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'GLD', 'SLV'][newValue])
  }
>
  <Tab label="NVDA" />
  <Tab label="MSFT" />
  <Tab label="GOOGL" />
  <Tab label="AAPL" />
  <Tab label="GLD" />
  <Tab label="SLV" />
</Tabs>

// TO:
<Tabs
  value={['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'GLD', 'SLV', 'TSLA', 'NFLX'].indexOf(selectedStock)}
  onChange={(_, newValue) =>
    setSelectedStock(['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'GLD', 'SLV', 'TSLA', 'NFLX'][newValue])
  }
>
  <Tab label="NVDA" />
  <Tab label="MSFT" />
  <Tab label="GOOGL" />
  <Tab label="AAPL" />
  <Tab label="GLD" />
  <Tab label="SLV" />
  <Tab label="TSLA" />
  <Tab label="NFLX" />
</Tabs>
```

**Alternative Improvement (Recommended):**
Create a constant at the top of the component to avoid duplication:

```typescript
// ADD: Near top of component (after imports)
const AVAILABLE_STOCKS = ['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'GLD', 'SLV', 'TSLA', 'NFLX'];

// THEN CHANGE: Lines 825-836 to:
<Tabs
  value={AVAILABLE_STOCKS.indexOf(selectedStock)}
  onChange={(_, newValue) => setSelectedStock(AVAILABLE_STOCKS[newValue])}
>
  {AVAILABLE_STOCKS.map(ticker => (
    <Tab key={ticker} label={ticker} />
  ))}
</Tabs>
```

**Impact:**
- Adds TSLA and NFLX tabs to Multi-Timeframe Guide
- Component already fetches data dynamically via API
- Cleaner, more maintainable code

---

## 2. API Client Changes

### 2.1 API Client (`frontend/src/api/client.ts`)

**Current State:**
- No hardcoded stock lists
- All endpoints accept `ticker` parameter
- Backend API endpoints are already ticker-agnostic

**Required Changes:**
- ✅ **NO CHANGES NEEDED**
- API client is fully dynamic and will work with any ticker the backend supports

**Verification Points:**
- Line 51-56: `getBacktestResults(ticker: string)` - accepts any ticker
- Line 94-99: `getRSIChartData(ticker: string)` - accepts any ticker
- Lines 109-112: `runSimulation(ticker: string)` - accepts any ticker

---

### 2.2 Backend API Endpoints (`backend/api.py`)

**Current State:**
- Line 64: `DEFAULT_TICKERS` array defines supported stocks
- Line 36-40: Imports GLD and SLV statistics from `stock_statistics.py`

**Required Changes:**

```python
# CHANGE: Line 64
# FROM:
DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "QQQ", "SPY", "GLD", "SLV"]

# TO:
DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "QQQ", "SPY", "GLD", "SLV", "TSLA", "NFLX"]

# CHANGE: Lines 36-40 (add TSLA/NFLX imports)
# ADD AFTER SLV imports:
    TSLA_4H_DATA, TSLA_DAILY_DATA,
    NFLX_4H_DATA, NFLX_DAILY_DATA
```

**File:** `backend/stock_statistics.py`

**Required Addition:**
- Add TSLA and NFLX data dictionaries after SLV data
- Format: Same structure as existing stocks (see section 4)

---

## 3. Component Data Flow Analysis

### 3.1 Components That Use Ticker Prop

All these components receive `ticker` as a prop and make dynamic API calls:

| Component | File Path | API Endpoint Used | Changes Needed |
|-----------|-----------|-------------------|----------------|
| RSIPercentileChart | `components/RSIPercentileChart.tsx` | `/api/rsi-chart/{ticker}` | ✅ None |
| PerformanceMatrixHeatmap | `components/PerformanceMatrixHeatmap.tsx` | N/A (receives data from parent) | ✅ None |
| EnhancedPerformanceMatrix | `components/EnhancedPerformanceMatrix.tsx` | N/A (receives data from parent) | ✅ None |
| ReturnDistributionChart | `components/ReturnDistributionChart.tsx` | N/A (receives data from parent) | ✅ None |
| OptimalExitPanel | `components/OptimalExitPanel.tsx` | N/A (receives data from parent) | ✅ None |
| StrategyRulesPanel | `components/StrategyRulesPanel.tsx` | N/A (receives data from parent) | ✅ None |
| ExitStrategyComparison | `components/ExitStrategyComparison.tsx` | `/api/optimal-exit/{ticker}/{threshold}` | ✅ None |
| TradeSimulationViewer | `components/TradeSimulationViewer.tsx` | Various simulation endpoints | ✅ None |
| LiveTradingSignals | `components/LiveTradingSignals.tsx` | `/api/live-signal/{ticker}`, `/api/exit-signal` | ✅ None |
| MultiTimeframeDivergence | `components/MultiTimeframeDivergence.tsx` | `/api/multi-timeframe/{ticker}` | ✅ None |
| PositionManagement | `components/PositionManagement.tsx` | `/api/position-management/{ticker}` | ✅ None |
| EnhancedDivergenceLifecycle | `components/EnhancedDivergenceLifecycle.tsx` | `/api/enhanced-lifecycle/{ticker}` | ✅ None |
| PercentileForwardMapper | `components/PercentileForwardMapper.tsx` | `/api/percentile-forward/{ticker}` | ✅ None |
| MultiTimeframeGuide | `components/MultiTimeframeGuide.tsx` | `/api/multi-timeframe-guide/{ticker}` | ⚠️ Update tabs |

### 3.2 Data Flow Summary

```
User Selection (App.tsx)
    ↓
selectedTicker state
    ↓
Passed as prop to components
    ↓
Components make API calls: `/api/endpoint/{ticker}`
    ↓
Backend fetches ticker-specific data
    ↓
Response rendered in UI
```

**Key Insight:** The architecture is already designed for dynamic ticker support. Only hardcoded lists need updating.

---

## 4. Backend Data Structure Requirements

### 4.1 Stock Statistics File Structure

**File:** `backend/stock_statistics.py`

**Required Addition (after SLV data, around line 250):**

```python
# ============================================
# TESLA (TSLA) DATA
# ============================================

TSLA_4H_DATA = {
    # Will be populated by generate_tsla_stats.py
    # Structure matches NVDA/MSFT/GOOGL/AAPL/GLD/SLV format
    # Format: "bin_range": BinStatistics(...)
}

TSLA_DAILY_DATA = {
    # Will be populated by generate_tsla_stats.py
}

# ============================================
# NETFLIX (NFLX) DATA
# ============================================

NFLX_4H_DATA = {
    # Will be populated by generate_nflx_stats.py
}

NFLX_DAILY_DATA = {
    # Will be populated by generate_nflx_stats.py
}
```

**Required Addition to STOCK_METADATA (around line 380):**

```python
STOCK_METADATA = {
    # ... existing stocks ...

    "TSLA": StockMetadata(
        ticker="TSLA",
        name="Tesla",
        personality="TBD - Generated from analysis",
        reliability_4h="TBD",
        reliability_daily="TBD",
        tradeable_4h_zones=[],  # Populated after data generation
        dead_zones_4h=[],
        best_4h_bin="TBD",
        best_4h_t_score=0.0,
        ease_rating=0,
        is_mean_reverter=False,  # TBD
        is_momentum=False,       # TBD
        volatility_level="TBD",
        entry_guidance="TBD",
        avoid_guidance="TBD",
        special_notes="TBD"
    ),

    "NFLX": StockMetadata(
        ticker="NFLX",
        name="Netflix",
        personality="TBD - Generated from analysis",
        reliability_4h="TBD",
        reliability_daily="TBD",
        tradeable_4h_zones=[],
        dead_zones_4h=[],
        best_4h_bin="TBD",
        best_4h_t_score=0.0,
        ease_rating=0,
        is_mean_reverter=False,
        is_momentum=False,
        volatility_level="TBD",
        entry_guidance="TBD",
        avoid_guidance="TBD",
        special_notes="TBD"
    )
}
```

### 4.2 Data Generation Scripts

**Files:**
- `backend/generate_tsla_stats.py` ✅ Already exists
- `backend/generate_nflx_stats.py` ✅ Already exists

**Process:**
1. Run TSLA script: Fetches TSLA data, calculates bin statistics, outputs Python code
2. Run NFLX script: Fetches NFLX data, calculates bin statistics, outputs Python code
3. Copy/paste generated code into `stock_statistics.py`
4. Update STOCK_METADATA with analyzed characteristics

---

## 5. UI/UX Considerations

### 5.1 Stock Selector Ordering

**Current Order:**
```
AAPL, MSFT, NVDA, GOOGL, AMZN, META, QQQ, SPY, GLD, SLV
```

**Recommended New Order:**
```
AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA, NFLX, QQQ, SPY, GLD, SLV
```

**Rationale:**
- Group individual stocks together
- ETFs (QQQ, SPY) and commodities (GLD, SLV) at end
- Alphabetical within categories

### 5.2 Default Ticker Selection

**Current:** `AAPL`
**Recommendation:** Keep `AAPL` as default (no change)
**Alternative:** Could change to `TSLA` if it becomes the most popular ticker

### 5.3 Loading States

**Current Behavior:**
- `CircularProgress` shown while fetching data
- Error messages displayed if API call fails

**Required Verification:**
- Test that TSLA/NFLX data loads correctly
- Verify error handling if backend data is missing
- Ensure loading spinners appear during initial fetch

---

## 6. Testing Checklist

### 6.1 Frontend Integration Tests

- [ ] **App.tsx Ticker Selector**
  - [ ] TSLA appears in dropdown
  - [ ] NFLX appears in dropdown
  - [ ] Selecting TSLA loads data correctly
  - [ ] Selecting NFLX loads data correctly

- [ ] **MultiTimeframeGuide Component**
  - [ ] TSLA tab appears and is clickable
  - [ ] NFLX tab appears and is clickable
  - [ ] Clicking TSLA tab fetches TSLA data
  - [ ] Clicking NFLX tab fetches NFLX data
  - [ ] Stock metadata displays correctly for TSLA
  - [ ] Stock metadata displays correctly for NFLX

- [ ] **All Components with Ticker Prop**
  - [ ] RSIPercentileChart renders for TSLA
  - [ ] RSIPercentileChart renders for NFLX
  - [ ] LiveTradingSignals works for TSLA
  - [ ] LiveTradingSignals works for NFLX
  - [ ] PositionManagement loads TSLA data
  - [ ] PositionManagement loads NFLX data
  - [ ] All 13 tab panels work with TSLA
  - [ ] All 13 tab panels work with NFLX

### 6.2 Backend Integration Tests

- [ ] **API Endpoints**
  - [ ] `/api/backtest/TSLA` returns valid data
  - [ ] `/api/backtest/NFLX` returns valid data
  - [ ] `/api/rsi-chart/TSLA` returns valid data
  - [ ] `/api/rsi-chart/NFLX` returns valid data
  - [ ] `/api/multi-timeframe-guide/TSLA` returns data
  - [ ] `/api/multi-timeframe-guide/NFLX` returns data
  - [ ] `/api/live-signal/TSLA` generates signals
  - [ ] `/api/live-signal/NFLX` generates signals

- [ ] **Data Quality**
  - [ ] TSLA_4H_DATA has all 8 percentile bins
  - [ ] TSLA_DAILY_DATA has all 8 percentile bins
  - [ ] NFLX_4H_DATA has all 8 percentile bins
  - [ ] NFLX_DAILY_DATA has all 8 percentile bins
  - [ ] BinStatistics objects have valid t-scores
  - [ ] Sample sizes are reasonable (>10 for reliability)

### 6.3 End-to-End User Flows

- [ ] **Entry Signal Flow**
  1. User selects TSLA from main dropdown
  2. Dashboard loads all TSLA data
  3. User navigates to "🔴 LIVE SIGNALS" tab
  4. User clicks "Get Entry Signal"
  5. Entry signal displays with expected returns

- [ ] **Position Management Flow**
  1. User selects NFLX from main dropdown
  2. User navigates to "💼 POSITION MANAGEMENT" tab
  3. Component displays current divergence state
  4. Profit-taking rules table renders
  5. Re-entry rules display correctly

---

## 7. File Change Summary

### Files to Modify

| File | Lines to Change | Type | Priority |
|------|----------------|------|----------|
| `frontend/src/App.tsx` | 90 | Add TSLA/NFLX to array | High |
| `frontend/src/components/MultiTimeframeGuide.tsx` | 825-836 | Add TSLA/NFLX tabs | High |
| `backend/api.py` | 36-40, 64 | Add imports and default tickers | High |
| `backend/stock_statistics.py` | ~250, ~380 | Add data structures and metadata | High |

### Files That Need NO Changes

✅ `frontend/src/api/client.ts` - Already dynamic
✅ `frontend/src/types/index.ts` - Type definitions are ticker-agnostic
✅ All 13 component files - They accept ticker as prop

---

## 8. Deployment Sequence

### Phase 1: Backend Data Generation
1. Run `python backend/generate_tsla_stats.py`
2. Copy generated TSLA_4H_DATA and TSLA_DAILY_DATA
3. Paste into `stock_statistics.py`
4. Run `python backend/generate_nflx_stats.py`
5. Copy generated NFLX_4H_DATA and NFLX_DAILY_DATA
6. Paste into `stock_statistics.py`
7. Analyze data and fill in STOCK_METADATA entries
8. Update imports in `api.py`
9. Update DEFAULT_TICKERS in `api.py`

### Phase 2: Frontend Integration
1. Update DEFAULT_TICKERS in `App.tsx`
2. Update MultiTimeframeGuide tabs
3. Test ticker selection in dropdown
4. Test all components with TSLA
5. Test all components with NFLX

### Phase 3: Verification
1. Run full test suite (see section 6)
2. Verify data accuracy against TradingView
3. Check for any console errors
4. Test on multiple browsers
5. Monitor API response times

---

## 9. Potential Issues & Mitigations

### Issue 1: Missing TSLA/NFLX Data in Backend

**Symptom:** API returns 404 or empty data
**Cause:** Data generation scripts not run or data not added to `stock_statistics.py`
**Mitigation:**
- Add error handling in API endpoints to return informative errors
- Create placeholder data structures with "TBD" values
- Display friendly error message in frontend: "TSLA data is being generated"

### Issue 2: Different Data Characteristics

**Symptom:** TSLA/NFLX charts look odd or break UI
**Cause:** Higher volatility or different statistical distribution
**Mitigation:**
- Verify BinStatistics calculations match other stocks
- Ensure percentile bins use same ranges (0-5, 5-15, etc.)
- Test with edge cases (very high/low returns)

### Issue 3: Tab Index Mismatch

**Symptom:** Clicking "TSLA" tab shows wrong stock data
**Cause:** Array index calculation error in MultiTimeframeGuide
**Mitigation:**
- Use the recommended constant approach (AVAILABLE_STOCKS)
- Add `key` props to all Tab components
- Test tab switching extensively

### Issue 4: API Performance

**Symptom:** Slow loading times with 12 stocks instead of 10
**Cause:** More data to process and cache
**Mitigation:**
- Implement caching for TSLA/NFLX data
- Use React Query's built-in caching (already in place)
- Consider lazy loading for less frequently used stocks

---

## 10. Code Quality & Maintainability

### Recommended Refactorings

**1. Create a Stock Constants File**

```typescript
// frontend/src/constants/stocks.ts
export const ALL_TICKERS = [
  'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META',
  'TSLA', 'NFLX', 'QQQ', 'SPY', 'GLD', 'SLV'
];

export const MULTI_TIMEFRAME_STOCKS = [
  'NVDA', 'MSFT', 'GOOGL', 'AAPL', 'GLD', 'SLV', 'TSLA', 'NFLX'
];

export const DEFAULT_TICKER = 'AAPL';
```

**2. Use Constants in Components**

```typescript
// In App.tsx
import { ALL_TICKERS, DEFAULT_TICKER } from '@/constants/stocks';

// In MultiTimeframeGuide.tsx
import { MULTI_TIMEFRAME_STOCKS } from '@/constants/stocks';
```

**Benefits:**
- Single source of truth
- Easy to add more stocks in future
- Type-safe imports
- Better for testing

### Style Consistency

**Current:** Mixed inline arrays and hardcoded values
**Recommended:** Extract all stock lists to constants
**Impact:** Improves maintainability and reduces bugs

---

## 11. Documentation Updates Needed

### User-Facing Documentation

- [ ] Update README with TSLA/NFLX availability
- [ ] Add TSLA-specific trading guidance
- [ ] Add NFLX-specific trading guidance
- [ ] Update screenshots to show 12 stocks
- [ ] Document any unique TSLA/NFLX characteristics

### Developer Documentation

- [ ] Update API documentation with TSLA/NFLX endpoints
- [ ] Document data generation process
- [ ] Add examples for adding future stocks
- [ ] Update component prop documentation

---

## 12. Performance Monitoring

### Metrics to Track

- **API Response Times:**
  - Baseline: Current average for GLD/SLV
  - Target: TSLA/NFLX within 10% of baseline

- **Frontend Bundle Size:**
  - Baseline: Current bundle size
  - Target: Minimal increase (<5KB)

- **User Engagement:**
  - Track TSLA/NFLX selection frequency
  - Monitor component load times
  - Analyze error rates

### Monitoring Tools

- Browser DevTools Network tab
- React Query DevTools
- Console error tracking
- User analytics (if implemented)

---

## 13. Rollback Plan

### If Issues Occur Post-Deployment

**Quick Rollback:**
1. Revert `App.tsx` DEFAULT_TICKERS to 10 stocks
2. Revert `MultiTimeframeGuide.tsx` tabs to 6 stocks
3. Revert `api.py` DEFAULT_TICKERS to 10 stocks
4. Clear frontend cache

**Partial Rollback:**
- Remove only TSLA or only NFLX if one has issues
- Keep working stock in production
- Debug problematic stock separately

**No Rollback Needed:**
- If backend data is missing, frontend gracefully shows error
- Users can still use all other stocks normally

---

## 14. Success Criteria

### Definition of Done

- ✅ TSLA appears in all stock selectors
- ✅ NFLX appears in all stock selectors
- ✅ All 13 components render correctly for TSLA
- ✅ All 13 components render correctly for NFLX
- ✅ API endpoints return valid data for both stocks
- ✅ No console errors when selecting TSLA/NFLX
- ✅ Loading states work correctly
- ✅ Error handling gracefully manages missing data
- ✅ All tests pass (see section 6)
- ✅ Documentation updated
- ✅ Code reviewed and approved

---

## 15. Next Steps for Coder Agent

Based on this analysis, the Coder Agent should:

1. **Immediate Actions:**
   - Update `App.tsx` line 90
   - Update `MultiTimeframeGuide.tsx` lines 825-836
   - Create `frontend/src/constants/stocks.ts` (recommended)

2. **Backend Coordination:**
   - Ensure backend team has run TSLA/NFLX generation scripts
   - Verify `stock_statistics.py` has TSLA/NFLX data
   - Confirm `api.py` imports are updated

3. **Testing:**
   - Test ticker selection in dropdown
   - Test all tabs with TSLA/NFLX
   - Verify API calls succeed
   - Check for console errors

4. **Documentation:**
   - Update component comments
   - Add TSLA/NFLX to README
   - Document any unique behavior

---

## 16. Coordination Notes

### Memory Keys Used

- `swarm/analyst/frontend-spec` - This specification document
- `swarm/researcher/integration-plan` - High-level plan (if exists)

### Notify Messages

- "Frontend analysis complete: 2 files need updates, 13 components work as-is"
- "TSLA/NFLX can be added with minimal changes - architecture already supports dynamic tickers"

### Handoff to Coder Agent

**Summary:** The frontend is already architected for dynamic ticker support. Only hardcoded stock lists in 2 files need updating. All components receive ticker as a prop and make dynamic API calls, so they'll work immediately with TSLA/NFLX once added to the selector arrays.

**Priority Files:**
1. `frontend/src/App.tsx` (1 line change)
2. `frontend/src/components/MultiTimeframeGuide.tsx` (tab array update)

**Optional Improvements:**
- Create `constants/stocks.ts` for centralized stock management
- Refactor hardcoded arrays to use constants

**No Changes Needed:**
- API client (already dynamic)
- Type definitions (ticker-agnostic)
- 13 component files (accept ticker prop)

---

## Appendix A: Complete File Diff Summary

### `frontend/src/App.tsx`

```diff
- const DEFAULT_TICKERS = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'QQQ', 'SPY', 'GLD', 'SLV'];
+ const DEFAULT_TICKERS = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'QQQ', 'SPY', 'GLD', 'SLV', 'TSLA', 'NFLX'];
```

### `frontend/src/components/MultiTimeframeGuide.tsx`

```diff
+ const AVAILABLE_STOCKS = ['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'GLD', 'SLV', 'TSLA', 'NFLX'];

  <Tabs
-   value={['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'GLD', 'SLV'].indexOf(selectedStock)}
-   onChange={(_, newValue) =>
-     setSelectedStock(['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'GLD', 'SLV'][newValue])
-   }
+   value={AVAILABLE_STOCKS.indexOf(selectedStock)}
+   onChange={(_, newValue) => setSelectedStock(AVAILABLE_STOCKS[newValue])}
  >
-   <Tab label="NVDA" />
-   <Tab label="MSFT" />
-   <Tab label="GOOGL" />
-   <Tab label="AAPL" />
-   <Tab label="GLD" />
-   <Tab label="SLV" />
+   {AVAILABLE_STOCKS.map(ticker => (
+     <Tab key={ticker} label={ticker} />
+   ))}
  </Tabs>
```

### `backend/api.py`

```diff
  from stock_statistics import (
      STOCK_METADATA,
      NVDA_4H_DATA, NVDA_DAILY_DATA,
      MSFT_4H_DATA, MSFT_DAILY_DATA,
      GOOGL_4H_DATA, GOOGL_DAILY_DATA,
      AAPL_4H_DATA, AAPL_DAILY_DATA,
      GLD_4H_DATA, GLD_DAILY_DATA,
-     SLV_4H_DATA, SLV_DAILY_DATA
+     SLV_4H_DATA, SLV_DAILY_DATA,
+     TSLA_4H_DATA, TSLA_DAILY_DATA,
+     NFLX_4H_DATA, NFLX_DAILY_DATA
  )

- DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "QQQ", "SPY", "GLD", "SLV"]
+ DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "QQQ", "SPY", "GLD", "SLV", "TSLA", "NFLX"]
```

---

**End of Frontend Integration Specification**

**Prepared by:** Analyst Agent
**For:** Hive Mind Swarm - TSLA/NFLX Integration Task
**Coordination:** Memory stored at `swarm/analyst/frontend-spec`
