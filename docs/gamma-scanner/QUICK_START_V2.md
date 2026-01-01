# Gamma Wall Scanner v2.0 - Quick Start Guide

## 🚀 What's New in v2.0

The completely redesigned Gamma Wall Scanner now features a **professional TradingView-inspired dark theme** with maximum data clarity and minimal visual noise.

## Key Visual Changes

### Before (v1) → After (v2)

#### 1. **Color Scheme**
- ❌ **v1:** Multiple colors (blue, orange, green, purple) per timeframe
- ✅ **v2:** Single soft blue (#2962FF) with opacity representing strength

#### 2. **Chart Type**
- ❌ **v1:** Time-based vertical chart with scattered data
- ✅ **v2:** Horizontal strength bars (Y-axis = Price, X-axis = Strength)

#### 3. **Layout**
- ❌ **v1:** Separate boxes with heavy borders
- ✅ **v2:** Unified dark canvas with integrated components

#### 4. **Key Levels**
- ❌ **v1:** Multiple colored lines, hard to distinguish
- ✅ **v2:**
  - **Current Price:** Pure white thick line
  - **Gamma Flip:** Bright orange dashed line
  - **SD Bands:** Faint gray dotted lines

#### 5. **Controls**
- ❌ **v1:** Chunky dropdowns and checkboxes
- ✅ **v2:** Clean toggle switches and thin sliders

#### 6. **Top Bar**
- ❌ **v1:** Large header with separate VIX/Regime boxes
- ✅ **v2:** Condensed inline metrics: `VIX 20.8 | Regime Normal | Updated 3:42pm`

## Visual Hierarchy

```
Priority 1 (Highest Contrast):
├─ Current Price Line (WHITE)
└─ Gamma Flip Line (ORANGE)

Priority 2 (Data):
└─ Gamma Wall Bars (BLUE with varying opacity)

Priority 3 (Context):
├─ SD Bands (FAINT GRAY)
└─ Grid Lines (SUBTLE)

Priority 4 (Background):
└─ Canvas (DEEP DARK)
```

## How Strength is Visualized

### v1 (Multi-Color)
```
🔴 Red Wall    = Swing Put
🟢 Green Wall  = Swing Call
🟠 Orange Wall = Long Put
🔵 Blue Wall   = Long Call
```
**Problem:** Color overload, hard to compare strengths

### v2 (Single Color + Opacity)
```
━━━━━━━━━━━━━━━━▓▓▓▓▓▓▓▓ (85% opacity = 85 strength)
━━━━━━━▓▓▓▓▓           (50% opacity = 50 strength)
━━━━━━━━━━━▓▓▓▓▓▓▓▓▓▓  (90% opacity = 90 strength)
```
**Benefit:** Instant visual comparison of wall strength

## Horizontal Bar Chart Benefits

### Why Horizontal?

1. **Price Scale Alignment:** Y-axis shows price levels naturally
2. **Strength Comparison:** Bar length = visual strength magnitude
3. **Less Clutter:** No overlapping time-series data
4. **Better Labels:** Strike prices align vertically

### Example Chart

```
Price ($)
   │
7400├──────────────────▓▓▓▓▓▓▓▓  Call Wall (80%)
7000├──────────▓▓▓▓▓▓            Put Wall (50%)
6800├─────────────────▓▓▓▓▓▓▓▓▓  Put Wall (85%)
6400├────────▓▓▓                 Put Wall (40%)
   │
   └────────────────────────────► Wall Strength
        0                      100
```

## Integrated Symbol Metrics Table

### v1 (Separate Component)
```
┌──────────────────┐
│ Chart Area       │
│                  │
└──────────────────┘

┌──────────────────┐ ← Separate box
│ Symbol Metrics   │
└──────────────────┘
```

### v2 (Integrated)
```
┌──────────────────────────────┐
│                              │
│  Chart Canvas                │
│  (Horizontal Bars)           │
│                              │
├──────────────────────────────┤ ← Seamless
│ Symbol Metrics (Dark Table)  │
└──────────────────────────────┘
```

**Benefits:**
- Feels like one application
- No visual disconnect
- Cleaner scrolling experience

## Collapsible Sidebar

### Default State (Expanded)
```
┌────┬──────────────────┐
│    │                  │
│ C  │   Chart Canvas   │
│ o  │                  │
│ n  │                  │
│ t  │                  │
│ r  │                  │
│ o  │                  │
│ l  │                  │
│ s  │                  │
│    │                  │
└────┴──────────────────┘
 280px
```

### Collapsed State
```
┌─┬─────────────────────┐
│◀│                     │
│ │   Chart Canvas      │
│ │   (Full Width)      │
│ │                     │
│ │                     │
└─┴─────────────────────┘
40px ← Just collapse button
```

## TradingView-Style Top Bar

```
┌────────────────────────────────────────────────────┐
│ GAMMA WALL SCANNER | VIX 20.8 | Regime Normal     │
│ | Updated 3:42pm | ● Live                          │
└────────────────────────────────────────────────────┘
```

**Elements:**
- Instrument name (BOLD)
- Key metrics inline (pipe-separated)
- Status indicator (colored dot)
- Minimalist spacing

## Typography & Spacing

### Font Stack
```css
font-family: "Roboto", "Open Sans", "Arial", sans-serif;
```

### Size Scale
- **12px:** Top bar, chart labels, table headers (uppercase)
- **13px:** Table values, control labels
- **14px:** Sidebar title
- **16px:** Main titles

### Weight Scale
- **400:** Normal text
- **500:** Slightly emphasized
- **600:** Bold key metrics

## Quick Setup

### 1. Install (if new)
```bash
cd frontend
npm install plotly.js-basic-dist
```

### 2. Use v2
```typescript
// App.tsx - Already configured!
import { GammaScannerTab } from './components/GammaScanner';

// Automatically uses v2
<GammaScannerTab />
```

### 3. Revert to v1 (if needed)
```typescript
import { GammaScannerTabV1 } from './components/GammaScanner';

<GammaScannerTabV1 />
```

## Testing Checklist

✅ **Visual Tests**
- [ ] Single blue color for gamma walls
- [ ] Opacity varies with strength
- [ ] White price line is most visible
- [ ] Orange gamma flip line stands out
- [ ] SD bands are subtle (not distracting)
- [ ] Table rows alternate colors smoothly
- [ ] Sidebar collapses to 40px

✅ **Functionality Tests**
- [ ] Hover shows wall details
- [ ] Toggle switches work
- [ ] Sliders adjust values
- [ ] Refresh button fetches data
- [ ] Symbol selection filters chart

✅ **Performance Tests**
- [ ] Chart renders < 1s
- [ ] Smooth resize
- [ ] No lag with 15 symbols

## Configuration Tips

### Optimal Settings for Clarity

```typescript
{
  wallOpacity: 0.8,        // High enough to see
  minStrength: 20,         // Filter noise
  hideWeakWalls: true,     // < 40 strength hidden
  showSDBands: true,       // Context
  showGammaFlip: true,     // Key pivot
  showTable: true,         // Integrated metrics
}
```

### For High-Density Data

```typescript
{
  wallOpacity: 0.6,        // Lower to reduce overlap
  minStrength: 40,         // Show only strong walls
  hideWeakWalls: true,
}
```

## Keyboard Shortcuts

- **← / →** : Collapse/expand sidebar
- **R** : Refresh data
- **T** : Toggle table visibility
- **G** : Toggle gamma flip line

*(To be implemented in future update)*

## Browser Requirements

- Chrome 90+ ✅
- Firefox 88+ ✅
- Safari 14+ ✅
- Edge 90+ ✅

## FAQ

**Q: Can I switch back to v1?**
A: Yes! Import `GammaScannerTabV1` instead.

**Q: Why horizontal bars instead of time-series?**
A: Better for comparing wall strengths at different price levels. Time dimension is less relevant for gamma walls.

**Q: Can I change the blue color?**
A: Currently fixed for consistency. Future update will add theme customization.

**Q: Table looks different - is it broken?**
A: No! It's now integrated below the chart with alternating row colors for better readability.

**Q: Where did the Debug Console go?**
A: Removed from v2 for cleaner design. Use browser devtools console for errors.

---

**v2.0 Status:** ✅ Production Ready
**Migration:** Automatic (no code changes needed)
**Docs:** See `/docs/gamma-scanner/V2_DESIGN.md`
