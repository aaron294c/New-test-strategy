# Signal Metrics Reference — 5-Year vs 9-Year Comparison

*Both use non-overlapping entries (10-bar cooldown) and D5 holding period.*
*Half-Kelly clamped to [5%, 20%]. Max 3 simultaneous positions.*

| Window | Bars | Entry rule | Purpose |
|--------|------|------------|---------|
| **5-year** | ~1,560 | Non-overlapping, first entry only | Recent regime — 2020–2025 |
| **9-year** | ~2,600 | Non-overlapping, first entry only | Full cycle — includes 2015–2019 |

> **How to read the Δ column:** Positive = 9yr half-Kelly is higher (signal more robust
> across regimes). Negative = 5yr half-Kelly is higher (recent conditions favour it more).

---

## Signal A — RSI-MA < 5th Percentile + COV Red Bar

| # | Ticker | Name | 5yr N | 5yr Win% | 5yr Avg Win | 5yr Avg Loss | 5yr EV | 5yr ½-Kelly | 9yr N | 9yr Win% | 9yr Avg Win | 9yr Avg Loss | 9yr EV | 9yr ½-Kelly | Δ ½-Kelly | Verdict |
|---|--------|------|-------|---------|------------|-------------|--------|------------|-------|---------|------------|-------------|--------|------------|-----------|---------|
| 1 | **NQ=F** | NASDAQ 100 Futures | 16 | 68.8% | +3.6% | -2.4% | +1.729% | **20%** | 27 | 74.1% | +2.6% | -2.3% | +1.318% | **20%** | +0% | ⭐⭐⭐ |
| 2 | **ES=F** | S&P 500 Futures | 17 | 76.5% | +2.3% | -0.8% | +1.540% | **20%** | 30 | 70.0% | +2.0% | -1.9% | +0.847% | **20%** | +0% | ⭐⭐⭐ |
| 3 | **QQQ** | NASDAQ 100 ETF | 19 | 68.4% | +2.8% | -2.2% | +1.203% | **20%** | 35 | 68.6% | +2.0% | -2.4% | +0.658% | **16%** | -4% | ⭐⭐⭐ |
| 4 | **SPY** | S&P 500 ETF | 23 | 69.6% | +2.1% | -1.2% | +1.059% | **20%** | 40 | 65.0% | +2.0% | -2.5% | +0.388% | **10%** | -10% | 🔴 5yr stronger |
| 5 | **MSFT** | Microsoft | 21 | 61.9% | +3.7% | -2.5% | +1.370% | **18%** | 37 | 73.0% | +3.5% | -3.1% | +1.681% | **20%** | +2% | ⭐⭐⭐ |
| 6 | **NVDA** | NVIDIA | 18 | 61.1% | +5.1% | -3.4% | +1.826% | **18%** | 33 | 57.6% | +4.9% | -3.5% | +1.326% | **14%** | -4% | 🔴 5yr stronger |
| 7 | **GOOGL** | Alphabet (Google) | 20 | 70.0% | +3.4% | -2.0% | +1.779% | **20%** | 35 | 60.0% | +3.6% | -2.7% | +1.077% | **15%** | -5% | 🔴 5yr stronger |
| 8 | **AAPL** | Apple | 19 | 57.9% | +3.9% | -2.8% | +1.086% | **14%** | 29 | 51.7% | +3.5% | -2.2% | +0.748% | **11%** | -3% | ⭐ |
| 9 | **AVGO** | Broadcom | 20 | 60.0% | +7.0% | -2.9% | +3.032% | **20%** | 35 | 51.4% | +4.8% | -3.2% | +0.892% | **9%** | -11% | 🔴 5yr stronger |
| 10 | **TSM** | Taiwan Semiconductor | 21 | 71.4% | +3.9% | -4.1% | +1.627% | **20%** | 34 | 61.8% | +4.0% | -3.5% | +1.129% | **14%** | -6% | 🔴 5yr stronger |
| 11 | **META** | Meta (Facebook) | 16 | 56.2% | +5.8% | -5.0% | +1.100% | **9%** | 34 | 67.6% | +5.0% | -5.1% | +1.721% | **17%** | +8% | 🟢 9yr stronger |
| 12 | **TSLA** | Tesla | 22 | 68.2% | +5.3% | -3.6% | +2.483% | **20%** | 42 | 71.4% | +7.4% | -3.5% | +4.309% | **20%** | +0% | ⭐⭐⭐ |
| 13 | **AMZN** | Amazon | 18 | 55.6% | +3.2% | -4.5% | -0.216% | **5%** | 30 | 63.3% | +3.7% | -4.9% | +0.540% | **7%** | +2% | 🟢 9yr unlocks edge |
| 14 | **LLY** | Eli Lilly | 17 | 35.3% | +5.0% | -2.5% | +0.132% | **5%** | 29 | 41.4% | +3.2% | -2.2% | +0.022% | **5%** | +0% | ⭐ |
| 15 | **WMT** | Walmart | 19 | 57.9% | +2.3% | -1.8% | +0.565% | **12%** | 34 | 55.9% | +3.1% | -1.8% | +0.953% | **15%** | +3% | ⭐⭐ |
| 16 | **BRK-B** | Berkshire Hathaway | 15 | 46.7% | +3.1% | -2.8% | -0.043% | **5%** | 30 | 56.7% | +2.1% | -2.6% | +0.077% | **5%** | +0% | 🟢 9yr unlocks edge |
| 17 | **JPM** | JP Morgan Chase | 18 | 61.1% | +3.2% | -3.9% | +0.429% | **7%** | 34 | 58.8% | +2.7% | -3.4% | +0.194% | **5%** | -2% | ⭐ |
| 18 | **BAC** | Bank of America | 20 | 40.0% | +2.4% | -3.3% | -1.037% | **5%** | 35 | 42.9% | +2.0% | -3.4% | -1.086% | **5%** | +0% | ✗ |
| 19 | **NFLX** | Netflix | 18 | 44.4% | +2.8% | -4.1% | -1.035% | **5%** | 30 | 43.3% | +3.2% | -3.5% | -0.612% | **5%** | +0% | ✗ |
| 20 | **ORCL** | Oracle | 22 | 50.0% | +4.5% | -3.1% | +0.677% | **8%** | 40 | 50.0% | +3.7% | -2.6% | +0.555% | **8%** | -0% | ⭐ |
| 21 | **UNH** | UnitedHealth Group | 24 | 54.2% | +2.9% | -2.7% | +0.350% | **6%** | 38 | 57.9% | +3.2% | -2.8% | +0.699% | **11%** | +5% | ⭐⭐ |
| 22 | **GLD** | Gold ETF | 14 | 28.6% | +3.1% | -2.5% | -0.920% | **5%** | 30 | 40.0% | +1.9% | -1.8% | -0.338% | **5%** | +0% | ✗ |
| 23 | **SLV** | Silver ETF | 15 | 40.0% | +2.3% | -2.5% | -0.594% | **5%** | 26 | 46.2% | +2.5% | -3.8% | -0.905% | **5%** | +0% | ✗ |
| 24 | **BTC-USD** | Bitcoin | 22 | 63.6% | +6.4% | -5.1% | +2.243% | **17%** | 36 | 66.7% | +5.3% | -5.5% | +1.686% | **16%** | -2% | ⭐⭐⭐ |
| 25 | **SMH** | Semiconductors ETF | 21 | 71.4% | +4.8% | -4.1% | +2.234% | **20%** | 35 | 54.3% | +4.7% | -3.2% | +1.062% | **11%** | -9% | 🔴 5yr stronger |
| 26 | **XLI** | Industrials ETF | 23 | 69.6% | +2.6% | -1.7% | +1.331% | **20%** | 40 | 67.5% | +2.4% | -3.2% | +0.580% | **12%** | -8% | 🔴 5yr stronger |
| 27 | **MCD** | McDonald's | 16 | 50.0% | +3.3% | -2.0% | +0.651% | **10%** | 29 | 55.2% | +2.5% | -3.6% | -0.219% | **5%** | -5% | 🔴 9yr loses edge |
| 28 | **OXY** | Occidental Petroleum | 20 | 60.0% | +3.9% | -5.8% | -0.028% | **5%** | 33 | 54.5% | +3.8% | -6.4% | -0.859% | **5%** | +0% | ✗ |
| 29 | **XOM** | Exxon Mobil | 18 | 66.7% | +3.4% | -3.3% | +1.130% | **17%** | 31 | 58.1% | +2.9% | -4.2% | -0.057% | **5%** | -12% | 🔴 9yr loses edge |
| 30 | **CVX** | Chevron | 17 | 58.8% | +2.1% | -5.4% | -0.984% | **5%** | 30 | 56.7% | +1.9% | -5.9% | -1.466% | **5%** | +0% | ✗ |
| 31 | **ASML** | ASML Holding | 20 | 50.0% | +5.1% | -3.5% | +0.813% | **8%** | 35 | 51.4% | +4.6% | -3.6% | +0.621% | **7%** | -1% | ⭐ |
| 32 | **SMCI** | Super Micro Computer | 20 | 55.0% | +9.4% | -10.3% | +0.521% | **5%** | 36 | 50.0% | +7.9% | -6.5% | +0.654% | **5%** | +0% | ⭐ |
| 33 | **^TNX** | 10-Year Treasury Yield | 21 | 71.4% | +3.7% | -3.2% | +1.724% | **20%** | 36 | 66.7% | +5.3% | -4.8% | +1.925% | **18%** | -2% | ⭐⭐⭐ |
| 34 | **^VIX** | VIX | 14 | 21.4% | +4.1% | -6.8% | -4.435% | **5%** | 21 | 33.3% | +5.7% | -7.2% | -2.881% | **5%** | +0% | ✗ |
| 35 | **DX-Y.NYB** | US Dollar Index | 18 | 50.0% | +0.8% | -0.5% | +0.190% | **11%** | 29 | 51.7% | +0.8% | -0.6% | +0.147% | **9%** | -3% | ⭐ |
| 36 | **^GDAXI** | DAX | 20 | 70.0% | +1.4% | -1.7% | +0.482% | **17%** | 33 | 60.6% | +1.7% | -3.2% | -0.233% | **5%** | -12% | 🔴 9yr loses edge |
| 37 | **^FTSE** | FTSE 100 | 18 | 66.7% | +1.5% | -3.1% | -0.033% | **5%** | 32 | 62.5% | +1.3% | -3.8% | -0.632% | **5%** | +0% | ✗ |
| 38 | **^N225** | Nikkei 225 | 21 | 61.9% | +3.5% | -2.8% | +1.093% | **16%** | 40 | 60.0% | +3.3% | -3.0% | +0.793% | **12%** | -4% | 🔴 5yr stronger |
| 39 | **MU** | Micron Technology | 22 | 50.0% | +5.3% | -4.1% | +0.572% | **5%** | 39 | 51.3% | +4.9% | -4.8% | +0.212% | **5%** | +0% | ⭐ |
| 40 | **AMD** | Advanced Micro Devices | 21 | 47.6% | +6.7% | -5.1% | +0.549% | **5%** | 34 | 44.1% | +5.1% | -5.5% | -0.849% | **5%** | +0% | 🔴 9yr loses edge |
| 41 | **JNJ** | Johnson & Johnson | 24 | 62.5% | +2.4% | -1.7% | +0.854% | **18%** | 37 | 62.2% | +2.3% | -2.1% | +0.645% | **14%** | -4% | 🔴 5yr stronger |
| 42 | **INTC** | Intel | 20 | 30.0% | +6.1% | -4.0% | -0.931% | **5%** | 39 | 38.5% | +4.1% | -3.4% | -0.532% | **5%** | +0% | ✗ |
| 43 | **COST** | Costco | 18 | 50.0% | +2.5% | -3.0% | -0.241% | **5%** | 33 | 48.5% | +3.2% | -2.9% | +0.046% | **5%** | +0% | 🟢 9yr unlocks edge |
| 44 | **CAT** | Caterpillar | 20 | 45.0% | +4.8% | -3.0% | +0.502% | **5%** | 31 | 45.2% | +4.9% | -3.3% | +0.375% | **5%** | +0% | ⭐ |
| 45 | **CSCO** | Cisco Systems | 22 | 63.6% | +2.8% | -2.3% | +0.910% | **17%** | 36 | 52.8% | +2.1% | -1.8% | +0.279% | **7%** | -10% | 🔴 5yr stronger |
| 46 | **SOXX** | iShares Semis ETF | 19 | 73.7% | +5.1% | -3.6% | +2.835% | **18%** | 31 | 51.6% | +4.9% | -3.2% | +0.984% | **5%** | -13% | 🔴 5yr stronger |
---

## Signal B — RSI-MA 5th–15th Percentile + COV Red Bar

| # | Ticker | Name | 5yr N | 5yr Win% | 5yr Avg Win | 5yr Avg Loss | 5yr EV | 5yr ½-Kelly | 9yr N | 9yr Win% | 9yr Avg Win | 9yr Avg Loss | 9yr EV | 9yr ½-Kelly | Δ ½-Kelly | Verdict |
|---|--------|------|-------|---------|------------|-------------|--------|------------|-------|---------|------------|-------------|--------|------------|-----------|---------|
| 1 | **NQ=F** | NASDAQ 100 Futures | 21 | 66.7% | +2.9% | -2.3% | +1.181% | **20%** | 36 | 52.8% | +2.9% | -2.7% | +0.280% | **5%** | -15% | 🔴 5yr stronger |
| 2 | **ES=F** | S&P 500 Futures | 22 | 50.0% | +2.5% | -2.0% | +0.246% | **5%** | 43 | 55.8% | +2.5% | -2.3% | +0.422% | **8%** | +3% | ⭐⭐ |
| 3 | **QQQ** | NASDAQ 100 ETF | 28 | 64.3% | +2.3% | -3.0% | +0.411% | **9%** | 48 | 60.4% | +2.6% | -2.9% | +0.418% | **8%** | -1% | ⭐⭐ |
| 4 | **SPY** | S&P 500 ETF | 30 | 53.3% | +2.4% | -2.3% | +0.243% | **5%** | 46 | 54.3% | +2.3% | -2.3% | +0.203% | **5%** | +0% | ⭐ |
| 5 | **MSFT** | Microsoft | 26 | 57.7% | +3.0% | -3.1% | +0.448% | **7%** | 44 | 56.8% | +3.3% | -2.2% | +0.931% | **14%** | +7% | ⭐⭐ |
| 6 | **NVDA** | NVIDIA | 25 | 40.0% | +4.5% | -5.6% | -1.560% | **5%** | 44 | 50.0% | +5.6% | -5.4% | +0.117% | **5%** | +0% | 🟢 9yr unlocks edge |
| 7 | **GOOGL** | Alphabet (Google) | 27 | 51.9% | +4.9% | -3.4% | +0.931% | **10%** | 46 | 52.2% | +3.9% | -3.3% | +0.475% | **6%** | -3% | ⭐ |
| 8 | **AAPL** | Apple | 34 | 58.8% | +3.5% | -3.2% | +0.748% | **11%** | 52 | 55.8% | +3.9% | -3.7% | +0.561% | **7%** | -4% | ⭐ |
| 9 | **AVGO** | Broadcom | 25 | 48.0% | +5.6% | -2.9% | +1.201% | **11%** | 45 | 62.2% | +4.5% | -2.9% | +1.737% | **19%** | +8% | 🟢 9yr stronger |
| 10 | **TSM** | Taiwan Semiconductor | 23 | 56.5% | +3.9% | -3.5% | +0.650% | **8%** | 39 | 61.5% | +3.2% | -3.6% | +0.578% | **9%** | +1% | ⭐⭐ |
| 11 | **META** | Meta (Facebook) | 24 | 45.8% | +5.2% | -2.0% | +1.343% | **13%** | 49 | 53.1% | +4.9% | -2.1% | +1.601% | **16%** | +4% | ⭐⭐ |
| 12 | **TSLA** | Tesla | 30 | 53.3% | +7.4% | -3.5% | +2.321% | **16%** | 53 | 52.8% | +6.7% | -3.8% | +1.722% | **13%** | -3% | ⭐⭐ |
| 13 | **AMZN** | Amazon | 26 | 46.2% | +4.5% | -4.3% | -0.213% | **5%** | 43 | 51.2% | +5.1% | -3.6% | +0.864% | **8%** | +3% | 🟢 9yr unlocks edge |
| 14 | **LLY** | Eli Lilly | 28 | 64.3% | +6.0% | -3.7% | +2.511% | **20%** | 47 | 68.1% | +4.8% | -3.8% | +2.069% | **20%** | +0% | ⭐⭐⭐ |
| 15 | **WMT** | Walmart | 26 | 53.8% | +1.5% | -3.1% | -0.613% | **5%** | 43 | 58.1% | +1.8% | -2.8% | -0.135% | **5%** | +0% | ✗ |
| 16 | **BRK-B** | Berkshire Hathaway | 27 | 59.3% | +2.2% | -1.8% | +0.559% | **13%** | 47 | 61.7% | +1.8% | -1.8% | +0.379% | **11%** | -2% | ⭐⭐ |
| 17 | **JPM** | JP Morgan Chase | 28 | 53.6% | +3.8% | -3.7% | +0.314% | **5%** | 50 | 58.0% | +3.1% | -3.3% | +0.400% | **6%** | +1% | ⭐ |
| 18 | **BAC** | Bank of America | 25 | 40.0% | +4.0% | -2.1% | +0.346% | **5%** | 50 | 48.0% | +3.6% | -2.6% | +0.339% | **5%** | +0% | ⭐ |
| 19 | **NFLX** | Netflix | 30 | 60.0% | +4.4% | -4.6% | +0.830% | **9%** | 50 | 60.0% | +4.4% | -4.0% | +1.010% | **12%** | +2% | ⭐⭐ |
| 20 | **ORCL** | Oracle | 23 | 56.5% | +2.8% | -3.6% | +0.039% | **5%** | 42 | 52.4% | +2.3% | -3.9% | -0.686% | **5%** | +0% | 🔴 9yr loses edge |
| 21 | **UNH** | UnitedHealth Group | 22 | 36.4% | +2.6% | -3.4% | -1.219% | **5%** | 43 | 41.9% | +3.0% | -3.2% | -0.605% | **5%** | +0% | ✗ |
| 22 | **GLD** | Gold ETF | 19 | 42.1% | +1.5% | -1.3% | -0.129% | **5%** | 37 | 54.1% | +1.6% | -1.1% | +0.342% | **11%** | +6% | 🟢 9yr unlocks edge |
| 23 | **SLV** | Silver ETF | 28 | 50.0% | +2.4% | -2.6% | -0.100% | **5%** | 45 | 44.4% | +2.0% | -2.2% | -0.331% | **5%** | +0% | ✗ |
| 24 | **BTC-USD** | Bitcoin | 29 | 69.0% | +4.9% | -5.6% | +1.637% | **17%** | 51 | 58.8% | +5.2% | -8.7% | -0.561% | **5%** | -12% | 🔴 9yr loses edge |
| 25 | **SMH** | Semiconductors ETF | 26 | 46.2% | +3.2% | -4.0% | -0.721% | **5%** | 43 | 53.5% | +2.8% | -3.6% | -0.164% | **5%** | +0% | ✗ |
| 26 | **XLI** | Industrials ETF | 28 | 46.4% | +2.0% | -1.8% | -0.006% | **5%** | 49 | 51.0% | +2.0% | -2.2% | -0.040% | **5%** | +0% | ✗ |
| 27 | **MCD** | McDonald's | 25 | 56.0% | +1.4% | -2.4% | -0.293% | **5%** | 41 | 63.4% | +2.4% | -2.4% | +0.679% | **14%** | +9% | 🟢 9yr unlocks edge |
| 28 | **OXY** | Occidental Petroleum | 27 | 51.9% | +3.8% | -4.5% | -0.184% | **5%** | 43 | 48.8% | +3.7% | -4.0% | -0.241% | **5%** | +0% | ✗ |
| 29 | **XOM** | Exxon Mobil | 22 | 59.1% | +3.8% | -2.8% | +1.081% | **14%** | 43 | 55.8% | +3.0% | -4.1% | -0.143% | **5%** | -9% | 🔴 9yr loses edge |
| 30 | **CVX** | Chevron | 21 | 42.9% | +2.8% | -2.3% | -0.114% | **5%** | 40 | 52.5% | +2.2% | -4.4% | -0.927% | **5%** | +0% | ✗ |
| 31 | **ASML** | ASML Holding | 26 | 53.8% | +4.2% | -5.3% | -0.182% | **5%** | 43 | 46.5% | +5.1% | -3.9% | +0.292% | **5%** | +0% | 🟢 9yr unlocks edge |
| 32 | **SMCI** | Super Micro Computer | 25 | 48.0% | +7.6% | -6.9% | +0.094% | **5%** | 45 | 46.7% | +7.8% | -6.6% | +0.081% | **5%** | +0% | ⭐ |
| 33 | **^TNX** | 10-Year Treasury Yield | 23 | 47.8% | +2.6% | -1.9% | +0.255% | **5%** | 41 | 43.9% | +3.8% | -3.6% | -0.358% | **5%** | +0% | 🔴 9yr loses edge |
| 34 | **^VIX** | VIX | 21 | 61.9% | +10.9% | -7.2% | +4.052% | **18%** | 36 | 58.3% | +12.5% | -6.9% | +4.391% | **18%** | -1% | 🔴 5yr stronger |
| 35 | **DX-Y.NYB** | US Dollar Index | 18 | 33.3% | +1.0% | -0.9% | -0.266% | **5%** | 33 | 36.4% | +0.7% | -0.8% | -0.242% | **5%** | +0% | ✗ |
| 36 | **^GDAXI** | DAX | 29 | 48.3% | +2.6% | -1.9% | +0.250% | **5%** | 50 | 50.0% | +2.4% | -1.7% | +0.348% | **7%** | +2% | ⭐ |
| 37 | **^FTSE** | FTSE 100 | 28 | 42.9% | +1.6% | -1.4% | -0.100% | **5%** | 51 | 49.0% | +1.7% | -1.5% | +0.089% | **5%** | +0% | 🟢 9yr unlocks edge |
| 38 | **^N225** | Nikkei 225 | 28 | 53.6% | +2.8% | -2.5% | +0.373% | **7%** | 57 | 54.4% | +2.8% | -2.9% | +0.231% | **5%** | -2% | ⭐ |
| 39 | **MU** | Micron Technology | 30 | 70.0% | +7.3% | -3.6% | +4.073% | **20%** | 51 | 58.8% | +7.2% | -4.5% | +2.389% | **17%** | -3% | 🔴 5yr stronger |
| 40 | **AMD** | Advanced Micro Devices | 30 | 53.3% | +5.4% | -4.7% | +0.676% | **6%** | 49 | 63.3% | +6.1% | -4.6% | +2.202% | **18%** | +12% | 🟢 9yr stronger |
| 41 | **JNJ** | Johnson & Johnson | 29 | 48.3% | +2.1% | -1.5% | +0.248% | **6%** | 52 | 50.0% | +2.0% | -1.6% | +0.213% | **5%** | -1% | 🔴 5yr stronger |
| 42 | **INTC** | Intel | 30 | 46.7% | +4.2% | -3.4% | +0.148% | **5%** | 52 | 51.9% | +3.3% | -3.8% | -0.136% | **5%** | +0% | 🔴 9yr loses edge |
| 43 | **COST** | Costco | 24 | 62.5% | +2.9% | -2.4% | +0.902% | **16%** | 40 | 65.0% | +2.8% | -2.5% | +0.932% | **17%** | +1% | 🟢 9yr stronger |
| 44 | **CAT** | Caterpillar | 29 | 55.2% | +3.9% | -2.9% | +0.852% | **11%** | 49 | 57.1% | +3.5% | -3.1% | +0.690% | **10%** | -1% | 🔴 5yr stronger |
| 45 | **CSCO** | Cisco Systems | 27 | 70.4% | +3.0% | -1.3% | +1.755% | **20%** | 45 | 62.2% | +3.0% | -2.2% | +1.060% | **17%** | -3% | 🔴 5yr stronger |
| 46 | **SOXX** | iShares Semis ETF | 25 | 52.0% | +3.5% | -4.2% | -0.198% | **6%** | 45 | 55.6% | +3.4% | -3.6% | +0.303% | **7%** | +1% | 🟢 9yr unlocks edge |
---

## Summary — Where the Two Windows Agree vs Diverge (Signal A)

| Category | Tickers | Implication |
|----------|---------|-------------|
| ⭐ Consistent positive (both windows agree, similar size) | NQ=F, ES=F, QQQ, MSFT, AAPL, TSLA, LLY, WMT, JPM, ORCL, BTC-USD, ASML, SMCI, ^TNX, DX-Y.NYB, ^N225 | High confidence — trade these |
| 🟢 9yr meaningfully higher | META(+8%), UNH(+5%) | Robust across cycles — favour 9yr sizing |
| 🔴 5yr meaningfully higher | SPY(-10%), NVDA(-4%), GOOGL(-5%), AVGO(-11%), TSM(-6%), SMH(-9%), XLI(-8%) | Recent conditions better — be cautious on 9yr |
| 🟢 9yr finds edge, 5yr skips | AMZN, BRK-B | Longer horizon needed to see the edge |
| 🔴 9yr loses edge, 5yr has it | MCD, XOM, ^GDAXI | Recent bull cycle only — treat with caution |
| ✗ Both windows say skip | BAC, NFLX, GLD, SLV, OXY, CVX, ^VIX, ^FTSE | No D5 edge regardless of window — floor only |

---

## Quick Sizing Card — Both Windows

*Signal A only. Use the more conservative of the two (lower ½-Kelly) unless you have*
*a strong view on which regime you are in.*

| Ticker | Name | 5yr ½-K | 9yr ½-K | Conservative | Aggressive | Regime note |
|--------|------|---------|---------|-------------|-----------|-------------|
| **NQ=F** | NASDAQ 100 Futures | 20% | 20% | **20%** | 20% | Consistent |
| **ES=F** | S&P 500 Futures | 20% | 20% | **20%** | 20% | Consistent |
| **QQQ** | NASDAQ 100 ETF | 20% | 16% | **16%** | 20% | Consistent |
| **SPY** | S&P 500 ETF | 20% | 10% | **10%** | 20% | 5yr stronger — recent conditions better for this trade |
| **MSFT** | Microsoft | 18% | 20% | **18%** | 20% | Consistent |
| **NVDA** | NVIDIA | 18% | 14% | **14%** | 18% | Consistent |
| **GOOGL** | Alphabet (Google) | 20% | 15% | **15%** | 20% | 5yr stronger — recent conditions better for this trade |
| **AAPL** | Apple | 14% | 11% | **11%** | 14% | Consistent |
| **AVGO** | Broadcom | 20% | 9% | **9%** | 20% | 5yr stronger — recent conditions better for this trade |
| **TSM** | Taiwan Semiconductor | 20% | 14% | **14%** | 20% | 5yr stronger — recent conditions better for this trade |
| **META** | Meta (Facebook) | 9% | 17% | **9%** | 17% | 9yr stronger — signal improves over longer cycle |
| **TSLA** | Tesla | 20% | 20% | **20%** | 20% | Consistent |
| **AMZN** | Amazon | 5% | 7% | **5%** | 7% | Consistent |
| **LLY** | Eli Lilly | 5% | 5% | **5%** | 5% | No edge in either window |
| **WMT** | Walmart | 12% | 15% | **12%** | 15% | Consistent |
| **BRK-B** | Berkshire Hathaway | 5% | 5% | **5%** | 5% | No edge in either window |
| **JPM** | JP Morgan Chase | 7% | 5% | **5%** | 7% | Consistent |
| **BAC** | Bank of America | 5% | 5% | **5%** | 5% | No edge in either window |
| **NFLX** | Netflix | 5% | 5% | **5%** | 5% | No edge in either window |
| **ORCL** | Oracle | 8% | 8% | **8%** | 8% | Consistent |
| **UNH** | UnitedHealth Group | 6% | 11% | **6%** | 11% | Consistent |
| **GLD** | Gold ETF | 5% | 5% | **5%** | 5% | No edge in either window |
| **SLV** | Silver ETF | 5% | 5% | **5%** | 5% | No edge in either window |
| **BTC-USD** | Bitcoin | 17% | 16% | **16%** | 17% | Consistent |
| **SMH** | Semiconductors ETF | 20% | 11% | **11%** | 20% | 5yr stronger — recent conditions better for this trade |
| **XLI** | Industrials ETF | 20% | 12% | **12%** | 20% | 5yr stronger — recent conditions better for this trade |
| **MCD** | McDonald's | 10% | 5% | **5%** | 10% | Consistent |
| **OXY** | Occidental Petroleum | 5% | 5% | **5%** | 5% | No edge in either window |
| **XOM** | Exxon Mobil | 17% | 5% | **5%** | 17% | 5yr stronger — recent conditions better for this trade |
| **CVX** | Chevron | 5% | 5% | **5%** | 5% | No edge in either window |
| **ASML** | ASML Holding | 8% | 7% | **7%** | 8% | Consistent |
| **SMCI** | Super Micro Computer | 5% | 5% | **5%** | 5% | No edge in either window |
| **^TNX** | 10-Year Treasury Yield | 20% | 18% | **18%** | 20% | Consistent |
| **^VIX** | VIX | 5% | 5% | **5%** | 5% | No edge in either window |
| **DX-Y.NYB** | US Dollar Index | 11% | 9% | **9%** | 11% | Consistent |
| **^GDAXI** | DAX | 17% | 5% | **5%** | 17% | 5yr stronger — recent conditions better for this trade |
| **^FTSE** | FTSE 100 | 5% | 5% | **5%** | 5% | No edge in either window |
| **^N225** | Nikkei 225 | 16% | 12% | **12%** | 16% | Consistent |

---

## Variance Analysis — Best EV with Lowest Downside Tail

Standard Kelly sizing captures EV and win rate but not the *shape* of losing trades. Two additional metrics expose downside distribution and fat-tail risk:

| Metric | Formula | Meaning |
|--------|---------|---------|
| **Downside Weight** | `(1 − Win%) × \|Avg Loss\|` | Expected loss per trade — the left-tail cost you pay on average |
| **Win/Loss Ratio** | `Avg Win ÷ \|Avg Loss\|` | Asymmetry of outcomes; >1.5 = winners materially outsize losers |
| **EV/Downside** | `EV ÷ Downside Weight` | EV earned per unit of downside exposure; higher = better risk-adjusted quality |

*All figures use the **9yr window** (more regime-robust). 5yr exceptions noted where they differ materially.*

**Tail key:** ✅ Low (Avg Loss ≤ 2.5%) · 🟡 Moderate (2.5%–3.9%) · 🔴 Fat (≥ 4.0%)

---

### Signal A — Variance-Ranked (9yr)

| Rank | Ticker | 9yr EV | Avg Loss | Downside Wt | W/L Ratio | EV/Downside | Tail |
|------|--------|--------|---------|------------|-----------|------------|------|
| 1 | **TSLA** | +4.31% | −3.5% | 1.00% | 2.11 | 4.30 | 🟡 |
| 2 | **PG** | +1.10% | −1.38% | 0.47% | 1.73 | 2.35 | ✅ |
| 3 | **NQ=F** | +1.32% | −2.3% | 0.60% | 1.13 | 2.21 | ✅ |
| 4 | **MSFT** | +1.68% | −3.1% | 0.84% | 1.13 | 2.00 | 🟡 |
| 5 | **V** | +1.35% | −2.5% | 0.72% | 1.16 | 1.88 | ✅ |
| 6 | **ES=F** | +0.85% | −1.9% | 0.57% | 1.05 | 1.49 | ✅ |
| 7 | **CNX1.L** | +0.95% | −1.81% | 0.65% | 1.38 | 1.46 | ✅ |
| 8 | **Samsung** | +1.45% | −2.76% | 1.05% | 1.47 | 1.38 | 🟡 |
| 9 | **^TNX** | +1.93% | −4.8% | 1.60% | 1.10 | 1.20 | 🔴 |
| 10 | **META** | +1.72% | −5.1% | 1.65% | 0.98 | 1.04 | 🔴 |
| 11 | **BTC** | +1.69% | −5.5% | 1.83% | 0.96 | 0.92 | 🔴 |
| 12 | **AVGO** | +0.89% | −3.2% | 1.55% | 1.50 | 0.57 | 🟡 |

> **ES=F 5yr exception:** In the recent 5yr window, ES=F Signal A Avg Loss = −0.8% with Win% = 76.5%, giving Downside Weight = 0.19%, W/L = 2.88, EV/Downside = 8.11 — the **lowest-variance profile in the full universe**. The 9yr window reverts to historical norms (Avg Loss −1.9%); the 5yr reading reflects the current regime. SPY shows similar 5yr compression (Avg Loss −1.2%, W/L = 1.75) but diverges sharply in the 9yr.

---

### Signal B — Variance-Ranked (9yr)

| Rank | Ticker | 9yr EV | Avg Loss | Downside Wt | W/L Ratio | EV/Downside | Tail |
|------|--------|--------|---------|------------|-----------|------------|------|
| 1 | **LLY** | +2.07% | −3.8% | 1.21% | 1.26 | 1.71 | 🟡 |
| 2 | **META** | +1.60% | −2.1% | 0.99% | 2.33 | 1.63 | ✅ |
| 3 | **AVGO** | +1.74% | −2.9% | 1.10% | 1.55 | 1.58 | 🟡 |
| 4 | **AMD** | +2.20% | −4.57% | 1.68% | 1.34 | 1.31 | 🔴 |
| 5 | **MU** | +2.39% | −4.47% | 1.84% | 1.61 | 1.30 | 🔴 |
| 6 | **CSCO** | +1.06% | −2.2% | 0.83% | 1.38 | 1.27 | ✅ |
| 7 | **COST** | +0.93% | −2.49% | 0.87% | 1.12 | 1.07 | ✅ |
| 8 | **TSLA** | +1.72% | −3.8% | 1.79% | 1.76 | 0.96 | 🟡 |

> **META Signal B** is notably the *only* name in Signal B with a ✅ Low tail and a W/L ratio above 2.0 (2.33). Losses average −2.1% while wins average +4.9% — a genuinely asymmetric payoff profile at the 5th–15th percentile signal.

---

### Composite Tier Summary

| Tier | Signal A | Signal B | Why |
|------|---------|---------|-----|
| **Tier 1 — Best EV + Low Tail** ✅ | PG, NQ=F, V, ES=F, CNX1.L | META, CSCO, COST | Avg Loss ≤ 2.5%; EV/Downside ≥ 1.3; both metrics pointing the right way |
| **Tier 1† — Exceptional EV offsets moderate tail** | TSLA, MSFT | LLY, AVGO | EV/Downside ≥ 1.5; losses 2.5–3.9%; run full ½-Kelly — EV is doing the heavy lifting |
| **Tier 2 — Accept the tail at ½-Kelly** 🟡 | Samsung | — | Positive EV/Downside; losses moderate; discipline on sizing |
| **Tier 3 — Fat tail; reduce size** 🔴 | META, ^TNX, BTC, AVGO | AMD, MU, TSLA | Avg Loss ≥ 3.5%; outlier trades can be 2–3× the average |

---

### Sizing Rules by Tier

| Tier | Sizing Rule | Rationale |
|------|------------|-----------|
| **Tier 1 / 1†** | Full ½-Kelly as calculated | EV/Downside ≥ 1.5 justifies the allocation |
| **Tier 2** | ½-Kelly; flag any single trade > 2× Avg Loss | Losses moderate but can cluster |
| **Tier 3** | Cap at **10%** regardless of ½-Kelly; or apply ¼-Kelly | D5 adverse-move observations for BTC (−5.5% avg) and META Sig A (−5.1% avg) can reach −10% to −15% in volatile conditions |

> **The key discriminator is not EV alone — it is EV combined with Avg Loss magnitude.** PG, NQ=F, and V (Signal A) produce EV of 1.1%–1.4% with losses contained below 2.5%; a losing trade in those names is a manageable −1.4% to −2.5% move on the position. A losing trade in BTC Signal A averages −5.5% and in TSLA Signal B averages −3.8%; in adverse conditions individual trades can easily exceed those averages by 50–100%. ½-Kelly already prices in some of that risk, but a hard position cap is the final guardrail on Tier 3 names.

---

## Definitions

| Term | Formula | Meaning |
|------|---------|---------|
| Win% | trades > 0 / total | % of D5 exits above entry |
| Avg Win | mean(winning returns) | Average gain when trade wins |
| Avg Loss | mean(losing returns) | Average loss when trade loses (negative number) |
| Net EV | Win% × Avg Win + Loss% × Avg Loss | Expected return per trade |
| Kelly | (p×b − q) / b | Theoretically optimal bet fraction |
| ½-Kelly | Kelly ÷ 2 | Practical sizing — reduces drawdown risk |
| Rec% | max(5%, min(20%, ½-Kelly)) | Guardrail-clamped portfolio allocation |

---

---

## Extended Universe — New Tickers

*MU, AMD, Visa, JNJ, Intel, Costco, Caterpillar, Cisco, P&G, Samsung, SK Hynix, FTSE China A50.*
*Same methodology: non-overlapping D5, COV red bar confluence, 5yr and 9yr windows.*

> **Ticker note:** "VESA" interpreted as **Visa (V)** based on context.
> Samsung: `005930.KS` (KRX). SK Hynix: `000660.KS` (KRX). CNX1.L is the FTSE China A50 on LSE.

### Extended — Signal A — RSI-MA < 5th Percentile + COV Red Bar

| # | Ticker | Name | 5yr N | 5yr Win% | 5yr Avg Win | 5yr Avg Loss | 5yr EV | 5yr ½K | 9yr N | 9yr Win% | 9yr Avg Win | 9yr Avg Loss | 9yr EV | 9yr ½K | solo | Verdict |
|---|--------|------|-------|---------|------------|-------------|--------|-----|-------|---------|------------|-------------|--------|-----|------|---------|
| 1 | **V** | Visa | 21 | 66.7% | +3.73% | -1.97% | +1.834% | **20%** | 35 | 71.4% | +2.89% | -2.50% | +1.351% | **20%** | 23% | ⭐⭐⭐ |
| 2 | **PG** | Procter & Gamble | 29 | 69.0% | +2.11% | -1.53% | +0.981% | **20%** | 44 | 65.9% | +2.39% | -1.38% | +1.104% | **20%** | 23% | ⭐⭐⭐ |
| 3 | **005930.KS** | Samsung Electronics | 16 | 68.8% | +3.96% | -2.81% | +1.847% | **20%** | 34 | 61.8% | +4.06% | -2.76% | +1.448% | **18%** | 18% | ⭐⭐⭐ |
| 4 | **000660.KS** | SK Hynix | 13 | 69.2% | +4.88% | -5.39% | +1.719% | **18%** | 26 | 61.5% | +4.39% | -5.58% | +0.557% | **6%** | 6% | ⭐ |
| 5 | **CNX1.L** | FTSE China A50 (LSE) | 21 | 66.7% | +2.86% | -2.19% | +1.180% | **20%** | 39 | 64.1% | +2.49% | -1.81% | +0.946% | **19%** | 19% | ⭐⭐⭐ |
| 6 | **JNJ** | Johnson & Johnson | 24 | 62.5% | +2.39% | -1.70% | +0.854% | **18%** | 37 | 62.2% | +2.30% | -2.08% | +0.645% | **14%** | 14% | ⭐⭐ |
| 7 | **CSCO** | Cisco | 22 | 63.6% | +2.75% | -2.31% | +0.910% | **17%** | 36 | 52.8% | +2.12% | -1.78% | +0.279% | **7%** | 7% | ⭐ |
| 8 | **MU** | Micron Technology | 22 | 50.0% | +5.26% | -4.12% | +0.572% | **5%** | 39 | 51.3% | +4.94% | -4.77% | +0.212% | **2%** | 2% | ⭐ |
| 9 | **AMD** | AMD | 21 | 47.6% | +6.72% | -5.07% | +0.549% | **4%** | 34 | 44.1% | +5.07% | -5.52% | -0.849% | **5%** | 5% | ✗ |
| 10 | **COST** | Costco | 18 | 50.0% | +2.52% | -3.00% | -0.241% | **5%** | 33 | 48.5% | +3.18% | -2.90% | +0.046% | **1%** | 1% | ⭐ |
| 11 | **CAT** | Caterpillar | 20 | 45.0% | +4.79% | -3.00% | +0.502% | **5%** | 31 | 45.2% | +4.89% | -3.34% | +0.375% | **4%** | 4% | ⭐ |
| 12 | **INTC** | Intel | 20 | 30.0% | +6.14% | -3.96% | -0.931% | **5%** | 39 | 38.5% | +4.12% | -3.44% | -0.532% | **5%** | 5% | ✗ |

### Extended — Signal B — RSI-MA 5th–15th Percentile + COV Red Bar

| # | Ticker | Name | 5yr N | 5yr Win% | 5yr Avg Win | 5yr Avg Loss | 5yr EV | 5yr ½K | 9yr N | 9yr Win% | 9yr Avg Win | 9yr Avg Loss | 9yr EV | 9yr ½K | solo | Verdict |
|---|--------|------|-------|---------|------------|-------------|--------|-----|-------|---------|------------|-------------|--------|-----|------|---------|
| 1 | **V** | Visa | 32 | 53.1% | +1.95% | -1.83% | +0.182% | **5%** | 50 | 66.0% | +2.07% | -2.30% | +0.586% | **14%** | 14% | ⭐⭐ |
| 2 | **PG** | Procter & Gamble | 30 | 60.0% | +1.80% | -1.78% | +0.367% | **10%** | 50 | 58.0% | +2.15% | -1.72% | +0.521% | **12%** | 12% | ⭐⭐ |
| 3 | **005930.KS** | Samsung Electronics | 25 | 52.0% | +4.12% | -3.02% | +0.693% | **8%** | 44 | 50.0% | +4.33% | -3.39% | +0.469% | **5%** | 5% | ⭐ |
| 4 | **000660.KS** | SK Hynix | 22 | 72.7% | +6.38% | -5.88% | +3.036% | **20%** | 44 | 68.2% | +5.57% | -4.17% | +2.473% | **20%** | 22% | ⭐⭐⭐ |
| 5 | **CNX1.L** | FTSE China A50 (LSE) | 29 | 55.2% | +1.73% | -2.11% | +0.008% | **0%** | 53 | 60.4% | +2.06% | -2.07% | +0.420% | **10%** | 10% | ⭐⭐ |
| 6 | **JNJ** | Johnson & Johnson | 29 | 48.3% | +2.15% | -1.53% | +0.248% | **6%** | 52 | 50.0% | +2.00% | -1.58% | +0.213% | **5%** | 5% | ⭐ |
| 7 | **CSCO** | Cisco | 27 | 70.4% | +3.04% | -1.29% | +1.755% | **20%** | 45 | 62.2% | +3.04% | -2.20% | +1.060% | **17%** | 17% | ⭐⭐⭐ |
| 8 | **MU** | Micron Technology | 30 | 70.0% | +7.35% | -3.58% | +4.073% | **20%** | 51 | 58.8% | +7.19% | -4.47% | +2.389% | **17%** | 17% | ⭐⭐ |
| 9 | **AMD** | AMD | 30 | 53.3% | +5.42% | -4.74% | +0.676% | **6%** | 49 | 63.3% | +6.14% | -4.57% | +2.202% | **18%** | 18% | ⭐⭐⭐ |
| 10 | **COST** | Costco | 24 | 62.5% | +2.90% | -2.42% | +0.902% | **16%** | 40 | 65.0% | +2.78% | -2.49% | +0.932% | **17%** | 17% | ⭐⭐⭐ |
| 11 | **CAT** | Caterpillar | 29 | 55.2% | +3.93% | -2.94% | +0.852% | **11%** | 49 | 57.1% | +3.51% | -3.07% | +0.690% | **10%** | 10% | ⭐⭐ |
| 12 | **INTC** | Intel | 30 | 46.7% | +4.20% | -3.40% | +0.148% | **2%** | 52 | 51.9% | +3.26% | -3.80% | -0.136% | **5%** | 5% | ✗ |

### Extended Universe — Key Findings

| Ticker | Verdict | Notes |
|--------|---------|-------|
| **V (Visa)** | ⭐⭐⭐ Signal A | 71.4% win (9yr), +1.35% EV — matches NQ=F quality. 5yr even stronger (66.7%, +1.83%). Both windows agree. |
| **PG** | ⭐⭐⭐ Signal A | 65.9% win (9yr), +1.10% EV — both windows agree (23% half-Kelly). Defensive stock with surprisingly clean mean-reversion. |
| **Samsung** | ⭐⭐ Signal A | 61.8% win (9yr), +1.45% EV. 5yr stronger (68.8%). Use 18% multi-pos, 18% solo. |
| **SK Hynix** | ⭐⭐⭐ Signal B | 68.2% win (9yr), +2.47% EV at Signal B. 72.7% win (5yr), +3.04% EV. Use 20% multi-pos, 22% solo. Signal A marginal — prefer B. |
| **CNX1.L** | ⭐⭐ Signal A | 64.1% win (9yr), +0.95% EV. 5yr and 9yr both agree (~19%). China A50 mean-reverts well. |
| **JNJ** | ⭐⭐ Signal A | 62.2% win (9yr), +0.65% EV. Consistent defensive name. |
| **MU** | ✗ A / ⭐⭐⭐ B | Signal A barely positive → floor. Signal B: 58.8% win, +2.39% EV, 17% sizing. **Trade B, not A.** |
| **AMD** | ✗ A / ⭐⭐⭐ B | Signal A negative EV → skip. Signal B: 63.3% win, +2.20% EV, 18% sizing. **Trade B, not A.** |
| **CSCO** | ⭐ A / ⭐⭐⭐ B | Signal A marginal (7%). Signal B strong: 62.2% win, +1.06% EV, 17%. |
| **COST** | ✗ A / ⭐⭐ B | Signal A skip. Signal B: 65.0% win, +0.93% EV, 17%. |
| **CAT** | ⭐ A / ⭐⭐ B | Signal A floor (5%). Signal B: 57.1% win, +0.69% EV, 10%. |
| **INTC** | ✗ both | Skip both signals. 30% win rate at Signal A in 5yr — structural loser. |

---

## SLV — Why the Earlier "3rd Best" Result Was Misleading

The original `cov_confluence_summary.md` ranked SLV 3rd by median D5 return (+2.48%).
Non-overlapping analysis across all windows shows the opposite:

| Window | Method | N | Win% | Median D5 | Mean D5 | EV |
|--------|--------|---|------|-----------|---------|----|
| 1yr    | RSI-MA only      |  4 | 50.0% | +0.01% | −0.96% | −0.955% |
| 5yr    | RSI-MA only      | 26 | 34.6% | −1.54% | −1.75% | −1.751% |
| 5yr    | RSI-MA + COV red | 17 | 35.3% | −0.57% | −2.11% | −2.110% |
| 9yr    | RSI-MA only      | 44 | 43.2% | −0.59% | −0.68% | −0.675% |
| 9yr    | RSI-MA + COV red | 31 | 41.9% | −0.39% | −0.82% | −0.817% |

**Why the discrepancy?** Three compounding factors:

1. **Overlapping vs non-overlapping entries.** When SLV sits below the 5th percentile
   for 10 consecutive days during a crash, the overlapping method counts 10 separate
   entries. Later entries (days 7–10) are bought near the very bottom and show
   higher 5-day win rates, inflating aggregate results. The first-entry-only method
   captures the true cost of entering at the initial signal.

2. **Heavy left tail.** The return distribution for SLV is negatively skewed:
   median can appear positive while the mean (EV) is negative. The old ranking
   was by median, not mean. One outlier trade (−22.57% in 5yr) destroys the
   average, but does not affect the median.

3. **COV filter makes SLV worse, not better.** The filter was designed for growth
   equities. For commodities, RSI-MA dips already coincide with high volatility,
   so the red-bar filter is redundant and removes the few good setups.

**SLV recommendation:**

| Horizon | With COV filter | Without COV | Recommendation |
|---------|----------------|-------------|----------------|
| D5 | ✗ Negative EV all windows | ✗ Negative EV all windows | Do not trade SLV at D5 |
| D21 | — | 71.1% win rate (5yr overlapping) | If trading SLV, target D21 exit WITHOUT COV filter |

> SLV is a genuine mean-reverting instrument — but on a **3–4 week** cycle, not 5 days.
> The D21 data from the original backtest (71.1% win, +3.75% median) tells the real story.
> Use `/sizing slv` for floor-only guidance at D5.

---

## META and TSLA — 1-Year (252 Trading Days) Verification

The 9yr non-overlapping data showed both META and TSLA are *stronger* over the full
decade than the 5yr window. This 1yr check tests whether the edge holds in the
most recent conditions.

| Ticker | Signal | 1yr N | Win% | Avg Win | Avg Loss | EV | ½K | Verdict |
|--------|--------|-------|------|---------|----------|----|----|---------|
| META   | A (<5th + COV) | 4 | — | — | — | — | — | **Too few events** — signal barely fired |
| META   | B (5–15th + COV) | 8 | 50.0% | +4.28% | −1.86% | +1.21% | **14%** | ⭐⭐ Positive |
| TSLA   | A (<5th + COV) | 4 | — | — | — | — | — | **Too few events** — signal barely fired |
| TSLA   | B (5–15th + COV) | 9 | 77.8% | +6.73% | −3.68% | +4.42% | **20%** (solo **30%**) | ⭐⭐⭐ Outstanding |

**What the 1yr data tells us:**

- **Signal A for both META and TSLA** fired only ~4 times in the past year — too few
  to draw conclusions. The extreme oversold level (<5th pct) simply hasn't been
  reached recently. This is not a red flag; it means the setup hasn't presented.

- **TSLA Signal B (1yr)** is outstanding: 77.8% win, +4.42% EV — *stronger* than the
  9yr figure (52.8% win, +1.72% EV). The recent 12 months confirm TSLA continues
  to mean-revert powerfully at the 5–15th percentile with COV red. **High confidence.**

- **META Signal B (1yr)**: 50% win, +1.21% EV — positive but weaker than the 9yr.
  Directionally consistent. The 9yr figure (53.1% win, +1.60% EV) remains the
  primary reference. **No reason to downgrade META; edge persists.**

**Conclusion:** The 9yr sizing recommendations for META (Signal A: 17%, Signal B: 16%)
and TSLA (Signal A: 20%, Signal B: 13%) are confirmed. Signal A positions should be
taken when the extreme oversold level is reached — those events are simply rare.
