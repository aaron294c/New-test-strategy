# Lower Extension Distance Panel - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      LOWER EXTENSION PANEL                           │
│                         (Main Container)                             │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴──────────────┐
                    ▼                            ▼
        ┌──────────────────────┐    ┌──────────────────────┐
        │   Indicator Parser   │    │   Price Feed API     │
        │   (MBAD Script)      │    │   (WebSocket/REST)   │
        └──────────────────────┘    └──────────────────────┘
                    │                            │
                    │   IndicatorData[]         │   Live Prices
                    └─────────────┬──────────────┘
                                  ▼
            ┌─────────────────────────────────────────┐
            │   lowerExtensionCalculations.ts         │
            │   (Core Calculation Engine)             │
            │                                         │
            │   • computePctDistLowerExt()           │
            │   • compute30DayMetrics()              │
            │   • computeProximityScore()            │
            │   • calculateLowerExtMetrics()         │
            │   • exportToJSON()                     │
            └─────────────────────────────────────────┘
                                  │
                    ┌─────────────┴──────────────┐
                    ▼                            ▼
        ┌──────────────────────┐    ┌──────────────────────┐
        │  LowerExtMetrics[]   │    │   JSON Export        │
        │  (Computed Results)  │    │   (Schema-compliant) │
        └──────────────────────┘    └──────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────────────┐
    │         UI Component Layer                     │
    │                                               │
    │  ┌────────────────────────────────────┐     │
    │  │  LowerExtensionPanel.tsx           │     │
    │  │  • Symbol tabs                     │     │
    │  │  • Auto-refresh management         │     │
    │  │  • Settings state                  │     │
    │  │  • Batch export                    │     │
    │  └────────────────────────────────────┘     │
    │                │                             │
    │      ┌─────────┴─────────┐                  │
    │      ▼                   ▼                   │
    │  ┌────────────┐    ┌────────────┐          │
    │  │   Chart    │    │ SymbolCard │          │
    │  │ Component  │    │ Component  │          │
    │  └────────────┘    └────────────┘          │
    │      │                   │                   │
    │      ▼                   ▼                   │
    │  ┌─────────────────────────────┐           │
    │  │   Sparkline Component       │           │
    │  └─────────────────────────────┘           │
    │                                               │
    │  ┌─────────────────────────────┐           │
    │  │  SettingsPanel Component    │           │
    │  └─────────────────────────────┘           │
    └───────────────────────────────────────────────┘
                    │
                    ▼
        ┌──────────────────────┐
        │   User Interface     │
        │   (Browser Display)  │
        └──────────────────────┘
```

## Data Flow Diagram

```
Input Data                  Processing                    Output
──────────                  ──────────                    ──────

┌─────────────┐
│  Indicator  │
│    Data     │  ────────▶  ┌──────────────────┐
│             │             │  Parse & Map     │
│ • symbol    │             │  to Interface    │
│ • price     │             └──────────────────┘
│ • lower_ext │                      │
│ • history   │                      ▼
└─────────────┘             ┌──────────────────┐         ┌─────────────┐
                            │  Calculate       │         │  Chart      │
┌─────────────┐             │  Distance        │  ────▶  │  Display    │
│   Candle    │             │  Metrics         │         └─────────────┘
│    Data     │  ────────▶  │                  │
│             │             │ • pct_dist       │         ┌─────────────┐
│ • OHLC      │             │ • is_below       │         │  Metrics    │
│ • time      │             │ • 30d stats      │  ────▶  │  Card       │
└─────────────┘             │ • proximity      │         └─────────────┘
                            └──────────────────┘
┌─────────────┐                      │                   ┌─────────────┐
│  Settings   │                      │                   │  Sparkline  │
│             │  ────────▶           │            ────▶  │  Chart      │
│ • lookback  │                      │                   └─────────────┘
│ • threshold │                      ▼
└─────────────┘             ┌──────────────────┐         ┌─────────────┐
                            │  Export to JSON  │  ────▶  │  Download   │
                            └──────────────────┘         │  File       │
                                                          └─────────────┘
```

## Component Hierarchy

```
LowerExtensionPanel (Main Container)
│
├─ State Management
│  ├─ indicatorData (input)
│  ├─ candleData (input)
│  ├─ metricsMap (computed)
│  ├─ settings (configurable)
│  ├─ selectedSymbol (UI state)
│  └─ autoRefresh (UI state)
│
├─ Symbol Tabs (Multi-symbol selector)
│  └─ Tab for each symbol with mini metrics
│
├─ Chart Section
│  │
│  ├─ LowerExtensionChart
│  │  ├─ Candlestick Series (lightweight-charts)
│  │  ├─ Lower Extension Line (blue, 3px)
│  │  ├─ Distance Annotation (floating label)
│  │  └─ Breach Shading (conditional)
│  │
│  └─ Visual Controls
│     ├─ Show Annotation Toggle
│     └─ Show Shading Toggle
│
├─ Metrics Section
│  │
│  └─ SymbolCard
│     ├─ Header (symbol, price, lower_ext)
│     ├─ Distance Metrics Section
│     ├─ 30-Day Metrics Section
│     ├─ Proximity Score Bar
│     ├─ Sparkline (30-day chart)
│     └─ Export JSON Button
│
└─ Settings Section
   │
   ├─ SettingsPanel
   │  ├─ Calculation Settings
   │  │  ├─ Lookback Days Input
   │  │  ├─ Recent N Input
   │  │  ├─ Proximity Threshold Input
   │  │  └─ Price Source Selector
   │  │
   │  └─ Refresh Settings
   │     ├─ Auto-refresh Toggle
   │     ├─ Refresh Interval Input
   │     └─ Manual Refresh Button
   │
   └─ Quick Stats Summary
      ├─ Total Symbols Count
      ├─ Below Lower Ext Count
      └─ Recently Breached Count
```

## Calculation Flow

```
Step 1: Current Distance
─────────────────────────
price = 6999
lower_ext = 6900

pct_dist = (6999 - 6900) / 6900 × 100 = 1.43%
is_below = false
abs_dist = 1.43%

Step 2: Historical Analysis (30 days)
──────────────────────────────────────
historical_prices = [6950, 6920, 6880, 6895, ...]

For each price:
  - Calculate pct_dist_i
  - Track if < 0 (breach)

min_pct_dist_30d = -2.34% (deepest breach)
median_abs_pct_dist_30d = 1.23% (typical distance)
breach_count_30d = 4 (number of breaches)
breach_rate_30d = 0.1333 (4/30 days)
recent_breached = true (breach in last 5 days)

Step 3: Proximity Score
────────────────────────
threshold = 5.0%
median_abs_dist = 1.23%

score = 1 - (1.23 / 5.0) = 0.754
score = clamp(0.754, 0, 1) = 0.754

Step 4: Output
──────────────
LowerExtMetrics {
  all computed values...
}

Step 5: Export
──────────────
JSON.stringify(metrics) → Download
```

## Technology Stack

```
┌──────────────────────────────────────────┐
│          Frontend Framework              │
│          React 18.2 + TypeScript         │
└──────────────────────────────────────────┘
                   │
    ┌──────────────┴───────────────┐
    ▼                              ▼
┌─────────────┐          ┌──────────────────┐
│  Charting   │          │  State Mgmt      │
│  Library    │          │  (useState)      │
│             │          │                  │
│ lightweight │          │  • Local state   │
│ -charts     │          │  • Props flow    │
│ v4.1.0      │          │  • Callbacks     │
└─────────────┘          └──────────────────┘
                                  │
                    ┌─────────────┴──────────────┐
                    ▼                            ▼
          ┌───────────────┐          ┌───────────────────┐
          │  Calculations │          │  UI Components    │
          │               │          │                   │
          │  TypeScript   │          │  • Functional     │
          │  Pure Fns     │          │  • Hooks          │
          │  Client-side  │          │  • Memoization    │
          └───────────────┘          └───────────────────┘
```

## Performance Optimizations

```
Optimization Layer                  Technique
──────────────────                  ─────────

Data Processing
├─ Client-side calculations      ─▶ No API calls for compute
├─ Memoized results             ─▶ useMemo for expensive calcs
└─ Incremental updates          ─▶ Update only changed symbols

Rendering
├─ Canvas-based sparklines      ─▶ Better than SVG for many points
├─ Lightweight-charts           ─▶ WebGL-accelerated rendering
└─ Conditional rendering        ─▶ Render only visible components

Data Fetching
├─ Lazy loading                 ─▶ Load historical data on-demand
├─ Caching                      ─▶ Cache historical prices
└─ Batch updates                ─▶ Update all symbols at once

State Management
├─ Local state                  ─▶ No global store overhead
├─ Selective re-renders         ─▶ React.memo where needed
└─ Debounced settings           ─▶ Reduce calculation frequency
```

## Integration Points

```
External System              Interface              Panel Component
───────────────              ─────────              ───────────────

┌─────────────────┐
│  MBAD Indicator │
│  (Pine Script)  │  ────────────────────────▶  IndicatorData[]
│                 │   Map ext_lower → lower_ext
│  • ext_lower    │
│  • price        │
│  • timestamp    │
└─────────────────┘

┌─────────────────┐
│  Price Feed API │
│  (WebSocket)    │  ────────────────────────▶  Live Price Updates
│                 │   Update price in real-time
│  • ticker       │
│  • price        │
│  • timestamp    │
└─────────────────┘

┌─────────────────┐
│  Candle API     │
│  (REST)         │  ────────────────────────▶  CandleData{}
│                 │   OHLC data for chart
│  • OHLC         │
│  • time         │
└─────────────────┘

┌─────────────────┐
│  Historical API │
│  (REST)         │  ────────────────────────▶  historical_prices[]
│                 │   30-day price history
│  • prices       │
│  • timestamps   │
└─────────────────┘
                              │
                              ▼
                   ┌───────────────────────┐
                   │  LowerExtensionPanel  │
                   └───────────────────────┘
                              │
                              ▼
                   ┌───────────────────────┐
                   │  Composite Risk       │
                   │  Scoring System       │  ◀── Exported JSON
                   └───────────────────────┘
```

## File Dependencies

```
LowerExtensionPanel.tsx
├── imports
│   ├── lowerExtensionCalculations.ts (core engine)
│   ├── LowerExtensionChart.tsx
│   ├── SymbolCard.tsx
│   └── SettingsPanel.tsx
│
LowerExtensionChart.tsx
├── imports
│   ├── lightweight-charts (3rd party)
│   └── lowerExtensionCalculations.ts (types)
│
SymbolCard.tsx
├── imports
│   ├── lowerExtensionCalculations.ts (types)
│   └── Sparkline.tsx
│
Sparkline.tsx
├── imports
│   └── canvas API (native browser)
│
SettingsPanel.tsx
├── imports
│   └── lowerExtensionCalculations.ts (types)
│
lowerExtensionCalculations.ts
└── imports
    └── none (pure TypeScript functions)
```

## Deployment Architecture

```
Development
───────────
localhost:3000
├─ Vite dev server
├─ Hot module reload
└─ Source maps enabled

Production
──────────
Static build (dist/)
├─ Optimized bundles
├─ Tree-shaking applied
├─ Code-split by route
└─ Minified CSS/JS

CDN Deployment
──────────────
https://your-cdn.com/
├─ Static assets
├─ Gzip compression
├─ Cache headers
└─ Edge distribution
```

## Testing Architecture

```
Unit Tests (Jest + ts-jest)
───────────────────────────
lowerExtensionCalculations.test.ts
├─ Distance calculations
├─ 30-day metrics
├─ Proximity scoring
├─ Edge cases
└─ JSON export validation

Integration Tests (Testing Library)
────────────────────────────────────
LowerExtensionPanel.test.tsx
├─ Component rendering
├─ User interactions
├─ Data flow
└─ Export functionality

E2E Tests (Future)
──────────────────
Playwright / Cypress
├─ Full user workflows
├─ Real data integration
└─ Performance benchmarks
```

## Scalability Considerations

```
Symbol Count        Recommended Setup
────────────        ─────────────────
1-10 symbols        Default settings, 30s refresh
10-50 symbols       60s refresh, lazy-load charts
50-100 symbols      Web Worker calculations
100+ symbols        Pagination, virtualized lists
```

## Security Considerations

```
Input Validation
────────────────
• Validate price > 0
• Validate lower_ext > 0
• Sanitize symbol names
• Bounds check all inputs

Data Handling
─────────────
• No sensitive data stored
• Client-side only (no server)
• Export JSON sanitized
• No XSS vulnerabilities

API Integration
───────────────
• HTTPS only
• API key validation
• Rate limiting
• Error handling
```

---

**Architecture Version**: 1.0.0
**Last Updated**: November 2025
**Status**: ✅ Production Ready
