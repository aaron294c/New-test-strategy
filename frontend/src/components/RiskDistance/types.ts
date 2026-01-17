/**
 * Risk Distance Types
 * Deterministic support distance calculations for Risk-Adjusted Expectancy
 */

/**
 * Input data required for distance calculations
 */
export interface RiskDistanceInput {
  symbol: string;
  price: number | null;        // Current market price
  st_put: number | null;       // Short-term put support
  lt_put: number | null;       // Long-term put support
  q_put: number | null;        // Quarterly put support
  max_pain: number | null;     // Max pain level
  lower_ext: number | null;    // MBAD Lower Extension (blue line)
  nw_lower_band: number | null; // Nadaraya-Watson Lower Band
  last_update?: string;        // Optional timestamp
}

/**
 * Distance calculation for a single support level
 */
export interface SupportDistance {
  level_value: number | null;  // The support level price
  pct_dist: number | null;     // Signed % distance (see calculator.ts for formulas)
  abs_pct_dist: number | null; // Absolute value of pct_dist
  is_below: boolean | null;    // True if current price is below level
}

/**
 * Complete output for a single symbol
 * This JSON structure will be consumed by the composite score routine
 */
export interface RiskDistanceOutput {
  symbol: string;
  price: number | null;

  // ST Put Support
  st_put: number | null;
  pct_dist_st_put: number | null;
  abs_pct_dist_st_put: number | null;
  is_below_st_put: boolean | null;

  // LT Put Support
  lt_put: number | null;
  pct_dist_lt_put: number | null;
  abs_pct_dist_lt_put: number | null;
  is_below_lt_put: boolean | null;

  // Q Put Support
  q_put: number | null;
  pct_dist_q_put: number | null;
  abs_pct_dist_q_put: number | null;
  is_below_q_put: boolean | null;

  // Max Pain
  max_pain: number | null;
  pct_dist_max_pain: number | null;
  abs_pct_dist_max_pain: number | null;
  is_below_max_pain: boolean | null;

  // Lower Extension (MBAD Blue Line)
  lower_ext: number | null;
  pct_dist_lower_ext: number | null;
  abs_pct_dist_lower_ext: number | null;
  is_below_lower_ext: boolean | null;

  // Nadaraya-Watson Lower Band
  nw_lower_band: number | null;
  pct_dist_nw_lower_band: number | null;
  abs_pct_dist_nw_lower_band: number | null;
  is_below_nw_lower_band: boolean | null;

  last_update: string;
}

/**
 * Internal calculation result with all distances
 */
export interface RiskDistanceCalculation {
  st_put: SupportDistance;
  lt_put: SupportDistance;
  q_put: SupportDistance;
  max_pain: SupportDistance;
  lower_ext: SupportDistance;
  nw_lower_band: SupportDistance;
}
