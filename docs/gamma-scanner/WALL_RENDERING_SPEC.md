# Wall Rendering Specification
## Multi-Layer Gradient Visualization System

---

## 1. Multi-Layer Wall Architecture

### Layer Stack (Z-Index Ordering)

```typescript
enum WallLayer {
  SD_BANDS = 1,           // Background statistical bands
  QUARTERLY_WALLS = 2,    // 90D walls (lowest priority)
  LONGTERM_WALLS = 3,     // 30D walls (medium priority)
  SWING_WALLS = 4,        // 14D walls (highest priority)
  CANDLESTICKS = 5,       // Price action (always visible)
  CURRENT_PRICE = 6,      // Current price line
  MAX_PAIN = 7,           // Max pain (always on top)
  HOVER_CARDS = 1000      // UI overlays
}
```

### Visual Encoding Matrix

| Property | Encodes | Range | Visual Effect |
|----------|---------|-------|---------------|
| **Opacity** | Wall Strength | 0.15-0.35 | Weak → Strong |
| **Gradient Intensity** | GEX Concentration | Flat → Vivid | Low → High |
| **Height** | Absolute GEX | 0.3%-1.0% of price | Small → Large |
| **Border Width** | Time frame | 1px-3px | Quarterly → Swing |
| **Color Hue** | Wall Type | Red/Green | Call/Put |

---

## 2. Plotly.js Implementation

### Gradient-Filled Wall Rectangle

```typescript
interface GradientWallTrace {
  type: 'scatter';
  mode: 'none';
  fill: 'toself';
  x: number[];  // [startDate, endDate, endDate, startDate]
  y: number[];  // [bottom, bottom, top, top]
  fillcolor: string;  // Gradient definition
  line: {
    color: string;
    width: number;
    dash?: 'solid' | 'dash' | 'dot';
  };
  name: string;
  showlegend: boolean;
  legendgroup: string;
  hoverinfo: 'none' | 'text';
  hovertext?: string;
  hoverlabel?: {
    bgcolor: string;
    font: { color: string; size: number };
  };
}

// Example: Strong Swing Call Wall
const createSwingCallWall = (
  strike: number,
  strength: number,
  gex: number,
  startDate: string,
  endDate: string,
  currentPrice: number
): GradientWallTrace => {
  const height = currentPrice * (0.003 + (strength / 100) * 0.007);
  const opacity = 0.25 + (strength / 100) * 0.10; // 0.25-0.35 range

  // Gradient intensity based on strength
  const gradientStart = strength > 70 ? 'rgba(255, 56, 56, 0.35)' : 'rgba(255, 107, 107, 0.25)';
  const gradientMid = strength > 70 ? 'rgba(255, 107, 0, 0.45)' : 'rgba(255, 142, 0, 0.35)';
  const gradientEnd = strength > 70 ? 'rgba(255, 56, 56, 0.35)' : 'rgba(255, 107, 107, 0.25)';

  return {
    type: 'scatter',
    mode: 'none',
    fill: 'toself',
    x: [startDate, endDate, endDate, startDate],
    y: [strike - height/2, strike - height/2, strike + height/2, strike + height/2],
    fillcolor: `linear-gradient(90deg, ${gradientStart} 0%, ${gradientMid} 50%, ${gradientEnd} 100%)`,
    line: {
      color: `rgba(255, 56, 56, ${opacity * 2})`,
      width: 3,
      dash: 'solid'
    },
    name: `SWING CALL $${strike.toFixed(0)}`,
    showlegend: true,
    legendgroup: 'swing-calls',
    hoverinfo: 'text',
    hovertext: `<b>Swing Call Wall</b><br>Strike: $${strike.toFixed(2)}<br>GEX: $${gex.toFixed(1)}M<br>Strength: ${strength.toFixed(0)}`,
    hoverlabel: {
      bgcolor: 'rgba(28, 33, 40, 0.98)',
      font: { color: '#D1D4DC', size: 11 }
    }
  };
};
```

### Plotly Shape Alternative (Better Performance)

```typescript
interface WallShape extends Partial<Plotly.Shape> {
  type: 'rect';
  xref: 'x';
  yref: 'y';
  x0: string | number;  // Start date/time
  x1: string | number;  // End date/time
  y0: number;           // Bottom price
  y1: number;           // Top price
  fillcolor: string;
  line: {
    color: string;
    width: number;
    dash?: 'solid' | 'dash' | 'dot';
  };
  layer: 'below' | 'above';
  opacity: number;
}

// Shape-based wall (more efficient for many walls)
const createWallShape = (
  strike: number,
  strength: number,
  timeframe: '14D' | '30D' | '90D',
  type: 'call' | 'put',
  xStart: string,
  xEnd: string,
  currentPrice: number
): WallShape => {
  const height = currentPrice * (0.003 + (strength / 100) * 0.007);
  const opacity = getOpacityForTimeframe(timeframe, strength);
  const color = getGradientColor(type, strength);
  const borderWidth = getBorderWidth(timeframe);
  const borderStyle = timeframe === '90D' ? 'dash' : 'solid';

  return {
    type: 'rect',
    xref: 'x',
    yref: 'y',
    x0: xStart,
    x1: xEnd,
    y0: strike - height/2,
    y1: strike + height/2,
    fillcolor: color,
    line: {
      color: getBorderColor(type, opacity),
      width: borderWidth,
      dash: borderStyle
    },
    layer: 'below', // Below candlesticks
    opacity: opacity
  };
};

// Helper functions
const getOpacityForTimeframe = (timeframe: string, strength: number): number => {
  const baseOpacity = {
    '14D': 0.35,  // Swing - highest
    '30D': 0.25,  // Long-term - medium
    '90D': 0.15   // Quarterly - lowest
  }[timeframe] || 0.25;

  // Strength multiplier: 0-40 → 0.7x, 40-70 → 1.0x, 70-100 → 1.2x
  const strengthMultiplier = strength < 40 ? 0.7 : strength > 70 ? 1.2 : 1.0;

  return Math.min(baseOpacity * strengthMultiplier, 1.0);
};

const getGradientColor = (type: 'call' | 'put', strength: number): string => {
  if (type === 'call') {
    if (strength > 70) return 'rgba(255, 56, 56, 0.35)';
    if (strength > 40) return 'rgba(255, 82, 82, 0.28)';
    return 'rgba(255, 107, 107, 0.20)';
  } else {
    if (strength > 70) return 'rgba(0, 137, 123, 0.35)';
    if (strength > 40) return 'rgba(38, 166, 154, 0.28)';
    return 'rgba(78, 205, 196, 0.20)';
  }
};

const getBorderWidth = (timeframe: string): number => {
  return { '14D': 3, '30D': 2, '90D': 1 }[timeframe] || 2;
};

const getBorderColor = (type: 'call' | 'put', opacity: number): string => {
  const alpha = Math.min(opacity * 2, 0.8);
  return type === 'call'
    ? `rgba(255, 56, 56, ${alpha})`
    : `rgba(0, 137, 123, ${alpha})`;
};
```

---

## 3. Gradient System Implementation

### CSS Gradient Approach (Limited in Plotly)

Since Plotly doesn't support CSS gradients directly in fills, we simulate gradients using:

**Method 1: Layered Semi-Transparent Shapes**
```typescript
const createLayeredGradient = (
  strike: number,
  strength: number,
  type: 'call' | 'put'
): WallShape[] => {
  const layers = 5;
  const shapes: WallShape[] = [];
  const baseColor = type === 'call' ? [255, 56, 56] : [0, 137, 123];

  for (let i = 0; i < layers; i++) {
    const layerOpacity = ((layers - i) / layers) * 0.35;
    const layerHeight = (currentPrice * 0.01) * (1 - (i / layers) * 0.3);

    shapes.push({
      type: 'rect',
      x0: startDate,
      x1: endDate,
      y0: strike - layerHeight/2,
      y1: strike + layerHeight/2,
      fillcolor: `rgba(${baseColor.join(',')}, ${layerOpacity})`,
      line: { width: 0 },
      layer: 'below',
      opacity: 1.0
    });
  }

  return shapes;
};
```

**Method 2: SVG Pattern (Advanced)**
```typescript
// Define SVG gradient pattern
const createSVGGradient = (id: string, type: 'call' | 'put', strength: number): string => {
  const colors = type === 'call'
    ? ['#FF3838', '#FF6B00', '#FF3838']
    : ['#00897B', '#26A69A', '#00897B'];

  return `
    <svg width="0" height="0">
      <defs>
        <linearGradient id="${id}" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style="stop-color:${colors[0]};stop-opacity:0.35" />
          <stop offset="50%" style="stop-color:${colors[1]};stop-opacity:0.45" />
          <stop offset="100%" style="stop-color:${colors[2]};stop-opacity:0.35" />
        </linearGradient>
      </defs>
    </svg>
  `;
};

// Use pattern in Plotly
const wallWithGradient = {
  fillcolor: `url(#gradient-swing-call-${strike})`,
  // ... other properties
};
```

---

## 4. Max Pain Visualization

### Max Pain Line Specification

```typescript
interface MaxPainTrace {
  type: 'scatter';
  mode: 'lines+text';
  x: number[];  // [startDate, endDate]
  y: number[];  // [maxPainPrice, maxPainPrice]
  line: {
    color: '#FF0080';
    width: 3;
    dash: 'solid';
  };
  text: string[];  // ['', 'MAX PAIN: $5,700']
  textposition: 'middle right';
  textfont: {
    family: 'Roboto, sans-serif';
    size: 13;
    color: '#FF0080';
    weight: 700;
  };
  name: 'Max Pain';
  showlegend: true;
  hovertemplate: '<b>Max Pain Level</b><br>Price: $%{y:.2f}<br>Total Option Value: $%{customdata}M<extra></extra>';
  customdata: number[];  // [totalOptionValue]
}

const createMaxPainLine = (
  maxPainPrice: number,
  totalOptionValue: number,
  startDate: string,
  endDate: string
): MaxPainTrace => {
  return {
    type: 'scatter',
    mode: 'lines+text',
    x: [startDate, endDate],
    y: [maxPainPrice, maxPainPrice],
    line: {
      color: '#FF0080',
      width: 3,
      dash: 'solid'
    },
    text: ['', `MAX PAIN: $${maxPainPrice.toFixed(0)}`],
    textposition: 'middle right',
    textfont: {
      family: 'Roboto, sans-serif',
      size: 13,
      color: '#FF0080',
      weight: 700
    },
    name: 'Max Pain',
    showlegend: true,
    hovertemplate: `<b>Max Pain Level</b><br>Price: $${maxPainPrice.toFixed(2)}<br>Total Option Value: $${totalOptionValue.toFixed(1)}M<extra></extra>`,
    customdata: [totalOptionValue]
  };
};
```

### Max Pain Glow Effect (CSS)

```css
/* Apply to SVG path element for max pain line */
.max-pain-line {
  filter: drop-shadow(0 0 4px #FF0080)
          drop-shadow(0 0 8px rgba(255, 0, 128, 0.5))
          drop-shadow(0 0 12px rgba(255, 0, 128, 0.3));
}

/* Animated pulse */
@keyframes max-pain-pulse {
  0%, 100% {
    filter: drop-shadow(0 0 4px #FF0080)
            drop-shadow(0 0 8px rgba(255, 0, 128, 0.5));
  }
  50% {
    filter: drop-shadow(0 0 8px #FF0080)
            drop-shadow(0 0 16px rgba(255, 0, 128, 0.7));
  }
}

.max-pain-line-animated {
  animation: max-pain-pulse 2s ease-in-out infinite;
}
```

---

## 5. Standard Deviation Bands

### SD Band Configuration

```typescript
interface SDBandTrace {
  type: 'scatter';
  mode: 'lines';
  x: number[];
  y: number[];
  line: {
    color: string;
    width: number;
    dash: 'dot';
  };
  name: string;
  showlegend: boolean;
  hovertemplate: string;
  opacity: number;
}

const createSDBands = (
  symbol: ParsedSymbolData,
  dates: string[]
): SDBandTrace[] => {
  const bands = [
    { level: symbol.sdBands.lower_2sd, label: '-2σ', opacity: 0.08 },
    { level: symbol.sdBands.lower_1_5sd, label: '-1.5σ', opacity: 0.10 },
    { level: symbol.sdBands.lower_1sd, label: '-1σ', opacity: 0.12 },
    { level: symbol.sdBands.upper_1sd, label: '+1σ', opacity: 0.12 },
    { level: symbol.sdBands.upper_1_5sd, label: '+1.5σ', opacity: 0.10 },
    { level: symbol.sdBands.upper_2sd, label: '+2σ', opacity: 0.08 }
  ];

  return bands.map(band => ({
    type: 'scatter',
    mode: 'lines',
    x: [dates[0], dates[dates.length - 1]],
    y: [band.level, band.level],
    line: {
      color: '#787B86',
      width: 1,
      dash: 'dot'
    },
    name: band.label,
    showlegend: false,
    hovertemplate: `${band.label}: $${band.level.toFixed(2)}<extra></extra>`,
    opacity: band.opacity
  }));
};
```

---

## 6. Performance Optimizations

### Viewport Culling

```typescript
interface ViewportBounds {
  minPrice: number;
  maxPrice: number;
  startDate: Date;
  endDate: Date;
}

const cullWallsToViewport = (
  walls: GammaWall[],
  viewport: ViewportBounds,
  buffer: number = 0.1  // 10% buffer
): GammaWall[] => {
  const priceRange = viewport.maxPrice - viewport.minPrice;
  const bufferAmount = priceRange * buffer;

  return walls.filter(wall => {
    const inPriceRange = wall.strike >= (viewport.minPrice - bufferAmount) &&
                        wall.strike <= (viewport.maxPrice + bufferAmount);

    // Time-based culling (for future historical data)
    const inTimeRange = true;  // Implement when historical data added

    return inPriceRange && inTimeRange;
  });
};
```

### Level of Detail (LOD)

```typescript
enum DetailLevel {
  HIGH = 'high',      // Full gradients, all walls
  MEDIUM = 'medium',  // Simplified gradients, strong walls only
  LOW = 'low'         // Solid colors, strongest walls only
}

const determineDetailLevel = (
  visibleWallCount: number,
  zoomLevel: number
): DetailLevel => {
  if (visibleWallCount > 100 || zoomLevel < 0.3) {
    return DetailLevel.LOW;
  } else if (visibleWallCount > 50 || zoomLevel < 0.6) {
    return DetailLevel.MEDIUM;
  }
  return DetailLevel.HIGH;
};

const renderWallWithLOD = (
  wall: GammaWall,
  detailLevel: DetailLevel
): WallShape | null => {
  // LOW: Only show walls with strength > 70
  if (detailLevel === DetailLevel.LOW && wall.strength < 70) {
    return null;
  }

  // MEDIUM: Show walls with strength > 40, simplified rendering
  if (detailLevel === DetailLevel.MEDIUM && wall.strength < 40) {
    return null;
  }

  // Adjust rendering complexity
  const useGradient = detailLevel === DetailLevel.HIGH;
  const useBorder = detailLevel !== DetailLevel.LOW;

  return createWallShape(
    wall.strike,
    wall.strength,
    wall.timeframe,
    wall.type,
    startDate,
    endDate,
    currentPrice,
    { useGradient, useBorder }
  );
};
```

### Trace Batching

```typescript
// Instead of creating 100 individual traces, batch similar walls
interface BatchedWallGroup {
  timeframe: '14D' | '30D' | '90D';
  type: 'call' | 'put';
  walls: GammaWall[];
}

const batchWallsByType = (walls: GammaWall[]): BatchedWallGroup[] => {
  const groups = new Map<string, GammaWall[]>();

  walls.forEach(wall => {
    const key = `${wall.timeframe}-${wall.type}`;
    if (!groups.has(key)) {
      groups.set(key, []);
    }
    groups.get(key)!.push(wall);
  });

  return Array.from(groups.entries()).map(([key, walls]) => {
    const [timeframe, type] = key.split('-');
    return { timeframe, type, walls } as BatchedWallGroup;
  });
};

// Create single trace with multiple shapes for each group
const createBatchedTrace = (group: BatchedWallGroup): Plotly.Data => {
  // Use single scatter trace with multiple fill regions
  const x: number[] = [];
  const y: number[] = [];

  group.walls.forEach((wall, idx) => {
    if (idx > 0) {
      x.push(null as any);  // Break between shapes
      y.push(null as any);
    }

    const height = calculateWallHeight(wall);
    x.push(startDate, endDate, endDate, startDate);
    y.push(
      wall.strike - height/2,
      wall.strike - height/2,
      wall.strike + height/2,
      wall.strike + height/2
    );
  });

  return {
    type: 'scatter',
    mode: 'none',
    fill: 'toself',
    x,
    y,
    fillcolor: getGradientColor(group.type, 50),  // Average strength
    line: {
      color: getBorderColor(group.type, 0.3),
      width: getBorderWidth(group.timeframe)
    },
    name: `${group.timeframe} ${group.type.toUpperCase()} Walls`,
    showlegend: true,
    legendgroup: `${group.timeframe}-${group.type}`
  };
};
```

---

## 7. WebGL Acceleration

### Enable WebGL for Large Datasets

```typescript
interface PlotlyConfig {
  responsive: true;
  displayModeBar: boolean;
  scrollZoom: boolean;
  // Enable WebGL for performance
  webgl: boolean;
}

const chartConfig: Partial<Plotly.Config> = {
  responsive: true,
  displayModeBar: true,
  scrollZoom: true,
  modeBarButtonsToRemove: ['toImage', 'lasso2d', 'select2d'],
  displaylogo: false
};

// Use scattergl instead of scatter for 100+ data points
const createWebGLWall = (wall: GammaWall): Plotly.Data => {
  return {
    type: 'scattergl',  // WebGL-accelerated
    mode: 'lines',
    x: [startDate, endDate],
    y: [wall.strike, wall.strike],
    line: {
      color: getWallColor(wall),
      width: calculateWallThickness(wall)
    },
    // ... other properties
  };
};
```

### GPU Shader for Gradients (Advanced)

```glsl
// Fragment shader for gradient rendering
precision mediump float;

varying vec2 vPosition;
uniform vec3 colorStart;
uniform vec3 colorEnd;
uniform float opacity;
uniform float strength;

void main() {
  // Horizontal gradient
  float gradient = smoothstep(0.0, 1.0, vPosition.x);

  // Center brightening based on strength
  float center = 1.0 - abs(vPosition.x - 0.5) * 2.0;
  float brightness = 1.0 + (strength / 100.0) * center * 0.5;

  // Interpolate colors
  vec3 color = mix(colorStart, colorEnd, gradient) * brightness;

  gl_FragColor = vec4(color, opacity);
}
```

---

## 8. Complete Rendering Pipeline

```typescript
class GammaWallRenderer {
  private plotlyDiv: HTMLDivElement;
  private currentDetailLevel: DetailLevel = DetailLevel.HIGH;
  private cachedTraces: Map<string, Plotly.Data> = new Map();

  constructor(div: HTMLDivElement) {
    this.plotlyDiv = div;
  }

  render(
    symbols: ParsedSymbolData[],
    settings: GammaScannerSettings,
    viewport: ViewportBounds
  ): void {
    // 1. Collect all walls
    const allWalls = this.collectWalls(symbols, settings);

    // 2. Cull to viewport
    const visibleWalls = cullWallsToViewport(allWalls, viewport);

    // 3. Determine detail level
    this.currentDetailLevel = determineDetailLevel(
      visibleWalls.length,
      viewport.zoomLevel
    );

    // 4. Sort by layer (quarterly → long → swing)
    const sortedWalls = this.sortByLayer(visibleWalls);

    // 5. Batch similar walls
    const batchedGroups = batchWallsByType(sortedWalls);

    // 6. Create traces
    const traces: Plotly.Data[] = [];

    // Add SD bands first (lowest layer)
    traces.push(...createSDBands(symbols[0], dates));

    // Add walls by group
    batchedGroups.forEach(group => {
      traces.push(createBatchedTrace(group));
    });

    // Add candlesticks
    traces.push(createCandlestickTrace(candleData));

    // Add current price line
    traces.push(createCurrentPriceLine(currentPrice, dates));

    // Add max pain (top layer)
    if (settings.showMaxPain) {
      traces.push(createMaxPainLine(maxPain, totalOI, dates));
    }

    // 7. Update plot
    Plotly.react(this.plotlyDiv, traces, this.getLayout(), this.getConfig());
  }

  private sortByLayer(walls: GammaWall[]): GammaWall[] {
    const layerOrder = { '90D': 1, '30D': 2, '14D': 3 };
    return walls.sort((a, b) => layerOrder[a.timeframe] - layerOrder[b.timeframe]);
  }

  private collectWalls(
    symbols: ParsedSymbolData[],
    settings: GammaScannerSettings
  ): GammaWall[] {
    const walls: GammaWall[] = [];

    symbols.forEach(symbol => {
      symbol.walls.forEach(wall => {
        // Apply filters
        if (!this.shouldRenderWall(wall, settings)) return;

        // Apply regime adjustment
        let strength = wall.strength;
        if (settings.applyRegimeAdjustment) {
          strength = applyRegimeAdjustment(strength, marketRegime);
        }

        walls.push({ ...wall, strength });
      });
    });

    return walls;
  }

  private shouldRenderWall(
    wall: GammaWall,
    settings: GammaScannerSettings
  ): boolean {
    // Check timeframe toggles
    if (wall.timeframe === 'swing' && !settings.showSwingWalls) return false;
    if (wall.timeframe === 'long' && !settings.showLongWalls) return false;
    if (wall.timeframe === 'quarterly' && !settings.showQuarterlyWalls) return false;

    // Check strength threshold
    if (wall.strength < settings.minStrength) return false;
    if (settings.hideWeakWalls && wall.strength < 40) return false;

    return true;
  }
}
```

---

**Version:** 1.0.0
**Last Updated:** November 7, 2025
**Author:** Data Visualization Specialist Agent
**Status:** 📋 Complete - Ready for Implementation
