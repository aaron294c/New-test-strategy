/**
 * Macro Risk Dashboard Component
 *
 * Displays comprehensive macro risk indicators:
 * - Yield Curve Analysis (10Y vs 3M)
 * - S&P 500 Breadth (% above 200 MA)
 * - MMFI (McClellan Market Facilitation Index)
 * - Composite Risk Score
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Chip,
  Alert,
  CircularProgress,
  LinearProgress,
  Tooltip,
  Paper,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Warning,
  CheckCircle,
  Error,
  ShowChart,
  Assessment,
} from '@mui/icons-material';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

interface YieldCurveMetrics {
  us_10y: number;
  us_3m: number;
  spread: number;
  is_inverted: boolean;
  inversion_severity: string;
  risk_level: string;
  historical_percentile: number;
}

interface BreadthMetrics {
  sp500_pct_above_200ma: number;
  breadth_signal: string;
  risk_level: string;
}

interface MMFIMetrics {
  mmfi_50d: number;
  mmfi_signal: string;
  risk_level: string;
}

interface CompositeRisk {
  composite_score: number;
  overall_risk_level: string;
  risk_description: string;
  component_risks: {
    yield_curve: string;
    breadth: string;
    mmfi: string;
  };
}

interface MacroRiskData {
  timestamp: string;
  yield_curve: YieldCurveMetrics;
  breadth: BreadthMetrics;
  mmfi: MMFIMetrics;
  composite_risk: CompositeRisk;
}

const getRiskColor = (riskLevel: string) => {
  switch (riskLevel) {
    case 'Low':
      return 'success';
    case 'Medium':
      return 'warning';
    case 'High':
      return 'error';
    default:
      return 'default';
  }
};

const getRiskIcon = (riskLevel: string) => {
  switch (riskLevel) {
    case 'Low':
      return <CheckCircle />;
    case 'Medium':
      return <Warning />;
    case 'High':
      return <Error />;
    default:
      return <Assessment />;
  }
};

export const MacroRiskDashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [riskData, setRiskData] = useState<MacroRiskData | null>(null);

  useEffect(() => {
    fetchRiskMetrics();
    // Refresh every 5 minutes
    const interval = setInterval(fetchRiskMetrics, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchRiskMetrics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_BASE_URL}/api/macro-risk/current`);
      setRiskData(response.data);
    } catch (err: any) {
      console.error('Error fetching macro risk metrics:', err);
      setError(err.message || 'Failed to fetch risk metrics');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !riskData) {
    return (
      <Paper elevation={3} sx={{ p: 3, textAlign: 'center' }}>
        <CircularProgress size={40} />
        <Typography sx={{ mt: 2 }}>Loading macro risk metrics...</Typography>
      </Paper>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        <Typography variant="h6">Error Loading Risk Metrics</Typography>
        <Typography>{error}</Typography>
      </Alert>
    );
  }

  if (!riskData) {
    return null;
  }

  const { yield_curve, breadth, mmfi, composite_risk } = riskData;

  return (
    <Box>
      {/* Header */}
      <Paper elevation={2} sx={{ p: 2, mb: 2, bgcolor: 'primary.dark' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Assessment /> Macro Risk Dashboard
          </Typography>
          <Chip
            icon={getRiskIcon(composite_risk.overall_risk_level)}
            label={`Overall Risk: ${composite_risk.overall_risk_level}`}
            color={getRiskColor(composite_risk.overall_risk_level)}
            size="medium"
            sx={{ fontSize: '1rem', py: 2.5 }}
          />
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {composite_risk.risk_description} | Composite Score: {composite_risk.composite_score}/3.0
        </Typography>
      </Paper>

      <Grid container spacing={2}>
        {/* Yield Curve Analysis */}
        <Grid item xs={12} md={4}>
          <Card elevation={3} sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ShowChart /> Yield Curve
                <Chip
                  label={yield_curve.risk_level}
                  color={getRiskColor(yield_curve.risk_level)}
                  size="small"
                />
              </Typography>

              <Box sx={{ mt: 2 }}>
                <Alert
                  severity={yield_curve.is_inverted ? 'error' : 'success'}
                  icon={yield_curve.is_inverted ? <Warning /> : <CheckCircle />}
                  sx={{ mb: 2 }}
                >
                  <Typography variant="body2" fontWeight="bold">
                    {yield_curve.inversion_severity}
                  </Typography>
                  {yield_curve.is_inverted && (
                    <Typography variant="caption">
                      Inverted yield curves historically precede recessions
                    </Typography>
                  )}
                </Alert>

                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        10-Year Yield
                      </Typography>
                      <Typography variant="h5" color="primary.main">
                        {yield_curve.us_10y.toFixed(2)}%
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={6}>
                    <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        3-Month Yield
                      </Typography>
                      <Typography variant="h5" color="primary.main">
                        {yield_curve.us_3m.toFixed(2)}%
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>

                <Box sx={{ mt: 2, p: 2, bgcolor: yield_curve.spread < 0 ? 'error.dark' : 'success.dark', borderRadius: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Spread (10Y - 3M)
                  </Typography>
                  <Typography variant="h4" fontWeight="bold">
                    {yield_curve.spread > 0 ? '+' : ''}{yield_curve.spread.toFixed(2)}%
                  </Typography>
                  <Typography variant="caption">
                    Historical Percentile: {yield_curve.historical_percentile.toFixed(0)}th
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* S&P 500 Breadth */}
        <Grid item xs={12} md={4}>
          <Card elevation={3} sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TrendingUp /> Market Breadth
                <Chip
                  label={breadth.risk_level}
                  color={getRiskColor(breadth.risk_level)}
                  size="small"
                />
              </Typography>

              <Box sx={{ mt: 2 }}>
                <Box sx={{ p: 3, bgcolor: 'background.default', borderRadius: 1, textAlign: 'center' }}>
                  <Typography variant="caption" color="text.secondary">
                    S&P 500 Stocks Above 200 MA
                  </Typography>
                  <Typography variant="h2" fontWeight="bold" color="primary.main">
                    {breadth.sp500_pct_above_200ma.toFixed(0)}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={breadth.sp500_pct_above_200ma}
                    sx={{ mt: 2, height: 10, borderRadius: 1 }}
                    color={breadth.sp500_pct_above_200ma > 60 ? 'success' : breadth.sp500_pct_above_200ma > 40 ? 'warning' : 'error'}
                  />
                </Box>

                <Alert
                  severity={breadth.breadth_signal === 'Bullish' ? 'success' : breadth.breadth_signal === 'Bearish' ? 'error' : 'warning'}
                  icon={breadth.breadth_signal === 'Bullish' ? <TrendingUp /> : breadth.breadth_signal === 'Bearish' ? <TrendingDown /> : <Warning />}
                  sx={{ mt: 2 }}
                >
                  <Typography variant="body2" fontWeight="bold">
                    {breadth.breadth_signal} Breadth
                  </Typography>
                  <Typography variant="caption">
                    {breadth.breadth_signal === 'Bullish' && 'Strong participation - healthy market'}
                    {breadth.breadth_signal === 'Neutral' && 'Mixed participation - selective market'}
                    {breadth.breadth_signal === 'Bearish' && 'Weak participation - deteriorating market'}
                  </Typography>
                </Alert>

                <Box sx={{ mt: 2, p: 2, bgcolor: 'info.dark', borderRadius: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Interpretation
                  </Typography>
                  <Typography variant="body2">
                    {breadth.sp500_pct_above_200ma > 70 && '📈 Strong uptrend - most stocks participating'}
                    {breadth.sp500_pct_above_200ma > 50 && breadth.sp500_pct_above_200ma <= 70 && '↗️ Moderate uptrend - average participation'}
                    {breadth.sp500_pct_above_200ma > 30 && breadth.sp500_pct_above_200ma <= 50 && '➡️ Mixed market - narrow leadership'}
                    {breadth.sp500_pct_above_200ma <= 30 && '📉 Downtrend - widespread weakness'}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* MMFI (McClellan Market Facilitation Index) */}
        <Grid item xs={12} md={4}>
          <Card elevation={3} sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Assessment /> MMFI (50-Day)
                <Chip
                  label={mmfi.risk_level}
                  color={getRiskColor(mmfi.risk_level)}
                  size="small"
                />
              </Typography>

              <Box sx={{ mt: 2 }}>
                <Box sx={{ p: 3, bgcolor: 'background.default', borderRadius: 1, textAlign: 'center' }}>
                  <Typography variant="caption" color="text.secondary">
                    Market Facilitation Index
                  </Typography>
                  <Typography
                    variant="h2"
                    fontWeight="bold"
                    color={mmfi.mmfi_50d > 5 ? 'success.main' : mmfi.mmfi_50d < -5 ? 'error.main' : 'warning.main'}
                  >
                    {mmfi.mmfi_50d > 0 ? '+' : ''}{mmfi.mmfi_50d.toFixed(1)}
                  </Typography>
                </Box>

                <Alert
                  severity={mmfi.mmfi_signal === 'Bullish' ? 'success' : mmfi.mmfi_signal === 'Bearish' ? 'error' : 'warning'}
                  icon={mmfi.mmfi_signal === 'Bullish' ? <TrendingUp /> : mmfi.mmfi_signal === 'Bearish' ? <TrendingDown /> : <Warning />}
                  sx={{ mt: 2 }}
                >
                  <Typography variant="body2" fontWeight="bold">
                    {mmfi.mmfi_signal} Signal
                  </Typography>
                  <Typography variant="caption">
                    {mmfi.mmfi_signal === 'Bullish' && 'Market advancing with declining volatility'}
                    {mmfi.mmfi_signal === 'Neutral' && 'Mixed signals - watch for confirmation'}
                    {mmfi.mmfi_signal === 'Bearish' && 'Market declining or elevated volatility'}
                  </Typography>
                </Alert>

                <Box sx={{ mt: 2, p: 2, bgcolor: 'info.dark', borderRadius: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    What is MMFI?
                  </Typography>
                  <Typography variant="body2">
                    Combines price momentum with volatility changes. Positive values suggest healthy market advance; negative values indicate stress or decline.
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Composite Risk Breakdown */}
        <Grid item xs={12}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📊 Composite Risk Analysis
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Weighted composite: Yield Curve (40%), Breadth (30%), MMFI (30%)
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={12} md={3}>
                  <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      Overall Score
                    </Typography>
                    <Typography variant="h3" fontWeight="bold" color={getRiskColor(composite_risk.overall_risk_level) + '.main'}>
                      {composite_risk.composite_score.toFixed(2)}
                    </Typography>
                    <Typography variant="caption">out of 3.0</Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} md={9}>
                  <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                    <Typography variant="caption" color="text.secondary" gutterBottom>
                      Component Risk Levels
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
                      <Chip
                        label={`Yield Curve: ${composite_risk.component_risks.yield_curve}`}
                        color={getRiskColor(composite_risk.component_risks.yield_curve)}
                        size="small"
                      />
                      <Chip
                        label={`Breadth: ${composite_risk.component_risks.breadth}`}
                        color={getRiskColor(composite_risk.component_risks.breadth)}
                        size="small"
                      />
                      <Chip
                        label={`MMFI: ${composite_risk.component_risks.mmfi}`}
                        color={getRiskColor(composite_risk.component_risks.mmfi)}
                        size="small"
                      />
                    </Box>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Last Updated */}
      <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block', textAlign: 'center' }}>
        Last updated: {new Date(riskData.timestamp).toLocaleString()}
      </Typography>
    </Box>
  );
};

export default MacroRiskDashboard;
