/**
 * RSI Percentile Chart Component
 * Displays RSI, RSI-MA with percentile coloring, and percentile threshold lines
 * Inspired by the TradingView MOST RSI with Percentile Ranking indicator
 */

import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import { Paper, Typography, Box, Chip, CircularProgress } from '@mui/material';
import type { RSIChartData } from '@/types';

interface RSIPercentileChartProps {
  data: RSIChartData | null;
  ticker: string;
  isLoading?: boolean;
}

// Helper function to get color based on percentile rank
const getColorForPercentile = (percentile: number): string => {
  if (percentile >= 95) return 'rgb(255, 0, 0)';       // Red
  if (percentile >= 85) return 'rgb(255, 165, 0)';     // Orange
  if (percentile >= 75) return 'rgb(255, 255, 0)';     // Yellow
  if (percentile >= 25) return 'rgb(255, 255, 255)';   // White
  if (percentile >= 15) return 'rgb(0, 0, 255)';       // Blue
  if (percentile >= 5) return 'rgb(0, 255, 0)';        // Lime
  return 'rgb(0, 200, 0)';                             // Green
};

// Helper function to create colored line segments for RSI-MA
const createColoredLineSegments = (
  dates: string[],
  values: number[],
  percentiles: number[]
) => {
  const segments: any[] = [];
  
  for (let i = 0; i < dates.length - 1; i++) {
    const color = getColorForPercentile(percentiles[i]);
    segments.push({
      x: [dates[i], dates[i + 1]],
      y: [values[i], values[i + 1]],
      mode: 'lines',
      name: i === 0 ? 'RSI-MA' : '',
      showlegend: i === 0,
      line: {
        color: color,
        width: 2,
      },
      hovertemplate: `<b>Date:</b> %{x}<br><b>RSI-MA:</b> %{y:.2f}<br><b>Percentile:</b> ${percentiles[i].toFixed(1)}%<extra></extra>`,
      type: 'scatter',
    });
  }
  
  return segments;
};

const RSIPercentileChart: React.FC<RSIPercentileChartProps> = ({ data, ticker, isLoading }) => {
  const plotData = useMemo(() => {
    if (!data) return [];

    const { dates, rsi, rsi_ma, percentile_rank, percentile_thresholds } = data;

    const traces: any[] = [
      // RSI Background Fill (30-70 bands)
      {
        x: dates,
        y: Array(dates.length).fill(70),
        fill: 'tonexty',
        fillcolor: 'rgba(126, 87, 194, 0.1)',
        line: { width: 0 },
        showlegend: false,
        hoverinfo: 'skip',
        type: 'scatter',
      },
      {
        x: dates,
        y: Array(dates.length).fill(30),
        fill: 'tonexty',
        fillcolor: 'rgba(126, 87, 194, 0.1)',
        line: { width: 0 },
        showlegend: false,
        hoverinfo: 'skip',
        type: 'scatter',
      },
      // RSI line (purple)
      {
        x: dates,
        y: rsi,
        mode: 'lines',
        name: 'RSI',
        line: {
          color: 'rgb(126, 87, 194)',
          width: 1.5,
        },
        hovertemplate: '<b>Date:</b> %{x}<br><b>RSI:</b> %{y:.2f}<extra></extra>',
        type: 'scatter',
      },
      // RSI-MA line (color-coded by percentile)
      // Since Plotly doesn't support per-point line colors easily, we'll use segments
      ...createColoredLineSegments(dates, rsi_ma, percentile_rank),
      // Percentile threshold lines
      {
        x: [dates[0], dates[dates.length - 1]],
        y: [percentile_thresholds.p50, percentile_thresholds.p50],
        mode: 'lines',
        name: '50th Percentile',
        line: {
          color: 'rgba(128, 128, 128, 0.7)',
          width: 2,
          dash: 'solid',
        },
        hovertemplate: '<b>50th Percentile:</b> %{y:.2f}<extra></extra>',
        type: 'scatter',
      },
      {
        x: [dates[0], dates[dates.length - 1]],
        y: [percentile_thresholds.p95, percentile_thresholds.p95],
        mode: 'lines',
        name: '95th Percentile',
        line: {
          color: 'rgba(255, 0, 0, 0.5)',
          width: 1,
          dash: 'dash',
        },
        hovertemplate: '<b>95th Percentile:</b> %{y:.2f}<extra></extra>',
        type: 'scatter',
      },
      {
        x: [dates[0], dates[dates.length - 1]],
        y: [percentile_thresholds.p85, percentile_thresholds.p85],
        mode: 'lines',
        name: '85th Percentile',
        line: {
          color: 'rgba(255, 165, 0, 0.5)',
          width: 1,
          dash: 'dash',
        },
        hovertemplate: '<b>85th Percentile:</b> %{y:.2f}<extra></extra>',
        type: 'scatter',
      },
      {
        x: [dates[0], dates[dates.length - 1]],
        y: [percentile_thresholds.p75, percentile_thresholds.p75],
        mode: 'lines',
        name: '75th Percentile',
        line: {
          color: 'rgba(255, 255, 0, 0.5)',
          width: 1,
          dash: 'dash',
        },
        hovertemplate: '<b>75th Percentile:</b> %{y:.2f}<extra></extra>',
        type: 'scatter',
      },
      {
        x: [dates[0], dates[dates.length - 1]],
        y: [percentile_thresholds.p25, percentile_thresholds.p25],
        mode: 'lines',
        name: '25th Percentile',
        line: {
          color: 'rgba(0, 0, 255, 0.5)',
          width: 1,
          dash: 'dash',
        },
        hovertemplate: '<b>25th Percentile:</b> %{y:.2f}<extra></extra>',
        type: 'scatter',
      },
      {
        x: [dates[0], dates[dates.length - 1]],
        y: [percentile_thresholds.p15, percentile_thresholds.p15],
        mode: 'lines',
        name: '15th Percentile',
        line: {
          color: 'rgba(0, 255, 0, 0.5)',
          width: 1,
          dash: 'dash',
        },
        hovertemplate: '<b>15th Percentile:</b> %{y:.2f}<extra></extra>',
        type: 'scatter',
      },
      {
        x: [dates[0], dates[dates.length - 1]],
        y: [percentile_thresholds.p5, percentile_thresholds.p5],
        mode: 'lines',
        name: '5th Percentile',
        line: {
          color: 'rgba(0, 200, 0, 0.5)',
          width: 1,
          dash: 'dash',
        },
        hovertemplate: '<b>5th Percentile:</b> %{y:.2f}<extra></extra>',
        type: 'scatter',
      },
      // Standard RSI levels
      {
        x: [dates[0], dates[dates.length - 1]],
        y: [70, 70],
        mode: 'lines',
        name: 'RSI Overbought (70)',
        line: {
          color: 'rgba(120, 123, 134, 0.5)',
          width: 1,
        },
        hoverinfo: 'skip',
        type: 'scatter',
      },
      {
        x: [dates[0], dates[dates.length - 1]],
        y: [30, 30],
        mode: 'lines',
        name: 'RSI Oversold (30)',
        line: {
          color: 'rgba(120, 123, 134, 0.5)',
          width: 1,
        },
        hoverinfo: 'skip',
        type: 'scatter',
      },
    ];

    return traces;
  }, [data]);

  const getPercentileLabel = (percentile: number): { text: string; color: string } => {
    if (percentile >= 95) return { text: 'Extreme High (>95%)', color: '#f44336' };
    if (percentile >= 85) return { text: 'Very High (85-95%)', color: '#ff9800' };
    if (percentile >= 75) return { text: 'High (75-85%)', color: '#ffeb3b' };
    if (percentile >= 25) return { text: 'Normal (25-75%)', color: '#9e9e9e' };
    if (percentile >= 15) return { text: 'Low (15-25%)', color: '#2196f3' };
    if (percentile >= 5) return { text: 'Very Low (5-15%)', color: '#8bc34a' };
    return { text: 'Extreme Low (<5%)', color: '#4caf50' };
  };

  if (isLoading) {
    return (
      <Paper sx={{ p: 3, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Paper>
    );
  }

  if (!data) {
    return (
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1" color="text.secondary">
          No chart data available
        </Typography>
      </Paper>
    );
  }

  const percentileInfo = getPercentileLabel(data.current_percentile);

  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
        <Typography variant="h6" gutterBottom>
          RSI-MA Percentile Indicator - {ticker}
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Chip
            label={`Current RSI: ${data.current_rsi.toFixed(2)}`}
            color="secondary"
            size="small"
          />
          <Chip
            label={`Current RSI-MA: ${data.current_rsi_ma.toFixed(2)}`}
            size="small"
            sx={{ 
              backgroundColor: getColorForPercentile(data.current_percentile),
              color: data.current_percentile >= 25 && data.current_percentile < 75 ? '#000' : '#fff'
            }}
          />
          <Chip
            label={`${percentileInfo.text} - ${data.current_percentile.toFixed(1)}%`}
            size="small"
            sx={{ backgroundColor: percentileInfo.color, color: '#fff' }}
          />
        </Box>
      </Box>
      
      <Plot
        data={plotData}
        layout={{
          autosize: true,
          height: 500,
          margin: { l: 60, r: 40, t: 40, b: 60 },
          xaxis: {
            title: { text: 'Date' },
            gridcolor: 'rgba(128, 128, 128, 0.2)',
            showgrid: true,
          },
          yaxis: {
            title: { text: 'RSI Value' },
            gridcolor: 'rgba(128, 128, 128, 0.2)',
            showgrid: true,
            range: [0, 100],
          },
          hovermode: 'x unified',
          showlegend: true,
          legend: {
            x: 0.01,
            y: 0.99,
            bgcolor: 'rgba(255, 255, 255, 0.8)',
            bordercolor: 'rgba(0, 0, 0, 0.2)',
            borderwidth: 1,
          },
          plot_bgcolor: 'rgba(17, 17, 17, 0.9)',
          paper_bgcolor: 'rgba(0, 0, 0, 0)',
          font: {
            color: 'rgba(255, 255, 255, 0.8)',
          },
        }}
        config={{
          responsive: true,
          displayModeBar: true,
          displaylogo: false,
          modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
        }}
        style={{ width: '100%' }}
      />
      
      <Box sx={{ mt: 2, p: 2, bgcolor: 'rgba(0, 0, 0, 0.2)', borderRadius: 1 }}>
        <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
          <strong>Interpretation:</strong>
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block">
          • <strong>RSI-MA below 5%:</strong> Extreme oversold - Strong potential entry signal
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block">
          • <strong>RSI-MA 5-15%:</strong> Oversold - Good entry opportunity
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block">
          • <strong>RSI-MA above 95%:</strong> Extreme overbought - Consider taking profits
        </Typography>
      </Box>
    </Paper>
  );
};

export default RSIPercentileChart;
