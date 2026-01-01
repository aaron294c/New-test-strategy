# Principle-Led Multi-Timeframe Trading Framework

A sophisticated, principle-led trading framework that adapts to market conditions through regime detection, percentile-based entry logic, risk-adjusted expectancy, and intelligent capital allocation.

## 🏗️ Architecture Overview

```
src/framework/
├── core/
│   ├── types.ts              # TypeScript interfaces & types
│   ├── config.ts             # Configuration management
│   └── TradingFramework.ts   # Main orchestrator
├── regime-detection/
│   └── RegimeDetector.ts     # Market regime classification
├── percentile-logic/
│   └── PercentileEngine.ts   # Entry/stop percentile logic
├── risk-expectancy/
│   └── ExpectancyCalculator.ts  # Risk-adjusted expectancy
├── composite-scoring/
│   └── InstrumentScorer.ts   # Multi-factor instrument scoring
├── capital-allocation/
│   └── AllocationEngine.ts   # Position sizing & allocation
└── index.ts                  # Main exports
```

## 🎯 Core Principles

### 1. **Principle-Led Design**
- Minimal hardcoded parameters
- Adaptive thresholds based on market data
- Self-adjusting to volatility and regime changes

### 2. **Multi-Timeframe Integration**
- Coherent analysis across H1, H4, D1 timeframes
- Weighted timeframe importance
- Cross-timeframe regime validation

### 3. **Risk-First Approach**
- Position sizing based on stop-loss distance
- Dynamic risk adjustment based on expectancy
- Portfolio-level risk constraints

### 4. **Data-Driven Decisions**
- Historical percentiles for entry/exit
- Statistical confidence in expectancy
- Regime-specific performance tracking

## 📚 Module Details

### Core Framework (`TradingFramework.ts`)

Main orchestrator that coordinates all modules:

```typescript
import { TradingFramework } from './framework';

const framework = new TradingFramework({
  timeframes: [
    { timeframe: 'H4', weight: 0.5 },
    { timeframe: 'H1', weight: 0.3 },
    { timeframe: 'D1', weight: 0.2 },
  ],
  riskManagement: {
    maxRiskPerTrade: 0.01,  // 1% per trade
    maxTotalRisk: 0.05,     // 5% total portfolio
    maxPositions: 8,
  },
});

framework.start();
```

**Features:**
- Automatic regime detection updates
- Real-time score calculations
- Dynamic position management
- Event-driven architecture

### Regime Detection (`RegimeDetector.ts`)

Classifies markets as momentum, mean-reversion, neutral, or transition:

```typescript
const detector = new RegimeDetector({
  lookbackPeriod: 100,
  coherenceThreshold: 0.6,
  trendStrengthMethod: 'adx',
});

const regime = detector.detectMultiTimeframeRegime(marketData, timeframes);
// regime.dominantRegime: 'momentum' | 'mean_reversion' | 'neutral' | 'transition'
// regime.coherence: 0-1 (how aligned timeframes are)
```

**Methods:**
- **ADX**: Average Directional Index for trend strength
- **Linear Regression**: R-squared for trend fitting
- **Percentile Rank**: Current price vs historical distribution
- **Mean Reversion Speed**: Half-life of price deviations
- **Momentum Persistence**: Duration of trending moves

### Percentile Engine (`PercentileEngine.ts`)

Entry and stop-loss based on historical percentiles:

```typescript
const engine = new PercentileEngine({
  lookbackBars: 100,
  entryPercentile: 90,    // Enter at 90th percentile extremes
  stopPercentile: 95,     // Stop at 95th percentile moves
  adaptiveThresholds: true,
});

// Generate entry signal
const entry = engine.generateEntrySignal(marketData, 'H4', regime);

// Calculate adaptive stop-loss
const stopLoss = engine.calculateStopLoss(
  marketData,
  entryPrice,
  'long',
  'H4',
  riskAmount
);
```

**Features:**
- Adaptive percentile thresholds based on regime
- ATR-based stop component (optional)
- Trailing stops in momentum regimes
- Tighter stops in mean-reversion

### Expectancy Calculator (`ExpectancyCalculator.ts`)

Calculates risk-adjusted trading expectancy:

```typescript
const calculator = new ExpectancyCalculator({
  minSampleSize: 30,
  volatilityLookback: 100,
});

// Add trade results
calculator.addTradeResult({
  entryPrice: 50000,
  exitPrice: 51000,
  direction: 'long',
  pnl: 1000,
  riskAmount: 500,
  regime: 'momentum',
});

// Get risk-adjusted expectancy
const expectancy = calculator.calculateRiskAdjustedExpectancy(
  'BTCUSD',
  marketData,
  currentRegime,
  'H4'
);

// expectancy.finalExpectancy: adjusted for volatility & regime
// expectancy.confidence: statistical confidence (0-1)
```

**Metrics:**
- Win rate, average win/loss, win/loss ratio
- Sharpe ratio, max drawdown, recovery factor
- Volatility adjustment (lower vol = better)
- Regime-specific expectancy

### Composite Scorer (`InstrumentScorer.ts`)

Multi-factor instrument scoring and ranking:

```typescript
const scorer = new InstrumentScorer({
  factors: [
    { name: 'regime_alignment', weight: 0.25 },
    { name: 'risk_adjusted_expectancy', weight: 0.25 },
    { name: 'percentile_extreme', weight: 0.20 },
    { name: 'momentum_strength', weight: 0.15 },
    { name: 'volatility_favorability', weight: 0.15 },
  ],
  minScore: 0.6,
});

const score = scorer.calculateScore(
  'BTCUSD',
  marketData,
  regime,
  expectancy,
  timeframes
);

// Rank multiple instruments
const ranked = scorer.rankInstruments([score1, score2, score3]);
```

**Scoring Factors:**
1. **Regime Alignment**: Coherence + favorability
2. **Risk-Adjusted Expectancy**: Normalized with confidence
3. **Percentile Extreme**: Distance from median
4. **Momentum Strength**: Trend persistence
5. **Volatility Favorability**: Low vol preferred

### Capital Allocation (`AllocationEngine.ts`)

Risk-based position sizing and portfolio allocation:

```typescript
const allocator = new AllocationEngine({
  totalCapital: 100000,
  maxRiskPerTrade: 0.01,
  maxTotalRisk: 0.05,
  maxPositions: 8,
  minScore: 0.6,
  diversificationRules: {
    maxPerSector: 0.3,
    maxCorrelatedPositions: 3,
  },
});

const result = allocator.allocateCapital(
  scores,
  portfolioConstraints,
  marketDataMap,
  stopLossMap
);

// result.decisions: allocation decisions with position sizes
// result.totalAllocated: capital allocated
// result.totalRisk: total portfolio risk
```

**Features:**
- Position size = Risk / Stop distance
- Score-based allocation multipliers
- Diversification constraints
- Dynamic rebalancing

## 🚀 Quick Start

### Basic Usage

```typescript
import { TradingFramework, DEFAULT_CONFIG } from './framework';

// 1. Create framework
const framework = new TradingFramework({
  primaryTimeframe: 'H4',
  riskManagement: {
    maxRiskPerTrade: 0.01,
    maxTotalRisk: 0.05,
  },
});

// 2. Add market data
framework.addMarketData('BTCUSD', {
  instrument: 'BTCUSD',
  bars: ohlcvBars,
  currentPrice: 50000,
  lastUpdate: new Date(),
});

// 3. Subscribe to events
framework.on('entry_signal', (event) => {
  console.log('Entry signal:', event.instrument, event.data);
});

framework.on('regime_change', (event) => {
  console.log('Regime changed:', event.data.from, '->', event.data.to);
});

// 4. Start framework
framework.start();

// 5. Get current state
const state = framework.getState();
console.log('Positions:', state.positions.length);
console.log('Current regime:', state.currentRegime.dominantRegime);
console.log('Total P&L:', state.metrics.totalPnL);

// 6. Stop when done
framework.stop();
```

### Conservative Configuration

```typescript
import { createConservativeConfig } from './framework';

const framework = new TradingFramework(createConservativeConfig());
// - 0.5% risk per trade
// - 2.5% total portfolio risk
// - Max 5 positions
// - Higher win rate requirement (40%)
```

### Aggressive Configuration

```typescript
import { createAggressiveConfig } from './framework';

const framework = new TradingFramework(createAggressiveConfig());
// - 2% risk per trade
// - 8% total portfolio risk
// - Max 12 positions
// - Lower win rate requirement (30%)
```

## 📊 Event Types

The framework emits events for monitoring and integration:

- `REGIME_CHANGE`: Market regime shifted
- `ENTRY_SIGNAL`: Entry condition detected
- `EXIT_SIGNAL`: Exit condition (stop hit, score drop)
- `STOP_ADJUSTMENT`: Stop-loss updated
- `SCORE_UPDATE`: Instrument score changed significantly
- `ALLOCATION_CHANGE`: Capital allocation updated
- `POSITION_OPENED`: New position initiated
- `POSITION_CLOSED`: Position closed
- `ERROR`: Framework error occurred

## 🔧 Configuration

### Default Configuration

```typescript
{
  timeframes: [
    { timeframe: 'H4', weight: 0.5 },
    { timeframe: 'H1', weight: 0.3 },
    { timeframe: 'D1', weight: 0.2 },
  ],
  primaryTimeframe: 'H4',

  regimeDetection: {
    lookbackPeriod: 100,
    coherenceThreshold: 0.6,
    updateFrequency: 15,  // minutes
  },

  percentileSettings: {
    entryPercentile: 90,
    stopPercentile: 95,
    lookbackBars: 100,
    adaptive: true,
  },

  riskManagement: {
    maxRiskPerTrade: 0.01,
    maxTotalRisk: 0.05,
    maxPositions: 8,
    minWinRate: 0.35,
    minExpectancy: 0.5,
  },

  allocation: {
    totalCapital: 100000,
    maxRiskPerTrade: 0.01,
    maxTotalRisk: 0.05,
    maxPositions: 8,
    minScore: 0.6,
  },

  updateInterval: 60000,  // 1 minute
  logLevel: 'info',
}
```

## 🧪 Testing

Each module is designed for unit testing:

```typescript
// Test regime detection
describe('RegimeDetector', () => {
  it('should detect momentum regime', () => {
    const detector = new RegimeDetector();
    const regime = detector.detectRegime(trendingData, 'H4');
    expect(regime.type).toBe('momentum');
  });
});

// Test percentile engine
describe('PercentileEngine', () => {
  it('should generate entry at 90th percentile', () => {
    const engine = new PercentileEngine({ entryPercentile: 90 });
    const entry = engine.generateEntrySignal(extremeData, 'H4');
    expect(entry).toBeDefined();
    expect(entry.direction).toBe('short');
  });
});
```

## 📈 Performance Considerations

1. **Update Frequency**: Default 1-minute updates balance responsiveness and overhead
2. **Lookback Periods**: 100 bars typical for most calculations
3. **Memory**: Stores market data, positions, scores in-memory
4. **Event Handlers**: Keep async handlers lightweight

## 🔄 Integration Points

### Data Providers
```typescript
// Integrate with your data source
async function fetchMarketData(symbol: string): Promise<MarketData> {
  const bars = await yourDataProvider.getOHLCV(symbol, '4h', 200);
  return {
    instrument: symbol,
    bars,
    currentPrice: bars[bars.length - 1].close,
    lastUpdate: new Date(),
  };
}

framework.addMarketData('BTCUSD', await fetchMarketData('BTCUSD'));
```

### Execution System
```typescript
framework.on('entry_signal', async (event) => {
  const allocation = framework.getState().allocations.get(event.instrument);
  if (allocation) {
    await yourExecutionSystem.placeOrder({
      symbol: event.instrument,
      side: event.data.direction,
      quantity: allocation.positionSize,
      stopLoss: event.data.stopPrice,
    });
  }
});
```

## 🛠️ Extensibility

### Custom Scoring Factors

```typescript
const scorer = new InstrumentScorer({
  factors: [
    ...DEFAULT_FACTORS,
    {
      name: 'custom_sentiment',
      value: 0,
      weight: 0.10,
      category: 'sentiment',
    },
  ],
});

// Override scoring calculation
class CustomScorer extends InstrumentScorer {
  protected calculateRawFactors(data, regime, expectancy) {
    const base = super.calculateRawFactors(data, regime, expectancy);
    return {
      ...base,
      custom_sentiment: this.calculateSentiment(data),
    };
  }
}
```

### Custom Regime Detection

```typescript
class CustomRegimeDetector extends RegimeDetector {
  public detectRegime(data, timeframe) {
    const base = super.detectRegime(data, timeframe);

    // Add custom regime logic
    const volumeProfile = this.analyzeVolume(data);
    if (volumeProfile.isDistribution) {
      return {
        ...base,
        type: 'mean_reversion',
        confidence: 0.9,
      };
    }

    return base;
  }
}
```

## 📝 Best Practices

1. **Sufficient Data**: Ensure at least 200 bars for reliable calculations
2. **Regular Updates**: Keep market data current (< 5 minutes stale)
3. **Monitor Events**: Subscribe to error events for debugging
4. **Validate Config**: Use `validateConfig()` before starting
5. **Backtesting**: Test configurations on historical data first
6. **Risk Limits**: Start conservative, increase gradually
7. **Diversification**: Don't override diversification rules
8. **Stop Discipline**: Never override stop-loss logic

## 🐛 Troubleshooting

### Common Issues

**"Insufficient data" errors**
- Ensure at least 100+ bars in market data
- Check timeframe filtering is correct

**Low regime coherence**
- Normal during market transitions
- Framework reduces exposure automatically

**No allocations generated**
- Check minimum score threshold (lower if needed)
- Verify risk limits aren't too restrictive
- Ensure market data is current

**Excessive stop-loss triggers**
- Consider lower stop percentile (90 instead of 95)
- Enable ATR-based stops for more adaptive stops
- Review regime classification accuracy

## 📚 References

- **ADX**: Wilder's Average Directional Index
- **Percentile Trading**: Statistical extremes
- **Expectancy**: Van Tharp's position sizing
- **Kelly Criterion**: Optimal bet sizing (adapted)
- **Multi-Timeframe**: Coherence analysis

## 🤝 Contributing

This framework is designed for extension. Consider contributing:
- Additional regime detection methods
- Alternative scoring factors
- Enhanced diversification rules
- Backtesting utilities
- Performance optimizations

---

**Built with principle-led design for adaptive multi-timeframe trading** 🚀
