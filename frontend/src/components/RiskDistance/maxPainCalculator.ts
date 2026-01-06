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

import { ParsedSymbolData } from '../GammaScanner/types';

export type ExpiryType = 'Auto-Detect' | 'Weekly Friday' | 'Monthly (3rd Fri)' | 'Manual Days';

export interface MaxPainSettings {
  // Mirrors the PineScript defaults shown in your screenshot
  expiryType: ExpiryType;
  manualDaysToExpiry: number;
  onlyHighConfidenceExpiries: boolean;
  maxPainStrikeCount: number;
  useGammaWeightedOI: boolean;
  dealerShortBias: number;
  confidenceThreshold: number;
  useDynamicPinZone: boolean;
  staticPinZonePct: number;
}

export const DEFAULT_MAX_PAIN_SETTINGS: MaxPainSettings = {
  expiryType: 'Auto-Detect',
  manualDaysToExpiry: 7,
  onlyHighConfidenceExpiries: true,
  maxPainStrikeCount: 35,
  useGammaWeightedOI: true,
  dealerShortBias: 0.65,
  confidenceThreshold: 0.7,
  useDynamicPinZone: true,
  staticPinZonePct: 2.0,
};

interface StrikeRow {
  strike: number;
  weight: number;
  callOI: number;
  putOI: number;
}

function isMajorWeeklySymbol(symbol: string): boolean {
  const prefix = symbol.substring(0, 3).toUpperCase();
  return prefix === 'SPY' || prefix === 'QQQ' || prefix === 'SPX' || prefix === 'NDX';
}

function daysUntilNextFriday(from: Date): number {
  // JS: 0=Sun .. 6=Sat, Friday=5
  const dow = from.getDay();
  let delta = (5 - dow + 7) % 7;
  // If it's already Friday, treat "next" as 7 days out (matches Pine intent after expiry)
  if (delta === 0) delta = 7;
  return delta;
}

function getThirdFridayOfMonth(year: number, month0Based: number): number {
  // month0Based: 0..11
  const first = new Date(year, month0Based, 1);
  const firstDow = first.getDay(); // 0..6
  const friday = 5;
  const daysToFirstFriday = (friday - firstDow + 7) % 7;
  const firstFriday = 1 + daysToFirstFriday;
  return firstFriday + 14;
}

function calculateExpiryDays(symbol: string, settings: MaxPainSettings, now: Date): number {
  if (settings.expiryType === 'Manual Days') return Math.max(1, settings.manualDaysToExpiry);

  const weeklyDays = daysUntilNextFriday(now);

  if (settings.expiryType === 'Weekly Friday') {
    if (settings.onlyHighConfidenceExpiries && !isMajorWeeklySymbol(symbol)) return 5;
    return weeklyDays;
  }

  if (settings.expiryType === 'Monthly (3rd Fri)') {
    const year = now.getFullYear();
    const month = now.getMonth();
    const today = now.getDate();
    const thirdFri = getThirdFridayOfMonth(year, month);
    if (today <= thirdFri) return Math.max(1, thirdFri - today);
    const nextMonth = month === 11 ? 0 : month + 1;
    const nextYear = month === 11 ? year + 1 : year;
    const thirdFriNext = getThirdFridayOfMonth(nextYear, nextMonth);
    return Math.max(1, (thirdFriNext - today) + 31);
  }

  // Auto-Detect: prefer weekly for major symbols, otherwise monthly
  if (isMajorWeeklySymbol(symbol)) return weeklyDays;

  const year = now.getFullYear();
  const month = now.getMonth();
  const today = now.getDate();
  const thirdFri = getThirdFridayOfMonth(year, month);
  let monthlyDays: number;
  if (today <= thirdFri) {
    monthlyDays = Math.max(1, thirdFri - today);
  } else {
    const nextMonth = month === 11 ? 0 : month + 1;
    const nextYear = month === 11 ? year + 1 : year;
    const thirdFriNext = getThirdFridayOfMonth(nextYear, nextMonth);
    monthlyDays = Math.max(1, (thirdFriNext - today) + 31);
  }

  // PineScript behavior: if "only high confidence" is enabled and monthly expiry is far,
  // fall back to a near-term default window.
  if (settings.onlyHighConfidenceExpiries && monthlyDays > 7) return 7;

  return monthlyDays;
}

function getExpiryTimeDecay(daysRemaining: number): number {
  if (daysRemaining <= 0) return 0.0;
  if (daysRemaining <= 1) return 2.0;
  if (daysRemaining <= 3) return 1.5;
  if (daysRemaining <= 5) return 1.2;
  if (daysRemaining <= 7) return 1.0;
  return 0.7;
}

function roundStrikeEnhanced(strike: number, currentPrice: number): number {
  if (currentPrice >= 500) return Math.round(strike / 10) * 10;
  if (currentPrice >= 100) return Math.round(strike / 5) * 5;
  if (currentPrice >= 20) return Math.round(strike / 2.5) * 2.5;
  return Math.round(strike);
}

function calculateDynamicPinZonePct(
  ivPercent: number | null | undefined,
  daysRemaining: number,
  currentPrice: number,
  confidence: number,
  regime: string | null | undefined,
  settings: MaxPainSettings
): number {
  if (!settings.useDynamicPinZone || !ivPercent || ivPercent <= 0 || currentPrice <= 0) return settings.staticPinZonePct;

  const dailyMovePct = (ivPercent / 100) / Math.sqrt(365);
  const timeFactor = getExpiryTimeDecay(daysRemaining);
  const confidenceFactor = 1.0 + (1.0 - confidence) * 0.5;

  const regimeFactor =
    regime && regime.includes('High Volatility') ? 1.4 : regime && regime.includes('Low Volatility') ? 0.7 : 1.0;

  const zonePct = dailyMovePct * timeFactor * confidenceFactor * regimeFactor * 100;
  return Math.max(0.5, Math.min(zonePct, 8.0));
}

/**
 * PineScript-style OI estimator (synthetic), integrating wall proximity and dealer bias.
 */
function estimateEnhancedOpenInterest(
  strike: number,
  currentPrice: number,
  isCall: boolean,
  gammaWallStrike: number | null,
  baseVolume: number,
  daysRemaining: number,
  settings: MaxPainSettings
): number {
  const distancePct = Math.abs(strike - currentPrice) / currentPrice;
  const baseFactor = 1 / (1 + distancePct * 8);
  const volatilityFactor = Math.pow(0.75, distancePct * 15);

  let wallProximityBoost = 1.0;
  if (settings.useGammaWeightedOI && gammaWallStrike !== null) {
    const wallDistance = Math.abs(strike - gammaWallStrike) / currentPrice;
    if (wallDistance < 0.02) wallProximityBoost = 2.5;
    else if (wallDistance < 0.05) wallProximityBoost = 1.6;
  }

  const baseOi = baseVolume * baseFactor * volatilityFactor * wallProximityBoost * 0.025;

  const dealerAdjustment = isCall ? 1.0 / settings.dealerShortBias : settings.dealerShortBias;

  const timeBias =
    daysRemaining <= 7 ? (isCall ? 0.9 : 1.4) : (isCall ? 1.0 : 1.2);

  const finalOi = baseOi * dealerAdjustment * timeBias;
  return Math.max(150, finalOi);
}

/**
 * Generate strike grid and weights similar to PineScript.
 */
function generateEnhancedStrikes(
  currentPrice: number,
  strikeCount: number,
  wallPut: number | null,
  wallCall: number | null,
  wallLtPut: number | null,
  wallLtCall: number | null,
  ivLevel: number | null | undefined
): { strikes: number[]; weights: number[] } {
  const ivToUse = ivLevel && ivLevel > 0 ? ivLevel : 25.0;
  const volFactor = ivToUse > 40 ? 0.2 : ivToUse > 25 ? 0.15 : 0.12;
  const strikeRange = currentPrice * volFactor;

  const minStrike = currentPrice - strikeRange;
  const maxStrike = currentPrice + strikeRange;
  const stepSize = (maxStrike - minStrike) / strikeCount;

  const strikes: number[] = [];
  const weights: number[] = [];

  for (let i = 0; i < strikeCount; i++) {
    const rawStrike = minStrike + i * stepSize;
    const roundedStrike = roundStrikeEnhanced(rawStrike, currentPrice);

    const distanceFactor = Math.abs(roundedStrike - currentPrice) / currentPrice;
    let weight = Math.exp(-distanceFactor * 5);

    let wallBoost = 1.0;
    if (wallPut !== null && Math.abs(roundedStrike - wallPut) / currentPrice < 0.03) wallBoost = 1.8;
    else if (wallCall !== null && Math.abs(roundedStrike - wallCall) / currentPrice < 0.03) wallBoost = 1.8;
    else if (wallLtPut !== null && Math.abs(roundedStrike - wallLtPut) / currentPrice < 0.03) wallBoost = 1.5;
    else if (wallLtCall !== null && Math.abs(roundedStrike - wallLtCall) / currentPrice < 0.03) wallBoost = 1.5;

    weight *= wallBoost;

    const last = strikes.length ? strikes[strikes.length - 1] : null;
    if (last === null || roundedStrike !== last) {
      strikes.push(roundedStrike);
      weights.push(weight);
    }
  }

  // Ensure key wall strikes are included (high weight)
  const wallValues: number[] = [];
  if (wallPut && wallPut > 0) wallValues.push(wallPut);
  if (wallCall && wallCall > 0) wallValues.push(wallCall);
  if (wallLtPut && wallLtPut > 0) wallValues.push(wallLtPut);
  if (wallLtCall && wallLtCall > 0) wallValues.push(wallLtCall);

  for (const wallStrike of wallValues) {
    const rounded = roundStrikeEnhanced(wallStrike, currentPrice);
    if (rounded < minStrike || rounded > maxStrike) continue;
    if (strikes.some(s => Math.abs(s - rounded) < 0.01)) continue;
    strikes.push(rounded);
    weights.push(2.0);
    if (strikes.length >= strikeCount + 10) break;
  }

  // Keep them ordered
  const zipped = strikes.map((s, idx) => ({ s, w: weights[idx] })).sort((a, b) => a.s - b.s);
  return { strikes: zipped.map(z => z.s), weights: zipped.map(z => z.w) };
}

function populateEnhancedOiData(
  currentPrice: number,
  activityScore: number | null | undefined,
  wallPut: number | null,
  wallCall: number | null,
  daysRemaining: number,
  strikes: number[],
  weights: number[],
  settings: MaxPainSettings
): StrikeRow[] {
  const activityToUse = activityScore ?? 3.0;
  const baseVolume = activityToUse >= 4 ? 800_000 : activityToUse >= 2.5 ? 600_000 : 400_000;

  return strikes.map((strike, idx) => {
    let relevantWall: number | null = null;
    if (wallPut !== null && wallCall !== null) {
      relevantWall = Math.abs(strike - wallPut) < Math.abs(strike - wallCall) ? wallPut : wallCall;
    } else if (wallPut !== null) {
      relevantWall = wallPut;
    } else if (wallCall !== null) {
      relevantWall = wallCall;
    } else {
      relevantWall = strike;
    }

    let callOi = estimateEnhancedOpenInterest(strike, currentPrice, true, relevantWall, baseVolume, daysRemaining, settings);
    let putOi = estimateEnhancedOpenInterest(strike, currentPrice, false, relevantWall, baseVolume, daysRemaining, settings);

    const weight = weights[idx] ?? 1.0;
    callOi *= weight;
    putOi *= weight;

    return { strike, weight, callOI: callOi, putOI: putOi };
  });
}

function calculateEnhancedMaxPain(
  currentPrice: number,
  daysRemaining: number,
  strikes: number[],
  weights: number[],
  rows: StrikeRow[]
): { maxPain: number; confidence: number } {
  if (!strikes.length || !rows.length) return { maxPain: currentPrice, confidence: 0.5 };

  let bestStrike = currentPrice;
  let minTotalPain = Number.POSITIVE_INFINITY;
  let maxTotalPain = 0;

  for (const testPrice of strikes) {
    let totalPain = 0;
    const timeDecayFactor = getExpiryTimeDecay(daysRemaining);

    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      const strike = row.strike;
      const weight = weights[i] ?? row.weight ?? 1.0;

      if (testPrice > strike) totalPain += row.callOI * (testPrice - strike) * timeDecayFactor * weight;
      if (testPrice < strike) totalPain += row.putOI * (strike - testPrice) * timeDecayFactor * weight;
    }

    maxTotalPain = Math.max(maxTotalPain, totalPain);
    if (totalPain < minTotalPain) {
      minTotalPain = totalPain;
      bestStrike = testPrice;
    }
  }

  let confidence = 0.5;
  if (maxTotalPain > 0) {
    const painSpread = (maxTotalPain - minTotalPain) / maxTotalPain;
    const baseConfidence = Math.min(0.95, painSpread * 1.2);
    const timeFactor = daysRemaining <= 3 ? 1.0 : daysRemaining <= 7 ? 0.9 : 0.7;
    confidence = baseConfidence * timeFactor;
  }

  return { maxPain: bestStrike, confidence };
}

/**
 * Calculate max pain level for a symbol
 * PineScript-aligned synthetic max pain (strike grid + estimated OI + confidence threshold).
 */
export function calculateMaxPain(
  symbol: ParsedSymbolData,
  opts?: {
    currentPriceOverride?: number;
    marketRegime?: string;
    settings?: Partial<MaxPainSettings>;
    now?: Date;
  }
): number | null {
  const settings: MaxPainSettings = { ...DEFAULT_MAX_PAIN_SETTINGS, ...(opts?.settings ?? {}) };
  const currentPrice = opts?.currentPriceOverride ?? symbol.currentPrice;
  if (!currentPrice || currentPrice <= 0) return null;

  const stPut = symbol.walls.find(w => w.type === 'put' && w.timeframe === 'swing')?.strike ?? null;
  const stCall = symbol.walls.find(w => w.type === 'call' && w.timeframe === 'swing')?.strike ?? null;
  const ltPut = symbol.walls.find(w => w.type === 'put' && w.timeframe === 'long')?.strike ?? null;
  const ltCall = symbol.walls.find(w => w.type === 'call' && w.timeframe === 'long')?.strike ?? null;

  const daysRemaining = calculateExpiryDays(symbol.symbol, settings, opts?.now ?? new Date());

  const { strikes, weights } = generateEnhancedStrikes(
    currentPrice,
    settings.maxPainStrikeCount,
    stPut,
    stCall,
    ltPut,
    ltCall,
    symbol.swingIV
  );

  const rows = populateEnhancedOiData(
    currentPrice,
    symbol.activityScore,
    stPut,
    stCall,
    daysRemaining,
    strikes,
    weights,
    settings
  );

  const { maxPain, confidence } = calculateEnhancedMaxPain(currentPrice, daysRemaining, strikes, weights, rows);

  const effectiveThreshold = Math.min(settings.confidenceThreshold, 0.5);
  if (confidence < effectiveThreshold) return null;

  // Round to reasonable precision
  return Math.round(maxPain * 100) / 100;
}

/**
 * Calculate max pain with detailed analysis
 */
export interface MaxPainAnalysis {
  maxPainLevel: number;
  currentPrice: number;
  distanceToPain: number;
  distancePct: number;
  pinRisk: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  dynamicPinZonePct: number;
  confidence: number;
  totalCallOI: number;
  totalPutOI: number;
  putCallRatio: number;
  nearestStrike: number;
}

export function calculateMaxPainAnalysis(
  symbol: ParsedSymbolData,
  opts?: {
    currentPriceOverride?: number;
    marketRegime?: string;
    settings?: Partial<MaxPainSettings>;
    now?: Date;
  }
): MaxPainAnalysis | null {
  const settings: MaxPainSettings = { ...DEFAULT_MAX_PAIN_SETTINGS, ...(opts?.settings ?? {}) };
  const currentPrice = opts?.currentPriceOverride ?? symbol.currentPrice;
  const maxPainLevel = calculateMaxPain(symbol, opts);

  if (maxPainLevel === null) {
    return null;
  }

  const stPut = symbol.walls.find(w => w.type === 'put' && w.timeframe === 'swing')?.strike ?? null;
  const stCall = symbol.walls.find(w => w.type === 'call' && w.timeframe === 'swing')?.strike ?? null;
  const ltPut = symbol.walls.find(w => w.type === 'put' && w.timeframe === 'long')?.strike ?? null;
  const ltCall = symbol.walls.find(w => w.type === 'call' && w.timeframe === 'long')?.strike ?? null;

  const daysRemaining = calculateExpiryDays(symbol.symbol, settings, opts?.now ?? new Date());

  const { strikes, weights } = generateEnhancedStrikes(
    currentPrice,
    settings.maxPainStrikeCount,
    stPut,
    stCall,
    ltPut,
    ltCall,
    symbol.swingIV
  );

  const rows = populateEnhancedOiData(
    currentPrice,
    symbol.activityScore,
    stPut,
    stCall,
    daysRemaining,
    strikes,
    weights,
    settings
  );

  let totalCallOI = 0;
  let totalPutOI = 0;
  for (const row of rows) {
    totalCallOI += row.callOI;
    totalPutOI += row.putOI;
  }

  // Distance calculations
  const distanceToPain = maxPainLevel - currentPrice;
  const distancePct = (distanceToPain / currentPrice) * 100;

  const { confidence } = calculateEnhancedMaxPain(currentPrice, daysRemaining, strikes, weights, rows);
  const dynamicPinZonePct = calculateDynamicPinZonePct(
    symbol.swingIV,
    daysRemaining,
    currentPrice,
    confidence,
    opts?.marketRegime,
    settings
  );

  const absPct = Math.abs(distancePct);
  const pinRisk: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' =
    absPct <= dynamicPinZonePct * 0.5
      ? 'CRITICAL'
      : absPct <= dynamicPinZonePct
        ? 'HIGH'
        : absPct <= dynamicPinZonePct * 2
          ? 'MEDIUM'
          : 'LOW';

  // Find nearest strike to max pain
  const nearestStrike = strikes.length
    ? strikes.reduce((prev, curr) =>
        Math.abs(curr - maxPainLevel) < Math.abs(prev - maxPainLevel) ? curr : prev
      )
    : maxPainLevel;

  return {
    maxPainLevel,
    currentPrice,
    distanceToPain,
    distancePct,
    pinRisk,
    dynamicPinZonePct,
    confidence,
    totalCallOI,
    totalPutOI,
    putCallRatio: totalCallOI > 0 ? totalPutOI / totalCallOI : 0,
    nearestStrike,
  };
}
