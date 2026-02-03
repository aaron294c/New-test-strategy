/**
 * Current Market State Component
 *
 * Shows LIVE RSI-MA percentile and risk-adjusted expectancy for all tickers
 * Highlights buy opportunities based on current market conditions
 * WITH SORTABLE COLUMNS AND DATA FOR ALL PERCENTILE RANGES
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
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
  Refresh,
} from '@mui/icons-material';
import axios from 'axios';
import {
  calculateWallStatus,
  normalizeWallData,
  WallStatusResult,
} from './wallStatusUtils';

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
  macdv_daily?: number | null;
  macdv_daily_trend?: string | null;
  macdv_delta_1d?: number | null;
  macdv_delta_5d?: number | null;
  macdv_delta_10d?: number | null;
  macdv_trend?: string | null;
  macdv_trend_label?: string | null;
  days_in_zone?: number | null;
  next_threshold?: number | null;
  next_threshold_distance?: number | null;
  macdv_d7_win_rate?: number | null;
  macdv_d7_mean_return?: number | null;
  macdv_d7_median_return?: number | null;
  macdv_d7_n?: number | null;
  macdv_d7_rsi_band?: string | null;
  prev_midday_percentile?: number | null;
  change_since_prev_midday?: number | null;
  prev_midday_price?: number | null;
  price_change_pct?: number | null;
  percentile_cohort: string;
  zone_label: string;
  in_entry_zone: boolean;
  regime: string;
  is_mean_reverter: boolean;
  is_momentum: boolean;
  volatility_level: string;
  live_expectancy: LiveExpectancy;
  last_extreme_low_date?: string | null;
}

interface MarketStateResponse {
  timestamp: string;
  market_state: MarketState[];
  prev_midday_snapshot?: {
    market_date: string;
    captured_at: string | null;
    timeframe: string;
  };
  midday_snapshot_saved?: boolean;
  summary: {
    total_tickers: number;
    in_entry_zone: number;
    extreme_low_opportunities: number;
    low_opportunities: number;
  };
}

type SortField =
  | 'ticker'
  | 'percentile'
  | 'macdv_daily'
  | 'macdv_delta_1d'
  | 'macdv_delta_5d'
  | 'macdv_delta_10d'
  | 'days_in_zone'
  | 'macdv_d7_win_rate'
  | 'macdv_d7_median_return'
  | 'macdv_d7_mean_return'
  | 'win_rate'
  | 'return'
  | 'risk_adj_expectancy'
  | 'hold_days';
type SortOrder = 'asc' | 'desc';

interface CurrentMarketStateProps {
  timeframe?: Timeframe;
}

// Wall data type for the ticker - matches normalizeWallData output
type WallData = Record<string, number | null>;

export const CurrentMarketState: React.FC<CurrentMarketStateProps> = ({ timeframe = 'daily' }) => {
  const [dailyData, setDailyData] = useState<MarketStateResponse | null>(null);
  const [fourHourData, setFourHourData] = useState<MarketStateResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField>('percentile');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const [wallDataMap, setWallDataMap] = useState<Map<string, WallData>>(new Map());

  const formatDateStamp = (dateString: string | null | undefined): string => {
    if (!dateString) return '—';

    try {
      const date = new Date(dateString);
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const year = String(date.getFullYear()).slice(-2);
      return `${month}/${day}/${year}`;
    } catch {
      return '—';
    }
  };

  const getDaysAgo = (dateString: string | null | undefined): string => {
    if (!dateString) return '';

    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

      if (diffDays === 0) return 'today';
      if (diffDays === 1) return '1 day ago';
      return `${diffDays} days ago`;
    } catch {
      return '';
    }
  };

  // Fetch wall data for ALL tickers in the table
  const fetchWallData = useCallback(async (tickers: string[]) => {
    if (tickers.length === 0) return;

    const newWallData = new Map<string, WallData>();
    const missingTickers = new Set(tickers);

    // Step 1: Try scanner-json first for quick cached data
    try {
      const response = await axios.get(`${API_BASE_URL}/api/gamma-data/scanner-json`, {
        params: { t: Date.now() },
      });

      const symbols = response.data?.symbols;
      if (symbols && typeof symbols === 'object') {
        for (const [ticker, data] of Object.entries(symbols)) {
          if (data && typeof data === 'object' && missingTickers.has(ticker)) {
            const wallData = normalizeWallData(data);
            if (wallData) {
              newWallData.set(ticker, wallData);
              missingTickers.delete(ticker);
            }
          }
        }
      }
      console.log(`✅ Scanner-json: ${newWallData.size} tickers, ${missingTickers.size} remaining`);
    } catch (err: any) {
      console.warn('⚠️ Scanner-json unavailable:', err.message);
    }

    // Step 2: For remaining tickers, try batch risk-distance endpoint
    if (missingTickers.size > 0) {
      try {
        const response = await axios.post(`${API_BASE_URL}/api/risk-distance/batch`, {
          symbols: Array.from(missingTickers),
        });

        const data = response.data?.data;
        if (data && typeof data === 'object') {
          for (const [ticker, symbolData] of Object.entries(data)) {
            if (symbolData && typeof symbolData === 'object') {
              const wallData = normalizeWallData(symbolData);
              if (wallData) {
                newWallData.set(ticker, wallData);
                missingTickers.delete(ticker);
              }
            }
          }
        }
        console.log(`✅ Risk-distance batch: now ${newWallData.size} total, ${missingTickers.size} remaining`);
      } catch (batchErr: any) {
        console.warn('⚠️ Batch risk-distance failed:', batchErr.message);
      }
    }

    // Step 3: For any still missing, try individual gamma/symbol endpoints
    if (missingTickers.size > 0 && missingTickers.size <= 10) {
      const individualPromises = Array.from(missingTickers).map(async (ticker) => {
        try {
          const response = await axios.get(`${API_BASE_URL}/api/gamma/${ticker}`);
          if (response.data) {
            const wallData = normalizeWallData(response.data);
            if (wallData) {
              return { ticker, wallData };
            }
          }
        } catch {
          // Ticker doesn't have gamma data (bonds, forex, etc.) - that's OK
        }
        return null;
      });

      const results = await Promise.allSettled(individualPromises);
      for (const result of results) {
        if (result.status === 'fulfilled' && result.value) {
          newWallData.set(result.value.ticker, result.value.wallData);
          missingTickers.delete(result.value.ticker);
        }
      }
      console.log(`✅ Individual fetches complete: ${newWallData.size} total`);
    }

    // Log any tickers without wall data (likely bonds, forex, etc.)
    if (missingTickers.size > 0) {
      console.log(`ℹ️ No wall data for: ${Array.from(missingTickers).join(', ')} (may not have options)`);
    }

    setWallDataMap(newWallData);
  }, []);

  const fetchCurrentState = async (
    target: Timeframe,
    refresh: boolean = false,
    forceRefresh: boolean = false
  ) => {
    if (!refresh) {
      setLoading(true);
    } else {
      setRefreshing(true);
    }
    setError(null);

    try {
      const endpoint =
        target === '4hour'
          ? `${API_BASE_URL}/api/swing-framework/current-state-4h`
          : `${API_BASE_URL}/api/swing-framework/current-state`;
      const response = await axios.get<MarketStateResponse>(endpoint, {
        params: forceRefresh ? { force_refresh: true } : undefined,
      });
      if (target === '4hour') {
        setFourHourData(response.data);
      } else {
        setDailyData(response.data);
      }
      console.log(`✅ ${target === '4hour' ? '4H' : 'Daily'} current market state loaded:`, response.data.summary);

      // Fetch wall data for the tickers (non-blocking)
      const tickers = response.data.market_state.map(s => s.ticker);
      fetchWallData(tickers);
    } catch (err: any) {
      console.error('❌ Error fetching current state:', err);
      setError(err.message || 'Failed to fetch current market state');
    } finally {
      setLoading(false);
      setRefreshing(false);
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

  // Memoized wall status calculation for all tickers (performance optimization)
  const wallStatusMap = useMemo(() => {
    const result = new Map<string, WallStatusResult>();
    if (!marketData?.market_state) return result;

    for (const state of marketData.market_state) {
      const wallData = wallDataMap.get(state.ticker);
      const status = calculateWallStatus(state.current_price, wallData || null);
      result.set(state.ticker, status);
    }
    return result;
  }, [marketData?.market_state, wallDataMap]);

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

      const normalizeNumber = (v: number | null | undefined): number => {
        if (v == null || Number.isNaN(v)) {
          return sortOrder === 'asc' ? Number.POSITIVE_INFINITY : Number.NEGATIVE_INFINITY;
        }
        return v;
      };

      switch (sortField) {
        case 'ticker':
          aValue = a.ticker;
          bValue = b.ticker;
          break;
        case 'percentile':
          aValue = a.current_percentile;
          bValue = b.current_percentile;
          break;
        case 'macdv_daily':
          aValue = normalizeNumber(a.macdv_daily);
          bValue = normalizeNumber(b.macdv_daily);
          break;
        case 'macdv_delta_1d':
          aValue = normalizeNumber(a.macdv_delta_1d);
          bValue = normalizeNumber(b.macdv_delta_1d);
          break;
        case 'macdv_delta_5d':
          aValue = normalizeNumber(a.macdv_delta_5d);
          bValue = normalizeNumber(b.macdv_delta_5d);
          break;
        case 'macdv_delta_10d':
          aValue = normalizeNumber(a.macdv_delta_10d);
          bValue = normalizeNumber(b.macdv_delta_10d);
          break;
        case 'days_in_zone':
          aValue = normalizeNumber(a.days_in_zone);
          bValue = normalizeNumber(b.days_in_zone);
          break;
        case 'macdv_d7_win_rate':
          aValue = normalizeNumber(a.macdv_d7_win_rate);
          bValue = normalizeNumber(b.macdv_d7_win_rate);
          break;
        case 'macdv_d7_median_return':
          aValue = normalizeNumber(a.macdv_d7_median_return);
          bValue = normalizeNumber(b.macdv_d7_median_return);
          break;
        case 'macdv_d7_mean_return':
          aValue = normalizeNumber(a.macdv_d7_mean_return);
          bValue = normalizeNumber(b.macdv_d7_mean_return);
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
  const prevMidday = marketData.prev_midday_snapshot;

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
        <Typography variant="h5" fontWeight="bold">
          🎯 Live Market State - {timeframe === '4hour' ? '4-Hour' : 'Daily'} Buy Opportunities (Stocks + Indices)
        </Typography>
        <Box display="flex" alignItems="center" gap={1}>
          <Tooltip title="Force a live recompute (bypasses static snapshots and caches)">
            <Chip
              icon={<Refresh fontSize="small" />}
              clickable
              disabled={refreshing}
              label={refreshing ? 'Refreshing…' : 'Force refresh'}
              size="small"
              variant="outlined"
              onClick={() => fetchCurrentState(timeframe, true, true)}
            />
          </Tooltip>
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

      <TableContainer
        sx={{
          maxHeight: '70vh',
          overflowX: 'auto',
          overflowY: 'auto',
          position: 'relative',
          border: '1px solid #e0e0e0',
          borderRadius: '4px',
          // Custom scrollbar styling for better visibility and UX
          '&::-webkit-scrollbar': {
            width: '12px',
            height: '12px',
          },
          '&::-webkit-scrollbar-track': {
            backgroundColor: '#f1f1f1',
            borderRadius: '10px',
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: '#888',
            borderRadius: '10px',
            border: '2px solid #f1f1f1',
            '&:hover': {
              backgroundColor: '#555',
            },
          },
          '&::-webkit-scrollbar-corner': {
            backgroundColor: '#f1f1f1',
          },
          // Firefox scrollbar styling
          scrollbarWidth: 'thin',
          scrollbarColor: '#888 #f1f1f1',
        }}
      >
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell
                sx={{
                  position: 'sticky',
                  left: 0,
                  backgroundColor: '#fff',
                  zIndex: 3,
                  boxShadow: '2px 0 5px rgba(0,0,0,0.1)',
                }}
              >
                <TableSortLabel
                  active={sortField === 'ticker'}
                  direction={sortField === 'ticker' ? sortOrder : 'asc'}
                  onClick={() => handleSort('ticker')}
                >
                  Ticker
                </TableSortLabel>
              </TableCell>
              <TableCell>Signal</TableCell>
              <TableCell>
                <Tooltip title="Walls breached (below) or approaching (within 1%): ST=Short-term Put, LT=Long-term Put, Q=Quarterly Put, MP=Max Pain, LE=Lower Ext, NW=NW Band">
                  <span>Wall Status</span>
                </Tooltip>
              </TableCell>
              <TableCell align="right">
                <TableSortLabel
                  active={sortField === 'percentile'}
                  direction={sortField === 'percentile' ? sortOrder : 'asc'}
                  onClick={() => handleSort('percentile')}
                >
                  Current %ile
                </TableSortLabel>
              </TableCell>
              <TableCell align="right">
                <Tooltip
                  title={
                    prevMidday?.captured_at
                      ? `Previous trading day snapshot (${prevMidday.market_date}) captured at ${new Date(prevMidday.captured_at).toLocaleString()}`
                      : `No previous trading day midday snapshot found for ${prevMidday?.market_date ?? 'previous trading day'}`
                  }
                >
                <span>Prev Midday %ile</span>
                </Tooltip>
              </TableCell>
              <TableCell>Zone</TableCell>
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
              <TableCell align="right">
                <Tooltip title="Last date when this asset hit ≤5% percentile (extreme low zone)">
                  <span>Last &lt;5%</span>
                </Tooltip>
              </TableCell>
              <TableCell align="right">Sample Size</TableCell>
              <TableCell align="right">
                <TableSortLabel
                  active={sortField === 'macdv_daily'}
                  direction={sortField === 'macdv_daily' ? sortOrder : 'asc'}
                  onClick={() => handleSort('macdv_daily')}
                >
                  MACD-V (D)
                </TableSortLabel>
              </TableCell>
              <TableCell align="right">
                <TableSortLabel
                  active={sortField === 'macdv_delta_1d'}
                  direction={sortField === 'macdv_delta_1d' ? sortOrder : 'asc'}
                  onClick={() => handleSort('macdv_delta_1d')}
                >
                  <Tooltip title="1-day MACD-V change">
                    <span>Δ 1D</span>
                  </Tooltip>
                </TableSortLabel>
              </TableCell>
              <TableCell align="right">
                <TableSortLabel
                  active={sortField === 'macdv_delta_5d'}
                  direction={sortField === 'macdv_delta_5d' ? sortOrder : 'asc'}
                  onClick={() => handleSort('macdv_delta_5d')}
                >
                  <Tooltip title="5-day average MACD-V change rate (per day)">
                    <span>Δ 5D</span>
                  </Tooltip>
                </TableSortLabel>
              </TableCell>
              <TableCell align="right">
                <TableSortLabel
                  active={sortField === 'macdv_delta_10d'}
                  direction={sortField === 'macdv_delta_10d' ? sortOrder : 'asc'}
                  onClick={() => handleSort('macdv_delta_10d')}
                >
                  <Tooltip title="10-day average MACD-V change rate (per day)">
                    <span>Δ 10D</span>
                  </Tooltip>
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <Tooltip title="Momentum trend: ↗↗ ACC (Accelerating), ↗ STR (Steady rise), →↗ FLAT (Flattening), ↘ DECEL (Decelerating), ↘↘ CRASH (Falling)">
                  <span>Trend</span>
                </Tooltip>
              </TableCell>
              <TableCell align="right">
                <TableSortLabel
                  active={sortField === 'days_in_zone'}
                  direction={sortField === 'days_in_zone' ? sortOrder : 'asc'}
                  onClick={() => handleSort('days_in_zone')}
                >
                  <Tooltip title="Days MACD-V has been in current threshold zone">
                    <span>Days in Zone</span>
                  </Tooltip>
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <Tooltip title="Distance to next critical threshold (±50, ±100). Warns when within 10 points.">
                  <span>Next Threshold</span>
                </Tooltip>
              </TableCell>
              <TableCell>Regime</TableCell>
              <TableCell align="right">
                <TableSortLabel
                  active={sortField === 'macdv_d7_win_rate'}
                  direction={sortField === 'macdv_d7_win_rate' ? sortOrder : 'asc'}
                  onClick={() => handleSort('macdv_d7_win_rate')}
                >
                  D7 Win%
                </TableSortLabel>
              </TableCell>
              <TableCell align="right">
                <TableSortLabel
                  active={sortField === 'macdv_d7_median_return'}
                  direction={sortField === 'macdv_d7_median_return' ? sortOrder : 'asc'}
                  onClick={() => handleSort('macdv_d7_median_return')}
                >
                  D7 Median
                </TableSortLabel>
              </TableCell>
              <TableCell align="right">
                <TableSortLabel
                  active={sortField === 'macdv_d7_mean_return'}
                  direction={sortField === 'macdv_d7_mean_return' ? sortOrder : 'asc'}
                  onClick={() => handleSort('macdv_d7_mean_return')}
                >
                  D7 Mean
                </TableSortLabel>
              </TableCell>
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
                <TableCell
                  sx={{
                    position: 'sticky',
                    left: 0,
                    backgroundColor: state.in_entry_zone
                      ? 'rgba(76, 175, 80, 0.08)'
                      : '#fff',
                    zIndex: 2,
                    boxShadow: '2px 0 5px rgba(0,0,0,0.1)',
                  }}
                >
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

                {/* Wall Status Column */}
                <TableCell>
                  {(() => {
                    const wallStatus = wallStatusMap.get(state.ticker);
                    if (!wallStatus || !wallStatus.hasEngagement) {
                      return (
                        <Typography variant="body2" color="text.secondary">
                          —
                        </Typography>
                      );
                    }
                    return (
                      <Tooltip
                        title={
                          <Box>
                            <Typography variant="caption" fontWeight="bold" sx={{ display: 'block', mb: 0.5 }}>
                              Engaged Walls:
                            </Typography>
                            {wallStatus.engagedWalls.map((w, i) => (
                              <Typography key={i} variant="caption" sx={{ display: 'block' }}>
                                {w.name}: {w.status === 'breached' ? 'BREACHED' : 'Approaching'} ({w.distance.toFixed(2)}%)
                              </Typography>
                            ))}
                          </Box>
                        }
                      >
                        <Box
                          sx={{
                            display: 'flex',
                            flexWrap: 'wrap',
                            gap: 0.5,
                            maxWidth: 180,
                          }}
                        >
                          {wallStatus.engagedWalls.slice(0, 3).map((w, i) => (
                            <Chip
                              key={i}
                              label={`${w.shortName}${w.distance < 0 ? '' : '+'}${w.distance.toFixed(1)}%`}
                              size="small"
                              sx={{
                                height: 20,
                                fontSize: '0.7rem',
                                backgroundColor: w.status === 'breached' ? `${w.color}40` : `${w.color}20`,
                                color: w.color,
                                border: w.status === 'breached' ? `1px solid ${w.color}` : 'none',
                                fontWeight: w.status === 'breached' ? 'bold' : 'normal',
                              }}
                            />
                          ))}
                          {wallStatus.engagedWalls.length > 3 && (
                            <Typography variant="caption" color="text.secondary">
                              +{wallStatus.engagedWalls.length - 3}
                            </Typography>
                          )}
                        </Box>
                      </Tooltip>
                    );
                  })()}
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

                <TableCell align="right">
                  {state.prev_midday_percentile == null ? (
                    <Typography variant="body2" color="text.secondary">
                      —
                    </Typography>
                  ) : (
                    <Box display="flex" flexDirection="column" alignItems="flex-end">
                      <Typography variant="body2">
                        {state.prev_midday_percentile.toFixed(1)}%
                      </Typography>
                      {state.change_since_prev_midday != null && (
                        <Box display="flex" alignItems="center" gap={0.5}>
                          {state.change_since_prev_midday > 0 ? (
                            <ArrowUpward sx={{ fontSize: 14, color: '#f44336' }} />
                          ) : state.change_since_prev_midday < 0 ? (
                            <ArrowDownward sx={{ fontSize: 14, color: '#4caf50' }} />
                          ) : null}
                          <Typography
                            variant="caption"
                            sx={{
                              color:
                                state.change_since_prev_midday > 0
                                  ? '#f44336'
                                  : state.change_since_prev_midday < 0
                                  ? '#4caf50'
                                  : 'text.secondary',
                            }}
                          >
                            {state.change_since_prev_midday > 0 ? '+' : ''}
                            {state.change_since_prev_midday.toFixed(1)}pp
                            {state.price_change_pct != null && (
                              <span style={{ marginLeft: '4px' }}>
                                ({state.price_change_pct > 0 ? '+' : ''}
                                {state.price_change_pct.toFixed(1)}%)
                              </span>
                            )}
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  )}
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
                  {state.last_extreme_low_date ? (
                    <Tooltip title={`Last saw ≤5% percentile on ${formatDateStamp(state.last_extreme_low_date)}`}>
                      <Box display="flex" flexDirection="column" alignItems="flex-end">
                        <Typography
                          variant="body2"
                          color={state.current_percentile <= 5 ? 'success.main' : 'text.secondary'}
                          fontWeight={state.current_percentile <= 5 ? 'medium' : 'normal'}
                        >
                          {formatDateStamp(state.last_extreme_low_date)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          ({getDaysAgo(state.last_extreme_low_date)})
                        </Typography>
                      </Box>
                    </Tooltip>
                  ) : (
                    <Typography variant="body2" color="text.disabled">
                      —
                    </Typography>
                  )}
                </TableCell>

                <TableCell align="right">
                  <Typography variant="body2" color="text.secondary">
                    n={state.live_expectancy.sample_size}
                  </Typography>
                </TableCell>

                <TableCell align="right">
                  {(() => {
                    const val = state.macdv_daily;
                    const trend = state.macdv_daily_trend;
                    const color =
                      trend === 'Bullish'
                        ? 'success.main'
                        : trend === 'Bearish'
                          ? 'error.main'
                          : 'text.secondary';

                    return (
                      <>
                        <Typography variant="body2" color={color} fontWeight="medium">
                          {val == null ? '—' : val.toFixed(1)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {trend || '—'}
                        </Typography>
                      </>
                    );
                  })()}
                </TableCell>

                <TableCell align="right">
                  {state.macdv_delta_1d != null ? (
                    <Typography
                      variant="body2"
                      sx={{
                        color: state.macdv_delta_1d > 0 ? '#4caf50' : state.macdv_delta_1d < 0 ? '#f44336' : 'text.secondary',
                        fontWeight: Math.abs(state.macdv_delta_1d) > 5 ? 'bold' : 'normal',
                      }}
                    >
                      {state.macdv_delta_1d > 0 ? '+' : ''}
                      {state.macdv_delta_1d.toFixed(1)}
                    </Typography>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      —
                    </Typography>
                  )}
                </TableCell>

                <TableCell align="right">
                  {state.macdv_delta_5d != null ? (
                    <Typography
                      variant="body2"
                      sx={{
                        color: state.macdv_delta_5d > 0 ? '#4caf50' : state.macdv_delta_5d < 0 ? '#f44336' : 'text.secondary',
                        fontWeight: Math.abs(state.macdv_delta_5d) > 5 ? 'bold' : 'normal',
                      }}
                    >
                      {state.macdv_delta_5d > 0 ? '+' : ''}
                      {state.macdv_delta_5d.toFixed(1)}
                    </Typography>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      —
                    </Typography>
                  )}
                </TableCell>

                <TableCell align="right">
                  {state.macdv_delta_10d != null ? (
                    <Typography
                      variant="body2"
                      sx={{
                        color: state.macdv_delta_10d > 0 ? '#4caf50' : state.macdv_delta_10d < 0 ? '#f44336' : 'text.secondary',
                        fontWeight: Math.abs(state.macdv_delta_10d) > 5 ? 'bold' : 'normal',
                      }}
                    >
                      {state.macdv_delta_10d > 0 ? '+' : ''}
                      {state.macdv_delta_10d.toFixed(1)}
                    </Typography>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      —
                    </Typography>
                  )}
                </TableCell>

                <TableCell>
                  {state.macdv_trend && state.macdv_trend_label ? (
                    <Chip
                      label={`${state.macdv_trend} ${state.macdv_trend_label}`}
                      size="small"
                      sx={{
                        backgroundColor:
                          state.macdv_trend_label === 'ACC'
                            ? '#4caf5020'
                            : state.macdv_trend_label === 'STR'
                            ? '#8bc34a20'
                            : state.macdv_trend_label === 'FLAT'
                            ? '#ff980020'
                            : state.macdv_trend_label === 'DECEL'
                            ? '#ff572220'
                            : state.macdv_trend_label === 'CRASH'
                            ? '#f4433620'
                            : 'transparent',
                        color:
                          state.macdv_trend_label === 'ACC' || state.macdv_trend_label === 'STR'
                            ? '#4caf50'
                            : state.macdv_trend_label === 'FLAT'
                            ? '#ff9800'
                            : '#f44336',
                        fontWeight: state.macdv_trend_label === 'ACC' || state.macdv_trend_label === 'CRASH' ? 'bold' : 'normal',
                      }}
                    />
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      —
                    </Typography>
                  )}
                </TableCell>

                <TableCell align="right">
                  {state.days_in_zone != null ? (
                    <Typography variant="body2" color="text.secondary">
                      {state.days_in_zone} days
                    </Typography>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      —
                    </Typography>
                  )}
                </TableCell>

                <TableCell>
                  {state.next_threshold != null && state.next_threshold_distance != null ? (
                    <Chip
                      label={`${state.next_threshold > 0 ? '+' : ''}${state.next_threshold} (${state.next_threshold_distance > 0 ? '+' : ''}${state.next_threshold_distance.toFixed(1)}pts)`}
                      size="small"
                      color={Math.abs(state.next_threshold_distance) <= 2 ? 'warning' : 'default'}
                      icon={Math.abs(state.next_threshold_distance) <= 2 ? <Warning fontSize="small" /> : undefined}
                    />
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      —
                    </Typography>
                  )}
                </TableCell>

                <TableCell>
                  <Chip
                    label={state.is_mean_reverter ? 'Mean Rev' : 'Momentum'}
                    size="small"
                    variant="outlined"
                  />
                </TableCell>

                <TableCell align="right">
                  {state.macdv_d7_win_rate == null ? (
                    <Typography variant="body2" color="text.secondary">
                      —
                    </Typography>
                  ) : (
                    <Tooltip
                      title={`MACD-V>120 & RSI band ${state.macdv_d7_rsi_band ?? '—'} • n=${state.macdv_d7_n ?? '—'}`}
                    >
                      <Typography variant="body2">
                        {state.macdv_d7_win_rate.toFixed(1)}%
                      </Typography>
                    </Tooltip>
                  )}
                </TableCell>

                <TableCell align="right">
                  {state.macdv_d7_median_return == null ? (
                    <Typography variant="body2" color="text.secondary">
                      —
                    </Typography>
                  ) : (
                    <Tooltip
                      title={`MACD-V>120 & RSI band ${state.macdv_d7_rsi_band ?? '—'} • n=${state.macdv_d7_n ?? '—'}`}
                    >
                      <Typography
                        variant="body2"
                        sx={{
                          color: state.macdv_d7_median_return > 0 ? '#4caf50' : '#f44336',
                        }}
                      >
                        {state.macdv_d7_median_return > 0 ? '+' : ''}
                        {state.macdv_d7_median_return.toFixed(2)}%
                      </Typography>
                    </Tooltip>
                  )}
                </TableCell>

                <TableCell align="right">
                  {state.macdv_d7_mean_return == null ? (
                    <Typography variant="body2" color="text.secondary">
                      —
                    </Typography>
                  ) : (
                    <Tooltip
                      title={`MACD-V>120 & RSI band ${state.macdv_d7_rsi_band ?? '—'} • n=${state.macdv_d7_n ?? '—'}`}
                    >
                      <Typography
                        variant="body2"
                        sx={{
                          color: state.macdv_d7_mean_return > 0 ? '#4caf50' : '#f44336',
                        }}
                      >
                        {state.macdv_d7_mean_return > 0 ? '+' : ''}
                        {state.macdv_d7_mean_return.toFixed(2)}%
                      </Typography>
                    </Tooltip>
                  )}
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
