import React from 'react';
import {
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Box,
  LinearProgress,
} from '@mui/material';
import { AccountBalance, TrendingUp, TrendingDown } from '@mui/icons-material';

interface AdaptiveStopLoss {
  initialStop: number;
  currentStop: number;
  riskAmount: number;
  updateReason?: string;
  timestamp: string;
}

interface Position {
  instrument: string;
  direction: 'long' | 'short';
  entryPrice: number;
  currentPrice: number;
  quantity: number;
  positionValue: number;
  unrealizedPnL: number;
  riskAmount: number;
  stopLoss: AdaptiveStopLoss;
  openedAt: string;
  timeframe: string;
}

interface PositionMonitorProps {
  positions: Position[];
  totalCapital: number;
}

const PositionMonitor: React.FC<PositionMonitorProps> = ({ positions, totalCapital }) => {
  const totalValue = positions.reduce((sum, p) => sum + p.positionValue, 0);
  const totalPnL = positions.reduce((sum, p) => sum + p.unrealizedPnL, 0);
  const totalRisk = positions.reduce((sum, p) => sum + p.riskAmount, 0);

  const pnlPercent = totalCapital > 0 ? (totalPnL / totalCapital) * 100 : 0;
  const riskPercent = totalCapital > 0 ? (totalRisk / totalCapital) * 100 : 0;

  const getDirectionColor = (direction: string) => (direction === 'long' ? 'success' : 'error');

  return (
    <Paper elevation={3} sx={{ p: 3, height: '100%' }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <AccountBalance />
        Active Positions & Risk Management
      </Typography>

      <Box sx={{ mb: 3, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 2 }}>
        <Box sx={{ p: 2, bgcolor: 'primary.dark', borderRadius: 1 }}>
          <Typography variant="caption">Total Capital</Typography>
          <Typography variant="h6" fontWeight="bold">
            ${totalCapital.toLocaleString()}
          </Typography>
        </Box>

        <Box sx={{ p: 2, bgcolor: 'info.dark', borderRadius: 1 }}>
          <Typography variant="caption">Position Value</Typography>
          <Typography variant="h6" fontWeight="bold">
            ${totalValue.toLocaleString()}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {((totalValue / totalCapital) * 100).toFixed(1)}% deployed
          </Typography>
        </Box>

        <Box sx={{ p: 2, bgcolor: pnlPercent >= 0 ? 'success.dark' : 'error.dark', borderRadius: 1 }}>
          <Typography variant="caption">Unrealized P&L</Typography>
          <Typography variant="h6" fontWeight="bold">
            ${totalPnL.toFixed(2)}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {pnlPercent >= 0 ? '+' : ''}{pnlPercent.toFixed(2)}%
          </Typography>
        </Box>

        <Box sx={{ p: 2, bgcolor: 'warning.dark', borderRadius: 1 }}>
          <Typography variant="caption">Total Risk</Typography>
          <Typography variant="h6" fontWeight="bold">
            ${totalRisk.toFixed(2)}
          </Typography>
          <Box sx={{ mt: 1 }}>
            <LinearProgress
              variant="determinate"
              value={Math.min(riskPercent, 100)}
              color={riskPercent > 5 ? 'error' : 'warning'}
              sx={{ height: 6, borderRadius: 1 }}
            />
          </Box>
        </Box>
      </Box>

      <TableContainer sx={{ maxHeight: 400 }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              <TableCell>Instrument</TableCell>
              <TableCell>Direction</TableCell>
              <TableCell>Timeframe</TableCell>
              <TableCell align="right">Entry</TableCell>
              <TableCell align="right">Current</TableCell>
              <TableCell align="right">Qty</TableCell>
              <TableCell align="right">P&L</TableCell>
              <TableCell align="right">Stop Loss</TableCell>
              <TableCell align="right">Risk $</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {positions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  <Typography variant="body2" color="text.secondary" sx={{ py: 4 }}>
                    No active positions
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              positions.map((position, idx) => {
                const pnlColor = position.unrealizedPnL >= 0 ? 'success.main' : 'error.main';
                const stopDistance = position.direction === 'long'
                  ? ((position.currentPrice - position.stopLoss.currentStop) / position.currentPrice) * 100
                  : ((position.stopLoss.currentStop - position.currentPrice) / position.currentPrice) * 100;

                return (
                  <TableRow key={idx} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="bold">
                        {position.instrument}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {new Date(position.openedAt).toLocaleDateString()}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={position.direction.toUpperCase()}
                        size="small"
                        color={getDirectionColor(position.direction)}
                        icon={position.direction === 'long' ? <TrendingUp /> : <TrendingDown />}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">{position.timeframe}</Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">${position.entryPrice.toFixed(2)}</Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight="bold">
                        ${position.currentPrice.toFixed(2)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">{position.quantity}</Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight="bold" color={pnlColor}>
                        ${position.unrealizedPnL.toFixed(2)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {((position.unrealizedPnL / position.positionValue) * 100).toFixed(1)}%
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">${position.stopLoss.currentStop.toFixed(2)}</Typography>
                      <Typography variant="caption" color={stopDistance < 2 ? 'error.main' : 'text.secondary'}>
                        {stopDistance.toFixed(1)}% away
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" color="warning.main">
                        ${position.riskAmount.toFixed(2)}
                      </Typography>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
        Positions are monitored in real-time with adaptive stop-loss management
      </Typography>
    </Paper>
  );
};

export default PositionMonitor;
