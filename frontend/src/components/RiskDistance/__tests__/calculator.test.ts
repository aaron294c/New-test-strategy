/**
 * Tests for Risk Distance calculations (relative to current price)
 */

import { calculateDistanceFromCurrentPrice, calculateRiskDistances } from '../calculator';
import type { RiskDistanceInput } from '../types';

describe('Risk Distance calculator', () => {
  describe('calculateDistanceFromCurrentPrice', () => {
    it('treats levels below price as negative (and BELOW)', () => {
      const price = 186.23;
      const level = 177.5;

      const result = calculateDistanceFromCurrentPrice(price, level);

      // (level - price) / price * 100
      expect(result.pct_dist).toBe(-4.69);
      expect(result.is_below).toBe(true);
      expect(result.abs_pct_dist).toBe(4.69);
    });

    it('treats levels above price as positive (and ABOVE)', () => {
      const price = 186.23;
      const level = 200;

      const result = calculateDistanceFromCurrentPrice(price, level);

      expect(result.pct_dist).toBe(7.39);
      expect(result.is_below).toBe(false);
      expect(result.abs_pct_dist).toBe(7.39);
    });
  });

  describe('calculateRiskDistances', () => {
    it('computes all levels relative to current price consistently', () => {
      const input: RiskDistanceInput = {
        symbol: 'NVDA',
        price: 186.23,
        st_put: 177.5,
        lt_put: 175,
        q_put: 160,
        max_pain: 185,
        lower_ext: 155.14,
        nw_lower_band: 174.67,
        last_update: '2026-01-17T00:00:00.000Z',
      };

      const out = calculateRiskDistances(input);

      expect(out.pct_dist_st_put).toBe(-4.69);
      expect(out.is_below_st_put).toBe(true);

      expect(out.pct_dist_lt_put).toBe(-6.03);
      expect(out.is_below_lt_put).toBe(true);

      expect(out.pct_dist_q_put).toBe(-14.08);
      expect(out.is_below_q_put).toBe(true);

      expect(out.pct_dist_max_pain).toBe(-0.66);
      expect(out.is_below_max_pain).toBe(true);

      expect(out.pct_dist_lower_ext).toBe(-16.69);
      expect(out.is_below_lower_ext).toBe(true);

      expect(out.pct_dist_nw_lower_band).toBe(-6.21);
      expect(out.is_below_nw_lower_band).toBe(true);
    });
  });
});

