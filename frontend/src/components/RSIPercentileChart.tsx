/**
 * RSI Percentile Chart Component
 * Enhanced version with improved cosmetics: better colors, opacity, readability
 * Inspired by TradingView's First Passage Time Distribution Analysis
 */

import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import { Paper, Typography, Box, Chip, CircularProgress, Grid } from '@mui/material';
import type { RSIChartData } from '@/types';

interface RSIPercentileChartProps {
  data: RSIChartData | null;
  ticker: string;
  isLoading?: boolean;
}

// Enhanced color scheme with better contrast
const getColorForPercentile = (percentile: number): string => {
  if (percentile >= 95) return 'rgb(220, 53, 69)';      // Vibrant Red (extreme high)
  if (percentile >= 85) return 'rgb(253, 126, 20)';     // Bright Orange (very high)
  if (percentile >= 75) return 'rgb(255, 193, 7)';      // Golden Yellow (high)
  if (percentile >= 25) return 'rgb(108, 117, 125)';    // Neutral Gray (normal)
  if (percentile >= 15) return 'rgb(13, 110, 253)';     // Bright Blue (low)
  if (percentile >= 5) return 'rgb(25, 135, 84)';       // Medium Green (very low)
  return 'rgb(16, 185, 129)';                           // Bright Green (extreme low)
};

// Background color for percentile zones with opacity
const getBackgroundColor = (percentile: number): string => {
  if (percentile >= 95) return 'rgba(220, 53, 69, 0.15)';
  if (percentile >= 85) return 'rgba(253, 126, 20, 0.12)';
  if (percentile >= 75) return 'rgba(255, 193, 7, 0.10)';
  if (percentile >= 25) return 'rgba(108, 117, 125, 0.05)';
  if (percentile >= 15) return 'rgba(13, 110, 253, 0.10)';
  if (percentile >= 5) return 'rgba(25, 135, 84, 0.12)';
  return 'rgba(16, 185, 129, 0.15)';
};

// Helper function to create colored line segments for RSI-MA
// ⭐ This is the STAR of the chart - thick, vibrant, color-coded
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
      name: i === 0 ? '⭐ RSI-MA (Percentile-Colored) - PRIMARY SIGNAL' : '',
      showlegend: i === 0,
      line: {
        color: color,
        width: 4,  // THICKER - This is the main signal line
      },
      hovertemplate: `<b>Date:</b> %{x}<br><b>⭐ RSI-MA:</b> %{y:.2f}<br><b>Percentile Rank:</b> ${percentiles[i].toFixed(1)}%<extra></extra>`,
      type: 'scatter',
    });
  }
  
  return segments;
};

const RSIPercentileChart: React.FC<RSIPercentileChartProps> = ({ data, ticker, isLoading }) => {
  // Calculate default date range - show last 30 days for daily analysis
  const defaultDateRange = useMemo(() => {
    if (!data || !data.dates || data.dates.length === 0) return null;
    const defaultStartIndex = Math.max(0, data.dates.length - 30);
    return {
      start: data.dates[defaultStartIndex],
      end: data.dates[data.dates.length - 1]
    };
  }, [data]);

  const plotData = useMemo(() => {
    if (!data) return [];

    const { dates, rsi, rsi_ma, percentile_rank, percentile_thresholds } = data;

    const traces: any[] = [
      // Background gradient zones (30-70 RSI bands)
      {
        x: dates,
        y: Array(dates.length).fill(100),
        fill: 'tonexty',
        fillcolor: 'rgba(220, 53, 69, 0.08)',  // Light red above 70
        line: { width: 0 },
        showlegend: false,
        hoverinfo: 'skip',
        type: 'scatter',
        name: '',
      },
      {
        x: dates,
        y: Array(dates.length).fill(70),
        fillcolor: 'rgba(108, 117, 125, 0.03)',  // Very light gray 30-70
        line: { width: 0 },
        showlegend: false,
        hoverinfo: 'skip',
        type: 'scatter',
        fill: 'tonexty',
      },
      {
        x: dates,
        y: Array(dates.length).fill(30),
        fill: 'tonexty',
        fillcolor: 'rgba(16, 185, 129, 0.08)',  // Light green below 30
        line: { width: 0 },
        showlegend: false,
        hoverinfo: 'skip',
        type: 'scatter',
      },
      {
        x: dates,
        y: Array(dates.length).fill(0),
        line: { width: 0 },
        showlegend: false,
        hoverinfo: 'skip',
        type: 'scatter',
      },
      // RSI line (very subtle background reference)
      {
        x: dates,
        y: rsi,
        mode: 'lines',
        name: 'RSI (14) - Reference',
        line: {
          color: 'rgba(156, 39, 176, 0.2)',  // Very faint purple
          width: 1,
          dash: 'dot',
        },
        hovertemplate: '<b>Date:</b> %{x}<br><b>RSI:</b> %{y:.2f}<extra></extra>',
        type: 'scatter',
        visible: 'legendonly',  // Hidden by default, can be toggled
      },
      // RSI-MA line (color-coded by percentile) - ⭐ MAIN FOCUS ⭐
      ...createColoredLineSegments(dates, rsi_ma, percentile_rank),
      // Percentile threshold lines - More subtle
      {
        x: [dates[0], dates[dates.length - 1]],
        y: [percentile_thresholds.p95, percentile_thresholds.p95],
        mode: 'lines',
        name: '95th %ile (Extreme High)',
        line: {
          color: 'rgba(220, 53, 69, 0.7)',
          width: 2,
          dash: 'dash',
        },
        hovertemplate: '<b>95th Percentile:</b> %{y:.2f}<extra></extra>',
        type: 'scatter',
      },
      {
        x: [dates[0], dates[dates.length - 1]],
        y: [percentile_thresholds.p85, percentile_thresholds.p85],
        mode: 'lines',
        name: '85th %ile (Very High)',
        line: {
          color: 'rgba(253, 126, 20, 0.6)',
          width: 1.5,
          dash: 'dash',
        },
        hovertemplate: '<b>85th Percentile:</b> %{y:.2f}<extra></extra>',
        type: 'scatter',
      },
      {
        x: [dates[0], dates[dates.length - 1]],
        y: [percentile_thresholds.p75, percentile_thresholds.p75],
        mode: 'lines',
        name: '75th %ile (High)',
        line: {
          color: 'rgba(255, 193, 7, 0.6)',
          width: 1.5,
          dash: 'dash',
        },
        hovertemplate: '<b>75th Percentile:</b> %{y:.2f}<extra></extra>',
        type: 'scatter',
      },
      {
        x: [dates[0], dates[dates.length - 1]],
        y: [percentile_thresholds.p50, percentile_thresholds.p50],
        mode: 'lines',
        name: '50th %ile (Median)',
        line: {
          color: 'rgba(255, 255, 255, 0.8)',
          width: 2,
          dash: 'solid',
        },
        hovertemplate: '<b>50th Percentile (Median):</b> %{y:.2f}<extra></extra>',
        type: 'scatter',
      },
      {
        x: [dates[0], dates[dates.length - 1]],
        y: [percentile_thresholds.p25, percentile_thresholds.p25],
        mode: 'lines',
        name: '25th %ile (Low)',
        line: {
          color: 'rgba(13, 110, 253, 0.6)',
          width: 1.5,
          dash: 'dash',
        },
        hovertemplate: '<b>25th Percentile:</b> %{y:.2f}<extra></extra>',
        type: 'scatter',
      },
      {
        x: [dates[0], dates[dates.length - 1]],
        y: [percentile_thresholds.p15, percentile_thresholds.p15],
        mode: 'lines',
        name: '15th %ile (Very Low)',
        line: {
          color: 'rgba(25, 135, 84, 0.6)',
          width: 1.5,
          dash: 'dash',
        },
        hovertemplate: '<b>15th Percentile:</b> %{y:.2f}<extra></extra>',
        type: 'scatter',
      },
      {
        x: [dates[0], dates[dates.length - 1]],
        y: [percentile_thresholds.p5, percentile_thresholds.p5],
        mode: 'lines',
        name: '5th %ile (Extreme Low)',
        line: {
          color: 'rgba(16, 185, 129, 0.7)',
          width: 2,
          dash: 'dash',
        },
        hovertemplate: '<b>5th Percentile:</b> %{y:.2f}<extra></extra>',
        type: 'scatter',
      },
      // Standard RSI levels (70/30)
      {
        x: [dates[0], dates[dates.length - 1]],
        y: [70, 70],
        mode: 'lines',
        name: 'Overbought (70)',
        line: {
          color: 'rgba(255, 255, 255, 0.3)',
          width: 1,
          dash: 'dot',
        },
        hoverinfo: 'skip',
        type: 'scatter',
      },
      {
        x: [dates[0], dates[dates.length - 1]],
        y: [30, 30],
        mode: 'lines',
        name: 'Oversold (30)',
        line: {
          color: 'rgba(255, 255, 255, 0.3)',
          width: 1,
          dash: 'dot',
        },
        hoverinfo: 'skip',
        type: 'scatter',
      },
    ];

    return traces;
  }, [data]);

  const getPercentileLabel = (percentile: number): { text: string; color: string; bgColor: string } => {
    if (percentile >= 95) return { text: 'EXTREME HIGH (>95%)', color: '#fff', bgColor: '#dc3545' };
    if (percentile >= 85) return { text: 'Very High (85-95%)', color: '#fff', bgColor: '#fd7e14' };
    if (percentile >= 75) return { text: 'High (75-85%)', color: '#000', bgColor: '#ffc107' };
    if (percentile >= 25) return { text: 'Normal Range (25-75%)', color: '#fff', bgColor: '#6c757d' };
    if (percentile >= 15) return { text: 'Low (15-25%)', color: '#fff', bgColor: '#0d6efd' };
    if (percentile >= 5) return { text: 'Very Low (5-15%)', color: '#fff', bgColor: '#198754' };
    return { text: 'EXTREME LOW (<5%) - STRONG BUY', color: '#fff', bgColor: '#10b981' };
  };

  if (isLoading) {
    return (
      <Paper sx={{ p: 3, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 500 }}>
        <Box sx={{ textAlign: 'center' }}>
          <CircularProgress size={60} />
          <Typography variant="body1" sx={{ mt: 2 }}>Loading RSI data...</Typography>
        </Box>
      </Paper>
    );
  }

  if (!data) {
    return (
      <Paper sx={{ p: 3, minHeight: 500 }}>
        <Typography variant="h6" color="error" gutterBottom>
          RSI Chart Data Unavailable
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Unable to load RSI percentile data. Please try refreshing or selecting a different ticker.
        </Typography>
      </Paper>
    );
  }

  const percentileInfo = getPercentileLabel(data.current_percentile);

  return (
    <Paper sx={{ p: 3, backgroundColor: 'rgba(18, 18, 18, 0.95)' }}>
      <Box sx={{ mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={5}>
            <Typography variant="h5" gutterBottom sx={{ color: '#fff', fontWeight: 600 }}>
              📊 RSI-MA Percentile Indicator
            </Typography>
            <Typography variant="subtitle2" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
              {ticker} • 252-Day Historical Analysis
            </Typography>
          </Grid>
          <Grid item xs={12} md={7}>
            <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', justifyContent: { xs: 'flex-start', md: 'flex-end' } }}>
              {/* ⭐ RSI-MA is the PRIMARY metric - make it stand out */}
              <Chip
                label={`⭐ RSI-MA: ${data.current_rsi_ma.toFixed(1)}`}
                sx={{ 
                  backgroundColor: getColorForPercentile(data.current_percentile),
                  color: '#fff',
                  fontWeight: 700,
                  fontSize: '1.1rem',
                  height: 44,
                  px: 2,
                  border: '2px solid rgba(255, 255, 255, 0.3)',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
                }}
              />
              <Chip
                label={`${percentileInfo.text}`}
                sx={{ 
                  backgroundColor: percentileInfo.bgColor,
                  color: percentileInfo.color,
                  fontWeight: 700,
                  fontSize: '1rem',
                  height: 44,
                  px: 2,
                  boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                }}
              />
              <Chip
                label={`RSI: ${data.current_rsi.toFixed(1)}`}
                size="small"
                sx={{ 
                  backgroundColor: 'rgba(156, 39, 176, 0.6)',
                  color: '#fff',
                  fontWeight: 500,
                  fontSize: '0.8rem',
                  height: 32,
                  opacity: 0.7,
                }}
              />
            </Box>
          </Grid>
        </Grid>
      </Box>
      
      <Plot
        data={plotData}
        layout={{
          autosize: true,
          height: 700,  // Taller for better visibility
          margin: { l: 70, r: 50, t: 20, b: 120 },  // More bottom margin for range slider
          xaxis: {
            title: { 
              text: 'Date (Showing Last 30 Days by Default)',
              font: { size: 14, color: 'rgba(255, 255, 255, 0.9)' }
            },
            gridcolor: 'rgba(255, 255, 255, 0.1)',
            showgrid: true,
            color: 'rgba(255, 255, 255, 0.8)',
            range: defaultDateRange ? [defaultDateRange.start, defaultDateRange.end] : undefined,  // Default to last 30 days
            rangeslider: { 
              visible: true,
              bgcolor: 'rgba(30, 30, 30, 0.8)',
              bordercolor: 'rgba(255, 255, 255, 0.2)',
              borderwidth: 1,
              thickness: 0.08,
            },
            rangeselector: {
              buttons: [
                { count: 7, label: '1W', step: 'day', stepmode: 'backward' },
                { count: 14, label: '2W', step: 'day', stepmode: 'backward' },
                { count: 30, label: '1M', step: 'day', stepmode: 'backward' },
                { count: 60, label: '2M', step: 'day', stepmode: 'backward' },
                { count: 90, label: '3M', step: 'day', stepmode: 'backward' },
                { step: 'all', label: 'ALL' }
              ],
              bgcolor: 'rgba(50, 50, 50, 0.8)',
              activecolor: 'rgba(99, 102, 241, 0.8)',
              font: { color: 'rgba(255, 255, 255, 0.9)', size: 11 },
              x: 0.01,
              y: 1.15,
            },
          },
          yaxis: {
            title: { 
              text: 'RSI Value (0-100)',
              font: { size: 16, color: 'rgba(255, 255, 255, 0.9)', weight: 'bold' }
            },
            gridcolor: 'rgba(255, 255, 255, 0.15)',
            showgrid: true,
            range: [0, 100],
            color: 'rgba(255, 255, 255, 0.8)',
            tickformat: '.0f',
            fixedrange: false,  // Allow zoom on Y-axis too
            dtick: 10,  // Show tick every 10 points
          },
          hovermode: 'x unified',
          showlegend: true,
          legend: {
            x: 0.01,
            y: 0.99,
            bgcolor: 'rgba(0, 0, 0, 0.85)',
            bordercolor: 'rgba(255, 255, 255, 0.4)',
            borderwidth: 2,
            font: { 
              size: 12,
              color: 'rgba(255, 255, 255, 0.95)' 
            },
          },
          plot_bgcolor: 'rgba(10, 10, 10, 0.95)',
          paper_bgcolor: 'rgba(0, 0, 0, 0)',
          font: {
            color: 'rgba(255, 255, 255, 0.9)',
            size: 12,
          },
          dragmode: 'zoom',  // Enable zoom by default
        }}
        config={{
          responsive: true,
          displayModeBar: true,
          displaylogo: false,
          scrollZoom: true,  // Enable scroll to zoom
          modeBarButtonsToAdd: ['drawline', 'drawopenpath', 'eraseshape'],
          toImageButtonOptions: {
            format: 'png',
            filename: `${ticker}_rsi_ma_chart`,
            height: 1080,
            width: 1920,
            scale: 2
          },
        }}
        style={{ width: '100%' }}
      />
      
      <Box sx={{ mt: 3, p: 2.5, bgcolor: 'rgba(0, 0, 0, 0.4)', borderRadius: 2, border: '1px solid rgba(255, 255, 255, 0.1)' }}>
        <Typography variant="caption" sx={{ color: '#6366f1', fontWeight: 700, display: 'block', mb: 2 }}>
          💡 CHART CONTROLS: Scroll to zoom in/out • Click & drag to pan • Quick view: 1W, 2W, 1M, 2M, 3M, ALL • Drag the slider at bottom for custom range
        </Typography>
        <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.6)', display: 'block', mb: 2 }}>
          ⭐ The thick color-coded line is RSI-MA - your primary signal. Color shows percentile rank (green = buy, red = sell).
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" sx={{ color: '#10b981', fontWeight: 700, mb: 1 }}>
              🟢 ENTRY SIGNALS (RSI-MA Percentile Oversold)
            </Typography>
            <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)', mb: 0.5 }}>
              • <strong>Extreme Low (&lt;5%):</strong> Strong buy - RSI-MA at historical lows
            </Typography>
            <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
              • <strong>Very Low (5-15%):</strong> Good entry - High probability of mean reversion
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" sx={{ color: '#dc3545', fontWeight: 700, mb: 1 }}>
              🔴 EXIT SIGNALS (RSI-MA Percentile Overbought)
            </Typography>
            <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)', mb: 0.5 }}>
              • <strong>Extreme High (&gt;95%):</strong> Take profits - RSI-MA at historical peaks
            </Typography>
            <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
              • <strong>Very High (85-95%):</strong> Consider exit - Overbought territory
            </Typography>
          </Grid>
        </Grid>
      </Box>
    </Paper>
  );
};

export default RSIPercentileChart;
