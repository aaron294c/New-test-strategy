# 4H Trading Masterclass: Risk & Entry Strategy

**Based on 410-bar (252 trading day) percentile window with live market data**

---

## 🎯 THE MOST CRITICAL INSIGHTS

### 1. **The 0h Median = INSTANT ESCAPE Pattern** (🔥 MOST IMPORTANT)

**What "Median Time in Low Zone: 0.0h" Actually Means:**

When you see `Median Time in Low Zone: 0.0h` for winners, it means:
- **50%+ of winning trades NEVER re-entered the <5% zone after initial entry**
- They entered at <5%ile and IMMEDIATELY started climbing
- By the very next 4H bar (4 hours later), they were already >5%ile

**CRITICAL INSIGHT:**
> **If your entry is correct, the stock should escape <5% within THE FIRST 4H BAR (4 hours)**

This is the single most important pattern across all stocks:
- ✅ **AAPL, NVDA, TSLA, AMZN**: 0h median = Winners escape IMMEDIATELY
- ⚠️ **MSFT, GOOGL**: 0h median for both winners AND losers = Duration doesn't predict outcome

### 2. **The 20h Bailout Rule** (🚨 RISK MANAGEMENT)

**Pattern across ALL stocks:**
- Winners: Median time to first profit = **20h (5 bars)**
- Losers: Median time stuck in low = **20h (5 bars)**
- Winner escape threshold: **27-31h (7-8 bars)**

**THE RULE:**
```
IF still <5%ile after 20 hours (5 bars) → 🚨 BAIL OUT
IF escaped >5%ile AND showing profit at 20h → ✅ WINNER PATTERN
```

**Why this works:**
- Winners show profit at 20h BUT percentile has already escaped >5%
- Losers show profit at 20h BUT percentile is STILL <5% (false signal!)
- After 20h stuck <5%, losers stay 2-3x longer before eventual escape

---

## 📊 STOCK-BY-STOCK BREAKDOWN

### **NVDA - The Perfect Pattern** (55 samples, 100% escape rate)

**Winner Pattern:**
- Median time in low: **0h** (instant escape!)
- Average escape: **28.6h** (7.2 bars)
- Win rate: **67%** (37W / 18L)
- Predictive p-value: **0.002** (highly significant)

**NVDA Strategy:**
1. ✅ **Entry**: Buy at <5%ile
2. ✅ **Check Bar 1 (4h)**: Should be >5%ile already (if not, MONITOR)
3. ✅ **Check Bar 5 (20h)**: Profit + >5%ile = WINNER ✓
4. 🚨 **Bailout Bar 5**: Still <5%ile = EXIT (loser pattern)
5. ✅ **Hold target**: 28.6h (7.2 bars / ~3 days)

**Risk Ratio:** Losers stuck **3.08x longer** → Early escape is CRITICAL

---

### **AAPL - High Predictive Value** (59 samples, 96% escape)

**Winner Pattern:**
- Median time in low: **0h** (instant escape!)
- Average escape: **27.7h** (6.9 bars)
- Win rate: **46%** (27W / 32L)
- Predictive p-value: **0.003** (highly significant)

**AAPL Strategy:**
1. ✅ **Entry**: Buy at <5%ile
2. ✅ **Check Bar 1 (4h)**: Should be >5%ile (instant escape pattern)
3. ✅ **Check Bar 5 (20h)**: DECISION POINT
   - Profit + >5%ile = HOLD ✓
   - Profit + <5%ile = EXIT 🚨 (false signal)
4. ✅ **Hold target**: 27.7h (~7 bars / 3 days)

**Risk Ratio:** Losers stuck **2.92x longer** → Duration is predictive

---

### **TSLA - Fastest Escape** (40 samples, 100% escape)

**Winner Pattern:**
- Median time in low: **0h** (fastest!)
- Average escape: **26.9h** (6.7 bars)
- Win rate: **65%** (26W / 14L)
- Predictive p-value: **0.014** (significant)

**TSLA Strategy:**
- **Most aggressive bailout**: 20h is MAX tolerance
- Winners escape in **<1 day** on average
- Losers stuck **3.30x longer**
- **Rule**: If not escaping <5% within 1 trading day (6.5h = 1.6 bars), EXIT

---

### **AMZN - Longest Loser Duration** (57 samples, 100% escape)

**Winner Pattern:**
- Median time in low: **0h**
- Average escape: **31.4h** (7.9 bars)
- Win rate: **49%** (28W / 29L)
- Predictive p-value: **0.001** (highly significant)

**Unique Risk:**
- Losers stuck at **MEDIAN 40h** (10 bars / 6 trading days!)
- Longest loser duration of all stocks
- **Critical bailout at 40h** if still <5%ile

**AMZN Strategy:**
- More patient hold (31.4h average escape)
- But STRICT 40h bailout if stuck <5%ile
- Duration difference is **2.84x** (highly predictive)

---

### **MSFT & GOOGL - Duration NOT Predictive** ⚠️

**MSFT** (49 samples, p=0.650):
- Median time in low: **0h for BOTH winners and losers**
- No statistical significance
- Use OTHER metrics (not duration) for MSFT

**GOOGL** (54 samples, p=0.309):
- Winners: 0h median
- Losers: 20h median
- Still not statistically significant
- Duration alone won't predict GOOGL outcomes

---

## 🎯 4H ENTRY STRATEGY

### **The Sniper Entry Checklist**

**Before Entry:**
1. ✅ Daily timeframe shows <5%ile (using 252-day lookback)
2. ✅ 4H timeframe CONFIRMS <5%ile (using 410-bar = 252-day lookback)
3. ✅ Both use SAME RSI-MA calculation (log returns → delta → RSI → EMA)
4. ✅ Current percentile matches between Daily and 4H tabs

**Entry Timing:**
- **Option 1**: Enter at market open (9:30 AM) if overnight showed <5%ile
- **Option 2**: Enter mid-session (1:30 PM Bar 1) if <5%ile confirmed
- **Best practice**: Wait for Bar 1 close (1:30 PM) to confirm entry

---

## ⏱️ 4H BAR-BY-BAR PLAYBOOK

### **Bar 0 (Entry - 9:30 AM)**
- **Action**: BUY at <5%ile
- **Expected**: Entry price locked in
- **Risk**: None yet (just entered)

### **Bar 1 (4h later - 1:30 PM same day)**
- **Check**: Is percentile still <5%?
- **WINNER SIGNAL**: Already >5%ile! (This is the 0h median pattern!)
- **WARNING**: Still <5%ile (monitor, but don't panic yet)
- **Action**: If >5% already, this is ideal winner pattern

### **Bar 2-3 (8-12h later - Next day morning)**
- **Check**: Building momentum? Percentile climbing?
- **WINNER**: Should be >5-10%ile by now
- **CAUTION**: Still hovering <5%ile = concerning

### **Bar 4-5 (16-20h later - Next day afternoon)** 🚨 **DECISION POINT**
- **Check 1**: Am I in profit?
- **Check 2**: What's the current percentile?

**4 Possible Scenarios:**

| P&L | Percentile | Action | Pattern |
|-----|-----------|--------|---------|
| ✅ Profit | ✅ >5%ile | **HOLD** | ✅ Winner confirmed |
| ✅ Profit | ❌ <5%ile | **EXIT** 🚨 | ⚠️ False signal (loser disguised) |
| ❌ Loss | ✅ >5%ile | **HOLD** | ⚠️ Slow starter (may recover) |
| ❌ Loss | ❌ <5%ile | **EXIT** 🚨 | ❌ Clear loser |

**CRITICAL**: Don't just look at P&L - CHECK PERCENTILE!

### **Bar 6-7 (24-28h later - Day 3 morning)** ⏰ **ESCAPE WINDOW**
- **Expected**: Winners should have escaped by now (27-31h average)
- **Check**: Percentile consistently >5-10%ile?
- **Action**: If still <5%, prepare to exit at Bar 10 (40h)

### **Bar 8-10 (32-40h later - Day 3-4)** 🚨 **DANGER ZONE**
- **WARNING**: Entering loser territory
- **MSFT exception**: Losers median 0h, so less predictive
- **AMZN critical**: Losers median 40h - THIS IS BAILOUT!
- **Action**: If still <5% at 40h, EXIT IMMEDIATELY

### **Bar 12+ (48-56h later - End of tracking window)** ❌ **CONFIRMED LOSER**
- **Conclusion**: If still <5% after 50h, confirmed loser pattern
- **Stats**: You've waited 2-3x longer than winners
- **Action**: EXIT ALL, accept loss

---

## 🎓 RISK MANAGEMENT FRAMEWORK

### **Position Sizing by Bar Count**

| Bar | Hours | Action | Position Size | Risk Level |
|-----|-------|--------|---------------|------------|
| 0 | Entry | FULL | 100% | LOW |
| 1-5 | 4-20h | HOLD | 100% | LOW |
| 5 | 20h | DECISION | 100% or 0% | MODERATE |
| 6-7 | 24-28h | MONITOR | 50-100% | MODERATE |
| 8-10 | 32-40h | REDUCE | 25-50% | HIGH |
| 10+ | 40h+ | EXIT | 0% | CRITICAL |

### **The 3-Tier Exit Strategy**

**Tier 1: Profit-Taking (Winners)**
- Bar 5-7 (20-28h): If >5%ile + profit → Take 25-50%
- Bar 7-9 (28-36h): If >10%ile + 3%+ profit → Take another 25%
- Bar 9-14 (36-56h): Hold remaining for max gain

**Tier 2: Break-Even Stops (Uncertain)**
- Bar 5 (20h): If <5%ile still but small profit → Set break-even stop
- Bar 7 (28h): If <5%ile → EXIT regardless of P&L

**Tier 3: Hard Stops (Losers)**
- Bar 5 (20h): If <5%ile + loss → EXIT 50%
- Bar 10 (40h): If <5%ile → EXIT ALL (no exceptions)
- Bar 12+ (50h+): Should already be out

---

## 📈 THE INTRADAY EDGE

### **Why 4H Beats Daily for Execution**

**Daily Resolution:**
- Entry/Exit signals only at 4:00 PM close
- 24-hour delay to see if pattern is working
- Miss intraday price swings

**4H Resolution (Your Edge):**
- Know if entry is working by **1:30 PM next day** (Bar 1)
- Confirm winner pattern by **Bar 3-5** (12-20h)
- Exit losers **4-24 hours earlier** than daily
- Add to winners at **1:30 PM** instead of waiting for 4 PM

### **Practical Trading Timeline**

**Monday 9:30 AM** - Entry at <5%ile (Bar 0)
- Daily shows: <5%ile from Friday close
- 4H shows: <5%ile confirmed at market open
- **Action**: BUY

**Monday 1:30 PM** - First check (Bar 1)
- Daily shows: Nothing (market still open)
- 4H shows: Percentile update available!
- **Edge**: Know if instant escape pattern (winner signal) **2.5h earlier**

**Tuesday 9:30 AM** - Second check (Bar 2)
- Daily shows: Monday's close may show progress
- 4H shows: Already 2 bars of data!
- **Edge**: See trend building **intraday**

**Tuesday 1:30 PM** - Winner confirmation (Bar 3)
- Daily shows: Still waiting for Tuesday close
- 4H shows: **Escaped >5%ile!** Winner confirmed!
- **Edge**: Add to position **2.5h before daily close**

**Tuesday 4:00 PM** - Daily catches up (Bar 3 close)
- Daily shows: Confirmed escape >5%ile
- 4H shows: Already knew since 1:30 PM
- **Result**: You added 2.5h earlier, already up another 0.5-1%

---

## 🎯 FINAL CHECKLIST

### **Entry Requirements (ALL must be TRUE)**
- [ ] Daily percentile <5%ile (252-day window)
- [ ] 4H percentile <5%ile (410-bar = 252-day window)
- [ ] Both percentiles calculated with same RSI-MA method
- [ ] Stock has 50+ historical samples (avoid low-data tickers)
- [ ] Not MSFT/GOOGL (duration not predictive)

### **Winner Confirmation (Bar 5 - 20h)**
- [ ] Currently in profit (any amount)
- [ ] Current percentile >5%ile
- [ ] Time in low zone <20h
- [ ] Showing sustained climb in percentile rank

### **Exit Signals (MUST EXIT if ANY is TRUE)**
- [ ] Bar 5 (20h): Still <5%ile regardless of P&L
- [ ] Bar 7 (28h): Still <5%ile (missed normal escape window)
- [ ] Bar 10 (40h): Still <5%ile (AMZN critical bailout)
- [ ] Bar 12+ (50h): Still <5%ile (confirmed loser)

---

## 💡 THE GOLDEN RULES

1. **0h Median Rule**: Winners escape IMMEDIATELY (first 4H bar). If not, be cautious.

2. **20h Decision Rule**: At Bar 5 (20h), check percentile + P&L. Exit if still <5%ile.

3. **Percentile > P&L Rule**: Profit means nothing if percentile is still <5% (false signal).

4. **40h Hard Stop Rule**: If still <5%ile after 40h (AMZN loser median), EXIT no matter what.

5. **Instant Escape Pattern**: 50% of winners escape <5% by Bar 1 (4 hours). This is the ideal signal.

6. **3x Duration Rule**: Losers take 3x longer in low zones. Quick escape = winner. Slow grind = loser.

7. **Bar 3-5 Add Rule**: Use 4H to add to winners at 1:30 PM (Bar 3-5), don't wait for 4 PM daily close.

8. **Stock Selection Rule**: Avoid MSFT/GOOGL for duration-based exits (not predictive). Focus on NVDA, AAPL, TSLA, AMZN.

---

## 🚀 SUMMARY: Your 4H Competitive Advantage

**What the 410-bar (252-day) window gives you:**
- ✅ Same time period as daily percentile (apples-to-apples comparison)
- ✅ Consistent percentile values between Daily and 4H tabs
- ✅ Reliable entry signals with proper historical context

**What 4H resolution gives you:**
- ✅ 2-6 hour early winner detection vs daily
- ✅ Intraday exit signals for losers (save 4-24 hours)
- ✅ Position management at 1:30 PM vs 4:00 PM
- ✅ Bar-by-bar progression tracking (not just daily snapshots)

**The killer combo:**
- Enter on Daily <5%ile signal (end of day)
- Manage with 4H bars (intraday precision)
- Exit losers early (before daily shows failure)
- Add to winners early (before daily confirms success)

**Result:** Same entries as daily traders, but 4-24 hour execution edge! 🎯
