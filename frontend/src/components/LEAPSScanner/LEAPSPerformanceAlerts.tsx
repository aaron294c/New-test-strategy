/**
 * LEAPS Performance & Alerts Component
 *
 * Displays historical backtest performance and real-time trading alerts.
 */

import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Alert,
  Chip,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  Stack,
  Divider,
} from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import WarningIcon from '@mui/icons-material/Warning';
import InfoIcon from '@mui/icons-material/Info';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

// Backend API base URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Type definitions
interface RegimeStats {
  total_trades: number;
  win_rate: number;
  avg_return: number;
  median_return: number;
  best_return: number;
  worst_return: number;
  std_dev: number;
  sharpe_ratio: number;
  avg_days_held: number;
  regime_name: string;
}

interface BacktestData {
  regimes: {
    LOW: { stats: RegimeStats };
    MODERATE: { stats: RegimeStats };
    HIGH: { stats: RegimeStats };
  };
  overall: {
    total_trades: number;
    avg_return: number;
    win_rate: number;
  };
  current_vix: number;
  current_regime: string;
  current_percentile: number;
  recommendations: Array<{
    priority: string;
    title: string;
    description: string;
    action: string;
  }>;
  analysis_period: string;
  timestamp: string;
}

interface AlertData {
  alerts: Array<{
    severity: string;
    type: string;
    title: string;
    message: string;
    action: string;
  }>;
  alert_count: number;
  current_vix: number;
  current_percentile: number;
  current_strategy: string;
  timestamp: string;
}

// Fetch functions
const fetchBacktest = async (): Promise<BacktestData> => {
  const response = await axios.get(`${API_BASE_URL}/api/leaps/backtest?years=5`);
  return response.data;
};

const fetchAlerts = async (): Promise<AlertData> => {
  const response = await axios.get(`${API_BASE_URL}/api/leaps/alerts`);
  return response.data;
};

// Helper functions
const getSeverityColor = (severity: string) => {
  switch (severity.toUpperCase()) {
    case 'HIGH': return 'error';
    case 'MEDIUM': return 'warning';
    case 'LOW': return 'info';
    default: return 'default';
  }
};

const getSeverityIcon = (severity: string) => {
  switch (severity.toUpperCase()) {
    case 'HIGH': return <WarningIcon />;
    case 'MEDIUM': return <InfoIcon />;
    default: return <InfoIcon />;
  }
};

const formatPercent = (value: number) => `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;

export const LEAPSPerformanceAlerts: React.FC = () => {
  const { data: backtestData, isLoading: loadingBacktest } = useQuery({
    queryKey: ['leaps-backtest'],
    queryFn: fetchBacktest,
    staleTime: 30 * 60 * 1000, // 30 minutes
  });

  const { data: alertsData, isLoading: loadingAlerts } = useQuery({
    queryKey: ['leaps-alerts'],
    queryFn: fetchAlerts,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 2 * 60 * 1000, // Auto-refresh every 2 minutes
  });

  if (loadingBacktest || loadingAlerts) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (!backtestData || !alertsData) return null;

  return (
    <Box sx={{ width: '100%' }}>
      {/* Alerts Section */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          Active Alerts
          <Chip
            label={`${alertsData.alert_count} Alert${alertsData.alert_count !== 1 ? 's' : ''}`}
            color={alertsData.alert_count > 0 ? 'warning' : 'success'}
            size="small"
            sx={{ ml: 2 }}
          />
        </Typography>

        {alertsData.alerts.length === 0 ? (
          <Alert severity="success" sx={{ mt: 2 }}>
            No active alerts. Market conditions are stable.
          </Alert>
        ) : (
          <Stack spacing={2} sx={{ mt: 2 }}>
            {alertsData.alerts.map((alert, index) => (
              <Alert
                key={index}
                severity={getSeverityColor(alert.severity) as any}
                icon={getSeverityIcon(alert.severity)}
              >
                <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                  {alert.title}
                </Typography>
                <Typography variant="body2" sx={{ mt: 0.5 }}>
                  {alert.message}
                </Typography>
                <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic', color: 'text.secondary' }}>
                  → {alert.action}
                </Typography>
              </Alert>
            ))}
          </Stack>
        )}
      </Box>

      <Divider sx={{ my: 4 }} />

      {/* Backtest Results Section */}
      <Typography variant="h5" gutterBottom>
        Historical Performance Analysis
        <Chip label={backtestData.analysis_period} size="small" sx={{ ml: 2 }} />
      </Typography>

      {/* Current Status */}
      <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #1E222D 0%, #2A2E3A 100%)' }}>
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2" color="text.secondary">Current VIX</Typography>
              <Typography variant="h4">{backtestData.current_vix.toFixed(2)}</Typography>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2" color="text.secondary">Regime</Typography>
              <Typography variant="h4">{backtestData.current_regime}</Typography>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2" color="text.secondary">Overall Win Rate</Typography>
              <Typography variant="h4" sx={{ color: '#4caf50' }}>
                {backtestData.overall.win_rate.toFixed(1)}%
              </Typography>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2" color="text.secondary">Total Trades</Typography>
              <Typography variant="h4">{backtestData.overall.total_trades}</Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Performance by Regime Table */}
      <TableContainer component={Paper} sx={{ mb: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>VIX Regime</TableCell>
              <TableCell align="right">Trades</TableCell>
              <TableCell align="right">Win Rate</TableCell>
              <TableCell align="right">Avg Return</TableCell>
              <TableCell align="right">Best/Worst</TableCell>
              <TableCell align="right">Sharpe</TableCell>
              <TableCell>Risk Profile</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.values(backtestData.regimes).map((regime) => {
              const stats = regime.stats;
              const isCurrent = stats.regime_name === backtestData.current_regime;

              return (
                <TableRow key={stats.regime_name} sx={{ bgcolor: isCurrent ? '#1E222D' : 'transparent' }}>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" sx={{ fontWeight: isCurrent ? 'bold' : 'normal' }}>
                        {stats.regime_name}
                      </Typography>
                      {isCurrent && <Chip label="Current" size="small" color="primary" />}
                    </Box>
                  </TableCell>
                  <TableCell align="right">{stats.total_trades}</TableCell>
                  <TableCell align="right">
                    <Chip
                      label={`${stats.win_rate.toFixed(1)}%`}
                      color={stats.win_rate >= 65 ? 'success' : stats.win_rate >= 55 ? 'warning' : 'error'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Typography
                      variant="body2"
                      sx={{
                        color: stats.avg_return > 0 ? '#4caf50' : '#f44336',
                        fontWeight: 'bold'
                      }}
                    >
                      {formatPercent(stats.avg_return)}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="caption" sx={{ display: 'block', color: '#4caf50' }}>
                      {formatPercent(stats.best_return)}
                    </Typography>
                    <Typography variant="caption" sx={{ display: 'block', color: '#f44336' }}>
                      {formatPercent(stats.worst_return)}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2">{stats.sharpe_ratio.toFixed(2)}</Typography>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ width: '100%' }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                        Volatility: {stats.std_dev.toFixed(1)}%
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={Math.min((stats.std_dev / 30) * 100, 100)}
                        sx={{
                          height: 6,
                          borderRadius: 1,
                          bgcolor: '#424242',
                          '& .MuiLinearProgress-bar': {
                            bgcolor: stats.std_dev < 15 ? '#4caf50' : stats.std_dev < 20 ? '#ff9800' : '#f44336'
                          }
                        }}
                      />
                    </Box>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Recommendations */}
      <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>
        Actionable Recommendations
      </Typography>
      <Grid container spacing={2}>
        {backtestData.recommendations.map((rec, index) => (
          <Grid item xs={12} md={4} key={index}>
            <Card sx={{ height: '100%', bgcolor: '#1E222D' }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                    {rec.title}
                  </Typography>
                  <Chip
                    label={rec.priority}
                    size="small"
                    color={rec.priority === 'HIGH' ? 'error' : rec.priority === 'MEDIUM' ? 'warning' : 'info'}
                  />
                </Box>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {rec.description}
                </Typography>
                <Divider sx={{ my: 1.5 }} />
                <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                  {rec.action}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Footer */}
      <Box sx={{ mt: 3, textAlign: 'center' }}>
        <Typography variant="caption" color="text.secondary">
          Backtest data updated: {new Date(backtestData.timestamp).toLocaleString()}
          {' | '}
          Alerts updated: {new Date(alertsData.timestamp).toLocaleString()}
        </Typography>
      </Box>
    </Box>
  );
};

export default LEAPSPerformanceAlerts;
