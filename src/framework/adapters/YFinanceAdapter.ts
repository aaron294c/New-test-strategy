/**
 * Yahoo Finance Data Adapter
 *
 * Direct market data adapter using Yahoo Finance API
 * Provides real-time and historical OHLCV data
 * Can be used as fallback or primary data source
 */

import {
  MarketData,
  OHLCV,
  Timeframe,
} from '../core/types';

/**
 * Configuration for Yahoo Finance adapter
 */
export interface YFinanceAdapterConfig {
  apiKey?: string; // Optional API key for premium endpoints
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  userAgent?: string;
}

/**
 * Default configuration
 */
const DEFAULT_CONFIG: Required<YFinanceAdapterConfig> = {
  apiKey: '',
  timeout: 10000,
  retries: 3,
  retryDelay: 1000,
  userAgent: 'Mozilla/5.0 (compatible; TradingFramework/1.0)',
};

/**
 * Yahoo Finance response types
 */
interface YFinanceQuote {
  chart: {
    result: Array<{
      meta: {
        symbol: string;
        regularMarketPrice: number;
        previousClose: number;
      };
      timestamp: number[];
      indicators: {
        quote: Array<{
          open: number[];
          high: number[];
          low: number[];
          close: number[];
          volume: number[];
        }>;
      };
    }>;
    error: any;
  };
}

/**
 * Timeframe mapping to Yahoo Finance intervals
 */
const TIMEFRAME_INTERVALS: Record<Timeframe, string> = {
  [Timeframe.M1]: '1m',
  [Timeframe.M5]: '5m',
  [Timeframe.M15]: '15m',
  [Timeframe.M30]: '30m',
  [Timeframe.H1]: '1h',
  [Timeframe.H4]: '4h',
  [Timeframe.D1]: '1d',
  [Timeframe.W1]: '1wk',
};

/**
 * Yahoo Finance Data Adapter class
 */
export class YFinanceAdapter {
  private config: Required<YFinanceAdapterConfig>;
  private baseUrl = 'https://query1.finance.yahoo.com/v8/finance/chart';

  constructor(config: YFinanceAdapterConfig = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Fetch historical market data for a ticker
   */
  async getMarketData(
    ticker: string,
    timeframe: Timeframe = Timeframe.D1,
    period: string = '1y'
  ): Promise<MarketData> {
    const interval = TIMEFRAME_INTERVALS[timeframe];
    const url = `${this.baseUrl}/${ticker}?interval=${interval}&range=${period}`;

    const response = await this.fetchWithRetry<YFinanceQuote>(url);

    if (response.chart.error) {
      throw new Error(
        `Yahoo Finance API error: ${JSON.stringify(response.chart.error)}`
      );
    }

    const result = response.chart.result[0];
    if (!result) {
      throw new Error(`No data returned for ${ticker}`);
    }

    return this.transformToMarketData(ticker, result, timeframe);
  }

  /**
   * Get current quote for a ticker
   */
  async getCurrentPrice(ticker: string): Promise<number> {
    const url = `${this.baseUrl}/${ticker}?interval=1d&range=1d`;
    const response = await this.fetchWithRetry<YFinanceQuote>(url);

    if (response.chart.error) {
      throw new Error(
        `Yahoo Finance API error: ${JSON.stringify(response.chart.error)}`
      );
    }

    const result = response.chart.result[0];
    return result?.meta.regularMarketPrice || 0;
  }

  /**
   * Get multi-timeframe data for a ticker
   */
  async getMultiTimeframeData(
    ticker: string,
    timeframes: Timeframe[] = [Timeframe.H4, Timeframe.H1, Timeframe.D1]
  ): Promise<Map<Timeframe, MarketData>> {
    const dataMap = new Map<Timeframe, MarketData>();

    // Fetch all timeframes in parallel
    const promises = timeframes.map(async (tf) => {
      const data = await this.getMarketData(ticker, tf);
      return { timeframe: tf, data };
    });

    const results = await Promise.all(promises);

    results.forEach(({ timeframe, data }) => {
      dataMap.set(timeframe, data);
    });

    return dataMap;
  }

  /**
   * Transform Yahoo Finance response to MarketData format
   */
  private transformToMarketData(
    ticker: string,
    result: YFinanceQuote['chart']['result'][0],
    timeframe: Timeframe
  ): MarketData {
    const quote = result.indicators.quote[0];
    const timestamps = result.timestamp;

    const bars: OHLCV[] = timestamps.map((ts, i) => ({
      open: quote.open[i] || 0,
      high: quote.high[i] || 0,
      low: quote.low[i] || 0,
      close: quote.close[i] || 0,
      volume: quote.volume[i] || 0,
      timestamp: new Date(ts * 1000),
      timeframe,
    }));

    // Filter out invalid bars
    const validBars = bars.filter(
      (bar) => bar.open > 0 && bar.close > 0
    );

    return {
      instrument: ticker,
      bars: validBars,
      currentPrice: result.meta.regularMarketPrice,
      lastUpdate: new Date(),
    };
  }

  /**
   * Calculate technical indicators from market data
   */
  calculateRSI(bars: OHLCV[], period = 14): number[] {
    const closes = bars.map((b) => b.close);
    const rsi: number[] = [];

    for (let i = 0; i < closes.length; i++) {
      if (i < period) {
        rsi.push(50); // Neutral RSI for initial period
        continue;
      }

      let gains = 0;
      let losses = 0;

      for (let j = i - period + 1; j <= i; j++) {
        const change = closes[j] - closes[j - 1];
        if (change > 0) {
          gains += change;
        } else {
          losses += Math.abs(change);
        }
      }

      const avgGain = gains / period;
      const avgLoss = losses / period;

      if (avgLoss === 0) {
        rsi.push(100);
      } else {
        const rs = avgGain / avgLoss;
        rsi.push(100 - 100 / (1 + rs));
      }
    }

    return rsi;
  }

  /**
   * Calculate Simple Moving Average
   */
  calculateSMA(values: number[], period: number): number[] {
    const sma: number[] = [];

    for (let i = 0; i < values.length; i++) {
      if (i < period - 1) {
        sma.push(values[i]); // Not enough data yet
        continue;
      }

      const sum = values
        .slice(i - period + 1, i + 1)
        .reduce((acc, val) => acc + val, 0);
      sma.push(sum / period);
    }

    return sma;
  }

  /**
   * Calculate RSI-MA (RSI with MA smoothing)
   */
  calculateRSIMA(
    bars: OHLCV[],
    rsiPeriod = 14,
    maPeriod = 14
  ): number[] {
    const rsi = this.calculateRSI(bars, rsiPeriod);
    return this.calculateSMA(rsi, maPeriod);
  }

  /**
   * Generic fetch with retry logic
   */
  private async fetchWithRetry<T>(
    url: string,
    attempt = 1
  ): Promise<T> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(
        () => controller.abort(),
        this.config.timeout
      );

      const response = await fetch(url, {
        signal: controller.signal,
        headers: {
          'User-Agent': this.config.userAgent,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (attempt < this.config.retries) {
        await this.delay(this.config.retryDelay * attempt);
        return this.fetchWithRetry<T>(url, attempt + 1);
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
   * Validate ticker symbol
   */
  async validateTicker(ticker: string): Promise<boolean> {
    try {
      await this.getCurrentPrice(ticker);
      return true;
    } catch {
      return false;
    }
  }
}

/**
 * Example Usage:
 *
 * ```typescript
 * import { YFinanceAdapter } from './adapters/YFinanceAdapter';
 * import { Timeframe } from '../core/types';
 *
 * // Create adapter instance
 * const adapter = new YFinanceAdapter({
 *   retries: 3,
 *   timeout: 10000,
 * });
 *
 * // Get daily market data
 * const dailyData = await adapter.getMarketData('AAPL', Timeframe.D1, '1y');
 * console.log('Current price:', dailyData.currentPrice);
 * console.log('Total bars:', dailyData.bars.length);
 *
 * // Get 4-hour data
 * const fourHourData = await adapter.getMarketData('AAPL', Timeframe.H4, '1mo');
 *
 * // Get multi-timeframe data
 * const mtfData = await adapter.getMultiTimeframeData('AAPL', [
 *   Timeframe.H1,
 *   Timeframe.H4,
 *   Timeframe.D1,
 * ]);
 *
 * // Calculate RSI-MA
 * const rsiMa = adapter.calculateRSIMA(dailyData.bars, 14, 14);
 * console.log('Latest RSI-MA:', rsiMa[rsiMa.length - 1]);
 *
 * // Validate ticker
 * const isValid = await adapter.validateTicker('AAPL');
 * console.log('Ticker valid:', isValid);
 *
 * // Get current price only
 * const price = await adapter.getCurrentPrice('AAPL');
 * console.log('Current price:', price);
 * ```
 */
