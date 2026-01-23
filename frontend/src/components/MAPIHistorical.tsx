import React, { useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  FormControlLabel,
  Grid,
  Paper,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useQuery } from '@tanstack/react-query';
import { mapiApi } from '@/api/client';

interface MAPIHistoricalProps {
  ticker: string;
}

const fmt = (v: number | null | undefined, decimals: number = 2) => {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  return v.toFixed(decimals);
};

const MAPIHistorical: React.FC<MAPIHistoricalProps> = ({ ticker }) => {
  const [lookbackDays, setLookbackDays] = useState(1095);
  const [requireMomentum, setRequireMomentum] = useState(false);
  const [adxThreshold, setAdxThreshold] = useState(25);

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['mapi-historical', ticker, lookbackDays, requireMomentum, adxThreshold],
    queryFn: async () =>
      mapiApi.getMAPIHistorical(ticker, {
        lookback_days: lookbackDays,
        require_momentum: requireMomentum,
        adx_threshold: adxThreshold,
      }),
    staleTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
  });

  const zones = data?.zone_stats || {};
  const binStats = data?.bin_stats || [];
  const signalStats = data?.signal_stats || {};
  const horizons: number[] = data?.horizons || [3, 7, 14, 21];
  const focusHorizon = horizons.includes(7) ? 7 : horizons[0] || 7;

  const zoneCards = useMemo(
    () => [
      { key: 'extreme_low', title: 'Extreme Low (0–20%)' },
      { key: 'low', title: 'Low (20–35%)' },
      { key: 'pullback_zone', title: 'Pullback (30–45%)' },
      { key: 'strong_momentum', title: 'Strong (65–100%)' },
      { key: 'all', title: 'All (0–100%)' },
    ],
    []
  );

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Failed to load MAPI historical analysis: {error instanceof Error ? error.message : 'Unknown error'}
      </Alert>
    );
  }

  if (!data?.success) {
    return <Alert severity="warning">No historical analysis available for {ticker}</Alert>;
  }

  return (
    <Box>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={8}>
            <Typography variant="h6">MAPI Historical (Percentile → Forward Returns)</Typography>
            <Typography variant="body2" color="text.secondary">
              Empirical mapping of MAPI composite percentile to forward returns ({horizons.join(', ')} days).
            </Typography>
          </Grid>
          <Grid item xs={12} md={4} textAlign="right">
            <Button variant="contained" startIcon={<RefreshIcon />} onClick={() => refetch()} disabled={isFetching}>
              {isFetching ? 'Refreshing…' : 'Refresh'}
            </Button>
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              label="Lookback days"
              type="number"
              size="small"
              value={lookbackDays}
              onChange={(e) => setLookbackDays(Math.max(200, Number(e.target.value || 0)))}
              fullWidth
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField
              label="ADX threshold"
              type="number"
              size="small"
              value={adxThreshold}
              onChange={(e) => setAdxThreshold(Math.max(5, Number(e.target.value || 0)))}
              fullWidth
              disabled={!requireMomentum}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <FormControlLabel
              control={<Switch checked={requireMomentum} onChange={(_, v) => setRequireMomentum(v)} />}
              label="Only ADX momentum rows"
            />
          </Grid>
        </Grid>
      </Paper>

      <Grid container spacing={2} sx={{ mb: 2 }}>
        {zoneCards.map((z) => {
          const row = zones?.[z.key] || {};
          const count = row.count ?? 0;
          const meanKey = `mean_return_${focusHorizon}d`;
          const winKey = `win_rate_${focusHorizon}d`;
          return (
            <Grid item xs={12} sm={6} md={4} key={z.key}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom variant="body2">
                    {z.title}
                  </Typography>
                  <Typography variant="h6">{count} samples</Typography>
                  <Typography variant="body2">
                    Win rate ({focusHorizon}d): {fmt(row[winKey], 1)}%
                  </Typography>
                  <Typography variant="body2">
                    Avg return ({focusHorizon}d): {fmt(row[meanKey], 2)}%
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      <Grid container spacing={2} sx={{ mb: 2 }}>
        {[
          { key: 'pullback_entry', title: 'Pullback Entry Signal' },
          { key: 'strong_momentum_entry', title: 'Strong Momentum Signal' },
          { key: 'exit_signal', title: 'Exit Signal' },
        ].map((s) => {
          const row = signalStats?.[s.key] || {};
          const count = row.count ?? 0;
          const meanKey = `mean_return_${focusHorizon}d`;
          const winKey = `win_rate_${focusHorizon}d`;
          return (
            <Grid item xs={12} md={4} key={s.key}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom variant="body2">
                    {s.title}
                  </Typography>
                  <Typography variant="h6">{count} signals</Typography>
                  <Typography variant="body2">
                    Win rate ({focusHorizon}d): {fmt(row[winKey], 1)}%
                  </Typography>
                  <Typography variant="body2">
                    Avg return ({focusHorizon}d): {fmt(row[meanKey], 2)}%
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ backgroundColor: 'primary.dark' }}>
              <TableCell>
                <Typography variant="subtitle2" color="white">
                  Composite %ile Bin
                </Typography>
              </TableCell>
              <TableCell align="right">
                <Typography variant="subtitle2" color="white">
                  N
                </Typography>
              </TableCell>
              {horizons.map((h) => (
                <TableCell key={`h-${h}`} align="right">
                  <Typography variant="subtitle2" color="white">
                    Mean {h}d
                  </Typography>
                </TableCell>
              ))}
              {horizons.map((h) => (
                <TableCell key={`w-${h}`} align="right">
                  <Typography variant="subtitle2" color="white">
                    Win {h}d
                  </Typography>
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {binStats.map((b: any) => (
              <TableRow key={b.bin_label} sx={{ '&:hover': { backgroundColor: 'action.hover' } }}>
                <TableCell>{b.bin_label}</TableCell>
                <TableCell align="right">{b.count}</TableCell>
                {horizons.map((h) => (
                  <TableCell key={`${b.bin_label}-m-${h}`} align="right">
                    {fmt(b.horizons?.[`${h}d`]?.mean, 2)}%
                  </TableCell>
                ))}
                {horizons.map((h) => (
                  <TableCell key={`${b.bin_label}-w-${h}`} align="right">
                    {fmt(b.horizons?.[`${h}d`]?.win_rate, 1)}%
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Paper sx={{ p: 2, mt: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Sample size used: {data.sample_size} rows · Cached: {String(!!data.cached)}
        </Typography>
      </Paper>
    </Box>
  );
};

export default MAPIHistorical;
