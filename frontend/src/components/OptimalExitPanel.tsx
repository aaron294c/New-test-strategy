/**
 * Optimal Exit Strategy Panel
 * 
 * Displays optimal exit recommendations based on return efficiency analysis
 */

import React from 'react';
import {
  Paper,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Alert,
  AlertTitle,
} from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import type { OptimalExitStrategy, RiskMetrics, TrendAnalysis } from '@/types';

interface OptimalExitPanelProps {
  optimalExit: OptimalExitStrategy;
  riskMetrics: RiskMetrics;
  trendAnalysis: TrendAnalysis;
  ticker: string;
  threshold: number;
}

const OptimalExitPanel: React.FC<OptimalExitPanelProps> = ({
  optimalExit,
  riskMetrics,
  trendAnalysis,
  ticker: _ticker,
  threshold: _threshold,
}) => {
  const getConfidenceColor = (confidence: string) => {
    const colors: Record<string, 'success' | 'primary' | 'warning' | 'error'> = {
      VH: 'success',
      H: 'primary',
      M: 'warning',
      L: 'error',
      VL: 'error',
    };
    return colors[confidence] || 'default';
  };

  const getTrendIndicator = () => {
    if (trendAnalysis.trend_p_value < 0.01) return 'Very Strong';
    if (trendAnalysis.trend_p_value < 0.05) return 'Strong';
    if (trendAnalysis.trend_p_value < 0.10) return 'Moderate';
    return 'Weak';
  };

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <TrendingUpIcon sx={{ fontSize: 32, mr: 1, color: 'success.main' }} />
        <Typography variant="h5" component="h2">
          Optimal Exit Strategy
        </Typography>
      </Box>

      {/* Primary Recommendation */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <AlertTitle>
          <strong>Recommended Exit: Day {optimalExit.optimal_day}</strong>
        </AlertTitle>
        <Typography variant="body2">
          Best risk-adjusted exit at <strong>{optimalExit.optimal_efficiency.toFixed(3)}%/day efficiency</strong>
          {' '}with expected <strong>{optimalExit.target_return.toFixed(2)}% total return</strong>
        </Typography>
      </Alert>

      {/* Exit Target Details */}
      {optimalExit.exit_percentile_target && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Exit Target Details
          </Typography>
          <TableContainer>
            <Table size="small">
              <TableBody>
                <TableRow>
                  <TableCell><strong>Target Percentile Range</strong></TableCell>
                  <TableCell>{optimalExit.exit_percentile_target.percentile_range}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>Expected Return</strong></TableCell>
                  <TableCell>
                    {optimalExit.exit_percentile_target.actual_return.toFixed(2)}%
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>Success Rate</strong></TableCell>
                  <TableCell>
                    {(optimalExit.exit_percentile_target.success_rate * 100).toFixed(1)}%
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>Sample Size</strong></TableCell>
                  <TableCell>
                    {optimalExit.exit_percentile_target.sample_size}
                    {' '}
                    <Chip
                      label={optimalExit.exit_percentile_target.confidence}
                      size="small"
                      color={getConfidenceColor(optimalExit.exit_percentile_target.confidence)}
                    />
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {/* Efficiency Rankings */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Efficiency Rankings (Top 5)
        </Typography>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Rank</TableCell>
                <TableCell>Day</TableCell>
                <TableCell align="right">Efficiency (%/day)</TableCell>
                <TableCell align="right">Total Return (%)</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {optimalExit.efficiency_rankings.slice(0, 5).map((ranking, index) => (
                <TableRow
                  key={ranking.day}
                  sx={{
                    bgcolor: ranking.day === optimalExit.optimal_day
                      ? 'success.light'
                      : 'transparent',
                  }}
                >
                  <TableCell>
                    {ranking.day === optimalExit.optimal_day ? '⭐' : index + 1}
                  </TableCell>
                  <TableCell>
                    <strong>D{ranking.day}</strong>
                  </TableCell>
                  <TableCell align="right">
                    {ranking.efficiency.toFixed(3)}
                  </TableCell>
                  <TableCell align="right">
                    {ranking.total_return > 0 ? '+' : ''}
                    {ranking.total_return.toFixed(2)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>

      {/* Trend Analysis */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Statistical Trend Analysis
        </Typography>
        <Box sx={{ pl: 2 }}>
          <Typography variant="body2" gutterBottom>
            • Trend Direction: <strong>{trendAnalysis.trend_direction}</strong>
            {' '}({getTrendIndicator()})
          </Typography>
          <Typography variant="body2" gutterBottom>
            • Correlation: <strong>{trendAnalysis.trend_correlation.toFixed(3)}</strong>
            {' '}(p={trendAnalysis.trend_p_value.toFixed(4)})
          </Typography>
          <Typography variant="body2" gutterBottom>
            • Peak Day: <strong>D{trendAnalysis.peak_day}</strong>
            {' '}({trendAnalysis.peak_return.toFixed(2)}% return)
          </Typography>
          <Typography variant="body2" gutterBottom>
            • Early vs Late: <strong>{trendAnalysis.early_vs_late_significance}</strong>
            {' '}(p={trendAnalysis.early_vs_late_p_value.toFixed(4)})
          </Typography>
        </Box>
      </Box>

      {/* Risk Summary */}
      <Box>
        <Typography variant="h6" gutterBottom>
          Risk Summary
        </Typography>
        <Box sx={{ pl: 2 }}>
          <Typography variant="body2" gutterBottom>
            • Median Drawdown: <strong>{riskMetrics.median_drawdown.toFixed(2)}%</strong>
          </Typography>
          <Typography variant="body2" gutterBottom>
            • P90 Drawdown: <strong>{riskMetrics.p90_drawdown.toFixed(2)}%</strong>
          </Typography>
          <Typography variant="body2" gutterBottom>
            • Max Consecutive Losses: <strong>{riskMetrics.max_consecutive_losses}</strong>
          </Typography>
          <Typography variant="body2" gutterBottom>
            • Recovery Rate: <strong>{(riskMetrics.recovery_rate * 100).toFixed(1)}%</strong>
            {' '}({riskMetrics.median_recovery_days.toFixed(0)} days median)
          </Typography>
        </Box>
      </Box>
    </Paper>
  );
};

export default OptimalExitPanel;
