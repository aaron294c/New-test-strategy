/**
 * Position Management Component
 *
 * Displays concrete, actionable position management recommendations based on
 * divergence-convergence analysis.
 *
 * Answers:
 * - Should I take partial profits? How much?
 * - What divergence gap triggers action?
 * - When should I re-enter after taking profits?
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Box,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Grid,
  Chip,
  LinearProgress,
  Divider,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Warning,
  CheckCircle,
  Info,
  MonetizationOn,
  ShowChart,
} from '@mui/icons-material';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface CurrentState {
  daily_percentile: number;
  hourly_4h_percentile: number;
  divergence_gap: number;
  divergence_state: string;
}

interface Recommendation {
  action: string;
  position_change_pct: number;
  confidence: number;
  rationale: string;
  expected_return_if_action: number;
  expected_return_if_hold: number;
  win_rate: number;
  max_risk: number;
  max_reward: number;
  sample_size: number;
}

interface ProfitRule {
  min_divergence_gap: number;
  max_divergence_gap: number;
  take_profit_pct: number;
  rationale: string;
  stats: {
    sample_size: number;
    avg_return_7d: number;
    avg_return_14d: number;
    win_rate: number;
    avg_max_drawdown: number;
    avg_max_upside: number;
    avg_time_to_convergence_days: number;
  };
}

interface ReentryRule {
  condition: string;
  action: string;
  rationale: string;
  stats: {
    sample_size: number;
    avg_return_7d: number;
    win_rate: number;
  };
}

interface PositionManagementData {
  ticker: string;
  current_state: CurrentState;
  recommendation: Recommendation;
  profit_taking_rules: Record<string, ProfitRule>;
  reentry_rules: Record<string, ReentryRule>;
}

interface PositionManagementProps {
  ticker: string;
}

export const PositionManagement: React.FC<PositionManagementProps> = ({ ticker }) => {
  const [data, setData] = useState<PositionManagementData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await axios.get(
          `${API_BASE_URL}/api/position-management/${ticker}`
        );
        setData(response.data.position_management);
      } catch (err: any) {
        setError(err.response?.data?.detail || err.message || 'Failed to fetch data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [ticker]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!data) {
    return (
      <Alert severity="info" sx={{ m: 2 }}>
        No position management data available
      </Alert>
    );
  }

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'TAKE_PROFIT':
        return <MonetizationOn sx={{ fontSize: 40, color: '#4caf50' }} />;
      case 'ADD_POSITION':
        return <TrendingUp sx={{ fontSize: 40, color: '#2196f3' }} />;
      case 'EXIT_ALL':
        return <Warning sx={{ fontSize: 40, color: '#f44336' }} />;
      case 'REDUCE':
        return <TrendingDown sx={{ fontSize: 40, color: '#ff9800' }} />;
      default:
        return <CheckCircle sx={{ fontSize: 40, color: '#9e9e9e' }} />;
    }
  };

  const getActionColor = (action: string): 'success' | 'error' | 'warning' | 'info' | 'default' => {
    switch (action) {
      case 'TAKE_PROFIT':
        return 'success';
      case 'ADD_POSITION':
        return 'info';
      case 'EXIT_ALL':
        return 'error';
      case 'REDUCE':
        return 'warning';
      default:
        return 'default';
    }
  };

  const { current_state, recommendation, profit_taking_rules, reentry_rules } = data;

  return (
    <Box className="p-6">
      {/* Current Action Recommendation */}
      <Card className="mb-6 bg-gradient-to-br from-slate-900 to-slate-800 border-2 border-blue-500">
        <CardContent>
          <Typography variant="h4" className="text-white mb-4 flex items-center gap-3">
            <ShowChart /> Position Management: {ticker}
          </Typography>

          <Grid container spacing={3}>
            {/* Action Card */}
            <Grid item xs={12} md={6}>
              <Paper className="p-6 bg-gradient-to-br from-blue-900 to-indigo-900">
                <Box className="flex items-center gap-4 mb-4">
                  {getActionIcon(recommendation.action)}
                  <Box>
                    <Typography variant="h5" className="text-white font-bold">
                      {recommendation.action.replace('_', ' ')}
                    </Typography>
                    <Typography variant="body2" className="text-gray-300">
                      Position Change: {recommendation.position_change_pct > 0 ? '+' : ''}
                      {recommendation.position_change_pct}%
                    </Typography>
                  </Box>
                </Box>

                <Divider sx={{ bgcolor: 'rgba(255,255,255,0.2)', my: 2 }} />

                <Typography variant="body1" className="text-gray-200 mb-3">
                  {recommendation.rationale}
                </Typography>

                <Box className="mt-4">
                  <Typography variant="body2" className="text-gray-400 mb-1">
                    Confidence Level
                  </Typography>
                  <Box className="flex items-center gap-2">
                    <LinearProgress
                      variant="determinate"
                      value={recommendation.confidence}
                      sx={{
                        flex: 1,
                        height: 10,
                        borderRadius: 5,
                        bgcolor: 'rgba(255,255,255,0.1)',
                        '& .MuiLinearProgress-bar': {
                          bgcolor: recommendation.confidence > 70 ? '#4caf50' : '#ff9800',
                        },
                      }}
                    />
                    <Typography variant="body2" className="text-white font-bold">
                      {Math.round(recommendation.confidence)}%
                    </Typography>
                  </Box>
                  <Typography variant="caption" className="text-gray-400">
                    Based on {recommendation.sample_size} historical events
                  </Typography>
                </Box>
              </Paper>
            </Grid>

            {/* Current State & Metrics */}
            <Grid item xs={12} md={6}>
              <Paper className="p-6 bg-gradient-to-br from-purple-900 to-pink-900">
                <Typography variant="h6" className="text-white mb-3">
                  Current Market State
                </Typography>

                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2" className="text-gray-300">
                      Daily Percentile
                    </Typography>
                    <Typography variant="h6" className="text-white font-bold">
                      {current_state.daily_percentile.toFixed(1)}%
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" className="text-gray-300">
                      4H Percentile
                    </Typography>
                    <Typography variant="h6" className="text-white font-bold">
                      {current_state.hourly_4h_percentile.toFixed(1)}%
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" className="text-gray-300">
                      Divergence Gap
                    </Typography>
                    <Typography variant="h6" className="text-white font-bold">
                      {current_state.divergence_gap.toFixed(1)}%
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" className="text-gray-300">
                      State
                    </Typography>
                    <Chip
                      label={current_state.divergence_state.replace('_', ' ').toUpperCase()}
                      size="small"
                      color={
                        current_state.divergence_state === 'aligned'
                          ? 'success'
                          : 'warning'
                      }
                    />
                  </Grid>
                </Grid>

                <Divider sx={{ bgcolor: 'rgba(255,255,255,0.2)', my: 2 }} />

                <Typography variant="h6" className="text-white mb-2">
                  Expected Outcomes (7 days)
                </Typography>

                <Box className="space-y-2">
                  <Box className="flex justify-between items-center">
                    <Typography variant="body2" className="text-gray-300">
                      If take action:
                    </Typography>
                    <Typography
                      variant="body1"
                      className={`font-bold ${
                        recommendation.expected_return_if_action > 0
                          ? 'text-green-400'
                          : 'text-red-400'
                      }`}
                    >
                      {recommendation.expected_return_if_action > 0 ? '+' : ''}
                      {recommendation.expected_return_if_action.toFixed(2)}%
                    </Typography>
                  </Box>
                  <Box className="flex justify-between items-center">
                    <Typography variant="body2" className="text-gray-300">
                      If hold:
                    </Typography>
                    <Typography
                      variant="body1"
                      className={`font-bold ${
                        recommendation.expected_return_if_hold > 0
                          ? 'text-green-400'
                          : 'text-red-400'
                      }`}
                    >
                      {recommendation.expected_return_if_hold > 0 ? '+' : ''}
                      {recommendation.expected_return_if_hold.toFixed(2)}%
                    </Typography>
                  </Box>
                  <Box className="flex justify-between items-center">
                    <Typography variant="body2" className="text-gray-300">
                      Win Rate:
                    </Typography>
                    <Typography variant="body1" className="text-white font-bold">
                      {recommendation.win_rate.toFixed(1)}%
                    </Typography>
                  </Box>
                  <Box className="flex justify-between items-center">
                    <Typography variant="body2" className="text-gray-300">
                      Risk / Reward:
                    </Typography>
                    <Typography variant="body1" className="text-white font-bold">
                      {recommendation.max_risk.toFixed(1)}% / +
                      {recommendation.max_reward.toFixed(1)}%
                    </Typography>
                  </Box>
                </Box>
              </Paper>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Profit Taking Rules */}
      {Object.keys(profit_taking_rules).length > 0 && (
        <Card className="mb-6 bg-slate-800">
          <CardContent>
            <Typography variant="h5" className="text-white mb-4 flex items-center gap-2">
              <MonetizationOn /> Profit Taking Rules by Divergence Gap
            </Typography>
            <Typography variant="body2" className="text-gray-400 mb-4">
              Historical analysis: When 4H overextends above Daily, how much profit should you take?
            </Typography>

            <TableContainer component={Paper} className="bg-slate-900">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell className="text-white font-bold">Divergence Gap</TableCell>
                    <TableCell className="text-white font-bold">Take Profit %</TableCell>
                    <TableCell className="text-white font-bold">Avg 7d Return</TableCell>
                    <TableCell className="text-white font-bold">Win Rate</TableCell>
                    <TableCell className="text-white font-bold">Max Risk</TableCell>
                    <TableCell className="text-white font-bold">Convergence Time</TableCell>
                    <TableCell className="text-white font-bold">Sample Size</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.values(profit_taking_rules).map((rule, idx) => (
                    <TableRow key={idx} hover>
                      <TableCell className="text-white">
                        {rule.min_divergence_gap}% - {rule.max_divergence_gap}%
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={`${rule.take_profit_pct}%`}
                          color={
                            rule.take_profit_pct >= 75
                              ? 'error'
                              : rule.take_profit_pct >= 50
                              ? 'warning'
                              : 'success'
                          }
                          size="small"
                        />
                      </TableCell>
                      <TableCell
                        className={
                          rule.stats.avg_return_7d > 0 ? 'text-green-400' : 'text-red-400'
                        }
                      >
                        {rule.stats.avg_return_7d > 0 ? '+' : ''}
                        {rule.stats.avg_return_7d.toFixed(2)}%
                      </TableCell>
                      <TableCell className="text-white">
                        {rule.stats.win_rate.toFixed(1)}%
                      </TableCell>
                      <TableCell className="text-red-400">
                        {rule.stats.avg_max_drawdown.toFixed(2)}%
                      </TableCell>
                      <TableCell className="text-gray-300">
                        {rule.stats.avg_time_to_convergence_days.toFixed(1)} days
                      </TableCell>
                      <TableCell className="text-gray-400">
                        n={rule.stats.sample_size}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Re-entry Rules */}
      {Object.keys(reentry_rules).length > 0 && (
        <Card className="bg-slate-800">
          <CardContent>
            <Typography variant="h5" className="text-white mb-4 flex items-center gap-2">
              <TrendingUp /> Re-Entry Rules After Convergence
            </Typography>
            <Typography variant="body2" className="text-gray-400 mb-4">
              When to add back position after divergence normalizes
            </Typography>

            <Grid container spacing={3}>
              {Object.entries(reentry_rules).map(([key, rule]) => (
                <Grid item xs={12} md={4} key={key}>
                  <Paper className="p-4 bg-gradient-to-br from-green-900 to-teal-900 h-full">
                    <Typography variant="h6" className="text-white mb-2">
                      {key.replace('convergence_', '').toUpperCase()}
                    </Typography>
                    <Divider sx={{ bgcolor: 'rgba(255,255,255,0.2)', my: 2 }} />

                    <Typography variant="body2" className="text-gray-300 mb-2">
                      <strong>Condition:</strong> {rule.condition}
                    </Typography>

                    <Typography variant="body2" className="text-gray-300 mb-2">
                      <strong>Action:</strong> {rule.action}
                    </Typography>

                    <Typography variant="body2" className="text-gray-300 mb-3">
                      {rule.rationale}
                    </Typography>

                    <Box className="flex justify-between text-sm">
                      <Typography variant="caption" className="text-gray-400">
                        Win Rate: {rule.stats.win_rate.toFixed(1)}%
                      </Typography>
                      <Typography variant="caption" className="text-gray-400">
                        n={rule.stats.sample_size}
                      </Typography>
                    </Box>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default PositionManagement;
