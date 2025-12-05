/**
 * Unit tests for Capital Allocation Engine
 */

import { AllocationEngine } from '../../../src/framework/capital-allocation/AllocationEngine';
import {
  AllocationParameters,
  CompositeScore,
  Position,
  AdaptiveStopLoss,
} from '../../../src/framework/core/types';
import { generateMockMarketData } from '../mocks/marketData';

describe('AllocationEngine', () => {
  let engine: AllocationEngine;
  let params: AllocationParameters;

  beforeEach(() => {
    params = {
      totalCapital: 100000,
      maxRiskPerTrade: 0.01,
      maxTotalRisk: 0.05,
      maxPositions: 8,
      minScore: 0.6,
      diversificationRules: {
        maxPerSector: 0.3,
        maxCorrelatedPositions: 3,
      },
    };

    engine = new AllocationEngine(params);
  });

  const createMockScore = (instrument: string, score: number): CompositeScore => ({
    instrument,
    totalScore: score,
    factors: [],
    timestamp: new Date(),
  });

  const createMockStopLoss = (stopPrice: number): AdaptiveStopLoss => ({
    initialStop: stopPrice,
    currentStop: stopPrice,
    percentileBased: {
      value: 2,
      percentile: 95,
      lookbackPeriod: 100,
      timeframe: 'H4' as any,
    },
    riskAmount: 1000,
    timestamp: new Date(),
  });

  describe('allocateCapital', () => {
    it('should allocate capital to top scoring instruments', () => {
      const scores = [
        createMockScore('AAPL', 0.9),
        createMockScore('GOOGL', 0.85),
        createMockScore('MSFT', 0.8),
      ];

      const marketDataMap = new Map([
        ['AAPL', generateMockMarketData('AAPL', 150)],
        ['GOOGL', generateMockMarketData('GOOGL', 150)],
        ['MSFT', generateMockMarketData('MSFT', 150)],
      ]);

      const stopLossMap = new Map([
        ['AAPL', createMockStopLoss(98)],
        ['GOOGL', createMockStopLoss(98)],
        ['MSFT', createMockStopLoss(98)],
      ]);

      const constraints = {
        currentPositions: [],
        availableCapital: 100000,
        currentRiskExposure: 0,
      };

      const result = engine.allocateCapital(scores, constraints, marketDataMap, stopLossMap);

      expect(result.decisions.length).toBeGreaterThan(0);
      expect(result.totalAllocated).toBeGreaterThan(0);
      expect(result.totalRisk).toBeLessThanOrEqual(params.maxTotalRisk * params.totalCapital);
    });

    it('should respect minimum score threshold', () => {
      const scores = [
        createMockScore('AAPL', 0.9),
        createMockScore('GOOGL', 0.5), // Below min score
        createMockScore('MSFT', 0.7),
      ];

      const marketDataMap = new Map([
        ['AAPL', generateMockMarketData('AAPL', 150)],
        ['GOOGL', generateMockMarketData('GOOGL', 150)],
        ['MSFT', generateMockMarketData('MSFT', 150)],
      ]);

      const stopLossMap = new Map([
        ['AAPL', createMockStopLoss(98)],
        ['GOOGL', createMockStopLoss(98)],
        ['MSFT', createMockStopLoss(98)],
      ]);

      const constraints = {
        currentPositions: [],
        availableCapital: 100000,
        currentRiskExposure: 0,
      };

      const result = engine.allocateCapital(scores, constraints, marketDataMap, stopLossMap);

      const googleAllocation = result.decisions.find((d) => d.instrument === 'GOOGL');
      expect(googleAllocation).toBeUndefined();
    });

    it('should respect maximum positions limit', () => {
      const scores = Array.from({ length: 15 }, (_, i) =>
        createMockScore(`INST${i}`, 0.9 - i * 0.01)
      );

      const marketDataMap = new Map(
        scores.map((s) => [s.instrument, generateMockMarketData(s.instrument, 150)])
      );

      const stopLossMap = new Map(
        scores.map((s) => [s.instrument, createMockStopLoss(98)])
      );

      const constraints = {
        currentPositions: [],
        availableCapital: 100000,
        currentRiskExposure: 0,
      };

      const result = engine.allocateCapital(scores, constraints, marketDataMap, stopLossMap);

      expect(result.decisions.length).toBeLessThanOrEqual(params.maxPositions);
    });

    it('should not exceed total risk limit', () => {
      const scores = Array.from({ length: 5 }, (_, i) =>
        createMockScore(`INST${i}`, 0.9)
      );

      const marketDataMap = new Map(
        scores.map((s) => [s.instrument, generateMockMarketData(s.instrument, 150)])
      );

      const stopLossMap = new Map(
        scores.map((s) => [s.instrument, createMockStopLoss(95)]) // Wide stop = more risk
      );

      const constraints = {
        currentPositions: [],
        availableCapital: 100000,
        currentRiskExposure: 0,
      };

      const result = engine.allocateCapital(scores, constraints, marketDataMap, stopLossMap);

      expect(result.totalRisk).toBeLessThanOrEqual(params.maxTotalRisk * params.totalCapital);
    });

    it('should skip existing positions', () => {
      const scores = [createMockScore('AAPL', 0.9), createMockScore('GOOGL', 0.85)];

      const existingPosition: Position = {
        instrument: 'AAPL',
        direction: 'long',
        entryPrice: 100,
        currentPrice: 105,
        quantity: 100,
        positionValue: 10500,
        unrealizedPnL: 500,
        riskAmount: 1000,
        stopLoss: createMockStopLoss(98),
        compositeScore: createMockScore('AAPL', 0.9),
        openedAt: new Date(),
        timeframe: 'H4' as any,
      };

      const marketDataMap = new Map([
        ['AAPL', generateMockMarketData('AAPL', 150)],
        ['GOOGL', generateMockMarketData('GOOGL', 150)],
      ]);

      const stopLossMap = new Map([
        ['AAPL', createMockStopLoss(98)],
        ['GOOGL', createMockStopLoss(98)],
      ]);

      const constraints = {
        currentPositions: [existingPosition],
        availableCapital: 89500,
        currentRiskExposure: 1000,
      };

      const result = engine.allocateCapital(scores, constraints, marketDataMap, stopLossMap);

      const aaplAllocation = result.decisions.find((d) => d.instrument === 'AAPL');
      expect(aaplAllocation).toBeUndefined();
    });

    it('should assign priority based on rank', () => {
      const scores = [
        createMockScore('AAPL', 0.95),
        createMockScore('GOOGL', 0.90),
        createMockScore('MSFT', 0.85),
      ];

      const marketDataMap = new Map(
        scores.map((s) => [s.instrument, generateMockMarketData(s.instrument, 150)])
      );

      const stopLossMap = new Map(
        scores.map((s) => [s.instrument, createMockStopLoss(98)])
      );

      const constraints = {
        currentPositions: [],
        availableCapital: 100000,
        currentRiskExposure: 0,
      };

      const result = engine.allocateCapital(scores, constraints, marketDataMap, stopLossMap);

      const priorities = result.decisions.map((d) => d.priority);
      expect(priorities).toEqual(priorities.slice().sort((a, b) => a - b));
    });

    it('should handle insufficient capital gracefully', () => {
      const scores = [createMockScore('AAPL', 0.9)];

      const marketDataMap = new Map([
        ['AAPL', generateMockMarketData('AAPL', 150)],
      ]);

      const stopLossMap = new Map([['AAPL', createMockStopLoss(98)]]);

      const constraints = {
        currentPositions: [],
        availableCapital: 100, // Very limited capital
        currentRiskExposure: 0,
      };

      const result = engine.allocateCapital(scores, constraints, marketDataMap, stopLossMap);

      // Should either scale down or reject
      expect(result).toBeDefined();
    });

    it('should provide rejection reasons', () => {
      const scores = [
        createMockScore('AAPL', 0.9),
        createMockScore('GOOGL', 0.5), // Below min score
      ];

      const marketDataMap = new Map([
        ['AAPL', generateMockMarketData('AAPL', 150)],
        ['GOOGL', generateMockMarketData('GOOGL', 150)],
      ]);

      const stopLossMap = new Map([
        ['AAPL', createMockStopLoss(98)],
        ['GOOGL', createMockStopLoss(98)],
      ]);

      const constraints = {
        currentPositions: [],
        availableCapital: 100000,
        currentRiskExposure: 0,
      };

      const result = engine.allocateCapital(scores, constraints, marketDataMap, stopLossMap);

      expect(result.rejectedInstruments.length).toBeGreaterThan(0);
      const googleRejection = result.rejectedInstruments.find((r) => r.instrument === 'GOOGL');
      expect(googleRejection).toBeDefined();
      expect(googleRejection!.reason).toBeDefined();
    });
  });

  describe('rebalancePortfolio', () => {
    it('should close positions below minimum score', () => {
      const positions: Position[] = [
        {
          instrument: 'AAPL',
          direction: 'long',
          entryPrice: 100,
          currentPrice: 105,
          quantity: 100,
          positionValue: 10500,
          unrealizedPnL: 500,
          riskAmount: 1000,
          stopLoss: createMockStopLoss(98),
          compositeScore: createMockScore('AAPL', 0.9),
          openedAt: new Date(),
          timeframe: 'H4' as any,
        },
      ];

      const newScores = [
        createMockScore('AAPL', 0.5), // Score dropped below minimum
      ];

      const rebalance = engine.rebalancePortfolio(positions, newScores, 100000);

      expect(rebalance.closePositions).toContain('AAPL');
    });

    it('should keep positions above minimum score', () => {
      const positions: Position[] = [
        {
          instrument: 'AAPL',
          direction: 'long',
          entryPrice: 100,
          currentPrice: 105,
          quantity: 100,
          positionValue: 10500,
          unrealizedPnL: 500,
          riskAmount: 1000,
          stopLoss: createMockStopLoss(98),
          compositeScore: createMockScore('AAPL', 0.9),
          openedAt: new Date(),
          timeframe: 'H4' as any,
        },
      ];

      const newScores = [
        createMockScore('AAPL', 0.8), // Still above minimum
      ];

      const rebalance = engine.rebalancePortfolio(positions, newScores, 100000);

      expect(rebalance.closePositions).not.toContain('AAPL');
    });
  });

  describe('calculatePortfolioMetrics', () => {
    it('should calculate portfolio metrics', () => {
      const positions: Position[] = [
        {
          instrument: 'AAPL',
          direction: 'long',
          entryPrice: 100,
          currentPrice: 105,
          quantity: 100,
          positionValue: 10500,
          unrealizedPnL: 500,
          riskAmount: 1000,
          stopLoss: createMockStopLoss(98),
          compositeScore: createMockScore('AAPL', 0.9),
          openedAt: new Date(),
          timeframe: 'H4' as any,
        },
        {
          instrument: 'GOOGL',
          direction: 'long',
          entryPrice: 200,
          currentPrice: 210,
          quantity: 50,
          positionValue: 10500,
          unrealizedPnL: 500,
          riskAmount: 1000,
          stopLoss: createMockStopLoss(195),
          compositeScore: createMockScore('GOOGL', 0.85),
          openedAt: new Date(),
          timeframe: 'H4' as any,
        },
      ];

      const metrics = engine.calculatePortfolioMetrics(positions);

      expect(metrics.totalValue).toBe(21000);
      expect(metrics.totalRisk).toBe(2000);
      expect(metrics.riskPercentage).toBeCloseTo(2, 1);
      expect(metrics.utilizationPercentage).toBeCloseTo(25, 1); // 2 out of 8 positions
      expect(metrics.averageScore).toBeCloseTo(0.875, 2);
    });

    it('should handle empty portfolio', () => {
      const metrics = engine.calculatePortfolioMetrics([]);

      expect(metrics.totalValue).toBe(0);
      expect(metrics.totalRisk).toBe(0);
      expect(metrics.averageScore).toBe(0);
    });
  });

  describe('Parameter Updates', () => {
    it('should update allocation parameters', () => {
      engine.updateParameters({ maxRiskPerTrade: 0.02 });

      const updatedParams = engine.getParameters();
      expect(updatedParams.maxRiskPerTrade).toBe(0.02);
    });

    it('should preserve other parameters when updating', () => {
      const originalCapital = params.totalCapital;
      engine.updateParameters({ maxRiskPerTrade: 0.02 });

      const updatedParams = engine.getParameters();
      expect(updatedParams.totalCapital).toBe(originalCapital);
    });
  });

  describe('Edge Cases', () => {
    it('should handle zero available capital', () => {
      const scores = [createMockScore('AAPL', 0.9)];
      const marketDataMap = new Map([['AAPL', generateMockMarketData('AAPL', 150)]]);
      const stopLossMap = new Map([['AAPL', createMockStopLoss(98)]]);

      const constraints = {
        currentPositions: [],
        availableCapital: 0,
        currentRiskExposure: 0,
      };

      const result = engine.allocateCapital(scores, constraints, marketDataMap, stopLossMap);

      expect(result.decisions).toHaveLength(0);
    });

    it('should handle maximum risk already used', () => {
      const scores = [createMockScore('AAPL', 0.9)];
      const marketDataMap = new Map([['AAPL', generateMockMarketData('AAPL', 150)]]);
      const stopLossMap = new Map([['AAPL', createMockStopLoss(98)]]);

      const constraints = {
        currentPositions: [],
        availableCapital: 100000,
        currentRiskExposure: params.maxTotalRisk * params.totalCapital, // Max risk used
      };

      const result = engine.allocateCapital(scores, constraints, marketDataMap, stopLossMap);

      expect(result.decisions).toHaveLength(0);
    });

    it('should handle missing market data', () => {
      const scores = [createMockScore('AAPL', 0.9)];
      const marketDataMap = new Map(); // Empty
      const stopLossMap = new Map([['AAPL', createMockStopLoss(98)]]);

      const constraints = {
        currentPositions: [],
        availableCapital: 100000,
        currentRiskExposure: 0,
      };

      const result = engine.allocateCapital(scores, constraints, marketDataMap, stopLossMap);

      expect(result.decisions).toHaveLength(0);
      expect(result.rejectedInstruments.some((r) => r.instrument === 'AAPL')).toBe(true);
    });
  });
});
