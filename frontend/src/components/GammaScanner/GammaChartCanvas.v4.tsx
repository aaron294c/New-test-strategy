/**
 * Gamma Chart Canvas v4.0 - TradingView Quality Visualization
 * Rich gradients, layered walls, max pain indicator, professional styling
 */

import React, { useMemo, useEffect, useRef } from 'react';
import Plotly from 'plotly.js-basic-dist';
import { ParsedSymbolData, GammaScannerSettings } from './types';
import { applyRegimeAdjustment } from './dataParser';
import {
  THEME_COLORS,
  getWallColors,
  getTimeframeOpacity,
  getBorderWidth,
  MAX_PAIN,
  SD_BANDS,
  formatPrice,
  formatGEX,
} from './colors';

interface GammaChartCanvasV4Props {
  symbols: ParsedSymbolData[];
  settings: GammaScannerSettings;
  marketRegime: string;
  timeframe: '1D' | '1H' | '5M' | '15M' | '4H';
  onWallHover?: (wall: any) => void;
  onWallClick?: (wall: any) => void;
}

export const GammaChartCanvasV4: React.FC<GammaChartCanvasV4Props> = ({
  symbols,
  settings,
  marketRegime,
  timeframe,
  onWallHover,
  onWallClick,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);

  // Generate synthetic candlestick data (production would fetch real data)
  const generateCandlestickData = (symbol: ParsedSymbolData, days: number = 30) => {
    const dates: string[] = [];
    const opens: number[] = [];
    const highs: number[] = [];
    const lows: number[] = [];
    const closes: number[] = [];

    const currentPrice = symbol.currentPrice;
    let price = currentPrice * 0.95;

    for (let i = 0; i < days; i++) {
      const date = new Date();
      date.setDate(date.getDate() - (days - i));
      dates.push(date.toISOString().split('T')[0]);

      const open = price;
      const volatility = (symbol.swingIV / 100) * 0.05;
      const change = (Math.random() - 0.5) * price * volatility;
      const close = price + change;

      const high = Math.max(open, close) * (1 + Math.random() * volatility * 0.5);
      const low = Math.min(open, close) * (1 - Math.random() * volatility * 0.5);

      opens.push(open);
      highs.push(high);
      lows.push(low);
      closes.push(close);

      price = close;
    }

    closes[closes.length - 1] = currentPrice;

    return { dates, opens, highs, lows, closes };
  };

  const chartData = useMemo(() => {
    const traces: Plotly.Data[] = [];
    const shapes: Partial<Plotly.Shape>[] = [];
    const annotations: Partial<Plotly.Annotations>[] = [];

    const filteredSymbols = symbols.filter(
      (s) => settings.selectedSymbols.length === 0 || settings.selectedSymbols.includes(s.symbol)
    );

    if (filteredSymbols.length === 0) return { traces: [], shapes: [], annotations: [] };

    const primarySymbol = filteredSymbols[0];
    const candleData = generateCandlestickData(primarySymbol);

    // 1. CANDLESTICK CHART
    traces.push({
      type: 'candlestick',
      x: candleData.dates,
      open: candleData.opens,
      high: candleData.highs,
      low: candleData.lows,
      close: candleData.closes,
      name: primarySymbol.displayName,
      increasing: {
        line: { color: THEME_COLORS.green, width: 1 },
        fillcolor: THEME_COLORS.green,
      },
      decreasing: {
        line: { color: THEME_COLORS.red, width: 1 },
        fillcolor: THEME_COLORS.red,
      },
      showlegend: false,
    });

    // 2. STANDARD DEVIATION BANDS (Background layer)
    if (settings.showSDBands) {
      const sdLevels = [
        { y: primarySymbol.sdBands.lower_2sd, label: '-2σ', opacity: SD_BANDS.opacity['2sd'] },
        { y: primarySymbol.sdBands.lower_1sd, label: '-1σ', opacity: SD_BANDS.opacity['1sd'] },
        { y: primarySymbol.sdBands.upper_1sd, label: '+1σ', opacity: SD_BANDS.opacity['1sd'] },
        { y: primarySymbol.sdBands.upper_2sd, label: '+2σ', opacity: SD_BANDS.opacity['2sd'] },
      ];

      sdLevels.forEach((level) => {
        shapes.push({
          type: 'line',
          xref: 'paper',
          yref: 'y',
          x0: 0,
          x1: 1,
          y0: level.y,
          y1: level.y,
          line: {
            color: SD_BANDS.color,
            width: 1,
            dash: 'dot',
          },
          opacity: level.opacity,
          layer: 'below',
        });
      });
    }

    // 3. GAMMA WALLS AS GRADIENT-FILLED RECTANGLES
    interface ProcessedWall {
      strike: number;
      strength: number;
      type: 'put' | 'call';
      timeframe: '14D' | '30D' | '90D';
      gex: number;
      zIndex: number;
    }

    const wallsToRender: ProcessedWall[] = [];

    primarySymbol.walls.forEach((wall) => {
      let adjustedStrength = wall.strength;
      if (settings.applyRegimeAdjustment) {
        adjustedStrength = applyRegimeAdjustment(wall.strength, marketRegime);
      }

      if (adjustedStrength < settings.minStrength) return;
      if (settings.hideWeakWalls && adjustedStrength < 40) return;

      const timeframeMap: Record<string, '14D' | '30D' | '90D'> = {
        swing: '14D',
        long: '30D',
        quarterly: '90D',
      };

      const mappedTimeframe = timeframeMap[wall.timeframe] || '14D';

      if (mappedTimeframe === '14D' && !settings.showSwingWalls) return;
      if (mappedTimeframe === '30D' && !settings.showLongWalls) return;
      if (mappedTimeframe === '90D' && !settings.showQuarterlyWalls) return;

      const zIndexMap = { '90D': 2, '30D': 3, '14D': 4 };

      wallsToRender.push({
        strike: wall.strike,
        strength: adjustedStrength,
        type: wall.type,
        timeframe: mappedTimeframe,
        gex: wall.gex,
        zIndex: zIndexMap[mappedTimeframe],
      });
    });

    // Sort by z-index (render quarterly first, swing last)
    wallsToRender.sort((a, b) => a.zIndex - b.zIndex);

    // Render walls as rounded rectangles with gradients
    wallsToRender.forEach((wall) => {
      const wallColors = getWallColors(wall.type, wall.strength);
      const opacity = getTimeframeOpacity(wall.timeframe, wall.strength);
      const borderWidth = getBorderWidth(wall.timeframe);

      // Calculate wall height based on strength (0.3% - 1.0% of price)
      const heightPercent = 0.003 + (wall.strength / 100) * 0.007;
      const wallHeight = primarySymbol.currentPrice * heightPercent;

      // Create gradient-filled zone using multiple scatter traces
      const numLayers = 7; // More layers = smoother gradient
      for (let i = 0; i < numLayers; i++) {
        const layerProgress = i / (numLayers - 1); // 0 to 1
        const layerHeight = wallHeight * (1 - layerProgress * 0.3); // Taper height

        // Gradient color interpolation
        let layerColor: string;
        if (layerProgress < 0.5) {
          // Start to mid
          const t = layerProgress * 2;
          layerColor = wall.strength > 70 ? wallColors.start : wallColors.mid;
        } else {
          // Mid to end
          const t = (layerProgress - 0.5) * 2;
          layerColor = wall.strength > 70 ? wallColors.mid : wallColors.end;
        }

        // Extract RGB and adjust alpha
        const match = layerColor.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
        if (match) {
          const [, r, g, b, a] = match;
          const baseAlpha = parseFloat(a || '1');
          const layerAlpha = baseAlpha * (1 - layerProgress * 0.5) * opacity;
          layerColor = `rgba(${r}, ${g}, ${b}, ${layerAlpha})`;
        }

        traces.push({
          type: 'scatter',
          mode: 'lines',
          fill: 'tozeroy',
          x: [candleData.dates[0], candleData.dates[candleData.dates.length - 1]],
          y: [wall.strike + layerHeight / 2, wall.strike + layerHeight / 2],
          fillcolor: layerColor,
          line: { width: 0 },
          showlegend: false,
          hoverinfo: 'skip',
        });
      }

      // Add border line
      traces.push({
        type: 'scatter',
        mode: 'lines',
        x: [candleData.dates[0], candleData.dates[candleData.dates.length - 1]],
        y: [wall.strike, wall.strike],
        line: {
          color: wallColors.border,
          width: borderWidth,
          dash: wall.timeframe === '90D' ? 'dash' : 'solid',
        },
        name: `${wall.timeframe} ${wall.type.toUpperCase()} $${wall.strike.toFixed(0)}`,
        showlegend: true, // Show in legend
        legendgroup: `${wall.timeframe}-${wall.type}`,
        hovertemplate:
          `<b>${primarySymbol.displayName}</b><br>` +
          `${wall.timeframe} ${wall.type.toUpperCase()} Wall<br>` +
          `Strike: ${formatPrice(wall.strike)}<br>` +
          `Strength: ${wall.strength.toFixed(0)}<br>` +
          `GEX: ${formatGEX(wall.gex)}<extra></extra>`,
      });

      // Add strike label on right axis for strong walls
      if (wall.strength > 60 && settings.showLabels) {
        annotations.push({
          x: 1,
          xref: 'paper',
          xanchor: 'left',
          y: wall.strike,
          yref: 'y',
          text: formatPrice(wall.strike),
          showarrow: false,
          font: {
            size: wall.strength > 80 ? 12 : 11,
            color: '#FFFFFF',
            family: 'Roboto, monospace',
            weight: 700,
          },
          bgcolor: wall.type === 'call' ? 'rgba(255, 56, 56, 0.9)' : 'rgba(0, 137, 123, 0.9)',
          bordercolor: wallColors.border,
          borderwidth: 2,
          borderpad: 4,
          opacity: 0.95,
        });
      }
    });

    // 4. CURRENT PRICE LINE
    const currentPrice = primarySymbol.currentPrice;
    traces.push({
      type: 'scatter',
      mode: 'lines+text',
      x: [candleData.dates[0], candleData.dates[candleData.dates.length - 1]],
      y: [currentPrice, currentPrice],
      line: {
        color: '#FFFFFF',
        width: 2,
        dash: 'solid',
      },
      name: 'Current Price',
      text: ['', formatPrice(currentPrice)],
      textposition: 'middle right',
      textfont: {
        color: '#FFFFFF',
        size: 13,
        family: 'Roboto, monospace',
        weight: 700,
      },
      showlegend: true,
      hovertemplate: `Current Price: ${formatPrice(currentPrice)}<extra></extra>`,
    });

    // 5. GAMMA FLIP LINE
    if (settings.showGammaFlip && primarySymbol.gammaFlip > 0) {
      traces.push({
        type: 'scatter',
        mode: 'lines+text',
        x: [candleData.dates[0], candleData.dates[candleData.dates.length - 1]],
        y: [primarySymbol.gammaFlip, primarySymbol.gammaFlip],
        line: {
          color: THEME_COLORS.orange,
          width: 2,
          dash: 'dash',
        },
        name: 'Gamma Flip',
        text: ['', `Flip: ${formatPrice(primarySymbol.gammaFlip)}`],
        textposition: 'middle right',
        textfont: {
          color: THEME_COLORS.orange,
          size: 12,
          family: 'Roboto, monospace',
          weight: 600,
        },
        showlegend: true,
        hovertemplate: `Gamma Flip: ${formatPrice(primarySymbol.gammaFlip)}<extra></extra>`,
      });
    }

    // 6. MAX PAIN INDICATOR (Top layer with glow)
    // Note: Max pain calculation would come from API/calculation
    // For demo, placing at a significant level
    const maxPainPrice = primarySymbol.currentPrice * 0.98; // Demo value

    shapes.push({
      type: 'line',
      xref: 'paper',
      yref: 'y',
      x0: 0,
      x1: 1,
      y0: maxPainPrice,
      y1: maxPainPrice,
      line: {
        color: MAX_PAIN.color,
        width: MAX_PAIN.width,
        dash: 'solid',
      },
      layer: 'above',
    });

    annotations.push({
      x: 0.5,
      xref: 'paper',
      xanchor: 'center',
      y: maxPainPrice,
      yref: 'y',
      yanchor: 'bottom',
      yshift: 8,
      text: `<b>MAX PAIN: ${formatPrice(maxPainPrice)}</b>`,
      showarrow: false,
      font: {
        size: 13,
        color: MAX_PAIN.labelText,
        family: 'Roboto, monospace',
        weight: 700,
      },
      bgcolor: MAX_PAIN.labelBg,
      bordercolor: MAX_PAIN.color,
      borderwidth: 2,
      borderpad: 6,
      opacity: 1.0,
    });

    return { traces, shapes, annotations };
  }, [symbols, settings, marketRegime, timeframe]);

  useEffect(() => {
    if (!chartRef.current || chartData.traces.length === 0) return;

    const layout: Partial<Plotly.Layout> = {
      title: undefined,
      xaxis: {
        title: undefined,
        type: 'date',
        gridcolor: THEME_COLORS.gridLine,
        color: THEME_COLORS.text,
        showgrid: true,
        zeroline: false,
        rangeslider: { visible: false },
      },
      yaxis: {
        title: undefined,
        gridcolor: THEME_COLORS.gridLine,
        color: THEME_COLORS.textBright,
        showgrid: true,
        zeroline: false,
        side: 'right',
        fixedrange: false,
      },
      plot_bgcolor: THEME_COLORS.background,
      paper_bgcolor: THEME_COLORS.background,
      font: {
        family: '"Roboto", "Open Sans", "Arial", sans-serif',
        color: THEME_COLORS.textBright,
        size: 11,
      },
      hovermode: 'x unified',
      showlegend: true,
      legend: {
        x: 0.01,
        y: 0.99,
        bgcolor: 'rgba(28, 33, 40, 0.90)',
        bordercolor: THEME_COLORS.border,
        borderwidth: 1,
        font: { size: 10, color: THEME_COLORS.textBright },
      },
      margin: { t: 8, b: 40, l: 8, r: 90 },
      dragmode: 'zoom',
      shapes: chartData.shapes,
      annotations: chartData.annotations,
    };

    const config: Partial<Plotly.Config> = {
      responsive: true,
      displayModeBar: true,
      modeBarButtonsToRemove: ['toImage', 'lasso2d', 'select2d', 'autoScale2d'],
      displaylogo: false,
      scrollZoom: true,
    };

    Plotly.newPlot(chartRef.current, chartData.traces, layout, config);

    return () => {
      if (chartRef.current) {
        Plotly.purge(chartRef.current);
      }
    };
  }, [chartData]);

  return (
    <div style={styles.container}>
      <div ref={chartRef} style={styles.chart} />
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: '100%',
    height: '100%',
    backgroundColor: THEME_COLORS.background,
  },
  chart: {
    width: '100%',
    height: '100%',
    minHeight: '700px',
  },
};
