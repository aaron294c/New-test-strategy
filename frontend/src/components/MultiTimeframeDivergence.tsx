/**
 * Multi-Timeframe Divergence Analysis Component
 *
 * Visualizes divergence/convergence between daily and 4-hourly RSI-MA
 * to identify mean reversion opportunities.
 */

import React, { useState, useEffect } from 'react';
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

  const fetchAnalysis = async () => {
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
  };

  useEffect(() => {
    fetchAnalysis();
  }, [ticker]);

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

  // Prepare chart data for divergence over time
  const getDivergenceChartData = () => {
    if (!analysis?.divergence_events) return [];

    // Get last 100 events for visualization
    const recentEvents = analysis.divergence_events.slice(-100);

    return recentEvents.map((event: any) => ({
      date: event.date,
      divergence_pct: event.divergence_pct,
      daily_pct: event.daily_percentile,
      '4h_pct': event.hourly_4h_percentile,
      price: event.daily_price,
      type: event.divergence_type,
    }));
  };

  // Prepare scatter plot data: divergence vs forward returns
  const getDivergenceReturnsData = () => {
    if (!analysis?.divergence_events) return [];

    return analysis.divergence_events.map((event: any) => ({
      divergence_pct: event.divergence_pct,
      return_d7: event.forward_returns?.D7 || 0,
      return_d14: event.forward_returns?.D14 || 0,
      type: event.divergence_type,
      strength: event.signal_strength,
    }));
  };

  // Prepare bar chart data for stats by divergence type
  const getStatsBarData = () => {
    if (!analysis?.divergence_stats) return [];

    const stats = analysis.divergence_stats;
    const data = [];

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
  };

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
          <LineChart data={getDivergenceChartData()}>
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
          <BarChart data={getStatsBarData()}>
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
              name="Bearish Divergence"
              data={getDivergenceReturnsData().filter((d: any) => d.type === 'bearish_divergence')}
              fill="#ff6b6b"
            />
            <Scatter
              name="Bullish Divergence"
              data={getDivergenceReturnsData().filter((d: any) => d.type === 'bullish_divergence')}
              fill="#51cf66"
            />
          </ScatterChart>
        </ResponsiveContainer>

        <Alert severity="info" sx={{ mt: 2 }}>
          <strong>Mean Reversion Pattern:</strong> Bearish divergence (positive X) tends to produce negative
          returns (below Y=0). Bullish divergence (negative X) tends to produce positive returns (above Y=0).
        </Alert>
      </TabPanel>

      {/* Tab 4: Optimal Thresholds */}
      <TabPanel value={tabValue} index={4}>
        <Typography variant="h6" gutterBottom>
          Optimal Divergence Thresholds
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          These thresholds maximize risk-adjusted returns (Sharpe ratio) for each divergence type
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card sx={{ bgcolor: 'error.light' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Bearish Divergence
                </Typography>
                <Typography variant="h4" sx={{ my: 2 }}>
                  {analysis.optimal_thresholds.bearish_divergence_threshold}%
                </Typography>
                <Typography variant="body2">
                  Sharpe Ratio: {analysis.optimal_thresholds.bearish_sharpe?.toFixed(2) || 'N/A'}
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Typography variant="body2">
                  <strong>Signal:</strong> When Daily is {analysis.optimal_thresholds.bearish_divergence_threshold}%+
                  above 4H, consider taking profits or shorting (mean reversion expected)
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card sx={{ bgcolor: 'success.light' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Bullish Divergence
                </Typography>
                <Typography variant="h4" sx={{ my: 2 }}>
                  {analysis.optimal_thresholds.bullish_divergence_threshold}%
                </Typography>
                <Typography variant="body2">
                  Sharpe Ratio: {analysis.optimal_thresholds.bullish_sharpe?.toFixed(2) || 'N/A'}
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Typography variant="body2">
                  <strong>Signal:</strong> When 4H is {analysis.optimal_thresholds.bullish_divergence_threshold}%+
                  above Daily, consider buying/re-entering (pullback complete, bounce expected)
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
            <li>Monitor current divergence % in real-time</li>
            <li>When divergence exceeds optimal threshold, mean reversion is likely</li>
            <li>Bearish divergence → Take profits or short</li>
            <li>Bullish divergence → Buy the pullback or re-enter</li>
            <li>Convergence (low divergence) → Trend likely to continue</li>
          </ul>
        </Alert>
      </TabPanel>
    </Paper>
  );
};

export default MultiTimeframeDivergence;
