/**
 * Multi-Timeframe Divergence Analysis Component
 *
 * Visualizes divergence/convergence between daily and 4-hourly RSI-MA
 * to identify mean reversion opportunities.
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Paper,
  Typography,
  Box,
  Button,
  CircularProgress,
  Alert,
  Grid,
  Card,
  CardContent,
  Chip,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
} from '@mui/material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import RefreshIcon from '@mui/icons-material/Refresh';
import TimelineIcon from '@mui/icons-material/Timeline';
import { PercentileThresholdAnalysis } from './PercentileThresholdAnalysis';

interface MultiTimeframeDivergenceProps {
  ticker: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const MultiTimeframeDivergence: React.FC<MultiTimeframeDivergenceProps> = ({ ticker }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [tabValue, setTabValue] = useState(0);

  const fetchAnalysis = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/multi-timeframe/${ticker}`);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API Error: ${response.status}\n${errorText}`);
      }

      const result = await response.json();
      setAnalysis(result.analysis);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch analysis');
    } finally {
      setLoading(false);
    }
  }, [ticker]);

  useEffect(() => {
    fetchAnalysis();
  }, [fetchAnalysis]);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const getSignalColor = (signal: string) => {
    if (signal.includes('bearish')) return 'error';
    if (signal.includes('bullish')) return 'success';
    return 'default';
  };

  const getActionColor = (action: string) => {
    if (action.includes('profit') || action.includes('short')) return 'warning';
    if (action.includes('buy') || action.includes('reenter')) return 'success';
    return 'info';
  };

  const formatPValue = (value: any) => {
    if (value === null || value === undefined || Number.isNaN(value)) return 'N/A';
    const n = Number(value);
    if (!Number.isFinite(n)) return 'N/A';
    if (n < 0.001) return '<0.001';
    return n.toFixed(3);
  };

  const getConfidence = (
    horizon: 'D1' | 'D3' | 'D7',
    row: any
  ): { level: 'High' | 'Medium' | 'Low'; reasons: string[] } => {
    const reasons: string[] = [];

    const p = typeof row?.p_value_mwu === 'number' ? row.p_value_mwu : null;
    const nHigh = typeof row?.n_high === 'number' ? row.n_high : 0;
    const nLow = typeof row?.n_low === 'number' ? row.n_low : 0;
    const nMin = Math.min(nHigh, nLow);

    const deltaMean = typeof row?.delta_mean === 'number' ? row.delta_mean : null;
    const deltaMedian = typeof row?.delta_median === 'number' ? row.delta_median : null;
    const deltaWin = typeof row?.delta_win_rate === 'number' ? row.delta_win_rate : null;

    // 1) p-value tier (evidence strength)
    let pScore = 0;
    if (p !== null) {
      if (p <= 0.05) {
        pScore = 2;
        reasons.push('p≤0.05');
      } else if (p <= 0.10) {
        pScore = 1;
        reasons.push('p≤0.10');
      } else if (p <= 0.15) {
        pScore = 0.5;
        reasons.push('p≤0.15');
      } else {
        reasons.push('p>0.15');
      }
    } else {
      reasons.push('p=N/A');
    }

    // 2) sample size (stability)
    let nScore = 0;
    if (nMin >= 50) {
      nScore = 2;
      reasons.push('n≥50');
    } else if (nMin >= 30) {
      nScore = 1;
      reasons.push('n≥30');
    } else if (nMin >= 20) {
      nScore = 0.5;
      reasons.push('n≥20');
    } else {
      reasons.push('n<20');
    }

    // 3) effect size (practical, not just statistically significant)
    // Thresholds tuned to your execution: D1/D3 matter more than D7.
    const meanThreshold = horizon === 'D1' ? 0.20 : horizon === 'D3' ? 0.40 : 0.80;
    const winThreshold = 5; // % points

    const meanEffect = deltaMean !== null && Math.abs(deltaMean) >= meanThreshold;
    const medianEffect = deltaMedian !== null && Math.abs(deltaMedian) >= meanThreshold;
    const winEffect = deltaWin !== null && Math.abs(deltaWin) >= winThreshold;

    let eScore = 0;
    if (meanEffect || medianEffect || winEffect) {
      eScore = 1.5;
      reasons.push(
        `effect≥${meanThreshold.toFixed(2)}% or win≥${winThreshold}pp`
      );
    } else {
      reasons.push('small effect');
    }

    // 4) horizon alignment (you exit earlier than D7)
    const hScore = horizon === 'D7' ? 0 : 1;
    if (horizon !== 'D7') reasons.push('matches early-exit horizon');

    const total = pScore + nScore + eScore + hScore;
    if (total >= 5) return { level: 'High', reasons };
    if (total >= 3) return { level: 'Medium', reasons };
    return { level: 'Low', reasons };
  };

  const divergenceEvents = analysis?.divergence_events || [];

  const divergenceChartData = useMemo(() => {
    if (!divergenceEvents.length) return [];
    const recentEvents = divergenceEvents.slice(-100);
    return recentEvents.map((event: any) => ({
      date: event.date,
      divergence_pct: event.divergence_pct,
      daily_pct: event.daily_percentile,
      '4h_pct': event.hourly_4h_percentile,
      price: event.daily_price,
      type: event.divergence_type,
    }));
  }, [divergenceEvents]);

  const divergenceReturnsByType = useMemo(() => {
    const grouped: Record<string, any[]> = {
      daily_overextended: [],
      '4h_overextended': [],
      bullish_convergence: [],
      bearish_convergence: [],
    };

    for (const event of divergenceEvents) {
      const point = {
        divergence_pct: event.divergence_pct,
        return_d7: event.forward_returns?.D7 || 0,
        return_d14: event.forward_returns?.D14 || 0,
        type: event.divergence_type,
        strength: event.signal_strength,
      };
      if (grouped[point.type]) grouped[point.type].push(point);
    }

    return grouped;
  }, [divergenceEvents]);

  const statsBarData = useMemo(() => {
    if (!analysis?.divergence_stats) return [];

    const stats = analysis.divergence_stats;
    const data: any[] = [];

    // New categories
    const categories = [
      { key: '4h_overextended', label: '4H Overextended (Take Profit)' },
      { key: 'bullish_convergence', label: 'Bullish Convergence (Re-entry)' },
      { key: 'daily_overextended', label: 'Daily Overextended (Reversal)' },
      { key: 'bearish_convergence', label: 'Bearish Convergence (Exit)' },
    ];

    for (const cat of categories) {
      if (stats[cat.key]) {
        data.push({
          type: cat.label,
          count: stats[cat.key].count,
          avg_return_D7: stats[cat.key].avg_return_D7 || 0,
          avg_return_D3: stats[cat.key].avg_return_D3 || 0,
          avg_return_D1: stats[cat.key].avg_return_D1 || 0,
          win_rate_D7: stats[cat.key].win_rate_D7 || 0,
          mean_reversion_D7: stats[cat.key].mean_reversion_rate_D7 || 0,
        });
      }
    }

    // Fallback to old categories if new ones don't exist
    if (data.length === 0) {
      if (stats.bearish_divergence) {
        data.push({
          type: 'Bearish Divergence',
          count: stats.bearish_divergence.count,
          avg_return_D7: stats.bearish_divergence.avg_return_D7 || 0,
          avg_return_D3: stats.bearish_divergence.avg_return_D3 || 0,
          avg_return_D1: stats.bearish_divergence.avg_return_D1 || 0,
          win_rate_D7: stats.bearish_divergence.win_rate_D7 || 0,
          mean_reversion_D7: stats.bearish_divergence.mean_reversion_rate_D7 || 0,
        });
      }

      if (stats.bullish_divergence) {
        data.push({
          type: 'Bullish Divergence',
          count: stats.bullish_divergence.count,
          avg_return_D7: stats.bullish_divergence.avg_return_D7 || 0,
          avg_return_D3: stats.bullish_divergence.avg_return_D3 || 0,
          avg_return_D1: stats.bullish_divergence.avg_return_D1 || 0,
          win_rate_D7: stats.bullish_divergence.win_rate_D7 || 0,
          mean_reversion_D7: stats.bullish_divergence.mean_reversion_rate_D7 || 0,
        });
      }
    }

    return data;
  }, [analysis?.divergence_stats]);

  if (loading && !analysis) {
    return (
      <Paper elevation={3} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
          <CircularProgress />
          <Typography variant="body1" sx={{ ml: 2 }}>
            Analyzing multi-timeframe divergence patterns...
          </Typography>
        </Box>
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper elevation={3} sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
        <Button onClick={fetchAnalysis} sx={{ mt: 2 }}>
          Retry
        </Button>
      </Paper>
    );
  }

  if (!analysis) {
    return null;
  }

  const rec = analysis.current_recommendation;

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <TimelineIcon sx={{ fontSize: 32, color: 'primary.main' }} />
          <Typography variant="h5" component="h2">
            Multi-Timeframe Divergence - {ticker}
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchAnalysis}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Analyze divergence between Daily and 4-Hourly RSI-MA to identify mean reversion opportunities
      </Typography>

      {/* Current Signal Card */}
      <Card sx={{ mb: 3, bgcolor: 'background.default' }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Current Divergence Signal
          </Typography>

          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Daily Percentile: <strong>{analysis.current_daily_percentile?.toFixed(1) ?? 'N/A'}%</strong>
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  4-Hour Percentile: <strong>{analysis.current_4h_percentile?.toFixed(1) ?? 'N/A'}%</strong>
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Divergence:{' '}
                  <strong
                    style={{
                      color:
                        analysis.current_divergence_pct && Math.abs(analysis.current_divergence_pct) > 25
                          ? analysis.current_divergence_pct > 0
                            ? 'red'
                            : 'green'
                          : 'gray',
                    }}
                  >
                    {analysis.current_divergence_pct !== null && analysis.current_divergence_pct !== undefined
                      ? `${analysis.current_divergence_pct > 0 ? '+' : ''}${analysis.current_divergence_pct.toFixed(1)}%`
                      : 'N/A'}
                  </strong>
                </Typography>
              </Box>

              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <Chip
                  label={rec.signal.replace(/_/g, ' ').toUpperCase()}
                  color={getSignalColor(rec.signal)}
                  size="medium"
                />
                <Chip
                  label={rec.action.replace(/_/g, ' ').toUpperCase()}
                  color={getActionColor(rec.action)}
                  size="medium"
                  variant="outlined"
                />
              </Box>
            </Grid>

            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" gutterBottom>
                Reasoning:
              </Typography>
              {rec.reasoning.map((reason: string, idx: number) => (
                <Typography key={idx} variant="body2" sx={{ mb: 0.5 }}>
                  • {reason}
                </Typography>
              ))}
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Tabs for different views */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="📊 Percentile Thresholds" />
          <Tab label="Divergence Timeline" />
          <Tab label="Performance Stats" />
          <Tab label="Scatter Analysis" />
          <Tab label="Optimal Thresholds" />
        </Tabs>
      </Box>

      {/* Tab 0: Percentile Thresholds */}
      <TabPanel value={tabValue} index={0}>
        <PercentileThresholdAnalysis ticker={ticker} />
      </TabPanel>

      {/* Tab 1: Divergence Timeline */}
      <TabPanel value={tabValue} index={1}>
        <Typography variant="h6" gutterBottom>
          Historical Divergence Patterns (Last 100 Events)
        </Typography>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={divergenceChartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tickFormatter={(value) => {
                const date = new Date(value);
                return `${date.getMonth() + 1}/${date.getDate()}`;
              }}
            />
            <YAxis />
            <Tooltip
              labelFormatter={(value) => `Date: ${value}`}
              formatter={(value: number) => value.toFixed(2)}
            />
            <Legend />
            <ReferenceLine y={0} stroke="gray" strokeDasharray="3 3" />
            <ReferenceLine y={25} stroke="red" strokeDasharray="3 3" label="Bearish Threshold" />
            <ReferenceLine y={-25} stroke="green" strokeDasharray="3 3" label="Bullish Threshold" />
            <Line
              type="monotone"
              dataKey="divergence_pct"
              stroke="#8884d8"
              name="Divergence %"
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>

        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Positive = Daily above 4H (bearish divergence), Negative = 4H above Daily (bullish divergence)
        </Typography>
      </TabPanel>

      {/* Tab 2: Performance Stats */}
      <TabPanel value={tabValue} index={2}>
        <Typography variant="h6" gutterBottom>
          Performance by Divergence Type
        </Typography>

        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={statsBarData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="type" />
            <YAxis />
            <Tooltip formatter={(value: number) => value.toFixed(2)} />
            <Legend />
            <Bar dataKey="avg_return_D7" fill="#8884d8" name="Avg Return D7 (%)" />
            <Bar dataKey="mean_reversion_D7" fill="#82ca9d" name="Mean Reversion Rate D7 (%)" />
          </BarChart>
        </ResponsiveContainer>

        <Divider sx={{ my: 3 }} />

        <Typography variant="h6" gutterBottom>
          Detailed Statistics
        </Typography>

        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Type</TableCell>
                <TableCell align="right">Count</TableCell>
                <TableCell align="right">Avg D1</TableCell>
                <TableCell align="right">Avg D3</TableCell>
                <TableCell align="right">Avg D7</TableCell>
                <TableCell align="right">Win Rate D7</TableCell>
                <TableCell align="right">MR Rate D7</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {[
                { key: '4h_overextended', label: '4H Overextended (Take Profit)' },
                { key: 'bullish_convergence', label: 'Bullish Convergence (Re-entry)' },
                { key: 'daily_overextended', label: 'Daily Overextended (Reversal)' },
                { key: 'bearish_convergence', label: 'Bearish Convergence (Exit)' },
              ].map((cat) => {
                const statData = analysis.divergence_stats[cat.key];
                if (!statData) return null;
                return (
                  <TableRow key={cat.key}>
                    <TableCell><strong>{cat.label}</strong></TableCell>
                    <TableCell align="right">{statData.count}</TableCell>
                    <TableCell align="right" style={{ color: (statData.avg_return_D1 || 0) > 0 ? 'green' : 'red' }}>
                      {statData.avg_return_D1?.toFixed(2) || 'N/A'}%
                    </TableCell>
                    <TableCell align="right" style={{ color: (statData.avg_return_D3 || 0) > 0 ? 'green' : 'red' }}>
                      {statData.avg_return_D3?.toFixed(2) || 'N/A'}%
                    </TableCell>
                    <TableCell align="right" style={{ color: (statData.avg_return_D7 || 0) > 0 ? 'green' : 'red' }}>
                      {statData.avg_return_D7?.toFixed(2) || 'N/A'}%
                    </TableCell>
                    <TableCell align="right">
                      {statData.win_rate_D7?.toFixed(1) || 'N/A'}%
                    </TableCell>
                    <TableCell align="right">
                      {statData.mean_reversion_rate_D7?.toFixed(1) || 'N/A'}%
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      {/* Tab 3: Scatter Analysis */}
      <TabPanel value={tabValue} index={3}>
        <Typography variant="h6" gutterBottom>
          Divergence vs Forward Returns (D7)
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Each point represents a divergence event. X-axis = divergence %, Y-axis = 7-day forward return
        </Typography>

        <ResponsiveContainer width="100%" height={400}>
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              type="number"
              dataKey="divergence_pct"
              name="Divergence %"
              label={{ value: 'Divergence %', position: 'insideBottom', offset: -5 }}
            />
            <YAxis
              type="number"
              dataKey="return_d7"
              name="D7 Return %"
              label={{ value: '7-Day Return %', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip cursor={{ strokeDasharray: '3 3' }} />
            <Legend />
            <ReferenceLine x={0} stroke="gray" />
            <ReferenceLine y={0} stroke="gray" />
            <Scatter
              name="Daily Overextended (reduce/hedge)"
              data={divergenceReturnsByType.daily_overextended}
              fill="#ff6b6b"
            />
            <Scatter
              name="4H Overextended (take profits)"
              data={divergenceReturnsByType['4h_overextended']}
              fill="#ffd43b"
            />
            <Scatter
              name="Bullish Convergence (buy/add)"
              data={divergenceReturnsByType.bullish_convergence}
              fill="#51cf66"
            />
            <Scatter
              name="Bearish Convergence (exit/avoid longs)"
              data={divergenceReturnsByType.bearish_convergence}
              fill="#845ef7"
            />
          </ScatterChart>
        </ResponsiveContainer>

        <Alert severity="info" sx={{ mt: 2 }}>
          <strong>Interpretation:</strong> Large absolute divergence is a “dislocation” (mean reversion risk),
          while convergence categories are the higher-confidence alignment signals.
        </Alert>
      </TabPanel>

      {/* Tab 4: Optimal Thresholds */}
      <TabPanel value={tabValue} index={4}>
        <Typography variant="h6" gutterBottom>
          Dislocation Thresholds (Per-Ticker)
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          These thresholds are derived from the ticker’s historical divergence distribution (percentile gaps).
        </Typography>

        {analysis.optimal_thresholds?.dislocation_sample && (
          <Alert severity="info" sx={{ mb: 3 }}>
            <strong>Sample used for P85/P95:</strong>{' '}
            {analysis.optimal_thresholds.dislocation_sample.n_days ?? 'N/A'} daily observations
            {analysis.optimal_thresholds.dislocation_sample.start_date
              ? ` (${analysis.optimal_thresholds.dislocation_sample.start_date} → ${analysis.optimal_thresholds.dislocation_sample.end_date})`
              : ''}{' '}
            • Lookback request: {analysis.optimal_thresholds.dislocation_sample.lookback_days_hourly ?? 'N/A'} days of 1H history
            • Percentile windows: Daily {analysis.optimal_thresholds.dislocation_sample.percentile_windows?.daily ?? 'N/A'} / 4H {analysis.optimal_thresholds.dislocation_sample.percentile_windows?.four_h ?? 'N/A'}
          </Alert>
        )}

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card sx={{ bgcolor: 'warning.light' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Significant Dislocation (P85)
                </Typography>
                <Typography variant="h4" sx={{ my: 2 }}>
                  {analysis.optimal_thresholds.dislocation_abs_p85
                    ? `${analysis.optimal_thresholds.dislocation_abs_p85.toFixed(1)}%`
                    : 'N/A'}
                </Typography>
                <Typography variant="body2">
                  <strong>Direction guides:</strong>{' '}
                  +{analysis.optimal_thresholds.dislocation_positive_p85
                    ? analysis.optimal_thresholds.dislocation_positive_p85.toFixed(1)
                    : 'N/A'}
                  % (Daily &gt; 4H), −{analysis.optimal_thresholds.dislocation_negative_p85
                    ? analysis.optimal_thresholds.dislocation_negative_p85.toFixed(1)
                    : 'N/A'}
                  % (4H &gt; Daily)
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Typography variant="body2">
                  <strong>Use:</strong> when |Daily − 4H| exceeds P85, treat it as a real dislocation
                  (mean reversion risk) and avoid chasing.
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card sx={{ bgcolor: 'error.light' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Extreme Dislocation (P95)
                </Typography>
                <Typography variant="h4" sx={{ my: 2 }}>
                  {analysis.optimal_thresholds.dislocation_abs_p95
                    ? `${analysis.optimal_thresholds.dislocation_abs_p95.toFixed(1)}%`
                    : 'N/A'}
                </Typography>
                <Typography variant="body2">
                  <strong>Legacy (directional) thresholds:</strong>{' '}
                  +{analysis.optimal_thresholds.bearish_divergence_threshold}% / −{analysis.optimal_thresholds.bullish_divergence_threshold}%
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Typography variant="body2">
                  <strong>Use:</strong> P95 dislocations are often best for profit-taking (if long) or
                  patience (wait for convergence) rather than adding risk.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Alert severity="success" sx={{ mt: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            How to Use These Thresholds:
          </Typography>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            <li>Use P85 as your “significant dislocation” line (risk of mean reversion increases)</li>
            <li>Use P95 as an “extreme” line (often take profits / wait for re-alignment)</li>
            <li>Combine with category: 4H overextended → take profits; bullish convergence → buy/add</li>
            <li>Because you often exit before 7D, treat large dislocations as an early-exit trigger</li>
          </ul>
        </Alert>

        {/* Stats: compare outcomes above/below dislocation thresholds */}
        {analysis.optimal_thresholds?.dislocation_stats && (
          <Box sx={{ mt: 4 }}>
            <Typography variant="h6" gutterBottom>
              Outcome Comparison (High Gap vs Low Gap)
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Compares forward returns for days where the divergence gap is above the threshold vs below it.
              P-values are Mann–Whitney U (non-parametric) when sample sizes permit.
            </Typography>

            <Alert severity="info" sx={{ mb: 2 }}>
              <strong>How to read “Confidence”:</strong> this is a trading-oriented label (risk management / filtering),
              not a claim of certainty. We score confidence using (1) p-value tier (≤0.05 / ≤0.10 / ≤0.15),
              (2) minimum sample size in both groups, (3) effect size (Δ mean/median and/or win-rate shift),
              and (4) whether the horizon is aligned to your early-exit style (D1/D3 weighted higher than D7).
            </Alert>

            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Threshold</TableCell>
                    <TableCell>Horizon</TableCell>
                    <TableCell>Confidence</TableCell>
                    <TableCell align="right">N (High)</TableCell>
                    <TableCell align="right">N (Low)</TableCell>
                    <TableCell align="right">Mean High</TableCell>
                    <TableCell align="right">Mean Low</TableCell>
                    <TableCell align="right">Δ Mean</TableCell>
                    <TableCell align="right">Δ Median</TableCell>
                    <TableCell align="right">Win High</TableCell>
                    <TableCell align="right">Win Low</TableCell>
                    <TableCell align="right">Δ Win</TableCell>
                    <TableCell align="right">p</TableCell>
                    <TableCell>Why</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(['abs_p85', 'abs_p95'] as const)
                    .filter((k) => analysis.optimal_thresholds.dislocation_stats?.[k])
                    .flatMap((k) => {
                      const block = analysis.optimal_thresholds.dislocation_stats[k];
                      const label = k === 'abs_p85'
                        ? `|gap| ≥ P85 (${block.threshold?.toFixed?.(1) ?? 'N/A'}%)`
                        : `|gap| ≥ P95 (${block.threshold?.toFixed?.(1) ?? 'N/A'}%)`;
                      const horizons = block.horizons || {};
                      return (['D1', 'D3', 'D7'] as const).map((h) => {
                        const row = horizons[h];
                        if (!row) return null;
                        const confidence = getConfidence(h, row);
                        const chipColor = confidence.level === 'High'
                          ? 'success'
                          : confidence.level === 'Medium'
                            ? 'warning'
                            : 'default';
                        return (
                          <TableRow key={`${k}-${h}`}>
                            <TableCell>{label}</TableCell>
                            <TableCell>{h}</TableCell>
                            <TableCell>
                              <Chip
                                size="small"
                                label={confidence.level}
                                color={chipColor as any}
                                variant="outlined"
                              />
                            </TableCell>
                            <TableCell align="right">{row.n_high ?? '—'}</TableCell>
                            <TableCell align="right">{row.n_low ?? '—'}</TableCell>
                            <TableCell align="right">{row.mean_high?.toFixed?.(2) ?? '—'}%</TableCell>
                            <TableCell align="right">{row.mean_low?.toFixed?.(2) ?? '—'}%</TableCell>
                            <TableCell align="right">{row.delta_mean?.toFixed?.(2) ?? '—'}%</TableCell>
                            <TableCell align="right">{row.delta_median?.toFixed?.(2) ?? '—'}%</TableCell>
                            <TableCell align="right">{row.win_rate_high?.toFixed?.(1) ?? '—'}%</TableCell>
                            <TableCell align="right">{row.win_rate_low?.toFixed?.(1) ?? '—'}%</TableCell>
                            <TableCell align="right">{row.delta_win_rate?.toFixed?.(1) ?? '—'}pp</TableCell>
                            <TableCell align="right">{formatPValue(row.p_value_mwu)}</TableCell>
                            <TableCell>{confidence.reasons.join(', ')}</TableCell>
                          </TableRow>
                        );
                      });
                    })
                    .filter(Boolean)}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}
      </TabPanel>
    </Paper>
  );
};

export default MultiTimeframeDivergence;
