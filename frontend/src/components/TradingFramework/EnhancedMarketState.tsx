/**
 * Enhanced Market State Component
 *
 * Shows LIVE RSI-MA percentile + MULTI-TIMEFRAME DIVERGENCE + P85/P95 THRESHOLDS
 * Combines daily and 4-hour analysis for quick visualization of divergence setups
 * 
 * Features:
 * - Divergence % between Daily and 4-Hour
 * - Comparison against P85 (significant dislocation) and P95 (extreme dislocation) thresholds
 * - Divergence category labels: 4H Overextended, Bullish Convergence, Bearish Convergence, Daily Overextended
 * - Status indicators for quick reference
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
  Info,
  Cancel,
} from '@mui/icons-material';
import axios from 'axios';

const API_BASE_URL = '';

interface EnrichedMarketState {
  ticker: string;
  name: string;
  current_price: number;
  current_percentile: number;
  four_h_percentile: number;
  divergence_pct: number;
  abs_divergence_pct: number;
  divergence_category: string;
  category_label: string;
  category_description: string;
  p85_threshold: number;
  p95_threshold: number;
  dislocation_level: string;
  dislocation_color: string;
  thresholds_text: string;
  percentile_cohort: string;
  zone_label: string;
  regime: string;
  live_expectancy: {
    expected_win_rate: number;
    expected_return_pct: number;
    expected_holding_days: number;
    expected_return_per_day_pct: number;
    risk_adjusted_expectancy_pct: number;
    sample_size: number;
  };
}

interface EnrichedResponse {
  timestamp: string;
  market_state: EnrichedMarketState[];
  summary: {
    total_tickers: number;
    bullish_convergence: number;
    bearish_convergence: number;
    '4h_overextended': number;
    'daily_overextended': number;
    extreme_dislocation: number;
    significant_dislocation: number;
  };
}

type SortField = 'ticker' | 'divergence' | 'dislocation' | 'daily_pct' | '4h_pct' | 'category';
type SortOrder = 'asc' | 'desc';

export const EnhancedMarketState: React.FC = () => {
  const [data, setData] = useState<EnrichedResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField>('divergence');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const fetchEnrichedState = async (refresh: boolean = false) => {
    if (!refresh) {
      setLoading(true);
    }
    setError(null);

    try {
      const response = await axios.get<EnrichedResponse>(
        `${API_BASE_URL}/api/swing-framework/current-state-enriched`
      );
      setData(response.data);
      console.log('✅ Enhanced market state loaded:', response.data.summary);
    } catch (err: any) {
      console.error('❌ Error fetching enriched state:', err);
      setError(err.message || 'Failed to fetch enriched market state');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEnrichedState();
    // Refresh every 5 minutes
    const interval = setInterval(() => fetchEnrichedState(true), 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const getSortedData = (states: EnrichedMarketState[]): EnrichedMarketState[] => {
    const sorted = [...states].sort((a, b) => {
      let aValue: number | string;
      let bValue: number | string;

      switch (sortField) {
        case 'ticker':
          aValue = a.ticker;
          bValue = b.ticker;
          break;
        case 'divergence':
          aValue = a.abs_divergence_pct;
          bValue = b.abs_divergence_pct;
          break;
        case 'dislocation':
          const dislocations = { Normal: 0, 'Significant (P85)': 1, 'Extreme (P95)': 2 };
          aValue = dislocations[a.dislocation_level as keyof typeof dislocations] || 0;
          bValue = dislocations[b.dislocation_level as keyof typeof dislocations] || 0;
          break;
        case 'daily_pct':
          aValue = a.current_percentile;
          bValue = b.current_percentile;
          break;
        case '4h_pct':
          aValue = a.four_h_percentile;
          bValue = b.four_h_percentile;
          break;
        case 'category':
          aValue = a.divergence_category;
          bValue = b.divergence_category;
          break;
        default:
          aValue = a.abs_divergence_pct;
          bValue = b.abs_divergence_pct;
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

  const getDivergenceStatusColor = (_divergence: number, category: string) => {
    if (category === 'bullish_convergence') return '#4caf50'; // Green
    if (category === 'bearish_convergence') return '#f44336'; // Red
    if (category === '4h_overextended') return '#ff9800'; // Orange
    if (category === 'daily_overextended') return '#ff6f00'; // Dark Orange
    return '#9e9e9e'; // Gray
  };

  const getDislocationType = (level: string) => {
    if (level === 'Extreme (P95)') return { icon: '⚡', color: '#d32f2f', label: 'EXTREME' };
    if (level === 'Significant (P85)') return { icon: '⚠️', color: '#ff6f00', label: 'SIGNIFICANT' };
    return { icon: '○', color: '#9e9e9e', label: 'NORMAL' };
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

  if (!data) {
    return null;
  }

  const { market_state, summary } = data;
  const sortedData = getSortedData(market_state);

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
        <Typography variant="h5" fontWeight="bold">
          📊 Live Market State - Daily + 4H Divergence Analysis
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Updated: {new Date(data.timestamp).toLocaleString()}
        </Typography>
      </Box>

      <Box display="flex" gap={2} mb={3} flexWrap="wrap">
        <Tooltip title="Both timeframes in low zone - Strong entry">
          <Chip
            icon={<CheckCircle />}
            label={`${summary.bullish_convergence} Bullish Convergence`}
            color="success"
            variant={summary.bullish_convergence > 0 ? 'filled' : 'outlined'}
          />
        </Tooltip>
        <Tooltip title="Both timeframes in high zone - Exit signal">
          <Chip
            icon={<Cancel />}
            label={`${summary.bearish_convergence} Bearish Convergence`}
            color="error"
            variant={summary.bearish_convergence > 0 ? 'filled' : 'outlined'}
          />
        </Tooltip>
        <Tooltip title="4H extended, Daily low - Profit-take zone">
          <Chip
            icon={<TrendingUp />}
            label={`${summary['4h_overextended']} 4H Overextended`}
            color="warning"
            variant={summary['4h_overextended'] > 0 ? 'filled' : 'outlined'}
          />
        </Tooltip>
        <Tooltip title="Daily extended, 4H low - Exit signal">
          <Chip
            icon={<TrendingDown />}
            label={`${summary['daily_overextended']} Daily Overextended`}
            color="info"
            variant={summary['daily_overextended'] > 0 ? 'filled' : 'outlined'}
          />
        </Tooltip>
        <Tooltip title="Extreme dislocation between timeframes">
          <Chip
            label={`${summary.extreme_dislocation} Extreme (P95)`}
            color="error"
            variant="outlined"
          />
        </Tooltip>
        <Tooltip title="Significant dislocation between timeframes">
          <Chip
            label={`${summary.significant_dislocation} Significant (P85)`}
            color="warning"
            variant="outlined"
          />
        </Tooltip>
      </Box>

      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
              <TableCell>
                <TableSortLabel
                  active={sortField === 'ticker'}
                  direction={sortField === 'ticker' ? sortOrder : 'asc'}
                  onClick={() => handleSort('ticker')}
                >
                  <strong>Ticker</strong>
                </TableSortLabel>
              </TableCell>
              <TableCell align="center">
                <TableSortLabel
                  active={sortField === 'daily_pct'}
                  direction={sortField === 'daily_pct' ? sortOrder : 'asc'}
                  onClick={() => handleSort('daily_pct')}
                >
                  <strong>Daily %ile</strong>
                </TableSortLabel>
              </TableCell>
              <TableCell align="center">
                <TableSortLabel
                  active={sortField === '4h_pct'}
                  direction={sortField === '4h_pct' ? sortOrder : 'asc'}
                  onClick={() => handleSort('4h_pct')}
                >
                  <strong>4H %ile</strong>
                </TableSortLabel>
              </TableCell>
              <TableCell align="center">
                <TableSortLabel
                  active={sortField === 'divergence'}
                  direction={sortField === 'divergence' ? sortOrder : 'asc'}
                  onClick={() => handleSort('divergence')}
                >
                  <strong>Divergence %</strong>
                </TableSortLabel>
              </TableCell>
              <TableCell align="center">
                <TableSortLabel
                  active={sortField === 'dislocation'}
                  direction={sortField === 'dislocation' ? sortOrder : 'asc'}
                  onClick={() => handleSort('dislocation')}
                >
                  <strong>Dislocation Level</strong>
                </TableSortLabel>
              </TableCell>
              <TableCell align="center">
                <TableSortLabel
                  active={sortField === 'category'}
                  direction={sortField === 'category' ? sortOrder : 'asc'}
                  onClick={() => handleSort('category')}
                >
                  <strong>Category</strong>
                </TableSortLabel>
              </TableCell>
              <TableCell align="center">
                <strong>P85 | P95 Thresholds</strong>
              </TableCell>
              <TableCell align="right">
                <strong>Expected Return</strong>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedData.map((state) => {
              const dislocationType = getDislocationType(state.dislocation_level);
              const categoryColor = getDivergenceStatusColor(
                state.divergence_pct,
                state.divergence_category
              );

              return (
                <TableRow
                  key={state.ticker}
                  sx={{
                    backgroundColor:
                      state.divergence_category === 'bullish_convergence'
                        ? 'rgba(76, 175, 80, 0.08)'
                        : state.divergence_category === 'bearish_convergence'
                        ? 'rgba(244, 67, 54, 0.08)'
                        : 'inherit',
                    '&:hover': {
                      backgroundColor: 'rgba(0, 0, 0, 0.04)',
                    },
                    borderLeft: `4px solid ${categoryColor}`,
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

                  <TableCell align="center">
                    <Box
                      sx={{
                        backgroundColor:
                          state.current_percentile <= 5
                            ? 'rgba(76, 175, 80, 0.2)'
                            : state.current_percentile <= 15
                            ? 'rgba(255, 152, 0, 0.2)'
                            : 'transparent',
                        padding: '4px 8px',
                        borderRadius: '4px',
                      }}
                    >
                      <Typography
                        variant="body2"
                        fontWeight="bold"
                        sx={{
                          color:
                            state.current_percentile <= 5
                              ? '#2e7d32'
                              : state.current_percentile <= 15
                              ? '#e65100'
                              : '#666',
                        }}
                      >
                        {state.current_percentile.toFixed(1)}%
                      </Typography>
                    </Box>
                  </TableCell>

                  <TableCell align="center">
                    <Box
                      sx={{
                        backgroundColor:
                          state.four_h_percentile <= 5
                            ? 'rgba(76, 175, 80, 0.2)'
                            : state.four_h_percentile <= 15
                            ? 'rgba(255, 152, 0, 0.2)'
                            : 'transparent',
                        padding: '4px 8px',
                        borderRadius: '4px',
                      }}
                    >
                      <Typography
                        variant="body2"
                        fontWeight="bold"
                        sx={{
                          color:
                            state.four_h_percentile <= 5
                              ? '#2e7d32'
                              : state.four_h_percentile <= 15
                              ? '#e65100'
                              : '#666',
                        }}
                      >
                        {state.four_h_percentile.toFixed(1)}%
                      </Typography>
                    </Box>
                  </TableCell>

                  <TableCell align="center">
                    <Tooltip title={`Daily (${state.current_percentile.toFixed(1)}%) minus 4H (${state.four_h_percentile.toFixed(1)}%)`}>
                      <Box
                        sx={{
                          fontWeight: 'bold',
                          fontSize: '14px',
                          color:
                            state.divergence_pct > 0
                              ? '#2e7d32'
                              : state.divergence_pct < 0
                              ? '#c62828'
                              : '#666',
                          backgroundColor:
                            state.divergence_pct > 0
                              ? 'rgba(76, 175, 80, 0.1)'
                              : state.divergence_pct < 0
                              ? 'rgba(198, 40, 40, 0.1)'
                              : 'transparent',
                          padding: '6px 12px',
                          borderRadius: '4px',
                        }}
                      >
                        {state.divergence_pct > 0 ? '+' : ''}
                        {state.divergence_pct.toFixed(1)}%
                      </Box>
                    </Tooltip>
                  </TableCell>

                  <TableCell align="center">
                    <Tooltip
                      title={`Absolute divergence: ${state.abs_divergence_pct.toFixed(1)}%`}
                    >
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '4px',
                          fontWeight: 'bold',
                          color: dislocationType.color,
                          backgroundColor: dislocationType.color + '15',
                          padding: '6px 12px',
                          borderRadius: '4px',
                          cursor: 'help',
                        }}
                      >
                        <span>{dislocationType.icon}</span>
                        <Typography variant="body2" fontWeight="bold">
                          {state.dislocation_level}
                        </Typography>
                      </Box>
                    </Tooltip>
                  </TableCell>

                  <TableCell align="center">
                    <Tooltip title={state.category_description}>
                      <Box
                        sx={{
                          padding: '6px 8px',
                          borderRadius: '4px',
                          backgroundColor: categoryColor + '20',
                          cursor: 'help',
                          minWidth: '150px',
                        }}
                      >
                        <Typography
                          variant="body2"
                          fontWeight="bold"
                          sx={{ color: categoryColor }}
                        >
                          {state.category_label}
                        </Typography>
                      </Box>
                    </Tooltip>
                  </TableCell>

                  <TableCell align="center">
                    <Tooltip title={`P85 = Significant | P95 = Extreme`}>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        <span style={{ color: '#ff9800' }}>{state.p85_threshold.toFixed(1)}%</span>
                        {' | '}
                        <span style={{ color: '#d32f2f' }}>{state.p95_threshold.toFixed(1)}%</span>
                      </Typography>
                    </Tooltip>
                  </TableCell>

                  <TableCell align="right">
                    <Box>
                      <Typography
                        variant="body2"
                        fontWeight="bold"
                        sx={{
                          color:
                            state.live_expectancy.expected_return_pct > 0
                              ? '#2e7d32'
                              : '#c62828',
                        }}
                      >
                        {state.live_expectancy.expected_return_pct > 0 ? '+' : ''}
                        {state.live_expectancy.expected_return_pct.toFixed(2)}%
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {(state.live_expectancy.expected_win_rate * 100).toFixed(0)}% win | n=
                        {state.live_expectancy.sample_size}
                      </Typography>
                    </Box>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      <Box mt={3}>
        <Alert severity="info" icon={<Info />}>
          <Typography variant="body2" sx={{ mb: 1 }}>
            <strong>📊 Divergence Analysis Legend:</strong>
          </Typography>
          <Box sx={{ ml: 2, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
            <Typography variant="caption">
              <strong>🟢 Bullish Convergence:</strong> Daily ≤15% & 4H ≤15% = Strong buy setup
            </Typography>
            <Typography variant="caption">
              <strong>🔴 Bearish Convergence:</strong> Daily ≥85% & 4H ≥85% = Exit/Short signal
            </Typography>
            <Typography variant="caption">
              <strong>🟡 4H Overextended:</strong> Daily ≤15% & 4H ≥50% = Profit-take opportunity
            </Typography>
            <Typography variant="caption">
              <strong>🟠 Daily Overextended:</strong> Daily ≥85% & 4H ≤50% = Exit signal
            </Typography>
            <Typography variant="caption">
              <strong>⚡ Extreme (P95):</strong> Divergence exceeds {`${Math.max(...market_state.map(s => s.p95_threshold)).toFixed(1)}%`} = Reversal likely
            </Typography>
            <Typography variant="caption">
              <strong>⚠️ Significant (P85):</strong> Divergence exceeds {`${Math.max(...market_state.map(s => s.p85_threshold)).toFixed(1)}%`} = Watch closely
            </Typography>
          </Box>
        </Alert>
      </Box>
    </Paper>
  );
};

export default EnhancedMarketState;
