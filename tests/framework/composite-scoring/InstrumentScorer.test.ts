/**
 * Unit tests for Composite Instrument Scoring
 */

import { InstrumentScorer } from '../../../src/framework/composite-scoring/InstrumentScorer';
import { RegimeType, Timeframe, CompositeScore } from '../../../src/framework/core/types';
import {
  generateMockMarketData,
  generateMockMultiTimeframeRegime,
  getDefaultTimeframeWeights,
} from '../mocks/marketData';

describe('InstrumentScorer', () => {
  let scorer: InstrumentScorer;

  beforeEach(() => {
    scorer = new InstrumentScorer({
      minScore: 0.6,
      normalizeScores: true,
      includeTimeframeBreakdown: true,
    });
  });

  const mockExpectancy = {
    baseExpectancy: 0.5,
    volatilityAdjustment: 0.1,
    regimeAdjustment: 0.15,
    finalExpectancy: 0.75,
    confidence: 0.8,
    instrument: 'AAPL',
    timestamp: new Date(),
  };

  describe('calculateScore', () => {
    it('should calculate composite score', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const regime = generateMockMultiTimeframeRegime(RegimeType.MOMENTUM, 0.8);
      const timeframes = getDefaultTimeframeWeights();

      const score = scorer.calculateScore(
        'AAPL',
        marketData,
        regime,
        mockExpectancy,
        timeframes
      );

      expect(score.instrument).toBe('AAPL');
      expect(score.totalScore).toBeGreaterThanOrEqual(0);
      expect(score.totalScore).toBeLessThanOrEqual(1);
      expect(score.factors.length).toBeGreaterThan(0);
    });

    it('should include all required factors', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const regime = generateMockMultiTimeframeRegime(RegimeType.MOMENTUM, 0.8);
      const timeframes = getDefaultTimeframeWeights();

      const score = scorer.calculateScore(
        'AAPL',
        marketData,
        regime,
        mockExpectancy,
        timeframes
      );

      const factorNames = score.factors.map((f) => f.name);
      expect(factorNames).toContain('regime_alignment');
      expect(factorNames).toContain('risk_adjusted_expectancy');
      expect(factorNames).toContain('percentile_extreme');
      expect(factorNames).toContain('momentum_strength');
      expect(factorNames).toContain('volatility_favorability');
    });

    it('should have normalized scores when enabled', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const regime = generateMockMultiTimeframeRegime(RegimeType.MOMENTUM, 0.8);
      const timeframes = getDefaultTimeframeWeights();

      const score = scorer.calculateScore(
        'AAPL',
        marketData,
        regime,
        mockExpectancy,
        timeframes
      );

      expect(score.totalScore).toBeGreaterThanOrEqual(0);
      expect(score.totalScore).toBeLessThanOrEqual(1);
    });

    it('should include timeframe breakdown when enabled', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const regime = generateMockMultiTimeframeRegime(RegimeType.MOMENTUM, 0.8);
      const timeframes = getDefaultTimeframeWeights();

      const score = scorer.calculateScore(
        'AAPL',
        marketData,
        regime,
        mockExpectancy,
        timeframes
      );

      expect(score.timeframeScores).toBeDefined();
      expect(score.timeframeScores!.size).toBe(timeframes.length);
    });

    it('should score higher for favorable regimes', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const timeframes = getDefaultTimeframeWeights();

      const momentumRegime = generateMockMultiTimeframeRegime(RegimeType.MOMENTUM, 0.9);
      const transitionRegime = generateMockMultiTimeframeRegime(RegimeType.TRANSITION, 0.5);

      const momentumScore = scorer.calculateScore(
        'AAPL',
        marketData,
        momentumRegime,
        mockExpectancy,
        timeframes
      );

      const transitionScore = scorer.calculateScore(
        'AAPL',
        marketData,
        transitionRegime,
        mockExpectancy,
        timeframes
      );

      expect(momentumScore.totalScore).toBeGreaterThan(transitionScore.totalScore);
    });
  });

  describe('rankInstruments', () => {
    it('should rank instruments by score', () => {
      const scores: CompositeScore[] = [
        {
          instrument: 'AAPL',
          totalScore: 0.8,
          factors: [],
          timestamp: new Date(),
        },
        {
          instrument: 'GOOGL',
          totalScore: 0.9,
          factors: [],
          timestamp: new Date(),
        },
        {
          instrument: 'MSFT',
          totalScore: 0.7,
          factors: [],
          timestamp: new Date(),
        },
      ];

      const ranked = scorer.rankInstruments(scores);

      expect(ranked[0].instrument).toBe('GOOGL'); // Highest score
      expect(ranked[0].rank).toBe(1);
      expect(ranked[1].instrument).toBe('AAPL');
      expect(ranked[1].rank).toBe(2);
      expect(ranked[2].instrument).toBe('MSFT'); // Lowest score
      expect(ranked[2].rank).toBe(3);
    });

    it('should assign percentiles', () => {
      const scores: CompositeScore[] = Array.from({ length: 10 }, (_, i) => ({
        instrument: `INST${i}`,
        totalScore: i * 0.1,
        factors: [],
        timestamp: new Date(),
      }));

      const ranked = scorer.rankInstruments(scores);

      expect(ranked[0].percentile).toBe(100); // Top rank
      expect(ranked[9].percentile).toBe(10); // Bottom rank
    });

    it('should preserve original scores', () => {
      const originalScores: CompositeScore[] = [
        { instrument: 'A', totalScore: 0.5, factors: [], timestamp: new Date() },
        { instrument: 'B', totalScore: 0.8, factors: [], timestamp: new Date() },
      ];

      const ranked = scorer.rankInstruments(originalScores);

      // Original array should not be modified
      expect(originalScores[0].instrument).toBe('A');
      expect(ranked[0].instrument).toBe('B');
    });
  });

  describe('filterByScore', () => {
    it('should filter instruments below minimum score', () => {
      const scores: CompositeScore[] = [
        { instrument: 'AAPL', totalScore: 0.8, factors: [], timestamp: new Date() },
        { instrument: 'GOOGL', totalScore: 0.5, factors: [], timestamp: new Date() },
        { instrument: 'MSFT', totalScore: 0.7, factors: [], timestamp: new Date() },
      ];

      const filtered = scorer.filterByScore(scores);

      expect(filtered).toHaveLength(2);
      expect(filtered.find((s) => s.instrument === 'GOOGL')).toBeUndefined();
    });

    it('should include scores exactly at minimum', () => {
      const scores: CompositeScore[] = [
        { instrument: 'AAPL', totalScore: 0.6, factors: [], timestamp: new Date() },
      ];

      const filtered = scorer.filterByScore(scores);

      expect(filtered).toHaveLength(1);
    });

    it('should handle empty array', () => {
      const filtered = scorer.filterByScore([]);
      expect(filtered).toHaveLength(0);
    });
  });

  describe('getTopInstruments', () => {
    it('should return top N instruments', () => {
      const scores: CompositeScore[] = Array.from({ length: 10 }, (_, i) => ({
        instrument: `INST${i}`,
        totalScore: i * 0.1,
        factors: [],
        timestamp: new Date(),
      }));

      const top3 = scorer.getTopInstruments(scores, 3);

      expect(top3).toHaveLength(3);
      expect(top3[0].totalScore).toBeGreaterThanOrEqual(top3[1].totalScore);
      expect(top3[1].totalScore).toBeGreaterThanOrEqual(top3[2].totalScore);
    });

    it('should handle N greater than array length', () => {
      const scores: CompositeScore[] = [
        { instrument: 'AAPL', totalScore: 0.8, factors: [], timestamp: new Date() },
      ];

      const top5 = scorer.getTopInstruments(scores, 5);
      expect(top5).toHaveLength(1);
    });
  });

  describe('analyzeFactorContributions', () => {
    it('should analyze factor contributions', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const regime = generateMockMultiTimeframeRegime(RegimeType.MOMENTUM, 0.8);
      const timeframes = getDefaultTimeframeWeights();

      const score = scorer.calculateScore(
        'AAPL',
        marketData,
        regime,
        mockExpectancy,
        timeframes
      );

      const analysis = scorer.analyzeFactorContributions(score);

      expect(analysis.length).toBe(score.factors.length);
      analysis.forEach((a) => {
        expect(a).toHaveProperty('factor');
        expect(a).toHaveProperty('value');
        expect(a).toHaveProperty('weight');
        expect(a).toHaveProperty('contribution');
        expect(a).toHaveProperty('percentage');
      });
    });

    it('should have contributions sum to total score', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const regime = generateMockMultiTimeframeRegime(RegimeType.MOMENTUM, 0.8);
      const timeframes = getDefaultTimeframeWeights();

      const score = scorer.calculateScore(
        'AAPL',
        marketData,
        regime,
        mockExpectancy,
        timeframes
      );

      const analysis = scorer.analyzeFactorContributions(score);
      const totalContribution = analysis.reduce((sum, a) => sum + a.contribution, 0);

      expect(totalContribution).toBeCloseTo(score.totalScore, 2);
    });
  });

  describe('updateFactorWeights', () => {
    it('should update factor weights', () => {
      const newFactors = [
        {
          name: 'regime_alignment',
          value: 0,
          weight: 0.5,
          category: 'regime' as const,
        },
        {
          name: 'risk_adjusted_expectancy',
          value: 0,
          weight: 0.5,
          category: 'risk' as const,
        },
      ];

      scorer.updateFactorWeights(newFactors);

      const config = scorer.getConfig();
      expect(config.factors).toEqual(newFactors);
    });
  });

  describe('Edge Cases', () => {
    it('should handle zero scores', () => {
      const score: CompositeScore = {
        instrument: 'TEST',
        totalScore: 0,
        factors: [],
        timestamp: new Date(),
      };

      const analysis = scorer.analyzeFactorContributions(score);
      expect(analysis).toBeDefined();
    });

    it('should handle perfect scores', () => {
      const score: CompositeScore = {
        instrument: 'TEST',
        totalScore: 1.0,
        factors: [
          { name: 'test', value: 1, weight: 1, category: 'technical' },
        ],
        timestamp: new Date(),
      };

      const ranked = scorer.rankInstruments([score]);
      expect(ranked[0].percentile).toBe(100);
    });

    it('should handle identical scores', () => {
      const scores: CompositeScore[] = [
        { instrument: 'A', totalScore: 0.8, factors: [], timestamp: new Date() },
        { instrument: 'B', totalScore: 0.8, factors: [], timestamp: new Date() },
        { instrument: 'C', totalScore: 0.8, factors: [], timestamp: new Date() },
      ];

      const ranked = scorer.rankInstruments(scores);
      expect(ranked).toHaveLength(3);
    });

    it('should handle negative expectancy', () => {
      const negativeExpectancy = {
        ...mockExpectancy,
        finalExpectancy: -0.5,
      };

      const marketData = generateMockMarketData('AAPL', 150);
      const regime = generateMockMultiTimeframeRegime(RegimeType.NEUTRAL, 0.5);
      const timeframes = getDefaultTimeframeWeights();

      const score = scorer.calculateScore(
        'AAPL',
        marketData,
        regime,
        negativeExpectancy,
        timeframes
      );

      expect(score.totalScore).toBeGreaterThanOrEqual(0);
    });
  });
});
