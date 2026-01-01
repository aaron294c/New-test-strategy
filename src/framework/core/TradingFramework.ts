/**
 * Main Trading Framework Orchestrator
 *
 * Coordinates all modules to provide a unified trading system:
 * - Regime detection
 * - Percentile entry/exit logic
 * - Risk-adjusted expectancy
 * - Composite scoring
 * - Capital allocation
 */

import {
  FrameworkConfig,
  FrameworkState,
  FrameworkEvent,
  EventType,
  EventHandler,
  MarketData,
  Position,
  CompositeScore,
  AllocationDecision,
  MultiTimeframeRegime,
} from './types';

import { mergeConfig, validateConfig, DEFAULT_CONFIG } from './config';
import { RegimeDetector } from '../regime-detection/RegimeDetector';
import { PercentileEngine } from '../percentile-logic/PercentileEngine';
import { ExpectancyCalculator, TradeResult } from '../risk-expectancy/ExpectancyCalculator';
import { InstrumentScorer } from '../composite-scoring/InstrumentScorer';
import { AllocationEngine } from '../capital-allocation/AllocationEngine';

/**
 * Main trading framework class
 */
export class TradingFramework {
  private config: FrameworkConfig;
  private state: FrameworkState;
  private eventHandlers: Map<EventType, EventHandler[]>;

  // Module instances
  private regimeDetector: RegimeDetector;
  private percentileEngine: PercentileEngine;
  private expectancyCalculator: ExpectancyCalculator;
  private instrumentScorer: InstrumentScorer;
  private allocationEngine: AllocationEngine;

  // Update interval timer
  private updateTimer?: NodeJS.Timeout;

  constructor(userConfig: Partial<FrameworkConfig> = {}) {
    // Merge and validate configuration
    this.config = mergeConfig(userConfig);
    const validation = validateConfig(this.config);

    if (!validation.valid) {
      throw new Error(
        `Invalid framework configuration: ${validation.errors.join(', ')}`
      );
    }

    // Initialize modules
    this.regimeDetector = new RegimeDetector({
      lookbackPeriod: this.config.regimeDetection.lookbackPeriod,
      coherenceThreshold: this.config.regimeDetection.coherenceThreshold,
    });

    this.percentileEngine = new PercentileEngine({
      lookbackBars: this.config.percentileSettings.lookbackBars,
      entryPercentile: this.config.percentileSettings.entryPercentile,
      stopPercentile: this.config.percentileSettings.stopPercentile,
      adaptiveThresholds: this.config.percentileSettings.adaptive,
    });

    this.expectancyCalculator = new ExpectancyCalculator({
      minSampleSize: 30,
      volatilityLookback: this.config.percentileSettings.lookbackBars,
    });

    this.instrumentScorer = new InstrumentScorer({
      factors: this.config.scoring.factors,
      minScore: this.config.scoring.minScore,
    });

    this.allocationEngine = new AllocationEngine(this.config.allocation);

    // Initialize state
    this.state = this.initializeState();

    // Initialize event handlers
    this.eventHandlers = new Map();
  }

  /**
   * Initialize framework state
   */
  private initializeState(): FrameworkState {
    return {
      config: this.config,
      currentRegime: {
        regimes: [],
        coherence: 0,
        dominantRegime: 'neutral' as any,
        timestamp: new Date(),
      },
      positions: [],
      scores: new Map(),
      allocations: new Map(),
      marketData: new Map(),
      lastUpdate: new Date(),
      isActive: false,
      metrics: {
        totalPnL: 0,
        totalRiskExposure: 0,
        averageScore: 0,
        regimeCoherence: 0,
      },
    };
  }

  /**
   * Start the framework
   */
  public start(): void {
    if (this.state.isActive) {
      throw new Error('Framework is already active');
    }

    this.state.isActive = true;
    this.emitEvent({
      type: EventType.REGIME_CHANGE,
      timestamp: new Date(),
      data: { message: 'Framework started' },
      severity: 'low',
      message: 'Trading framework initialized and started',
    });

    // Start update loop
    this.updateTimer = setInterval(() => {
      this.update().catch((error) => {
        this.emitEvent({
          type: EventType.ERROR,
          timestamp: new Date(),
          data: error,
          severity: 'high',
          message: `Framework update error: ${error.message}`,
        });
      });
    }, this.config.updateInterval);
  }

  /**
   * Stop the framework
   */
  public stop(): void {
    if (!this.state.isActive) {
      throw new Error('Framework is not active');
    }

    if (this.updateTimer) {
      clearInterval(this.updateTimer);
      this.updateTimer = undefined;
    }

    this.state.isActive = false;
    this.emitEvent({
      type: EventType.REGIME_CHANGE,
      timestamp: new Date(),
      data: { message: 'Framework stopped' },
      severity: 'low',
      message: 'Trading framework stopped',
    });
  }

  /**
   * Main update cycle
   */
  private async update(): Promise<void> {
    try {
      // Update regime detection
      await this.updateRegimes();

      // Update instrument scores
      await this.updateScores();

      // Update capital allocations
      await this.updateAllocations();

      // Update positions
      await this.updatePositions();

      // Update metrics
      this.updateMetrics();

      this.state.lastUpdate = new Date();
    } catch (error) {
      throw error;
    }
  }

  /**
   * Update market regime detection
   */
  private async updateRegimes(): Promise<void> {
    const marketDataArray = Array.from(this.state.marketData.values());

    if (marketDataArray.length === 0) {
      return; // No market data available
    }

    // Use first instrument as reference for regime (in production, use index/aggregate)
    const referenceData = marketDataArray[0];

    const previousRegime = this.state.currentRegime.dominantRegime;
    const newRegime = this.regimeDetector.detectMultiTimeframeRegime(
      referenceData,
      this.config.timeframes
    );

    this.state.currentRegime = newRegime;

    // Emit event if regime changed
    if (previousRegime !== newRegime.dominantRegime) {
      this.emitEvent({
        type: EventType.REGIME_CHANGE,
        timestamp: new Date(),
        data: {
          from: previousRegime,
          to: newRegime.dominantRegime,
          coherence: newRegime.coherence,
        },
        severity: 'medium',
        message: `Regime changed from ${previousRegime} to ${newRegime.dominantRegime}`,
      });
    }
  }

  /**
   * Update instrument composite scores
   */
  private async updateScores(): Promise<void> {
    const newScores = new Map<string, CompositeScore>();

    for (const [instrument, marketData] of this.state.marketData) {
      // Calculate expectancy for this instrument
      const expectancy = this.expectancyCalculator.calculateRiskAdjustedExpectancy(
        instrument,
        marketData,
        this.state.currentRegime.dominantRegime,
        this.config.primaryTimeframe
      );

      // Calculate composite score
      const score = this.instrumentScorer.calculateScore(
        instrument,
        marketData,
        this.state.currentRegime,
        expectancy,
        this.config.timeframes
      );

      newScores.set(instrument, score);

      // Emit event for significant score changes
      const oldScore = this.state.scores.get(instrument);
      if (oldScore && Math.abs(score.totalScore - oldScore.totalScore) > 0.1) {
        this.emitEvent({
          type: EventType.SCORE_UPDATE,
          timestamp: new Date(),
          instrument,
          data: {
            from: oldScore.totalScore,
            to: score.totalScore,
          },
          severity: 'low',
          message: `Score updated for ${instrument}: ${oldScore.totalScore.toFixed(2)} → ${score.totalScore.toFixed(2)}`,
        });
      }
    }

    this.state.scores = newScores;
  }

  /**
   * Update capital allocations
   */
  private async updateAllocations(): Promise<void> {
    const scores = Array.from(this.state.scores.values());
    const rankedScores = this.instrumentScorer.rankInstruments(scores);

    // Calculate available capital
    const positionValue = this.state.positions.reduce(
      (sum, p) => sum + p.positionValue,
      0
    );
    const availableCapital = this.config.allocation.totalCapital - positionValue;

    // Calculate current risk exposure
    const currentRisk = this.state.positions.reduce(
      (sum, p) => sum + p.riskAmount,
      0
    );

    // Generate stop losses for new allocations
    const stopLossMap = new Map();
    for (const score of rankedScores) {
      const marketData = this.state.marketData.get(score.instrument);
      if (marketData) {
        const entry = this.percentileEngine.generateEntrySignal(
          marketData,
          this.config.primaryTimeframe,
          this.state.currentRegime.dominantRegime
        );

        if (entry) {
          const stopLoss = this.percentileEngine.calculateStopLoss(
            marketData,
            entry.currentPrice,
            entry.direction,
            this.config.primaryTimeframe,
            this.config.allocation.totalCapital * this.config.riskManagement.maxRiskPerTrade
          );
          stopLossMap.set(score.instrument, stopLoss);
        }
      }
    }

    // Allocate capital
    const allocationResult = this.allocationEngine.allocateCapital(
      rankedScores,
      {
        currentPositions: this.state.positions,
        availableCapital,
        currentRiskExposure: currentRisk,
      },
      this.state.marketData,
      stopLossMap
    );

    // Update allocations
    const newAllocations = new Map<string, AllocationDecision>();
    allocationResult.decisions.forEach((decision) => {
      newAllocations.set(decision.instrument, decision);
    });

    this.state.allocations = newAllocations;

    // Emit allocation change event
    if (allocationResult.decisions.length > 0) {
      this.emitEvent({
        type: EventType.ALLOCATION_CHANGE,
        timestamp: new Date(),
        data: {
          allocated: allocationResult.totalAllocated,
          risk: allocationResult.totalRisk,
          positions: allocationResult.decisions.length,
        },
        severity: 'low',
        message: `Capital allocated to ${allocationResult.decisions.length} instruments`,
      });
    }
  }

  /**
   * Update existing positions
   */
  private async updatePositions(): Promise<void> {
    const updatedPositions: Position[] = [];

    for (const position of this.state.positions) {
      const marketData = this.state.marketData.get(position.instrument);
      if (!marketData) continue;

      // Update position value and P&L
      const currentPrice = marketData.currentPrice;
      const unrealizedPnL =
        position.direction === 'long'
          ? (currentPrice - position.entryPrice) * position.quantity
          : (position.entryPrice - currentPrice) * position.quantity;

      // Update stop loss
      const updatedStop = this.percentileEngine.updateStopLoss(
        position.stopLoss,
        marketData,
        currentPrice,
        position.direction,
        this.state.currentRegime.dominantRegime
      );

      // Check if stop hit
      const stopHit =
        position.direction === 'long'
          ? currentPrice <= updatedStop.currentStop
          : currentPrice >= updatedStop.currentStop;

      if (stopHit) {
        this.emitEvent({
          type: EventType.EXIT_SIGNAL,
          timestamp: new Date(),
          instrument: position.instrument,
          data: {
            reason: 'Stop loss hit',
            price: currentPrice,
            pnl: unrealizedPnL,
          },
          severity: 'medium',
          message: `Stop loss hit for ${position.instrument}`,
        });

        // Record trade result
        this.expectancyCalculator.addTradeResult({
          entryPrice: position.entryPrice,
          exitPrice: currentPrice,
          direction: position.direction,
          pnl: unrealizedPnL,
          riskAmount: position.riskAmount,
          regime: this.state.currentRegime.dominantRegime,
          timestamp: new Date(),
        });

        continue; // Don't add to updated positions
      }

      // Update position
      updatedPositions.push({
        ...position,
        currentPrice,
        positionValue: currentPrice * position.quantity,
        unrealizedPnL,
        stopLoss: updatedStop,
      });
    }

    this.state.positions = updatedPositions;
  }

  /**
   * Update framework metrics
   */
  private updateMetrics(): void {
    const totalPnL = this.state.positions.reduce(
      (sum, p) => sum + p.unrealizedPnL,
      0
    );
    const totalRiskExposure = this.state.positions.reduce(
      (sum, p) => sum + p.riskAmount,
      0
    );
    const averageScore =
      this.state.positions.length > 0
        ? this.state.positions.reduce(
            (sum, p) => sum + p.compositeScore.totalScore,
            0
          ) / this.state.positions.length
        : 0;

    this.state.metrics = {
      totalPnL,
      totalRiskExposure,
      averageScore,
      regimeCoherence: this.state.currentRegime.coherence,
    };
  }

  /**
   * Add market data for an instrument
   */
  public addMarketData(instrument: string, data: MarketData): void {
    this.state.marketData.set(instrument, data);
  }

  /**
   * Get current framework state
   */
  public getState(): FrameworkState {
    return { ...this.state };
  }

  /**
   * Subscribe to framework events
   */
  public on(eventType: EventType, handler: EventHandler): void {
    const handlers = this.eventHandlers.get(eventType) ?? [];
    handlers.push(handler);
    this.eventHandlers.set(eventType, handlers);
  }

  /**
   * Unsubscribe from framework events
   */
  public off(eventType: EventType, handler: EventHandler): void {
    const handlers = this.eventHandlers.get(eventType) ?? [];
    const filtered = handlers.filter((h) => h !== handler);
    this.eventHandlers.set(eventType, filtered);
  }

  /**
   * Emit framework event
   */
  private emitEvent(event: FrameworkEvent): void {
    const handlers = this.eventHandlers.get(event.type) ?? [];
    handlers.forEach((handler) => {
      try {
        handler(event);
      } catch (error) {
        console.error(`Error in event handler for ${event.type}:`, error);
      }
    });
  }

  /**
   * Get framework configuration
   */
  public getConfig(): FrameworkConfig {
    return { ...this.config };
  }

  /**
   * Update framework configuration (requires restart)
   */
  public updateConfig(newConfig: Partial<FrameworkConfig>): void {
    if (this.state.isActive) {
      throw new Error('Cannot update config while framework is active. Stop first.');
    }

    this.config = mergeConfig(newConfig);
    const validation = validateConfig(this.config);

    if (!validation.valid) {
      throw new Error(
        `Invalid configuration: ${validation.errors.join(', ')}`
      );
    }

    // Reinitialize modules with new config
    // (Implementation details omitted for brevity)
  }
}
