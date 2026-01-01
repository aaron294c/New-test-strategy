/**
 * Order Router
 *
 * Abstract order routing layer that provides:
 * - Venue abstraction
 * - Order validation and risk checks
 * - Order lifecycle management
 * - Support for multiple execution venues
 */

import { EventEmitter } from 'events';
import {
  Order,
  OrderParams,
  OrderStatus,
  OrderType,
  OrderSide,
  TimeInForce,
  OrderFill,
  ExecutionVenue,
  OrderValidation,
  RiskCheck,
  RiskLimits,
  AccountBalance,
} from './types';

/**
 * Order Router for managing order execution across venues
 */
export class OrderRouter extends EventEmitter {
  private venue: ExecutionVenue;
  private riskLimits: RiskLimits;
  private orders: Map<string, Order>;
  private dailyOrderCount: number = 0;
  private lastResetDate: Date = new Date();

  constructor(venue: ExecutionVenue, riskLimits: RiskLimits) {
    super();
    this.venue = venue;
    this.riskLimits = riskLimits;
    this.orders = new Map();
  }

  /**
   * Submit order to execution venue
   */
  public async submitOrder(params: OrderParams): Promise<Order> {
    // Validate order
    const validation = await this.validateOrder(params);
    if (!validation.valid) {
      throw new Error(`Order validation failed: ${validation.errors.join(', ')}`);
    }

    // Check daily order limit
    this.resetDailyCountIfNeeded();
    if (this.dailyOrderCount >= this.riskLimits.maxDailyOrders) {
      throw new Error('Daily order limit reached');
    }

    try {
      // Submit to venue
      const order = await this.venue.submitOrder(params);

      // Store order
      this.orders.set(order.id, order);
      this.dailyOrderCount++;

      // Monitor order status
      this.monitorOrder(order.id);

      return order;
    } catch (error) {
      this.emit('order_error', {
        params,
        error: error.message,
      });
      throw error;
    }
  }

  /**
   * Cancel order
   */
  public async cancelOrder(orderId: string): Promise<boolean> {
    const order = this.orders.get(orderId);
    if (!order) {
      throw new Error(`Order not found: ${orderId}`);
    }

    if (
      order.status === OrderStatus.FILLED ||
      order.status === OrderStatus.CANCELLED ||
      order.status === OrderStatus.REJECTED
    ) {
      return false; // Order cannot be cancelled
    }

    try {
      const success = await this.venue.cancelOrder(orderId);

      if (success) {
        order.status = OrderStatus.CANCELLED;
        order.cancelledAt = new Date();
        order.updatedAt = new Date();
        this.orders.set(orderId, order);
        this.emit('order_cancelled', order);
      }

      return success;
    } catch (error) {
      this.emit('order_error', {
        orderId,
        error: error.message,
      });
      throw error;
    }
  }

  /**
   * Modify existing order
   */
  public async modifyOrder(
    orderId: string,
    updates: Partial<OrderParams>
  ): Promise<Order> {
    const order = this.orders.get(orderId);
    if (!order) {
      throw new Error(`Order not found: ${orderId}`);
    }

    if (order.status !== OrderStatus.PENDING && order.status !== OrderStatus.SUBMITTED) {
      throw new Error(`Order cannot be modified in ${order.status} status`);
    }

    try {
      const modifiedOrder = await this.venue.modifyOrder(orderId, updates);
      this.orders.set(orderId, modifiedOrder);
      this.emit('order_modified', modifiedOrder);
      return modifiedOrder;
    } catch (error) {
      this.emit('order_error', {
        orderId,
        error: error.message,
      });
      throw error;
    }
  }

  /**
   * Get order by ID
   */
  public async getOrder(orderId: string): Promise<Order> {
    // Try to get from venue first for latest status
    try {
      const order = await this.venue.getOrder(orderId);
      this.orders.set(orderId, order);
      return order;
    } catch (error) {
      // Fall back to local cache
      const cachedOrder = this.orders.get(orderId);
      if (!cachedOrder) {
        throw new Error(`Order not found: ${orderId}`);
      }
      return cachedOrder;
    }
  }

  /**
   * Get all orders, optionally filtered by instrument
   */
  public async getOrders(instrument?: string): Promise<Order[]> {
    try {
      const venueOrders = await this.venue.getOrders(instrument);

      // Update local cache
      venueOrders.forEach((order) => {
        this.orders.set(order.id, order);
      });

      return venueOrders;
    } catch (error) {
      // Fall back to local cache
      const orders = Array.from(this.orders.values());
      return instrument
        ? orders.filter((o) => o.instrument === instrument)
        : orders;
    }
  }

  /**
   * Validate order before submission
   */
  public async validateOrder(params: OrderParams): Promise<OrderValidation> {
    const checks: RiskCheck[] = [];
    const errors: string[] = [];
    const warnings: string[] = [];

    // Basic parameter validation
    if (!params.instrument || !params.side || !params.type || !params.quantity) {
      errors.push('Missing required order parameters');
      return { valid: false, checks, errors, warnings };
    }

    if (params.quantity <= 0) {
      errors.push('Quantity must be positive');
    }

    // Check instrument restrictions
    if (this.riskLimits.allowedInstruments &&
        !this.riskLimits.allowedInstruments.includes(params.instrument)) {
      checks.push({
        name: 'instrument_allowed',
        passed: false,
        message: `Instrument ${params.instrument} is not in allowed list`,
        severity: 'error',
      });
      errors.push(`Instrument ${params.instrument} not allowed`);
    }

    if (this.riskLimits.blockedInstruments?.includes(params.instrument)) {
      checks.push({
        name: 'instrument_blocked',
        passed: false,
        message: `Instrument ${params.instrument} is blocked`,
        severity: 'error',
      });
      errors.push(`Instrument ${params.instrument} is blocked`);
    }

    // Check position size limit
    if (params.quantity > this.riskLimits.maxPositionSize) {
      checks.push({
        name: 'position_size',
        passed: false,
        message: `Quantity ${params.quantity} exceeds max position size ${this.riskLimits.maxPositionSize}`,
        severity: 'error',
      });
      errors.push('Position size exceeds limit');
    }

    // Check order value limit
    const estimatedPrice = params.price || await this.getEstimatedPrice(params);
    const orderValue = params.quantity * estimatedPrice;

    if (orderValue > this.riskLimits.maxOrderValue) {
      checks.push({
        name: 'order_value',
        passed: false,
        message: `Order value ${orderValue} exceeds limit ${this.riskLimits.maxOrderValue}`,
        severity: 'error',
      });
      errors.push('Order value exceeds limit');
    }

    // Check daily order limit
    this.resetDailyCountIfNeeded();
    if (this.dailyOrderCount >= this.riskLimits.maxDailyOrders) {
      checks.push({
        name: 'daily_orders',
        passed: false,
        message: `Daily order limit reached: ${this.riskLimits.maxDailyOrders}`,
        severity: 'error',
      });
      errors.push('Daily order limit reached');
    }

    // Check max open positions
    try {
      const positions = await this.venue.getPositions();
      if (params.side === OrderSide.BUY) {
        const buyPositions = positions.filter(p => p.quantity > 0);
        if (buyPositions.length >= this.riskLimits.maxOpenPositions) {
          checks.push({
            name: 'max_positions',
            passed: false,
            message: `Max open positions reached: ${this.riskLimits.maxOpenPositions}`,
            severity: 'warning',
          });
          warnings.push('At max position limit');
        }
      }
    } catch (error) {
      // Ignore if positions cannot be retrieved
    }

    // Check account balance
    try {
      const balance = await this.venue.getAccountBalance();
      if (balance.cash < this.riskLimits.minAccountBalance) {
        checks.push({
          name: 'min_balance',
          passed: false,
          message: `Account balance ${balance.cash} below minimum ${this.riskLimits.minAccountBalance}`,
          severity: 'error',
        });
        errors.push('Insufficient account balance');
      }

      if (orderValue > balance.buyingPower) {
        checks.push({
          name: 'buying_power',
          passed: false,
          message: `Order value ${orderValue} exceeds buying power ${balance.buyingPower}`,
          severity: 'error',
        });
        errors.push('Insufficient buying power');
      }
    } catch (error) {
      warnings.push('Could not verify account balance');
    }

    // Order type specific validation
    if (params.type === OrderType.LIMIT && !params.price) {
      errors.push('Limit orders require a price');
    }

    if ((params.type === OrderType.STOP_LOSS || params.type === OrderType.STOP_LIMIT) &&
        !params.stopPrice) {
      errors.push('Stop orders require a stop price');
    }

    const valid = errors.length === 0;

    return {
      valid,
      checks,
      errors,
      warnings,
    };
  }

  /**
   * Monitor order status until filled or terminal state
   */
  private async monitorOrder(orderId: string): Promise<void> {
    const checkStatus = async () => {
      try {
        const order = await this.getOrder(orderId);

        switch (order.status) {
          case OrderStatus.FILLED:
            this.emit('order_filled', order);
            return; // Stop monitoring

          case OrderStatus.PARTIALLY_FILLED:
            this.emit('order_partially_filled', order);
            // Continue monitoring
            setTimeout(checkStatus, 1000);
            break;

          case OrderStatus.CANCELLED:
            this.emit('order_cancelled', order);
            return; // Stop monitoring

          case OrderStatus.REJECTED:
            this.emit('order_rejected', order);
            return; // Stop monitoring

          case OrderStatus.EXPIRED:
            this.emit('order_expired', order);
            return; // Stop monitoring

          default:
            // Continue monitoring for pending/submitted orders
            setTimeout(checkStatus, 1000);
        }
      } catch (error) {
        this.emit('order_error', {
          orderId,
          error: error.message,
        });
      }
    };

    // Start monitoring
    setTimeout(checkStatus, 100);
  }

  /**
   * Get estimated price for order validation
   */
  private async getEstimatedPrice(params: OrderParams): Promise<number> {
    try {
      return await this.venue.getCurrentPrice(params.instrument);
    } catch (error) {
      // Use provided price or default to 0
      return params.price || params.stopPrice || 0;
    }
  }

  /**
   * Reset daily order count if new day
   */
  private resetDailyCountIfNeeded(): void {
    const now = new Date();
    if (now.toDateString() !== this.lastResetDate.toDateString()) {
      this.dailyOrderCount = 0;
      this.lastResetDate = now;
    }
  }

  /**
   * Get risk limits
   */
  public getRiskLimits(): RiskLimits {
    return { ...this.riskLimits };
  }

  /**
   * Update risk limits
   */
  public updateRiskLimits(limits: Partial<RiskLimits>): void {
    this.riskLimits = {
      ...this.riskLimits,
      ...limits,
    };
  }

  /**
   * Get venue instance
   */
  public getVenue(): ExecutionVenue {
    return this.venue;
  }
}
