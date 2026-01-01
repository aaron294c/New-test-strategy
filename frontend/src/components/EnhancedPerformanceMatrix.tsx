/**
 * Enhanced Performance Matrix Component
 * Shows the full matrix with:
 * - Main heatmap (expected returns by percentile/day)
 * - Win rate row
 * - Return distribution row (median ± std)
 * - 68% return range row (±1SD)
 * - 95% return range row (±2SD)
 */

import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
} from '@mui/material';
import type { PerformanceMatrix, ReturnDistribution } from '../types';

interface EnhancedPerformanceMatrixProps {
  matrix: PerformanceMatrix;
  winRates: { [day: number]: number };
  returnDistributions: { [day: number]: ReturnDistribution };
  title: string;
  maxDay?: number;
}

const EnhancedPerformanceMatrix: React.FC<EnhancedPerformanceMatrixProps> = ({
  matrix,
  winRates,
  returnDistributions,
  title,
  maxDay = 21,
}) => {
  // Extract percentile ranges
  const percentileRanges = Object.keys(matrix).sort((a, b) => {
    const aStart = parseInt(a.split('-')[0]);
    const bStart = parseInt(b.split('-')[0]);
    return aStart - bStart; // Ascending order
  });

  // Days array
  const days = Array.from({ length: maxDay }, (_, i) => i + 1);

  // Color scale for returns
  const getReturnColor = (ret: number) => {
    if (ret > 3) return '#2e7d32'; // Dark green
    if (ret > 2) return '#43a047';
    if (ret > 1) return '#66bb6a';
    if (ret > 0.5) return '#81c784';
    if (ret > 0) return '#a5d6a7';
    if (ret === 0) return '#fff9c4'; // Yellow
    if (ret > -0.5) return '#ffccbc';
    if (ret > -1) return '#ff8a65';
    if (ret > -2) return '#f4511e';
    return '#c62828'; // Dark red
  };

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Shows: CUMULATIVE Return% (Sample Size & Confidence Level)
      </Typography>

      <TableContainer sx={{ maxHeight: 800, mt: 2 }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold', minWidth: 120 }}>Percentile</TableCell>
              {days.map((day) => (
                <TableCell key={day} align="center" sx={{ fontWeight: 'bold', minWidth: 120 }}>
                  D{day}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {/* Main matrix rows */}
            {percentileRanges.map((range) => (
              <TableRow key={range} hover>
                <TableCell sx={{ fontWeight: 'bold' }}>{range}</TableCell>
                {days.map((day) => {
                  const cell = matrix[range]?.[day];
                  return (
                    <TableCell
                      key={day}
                      align="center"
                      sx={{
                        bgcolor: cell ? getReturnColor(cell.expected_cumulative_return) : 'transparent',
                        color: cell && Math.abs(cell.expected_cumulative_return) > 1 ? '#fff' : 'inherit',
                      }}
                    >
                      {cell ? (
                        <Box>
                          <Typography variant="body2" fontWeight="bold">
                            {cell.expected_cumulative_return > 0 ? '+' : ''}
                            {cell.expected_cumulative_return.toFixed(2)}%
                          </Typography>
                          <Typography variant="caption" sx={{ opacity: 0.9 }}>
                            ({cell.sample_size}{cell.confidence_level})
                          </Typography>
                        </Box>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}

            {/* Divider row */}
            <TableRow>
              <TableCell colSpan={maxDay + 1} sx={{ bgcolor: 'action.hover' }} />
            </TableRow>

            {/* Win Rate % row */}
            <TableRow sx={{ bgcolor: 'action.selected' }}>
              <TableCell sx={{ fontWeight: 'bold' }}>Win Rate %</TableCell>
              {days.map((day) => {
                const winRate = winRates[day];
                return (
                  <TableCell key={day} align="center">
                    {winRate !== undefined ? (
                      <Typography variant="body2" fontWeight="bold" color={winRate > 60 ? 'success.main' : winRate > 50 ? 'info.main' : 'error.main'}>
                        {winRate.toFixed(1)}%
                      </Typography>
                    ) : (
                      '-'
                    )}
                  </TableCell>
                );
              })}
            </TableRow>

            {/* Return Distribution (median ± std) row */}
            <TableRow sx={{ bgcolor: 'action.selected' }}>
              <TableCell sx={{ fontWeight: 'bold' }}>Ret Dist %</TableCell>
              {days.map((day) => {
                const dist = returnDistributions[day];
                return (
                  <TableCell key={day} align="center">
                    {dist && dist.sample_size > 0 ? (
                      <Typography variant="body2">
                        {dist.median > 0 ? '+' : ''}{dist.median.toFixed(1)} ± {dist.std.toFixed(1)}
                      </Typography>
                    ) : (
                      '-'
                    )}
                  </TableCell>
                );
              })}
            </TableRow>

            {/* 68% Return Range (±1SD) row */}
            <TableRow sx={{ bgcolor: 'action.selected' }}>
              <TableCell sx={{ fontWeight: 'bold' }}>68% Ret Rng</TableCell>
              {days.map((day) => {
                const dist = returnDistributions[day];
                return (
                  <TableCell key={day} align="center">
                    {dist && dist.sample_size > 0 ? (
                      <Typography variant="body2" fontSize="0.75rem">
                        {dist.minus_1sd > 0 ? '+' : ''}{dist.minus_1sd.toFixed(1)} ~
                        {dist.plus_1sd > 0 ? '+' : ''}{dist.plus_1sd.toFixed(1)}
                      </Typography>
                    ) : (
                      '-'
                    )}
                  </TableCell>
                );
              })}
            </TableRow>

            {/* 95% Return Range (±2SD) row */}
            <TableRow sx={{ bgcolor: 'action.selected' }}>
              <TableCell sx={{ fontWeight: 'bold' }}>95% Ret Rng</TableCell>
              {days.map((day) => {
                const dist = returnDistributions[day];
                return (
                  <TableCell key={day} align="center">
                    {dist && dist.sample_size > 0 ? (
                      <Typography variant="body2" fontSize="0.75rem">
                        {dist.minus_2sd > 0 ? '+' : ''}{dist.minus_2sd.toFixed(1)} ~
                        {dist.plus_2sd > 0 ? '+' : ''}{dist.plus_2sd.toFixed(1)}
                      </Typography>
                    ) : (
                      '-'
                    )}
                  </TableCell>
                );
              })}
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>

      {/* Legend */}
      <Box sx={{ mt: 3, display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
        <Box>
          <Typography variant="caption" fontWeight="bold">
            Confidence Levels:
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
            <Chip label="VH: 20+" size="small" color="success" />
            <Chip label="H: 10-19" size="small" color="primary" />
            <Chip label="M: 5-9" size="small" color="warning" />
            <Chip label="L: 3-4" size="small" color="error" variant="outlined" />
            <Chip label="VL: 1-2" size="small" variant="outlined" />
          </Box>
        </Box>
      </Box>

      {/* Color scale legend */}
      <Box sx={{ mt: 2, display: 'flex', gap: 1, justifyContent: 'center', alignItems: 'center' }}>
        <Typography variant="caption">Return Scale:</Typography>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Box sx={{ width: 40, height: 20, bgcolor: '#c62828' }} />
          <Typography variant="caption" sx={{ mx: 0.5 }}>-2%</Typography>
          <Box sx={{ width: 40, height: 20, bgcolor: '#f4511e' }} />
          <Box sx={{ width: 40, height: 20, bgcolor: '#ff8a65' }} />
          <Box sx={{ width: 40, height: 20, bgcolor: '#fff9c4' }} />
          <Typography variant="caption" sx={{ mx: 0.5 }}>0%</Typography>
          <Box sx={{ width: 40, height: 20, bgcolor: '#a5d6a7' }} />
          <Box sx={{ width: 40, height: 20, bgcolor: '#66bb6a' }} />
          <Box sx={{ width: 40, height: 20, bgcolor: '#43a047' }} />
          <Box sx={{ width: 40, height: 20, bgcolor: '#2e7d32' }} />
          <Typography variant="caption" sx={{ mx: 0.5 }}>+3%</Typography>
        </Box>
      </Box>
    </Paper>
  );
};

export default EnhancedPerformanceMatrix;
