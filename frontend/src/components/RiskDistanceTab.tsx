import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  Tooltip,
  IconButton,
  Divider,
  Stack,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Warning,
  CheckCircle,
  Info,
  Refresh,
} from '@mui/icons-material';
import { getRiskDistance } from '../api/client';
import type { SymbolRiskDistanceData, RiskDistanceLevel, MaxPainData } from '../types';

interface RiskDistanceTabProps {
  symbol: string;
}

const formatPrice = (price: number): string => {
  return price.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  });
};

const formatPercent = (pct: number): string => {
  const sign = pct >= 0 ? '+' : '';
  return `${sign}${pct.toFixed(2)}%`;
};

const getDistanceColor = (distance: number): string => {
  const abs = Math.abs(distance);
  if (abs < 2) return '#f44336'; // Red - very close
  if (abs < 5) return '#ff9800'; // Orange - close
  if (abs < 10) return '#2196f3'; // Blue - moderate
  return '#4caf50'; // Green - far
};

const getStrengthColor = (strength: number): string => {
  if (strength >= 70) return '#4caf50';
  if (strength >= 50) return '#ff9800';
  if (strength >= 30) return '#2196f3';
  return '#9e9e9e';
};

const DistanceBar: React.FC<{ distance: number; label: string; isSupport: boolean }> = ({
  distance,
  label,
  isSupport,
}) => {
  const normalizedValue = Math.min(Math.abs(distance), 20) * 5; // Scale to 0-100
  const color = getDistanceColor(distance);

  return (
    <Box sx={{ mb: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
        <Typography variant="body2" fontWeight="bold" sx={{ color }}>
          {formatPercent(distance)}
        </Typography>
      </Box>
      <LinearProgress
        variant="determinate"
        value={normalizedValue}
        sx={{
          height: 8,
          borderRadius: 4,
          backgroundColor: 'rgba(0,0,0,0.1)',
          '& .MuiLinearProgress-bar': {
            backgroundColor: color,
            borderRadius: 4,
          },
        }}
      />
    </Box>
  );
};

const WallCard: React.FC<{
  title: string;
  walls: Record<string, RiskDistanceLevel>;
  isSupport: boolean;
}> = ({ title, walls, isSupport }) => {
  const timeframes = ['weekly', 'swing', 'long', 'quarterly'];
  const icon = isSupport ? <TrendingDown color="success" /> : <TrendingUp color="error" />;

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          {icon}
          <Typography variant="h6" sx={{ ml: 1 }}>
            {title}
          </Typography>
        </Box>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Timeframe</TableCell>
                <TableCell align="right">Level</TableCell>
                <TableCell align="right">Distance</TableCell>
                <TableCell align="right">Strength</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {timeframes.map((tf) => {
                const wall = walls[tf];
                if (!wall) return null;
                return (
                  <TableRow key={tf}>
                    <TableCell>
                      <Chip
                        label={tf.charAt(0).toUpperCase() + tf.slice(1)}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell align="right">{formatPrice(wall.strike)}</TableCell>
                    <TableCell
                      align="right"
                      sx={{ color: getDistanceColor(wall.distance_pct), fontWeight: 'bold' }}
                    >
                      {formatPercent(wall.distance_pct)}
                    </TableCell>
                    <TableCell align="right">
                      <Chip
                        label={`${wall.strength.toFixed(0)}%`}
                        size="small"
                        sx={{
                          backgroundColor: getStrengthColor(wall.strength),
                          color: 'white',
                        }}
                      />
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );
};

const MaxPainCard: React.FC<{ maxPain: Record<string, MaxPainData>; currentPrice: number }> = ({
  maxPain,
  currentPrice,
}) => {
  const timeframes = ['weekly', 'swing', 'long', 'quarterly'];

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Warning color="warning" />
          <Typography variant="h6" sx={{ ml: 1 }}>
            Max Pain Levels
          </Typography>
          <Tooltip title="Max pain is the strike price where option holders lose the most money at expiration. Price often gravitates toward max pain near expiration.">
            <IconButton size="small" sx={{ ml: 1 }}>
              <Info fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Timeframe</TableCell>
                <TableCell align="right">Max Pain</TableCell>
                <TableCell align="right">Distance</TableCell>
                <TableCell align="right">Direction</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {timeframes.map((tf) => {
                const mp = maxPain[tf];
                if (!mp) return null;
                const direction = mp.strike > currentPrice ? 'Above' : 'Below';
                const directionColor = mp.strike > currentPrice ? '#4caf50' : '#f44336';
                return (
                  <TableRow key={tf}>
                    <TableCell>
                      <Chip
                        label={tf.charAt(0).toUpperCase() + tf.slice(1)}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell align="right">{formatPrice(mp.strike)}</TableCell>
                    <TableCell
                      align="right"
                      sx={{ color: getDistanceColor(mp.distance_pct), fontWeight: 'bold' }}
                    >
                      {formatPercent(mp.distance_pct)}
                    </TableCell>
                    <TableCell align="right">
                      <Chip label={direction} size="small" sx={{ backgroundColor: directionColor, color: 'white' }} />
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );
};

const SummaryCard: React.FC<{ data: SymbolRiskDistanceData }> = ({ data }) => {
  const { summary, gamma_flip, weighted_walls, sd_levels } = data;
  
  const positionColors: Record<string, string> = {
    near_support: '#4caf50',
    mid_range: '#2196f3',
    near_resistance: '#f44336',
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Risk Summary
        </Typography>
        
        <Grid container spacing={2}>
          {/* Position Status */}
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'rgba(0,0,0,0.02)', borderRadius: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Current Position
              </Typography>
              <Chip
                label={summary.position_in_range.replace('_', ' ').toUpperCase()}
                sx={{
                  mt: 1,
                  backgroundColor: positionColors[summary.position_in_range],
                  color: 'white',
                  fontWeight: 'bold',
                }}
              />
            </Box>
          </Grid>
          
          {/* Risk/Reward */}
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'rgba(0,0,0,0.02)', borderRadius: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Risk/Reward Ratio
              </Typography>
              <Typography variant="h4" sx={{ mt: 1, color: summary.risk_reward_ratio > 1 ? '#4caf50' : '#f44336' }}>
                {summary.risk_reward_ratio.toFixed(2)}
              </Typography>
            </Box>
          </Grid>
          
          {/* Gamma Flip */}
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'rgba(0,0,0,0.02)', borderRadius: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Gamma Flip
              </Typography>
              <Typography variant="h5" sx={{ mt: 1 }}>
                {gamma_flip ? formatPrice(gamma_flip.strike) : 'N/A'}
              </Typography>
              {gamma_flip && (
                <Typography variant="body2" color="text.secondary">
                  {formatPercent(gamma_flip.distance_pct)} away
                </Typography>
              )}
            </Box>
          </Grid>
        </Grid>
        
        {/* Recommendation */}
        <Alert
          severity={summary.position_in_range === 'near_support' ? 'success' : summary.position_in_range === 'near_resistance' ? 'warning' : 'info'}
          icon={summary.position_in_range === 'near_support' ? <CheckCircle /> : <Warning />}
          sx={{ mt: 2 }}
        >
          {summary.recommendation}
        </Alert>
        
        {/* Weighted Wall Recommendation */}
        {weighted_walls?.put && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Recommended Support Level ({weighted_walls.put.method_used}):
            </Typography>
            <Typography variant="h6">
              {formatPrice(weighted_walls.put.recommended_wall)}
              <Chip
                label={weighted_walls.put.confidence}
                size="small"
                sx={{ ml: 1 }}
                color={weighted_walls.put.confidence === 'high' ? 'success' : 'default'}
              />
            </Typography>
          </Box>
        )}
        
        {/* SD Levels */}
        {sd_levels && (
          <Box sx={{ mt: 2 }}>
            <Divider sx={{ my: 2 }} />
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Expected Move ({sd_levels.dte} DTE, IV: {sd_levels.iv_used}%)
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              <Chip label={`-1σ: ${formatPrice(sd_levels.lower_1sd)}`} size="small" variant="outlined" />
              <Chip label={`+1σ: ${formatPrice(sd_levels.upper_1sd)}`} size="small" variant="outlined" />
              <Chip label={`-2σ: ${formatPrice(sd_levels.lower_2sd)}`} size="small" variant="outlined" color="error" />
              <Chip label={`+2σ: ${formatPrice(sd_levels.upper_2sd)}`} size="small" variant="outlined" color="success" />
            </Stack>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export const RiskDistanceTab: React.FC<RiskDistanceTabProps> = ({ symbol }) => {
  const [data, setData] = useState<SymbolRiskDistanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getRiskDistance(symbol);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch risk distance data');
    } finally {
      setLoading(false);
    }
  };

  const fetchGammaData = async (forceRefresh = false) => {
    try {
      const url = forceRefresh 
        ? '/api/gamma/refresh' 
        : '/api/gamma/data';
      
      const response = await fetch(url, {
        method: forceRefresh ? 'POST' : 'GET',
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch gamma data: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      if (result.status === 'error') {
        console.error('Gamma data error:', result.message);
        return null;
      }
      
      return result.data;
    } catch (error) {
      console.error('Error fetching gamma data:', error);
      return null;
    }
  };

  useEffect(() => {
    fetchData();
  }, [symbol]);

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2, textAlign: 'center' }}>
          Loading risk distance data for {symbol}...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!data) {
    return (
      <Alert severity="warning" sx={{ m: 2 }}>
        No risk distance data available for {symbol}
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h5">
            {symbol} Risk Distance Analysis
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Current Price: {formatPrice(data.current_price)} | Updated: {new Date(data.timestamp).toLocaleString()}
          </Typography>
        </Box>
        <IconButton onClick={fetchData} title="Refresh">
          <Refresh />
        </IconButton>
      </Box>

      {/* Summary Card */}
      <Box sx={{ mb: 3 }}>
        <SummaryCard data={data} />
      </Box>

      {/* Distance Bars */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Quick Distance View
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Support Levels (Put Walls)
              </Typography>
              {Object.entries(data.put_walls).map(([tf, wall]) => (
                <DistanceBar
                  key={tf}
                  distance={wall.distance_pct}
                  label={`${tf.charAt(0).toUpperCase() + tf.slice(1)} (${formatPrice(wall.strike)})`}
                  isSupport={true}
                />
              ))}
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Resistance Levels (Call Walls)
              </Typography>
              {Object.entries(data.call_walls).map(([tf, wall]) => (
                <DistanceBar
                  key={tf}
                  distance={wall.distance_pct}
                  label={`${tf.charAt(0).toUpperCase() + tf.slice(1)} (${formatPrice(wall.strike)})`}
                  isSupport={false}
                />
              ))}
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Detailed Tables */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <WallCard title="Support Levels (Put Walls)" walls={data.put_walls} isSupport={true} />
        </Grid>
        <Grid item xs={12} md={6}>
          <WallCard title="Resistance Levels (Call Walls)" walls={data.call_walls} isSupport={false} />
        </Grid>
        <Grid item xs={12}>
          <MaxPainCard maxPain={data.max_pain} currentPrice={data.current_price} />
        </Grid>
      </Grid>
    </Box>
  );
};

export default RiskDistanceTab;
