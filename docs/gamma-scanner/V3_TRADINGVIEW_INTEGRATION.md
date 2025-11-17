# Gamma Wall Scanner v3.0 - Full TradingView Integration

## Overview

Version 3.0 represents the complete transformation of the Gamma Wall Scanner into a high-fidelity TradingView-style charting application. This version integrates traditional candlestick price action with gamma walls as dynamic support/resistance overlays.

## Key Features

### 1. **Candlestick Chart Integration**
- Traditional Japanese candlestick chart (OHLC data)
- Green candles (`#26A69A`) for bullish moves
- Red candles (`#EF5350`) for bearish moves
- Time-based X-axis (dates) instead of generic 0-100 scale
- Price axis positioned on the right side (TradingView standard)

### 2. **Gamma Walls as Support/Resistance Overlays**
- **Put Walls (Support)**: Light green/cyan `rgba(38, 166, 154, 0.25)`
- **Call Walls (Resistance)**: Light red/magenta `rgba(239, 83, 80, 0.25)`
- Wall strength represented by:
  - **Line thickness**: 1-3px based on strength (0-100)
  - **Opacity**: Increases with strength
- Horizontal lines extend across entire visible time window

### 3. **Timeframe Selector**
Located in top bar with 5 options:
- **5M** - 5 Minute candles
- **15M** - 15 Minute candles
- **1H** - Hourly candles
- **4H** - 4 Hour candles
- **1D** - Daily candles (default)

### 4. **Key Price Levels**
- **Current Price**: White solid line (`#FFFFFF`) with right-side label
- **Gamma Flip**: Orange dashed line (`#FFA726`) - critical pivot level
- **SD Bands**: Faint dotted lines for ±1σ, ±1.5σ, ±2σ zones

### 5. **Bottom Metrics Panel**
- Collapsible panel below chart (toggle with ▼/▲)
- Displays Symbol Metrics Table with:
  - Symbol, Price, Gamma Flip, IV%
  - ST/LT Put/Call walls with strikes and strengths
  - Standard deviation bands (-1σ, +1σ)
  - Total GEX (Gamma Exposure)

### 6. **TradingView Layout Structure**
```
┌─────────────────────────────────────────────────────┐
│ TOP BAR: Title | VIX | Regime | Time | [5M 15M 1H 4H 1D] | Status │
├───────┬─────────────────────────────────────────────┤
│       │                                             │
│ Side  │          Candlestick Chart                  │
│ bar   │     with Gamma Wall Overlays               │
│       │                                             │
│ (280px│                                             │
│  or   │                                             │
│ 40px) │                                             │
│       ├─────────────────────────────────────────────┤
│       │ BOTTOM PANEL: Symbol Metrics [▼/▲]         │
│       │ [Collapsible Table]                         │
└───────┴─────────────────────────────────────────────┘
```

## Technical Implementation

### Component Architecture

#### **GammaChartCanvas.v3.tsx**
Main chart rendering component using Plotly.js:

**Props:**
```typescript
interface GammaChartCanvasV3Props {
  symbols: ParsedSymbolData[];
  settings: GammaScannerSettings;
  marketRegime: string;
  timeframe: '1D' | '1H' | '5M' | '15M' | '4H';
}
```

**Chart Layers (bottom to top):**
1. **Candlestick trace** (base layer)
2. **Standard deviation bands** (background context)
3. **Gamma walls** (support/resistance zones)
4. **Current price line** (white, prominent)
5. **Gamma flip line** (orange, dashed)

**Key Functions:**
- `generateCandlestickData(symbol, days)` - Generates synthetic OHLC data
  - Currently generates demo data for testing
  - Production should fetch real historical price data via API
- `applyRegimeAdjustment()` - Adjusts wall strength based on VIX regime

#### **GammaScannerTab.v3.tsx**
Main container with full layout management:

**State Management:**
```typescript
const [timeframe, setTimeframe] = useState<TimeframeOption>('1D');
const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
const [metricsExpanded, setMetricsExpanded] = useState<boolean>(true);
```

**Features:**
- Auto-refresh every 5 minutes (configurable)
- API polling with error handling
- Manual paste mode fallback
- Loading states and error banners

#### **SymbolMetricsTable.tsx**
Compact metrics display in TradingView style:

**Columns:**
| Symbol | Price | Γ Flip | IV% | ST Put | ST Call | LT Put | LT Call | -1σ | +1σ | Total GEX |
|--------|-------|--------|-----|--------|---------|--------|---------|-----|-----|-----------|

**Styling:**
- Dark surface background `#1E222D`
- Alternating row colors for readability
- Color-coded walls: Green (put), Red (call), Orange (flip)

### Color Palette (TradingView Standard)

```typescript
const TRADINGVIEW_COLORS = {
  background: '#131722',   // Main canvas background
  surface: '#1E222D',      // Panels, sidebar, table
  gridline: '#2A2E39',     // Grid and borders
  text: '#787B86',         // Secondary text
  textBright: '#D1D4DC',   // Primary text
  candleUp: '#26A69A',     // Green candles (bullish)
  candleDown: '#EF5350',   // Red candles (bearish)
  putWall: 'rgba(38, 166, 154, 0.25)',   // Light green (support)
  callWall: 'rgba(239, 83, 80, 0.25)',   // Light red (resistance)
  gammaFlip: '#FFA726',    // Bright orange (pivot)
  currentPrice: '#FFFFFF', // Pure white (most important)
  sdBand: 'rgba(120, 123, 134, 0.08)',   // Faint gray
};
```

## Data Flow

```
1. API Endpoint
   /api/gamma-data
   ↓
2. GammaDataParser
   parseLevelData() → ParsedSymbolData[]
   ↓
3. GammaScannerTab.v3
   State management, polling, error handling
   ↓
4. GammaChartCanvas.v3
   Generate candlesticks + plot gamma walls
   ↓
5. Plotly.js
   Render interactive chart with zoom/pan
   ↓
6. SymbolMetricsTable
   Display summary metrics below chart
```

## Setup and Usage

### Prerequisites
```bash
cd frontend
npm install plotly.js-basic-dist
```

### Start Development
```bash
# Terminal 1 - Backend
cd backend
python api.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Access
- Frontend: http://localhost:3001
- Navigate to: **🔰 GAMMA WALL SCANNER** tab
- API: http://localhost:8000/api/gamma-data

### Configuration

**Auto-Refresh Interval:**
Edit `GammaScannerTab.v3.tsx`:
```typescript
const interval = setInterval(fetchData, 5 * 60 * 1000); // 5 minutes
```

**Default Timeframe:**
```typescript
const [timeframe, setTimeframe] = useState<TimeframeOption>('1D');
```

**Candlestick Data Period:**
```typescript
const candleData = generateCandlestickData(primarySymbol, 30); // 30 days
```

## Production Considerations

### Historical Price Data Integration

**Current Implementation (Demo):**
```typescript
const generateCandlestickData = (symbol: ParsedSymbolData, days: number = 30) => {
  // Generates synthetic OHLC data for demonstration
  // Uses random walk with volatility based on symbol.swingIV
}
```

**Production Implementation Required:**
```typescript
const fetchHistoricalPriceData = async (
  symbol: string,
  timeframe: string,
  startDate: Date,
  endDate: Date
) => {
  // Fetch real OHLC data from:
  // - Yahoo Finance API
  // - Alpha Vantage
  // - Polygon.io
  // - IEX Cloud
  // - Internal data provider

  return {
    dates: Date[],
    opens: number[],
    highs: number[],
    lows: number[],
    closes: number[]
  };
}
```

**Backend Endpoint Needed:**
```python
@router.get("/api/ohlc-data/{symbol}")
async def get_ohlc_data(
    symbol: str,
    timeframe: str = "1D",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Fetch historical OHLC data for symbol
    Returns: {dates: [], opens: [], highs: [], lows: [], closes: []}
    """
    # Implement using yfinance or other data provider
    pass
```

### Performance Optimizations

**Large Datasets:**
- Implement data windowing (only load visible time range)
- Use Plotly's `scattergl` for large datasets (WebGL acceleration)
- Lazy load historical data as user zooms/pans

**Memory Management:**
- Cache candlestick data in localStorage
- Implement data eviction for old timeframes
- Use React.memo for expensive components

**API Optimization:**
- Implement WebSocket for real-time updates
- Use ETags for conditional requests
- Batch multiple symbol requests

## Testing Checklist

### Visual Verification
- [ ] Candlesticks render correctly (green/red colors)
- [ ] Gamma walls appear as horizontal overlays
- [ ] Put walls are light green/cyan
- [ ] Call walls are light red/magenta
- [ ] Current price line is white and prominent
- [ ] Gamma flip line is orange and dashed
- [ ] SD bands are faint dotted lines
- [ ] Price axis is on right side
- [ ] Time axis shows dates (not 0-100 scale)

### Functional Testing
- [ ] Timeframe selector switches between 5M/15M/1H/4H/1D
- [ ] Sidebar collapses/expands (40px ↔ 280px)
- [ ] Bottom metrics panel toggles (▼/▲)
- [ ] Symbol metrics table displays all columns
- [ ] API data loads successfully
- [ ] Manual paste mode works
- [ ] Error banner appears on failure
- [ ] Loading spinner shows during fetch
- [ ] Auto-refresh works (5 min intervals)

### Interaction Testing
- [ ] Chart zoom (mouse wheel)
- [ ] Chart pan (click and drag)
- [ ] Hover tooltips show wall details
- [ ] Legend shows/hides traces
- [ ] Wall strength affects line thickness
- [ ] Regime adjustment modifies wall strength
- [ ] Settings panel updates chart in real-time

## Migration from v2 to v3

**Index.ts Export Change:**
```typescript
// OLD (v2)
export { GammaScannerTabV2 as GammaScannerTab } from './GammaScannerTab.v2';

// NEW (v3)
export { GammaScannerTabV3 as GammaScannerTab } from './GammaScannerTab.v3';
```

**App.tsx Integration:**
No changes required - v3 maintains same export name:
```typescript
import { GammaScannerTab } from './components/GammaScanner';
```

**Rollback Process:**
```typescript
// In index.ts, revert to v2
export { GammaScannerTabV2 as GammaScannerTab } from './GammaScannerTab.v2';
```

## Known Limitations

1. **Synthetic Candlestick Data**
   - Currently uses generated demo data
   - Needs real historical price API integration

2. **Single Symbol Display**
   - Chart shows primary symbol only
   - Multi-symbol overlay planned for future

3. **Fixed Time Window**
   - Currently generates 30 days of data
   - Should be dynamic based on timeframe selection

4. **No Real-time Updates**
   - Polling interval is 5 minutes
   - WebSocket integration needed for true real-time

## Future Enhancements

### Phase 1 - Data Integration
- [ ] Real historical price data API
- [ ] Multi-symbol overlay support
- [ ] Dynamic time window based on timeframe
- [ ] WebSocket for real-time updates

### Phase 2 - Advanced Features
- [ ] Drawing tools (trendlines, rectangles)
- [ ] Technical indicators (RSI, MACD, Bollinger Bands)
- [ ] Alert system for price crossing gamma walls
- [ ] Custom wall highlighting/annotation

### Phase 3 - Professional Tools
- [ ] Save/load chart layouts
- [ ] Export chart as image
- [ ] Advanced order flow visualization
- [ ] Delta-neutral level calculation

## Support and Documentation

**File Reference:**
- Implementation: `frontend/src/components/GammaScanner/GammaScannerTab.v3.tsx`
- Chart Logic: `frontend/src/components/GammaScanner/GammaChartCanvas.v3.tsx`
- Metrics Table: `frontend/src/components/GammaScanner/SymbolMetricsTable.tsx`
- Type Definitions: `frontend/src/components/GammaScanner/types.ts`

**Related Docs:**
- `V2_DESIGN.md` - Design philosophy and color palette
- `README.md` - General integration guide
- `QUICK_START_V2.md` - Quick setup instructions

---

**Version:** 3.0.0
**Last Updated:** November 7, 2025
**Status:** ✅ Production Ready (requires real OHLC data integration)
