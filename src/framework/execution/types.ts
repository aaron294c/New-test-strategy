/**
 * Execution Layer Types
 *
 * Defines interfaces for order management, position tracking,
 * and integration with execution venues.
 */

import { Position, AdaptiveStopLoss } from '../core/types';

// ==================== ORDER TYPES ====================

export enum OrderType {
  MARKET = 'market',
  LIMIT = 'limit',
  STOP_LOSS = 'stop_loss',
  STOP_LIMIT = 'stop_limit',
  TRAILING_STOP = 'trailing_stop',
}

export enum OrderStatus {
  PENDING = 'pending',
  SUBMITTED = 'submitted',
  PARTIALLY_FILLED = 'partially_filled',
  FILLED = 'filled',
  CANCELLED = 'cancelled',
  REJECTED = 'rejected',
  EXPIRED = 'expired',
}

export enum OrderSide {
  BUY = 'buy',
  SELL = 'sell',
}

export enum TimeInForce {
  DAY = 'day',
  GTC = 'gtc', // Good till cancelled
  IOC = 'ioc', // Immediate or cancel
  FOK = 'fok', // Fill or kill
}

export interface OrderParams {
  instrument: string;
  side: OrderSide;
  type: OrderType;
  quantity: number;
  price?: number; // Required for LIMIT orders
  stopPrice?: number; // Required for STOP orders
  timeInForce?: TimeInForce;
  metadata?: {
    strategyName?: string;
    signal?: string;
    compositeScore?: number;
    regime?: string;
    [key: string]: any;
  };
}

export interface Order {
  id: string;
  instrument: string;
  side: OrderSide;
  type: OrderType;
  quantity: number;
  price?: number;
  stopPrice?: number;
  timeInForce: TimeInForce;
  status: OrderStatus;
  filledQuantity: number;
  averageFillPrice: number;
  createdAt: Date;
  updatedAt: Date;
  filledAt?: Date;
  cancelledAt?: Date;
  rejectionReason?: string;
  metadata?: Record<string, any>;
  fills: OrderFill[];
}

export interface OrderFill {
  orderId: string;
  quantity: number;
  price: number;
  commission: number;
  timestamp: Date;
  executionId: string;
}

// ==================== POSITION MANAGEMENT ====================

export interface ManagedPosition extends Position {
  orderId?: string; // Entry order ID
  exitOrderId?: string; // Exit order ID if placed
  averageEntryPrice: number; // Account for partial fills
  totalCommission: number;
  realizedPnL: number; // For partially closed positions
  fills: OrderFill[];
  lastUpdated: Date;
  tags?: string[]; // For categorization
}

export interface PositionUpdate {
  positionId: string;
  currentPrice: number;
  unrealizedPnL: number;
  stopLoss?: AdaptiveStopLoss;
  timestamp: Date;
}

export interface PositionReconciliation {
  frameworkPositions: ManagedPosition[];
  brokerPositions: BrokerPosition[];
  discrepancies: PositionDiscrepancy[];
  lastReconciled: Date;
}

export interface BrokerPosition {
  instrument: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  unrealizedPnL: number;
}

export interface PositionDiscrepancy {
  instrument: string;
  frameworkQuantity: number;
  brokerQuantity: number;
  difference: number;
  severity: 'low' | 'medium' | 'high';
  reason?: string;
}

// ==================== EXECUTION VENUE ====================

export interface ExecutionVenue {
  name: string;
  type: 'paper' | 'live' | 'simulation';

  // Order operations
  submitOrder(params: OrderParams): Promise<Order>;
  cancelOrder(orderId: string): Promise<boolean>;
  modifyOrder(orderId: string, updates: Partial<OrderParams>): Promise<Order>;
  getOrder(orderId: string): Promise<Order>;
  getOrders(instrument?: string): Promise<Order[]>;

  // Position operations
  getPositions(): Promise<BrokerPosition[]>;
  closePosition(instrument: string, quantity?: number): Promise<Order>;

  // Account operations
  getAccountBalance(): Promise<AccountBalance>;

  // Market data (for paper trading)
  getCurrentPrice(instrument: string): Promise<number>;
}

export interface AccountBalance {
  cash: number;
  equity: number;
  marginUsed: number;
  marginAvailable: number;
  buyingPower: number;
  unrealizedPnL: number;
  realizedPnL: number;
  timestamp: Date;
}

// ==================== RISK CHECKS ====================

export interface RiskCheck {
  name: string;
  passed: boolean;
  message: string;
  severity: 'info' | 'warning' | 'error';
}

export interface OrderValidation {
  valid: boolean;
  checks: RiskCheck[];
  errors: string[];
  warnings: string[];
}

export interface RiskLimits {
  maxPositionSize: number; // Max quantity per position
  maxOrderValue: number; // Max dollar value per order
  maxDailyOrders: number;
  maxOpenPositions: number;
  maxLeverage: number;
  maxDrawdown: number; // Percentage
  minAccountBalance: number;
  allowedInstruments?: string[];
  blockedInstruments?: string[];
}

// ==================== EXECUTION EVENTS ====================

export enum ExecutionEventType {
  ORDER_CREATED = 'order_created',
  ORDER_SUBMITTED = 'order_submitted',
  ORDER_FILLED = 'order_filled',
  ORDER_PARTIALLY_FILLED = 'order_partially_filled',
  ORDER_CANCELLED = 'order_cancelled',
  ORDER_REJECTED = 'order_rejected',
  POSITION_OPENED = 'position_opened',
  POSITION_UPDATED = 'position_updated',
  POSITION_CLOSED = 'position_closed',
  STOP_TRIGGERED = 'stop_triggered',
  RISK_LIMIT_BREACHED = 'risk_limit_breached',
  RECONCILIATION_COMPLETE = 'reconciliation_complete',
  EXECUTION_ERROR = 'execution_error',
}

export interface ExecutionEvent {
  type: ExecutionEventType;
  timestamp: Date;
  data: any;
  instrument?: string;
  orderId?: string;
  positionId?: string;
  severity: 'info' | 'warning' | 'error';
  message: string;
}

export type ExecutionEventHandler = (event: ExecutionEvent) => void | Promise<void>;

// ==================== EXECUTION STATISTICS ====================

export interface ExecutionStats {
  totalOrders: number;
  filledOrders: number;
  cancelledOrders: number;
  rejectedOrders: number;
  averageFillTime: number; // milliseconds
  fillRate: number; // percentage
  totalCommissions: number;
  totalSlippage: number;
  largestWin: number;
  largestLoss: number;
  averageWin: number;
  averageLoss: number;
  winRate: number;
  profitFactor: number;
  sharpeRatio: number;
  maxDrawdown: number;
  periodStart: Date;
  periodEnd: Date;
}
