/**
 * Lower Extension Distance Calculations
 * Computes signed percent distance, breach metrics, and proximity scores
 */

export interface HistoricalPrice {
  timestamp: string | number;
  price: number;
}

export interface IndicatorData {
  symbol: string;
  price: number;
  lower_ext: number;
  timestamp?: string;
  last_update?: string;
  historical_prices?: HistoricalPrice[];
  // Pre-calculated metrics from backend API
  pct_dist_lower_ext?: number;
  is_below_lower_ext?: boolean;
  abs_pct_dist_lower_ext?: number;
  min_pct_dist_30d?: number;
  median_abs_pct_dist_30d?: number;
  breach_count_30d?: number;
  breach_rate_30d?: number;
  recent_breached?: boolean;
  proximity_score_30d?: number;
  all_levels?: any;
}

export interface LowerExtMetrics {
  symbol: string;
  price: number;
  lower_ext: number;
  pct_dist_lower_ext: number;
  is_below_lower_ext: boolean;
  abs_pct_dist_lower_ext: number;
  min_pct_dist_30d: number;
  median_abs_pct_dist_30d: number;
  breach_count_30d: number;
  breach_rate_30d: number;
  recent_breached: boolean;
  proximity_score_30d: number;
  last_update: string;
  stale_data?: boolean;
}

export interface CalculationSettings {
  lookback_days: number;
  recent_N: number;
  proximity_threshold: number;
  price_source: 'close' | 'wick' | 'high' | 'low';
}

const DEFAULT_SETTINGS: CalculationSettings = {
  lookback_days: 30,
  recent_N: 5,
  proximity_threshold: 5.0,
  price_source: 'close'
};

/**
 * Round to specified decimal places
 */
function roundTo(value: number, decimals: number = 2): number {
  return Math.round(value * Math.pow(10, decimals)) / Math.pow(10, decimals);
}

/**
 * Clamp value between min and max
 */
function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

/**
 * Calculate median of an array
 */
function median(values: number[]): number {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0
    ? (sorted[mid - 1] + sorted[mid]) / 2
    : sorted[mid];
}

/**
 * Compute signed percent distance to lower extension
 * Formula: (price - lower_ext) / lower_ext * 100
 * Positive => above line, Negative => below line (breached)
 */
export function computePctDistLowerExt(price: number, lower_ext: number): number {
  if (lower_ext === 0) return 0;
  return roundTo(((price - lower_ext) / lower_ext) * 100, 2);
}

/**
 * Check if price is below lower extension
 */
export function isBelow(pct_dist: number): boolean {
  return pct_dist < 0;
}

/**
 * Compute 30-day lookback metrics from historical prices
 */
export function compute30DayMetrics(
  historical_prices: HistoricalPrice[],
  lower_ext: number,
  settings: CalculationSettings = DEFAULT_SETTINGS
): {
  min_pct_dist_30d: number;
  median_abs_pct_dist_30d: number;
  breach_count_30d: number;
  breach_rate_30d: number;
  recent_breached: boolean;
  stale_data: boolean;
} {
  if (!historical_prices || historical_prices.length === 0) {
    return {
      min_pct_dist_30d: 0,
      median_abs_pct_dist_30d: 0,
      breach_count_30d: 0,
      breach_rate_30d: 0,
      recent_breached: false,
      stale_data: true
    };
  }

  // Filter to last N days
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - settings.lookback_days);

  const recentPrices = historical_prices
    .filter(p => {
      const ts = typeof p.timestamp === 'string'
        ? new Date(p.timestamp).getTime()
        : p.timestamp;
      return ts >= cutoffDate.getTime();
    })
    .sort((a, b) => {
      const tsA = typeof a.timestamp === 'string' ? new Date(a.timestamp).getTime() : a.timestamp;
      const tsB = typeof b.timestamp === 'string' ? new Date(b.timestamp).getTime() : b.timestamp;
      return tsA - tsB;
    });

  if (recentPrices.length === 0) {
    return {
      min_pct_dist_30d: 0,
      median_abs_pct_dist_30d: 0,
      breach_count_30d: 0,
      breach_rate_30d: 0,
      recent_breached: false,
      stale_data: true
    };
  }

  // Compute pct_dist for each historical price
  const pctDists = recentPrices.map(p => computePctDistLowerExt(p.price, lower_ext));
  const absPctDists = pctDists.map(d => Math.abs(d));

  // Min distance (most negative = deepest breach)
  const min_pct_dist_30d = roundTo(Math.min(...pctDists), 2);

  // Median absolute distance
  const median_abs_pct_dist_30d = roundTo(median(absPctDists), 2);

  // Breach count and rate
  const breach_count_30d = pctDists.filter(d => d < 0).length;
  const breach_rate_30d = roundTo(breach_count_30d / recentPrices.length, 4);

  // Check if recently breached (last N points)
  const recentN = recentPrices.slice(-settings.recent_N);
  const recent_breached = recentN.some(p => computePctDistLowerExt(p.price, lower_ext) < 0);

  return {
    min_pct_dist_30d,
    median_abs_pct_dist_30d,
    breach_count_30d,
    breach_rate_30d,
    recent_breached,
    stale_data: false
  };
}

/**
 * Compute proximity score (0-1, normalized)
 * Formula: 1 - (median_abs_pct_dist_30d / threshold)
 * Higher score = closer historically (less risky)
 */
export function computeProximityScore(
  median_abs_pct_dist_30d: number,
  threshold: number
): number {
  const score = 1 - (median_abs_pct_dist_30d / threshold);
  return roundTo(clamp(score, 0, 1), 3);
}

/**
 * Main calculation function - computes all metrics for a symbol
 */
export function calculateLowerExtMetrics(
  data: IndicatorData,
  settings: CalculationSettings = DEFAULT_SETTINGS
): LowerExtMetrics | null {
  // Validate required fields
  if (!data.symbol || data.price === undefined || data.lower_ext === undefined) {
    return null;
  }

  // Compute current distance metrics
  const pct_dist_lower_ext = computePctDistLowerExt(data.price, data.lower_ext);
  const is_below_lower_ext = isBelow(pct_dist_lower_ext);
  const abs_pct_dist_lower_ext = roundTo(Math.abs(pct_dist_lower_ext), 2);

  // Compute 30-day metrics
  const thirtyDayMetrics = compute30DayMetrics(
    data.historical_prices || [],
    data.lower_ext,
    settings
  );

  // Compute proximity score
  const proximity_score_30d = computeProximityScore(
    thirtyDayMetrics.median_abs_pct_dist_30d,
    settings.proximity_threshold
  );

  // Format timestamp
  const last_update = data.last_update || data.timestamp || new Date().toISOString();

  return {
    symbol: data.symbol,
    price: roundTo(data.price, 2),
    lower_ext: roundTo(data.lower_ext, 2),
    pct_dist_lower_ext,
    is_below_lower_ext,
    abs_pct_dist_lower_ext,
    ...thirtyDayMetrics,
    proximity_score_30d,
    last_update,
    stale_data: thirtyDayMetrics.stale_data
  };
}

/**
 * Export metrics to JSON with exact schema
 */
export function exportToJSON(metrics: LowerExtMetrics): string {
  const exportData = {
    symbol: metrics.symbol,
    price: metrics.price,
    lower_ext: metrics.lower_ext,
    pct_dist_lower_ext: metrics.pct_dist_lower_ext,
    is_below_lower_ext: metrics.is_below_lower_ext,
    abs_pct_dist_lower_ext: metrics.abs_pct_dist_lower_ext,
    min_pct_dist_30d: metrics.min_pct_dist_30d,
    median_abs_pct_dist_30d: metrics.median_abs_pct_dist_30d,
    breach_count_30d: metrics.breach_count_30d,
    breach_rate_30d: metrics.breach_rate_30d,
    recent_breached: metrics.recent_breached,
    proximity_score_30d: metrics.proximity_score_30d,
    last_update: metrics.last_update
  };

  return JSON.stringify(exportData, null, 2);
}

/**
 * Batch export multiple symbols to JSON array
 */
export function exportMultipleToJSON(metricsArray: LowerExtMetrics[]): string {
  const exportData = metricsArray.map(m => ({
    symbol: m.symbol,
    price: m.price,
    lower_ext: m.lower_ext,
    pct_dist_lower_ext: m.pct_dist_lower_ext,
    is_below_lower_ext: m.is_below_lower_ext,
    abs_pct_dist_lower_ext: m.abs_pct_dist_lower_ext,
    min_pct_dist_30d: m.min_pct_dist_30d,
    median_abs_pct_dist_30d: m.median_abs_pct_dist_30d,
    breach_count_30d: m.breach_count_30d,
    breach_rate_30d: m.breach_rate_30d,
    recent_breached: m.recent_breached,
    proximity_score_30d: m.proximity_score_30d,
    last_update: m.last_update
  }));

  return JSON.stringify(exportData, null, 2);
}

export default {
  calculateLowerExtMetrics,
  computePctDistLowerExt,
  compute30DayMetrics,
  computeProximityScore,
  exportToJSON,
  exportMultipleToJSON,
  DEFAULT_SETTINGS
};
