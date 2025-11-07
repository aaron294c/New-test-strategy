/**
 * Unit tests for Risk-Adjusted Expectancy Calculator
 */

import {
  ExpectancyCalculator,
  TradeResult,
} from '../../../src/framework/risk-expectancy/ExpectancyCalculator';
import { RegimeType, Timeframe } from '../../../src/framework/core/types';
import { generateMockMarketData } from '../mocks/marketData';

describe('ExpectancyCalculator', () => {
  let calculator: ExpectancyCalculator;

  beforeEach(() => {
    calculator = new ExpectancyCalculator({
      minSampleSize: 30,
      volatilityLookback: 100,
      regimeAdjustmentFactor: 0.3,
      confidenceLevel: 0.95,
    });
  });

  const createMockTrade = (
    pnl: number,
    regime: RegimeType = RegimeType.NEUTRAL
  ): TradeResult => ({
    entryPrice: 100,
    exitPrice: 100 + pnl,
    direction: pnl > 0 ? 'long' : 'short',
    pnl,
    riskAmount: 100,
    regime,
    timestamp: new Date(),
  });

  describe('calculateRiskMetrics', () => {
    it('should calculate metrics for winning trades', () => {
      const trades: TradeResult[] = [
        createMockTrade(10), // Win
        createMockTrade(15), // Win
        createMockTrade(-5), // Loss
        createMockTrade(20), // Win
        createMockTrade(-8), // Loss
      ];

      trades.forEach((t) => calculator.addTradeResult(t));
      const metrics = calculator.calculateRiskMetrics();

      expect(metrics.winRate).toBe(0.6); // 3 wins out of 5
      expect(metrics.avgWin).toBeCloseTo(15, 1);
      expect(metrics.avgLoss).toBeCloseTo(6.5, 1);
      expect(metrics.expectancy).toBeGreaterThan(0);
      expect(metrics.sampleSize).toBe(5);
    });

    it('should handle all winning trades', () => {
      const trades = [createMockTrade(10), createMockTrade(15), createMockTrade(20)];
      trades.forEach((t) => calculator.addTradeResult(t));

      const metrics = calculator.calculateRiskMetrics();

      expect(metrics.winRate).toBe(1.0);
      expect(metrics.avgWin).toBeGreaterThan(0);
      expect(metrics.avgLoss).toBe(0);
      expect(metrics.expectancy).toBeGreaterThan(0);
    });

    it('should handle all losing trades', () => {
      const trades = [createMockTrade(-10), createMockTrade(-15), createMockTrade(-5)];
      trades.forEach((t) => calculator.addTradeResult(t));

      const metrics = calculator.calculateRiskMetrics();

      expect(metrics.winRate).toBe(0);
      expect(metrics.avgWin).toBe(0);
      expect(metrics.avgLoss).toBeGreaterThan(0);
      expect(metrics.expectancy).toBeLessThan(0);
    });

    it('should calculate Sharpe ratio', () => {
      const trades = Array.from({ length: 20 }, (_, i) =>
        createMockTrade(i % 3 === 0 ? 10 : -5)
      );
      trades.forEach((t) => calculator.addTradeResult(t));

      const metrics = calculator.calculateRiskMetrics();

      expect(metrics.sharpeRatio).toBeDefined();
      expect(typeof metrics.sharpeRatio).toBe('number');
    });

    it('should calculate max drawdown', () => {
      const trades = [
        createMockTrade(10),
        createMockTrade(-20), // Creates drawdown
        createMockTrade(-10),
        createMockTrade(30), // Recovery
      ];
      trades.forEach((t) => calculator.addTradeResult(t));

      const metrics = calculator.calculateRiskMetrics();

      expect(metrics.maxDrawdown).toBeGreaterThan(0);
    });

    it('should calculate recovery factor', () => {
      const trades = [createMockTrade(-10), createMockTrade(20)];
      trades.forEach((t) => calculator.addTradeResult(t));

      const metrics = calculator.calculateRiskMetrics();

      expect(metrics.recoveryFactor).toBeDefined();
    });

    it('should return default metrics for no trades', () => {
      const metrics = calculator.calculateRiskMetrics();

      expect(metrics.winRate).toBe(0.5);
      expect(metrics.avgWin).toBe(1);
      expect(metrics.avgLoss).toBe(1);
      expect(metrics.expectancy).toBe(0);
      expect(metrics.sampleSize).toBe(0);
    });
  });

  describe('calculateRiskAdjustedExpectancy', () => {
    it('should calculate risk-adjusted expectancy', () => {
      // Add some trade history
      const trades = Array.from({ length: 50 }, (_, i) =>
        createMockTrade(i % 3 === 0 ? 15 : -5)
      );
      trades.forEach((t) => calculator.addTradeResult(t));

      const marketData = generateMockMarketData('AAPL', 150);
      const expectancy = calculator.calculateRiskAdjustedExpectancy(
        'AAPL',
        marketData,
        RegimeType.MOMENTUM,
        Timeframe.H4
      );

      expect(expectancy.instrument).toBe('AAPL');
      expect(expectancy.baseExpectancy).toBeDefined();
      expect(expectancy.volatilityAdjustment).toBeDefined();
      expect(expectancy.regimeAdjustment).toBeDefined();
      expect(expectancy.finalExpectancy).toBeDefined();
      expect(expectancy.confidence).toBeGreaterThan(0);
    });

    it('should adjust for volatility', () => {
      const marketData = generateMockMarketData('AAPL', 150);
      const expectancy = calculator.calculateRiskAdjustedExpectancy(
        'AAPL',
        marketData,
        RegimeType.NEUTRAL,
        Timeframe.H4
      );

      expect(expectancy.volatilityAdjustment).toBeGreaterThanOrEqual(-0.5);
      expect(expectancy.volatilityAdjustment).toBeLessThanOrEqual(0.5);
    });

    it('should adjust for regime', () => {
      const marketData = generateMockMarketData('AAPL', 150);

      const momentumExpectancy = calculator.calculateRiskAdjustedExpectancy(
        'AAPL',
        marketData,
        RegimeType.MOMENTUM,
        Timeframe.H4
      );

      const transitionExpectancy = calculator.calculateRiskAdjustedExpectancy(
        'AAPL',
        marketData,
        RegimeType.TRANSITION,
        Timeframe.H4
      );

      expect(momentumExpectancy.regimeAdjustment).toBeDefined();
      expect(transitionExpectancy.regimeAdjustment).toBeDefined();
    });

    it('should increase confidence with more trades', () => {
      const marketData = generateMockMarketData('AAPL', 150);

      // Few trades
      const earlyExpectancy = calculator.calculateRiskAdjustedExpectancy(
        'AAPL',
        marketData,
        RegimeType.NEUTRAL,
        Timeframe.H4
      );

      // Add many trades
      const trades = Array.from({ length: 100 }, (_, i) => createMockTrade(i % 2 === 0 ? 10 : -5));
      trades.forEach((t) => calculator.addTradeResult(t));

      const lateExpectancy = calculator.calculateRiskAdjustedExpectancy(
        'AAPL',
        marketData,
        RegimeType.NEUTRAL,
        Timeframe.H4
      );

      expect(lateExpectancy.confidence).toBeGreaterThan(earlyExpectancy.confidence);
    });
  });

  describe('Regime-Specific Analysis', () => {
    it('should calculate regime-specific expectancy', () => {
      const trades = [
        createMockTrade(10, RegimeType.MOMENTUM),
        createMockTrade(15, RegimeType.MOMENTUM),
        createMockTrade(-5, RegimeType.MOMENTUM),
        createMockTrade(8, RegimeType.MEAN_REVERSION),
        createMockTrade(-3, RegimeType.MEAN_REVERSION),
      ];
      trades.forEach((t) => calculator.addTradeResult(t));

      const momentumMetrics = calculator.calculateRegimeSpecificExpectancy(
        RegimeType.MOMENTUM
      );

      expect(momentumMetrics).toBeDefined();
      expect(momentumMetrics!.sampleSize).toBe(3);
    });

    it('should return null for insufficient regime data', () => {
      const trades = [createMockTrade(10, RegimeType.MOMENTUM)];
      trades.forEach((t) => calculator.addTradeResult(t));

      const metrics = calculator.calculateRegimeSpecificExpectancy(RegimeType.MEAN_REVERSION);
      expect(metrics).toBeNull();
    });
  });

  describe('getPerformanceSummary', () => {
    it('should generate complete performance summary', () => {
      const trades = Array.from({ length: 30 }, (_, i) => {
        const regime =
          i % 3 === 0
            ? RegimeType.MOMENTUM
            : i % 3 === 1
            ? RegimeType.MEAN_REVERSION
            : RegimeType.NEUTRAL;
        return createMockTrade(i % 2 === 0 ? 10 : -5, regime);
      });
      trades.forEach((t) => calculator.addTradeResult(t));

      const summary = calculator.getPerformanceSummary();

      expect(summary.overall).toBeDefined();
      expect(summary.totalTrades).toBe(30);
      expect(summary.totalPnL).toBeDefined();
      expect(summary.byRegime.size).toBeGreaterThan(0);
    });

    it('should include all regime types with sufficient data', () => {
      const trades = [
        ...Array.from({ length: 10 }, () => createMockTrade(10, RegimeType.MOMENTUM)),
        ...Array.from({ length: 10 }, () => createMockTrade(5, RegimeType.MEAN_REVERSION)),
        ...Array.from({ length: 10 }, () => createMockTrade(8, RegimeType.NEUTRAL)),
      ];
      trades.forEach((t) => calculator.addTradeResult(t));

      const summary = calculator.getPerformanceSummary();

      expect(summary.byRegime.has(RegimeType.MOMENTUM)).toBe(true);
      expect(summary.byRegime.has(RegimeType.MEAN_REVERSION)).toBe(true);
      expect(summary.byRegime.has(RegimeType.NEUTRAL)).toBe(true);
    });
  });

  describe('Trade History Management', () => {
    it('should add trade results', () => {
      const trade = createMockTrade(10);
      calculator.addTradeResult(trade);

      const history = calculator.getTradeHistory();
      expect(history).toHaveLength(1);
      expect(history[0]).toEqual(trade);
    });

    it('should clear trade history', () => {
      const trades = [createMockTrade(10), createMockTrade(-5)];
      trades.forEach((t) => calculator.addTradeResult(t));

      calculator.clearHistory();

      const history = calculator.getTradeHistory();
      expect(history).toHaveLength(0);
    });

    it('should preserve trade order', () => {
      const trades = [createMockTrade(10), createMockTrade(-5), createMockTrade(15)];
      trades.forEach((t) => calculator.addTradeResult(t));

      const history = calculator.getTradeHistory();
      expect(history[0].pnl).toBe(10);
      expect(history[1].pnl).toBe(-5);
      expect(history[2].pnl).toBe(15);
    });
  });

  describe('Edge Cases', () => {
    it('should handle zero risk amount', () => {
      const trade: TradeResult = {
        ...createMockTrade(10),
        riskAmount: 0,
      };
      calculator.addTradeResult(trade);

      const metrics = calculator.calculateRiskMetrics();
      expect(metrics).toBeDefined();
    });

    it('should handle extremely large samples', () => {
      const trades = Array.from({ length: 1000 }, (_, i) => createMockTrade(i % 2 === 0 ? 10 : -5));
      trades.forEach((t) => calculator.addTradeResult(t));

      const metrics = calculator.calculateRiskMetrics();
      expect(metrics.sampleSize).toBe(1000);
    });

    it('should handle break-even trades', () => {
      const trades = [createMockTrade(0), createMockTrade(0), createMockTrade(0)];
      trades.forEach((t) => calculator.addTradeResult(t));

      const metrics = calculator.calculateRiskMetrics();
      expect(metrics.expectancy).toBe(0);
    });

    it('should handle very small P&L values', () => {
      const trades = [createMockTrade(0.01), createMockTrade(-0.01)];
      trades.forEach((t) => calculator.addTradeResult(t));

      const metrics = calculator.calculateRiskMetrics();
      expect(metrics).toBeDefined();
    });
  });

  describe('Statistical Confidence', () => {
    it('should have low confidence with few trades', () => {
      const trades = Array.from({ length: 5 }, () => createMockTrade(10));
      trades.forEach((t) => calculator.addTradeResult(t));

      const marketData = generateMockMarketData();
      const expectancy = calculator.calculateRiskAdjustedExpectancy(
        'AAPL',
        marketData,
        RegimeType.NEUTRAL,
        Timeframe.H4
      );

      expect(expectancy.confidence).toBeLessThan(0.5);
    });

    it('should approach max confidence with many trades', () => {
      const trades = Array.from({ length: 200 }, () => createMockTrade(10));
      trades.forEach((t) => calculator.addTradeResult(t));

      const marketData = generateMockMarketData();
      const expectancy = calculator.calculateRiskAdjustedExpectancy(
        'AAPL',
        marketData,
        RegimeType.NEUTRAL,
        Timeframe.H4
      );

      expect(expectancy.confidence).toBeCloseTo(0.95, 1);
    });
  });
});
