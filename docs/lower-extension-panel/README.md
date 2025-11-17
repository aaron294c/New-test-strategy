# Lower Extension Distance Panel

> **Compact frontend feature for computing signed percent distance to the blue lower extension line with 30-day lookback metrics for mean reversion trading.**

## 🎯 Quick Start

```typescript
import { LowerExtensionPanel } from './components/LowerExtensionPanel';

<LowerExtensionPanel
  indicatorData={[
    {
      symbol: "SPX",
      price: 6999.00,
      lower_ext: 6900.00,
      last_update: "nov 07, 03:42pm",
      historical_prices: [...]
    }
  ]}
  candleData={{
    "SPX": [
      { time: "2025-10-08", open: 6945, high: 6960, low: 6940, close: 6950 }
    ]
  }}
/>
```

## 📊 Key Metrics Computed

| Metric | Formula | Purpose |
|--------|---------|---------|
| **pct_dist_lower_ext** | `(price - lower_ext) / lower_ext * 100` | Signed distance (+above, -below) |
| **is_below_lower_ext** | `pct_dist < 0` | Quick breach flag |
| **abs_pct_dist_lower_ext** | `abs(pct_dist)` | Absolute distance for ranking |
| **min_pct_dist_30d** | `min(historical distances)` | Deepest breach in period |
| **median_abs_pct_dist_30d** | `median(abs distances)` | Typical distance magnitude |
| **breach_count_30d** | `count(distance < 0)` | Number of breach days |
| **breach_rate_30d** | `breach_count / total_days` | Breach frequency |
| **recent_breached** | `any breach in last N days` | Recent weakness flag |
| **proximity_score_30d** | `clamp(1 - median/threshold, 0, 1)` | Normalized risk score (0-1) |

## 🚀 Features

- ✅ **Real-time calculations** - Client-side, instant updates
- ✅ **Interactive charts** - Candles + lower extension overlay with annotations
- ✅ **30-day analytics** - Breach history, proximity metrics, risk scoring
- ✅ **Sparkline visualization** - Mini chart showing 30-day price vs lower_ext
- ✅ **JSON export** - Exact schema for downstream composite scoring
- ✅ **Configurable settings** - Thresholds, lookback periods, price source
- ✅ **Auto-refresh** - Live price updates with configurable intervals
- ✅ **Multi-symbol support** - Track multiple instruments simultaneously

## 📁 Project Structure

```
frontend/src/
├── components/LowerExtensionPanel/
│   ├── LowerExtensionPanel.tsx    # Main panel (tab/page container)
│   ├── LowerExtensionChart.tsx    # Chart with candles + lower_ext line
│   ├── SymbolCard.tsx             # Metrics summary card
│   ├── SettingsPanel.tsx          # Configuration controls
│   ├── Sparkline.tsx              # 30-day mini chart
│   └── index.ts                   # Exports
└── utils/
    └── lowerExtensionCalculations.ts  # Core calculation engine

docs/lower-extension-panel/
├── README.md                      # This file
├── INTEGRATION_GUIDE.md           # Detailed integration steps
└── EXAMPLE_USAGE.md               # Working examples & strategies
```

## 🔧 Installation

```bash
# Install required dependencies
npm install lightweight-charts
```

## 📝 Minimal Example

```typescript
const indicatorData = [
  {
    symbol: "SPX",
    price: 6999,
    lower_ext: 6900,
    historical_prices: [
      { timestamp: "2025-10-08", price: 6950 },
      { timestamp: "2025-10-09", price: 6920 },
      // ... 30 days
    ]
  }
];

const candleData = {
  "SPX": [
    { time: "2025-10-08", open: 6945, high: 6960, low: 6940, close: 6950 }
  ]
};

function App() {
  return <LowerExtensionPanel indicatorData={indicatorData} candleData={candleData} />;
}
```

## 📤 JSON Export Format

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

## ⚙️ Configuration

### Calculation Settings

```typescript
{
  lookback_days: 30,           // Historical window
  recent_N: 5,                 // Recent breach check period
  proximity_threshold: 5.0,    // % threshold for scoring
  price_source: 'close'        // 'close' | 'wick' | 'high' | 'low'
}
```

### Mean Reversion Settings (from MBAD Indicator)

```pinescript
// Asymmetry Thresholds
Inner Asymmetry High: 1.2
Inner Asymmetry Low: 0.8
Outer Asymmetry High: 1.2
Outer Asymmetry Low: 0.8
Outer/Inner Ratio High: 1.2
Outer/Inner Ratio Low: 0.8

// Change Detection
15-Candle Lookback: 15
5-Candle Lookback: 5
Change Positive Threshold: 5%
Change Negative Threshold: -5%
```

## 🎨 Visual Features

### Chart
- ✅ Candlestick price data
- ✅ Bold blue lower extension line
- ✅ Distance annotation (floating label)
- ✅ Breach zone shading (optional)
- ✅ Interactive crosshair and tooltips

### Symbol Card
- ✅ Current price & lower_ext value
- ✅ Distance status badge (above/below)
- ✅ All 30-day metrics in organized sections
- ✅ Proximity score progress bar
- ✅ Sparkline chart with breach indicators

### Settings Panel
- ✅ Lookback period adjustment
- ✅ Threshold configuration
- ✅ Price source selection
- ✅ Auto-refresh toggle with interval
- ✅ Manual refresh button

## 🧪 Testing

```bash
# Run unit tests
npm test -- lowerExtensionCalculations.test.ts

# Watch mode
npm test -- --watch

# Coverage report
npm test -- --coverage
```

### Test Coverage

- ✅ Distance calculations (positive, negative, zero)
- ✅ 30-day metrics (min, median, breach count/rate)
- ✅ Proximity score normalization
- ✅ Recent breach detection
- ✅ JSON export schema validation
- ✅ Edge cases (missing data, extreme values)

## 📋 Acceptance Checklist

- [x] Chart displays candles and blue lower_ext line clearly
- [x] Annotation correctly shows pct_dist_lower_ext for current candle
- [x] is_below_lower_ext flag is true when price < lower_ext
- [x] 30-day metrics (min, median, breach_count, breach_rate) calculate correctly
- [x] proximity_score_30d responds to threshold adjustments
- [x] Export JSON available and matches schema exactly
- [x] Feature is in new tab/panel and non-destructive to existing UI
- [x] Settings persist and affect calculations in real-time
- [x] Auto-refresh works at configured interval
- [x] Manual refresh updates all symbols

## 🎯 Trading Strategy Use Cases

### Mean Reversion Entry Signals
- Price breaches lower_ext (`is_below_lower_ext = true`)
- No recent breaches (`recent_breached = false`) = stable support
- High proximity score (`> 0.7`) = historically close to line

### Risk Assessment
- High breach rate (`> 0.3`) = unstable, higher risk
- Deep min distance (`< -5%`) = volatile, use caution
- Low proximity score (`< 0.3`) = far from mean, wait

### Position Management
- Exit when `pct_dist_lower_ext > 3%` (take profits)
- Scale in as `abs_pct_dist_lower_ext` decreases
- Monitor `breach_count_30d` for support strength

## 🔗 Integration Points

1. **Indicator Parser** → Provides `IndicatorData` with `lower_ext` from MBAD script
2. **Price Feed** → Updates `price` in real-time via WebSocket or API
3. **Historical Data** → Supplies 30-day `historical_prices` array
4. **Candle Data** → Provides OHLC data for chart visualization
5. **Composite Scoring** → Consumes exported JSON for risk models

## 📚 Documentation

- **[INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)** - Complete integration steps with API examples
- **[EXAMPLE_USAGE.md](./EXAMPLE_USAGE.md)** - Working code examples and trading strategies

## 🚨 Important Notes

### Required Fields
- `symbol` (string) - REQUIRED
- `price` (number) - REQUIRED
- `lower_ext` (number) - REQUIRED (blue lower extension from MBAD)

### Optional Fields
- `timestamp` or `last_update` (string) - Display only
- `historical_prices` (array) - For 30-day metrics (fetch via callback if missing)

### Indicator Mapping
From your MBAD Pine Script indicator:
```pinescript
ext_lower  // Maps to lower_ext (BLUE LINE)
dev_lower  // DO NOT USE (grey line, not the target)
lim_lower  // DO NOT USE (red line, extreme level)
```

### Performance
- All calculations are client-side (instant)
- Use Web Worker for 50+ symbols
- Auto-refresh interval: 30-60s recommended
- Historical data: fetch once, update incrementally

## 🛠️ Troubleshooting

### "N/A" in 30-day metrics
→ Provide `historical_prices` in `IndicatorData` or implement `onFetchHistoricalPrices` callback

### lower_ext value is 0 or undefined
→ Check indicator parser is mapping `ext_lower` correctly from MBAD script

### Stale data warning
→ Historical prices missing or < 30 days - fetch more data

### Chart not rendering
→ Verify `candleData` has valid OHLC arrays with `time` field

### Slow performance with many symbols
→ Enable auto-refresh with longer intervals (60s+) and lazy-load charts

## 💡 Next Steps

1. **Integrate with your indicator parser** - Map MBAD output to `IndicatorData` format
2. **Configure thresholds** - Adjust settings for your mean reversion strategy
3. **Setup auto-refresh** - Connect to WebSocket or polling API for live updates
4. **Export JSON** - Feed metrics into your composite risk scoring system
5. **Customize styling** - Match colors and fonts to your app theme

## 📊 Example Output

```
Symbol: SPX
Price: $6,999.00
Lower Extension: $6,900.00
Status: ↑ Above (+1.45%)

30-Day Metrics:
├─ Min Distance: -2.34% (deepest breach)
├─ Median Abs Distance: 1.23%
├─ Breach Count: 4 days
├─ Breach Rate: 13.33%
├─ Recently Breached: Yes
└─ Proximity Score: 0.754 ████████████░░░░

Interpretation:
Price is currently 1.45% above the lower extension.
Recent breach detected, but price recovering.
Proximity score 0.754 suggests moderate mean reversion opportunity.
```

---

**Built for systematic mean reversion traders. Deploy, configure, and trade with confidence.**
