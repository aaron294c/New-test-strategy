/**
 * Mock Data Generators for Testing
 *
 * Provides realistic market data for unit and integration tests
 */

import {
  OHLCV,
  MarketData,
  Timeframe,
  RegimeType,
  TimeframeWeight,
  MultiTimeframeRegime,
  RegimeSignal,
} from '../../../src/framework/core/types';

/**
 * Generate mock OHLCV bars with realistic price movements
 */
export function generateMockBars(
  count: number,
  timeframe: Timeframe = Timeframe.H4,
  options: {
    startPrice?: number;
    volatility?: number;
    trend?: 'up' | 'down' | 'sideways';
    startDate?: Date;
  } = {}
): OHLCV[] {
  const {
    startPrice = 100,
    volatility = 0.02,
    trend = 'sideways',
    startDate = new Date('2024-01-01'),
  } = options;

  const bars: OHLCV[] = [];
  let currentPrice = startPrice;
  let currentDate = new Date(startDate);

  const trendBias = trend === 'up' ? 0.001 : trend === 'down' ? -0.001 : 0;

  for (let i = 0; i < count; i++) {
    // Add trend bias and random walk
    const change = (Math.random() - 0.5) * volatility + trendBias;
    currentPrice *= 1 + change;

    // Generate OHLC from close
    const low = currentPrice * (1 - Math.random() * volatility);
    const high = currentPrice * (1 + Math.random() * volatility);
    const open = low + Math.random() * (high - low);
    const close = low + Math.random() * (high - low);

    bars.push({
      open,
      high,
      low,
      close,
      volume: Math.random() * 1000000 + 100000,
      timestamp: new Date(currentDate),
      timeframe,
    });

    // Increment time based on timeframe
    currentDate = incrementTime(currentDate, timeframe);
    currentPrice = close;
  }

  return bars;
}

/**
 * Generate trending market data
 */
export function generateTrendingBars(
  count: number,
  direction: 'up' | 'down',
  timeframe: Timeframe = Timeframe.H4
): OHLCV[] {
  return generateMockBars(count, timeframe, {
    trend: direction,
    volatility: 0.015,
  });
}

/**
 * Generate mean-reverting market data
 */
export function generateMeanRevertingBars(
  count: number,
  timeframe: Timeframe = Timeframe.H4
): OHLCV[] {
  const bars: OHLCV[] = [];
  const meanPrice = 100;
  let currentPrice = 100;
  let currentDate = new Date('2024-01-01');

  for (let i = 0; i < count; i++) {
    // Mean reversion: pull towards mean
    const pullToMean = (meanPrice - currentPrice) * 0.1;
    const randomWalk = (Math.random() - 0.5) * 0.02;
    currentPrice += pullToMean + randomWalk;

    const volatility = 0.01;
    const low = currentPrice * (1 - Math.random() * volatility);
    const high = currentPrice * (1 + Math.random() * volatility);
    const open = low + Math.random() * (high - low);
    const close = low + Math.random() * (high - low);

    bars.push({
      open,
      high,
      low,
      close,
      volume: Math.random() * 1000000 + 100000,
      timestamp: new Date(currentDate),
      timeframe,
    });

    currentDate = incrementTime(currentDate, timeframe);
    currentPrice = close;
  }

  return bars;
}

/**
 * Generate volatile market data
 */
export function generateVolatileBars(
  count: number,
  timeframe: Timeframe = Timeframe.H4
): OHLCV[] {
  return generateMockBars(count, timeframe, {
    volatility: 0.05, // High volatility
  });
}

/**
 * Generate complete MarketData object
 */
export function generateMockMarketData(
  instrument: string = 'AAPL',
  barCount: number = 200,
  options?: {
    trend?: 'up' | 'down' | 'sideways';
    timeframe?: Timeframe;
  }
): MarketData {
  const timeframe = options?.timeframe ?? Timeframe.H4;
  const bars = generateMockBars(barCount, timeframe, {
    trend: options?.trend,
  });

  const currentPrice = bars[bars.length - 1].close;

  return {
    instrument,
    bars,
    currentPrice,
    bid: currentPrice - 0.01,
    ask: currentPrice + 0.01,
    spread: 0.02,
    lastUpdate: new Date(),
  };
}

/**
 * Generate multi-timeframe market data
 */
export function generateMultiTimeframeData(
  instrument: string = 'AAPL',
  timeframes: Timeframe[] = [Timeframe.H1, Timeframe.H4, Timeframe.D1]
): MarketData {
  const allBars: OHLCV[] = [];

  timeframes.forEach((tf) => {
    const bars = generateMockBars(200, tf);
    allBars.push(...bars);
  });

  const currentPrice = allBars[allBars.length - 1].close;

  return {
    instrument,
    bars: allBars,
    currentPrice,
    lastUpdate: new Date(),
  };
}

/**
 * Generate mock regime signal
 */
export function generateMockRegimeSignal(
  type: RegimeType = RegimeType.NEUTRAL,
  timeframe: Timeframe = Timeframe.H4,
  confidence: number = 0.7
): RegimeSignal {
  return {
    type,
    confidence,
    strength: type === RegimeType.MOMENTUM ? 0.6 : type === RegimeType.MEAN_REVERSION ? -0.5 : 0,
    timeframe,
    timestamp: new Date(),
    metrics: {
      trendStrength: type === RegimeType.MOMENTUM ? 35 : 15,
      volatilityRatio: 1.0,
      meanReversionSpeed: type === RegimeType.MEAN_REVERSION ? 0.7 : 0.3,
      momentumPersistence: type === RegimeType.MOMENTUM ? 0.6 : 0.2,
    },
  };
}

/**
 * Generate multi-timeframe regime
 */
export function generateMockMultiTimeframeRegime(
  dominantType: RegimeType = RegimeType.NEUTRAL,
  coherence: number = 0.7
): MultiTimeframeRegime {
  const regimes: RegimeSignal[] = [
    generateMockRegimeSignal(dominantType, Timeframe.H1, 0.6),
    generateMockRegimeSignal(dominantType, Timeframe.H4, 0.8),
    generateMockRegimeSignal(dominantType, Timeframe.D1, 0.7),
  ];

  return {
    regimes,
    coherence,
    dominantRegime: dominantType,
    timestamp: new Date(),
  };
}

/**
 * Increment time based on timeframe
 */
function incrementTime(date: Date, timeframe: Timeframe): Date {
  const newDate = new Date(date);

  switch (timeframe) {
    case Timeframe.M1:
      newDate.setMinutes(newDate.getMinutes() + 1);
      break;
    case Timeframe.M5:
      newDate.setMinutes(newDate.getMinutes() + 5);
      break;
    case Timeframe.M15:
      newDate.setMinutes(newDate.getMinutes() + 15);
      break;
    case Timeframe.M30:
      newDate.setMinutes(newDate.getMinutes() + 30);
      break;
    case Timeframe.H1:
      newDate.setHours(newDate.getHours() + 1);
      break;
    case Timeframe.H4:
      newDate.setHours(newDate.getHours() + 4);
      break;
    case Timeframe.D1:
      newDate.setDate(newDate.getDate() + 1);
      break;
    case Timeframe.W1:
      newDate.setDate(newDate.getDate() + 7);
      break;
  }

  return newDate;
}

/**
 * Generate price at specific percentile
 */
export function generatePriceAtPercentile(
  bars: OHLCV[],
  percentile: number
): number {
  const closes = bars.map((b) => b.close).sort((a, b) => a - b);
  const index = Math.floor((percentile / 100) * (closes.length - 1));
  return closes[index];
}

/**
 * Default timeframe weights for testing
 */
export function getDefaultTimeframeWeights(): TimeframeWeight[] {
  return [
    { timeframe: Timeframe.H4, weight: 0.5 },
    { timeframe: Timeframe.H1, weight: 0.3 },
    { timeframe: Timeframe.D1, weight: 0.2 },
  ];
}
