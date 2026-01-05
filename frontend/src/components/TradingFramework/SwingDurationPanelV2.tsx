import React, { useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import {
  Alert,
  Box,
  Button,
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
  TableSortLabel,
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
type Timeframe = 'daily' | 'intraday';

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
  const [timeframe, setTimeframe] = useState<Timeframe>('daily');
  const [data, setData] = useState<DurationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [summaryCache, setSummaryCache] = useState<Record<Timeframe, Record<string, DurationResponse>>>({
    daily: {},
    intraday: {},
  });
  const [summaryErrors, setSummaryErrors] = useState<Record<Timeframe, Record<string, string>>>({
    daily: {},
    intraday: {},
  });
  const [summaryLoadingState, setSummaryLoadingState] = useState<{
    timeframe: Timeframe;
    loaded: number;
    total: number;
  } | null>(null);

  type SummarySortKey =
    | 'ticker'
    | 'sample_size'
    | 'median_time_to_profit'
    | 'median_escape'
    | 'escape_rate'
    | 'data_source';

  const [summarySort, setSummarySort] = useState<{
    key: SummarySortKey;
    direction: 'asc' | 'desc';
  }>({ key: 'ticker', direction: 'asc' });

  const summaryRunIdRef = useRef(0);

  useEffect(() => {
    return () => {
      summaryRunIdRef.current += 1;
    };
  }, []);

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

  const handleSummarySortChange = (key: SummarySortKey) => {
    setSummarySort((current) => {
      if (current.key !== key) return { key, direction: 'asc' };
      return { key, direction: current.direction === 'asc' ? 'desc' : 'asc' };
    });
  };

  const loadSummary = async () => {
    if (summaryLoadingState) return;

    const timeframeToLoad = timeframe;
    const runId = summaryRunIdRef.current + 1;
    summaryRunIdRef.current = runId;

    setSummaryLoadingState({ timeframe: timeframeToLoad, loaded: 0, total: tickers.length });
    setSummaryCache((prev) => ({ ...prev, [timeframeToLoad]: {} }));
    setSummaryErrors((prev) => ({ ...prev, [timeframeToLoad]: {} }));

    for (let index = 0; index < tickers.length; index += 1) {
      const symbol = tickers[index];
      try {
        const response = await axios.get(`${API_BASE_URL}/api/swing-duration/${symbol}`, {
          params: { threshold, use_sample_data: false, timeframe: timeframeToLoad },
        });

        if (summaryRunIdRef.current !== runId) return;
        setSummaryCache((prev) => ({
          ...prev,
          [timeframeToLoad]: { ...prev[timeframeToLoad], [symbol]: response.data },
        }));
      } catch (err: any) {
        if (summaryRunIdRef.current !== runId) return;
        const message =
          err?.response?.data?.detail || err?.message || 'Failed to load duration analysis';
        setSummaryErrors((prev) => ({
          ...prev,
          [timeframeToLoad]: { ...prev[timeframeToLoad], [symbol]: message },
        }));
      } finally {
        if (summaryRunIdRef.current !== runId) return;
        setSummaryLoadingState((prev) =>
          prev
            ? { ...prev, loaded: Math.min(index + 1, prev.total) }
            : { timeframe: timeframeToLoad, loaded: index + 1, total: tickers.length }
        );
      }
    }

    if (summaryRunIdRef.current !== runId) return;
    setSummaryLoadingState(null);
  };

  const currentSummaryCache = summaryCache[timeframe];
  const currentSummaryErrors = summaryErrors[timeframe];
  const hasAnySummaryData =
    Object.keys(currentSummaryCache).length > 0 || Object.keys(currentSummaryErrors).length > 0;

  type SummaryRow = {
    ticker: string;
    data?: DurationResponse;
    error?: string;
    unit?: DurationUnit;
    sampleSize: number | null;
    medianTimeToProfit: number | null;
    medianTimeToProfitDays: number | null;
    medianEscape: number | null;
    medianEscapeDays: number | null;
    escapeRate: number | null;
    dataSource: string | null;
  };

  const summaryRows: SummaryRow[] = useMemo(() => {
    const rows: SummaryRow[] = tickers.map((symbol) => {
      const cached = currentSummaryCache[symbol];
      const rowError = currentSummaryErrors[symbol];
      if (!cached) {
        return {
          ticker: symbol,
          error: rowError,
          sampleSize: null,
          medianTimeToProfit: null,
          medianTimeToProfitDays: null,
          medianEscape: null,
          medianEscapeDays: null,
          escapeRate: null,
          dataSource: null,
        };
      }

      const unit = resolveDurationUnit(cached);
      const w5 = cached.winners.threshold_5pct;
      const medianTimeToProfit = pickMedianTimeToProfit(w5, unit);
      const medianEscape = pickMedianEscapeFromProfile(cached.ticker_profile, unit);

      return {
        ticker: symbol,
        data: cached,
        error: rowError,
        unit,
        sampleSize: cached.sample_size ?? null,
        medianTimeToProfit,
        medianTimeToProfitDays: convertDurationToDays(medianTimeToProfit, unit),
        medianEscape,
        medianEscapeDays: convertDurationToDays(medianEscape, unit),
        escapeRate: w5.escape_rate ?? null,
        dataSource: cached.data_source ?? null,
      };
    });

    const compareNullableNumbers = (a: number | null, b: number | null) => {
      if (a === null && b === null) return 0;
      if (a === null) return 1;
      if (b === null) return -1;
      return a - b;
    };

    const compareNullableStrings = (a: string | null, b: string | null) => {
      if (a === null && b === null) return 0;
      if (a === null) return 1;
      if (b === null) return -1;
      return a.localeCompare(b);
    };

    const comparator = (a: SummaryRow, b: SummaryRow) => {
      switch (summarySort.key) {
        case 'ticker':
          return a.ticker.localeCompare(b.ticker);
        case 'sample_size':
          return compareNullableNumbers(a.sampleSize, b.sampleSize);
        case 'median_time_to_profit':
          return compareNullableNumbers(a.medianTimeToProfitDays, b.medianTimeToProfitDays);
        case 'median_escape':
          return compareNullableNumbers(a.medianEscapeDays, b.medianEscapeDays);
        case 'escape_rate':
          return compareNullableNumbers(a.escapeRate, b.escapeRate);
        case 'data_source':
          return compareNullableStrings(a.dataSource, b.dataSource);
        default:
          return 0;
      }
    };

    const sorted = [...rows].sort((a, b) => {
      const delta = comparator(a, b);
      if (delta === 0) return a.ticker.localeCompare(b.ticker);
      return summarySort.direction === 'asc' ? delta : -delta;
    });

    return sorted;
  }, [tickers, currentSummaryCache, currentSummaryErrors, summarySort]);

  const isSummaryLoading = summaryLoadingState !== null;
  const isSummaryLoadingForCurrentTimeframe = summaryLoadingState?.timeframe === timeframe;

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
              onChange={(e) => setTimeframe(e.target.value as Timeframe)}
              sx={{ minWidth: 180 }}
            >
              <MenuItem value="daily">Daily (1D)</MenuItem>
              <MenuItem value="intraday">Intraday (4H bars)</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Box>

      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent sx={{ py: 2, '&:last-child': { pb: 2 } }}>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: 2,
              flexWrap: 'wrap',
            }}
          >
            <Box>
              <Typography variant="h6" fontWeight="bold">
                All Tickers Summary
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Scan duration metrics at the selected resolution, then click a ticker to drill in.
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
              <Button
                size="small"
                variant="outlined"
                onClick={loadSummary}
                disabled={isSummaryLoading || tickers.length === 0}
              >
                {hasAnySummaryData ? 'Reload Summary' : 'Load Summary'}
              </Button>
              {isSummaryLoadingForCurrentTimeframe && <CircularProgress size={18} />}
              {isSummaryLoadingForCurrentTimeframe && summaryLoadingState && (
                <Typography variant="body2" color="text.secondary">
                  {summaryLoadingState.loaded}/{summaryLoadingState.total}
                </Typography>
              )}
            </Box>
          </Box>

          {!hasAnySummaryData && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Click “Load Summary” to fetch stats for all tickers without changing the detailed view.
            </Typography>
          )}

          {hasAnySummaryData && (
            <TableContainer component={Paper} variant="outlined" sx={{ mt: 2 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sortDirection={summarySort.key === 'ticker' ? summarySort.direction : false}>
                      <TableSortLabel
                        active={summarySort.key === 'ticker'}
                        direction={summarySort.key === 'ticker' ? summarySort.direction : 'asc'}
                        onClick={() => handleSummarySortChange('ticker')}
                      >
                        Ticker
                      </TableSortLabel>
                    </TableCell>

                    <TableCell
                      align="right"
                      sortDirection={summarySort.key === 'sample_size' ? summarySort.direction : false}
                    >
                      <TableSortLabel
                        active={summarySort.key === 'sample_size'}
                        direction={summarySort.key === 'sample_size' ? summarySort.direction : 'asc'}
                        onClick={() => handleSummarySortChange('sample_size')}
                      >
                        n
                      </TableSortLabel>
                    </TableCell>

                    <TableCell
                      align="right"
                      sortDirection={summarySort.key === 'median_time_to_profit' ? summarySort.direction : false}
                    >
                      <TableSortLabel
                        active={summarySort.key === 'median_time_to_profit'}
                        direction={summarySort.key === 'median_time_to_profit' ? summarySort.direction : 'asc'}
                        onClick={() => handleSummarySortChange('median_time_to_profit')}
                      >
                        Median time-to-profit (W @5%)
                      </TableSortLabel>
                    </TableCell>

                    <TableCell
                      align="right"
                      sortDirection={summarySort.key === 'median_escape' ? summarySort.direction : false}
                    >
                      <TableSortLabel
                        active={summarySort.key === 'median_escape'}
                        direction={summarySort.key === 'median_escape' ? summarySort.direction : 'asc'}
                        onClick={() => handleSummarySortChange('median_escape')}
                      >
                        Median escape (W @5%)
                      </TableSortLabel>
                    </TableCell>

                    <TableCell
                      align="right"
                      sortDirection={summarySort.key === 'escape_rate' ? summarySort.direction : false}
                    >
                      <TableSortLabel
                        active={summarySort.key === 'escape_rate'}
                        direction={summarySort.key === 'escape_rate' ? summarySort.direction : 'asc'}
                        onClick={() => handleSummarySortChange('escape_rate')}
                      >
                        Escape rate
                      </TableSortLabel>
                    </TableCell>

                    <TableCell sortDirection={summarySort.key === 'data_source' ? summarySort.direction : false}>
                      <TableSortLabel
                        active={summarySort.key === 'data_source'}
                        direction={summarySort.key === 'data_source' ? summarySort.direction : 'asc'}
                        onClick={() => handleSummarySortChange('data_source')}
                      >
                        Data source
                      </TableSortLabel>
                    </TableCell>
                  </TableRow>
                </TableHead>

                <TableBody>
                  {summaryRows.map((row) => (
                    <TableRow
                      key={row.ticker}
                      hover
                      onClick={() => handleTickerChange(row.ticker)}
                      sx={{
                        cursor: 'pointer',
                        ...(row.ticker === ticker ? { backgroundColor: 'action.selected' } : null),
                      }}
                    >
                      <TableCell>
                        <Typography variant="body2" fontWeight={row.ticker === ticker ? 'bold' : 'normal'}>
                          {row.ticker}
                        </Typography>
                        {row.error && (
                          <Typography variant="caption" color="error" sx={{ display: 'block' }}>
                            {row.error}
                          </Typography>
                        )}
                      </TableCell>

                      <TableCell align="right">{row.sampleSize ?? '—'}</TableCell>
                      <TableCell align="right">
                        {row.unit ? formatDurationValue(row.medianTimeToProfit, row.unit) : '—'}
                      </TableCell>
                      <TableCell align="right">
                        {row.unit ? formatDurationValue(row.medianEscape, row.unit) : '—'}
                      </TableCell>
                      <TableCell align="right">{formatPercent(row.escapeRate, 0)}</TableCell>
                      <TableCell>
                        {row.dataSource === 'sample' && (
                          <Chip size="small" label="SAMPLE" color="warning" variant="outlined" />
                        )}
                        {row.dataSource && row.dataSource !== 'sample' && (
                          <Chip size="small" label={row.dataSource.toUpperCase()} color="success" variant="outlined" />
                        )}
                        {!row.dataSource && row.error && (
                          <Chip size="small" label="ERROR" color="error" variant="outlined" />
                        )}
                        {!row.dataSource && !row.error && (
                          <Chip size="small" label="NOT LOADED" variant="outlined" />
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

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

          {/* WARNING: Low Escape Rate Detection for Percentile-Non-Responsive Tickers */}
          {durationUnit === 'hours' &&
           data.winners.threshold_5pct.escape_rate !== null &&
           data.winners.threshold_5pct.escape_rate < 0.5 && (
            <Alert severity="warning" sx={{ mb: 3 }}>
              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                ⚠️ WARNING: Percentile-Non-Responsive Ticker at 4H Resolution
              </Typography>
              <Typography variant="body2">
                This ticker shows <strong>{formatPercent(data.winners.threshold_5pct.escape_rate)}</strong> escape rate,
                meaning <strong>{formatPercent(1 - (data.winners.threshold_5pct.escape_rate || 0))}</strong> of winners NEVER escape
                the &lt;5% percentile zone at 4H resolution within the tracking window.
              </Typography>
              <Typography variant="body2" sx={{ mt: 1, fontWeight: 'bold' }}>
                🎯 CRITICAL: The 4H percentile strategy does NOT work for this ticker!
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                <strong>Why:</strong> Percentile stays in low zone (&lt;5%) even when price recovers and shows positive returns.
                This causes the percentile-based exit signals to fail - you'd wait 12-24 days for an escape that never comes.
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                <strong>Recommendation:</strong> Use <strong>DAILY timeframe</strong> for percentile monitoring instead of 4H.
                At daily resolution, this ticker's percentile typically escapes within 1-2 days.
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                ❌ <strong>Do NOT use for this ticker:</strong> 4H sniper entry timing, 4H bailout timers, 4H percentile escape signals<br />
                ✅ <strong>Use instead:</strong> Daily percentile monitoring + price targets (e.g., +3%, +5%) + time stops (e.g., hold 2 days max)
              </Typography>
            </Alert>
          )}

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

          {/* Conditional warning for non-responsive tickers */}
          {durationUnit === 'hours' &&
           data.winners.threshold_5pct.escape_rate !== null &&
           data.winners.threshold_5pct.escape_rate < 0.5 && (
            <Alert severity="error" sx={{ mb: 2 }}>
              <Typography variant="body2" fontWeight="bold">
                ⚠️ WARNING: 4H Bailout timers do NOT apply to this ticker!
              </Typography>
              <Typography variant="body2" sx={{ mt: 0.5 }}>
                For percentile-non-responsive tickers, the bailout timers shown below would EXIT WINNERS prematurely.
                Use Daily timeframe data instead for this ticker's bailout guidance.
              </Typography>
            </Alert>
          )}

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

          {/* NEW: Sniper Entry Analysis (4H vs Daily) - Only show for percentile-responsive tickers */}
          {durationUnit === 'hours' &&
           data.winners.threshold_5pct.escape_rate !== null &&
           data.winners.threshold_5pct.escape_rate >= 0.5 && (
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
