/**
 * ExecutionManager Tests
 *
 * Comprehensive test suite for ExecutionManager functionality
 */

import {
  ExecutionManager,
  PaperTradingVenue,
  ExecutionEventType,
  RiskLimits,
  OrderSide,
  OrderType,
  TimeInForce,
} from '../../../src/framework/execution';
import { EventType, Timeframe } from '../../../src/framework/core/types';

describe('ExecutionManager', () => {
  let venue: PaperTradingVenue;
  let executionManager: ExecutionManager;
  let riskLimits: RiskLimits;

  beforeEach(() => {
    venue = new PaperTradingVenue({
      initialCapital: 100000,
      commissionPercent: 0.001,
      slippagePercent: 0.001,
      fillDelay: 10,
    });

    riskLimits = {
      maxPositionSize: 1000,
      maxOrderValue: 50000,
      maxDailyOrders: 100,
      maxOpenPositions: 10,
      maxLeverage: 1,
      maxDrawdown: 0.2,
      minAccountBalance: 10000,
    };

    executionManager = new ExecutionManager({
      venue,
      riskLimits,
      autoExecute: true,
      autoStopLoss: true,
      reconciliationInterval: 0, // Disable auto-reconciliation in tests
      enableLogging: false,
    });
  });

  afterEach(() => {
    if (executionManager) {
      executionManager.stop();
    }
  });

  describe('Initialization', () => {
    it('should initialize with correct configuration', () => {
      expect(executionManager).toBeDefined();
      expect(executionManager.getRouter()).toBeDefined();
      expect(executionManager.getPositionManager()).toBeDefined();
    });

    it('should start and stop successfully', () => {
      expect(() => executionManager.start()).not.toThrow();
      expect(() => executionManager.stop()).not.toThrow();
    });

    it('should throw error when starting already active manager', () => {
      executionManager.start();
      expect(() => executionManager.start()).toThrow();
    });

    it('should throw error when stopping inactive manager', () => {
      expect(() => executionManager.stop()).toThrow();
    });
  });

  describe('Order Submission', () => {
    beforeEach(() => {
      executionManager.start();
      venue.setMarketPrice('AAPL', 150.0);
    });

    it('should submit market order successfully', async () => {
      const order = await executionManager.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
        timeInForce: TimeInForce.GTC,
      });

      expect(order).toBeDefined();
      expect(order.instrument).toBe('AAPL');
      expect(order.side).toBe(OrderSide.BUY);
      expect(order.quantity).toBe(100);
    });

    it('should reject order exceeding position size limit', async () => {
      await expect(
        executionManager.submitOrder({
          instrument: 'AAPL',
          side: OrderSide.BUY,
          type: OrderType.MARKET,
          quantity: 2000, // Exceeds maxPositionSize
        })
      ).rejects.toThrow();
    });

    it('should reject order exceeding order value limit', async () => {
      await expect(
        executionManager.submitOrder({
          instrument: 'AAPL',
          side: OrderSide.BUY,
          type: OrderType.MARKET,
          quantity: 500, // 500 * 150 = 75000 > 50000
        })
      ).rejects.toThrow();
    });

    it('should emit ORDER_SUBMITTED event', (done) => {
      executionManager.on(ExecutionEventType.ORDER_SUBMITTED, (event) => {
        expect(event.instrument).toBe('AAPL');
        done();
      });

      executionManager.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
      });
    });
  });

  describe('Order Fills', () => {
    beforeEach(() => {
      executionManager.start();
      venue.setMarketPrice('AAPL', 150.0);
    });

    it('should emit ORDER_FILLED event when order fills', (done) => {
      executionManager.on(ExecutionEventType.ORDER_FILLED, (event) => {
        expect(event.instrument).toBe('AAPL');
        expect(event.data.filledQuantity).toBe(100);
        done();
      });

      executionManager.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
        metadata: { signal: 'entry' },
      });
    }, 1000);

    it('should open position when entry order fills', (done) => {
      executionManager.on(ExecutionEventType.POSITION_OPENED, (event) => {
        expect(event.instrument).toBe('AAPL');
        const position = executionManager.getPosition('AAPL');
        expect(position).toBeDefined();
        expect(position!.quantity).toBe(100);
        done();
      });

      executionManager.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
        metadata: { signal: 'entry' },
      });
    }, 1000);

    it('should update statistics after fill', async () => {
      await executionManager.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
        metadata: { signal: 'entry' },
      });

      await new Promise((resolve) => setTimeout(resolve, 100));

      const stats = executionManager.getStats();
      expect(stats.totalOrders).toBeGreaterThan(0);
      expect(stats.filledOrders).toBeGreaterThan(0);
    });
  });

  describe('Position Management', () => {
    beforeEach(async () => {
      executionManager.start();
      venue.setMarketPrice('AAPL', 150.0);

      // Open position
      await executionManager.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
        metadata: { signal: 'entry' },
      });

      await new Promise((resolve) => setTimeout(resolve, 100));
    });

    it('should track open positions', () => {
      const positions = executionManager.getPositions();
      expect(positions.length).toBe(1);
      expect(positions[0].instrument).toBe('AAPL');
    });

    it('should get specific position', () => {
      const position = executionManager.getPosition('AAPL');
      expect(position).toBeDefined();
      expect(position!.instrument).toBe('AAPL');
      expect(position!.quantity).toBe(100);
    });

    it('should update position with market data', async () => {
      venue.setMarketPrice('AAPL', 155.0);

      await executionManager.updatePosition('AAPL', {
        instrument: 'AAPL',
        bars: [],
        currentPrice: 155.0,
        lastUpdate: new Date(),
      });

      const position = executionManager.getPosition('AAPL');
      expect(position!.currentPrice).toBe(155.0);
      expect(position!.unrealizedPnL).toBeGreaterThan(0);
    });

    it('should close position when exit order fills', async (done) => {
      executionManager.on(ExecutionEventType.POSITION_CLOSED, (event) => {
        expect(event.instrument).toBe('AAPL');
        const position = executionManager.getPosition('AAPL');
        expect(position).toBeNull();
        done();
      });

      await executionManager.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.SELL,
        type: OrderType.MARKET,
        quantity: 100,
        metadata: { signal: 'exit' },
      });
    }, 1000);
  });

  describe('Framework Signal Handling', () => {
    beforeEach(() => {
      executionManager.start();
      venue.setMarketPrice('AAPL', 150.0);
    });

    it('should handle entry signal when autoExecute enabled', async () => {
      const entrySignal = {
        type: EventType.ENTRY_SIGNAL,
        timestamp: new Date(),
        instrument: 'AAPL',
        data: {
          instrument: 'AAPL',
          direction: 'long',
          price: 150.0,
          quantity: 100,
          stopLoss: { currentStop: 145.0 },
          metadata: { signal: 'entry' },
        },
        severity: 'medium' as const,
        message: 'Entry signal generated',
      };

      await executionManager.handleEntrySignal(entrySignal);

      await new Promise((resolve) => setTimeout(resolve, 100));

      const position = executionManager.getPosition('AAPL');
      expect(position).toBeDefined();
    });

    it('should handle exit signal', async () => {
      // First open a position
      await executionManager.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
        metadata: { signal: 'entry' },
      });

      await new Promise((resolve) => setTimeout(resolve, 100));

      // Then send exit signal
      const exitSignal = {
        type: EventType.EXIT_SIGNAL,
        timestamp: new Date(),
        instrument: 'AAPL',
        data: {
          instrument: 'AAPL',
          reason: 'stop_hit',
          price: 145.0,
        },
        severity: 'medium' as const,
        message: 'Exit signal generated',
      };

      await executionManager.handleExitSignal(exitSignal);

      await new Promise((resolve) => setTimeout(resolve, 100));

      const position = executionManager.getPosition('AAPL');
      expect(position).toBeNull();
    });
  });

  describe('Event Emission', () => {
    beforeEach(() => {
      executionManager.start();
      venue.setMarketPrice('AAPL', 150.0);
    });

    it('should allow subscribing to execution events', (done) => {
      let eventReceived = false;

      executionManager.on(ExecutionEventType.ORDER_SUBMITTED, () => {
        eventReceived = true;
      });

      executionManager.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
      });

      setTimeout(() => {
        expect(eventReceived).toBe(true);
        done();
      }, 50);
    });

    it('should allow unsubscribing from events', (done) => {
      let eventCount = 0;
      const handler = () => {
        eventCount++;
      };

      executionManager.on(ExecutionEventType.ORDER_SUBMITTED, handler);

      executionManager.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 50,
      });

      setTimeout(() => {
        executionManager.off(ExecutionEventType.ORDER_SUBMITTED, handler);

        executionManager.submitOrder({
          instrument: 'AAPL',
          side: OrderSide.BUY,
          type: OrderType.MARKET,
          quantity: 50,
        });

        setTimeout(() => {
          expect(eventCount).toBe(1);
          done();
        }, 50);
      }, 50);
    });
  });

  describe('Statistics', () => {
    beforeEach(() => {
      executionManager.start();
      venue.setMarketPrice('AAPL', 150.0);
    });

    it('should track order statistics', async () => {
      await executionManager.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
      });

      await new Promise((resolve) => setTimeout(resolve, 100));

      const stats = executionManager.getStats();
      expect(stats.totalOrders).toBeGreaterThan(0);
      expect(stats.fillRate).toBeGreaterThan(0);
    });

    it('should reset statistics', async () => {
      await executionManager.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
      });

      await new Promise((resolve) => setTimeout(resolve, 100));

      executionManager.resetStats();

      const stats = executionManager.getStats();
      expect(stats.totalOrders).toBe(0);
      expect(stats.filledOrders).toBe(0);
    });
  });

  describe('Error Handling', () => {
    beforeEach(() => {
      executionManager.start();
      venue.setMarketPrice('AAPL', 150.0);
    });

    it('should emit error event for invalid orders', (done) => {
      executionManager.on(ExecutionEventType.EXECUTION_ERROR, (event) => {
        expect(event.severity).toBe('error');
        done();
      });

      // Try to submit invalid order
      executionManager.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 10000, // Exceeds limits
      }).catch(() => {
        // Expected to fail
      });
    });

    it('should handle missing position gracefully', async () => {
      const exitSignal = {
        type: EventType.EXIT_SIGNAL,
        timestamp: new Date(),
        instrument: 'NONEXISTENT',
        data: {
          instrument: 'NONEXISTENT',
          reason: 'test',
          price: 100,
        },
        severity: 'medium' as const,
        message: 'Exit signal',
      };

      // Should not throw
      await expect(
        executionManager.handleExitSignal(exitSignal)
      ).resolves.not.toThrow();
    });
  });
});
