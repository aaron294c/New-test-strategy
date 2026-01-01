/**
 * Configuration management for the trading framework
 *
 * Provides default configurations and utilities for config validation and merging
 */

import {
  FrameworkConfig,
  Timeframe,
  TimeframeWeight,
  ScoringFactor,
} from './types';

/**
 * Default framework configuration with principle-led parameters
 */
export const DEFAULT_CONFIG: FrameworkConfig = {
  // Multi-timeframe setup: H4 primary, H1 and D1 supporting
  timeframes: [
    { timeframe: Timeframe.H4, weight: 0.5 },
    { timeframe: Timeframe.H1, weight: 0.3 },
    { timeframe: Timeframe.D1, weight: 0.2 },
  ],
  primaryTimeframe: Timeframe.H4,

  // Regime detection: adaptive parameters
  regimeDetection: {
    lookbackPeriod: 100, // bars to analyze
    coherenceThreshold: 0.6, // 60% alignment across timeframes
    updateFrequency: 15, // check every 15 minutes
  },

  // Percentile-based entries and stops
  percentileSettings: {
    entryPercentile: 90, // Enter at 90th percentile extremes
    stopPercentile: 95, // Stop at 95th percentile move against
    lookbackBars: 100,
    adaptive: true, // Adjust based on volatility regime
  },

  // Risk management: principle-led, conservative defaults
  riskManagement: {
    maxRiskPerTrade: 0.01, // 1% per trade
    maxTotalRisk: 0.05, // 5% total portfolio risk
    maxPositions: 8,
    minWinRate: 0.35, // Min 35% win rate required
    minExpectancy: 0.5, // Min $0.50 expected per $1 risked
  },

  // Composite scoring factors (weights sum to ~1)
  scoring: {
    factors: [
      {
        name: 'regime_alignment',
        value: 0,
        weight: 0.25,
        category: 'regime',
      },
      {
        name: 'risk_adjusted_expectancy',
        value: 0,
        weight: 0.25,
        category: 'risk',
      },
      {
        name: 'percentile_extreme',
        value: 0,
        weight: 0.20,
        category: 'technical',
      },
      {
        name: 'momentum_strength',
        value: 0,
        weight: 0.15,
        category: 'technical',
      },
      {
        name: 'volatility_favorability',
        value: 0,
        weight: 0.15,
        category: 'risk',
      },
    ],
    minScore: 0.6, // Require 60/100 score to consider
    rebalanceFrequency: 60, // Recalculate every hour
  },

  // Capital allocation
  allocation: {
    totalCapital: 100000, // $100k default
    maxRiskPerTrade: 0.01,
    maxTotalRisk: 0.05,
    maxPositions: 8,
    minScore: 0.6,
    diversificationRules: {
      maxPerSector: 0.3, // Max 30% in one sector
      maxCorrelatedPositions: 3, // Max 3 highly correlated positions
    },
  },

  // System settings
  updateInterval: 60000, // 1 minute updates
  logLevel: 'info',
};

/**
 * Validates a framework configuration
 */
export function validateConfig(config: Partial<FrameworkConfig>): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  // Validate timeframe weights sum to 1
  if (config.timeframes) {
    const weightSum = config.timeframes.reduce((sum, tf) => sum + tf.weight, 0);
    if (Math.abs(weightSum - 1.0) > 0.01) {
      errors.push(`Timeframe weights must sum to 1.0, got ${weightSum}`);
    }
  }

  // Validate scoring factor weights
  if (config.scoring?.factors) {
    const weightSum = config.scoring.factors.reduce((sum, f) => sum + f.weight, 0);
    if (Math.abs(weightSum - 1.0) > 0.1) {
      // Allow some tolerance
      errors.push(`Scoring factor weights should sum to ~1.0, got ${weightSum}`);
    }
  }

  // Validate risk parameters
  if (config.riskManagement) {
    const { maxRiskPerTrade, maxTotalRisk } = config.riskManagement;
    if (maxRiskPerTrade && maxRiskPerTrade > 0.05) {
      errors.push(`maxRiskPerTrade > 5% is dangerous: ${maxRiskPerTrade}`);
    }
    if (maxTotalRisk && maxTotalRisk > 0.2) {
      errors.push(`maxTotalRisk > 20% is dangerous: ${maxTotalRisk}`);
    }
    if (maxRiskPerTrade && maxTotalRisk && maxRiskPerTrade > maxTotalRisk) {
      errors.push('maxRiskPerTrade cannot exceed maxTotalRisk');
    }
  }

  // Validate percentiles
  if (config.percentileSettings) {
    const { entryPercentile, stopPercentile } = config.percentileSettings;
    if (entryPercentile && (entryPercentile < 0 || entryPercentile > 100)) {
      errors.push(`entryPercentile must be 0-100: ${entryPercentile}`);
    }
    if (stopPercentile && (stopPercentile < 0 || stopPercentile > 100)) {
      errors.push(`stopPercentile must be 0-100: ${stopPercentile}`);
    }
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Merges user config with defaults
 */
export function mergeConfig(
  userConfig: Partial<FrameworkConfig>
): FrameworkConfig {
  const merged = {
    ...DEFAULT_CONFIG,
    ...userConfig,
  } as FrameworkConfig;

  // Deep merge nested objects
  if (userConfig.regimeDetection) {
    merged.regimeDetection = {
      ...DEFAULT_CONFIG.regimeDetection,
      ...userConfig.regimeDetection,
    };
  }

  if (userConfig.percentileSettings) {
    merged.percentileSettings = {
      ...DEFAULT_CONFIG.percentileSettings,
      ...userConfig.percentileSettings,
    };
  }

  if (userConfig.riskManagement) {
    merged.riskManagement = {
      ...DEFAULT_CONFIG.riskManagement,
      ...userConfig.riskManagement,
    };
  }

  if (userConfig.scoring) {
    merged.scoring = {
      ...DEFAULT_CONFIG.scoring,
      ...userConfig.scoring,
    };
  }

  if (userConfig.allocation) {
    merged.allocation = {
      ...DEFAULT_CONFIG.allocation,
      ...userConfig.allocation,
    };
  }

  return merged;
}

/**
 * Creates a conservative config for risk-averse trading
 */
export function createConservativeConfig(): FrameworkConfig {
  return mergeConfig({
    riskManagement: {
      maxRiskPerTrade: 0.005, // 0.5% per trade
      maxTotalRisk: 0.025, // 2.5% total
      maxPositions: 5,
      minWinRate: 0.4,
      minExpectancy: 0.75,
    },
    allocation: {
      ...DEFAULT_CONFIG.allocation,
      maxRiskPerTrade: 0.005,
      maxTotalRisk: 0.025,
      maxPositions: 5,
    },
  });
}

/**
 * Creates an aggressive config for higher risk tolerance
 */
export function createAggressiveConfig(): FrameworkConfig {
  return mergeConfig({
    riskManagement: {
      maxRiskPerTrade: 0.02, // 2% per trade
      maxTotalRisk: 0.08, // 8% total
      maxPositions: 12,
      minWinRate: 0.3,
      minExpectancy: 0.3,
    },
    allocation: {
      ...DEFAULT_CONFIG.allocation,
      maxRiskPerTrade: 0.02,
      maxTotalRisk: 0.08,
      maxPositions: 12,
    },
  });
}

/**
 * Export config to JSON
 */
export function exportConfig(config: FrameworkConfig): string {
  return JSON.stringify(config, null, 2);
}

/**
 * Import config from JSON
 */
export function importConfig(json: string): FrameworkConfig {
  const parsed = JSON.parse(json) as Partial<FrameworkConfig>;
  const merged = mergeConfig(parsed);

  const validation = validateConfig(merged);
  if (!validation.valid) {
    throw new Error(
      `Invalid configuration: ${validation.errors.join(', ')}`
    );
  }

  return merged;
}
