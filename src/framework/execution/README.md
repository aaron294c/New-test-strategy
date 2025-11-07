# Execution Integration Layer

Comprehensive order execution and position management system for the trading framework.

## Architecture

### Core Components

1. **ExecutionManager** - Main orchestrator
   - Listens to framework entry/exit signals
   - Manages order lifecycle
   - Coordinates position tracking
   - Provides execution statistics

2. **OrderRouter** - Order routing abstraction
   - Venue-agnostic order submission
   - Risk validation and checks
   - Order lifecycle monitoring
   - Support for multiple order types

3. **PositionManager** - Position tracking
   - Real-time position monitoring
   - P&L calculation (realized and unrealized)
   - Position reconciliation with broker
   - Risk metrics per position

4. **PaperTradingVenue** - Simulated execution
   - Paper trading implementation
   - Realistic order fills with slippage
   - Commission simulation
   - No real capital required

## Quick Start

### Basic Setup

```typescript
import { TradingFramework } from '../core/TradingFramework';
import {
  ExecutionManager,
  PaperTradingVenue,
  RiskLimits,
} from './index';

// Create paper trading venue
const venue = new PaperTradingVenue({
  initialCapital: 100000,
  commissionPercent: 0.001, // 0.1%
  slippagePercent: 0.001, // 0.1%
  fillDelay: 100, // 100ms
});

// Configure risk limits
const riskLimits: RiskLimits = {
  maxPositionSize: 1000,
  maxOrderValue: 50000,
  maxDailyOrders: 100,
  maxOpenPositions: 10,
  maxLeverage: 1,
  maxDrawdown: 0.2, // 20%
  minAccountBalance: 10000,
};

// Create execution manager
const executionManager = new ExecutionManager({
  venue,
  riskLimits,
  autoExecute: true,
  autoStopLoss: true,
  reconciliationInterval: 5, // minutes
  enableLogging: true,
  logLevel: 'info',
});

// Create trading framework
const framework = new TradingFramework({
  // ... framework config
});

// Connect execution to framework
framework.on('entry_signal', (event) => {
  executionManager.handleEntrySignal(event);
});

framework.on('exit_signal', (event) => {
  executionManager.handleExitSignal(event);
});

framework.on('stop_adjustment', (event) => {
  executionManager.handleStopAdjustment(event);
});

// Start both systems
framework.start();
executionManager.start();
```

### Listen to Execution Events

```typescript
import { ExecutionEventType } from './types';

// Order filled
executionManager.on(ExecutionEventType.ORDER_FILLED, (event) => {
  console.log(`Order filled: ${event.instrument} @ ${event.data.averageFillPrice}`);
});

// Position opened
executionManager.on(ExecutionEventType.POSITION_OPENED, (event) => {
  console.log(`Position opened: ${event.data.instrument}`);
});

// Position closed
executionManager.on(ExecutionEventType.POSITION_CLOSED, (event) => {
  console.log(`Position closed: P&L = ${event.data.unrealizedPnL}`);
});

// Risk limit breached
executionManager.on(ExecutionEventType.RISK_LIMIT_BREACHED, (event) => {
  console.error(`Risk limit breached: ${event.message}`);
});
```

### Manual Order Submission

```typescript
import { OrderSide, OrderType, TimeInForce } from './types';

// Submit market order
const order = await executionManager.submitOrder({
  instrument: 'AAPL',
  side: OrderSide.BUY,
  type: OrderType.MARKET,
  quantity: 100,
  timeInForce: TimeInForce.GTC,
  metadata: {
    strategyName: 'manual_entry',
    signal: 'buy',
  },
});

// Submit limit order
const limitOrder = await executionManager.submitOrder({
  instrument: 'AAPL',
  side: OrderSide.BUY,
  type: OrderType.LIMIT,
  quantity: 100,
  price: 150.00,
  timeInForce: TimeInForce.DAY,
});

// Submit stop-loss order
const stopOrder = await executionManager.submitOrder({
  instrument: 'AAPL',
  side: OrderSide.SELL,
  type: OrderType.STOP_LOSS,
  quantity: 100,
  stopPrice: 145.00,
});
```

### Position Management

```typescript
// Get all positions
const positions = executionManager.getPositions();

// Get specific position
const position = executionManager.getPosition('AAPL');

// Get position metrics
const positionManager = executionManager.getPositionManager();
const metrics = positionManager.calculatePositionMetrics(position);
console.log(`Return: ${metrics.returnPercent}%`);
console.log(`Risk/Reward: ${metrics.riskRewardRatio}`);

// Get position statistics
const stats = positionManager.getPositionStats();
console.log(`Total Positions: ${stats.totalPositions}`);
console.log(`Unrealized P&L: ${stats.totalUnrealizedPnL}`);
console.log(`Win Rate: ${(stats.winningPositions / (stats.winningPositions + stats.losingPositions)) * 100}%`);
```

### Execution Statistics

```typescript
// Get execution stats
const stats = executionManager.getStats();
console.log(`Fill Rate: ${stats.fillRate}%`);
console.log(`Total Orders: ${stats.totalOrders}`);
console.log(`Total Commissions: ${stats.totalCommissions}`);
console.log(`Win Rate: ${stats.winRate}%`);
console.log(`Profit Factor: ${stats.profitFactor}`);
console.log(`Sharpe Ratio: ${stats.sharpeRatio}`);

// Reset stats for new period
executionManager.resetStats();
```

## Order Types

### Market Orders
- Execute immediately at current market price
- Guaranteed fill (in liquid markets)
- Subject to slippage

### Limit Orders
- Execute only at specified price or better
- May not fill if price not reached
- No slippage beyond limit price

### Stop-Loss Orders
- Trigger when stop price is hit
- Convert to market order when triggered
- Used for risk management

### Trailing Stops (coming soon)
- Dynamic stop-loss that trails price
- Locks in profits while protecting downside

## Risk Management

### Pre-Trade Validation

All orders go through comprehensive risk checks:

1. **Position Size** - Ensure quantity within limits
2. **Order Value** - Check total order value
3. **Daily Orders** - Prevent excessive trading
4. **Open Positions** - Limit concurrent positions
5. **Account Balance** - Verify sufficient funds
6. **Buying Power** - Check margin availability
7. **Instrument Rules** - Allowed/blocked symbols

### Risk Limits Configuration

```typescript
const riskLimits: RiskLimits = {
  maxPositionSize: 1000, // Max quantity per position
  maxOrderValue: 50000, // Max dollar value per order
  maxDailyOrders: 100, // Max orders per day
  maxOpenPositions: 10, // Max concurrent positions
  maxLeverage: 2, // Max leverage ratio
  maxDrawdown: 0.2, // Max 20% drawdown
  minAccountBalance: 10000, // Minimum account balance
  allowedInstruments: ['AAPL', 'MSFT'], // Whitelist
  blockedInstruments: ['GME'], // Blacklist
};
```

## Position Reconciliation

Automatic reconciliation ensures framework positions match broker positions:

```typescript
// Manual reconciliation
const positionManager = executionManager.getPositionManager();
const reconciliation = await positionManager.reconcileWithBroker();

if (reconciliation.discrepancies.length > 0) {
  console.log('Discrepancies found:');
  reconciliation.discrepancies.forEach(disc => {
    console.log(`${disc.instrument}: Framework=${disc.frameworkQuantity}, Broker=${disc.brokerQuantity}`);
    console.log(`Severity: ${disc.severity}, Reason: ${disc.reason}`);
  });
}

// Force sync specific position
await positionManager.syncPositionFromBroker('AAPL');
```

## Paper Trading Features

### Realistic Simulation

The PaperTradingVenue provides:

- **Slippage Simulation** - Configurable price slippage
- **Commission Calculation** - Flat + percentage commissions
- **Fill Delays** - Simulate order processing time
- **Partial Fills** - Random partial fill simulation
- **Order Rejection** - Configurable rejection rate
- **Price Movement** - Simulated market price changes

### Configuration

```typescript
const venue = new PaperTradingVenue({
  initialCapital: 100000, // Starting capital
  commission: 0.01, // $0.01 per share
  commissionPercent: 0.001, // 0.1% of order value
  slippagePercent: 0.001, // 0.1% slippage
  fillDelay: 100, // 100ms fill delay
  rejectRate: 0.01, // 1% rejection rate
  partialFillRate: 0.05, // 5% partial fill rate
});
```

### Testing Utilities

```typescript
// Set specific market price for testing
venue.setMarketPrice('AAPL', 150.00);

// Reset to initial state
venue.reset();

// Get account balance
const balance = await venue.getAccountBalance();
console.log(`Cash: ${balance.cash}`);
console.log(`Equity: ${balance.equity}`);
console.log(`Unrealized P&L: ${balance.unrealizedPnL}`);
```

## Event Types

### Execution Events

- `ORDER_CREATED` - New order created
- `ORDER_SUBMITTED` - Order sent to venue
- `ORDER_FILLED` - Order completely filled
- `ORDER_PARTIALLY_FILLED` - Order partially filled
- `ORDER_CANCELLED` - Order cancelled
- `ORDER_REJECTED` - Order rejected by venue
- `POSITION_OPENED` - New position opened
- `POSITION_UPDATED` - Position updated
- `POSITION_CLOSED` - Position closed
- `STOP_TRIGGERED` - Stop-loss triggered
- `RISK_LIMIT_BREACHED` - Risk limit violation
- `RECONCILIATION_COMPLETE` - Position reconciliation done
- `EXECUTION_ERROR` - Execution error occurred

## Integration with Framework

### Automatic Entry Signal Execution

```typescript
// Framework emits entry signal
framework.on('entry_signal', async (event) => {
  // Execution manager automatically:
  // 1. Creates entry order
  // 2. Submits to venue
  // 3. Places stop-loss (if enabled)
  // 4. Tracks position
  await executionManager.handleEntrySignal(event);
});
```

### Automatic Exit Signal Execution

```typescript
// Framework emits exit signal
framework.on('exit_signal', async (event) => {
  // Execution manager automatically:
  // 1. Creates exit order
  // 2. Closes position
  // 3. Calculates P&L
  // 4. Updates statistics
  await executionManager.handleExitSignal(event);
});
```

### Automatic Stop-Loss Adjustment

```typescript
// Framework emits stop adjustment
framework.on('stop_adjustment', async (event) => {
  // Execution manager automatically:
  // 1. Cancels existing stop order
  // 2. Places new stop at updated level
  // 3. Tracks adjustment reason
  await executionManager.handleStopAdjustment(event);
});
```

## Error Handling

### Comprehensive Logging

```typescript
const executionManager = new ExecutionManager({
  venue,
  riskLimits,
  enableLogging: true,
  logLevel: 'debug', // 'debug' | 'info' | 'warn' | 'error'
});
```

### Error Events

```typescript
executionManager.on(ExecutionEventType.EXECUTION_ERROR, (event) => {
  console.error(`Execution error: ${event.message}`);
  console.error('Error data:', event.data);

  // Implement error recovery logic
  if (event.severity === 'error') {
    // Alert or failsafe actions
  }
});
```

## Advanced Usage

### Custom Execution Venue

Implement your own execution venue:

```typescript
import { ExecutionVenue, Order, OrderParams, BrokerPosition, AccountBalance } from './types';

class MyCustomVenue implements ExecutionVenue {
  name = 'My Broker';
  type = 'live' as const;

  async submitOrder(params: OrderParams): Promise<Order> {
    // Implement broker-specific order submission
  }

  async cancelOrder(orderId: string): Promise<boolean> {
    // Implement order cancellation
  }

  // Implement other required methods...
}

// Use with execution manager
const venue = new MyCustomVenue();
const executionManager = new ExecutionManager({ venue, riskLimits });
```

### Direct Router Access

```typescript
// Get router for advanced operations
const router = executionManager.getRouter();

// Custom validation
const validation = await router.validateOrder(orderParams);
if (!validation.valid) {
  console.log('Validation errors:', validation.errors);
  console.log('Validation warnings:', validation.warnings);
}

// Update risk limits dynamically
router.updateRiskLimits({
  maxPositionSize: 2000,
  maxDailyOrders: 200,
});
```

## Best Practices

1. **Always validate orders** before submission
2. **Monitor execution events** for system health
3. **Reconcile positions regularly** to catch discrepancies
4. **Set appropriate risk limits** for your strategy
5. **Use paper trading** for testing before going live
6. **Log execution events** for audit trail
7. **Handle errors gracefully** with recovery logic
8. **Monitor fill rates** and execution quality
9. **Track commissions** and slippage costs
10. **Test edge cases** with paper trading configuration

## Performance Considerations

- Order validation is synchronous and fast
- Position updates are in-memory
- Reconciliation is async and can be scheduled
- Event handlers should be non-blocking
- Statistics calculations are cached
- Paper trading has minimal overhead

## Future Enhancements

- [ ] Support for multi-leg orders
- [ ] Advanced order types (iceberg, TWAP, VWAP)
- [ ] Smart order routing across venues
- [ ] Fill quality analytics
- [ ] Transaction cost analysis (TCA)
- [ ] Real-time risk monitoring dashboard
- [ ] Historical execution replay
- [ ] Broker API integrations (Interactive Brokers, Alpaca, etc.)
