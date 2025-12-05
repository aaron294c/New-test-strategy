/**
 * Tests for Lower Extension Distance Calculations
 */

import {
  computePctDistLowerExt,
  isBelow,
  compute30DayMetrics,
  computeProximityScore,
  calculateLowerExtMetrics,
  exportToJSON,
  IndicatorData,
  CalculationSettings,
} from '../lowerExtensionCalculations';

describe('Lower Extension Distance Calculations', () => {
  describe('computePctDistLowerExt', () => {
    it('should calculate positive distance when price is above lower_ext', () => {
      const result = computePctDistLowerExt(6999, 6900);
      expect(result).toBe(1.43); // (6999 - 6900) / 6900 * 100 = 1.43%
    });

    it('should calculate negative distance when price is below lower_ext', () => {
      const result = computePctDistLowerExt(6850, 6900);
      expect(result).toBe(-0.72); // (6850 - 6900) / 6900 * 100 = -0.72%
    });

    it('should return 0 when price equals lower_ext', () => {
      const result = computePctDistLowerExt(6900, 6900);
      expect(result).toBe(0);
    });

    it('should handle division by zero', () => {
      const result = computePctDistLowerExt(6900, 0);
      expect(result).toBe(0);
    });

    it('should round to 2 decimal places', () => {
      const result = computePctDistLowerExt(6999.99, 6900.01);
      expect(result).toBeCloseTo(1.45, 2);
    });
  });

  describe('isBelow', () => {
    it('should return true for negative percent distance', () => {
      expect(isBelow(-0.72)).toBe(true);
    });

    it('should return false for positive percent distance', () => {
      expect(isBelow(1.43)).toBe(false);
    });

    it('should return false for zero', () => {
      expect(isBelow(0)).toBe(false);
    });
  });

  describe('compute30DayMetrics', () => {
    const settings: CalculationSettings = {
      lookback_days: 30,
      recent_N: 5,
      proximity_threshold: 5.0,
      price_source: 'close',
    };

    it('should calculate min_pct_dist_30d correctly', () => {
      const historicalPrices = [
        { timestamp: '2025-10-01', price: 6950 },
        { timestamp: '2025-10-02', price: 6920 },
        { timestamp: '2025-10-03', price: 6880 }, // Deepest breach
        { timestamp: '2025-10-04', price: 6910 },
        { timestamp: '2025-10-05', price: 6940 },
      ];

      const result = compute30DayMetrics(historicalPrices, 6900, settings);

      // Deepest: (6880 - 6900) / 6900 * 100 = -0.29%
      expect(result.min_pct_dist_30d).toBeCloseTo(-0.29, 2);
    });

    it('should calculate breach count and rate correctly', () => {
      const historicalPrices = [
        { timestamp: '2025-10-01', price: 6950 }, // Above
        { timestamp: '2025-10-02', price: 6880 }, // Below
        { timestamp: '2025-10-03', price: 6890 }, // Below
        { timestamp: '2025-10-04', price: 6920 }, // Above
        { timestamp: '2025-10-05', price: 6940 }, // Above
      ];

      const result = compute30DayMetrics(historicalPrices, 6900, settings);

      expect(result.breach_count_30d).toBe(2);
      expect(result.breach_rate_30d).toBe(0.4); // 2/5 = 0.4
    });

    it('should detect recent breaches', () => {
      const historicalPrices = [
        { timestamp: '2025-10-01', price: 6950 },
        { timestamp: '2025-10-02', price: 6920 },
        { timestamp: '2025-10-03', price: 6940 },
        { timestamp: '2025-10-04', price: 6910 },
        { timestamp: '2025-10-05', price: 6880 }, // Recent breach
      ];

      const result = compute30DayMetrics(historicalPrices, 6900, settings);

      expect(result.recent_breached).toBe(true);
    });

    it('should not detect recent breaches if none in last N', () => {
      const historicalPrices = [
        { timestamp: '2025-10-01', price: 6880 }, // Old breach
        { timestamp: '2025-10-02', price: 6920 },
        { timestamp: '2025-10-03', price: 6940 },
        { timestamp: '2025-10-04', price: 6950 },
        { timestamp: '2025-10-05', price: 6960 },
      ];

      const result = compute30DayMetrics(historicalPrices, 6900, settings);

      expect(result.recent_breached).toBe(false);
    });

    it('should return stale_data flag when no historical prices', () => {
      const result = compute30DayMetrics([], 6900, settings);

      expect(result.stale_data).toBe(true);
      expect(result.breach_count_30d).toBe(0);
      expect(result.recent_breached).toBe(false);
    });

    it('should calculate median absolute distance correctly', () => {
      const historicalPrices = [
        { timestamp: '2025-10-01', price: 6850 }, // -0.72%
        { timestamp: '2025-10-02', price: 6900 }, // 0%
        { timestamp: '2025-10-03', price: 6950 }, // +0.72%
        { timestamp: '2025-10-04', price: 6975 }, // +1.09%
        { timestamp: '2025-10-05', price: 6925 }, // +0.36%
      ];

      const result = compute30DayMetrics(historicalPrices, 6900, settings);

      // Absolute distances: 0.72, 0, 0.72, 1.09, 0.36
      // Sorted: 0, 0.36, 0.72, 0.72, 1.09
      // Median: 0.72
      expect(result.median_abs_pct_dist_30d).toBeCloseTo(0.72, 2);
    });
  });

  describe('computeProximityScore', () => {
    it('should return 1.0 for distance at 0', () => {
      const score = computeProximityScore(0, 5.0);
      expect(score).toBe(1.0);
    });

    it('should return 0.5 for distance at half threshold', () => {
      const score = computeProximityScore(2.5, 5.0);
      expect(score).toBe(0.5);
    });

    it('should return 0.0 for distance at threshold', () => {
      const score = computeProximityScore(5.0, 5.0);
      expect(score).toBe(0.0);
    });

    it('should clamp to 0.0 for distance beyond threshold', () => {
      const score = computeProximityScore(10.0, 5.0);
      expect(score).toBe(0.0);
    });

    it('should round to 3 decimal places', () => {
      const score = computeProximityScore(1.234567, 5.0);
      expect(score).toBeCloseTo(0.753, 3);
    });
  });

  describe('calculateLowerExtMetrics', () => {
    const settings: CalculationSettings = {
      lookback_days: 30,
      recent_N: 5,
      proximity_threshold: 5.0,
      price_source: 'close',
    };

    it('should return null for missing required fields', () => {
      const invalidData: any = { symbol: 'SPX' };
      const result = calculateLowerExtMetrics(invalidData, settings);
      expect(result).toBeNull();
    });

    it('should calculate all metrics correctly for valid data', () => {
      const data: IndicatorData = {
        symbol: 'SPX',
        price: 6999,
        lower_ext: 6900,
        last_update: '2025-11-07',
        historical_prices: [
          { timestamp: '2025-10-01', price: 6950 },
          { timestamp: '2025-10-02', price: 6920 },
          { timestamp: '2025-10-03', price: 6940 },
          { timestamp: '2025-10-04', price: 6910 },
          { timestamp: '2025-10-05', price: 6930 },
        ],
      };

      const result = calculateLowerExtMetrics(data, settings);

      expect(result).not.toBeNull();
      expect(result!.symbol).toBe('SPX');
      expect(result!.price).toBe(6999);
      expect(result!.lower_ext).toBe(6900);
      expect(result!.pct_dist_lower_ext).toBeCloseTo(1.43, 2);
      expect(result!.is_below_lower_ext).toBe(false);
      expect(result!.abs_pct_dist_lower_ext).toBeCloseTo(1.43, 2);
      expect(result!.proximity_score_30d).toBeGreaterThan(0);
      expect(result!.proximity_score_30d).toBeLessThanOrEqual(1);
    });

    it('should mark stale_data when no historical prices', () => {
      const data: IndicatorData = {
        symbol: 'SPX',
        price: 6999,
        lower_ext: 6900,
      };

      const result = calculateLowerExtMetrics(data, settings);

      expect(result).not.toBeNull();
      expect(result!.stale_data).toBe(true);
    });
  });

  describe('exportToJSON', () => {
    it('should export metrics in exact schema format', () => {
      const metrics = {
        symbol: 'SPX',
        price: 6999.0,
        lower_ext: 6900.0,
        pct_dist_lower_ext: 1.43,
        is_below_lower_ext: false,
        abs_pct_dist_lower_ext: 1.43,
        min_pct_dist_30d: -2.34,
        median_abs_pct_dist_30d: 1.23,
        breach_count_30d: 4,
        breach_rate_30d: 0.1333,
        recent_breached: true,
        proximity_score_30d: 0.754,
        last_update: 'nov 07, 03:42pm',
      };

      const json = exportToJSON(metrics);
      const parsed = JSON.parse(json);

      expect(parsed).toHaveProperty('symbol', 'SPX');
      expect(parsed).toHaveProperty('price', 6999.0);
      expect(parsed).toHaveProperty('lower_ext', 6900.0);
      expect(parsed).toHaveProperty('pct_dist_lower_ext', 1.43);
      expect(parsed).toHaveProperty('is_below_lower_ext', false);
      expect(parsed).toHaveProperty('abs_pct_dist_lower_ext', 1.43);
      expect(parsed).toHaveProperty('min_pct_dist_30d', -2.34);
      expect(parsed).toHaveProperty('median_abs_pct_dist_30d', 1.23);
      expect(parsed).toHaveProperty('breach_count_30d', 4);
      expect(parsed).toHaveProperty('breach_rate_30d', 0.1333);
      expect(parsed).toHaveProperty('recent_breached', true);
      expect(parsed).toHaveProperty('proximity_score_30d', 0.754);
      expect(parsed).toHaveProperty('last_update', 'nov 07, 03:42pm');

      // Should not include stale_data in export
      expect(parsed).not.toHaveProperty('stale_data');
    });
  });

  describe('Edge Cases', () => {
    const settings: CalculationSettings = {
      lookback_days: 30,
      recent_N: 5,
      proximity_threshold: 5.0,
      price_source: 'close',
    };

    it('should handle very small price differences', () => {
      const result = computePctDistLowerExt(6900.01, 6900.00);
      expect(result).toBeCloseTo(0.0, 2);
    });

    it('should handle very large price differences', () => {
      const result = computePctDistLowerExt(10000, 6900);
      expect(result).toBeCloseTo(44.93, 2);
    });

    it('should handle historical prices with Unix timestamps', () => {
      const historicalPrices = [
        { timestamp: Date.now() - 86400000 * 5, price: 6950 },
        { timestamp: Date.now() - 86400000 * 4, price: 6920 },
        { timestamp: Date.now() - 86400000 * 3, price: 6940 },
      ];

      const result = compute30DayMetrics(historicalPrices, 6900, settings);

      expect(result.stale_data).toBe(false);
      expect(result.breach_count_30d).toBeGreaterThanOrEqual(0);
    });

    it('should handle mixed timestamp formats', () => {
      const historicalPrices = [
        { timestamp: '2025-10-01T00:00:00Z', price: 6950 },
        { timestamp: Date.now() - 86400000, price: 6920 },
        { timestamp: '2025-10-03', price: 6940 },
      ];

      const result = compute30DayMetrics(historicalPrices, 6900, settings);

      expect(result.breach_count_30d).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Integration Test', () => {
    it('should produce correct output for example scenario', () => {
      const data: IndicatorData = {
        symbol: 'SPX',
        price: 6999.00,
        lower_ext: 6900.00,
        last_update: 'nov 07, 03:42pm',
        historical_prices: [
          { timestamp: '2025-10-08', price: 6950.00 },
          { timestamp: '2025-10-09', price: 6920.00 },
          { timestamp: '2025-10-10', price: 6880.00 },
          { timestamp: '2025-10-11', price: 6895.00 },
          { timestamp: '2025-10-12', price: 6910.00 },
          { timestamp: '2025-10-13', price: 6930.00 },
          { timestamp: '2025-10-14', price: 6945.00 },
          { timestamp: '2025-10-15', price: 6960.00 },
          { timestamp: '2025-10-16', price: 6975.00 },
          { timestamp: '2025-10-17', price: 6990.00 },
        ],
      };

      const settings: CalculationSettings = {
        lookback_days: 30,
        recent_N: 5,
        proximity_threshold: 5.0,
        price_source: 'close',
      };

      const metrics = calculateLowerExtMetrics(data, settings);

      expect(metrics).not.toBeNull();
      expect(metrics!.symbol).toBe('SPX');
      expect(metrics!.price).toBe(6999.0);
      expect(metrics!.lower_ext).toBe(6900.0);
      expect(metrics!.pct_dist_lower_ext).toBeGreaterThan(0);
      expect(metrics!.is_below_lower_ext).toBe(false);
      expect(metrics!.breach_count_30d).toBeGreaterThan(0); // 6880, 6895 are below 6900
      expect(metrics!.proximity_score_30d).toBeGreaterThan(0);
      expect(metrics!.proximity_score_30d).toBeLessThanOrEqual(1);

      // Export and verify JSON
      const json = exportToJSON(metrics!);
      const parsed = JSON.parse(json);

      expect(parsed.symbol).toBe('SPX');
      expect(parsed.is_below_lower_ext).toBe(false);
    });
  });
});
