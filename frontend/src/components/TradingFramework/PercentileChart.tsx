import React from 'react';
import { Paper, Typography, Box, Tooltip } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { TrendingUp } from '@mui/icons-material';

interface PercentileData {
  value: number;
  percentile: number;
  lookbackPeriod: number;
  timeframe: string;
}

interface PercentileEntry {
  instrument: string;
  currentPrice: number;
  percentileLevel: PercentileData;
  entryThreshold: number;
  direction: 'long' | 'short';
  timestamp: string;
}

interface PercentileChartProps {
  entries: PercentileEntry[];
  historicalData?: Array<{ timestamp: string; percentile: number; price: number }>;
}

const PercentileChart: React.FC<PercentileChartProps> = ({ entries, historicalData }) => {
  const latestEntry = entries.length > 0 ? entries[entries.length - 1] : null;

  // Generate sample historical data if not provided
  const chartData = historicalData || Array.from({ length: 50 }, (_, i) => ({
    timestamp: new Date(Date.now() - (50 - i) * 60000).toLocaleTimeString(),
    percentile: 30 + Math.random() * 60,
    price: 100 + Math.random() * 20,
  }));

  if (latestEntry) {
    chartData.push({
      timestamp: new Date(latestEntry.timestamp).toLocaleTimeString(),
      percentile: latestEntry.percentileLevel.percentile,
      price: latestEntry.currentPrice,
    });
  }

  return (
    <Paper elevation={3} sx={{ p: 3, height: '100%' }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <TrendingUp />
        Percentile-Based Entry Logic
      </Typography>

      {latestEntry && (
        <Box sx={{ mb: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 2 }}>
            <Box>
              <Typography variant="caption" color="text.secondary">Instrument</Typography>
              <Typography variant="body1" fontWeight="bold">{latestEntry.instrument}</Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Current Percentile</Typography>
              <Typography variant="body1" fontWeight="bold" color={latestEntry.percentileLevel.percentile > 85 ? 'success.main' : 'text.primary'}>
                {latestEntry.percentileLevel.percentile.toFixed(1)}%
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Direction</Typography>
              <Typography variant="body1" fontWeight="bold" color={latestEntry.direction === 'long' ? 'success.main' : 'error.main'}>
                {latestEntry.direction.toUpperCase()}
              </Typography>
            </Box>
          </Box>
        </Box>
      )}

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="timestamp"
            stroke="#9CA3AF"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => value.split(':').slice(0, 2).join(':')}
          />
          <YAxis
            yAxisId="left"
            stroke="#9CA3AF"
            label={{ value: 'Percentile', angle: -90, position: 'insideLeft' }}
            domain={[0, 100]}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            stroke="#9CA3AF"
            label={{ value: 'Price', angle: 90, position: 'insideRight' }}
          />
          <RechartsTooltip
            contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
            labelStyle={{ color: '#F3F4F6' }}
          />
          <Legend />
          <ReferenceLine yAxisId="left" y={95} stroke="#10B981" strokeDasharray="5 5" label="Entry Zone" />
          <ReferenceLine yAxisId="left" y={85} stroke="#FBBF24" strokeDasharray="5 5" label="Watch Zone" />
          <Line yAxisId="left" type="monotone" dataKey="percentile" stroke="#3B82F6" strokeWidth={2} dot={false} name="Percentile" />
          <Line yAxisId="right" type="monotone" dataKey="price" stroke="#10B981" strokeWidth={2} dot={false} name="Price" />
        </LineChart>
      </ResponsiveContainer>

      <Box sx={{ mt: 2, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 2 }}>
        <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'success.dark', borderRadius: 1, opacity: 0.8 }}>
          <Typography variant="caption">Entry Zone</Typography>
          <Typography variant="body2" fontWeight="bold">&gt; 95%</Typography>
        </Box>
        <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'warning.dark', borderRadius: 1, opacity: 0.8 }}>
          <Typography variant="caption">Watch Zone</Typography>
          <Typography variant="body2" fontWeight="bold">85-95%</Typography>
        </Box>
        <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'grey.700', borderRadius: 1, opacity: 0.8 }}>
          <Typography variant="caption">Neutral</Typography>
          <Typography variant="body2" fontWeight="bold">&lt; 85%</Typography>
        </Box>
      </Box>
    </Paper>
  );
};

export default PercentileChart;
