/**
 * Risk Distance Calculator
 * Deterministic calculations for support distance metrics
 * NO subjective logic, NO recommendations - pure math only
 */

import { RiskDistanceInput, RiskDistanceOutput, SupportDistance } from './types';

/**
 * Calculate signed % distance from price to a support level
 * Formula: pct_dist = (price - level) / level * 100
 *
 * Returns:
 *   - Positive if price is above level
 *   - Negative if price is below level
 *   - null if either price or level is missing
 */
export const calculateDistance = (price: number | null, level: number | null): SupportDistance => {
  // Handle missing data
  if (price === null || level === null || level === 0) {
    return {
      level_value: level,
      pct_dist: null,
      abs_pct_dist: null,
      is_below: null,
    };
  }

  // Calculate signed % distance
  const pct_dist = ((price - level) / level) * 100;

  // Round to 2 decimal places
  const pct_dist_rounded = Math.round(pct_dist * 100) / 100;

  // Calculate absolute distance
  const abs_pct_dist = Math.abs(pct_dist_rounded);

  // Determine if level is below current price
  const is_below = level < price;

  return {
    level_value: level,
    pct_dist: pct_dist_rounded,
    abs_pct_dist: abs_pct_dist,
    is_below: is_below,
  };
};

/**
 * Calculate signed % distance using PineScript-style normalization (move from current price)
 * Formula: pct_dist = (level - price) / price * 100
 *
 * Returns:
 *   - Positive if level is above current price
 *   - Negative if level is below current price
 *   - null if either price or level is missing
 */
export const calculateDistanceFromCurrentPrice = (
  price: number | null,
  level: number | null
): SupportDistance => {
  if (price === null || level === null || price === 0) {
    return {
      level_value: level,
      pct_dist: null,
      abs_pct_dist: null,
      is_below: null,
    };
  }

  const pct_dist = ((level - price) / price) * 100;
  const pct_dist_rounded = Math.round(pct_dist * 100) / 100;

  return {
    level_value: level,
    pct_dist: pct_dist_rounded,
    abs_pct_dist: Math.abs(pct_dist_rounded),
    is_below: level < price,
  };
};

/**
 * Calculate all risk distances for a symbol
 * Pure deterministic function - no side effects
 */
export const calculateRiskDistances = (input: RiskDistanceInput): RiskDistanceOutput => {
  const { symbol, price, st_put, lt_put, q_put, max_pain, lower_ext, nw_lower_band, last_update } = input;

  // Distance convention: normalized to current price (move required from current price)
  const st_put_dist = calculateDistanceFromCurrentPrice(price, st_put);
  const lt_put_dist = calculateDistanceFromCurrentPrice(price, lt_put);
  const q_put_dist = calculateDistanceFromCurrentPrice(price, q_put);
  const max_pain_dist = calculateDistanceFromCurrentPrice(price, max_pain);
  const lower_ext_dist = calculateDistanceFromCurrentPrice(price, lower_ext);
  const nw_lower_band_dist = calculateDistanceFromCurrentPrice(price, nw_lower_band);

  // Build output in exact format for composite score consumption
  return {
    symbol,
    price,

    // ST Put Support
    st_put,
    pct_dist_st_put: st_put_dist.pct_dist,
    abs_pct_dist_st_put: st_put_dist.abs_pct_dist,
    is_below_st_put: st_put_dist.is_below,

    // LT Put Support
    lt_put,
    pct_dist_lt_put: lt_put_dist.pct_dist,
    abs_pct_dist_lt_put: lt_put_dist.abs_pct_dist,
    is_below_lt_put: lt_put_dist.is_below,

    // Q Put Support
    q_put,
    pct_dist_q_put: q_put_dist.pct_dist,
    abs_pct_dist_q_put: q_put_dist.abs_pct_dist,
    is_below_q_put: q_put_dist.is_below,

    // Max Pain
    max_pain,
    pct_dist_max_pain: max_pain_dist.pct_dist,
    abs_pct_dist_max_pain: max_pain_dist.abs_pct_dist,
    is_below_max_pain: max_pain_dist.is_below,

    // Lower Extension (MBAD Blue Line)
    lower_ext,
    pct_dist_lower_ext: lower_ext_dist.pct_dist,
    abs_pct_dist_lower_ext: lower_ext_dist.abs_pct_dist,
    is_below_lower_ext: lower_ext_dist.is_below,

    // Nadaraya-Watson Lower Band
    nw_lower_band,
    pct_dist_nw_lower_band: nw_lower_band_dist.pct_dist,
    abs_pct_dist_nw_lower_band: nw_lower_band_dist.abs_pct_dist,
    is_below_nw_lower_band: nw_lower_band_dist.is_below,

    last_update: last_update || new Date().toISOString(),
  };
};

/**
 * Find the closest support level (by absolute distance)
 * Returns: 'st_put' | 'lt_put' | 'q_put' | 'max_pain' | 'lower_ext' | 'nw_lower_band' | null
 */
export const findClosestSupport = (output: RiskDistanceOutput): string | null => {
  const distances = [
    { name: 'st_put', dist: output.abs_pct_dist_st_put },
    { name: 'lt_put', dist: output.abs_pct_dist_lt_put },
    { name: 'q_put', dist: output.abs_pct_dist_q_put },
    { name: 'max_pain', dist: output.abs_pct_dist_max_pain },
    { name: 'lower_ext', dist: output.abs_pct_dist_lower_ext },
    { name: 'nw_lower_band', dist: output.abs_pct_dist_nw_lower_band },
  ];

  // Filter out null distances
  const valid = distances.filter(d => d.dist !== null);

  if (valid.length === 0) return null;

  // Find minimum
  let closest = valid[0];
  for (const d of valid) {
    if (d.dist! < closest.dist!) {
      closest = d;
    }
  }

  return closest.name;
};

/**
 * Format distance for display
 * Returns: "+2.50%" or "-1.23%" or "N/A"
 */
export const formatDistance = (pct_dist: number | null): string => {
  if (pct_dist === null) return 'N/A';
  const sign = pct_dist >= 0 ? '+' : '';
  return `${sign}${pct_dist.toFixed(2)}%`;
};

/**
 * Format price for display
 * Returns: "$5,724.09" or "N/A"
 */
export const formatPrice = (price: number | null): string => {
  if (price === null) return 'N/A';
  return `$${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

/**
 * Export multiple symbols as JSON
 * For integration with composite score system
 */
export const exportToJSON = (outputs: RiskDistanceOutput[]): string => {
  return JSON.stringify(outputs, null, 2);
};

/**
 * Export as CSV for spreadsheet analysis
 */
export const exportToCSV = (outputs: RiskDistanceOutput[]): string => {
  const headers = [
    'symbol',
    'price',
    'st_put',
    'pct_dist_st_put',
    'is_below_st_put',
    'lt_put',
    'pct_dist_lt_put',
    'is_below_lt_put',
    'q_put',
    'pct_dist_q_put',
    'is_below_q_put',
    'max_pain',
    'pct_dist_max_pain',
    'is_below_max_pain',
    'lower_ext',
    'pct_dist_lower_ext',
    'is_below_lower_ext',
    'nw_lower_band',
    'pct_dist_nw_lower_band',
    'is_below_nw_lower_band',
    'last_update',
  ];

  const rows = outputs.map(o => [
    o.symbol,
    o.price,
    o.st_put,
    o.pct_dist_st_put,
    o.is_below_st_put,
    o.lt_put,
    o.pct_dist_lt_put,
    o.is_below_lt_put,
    o.q_put,
    o.pct_dist_q_put,
    o.is_below_q_put,
    o.max_pain,
    o.pct_dist_max_pain,
    o.is_below_max_pain,
    o.lower_ext,
    o.pct_dist_lower_ext,
    o.is_below_lower_ext,
    o.nw_lower_band,
    o.pct_dist_nw_lower_band,
    o.is_below_nw_lower_band,
    o.last_update,
  ]);

  return [headers, ...rows].map(row => row.join(',')).join('\n');
};
