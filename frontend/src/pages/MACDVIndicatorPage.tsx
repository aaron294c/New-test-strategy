/**
 * MACD-V (MACD Volatility-Normalized) Indicator Page
 *
 * Pine Script v6 implementation with:
 * - MACD normalized by ATR for cross-asset comparison
 * - Chart mode: MACD-V oscillator visualization
 * - Dashboard mode: Multi-ticker, multi-timeframe table
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { createChart, IChartApi, ISeriesApi, LineData, LineStyle, UTCTimestamp } from 'lightweight-charts';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import DashboardIcon from '@mui/icons-material/Dashboard';
import { macdvApi } from '@/api/client';

interface MACDVIndicatorPageProps {
  ticker: string;
}

const SWING_TICKERS = [
  'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'QQQ', 'SPY',
  'GLD', 'SLV', 'TSLA', 'NFLX', 'BRK-B', 'WMT', 'UNH', 'AVGO',
  'LLY', 'TSM', 'ORCL', 'OXY', 'XOM', 'CVX', 'JPM', 'BAC',
  'ES=F', 'NQ=F', 'BTC-USD', '^VIX', 'DX-Y.NYB', '^TNX', 'XLI'
];

const TIMEFRAMES = ['1mo', '1wk', '1d'];
const TIMEFRAME_LABELS: Record<string, string> = {
  '1mo': 'Monthly',
  '1wk': 'Weekly',
  '1d': 'Daily'
};

const MACDVIndicatorPage: React.FC<MACDVIndicatorPageProps> = ({ ticker }) => {
  const [activeTab, setActiveTab] = useState<'chart' | 'dashboard'>('chart');
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);

  // Fetch MACD-V chart data
  const { data: chartDataResponse, isLoading: isLoadingChart, error: chartError } = useQuery({
    queryKey: ['macdv-chart', ticker],
    queryFn: async () => {
      console.log(`[MACD-V] Fetching chart data for ${ticker}...`);
      const result = await macdvApi.getMACDVChartData(ticker, 252);
      console.log(`[MACD-V] Chart data received:`, result);
      return result;
    },
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 3,
    enabled: activeTab === 'chart',
  });

  // Fetch MACD-V dashboard data
  const { data: dashboardDataResponse, isLoading: isLoadingDashboard, error: dashboardError } = useQuery({
    queryKey: ['macdv-dashboard'],
    queryFn: async () => {
      console.log(`[MACD-V] Fetching dashboard data...`);
      const result = await macdvApi.getMACDVDashboard(TIMEFRAMES.join(','));
      console.log(`[MACD-V] Dashboard data received:`, result);
      return result;
    },
    staleTime: 1 * 60 * 1000, // 1 minute cache
    refetchOnWindowFocus: false,
    retry: 2,
    enabled: activeTab === 'dashboard',
  });

  const chartData = chartDataResponse?.chart_data;
  const current = chartData?.current;
  const dashboardData = dashboardDataResponse?.dashboard;

  // Memoize timestamps
  const timestamps = useMemo<UTCTimestamp[]>(() => {
    if (!chartData?.dates) return [];
    return chartData.dates.map((d: string) => {
      const date = new Date(d);
      return Math.floor(date.getTime() / 1000) as UTCTimestamp;
    });
  }, [chartData?.dates]);

  // Memoize MACD-V data
  const macdvData = useMemo(() => {
    if (!timestamps.length || !chartData?.macdv_val) return [];
    return timestamps.map((time: UTCTimestamp, i: number) => ({
      time,
      value: chartData.macdv_val[i] ?? 0,
    }));
  }, [timestamps, chartData?.macdv_val]);

  const signalData = useMemo(() => {
    if (!timestamps.length || !chartData?.macdv_signal) return [];
    return timestamps.map((time: UTCTimestamp, i: number) => ({
      time,
      value: chartData.macdv_signal[i] ?? 0,
    }));
  }, [timestamps, chartData?.macdv_signal]);

  const histogramData = useMemo(() => {
    if (!timestamps.length || !chartData?.macdv_hist) return [];
    return timestamps.map((time: UTCTimestamp, i: number) => ({
      time,
      value: chartData.macdv_hist[i] ?? 0,
      color: chartData.macdv_hist[i] > (chartData.macdv_hist[i-1] ?? 0) ? '#26a69a' : '#ef5350',
    }));
  }, [timestamps, chartData?.macdv_hist]);

  // Create chart
  useEffect(() => {
    const container = chartContainerRef.current;
    if (!container || chartRef.current) return;

    const chart = createChart(container, {
      width: Math.max(container.clientWidth, 1),
      height: 500,
      layout: {
        background: { color: '#131722' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#1e222d' },
        horzLines: { color: '#1e222d' },
      },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: '#2B2B43' },
      timeScale: { borderColor: '#2B2B43', timeVisible: true },
    });

    chartRef.current = chart;

    const applyContainerSize = () => {
      const el = chartContainerRef.current;
      const c = chartRef.current;
      if (!el || !c) return;
      const width = Math.max(el.clientWidth, 1);
      const height = 500;
      c.applyOptions({ width, height });
      c.timeScale().fitContent();
    };

    resizeObserverRef.current = new ResizeObserver(() => {
      requestAnimationFrame(applyContainerSize);
    });
    resizeObserverRef.current.observe(container);
    window.addEventListener('resize', applyContainerSize);
    requestAnimationFrame(applyContainerSize);

    return () => {
      window.removeEventListener('resize', applyContainerSize);
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect();
        resizeObserverRef.current = null;
      }
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [chartData]);

  // Update chart series
  useEffect(() => {
    if (!chartRef.current || !timestamps.length) return;

    const chart = chartRef.current;
    const seriesMap = new Map<string, ISeriesApi<any>>();

    // Histogram
    const histSeries = chart.addHistogramSeries({
      color: '#26a69a',
      priceFormat: { type: 'price', precision: 2, minMove: 0.01 },
    });
    seriesMap.set('hist', histSeries);
    histSeries.setData(histogramData);

    // MACD-V Line
    const macdvSeries = chart.addLineSeries({
      color: '#2962FF',
      lineWidth: 2,
      title: 'MACD-V',
    });
    seriesMap.set('macdv', macdvSeries);
    macdvSeries.setData(macdvData as LineData<UTCTimestamp>[]);

    // Signal Line
    const signalSeries = chart.addLineSeries({
      color: '#f50057',
      lineWidth: 2,
      title: 'Signal',
    });
    seriesMap.set('signal', signalSeries);
    signalSeries.setData(signalData as LineData<UTCTimestamp>[]);

    // Horizontal lines (zones)
    const zeroLine = chart.addLineSeries({
      color: '#888888',
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    zeroLine.setData(timestamps.map((time: UTCTimestamp) => ({ time, value: 0 })));
    seriesMap.set('zero', zeroLine);

    const rangingUpLine = chart.addLineSeries({
      color: '#4caf50',
      lineWidth: 1,
      lineStyle: LineStyle.Dotted,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    rangingUpLine.setData(timestamps.map((time: UTCTimestamp) => ({ time, value: 50 })));
    seriesMap.set('ranging_up', rangingUpLine);

    const rangingDownLine = chart.addLineSeries({
      color: '#f44336',
      lineWidth: 1,
      lineStyle: LineStyle.Dotted,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    rangingDownLine.setData(timestamps.map((time: UTCTimestamp) => ({ time, value: -50 })));
    seriesMap.set('ranging_down', rangingDownLine);

    const riskUpLine = chart.addLineSeries({
      color: '#2196f3',
      lineWidth: 1,
      lineStyle: LineStyle.Solid,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    riskUpLine.setData(timestamps.map((time: UTCTimestamp) => ({ time, value: 150 })));
    seriesMap.set('risk_up', riskUpLine);

    const riskDownLine = chart.addLineSeries({
      color: '#2196f3',
      lineWidth: 1,
      lineStyle: LineStyle.Solid,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    riskDownLine.setData(timestamps.map((time: UTCTimestamp) => ({ time, value: -150 })));
    seriesMap.set('risk_down', riskDownLine);

    chart.timeScale().fitContent();

    return () => {
      seriesMap.forEach(series => {
        try {
          chart.removeSeries(series);
        } catch (e) {
          // ignore
        }
      });
      seriesMap.clear();
    };
  }, [macdvData, signalData, histogramData, timestamps]);

  // Get color for MACD-V value
  const getColorForValue = (val: number, trend: string) => {
    if (trend === 'Ranging') return 'default';
    if (trend === 'Bullish') return 'success';
    if (trend === 'Bearish') return 'error';
    return 'default';
  };

  if (activeTab === 'chart' && isLoadingChart) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (activeTab === 'chart' && chartError) {
    return (
      <Alert severity="error">
        Failed to load MACD-V data: {chartError instanceof Error ? chartError.message : 'Unknown error'}
      </Alert>
    );
  }

  if (activeTab === 'dashboard' && isLoadingDashboard) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (activeTab === 'dashboard' && dashboardError) {
    return (
      <Alert severity="error">
        Failed to load dashboard: {dashboardError instanceof Error ? dashboardError.message : 'Unknown error'}
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={8}>
            <Typography variant="h5" gutterBottom>
              MACD-V - MACD Volatility-Normalized
            </Typography>
            <Typography variant="body2" color="text.secondary">
              MACD normalized by ATR for cross-asset and cross-regime comparison (Pine Script v6)
            </Typography>
          </Grid>
          <Grid item xs={12} md={4} textAlign="right">
            {current && (
              <Chip
                label={`${ticker} - ${current.macdv_trend}`}
                color={getColorForValue(current.macdv_val, current.macdv_trend) as any}
                icon={<ShowChartIcon />}
              />
            )}
          </Grid>
        </Grid>
      </Paper>

      {/* Tab Navigation */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <ToggleButtonGroup
          value={activeTab}
          exclusive
          onChange={(_, value) => value && setActiveTab(value)}
          size="small"
        >
          <ToggleButton value="chart">
            <ShowChartIcon sx={{ mr: 1 }} />
            MACD-V Chart
          </ToggleButton>
          <ToggleButton value="dashboard">
            <DashboardIcon sx={{ mr: 1 }} />
            Dashboard (All Tickers)
          </ToggleButton>
        </ToggleButtonGroup>
      </Paper>

      {/* Chart Tab */}
      {activeTab === 'chart' && chartData && current && (
        <>
          {/* Current Metrics */}
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom variant="body2">
                    MACD-V Value
                  </Typography>
                  <Typography
                    variant="h4"
                    color={current.macdv_val > 50 ? 'success.main' :
                           current.macdv_val < -50 ? 'error.main' : 'text.primary'}
                  >
                    {current.macdv_val?.toFixed(2) || 'N/A'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Trend: {current.macdv_trend}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom variant="body2">
                    Signal Line
                  </Typography>
                  <Typography variant="h4">
                    {current.macdv_signal?.toFixed(2) || 'N/A'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    EMA(9) of MACD-V
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom variant="body2">
                    Histogram
                  </Typography>
                  <Typography variant="h4" color={current.macdv_hist > 0 ? 'success.main' : 'error.main'}>
                    {current.macdv_hist?.toFixed(2) || 'N/A'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    MACD-V - Signal
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom variant="body2">
                    Current Price
                  </Typography>
                  <Typography variant="h4">
                    ${current.close?.toFixed(2) || 'N/A'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Latest close
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Chart */}
          <Paper sx={{ p: 2, mb: 2 }}>
            <div ref={chartContainerRef} style={{ width: '100%', height: '500px' }} />
          </Paper>

          {/* Signal Interpretation */}
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              MACD-V Zone Classification
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="success.main">
                  Bullish Zones (MACD-V {'>'} 0)
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  • <strong>Rebounding (0 to 50):</strong> Recovering from weakness<br />
                  • <strong>Rallying (50 to 150):</strong> Strong uptrend<br />
                  • <strong>Risk ({'>'} 150):</strong> Extreme overextension
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="error.main">
                  Bearish Zones (MACD-V {'<'} 0)
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  • <strong>Retracing (0 to -50):</strong> Minor pullback<br />
                  • <strong>Reversing (-50 to -150):</strong> Downtrend forming<br />
                  • <strong>Risk ({'<'} -150):</strong> Extreme oversold
                </Typography>
              </Grid>
            </Grid>
          </Paper>
        </>
      )}

      {/* Dashboard Tab */}
      {activeTab === 'dashboard' && dashboardData && (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow sx={{ backgroundColor: 'primary.dark' }}>
                <TableCell>
                  <Typography variant="subtitle2" color="white">
                    Ticker
                  </Typography>
                </TableCell>
                {TIMEFRAMES.map((tf) => (
                  <TableCell key={tf} align="center">
                    <Typography variant="subtitle2" color="white">
                      {TIMEFRAME_LABELS[tf]}
                    </Typography>
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {SWING_TICKERS.map((sym) => {
                const symData = dashboardData.symbols?.[sym];
                if (!symData) return null;

                return (
                  <TableRow key={sym} sx={{ '&:hover': { backgroundColor: 'action.hover' } }}>
                    <TableCell>
                      <Typography variant="body2" fontWeight="bold">
                        {sym}
                      </Typography>
                    </TableCell>
                    {TIMEFRAMES.map((tf) => {
                      const tfData = symData[tf];
                      if (!tfData) {
                        return (
                          <TableCell key={tf} align="center">
                            <Typography variant="caption" color="text.disabled">
                              —
                            </Typography>
                          </TableCell>
                        );
                      }

                      const val = tfData.macdv_val;
                      const trend = tfData.macdv_trend;
                      const color = trend === 'Bullish' ? 'success.main' :
                                   trend === 'Bearish' ? 'error.main' : 'text.secondary';

                      return (
                        <TableCell key={tf} align="center">
                          <Typography variant="body2" color={color} fontWeight="medium">
                            {val?.toFixed(1) || '—'}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {trend}
                          </Typography>
                        </TableCell>
                      );
                    })}
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
};

export default MACDVIndicatorPage;
