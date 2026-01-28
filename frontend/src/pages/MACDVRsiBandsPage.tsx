import { useMemo, useState } from 'react';
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';

import { backtestApi } from '@/api/client';
import type { MACDVRsiBandsAnalysis, ReturnStats } from '@/types';

type Metric = 'n' | 'win_rate' | 'mean' | 'median';

const DEFAULT_UNIVERSE = ['AAPL', 'NVDA', 'GOOGL', 'MSFT', 'META', 'QQQ', 'SPY', 'BRK-B', 'AMZN'];

function formatMetric(metric: Metric, value: number | null): string {
  if (metric === 'n') return value == null ? '—' : String(Math.trunc(value));
  if (value == null) return '—';
  if (metric === 'win_rate') return value.toFixed(1) + '%';
  return value.toFixed(2) + '%';
}

function StatCard({ title, stats }: { title: string; stats: ReturnStats }) {
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
        {title}
      </Typography>
      <Grid container spacing={1}>
        <Grid item xs={6} md={3}>
          <Typography variant="caption" color="text.secondary">
            n
          </Typography>
          <Typography variant="h6">{stats.n}</Typography>
        </Grid>
        <Grid item xs={6} md={3}>
          <Typography variant="caption" color="text.secondary">
            win
          </Typography>
          <Typography variant="h6">{formatMetric('win_rate', stats.win_rate)}</Typography>
        </Grid>
        <Grid item xs={6} md={3}>
          <Typography variant="caption" color="text.secondary">
            mean
          </Typography>
          <Typography variant="h6">{formatMetric('mean', stats.mean)}</Typography>
        </Grid>
        <Grid item xs={6} md={3}>
          <Typography variant="caption" color="text.secondary">
            median
          </Typography>
          <Typography variant="h6">{formatMetric('median', stats.median)}</Typography>
        </Grid>
      </Grid>
    </Paper>
  );
}

function MetricTable({
  analysis,
  metric,
  title,
}: {
  analysis: MACDVRsiBandsAnalysis;
  metric: Metric;
  title: string;
}) {
  const bands = analysis.params.rsi_bands.map((b) => b.label);
  const tickers = useMemo(() => {
    const keys = Object.keys(analysis.table);
    const sorted = keys.filter((k) => k !== 'ALL').sort();
    return ['ALL', ...sorted];
  }, [analysis.table]);

  return (
    <Paper sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2, flexWrap: 'wrap' }}>
        <Typography variant="h6">{title}</Typography>
        <Chip
          size="small"
          label={`MACD-V ${analysis.params.macdv_lo.toFixed(0)}-${analysis.params.macdv_hi.toFixed(
            0
          )} • D${analysis.params.horizon}`}
        />
      </Box>
      <Box sx={{ overflowX: 'auto', mt: 1 }}>
        <Table size="small" sx={{ minWidth: 900 }}>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold' }}>Ticker</TableCell>
              {bands.map((b) => (
                <TableCell key={b} align="right" sx={{ fontWeight: 'bold', whiteSpace: 'nowrap' }}>
                  {b}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {tickers.map((t) => (
              <TableRow key={t} hover>
                <TableCell sx={{ fontWeight: t === 'ALL' ? 'bold' : 'normal' }}>{t}</TableCell>
                {bands.map((b) => {
                  const s = analysis.table[t]?.[b];
                  const raw = metric === 'n' ? s?.n ?? null : (s as any)?.[metric] ?? null;
                  return (
                    <TableCell key={`${t}-${b}`} align="right">
                      {formatMetric(metric, raw)}
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Box>
    </Paper>
  );
}

function NonOverlapTable({ analysis }: { analysis: MACDVRsiBandsAnalysis }) {
  const tickers = useMemo(() => {
    const keys = Object.keys(analysis.non_overlapping.results);
    const sorted = keys.filter((k) => k !== 'ALL').sort();
    return ['ALL', ...sorted];
  }, [analysis.non_overlapping.results]);

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Non-Overlapping Backtest (Fixed D{analysis.non_overlapping.horizon})
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {analysis.non_overlapping.rule}
      </Typography>
      <Box sx={{ overflowX: 'auto' }}>
        <Table size="small" sx={{ minWidth: 650 }}>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold' }}>Ticker</TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                trades
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                win
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                mean
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                median
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tickers.map((t) => {
              const s = analysis.non_overlapping.results[t];
              return (
                <TableRow key={t} hover>
                  <TableCell sx={{ fontWeight: t === 'ALL' ? 'bold' : 'normal' }}>{t}</TableCell>
                  <TableCell align="right">{s?.n ?? 0}</TableCell>
                  <TableCell align="right">{formatMetric('win_rate', s?.win_rate ?? null)}</TableCell>
                  <TableCell align="right">{formatMetric('mean', s?.mean ?? null)}</TableCell>
                  <TableCell align="right">{formatMetric('median', s?.median ?? null)}</TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </Box>
    </Paper>
  );
}

export default function MACDVRsiBandsPage() {
  const [metric, setMetric] = useState<Metric>('win_rate');
  const [pctLookback, setPctLookback] = useState<number>(252);
  const [period, setPeriod] = useState<string>('10y');
  const [forceRefresh, setForceRefresh] = useState<boolean>(false);

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['macdvRsiBands', DEFAULT_UNIVERSE.join(','), period, pctLookback, 7],
    queryFn: () =>
      backtestApi.getMACDVRsiBandsAnalysis({
        tickers: DEFAULT_UNIVERSE,
        period,
        pct_lookback: pctLookback,
        horizon: 7,
        force_refresh: forceRefresh,
      }),
    staleTime: 60 * 60 * 1000,
    onSuccess: () => {
      if (forceRefresh) setForceRefresh(false);
    },
  });

  const analysis = data as MACDVRsiBandsAnalysis | undefined;

  return (
    <Box>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={7}>
            <Typography variant="h5">MACD-V 120–150 × RSI-MA Bands (D7)</Typography>
            <Typography variant="body2" color="text.secondary">
              Universe: {DEFAULT_UNIVERSE.join(', ')} • Close-to-close forward returns at D7
            </Typography>
          </Grid>
          <Grid item xs={12} md={5}>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Lookback</InputLabel>
                  <Select
                    value={pctLookback}
                    label="Lookback"
                    onChange={(e) => setPctLookback(Number(e.target.value))}
                  >
                    <MenuItem value={252}>252</MenuItem>
                    <MenuItem value={500}>500</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Period</InputLabel>
                  <Select value={period} label="Period" onChange={(e) => setPeriod(String(e.target.value))}>
                    <MenuItem value="5y">5y</MenuItem>
                    <MenuItem value="10y">10y</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => {
                    setForceRefresh(true);
                    refetch();
                  }}
                  disabled={isFetching}
                >
                  {isFetching ? <CircularProgress size={18} /> : 'Refresh'}
                </Button>
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </Paper>

      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
          <CircularProgress />
        </Box>
      )}

      {error && (
        <Paper sx={{ p: 2 }}>
          <Typography color="error">Failed to load analysis: {(error as Error).message}</Typography>
        </Paper>
      )}

      {analysis && (
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <StatCard title="RSI < 50 (within MACD-V 120–150)" stats={analysis.summary.rsi_lt_50} />
              </Grid>
              <Grid item xs={12} md={6}>
                <StatCard title="RSI ≥ 50 (within MACD-V 120–150)" stats={analysis.summary.rsi_gte_50} />
              </Grid>
              <Grid item xs={12}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Interpretation: when RSI-MA percentile is ≥50 inside a strong MACD-V regime (120–150), you’re often
                    getting less of a “pullback”, and D7 follow-through is more mixed. This is an observation (not proof
                    of causality).
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          </Grid>

          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} md={6}>
                  <Typography variant="h6">Band Tables</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Choose a metric and compare bands across tickers (includes ALL row).
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Metric</InputLabel>
                    <Select value={metric} label="Metric" onChange={(e) => setMetric(e.target.value as Metric)}>
                      <MenuItem value="n">Sample size (n)</MenuItem>
                      <MenuItem value="win_rate">Win rate</MenuItem>
                      <MenuItem value="mean">Mean return</MenuItem>
                      <MenuItem value="median">Median return</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          <Grid item xs={12}>
            <MetricTable
              analysis={analysis}
              metric={metric}
              title={
                metric === 'n'
                  ? 'Sample Size (n)'
                  : metric === 'win_rate'
                    ? 'Win Rate'
                    : metric === 'mean'
                      ? 'Mean Return'
                      : 'Median Return'
              }
            />
          </Grid>

          <Grid item xs={12}>
            <NonOverlapTable analysis={analysis} />
          </Grid>
        </Grid>
      )}
    </Box>
  );
}
