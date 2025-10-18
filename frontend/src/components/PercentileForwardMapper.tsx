/**
 * Percentile Forward Mapper Component
 *
 * Visualizes prospective extrapolation from RSI-MA percentiles to expected forward returns.
 * Displays:
 * - Current percentile & predicted returns (3d, 7d, 14d, 21d)
 * - Empirical bin mapping table
 * - Transition matrix heatmaps
 * - Model comparison (Empirical, Markov, Regression, Kernel, Ensemble)
 * - Backtest accuracy metrics
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  Chip,
} from '@mui/material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  ReferenceLine,
} from 'recharts';
import RefreshIcon from '@mui/icons-material/Refresh';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import ShowChartIcon from '@mui/icons-material/ShowChart';

interface PercentileForwardMapperProps {
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
      id={`forward-tabpanel-${index}`}
      aria-labelledby={`forward-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const PercentileForwardMapper: React.FC<PercentileForwardMapperProps> = ({ ticker }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [tabValue, setTabValue] = useState(0);

  const fetchAnalysis = async () => {
    setLoading(true);
    setError(null);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/percentile-forward/${ticker}`);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API Error: ${response.status}\n${errorText}`);
      }

      const result = await response.json();
      setAnalysis(result);
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

  // Helper to render transition matrix heatmap
  const renderTransitionMatrix = (tm: any) => {
    if (!tm || !tm.matrix) return null;

    const matrix = tm.matrix;
    const bins = tm.bins;

    return (
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell><strong>From \ To</strong></TableCell>
              {bins.map((bin: string) => (
                <TableCell key={bin} align="center"><strong>{bin}</strong></TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {matrix.map((row: number[], i: number) => (
              <TableRow key={bins[i]}>
                <TableCell><strong>{bins[i]}</strong></TableCell>
                {row.map((prob: number, j: number) => {
                  const colorIntensity = Math.floor(prob * 255);
                  const bgColor = `rgba(76, 175, 80, ${prob})`;
                  return (
                    <TableCell
                      key={j}
                      align="center"
                      sx={{
                        bgcolor: bgColor,
                        color: prob > 0.5 ? 'white' : 'black',
                        fontWeight: prob > 0.3 ? 'bold' : 'normal'
                      }}
                    >
                      {(prob * 100).toFixed(0)}%
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  // Helper to render bin stats chart (all horizons)
  const renderBinStatsChart = () => {
    if (!analysis?.bin_stats) return null;

    const chartData = Object.values(analysis.bin_stats).map((stats: any) => ({
      bin: stats.bin_label,
      mean_3d: stats.mean_return_3d,
      mean_7d: stats.mean_return_7d,
      mean_14d: stats.mean_return_14d,
      mean_21d: stats.mean_return_21d,
      count: stats.count
    }));

    return (
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="bin" />
          <YAxis label={{ value: 'Expected Return (%)', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Legend />
          <ReferenceLine y={0} stroke="#000" />
          <Bar dataKey="mean_3d" fill="#2196f3" name="3-day" />
          <Bar dataKey="mean_7d" fill="#ff9800" name="7-day" />
          <Bar dataKey="mean_14d" fill="#4caf50" name="14-day" />
          <Bar dataKey="mean_21d" fill="#9c27b0" name="21-day" />
        </BarChart>
      </ResponsiveContainer>
    );
  };

  // Helper to render 7-day bin stats chart
  const renderBinStatsChart7d = () => {
    if (!analysis?.bin_stats) return null;

    const chartData = Object.values(analysis.bin_stats).map((stats: any) => ({
      bin: stats.bin_label,
      mean_7d: stats.mean_return_7d,
      count: stats.count
    }));

    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="bin" />
          <YAxis label={{ value: 'Expected Return (%)', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Legend />
          <ReferenceLine y={0} stroke="#000" />
          <Bar dataKey="mean_7d" fill="#ff9800" name="7-day" />
        </BarChart>
      </ResponsiveContainer>
    );
  };

  // Helper to render 14-day bin stats chart
  const renderBinStatsChart14d = () => {
    if (!analysis?.bin_stats) return null;

    const chartData = Object.values(analysis.bin_stats).map((stats: any) => ({
      bin: stats.bin_label,
      mean_14d: stats.mean_return_14d,
      count: stats.count
    }));

    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="bin" />
          <YAxis label={{ value: 'Expected Return (%)', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Legend />
          <ReferenceLine y={0} stroke="#000" />
          <Bar dataKey="mean_14d" fill="#4caf50" name="14-day" />
        </BarChart>
      </ResponsiveContainer>
    );
  };

  // Helper to render 21-day bin stats chart
  const renderBinStatsChart21d = () => {
    if (!analysis?.bin_stats) return null;

    const chartData = Object.values(analysis.bin_stats).map((stats: any) => ({
      bin: stats.bin_label,
      mean_21d: stats.mean_return_21d,
      count: stats.count
    }));

    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="bin" />
          <YAxis label={{ value: 'Expected Return (%)', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Legend />
          <ReferenceLine y={0} stroke="#000" />
          <Bar dataKey="mean_21d" fill="#9c27b0" name="21-day" />
        </BarChart>
      </ResponsiveContainer>
    );
  };

  // Helper to render backtest scatter plot (predicted vs actual)
  const renderBacktestScatter = () => {
    if (!analysis?.backtest_results || analysis.backtest_results.length === 0) return null;

    const scatterData = analysis.backtest_results
      .filter((r: any) => !isNaN(r.actual_3d) && !isNaN(r.predicted_3d))
      .map((r: any) => ({
        actual: r.actual_3d,
        predicted: r.predicted_3d,
        date: r.date
      }));

    return (
      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="actual" label={{ value: 'Actual Return (%)', position: 'insideBottom', offset: -5 }} />
          <YAxis dataKey="predicted" label={{ value: 'Predicted Return (%)', angle: -90, position: 'insideLeft' }} />
          <Tooltip cursor={{ strokeDasharray: '3 3' }} />
          <Legend />
          <ReferenceLine y={0} stroke="#999" strokeDasharray="3 3" />
          <ReferenceLine x={0} stroke="#999" strokeDasharray="3 3" />
          <Scatter name="3-Day Predictions" data={scatterData} fill="#8884d8" />
        </ScatterChart>
      </ResponsiveContainer>
    );
  };

  if (loading && !analysis) {
    return (
      <Paper elevation={3} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
          <CircularProgress />
          <Typography variant="body1" sx={{ ml: 2 }}>
            Computing percentile forward mappings...
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

  const prediction = analysis.prediction;

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ShowChartIcon sx={{ fontSize: 32, color: 'primary.main' }} />
          <Typography variant="h5" component="h2">
            Percentile → Forward Return Mapping - {ticker}
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
        Prospective extrapolation: Turn current RSI-MA percentile into expected forward % change using empirical mapping,
        Markov transitions, regression, kernel smoothing, and ensemble methods.
        {analysis.cached && (
          <Chip
            label={`Cached (${analysis.cache_age_hours?.toFixed(1)}h old)`}
            size="small"
            color="info"
            sx={{ ml: 2 }}
          />
        )}
      </Typography>

      {/* Current State & Forecast Summary */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card sx={{ bgcolor: 'info.light' }}>
            <CardContent>
              <Typography variant="h6">Current Percentile</Typography>
              <Typography variant="h4">
                {analysis.current_percentile?.toFixed(1) || '0'}%ile
              </Typography>
              <Typography variant="caption">
                RSI-MA: {analysis.current_rsi_ma?.toFixed(2) || '0'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ bgcolor: prediction?.ensemble_forecast_3d > 0 ? 'success.light' : 'error.light' }}>
            <CardContent>
              <Typography variant="h6">3-Day Forecast</Typography>
              <Typography variant="h4" style={{ color: prediction?.ensemble_forecast_3d > 0 ? 'green' : 'red' }}>
                {prediction?.ensemble_forecast_3d > 0 ? '+' : ''}{prediction?.ensemble_forecast_3d?.toFixed(2) || '0'}%
              </Typography>
              <Typography variant="caption">
                Ensemble Prediction
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={2}>
          <Card sx={{ bgcolor: prediction?.ensemble_forecast_7d > 0 ? 'success.light' : 'error.light' }}>
            <CardContent>
              <Typography variant="h6">7-Day Forecast</Typography>
              <Typography variant="h4" style={{ color: prediction?.ensemble_forecast_7d > 0 ? 'green' : 'red' }}>
                {prediction?.ensemble_forecast_7d > 0 ? '+' : ''}{prediction?.ensemble_forecast_7d?.toFixed(2) || '0'}%
              </Typography>
              <Typography variant="caption">
                Ensemble
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={2}>
          <Card sx={{ bgcolor: prediction?.ensemble_forecast_14d > 0 ? 'success.light' : 'error.light' }}>
            <CardContent>
              <Typography variant="h6">14-Day Forecast</Typography>
              <Typography variant="h4" style={{ color: prediction?.ensemble_forecast_14d > 0 ? 'green' : 'red' }}>
                {prediction?.ensemble_forecast_14d > 0 ? '+' : ''}{prediction?.ensemble_forecast_14d?.toFixed(2) || '0'}%
              </Typography>
              <Typography variant="caption">
                Ensemble
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={2}>
          <Card sx={{ bgcolor: prediction?.ensemble_forecast_21d > 0 ? 'success.light' : 'error.light' }}>
            <CardContent>
              <Typography variant="h6">21-Day Forecast</Typography>
              <Typography variant="h4" style={{ color: prediction?.ensemble_forecast_21d > 0 ? 'green' : 'red' }}>
                {prediction?.ensemble_forecast_21d > 0 ? '+' : ''}{prediction?.ensemble_forecast_21d?.toFixed(2) || '0'}%
              </Typography>
              <Typography variant="caption">
                Ensemble
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange} variant="scrollable" scrollButtons="auto">
          <Tab label="📊 Empirical Bin Mapping" />
          <Tab label="🔄 Transition Matrices" />
          <Tab label="📈 Model Comparison" />
          <Tab label="🎯 Backtest Accuracy" />
          <Tab label="📉 Predicted vs Actual" />
        </Tabs>
      </Box>

      {/* Tab 0: Empirical Bin Mapping */}
      <TabPanel value={tabValue} index={0}>
        <Typography variant="h6" gutterBottom>
          Empirical Conditional Expectation: E[Return | Percentile Bin]
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Historical average returns for each percentile bin. This is the direct lookup table mapping
          percentile → expected forward % change.
        </Typography>

        {renderBinStatsChart()}

        <Typography variant="subtitle1" gutterBottom sx={{ mt: 3 }}>
          <strong>Detailed Statistics by Bin</strong>
        </Typography>

        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell><strong>Percentile Bin</strong></TableCell>
                <TableCell align="right"><strong>Count</strong></TableCell>
                <TableCell align="right"><strong>Mean 3d</strong></TableCell>
                <TableCell align="right"><strong>Median 3d</strong></TableCell>
                <TableCell align="right"><strong>Std 3d</strong></TableCell>
                <TableCell align="right"><strong>5th %ile</strong></TableCell>
                <TableCell align="right"><strong>95th %ile</strong></TableCell>
                <TableCell align="right"><strong>Upside</strong></TableCell>
                <TableCell align="right"><strong>Downside</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.values(analysis.bin_stats || {}).map((stats: any) => (
                <TableRow key={stats.bin_label}>
                  <TableCell><strong>{stats.bin_label}%</strong></TableCell>
                  <TableCell align="right">{stats.count}</TableCell>
                  <TableCell
                    align="right"
                    style={{ color: stats.mean_return_3d > 0 ? 'green' : 'red', fontWeight: 'bold' }}
                  >
                    {stats.mean_return_3d > 0 ? '+' : ''}{stats.mean_return_3d.toFixed(2)}%
                  </TableCell>
                  <TableCell align="right">{stats.median_return_3d.toFixed(2)}%</TableCell>
                  <TableCell align="right">{stats.std_return_3d.toFixed(2)}%</TableCell>
                  <TableCell align="right" style={{ color: 'red' }}>
                    {stats.pct_5_return_3d.toFixed(2)}%
                  </TableCell>
                  <TableCell align="right" style={{ color: 'green' }}>
                    +{stats.pct_95_return_3d.toFixed(2)}%
                  </TableCell>
                  <TableCell align="right" style={{ color: 'green' }}>
                    +{stats.upside_potential_3d.toFixed(2)}%
                  </TableCell>
                  <TableCell align="right" style={{ color: 'red' }}>
                    {stats.downside_risk_3d.toFixed(2)}%
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <Alert severity="info" sx={{ mt: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            <strong>How to Read This Table:</strong>
          </Typography>
          <Typography variant="body2">
            • <strong>Mean 3d:</strong> Average return 3 days forward when percentile is in this bin (direct lookup)
            <br />
            • <strong>5th/95th percentiles:</strong> Risk range (5% worst case, 95% best case)
            <br />
            • <strong>Upside Potential:</strong> Average positive return when signal is profitable
            <br />
            • <strong>Downside Risk:</strong> Volatility of negative returns (loss magnitude)
            <br />
            <br />
            <strong>Current Bin:</strong> {prediction?.empirical_bin_stats?.bin_label || 'N/A'} →
            Expected 3d return: {prediction?.empirical_bin_stats?.mean_return_3d > 0 ? '+' : ''}
            {prediction?.empirical_bin_stats?.mean_return_3d?.toFixed(2) || '0'}%
          </Typography>
        </Alert>

        {/* 7-Day Bar Chart */}
        <Typography variant="h6" gutterBottom sx={{ mt: 5 }}>
          7-Day Horizon: Bin Returns Overview
        </Typography>
        {renderBinStatsChart7d()}

        {/* 7-Day Detailed Statistics */}
        <Typography variant="subtitle1" gutterBottom sx={{ mt: 3 }}>
          <strong>Detailed Statistics by Bin - 7-Day Horizon</strong>
        </Typography>

        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell><strong>Percentile Bin</strong></TableCell>
                <TableCell align="right"><strong>Count</strong></TableCell>
                <TableCell align="right"><strong>Mean 7d</strong></TableCell>
                <TableCell align="right"><strong>Median 7d</strong></TableCell>
                <TableCell align="right"><strong>Std 7d</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.values(analysis.bin_stats || {}).map((stats: any) => (
                <TableRow key={stats.bin_label + '_7d'}>
                  <TableCell><strong>{stats.bin_label}%</strong></TableCell>
                  <TableCell align="right">{stats.count}</TableCell>
                  <TableCell
                    align="right"
                    style={{ color: stats.mean_return_7d > 0 ? 'green' : 'red', fontWeight: 'bold' }}
                  >
                    {stats.mean_return_7d > 0 ? '+' : ''}{stats.mean_return_7d.toFixed(2)}%
                  </TableCell>
                  <TableCell align="right">{stats.median_return_7d.toFixed(2)}%</TableCell>
                  <TableCell align="right">{stats.std_return_7d.toFixed(2)}%</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <Alert severity="info" sx={{ mt: 3 }}>
          <Typography variant="body2">
            <strong>Current Bin:</strong> {prediction?.empirical_bin_stats?.bin_label || 'N/A'} →
            Expected 7d return: {prediction?.empirical_bin_stats?.mean_return_7d > 0 ? '+' : ''}
            {prediction?.empirical_bin_stats?.mean_return_7d?.toFixed(2) || '0'}%
          </Typography>
        </Alert>

        {/* 14-Day Bar Chart */}
        <Typography variant="h6" gutterBottom sx={{ mt: 5 }}>
          14-Day Horizon: Bin Returns Overview
        </Typography>
        {renderBinStatsChart14d()}

        {/* 14-Day Detailed Statistics */}
        <Typography variant="subtitle1" gutterBottom sx={{ mt: 3 }}>
          <strong>Detailed Statistics by Bin - 14-Day Horizon</strong>
        </Typography>

        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell><strong>Percentile Bin</strong></TableCell>
                <TableCell align="right"><strong>Count</strong></TableCell>
                <TableCell align="right"><strong>Mean 14d</strong></TableCell>
                <TableCell align="right"><strong>Median 14d</strong></TableCell>
                <TableCell align="right"><strong>Std 14d</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.values(analysis.bin_stats || {}).map((stats: any) => (
                <TableRow key={stats.bin_label + '_14d'}>
                  <TableCell><strong>{stats.bin_label}%</strong></TableCell>
                  <TableCell align="right">{stats.count}</TableCell>
                  <TableCell
                    align="right"
                    style={{ color: stats.mean_return_14d > 0 ? 'green' : 'red', fontWeight: 'bold' }}
                  >
                    {stats.mean_return_14d > 0 ? '+' : ''}{stats.mean_return_14d.toFixed(2)}%
                  </TableCell>
                  <TableCell align="right">{stats.median_return_14d.toFixed(2)}%</TableCell>
                  <TableCell align="right">{stats.std_return_14d.toFixed(2)}%</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <Alert severity="info" sx={{ mt: 3 }}>
          <Typography variant="body2">
            <strong>Current Bin:</strong> {prediction?.empirical_bin_stats?.bin_label || 'N/A'} →
            Expected 14d return: {prediction?.empirical_bin_stats?.mean_return_14d > 0 ? '+' : ''}
            {prediction?.empirical_bin_stats?.mean_return_14d?.toFixed(2) || '0'}%
          </Typography>
        </Alert>

        {/* 21-Day Bar Chart */}
        <Typography variant="h6" gutterBottom sx={{ mt: 5 }}>
          21-Day Horizon: Bin Returns Overview
        </Typography>
        {renderBinStatsChart21d()}

        {/* 21-Day Detailed Statistics */}
        <Typography variant="subtitle1" gutterBottom sx={{ mt: 3 }}>
          <strong>Detailed Statistics by Bin - 21-Day Horizon</strong>
        </Typography>

        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell><strong>Percentile Bin</strong></TableCell>
                <TableCell align="right"><strong>Count</strong></TableCell>
                <TableCell align="right"><strong>Mean 21d</strong></TableCell>
                <TableCell align="right"><strong>Median 21d</strong></TableCell>
                <TableCell align="right"><strong>Std 21d</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.values(analysis.bin_stats || {}).map((stats: any) => (
                <TableRow key={stats.bin_label + '_21d'}>
                  <TableCell><strong>{stats.bin_label}%</strong></TableCell>
                  <TableCell align="right">{stats.count}</TableCell>
                  <TableCell
                    align="right"
                    style={{ color: stats.mean_return_21d > 0 ? 'green' : 'red', fontWeight: 'bold' }}
                  >
                    {stats.mean_return_21d > 0 ? '+' : ''}{stats.mean_return_21d.toFixed(2)}%
                  </TableCell>
                  <TableCell align="right">{stats.median_return_21d.toFixed(2)}%</TableCell>
                  <TableCell align="right">{stats.std_return_21d.toFixed(2)}%</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <Alert severity="info" sx={{ mt: 3 }}>
          <Typography variant="body2">
            <strong>Current Bin:</strong> {prediction?.empirical_bin_stats?.bin_label || 'N/A'} →
            Expected 21d return: {prediction?.empirical_bin_stats?.mean_return_21d > 0 ? '+' : ''}
            {prediction?.empirical_bin_stats?.mean_return_21d?.toFixed(2) || '0'}%
          </Typography>
        </Alert>
      </TabPanel>

      {/* Tab 1: Transition Matrices */}
      <TabPanel value={tabValue} index={1}>
        <Typography variant="h6" gutterBottom>
          Markov Transition Matrices: Percentile Evolution Probabilities
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          P[i,j] = Probability of moving from percentile bin i to bin j after h days.
          <br />
          Used to forecast future percentile distribution, then map to expected returns.
        </Typography>

        {analysis.transition_matrices && Object.entries(analysis.transition_matrices).map(([horizon, tm]: [string, any]) => (
          <Box key={horizon} sx={{ mb: 4 }}>
            <Typography variant="subtitle1" gutterBottom>
              <strong>{horizon} Transition Matrix</strong> (Sample size: {tm.sample_sizes?.reduce((a: number, b: number) => a + b, 0) || 0})
            </Typography>
            {renderTransitionMatrix(tm)}
          </Box>
        ))}

        <Alert severity="info" sx={{ mt: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            <strong>Markov Forecast Logic:</strong>
          </Typography>
          <Typography variant="body2">
            1. Start from current bin (e.g., 75-85%ile)
            <br />
            2. Look at transition probabilities to all future bins
            <br />
            3. Weight each future bin's expected return by its transition probability
            <br />
            4. Sum to get Markov-forecasted return
            <br />
            <br />
            <strong>Current Markov Forecasts:</strong>
            <br />
            3-day: {prediction?.markov_forecast_3d > 0 ? '+' : ''}{prediction?.markov_forecast_3d?.toFixed(2) || '0'}%
            <br />
            7-day: {prediction?.markov_forecast_7d > 0 ? '+' : ''}{prediction?.markov_forecast_7d?.toFixed(2) || '0'}%
            <br />
            14-day: {prediction?.markov_forecast_14d > 0 ? '+' : ''}{prediction?.markov_forecast_14d?.toFixed(2) || '0'}%
            <br />
            21-day: {prediction?.markov_forecast_21d > 0 ? '+' : ''}{prediction?.markov_forecast_21d?.toFixed(2) || '0'}%
          </Typography>
        </Alert>
      </TabPanel>

      {/* Tab 2: Model Comparison */}
      <TabPanel value={tabValue} index={2}>
        <Typography variant="h6" gutterBottom>
          Model Comparison: All Methods for 3-Day Forecast
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Compare predictions from different methods: Empirical, Markov, Linear Regression, Polynomial,
          Quantile Regression (median, 5th, 95th), Kernel Smoothing, and Ensemble average.
        </Typography>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>Method</strong></TableCell>
                <TableCell align="right"><strong>3-Day Forecast</strong></TableCell>
                <TableCell><strong>Notes</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell>Empirical (Bin Lookup)</TableCell>
                <TableCell align="right" style={{ color: prediction?.empirical_bin_stats?.mean_return_3d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                  {prediction?.empirical_bin_stats?.mean_return_3d > 0 ? '+' : ''}
                  {prediction?.empirical_bin_stats?.mean_return_3d?.toFixed(2) || '0'}%
                </TableCell>
                <TableCell>Simple historical average for current bin</TableCell>
              </TableRow>

              <TableRow>
                <TableCell>Markov Chain</TableCell>
                <TableCell align="right" style={{ color: prediction?.markov_forecast_3d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                  {prediction?.markov_forecast_3d > 0 ? '+' : ''}{prediction?.markov_forecast_3d?.toFixed(2) || '0'}%
                </TableCell>
                <TableCell>Transition-weighted expectation</TableCell>
              </TableRow>

              {prediction?.linear_regression && (
                <TableRow>
                  <TableCell>Linear Regression</TableCell>
                  <TableCell align="right" style={{ color: prediction.linear_regression.forecast_3d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                    {prediction.linear_regression.forecast_3d > 0 ? '+' : ''}{prediction.linear_regression.forecast_3d.toFixed(2)}%
                  </TableCell>
                  <TableCell>R² = {prediction.linear_regression.r_squared.toFixed(3)}, MAE = {prediction.linear_regression.mae.toFixed(2)}%</TableCell>
                </TableRow>
              )}

              {prediction?.polynomial_regression && (
                <TableRow>
                  <TableCell>Polynomial Regression</TableCell>
                  <TableCell align="right" style={{ color: prediction.polynomial_regression.forecast_3d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                    {prediction.polynomial_regression.forecast_3d > 0 ? '+' : ''}{prediction.polynomial_regression.forecast_3d.toFixed(2)}%
                  </TableCell>
                  <TableCell>Degree 2, R² = {prediction.polynomial_regression.r_squared.toFixed(3)}</TableCell>
                </TableRow>
              )}

              <TableRow>
                <TableCell>Quantile Regression (Median)</TableCell>
                <TableCell align="right" style={{ color: prediction?.quantile_regression_median?.forecast_3d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                  {prediction?.quantile_regression_median?.forecast_3d > 0 ? '+' : ''}
                  {prediction?.quantile_regression_median?.forecast_3d?.toFixed(2) || '0'}%
                </TableCell>
                <TableCell>50th percentile prediction</TableCell>
              </TableRow>

              <TableRow sx={{ bgcolor: 'error.light' }}>
                <TableCell>Quantile Regression (5th)</TableCell>
                <TableCell align="right" style={{ fontWeight: 'bold', color: 'red' }}>
                  {prediction?.quantile_regression_05?.forecast_3d?.toFixed(2) || '0'}%
                </TableCell>
                <TableCell>Downside risk (worst 5%)</TableCell>
              </TableRow>

              <TableRow sx={{ bgcolor: 'success.light' }}>
                <TableCell>Quantile Regression (95th)</TableCell>
                <TableCell align="right" style={{ fontWeight: 'bold', color: 'green' }}>
                  +{prediction?.quantile_regression_95?.forecast_3d?.toFixed(2) || '0'}%
                </TableCell>
                <TableCell>Upside potential (best 5%)</TableCell>
              </TableRow>

              <TableRow>
                <TableCell>Kernel Smoothing</TableCell>
                <TableCell align="right" style={{ color: prediction?.kernel_forecast?.forecast_3d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                  {prediction?.kernel_forecast?.forecast_3d > 0 ? '+' : ''}
                  {prediction?.kernel_forecast?.forecast_3d?.toFixed(2) || '0'}%
                </TableCell>
                <TableCell>
                  Bandwidth = {prediction?.kernel_forecast?.bandwidth || 0}, Eff. n = {prediction?.kernel_forecast?.effective_sample_size?.toFixed(0) || 0}
                </TableCell>
              </TableRow>

              <TableRow sx={{ bgcolor: 'primary.light' }}>
                <TableCell><strong>Ensemble (Average)</strong></TableCell>
                <TableCell align="right" style={{ color: prediction?.ensemble_forecast_3d > 0 ? 'green' : 'red', fontWeight: 'bold', fontSize: '1.1em' }}>
                  {prediction?.ensemble_forecast_3d > 0 ? '+' : ''}{prediction?.ensemble_forecast_3d?.toFixed(2) || '0'}%
                </TableCell>
                <TableCell><strong>Recommended: Average of all methods</strong></TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>

        <Alert severity="success" sx={{ mt: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            <strong>Ensemble Advantage:</strong>
          </Typography>
          <Typography variant="body2">
            Averaging multiple methods reduces overfitting and improves out-of-sample accuracy.
            The ensemble forecast combines strengths of each approach:
            <br />
            • Empirical: Historical ground truth
            <br />
            • Markov: Accounts for percentile evolution
            <br />
            • Regression: Captures continuous relationship
            <br />
            • Quantile: Models tail risk
            <br />
            • Kernel: Nonparametric smoothing
          </Typography>
        </Alert>

        {/* 7-Day Forecast Table */}
        <Typography variant="h6" gutterBottom sx={{ mt: 5 }}>
          Model Comparison: All Methods for 7-Day Forecast
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Compare predictions from different methods for the 7-day horizon.
        </Typography>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>Method</strong></TableCell>
                <TableCell align="right"><strong>7-Day Forecast</strong></TableCell>
                <TableCell><strong>Notes</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell>Empirical (Bin Lookup)</TableCell>
                <TableCell align="right" style={{ color: prediction?.empirical_bin_stats?.mean_return_7d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                  {prediction?.empirical_bin_stats?.mean_return_7d > 0 ? '+' : ''}
                  {prediction?.empirical_bin_stats?.mean_return_7d?.toFixed(2) || '0'}%
                </TableCell>
                <TableCell>Simple historical average for current bin</TableCell>
              </TableRow>

              <TableRow>
                <TableCell>Markov Chain</TableCell>
                <TableCell align="right" style={{ color: prediction?.markov_forecast_7d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                  {prediction?.markov_forecast_7d > 0 ? '+' : ''}{prediction?.markov_forecast_7d?.toFixed(2) || '0'}%
                </TableCell>
                <TableCell>Transition-weighted expectation</TableCell>
              </TableRow>

              {prediction?.linear_regression && (
                <TableRow>
                  <TableCell>Linear Regression</TableCell>
                  <TableCell align="right" style={{ color: prediction.linear_regression.forecast_7d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                    {prediction.linear_regression.forecast_7d > 0 ? '+' : ''}{prediction.linear_regression.forecast_7d.toFixed(2)}%
                  </TableCell>
                  <TableCell>R² = {prediction.linear_regression.r_squared.toFixed(3)}, MAE = {prediction.linear_regression.mae.toFixed(2)}%</TableCell>
                </TableRow>
              )}

              {prediction?.polynomial_regression && (
                <TableRow>
                  <TableCell>Polynomial Regression</TableCell>
                  <TableCell align="right" style={{ color: prediction.polynomial_regression.forecast_7d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                    {prediction.polynomial_regression.forecast_7d > 0 ? '+' : ''}{prediction.polynomial_regression.forecast_7d.toFixed(2)}%
                  </TableCell>
                  <TableCell>Degree 2, R² = {prediction.polynomial_regression.r_squared.toFixed(3)}</TableCell>
                </TableRow>
              )}

              <TableRow>
                <TableCell>Quantile Regression (Median)</TableCell>
                <TableCell align="right" style={{ color: prediction?.quantile_regression_median?.forecast_7d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                  {prediction?.quantile_regression_median?.forecast_7d > 0 ? '+' : ''}
                  {prediction?.quantile_regression_median?.forecast_7d?.toFixed(2) || '0'}%
                </TableCell>
                <TableCell>50th percentile prediction</TableCell>
              </TableRow>

              <TableRow>
                <TableCell>Kernel Smoothing</TableCell>
                <TableCell align="right" style={{ color: prediction?.kernel_forecast?.forecast_7d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                  {prediction?.kernel_forecast?.forecast_7d > 0 ? '+' : ''}
                  {prediction?.kernel_forecast?.forecast_7d?.toFixed(2) || '0'}%
                </TableCell>
                <TableCell>
                  Bandwidth = {prediction?.kernel_forecast?.bandwidth || 0}, Eff. n = {prediction?.kernel_forecast?.effective_sample_size?.toFixed(0) || 0}
                </TableCell>
              </TableRow>

              <TableRow sx={{ bgcolor: 'primary.light' }}>
                <TableCell><strong>Ensemble (Average)</strong></TableCell>
                <TableCell align="right" style={{ color: prediction?.ensemble_forecast_7d > 0 ? 'green' : 'red', fontWeight: 'bold', fontSize: '1.1em' }}>
                  {prediction?.ensemble_forecast_7d > 0 ? '+' : ''}{prediction?.ensemble_forecast_7d?.toFixed(2) || '0'}%
                </TableCell>
                <TableCell><strong>Recommended: Average of all methods</strong></TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>

        {/* 14-Day Forecast Table */}
        <Typography variant="h6" gutterBottom sx={{ mt: 5 }}>
          Model Comparison: All Methods for 14-Day Forecast
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Compare predictions from different methods for the 14-day horizon.
        </Typography>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>Method</strong></TableCell>
                <TableCell align="right"><strong>14-Day Forecast</strong></TableCell>
                <TableCell><strong>Notes</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell>Empirical (Bin Lookup)</TableCell>
                <TableCell align="right" style={{ color: prediction?.empirical_bin_stats?.mean_return_14d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                  {prediction?.empirical_bin_stats?.mean_return_14d > 0 ? '+' : ''}
                  {prediction?.empirical_bin_stats?.mean_return_14d?.toFixed(2) || '0'}%
                </TableCell>
                <TableCell>Simple historical average for current bin</TableCell>
              </TableRow>

              <TableRow>
                <TableCell>Markov Chain</TableCell>
                <TableCell align="right" style={{ color: prediction?.markov_forecast_14d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                  {prediction?.markov_forecast_14d > 0 ? '+' : ''}{prediction?.markov_forecast_14d?.toFixed(2) || '0'}%
                </TableCell>
                <TableCell>Transition-weighted expectation</TableCell>
              </TableRow>

              {prediction?.linear_regression && (
                <TableRow>
                  <TableCell>Linear Regression</TableCell>
                  <TableCell align="right" style={{ color: prediction.linear_regression.forecast_14d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                    {prediction.linear_regression.forecast_14d > 0 ? '+' : ''}{prediction.linear_regression.forecast_14d.toFixed(2)}%
                  </TableCell>
                  <TableCell>R² = {prediction.linear_regression.r_squared.toFixed(3)}, MAE = {prediction.linear_regression.mae.toFixed(2)}%</TableCell>
                </TableRow>
              )}

              {prediction?.polynomial_regression && (
                <TableRow>
                  <TableCell>Polynomial Regression</TableCell>
                  <TableCell align="right" style={{ color: prediction.polynomial_regression.forecast_14d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                    {prediction.polynomial_regression.forecast_14d > 0 ? '+' : ''}{prediction.polynomial_regression.forecast_14d.toFixed(2)}%
                  </TableCell>
                  <TableCell>Degree 2, R² = {prediction.polynomial_regression.r_squared.toFixed(3)}</TableCell>
                </TableRow>
              )}

              <TableRow>
                <TableCell>Quantile Regression (Median)</TableCell>
                <TableCell align="right" style={{ color: prediction?.quantile_regression_median?.forecast_14d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                  {prediction?.quantile_regression_median?.forecast_14d > 0 ? '+' : ''}
                  {prediction?.quantile_regression_median?.forecast_14d?.toFixed(2) || '0'}%
                </TableCell>
                <TableCell>50th percentile prediction</TableCell>
              </TableRow>

              <TableRow>
                <TableCell>Kernel Smoothing</TableCell>
                <TableCell align="right" style={{ color: prediction?.kernel_forecast?.forecast_14d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                  {prediction?.kernel_forecast?.forecast_14d > 0 ? '+' : ''}
                  {prediction?.kernel_forecast?.forecast_14d?.toFixed(2) || '0'}%
                </TableCell>
                <TableCell>
                  Bandwidth = {prediction?.kernel_forecast?.bandwidth || 0}, Eff. n = {prediction?.kernel_forecast?.effective_sample_size?.toFixed(0) || 0}
                </TableCell>
              </TableRow>

              <TableRow sx={{ bgcolor: 'primary.light' }}>
                <TableCell><strong>Ensemble (Average)</strong></TableCell>
                <TableCell align="right" style={{ color: prediction?.ensemble_forecast_14d > 0 ? 'green' : 'red', fontWeight: 'bold', fontSize: '1.1em' }}>
                  {prediction?.ensemble_forecast_14d > 0 ? '+' : ''}{prediction?.ensemble_forecast_14d?.toFixed(2) || '0'}%
                </TableCell>
                <TableCell><strong>Recommended: Average of all methods</strong></TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>

        {/* 21-Day Forecast Table */}
        <Typography variant="h6" gutterBottom sx={{ mt: 5 }}>
          Model Comparison: All Methods for 21-Day Forecast
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Compare predictions from different methods for the 21-day horizon.
        </Typography>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>Method</strong></TableCell>
                <TableCell align="right"><strong>21-Day Forecast</strong></TableCell>
                <TableCell><strong>Notes</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell>Empirical (Bin Lookup)</TableCell>
                <TableCell align="right" style={{ color: prediction?.empirical_bin_stats?.mean_return_21d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                  {prediction?.empirical_bin_stats?.mean_return_21d > 0 ? '+' : ''}
                  {prediction?.empirical_bin_stats?.mean_return_21d?.toFixed(2) || '0'}%
                </TableCell>
                <TableCell>Simple historical average for current bin</TableCell>
              </TableRow>

              <TableRow>
                <TableCell>Markov Chain</TableCell>
                <TableCell align="right" style={{ color: prediction?.markov_forecast_21d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                  {prediction?.markov_forecast_21d > 0 ? '+' : ''}{prediction?.markov_forecast_21d?.toFixed(2) || '0'}%
                </TableCell>
                <TableCell>Transition-weighted expectation</TableCell>
              </TableRow>

              {prediction?.linear_regression && (
                <TableRow>
                  <TableCell>Linear Regression</TableCell>
                  <TableCell align="right" style={{ color: prediction.linear_regression.forecast_21d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                    {prediction.linear_regression.forecast_21d > 0 ? '+' : ''}{prediction.linear_regression.forecast_21d.toFixed(2)}%
                  </TableCell>
                  <TableCell>R² = {prediction.linear_regression.r_squared.toFixed(3)}, MAE = {prediction.linear_regression.mae.toFixed(2)}%</TableCell>
                </TableRow>
              )}

              {prediction?.polynomial_regression && (
                <TableRow>
                  <TableCell>Polynomial Regression</TableCell>
                  <TableCell align="right" style={{ color: prediction.polynomial_regression.forecast_21d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                    {prediction.polynomial_regression.forecast_21d > 0 ? '+' : ''}{prediction.polynomial_regression.forecast_21d.toFixed(2)}%
                  </TableCell>
                  <TableCell>Degree 2, R² = {prediction.polynomial_regression.r_squared.toFixed(3)}</TableCell>
                </TableRow>
              )}

              <TableRow>
                <TableCell>Quantile Regression (Median)</TableCell>
                <TableCell align="right" style={{ color: prediction?.quantile_regression_median?.forecast_21d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                  {prediction?.quantile_regression_median?.forecast_21d > 0 ? '+' : ''}
                  {prediction?.quantile_regression_median?.forecast_21d?.toFixed(2) || '0'}%
                </TableCell>
                <TableCell>50th percentile prediction</TableCell>
              </TableRow>

              <TableRow>
                <TableCell>Kernel Smoothing</TableCell>
                <TableCell align="right" style={{ color: prediction?.kernel_forecast?.forecast_21d > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                  {prediction?.kernel_forecast?.forecast_21d > 0 ? '+' : ''}
                  {prediction?.kernel_forecast?.forecast_21d?.toFixed(2) || '0'}%
                </TableCell>
                <TableCell>
                  Bandwidth = {prediction?.kernel_forecast?.bandwidth || 0}, Eff. n = {prediction?.kernel_forecast?.effective_sample_size?.toFixed(0) || 0}
                </TableCell>
              </TableRow>

              <TableRow sx={{ bgcolor: 'primary.light' }}>
                <TableCell><strong>Ensemble (Average)</strong></TableCell>
                <TableCell align="right" style={{ color: prediction?.ensemble_forecast_21d > 0 ? 'green' : 'red', fontWeight: 'bold', fontSize: '1.1em' }}>
                  {prediction?.ensemble_forecast_21d > 0 ? '+' : ''}{prediction?.ensemble_forecast_21d?.toFixed(2) || '0'}%
                </TableCell>
                <TableCell><strong>Recommended: Average of all methods</strong></TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      {/* Tab 3: Backtest Accuracy */}
      <TabPanel value={tabValue} index={3}>
        <Typography variant="h6" gutterBottom>
          Rolling Window Backtest: Out-of-Sample Accuracy Metrics
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Train on past 252 days, predict next 21 days, then roll forward. Evaluate forecast quality
          using MAE, RMSE, Hit Rate, Sharpe Ratio, and Information Ratio.
        </Typography>

        {analysis.accuracy_metrics && Object.entries(analysis.accuracy_metrics).map(([horizon, metrics]: [string, any]) => (
          <Card key={horizon} sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {horizon.toUpperCase()} Horizon Metrics
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle2">Error Metrics</Typography>
                  <Typography variant="body2">
                    MAE: <strong>{metrics.mae?.toFixed(2) || 0}%</strong>
                    <br />
                    RMSE: <strong>{metrics.rmse?.toFixed(2) || 0}%</strong>
                    <br />
                    Correlation: <strong>{metrics.correlation?.toFixed(3) || 0}</strong>
                  </Typography>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle2">Trading Performance</Typography>
                  <Typography variant="body2">
                    Hit Rate: <strong style={{ color: metrics.hit_rate > 55 ? 'green' : 'red' }}>
                      {metrics.hit_rate?.toFixed(1) || 0}%
                    </strong>
                    <br />
                    Sharpe Ratio: <strong style={{ color: metrics.sharpe > 1 ? 'green' : 'red' }}>
                      {metrics.sharpe?.toFixed(2) || 0}
                    </strong>
                    <br />
                    Information Ratio: <strong>{metrics.information_ratio?.toFixed(2) || 0}</strong>
                  </Typography>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle2">Return Statistics</Typography>
                  <Typography variant="body2">
                    Mean Prediction: <strong style={{ color: metrics.mean_prediction > 0 ? 'green' : 'red' }}>
                      {metrics.mean_prediction > 0 ? '+' : ''}{metrics.mean_prediction?.toFixed(2) || 0}%
                    </strong>
                    <br />
                    Mean Actual: <strong style={{ color: metrics.mean_actual > 0 ? 'green' : 'red' }}>
                      {metrics.mean_actual > 0 ? '+' : ''}{metrics.mean_actual?.toFixed(2) || 0}%
                    </strong>
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        ))}

        <Alert severity={
          analysis.accuracy_metrics?.['3d']?.hit_rate > 55 && analysis.accuracy_metrics?.['3d']?.sharpe > 1 ? 'success' : 'info'
        }>
          <Typography variant="subtitle2" gutterBottom>
            <strong>Interpretation:</strong>
          </Typography>
          <Typography variant="body2">
            • <strong>Hit Rate &gt; 55%:</strong> Model has predictive edge (better than random)
            <br />
            • <strong>Sharpe &gt; 1.0:</strong> Good risk-adjusted returns
            <br />
            • <strong>Information Ratio &gt; 0.5:</strong> Outperforms naive long-only strategy
            <br />
            • <strong>Correlation &gt; 0.3:</strong> Meaningful relationship between predictions and outcomes
            <br />
            <br />
            {analysis.accuracy_metrics?.['3d']?.hit_rate > 55 && analysis.accuracy_metrics?.['3d']?.sharpe > 1 ? (
              <span style={{ color: 'green' }}>
                ✅ Model shows significant predictive power! Safe to use for trading decisions.
              </span>
            ) : (
              <span style={{ color: 'orange' }}>
                ⚠️ Model performance is modest. Use with caution and combine with other signals.
              </span>
            )}
          </Typography>
        </Alert>
      </TabPanel>

      {/* Tab 4: Predicted vs Actual Scatter */}
      <TabPanel value={tabValue} index={4}>
        <Typography variant="h6" gutterBottom>
          Predicted vs Actual Returns: Visual Validation
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Scatter plot of out-of-sample predictions vs actual realized returns. Points near the diagonal
          indicate accurate predictions. Spread indicates forecast error variance.
        </Typography>

        {renderBacktestScatter()}

        <Typography variant="subtitle1" gutterBottom sx={{ mt: 3 }}>
          <strong>Recent Predictions (Last 20)</strong>
        </Typography>

        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell align="right">Percentile</TableCell>
                <TableCell align="right">Predicted</TableCell>
                <TableCell align="right">Actual</TableCell>
                <TableCell align="right">Error</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {analysis.backtest_results?.slice(-20).reverse().map((result: any, idx: number) => {
                const error = result.actual_3d - result.predicted_3d;
                return (
                  <TableRow key={idx}>
                    <TableCell>{result.date}</TableCell>
                    <TableCell align="right">{result.percentile?.toFixed(1) || 0}%</TableCell>
                    <TableCell align="right" style={{ color: result.predicted_3d > 0 ? 'green' : 'red' }}>
                      {result.predicted_3d > 0 ? '+' : ''}{result.predicted_3d?.toFixed(2) || 0}%
                    </TableCell>
                    <TableCell align="right" style={{ color: result.actual_3d > 0 ? 'green' : 'red' }}>
                      {result.actual_3d > 0 ? '+' : ''}{result.actual_3d?.toFixed(2) || 0}%
                    </TableCell>
                    <TableCell align="right" style={{ color: Math.abs(error) < 1 ? 'green' : 'red' }}>
                      {error > 0 ? '+' : ''}{error?.toFixed(2) || 0}%
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>
    </Paper>
  );
};

export default PercentileForwardMapper;
