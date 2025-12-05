/**
 * Trade Simulation Viewer Component
 * Shows day-by-day trade management decisions with exit pressure, state, and recommendations
 */

import React, { useState } from 'react';
import {
  Paper,
  Typography,
  Box,
  Button,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  TextField,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';

interface TradeSimulationViewerProps {
  ticker: string;
}

const TradeSimulationViewer: React.FC<TradeSimulationViewerProps> = ({ ticker }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [simulation, setSimulation] = useState<any>(null);
  const [entryPercentile, setEntryPercentile] = useState(5.0);
  const [daysToSimulate, setDaysToSimulate] = useState(21);

  const fetchSimulation = async () => {
    setLoading(true);
    setError(null);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(
        `${apiUrl}/api/trade-simulation/${ticker}?entry_percentile=${entryPercentile}&days_to_simulate=${daysToSimulate}`
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setSimulation(result.simulation);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch simulation');
    } finally {
      setLoading(false);
    }
  };

  const getStateColor = (state: string): 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error' => {
    if (state.includes('rebound')) return 'success';
    if (state.includes('momentum')) return 'primary';
    if (state.includes('acceleration')) return 'warning';
    if (state.includes('distribution')) return 'error';
    if (state.includes('reversal')) return 'error';
    return 'default';
  };

  const getActionColor = (action: string): 'default' | 'success' | 'warning' | 'error' => {
    if (action === 'hold') return 'success';
    if (action === 'reduce_25') return 'warning';
    if (action.includes('reduce')) return 'error';
    if (action === 'exit_all') return 'error';
    return 'default';
  };

  const getPressureColor = (pressure: number) => {
    if (pressure < 40) return 'success.main';
    if (pressure < 60) return 'warning.main';
    return 'error.main';
  };

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PlayArrowIcon sx={{ fontSize: 32, color: 'primary.main' }} />
          <Typography variant="h5" component="h2">
            Trade Simulation
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField
            label="Entry Percentile"
            type="number"
            size="small"
            value={entryPercentile}
            onChange={(e) => setEntryPercentile(Number(e.target.value))}
            sx={{ width: 140 }}
            inputProps={{ min: 1, max: 20, step: 0.5 }}
          />
          <TextField
            label="Days to Simulate"
            type="number"
            size="small"
            value={daysToSimulate}
            onChange={(e) => setDaysToSimulate(Number(e.target.value))}
            sx={{ width: 140 }}
            inputProps={{ min: 7, max: 30 }}
          />
          <Button
            variant="contained"
            onClick={fetchSimulation}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : <PlayArrowIcon />}
          >
            {loading ? 'Simulating...' : 'Run Simulation'}
          </Button>
        </Box>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Simulate a trade for {ticker} with day-by-day exit pressure, state evolution, and management decisions
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {simulation && (
        <>
          {/* Summary */}
          <Box sx={{ mb: 3 }}>
            <Alert
              severity={simulation.final_return > 0 ? 'success' : 'error'}
              icon={simulation.final_return > 0 ? <TrendingUpIcon /> : <TrendingDownIcon />}
            >
              <Typography variant="body2">
                <strong>Entry:</strong> {new Date(simulation.entry_date).toLocaleDateString()} @ $
                {simulation.entry_price.toFixed(2)} ({simulation.entry_percentile.toFixed(1)}th percentile)
                <br />
                <strong>Days Held:</strong> {simulation.total_days_held} days
                <br />
                <strong>Final Return:</strong>{' '}
                <span style={{ fontSize: '1.1em', fontWeight: 'bold' }}>
                  {simulation.final_return > 0 ? '+' : ''}
                  {simulation.final_return.toFixed(2)}%
                </span>
              </Typography>
            </Alert>
          </Box>

          {/* Exit Reasoning Summary */}
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2" fontWeight="bold" gutterBottom>
              Exit Decision Framework:
            </Typography>
            <Typography variant="caption" component="div">
              • <strong>Exit Pressure (0-100):</strong> Velocity({simulation.daily_analysis[0]?.exit_pressure.percentile_velocity_component.toFixed(0)}) + Time({simulation.daily_analysis[0]?.exit_pressure.time_decay_component.toFixed(0)}) + Divergence({simulation.daily_analysis[0]?.exit_pressure.divergence_component.toFixed(0)}) + Volatility({simulation.daily_analysis[0]?.exit_pressure.volatility_component.toFixed(0)})
              <br />
              • <strong>Velocity:</strong> Percentile rising too fast = exhaustion signal
              <br />
              • <strong>Divergence:</strong> Daily vs 4h momentum mismatch = distribution
              <br />
              • <strong>Time Decay:</strong> Edge diminishes as trade ages
              <br />
              • <strong>Trade State:</strong> Lifecycle position (Rebound→Momentum→Acceleration→Distribution→Reversal)
            </Typography>
          </Alert>

          {/* Day-by-Day Analysis */}
          <Typography variant="h6" gutterBottom>
            Day-by-Day Analysis
          </Typography>

          <TableContainer sx={{ maxHeight: 500 }}>
            <Table stickyHeader size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Day</strong></TableCell>
                  <TableCell align="right"><strong>Price</strong></TableCell>
                  <TableCell align="right"><strong>Return</strong></TableCell>
                  <TableCell><strong>Exit Pressure</strong></TableCell>
                  <TableCell><strong>Trade State</strong></TableCell>
                  <TableCell><strong>Action</strong></TableCell>
                  <TableCell align="right"><strong>Stop</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {simulation.daily_analysis.map((day: any) => (
                  <TableRow
                    key={day.day}
                    sx={{
                      bgcolor: day.triggered_stop ? 'error.light' :
                              day.triggered_exit_signal ? 'warning.light' :
                              'transparent'
                    }}
                  >
                    <TableCell>
                      <strong>D{day.day}</strong>
                    </TableCell>
                    <TableCell align="right">
                      ${day.price.toFixed(2)}
                    </TableCell>
                    <TableCell align="right">
                      <Typography
                        variant="body2"
                        color={day.return_pct > 0 ? 'success.main' : 'error.main'}
                        fontWeight="bold"
                      >
                        {day.return_pct > 0 ? '+' : ''}
                        {day.return_pct.toFixed(2)}%
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box sx={{ width: 100 }}>
                          <LinearProgress
                            variant="determinate"
                            value={Math.min(day.exit_pressure.overall_pressure, 100)}
                            color={
                              day.exit_pressure.overall_pressure < 40 ? 'success' :
                              day.exit_pressure.overall_pressure < 70 ? 'warning' : 'error'
                            }
                          />
                        </Box>
                        <Typography
                          variant="caption"
                          color={getPressureColor(day.exit_pressure.overall_pressure)}
                          fontWeight="bold"
                        >
                          {day.exit_pressure.overall_pressure.toFixed(0)}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={day.trade_state.current_state.replace(/_/g, ' ').toUpperCase()}
                        size="small"
                        color={getStateColor(day.trade_state.current_state)}
                      />
                    </TableCell>
                    <TableCell>
                      <Box>
                        <Chip
                          label={day.exposure_recommendation.action.replace(/_/g, ' ').toUpperCase()}
                          size="small"
                          color={getActionColor(day.exposure_recommendation.action)}
                        />
                        <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                          {day.exit_pressure.overall_pressure >= 70 && "⚠️ High pressure"}
                          {day.trade_state.current_state.includes('distribution') && " 📉 Distribution"}
                          {day.trade_state.current_state.includes('reversal') && " 🔄 Reversal"}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      {day.triggered_stop ? (
                        <Chip label="🛑 HIT" size="small" color="error" />
                      ) : (
                        <Typography variant="caption">
                          ${day.trailing_stop.toFixed(2)}
                        </Typography>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Detailed Exit Pressure Breakdown */}
          <Box sx={{ mt: 3 }}>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">📊 Exit Pressure Component Breakdown (WHY Exit?)</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Alert severity="warning" sx={{ mb: 2 }}>
                  <Typography variant="body2" fontWeight="bold">
                    Understanding Exit Signals:
                  </Typography>
                  <Typography variant="caption" component="div">
                    • <strong>Velocity (0-25):</strong> Percentile rising &gt;5pts/day = exhaustion. Fast moves up often reverse quickly.<br />
                    • <strong>Time Decay (0-20):</strong> Edge diminishes exponentially. Longer holds = higher risk of reversal.<br />
                    • <strong>Divergence (0-25):</strong> Daily momentum vs 4h approx. Mismatch = institutional selling (distribution).<br />
                    • <strong>Volatility (5-30):</strong> High vol regime = wider swings, higher exit bias for protection.<br />
                    • <strong>Total &gt;70 = STRONG EXIT SIGNAL</strong><br />
                    • <strong>Total 50-70 = Consider partial exit</strong><br />
                    • <strong>Total &lt;50 = Hold position</strong>
                  </Typography>
                </Alert>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell><strong>Day</strong></TableCell>
                        <TableCell align="right"><strong>Velocity</strong></TableCell>
                        <TableCell align="right"><strong>Time Decay</strong></TableCell>
                        <TableCell align="right"><strong>Divergence</strong></TableCell>
                        <TableCell align="right"><strong>Volatility</strong></TableCell>
                        <TableCell align="right"><strong>Total</strong></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {simulation.daily_analysis.slice(0, 10).map((day: any) => (
                        <TableRow key={day.day}>
                          <TableCell>D{day.day}</TableCell>
                          <TableCell align="right">
                            {day.exit_pressure.percentile_velocity_component.toFixed(1)}
                          </TableCell>
                          <TableCell align="right">
                            {day.exit_pressure.time_decay_component.toFixed(1)}
                          </TableCell>
                          <TableCell align="right">
                            {day.exit_pressure.divergence_component.toFixed(1)}
                          </TableCell>
                          <TableCell align="right">
                            {day.exit_pressure.volatility_component.toFixed(1)}
                          </TableCell>
                          <TableCell align="right">
                            <strong>{day.exit_pressure.overall_pressure.toFixed(1)}</strong>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </AccordionDetails>
            </Accordion>
          </Box>
        </>
      )}

      {!simulation && !loading && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body1" color="text.secondary">
            Click "Run Simulation" to see day-by-day trade management
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default TradeSimulationViewer;
