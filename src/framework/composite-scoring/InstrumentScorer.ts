/**
 * Composite Instrument Scoring System
 *
 * Aggregates multiple factors to rank and score trading instruments:
 * - Regime alignment
 * - Risk-adjusted expectancy
 * - Technical indicators
 * - Multi-timeframe coherence
 */

import {
  CompositeScore,
  ScoringFactor,
  MarketData,
  MultiTimeframeRegime,
  RiskAdjustedExpectancy,
  RegimeType,
  Timeframe,
  TimeframeWeight,
} from '../core/types';

/**
 * Configuration for instrument scorer
 */
export interface ScorerConfig {
  factors: ScoringFactor[];
  minScore: number;
  normalizeScores: boolean;
  includeTimeframeBreakdown: boolean;
}

/**
 * Raw factor values before weighting
 */
interface RawFactorValues {
  regimeAlignment: number;
  riskAdjustedExpectancy: number;
  percentileExtreme: number;
  momentumStrength: number;
  volatilityFavorability: number;
}

/**
 * Main instrument scoring class
 */
export class InstrumentScorer {
  private config: ScorerConfig;

  constructor(config: Partial<ScorerConfig> = {}) {
    this.config = {
      factors: config.factors ?? this.getDefaultFactors(),
      minScore: config.minScore ?? 0.6,
      normalizeScores: config.normalizeScores ?? true,
      includeTimeframeBreakdown: config.includeTimeframeBreakdown ?? true,
    };
  }

  /**
   * Calculate composite score for an instrument
   */
  public calculateScore(
    instrument: string,
    marketData: MarketData,
    regime: MultiTimeframeRegime,
    expectancy: RiskAdjustedExpectancy,
    timeframes: TimeframeWeight[]
  ): CompositeScore {
    // Calculate raw factor values
    const rawValues = this.calculateRawFactors(
      marketData,
      regime,
      expectancy
    );

    // Convert to scoring factors with weights
    const factors = this.createScoringFactors(rawValues);

    // Calculate weighted total score
    const totalScore = factors.reduce(
      (sum, factor) => sum + factor.value * factor.weight,
      0
    );

    // Normalize to 0-1 range if enabled
    const finalScore = this.config.normalizeScores
      ? Math.max(0, Math.min(1, totalScore))
      : totalScore;

    // Calculate timeframe breakdown
    const timeframeScores = this.config.includeTimeframeBreakdown
      ? this.calculateTimeframeScores(marketData, regime, expectancy, timeframes)
      : undefined;

    return {
      instrument,
      totalScore: finalScore,
      factors,
      timestamp: new Date(),
      timeframeScores,
    };
  }

  /**
   * Rank multiple instruments by their composite scores
   */
  public rankInstruments(scores: CompositeScore[]): CompositeScore[] {
    // Sort by score descending
    const sorted = [...scores].sort((a, b) => b.totalScore - a.totalScore);

    // Assign ranks and percentiles
    return sorted.map((score, index) => ({
      ...score,
      rank: index + 1,
      percentile: ((sorted.length - index) / sorted.length) * 100,
    }));
  }

  /**
   * Filter instruments by minimum score
   */
  public filterByScore(scores: CompositeScore[]): CompositeScore[] {
    return scores.filter((s) => s.totalScore >= this.config.minScore);
  }

  /**
   * Get top N instruments
   */
  public getTopInstruments(
    scores: CompositeScore[],
    count: number
  ): CompositeScore[] {
    const ranked = this.rankInstruments(scores);
    return ranked.slice(0, count);
  }

  /**
   * Calculate raw factor values
   */
  private calculateRawFactors(
    marketData: MarketData,
    regime: MultiTimeframeRegime,
    expectancy: RiskAdjustedExpectancy
  ): RawFactorValues {
    return {
      regimeAlignment: this.calculateRegimeAlignment(regime),
      riskAdjustedExpectancy: this.normalizeExpectancy(
        expectancy.finalExpectancy,
        expectancy.confidence
      ),
      percentileExtreme: this.calculatePercentileExtreme(marketData),
      momentumStrength: this.calculateMomentumStrength(regime),
      volatilityFavorability: this.calculateVolatilityFavorability(
        expectancy.volatilityAdjustment
      ),
    };
  }

  /**
   * Create scoring factors from raw values
   */
  private createScoringFactors(raw: RawFactorValues): ScoringFactor[] {
    const factorMap = new Map<string, number>([
      ['regime_alignment', raw.regimeAlignment],
      ['risk_adjusted_expectancy', raw.riskAdjustedExpectancy],
      ['percentile_extreme', raw.percentileExtreme],
      ['momentum_strength', raw.momentumStrength],
      ['volatility_favorability', raw.volatilityFavorability],
    ]);

    return this.config.factors.map((factor) => ({
      ...factor,
      value: factorMap.get(factor.name) ?? 0,
    }));
  }

  /**
   * Calculate regime alignment score
   * Higher coherence + favorable regime = higher score
   */
  private calculateRegimeAlignment(regime: MultiTimeframeRegime): number {
    const coherence = regime.coherence;

    // Bonus for favorable regimes
    let regimeBonus = 0;
    if (regime.dominantRegime === RegimeType.MOMENTUM) {
      regimeBonus = 0.2; // Momentum regimes often favorable
    } else if (regime.dominantRegime === RegimeType.MEAN_REVERSION) {
      regimeBonus = 0.1; // Mean reversion can work too
    } else if (regime.dominantRegime === RegimeType.TRANSITION) {
      regimeBonus = -0.2; // Transitions are risky
    }

    const score = coherence + regimeBonus;
    return Math.max(0, Math.min(1, score));
  }

  /**
   * Normalize expectancy to 0-1 scale
   */
  private normalizeExpectancy(expectancy: number, confidence: number): number {
    // Expectancy can be negative, so map it to 0-1
    // Assume typical range is -2 to +2
    let normalized = (expectancy + 2) / 4;
    normalized = Math.max(0, Math.min(1, normalized));

    // Adjust by confidence
    return normalized * confidence;
  }

  /**
   * Calculate percentile extreme score
   * Higher when price is at extreme percentiles
   */
  private calculatePercentileExtreme(marketData: MarketData): number {
    const bars = marketData.bars.slice(-100);
    if (bars.length === 0) return 0;

    const closes = bars.map((b) => b.close);
    const current = marketData.currentPrice;

    // Calculate percentile rank
    const belowCount = closes.filter((c) => c < current).length;
    const percentile = (belowCount / closes.length) * 100;

    // Distance from 50th percentile (extreme = high score)
    const distanceFrom50 = Math.abs(percentile - 50);

    // Normalize to 0-1: 50 distance = 1.0
    return Math.min(1, distanceFrom50 / 50);
  }

  /**
   * Calculate momentum strength from regime
   */
  private calculateMomentumStrength(regime: MultiTimeframeRegime): number {
    // Find momentum regime strength
    const momentumRegimes = regime.regimes.filter(
      (r) => r.type === RegimeType.MOMENTUM
    );

    if (momentumRegimes.length === 0) return 0;

    // Average strength of momentum regimes
    const avgStrength =
      momentumRegimes.reduce((sum, r) => sum + Math.abs(r.strength), 0) /
      momentumRegimes.length;

    // Weight by confidence
    const avgConfidence =
      momentumRegimes.reduce((sum, r) => sum + r.confidence, 0) /
      momentumRegimes.length;

    return avgStrength * avgConfidence;
  }

  /**
   * Calculate volatility favorability
   * Lower volatility = more favorable
   */
  private calculateVolatilityFavorability(volAdjustment: number): number {
    // volAdjustment: negative = high vol, positive = low vol
    // Map to 0-1 where 1 = most favorable (low vol)
    // Assume range is -0.5 to +0.5
    const normalized = (volAdjustment + 0.5) / 1.0;
    return Math.max(0, Math.min(1, normalized));
  }

  /**
   * Calculate scores for each timeframe
   */
  private calculateTimeframeScores(
    marketData: MarketData,
    regime: MultiTimeframeRegime,
    expectancy: RiskAdjustedExpectancy,
    timeframes: TimeframeWeight[]
  ): Map<Timeframe, number> {
    const scores = new Map<Timeframe, number>();

    timeframes.forEach((tf) => {
      // Find regime for this timeframe
      const tfRegime = regime.regimes.find((r) => r.timeframe === tf.timeframe);

      if (tfRegime) {
        // Simple score based on regime confidence and strength
        const score = (tfRegime.confidence + Math.abs(tfRegime.strength)) / 2;
        scores.set(tf.timeframe, score);
      } else {
        scores.set(tf.timeframe, 0);
      }
    });

    return scores;
  }

  /**
   * Get default scoring factors
   */
  private getDefaultFactors(): ScoringFactor[] {
    return [
      {
        name: 'regime_alignment',
        value: 0,
        weight: 0.25,
        category: 'regime',
      },
      {
        name: 'risk_adjusted_expectancy',
        value: 0,
        weight: 0.25,
        category: 'risk',
      },
      {
        name: 'percentile_extreme',
        value: 0,
        weight: 0.20,
        category: 'technical',
      },
      {
        name: 'momentum_strength',
        value: 0,
        weight: 0.15,
        category: 'technical',
      },
      {
        name: 'volatility_favorability',
        value: 0,
        weight: 0.15,
        category: 'risk',
      },
    ];
  }

  /**
   * Analyze factor contributions for debugging
   */
  public analyzeFactor Contributions(score: CompositeScore): {
    factor: string;
    value: number;
    weight: number;
    contribution: number;
    percentage: number;
  }[] {
    const totalScore = score.totalScore;

    return score.factors.map((factor) => {
      const contribution = factor.value * factor.weight;
      const percentage = totalScore === 0 ? 0 : (contribution / totalScore) * 100;

      return {
        factor: factor.name,
        value: factor.value,
        weight: factor.weight,
        contribution,
        percentage,
      };
    });
  }

  /**
   * Update scoring factor weights
   */
  public updateFactorWeights(newFactors: ScoringFactor[]): void {
    this.config.factors = newFactors;
  }

  /**
   * Get current configuration
   */
  public getConfig(): ScorerConfig {
    return { ...this.config };
  }
}
