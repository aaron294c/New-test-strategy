# Gamma Wall Scanner v2.0 - TradingView Design

## 🎨 Design Philosophy

The v2.0 redesign implements a **professional, minimalist, dark-theme aesthetic** that emulates TradingView's chart interface, maximizing data clarity and reducing visual noise.

## Key Design Changes

### 1. Color Palette (TradingView Dark Theme)

```typescript
const TRADINGVIEW_COLORS = {
  background: '#131722',      // Deep dark background
  paper: '#1E222D',          // Elevated surfaces
  gridline: '#2A2E39',       // Subtle grid lines
  text: '#787B86',           // Secondary text
  textBright: '#D1D4DC',     // Primary text
  gammaWall: '#2962FF',      // Single blue for walls
  gammaFlip: '#FFA726',      // Bright orange pivot
  currentPrice: '#FFFFFF',    // Pure white price line
  sdBand: 'rgba(120, 123, 134, 0.1)', // Faint gray bands
};
```

**Rationale:**
- Single color scheme eliminates visual confusion
- Opacity represents strength instead of multiple colors
- High-contrast key levels (flip/price) stand out immediately

### 2. Layout Architecture

```
┌─────────────────────────────────────────────────┐
│ Top Bar (Condensed Metrics)                    │
│ VIX | Regime | Updated | Status                │
├──────┬──────────────────────────────────────────┤
│      │                                          │
│ Side │  Main Chart Canvas                      │
│ bar  │  (Horizontal Gamma Bars)                │
│      │                                          │
│ (280)│  Integrated Symbol Metrics Table        │
│      │                                          │
└──────┴──────────────────────────────────────────┘
```

**Changes:**
- ✅ Unified canvas with no separate boxes
- ✅ Collapsible sidebar (280px → 40px)
- ✅ Top bar shows key metrics inline
- ✅ Table integrated below chart (not separate)

### 3. Horizontal Gamma Bars

**Old Design:**
- Vertical time-based chart
- Multiple colors per timeframe
- Cluttered legend

**New Design:**
- Horizontal bars showing strength
- Y-axis = Price levels
- X-axis = Wall strength (0-100)
- Single blue color with varying opacity

```
Price
 │
7400 ├────────────────────▓▓▓▓▓▓ (Call Wall, 80%)
7000 ├──────────▓▓▓▓▓ (Put Wall, 50%)
6800 ├─────────────────▓▓▓▓▓▓▓▓ (Put Wall, 85%)
 │
 └─────────────────────────────► Strength
     0                        100
```

### 4. Key Level Visualization

**Gamma Flip:**
- Horizontal dashed line
- Bright orange (#FFA726)
- Crosses entire chart
- Instantly recognizable as pivot

**Current Price:**
- Thick white line (#FFFFFF)
- Circle marker on right axis
- Like TradingView's real-time price tag

**SD Bands:**
- Faint dotted lines
- Gray color that doesn't compete
- Background-level visual priority

### 5. Typography

- **Font:** Roboto, Open Sans, Arial (sans-serif stack)
- **Sizes:**
  - Top bar metrics: 12px
  - Chart labels: 12px
  - Table headers: 12px (uppercase, 0.5px letter-spacing)
  - Table values: 13px
  - Key metrics (bold): 13px, weight 600

### 6. Symbol Metrics Table

**Design:**
- Alternating row backgrounds (#1E222D / #131722)
- Monospace numbers for alignment
- Bold key columns (Gamma Flip, Strongest Wall)
- No heavy borders, just subtle 1px dividers

```
┌────────────────────────────────────────────────┐
│ Symbol Metrics                                 │
├────────┬────────┬──────────┬────────┬─────────┤
│ Symbol │ Price  │ G. Flip  │ Dist % │ IV      │
├────────┼────────┼──────────┼────────┼─────────┤
│ SPX    │ 5724.09│ 5724.09  │ +2.1%  │ 25.0%   │ ← Even row
│ QQQ    │ 260.80 │ 260.80   │ -1.5%  │ 28.6%   │ ← Odd row
└────────┴────────┴──────────┴────────┴─────────┘
```

### 7. Control Panel (Sidebar)

**Clean Features:**
- Toggle switches instead of checkboxes
- Thin sliders with value display
- Radio buttons with custom styling
- Collapsible to 40px with arrow button

**Toggle Switch:**
```
Label Text               [○─────]  (off)
Label Text               [───────●] (on, blue)
```

### 8. Top Bar (Inline Metrics)

```
GAMMA WALL SCANNER | VIX 20.8 | Regime Normal | Updated 3:42pm | ● Live
```

- All metrics inline, separated by pipes (|)
- Small regime chip with transparent background
- Live status dot (green/red)
- No excessive spacing

## Component Breakdown

### GammaScannerTab.v2.tsx
- Main container
- Top bar layout
- Sidebar collapse logic
- State management

### GammaChartCanvas.v2.tsx
- Plotly horizontal bar chart
- Single-color gamma walls
- Key level overlays
- Integrated metrics table

### GammaControlPanel.tsx
- Toggle switches
- Slider controls
- Radio buttons
- Manual paste input

## Interaction Design

### Hover States
- **Gamma Bars:** Show tooltip with strike/strength/GEX/DTE
- **Price Line:** Show current price tooltip
- **Flip Line:** Show gamma flip value
- **Table Rows:** Subtle background highlight

### Responsive Behavior
- Sidebar collapses to 40px on narrow screens
- Chart resizes fluidly
- Table scrolls horizontally if needed

## Performance Optimizations

1. **Plotly Config:**
   - Remove unnecessary mode bar buttons
   - Add custom reset button
   - Disable logo
   - Enable responsive resize

2. **React Optimizations:**
   - useMemo for chart data
   - useCallback for handlers
   - Minimal re-renders

## Accessibility

- Sufficient color contrast (WCAG AA)
- Focus states on interactive elements
- Keyboard navigation support
- Screen reader labels

## Migration Path

**From v1 to v2:**
```typescript
// Old
import { GammaScannerTab } from './components/GammaScanner';

// New (automatic)
import { GammaScannerTab } from './components/GammaScanner';
// Now imports v2 by default

// Explicit v1 (legacy)
import { GammaScannerTabV1 } from './components/GammaScanner';
```

## Comparison

| Feature | v1 | v2 |
|---------|----|----|
| Color Scheme | Multi-color | Single blue + key highlights |
| Layout | Separate boxes | Unified canvas |
| Chart Type | Time-based vertical | Strength-based horizontal |
| Sidebar | Always visible | Collapsible |
| Table | Separate component | Integrated below chart |
| Top Bar | Large header | Condensed metrics |
| Typography | Mixed | Clean sans-serif |
| Visual Weight | Heavy | Minimal |

## Future Enhancements

- [ ] WebGL renderer for 100+ walls
- [ ] Real-time animation of price movement
- [ ] Historical wall tracking overlay
- [ ] Alert system integration
- [ ] Mobile-responsive breakpoints
- [ ] Dark/Light theme toggle

---

**Design Status:** ✅ Complete
**Production Ready:** Yes
**Browser Support:** Chrome, Firefox, Safari, Edge (latest 2 versions)
