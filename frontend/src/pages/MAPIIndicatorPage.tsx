/**
 * MAPI (Momentum-Adapted Percentile Indicator) Page
 *
 * Designed for momentum stocks (AAPL, TSLA, AVGO, NFLX)
 * Uses EMA distance and slope velocity with percentile framework
 */

import React, { useEffect, useRef, useState, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  ToggleButtonGroup,
  ToggleButton,
  Divider,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { createChart, IChartApi, ISeriesApi, LineStyle } from 'lightweight-charts';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TimelineIcon from '@mui/icons-material/Timeline';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import { mapiApi } from '@/api/client';

interface MAPIIndicatorPageProps {
  ticker: string;
  onRefresh?: () => void;
}

const MAPIIndicatorPage: React.FC<MAPIIndicatorPageProps> = ({ ticker }) => {
  const [chartType, setChartType] = useState<'composite' | 'components' | 'ema'>('composite');
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  // Fetch MAPI data
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['mapi-chart', ticker],
    queryFn: () => mapiApi.getMAPIChartData(ticker, 252),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });

  const chartData = data?.chart_data;
  const current = chartData?.current;
  const thresholds = chartData?.thresholds;

  // Memoize timestamp conversion to prevent recalculation
  const timestamps = useMemo(() => {
    if (!chartData?.dates) return [];
    return chartData.dates.map((d: string) => {
      const date = new Date(d);
      return Math.floor(date.getTime() / 1000);
    });
  }, [chartData?.dates]);

  // Memoize chart data transformations
  const compositeData = useMemo(() => {
    if (!timestamps.length || !chartData?.composite_score) return [];
    return timestamps.map((time: number, i: number) => ({
      time,
      value: chartData.composite_score[i] ?? 50,
    }));
  }, [timestamps, chartData?.composite_score]);

  const edrData = useMemo(() => {
    if (!timestamps.length || !chartData?.edr_percentile) return [];
    return timestamps.map((time: number, i: number) => ({
      time,
      value: chartData.edr_percentile[i] ?? 50,
    }));
  }, [timestamps, chartData?.edr_percentile]);

  const esvData = useMemo(() => {
    if (!timestamps.length || !chartData?.esv_percentile) return [];
    return timestamps.map((time: number, i: number) => ({
      time,
      value: chartData.esv_percentile[i] ?? 50,
    }));
  }, [timestamps, chartData?.esv_percentile]);

  const priceData = useMemo(() => {
    if (!timestamps.length || !chartData?.close) return [];
    return timestamps.map((time: number, i: number) => ({
      time,
      value: chartData.close[i],
    }));
  }, [timestamps, chartData?.close]);

  const ema20Data = useMemo(() => {
    if (!timestamps.length || !chartData?.ema20) return [];
    return timestamps.map((time: number, i: number) => ({
      time,
      value: chartData.ema20[i],
    }));
  }, [timestamps, chartData?.ema20]);

  const ema50Data = useMemo(() => {
    if (!timestamps.length || !chartData?.ema50) return [];
    return timestamps.map((time: number, i: number) => ({
      time,
      value: chartData.ema50[i],
    }));
  }, [timestamps, chartData?.ema50]);

  // Memoize markers to prevent recalculation
  const markers = useMemo(() => {
    if (!timestamps.length || !chartData) return [];
    const result: any[] = [];
    timestamps.forEach((time: number, i: number) => {
      if (chartData.strong_momentum_signals?.[i]) {
        result.push({
          time,
          position: 'belowBar',
          color: '#4caf50',
          shape: 'arrowUp',
          text: 'Strong',
        });
      }
      if (chartData.pullback_signals?.[i]) {
        result.push({
          time,
          position: 'belowBar',
          color: '#2196f3',
          shape: 'circle',
          text: 'Pullback',
        });
      }
      if (chartData.exit_signals?.[i]) {
        result.push({
          time,
          position: 'aboveBar',
          color: '#f44336',
          shape: 'arrowDown',
          text: 'Exit',
        });
      }
    });
    return result;
  }, [timestamps, chartData?.strong_momentum_signals, chartData?.pullback_signals, chartData?.exit_signals]);

  // Create chart only once
  useEffect(() => {
    if (!chartContainerRef.current || chartRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { color: '#131722' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#1e222d' },
        horzLines: { color: '#1e222d' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#2B2B43',
      },
      timeScale: {
        borderColor: '#2B2B43',
        timeVisible: true,
      },
    });

    chartRef.current = chart;

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, []);

  // Update chart series when data or chart type changes
  useEffect(() => {
    if (!chartRef.current || !timestamps.length) return;

    const chart = chartRef.current;

    // Remove all series
    chart.options();

    // Clear existing series - store references to avoid memory leaks
    const seriesMap = new Map();

    if (chartType === 'composite') {
      // Composite Score Chart
      const compositeSeries = chart.addLineSeries({
        color: '#2962FF',
        lineWidth: 2,
        title: 'Composite Momentum Score',
      });
      seriesMap.set('composite', compositeSeries);

      compositeSeries.setData(compositeData);

      // Add threshold lines
      const addThresholdLine = (value: number, color: string, lineStyle: LineStyle) => {
        const thresholdData = timestamps.map((time: number) => ({
          time,
          value,
        }));
        const line = chart.addLineSeries({
          color,
          lineWidth: 1,
          lineStyle,
          priceLineVisible: false,
          lastValueVisible: false,
        });
        line.setData(thresholdData);
        return line;
      };

      seriesMap.set('threshold1', addThresholdLine(thresholds?.strong_momentum || 65, '#4caf50', LineStyle.Dashed));
      seriesMap.set('threshold2', addThresholdLine(thresholds?.exit_threshold || 40, '#f44336', LineStyle.Dashed));
      seriesMap.set('threshold3', addThresholdLine(50, '#888888', LineStyle.Dotted));

      compositeSeries.setMarkers(markers);

    } else if (chartType === 'components') {
      // EDR and ESV Percentiles
      const edrSeries = chart.addLineSeries({
        color: '#2962FF',
        lineWidth: 2,
        title: 'EDR Percentile',
      });
      seriesMap.set('edr', edrSeries);

      const esvSeries = chart.addLineSeries({
        color: '#f50057',
        lineWidth: 2,
        title: 'ESV Percentile',
      });
      seriesMap.set('esv', esvSeries);

      edrSeries.setData(edrData);
      esvSeries.setData(esvData);

      // 50% reference line
      const refData = timestamps.map((time: number) => ({
        time,
        value: 50,
      }));
      const refLine = chart.addLineSeries({
        color: '#888888',
        lineWidth: 1,
        lineStyle: LineStyle.Dotted,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      refLine.setData(refData);
      seriesMap.set('ref', refLine);

    } else if (chartType === 'ema') {
      // Price with EMAs
      const priceSeries = chart.addLineSeries({
        color: '#ffffff',
        lineWidth: 2,
        title: 'Price',
      });
      seriesMap.set('price', priceSeries);

      const ema20Series = chart.addLineSeries({
        color: '#2962FF',
        lineWidth: 2,
        title: 'EMA(20)',
      });
      seriesMap.set('ema20', ema20Series);

      const ema50Series = chart.addLineSeries({
        color: '#f50057',
        lineWidth: 2,
        title: 'EMA(50)',
      });
      seriesMap.set('ema50', ema50Series);

      priceSeries.setData(priceData);
      ema20Series.setData(ema20Data);
      ema50Series.setData(ema50Data);
    }

    chart.timeScale().fitContent();

    return () => {
      // Clean up series when chart type changes
      seriesMap.forEach(series => {
        try {
          chart.removeSeries(series);
        } catch (e) {
          // Series might already be removed
        }
      });
      seriesMap.clear();
    };
  }, [chartType, compositeData, edrData, esvData, priceData, ema20Data, ema50Data, timestamps, thresholds, markers]);

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Failed to load MAPI data: {error instanceof Error ? error.message : 'Unknown error'}
      </Alert>
    );
  }

  if (!chartData || !current) {
    return <Alert severity="info">No MAPI data available for {ticker}</Alert>;
  }

  // Determine signal type
  const getSignalInfo = () => {
    if (current.strong_momentum_entry) {
      return {
        label: 'STRONG MOMENTUM ENTRY',
        color: 'success',
        icon: <TrendingUpIcon />,
      };
    }
    if (current.pullback_entry) {
      return {
        label: 'PULLBACK ENTRY',
        color: 'info',
        icon: <TimelineIcon />,
      };
    }
    if (current.exit_signal) {
      return {
        label: 'EXIT SIGNAL',
        color: 'error',
        icon: <TrendingDownIcon />,
      };
    }
    if (current.composite_score > 50) {
      return {
        label: 'BULLISH',
        color: 'success',
        icon: <TrendingUpIcon />,
      };
    }
    return {
      label: 'NEUTRAL',
      color: 'default',
      icon: <ShowChartIcon />,
    };
  };

  const signalInfo = getSignalInfo();
  const regimeColor = current.regime === 'Momentum' ? 'success' :
                      current.regime === 'Mean Reversion' ? 'warning' : 'default';

  return (
    <Box>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={8}>
            <Typography variant="h5" gutterBottom>
              MAPI - Momentum-Adapted Percentile Indicator
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Designed for momentum stocks using EMA distance, slope velocity, and percentile framework
            </Typography>
          </Grid>
          <Grid item xs={12} md={4} textAlign="right">
            <Chip
              label={`${ticker} - ${current.regime}`}
              color={regimeColor as any}
              icon={signalInfo.icon}
              sx={{ mr: 1 }}
            />
            <Chip
              label={signalInfo.label}
              color={signalInfo.color as any}
              icon={signalInfo.icon}
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Current Metrics */}
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Composite Score
              </Typography>
              <Typography variant="h4" color={current.composite_score > 65 ? 'success.main' :
                                               current.composite_score < 40 ? 'error.main' : 'text.primary'}>
                {current.composite_score.toFixed(1)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {current.composite_score > 65 ? 'Strong momentum' :
                 current.composite_score < 40 ? 'Weak momentum' : 'Neutral'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                EDR Percentile
              </Typography>
              <Typography variant="h4">
                {current.edr_percentile.toFixed(1)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Price-to-EMA distance
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                ESV Percentile
              </Typography>
              <Typography variant="h4">
                {current.esv_percentile.toFixed(1)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                EMA slope velocity
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Distance to EMA(20)
              </Typography>
              <Typography variant="h4" color={current.distance_to_ema20_pct > 0 ? 'success.main' : 'error.main'}>
                {current.distance_to_ema20_pct > 0 ? '+' : ''}{current.distance_to_ema20_pct.toFixed(2)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                ${current.ema20.toFixed(2)} EMA(20)
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Chart Controls */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <ToggleButtonGroup
          value={chartType}
          exclusive
          onChange={(_, value) => value && setChartType(value)}
          size="small"
        >
          <ToggleButton value="composite">
            Composite Score
          </ToggleButton>
          <ToggleButton value="components">
            EDR & ESV
          </ToggleButton>
          <ToggleButton value="ema">
            Price & EMAs
          </ToggleButton>
        </ToggleButtonGroup>
      </Paper>

      {/* Chart */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <div ref={chartContainerRef} style={{ width: '100%', height: '500px' }} />
      </Paper>

      {/* Signal Interpretation */}
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Entry Signals
              </Typography>
              <Divider sx={{ my: 1 }} />

              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="success.main" gutterBottom>
                  Strong Momentum Entry (Composite &gt; 65%)
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  • Price above EMA(20)<br />
                  • ESV &gt; 50% (positive slope)<br />
                  • Strong uptrend confirmation
                </Typography>
              </Box>

              <Box>
                <Typography variant="subtitle2" color="info.main" gutterBottom>
                  Pullback Entry (30-45% zone)
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  • Price touches EMA(20)<br />
                  • ESV &gt; 40% (trend intact)<br />
                  • Composite Score recovering
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Current Status
              </Typography>
              <Divider sx={{ my: 1 }} />

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2">
                  <strong>Regime:</strong> {current.regime} (ADX: {current.adx.toFixed(1)})
                </Typography>
                <Typography variant="body2">
                  <strong>Price:</strong> ${current.close.toFixed(2)}
                </Typography>
                <Typography variant="body2">
                  <strong>EMA(20):</strong> ${current.ema20.toFixed(2)}
                </Typography>
                <Typography variant="body2">
                  <strong>EMA(50):</strong> ${current.ema50.toFixed(2)}
                </Typography>
              </Box>

              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Thresholds
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Strong Momentum: &gt;{thresholds?.strong_momentum}%<br />
                  Pullback Zone: {thresholds?.pullback_zone_low}-{thresholds?.pullback_zone_high}%<br />
                  Exit: &lt;{thresholds?.exit_threshold}%<br />
                  Momentum ADX: &gt;{thresholds?.adx_momentum}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MAPIIndicatorPage;
