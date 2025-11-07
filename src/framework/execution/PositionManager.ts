/**
 * Position Manager
 *
 * Manages position lifecycle, tracking, and reconciliation:
 * - Real-time position monitoring
 * - P&L calculation
 * - Risk metrics per position
 * - Position reconciliation with broker
 */

import { EventEmitter } from 'events';
import {
  Order,
  OrderStatus,
  OrderSide,
  ManagedPosition,
  PositionUpdate,
  PositionReconciliation,
  BrokerPosition,
  PositionDiscrepancy,
  ExecutionVenue,
} from './types';
import { Position, AdaptiveStopLoss } from '../core/types';

/**
 * Position Manager for tracking and reconciling positions
 */
export class PositionManager extends EventEmitter {
  private venue: ExecutionVenue;
  private positions: Map<string, ManagedPosition>;
  private closedPositions: ManagedPosition[] = [];

  constructor(venue: ExecutionVenue) {
    super();
    this.venue = venue;
    this.positions = new Map();
  }

  /**
   * Open new position from filled order
   */
  public async openPosition(order: Order): Promise<ManagedPosition> {
    if (order.status !== OrderStatus.FILLED) {
      throw new Error('Can only open position from filled order');
    }

    const existingPosition = this.positions.get(order.instrument);

    // Calculate average entry price accounting for fills
    const totalCost = order.fills.reduce((sum, fill) => sum + fill.price * fill.quantity, 0);
    const totalQuantity = order.filledQuantity;
    const averagePrice = totalCost / totalQuantity;

    // Calculate total commission
    const totalCommission = order.fills.reduce((sum, fill) => sum + fill.commission, 0);

    if (existingPosition) {
      // Add to existing position (averaging)
      const newQuantity = existingPosition.quantity + totalQuantity;
      const newAveragePrice =
        (existingPosition.averageEntryPrice * existingPosition.quantity + totalCost) /
        newQuantity;

      const updatedPosition: ManagedPosition = {
        ...existingPosition,
        quantity: newQuantity,
        averageEntryPrice: newAveragePrice,
        entryPrice: newAveragePrice,
        totalCommission: existingPosition.totalCommission + totalCommission,
        fills: [...existingPosition.fills, ...order.fills],
        lastUpdated: new Date(),
      };

      this.positions.set(order.instrument, updatedPosition);
      this.emit('position_updated', updatedPosition);
      return updatedPosition;
    } else {
      // Create new position
      const direction = order.side === OrderSide.BUY ? 'long' : 'short';

      const position: ManagedPosition = {
        instrument: order.instrument,
        direction,
        entryPrice: averagePrice,
        currentPrice: averagePrice,
        quantity: totalQuantity,
        positionValue: averagePrice * totalQuantity,
        unrealizedPnL: 0,
        riskAmount: 0, // Will be set when stop-loss is placed
        stopLoss: this.createDefaultStopLoss(averagePrice),
        compositeScore: {
          instrument: order.instrument,
          totalScore: 0,
          factors: [],
          timestamp: new Date(),
        },
        openedAt: order.filledAt || new Date(),
        timeframe: 'H4' as any, // Default timeframe
        orderId: order.id,
        averageEntryPrice: averagePrice,
        totalCommission,
        realizedPnL: 0,
        fills: order.fills,
        lastUpdated: new Date(),
      };

      this.positions.set(order.instrument, position);
      this.emit('position_opened', position);
      return position;
    }
  }

  /**
   * Close position from filled exit order
   */
  public async closePosition(order: Order): Promise<void> {
    if (order.status !== OrderStatus.FILLED) {
      throw new Error('Can only close position from filled order');
    }

    const position = this.positions.get(order.instrument);
    if (!position) {
      throw new Error(`No position found for ${order.instrument}`);
    }

    // Calculate exit price and final P&L
    const exitPrice = order.averageFillPrice;
    const commission = order.fills.reduce((sum, fill) => sum + fill.commission, 0);

    const grossPnL =
      position.direction === 'long'
        ? (exitPrice - position.averageEntryPrice) * position.quantity
        : (position.averageEntryPrice - exitPrice) * position.quantity;

    const netPnL = grossPnL - position.totalCommission - commission;

    // Update position before closing
    const closedPosition: ManagedPosition = {
      ...position,
      currentPrice: exitPrice,
      unrealizedPnL: netPnL,
      realizedPnL: netPnL,
      exitOrderId: order.id,
      totalCommission: position.totalCommission + commission,
      fills: [...position.fills, ...order.fills],
      lastUpdated: new Date(),
    };

    // Remove from active positions
    this.positions.delete(order.instrument);

    // Store in closed positions history
    this.closedPositions.push(closedPosition);

    this.emit('position_closed', closedPosition);
  }

  /**
   * Update position with current market data
   */
  public async updatePosition(update: PositionUpdate): Promise<void> {
    const position = this.positions.get(update.positionId);
    if (!position) {
      return;
    }

    const updatedPosition: ManagedPosition = {
      ...position,
      currentPrice: update.currentPrice,
      positionValue: update.currentPrice * position.quantity,
      unrealizedPnL: update.unrealizedPnL,
      stopLoss: update.stopLoss || position.stopLoss,
      lastUpdated: update.timestamp,
    };

    this.positions.set(update.positionId, updatedPosition);
    this.emit('position_updated', updatedPosition);
  }

  /**
   * Get position by instrument
   */
  public getPosition(instrument: string): ManagedPosition | null {
    return this.positions.get(instrument) || null;
  }

  /**
   * Get all active positions
   */
  public getAllPositions(): ManagedPosition[] {
    return Array.from(this.positions.values());
  }

  /**
   * Get closed positions
   */
  public getClosedPositions(limit?: number): ManagedPosition[] {
    return limit
      ? this.closedPositions.slice(-limit)
      : [...this.closedPositions];
  }

  /**
   * Calculate position metrics
   */
  public calculatePositionMetrics(position: ManagedPosition): {
    returnPercent: number;
    riskRewardRatio: number;
    holdingPeriod: number;
    efficiency: number;
  } {
    const returnPercent =
      ((position.currentPrice - position.averageEntryPrice) / position.averageEntryPrice) * 100;

    const riskAmount = Math.abs(position.averageEntryPrice - position.stopLoss.currentStop);
    const potentialReward = Math.abs(position.currentPrice - position.averageEntryPrice);
    const riskRewardRatio = riskAmount > 0 ? potentialReward / riskAmount : 0;

    const holdingPeriod = Date.now() - position.openedAt.getTime();

    const efficiency = holdingPeriod > 0
      ? (position.unrealizedPnL / (holdingPeriod / (1000 * 60 * 60 * 24))) // P&L per day
      : 0;

    return {
      returnPercent,
      riskRewardRatio,
      holdingPeriod,
      efficiency,
    };
  }

  /**
   * Reconcile positions with broker
   */
  public async reconcileWithBroker(): Promise<PositionReconciliation> {
    const frameworkPositions = this.getAllPositions();
    const brokerPositions = await this.venue.getPositions();
    const discrepancies: PositionDiscrepancy[] = [];

    // Create maps for easy lookup
    const frameworkMap = new Map(frameworkPositions.map(p => [p.instrument, p]));
    const brokerMap = new Map(brokerPositions.map(p => [p.instrument, p]));

    // Check all framework positions
    for (const [instrument, fwPosition] of frameworkMap) {
      const brokerPosition = brokerMap.get(instrument);

      if (!brokerPosition) {
        // Position exists in framework but not in broker
        discrepancies.push({
          instrument,
          frameworkQuantity: fwPosition.quantity,
          brokerQuantity: 0,
          difference: fwPosition.quantity,
          severity: 'high',
          reason: 'Position exists in framework but not in broker',
        });
      } else if (Math.abs(fwPosition.quantity - brokerPosition.quantity) > 0.001) {
        // Quantity mismatch
        const difference = fwPosition.quantity - brokerPosition.quantity;
        discrepancies.push({
          instrument,
          frameworkQuantity: fwPosition.quantity,
          brokerQuantity: brokerPosition.quantity,
          difference,
          severity: Math.abs(difference) > fwPosition.quantity * 0.1 ? 'high' : 'medium',
          reason: 'Quantity mismatch between framework and broker',
        });
      }
    }

    // Check for positions in broker but not in framework
    for (const [instrument, brokerPosition] of brokerMap) {
      if (!frameworkMap.has(instrument)) {
        discrepancies.push({
          instrument,
          frameworkQuantity: 0,
          brokerQuantity: brokerPosition.quantity,
          difference: -brokerPosition.quantity,
          severity: 'high',
          reason: 'Position exists in broker but not in framework',
        });
      }
    }

    const reconciliation: PositionReconciliation = {
      frameworkPositions,
      brokerPositions,
      discrepancies,
      lastReconciled: new Date(),
    };

    this.emit('reconciliation_complete', reconciliation);
    return reconciliation;
  }

  /**
   * Force sync position from broker
   */
  public async syncPositionFromBroker(instrument: string): Promise<void> {
    const brokerPositions = await this.venue.getPositions();
    const brokerPosition = brokerPositions.find(p => p.instrument === instrument);

    if (!brokerPosition) {
      // Position doesn't exist in broker, remove from framework
      this.positions.delete(instrument);
      return;
    }

    const frameworkPosition = this.positions.get(instrument);

    if (frameworkPosition) {
      // Update quantity to match broker
      const updatedPosition: ManagedPosition = {
        ...frameworkPosition,
        quantity: brokerPosition.quantity,
        currentPrice: brokerPosition.currentPrice,
        positionValue: brokerPosition.currentPrice * brokerPosition.quantity,
        unrealizedPnL: brokerPosition.unrealizedPnL,
        lastUpdated: new Date(),
      };
      this.positions.set(instrument, updatedPosition);
    }
  }

  /**
   * Create default stop-loss structure
   */
  private createDefaultStopLoss(entryPrice: number): AdaptiveStopLoss {
    return {
      initialStop: entryPrice * 0.98, // 2% stop as default
      currentStop: entryPrice * 0.98,
      percentileBased: {
        value: entryPrice * 0.02,
        percentile: 95,
        lookbackPeriod: 100,
        timeframe: 'H4' as any,
      },
      riskAmount: 0,
      timestamp: new Date(),
    };
  }

  /**
   * Get position statistics
   */
  public getPositionStats(): {
    totalPositions: number;
    totalValue: number;
    totalUnrealizedPnL: number;
    totalRealizedPnL: number;
    avgPositionSize: number;
    winningPositions: number;
    losingPositions: number;
  } {
    const positions = this.getAllPositions();
    const closedPositions = this.closedPositions;

    const totalPositions = positions.length;
    const totalValue = positions.reduce((sum, p) => sum + p.positionValue, 0);
    const totalUnrealizedPnL = positions.reduce((sum, p) => sum + p.unrealizedPnL, 0);
    const totalRealizedPnL = closedPositions.reduce((sum, p) => sum + p.realizedPnL, 0);
    const avgPositionSize = totalPositions > 0 ? totalValue / totalPositions : 0;
    const winningPositions = closedPositions.filter(p => p.realizedPnL > 0).length;
    const losingPositions = closedPositions.filter(p => p.realizedPnL < 0).length;

    return {
      totalPositions,
      totalValue,
      totalUnrealizedPnL,
      totalRealizedPnL,
      avgPositionSize,
      winningPositions,
      losingPositions,
    };
  }
}
