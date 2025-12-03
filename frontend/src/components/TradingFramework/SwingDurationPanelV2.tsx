import React, { useEffect, useState } from 'react';
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AccessTime,
  Speed,
  Warning,
  CheckCircle,
} from '@mui/icons-material';

interface ThresholdStats {
  sample_size: number;
  avg_days_in_low: number | null;
  median_days_in_low: number | null;
  p25_days: number | null;
  p75_days: number | null;
  avg_escape_time: number | null;
  escape_rate: number | null;
  avg_time_to_profit: number | null;
  median_time_to_profit: number | null;
}

interface DurationResponse {
  ticker: string;
  entry_threshold: number;
  sample_size: number;
  data_source: string;
  winners: {
    count: number;
    threshold_5pct: ThresholdStats;
    threshold_10pct: ThresholdStats;
    threshold_15pct: ThresholdStats;
  };
  losers: {
    count: number;
    threshold_5pct: ThresholdStats;
    threshold_10pct: ThresholdStats;
    threshold_15pct: ThresholdStats;
  };
  comparison: {
    statistical_significance_p: number | null;
    predictive_value: string;
    winner_vs_loser_ratio_5pct: number | null;
  };
  ticker_profile: {
    bounce_speed: string;
    median_escape_time_winners: number | null;
    recommendation: string;
  };
}

interface SwingDurationPanelV2Props {
  tickers: string[];
  selectedTicker?: string;
  onTickerChange?: (ticker: string) => void;
  defaultThreshold?: number;
}

const API_BASE_URL = import.meta.env?.VITE_API_URL || '';

const formatNumber = (value: number | null | undefined, digits = 1) => {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return value.toFixed(digits);
};

const formatPercent = (value: number | null | undefined, digits = 0) => {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return `${(value * 100).toFixed(digits)}%`;
};

const getBounceSpeedColor = (speed: string) => {
  switch (speed) {
    case 'fast_bouncer':
      return 'success';
    case 'balanced':
      return 'primary';
    case 'slow_bouncer':
      return 'warning';
    default:
      return 'default';
  }
};

const getInsightIcon = (ratio: number | null) => {
  if (!ratio) return null;
  if (ratio > 1.5) return <TrendingUp color="success" />;
  if (ratio < 0.7) return <TrendingDown color="error" />;
  return <AccessTime color="primary" />;
};

export const SwingDurationPanelV2: React.FC<SwingDurationPanelV2Props> = ({
  tickers,
  selectedTicker,
  onTickerChange,
  defaultThreshold = 5,
}) => {
  const [ticker, setTicker] = useState<string>(selectedTicker || tickers[0]);
  const [threshold] = useState<number>(defaultThreshold);
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
          params: { threshold, use_sample_data: false }, // ALWAYS use live data
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

  const handleTickerChange = (value: string) => {
    setTicker(value);
    onTickerChange?.(value);
  };

  // Generate actionable insights
  const getActionableInsights = () => {
    if (!data) return [];

    const insights: Array<{ type: 'success' | 'warning' | 'info' | 'error'; message: string }> = [];

    const w5 = data.winners.threshold_5pct;
    const l5 = data.losers.threshold_5pct;
    const ratio = data.comparison.winner_vs_loser_ratio_5pct;

    // Data source warning
    if (data.data_source === 'sample') {
      insights.push({
        type: 'warning',
        message: '⚠️ Using SAMPLE data - live fetch may have failed. Results may not reflect current market conditions.',
      });
    } else {
      insights.push({
        type: 'success',
        message: '✓ Using LIVE market data - insights are current and actionable.',
      });
    }

    // Sample size check
    if (data.sample_size < 20) {
      insights.push({
        type: 'warning',
        message: `⚠️ Small sample size (${data.sample_size} trades). Increase confidence by waiting for more signals.`,
      });
    }

    // Winner/Loser behavior insights
    if (ratio && ratio > 1.5) {
      insights.push({
        type: 'info',
        message: `📊 Winners stay ${formatNumber(ratio, 2)}x longer in low zones before bouncing. Patience is key - don't exit early.`,
      });
    } else if (ratio && ratio < 0.7) {
      insights.push({
        type: 'error',
        message: `⚠️ Losers stay ${formatNumber(1/ratio, 2)}x longer in low zones. Quick escape = good sign. Prolonged stagnation = exit signal.`,
      });
    }

    // Bounce speed insights
    if (data.ticker_profile.bounce_speed === 'fast_bouncer') {
      insights.push({
        type: 'success',
        message: `⚡ ${ticker} is a FAST BOUNCER (median escape: ${formatNumber(data.ticker_profile.median_escape_time_winners)}d). Monitor intraday for quick exits.`,
      });
    } else if (data.ticker_profile.bounce_speed === 'slow_bouncer') {
      insights.push({
        type: 'warning',
        message: `🐌 ${ticker} is a SLOW BOUNCER (median escape: ${formatNumber(data.ticker_profile.median_escape_time_winners)}d). Requires 4+ days patience before typical bounce.`,
      });
    }

    // Time to profit insights
    if (w5.median_time_to_profit && w5.median_time_to_profit <= 1) {
      insights.push({
        type: 'success',
        message: `💰 Winners typically profitable within ${formatNumber(w5.median_time_to_profit)} day. Quick turnaround expected.`,
      });
    } else if (w5.median_time_to_profit && w5.median_time_to_profit >= 3) {
      insights.push({
        type: 'info',
        message: `⏳ Winners take ${formatNumber(w5.median_time_to_profit)} days median to first profit. Plan for multi-day hold.`,
      });
    }

    // Statistical significance
    if (data.comparison.statistical_significance_p && data.comparison.statistical_significance_p < 0.05) {
      insights.push({
        type: 'success',
        message: `✓ Statistically significant difference between winners/losers (p=${formatNumber(data.comparison.statistical_significance_p, 3)}). Duration metrics are predictive.`,
      });
    } else {
      insights.push({
        type: 'info',
        message: `⚠️ No statistically significant difference (p=${formatNumber(data.comparison.statistical_significance_p || 0, 3)}). Duration alone may not predict outcomes for ${ticker}.`,
      });
    }

    return insights;
  };

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h5" fontWeight="bold">
            SWING Duration Analysis V2
          </Typography>
          <Typography variant="body2" color="text.secondary">
            How long do trades stay in low percentile zones? Winners vs Losers comparative analysis.
          </Typography>
        </Box>

        <FormControl size="small">
          <InputLabel>Ticker</InputLabel>
          <Select
            value={ticker}
            label="Ticker"
            onChange={(e) => handleTickerChange(e.target.value)}
            sx={{ minWidth: 140 }}
          >
            {tickers.map((t) => (
              <MenuItem key={t} value={t}>
                {t}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {loading && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <CircularProgress />
          <Typography variant="body2" sx={{ mt: 1 }}>
            Analyzing duration patterns for {ticker}...
          </Typography>
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {!loading && !error && data && (
        <>
          {/* Actionable Insights */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              📋 Actionable Insights
            </Typography>
            {getActionableInsights().map((insight, idx) => (
              <Alert key={idx} severity={insight.type} sx={{ mb: 1 }}>
                {insight.message}
              </Alert>
            ))}
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* Key Metrics Overview */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} md={3}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="caption" color="text.secondary">
                    Sample Size
                  </Typography>
                  <Typography variant="h4" fontWeight="bold">
                    {data.sample_size}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {data.winners.count}W / {data.losers.count}L
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="caption" color="text.secondary">
                    Bounce Speed
                  </Typography>
                  <Box sx={{ mt: 1 }}>
                    <Chip
                      label={data.ticker_profile.bounce_speed.replace('_', ' ').toUpperCase()}
                      color={getBounceSpeedColor(data.ticker_profile.bounce_speed)}
                      icon={<Speed />}
                    />
                  </Box>
                  <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
                    Median escape: {formatNumber(data.ticker_profile.median_escape_time_winners)}d
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="caption" color="text.secondary">
                    Winner/Loser Ratio
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                    {getInsightIcon(data.comparison.winner_vs_loser_ratio_5pct)}
                    <Typography variant="h5" fontWeight="bold">
                      {formatNumber(data.comparison.winner_vs_loser_ratio_5pct, 2)}x
                    </Typography>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    Days in low zone (5%)
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="caption" color="text.secondary">
                    Predictive Value
                  </Typography>
                  <Box sx={{ mt: 1 }}>
                    <Chip
                      label={data.comparison.predictive_value.toUpperCase()}
                      color={data.comparison.predictive_value === 'high' ? 'success' : 'default'}
                      icon={data.comparison.predictive_value === 'high' ? <CheckCircle /> : <Warning />}
                      variant="outlined"
                    />
                  </Box>
                  <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
                    p-value: {formatNumber(data.comparison.statistical_significance_p, 3)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Winners vs Losers Comparison */}
          <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
            🏆 Winners vs ❌ Losers: Duration Comparison (≤5% Threshold)
          </Typography>
          <TableContainer component={Paper} variant="outlined" sx={{ mb: 3 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Metric</strong></TableCell>
                  <TableCell align="right"><strong>🏆 Winners ({data.winners.count})</strong></TableCell>
                  <TableCell align="right"><strong>❌ Losers ({data.losers.count})</strong></TableCell>
                  <TableCell align="right"><strong>Difference</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Avg Days in Low Zone</TableCell>
                  <TableCell align="right">{formatNumber(data.winners.threshold_5pct.avg_days_in_low)} days</TableCell>
                  <TableCell align="right">{formatNumber(data.losers.threshold_5pct.avg_days_in_low)} days</TableCell>
                  <TableCell align="right">
                    {data.comparison.winner_vs_loser_ratio_5pct
                      ? `${formatNumber(data.comparison.winner_vs_loser_ratio_5pct, 2)}x`
                      : '—'}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Median Days in Low Zone</TableCell>
                  <TableCell align="right">{formatNumber(data.winners.threshold_5pct.median_days_in_low)} days</TableCell>
                  <TableCell align="right">{formatNumber(data.losers.threshold_5pct.median_days_in_low)} days</TableCell>
                  <TableCell align="right">—</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Avg Escape Time</TableCell>
                  <TableCell align="right">{formatNumber(data.winners.threshold_5pct.avg_escape_time)} days</TableCell>
                  <TableCell align="right">{formatNumber(data.losers.threshold_5pct.avg_escape_time)} days</TableCell>
                  <TableCell align="right">—</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Median Time to First Profit</TableCell>
                  <TableCell align="right">{formatNumber(data.winners.threshold_5pct.median_time_to_profit)} days</TableCell>
                  <TableCell align="right">{formatNumber(data.losers.threshold_5pct.median_time_to_profit)} days</TableCell>
                  <TableCell align="right">—</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Escape Rate</TableCell>
                  <TableCell align="right">{formatPercent(data.winners.threshold_5pct.escape_rate)}</TableCell>
                  <TableCell align="right">{formatPercent(data.losers.threshold_5pct.escape_rate)}</TableCell>
                  <TableCell align="right">—</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          {/* Multi-Threshold Analysis */}
          <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
            📊 Multi-Threshold Duration Profile (Winners Only)
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Threshold</strong></TableCell>
                  <TableCell align="right"><strong>Avg Days in Low</strong></TableCell>
                  <TableCell align="right"><strong>Median Days</strong></TableCell>
                  <TableCell align="right"><strong>Avg Escape Time</strong></TableCell>
                  <TableCell align="right"><strong>Median Time to Profit</strong></TableCell>
                  <TableCell align="right"><strong>Escape Rate</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>≤ 5%</TableCell>
                  <TableCell align="right">{formatNumber(data.winners.threshold_5pct.avg_days_in_low)} days</TableCell>
                  <TableCell align="right">{formatNumber(data.winners.threshold_5pct.median_days_in_low)} days</TableCell>
                  <TableCell align="right">{formatNumber(data.winners.threshold_5pct.avg_escape_time)} days</TableCell>
                  <TableCell align="right">{formatNumber(data.winners.threshold_5pct.median_time_to_profit)} days</TableCell>
                  <TableCell align="right">{formatPercent(data.winners.threshold_5pct.escape_rate)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>≤ 10%</TableCell>
                  <TableCell align="right">{formatNumber(data.winners.threshold_10pct.avg_days_in_low)} days</TableCell>
                  <TableCell align="right">{formatNumber(data.winners.threshold_10pct.median_days_in_low)} days</TableCell>
                  <TableCell align="right">{formatNumber(data.winners.threshold_10pct.avg_escape_time)} days</TableCell>
                  <TableCell align="right">{formatNumber(data.winners.threshold_10pct.median_time_to_profit)} days</TableCell>
                  <TableCell align="right">{formatPercent(data.winners.threshold_10pct.escape_rate)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>≤ 15%</TableCell>
                  <TableCell align="right">{formatNumber(data.winners.threshold_15pct.avg_days_in_low)} days</TableCell>
                  <TableCell align="right">{formatNumber(data.winners.threshold_15pct.median_days_in_low)} days</TableCell>
                  <TableCell align="right">{formatNumber(data.winners.threshold_15pct.avg_escape_time)} days</TableCell>
                  <TableCell align="right">{formatNumber(data.winners.threshold_15pct.median_time_to_profit)} days</TableCell>
                  <TableCell align="right">{formatPercent(data.winners.threshold_15pct.escape_rate)}</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          {/* Recommendation */}
          <Card sx={{ mt: 3, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                💡 Trading Recommendation
              </Typography>
              <Typography variant="body1">{data.ticker_profile.recommendation}</Typography>
            </CardContent>
          </Card>
        </>
      )}
    </Paper>
  );
};
