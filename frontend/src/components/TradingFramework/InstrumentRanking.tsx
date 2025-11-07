import React, { useState } from 'react';
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
  IconButton,
  Collapse,
} from '@mui/material';
import { LeaderboardOutlined, KeyboardArrowDown, KeyboardArrowUp, TrendingUp, TrendingDown } from '@mui/icons-material';

interface ScoringFactor {
  name: string;
  value: number;
  weight: number;
  category: 'technical' | 'fundamental' | 'sentiment' | 'regime' | 'risk';
}

interface CompositeScore {
  instrument: string;
  totalScore: number;
  factors: ScoringFactor[];
  rank?: number;
  percentile?: number;
  timestamp: string;
}

interface InstrumentRankingProps {
  scores: CompositeScore[];
}

const InstrumentRow: React.FC<{ score: CompositeScore }> = ({ score }) => {
  const [open, setOpen] = useState(false);

  const getScoreColor = (value: number) => {
    if (value > 0.7) return 'success';
    if (value > 0.4) return 'warning';
    return 'error';
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      technical: '#3B82F6',
      fundamental: '#10B981',
      sentiment: '#FBBF24',
      regime: '#8B5CF6',
      risk: '#EF4444',
    };
    return colors[category] || '#6B7280';
  };

  return (
    <>
      <TableRow hover onClick={() => setOpen(!open)} sx={{ cursor: 'pointer' }}>
        <TableCell>
          <IconButton size="small">
            {open ? <KeyboardArrowUp /> : <KeyboardArrowDown />}
          </IconButton>
        </TableCell>
        <TableCell>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body1" fontWeight="bold">
              #{score.rank}
            </Typography>
            {score.rank === 1 && <Chip label="TOP" size="small" color="success" />}
          </Box>
        </TableCell>
        <TableCell>
          <Typography variant="body1" fontWeight="bold">
            {score.instrument}
          </Typography>
        </TableCell>
        <TableCell>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body1" fontWeight="bold" color={getScoreColor(score.totalScore) + '.main'}>
              {(score.totalScore * 100).toFixed(1)}
            </Typography>
            <Box sx={{ flexGrow: 1, maxWidth: 100 }}>
              <LinearProgress
                variant="determinate"
                value={score.totalScore * 100}
                color={getScoreColor(score.totalScore)}
                sx={{ height: 6, borderRadius: 1 }}
              />
            </Box>
          </Box>
        </TableCell>
        <TableCell>
          <Typography variant="body2" color="text.secondary">
            {score.percentile ? `${score.percentile.toFixed(0)}%ile` : '-'}
          </Typography>
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={5}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ margin: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Scoring Factors Breakdown
              </Typography>
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2, mt: 1 }}>
                {score.factors.map((factor, idx) => (
                  <Box
                    key={idx}
                    sx={{
                      p: 1.5,
                      border: 1,
                      borderColor: getCategoryColor(factor.category),
                      borderRadius: 1,
                      bgcolor: 'background.default',
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" fontWeight="bold">
                        {factor.name}
                      </Typography>
                      <Chip
                        label={factor.category}
                        size="small"
                        sx={{
                          height: 18,
                          fontSize: '0.65rem',
                          bgcolor: getCategoryColor(factor.category),
                          color: 'white',
                        }}
                      />
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                      <Typography variant="body2" fontWeight="bold">
                        {(factor.value * 100).toFixed(0)}
                      </Typography>
                      <Box sx={{ flexGrow: 1 }}>
                        <LinearProgress
                          variant="determinate"
                          value={Math.abs(factor.value) * 100}
                          color={factor.value > 0 ? 'success' : 'error'}
                          sx={{ height: 4, borderRadius: 1 }}
                        />
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        w: {factor.weight.toFixed(2)}
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </Box>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
};

const InstrumentRanking: React.FC<InstrumentRankingProps> = ({ scores }) => {
  const topGainer = scores[0];
  const topLoser = scores[scores.length - 1];

  return (
    <Paper elevation={3} sx={{ p: 3, height: '100%' }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <LeaderboardOutlined />
        Instrument Composite Scores & Rankings
      </Typography>

      <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
        <Box sx={{ flex: 1, p: 2, bgcolor: 'success.dark', borderRadius: 1, opacity: 0.9 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <TrendingUp />
            <Typography variant="caption">Top Scorer</Typography>
          </Box>
          <Typography variant="h6" fontWeight="bold">
            {topGainer?.instrument}
          </Typography>
          <Typography variant="body2">
            Score: {((topGainer?.totalScore || 0) * 100).toFixed(1)}
          </Typography>
        </Box>

        <Box sx={{ flex: 1, p: 2, bgcolor: 'error.dark', borderRadius: 1, opacity: 0.9 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <TrendingDown />
            <Typography variant="caption">Lowest Score</Typography>
          </Box>
          <Typography variant="h6" fontWeight="bold">
            {topLoser?.instrument}
          </Typography>
          <Typography variant="body2">
            Score: {((topLoser?.totalScore || 0) * 100).toFixed(1)}
          </Typography>
        </Box>
      </Box>

      <TableContainer sx={{ maxHeight: 500 }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell width={50} />
              <TableCell>Rank</TableCell>
              <TableCell>Instrument</TableCell>
              <TableCell>Composite Score</TableCell>
              <TableCell>Percentile</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {scores.map((score) => (
              <InstrumentRow key={score.instrument} score={score} />
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2, textAlign: 'center' }}>
        Rankings updated in real-time based on multi-factor composite scoring
      </Typography>
    </Paper>
  );
};

export default InstrumentRanking;
