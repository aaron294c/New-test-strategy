import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Tabs,
  Tab,
  Chip,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import InfoIcon from '@mui/icons-material/Info';
import axios from 'axios';

// Use environment variable for API base URL
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// Helper function to safely format numbers - MUST be defined before component
const safeToFixed = (value: number | null | undefined, decimals: number = 2): string => {
  if (value == null || typeof value !== 'number' || isNaN(value)) return 'N/A';
  return value.toFixed(decimals);
};

// Helper to parse position_size (handles both number and "50%" string formats)
const parsePositionSize = (value: number | string | null | undefined): number => {
  if (value == null) return 0;
  if (typeof value === 'number') return value;
  const parsed = parseFloat(String(value).replace('%', ''));
  return isNaN(parsed) ? 0 : parsed;
};

interface BinStatistic {
  bin_range: string;
  mean: number;
  median: number | null;
  std: number;
  sample_size: number;
  t_score: number;
  is_significant: boolean;
  signal_strength: string;
  confidence_interval_95: [number, number];
  percentile_5th: number | null;
  percentile_95th: number | null;
  upside: number | null;
  downside: number | null;
  action: string;
  position_size_guidance: string;
  action_color: string;
}

interface StockMetadata {
  ticker: string;
  name: string;
  personality: string;
  reliability_4h: string;
  reliability_daily: string;
  tradeable_4h_zones: string[];
  dead_zones_4h: string[];
  best_4h_bin: string;
  best_4h_t_score: number;
  ease_rating: number;
  characteristics: {
    is_mean_reverter: boolean;
    is_momentum: boolean;
    volatility_level: string;
  };
  guidance: {
    entry: string;
    avoid: string;
    special_notes: string;
  };
}

interface TradingRecommendation {
  ticker: string;
  stock_name: string;
  personality: string;
  current_4h_bin: string;
  current_daily_bin: string;
  fourh_mean: number;
  fourh_t_score: number;
  fourh_is_significant: boolean;
  fourh_signal_strength: string;
  daily_mean: number;
  daily_t_score: number;
  daily_is_significant: boolean;
  daily_signal_strength: string;
  recommended_action: string;
  position_size: number | string;  // Can be number or string like "50%"
  confidence: string;
  detailed_guidance: string;
  stop_loss_5th_percentile: number | null;
  upside_95th_percentile: number | null;
}

interface TradeManagementRules {
  ticker: string;
  stock_name: string;
  personality: string;
  add_rules: Array<{
    bin: string;
    intensity: string;
    max_position: number;
    expected_return: number;
    t_score: number;
    confidence: string;
    stop_loss: number | null;
    upside: number | null;
  }>;
  trim_rules: Array<{
    bin: string;
    action: string;
    trim_percentage: number;
    reason: string;
  }>;
  exit_rules: Array<{
    bin: string;
    action: string;
    expected_return: number;
    t_score: number;
    reason: string;
  }>;
  stop_loss_guidance: {
    dynamic_stop_loss: number;
    recommended_stop: number;
    explanation: string;
  };
  time_management: {
    hold_period: string;
    early_exit_trigger: string;
    daily_monitoring: string;
  };
}

const PERCENTILE_BINS = [
  '0-5', '5-15', '15-25', '25-50', '50-75', '75-85', '85-95', '95-100'
];

const STOCK_TABS = [
  'NVDA', 'MSFT', 'GOOGL', 'AAPL', 'GLD', 'SLV', 'TSLA', 'NFLX', 'BRK-B', 'WMT', 'UNH', 'AVGO', 'LLY', 'TSM', 'ORCL', 'OXY'
];

interface MultiTimeframeGuideProps {
  ticker?: string;
}

const MultiTimeframeGuide: React.FC<MultiTimeframeGuideProps> = ({ ticker }) => {
  const [selectedStock, setSelectedStock] = useState<string>(() => (
    ticker && STOCK_TABS.includes(ticker) ? ticker : 'NVDA'
  ));
  const [selectedTab, setSelectedTab] = useState<number>(0);
  const [stockMetadata, setStockMetadata] = useState<StockMetadata | null>(null);
  const [fourHBins, setFourHBins] = useState<BinStatistic[]>([]);
  const [dailyBins, setDailyBins] = useState<BinStatistic[]>([]);
  const [current4HBin, setCurrent4HBin] = useState<string>('50-75');
  const [currentDailyBin, setCurrentDailyBin] = useState<string>('25-50');
  const [recommendation, setRecommendation] = useState<TradingRecommendation | null>(null);
  const [tradeManagement, setTradeManagement] = useState<TradeManagementRules | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  // Keep Trading Guide selection in sync with global ticker selector (when supported)
  useEffect(() => {
    if (!ticker || !STOCK_TABS.includes(ticker)) return;
    if (ticker === selectedStock) return;
    setSelectedStock(ticker);
  }, [ticker, selectedStock]);

  // Load stock metadata
  useEffect(() => {
    loadStockMetadata();
    loadBinData('4H');
    loadBinData('Daily');
    loadTradeManagement();
  }, [selectedStock]);

  // Load recommendation when bins change
  useEffect(() => {
    loadRecommendation();
  }, [selectedStock, current4HBin, currentDailyBin]);

  const loadStockMetadata = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/stock/${selectedStock}`);
      setStockMetadata(response.data);
    } catch (error) {
      console.error('Error loading stock metadata:', error);
    }
  };

  const loadBinData = async (timeframe: string) => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/bins/${selectedStock}/${timeframe}`
      );
      // Convert object to array
      const binsArray = Object.values(response.data);
      if (timeframe === '4H') {
        setFourHBins(binsArray);
      } else {
        setDailyBins(binsArray);
      }
    } catch (error) {
      console.error(`Error loading ${timeframe} bins:`, error);
      // Set empty array on error to prevent crashes
      if (timeframe === '4H') {
        setFourHBins([]);
      } else {
        setDailyBins([]);
      }
    }
  };

  const loadRecommendation = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/recommendation`, {
        ticker: selectedStock,
        current_4h_bin: current4HBin,
        current_daily_bin: currentDailyBin,
      });
      setRecommendation(response.data);
    } catch (error) {
      console.error('Error loading recommendation:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSignalColor = (tScore: number): string => {
    const t = Math.abs(tScore);
    if (t >= 4.0) return '#1b5e20'; // Dark green
    if (t >= 3.0) return '#2e7d32'; // Green
    if (t >= 2.0) return '#388e3c'; // Light green
    if (t >= 1.5) return '#ff9800'; // Orange
    return '#d32f2f'; // Red
  };

  const getActionColor = (action: string): string => {
    if (action.includes('Add') || action.includes('Enter')) return 'success';
    if (action.includes('Trim') || action.includes('Avoid')) return 'error';
    if (action.includes('Wait')) return 'warning';
    return 'default';
  };

  const loadTradeManagement = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/trade-management/${selectedStock}`);
      setTradeManagement(response.data);
    } catch (error) {
      console.error('Error loading trade management rules:', error);
    }
  };

  const renderIntroduction = () => (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h5" gutterBottom>
          🎯 Trade the Week, Time the Entry
        </Typography>
        <Typography variant="body1" paragraph>
          Our Daily 7-day model gives direction; the 4-hour percentile gives you execution
          and risk controls inside that week. Enter when Daily is bullish and 4H is in a
          favorable bin (ideally 0–75%). Use 4H to add on dips, trim on spikes, and to
          trigger early exits if the intraday signal turns decisively bearish.
        </Typography>
      </CardContent>
    </Card>
  );

  const renderQuickDecisionChecklist = () => (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          📋 Quick Decision Checklist
        </Typography>

        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="textSecondary" gutterBottom>
            Step 1: Check Daily 7d Signal
          </Typography>
          {recommendation && (
            <Alert
              severity={recommendation.daily_is_significant ? 'success' : 'error'}
              icon={recommendation.daily_is_significant ? <CheckCircleIcon /> : <WarningIcon />}
            >
              Daily t-score: {safeToFixed(recommendation.daily_t_score)}{' '}
              {recommendation.daily_is_significant ? '✅ Proceed to Step 2' : '❌ SKIP - No trade'}
            </Alert>
          )}
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="textSecondary" gutterBottom>
            Step 2: Check 4H Entry Zone
          </Typography>
          <Grid container spacing={1}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth size="small">
                <InputLabel>Current 4H Bin</InputLabel>
                <Select
                  value={current4HBin}
                  onChange={(e) => setCurrent4HBin(e.target.value)}
                  label="Current 4H Bin"
                >
                  {PERCENTILE_BINS.map((bin) => (
                    <MenuItem key={bin} value={bin}>
                      {bin}%
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth size="small">
                <InputLabel>Current Daily Bin</InputLabel>
                <Select
                  value={currentDailyBin}
                  onChange={(e) => setCurrentDailyBin(e.target.value)}
                  label="Current Daily Bin"
                >
                  {PERCENTILE_BINS.map((bin) => (
                    <MenuItem key={bin} value={bin}>
                      {bin}%
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Box>

        {recommendation && (() => {
          const posSize = parsePositionSize(recommendation.position_size);
          return (
            <Alert
              severity={
                posSize >= 50
                  ? 'success'
                  : posSize >= 30
                  ? 'info'
                  : posSize > 0
                  ? 'warning'
                  : 'error'
              }
              icon={
                posSize >= 50 ? (
                  <TrendingUpIcon />
                ) : posSize > 0 ? (
                  <InfoIcon />
                ) : (
                  <TrendingDownIcon />
                )
              }
            >
              <Typography variant="subtitle2" gutterBottom>
                <strong>Recommendation:</strong> {recommendation.recommended_action}
              </Typography>
              <Typography variant="body2">
                Position Size: <strong>{posSize}%</strong> | Confidence:{' '}
                <strong>{recommendation.confidence}</strong>
              </Typography>
            </Alert>
          );
        })()}
      </CardContent>
    </Card>
  );

  const render4HBinTable = () => (
    <TableContainer component={Paper} sx={{ mb: 3 }}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell><strong>4H Bin</strong></TableCell>
            <TableCell align="right"><strong>Mean (48h)</strong></TableCell>
            <TableCell align="right"><strong>t-score</strong></TableCell>
            <TableCell align="center"><strong>Signal</strong></TableCell>
            <TableCell><strong>Action</strong></TableCell>
            <TableCell><strong>Position Size</strong></TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {(fourHBins || []).map((bin) => {
            if (!bin) return null;  // Skip undefined bins
            const isCurrentBin = bin.bin_range === current4HBin + '%';
            return (
              <TableRow
                key={bin.bin_range}
                sx={{
                  backgroundColor: isCurrentBin ? 'rgba(25, 118, 210, 0.08)' : 'inherit',
                  fontWeight: isCurrentBin ? 'bold' : 'normal',
                }}
              >
                <TableCell>
                  {bin.bin_range} {isCurrentBin && '← Current'}
                </TableCell>
                <TableCell align="right">
                  <Typography
                    color={(bin.mean ?? 0) > 0 ? 'success.main' : 'error.main'}
                    fontWeight={bin.is_significant ? 'bold' : 'normal'}
                  >
                    {(bin.mean ?? 0) > 0 ? '+' : ''}
                    {safeToFixed(bin.mean)}%
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Chip
                    label={safeToFixed(bin.t_score)}
                    size="small"
                    sx={{
                      backgroundColor: getSignalColor(bin.t_score ?? 0),
                      color: 'white',
                      fontWeight: 'bold',
                    }}
                  />
                </TableCell>
                <TableCell align="center">
                  <Typography variant="caption">{bin.signal_strength ?? 'N/A'}</Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={bin.action ?? 'N/A'}
                    size="small"
                    color={getActionColor(bin.action ?? '') as any}
                    variant={bin.is_significant ? 'filled' : 'outlined'}
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2">{bin.position_size_guidance ?? 'N/A'}</Typography>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </TableContainer>
  );

  const renderDailyBinTable = () => (
    <TableContainer component={Paper} sx={{ mb: 3 }}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell><strong>Daily Bin</strong></TableCell>
            <TableCell align="right"><strong>Mean (7d)</strong></TableCell>
            <TableCell align="right"><strong>t-score</strong></TableCell>
            <TableCell align="center"><strong>Signal</strong></TableCell>
            <TableCell align="right"><strong>Sample Size</strong></TableCell>
            <TableCell align="right"><strong>95% CI</strong></TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {(dailyBins || []).map((bin) => {
            if (!bin) return null;  // Skip undefined bins
            const isCurrentBin = bin.bin_range === currentDailyBin + '%';
            return (
              <TableRow
                key={bin.bin_range}
                sx={{
                  backgroundColor: isCurrentBin ? 'rgba(25, 118, 210, 0.08)' : 'inherit',
                }}
              >
                <TableCell>
                  {bin.bin_range} {isCurrentBin && '← Current'}
                </TableCell>
                <TableCell align="right">
                  <Typography
                    color={(bin.mean ?? 0) > 0 ? 'success.main' : 'error.main'}
                    fontWeight={bin.is_significant ? 'bold' : 'normal'}
                  >
                    {(bin.mean ?? 0) > 0 ? '+' : ''}
                    {safeToFixed(bin.mean)}%
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Chip
                    label={safeToFixed(bin.t_score)}
                    size="small"
                    sx={{
                      backgroundColor: getSignalColor(bin.t_score ?? 0),
                      color: 'white',
                      fontWeight: 'bold',
                    }}
                  />
                </TableCell>
                <TableCell align="center">
                  <Typography variant="caption">{bin.signal_strength ?? 'N/A'}</Typography>
                </TableCell>
                <TableCell align="right">{bin.sample_size ?? 0}</TableCell>
                <TableCell align="right">
                  <Typography variant="caption">
                    [{safeToFixed(bin.confidence_interval_95?.[0])}%, {safeToFixed(bin.confidence_interval_95?.[1])}%]
                  </Typography>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </TableContainer>
  );

  const renderPositionSizing = () => (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          🎯 Position Sizing Calculator
        </Typography>

        {recommendation && (
          <Box>
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2, backgroundColor: 'background.default' }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Daily Score
                  </Typography>
                  <Typography variant="h4">
                    {safeToFixed((recommendation.daily_t_score / 2.0) * 100, 0)}
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={Math.min((recommendation.daily_t_score / 2.0) * 100, 100)}
                    sx={{ mt: 1 }}
                  />
                  <Typography variant="caption" color="textSecondary">
                    t-score: {safeToFixed(recommendation.daily_t_score)} / 4.0 (max)
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2, backgroundColor: 'background.default' }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    4H Score
                  </Typography>
                  <Typography variant="h4">
                    {safeToFixed((recommendation.fourh_t_score / 2.0) * 100, 0)}
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={Math.min((recommendation.fourh_t_score / 2.0) * 100, 100)}
                    sx={{ mt: 1 }}
                  />
                  <Typography variant="caption" color="textSecondary">
                    t-score: {safeToFixed(recommendation.fourh_t_score)} / 4.0 (max)
                  </Typography>
                </Paper>
              </Grid>
            </Grid>

            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2" gutterBottom>
                <strong>Combined Analysis:</strong>
              </Typography>
              <Typography variant="body2">{recommendation.detailed_guidance}</Typography>
            </Alert>

            <Paper sx={{ p: 2, backgroundColor: 'success.light', color: 'success.contrastText' }}>
              <Typography variant="h5" align="center" gutterBottom>
                Recommended Position: {parsePositionSize(recommendation.position_size)}%
              </Typography>
              <Typography variant="subtitle1" align="center">
                Confidence: {recommendation.confidence}
              </Typography>
              {recommendation.stop_loss_5th_percentile != null && (
                <Typography variant="body2" align="center" sx={{ mt: 1 }}>
                  Stop Loss (5th percentile): {safeToFixed(recommendation.stop_loss_5th_percentile)}%
                </Typography>
              )}
            </Paper>
          </Box>
        )}
      </CardContent>
    </Card>
  );

  const renderStockSpecificGuidance = () => {
    if (!stockMetadata) return null;

    return (
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            📊 {stockMetadata.name} ({stockMetadata.ticker}) - Specific Guidance
          </Typography>

          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2, backgroundColor: 'background.default' }}>
                <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                  Personality
                </Typography>
                <Typography variant="h6" color="primary">
                  "{stockMetadata.personality}"
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <Chip label={stockMetadata.characteristics.volatility_level} size="small" sx={{ mr: 1 }} />
                  {stockMetadata.characteristics.is_mean_reverter && (
                    <Chip label="Mean Reverter" size="small" color="success" sx={{ mr: 1 }} />
                  )}
                  {stockMetadata.characteristics.is_momentum && (
                    <Chip label="Momentum" size="small" color="info" />
                  )}
                </Box>
              </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2, backgroundColor: 'background.default' }}>
                <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                  Reliability
                </Typography>
                <Typography variant="body2">4H: {stockMetadata.reliability_4h}</Typography>
                <Typography variant="body2">Daily: {stockMetadata.reliability_daily}</Typography>
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Ease of Trading: {'⭐'.repeat(stockMetadata.ease_rating)}
                </Typography>
              </Paper>
            </Grid>
          </Grid>

          <Accordion sx={{ mt: 2 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">
                ✅ Entry Guidance
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">{stockMetadata.guidance.entry}</Typography>
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" color="textSecondary">
                  Best 4H Zone: <strong>{stockMetadata.best_4h_bin}</strong> (t-score: {stockMetadata.best_4h_t_score != null ? stockMetadata.best_4h_t_score.toFixed(2) : 'N/A'})
                </Typography>
              </Box>
            </AccordionDetails>
          </Accordion>

          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">
                ❌ What to Avoid
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">{stockMetadata.guidance.avoid}</Typography>
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" color="error">
                  Dead Zones: {stockMetadata.dead_zones_4h.join(', ')}
                </Typography>
              </Box>
            </AccordionDetails>
          </Accordion>

          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">
                💡 Special Notes
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2">{stockMetadata.guidance.special_notes}</Typography>
            </AccordionDetails>
          </Accordion>
        </CardContent>
      </Card>
    );
  };

  const renderTradeManagementRules = () => {
    if (!tradeManagement) {
      return (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography>Loading trade management rules...</Typography>
          </CardContent>
        </Card>
      );
    }

    return (
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            🔄 {tradeManagement.stock_name} Trade Management Rules (Day 0 → Day 7)
          </Typography>
          <Typography variant="caption" color="textSecondary" display="block" gutterBottom>
            {tradeManagement.personality} • {tradeManagement.time_management?.daily_monitoring ?? 'N/A'}
          </Typography>

          {/* ADD RULES */}
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">🟢 ADD Rules (Buy the Dip) - {tradeManagement.add_rules?.length ?? 0} Zones</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2" paragraph>
                Monitor 4H percentile changes daily. Add to position when 4H drops into these zones:
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>4H Zone</strong></TableCell>
                      <TableCell><strong>Action</strong></TableCell>
                      <TableCell align="right"><strong>Max Position</strong></TableCell>
                      <TableCell align="right"><strong>Expected Return</strong></TableCell>
                      <TableCell align="right"><strong>t-score</strong></TableCell>
                      <TableCell align="right"><strong>Stop Loss</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(tradeManagement.add_rules || []).map((rule) => {
                      if (!rule) return null;
                      return (
                        <TableRow key={rule.bin}>
                          <TableCell>{rule.bin}</TableCell>
                          <TableCell>
                            <Chip label={rule.intensity ?? 'N/A'} color="success" size="small" />
                          </TableCell>
                          <TableCell align="right"><strong>{rule.max_position ?? 0}%</strong></TableCell>
                          <TableCell align="right" style={{ color: '#2e7d32' }}>
                            +{safeToFixed(rule.expected_return)}%
                          </TableCell>
                          <TableCell align="right">
                            <Chip label={safeToFixed(rule.t_score)} size="small" sx={{ backgroundColor: getSignalColor(rule.t_score ?? 0), color: 'white' }} />
                          </TableCell>
                          <TableCell align="right" style={{ color: '#d32f2f' }}>
                            {rule.stop_loss != null ? safeToFixed(rule.stop_loss) + '%' : 'N/A'}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            </AccordionDetails>
          </Accordion>

          {/* TRIM RULES */}
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">🔴 TRIM Rules (Take Profits)</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>4H Zone</strong></TableCell>
                      <TableCell><strong>Action</strong></TableCell>
                      <TableCell align="right"><strong>Trim %</strong></TableCell>
                      <TableCell><strong>Reason</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(tradeManagement.trim_rules || []).map((rule) => {
                      if (!rule) return null;
                      return (
                        <TableRow key={rule.bin}>
                          <TableCell>{rule.bin}</TableCell>
                          <TableCell>
                            <Chip label={rule.action ?? 'N/A'} color="warning" size="small" />
                          </TableCell>
                          <TableCell align="right"><strong>{rule.trim_percentage ?? 0}%</strong></TableCell>
                          <TableCell>{rule.reason ?? 'N/A'}</TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            </AccordionDetails>
          </Accordion>

          {/* EXIT RULES */}
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">🛑 EXIT Rules (Stop Loss / Early Exit)</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {(tradeManagement.exit_rules?.length ?? 0) > 0 && (
                <>
                  <Typography variant="body2" paragraph>
                    <strong>Bearish Zone Exit Triggers:</strong>
                  </Typography>
                  <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell><strong>4H Zone</strong></TableCell>
                          <TableCell><strong>Action</strong></TableCell>
                          <TableCell align="right"><strong>Expected Return</strong></TableCell>
                          <TableCell><strong>Reason</strong></TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {(tradeManagement.exit_rules || []).map((rule) => {
                          if (!rule) return null;
                          return (
                            <TableRow key={rule.bin}>
                              <TableCell>{rule.bin}</TableCell>
                              <TableCell>
                                <Chip label={rule.action ?? 'N/A'} color="error" size="small" />
                              </TableCell>
                              <TableCell align="right" style={{ color: '#d32f2f' }}>
                                {safeToFixed(rule.expected_return)}%
                              </TableCell>
                              <TableCell>{rule.reason ?? 'N/A'}</TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </>
              )}
              <Typography variant="body2" paragraph>
                <strong>Time-Based Exit Triggers:</strong>
              </Typography>
              <ul>
                <li>✅ Target hit early ({tradeManagement.time_management?.early_exit_trigger ?? 'N/A'})</li>
                <li>📅 Hold period complete ({tradeManagement.time_management?.hold_period ?? 'N/A'})</li>
              </ul>
              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  <strong>Dynamic Stop Loss for {tradeManagement.stock_name}:</strong> {safeToFixed(tradeManagement.stop_loss_guidance?.recommended_stop)}%
                </Typography>
                <Typography variant="caption">
                  {tradeManagement.stop_loss_guidance?.explanation ?? 'N/A'}
                </Typography>
              </Alert>
            </AccordionDetails>
          </Accordion>
        </CardContent>
      </Card>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Multi-Timeframe Trading Guide
      </Typography>

      {/* Stock Selector */}
      <Box sx={{ mb: 3 }}>
        <Tabs
          value={Math.max(0, STOCK_TABS.indexOf(selectedStock))}
          onChange={(_, newValue) => setSelectedStock(STOCK_TABS[newValue] ?? selectedStock)}
          variant="scrollable"
          scrollButtons="auto"
        >
          {STOCK_TABS.map((symbol) => (
            <Tab key={symbol} label={symbol} />
          ))}
        </Tabs>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {renderIntroduction()}
      {renderQuickDecisionChecklist()}
      {renderPositionSizing()}

      <Tabs value={selectedTab} onChange={(_, v) => setSelectedTab(v)} sx={{ mb: 2 }}>
        <Tab label="4H Bins (48h)" />
        <Tab label="Daily Bins (7d)" />
        <Tab label="Stock Guidance" />
        <Tab label="Trade Management" />
      </Tabs>

      {selectedTab === 0 && render4HBinTable()}
      {selectedTab === 1 && renderDailyBinTable()}
      {selectedTab === 2 && renderStockSpecificGuidance()}
      {selectedTab === 3 && renderTradeManagementRules()}
    </Box>
  );
};

export default MultiTimeframeGuide;
