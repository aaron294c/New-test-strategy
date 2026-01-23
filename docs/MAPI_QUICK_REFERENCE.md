# MAPI Quick Reference Card

## 🎯 What is MAPI?

**Momentum-Adapted Percentile Indicator** - Designed for momentum stocks where **high percentile readings = strong trend** (opposite of RSI-MA's low percentile entries).

---

## 📊 Three Sub-Tabs

### Tab 1: Composite Score (Main View)
**What it shows:** Combined momentum signal (0-100%)
- 🟢 **>65%** = Strong momentum entry
- 🔵 **30-45%** = Pullback entry zone
- 🔴 **<40%** = Exit signal
- Markers show entry/exit points

### Tab 2: EDR & ESV (Components)
**What it shows:** Breakdown of the composite score
- **EDR (Blue)** = Price distance from EMA(20)
- **ESV (Pink)** = EMA slope velocity
- See which component drives the signal

### Tab 3: Price & EMAs (Price Action)
**What it shows:** Price with moving averages
- **White** = Price
- **Blue** = EMA(20)
- **Pink** = EMA(50)
- Visualize support/resistance levels

---

## 🎨 Dashboard Metrics (4 Cards)

| Metric | Description | Color Coding |
|--------|-------------|--------------|
| **Composite Score** | Main signal (0-100%) | 🟢 >65%, 🔴 <40%, ⚪ neutral |
| **EDR Percentile** | Price-to-EMA distance | - |
| **ESV Percentile** | EMA slope velocity | - |
| **Distance to EMA(20)** | % from EMA(20) | 🟢 positive, 🔴 negative |

---

## 📈 Signal Logic

### Strong Momentum Entry (🟢)
- Composite Score **>65%**
- Price **above** EMA(20)
- ESV **>50%** (positive slope)
- **Action:** Consider long entry

### Pullback Entry (🔵)
- Composite Score **30-45%**
- Price **touches** EMA(20)
- ESV **>40%** (trend intact)
- Composite Score **recovering**
- **Action:** Consider long entry on bounce

### Exit Signal (🔴)
- Composite Score **<40%**
- **Action:** Consider closing longs

### Neutral (⚪)
- Composite Score **40-65%**
- **Action:** Wait for clearer signal

---

## 🎭 Regime Detection

| Regime | ADX | Indicator to Use | Entry Style |
|--------|-----|------------------|-------------|
| **Momentum** | >25 | MAPI | High percentile (>65%) |
| **Mean Reversion** | <20 | RSI-MA | Low percentile (5-15%) |

---

## 🔢 Formula Basics

### EDR (EMA Distance Ratio)
```
EDR = (Price - EMA(20)) / ATR(14)
EDR Percentile = Rank(EDR, 60-day window)
```

### ESV (EMA Slope Velocity)
```
ESV = (EMA(20)_today - EMA(20)_5days_ago) / EMA(20)_5days_ago
ESV Percentile = Rank(ESV, 90-day window)
```

### Composite Score
```
Composite = (EDR Percentile × 0.6) + (ESV Percentile × 0.4)
```

---

## 🎯 Best Stocks for MAPI

### High Momentum Stocks
- ✅ **AAPL** - Strong trend follower
- ✅ **TSLA** - High momentum, respects EMAs
- ✅ **AVGO** - Semiconductor momentum
- ✅ **NFLX** - Tech momentum

### Not Ideal (Use RSI-MA Instead)
- ❌ **SPY/SPX** - Mean reverting
- ❌ **QQQ/NDX** - Mean reverting
- ❌ **NVDA** - Mean reverting
- ❌ **GOOGL** - Mean reverting

---

## 🚀 How to Use

### Step 1: Select Stock
Choose a momentum stock from the dropdown

### Step 2: Check Current Metrics
Look at the 4 metric cards at top

### Step 3: Switch Sub-Tabs
- Start with **Composite Score** for quick signal
- Check **EDR & ESV** to understand components
- View **Price & EMAs** for visual confirmation

### Step 4: Interpret Signal
- Green chip = Consider entry
- Blue chip = Wait for bounce
- Red chip = Consider exit
- White chip = Hold or wait

### Step 5: Confirm with Price Action
Switch to **Price & EMAs** tab to visualize:
- Price above/below EMA(20)
- Distance from support
- Trend direction

---

## 🔑 Key Differences: MAPI vs RSI-MA

| Aspect | RSI-MA | MAPI |
|--------|--------|------|
| **Entry Signal** | Low percentile (5-15%) | High percentile (65-85%) |
| **Logic** | Oversold bounce | Momentum confirmation |
| **Best For** | Mean reversion | Momentum stocks |
| **EMA Role** | Cross above | Support/bounce |
| **Stocks** | SPX, NDX, NVDA | AAPL, TSLA, AVGO |

---

## ⚙️ Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| **EMA Period** | 20 | Primary moving average |
| **EMA Slope Period** | 5 | Slope calculation window |
| **ATR Period** | 14 | Volatility normalization |
| **EDR Lookback** | 60 days | Percentile calculation window |
| **ESV Lookback** | 90 days | Percentile calculation window |

---

## 📍 Thresholds

| Threshold | Value | Purpose |
|-----------|-------|---------|
| **Strong Momentum** | 65% | Entry signal |
| **Pullback Zone** | 30-45% | Bounce entry zone |
| **Exit** | 40% | Exit warning |
| **ADX Momentum** | 25 | Regime classification |
| **ADX Mean Rev** | 20 | Regime classification |

---

## 💡 Pro Tips

1. **Use with Momentum Stocks Only**
   - Check ADX >25 first
   - Don't use on mean-reverting stocks

2. **Combine All Three Tabs**
   - Composite for signal
   - Components for confirmation
   - Price & EMAs for visualization

3. **Wait for Pullbacks**
   - Don't chase high scores
   - Wait for 30-45% zone
   - Enter on bounce recovery

4. **Respect the Exit**
   - Exit when <40%
   - Don't fight the trend break
   - Momentum can reverse quickly

5. **Check Distance to EMA(20)**
   - Ideal entry: 0-5% above EMA(20)
   - Too extended: >10% above EMA(20)
   - Risk: Price below EMA(20)

---

## 📱 Access

**Location:** Tab #16 (last tab) - "MAPI (Momentum)"

**URL (Production):**
```
https://new-test-strategy.vercel.app
```

**API Endpoint:**
```
GET https://new-test-strategy.onrender.com/api/mapi-chart/{ticker}?days=252
```

---

## 🧪 Test It

Run the test suite:
```bash
cd /workspaces/New-test-strategy/tests
python3 test_mapi_endpoint.py
```

---

## 📚 Full Documentation

- **Implementation Guide:** `/docs/MAPI_IMPLEMENTATION.md`
- **Sub-Tabs Verification:** `/docs/MAPI_SUB_TABS_VERIFICATION.md`
- **Deployment Summary:** `/docs/MAPI_DEPLOYMENT_SUMMARY.md`

---

## ✅ Status

**Version:** 1.0.0
**Status:** 🟢 Production Ready
**All Sub-Tabs:** ✅ Working
**Tests:** ✅ All Passed (7/7)

---

*MAPI - Built for momentum traders who respect the trend*
