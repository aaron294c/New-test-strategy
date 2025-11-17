/**
 * Max Pain Calculator
 * Based on options theory: Max pain is the strike price where option holders
 * (both call and put) experience maximum loss at expiration.
 *
 * CRITICAL: Max pain calculation uses options data AROUND 7 days DTE (5-15 day range).
 * This targets weekly options expiring on the nearest Friday, which dominate
 * immediate price action.
 *
 * Algorithm:
 * 1. Filter walls to short-term options (5-15 DTE, preferring ~7 days)
 * 2. If no walls in range, use closest DTE within 30 days
 * 3. For each potential expiration price (test strike)
 * 4. Calculate total pain = sum of all ITM option losses
 *    - Call pain: If price > strike, pain = call_OI * (price - strike)
 *    - Put pain:  If price < strike, pain = put_OI * (strike - price)
 * 5. Find strike with minimum total pain
 */

import { ParsedSymbolData, GammaWall } from '../GammaScanner/types';

// DTE range for weekly options (approximately 7 days, allow 5-15 day range)
const MIN_DTE_THRESHOLD = 5;
const MAX_DTE_THRESHOLD = 15;
const TARGET_DTE = 7;

interface StrikeData {
  strike: number;
  callOI: number;
  putOI: number;
  callGEX: number;
  putGEX: number;
}

/**
 * Estimate open interest based on GEX and distance from current price
 */
function estimateOpenInterest(
  strike: number,
  currentPrice: number,
  gex: number,
  isCall: boolean
): number {
  // Convert GEX to estimated contract volume
  // GEX is gamma exposure in millions, use as proxy for open interest
  const baseOI = Math.abs(gex) * 100; // Scale factor

  // Distance decay: OI typically higher near current price
  const distancePct = Math.abs(strike - currentPrice) / currentPrice;
  const decayFactor = Math.exp(-distancePct * 8); // Exponential decay

  return baseOI * decayFactor;
}

/**
 * Calculate pain at a specific expiration price
 */
function calculatePainAtPrice(
  expirationPrice: number,
  strikes: StrikeData[]
): number {
  let totalPain = 0;

  for (const strike of strikes) {
    // Call pain: calls are ITM when price > strike
    if (expirationPrice > strike.strike) {
      totalPain += strike.callOI * (expirationPrice - strike.strike);
    }

    // Put pain: puts are ITM when price < strike
    if (expirationPrice < strike.strike) {
      totalPain += strike.putOI * (strike.strike - expirationPrice);
    }
  }

  return totalPain;
}

/**
 * Generate test prices around current price
 */
function generateTestPrices(
  currentPrice: number,
  minStrike: number,
  maxStrike: number,
  numTests: number = 50
): number[] {
  const testPrices: number[] = [];
  const step = (maxStrike - minStrike) / numTests;

  for (let i = 0; i <= numTests; i++) {
    const price = minStrike + i * step;
    testPrices.push(price);
  }

  return testPrices;
}

/**
 * Calculate max pain level for a symbol
 * Uses walls with DTE around 7 days (5-15 day range for weekly options)
 */
export function calculateMaxPain(symbol: ParsedSymbolData): number | null {
  const { walls, currentPrice } = symbol;

  if (walls.length === 0) {
    return null;
  }

  // Filter to short-term options (5-15 DTE, targeting ~7 days)
  // This captures weekly options expiring on the nearest Friday
  const shortTermWalls = walls.filter(
    wall => wall.dte >= MIN_DTE_THRESHOLD && wall.dte <= MAX_DTE_THRESHOLD
  );

  // If no walls in the 5-15 range, try to find the closest to 7 days
  if (shortTermWalls.length === 0) {
    // Find walls closest to target DTE
    const sortedByDte = [...walls].sort((a, b) =>
      Math.abs(a.dte - TARGET_DTE) - Math.abs(b.dte - TARGET_DTE)
    );

    // Use the closest DTE if it's within 30 days
    if (sortedByDte.length > 0 && sortedByDte[0].dte <= 30) {
      const closestDte = sortedByDte[0].dte;
      shortTermWalls.push(...walls.filter(w => w.dte === closestDte));
    }
  }

  if (shortTermWalls.length === 0) {
    // No suitable options available
    return null;
  }

  // Extract strike data from SHORT-TERM walls ONLY
  const strikeMap = new Map<number, StrikeData>();

  for (const wall of shortTermWalls) {
    if (!strikeMap.has(wall.strike)) {
      strikeMap.set(wall.strike, {
        strike: wall.strike,
        callOI: 0,
        putOI: 0,
        callGEX: 0,
        putGEX: 0,
      });
    }

    const strikeData = strikeMap.get(wall.strike)!;

    if (wall.type === 'call') {
      strikeData.callGEX += wall.gex;
      strikeData.callOI += estimateOpenInterest(wall.strike, currentPrice, wall.gex, true);
    } else {
      strikeData.putGEX += wall.gex;
      strikeData.putOI += estimateOpenInterest(wall.strike, currentPrice, wall.gex, false);
    }
  }

  const strikes = Array.from(strikeMap.values());

  // Sort strikes by value
  strikes.sort((a, b) => a.strike - b.strike);

  if (strikes.length === 0) {
    return null;
  }

  // Determine price range to test
  const allStrikes = strikes.map(s => s.strike);
  const minStrike = Math.min(...allStrikes);
  const maxStrike = Math.max(...allStrikes);

  // Generate test prices
  const testPrices = generateTestPrices(currentPrice, minStrike, maxStrike, 100);

  // Calculate pain at each test price
  let minPain = Infinity;
  let maxPainLevel = currentPrice;

  for (const testPrice of testPrices) {
    const pain = calculatePainAtPrice(testPrice, strikes);

    if (pain < minPain) {
      minPain = pain;
      maxPainLevel = testPrice;
    }
  }

  // Round to reasonable precision
  return Math.round(maxPainLevel * 100) / 100;
}

/**
 * Calculate max pain with detailed analysis
 */
export interface MaxPainAnalysis {
  maxPainLevel: number;
  currentPrice: number;
  distanceToPain: number;
  distancePct: number;
  pinRisk: 'HIGH' | 'MEDIUM' | 'LOW';
  totalCallOI: number;
  totalPutOI: number;
  putCallRatio: number;
  nearestStrike: number;
  painAtCurrent: number;
  painAtMaxPain: number;
}

export function calculateMaxPainAnalysis(
  symbol: ParsedSymbolData
): MaxPainAnalysis | null {
  const maxPainLevel = calculateMaxPain(symbol);

  if (maxPainLevel === null) {
    return null;
  }

  const { walls, currentPrice } = symbol;

  // Filter to short-term options (5-15 DTE, targeting ~7 days)
  const shortTermWalls = walls.filter(
    wall => wall.dte >= MIN_DTE_THRESHOLD && wall.dte <= MAX_DTE_THRESHOLD
  );

  // Fallback to closest DTE if no walls in range
  if (shortTermWalls.length === 0) {
    const sortedByDte = [...walls].sort((a, b) =>
      Math.abs(a.dte - TARGET_DTE) - Math.abs(b.dte - TARGET_DTE)
    );
    if (sortedByDte.length > 0 && sortedByDte[0].dte <= 30) {
      const closestDte = sortedByDte[0].dte;
      shortTermWalls.push(...walls.filter(w => w.dte === closestDte));
    }
  }

  if (shortTermWalls.length === 0) {
    return null;
  }

  // Calculate aggregate metrics from SHORT-TERM walls ONLY
  let totalCallOI = 0;
  let totalPutOI = 0;

  const strikeData: StrikeData[] = [];
  const strikeMap = new Map<number, StrikeData>();

  for (const wall of shortTermWalls) {
    if (!strikeMap.has(wall.strike)) {
      strikeMap.set(wall.strike, {
        strike: wall.strike,
        callOI: 0,
        putOI: 0,
        callGEX: 0,
        putGEX: 0,
      });
    }

    const data = strikeMap.get(wall.strike)!;
    const oi = estimateOpenInterest(wall.strike, currentPrice, wall.gex, wall.type === 'call');

    if (wall.type === 'call') {
      data.callOI += oi;
      data.callGEX += wall.gex;
      totalCallOI += oi;
    } else {
      data.putOI += oi;
      data.putGEX += wall.gex;
      totalPutOI += oi;
    }
  }

  strikeData.push(...Array.from(strikeMap.values()));

  // Distance calculations
  const distanceToPain = maxPainLevel - currentPrice;
  const distancePct = (distanceToPain / currentPrice) * 100;

  // Pin risk: HIGH if within 2%, MEDIUM if within 5%, LOW otherwise
  const absPct = Math.abs(distancePct);
  const pinRisk: 'HIGH' | 'MEDIUM' | 'LOW' =
    absPct < 2 ? 'HIGH' : absPct < 5 ? 'MEDIUM' : 'LOW';

  // Find nearest strike to max pain
  const strikes = Array.from(strikeMap.keys()).sort((a, b) => a - b);
  const nearestStrike = strikes.reduce((prev, curr) =>
    Math.abs(curr - maxPainLevel) < Math.abs(prev - maxPainLevel) ? curr : prev
  );

  // Calculate pain at current price vs max pain
  const painAtCurrent = calculatePainAtPrice(currentPrice, strikeData);
  const painAtMaxPain = calculatePainAtPrice(maxPainLevel, strikeData);

  return {
    maxPainLevel,
    currentPrice,
    distanceToPain,
    distancePct,
    pinRisk,
    totalCallOI,
    totalPutOI,
    putCallRatio: totalCallOI > 0 ? totalPutOI / totalCallOI : 0,
    nearestStrike,
    painAtCurrent,
    painAtMaxPain,
  };
}
