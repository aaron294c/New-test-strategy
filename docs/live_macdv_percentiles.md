# Live MACD-V Percentiles

**Updated:** 2026-02-04 09:09:24

**Total Tickers:** 4

## Complete Table

| Ticker | MACD-V | Zone | Range | Cat %ile | Asym %ile | Interpretation |
|--------|--------|------|-------|----------|-----------|----------------|
| MSFT | -113.08 | Extreme Bearish | < -100 | 33.3% | 0.9% | ↘️ Weakening (33% within extreme_bearish zone) |
| AAPL | -21.86 | Ranging | -50 to +50 | 38.7% | 76.8% | 📉 Lower range (39% - bearish side of range) |
| NVDA | 10.16 | Ranging | -50 to +50 | 58.1% | 7.8% | ➡️ Mid-range (58% - neutral) |
| SPY | 37.18 | Ranging | -50 to +50 | 60.0% | 13.0% | 📈 Upper range (60% - bullish side of range) |

## Understanding the Percentiles

### Categorical Percentile (Cat %ile)
- Calculated **within the current zone** (e.g., within strong_bullish zone)
- Shows relative position within that specific market regime
- Example: 84% in ranging zone = at 84th percentile of ranging values (near top of range)

**In Bearish Zones:**
- High percentile (≥80%) = Near top of zone = Recovering / Less bearish
- Low percentile (≤20%) = Near bottom of zone = Deepening / More bearish

**In Bullish Zones:**
- High percentile (≥80%) = Near top of zone = Strong / More bullish
- Low percentile (≤20%) = Near bottom of zone = Weak / Less bullish

### Asymmetric Percentile (Asym %ile)
- Calculated separately for bullish (≥0) and bearish (<0) regimes
- Shows relative position within the directional regime
- Useful for directional comparison independent of zone

## Zone Definitions

| Zone | Range | Regime | Typical Market Condition |
|------|-------|--------|-------------------------|
| Extreme Bearish | < -100 | Strong Downtrend | Severe selling pressure |
| Strong Bearish | -100 to -50 | Downtrend | Clear downward momentum |
| Ranging | -50 to +50 | Mean Reversion | Consolidation, no clear trend |
| Strong Bullish | +50 to +100 | Uptrend | Clear upward momentum |
| Extreme Bullish | > +100 | Strong Uptrend | Extreme buying pressure |

