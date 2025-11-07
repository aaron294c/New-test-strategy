/**
 * Parameter Display Component
 *
 * Shows active calculation parameters in a compact, always-visible panel.
 * Ensures users know exactly what settings produced the displayed metrics.
 */

import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Grid,
  Tooltip,
  Divider,
  IconButton,
  Collapse
} from '@mui/material';
import {
  Settings,
  ExpandMore,
  ExpandLess,
  Info
} from '@mui/icons-material';

export interface CalculationParameters {
  // Lookback windows
  percentile_lookback: number;
  regime_lookback: number;
  trade_lookback_days: number;

  // Percentile bins
  entry_bins: string[];
  exit_threshold: number;
  dead_zone_threshold: number;

  // Stop loss
  stop_loss_method: string;
  atr_multiplier: number;
  std_multiplier: number;
  confidence_level: number;

  // Bootstrap
  bootstrap_iterations: number;
  bootstrap_seed: number;
  bootstrap_confidence: number;
  block_size: number;

  // Trade construction
  allow_overlapping_signals: boolean;
  allow_reentry_same_day: boolean;
  max_holding_days: number;
  min_holding_days: number;

  // Risk
  risk_per_trade: number;
  max_positions: number;

  // Scoring weights
  expectancy_weight: number;
  confidence_weight: number;
  percentile_weight: number;
}

interface ParameterDisplayProps {
  parameters: CalculationParameters;
  snapshotId?: string;
  snapshotTimestamp?: string;
  parameterHash?: string;
  compact?: boolean;
}

const ParameterDisplay: React.FC<ParameterDisplayProps> = ({
  parameters,
  snapshotId,
  snapshotTimestamp,
  parameterHash,
  compact = false
}) => {
  const [expanded, setExpanded] = React.useState(!compact);

  return (
    <Paper elevation={2} sx={{ p: 2, bgcolor: 'info.dark', mb: 2 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Settings fontSize="small" />
          <Typography variant="subtitle2" fontWeight="bold">
            Active Model Parameters
          </Typography>
          <Tooltip title="These parameters define how all metrics are calculated. Changing these will produce different results.">
            <Info fontSize="small" sx={{ color: 'text.secondary', cursor: 'help' }} />
          </Tooltip>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {parameterHash && (
            <Chip
              label={`Hash: ${parameterHash}`}
              size="small"
              variant="outlined"
              sx={{ fontSize: '0.7rem' }}
            />
          )}
          <IconButton size="small" onClick={() => setExpanded(!expanded)}>
            {expanded ? <ExpandLess /> : <ExpandMore />}
          </IconButton>
        </Box>
      </Box>

      {/* Snapshot Info */}
      {snapshotId && (
        <Box sx={{ mb: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Data Snapshot: <strong>{snapshotId}</strong>
            {snapshotTimestamp && ` (${new Date(snapshotTimestamp).toLocaleString()})`}
          </Typography>
        </Box>
      )}

      {/* Quick Summary (Always Visible) */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: expanded ? 2 : 0 }}>
        <Chip
          label={`Lookback: ${parameters.percentile_lookback}d`}
          size="small"
          color="primary"
          variant="outlined"
        />
        <Chip
          label={`Entry: ${parameters.entry_bins.join(', ')}`}
          size="small"
          color="success"
          variant="outlined"
        />
        <Chip
          label={`Exit: ${parameters.exit_threshold}%`}
          size="small"
          color="warning"
          variant="outlined"
        />
        <Chip
          label={`Stop: ${parameters.stop_loss_method}`}
          size="small"
          color="error"
          variant="outlined"
        />
        <Chip
          label={`Bootstrap: n=${parameters.bootstrap_iterations}, seed=${parameters.bootstrap_seed}`}
          size="small"
          variant="outlined"
        />
      </Box>

      {/* Detailed Parameters (Expandable) */}
      <Collapse in={expanded}>
        <Divider sx={{ my: 2 }} />

        <Grid container spacing={2}>
          {/* Lookback Windows */}
          <Grid item xs={12} md={4}>
            <Typography variant="caption" color="text.secondary" gutterBottom>
              <strong>Lookback Windows</strong>
            </Typography>
            <Box sx={{ pl: 1 }}>
              <Typography variant="caption" display="block">
                Percentile Mapping: {parameters.percentile_lookback} periods
              </Typography>
              <Typography variant="caption" display="block">
                Regime Detection: {parameters.regime_lookback} periods
              </Typography>
              <Typography variant="caption" display="block">
                Recent Trades: {parameters.trade_lookback_days} days
              </Typography>
            </Box>
          </Grid>

          {/* Percentile Bins */}
          <Grid item xs={12} md={4}>
            <Typography variant="caption" color="text.secondary" gutterBottom>
              <strong>Percentile Strategy</strong>
            </Typography>
            <Box sx={{ pl: 1 }}>
              <Typography variant="caption" display="block">
                Entry Bins: {parameters.entry_bins.join(', ')}
              </Typography>
              <Typography variant="caption" display="block">
                Exit Threshold: {parameters.exit_threshold}%
              </Typography>
              <Typography variant="caption" display="block">
                Dead Zone: &gt;{parameters.dead_zone_threshold}%
              </Typography>
            </Box>
          </Grid>

          {/* Stop Loss */}
          <Grid item xs={12} md={4}>
            <Typography variant="caption" color="text.secondary" gutterBottom>
              <strong>Stop Loss Formula</strong>
            </Typography>
            <Box sx={{ pl: 1 }}>
              <Typography variant="caption" display="block">
                Method: {parameters.stop_loss_method}
              </Typography>
              <Typography variant="caption" display="block">
                ATR Multiplier: {parameters.atr_multiplier}×
              </Typography>
              <Typography variant="caption" display="block">
                Std Multiplier: {parameters.std_multiplier}σ
              </Typography>
              <Typography variant="caption" display="block">
                Confidence: {(parameters.confidence_level * 100).toFixed(0)}%
              </Typography>
            </Box>
          </Grid>

          {/* Bootstrap Settings */}
          <Grid item xs={12} md={4}>
            <Typography variant="caption" color="text.secondary" gutterBottom>
              <strong>Bootstrap (Deterministic)</strong>
            </Typography>
            <Box sx={{ pl: 1 }}>
              <Typography variant="caption" display="block">
                Iterations: {parameters.bootstrap_iterations.toLocaleString()}
              </Typography>
              <Typography variant="caption" display="block" color="warning.main">
                Fixed Seed: {parameters.bootstrap_seed}
              </Typography>
              <Typography variant="caption" display="block">
                Confidence: {(parameters.bootstrap_confidence * 100).toFixed(0)}%
              </Typography>
              <Typography variant="caption" display="block">
                Block Size: {parameters.block_size} trades
              </Typography>
            </Box>
          </Grid>

          {/* Trade Construction */}
          <Grid item xs={12} md={4}>
            <Typography variant="caption" color="text.secondary" gutterBottom>
              <strong>Trade Construction Rules</strong>
            </Typography>
            <Box sx={{ pl: 1 }}>
              <Typography variant="caption" display="block">
                Overlapping Signals: {parameters.allow_overlapping_signals ? '✓ Allowed' : '✗ Blocked'}
              </Typography>
              <Typography variant="caption" display="block">
                Same-Day Re-entry: {parameters.allow_reentry_same_day ? '✓ Allowed' : '✗ Blocked'}
              </Typography>
              <Typography variant="caption" display="block">
                Holding Period: {parameters.min_holding_days}–{parameters.max_holding_days} days
              </Typography>
            </Box>
          </Grid>

          {/* Risk & Scoring */}
          <Grid item xs={12} md={4}>
            <Typography variant="caption" color="text.secondary" gutterBottom>
              <strong>Risk & Scoring Weights</strong>
            </Typography>
            <Box sx={{ pl: 1 }}>
              <Typography variant="caption" display="block">
                Risk Per Trade: {(parameters.risk_per_trade * 100).toFixed(1)}%
              </Typography>
              <Typography variant="caption" display="block">
                Max Positions: {parameters.max_positions}
              </Typography>
              <Divider sx={{ my: 0.5 }} />
              <Typography variant="caption" display="block">
                Expectancy: {(parameters.expectancy_weight * 100).toFixed(0)}%
              </Typography>
              <Typography variant="caption" display="block">
                Confidence: {(parameters.confidence_weight * 100).toFixed(0)}%
              </Typography>
              <Typography variant="caption" display="block">
                Percentile: {(parameters.percentile_weight * 100).toFixed(0)}%
              </Typography>
            </Box>
          </Grid>
        </Grid>

        {/* Warning about deterministic execution */}
        <Box sx={{ mt: 2, p: 1, bgcolor: 'warning.dark', borderRadius: 1 }}>
          <Typography variant="caption">
            <strong>⚠️ Deterministic Execution:</strong> All calculations use fixed seed ({parameters.bootstrap_seed})
            for bootstrap operations. Results are 100% reproducible across runs and views.
          </Typography>
        </Box>
      </Collapse>
    </Paper>
  );
};

export default ParameterDisplay;
