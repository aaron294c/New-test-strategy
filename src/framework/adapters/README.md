# Data Adapters

Production-ready data adapters for connecting the TypeScript trading framework to external data sources.

## Overview

Two primary adapters are provided:

1. **BackendDataAdapter** - Connects to Python backend API at `http://localhost:8000`
2. **YFinanceAdapter** - Direct integration with Yahoo Finance API for real-time data

## Installation

```bash
npm install
```

## BackendDataAdapter

### Features

- ✅ Full Python API integration (all 20+ endpoints)
- ✅ Automatic retry logic with exponential backoff
- ✅ In-memory response caching with TTL
- ✅ Type-safe TypeScript interfaces
- ✅ Error handling and timeout management
- ✅ Response transformation to framework types

### Usage

```typescript
import { BackendDataAdapter } from './adapters/BackendDataAdapter';

const adapter = new BackendDataAdapter({
  baseUrl: 'http://localhost:8000',
  timeout: 30000,
  retries: 3,
  cacheEnabled: true,
  cacheTTL: 300000, // 5 minutes
});

// Backtest results
const backtest = await adapter.getBacktestResults('AAPL');
console.log('Win rates:', backtest.data.thresholds['5.0'].win_rates);

// RSI chart for visualization
const rsiChart = await adapter.getRSIChart('AAPL', 252);
const marketData = adapter.transformToMarketData('AAPL', rsiChart);

// Percentile forward mapping
const forward = await adapter.getPercentileForward('AAPL');
const percentileData = adapter.transformToPercentileData(forward);

// Monte Carlo simulation
const mc = await adapter.runMonteCarloSimulation({
  ticker: 'AAPL',
  num_simulations: 1000,
  max_periods: 21,
});

// Live trading signal
const signal = await adapter.getLiveSignal('AAPL');
console.log('Signal:', signal.signal.strength);

// Multi-timeframe analysis
const mtf = await adapter.getMultiTimeframeAnalysis('AAPL');
```

### API Methods

#### Core Methods

- `getBacktestResults(ticker, forceRefresh?)` - Backtest results for ticker
- `getRSIChart(ticker, days?)` - RSI/percentile time series
- `getPercentileForward(ticker, forceRefresh?)` - Forward return predictions
- `getPercentileForward4H(ticker, forceRefresh?)` - 4-hour timeframe predictions
- `runMonteCarloSimulation(request)` - Monte Carlo simulation
- `getLiveSignal(ticker)` - Real-time entry signal
- `getMultiTimeframeAnalysis(ticker)` - Divergence analysis
- `batchBacktest(request)` - Batch multiple tickers

#### Transformation Methods

- `transformToMarketData(ticker, chartData)` - Convert to MarketData format
- `transformToPercentileData(response, timeframe?)` - Convert to PercentileData
- `transformRiskMetrics(backtestData, threshold)` - Convert to framework RiskMetrics

#### Utility Methods

- `clearCache()` - Clear all cached responses
- `healthCheck()` - Check backend availability

## YFinanceAdapter

### Features

- ✅ Real-time and historical OHLCV data
- ✅ Multi-timeframe support (1m to 1w)
- ✅ Built-in technical indicators (RSI, SMA, RSI-MA)
- ✅ Automatic retry logic
- ✅ Ticker validation

### Usage

```typescript
import { YFinanceAdapter } from './adapters/YFinanceAdapter';
import { Timeframe } from '../core/types';

const adapter = new YFinanceAdapter({
  timeout: 10000,
  retries: 3,
});

// Get daily market data
const dailyData = await adapter.getMarketData('AAPL', Timeframe.D1, '1y');

// Get 4-hour data
const fourHourData = await adapter.getMarketData('AAPL', Timeframe.H4, '1mo');

// Multi-timeframe data
const mtfData = await adapter.getMultiTimeframeData('AAPL', [
  Timeframe.H1,
  Timeframe.H4,
  Timeframe.D1,
]);

// Calculate indicators
const rsiMa = adapter.calculateRSIMA(dailyData.bars, 14, 14);
const rsi = adapter.calculateRSI(dailyData.bars, 14);
const sma = adapter.calculateSMA(dailyData.bars.map(b => b.close), 20);

// Validate ticker
const isValid = await adapter.validateTicker('AAPL');

// Current price only
const price = await adapter.getCurrentPrice('AAPL');
```

### API Methods

- `getMarketData(ticker, timeframe, period)` - Historical OHLCV data
- `getCurrentPrice(ticker)` - Latest price
- `getMultiTimeframeData(ticker, timeframes)` - Multi-TF data
- `calculateRSI(bars, period)` - RSI indicator
- `calculateSMA(values, period)` - Simple moving average
- `calculateRSIMA(bars, rsiPeriod, maPeriod)` - RSI with MA smoothing
- `validateTicker(ticker)` - Check if ticker exists

## Type Definitions

All API response types are fully typed in `types.ts`:

```typescript
// Backtest response
interface BacktestResponse {
  ticker: string;
  data: BacktestData;
  timestamp: string;
}

// RSI chart data
interface RSIChartResponse {
  ticker: string;
  chart_data: RSIChartData;
  timestamp: string;
}

// Percentile forward mapping
interface PercentileForwardResponse {
  ticker: string;
  current_state: { current_percentile: number; current_rsi_ma: number };
  prediction: PercentilePrediction;
  accuracy_metrics: AccuracyMetrics;
}
```

## Error Handling

All adapters include comprehensive error handling:

```typescript
try {
  const data = await adapter.getBacktestResults('AAPL');
} catch (error) {
  if (error.message.includes('timeout')) {
    // Handle timeout
  } else if (error.message.includes('404')) {
    // Handle not found
  } else {
    // Generic error
  }
}
```

## Caching

BackendDataAdapter includes intelligent caching:

- **Backtest results**: 5 minutes TTL
- **Percentile forward**: 1 hour TTL (already cached on backend)
- **RSI charts**: 5 minutes TTL
- **Live signals**: No cache (always fresh)

```typescript
// Force refresh (bypass cache)
const freshData = await adapter.getBacktestResults('AAPL', true);

// Clear all cache
adapter.clearCache();
```

## Retry Logic

Both adapters implement exponential backoff:

- Default: 3 retries
- Delay: 1s, 2s, 3s (multiplied by attempt number)
- Timeout: 30s (backend), 10s (yfinance)

```typescript
const adapter = new BackendDataAdapter({
  retries: 5,
  retryDelay: 2000, // 2s base delay
  timeout: 60000,   // 1 minute timeout
});
```

## Integration with Framework

Complete example integrating both adapters:

```typescript
import { TradingFramework } from '../core/TradingFramework';
import { BackendDataAdapter, YFinanceAdapter } from './adapters';
import { Timeframe } from '../core/types';

// Initialize adapters
const backend = new BackendDataAdapter();
const yfinance = new YFinanceAdapter();

// Initialize framework
const framework = new TradingFramework({
  timeframes: [
    { timeframe: Timeframe.H4, weight: 0.5 },
    { timeframe: Timeframe.D1, weight: 0.5 },
  ],
});

// Get data from both sources
const ticker = 'AAPL';

// Backend: Historical analysis
const backtest = await backend.getBacktestResults(ticker);
const forward = await backend.getPercentileForward(ticker);
const signal = await backend.getLiveSignal(ticker);

// YFinance: Real-time data
const mtfData = await yfinance.getMultiTimeframeData(ticker);

// Add to framework
for (const [timeframe, data] of mtfData) {
  framework.addMarketData(ticker, data);
}

// Transform backend data
const percentileData = backend.transformToPercentileData(forward);
const riskMetrics = backend.transformRiskMetrics(backtest, '5.0');

// Use in trading decisions
if (signal.signal.strength === 'strong_buy' && percentileData.percentile < 10) {
  console.log('Strong buy signal at extreme low percentile');
}
```

## Testing

```bash
# Test backend connectivity
const healthy = await adapter.healthCheck();
console.log('Backend healthy:', healthy);

# Test ticker validity
const valid = await yfinance.validateTicker('AAPL');
console.log('Ticker valid:', valid);

# Test with sample ticker
const test = await adapter.getBacktestResults('AAPL');
console.log('Data points:', Object.keys(test.data.thresholds).length);
```

## Performance

- **BackendDataAdapter**: ~100-500ms per request (with caching)
- **YFinanceAdapter**: ~200-800ms per request
- **Batch operations**: Use `batchBacktest()` for multiple tickers

## Limitations

- **BackendDataAdapter**: Requires Python backend running at localhost:8000
- **YFinanceAdapter**: Rate limited by Yahoo Finance (avoid excessive requests)
- **Cache**: In-memory only (cleared on restart)

## Future Enhancements

- [ ] WebSocket support for real-time updates
- [ ] Redis/persistent cache layer
- [ ] Additional data sources (Alpha Vantage, Polygon, etc.)
- [ ] Offline mode with local database
- [ ] Request queuing and rate limiting

## Support

For issues or questions:
- Backend API: Check `/workspaces/New-test-strategy/backend/api.py`
- Framework: Check `/workspaces/New-test-strategy/src/framework/README.md`
