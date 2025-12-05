import React from 'react';
import { Box, Paper, Typography, Chip, LinearProgress } from '@mui/material';
import { TrendingUp, TrendingDown, Remove, Autorenew } from '@mui/icons-material';

interface RegimeSignal {
  type: 'momentum' | 'mean_reversion' | 'neutral' | 'transition';
  confidence: number;
  strength: number;
  timeframe: string;
  timestamp: string;
  metrics: {
    trendStrength?: number;
    volatilityRatio?: number;
    meanReversionSpeed?: number;
    momentumPersistence?: number;
  };
}

interface MultiTimeframeRegime {
  regimes: RegimeSignal[];
  coherence: number;
  dominantRegime: string;
  timestamp: string;
}

interface RegimeIndicatorProps {
  regime: MultiTimeframeRegime;
}

const RegimeIndicator: React.FC<RegimeIndicatorProps> = ({ regime }) => {
  const getRegimeIcon = (type: string) => {
    switch (type) {
      case 'momentum':
        return <TrendingUp />;
      case 'mean_reversion':
        return <TrendingDown />;
      case 'transition':
        return <Autorenew />;
      default:
        return <Remove />;
    }
  };

  const getRegimeColor = (type: string) => {
    switch (type) {
      case 'momentum':
        return 'success';
      case 'mean_reversion':
        return 'warning';
      case 'transition':
        return 'info';
      default:
        return 'default';
    }
  };

  const coherenceColor = regime.coherence > 0.7 ? 'success' : regime.coherence > 0.4 ? 'warning' : 'error';

  return (
    <Paper elevation={3} sx={{ p: 3, height: '100%' }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {getRegimeIcon(regime.dominantRegime)}
        Market Regime Detection
      </Typography>

      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="body2">Dominant Regime:</Typography>
          <Chip
            label={regime.dominantRegime.replace('_', ' ').toUpperCase()}
            color={getRegimeColor(regime.dominantRegime) as any}
            size="small"
          />
        </Box>

        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="caption">Coherence Score</Typography>
            <Typography variant="caption" fontWeight="bold">
              {(regime.coherence * 100).toFixed(1)}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={regime.coherence * 100}
            color={coherenceColor}
            sx={{ height: 8, borderRadius: 1 }}
          />
        </Box>
      </Box>

      <Typography variant="subtitle2" gutterBottom>
        Multi-Timeframe Analysis
      </Typography>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {regime.regimes.map((signal, index) => (
          <Box key={index} sx={{ borderLeft: 3, borderColor: `${getRegimeColor(signal.type)}.main`, pl: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="caption" fontWeight="bold">
                {signal.timeframe}
              </Typography>
              <Chip
                label={signal.type.replace('_', ' ')}
                size="small"
                color={getRegimeColor(signal.type) as any}
                sx={{ height: 20, fontSize: '0.7rem' }}
              />
            </Box>

            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, mb: 1 }}>
              <Box>
                <Typography variant="caption" color="text.secondary">Confidence</Typography>
                <LinearProgress
                  variant="determinate"
                  value={signal.confidence * 100}
                  sx={{ height: 4, borderRadius: 1, mt: 0.5 }}
                />
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">Strength</Typography>
                <LinearProgress
                  variant="determinate"
                  value={(signal.strength + 1) * 50}
                  color={signal.strength > 0 ? 'success' : 'error'}
                  sx={{ height: 4, borderRadius: 1, mt: 0.5 }}
                />
              </Box>
            </Box>

            {signal.metrics && (
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 0.5, fontSize: '0.7rem' }}>
                {signal.metrics.trendStrength !== undefined && (
                  <Typography variant="caption" color="text.secondary">
                    Trend: {signal.metrics.trendStrength.toFixed(2)}
                  </Typography>
                )}
                {signal.metrics.volatilityRatio !== undefined && (
                  <Typography variant="caption" color="text.secondary">
                    Vol Ratio: {signal.metrics.volatilityRatio.toFixed(2)}
                  </Typography>
                )}
              </Box>
            )}
          </Box>
        ))}
      </Box>

      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2, textAlign: 'center' }}>
        Last Update: {new Date(regime.timestamp).toLocaleTimeString()}
      </Typography>
    </Paper>
  );
};

export default RegimeIndicator;
