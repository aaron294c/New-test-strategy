/**
 * Historical Backtesting Module for Trading Framework
 *
 * Features:
 * - Replays historical market data through the trading framework
 * - Simulates order execution with realistic slippage and transaction costs
 * - Tracks all signals, entries, exits, and PnL
 * - Calculates comprehensive performance metrics (Sharpe, max DD, win rate, etc.)
 * - Generates detailed trade logs and performance reports
 * - Regime-specific performance analysis
 * - Statistical confidence intervals
 */

import {
  FrameworkConfig,
  OHLCV,
  MarketData,
  Timeframe,
  Position,
  RegimeType,
  FrameworkEvent,
  EventType,
  CompositeScore,
  AllocationDecision,
} from '../core/types';

import { TradingFramework } from '../core/TradingFramework';
import { TradeResult } from '../risk-expectancy/ExpectancyCalculator';

/**
 * Configuration for backtest execution
 */
export interface BacktestConfig {
  /** Starting capital for the backtest */
  initialCapital: number;

  /** Slippage model configuration */
  slippage: {
    /** Fixed slippage in basis points (e.g., 5 = 0.05%) */
    basisPoints: number;
    /** Variable slippage based on volatility */
    useVolatilityAdjusted: boolean;
    /** Max slippage cap in basis points */
    maxBasisPoints: number;
  };

  /** Transaction costs */
  costs: {
    /** Commission per trade (dollars or percentage) */
    commission: number;
    /** Commission type: 'fixed' or 'percentage' */
    commissionType: 'fixed' | 'percentage';
    /** Additional fees per trade */
    additionalFees: number;
  };

  /** Enable/disable specific features */
  features: {
    /** Track intrabar price action (more realistic fills) */
    intrabarExecution: boolean;
    /** Simulate partial fills for large orders */
    partialFills: boolean;
    /** Account for market impact */
    marketImpact: boolean;
  };

  /** Date range for backtest */
  startDate: Date;
  endDate: Date;

  /** Warmup period (bars before start date for indicators) */
  warmupBars: number;
}

/**
 * Individual trade record
 */
export interface Trade {
  id: string;
  instrument: string;
  direction: 'long' | 'short';
  entryTime: Date;
  entryPrice: number;
  exitTime?: Date;
  exitPrice?: number;
  quantity: number;
  positionSize: number;
  riskAmount: number;
  stopLoss: number;
  initialStop: number;
  regime: RegimeType;
  compositeScore: number;
  slippage: number;
  commission: number;
  fees: number;
  pnl?: number;
  pnlPercent?: number;
  rMultiple?: number;
  exitReason?: string;
  holdingPeriodBars?: number;
  maxAdverseExcursion?: number;
  maxFavorableExcursion?: number;
}

/**
 * Performance metrics for backtest results
 */
export interface PerformanceMetrics {
  // Overall metrics
  totalReturn: number;
  totalReturnPercent: number;
  cagr: number;
  sharpeRatio: number;
  sortinoRatio: number;
  calmarRatio: number;

  // Trade statistics
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  avgWin: number;
  avgLoss: number;
  avgWinPercent: number;
  avgLossPercent: number;
  winLossRatio: number;
  expectancy: number;
  expectancyPercent: number;

  // Risk metrics
  maxDrawdown: number;
  maxDrawdownPercent: number;
  maxDrawdownDuration: number;
  avgDrawdown: number;
  recoveryFactor: number;
  avgMAE: number;
  avgMFE: number;

  // Position metrics
  avgHoldingPeriod: number;
  avgPositionSize: number;
  maxPositionSize: number;
  avgRiskPerTrade: number;

  // Costs
  totalSlippage: number;
  totalCommission: number;
  totalFees: number;
  totalCosts: number;
  costsAsPercentOfPnL: number;

  // Time-based
  tradingDays: number;
  avgTradesPerDay: number;
  avgTradesPerMonth: number;

  // Consistency
  profitFactor: number;
  ulcerIndex: number;
  maxConsecutiveWins: number;
  maxConsecutiveLosses: number;

  // Statistical
  standardDeviation: number;
  downSideDeviation: number;
  skewness: number;
  kurtosis: number;

  // Confidence intervals (95%)
  expectedReturnLower: number;
  expectedReturnUpper: number;
}

/**
 * Regime-specific performance breakdown
 */
export interface RegimePerformance {
  regime: RegimeType;
  metrics: PerformanceMetrics;
  trades: number;
  totalPnL: number;
  winRate: number;
}

/**
 * Equity curve data point
 */
export interface EquityCurvePoint {
  timestamp: Date;
  equity: number;
  drawdown: number;
  drawdownPercent: number;
  openPositions: number;
  dailyReturn: number;
}

/**
 * Complete backtest results
 */
export interface BacktestResults {
  config: BacktestConfig;
  frameworkConfig: FrameworkConfig;

  // Performance
  metrics: PerformanceMetrics;
  regimePerformance: Map<RegimeType, RegimePerformance>;

  // Trade data
  trades: Trade[];
  openTrades: Trade[];

  // Equity curve
  equityCurve: EquityCurvePoint[];

  // Monthly breakdown
  monthlyReturns: Map<string, number>;

  // Events log
  events: FrameworkEvent[];

  // Summary
  startDate: Date;
  endDate: Date;
  durationDays: number;
  initialCapital: number;
  finalCapital: number;
}

/**
 * Historical Backtester - Replays market data through the framework
 */
export class HistoricalBacktester {
  private config: BacktestConfig;
  private framework: TradingFramework;

  // State tracking
  private currentCapital: number;
  private trades: Trade[] = [];
  private openTrades: Map<string, Trade> = new Map();
  private equityCurve: EquityCurvePoint[] = [];
  private events: FrameworkEvent[] = [];
  private currentBar: number = 0;

  // Market data storage
  private historicalData: Map<string, OHLCV[]> = new Map();

  constructor(
    frameworkConfig: Partial<FrameworkConfig>,
    backtestConfig: Partial<BacktestConfig>
  ) {
    // Initialize framework
    this.framework = new TradingFramework(frameworkConfig);

    // Set default backtest config
    this.config = {
      initialCapital: backtestConfig.initialCapital ?? 100000,
      slippage: {
        basisPoints: backtestConfig.slippage?.basisPoints ?? 5,
        useVolatilityAdjusted: backtestConfig.slippage?.useVolatilityAdjusted ?? true,
        maxBasisPoints: backtestConfig.slippage?.maxBasisPoints ?? 20,
      },
      costs: {
        commission: backtestConfig.costs?.commission ?? 1.0,
        commissionType: backtestConfig.costs?.commissionType ?? 'fixed',
        additionalFees: backtestConfig.costs?.additionalFees ?? 0,
      },
      features: {
        intrabarExecution: backtestConfig.features?.intrabarExecution ?? true,
        partialFills: backtestConfig.features?.partialFills ?? false,
        marketImpact: backtestConfig.features?.marketImpact ?? false,
      },
      startDate: backtestConfig.startDate ?? new Date('2020-01-01'),
      endDate: backtestConfig.endDate ?? new Date(),
      warmupBars: backtestConfig.warmupBars ?? 200,
    };

    this.currentCapital = this.config.initialCapital;

    // Subscribe to framework events
    this.subscribeToEvents();
  }

  /**
   * Load historical market data for instruments
   */
  public loadMarketData(instrument: string, bars: OHLCV[]): void {
    // Sort bars by timestamp
    const sortedBars = [...bars].sort(
      (a, b) => a.timestamp.getTime() - b.timestamp.getTime()
    );

    this.historicalData.set(instrument, sortedBars);
  }

  /**
   * Run the backtest
   */
  public async runBacktest(): Promise<BacktestResults> {
    console.log('Starting backtest...');
    console.log(`Period: ${this.config.startDate.toISOString()} to ${this.config.endDate.toISOString()}`);
    console.log(`Initial Capital: $${this.config.initialCapital.toLocaleString()}`);

    // Reset state
    this.resetState();

    // Determine all unique timestamps across instruments
    const allTimestamps = this.getAllTimestamps();
    console.log(`Processing ${allTimestamps.length} bars...`);

    // Main backtest loop
    for (let i = 0; i < allTimestamps.length; i++) {
      const timestamp = allTimestamps[i];
      this.currentBar = i;

      // Skip warmup period
      if (i < this.config.warmupBars) {
        this.feedMarketData(timestamp, true);
        continue;
      }

      // Check if within backtest date range
      if (timestamp < this.config.startDate) continue;
      if (timestamp > this.config.endDate) break;

      // Feed market data to framework
      this.feedMarketData(timestamp, false);

      // Process open positions (check stops, exits)
      this.processOpenPositions(timestamp);

      // Process new signals from framework
      this.processNewSignals(timestamp);

      // Record equity curve point
      this.recordEquityPoint(timestamp);

      // Progress indicator
      if (i % 100 === 0) {
        const progress = ((i / allTimestamps.length) * 100).toFixed(1);
        console.log(`Progress: ${progress}% (Bar ${i}/${allTimestamps.length})`);
      }
    }

    // Close any remaining open positions
    this.closeAllPositions(allTimestamps[allTimestamps.length - 1]);

    console.log('Backtest complete. Generating results...');

    // Generate and return results
    return this.generateResults();
  }

  /**
   * Reset backtester state
   */
  private resetState(): void {
    this.currentCapital = this.config.initialCapital;
    this.trades = [];
    this.openTrades.clear();
    this.equityCurve = [];
    this.events = [];
    this.currentBar = 0;
  }

  /**
   * Get all unique timestamps from all instruments
   */
  private getAllTimestamps(): Date[] {
    const timestampSet = new Set<number>();

    for (const bars of this.historicalData.values()) {
      bars.forEach(bar => timestampSet.add(bar.timestamp.getTime()));
    }

    const timestamps = Array.from(timestampSet)
      .map(ts => new Date(ts))
      .sort((a, b) => a.getTime() - b.getTime());

    return timestamps;
  }

  /**
   * Feed market data to framework for a specific timestamp
   */
  private feedMarketData(timestamp: Date, isWarmup: boolean): void {
    for (const [instrument, bars] of this.historicalData) {
      // Find all bars up to current timestamp
      const availableBars = bars.filter(
        bar => bar.timestamp.getTime() <= timestamp.getTime()
      );

      if (availableBars.length === 0) continue;

      const currentBar = availableBars[availableBars.length - 1];

      // Create MarketData object
      const marketData: MarketData = {
        instrument,
        bars: availableBars,
        currentPrice: currentBar.close,
        bid: currentBar.close - (currentBar.close * 0.0001), // Simulate spread
        ask: currentBar.close + (currentBar.close * 0.0001),
        spread: currentBar.close * 0.0002,
        lastUpdate: timestamp,
      };

      this.framework.addMarketData(instrument, marketData);
    }

    // Don't start framework during warmup
    if (!isWarmup && !this.framework.getState().isActive) {
      this.framework.start();
    }
  }

  /**
   * Process open positions - check stops and exits
   */
  private processOpenPositions(timestamp: Date): void {
    const state = this.framework.getState();

    for (const position of state.positions) {
      const trade = this.openTrades.get(position.instrument);
      if (!trade) continue;

      const marketData = state.marketData.get(position.instrument);
      if (!marketData) continue;

      const currentBar = this.getCurrentBar(position.instrument, timestamp);
      if (!currentBar) continue;

      // Update MAE/MFE
      this.updateTradeExcursions(trade, currentBar, position);

      // Check if stop loss hit (intrabar execution)
      if (this.config.features.intrabarExecution) {
        const stopHit = this.checkIntrabarStop(trade, currentBar);
        if (stopHit) {
          this.closePosition(trade, stopHit.price, timestamp, 'Stop Loss');
          continue;
        }
      }

      // Check exit signal from framework
      // (Framework already handles this in its update cycle)
    }
  }

  /**
   * Process new entry signals from framework
   */
  private processNewSignals(timestamp: Date): void {
    const state = this.framework.getState();

    // Check for new allocations (entry signals)
    for (const [instrument, allocation] of state.allocations) {
      // Skip if already have position
      if (this.openTrades.has(instrument)) continue;

      const marketData = state.marketData.get(instrument);
      if (!marketData) continue;

      const score = state.scores.get(instrument);
      if (!score) continue;

      // Execute entry
      this.executeEntry(instrument, allocation, marketData, score, timestamp);
    }
  }

  /**
   * Execute entry order
   */
  private executeEntry(
    instrument: string,
    allocation: AllocationDecision,
    marketData: MarketData,
    score: CompositeScore,
    timestamp: Date
  ): void {
    const currentBar = this.getCurrentBar(instrument, timestamp);
    if (!currentBar) return;

    // Calculate entry price with slippage
    const direction: 'long' | 'short' = allocation.positionSize > 0 ? 'long' : 'short';
    const entryPrice = this.calculateEntryPrice(
      direction === 'long' ? currentBar.close : currentBar.close,
      direction,
      currentBar
    );

    // Calculate position size
    const quantity = Math.abs(allocation.positionSize);
    const positionSize = entryPrice * quantity;

    // Check if we have enough capital
    if (positionSize > this.currentCapital * 0.95) {
      console.log(`Insufficient capital for ${instrument}: Need $${positionSize}, have $${this.currentCapital}`);
      return;
    }

    // Calculate costs
    const commission = this.calculateCommission(positionSize);
    const fees = this.config.costs.additionalFees;
    const slippage = Math.abs(entryPrice - currentBar.close);

    // Create trade record
    const trade: Trade = {
      id: `${instrument}_${timestamp.getTime()}`,
      instrument,
      direction,
      entryTime: timestamp,
      entryPrice,
      quantity,
      positionSize,
      riskAmount: allocation.riskAmount,
      stopLoss: 0, // Will be set from framework position
      initialStop: 0,
      regime: this.framework.getState().currentRegime.dominantRegime,
      compositeScore: score.totalScore,
      slippage,
      commission,
      fees,
      maxAdverseExcursion: 0,
      maxFavorableExcursion: 0,
    };

    // Deduct capital
    this.currentCapital -= (positionSize + commission + fees);

    this.openTrades.set(instrument, trade);

    console.log(`ENTRY: ${instrument} ${direction} @ $${entryPrice.toFixed(2)} | Size: $${positionSize.toFixed(2)} | Score: ${score.totalScore.toFixed(2)}`);
  }

  /**
   * Close position
   */
  private closePosition(
    trade: Trade,
    exitPrice: number,
    timestamp: Date,
    reason: string
  ): void {
    trade.exitTime = timestamp;
    trade.exitPrice = exitPrice;
    trade.exitReason = reason;

    // Calculate holding period
    trade.holdingPeriodBars = this.calculateHoldingPeriod(trade);

    // Calculate PnL
    const positionValue = exitPrice * trade.quantity;
    const commission = this.calculateCommission(positionValue);
    const fees = this.config.costs.additionalFees;

    const grossPnL = trade.direction === 'long'
      ? (exitPrice - trade.entryPrice) * trade.quantity
      : (trade.entryPrice - exitPrice) * trade.quantity;

    const netPnL = grossPnL - commission - fees - (trade.slippage * trade.quantity);

    trade.pnl = netPnL;
    trade.pnlPercent = (netPnL / trade.positionSize) * 100;
    trade.rMultiple = trade.riskAmount > 0 ? netPnL / trade.riskAmount : 0;
    trade.commission += commission;
    trade.fees += fees;

    // Return capital
    this.currentCapital += positionValue + netPnL;

    // Move to closed trades
    this.trades.push(trade);
    this.openTrades.delete(trade.instrument);

    console.log(`EXIT: ${trade.instrument} @ $${exitPrice.toFixed(2)} | PnL: $${netPnL.toFixed(2)} (${trade.pnlPercent?.toFixed(2)}%) | Reason: ${reason}`);
  }

  /**
   * Close all open positions (end of backtest)
   */
  private closeAllPositions(timestamp: Date): void {
    for (const [instrument, trade] of this.openTrades) {
      const currentBar = this.getCurrentBar(instrument, timestamp);
      if (currentBar) {
        this.closePosition(trade, currentBar.close, timestamp, 'End of Backtest');
      }
    }
  }

  /**
   * Calculate entry price with slippage
   */
  private calculateEntryPrice(
    basePrice: number,
    direction: 'long' | 'short',
    bar: OHLCV
  ): number {
    let slippageBps = this.config.slippage.basisPoints;

    // Adjust for volatility if enabled
    if (this.config.slippage.useVolatilityAdjusted) {
      const barRange = (bar.high - bar.low) / bar.close;
      slippageBps = Math.min(
        slippageBps * (1 + barRange * 10),
        this.config.slippage.maxBasisPoints
      );
    }

    const slippageAmount = basePrice * (slippageBps / 10000);

    return direction === 'long'
      ? basePrice + slippageAmount
      : basePrice - slippageAmount;
  }

  /**
   * Calculate commission
   */
  private calculateCommission(positionSize: number): number {
    if (this.config.costs.commissionType === 'fixed') {
      return this.config.costs.commission;
    } else {
      return positionSize * (this.config.costs.commission / 100);
    }
  }

  /**
   * Check for intrabar stop hit
   */
  private checkIntrabarStop(
    trade: Trade,
    bar: OHLCV
  ): { hit: boolean; price: number } | null {
    if (trade.direction === 'long') {
      if (bar.low <= trade.stopLoss) {
        return { hit: true, price: Math.min(trade.stopLoss, bar.open) };
      }
    } else {
      if (bar.high >= trade.stopLoss) {
        return { hit: true, price: Math.max(trade.stopLoss, bar.open) };
      }
    }

    return null;
  }

  /**
   * Update trade excursions (MAE/MFE)
   */
  private updateTradeExcursions(trade: Trade, bar: OHLCV, position: Position): void {
    const entry = trade.entryPrice;

    if (trade.direction === 'long') {
      const mae = entry - bar.low;
      const mfe = bar.high - entry;

      trade.maxAdverseExcursion = Math.max(trade.maxAdverseExcursion || 0, mae);
      trade.maxFavorableExcursion = Math.max(trade.maxFavorableExcursion || 0, mfe);
    } else {
      const mae = bar.high - entry;
      const mfe = entry - bar.low;

      trade.maxAdverseExcursion = Math.max(trade.maxAdverseExcursion || 0, mae);
      trade.maxFavorableExcursion = Math.max(trade.maxFavorableExcursion || 0, mfe);
    }

    // Update stop loss from position
    trade.stopLoss = position.stopLoss.currentStop;
    if (trade.initialStop === 0) {
      trade.initialStop = position.stopLoss.initialStop;
    }
  }

  /**
   * Get current bar for instrument at timestamp
   */
  private getCurrentBar(instrument: string, timestamp: Date): OHLCV | null {
    const bars = this.historicalData.get(instrument);
    if (!bars) return null;

    // Find exact or closest bar
    for (let i = bars.length - 1; i >= 0; i--) {
      if (bars[i].timestamp.getTime() <= timestamp.getTime()) {
        return bars[i];
      }
    }

    return null;
  }

  /**
   * Calculate holding period in bars
   */
  private calculateHoldingPeriod(trade: Trade): number {
    if (!trade.exitTime) return 0;

    const bars = this.historicalData.get(trade.instrument);
    if (!bars) return 0;

    const entryTime = trade.entryTime.getTime();
    const exitTime = trade.exitTime.getTime();

    return bars.filter(
      bar => bar.timestamp.getTime() >= entryTime && bar.timestamp.getTime() <= exitTime
    ).length;
  }

  /**
   * Record equity curve point
   */
  private recordEquityPoint(timestamp: Date): void {
    const state = this.framework.getState();

    // Calculate current equity (cash + open positions value)
    let equity = this.currentCapital;

    for (const position of state.positions) {
      equity += position.positionValue;
    }

    // Calculate drawdown
    const peak = this.equityCurve.length > 0
      ? Math.max(...this.equityCurve.map(p => p.equity))
      : this.config.initialCapital;

    const drawdown = peak - equity;
    const drawdownPercent = (drawdown / peak) * 100;

    // Calculate daily return
    const dailyReturn = this.equityCurve.length > 0
      ? ((equity - this.equityCurve[this.equityCurve.length - 1].equity) /
         this.equityCurve[this.equityCurve.length - 1].equity) * 100
      : 0;

    this.equityCurve.push({
      timestamp,
      equity,
      drawdown,
      drawdownPercent,
      openPositions: state.positions.length,
      dailyReturn,
    });
  }

  /**
   * Subscribe to framework events
   */
  private subscribeToEvents(): void {
    Object.values(EventType).forEach(eventType => {
      this.framework.on(eventType as EventType, (event: FrameworkEvent) => {
        this.events.push(event);

        // Handle position closed events
        if (event.type === EventType.POSITION_CLOSED && event.instrument) {
          const trade = this.openTrades.get(event.instrument);
          if (trade && event.data?.price) {
            this.closePosition(
              trade,
              event.data.price,
              event.timestamp,
              event.data.reason || 'Framework Signal'
            );
          }
        }
      });
    });
  }

  /**
   * Generate complete backtest results
   */
  private generateResults(): BacktestResults {
    const metrics = this.calculatePerformanceMetrics();
    const regimePerformance = this.calculateRegimePerformance();
    const monthlyReturns = this.calculateMonthlyReturns();

    const durationDays = Math.ceil(
      (this.config.endDate.getTime() - this.config.startDate.getTime()) /
      (1000 * 60 * 60 * 24)
    );

    return {
      config: this.config,
      frameworkConfig: this.framework.getConfig(),
      metrics,
      regimePerformance,
      trades: this.trades,
      openTrades: Array.from(this.openTrades.values()),
      equityCurve: this.equityCurve,
      monthlyReturns,
      events: this.events,
      startDate: this.config.startDate,
      endDate: this.config.endDate,
      durationDays,
      initialCapital: this.config.initialCapital,
      finalCapital: this.currentCapital,
    };
  }

  /**
   * Calculate comprehensive performance metrics
   */
  private calculatePerformanceMetrics(): PerformanceMetrics {
    if (this.trades.length === 0) {
      return this.getEmptyMetrics();
    }

    // Basic trade stats
    const winners = this.trades.filter(t => (t.pnl ?? 0) > 0);
    const losers = this.trades.filter(t => (t.pnl ?? 0) < 0);

    const totalReturn = this.trades.reduce((sum, t) => sum + (t.pnl ?? 0), 0);
    const totalReturnPercent = (totalReturn / this.config.initialCapital) * 100;

    const avgWin = winners.length > 0
      ? winners.reduce((sum, t) => sum + (t.pnl ?? 0), 0) / winners.length
      : 0;

    const avgLoss = losers.length > 0
      ? Math.abs(losers.reduce((sum, t) => sum + (t.pnl ?? 0), 0) / losers.length)
      : 0;

    const avgWinPercent = winners.length > 0
      ? winners.reduce((sum, t) => sum + (t.pnlPercent ?? 0), 0) / winners.length
      : 0;

    const avgLossPercent = losers.length > 0
      ? Math.abs(losers.reduce((sum, t) => sum + (t.pnlPercent ?? 0), 0) / losers.length)
      : 0;

    const winRate = winners.length / this.trades.length;
    const winLossRatio = avgLoss === 0 ? avgWin : avgWin / avgLoss;
    const expectancy = winRate * avgWin - (1 - winRate) * avgLoss;
    const expectancyPercent = winRate * avgWinPercent - (1 - winRate) * avgLossPercent;

    // Time-based metrics
    const durationYears = (this.config.endDate.getTime() - this.config.startDate.getTime()) /
      (1000 * 60 * 60 * 24 * 365.25);

    const cagr = durationYears > 0
      ? (Math.pow(this.currentCapital / this.config.initialCapital, 1 / durationYears) - 1) * 100
      : 0;

    // Risk metrics
    const returns = this.equityCurve.map(p => p.dailyReturn);
    const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
    const stdDev = Math.sqrt(
      returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 0), 0) / returns.length
    );

    const downSideReturns = returns.filter(r => r < 0);
    const downSideDeviation = downSideReturns.length > 0
      ? Math.sqrt(
          downSideReturns.reduce((sum, r) => sum + Math.pow(r, 2), 0) / downSideReturns.length
        )
      : 0;

    const sharpeRatio = stdDev === 0 ? 0 : (avgReturn / stdDev) * Math.sqrt(252);
    const sortinoRatio = downSideDeviation === 0
      ? 0
      : (avgReturn / downSideDeviation) * Math.sqrt(252);

    // Drawdown metrics
    const { maxDrawdown, maxDrawdownPercent, maxDrawdownDuration } = this.calculateDrawdownMetrics();
    const calmarRatio = maxDrawdownPercent === 0 ? 0 : cagr / maxDrawdownPercent;
    const recoveryFactor = maxDrawdown === 0 ? 0 : totalReturn / maxDrawdown;

    // Position metrics
    const avgHoldingPeriod = this.trades.reduce(
      (sum, t) => sum + (t.holdingPeriodBars ?? 0),
      0
    ) / this.trades.length;

    const avgPositionSize = this.trades.reduce(
      (sum, t) => sum + t.positionSize,
      0
    ) / this.trades.length;

    const maxPositionSize = Math.max(...this.trades.map(t => t.positionSize));

    const avgRiskPerTrade = this.trades.reduce(
      (sum, t) => sum + t.riskAmount,
      0
    ) / this.trades.length;

    // Cost metrics
    const totalSlippage = this.trades.reduce((sum, t) => sum + t.slippage, 0);
    const totalCommission = this.trades.reduce((sum, t) => sum + t.commission, 0);
    const totalFees = this.trades.reduce((sum, t) => sum + t.fees, 0);
    const totalCosts = totalSlippage + totalCommission + totalFees;
    const costsAsPercentOfPnL = totalReturn === 0 ? 0 : (totalCosts / Math.abs(totalReturn)) * 100;

    // Additional metrics
    const avgMAE = this.trades.reduce((sum, t) => sum + (t.maxAdverseExcursion ?? 0), 0) / this.trades.length;
    const avgMFE = this.trades.reduce((sum, t) => sum + (t.maxFavorableExcursion ?? 0), 0) / this.trades.length;

    const totalWins = winners.reduce((sum, t) => sum + (t.pnl ?? 0), 0);
    const totalLosses = Math.abs(losers.reduce((sum, t) => sum + (t.pnl ?? 0), 0));
    const profitFactor = totalLosses === 0 ? totalWins : totalWins / totalLosses;

    // Consecutive wins/losses
    let maxConsecutiveWins = 0;
    let maxConsecutiveLosses = 0;
    let currentWinStreak = 0;
    let currentLossStreak = 0;

    this.trades.forEach(trade => {
      if ((trade.pnl ?? 0) > 0) {
        currentWinStreak++;
        currentLossStreak = 0;
        maxConsecutiveWins = Math.max(maxConsecutiveWins, currentWinStreak);
      } else {
        currentLossStreak++;
        currentWinStreak = 0;
        maxConsecutiveLosses = Math.max(maxConsecutiveLosses, currentLossStreak);
      }
    });

    // Statistical metrics
    const skewness = this.calculateSkewness(returns, avgReturn, stdDev);
    const kurtosis = this.calculateKurtosis(returns, avgReturn, stdDev);

    // Ulcer index
    const ulcerIndex = this.calculateUlcerIndex();

    // Trading frequency
    const tradingDays = this.equityCurve.length;
    const avgTradesPerDay = this.trades.length / tradingDays;
    const avgTradesPerMonth = (this.trades.length / tradingDays) * 21;

    // Average drawdown
    const avgDrawdown = this.equityCurve.reduce(
      (sum, p) => sum + p.drawdown,
      0
    ) / this.equityCurve.length;

    // Confidence intervals (simple approximation)
    const standardError = stdDev / Math.sqrt(this.trades.length);
    const zScore = 1.96; // 95% confidence
    const expectedReturnLower = avgReturn - zScore * standardError;
    const expectedReturnUpper = avgReturn + zScore * standardError;

    return {
      totalReturn,
      totalReturnPercent,
      cagr,
      sharpeRatio,
      sortinoRatio,
      calmarRatio,
      totalTrades: this.trades.length,
      winningTrades: winners.length,
      losingTrades: losers.length,
      winRate,
      avgWin,
      avgLoss,
      avgWinPercent,
      avgLossPercent,
      winLossRatio,
      expectancy,
      expectancyPercent,
      maxDrawdown,
      maxDrawdownPercent,
      maxDrawdownDuration,
      avgDrawdown,
      recoveryFactor,
      avgMAE,
      avgMFE,
      avgHoldingPeriod,
      avgPositionSize,
      maxPositionSize,
      avgRiskPerTrade,
      totalSlippage,
      totalCommission,
      totalFees,
      totalCosts,
      costsAsPercentOfPnL,
      tradingDays,
      avgTradesPerDay,
      avgTradesPerMonth,
      profitFactor,
      ulcerIndex,
      maxConsecutiveWins,
      maxConsecutiveLosses,
      standardDeviation: stdDev,
      downSideDeviation,
      skewness,
      kurtosis,
      expectedReturnLower,
      expectedReturnUpper,
    };
  }

  /**
   * Calculate regime-specific performance
   */
  private calculateRegimePerformance(): Map<RegimeType, RegimePerformance> {
    const regimePerf = new Map<RegimeType, RegimePerformance>();

    Object.values(RegimeType).forEach(regime => {
      const regimeTrades = this.trades.filter(t => t.regime === regime);

      if (regimeTrades.length === 0) return;

      const totalPnL = regimeTrades.reduce((sum, t) => sum + (t.pnl ?? 0), 0);
      const winners = regimeTrades.filter(t => (t.pnl ?? 0) > 0);
      const winRate = winners.length / regimeTrades.length;

      // Create temporary backtester instance for regime-specific metrics
      // (simplified - just calculate basic metrics)
      const metrics = this.calculateMetricsForTrades(regimeTrades);

      regimePerf.set(regime, {
        regime,
        metrics,
        trades: regimeTrades.length,
        totalPnL,
        winRate,
      });
    });

    return regimePerf;
  }

  /**
   * Calculate metrics for specific trades subset
   */
  private calculateMetricsForTrades(trades: Trade[]): PerformanceMetrics {
    // Simplified version - reuse main calculation logic
    const savedTrades = this.trades;
    this.trades = trades;
    const metrics = this.calculatePerformanceMetrics();
    this.trades = savedTrades;
    return metrics;
  }

  /**
   * Calculate drawdown metrics
   */
  private calculateDrawdownMetrics(): {
    maxDrawdown: number;
    maxDrawdownPercent: number;
    maxDrawdownDuration: number;
    avgDrawdown: number;
  } {
    let maxDrawdown = 0;
    let maxDrawdownPercent = 0;
    let maxDrawdownDuration = 0;
    let currentDrawdownDuration = 0;
    let peak = this.config.initialCapital;

    this.equityCurve.forEach(point => {
      if (point.equity > peak) {
        peak = point.equity;
        currentDrawdownDuration = 0;
      } else {
        currentDrawdownDuration++;
      }

      const drawdown = peak - point.equity;
      const drawdownPercent = (drawdown / peak) * 100;

      maxDrawdown = Math.max(maxDrawdown, drawdown);
      maxDrawdownPercent = Math.max(maxDrawdownPercent, drawdownPercent);
      maxDrawdownDuration = Math.max(maxDrawdownDuration, currentDrawdownDuration);
    });

    const avgDrawdown = this.equityCurve.reduce(
      (sum, p) => sum + p.drawdown,
      0
    ) / this.equityCurve.length;

    return { maxDrawdown, maxDrawdownPercent, maxDrawdownDuration, avgDrawdown };
  }

  /**
   * Calculate monthly returns
   */
  private calculateMonthlyReturns(): Map<string, number> {
    const monthlyReturns = new Map<string, number>();

    let monthStart = this.equityCurve[0];
    let currentMonth = '';

    this.equityCurve.forEach(point => {
      const monthKey = `${point.timestamp.getFullYear()}-${String(point.timestamp.getMonth() + 1).padStart(2, '0')}`;

      if (monthKey !== currentMonth) {
        if (currentMonth) {
          // Calculate return for previous month
          const prevPoint = this.equityCurve[this.equityCurve.indexOf(point) - 1];
          const monthReturn = ((prevPoint.equity - monthStart.equity) / monthStart.equity) * 100;
          monthlyReturns.set(currentMonth, monthReturn);
        }
        currentMonth = monthKey;
        monthStart = point;
      }
    });

    // Add final month
    if (this.equityCurve.length > 0) {
      const lastPoint = this.equityCurve[this.equityCurve.length - 1];
      const monthReturn = ((lastPoint.equity - monthStart.equity) / monthStart.equity) * 100;
      monthlyReturns.set(currentMonth, monthReturn);
    }

    return monthlyReturns;
  }

  /**
   * Calculate Ulcer Index (drawdown volatility)
   */
  private calculateUlcerIndex(): number {
    const drawdownSquared = this.equityCurve.reduce(
      (sum, p) => sum + Math.pow(p.drawdownPercent, 2),
      0
    );

    return Math.sqrt(drawdownSquared / this.equityCurve.length);
  }

  /**
   * Calculate skewness
   */
  private calculateSkewness(values: number[], mean: number, stdDev: number): number {
    if (stdDev === 0) return 0;

    const n = values.length;
    const sum = values.reduce((acc, val) => acc + Math.pow((val - mean) / stdDev, 3), 0);

    return (n / ((n - 1) * (n - 2))) * sum;
  }

  /**
   * Calculate kurtosis
   */
  private calculateKurtosis(values: number[], mean: number, stdDev: number): number {
    if (stdDev === 0) return 0;

    const n = values.length;
    const sum = values.reduce((acc, val) => acc + Math.pow((val - mean) / stdDev, 4), 0);

    return ((n * (n + 1)) / ((n - 1) * (n - 2) * (n - 3))) * sum -
           (3 * Math.pow(n - 1, 2)) / ((n - 2) * (n - 3));
  }

  /**
   * Get empty metrics template
   */
  private getEmptyMetrics(): PerformanceMetrics {
    return {
      totalReturn: 0,
      totalReturnPercent: 0,
      cagr: 0,
      sharpeRatio: 0,
      sortinoRatio: 0,
      calmarRatio: 0,
      totalTrades: 0,
      winningTrades: 0,
      losingTrades: 0,
      winRate: 0,
      avgWin: 0,
      avgLoss: 0,
      avgWinPercent: 0,
      avgLossPercent: 0,
      winLossRatio: 0,
      expectancy: 0,
      expectancyPercent: 0,
      maxDrawdown: 0,
      maxDrawdownPercent: 0,
      maxDrawdownDuration: 0,
      avgDrawdown: 0,
      recoveryFactor: 0,
      avgMAE: 0,
      avgMFE: 0,
      avgHoldingPeriod: 0,
      avgPositionSize: 0,
      maxPositionSize: 0,
      avgRiskPerTrade: 0,
      totalSlippage: 0,
      totalCommission: 0,
      totalFees: 0,
      totalCosts: 0,
      costsAsPercentOfPnL: 0,
      tradingDays: 0,
      avgTradesPerDay: 0,
      avgTradesPerMonth: 0,
      profitFactor: 0,
      ulcerIndex: 0,
      maxConsecutiveWins: 0,
      maxConsecutiveLosses: 0,
      standardDeviation: 0,
      downSideDeviation: 0,
      skewness: 0,
      kurtosis: 0,
      expectedReturnLower: 0,
      expectedReturnUpper: 0,
    };
  }

  /**
   * Export results to JSON
   */
  public exportResults(results: BacktestResults): string {
    return JSON.stringify({
      ...results,
      regimePerformance: Array.from(results.regimePerformance.entries()),
      monthlyReturns: Array.from(results.monthlyReturns.entries()),
    }, null, 2);
  }

  /**
   * Generate human-readable report
   */
  public generateReport(results: BacktestResults): string {
    const { metrics } = results;

    let report = '\n';
    report += '═══════════════════════════════════════════════════════════════\n';
    report += '                    BACKTEST RESULTS REPORT                     \n';
    report += '═══════════════════════════════════════════════════════════════\n\n';

    report += `Period: ${results.startDate.toISOString().split('T')[0]} to ${results.endDate.toISOString().split('T')[0]}\n`;
    report += `Duration: ${results.durationDays} days\n`;
    report += `Initial Capital: $${results.initialCapital.toLocaleString()}\n`;
    report += `Final Capital: $${results.finalCapital.toLocaleString()}\n\n`;

    report += '─────────────────────────────────────────────────────────────\n';
    report += '  PERFORMANCE METRICS\n';
    report += '─────────────────────────────────────────────────────────────\n';
    report += `Total Return: $${metrics.totalReturn.toFixed(2)} (${metrics.totalReturnPercent.toFixed(2)}%)\n`;
    report += `CAGR: ${metrics.cagr.toFixed(2)}%\n`;
    report += `Sharpe Ratio: ${metrics.sharpeRatio.toFixed(2)}\n`;
    report += `Sortino Ratio: ${metrics.sortinoRatio.toFixed(2)}\n`;
    report += `Calmar Ratio: ${metrics.calmarRatio.toFixed(2)}\n\n`;

    report += '─────────────────────────────────────────────────────────────\n';
    report += '  TRADE STATISTICS\n';
    report += '─────────────────────────────────────────────────────────────\n';
    report += `Total Trades: ${metrics.totalTrades}\n`;
    report += `Winning Trades: ${metrics.winningTrades} (${(metrics.winRate * 100).toFixed(2)}%)\n`;
    report += `Losing Trades: ${metrics.losingTrades}\n`;
    report += `Average Win: $${metrics.avgWin.toFixed(2)} (${metrics.avgWinPercent.toFixed(2)}%)\n`;
    report += `Average Loss: $${metrics.avgLoss.toFixed(2)} (${metrics.avgLossPercent.toFixed(2)}%)\n`;
    report += `Win/Loss Ratio: ${metrics.winLossRatio.toFixed(2)}\n`;
    report += `Expectancy: $${metrics.expectancy.toFixed(2)} (${metrics.expectancyPercent.toFixed(2)}%)\n`;
    report += `Profit Factor: ${metrics.profitFactor.toFixed(2)}\n\n`;

    report += '─────────────────────────────────────────────────────────────\n';
    report += '  RISK METRICS\n';
    report += '─────────────────────────────────────────────────────────────\n';
    report += `Max Drawdown: $${metrics.maxDrawdown.toFixed(2)} (${metrics.maxDrawdownPercent.toFixed(2)}%)\n`;
    report += `Max DD Duration: ${metrics.maxDrawdownDuration} bars\n`;
    report += `Average Drawdown: $${metrics.avgDrawdown.toFixed(2)}\n`;
    report += `Recovery Factor: ${metrics.recoveryFactor.toFixed(2)}\n`;
    report += `Ulcer Index: ${metrics.ulcerIndex.toFixed(2)}\n`;
    report += `Avg MAE: $${metrics.avgMAE.toFixed(2)}\n`;
    report += `Avg MFE: $${metrics.avgMFE.toFixed(2)}\n\n`;

    report += '─────────────────────────────────────────────────────────────\n';
    report += '  POSITION METRICS\n';
    report += '─────────────────────────────────────────────────────────────\n';
    report += `Avg Holding Period: ${metrics.avgHoldingPeriod.toFixed(1)} bars\n`;
    report += `Avg Position Size: $${metrics.avgPositionSize.toFixed(2)}\n`;
    report += `Max Position Size: $${metrics.maxPositionSize.toFixed(2)}\n`;
    report += `Avg Risk Per Trade: $${metrics.avgRiskPerTrade.toFixed(2)}\n\n`;

    report += '─────────────────────────────────────────────────────────────\n';
    report += '  COST ANALYSIS\n';
    report += '─────────────────────────────────────────────────────────────\n';
    report += `Total Slippage: $${metrics.totalSlippage.toFixed(2)}\n`;
    report += `Total Commission: $${metrics.totalCommission.toFixed(2)}\n`;
    report += `Total Fees: $${metrics.totalFees.toFixed(2)}\n`;
    report += `Total Costs: $${metrics.totalCosts.toFixed(2)} (${metrics.costsAsPercentOfPnL.toFixed(2)}% of PnL)\n\n`;

    report += '─────────────────────────────────────────────────────────────\n';
    report += '  REGIME PERFORMANCE\n';
    report += '─────────────────────────────────────────────────────────────\n';

    results.regimePerformance.forEach((perf, regime) => {
      report += `\n${regime.toUpperCase()}:\n`;
      report += `  Trades: ${perf.trades}\n`;
      report += `  Win Rate: ${(perf.winRate * 100).toFixed(2)}%\n`;
      report += `  Total PnL: $${perf.totalPnL.toFixed(2)}\n`;
      report += `  Expectancy: $${perf.metrics.expectancy.toFixed(2)}\n`;
    });

    report += '\n\n';
    report += '─────────────────────────────────────────────────────────────\n';
    report += '  STATISTICAL METRICS\n';
    report += '─────────────────────────────────────────────────────────────\n';
    report += `Standard Deviation: ${metrics.standardDeviation.toFixed(4)}\n`;
    report += `Downside Deviation: ${metrics.downSideDeviation.toFixed(4)}\n`;
    report += `Skewness: ${metrics.skewness.toFixed(4)}\n`;
    report += `Kurtosis: ${metrics.kurtosis.toFixed(4)}\n`;
    report += `Max Consecutive Wins: ${metrics.maxConsecutiveWins}\n`;
    report += `Max Consecutive Losses: ${metrics.maxConsecutiveLosses}\n\n`;

    report += '─────────────────────────────────────────────────────────────\n';
    report += '  CONFIDENCE INTERVALS (95%)\n';
    report += '─────────────────────────────────────────────────────────────\n';
    report += `Expected Return Range: ${metrics.expectedReturnLower.toFixed(4)}% to ${metrics.expectedReturnUpper.toFixed(4)}%\n\n`;

    report += '═══════════════════════════════════════════════════════════════\n\n';

    return report;
  }
}
