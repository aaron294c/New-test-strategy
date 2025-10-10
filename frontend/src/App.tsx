/**
 * Main Application Component
 * RSI-MA Performance Analytics Dashboard
 */

import React, { useState } from 'react';
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

import { backtestApi } from './api/client';
import PerformanceMatrixHeatmap from './components/PerformanceMatrixHeatmap';
import ReturnDistributionChart from './components/ReturnDistributionChart';
import OptimalExitPanel from './components/OptimalExitPanel';

// Create theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#4caf50',
    },
  },
});

// Create query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const DEFAULT_TICKERS = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'QQQ', 'SPY'];

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

  // Fetch backtest data
  const { data: backtestData, isLoading, error, refetch } = useQuery({
    queryKey: ['backtest', selectedTicker],
    queryFn: () => backtestApi.getBacktestResults(selectedTicker),
  });

  const thresholdData = backtestData?.thresholds?.[selectedThreshold.toString()];

  const handleTickerChange = (event: any) => {
    setSelectedTicker(event.target.value);
  };

  const handleThresholdChange = (event: any) => {
    setSelectedThreshold(event.target.value);
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

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
        {/* Controls */}
        <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Ticker</InputLabel>
                <Select
                  value={selectedTicker}
                  onChange={handleTickerChange}
                  label="Ticker"
                >
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
                <Select
                  value={selectedThreshold}
                  onChange={handleThresholdChange}
                  label="Entry Threshold"
                >
                  <MenuItem value={5}>≤ 5%</MenuItem>
                  <MenuItem value={10}>≤ 10%</MenuItem>
                  <MenuItem value={15}>≤ 15%</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={3}>
              <Button
                variant="outlined"
                onClick={() => refetch()}
                fullWidth
                disabled={isLoading}
              >
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

        {/* Loading State */}
        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress size={60} />
          </Box>
        )}

        {/* Error State */}
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

        {/* Main Content */}
        {!isLoading && !error && thresholdData && (
          <>
            <Paper elevation={3} sx={{ mb: 3 }}>
              <Tabs value={activeTab} onChange={handleTabChange}>
                <Tab icon={<AssessmentIcon />} label="Performance Matrix" />
                <Tab icon={<ShowChartIcon />} label="Return Analysis" />
                <Tab icon={<TrendingUpIcon />} label="Optimal Exit" />
              </Tabs>
            </Paper>

            <TabPanel value={activeTab} index={0}>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <PerformanceMatrixHeatmap
                    matrix={thresholdData.performance_matrix}
                    title={`${selectedTicker} Performance Matrix (Entry ≤${selectedThreshold}%)`}
                    maxDay={21}
                  />
                </Grid>
              </Grid>
            </TabPanel>

            <TabPanel value={activeTab} index={1}>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <ReturnDistributionChart
                    returnDistributions={thresholdData.return_distributions}
                    benchmark={backtestData.benchmark}
                    title={`${selectedTicker} Return Distribution (Entry ≤${selectedThreshold}%)`}
                    maxDay={21}
                  />
                </Grid>
              </Grid>
            </TabPanel>

            <TabPanel value={activeTab} index={2}>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <OptimalExitPanel
                    optimalExit={thresholdData.optimal_exit_strategy}
                    riskMetrics={thresholdData.risk_metrics}
                    trendAnalysis={thresholdData.trend_analysis}
                    ticker={selectedTicker}
                    threshold={selectedThreshold}
                  />
                </Grid>
              </Grid>
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
