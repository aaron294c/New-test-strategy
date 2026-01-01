# Data Adapters - Quick Start Guide

## 5-Minute Setup

### 1. Start the Python Backend

```bash
cd /workspaces/New-test-strategy/backend
python api.py
```

You should see:
```
RSI-MA Performance Analytics API
Multi-Timeframe Trading Guide Enabled
===============================================
Cache directory: /workspaces/New-test-strategy/backend/cache
```

Backend will be available at: `http://localhost:8000`

### 2. Test Backend Health

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{"status": "healthy", "timestamp": "2025-11-06T..."}
```

### 3. Run Example Code

```bash
# Backend adapter examples
cd /workspaces/New-test-strategy
npx ts-node tests/framework/adapters/backend-adapter.example.ts

# YFinance adapter examples (no backend needed)
npx ts-node tests/framework/adapters/yfinance-adapter.example.ts
```

## Basic Usage

### BackendDataAdapter (Python API)

```typescript
import { BackendDataAdapter } from './src/framework/adapters';

// Create adapter
const adapter = new BackendDataAdapter();

// Get backtest results
const backtest = await adapter.getBacktestResults('AAPL');
console.log(backtest.data.thresholds['5.0'].win_rates);

// Get RSI chart
const chart = await adapter.getRSIChart('AAPL', 252);
console.log('Current percentile:', chart.chart_data.current.percentile);

// Get percentile forward predictions
const forward = await adapter.getPercentileForward('AAPL');
console.log('1-day forecast:', forward.prediction.ensemble_forecast_1d);

// Get live signal
const signal = await adapter.getLiveSignal('AAPL');
console.log('Signal:', signal.signal.strength);
```

### YFinanceAdapter (Real-time Data)

```typescript
import { YFinanceAdapter, Timeframe } from './src/framework/adapters';

// Create adapter
const adapter = new YFinanceAdapter();

// Get daily data
const data = await adapter.getMarketData('AAPL', Timeframe.D1, '1y');
console.log('Bars:', data.bars.length);

// Get current price
const price = await adapter.getCurrentPrice('AAPL');
console.log('Price:', price);

// Calculate RSI-MA
const rsiMa = adapter.calculateRSIMA(data.bars, 14, 14);
console.log('RSI-MA:', rsiMa[rsiMa.length - 1]);

// Multi-timeframe data
const mtfData = await adapter.getMultiTimeframeData('AAPL', [
  Timeframe.H4,
  Timeframe.D1,
]);
```

## Common Use Cases

### 1. Get Trading Signal

```typescript
const adapter = new BackendDataAdapter();

// Get live signal
const signal = await adapter.getLiveSignal('AAPL');

if (signal.signal.strength === 'strong_buy') {
  console.log('🟢 STRONG BUY');
  console.log('Expected 7d return:', signal.expected_returns['7d'], '%');
  console.log('Position size:', signal.position_size.recommended, '%');
  console.log('Reasoning:', signal.reasoning.join(', '));
}
```

### 2. Analyze Backtest Performance

```typescript
const adapter = new BackendDataAdapter();

const backtest = await adapter.getBacktestResults('AAPL');
const threshold = '5.0';
const data = backtest.data.thresholds[threshold];

console.log(`Threshold: ${threshold}%`);
console.log(`Total events: ${data.events}`);
console.log(`Win rates by day:`, data.win_rates);
console.log(`Optimal exit: Day ${data.optimal_exit_strategy?.recommended_exit_day}`);
console.log(`Expected return: ${data.optimal_exit_strategy?.expected_return}%`);
```

### 3. Get Price Predictions

```typescript
const adapter = new BackendDataAdapter();

const forward = await adapter.getPercentileForward('AAPL');

console.log('Current percentile:', forward.current_state.current_percentile);
console.log('\nForecasts:');
console.log('1-day:', forward.prediction.ensemble_forecast_1d, '%');
console.log('5-day:', forward.prediction.ensemble_forecast_5d, '%');
console.log('10-day:', forward.prediction.ensemble_forecast_10d, '%');
console.log('21-day:', forward.prediction.ensemble_forecast_21d, '%');

// Check accuracy
const acc = forward.accuracy_metrics['1d'];
console.log('\nModel accuracy:');
console.log('Hit rate:', (acc.hit_rate * 100).toFixed(1), '%');
console.log('Sharpe ratio:', acc.sharpe.toFixed(2));
```

### 4. Multi-Timeframe Divergence

```typescript
const adapter = new BackendDataAdapter();

const mtf = await adapter.getMultiTimeframeAnalysis('AAPL');
const div = mtf.analysis.current_divergence;

console.log('Divergence state:', div.state);
console.log('Daily percentile:', div.daily_percentile);
console.log('4H percentile:', div.fourh_percentile);
console.log('Gap:', div.gap);
console.log('\nRecommendation:', div.recommendation);
```

### 5. Compare Multiple Tickers

```typescript
const backend = new BackendDataAdapter();
const tickers = ['AAPL', 'MSFT', 'GOOGL'];

for (const ticker of tickers) {
  const signal = await backend.getLiveSignal(ticker);
  const forward = await backend.getPercentileForward(ticker);

  console.log(`\n${ticker}:`);
  console.log('  Signal:', signal.signal.strength);
  console.log('  Percentile:', forward.current_state.current_percentile);
  console.log('  7d forecast:', forward.prediction.ensemble_forecast_5d, '%');
}
```

### 6. Get Real-Time Market Data

```typescript
const adapter = new YFinanceAdapter();

// Current prices
const tickers = ['AAPL', 'MSFT', 'GOOGL'];
for (const ticker of tickers) {
  const price = await adapter.getCurrentPrice(ticker);
  console.log(`${ticker}: $${price.toFixed(2)}`);
}

// Historical data with indicators
const data = await adapter.getMarketData('AAPL', Timeframe.D1, '6mo');
const rsi = adapter.calculateRSI(data.bars, 14);
const rsiMa = adapter.calculateRSIMA(data.bars, 14, 14);

console.log('\nTechnical Indicators:');
console.log('RSI:', rsi[rsi.length - 1].toFixed(2));
console.log('RSI-MA:', rsiMa[rsiMa.length - 1].toFixed(2));
```

## Error Handling

```typescript
const adapter = new BackendDataAdapter({
  timeout: 30000,
  retries: 3,
});

try {
  const data = await adapter.getBacktestResults('AAPL');
  console.log('Success:', data.ticker);
} catch (error) {
  if (error.message.includes('timeout')) {
    console.error('Request timed out');
  } else if (error.message.includes('404')) {
    console.error('Ticker not found');
  } else {
    console.error('Error:', error.message);
  }
}
```

## Caching

```typescript
// Enable caching (default)
const adapter = new BackendDataAdapter({
  cacheEnabled: true,
  cacheTTL: 300000, // 5 minutes
});

// First call hits API (slow)
const data1 = await adapter.getBacktestResults('AAPL');

// Second call uses cache (fast)
const data2 = await adapter.getBacktestResults('AAPL');

// Force refresh (bypass cache)
const fresh = await adapter.getBacktestResults('AAPL', true);

// Clear all cache
adapter.clearCache();
```

## Transform to Framework Types

```typescript
import { BackendDataAdapter } from './src/framework/adapters';
import { Timeframe } from './src/framework/core/types';

const adapter = new BackendDataAdapter();

// Get and transform RSI chart to MarketData
const rsiChart = await adapter.getRSIChart('AAPL', 252);
const marketData = adapter.transformToMarketData('AAPL', rsiChart);
console.log('Market data bars:', marketData.bars.length);

// Transform percentile forward to PercentileData
const forward = await adapter.getPercentileForward('AAPL');
const percentileData = adapter.transformToPercentileData(forward, Timeframe.D1);
console.log('Percentile:', percentileData.percentile);

// Transform risk metrics
const backtest = await adapter.getBacktestResults('AAPL');
const riskMetrics = adapter.transformRiskMetrics(backtest, '5.0');
console.log('Win rate:', riskMetrics?.winRate);
```

## Configuration

### Custom Backend URL

```typescript
const adapter = new BackendDataAdapter({
  baseUrl: 'http://api.example.com:8000',
  timeout: 60000,     // 1 minute
  retries: 5,
  retryDelay: 2000,   // 2 seconds
});
```

### Custom Yahoo Finance Settings

```typescript
const adapter = new YFinanceAdapter({
  timeout: 15000,     // 15 seconds
  retries: 3,
  userAgent: 'MyTradingApp/1.0',
});
```

## API Reference

### BackendDataAdapter Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `getBacktestResults(ticker, forceRefresh?)` | `BacktestResponse` | Backtest performance matrix |
| `getRSIChart(ticker, days?)` | `RSIChartResponse` | RSI/percentile time series |
| `getPercentileForward(ticker, forceRefresh?)` | `PercentileForwardResponse` | Daily forward predictions |
| `getPercentileForward4H(ticker, forceRefresh?)` | `PercentileForwardResponse` | 4H forward predictions |
| `runMonteCarloSimulation(request)` | `MonteCarloResponse` | Monte Carlo simulation |
| `getLiveSignal(ticker)` | `LiveSignalResponse` | Real-time entry signal |
| `getMultiTimeframeAnalysis(ticker)` | `MultiTimeframeResponse` | Divergence analysis |
| `batchBacktest(request)` | `any` | Batch multiple tickers |
| `healthCheck()` | `boolean` | Check backend status |

### YFinanceAdapter Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `getMarketData(ticker, timeframe, period)` | `MarketData` | Historical OHLCV |
| `getCurrentPrice(ticker)` | `number` | Latest price |
| `getMultiTimeframeData(ticker, timeframes)` | `Map<Timeframe, MarketData>` | Multi-TF data |
| `calculateRSI(bars, period)` | `number[]` | RSI values |
| `calculateSMA(values, period)` | `number[]` | SMA values |
| `calculateRSIMA(bars, rsiPeriod, maPeriod)` | `number[]` | RSI-MA values |
| `validateTicker(ticker)` | `boolean` | Check ticker validity |

## Troubleshooting

### Backend Not Running

**Problem:** `Failed to fetch http://localhost:8000`

**Solution:**
```bash
cd /workspaces/New-test-strategy/backend
python api.py
```

### Import Errors

**Problem:** `Cannot find module './src/framework/adapters'`

**Solution:**
```bash
npm install
npx tsc  # Compile TypeScript
```

### Rate Limiting

**Problem:** Yahoo Finance returns 429 errors

**Solution:**
- Reduce request frequency
- Add delays between requests
- Use backend adapter for historical data
- Cache aggressively

### Type Errors

**Problem:** TypeScript compilation errors

**Solution:**
```bash
# Check TypeScript version
npx tsc --version

# Install dependencies
npm install

# Check for errors
npx tsc --noEmit
```

## Next Steps

1. **Read the full documentation:**
   - `/workspaces/New-test-strategy/src/framework/adapters/README.md`

2. **Run the examples:**
   - `/workspaces/New-test-strategy/tests/framework/adapters/backend-adapter.example.ts`
   - `/workspaces/New-test-strategy/tests/framework/adapters/yfinance-adapter.example.ts`

3. **Integrate with your framework:**
   - See `/workspaces/New-test-strategy/docs/ADAPTER-IMPLEMENTATION.md`

4. **Explore the Python backend:**
   - `/workspaces/New-test-strategy/backend/api.py`

## Support

For issues or questions, refer to:
- Implementation summary: `/workspaces/New-test-strategy/docs/ADAPTER-IMPLEMENTATION.md`
- Full README: `/workspaces/New-test-strategy/src/framework/adapters/README.md`
- Type definitions: `/workspaces/New-test-strategy/src/framework/adapters/types.ts`
