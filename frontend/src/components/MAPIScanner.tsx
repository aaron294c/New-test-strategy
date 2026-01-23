/**
 * MAPI Market Scanner - Similar to RSI-MA Live Signals Table
 *
 * Shows current MAPI signals across multiple stocks with:
 * - Composite score & percentile
 * - EDR & ESV percentiles
 * - Entry signals
 * - Historical performance metrics
 */

import React, { useState } from 'react';
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
  Button,
  Stack,
  Tooltip,
  IconButton,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { mapiApi } from '@/api/client';

interface MAPISignal {
  symbol: string;
  date: string;
  price: number;
  composite_score: number;
  composite_percentile: number;
  edr_percentile: number;
  esv_percentile: number;
  regime: string;
  adx: number;
  distance_to_ema20_pct: number;
  entry_signal: boolean;
  days_since_last_signal: number;
  historical_win_rate: number;
  historical_avg_return: number;
  sample_size: number;
}

interface ScannerResponse {
  success: boolean;
  timestamp: string;
  criteria: {
    composite_threshold: number;
    edr_threshold: number;
  };
  summary: {
    total: number;
    extreme_low: number;
    low: number;
    not_in_zone: number;
  };
  signals: MAPISignal[];
  extreme_low_signals: MAPISignal[];
  low_signals: MAPISignal[];
}

const DEFAULT_SYMBOLS = [
  'AAPL', 'TSLA', 'META', 'GOOGL', 'MSFT', 'AMZN', 'NVDA', 'NFLX',
  'AVGO', 'TSM', 'WMT', 'COST', 'JPM', 'BAC', 'XOM', 'CVX',
  'SPY', 'QQQ', 'BRK-B', 'LLY', 'UNH', 'JNJ', 'V', 'MA',
];

const MAPIScanner: React.FC = () => {
  const [compositeThreshold, setCompositeThreshold] = useState(35);
  const [edrThreshold, setEdrThreshold] = useState(20);
  const queryClient = useQueryClient();

  // Scan mutation
  const scanMutation = useMutation({
    mutationFn: async (params: {
      symbols: string[];
      composite_threshold: number;
      edr_threshold: number;
    }) => {
      console.log('[MAPI Scanner] Scanning with params:', params);
      const result = await mapiApi.scanMarket(params);
      console.log('[MAPI Scanner] Scan result:', result);
      return result as ScannerResponse;
    },
    onSuccess: (data) => {
      console.log('[MAPI Scanner] Scan successful:', data);
      queryClient.invalidateQueries({ queryKey: ['mapi-scanner'] });
    },
    onError: (error) => {
      console.error('[MAPI Scanner] Scan error:', error);
    },
  });

  // Auto-scan on mount
  React.useEffect(() => {
    handleScan();
  }, []);

  const handleScan = () => {
    scanMutation.mutate({
      symbols: DEFAULT_SYMBOLS,
      composite_threshold: compositeThreshold,
      edr_threshold: edrThreshold,
    });
  };

  const data = scanMutation.data;
  const isLoading = scanMutation.isPending;
  const error = scanMutation.error;

  const getPercentileColor = (percentile: number) => {
    if (percentile <= 20) return 'success';
    if (percentile <= 35) return 'info';
    if (percentile <= 50) return 'warning';
    return 'default';
  };

  const getRegimeColor = (regime: string) => {
    if (regime === 'Momentum') return 'success';
    if (regime === 'Mean Reversion') return 'warning';
    return 'default';
  };

  const formatDaysAgo = (days: number) => {
    if (days === 0) return 'Today';
    if (days === 1) return '1 day ago';
    if (days === 999) return 'Never';
    return `${days} days ago`;
  };

  if (error) {
    return (
      <Alert severity="error">
        Failed to scan market: {error instanceof Error ? error.message : 'Unknown error'}
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
          <Box>
            <Typography variant="h5" gutterBottom>
              MAPI Market Scanner - Entry Opportunities
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Momentum stocks with MAPI composite scores in buy zones
            </Typography>
          </Box>
          <Button
            variant="contained"
            startIcon={<RefreshIcon />}
            onClick={handleScan}
            disabled={isLoading}
          >
            {isLoading ? 'Scanning...' : 'Refresh'}
          </Button>
        </Stack>

        {data && (
          <Stack direction="row" spacing={2}>
            <Chip
              label={`Extreme Low (≤20%): ${data.summary.extreme_low}`}
              color="success"
              variant="outlined"
            />
            <Chip
              label={`Low (20-35%): ${data.summary.low}`}
              color="info"
              variant="outlined"
            />
            <Chip
              label={`Not in Zone: ${data.summary.not_in_zone}`}
              color="default"
              variant="outlined"
            />
            <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto', alignSelf: 'center' }}>
              Updated: {data.timestamp ? new Date(data.timestamp).toLocaleString() : ''}
            </Typography>
          </Stack>
        )}
      </Paper>

      {/* Loading */}
      {isLoading && !data && (
        <Box display="flex" justifyContent="center" p={4}>
          <CircularProgress />
        </Box>
      )}

      {/* Scanner Table */}
      {data && (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow sx={{ backgroundColor: 'primary.dark' }}>
                <TableCell>
                  <Typography variant="subtitle2" color="white">
                    Signal
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Typography variant="subtitle2" color="white">
                    Price
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="Raw composite score (clusters around 50)">
                    <Typography variant="subtitle2" color="white">
                      Composite Raw
                    </Typography>
                  </Tooltip>
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="Percentile rank of composite (lower = better entry)">
                    <Typography variant="subtitle2" color="white">
                      Composite %ile
                    </Typography>
                  </Tooltip>
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="EMA Distance Ratio percentile">
                    <Typography variant="subtitle2" color="white">
                      EDR %ile
                    </Typography>
                  </Tooltip>
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="EMA Slope Velocity percentile">
                    <Typography variant="subtitle2" color="white">
                      ESV %ile
                    </Typography>
                  </Tooltip>
                </TableCell>
                <TableCell align="center">
                  <Typography variant="subtitle2" color="white">
                    Regime
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Typography variant="subtitle2" color="white">
                    ADX
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="Distance to EMA(20)">
                    <Typography variant="subtitle2" color="white">
                      EMA Dist
                    </Typography>
                  </Tooltip>
                </TableCell>
                <TableCell align="center">
                  <Tooltip title="Historical win rate (7-day holds)">
                    <Typography variant="subtitle2" color="white">
                      Win Rate
                    </Typography>
                  </Tooltip>
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="Historical average return (7-day holds)">
                    <Typography variant="subtitle2" color="white">
                      Avg Return
                    </Typography>
                  </Tooltip>
                </TableCell>
                <TableCell align="center">
                  <Tooltip title="Days since last entry signal">
                    <Typography variant="subtitle2" color="white">
                      Last Signal
                    </Typography>
                  </Tooltip>
                </TableCell>
                <TableCell align="center">
                  <Tooltip title="Number of historical signals">
                    <Typography variant="subtitle2" color="white">
                      Sample
                    </Typography>
                  </Tooltip>
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.signals.map((signal) => (
                <TableRow
                  key={signal.symbol}
                  sx={{
                    backgroundColor: signal.entry_signal ? 'success.light' : 'inherit',
                    '&:hover': { backgroundColor: 'action.hover' },
                  }}
                >
                  <TableCell>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Typography variant="body2" fontWeight="bold">
                        {signal.symbol}
                      </Typography>
                      {signal.entry_signal && (
                        <TrendingUpIcon color="success" fontSize="small" />
                      )}
                    </Stack>
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2">${signal.price.toFixed(2)}</Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2">{signal.composite_score.toFixed(2)}</Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Chip
                      label={`${signal.composite_percentile.toFixed(1)}%`}
                      color={getPercentileColor(signal.composite_percentile) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Typography
                      variant="body2"
                      color={signal.edr_percentile < 20 ? 'success.main' : 'text.primary'}
                    >
                      {signal.edr_percentile.toFixed(1)}%
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography
                      variant="body2"
                      color={signal.esv_percentile < 20 ? 'warning.main' : 'text.primary'}
                    >
                      {signal.esv_percentile.toFixed(1)}%
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={signal.regime}
                      color={getRegimeColor(signal.regime) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2">{signal.adx.toFixed(1)}</Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography
                      variant="body2"
                      color={signal.distance_to_ema20_pct > 0 ? 'success.main' : 'error.main'}
                    >
                      {signal.distance_to_ema20_pct > 0 ? '+' : ''}
                      {signal.distance_to_ema20_pct.toFixed(2)}%
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Typography
                      variant="body2"
                      color={signal.historical_win_rate >= 65 ? 'success.main' : 'text.primary'}
                    >
                      {signal.historical_win_rate.toFixed(1)}%
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography
                      variant="body2"
                      color={signal.historical_avg_return > 0 ? 'success.main' : 'error.main'}
                    >
                      {signal.historical_avg_return > 0 ? '+' : ''}
                      {signal.historical_avg_return.toFixed(2)}%
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Typography variant="caption" color="text.secondary">
                      {formatDaysAgo(signal.days_since_last_signal)}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Typography variant="caption" color="text.secondary">
                      n={signal.sample_size}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
};

export default MAPIScanner;
