/**
 * Capital Allocation Engine
 *
 * Manages position sizing and portfolio allocation based on:
 * - Risk-adjusted composite scores
 * - Available capital and risk limits
 * - Diversification rules
 * - Dynamic rebalancing
 */

import {
  AllocationParameters,
  AllocationDecision,
  CompositeScore,
  Position,
  AdaptiveStopLoss,
  MarketData,
} from '../core/types';

/**
 * Portfolio constraints for allocation
 */
export interface PortfolioConstraints {
  currentPositions: Position[];
  availableCapital: number;
  currentRiskExposure: number;
}

/**
 * Allocation result with detailed breakdown
 */
export interface AllocationResult {
  decisions: AllocationDecision[];
  totalAllocated: number;
  totalRisk: number;
  remainingCapital: number;
  rejectedInstruments: {
    instrument: string;
    reason: string;
  }[];
}

/**
 * Main capital allocation engine
 */
export class AllocationEngine {
  private params: AllocationParameters;

  constructor(params: AllocationParameters) {
    this.params = params;
  }

  /**
   * Allocate capital across instruments based on scores
   */
  public allocateCapital(
    scores: CompositeScore[],
    constraints: PortfolioConstraints,
    marketDataMap: Map<string, MarketData>,
    stopLossMap: Map<string, AdaptiveStopLoss>
  ): AllocationResult {
    // Filter by minimum score
    const qualified = scores.filter((s) => s.totalScore >= this.params.minScore);

    // Sort by score (highest first)
    const sorted = [...qualified].sort((a, b) => b.totalScore - a.totalScore);

    const decisions: AllocationDecision[] = [];
    const rejected: { instrument: string; reason: string }[] = [];

    let allocatedCapital = 0;
    let totalRisk = constraints.currentRiskExposure;

    // Check if we're already at max positions
    const availableSlots =
      this.params.maxPositions - constraints.currentPositions.length;

    if (availableSlots <= 0) {
      sorted.forEach((score) => {
        rejected.push({
          instrument: score.instrument,
          reason: 'Maximum positions reached',
        });
      });

      return this.createResult(decisions, rejected, constraints.availableCapital);
    }

    // Allocate to top instruments
    let priority = 1;
    for (const score of sorted) {
      // Check if we have slots left
      if (decisions.length >= availableSlots) {
        rejected.push({
          instrument: score.instrument,
          reason: 'No available position slots',
        });
        continue;
      }

      // Check if instrument already has a position
      if (this.hasPosition(score.instrument, constraints.currentPositions)) {
        rejected.push({
          instrument: score.instrument,
          reason: 'Position already exists',
        });
        continue;
      }

      // Get market data and stop loss
      const marketData = marketDataMap.get(score.instrument);
      const stopLoss = stopLossMap.get(score.instrument);

      if (!marketData || !stopLoss) {
        rejected.push({
          instrument: score.instrument,
          reason: 'Missing market data or stop loss',
        });
        continue;
      }

      // Calculate position size based on risk
      const allocation = this.calculateAllocation(
        score,
        marketData,
        stopLoss,
        constraints.availableCapital - allocatedCapital,
        this.params.maxTotalRisk - totalRisk
      );

      if (!allocation) {
        rejected.push({
          instrument: score.instrument,
          reason: 'Risk limits exceeded or insufficient capital',
        });
        continue;
      }

      // Check diversification rules
      if (!this.checkDiversification(score.instrument, decisions, constraints)) {
        rejected.push({
          instrument: score.instrument,
          reason: 'Diversification limits exceeded',
        });
        continue;
      }

      // Add allocation decision
      decisions.push({
        instrument: score.instrument,
        allocatedCapital: allocation.capital,
        positionSize: allocation.size,
        riskAmount: allocation.risk,
        justification: allocation.justification,
        score: score.totalScore,
        priority: priority++,
        timestamp: new Date(),
      });

      allocatedCapital += allocation.capital;
      totalRisk += allocation.risk;
    }

    return this.createResult(
      decisions,
      rejected,
      constraints.availableCapital - allocatedCapital
    );
  }

  /**
   * Calculate allocation for a single instrument
   */
  private calculateAllocation(
    score: CompositeScore,
    marketData: MarketData,
    stopLoss: AdaptiveStopLoss,
    availableCapital: number,
    availableRisk: number
  ): { capital: number; size: number; risk: number; justification: string } | null {
    const currentPrice = marketData.currentPrice;
    const stopPrice = stopLoss.currentStop;
    const stopDistance = Math.abs(currentPrice - stopPrice);

    // Calculate maximum risk for this trade
    const maxTradeRisk = this.params.totalCapital * this.params.maxRiskPerTrade;

    // Don't exceed remaining risk budget
    const tradeRisk = Math.min(maxTradeRisk, availableRisk);

    if (tradeRisk <= 0) {
      return null; // No risk budget available
    }

    // Calculate position size based on risk
    // Risk = PositionSize * StopDistance
    // Therefore: PositionSize = Risk / StopDistance
    const positionSize = stopDistance > 0 ? tradeRisk / stopDistance : 0;

    if (positionSize <= 0) {
      return null;
    }

    // Calculate required capital
    const requiredCapital = positionSize * currentPrice;

    // Check if we have enough capital
    if (requiredCapital > availableCapital) {
      // Scale down if insufficient capital
      const scaledSize = availableCapital / currentPrice;
      const scaledRisk = scaledSize * stopDistance;

      if (scaledRisk > maxTradeRisk) {
        return null; // Even scaled position exceeds risk limit
      }

      return {
        capital: availableCapital,
        size: scaledSize,
        risk: scaledRisk,
        justification: `Capital-limited allocation (score: ${score.totalScore.toFixed(2)})`,
      };
    }

    // Score-based allocation adjustment
    // Higher scores get slightly larger allocations (within limits)
    const scoreMultiplier = 0.8 + score.totalScore * 0.4; // Range: 0.8 to 1.2
    const adjustedRisk = Math.min(tradeRisk * scoreMultiplier, maxTradeRisk, availableRisk);
    const adjustedSize = adjustedRisk / stopDistance;
    const adjustedCapital = adjustedSize * currentPrice;

    return {
      capital: adjustedCapital,
      size: adjustedSize,
      risk: adjustedRisk,
      justification: `Risk-based allocation with score adjustment (${(scoreMultiplier * 100).toFixed(0)}%, score: ${score.totalScore.toFixed(2)})`,
    };
  }

  /**
   * Check if instrument already has a position
   */
  private hasPosition(instrument: string, positions: Position[]): boolean {
    return positions.some((p) => p.instrument === instrument);
  }

  /**
   * Check diversification rules
   */
  private checkDiversification(
    instrument: string,
    decisions: AllocationDecision[],
    constraints: PortfolioConstraints
  ): boolean {
    if (!this.params.diversificationRules) {
      return true; // No diversification rules
    }

    // Check sector concentration (simplified - would need sector mapping in production)
    const { maxPerSector, maxCorrelatedPositions } = this.params.diversificationRules;

    if (maxPerSector) {
      // In production, check actual sector allocation
      // For now, assume uniform distribution
      const sectorAllocation =
        (decisions.length + constraints.currentPositions.length) /
        this.params.maxPositions;

      if (sectorAllocation > maxPerSector) {
        return false;
      }
    }

    if (maxCorrelatedPositions) {
      // In production, calculate actual correlation
      // For now, use simple count check
      if (decisions.length >= maxCorrelatedPositions) {
        return false;
      }
    }

    return true;
  }

  /**
   * Create allocation result
   */
  private createResult(
    decisions: AllocationDecision[],
    rejected: { instrument: string; reason: string }[],
    remainingCapital: number
  ): AllocationResult {
    const totalAllocated = decisions.reduce((sum, d) => sum + d.allocatedCapital, 0);
    const totalRisk = decisions.reduce((sum, d) => sum + d.riskAmount, 0);

    return {
      decisions,
      totalAllocated,
      totalRisk,
      remainingCapital,
      rejectedInstruments: rejected,
    };
  }

  /**
   * Rebalance existing positions based on new scores
   */
  public rebalancePortfolio(
    currentPositions: Position[],
    newScores: CompositeScore[],
    availableCapital: number
  ): {
    closePositions: string[];
    adjustPositions: { instrument: string; newSize: number }[];
    reason: string;
  } {
    const closePositions: string[] = [];
    const adjustPositions: { instrument: string; newSize: number }[] = [];

    // Check each position against minimum score
    currentPositions.forEach((position) => {
      const score = newScores.find((s) => s.instrument === position.instrument);

      if (!score || score.totalScore < this.params.minScore) {
        closePositions.push(position.instrument);
      } else {
        // Optionally adjust position size based on score changes
        // For now, keep existing positions if they meet minimum score
      }
    });

    return {
      closePositions,
      adjustPositions,
      reason: 'Rebalancing based on updated composite scores',
    };
  }

  /**
   * Calculate portfolio metrics
   */
  public calculatePortfolioMetrics(positions: Position[]): {
    totalValue: number;
    totalRisk: number;
    riskPercentage: number;
    utilizationPercentage: number;
    averageScore: number;
  } {
    const totalValue = positions.reduce((sum, p) => sum + p.positionValue, 0);
    const totalRisk = positions.reduce((sum, p) => sum + p.riskAmount, 0);
    const riskPercentage = (totalRisk / this.params.totalCapital) * 100;
    const utilizationPercentage =
      (positions.length / this.params.maxPositions) * 100;
    const averageScore =
      positions.length > 0
        ? positions.reduce((sum, p) => sum + p.compositeScore.totalScore, 0) /
          positions.length
        : 0;

    return {
      totalValue,
      totalRisk,
      riskPercentage,
      utilizationPercentage,
      averageScore,
    };
  }

  /**
   * Update allocation parameters
   */
  public updateParameters(params: Partial<AllocationParameters>): void {
    this.params = {
      ...this.params,
      ...params,
    };
  }

  /**
   * Get current parameters
   */
  public getParameters(): AllocationParameters {
    return { ...this.params };
  }
}
