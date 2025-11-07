# Trading Framework Backtesting Module

Comprehensive historical backtesting system for the principle-led multi-timeframe trading framework.

## Features

### Core Capabilities

- **Historical Data Replay**: Simulates framework execution on historical market data
- **Realistic Order Execution**: Accounts for slippage, commissions, and transaction costs
- **Intrabar Execution**: Models stop loss hits within bars for accuracy
- **Multi-Instrument Support**: Backtest portfolios across multiple instruments
- **Regime Analysis**: Track performance by market regime (momentum, mean-reversion, etc.)

### Performance Analytics

- **Comprehensive Metrics**: 40+ performance metrics including:
  - Returns: Total return, CAGR, monthly/yearly breakdowns
  - Risk-Adjusted: Sharpe, Sortino, Calmar ratios
  - Trade Stats: Win rate, expectancy, profit factor
  - Risk: Max drawdown, MAE/MFE, Ulcer index
  - Statistical: Skewness, kurtosis, confidence intervals

- **Trade-by-Trade Analysis**: Detailed logs with entry/exit prices, PnL, holding periods
- **Equity Curve Tracking**: Visualize portfolio value and drawdowns over time
- **Cost Analysis**: Track slippage, commissions, and total transaction costs

### Reporting

- **Multiple Formats**: Text, JSON, Markdown, CSV, HTML
- **Chart Data**: Pre-formatted data for equity curves, monthly returns, regime performance
- **Regime Breakdown**: Performance statistics segmented by market regime
- **Top Trades**: Best and worst performers analysis

## Quick Start

### Basic Usage

```typescript
import { HistoricalBacktester, BacktestDataLoader } from './framework/backtesting';
import { Timeframe } from './framework/core/types';

// 1. Configure framework
const frameworkConfig = {
  timeframes: [
    { timeframe: Timeframe.H4, weight: 0.5 },
    { timeframe: Timeframe.H1, weight: 0.3 },
    { timeframe: Timeframe.D1, weight: 0.2 },
  ],
  allocation: {
    totalCapital: 100000,
    maxRiskPerTrade: 0.01,
    maxTotalRisk: 0.05,
    maxPositions: 5,
  },
};

// 2. Configure backtest
const backtestConfig = {
  initialCapital: 100000,
  startDate: new Date('2023-01-01'),
  endDate: new Date('2023-12-31'),
  slippage: {
    basisPoints: 5,
    useVolatilityAdjusted: true,
  },
  costs: {
    commission: 1.0,
    commissionType: 'fixed',
  },
};

// 3. Create backtester
const backtester = new HistoricalBacktester(frameworkConfig, backtestConfig);

// 4. Load market data
const data = BacktestDataLoader.generateSyntheticData({
  bars: 1000,
  initialPrice: 150,
  volatility: 0.02,
  timeframe: Timeframe.H4,
  startDate: new Date('2022-01-01'),
});

backtester.loadMarketData('AAPL', data);

// 5. Run backtest
const results = await backtester.runBacktest();

// 6. Generate report
console.log(PerformanceReporter.generateTextReport(results));
```

### Loading Real Data

```typescript
// From backend format (compatible with existing Python backtester)
const backendData = [
  { timestamp: '2023-01-01', open: 150, high: 152, low: 149, close: 151, volume: 1000000 },
  // ... more bars
];

const ohlcv = BacktestDataLoader.loadFromBackendFormat(backendData, Timeframe.H4);
backtester.loadMarketData('AAPL', ohlcv);
```

### Regime-Specific Analysis

```typescript
// Run backtest
const results = await backtester.runBacktest();

// Analyze by regime
results.regimePerformance.forEach((perf, regime) => {
  console.log(`${regime}:`);
  console.log(`  Win Rate: ${(perf.winRate * 100).toFixed(2)}%`);
  console.log(`  Expectancy: $${perf.metrics.expectancy.toFixed(2)}`);
  console.log(`  Sharpe: ${perf.metrics.sharpeRatio.toFixed(2)}`);
});
```

## Configuration

### Backtest Configuration

```typescript
interface BacktestConfig {
  initialCapital: number;
  startDate: Date;
  endDate: Date;
  warmupBars: number; // Bars before start for indicator calculation

  slippage: {
    basisPoints: number; // Fixed slippage (5 = 0.05%)
    useVolatilityAdjusted: boolean; // Scale with volatility
    maxBasisPoints: number; // Cap on slippage
  };

  costs: {
    commission: number; // Per trade cost
    commissionType: 'fixed' | 'percentage';
    additionalFees: number; // Other fees per trade
  };

  features: {
    intrabarExecution: boolean; // Check stops within bars
    partialFills: boolean; // Simulate partial order fills
    marketImpact: boolean; // Model market impact on price
  };
}
```

### Slippage Models

**Fixed Slippage**:
```typescript
slippage: {
  basisPoints: 5, // Always 0.05% slippage
  useVolatilityAdjusted: false,
}
```

**Volatility-Adjusted**:
```typescript
slippage: {
  basisPoints: 5, // Base slippage
  useVolatilityAdjusted: true, // Scale with bar range
  maxBasisPoints: 20, // Cap at 0.20%
}
```

### Cost Models

**Fixed Commission**:
```typescript
costs: {
  commission: 1.0, // $1 per trade
  commissionType: 'fixed',
}
```

**Percentage Commission**:
```typescript
costs: {
  commission: 0.005, // 0.5% of position size
  commissionType: 'percentage',
}
```

## Performance Metrics

### Returns Metrics

- **Total Return**: Absolute and percentage return
- **CAGR**: Compound annual growth rate
- **Monthly/Yearly Returns**: Breakdown by time period

### Risk-Adjusted Metrics

- **Sharpe Ratio**: Return per unit of volatility
- **Sortino Ratio**: Return per unit of downside volatility
- **Calmar Ratio**: CAGR / Max Drawdown

### Trade Statistics

- **Win Rate**: Percentage of winning trades
- **Expectancy**: Average profit per trade
- **Profit Factor**: Gross profit / Gross loss
- **Win/Loss Ratio**: Average win / Average loss

### Risk Metrics

- **Max Drawdown**: Largest peak-to-trough decline
- **Average Drawdown**: Mean drawdown
- **Recovery Factor**: Total return / Max drawdown
- **Ulcer Index**: Drawdown volatility
- **MAE/MFE**: Max adverse/favorable excursion

### Statistical Metrics

- **Standard Deviation**: Return volatility
- **Downside Deviation**: Downside volatility only
- **Skewness**: Return distribution asymmetry
- **Kurtosis**: Return distribution tail thickness

## Data Loading

### From Backend Format

```typescript
const data = BacktestDataLoader.loadFromBackendFormat(backendData, Timeframe.H4);
```

### Generate Synthetic Data

```typescript
const data = BacktestDataLoader.generateSyntheticData({
  bars: 1000,
  initialPrice: 150,
  volatility: 0.02, // 2% daily volatility
  trend: 0.0005, // 0.05% daily trend
  timeframe: Timeframe.H4,
  startDate: new Date('2022-01-01'),
});
```

### Resample Data

```typescript
// Convert 1-hour bars to 4-hour bars
const h4Bars = BacktestDataLoader.resampleData(h1Bars, Timeframe.H4);
```

### Validate Data

```typescript
const validation = BacktestDataLoader.validateData(bars);
if (!validation.valid) {
  console.error('Data errors:', validation.errors);
  console.warn('Data warnings:', validation.warnings);
}
```

## Report Formats

### Text Report

```typescript
const report = PerformanceReporter.generateTextReport(results);
console.log(report);
```

### JSON Export

```typescript
const json = PerformanceReporter.generateJSONReport(results);
fs.writeFileSync('backtest-results.json', json);
```

### Markdown Report

```typescript
const markdown = PerformanceReporter.generateMarkdownReport(results);
fs.writeFileSync('BACKTEST_REPORT.md', markdown);
```

### CSV Trade Log

```typescript
const csv = PerformanceReporter.generateCSVTradeLog(results);
fs.writeFileSync('trades.csv', csv);
```

## Chart Data

### Equity Curve

```typescript
const equityData = PerformanceReporter.getEquityCurveData(results);
// Use with charting library (Chart.js, D3, etc.)
```

### Monthly Returns

```typescript
const monthlyData = PerformanceReporter.getMonthlyReturnsData(results);
```

### Regime Performance

```typescript
const regimeData = PerformanceReporter.getRegimePerformanceData(results);
```

### Trade Distribution

```typescript
const distributionData = PerformanceReporter.getTradeDistributionData(results);
```

## Walk-Forward Analysis

```typescript
const periods = [
  { start: new Date('2023-Q1'), end: new Date('2023-Q1-end') },
  { start: new Date('2023-Q2'), end: new Date('2023-Q2-end') },
  // ...
];

for (const period of periods) {
  const config = { ...backtestConfig, startDate: period.start, endDate: period.end };
  const backtester = new HistoricalBacktester(frameworkConfig, config);

  // Load data...
  const results = await backtester.runBacktest();

  console.log(`${period.name}: ${results.metrics.totalReturnPercent}%`);
}
```

## Integration with Backend

The backtester is fully compatible with the existing Python backend data format:

```typescript
// Python backend returns data in this format
const backendResponse = await fetch('/api/backtest/data/AAPL');
const backendData = await backendResponse.json();

// Load directly into framework
const ohlcv = BacktestDataLoader.loadFromBackendFormat(
  backendData.bars,
  Timeframe.H4
);

backtester.loadMarketData('AAPL', ohlcv);
```

## Best Practices

### 1. Use Sufficient Warmup Period

```typescript
backtestConfig: {
  warmupBars: 200, // Allow indicators to stabilize
  // ...
}
```

### 2. Model Realistic Costs

```typescript
costs: {
  commission: 1.0, // Match your broker
  commissionType: 'fixed',
  additionalFees: 0, // SEC fees, etc.
}
```

### 3. Enable Intrabar Execution

```typescript
features: {
  intrabarExecution: true, // More accurate stop modeling
  // ...
}
```

### 4. Validate Data Quality

```typescript
const validation = BacktestDataLoader.validateData(bars);
if (!validation.valid) {
  throw new Error(`Invalid data: ${validation.errors.join(', ')}`);
}
```

### 5. Analyze by Regime

```typescript
results.regimePerformance.forEach((perf, regime) => {
  if (perf.metrics.expectancy < 0) {
    console.warn(`Negative expectancy in ${regime} regime`);
  }
});
```

## Examples

See `/examples/backtestExample.ts` for comprehensive usage examples:

- Basic backtest with synthetic data
- Advanced backtest with multiple instruments
- Regime-specific analysis
- Walk-forward testing
- Report generation

## API Reference

### HistoricalBacktester

```typescript
class HistoricalBacktester {
  constructor(frameworkConfig, backtestConfig);
  loadMarketData(instrument: string, bars: OHLCV[]): void;
  runBacktest(): Promise<BacktestResults>;
  exportResults(results: BacktestResults): string;
  generateReport(results: BacktestResults): string;
}
```

### BacktestDataLoader

```typescript
class BacktestDataLoader {
  static loadFromBackendFormat(data: any[], timeframe: Timeframe): OHLCV[];
  static generateSyntheticData(config): OHLCV[];
  static validateData(bars: OHLCV[]): ValidationResult;
  static resampleData(bars: OHLCV[], timeframe: Timeframe): OHLCV[];
  static fillGaps(bars: OHLCV[]): OHLCV[];
  static splitData(bars: OHLCV[], trainRatio: number): { train, test };
}
```

### PerformanceReporter

```typescript
class PerformanceReporter {
  static generateTextReport(results: BacktestResults): string;
  static generateJSONReport(results: BacktestResults): string;
  static generateMarkdownReport(results: BacktestResults): string;
  static generateCSVTradeLog(results: BacktestResults): string;
  static getEquityCurveData(results: BacktestResults): ChartData;
  static getMonthlyReturnsData(results: BacktestResults): ChartData;
  static getRegimePerformanceData(results: BacktestResults): ChartData;
}
```

## Performance Considerations

- Backtesting 1000 bars across 5 instruments typically takes < 1 second
- Memory usage scales with number of instruments × bars
- Enable `partialFills` and `marketImpact` only for large position sizes
- Use `warmupBars` to avoid indicator initialization artifacts

## Troubleshooting

### Issue: No Trades Generated

**Solution**: Check that:
- Market data is loaded correctly
- Score threshold (`minScore`) isn't too high
- Risk parameters allow position sizing
- Warmup period is sufficient

### Issue: Unrealistic Results

**Solution**: Verify:
- Slippage is enabled and reasonable
- Commission costs are included
- Intrabar execution is enabled for stop accuracy
- Data quality is good (no gaps or errors)

### Issue: High Costs

**Solution**: Review:
- Commission settings match broker
- Trade frequency (high frequency = high costs)
- Slippage model (volatility-adjusted may be too aggressive)

## Future Enhancements

- Monte Carlo simulation
- Parameter optimization
- Multi-threaded backtesting
- Live trading integration
- Advanced order types (limit, stop-limit)
- Position sizing algorithms
- Risk parity allocation

## License

Part of the Trading Framework project.
