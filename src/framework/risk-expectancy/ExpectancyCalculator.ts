/**
 * Risk-Adjusted Expectancy Calculator
 *
 * Calculates and adjusts trading expectancy based on:
 * - Historical win rate and profit/loss ratios
 * - Current volatility conditions
 * - Market regime favorability
 * - Statistical confidence levels
 */

import {
  RiskMetrics,
  RiskAdjustedExpectancy,
  RegimeType,
  OHLCV,
  MarketData,
  Timeframe,
} from '../core/types';

/**
 * Trade result for expectancy calculation
 */
export interface TradeResult {
  entryPrice: number;
  exitPrice: number;
  direction: 'long' | 'short';
  pnl: number;
  riskAmount: number;
  regime?: RegimeType;
  timestamp: Date;
}

/**
 * Configuration for expectancy calculator
 */
export interface ExpectancyConfig {
  minSampleSize: number; // Minimum trades for reliable calculation
  volatilityLookback: number; // Bars to calculate volatility
  regimeAdjustmentFactor: number; // How much to adjust for regime (0-1)
  confidenceLevel: number; // Statistical confidence (0.95 = 95%)
}

/**
 * Main expectancy calculator class
 */
export class ExpectancyCalculator {
  private config: ExpectancyConfig;
  private tradeHistory: TradeResult[] = [];

  constructor(config: Partial<ExpectancyConfig> = {}) {
    this.config = {
      minSampleSize: config.minSampleSize ?? 30,
      volatilityLookback: config.volatilityLookback ?? 100,
      regimeAdjustmentFactor: config.regimeAdjustmentFactor ?? 0.3,
      confidenceLevel: config.confidenceLevel ?? 0.95,
    };
  }

  /**
   * Add trade result to history
   */
  public addTradeResult(trade: TradeResult): void {
    this.tradeHistory.push(trade);
  }

  /**
   * Calculate base risk metrics from trade history
   */
  public calculateRiskMetrics(
    trades?: TradeResult[]
  ): RiskMetrics {
    const tradesToAnalyze = trades ?? this.tradeHistory;

    if (tradesToAnalyze.length === 0) {
      return this.getDefaultMetrics();
    }

    const wins = tradesToAnalyze.filter((t) => t.pnl > 0);
    const losses = tradesToAnalyze.filter((t) => t.pnl < 0);

    const winRate = wins.length / tradesToAnalyze.length;
    const avgWin = wins.length > 0
      ? wins.reduce((sum, t) => sum + t.pnl, 0) / wins.length
      : 0;
    const avgLoss = losses.length > 0
      ? Math.abs(losses.reduce((sum, t) => sum + t.pnl, 0) / losses.length)
      : 0;

    const winLossRatio = avgLoss === 0 ? avgWin : avgWin / avgLoss;
    const expectancy = winRate * avgWin - (1 - winRate) * avgLoss;

    // Calculate Sharpe ratio
    const returns = tradesToAnalyze.map((t) => t.pnl / t.riskAmount);
    const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
    const stdDev = Math.sqrt(
      returns.reduce((sum, r) => sum + (r - avgReturn) ** 2, 0) /
        returns.length
    );
    const sharpeRatio = stdDev === 0 ? 0 : avgReturn / stdDev;

    // Calculate max drawdown
    const cumulativePnL: number[] = [];
    let sum = 0;
    tradesToAnalyze.forEach((t) => {
      sum += t.pnl;
      cumulativePnL.push(sum);
    });

    let maxDrawdown = 0;
    let peak = cumulativePnL[0];
    cumulativePnL.forEach((value) => {
      if (value > peak) peak = value;
      const drawdown = peak - value;
      if (drawdown > maxDrawdown) maxDrawdown = drawdown;
    });

    // Recovery factor
    const totalPnL = tradesToAnalyze.reduce((sum, t) => sum + t.pnl, 0);
    const recoveryFactor =
      maxDrawdown === 0 ? 0 : Math.abs(totalPnL / maxDrawdown);

    return {
      winRate,
      avgWin,
      avgLoss,
      winLossRatio,
      expectancy,
      sharpeRatio,
      maxDrawdown,
      recoveryFactor,
      sampleSize: tradesToAnalyze.length,
    };
  }

  /**
   * Calculate risk-adjusted expectancy for an instrument
   */
  public calculateRiskAdjustedExpectancy(
    instrument: string,
    marketData: MarketData,
    currentRegime: RegimeType,
    timeframe: Timeframe
  ): RiskAdjustedExpectancy {
    const baseMetrics = this.calculateRiskMetrics();
    const baseExpectancy = baseMetrics.expectancy;

    // Calculate volatility adjustment
    const volatilityAdj = this.calculateVolatilityAdjustment(
      marketData,
      timeframe
    );

    // Calculate regime adjustment
    const regimeAdj = this.calculateRegimeAdjustment(
      currentRegime,
      baseMetrics
    );

    // Calculate final expectancy
    const finalExpectancy =
      baseExpectancy * (1 + volatilityAdj) * (1 + regimeAdj);

    // Calculate statistical confidence
    const confidence = this.calculateConfidence(baseMetrics.sampleSize);

    return {
      baseExpectancy,
      volatilityAdjustment: volatilityAdj,
      regimeAdjustment: regimeAdj,
      finalExpectancy,
      confidence,
      instrument,
      timestamp: new Date(),
    };
  }

  /**
   * Calculate volatility adjustment factor
   * Lower volatility = positive adjustment, higher = negative
   */
  private calculateVolatilityAdjustment(
    marketData: MarketData,
    timeframe: Timeframe
  ): number {
    const bars = marketData.bars
      .filter((b) => b.timeframe === timeframe)
      .slice(-this.config.volatilityLookback);

    if (bars.length < 2) return 0;

    // Calculate current volatility (ATR)
    const currentVol = this.calculateATR(bars, 14);

    // Calculate historical average volatility
    const historicalBars = bars.slice(0, Math.floor(bars.length * 0.7));
    const historicalVol = this.calculateATR(historicalBars, 14);

    if (historicalVol === 0) return 0;

    // Volatility ratio: <1 = lower vol (good), >1 = higher vol (bad)
    const volRatio = currentVol / historicalVol;

    // Convert to adjustment factor: lower vol = positive, higher = negative
    // Range: approximately -0.5 to +0.5
    const adjustment = (1 - volRatio) * 0.5;

    return Math.max(-0.5, Math.min(0.5, adjustment));
  }

  /**
   * Calculate regime adjustment factor
   */
  private calculateRegimeAdjustment(
    currentRegime: RegimeType,
    metrics: RiskMetrics
  ): number {
    // Filter trades by regime
    const regimeTrades = this.tradeHistory.filter(
      (t) => t.regime === currentRegime
    );

    if (regimeTrades.length < 10) {
      // Not enough regime-specific data, use default adjustments
      return this.getDefaultRegimeAdjustment(currentRegime);
    }

    // Calculate regime-specific metrics
    const regimeMetrics = this.calculateRiskMetrics(regimeTrades);

    // Compare regime expectancy to overall expectancy
    const baseExpectancy = metrics.expectancy || 0.01; // Avoid division by zero
    const expectancyRatio = regimeMetrics.expectancy / baseExpectancy;

    // Convert to adjustment factor
    const adjustment = (expectancyRatio - 1) * this.config.regimeAdjustmentFactor;

    return Math.max(-0.5, Math.min(0.5, adjustment));
  }

  /**
   * Default regime adjustments (when insufficient data)
   */
  private getDefaultRegimeAdjustment(regime: RegimeType): number {
    switch (regime) {
      case RegimeType.MOMENTUM:
        return 0.1; // Slightly favor momentum trades
      case RegimeType.MEAN_REVERSION:
        return -0.1; // Slightly less favorable
      case RegimeType.TRANSITION:
        return -0.2; // Reduce exposure during transitions
      case RegimeType.NEUTRAL:
        return -0.15; // Slightly reduce in neutral conditions
      default:
        return 0;
    }
  }

  /**
   * Calculate statistical confidence based on sample size
   */
  private calculateConfidence(sampleSize: number): number {
    if (sampleSize < this.config.minSampleSize) {
      return sampleSize / this.config.minSampleSize;
    }

    // Use Student's t-distribution for confidence
    // Simplified: more samples = higher confidence, asymptotic to 1
    const maxConfidence = this.config.confidenceLevel;
    const confidence = maxConfidence * (1 - Math.exp(-sampleSize / 50));

    return Math.min(maxConfidence, confidence);
  }

  /**
   * Calculate ATR (Average True Range)
   */
  private calculateATR(bars: OHLCV[], period: number): number {
    if (bars.length < period + 1) return 0;

    const tr: number[] = [];
    for (let i = 1; i < bars.length; i++) {
      const high = bars[i].high;
      const low = bars[i].low;
      const prevClose = bars[i - 1].close;
      tr.push(
        Math.max(
          high - low,
          Math.abs(high - prevClose),
          Math.abs(low - prevClose)
        )
      );
    }

    const recentTR = tr.slice(-period);
    return recentTR.reduce((sum, val) => sum + val, 0) / recentTR.length;
  }

  /**
   * Get default metrics when no trade history exists
   */
  private getDefaultMetrics(): RiskMetrics {
    return {
      winRate: 0.5,
      avgWin: 1,
      avgLoss: 1,
      winLossRatio: 1,
      expectancy: 0,
      sharpeRatio: 0,
      maxDrawdown: 0,
      recoveryFactor: 0,
      sampleSize: 0,
    };
  }

  /**
   * Get trade history
   */
  public getTradeHistory(): TradeResult[] {
    return [...this.tradeHistory];
  }

  /**
   * Clear trade history
   */
  public clearHistory(): void {
    this.tradeHistory = [];
  }

  /**
   * Calculate expectancy for specific regime
   */
  public calculateRegimeSpecificExpectancy(
    regime: RegimeType
  ): RiskMetrics | null {
    const regimeTrades = this.tradeHistory.filter((t) => t.regime === regime);

    if (regimeTrades.length < 5) {
      return null; // Insufficient data
    }

    return this.calculateRiskMetrics(regimeTrades);
  }

  /**
   * Get performance summary
   */
  public getPerformanceSummary(): {
    overall: RiskMetrics;
    byRegime: Map<RegimeType, RiskMetrics>;
    totalTrades: number;
    totalPnL: number;
  } {
    const overall = this.calculateRiskMetrics();
    const byRegime = new Map<RegimeType, RiskMetrics>();

    Object.values(RegimeType).forEach((regime) => {
      const metrics = this.calculateRegimeSpecificExpectancy(regime);
      if (metrics) {
        byRegime.set(regime, metrics);
      }
    });

    const totalPnL = this.tradeHistory.reduce((sum, t) => sum + t.pnl, 0);

    return {
      overall,
      byRegime,
      totalTrades: this.tradeHistory.length,
      totalPnL,
    };
  }
}
