# 🎯 Live Market State - WITH MACD-V Percentiles

## Updated Table Structure

Your existing table structure with **NEW COLUMNS** added:

---

### Example: NVDA Row (Updated)

**BEFORE (Your current table):**
```
NVDA | $180.34 | ST-1.2% MP+0.2% | 5.0% | 3.6% | +1.4pp(0.0%) | 5-15% | 45.6% | +1.04% | +0.214%/day | +0.52% | 4.8 | 09/05/25 | n=79 | 10.7 | Ranging | -14.3, -0.0, +1.1 | → FLAT | 15 days | Mean Rev
```

**AFTER (With MACD-V Percentiles):**
```
NVDA | $180.34 | ST-1.2% MP+0.2% | 5.0% | 3.6% | +1.4pp(0.0%) | 5-15% | 45.6% | +1.04% | +0.214%/day | +0.52% | 4.8 | 09/05/25 | n=79 |
  MACD-V: 10.7 | Ranging (-50 to +50) | 59.4% (within zone) | 50.0% (bull/bear) | ➡️ Mid-range |
  Ranging | -14.3, -0.0, +1.1 | → FLAT | 15 days | Mean Rev
```

---

## Complete Live Table with New Columns

| Ticker | Price | MACD-V | **Zone** | **Cat %ile** | **Asym %ile** | **Interpretation** | Current Trend | Regime |
|--------|-------|--------|----------|--------------|---------------|--------------------|--------------|----- ---|
| **SLV** | $76.96 | **74.3** | **Strong Bullish (+50 to +100)** | **38.1%** | **75.0%** | **📉 Weakening** | Bullish | Momentum |
| **MSFT** | $411.21 | **-113.1** | **Extreme Bearish (<-100)** | **16.7%** | **10.0%** | **⚠️ Extreme bearish** | Bearish | Mean Rev |
| **NVDA** | $180.34 | **10.2** | **Ranging (-50 to +50)** | **59.4%** | **50.0%** | **➡️ Mid-range** | Ranging | Mean Rev |
| **BTC-USD** | $76,043.91 | **-126.1** | **Extreme Bearish (<-100)** | **31.2%** | **10.0%** | **↘️ Weakening** | Bearish | Momentum |
| **NFLX** | $79.94 | **-157.6** | **Extreme Bearish (<-100)** | **2.6%** | **10.0%** | **⚠️ Extreme bearish** | Bearish | Momentum |
| **UNH** | $284.18 | **-109.2** | **Extreme Bearish (<-100)** | **85.7%** | **10.0%** | **🔄 High recovery** | Bearish | Momentum |
| **LLY** | $1,003.46 | **-20.9** | **Ranging (-50 to +50)** | **20.4%** | **25.0%** | **📉 Lower range** | Neutral | Momentum |
| **QQQ** | $616.52 | **18.6** | **Ranging (-50 to +50)** | **43.5%** | **50.0%** | **➡️ Mid-range** | Ranging | Mean Rev |
| **NQ=F** | $25,389.75 | **6.5** | **Ranging (-50 to +50)** | **22.4%** | **50.0%** | **📉 Lower range** | Ranging | Mean Rev |
| **SPY** | $689.53 | **37.2** | **Ranging (-50 to +50)** | **61.5%** | **50.0%** | **📈 Upper range** | Neutral | Mean Rev |

---

## Column Definitions

### New Columns (Bold):

1. **Zone** - Market regime with range
   - Extreme Bearish (<-100)
   - Strong Bearish (-100 to -50)
   - **Ranging (-50 to +50)** ← Most common
   - Strong Bullish (+50 to +100)
   - Extreme Bullish (>+100)

2. **Cat %ile** - Categorical Percentile (within the zone)
   - Shows where current value ranks within its zone
   - Example: **59.4%** for NVDA means at 59th percentile within ranging zone
   - **High % in ranging = overbought, low % = oversold**

3. **Asym %ile** - Asymmetric Percentile (within bull/bear regime)
   - Calculated separately for bullish (≥0) vs bearish (<0)
   - Useful for directional comparison

4. **Interpretation** - Quick interpretation
   - ⚠️ Extreme, 🔄 Recovery, 📈 Strengthening, 📉 Weakening, ➡️ Mid-range, 💡 Oversold

---

## Integration Instructions

### Option 1: Use the JSON API
```javascript
// Load from JSON file
fetch('/docs/live_table_macdv_percentiles.json')
  .then(response => response.json())
  .then(data => {
    data.data.forEach(ticker => {
      console.log(`${ticker.Ticker}: ${ticker.Zone_Display} (${ticker.Cat_Percentile}%)`);
    });
  });
```

### Option 2: Use Python Reference Lookup
```python
from macdv_reference_lookup import MACDVReferenceLookup

lookup = MACDVReferenceLookup()

# Get for any ticker
info = lookup.get_ticker_info("NVDA")
curr = info['current_state']

print(f"Zone: {curr['zone']}")  # "ranging"
print(f"Percentile: {curr['categorical_percentile']:.1f}%")  # "59.4%"
```

### Option 3: Direct CSV Import
- File: `docs/live_table_macdv_percentiles.csv`
- Import into your database/spreadsheet
- Join on ticker symbol

---

## Quick Reference

### Ranging Zone (-50 to +50) Interpretation:

| Cat %ile | Interpretation | Action |
|----------|----------------|--------|
| **≥80%** | ⚠️ **Overbought** (near top) | Likely revert DOWN |
| **60-80%** | 📈 Upper range (bullish side) | Watch for reversal |
| **40-60%** | ➡️ Mid-range (neutral) | No strong signal |
| **20-40%** | 📉 Lower range (bearish side) | Watch for reversal |
| **≤20%** | 💡 **Oversold** (near bottom) | Likely revert UP |

### Examples from Current Data:

1. **SPY: 37.2 (Ranging, 61.5%)**
   - 📈 Upper range - bullish side of ranging zone
   - Could be approaching overbought within range

2. **NVDA: 10.2 (Ranging, 59.4%)**
   - ➡️ Mid-range - neutral within ranging zone
   - No strong mean reversion signal yet

3. **LLY: -20.9 (Ranging, 20.4%)**
   - 📉 Lower range - bearish side of ranging zone
   - **Near oversold** - potential for mean revert up

4. **UNH: -109.2 (Extreme Bearish, 85.7%)**
   - 🔄 High recovery - at **85th percentile** within extreme bearish zone
   - Near top of bearish zone = **recovering strongly**

---

## Files Available

### Data Files:
1. **JSON**: `/docs/live_table_macdv_percentiles.json` - For API/JavaScript
2. **CSV**: `/docs/live_table_macdv_percentiles.csv` - For spreadsheets
3. **Markdown**: `/docs/live_table_macdv_percentiles.md` - For documentation
4. **HTML**: `/docs/live_table_macdv_percentiles.html` - For web embedding

### Reference Database:
- **Main DB**: `/docs/macdv_reference_database.json` (95 KB, 31 tickers)
- **Summary**: `/docs/macdv_reference_summary.md`

### Backend Code:
- **Lookup Utility**: `backend/macdv_reference_lookup.py`
- **Integration Script**: `backend/integrate_macdv_percentiles_to_live_table.py`

---

## How to Update

### Daily/Real-time Updates:
```bash
# Regenerate live percentiles for your tickers
python3 backend/integrate_macdv_percentiles_to_live_table.py

# Output files will be updated automatically
```

### Weekly Database Refresh (Optional):
```bash
# Refresh historical reference data (not needed daily)
python3 backend/precompute_macdv_references.py all
```

---

## Key Insights from Current Data

### By Zone Distribution:
- **Ranging (5 tickers)**: NVDA, LLY, QQQ, NQ=F, SPY
  - Most common zone (43.5% of time historically)
  - Mean reversion behavior
  - Watch for percentile extremes (>80% or <20%)

- **Extreme Bearish (4 tickers)**: MSFT, BTC-USD, NFLX, UNH
  - Strong downtrend zone
  - UNH at 85.7% = **high recovery** signal
  - NFLX at 2.6% = **extreme weakness**

- **Strong Bullish (1 ticker)**: SLV
  - Uptrend zone
  - At 38.1% = weakening within uptrend

### Trading Signals:

**Potential Mean Reversion Buys (Ranging zone, low percentile):**
- LLY: 20.4% (lower range, could revert up)
- NQ=F: 22.4% (lower range, could revert up)

**Potential Mean Reversion Sells (Ranging zone, high percentile):**
- SPY: 61.5% (upper range, watch for reversion)
- NVDA: 59.4% (approaching upper range)

**Recovery Plays (Bearish zones, high percentile):**
- UNH: 85.7% (extreme bearish, high recovery signal)

**Avoid (Extreme weakness):**
- NFLX: 2.6% (extreme bearish, at bottom of zone)
- MSFT: 16.7% (extreme bearish, weak)

---

## 🎯 Next Steps

1. **Add the new columns** to your live table using the files provided
2. **Update daily** by running the integration script
3. **Monitor ranging zone percentiles** for mean reversion opportunities
4. **Watch for recovery signals** (high percentiles in bearish zones)

**All files are ready in `/workspaces/New-test-strategy/docs/`!** 🚀
