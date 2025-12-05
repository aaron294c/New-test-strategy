/**
 * Core TypeScript interfaces for the principle-led multi-timeframe trading framework
 *
 * Design Philosophy:
 * - Principle-led: Minimal hardcoded parameters, adaptive thresholds
 * - Multi-timeframe: All structures support timeframe aggregation
 * - Extensible: Easy to add new regime types, factors, and instruments
 */

// ==================== TIMEFRAME TYPES ====================

export enum Timeframe {
  M1 = '1m',
  M5 = '5m',
  M15 = '15m',
  M30 = '30m',
  H1 = '1h',
  H4 = '4h',
  D1 = '1d',
  W1 = '1w',
}

export interface TimeframeWeight {
  timeframe: Timeframe;
  weight: number; // 0-1, sum of all weights should equal 1
}

// ==================== REGIME DETECTION ====================

export enum RegimeType {
  MOMENTUM = 'momentum',
  MEAN_REVERSION = 'mean_reversion',
  NEUTRAL = 'neutral',
  TRANSITION = 'transition', // Regime change in progress
}

export interface RegimeSignal {
  type: RegimeType;
  confidence: number; // 0-1
  strength: number; // How strong is the regime (-1 to 1)
  timeframe: Timeframe;
  timestamp: Date;
  metrics: {
    trendStrength?: number; // ADX-like measure
    volatilityRatio?: number; // Current vs historical
    meanReversionSpeed?: number; // How quickly price returns to mean
    momentumPersistence?: number; // How long momentum trends last
  };
}

export interface MultiTimeframeRegime {
  regimes: RegimeSignal[];
  coherence: number; // 0-1, how aligned are the timeframes
  dominantRegime: RegimeType;
  timestamp: Date;
}

// ==================== PERCENTILE LOGIC ====================

export interface PercentileData {
  value: number;
  percentile: number; // 0-100
  lookbackPeriod: number; // How many bars used for calculation
  timeframe: Timeframe;
}

export interface PercentileEntry {
  instrument: string;
  currentPrice: number;
  percentileLevel: PercentileData;
  entryThreshold: number; // Adaptive percentile threshold (e.g., 95th)
  direction: 'long' | 'short';
  timestamp: Date;
}

export interface AdaptiveStopLoss {
  initialStop: number;
  currentStop: number;
  percentileBased: PercentileData; // Stop based on historical move percentiles
  atrMultiplier?: number; // Optional ATR-based component
  riskAmount: number; // Dollar or percentage risk
  updateReason?: string; // Why the stop was adjusted
  timestamp: Date;
}

// ==================== RISK & EXPECTANCY ====================

export interface RiskMetrics {
  winRate: number; // 0-1
  avgWin: number;
  avgLoss: number;
  winLossRatio: number; // avgWin / avgLoss
  expectancy: number; // (winRate * avgWin) - (lossRate * avgLoss)
  sharpeRatio?: number;
  maxDrawdown?: number;
  recoveryFactor?: number;
  sampleSize: number; // Number of trades in calculation
}

export interface RiskAdjustedExpectancy {
  baseExpectancy: number;
  volatilityAdjustment: number; // Adjustment factor based on current volatility
  regimeAdjustment: number; // Adjustment based on regime favorability
  finalExpectancy: number;
  confidence: number; // 0-1, statistical confidence in the calculation
  instrument: string;
  timestamp: Date;
}

// ==================== COMPOSITE SCORING ====================

export interface ScoringFactor {
  name: string;
  value: number; // Normalized 0-1 or -1 to 1
  weight: number; // Importance weight 0-1
  category: 'technical' | 'fundamental' | 'sentiment' | 'regime' | 'risk';
}

export interface CompositeScore {
  instrument: string;
  totalScore: number; // Weighted aggregate
  factors: ScoringFactor[];
  rank?: number; // Relative rank among all instruments
  percentile?: number; // Score percentile 0-100
  timestamp: Date;
  timeframeScores?: Map<Timeframe, number>; // Multi-timeframe breakdown
}

// ==================== CAPITAL ALLOCATION ====================

export interface Position {
  instrument: string;
  direction: 'long' | 'short';
  entryPrice: number;
  currentPrice: number;
  quantity: number;
  positionValue: number;
  unrealizedPnL: number;
  riskAmount: number;
  stopLoss: AdaptiveStopLoss;
  compositeScore: CompositeScore;
  openedAt: Date;
  timeframe: Timeframe;
}

export interface AllocationParameters {
  totalCapital: number;
  maxRiskPerTrade: number; // Percentage of capital (e.g., 0.01 = 1%)
  maxTotalRisk: number; // Max combined risk across all positions
  maxPositions: number;
  minScore: number; // Minimum composite score to consider
  diversificationRules?: {
    maxPerSector?: number;
    maxCorrelatedPositions?: number;
  };
}

export interface AllocationDecision {
  instrument: string;
  allocatedCapital: number;
  positionSize: number;
  riskAmount: number;
  justification: string;
  score: number;
  priority: number; // 1 = highest priority
  timestamp: Date;
}

// ==================== MARKET DATA ====================

export interface OHLCV {
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  timestamp: Date;
  timeframe: Timeframe;
}

export interface MarketData {
  instrument: string;
  bars: OHLCV[];
  currentPrice: number;
  bid?: number;
  ask?: number;
  spread?: number;
  lastUpdate: Date;
}

// ==================== FRAMEWORK CONFIGURATION ====================

export interface FrameworkConfig {
  // Timeframe settings
  timeframes: TimeframeWeight[];
  primaryTimeframe: Timeframe;

  // Regime detection
  regimeDetection: {
    lookbackPeriod: number;
    coherenceThreshold: number; // Min coherence to act
    updateFrequency: number; // Minutes between updates
  };

  // Percentile logic
  percentileSettings: {
    entryPercentile: number; // Default entry threshold
    stopPercentile: number; // Default stop threshold
    lookbackBars: number;
    adaptive: boolean; // Adjust thresholds based on regime
  };

  // Risk management
  riskManagement: {
    maxRiskPerTrade: number;
    maxTotalRisk: number;
    maxPositions: number;
    minWinRate: number; // Min acceptable win rate
    minExpectancy: number; // Min acceptable expectancy
  };

  // Scoring
  scoring: {
    factors: ScoringFactor[];
    minScore: number;
    rebalanceFrequency: number; // Minutes between score recalculation
  };

  // Capital allocation
  allocation: AllocationParameters;

  // General settings
  updateInterval: number; // Milliseconds between framework updates
  logLevel: 'debug' | 'info' | 'warn' | 'error';
}

// ==================== FRAMEWORK STATE ====================

export interface FrameworkState {
  config: FrameworkConfig;
  currentRegime: MultiTimeframeRegime;
  positions: Position[];
  scores: Map<string, CompositeScore>;
  allocations: Map<string, AllocationDecision>;
  marketData: Map<string, MarketData>;
  lastUpdate: Date;
  isActive: boolean;
  metrics: {
    totalPnL: number;
    totalRiskExposure: number;
    averageScore: number;
    regimeCoherence: number;
  };
}

// ==================== EVENT TYPES ====================

export enum EventType {
  REGIME_CHANGE = 'regime_change',
  ENTRY_SIGNAL = 'entry_signal',
  EXIT_SIGNAL = 'exit_signal',
  STOP_ADJUSTMENT = 'stop_adjustment',
  SCORE_UPDATE = 'score_update',
  ALLOCATION_CHANGE = 'allocation_change',
  POSITION_OPENED = 'position_opened',
  POSITION_CLOSED = 'position_closed',
  ERROR = 'error',
}

export interface FrameworkEvent {
  type: EventType;
  timestamp: Date;
  data: any;
  instrument?: string;
  severity?: 'low' | 'medium' | 'high';
  message: string;
}

export type EventHandler = (event: FrameworkEvent) => void | Promise<void>;
