/**
 * Yahoo Finance Adapter - Example Usage
 *
 * This file demonstrates how to use the YFinanceAdapter to fetch
 * real-time and historical market data directly from Yahoo Finance.
 */

import { YFinanceAdapter } from '../../../src/framework/adapters/YFinanceAdapter';
import { Timeframe } from '../../../src/framework/core/types';

/**
 * Example 1: Basic market data retrieval
 */
async function example1_basicMarketData() {
  console.log('\n=== Example 1: Basic Market Data ===\n');

  const adapter = new YFinanceAdapter();

  try {
    // Get 1 year of daily data
    const dailyData = await adapter.getMarketData('AAPL', Timeframe.D1, '1y');

    console.log('Instrument:', dailyData.instrument);
    console.log('Current price:', dailyData.currentPrice);
    console.log('Total bars:', dailyData.bars.length);

    // Latest 5 bars
    console.log('\nLatest 5 bars:');
    dailyData.bars.slice(-5).forEach((bar) => {
      console.log(
        `${bar.timestamp.toISOString().split('T')[0]}: O=${bar.open.toFixed(2)} H=${bar.high.toFixed(2)} L=${bar.low.toFixed(2)} C=${bar.close.toFixed(2)} V=${bar.volume}`
      );
    });

    // Calculate price change
    const firstPrice = dailyData.bars[0].close;
    const lastPrice = dailyData.bars[dailyData.bars.length - 1].close;
    const change = ((lastPrice - firstPrice) / firstPrice) * 100;

    console.log('\nYTD Performance:');
    console.log(`- Start price: $${firstPrice.toFixed(2)}`);
    console.log(`- Current price: $${lastPrice.toFixed(2)}`);
    console.log(`- Change: ${change > 0 ? '+' : ''}${change.toFixed(2)}%`);
  } catch (error) {
    console.error('Error:', error instanceof Error ? error.message : error);
  }
}

/**
 * Example 2: Multi-timeframe data
 */
async function example2_multiTimeframe() {
  console.log('\n=== Example 2: Multi-Timeframe Data ===\n');

  const adapter = new YFinanceAdapter();

  try {
    // Get data for multiple timeframes
    const mtfData = await adapter.getMultiTimeframeData('AAPL', [
      Timeframe.H1,
      Timeframe.H4,
      Timeframe.D1,
    ]);

    console.log('Retrieved data for', mtfData.size, 'timeframes\n');

    for (const [timeframe, data] of mtfData) {
      console.log(`${timeframe}:`);
      console.log(`- Bars: ${data.bars.length}`);
      console.log(`- Current price: $${data.currentPrice.toFixed(2)}`);
      console.log(`- Last update: ${data.lastUpdate.toISOString()}`);

      if (data.bars.length > 0) {
        const latest = data.bars[data.bars.length - 1];
        console.log(
          `- Latest bar: ${latest.timestamp.toISOString()} | C=${latest.close.toFixed(2)}`
        );
      }
      console.log();
    }
  } catch (error) {
    console.error('Error:', error instanceof Error ? error.message : error);
  }
}

/**
 * Example 3: Technical indicators
 */
async function example3_technicalIndicators() {
  console.log('\n=== Example 3: Technical Indicators ===\n');

  const adapter = new YFinanceAdapter();

  try {
    // Get daily data
    const data = await adapter.getMarketData('AAPL', Timeframe.D1, '6mo');

    // Calculate RSI
    const rsi = adapter.calculateRSI(data.bars, 14);

    // Calculate SMA
    const closes = data.bars.map((b) => b.close);
    const sma20 = adapter.calculateSMA(closes, 20);
    const sma50 = adapter.calculateSMA(closes, 50);

    // Calculate RSI-MA
    const rsiMa = adapter.calculateRSIMA(data.bars, 14, 14);

    console.log('Technical Indicators (latest values):');
    console.log('- RSI(14):', rsi[rsi.length - 1].toFixed(2));
    console.log('- RSI-MA(14,14):', rsiMa[rsiMa.length - 1].toFixed(2));
    console.log('- SMA(20):', sma20[sma20.length - 1].toFixed(2));
    console.log('- SMA(50):', sma50[sma50.length - 1].toFixed(2));
    console.log('- Current price:', data.currentPrice.toFixed(2));

    // Trend analysis
    const currentPrice = data.currentPrice;
    const isBullish20 = currentPrice > sma20[sma20.length - 1];
    const isBullish50 = currentPrice > sma50[sma50.length - 1];
    const sma20AboveSma50 = sma20[sma20.length - 1] > sma50[sma50.length - 1];

    console.log('\nTrend Analysis:');
    console.log('- Price above SMA(20):', isBullish20 ? 'Yes ✓' : 'No ✗');
    console.log('- Price above SMA(50):', isBullish50 ? 'Yes ✓' : 'No ✗');
    console.log('- SMA(20) above SMA(50):', sma20AboveSma50 ? 'Yes ✓' : 'No ✗');

    const currentRsi = rsi[rsi.length - 1];
    let rsiSignal = 'Neutral';
    if (currentRsi > 70) rsiSignal = 'Overbought';
    else if (currentRsi < 30) rsiSignal = 'Oversold';

    console.log('- RSI Signal:', rsiSignal);
  } catch (error) {
    console.error('Error:', error instanceof Error ? error.message : error);
  }
}

/**
 * Example 4: Ticker validation
 */
async function example4_tickerValidation() {
  console.log('\n=== Example 4: Ticker Validation ===\n');

  const adapter = new YFinanceAdapter();

  const tickers = ['AAPL', 'MSFT', 'INVALID123', 'GOOGL', 'FAKE'];

  console.log('Validating tickers...\n');

  for (const ticker of tickers) {
    try {
      const isValid = await adapter.validateTicker(ticker);
      console.log(`${ticker}: ${isValid ? '✓ Valid' : '✗ Invalid'}`);
    } catch (error) {
      console.log(`${ticker}: ✗ Invalid (${error instanceof Error ? error.message : 'Unknown error'})`);
    }
  }
}

/**
 * Example 5: Current price lookup
 */
async function example5_currentPrice() {
  console.log('\n=== Example 5: Current Price Lookup ===\n');

  const adapter = new YFinanceAdapter();

  const tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META'];

  console.log('Fetching current prices...\n');

  const prices: Record<string, number> = {};

  for (const ticker of tickers) {
    try {
      const price = await adapter.getCurrentPrice(ticker);
      prices[ticker] = price;
      console.log(`${ticker}: $${price.toFixed(2)}`);
    } catch (error) {
      console.log(`${ticker}: Error - ${error instanceof Error ? error.message : 'Unknown'}`);
    }
  }

  // Portfolio value example
  const portfolio = {
    AAPL: 10,
    MSFT: 5,
    GOOGL: 3,
  };

  let totalValue = 0;
  console.log('\nPortfolio Value:');
  Object.entries(portfolio).forEach(([ticker, shares]) => {
    const value = shares * (prices[ticker] || 0);
    totalValue += value;
    console.log(`- ${ticker}: ${shares} shares × $${(prices[ticker] || 0).toFixed(2)} = $${value.toFixed(2)}`);
  });

  console.log(`\nTotal Portfolio Value: $${totalValue.toFixed(2)}`);
}

/**
 * Example 6: Intraday data (4-hour)
 */
async function example6_intradayData() {
  console.log('\n=== Example 6: Intraday 4-Hour Data ===\n');

  const adapter = new YFinanceAdapter();

  try {
    // Get 1 month of 4-hour data
    const fourHourData = await adapter.getMarketData('AAPL', Timeframe.H4, '1mo');

    console.log('Instrument:', fourHourData.instrument);
    console.log('Total 4H bars:', fourHourData.bars.length);
    console.log('Current price:', fourHourData.currentPrice);

    // Latest 10 bars
    console.log('\nLatest 10 bars (4-hour):');
    fourHourData.bars.slice(-10).forEach((bar) => {
      const time = bar.timestamp.toISOString().split('T');
      const date = time[0];
      const hour = time[1].substring(0, 5);
      console.log(
        `${date} ${hour}: C=${bar.close.toFixed(2)} H=${bar.high.toFixed(2)} L=${bar.low.toFixed(2)} V=${bar.volume}`
      );
    });

    // Calculate intraday volatility
    const returns = fourHourData.bars
      .slice(-20)
      .map((bar, i, arr) => (i > 0 ? (bar.close - arr[i - 1].close) / arr[i - 1].close : 0));

    const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
    const variance =
      returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length;
    const stdDev = Math.sqrt(variance);

    console.log('\nIntraday Statistics (last 20 bars):');
    console.log('- Average 4H return:', (avgReturn * 100).toFixed(3), '%');
    console.log('- Std deviation:', (stdDev * 100).toFixed(3), '%');
    console.log('- Annualized volatility:', (stdDev * Math.sqrt(365 * 6) * 100).toFixed(2), '%');
  } catch (error) {
    console.error('Error:', error instanceof Error ? error.message : error);
  }
}

/**
 * Example 7: Compare multiple tickers
 */
async function example7_compareTickets() {
  console.log('\n=== Example 7: Compare Multiple Tickers ===\n');

  const adapter = new YFinanceAdapter();
  const tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN'];

  console.log('Fetching 3-month performance for comparison...\n');

  for (const ticker of tickers) {
    try {
      const data = await adapter.getMarketData(ticker, Timeframe.D1, '3mo');

      const firstPrice = data.bars[0].close;
      const lastPrice = data.bars[data.bars.length - 1].close;
      const change = ((lastPrice - firstPrice) / firstPrice) * 100;

      // Calculate RSI
      const rsi = adapter.calculateRSI(data.bars, 14);
      const currentRsi = rsi[rsi.length - 1];

      console.log(`${ticker}:`);
      console.log(`  - 3-month return: ${change > 0 ? '+' : ''}${change.toFixed(2)}%`);
      console.log(`  - Current price: $${lastPrice.toFixed(2)}`);
      console.log(`  - RSI(14): ${currentRsi.toFixed(2)}`);
      console.log();
    } catch (error) {
      console.log(`${ticker}: Error - ${error instanceof Error ? error.message : 'Unknown'}\n`);
    }
  }
}

/**
 * Example 8: Error handling
 */
async function example8_errorHandling() {
  console.log('\n=== Example 8: Error Handling ===\n');

  const adapter = new YFinanceAdapter({
    timeout: 5000,
    retries: 2,
  });

  // Test various error scenarios
  console.log('Testing error scenarios:\n');

  // Invalid ticker
  console.log('1. Invalid ticker:');
  try {
    await adapter.getMarketData('INVALID_TICKER_123', Timeframe.D1, '1mo');
  } catch (error) {
    console.log('   ✓ Caught error:', error instanceof Error ? error.message : 'Unknown');
  }

  // Invalid timeframe (this might work, but let's show handling)
  console.log('\n2. Timeout handling (using very short timeout):');
  const shortTimeoutAdapter = new YFinanceAdapter({ timeout: 1 }); // 1ms timeout
  try {
    await shortTimeoutAdapter.getMarketData('AAPL', Timeframe.D1, '1y');
  } catch (error) {
    console.log('   ✓ Caught timeout:', error instanceof Error ? error.message : 'Unknown');
  }

  console.log('\n3. Successful retry:');
  try {
    const data = await adapter.getMarketData('AAPL', Timeframe.D1, '1mo');
    console.log('   ✓ Successfully fetched', data.bars.length, 'bars after retry logic');
  } catch (error) {
    console.log('   ✗ Failed:', error instanceof Error ? error.message : 'Unknown');
  }
}

/**
 * Run all examples
 */
async function runAllExamples() {
  console.log('╔════════════════════════════════════════════════════════════════╗');
  console.log('║  Yahoo Finance Adapter - Example Usage                        ║');
  console.log('╚════════════════════════════════════════════════════════════════╝');

  await example1_basicMarketData();
  await example2_multiTimeframe();
  await example3_technicalIndicators();
  await example4_tickerValidation();
  await example5_currentPrice();
  await example6_intradayData();
  await example7_compareTickets();
  await example8_errorHandling();

  console.log('\n✅ All examples completed!\n');
}

// Run examples if executed directly
if (require.main === module) {
  runAllExamples().catch(console.error);
}

export {
  example1_basicMarketData,
  example2_multiTimeframe,
  example3_technicalIndicators,
  example4_tickerValidation,
  example5_currentPrice,
  example6_intradayData,
  example7_compareTickets,
  example8_errorHandling,
};
