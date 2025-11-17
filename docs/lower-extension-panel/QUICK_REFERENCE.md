# Lower Extension Distance Panel - Quick Reference Card

## 🚀 One-Minute Setup

```bash
# Install
cd /workspaces/New-test-strategy
./docs/lower-extension-panel/INSTALL.sh

# Or manually
cd frontend && npm install
```

## 📦 Import & Use

```typescript
import { LowerExtensionPanel } from './components/LowerExtensionPanel';

<LowerExtensionPanel
  indicatorData={[{ symbol: "SPX", price: 6999, lower_ext: 6900, historical_prices: [...] }]}
  candleData={{ "SPX": [{ time: "2025-10-08", open: 6945, high: 6960, low: 6940, close: 6950 }] }}
/>
```

## 🎯 Core Formulas

```typescript
// Distance
pct_dist = (price - lower_ext) / lower_ext × 100

// Below flag
is_below = pct_dist < 0

// Proximity score
score = clamp(1 - (median_abs_dist / threshold), 0, 1)
```

## 📊 JSON Export Schema

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

## ⚙️ Default Settings

```typescript
{
  lookback_days: 30,
  recent_N: 5,
  proximity_threshold: 5.0,
  price_source: 'close'
}
```

## 📁 File Locations

```
frontend/src/
├── components/LowerExtensionPanel/
│   ├── LowerExtensionPanel.tsx     # Main container
│   ├── LowerExtensionChart.tsx     # Chart + blue line
│   ├── SymbolCard.tsx              # Metrics display
│   ├── SettingsPanel.tsx           # Config panel
│   └── Sparkline.tsx               # 30-day mini chart
└── utils/
    └── lowerExtensionCalculations.ts  # Core engine
```

## 🧪 Testing

```bash
# Run all tests
npm test

# Run specific test
npm test -- lowerExtensionCalculations.test.ts

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage
```

## 🔌 Required Data Format

```typescript
interface IndicatorData {
  symbol: string;           // Required
  price: number;            // Required
  lower_ext: number;        // Required (blue line from MBAD)
  historical_prices?: {     // Optional (for 30-day metrics)
    timestamp: string;
    price: number;
  }[];
}
```

## 🎨 Component Props

```typescript
<LowerExtensionPanel
  indicatorData={[...]}              // Required: indicator data array
  candleData={{...}}                 // Required: OHLC candle data
  onFetchHistoricalPrices={...}      // Optional: async fetch function
/>
```

## 📊 Key Metrics Explained

| Metric | Range | Interpretation |
|--------|-------|----------------|
| `pct_dist_lower_ext` | -∞ to +∞ | Signed distance (- = below, + = above) |
| `is_below_lower_ext` | true/false | Price breached lower_ext |
| `min_pct_dist_30d` | -∞ to 0 | Deepest breach in 30 days |
| `breach_rate_30d` | 0 to 1 | Fraction of days breached |
| `proximity_score_30d` | 0 to 1 | 1 = closest, 0 = farthest |

## 🎯 Trading Signals

### Entry Signal
```
is_below_lower_ext = true
recent_breached = false
proximity_score > 0.7
→ Strong mean reversion opportunity
```

### Exit Signal
```
pct_dist_lower_ext > 3%
→ Take profits
```

### Risk Warning
```
breach_rate_30d > 0.3
min_pct_dist_30d < -5%
→ Unstable support, higher risk
```

## 🚨 Common Issues

| Issue | Solution |
|-------|----------|
| "N/A" metrics | Provide `historical_prices` or implement fetch callback |
| `lower_ext = 0` | Map `ext_lower` from MBAD (not dev_lower/lim_lower) |
| Chart not showing | Verify `candleData` has `time`, `open`, `high`, `low`, `close` |
| Slow performance | Increase refresh interval to 60s for 10+ symbols |

## 📚 Documentation Index

- **README.md** - Features overview & quick start
- **INTEGRATION_GUIDE.md** - Step-by-step integration
- **EXAMPLE_USAGE.md** - Working code examples
- **SUMMARY.md** - Complete implementation summary
- **QUICK_REFERENCE.md** - This card

## 🔧 Scripts

```bash
npm run dev              # Development server
npm run build            # Production build
npm run test             # Run tests
npm run test:watch       # Watch mode
npm run test:coverage    # Coverage report
npm run lint             # Lint code
```

## 💡 Pro Tips

1. **Use proximity_score_30d for ranking** - Higher score = lower risk entry
2. **Monitor breach_rate_30d** - < 0.2 = stable support
3. **Check min_pct_dist_30d** - Recent deep breach = caution
4. **Export JSON for composite scoring** - Combine with other indicators
5. **Set auto-refresh to 30-60s** - Balance freshness vs performance

## 🎨 Customization Points

```typescript
// Custom color scheme
const customColors = {
  belowColor: '#22c55e',  // Green for below (breach)
  aboveColor: '#6b7280',  // Gray for above
  lineColor: '#2962ff',   // Blue lower_ext line
};

// Custom thresholds for your strategy
const customSettings = {
  lookback_days: 45,        // Longer lookback
  proximity_threshold: 3.0, // Tighter scoring
  recent_N: 3,              // More recent focus
};
```

## 📞 Getting Help

1. Check **INTEGRATION_GUIDE.md** for detailed steps
2. Review **EXAMPLE_USAGE.md** for working examples
3. Run tests to verify calculations
4. Check console for error messages
5. Verify indicator data format matches specification

---

**Version**: 1.0.0
**Status**: ✅ Production Ready
**Last Updated**: November 2025
