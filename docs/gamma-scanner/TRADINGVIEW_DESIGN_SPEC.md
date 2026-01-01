# TradingView Design System Specification
## Gamma Wall Scanner v4.0 - Rich, Layered Visualization

---

## 1. Color Palette Enhancement

### Primary Wall Colors

**Call Walls (Resistance) - Red/Orange Gradients:**
```css
/* Weak Call Walls (Strength 0-40) */
--call-weak-start: #FF6B6B;
--call-weak-end: #FF8E8E;

/* Medium Call Walls (Strength 40-70) */
--call-medium-start: #FF5252;
--call-medium-end: #FFA500;

/* Strong Call Walls (Strength 70-100) */
--call-strong-start: #FF3838;
--call-strong-end: #FF6B00;
```

**Put Walls (Support) - Green/Cyan Gradients:**
```css
/* Weak Put Walls (Strength 0-40) */
--put-weak-start: #4ECDC4;
--put-weak-end: #6EE7DF;

/* Medium Put Walls (Strength 40-70) */
--put-medium-start: #26A69A;
--put-medium-end: #4ECDC4;

/* Strong Put Walls (Strength 70-100) */
--put-strong-start: #00897B;
--put-strong-end: #26A69A;
```

### Timeframe Color Coding

**Quarterly Walls (90D) - Purple/Violet:**
```css
--quarterly-primary: #9C27B0;
--quarterly-secondary: #BA68C8;
--quarterly-opacity: 0.15;
--quarterly-border: 1px dashed #9C27B0;
```

**Long-term Walls (30D) - Blue Accent:**
```css
--longterm-primary: #2962FF;
--longterm-secondary: #5E92F3;
--longterm-opacity: 0.25;
--longterm-border: 2px solid rgba(41, 98, 255, 0.6);
```

**Swing Walls (14D) - Primary Colors (Red/Green):**
```css
--swing-opacity: 0.35;
--swing-border: 3px solid;
--swing-call-border-color: rgba(255, 56, 56, 0.8);
--swing-put-border-color: rgba(0, 137, 123, 0.8);
```

### Special Indicators

**Max Pain - Bright Magenta:**
```css
--max-pain-line: #FF0080;
--max-pain-glow: 0 0 8px #FF0080, 0 0 16px rgba(255, 0, 128, 0.5);
--max-pain-width: 3px;
--max-pain-label-bg: rgba(255, 0, 128, 0.95);
--max-pain-label-text: #FFFFFF;
```

**Current Volatility - Blue:**
```css
--volatility-normal: #2962FF;
--volatility-high: #FF6B00;
--volatility-low: #00897B;
--volatility-indicator-size: 12px;
```

### Background & Surface

```css
--background-primary: #0D1117; /* Darker than current #131722 */
--surface-elevated: #1C2128;
--surface-elevated-hover: #22272E;
--grid-line: #30363D;
--border-subtle: #373E47;
```

---

## 2. Layout Transformation

### Dimensional Specifications

**Before (v3.0):**
```
┌────────────────────────────────────────┐
│ Top Bar: 40px                          │
├────────┬───────────────────────────────┤
│        │                               │
│ Side   │      Chart                    │
│ bar    │      Canvas                   │
│ 280px  │                               │
│        │                               │
└────────┴───────────────────────────────┘
```

**After (v4.0):**
```
┌────────────────────────────────────────┐
│ Top Bar: 30px (compact)                │
├──────┬─────────────────────────────────┤
│      │                                 │
│ Side │         Chart Canvas            │
│ bar  │    (Maximum Real Estate)        │
│220px │                                 │
│      │                                 │
│      ├─────────────────────────────────┤
│      │ Metrics Table: 120px (compact)  │
└──────┴─────────────────────────────────┘
```

### Component Dimensions

**Top Bar:**
- Height: `30px` (reduced from 40px)
- Padding: `6px 16px`
- Font size: `11px` (title), `10px` (metrics)
- Timeframe buttons: `36px × 28px`

**Sidebar:**
- Width: `220px` (reduced from 280px)
- Collapsed: `36px`
- Section padding: `12px 14px` (reduced from 16px)
- Control spacing: `8px` vertical gap

**Chart Canvas:**
- Margins: `t: 8px, b: 8px, l: 8px, r: 80px`
- Right axis width: `80px` (more space for strike labels)
- Grid line width: `0.5px` (subtle)

**Metrics Table:**
- Height: `120px` (fixed, scrollable)
- Row height: `32px` (compact)
- Font size: `10px`
- Cell padding: `6px 10px`

---

## 3. Wall Visualization Design

### Gradient Fill Specifications

**Implementation Pattern:**
```typescript
interface WallGradient {
  type: 'linear';
  x0: 0;
  y0: 0;
  x1: 1;
  y1: 0;
  colorscale: [
    [0, startColor],    // Left edge
    [0.5, midColor],    // Center (brightest)
    [1, endColor]       // Right edge
  ];
}

// Example for Strong Call Wall:
const strongCallGradient = {
  colorscale: [
    [0, 'rgba(255, 56, 56, 0.35)'],
    [0.5, 'rgba(255, 107, 0, 0.45)'],
    [1, 'rgba(255, 56, 56, 0.35)']
  ]
};
```

### Wall Rendering Layers (Z-Index)

```
Z-Index Stack (bottom to top):
- 1: Standard Deviation Bands (faint dotted)
- 2: Quarterly Walls (90D) - dashed, lowest opacity
- 3: Long-term Walls (30D) - solid, medium opacity
- 4: Swing Walls (14D) - bold, highest opacity
- 5: Candlesticks
- 6: Current Price Line
- 7: Max Pain Line (always on top)
- 8: Hover Cards & Tooltips (z-index: 1000)
```

### Wall Shape Specifications

**Rounded Rectangle Walls:**
```typescript
interface WallShape {
  type: 'rect';
  xref: 'x';
  yref: 'y';
  x0: startDate;
  x1: endDate;
  y0: strike - (height / 2);  // Center on strike
  y1: strike + (height / 2);
  fillcolor: gradientColor;
  line: {
    color: borderColor;
    width: borderWidth;
  };
  layer: 'below'; // Below candlesticks
  opacity: calculateOpacity(strength);
}

// Height calculation based on strength
const wallHeight = basePrice * (0.003 + (strength / 100) * 0.007);
// Strength 0: 0.3% of price
// Strength 100: 1.0% of price
```

### Border Styling

**Quarterly Walls (90D):**
- Style: `dashed`
- Width: `1px`
- Dash pattern: `[5, 3]` (5px dash, 3px gap)
- Color: `rgba(156, 39, 176, 0.6)`

**Long-term Walls (30D):**
- Style: `solid`
- Width: `2px`
- Color: `rgba(41, 98, 255, 0.6)`

**Swing Walls (14D):**
- Style: `solid`
- Width: `3px`
- Color: `rgba(255, 56, 56, 0.8)` for calls, `rgba(0, 137, 123, 0.8)` for puts

---

## 4. Strike Price Labels (Right Y-Axis)

### Label Design

**Strong Walls (Strength > 70):**
```css
.strike-label-strong {
  font-size: 12px;
  font-weight: 700;
  padding: 4px 8px;
  border-radius: 3px;
  background: rgba(255, 56, 56, 0.9); /* Call */
  background: rgba(0, 137, 123, 0.9); /* Put */
  color: #FFFFFF;
  border-left: 4px solid #FF3838; /* Call */
  border-left: 4px solid #00897B; /* Put */
}
```

**Medium Walls (Strength 40-70):**
```css
.strike-label-medium {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 6px;
  background: rgba(255, 82, 82, 0.7);
  color: #FFFFFF;
}
```

**Weak Walls (Strength < 40):**
```css
.strike-label-weak {
  font-size: 10px;
  font-weight: 500;
  padding: 2px 5px;
  background: rgba(255, 107, 107, 0.5);
  color: rgba(255, 255, 255, 0.9);
}
```

### Label Positioning
- Align: Right edge of chart canvas
- Offset: `+4px` from Y-axis line
- Anti-collision: Minimum 24px vertical spacing between labels
- Overflow: Hide labels outside visible range

---

## 5. Hover Card / Tooltip Design

### Card Layout

```
┌─────────────────────────────────────┐
│ █ SPX SWING PUT WALL                │ ← Header (colored bar)
├─────────────────────────────────────┤
│ Strike Price:        $5,700.00      │
│ Gamma Exposure:      $847M          │
│ Wall Strength:       ████████░░ 82  │ ← Progress bar
│ Days to Expiration:  14D            │
│ Open Interest:       125,430        │
│ Delta Exposure:      $1.2B          │
│ Implied Volatility:  28.4%          │
├─────────────────────────────────────┤
│              [Add Alert]            │ ← Action button
└─────────────────────────────────────┘
```

### Card Styling

```css
.hover-card {
  position: absolute;
  width: 280px;
  background: rgba(28, 33, 40, 0.98);
  backdrop-filter: blur(10px);
  border: 1px solid #373E47;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
  padding: 0;
  font-family: 'Roboto', sans-serif;
  z-index: 1000;
  pointer-events: auto;
}

.hover-card-header {
  padding: 10px 12px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  border-bottom: 1px solid #373E47;
  display: flex;
  align-items: center;
  gap: 8px;
}

.hover-card-header::before {
  content: '';
  width: 4px;
  height: 16px;
  background: linear-gradient(180deg, #FF3838, #FF6B00);
  border-radius: 2px;
}

.hover-card-body {
  padding: 12px;
}

.hover-card-row {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  line-height: 20px;
  color: #8B949E;
}

.hover-card-row-value {
  color: #D1D4DC;
  font-weight: 600;
}

.hover-card-footer {
  padding: 10px 12px;
  border-top: 1px solid #373E47;
}

.hover-card-button {
  width: 100%;
  padding: 8px;
  background: #2962FF;
  color: #FFFFFF;
  border: none;
  border-radius: 5px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.hover-card-button:hover {
  background: #1E4FCC;
}
```

### Strength Progress Bar

```html
<div class="strength-bar-container">
  <span class="strength-label">Wall Strength:</span>
  <div class="strength-bar">
    <div class="strength-fill" style="width: 82%;"></div>
  </div>
  <span class="strength-value">82</span>
</div>
```

```css
.strength-bar-container {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 8px 0;
}

.strength-bar {
  flex: 1;
  height: 6px;
  background: rgba(55, 62, 71, 0.5);
  border-radius: 3px;
  overflow: hidden;
}

.strength-fill {
  height: 100%;
  background: linear-gradient(90deg, #FF3838, #FF6B00);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.strength-value {
  font-weight: 700;
  color: #D1D4DC;
  min-width: 24px;
  text-align: right;
}
```

---

## 6. Compact Sidebar Design

### Visual Hierarchy

**Section Structure:**
```
┌──────────────────────┐
│ ⚡ QUICK PRESETS      │ ← Prominent
│ ○ Day Trader         │
│ ○ Swing Trader       │
│ ○ Options Seller     │
├──────────────────────┤
│ 📊 WALL DISPLAY      │ ← Medium emphasis
│ ☑ 14D Swing          │
│ ☑ 30D Long-term      │
│ ☐ 90D Quarterly      │
├──────────────────────┤
│ 🎨 VISUAL            │ ← Collapsed by default
│ ▸ Click to expand    │
├──────────────────────┤
│ ⚙️ ADVANCED          │ ← Collapsed
│ ▸ Click to expand    │
└──────────────────────┘
```

### Section Styling

```css
.sidebar-section {
  padding: 12px 14px;
  border-bottom: 1px solid #30363D;
}

.sidebar-section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  color: #8B949E;
  margin-bottom: 10px;
}

.sidebar-section-header-icon {
  font-size: 12px;
}

.sidebar-control {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0;
  font-size: 11px;
  color: #D1D4DC;
}

/* Collapsible section */
.sidebar-section-collapsible {
  cursor: pointer;
  transition: background 0.2s;
}

.sidebar-section-collapsible:hover {
  background: rgba(255, 255, 255, 0.03);
}
```

### Preset Buttons

```css
.preset-button {
  width: 100%;
  padding: 10px 12px;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #1C2128 0%, #22272E 100%);
  border: 1px solid #373E47;
  border-radius: 6px;
  color: #D1D4DC;
  font-size: 11px;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
}

.preset-button::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, #2962FF, #5E92F3);
  opacity: 0;
  transition: opacity 0.2s;
}

.preset-button:hover {
  background: linear-gradient(135deg, #22272E 0%, #2A2F38 100%);
  border-color: #2962FF;
  transform: translateX(2px);
}

.preset-button:hover::before {
  opacity: 1;
}

.preset-button-active {
  background: linear-gradient(135deg, #1E3A8A 0%, #2962FF 100%);
  border-color: #2962FF;
}

.preset-button-active::before {
  opacity: 1;
  background: #FFFFFF;
}
```

---

## 7. Typography & Iconography

### Font Scale

```css
:root {
  /* Display */
  --font-size-display: 14px;
  --font-weight-display: 700;

  /* Headings */
  --font-size-h1: 13px;
  --font-size-h2: 12px;
  --font-size-h3: 11px;
  --font-weight-heading: 600;

  /* Body */
  --font-size-body: 11px;
  --font-size-small: 10px;
  --font-size-tiny: 9px;
  --font-weight-body: 400;

  /* Labels */
  --font-size-label: 10px;
  --font-weight-label: 500;
  --letter-spacing-label: 0.5px;
}
```

### Icon System

**Wall Type Icons:**
```
14D Swing:     📊 or ⚡ (fast-moving)
30D Long-term: 📈 or ⏳ (medium-term)
90D Quarterly: 📅 or 📆 (long-term)
Max Pain:      🎯 or 💥 (critical level)
Gamma Flip:    🔄 or ↕️ (pivot)
SD Bands:      📏 or ◈ (boundaries)
```

**Status Icons:**
```
Live:          🟢 or ● (green dot)
Offline:       🔴 or ● (red dot)
Loading:       ⟳ (rotating)
Error:         ⚠️ (warning triangle)
Success:       ✓ (checkmark)
```

### Number Formatting

**Price Formatting:**
```typescript
const formatPrice = (price: number): string => {
  if (price >= 10000) return `$${(price / 1000).toFixed(1)}K`;
  if (price >= 1000) return `$${price.toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
  return `$${price.toFixed(2)}`;
};

// Examples:
// 5724.09 → $5,724
// 15234.5 → $15.2K
// 123.45 → $123.45
```

**GEX Formatting:**
```typescript
const formatGEX = (gex: number): string => {
  const absGex = Math.abs(gex);
  if (absGex >= 1000) return `${(gex / 1000).toFixed(1)}B`;
  return `${gex.toFixed(1)}M`;
};

// Examples:
// 847.3 → $847M
// 1234.5 → $1.2B
// -250.0 → -$250M
```

**Percentage Formatting:**
```typescript
const formatPercent = (value: number): string => {
  return `${value.toFixed(1)}%`;
};

// Examples:
// 28.437 → 28.4%
// 0.5 → 0.5%
```

---

## 8. Animation & Transitions

### Transition Timing

```css
:root {
  --transition-fast: 150ms;
  --transition-medium: 250ms;
  --transition-slow: 400ms;
  --easing-standard: cubic-bezier(0.4, 0.0, 0.2, 1);
  --easing-decelerate: cubic-bezier(0.0, 0.0, 0.2, 1);
  --easing-accelerate: cubic-bezier(0.4, 0.0, 1, 1);
}
```

### Wall Fade Transitions

```css
.gamma-wall {
  transition: opacity var(--transition-medium) var(--easing-standard),
              transform var(--transition-fast) var(--easing-standard);
}

.gamma-wall-enter {
  opacity: 0;
  transform: scaleY(0);
}

.gamma-wall-enter-active {
  opacity: 1;
  transform: scaleY(1);
}

.gamma-wall-exit {
  opacity: 1;
}

.gamma-wall-exit-active {
  opacity: 0;
  transition: opacity var(--transition-fast) var(--easing-accelerate);
}
```

### Max Pain Pulse Animation

```css
@keyframes max-pain-pulse {
  0%, 100% {
    opacity: 1;
    filter: drop-shadow(0 0 4px #FF0080);
  }
  50% {
    opacity: 0.85;
    filter: drop-shadow(0 0 12px #FF0080);
  }
}

.max-pain-line {
  animation: max-pain-pulse 2s ease-in-out infinite;
}
```

### Hover Card Entrance

```css
@keyframes hover-card-enter {
  from {
    opacity: 0;
    transform: translateY(-8px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.hover-card {
  animation: hover-card-enter var(--transition-medium) var(--easing-decelerate);
}
```

---

## 9. Loading & Error States

### Skeleton Screen

```html
<div class="chart-skeleton">
  <div class="skeleton-header"></div>
  <div class="skeleton-chart">
    <div class="skeleton-candlestick"></div>
    <div class="skeleton-wall"></div>
    <div class="skeleton-wall"></div>
    <div class="skeleton-wall"></div>
  </div>
  <div class="skeleton-metrics"></div>
</div>
```

```css
@keyframes skeleton-pulse {
  0%, 100% {
    opacity: 0.3;
  }
  50% {
    opacity: 0.6;
  }
}

.skeleton-element {
  background: linear-gradient(90deg,
    rgba(55, 62, 71, 0.3) 0%,
    rgba(55, 62, 71, 0.5) 50%,
    rgba(55, 62, 71, 0.3) 100%);
  background-size: 200% 100%;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
  border-radius: 4px;
}

.skeleton-wall {
  height: 40px;
  margin: 12px 0;
}
```

### Error State

```html
<div class="error-state">
  <div class="error-icon">⚠️</div>
  <div class="error-title">Failed to Load Gamma Data</div>
  <div class="error-message">
    Unable to connect to data source. Please check your connection.
  </div>
  <button class="error-retry-button">Retry</button>
</div>
```

```css
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px;
  text-align: center;
}

.error-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.6;
}

.error-title {
  font-size: 16px;
  font-weight: 600;
  color: #D1D4DC;
  margin-bottom: 8px;
}

.error-message {
  font-size: 12px;
  color: #8B949E;
  max-width: 400px;
  margin-bottom: 24px;
}

.error-retry-button {
  padding: 10px 24px;
  background: #2962FF;
  color: #FFFFFF;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.error-retry-button:hover {
  background: #1E4FCC;
}
```

---

## 10. Implementation Priority

### Phase 1: Core Visual Enhancements (Week 1)
1. ✅ Implement gradient fill system for walls
2. ✅ Add rounded rectangle wall shapes
3. ✅ Update color palette to new specifications
4. ✅ Add layered rendering (z-index management)
5. ✅ Create max pain indicator

### Phase 2: Interactive Features (Week 2)
1. ✅ Build hover card system
2. ✅ Add wall click interactions
3. ✅ Implement strength progress bars
4. ✅ Create pinnable cards

### Phase 3: Layout Optimization (Week 3)
1. ✅ Compact sidebar (280px → 220px)
2. ✅ Reduce top bar height (40px → 30px)
3. ✅ Redesign metrics table
4. ✅ Add preset buttons

### Phase 4: Polish & Refinement (Week 4)
1. ✅ Add animations and transitions
2. ✅ Implement loading states
3. ✅ Create error states
4. ✅ Performance optimization

---

**Version:** 4.0.0
**Last Updated:** November 7, 2025
**Design Lead:** UI/UX Designer Agent
**Status:** 📋 Specification Complete - Ready for Implementation
