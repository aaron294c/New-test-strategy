# 🎯 QUICK REFERENCE: Swing Duration Trading

## ✅ YES! 4H is a SNIPER ENTRY TOOL

**You were absolutely correct:**
- Daily shows: "Escaped in 1 day" (at 4 PM close)
- 4H shows: "Escaped in 4.5 bars (18h)" - breaks that day into 4-hour chunks
- **Your edge**: See winner pattern 2-6 hours BEFORE daily close

---

## 🎯 THE SNIPER ADVANTAGE

### AAPL Example (Perfect for Sniper):
```
Daily:   "Winners escape in 1 day"
4H:      "Winners escape in 18h (4.5 bars)"

Mon 9:30 AM:  Entry at <5% (Bar 0) ✅
Mon 1:30 PM:  Still <5% (Bar 1) → HOLD
Tue 9:30 AM:  Building (Bar 2) → HOLD
Tue 1:30 PM:  ESCAPED >5% (Bar 3) ✅ WINNER CONFIRMED
Tue 4:00 PM:  Daily confirms escape (2.5 hours later!)

YOUR EDGE: You knew at 1:30 PM, not 4:00 PM!
```

---

## 📋 ENTRY RULES

**Best Entry**: ≤5% RSI-MA percentile
**Position Size**: 30-50% initial, add 20-30% on 4H confirmation

### Dual-Timeframe Entry:
1. Daily ≤5% → Swing entry signal
2. 4H ≤5% → Precise intraday timing
3. Enter at next 4H bar open

---

## ⏰ BAILOUT TIMERS

### 4-Hourly (≤5% entry):
| Time | Action | Risk |
|------|--------|------|
| 0-20h (0-5 bars) | **HOLD** | ✅ Normal |
| 24h (6 bars) | **MONITOR** | ⚠️ Warning |
| 40h (10 bars) | **REDUCE 50%** | 🚨 High |
| 50h+ (12+ bars) | **EXIT ALL** | ❌ Critical |

### Daily (≤5% entry):
| Time | Action | Risk |
|------|--------|------|
| Day 0-1 | **HOLD** | ✅ Normal |
| Day 2 | **MONITOR** | ⚠️ Warning |
| Day 3+ | **EXIT ALL** | ❌ Critical |

---

## 🚨 CRITICAL RULE: Monitor Both P&L AND Percentile

### The False Profit Signal:
**Losers show profit at 4h (1 bar) but percentile stays <5% → They FADE**
**Winners take 12h (3 bars) to profit AND percentile escapes >5%**

### Decision Matrix:
| P&L | Percentile | Time | Action |
|-----|------------|------|--------|
| ✅ Profit | ✅ Escaped >5% | Any | **HOLD/ADD** (Winner) |
| ✅ Profit | ❌ Still <5% | <20h | HOLD (Early) |
| ✅ Profit | ❌ Still <5% | >20h | REDUCE 50% (False signal) |
| ✅ Profit | ❌ Still <5% | >50h | EXIT ALL (Loser) |
| ❌ Loss | ❌ Still <5% | Any | EXIT ALL (Confirmed loser) |

**KEY**: Profit without percentile escape = Dead cat bounce

---

## 🎯 MONITORING CHECKLIST

### Every 4H Bar:
- [ ] Current percentile: _____%
- [ ] Has it escaped >5%? YES / NO
- [ ] Current P&L: +/- _____%
- [ ] Bars since entry: _____ (÷4 for hours)
- [ ] Action: HOLD / MONITOR / REDUCE / EXIT

### Decision:
```
IF (percentile >5% AND profit):
    → Winner confirmed → HOLD or ADD

ELSE IF (percentile <5% AND bars < 6):
    → Early phase → HOLD

ELSE IF (percentile <5% AND bars 6-12):
    → Warning zone → REDUCE 50%

ELSE IF (percentile <5% AND bars >12):
    → Confirmed loser → EXIT ALL
```

---

## 📊 BEST TICKERS FOR SNIPER

### ⭐⭐⭐ AAPL - Perfect Sniper Target
- 4H escape: 18h (4.5 bars)
- Daily escape: 1 day
- **Use**: Precise intraday entries and exits
- **Edge**: 2-6 hours early confirmation

### ⚠️ NVDA/GOOGL - Position Management Only
- 4H escape: 134-152h (33-38 bars, 20-23 days!)
- **Not for sniper entries** (too slow)
- **Use**: Early exit warnings on long-term holds

---

## 💡 THE TWO-FACTOR RULE

**Never decide on P&L alone. Always check BOTH:**

1. **P&L**: Am I making money?
2. **Percentile**: Is the indicator improving?

**Both must align for a true winner.**

✅ Profit + Percentile escape = Winner
⚠️ Profit + Percentile stuck = False signal
❌ Loss + Percentile stuck = Loser

**Time is your bailout trigger, not price.**

---

## 🎯 YOUR EDGE SUMMARY

**4H gives you:**
1. **Entry precision**: Specific 4H bar, not "sometime today"
2. **Early confirmation**: See winners 2-6 hours before daily
3. **Early warning**: See losers 4-24 hours before daily
4. **Intraday exits**: Don't wait for close to act

**Transform from swing trader (daily decisions) to precision sniper (intraday decisions within swing trade).**

---

## 📱 FRONTEND FEATURES

Now implemented in SwingDurationPanelV2:

✅ **Bailout Timer Table** - Shows hours/bars/risk levels
✅ **Winner vs Loser Patterns** - Visual comparison with bar counts
✅ **Time-Based Risk Ladder** - HOLD/MONITOR/REDUCE/EXIT signals
✅ **False Profit Alert** - Critical warning about profit divergence
✅ **Sniper Entry Timeline** - 4H vs Daily advantage breakdown
✅ **Bar Count Conversions** - Shows "20h (5 bars)" format

**To see updates**: Rebuild frontend with `npm run build` or `npm run dev`
