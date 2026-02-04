## Updated Live Market Table with MACD-V Percentiles

Add these columns to your existing table:

| Ticker | Current MACD-V | Zone | Cat %ile | Asym %ile | Interpretation |
|--------|----------------|------|----------|-----------|----------------|
| SLV | 74.3 | Strong Bullish (+50 to +100) | 38.1% | 75.0% | 📉 Weakening |
| MSFT | -113.1 | Extreme Bearish (<-100) | 16.7% | 10.0% | ⚠️ Extreme bearish |
| NVDA | 10.2 | Ranging (-50 to +50) | 59.4% | 50.0% | ➡️ Mid-range |
| BTC-USD | -126.1 | Extreme Bearish (<-100) | 31.2% | 10.0% | ↘️ Weakening |
| NFLX | -157.6 | Extreme Bearish (<-100) | 2.6% | 10.0% | ⚠️ Extreme bearish |
| UNH | -109.2 | Extreme Bearish (<-100) | 85.7% | 10.0% | 🔄 High recovery |
| LLY | -20.9 | Ranging (-50 to +50) | 20.4% | 25.0% | 📉 Lower range |
| QQQ | 18.6 | Ranging (-50 to +50) | 43.5% | 50.0% | ➡️ Mid-range |
| NQ=F | 6.5 | Ranging (-50 to +50) | 22.4% | 50.0% | 📉 Lower range |
| SPY | 37.2 | Ranging (-50 to +50) | 61.5% | 50.0% | 📈 Upper range |

### Column Explanations

- **Current MACD-V**: Current MACD-V value
- **Zone**: Market regime zone with range
- **Cat %ile**: Categorical percentile (within the zone)
- **Asym %ile**: Asymmetric percentile (within bull/bear regime)
- **Interpretation**: Quick interpretation of the signal

### Interpretation Guide

**Ranging Zone (-50 to +50):**
- ≥80%: ⚠️ Overbought (likely revert down)
- 60-80%: 📈 Upper range (bullish side)
- 40-60%: ➡️ Mid-range (neutral)
- 20-40%: 📉 Lower range (bearish side)
- ≤20%: 💡 Oversold (likely revert up)

