/**
 * Main Application Component
 * RSI-MA Performance Analytics Dashboard
 */

import React, { useMemo, useState } from 'react';
import {
  AppBar,
  Box,
  Container,
  CssBaseline,
  Toolbar,
  Typography,
  ThemeProvider,
  createTheme,
  Paper,
  Grid,
  Tab,
  Tabs,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  CircularProgress,
} from '@mui/material';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import AssessmentIcon from '@mui/icons-material/Assessment';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import TimelineIcon from '@mui/icons-material/Timeline';

import { backtestApi } from './api/client';

// Tab-level code-splitting
const MultiTimeframeGuide = React.lazy(() => import('./components/MultiTimeframeGuide'));
const SwingTradingFramework = React.lazy(() => import('./components/TradingFramework/SwingTradingFramework'));
const MultiTimeframeDivergence = React.lazy(() => import('./components/MultiTimeframeDivergence'));
const PercentileForwardMapper = React.lazy(() => import('./components/PercentileForwardMapper'));
const RSIIndicatorPage = React.lazy(() => import('./pages/RSIIndicatorPage'));
const MBADIndicatorPage = React.lazy(() => import('./pages/MBADIndicatorPage'));
const PerformanceMatrixHeatmap = React.lazy(() => import('./components/PerformanceMatrixHeatmap'));
const EnhancedPerformanceMatrix = React.lazy(() => import('./components/EnhancedPerformanceMatrix'));
const TradeSimulationViewer = React.lazy(() => import('./components/TradeSimulationViewer'));
const GammaScannerTab = React.lazy(() =>
  import('./components/GammaScanner').then((m) => ({ default: m.GammaScannerTab }))
);
const RiskDistanceTab = React.lazy(() =>
  import('./components/RiskDistance').then((m) => ({ default: m.RiskDistanceTab }))
);
const LowerExtensionPage = React.lazy(() => import('./pages/LowerExtensionPage'));
const WeightedFourierTransformPage = React.lazy(() => import('./pages/WeightedFourierTransformPage'));
const LEAPSStrategyPanel = React.lazy(() => import('./components/LEAPSScanner/LEAPSStrategyPanel'));
const DailyTrendScannerPage = React.lazy(() => import('./pages/DailyTrendScannerPage'));
const RSIChebyshevLeadingPage = React.lazy(() => import('./pages/RSIChebyshevLeadingPage'));
const RSIChebyshevProPage = React.lazy(() => import('./pages/RSIChebyshevProPage'));
const MAPIIndicatorPage = React.lazy(() => import('./pages/MAPIIndicatorPage'));
const MACDVIndicatorPage = React.lazy(() => import('./pages/MACDVIndicatorPage'));

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#2962FF' },
    secondary: { main: '#4caf50' },
    background: { default: '#131722', paper: '#1E222D' },
    text: { primary: '#D1D4DC', secondary: '#787B86' },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: { backgroundImage: 'none' },
      },
    },
  },
});

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { refetchOnWindowFocus: false, retry: 1 },
  },
});

const DEFAULT_TICKERS = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'QQQ', 'SPY', 'GLD', 'SLV', 'TSLA', 'NFLX', 'BRK-B', 'WMT', 'UNH', 'AVGO', 'LLY', 'TSM', 'ORCL', 'OXY', 'XOM', 'CVX', 'JPM', 'BAC', 'CNX1', 'CSP1', 'BTCUSD', 'ES1', 'NQ1', 'VIX', 'IGLS', 'USDGBP', 'US10'];

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

function Dashboard() {
  const [selectedTicker, setSelectedTicker] = useState('AAPL');
  const [selectedThreshold, setSelectedThreshold] = useState<number>(5);
  const [activeTab, setActiveTab] = useState(0);

  const suspenseFallback = useMemo(
    () => (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress size={44} />
      </Box>
    ),
    []
  );

  const { data: backtestData, isLoading, error, refetch } = useQuery({
    queryKey: ['backtest', selectedTicker],
    queryFn: () => backtestApi.getBacktestResults(selectedTicker),
    staleTime: 5 * 60 * 1000,
  });

  const { data: rsiChartData, isLoading: isLoadingRSIChart, refetch: refetchRSIChart } = useQuery({
    queryKey: ['rsiChart', selectedTicker, 252],
    queryFn: () => backtestApi.getRSIChartData(selectedTicker, 252),
    enabled: activeTab === 4,
    staleTime: 5 * 60 * 1000,
  });

  const thresholdData = backtestData?.thresholds?.[selectedThreshold.toFixed(1)];

  const handleTickerChange = (event: any) => setSelectedTicker(event.target.value);
  const handleThresholdChange = (event: any) => setSelectedThreshold(event.target.value);
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => setActiveTab(newValue);

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static" elevation={2}>
        <Toolbar>
          <TrendingUpIcon sx={{ mr: 2, fontSize: 32 }} />
          <Typography variant="h5" component="div" sx={{ flexGrow: 1 }}>
            RSI-MA Performance Analytics Dashboard
          </Typography>
          <Typography variant="subtitle2" sx={{ opacity: 0.9 }}>
            D1-D21 Backtest Analysis
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Ticker</InputLabel>
                <Select value={selectedTicker} onChange={handleTickerChange} label="Ticker">
                  {DEFAULT_TICKERS.map((ticker) => (
                    <MenuItem key={ticker} value={ticker}>
                      {ticker}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Entry Threshold</InputLabel>
                <Select value={selectedThreshold} onChange={handleThresholdChange} label="Entry Threshold">
                  <MenuItem value={5}>ƒ%Ï 5%</MenuItem>
                  <MenuItem value={10}>ƒ%Ï 10%</MenuItem>
                  <MenuItem value={15}>ƒ%Ï 15%</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={3}>
              <Button variant="outlined" onClick={() => refetch()} fullWidth disabled={isLoading}>
                {isLoading ? <CircularProgress size={24} /> : 'Refresh Data'}
              </Button>
            </Grid>

            <Grid item xs={12} md={3}>
              {thresholdData && (
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h6" color="primary">
                    {thresholdData.events}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Total Events
                  </Typography>
                </Box>
              )}
            </Grid>
          </Grid>
        </Paper>

        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress size={60} />
          </Box>
        )}

        {error && (
          <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
            <Typography color="error" variant="h6">
              Error loading data: {(error as Error).message}
            </Typography>
            <Button onClick={() => refetch()} sx={{ mt: 2 }}>
              Retry
            </Button>
          </Paper>
        )}

        {!isLoading && !error && thresholdData && (
          <>
            <Paper elevation={3} sx={{ mb: 3 }}>
              <Tabs value={activeTab} onChange={handleTabChange} variant="scrollable" scrollButtons="auto">
                <Tab icon={<TrendingUpIcon />} label="Trading Guide" />
                <Tab icon={<AssessmentIcon />} label="Swing Framework" />
                <Tab icon={<TimelineIcon />} label="Multi-Timeframe Divergence" />
                <Tab icon={<ShowChartIcon />} label="Percentile Forward Mapping" />
                <Tab icon={<TimelineIcon />} label="RSI Indicator" />
                <Tab icon={<TimelineIcon />} label="MBAD Indicator" />
                <Tab icon={<AssessmentIcon />} label="Performance Matrix" />
                <Tab icon={<ShowChartIcon />} label="Trade Simulation" />
                <Tab icon={<AssessmentIcon />} label="Gamma Wall Scanner" />
                <Tab icon={<ShowChartIcon />} label="Risk Distance" />
                <Tab icon={<TrendingUpIcon />} label="Lower Extension" />
                <Tab icon={<TimelineIcon />} label="WFT Spectral Gating" />
                <Tab icon={<TrendingUpIcon />} label="LEAPS Scanner" />
                <Tab icon={<ShowChartIcon />} label="Daily Trend Scanner" />
                <Tab icon={<TimelineIcon />} label="RSI Chebyshev Leading" />
                <Tab icon={<ShowChartIcon />} label="RSI Chebyshev Pro (TV)" />
                <Tab icon={<TrendingUpIcon />} label="MAPI (Momentum)" />
                <Tab icon={<ShowChartIcon />} label="MACD-V (Momentum)" />
              </Tabs>
            </Paper>

            <TabPanel value={activeTab} index={0}>
              <React.Suspense fallback={suspenseFallback}>
                <MultiTimeframeGuide ticker={selectedTicker} />
              </React.Suspense>
            </TabPanel>

            <TabPanel value={activeTab} index={1}>
              <React.Suspense fallback={suspenseFallback}>
                <SwingTradingFramework ticker={selectedTicker} />
              </React.Suspense>
            </TabPanel>

            <TabPanel value={activeTab} index={2}>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <React.Suspense fallback={suspenseFallback}>
                    <MultiTimeframeDivergence ticker={selectedTicker} />
                  </React.Suspense>
                </Grid>
              </Grid>
            </TabPanel>

            <TabPanel value={activeTab} index={3}>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <React.Suspense fallback={suspenseFallback}>
                    <PercentileForwardMapper ticker={selectedTicker} />
                  </React.Suspense>
                </Grid>
              </Grid>
            </TabPanel>

            <TabPanel value={activeTab} index={4}>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <React.Suspense fallback={suspenseFallback}>
                    <RSIIndicatorPage
                      data={rsiChartData || null}
                      ticker={selectedTicker}
                      isLoading={isLoadingRSIChart}
                      onRefresh={() => refetchRSIChart()}
                    />
                  </React.Suspense>
                </Grid>
              </Grid>
            </TabPanel>

            <TabPanel value={activeTab} index={5}>
              <React.Suspense fallback={suspenseFallback}>
                <MBADIndicatorPage ticker={selectedTicker} />
              </React.Suspense>
            </TabPanel>

            <TabPanel value={activeTab} index={6}>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <React.Suspense fallback={suspenseFallback}>
                    <PerformanceMatrixHeatmap
                      matrix={thresholdData.performance_matrix}
                      title={`${selectedTicker} Performance Heatmap (Entry ƒ%Ï${selectedThreshold}%)`}
                      maxDay={21}
                    />
                  </React.Suspense>
                </Grid>
                <Grid item xs={12}>
                  <React.Suspense fallback={suspenseFallback}>
                    <EnhancedPerformanceMatrix
                      matrix={thresholdData.performance_matrix}
                      winRates={thresholdData.win_rates}
                      returnDistributions={thresholdData.return_distributions}
                      title={`${selectedTicker} Complete Performance Matrix (Entry ƒ%Ï${selectedThreshold}%)`}
                      maxDay={21}
                    />
                  </React.Suspense>
                </Grid>
              </Grid>
            </TabPanel>

            <TabPanel value={activeTab} index={7}>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <React.Suspense fallback={suspenseFallback}>
                    <TradeSimulationViewer ticker={selectedTicker} />
                  </React.Suspense>
                </Grid>
              </Grid>
            </TabPanel>

            <TabPanel value={activeTab} index={8}>
              <React.Suspense fallback={suspenseFallback}>
                <GammaScannerTab />
              </React.Suspense>
            </TabPanel>

            <TabPanel value={activeTab} index={9}>
              <React.Suspense fallback={suspenseFallback}>
                <RiskDistanceTab />
              </React.Suspense>
            </TabPanel>

            <TabPanel value={activeTab} index={10}>
              <React.Suspense fallback={suspenseFallback}>
                <LowerExtensionPage />
              </React.Suspense>
            </TabPanel>

            <TabPanel value={activeTab} index={11}>
              <React.Suspense fallback={suspenseFallback}>
                <WeightedFourierTransformPage ticker={selectedTicker} />
              </React.Suspense>
            </TabPanel>

            <TabPanel value={activeTab} index={12}>
              <React.Suspense fallback={suspenseFallback}>
                <LEAPSStrategyPanel />
              </React.Suspense>
            </TabPanel>

            <TabPanel value={activeTab} index={13}>
              <React.Suspense fallback={suspenseFallback}>
                <DailyTrendScannerPage ticker={selectedTicker} />
              </React.Suspense>
            </TabPanel>

            <TabPanel value={activeTab} index={14}>
              <React.Suspense fallback={suspenseFallback}>
                <RSIChebyshevLeadingPage ticker={selectedTicker} />
              </React.Suspense>
            </TabPanel>

            <TabPanel value={activeTab} index={15}>
              <React.Suspense fallback={suspenseFallback}>
                <RSIChebyshevProPage ticker={selectedTicker} />
              </React.Suspense>
            </TabPanel>

            {/* Tab 16: MAPI (Momentum-Adapted Percentile Indicator) */}
            <TabPanel value={activeTab} index={16}>
              <React.Suspense fallback={suspenseFallback}>
                <MAPIIndicatorPage ticker={selectedTicker} />
              </React.Suspense>
            </TabPanel>

            {/* Tab 17: MACD-V (MACD Volatility-Normalized) */}
            <TabPanel value={activeTab} index={17}>
              <React.Suspense fallback={suspenseFallback}>
                <MACDVIndicatorPage ticker={selectedTicker} />
              </React.Suspense>
            </TabPanel>
          </>
        )}
      </Container>
    </Box>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Dashboard />
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
