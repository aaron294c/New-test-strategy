/**
 * LEAPS Strategy Panel Component
 *
 * Displays VIX-based LEAPS options strategy recommendations.
 * Fetches current VIX level and provides actionable trading strategies
 * based on volatility environment.
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Button,
  CircularProgress,
  Alert,
  Divider,
  Paper,
  Stack,
  Tabs,
  Tab,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import RemoveIcon from '@mui/icons-material/Remove';
import TimelineIcon from '@mui/icons-material/Timeline';
import ListIcon from '@mui/icons-material/List';
import AssessmentIcon from '@mui/icons-material/Assessment';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import LEAPSOpportunitiesTable from './LEAPSOpportunitiesTable';
import LEAPSPerformanceAlerts from './LEAPSPerformanceAlerts';

// Backend API base URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Type definitions
interface VIXContext {
  environment: string;
  description: string;
  percentile_context: string;
}

interface Recommendations {
  delta_range: [number, number];
  extrinsic_pct_max: number;
  strike_depth_pct: [number, number];
  vega_range: [number, number];
}

interface LEAPSStrategyData {
  vix_current: number;
  vix_percentile: number;
  strategy: string;
  strategy_full: string;
  recommendations: Recommendations;
  rationale: string;
  vega_exposure: string;
  key_filters: string[];
  vix_context: VIXContext;
  timestamp: string;
  error?: string;
}

// Fetch LEAPS strategy data
const fetchLEAPSStrategy = async (): Promise<LEAPSStrategyData> => {
  const response = await axios.get(`${API_BASE_URL}/api/leaps/vix-strategy`);
  return response.data;
};

// Helper function to get VIX color based on level
const getVIXColor = (vix: number): string => {
  if (vix < 15) return 'success';
  if (vix <= 20) return 'warning';
  return 'error';
};

// Helper function to get VIX icon
const getVIXIcon = (vix: number) => {
  if (vix < 15) return <TrendingDownIcon />;
  if (vix <= 20) return <RemoveIcon />;
  return <TrendingUpIcon />;
};

// Helper function to get strategy color
const getStrategyColor = (strategy: string): 'success' | 'warning' | 'error' => {
  if (strategy === 'ATM') return 'success';
  if (strategy === 'MODERATE_ITM') return 'warning';
  return 'error';
};

export const LEAPSStrategyPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['leaps-strategy'],
    queryFn: fetchLEAPSStrategy,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 5 * 60 * 1000, // Auto-refresh every 5 minutes
  });

  const handleRefresh = () => {
    refetch();
  };

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        Failed to fetch LEAPS strategy data. Please try again later.
        <br />
        Error: {error instanceof Error ? error.message : 'Unknown error'}
      </Alert>
    );
  }

  if (!data) {
    return (
      <Alert severity="info" sx={{ mb: 3 }}>
        No LEAPS strategy data available.
      </Alert>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header with Tabs */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h4">
            LEAPS Options Scanner
          </Typography>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            size="small"
          >
            Refresh
          </Button>
        </Box>

        <Tabs value={activeTab} onChange={handleTabChange} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tab icon={<TimelineIcon />} label="Strategy Overview" iconPosition="start" />
          <Tab icon={<ListIcon />} label="Opportunities" iconPosition="start" />
          <Tab icon={<AssessmentIcon />} label="Performance & Alerts" iconPosition="start" />
        </Tabs>
      </Box>

      {/* Strategy Overview Tab */}
      {activeTab === 0 && (
        <Box>
          {/* Show warning if VIX fetch had error */}
          {data.error && (
            <Alert severity="warning" sx={{ mb: 3 }}>
              Using fallback VIX data. Live data unavailable: {data.error}
            </Alert>
          )}

          {/* VIX Display Card */}
      <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #1E222D 0%, #2A2E3A 100%)' }}>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={4}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Current VIX Level
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 2 }}>
                  <Typography variant="h2" sx={{ fontWeight: 'bold' }}>
                    {data.vix_current.toFixed(2)}
                  </Typography>
                  <Chip
                    icon={getVIXIcon(data.vix_current)}
                    label={`P${data.vix_percentile}`}
                    color={getVIXColor(data.vix_current) as any}
                    size="medium"
                    sx={{ fontSize: '1.1rem', py: 2 }}
                  />
                </Box>
              </Box>
            </Grid>

            <Grid item xs={12} md={4}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  VIX Environment
                </Typography>
                <Typography variant="h6" gutterBottom>
                  {data.vix_context.environment.replace(/_/g, ' ')}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {data.vix_context.description}
                </Typography>
              </Box>
            </Grid>

            <Grid item xs={12} md={4}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Historical Context
                </Typography>
                <Typography variant="body1">
                  {data.vix_context.percentile_context}
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Strategy Recommendation Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Typography variant="h5">Recommended Strategy</Typography>
            <Chip
              label={data.strategy_full}
              color={getStrategyColor(data.strategy)}
              size="medium"
            />
          </Box>

          <Divider sx={{ my: 2 }} />

          <Typography variant="body1" paragraph sx={{ lineHeight: 1.8 }}>
            {data.rationale}
          </Typography>

          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              <strong>Vega Exposure:</strong>
            </Typography>
            <Typography variant="body2">
              {data.vega_exposure}
            </Typography>
          </Alert>
        </CardContent>
      </Card>

      {/* Recommendations Grid */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 3, height: '100%', bgcolor: '#1E222D' }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Delta Range
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#4caf50' }}>
              {data.recommendations.delta_range[0].toFixed(2)} - {data.recommendations.delta_range[1].toFixed(2)}
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 3, height: '100%', bgcolor: '#1E222D' }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Max Extrinsic %
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#2962FF' }}>
              {data.recommendations.extrinsic_pct_max}%
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 3, height: '100%', bgcolor: '#1E222D' }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Strike Depth (ITM %)
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#ff9800' }}>
              {data.recommendations.strike_depth_pct[0]}% - {data.recommendations.strike_depth_pct[1]}%
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 3, height: '100%', bgcolor: '#1E222D' }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Vega Range
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#e91e63' }}>
              {data.recommendations.vega_range[0].toFixed(2)} - {data.recommendations.vega_range[1].toFixed(2)}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Key Filters Card */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Key Filtering Criteria
          </Typography>
          <Divider sx={{ my: 2 }} />
          <Stack spacing={1.5}>
            {data.key_filters.map((filter, index) => (
              <Box
                key={index}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  p: 1.5,
                  bgcolor: '#1E222D',
                  borderRadius: 1,
                }}
              >
                <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                  • {filter}
                </Typography>
              </Box>
            ))}
          </Stack>
        </CardContent>
      </Card>

          {/* Footer with timestamp */}
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              Last updated: {new Date(data.timestamp).toLocaleString()}
            </Typography>
          </Box>
        </Box>
      )}

      {/* Opportunities Tab */}
      {activeTab === 1 && (
        <Box>
          <LEAPSOpportunitiesTable initialStrategy={data?.strategy} />
        </Box>
      )}

      {/* Performance & Alerts Tab */}
      {activeTab === 2 && (
        <Box>
          <LEAPSPerformanceAlerts />
        </Box>
      )}
    </Box>
  );
};

export default LEAPSStrategyPanel;
