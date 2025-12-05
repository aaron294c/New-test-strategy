/**
 * Complete Example: Trading Framework with Execution Integration
 *
 * This example demonstrates how to integrate the execution layer
 * with the trading framework for end-to-end automated trading.
 */

import { TradingFramework } from '../src/framework/core/TradingFramework';
import {
  ExecutionManager,
  PaperTradingVenue,
  ExecutionEventType,
  RiskLimits,
  OrderSide,
  OrderType,
} from '../src/framework/execution';
import {
  EventType,
  Timeframe,
  MarketData,
  OHLCV,
} from '../src/framework/core/types';

// ==================== CONFIGURATION ====================

// Configure paper trading venue
const paperVenue = new PaperTradingVenue({
  initialCapital: 100000,
  commission: 0.01, // $0.01 per share
  commissionPercent: 0.001, // 0.1% of order value
  slippagePercent: 0.0005, // 0.05% slippage
  fillDelay: 50, // 50ms fill delay
  rejectRate: 0, // No rejections for demo
  partialFillRate: 0, // No partial fills for demo
});

// Configure risk limits
const riskLimits: RiskLimits = {
  maxPositionSize: 1000,
  maxOrderValue: 50000,
  maxDailyOrders: 100,
  maxOpenPositions: 5,
  maxLeverage: 1,
  maxDrawdown: 0.15, // 15%
  minAccountBalance: 10000,
  allowedInstruments: ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],
};

// Create execution manager
const executionManager = new ExecutionManager({
  venue: paperVenue,
  riskLimits,
  autoExecute: true, // Automatically execute framework signals
  autoStopLoss: true, // Automatically place stop-loss orders
  reconciliationInterval: 5, // Reconcile every 5 minutes
  enableLogging: true,
  logLevel: 'info',
});

// Create trading framework
const framework = new TradingFramework({
  timeframes: [
    { timeframe: Timeframe.H4, weight: 0.6 },
    { timeframe: Timeframe.D1, weight: 0.4 },
  ],
  primaryTimeframe: Timeframe.H4,
  regimeDetection: {
    lookbackPeriod: 50,
    coherenceThreshold: 0.7,
    updateFrequency: 15,
  },
  percentileSettings: {
    entryPercentile: 90,
    stopPercentile: 95,
    lookbackBars: 100,
    adaptive: true,
  },
  riskManagement: {
    maxRiskPerTrade: 0.01, // 1% per trade
    maxTotalRisk: 0.05, // 5% total
    maxPositions: 5,
    minWinRate: 0.4,
    minExpectancy: 0.5,
  },
  scoring: {
    factors: [],
    minScore: 0.6,
    rebalanceFrequency: 30,
  },
  allocation: {
    totalCapital: 100000,
    maxRiskPerTrade: 0.01,
    maxTotalRisk: 0.05,
    maxPositions: 5,
    minScore: 0.6,
  },
  updateInterval: 60000, // 1 minute
  logLevel: 'info',
});

// ==================== EVENT HANDLERS ====================

// Connect framework signals to execution manager
framework.on(EventType.ENTRY_SIGNAL, async (event) => {
  console.log(`\n📈 Entry Signal: ${event.instrument}`);
  console.log(`Direction: ${event.data.direction}`);
  console.log(`Price: ${event.data.price}`);
  console.log(`Composite Score: ${event.data.metadata?.compositeScore}`);

  await executionManager.handleEntrySignal(event);
});

framework.on(EventType.EXIT_SIGNAL, async (event) => {
  console.log(`\n📉 Exit Signal: ${event.instrument}`);
  console.log(`Reason: ${event.data.reason}`);
  console.log(`P&L: ${event.data.pnl?.toFixed(2)}`);

  await executionManager.handleExitSignal(event);
});

framework.on(EventType.STOP_ADJUSTMENT, async (event) => {
  console.log(`\n🛑 Stop Adjusted: ${event.instrument}`);
  console.log(`New Stop: ${event.data.newStop.currentStop}`);

  await executionManager.handleStopAdjustment(event);
});

framework.on(EventType.REGIME_CHANGE, (event) => {
  console.log(`\n🔄 Regime Change: ${event.data.from} → ${event.data.to}`);
  console.log(`Coherence: ${event.data.coherence?.toFixed(2)}`);
});

// Listen to execution events
executionManager.on(ExecutionEventType.ORDER_SUBMITTED, (event) => {
  console.log(`✓ Order Submitted: ${event.orderId}`);
});

executionManager.on(ExecutionEventType.ORDER_FILLED, (event) => {
  console.log(`✓ Order Filled: ${event.instrument} @ ${event.data.averageFillPrice}`);
  console.log(`  Quantity: ${event.data.filledQuantity}`);
  console.log(`  Commission: ${event.data.fills.reduce((s: number, f: any) => s + f.commission, 0).toFixed(2)}`);
});

executionManager.on(ExecutionEventType.POSITION_OPENED, (event) => {
  console.log(`\n💼 Position Opened: ${event.instrument}`);
  console.log(`  Direction: ${event.data.direction}`);
  console.log(`  Quantity: ${event.data.quantity}`);
  console.log(`  Entry Price: ${event.data.entryPrice}`);
  console.log(`  Stop Loss: ${event.data.stopLoss.currentStop}`);
});

executionManager.on(ExecutionEventType.POSITION_CLOSED, (event) => {
  console.log(`\n💰 Position Closed: ${event.instrument}`);
  console.log(`  P&L: $${event.data.unrealizedPnL.toFixed(2)}`);
  console.log(`  Commission: $${event.data.totalCommission.toFixed(2)}`);
  console.log(`  Net P&L: $${event.data.realizedPnL.toFixed(2)}`);
});

executionManager.on(ExecutionEventType.ORDER_REJECTED, (event) => {
  console.error(`\n❌ Order Rejected: ${event.instrument}`);
  console.error(`  Reason: ${event.data.rejectionReason}`);
});

executionManager.on(ExecutionEventType.RISK_LIMIT_BREACHED, (event) => {
  console.error(`\n⚠️ Risk Limit Breached: ${event.message}`);
});

executionManager.on(ExecutionEventType.EXECUTION_ERROR, (event) => {
  console.error(`\n🔥 Execution Error: ${event.message}`);
  console.error(event.data);
});

// ==================== MARKET DATA SIMULATION ====================

/**
 * Generate simulated OHLCV data for testing
 */
function generateMarketData(
  instrument: string,
  bars: number,
  basePrice: number
): MarketData {
  const ohlcv: OHLCV[] = [];
  let price = basePrice;

  const now = new Date();

  for (let i = bars - 1; i >= 0; i--) {
    // Random walk with drift
    const change = (Math.random() - 0.48) * (basePrice * 0.02); // Slight upward bias
    price = Math.max(basePrice * 0.5, price + change);

    const high = price * (1 + Math.random() * 0.01);
    const low = price * (1 - Math.random() * 0.01);
    const open = low + Math.random() * (high - low);
    const close = low + Math.random() * (high - low);
    const volume = Math.floor(1000000 + Math.random() * 9000000);

    const timestamp = new Date(now.getTime() - i * 4 * 60 * 60 * 1000); // 4h bars

    ohlcv.push({
      open,
      high,
      low,
      close,
      volume,
      timestamp,
      timeframe: Timeframe.H4,
    });
  }

  return {
    instrument,
    bars: ohlcv,
    currentPrice: ohlcv[ohlcv.length - 1].close,
    lastUpdate: now,
  };
}

/**
 * Update market data with new bar
 */
function updateMarketData(data: MarketData): MarketData {
  const lastBar = data.bars[data.bars.length - 1];
  const change = (Math.random() - 0.48) * (lastBar.close * 0.02);
  const newPrice = Math.max(lastBar.close * 0.9, lastBar.close + change);

  const high = newPrice * (1 + Math.random() * 0.01);
  const low = newPrice * (1 - Math.random() * 0.01);
  const open = low + Math.random() * (high - low);
  const close = newPrice;
  const volume = Math.floor(1000000 + Math.random() * 9000000);

  const newBar: OHLCV = {
    open,
    high,
    low,
    close,
    volume,
    timestamp: new Date(),
    timeframe: Timeframe.H4,
  };

  // Update paper venue price
  paperVenue.setMarketPrice(data.instrument, newPrice);

  return {
    ...data,
    bars: [...data.bars.slice(-199), newBar], // Keep last 200 bars
    currentPrice: newPrice,
    lastUpdate: new Date(),
  };
}

// ==================== MAIN EXECUTION ====================

async function runTradingSystem() {
  console.log('='.repeat(60));
  console.log('🚀 Starting Trading Framework with Execution Integration');
  console.log('='.repeat(60));

  // Initialize market data for instruments
  const instruments = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'];
  const marketDataMap = new Map<string, MarketData>();

  instruments.forEach((instrument, i) => {
    const basePrice = 100 + i * 50; // Different base prices
    const data = generateMarketData(instrument, 200, basePrice);
    marketDataMap.set(instrument, data);
    framework.addMarketData(instrument, data);

    // Set initial paper trading prices
    paperVenue.setMarketPrice(instrument, data.currentPrice);
  });

  // Start systems
  framework.start();
  executionManager.start();

  console.log('\n✓ Framework and Execution Manager started\n');

  // Main trading loop
  let updateCount = 0;
  const updateInterval = setInterval(async () => {
    updateCount++;

    // Update market data for all instruments
    for (const [instrument, data] of marketDataMap) {
      const updatedData = updateMarketData(data);
      marketDataMap.set(instrument, updatedData);
      framework.addMarketData(instrument, updatedData);

      // Update positions with current prices
      await executionManager.updatePosition(instrument, updatedData);
    }

    // Print status every 10 updates
    if (updateCount % 10 === 0) {
      await printSystemStatus();
    }

    // Stop after 100 updates (demo)
    if (updateCount >= 100) {
      clearInterval(updateInterval);
      await shutdown();
    }
  }, 5000); // Update every 5 seconds for demo
}

/**
 * Print system status
 */
async function printSystemStatus() {
  console.log('\n' + '='.repeat(60));
  console.log('📊 System Status');
  console.log('='.repeat(60));

  // Framework state
  const state = framework.getState();
  console.log('\n🎯 Framework:');
  console.log(`  Active Positions: ${state.positions.length}`);
  console.log(`  Total P&L: $${state.metrics.totalPnL.toFixed(2)}`);
  console.log(`  Risk Exposure: $${state.metrics.totalRiskExposure.toFixed(2)}`);
  console.log(`  Regime: ${state.currentRegime.dominantRegime} (coherence: ${state.currentRegime.coherence.toFixed(2)})`);

  // Execution stats
  const execStats = executionManager.getStats();
  console.log('\n📈 Execution:');
  console.log(`  Total Orders: ${execStats.totalOrders}`);
  console.log(`  Fill Rate: ${execStats.fillRate.toFixed(1)}%`);
  console.log(`  Total Commissions: $${execStats.totalCommissions.toFixed(2)}`);

  // Account balance
  const balance = await paperVenue.getAccountBalance();
  console.log('\n💰 Account:');
  console.log(`  Cash: $${balance.cash.toFixed(2)}`);
  console.log(`  Equity: $${balance.equity.toFixed(2)}`);
  console.log(`  Unrealized P&L: $${balance.unrealizedPnL.toFixed(2)}`);
  console.log(`  Realized P&L: $${balance.realizedPnL.toFixed(2)}`);

  // Positions
  const positions = executionManager.getPositions();
  if (positions.length > 0) {
    console.log('\n📋 Open Positions:');
    positions.forEach((pos) => {
      const pnlPercent = ((pos.unrealizedPnL / pos.positionValue) * 100).toFixed(2);
      console.log(`  ${pos.instrument}: ${pos.direction} ${pos.quantity} @ ${pos.entryPrice.toFixed(2)}`);
      console.log(`    Current: ${pos.currentPrice.toFixed(2)}, P&L: $${pos.unrealizedPnL.toFixed(2)} (${pnlPercent}%)`);
    });
  }

  console.log('='.repeat(60) + '\n');
}

/**
 * Shutdown trading system
 */
async function shutdown() {
  console.log('\n' + '='.repeat(60));
  console.log('🛑 Shutting Down Trading System');
  console.log('='.repeat(60));

  // Close all positions
  const positions = executionManager.getPositions();
  for (const position of positions) {
    console.log(`\nClosing position: ${position.instrument}`);
    await paperVenue.closePosition(position.instrument);
  }

  // Final status
  await printSystemStatus();

  // Final statistics
  const stats = executionManager.getStats();
  console.log('\n📊 Final Statistics:');
  console.log(`  Total Orders: ${stats.totalOrders}`);
  console.log(`  Filled: ${stats.filledOrders}`);
  console.log(`  Cancelled: ${stats.cancelledOrders}`);
  console.log(`  Rejected: ${stats.rejectedOrders}`);
  console.log(`  Fill Rate: ${stats.fillRate.toFixed(1)}%`);
  console.log(`  Win Rate: ${stats.winRate.toFixed(1)}%`);
  console.log(`  Profit Factor: ${stats.profitFactor.toFixed(2)}`);
  console.log(`  Max Drawdown: ${(stats.maxDrawdown * 100).toFixed(2)}%`);

  // Stop systems
  framework.stop();
  executionManager.stop();

  console.log('\n✓ Systems stopped');
  console.log('='.repeat(60) + '\n');
}

// ==================== MANUAL TRADING EXAMPLE ====================

/**
 * Example: Manual order placement
 */
async function manualTradingExample() {
  console.log('\n📝 Manual Trading Example\n');

  // Submit market order
  console.log('Submitting market buy order for AAPL...');
  const marketOrder = await executionManager.submitOrder({
    instrument: 'AAPL',
    side: OrderSide.BUY,
    type: OrderType.MARKET,
    quantity: 100,
    metadata: {
      strategyName: 'manual',
      signal: 'manual_entry',
    },
  });
  console.log(`Order ID: ${marketOrder.id}`);

  // Wait for fill
  await new Promise((resolve) => setTimeout(resolve, 200));

  // Submit limit order
  console.log('\nSubmitting limit sell order for MSFT...');
  const limitOrder = await executionManager.submitOrder({
    instrument: 'MSFT',
    side: OrderSide.SELL,
    type: OrderType.LIMIT,
    quantity: 50,
    price: 200.00,
  });
  console.log(`Order ID: ${limitOrder.id}`);

  // Submit stop-loss order
  console.log('\nSubmitting stop-loss order for AAPL...');
  const stopOrder = await executionManager.submitOrder({
    instrument: 'AAPL',
    side: OrderSide.SELL,
    type: OrderType.STOP_LOSS,
    quantity: 100,
    stopPrice: 145.00,
  });
  console.log(`Order ID: ${stopOrder.id}`);
}

// ==================== RUN ====================

if (require.main === module) {
  runTradingSystem().catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export {
  framework,
  executionManager,
  paperVenue,
  runTradingSystem,
  manualTradingExample,
};
