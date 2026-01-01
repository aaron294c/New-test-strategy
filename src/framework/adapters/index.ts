/**
 * Data Adapters - Export Module
 *
 * Provides adapters to connect the framework to external data sources:
 * - BackendDataAdapter: Python backend API at http://localhost:8000
 * - YFinanceAdapter: Direct Yahoo Finance API integration
 */

export { BackendDataAdapter, BackendAdapterConfig } from './BackendDataAdapter';
export { YFinanceAdapter, YFinanceAdapterConfig } from './YFinanceAdapter';

// Export all type definitions
export * from './types';

/**
 * Quick Start Examples:
 *
 * BACKEND ADAPTER (Recommended for backtesting and analysis):
 * ```typescript
 * import { BackendDataAdapter } from './adapters';
 *
 * const backend = new BackendDataAdapter({
 *   baseUrl: 'http://localhost:8000',
 *   cacheEnabled: true,
 * });
 *
 * // Get backtest results
 * const backtest = await backend.getBacktestResults('AAPL');
 *
 * // Get RSI chart data
 * const chart = await backend.getRSIChart('AAPL', 252);
 *
 * // Get percentile forward mapping
 * const forward = await backend.getPercentileForward('AAPL');
 * ```
 *
 * YFINANCE ADAPTER (Real-time market data):
 * ```typescript
 * import { YFinanceAdapter, Timeframe } from './adapters';
 *
 * const yfinance = new YFinanceAdapter();
 *
 * // Get market data
 * const data = await yfinance.getMarketData('AAPL', Timeframe.H4, '1mo');
 *
 * // Calculate RSI-MA
 * const rsiMa = yfinance.calculateRSIMA(data.bars, 14, 14);
 * ```
 *
 * COMBINED USAGE:
 * ```typescript
 * // Use backend for historical analysis
 * const percentileData = await backend.getPercentileForward('AAPL');
 *
 * // Use YFinance for real-time data
 * const currentPrice = await yfinance.getCurrentPrice('AAPL');
 *
 * // Combine for trading decisions
 * const signal = await backend.getLiveSignal('AAPL');
 * const mtfData = await yfinance.getMultiTimeframeData('AAPL');
 * ```
 */
