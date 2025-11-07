/**
 * Unit tests for Regime Detection
 */

import { RegimeDetector } from '../../../src/framework/regime-detection/RegimeDetector';
import { RegimeType, Timeframe } from '../../../src/framework/core/types';
import {
  generateMockMarketData,
  generateTrendingBars,
  generateMeanRevertingBars,
  getDefaultTimeframeWeights,
  generateMultiTimeframeData,
} from '../mocks/marketData';

describe('RegimeDetector', () => {
  let detector: RegimeDetector;

  beforeEach(() => {
    detector = new RegimeDetector({
      lookbackPeriod: 100,
      coherenceThreshold: 0.6,
    });
  });

  describe('detectRegime', () => {
    it('should detect momentum regime in trending market', () => {
      const trendingBars = generateTrendingBars(150, 'up', Timeframe.H4);
      const marketData = {
        ...generateMockMarketData(),
        bars: trendingBars,
      };

      const regime = detector.detectRegime(marketData, Timeframe.H4);

      expect(regime.type).toBe(RegimeType.MOMENTUM);
      expect(regime.confidence).toBeGreaterThan(0);
      expect(regime.strength).toBeGreaterThan(0);
      expect(regime.timeframe).toBe(Timeframe.H4);
      expect(regime.metrics.trendStrength).toBeDefined();
    });

    it('should detect mean reversion regime', () => {
      const meanRevertingBars = generateMeanRevertingBars(150, Timeframe.H4);
      const marketData = {
        ...generateMockMarketData(),
        bars: meanRevertingBars,
      };

      const regime = detector.detectRegime(marketData, Timeframe.H4);

      expect([RegimeType.MEAN_REVERSION, RegimeType.NEUTRAL]).toContain(regime.type);
      expect(regime.metrics.meanReversionSpeed).toBeGreaterThan(0);
    });

    it('should throw on insufficient data', () => {
      const marketData = {
        ...generateMockMarketData(),
        bars: generateMockMarketData('AAPL', 50).bars,
      };

      expect(() => detector.detectRegime(marketData, Timeframe.H4)).toThrow(
        'Insufficient data'
      );
    });

    it('should calculate all required metrics', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const regime = detector.detectRegime(marketData, Timeframe.H4);

      expect(regime.metrics).toHaveProperty('trendStrength');
      expect(regime.metrics).toHaveProperty('volatilityRatio');
      expect(regime.metrics).toHaveProperty('meanReversionSpeed');
      expect(regime.metrics).toHaveProperty('momentumPersistence');
    });

    it('should have confidence between 0 and 1', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const regime = detector.detectRegime(marketData, Timeframe.H4);

      expect(regime.confidence).toBeGreaterThanOrEqual(0);
      expect(regime.confidence).toBeLessThanOrEqual(1);
    });

    it('should have strength between -1 and 1', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const regime = detector.detectRegime(marketData, Timeframe.H4);

      expect(regime.strength).toBeGreaterThanOrEqual(-1);
      expect(regime.strength).toBeLessThanOrEqual(1);
    });
  });

  describe('detectMultiTimeframeRegime', () => {
    it('should detect regime across multiple timeframes', () => {
      const marketData = generateMultiTimeframeData('AAPL', [
        Timeframe.H1,
        Timeframe.H4,
        Timeframe.D1,
      ]);
      const timeframes = getDefaultTimeframeWeights();

      const multiRegime = detector.detectMultiTimeframeRegime(marketData, timeframes);

      expect(multiRegime.regimes).toHaveLength(3);
      expect(multiRegime.coherence).toBeGreaterThanOrEqual(0);
      expect(multiRegime.coherence).toBeLessThanOrEqual(1);
      expect(multiRegime.dominantRegime).toBeDefined();
    });

    it('should calculate coherence correctly', () => {
      const marketData = generateMultiTimeframeData('AAPL');
      const timeframes = getDefaultTimeframeWeights();

      const multiRegime = detector.detectMultiTimeframeRegime(marketData, timeframes);

      // Coherence should be weighted average of agreements
      expect(multiRegime.coherence).toBeGreaterThanOrEqual(0);
      expect(multiRegime.coherence).toBeLessThanOrEqual(1);
    });

    it('should identify dominant regime', () => {
      const trendingBars = generateTrendingBars(200, 'up');
      const marketData = generateMultiTimeframeData('AAPL');
      marketData.bars = trendingBars;

      const timeframes = getDefaultTimeframeWeights();
      const multiRegime = detector.detectMultiTimeframeRegime(marketData, timeframes);

      expect(Object.values(RegimeType)).toContain(multiRegime.dominantRegime);
    });

    it('should handle single timeframe', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const timeframes = [{ timeframe: Timeframe.H4, weight: 1.0 }];

      const multiRegime = detector.detectMultiTimeframeRegime(marketData, timeframes);

      expect(multiRegime.regimes).toHaveLength(1);
      expect(multiRegime.coherence).toBe(1.0);
    });
  });

  describe('Calculation Methods', () => {
    it('should calculate ADX correctly', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const regime = detector.detectRegime(marketData, Timeframe.H4);

      // ADX should be between 0 and 100
      expect(regime.metrics.trendStrength).toBeGreaterThanOrEqual(0);
      expect(regime.metrics.trendStrength).toBeLessThanOrEqual(100);
    });

    it('should calculate volatility ratio', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const regime = detector.detectRegime(marketData, Timeframe.H4);

      expect(regime.metrics.volatilityRatio).toBeGreaterThan(0);
    });

    it('should handle low volatility markets', () => {
      const bars = generateMeanRevertingBars(150, Timeframe.H4);
      const marketData = { ...generateMockMarketData(), bars };

      const regime = detector.detectRegime(marketData, Timeframe.H4);

      expect(regime.metrics.volatilityRatio).toBeDefined();
      expect(regime.metrics.volatilityRatio).toBeGreaterThan(0);
    });
  });

  describe('Edge Cases', () => {
    it('should handle exactly minimum bars', () => {
      const marketData = {
        ...generateMockMarketData(),
        bars: generateMockMarketData('AAPL', 100).bars,
      };

      const regime = detector.detectRegime(marketData, Timeframe.H4);
      expect(regime).toBeDefined();
    });

    it('should handle different timeframes', () => {
      const marketData = generateMockMarketData('AAPL', 150);

      [Timeframe.H1, Timeframe.H4, Timeframe.D1].forEach((tf) => {
        // Update bars to match timeframe
        marketData.bars = marketData.bars.map((b) => ({ ...b, timeframe: tf }));
        const regime = detector.detectRegime(marketData, tf);
        expect(regime.timeframe).toBe(tf);
      });
    });

    it('should handle flat market (no movement)', () => {
      const flatBars = generateMockMarketData('AAPL', 150).bars.map((b) => ({
        ...b,
        open: 100,
        high: 100.1,
        low: 99.9,
        close: 100,
      }));

      const marketData = { ...generateMockMarketData(), bars: flatBars };
      const regime = detector.detectRegime(marketData, Timeframe.H4);

      expect([RegimeType.NEUTRAL, RegimeType.MEAN_REVERSION]).toContain(regime.type);
    });
  });

  describe('Configuration', () => {
    it('should respect custom lookback period', () => {
      const customDetector = new RegimeDetector({ lookbackPeriod: 50 });
      const marketData = generateMockMarketData('AAPL', 60);

      expect(() => customDetector.detectRegime(marketData, Timeframe.H4)).not.toThrow();
    });

    it('should use adaptive thresholds when enabled', () => {
      const adaptiveDetector = new RegimeDetector({ adaptiveThresholds: true });
      const marketData = generateMockMarketData('AAPL', 150);

      const regime = adaptiveDetector.detectRegime(marketData, Timeframe.H4);
      expect(regime).toBeDefined();
    });

    it('should use different trend strength methods', () => {
      const methods = ['adx', 'linear_regression', 'percentile_rank'] as const;

      methods.forEach((method) => {
        const customDetector = new RegimeDetector({ trendStrengthMethod: method });
        const marketData = generateMockMarketData('AAPL', 150);
        const regime = customDetector.detectRegime(marketData, Timeframe.H4);

        expect(regime.metrics.trendStrength).toBeDefined();
      });
    });
  });
});
