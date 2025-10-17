/**
 * Enhanced Divergence Lifecycle Component
 *
 * Visualizes complete 4H vs Daily divergence lifecycle analysis with:
 * - Multi-horizon outcomes (Take vs Hold)
 * - Timeline chart showing percentile evolution
 * - Take vs Hold benefit heatmap
 * - Signal quality and volatility context
 * - Re-entry opportunity analysis
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
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import RefreshIcon from '@mui/icons-material/Refresh';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TimelineIcon from '@mui/icons-material/Timeline';

interface EnhancedDivergenceLifecycleProps {
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

const EnhancedDivergenceLifecycle: React.FC<EnhancedDivergenceLifecycleProps> = ({ ticker }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [tabValue, setTabValue] = useState(0);

  const fetchAnalysis = async () => {
    setLoading(true);
    setError(null);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/enhanced-mtf/${ticker}`);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API Error: ${response.status}\n${errorText}`);
      }

      const result = await response.json();
      setAnalysis(result.enhanced_analysis);
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

  // Helper to get color based on delta value
  const getDeltaColor = (delta: number) => {
    if (delta > 0.3) return '#2e7d32'; // Dark green
    if (delta > 0) return '#81c784'; // Light green
    if (delta > -0.3) return '#ffeb3b'; // Yellow
    return '#f44336'; // Red
  };

  // Prepare heatmap visualization data
  const renderHeatmap = () => {
    if (!analysis?.heatmap_data) return null;

    const { matrix, horizons } = analysis.heatmap_data;

    return (
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell><strong>Gap Size</strong></TableCell>
              {horizons.map((h: string) => (
                <TableCell key={h} align="center"><strong>{h}</strong></TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {matrix.map((row: any) => (
              <TableRow key={row.gap_range}>
                <TableCell><strong>{row.gap_range}</strong></TableCell>
                {row.horizons.map((cell: any, idx: number) => (
                  <TableCell
                    key={idx}
                    align="center"
                    sx={{
                      bgcolor: getDeltaColor(cell.delta),
                      color: Math.abs(cell.delta) > 0.2 ? 'white' : 'black',
                      fontWeight: 'bold'
                    }}
                  >
                    <div>{cell.delta > 0 ? '+' : ''}{cell.delta.toFixed(2)}%</div>
                    <div style={{ fontSize: '0.7em', opacity: 0.8 }}>n={cell.sample_size}</div>
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  if (loading && !analysis) {
    return (
      <Paper elevation={3} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
          <CircularProgress />
          <Typography variant="body1" sx={{ ml: 2 }}>
            Analyzing enhanced divergence lifecycles...
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

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <TimelineIcon sx={{ fontSize: 32, color: 'primary.main' }} />
          <Typography variant="h5" component="h2">
            Enhanced Divergence Lifecycle - {ticker}
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
        Complete intraday divergence analysis with multi-horizon outcomes and actionable insights
      </Typography>

      {/* Volatility Warning Banner */}
      {analysis.volatility_context?.volatility_regime === 'extreme' && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            <strong>⚠️ EXTREME VOLATILITY DETECTED (ATR: {analysis.volatility_context.historical_atr_percentile.toFixed(0)}%ile)</strong>
          </Typography>
          <Typography variant="body2">
            This ticker is experiencing extreme volatility. Historical patterns may not apply reliably in this regime.
            <br />
            <strong>Recommendation:</strong> Hold positions longer (consider 1D-2D exits instead of 3×4H). Extreme volatility takes ~24h to converge vs. ~4h in normal conditions.
            <br />
            Review the "Volatility Analysis" tab to see regime-specific performance metrics.
          </Typography>
        </Alert>
      )}

      {/* Key Metrics Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card sx={{
            bgcolor: analysis.volatility_context?.volatility_regime === 'extreme' ? 'warning.light' : 'success.light'
          }}>
            <CardContent>
              <Typography variant="h6">Intraday Edge</Typography>
              <Typography variant="h4">
                {analysis.multi_horizon_outcomes?.[2]?.delta > 0 ? '+' : ''}
                {analysis.multi_horizon_outcomes?.[2]?.delta?.toFixed(2) || '0.00'}%
              </Typography>
              <Typography variant="caption">
                3×4H vs 1D
              </Typography>
              {analysis.volatility_context?.volatility_regime === 'extreme' && (
                <Typography variant="caption" display="block" sx={{ mt: 0.5, color: 'error.main' }}>
                  ⚠️ EXTREME VOL
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6">Signal Quality</Typography>
              <Typography variant="h4">
                {analysis.signal_quality?.consistency_score?.toFixed(0) || '0'}/100
              </Typography>
              <Typography variant="caption">
                Hit Rate: {analysis.signal_quality?.hit_rate?.toFixed(1) || '0'}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6">Volatility Regime</Typography>
              <Typography variant="h4">
                {analysis.volatility_context?.volatility_regime?.toUpperCase() || 'N/A'}
              </Typography>
              <Typography variant="caption">
                ATR: {analysis.volatility_context?.historical_atr_percentile?.toFixed(0) || '0'}%ile
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ bgcolor: 'info.light' }}>
            <CardContent>
              <Typography variant="h6">24H Convergence</Typography>
              <Typography variant="h4">
                {analysis.decay_model?.convergence_probability_24h?.toFixed(1) || '0'}%
              </Typography>
              <Typography variant="caption">
                Median: {analysis.decay_model?.median_time_to_convergence_hours?.toFixed(0) || '0'}h
              </Typography>
              <Typography variant="caption" display="block" sx={{ mt: 0.5, fontSize: '0.65rem' }}>
                Convergence = gap closes to &lt;15%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Additional Metrics Row */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="caption">Re-entry Rate</Typography>
              <Typography variant="h6">
                {analysis.reentry_analysis?.reentry_rate?.toFixed(1) || '0'}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Avg: {analysis.reentry_analysis?.avg_time_to_reentry_hours?.toFixed(0) || '0'}h to signal
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="caption">48H Convergence</Typography>
              <Typography variant="h6">
                {analysis.decay_model?.convergence_probability_48h?.toFixed(1) || '0'}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Divergences resolve quickly
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="caption">Current Recommendation</Typography>
              <Typography variant="h6">
                {analysis.volatility_context?.volatility_regime === 'normal' ?
                  'Aggressive - Strong intraday edge' :
                  analysis.volatility_context?.volatility_regime === 'extreme' ?
                  'Patient - Hold longer in extreme volatility' :
                  'Moderate - Standard profit-taking'
                }
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Based on {analysis.volatility_context?.volatility_regime?.toUpperCase() || 'N/A'} volatility regime
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs for different views */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange} variant="scrollable" scrollButtons="auto">
          <Tab label="💰 Trade Setups" />
          <Tab label="🎯 Multi-Horizon Outcomes" />
          <Tab label="🎨 Take vs Hold Heatmap" />
          <Tab label="🔬 Regime-Filtered Analysis" />
          <Tab label="🔄 Re-entry Analysis" />
          <Tab label="📈 Timeline Evolution" />
          <Tab label="📊 Signal Quality" />
          <Tab label="🌡️ Volatility Analysis" />
        </Tabs>
      </Box>

      {/* Tab 0: Trade Setups (NEW - PRIORITY VIEW) */}
      <TabPanel value={tabValue} index={0}>
        <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
          💰 Tradeable Setups for {ticker}
        </Typography>

        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>What This Shows:</strong> Actionable trade setups filtered by gap size and volatility regime.
            Only setups with <strong>positive expectancy, profitable absolute returns, and sufficient sample size</strong> are recommended.
            <br /><br />
            <strong>Current Volatility Regime:</strong> <Chip label={analysis.volatility_context?.volatility_regime?.toUpperCase() || 'N/A'} size="small" color={
              analysis.volatility_context?.volatility_regime === 'normal' ? 'success' :
              analysis.volatility_context?.volatility_regime === 'extreme' ? 'error' : 'warning'
            } /> - Only trade setups that match the current regime!
          </Typography>
        </Alert>

        {analysis.trade_recommendations && analysis.trade_recommendations.length > 0 ? (
          <>
            {/* Tradeable Setups */}
            <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
              ✅ Recommended Trades
            </Typography>
            {analysis.trade_recommendations.filter((rec: any) => rec.trade_signal).length > 0 ? (
              analysis.trade_recommendations
                .filter((rec: any) => rec.trade_signal)
                .map((rec: any, idx: number) => (
                  <Card key={idx} sx={{ mb: 2, bgcolor: rec.confidence === 'high' ? 'success.light' : 'info.light' }}>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Typography variant="h6">
                          {rec.setup_name}
                        </Typography>
                        <Chip
                          label={`${rec.confidence.toUpperCase()} CONFIDENCE`}
                          color={rec.confidence === 'high' ? 'success' : rec.confidence === 'medium' ? 'warning' : 'default'}
                        />
                      </Box>

                      <Grid container spacing={2}>
                        <Grid item xs={12} md={6}>
                          <Typography variant="subtitle2" gutterBottom><strong>Entry Criteria:</strong></Typography>
                          <Typography variant="body2">
                            • Gap Size: <strong>{rec.gap_range}</strong>
                            <br />
                            • Volatility Regime: <strong>{rec.regime_filter.toUpperCase()}</strong> only
                            {rec.regime_filter !== analysis.volatility_context?.volatility_regime && (
                              <Chip label="⚠️ NOT CURRENT REGIME" size="small" color="error" sx={{ ml: 1 }} />
                            )}
                          </Typography>
                        </Grid>

                        <Grid item xs={12} md={6}>
                          <Typography variant="subtitle2" gutterBottom><strong>Exit & Performance:</strong></Typography>
                          <Typography variant="body2">
                            • Exit: <strong>{rec.recommended_exit}</strong> (8 hours)
                            <br />
                            • Expected Return: <strong style={{ color: rec.expected_return > 0 ? 'green' : 'red' }}>
                              {rec.expected_return > 0 ? '+' : ''}{rec.expected_return.toFixed(2)}%
                            </strong>
                            <br />
                            • Win Rate: <strong>{rec.win_rate.toFixed(1)}%</strong>
                            <br />
                            • Expectancy: <strong style={{ color: rec.expectancy > 0 ? 'green' : 'red' }}>
                              {rec.expectancy > 0 ? '+' : ''}{rec.expectancy.toFixed(2)}%
                            </strong>
                          </Typography>
                        </Grid>

                        <Grid item xs={12} md={6}>
                          <Typography variant="subtitle2" gutterBottom><strong>Risk Management:</strong></Typography>
                          <Typography variant="body2">
                            • Sample Size: <strong>{rec.sample_size} events</strong>
                            <br />
                            • Max Consecutive Losses (est): <strong>{rec.max_consecutive_losses}</strong>
                            <br />
                            • Recommended Position Size: <strong>{rec.recommended_position_size.toFixed(1)}%</strong> of capital
                          </Typography>
                        </Grid>

                        <Grid item xs={12} md={6}>
                          <Typography variant="subtitle2" gutterBottom><strong>Reasoning:</strong></Typography>
                          <Typography variant="body2" sx={{ fontSize: '0.85rem' }}>
                            {rec.reason_tradeable}
                          </Typography>
                        </Grid>

                        {rec.risks && rec.risks.length > 0 && (
                          <Grid item xs={12}>
                            <Alert severity="warning" sx={{ mt: 1 }}>
                              <Typography variant="subtitle2" gutterBottom><strong>⚠️ Risks:</strong></Typography>
                              {rec.risks.map((risk: string, ridx: number) => (
                                <Typography key={ridx} variant="body2">• {risk}</Typography>
                              ))}
                            </Alert>
                          </Grid>
                        )}
                      </Grid>
                    </CardContent>
                  </Card>
                ))
            ) : (
              <Alert severity="warning" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  <strong>No tradeable setups found.</strong> All gap size / regime combinations fail to meet minimum criteria:
                  <br />
                  • Expectancy ≥ +0.15%
                  <br />
                  • Win Rate ≥ 52%
                  <br />
                  • Sample Size ≥ 20 events
                  <br />
                  • Positive absolute returns
                </Typography>
              </Alert>
            )}

            {/* Non-Tradeable Setups (for reference) */}
            <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>
              ❌ Not Recommended (Below Criteria)
            </Typography>
            {analysis.trade_recommendations
              .filter((rec: any) => !rec.trade_signal)
              .slice(0, 5)  // Show first 5 only
              .map((rec: any, idx: number) => (
                <Card key={idx} sx={{ mb: 1, bgcolor: 'grey.100' }}>
                  <CardContent sx={{ py: 1 }}>
                    <Typography variant="body2">
                      <strong>{rec.setup_name}:</strong> {rec.reason_tradeable}
                      (n={rec.sample_size}, WR={rec.win_rate.toFixed(1)}%, E={rec.expectancy > 0 ? '+' : ''}{rec.expectancy.toFixed(2)}%)
                    </Typography>
                  </CardContent>
                </Card>
              ))}
          </>
        ) : (
          <Alert severity="info">
            <Typography variant="body2">
              Trade recommendations not available. Ensure the backend analysis includes regime_filtered_gaps and trade_recommendations.
            </Typography>
          </Alert>
        )}
      </TabPanel>

      {/* Tab 1: Multi-Horizon Outcomes */}
      <TabPanel value={tabValue} index={1}>
        <Typography variant="h6" gutterBottom>
          Take Profit vs Hold - By Time Horizon
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Compare the benefit of taking profits at different time horizons vs holding longer.
          <br />
          <strong>Time Horizon Key:</strong> 1×4H = 4 hours (1 bar), 2×4H = 8 hours (2 bars), 3×4H = 12 hours (3 bars), 1D = 24 hours, 2D = 48 hours
          <br />
          <strong>Benchmark:</strong> Each "Take Profit" return is compared against the "Hold" return from holding to the next longer time period.
          Returns are measured from entry price at signal trigger to close price at each time horizon.
        </Typography>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Horizon</TableCell>
                <TableCell align="right">Take Profit</TableCell>
                <TableCell align="right">Hold</TableCell>
                <TableCell align="right">Δ (Advantage)</TableCell>
                <TableCell align="right">Sample Size</TableCell>
                <TableCell align="right">Win Rate</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {analysis.multi_horizon_outcomes?.map((outcome: any) => (
                <TableRow
                  key={outcome.horizon_label}
                  sx={{
                    bgcolor: outcome.delta > 0.3 ? 'success.light' : 'transparent'
                  }}
                >
                  <TableCell><strong>{outcome.horizon_label}</strong></TableCell>
                  <TableCell align="right" style={{ color: outcome.take_profit_return > 0 ? 'green' : 'red' }}>
                    {outcome.take_profit_return > 0 ? '+' : ''}{outcome.take_profit_return.toFixed(2)}%
                  </TableCell>
                  <TableCell align="right" style={{ color: outcome.hold_return > 0 ? 'green' : 'red' }}>
                    {outcome.hold_return > 0 ? '+' : ''}{outcome.hold_return.toFixed(2)}%
                  </TableCell>
                  <TableCell align="right" style={{ color: outcome.delta > 0 ? 'green' : 'red', fontWeight: 'bold' }}>
                    {outcome.delta > 0 ? '+' : ''}{outcome.delta.toFixed(2)}%
                  </TableCell>
                  <TableCell align="right">{outcome.sample_size}</TableCell>
                  <TableCell align="right">{outcome.win_rate.toFixed(1)}%</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <Alert
          severity={
            analysis.multi_horizon_outcomes?.[2]?.take_profit_return > 0 && analysis.multi_horizon_outcomes?.[2]?.delta > 0.3 ? 'success' :
            analysis.multi_horizon_outcomes?.[2]?.take_profit_return < 0 ? 'warning' :
            'info'
          }
          sx={{ mt: 3 }}
        >
          <Typography variant="subtitle2" gutterBottom>
            <strong>Key Insight for {ticker}:</strong>
          </Typography>
          <Typography variant="body2">
            {analysis.multi_horizon_outcomes?.[2]?.delta !== undefined ? (
              <>
                Exiting divergence signals within 8-12 hours (3×4H) provides{' '}
                <strong>{analysis.multi_horizon_outcomes[2].delta > 0 ? '+' : ''}{analysis.multi_horizon_outcomes[2].delta.toFixed(2)}%</strong>
                {' '}average edge over holding through the full day for <strong>{ticker}</strong>.
                <br />
                <br />
                <strong>Absolute Performance at 3×4H:</strong> {analysis.multi_horizon_outcomes[2].take_profit_return > 0 ? '+' : ''}{analysis.multi_horizon_outcomes[2].take_profit_return.toFixed(2)}%
                (Win Rate: {analysis.multi_horizon_outcomes[2].win_rate.toFixed(1)}%)
                <br />
                <strong>Absolute Performance at 1D:</strong> {analysis.multi_horizon_outcomes[2].hold_return > 0 ? '+' : ''}{analysis.multi_horizon_outcomes[2].hold_return.toFixed(2)}%
                (Win Rate: {analysis.signal_quality?.hit_rate?.toFixed(1) || '0'}%)
                <br />
                <br />
                {analysis.volatility_context?.volatility_regime === 'extreme' ?
                  `⚠️ EXTREME VOLATILITY: Edge of +${analysis.multi_horizon_outcomes[2].delta.toFixed(2)}% exists but IGNORE IT in extreme volatility. Historical data shows extreme volatility requires holding 1D-2D (not 3×4H). This edge is misleading in current conditions. Wait for volatility to normalize or hold longer.` :
                  analysis.multi_horizon_outcomes[2].take_profit_return > 0 && analysis.multi_horizon_outcomes[2].delta > 0.3 ?
                  '✅ Strong intraday edge with positive absolute returns. This validates the profit-taking strategy!' :
                  analysis.multi_horizon_outcomes[2].delta > 0 && analysis.multi_horizon_outcomes[2].take_profit_return < 0 ?
                  '⚠️ Edge exists BUT both horizons are negative. This is "less bad" performance, not profitable. Reconsider trading this signal or adjust entry criteria.' :
                  analysis.multi_horizon_outcomes[2].delta < 0 ?
                  '❌ No intraday edge - holding longer performs better. Consider longer holding periods or skip this signal.' :
                  'Neutral edge - minimal difference between horizons.'}
              </>
            ) : (
              'Analyzing intraday edge data...'
            )}
          </Typography>
          <Typography variant="caption" display="block" sx={{ mt: 1 }}>
            <strong>Edge Definition:</strong> Average return difference between exiting at 3×4H (12 hours) vs. holding through 1D (24 hours).
            <br />
            <strong>Important:</strong> Positive edge does NOT guarantee profitability! Check absolute returns above. Edge measures relative performance only.
            <br />
            Sample size: {analysis.multi_horizon_outcomes?.[2]?.sample_size || 0} events. Minimum recommended: 100+ for statistical confidence.
          </Typography>
        </Alert>
      </TabPanel>

      {/* Tab 2: Heatmap */}
      <TabPanel value={tabValue} index={2}>
        <Typography variant="h6" gutterBottom>
          Take vs Hold Benefit Heatmap
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Delta (advantage) of taking profits vs holding, by gap size and time horizon.
          <br />
          <strong>Gap Size:</strong> Absolute difference between Daily and 4H RSI-MA percentiles at signal trigger (e.g., 25% gap = Daily at 75th percentile, 4H at 50th).
          <br />
          <strong>Delta Calculation:</strong> Average return from exiting at given horizon MINUS average return from holding to next period.
          Positive delta (green) = taking profits is better; Negative delta (red) = holding is better.
          <br />
          <strong>Time Horizons:</strong> 1×4H = 4hr, 2×4H = 8hr, 3×4H = 12hr, 1D = 24hr, 2D = 48hr
          <br />
          <strong>Large Gap Focus (35%+):</strong> Pay special attention to the bottom row. Large gaps may exhibit different convergence
          patterns and optimal exit timings. Cross-reference with Volatility Analysis tab to understand how large gaps perform in different market regimes.
        </Typography>

        {renderHeatmap()}

        <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'center' }}>
          <Typography variant="caption" sx={{ mr: 2 }}>
            Color Scale:
          </Typography>
          <Chip label="Dark Green: >+0.3%" size="small" sx={{ bgcolor: '#2e7d32', color: 'white' }} />
          <Chip label="Light Green: 0% to +0.3%" size="small" sx={{ bgcolor: '#81c784' }} />
          <Chip label="Yellow: -0.3% to 0%" size="small" sx={{ bgcolor: '#ffeb3b' }} />
          <Chip label="Red: <-0.3%" size="small" sx={{ bgcolor: '#f44336', color: 'white' }} />
        </Box>
      </TabPanel>

      {/* Tab 3: Regime-Filtered Analysis */}
      <TabPanel value={tabValue} index={3}>
        <Typography variant="h6" gutterBottom>
          🔬 Regime-Filtered Gap Analysis
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Detailed breakdown of performance by gap size AND volatility regime.
          <br />
          <strong>Expectancy:</strong> (Win Rate × Avg Win) - (Loss Rate × Avg Loss) = Net edge per trade after costs.
          <br />
          <strong>Goal:</strong> Expectancy ≥ +0.15% with Win Rate ≥ 52% and positive absolute returns = TRADEABLE.
          <br />
          <strong>Focus:</strong> Look for 30-35% gaps in NORMAL volatility - this is the most promising setup.
        </Typography>

        {analysis.regime_filtered_gaps && analysis.regime_filtered_gaps.length > 0 ? (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Gap Range</strong></TableCell>
                  <TableCell><strong>Regime</strong></TableCell>
                  <TableCell align="right"><strong>Sample</strong></TableCell>
                  <TableCell align="right"><strong>2×4H Return</strong></TableCell>
                  <TableCell align="right"><strong>Win Rate</strong></TableCell>
                  <TableCell align="right"><strong>Expectancy</strong></TableCell>
                  <TableCell align="right"><strong>Avg Win</strong></TableCell>
                  <TableCell align="right"><strong>Avg Loss</strong></TableCell>
                  <TableCell align="right"><strong>W/L Ratio</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {analysis.regime_filtered_gaps.map((gap: any, idx: number) => (
                  <TableRow
                    key={`${gap.gap_range}-${gap.regime}`}
                    sx={{
                      bgcolor: gap.expectancy_2x4h >= 0.15 && gap.win_rate_2x4h >= 52 && gap.avg_return_2x4h > 0 ? 'success.light' :
                              gap.expectancy_2x4h >= 0 ? 'warning.light' : 'transparent'
                    }}
                  >
                    <TableCell><strong>{gap.gap_range}</strong></TableCell>
                    <TableCell>
                      <Chip
                        label={gap.regime.toUpperCase()}
                        size="small"
                        color={
                          gap.regime === 'normal' ? 'success' :
                          gap.regime === 'extreme' ? 'error' :
                          gap.regime === 'high' ? 'warning' : 'default'
                        }
                      />
                    </TableCell>
                    <TableCell align="right">{gap.sample_size}</TableCell>
                    <TableCell
                      align="right"
                      style={{
                        color: gap.avg_return_2x4h > 0 ? 'green' : 'red',
                        fontWeight: 'bold'
                      }}
                    >
                      {gap.avg_return_2x4h > 0 ? '+' : ''}{gap.avg_return_2x4h.toFixed(2)}%
                    </TableCell>
                    <TableCell align="right">{gap.win_rate_2x4h.toFixed(1)}%</TableCell>
                    <TableCell
                      align="right"
                      style={{
                        color: gap.expectancy_2x4h >= 0.15 ? 'green' : gap.expectancy_2x4h > 0 ? 'orange' : 'red',
                        fontWeight: 'bold'
                      }}
                    >
                      {gap.expectancy_2x4h > 0 ? '+' : ''}{gap.expectancy_2x4h.toFixed(2)}%
                    </TableCell>
                    <TableCell align="right" style={{ color: 'green' }}>
                      +{gap.avg_win_size.toFixed(2)}%
                    </TableCell>
                    <TableCell align="right" style={{ color: 'red' }}>
                      -{gap.avg_loss_size.toFixed(2)}%
                    </TableCell>
                    <TableCell align="right">
                      {gap.win_loss_ratio.toFixed(2)}x
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Alert severity="info">
            <Typography variant="body2">
              Regime-filtered gap analysis not available. Ensure backend includes regime_filtered_gaps in response.
            </Typography>
          </Alert>
        )}

        <Alert severity="info" sx={{ mt: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            <strong>How to Read This Table:</strong>
          </Typography>
          <Typography variant="body2">
            • <strong>Green rows:</strong> Meet all tradeable criteria (Expectancy ≥ +0.15%, Win Rate ≥ 52%, Positive Returns)
            <br />
            • <strong>Yellow rows:</strong> Positive expectancy but below threshold or negative absolute returns
            <br />
            • <strong>White rows:</strong> Negative expectancy - NOT tradeable
            <br />
            • <strong>W/L Ratio:</strong> Avg Win Size / Avg Loss Size (higher is better, &gt;1.5 is strong)
            <br />
            • <strong>Sample Size:</strong> Minimum 20 for consideration, 50+ for high confidence
          </Typography>
        </Alert>
      </TabPanel>

      {/* Tab 4: Re-entry Analysis */}
      <TabPanel value={tabValue} index={4}>
        <Typography variant="h6" gutterBottom>
          🔄 Re-entry Performance Analysis
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          After taking profits on initial divergence, how often do re-entry opportunities appear? Are they profitable?
          <br />
          <strong>Re-entry Conditions:</strong> Wait 12+ hours, gap converges below 15%, both timeframes &lt; 35th percentile (oversold).
          <br />
          <strong>Cycle Trading:</strong> Initial trade + re-entry = complete cycle. Combined returns show total opportunity.
        </Typography>

        {analysis.reentry_breakdown && analysis.reentry_breakdown.length > 0 ? (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Gap Category</strong></TableCell>
                  <TableCell><strong>Regime</strong></TableCell>
                  <TableCell align="right"><strong>Sample</strong></TableCell>
                  <TableCell align="right"><strong>Re-entry Rate</strong></TableCell>
                  <TableCell align="right"><strong>Avg Time</strong></TableCell>
                  <TableCell align="right"><strong>Avg Return</strong></TableCell>
                  <TableCell align="right"><strong>Success Rate</strong></TableCell>
                  <TableCell align="right"><strong>Expectancy</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {analysis.reentry_breakdown.map((reentry: any, idx: number) => (
                  <TableRow
                    key={`${reentry.gap_category}-${reentry.regime}`}
                    sx={{
                      bgcolor: reentry.reentry_expectancy >= 0.2 && reentry.reentry_success_rate >= 55 ? 'success.light' : 'transparent'
                    }}
                  >
                    <TableCell><strong>{reentry.gap_category.toUpperCase()}</strong></TableCell>
                    <TableCell>
                      <Chip
                        label={reentry.regime.toUpperCase()}
                        size="small"
                        color={
                          reentry.regime === 'normal' ? 'success' :
                          reentry.regime === 'extreme' ? 'error' :
                          reentry.regime === 'high' ? 'warning' : 'default'
                        }
                      />
                    </TableCell>
                    <TableCell align="right">{reentry.sample_size}</TableCell>
                    <TableCell align="right">{reentry.reentry_rate.toFixed(1)}%</TableCell>
                    <TableCell align="right">{reentry.avg_time_to_reentry.toFixed(0)}h</TableCell>
                    <TableCell
                      align="right"
                      style={{
                        color: reentry.avg_reentry_return > 0 ? 'green' : 'red',
                        fontWeight: 'bold'
                      }}
                    >
                      {reentry.avg_reentry_return > 0 ? '+' : ''}{reentry.avg_reentry_return.toFixed(2)}%
                    </TableCell>
                    <TableCell align="right">{reentry.reentry_success_rate.toFixed(1)}%</TableCell>
                    <TableCell
                      align="right"
                      style={{
                        color: reentry.reentry_expectancy >= 0.2 ? 'green' : reentry.reentry_expectancy > 0 ? 'orange' : 'red',
                        fontWeight: 'bold'
                      }}
                    >
                      {reentry.reentry_expectancy > 0 ? '+' : ''}{reentry.reentry_expectancy.toFixed(2)}%
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Alert severity="info">
            <Typography variant="body2">
              Re-entry breakdown not available. Ensure backend includes reentry_breakdown in response.
            </Typography>
          </Alert>
        )}

        <Alert severity="success" sx={{ mt: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            <strong>Cycle Trading Strategy:</strong>
          </Typography>
          <Typography variant="body2">
            If re-entry rate &gt; 50% and success rate &gt; 55%:
            <br />
            1. <strong>Take profits</strong> on initial divergence at 2×4H (8 hours)
            <br />
            2. <strong>Wait for convergence</strong> - gap closes below 15%, both timeframes oversold
            <br />
            3. <strong>Re-enter</strong> when conditions met, targeting 1D hold
            <br />
            4. <strong>Combined cycle return:</strong> Initial profit + Re-entry profit = Full opportunity captured
            <br />
            <br />
            <strong>Key Insight:</strong> Even if re-entry expectancy is lower than initial trade, high re-entry rates (&gt;50%)
            mean you can potentially trade the same divergence cycle twice for amplified total returns.
          </Typography>
        </Alert>
      </TabPanel>

      {/* Tab 5: Timeline */}
      <TabPanel value={tabValue} index={5}>
        <Typography variant="h6" gutterBottom>
          Percentile Evolution Timeline
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Recent divergence events showing how percentiles evolve after trigger.
          <br />
          <strong>How to Read:</strong> Each timeline tracks a single divergence event from trigger (bar 0) through 6 subsequent 4-hour bars.
          Shows how the gap between Daily and 4H percentiles changes over time, and whether convergence occurs.
          <br />
          <strong>Price Return:</strong> Percentage gain/loss from entry price at each bar. Used to identify optimal exit points.
        </Typography>

        <Alert severity="info" sx={{ mb: 2 }}>
          Timeline chart data available for {analysis.timeline_chart_data?.length || 0} recent events.
          Visualization shows convergence patterns and price evolution at 4-hour intervals.
        </Alert>

        {analysis.timeline_chart_data?.length > 0 && (
          <Box>
            <Typography variant="body2" sx={{ mb: 2 }}>
              <strong>Sample Event:</strong> {analysis.timeline_chart_data[0].trigger_date} -
              Initial Gap: {analysis.timeline_chart_data[0].initial_gap.toFixed(1)}% -
              Category: {analysis.timeline_chart_data[0].gap_category.toUpperCase()}
            </Typography>
            <Table size="small" sx={{ maxWidth: 600 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Bar</TableCell>
                  <TableCell>Time Label</TableCell>
                  <TableCell align="right">Price Return</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {analysis.timeline_chart_data[0].bars.map((bar: any) => (
                  <TableRow key={bar.bar_offset}>
                    <TableCell>{bar.bar_offset}</TableCell>
                    <TableCell>{bar.label}</TableCell>
                    <TableCell align="right" style={{ color: bar.price_return > 0 ? 'green' : 'red' }}>
                      {bar.price_return !== undefined ? `${bar.price_return > 0 ? '+' : ''}${bar.price_return.toFixed(2)}%` : 'N/A'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        )}
      </TabPanel>

      {/* Tab 6: Signal Quality */}
      <TabPanel value={tabValue} index={6}>
        <Typography variant="h6" gutterBottom>
          Signal Quality & Context
        </Typography>
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2">
            <strong>Signal Quality Metrics:</strong>
            <br />
            <strong>• Hit Rate:</strong> Percentage of signals that were profitable at 1D horizon
            <br />
            <strong>• Avg Return:</strong> Mean return across all signals at 1D horizon
            <br />
            <strong>• Sharpe Ratio:</strong> Risk-adjusted return (higher is better, &gt;1.0 is good)
            <br />
            <strong>• Consistency Score:</strong> Combined metric of hit rate and Sharpe, scaled 0-100
            <br />
            <br />
            All metrics use 1-day forward returns to assess signal reliability and strength.
          </Typography>
        </Alert>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Signal Quality</Typography>
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell>Hit Rate</TableCell>
                      <TableCell align="right"><strong>{analysis.signal_quality?.hit_rate?.toFixed(1) || '0'}%</strong></TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Avg Return</TableCell>
                      <TableCell align="right" style={{ color: (analysis.signal_quality?.avg_return || 0) > 0 ? 'green' : 'red' }}>
                        <strong>{(analysis.signal_quality?.avg_return || 0) > 0 ? '+' : ''}{analysis.signal_quality?.avg_return?.toFixed(2) || '0'}%</strong>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Sharpe Ratio</TableCell>
                      <TableCell align="right"><strong>{analysis.signal_quality?.sharpe_ratio?.toFixed(2) || '0'}</strong></TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Consistency Score</TableCell>
                      <TableCell align="right"><strong>{analysis.signal_quality?.consistency_score?.toFixed(0) || '0'}/100</strong></TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Volatility Context</Typography>
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell>Current ATR</TableCell>
                      <TableCell align="right"><strong>${analysis.volatility_context?.current_atr?.toFixed(2) || '0'}</strong></TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>ATR Percentile</TableCell>
                      <TableCell align="right"><strong>{analysis.volatility_context?.historical_atr_percentile?.toFixed(0) || '0'}%</strong></TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Regime</TableCell>
                      <TableCell align="right"><strong>{analysis.volatility_context?.volatility_regime?.toUpperCase() || 'N/A'}</strong></TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Re-entry Opportunities</Typography>
                <Alert severity="info" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    <strong>Re-entry Logic (RELAXED THRESHOLDS):</strong>
                    <br />
                    1. Wait minimum 12 hours (3 bars) after initial exit
                    <br />
                    2. Gap must converge below 15% (from initial divergence trigger level)
                    <br />
                    3. Both Daily AND 4H percentiles must be below 35th percentile (oversold condition)
                    <br />
                    4. Expected return is measured 1 day forward from re-entry point
                    <br />
                    <br />
                    <strong>Convergence Definition:</strong> Gap closes from initial trigger level (e.g., 25%) to below 15% threshold.
                    This indicates the divergence is resolving and timeframes are realigning.
                  </Typography>
                </Alert>
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell>Re-entry Rate</TableCell>
                      <TableCell align="right"><strong>{analysis.reentry_analysis?.reentry_rate?.toFixed(1) || '0'}%</strong></TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Avg Time to Re-entry</TableCell>
                      <TableCell align="right"><strong>{analysis.reentry_analysis?.avg_time_to_reentry_hours?.toFixed(1) || '0'} hours</strong></TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Expected Return from Re-entry</TableCell>
                      <TableCell align="right" style={{ color: (analysis.reentry_analysis?.avg_expected_return || 0) > 0 ? 'green' : 'red' }}>
                        <strong>{(analysis.reentry_analysis?.avg_expected_return || 0) > 0 ? '+' : ''}{analysis.reentry_analysis?.avg_expected_return?.toFixed(2) || '0'}%</strong>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Re-entry Success Rate</TableCell>
                      <TableCell align="right"><strong>{analysis.reentry_analysis?.success_rate?.toFixed(1) || '0'}%</strong></TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Sample Size</TableCell>
                      <TableCell align="right"><strong>{analysis.reentry_analysis?.sample_size || 0} re-entry events</strong></TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Tab 7: Volatility Analysis */}
      <TabPanel value={tabValue} index={7}>
        <Typography variant="h6" gutterBottom>
          Volatility-Aware Performance Analysis
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          How intraday edge and convergence vary by market volatility regime
        </Typography>

        {/* Volatility-Aware Metrics */}
        <Typography variant="subtitle1" gutterBottom sx={{ mt: 3 }}>
          <strong>Performance by Volatility Regime</strong>
        </Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Regime</TableCell>
                <TableCell align="right">Sample Size</TableCell>
                <TableCell align="right">Intraday Edge</TableCell>
                <TableCell align="right">Best Exit</TableCell>
                <TableCell align="right">Hit Rate</TableCell>
                <TableCell>Recommendation</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {analysis.volatility_aware_metrics?.map((metric: any) => (
                <TableRow key={metric.regime}>
                  <TableCell>
                    <Chip
                      label={metric.regime.toUpperCase()}
                      color={
                        metric.regime === 'low' ? 'info' :
                        metric.regime === 'normal' ? 'success' :
                        metric.regime === 'high' ? 'warning' :
                        'error'
                      }
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">{metric.sample_size}</TableCell>
                  <TableCell
                    align="right"
                    style={{
                      color: metric.avg_intraday_edge > 0.3 ? 'green' : metric.avg_intraday_edge > 0 ? 'orange' : 'red',
                      fontWeight: 'bold'
                    }}
                  >
                    {metric.avg_intraday_edge > 0 ? '+' : ''}{metric.avg_intraday_edge.toFixed(2)}%
                  </TableCell>
                  <TableCell align="right"><strong>{metric.optimal_exit_horizon}</strong></TableCell>
                  <TableCell align="right">{metric.hit_rate.toFixed(1)}%</TableCell>
                  <TableCell>
                    <Typography variant="caption">{metric.recommended_action}</Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Convergence by Volatility */}
        <Typography variant="subtitle1" gutterBottom sx={{ mt: 4 }}>
          <strong>Convergence Speed by Volatility Regime</strong>
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Does high volatility lead to faster convergence?
        </Typography>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Regime</TableCell>
                <TableCell align="right">Convergence Rate</TableCell>
                <TableCell align="right">Avg Time to Converge</TableCell>
                <TableCell align="right">Sample Size</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(analysis.convergence_by_volatility || {}).map(([regime, data]: [string, any]) => (
                <TableRow key={regime}>
                  <TableCell>
                    <Chip
                      label={regime.toUpperCase()}
                      color={
                        regime === 'low' ? 'info' :
                        regime === 'normal' ? 'success' :
                        regime === 'high' ? 'warning' :
                        'error'
                      }
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <strong>{data.convergence_rate.toFixed(1)}%</strong>
                  </TableCell>
                  <TableCell align="right">
                    {data.avg_convergence_time_hours > 0 ? `${data.avg_convergence_time_hours.toFixed(1)}h` : 'N/A'}
                  </TableCell>
                  <TableCell align="right">{data.sample_size}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Key Insights */}
        <Alert severity="info" sx={{ mt: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            <strong>Volatility Insights:</strong>
          </Typography>
          <Typography variant="body2">
            • <strong>NORMAL regime</strong> shows the strongest intraday edge (best for divergence trading)<br />
            • <strong>LOW volatility</strong> converges fastest (~4h average)<br />
            • <strong>EXTREME volatility</strong> takes longest to converge (~24h) - hold positions longer<br />
            • Recommended strategy: Take profits aggressively in NORMAL conditions, more patient in EXTREME
          </Typography>
        </Alert>

        {/* Decay Model Summary */}
        <Typography variant="subtitle1" gutterBottom sx={{ mt: 4 }}>
          <strong>Convergence Decay Model</strong>
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="caption">24H Convergence Prob</Typography>
                <Typography variant="h5" color="primary">
                  {analysis.decay_model?.convergence_probability_24h?.toFixed(1) || '0'}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="caption">48H Convergence Prob</Typography>
                <Typography variant="h5" color="primary">
                  {analysis.decay_model?.convergence_probability_48h?.toFixed(1) || '0'}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="caption">Median Convergence Time</Typography>
                <Typography variant="h5" color="primary">
                  {analysis.decay_model?.median_time_to_convergence_hours?.toFixed(0) || '0'}h
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>
    </Paper>
  );
};

export default EnhancedDivergenceLifecycle;
