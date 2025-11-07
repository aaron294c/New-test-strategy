# Trading Framework Dashboard

A comprehensive React-based visualization dashboard for the principle-led multi-timeframe trading framework.

## Features

### 1. Market Regime Detection
**Component:** `RegimeIndicator.tsx`

- Real-time regime classification (Momentum, Mean Reversion, Neutral, Transition)
- Multi-timeframe regime analysis with coherence scoring
- Visual indicators for trend strength and volatility
- Confidence metrics for each timeframe
- Color-coded regime states

### 2. Percentile-Based Entry Logic
**Component:** `PercentileChart.tsx`

- Historical percentile tracking across timeframes
- Entry and watch zone visualization
- Real-time percentile calculations
- Dual-axis chart (percentile vs price)
- Dynamic threshold indicators

### 3. Risk-Adjusted Expectancy
**Component:** `ExpectancyDashboard.tsx`

- Expectancy breakdown (Base, Volatility Adj, Regime Adj)
- Win/Loss ratio visualization
- Risk metrics (Win Rate, Avg Win/Loss, Sharpe Ratio)
- Confidence scoring
- Interactive bar charts

### 4. Composite Instrument Scoring
**Component:** `InstrumentRanking.tsx`

- Real-time instrument rankings
- Multi-factor scoring breakdown
- Expandable row details
- Category-based factor visualization
- Top/Bottom performer highlights

### 5. Position & Risk Management
**Component:** `PositionMonitor.tsx`

- Active position tracking
- Unrealized P&L monitoring
- Adaptive stop-loss visualization
- Risk exposure metrics
- Position-level performance

### 6. Main Dashboard
**Component:** `TradingFrameworkDashboard.tsx`

- Unified view of all components
- Auto-refresh every 5 seconds
- System-wide metrics
- Real-time notifications
- Responsive grid layout

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Material-UI (MUI)** - Component library
- **Recharts** - Data visualization
- **Vite** - Build tool

## Installation

```bash
cd frontend
npm install
```

## Running the Dashboard

### Development Mode
```bash
npm run dev
```
Opens at `http://localhost:3000`

### Production Build
```bash
npm run build
npm run preview
```

## Component Structure

```
src/components/TradingFramework/
├── RegimeIndicator.tsx          # Market regime detection UI
├── PercentileChart.tsx          # Percentile entry logic visualization
├── ExpectancyDashboard.tsx      # Risk-adjusted expectancy metrics
├── InstrumentRanking.tsx        # Composite score rankings
├── PositionMonitor.tsx          # Active position tracking
└── TradingFrameworkDashboard.tsx # Main dashboard container
```

## Data Flow

### Sample Data Generation
Currently uses `generateSampleData()` function for demonstration:
- Generates realistic multi-timeframe regime data
- Creates percentile entries across instruments
- Simulates risk metrics and expectancy
- Produces composite scores and rankings
- Generates active positions

### Integration with Backend
To connect to your trading framework backend:

1. **Create API Service** (`src/services/frameworkApi.ts`):
```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
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
```

2. **Update Dashboard Component**:
```typescript
import { useEffect } from 'react';
import { getFrameworkState } from '../services/frameworkApi';

const TradingFrameworkDashboard = () => {
  useEffect(() => {
    const fetchData = async () => {
      const state = await getFrameworkState();
      setData(state);
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  // ... rest of component
};
```

## Configuration

### Theme Customization
Edit `App-TradingFramework.tsx` to customize the dark theme:

```typescript
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#3B82F6' },
    // ... customize colors
  },
});
```

### Update Frequency
Adjust auto-refresh interval in `TradingFrameworkDashboard.tsx`:

```typescript
useEffect(() => {
  const interval = setInterval(() => {
    refreshData();
  }, 5000); // Change this value (milliseconds)

  return () => clearInterval(interval);
}, []);
```

## Key Metrics Displayed

### Regime Detection
- Dominant regime type
- Coherence score (0-100%)
- Per-timeframe confidence
- Trend strength and volatility ratios

### Percentile Logic
- Current percentile level
- Entry threshold (default 95%)
- Watch zone (85-95%)
- Neutral zone (<85%)

### Risk-Adjusted Expectancy
- Base expectancy
- Volatility adjustment
- Regime adjustment
- Final expectancy with confidence

### Composite Scoring
- Total composite score (0-100)
- Individual factor contributions
- Instrument rankings
- Percentile placement

### Position Management
- Total capital deployed
- Unrealized P&L ($ and %)
- Total risk exposure
- Per-position stop-loss tracking

## Responsive Design

The dashboard is fully responsive:
- **Desktop (>1200px)**: Full 4-column grid layout
- **Tablet (768-1200px)**: 2-column adaptive layout
- **Mobile (<768px)**: Single column stacked view

## Color Coding

### Regime Types
- 🟢 **Momentum**: Green (success)
- 🟡 **Mean Reversion**: Yellow (warning)
- 🔵 **Transition**: Blue (info)
- ⚪ **Neutral**: Grey (default)

### Performance Indicators
- 🟢 **Positive P&L**: Green
- 🔴 **Negative P&L**: Red
- 🟡 **Warning**: Yellow
- 🔵 **Information**: Blue

## Development Tips

### Hot Reload
Vite provides instant hot module replacement (HMR). Changes to components update immediately without full page reload.

### TypeScript Strict Mode
All components use strict TypeScript. Ensure proper typing for:
- Component props
- State variables
- API responses
- Event handlers

### Adding New Components
1. Create component in `src/components/TradingFramework/`
2. Export from component file
3. Import in `TradingFrameworkDashboard.tsx`
4. Add to grid layout

### Debugging
- Use React DevTools browser extension
- Check console for errors
- Inspect network tab for API calls
- Use browser's responsive mode for mobile testing

## Future Enhancements

### Planned Features
1. **WebSocket Integration**: Real-time streaming updates
2. **Historical Playback**: Replay past trading sessions
3. **Alerts & Notifications**: Custom threshold alerts
4. **Export Functionality**: Download reports as PDF/CSV
5. **Custom Layouts**: User-configurable dashboard layouts
6. **Dark/Light Theme Toggle**: User preference
7. **Multi-Account Support**: Switch between accounts
8. **Advanced Filtering**: Filter by timeframe, regime, score

### Backend Integration
Connect to the TypeScript trading framework:

```typescript
// Example API endpoints to implement:
GET  /api/framework/state          // Full framework state
GET  /api/framework/regime         // Current regime data
GET  /api/framework/positions      // Active positions
GET  /api/framework/scores         // Instrument scores
POST /api/framework/entry          // Create entry signal
POST /api/framework/exit           // Exit position
PUT  /api/framework/config         // Update configuration
```

## Performance Optimization

### Current Optimizations
- React.memo for expensive components
- useCallback for event handlers
- Debounced refresh intervals
- Lazy loading for charts

### Recommendations
- Implement virtualization for large instrument lists
- Use Web Workers for heavy calculations
- Cache API responses with React Query
- Implement progressive loading

## Testing

### Unit Tests (Recommended)
```bash
npm install -D @testing-library/react @testing-library/jest-dom vitest
```

### Integration Tests
Test component interactions and data flow

### E2E Tests
Use Playwright or Cypress for full workflow testing

## Documentation

### Component Documentation
Each component includes:
- TypeScript interface definitions
- Props documentation
- Usage examples in comments

### API Documentation
Document all API endpoints in `docs/API.md`

## Support

For issues or questions:
1. Check the component source code
2. Review TypeScript interfaces
3. Inspect browser console
4. Check network requests
5. Review MUI documentation

## License

Part of the multi-timeframe trading framework project.

---

**Last Updated**: November 6, 2025
**Version**: 1.0.0
**Framework**: React 18 + TypeScript + Material-UI
