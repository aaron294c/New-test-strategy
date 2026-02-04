/**
 * MACD-V Historical Reference Data Component
 *
 * Displays precomputed MACD-V percentile reference data for all tickers
 * Shows zone distributions, statistics, and historical patterns
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Card,
  CardContent,
} from '@mui/material';
import {
  ExpandMore,
  Info,
  Timeline,
  Assessment,
} from '@mui/icons-material';

interface ZoneDistribution {
  count: number;
  percentage: number;
  min: number;
  max: number;
  mean: number;
  median: number;
  std: number;
  percentiles: { [key: string]: number };
}

interface CurrentState {
  current_macdv: number;
  zone: string;
  zone_display: string;
  categorical_percentile: number;
  asymmetric_percentile: number;
  interpretation: string;
}

interface TickerReference {
  ticker: string;
  total_data_points: number;
  overall_stats: {
    min: number;
    max: number;
    mean: number;
    median: number;
    std: number;
    percentiles: { [key: string]: number };
  };
  zone_distributions: {
    extreme_bearish?: ZoneDistribution;
    strong_bearish?: ZoneDistribution;
    ranging?: ZoneDistribution;
    strong_bullish?: ZoneDistribution;
    extreme_bullish?: ZoneDistribution;
  };
  current_state: CurrentState;
}

interface MACDVReferenceData {
  timestamp: string;
  total_tickers: number;
  total_data_points: number;
  tickers: { [key: string]: TickerReference };
}

const ZONE_COLORS: { [key: string]: { bg: string; color: string } } = {
  extreme_bearish: { bg: '#ff980020', color: '#f44336' },
  strong_bearish: { bg: '#f4433620', color: '#f44336' },
  ranging: { bg: '#9e9e9e20', color: '#757575' },
  strong_bullish: { bg: '#4caf5020', color: '#4caf50' },
  extreme_bullish: { bg: '#ff980020', color: '#4caf50' },
};

export const MACDVHistoricalData: React.FC = () => {
  const [data, setData] = useState<MACDVReferenceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedTicker, setExpandedTicker] = useState<string | null>(null);

  useEffect(() => {
    const loadReferenceData = async () => {
      try {
        // Load the precomputed reference database
        const response = await fetch('/docs/macdv_reference_database.json');
        if (!response.ok) {
          throw new Error('Failed to load MACD-V reference database');
        }
        const jsonData = await response.json();
        setData(jsonData);
        console.log('✅ MACD-V reference data loaded:', jsonData.total_tickers, 'tickers');
      } catch (err: any) {
        console.error('❌ Error loading MACD-V reference data:', err);
        setError(err.message || 'Failed to load reference data');
      } finally {
        setLoading(false);
      }
    };

    loadReferenceData();
  }, []);

  const handleAccordionChange = (ticker: string) => {
    setExpandedTicker(expandedTicker === ticker ? null : ticker);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ my: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!data) {
    return null;
  }

  const tickers = Object.keys(data.tickers).sort();

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
        <Typography variant="h5" fontWeight="bold">
          📊 MACD-V Historical Reference Database
        </Typography>
        <Box display="flex" alignItems="center" gap={1}>
          <Chip
            icon={<Assessment />}
            label={`${data.total_tickers} Tickers`}
            color="primary"
            size="small"
          />
          <Chip
            icon={<Timeline />}
            label={`${data.total_data_points.toLocaleString()} Data Points`}
            color="secondary"
            size="small"
          />
          <Typography variant="caption" color="text.secondary">
            Updated: {new Date(data.timestamp).toLocaleString()}
          </Typography>
        </Box>
      </Box>

      <Alert severity="info" icon={<Info />} sx={{ mb: 3 }}>
        <Typography variant="body2">
          This database contains precomputed MACD-V percentile distributions for historical analysis.
          Each ticker shows zone-specific statistics and current percentile rankings.
          <strong> Click on a ticker to see detailed zone breakdowns.</strong>
        </Typography>
      </Alert>

      <TableContainer sx={{ maxHeight: '60vh', overflowY: 'auto' }}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell>Ticker</TableCell>
              <TableCell align="right">Data Points</TableCell>
              <TableCell>Current Zone</TableCell>
              <TableCell align="right">Current MACD-V</TableCell>
              <TableCell align="right">Cat %ile</TableCell>
              <TableCell>Interpretation</TableCell>
              <TableCell align="right">Overall Min</TableCell>
              <TableCell align="right">Overall Max</TableCell>
              <TableCell align="right">Mean</TableCell>
              <TableCell align="right">Median</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tickers.map((ticker) => {
              const tickerData = data.tickers[ticker];
              const currentState = tickerData.current_state;
              const stats = tickerData.overall_stats;
              const zoneColors = ZONE_COLORS[currentState.zone] || ZONE_COLORS.ranging;

              return (
                <React.Fragment key={ticker}>
                  <TableRow
                    hover
                    sx={{
                      cursor: 'pointer',
                      backgroundColor: expandedTicker === ticker ? '#f5f5f5' : 'inherit',
                    }}
                    onClick={() => handleAccordionChange(ticker)}
                  >
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        <ExpandMore
                          sx={{
                            transform: expandedTicker === ticker ? 'rotate(180deg)' : 'rotate(0deg)',
                            transition: 'transform 0.3s',
                          }}
                        />
                        <Typography variant="body2" fontWeight="bold">
                          {ticker}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" color="text.secondary">
                        {tickerData.total_data_points.toLocaleString()}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={currentState.zone_display}
                        size="small"
                        sx={{
                          backgroundColor: zoneColors.bg,
                          color: zoneColors.color,
                          fontSize: '0.7rem',
                        }}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight="medium">
                        {currentState.current_macdv.toFixed(1)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography
                        variant="body2"
                        fontWeight="medium"
                        sx={{
                          color:
                            currentState.zone === 'ranging'
                              ? currentState.categorical_percentile >= 80
                                ? '#f44336'
                                : currentState.categorical_percentile <= 20
                                ? '#4caf50'
                                : 'text.secondary'
                              : currentState.categorical_percentile >= 80
                              ? '#4caf50'
                              : 'text.secondary',
                        }}
                      >
                        {currentState.categorical_percentile.toFixed(1)}%
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontSize="0.8rem">
                        {currentState.interpretation}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" color="error.main">
                        {stats.min.toFixed(1)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" color="success.main">
                        {stats.max.toFixed(1)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">{stats.mean.toFixed(1)}</Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">{stats.median.toFixed(1)}</Typography>
                    </TableCell>
                  </TableRow>
                  {expandedTicker === ticker && (
                    <TableRow>
                      <TableCell colSpan={10} sx={{ py: 3, backgroundColor: '#fafafa' }}>
                        <Typography variant="h6" gutterBottom>
                          Zone Distributions for {ticker}
                        </Typography>
                        <Grid container spacing={2}>
                          {Object.entries(tickerData.zone_distributions).map(([zone, dist]) => {
                            const zoneColors = ZONE_COLORS[zone];
                            const zoneLabels: { [key: string]: string } = {
                              extreme_bearish: 'Extreme Bearish (< -100)',
                              strong_bearish: 'Strong Bearish (-100 to -50)',
                              ranging: 'Ranging (-50 to +50)',
                              strong_bullish: 'Strong Bullish (+50 to +100)',
                              extreme_bullish: 'Extreme Bullish (> +100)',
                            };

                            return (
                              <Grid item xs={12} md={6} lg={4} key={zone}>
                                <Card
                                  sx={{
                                    border: currentState.zone === zone ? '2px solid' : 'none',
                                    borderColor: currentState.zone === zone ? zoneColors.color : 'transparent',
                                  }}
                                >
                                  <CardContent>
                                    <Typography
                                      variant="subtitle2"
                                      gutterBottom
                                      sx={{ color: zoneColors.color, fontWeight: 'bold' }}
                                    >
                                      {zoneLabels[zone]}
                                      {currentState.zone === zone && ' (Current)'}
                                    </Typography>
                                    <Box display="flex" flexDirection="column" gap={0.5}>
                                      <Typography variant="caption">
                                        <strong>Count:</strong> {dist.count} ({dist.percentage.toFixed(1)}%)
                                      </Typography>
                                      <Typography variant="caption">
                                        <strong>Range:</strong> {dist.min.toFixed(1)} to {dist.max.toFixed(1)}
                                      </Typography>
                                      <Typography variant="caption">
                                        <strong>Mean:</strong> {dist.mean.toFixed(1)} | <strong>Median:</strong>{' '}
                                        {dist.median.toFixed(1)}
                                      </Typography>
                                      <Typography variant="caption">
                                        <strong>Std Dev:</strong> {dist.std.toFixed(1)}
                                      </Typography>
                                      <Typography variant="caption" sx={{ mt: 1, fontWeight: 'bold' }}>
                                        Key Percentiles:
                                      </Typography>
                                      <Box display="flex" gap={1} flexWrap="wrap">
                                        {Object.entries(dist.percentiles)
                                          .filter(([p]) => ['10', '25', '50', '75', '90'].includes(p))
                                          .map(([p, val]) => (
                                            <Chip
                                              key={p}
                                              label={`${p}%: ${(val as number).toFixed(1)}`}
                                              size="small"
                                              sx={{
                                                height: 20,
                                                fontSize: '0.65rem',
                                                backgroundColor: zoneColors.bg,
                                                color: zoneColors.color,
                                              }}
                                            />
                                          ))}
                                      </Box>
                                    </Box>
                                  </CardContent>
                                </Card>
                              </Grid>
                            );
                          })}
                        </Grid>
                      </TableCell>
                    </TableRow>
                  )}
                </React.Fragment>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};

export default MACDVHistoricalData;
