import React from 'react';
import { Paper, Typography, Box, Grid, Chip } from '@mui/material';
import { Assessment, TrendingUp, TrendingDown, PieChart } from '@mui/icons-material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface RiskAdjustedExpectancy {
  baseExpectancy: number;
  volatilityAdjustment: number;
  regimeAdjustment: number;
  finalExpectancy: number;
  confidence: number;
  instrument: string;
  timestamp: string;
}

interface RiskMetrics {
  winRate: number;
  avgWin: number;
  avgLoss: number;
  winLossRatio: number;
  expectancy: number;
  sharpeRatio?: number;
  maxDrawdown?: number;
  sampleSize: number;
}

interface ExpectancyDashboardProps {
  expectancy: RiskAdjustedExpectancy;
  metrics: RiskMetrics;
}

const ExpectancyDashboard: React.FC<ExpectancyDashboardProps> = ({ expectancy, metrics }) => {
  const expectancyData = [
    { name: 'Base', value: expectancy.baseExpectancy, fill: '#3B82F6' },
    { name: 'Vol Adj', value: expectancy.volatilityAdjustment, fill: '#FBBF24' },
    { name: 'Regime', value: expectancy.regimeAdjustment, fill: '#10B981' },
    { name: 'Final', value: expectancy.finalExpectancy, fill: expectancy.finalExpectancy > 0 ? '#10B981' : '#EF4444' },
  ];

  const getExpectancyColor = (value: number) => {
    if (value > 0.5) return 'success';
    if (value > 0) return 'warning';
    return 'error';
  };

  return (
    <Paper elevation={3} sx={{ p: 3, height: '100%' }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Assessment />
        Risk-Adjusted Expectancy
      </Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6}>
          <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
            <Typography variant="caption" color="text.secondary">Final Expectancy</Typography>
            <Typography variant="h4" color={getExpectancyColor(expectancy.finalExpectancy) + '.main'} fontWeight="bold">
              {(expectancy.finalExpectancy * 100).toFixed(2)}%
            </Typography>
            <Box sx={{ mt: 1 }}>
              <Chip
                label={`Confidence: ${(expectancy.confidence * 100).toFixed(0)}%`}
                size="small"
                color={expectancy.confidence > 0.7 ? 'success' : 'warning'}
              />
            </Box>
          </Box>
        </Grid>
        <Grid item xs={6}>
          <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
            <Typography variant="caption" color="text.secondary">Win Rate</Typography>
            <Typography variant="h4" color="primary.main" fontWeight="bold">
              {(metrics.winRate * 100).toFixed(1)}%
            </Typography>
            <Typography variant="caption" color="text.secondary">
              W/L Ratio: {metrics.winLossRatio.toFixed(2)}
            </Typography>
          </Box>
        </Grid>
      </Grid>

      <Typography variant="subtitle2" gutterBottom>
        Expectancy Breakdown
      </Typography>

      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={expectancyData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="name" stroke="#9CA3AF" tick={{ fontSize: 12 }} />
          <YAxis stroke="#9CA3AF" />
          <Tooltip
            contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
            labelStyle={{ color: '#F3F4F6' }}
          />
          <Bar dataKey="value" radius={[8, 8, 0, 0]}>
            {expectancyData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <Box sx={{ mt: 3, display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2 }}>
        <Box sx={{ p: 1.5, border: 1, borderColor: 'success.main', borderRadius: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
            <TrendingUp fontSize="small" color="success" />
            <Typography variant="caption" color="text.secondary">Avg Win</Typography>
          </Box>
          <Typography variant="h6" color="success.main">
            ${metrics.avgWin.toFixed(2)}
          </Typography>
        </Box>

        <Box sx={{ p: 1.5, border: 1, borderColor: 'error.main', borderRadius: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
            <TrendingDown fontSize="small" color="error" />
            <Typography variant="caption" color="text.secondary">Avg Loss</Typography>
          </Box>
          <Typography variant="h6" color="error.main">
            ${metrics.avgLoss.toFixed(2)}
          </Typography>
        </Box>

        {metrics.sharpeRatio && (
          <Box sx={{ p: 1.5, border: 1, borderColor: 'info.main', borderRadius: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <PieChart fontSize="small" color="info" />
              <Typography variant="caption" color="text.secondary">Sharpe Ratio</Typography>
            </Box>
            <Typography variant="h6" color="info.main">
              {metrics.sharpeRatio.toFixed(2)}
            </Typography>
          </Box>
        )}

        <Box sx={{ p: 1.5, border: 1, borderColor: 'grey.500', borderRadius: 1 }}>
          <Typography variant="caption" color="text.secondary">Sample Size</Typography>
          <Typography variant="h6" color="text.primary">
            {metrics.sampleSize} trades
          </Typography>
        </Box>
      </Box>

      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2, textAlign: 'center' }}>
        Instrument: {expectancy.instrument} | Updated: {new Date(expectancy.timestamp).toLocaleTimeString()}
      </Typography>
    </Paper>
  );
};

export default ExpectancyDashboard;
