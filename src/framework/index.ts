/**
 * Trading Framework - Main Export
 *
 * Principle-led multi-timeframe trading framework
 */

// Core framework
export { TradingFramework } from './core/TradingFramework';
export { DEFAULT_CONFIG, mergeConfig, validateConfig, exportConfig, importConfig, createConservativeConfig, createAggressiveConfig } from './core/config';
export * from './core/types';

// Modules
export { RegimeDetector } from './regime-detection/RegimeDetector';
export { PercentileEngine } from './percentile-logic/PercentileEngine';
export { ExpectancyCalculator, TradeResult } from './risk-expectancy/ExpectancyCalculator';
export { InstrumentScorer } from './composite-scoring/InstrumentScorer';
export { AllocationEngine } from './capital-allocation/AllocationEngine';

// Backtesting
export {
  HistoricalBacktester,
  BacktestConfig,
  BacktestResults,
  Trade,
  PerformanceMetrics,
  RegimePerformance,
  EquityCurvePoint,
} from './backtesting/Backtester';
export { BacktestDataLoader } from './backtesting/BacktestDataLoader';
export { PerformanceReporter, ReportFormat } from './backtesting/PerformanceReporter';

/**
 * Quick start example:
 *
 * ```typescript
 * import { TradingFramework, DEFAULT_CONFIG } from './framework';
 *
 * // Create framework with custom config
 * const framework = new TradingFramework({
 *   riskManagement: {
 *     maxRiskPerTrade: 0.01,
 *     maxTotalRisk: 0.05,
 *   },
 * });
 *
 * // Add market data
 * framework.addMarketData('BTCUSD', marketData);
 *
 * // Start framework
 * framework.start();
 *
 * // Subscribe to events
 * framework.on('entry_signal', (event) => {
 *   console.log('Entry signal:', event);
 * });
 *
 * // Get current state
 * const state = framework.getState();
 * ```
 */
