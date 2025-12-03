import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Slider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';

type DurationGroup = {
  avg: number | null;
  median: number | null;
  p25: number | null;
  p75: number | null;
  escape_time_avg: number | null;
  escape_rate: number | null;
  time_to_first_profit_avg: number | null;
  time_to_first_profit_median: number | null;
  sample_size: number;
};

type DurationComparison = {
  winner_vs_loser_ratio: number | null;
  stagnation_rate: number | null;
  statistical_significance_p: number | null;
  predictive_value: string | null;
};

type DurationResponse = {
  ticker: string;
  threshold: number;
  sample_size: number;
  thresholds_tracked: number[];
  winners: DurationGroup;
  losers: DurationGroup;
  comparison: DurationComparison;
  per_threshold: Record<string, DurationGroup>;
  ticker_profile: {
    bounce_speed: string;
    median_escape_time_winners: number | null;
    median_time_to_first_profit: number | null;
    recommendation: string;
  };
  metadata: {
    max_horizon: number;
    outcome_day: number;
    event_count_all_thresholds: number;
  };
};

interface SwingDurationPanelProps {
  tickers: string[];
  selectedTicker?: string;
  onTickerChange?: (ticker: string) => void;
  defaultThreshold?: number;
}

const API_BASE_URL = import.meta.env?.VITE_API_URL || '';

const marks = [
  { value: 5, label: '5%' },
  { value: 10, label: '10%' },
  { value: 15, label: '15%' },
];

const formatNumber = (value: number | null | undefined, digits = 1) => {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return value.toFixed(digits);
};

const formatPercent = (value: number | null | undefined, digits = 1) => {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return `${(value * 100).toFixed(digits)}%`;
};

export const SwingDurationPanel: React.FC<SwingDurationPanelProps> = ({
  tickers,
  selectedTicker,
  onTickerChange,
  defaultThreshold = 5,
}) => {
  const [ticker, setTicker] = useState<string>(selectedTicker || tickers[0]);
  const [threshold, setThreshold] = useState<number>(defaultThreshold);
  const [data, setData] = useState<DurationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedTicker) {
      setTicker(selectedTicker);
    }
  }, [selectedTicker]);

  useEffect(() => {
    if (!ticker) return;
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await axios.get(`${API_BASE_URL}/api/swing-duration/${ticker}`, {
          params: { threshold },
        });
        setData(response.data);
      } catch (err: any) {
        const message = err?.response?.data?.detail || err?.message || 'Failed to load duration analysis';
        setError(message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [ticker, threshold]);

  const winnerLoserRows = useMemo(() => {
    if (!data) return [];
    return [
      { label: 'Avg days in low zone', winner: data.winners.avg, loser: data.losers.avg, suffix: ' days' },
      { label: 'Median days in low zone', winner: data.winners.median, loser: data.losers.median, suffix: ' days' },
      { label: 'Escape time (avg)', winner: data.winners.escape_time_avg, loser: data.losers.escape_time_avg, suffix: ' days' },
      { label: 'Time to first profit (median)', winner: data.winners.time_to_first_profit_median, loser: data.losers.time_to_first_profit_median, suffix: ' days' },
      { label: 'Escape rate', winner: data.winners.escape_rate, loser: data.losers.escape_rate, suffix: ' rate', format: formatPercent },
    ];
  }, [data]);

  const handleTickerChange = (value: string) => {
    setTicker(value);
    onTickerChange?.(value);
  };

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2, mb: 2 }}>
        <Box>
          <Typography variant="h6">Swing Duration Analysis</Typography>
          <Typography variant="body2" color="text.secondary">
            How long entries stay in low percentile zones before escaping or becoming profitable.
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <FormControl size="small">
            <InputLabel>Ticker</InputLabel>
            <Select
              value={ticker}
              label="Ticker"
              onChange={(e) => handleTickerChange(e.target.value)}
              sx={{ minWidth: 140 }}
            >
              {tickers.map(t => (
                <MenuItem key={t} value={t}>{t}</MenuItem>
              ))}
            </Select>
          </FormControl>

          <Box sx={{ width: 220 }}>
            <Typography variant="caption" color="text.secondary">Entry Threshold</Typography>
            <Slider
              size="small"
              value={threshold}
              min={5}
              max={15}
              step={5}
              marks={marks}
              onChange={(_, value) => setThreshold(value as number)}
              valueLabelDisplay="auto"
              valueLabelFormat={(val) => `${val}%`}
            />
          </Box>
        </Box>
      </Box>

      {loading && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <CircularProgress />
          <Typography variant="body2" sx={{ mt: 1 }}>Loading duration stats for {ticker}...</Typography>
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {!loading && !error && data && (
        <>
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="caption" color="text.secondary">Sample Size</Typography>
                  <Typography variant="h5" fontWeight="bold">{data.sample_size}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Total events (≤{data.threshold}%): {data.sample_size} of {data.metadata.event_count_all_thresholds}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="caption" color="text.secondary">Bounce Profile</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                    <Chip label={data.ticker_profile.bounce_speed.replace('_', ' ')} color="primary" size="small" />
                    <Chip
                      label={data.comparison.predictive_value ? data.comparison.predictive_value.toUpperCase() : 'N/A'}
                      size="small"
                      variant="outlined"
                      color={data.comparison.predictive_value === 'high' ? 'success' : 'default'}
                    />
                  </Box>
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    {data.ticker_profile.recommendation}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="caption" color="text.secondary">Stagnation & Significance</Typography>
                  <Typography variant="body1">
                    Stagnation: {formatPercent(data.comparison.stagnation_rate, 0)}
                  </Typography>
                  <Typography variant="body1">
                    p-value: {formatNumber(data.comparison.statistical_significance_p, 3)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Winner/Loser ratio: {formatNumber(data.comparison.winner_vs_loser_ratio, 2)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Typography variant="subtitle1" gutterBottom>Winner vs Loser Duration</Typography>
          <TableContainer component={Paper} variant="outlined" sx={{ mb: 3 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Metric</strong></TableCell>
                  <TableCell align="right"><strong>Winners</strong></TableCell>
                  <TableCell align="right"><strong>Losers</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {winnerLoserRows.map(row => (
                  <TableRow key={row.label}>
                    <TableCell>{row.label}</TableCell>
                    <TableCell align="right">
                      {row.format ? row.format(row.winner) : `${formatNumber(row.winner)}${row.suffix ? ` ${row.suffix}` : ''}`}
                    </TableCell>
                    <TableCell align="right">
                      {row.format ? row.format(row.loser) : `${formatNumber(row.loser)}${row.suffix ? ` ${row.suffix}` : ''}`}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <Divider sx={{ my: 2 }} />

          <Typography variant="subtitle1" gutterBottom>Per-Threshold Patience Profile</Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Threshold</strong></TableCell>
                  <TableCell align="right"><strong>Avg Days ≤ Threshold</strong></TableCell>
                  <TableCell align="right"><strong>Median Days</strong></TableCell>
                  <TableCell align="right"><strong>Escape Time (avg)</strong></TableCell>
                  <TableCell align="right"><strong>Escape Rate</strong></TableCell>
                  <TableCell align="right"><strong>Time to First Profit (median)</strong></TableCell>
                  <TableCell align="right"><strong>Samples</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.thresholds_tracked.map((th) => {
                  const key = Number.isInteger(th) ? String(th) : th.toString();
                  const stats = data.per_threshold[key];
                  return (
                    <TableRow key={th}>
                      <TableCell>≤{th}%</TableCell>
                      <TableCell align="right">{formatNumber(stats?.avg)} days</TableCell>
                      <TableCell align="right">{formatNumber(stats?.median)} days</TableCell>
                      <TableCell align="right">{formatNumber(stats?.escape_time_avg)} days</TableCell>
                      <TableCell align="right">{formatPercent(stats?.escape_rate, 0)}</TableCell>
                      <TableCell align="right">{formatNumber(stats?.time_to_first_profit_median)} days</TableCell>
                      <TableCell align="right">{stats?.sample_size ?? 0}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}
    </Paper>
  );
};
