/**
 * Backend Data Adapter
 *
 * Connects the TypeScript framework to the Python backend API at http://localhost:8000
 * Transforms Python response formats to framework's MarketData format
 * Includes error handling, retry logic, and response caching
 */

import {
  MarketData,
  OHLCV,
  Timeframe,
  PercentileData,
  RiskMetrics as FrameworkRiskMetrics,
} from '../core/types';

import {
  BacktestResponse,
  RSIChartResponse,
  PercentileForwardResponse,
  MonteCarloResponse,
  LiveSignalResponse,
  MultiTimeframeResponse,
  BacktestRequest,
  MonteCarloRequest,
  ExitSignalRequest,
  APIError,
} from './types';

/**
 * Configuration for the backend adapter
 */
export interface BackendAdapterConfig {
  baseUrl?: string;
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  cacheEnabled?: boolean;
  cacheTTL?: number;
}

/**
 * Default configuration
 */
const DEFAULT_CONFIG: Required<BackendAdapterConfig> = {
  baseUrl: 'http://localhost:8000',
  timeout: 30000, // 30 seconds
  retries: 3,
  retryDelay: 1000, // 1 second
  cacheEnabled: true,
  cacheTTL: 300000, // 5 minutes
};

/**
 * Simple in-memory cache
 */
interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

class ResponseCache {
  private cache = new Map<string, CacheEntry<any>>();

  set<T>(key: string, data: T, ttl: number): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now() + ttl,
    });
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    if (Date.now() > entry.timestamp) {
      this.cache.delete(key);
      return null;
    }

    return entry.data as T;
  }

  clear(): void {
    this.cache.clear();
  }

  clearExpired(): void {
    const now = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (now > entry.timestamp) {
        this.cache.delete(key);
      }
    }
  }
}

/**
 * Backend Data Adapter class
 */
export class BackendDataAdapter {
  private config: Required<BackendAdapterConfig>;
  private cache: ResponseCache;

  constructor(config: BackendAdapterConfig = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.cache = new ResponseCache();

    // Clear expired cache entries every 5 minutes
    if (this.config.cacheEnabled) {
      setInterval(() => this.cache.clearExpired(), 300000);
    }
  }

  /**
   * Fetch backtest results for a ticker
   */
  async getBacktestResults(
    ticker: string,
    forceRefresh = false
  ): Promise<BacktestResponse> {
    const cacheKey = `backtest_${ticker}`;

    if (!forceRefresh && this.config.cacheEnabled) {
      const cached = this.cache.get<BacktestResponse>(cacheKey);
      if (cached) return cached;
    }

    const url = `${this.config.baseUrl}/api/backtest/${ticker}${
      forceRefresh ? '?force_refresh=true' : ''
    }`;

    const response = await this.fetchWithRetry<BacktestResponse>(url);

    if (this.config.cacheEnabled) {
      this.cache.set(cacheKey, response, this.config.cacheTTL);
    }

    return response;
  }

  /**
   * Fetch RSI chart data for visualization
   */
  async getRSIChart(
    ticker: string,
    days?: number
  ): Promise<RSIChartResponse> {
    const cacheKey = `rsi_chart_${ticker}_${days || 'all'}`;

    if (this.config.cacheEnabled) {
      const cached = this.cache.get<RSIChartResponse>(cacheKey);
      if (cached) return cached;
    }

    const url = `${this.config.baseUrl}/api/rsi-chart/${ticker}${
      days ? `?days=${days}` : ''
    }`;

    const response = await this.fetchWithRetry<RSIChartResponse>(url);

    if (this.config.cacheEnabled) {
      this.cache.set(cacheKey, response, this.config.cacheTTL);
    }

    return response;
  }

  /**
   * Fetch percentile forward mapping analysis
   */
  async getPercentileForward(
    ticker: string,
    forceRefresh = false
  ): Promise<PercentileForwardResponse> {
    const cacheKey = `percentile_forward_${ticker}`;

    if (!forceRefresh && this.config.cacheEnabled) {
      const cached = this.cache.get<PercentileForwardResponse>(cacheKey);
      if (cached) return cached;
    }

    const url = `${this.config.baseUrl}/api/percentile-forward/${ticker}${
      forceRefresh ? '?force_refresh=true' : ''
    }`;

    const response = await this.fetchWithRetry<PercentileForwardResponse>(url);

    if (this.config.cacheEnabled) {
      // Use longer cache for percentile forward (already cached on backend)
      this.cache.set(cacheKey, response, 3600000); // 1 hour
    }

    return response;
  }

  /**
   * Fetch 4-hour percentile forward mapping
   */
  async getPercentileForward4H(
    ticker: string,
    forceRefresh = false
  ): Promise<PercentileForwardResponse> {
    const cacheKey = `percentile_forward_4h_${ticker}`;

    if (!forceRefresh && this.config.cacheEnabled) {
      const cached = this.cache.get<PercentileForwardResponse>(cacheKey);
      if (cached) return cached;
    }

    const url = `${this.config.baseUrl}/api/percentile-forward-4h/${ticker}${
      forceRefresh ? '?force_refresh=true' : ''
    }`;

    const response = await this.fetchWithRetry<PercentileForwardResponse>(url);

    if (this.config.cacheEnabled) {
      this.cache.set(cacheKey, response, 3600000);
    }

    return response;
  }

  /**
   * Run Monte Carlo simulation
   */
  async runMonteCarloSimulation(
    request: MonteCarloRequest
  ): Promise<MonteCarloResponse> {
    const url = `${this.config.baseUrl}/api/monte-carlo/${request.ticker}`;

    const response = await this.fetchWithRetry<MonteCarloResponse>(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        num_simulations: request.num_simulations,
        max_periods: request.max_periods,
        target_percentiles: request.target_percentiles,
      }),
    });

    return response;
  }

  /**
   * Get live entry signal
   */
  async getLiveSignal(ticker: string): Promise<LiveSignalResponse> {
    const url = `${this.config.baseUrl}/api/live-signal/${ticker}`;
    return await this.fetchWithRetry<LiveSignalResponse>(url);
  }

  /**
   * Get multi-timeframe analysis
   */
  async getMultiTimeframeAnalysis(
    ticker: string
  ): Promise<MultiTimeframeResponse> {
    const cacheKey = `mtf_${ticker}`;

    if (this.config.cacheEnabled) {
      const cached = this.cache.get<MultiTimeframeResponse>(cacheKey);
      if (cached) return cached;
    }

    const url = `${this.config.baseUrl}/api/multi-timeframe/${ticker}`;
    const response = await this.fetchWithRetry<MultiTimeframeResponse>(url);

    if (this.config.cacheEnabled) {
      this.cache.set(cacheKey, response, this.config.cacheTTL);
    }

    return response;
  }

  /**
   * Batch backtest multiple tickers
   */
  async batchBacktest(request: BacktestRequest): Promise<any> {
    const url = `${this.config.baseUrl}/api/backtest/batch`;

    return await this.fetchWithRetry(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
  }

  /**
   * Transform RSI chart data to MarketData format
   */
  transformToMarketData(
    ticker: string,
    chartData: RSIChartResponse
  ): MarketData {
    const bars: OHLCV[] = chartData.chart_data.dates.map((dateStr, i) => ({
      open: chartData.chart_data.prices[i],
      high: chartData.chart_data.prices[i],
      low: chartData.chart_data.prices[i],
      close: chartData.chart_data.prices[i],
      volume: 0, // Not provided by backend
      timestamp: new Date(dateStr),
      timeframe: Timeframe.D1, // Default to daily
    }));

    return {
      instrument: ticker,
      bars,
      currentPrice: chartData.chart_data.current.price,
      lastUpdate: new Date(chartData.timestamp),
    };
  }

  /**
   * Transform percentile forward data to PercentileData format
   */
  transformToPercentileData(
    response: PercentileForwardResponse,
    timeframe: Timeframe = Timeframe.D1
  ): PercentileData {
    return {
      value: response.current_state.current_rsi_ma,
      percentile: response.current_state.current_percentile,
      lookbackPeriod: 100, // Default lookback
      timeframe,
    };
  }

  /**
   * Transform backend risk metrics to framework format
   */
  transformRiskMetrics(
    backtestData: BacktestResponse,
    threshold: string
  ): FrameworkRiskMetrics | null {
    const thresholdData = backtestData.data.thresholds[threshold];
    if (!thresholdData?.risk_metrics) return null;

    const rm = thresholdData.risk_metrics;

    // Calculate win rate and expectancy from threshold data
    const winRates = Object.values(thresholdData.win_rates);
    const avgWinRate =
      winRates.reduce((sum, rate) => sum + rate, 0) / winRates.length;

    return {
      winRate: avgWinRate,
      avgWin: 0, // Not directly provided
      avgLoss: 0, // Not directly provided
      winLossRatio: 0, // Would need to calculate
      expectancy: thresholdData.optimal_exit_strategy?.expected_return || 0,
      sharpeRatio: rm.sharpe_ratio,
      maxDrawdown: rm.max_drawdown,
      recoveryFactor: undefined,
      sampleSize: thresholdData.events,
    };
  }

  /**
   * Generic fetch with retry logic
   */
  private async fetchWithRetry<T>(
    url: string,
    options: RequestInit = {},
    attempt = 1
  ): Promise<T> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(
        () => controller.abort(),
        this.config.timeout
      );

      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error: APIError = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      if (attempt < this.config.retries) {
        await this.delay(this.config.retryDelay * attempt);
        return this.fetchWithRetry<T>(url, options, attempt + 1);
      }

      throw new Error(
        `Failed to fetch ${url} after ${attempt} attempts: ${
          error instanceof Error ? error.message : 'Unknown error'
        }`
      );
    }
  }

  /**
   * Delay utility for retry logic
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Clear all cached data
   */
  clearCache(): void {
    this.cache.clear();
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<boolean> {
    try {
      const url = `${this.config.baseUrl}/api/health`;
      const response = await fetch(url, {
        signal: AbortSignal.timeout(5000),
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}

/**
 * Example Usage:
 *
 * ```typescript
 * import { BackendDataAdapter } from './adapters/BackendDataAdapter';
 *
 * // Create adapter instance
 * const adapter = new BackendDataAdapter({
 *   baseUrl: 'http://localhost:8000',
 *   retries: 3,
 *   cacheEnabled: true,
 * });
 *
 * // Fetch backtest results
 * const backtest = await adapter.getBacktestResults('AAPL');
 * console.log('Win rate:', backtest.data.thresholds['5.0'].win_rates);
 *
 * // Fetch RSI chart and transform to MarketData
 * const rsiChart = await adapter.getRSIChart('AAPL', 252);
 * const marketData = adapter.transformToMarketData('AAPL', rsiChart);
 *
 * // Get percentile forward mapping
 * const percentileForward = await adapter.getPercentileForward('AAPL');
 * const percentileData = adapter.transformToPercentileData(percentileForward);
 *
 * // Run Monte Carlo simulation
 * const monteCarlo = await adapter.runMonteCarloSimulation({
 *   ticker: 'AAPL',
 *   num_simulations: 1000,
 *   max_periods: 21,
 * });
 *
 * // Get live signal
 * const liveSignal = await adapter.getLiveSignal('AAPL');
 * console.log('Signal strength:', liveSignal.signal.strength);
 *
 * // Multi-timeframe analysis
 * const mtfAnalysis = await adapter.getMultiTimeframeAnalysis('AAPL');
 * console.log('Current divergence:', mtfAnalysis.analysis.current_divergence);
 *
 * // Health check
 * const isHealthy = await adapter.healthCheck();
 * ```
 */
