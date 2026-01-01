/**
 * Current Market State Component
 *
 * Shows LIVE RSI-MA percentile and risk-adjusted expectancy for all tickers
 * Highlights buy opportunities based on current market conditions
 * WITH SORTABLE COLUMNS AND DATA FOR ALL PERCENTILE RANGES
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
  TableSortLabel,
} from '@mui/material';
import {
  TrendingDown,
  TrendingUp,
  CheckCircle,
  Warning,
  Info,
  Cancel,
  ArrowUpward,
  ArrowDownward,
} from '@mui/icons-material';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';
type Timeframe = 'daily' | '4hour';

interface LiveExpectancy {
  expected_win_rate: number;
  expected_return_pct: number;
  expected_holding_days: number;
  expected_return_per_day_pct: number;
  risk_adjusted_expectancy_pct: number;
  sample_size: number;
}

interface MarketState {
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
  live_expectancy: LiveExpectancy;
}

interface MarketStateResponse {
  timestamp: string;
  market_state: MarketState[];
  summary: {
    total_tickers: number;
    in_entry_zone: number;
    extreme_low_opportunities: number;
    low_opportunities: number;
  };
}

type SortField = 'ticker' | 'percentile' | 'win_rate' | 'return' | 'risk_adj_expectancy' | 'hold_days';
type SortOrder = 'asc' | 'desc';

interface CurrentMarketStateProps {
  timeframe?: Timeframe;
}

export const CurrentMarketState: React.FC<CurrentMarketStateProps> = ({ timeframe = 'daily' }) => {
  const [dailyData, setDailyData] = useState<MarketStateResponse | null>(null);
  const [fourHourData, setFourHourData] = useState<MarketStateResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField>('percentile');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');

  const fetchCurrentState = async (target: Timeframe, refresh: boolean = false) => {
    if (!refresh) {
      setLoading(true);
    }
    setError(null);

    try {
      const endpoint =
        target === '4hour'
          ? `${API_BASE_URL}/api/swing-framework/current-state-4h`
          : `${API_BASE_URL}/api/swing-framework/current-state`;
      const response = await axios.get<MarketStateResponse>(endpoint);
      if (target === '4hour') {
        setFourHourData(response.data);
      } else {
        setDailyData(response.data);
      }
      console.log(`✅ ${target === '4hour' ? '4H' : 'Daily'} current market state loaded:`, response.data.summary);
    } catch (err: any) {
      console.error('❌ Error fetching current state:', err);
      setError(err.message || 'Failed to fetch current market state');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const hasData = timeframe === '4hour' ? fourHourData : dailyData;

    if (!hasData) {
      fetchCurrentState(timeframe);
    } else {
      setLoading(false);
      setError(null);
    }

    // Refresh every 5 minutes
    const interval = setInterval(() => fetchCurrentState(timeframe, true), 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [timeframe]); // eslint-disable-line react-hooks/exhaustive-deps

  const marketData = timeframe === '4hour' ? fourHourData : dailyData;

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      // Toggle sort order
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      // New field - default to ascending
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const getSortedData = (data: MarketState[]): MarketState[] => {
    const sorted = [...data].sort((a, b) => {
      let aValue: number | string;
      let bValue: number | string;

      switch (sortField) {
        case 'ticker':
          aValue = a.ticker;
          bValue = b.ticker;
          break;
        case 'percentile':
          aValue = a.current_percentile;
          bValue = b.current_percentile;
          break;
        case 'win_rate':
          aValue = a.live_expectancy.expected_win_rate;
          bValue = b.live_expectancy.expected_win_rate;
          break;
        case 'return':
          aValue = a.live_expectancy.expected_return_pct;
          bValue = b.live_expectancy.expected_return_pct;
          break;
        case 'risk_adj_expectancy':
          aValue = a.live_expectancy.risk_adjusted_expectancy_pct;
          bValue = b.live_expectancy.risk_adjusted_expectancy_pct;
          break;
        case 'hold_days':
          aValue = a.live_expectancy.expected_holding_days;
          bValue = b.live_expectancy.expected_holding_days;
          break;
        default:
          aValue = a.current_percentile;
          bValue = b.current_percentile;
      }

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortOrder === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      return sortOrder === 'asc'
        ? (aValue as number) - (bValue as number)
        : (bValue as number) - (aValue as number);
    });

    return sorted;
  };

  const getBuySignalIcon = (state: MarketState) => {
    const percentile = state.current_percentile;

    if (percentile <= 5) {
      return (
        <Tooltip title="Strong Buy - Extreme Low (≤5%)">
          <CheckCircle color="success" fontSize="small" />
        </Tooltip>
      );
    } else if (percentile <= 15) {
      return (
        <Tooltip title="Buy - Low (5-15%)">
          <Warning color="warning" fontSize="small" />
        </Tooltip>
      );
    } else {
      return (
        <Tooltip title="Not in Entry Zone (>15%)">
          <Cancel color="error" fontSize="small" />
        </Tooltip>
      );
    }
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

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
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

  if (!marketData) {
    return null;
  }

  const { market_state, summary } = marketData;
  const sortedData = getSortedData(market_state);

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
        <Typography variant="h5" fontWeight="bold">
          🎯 Live Market State - {timeframe === '4hour' ? '4-Hour' : 'Daily'} Buy Opportunities (Stocks + Indices)
        </Typography>
        <Box display="flex" alignItems="center" gap={1}>
          <Tooltip
            title={
              timeframe === '4hour'
                ? 'Using 4-hour RSI-MA percentiles and intraday bin statistics'
                : 'Using daily RSI-MA percentiles and daily bin statistics'
            }
          >
            <Chip
              label={timeframe === '4hour' ? '4-Hour timeframe' : 'Daily timeframe'}
              color={timeframe === '4hour' ? 'secondary' : 'primary'}
              size="small"
            />
          </Tooltip>
          <Typography variant="caption" color="text.secondary">
            Updated: {new Date(marketData.timestamp).toLocaleString()}
          </Typography>
        </Box>
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
              <TableCell>
                <TableSortLabel
                  active={sortField === 'ticker'}
                  direction={sortField === 'ticker' ? sortOrder : 'asc'}
                  onClick={() => handleSort('ticker')}
                >
                  Ticker
                </TableSortLabel>
              </TableCell>
              <TableCell>Signal</TableCell>
              <TableCell align="right">
                <TableSortLabel
                  active={sortField === 'percentile'}
                  direction={sortField === 'percentile' ? sortOrder : 'asc'}
                  onClick={() => handleSort('percentile')}
                >
                  Current %ile
                </TableSortLabel>
              </TableCell>
              <TableCell>Zone</TableCell>
              <TableCell>Regime</TableCell>
              <TableCell align="right">
                <TableSortLabel
                  active={sortField === 'win_rate'}
                  direction={sortField === 'win_rate' ? sortOrder : 'asc'}
                  onClick={() => handleSort('win_rate')}
                >
                  Expected Win Rate
                </TableSortLabel>
              </TableCell>
              <TableCell align="right">
                <TableSortLabel
                  active={sortField === 'return'}
                  direction={sortField === 'return' ? sortOrder : 'asc'}
                  onClick={() => handleSort('return')}
                >
                  Expected Return
                </TableSortLabel>
              </TableCell>
              <TableCell align="right">
                <TableSortLabel
                  active={sortField === 'risk_adj_expectancy'}
                  direction={sortField === 'risk_adj_expectancy' ? sortOrder : 'asc'}
                  onClick={() => handleSort('risk_adj_expectancy')}
                >
                  Risk-Adj. Expectancy
                </TableSortLabel>
              </TableCell>
              <TableCell align="right">
                <TableSortLabel
                  active={sortField === 'hold_days'}
                  direction={sortField === 'hold_days' ? sortOrder : 'asc'}
                  onClick={() => handleSort('hold_days')}
                >
                  Avg Hold (days)
                </TableSortLabel>
              </TableCell>
              <TableCell align="right">Sample Size</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedData.map((state) => (
              <TableRow
                key={state.ticker}
                sx={{
                  backgroundColor: state.in_entry_zone
                    ? 'rgba(76, 175, 80, 0.08)'
                    : 'inherit',
                  '&:hover': {
                    backgroundColor: state.in_entry_zone
                      ? 'rgba(76, 175, 80, 0.15)'
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
                          : state.current_percentile.toFixed(0) + '%'
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
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Box mt={2}>
        <Alert severity="info" icon={<Info />}>
          <Typography variant="body2">
            <strong>Live Expectancy</strong> shows expected performance based on historical
            cohort statistics for the current percentile range ({timeframe === '4hour' ? '4H bars' : 'daily bars'}). Risk-adjusted expectancy
            accounts for volatility level ({' '}
            <Tooltip title="Low volatility stocks get full value, medium = 1.5x divisor, high = 2.0x">
              <span style={{ textDecoration: 'underline', cursor: 'help' }}>volatility adjustment</span>
            </Tooltip>
            ). <strong>Click column headers to sort.</strong>
          </Typography>
        </Alert>
      </Box>
    </Paper>
  );
};

export default CurrentMarketState;
