/**
 * Gamma Chart Canvas v2.0 - TradingView-Inspired Design
 * Horizontal gamma bars with minimal visual noise
 */

import React, { useMemo, useEffect, useRef } from 'react';
import Plotly from 'plotly.js-basic-dist';
import { ParsedSymbolData, GammaScannerSettings } from './types';
import { applyRegimeAdjustment } from './dataParser';

interface GammaChartCanvasV2Props {
  symbols: ParsedSymbolData[];
  settings: GammaScannerSettings;
  marketRegime: string;
}

const TRADINGVIEW_COLORS = {
  background: '#131722',
  gridline: '#2A2E39',
  text: '#787B86',
  textBright: '#D1D4DC',
  gammaWall: '#2962FF', // TradingView blue
  gammaFlip: '#FFA726', // Bright orange for pivot
  currentPrice: '#FFFFFF', // Pure white
  sdBand: 'rgba(120, 123, 134, 0.1)', // Faint gray
};

export const GammaChartCanvasV2: React.FC<GammaChartCanvasV2Props> = ({
  symbols,
  settings,
  marketRegime,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);

  const chartData = useMemo(() => {
    const traces: Plotly.Data[] = [];

    // Filter symbols
    const filteredSymbols = symbols.filter(s =>
      settings.selectedSymbols.length === 0 || settings.selectedSymbols.includes(s.symbol)
    );

    if (filteredSymbols.length === 0) return [];

    // Use first symbol for detailed view (or allow selection)
    const primarySymbol = filteredSymbols[0];

    // Collect all wall data with adjusted strengths
    const wallBars: Array<{
      strike: number;
      strength: number;
      type: 'put' | 'call';
      timeframe: string;
      gex: number;
      dte: number;
    }> = [];

    primarySymbol.walls.forEach((wall) => {
      let adjustedStrength = wall.strength;
      if (settings.applyRegimeAdjustment) {
        adjustedStrength = applyRegimeAdjustment(wall.strength, marketRegime);
      }

      // Filter by settings
      if (adjustedStrength < settings.minStrength) return;
      if (settings.hideWeakWalls && adjustedStrength < 40) return;
      if (wall.timeframe === 'swing' && !settings.showSwingWalls) return;
      if (wall.timeframe === 'long' && !settings.showLongWalls) return;
      if (wall.timeframe === 'quarterly' && !settings.showQuarterlyWalls) return;

      wallBars.push({
        strike: wall.strike,
        strength: adjustedStrength,
        type: wall.type,
        timeframe: wall.timeframe,
        gex: wall.gex,
        dte: wall.dte,
      });
    });

    // Sort by strike price
    wallBars.sort((a, b) => b.strike - a.strike); // Top to bottom

    // Create horizontal bar chart for gamma walls
    const strikes = wallBars.map(w => w.strike);
    const strengths = wallBars.map(w => w.strength);
    const colors = wallBars.map(w => {
      const baseOpacity = (w.strength / 100) * settings.wallOpacity;
      return `rgba(41, 98, 255, ${baseOpacity})`; // Single blue color with varying opacity
    });

    const hoverTexts = wallBars.map((w) =>
      `${primarySymbol.displayName}<br>` +
      `${w.timeframe.toUpperCase()} ${w.type.toUpperCase()} Wall<br>` +
      `Strike: $${w.strike.toFixed(2)}<br>` +
      `Strength: ${w.strength.toFixed(1)}<br>` +
      `GEX: $${w.gex.toFixed(1)}M<br>` +
      `DTE: ${w.dte}d`
    );

    // Gamma walls as horizontal bars
    traces.push({
      type: 'bar',
      y: strikes,
      x: strengths,
      orientation: 'h',
      marker: {
        color: colors,
        line: { width: 0 },
      },
      hovertemplate: '%{text}<extra></extra>',
      text: hoverTexts,
      showlegend: false,
    });

    // Current price line (horizontal, bright white)
    traces.push({
      type: 'scatter',
      mode: 'lines+markers',
      y: [primarySymbol.currentPrice, primarySymbol.currentPrice],
      x: [0, 100],
      line: {
        color: TRADINGVIEW_COLORS.currentPrice,
        width: 2,
      },
      marker: {
        size: 8,
        color: TRADINGVIEW_COLORS.currentPrice,
        symbol: 'circle',
      },
      name: 'Current Price',
      hovertemplate: `${primarySymbol.displayName}<br>Price: $${primarySymbol.currentPrice.toFixed(2)}<extra></extra>`,
    });

    // Gamma flip line (horizontal, dashed, bright orange)
    if (settings.showGammaFlip && primarySymbol.gammaFlip > 0) {
      traces.push({
        type: 'scatter',
        mode: 'lines',
        y: [primarySymbol.gammaFlip, primarySymbol.gammaFlip],
        x: [0, 100],
        line: {
          color: TRADINGVIEW_COLORS.gammaFlip,
          width: 2,
          dash: 'dash',
        },
        name: 'Gamma Flip',
        hovertemplate: `Gamma Flip: $${primarySymbol.gammaFlip.toFixed(2)}<extra></extra>`,
      });
    }

    // Add SD bands as shaded horizontal regions (background)
    if (settings.showSDBands) {
      const sdBands = [
        { y: primarySymbol.sdBands.lower_2sd, name: '-2σ' },
        { y: primarySymbol.sdBands.lower_1_5sd, name: '-1.5σ' },
        { y: primarySymbol.sdBands.lower_1sd, name: '-1σ' },
        { y: primarySymbol.sdBands.upper_1sd, name: '+1σ' },
        { y: primarySymbol.sdBands.upper_1_5sd, name: '+1.5σ' },
        { y: primarySymbol.sdBands.upper_2sd, name: '+2σ' },
      ];

      sdBands.forEach((band) => {
        traces.push({
          type: 'scatter',
          mode: 'lines',
          y: [band.y, band.y],
          x: [0, 100],
          line: {
            color: TRADINGVIEW_COLORS.sdBand.replace('0.1', '0.3'),
            width: 1,
            dash: 'dot',
          },
          name: band.name,
          showlegend: false,
          hovertemplate: `${band.name}: $${band.y.toFixed(2)}<extra></extra>`,
        });
      });
    }

    return traces;
  }, [symbols, settings, marketRegime]);

  useEffect(() => {
    if (!chartRef.current || chartData.length === 0) return;

    const layout: Partial<Plotly.Layout> = {
      title: undefined, // No title, use top bar instead
      xaxis: {
        title: 'Wall Strength',
        gridcolor: TRADINGVIEW_COLORS.gridline,
        color: TRADINGVIEW_COLORS.text,
        showgrid: true,
        zeroline: false,
        range: [0, 100],
      },
      yaxis: {
        title: 'Price ($)',
        gridcolor: TRADINGVIEW_COLORS.gridline,
        color: TRADINGVIEW_COLORS.textBright,
        showgrid: true,
        zeroline: false,
        autorange: true,
      },
      plot_bgcolor: TRADINGVIEW_COLORS.background,
      paper_bgcolor: TRADINGVIEW_COLORS.background,
      font: {
        family: '"Roboto", "Open Sans", "Arial", sans-serif',
        color: TRADINGVIEW_COLORS.textBright,
        size: 12,
      },
      hovermode: 'closest',
      showlegend: true,
      legend: {
        x: 1.02,
        y: 1,
        bgcolor: 'rgba(30, 34, 45, 0.9)',
        bordercolor: TRADINGVIEW_COLORS.gridline,
        borderwidth: 1,
        font: { size: 11, color: TRADINGVIEW_COLORS.textBright },
      },
      margin: { t: 20, b: 60, l: 80, r: 150 },
    };

    const config: Partial<Plotly.Config> = {
      responsive: true,
      displayModeBar: true,
      modeBarButtonsToRemove: ['toImage', 'lasso2d', 'select2d'],
      displaylogo: false,
      modeBarButtonsToAdd: [
        {
          name: 'Reset',
          icon: Plotly.Icons.home,
          click: function (gd: any) {
            Plotly.relayout(gd, {
              'xaxis.autorange': true,
              'yaxis.autorange': true,
            });
          },
        },
      ],
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
      {/* Integrated Symbol Metrics Table */}
      {settings.showTable && symbols.length > 0 && (
        <div style={styles.metricsTable}>
          <SymbolMetricsTable symbols={symbols} />
        </div>
      )}
    </div>
  );
};

// Integrated Symbol Metrics Table Component
const SymbolMetricsTable: React.FC<{ symbols: ParsedSymbolData[] }> = ({ symbols }) => {
  return (
    <div style={tableStyles.container}>
      <div style={tableStyles.header}>Symbol Metrics</div>
      <table style={tableStyles.table}>
        <thead>
          <tr style={tableStyles.headerRow}>
            <th style={tableStyles.th}>Symbol</th>
            <th style={tableStyles.th}>Price</th>
            <th style={tableStyles.th}>Gamma Flip</th>
            <th style={tableStyles.th}>Dist %</th>
            <th style={tableStyles.th}>Swing IV</th>
            <th style={tableStyles.th}>Strongest Wall</th>
          </tr>
        </thead>
        <tbody>
          {symbols.map((symbol, idx) => {
            const distToFlip = ((symbol.gammaFlip - symbol.currentPrice) / symbol.currentPrice) * 100;
            const strongestWall = symbol.walls.reduce(
              (max, w) => (w.strength > max.strength ? w : max),
              symbol.walls[0] || { strength: 0, strike: 0, type: 'put' as const }
            );

            return (
              <tr
                key={symbol.symbol}
                style={{
                  ...tableStyles.row,
                  backgroundColor: idx % 2 === 0 ? '#1E222D' : '#131722',
                }}
              >
                <td style={tableStyles.td}>{symbol.displayName}</td>
                <td style={tableStyles.tdNumber}>${symbol.currentPrice.toFixed(2)}</td>
                <td style={{ ...tableStyles.tdNumber, fontWeight: 600 }}>
                  ${symbol.gammaFlip.toFixed(2)}
                </td>
                <td
                  style={{
                    ...tableStyles.tdNumber,
                    color: distToFlip > 0 ? '#00C853' : '#FF5252',
                  }}
                >
                  {distToFlip > 0 ? '+' : ''}
                  {distToFlip.toFixed(2)}%
                </td>
                <td style={tableStyles.tdNumber}>{symbol.swingIV.toFixed(1)}%</td>
                <td style={{ ...tableStyles.td, fontWeight: 600 }}>
                  ${strongestWall.strike.toFixed(0)} {strongestWall.type.toUpperCase()} (
                  {strongestWall.strength.toFixed(0)})
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: '100%',
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: TRADINGVIEW_COLORS.background,
  },
  chart: {
    width: '100%',
    flex: 1,
    minHeight: '600px',
  },
  metricsTable: {
    width: '100%',
    borderTop: `1px solid ${TRADINGVIEW_COLORS.gridline}`,
  },
};

const tableStyles: Record<string, React.CSSProperties> = {
  container: {
    width: '100%',
    backgroundColor: '#1E222D',
  },
  header: {
    padding: '12px 16px',
    fontSize: '14px',
    fontWeight: 600,
    color: '#FFFFFF',
    borderBottom: `1px solid ${TRADINGVIEW_COLORS.gridline}`,
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '13px',
  },
  headerRow: {
    backgroundColor: '#131722',
  },
  th: {
    padding: '10px 12px',
    textAlign: 'left',
    color: TRADINGVIEW_COLORS.text,
    fontWeight: 500,
    borderBottom: `1px solid ${TRADINGVIEW_COLORS.gridline}`,
    fontSize: '12px',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  row: {
    transition: 'background-color 0.2s',
  },
  td: {
    padding: '10px 12px',
    color: TRADINGVIEW_COLORS.textBright,
    borderBottom: `1px solid ${TRADINGVIEW_COLORS.gridline}`,
  },
  tdNumber: {
    padding: '10px 12px',
    color: TRADINGVIEW_COLORS.textBright,
    textAlign: 'right',
    fontFamily: 'monospace',
    borderBottom: `1px solid ${TRADINGVIEW_COLORS.gridline}`,
  },
};
