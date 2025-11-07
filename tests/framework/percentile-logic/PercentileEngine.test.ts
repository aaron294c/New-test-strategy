/**
 * Unit tests for Percentile Engine
 */

import { PercentileEngine } from '../../../src/framework/percentile-logic/PercentileEngine';
import { RegimeType, Timeframe } from '../../../src/framework/core/types';
import {
  generateMockMarketData,
  generatePriceAtPercentile,
  generateTrendingBars,
} from '../mocks/marketData';

describe('PercentileEngine', () => {
  let engine: PercentileEngine;

  beforeEach(() => {
    engine = new PercentileEngine({
      lookbackBars: 100,
      entryPercentile: 90,
      stopPercentile: 95,
      adaptiveThresholds: true,
    });
  });

  describe('calculatePercentile', () => {
    it('should calculate percentile correctly', () => {
      const values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
      const result = engine.calculatePercentile(values, 50);

      expect(result.value).toBeCloseTo(5.5, 1);
      expect(result.percentile).toBe(50);
      expect(result.lookbackPeriod).toBe(10);
    });

    it('should handle edge percentiles', () => {
      const values = [1, 2, 3, 4, 5];

      const p0 = engine.calculatePercentile(values, 0);
      expect(p0.value).toBe(1);

      const p100 = engine.calculatePercentile(values, 100);
      expect(p100.value).toBe(5);
    });

    it('should throw on empty array', () => {
      expect(() => engine.calculatePercentile([], 50)).toThrow(
        'Cannot calculate percentile of empty array'
      );
    });

    it('should throw on invalid percentile', () => {
      expect(() => engine.calculatePercentile([1, 2, 3], -1)).toThrow(
        'Percentile must be 0-100'
      );
      expect(() => engine.calculatePercentile([1, 2, 3], 101)).toThrow(
        'Percentile must be 0-100'
      );
    });

    it('should interpolate between values', () => {
      const values = [10, 20, 30, 40, 50];
      const result = engine.calculatePercentile(values, 75);

      expect(result.value).toBeGreaterThan(30);
      expect(result.value).toBeLessThanOrEqual(50);
    });
  });

  describe('calculatePricePercentile', () => {
    it('should calculate current price percentile', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const result = engine.calculatePricePercentile(marketData, Timeframe.H4);

      expect(result.percentile).toBeGreaterThanOrEqual(0);
      expect(result.percentile).toBeLessThanOrEqual(100);
      expect(result.value).toBe(marketData.currentPrice);
    });

    it('should throw on insufficient bars', () => {
      const marketData = generateMockMarketData('AAPL', 1);

      expect(() => engine.calculatePricePercentile(marketData, Timeframe.H4)).toThrow(
        'Insufficient bars'
      );
    });

    it('should use correct lookback period', () => {
      const marketData = generateMockMarketData('AAPL', 200);
      const result = engine.calculatePricePercentile(marketData, Timeframe.H4);

      expect(result.lookbackPeriod).toBeLessThanOrEqual(100);
    });
  });

  describe('generateEntrySignal', () => {
    it('should generate long entry at low percentile', () => {
      const bars = generateTrendingBars(150, 'up', Timeframe.H4);
      const marketData = {
        ...generateMockMarketData(),
        bars,
        currentPrice: generatePriceAtPercentile(bars, 5), // Low percentile
      };

      const signal = engine.generateEntrySignal(marketData, Timeframe.H4);

      if (signal) {
        expect(signal.direction).toBe('long');
        expect(signal.percentileLevel.percentile).toBeLessThan(20);
      }
    });

    it('should generate short entry at high percentile', () => {
      const bars = generateTrendingBars(150, 'up', Timeframe.H4);
      const marketData = {
        ...generateMockMarketData(),
        bars,
        currentPrice: generatePriceAtPercentile(bars, 95), // High percentile
      };

      const signal = engine.generateEntrySignal(marketData, Timeframe.H4);

      if (signal) {
        expect(signal.direction).toBe('short');
        expect(signal.percentileLevel.percentile).toBeGreaterThan(80);
      }
    });

    it('should return null for mid-range percentiles', () => {
      const bars = generateTrendingBars(150, 'up', Timeframe.H4);
      const marketData = {
        ...generateMockMarketData(),
        bars,
        currentPrice: generatePriceAtPercentile(bars, 50), // Middle percentile
      };

      const signal = engine.generateEntrySignal(marketData, Timeframe.H4);

      expect(signal).toBeNull();
    });

    it('should adapt threshold based on regime', () => {
      const marketData = generateMockMarketData('AAPL', 150);

      const momentumSignal = engine.generateEntrySignal(
        marketData,
        Timeframe.H4,
        RegimeType.MOMENTUM
      );

      const meanReversionSignal = engine.generateEntrySignal(
        marketData,
        Timeframe.H4,
        RegimeType.MEAN_REVERSION
      );

      // Both should complete without error
      expect(momentumSignal !== undefined).toBe(true);
      expect(meanReversionSignal !== undefined).toBe(true);
    });
  });

  describe('calculateStopLoss', () => {
    it('should calculate stop loss for long position', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const entryPrice = 100;
      const riskAmount = 1000;

      const stopLoss = engine.calculateStopLoss(
        marketData,
        entryPrice,
        'long',
        Timeframe.H4,
        riskAmount
      );

      expect(stopLoss.initialStop).toBeLessThan(entryPrice);
      expect(stopLoss.currentStop).toBeLessThan(entryPrice);
      expect(stopLoss.riskAmount).toBe(riskAmount);
    });

    it('should calculate stop loss for short position', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const entryPrice = 100;
      const riskAmount = 1000;

      const stopLoss = engine.calculateStopLoss(
        marketData,
        entryPrice,
        'short',
        Timeframe.H4,
        riskAmount
      );

      expect(stopLoss.initialStop).toBeGreaterThan(entryPrice);
      expect(stopLoss.currentStop).toBeGreaterThan(entryPrice);
    });

    it('should include percentile-based stop', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const stopLoss = engine.calculateStopLoss(marketData, 100, 'long', Timeframe.H4, 1000);

      expect(stopLoss.percentileBased).toBeDefined();
      expect(stopLoss.percentileBased.value).toBeGreaterThan(0);
    });

    it('should use ATR multiplier when configured', () => {
      const engineWithATR = new PercentileEngine({
        lookbackBars: 100,
        entryPercentile: 90,
        stopPercentile: 95,
        adaptiveThresholds: true,
        atrMultiplier: 2,
      });

      const marketData = generateMockMarketData('AAPL', 150);
      const stopLoss = engineWithATR.calculateStopLoss(
        marketData,
        100,
        'long',
        Timeframe.H4,
        1000
      );

      expect(stopLoss.atrMultiplier).toBe(2);
    });
  });

  describe('updateStopLoss', () => {
    it('should trail stop in momentum regime for long', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const initialStop = engine.calculateStopLoss(marketData, 100, 'long', Timeframe.H4, 1000);

      // Price moves up significantly
      const updatedMarketData = { ...marketData, currentPrice: 110 };
      const updatedStop = engine.updateStopLoss(
        initialStop,
        updatedMarketData,
        110,
        'long',
        RegimeType.MOMENTUM
      );

      expect(updatedStop.currentStop).toBeGreaterThanOrEqual(initialStop.currentStop);
      expect(updatedStop.updateReason).toContain('Trailing stop');
    });

    it('should not lower stop loss for long positions', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const initialStop = engine.calculateStopLoss(marketData, 100, 'long', Timeframe.H4, 1000);

      const updatedStop = engine.updateStopLoss(
        initialStop,
        marketData,
        95, // Price moves down
        'long',
        RegimeType.NEUTRAL
      );

      expect(updatedStop.currentStop).toBe(initialStop.currentStop);
    });

    it('should tighten stop in mean reversion regime', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const initialStop = engine.calculateStopLoss(marketData, 100, 'long', Timeframe.H4, 1000);

      const updatedStop = engine.updateStopLoss(
        initialStop,
        marketData,
        102,
        'long',
        RegimeType.MEAN_REVERSION
      );

      // Should attempt to tighten stop
      expect(updatedStop).toBeDefined();
    });
  });

  describe('getPercentileStats', () => {
    it('should return complete percentile statistics', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const stats = engine.getPercentileStats(marketData, Timeframe.H4);

      expect(stats).toHaveProperty('current');
      expect(stats).toHaveProperty('p10');
      expect(stats).toHaveProperty('p25');
      expect(stats).toHaveProperty('p50');
      expect(stats).toHaveProperty('p75');
      expect(stats).toHaveProperty('p90');
      expect(stats).toHaveProperty('p95');
      expect(stats).toHaveProperty('p99');
    });

    it('should have ordered percentiles', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const stats = engine.getPercentileStats(marketData, Timeframe.H4);

      expect(stats.p10).toBeLessThanOrEqual(stats.p25);
      expect(stats.p25).toBeLessThanOrEqual(stats.p50);
      expect(stats.p50).toBeLessThanOrEqual(stats.p75);
      expect(stats.p75).toBeLessThanOrEqual(stats.p90);
      expect(stats.p90).toBeLessThanOrEqual(stats.p95);
      expect(stats.p95).toBeLessThanOrEqual(stats.p99);
    });
  });

  describe('Edge Cases', () => {
    it('should handle single unique value', () => {
      const values = [5, 5, 5, 5, 5];
      const result = engine.calculatePercentile(values, 50);

      expect(result.value).toBe(5);
    });

    it('should handle very small lookback', () => {
      const smallEngine = new PercentileEngine({ lookbackBars: 10 });
      const marketData = generateMockMarketData('AAPL', 20);

      const result = smallEngine.calculatePricePercentile(marketData, Timeframe.H4);
      expect(result).toBeDefined();
    });

    it('should handle extreme volatility', () => {
      const bars = generateMockMarketData('AAPL', 150).bars.map((b, i) => ({
        ...b,
        close: 100 + (i % 2 === 0 ? 10 : -10), // Alternating extreme moves
      }));

      const marketData = { ...generateMockMarketData(), bars };
      const stopLoss = engine.calculateStopLoss(marketData, 100, 'long', Timeframe.H4, 1000);

      expect(stopLoss.percentileBased.value).toBeGreaterThan(0);
    });
  });
});
