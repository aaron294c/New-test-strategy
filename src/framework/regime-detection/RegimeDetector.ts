/**
 * Regime Detection Module
 *
 * Classifies market conditions as momentum vs mean-reversion across multiple timeframes
 * Uses principle-led approach: derives thresholds from market data, not hardcoded values
 */

import {
  RegimeType,
  RegimeSignal,
  MultiTimeframeRegime,
  Timeframe,
  OHLCV,
  MarketData,
  TimeframeWeight,
} from '../core/types';

/**
 * Regime detection configuration
 */
export interface RegimeDetectorConfig {
  lookbackPeriod: number;
  coherenceThreshold: number;
  trendStrengthMethod: 'adx' | 'linear_regression' | 'percentile_rank';
  volatilityMethod: 'atr' | 'std_dev' | 'percentile';
  adaptiveThresholds: boolean;
}

/**
 * Main regime detector class
 */
export class RegimeDetector {
  private config: RegimeDetectorConfig;

  constructor(config: Partial<RegimeDetectorConfig> = {}) {
    this.config = {
      lookbackPeriod: config.lookbackPeriod ?? 100,
      coherenceThreshold: config.coherenceThreshold ?? 0.6,
      trendStrengthMethod: config.trendStrengthMethod ?? 'adx',
      volatilityMethod: config.volatilityMethod ?? 'atr',
      adaptiveThresholds: config.adaptiveThresholds ?? true,
    };
  }

  /**
   * Detect regime for a single timeframe
   */
  public detectRegime(
    marketData: MarketData,
    timeframe: Timeframe
  ): RegimeSignal {
    const bars = this.filterByTimeframe(marketData.bars, timeframe);

    if (bars.length < this.config.lookbackPeriod) {
      throw new Error(
        `Insufficient data: need ${this.config.lookbackPeriod}, got ${bars.length}`
      );
    }

    // Calculate regime indicators
    const trendStrength = this.calculateTrendStrength(bars);
    const volatilityRatio = this.calculateVolatilityRatio(bars);
    const meanReversionSpeed = this.calculateMeanReversionSpeed(bars);
    const momentumPersistence = this.calculateMomentumPersistence(bars);

    // Classify regime based on indicators
    const classification = this.classifyRegime(
      trendStrength,
      volatilityRatio,
      meanReversionSpeed,
      momentumPersistence
    );

    return {
      type: classification.type,
      confidence: classification.confidence,
      strength: classification.strength,
      timeframe,
      timestamp: new Date(),
      metrics: {
        trendStrength,
        volatilityRatio,
        meanReversionSpeed,
        momentumPersistence,
      },
    };
  }

  /**
   * Detect regime across multiple timeframes
   */
  public detectMultiTimeframeRegime(
    marketData: MarketData,
    timeframes: TimeframeWeight[]
  ): MultiTimeframeRegime {
    const regimes = timeframes.map((tf) =>
      this.detectRegime(marketData, tf.timeframe)
    );

    const coherence = this.calculateCoherence(regimes, timeframes);
    const dominantRegime = this.determineDominantRegime(regimes, timeframes);

    return {
      regimes,
      coherence,
      dominantRegime,
      timestamp: new Date(),
    };
  }

  /**
   * Calculate trend strength using multiple methods
   */
  private calculateTrendStrength(bars: OHLCV[]): number {
    switch (this.config.trendStrengthMethod) {
      case 'adx':
        return this.calculateADX(bars);
      case 'linear_regression':
        return this.calculateLinearRegressionStrength(bars);
      case 'percentile_rank':
        return this.calculatePercentileRank(bars);
      default:
        return this.calculateADX(bars);
    }
  }

  /**
   * ADX (Average Directional Index) calculation
   * Returns 0-100, where >25 indicates strong trend
   */
  private calculateADX(bars: OHLCV[]): number {
    const period = 14;
    if (bars.length < period + 1) return 0;

    // Calculate True Range
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

    // Calculate +DM and -DM
    const plusDM: number[] = [];
    const minusDM: number[] = [];
    for (let i = 1; i < bars.length; i++) {
      const upMove = bars[i].high - bars[i - 1].high;
      const downMove = bars[i - 1].low - bars[i].low;

      plusDM.push(upMove > downMove && upMove > 0 ? upMove : 0);
      minusDM.push(downMove > upMove && downMove > 0 ? downMove : 0);
    }

    // Smooth the values using Wilder's smoothing
    const smoothTR = this.wilderSmooth(tr, period);
    const smoothPlusDM = this.wilderSmooth(plusDM, period);
    const smoothMinusDM = this.wilderSmooth(minusDM, period);

    // Calculate +DI and -DI
    const plusDI = smoothPlusDM.map((dm, i) => (dm / smoothTR[i]) * 100);
    const minusDI = smoothMinusDM.map((dm, i) => (dm / smoothTR[i]) * 100);

    // Calculate DX and ADX
    const dx = plusDI.map((pdi, i) => {
      const sum = pdi + minusDI[i];
      return sum === 0 ? 0 : (Math.abs(pdi - minusDI[i]) / sum) * 100;
    });

    const adx = this.wilderSmooth(dx, period);
    return adx[adx.length - 1];
  }

  /**
   * Wilder's smoothing method
   */
  private wilderSmooth(values: number[], period: number): number[] {
    const smoothed: number[] = [];
    let sum = values.slice(0, period).reduce((a, b) => a + b, 0);
    smoothed.push(sum / period);

    for (let i = period; i < values.length; i++) {
      const next = (smoothed[smoothed.length - 1] * (period - 1) + values[i]) / period;
      smoothed.push(next);
    }

    return smoothed;
  }

  /**
   * Linear regression strength (R-squared)
   */
  private calculateLinearRegressionStrength(bars: OHLCV[]): number {
    const closes = bars.map((b) => b.close);
    const n = closes.length;
    const xMean = (n - 1) / 2;
    const yMean = closes.reduce((a, b) => a + b, 0) / n;

    let numerator = 0;
    let denominator = 0;

    for (let i = 0; i < n; i++) {
      numerator += (i - xMean) * (closes[i] - yMean);
      denominator += (i - xMean) ** 2;
    }

    const slope = numerator / denominator;
    const intercept = yMean - slope * xMean;

    // Calculate R-squared
    let ssRes = 0;
    let ssTot = 0;
    for (let i = 0; i < n; i++) {
      const predicted = slope * i + intercept;
      ssRes += (closes[i] - predicted) ** 2;
      ssTot += (closes[i] - yMean) ** 2;
    }

    const rSquared = 1 - ssRes / ssTot;
    return Math.max(0, Math.min(100, rSquared * 100)); // Normalize to 0-100
  }

  /**
   * Percentile rank of current price
   */
  private calculatePercentileRank(bars: OHLCV[]): number {
    const closes = bars.map((b) => b.close);
    const current = closes[closes.length - 1];
    const belowCount = closes.filter((c) => c < current).length;
    return (belowCount / closes.length) * 100;
  }

  /**
   * Calculate volatility ratio (current vs historical)
   */
  private calculateVolatilityRatio(bars: OHLCV[]): number {
    const atr = this.calculateATR(bars, 14);
    const historicalATR = this.calculateATR(
      bars.slice(0, Math.floor(bars.length / 2)),
      14
    );

    return historicalATR === 0 ? 1 : atr / historicalATR;
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

    const smoothed = this.wilderSmooth(tr, period);
    return smoothed[smoothed.length - 1];
  }

  /**
   * Calculate mean reversion speed (half-life of price deviations)
   */
  private calculateMeanReversionSpeed(bars: OHLCV[]): number {
    const closes = bars.map((b) => b.close);
    const sma = closes.reduce((a, b) => a + b, 0) / closes.length;

    // Calculate deviations from mean
    const deviations = closes.map((c) => c - sma);

    // Estimate autocorrelation (lag-1)
    let numerator = 0;
    let denominator = 0;

    for (let i = 1; i < deviations.length; i++) {
      numerator += deviations[i] * deviations[i - 1];
      denominator += deviations[i - 1] ** 2;
    }

    const autocorr = denominator === 0 ? 0 : numerator / denominator;

    // Half-life formula: -log(2) / log(autocorr)
    // Normalize to 0-1: faster mean reversion = higher value
    if (autocorr <= 0 || autocorr >= 1) return 0;

    const halfLife = -Math.log(2) / Math.log(autocorr);
    return Math.max(0, Math.min(1, 1 / halfLife));
  }

  /**
   * Calculate momentum persistence (how long trends last)
   */
  private calculateMomentumPersistence(bars: OHLCV[]): number {
    const closes = bars.map((b) => b.close);
    let trendLength = 0;
    let maxTrendLength = 0;
    let lastDirection = 0;

    for (let i = 1; i < closes.length; i++) {
      const direction = closes[i] > closes[i - 1] ? 1 : -1;

      if (direction === lastDirection) {
        trendLength++;
      } else {
        maxTrendLength = Math.max(maxTrendLength, trendLength);
        trendLength = 1;
        lastDirection = direction;
      }
    }

    maxTrendLength = Math.max(maxTrendLength, trendLength);

    // Normalize to 0-1
    return Math.min(1, maxTrendLength / (closes.length / 4));
  }

  /**
   * Classify regime based on calculated metrics
   */
  private classifyRegime(
    trendStrength: number,
    volatilityRatio: number,
    meanReversionSpeed: number,
    momentumPersistence: number
  ): { type: RegimeType; confidence: number; strength: number } {
    // Adaptive thresholds based on volatility
    const trendThreshold = this.config.adaptiveThresholds
      ? 25 * volatilityRatio
      : 25;

    // Decision logic
    if (trendStrength > trendThreshold && momentumPersistence > 0.3) {
      return {
        type: RegimeType.MOMENTUM,
        confidence: Math.min(1, trendStrength / 50),
        strength: (trendStrength / 100) * 2 - 1, // -1 to 1
      };
    } else if (meanReversionSpeed > 0.6 && trendStrength < 20) {
      return {
        type: RegimeType.MEAN_REVERSION,
        confidence: meanReversionSpeed,
        strength: -meanReversionSpeed, // Negative for mean reversion
      };
    } else if (
      Math.abs(trendStrength - 25) < 10 &&
      Math.abs(meanReversionSpeed - 0.5) < 0.2
    ) {
      return {
        type: RegimeType.TRANSITION,
        confidence: 0.5,
        strength: 0,
      };
    } else {
      return {
        type: RegimeType.NEUTRAL,
        confidence: 1 - Math.abs(trendStrength - 25) / 25,
        strength: 0,
      };
    }
  }

  /**
   * Calculate coherence across multiple timeframes
   */
  private calculateCoherence(
    regimes: RegimeSignal[],
    timeframes: TimeframeWeight[]
  ): number {
    if (regimes.length === 0) return 0;

    const weightedRegimes = regimes.map((regime, i) => ({
      regime,
      weight: timeframes[i].weight,
    }));

    // Count agreements (same regime type)
    const regimeTypes = weightedRegimes.map((wr) => wr.regime.type);
    const mostCommon = this.mostCommonRegime(regimeTypes);

    const agreementWeight = weightedRegimes
      .filter((wr) => wr.regime.type === mostCommon)
      .reduce((sum, wr) => sum + wr.weight, 0);

    return agreementWeight;
  }

  /**
   * Determine dominant regime across timeframes
   */
  private determineDominantRegime(
    regimes: RegimeSignal[],
    timeframes: TimeframeWeight[]
  ): RegimeType {
    const weightedScores: Map<RegimeType, number> = new Map();

    regimes.forEach((regime, i) => {
      const weight = timeframes[i].weight * regime.confidence;
      const current = weightedScores.get(regime.type) ?? 0;
      weightedScores.set(regime.type, current + weight);
    });

    let maxScore = 0;
    let dominant = RegimeType.NEUTRAL;

    weightedScores.forEach((score, type) => {
      if (score > maxScore) {
        maxScore = score;
        dominant = type;
      }
    });

    return dominant;
  }

  /**
   * Find most common regime type
   */
  private mostCommonRegime(types: RegimeType[]): RegimeType {
    const counts = new Map<RegimeType, number>();
    types.forEach((type) => {
      counts.set(type, (counts.get(type) ?? 0) + 1);
    });

    let maxCount = 0;
    let mostCommon = RegimeType.NEUTRAL;

    counts.forEach((count, type) => {
      if (count > maxCount) {
        maxCount = count;
        mostCommon = type;
      }
    });

    return mostCommon;
  }

  /**
   * Filter bars by timeframe (helper method)
   */
  private filterByTimeframe(bars: OHLCV[], timeframe: Timeframe): OHLCV[] {
    // For now, return all bars assuming they match the timeframe
    // In production, implement proper timeframe filtering/aggregation
    return bars.filter((b) => b.timeframe === timeframe);
  }
}
