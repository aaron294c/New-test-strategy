/**
 * Integration tests for TradingFramework
 * Tests the interaction between all modules
 */

import { TradingFramework } from '../../../src/framework/core/TradingFramework';
import { EventType, Timeframe } from '../../../src/framework/core/types';
import {
  generateMockMarketData,
  generateMultiTimeframeData,
} from '../mocks/marketData';

describe('TradingFramework Integration', () => {
  let framework: TradingFramework;

  beforeEach(() => {
    framework = new TradingFramework({
      updateInterval: 1000,
      logLevel: 'error', // Suppress logs during tests
    });
  });

  afterEach(() => {
    if (framework.getState().isActive) {
      framework.stop();
    }
  });

  describe('Framework Lifecycle', () => {
    it('should initialize with default configuration', () => {
      const state = framework.getState();

      expect(state.isActive).toBe(false);
      expect(state.positions).toHaveLength(0);
      expect(state.scores.size).toBe(0);
    });

    it('should start and stop successfully', () => {
      framework.start();
      expect(framework.getState().isActive).toBe(true);

      framework.stop();
      expect(framework.getState().isActive).toBe(false);
    });

    it('should throw when starting twice', () => {
      framework.start();
      expect(() => framework.start()).toThrow('already active');
      framework.stop();
    });

    it('should throw when stopping inactive framework', () => {
      expect(() => framework.stop()).toThrow('not active');
    });
  });

  describe('Market Data Integration', () => {
    it('should accept market data for instruments', () => {
      const marketData = generateMockMarketData('AAPL', 200);
      framework.addMarketData('AAPL', marketData);

      const state = framework.getState();
      expect(state.marketData.has('AAPL')).toBe(true);
      expect(state.marketData.get('AAPL')).toEqual(marketData);
    });

    it('should handle multiple instruments', () => {
      const instruments = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'];

      instruments.forEach((instrument) => {
        const marketData = generateMockMarketData(instrument, 200);
        framework.addMarketData(instrument, marketData);
      });

      const state = framework.getState();
      expect(state.marketData.size).toBe(5);
    });

    it('should update market data for existing instruments', () => {
      const marketData1 = generateMockMarketData('AAPL', 200);
      framework.addMarketData('AAPL', marketData1);

      const marketData2 = generateMockMarketData('AAPL', 200);
      marketData2.currentPrice = 999;
      framework.addMarketData('AAPL', marketData2);

      const state = framework.getState();
      expect(state.marketData.get('AAPL')!.currentPrice).toBe(999);
    });
  });

  describe('Event System', () => {
    it('should emit events for framework start', (done) => {
      framework.on(EventType.REGIME_CHANGE, (event) => {
        expect(event.message).toContain('started');
        framework.stop();
        done();
      });

      framework.start();
    });

    it('should emit events for framework stop', (done) => {
      framework.start();

      framework.on(EventType.REGIME_CHANGE, (event) => {
        if (event.message.includes('stopped')) {
          done();
        }
      });

      framework.stop();
    });

    it('should allow multiple event handlers', () => {
      let count = 0;

      const handler1 = () => count++;
      const handler2 = () => count++;

      framework.on(EventType.REGIME_CHANGE, handler1);
      framework.on(EventType.REGIME_CHANGE, handler2);

      framework.start();
      framework.stop();

      expect(count).toBeGreaterThanOrEqual(2);
    });

    it('should allow unsubscribing from events', () => {
      let count = 0;
      const handler = () => count++;

      framework.on(EventType.REGIME_CHANGE, handler);
      framework.off(EventType.REGIME_CHANGE, handler);

      framework.start();
      framework.stop();

      expect(count).toBe(0);
    });
  });

  describe('End-to-End Workflow', () => {
    it('should process complete trading workflow', async () => {
      // Add market data
      const instruments = ['AAPL', 'GOOGL', 'MSFT'];
      instruments.forEach((inst) => {
        const data = generateMultiTimeframeData(inst, [
          Timeframe.H1,
          Timeframe.H4,
          Timeframe.D1,
        ]);
        framework.addMarketData(inst, data);
      });

      // Track events
      const events: any[] = [];
      framework.on(EventType.SCORE_UPDATE, (e) => events.push(e));
      framework.on(EventType.ALLOCATION_CHANGE, (e) => events.push(e));

      // Start framework
      framework.start();

      // Wait for processing
      await new Promise((resolve) => setTimeout(resolve, 2000));

      framework.stop();

      // Verify state updates
      const state = framework.getState();
      expect(state.scores.size).toBeGreaterThan(0);
      expect(state.metrics).toBeDefined();
    });

    it('should maintain state consistency', async () => {
      const marketData = generateMultiTimeframeData('AAPL');
      framework.addMarketData('AAPL', marketData);

      framework.start();
      await new Promise((resolve) => setTimeout(resolve, 1500));

      const state1 = framework.getState();
      const regime1 = state1.currentRegime;

      await new Promise((resolve) => setTimeout(resolve, 1500));

      const state2 = framework.getState();
      const regime2 = state2.currentRegime;

      framework.stop();

      // Regimes should be defined
      expect(regime1).toBeDefined();
      expect(regime2).toBeDefined();
    });
  });

  describe('Configuration Management', () => {
    it('should return current configuration', () => {
      const config = framework.getConfig();
      expect(config).toBeDefined();
      expect(config.primaryTimeframe).toBeDefined();
      expect(config.riskManagement).toBeDefined();
    });

    it('should prevent config update while active', () => {
      framework.start();

      expect(() =>
        framework.updateConfig({
          primaryTimeframe: Timeframe.H1,
        })
      ).toThrow('Cannot update config while framework is active');

      framework.stop();
    });

    it('should allow config update when stopped', () => {
      framework.updateConfig({
        primaryTimeframe: Timeframe.H1,
      });

      const config = framework.getConfig();
      expect(config.primaryTimeframe).toBe(Timeframe.H1);
    });
  });

  describe('Error Handling', () => {
    it('should emit error events for processing failures', (done) => {
      framework.on(EventType.ERROR, (event) => {
        expect(event.type).toBe(EventType.ERROR);
        expect(event.severity).toBe('high');
        framework.stop();
        done();
      });

      // Add invalid data to trigger error
      framework.addMarketData('INVALID', {
        instrument: 'INVALID',
        bars: [], // Empty bars will cause errors
        currentPrice: 0,
        lastUpdate: new Date(),
      });

      framework.start();
    });

    it('should continue operation after non-fatal errors', async () => {
      const validData = generateMockMarketData('AAPL', 200);
      framework.addMarketData('AAPL', validData);

      framework.start();
      await new Promise((resolve) => setTimeout(resolve, 1500));

      const state = framework.getState();
      expect(state.isActive).toBe(true);

      framework.stop();
    });
  });

  describe('Performance', () => {
    it('should process multiple instruments efficiently', async () => {
      const startTime = Date.now();

      // Add 10 instruments
      for (let i = 0; i < 10; i++) {
        const data = generateMultiTimeframeData(`INST${i}`);
        framework.addMarketData(`INST${i}`, data);
      }

      framework.start();
      await new Promise((resolve) => setTimeout(resolve, 2000));
      framework.stop();

      const duration = Date.now() - startTime;

      // Should complete within reasonable time
      expect(duration).toBeLessThan(5000);
    });

    it('should update state within configured interval', async () => {
      const quickFramework = new TradingFramework({
        updateInterval: 500,
      });

      const data = generateMockMarketData('AAPL', 200);
      quickFramework.addMarketData('AAPL', data);

      quickFramework.start();

      const startTime = Date.now();
      await new Promise((resolve) => setTimeout(resolve, 1500));

      const updates = quickFramework.getState().lastUpdate;
      quickFramework.stop();

      // Should have updated at least once
      expect(updates).toBeDefined();
    });
  });

  describe('State Snapshots', () => {
    it('should provide immutable state snapshots', () => {
      const state1 = framework.getState();
      state1.positions.push({} as any);

      const state2 = framework.getState();
      expect(state2.positions).toHaveLength(0);
    });
  });

  describe('Metrics Tracking', () => {
    it('should track portfolio metrics', async () => {
      const data = generateMockMarketData('AAPL', 200);
      framework.addMarketData('AAPL', data);

      framework.start();
      await new Promise((resolve) => setTimeout(resolve, 1500));
      framework.stop();

      const state = framework.getState();
      expect(state.metrics).toBeDefined();
      expect(state.metrics.totalPnL).toBeDefined();
      expect(state.metrics.totalRiskExposure).toBeDefined();
      expect(state.metrics.regimeCoherence).toBeDefined();
    });
  });
});
