import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  AppBar,
  Toolbar,
  IconButton,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Refresh, Settings, Notifications } from '@mui/icons-material';
import RegimeIndicator from './RegimeIndicator';
import PercentileChart from './PercentileChart';
import ExpectancyDashboard from './ExpectancyDashboard';
import InstrumentRanking from './InstrumentRanking';
import PositionMonitor from './PositionMonitor';

// Sample data generator for demonstration
const generateSampleData = () => {
  const instruments = ['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'TSLA', 'NFLX', 'GLD', 'SLV'];
  const timeframes = ['1m', '5m', '15m', '1h', '4h', '1d'];

  // Multi-timeframe regime
  const multiTimeframeRegime = {
    regimes: timeframes.slice(0, 4).map(tf => ({
      type: Math.random() > 0.5 ? 'momentum' : 'mean_reversion' as any,
      confidence: 0.6 + Math.random() * 0.3,
      strength: -0.5 + Math.random(),
      timeframe: tf,
      timestamp: new Date().toISOString(),
      metrics: {
        trendStrength: Math.random(),
        volatilityRatio: 0.8 + Math.random() * 0.4,
        meanReversionSpeed: Math.random(),
        momentumPersistence: Math.random(),
      },
    })),
    coherence: 0.5 + Math.random() * 0.4,
    dominantRegime: Math.random() > 0.5 ? 'momentum' : 'mean_reversion',
    timestamp: new Date().toISOString(),
  };

  // Percentile entries
  const percentileEntries = instruments.slice(0, 3).map(inst => ({
    instrument: inst,
    currentPrice: 100 + Math.random() * 50,
    percentileLevel: {
      value: 100 + Math.random() * 50,
      percentile: 70 + Math.random() * 25,
      lookbackPeriod: 100,
      timeframe: '4h',
    },
    entryThreshold: 95,
    direction: Math.random() > 0.5 ? 'long' : 'short' as any,
    timestamp: new Date().toISOString(),
  }));

  // Risk-adjusted expectancy
  const expectancy = {
    baseExpectancy: 0.1 + Math.random() * 0.2,
    volatilityAdjustment: -0.05 + Math.random() * 0.1,
    regimeAdjustment: -0.02 + Math.random() * 0.08,
    finalExpectancy: 0.08 + Math.random() * 0.15,
    confidence: 0.7 + Math.random() * 0.25,
    instrument: 'NVDA',
    timestamp: new Date().toISOString(),
  };

  const riskMetrics = {
    winRate: 0.55 + Math.random() * 0.15,
    avgWin: 100 + Math.random() * 150,
    avgLoss: 50 + Math.random() * 75,
    winLossRatio: 1.5 + Math.random() * 0.5,
    expectancy: 0.08 + Math.random() * 0.15,
    sharpeRatio: 1.2 + Math.random() * 0.8,
    maxDrawdown: 0.1 + Math.random() * 0.15,
    sampleSize: 50 + Math.floor(Math.random() * 100),
  };

  // Composite scores
  const compositeScores = instruments.map((inst, idx) => ({
    instrument: inst,
    totalScore: 0.3 + Math.random() * 0.6,
    factors: [
      { name: 'Trend Strength', value: Math.random(), weight: 0.25, category: 'technical' as const },
      { name: 'Volatility', value: Math.random(), weight: 0.15, category: 'risk' as const },
      { name: 'Regime Alignment', value: Math.random(), weight: 0.2, category: 'regime' as const },
      { name: 'Expectancy', value: Math.random(), weight: 0.25, category: 'risk' as const },
      { name: 'Momentum', value: Math.random(), weight: 0.15, category: 'technical' as const },
    ],
    rank: idx + 1,
    percentile: 100 - (idx * 12.5),
    timestamp: new Date().toISOString(),
  })).sort((a, b) => b.totalScore - a.totalScore);

  // Positions
  const positions = instruments.slice(0, 3).map((inst, idx) => ({
    instrument: inst,
    direction: idx % 2 === 0 ? 'long' : 'short' as any,
    entryPrice: 100 + Math.random() * 50,
    currentPrice: 100 + Math.random() * 55,
    quantity: 10 + Math.floor(Math.random() * 90),
    positionValue: (100 + Math.random() * 55) * (10 + Math.floor(Math.random() * 90)),
    unrealizedPnL: -500 + Math.random() * 1500,
    riskAmount: 200 + Math.random() * 300,
    stopLoss: {
      initialStop: 95 + Math.random() * 5,
      currentStop: 96 + Math.random() * 4,
      riskAmount: 200 + Math.random() * 300,
      updateReason: 'Trailing stop adjustment',
      timestamp: new Date().toISOString(),
    },
    openedAt: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
    timeframe: timeframes[Math.floor(Math.random() * timeframes.length)],
  }));

  return {
    multiTimeframeRegime,
    percentileEntries,
    expectancy,
    riskMetrics,
    compositeScores,
    positions,
    totalCapital: 100000,
  };
};

const TradingFrameworkDashboard: React.FC = () => {
  const [data, setData] = useState(generateSampleData());
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  const refreshData = () => {
    setLoading(true);
    setTimeout(() => {
      setData(generateSampleData());
      setLastUpdate(new Date());
      setLoading(false);
    }, 500);
  };

  useEffect(() => {
    const interval = setInterval(() => {
      refreshData();
    }, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, []);

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar position="sticky" elevation={1}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
            Multi-Timeframe Trading Framework Dashboard
          </Typography>

          <Chip
            label={`${data.positions.length} Active Positions`}
            color="primary"
            size="small"
            sx={{ mr: 2 }}
          />

          <Chip
            label={`Regime: ${data.multiTimeframeRegime.dominantRegime.toUpperCase()}`}
            color={data.multiTimeframeRegime.dominantRegime === 'momentum' ? 'success' : 'warning'}
            size="small"
            sx={{ mr: 2 }}
          />

          <IconButton color="inherit" onClick={refreshData} disabled={loading}>
            {loading ? <CircularProgress size={24} color="inherit" /> : <Refresh />}
          </IconButton>

          <IconButton color="inherit">
            <Notifications />
          </IconButton>

          <IconButton color="inherit">
            <Settings />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Container maxWidth={false} sx={{ mt: 3, mb: 3 }}>
        <Alert severity="info" sx={{ mb: 3 }}>
          This dashboard visualizes the principle-led multi-timeframe trading framework with regime awareness,
          percentile-based entry logic, risk-adjusted expectancy, and dynamic capital allocation.
          Data updates automatically every 5 seconds.
          <Typography variant="caption" display="block" sx={{ mt: 1 }}>
            Last Update: {lastUpdate.toLocaleTimeString()}
          </Typography>
        </Alert>

        <Grid container spacing={3}>
          {/* Row 1: Regime and Percentile */}
          <Grid item xs={12} md={4}>
            <RegimeIndicator regime={data.multiTimeframeRegime} />
          </Grid>
          <Grid item xs={12} md={8}>
            <PercentileChart entries={data.percentileEntries} />
          </Grid>

          {/* Row 2: Expectancy */}
          <Grid item xs={12}>
            <ExpectancyDashboard expectancy={data.expectancy} metrics={data.riskMetrics} />
          </Grid>

          {/* Row 3: Rankings */}
          <Grid item xs={12}>
            <InstrumentRanking scores={data.compositeScores} />
          </Grid>

          {/* Row 4: Positions */}
          <Grid item xs={12}>
            <PositionMonitor positions={data.positions} totalCapital={data.totalCapital} />
          </Grid>

          {/* Framework Metrics Summary */}
          <Grid item xs={12}>
            <Paper elevation={3} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Framework Performance Metrics
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'primary.dark', borderRadius: 1 }}>
                    <Typography variant="caption">Total Capital</Typography>
                    <Typography variant="h5" fontWeight="bold">
                      ${data.totalCapital.toLocaleString()}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'success.dark', borderRadius: 1 }}>
                    <Typography variant="caption">Win Rate</Typography>
                    <Typography variant="h5" fontWeight="bold">
                      {(data.riskMetrics.winRate * 100).toFixed(1)}%
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'info.dark', borderRadius: 1 }}>
                    <Typography variant="caption">Sharpe Ratio</Typography>
                    <Typography variant="h5" fontWeight="bold">
                      {data.riskMetrics.sharpeRatio?.toFixed(2)}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'warning.dark', borderRadius: 1 }}>
                    <Typography variant="caption">Regime Coherence</Typography>
                    <Typography variant="h5" fontWeight="bold">
                      {(data.multiTimeframeRegime.coherence * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

export default TradingFrameworkDashboard;
