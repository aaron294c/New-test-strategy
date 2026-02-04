# MACD-V Percentiles - Quick Reference Card

## TL;DR

**Question:** "Should we include percentiles for MACD-V like RSI-MA?"

**Answer:** ✅ **YES - Use categorical (zone-based) percentiles**

---

## The 3 Methods

| Method | When to Use | Complexity |
|--------|-------------|------------|
| **Categorical** ✅ | Default - respects zone structure | Medium |
| Global | Want simplicity, don't care about regimes | Low |
| Asymmetric | Directional strategies only | High |

---

## Zone Structure (Categorical Method)

```
       > +150  │ ░░ Extreme Bullish (rare)
  +100 to +150 │ ▓▓ Extreme Bullish (5%)
   +50 to +100 │ ██ Strong Bullish (21%)
     0 to  +50 │ ▒▒ Weak Bullish (26%)
   -50 to    0 │ ▒▒ Weak Bearish (17%)
  -100 to  -50 │ ██ Strong Bearish (11%)
  -150 to -100 │ ▓▓ Extreme Bearish (3%)
       < -150  │ ░░ Extreme Bearish (rare)
```

---

## Quick Start

### Import:
```python
from macdv_percentile_calculator import MACDVPercentileCalculator
```

### Calculate:
```python
calc = MACDVPercentileCalculator(percentile_lookback=252)
df = calc.calculate_macdv_with_percentiles(data, method="categorical")
```

### Access:
```python
latest = df.iloc[-1]
print(f"{latest['macdv_val']:.2f} ({latest['macdv_percentile']:.0f}% in {latest['macdv_zone']})")
```

---

## Interpretation Cheat Sheet

### Reading the Signal:

**Format:** `MACD-V = X (Y% in zone_name)`

| Zone | Percentile | Interpretation |
|------|------------|----------------|
| strong_bullish | 80% | Very high momentum in uptrend |
| strong_bullish | 20% | Early-stage strong uptrend |
| weak_bullish | 80% | Approaching breakout to strong |
| weak_bullish | 20% | Weak uptrend, low confidence |
| strong_bearish | 80% | Starting to recover from downtrend |
| strong_bearish | 20% | Deepening downtrend |

---

## Top 3 Bands (Tested on AAPL, NVDA, QQQ)

### #1: Strong Bearish Oversold
```
MACD-V: strong_bearish (70-100%)
RSI-MA: 0-30%
→ Mean: +3.24%, Win: 57%, Sharpe: 0.51
💡 "Bounce from oversold bearish zone"
```

### #2: Strong Bullish Low RSI
```
MACD-V: strong_bullish (60-100%)
RSI-MA: 0-30%
→ Mean: +1.85%, Win: 69%, Sharpe: 0.38
💡 "Buy the dip in uptrend"
```

### #3: Extreme Bullish Overbought
```
MACD-V: extreme_bullish (70-100%)
RSI-MA: 80-100%
→ Mean: +1.54%, Win: 64%, Sharpe: 0.36
💡 "Momentum continues at extremes"
```

---

## API Response

```json
{
  "macdv_val": 75.32,
  "macdv_percentile": 82.5,
  "macdv_zone": "strong_bullish",
  "zone_stats": {
    "strong_bullish": {
      "count": 72,
      "pct_of_total": 19.9,
      "avg_percentile": 52.8
    }
  }
}
```

---

## Common Patterns

### Pattern 1: Zone Entry
```
Before: weak_bullish (75th percentile)
After:  strong_bullish (10th percentile)
→ Just entered strong zone, early signal
```

### Pattern 2: Peak Momentum
```
Current: extreme_bullish (95th percentile)
→ At very high levels, consider profit taking
```

### Pattern 3: Mean Reversion
```
Current: strong_bearish (90th percentile)
→ High within bearish zone = recovering
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `macdv_percentile_calculator.py` | Main implementation |
| `test_macdv_percentiles.py` | Testing/demo script |
| `macdv_rsi_percentile_band_analysis.py` | Integrated analysis |
| `macdv_percentiles_guide.md` | Full documentation |
| `macdv_percentiles_summary.md` | Implementation summary |

---

## Command Line Usage

### Test single ticker:
```bash
python3 test_macdv_percentiles.py AAPL
```

### Run band analysis:
```bash
python3 macdv_rsi_percentile_band_analysis.py "AAPL,NVDA,QQQ"
```

---

## When to Use Each Method

### Use CATEGORICAL if:
- ✅ You care about market regimes
- ✅ You want regime-aware relative positioning
- ✅ You're building multi-dimensional strategies
- ✅ You want to combine absolute + relative info

### Use GLOBAL if:
- ✅ You want simplicity
- ✅ You only care about extreme values
- ✅ You don't need regime-specific analysis

### Use ASYMMETRIC if:
- ✅ You're building directional strategies
- ✅ You want to treat bull/bear differently
- ✅ You need separate percentiles for each direction

---

## Key Insights

### Distribution:
- 94.6% of values within ±150 (confirmed your intuition!)
- Mean = 34.38 (bullish skew in data)
- Median = 34.06

### Performance:
- Best signals combine zone transition + RSI divergence
- Oversold in bearish zones → bounce plays
- Low RSI in bullish zones → dip buying
- Extreme momentum → trend continuation

### Practical Tips:
1. **Zone matters more than absolute value**
   - MACD-V = 25 (80% in weak_bullish) > MACD-V = 30 (20% in weak_bullish)

2. **Combine with RSI-MA percentile**
   - MACD-V percentile → regime strength
   - RSI-MA percentile → overbought/oversold

3. **Watch zone transitions**
   - Crossing into new zone = early signal
   - High percentile in zone = mature signal

---

## Remember

> **Categorical percentiles give you TWO pieces of information:**
> 1. What zone are we in? (absolute level)
> 2. How extreme within that zone? (relative position)
>
> This is more powerful than a single global percentile.

---

## Support

- Full Guide: `docs/macdv_percentiles_guide.md`
- Summary: `docs/macdv_percentiles_summary.md`
- Code: `backend/macdv_percentile_calculator.py`
