# MACD-V (MACD Volatility-Normalized) Implementation

## Overview
MACD-V is a Pine Script v6 indicator that normalizes the MACD by ATR volatility, making it suitable for cross-asset and cross-regime comparison.

## Implementation Summary

### Backend Components

#### 1. MACD-V Calculator (`backend/macdv_calculator.py`)
- **Class**: `MACDVCalculator`
- **Parameters**:
  - `fast_length`: 12 (EMA fast period)
  - `slow_length`: 26 (EMA slow period)
  - `signal_length`: 9 (Signal line EMA period)
  - `atr_length`: 26 (ATR normalization period)

- **Methods**:
  - `calculate_macdv()`: Calculates MACD-V, signal, histogram, color, and trend
  - `get_dashboard_data()`: Fetches multi-ticker, multi-timeframe data
  - `prepare_chart_data()`: Formats data for frontend charts

- **Color Classification**:
  - **Gray (Ranging)**: -50 < MACD-V < 50 for 19+ bars
  - **Blue (Risk)**: |MACD-V| ≥ 150 (extreme zones)
  - **Green-Dark (Rallying)**: 50 ≤ MACD-V < 150 and rising
  - **Green (Rebounding)**: -150 < MACD-V < 50 and rising
  - **Orange (Retracing)**: MACD-V > -50 and falling
  - **Red (Reversing)**: -150 < MACD-V ≤ -50 and falling

#### 2. API Endpoints (`backend/api.py`)
Added two new endpoints:

##### GET `/api/macdv-chart/{ticker}`
Fetches MACD-V chart data for a single ticker.
- **Parameters**:
  - `ticker`: Stock symbol (e.g., 'AAPL', 'ES=F', 'BTC-USD')
  - `days`: Number of days (default: 252)
- **Returns**: Chart data with MACD-V values, histogram, colors, and trends

##### GET `/api/macdv-dashboard`
Fetches MACD-V dashboard with all swing framework tickers across multiple timeframes.
- **Parameters**:
  - `timeframes`: Comma-separated timeframes (default: '1mo,1wk,1d')
- **Returns**: Dashboard with MACD-V values for all tickers

### Frontend Components

#### 1. API Client (`frontend/src/api/client.ts`)
Added `macdvApi` object with two methods:
- `getMACDVChartData(ticker, days)`: Fetch chart data
- `getMACDVDashboard(timeframes)`: Fetch dashboard data

#### 2. MACD-V Indicator Page (`frontend/src/pages/MACDVIndicatorPage.tsx`)
React component with two modes:

##### Chart Mode
- **Visualization**: MACD-V oscillator with:
  - Histogram (green/red bars)
  - MACD-V line (blue)
  - Signal line (red)
  - Horizontal zone lines (0, ±50, ±150)

- **Current Metrics Cards**:
  - MACD-V Value
  - Signal Line
  - Histogram
  - Current Price

- **Signal Interpretation**:
  - Bullish Zones explanation
  - Bearish Zones explanation

##### Dashboard Mode
- **Table View**: All swing framework tickers × selected timeframes
- **Columns**: Ticker | Monthly | Weekly | Daily
- **Cell Data**: MACD-V value + trend classification
- **Color Coding**: Green (Bullish), Red (Bearish), Gray (Ranging/Neutral)

#### 3. App Integration (`frontend/src/App.tsx`)
- Added lazy-loaded import for `MACDVIndicatorPage`
- Added new tab: "MACD-V (Momentum)" (Tab index 17)
- Positioned after "MAPI (Momentum)" tab

## Swing Framework Tickers
The dashboard uses all 33 tickers from `DEFAULT_TICKERS`:
```
'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'QQQ', 'SPY',
'GLD', 'SLV', 'TSLA', 'NFLX', 'BRK-B', 'WMT', 'UNH', 'AVGO',
'LLY', 'TSM', 'ORCL', 'OXY', 'XOM', 'CVX', 'JPM', 'BAC',
'CNX1', 'CSP1', 'BTCUSD', 'ES1', 'NQ1', 'VIX', 'IGLS', 'USDGBP', 'US10'
```

## Usage

### Accessing the MACD-V Tab
1. Open the application
2. Navigate to the tabs at the top
3. Click on **"MACD-V (Momentum)"** (after MAPI tab)

### Chart Mode
- View MACD-V oscillator for the selected ticker
- See current MACD-V value, signal, and histogram
- Interpret bullish/bearish zones based on MACD-V levels

### Dashboard Mode
- View all swing framework tickers at once
- Compare MACD-V across Monthly, Weekly, and Daily timeframes
- Identify which assets are in bullish/bearish/ranging zones

## Technical Details

### MACD-V Calculation
```python
# 1. Calculate standard MACD
fast_ma = EMA(close, 12)
slow_ma = EMA(close, 26)
macd = fast_ma - slow_ma

# 2. Calculate ATR
atr = ATR(26)

# 3. Normalize MACD by ATR
macdv = (macd / atr) * 100

# 4. Calculate signal line
signal = EMA(macdv, 9)

# 5. Calculate histogram
histogram = macdv - signal
```

### Trend Classification Logic
```python
if in_range and bars_since_range >= 19:
    trend = 'Ranging'
elif macdv > 50:
    trend = 'Bullish'
elif macdv < -50:
    trend = 'Bearish'
else:
    trend = 'Neutral'
```

## Benefits of MACD-V

1. **Volatility Normalization**: ATR normalization allows fair comparison across:
   - Different assets (stocks, futures, crypto)
   - Different market regimes (low/high volatility)

2. **Zone-Based Signals**:
   - Clear entry/exit zones (±50, ±150)
   - Ranging detection (19+ bars in ±50 zone)

3. **Multi-Timeframe Analysis**:
   - Compare same asset across timeframes
   - Identify alignment/divergence

4. **Cross-Asset Scanning**:
   - Dashboard view of all swing framework assets
   - Quickly identify which assets are in favorable zones

## Files Created/Modified

### Created
- `backend/macdv_calculator.py` - MACD-V calculation engine
- `frontend/src/pages/MACDVIndicatorPage.tsx` - React component
- `docs/MACDV_IMPLEMENTATION.md` - This documentation

### Modified
- `backend/api.py` - Added MACD-V API endpoints
- `frontend/src/api/client.ts` - Added macdvApi client
- `frontend/src/App.tsx` - Added MACD-V tab

## Next Steps

1. **Test the implementation**:
   ```bash
   # Start backend
   cd backend
   python api.py

   # Start frontend (in another terminal)
   cd frontend
   npm run dev
   ```

2. **Navigate to the MACD-V tab** and verify:
   - Chart mode loads correctly
   - Dashboard mode displays all tickers
   - Data updates properly when switching tickers

3. **Future Enhancements**:
   - Add historical analysis (like MAPI Historical tab)
   - Add market scanner functionality
   - Add signal alerts/notifications
   - Add custom timeframe selection in dashboard

## Questions or Issues?

If you encounter any issues:
1. Check browser console for frontend errors
2. Check backend logs for API errors
3. Verify all dependencies are installed:
   ```bash
   pip install yfinance pandas numpy
   npm install
   ```
