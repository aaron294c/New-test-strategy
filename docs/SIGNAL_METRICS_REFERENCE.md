# Signal Metrics Reference — 5-Year vs 9-Year Comparison

*Both use non-overlapping entries (10-bar cooldown) and D5 holding period.*
*Half-Kelly clamped to [5%, 20%]. Max 3 simultaneous positions.*

> **🔄 /value data maintenance — update after earnings.** The `/value` fundamentals
> snapshot is precomputed from yfinance. After each earnings season (or whenever a
> covered name reports), refresh it with:
> ```
> python scripts/compute_value_snapshot.py
> ```
> This rewrites `backend/static_snapshots/fundamentals/value.json`, which the `/value`
> command reads. (`/mr` and `/sortino` read this doc live — no refresh needed.)

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
| 12 | **NVDA** | +1.33% | −3.5% | 1.48% | 1.40 | 0.89 | 🟡 |
| 13 | **AVGO** | +0.89% | −3.2% | 1.55% | 1.50 | 0.57 | 🟡 |

> **ES=F 5yr exception:** In the recent 5yr window, ES=F Signal A Avg Loss = −0.8% with Win% = 76.5%, giving Downside Weight = 0.19%, W/L = 2.88, EV/Downside = 8.11 — the **lowest-variance profile in the full universe**. The 9yr window reverts to historical norms (Avg Loss −1.9%); the 5yr reading reflects the current regime. SPY shows similar 5yr compression (Avg Loss −1.2%, W/L = 1.75) but diverges sharply in the 9yr.

---

### Signal B — Variance-Ranked (9yr)

| Rank | Ticker | 9yr EV | Avg Loss | Downside Wt | W/L Ratio | EV/Downside | Tail |
|------|--------|--------|---------|------------|-----------|------------|------|
| 1 | **SK Hynix** | +2.47% | −4.17% | 1.33% | 1.34 | 1.87 | 🔴 |
| 2 | **LLY** | +2.07% | −3.8% | 1.21% | 1.26 | 1.71 | 🟡 |
| 3 | **META** | +1.60% | −2.1% | 0.99% | 2.33 | 1.63 | ✅ |
| 4 | **AVGO** | +1.74% | −2.9% | 1.10% | 1.55 | 1.58 | 🟡 |
| 5 | **AMD** | +2.20% | −4.57% | 1.68% | 1.34 | 1.31 | 🔴 |
| 6 | **MU** | +2.39% | −4.47% | 1.84% | 1.61 | 1.30 | 🔴 |
| 7 | **CSCO** | +1.06% | −2.2% | 0.83% | 1.38 | 1.27 | ✅ |
| 8 | **COST** | +0.93% | −2.49% | 0.87% | 1.12 | 1.07 | ✅ |
| 9 | **TSLA** | +1.72% | −3.8% | 1.79% | 1.76 | 0.96 | 🟡 |

> **SK Hynix Signal B** ranks first by EV/Downside (1.87) despite a fat tail (Avg Loss −4.17%). EV of +2.47% more than compensates; treat as Tier 1† but do not exceed the 20% ½-Kelly cap — the 2% budget is exactly at the boundary. **META Signal B** remains the *only* name with a ✅ Low tail and W/L above 2.0 (2.33) — losses average −2.1%, wins +4.9% — a genuinely asymmetric payoff profile.

---

### Composite Tier Summary

| Tier | Signal A | Signal B | Why |
|------|---------|---------|-----|
| **Tier 1 — Best EV + Low Tail** ✅ | PG, NQ=F, V, ES=F, CNX1.L | META, CSCO, COST | Avg Loss ≤ 2.5%; EV/Downside ≥ 1.3; both metrics pointing the right way |
| **Tier 1† — Exceptional EV offsets moderate/fat tail** | TSLA, MSFT | LLY, AVGO, SK Hynix† | EV/Downside ≥ 1.5; losses 2.5–3.9% (or fat for SK Hynix); run full ½-Kelly |
| **Tier 2 — Accept the tail at ½-Kelly** 🟡 | Samsung, NVDA | — | Positive EV/Downside (0.5–1.3); losses moderate; maintain discipline on sizing |
| **Tier 3 — Fat tail; reduce size** 🔴 | META, ^TNX, BTC, AVGO | AMD, MU, TSLA | Avg Loss ≥ 3.5%; outlier trades can be 2–3× the average |

> †SK Hynix Signal B: Avg Loss = −4.17% (fat tail, 🔴) but EV/Downside = 1.87 — highest in Signal B. Placed in Tier 1† because EV fully compensates the tail risk. Do not exceed 20%; the 2% loss budget is exactly at the boundary.

---

### Sizing Rules by Tier

| Tier | Sizing Rule | Rationale |
|------|------------|-----------|
| **Tier 1 / 1†** | Full ½-Kelly as calculated | EV/Downside ≥ 1.5 justifies the allocation |
| **Tier 2** | ½-Kelly; flag any single trade > 2× Avg Loss | Losses moderate but can cluster |
| **Tier 3** | Cap at **10%** regardless of ½-Kelly; or apply ¼-Kelly | D5 adverse-move observations for BTC (−5.5% avg) and META Sig A (−5.1% avg) can reach −10% to −15% in volatile conditions |

> **The key discriminator is not EV alone — it is EV combined with Avg Loss magnitude.** PG, NQ=F, and V (Signal A) produce EV of 1.1%–1.4% with losses contained below 2.5%; a losing trade in those names is a manageable −1.4% to −2.5% move on the position. A losing trade in BTC Signal A averages −5.5% and in TSLA Signal B averages −3.8%; in adverse conditions individual trades can easily exceed those averages by 50–100%. ½-Kelly already prices in some of that risk, but a hard position cap is the final guardrail on Tier 3 names.

---

## Downside Deviation Batches — EV-Ranked Sizing

Kelly and ½-Kelly price in the **average** loss. They do not capture the *spread* of losing outcomes. Two signals can share the same average loss yet have very different tail widths. Downside semi-deviation fills this gap: it estimates the standard deviation of losing trades only, producing a realistic per-trade worst-case to size against.

### Method

| Input | Formula | Note |
|-------|---------|------|
| **σ_down** (semi-deviation est.) | \|Avg Loss\| × k | k = 0.50 ✅ · 0.65 🟡 · 0.85 🔴 |
| **95th-pct adverse move** | \|Avg Loss\| + 1.65 × σ_down | One-in-20 losing trade |
| **Max size — 2% budget** | 2% ÷ 95th-pct adverse move | For 1–3 concurrent positions |
| **Max size — 3% budget** | 3% ÷ 95th-pct adverse move | Max-3-position book, low correlation |

*k multipliers reflect empirical equity return distributions: low-tail losses cluster tightly around their average; fat-tail losses show 80–100% dispersion relative to the mean. Cap = 20% in all cases. All figures use the 9yr window unless noted.*

---

### Batch 1 — EV ≥ 3.0%

| Ticker | Sig | 9yr EV | Avg Loss | Tail | σ_down | 95th-pct | Max (2%) | Max (3%) | ½-Kelly | Action |
|--------|-----|--------|----------|------|--------|----------|---------|---------|---------|--------|
| **TSLA** | A | +4.31% | −3.5% | 🟡 | 2.28% | 7.26% | 27.6% → **20%** | 41.3% → **20%** | **20%** | Full ½-Kelly |

TSLA Signal A has the highest EV/Downside ratio in the universe (4.30). At a 20% position, a 95th-pct adverse trade costs −1.45% of portfolio — well inside the 2% budget. Run full ½-Kelly. Note: the 1yr verification shows TSLA Signal B approaching similar territory (77.8% win, +4.42% EV), confirming ongoing mean-reversion strength.

---

### Batch 2 — EV 2.0%–2.99%

| Ticker | Sig | 9yr EV | Avg Loss | Tail | σ_down | 95th-pct | Max (2%) | Max (3%) | ½-Kelly | Action |
|--------|-----|--------|----------|------|--------|----------|---------|---------|---------|--------|
| **SK Hynix** | B | +2.47% | −4.17% | 🔴 | 3.54% | 10.01% | **20.0%** | 30.0% → **20%** | **20%** | At limit — do not exceed |
| **MU** | B | +2.39% | −4.47% | 🔴 | 3.80% | 10.74% | **18.6%** | 27.9% → **20%** | **17%** | ½-Kelly (17%) is binding |
| **AMD** | B | +2.20% | −4.57% | 🔴 | 3.88% | 10.98% | **18.2%** | 27.3% → **20%** | **18%** | Use 18% — both methods agree |
| **LLY** | B | +2.07% | −3.8% | 🟡 | 2.47% | 7.88% | 25.4% → **20%** | 38.1% → **20%** | **20%** | Full ½-Kelly |

Three of the four highest-EV signals (excluding TSLA A) carry fat tails. SK Hynix B sits exactly at the 2% budget limit (20%); do not treat the ½-Kelly cap as licence to add. MU: ½-Kelly (17%) is already more conservative than the 2% budget (18.6%) — the 17% limit holds without variance adjustment. AMD's two methods agree at 18%. LLY's moderate tail leaves full ½-Kelly justified.

---

### Batch 3 — EV 1.5%–1.99%

| Ticker | Sig | 9yr EV | Avg Loss | Tail | σ_down | 95th-pct | Max (2%) | Max (3%) | ½-Kelly | Action |
|--------|-----|--------|----------|------|--------|----------|---------|---------|---------|--------|
| **^TNX** | A | +1.93% | −4.8% | 🔴 | 4.08% | 11.53% | **17.3%** | 26.0% → **20%** | **18%** | Use **17%** — variance binding |
| **AVGO** | B | +1.74% | −2.9% | 🟡 | 1.89% | 6.02% | 33.2% → **20%** | 49.8% → **20%** | **19%** | Full ½-Kelly |
| **TSLA** | B | +1.72% | −3.8% | 🟡 | 2.47% | 7.88% | 25.4% → **20%** | 38.1% → **20%** | **13%** | Full ½-Kelly |
| **META** | A | +1.72% | −5.1% | 🔴 | 4.34% | 12.26% | **16.3%** | 24.5% → **20%** | **17%** | Use **16%** — variance binding |
| **BTC** | A | +1.69% | −5.5% | 🔴 | 4.68% | 13.22% | **15.1%** | 22.7% → **20%** | **16%** | Use **15%** — variance binding |
| **MSFT** | A | +1.68% | −3.1% | 🟡 | 2.02% | 6.43% | 31.1% → **20%** | 46.7% → **20%** | **20%** | Full ½-Kelly |

This batch contains the three signals where the 2% budget is **strictly tighter** than ½-Kelly: ^TNX A (17% not 18%), META A (16% not 17%), BTC A (15% not 16%). All three have Avg Loss ≥ 4.8% and 95th-pct adverse moves of 11–13%. A single bad trade at 17–18% size could breach the 2% portfolio loss threshold. Shave by 1% in each case.

AVGO B and MSFT A: moderate tails, 95th-pct adverse well below 7%, variance non-binding — full ½-Kelly.

---

### Batch 4 — EV 1.0%–1.49%

| Ticker | Sig | 9yr EV | Avg Loss | Tail | σ_down | 95th-pct | Max (2%) | Max (3%) | ½-Kelly | Action |
|--------|-----|--------|----------|------|--------|----------|---------|---------|---------|--------|
| **Samsung** | A | +1.45% | −2.76% | 🟡 | 1.79% | 5.72% | 35.0% → **20%** | 52.5% → **20%** | **18%** | Full ½-Kelly |
| **V** | A | +1.35% | −2.5% | ✅ | 1.25% | 4.56% | 43.9% → **20%** | 65.8% → **20%** | **20%** | Full ½-Kelly |
| **NVDA** | A | +1.33% | −3.5% | 🟡 | 2.28% | 7.26% | 27.5% → **20%** | 41.3% → **20%** | **14%** | Full ½-Kelly |
| **NQ=F** | A | +1.32% | −2.3% | ✅ | 1.15% | 4.20% | 47.6% → **20%** | 71.4% → **20%** | **20%** | Full ½-Kelly |
| **TSM** | A | +1.13% | −3.5% | 🟡 | 2.28% | 7.26% | 27.5% → **20%** | 41.3% → **20%** | **14%** | Full ½-Kelly |
| **PG** | A | +1.10% | −1.38% | ✅ | 0.69% | 2.52% | 79.4% → **20%** | ≥100% → **20%** | **20%** | Full ½-Kelly |
| **GOOGL** | A | +1.08% | −2.7% | 🟡 | 1.76% | 5.60% | 35.7% → **20%** | 53.6% → **20%** | **15%** | Full ½-Kelly |
| **SMH** | A | +1.06% | −3.2% | 🟡 | 2.08% | 6.63% | 30.2% → **20%** | 45.3% → **20%** | **11%** | Full ½-Kelly |
| **CSCO** | B | +1.06% | −2.2% | ✅ | 1.10% | 4.02% | 49.8% → **20%** | 74.7% → **20%** | **17%** | Full ½-Kelly |
| **NFLX** | B | +1.01% | −4.0% | 🔴 | 3.40% | 9.61% | 20.8% → **20%** | 31.2% → **20%** | **12%** | Full ½-Kelly |

Variance is **not** the binding constraint for any Batch 4 signal. Even NFLX B (🔴, 9.61% 95th-pct) sees Max (2%) = 20.8% — just over the cap — so ½-Kelly (12%) is the operative limit regardless.

NVDA: same Avg Loss as TSM (−3.50%) giving identical σ_down and 95th-pct (7.26%); ½-Kelly = 14%. PG stands out: 95th-pct of only 2.52% — a 20% position risks −0.50% of portfolio at the 95th percentile. It is the tightest downside profile in the entire universe.

---

### Batch 5 — EV 0.5%–0.99% (21 signals)

½-Kelly is the operative limit for all names in this band. Variance budget is non-binding throughout.

| Ticker | Sig | 9yr EV | Avg Loss | Tail | σ_down | 95th-pct | Max (2%) | ½-Kelly |
|--------|-----|--------|----------|------|--------|----------|---------|---------|
| **WMT** | A | +0.95% | −1.80% | ✅ | 0.90% | 3.29% | 60.8% → **20%** | **15%** |
| **CNX1.L** | A | +0.95% | −1.81% | ✅ | 0.91% | 3.31% | 60.4% → **20%** | **19%** |
| **COST** | B | +0.93% | −2.49% | ✅ | 1.25% | 4.55% | 44.0% → **20%** | **17%** |
| **MSFT** | B | +0.93% | −2.20% | ✅ | 1.10% | 4.02% | 49.8% → **20%** | **14%** |
| **AVGO** | A | +0.89% | −3.20% | 🟡 | 2.08% | 6.63% | 30.2% → **20%** | **9%** |
| **ES=F** | A | +0.85% | −1.90% | ✅ | 0.95% | 3.47% | 57.7% → **20%** | **20%** |
| **^N225** | A | +0.79% | −3.00% | 🟡 | 1.95% | 6.22% | 32.2% → **20%** | **12%** |
| **AAPL** | A | +0.75% | −2.20% | ✅ | 1.10% | 4.02% | 49.8% → **20%** | **11%** |
| **UNH** | A | +0.70% | −2.80% | 🟡 | 1.82% | 5.79% | 34.5% → **20%** | **11%** |
| **CAT** | B | +0.69% | −3.07% | 🟡 | 2.00% | 6.37% | 31.4% → **20%** | **10%** |
| **MCD** | B | +0.68% | −2.40% | ✅ | 1.20% | 4.38% | 45.7% → **20%** | **14%** |
| **QQQ** | A | +0.66% | −2.40% | ✅ | 1.20% | 4.38% | 45.7% → **20%** | **16%** |
| **SMCI** | A | +0.65% | −6.50% | 🔴 | 5.53% | 15.62% | **12.8%** | **5%** |
| **JNJ** | A | +0.65% | −2.08% | ✅ | 1.04% | 3.80% | 52.6% → **20%** | **14%** |
| **ASML** | A | +0.62% | −3.60% | 🟡 | 2.34% | 7.46% | 26.8% → **20%** | **7%** |
| **V** | B | +0.59% | −2.30% | ✅ | 1.15% | 4.20% | 47.6% → **20%** | **14%** |
| **XLI** | A | +0.58% | −3.20% | 🟡 | 2.08% | 6.63% | 30.2% → **20%** | **12%** |
| **TSM** | B | +0.58% | −3.60% | 🟡 | 2.34% | 7.46% | 26.8% → **20%** | **9%** |
| **AAPL** | B | +0.56% | −3.70% | 🟡 | 2.41% | 7.67% | 26.1% → **20%** | **7%** |
| **ORCL** | A | +0.56% | −2.60% | 🟡 | 1.69% | 5.39% | 37.1% → **20%** | **8%** |
| **PG** | B | +0.52% | −1.72% | ✅ | 0.86% | 3.14% | 63.7% → **20%** | **12%** |

> **SMCI exception:** Avg Loss −6.50% (🔴 fat tail) gives a 95th-pct adverse move of 15.62%. Max (2%) = 12.8% — but ½-Kelly = 5% (floor) is already the most conservative limit. No additional shaving required; the floor holds.

> **ES=F 5yr exception:** In the 5yr window, ES=F Signal A Avg Loss compresses to −0.8% (76.5% win). σ_down ≈ 0.40%, 95th-pct ≈ 1.46%, Max (2%) ≈ 137%. Effectively zero sizing constraint in the current regime. WMT, CNX1.L, PG B, V B share the same characteristic of very tight loss distributions.

---

### Variance-Binding Summary

Across the full universe, the 2% per-trade loss budget is strictly tighter than ½-Kelly in only **three signals**:

| Signal | ½-Kelly | 2% Budget Cap | **Use** | Difference |
|--------|---------|--------------|---------|------------|
| **^TNX Signal A** | 18% | 17.3% | **17%** | −1% |
| **META Signal A** | 17% | 16.3% | **16%** | −1% |
| **BTC Signal A** | 16% | 15.1% | **15%** | −1% |

For every other positive-EV signal, ½-Kelly is the binding limit. The 3% budget (lower-concentration book) is non-binding for all signals including the three above.

> **Key takeaway for sizing:** The existing ½-Kelly framework is well-calibrated for the full universe except these three fat-tail signals. Reduce each by 1 percentage point. Nothing else changes.

---

## Loss Percentile Distribution — Key Tickers (Signal A, 9yr)

The mean (Avg Loss) and median loss are not the same. Equity D5 losses are right-skewed: more trades cluster near the median than the mean implies, but the tail pulls the average higher. This table maps the full loss distribution across four percentiles for the highest-priority Signal A tickers.

**How to read:** On a losing trade in NQ=F, 50% of the time the loss is ≤ 2.12% (median). Only 1 in 20 trades reaches −4.20% (P95). The P34–P66 band is where the bulk of losses land.

*Method: σ_down = \|Avg Loss\| × k (k = 0.50 for ✅, 0.65 for 🟡 tail). P34 = Avg − 0.41σ · P50 = Avg × 0.92 (skew-adjusted median) · P66 = Avg + 0.41σ · P95 = Avg + 1.65σ. All figures are loss magnitudes (positive = loss on the position).*

| Ticker | Tail | Avg Loss | P34 loss | P50 loss | P66 loss | P95 loss | ½-Kelly |
|--------|------|----------|----------|----------|----------|----------|---------|
| **NQ=F** | ✅ | −2.30% | −1.83% | −2.12% | −2.77% | −4.20% | **20%** |
| **ES=F** | ✅ | −1.90% | −1.51% | −1.75% | −2.29% | −3.47% | **20%** |
| **PG** | ✅ | −1.38% | −1.10% | −1.27% | −1.66% | −2.52% | **20%** |
| **V** | ✅ | −2.50% | −1.99% | −2.30% | −3.01% | −4.56% | **20%** |
| **AAPL** | ✅ | −2.20% | −1.75% | −2.02% | −2.65% | −4.02% | **11%** |
| **GOOGL** | 🟡 | −2.70% | −1.98% | −2.48% | −3.42% | −5.60% | **15%** |
| **MSFT** | 🟡 | −3.10% | −2.27% | −2.85% | −3.93% | −6.43% | **20%** |
| **NVDA** | 🟡 | −3.50% | −2.57% | −3.22% | −4.43% | −7.26% | **14%** |

### What this means for sizing

**Low-tail tickers (✅ — NQ=F, ES=F, PG, V, AAPL):**
The median losing trade is contained. In NQ=F, half of all losing trades are under −2.12%. The P66 is still only −2.77% — two-thirds of losing trades never breach that. At 20% position size, the median losing trade costs **−0.42% of portfolio**. The P95 (worst 1-in-20) costs −0.84%. These are genuinely manageable.

**Moderate-tail tickers (🟡 — GOOGL, MSFT, NVDA):**
The median is tolerable but the P66–P95 gap widens materially. In NVDA, the median loss is −3.22% but the P95 reaches −7.26% — a 2.3× step from median to tail. At 14% position size (½-Kelly), the P95 costs −1.02% of portfolio. Run full ½-Kelly but be aware the spread between a normal bad trade and a tail trade is larger than the low-tail names.

**P34 as a "quick bounce" benchmark:** If a trade goes against you but is still within the P34 loss (e.g. −1.83% for NQ=F), statistical history says you're in the benign half of the loss distribution — no signal to add or panic.

| Percentile | Interpretation |
|------------|---------------|
| **P34** | Mild loss — bottom third of losers; common outcome |
| **P50** | Median loss — the "typical" bad trade |
| **P66** | Upper-middle loss — 2 in 3 losers are at or below this |
| **P95** | Tail loss — one-in-twenty; the sizing guardrail level |

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

---

## DCA-Cluster (Overlapping) — D5 Blended Entry

*Companion to the non-overlapping tables above. Uses the same RSI-MA + COV signal*
*definitions but groups consecutive trigger bars into one **cluster** and treats them*
*as a single equal-weight DCA entry.*

**Method**

- A **cluster** = run of consecutive bars where the entry condition fires (no gap allowed).
- **Blended entry** = mean close across the cluster bars (equal-weight DCA).
- **Return** = (close at +5 bars after the last cluster bar) / blended_entry − 1.
- One return per cluster. Universe = 50 SWING_FRAMEWORK_TICKERS, ~10y daily.
- Source: `backend/cache/cluster_dca_d5_results.json` · Detail: `docs/CLUSTER_DCA_ANALYSIS.md`

**Universe-wide cluster shape (medians)**

| Definition | Clusters/ticker | Avg length | Max typical | % multi-day | Median days→green |
|---|---:|---:|---:|---:|---:|
| pct<5 + COV red  | 38 | 1.91 | 4–5 | 48% | 1 |
| pct<15 + COV red | 68 | 2.13 | 5–7 | 58% | 1 |

### Signal A — RSI-MA < 5th Percentile + COV Red (DCA-blended, D5)

#### Top 3 by EV

| # | Ticker | N | EV | Win% | Avg Win | Avg Loss | Median | Avg cluster len |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | **TSLA** | 47 | +3.95% | 70.2% | +7.65% | -4.78% | +2.20% | 1.57 |
| 2 | **SMCI** | 37 | +2.85% | 62.2% | +9.46% | -8.01% | +1.77% | 2.16 |
| 3 | **ASML** | 40 | +2.54% | 67.5% | +5.45% | -3.50% | +1.65% | 1.57 |

#### Top 3 by Win Rate

| # | Ticker | N | EV | Win% | Avg Win | Avg Loss | Median | Avg cluster len |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | **V** | 38 | +2.26% | 78.9% | +3.16% | -1.14% | +1.58% | 1.95 |
| 2 | **MSFT** | 40 | +2.02% | 75.0% | +3.50% | -2.42% | +1.93% | 1.62 |
| 3 | **NFLX** | 36 | +2.33% | 72.2% | +4.77% | -3.99% | +2.21% | 2.19 |

**On both top-10 lists (EV ∩ Win rate):** MSFT, NFLX, TSLA, V

#### Full universe — sorted by EV

| Ticker | N | EV | Win% | Avg Win | Avg Loss | Median | Avg len | Max len |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| TSLA | 47 | +3.95% | 70.2% | +7.65% | -4.78% | +2.20% | 1.57 | 4 |
| SMCI | 37 | +2.85% | 62.2% | +9.46% | -8.01% | +1.77% | 2.16 | 5 |
| ASML | 40 | +2.54% | 67.5% | +5.45% | -3.50% | +1.65% | 1.57 | 4 |
| NFLX | 36 | +2.33% | 72.2% | +4.77% | -3.99% | +2.21% | 2.19 | 4 |
| BTC-USD | 40 | +2.32% | 65.0% | +5.65% | -3.86% | +1.65% | 1.73 | 5 |
| V | 38 | +2.26% | 78.9% | +3.16% | -1.14% | +1.58% | 1.95 | 6 |
| META | 39 | +2.17% | 66.7% | +5.24% | -3.98% | +2.90% | 1.90 | 5 |
| AVGO | 39 | +2.05% | 66.7% | +5.26% | -4.39% | +2.11% | 1.92 | 4 |
| MSFT | 40 | +2.02% | 75.0% | +3.50% | -2.42% | +1.93% | 1.62 | 4 |
| MU | 44 | +2.00% | 59.1% | +5.72% | -3.39% | +1.42% | 1.70 | 4 |
| AMD | 36 | +1.96% | 63.9% | +5.83% | -4.89% | +2.22% | 1.67 | 4 |
| NVDA | 37 | +1.80% | 59.5% | +4.91% | -2.77% | +1.32% | 1.59 | 4 |
| AAPL | 31 | +1.78% | 64.5% | +3.77% | -1.85% | +1.46% | 2.00 | 5 |
| 000660.KS | 34 | +1.77% | 67.6% | +5.32% | -5.64% | +2.66% | 1.94 | 5 |
| LLY | 30 | +1.77% | 66.7% | +3.68% | -2.05% | +1.75% | 2.30 | 6 |
| WMT | 41 | +1.69% | 68.3% | +3.17% | -1.50% | +1.16% | 1.83 | 4 |
| ^TNX | 41 | +1.62% | 58.5% | +5.86% | -4.37% | +1.00% | 1.73 | 5 |
| PG | 44 | +1.56% | 65.9% | +2.88% | -0.98% | +0.94% | 1.91 | 4 |
| SOXX | 36 | +1.54% | 63.9% | +4.19% | -3.15% | +1.49% | 1.64 | 4 |
| AMZN | 32 | +1.50% | 71.9% | +3.73% | -4.19% | +1.56% | 2.25 | 4 |
| COST | 36 | +1.46% | 66.7% | +3.58% | -2.78% | +1.61% | 2.08 | 5 |
| SMH | 39 | +1.43% | 61.5% | +4.36% | -3.27% | +1.73% | 1.92 | 4 |
| 005930.KS | 34 | +1.32% | 61.8% | +4.04% | -3.07% | +1.79% | 1.68 | 5 |
| GOOGL | 38 | +1.28% | 63.2% | +3.58% | -2.66% | +2.09% | 1.89 | 4 |
| ^N225 | 43 | +1.24% | 60.5% | +3.49% | -2.21% | +1.23% | 1.74 | 4 |
| ORCL | 48 | +1.10% | 60.4% | +3.86% | -3.12% | +0.97% | 1.88 | 5 |
| CSCO | 36 | +1.08% | 66.7% | +2.46% | -1.70% | +0.80% | 2.22 | 5 |
| JNJ | 38 | +1.06% | 60.5% | +2.69% | -1.43% | +1.05% | 1.95 | 5 |
| UNH | 44 | +1.05% | 59.1% | +3.69% | -2.76% | +1.29% | 1.86 | 4 |
| XOM | 36 | +1.05% | 63.9% | +3.38% | -3.07% | +1.71% | 2.03 | 5 |
| ES=F | 34 | +0.98% | 70.6% | +2.02% | -1.51% | +0.63% | 1.74 | 5 |
| MCD | 35 | +0.96% | 60.0% | +3.50% | -2.86% | +1.04% | 2.31 | 7 |
| NQ=F | 31 | +0.96% | 64.5% | +2.65% | -2.12% | +1.30% | 1.58 | 5 |
| INTC | 39 | +0.94% | 48.7% | +4.66% | -2.59% | -0.37% | 2.03 | 5 |
| TSM | 40 | +0.94% | 55.0% | +4.58% | -3.51% | +0.83% | 1.70 | 3 |
| CVX | 33 | +0.91% | 57.6% | +4.25% | -3.64% | +0.77% | 2.42 | 8 |
| SLV | 30 | +0.81% | 63.3% | +2.74% | -2.53% | +0.93% | 2.03 | 5 |
| GLD | 35 | +0.69% | 54.3% | +2.27% | -1.18% | +0.41% | 1.91 | 5 |
| CAT | 33 | +0.66% | 57.6% | +3.41% | -3.07% | +0.46% | 2.09 | 5 |
| SPY | 47 | +0.61% | 66.0% | +1.98% | -2.03% | +0.89% | 1.70 | 4 |
| ^GDAXI | 37 | +0.58% | 70.3% | +2.20% | -3.25% | +0.77% | 2.08 | 6 |
| QQQ | 41 | +0.53% | 63.4% | +2.03% | -2.05% | +0.25% | 1.66 | 4 |
| OXY | 34 | +0.51% | 58.8% | +4.78% | -5.58% | +0.83% | 2.09 | 5 |
| XLI | 45 | +0.47% | 68.9% | +2.34% | -3.66% | +0.80% | 1.82 | 5 |
| BRK-B | 35 | +0.37% | 65.7% | +1.83% | -2.44% | +0.54% | 2.03 | 5 |
| BAC | 43 | +0.31% | 60.5% | +2.59% | -3.18% | +0.36% | 2.12 | 5 |
| JPM | 38 | +0.28% | 60.5% | +3.39% | -4.49% | +0.73% | 2.03 | 5 |
| DX-Y.NYB | 33 | +0.25% | 57.6% | +0.81% | -0.50% | +0.14% | 1.36 | 4 |
| ^FTSE | 39 | +0.03% | 64.1% | +1.68% | -2.90% | +0.53% | 1.95 | 5 |
| ^VIX | 23 | -1.52% | 47.8% | +5.64% | -8.09% | -1.17% | 1.43 | 3 |

### Signal B — RSI-MA 5th–15th Percentile + COV Red (DCA-blended, D5)

#### Top 3 by EV

| # | Ticker | N | EV | Win% | Avg Win | Avg Loss | Median | Avg cluster len |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | **^VIX** | 50 | +2.99% | 56.0% | +11.02% | -7.23% | +1.90% | 1.62 |
| 2 | **TSLA** | 71 | +2.69% | 60.6% | +7.37% | -4.50% | +2.14% | 2.13 |
| 3 | **000660.KS** | 71 | +2.56% | 67.6% | +5.62% | -3.81% | +3.23% | 2.00 |

#### Top 3 by Win Rate

| # | Ticker | N | EV | Win% | Avg Win | Avg Loss | Median | Avg cluster len |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | **COST** | 57 | +1.53% | 71.9% | +2.99% | -2.21% | +1.06% | 2.37 |
| 2 | **V** | 71 | +1.57% | 71.8% | +2.73% | -1.37% | +1.19% | 2.08 |
| 3 | **LLY** | 64 | +2.51% | 70.3% | +4.63% | -2.51% | +1.97% | 2.23 |

**On both top-10 lists (EV ∩ Win rate):** 000660.KS, LLY

#### Full universe — sorted by EV

| Ticker | N | EV | Win% | Avg Win | Avg Loss | Median | Avg len | Max len |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ^VIX | 50 | +2.99% | 56.0% | +11.02% | -7.23% | +1.90% | 1.62 | 3 |
| TSLA | 71 | +2.69% | 60.6% | +7.37% | -4.50% | +2.14% | 2.13 | 4 |
| 000660.KS | 71 | +2.56% | 67.6% | +5.62% | -3.81% | +3.23% | 2.00 | 5 |
| LLY | 64 | +2.51% | 70.3% | +4.63% | -2.51% | +1.97% | 2.23 | 6 |
| MU | 71 | +2.50% | 60.6% | +6.65% | -3.87% | +2.29% | 2.06 | 5 |
| AMD | 75 | +2.48% | 60.0% | +6.29% | -3.25% | +1.60% | 1.83 | 5 |
| META | 69 | +2.10% | 65.2% | +4.94% | -3.23% | +2.55% | 2.25 | 5 |
| AVGO | 68 | +2.05% | 64.7% | +5.63% | -4.52% | +2.73% | 2.07 | 4 |
| SMCI | 67 | +1.73% | 56.7% | +8.46% | -7.10% | +0.84% | 2.24 | 5 |
| NFLX | 74 | +1.65% | 63.5% | +4.79% | -3.84% | +0.76% | 2.16 | 7 |
| V | 71 | +1.57% | 71.8% | +2.73% | -1.37% | +1.19% | 2.08 | 8 |
| COST | 57 | +1.53% | 71.9% | +2.99% | -2.21% | +1.06% | 2.37 | 6 |
| TSM | 63 | +1.53% | 61.9% | +4.62% | -3.48% | +1.76% | 2.06 | 5 |
| CSCO | 63 | +1.43% | 68.3% | +2.99% | -1.92% | +1.36% | 2.35 | 6 |
| SMH | 74 | +1.36% | 62.2% | +3.96% | -2.92% | +1.67% | 1.91 | 6 |
| MSFT | 67 | +1.35% | 62.7% | +3.35% | -2.01% | +1.28% | 1.97 | 6 |
| BTC-USD | 68 | +1.33% | 58.8% | +6.59% | -6.19% | +1.23% | 2.19 | 5 |
| ORCL | 79 | +1.30% | 57.0% | +4.75% | -3.27% | +0.76% | 2.19 | 5 |
| AAPL | 69 | +1.28% | 62.3% | +3.86% | -2.97% | +1.23% | 2.17 | 5 |
| SOXX | 71 | +1.27% | 60.6% | +4.38% | -3.51% | +1.51% | 1.90 | 6 |
| ASML | 68 | +1.26% | 58.8% | +4.93% | -3.99% | +1.27% | 1.93 | 4 |
| PG | 73 | +1.22% | 61.6% | +2.82% | -1.36% | +0.60% | 2.27 | 7 |
| 005930.KS | 65 | +1.21% | 60.0% | +4.28% | -3.40% | +1.75% | 1.91 | 6 |
| ^N225 | 81 | +1.21% | 65.4% | +3.04% | -2.24% | +1.56% | 1.99 | 6 |
| ^TNX | 65 | +1.21% | 55.4% | +5.08% | -3.60% | +0.44% | 2.14 | 6 |
| AMZN | 67 | +1.15% | 59.7% | +4.26% | -3.45% | +1.43% | 2.10 | 5 |
| CAT | 67 | +1.11% | 61.2% | +3.68% | -2.94% | +2.11% | 2.09 | 5 |
| QQQ | 73 | +1.08% | 65.8% | +2.74% | -2.11% | +1.30% | 2.07 | 7 |
| WMT | 68 | +1.08% | 69.1% | +2.67% | -2.48% | +1.08% | 2.21 | 6 |
| NQ=F | 60 | +1.07% | 65.0% | +2.87% | -2.28% | +1.30% | 1.88 | 5 |
| NVDA | 66 | +1.07% | 56.1% | +5.63% | -4.75% | +1.38% | 2.03 | 5 |
| ES=F | 57 | +1.00% | 66.7% | +2.31% | -1.62% | +0.70% | 2.18 | 6 |
| JPM | 68 | +0.93% | 66.2% | +3.38% | -3.87% | +1.47% | 2.41 | 5 |
| GOOGL | 69 | +0.92% | 62.3% | +3.49% | -3.33% | +1.07% | 2.13 | 5 |
| INTC | 77 | +0.90% | 55.8% | +3.99% | -3.01% | +0.77% | 2.12 | 5 |
| MCD | 59 | +0.86% | 61.0% | +2.99% | -2.46% | +0.88% | 2.24 | 7 |
| BAC | 74 | +0.85% | 59.5% | +3.46% | -2.98% | +0.74% | 2.35 | 7 |
| GLD | 60 | +0.85% | 65.0% | +1.93% | -1.16% | +0.56% | 2.12 | 7 |
| SLV | 71 | +0.82% | 63.4% | +2.72% | -2.46% | +0.96% | 2.00 | 5 |
| JNJ | 76 | +0.72% | 55.3% | +2.81% | -1.85% | +0.57% | 2.04 | 5 |
| XLI | 75 | +0.67% | 64.0% | +2.46% | -2.51% | +0.70% | 2.23 | 6 |
| BRK-B | 64 | +0.65% | 64.1% | +2.06% | -1.86% | +0.51% | 2.25 | 6 |
| SPY | 68 | +0.65% | 67.6% | +2.00% | -2.18% | +0.72% | 2.26 | 9 |
| UNH | 69 | +0.61% | 55.1% | +3.45% | -2.86% | +0.65% | 2.36 | 5 |
| XOM | 62 | +0.61% | 66.1% | +3.10% | -4.26% | +0.94% | 2.18 | 7 |
| ^GDAXI | 71 | +0.49% | 66.2% | +2.18% | -2.83% | +1.15% | 2.37 | 6 |
| CVX | 61 | +0.48% | 62.3% | +3.18% | -3.97% | +0.73% | 2.49 | 8 |
| ^FTSE | 75 | +0.35% | 68.0% | +1.55% | -2.19% | +0.75% | 2.13 | 7 |
| OXY | 69 | +0.27% | 52.2% | +4.39% | -4.22% | +0.34% | 2.09 | 5 |
| DX-Y.NYB | 49 | +0.11% | 53.1% | +0.72% | -0.59% | +0.02% | 2.04 | 6 |

### How to use this vs the non-overlapping tables

- **Non-overlapping tables** (above) measure each isolated signal. Best for *trade*
  *frequency planning* ("how often does an independent setup fire?") and Kelly sizing
  on single-shot entries.
- **DCA-cluster tables** measure what happens when you **scale in across the whole
  oversold streak** — closer to how you'd actually deploy capital when a name stays
  below the threshold for several days.
- **Names appearing on both** the non-overlap top list *and* the DCA top list are the
  highest-conviction setups regardless of execution style.

---

## DCA-Cluster — Risk-Aware Rankings (D5)

Same DCA-blended D5 setup as the section above, but ranked by **risk-aware**
metrics instead of raw EV. This is the section that explains why TSLA/META look
dominant on raw EV but feel riskier than V — they earn the EV by accepting much
wider per-trade swings.

### Glossary

| Metric | Definition | What it tells you |
|---|---|---|
| **EV** | mean(cluster returns) | Average outcome per cluster — ignores variance |
| **Avg loss** | mean(losing clusters) | Typical losing-trade size — **lower magnitude = safer** |
| **Worst loss** | min(cluster returns) | The largest single losing cluster on record |
| **σ (stdev)** | stdev(cluster returns) | Total dispersion of outcomes — pure volatility |
| **Sortino-like** | EV / downside-deviation | Return per unit of *downside* volatility (penalises only losses) |
| **Sharpe-like** | EV / stdev | Return per unit of *total* volatility |
| **EV / \|Avg loss\|** | EV ÷ \|avg_loss\| | $ of expected return per $ of typical loss — the simplest risk-adjusted edge |

> **The intuition you're missing on EV.** EV = win_rate × avg_win + loss_rate × avg_loss.
> Two setups can share the same EV but have very different *paths* to it: V earns +2.26%
> EV with avg_win +3.16% / avg_loss −1.14% (range ≈ 4 pts). TSLA earns +3.95% EV with
> avg_win +7.65% / avg_loss −4.78% (range ≈ 12 pts). TSLA pays you ~75% more EV but you
> ride 3× wider swings per cluster. Sharpe/Sortino/EV-per-loss normalise this so you can
> compare them on equal footing.

### Signal A — RSI-MA < 5th Percentile + COV Red — D5 DCA-blended, risk views

#### Top 10 — **smallest** average loss (safest typical downside)

| # | Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **DX-Y.NYB** | 33 | +0.25 | 57.6 | -0.50 | -1.18 | 0.84 | +0.630 | +0.301 | +0.501 |
| 2 | **PG** | 44 | +1.56 | 65.9 | -0.98 | -3.00 | 2.65 | +2.130 | +0.590 | +1.590 |
| 3 | **V** | 38 | +2.26 | 78.9 | -1.14 | -2.58 | 3.17 | +3.357 | +0.711 | +1.973 |
| 4 | **GLD** | 35 | +0.69 | 54.3 | -1.18 | -3.28 | 2.45 | +0.702 | +0.283 | +0.587 |
| 5 | **JNJ** | 38 | +1.06 | 60.5 | -1.43 | -2.90 | 2.55 | +0.972 | +0.418 | +0.745 |
| 6 | **WMT** | 41 | +1.69 | 68.3 | -1.50 | -3.96 | 3.46 | +1.660 | +0.490 | +1.132 |
| 7 | **ES=F** | 34 | +0.98 | 70.6 | -1.51 | -3.62 | 2.31 | +0.994 | +0.425 | +0.653 |
| 8 | **CSCO** | 36 | +1.08 | 66.7 | -1.70 | -4.06 | 2.74 | +0.793 | +0.393 | +0.633 |
| 9 | **AAPL** | 31 | +1.78 | 64.5 | -1.85 | -6.83 | 3.92 | +1.125 | +0.453 | +0.961 |
| 10 | **SPY** | 47 | +0.61 | 66.0 | -2.03 | -12.54 | 2.90 | +0.296 | +0.212 | +0.303 |

#### Top 10 — **smallest worst loss** (tightest left tail)

| # | Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **DX-Y.NYB** | 33 | +0.25 | 57.6 | -0.50 | -1.18 | 0.84 | +0.630 | +0.301 | +0.501 |
| 2 | **V** | 38 | +2.26 | 78.9 | -1.14 | -2.58 | 3.17 | +3.357 | +0.711 | +1.973 |
| 3 | **JNJ** | 38 | +1.06 | 60.5 | -1.43 | -2.90 | 2.55 | +0.972 | +0.418 | +0.745 |
| 4 | **PG** | 44 | +1.56 | 65.9 | -0.98 | -3.00 | 2.65 | +2.130 | +0.590 | +1.590 |
| 5 | **GLD** | 35 | +0.69 | 54.3 | -1.18 | -3.28 | 2.45 | +0.702 | +0.283 | +0.587 |
| 6 | **NQ=F** | 31 | +0.96 | 64.5 | -2.12 | -3.55 | 2.79 | +0.687 | +0.342 | +0.451 |
| 7 | **ES=F** | 34 | +0.98 | 70.6 | -1.51 | -3.62 | 2.31 | +0.994 | +0.425 | +0.653 |
| 8 | **WMT** | 41 | +1.69 | 68.3 | -1.50 | -3.96 | 3.46 | +1.660 | +0.490 | +1.132 |
| 9 | **CSCO** | 36 | +1.08 | 66.7 | -1.70 | -4.06 | 2.74 | +0.793 | +0.393 | +0.633 |
| 10 | **QQQ** | 41 | +0.53 | 63.4 | -2.05 | -4.11 | 2.59 | +0.376 | +0.206 | +0.260 |

#### Top 10 — **EV per unit of typical loss** (best gain-vs-pain)

| # | Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **V** | 38 | +2.26 | 78.9 | -1.14 | -2.58 | 3.17 | +3.357 | +0.711 | +1.973 |
| 2 | **PG** | 44 | +1.56 | 65.9 | -0.98 | -3.00 | 2.65 | +2.130 | +0.590 | +1.590 |
| 3 | **WMT** | 41 | +1.69 | 68.3 | -1.50 | -3.96 | 3.46 | +1.660 | +0.490 | +1.132 |
| 4 | **AAPL** | 31 | +1.78 | 64.5 | -1.85 | -6.83 | 3.92 | +1.125 | +0.453 | +0.961 |
| 5 | **LLY** | 30 | +1.77 | 66.7 | -2.05 | -7.10 | 4.11 | +1.085 | +0.432 | +0.865 |
| 6 | **MSFT** | 40 | +2.02 | 75.0 | -2.42 | -4.87 | 3.52 | +1.463 | +0.574 | +0.836 |
| 7 | **TSLA** | 47 | +3.95 | 70.2 | -4.78 | -13.21 | 9.24 | +1.124 | +0.428 | +0.826 |
| 8 | **JNJ** | 38 | +1.06 | 60.5 | -1.43 | -2.90 | 2.55 | +0.972 | +0.418 | +0.745 |
| 9 | **ASML** | 40 | +2.54 | 67.5 | -3.50 | -11.10 | 6.93 | +1.035 | +0.367 | +0.727 |
| 10 | **ES=F** | 34 | +0.98 | 70.6 | -1.51 | -3.62 | 2.31 | +0.994 | +0.425 | +0.653 |

#### Top 10 — **Sortino-like** (EV / downside σ)

| # | Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **V** | 38 | +2.26 | 78.9 | -1.14 | -2.58 | 3.17 | +3.357 | +0.711 | +1.973 |
| 2 | **PG** | 44 | +1.56 | 65.9 | -0.98 | -3.00 | 2.65 | +2.130 | +0.590 | +1.590 |
| 3 | **WMT** | 41 | +1.69 | 68.3 | -1.50 | -3.96 | 3.46 | +1.660 | +0.490 | +1.132 |
| 4 | **MSFT** | 40 | +2.02 | 75.0 | -2.42 | -4.87 | 3.52 | +1.463 | +0.574 | +0.836 |
| 5 | **AAPL** | 31 | +1.78 | 64.5 | -1.85 | -6.83 | 3.92 | +1.125 | +0.453 | +0.961 |
| 6 | **TSLA** | 47 | +3.95 | 70.2 | -4.78 | -13.21 | 9.24 | +1.124 | +0.428 | +0.826 |
| 7 | **LLY** | 30 | +1.77 | 66.7 | -2.05 | -7.10 | 4.11 | +1.085 | +0.432 | +0.865 |
| 8 | **ASML** | 40 | +2.54 | 67.5 | -3.50 | -11.10 | 6.93 | +1.035 | +0.367 | +0.727 |
| 9 | **ES=F** | 34 | +0.98 | 70.6 | -1.51 | -3.62 | 2.31 | +0.994 | +0.425 | +0.653 |
| 10 | **JNJ** | 38 | +1.06 | 60.5 | -1.43 | -2.90 | 2.55 | +0.972 | +0.418 | +0.745 |

#### Top 10 — **Sharpe-like** (EV / total σ)

| # | Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **V** | 38 | +2.26 | 78.9 | -1.14 | -2.58 | 3.17 | +3.357 | +0.711 | +1.973 |
| 2 | **PG** | 44 | +1.56 | 65.9 | -0.98 | -3.00 | 2.65 | +2.130 | +0.590 | +1.590 |
| 3 | **MSFT** | 40 | +2.02 | 75.0 | -2.42 | -4.87 | 3.52 | +1.463 | +0.574 | +0.836 |
| 4 | **WMT** | 41 | +1.69 | 68.3 | -1.50 | -3.96 | 3.46 | +1.660 | +0.490 | +1.132 |
| 5 | **AAPL** | 31 | +1.78 | 64.5 | -1.85 | -6.83 | 3.92 | +1.125 | +0.453 | +0.961 |
| 6 | **LLY** | 30 | +1.77 | 66.7 | -2.05 | -7.10 | 4.11 | +1.085 | +0.432 | +0.865 |
| 7 | **TSLA** | 47 | +3.95 | 70.2 | -4.78 | -13.21 | 9.24 | +1.124 | +0.428 | +0.826 |
| 8 | **ES=F** | 34 | +0.98 | 70.6 | -1.51 | -3.62 | 2.31 | +0.994 | +0.425 | +0.653 |
| 9 | **JNJ** | 38 | +1.06 | 60.5 | -1.43 | -2.90 | 2.55 | +0.972 | +0.418 | +0.745 |
| 10 | **NFLX** | 36 | +2.33 | 72.2 | -3.99 | -8.28 | 5.86 | +0.926 | +0.398 | +0.585 |

### Signal B — RSI-MA 5th–15th Percentile + COV Red — D5 DCA-blended, risk views

#### Top 10 — **smallest** average loss (safest typical downside)

| # | Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **DX-Y.NYB** | 49 | +0.11 | 53.1 | -0.59 | -1.39 | 0.88 | +0.218 | +0.120 | +0.178 |
| 2 | **GLD** | 60 | +0.85 | 65.0 | -1.16 | -2.99 | 2.19 | +1.021 | +0.387 | +0.730 |
| 3 | **PG** | 73 | +1.22 | 61.6 | -1.36 | -3.61 | 2.75 | +1.203 | +0.443 | +0.896 |
| 4 | **V** | 71 | +1.57 | 71.8 | -1.37 | -4.34 | 3.02 | +1.642 | +0.520 | +1.146 |
| 5 | **ES=F** | 57 | +1.00 | 66.7 | -1.62 | -4.35 | 2.49 | +0.833 | +0.400 | +0.613 |
| 6 | **JNJ** | 77 | +0.73 | 55.8 | -1.85 | -12.58 | 3.55 | +0.391 | +0.207 | +0.396 |
| 7 | **BRK-B** | 64 | +0.65 | 64.1 | -1.86 | -5.29 | 2.49 | +0.474 | +0.261 | +0.350 |
| 8 | **CSCO** | 63 | +1.43 | 68.3 | -1.92 | -6.70 | 3.36 | +0.975 | +0.425 | +0.742 |
| 9 | **MSFT** | 67 | +1.35 | 62.7 | -2.01 | -6.69 | 3.46 | +0.804 | +0.392 | +0.675 |
| 10 | **QQQ** | 73 | +1.08 | 65.8 | -2.11 | -6.15 | 3.03 | +0.681 | +0.358 | +0.514 |

#### Top 10 — **smallest worst loss** (tightest left tail)

| # | Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **DX-Y.NYB** | 49 | +0.11 | 53.1 | -0.59 | -1.39 | 0.88 | +0.218 | +0.120 | +0.178 |
| 2 | **GLD** | 60 | +0.85 | 65.0 | -1.16 | -2.99 | 2.19 | +1.021 | +0.387 | +0.730 |
| 3 | **PG** | 73 | +1.22 | 61.6 | -1.36 | -3.61 | 2.75 | +1.203 | +0.443 | +0.896 |
| 4 | **V** | 71 | +1.57 | 71.8 | -1.37 | -4.34 | 3.02 | +1.642 | +0.520 | +1.146 |
| 5 | **ES=F** | 57 | +1.00 | 66.7 | -1.62 | -4.35 | 2.49 | +0.833 | +0.400 | +0.613 |
| 6 | **BRK-B** | 64 | +0.65 | 64.1 | -1.86 | -5.29 | 2.49 | +0.474 | +0.261 | +0.350 |
| 7 | **QQQ** | 73 | +1.08 | 65.8 | -2.11 | -6.15 | 3.03 | +0.681 | +0.358 | +0.514 |
| 8 | **NQ=F** | 60 | +1.07 | 65.0 | -2.28 | -6.23 | 3.16 | +0.643 | +0.339 | +0.469 |
| 9 | **SMH** | 74 | +1.36 | 62.2 | -2.92 | -6.48 | 4.23 | +0.623 | +0.320 | +0.464 |
| 10 | **MSFT** | 67 | +1.35 | 62.7 | -2.01 | -6.69 | 3.46 | +0.804 | +0.392 | +0.675 |

#### Top 10 — **EV per unit of typical loss** (best gain-vs-pain)

| # | Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **V** | 71 | +1.57 | 71.8 | -1.37 | -4.34 | 3.02 | +1.642 | +0.520 | +1.146 |
| 2 | **LLY** | 64 | +2.51 | 70.3 | -2.51 | -9.30 | 5.43 | +1.325 | +0.463 | +1.001 |
| 3 | **PG** | 73 | +1.22 | 61.6 | -1.36 | -3.61 | 2.75 | +1.203 | +0.443 | +0.896 |
| 4 | **AMD** | 75 | +2.48 | 60.0 | -3.25 | -10.22 | 6.09 | +0.991 | +0.406 | +0.762 |
| 5 | **CSCO** | 63 | +1.43 | 68.3 | -1.92 | -6.70 | 3.36 | +0.975 | +0.425 | +0.742 |
| 6 | **GLD** | 60 | +0.85 | 65.0 | -1.16 | -2.99 | 2.19 | +1.021 | +0.387 | +0.730 |
| 7 | **COST** | 57 | +1.53 | 71.9 | -2.21 | -8.99 | 3.51 | +0.892 | +0.435 | +0.693 |
| 8 | **MSFT** | 67 | +1.35 | 62.7 | -2.01 | -6.69 | 3.46 | +0.804 | +0.392 | +0.675 |
| 9 | **000660.KS** | 71 | +2.56 | 67.6 | -3.81 | -14.85 | 6.07 | +0.805 | +0.422 | +0.673 |
| 10 | **META** | 69 | +2.10 | 65.2 | -3.23 | -18.24 | 5.15 | +0.737 | +0.408 | +0.651 |

#### Top 10 — **Sortino-like** (EV / downside σ)

| # | Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **V** | 71 | +1.57 | 71.8 | -1.37 | -4.34 | 3.02 | +1.642 | +0.520 | +1.146 |
| 2 | **LLY** | 64 | +2.51 | 70.3 | -2.51 | -9.30 | 5.43 | +1.325 | +0.463 | +1.001 |
| 3 | **PG** | 73 | +1.22 | 61.6 | -1.36 | -3.61 | 2.75 | +1.203 | +0.443 | +0.896 |
| 4 | **GLD** | 60 | +0.85 | 65.0 | -1.16 | -2.99 | 2.19 | +1.021 | +0.387 | +0.730 |
| 5 | **AMD** | 75 | +2.48 | 60.0 | -3.25 | -10.22 | 6.09 | +0.991 | +0.406 | +0.762 |
| 6 | **CSCO** | 63 | +1.43 | 68.3 | -1.92 | -6.70 | 3.36 | +0.975 | +0.425 | +0.742 |
| 7 | **COST** | 57 | +1.53 | 71.9 | -2.21 | -8.99 | 3.51 | +0.892 | +0.435 | +0.693 |
| 8 | **ES=F** | 57 | +1.00 | 66.7 | -1.62 | -4.35 | 2.49 | +0.833 | +0.400 | +0.613 |
| 9 | **000660.KS** | 71 | +2.56 | 67.6 | -3.81 | -14.85 | 6.07 | +0.805 | +0.422 | +0.673 |
| 10 | **MSFT** | 67 | +1.35 | 62.7 | -2.01 | -6.69 | 3.46 | +0.804 | +0.392 | +0.675 |

#### Top 10 — **Sharpe-like** (EV / total σ)

| # | Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **V** | 71 | +1.57 | 71.8 | -1.37 | -4.34 | 3.02 | +1.642 | +0.520 | +1.146 |
| 2 | **LLY** | 64 | +2.51 | 70.3 | -2.51 | -9.30 | 5.43 | +1.325 | +0.463 | +1.001 |
| 3 | **PG** | 73 | +1.22 | 61.6 | -1.36 | -3.61 | 2.75 | +1.203 | +0.443 | +0.896 |
| 4 | **COST** | 57 | +1.53 | 71.9 | -2.21 | -8.99 | 3.51 | +0.892 | +0.435 | +0.693 |
| 5 | **CSCO** | 63 | +1.43 | 68.3 | -1.92 | -6.70 | 3.36 | +0.975 | +0.425 | +0.742 |
| 6 | **000660.KS** | 71 | +2.56 | 67.6 | -3.81 | -14.85 | 6.07 | +0.805 | +0.422 | +0.673 |
| 7 | **META** | 69 | +2.10 | 65.2 | -3.23 | -18.24 | 5.15 | +0.737 | +0.408 | +0.651 |
| 8 | **AMD** | 75 | +2.48 | 60.0 | -3.25 | -10.22 | 6.09 | +0.991 | +0.406 | +0.762 |
| 9 | **ES=F** | 57 | +1.00 | 66.7 | -1.62 | -4.35 | 2.49 | +0.833 | +0.400 | +0.613 |
| 10 | **MSFT** | 67 | +1.35 | 62.7 | -2.01 | -6.69 | 3.46 | +0.804 | +0.392 | +0.675 |

### Side-by-side: TSLA / META vs V — why "high EV" doesn't equal "best risk-adjusted"

*Signal A (pct<5 + COV red), D5 DCA-blended.*

| Ticker | EV | Win% | Avg Win | Avg Loss | σ | Sortino | Sharpe | EV/\|Loss\| |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **TSLA** | +3.95% | 70.2% | +7.65% | -4.78% | 9.24 | +1.124 | +0.428 | +0.826 |
| **META** | +2.17% | 66.7% | +5.24% | -3.98% | 5.48 | +0.679 | +0.395 | +0.545 |
| **V** | +2.26% | 78.9% | +3.16% | -1.14% | 3.17 | +3.357 | +0.711 | +1.973 |
| **MSFT** | +2.02% | 75.0% | +3.50% | -2.42% | 3.52 | +1.463 | +0.574 | +0.836 |
| **ASML** | +2.54% | 67.5% | +5.45% | -3.50% | 6.93 | +1.035 | +0.367 | +0.727 |
| **AVGO** | +2.05% | 66.7% | +5.26% | -4.39% | 6.51 | +0.613 | +0.314 | +0.466 |
| **AAPL** | +1.78% | 64.5% | +3.77% | -1.85% | 3.92 | +1.125 | +0.453 | +0.961 |

**Read the row:** TSLA's EV (+3.95%) beats V's (+2.26%), but V's σ is ~⅓ of TSLA's,
so V's **Sharpe-like** and **EV-per-loss** can be higher even with smaller raw EV.
That's the missing dimension: EV is the *mean*, the risk metrics tell you about the
*spread*. Position size should fall as σ rises — Kelly already does some of this, but
looking at Sharpe/Sortino/EV-per-loss makes it explicit.

### Practical interpretation

- Use **EV** to rank *opportunity size*.
- Use **EV / |Avg Loss|** as a quick sanity check: anything < ~0.4 means each $ of edge
  costs you nearly $2.50 of typical loss — heavy tails.
- Use **Sortino** to rank *risk-adjusted edge* in a way that doesn't penalise upside variance.
- For sizing, multiply Half-Kelly by a haircut when σ is in the top quartile of the
  universe (TSLA, SMCI, BTC-USD typically qualify).

### Index ETFs & futures — why they don't surface in the top 10s

All 50 SWING_FRAMEWORK_TICKERS ran with full data (~10y daily). The broad-index names
simply have modest per-trade edges because their wins and losses are nearly symmetric.
Their value is **consistency and reliability**, not headline EV.

*Signal A (pct<5 + COV red), D5 DCA-blended.*

| Ticker | N | EV | Win% | Avg Win | Avg Loss | σ | Sortino | EV/\|Loss\| |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| QQQ | 41 | +0.53% | 63.4% | +2.03% | -2.05% | 2.59 | +0.376 | +0.260 |
| NQ=F | 31 | +0.96% | 64.5% | +2.65% | -2.12% | 2.79 | +0.687 | +0.451 |
| SPY | 47 | +0.61% | 66.0% | +1.98% | -2.03% | 2.90 | +0.296 | +0.303 |
| ES=F | 34 | +0.98% | 70.6% | +2.02% | -1.51% | 2.31 | +0.994 | +0.653 |
| ^N225 | 43 | +1.24% | 60.5% | +3.49% | -2.21% | 3.83 | +0.577 | +0.560 |
| ^GDAXI | 37 | +0.58% | 70.3% | +2.20% | -3.25% | 3.52 | +0.225 | +0.178 |
| ^FTSE | 39 | +0.03% | 64.1% | +1.68% | -2.90% | 3.13 | +0.012 | +0.011 |

*Signal B (pct<15 + COV red), D5 DCA-blended.*

| Ticker | N | EV | Win% | Avg Win | Avg Loss | σ | Sortino | EV/\|Loss\| |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| QQQ | 73 | +1.08% | 65.8% | +2.74% | -2.11% | 3.03 | +0.681 | +0.514 |
| NQ=F | 60 | +1.07% | 65.0% | +2.87% | -2.28% | 3.16 | +0.643 | +0.469 |
| SPY | 68 | +0.65% | 67.6% | +2.00% | -2.18% | 2.81 | +0.335 | +0.299 |
| ES=F | 57 | +1.00% | 66.7% | +2.31% | -1.62% | 2.49 | +0.833 | +0.613 |
| ^N225 | 81 | +1.21% | 65.4% | +3.04% | -2.24% | 3.43 | +0.576 | +0.541 |
| ^GDAXI | 71 | +0.49% | 66.2% | +2.18% | -2.83% | 3.16 | +0.212 | +0.172 |
| ^FTSE | 75 | +0.35% | 68.0% | +1.55% | -2.19% | 2.53 | +0.178 | +0.161 |

**Read-out.** ES=F is the standout: 70.6% win, +0.99 Sortino — would be #11 on the
Sortino board. SPY/QQQ are reliable but with EV near +0.5–1.0% the DCA-cluster method
doesn't put them on a 10-slot leaderboard. **Treat them as low-variance utility positions**:
they earn their place from low σ and high win rate, not raw expectancy. Pair them with a
higher-EV single-name (TSLA, ASML, AVGO) for a barbell of risk-adjusted edge and ceiling.

> Full per-ticker rows including all index names are in the *Full universe — sorted by EV*
> tables earlier in this section.

---

## DCA-Cluster — Risk-Aware Rankings (D5, no-COV variants)

Same DCA-blended D5 method as the prior risk section, but **without** the COV red
filter. Two buckets:

- **pct < 5**  — RSI-MA percentile below 5th (deep oversold)
- **pct 5–10** — RSI-MA percentile in the 5th–10th band (moderate oversold)

Universe = 50 SWING_FRAMEWORK_TICKERS, ~10y daily.

### pct < 5 (no COV) — D5 DCA-blended, risk views

#### Top 10 — **smallest** average loss (safest typical downside)

| # | Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **DX-Y.NYB** | 64 | +0.35 | 67.2 | -0.58 | -1.45 | 0.87 | +0.845 | +0.395 | +0.590 |
| 2 | **GLD** | 54 | +1.17 | 64.8 | -1.15 | -3.28 | 2.59 | +1.400 | +0.449 | +1.016 |
| 3 | **JNJ** | 62 | +0.93 | 62.9 | -1.47 | -5.92 | 2.42 | +0.742 | +0.385 | +0.634 |
| 4 | **PG** | 69 | +1.58 | 72.5 | -1.59 | -4.76 | 2.89 | +1.467 | +0.547 | +0.994 |
| 5 | **CSCO** | 48 | +1.67 | 68.8 | -1.62 | -4.06 | 3.29 | +1.449 | +0.507 | +1.029 |
| 6 | **^GDAXI** | 55 | +1.02 | 72.7 | -1.77 | -15.42 | 2.99 | +0.475 | +0.341 | +0.575 |
| 7 | **BRK-B** | 59 | +0.82 | 66.1 | -1.97 | -7.95 | 2.73 | +0.535 | +0.302 | +0.418 |
| 8 | **SLV** | 47 | +1.04 | 63.8 | -2.01 | -4.97 | 2.96 | +0.661 | +0.351 | +0.518 |
| 9 | **SPY** | 69 | +0.92 | 69.6 | -2.06 | -12.54 | 2.84 | +0.491 | +0.325 | +0.449 |
| 10 | **WMT** | 58 | +1.27 | 65.5 | -2.08 | -6.86 | 3.52 | +0.856 | +0.362 | +0.611 |

#### Top 10 — **smallest worst loss** (tightest left tail)

| # | Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **DX-Y.NYB** | 64 | +0.35 | 67.2 | -0.58 | -1.45 | 0.87 | +0.845 | +0.395 | +0.590 |
| 2 | **GLD** | 54 | +1.17 | 64.8 | -1.15 | -3.28 | 2.59 | +1.400 | +0.449 | +1.016 |
| 3 | **CSCO** | 48 | +1.67 | 68.8 | -1.62 | -4.06 | 3.29 | +1.449 | +0.507 | +1.029 |
| 4 | **PG** | 69 | +1.58 | 72.5 | -1.59 | -4.76 | 2.89 | +1.467 | +0.547 | +0.994 |
| 5 | **SLV** | 47 | +1.04 | 63.8 | -2.01 | -4.97 | 2.96 | +0.661 | +0.351 | +0.518 |
| 6 | **JNJ** | 62 | +0.93 | 62.9 | -1.47 | -5.92 | 2.42 | +0.742 | +0.385 | +0.634 |
| 7 | **UNH** | 62 | +1.24 | 62.9 | -2.48 | -6.75 | 3.84 | +0.645 | +0.324 | +0.501 |
| 8 | **COST** | 53 | +1.51 | 69.8 | -2.55 | -6.84 | 3.63 | +0.782 | +0.416 | +0.591 |
| 9 | **WMT** | 58 | +1.27 | 65.5 | -2.08 | -6.86 | 3.52 | +0.856 | +0.362 | +0.611 |
| 10 | **LLY** | 43 | +1.50 | 65.1 | -2.83 | -7.10 | 4.18 | +0.675 | +0.358 | +0.529 |

#### Top 10 — **EV per unit of typical loss** (best gain-vs-pain)

| # | Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **CSCO** | 48 | +1.67 | 68.8 | -1.62 | -4.06 | 3.29 | +1.449 | +0.507 | +1.029 |
| 2 | **GLD** | 54 | +1.17 | 64.8 | -1.15 | -3.28 | 2.59 | +1.400 | +0.449 | +1.016 |
| 3 | **PG** | 69 | +1.58 | 72.5 | -1.59 | -4.76 | 2.89 | +1.467 | +0.547 | +0.994 |
| 4 | **NVDA** | 72 | +3.00 | 66.7 | -3.53 | -7.97 | 6.18 | +1.274 | +0.485 | +0.850 |
| 5 | **ASML** | 70 | +2.42 | 74.3 | -3.24 | -11.10 | 5.69 | +1.119 | +0.425 | +0.745 |
| 6 | **005930.KS** | 65 | +1.97 | 70.8 | -2.66 | -12.48 | 4.30 | +0.944 | +0.459 | +0.743 |
| 7 | **BTC-USD** | 66 | +2.40 | 65.2 | -3.40 | -10.56 | 6.30 | +0.851 | +0.380 | +0.704 |
| 8 | **GOOGL** | 60 | +1.97 | 73.3 | -2.83 | -11.74 | 4.02 | +0.919 | +0.489 | +0.695 |
| 9 | **AVGO** | 57 | +2.47 | 66.7 | -3.70 | -11.12 | 6.75 | +0.856 | +0.366 | +0.668 |
| 10 | **AAPL** | 56 | +1.41 | 58.9 | -2.19 | -7.35 | 4.17 | +0.781 | +0.339 | +0.646 |

#### Top 10 — **Sortino-like** (EV / downside σ)

| # | Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **PG** | 69 | +1.58 | 72.5 | -1.59 | -4.76 | 2.89 | +1.467 | +0.547 | +0.994 |
| 2 | **CSCO** | 48 | +1.67 | 68.8 | -1.62 | -4.06 | 3.29 | +1.449 | +0.507 | +1.029 |
| 3 | **GLD** | 54 | +1.17 | 64.8 | -1.15 | -3.28 | 2.59 | +1.400 | +0.449 | +1.016 |
| 4 | **NVDA** | 72 | +3.00 | 66.7 | -3.53 | -7.97 | 6.18 | +1.274 | +0.485 | +0.850 |
| 5 | **ASML** | 70 | +2.42 | 74.3 | -3.24 | -11.10 | 5.69 | +1.119 | +0.425 | +0.745 |
| 6 | **005930.KS** | 65 | +1.97 | 70.8 | -2.66 | -12.48 | 4.30 | +0.944 | +0.459 | +0.743 |
| 7 | **GOOGL** | 60 | +1.97 | 73.3 | -2.83 | -11.74 | 4.02 | +0.919 | +0.489 | +0.695 |
| 8 | **AVGO** | 57 | +2.47 | 66.7 | -3.70 | -11.12 | 6.75 | +0.856 | +0.366 | +0.668 |
| 9 | **WMT** | 58 | +1.27 | 65.5 | -2.08 | -6.86 | 3.52 | +0.856 | +0.362 | +0.611 |
| 10 | **BTC-USD** | 66 | +2.40 | 65.2 | -3.40 | -10.56 | 6.30 | +0.851 | +0.380 | +0.704 |

#### Top 10 — **Sharpe-like** (EV / total σ)

| # | Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **PG** | 69 | +1.58 | 72.5 | -1.59 | -4.76 | 2.89 | +1.467 | +0.547 | +0.994 |
| 2 | **CSCO** | 48 | +1.67 | 68.8 | -1.62 | -4.06 | 3.29 | +1.449 | +0.507 | +1.029 |
| 3 | **GOOGL** | 60 | +1.97 | 73.3 | -2.83 | -11.74 | 4.02 | +0.919 | +0.489 | +0.695 |
| 4 | **NVDA** | 72 | +3.00 | 66.7 | -3.53 | -7.97 | 6.18 | +1.274 | +0.485 | +0.850 |
| 5 | **005930.KS** | 65 | +1.97 | 70.8 | -2.66 | -12.48 | 4.30 | +0.944 | +0.459 | +0.743 |
| 6 | **GLD** | 54 | +1.17 | 64.8 | -1.15 | -3.28 | 2.59 | +1.400 | +0.449 | +1.016 |
| 7 | **MSFT** | 73 | +1.60 | 74.0 | -3.15 | -10.09 | 3.70 | +0.839 | +0.433 | +0.509 |
| 8 | **ASML** | 70 | +2.42 | 74.3 | -3.24 | -11.10 | 5.69 | +1.119 | +0.425 | +0.745 |
| 9 | **COST** | 53 | +1.51 | 69.8 | -2.55 | -6.84 | 3.63 | +0.782 | +0.416 | +0.591 |
| 10 | **V** | 59 | +1.52 | 71.2 | -2.35 | -11.17 | 3.70 | +0.747 | +0.411 | +0.645 |

#### Top 10 — **EV** (for cross-reference vs the risk views above)

| # | Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **NVDA** | 72 | +3.00 | 66.7 | -3.53 | -7.97 | 6.18 | +1.274 | +0.485 | +0.850 |
| 2 | **AVGO** | 57 | +2.47 | 66.7 | -3.70 | -11.12 | 6.75 | +0.856 | +0.366 | +0.668 |
| 3 | **ASML** | 70 | +2.42 | 74.3 | -3.24 | -11.10 | 5.69 | +1.119 | +0.425 | +0.745 |
| 4 | **BTC-USD** | 66 | +2.40 | 65.2 | -3.40 | -10.56 | 6.30 | +0.851 | +0.380 | +0.704 |
| 5 | **000660.KS** | 60 | +2.31 | 71.7 | -5.54 | -16.23 | 6.81 | +0.585 | +0.340 | +0.418 |
| 6 | **^VIX** | 49 | +2.26 | 53.1 | -7.92 | -22.97 | 12.39 | +0.328 | +0.182 | +0.285 |
| 7 | **TSLA** | 69 | +2.18 | 60.9 | -5.48 | -26.80 | 8.50 | +0.440 | +0.257 | +0.398 |
| 8 | **MU** | 73 | +2.15 | 63.0 | -4.24 | -25.02 | 6.71 | +0.544 | +0.321 | +0.507 |
| 9 | **005930.KS** | 65 | +1.97 | 70.8 | -2.66 | -12.48 | 4.30 | +0.944 | +0.459 | +0.743 |
| 10 | **GOOGL** | 60 | +1.97 | 73.3 | -2.83 | -11.74 | 4.02 | +0.919 | +0.489 | +0.695 |

#### Full universe — pct < 5 (no COV), sorted by EV

| Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| NVDA | 72 | +3.00 | 66.7 | -3.53 | -7.97 | 6.18 | +1.274 | +0.485 | +0.850 |
| AVGO | 57 | +2.47 | 66.7 | -3.70 | -11.12 | 6.75 | +0.856 | +0.366 | +0.668 |
| ASML | 70 | +2.42 | 74.3 | -3.24 | -11.10 | 5.69 | +1.119 | +0.425 | +0.745 |
| BTC-USD | 66 | +2.40 | 65.2 | -3.40 | -10.56 | 6.30 | +0.851 | +0.380 | +0.704 |
| 000660.KS | 60 | +2.31 | 71.7 | -5.54 | -16.23 | 6.81 | +0.585 | +0.340 | +0.418 |
| ^VIX | 49 | +2.26 | 53.1 | -7.92 | -22.97 | 12.39 | +0.328 | +0.182 | +0.285 |
| TSLA | 69 | +2.18 | 60.9 | -5.48 | -26.80 | 8.50 | +0.440 | +0.257 | +0.398 |
| MU | 73 | +2.15 | 63.0 | -4.24 | -25.02 | 6.71 | +0.544 | +0.321 | +0.507 |
| 005930.KS | 65 | +1.97 | 70.8 | -2.66 | -12.48 | 4.30 | +0.944 | +0.459 | +0.743 |
| GOOGL | 60 | +1.97 | 73.3 | -2.83 | -11.74 | 4.02 | +0.919 | +0.489 | +0.695 |
| AMD | 62 | +1.80 | 59.7 | -4.37 | -11.42 | 6.59 | +0.509 | +0.274 | +0.413 |
| AMZN | 53 | +1.74 | 71.7 | -3.34 | -9.75 | 4.42 | +0.768 | +0.393 | +0.521 |
| CSCO | 48 | +1.67 | 68.8 | -1.62 | -4.06 | 3.29 | +1.449 | +0.507 | +1.029 |
| ^TNX | 66 | +1.64 | 60.6 | -2.57 | -11.25 | 5.08 | +0.658 | +0.323 | +0.639 |
| MSFT | 73 | +1.60 | 74.0 | -3.15 | -10.09 | 3.70 | +0.839 | +0.433 | +0.509 |
| PG | 69 | +1.58 | 72.5 | -1.59 | -4.76 | 2.89 | +1.467 | +0.547 | +0.994 |
| V | 59 | +1.52 | 71.2 | -2.35 | -11.17 | 3.70 | +0.747 | +0.411 | +0.645 |
| COST | 53 | +1.51 | 69.8 | -2.55 | -6.84 | 3.63 | +0.782 | +0.416 | +0.591 |
| LLY | 43 | +1.50 | 65.1 | -2.83 | -7.10 | 4.18 | +0.675 | +0.358 | +0.529 |
| META | 55 | +1.49 | 60.0 | -4.14 | -13.86 | 5.94 | +0.406 | +0.252 | +0.361 |
| AAPL | 56 | +1.41 | 58.9 | -2.19 | -7.35 | 4.17 | +0.781 | +0.339 | +0.646 |
| ORCL | 57 | +1.33 | 63.2 | -2.82 | -10.80 | 4.47 | +0.560 | +0.299 | +0.474 |
| SMH | 69 | +1.32 | 63.8 | -3.40 | -15.66 | 4.56 | +0.478 | +0.290 | +0.389 |
| WMT | 58 | +1.27 | 65.5 | -2.08 | -6.86 | 3.52 | +0.856 | +0.362 | +0.611 |
| UNH | 62 | +1.24 | 62.9 | -2.48 | -6.75 | 3.84 | +0.645 | +0.324 | +0.501 |
| TSM | 66 | +1.21 | 65.2 | -2.97 | -7.21 | 3.95 | +0.561 | +0.308 | +0.408 |
| SOXX | 63 | +1.18 | 58.7 | -3.18 | -15.93 | 4.71 | +0.420 | +0.252 | +0.373 |
| CAT | 54 | +1.17 | 68.5 | -2.77 | -9.17 | 3.50 | +0.561 | +0.334 | +0.423 |
| GLD | 54 | +1.17 | 64.8 | -1.15 | -3.28 | 2.59 | +1.400 | +0.449 | +1.016 |
| SMCI | 64 | +1.14 | 54.7 | -6.68 | -27.48 | 10.52 | +0.176 | +0.108 | +0.171 |
| SLV | 47 | +1.04 | 63.8 | -2.01 | -4.97 | 2.96 | +0.661 | +0.351 | +0.518 |
| ^GDAXI | 55 | +1.02 | 72.7 | -1.77 | -15.42 | 2.99 | +0.475 | +0.341 | +0.575 |
| NFLX | 61 | +1.00 | 67.2 | -6.36 | -28.27 | 7.47 | +0.182 | +0.133 | +0.157 |
| INTC | 52 | +0.97 | 57.7 | -2.93 | -8.35 | 4.67 | +0.398 | +0.207 | +0.330 |
| ES=F | 53 | +0.94 | 69.8 | -2.31 | -12.06 | 3.11 | +0.465 | +0.304 | +0.409 |
| JNJ | 62 | +0.93 | 62.9 | -1.47 | -5.92 | 2.42 | +0.742 | +0.385 | +0.634 |
| ^N225 | 59 | +0.93 | 66.1 | -3.20 | -13.69 | 4.09 | +0.335 | +0.227 | +0.290 |
| SPY | 69 | +0.92 | 69.6 | -2.06 | -12.54 | 2.84 | +0.491 | +0.325 | +0.449 |
| NQ=F | 55 | +0.87 | 61.8 | -2.60 | -11.24 | 3.51 | +0.402 | +0.247 | +0.334 |
| QQQ | 68 | +0.87 | 64.7 | -2.55 | -12.54 | 3.33 | +0.417 | +0.262 | +0.342 |
| BRK-B | 59 | +0.82 | 66.1 | -1.97 | -7.95 | 2.73 | +0.535 | +0.302 | +0.418 |
| BAC | 55 | +0.80 | 65.5 | -3.97 | -21.33 | 4.87 | +0.226 | +0.165 | +0.203 |
| OXY | 54 | +0.70 | 63.0 | -5.85 | -34.08 | 7.92 | +0.118 | +0.089 | +0.120 |
| JPM | 52 | +0.49 | 63.5 | -4.22 | -18.13 | 5.09 | +0.130 | +0.097 | +0.117 |
| MCD | 59 | +0.41 | 64.4 | -3.34 | -23.46 | 4.37 | +0.117 | +0.093 | +0.122 |
| DX-Y.NYB | 64 | +0.35 | 67.2 | -0.58 | -1.45 | 0.87 | +0.845 | +0.395 | +0.590 |
| XLI | 64 | +0.35 | 67.2 | -3.64 | -15.16 | 4.12 | +0.108 | +0.085 | +0.097 |
| XOM | 52 | +0.29 | 57.7 | -3.65 | -13.66 | 4.50 | +0.087 | +0.063 | +0.078 |
| ^FTSE | 54 | +0.28 | 72.2 | -2.97 | -10.71 | 2.83 | +0.121 | +0.099 | +0.094 |
| CVX | 50 | -0.39 | 58.0 | -5.48 | -24.74 | 7.24 | -0.069 | -0.054 | -0.071 |

### pct 5–10 (no COV) — D5 DCA-blended, risk views

#### Top 10 — **smallest** average loss (safest typical downside)

| # | Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **DX-Y.NYB** | 68 | +0.17 | 51.5 | -0.61 | -1.76 | 1.04 | +0.325 | +0.159 | +0.270 |
| 2 | **GLD** | 92 | +0.79 | 67.4 | -1.72 | -12.29 | 2.63 | +0.468 | +0.301 | +0.459 |
| 3 | **JNJ** | 93 | +0.57 | 55.9 | -1.75 | -6.82 | 3.14 | +0.363 | +0.180 | +0.323 |
| 4 | **BRK-B** | 83 | +0.51 | 61.4 | -1.77 | -4.46 | 2.28 | +0.392 | +0.222 | +0.287 |
| 5 | **^FTSE** | 90 | +0.30 | 63.3 | -1.82 | -16.97 | 2.69 | +0.144 | +0.111 | +0.164 |
| 6 | **WMT** | 77 | +0.35 | 54.5 | -1.91 | -7.25 | 2.73 | +0.199 | +0.130 | +0.186 |
| 7 | **PG** | 92 | +0.46 | 59.8 | -1.95 | -6.68 | 2.93 | +0.282 | +0.157 | +0.235 |
| 8 | **005930.KS** | 92 | +1.55 | 58.7 | -2.05 | -6.27 | 4.20 | +0.899 | +0.369 | +0.757 |
| 9 | **MSFT** | 90 | +0.69 | 54.4 | -2.26 | -8.61 | 3.50 | +0.336 | +0.198 | +0.308 |
| 10 | **CSCO** | 89 | +0.81 | 59.6 | -2.46 | -8.87 | 3.78 | +0.404 | +0.215 | +0.331 |

#### Top 10 — **smallest worst loss** (tightest left tail)

| # | Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **DX-Y.NYB** | 68 | +0.17 | 51.5 | -0.61 | -1.76 | 1.04 | +0.325 | +0.159 | +0.270 |
| 2 | **BRK-B** | 83 | +0.51 | 61.4 | -1.77 | -4.46 | 2.28 | +0.392 | +0.222 | +0.287 |
| 3 | **005930.KS** | 92 | +1.55 | 58.7 | -2.05 | -6.27 | 4.20 | +0.899 | +0.369 | +0.757 |
| 4 | **PG** | 92 | +0.46 | 59.8 | -1.95 | -6.68 | 2.93 | +0.282 | +0.157 | +0.235 |
| 5 | **JNJ** | 93 | +0.57 | 55.9 | -1.75 | -6.82 | 3.14 | +0.363 | +0.180 | +0.323 |
| 6 | **WMT** | 77 | +0.35 | 54.5 | -1.91 | -7.25 | 2.73 | +0.199 | +0.130 | +0.186 |
| 7 | **SOXX** | 88 | +0.66 | 52.3 | -2.78 | -8.03 | 4.05 | +0.275 | +0.162 | +0.235 |
| 8 | **SMH** | 78 | +0.56 | 53.8 | -2.99 | -8.38 | 4.04 | +0.218 | +0.137 | +0.186 |
| 9 | **COST** | 81 | +0.85 | 67.9 | -3.03 | -8.52 | 3.39 | +0.387 | +0.252 | +0.282 |
| 10 | **MSFT** | 90 | +0.69 | 54.4 | -2.26 | -8.61 | 3.50 | +0.336 | +0.198 | +0.308 |

#### Top 10 — **EV per unit of typical loss** (best gain-vs-pain)

| # | Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **005930.KS** | 92 | +1.55 | 58.7 | -2.05 | -6.27 | 4.20 | +0.899 | +0.369 | +0.757 |
| 2 | **AVGO** | 95 | +2.08 | 66.3 | -3.94 | -24.28 | 6.06 | +0.579 | +0.343 | +0.528 |
| 3 | **GLD** | 92 | +0.79 | 67.4 | -1.72 | -12.29 | 2.63 | +0.468 | +0.301 | +0.459 |
| 4 | **TSM** | 93 | +1.31 | 61.3 | -3.03 | -9.00 | 4.56 | +0.542 | +0.287 | +0.433 |
| 5 | **^TNX** | 74 | +1.24 | 60.8 | -3.00 | -10.90 | 5.09 | +0.485 | +0.243 | +0.412 |
| 6 | **META** | 102 | +1.28 | 52.9 | -3.21 | -12.71 | 5.78 | +0.442 | +0.222 | +0.400 |
| 7 | **LLY** | 75 | +1.31 | 65.3 | -3.65 | -13.41 | 5.18 | +0.447 | +0.254 | +0.360 |
| 8 | **ASML** | 87 | +1.37 | 64.4 | -3.81 | -13.22 | 5.08 | +0.437 | +0.269 | +0.359 |
| 9 | **NFLX** | 92 | +0.97 | 52.2 | -2.91 | -12.90 | 5.07 | +0.346 | +0.191 | +0.332 |
| 10 | **CSCO** | 89 | +0.81 | 59.6 | -2.46 | -8.87 | 3.78 | +0.404 | +0.215 | +0.331 |

#### Top 10 — **Sortino-like** (EV / downside σ)

| # | Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **005930.KS** | 92 | +1.55 | 58.7 | -2.05 | -6.27 | 4.20 | +0.899 | +0.369 | +0.757 |
| 2 | **AVGO** | 95 | +2.08 | 66.3 | -3.94 | -24.28 | 6.06 | +0.579 | +0.343 | +0.528 |
| 3 | **TSM** | 93 | +1.31 | 61.3 | -3.03 | -9.00 | 4.56 | +0.542 | +0.287 | +0.433 |
| 4 | **^TNX** | 74 | +1.24 | 60.8 | -3.00 | -10.90 | 5.09 | +0.485 | +0.243 | +0.412 |
| 5 | **GLD** | 92 | +0.79 | 67.4 | -1.72 | -12.29 | 2.63 | +0.468 | +0.301 | +0.459 |
| 6 | **LLY** | 75 | +1.31 | 65.3 | -3.65 | -13.41 | 5.18 | +0.447 | +0.254 | +0.360 |
| 7 | **META** | 102 | +1.28 | 52.9 | -3.21 | -12.71 | 5.78 | +0.442 | +0.222 | +0.400 |
| 8 | **ASML** | 87 | +1.37 | 64.4 | -3.81 | -13.22 | 5.08 | +0.437 | +0.269 | +0.359 |
| 9 | **CSCO** | 89 | +0.81 | 59.6 | -2.46 | -8.87 | 3.78 | +0.404 | +0.215 | +0.331 |
| 10 | **BRK-B** | 83 | +0.51 | 61.4 | -1.77 | -4.46 | 2.28 | +0.392 | +0.222 | +0.287 |

#### Top 10 — **Sharpe-like** (EV / total σ)

| # | Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **005930.KS** | 92 | +1.55 | 58.7 | -2.05 | -6.27 | 4.20 | +0.899 | +0.369 | +0.757 |
| 2 | **AVGO** | 95 | +2.08 | 66.3 | -3.94 | -24.28 | 6.06 | +0.579 | +0.343 | +0.528 |
| 3 | **GLD** | 92 | +0.79 | 67.4 | -1.72 | -12.29 | 2.63 | +0.468 | +0.301 | +0.459 |
| 4 | **TSM** | 93 | +1.31 | 61.3 | -3.03 | -9.00 | 4.56 | +0.542 | +0.287 | +0.433 |
| 5 | **ASML** | 87 | +1.37 | 64.4 | -3.81 | -13.22 | 5.08 | +0.437 | +0.269 | +0.359 |
| 6 | **LLY** | 75 | +1.31 | 65.3 | -3.65 | -13.41 | 5.18 | +0.447 | +0.254 | +0.360 |
| 7 | **COST** | 81 | +0.85 | 67.9 | -3.03 | -8.52 | 3.39 | +0.387 | +0.252 | +0.282 |
| 8 | **^TNX** | 74 | +1.24 | 60.8 | -3.00 | -10.90 | 5.09 | +0.485 | +0.243 | +0.412 |
| 9 | **V** | 100 | +0.96 | 70.0 | -3.10 | -14.15 | 4.14 | +0.381 | +0.232 | +0.310 |
| 10 | **000660.KS** | 94 | +1.37 | 57.4 | -4.23 | -20.19 | 6.17 | +0.373 | +0.222 | +0.323 |

#### Top 10 — **EV** (for cross-reference vs the risk views above)

| # | Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **AVGO** | 95 | +2.08 | 66.3 | -3.94 | -24.28 | 6.06 | +0.579 | +0.343 | +0.528 |
| 2 | **005930.KS** | 92 | +1.55 | 58.7 | -2.05 | -6.27 | 4.20 | +0.899 | +0.369 | +0.757 |
| 3 | **MU** | 93 | +1.55 | 57.0 | -5.22 | -16.68 | 7.59 | +0.369 | +0.204 | +0.297 |
| 4 | **^VIX** | 81 | +1.41 | 50.6 | -8.31 | -24.03 | 11.99 | +0.187 | +0.118 | +0.170 |
| 5 | **000660.KS** | 94 | +1.37 | 57.4 | -4.23 | -20.19 | 6.17 | +0.373 | +0.222 | +0.323 |
| 6 | **ASML** | 87 | +1.37 | 64.4 | -3.81 | -13.22 | 5.08 | +0.437 | +0.269 | +0.359 |
| 7 | **LLY** | 75 | +1.31 | 65.3 | -3.65 | -13.41 | 5.18 | +0.447 | +0.254 | +0.360 |
| 8 | **TSM** | 93 | +1.31 | 61.3 | -3.03 | -9.00 | 4.56 | +0.542 | +0.287 | +0.433 |
| 9 | **META** | 102 | +1.28 | 52.9 | -3.21 | -12.71 | 5.78 | +0.442 | +0.222 | +0.400 |
| 10 | **^TNX** | 74 | +1.24 | 60.8 | -3.00 | -10.90 | 5.09 | +0.485 | +0.243 | +0.412 |

#### Full universe — pct 5–10 (no COV), sorted by EV

| Ticker | N | EV% | Win% | Avg Loss | Worst | σ | Sortino | Sharpe | EV/\|Loss\| |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| AVGO | 95 | +2.08 | 66.3 | -3.94 | -24.28 | 6.06 | +0.579 | +0.343 | +0.528 |
| 005930.KS | 92 | +1.55 | 58.7 | -2.05 | -6.27 | 4.20 | +0.899 | +0.369 | +0.757 |
| MU | 93 | +1.55 | 57.0 | -5.22 | -16.68 | 7.59 | +0.369 | +0.204 | +0.297 |
| ^VIX | 81 | +1.41 | 50.6 | -8.31 | -24.03 | 11.99 | +0.187 | +0.118 | +0.170 |
| 000660.KS | 94 | +1.37 | 57.4 | -4.23 | -20.19 | 6.17 | +0.373 | +0.222 | +0.323 |
| ASML | 87 | +1.37 | 64.4 | -3.81 | -13.22 | 5.08 | +0.437 | +0.269 | +0.359 |
| LLY | 75 | +1.31 | 65.3 | -3.65 | -13.41 | 5.18 | +0.447 | +0.254 | +0.360 |
| TSM | 93 | +1.31 | 61.3 | -3.03 | -9.00 | 4.56 | +0.542 | +0.287 | +0.433 |
| META | 102 | +1.28 | 52.9 | -3.21 | -12.71 | 5.78 | +0.442 | +0.222 | +0.400 |
| ^TNX | 74 | +1.24 | 60.8 | -3.00 | -10.90 | 5.09 | +0.485 | +0.243 | +0.412 |
| AMZN | 92 | +0.98 | 55.4 | -3.70 | -12.62 | 5.59 | +0.295 | +0.174 | +0.263 |
| NFLX | 92 | +0.97 | 52.2 | -2.91 | -12.90 | 5.07 | +0.346 | +0.191 | +0.332 |
| V | 100 | +0.96 | 70.0 | -3.10 | -14.15 | 4.14 | +0.381 | +0.232 | +0.310 |
| COST | 81 | +0.85 | 67.9 | -3.03 | -8.52 | 3.39 | +0.387 | +0.252 | +0.282 |
| AMD | 89 | +0.82 | 52.8 | -4.83 | -25.49 | 7.12 | +0.170 | +0.114 | +0.169 |
| CSCO | 89 | +0.81 | 59.6 | -2.46 | -8.87 | 3.78 | +0.404 | +0.215 | +0.331 |
| GLD | 92 | +0.79 | 67.4 | -1.72 | -12.29 | 2.63 | +0.468 | +0.301 | +0.459 |
| CVX | 85 | +0.76 | 63.5 | -4.06 | -33.70 | 6.51 | +0.168 | +0.117 | +0.187 |
| GOOGL | 87 | +0.73 | 57.5 | -3.52 | -12.30 | 4.56 | +0.240 | +0.159 | +0.206 |
| MSFT | 90 | +0.69 | 54.4 | -2.26 | -8.61 | 3.50 | +0.336 | +0.198 | +0.308 |
| QQQ | 92 | +0.67 | 63.0 | -3.02 | -10.63 | 3.61 | +0.275 | +0.187 | +0.224 |
| SOXX | 88 | +0.66 | 52.3 | -2.78 | -8.03 | 4.05 | +0.275 | +0.162 | +0.235 |
| ^N225 | 96 | +0.64 | 61.5 | -3.29 | -18.22 | 4.52 | +0.197 | +0.141 | +0.195 |
| ORCL | 91 | +0.60 | 59.3 | -2.87 | -11.98 | 4.16 | +0.238 | +0.145 | +0.210 |
| JNJ | 93 | +0.57 | 55.9 | -1.75 | -6.82 | 3.14 | +0.363 | +0.180 | +0.323 |
| SMH | 78 | +0.56 | 53.8 | -2.99 | -8.38 | 4.04 | +0.218 | +0.137 | +0.186 |
| MCD | 86 | +0.55 | 67.4 | -3.32 | -26.14 | 4.77 | +0.164 | +0.116 | +0.166 |
| BRK-B | 83 | +0.51 | 61.4 | -1.77 | -4.46 | 2.28 | +0.392 | +0.222 | +0.287 |
| NQ=F | 76 | +0.46 | 57.9 | -3.31 | -10.62 | 4.01 | +0.170 | +0.116 | +0.140 |
| PG | 92 | +0.46 | 59.8 | -1.95 | -6.68 | 2.93 | +0.282 | +0.157 | +0.235 |
| UNH | 83 | +0.45 | 61.4 | -3.51 | -13.41 | 4.48 | +0.150 | +0.101 | +0.129 |
| ES=F | 80 | +0.37 | 60.0 | -2.62 | -13.88 | 3.33 | +0.149 | +0.112 | +0.142 |
| WMT | 77 | +0.35 | 54.5 | -1.91 | -7.25 | 2.73 | +0.199 | +0.130 | +0.186 |
| SLV | 86 | +0.34 | 59.3 | -3.12 | -28.51 | 4.64 | +0.093 | +0.073 | +0.109 |
| JPM | 87 | +0.32 | 60.9 | -3.66 | -19.93 | 4.41 | +0.096 | +0.073 | +0.088 |
| ^FTSE | 90 | +0.30 | 63.3 | -1.82 | -16.97 | 2.69 | +0.144 | +0.111 | +0.164 |
| BTC-USD | 95 | +0.29 | 52.6 | -5.54 | -32.43 | 7.69 | +0.050 | +0.038 | +0.052 |
| SMCI | 79 | +0.26 | 46.8 | -7.15 | -29.32 | 11.81 | +0.037 | +0.022 | +0.036 |
| AAPL | 96 | +0.19 | 53.1 | -3.54 | -12.68 | 4.78 | +0.064 | +0.040 | +0.054 |
| ^GDAXI | 97 | +0.19 | 62.9 | -3.00 | -23.30 | 3.99 | +0.061 | +0.047 | +0.063 |
| DX-Y.NYB | 68 | +0.17 | 51.5 | -0.61 | -1.76 | 1.04 | +0.325 | +0.159 | +0.270 |
| INTC | 100 | +0.17 | 55.0 | -4.82 | -34.19 | 6.74 | +0.035 | +0.025 | +0.035 |
| SPY | 101 | +0.15 | 63.4 | -3.08 | -14.71 | 3.28 | +0.058 | +0.046 | +0.049 |
| CAT | 86 | +0.12 | 51.2 | -3.07 | -13.27 | 4.16 | +0.043 | +0.029 | +0.040 |
| BAC | 95 | +0.11 | 49.5 | -3.27 | -13.09 | 4.49 | +0.035 | +0.025 | +0.034 |
| XOM | 87 | +0.02 | 60.9 | -5.19 | -21.11 | 5.90 | +0.004 | +0.003 | +0.003 |
| XLI | 102 | -0.22 | 50.0 | -2.69 | -18.33 | 3.84 | -0.069 | -0.058 | -0.084 |
| NVDA | 88 | -0.39 | 46.6 | -5.78 | -19.98 | 6.93 | -0.076 | -0.056 | -0.068 |
| OXY | 99 | -0.85 | 50.5 | -5.98 | -61.09 | 10.03 | -0.094 | -0.085 | -0.142 |
| TSLA | 92 | -0.89 | 45.7 | -7.49 | -43.54 | 10.72 | -0.113 | -0.083 | -0.119 |

### Compare COV vs no-COV (Signal A, pct<5)

Drops the CoV red-bar requirement. Sample sizes roughly double; the risk-adjusted
leaders are similar (V, PG, WMT, MSFT, AAPL still dominate Sortino) but the EV-ranking
changes because more average setups are admitted. Use this section when you want to
see how much edge the COV filter contributes versus the raw percentile entry.

---

## Entry & Sizing Diagnostics (Signal A: pct<5 + COV red, D5 DCA)

*Three cross-cutting checks that change entry timing and position sizing beyond
single-name EV. Generated from `backend/cache/entry_sizing_diagnostics.json`.*

### 1. Correlation Clusters & Concurrent-Firing Risk

Daily-return correlation over the last ~3 years, greedily clustered at ρ ≥ 0.60.
**Co-fire** = average number of cluster members whose Signal-A entry fires within
±1 trading day of any member's entry. High co-fire means "3 positions" is really
one concentrated bet.

| Cluster | Members | Avg co-fire | Max co-fire |
|---|---|---:|---:|
| 5-name | AAPL, QQQ, SPY, ES=F, NQ=F | 3.17 | 5 |
| 5-name | NVDA, AVGO, SMH, SOXX, TSM | 3.04 | 5 |
| 3-name | JPM, BAC, XLI | 2.14 | 3 |
| 3-name | XOM, CVX, OXY | 2.09 | 3 |
| 2-name | WMT, COST | 1.47 | 2 |
| 2-name | 005930.KS, 000660.KS | 1.47 | 2 |
| 2-name | ^GDAXI, ^FTSE | 1.63 | 2 |
| 2-name | GLD, SLV | 1.54 | 2 |

**Uncorrelated singles (26):** MSFT, GOOGL, AMZN, META, TSLA, AMD, MU, INTC, ASML, SMCI, ORCL, NFLX, MCD, PG, UNH, LLY, JNJ, BRK-B, V, CAT, CSCO, ^N225, BTC-USD, ^VIX, DX-Y.NYB, ^TNX

> **Sizing rule:** treat each cluster as **one slot**. The semis cluster
> (NVDA/AVGO/SMH/SOXX/TSM) and the index/mega-cap-beta cluster (AAPL/QQQ/SPY/ES=F/NQ=F)
> both co-fire 3+ names on the same day with max 5 — opening all of them is 3–5×
> the intended risk. Pick the best name per cluster, or split one slot's size across them.

### 2. EV Above Buy-and-Hold Baseline

`baseline_d5` = the asset's *unconditional* average 5-day return over the same window.
`edge` = signal EV − baseline. `win_edge` = signal win-rate − unconditional win-rate.
**This separates real signal alpha from just being long a drifting asset.**

| Ticker | Signal EV | Baseline D5 | **Edge** | Sig Win% | Base Win% | Win Edge |
|---|---:|---:|---:|---:|---:|---:|
| TSLA | +3.95% | +1.07% | **+2.88%** | 70.2% | 53.1% | +17.1pp |
| V | +2.26% | +0.36% | **+1.90%** | 78.9% | 58.8% | +20.1pp |
| ASML | +2.54% | +0.71% | **+1.83%** | 67.5% | 57.5% | +10.0pp |
| NFLX | +2.33% | +0.57% | **+1.76%** | 72.2% | 54.1% | +18.1pp |
| SMCI | +2.85% | +1.10% | **+1.75%** | 62.2% | 53.0% | +9.2pp |
| META | +2.17% | +0.48% | **+1.69%** | 66.7% | 56.4% | +10.3pp |
| BTC-USD | +2.32% | +0.74% | **+1.58%** | 65.0% | 53.9% | +11.1pp |
| MSFT | +2.02% | +0.48% | **+1.54%** | 75.0% | 59.2% | +15.8pp |
| PG | +1.56% | +0.19% | **+1.37%** | 65.9% | 55.6% | +10.3pp |
| ^TNX | +1.62% | +0.34% | **+1.27%** | 58.5% | 51.6% | +6.9pp |
| WMT | +1.69% | +0.44% | **+1.26%** | 68.3% | 56.6% | +11.7pp |
| AAPL | +1.78% | +0.59% | **+1.19%** | 64.5% | 58.8% | +5.7pp |
| AVGO | +2.05% | +0.85% | **+1.19%** | 66.7% | 56.8% | +9.9pp |
| LLY | +1.77% | +0.69% | **+1.08%** | 66.7% | 58.4% | +8.3pp |
| AMZN | +1.50% | +0.50% | **+1.00%** | 71.9% | 56.2% | +15.7pp |
| COST | +1.46% | +0.47% | **+0.99%** | 66.7% | 59.5% | +7.2pp |
| MU | +1.98% | +1.03% | **+0.95%** | 58.1% | 54.2% | +3.9pp |
| ^N225 | +1.24% | +0.32% | **+0.92%** | 60.5% | 56.9% | +3.6pp |
| SOXX | +1.54% | +0.67% | **+0.87%** | 63.9% | 57.9% | +6.0pp |
| AMD | +1.96% | +1.13% | **+0.83%** | 63.9% | 55.5% | +8.4pp |
| JNJ | +1.06% | +0.24% | **+0.83%** | 60.5% | 54.2% | +6.3pp |
| XOM | +1.05% | +0.29% | **+0.76%** | 63.9% | 54.1% | +9.8pp |
| UNH | +1.05% | +0.31% | **+0.74%** | 59.1% | 55.2% | +3.9pp |
| SMH | +1.43% | +0.70% | **+0.73%** | 61.5% | 58.6% | +2.9pp |
| GOOGL | +1.28% | +0.55% | **+0.72%** | 63.2% | 58.1% | +5.1pp |
| 000660.KS | +1.77% | +1.05% | **+0.72%** | 67.6% | 53.6% | +14.0pp |
| MCD | +0.96% | +0.26% | **+0.70%** | 60.0% | 57.1% | +2.9pp |
| 005930.KS | +1.32% | +0.62% | **+0.70%** | 61.8% | 53.1% | +8.7pp |
| ES=F | +0.98% | +0.30% | **+0.69%** | 70.6% | 60.8% | +9.8pp |
| CSCO | +1.08% | +0.41% | **+0.67%** | 66.7% | 57.9% | +8.8pp |
| NVDA | +1.81% | +1.16% | **+0.65%** | 59.5% | 58.8% | +0.7pp |
| CVX | +0.91% | +0.27% | **+0.63%** | 57.6% | 55.2% | +2.4pp |
| ORCL | +1.10% | +0.48% | **+0.61%** | 60.4% | 55.5% | +4.9pp |
| NQ=F | +0.96% | +0.43% | **+0.52%** | 64.5% | 60.4% | +4.1pp |
| INTC | +0.94% | +0.49% | **+0.45%** | 48.7% | 52.7% | -4.0pp |
| ^GDAXI | +0.58% | +0.19% | **+0.39%** | 70.3% | 57.5% | +12.8pp |
| GLD | +0.69% | +0.30% | **+0.39%** | 54.3% | 56.4% | -2.1pp |
| SLV | +0.81% | +0.42% | **+0.39%** | 63.3% | 54.2% | +9.1pp |
| SPY | +0.61% | +0.31% | **+0.30%** | 66.0% | 62.3% | +3.7pp |
| OXY | +0.51% | +0.28% | **+0.24%** | 58.8% | 50.1% | +8.7pp |
| DX-Y.NYB | +0.25% | +0.01% | **+0.24%** | 57.6% | 50.1% | +7.5pp |
| TSM | +0.94% | +0.71% | **+0.23%** | 55.0% | 56.2% | -1.2pp |
| XLI | +0.47% | +0.28% | **+0.19%** | 68.9% | 58.6% | +10.3pp |
| BRK-B | +0.37% | +0.26% | **+0.10%** | 65.7% | 55.5% | +10.2pp |
| QQQ | +0.53% | +0.43% | **+0.10%** | 63.4% | 60.8% | +2.6pp |
| CAT | +0.66% | +0.61% | **+0.05%** | 57.6% | 56.9% | +0.7pp |
| BAC | +0.31% | +0.31% | **+0.00%** | 60.5% | 55.0% | +5.5pp |
| ^FTSE | +0.03% | +0.10% | **-0.07%** | 64.1% | 55.7% | +8.4pp |
| JPM | +0.28% | +0.39% | **-0.11%** | 60.5% | 57.2% | +3.3pp |
| ^VIX | -1.52% | +1.48% | **-3.00%** | 47.8% | 45.3% | +2.5pp |

> **Read-out:** TSLA, V, ASML, NFLX, META carry the largest *true* edge (+1.7–2.9pp).
> **^VIX has negative edge** (−3.0%) — the signal is worse than holding. **QQQ, CAT, BAC,
> ^FTSE, JPM** add ≈0 over buy-and-hold — their headline EV is almost entirely market drift,
> not signal. Don't pay signal-level attention (or size) to a near-zero-edge name.

### 3. Max Adverse Excursion (MAE) + 200DMA Regime Split

`avg_mae` = mean of the deepest intratrade drawdown within the 5-day hold (from blended
entry). `worst_mae` = single worst. **EV>200 / WR>** = entries where blended price was
*above* its 200-day MA (uptrend); **EV<200 / WR<** = below (downtrend).

| Ticker | N | Avg MAE | Worst MAE | EV | EV >200DMA | WR> | EV <200DMA | WR< |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ^VIX | 23 | -5.62% | -18.15% | -1.52% | -5.99% | 17% | -0.07% | 56% |
| SMCI | 37 | -2.95% | -24.57% | +2.85% | +1.78% | 62% | +4.74% | 64% |
| AMD | 36 | -2.68% | -13.64% | +1.96% | +1.25% | 71% | +2.70% | 46% |
| OXY | 34 | -2.35% | -20.39% | +0.51% | +2.20% | 62% | -1.42% | 56% |
| MU | 43 | -2.21% | -16.47% | +1.98% | +1.73% | 52% | +2.46% | 65% |
| BTC-USD | 40 | -2.20% | -19.40% | +2.32% | +4.80% | 81% | -1.48% | 47% |
| CVX | 33 | -2.13% | -15.85% | +0.91% | +0.57% | 69% | +1.04% | 47% |
| CAT | 33 | -2.12% | -9.17% | +0.66% | +0.39% | 55% | +1.02% | 54% |
| AVGO | 39 | -1.93% | -23.27% | +2.05% | +2.40% | 64% | +0.35% | 57% |
| 000660.KS | 34 | -1.83% | -17.36% | +1.77% | +0.24% | 61% | +3.93% | 79% |
| INTC | 39 | -1.82% | -8.66% | +0.94% | +1.62% | 67% | +0.61% | 40% |
| MCD | 35 | -1.80% | -19.30% | +0.96% | +0.39% | 55% | +1.68% | 62% |
| JPM | 38 | -1.76% | -13.25% | +0.28% | -0.05% | 62% | +0.55% | 46% |
| ASML | 40 | -1.68% | -18.18% | +2.54% | +0.89% | 54% | +5.33% | 87% |
| UNH | 44 | -1.63% | -11.89% | +1.05% | +1.75% | 67% | +0.26% | 50% |
| BAC | 43 | -1.62% | -12.76% | +0.31% | +0.16% | 62% | +0.33% | 53% |
| SLV | 30 | -1.58% | -11.02% | +0.81% | +0.97% | 60% | +1.66% | 73% |
| AMZN | 32 | -1.42% | -11.48% | +1.50% | +0.61% | 67% | +2.44% | 71% |
| META | 39 | -1.38% | -13.86% | +2.17% | +3.07% | 73% | +0.45% | 50% |
| TSM | 40 | -1.31% | -8.66% | +0.94% | +1.25% | 58% | +0.34% | 46% |
| XOM | 36 | -1.31% | -19.10% | +1.05% | +2.76% | 76% | -0.73% | 47% |
| ^TNX | 41 | -1.30% | -50.15% | +1.62% | +1.16% | 65% | +1.94% | 50% |
| LLY | 30 | -1.22% | -7.46% | +1.77% | +1.11% | 68% | +3.45% | 67% |
| ^FTSE | 39 | -1.22% | -11.80% | +0.03% | +0.69% | 67% | -0.88% | 53% |
| SMH | 39 | -1.20% | -6.94% | +1.43% | +1.83% | 63% | +0.41% | 60% |
| SOXX | 36 | -1.17% | -6.89% | +1.54% | +1.78% | 67% | +0.48% | 50% |
| ^GDAXI | 37 | -1.13% | -12.16% | +0.58% | +1.06% | 82% | -0.95% | 36% |
| NFLX | 36 | -1.10% | -13.30% | +2.33% | +1.85% | 71% | +3.53% | 77% |
| NVDA | 37 | -1.09% | -10.79% | +1.81% | +2.01% | 64% | +1.63% | 50% |
| GOOGL | 38 | -1.04% | -11.74% | +1.28% | +1.83% | 60% | +0.12% | 64% |
| NQ=F | 31 | -1.03% | -4.42% | +0.96% | +0.65% | 56% | +2.95% | 100% |
| QQQ | 41 | -1.02% | -5.57% | +0.53% | +0.10% | 52% | +2.53% | 100% |
| COST | 36 | -0.98% | -7.15% | +1.46% | +1.21% | 69% | +3.20% | 71% |
| ^N225 | 43 | -0.94% | -12.59% | +1.24% | +1.70% | 74% | +0.87% | 50% |
| BRK-B | 35 | -0.86% | -5.48% | +0.37% | +0.70% | 71% | -0.75% | 50% |
| GLD | 35 | -0.81% | -3.35% | +0.69% | +1.17% | 63% | +0.33% | 54% |
| XLI | 45 | -0.76% | -15.16% | +0.47% | +1.31% | 82% | -1.28% | 40% |
| AAPL | 31 | -0.74% | -6.83% | +1.78% | +1.03% | 63% | +3.48% | 70% |
| ORCL | 48 | -0.71% | -10.80% | +1.10% | +0.61% | 62% | +1.83% | 65% |
| SPY | 47 | -0.70% | -12.54% | +0.61% | +0.84% | 65% | -1.00% | 67% |
| 005930.KS | 34 | -0.66% | -14.01% | +1.32% | +1.55% | 69% | +1.02% | 60% |
| MSFT | 40 | -0.58% | -8.00% | +2.02% | +2.09% | 76% | +1.83% | 67% |
| CSCO | 36 | -0.53% | -5.64% | +1.08% | +1.21% | 67% | +0.87% | 56% |
| ES=F | 34 | -0.41% | -3.62% | +0.98% | +0.91% | 70% | +2.12% | 75% |
| JNJ | 38 | -0.39% | -5.54% | +1.06% | +0.74% | 53% | +1.41% | 68% |
| WMT | 41 | -0.23% | -4.10% | +1.69% | +0.54% | 59% | +4.13% | 82% |
| DX-Y.NYB | 33 | -0.22% | -2.45% | +0.25% | +0.41% | 67% | +0.15% | 53% |
| TSLA | 47 | -0.21% | -13.21% | +3.95% | +6.99% | 83% | +2.48% | 67% |
| PG | 44 | -0.13% | -3.13% | +1.56% | +1.50% | 77% | +1.95% | 63% |
| V | 38 | +0.05% | -4.05% | +2.26% | +1.43% | 71% | +4.24% | 91% |

> **Two ways to use this:**
> 1. **Stops/buffer** — `avg_mae` is how far the trade typically digs against you before
>    recovering. TSLA's terminal avg loss looks tame but worst MAE is −13%; SMCI −24.6%,
>    AVGO −23%, OXY −20%. Size so worst-MAE × position ≤ your per-trade pain limit, and
>    don't place a hard stop tighter than `avg_mae` or you'll be shaken out of winners.
> 2. **Regime filter** — names where **EV<200DMA is negative** are falling knives in
>    downtrends: OXY (−1.42), BTC-USD (−1.48), XOM (−0.73), ^GDAXI (−0.95), ^FTSE (−0.88),
>    SPY (−1.00), XLI (−1.28), BRK-B (−0.75). For these, **only take the signal when price
>    is above its 200DMA.** Others (ASML, WMT, V, AAPL, NFLX, MU) actually do *better*
>    below the 200DMA — true mean-reverters you can buy into weakness.

> **Note:** the 100% WR< cells for QQQ/NQ=F are tiny-sample (very few sub-200DMA entries) —
> ignore those, not enough events.
