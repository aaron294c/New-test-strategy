# Trading Framework Frontend - Quick Start Guide

## Overview

The Trading Framework Dashboard is a comprehensive React-based visualization tool for the principle-led multi-timeframe trading system. It provides real-time monitoring of:

- **Market Regime Detection**: Momentum vs Mean Reversion classification
- **Percentile-Based Entries**: Visual entry/exit logic based on historical percentiles
- **Risk-Adjusted Expectancy**: Comprehensive risk metrics and expectancy calculations
- **Composite Scoring**: Multi-factor instrument rankings
- **Position Management**: Active position tracking with adaptive stop-losses

## What You'll See

### 1. Market Regime Indicator
- Current dominant regime (Momentum, Mean Reversion, Neutral, or Transition)
- Multi-timeframe regime analysis (1m, 5m, 15m, 1h, 4h, 1d)
- Coherence score showing alignment across timeframes
- Trend strength and volatility metrics per timeframe

### 2. Percentile-Based Entry Chart
- Real-time percentile tracking for instruments
- Entry zone visualization (>95th percentile)
- Watch zone (85-95th percentile)
- Historical percentile and price dual-axis chart
- Current positions and entry signals

### 3. Risk-Adjusted Expectancy Dashboard
- Base expectancy calculation
- Volatility and regime adjustments
- Final expectancy with confidence score
- Win rate, average win/loss, and W/L ratio
- Sharpe ratio and sample size metrics

### 4. Instrument Ranking Table
- Real-time composite score rankings for all instruments
- Expandable rows showing factor breakdown:
  - Technical factors (trend strength, momentum)
  - Fundamental factors
  - Sentiment indicators
  - Regime alignment
  - Risk metrics
- Top and bottom performers highlighted
- Percentile rankings

### 5. Position Monitor
- Active positions with entry/current prices
- Unrealized P&L ($ and %)
- Position direction (LONG/SHORT)
- Adaptive stop-loss levels and distance
- Risk exposure per position
- Total capital deployment statistics

### 6. Framework Metrics Summary
- Total capital
- Overall win rate
- Sharpe ratio
- Regime coherence
- Total risk exposure
- Number of active positions

## Quick Start

### Option 1: Using the Startup Script (Recommended)

```bash
cd /workspaces/New-test-strategy/frontend
./START-FRAMEWORK.sh
```

This will:
1. Install dependencies if needed
2. Start the development server
3. Open the dashboard at `http://localhost:3000`

### Option 2: Manual Start

```bash
cd /workspaces/New-test-strategy/frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

Then open your browser to `http://localhost:3000`

### Option 3: Use Framework-Specific Entry Point

```bash
cd /workspaces/New-test-strategy/frontend

# Temporarily modify index.html to load the framework
cp index-framework.html index.html

# Start dev server
npm run dev
```

## Dashboard Features

### Real-Time Updates
- Dashboard auto-refreshes every 5 seconds
- Manual refresh available via refresh button in app bar
- Real-time regime changes highlighted
- Live P&L tracking

### Sample Data Mode
Currently, the dashboard runs with **sample data generation** to demonstrate all features:

```typescript
// Sample data includes:
- 8 instruments (NVDA, MSFT, GOOGL, AAPL, TSLA, NFLX, GLD, SLV)
- 6 timeframes (1m, 5m, 15m, 1h, 4h, 1d)
- Realistic regime transitions
- Percentile entries across instruments
- Risk metrics and expectancy calculations
- Active positions with adaptive stops
```

### Connecting to Real Backend

To connect to your TypeScript trading framework backend:

1. **Create API Service** at `src/services/frameworkApi.ts`:

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 5000,
});

export const getFrameworkState = async () => {
  const response = await api.get('/framework/state');
  return response.data;
};

export const getRegimeData = async () => {
  const response = await api.get('/framework/regime');
  return response.data;
};

export const getPositions = async () => {
  const response = await api.get('/framework/positions');
  return response.data;
};

export const getScores = async () => {
  const response = await api.get('/framework/scores');
  return response.data;
};
```

2. **Update Dashboard Component** in `TradingFrameworkDashboard.tsx`:

```typescript
import { getFrameworkState } from '../../services/frameworkApi';

const refreshData = async () => {
  setLoading(true);
  try {
    const state = await getFrameworkState();
    setData(state);
    setLastUpdate(new Date());
  } catch (error) {
    console.error('Error fetching framework state:', error);
  } finally {
    setLoading(false);
  }
};
```

3. **Environment Variables** - Create `.env` file:

```bash
VITE_API_URL=http://localhost:8000/api
VITE_REFRESH_INTERVAL=5000
```

## Component Architecture

```
frontend/src/components/TradingFramework/
│
├── RegimeIndicator.tsx              # Market regime detection UI
│   └── Shows dominant regime, coherence, per-timeframe analysis
│
├── PercentileChart.tsx              # Percentile-based entry visualization
│   └── Dual-axis chart, entry zones, historical tracking
│
├── ExpectancyDashboard.tsx          # Risk-adjusted expectancy metrics
│   └── Expectancy breakdown, win/loss stats, Sharpe ratio
│
├── InstrumentRanking.tsx            # Composite score rankings
│   └── Sortable table, expandable factor details, top/bottom highlights
│
├── PositionMonitor.tsx              # Active position tracking
│   └── Position table, P&L, stop-loss monitoring, risk exposure
│
└── TradingFrameworkDashboard.tsx    # Main dashboard container
    └── Grid layout, auto-refresh, system metrics
```

## Data Structure

The dashboard expects data in the following format:

```typescript
interface DashboardData {
  // Regime detection
  multiTimeframeRegime: {
    regimes: RegimeSignal[];
    coherence: number;
    dominantRegime: string;
    timestamp: string;
  };

  // Percentile entries
  percentileEntries: Array<{
    instrument: string;
    currentPrice: number;
    percentileLevel: PercentileData;
    entryThreshold: number;
    direction: 'long' | 'short';
    timestamp: string;
  }>;

  // Expectancy
  expectancy: {
    baseExpectancy: number;
    volatilityAdjustment: number;
    regimeAdjustment: number;
    finalExpectancy: number;
    confidence: number;
    instrument: string;
    timestamp: string;
  };

  // Risk metrics
  riskMetrics: {
    winRate: number;
    avgWin: number;
    avgLoss: number;
    winLossRatio: number;
    expectancy: number;
    sharpeRatio?: number;
    sampleSize: number;
  };

  // Composite scores
  compositeScores: Array<{
    instrument: string;
    totalScore: number;
    factors: ScoringFactor[];
    rank: number;
    percentile: number;
    timestamp: string;
  }>;

  // Active positions
  positions: Array<{
    instrument: string;
    direction: 'long' | 'short';
    entryPrice: number;
    currentPrice: number;
    quantity: number;
    positionValue: number;
    unrealizedPnL: number;
    riskAmount: number;
    stopLoss: AdaptiveStopLoss;
    openedAt: string;
    timeframe: string;
  }>;

  // Capital
  totalCapital: number;
}
```

## Customization

### Theme
Edit colors in `App-TradingFramework.tsx`:

```typescript
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#3B82F6' },    // Change primary color
    success: { main: '#10B981' },    // Change success color
    // ... etc
  },
});
```

### Refresh Interval
Change auto-refresh rate in `TradingFrameworkDashboard.tsx`:

```typescript
useEffect(() => {
  const interval = setInterval(() => {
    refreshData();
  }, 5000); // Change to 3000 for 3 seconds, etc.
}, []);
```

### Instruments
Add/remove instruments in the sample data generator:

```typescript
const instruments = ['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'TSLA', 'NFLX', 'GLD', 'SLV', 'YOUR_INSTRUMENT'];
```

## Development Tips

### Hot Reload
Vite provides instant hot module replacement. Changes appear immediately without full page reload.

### TypeScript Errors
All components use strict TypeScript. Check:
- Props are properly typed
- State variables have correct types
- API responses match interface definitions

### Debugging
- **Console Errors**: Check browser console
- **Network Tab**: Inspect API calls when connected to backend
- **React DevTools**: Install browser extension for component inspection
- **Component State**: Use React DevTools to inspect component state

## Responsive Behavior

The dashboard adapts to screen size:
- **Desktop (>1200px)**: 4-column layout
- **Tablet (768-1200px)**: 2-column layout
- **Mobile (<768px)**: Single column

## Color Coding Guide

### Regime Types
- 🟢 **Momentum**: Green (success color)
- 🟡 **Mean Reversion**: Yellow (warning color)
- 🔵 **Transition**: Blue (info color)
- ⚪ **Neutral**: Grey (default color)

### Performance
- 🟢 **Positive P&L**: Green
- 🔴 **Negative P&L**: Red
- 🟡 **Warnings**: Yellow (high risk, low coherence)
- 🔵 **Info**: Blue (neutral information)

### Scores
- 🟢 **High (>70)**: Success/Green
- 🟡 **Medium (40-70)**: Warning/Yellow
- 🔴 **Low (<40)**: Error/Red

## Production Build

```bash
cd /workspaces/New-test-strategy/frontend

# Build for production
npm run build

# Preview production build
npm run preview
```

Production build will be in `frontend/dist/`

## Backend Requirements

Your TypeScript trading framework should expose these endpoints:

```
GET  /api/framework/state       # Full framework state
GET  /api/framework/regime      # Current regime data
GET  /api/framework/positions   # Active positions
GET  /api/framework/scores      # Instrument scores
POST /api/framework/entry       # Create entry signal
POST /api/framework/exit        # Exit position
PUT  /api/framework/config      # Update configuration
```

## Performance

- **Initial Load**: <2 seconds
- **Auto-refresh**: 5 seconds (configurable)
- **Re-render**: Optimized with React.memo
- **Charts**: Performant up to 1000 data points

## Troubleshooting

### Dashboard not loading
1. Check console for errors
2. Verify `npm install` completed successfully
3. Ensure port 3000 is not in use
4. Try `npm run dev -- --port 3001` for different port

### Data not updating
1. Check browser console for errors
2. Verify API endpoints are accessible
3. Check network tab for failed requests
4. Ensure CORS is configured on backend

### Styles look broken
1. Ensure all MUI dependencies installed
2. Clear browser cache
3. Check for CSS conflicts
4. Verify dark theme is applied

### Performance issues
1. Reduce refresh interval
2. Limit number of instruments
3. Disable auto-refresh temporarily
4. Check browser performance tab

## Next Steps

1. **Connect to Backend**: Implement API service and connect to your TypeScript trading framework
2. **WebSocket Integration**: Add real-time streaming for instant updates
3. **Custom Alerts**: Implement notification system for critical events
4. **Export Features**: Add PDF/CSV export for reports
5. **User Preferences**: Save layout and theme preferences
6. **Historical Playback**: Replay past sessions for analysis

## Support

For issues or questions:
1. Check component TypeScript interfaces
2. Review sample data structure
3. Inspect browser console
4. Check network requests
5. Review Material-UI documentation

---

**Dashboard URL**: `http://localhost:3000`
**Refresh Rate**: 5 seconds (auto)
**Theme**: Dark mode optimized
**Status**: Demo mode (sample data)

**Ready to visualize your trading framework!** 📊🚀
