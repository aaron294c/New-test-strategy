# MAPI (Momentum-Adapted Percentile Indicator) Implementation

## Overview

MAPI is a custom indicator designed specifically for **momentum stocks** (AAPL, TSLA, AVGO, NFLX) as an alternative to RSI-MA. While RSI-MA works best for mean-reverting stocks with low percentile entries, MAPI inverts this logic for momentum stocks where **high percentile readings indicate strong trend continuation**.

## Key Differences from RSI-MA

| Aspect | RSI-MA (Mean Reversion) | MAPI (Momentum) |
|--------|------------------------|-----------------|
| **Best Entry** | 5-15th percentile (oversold) | 65-85th percentile (strong momentum) |
| **Signal Type** | Oversold bounce | Trend confirmation |
| **EMA Relation** | Price crosses above MA | Price respects MA as support |
| **Exit** | 85-95th percentile | Composite Score < 40th percentile |
| **Ideal Stocks** | SPX, NDX, NVDA, GOOGL | AAPL, TSLA, AVGO, NFLX |

## Core Components

### 1. EDR (EMA Distance Ratio)
```
EDR = (Price - EMA(20)) / ATR(14)
```
- Measures price distance from EMA(20) normalized by volatility (ATR)
- Positive EDR = price above EMA (bullish momentum)
- Magnitude indicates trend strength

### 2. ESV (EMA Slope Velocity)
```
ESV = (EMA(20)_today - EMA(20)_5days_ago) / EMA(20)_5days_ago
```
- Rate of change of EMA itself
- Confirms if trend is accelerating or decelerating

### 3. Composite Momentum Score
```
Composite Score = (EDR Percentile × 0.6) + (ESV Percentile × 0.4)
```
- Weighted combination of EDR and ESV percentiles
- 0-100% scale for easy interpretation

### 4. Regime Detection (ADX)
```
ADX > 25 = Momentum Regime
ADX < 20 = Mean Reversion Regime
```

## Entry Signals

### Strong Momentum Entry
**Conditions:**
- Composite Score > 65th percentile
- Price > EMA(20) > EMA(50)
- ESV > 50th percentile (positive slope)

**Interpretation:** Strong uptrend confirmed, momentum accelerating

### Pullback Entry (EMA Bounce)
**Conditions:**
- Composite Score drops to 30-45% (pullback zone)
- Price touches or slightly penetrates EMA(20)
- ESV > 40th percentile (trend still intact)
- Composite Score begins recovering

**Interpretation:** Healthy pullback in uptrend, price respecting support

## Exit Signal

**Condition:** Composite Score < 40th percentile

**Interpretation:** Momentum weakening, trend potentially reversing

## Implementation Files

### Backend
1. **`/backend/mapi_calculator.py`**
   - Core calculation engine
   - Class: `MAPICalculator`
   - Functions: `calculate_edr()`, `calculate_esv()`, `calculate_composite_score()`, `detect_ema_bounce()`

2. **`/backend/api.py`**
   - New endpoint: `GET /api/mapi-chart/{ticker}?days=252`
   - Returns chart data, current signals, thresholds

### Frontend
1. **`/frontend/src/pages/MAPIIndicatorPage.tsx`**
   - Complete MAPI page component
   - Interactive charts with Lightweight Charts
   - Real-time signal display
   - Three chart modes:
     - Composite Score with entry/exit signals
     - EDR & ESV percentiles
     - Price with EMA(20) and EMA(50)

2. **`/frontend/src/types/index.ts`**
   - New types: `MAPIChartData`, `MAPICurrentSignal`, `MAPIThresholds`, `MAPIResponse`

3. **`/frontend/src/api/client.ts`**
   - New API client: `mapiApi.getMAPIChartData(ticker, days)`

4. **`/frontend/src/App.tsx`**
   - New tab: "MAPI (Momentum)" (Tab #16)
   - Lazy-loaded page component

## Chart Features

### Chart Mode 1: Composite Score
- Line chart of Composite Momentum Score
- Threshold lines:
  - Green dashed (65%) - Strong momentum entry
  - Red dashed (40%) - Exit threshold
  - Gray dotted (50%) - Neutral line
- Markers:
  - Green arrow up ↑ - Strong momentum entry signal
  - Blue circle ○ - Pullback entry signal
  - Red arrow down ↓ - Exit signal

### Chart Mode 2: EDR & ESV
- Two lines: EDR Percentile (blue) and ESV Percentile (pink)
- 50% reference line
- Shows component breakdown

### Chart Mode 3: Price & EMAs
- Price line (white)
- EMA(20) line (blue)
- EMA(50) line (pink)
- Visualizes EMA distance and bounce opportunities

## Current Metrics Dashboard

Displays real-time values:
1. **Composite Score** - Main signal (colored: green >65, red <40)
2. **EDR Percentile** - Price-to-EMA distance strength
3. **ESV Percentile** - Trend acceleration
4. **Distance to EMA(20)** - Percentage distance with sign

## Percentile Lookback Periods

- **EDR Lookback:** 60 days (recent momentum cycles)
- **ESV Lookback:** 90 days (trend strength is more stable)

## Usage Example

### For AAPL (Momentum Stock):

**Scenario 1: Strong Entry**
```
Composite Score: 72%
EDR Percentile: 75%
ESV Percentile: 65%
Price: $248.35 (above EMA(20) $245.20)
→ STRONG MOMENTUM ENTRY signal
```

**Scenario 2: Pullback Entry**
```
Composite Score: 38% (was 72% yesterday)
EDR Percentile: 42%
ESV Percentile: 48%
Price: $246.10 (touching EMA(20) $246.00)
Composite recovering: 38% → 42%
→ PULLBACK ENTRY signal
```

**Scenario 3: Exit**
```
Composite Score: 35%
EDR Percentile: 30%
ESV Percentile: 38%
→ EXIT SIGNAL (momentum weakening)
```

## When to Use MAPI vs RSI-MA

### Use MAPI for:
- Momentum regime stocks (ADX > 25)
- AAPL, TSLA, AVGO, NFLX
- Strong trending environments
- EMA-respecting price action

### Use RSI-MA for:
- Mean reversion regime stocks (ADX < 20)
- SPX, NDX, NVDA, GOOGL
- Range-bound or oscillating markets
- Oversold/overbought bounces

## API Usage

### Get MAPI Data
```bash
GET http://localhost:8000/api/mapi-chart/AAPL?days=252
```

### Response Structure
```json
{
  "success": true,
  "ticker": "AAPL",
  "chart_data": {
    "dates": ["2025-01-01", ...],
    "close": [248.35, ...],
    "composite_score": [72.5, ...],
    "edr_percentile": [75.2, ...],
    "esv_percentile": [65.8, ...],
    "ema20": [245.20, ...],
    "ema50": [242.10, ...],
    "adx": [28.5, ...],
    "regime": ["Momentum", ...],
    "strong_momentum_signals": [true, ...],
    "pullback_signals": [false, ...],
    "exit_signals": [false, ...],
    "current": {
      "composite_score": 72.5,
      "regime": "Momentum",
      "strong_momentum_entry": true,
      ...
    },
    "thresholds": {
      "strong_momentum": 65,
      "exit_threshold": 40,
      ...
    }
  },
  "metadata": {
    "ema_period": 20,
    "atr_period": 14,
    "edr_lookback": 60,
    "esv_lookback": 90
  }
}
```

## Access the Tab

1. Start the application
2. Navigate to the "MAPI (Momentum)" tab (last tab)
3. Select a momentum stock from the ticker dropdown (AAPL, TSLA, AVGO, NFLX recommended)
4. View real-time signals and charts

## Technical Details

### Percentile Calculation
- Uses rolling window approach
- Ranks current value against historical window
- Returns 0-100% percentile rank

### Signal Generation
- Signals generated frame-by-frame (daily)
- Multiple conditions must align for entry
- Exit is single condition (composite < 40%)

### Performance
- Backend caching for repeated requests
- Frontend lazy loading for optimal UX
- Chart rendering optimized with Lightweight Charts library

## Future Enhancements

Potential improvements:
1. **Backtesting Module** - Test MAPI signals historically
2. **Alert System** - Notify when signals trigger
3. **Multi-Timeframe** - Add 4H MAPI alongside daily
4. **Parameter Optimization** - Find optimal thresholds per stock
5. **Regime Auto-Switch** - Automatically use MAPI or RSI-MA based on detected regime

---

**Built:** 2026-01-22
**Status:** ✅ Production Ready
**Location:** Tab #16 in main dashboard
