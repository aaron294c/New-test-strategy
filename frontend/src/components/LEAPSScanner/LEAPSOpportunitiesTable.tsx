/**
 * LEAPS Opportunities Table Component
 *
 * Displays filtered LEAPS options with interactive controls,
 * sortable columns, and detailed option information.
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Paper,
  Chip,
  Grid,
  Slider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  CircularProgress,
  Alert,
  Tooltip,
  IconButton,
  Collapse,
  Stack,
  LinearProgress,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import RefreshIcon from '@mui/icons-material/Refresh';
import FilterListIcon from '@mui/icons-material/FilterList';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

// Backend API base URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Type definitions
interface LEAPSOption {
  symbol: string;
  strike: number;
  expiration: string;
  days_to_expiration: number;
  years_to_expiration: number;
  current_price: number;
  premium: number;
  bid: number;
  ask: number;
  bid_ask_spread: number;
  bid_ask_spread_pct: number;
  volume: number;
  open_interest: number;
  implied_volatility: number;
  intrinsic_value: number;
  extrinsic_value: number;
  extrinsic_pct: number;
  strike_pct: number;
  delta: number;
  gamma: number;
  vega: number;
  theta: number;
  rho: number;
  iv_rank: number;
  iv_percentile: number;
  quality_score: number;
  opportunity_score: number;
  // New metrics
  leverage_factor?: number;
  vega_efficiency?: number;
  cost_basis?: number;
  roi_10pct_move?: number;
  // Entry quality assessment
  entry_quality?: string;
  entry_quality_label?: string;
  entry_quality_description?: string;
}

// Vega risk scenario assessment
interface VegaRiskScenario {
  label: string;
  color: string;
  bgColor: string;
  description: string;
  rating: 'ideal' | 'acceptable' | 'caution' | 'avoid';
}

interface OpportunitiesData {
  current_price: number;
  strategy_used: string;
  filter_criteria: {
    delta_range: [number, number];
    extrinsic_max: number;
    vega_range: [number, number] | null;
  };
  total_options: number;
  filtered_options: number;
  top_opportunities: LEAPSOption[];
  data_source: string;
  timestamp: string;
}

type SortField = keyof LEAPSOption;
type SortOrder = 'asc' | 'desc';

// Helper function to assess vega risk scenario
const assessVegaRisk = (vega: number, ivRank: number): VegaRiskScenario => {
  // Scenario 3: Low Vega = IDEAL (stock-like, don't care about IV)
  if (vega <= 0.10) {
    return {
      label: 'Low Vega (Ideal)',
      color: '#ffffff',
      bgColor: '#4caf50',
      description: 'Stock-like stability - minimal volatility exposure',
      rating: 'ideal'
    };
  }

  // Scenario 1: High Vega + Low IV Rank = ACCEPTABLE (buying volatility cheap)
  if (vega > 0.10 && ivRank < 0.30) {
    return {
      label: 'High Vega + Cheap IV',
      color: '#ffffff',
      bgColor: '#ff9800',
      description: 'High volatility exposure BUT buying it cheap',
      rating: 'acceptable'
    };
  }

  // Scenario 2: High Vega + Mid IV Rank = CAUTION
  if (vega > 0.10 && ivRank >= 0.30 && ivRank < 0.60) {
    return {
      label: 'High Vega + Mid IV',
      color: '#ffffff',
      bgColor: '#ff5722',
      description: 'High volatility exposure at fair-to-elevated IV',
      rating: 'caution'
    };
  }

  // Scenario 2: High Vega + High IV Rank = AVOID (overpaying for volatility)
  return {
    label: 'High Vega + Expensive IV',
    color: '#ffffff',
    bgColor: '#f44336',
    description: 'High volatility exposure AND overpaying for it - AVOID!',
    rating: 'avoid'
  };
};

// Helper function to get entry quality badge styling
const getEntryQualityBadge = (quality?: string) => {
  switch (quality) {
    case 'excellent':
      return {
        label: 'Excellent Entry',
        color: '#ffffff',
        bgColor: '#4caf50', // Green
        icon: '🟢',
        description: 'Low IV + Low vega - Ideal buying opportunity!'
      };
    case 'good':
      return {
        label: 'Good Entry',
        color: '#ffffff',
        bgColor: '#8bc34a', // Light green
        icon: '🟢',
        description: 'Low IV but moderate vega - Good buying opportunity'
      };
    case 'fair':
      return {
        label: 'Fair Entry',
        color: '#000000',
        bgColor: '#ffeb3b', // Yellow
        icon: '🟡',
        description: 'Moderate IV and vega - Acceptable entry point'
      };
    case 'caution':
      return {
        label: 'Caution',
        color: '#ffffff',
        bgColor: '#ff9800', // Orange
        icon: '🟠',
        description: 'Moderate IV but higher vega - Consider waiting'
      };
    case 'wait':
      return {
        label: 'Wait for Better',
        color: '#ffffff',
        bgColor: '#f44336', // Red
        icon: '🔴',
        description: 'High IV percentile or high vega - Wait for better conditions'
      };
    default:
      return {
        label: 'Unknown',
        color: '#000000',
        bgColor: '#9e9e9e',
        icon: '⚪',
        description: 'Entry quality not assessed'
      };
  }
};

// Fetch opportunities
const fetchOpportunities = async (
  strategy?: string,
  minDelta?: number,
  maxDelta?: number,
  maxExtrinsic?: number,
  minStrike?: number,
  maxStrike?: number,
  minVega?: number,
  maxVega?: number,
  maxIvRank?: number,
  minIvPercentile?: number,
  maxIvPercentile?: number,
  rankBy?: string,
  topN: number = 10,
  useSample: boolean = false
): Promise<OpportunitiesData> => {
  const params = new URLSearchParams();
  if (strategy) params.append('strategy', strategy);
  if (minDelta !== undefined) params.append('min_delta', minDelta.toString());
  if (maxDelta !== undefined) params.append('max_delta', maxDelta.toString());
  if (maxExtrinsic !== undefined) params.append('max_extrinsic', maxExtrinsic.toString());
  if (minStrike !== undefined) params.append('min_strike', minStrike.toString());
  if (maxStrike !== undefined) params.append('max_strike', maxStrike.toString());
  if (minVega !== undefined) params.append('min_vega', minVega.toString());
  if (maxVega !== undefined) params.append('max_vega', maxVega.toString());
  if (maxIvRank !== undefined) params.append('max_iv_rank', maxIvRank.toString());
  if (minIvPercentile !== undefined) params.append('min_iv_percentile', minIvPercentile.toString());
  if (maxIvPercentile !== undefined) params.append('max_iv_percentile', maxIvPercentile.toString());
  if (rankBy) params.append('rank_by', rankBy);
  params.append('top_n', topN.toString());
  params.append('use_sample', useSample.toString());

  const response = await axios.get(`${API_BASE_URL}/api/leaps/opportunities?${params}`);
  return response.data;
};

interface LEAPSOpportunitiesTableProps {
  initialStrategy?: string;
}

export const LEAPSOpportunitiesTable: React.FC<LEAPSOpportunitiesTableProps> = ({
  initialStrategy
}) => {
  const [strategy, setStrategy] = useState<string>(initialStrategy || '');
  const [deltaRange, setDeltaRange] = useState<[number, number]>([0.45, 0.98]);
  const [maxExtrinsic, setMaxExtrinsic] = useState<number>(35);
  const [strikeRange, setStrikeRange] = useState<[number, number]>([0, 1000]);
  const [vegaRange, setVegaRange] = useState<[number, number]>([0, 2]);
  const [maxIvRank, setMaxIvRank] = useState<number>(1.0);
  const [ivPercentileRange, setIvPercentileRange] = useState<[number, number]>([0, 100]);
  const [rankBy, setRankBy] = useState<string>('opportunity_score');
  const [topN, setTopN] = useState<number>(10);
  const [sortField, setSortField] = useState<SortField>('opportunity_score');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState<boolean>(false);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState<boolean>(false);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['leaps-opportunities', strategy, deltaRange, maxExtrinsic, strikeRange, vegaRange, maxIvRank, ivPercentileRange, rankBy, topN],
    queryFn: () => fetchOpportunities(
      strategy || undefined,
      strategy ? undefined : deltaRange[0],
      strategy ? undefined : deltaRange[1],
      strategy ? undefined : maxExtrinsic,
      strikeRange[0] > 0 ? strikeRange[0] : undefined,
      strikeRange[1] < 1000 ? strikeRange[1] : undefined,
      vegaRange[0] > 0 ? vegaRange[0] : undefined,
      vegaRange[1] < 2 ? vegaRange[1] : undefined,
      maxIvRank < 1.0 ? maxIvRank : undefined,
      ivPercentileRange[0] > 0 ? ivPercentileRange[0] : undefined,
      ivPercentileRange[1] < 100 ? ivPercentileRange[1] : undefined,
      rankBy,
      topN,
      false // Never use sample data
    ),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const handleStrategyChange = (newStrategy: string) => {
    setStrategy(newStrategy);
    // Reset custom filters when switching to preset strategy
    if (newStrategy) {
      setDeltaRange([0.45, 0.98]);
      setMaxExtrinsic(35);
      setStrikeRange([0, 1000]);
      setVegaRange([0, 2]);
      setMaxIvRank(1.0);
      setIvPercentileRange([0, 100]);
    }
  };

  const getDataSourceColor = (source: string) => {
    return source === 'live' ? 'success' : 'warning';
  };

  const sortedOptions = React.useMemo(() => {
    if (!data?.top_opportunities) return [];

    return [...data.top_opportunities].sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
      }

      return 0;
    });
  }, [data?.top_opportunities, sortField, sortOrder]);

  const formatCurrency = (value: number) => `$${value.toFixed(2)}`;
  const formatPercent = (value: number) => `${value.toFixed(2)}%`;
  const formatGreek = (value: number, decimals: number = 3) => value.toFixed(decimals);

  const getQualityColor = (score: number) => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  const getDeltaColor = (delta: number) => {
    if (delta >= 0.85) return '#4caf50';
    if (delta >= 0.70) return '#ff9800';
    return '#2196f3';
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
        <Typography variant="subtitle2" gutterBottom>
          Failed to fetch live options data
        </Typography>
        <Typography variant="body2">
          {error instanceof Error ? error.message : 'Unable to connect to options data provider. Please try again later.'}
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => refetch()}
          size="small"
          sx={{ mt: 2 }}
        >
          Retry
        </Button>
      </Alert>
    );
  }

  if (!data) return null;

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header with Controls */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h5">
            LEAPS Opportunities
          </Typography>
          <Chip
            label={data.strategy_used.toUpperCase()}
            color="primary"
            size="small"
          />
          {data.data_source === 'live' && (
            <Chip
              label="LIVE DATA"
              color="success"
              size="small"
            />
          )}
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<FilterListIcon />}
            onClick={() => setShowFilters(!showFilters)}
            size="small"
          >
            Filters
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => refetch()}
            size="small"
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Filter Controls */}
      <Collapse in={showFilters}>
        <Card sx={{ mb: 3, bgcolor: '#1E222D' }}>
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Strategy</InputLabel>
                  <Select
                    value={strategy}
                    label="Strategy"
                    onChange={(e) => handleStrategyChange(e.target.value)}
                  >
                    <MenuItem value="">Auto (from VIX)</MenuItem>
                    <MenuItem value="ATM">ATM Strategy</MenuItem>
                    <MenuItem value="MODERATE_ITM">Moderate ITM</MenuItem>
                    <MenuItem value="DEEP_ITM">Deep ITM</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Rank By</InputLabel>
                  <Select
                    value={rankBy}
                    label="Rank By"
                    onChange={(e) => setRankBy(e.target.value)}
                  >
                    <MenuItem value="opportunity_score">Opportunity Score (Best to Worst)</MenuItem>
                    <MenuItem value="quality_score">Quality Score</MenuItem>
                    <MenuItem value="delta">Delta</MenuItem>
                    <MenuItem value="vega">Vega</MenuItem>
                    <MenuItem value="iv_rank">IV Rank (Lower Better)</MenuItem>
                    <MenuItem value="premium">Premium (Lower Better)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={3}>
                <Typography gutterBottom>Delta Range</Typography>
                <Slider
                  value={deltaRange}
                  onChange={(_, newValue) => setDeltaRange(newValue as [number, number])}
                  valueLabelDisplay="auto"
                  min={0.3}
                  max={0.99}
                  step={0.05}
                  marks={[
                    { value: 0.5, label: '0.50' },
                    { value: 0.75, label: '0.75' },
                    { value: 0.90, label: '0.90' },
                  ]}
                  disabled={!!strategy}
                />
              </Grid>

              <Grid item xs={12} md={3}>
                <Typography gutterBottom>Max Extrinsic %</Typography>
                <Slider
                  value={maxExtrinsic}
                  onChange={(_, newValue) => setMaxExtrinsic(newValue as number)}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(v) => `${v}%`}
                  min={5}
                  max={50}
                  step={5}
                  marks={[
                    { value: 10, label: '10%' },
                    { value: 25, label: '25%' },
                  ]}
                  disabled={!!strategy}
                />
              </Grid>
            </Grid>

            {/* Advanced Filters Section */}
            <Box sx={{ mt: 3 }}>
              <Button
                variant="text"
                onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                size="small"
              >
                {showAdvancedFilters ? 'Hide' : 'Show'} Advanced Filters
              </Button>
            </Box>

            <Collapse in={showAdvancedFilters}>
              <Grid container spacing={3} sx={{ mt: 1 }}>
                <Grid item xs={12} md={4}>
                  <Typography gutterBottom>Strike Range ($)</Typography>
                  <Slider
                    value={strikeRange}
                    onChange={(_, newValue) => setStrikeRange(newValue as [number, number])}
                    valueLabelDisplay="auto"
                    min={0}
                    max={1000}
                    step={10}
                    marks={[
                      { value: 0, label: '$0' },
                      { value: 500, label: '$500' },
                      { value: 1000, label: '$1000' },
                    ]}
                  />
                </Grid>

                <Grid item xs={12} md={4}>
                  <Typography gutterBottom>Vega Range</Typography>
                  <Slider
                    value={vegaRange}
                    onChange={(_, newValue) => setVegaRange(newValue as [number, number])}
                    valueLabelDisplay="auto"
                    min={0}
                    max={2}
                    step={0.1}
                    marks={[
                      { value: 0, label: '0' },
                      { value: 1, label: '1.0' },
                      { value: 2, label: '2.0' },
                    ]}
                  />
                </Grid>

                <Grid item xs={12} md={4}>
                  <Typography gutterBottom>Max IV Rank</Typography>
                  <Slider
                    value={maxIvRank}
                    onChange={(_, newValue) => setMaxIvRank(newValue as number)}
                    valueLabelDisplay="auto"
                    min={0}
                    max={1}
                    step={0.05}
                    marks={[
                      { value: 0.25, label: '0.25' },
                      { value: 0.50, label: '0.50' },
                      { value: 0.75, label: '0.75' },
                    ]}
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <Typography gutterBottom>IV Percentile Range</Typography>
                  <Slider
                    value={ivPercentileRange}
                    onChange={(_, newValue) => setIvPercentileRange(newValue as [number, number])}
                    valueLabelDisplay="auto"
                    valueLabelFormat={(v) => `${v}%`}
                    min={0}
                    max={100}
                    step={5}
                    marks={[
                      { value: 0, label: '0%' },
                      { value: 50, label: '50%' },
                      { value: 100, label: '100%' },
                    ]}
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <Typography gutterBottom>Results Limit</Typography>
                  <Slider
                    value={topN}
                    onChange={(_, newValue) => setTopN(newValue as number)}
                    valueLabelDisplay="auto"
                    min={5}
                    max={25}
                    step={5}
                    marks={[
                      { value: 10, label: '10' },
                      { value: 20, label: '20' },
                    ]}
                  />
                </Grid>
              </Grid>
            </Collapse>

            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Showing {data.filtered_options} of {data.total_options} total options
              </Typography>
              <Typography variant="caption" color="text.secondary">
                SPY Price: {formatCurrency(data.current_price)}
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Collapse>

      {/* Options Table */}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell />
              <TableCell>
                <TableSortLabel
                  active={sortField === 'opportunity_score'}
                  direction={sortField === 'opportunity_score' ? sortOrder : 'asc'}
                  onClick={() => handleSort('opportunity_score')}
                >
                  Opportunity
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={sortField === 'quality_score'}
                  direction={sortField === 'quality_score' ? sortOrder : 'asc'}
                  onClick={() => handleSort('quality_score')}
                >
                  Quality
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={sortField === 'strike'}
                  direction={sortField === 'strike' ? sortOrder : 'asc'}
                  onClick={() => handleSort('strike')}
                >
                  Strike
                </TableSortLabel>
              </TableCell>
              <TableCell>Expiration</TableCell>
              <TableCell>
                <TableSortLabel
                  active={sortField === 'premium'}
                  direction={sortField === 'premium' ? sortOrder : 'asc'}
                  onClick={() => handleSort('premium')}
                >
                  Premium
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={sortField === 'delta'}
                  direction={sortField === 'delta' ? sortOrder : 'asc'}
                  onClick={() => handleSort('delta')}
                >
                  Delta
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={sortField === 'extrinsic_pct'}
                  direction={sortField === 'extrinsic_pct' ? sortOrder : 'asc'}
                  onClick={() => handleSort('extrinsic_pct')}
                >
                  Extrinsic %
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={sortField === 'vega'}
                  direction={sortField === 'vega' ? sortOrder : 'asc'}
                  onClick={() => handleSort('vega')}
                >
                  Vega
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <Tooltip title="Vega + IV Rank combined assessment">
                  <span>Vega Risk</span>
                </Tooltip>
              </TableCell>
              <TableCell>
                <Tooltip title="IV Percentile + Vega combined - tells you WHEN to buy">
                  <span>Entry Quality</span>
                </Tooltip>
              </TableCell>
              <TableCell>
                <Tooltip title="Raw implied volatility value">
                  <TableSortLabel
                    active={sortField === 'implied_volatility'}
                    direction={sortField === 'implied_volatility' ? sortOrder : 'asc'}
                    onClick={() => handleSort('implied_volatility')}
                  >
                    IV
                  </TableSortLabel>
                </Tooltip>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={sortField === 'iv_rank'}
                  direction={sortField === 'iv_rank' ? sortOrder : 'asc'}
                  onClick={() => handleSort('iv_rank')}
                >
                  IV Rank
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={sortField === 'iv_percentile'}
                  direction={sortField === 'iv_percentile' ? sortOrder : 'asc'}
                  onClick={() => handleSort('iv_percentile')}
                >
                  IV %ile
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <Tooltip title="Stock exposure per dollar invested (higher = more leverage)">
                  <TableSortLabel
                    active={sortField === 'leverage_factor'}
                    direction={sortField === 'leverage_factor' ? sortOrder : 'asc'}
                    onClick={() => handleSort('leverage_factor')}
                  >
                    Leverage
                  </TableSortLabel>
                </Tooltip>
              </TableCell>
              <TableCell>
                <Tooltip title="Volatility exposure per $100 invested (lower is better)">
                  <TableSortLabel
                    active={sortField === 'vega_efficiency'}
                    direction={sortField === 'vega_efficiency' ? sortOrder : 'asc'}
                    onClick={() => handleSort('vega_efficiency')}
                  >
                    Vega Eff
                  </TableSortLabel>
                </Tooltip>
              </TableCell>
              <TableCell>
                <Tooltip title="Effective cost per share of exposure (lower is better)">
                  <TableSortLabel
                    active={sortField === 'cost_basis'}
                    direction={sortField === 'cost_basis' ? sortOrder : 'asc'}
                    onClick={() => handleSort('cost_basis')}
                  >
                    Cost/Share
                  </TableSortLabel>
                </Tooltip>
              </TableCell>
              <TableCell>
                <Tooltip title="Expected return if stock moves up 10%">
                  <TableSortLabel
                    active={sortField === 'roi_10pct_move'}
                    direction={sortField === 'roi_10pct_move' ? sortOrder : 'asc'}
                    onClick={() => handleSort('roi_10pct_move')}
                  >
                    ROI 10%
                  </TableSortLabel>
                </Tooltip>
              </TableCell>
              <TableCell>Volume</TableCell>
              <TableCell>OI</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedOptions.map((option) => (
              <React.Fragment key={option.symbol}>
                <TableRow hover sx={{ cursor: 'pointer' }}>
                  <TableCell>
                    <IconButton
                      size="small"
                      onClick={() => setExpandedRow(expandedRow === option.symbol ? null : option.symbol)}
                    >
                      {expandedRow === option.symbol ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                    </IconButton>
                  </TableCell>
                  <TableCell>
                    {option.opportunity_score !== undefined ? (
                      <Chip
                        label={option.opportunity_score.toFixed(0)}
                        size="small"
                        sx={{
                          backgroundColor: option.opportunity_score >= 75 ? '#4caf50' :
                                         option.opportunity_score >= 50 ? '#ff9800' : '#f44336',
                          color: 'white',
                          fontWeight: 'bold'
                        }}
                      />
                    ) : (
                      <Typography variant="body2" color="text.secondary">N/A</Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    {option.quality_score !== undefined ? (
                      <Chip
                        label={option.quality_score.toFixed(0)}
                        color={getQualityColor(option.quality_score) as any}
                        size="small"
                      />
                    ) : (
                      <Typography variant="body2" color="text.secondary">N/A</Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                      {formatCurrency(option.strike)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {option.strike_pct !== undefined && (
                        <>{option.strike_pct > 0 ? '+' : ''}{option.strike_pct.toFixed(1)}%</>
                      )}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{option.expiration}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {option.days_to_expiration}d
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 'bold', color: '#4caf50' }}>
                      {formatCurrency(option.premium)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {formatCurrency(option.bid)}-{formatCurrency(option.ask)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {option.delta !== undefined ? (
                      <Chip
                        label={option.delta.toFixed(3)}
                        size="small"
                        sx={{
                          bgcolor: getDeltaColor(option.delta),
                          color: 'white',
                          fontWeight: 'bold'
                        }}
                      />
                    ) : (
                      <Typography variant="body2" color="text.secondary">N/A</Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {option.extrinsic_pct !== undefined ? formatPercent(option.extrinsic_pct) : 'N/A'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {option.extrinsic_value !== undefined && formatCurrency(option.extrinsic_value)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 'bold', color: '#e91e63' }}>
                      {option.vega !== undefined ? formatGreek(option.vega) : 'N/A'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {option.vega !== undefined && option.iv_rank !== undefined ? (
                      <Tooltip title={assessVegaRisk(option.vega, option.iv_rank).description}>
                        <Chip
                          label={assessVegaRisk(option.vega, option.iv_rank).label}
                          size="small"
                          sx={{
                            bgcolor: assessVegaRisk(option.vega, option.iv_rank).bgColor,
                            color: assessVegaRisk(option.vega, option.iv_rank).color,
                            fontWeight: 'bold',
                            fontSize: '0.7rem',
                            minWidth: '140px'
                          }}
                        />
                      </Tooltip>
                    ) : (
                      <Typography variant="body2" color="text.secondary">N/A</Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    {option.entry_quality ? (
                      <Tooltip title={getEntryQualityBadge(option.entry_quality).description}>
                        <Chip
                          label={getEntryQualityBadge(option.entry_quality).label}
                          size="small"
                          sx={{
                            bgcolor: getEntryQualityBadge(option.entry_quality).bgColor,
                            color: getEntryQualityBadge(option.entry_quality).color,
                            fontWeight: 'bold',
                            fontSize: '0.75rem',
                            minWidth: '150px'
                          }}
                        />
                      </Tooltip>
                    ) : (
                      <Typography variant="body2" color="text.secondary">N/A</Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 'bold', color: '#9c27b0' }}>
                      {option.implied_volatility !== undefined ? `${(option.implied_volatility * 100).toFixed(1)}%` : 'N/A'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {option.iv_rank !== undefined ? (
                      <Tooltip title="Lower is better - cheaper vega exposure">
                        <Chip
                          label={option.iv_rank.toFixed(2)}
                          size="small"
                          color={option.iv_rank < 0.3 ? 'success' : option.iv_rank < 0.6 ? 'warning' : 'error'}
                        />
                      </Tooltip>
                    ) : (
                      <Typography variant="body2" color="text.secondary">N/A</Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {option.iv_percentile !== undefined ? `${option.iv_percentile.toFixed(0)}%` : 'N/A'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {option.leverage_factor !== undefined ? (
                      <Chip
                        label={`${option.leverage_factor.toFixed(1)}x`}
                        size="small"
                        sx={{
                          bgcolor: option.leverage_factor >= 6 ? '#4caf50' :
                                   option.leverage_factor >= 4 ? '#ff9800' : '#f44336',
                          color: 'white',
                          fontWeight: 'bold'
                        }}
                      />
                    ) : (
                      <Typography variant="body2" color="text.secondary">N/A</Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    {option.vega_efficiency !== undefined ? (
                      <Chip
                        label={`${option.vega_efficiency.toFixed(2)}%`}
                        size="small"
                        sx={{
                          bgcolor: option.vega_efficiency <= 0.15 ? '#4caf50' :
                                   option.vega_efficiency <= 0.30 ? '#ff9800' : '#f44336',
                          color: 'white',
                          fontWeight: 'bold'
                        }}
                      />
                    ) : (
                      <Typography variant="body2" color="text.secondary">N/A</Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 'bold', color: '#2196f3' }}>
                      {option.cost_basis !== undefined ? `$${option.cost_basis.toFixed(0)}` : 'N/A'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {option.roi_10pct_move !== undefined ? (
                      <Chip
                        label={`${option.roi_10pct_move.toFixed(1)}%`}
                        size="small"
                        sx={{
                          bgcolor: option.roi_10pct_move >= 70 ? '#4caf50' :
                                   option.roi_10pct_move >= 50 ? '#ff9800' : '#f44336',
                          color: 'white',
                          fontWeight: 'bold'
                        }}
                      />
                    ) : (
                      <Typography variant="body2" color="text.secondary">N/A</Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{option.volume.toLocaleString()}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{option.open_interest.toLocaleString()}</Typography>
                  </TableCell>
                </TableRow>

                {/* Expanded Row Details */}
                <TableRow>
                  <TableCell colSpan={19} sx={{ py: 0, borderBottom: expandedRow === option.symbol ? undefined : 'none' }}>
                    <Collapse in={expandedRow === option.symbol} timeout="auto" unmountOnExit>
                      <Box sx={{ p: 3, bgcolor: '#1E222D', borderRadius: 1 }}>
                        <Grid container spacing={3}>
                          <Grid item xs={12} md={6}>
                            <Typography variant="subtitle2" gutterBottom>Greeks</Typography>
                            <Stack spacing={1}>
                              {option.delta !== undefined && (
                                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                  <Typography variant="body2">Delta:</Typography>
                                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                                    {formatGreek(option.delta)}
                                  </Typography>
                                </Box>
                              )}
                              {option.gamma !== undefined && (
                                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                  <Typography variant="body2">Gamma:</Typography>
                                  <Typography variant="body2">{formatGreek(option.gamma, 6)}</Typography>
                                </Box>
                              )}
                              {option.vega !== undefined && (
                                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                  <Typography variant="body2">Vega:</Typography>
                                  <Typography variant="body2">{formatGreek(option.vega)}</Typography>
                                </Box>
                              )}
                              {option.theta !== undefined && (
                                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                  <Typography variant="body2">Theta:</Typography>
                                  <Typography variant="body2" sx={{ color: '#f44336' }}>
                                    {formatGreek(option.theta)} / day
                                  </Typography>
                                </Box>
                              )}
                              {option.implied_volatility !== undefined && (
                                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                  <Typography variant="body2">IV:</Typography>
                                  <Typography variant="body2">{formatPercent(option.implied_volatility * 100)}</Typography>
                                </Box>
                              )}
                              {option.iv_rank !== undefined && (
                                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                  <Typography variant="body2">IV Rank:</Typography>
                                  <Chip
                                    label={option.iv_rank.toFixed(2)}
                                    size="small"
                                    color={option.iv_rank < 0.3 ? 'success' : option.iv_rank < 0.6 ? 'warning' : 'error'}
                                  />
                                </Box>
                              )}
                              {option.iv_percentile !== undefined && (
                                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                  <Typography variant="body2">IV Percentile:</Typography>
                                  <Typography variant="body2">{option.iv_percentile.toFixed(0)}%</Typography>
                                </Box>
                              )}
                            </Stack>
                          </Grid>

                          <Grid item xs={12} md={6}>
                            <Typography variant="subtitle2" gutterBottom>Contract Details</Typography>
                            <Stack spacing={1}>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                <Typography variant="body2">Symbol:</Typography>
                                <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                                  {option.symbol}
                                </Typography>
                              </Box>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                <Typography variant="body2">Intrinsic:</Typography>
                                <Typography variant="body2">{formatCurrency(option.intrinsic_value)}</Typography>
                              </Box>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                <Typography variant="body2">Extrinsic:</Typography>
                                <Typography variant="body2">{formatCurrency(option.extrinsic_value)}</Typography>
                              </Box>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                <Typography variant="body2">Bid-Ask Spread:</Typography>
                                <Typography variant="body2">
                                  {formatCurrency(option.bid_ask_spread)} ({option.bid_ask_spread_pct.toFixed(2)}%)
                                </Typography>
                              </Box>
                              {option.quality_score !== undefined && (
                                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                  <Typography variant="body2">Quality Score:</Typography>
                                  <Box sx={{ flexGrow: 1, mx: 2 }}>
                                    <LinearProgress
                                      variant="determinate"
                                      value={option.quality_score}
                                      sx={{
                                        height: 8,
                                        borderRadius: 1,
                                        bgcolor: '#424242',
                                        '& .MuiLinearProgress-bar': {
                                          bgcolor: option.quality_score >= 80 ? '#4caf50' :
                                            option.quality_score >= 60 ? '#ff9800' : '#f44336'
                                        }
                                      }}
                                    />
                                  </Box>
                                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                                    {option.quality_score.toFixed(0)}/100
                                  </Typography>
                                </Box>
                              )}
                            </Stack>
                          </Grid>

                          {/* Advanced Metrics Section */}
                          <Grid item xs={12}>
                            <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                              Advanced Metrics
                            </Typography>
                            <Grid container spacing={2}>
                              <Grid item xs={6} md={3}>
                                <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: '#2a2e3a', borderRadius: 1 }}>
                                  <Typography variant="caption" color="text.secondary">
                                    Leverage Factor
                                  </Typography>
                                  <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#4caf50' }}>
                                    {option.leverage_factor !== undefined ? `${option.leverage_factor.toFixed(1)}x` : 'N/A'}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    Stock exposure/$
                                  </Typography>
                                </Box>
                              </Grid>
                              <Grid item xs={6} md={3}>
                                <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: '#2a2e3a', borderRadius: 1 }}>
                                  <Typography variant="caption" color="text.secondary">
                                    Vega Efficiency
                                  </Typography>
                                  <Typography variant="h6" sx={{
                                    fontWeight: 'bold',
                                    color: option.vega_efficiency !== undefined && option.vega_efficiency <= 0.15 ? '#4caf50' :
                                           option.vega_efficiency !== undefined && option.vega_efficiency <= 0.30 ? '#ff9800' : '#f44336'
                                  }}>
                                    {option.vega_efficiency !== undefined ? `${option.vega_efficiency.toFixed(2)}%` : 'N/A'}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    Vega per $100
                                  </Typography>
                                </Box>
                              </Grid>
                              <Grid item xs={6} md={3}>
                                <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: '#2a2e3a', borderRadius: 1 }}>
                                  <Typography variant="caption" color="text.secondary">
                                    Cost Basis
                                  </Typography>
                                  <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#2196f3' }}>
                                    {option.cost_basis !== undefined ? `$${option.cost_basis.toFixed(0)}` : 'N/A'}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    Per share
                                  </Typography>
                                </Box>
                              </Grid>
                              <Grid item xs={6} md={3}>
                                <Box sx={{ textAlign: 'center', p: 1.5, bgcolor: '#2a2e3a', borderRadius: 1 }}>
                                  <Typography variant="caption" color="text.secondary">
                                    ROI on 10% Move
                                  </Typography>
                                  <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#9c27b0' }}>
                                    {option.roi_10pct_move !== undefined ? `${option.roi_10pct_move.toFixed(1)}%` : 'N/A'}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    If stock +10%
                                  </Typography>
                                </Box>
                              </Grid>
                            </Grid>
                          </Grid>
                        </Grid>
                      </Box>
                    </Collapse>
                  </TableCell>
                </TableRow>
              </React.Fragment>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {sortedOptions.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          No LEAPS opportunities found matching the current filters. Try adjusting your criteria.
        </Alert>
      )}

      {/* Footer */}
      <Box sx={{ mt: 2, textAlign: 'center' }}>
        <Typography variant="caption" color="text.secondary">
          Last updated: {new Date(data.timestamp).toLocaleString()}
        </Typography>
      </Box>
    </Box>
  );
};

export default LEAPSOpportunitiesTable;
