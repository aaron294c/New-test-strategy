/**
 * Live Trading Signals Component
 * Real-time actionable signals based on current market conditions
 */

import React, { useState } from 'react';
import {
  Paper,
  Typography,
  Box,
  Button,
  CircularProgress,
  Alert,
  Chip,
  TextField,
  Grid,
  Card,
  CardContent,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningIcon from '@mui/icons-material/Warning';
import InfoIcon from '@mui/icons-material/Info';
import RefreshIcon from '@mui/icons-material/Refresh';

interface LiveTradingSignalsProps {
  ticker: string;
}

const LiveTradingSignals: React.FC<LiveTradingSignalsProps> = ({ ticker }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [entrySignal, setEntrySignal] = useState<any>(null);
  const [exitSignal, setExitSignal] = useState<any>(null);

  // For exit signal tracking
  const [hasPosition, setHasPosition] = useState(false);
  const [entryPrice, setEntryPrice] = useState('');
  const [entryDate, setEntryDate] = useState('');
  const [availableDates, setAvailableDates] = useState<{start_date: string, end_date: string} | null>(null);

  // Fetch available dates when component mounts or ticker changes
  React.useEffect(() => {
    const fetchAvailableDates = async () => {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiUrl}/api/available-dates/${ticker}`);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const dates = await response.json();
        setAvailableDates(dates);
        
        // Set default entry date to latest available date
        setEntryDate(dates.end_date);
        
      } catch (err) {
        console.error('Failed to fetch available dates:', err);
      }
    };
    
    fetchAvailableDates();
  }, [ticker]);

  const fetchEntrySignal = async () => {
    setLoading(true);
    setError(null);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/live-signal/${ticker}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setEntrySignal(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch signals');
    } finally {
      setLoading(false);
    }
  };

  const fetchExitSignal = async () => {
    if (!entryPrice || parseFloat(entryPrice) <= 0) {
      setError('Please enter a valid entry price');
      return;
    }
    
    if (!entryDate || !entryDate.match(/^\d{4}-\d{2}-\d{2}$/)) {
      setError('Please enter a valid entry date (YYYY-MM-DD)');
      return;
    }

    if (availableDates) {
      const entryTimestamp = new Date(entryDate).getTime();
      const startTimestamp = new Date(availableDates.start_date).getTime();
      const endTimestamp = new Date(availableDates.end_date).getTime();
      
      if (entryTimestamp < startTimestamp || entryTimestamp > endTimestamp) {
        setError(`Entry date must be between ${availableDates.start_date} and ${availableDates.end_date}`);
        return;
      }
    }

    setLoading(true);
    setError(null);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/exit-signal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker,
          entry_price: parseFloat(entryPrice),
          entry_date: entryDate,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API Error: ${response.status}\n${errorText}`);
      }

      const result = await response.json();
      setExitSignal(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch exit signal');
    } finally {
      setLoading(false);
    }
  };

  const getSignalColor = (strength: string) => {
    if (strength === 'strong_buy') return 'success';
    if (strength === 'buy') return 'info';
    if (strength === 'neutral') return 'warning';
    return 'error';
  };

  const getUrgencyColor = (urgency: string) => {
    if (urgency === 'critical') return 'error';
    if (urgency === 'high') return 'warning';
    if (urgency === 'medium') return 'info';
    return 'success';
  };

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <TrendingUpIcon sx={{ fontSize: 32, color: 'primary.main' }} />
          <Typography variant="h5" component="h2">
            Live Trading Signals - {ticker}
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => hasPosition ? fetchExitSignal() : fetchEntrySignal()}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Real-time actionable signals based on historical analysis applied to current market conditions
      </Typography>

      {/* Position Toggle */}
      <Box sx={{ mb: 3 }}>
        <Button
          variant={!hasPosition ? 'contained' : 'outlined'}
          onClick={() => {
            setHasPosition(false);
            setExitSignal(null);
          }}
          sx={{ mr: 2 }}
        >
          Looking to Enter
        </Button>
        <Button
          variant={hasPosition ? 'contained' : 'outlined'}
          onClick={() => {
            setHasPosition(true);
            setEntrySignal(null);
          }}
        >
          Already in Position
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Entry Signal View */}
      {!hasPosition && (
        <Box>
          <Button
            variant="contained"
            onClick={fetchEntrySignal}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : <TrendingUpIcon />}
            fullWidth
            sx={{ mb: 3 }}
          >
            {loading ? 'Analyzing Market...' : 'Get Entry Signal'}
          </Button>

          {entrySignal && (
            <Grid container spacing={3}>
              {/* Main Signal Card */}
              <Grid item xs={12} md={6}>
                <Card sx={{ bgcolor: 'background.default', height: '100%' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Signal Strength
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                      <Chip
                        label={entrySignal.entry_signal.signal_strength.replace('_', ' ').toUpperCase()}
                        color={getSignalColor(entrySignal.entry_signal.signal_strength)}
                        size="large"
                        sx={{ fontSize: '1.1em', py: 3 }}
                      />
                      <Typography variant="h6">
                        Confidence: {(entrySignal.entry_signal.confidence * 100).toFixed(0)}%
                      </Typography>
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Current Price: ${entrySignal.market_context.current_price.toFixed(2)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Percentile: {entrySignal.entry_signal.current_percentile.toFixed(1)}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Recommended Size: {entrySignal.entry_signal.recommended_entry_size.toFixed(0)}% of intended position
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* Expected Returns */}
              <Grid item xs={12} md={6}>
                <Card sx={{ bgcolor: 'background.default', height: '100%' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Expected Returns (Historical)
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">7-Day:</Typography>
                        <Typography
                          variant="body2"
                          fontWeight="bold"
                          color={entrySignal.entry_signal.expected_return_7d > 0 ? 'success.main' : 'error.main'}
                        >
                          {entrySignal.entry_signal.expected_return_7d > 0 ? '+' : ''}
                          {entrySignal.entry_signal.expected_return_7d.toFixed(2)}%
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">14-Day:</Typography>
                        <Typography
                          variant="body2"
                          fontWeight="bold"
                          color={entrySignal.entry_signal.expected_return_14d > 0 ? 'success.main' : 'error.main'}
                        >
                          {entrySignal.entry_signal.expected_return_14d > 0 ? '+' : ''}
                          {entrySignal.entry_signal.expected_return_14d.toFixed(2)}%
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">21-Day:</Typography>
                        <Typography
                          variant="body2"
                          fontWeight="bold"
                          color={entrySignal.entry_signal.expected_return_21d > 0 ? 'success.main' : 'error.main'}
                        >
                          {entrySignal.entry_signal.expected_return_21d > 0 ? '+' : ''}
                          {entrySignal.entry_signal.expected_return_21d.toFixed(2)}%
                        </Typography>
                      </Box>
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    <Typography variant="body2" color="text.secondary">
                      Win Rate: {(entrySignal.entry_signal.win_rate_historical * 100).toFixed(1)}%
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* Reasoning */}
              <Grid item xs={12}>
                <Card sx={{ bgcolor: 'success.light' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      📊 Why This Signal?
                    </Typography>
                    <List dense>
                      {entrySignal.entry_signal.reasoning.map((reason: string, idx: number) => (
                        <ListItem key={idx}>
                          <ListItemIcon>
                            <CheckCircleIcon color="success" />
                          </ListItemIcon>
                          <ListItemText primary={reason} />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              </Grid>

              {/* Risk Factors */}
              {entrySignal.entry_signal.risk_factors.length > 0 && (
                <Grid item xs={12}>
                  <Card sx={{ bgcolor: 'warning.light' }}>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        ⚠️ Risk Factors
                      </Typography>
                      <List dense>
                        {entrySignal.entry_signal.risk_factors.map((risk: string, idx: number) => (
                          <ListItem key={idx}>
                            <ListItemIcon>
                              <WarningIcon color="warning" />
                            </ListItemIcon>
                            <ListItemText primary={risk} />
                          </ListItem>
                        ))}
                      </List>
                    </CardContent>
                  </Card>
                </Grid>
              )}

              {/* Market Context */}
              <Grid item xs={12}>
                <Card sx={{ bgcolor: 'background.default' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Market Context
                    </Typography>
                    <Typography variant="body2">
                      52-Week High: ${entrySignal.market_context['52w_high'].toFixed(2)} (
                      {entrySignal.market_context.distance_from_52w_high_pct.toFixed(1)}% from current)
                    </Typography>
                    <Typography variant="body2">
                      52-Week Low: ${entrySignal.market_context['52w_low'].toFixed(2)} (
                      {entrySignal.market_context.distance_from_52w_low_pct.toFixed(1)}% from current)
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </Box>
      )}

      {/* Exit Signal View */}
      {hasPosition && (
        <Box>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Entry Price"
                type="number"
                fullWidth
                value={entryPrice}
                onChange={(e) => setEntryPrice(e.target.value)}
                placeholder="e.g., 225.50"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Entry Date"
                type="date"
                fullWidth
                value={entryDate}
                onChange={(e) => setEntryDate(e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
          </Grid>

          <Button
            variant="contained"
            onClick={fetchExitSignal}
            disabled={loading || !entryPrice || !entryDate}
            startIcon={loading ? <CircularProgress size={20} /> : <TrendingDownIcon />}
            fullWidth
            sx={{ mb: 3 }}
          >
            {loading ? 'Analyzing Position...' : 'Get Exit Signal'}
          </Button>

          {exitSignal && (
            <Grid container spacing={3}>
              {/* Exit Recommendation */}
              <Grid item xs={12} md={6}>
                <Card sx={{ bgcolor: 'background.default', height: '100%' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Recommended Action
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                      <Chip
                        label={exitSignal.exit_signal.recommended_action.replace(/_/g, ' ').toUpperCase()}
                        color={
                          exitSignal.exit_signal.recommended_action === 'hold'
                            ? 'success'
                            : exitSignal.exit_signal.recommended_action.includes('reduce_25')
                            ? 'info'
                            : 'error'
                        }
                        size="large"
                        sx={{ fontSize: '1.1em', py: 3 }}
                      />
                      <Chip
                        label={`Urgency: ${exitSignal.exit_signal.urgency.toUpperCase()}`}
                        color={getUrgencyColor(exitSignal.exit_signal.urgency)}
                      />
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Current Return:{' '}
                      <span
                        style={{
                          color: exitSignal.exit_signal.current_return > 0 ? 'green' : 'red',
                          fontWeight: 'bold',
                        }}
                      >
                        {exitSignal.exit_signal.current_return > 0 ? '+' : ''}
                        {exitSignal.exit_signal.current_return.toFixed(2)}%
                      </span>
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Days Held: {exitSignal.exit_signal.days_held}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Exit Pressure: {exitSignal.exit_signal.exit_pressure.toFixed(0)}/100
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* Expectancy Comparison */}
              <Grid item xs={12} md={6}>
                <Card sx={{ bgcolor: 'background.default', height: '100%' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Expected Returns
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          If Hold 7 More Days:
                        </Typography>
                        <Typography
                          variant="h6"
                          color={
                            exitSignal.exit_signal.expected_return_if_hold_7d > 0
                              ? 'success.main'
                              : 'error.main'
                          }
                        >
                          {exitSignal.exit_signal.expected_return_if_hold_7d > 0 ? '+' : ''}
                          {exitSignal.exit_signal.expected_return_if_hold_7d.toFixed(2)}%
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          If Exit Now:
                        </Typography>
                        <Typography
                          variant="h6"
                          color={
                            exitSignal.exit_signal.expected_return_if_exit_now > 0
                              ? 'success.main'
                              : 'error.main'
                          }
                        >
                          {exitSignal.exit_signal.expected_return_if_exit_now > 0 ? '+' : ''}
                          {exitSignal.exit_signal.expected_return_if_exit_now.toFixed(2)}%
                        </Typography>
                      </Box>
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    <Typography variant="body2" color="text.secondary">
                      Trailing Stop: ${exitSignal.exit_signal.trailing_stop.toFixed(2)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* Reasoning */}
              <Grid item xs={12}>
                <Card sx={{ bgcolor: 'info.light' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      📊 Analysis
                    </Typography>
                    <List dense>
                      {exitSignal.exit_signal.reasoning.map((reason: string, idx: number) => (
                        <ListItem key={idx}>
                          <ListItemIcon>
                            <InfoIcon color="info" />
                          </ListItemIcon>
                          <ListItemText primary={reason} />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </Box>
      )}

      {!entrySignal && !exitSignal && !loading && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body1" color="text.secondary">
            {hasPosition
              ? 'Enter your position details and click "Get Exit Signal" for real-time exit recommendations'
              : 'Click "Get Entry Signal" to see if now is a good time to enter'}
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default LiveTradingSignals;
