/**
 * Performance Matrix Heatmap Component
 * 
 * Interactive heatmap showing expected returns by percentile range and day (D1-D21)
 * - Color scale: Red (negative) → Yellow (0%) → Green (positive)
 * - Hover: Show sample size, confidence level, success rate
 * - Click: Drill down to distribution details
 */

import React, { useMemo } from 'react';
import { Box, Paper, Typography, Tooltip, Chip } from '@mui/material';
import Plot from 'react-plotly.js';
import type { PerformanceMatrix, PerformanceCell } from '@/types';

interface PerformanceMatrixHeatmapProps {
  matrix: PerformanceMatrix;
  title?: string;
  maxDay?: number;
  showConfidence?: boolean;
  onCellClick?: (cell: PerformanceCell) => void;
}

const PerformanceMatrixHeatmap: React.FC<PerformanceMatrixHeatmapProps> = ({
  matrix,
  title = 'Performance Matrix Heatmap',
  maxDay = 21,
  showConfidence = true,
  onCellClick,
}) => {
  const { data, layout } = useMemo(() => {
    // Extract percentile ranges (Y-axis)
    const percentileRanges = Object.keys(matrix).sort((a, b) => {
      const aStart = parseInt(a.split('-')[0]);
      const bStart = parseInt(b.split('-')[0]);
      return bStart - aStart; // Reverse order (95-100% at top)
    });

    // Days (X-axis)
    const days = Array.from({ length: maxDay }, (_, i) => i + 1);

    // Build Z matrix (returns)
    const zValues: (number | null)[][] = [];
    const customData: string[][] = [];
    const hoverText: string[][] = [];

    percentileRanges.forEach((range) => {
      const row: (number | null)[] = [];
      const customRow: string[] = [];
      const hoverRow: string[] = [];

      days.forEach((day) => {
        const cell = matrix[range]?.[day];
        
        if (cell) {
          row.push(cell.expected_cumulative_return);
          customRow.push(cell.confidence_level);
          
          const hoverInfo = [
            `<b>${range} on D${day}</b>`,
            `Expected Return: ${cell.expected_cumulative_return.toFixed(2)}%`,
            `Success Rate: ${(cell.expected_success_rate * 100).toFixed(1)}%`,
            `Sample Size: ${cell.sample_size} (${cell.confidence_level})`,
            `P25-P75: ${cell.p25_return.toFixed(2)}% to ${cell.p75_return.toFixed(2)}%`,
          ].join('<br>');
          hoverRow.push(hoverInfo);
        } else {
          row.push(null);
          customRow.push('');
          hoverRow.push('No data');
        }
      });

      zValues.push(row);
      customData.push(customRow);
      hoverText.push(hoverRow);
    });

    const plotData: Plotly.Data[] = [
      {
        z: zValues,
        x: days.map(d => `D${d}`),
        y: percentileRanges,
        type: 'heatmap',
        colorscale: [
          [0, '#c62828'],      // Dark red (negative)
          [0.4, '#f44336'],    // Red
          [0.45, '#ffebee'],   // Light red
          [0.5, '#fff9c4'],    // Yellow (neutral)
          [0.55, '#e8f5e9'],   // Light green
          [0.6, '#81c784'],    // Green
          [1, '#2e7d32'],      // Dark green (positive)
        ],
        colorbar: {
          title: 'Return %',
          titleside: 'right',
        },
        hovertemplate: '%{text}<extra></extra>',
        text: hoverText,
        customdata: customData,
      } as any,
    ];

    const plotLayout: Partial<Plotly.Layout> = {
      title: {
        text: title,
        font: { size: 16 },
      },
      xaxis: {
        title: 'Holding Period (Days)',
        side: 'bottom',
        tickmode: 'linear',
        dtick: 1,
      },
      yaxis: {
        title: 'RSI-MA Percentile Range',
        tickmode: 'linear',
      },
      height: 600,
      margin: { l: 100, r: 100, t: 80, b: 80 },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
    };

    return { data: plotData, layout: plotLayout };
  }, [matrix, maxDay, title]);

  return (
    <Paper elevation={3} sx={{ p: 2 }}>
      <Plot
        data={data}
        layout={layout}
        config={{
          responsive: true,
          displayModeBar: true,
          displaylogo: false,
          modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
        }}
        style={{ width: '100%', height: '100%' }}
      />
      
      {showConfidence && (
        <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'center' }}>
          <Typography variant="caption" sx={{ mr: 2 }}>
            Confidence Levels:
          </Typography>
          <Chip label="VH: 20+ samples" size="small" color="success" />
          <Chip label="H: 10-19 samples" size="small" color="primary" />
          <Chip label="M: 5-9 samples" size="small" color="warning" />
          <Chip label="L: 3-4 samples" size="small" color="error" variant="outlined" />
          <Chip label="VL: 1-2 samples" size="small" variant="outlined" />
        </Box>
      )}
    </Paper>
  );
};

export default PerformanceMatrixHeatmap;
