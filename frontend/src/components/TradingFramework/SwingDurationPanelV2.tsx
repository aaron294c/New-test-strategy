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

type DurationUnit = 'days' | 'hours';

interface ThresholdStats {
  sample_size: number;
  avg_days_in_low?: number | null;
  median_days_in_low?: number | null;
  p25_days?: number | null;
  p75_days?: number | null;
  avg_escape_time?: number | null;
  escape_rate: number | null;
  avg_time_to_profit?: number | null;
  median_time_to_profit?: number | null;
  // Intraday (hours) variants
  avg_hours_in_low?: number | null;
  median_hours_in_low?: number | null;
  avg_escape_time_hours?: number | null;
  avg_hours_to_profit?: number | null;
  median_hours_to_profit?: number | null;
}

interface DurationResponse {
  ticker: string;
  entry_threshold: number;
  sample_size: number;
  data_source: string;
  duration_unit?: DurationUnit;
  duration_granularity?: string;
  bar_interval_hours?: number;
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
    median_escape_time_winners?: number | null;
    median_escape_hours_winners?: number | null;
    median_escape_days_winners?: number | null;
    duration_unit?: DurationUnit;
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

const resolveDurationUnit = (data?: DurationResponse): DurationUnit =>
  data?.duration_unit === 'hours' ? 'hours' : 'days';

const formatDurationValue = (
  value: number | null | undefined,
  unit: DurationUnit,
  digits = 1
) => {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  const suffix = unit === 'hours' ? 'h' : 'd';
  return `${value.toFixed(digits)}${suffix}`;
};

const pickAvgInLow = (stats: ThresholdStats, unit: DurationUnit) =>
  unit === 'hours' ? stats.avg_hours_in_low ?? null : stats.avg_days_in_low ?? null;

const pickMedianInLow = (stats: ThresholdStats, unit: DurationUnit) =>
  unit === 'hours' ? stats.median_hours_in_low ?? null : stats.median_days_in_low ?? null;

const pickAvgEscape = (stats: ThresholdStats, unit: DurationUnit) =>
  unit === 'hours'
    ? stats.avg_escape_time_hours ?? stats.avg_escape_time ?? null
    : stats.avg_escape_time ?? null;

const pickMedianTimeToProfit = (stats: ThresholdStats, unit: DurationUnit) =>
  unit === 'hours'
    ? stats.median_hours_to_profit ?? stats.median_time_to_profit ?? null
    : stats.median_time_to_profit ?? null;

const pickMedianEscapeFromProfile = (
  profile: DurationResponse['ticker_profile'],
  unit: DurationUnit
) => {
  if (unit === 'hours') {
    return profile.median_escape_hours_winners
      ?? profile.median_escape_time_winners
      ?? null;
  }
  return profile.median_escape_days_winners
    ?? profile.median_escape_time_winners
    ?? null;
};

// Convert duration to TRADING days (not calendar days)
// For 4H bars: market is open 6.5 hours/day, so 1 trading day = 6.5 hours
const MARKET_HOURS_PER_DAY = 6.5;

const convertDurationToDays = (value: number | null | undefined, unit: DurationUnit) => {
  if (value === null || value === undefined) return null;
  // CRITICAL: Use market hours for accurate day conversion (NOT 24 hours!)
  return unit === 'hours' ? value / MARKET_HOURS_PER_DAY : value;
};

const getBounceSpeedColor = (speed: string) => {
  switch (speed) {
    case 'ultra_fast_bouncer':
      return 'success';  // Ultra fast = green
    case 'fast_bouncer':
      return 'success';  // Fast = green
    case 'balanced':
      return 'primary';  // Balanced = blue
    case 'slow_bouncer':
      return 'warning';  // Slow = orange
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
  const [timeframe, setTimeframe] = useState<'daily' | 'intraday'>('daily');
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
          params: { threshold, use_sample_data: false, timeframe }, // ALWAYS use live data
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
  }, [ticker, threshold, timeframe]);

  const durationUnit: DurationUnit = resolveDurationUnit(data || undefined);
  const durationLabel = durationUnit === 'hours' ? 'hours' : 'days';
  const medianEscape = data ? pickMedianEscapeFromProfile(data.ticker_profile, durationUnit) : null;

  const handleTickerChange = (value: string) => {
    setTicker(value);
    onTickerChange?.(value);
  };

  // Generate actionable insights
  const getActionableInsights = () => {
    if (!data) return [];

    const insights: Array<{ type: 'success' | 'warning' | 'info' | 'error'; message: string }> = [];

    const w5 = data.winners.threshold_5pct;
    const ratio = data.comparison.winner_vs_loser_ratio_5pct;
    const medianEscape = pickMedianEscapeFromProfile(data.ticker_profile, durationUnit);
    const medianEscapeText = formatDurationValue(medianEscape, durationUnit);
    const medianTimeToProfit = pickMedianTimeToProfit(w5, durationUnit);
    const medianTimeToProfitDays = convertDurationToDays(medianTimeToProfit, durationUnit);

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
        message: `⚡ ${ticker} is a FAST BOUNCER (median escape: ${medianEscapeText}). Monitor intraday for quick exits.`,
      });
    } else if (data.ticker_profile.bounce_speed === 'slow_bouncer') {
      insights.push({
        type: 'warning',
        message: `🐌 ${ticker} is a SLOW BOUNCER (median escape: ${medianEscapeText}). Requires extended patience before typical bounce.`,
      });
    }

    // Time to profit insights (adjusted for proper trading day calculations)
    if (medianTimeToProfitDays && medianTimeToProfitDays <= 1.5) {
      insights.push({
        type: 'success',
        message: `💰 Winners typically profitable within ${formatDurationValue(medianTimeToProfit, durationUnit)} (${formatNumber(medianTimeToProfitDays, 1)} trading days). Quick turnaround expected.`,
      });
    } else if (medianTimeToProfitDays && medianTimeToProfitDays >= 4) {
      insights.push({
        type: 'info',
        message: `⏳ Winners take ${formatDurationValue(medianTimeToProfit, durationUnit)} (${formatNumber(medianTimeToProfitDays, 1)} trading days) median to first profit. Plan for a longer hold.`,
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

        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
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

          <FormControl size="small">
            <InputLabel>Resolution</InputLabel>
            <Select
              value={timeframe}
              label="Resolution"
              onChange={(e) => setTimeframe(e.target.value as 'daily' | 'intraday')}
              sx={{ minWidth: 180 }}
            >
              <MenuItem value="daily">Daily (1D)</MenuItem>
              <MenuItem value="intraday">Intraday (4H bars)</MenuItem>
            </Select>
          </FormControl>
        </Box>
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
                    Median escape: {formatDurationValue(medianEscape, durationUnit)}
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
                    Time in low zone (5%)
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
                  <TableCell>Avg Time in Low Zone</TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickAvgInLow(data.winners.threshold_5pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickAvgInLow(data.losers.threshold_5pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {data.comparison.winner_vs_loser_ratio_5pct
                      ? `${formatNumber(data.comparison.winner_vs_loser_ratio_5pct, 2)}x`
                      : '—'}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Median Time in Low Zone</TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickMedianInLow(data.winners.threshold_5pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickMedianInLow(data.losers.threshold_5pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">—</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Avg Escape Time</TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickAvgEscape(data.winners.threshold_5pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickAvgEscape(data.losers.threshold_5pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">—</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Median Time to First Profit</TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickMedianTimeToProfit(data.winners.threshold_5pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickMedianTimeToProfit(data.losers.threshold_5pct, durationUnit), durationUnit)}
                  </TableCell>
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
                  <TableCell align="right"><strong>Avg Time in Low ({durationLabel})</strong></TableCell>
                  <TableCell align="right"><strong>Median Time</strong></TableCell>
                  <TableCell align="right"><strong>Avg Escape Time</strong></TableCell>
                  <TableCell align="right"><strong>Median Time to Profit</strong></TableCell>
                  <TableCell align="right"><strong>Escape Rate</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>≤ 5%</TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickAvgInLow(data.winners.threshold_5pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickMedianInLow(data.winners.threshold_5pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickAvgEscape(data.winners.threshold_5pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickMedianTimeToProfit(data.winners.threshold_5pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">{formatPercent(data.winners.threshold_5pct.escape_rate)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>≤ 10%</TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickAvgInLow(data.winners.threshold_10pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickMedianInLow(data.winners.threshold_10pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickAvgEscape(data.winners.threshold_10pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickMedianTimeToProfit(data.winners.threshold_10pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">{formatPercent(data.winners.threshold_10pct.escape_rate)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>≤ 15%</TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickAvgInLow(data.winners.threshold_15pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickMedianInLow(data.winners.threshold_15pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickAvgEscape(data.winners.threshold_15pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickMedianTimeToProfit(data.winners.threshold_15pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">{formatPercent(data.winners.threshold_15pct.escape_rate)}</TableCell>
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
                  <TableCell align="right"><strong>Avg Time in Low ({durationLabel})</strong></TableCell>
                  <TableCell align="right"><strong>Median Time</strong></TableCell>
                  <TableCell align="right"><strong>Avg Escape Time</strong></TableCell>
                  <TableCell align="right"><strong>Median Time to Profit</strong></TableCell>
                  <TableCell align="right"><strong>Escape Rate</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>≤ 5%</TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickAvgInLow(data.winners.threshold_5pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickMedianInLow(data.winners.threshold_5pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickAvgEscape(data.winners.threshold_5pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickMedianTimeToProfit(data.winners.threshold_5pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">{formatPercent(data.winners.threshold_5pct.escape_rate)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>≤ 10%</TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickAvgInLow(data.winners.threshold_10pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickMedianInLow(data.winners.threshold_10pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickAvgEscape(data.winners.threshold_10pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickMedianTimeToProfit(data.winners.threshold_10pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">{formatPercent(data.winners.threshold_10pct.escape_rate)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>≤ 15%</TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickAvgInLow(data.winners.threshold_15pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickMedianInLow(data.winners.threshold_15pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickAvgEscape(data.winners.threshold_15pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatDurationValue(pickMedianTimeToProfit(data.winners.threshold_15pct, durationUnit), durationUnit)}
                  </TableCell>
                  <TableCell align="right">{formatPercent(data.winners.threshold_15pct.escape_rate)}</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          {/* NEW: Bailout Timer & Risk Signals */}
          <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
            ⏰ Bailout Timer & Risk Management
          </Typography>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ bgcolor: 'success.light', p: 2 }}>
                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                  ✅ WINNER PATTERN (5% Entry)
                </Typography>
                <Box sx={{ pl: 2 }}>
                  <Typography variant="body2">
                    • Escape threshold: {formatDurationValue(pickAvgEscape(data.winners.threshold_5pct, durationUnit), durationUnit)}
                    {durationUnit === 'hours' && ` (${formatNumber((pickAvgEscape(data.winners.threshold_5pct, durationUnit) || 0) / 4, 1)} bars)`}
                  </Typography>
                  <Typography variant="body2">
                    • First profit: {formatDurationValue(pickMedianTimeToProfit(data.winners.threshold_5pct, durationUnit), durationUnit)}
                    {durationUnit === 'hours' && ` (${formatNumber((pickMedianTimeToProfit(data.winners.threshold_5pct, durationUnit) || 0) / 4, 1)} bars)`}
                  </Typography>
                  <Typography variant="body2">
                    • Time in low: {formatDurationValue(pickMedianInLow(data.winners.threshold_5pct, durationUnit), durationUnit)}
                    {durationUnit === 'hours' && ` (${formatNumber((pickMedianInLow(data.winners.threshold_5pct, durationUnit) || 0) / 4, 1)} bars)`}
                  </Typography>
                  <Typography variant="body2" fontWeight="bold" sx={{ mt: 1 }}>
                    📊 Action: HOLD if percentile escapes &gt;5%
                  </Typography>
                </Box>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ bgcolor: 'error.light', p: 2 }}>
                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                  ❌ LOSER PATTERN (5% Entry)
                </Typography>
                <Box sx={{ pl: 2 }}>
                  <Typography variant="body2">
                    • Stuck in low: {formatDurationValue(pickMedianInLow(data.losers.threshold_5pct, durationUnit), durationUnit)}
                    {durationUnit === 'hours' && ` (${formatNumber((pickMedianInLow(data.losers.threshold_5pct, durationUnit) || 0) / 4, 1)} bars)`}
                  </Typography>
                  <Typography variant="body2">
                    • False profit: {formatDurationValue(pickMedianTimeToProfit(data.losers.threshold_5pct, durationUnit), durationUnit)}
                    {durationUnit === 'hours' && ` (${formatNumber((pickMedianTimeToProfit(data.losers.threshold_5pct, durationUnit) || 0) / 4, 1)} bars)`}
                  </Typography>
                  <Typography variant="body2" color="error" fontWeight="bold" sx={{ mt: 1 }}>
                    ⚠️ Ratio: {formatNumber(data.comparison.winner_vs_loser_ratio_5pct, 1)}x longer stuck than winners
                  </Typography>
                  <Typography variant="body2" fontWeight="bold" sx={{ mt: 1 }}>
                    🚨 BAILOUT: If still &lt;5% after {formatDurationValue(pickMedianInLow(data.losers.threshold_5pct, durationUnit), durationUnit)} → EXIT
                  </Typography>
                </Box>
              </Card>
            </Grid>
          </Grid>

          {/* NEW: Time-Based Risk Ladder */}
          <Card sx={{ mt: 3, bgcolor: 'warning.light', p: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                ⏱️ Time-Based Risk Ladder (5% Entry)
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Time Elapsed</strong></TableCell>
                      <TableCell><strong>If Still &lt;5%</strong></TableCell>
                      <TableCell><strong>Action</strong></TableCell>
                      <TableCell><strong>Risk Level</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {durationUnit === 'hours' ? (
                      <>
                        <TableRow>
                          <TableCell>0-20h (0-5 bars)</TableCell>
                          <TableCell>Normal winner range</TableCell>
                          <TableCell><Chip label="HOLD" color="success" size="small" /></TableCell>
                          <TableCell><Chip label="LOW" color="success" size="small" variant="outlined" /></TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>24h (6 bars)</TableCell>
                          <TableCell>Exceeding winner median</TableCell>
                          <TableCell><Chip label="MONITOR" color="warning" size="small" /></TableCell>
                          <TableCell><Chip label="MODERATE" color="warning" size="small" variant="outlined" /></TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>40h (10 bars)</TableCell>
                          <TableCell>Entering loser territory</TableCell>
                          <TableCell><Chip label="REDUCE 50%" color="warning" size="small" /></TableCell>
                          <TableCell><Chip label="HIGH" color="error" size="small" variant="outlined" /></TableCell>
                        </TableRow>
                        <TableRow sx={{ bgcolor: 'error.main', '& td': { color: 'white', fontWeight: 'bold' } }}>
                          <TableCell>50h+ (12+ bars)</TableCell>
                          <TableCell>Confirmed loser pattern</TableCell>
                          <TableCell><Chip label="EXIT ALL" color="error" size="small" sx={{ bgcolor: 'white', color: 'error.main' }} /></TableCell>
                          <TableCell><Chip label="CRITICAL" color="error" size="small" sx={{ bgcolor: 'white', color: 'error.main' }} /></TableCell>
                        </TableRow>
                      </>
                    ) : (
                      <>
                        <TableRow>
                          <TableCell>Day 0-1</TableCell>
                          <TableCell>Normal winner range</TableCell>
                          <TableCell><Chip label="HOLD" color="success" size="small" /></TableCell>
                          <TableCell><Chip label="LOW" color="success" size="small" variant="outlined" /></TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Day 2</TableCell>
                          <TableCell>Exceeding winner median</TableCell>
                          <TableCell><Chip label="MONITOR" color="warning" size="small" /></TableCell>
                          <TableCell><Chip label="MODERATE" color="warning" size="small" variant="outlined" /></TableCell>
                        </TableRow>
                        <TableRow sx={{ bgcolor: 'error.main', '& td': { color: 'white', fontWeight: 'bold' } }}>
                          <TableCell>Day 3+</TableCell>
                          <TableCell>Confirmed loser pattern</TableCell>
                          <TableCell><Chip label="EXIT ALL" color="error" size="small" sx={{ bgcolor: 'white', color: 'error.main' }} /></TableCell>
                          <TableCell><Chip label="CRITICAL" color="error" size="small" sx={{ bgcolor: 'white', color: 'error.main' }} /></TableCell>
                        </TableRow>
                      </>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>

          {/* NEW: Critical Signal - Profit Without Percentile Escape */}
          <Alert severity="error" sx={{ mt: 3 }}>
            <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
              🚨 CRITICAL: Monitor Percentile, Not Just P&L
            </Typography>
            <Typography variant="body2">
              <strong>False Profit Signal:</strong> Losers show profit at {formatDurationValue(pickMedianTimeToProfit(data.losers.threshold_5pct, durationUnit), durationUnit)}
              {durationUnit === 'hours' && ` (${formatNumber((pickMedianTimeToProfit(data.losers.threshold_5pct, durationUnit) || 0) / 4, 1)} bars)`},
              but percentile stays &lt;5% and they FADE by day 7.
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              <strong>Winners</strong> take {formatDurationValue(pickMedianTimeToProfit(data.winners.threshold_5pct, durationUnit), durationUnit)}
              {durationUnit === 'hours' && ` (${formatNumber((pickMedianTimeToProfit(data.winners.threshold_5pct, durationUnit) || 0) / 4, 1)} bars)`}
              to profit BUT percentile escapes &gt;5% and sustains.
            </Typography>
            <Typography variant="body2" sx={{ mt: 1, fontWeight: 'bold' }}>
              ✅ RULE: Profit + Percentile Escape &gt;5% = Winner Pattern<br />
              ⚠️ RULE: Profit + Still &lt;5% after {formatDurationValue(pickAvgEscape(data.winners.threshold_5pct, durationUnit), durationUnit)} = False Signal → Prepare to EXIT
            </Typography>
          </Alert>

          {/* NEW: Sniper Entry Analysis (4H vs Daily) */}
          {durationUnit === 'hours' && (
            <Card sx={{ mt: 3, bgcolor: 'info.light', p: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  🎯 SNIPER ENTRY ADVANTAGE: 4-Hourly Leading Indicator
                </Typography>
                <Alert severity="info" sx={{ mb: 2 }}>
                  <Typography variant="body2" fontWeight="bold">
                    4H Resolution gives you INTRADAY precision that Daily misses!
                  </Typography>
                </Alert>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                      📊 4-Hourly Breakdown:
                    </Typography>
                    <Box sx={{ pl: 2 }}>
                      <Typography variant="body2">
                        • Median escape: {formatDurationValue(medianEscape, durationUnit)}
                        {' '}= <strong>{formatNumber((medianEscape || 0) / 4, 1)} bars</strong>
                        {' '}= <strong>{formatNumber((medianEscape || 0) / 6.5, 1)} trading days</strong>
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        • Winner detection: Bar 3-5 (12-20h)
                      </Typography>
                      <Typography variant="body2">
                        • Warning zone: Bar 6+ (24h+)
                      </Typography>
                      <Typography variant="body2">
                        • Bailout signal: Bar 12+ (48-50h)
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                      ⚡ Your Intraday Edge:
                    </Typography>
                    <Box sx={{ pl: 2 }}>
                      <Typography variant="body2">
                        ✅ See winner pattern <strong>2-6 hours earlier</strong> than daily close
                      </Typography>
                      <Typography variant="body2">
                        ✅ Detect false signals <strong>4-8 hours earlier</strong> than daily
                      </Typography>
                      <Typography variant="body2">
                        ✅ Exit losers <strong>4-24 hours earlier</strong> than daily bailout
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 1, fontWeight: 'bold', color: 'success.main' }}>
                        📈 Add to winners at 1:30 PM, not 4:00 PM close!
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                  🎯 Sniper Entry Timeline (AAPL Example):
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell><strong>Time</strong></TableCell>
                        <TableCell><strong>4H Bar</strong></TableCell>
                        <TableCell><strong>What 4H Shows</strong></TableCell>
                        <TableCell><strong>What Daily Shows</strong></TableCell>
                        <TableCell><strong>Your Edge</strong></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      <TableRow>
                        <TableCell>Mon 9:30 AM</TableCell>
                        <TableCell>Bar 0</TableCell>
                        <TableCell>Entry at &lt;5% ✅</TableCell>
                        <TableCell>—</TableCell>
                        <TableCell>Precise entry timing</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Mon 1:30 PM</TableCell>
                        <TableCell>Bar 1</TableCell>
                        <TableCell>Still &lt;5%, monitor</TableCell>
                        <TableCell>—</TableCell>
                        <TableCell>Early progress check</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Tue 9:30 AM</TableCell>
                        <TableCell>Bar 2</TableCell>
                        <TableCell>Building, ~5%</TableCell>
                        <TableCell>—</TableCell>
                        <TableCell>See improvement intraday</TableCell>
                      </TableRow>
                      <TableRow sx={{ bgcolor: 'success.light' }}>
                        <TableCell><strong>Tue 1:30 PM</strong></TableCell>
                        <TableCell><strong>Bar 3</strong></TableCell>
                        <TableCell><strong>ESCAPED &gt;5% ✅</strong></TableCell>
                        <TableCell>—</TableCell>
                        <TableCell><strong>Winner confirmed 2.5h early!</strong></TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Tue 4:00 PM</TableCell>
                        <TableCell>Bar 3 close</TableCell>
                        <TableCell>Sustained &gt;5%</TableCell>
                        <TableCell>Escape confirmed ✅</TableCell>
                        <TableCell>Daily catches up</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
                <Alert severity="success" sx={{ mt: 2 }}>
                  <Typography variant="body2" fontWeight="bold">
                    💡 STRATEGY: Enter on Daily signal, manage with 4H precision. Add positions or take profits at 1:30 PM Bar 3-5, don't wait for 4 PM close!
                  </Typography>
                </Alert>
              </CardContent>
            </Card>
          )}

          {/* Recommendation */}
          <Card sx={{ mt: 3, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                💡 Trading Recommendation
              </Typography>
              <Typography variant="body1">{data.ticker_profile.recommendation}</Typography>
              {durationUnit === 'hours' && (
                <Typography variant="body2" sx={{ mt: 2, fontStyle: 'italic' }}>
                  🎯 For sniper entries: Use 4H to catch winner confirmations 2-6 hours before daily close.
                  Monitor every 4H bar for early escape signals.
                </Typography>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </Paper>
  );
};
