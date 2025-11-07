/**
 * Data Loading Utilities for Backtesting
 *
 * Provides utilities to load historical market data from various sources
 * and convert to framework-compatible format
 */

import { OHLCV, Timeframe } from '../core/types';

/**
 * Raw OHLCV data format (from data sources)
 */
export interface RawOHLCV {
  timestamp: string | Date | number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

/**
 * Data loader configuration
 */
export interface DataLoaderConfig {
  /** Timeframe to load */
  timeframe: Timeframe;
  /** Date range */
  startDate: Date;
  endDate: Date;
  /** Validate data quality */
  validateData: boolean;
}

/**
 * Backtest Data Loader
 */
export class BacktestDataLoader {
  /**
   * Load data from CSV file
   */
  public static async loadFromCSV(
    filePath: string,
    config: Partial<DataLoaderConfig> = {}
  ): Promise<OHLCV[]> {
    // Implementation would use fs to read CSV
    // This is a placeholder for the structure
    throw new Error('loadFromCSV not implemented - requires filesystem access');
  }

  /**
   * Load data from JSON file
   */
  public static async loadFromJSON(
    filePath: string,
    config: Partial<DataLoaderConfig> = {}
  ): Promise<OHLCV[]> {
    // Implementation would use fs to read JSON
    throw new Error('loadFromJSON not implemented - requires filesystem access');
  }

  /**
   * Load data from API (e.g., yfinance-compatible format)
   */
  public static async loadFromAPI(
    symbol: string,
    config: Partial<DataLoaderConfig> = {}
  ): Promise<OHLCV[]> {
    // Implementation would fetch from API
    throw new Error('loadFromAPI not implemented - requires API integration');
  }

  /**
   * Convert raw OHLCV data to framework format
   */
  public static convertToFrameworkFormat(
    rawData: RawOHLCV[],
    timeframe: Timeframe
  ): OHLCV[] {
    return rawData.map(bar => ({
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
      volume: bar.volume,
      timestamp: this.normalizeTimestamp(bar.timestamp),
      timeframe,
    }));
  }

  /**
   * Load data from Python backend format
   */
  public static loadFromBackendFormat(
    data: any[],
    timeframe: Timeframe = Timeframe.H4
  ): OHLCV[] {
    return data.map((item: any) => {
      // Handle various timestamp formats from backend
      let timestamp: Date;

      if (item.timestamp) {
        timestamp = new Date(item.timestamp);
      } else if (item.date) {
        timestamp = new Date(item.date);
      } else if (item.time) {
        timestamp = new Date(item.time);
      } else {
        timestamp = new Date();
      }

      return {
        open: item.open || item.Open || 0,
        high: item.high || item.High || 0,
        low: item.low || item.Low || 0,
        close: item.close || item.Close || 0,
        volume: item.volume || item.Volume || 0,
        timestamp,
        timeframe,
      };
    });
  }

  /**
   * Validate OHLCV data quality
   */
  public static validateData(bars: OHLCV[]): {
    valid: boolean;
    errors: string[];
    warnings: string[];
  } {
    const errors: string[] = [];
    const warnings: string[] = [];

    if (bars.length === 0) {
      errors.push('No data provided');
      return { valid: false, errors, warnings };
    }

    bars.forEach((bar, index) => {
      // Check for invalid prices
      if (bar.high < bar.low) {
        errors.push(`Bar ${index}: High (${bar.high}) < Low (${bar.low})`);
      }

      if (bar.close < bar.low || bar.close > bar.high) {
        warnings.push(`Bar ${index}: Close outside High/Low range`);
      }

      if (bar.open < bar.low || bar.open > bar.high) {
        warnings.push(`Bar ${index}: Open outside High/Low range`);
      }

      // Check for zero or negative prices
      if (bar.open <= 0 || bar.high <= 0 || bar.low <= 0 || bar.close <= 0) {
        errors.push(`Bar ${index}: Invalid price (zero or negative)`);
      }

      // Check for zero volume (warning only)
      if (bar.volume === 0) {
        warnings.push(`Bar ${index}: Zero volume`);
      }
    });

    // Check for gaps in timestamps
    for (let i = 1; i < bars.length; i++) {
      const prevTime = bars[i - 1].timestamp.getTime();
      const currTime = bars[i].timestamp.getTime();

      if (currTime <= prevTime) {
        errors.push(`Bar ${i}: Timestamp not in ascending order`);
      }
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings,
    };
  }

  /**
   * Resample data to different timeframe
   */
  public static resampleData(
    bars: OHLCV[],
    targetTimeframe: Timeframe
  ): OHLCV[] {
    // Get timeframe duration in milliseconds
    const duration = this.getTimeframeDuration(targetTimeframe);

    const resampled: OHLCV[] = [];
    let currentBar: OHLCV | null = null;
    let barStart: number = 0;

    bars.forEach(bar => {
      const barTime = bar.timestamp.getTime();

      // Determine if this bar belongs to current resampled bar
      if (!currentBar || barTime >= barStart + duration) {
        // Start new resampled bar
        if (currentBar) {
          resampled.push(currentBar);
        }

        barStart = Math.floor(barTime / duration) * duration;
        currentBar = {
          ...bar,
          timestamp: new Date(barStart),
          timeframe: targetTimeframe,
        };
      } else {
        // Update current resampled bar
        currentBar.high = Math.max(currentBar.high, bar.high);
        currentBar.low = Math.min(currentBar.low, bar.low);
        currentBar.close = bar.close;
        currentBar.volume += bar.volume;
      }
    });

    // Add final bar
    if (currentBar) {
      resampled.push(currentBar);
    }

    return resampled;
  }

  /**
   * Fill gaps in data with forward-fill
   */
  public static fillGaps(bars: OHLCV[]): OHLCV[] {
    if (bars.length === 0) return bars;

    const filled: OHLCV[] = [bars[0]];
    const duration = this.getTimeframeDuration(bars[0].timeframe);

    for (let i = 1; i < bars.length; i++) {
      const prevBar = filled[filled.length - 1];
      const currentBar = bars[i];

      const expectedTime = prevBar.timestamp.getTime() + duration;
      const actualTime = currentBar.timestamp.getTime();

      // Fill any gaps
      while (expectedTime < actualTime) {
        const gapBar: OHLCV = {
          open: prevBar.close,
          high: prevBar.close,
          low: prevBar.close,
          close: prevBar.close,
          volume: 0,
          timestamp: new Date(expectedTime),
          timeframe: prevBar.timeframe,
        };
        filled.push(gapBar);
      }

      filled.push(currentBar);
    }

    return filled;
  }

  /**
   * Normalize timestamp to Date object
   */
  private static normalizeTimestamp(timestamp: string | Date | number): Date {
    if (timestamp instanceof Date) {
      return timestamp;
    }

    if (typeof timestamp === 'number') {
      // Check if seconds or milliseconds
      if (timestamp < 10000000000) {
        return new Date(timestamp * 1000); // Seconds
      }
      return new Date(timestamp); // Milliseconds
    }

    return new Date(timestamp);
  }

  /**
   * Get timeframe duration in milliseconds
   */
  private static getTimeframeDuration(timeframe: Timeframe): number {
    const durations: Record<Timeframe, number> = {
      [Timeframe.M1]: 60 * 1000,
      [Timeframe.M5]: 5 * 60 * 1000,
      [Timeframe.M15]: 15 * 60 * 1000,
      [Timeframe.M30]: 30 * 60 * 1000,
      [Timeframe.H1]: 60 * 60 * 1000,
      [Timeframe.H4]: 4 * 60 * 60 * 1000,
      [Timeframe.D1]: 24 * 60 * 60 * 1000,
      [Timeframe.W1]: 7 * 24 * 60 * 60 * 1000,
    };

    return durations[timeframe] || 60 * 60 * 1000;
  }

  /**
   * Split data into train/test sets
   */
  public static splitData(
    bars: OHLCV[],
    trainRatio: number = 0.7
  ): { train: OHLCV[]; test: OHLCV[] } {
    const splitIndex = Math.floor(bars.length * trainRatio);

    return {
      train: bars.slice(0, splitIndex),
      test: bars.slice(splitIndex),
    };
  }

  /**
   * Generate synthetic data for testing
   */
  public static generateSyntheticData(
    config: {
      bars: number;
      initialPrice: number;
      volatility: number;
      trend: number;
      timeframe: Timeframe;
      startDate: Date;
    }
  ): OHLCV[] {
    const bars: OHLCV[] = [];
    const duration = this.getTimeframeDuration(config.timeframe);

    let price = config.initialPrice;
    let timestamp = config.startDate.getTime();

    for (let i = 0; i < config.bars; i++) {
      // Random walk with trend
      const change = (Math.random() - 0.5) * config.volatility + config.trend;
      price *= (1 + change);

      const high = price * (1 + Math.random() * config.volatility * 0.5);
      const low = price * (1 - Math.random() * config.volatility * 0.5);
      const open = low + Math.random() * (high - low);
      const close = low + Math.random() * (high - low);

      bars.push({
        open,
        high,
        low,
        close,
        volume: Math.floor(Math.random() * 1000000) + 100000,
        timestamp: new Date(timestamp),
        timeframe: config.timeframe,
      });

      timestamp += duration;
    }

    return bars;
  }
}
