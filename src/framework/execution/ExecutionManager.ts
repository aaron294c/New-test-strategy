/**
 * Execution Manager
 *
 * Orchestrates order lifecycle management, position tracking,
 * and coordinates between framework signals and execution venues.
 */

import { EventEmitter } from 'events';
import {
  Order,
  OrderParams,
  OrderStatus,
  OrderSide,
  OrderType,
  TimeInForce,
  ExecutionVenue,
  ExecutionEvent,
  ExecutionEventType,
  ExecutionEventHandler,
  ManagedPosition,
  PositionUpdate,
  OrderValidation,
  RiskLimits,
  ExecutionStats,
} from './types';
import {
  FrameworkEvent,
  EventType,
  Position,
  MarketData,
} from '../core/types';
import { OrderRouter } from './OrderRouter';
import { PositionManager } from './PositionManager';

export interface ExecutionManagerConfig {
  venue: ExecutionVenue;
  riskLimits: RiskLimits;
  autoExecute?: boolean; // Auto-execute framework entry signals
  autoStopLoss?: boolean; // Auto-place stop-loss orders
  reconciliationInterval?: number; // Minutes between position reconciliation
  enableLogging?: boolean;
  logLevel?: 'debug' | 'info' | 'warn' | 'error';
}

/**
 * Main execution management class
 */
export class ExecutionManager extends EventEmitter {
  private config: ExecutionManagerConfig;
  private orderRouter: OrderRouter;
  private positionManager: PositionManager;
  private isActive: boolean = false;
  private reconciliationTimer?: NodeJS.Timeout;
  private eventHandlers: Map<ExecutionEventType, ExecutionEventHandler[]>;
  private stats: ExecutionStats;

  constructor(config: ExecutionManagerConfig) {
    super();
    this.config = {
      autoExecute: true,
      autoStopLoss: true,
      reconciliationInterval: 5, // Default 5 minutes
      enableLogging: true,
      logLevel: 'info',
      ...config,
    };

    this.orderRouter = new OrderRouter(config.venue, config.riskLimits);
    this.positionManager = new PositionManager(config.venue);
    this.eventHandlers = new Map();
    this.stats = this.initializeStats();

    // Wire up internal event handlers
    this.setupInternalHandlers();
  }

  /**
   * Initialize execution statistics
   */
  private initializeStats(): ExecutionStats {
    return {
      totalOrders: 0,
      filledOrders: 0,
      cancelledOrders: 0,
      rejectedOrders: 0,
      averageFillTime: 0,
      fillRate: 0,
      totalCommissions: 0,
      totalSlippage: 0,
      largestWin: 0,
      largestLoss: 0,
      averageWin: 0,
      averageLoss: 0,
      winRate: 0,
      profitFactor: 0,
      sharpeRatio: 0,
      maxDrawdown: 0,
      periodStart: new Date(),
      periodEnd: new Date(),
    };
  }

  /**
   * Setup internal event handlers for order router and position manager
   */
  private setupInternalHandlers(): void {
    // Handle order events from router
    this.orderRouter.on('order_filled', async (order: Order) => {
      await this.handleOrderFilled(order);
    });

    this.orderRouter.on('order_rejected', (order: Order) => {
      this.handleOrderRejected(order);
    });

    // Handle position events from manager
    this.positionManager.on('position_opened', (position: ManagedPosition) => {
      this.emitExecutionEvent({
        type: ExecutionEventType.POSITION_OPENED,
        timestamp: new Date(),
        data: position,
        instrument: position.instrument,
        severity: 'info',
        message: `Position opened: ${position.instrument} ${position.direction} ${position.quantity} @ ${position.entryPrice}`,
      });
    });

    this.positionManager.on('position_closed', (position: ManagedPosition) => {
      this.emitExecutionEvent({
        type: ExecutionEventType.POSITION_CLOSED,
        timestamp: new Date(),
        data: position,
        instrument: position.instrument,
        severity: 'info',
        message: `Position closed: ${position.instrument} P&L: ${position.unrealizedPnL.toFixed(2)}`,
      });
    });
  }

  /**
   * Start execution manager
   */
  public start(): void {
    if (this.isActive) {
      throw new Error('Execution manager is already active');
    }

    this.isActive = true;
    this.log('info', 'Execution manager started');

    // Start position reconciliation loop
    if (this.config.reconciliationInterval && this.config.reconciliationInterval > 0) {
      this.reconciliationTimer = setInterval(
        () => this.reconcilePositions(),
        this.config.reconciliationInterval * 60 * 1000
      );
    }
  }

  /**
   * Stop execution manager
   */
  public stop(): void {
    if (!this.isActive) {
      throw new Error('Execution manager is not active');
    }

    if (this.reconciliationTimer) {
      clearInterval(this.reconciliationTimer);
      this.reconciliationTimer = undefined;
    }

    this.isActive = false;
    this.log('info', 'Execution manager stopped');
  }

  /**
   * Handle framework entry signal
   */
  public async handleEntrySignal(event: FrameworkEvent): Promise<void> {
    if (event.type !== EventType.ENTRY_SIGNAL || !this.config.autoExecute) {
      return;
    }

    try {
      const { instrument, direction, price, quantity, stopLoss, metadata } = event.data;

      // Create entry order
      const orderParams: OrderParams = {
        instrument,
        side: direction === 'long' ? OrderSide.BUY : OrderSide.SELL,
        type: OrderType.MARKET, // Use market orders for simplicity
        quantity,
        timeInForce: TimeInForce.GTC,
        metadata: {
          strategyName: 'framework_entry',
          signal: 'entry',
          ...metadata,
        },
      };

      const order = await this.submitOrder(orderParams);

      // Place stop-loss if enabled
      if (this.config.autoStopLoss && stopLoss) {
        await this.placeStopLoss(instrument, direction, quantity, stopLoss.currentStop);
      }

      this.log('info', `Entry signal executed: ${instrument} ${direction} ${quantity} @ ${price}`);
    } catch (error) {
      this.log('error', `Failed to execute entry signal: ${error.message}`);
      this.emitExecutionEvent({
        type: ExecutionEventType.EXECUTION_ERROR,
        timestamp: new Date(),
        data: error,
        severity: 'error',
        message: `Entry signal execution failed: ${error.message}`,
      });
    }
  }

  /**
   * Handle framework exit signal
   */
  public async handleExitSignal(event: FrameworkEvent): Promise<void> {
    if (event.type !== EventType.EXIT_SIGNAL) {
      return;
    }

    try {
      const { instrument, reason, price } = event.data;
      const position = this.positionManager.getPosition(instrument);

      if (!position) {
        this.log('warn', `No position found for exit signal: ${instrument}`);
        return;
      }

      // Create exit order
      const orderParams: OrderParams = {
        instrument,
        side: position.direction === 'long' ? OrderSide.SELL : OrderSide.BUY,
        type: OrderType.MARKET,
        quantity: position.quantity,
        timeInForce: TimeInForce.GTC,
        metadata: {
          strategyName: 'framework_exit',
          signal: 'exit',
          reason,
        },
      };

      await this.submitOrder(orderParams);
      this.log('info', `Exit signal executed: ${instrument} ${reason}`);
    } catch (error) {
      this.log('error', `Failed to execute exit signal: ${error.message}`);
      this.emitExecutionEvent({
        type: ExecutionEventType.EXECUTION_ERROR,
        timestamp: new Date(),
        data: error,
        severity: 'error',
        message: `Exit signal execution failed: ${error.message}`,
      });
    }
  }

  /**
   * Handle stop adjustment event
   */
  public async handleStopAdjustment(event: FrameworkEvent): Promise<void> {
    if (event.type !== EventType.STOP_ADJUSTMENT || !this.config.autoStopLoss) {
      return;
    }

    try {
      const { instrument, newStop } = event.data;
      const position = this.positionManager.getPosition(instrument);

      if (!position) {
        return;
      }

      // Cancel existing stop order if any
      if (position.exitOrderId) {
        await this.orderRouter.cancelOrder(position.exitOrderId);
      }

      // Place new stop order
      await this.placeStopLoss(
        instrument,
        position.direction,
        position.quantity,
        newStop.currentStop
      );

      this.log('info', `Stop-loss adjusted: ${instrument} to ${newStop.currentStop}`);
    } catch (error) {
      this.log('error', `Failed to adjust stop-loss: ${error.message}`);
    }
  }

  /**
   * Submit order through router
   */
  public async submitOrder(params: OrderParams): Promise<Order> {
    // Validate order
    const validation = await this.orderRouter.validateOrder(params);
    if (!validation.valid) {
      throw new Error(`Order validation failed: ${validation.errors.join(', ')}`);
    }

    // Submit order
    const order = await this.orderRouter.submitOrder(params);

    // Update statistics
    this.stats.totalOrders++;

    this.emitExecutionEvent({
      type: ExecutionEventType.ORDER_SUBMITTED,
      timestamp: new Date(),
      data: order,
      instrument: order.instrument,
      orderId: order.id,
      severity: 'info',
      message: `Order submitted: ${order.instrument} ${order.side} ${order.quantity}`,
    });

    return order;
  }

  /**
   * Cancel order
   */
  public async cancelOrder(orderId: string): Promise<boolean> {
    const success = await this.orderRouter.cancelOrder(orderId);

    if (success) {
      this.stats.cancelledOrders++;
      this.emitExecutionEvent({
        type: ExecutionEventType.ORDER_CANCELLED,
        timestamp: new Date(),
        data: { orderId },
        orderId,
        severity: 'info',
        message: `Order cancelled: ${orderId}`,
      });
    }

    return success;
  }

  /**
   * Place stop-loss order
   */
  private async placeStopLoss(
    instrument: string,
    direction: 'long' | 'short',
    quantity: number,
    stopPrice: number
  ): Promise<Order> {
    const orderParams: OrderParams = {
      instrument,
      side: direction === 'long' ? OrderSide.SELL : OrderSide.BUY,
      type: OrderType.STOP_LOSS,
      quantity,
      stopPrice,
      timeInForce: TimeInForce.GTC,
      metadata: {
        strategyName: 'stop_loss',
        signal: 'stop',
      },
    };

    return this.submitOrder(orderParams);
  }

  /**
   * Handle order filled event
   */
  private async handleOrderFilled(order: Order): Promise<void> {
    this.stats.filledOrders++;
    this.stats.fillRate = (this.stats.filledOrders / this.stats.totalOrders) * 100;

    // Calculate commissions
    const totalCommission = order.fills.reduce((sum, fill) => sum + fill.commission, 0);
    this.stats.totalCommissions += totalCommission;

    // Update position
    if (order.metadata?.signal === 'entry') {
      await this.positionManager.openPosition(order);
    } else if (order.metadata?.signal === 'exit' || order.metadata?.signal === 'stop') {
      await this.positionManager.closePosition(order);
    }

    this.emitExecutionEvent({
      type: ExecutionEventType.ORDER_FILLED,
      timestamp: new Date(),
      data: order,
      instrument: order.instrument,
      orderId: order.id,
      severity: 'info',
      message: `Order filled: ${order.instrument} ${order.quantity} @ ${order.averageFillPrice}`,
    });
  }

  /**
   * Handle order rejected event
   */
  private handleOrderRejected(order: Order): void {
    this.stats.rejectedOrders++;

    this.emitExecutionEvent({
      type: ExecutionEventType.ORDER_REJECTED,
      timestamp: new Date(),
      data: order,
      instrument: order.instrument,
      orderId: order.id,
      severity: 'error',
      message: `Order rejected: ${order.rejectionReason || 'Unknown reason'}`,
    });
  }

  /**
   * Update position with current market data
   */
  public async updatePosition(instrument: string, marketData: MarketData): Promise<void> {
    const position = this.positionManager.getPosition(instrument);
    if (!position) return;

    const update: PositionUpdate = {
      positionId: instrument, // Using instrument as position ID for simplicity
      currentPrice: marketData.currentPrice,
      unrealizedPnL: this.calculateUnrealizedPnL(position, marketData.currentPrice),
      timestamp: new Date(),
    };

    await this.positionManager.updatePosition(update);
  }

  /**
   * Calculate unrealized P&L
   */
  private calculateUnrealizedPnL(position: ManagedPosition, currentPrice: number): number {
    return position.direction === 'long'
      ? (currentPrice - position.entryPrice) * position.quantity
      : (position.entryPrice - currentPrice) * position.quantity;
  }

  /**
   * Reconcile positions with broker
   */
  private async reconcilePositions(): Promise<void> {
    try {
      const reconciliation = await this.positionManager.reconcileWithBroker();

      if (reconciliation.discrepancies.length > 0) {
        this.emitExecutionEvent({
          type: ExecutionEventType.RECONCILIATION_COMPLETE,
          timestamp: new Date(),
          data: reconciliation,
          severity: 'warning',
          message: `Position reconciliation found ${reconciliation.discrepancies.length} discrepancies`,
        });
      }

      this.log('info', 'Position reconciliation completed');
    } catch (error) {
      this.log('error', `Position reconciliation failed: ${error.message}`);
    }
  }

  /**
   * Get current positions
   */
  public getPositions(): ManagedPosition[] {
    return this.positionManager.getAllPositions();
  }

  /**
   * Get specific position
   */
  public getPosition(instrument: string): ManagedPosition | null {
    return this.positionManager.getPosition(instrument);
  }

  /**
   * Get execution statistics
   */
  public getStats(): ExecutionStats {
    this.stats.periodEnd = new Date();
    return { ...this.stats };
  }

  /**
   * Reset statistics
   */
  public resetStats(): void {
    this.stats = this.initializeStats();
  }

  /**
   * Subscribe to execution events
   */
  public on(eventType: ExecutionEventType, handler: ExecutionEventHandler): void {
    const handlers = this.eventHandlers.get(eventType) ?? [];
    handlers.push(handler);
    this.eventHandlers.set(eventType, handlers);
  }

  /**
   * Unsubscribe from execution events
   */
  public off(eventType: ExecutionEventType, handler: ExecutionEventHandler): void {
    const handlers = this.eventHandlers.get(eventType) ?? [];
    const filtered = handlers.filter((h) => h !== handler);
    this.eventHandlers.set(eventType, filtered);
  }

  /**
   * Emit execution event
   */
  private emitExecutionEvent(event: ExecutionEvent): void {
    const handlers = this.eventHandlers.get(event.type) ?? [];
    handlers.forEach((handler) => {
      try {
        handler(event);
      } catch (error) {
        this.log('error', `Error in event handler for ${event.type}: ${error.message}`);
      }
    });
  }

  /**
   * Log message
   */
  private log(level: 'debug' | 'info' | 'warn' | 'error', message: string): void {
    if (!this.config.enableLogging) return;

    const levels = { debug: 0, info: 1, warn: 2, error: 3 };
    const configLevel = levels[this.config.logLevel || 'info'];
    const messageLevel = levels[level];

    if (messageLevel >= configLevel) {
      const timestamp = new Date().toISOString();
      console[level](`[${timestamp}] [ExecutionManager] [${level.toUpperCase()}] ${message}`);
    }
  }

  /**
   * Get router instance (for advanced usage)
   */
  public getRouter(): OrderRouter {
    return this.orderRouter;
  }

  /**
   * Get position manager instance (for advanced usage)
   */
  public getPositionManager(): PositionManager {
    return this.positionManager;
  }
}
