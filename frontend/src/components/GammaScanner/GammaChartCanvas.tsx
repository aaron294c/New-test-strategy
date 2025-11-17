/**
 * Gamma Chart Canvas Component
 * Visualizes gamma walls, zones, and price data using Plotly
 */

import React, { useMemo, useEffect, useRef } from 'react';
import Plotly from 'plotly.js-basic-dist';
import { ParsedSymbolData, GammaScannerSettings, COLOR_SCHEMES } from './types';
import { applyRegimeAdjustment } from './dataParser';

interface GammaChartCanvasProps {
  symbols: ParsedSymbolData[];
  settings: GammaScannerSettings;
  marketRegime: string;
}

export const GammaChartCanvas: React.FC<GammaChartCanvasProps> = ({
  symbols,
  settings,
  marketRegime,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);

  const chartData = useMemo(() => {
    const traces: Plotly.Data[] = [];
    const colors = COLOR_SCHEMES[settings.colorScheme];

    // Filter symbols based on selection
    const filteredSymbols = symbols.filter(s =>
      settings.selectedSymbols.length === 0 || settings.selectedSymbols.includes(s.symbol)
    );

    filteredSymbols.forEach((symbolData, symbolIndex) => {
      const baseY = symbolIndex * 2; // Vertical offset for each symbol

      // Add current price line
      traces.push({
        type: 'scatter',
        mode: 'lines+markers',
        name: `${symbolData.displayName} Price`,
        x: [0, 30], // Extend to 30 days
        y: [symbolData.currentPrice, symbolData.currentPrice],
        line: { color: '#FFFFFF', width: 2, dash: 'dot' },
        marker: { size: 6, color: '#FFFFFF' },
        showlegend: true,
        hovertemplate: `${symbolData.displayName}<br>Price: $%{y:.2f}<extra></extra>`,
      });

      // Add gamma walls
      symbolData.walls.forEach((wall) => {
        // Apply regime adjustment if enabled
        let adjustedStrength = wall.strength;
        if (settings.applyRegimeAdjustment) {
          adjustedStrength = applyRegimeAdjustment(wall.strength, marketRegime);
        }

        // Filter by strength
        if (adjustedStrength < settings.minStrength) {
          return;
        }

        if (settings.hideWeakWalls && adjustedStrength < 40) {
          return;
        }

        // Filter by timeframe
        if (wall.timeframe === 'swing' && !settings.showSwingWalls) return;
        if (wall.timeframe === 'long' && !settings.showLongWalls) return;
        if (wall.timeframe === 'quarterly' && !settings.showQuarterlyWalls) return;

        // Determine color
        let wallColor: string;
        if (wall.timeframe === 'swing') {
          wallColor = wall.type === 'put' ? colors.swingPut : colors.swingCall;
        } else if (wall.timeframe === 'long') {
          wallColor = wall.type === 'put' ? colors.longPut : colors.longCall;
        } else {
          wallColor = wall.type === 'put' ? colors.quarterlyPut : colors.quarterlyCall;
        }

        // Calculate opacity based on strength
        const opacity = settings.wallOpacity * (adjustedStrength / 100);

        // Add wall line
        traces.push({
          type: 'scatter',
          mode: 'lines',
          name: `${symbolData.displayName} ${wall.timeframe} ${wall.type} wall`,
          x: [0, wall.dte], // Extend to DTE
          y: [wall.strike, wall.strike],
          line: {
            color: wallColor,
            width: 3 + (adjustedStrength / 50), // Thicker for stronger walls
          },
          opacity,
          showlegend: false,
          hovertemplate: `${symbolData.displayName}<br>` +
            `${wall.timeframe} ${wall.type} wall<br>` +
            `Strike: $%{y:.2f}<br>` +
            `Strength: ${adjustedStrength.toFixed(1)}<br>` +
            `GEX: $${wall.gex.toFixed(1)}M<br>` +
            `DTE: ${wall.dte}d<extra></extra>`,
        });

        // Add wall zone (filled area)
        if (settings.showLabels) {
          const zoneHeight = symbolData.currentPrice * 0.02; // 2% zone height
          traces.push({
            type: 'scatter',
            mode: 'none',
            name: `${wall.timeframe} ${wall.type} zone`,
            x: [0, wall.dte, wall.dte, 0],
            y: [
              wall.strike - zoneHeight,
              wall.strike - zoneHeight,
              wall.strike + zoneHeight,
              wall.strike + zoneHeight,
            ],
            fill: 'toself',
            fillcolor: wallColor,
            opacity: opacity * 0.3,
            showlegend: false,
            hoverinfo: 'skip',
          });
        }
      });

      // Add gamma flip line
      if (settings.showGammaFlip && symbolData.gammaFlip > 0) {
        traces.push({
          type: 'scatter',
          mode: 'lines',
          name: `${symbolData.displayName} Gamma Flip`,
          x: [0, 30],
          y: [symbolData.gammaFlip, symbolData.gammaFlip],
          line: {
            color: colors.gammaFlip,
            width: 2,
            dash: 'dashdot',
          },
          showlegend: true,
          hovertemplate: `${symbolData.displayName}<br>Gamma Flip: $%{y:.2f}<extra></extra>`,
        });
      }

      // Add standard deviation bands
      if (settings.showSDBands) {
        const sdBands = [
          { lower: symbolData.sdBands.lower_1sd, upper: symbolData.sdBands.upper_1sd, name: '±1σ' },
          { lower: symbolData.sdBands.lower_1_5sd, upper: symbolData.sdBands.upper_1_5sd, name: '±1.5σ' },
          { lower: symbolData.sdBands.lower_2sd, upper: symbolData.sdBands.upper_2sd, name: '±2σ' },
        ];

        sdBands.forEach((band, idx) => {
          const opacity = 0.2 - idx * 0.05;

          // Upper band
          traces.push({
            type: 'scatter',
            mode: 'lines',
            name: `${symbolData.displayName} ${band.name} upper`,
            x: [0, 30],
            y: [band.upper, band.upper],
            line: {
              color: colors.sdBands,
              width: 1,
              dash: 'dash',
            },
            opacity,
            showlegend: idx === 0,
            hovertemplate: `${symbolData.displayName}<br>${band.name} Upper: $%{y:.2f}<extra></extra>`,
          });

          // Lower band
          traces.push({
            type: 'scatter',
            mode: 'lines',
            name: `${symbolData.displayName} ${band.name} lower`,
            x: [0, 30],
            y: [band.lower, band.lower],
            line: {
              color: colors.sdBands,
              width: 1,
              dash: 'dash',
            },
            opacity,
            showlegend: false,
            hovertemplate: `${symbolData.displayName}<br>${band.name} Lower: $%{y:.2f}<extra></extra>`,
          });
        });
      }
    });

    return traces;
  }, [symbols, settings, marketRegime]);

  useEffect(() => {
    if (!chartRef.current || chartData.length === 0) return;

    const layout: Partial<Plotly.Layout> = {
      title: {
        text: 'Gamma Wall Scanner',
        font: { size: 20, color: '#FFFFFF' },
      },
      xaxis: {
        title: 'Days',
        gridcolor: '#333333',
        color: '#CCCCCC',
      },
      yaxis: {
        title: 'Price ($)',
        gridcolor: '#333333',
        color: '#CCCCCC',
      },
      plot_bgcolor: '#1a1a1a',
      paper_bgcolor: '#0d0d0d',
      font: { color: '#CCCCCC' },
      hovermode: 'closest',
      showlegend: true,
      legend: {
        x: 1.05,
        y: 1,
        bgcolor: '#0d0d0d',
        bordercolor: '#333333',
        borderwidth: 1,
      },
      margin: { t: 60, b: 60, l: 80, r: 200 },
    };

    const config: Partial<Plotly.Config> = {
      responsive: true,
      displayModeBar: true,
      modeBarButtonsToRemove: ['toImage'],
      displaylogo: false,
    };

    Plotly.newPlot(chartRef.current, chartData, layout, config);

    return () => {
      if (chartRef.current) {
        Plotly.purge(chartRef.current);
      }
    };
  }, [chartData]);

  return (
    <div className="gamma-chart-canvas" style={{ width: '100%', height: '600px' }}>
      <div ref={chartRef} style={{ width: '100%', height: '100%' }} />
    </div>
  );
};
