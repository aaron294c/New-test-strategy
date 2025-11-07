/**
 * Backtest Example - Demonstrating Historical Backtester Usage
 *
 * This example shows how to:
 * 1. Set up a backtest with framework configuration
 * 2. Load historical market data for multiple instruments
 * 3. Run the backtest simulation
 * 4. Analyze performance results
 * 5. Generate detailed reports
 */

import { HistoricalBacktester, BacktestConfig } from '../Backtester';
import { BacktestDataLoader } from '../BacktestDataLoader';
import { PerformanceReporter, ReportFormat } from '../PerformanceReporter';
import { FrameworkConfig, Timeframe, RegimeType } from '../../core/types';
import { OHLCV } from '../../core/types';

/**
 * Example 1: Basic Backtest with Synthetic Data
 */
export async function runBasicBacktest(): Promise<void> {
  console.log('=== Running Basic Backtest Example ===\n');

  // 1. Configure the trading framework
  const frameworkConfig: Partial<FrameworkConfig> = {
    timeframes: [
      { timeframe: Timeframe.H4, weight: 0.5 },
      { timeframe: Timeframe.H1, weight: 0.3 },
      { timeframe: Timeframe.D1, weight: 0.2 },
    ],
    primaryTimeframe: Timeframe.H4,

    riskManagement: {
      maxRiskPerTrade: 0.01, // 1% risk per trade
      maxTotalRisk: 0.05, // 5% total portfolio risk
      maxPositions: 5,
      minWinRate: 0.35,
      minExpectancy: 0.5,
    },

    allocation: {
      totalCapital: 100000,
      maxRiskPerTrade: 0.01,
      maxTotalRisk: 0.05,
      maxPositions: 5,
      minScore: 0.6,
    },
  };

  // 2. Configure backtest parameters
  const backtestConfig: Partial<BacktestConfig> = {
    initialCapital: 100000,
    startDate: new Date('2023-01-01'),
    endDate: new Date('2023-12-31'),
    warmupBars: 200,

    slippage: {
      basisPoints: 5,
      useVolatilityAdjusted: true,
      maxBasisPoints: 20,
    },

    costs: {
      commission: 1.0,
      commissionType: 'fixed',
      additionalFees: 0,
    },

    features: {
      intrabarExecution: true,
      partialFills: false,
      marketImpact: false,
    },
  };

  // 3. Create backtester instance
  const backtester = new HistoricalBacktester(frameworkConfig, backtestConfig);

  // 4. Generate synthetic data for testing
  const instruments = ['AAPL', 'NVDA', 'GOOGL'];

  instruments.forEach(instrument => {
    const data = BacktestDataLoader.generateSyntheticData({
      bars: 1000,
      initialPrice: 150,
      volatility: 0.02,
      trend: 0.0005,
      timeframe: Timeframe.H4,
      startDate: new Date('2022-01-01'),
    });

    backtester.loadMarketData(instrument, data);
  });

  // 5. Run backtest
  console.log('Running backtest...\n');
  const results = await backtester.runBacktest();

  // 6. Generate and display reports
  console.log(PerformanceReporter.generateTextReport(results));

  // 7. Export results
  console.log('\nExporting results...');
  const jsonReport = PerformanceReporter.generateJSONReport(results);
  console.log('JSON report generated (first 500 chars):');
  console.log(jsonReport.substring(0, 500) + '...\n');

  // 8. Display key metrics
  displayKeyMetrics(results.metrics);

  // 9. Display regime performance
  displayRegimePerformance(results);

  return;
}

/**
 * Example 2: Advanced Backtest with Real Data Format
 */
export async function runAdvancedBacktest(): Promise<void> {
  console.log('\n=== Running Advanced Backtest Example ===\n');

  // Framework configuration with more aggressive parameters
  const frameworkConfig: Partial<FrameworkConfig> = {
    timeframes: [
      { timeframe: Timeframe.D1, weight: 0.4 },
      { timeframe: Timeframe.H4, weight: 0.4 },
      { timeframe: Timeframe.H1, weight: 0.2 },
    ],
    primaryTimeframe: Timeframe.D1,

    riskManagement: {
      maxRiskPerTrade: 0.02, // 2% risk per trade
      maxTotalRisk: 0.08, // 8% total portfolio risk
      maxPositions: 8,
      minWinRate: 0.3,
      minExpectancy: 0.3,
    },

    allocation: {
      totalCapital: 250000,
      maxRiskPerTrade: 0.02,
      maxTotalRisk: 0.08,
      maxPositions: 8,
      minScore: 0.55,
    },

    percentileSettings: {
      entryPercentile: 85, // More aggressive entries
      stopPercentile: 90,
      lookbackBars: 100,
      adaptive: true,
    },
  };

  // Backtest configuration with realistic costs
  const backtestConfig: Partial<BacktestConfig> = {
    initialCapital: 250000,
    startDate: new Date('2020-01-01'),
    endDate: new Date('2023-12-31'),
    warmupBars: 250,

    slippage: {
      basisPoints: 10, // Higher slippage for larger positions
      useVolatilityAdjusted: true,
      maxBasisPoints: 30,
    },

    costs: {
      commission: 0.005, // 0.5% commission
      commissionType: 'percentage',
      additionalFees: 1.0,
    },

    features: {
      intrabarExecution: true,
      partialFills: true,
      marketImpact: true,
    },
  };

  const backtester = new HistoricalBacktester(frameworkConfig, backtestConfig);

  // Load data for multiple instruments
  const instruments = ['AAPL', 'NVDA', 'GOOGL', 'MSFT', 'TSLA'];

  instruments.forEach(instrument => {
    // In production, you would load actual historical data here
    // For this example, we'll generate synthetic data with different characteristics
    const data = BacktestDataLoader.generateSyntheticData({
      bars: 2000,
      initialPrice: Math.random() * 200 + 50,
      volatility: Math.random() * 0.03 + 0.01,
      trend: (Math.random() - 0.5) * 0.001,
      timeframe: Timeframe.D1,
      startDate: new Date('2019-01-01'),
    });

    backtester.loadMarketData(instrument, data);
  });

  // Run backtest
  console.log('Running advanced backtest with 5 instruments...\n');
  const results = await backtester.runBacktest();

  // Generate comprehensive reports
  console.log(PerformanceReporter.generateTextReport(results));

  // Generate Markdown report
  const mdReport = PerformanceReporter.generateMarkdownReport(results);
  console.log('\nMarkdown Report Generated (first 1000 chars):');
  console.log(mdReport.substring(0, 1000) + '...\n');

  // Display advanced analytics
  displayAdvancedAnalytics(results);

  return;
}

/**
 * Example 3: Regime-Specific Backtest Analysis
 */
export async function runRegimeBacktest(): Promise<void> {
  console.log('\n=== Running Regime-Specific Backtest ===\n');

  const frameworkConfig: Partial<FrameworkConfig> = {
    timeframes: [
      { timeframe: Timeframe.H4, weight: 0.5 },
      { timeframe: Timeframe.H1, weight: 0.3 },
      { timeframe: Timeframe.D1, weight: 0.2 },
    ],
    primaryTimeframe: Timeframe.H4,

    regimeDetection: {
      lookbackPeriod: 150,
      coherenceThreshold: 0.7, // Higher coherence required
      updateFrequency: 30,
    },

    allocation: {
      totalCapital: 100000,
      maxRiskPerTrade: 0.015,
      maxTotalRisk: 0.06,
      maxPositions: 6,
      minScore: 0.65,
    },
  };

  const backtestConfig: Partial<BacktestConfig> = {
    initialCapital: 100000,
    startDate: new Date('2022-01-01'),
    endDate: new Date('2023-12-31'),
    warmupBars: 200,

    slippage: {
      basisPoints: 5,
      useVolatilityAdjusted: true,
      maxBasisPoints: 15,
    },

    costs: {
      commission: 1.0,
      commissionType: 'fixed',
      additionalFees: 0,
    },

    features: {
      intrabarExecution: true,
      partialFills: false,
      marketImpact: false,
    },
  };

  const backtester = new HistoricalBacktester(frameworkConfig, backtestConfig);

  // Load data
  const instruments = ['AAPL', 'NVDA', 'GOOGL'];

  instruments.forEach(instrument => {
    const data = BacktestDataLoader.generateSyntheticData({
      bars: 1200,
      initialPrice: 150,
      volatility: 0.025,
      trend: 0.0003,
      timeframe: Timeframe.H4,
      startDate: new Date('2021-06-01'),
    });

    backtester.loadMarketData(instrument, data);
  });

  // Run backtest
  console.log('Running regime-focused backtest...\n');
  const results = await backtester.runBacktest();

  // Focus on regime performance
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('                REGIME PERFORMANCE ANALYSIS');
  console.log('═══════════════════════════════════════════════════════════════\n');

  results.regimePerformance.forEach((perf, regime) => {
    console.log(`${regime.toUpperCase()} REGIME:`);
    console.log(`  Total Trades:        ${perf.trades}`);
    console.log(`  Win Rate:            ${(perf.winRate * 100).toFixed(2)}%`);
    console.log(`  Total PnL:           $${perf.totalPnL.toFixed(2)}`);
    console.log(`  Avg Win:             $${perf.metrics.avgWin.toFixed(2)}`);
    console.log(`  Avg Loss:            $${perf.metrics.avgLoss.toFixed(2)}`);
    console.log(`  Expectancy:          $${perf.metrics.expectancy.toFixed(2)}`);
    console.log(`  Sharpe Ratio:        ${perf.metrics.sharpeRatio.toFixed(2)}`);
    console.log(`  Max Drawdown:        ${perf.metrics.maxDrawdownPercent.toFixed(2)}%`);
    console.log();
  });

  // Export CSV trade log
  const csvLog = PerformanceReporter.generateCSVTradeLog(results);
  console.log('CSV Trade Log Generated (first 500 chars):');
  console.log(csvLog.substring(0, 500) + '...\n');

  return;
}

/**
 * Example 4: Walk-Forward Analysis
 */
export async function runWalkForwardAnalysis(): Promise<void> {
  console.log('\n=== Running Walk-Forward Analysis ===\n');

  const frameworkConfig: Partial<FrameworkConfig> = {
    timeframes: [
      { timeframe: Timeframe.H4, weight: 0.5 },
      { timeframe: Timeframe.H1, weight: 0.3 },
      { timeframe: Timeframe.D1, weight: 0.2 },
    ],
    primaryTimeframe: Timeframe.H4,

    allocation: {
      totalCapital: 100000,
      maxRiskPerTrade: 0.01,
      maxTotalRisk: 0.05,
      maxPositions: 5,
      minScore: 0.6,
    },
  };

  // Generate data once
  const instruments = ['AAPL', 'NVDA', 'GOOGL'];
  const allData = new Map<string, OHLCV[]>();

  instruments.forEach(instrument => {
    const data = BacktestDataLoader.generateSyntheticData({
      bars: 2000,
      initialPrice: 150,
      volatility: 0.02,
      trend: 0.0005,
      timeframe: Timeframe.H4,
      startDate: new Date('2020-01-01'),
    });

    allData.set(instrument, data);
  });

  // Split into train/test periods
  const periods = [
    { name: 'Q1 2023', start: new Date('2023-01-01'), end: new Date('2023-03-31') },
    { name: 'Q2 2023', start: new Date('2023-04-01'), end: new Date('2023-06-30') },
    { name: 'Q3 2023', start: new Date('2023-07-01'), end: new Date('2023-09-30') },
    { name: 'Q4 2023', start: new Date('2023-10-01'), end: new Date('2023-12-31') },
  ];

  console.log('Running walk-forward analysis across 4 quarters...\n');

  for (const period of periods) {
    console.log(`\n${'='.repeat(65)}`);
    console.log(`Testing Period: ${period.name}`);
    console.log('='.repeat(65));

    const backtestConfig: Partial<BacktestConfig> = {
      initialCapital: 100000,
      startDate: period.start,
      endDate: period.end,
      warmupBars: 200,

      slippage: {
        basisPoints: 5,
        useVolatilityAdjusted: true,
        maxBasisPoints: 20,
      },

      costs: {
        commission: 1.0,
        commissionType: 'fixed',
        additionalFees: 0,
      },

      features: {
        intrabarExecution: true,
        partialFills: false,
        marketImpact: false,
      },
    };

    const backtester = new HistoricalBacktester(frameworkConfig, backtestConfig);

    // Load data for this period
    allData.forEach((data, instrument) => {
      backtester.loadMarketData(instrument, data);
    });

    const results = await backtester.runBacktest();

    // Display summary for this period
    console.log(`Total Trades:   ${results.metrics.totalTrades}`);
    console.log(`Win Rate:       ${(results.metrics.winRate * 100).toFixed(2)}%`);
    console.log(`Total Return:   ${results.metrics.totalReturnPercent.toFixed(2)}%`);
    console.log(`Sharpe Ratio:   ${results.metrics.sharpeRatio.toFixed(2)}`);
    console.log(`Max Drawdown:   ${results.metrics.maxDrawdownPercent.toFixed(2)}%`);
    console.log(`Expectancy:     $${results.metrics.expectancy.toFixed(2)}`);
  }

  console.log('\n' + '='.repeat(65));
  console.log('Walk-Forward Analysis Complete');
  console.log('='.repeat(65) + '\n');

  return;
}

/**
 * Helper: Display key metrics
 */
function displayKeyMetrics(metrics: any): void {
  console.log('\n┌─────────────────────────────────────────┐');
  console.log('│          KEY PERFORMANCE METRICS        │');
  console.log('├─────────────────────────────────────────┤');
  console.log(`│ Total Return:    ${metrics.totalReturnPercent.toFixed(2)}%`.padEnd(42) + '│');
  console.log(`│ CAGR:            ${metrics.cagr.toFixed(2)}%`.padEnd(42) + '│');
  console.log(`│ Sharpe Ratio:    ${metrics.sharpeRatio.toFixed(2)}`.padEnd(42) + '│');
  console.log(`│ Win Rate:        ${(metrics.winRate * 100).toFixed(2)}%`.padEnd(42) + '│');
  console.log(`│ Profit Factor:   ${metrics.profitFactor.toFixed(2)}`.padEnd(42) + '│');
  console.log(`│ Max Drawdown:    ${metrics.maxDrawdownPercent.toFixed(2)}%`.padEnd(42) + '│');
  console.log('└─────────────────────────────────────────┘\n');
}

/**
 * Helper: Display regime performance
 */
function displayRegimePerformance(results: any): void {
  console.log('┌───────────────────────────────────────────────────────────┐');
  console.log('│             PERFORMANCE BY REGIME                         │');
  console.log('├───────────────────────────────────────────────────────────┤');

  results.regimePerformance.forEach((perf: any, regime: RegimeType) => {
    console.log(`│ ${regime.toUpperCase().padEnd(20)} │ Win Rate: ${(perf.winRate * 100).toFixed(1)}%`.padEnd(60) + '│');
    console.log(`│ ${' '.repeat(20)} │ PnL: $${perf.totalPnL.toFixed(2)}`.padEnd(60) + '│');
  });

  console.log('└───────────────────────────────────────────────────────────┘\n');
}

/**
 * Helper: Display advanced analytics
 */
function displayAdvancedAnalytics(results: any): void {
  console.log('\n┌─────────────────────────────────────────────────────────────┐');
  console.log('│              ADVANCED ANALYTICS                             │');
  console.log('├─────────────────────────────────────────────────────────────┤');
  console.log(`│ Standard Deviation:     ${results.metrics.standardDeviation.toFixed(4)}`.padEnd(62) + '│');
  console.log(`│ Downside Deviation:     ${results.metrics.downSideDeviation.toFixed(4)}`.padEnd(62) + '│');
  console.log(`│ Skewness:               ${results.metrics.skewness.toFixed(4)}`.padEnd(62) + '│');
  console.log(`│ Kurtosis:               ${results.metrics.kurtosis.toFixed(4)}`.padEnd(62) + '│');
  console.log(`│ Ulcer Index:            ${results.metrics.ulcerIndex.toFixed(4)}`.padEnd(62) + '│');
  console.log(`│ Max Consecutive Wins:   ${results.metrics.maxConsecutiveWins}`.padEnd(62) + '│');
  console.log(`│ Max Consecutive Losses: ${results.metrics.maxConsecutiveLosses}`.padEnd(62) + '│');
  console.log(`│ Total Costs:            $${results.metrics.totalCosts.toFixed(2)}`.padEnd(62) + '│');
  console.log(`│ Costs as % of PnL:      ${results.metrics.costsAsPercentOfPnL.toFixed(2)}%`.padEnd(62) + '│');
  console.log('└─────────────────────────────────────────────────────────────┘\n');
}

/**
 * Main entry point - Run all examples
 */
export async function runAllExamples(): Promise<void> {
  console.log('\n');
  console.log('╔═══════════════════════════════════════════════════════════════╗');
  console.log('║      TRADING FRAMEWORK BACKTEST EXAMPLES                      ║');
  console.log('╚═══════════════════════════════════════════════════════════════╝');
  console.log('\n');

  try {
    // Run all examples
    await runBasicBacktest();
    await runAdvancedBacktest();
    await runRegimeBacktest();
    await runWalkForwardAnalysis();

    console.log('\n');
    console.log('╔═══════════════════════════════════════════════════════════════╗');
    console.log('║      ALL EXAMPLES COMPLETED SUCCESSFULLY                      ║');
    console.log('╚═══════════════════════════════════════════════════════════════╝');
    console.log('\n');
  } catch (error) {
    console.error('Error running examples:', error);
    throw error;
  }
}

// If running this file directly
if (require.main === module) {
  runAllExamples().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}
