# Live Trading Signals System

## Overview

This system transforms historical backtest analysis into **real-time, actionable trading signals**. It applies lessons learned from past data to current market conditions, answering the critical question: **"What should I do RIGHT NOW?"**

## Key Features

### 1. Entry Signals (`/api/live-signal/{ticker}`)

Analyzes current market conditions to determine if NOW is a good time to enter a position.

**Provides:**
- **Signal Strength**: `strong_buy`, `buy`, `neutral`, or `avoid`
- **Confidence Score**: 0-100% based on historical data quality
- **Current Percentile**: Where the stock is in its RSI-MA percentile range
- **Expected Returns**: Historical median returns at 7d, 14d, and 21d
- **Win Rate**: Historical win rate from similar entry conditions
- **Recommended Position Size**: 0-100% based on signal quality
- **Detailed Reasoning**: Why this signal is being generated
- **Risk Factors**: Warnings about current market conditions

**Example Signal:**
```json
{
  "entry_signal": {
    "signal_strength": "strong_buy",
    "confidence": 0.85,
    "current_percentile": 3.2,
    "expected_return_7d": 2.8,
    "expected_return_14d": 4.2,
    "expected_return_21d": 5.5,
    "win_rate_historical": 0.72,
    "recommended_entry_size": 100,
    "reasoning": [
      "Percentile at 3.2% - historically top 5% entry zone",
      "Historical 5% entries: 43 trades analyzed",
      "Recent 90-day similar entries: 5 trades, avg return: 6.2%"
    ],
    "risk_factors": []
  }
}
```

### 2. Exit Signals (`/api/exit-signal`)

For existing positions, calculates real-time exit pressure and provides actionable recommendations.

**Provides:**
- **Current Return**: P&L since entry
- **Days Held**: How long you've been in the trade
- **Exit Pressure**: 0-100 composite score (>70 = strong exit signal)
  - Velocity component (percentile rising too fast)
  - Time decay component (edge diminishes over time)
  - Divergence component (daily vs 4h momentum mismatch)
  - Volatility component (regime-based risk)
- **Recommended Action**: `hold`, `reduce_25`, `reduce_50`, `reduce_75`, `exit_all`
- **Urgency**: `low`, `medium`, `high`, `critical`
- **Expectancy Comparison**: Expected return if hold 7 more days vs exit now
- **Trailing Stop Level**: ATR-based adaptive stop
- **Detailed Breakdown**: Component-by-component reasoning

**Example Signal:**
```json
{
  "exit_signal": {
    "current_return": 8.3,
    "days_held": 12,
    "exit_pressure": 72,
    "recommended_action": "reduce_50",
    "urgency": "high",
    "expected_return_if_hold_7d": 1.2,
    "expected_return_if_exit_now": 8.3,
    "trailing_stop": 228.50,
    "reasoning": [
      "Current return: +8.3% after 12 days",
      "Exit pressure: 72/100",
      "  • Velocity: 18/25 pts",
      "  • Time decay: 12/20 pts",
      "  • Divergence: 22/25 pts",
      "  • Volatility: 20/30 pts",
      "Trade state: Distribution",
      "Expected return if hold vs exit now: 1.2% vs 8.3%",
      "Trailing stop: $228.50 (2.1% below current)"
    ]
  }
}
```

## How It Works

### Entry Signal Logic

1. **Fetches Latest Data**: Gets most recent price and percentile data
2. **Compares to Historical Entries**: Finds similar entry conditions from backtests
3. **Calculates Expected Returns**: Uses median returns from similar past situations
4. **Checks Risk Factors**:
   - Recent momentum (rapid rise = wait for pullback)
   - Volatility regime (high vol = reduce size)
   - Distance from 52-week high/low
5. **Generates Recommendation**: Combines all factors into actionable signal

### Exit Signal Logic

1. **Calculates Exit Pressure Components**:
   - **Velocity**: Is percentile rising >5pts/day? (Exhaustion signal)
   - **Time Decay**: Edge diminishes exponentially after entry
   - **Divergence**: Daily momentum vs approximated 4h (distribution detection)
   - **Volatility**: High vol regime = higher exit bias
2. **Classifies Trade State**:
   - Rebound Initiation (D1-D3)
   - Momentum Establishment (D3-D7)
   - Acceleration (rapid percentile climb)
   - Distribution (stall + divergence)
   - Reversal (percentile declining)
3. **Calculates Conditional Expectancy**:
   - E[Return|Hold 7d] from similar historical situations
   - E[Return|Exit Now] = current P&L
4. **Generates Exposure Recommendation**:
   - Combines pressure, state, and expectancy
   - Maps to specific action (hold, reduce_25, reduce_50, reduce_75, exit_all)
5. **Sets Urgency Level**:
   - Critical: Pressure >80 OR stop hit
   - High: Pressure >70
   - Medium: Pressure >50
   - Low: Pressure <50

## Frontend UI

The **Live Signals** tab (first tab in dashboard) provides:

### Entry Mode
- Big, clear signal strength badge (STRONG BUY, BUY, NEUTRAL, AVOID)
- Confidence percentage
- Expected returns table (7d, 14d, 21d)
- Historical win rate
- Recommended position size
- Green box with reasoning bullets
- Orange/yellow box with risk factors (if any)
- Market context (52w high/low distances)

### Exit Mode
- Input fields for entry price and date
- Recommended action badge (HOLD, REDUCE 25%, etc.)
- Urgency indicator (Low, Medium, High, Critical)
- Current P&L and days held
- Exit pressure gauge (0-100)
- Expected return comparison (hold vs exit)
- Trailing stop level
- Detailed analysis with component breakdown

## Integration with Historical System

The live signals system **applies** the statistical edge found in historical analysis:

- **Historical**: "Entries at 5% percentile have 72% win rate and 5.5% median return at D21"
- **Live Signal**: "Current percentile is 3.2% → STRONG BUY → Enter with 100% size → Expect +5.5% in 21 days"

- **Historical**: "Exit pressure >70 with distribution state = avg future return only +1.2%"
- **Live Signal**: "Exit pressure is 72, state is Distribution, you're at +8.3% → REDUCE 50% → Urgency HIGH"

## Usage Examples

### Checking Entry Opportunity
```bash
curl http://localhost:8000/api/live-signal/AAPL
```

**Decision Flow:**
1. If signal = `strong_buy` + confidence >80% → Enter with full size
2. If signal = `buy` + confidence >70% → Enter with 50-75% size
3. If signal = `neutral` → Wait for better setup
4. If signal = `avoid` → Stay out

### Checking Exit for Existing Position
```bash
curl -X POST http://localhost:8000/api/exit-signal \\
  -H "Content-Type: application/json" \\
  -d '{
    "ticker": "AAPL",
    "entry_price": 225.50,
    "entry_date": "2025-09-10"
  }'
```

**Decision Flow:**
1. If urgency = `critical` → Exit immediately (at least 75%)
2. If urgency = `high` AND expected_hold < expected_exit → Reduce 50%
3. If urgency = `medium` → Consider partial exit (25%)
4. If urgency = `low` AND action = `hold` → Hold full position

## Key Advantages

1. **Prospective, Not Retrospective**: Acts on current data, not past events
2. **Quantitative**: Based on statistical analysis of 100s of historical trades
3. **Adaptive**: ATR-based stops adapt to volatility
4. **Multi-Factor**: Combines momentum, time, divergence, volatility
5. **Actionable**: Clear recommendations with specific position sizing
6. **Explainable**: Detailed reasoning for every signal
7. **Risk-Aware**: Highlights concerns and adjusts size accordingly

## Technical Implementation

### Backend Stack
- **`live_signal_generator.py`**: Core signal generation engine
- **FastAPI Endpoints**: `/api/live-signal/{ticker}` and `/api/exit-signal`
- **Dependencies**: Uses existing `EnhancedPerformanceMatrixBacktester` for historical context

### Frontend Stack
- **`LiveTradingSignals.tsx`**: React component with toggle between entry/exit modes
- **Material-UI**: Professional trading UI with badges, cards, chips
- **Real-time Updates**: Refresh button to get latest signals

### Data Flow
```
User → Frontend → API Endpoint → LiveSignalGenerator
                                        ↓
                        Fetch latest market data (yfinance)
                                        ↓
                        Calculate current percentile
                                        ↓
                        Compare to historical entry events
                                        ↓
                        Generate signal with reasoning
                                        ↓
API Response ← JSON with signal details
      ↓
Frontend displays actionable recommendation
```

## Future Enhancements

- **Real-time WebSocket Updates**: Push signals every minute
- **Multi-Ticker Screener**: Scan all tickers for entry signals
- **Alert System**: Notify when strong signals appear
- **Position Tracker**: Track multiple open positions
- **Signal History**: Log all signals for performance tracking
- **Backtesting Signals**: Test signal accuracy against future returns
- **4h Data Integration**: Replace 4h momentum approximation with actual 4h bars

## Restart Instructions

After making backend changes:
1. Stop current backend: `Ctrl+C` in terminal
2. Restart: `python3 api.py`
3. Frontend auto-reloads with Vite HMR

The system is now fully operational and ready to generate real-time trading signals!
