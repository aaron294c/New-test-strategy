/**
 * Wall Status Utility
 * Calculates which support walls are being engaged (breached or within threshold)
 *
 * Performance optimized:
 * - Pure functions with no side effects
 * - Pre-computed thresholds
 * - Minimal object allocations
 */

export interface WallLevel {
  name: string;
  shortName: string;
  value: number | null;
  color: string;
}

export interface EngagedWall {
  name: string;
  shortName: string;
  distance: number; // negative = breached, positive = approaching
  status: 'breached' | 'approaching';
  color: string;
}

export interface WallStatusResult {
  engagedWalls: EngagedWall[];
  summary: string;
  hasEngagement: boolean;
}

// Wall definitions with colors
const WALL_DEFINITIONS = [
  { key: 'st_put', name: 'ST Put', shortName: 'ST', color: '#4caf50' },
  { key: 'lt_put', name: 'LT Put', shortName: 'LT', color: '#2196f3' },
  { key: 'q_put', name: 'Q Put', shortName: 'Q', color: '#9c27b0' },
  { key: 'max_pain', name: 'Max Pain', shortName: 'MP', color: '#ff9800' },
  { key: 'lower_ext', name: 'Lower Ext', shortName: 'LE', color: '#00bcd4' },
  { key: 'nw_lower_band', name: 'NW Band', shortName: 'NW', color: '#e91e63' },
] as const;

// Threshold for "approaching" status (1% above wall)
const APPROACH_THRESHOLD_PCT = 1.0;

/**
 * Calculate which walls are engaged for a given price and wall levels
 *
 * @param currentPrice - Current market price
 * @param wallData - Object containing wall values (st_put, lt_put, etc.)
 * @returns WallStatusResult with engaged walls and summary
 */
export function calculateWallStatus(
  currentPrice: number | null,
  wallData: Record<string, number | null> | null
): WallStatusResult {
  const emptyResult: WallStatusResult = {
    engagedWalls: [],
    summary: '—',
    hasEngagement: false,
  };

  if (currentPrice === null || currentPrice === 0 || !wallData) {
    return emptyResult;
  }

  const engagedWalls: EngagedWall[] = [];

  for (const def of WALL_DEFINITIONS) {
    const wallValue = wallData[def.key];

    if (wallValue === null || wallValue === undefined || wallValue === 0) {
      continue;
    }

    // Calculate percentage distance from current price to wall
    // Negative = price is BELOW wall (breached)
    // Positive = price is ABOVE wall
    const distancePct = ((currentPrice - wallValue) / wallValue) * 100;

    // Check if engaged: breached (price below wall) or approaching (within threshold above)
    if (distancePct < 0) {
      // Price is BELOW wall - BREACHED
      engagedWalls.push({
        name: def.name,
        shortName: def.shortName,
        distance: distancePct,
        status: 'breached',
        color: def.color,
      });
    } else if (distancePct <= APPROACH_THRESHOLD_PCT) {
      // Price is within threshold ABOVE wall - APPROACHING
      engagedWalls.push({
        name: def.name,
        shortName: def.shortName,
        distance: distancePct,
        status: 'approaching',
        color: def.color,
      });
    }
  }

  // Sort by distance (most breached first, then closest approaching)
  engagedWalls.sort((a, b) => a.distance - b.distance);

  // Build summary string
  let summary = '—';
  if (engagedWalls.length > 0) {
    summary = engagedWalls
      .slice(0, 3) // Max 3 walls in summary
      .map(w => {
        const sign = w.distance < 0 ? '' : '+';
        return `${w.shortName}(${sign}${w.distance.toFixed(1)}%)`;
      })
      .join(' ');

    if (engagedWalls.length > 3) {
      summary += ` +${engagedWalls.length - 3}`;
    }
  }

  return {
    engagedWalls,
    summary,
    hasEngagement: engagedWalls.length > 0,
  };
}

/**
 * Format wall data from API response to the expected structure
 * Handles different API response formats (scanner-json, risk-distance, etc.)
 */
export function normalizeWallData(apiData: any): Record<string, number | null> | null {
  if (!apiData) return null;

  // Handle scanner-json format (st_put_wall, lt_put_wall, q_put_wall)
  // Handle risk-distance format (st_put, lt_put, q_put)
  // Handle weighted_walls format (put.st_wall, put.lt_wall, etc.)
  return {
    st_put: apiData.st_put_wall ?? apiData.st_put ?? apiData.stPut ??
            apiData.weighted_walls?.put?.st_wall?.recommended_wall ?? null,
    lt_put: apiData.lt_put_wall ?? apiData.lt_put ?? apiData.ltPut ??
            apiData.weighted_walls?.put?.lt_wall?.recommended_wall ?? null,
    q_put: apiData.q_put_wall ?? apiData.q_put ?? apiData.qPut ??
           apiData.weighted_walls?.put?.q_wall?.recommended_wall ?? null,
    max_pain: apiData.max_pain ?? apiData.maxPain ??
              apiData.max_pain?.swing?.level ?? null,
    lower_ext: apiData.lower_ext ?? apiData.lowerExt ?? apiData.lower_extension ?? null,
    nw_lower_band: apiData.nw_lower_band ?? apiData.nwLowerBand ?? apiData.nw_band ?? null,
  };
}

/**
 * Batch calculate wall status for multiple tickers
 * Optimized for bulk operations
 */
export function batchCalculateWallStatus(
  tickers: Array<{ ticker: string; price: number | null }>,
  wallDataMap: Map<string, Record<string, number | null>>
): Map<string, WallStatusResult> {
  const results = new Map<string, WallStatusResult>();

  for (const { ticker, price } of tickers) {
    const wallData = wallDataMap.get(ticker) || null;
    results.set(ticker, calculateWallStatus(price, wallData));
  }

  return results;
}
