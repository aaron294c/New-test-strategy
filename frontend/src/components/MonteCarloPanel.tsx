/**
 * Monte Carlo Simulation Panel
 * Forward-looking probability analysis for RSI-MA percentile movements
 * 
 * Features:
 * - First Passage Time analysis (probability of reaching target percentiles)
 * - First Hit Rate (upside vs downside probability)
 * - Directional Bias indicator
 * - Fan Chart with confidence bands
 * - Exit timing optimization
 */

import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import {
  Paper,
  Typography,
  Box,
  Grid,
  Chip,
  Card,
  CardContent,
  LinearProgress,
  Alert,
  AlertTitle,
} from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat';
import TimelineIcon from '@mui/icons-material/Timeline';
import type { MonteCarloResults } from '@/types';

interface MonteCarloPanelProps {
  data: MonteCarloResults | null;
  ticker: string;
  isLoading?: boolean;
}

const MonteCarloPanel: React.FC<MonteCarloPanelProps> = ({ data, ticker, isLoading }) => {
  // Calculate First Hit Rate (upside vs downside)
  const firstHitAnalysis = useMemo(() => {
    if (!data || !data.first_passage_times) return null;

    const currentPercentile = data.current_percentile;
    const fpt = data.first_passage_times;

    // Find upside and downside targets
    const upsideTargets = Object.entries(fpt)
      .filter(([key]) => parseFloat(key) > currentPercentile)
      .map(([key, val]) => ({ percentile: parseFloat(key), ...val }));

    const downsideTargets = Object.entries(fpt)
      .filter(([key]) => parseFloat(key) < currentPercentile)
      .map(([key, val]) => ({ percentile: parseFloat(key), ...val }));

    // Calculate average probabilities
    const upsideProbability = upsideTargets.length > 0
      ? upsideTargets.reduce((sum, t) => sum + t.probability, 0) / upsideTargets.length
      : 0;

    const downsideProbability = downsideTargets.length > 0
      ? downsideTargets.reduce((sum, t) => sum + t.probability, 0) / downsideTargets.length
      : 0;

    // Directional bias
    const totalProb = upsideProbability + downsideProbability;
    const normalizedUpside = totalProb > 0 ? (upsideProbability / totalProb) * 100 : 50;
    const normalizedDownside = totalProb > 0 ? (downsideProbability / totalProb) * 100 : 50;

    const bias = normalizedUpside > 55 ? 'bullish' : normalizedDownside > 55 ? 'bearish' : 'neutral';
    const biasStrength = Math.abs(normalizedUpside - normalizedDownside);

    return {
      upsideProbability: normalizedUpside,
      downsideProbability: normalizedDownside,
      bias,
      biasStrength,
      upsideTargets,
      downsideTargets,
    };
  }, [data]);

  // Fan Chart data
  const fanChartData = useMemo(() => {
    if (!data || !data.fan_chart) return [];

    const { days, median, bands } = data.fan_chart;
    const traces: any[] = [];

    // Add confidence bands (from widest to narrowest for proper layering)
    const confidenceLevels = [95, 68, 50];
    const colors = [
      'rgba(99, 102, 241, 0.15)',  // 95% - very light indigo
      'rgba(99, 102, 241, 0.25)',  // 68% - light indigo
      'rgba(99, 102, 241, 0.35)',  // 50% - medium indigo
    ];

    confidenceLevels.forEach((ci, idx) => {
      if (bands[ci]) {
        // Upper bound
        traces.push({
          x: days,
          y: bands[ci].upper,
          mode: 'lines',
          name: `${ci}% CI Upper`,
          line: { width: 0 },
          showlegend: false,
          hoverinfo: 'skip',
          type: 'scatter',
        });

        // Lower bound with fill
        traces.push({
          x: days,
          y: bands[ci].lower,
          mode: 'lines',
          name: `${ci}% Confidence`,
          fill: 'tonexty',
          fillcolor: colors[idx],
          line: { width: 0 },
          showlegend: true,
          hovertemplate: `<b>Day %{x}</b><br>${ci}% CI: %{y:.1f}<extra></extra>`,
          type: 'scatter',
        });
      }
    });

    // Median line
    traces.push({
      x: days,
      y: median,
      mode: 'lines',
      name: 'Median Forecast',
      line: {
        color: 'rgb(99, 102, 241)',
        width: 3,
      },
      hovertemplate: '<b>Day %{x}</b><br>Median: %{y:.1f}%<extra></extra>',
      type: 'scatter',
    });

    // Current percentile marker
    traces.push({
      x: [0],
      y: [data.current_percentile],
      mode: 'markers',
      name: 'Current Position',
      marker: {
        size: 12,
        color: 'rgb(239, 68, 68)',
        symbol: 'diamond',
        line: { color: 'white', width: 2 },
      },
      hovertemplate: '<b>Current</b><br>Percentile: %{y:.1f}%<extra></extra>',
      type: 'scatter',
    });

    // Add target percentile lines
    const targets = [5, 15, 25, 50, 75, 85, 95];
    targets.forEach((target) => {
      const isAbove = target > data.current_percentile;
      const color = target <= 15 ? 'rgba(16, 185, 129, 0.5)' :
                   target >= 85 ? 'rgba(220, 53, 69, 0.5)' :
                   'rgba(108, 117, 125, 0.4)';

      traces.push({
        x: [days[0], days[days.length - 1]],
        y: [target, target],
        mode: 'lines',
        name: `${target}th %ile`,
        line: {
          color,
          width: 1,
          dash: 'dash',
        },
        showlegend: false,
        hovertemplate: `<b>${target}th Percentile</b><extra></extra>`,
        type: 'scatter',
      });
    });

    return traces;
  }, [data]);

  // First Passage Time table data
  const firstPassageData = useMemo(() => {
    if (!data || !data.first_passage_times) return [];

    return Object.entries(data.first_passage_times)
      .map(([key, val]) => ({
        percentile: parseFloat(key),
        ...val,
      }))
      .sort((a, b) => a.percentile - b.percentile);
  }, [data]);

  if (isLoading) {
    return (
      <Paper sx={{ p: 3, minHeight: 600 }}>
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <TimelineIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Running Monte Carlo Simulation...
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Simulating 1000+ price paths for forward-looking probability analysis
          </Typography>
          <LinearProgress sx={{ maxWidth: 400, mx: 'auto' }} />
        </Box>
      </Paper>
    );
  }

  if (!data) {
    return (
      <Paper sx={{ p: 3 }}>
        <Alert severity="info">
          <AlertTitle>Monte Carlo Simulation Unavailable</AlertTitle>
          Select a ticker and threshold to view forward-looking probability analysis.
        </Alert>
      </Paper>
    );
  }

  const { bias, biasStrength, upsideProbability, downsideProbability } = firstHitAnalysis || {
    bias: 'neutral',
    biasStrength: 0,
    upsideProbability: 50,
    downsideProbability: 50,
  };

  const BiasIcon = bias === 'bullish' ? TrendingUpIcon : bias === 'bearish' ? TrendingDownIcon : TrendingFlatIcon;
  const biasColor = bias === 'bullish' ? '#10b981' : bias === 'bearish' ? '#dc3545' : '#6c757d';

  return (
    <Box>
      {/* Header Section */}
      <Paper sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <TimelineIcon sx={{ fontSize: 40, color: 'white' }} />
              <Box>
                <Typography variant="h5" sx={{ color: 'white', fontWeight: 700 }}>
                  Monte Carlo Simulation
                </Typography>
                <Typography variant="subtitle2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                  {ticker} • Forward-Looking Probability Analysis
                </Typography>
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box sx={{ textAlign: { xs: 'left', md: 'right' } }}>
              <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                Current Position
              </Typography>
              <Typography variant="h4" sx={{ color: 'white', fontWeight: 700 }}>
                {data.current_percentile.toFixed(1)}th Percentile
              </Typography>
              <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                RSI-MA: {data.parameters.current_price?.toFixed(2) || 'N/A'}
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Directional Bias Card */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ 
            background: `linear-gradient(135deg, ${biasColor}22 0%, ${biasColor}11 100%)`,
            border: `2px solid ${biasColor}`,
            height: '100%',
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <BiasIcon sx={{ fontSize: 32, color: biasColor }} />
                <Typography variant="h6" sx={{ fontWeight: 700, textTransform: 'uppercase' }}>
                  Directional Bias
                </Typography>
              </Box>
              <Typography variant="h3" sx={{ color: biasColor, fontWeight: 700, mb: 1 }}>
                {bias === 'bullish' ? '↑' : bias === 'bearish' ? '↓' : '↔'} {bias.toUpperCase()}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Bias Strength: <strong>{biasStrength.toFixed(1)}%</strong>
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Typography variant="caption" color="text.secondary">Probability Breakdown</Typography>
                <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                  <Chip
                    icon={<TrendingUpIcon />}
                    label={`Upside ${upsideProbability.toFixed(0)}%`}
                    sx={{ backgroundColor: '#10b981', color: 'white', fontWeight: 600 }}
                  />
                  <Chip
                    icon={<TrendingDownIcon />}
                    label={`Downside ${downsideProbability.toFixed(0)}%`}
                    sx={{ backgroundColor: '#dc3545', color: 'white', fontWeight: 600 }}
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', background: 'linear-gradient(135deg, #10b98122 0%, #10b98111 100%)' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 700 }}>
                📈 Upside Probability
              </Typography>
              <Typography variant="h3" sx={{ color: '#10b981', fontWeight: 700, mb: 1 }}>
                {upsideProbability.toFixed(1)}%
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Probability of reaching higher percentiles
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={upsideProbability} 
                sx={{ 
                  height: 8, 
                  borderRadius: 4,
                  backgroundColor: 'rgba(16, 185, 129, 0.2)',
                  '& .MuiLinearProgress-bar': { backgroundColor: '#10b981' }
                }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', background: 'linear-gradient(135deg, #dc354522 0%, #dc354511 100%)' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 700 }}>
                📉 Downside Probability
              </Typography>
              <Typography variant="h3" sx={{ color: '#dc3545', fontWeight: 700, mb: 1 }}>
                {downsideProbability.toFixed(1)}%
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Probability of reaching lower percentiles
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={downsideProbability} 
                sx={{ 
                  height: 8, 
                  borderRadius: 4,
                  backgroundColor: 'rgba(220, 53, 69, 0.2)',
                  '& .MuiLinearProgress-bar': { backgroundColor: '#dc3545' }
                }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Fan Chart */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 700 }}>
          📊 Percentile Movement Fan Chart (21-Day Forecast)
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Confidence bands showing probable paths for RSI-MA percentile rank over the next 21 trading days
        </Typography>
        <Plot
          data={fanChartData}
          layout={{
            autosize: true,
            height: 500,
            margin: { l: 70, r: 50, t: 20, b: 70 },
            xaxis: {
              title: { 
                text: 'Days Ahead',
                font: { size: 14, color: 'rgba(255, 255, 255, 0.9)' }
              },
              gridcolor: 'rgba(255, 255, 255, 0.1)',
              showgrid: true,
              color: 'rgba(255, 255, 255, 0.8)',
              range: [0, 21],
            },
            yaxis: {
              title: { 
                text: 'Percentile Rank (%)',
                font: { size: 14, color: 'rgba(255, 255, 255, 0.9)' }
              },
              gridcolor: 'rgba(255, 255, 255, 0.1)',
              showgrid: true,
              range: [0, 100],
              color: 'rgba(255, 255, 255, 0.8)',
            },
            hovermode: 'x unified',
            showlegend: true,
            legend: {
              x: 0.01,
              y: 0.99,
              bgcolor: 'rgba(0, 0, 0, 0.8)',
              bordercolor: 'rgba(255, 255, 255, 0.3)',
              borderwidth: 1,
              font: { size: 11, color: 'rgba(255, 255, 255, 0.9)' },
            },
            plot_bgcolor: 'rgba(10, 10, 10, 0.95)',
            paper_bgcolor: 'rgba(0, 0, 0, 0)',
            font: { color: 'rgba(255, 255, 255, 0.9)', size: 12 },
          }}
          config={{
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
          }}
          style={{ width: '100%' }}
        />
      </Paper>

      {/* First Passage Time Analysis */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 700 }}>
          ⏱️ First Passage Time Analysis
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Expected time (in days) to reach each percentile threshold for the first time
        </Typography>

        <Grid container spacing={2}>
          {firstPassageData.map((fpt) => {
            const isUpside = fpt.percentile > data.current_percentile;
            const isCritical = fpt.percentile <= 15 || fpt.percentile >= 85;
            const bgColor = fpt.percentile <= 15 ? 'rgba(16, 185, 129, 0.1)' :
                           fpt.percentile >= 85 ? 'rgba(220, 53, 69, 0.1)' :
                           'rgba(108, 117, 125, 0.05)';
            const borderColor = fpt.percentile <= 15 ? '#10b981' :
                               fpt.percentile >= 85 ? '#dc3545' :
                               '#6c757d';

            return (
              <Grid item xs={12} sm={6} md={4} key={fpt.percentile}>
                <Card 
                  sx={{ 
                    backgroundColor: bgColor,
                    border: `1px solid ${borderColor}`,
                    ...(isCritical && { borderWidth: 2 }),
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="h6" sx={{ fontWeight: 700 }}>
                        {fpt.percentile}th %ile
                      </Typography>
                      <Chip
                        label={`${fpt.probability.toFixed(0)}%`}
                        size="small"
                        sx={{
                          backgroundColor: borderColor,
                          color: 'white',
                          fontWeight: 600,
                        }}
                      />
                    </Box>
                    <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
                      {fpt.median_days.toFixed(1)} days
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Median time to reach
                    </Typography>
                    <Box sx={{ mt: 1, pt: 1, borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                      <Typography variant="caption" color="text.secondary">
                        Range: {fpt.p25_days.toFixed(1)} - {fpt.p75_days.toFixed(1)} days (25th-75th %ile)
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      </Paper>

      {/* Simulation Parameters */}
      <Paper sx={{ p: 2, mt: 3, backgroundColor: 'rgba(0, 0, 0, 0.2)' }}>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
          <strong>Simulation Parameters:</strong>
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Typography variant="caption" color="text.secondary">Simulations</Typography>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {data.parameters.num_simulations.toLocaleString()}
            </Typography>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Typography variant="caption" color="text.secondary">Drift (Daily)</Typography>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {(data.parameters.drift * 100).toFixed(4)}%
            </Typography>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Typography variant="caption" color="text.secondary">Volatility (Daily)</Typography>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {(data.parameters.volatility * 100).toFixed(2)}%
            </Typography>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Typography variant="caption" color="text.secondary">Forecast Period</Typography>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {data.parameters.max_periods} days
            </Typography>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default MonteCarloPanel;
