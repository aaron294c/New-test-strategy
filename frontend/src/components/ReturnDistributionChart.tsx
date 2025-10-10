/**
 * Return Distribution Chart Component
 * 
 * Shows return distributions by day with confidence intervals
 * - Box plots showing median, quartiles, and outliers
 * - Overlay with market benchmark comparison
 */

import React, { useMemo } from 'react';
import { Paper, Typography, Box } from '@mui/material';
import Plot from 'react-plotly.js';
import type { ReturnDistribution, MarketBenchmark } from '@/types';

interface ReturnDistributionChartProps {
  returnDistributions: { [day: number]: ReturnDistribution };
  benchmark?: MarketBenchmark;
  title?: string;
  maxDay?: number;
}

const ReturnDistributionChart: React.FC<ReturnDistributionChartProps> = ({
  returnDistributions,
  benchmark,
  title = 'Return Distribution by Holding Period',
  maxDay = 21,
}) => {
  const { data, layout } = useMemo(() => {
    const days = Array.from({ length: maxDay }, (_, i) => i + 1).filter(
      (day) => returnDistributions[day]?.sample_size > 0
    );

    // Strategy returns with confidence bands
    const medianReturns = days.map(day => returnDistributions[day].median);
    const plus1sd = days.map(day => returnDistributions[day].plus_1sd);
    const minus1sd = days.map(day => returnDistributions[day].minus_1sd);
    const plus2sd = days.map(day => returnDistributions[day].plus_2sd);
    const minus2sd = days.map(day => returnDistributions[day].minus_2sd);

    const plotData: Plotly.Data[] = [
      // 95% confidence band (±2SD)
      {
        x: days.map(d => `D${d}`),
        y: plus2sd,
        fill: 'tonexty',
        fillcolor: 'rgba(76, 175, 80, 0.1)',
        line: { color: 'transparent' },
        name: '95% Band',
        type: 'scatter',
        mode: 'lines',
        showlegend: true,
        hoverinfo: 'skip',
      },
      {
        x: days.map(d => `D${d}`),
        y: minus2sd,
        fill: 'none',
        line: { color: 'transparent' },
        name: '95% Lower',
        type: 'scatter',
        mode: 'lines',
        showlegend: false,
        hoverinfo: 'skip',
      },

      // 68% confidence band (±1SD)
      {
        x: days.map(d => `D${d}`),
        y: plus1sd,
        fill: 'tonexty',
        fillcolor: 'rgba(76, 175, 80, 0.2)',
        line: { color: 'rgba(76, 175, 80, 0.4)', dash: 'dash' },
        name: '68% Band',
        type: 'scatter',
        mode: 'lines',
        showlegend: true,
      },
      {
        x: days.map(d => `D${d}`),
        y: minus1sd,
        line: { color: 'rgba(76, 175, 80, 0.4)', dash: 'dash' },
        name: '68% Lower',
        type: 'scatter',
        mode: 'lines',
        showlegend: false,
      },

      // Median return line
      {
        x: days.map(d => `D${d}`),
        y: medianReturns,
        name: 'Strategy Median',
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: '#4caf50', width: 3 },
        marker: { size: 8, color: '#4caf50' },
        hovertemplate: '<b>D%{x}</b><br>Median Return: %{y:.2f}%<extra></extra>',
      },
    ];

    // Add benchmark if available
    if (benchmark) {
      const benchmarkReturns = days.map(day => benchmark.cumulative_returns[day] || 0);
      plotData.push({
        x: days.map(d => `D${d}`),
        y: benchmarkReturns,
        name: `${benchmark.ticker} Benchmark`,
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: '#2196f3', width: 2, dash: 'dot' },
        marker: { size: 6, color: '#2196f3' },
        hovertemplate: '<b>D%{x}</b><br>Benchmark: %{y:.2f}%<extra></extra>',
      });
    }

    const plotLayout: Partial<Plotly.Layout> = {
      title: {
        text: title,
        font: { size: 16 },
      },
      xaxis: {
        title: 'Holding Period',
        tickmode: 'linear',
        dtick: 1,
      },
      yaxis: {
        title: 'Cumulative Return (%)',
        zeroline: true,
        zerolinewidth: 2,
        zerolinecolor: '#999',
      },
      hovermode: 'x unified',
      height: 500,
      margin: { l: 60, r: 40, t: 80, b: 60 },
      showlegend: true,
      legend: {
        x: 0.02,
        y: 0.98,
        bgcolor: 'rgba(255, 255, 255, 0.9)',
        bordercolor: '#ccc',
        borderwidth: 1,
      },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
    };

    return { data: plotData, layout: plotLayout };
  }, [returnDistributions, benchmark, maxDay, title]);

  return (
    <Paper elevation={3} sx={{ p: 2 }}>
      <Plot
        data={data}
        layout={layout}
        config={{
          responsive: true,
          displayModeBar: true,
          displaylogo: false,
        }}
        style={{ width: '100%', height: '100%' }}
      />
      
      <Box sx={{ mt: 2, px: 2 }}>
        <Typography variant="caption" color="text.secondary">
          Shaded areas represent 68% (1σ) and 95% (2σ) confidence intervals.
          Median returns shown as solid green line.
        </Typography>
      </Box>
    </Paper>
  );
};

export default ReturnDistributionChart;
