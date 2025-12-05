/**
 * Exit Strategy Comparison Component
 * Compares different exit strategies (Buy & Hold, Trailing Stop, Exit Pressure, etc.)
 */

import React, { useState } from 'react';
import {
  Paper,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  CircularProgress,
  Alert,
  Chip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';

interface StrategyPerformance {
  strategy_name: string;
  total_trades: number;
  avg_return: number;
  median_return: number;
  win_rate: number;
  avg_hold_days: number;
  sharpe_ratio: number;
  max_drawdown: number;
  profit_factor: number;
  expectancy: number;
}

interface ExitStrategyComparisonProps {
  ticker: string;
  threshold: number;
}

const ExitStrategyComparison: React.FC<ExitStrategyComparisonProps> = ({
  ticker,
  threshold,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<any>(null);
  const [maxHoldDays, setMaxHoldDays] = useState(21);

  const fetchComparison = async () => {
    setLoading(true);
    setError(null);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/advanced-backtest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker,
          threshold,
          max_hold_days: maxHoldDays,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch comparison');
    } finally {
      setLoading(false);
    }
  };

  const getBestStrategy = () => {
    if (!data?.strategy_comparison) return null;

    const strategies = [
      data.strategy_comparison.buy_and_hold,
      data.strategy_comparison.trailing_stop_atr,
      data.strategy_comparison.adaptive_exit_pressure,
      data.strategy_comparison.conditional_expectancy,
    ];

    return strategies.reduce((best, current) =>
      current.sharpe_ratio > best.sharpe_ratio ? current : best
    );
  };

  const renderStrategyRow = (strategy: StrategyPerformance, isBest: boolean) => (
    <TableRow
      key={strategy.strategy_name}
      sx={{ bgcolor: isBest ? 'success.light' : 'transparent' }}
    >
      <TableCell>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {isBest && '🏆 '}
          <strong>{strategy.strategy_name}</strong>
        </Box>
      </TableCell>
      <TableCell align="right">
        <Typography
          variant="body2"
          color={strategy.avg_return > 0 ? 'success.main' : 'error.main'}
          fontWeight="bold"
        >
          {strategy.avg_return > 0 ? '+' : ''}
          {strategy.avg_return.toFixed(2)}%
        </Typography>
      </TableCell>
      <TableCell align="right">
        {(strategy.win_rate * 100).toFixed(1)}%
      </TableCell>
      <TableCell align="right">
        {strategy.avg_hold_days.toFixed(1)}
      </TableCell>
      <TableCell align="right">
        <Chip
          label={strategy.sharpe_ratio.toFixed(2)}
          size="small"
          color={strategy.sharpe_ratio > 0.6 ? 'success' : strategy.sharpe_ratio > 0.4 ? 'primary' : 'default'}
        />
      </TableCell>
      <TableCell align="right">
        {strategy.expectancy.toFixed(2)}%
      </TableCell>
      <TableCell align="right">
        {strategy.profit_factor.toFixed(2)}
      </TableCell>
    </TableRow>
  );

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CompareArrowsIcon sx={{ fontSize: 32, color: 'primary.main' }} />
          <Typography variant="h5" component="h2">
            Exit Strategy Comparison
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Max Hold Days</InputLabel>
            <Select
              value={maxHoldDays}
              label="Max Hold Days"
              onChange={(e) => setMaxHoldDays(Number(e.target.value))}
            >
              <MenuItem value={7}>7 days</MenuItem>
              <MenuItem value={14}>14 days</MenuItem>
              <MenuItem value={21}>21 days</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="contained"
            onClick={fetchComparison}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : <TrendingUpIcon />}
          >
            {loading ? 'Running...' : 'Run Comparison'}
          </Button>
        </Box>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {ticker} • Entry ≤{threshold}% • Comparing 5+ exit strategies
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {data && (
        <>
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>Best Strategy (by Sharpe Ratio): </strong>
              {getBestStrategy()?.strategy_name} with {getBestStrategy()?.sharpe_ratio.toFixed(2)} Sharpe
              and {getBestStrategy()?.avg_return.toFixed(2)}% average return
            </Typography>
          </Alert>

          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Strategy</strong></TableCell>
                  <TableCell align="right"><strong>Avg Return</strong></TableCell>
                  <TableCell align="right"><strong>Win Rate</strong></TableCell>
                  <TableCell align="right"><strong>Avg Hold Days</strong></TableCell>
                  <TableCell align="right"><strong>Sharpe Ratio</strong></TableCell>
                  <TableCell align="right"><strong>Expectancy</strong></TableCell>
                  <TableCell align="right"><strong>Profit Factor</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.strategy_comparison.buy_and_hold &&
                  renderStrategyRow(
                    data.strategy_comparison.buy_and_hold,
                    data.strategy_comparison.buy_and_hold === getBestStrategy()
                  )}

                {Object.entries(data.strategy_comparison.fixed_days || {}).map(
                  ([_day, perf]: [string, any]) =>
                    renderStrategyRow(perf, perf === getBestStrategy())
                )}

                {data.strategy_comparison.trailing_stop_atr &&
                  renderStrategyRow(
                    data.strategy_comparison.trailing_stop_atr,
                    data.strategy_comparison.trailing_stop_atr === getBestStrategy()
                  )}

                {data.strategy_comparison.adaptive_exit_pressure &&
                  renderStrategyRow(
                    data.strategy_comparison.adaptive_exit_pressure,
                    data.strategy_comparison.adaptive_exit_pressure === getBestStrategy()
                  )}

                {data.strategy_comparison.conditional_expectancy &&
                  renderStrategyRow(
                    data.strategy_comparison.conditional_expectancy,
                    data.strategy_comparison.conditional_expectancy === getBestStrategy()
                  )}
              </TableBody>
            </Table>
          </TableContainer>

          <Box sx={{ mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              Key Insights
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
              <Alert severity="success" sx={{ py: 1 }}>
                <Typography variant="body2">
                  <strong>Best Return:</strong> {Math.max(
                    data.strategy_comparison.buy_and_hold?.avg_return || 0,
                    data.strategy_comparison.trailing_stop_atr?.avg_return || 0,
                    data.strategy_comparison.adaptive_exit_pressure?.avg_return || 0,
                    data.strategy_comparison.conditional_expectancy?.avg_return || 0
                  ).toFixed(2)}%
                </Typography>
              </Alert>
              <Alert severity="info" sx={{ py: 1 }}>
                <Typography variant="body2">
                  <strong>Total Trades:</strong> {data.entry_events_count}
                </Typography>
              </Alert>
            </Box>
          </Box>
        </>
      )}

      {!data && !loading && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body1" color="text.secondary">
            Click "Run Comparison" to analyze exit strategies
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default ExitStrategyComparison;
