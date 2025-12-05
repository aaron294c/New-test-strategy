/**
 * Backend Data Adapter - Example Usage
 *
 * This file demonstrates how to use the BackendDataAdapter to connect
 * to the Python backend API and retrieve trading data.
 */

import { BackendDataAdapter } from '../../../src/framework/adapters/BackendDataAdapter';
import { Timeframe } from '../../../src/framework/core/types';

/**
 * Example 1: Basic backtest data retrieval
 */
async function example1_backtestData() {
  console.log('\n=== Example 1: Backtest Data ===\n');

  const adapter = new BackendDataAdapter({
    baseUrl: 'http://localhost:8000',
    cacheEnabled: true,
  });

  try {
    // Check if backend is healthy
    const isHealthy = await adapter.healthCheck();
    console.log('Backend healthy:', isHealthy);

    if (!isHealthy) {
      console.log('Backend is not running. Start it with: cd backend && python api.py');
      return;
    }

    // Get backtest results for AAPL
    const backtest = await adapter.getBacktestResults('AAPL');

    console.log('Ticker:', backtest.ticker);
    console.log('Data source:', backtest.source);
    console.log('Available thresholds:', Object.keys(backtest.data.thresholds));

    // Analyze 5% threshold
    const threshold5 = backtest.data.thresholds['5.0'];
    if (threshold5) {
      console.log('\n5% Threshold Analysis:');
      console.log('- Total events:', threshold5.events);
      console.log('- Win rates by day:', threshold5.win_rates);
      console.log('- Optimal exit:', threshold5.optimal_exit_strategy);
      console.log('- Risk metrics:', threshold5.risk_metrics);
    }

    // Transform to framework risk metrics
    const riskMetrics = adapter.transformRiskMetrics(backtest, '5.0');
    console.log('\nFramework Risk Metrics:', riskMetrics);
  } catch (error) {
    console.error('Error:', error instanceof Error ? error.message : error);
  }
}

/**
 * Example 2: RSI chart data and visualization
 */
async function example2_rsiChart() {
  console.log('\n=== Example 2: RSI Chart Data ===\n');

  const adapter = new BackendDataAdapter();

  try {
    // Get RSI chart data for last 252 days (1 year)
    const rsiChart = await adapter.getRSIChart('AAPL', 252);

    console.log('Ticker:', rsiChart.ticker);
    console.log('Data points:', rsiChart.chart_data.dates.length);

    // Current state
    console.log('\nCurrent State:');
    console.log('- Price:', rsiChart.chart_data.current.price);
    console.log('- RSI:', rsiChart.chart_data.current.rsi.toFixed(2));
    console.log('- RSI-MA:', rsiChart.chart_data.current.rsi_ma.toFixed(2));
    console.log('- Percentile:', rsiChart.chart_data.current.percentile.toFixed(2));

    // Transform to framework MarketData
    const marketData = adapter.transformToMarketData('AAPL', rsiChart);

    console.log('\nMarket Data:');
    console.log('- Instrument:', marketData.instrument);
    console.log('- Total bars:', marketData.bars.length);
    console.log('- Current price:', marketData.currentPrice);
    console.log('- Last update:', marketData.lastUpdate);

    // Latest 5 bars
    console.log('\nLatest 5 bars:');
    marketData.bars.slice(-5).forEach((bar) => {
      console.log(`${bar.timestamp.toISOString()}: Close=${bar.close}`);
    });
  } catch (error) {
    console.error('Error:', error instanceof Error ? error.message : error);
  }
}

/**
 * Example 3: Percentile forward mapping
 */
async function example3_percentileForward() {
  console.log('\n=== Example 3: Percentile Forward Mapping ===\n');

  const adapter = new BackendDataAdapter();

  try {
    // Get percentile forward mapping
    const forward = await adapter.getPercentileForward('AAPL');

    console.log('Ticker:', forward.ticker);
    console.log('Current percentile:', forward.current_state.current_percentile);
    console.log('Current RSI-MA:', forward.current_state.current_rsi_ma);

    // Predictions
    console.log('\nEnsemble Predictions:');
    console.log('- 1-day:', forward.prediction.ensemble_forecast_1d?.toFixed(2), '%');
    console.log('- 5-day:', forward.prediction.ensemble_forecast_5d?.toFixed(2), '%');
    console.log('- 10-day:', forward.prediction.ensemble_forecast_10d?.toFixed(2), '%');
    console.log('- 21-day:', forward.prediction.ensemble_forecast_21d?.toFixed(2), '%');

    // Accuracy metrics
    console.log('\nModel Accuracy (1-day):');
    const metrics1d = forward.accuracy_metrics['1d'];
    if (metrics1d) {
      console.log('- Hit rate:', (metrics1d.hit_rate * 100).toFixed(1), '%');
      console.log('- Sharpe ratio:', metrics1d.sharpe.toFixed(2));
      console.log('- MAE:', metrics1d.mae.toFixed(2), '%');
      console.log('- RMSE:', metrics1d.rmse.toFixed(2), '%');
    }

    // Transform to framework PercentileData
    const percentileData = adapter.transformToPercentileData(forward, Timeframe.D1);

    console.log('\nFramework Percentile Data:');
    console.log('- Value:', percentileData.value.toFixed(2));
    console.log('- Percentile:', percentileData.percentile.toFixed(2));
    console.log('- Timeframe:', percentileData.timeframe);
  } catch (error) {
    console.error('Error:', error instanceof Error ? error.message : error);
  }
}

/**
 * Example 4: Monte Carlo simulation
 */
async function example4_monteCarlo() {
  console.log('\n=== Example 4: Monte Carlo Simulation ===\n');

  const adapter = new BackendDataAdapter();

  try {
    const result = await adapter.runMonteCarloSimulation({
      ticker: 'AAPL',
      num_simulations: 1000,
      max_periods: 21,
      target_percentiles: [25, 50, 75, 90],
    });

    console.log('Ticker:', result.ticker);
    console.log('Current percentile:', result.current_percentile.toFixed(2));
    console.log('Current price:', result.current_price);

    console.log('\nTarget Percentile Probabilities:');
    Object.entries(result.simulation_results.target_probabilities).forEach(
      ([target, data]) => {
        console.log(
          `- Reach ${target}th percentile: ${(data.probability * 100).toFixed(1)}% (avg ${data.avg_periods.toFixed(1)} periods)`
        );
      }
    );

    console.log('\nStatistics (21-day forecast):');
    const stats = result.simulation_results.statistics;
    const lastIdx = stats.mean_path.length - 1;
    console.log('- Mean path:', stats.mean_path[lastIdx].toFixed(2));
    console.log('- Median path:', stats.median_path[lastIdx].toFixed(2));
    console.log('- 5th percentile:', stats.percentile_5[lastIdx].toFixed(2));
    console.log('- 95th percentile:', stats.percentile_95[lastIdx].toFixed(2));
  } catch (error) {
    console.error('Error:', error instanceof Error ? error.message : error);
  }
}

/**
 * Example 5: Live trading signal
 */
async function example5_liveSignal() {
  console.log('\n=== Example 5: Live Trading Signal ===\n');

  const adapter = new BackendDataAdapter();

  try {
    const signal = await adapter.getLiveSignal('AAPL');

    console.log('Ticker:', signal.ticker);

    console.log('\nCurrent State:');
    console.log('- Price:', signal.current_state.price);
    console.log('- Percentile:', signal.current_state.percentile.toFixed(2));
    console.log('- RSI-MA:', signal.current_state.rsi_ma.toFixed(2));

    console.log('\nSignal:');
    console.log('- Strength:', signal.signal.strength);
    console.log('- Confidence:', (signal.signal.confidence * 100).toFixed(1), '%');
    console.log('- Direction:', signal.signal.direction);

    console.log('\nExpected Returns:');
    console.log('- 7-day:', signal.expected_returns['7d'].toFixed(2), '%');
    console.log('- 14-day:', signal.expected_returns['14d'].toFixed(2), '%');
    console.log('- 21-day:', signal.expected_returns['21d'].toFixed(2), '%');

    console.log('\nPosition Size:');
    console.log('- Recommended:', signal.position_size.recommended, '%');
    console.log('- Max risk:', signal.position_size.max_risk, '%');

    console.log('\nReasoning:');
    signal.reasoning.forEach((reason, i) => {
      console.log(`${i + 1}. ${reason}`);
    });

    if (signal.risk_factors.length > 0) {
      console.log('\nRisk Factors:');
      signal.risk_factors.forEach((risk, i) => {
        console.log(`${i + 1}. ${risk}`);
      });
    }
  } catch (error) {
    console.error('Error:', error instanceof Error ? error.message : error);
  }
}

/**
 * Example 6: Multi-timeframe analysis
 */
async function example6_multiTimeframe() {
  console.log('\n=== Example 6: Multi-Timeframe Analysis ===\n');

  const adapter = new BackendDataAdapter();

  try {
    const mtf = await adapter.getMultiTimeframeAnalysis('AAPL');

    console.log('Ticker:', mtf.ticker);

    console.log('\nCurrent Divergence:');
    const div = mtf.analysis.current_divergence;
    console.log('- State:', div.state);
    console.log('- Daily percentile:', div.daily_percentile.toFixed(2));
    console.log('- 4H percentile:', div.fourh_percentile.toFixed(2));
    console.log('- Gap:', div.gap.toFixed(2));
    console.log('- Recommendation:', div.recommendation);

    console.log('\nDivergence Statistics:');
    Object.entries(mtf.analysis.statistics_by_type).forEach(([type, stats]) => {
      console.log(`\n${type}:`);
      console.log(`  - Count: ${stats.count}`);
      console.log(`  - Avg 1-day return: ${stats.avg_return_1d.toFixed(2)}%`);
      console.log(`  - Avg 7-day return: ${stats.avg_return_7d.toFixed(2)}%`);
      console.log(`  - Win rate (1d): ${(stats.win_rate_1d * 100).toFixed(1)}%`);
      if (stats.sharpe_ratio) {
        console.log(`  - Sharpe ratio: ${stats.sharpe_ratio.toFixed(2)}`);
      }
    });

    console.log('\nRecent Divergence Events:');
    mtf.analysis.divergence_events.slice(-5).forEach((event) => {
      console.log(
        `${event.date}: ${event.type} (gap=${event.gap.toFixed(1)}, 1d return=${event.forward_returns['1d'].toFixed(2)}%)`
      );
    });
  } catch (error) {
    console.error('Error:', error instanceof Error ? error.message : error);
  }
}

/**
 * Example 7: Batch backtest
 */
async function example7_batchBacktest() {
  console.log('\n=== Example 7: Batch Backtest ===\n');

  const adapter = new BackendDataAdapter();

  try {
    const result = await adapter.batchBacktest({
      tickers: ['AAPL', 'MSFT', 'GOOGL'],
      lookback_period: 500,
      rsi_length: 14,
      ma_length: 14,
      max_horizon: 21,
    });

    console.log('Status:', result.status);
    console.log('Tickers processed:', result.tickers.join(', '));

    Object.entries(result.results).forEach(([ticker, data]: [string, any]) => {
      console.log(`\n${ticker}:`);
      const thresholds = Object.keys(data.thresholds || {});
      console.log('- Available thresholds:', thresholds.join(', '));

      if (data.thresholds?.['5.0']) {
        const t5 = data.thresholds['5.0'];
        console.log('- 5% threshold events:', t5.events);
        console.log('- Optimal exit day:', t5.optimal_exit_strategy?.recommended_exit_day);
        console.log('- Expected return:', t5.optimal_exit_strategy?.expected_return.toFixed(2), '%');
      }
    });
  } catch (error) {
    console.error('Error:', error instanceof Error ? error.message : error);
  }
}

/**
 * Example 8: Cache management
 */
async function example8_cacheManagement() {
  console.log('\n=== Example 8: Cache Management ===\n');

  const adapter = new BackendDataAdapter({
    cacheEnabled: true,
    cacheTTL: 300000, // 5 minutes
  });

  try {
    console.log('Fetching data (will cache)...');
    const start1 = Date.now();
    await adapter.getBacktestResults('AAPL');
    const time1 = Date.now() - start1;
    console.log(`First fetch: ${time1}ms`);

    console.log('\nFetching again (from cache)...');
    const start2 = Date.now();
    await adapter.getBacktestResults('AAPL');
    const time2 = Date.now() - start2;
    console.log(`Second fetch: ${time2}ms`);

    console.log(`\nCache speedup: ${(time1 / time2).toFixed(1)}x faster`);

    console.log('\nClearing cache...');
    adapter.clearCache();

    console.log('Fetching after clear (will hit API)...');
    const start3 = Date.now();
    await adapter.getBacktestResults('AAPL');
    const time3 = Date.now() - start3;
    console.log(`Third fetch: ${time3}ms`);
  } catch (error) {
    console.error('Error:', error instanceof Error ? error.message : error);
  }
}

/**
 * Run all examples
 */
async function runAllExamples() {
  console.log('╔════════════════════════════════════════════════════════════════╗');
  console.log('║  Backend Data Adapter - Example Usage                         ║');
  console.log('╚════════════════════════════════════════════════════════════════╝');

  await example1_backtestData();
  await example2_rsiChart();
  await example3_percentileForward();
  await example4_monteCarlo();
  await example5_liveSignal();
  await example6_multiTimeframe();
  await example7_batchBacktest();
  await example8_cacheManagement();

  console.log('\n✅ All examples completed!\n');
}

// Run examples if executed directly
if (require.main === module) {
  runAllExamples().catch(console.error);
}

export {
  example1_backtestData,
  example2_rsiChart,
  example3_percentileForward,
  example4_monteCarlo,
  example5_liveSignal,
  example6_multiTimeframe,
  example7_batchBacktest,
  example8_cacheManagement,
};
