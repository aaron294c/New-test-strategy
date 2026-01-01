/**
 * Paper Trading Venue
 *
 * Simulated execution venue for testing and development.
 * Provides realistic order execution without real money.
 */

import {
  ExecutionVenue,
  Order,
  OrderParams,
  OrderStatus,
  OrderType,
  OrderSide,
  OrderFill,
  BrokerPosition,
  AccountBalance,
  TimeInForce,
} from './types';

export interface PaperTradingConfig {
  initialCapital: number;
  commission?: number; // Per share/contract
  commissionPercent?: number; // As percentage of order value
  slippagePercent?: number; // Simulated slippage
  fillDelay?: number; // Milliseconds to simulate fill delay
  rejectRate?: number; // Probability of order rejection (0-1)
  partialFillRate?: number; // Probability of partial fill (0-1)
}

/**
 * Paper trading implementation of ExecutionVenue
 */
export class PaperTradingVenue implements ExecutionVenue {
  public readonly name: string = 'Paper Trading';
  public readonly type: 'paper' = 'paper';

  private config: Required<PaperTradingConfig>;
  private orders: Map<string, Order> = new Map();
  private positions: Map<string, BrokerPosition> = new Map();
  private accountBalance: AccountBalance;
  private orderIdCounter: number = 1;
  private marketPrices: Map<string, number> = new Map();

  constructor(config: PaperTradingConfig) {
    this.config = {
      commission: 0,
      commissionPercent: 0.001, // 0.1% default
      slippagePercent: 0.001, // 0.1% default
      fillDelay: 100, // 100ms default
      rejectRate: 0, // No rejections by default
      partialFillRate: 0, // No partial fills by default
      ...config,
    };

    this.accountBalance = {
      cash: config.initialCapital,
      equity: config.initialCapital,
      marginUsed: 0,
      marginAvailable: config.initialCapital,
      buyingPower: config.initialCapital,
      unrealizedPnL: 0,
      realizedPnL: 0,
      timestamp: new Date(),
    };
  }

  /**
   * Submit order to paper trading venue
   */
  public async submitOrder(params: OrderParams): Promise<Order> {
    const orderId = this.generateOrderId();

    // Check for random rejection
    if (Math.random() < this.config.rejectRate) {
      const order: Order = {
        id: orderId,
        instrument: params.instrument,
        side: params.side,
        type: params.type,
        quantity: params.quantity,
        price: params.price,
        stopPrice: params.stopPrice,
        timeInForce: params.timeInForce || TimeInForce.GTC,
        status: OrderStatus.REJECTED,
        filledQuantity: 0,
        averageFillPrice: 0,
        createdAt: new Date(),
        updatedAt: new Date(),
        rejectionReason: 'Simulated rejection for testing',
        metadata: params.metadata,
        fills: [],
      };

      this.orders.set(orderId, order);
      return order;
    }

    // Create order
    const order: Order = {
      id: orderId,
      instrument: params.instrument,
      side: params.side,
      type: params.type,
      quantity: params.quantity,
      price: params.price,
      stopPrice: params.stopPrice,
      timeInForce: params.timeInForce || TimeInForce.GTC,
      status: OrderStatus.PENDING,
      filledQuantity: 0,
      averageFillPrice: 0,
      createdAt: new Date(),
      updatedAt: new Date(),
      metadata: params.metadata,
      fills: [],
    };

    this.orders.set(orderId, order);

    // Simulate async order processing
    setTimeout(() => {
      this.processOrder(orderId).catch(error => {
        console.error(`Error processing order ${orderId}:`, error);
      });
    }, this.config.fillDelay);

    return order;
  }

  /**
   * Process order and simulate fill
   */
  private async processOrder(orderId: string): Promise<void> {
    const order = this.orders.get(orderId);
    if (!order || order.status !== OrderStatus.PENDING) {
      return;
    }

    // Get current market price
    const currentPrice = await this.getCurrentPrice(order.instrument);

    // Determine fill price based on order type
    let fillPrice: number;

    switch (order.type) {
      case OrderType.MARKET:
        // Market order fills at current price with slippage
        const slippage = currentPrice * this.config.slippagePercent;
        fillPrice = order.side === OrderSide.BUY
          ? currentPrice + slippage
          : currentPrice - slippage;
        break;

      case OrderType.LIMIT:
        // Limit order only fills if price is favorable
        if (!order.price) {
          order.status = OrderStatus.REJECTED;
          order.rejectionReason = 'Limit order requires price';
          order.updatedAt = new Date();
          return;
        }

        const canFill = order.side === OrderSide.BUY
          ? currentPrice <= order.price
          : currentPrice >= order.price;

        if (!canFill) {
          // Order remains pending
          return;
        }

        fillPrice = order.price;
        break;

      case OrderType.STOP_LOSS:
        // Stop loss converts to market when stop price hit
        if (!order.stopPrice) {
          order.status = OrderStatus.REJECTED;
          order.rejectionReason = 'Stop order requires stop price';
          order.updatedAt = new Date();
          return;
        }

        const stopTriggered = order.side === OrderSide.BUY
          ? currentPrice >= order.stopPrice
          : currentPrice <= order.stopPrice;

        if (!stopTriggered) {
          return;
        }

        fillPrice = currentPrice;
        break;

      default:
        fillPrice = currentPrice;
    }

    // Determine fill quantity (may be partial)
    let fillQuantity = order.quantity;
    let status = OrderStatus.FILLED;

    if (Math.random() < this.config.partialFillRate) {
      fillQuantity = Math.floor(order.quantity * (0.5 + Math.random() * 0.5));
      status = OrderStatus.PARTIALLY_FILLED;
    }

    // Calculate commission
    const commission = this.calculateCommission(fillQuantity, fillPrice);

    // Create fill
    const fill: OrderFill = {
      orderId: order.id,
      quantity: fillQuantity,
      price: fillPrice,
      commission,
      timestamp: new Date(),
      executionId: `${orderId}-${Date.now()}`,
    };

    // Update order
    order.fills.push(fill);
    order.filledQuantity += fillQuantity;
    order.averageFillPrice = this.calculateAverageFillPrice(order.fills);
    order.status = status;
    order.updatedAt = new Date();
    if (status === OrderStatus.FILLED) {
      order.filledAt = new Date();
    }

    // Update position
    await this.updatePosition(order, fill);

    // Update account balance
    this.updateAccountBalance(order, fill);
  }

  /**
   * Update position after fill
   */
  private async updatePosition(order: Order, fill: OrderFill): Promise<void> {
    const existing = this.positions.get(order.instrument);

    const currentPrice = await this.getCurrentPrice(order.instrument);
    const quantityChange = order.side === OrderSide.BUY ? fill.quantity : -fill.quantity;

    if (existing) {
      const newQuantity = existing.quantity + quantityChange;

      if (Math.abs(newQuantity) < 0.001) {
        // Position closed
        this.positions.delete(order.instrument);
      } else {
        // Update position
        const newAveragePrice = newQuantity !== 0
          ? (existing.averagePrice * existing.quantity + fill.price * quantityChange) / newQuantity
          : existing.averagePrice;

        const unrealizedPnL = (currentPrice - newAveragePrice) * newQuantity;

        this.positions.set(order.instrument, {
          instrument: order.instrument,
          quantity: newQuantity,
          averagePrice: newAveragePrice,
          currentPrice,
          unrealizedPnL,
        });
      }
    } else {
      // New position
      const unrealizedPnL = (currentPrice - fill.price) * quantityChange;

      this.positions.set(order.instrument, {
        instrument: order.instrument,
        quantity: quantityChange,
        averagePrice: fill.price,
        currentPrice,
        unrealizedPnL,
      });
    }
  }

  /**
   * Update account balance after fill
   */
  private updateAccountBalance(order: Order, fill: OrderFill): void {
    const cashChange = order.side === OrderSide.BUY
      ? -(fill.price * fill.quantity + fill.commission)
      : fill.price * fill.quantity - fill.commission;

    this.accountBalance.cash += cashChange;

    // Update realized P&L (commissions are realized costs)
    this.accountBalance.realizedPnL -= fill.commission;

    // Recalculate equity and unrealized P&L
    this.accountBalance.unrealizedPnL = Array.from(this.positions.values())
      .reduce((sum, pos) => sum + pos.unrealizedPnL, 0);

    this.accountBalance.equity = this.accountBalance.cash + this.accountBalance.unrealizedPnL;
    this.accountBalance.buyingPower = this.accountBalance.cash;
    this.accountBalance.timestamp = new Date();
  }

  /**
   * Calculate commission for fill
   */
  private calculateCommission(quantity: number, price: number): number {
    const flatCommission = this.config.commission * quantity;
    const percentCommission = (quantity * price) * this.config.commissionPercent;
    return flatCommission + percentCommission;
  }

  /**
   * Calculate average fill price from fills
   */
  private calculateAverageFillPrice(fills: OrderFill[]): number {
    const totalCost = fills.reduce((sum, fill) => sum + fill.price * fill.quantity, 0);
    const totalQuantity = fills.reduce((sum, fill) => sum + fill.quantity, 0);
    return totalQuantity > 0 ? totalCost / totalQuantity : 0;
  }

  /**
   * Cancel order
   */
  public async cancelOrder(orderId: string): Promise<boolean> {
    const order = this.orders.get(orderId);

    if (!order) {
      return false;
    }

    if (order.status === OrderStatus.FILLED ||
        order.status === OrderStatus.CANCELLED ||
        order.status === OrderStatus.REJECTED) {
      return false;
    }

    order.status = OrderStatus.CANCELLED;
    order.cancelledAt = new Date();
    order.updatedAt = new Date();

    return true;
  }

  /**
   * Modify order
   */
  public async modifyOrder(orderId: string, updates: Partial<OrderParams>): Promise<Order> {
    const order = this.orders.get(orderId);

    if (!order) {
      throw new Error(`Order not found: ${orderId}`);
    }

    if (order.status !== OrderStatus.PENDING) {
      throw new Error(`Cannot modify order in ${order.status} status`);
    }

    if (updates.price !== undefined) {
      order.price = updates.price;
    }
    if (updates.stopPrice !== undefined) {
      order.stopPrice = updates.stopPrice;
    }
    if (updates.quantity !== undefined) {
      order.quantity = updates.quantity;
    }

    order.updatedAt = new Date();

    return order;
  }

  /**
   * Get order by ID
   */
  public async getOrder(orderId: string): Promise<Order> {
    const order = this.orders.get(orderId);
    if (!order) {
      throw new Error(`Order not found: ${orderId}`);
    }
    return order;
  }

  /**
   * Get all orders
   */
  public async getOrders(instrument?: string): Promise<Order[]> {
    const orders = Array.from(this.orders.values());
    return instrument
      ? orders.filter(o => o.instrument === instrument)
      : orders;
  }

  /**
   * Get all positions
   */
  public async getPositions(): Promise<BrokerPosition[]> {
    return Array.from(this.positions.values());
  }

  /**
   * Close position
   */
  public async closePosition(instrument: string, quantity?: number): Promise<Order> {
    const position = this.positions.get(instrument);
    if (!position) {
      throw new Error(`No position found for ${instrument}`);
    }

    const closeQuantity = quantity || Math.abs(position.quantity);
    const side = position.quantity > 0 ? OrderSide.SELL : OrderSide.BUY;

    return this.submitOrder({
      instrument,
      side,
      type: OrderType.MARKET,
      quantity: closeQuantity,
      metadata: {
        signal: 'close_position',
      },
    });
  }

  /**
   * Get account balance
   */
  public async getAccountBalance(): Promise<AccountBalance> {
    // Update current prices and unrealized P&L
    for (const [instrument, position] of this.positions) {
      const currentPrice = await this.getCurrentPrice(instrument);
      position.currentPrice = currentPrice;
      position.unrealizedPnL = (currentPrice - position.averagePrice) * position.quantity;
    }

    this.accountBalance.unrealizedPnL = Array.from(this.positions.values())
      .reduce((sum, pos) => sum + pos.unrealizedPnL, 0);

    this.accountBalance.equity = this.accountBalance.cash + this.accountBalance.unrealizedPnL;
    this.accountBalance.timestamp = new Date();

    return { ...this.accountBalance };
  }

  /**
   * Get current price for instrument
   */
  public async getCurrentPrice(instrument: string): Promise<number> {
    // Return cached price or generate random price for simulation
    const cached = this.marketPrices.get(instrument);
    if (cached) {
      // Simulate price movement
      const change = (Math.random() - 0.5) * 0.02; // ±1% random walk
      const newPrice = cached * (1 + change);
      this.marketPrices.set(instrument, newPrice);
      return newPrice;
    }

    // Initialize with random price between 10 and 1000
    const initialPrice = 10 + Math.random() * 990;
    this.marketPrices.set(instrument, initialPrice);
    return initialPrice;
  }

  /**
   * Set market price for instrument (for testing)
   */
  public setMarketPrice(instrument: string, price: number): void {
    this.marketPrices.set(instrument, price);
  }

  /**
   * Generate unique order ID
   */
  private generateOrderId(): string {
    return `PT-${Date.now()}-${this.orderIdCounter++}`;
  }

  /**
   * Reset paper trading venue to initial state
   */
  public reset(): void {
    this.orders.clear();
    this.positions.clear();
    this.marketPrices.clear();
    this.orderIdCounter = 1;
    this.accountBalance = {
      cash: this.config.initialCapital,
      equity: this.config.initialCapital,
      marginUsed: 0,
      marginAvailable: this.config.initialCapital,
      buyingPower: this.config.initialCapital,
      unrealizedPnL: 0,
      realizedPnL: 0,
      timestamp: new Date(),
    };
  }

  /**
   * Get configuration
   */
  public getConfig(): Required<PaperTradingConfig> {
    return { ...this.config };
  }
}
