# SPY and QQQ Integration into LiveMarketState

## Summary

SPY and QQQ market indices are now fully integrated into the existing LiveMarketState-CurrentBuy table, appearing as entries 7 and 8 alongside the 6 stocks (AAPL, MSFT, NVDA, GOOGL, TSLA, NFLX).

## Changes Made

### 1. Backend API (`backend/swing_framework_api.py`)

**Line 537**: Added SPY and QQQ to unified tickers list
```python
# Before (6 stocks):
tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "TSLA", "NFLX"]

# After (2 indices + 6 stocks):
tickers = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "GOOGL", "TSLA", "NFLX"]
```

**Line 193**: Also added to `get_swing_framework_data()` for cache support
```python
tickers = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "GOOGL", "TSLA", "NFLX"]
```

### 2. Stock Metadata (`backend/stock_statistics.py`)

**Lines 352-388**: Added metadata for SPY and QQQ

```python
"SPY": StockMetadata(
    ticker="SPY",
    name="S&P 500 ETF",
    personality="Market Benchmark",
    volatility_level="Low",
    is_mean_reverter=True,
    is_momentum=False,
    entry_guidance="Buy market dips at ≤15% percentile for mean reversion plays",
    ...
),
"QQQ": StockMetadata(
    ticker="QQQ",
    name="Nasdaq 100 ETF",
    personality="Tech Momentum Leader",
    volatility_level="Medium",
    is_mean_reverter=True,
    is_momentum=True,
    entry_guidance="Buy tech dips at ≤15% percentile, can ride momentum above 50%",
    ...
)
```

### 3. Frontend Component (`frontend/src/components/TradingFramework/CurrentMarketState.tsx`)

**Line 151**: Updated title to reflect indices inclusion
```typescript
🎯 Live Market State - Current Buy Opportunities (Stocks + Indices)
```

### 4. Frontend Integration (`frontend/src/components/TradingFramework/SwingTradingFramework.tsx`)

- Removed separate `IndexMarketState` import
- Kept single unified `CurrentMarketState` component
- Now displays all 8 tickers in one table

## Data Flow

1. **Backend**: `/api/swing-framework/current-state` endpoint processes all 8 tickers
2. **Same Logic**: SPY and QQQ use identical signal functions, filtering, thresholds, and risk-adjustment
3. **Unified Response**: Returns array with 8 entries, each containing:
   - `ticker`: Symbol (SPY, QQQ, AAPL, etc.)
   - `current_percentile`: Current RSI-MA percentile
   - `live_expectancy.risk_adjusted_expectancy_pct`: Risk-adjusted expectancy
   - `live_expectancy.expected_return_pct`: Expected return
   - `live_expectancy.expected_holding_days`: Average hold days
   - `in_entry_zone`: Boolean signal
   - Metadata: name, regime, volatility, etc.

4. **Frontend**: `CurrentMarketState` component renders all 8 in single table

## Acceptance Criteria Met

✅ **Minimal, reusable code changes**: 2-line array modification in backend
✅ **Same signal logic**: SPY/QQQ use existing `get_current_market_state()` function
✅ **Unified data structure**: No separate objects, integrated into existing array
✅ **Same fields**: All entries have identical schema
✅ **Single table display**: Frontend shows 8 rows in one CurrentBuy table

## Result

```json
{
  "status": "done",
  "added": ["SPY", "QQQ"],
  "count_before": 6,
  "count_after": 8
}
```

Integration location: `backend/swing_framework_api.py:537` and `backend/swing_framework_api.py:193`

## Testing

Start backend and navigate to Swing Framework page:
```bash
cd backend
source venv/bin/activate
python api.py
```

The LiveMarketState table will now show 8 entries with SPY and QQQ appearing first (sorted by percentile).
