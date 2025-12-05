/**
 * Unit tests for Configuration Management
 */

import {
  validateConfig,
  mergeConfig,
  createConservativeConfig,
  createAggressiveConfig,
  exportConfig,
  importConfig,
  DEFAULT_CONFIG,
} from '../../../src/framework/core/config';
import { Timeframe } from '../../../src/framework/core/types';

describe('Configuration Management', () => {
  describe('validateConfig', () => {
    it('should validate default config successfully', () => {
      const result = validateConfig(DEFAULT_CONFIG);
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should detect invalid timeframe weights', () => {
      const invalidConfig = {
        ...DEFAULT_CONFIG,
        timeframes: [
          { timeframe: Timeframe.H4, weight: 0.5 },
          { timeframe: Timeframe.H1, weight: 0.6 }, // Sums to 1.1
        ],
      };

      const result = validateConfig(invalidConfig);
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.includes('Timeframe weights'))).toBe(true);
    });

    it('should detect excessive risk per trade', () => {
      const invalidConfig = {
        ...DEFAULT_CONFIG,
        riskManagement: {
          ...DEFAULT_CONFIG.riskManagement,
          maxRiskPerTrade: 0.1, // 10% is dangerous
        },
      };

      const result = validateConfig(invalidConfig);
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.includes('maxRiskPerTrade'))).toBe(true);
    });

    it('should detect invalid percentile ranges', () => {
      const invalidConfig = {
        ...DEFAULT_CONFIG,
        percentileSettings: {
          ...DEFAULT_CONFIG.percentileSettings,
          entryPercentile: 150, // Invalid: >100
        },
      };

      const result = validateConfig(invalidConfig);
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.includes('entryPercentile'))).toBe(true);
    });

    it('should detect maxRiskPerTrade > maxTotalRisk', () => {
      const invalidConfig = {
        ...DEFAULT_CONFIG,
        riskManagement: {
          ...DEFAULT_CONFIG.riskManagement,
          maxRiskPerTrade: 0.04,
          maxTotalRisk: 0.02, // Less than per trade
        },
      };

      const result = validateConfig(invalidConfig);
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.includes('cannot exceed'))).toBe(true);
    });
  });

  describe('mergeConfig', () => {
    it('should merge partial config with defaults', () => {
      const userConfig = {
        riskManagement: {
          maxRiskPerTrade: 0.02,
        },
      };

      const merged = mergeConfig(userConfig);

      expect(merged.riskManagement.maxRiskPerTrade).toBe(0.02);
      expect(merged.riskManagement.maxTotalRisk).toBe(DEFAULT_CONFIG.riskManagement.maxTotalRisk);
      expect(merged.timeframes).toEqual(DEFAULT_CONFIG.timeframes);
    });

    it('should deep merge nested objects', () => {
      const userConfig = {
        percentileSettings: {
          entryPercentile: 95,
        },
      };

      const merged = mergeConfig(userConfig);

      expect(merged.percentileSettings.entryPercentile).toBe(95);
      expect(merged.percentileSettings.stopPercentile).toBe(
        DEFAULT_CONFIG.percentileSettings.stopPercentile
      );
    });

    it('should preserve user-provided arrays', () => {
      const customTimeframes = [
        { timeframe: Timeframe.H1, weight: 0.6 },
        { timeframe: Timeframe.D1, weight: 0.4 },
      ];

      const merged = mergeConfig({ timeframes: customTimeframes });

      expect(merged.timeframes).toEqual(customTimeframes);
    });
  });

  describe('Preset Configurations', () => {
    it('should create conservative config', () => {
      const config = createConservativeConfig();

      expect(config.riskManagement.maxRiskPerTrade).toBe(0.005);
      expect(config.riskManagement.maxTotalRisk).toBe(0.025);
      expect(config.riskManagement.maxPositions).toBe(5);
      expect(config.riskManagement.minWinRate).toBe(0.4);
    });

    it('should create aggressive config', () => {
      const config = createAggressiveConfig();

      expect(config.riskManagement.maxRiskPerTrade).toBe(0.02);
      expect(config.riskManagement.maxTotalRisk).toBe(0.08);
      expect(config.riskManagement.maxPositions).toBe(12);
      expect(config.riskManagement.minWinRate).toBe(0.3);
    });

    it('should validate conservative config', () => {
      const config = createConservativeConfig();
      const result = validateConfig(config);

      expect(result.valid).toBe(true);
    });

    it('should validate aggressive config', () => {
      const config = createAggressiveConfig();
      const result = validateConfig(config);

      expect(result.valid).toBe(true);
    });
  });

  describe('Export/Import', () => {
    it('should export config to JSON', () => {
      const json = exportConfig(DEFAULT_CONFIG);
      const parsed = JSON.parse(json);

      expect(parsed.primaryTimeframe).toBe(DEFAULT_CONFIG.primaryTimeframe);
      expect(parsed.riskManagement).toEqual(DEFAULT_CONFIG.riskManagement);
    });

    it('should import config from JSON', () => {
      const json = exportConfig(DEFAULT_CONFIG);
      const imported = importConfig(json);

      expect(imported).toEqual(DEFAULT_CONFIG);
    });

    it('should throw on invalid imported config', () => {
      const invalidJson = JSON.stringify({
        riskManagement: {
          maxRiskPerTrade: 0.5, // Too high
        },
      });

      expect(() => importConfig(invalidJson)).toThrow('Invalid configuration');
    });

    it('should handle partial import with merge', () => {
      const partialJson = JSON.stringify({
        updateInterval: 30000,
      });

      const imported = importConfig(partialJson);

      expect(imported.updateInterval).toBe(30000);
      expect(imported.riskManagement).toEqual(DEFAULT_CONFIG.riskManagement);
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty config merge', () => {
      const merged = mergeConfig({});
      expect(merged).toEqual(DEFAULT_CONFIG);
    });

    it('should handle config with all custom values', () => {
      const customConfig = {
        ...DEFAULT_CONFIG,
        primaryTimeframe: Timeframe.H1,
        updateInterval: 30000,
        logLevel: 'debug' as const,
      };

      const merged = mergeConfig(customConfig);
      expect(merged.primaryTimeframe).toBe(Timeframe.H1);
      expect(merged.updateInterval).toBe(30000);
      expect(merged.logLevel).toBe('debug');
    });
  });
});
