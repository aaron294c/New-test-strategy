/**
 * Gamma Chart Canvas v3.0 - Full TradingView Integration
 * Candlestick price action + Gamma walls as support/resistance overlays
 */

import React, { useMemo, useEffect, useRef, useState } from 'react';
import Plotly from 'plotly.js-basic-dist';
import { ParsedSymbolData, GammaScannerSettings } from './types';
import { applyRegimeAdjustment } from './dataParser';

interface GammaChartCanvasV3Props {
  symbols: ParsedSymbolData[];
  settings: GammaScannerSettings;
  marketRegime: string;
  timeframe: '1D' | '1H' | '5M' | '15M' | '4H';
}

const TRADINGVIEW_COLORS = {
  background: '#131722',
  gridline: '#2A2E39',
  text: '#787B86',
  textBright: '#D1D4DC',
  candleUp: '#26A69A', // Green
  candleDown: '#EF5350', // Red
  putWall: 'rgba(38, 166, 154, 0.25)', // Light green (support)
  callWall: 'rgba(239, 83, 80, 0.25)', // Light red (resistance)
  gammaFlip: '#FFA726', // Bright orange
  currentPrice: '#FFFFFF', // Pure white
  sdBand: 'rgba(120, 123, 134, 0.08)',
};

export const GammaChartCanvasV3: React.FC<GammaChartCanvasV3Props> = ({
  symbols,
  settings,
  marketRegime,
  timeframe,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const [priceData, setPriceData] = useState<any>(null);

  // Generate synthetic candlestick data for demonstration
  // In production, this would fetch real historical price data
  const generateCandlestickData = (symbol: ParsedSymbolData, days: number = 30) => {
    const dates: string[] = [];
    const opens: number[] = [];
    const highs: number[] = [];
    const lows: number[] = [];
    const closes: number[] = [];

    const currentPrice = symbol.currentPrice;
    let price = currentPrice * 0.95; // Start 5% below current

    for (let i = 0; i < days; i++) {
      const date = new Date();
      date.setDate(date.getDate() - (days - i));
      dates.push(date.toISOString().split('T')[0]);

      const open = price;
      const volatility = (symbol.swingIV / 100) * 0.05; // Daily vol
      const change = (Math.random() - 0.5) * price * volatility;
      const close = price + change;

      const high = Math.max(open, close) * (1 + Math.random() * volatility * 0.5);
      const low = Math.min(open, close) * (1 - Math.random() * volatility * 0.5);

      opens.push(open);
      highs.push(high);
      lows.push(low);
      closes.push(close);

      price = close; // Next candle starts where this one ended
    }

    // Ensure last close is near current price
    closes[closes.length - 1] = currentPrice;

    return { dates, opens, highs, lows, closes };
  };

  const chartData = useMemo(() => {
    const traces: Plotly.Data[] = [];

    const filteredSymbols = symbols.filter(
      (s) => settings.selectedSymbols.length === 0 || settings.selectedSymbols.includes(s.symbol)
    );

    if (filteredSymbols.length === 0) return [];

    const primarySymbol = filteredSymbols[0];

    // Generate candlestick data
    const candleData = generateCandlestickData(primarySymbol);

    // 1. CANDLESTICK CHART (Base Layer)
    traces.push({
      type: 'candlestick',
      x: candleData.dates,
      open: candleData.opens,
      high: candleData.highs,
      low: candleData.lows,
      close: candleData.closes,
      name: primarySymbol.displayName,
      increasing: {
        line: { color: TRADINGVIEW_COLORS.candleUp, width: 1 },
        fillcolor: TRADINGVIEW_COLORS.candleUp,
      },
      decreasing: {
        line: { color: TRADINGVIEW_COLORS.candleDown, width: 1 },
        fillcolor: TRADINGVIEW_COLORS.candleDown,
      },
      showlegend: false,
    });

    // 2. GAMMA WALLS AS SUPPORT/RESISTANCE ZONES
    const wallZones: Array<{
      strike: number;
      strength: number;
      type: 'put' | 'call';
      timeframe: string;
      gex: number;
    }> = [];

    primarySymbol.walls.forEach((wall) => {
      let adjustedStrength = wall.strength;
      if (settings.applyRegimeAdjustment) {
        adjustedStrength = applyRegimeAdjustment(wall.strength, marketRegime);
      }

      if (adjustedStrength < settings.minStrength) return;
      if (settings.hideWeakWalls && adjustedStrength < 40) return;
      if (wall.timeframe === 'swing' && !settings.showSwingWalls) return;
      if (wall.timeframe === 'long' && !settings.showLongWalls) return;
      if (wall.timeframe === 'quarterly' && !settings.showQuarterlyWalls) return;

      wallZones.push({
        strike: wall.strike,
        strength: adjustedStrength,
        type: wall.type,
        timeframe: wall.timeframe,
        gex: wall.gex,
      });
    });

    // Sort by strike for better visual layering
    wallZones.sort((a, b) => a.strike - b.strike);

    // Draw gamma walls as horizontal support/resistance zones
    wallZones.forEach((wall) => {
      const opacity = (wall.strength / 100) * settings.wallOpacity * 0.5;
      const lineWidth = 1 + (wall.strength / 100) * 2; // 1-3px based on strength

      const color = wall.type === 'put' ? TRADINGVIEW_COLORS.putWall : TRADINGVIEW_COLORS.callWall;
      const lineColor =
        wall.type === 'put'
          ? `rgba(38, 166, 154, ${opacity * 2})`
          : `rgba(239, 83, 80, ${opacity * 2})`;

      // Horizontal line for the wall
      traces.push({
        type: 'scatter',
        mode: 'lines',
        x: [candleData.dates[0], candleData.dates[candleData.dates.length - 1]],
        y: [wall.strike, wall.strike],
        line: {
          color: lineColor,
          width: lineWidth,
          dash: wall.timeframe === 'quarterly' ? 'dot' : 'solid',
        },
        name: `${wall.timeframe.toUpperCase()} ${wall.type.toUpperCase()} $${wall.strike.toFixed(0)}`,
        showlegend: true,
        legendgroup: wall.type,
        hovertemplate:
          `<b>${primarySymbol.displayName}</b><br>` +
          `${wall.timeframe.toUpperCase()} ${wall.type.toUpperCase()} Wall<br>` +
          `Strike: $${wall.strike.toFixed(2)}<br>` +
          `Strength: ${wall.strength.toFixed(1)}<br>` +
          `GEX: $${wall.gex.toFixed(1)}M<extra></extra>`,
      });

      // Optional: Add shaded zone around strong walls
      if (wall.strength > 70 && settings.showLabels) {
        const zoneHeight = primarySymbol.currentPrice * 0.01; // 1% zone
        traces.push({
          type: 'scatter',
          mode: 'none',
          x: [
            candleData.dates[0],
            candleData.dates[candleData.dates.length - 1],
            candleData.dates[candleData.dates.length - 1],
            candleData.dates[0],
          ],
          y: [
            wall.strike - zoneHeight,
            wall.strike - zoneHeight,
            wall.strike + zoneHeight,
            wall.strike + zoneHeight,
          ],
          fill: 'toself',
          fillcolor: color,
          showlegend: false,
          hoverinfo: 'skip',
        });
      }
    });

    // 3. CURRENT PRICE LINE (Most Recent Close)
    const currentPrice = primarySymbol.currentPrice;
    traces.push({
      type: 'scatter',
      mode: 'lines+text',
      x: [candleData.dates[0], candleData.dates[candleData.dates.length - 1]],
      y: [currentPrice, currentPrice],
      line: {
        color: TRADINGVIEW_COLORS.currentPrice,
        width: 2,
        dash: 'solid',
      },
      name: 'Current Price',
      text: [``, `$${currentPrice.toFixed(2)}`],
      textposition: 'middle right',
      textfont: {
        color: TRADINGVIEW_COLORS.currentPrice,
        size: 12,
        family: 'Roboto, sans-serif',
      },
      showlegend: true,
      hovertemplate: `Current Price: $${currentPrice.toFixed(2)}<extra></extra>`,
    });

    // 4. GAMMA FLIP LINE (Critical Pivot)
    if (settings.showGammaFlip && primarySymbol.gammaFlip > 0) {
      traces.push({
        type: 'scatter',
        mode: 'lines+text',
        x: [candleData.dates[0], candleData.dates[candleData.dates.length - 1]],
        y: [primarySymbol.gammaFlip, primarySymbol.gammaFlip],
        line: {
          color: TRADINGVIEW_COLORS.gammaFlip,
          width: 2,
          dash: 'dash',
        },
        name: 'Gamma Flip',
        text: [``, `Flip: $${primarySymbol.gammaFlip.toFixed(2)}`],
        textposition: 'middle right',
        textfont: {
          color: TRADINGVIEW_COLORS.gammaFlip,
          size: 11,
          family: 'Roboto, sans-serif',
        },
        showlegend: true,
        hovertemplate: `Gamma Flip: $${primarySymbol.gammaFlip.toFixed(2)}<extra></extra>`,
      });
    }

    // 5. STANDARD DEVIATION BANDS (Background Context)
    if (settings.showSDBands) {
      const sdLevels = [
        { y: primarySymbol.sdBands.lower_2sd, label: '-2σ', opacity: 0.15 },
        { y: primarySymbol.sdBands.lower_1sd, label: '-1σ', opacity: 0.25 },
        { y: primarySymbol.sdBands.upper_1sd, label: '+1σ', opacity: 0.25 },
        { y: primarySymbol.sdBands.upper_2sd, label: '+2σ', opacity: 0.15 },
      ];

      sdLevels.forEach((level) => {
        traces.push({
          type: 'scatter',
          mode: 'lines',
          x: [candleData.dates[0], candleData.dates[candleData.dates.length - 1]],
          y: [level.y, level.y],
          line: {
            color: `rgba(120, 123, 134, ${level.opacity})`,
            width: 1,
            dash: 'dot',
          },
          name: level.label,
          showlegend: false,
          hovertemplate: `${level.label}: $${level.y.toFixed(2)}<extra></extra>`,
        });
      });
    }

    return traces;
  }, [symbols, settings, marketRegime, timeframe]);

  useEffect(() => {
    if (!chartRef.current || chartData.length === 0) return;

    const layout: Partial<Plotly.Layout> = {
      title: undefined,
      xaxis: {
        title: undefined,
        type: 'date',
        gridcolor: TRADINGVIEW_COLORS.gridline,
        color: TRADINGVIEW_COLORS.text,
        showgrid: true,
        zeroline: false,
        rangeslider: { visible: false }, // TradingView doesn't show rangeslider
      },
      yaxis: {
        title: undefined,
        gridcolor: TRADINGVIEW_COLORS.gridline,
        color: TRADINGVIEW_COLORS.textBright,
        showgrid: true,
        zeroline: false,
        side: 'right', // Price axis on right like TradingView
        fixedrange: false,
      },
      plot_bgcolor: TRADINGVIEW_COLORS.background,
      paper_bgcolor: TRADINGVIEW_COLORS.background,
      font: {
        family: '"Roboto", "Open Sans", "Arial", sans-serif',
        color: TRADINGVIEW_COLORS.textBright,
        size: 11,
      },
      hovermode: 'x unified',
      showlegend: true,
      legend: {
        x: 0.01,
        y: 0.99,
        bgcolor: 'rgba(30, 34, 45, 0.85)',
        bordercolor: TRADINGVIEW_COLORS.gridline,
        borderwidth: 1,
        font: { size: 10, color: TRADINGVIEW_COLORS.textBright },
        orientation: 'v',
      },
      margin: { t: 10, b: 40, l: 10, r: 80 },
      dragmode: 'zoom',
    };

    const config: Partial<Plotly.Config> = {
      responsive: true,
      displayModeBar: true,
      modeBarButtonsToRemove: ['toImage', 'lasso2d', 'select2d', 'autoScale2d'],
      displaylogo: false,
      scrollZoom: true,
    };

    Plotly.newPlot(chartRef.current, chartData, layout, config);

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
    backgroundColor: TRADINGVIEW_COLORS.background,
  },
  chart: {
    width: '100%',
    height: '100%',
    minHeight: '700px',
  },
};
