/**
 * Swing Trading Framework Dashboard - Risk Management Layer
 *
 * Built ON TOP of percentile mapping (4H/Daily bins) with:
 * - Mean Reversion Detection (buy at low percentiles 0-15%)
 * - Momentum Pullback Detection (buy dips in uptrends)
 * - Risk-Adjusted Expectancy from bin statistics
 * - Strategic Capital Allocation
 *
 * Foundation: 4H/Daily percentile bins from backend
 * Entry Focus: 0-5%, 5-15% percentile zones (mean reversion)
 * Holding Period: 3-21 days
 * Exit: 50%+ percentile (strategy stops working)
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  Chip,
  Tabs,
  Tab,
  Alert,
  Card,
  CardContent,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  Tooltip,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Assessment,
  AccountBalance,
  ShowChart,
  Warning,
  CheckCircle,
  Cancel,
  Info,
} from '@mui/icons-material';
import axios from 'axios';
import {
  calculateExpectancyMetrics,
  formatMetricWithTimeFrame,
  ExpectancyMetrics,
} from '../../utils/expectancyCalculations';
import { CurrentMarketState } from './CurrentMarketState';
import { SwingDurationPanelV2 } from './SwingDurationPanelV2';

const API_BASE_URL = '';

// Inline helper function (previously from tradeSimulator.ts)
interface SimBinStatistic {
  bin_range: string;
  mean: number;
  std: number;
  sample_size: number;
  t_score: number;
  is_significant: boolean;
  signal_strength: string;
  action: string;
}

/**
 * Calculate stop distance based on volatility of LOW percentile bins
 * Lower percentiles = entry zones, want to avoid getting stopped out on noise
 */
const calculateStopDistance = (bins: SimBinStatistic[], minStopPct: number = 2.0): number => {
  // Get bins in the 0-20% range (entry zones)
  const lowBins = bins.filter(b => {
    const binStart = parseInt(b.bin_range.split('-')[0]);
    return binStart < 20;
  });

  if (lowBins.length === 0) return minStopPct;

  // Use mean + 1 std of negative moves as stop distance
  const avgStd = lowBins.reduce((sum, b) => sum + Math.abs(b.std), 0) / lowBins.length;
  const stopDistance = Math.max(avgStd * 1.0, minStopPct); // At least minStopPct%

  return stopDistance;
};

interface SwingFrameworkProps {
  ticker?: string;
}

interface BinStatistic {
  bin_range: string;
  mean: number;
  std: number;
  sample_size: number;
  t_score: number;
  is_significant: boolean;
  signal_strength: string;
  action: string;
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

interface RiskMetrics {
  ticker: string;
  regime: 'mean_reversion' | 'momentum' | 'neutral';
  regimeScore: number; // -1 to +1
  inEntryZone: boolean;
  currentPercentile: number;
  entryBins: string[];

  // Per-trade metrics (7d lookback)
  winRate: number;
  winRateCI: [number, number]; // Wilson 95% CI
  avgWin: number;
  avgLoss: number;
  expectancyPerTrade: number;
  expectancyCI: [number, number]; // Bootstrap 95% CI

  // Time-normalized metrics
  avgHoldingDays: number;
  expectancyPerDay: number; // E_per_day = E_trade / H
  optimalHoldingDays: number;
  diminishingReturnsDay: number;

  // Risk-adjusted metrics
  stopDistancePct: number;
  stopLossMethod: string; // 'percentile_5th' or 'mean_minus_2std'
  stopLossCalculation: string; // Transparent explanation
  riskPerTrade: number;
  expectancyPer1PctRisk: number;

  // NEW: Enhanced metrics from user feedback
  maxDrawdown: number;
  returnToDrawdownRatio: number;
  probabilityPositive: number; // p(E > 0) from bootstrap
  effectiveSampleSize: number; // n / blockSize

  // Regime conditional
  expectancyMeanReversion: number;
  expectancyMomentum: number;

  // NEW: Quantitative regime metrics
  regimeMetrics: {
    hurstExponent: number;
    hurstCI: [number, number];
    autocorrelation: number;
    varianceRatio: number;
    lookbackPeriods: number;
  };

  // Statistical confidence
  confidenceScore: number; // 0-1 composite
  sampleSize: number;

  // Composite scoring with transparent breakdown
  compositeScore: number;
  compositeBreakdown: {
    expectancyContribution: number; // α₁ (60%)
    confidenceContribution: number; // α₂ (25%)
    percentileContribution: number; // α₃ (15%)
    rawScores: {
      expectancyRaw: number;
      confidenceRaw: number;
      percentileRaw: number;
    };
    detailedCalculation: {
      expectancyNormalized: number;
      expectancyWeight: number;
      confidenceNormalized: number;
      confidenceWeight: number;
      percentileNormalized: number;
      percentileWeight: number;
    };
  };

  bestBinMean: number;
  bestBinTScore: number;
  strategyApplicable: boolean;
  reason: string;
}

interface AllocationDecision {
  ticker: string;
  rank: number;
  allocatedCapital: number;
  positionSize: number;
  riskAmount: number;
  expectedReturn: number;
  entryZone: string;
  stopLoss: number;
  targetExit: string;
  holdingPeriod: string;
  compositeScore: number;
}

const SwingTradingFramework: React.FC<SwingFrameworkProps> = ({ ticker }) => {
  const [loading, setLoading] = useState(true);
  const [stocksMetadata, setStocksMetadata] = useState<Map<string, StockMetadata>>(new Map());
  const [binStatistics4H, setBinStatistics4H] = useState<Map<string, BinStatistic[]>>(new Map());
  const [binStatisticsDaily, setBinStatisticsDaily] = useState<Map<string, BinStatistic[]>>(new Map());
  const [riskMetrics, setRiskMetrics] = useState<RiskMetrics[]>([]);
  const [allocations, setAllocations] = useState<AllocationDecision[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [timeframe, setTimeframe] = useState<'daily' | '4hour'>('daily');
  const [viewMode, setViewMode] = useState<'framework' | 'duration'>('framework');

  const TICKERS = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'TSLA', 'NFLX', 'AMZN'];

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    setError(null);

    try {
      console.log('🔄 Fetching REAL data from /api/swing-framework/all-tickers...');

      // NEW: Single endpoint with REAL historical trades
      const response = await axios.get(`${API_BASE_URL}/api/swing-framework/all-tickers`);
      const snapshot = response.data;

      console.log('✅ Loaded REAL data:', snapshot.summary);
      console.log('📊 Snapshot timestamp:', snapshot.snapshot_timestamp);

      // Process metadata
      const metadata = new Map<string, StockMetadata>();
      const bins4H = new Map<string, BinStatistic[]>();
      const binsDaily = new Map<string, BinStatistic[]>();

      Object.entries(snapshot.tickers).forEach(([ticker, tickerData]: [string, any]) => {
        // Store metadata
        const meta = tickerData.metadata;
        metadata.set(ticker, {
          ticker: meta.ticker,
          name: meta.name,
          personality: meta.personality,
          reliability_4h: meta.reliability_4h,
          reliability_daily: meta.reliability_daily,
          tradeable_4h_zones: meta.tradeable_4h_zones,
          dead_zones_4h: meta.dead_zones_4h,
          best_4h_bin: meta.best_4h_bin,
          best_4h_t_score: meta.best_4h_t_score,
          ease_rating: meta.ease_rating,
          characteristics: {
            is_mean_reverter: meta.is_mean_reverter,
            is_momentum: meta.is_momentum,
            volatility_level: meta.volatility_level
          },
          guidance: {
            entry: meta.entry_guidance,
            avoid: meta.avoid_guidance,
            special_notes: meta.special_notes
          }
        });

        // Store bins (convert object to array)
        bins4H.set(ticker, Object.values(tickerData.bins_4h));
        binsDaily.set(ticker, Object.values(tickerData.bins_daily));

        console.log(`  ${ticker}: ${tickerData.historical_trades.length} REAL trades`);
      });

      setStocksMetadata(metadata);
      setBinStatistics4H(bins4H);
      setBinStatisticsDaily(binsDaily);

      // Calculate risk metrics using REAL trades
      const metrics = calculateRiskMetricsFromRealTrades(snapshot.tickers, metadata);
      setRiskMetrics(metrics);

      // Generate allocations
      const decisions = generateAllocations(metrics, metadata, bins4H);
      setAllocations(decisions);

      if (metrics.length > 0) {
        setSelectedTicker(metrics[0].ticker);
      }

      console.log('✅ Framework loaded with REAL data');

    } catch (err: any) {
      console.error('❌ Error fetching real data:', err);
      setError(err.message || 'Failed to fetch framework data. Make sure backend is running!');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Calculate risk metrics from REAL historical trades (not simulated)
   * Uses actual backtest results from backend instead of client-side simulation
   */
  const calculateRiskMetricsFromRealTrades = (
    tickers: Record<string, any>,
    metadata: Map<string, StockMetadata>
  ): RiskMetrics[] => {
    const metrics: RiskMetrics[] = [];

    Object.entries(tickers).forEach(([ticker, tickerData]: [string, any]) => {
      const meta = metadata.get(ticker);
      if (!meta) {
        console.warn(`No metadata for ${ticker}`);
        return;
      }

      // Get REAL historical trades from backend
      const historicalTrades: TradeResult[] = tickerData.historical_trades.map((trade: any) => ({
        entryPrice: trade.entry_price,
        exitPrice: trade.exit_price,
        holdingDays: trade.holding_days,
        return: trade.return_pct / 100,  // Backend sends percentage, convert to decimal
        entryPercentile: trade.entry_percentile,
        exitPercentile: trade.exit_percentile,
        regime: trade.regime as 'mean_reversion' | 'momentum'
      }));

      console.log(`  📊 ${ticker}: Processing ${historicalTrades.length} REAL trades`);

      // Determine regime from metadata
      const regime = meta.characteristics.is_mean_reverter ? 'mean_reversion' :
                     meta.characteristics.is_momentum ? 'momentum' : 'neutral';

      // Assume current percentile (in production, get from backend)
      const currentPercentile = tickerData.metadata.current_percentile || 10;

      // Get LOW percentile bins (entry zones)
      const bins4H = Object.values(tickerData.bins_4h) as BinStatistic[];
      const lowPercentileBins = bins4H.filter(bin => {
        const binStart = parseInt(bin.bin_range.split('-')[0]);
        return binStart < 15; // 0-5%, 5-15%
      });

      const entryBins = lowPercentileBins.map(b => b.bin_range);

      // === CALCULATE STOP DISTANCE ===
      const stopDistancePct = calculateStopDistance(bins4H as SimBinStatistic[], 2.0);

      // === CALCULATE COMPREHENSIVE EXPECTANCY METRICS FROM REAL TRADES ===
      const expectancyMetrics = calculateExpectancyMetrics(
        historicalTrades,  // ← Using REAL trades, not simulated!
        currentPercentile,
        stopDistancePct,
        0.02, // 2% risk per trade
        7 // 7-day lookback
      );

      // === CALCULATE REGIME-CONDITIONAL EXPECTANCY ===
      const meanReversionTrades = historicalTrades.filter(t => t.regime === 'mean_reversion');
      const momentumTrades = historicalTrades.filter(t => t.regime === 'momentum');

      const expectancyMR = meanReversionTrades.length > 0
        ? calculateExpectancyMetrics(meanReversionTrades, currentPercentile, stopDistancePct, 0.02, 7).expectancyPerTrade
        : 0;

      const expectancyMom = momentumTrades.length > 0
        ? calculateExpectancyMetrics(momentumTrades, currentPercentile, stopDistancePct, 0.02, 7).expectancyPerTrade
        : 0;

      // === DETERMINE STRATEGY APPLICABILITY ===
      let strategyApplicable = false;
      let reason = '';

      const expectancyPerTrade = expectancyMetrics.expectancyPerTrade * 100; // Convert to %

      if (regime === 'mean_reversion' && expectancyPerTrade > 0) {
        strategyApplicable = true;
        reason = `Mean reversion stock with ${expectancyPerTrade.toFixed(2)}% expectancy per trade (${(expectancyMetrics.expectancyPerDay * 100).toFixed(3)}%/day) in low percentile zones`;
      } else if (regime === 'momentum' && expectancyPerTrade > 0) {
        strategyApplicable = true;
        reason = `Momentum stock with ${expectancyPerTrade.toFixed(2)}% expectancy per trade on pullbacks to low percentiles`;
      } else if (expectancyPerTrade <= 0) {
        strategyApplicable = false;
        reason = `Negative expectancy (${expectancyPerTrade.toFixed(2)}% per trade) - strategy does not work`;
      } else {
        strategyApplicable = false;
        reason = 'Neutral regime - unclear strategy applicability';
      }

      // === GET BEST BIN STATS ===
      const bestBin = bins4H.find(b => b.bin_range === meta.best_4h_bin);
      const bestBinMean = bestBin ? bestBin.mean : 0;
      const bestBinTScore = bestBin ? bestBin.t_score : 0;

      // === DETERMINE IF IN ENTRY ZONE ===
      const inEntryZone = currentPercentile <= 15 && expectancyPerTrade > 0;

      // === REGIME SCORE (simplified from trade distribution) ===
      const regimeScore = historicalTrades.length > 0
        ? (momentumTrades.length - meanReversionTrades.length) / historicalTrades.length
        : regime === 'momentum' ? 0.5 : regime === 'mean_reversion' ? -0.5 : 0;

      metrics.push({
        ticker,
        regime,
        regimeScore,
        inEntryZone,
        currentPercentile,
        entryBins,

        // Per-trade metrics (7d)
        winRate: expectancyMetrics.winRate,
        winRateCI: expectancyMetrics.winRateCI,
        avgWin: expectancyMetrics.avgWin * 100, // Convert to %
        avgLoss: expectancyMetrics.avgLoss * 100,
        expectancyPerTrade,
        expectancyCI: [
          expectancyMetrics.expectancyCI[0] * 100,
          expectancyMetrics.expectancyCI[1] * 100
        ],

        // Time-normalized
        avgHoldingDays: expectancyMetrics.avgHoldingDays,
        expectancyPerDay: expectancyMetrics.expectancyPerDay * 100, // Convert to %
        optimalHoldingDays: expectancyMetrics.optimalHoldingDays,
        diminishingReturnsDay: expectancyMetrics.diminishingReturnsDay,

        // Risk-adjusted
        stopDistancePct,
        riskPerTrade: expectancyMetrics.riskPerTrade,
        expectancyPer1PctRisk: expectancyMetrics.expectancyPer1PctRisk * 100,

        // Regime conditional
        expectancyMeanReversion: expectancyMR * 100,
        expectancyMomentum: expectancyMom * 100,

        // Statistical confidence
        confidenceScore: expectancyMetrics.confidenceScore,
        sampleSize: expectancyMetrics.sampleSize,

        // Composite scoring
        compositeScore: expectancyMetrics.compositeScore,
        compositeBreakdown: {
          expectancyContribution: expectancyMetrics.compositeBreakdown.expectancyContribution,
          winRateContribution: expectancyMetrics.compositeBreakdown.winRateContribution,
          confidenceContribution: expectancyMetrics.compositeBreakdown.confidenceContribution,
          riskAdjustmentContribution: expectancyMetrics.compositeBreakdown.riskAdjustmentContribution,
          timeEfficiencyContribution: expectancyMetrics.compositeBreakdown.timeEfficiencyContribution,
        },

        // Best bin info
        bestBin: meta.best_4h_bin,
        bestBinMean,
        bestBinTScore,

        // Strategy applicability
        strategyApplicable,
        reason,

        // Additional metadata
        volatilityLevel: meta.volatility_level || 'medium',
        easeRating: meta.ease_rating || 5,
      });
    });

    // Sort by composite score (descending)
    return metrics.sort((a, b) => b.compositeScore - a.compositeScore);
  };

  const calculateRiskMetrics = (
    metadata: Map<string, StockMetadata>,
    bins4H: Map<string, BinStatistic[]>,
    binsDaily: Map<string, BinStatistic[]>
  ): RiskMetrics[] => {
    const metrics: RiskMetrics[] = [];

    metadata.forEach((meta, ticker) => {
      const fourHBins = bins4H.get(ticker);
      const dailyBins = binsDaily.get(ticker);

      if (!fourHBins || fourHBins.length === 0) {
        console.warn(`No 4H bins for ${ticker}`);
        return;
      }

      // Determine regime from metadata
      const regime = meta.characteristics.is_mean_reverter ? 'mean_reversion' :
                     meta.characteristics.is_momentum ? 'momentum' : 'neutral';

      // Assume current percentile (in production, get from backend)
      const currentPercentile = 10; // Example: stock at 10th percentile

      // Get LOW percentile bins (entry zones)
      const lowPercentileBins = fourHBins.filter(bin => {
        const binStart = parseInt(bin.bin_range.split('-')[0]);
        return binStart < 15; // 0-5%, 5-15%
      });

      const entryBins = lowPercentileBins.map(b => b.bin_range);

      // === SIMULATE TRADES FROM BIN STATISTICS ===
      const { combinedTrades, trades4H, tradesDaily } = simulateTradesMultiTimeframe(
        fourHBins as SimBinStatistic[],
        (dailyBins || []) as SimBinStatistic[],
        regime,
        {
          entryPercentileThreshold: 15,
          exitPercentileThreshold: 50,
          maxHoldingDays: 21,
          lookbackDays: 7
        }
      );

      // === CALCULATE STOP DISTANCE ===
      const stopDistancePct = calculateStopDistance(fourHBins as SimBinStatistic[], 2.0);

      // === CALCULATE COMPREHENSIVE EXPECTANCY METRICS ===
      const expectancyMetrics = calculateExpectancyMetrics(
        combinedTrades,
        currentPercentile,
        stopDistancePct,
        0.02, // 2% risk per trade
        7 // 7-day lookback
      );

      // === CALCULATE REGIME-CONDITIONAL EXPECTANCY ===
      const meanReversionTrades = combinedTrades.filter(t => t.regime === 'mean_reversion');
      const momentumTrades = combinedTrades.filter(t => t.regime === 'momentum');

      const expectancyMR = meanReversionTrades.length > 0
        ? calculateExpectancyMetrics(meanReversionTrades, currentPercentile, stopDistancePct, 0.02, 7).expectancyPerTrade
        : 0;

      const expectancyMom = momentumTrades.length > 0
        ? calculateExpectancyMetrics(momentumTrades, currentPercentile, stopDistancePct, 0.02, 7).expectancyPerTrade
        : 0;

      // === DETERMINE STRATEGY APPLICABILITY ===
      let strategyApplicable = false;
      let reason = '';

      const expectancyPerTrade = expectancyMetrics.expectancyPerTrade * 100; // Convert to %

      if (regime === 'mean_reversion' && expectancyPerTrade > 0) {
        strategyApplicable = true;
        reason = `Mean reversion stock with ${expectancyPerTrade.toFixed(2)}% expectancy per trade (${(expectancyMetrics.expectancyPerDay * 100).toFixed(3)}%/day) in low percentile zones`;
      } else if (regime === 'momentum' && expectancyPerTrade > 0) {
        strategyApplicable = true;
        reason = `Momentum stock with ${expectancyPerTrade.toFixed(2)}% expectancy per trade on pullbacks to low percentiles`;
      } else if (expectancyPerTrade <= 0) {
        strategyApplicable = false;
        reason = `Negative expectancy (${expectancyPerTrade.toFixed(2)}% per trade) - strategy does not work`;
      } else {
        strategyApplicable = false;
        reason = 'Neutral regime - unclear strategy applicability';
      }

      // === GET BEST BIN STATS ===
      const bestBin = fourHBins.find(b => b.bin_range === meta.best_4h_bin);
      const bestBinMean = bestBin ? bestBin.mean : 0;
      const bestBinTScore = bestBin ? bestBin.t_score : 0;

      // === DETERMINE IF IN ENTRY ZONE ===
      const inEntryZone = currentPercentile <= 15 && expectancyPerTrade > 0;

      // === REGIME SCORE (simplified from trade distribution) ===
      const regimeScore = combinedTrades.length > 0
        ? (momentumTrades.length - meanReversionTrades.length) / combinedTrades.length
        : regime === 'momentum' ? 0.5 : regime === 'mean_reversion' ? -0.5 : 0;

      metrics.push({
        ticker,
        regime,
        regimeScore,
        inEntryZone,
        currentPercentile,
        entryBins,

        // Per-trade metrics (7d)
        winRate: expectancyMetrics.winRate,
        winRateCI: expectancyMetrics.winRateCI,
        avgWin: expectancyMetrics.avgWin * 100, // Convert to %
        avgLoss: expectancyMetrics.avgLoss * 100,
        expectancyPerTrade,
        expectancyCI: [
          expectancyMetrics.expectancyCI[0] * 100,
          expectancyMetrics.expectancyCI[1] * 100
        ],

        // Time-normalized
        avgHoldingDays: expectancyMetrics.avgHoldingDays,
        expectancyPerDay: expectancyMetrics.expectancyPerDay * 100, // Convert to %
        optimalHoldingDays: expectancyMetrics.optimalHoldingDays,
        diminishingReturnsDay: expectancyMetrics.diminishingReturnsDay,

        // Risk-adjusted
        stopDistancePct,
        riskPerTrade: expectancyMetrics.riskPerTrade,
        expectancyPer1PctRisk: expectancyMetrics.expectancyPer1PctRisk * 100,

        // Regime conditional
        expectancyMeanReversion: expectancyMR * 100,
        expectancyMomentum: expectancyMom * 100,

        // Statistical confidence
        confidenceScore: expectancyMetrics.confidenceScore,
        sampleSize: expectancyMetrics.sampleSize,

        // Composite scoring
        compositeScore: expectancyMetrics.compositeScore,
        compositeBreakdown: {
          expectancyContribution: expectancyMetrics.compositeBreakdown.expectancyContribution,
          confidenceContribution: expectancyMetrics.compositeBreakdown.confidenceContribution,
          percentileContribution: expectancyMetrics.compositeBreakdown.percentileContribution,
          rawScores: {
            expectancyRaw: expectancyMetrics.compositeBreakdown.rawScores.expectancyRaw * 100,
            confidenceRaw: expectancyMetrics.compositeBreakdown.rawScores.confidenceRaw,
            percentileRaw: expectancyMetrics.compositeBreakdown.rawScores.percentileRaw
          }
        },

        bestBinMean,
        bestBinTScore,
        strategyApplicable,
        reason,
      });
    });

    // Sort by composite score (highest first)
    return metrics.sort((a, b) => b.compositeScore - a.compositeScore);
  };

  const generateAllocations = (
    metrics: RiskMetrics[],
    metadata: Map<string, StockMetadata>,
    bins4H: Map<string, BinStatistic[]>
  ): AllocationDecision[] => {
    const TOTAL_CAPITAL = 100000;
    const MAX_POSITIONS = 5;

    // Filter to only strategy-applicable stocks with positive expectancy per trade
    const qualified = metrics.filter(m => m.strategyApplicable && m.expectancyPerTrade > 0.5);

    // Already sorted by composite score in calculateRiskMetrics
    // Take top 5
    const top = qualified.slice(0, MAX_POSITIONS);

    const decisions: AllocationDecision[] = top.map((metric, index) => {
      const meta = metadata.get(metric.ticker);

      // Use composite score from expectancy calculations (already calculated)
      const compositeScore = metric.compositeScore;

      // Allocation amount proportional to composite score
      const totalScores = top.reduce((sum, m) => sum + m.compositeScore, 0);
      const allocationPct = totalScores > 0 ? metric.compositeScore / totalScores : 1 / top.length;
      const allocation = TOTAL_CAPITAL * allocationPct;

      // Risk amount based on stop distance
      const riskAmount = allocation * (metric.stopDistancePct / 100);

      // Stop loss from stop distance calculation (ATR-based)
      const stopLoss = metric.stopDistancePct / 100;

      // Holding period from optimal holding calculation
      const holdingPeriod = `${metric.optimalHoldingDays - 3}-${metric.optimalHoldingDays + 3} days (optimal: ${metric.optimalHoldingDays}d)`;

      // Expected return based on expectancy per day and optimal holding
      const expectedReturn = metric.expectancyPerDay * metric.optimalHoldingDays;

      return {
        ticker: metric.ticker,
        rank: index + 1,
        allocatedCapital: allocation,
        positionSize: allocation,
        riskAmount,
        expectedReturn,
        entryZone: metric.entryBins.join(', '),
        stopLoss,
        targetExit: '50th percentile (strategy stops working above this)',
        holdingPeriod,
        compositeScore,
      };
    });

    return decisions;
  };

  const selectedMetrics = selectedTicker ? riskMetrics.find(m => m.ticker === selectedTicker) : null;
  const selectedMeta = selectedTicker ? stocksMetadata.get(selectedTicker) : null;

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, textAlign: 'center' }}>
        <CircularProgress size={60} />
        <Typography sx={{ mt: 2 }}>
          Analyzing {TICKERS.length} stocks for mean reversion opportunities in low percentile zones...
        </Typography>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4 }}>
        <Alert severity="error">
          <Typography variant="h6">Error Loading Framework Data</Typography>
          <Typography>{error}</Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            Make sure the backend is running: <code>cd backend && python api.py</code>
          </Typography>
        </Alert>
      </Container>
    );
  }

  if (riskMetrics.length === 0) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4 }}>
        <Alert severity="warning">
          No stocks with valid data found. Make sure backend has data for: {TICKERS.join(', ')}
        </Alert>
      </Container>
    );
  }

  if (viewMode === 'duration') {
    return (
      <Container maxWidth="xl" sx={{ mt: 2 }}>
        <Paper elevation={2} sx={{ mb: 2, p: 1, bgcolor: 'background.paper' }}>
          <Tabs
            value={viewMode}
            onChange={(_, value) => setViewMode(value as 'framework' | 'duration')}
            textColor="primary"
            indicatorColor="primary"
            variant="fullWidth"
          >
            <Tab value="framework" label="Swing Framework" />
            <Tab value="duration" label="Duration Analysis" />
          </Tabs>
        </Paper>

        <SwingDurationPanelV2
          tickers={TICKERS}
          selectedTicker={selectedTicker || TICKERS[0]}
          onTickerChange={setSelectedTicker}
        />
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 2 }}>
      <Paper elevation={2} sx={{ mb: 2, p: 1, bgcolor: 'background.paper' }}>
        <Tabs
          value={viewMode}
          onChange={(_, value) => setViewMode(value as 'framework' | 'duration')}
          textColor="primary"
          indicatorColor="primary"
          variant="fullWidth"
        >
          <Tab value="framework" label="Swing Framework" />
          <Tab value="duration" label="Duration Analysis" />
        </Tabs>
      </Paper>

      {/* Live Market State - All Buy Opportunities (Stocks + Indices) */}
      <Paper elevation={2} sx={{ mb: 2, p: 1, bgcolor: 'background.paper' }}>
        <Tabs
          value={timeframe}
          onChange={(_, value) => setTimeframe(value as 'daily' | '4hour')}
          textColor="primary"
          indicatorColor="primary"
          variant="fullWidth"
        >
          <Tab value="daily" label="Daily Analysis" />
          <Tab value="4hour" label="4-Hour Analysis" />
        </Tabs>
      </Paper>
      <CurrentMarketState timeframe={timeframe} />

      {/* Framework Header */}
      <Alert severity="info" icon={<Assessment />} sx={{ mb: 3 }}>
        <Typography variant="h6" fontWeight="bold">
          🎯 Swing Trading Framework - Mean Reversion Entry Strategy
        </Typography>
        <Typography variant="body2">
          <strong>Entry Focus:</strong> Buy at 0-5% and 5-15% percentile zones (extreme lows)<br/>
          <strong>Exit Target:</strong> 50th percentile (strategy effectiveness drops above 50%)<br/>
          <strong>Regime:</strong> Best for mean reversion stocks; also works for momentum pullbacks<br/>
          <strong>Holding:</strong> 3-21 days based on expected return
        </Typography>
      </Alert>

      <Grid container spacing={3}>
        {/* Strategic Allocation */}
        <Grid item xs={12}>
          <Paper elevation={4} sx={{ p: 3, bgcolor: 'primary.dark' }}>
            <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AccountBalance /> Strategic Capital Allocation ($100k Portfolio)
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Top {allocations.length} stocks with positive expectancy in low percentile entry zones
            </Typography>

            {allocations.length === 0 ? (
              <Alert severity="warning">
                No stocks currently meet strategy criteria (positive expectancy in 0-15% percentile zones)
              </Alert>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Rank</strong></TableCell>
                      <TableCell><strong>Ticker</strong></TableCell>
                      <TableCell align="right"><strong>Allocation</strong></TableCell>
                      <TableCell align="right"><strong>Risk (2%)</strong></TableCell>
                      <TableCell align="right"><strong>Expected Return</strong></TableCell>
                      <TableCell><strong>Entry Zone</strong></TableCell>
                      <TableCell align="right"><strong>Stop Loss</strong></TableCell>
                      <TableCell><strong>Exit Target</strong></TableCell>
                      <TableCell><strong>Holding Period</strong></TableCell>
                      <TableCell align="right"><strong>Score</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {allocations.map((decision) => (
                      <TableRow
                        key={decision.ticker}
                        hover
                        onClick={() => setSelectedTicker(decision.ticker)}
                        sx={{
                          cursor: 'pointer',
                          bgcolor: decision.ticker === selectedTicker ? 'action.selected' : 'transparent'
                        }}
                      >
                        <TableCell>#{decision.rank}</TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography fontWeight="bold">{decision.ticker}</Typography>
                            {decision.ticker === selectedTicker && (
                              <Chip label="Selected" size="small" color="primary" />
                            )}
                          </Box>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" fontWeight="bold" color="success.main">
                            ${decision.allocatedCapital.toLocaleString()}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" color="error.main">
                            ${decision.riskAmount.toLocaleString()}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Chip
                            label={`+${decision.expectedReturn.toFixed(2)}%`}
                            size="small"
                            color={decision.expectedReturn > 4 ? 'success' : decision.expectedReturn > 2 ? 'warning' : 'default'}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption">{decision.entryZone}</Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" color="text.secondary">
                            -{(decision.stopLoss * 100).toFixed(0)}%
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption">50th %ile</Typography>
                        </TableCell>
                        <TableCell>
                          <Chip label={decision.holdingPeriod} size="small" variant="outlined" />
                        </TableCell>
                        <TableCell align="right">
                          <Chip
                            label={(decision.compositeScore * 100).toFixed(0)}
                            size="small"
                            color={decision.compositeScore > 0.7 ? 'success' : 'warning'}
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>
        </Grid>

        {/* Comprehensive Risk-Adjusted Expectancy with Time Frames & CI */}
        {selectedMetrics && (
          <Grid item xs={12} md={6}>
            <Card elevation={3}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <ShowChart /> Risk-Adjusted Expectancy - {selectedTicker}
                  <Tooltip title="All metrics calculated from 7-day lookback window with bootstrap confidence intervals">
                    <Info fontSize="small" sx={{ ml: 1, color: 'text.secondary' }} />
                  </Tooltip>
                </Typography>

                {/* Strategy Applicability */}
                <Alert
                  severity={selectedMetrics.strategyApplicable ? 'success' : 'error'}
                  icon={selectedMetrics.strategyApplicable ? <CheckCircle /> : <Cancel />}
                  sx={{ mb: 2 }}
                >
                  <Typography variant="body2">
                    <strong>Strategy Status:</strong> {selectedMetrics.strategyApplicable ? 'APPLICABLE' : 'NOT APPLICABLE'}
                  </Typography>
                  <Typography variant="caption">{selectedMetrics.reason}</Typography>
                </Alert>

                <Grid container spacing={2} sx={{ mt: 1 }}>
                  {/* Per-Trade Expectancy */}
                  <Grid item xs={6}>
                    <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                      <Typography variant="caption" color="text.secondary">Expectancy Per Trade (7d)</Typography>
                      <Typography
                        variant="h4"
                        color={selectedMetrics.expectancyPerTrade > 0 ? 'success.main' : 'error.main'}
                        fontWeight="bold"
                      >
                        {selectedMetrics.expectancyPerTrade > 0 ? '+' : ''}{selectedMetrics.expectancyPerTrade.toFixed(2)}%
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        95% CI: [{selectedMetrics.expectancyCI[0].toFixed(2)}%, {selectedMetrics.expectancyCI[1].toFixed(2)}%]
                      </Typography>
                    </Box>
                  </Grid>

                  {/* Per-Day Expectancy (Time-Normalized) */}
                  <Grid item xs={6}>
                    <Box sx={{ p: 2, bgcolor: 'success.light', borderRadius: 1 }}>
                      <Typography variant="caption" color="text.secondary">Expectancy Per Day (7d)</Typography>
                      <Typography variant="h4" color="success.dark" fontWeight="bold">
                        {selectedMetrics.expectancyPerDay > 0 ? '+' : ''}{selectedMetrics.expectancyPerDay.toFixed(3)}%
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Avg hold: {selectedMetrics.avgHoldingDays.toFixed(1)} days
                      </Typography>
                    </Box>
                  </Grid>

                  {/* Win Rate with CI */}
                  <Grid item xs={6}>
                    <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                      <Typography variant="caption" color="text.secondary">Win Rate (7d)</Typography>
                      <Typography variant="h5" color="primary.main" fontWeight="bold">
                        {(selectedMetrics.winRate * 100).toFixed(1)}%
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        95% CI: [{(selectedMetrics.winRateCI[0] * 100).toFixed(1)}%, {(selectedMetrics.winRateCI[1] * 100).toFixed(1)}%]
                      </Typography>
                    </Box>
                  </Grid>

                  {/* Sample Size & Confidence */}
                  <Grid item xs={6}>
                    <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                      <Typography variant="caption" color="text.secondary">Statistical Confidence</Typography>
                      <Typography variant="h5" color="success.main" fontWeight="bold">
                        {(selectedMetrics.confidenceScore * 100).toFixed(1)}%
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        n={selectedMetrics.sampleSize} trades
                      </Typography>
                    </Box>
                  </Grid>

                  {/* Avg Win/Loss */}
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Avg Win (7d)</Typography>
                    <Typography variant="h6" color="success.main">+{selectedMetrics.avgWin.toFixed(2)}%</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Avg Loss (7d)</Typography>
                    <Typography variant="h6" color="error.main">-{selectedMetrics.avgLoss.toFixed(2)}%</Typography>
                  </Grid>

                  {/* Risk-Adjusted Metrics */}
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Stop Distance</Typography>
                    <Typography variant="h6">{selectedMetrics.stopDistancePct.toFixed(2)}%</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">E per 1% Risk</Typography>
                    <Typography variant="h6">{selectedMetrics.expectancyPer1PctRisk.toFixed(2)}%</Typography>
                  </Grid>

                  {/* Holding Period Analysis */}
                  <Grid item xs={12}>
                    <Box sx={{ p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                      <Typography variant="caption" color="text.secondary">Optimal Holding Period</Typography>
                      <Typography variant="body1" fontWeight="bold">
                        {selectedMetrics.optimalHoldingDays} days (returns flatten after day {selectedMetrics.diminishingReturnsDay})
                      </Typography>
                    </Box>
                  </Grid>

                  {/* Regime Conditional Expectancy */}
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">E (Mean Reversion)</Typography>
                    <Typography variant="body2" color={selectedMetrics.expectancyMeanReversion > 0 ? 'success.main' : 'error.main'}>
                      {selectedMetrics.expectancyMeanReversion > 0 ? '+' : ''}{selectedMetrics.expectancyMeanReversion.toFixed(2)}%
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">E (Momentum)</Typography>
                    <Typography variant="body2" color={selectedMetrics.expectancyMomentum > 0 ? 'success.main' : 'error.main'}>
                      {selectedMetrics.expectancyMomentum > 0 ? '+' : ''}{selectedMetrics.expectancyMomentum.toFixed(2)}%
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Regime & Entry Zones */}
        {selectedMetrics && selectedMeta && (
          <Grid item xs={12} md={6}>
            <Card elevation={3}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📊 Market Regime & Entry Zones - {selectedTicker}
                </Typography>

                <Box sx={{ mb: 3 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>Market Regime</Typography>
                  <Chip
                    label={selectedMetrics.regime.replace('_', ' ').toUpperCase()}
                    color={selectedMetrics.regime === 'mean_reversion' ? 'success' : 'warning'}
                    sx={{ fontSize: '1rem', py: 2.5, px: 1 }}
                  />
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    {selectedMeta.characteristics.is_mean_reverter && 'Best for buying extreme lows'}
                    {selectedMeta.characteristics.is_momentum && 'Buy pullbacks in uptrends'}
                  </Typography>
                </Box>

                <Box sx={{ mb: 3 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>Entry Zones (Low Percentiles)</Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {selectedMetrics.entryBins.map(bin => (
                      <Chip key={bin} label={bin} size="small" color="success" variant="outlined" />
                    ))}
                  </Box>
                  <Typography variant="caption" display="block" sx={{ mt: 1 }} color="success.main">
                    ✓ Strategy works in these zones
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>Exit Target</Typography>
                  <Alert severity="warning" icon={<Warning />}>
                    <Typography variant="body2">
                      <strong>50th Percentile:</strong> Strategy effectiveness drops above 50% percentile. Take profits and exit.
                    </Typography>
                  </Alert>
                </Box>

                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>Best Performing Bin</Typography>
                  <Typography variant="body1">{selectedMeta.best_4h_bin}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Mean: {selectedMetrics.bestBinMean.toFixed(2)}% | T-Score: {selectedMetrics.bestBinTScore.toFixed(2)}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Complete Rankings with Transparent Composite Scoring */}
        <Grid item xs={12}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">
                📈 Complete Risk-Adjusted Rankings
              </Typography>
              <Tooltip title="Composite Score = 60% Expectancy/Day + 25% Confidence + 15% Percentile Extremeness">
                <Chip
                  icon={<Info />}
                  label="Scoring Breakdown"
                  size="small"
                  variant="outlined"
                  color="info"
                />
              </Tooltip>
            </Box>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Rank</strong></TableCell>
                    <TableCell><strong>Ticker</strong></TableCell>
                    <TableCell align="right">
                      <Tooltip title="Expectancy per trade with 95% bootstrap confidence interval">
                        <span><strong>E/Trade (7d)</strong></span>
                      </Tooltip>
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Time-normalized expectancy per day">
                        <span><strong>E/Day (7d)</strong></span>
                      </Tooltip>
                    </TableCell>
                    <TableCell align="right"><strong>Win Rate</strong></TableCell>
                    <TableCell align="right"><strong>Composite Score</strong></TableCell>
                    <TableCell><strong>Score Breakdown</strong></TableCell>
                    <TableCell><strong>Status</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {riskMetrics.map((metric, index) => (
                    <TableRow
                      key={metric.ticker}
                      hover
                      onClick={() => setSelectedTicker(metric.ticker)}
                      sx={{
                        cursor: 'pointer',
                        bgcolor: metric.ticker === selectedTicker ? 'action.selected' : 'transparent'
                      }}
                    >
                      <TableCell>#{index + 1}</TableCell>
                      <TableCell>
                        <Typography fontWeight={metric.ticker === selectedTicker ? 'bold' : 'normal'}>
                          {metric.ticker}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {metric.regime === 'mean_reversion' ? 'Mean Rev' : 'Momentum'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography
                          variant="body2"
                          color={metric.expectancyPerTrade > 0 ? 'success.main' : 'error.main'}
                          fontWeight="bold"
                        >
                          {metric.expectancyPerTrade > 0 ? '+' : ''}{metric.expectancyPerTrade.toFixed(2)}%
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          [{metric.expectancyCI[0].toFixed(1)}, {metric.expectancyCI[1].toFixed(1)}]
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography
                          variant="body2"
                          color="success.main"
                          fontWeight="bold"
                        >
                          {metric.expectancyPerDay > 0 ? '+' : ''}{metric.expectancyPerDay.toFixed(3)}%
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {metric.avgHoldingDays.toFixed(1)}d hold
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {(metric.winRate * 100).toFixed(1)}%
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          n={metric.sampleSize}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          label={(metric.compositeScore * 100).toFixed(1)}
                          size="small"
                          color={metric.compositeScore > 0.6 ? 'success' : metric.compositeScore > 0.4 ? 'warning' : 'default'}
                        />
                      </TableCell>
                      <TableCell>
                        <Tooltip title={`
                          Expectancy (60%): ${(metric.compositeBreakdown.expectancyContribution * 100).toFixed(1)}
                          Confidence (25%): ${(metric.compositeBreakdown.confidenceContribution * 100).toFixed(1)}
                          Percentile (15%): ${(metric.compositeBreakdown.percentileContribution * 100).toFixed(1)}
                        `}>
                          <Box sx={{ display: 'flex', gap: 0.5 }}>
                            <Chip
                              label={`E:${(metric.compositeBreakdown.expectancyContribution * 100).toFixed(0)}`}
                              size="small"
                              variant="outlined"
                              sx={{ fontSize: '0.7rem', height: 20 }}
                            />
                            <Chip
                              label={`C:${(metric.compositeBreakdown.confidenceContribution * 100).toFixed(0)}`}
                              size="small"
                              variant="outlined"
                              sx={{ fontSize: '0.7rem', height: 20 }}
                            />
                            <Chip
                              label={`P:${(metric.compositeBreakdown.percentileContribution * 100).toFixed(0)}`}
                              size="small"
                              variant="outlined"
                              sx={{ fontSize: '0.7rem', height: 20 }}
                            />
                          </Box>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        {metric.strategyApplicable ? (
                          <Chip icon={<CheckCircle />} label="✓" size="small" color="success" />
                        ) : (
                          <Chip icon={<Cancel />} label="✗" size="small" color="error" />
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {/* Legend */}
            <Box sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
              <Typography variant="caption" color="text.secondary">
                <strong>Legend:</strong> E/Trade = Expectancy per trade | E/Day = Expectancy per day (time-normalized) |
                Score Breakdown: E=Expectancy(60%), C=Confidence(25%), P=Percentile(15%) |
                All metrics from 7-day lookback with bootstrap CI
              </Typography>
            </Box>
          </Paper>
        </Grid>

        {/* Strategy Foundation */}
        <Grid item xs={12}>
          <Alert severity="success" icon={<CheckCircle />}>
            <Typography variant="body2">
              <strong>Foundation:</strong> All expectancy calculations derived from YOUR percentile bin statistics (mean, t-score, significance).<br/>
              <strong>Entry:</strong> Focus on 0-5% and 5-15% percentile bins only (extreme lows).<br/>
              <strong>Exit:</strong> Target 50th percentile - strategy effectiveness drops above this level.<br/>
              <strong>Regime:</strong> Works best for mean reversion stocks, but also effective for momentum pullbacks.
            </Typography>
          </Alert>
        </Grid>
      </Grid>
    </Container>
  );
};

export default SwingTradingFramework;
