/**
 * PaperTradingVenue Tests
 *
 * Test suite for paper trading venue implementation
 */

import {
  PaperTradingVenue,
  OrderSide,
  OrderType,
  OrderStatus,
  TimeInForce,
} from '../../../src/framework/execution';

describe('PaperTradingVenue', () => {
  let venue: PaperTradingVenue;

  beforeEach(() => {
    venue = new PaperTradingVenue({
      initialCapital: 100000,
      commission: 0.01,
      commissionPercent: 0.001,
      slippagePercent: 0.001,
      fillDelay: 10,
      rejectRate: 0,
      partialFillRate: 0,
    });
  });

  describe('Initialization', () => {
    it('should initialize with correct capital', async () => {
      const balance = await venue.getAccountBalance();
      expect(balance.cash).toBe(100000);
      expect(balance.equity).toBe(100000);
      expect(balance.buyingPower).toBe(100000);
    });

    it('should have correct venue properties', () => {
      expect(venue.name).toBe('Paper Trading');
      expect(venue.type).toBe('paper');
    });
  });

  describe('Market Prices', () => {
    it('should generate random price if not set', async () => {
      const price = await venue.getCurrentPrice('AAPL');
      expect(price).toBeGreaterThan(0);
      expect(price).toBeLessThan(1010);
    });

    it('should allow setting market price', async () => {
      venue.setMarketPrice('AAPL', 150.0);
      const price = await venue.getCurrentPrice('AAPL');
      expect(price).toBeCloseTo(150.0, 1);
    });

    it('should simulate price movement', async () => {
      venue.setMarketPrice('AAPL', 150.0);
      const price1 = await venue.getCurrentPrice('AAPL');
      const price2 = await venue.getCurrentPrice('AAPL');

      // Prices should be different due to random walk
      expect(price1).not.toBe(price2);
    });
  });

  describe('Market Orders', () => {
    beforeEach(() => {
      venue.setMarketPrice('AAPL', 150.0);
    });

    it('should submit market order successfully', async () => {
      const order = await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
      });

      expect(order.instrument).toBe('AAPL');
      expect(order.side).toBe(OrderSide.BUY);
      expect(order.quantity).toBe(100);
      expect(order.status).toBe(OrderStatus.PENDING);
    });

    it('should fill market order after delay', async () => {
      const order = await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
      });

      await new Promise((resolve) => setTimeout(resolve, 50));

      const filledOrder = await venue.getOrder(order.id);
      expect(filledOrder.status).toBe(OrderStatus.FILLED);
      expect(filledOrder.filledQuantity).toBe(100);
    });

    it('should apply slippage to market orders', async () => {
      const order = await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
      });

      await new Promise((resolve) => setTimeout(resolve, 50));

      const filledOrder = await venue.getOrder(order.id);

      // Buy orders should have slippage above current price
      expect(filledOrder.averageFillPrice).toBeGreaterThan(150.0);
    });

    it('should calculate commission correctly', async () => {
      const order = await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
      });

      await new Promise((resolve) => setTimeout(resolve, 50));

      const filledOrder = await venue.getOrder(order.id);
      expect(filledOrder.fills.length).toBeGreaterThan(0);

      const totalCommission = filledOrder.fills.reduce(
        (sum, fill) => sum + fill.commission,
        0
      );
      expect(totalCommission).toBeGreaterThan(0);
    });
  });

  describe('Limit Orders', () => {
    beforeEach(() => {
      venue.setMarketPrice('AAPL', 150.0);
    });

    it('should submit limit order successfully', async () => {
      const order = await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.LIMIT,
        quantity: 100,
        price: 145.0,
      });

      expect(order.type).toBe(OrderType.LIMIT);
      expect(order.price).toBe(145.0);
    });

    it('should fill limit buy order when price drops', async () => {
      const order = await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.LIMIT,
        quantity: 100,
        price: 145.0,
      });

      // Set price below limit
      venue.setMarketPrice('AAPL', 144.0);

      await new Promise((resolve) => setTimeout(resolve, 50));

      const filledOrder = await venue.getOrder(order.id);
      expect(filledOrder.status).toBe(OrderStatus.FILLED);
    });

    it('should not fill limit buy order when price too high', async () => {
      const order = await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.LIMIT,
        quantity: 100,
        price: 145.0,
      });

      await new Promise((resolve) => setTimeout(resolve, 50));

      const pendingOrder = await venue.getOrder(order.id);
      expect(pendingOrder.status).toBe(OrderStatus.PENDING);
    });
  });

  describe('Stop Orders', () => {
    beforeEach(() => {
      venue.setMarketPrice('AAPL', 150.0);
    });

    it('should submit stop-loss order successfully', async () => {
      const order = await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.SELL,
        type: OrderType.STOP_LOSS,
        quantity: 100,
        stopPrice: 145.0,
      });

      expect(order.type).toBe(OrderType.STOP_LOSS);
      expect(order.stopPrice).toBe(145.0);
    });

    it('should trigger stop-loss when price falls', async () => {
      const order = await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.SELL,
        type: OrderType.STOP_LOSS,
        quantity: 100,
        stopPrice: 145.0,
      });

      // Set price below stop
      venue.setMarketPrice('AAPL', 144.0);

      await new Promise((resolve) => setTimeout(resolve, 50));

      const filledOrder = await venue.getOrder(order.id);
      expect(filledOrder.status).toBe(OrderStatus.FILLED);
    });
  });

  describe('Position Management', () => {
    beforeEach(() => {
      venue.setMarketPrice('AAPL', 150.0);
    });

    it('should create position after buy order fills', async () => {
      await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
      });

      await new Promise((resolve) => setTimeout(resolve, 50));

      const positions = await venue.getPositions();
      expect(positions.length).toBe(1);
      expect(positions[0].instrument).toBe('AAPL');
      expect(positions[0].quantity).toBe(100);
    });

    it('should update position value with price changes', async () => {
      await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
      });

      await new Promise((resolve) => setTimeout(resolve, 50));

      venue.setMarketPrice('AAPL', 155.0);
      const positions = await venue.getPositions();

      expect(positions[0].currentPrice).toBeGreaterThan(150.0);
      expect(positions[0].unrealizedPnL).toBeGreaterThan(0);
    });

    it('should close position when full quantity sold', async () => {
      await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
      });

      await new Promise((resolve) => setTimeout(resolve, 50));

      await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.SELL,
        type: OrderType.MARKET,
        quantity: 100,
      });

      await new Promise((resolve) => setTimeout(resolve, 50));

      const positions = await venue.getPositions();
      expect(positions.length).toBe(0);
    });

    it('should use closePosition method', async () => {
      await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
      });

      await new Promise((resolve) => setTimeout(resolve, 50));

      const closeOrder = await venue.closePosition('AAPL');
      expect(closeOrder.side).toBe(OrderSide.SELL);
      expect(closeOrder.quantity).toBe(100);
    });
  });

  describe('Account Balance', () => {
    beforeEach(() => {
      venue.setMarketPrice('AAPL', 150.0);
    });

    it('should decrease cash after buy', async () => {
      await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
      });

      await new Promise((resolve) => setTimeout(resolve, 50));

      const balance = await venue.getAccountBalance();
      expect(balance.cash).toBeLessThan(100000);
    });

    it('should increase cash after sell', async () => {
      // First buy
      await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
      });

      await new Promise((resolve) => setTimeout(resolve, 50));

      const balanceAfterBuy = await venue.getAccountBalance();

      // Then sell
      venue.setMarketPrice('AAPL', 160.0);
      await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.SELL,
        type: OrderType.MARKET,
        quantity: 100,
      });

      await new Promise((resolve) => setTimeout(resolve, 50));

      const balanceAfterSell = await venue.getAccountBalance();
      expect(balanceAfterSell.cash).toBeGreaterThan(balanceAfterBuy.cash);
    });

    it('should track unrealized P&L', async () => {
      await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
      });

      await new Promise((resolve) => setTimeout(resolve, 50));

      venue.setMarketPrice('AAPL', 160.0);
      const balance = await venue.getAccountBalance();

      expect(balance.unrealizedPnL).toBeGreaterThan(0);
      expect(balance.equity).toBeGreaterThan(balance.cash);
    });

    it('should track realized P&L from commissions', async () => {
      await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
      });

      await new Promise((resolve) => setTimeout(resolve, 50));

      const balance = await venue.getAccountBalance();
      expect(balance.realizedPnL).toBeLessThan(0); // Negative due to commissions
    });
  });

  describe('Order Cancellation', () => {
    beforeEach(() => {
      venue.setMarketPrice('AAPL', 150.0);
    });

    it('should cancel pending limit order', async () => {
      const order = await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.LIMIT,
        quantity: 100,
        price: 140.0, // Below current price, won't fill
      });

      const cancelled = await venue.cancelOrder(order.id);
      expect(cancelled).toBe(true);

      const cancelledOrder = await venue.getOrder(order.id);
      expect(cancelledOrder.status).toBe(OrderStatus.CANCELLED);
    });

    it('should not cancel filled order', async () => {
      const order = await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
      });

      await new Promise((resolve) => setTimeout(resolve, 50));

      const cancelled = await venue.cancelOrder(order.id);
      expect(cancelled).toBe(false);
    });
  });

  describe('Order Modification', () => {
    beforeEach(() => {
      venue.setMarketPrice('AAPL', 150.0);
    });

    it('should modify pending limit order price', async () => {
      const order = await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.LIMIT,
        quantity: 100,
        price: 140.0,
      });

      const modifiedOrder = await venue.modifyOrder(order.id, {
        price: 145.0,
      });

      expect(modifiedOrder.price).toBe(145.0);
    });

    it('should modify pending order quantity', async () => {
      const order = await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.LIMIT,
        quantity: 100,
        price: 140.0,
      });

      const modifiedOrder = await venue.modifyOrder(order.id, {
        quantity: 200,
      });

      expect(modifiedOrder.quantity).toBe(200);
    });
  });

  describe('Reset Functionality', () => {
    beforeEach(() => {
      venue.setMarketPrice('AAPL', 150.0);
    });

    it('should reset to initial state', async () => {
      // Create some activity
      await venue.submitOrder({
        instrument: 'AAPL',
        side: OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: 100,
      });

      await new Promise((resolve) => setTimeout(resolve, 50));

      // Reset
      venue.reset();

      // Check state
      const balance = await venue.getAccountBalance();
      expect(balance.cash).toBe(100000);
      expect(balance.equity).toBe(100000);

      const positions = await venue.getPositions();
      expect(positions.length).toBe(0);

      const orders = await venue.getOrders();
      expect(orders.length).toBe(0);
    });
  });

  describe('Configuration', () => {
    it('should expose configuration', () => {
      const config = venue.getConfig();
      expect(config.initialCapital).toBe(100000);
      expect(config.commissionPercent).toBe(0.001);
      expect(config.slippagePercent).toBe(0.001);
    });
  });
});
