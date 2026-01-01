/**
 * Snapshot Selector Component
 *
 * Allows users to select and create data snapshots.
 * Shows snapshot timestamp and indicates when data is cached.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Select,
  MenuItem,
  Button,
  Chip,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Tooltip,
  IconButton
} from '@mui/material';
import {
  Refresh,
  Add,
  CheckCircle,
  Schedule,
  Storage
} from '@mui/icons-material';
import axios from 'axios';

interface Snapshot {
  snapshot_id: string;
  created_at: string;
  data_start_date: string;
  data_end_date: string;
  tickers: string[];
  parameter_hash: string;
  parameter_display: string;
}

interface SnapshotSelectorProps {
  selectedSnapshotId: string | null;
  onSnapshotChange: (snapshotId: string, snapshot: Snapshot) => void;
  apiBaseUrl?: string;
}

const SnapshotSelector: React.FC<SnapshotSelectorProps> = ({
  selectedSnapshotId,
  onSnapshotChange,
  apiBaseUrl = ''
}) => {
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cacheStatus, setCacheStatus] = useState<'cached' | 'computing' | 'unknown'>('unknown');

  useEffect(() => {
    loadSnapshots();
  }, []);

  const loadSnapshots = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(`${apiBaseUrl}/api/snapshot/list`);
      const snapshotList = response.data as Snapshot[];
      setSnapshots(snapshotList);

      // Auto-select latest if none selected
      if (!selectedSnapshotId && snapshotList.length > 0) {
        const latest = snapshotList[0];
        onSnapshotChange(latest.snapshot_id, latest);
      }

    } catch (err: any) {
      console.error('Failed to load snapshots:', err);
      setError(err.message || 'Failed to load snapshots');
    } finally {
      setLoading(false);
    }
  };

  const createSnapshot = async () => {
    setCreating(true);
    setError(null);

    try {
      const response = await axios.post(`${apiBaseUrl}/api/snapshot/create`, {
        tickers: ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'TSLA', 'META', 'AMZN', 'NFLX'],
        force_refresh: true
      });

      const newSnapshot = response.data as Snapshot;

      // Reload snapshot list
      await loadSnapshots();

      // Select new snapshot
      onSnapshotChange(newSnapshot.snapshot_id, newSnapshot);

    } catch (err: any) {
      console.error('Failed to create snapshot:', err);
      setError(err.message || 'Failed to create snapshot');
    } finally {
      setCreating(false);
    }
  };

  const handleSnapshotChange = (snapshotId: string) => {
    const snapshot = snapshots.find(s => s.snapshot_id === snapshotId);
    if (snapshot) {
      onSnapshotChange(snapshotId, snapshot);
    }
  };

  const selectedSnapshot = snapshots.find(s => s.snapshot_id === selectedSnapshotId);

  if (loading) {
    return (
      <Paper elevation={2} sx={{ p: 2, mb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
        <CircularProgress size={24} />
        <Typography>Loading snapshots...</Typography>
      </Paper>
    );
  }

  if (error && snapshots.length === 0) {
    return (
      <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
        <Alert severity="error">
          <Typography variant="body2">{error}</Typography>
          <Button size="small" onClick={loadSnapshots} sx={{ mt: 1 }}>
            Retry
          </Button>
        </Alert>
      </Paper>
    );
  }

  return (
    <Paper elevation={2} sx={{ p: 2, mb: 2, bgcolor: 'primary.dark' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
        {/* Snapshot Selector */}
        <FormControl sx={{ minWidth: 300 }} size="small">
          <InputLabel>Data Snapshot</InputLabel>
          <Select
            value={selectedSnapshotId || ''}
            label="Data Snapshot"
            onChange={(e) => handleSnapshotChange(e.target.value)}
          >
            {snapshots.map((snapshot) => (
              <MenuItem key={snapshot.snapshot_id} value={snapshot.snapshot_id}>
                <Box>
                  <Typography variant="body2">
                    {new Date(snapshot.created_at).toLocaleString()}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {snapshot.tickers.length} tickers, Hash: {snapshot.parameter_hash}
                  </Typography>
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Actions */}
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <Tooltip title="Refresh snapshot list">
            <IconButton onClick={loadSnapshots} size="small" disabled={loading}>
              <Refresh />
            </IconButton>
          </Tooltip>

          <Button
            variant="contained"
            size="small"
            startIcon={creating ? <CircularProgress size={16} /> : <Add />}
            onClick={createSnapshot}
            disabled={creating}
          >
            New Snapshot
          </Button>
        </Box>

        {/* Snapshot Info */}
        {selectedSnapshot && (
          <Box sx={{ flex: 1, display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
            <Chip
              icon={<Schedule />}
              label={new Date(selectedSnapshot.created_at).toLocaleString()}
              size="small"
              color="primary"
            />
            <Chip
              icon={<Storage />}
              label={`${selectedSnapshot.tickers.length} tickers`}
              size="small"
            />
            {cacheStatus === 'cached' && (
              <Chip
                icon={<CheckCircle />}
                label="Cached"
                size="small"
                color="success"
              />
            )}
          </Box>
        )}
      </Box>

      {/* Parameter Display (Compact) */}
      {selectedSnapshot && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
            <strong>Parameters:</strong>
          </Typography>
          <Typography variant="caption" sx={{ fontFamily: 'monospace', fontSize: '0.7rem' }}>
            {selectedSnapshot.parameter_display}
          </Typography>
        </Box>
      )}

      {error && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
    </Paper>
  );
};

export default SnapshotSelector;
