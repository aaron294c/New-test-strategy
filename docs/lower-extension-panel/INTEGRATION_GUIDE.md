# Lower Extension Distance Panel - Integration Guide

## Overview

The Lower Extension Distance Panel is a comprehensive frontend feature that computes and visualizes the signed percent distance to the blue lower extension line with 30-day lookback metrics for mean reversion trading strategies.

## Features

- ✅ Signed percent distance calculation (positive = above, negative = below)
- ✅ Boolean below/above flag for quick identification
- ✅ 30-day lookback metrics (min distance, median distance, breach count/rate)
- ✅ Proximity score (0-1 normalized, higher = less risky)
- ✅ Interactive chart with candles and lower extension overlay
- ✅ Sparkline visualization showing 30-day price history with breaches
- ✅ JSON export with exact schema for downstream composite scoring
- ✅ Configurable settings (lookback period, thresholds, price source)
- ✅ Auto-refresh and manual refresh capabilities

## Installation

### Dependencies

Install the required charting library:

```bash
npm install lightweight-charts
# or
yarn add lightweight-charts
```

### File Structure

```
frontend/src/
├── components/
│   └── LowerExtensionPanel/
│       ├── LowerExtensionPanel.tsx    # Main panel component
│       ├── LowerExtensionChart.tsx    # Chart visualization
│       ├── SymbolCard.tsx             # Metrics card display
│       ├── SettingsPanel.tsx          # Configuration panel
│       ├── Sparkline.tsx              # 30-day sparkline chart
│       └── index.ts                   # Exports
└── utils/
    └── lowerExtensionCalculations.ts  # Core calculation functions
```

## Data Requirements

### Indicator Data Format

Your indicator parser must provide data in this format:

```typescript
interface IndicatorData {
  symbol: string;                    // Required: e.g., "SPX"
  price: number;                     // Required: current price
  lower_ext: number;                 // Required: blue lower extension value
  timestamp?: string;                // Optional: ISO timestamp
  last_update?: string;              // Optional: formatted timestamp
  historical_prices?: Array<{        // Optional: 30-day history
    timestamp: string | number;
    price: number;
  }>;
}
```

### Candle Data Format

```typescript
interface CandleData {
  time: string | number;  // ISO string or Unix timestamp
  open: number;
  high: number;
  low: number;
  close: number;
}
```

## Basic Integration

### 1. Import the Component

```typescript
import { LowerExtensionPanel } from './components/LowerExtensionPanel';
```

### 2. Prepare Your Data

```typescript
// Example: Parse your indicator output
const indicatorData = [
  {
    symbol: "SPX",
    price: 6999.00,
    lower_ext: 6900.00,
    last_update: "nov 07, 03:42pm",
    historical_prices: [
      { timestamp: "2025-10-08", price: 6950.00 },
      { timestamp: "2025-10-09", price: 6920.00 },
      // ... 30 days of data
    ]
  },
  // ... more symbols
];

// Candle data for each symbol
const candleData = {
  "SPX": [
    { time: "2025-10-08", open: 6945, high: 6960, low: 6940, close: 6950 },
    { time: "2025-10-09", open: 6950, high: 6970, low: 6915, close: 6920 },
    // ... more candles
  ]
};
```

### 3. Render the Panel

```typescript
function App() {
  return (
    <LowerExtensionPanel
      indicatorData={indicatorData}
      candleData={candleData}
      onFetchHistoricalPrices={async (symbol, days) => {
        // Optional: Fetch historical prices if not provided
        const response = await fetch(`/api/prices/${symbol}?days=${days}`);
        return response.json();
      }}
    />
  );
}
```

## Advanced Integration

### With Existing App Router

```typescript
// Add new route in your App.tsx
import { LowerExtensionPanel } from './components/LowerExtensionPanel';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div>
      <nav>
        <button onClick={() => setActiveTab('dashboard')}>Dashboard</button>
        <button onClick={() => setActiveTab('lower-ext')}>Lower Extension Analysis</button>
      </nav>

      {activeTab === 'dashboard' && <Dashboard />}
      {activeTab === 'lower-ext' && (
        <LowerExtensionPanel
          indicatorData={indicatorData}
          candleData={candleData}
        />
      )}
    </div>
  );
}
```

### With Custom Data Fetcher

```typescript
// Create a custom hook for data fetching
function useLowerExtData() {
  const [data, setData] = useState<IndicatorData[]>([]);

  useEffect(() => {
    async function fetchData() {
      // Fetch from your indicator parser API
      const response = await fetch('/api/indicator/mbad');
      const result = await response.json();

      // Transform to required format
      const transformed = result.symbols.map(s => ({
        symbol: s.name,
        price: s.currentPrice,
        lower_ext: s.levels.ext_lower,  // Map to your indicator's field names
        historical_prices: s.history
      }));

      setData(transformed);
    }

    fetchData();
  }, []);

  return data;
}

// Use in component
function LowerExtensionPage() {
  const indicatorData = useLowerExtData();

  return <LowerExtensionPanel indicatorData={indicatorData} candleData={candleData} />;
}
```

## Calculation Details

### 1. Signed Percent Distance

```typescript
pct_dist_lower_ext = (price - lower_ext) / lower_ext * 100

// Examples:
// Price = 6999, lower_ext = 6900: +1.45% (above)
// Price = 6850, lower_ext = 6900: -0.72% (below/breached)
```

### 2. 30-Day Metrics

- **min_pct_dist_30d**: Most negative distance (deepest breach)
- **median_abs_pct_dist_30d**: Typical distance magnitude
- **breach_count_30d**: Number of days below lower_ext
- **breach_rate_30d**: Fraction of days breached (0-1)
- **recent_breached**: True if breached in last N days (default N=5)

### 3. Proximity Score

```typescript
proximity_score_30d = clamp(1 - (median_abs_pct_dist_30d / threshold), 0, 1)

// Default threshold: 5.0%
// Score 1.0 = price at or very close to lower_ext (high opportunity)
// Score 0.0 = price far from lower_ext (low opportunity)
```

## JSON Export Schema

The exported JSON follows this exact schema:

```json
{
  "symbol": "SPX",
  "price": 6999.00,
  "lower_ext": 6900.00,
  "pct_dist_lower_ext": 1.45,
  "is_below_lower_ext": false,
  "abs_pct_dist_lower_ext": 1.45,
  "min_pct_dist_30d": -2.34,
  "median_abs_pct_dist_30d": 1.23,
  "breach_count_30d": 4,
  "breach_rate_30d": 0.1333,
  "recent_breached": true,
  "proximity_score_30d": 0.754,
  "last_update": "nov 07, 03:42pm"
}
```

## Configuration Options

### Calculation Settings

```typescript
interface CalculationSettings {
  lookback_days: number;        // Default: 30
  recent_N: number;             // Default: 5
  proximity_threshold: number;  // Default: 5.0%
  price_source: 'close' | 'wick' | 'high' | 'low';  // Default: 'close'
}
```

### Visual Settings

- `showAnnotation`: Display distance annotation on chart
- `showShading`: Highlight breach zones with color gradient

## API Integration Examples

### Example 1: Real-time Price Updates

```typescript
function LiveLowerExtPanel() {
  const [indicatorData, setIndicatorData] = useState<IndicatorData[]>([]);

  useEffect(() => {
    const ws = new WebSocket('wss://your-api.com/prices');

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);

      setIndicatorData(prev => prev.map(item =>
        item.symbol === update.symbol
          ? { ...item, price: update.price, last_update: new Date().toISOString() }
          : item
      ));
    };

    return () => ws.close();
  }, []);

  return <LowerExtensionPanel indicatorData={indicatorData} candleData={candleData} />;
}
```

### Example 2: With TradingView Indicator Parser

```typescript
// Parse TradingView indicator output
async function parseTradingViewIndicator(scriptOutput: string): Promise<IndicatorData[]> {
  // Assuming your indicator exports JSON or structured text
  const parsed = JSON.parse(scriptOutput);

  return parsed.symbols.map(s => ({
    symbol: s.ticker,
    price: s.close,
    lower_ext: s.ext_lower,  // From MBAD indicator
    timestamp: s.timestamp,
    historical_prices: s.historical.map(h => ({
      timestamp: h.time,
      price: h.close
    }))
  }));
}

function TradingViewIntegration() {
  const [indicatorData, setIndicatorData] = useState<IndicatorData[]>([]);

  useEffect(() => {
    async function loadData() {
      const scriptOutput = await fetch('/api/tradingview/mbad').then(r => r.text());
      const data = await parseTradingViewIndicator(scriptOutput);
      setIndicatorData(data);
    }

    loadData();
  }, []);

  return <LowerExtensionPanel indicatorData={indicatorData} candleData={candleData} />;
}
```

## Troubleshooting

### Missing Historical Prices

If historical prices are not available:

1. The UI will show "N/A" for 30-day metrics
2. Export JSON will include `stale_data: true`
3. Provide `onFetchHistoricalPrices` callback to fetch on-demand

```typescript
<LowerExtensionPanel
  indicatorData={indicatorData}
  candleData={candleData}
  onFetchHistoricalPrices={async (symbol, days) => {
    const endDate = new Date();
    const startDate = new Date(endDate);
    startDate.setDate(startDate.getDate() - days);

    const response = await fetch(
      `/api/prices/${symbol}?start=${startDate.toISOString()}&end=${endDate.toISOString()}`
    );
    return response.json();
  }}
/>
```

### Lower Extension Value Missing

If `lower_ext` is undefined:
- Check your indicator parser is correctly mapping the blue lower extension line
- Ensure the MBAD indicator is using the correct calculation (ext_lower in your script)
- Verify the indicator is set to "Mean Reversion" mode

### Performance with Many Symbols

For 10+ symbols:
- Enable auto-refresh with longer intervals (30-60 seconds)
- Consider lazy-loading candle data per symbol
- Use Web Worker for calculations (already client-side optimized)

## Testing Checklist

- [ ] Chart displays candles and blue lower_ext line
- [ ] Annotation shows correct pct_dist_lower_ext
- [ ] is_below_lower_ext flag is accurate
- [ ] 30-day metrics calculate correctly
- [ ] proximity_score_30d responds to threshold changes
- [ ] Export JSON matches exact schema
- [ ] Settings persist and affect calculations
- [ ] Auto-refresh works at configured interval
- [ ] Manual refresh updates all data
- [ ] Multiple symbols display correctly

## Next Steps

1. **Integrate with your indicator parser**: Map your MBAD indicator output to `IndicatorData` format
2. **Add to your app routing**: Create new tab/route for the panel
3. **Configure thresholds**: Adjust settings for your trading strategy
4. **Export data**: Use JSON exports for downstream composite risk scoring
5. **Customize visuals**: Modify colors and styling to match your app theme

## Support

For issues or questions:
- Check the calculation functions in `lowerExtensionCalculations.ts`
- Review component props and interfaces
- Ensure all required fields are provided in indicator data
- Verify historical prices cover the lookback period
