/**
 * Percentile-based Entry & Stop-Loss Engine
 *
 * Implements principle-led percentile logic for:
 * - Entry signals based on price extremes
 * - Adaptive stop-loss placement
 * - Dynamic threshold adjustment
 */

import {
  PercentileData,
  PercentileEntry,
  AdaptiveStopLoss,
  OHLCV,
  MarketData,
  Timeframe,
  RegimeType,
} from '../core/types';

/**
 * Configuration for percentile engine
 */
export interface PercentileEngineConfig {
  lookbackBars: number;
  entryPercentile: number; // 0-100
  stopPercentile: number; // 0-100
  adaptiveThresholds: boolean;
  atrMultiplier?: number; // Optional ATR-based stop component
}

/**
 * Main percentile calculation engine
 */
export class PercentileEngine {
  private config: PercentileEngineConfig;

  constructor(config: Partial<PercentileEngineConfig> = {}) {
    this.config = {
      lookbackBars: config.lookbackBars ?? 100,
      entryPercentile: config.entryPercentile ?? 90,
      stopPercentile: config.stopPercentile ?? 95,
      adaptiveThresholds: config.adaptiveThresholds ?? true,
      atrMultiplier: config.atrMultiplier,
    };
  }

  /**
   * Calculate percentile value from historical data
   */
  public calculatePercentile(
    values: number[],
    percentile: number
  ): PercentileData {
    if (values.length === 0) {
      throw new Error('Cannot calculate percentile of empty array');
    }

    if (percentile < 0 || percentile > 100) {
      throw new Error(`Percentile must be 0-100, got ${percentile}`);
    }

    const sorted = [...values].sort((a, b) => a - b);
    const index = (percentile / 100) * (sorted.length - 1);
    const lower = Math.floor(index);
    const upper = Math.ceil(index);
    const weight = index - lower;

    const value =
      lower === upper
        ? sorted[lower]
        : sorted[lower] * (1 - weight) + sorted[upper] * weight;

    return {
      value,
      percentile,
      lookbackPeriod: values.length,
      timeframe: Timeframe.H4, // Default, should be passed in
    };
  }

  /**
   * Calculate current price percentile rank
   */
  public calculatePricePercentile(
    marketData: MarketData,
    timeframe: Timeframe
  ): PercentileData {
    const bars = this.filterByTimeframe(marketData.bars, timeframe).slice(
      -this.config.lookbackBars
    );

    if (bars.length < 2) {
      throw new Error('Insufficient bars for percentile calculation');
    }

    const closes = bars.map((b) => b.close);
    const currentPrice = marketData.currentPrice;

    // Calculate percentile rank
    const belowCount = closes.filter((c) => c < currentPrice).length;
    const percentile = (belowCount / closes.length) * 100;

    return {
      value: currentPrice,
      percentile,
      lookbackPeriod: bars.length,
      timeframe,
    };
  }

  /**
   * Generate entry signal based on percentile extremes
   */
  public generateEntrySignal(
    marketData: MarketData,
    timeframe: Timeframe,
    regime?: RegimeType
  ): PercentileEntry | null {
    const pricePercentile = this.calculatePricePercentile(marketData, timeframe);

    // Adapt threshold based on regime
    let entryThreshold = this.config.entryPercentile;
    if (this.config.adaptiveThresholds && regime) {
      entryThreshold = this.adaptEntryThreshold(regime, entryThreshold);
    }

    // Check for entry at upper extreme (potential short/reversal)
    if (pricePercentile.percentile >= entryThreshold) {
      return {
        instrument: marketData.instrument,
        currentPrice: marketData.currentPrice,
        percentileLevel: pricePercentile,
        entryThreshold,
        direction: 'short',
        timestamp: new Date(),
      };
    }

    // Check for entry at lower extreme (potential long/reversal)
    const lowerThreshold = 100 - entryThreshold;
    if (pricePercentile.percentile <= lowerThreshold) {
      return {
        instrument: marketData.instrument,
        currentPrice: marketData.currentPrice,
        percentileLevel: pricePercentile,
        entryThreshold: lowerThreshold,
        direction: 'long',
        timestamp: new Date(),
      };
    }

    return null; // No entry signal
  }

  /**
   * Calculate adaptive stop-loss based on percentiles
   */
  public calculateStopLoss(
    marketData: MarketData,
    entryPrice: number,
    direction: 'long' | 'short',
    timeframe: Timeframe,
    riskAmount: number
  ): AdaptiveStopLoss {
    const bars = this.filterByTimeframe(marketData.bars, timeframe).slice(
      -this.config.lookbackBars
    );

    // Calculate historical move percentiles
    const moves = this.calculateHistoricalMoves(bars);
    const stopPercentile = this.calculatePercentile(
      moves,
      this.config.stopPercentile
    );

    // Calculate stop distance
    let stopDistance = stopPercentile.value;

    // Optional: Incorporate ATR
    if (this.config.atrMultiplier) {
      const atr = this.calculateATR(bars, 14);
      const atrStop = atr * this.config.atrMultiplier;
      stopDistance = Math.max(stopDistance, atrStop); // Use wider stop
    }

    // Calculate stop price
    const stopPrice =
      direction === 'long'
        ? entryPrice - stopDistance
        : entryPrice + stopDistance;

    return {
      initialStop: stopPrice,
      currentStop: stopPrice,
      percentileBased: {
        ...stopPercentile,
        timeframe,
      },
      atrMultiplier: this.config.atrMultiplier,
      riskAmount,
      timestamp: new Date(),
    };
  }

  /**
   * Update stop-loss (for trailing stops or regime changes)
   */
  public updateStopLoss(
    currentStop: AdaptiveStopLoss,
    marketData: MarketData,
    currentPrice: number,
    direction: 'long' | 'short',
    regime?: RegimeType
  ): AdaptiveStopLoss {
    let newStop = currentStop.currentStop;
    let updateReason: string | undefined;

    // Trailing stop logic for trending regimes
    if (regime === RegimeType.MOMENTUM) {
      const trailingDistance =
        currentStop.percentileBased.value * 0.5; // Trail at 50% of initial stop

      if (direction === 'long') {
        const potentialStop = currentPrice - trailingDistance;
        if (potentialStop > currentStop.currentStop) {
          newStop = potentialStop;
          updateReason = 'Trailing stop in momentum regime';
        }
      } else {
        const potentialStop = currentPrice + trailingDistance;
        if (potentialStop < currentStop.currentStop) {
          newStop = potentialStop;
          updateReason = 'Trailing stop in momentum regime';
        }
      }
    }

    // Tighter stops in mean-reversion regimes
    if (regime === RegimeType.MEAN_REVERSION) {
      const tighterDistance = currentStop.percentileBased.value * 0.75;

      if (direction === 'long') {
        const potentialStop = currentStop.initialStop + tighterDistance * 0.25;
        if (potentialStop > currentStop.currentStop) {
          newStop = potentialStop;
          updateReason = 'Tightening stop in mean-reversion regime';
        }
      } else {
        const potentialStop = currentStop.initialStop - tighterDistance * 0.25;
        if (potentialStop < currentStop.currentStop) {
          newStop = potentialStop;
          updateReason = 'Tightening stop in mean-reversion regime';
        }
      }
    }

    return {
      ...currentStop,
      currentStop: newStop,
      updateReason,
      timestamp: new Date(),
    };
  }

  /**
   * Calculate historical price moves (bar-to-bar)
   */
  private calculateHistoricalMoves(bars: OHLCV[]): number[] {
    const moves: number[] = [];

    for (let i = 1; i < bars.length; i++) {
      const move = Math.abs(bars[i].close - bars[i - 1].close);
      moves.push(move);
    }

    return moves;
  }

  /**
   * Calculate Average True Range
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

    // Simple average for last 'period' bars
    const recentTR = tr.slice(-period);
    return recentTR.reduce((sum, val) => sum + val, 0) / recentTR.length;
  }

  /**
   * Adapt entry threshold based on regime
   */
  private adaptEntryThreshold(
    regime: RegimeType,
    baseThreshold: number
  ): number {
    switch (regime) {
      case RegimeType.MOMENTUM:
        // In momentum, wait for more extreme reversals
        return Math.min(95, baseThreshold + 5);

      case RegimeType.MEAN_REVERSION:
        // In mean-reversion, can enter earlier
        return Math.max(80, baseThreshold - 5);

      case RegimeType.TRANSITION:
        // In transition, be more conservative
        return Math.min(95, baseThreshold + 3);

      default:
        return baseThreshold;
    }
  }

  /**
   * Filter bars by timeframe
   */
  private filterByTimeframe(bars: OHLCV[], timeframe: Timeframe): OHLCV[] {
    return bars.filter((b) => b.timeframe === timeframe);
  }

  /**
   * Get percentile statistics for debugging/analysis
   */
  public getPercentileStats(
    marketData: MarketData,
    timeframe: Timeframe
  ): {
    current: number;
    p10: number;
    p25: number;
    p50: number;
    p75: number;
    p90: number;
    p95: number;
    p99: number;
  } {
    const bars = this.filterByTimeframe(marketData.bars, timeframe).slice(
      -this.config.lookbackBars
    );
    const closes = bars.map((b) => b.close);

    return {
      current: marketData.currentPrice,
      p10: this.calculatePercentile(closes, 10).value,
      p25: this.calculatePercentile(closes, 25).value,
      p50: this.calculatePercentile(closes, 50).value,
      p75: this.calculatePercentile(closes, 75).value,
      p90: this.calculatePercentile(closes, 90).value,
      p95: this.calculatePercentile(closes, 95).value,
      p99: this.calculatePercentile(closes, 99).value,
    };
  }
}
