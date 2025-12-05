/**
 * Index Market State Component - SPY and QQQ
 *
 * Shows LIVE RSI-MA percentile and risk-adjusted expectancy for market indices
 * Mirrors CurrentMarketState component structure for consistent UX
 */

import React, { useState, useEffect } from 'react';
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
  CircularProgress,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  TrendingDown,
  TrendingUp,
  CheckCircle,
  Warning,
  Info,
  ShowChart,
} from '@mui/icons-material';
import axios from 'axios';

const API_BASE_URL = '';

interface LiveExpectancy {
  expected_win_rate: number;
  expected_return_pct: number;
  expected_holding_days: number;
  expected_return_per_day_pct: number;
  risk_adjusted_expectancy_pct: number;
  sample_size: number;
}

interface IndexState {
  ticker: string;
  name: string;
  current_date: string;
  current_price: number;
  current_percentile: number;
  percentile_cohort: string;
  zone_label: string;
  in_entry_zone: boolean;
  regime: string;
  is_mean_reverter: boolean;
  is_momentum: boolean;
  volatility_level: string;
  live_expectancy: LiveExpectancy | null;
}

interface IndexStateResponse {
  timestamp: string;
  market_state: IndexState[];
  summary: {
    total_tickers: number;
    in_entry_zone: number;
    extreme_low_opportunities: number;
    low_opportunities: number;
  };
}

export const IndexMarketState: React.FC = () => {
  const [indexData, setIndexData] = useState<IndexStateResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchIndexState = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get<IndexStateResponse>(
        `${API_BASE_URL}/api/swing-framework/current-state-indices`
      );
      setIndexData(response.data);
      console.log('✅ Index market state loaded:', response.data.summary);
    } catch (err: any) {
      console.error('❌ Error fetching index state:', err);
      setError(err.message || 'Failed to fetch index market state');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIndexState();

    // Refresh every 5 minutes (same as stocks)
    const interval = setInterval(fetchIndexState, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ my: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!indexData) {
    return null;
  }

  const { market_state, summary } = indexData;

  const getBuySignalIcon = (state: IndexState) => {
    if (!state.in_entry_zone) return null;

    if (state.percentile_cohort === 'extreme_low') {
      return <CheckCircle color="success" fontSize="small" />;
    }
    return <Warning color="warning" fontSize="small" />;
  };

  const getPercentileColor = (percentile: number) => {
    if (percentile <= 5) return '#4caf50'; // Green - strong buy
    if (percentile <= 15) return '#ff9800'; // Orange - buy
    if (percentile <= 30) return '#2196f3'; // Blue - watch
    return '#9e9e9e'; // Gray - neutral
  };

  const getExpectancyColor = (expectancy: number) => {
    if (expectancy > 0.4) return '#4caf50'; // Green - excellent
    if (expectancy > 0.2) return '#8bc34a'; // Light green - good
    if (expectancy > 0) return '#ff9800'; // Orange - marginal
    return '#f44336'; // Red - negative
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3, bgcolor: '#f5f5f5' }}>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
        <Box display="flex" alignItems="center" gap={1}>
          <ShowChart color="primary" />
          <Typography variant="h5" fontWeight="bold">
            📊 Market Indices - SPY & QQQ CurrentBuy Opportunities
          </Typography>
        </Box>
        <Typography variant="caption" color="text.secondary">
          Updated: {new Date(indexData.timestamp).toLocaleString()}
        </Typography>
      </Box>

      <Box display="flex" gap={2} mb={3}>
        <Chip
          icon={<TrendingDown />}
          label={`${summary.extreme_low_opportunities} Extreme Low (≤5%)`}
          color="success"
          variant={summary.extreme_low_opportunities > 0 ? 'filled' : 'outlined'}
        />
        <Chip
          icon={<TrendingUp />}
          label={`${summary.low_opportunities} Low (5-15%)`}
          color="warning"
          variant={summary.low_opportunities > 0 ? 'filled' : 'outlined'}
        />
        <Chip
          icon={<Info />}
          label={`${summary.total_tickers - summary.in_entry_zone} Not in Entry Zone`}
          variant="outlined"
        />
      </Box>

      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Index</TableCell>
              <TableCell>Signal</TableCell>
              <TableCell align="right">Current %ile</TableCell>
              <TableCell>Zone</TableCell>
              <TableCell>Regime</TableCell>
              <TableCell align="right">Expected Win Rate</TableCell>
              <TableCell align="right">Expected Return</TableCell>
              <TableCell align="right">Risk-Adj. Expectancy</TableCell>
              <TableCell align="right">Avg Hold (days)</TableCell>
              <TableCell align="right">Sample Size</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {market_state.map((state) => (
              <TableRow
                key={state.ticker}
                sx={{
                  backgroundColor: state.in_entry_zone
                    ? 'rgba(76, 175, 80, 0.12)'
                    : 'inherit',
                  '&:hover': {
                    backgroundColor: state.in_entry_zone
                      ? 'rgba(76, 175, 80, 0.20)'
                      : 'rgba(0, 0, 0, 0.04)',
                  },
                }}
              >
                <TableCell>
                  <Box>
                    <Typography variant="body2" fontWeight="bold">
                      {state.ticker}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      ${state.current_price.toFixed(2)}
                    </Typography>
                  </Box>
                </TableCell>

                <TableCell>
                  {getBuySignalIcon(state)}
                </TableCell>

                <TableCell align="right">
                  <Typography
                    variant="body2"
                    fontWeight="bold"
                    sx={{ color: getPercentileColor(state.current_percentile) }}
                  >
                    {state.current_percentile.toFixed(1)}%
                  </Typography>
                </TableCell>

                <TableCell>
                  <Tooltip title={state.zone_label}>
                    <Chip
                      label={
                        state.percentile_cohort === 'extreme_low'
                          ? '≤5%'
                          : state.percentile_cohort === 'low'
                          ? '5-15%'
                          : 'N/A'
                      }
                      size="small"
                      color={
                        state.percentile_cohort === 'extreme_low'
                          ? 'success'
                          : state.percentile_cohort === 'low'
                          ? 'warning'
                          : 'default'
                      }
                    />
                  </Tooltip>
                </TableCell>

                <TableCell>
                  <Chip
                    label={state.is_mean_reverter ? 'Mean Rev' : 'Momentum'}
                    size="small"
                    variant="outlined"
                  />
                </TableCell>

                {state.live_expectancy ? (
                  <>
                    <TableCell align="right">
                      <Typography variant="body2">
                        {(state.live_expectancy.expected_win_rate * 100).toFixed(1)}%
                      </Typography>
                    </TableCell>

                    <TableCell align="right">
                      <Typography
                        variant="body2"
                        sx={{
                          color:
                            state.live_expectancy.expected_return_pct > 0
                              ? '#4caf50'
                              : '#f44336',
                        }}
                      >
                        {state.live_expectancy.expected_return_pct > 0 ? '+' : ''}
                        {state.live_expectancy.expected_return_pct.toFixed(2)}%
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {state.live_expectancy.expected_return_per_day_pct > 0 ? '+' : ''}
                        {state.live_expectancy.expected_return_per_day_pct.toFixed(3)}%/day
                      </Typography>
                    </TableCell>

                    <TableCell align="right">
                      <Typography
                        variant="body2"
                        fontWeight="bold"
                        sx={{
                          color: getExpectancyColor(
                            state.live_expectancy.risk_adjusted_expectancy_pct
                          ),
                        }}
                      >
                        {state.live_expectancy.risk_adjusted_expectancy_pct > 0 ? '+' : ''}
                        {state.live_expectancy.risk_adjusted_expectancy_pct.toFixed(2)}%
                      </Typography>
                    </TableCell>

                    <TableCell align="right">
                      <Typography variant="body2">
                        {state.live_expectancy.expected_holding_days.toFixed(1)}
                      </Typography>
                    </TableCell>

                    <TableCell align="right">
                      <Typography variant="body2" color="text.secondary">
                        n={state.live_expectancy.sample_size}
                      </Typography>
                    </TableCell>
                  </>
                ) : (
                  <>
                    <TableCell align="center" colSpan={5}>
                      <Typography variant="caption" color="text.secondary">
                        Not in entry zone - no expected performance data
                      </Typography>
                    </TableCell>
                  </>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Box mt={2}>
        <Alert severity="info" icon={<Info />}>
          <Typography variant="body2">
            <strong>Index Tracking:</strong> SPY tracks S&P 500 (broad market), QQQ tracks Nasdaq 100 (tech-heavy).
            Both follow the same RSI-MA mean reversion logic as individual stocks. Buy signals at ≤15% percentile
            indicate market-wide dip opportunities with historically positive risk-adjusted expectancy.
          </Typography>
        </Alert>
      </Box>
    </Paper>
  );
};

export default IndexMarketState;
