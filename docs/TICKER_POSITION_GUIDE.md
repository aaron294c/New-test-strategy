# Per-Ticker Position Sizing Guide

*All figures from backtested D5 returns, non-overlapping entries, RSI-MA + COV red confluence.*
*Half-Kelly sizing clamped to 5–20% guardrail. Max 3 simultaneous positions.*

## Quick Legend

| Rating | Meaning | Typical Recommended Size |
|--------|---------|--------------------------|
| ⭐⭐⭐ STRONG | Kelly ≥ 30%, win ≥ 60% | 15–20% |
| ⭐⭐ GOOD | Kelly ≥ 15%, win ≥ 52%, EV > 0 | 7–14% |
| ⭐ MARGINAL | Kelly > 0, EV > 0 | 5–7% |
| ✗ SKIP | Kelly ≤ 0 or EV ≤ 0 | 5% floor only |

> **How to size with multiple signals open:** If Signal A on NQ=F fires (20%) and Signal B on MSFT fires (14%),
> that's 34% combined — within the 60% max (3 × 20%). Both are fine to run simultaneously.

---

## Tier 1 — Primary Trading Vehicles
*These are the names you are most likely to trade.*

### NQ=F — NASDAQ Futures

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐⭐⭐ STRONG | ⭐ MARGINAL |
| Win rate | 74.1% | 52.8% |
| Avg win | +2.58% | +2.94% |
| Avg loss | -2.29% | -2.69% |
| EV per trade | +1.318% | +0.280% |
| Kelly | 51.1% | 9.5% |
| **Recommended size** | **20%** | **5%** |

> Signal A is **high conviction** — this is a core entry vehicle at this extreme.

---

### ES=F — S&P 500 Futures

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐⭐⭐ STRONG | ⭐⭐ GOOD |
| Win rate | 70.0% | 55.8% |
| Avg win | +2.0% | +2.55% |
| Avg loss | -1.86% | -2.26% |
| EV per trade | +0.847% | +0.422% |
| Kelly | 42.2% | 16.6% |
| **Recommended size** | **20%** | **8%** |

> Signal A is **high conviction** — this is a core entry vehicle at this extreme.

---

### QQQ — NASDAQ ETF

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐⭐⭐ STRONG | ⭐⭐ GOOD |
| Win rate | 68.6% | 60.4% |
| Avg win | +2.05% | +2.61% |
| Avg loss | -2.39% | -2.93% |
| EV per trade | +0.658% | +0.418% |
| Kelly | 32.1% | 16.0% |
| **Recommended size** | **16%** | **8%** |

> Signal A is **high conviction** — this is a core entry vehicle at this extreme.

---

### SPY — S&P 500 ETF

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐⭐ GOOD | ⭐ MARGINAL |
| Win rate | 65.0% | 54.3% |
| Avg win | +1.96% | +2.28% |
| Avg loss | -2.53% | -2.27% |
| EV per trade | +0.388% | +0.203% |
| Kelly | 19.8% | 8.9% |
| **Recommended size** | **10%** | **5%** |

---

### GOOGL — Alphabet / Google

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐⭐ GOOD | ⭐ MARGINAL |
| Win rate | 60.0% | 52.2% |
| Avg win | +3.62% | +3.92% |
| Avg loss | -2.74% | -3.29% |
| EV per trade | +1.077% | +0.475% |
| Kelly | 29.7% | 12.1% |
| **Recommended size** | **15%** | **6%** |

---

### NVDA — NVIDIA

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐⭐ GOOD | ⭐ MARGINAL |
| Win rate | 57.6% | 50.0% |
| Avg win | +4.9% | +5.63% |
| Avg loss | -3.53% | -5.4% |
| EV per trade | +1.326% | +0.117% |
| Kelly | 27.0% | 2.1% |
| **Recommended size** | **14%** | **5%** |

---

### AVGO — Broadcom

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐ MARGINAL | ⭐⭐⭐ STRONG |
| Win rate | 51.4% | 62.2% |
| Avg win | +4.77% | +4.55% |
| Avg loss | -3.21% | -2.9% |
| EV per trade | +0.892% | +1.737% |
| Kelly | 18.7% | 38.1% |
| **Recommended size** | **9%** | **19%** |

> Signal B also shows strong edge — the 5–15th bucket is tradeable for this name.

---

### SLV — Silver ETF

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ✗ SKIP | ✗ SKIP |
| Win rate | 46.2% | 44.4% |
| Avg win | +2.46% | +2.05% |
| Avg loss | -3.79% | -2.24% |
| EV per trade | -0.905% | -0.331% |
| Kelly | -36.8% | -16.1% |
| **Recommended size** | **5%** | **5%** |

> Signal A has negative edge — use **floor sizing only**, don't size up.

---

### GLD — Gold ETF

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ✗ SKIP | ⭐⭐ GOOD |
| Win rate | 40.0% | 54.1% |
| Avg win | +1.91% | +1.58% |
| Avg loss | -1.84% | -1.11% |
| EV per trade | -0.338% | +0.342% |
| Kelly | -17.7% | 21.7% |
| **Recommended size** | **5%** | **11%** |

> Signal A has negative edge — use **floor sizing only**, don't size up.

---

### AAPL — Apple

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐ MARGINAL | ⭐ MARGINAL |
| Win rate | 51.7% | 55.8% |
| Avg win | +3.53% | +3.92% |
| Avg loss | -2.24% | -3.68% |
| EV per trade | +0.748% | +0.561% |
| Kelly | 21.2% | 14.3% |
| **Recommended size** | **11%** | **7%** |

---

### MSFT — Microsoft

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐⭐⭐ STRONG | ⭐⭐ GOOD |
| Win rate | 73.0% | 56.8% |
| Avg win | +3.46% | +3.29% |
| Avg loss | -3.11% | -2.17% |
| EV per trade | +1.681% | +0.931% |
| Kelly | 48.6% | 28.3% |
| **Recommended size** | **20%** | **14%** |

> Signal A is **high conviction** — this is a core entry vehicle at this extreme.

---

### TSM — Taiwan Semiconductor

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐⭐ GOOD | ⭐⭐ GOOD |
| Win rate | 61.8% | 61.5% |
| Avg win | +4.02% | +3.22% |
| Avg loss | -3.55% | -3.64% |
| EV per trade | +1.129% | +0.578% |
| Kelly | 28.1% | 18.0% |
| **Recommended size** | **14%** | **9%** |

---

## Tier 2 — Secondary Trading Vehicles
*Less frequent. Trade only on high-conviction setups.*

### META — Meta / Facebook

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐⭐⭐ STRONG | ⭐⭐ GOOD |
| Win rate | 67.6% | 53.1% |
| Avg win | +4.97% | +4.87% |
| Avg loss | -5.08% | -2.1% |
| EV per trade | +1.721% | +1.601% |
| Kelly | 34.6% | 32.9% |
| **Recommended size** | **17%** | **16%** |

> Signal A is **high conviction** — this is a core entry vehicle at this extreme.

---

### TSLA — Tesla

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐⭐⭐ STRONG | ⭐⭐ GOOD |
| Win rate | 71.4% | 52.8% |
| Avg win | +7.41% | +6.68% |
| Avg loss | -3.45% | -3.83% |
| EV per trade | +4.309% | +1.722% |
| Kelly | 58.1% | 25.8% |
| **Recommended size** | **20%** | **13%** |

> Signal A is **high conviction** — this is a core entry vehicle at this extreme.

---

### BAC — Bank of America

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ✗ SKIP | ⭐ MARGINAL |
| Win rate | 42.9% | 48.0% |
| Avg win | +1.96% | +3.56% |
| Avg loss | -3.37% | -2.63% |
| EV per trade | -1.086% | +0.339% |
| Kelly | -55.4% | 9.5% |
| **Recommended size** | **5%** | **5%** |

> Signal A has negative edge — use **floor sizing only**, don't size up.

---

### CVX — Chevron

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ✗ SKIP | ✗ SKIP |
| Win rate | 56.7% | 52.5% |
| Avg win | +1.91% | +2.18% |
| Avg loss | -5.88% | -4.37% |
| EV per trade | -1.466% | -0.927% |
| Kelly | -76.8% | -42.4% |
| **Recommended size** | **5%** | **5%** |

> Signal A has negative edge — use **floor sizing only**, don't size up.

---

### NFLX — Netflix

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ✗ SKIP | ⭐⭐ GOOD |
| Win rate | 43.3% | 60.0% |
| Avg win | +3.2% | +4.36% |
| Avg loss | -3.53% | -4.01% |
| EV per trade | -0.612% | +1.010% |
| Kelly | -19.1% | 23.2% |
| **Recommended size** | **5%** | **12%** |

> Signal A has negative edge — use **floor sizing only**, don't size up.

---

### OXY — Occidental Petroleum

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ✗ SKIP | ✗ SKIP |
| Win rate | 54.5% | 48.8% |
| Avg win | +3.76% | +3.66% |
| Avg loss | -6.41% | -3.96% |
| EV per trade | -0.859% | -0.241% |
| Kelly | -22.8% | -6.6% |
| **Recommended size** | **5%** | **5%** |

> Signal A has negative edge — use **floor sizing only**, don't size up.

---

### ^FTSE — FTSE 100

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ✗ SKIP | ⭐ MARGINAL |
| Win rate | 62.5% | 49.0% |
| Avg win | +1.28% | +1.72% |
| Avg loss | -3.82% | -1.48% |
| EV per trade | -0.632% | +0.089% |
| Kelly | -49.5% | 5.2% |
| **Recommended size** | **5%** | **5%** |

> Signal A has negative edge — use **floor sizing only**, don't size up.

---

### XOM — Exxon Mobil

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ✗ SKIP | ✗ SKIP |
| Win rate | 58.1% | 55.8% |
| Avg win | +2.94% | +2.96% |
| Avg loss | -4.2% | -4.06% |
| EV per trade | -0.057% | -0.143% |
| Kelly | -1.9% | -4.8% |
| **Recommended size** | **5%** | **5%** |

> Signal A has negative edge — use **floor sizing only**, don't size up.

---

### BTC-USD — Bitcoin

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐⭐⭐ STRONG | ✗ SKIP |
| Win rate | 66.7% | 58.8% |
| Avg win | +5.29% | +5.16% |
| Avg loss | -5.52% | -8.74% |
| EV per trade | +1.686% | -0.561% |
| Kelly | 31.9% | -10.9% |
| **Recommended size** | **16%** | **5%** |

> Signal B has negative edge — only trade Signal A entries for this name.
> Signal A is **high conviction** — this is a core entry vehicle at this extreme.

---

## Tier 3 — Full Universe (Remaining Tickers)

### BRK-B — Berkshire Hathaway

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐ MARGINAL | ⭐⭐ GOOD |
| Win rate | 56.7% | 61.7% |
| Avg win | +2.11% | +1.75% |
| Avg loss | -2.58% | -1.83% |
| EV per trade | +0.077% | +0.379% |
| Kelly | 3.6% | 21.7% |
| **Recommended size** | **5%** | **11%** |

---

### WMT — Walmart

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐⭐ GOOD | ✗ SKIP |
| Win rate | 55.9% | 58.1% |
| Avg win | +3.13% | +1.81% |
| Avg loss | -1.8% | -2.83% |
| EV per trade | +0.953% | -0.135% |
| Kelly | 30.5% | -7.4% |
| **Recommended size** | **15%** | **5%** |

> Signal B has negative edge — only trade Signal A entries for this name.

---

### UNH — UnitedHealth

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐⭐ GOOD | ✗ SKIP |
| Win rate | 57.9% | 41.9% |
| Avg win | +3.24% | +2.95% |
| Avg loss | -2.8% | -3.16% |
| EV per trade | +0.699% | -0.605% |
| Kelly | 21.6% | -20.5% |
| **Recommended size** | **11%** | **5%** |

> Signal B has negative edge — only trade Signal A entries for this name.

---

### LLY — Eli Lilly

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐ MARGINAL | ⭐⭐⭐ STRONG |
| Win rate | 41.4% | 68.1% |
| Avg win | +3.16% | +4.81% |
| Avg loss | -2.19% | -3.77% |
| EV per trade | +0.022% | +2.069% |
| Kelly | 0.7% | 43.0% |
| **Recommended size** | **5%** | **20%** |

> Signal B also shows strong edge — the 5–15th bucket is tradeable for this name.

---

### ORCL — Oracle

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐ MARGINAL | ✗ SKIP |
| Win rate | 50.0% | 52.4% |
| Avg win | +3.7% | +2.27% |
| Avg loss | -2.59% | -3.94% |
| EV per trade | +0.555% | -0.686% |
| Kelly | 15.0% | -30.2% |
| **Recommended size** | **8%** | **5%** |

> Signal B has negative edge — only trade Signal A entries for this name.

---

### JPM — JP Morgan

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐ MARGINAL | ⭐ MARGINAL |
| Win rate | 58.8% | 58.0% |
| Avg win | +2.68% | +3.09% |
| Avg loss | -3.35% | -3.32% |
| EV per trade | +0.194% | +0.400% |
| Kelly | 7.2% | 12.9% |
| **Recommended size** | **5%** | **6%** |

---

### ^VIX — VIX

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ✗ SKIP | ⭐⭐ GOOD |
| Win rate | 33.3% | 58.3% |
| Avg win | +5.72% | +12.47% |
| Avg loss | -7.18% | -6.91% |
| EV per trade | -2.881% | +4.391% |
| Kelly | -50.4% | 35.2% |
| **Recommended size** | **5%** | **18%** |

> Signal A has negative edge — use **floor sizing only**, don't size up.

---

### DX-Y.NYB — US Dollar Index

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐ MARGINAL | ✗ SKIP |
| Win rate | 51.7% | 36.4% |
| Avg win | +0.84% | +0.69% |
| Avg loss | -0.59% | -0.78% |
| EV per trade | +0.147% | -0.242% |
| Kelly | 17.5% | -35.0% |
| **Recommended size** | **9%** | **5%** |

> Signal B has negative edge — only trade Signal A entries for this name.

---

### ^TNX — 10-Year Yield

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐⭐⭐ STRONG | ✗ SKIP |
| Win rate | 66.7% | 43.9% |
| Avg win | +5.28% | +3.78% |
| Avg loss | -4.79% | -3.6% |
| EV per trade | +1.925% | -0.358% |
| Kelly | 36.4% | -9.5% |
| **Recommended size** | **18%** | **5%** |

> Signal B has negative edge — only trade Signal A entries for this name.
> Signal A is **high conviction** — this is a core entry vehicle at this extreme.

---

### XLI — Industrials ETF

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐⭐ GOOD | ✗ SKIP |
| Win rate | 67.5% | 51.0% |
| Avg win | +2.4% | +2.03% |
| Avg loss | -3.21% | -2.2% |
| EV per trade | +0.580% | -0.040% |
| Kelly | 24.1% | -2.0% |
| **Recommended size** | **12%** | **5%** |

> Signal B has negative edge — only trade Signal A entries for this name.

---

### MCD — McDonald's

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ✗ SKIP | ⭐⭐ GOOD |
| Win rate | 55.2% | 63.4% |
| Avg win | +2.49% | +2.43% |
| Avg loss | -3.56% | -2.35% |
| EV per trade | -0.219% | +0.679% |
| Kelly | -8.8% | 28.0% |
| **Recommended size** | **5%** | **14%** |

> Signal A has negative edge — use **floor sizing only**, don't size up.

---

### SMH — Semiconductors ETF

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐⭐ GOOD | ✗ SKIP |
| Win rate | 54.3% | 53.5% |
| Avg win | +4.66% | +2.83% |
| Avg loss | -3.21% | -3.6% |
| EV per trade | +1.062% | -0.164% |
| Kelly | 22.8% | -5.8% |
| **Recommended size** | **11%** | **5%** |

> Signal B has negative edge — only trade Signal A entries for this name.

---

### ASML — ASML

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐ MARGINAL | ⭐ MARGINAL |
| Win rate | 51.4% | 46.5% |
| Avg win | +4.58% | +5.07% |
| Avg loss | -3.57% | -3.87% |
| EV per trade | +0.621% | +0.292% |
| Kelly | 13.6% | 5.7% |
| **Recommended size** | **7%** | **5%** |

---

### SMCI — Super Micro Computer

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐ MARGINAL | ⭐ MARGINAL |
| Win rate | 50.0% | 46.7% |
| Avg win | +7.86% | +7.76% |
| Avg loss | -6.55% | -6.63% |
| EV per trade | +0.654% | +0.081% |
| Kelly | 8.3% | 1.1% |
| **Recommended size** | **5%** | **5%** |

---

### ^GDAXI — DAX

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ✗ SKIP | ⭐ MARGINAL |
| Win rate | 60.6% | 50.0% |
| Avg win | +1.7% | +2.43% |
| Avg loss | -3.21% | -1.74% |
| EV per trade | -0.233% | +0.348% |
| Kelly | -13.7% | 14.3% |
| **Recommended size** | **5%** | **7%** |

> Signal A has negative edge — use **floor sizing only**, don't size up.

---

### ^N225 — Nikkei 225

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐⭐ GOOD | ⭐ MARGINAL |
| Win rate | 60.0% | 54.4% |
| Avg win | +3.3% | +2.83% |
| Avg loss | -2.98% | -2.86% |
| EV per trade | +0.793% | +0.231% |
| Kelly | 24.0% | 8.2% |
| **Recommended size** | **12%** | **5%** |

---

### AMZN — Amazon

| | Signal A (<5th + COV) | Signal B (5–15th + COV) |
|---|---|---|
| Rating | ⭐ MARGINAL | ⭐ MARGINAL |
| Win rate | 63.3% | 51.2% |
| Avg win | +3.67% | +5.12% |
| Avg loss | -4.86% | -3.59% |
| EV per trade | +0.540% | +0.864% |
| Kelly | 14.7% | 16.9% |
| **Recommended size** | **7%** | **8%** |

---

## Summary Table — All Tickers

| Ticker | Name | A Rating | A Rec% | B Rating | B Rec% |
|--------|------|----------|--------|----------|--------|
| **NQ=F** | NASDAQ Futures | ⭐⭐⭐ STRONG | **20%** | ⭐ MARGINAL | **5%** |
| **ES=F** | S&P 500 Futures | ⭐⭐⭐ STRONG | **20%** | ⭐⭐ GOOD | **8%** |
| **QQQ** | NASDAQ ETF | ⭐⭐⭐ STRONG | **16%** | ⭐⭐ GOOD | **8%** |
| **SPY** | S&P 500 ETF | ⭐⭐ GOOD | **10%** | ⭐ MARGINAL | **5%** |
| **GOOGL** | Alphabet / Google | ⭐⭐ GOOD | **15%** | ⭐ MARGINAL | **6%** |
| **NVDA** | NVIDIA | ⭐⭐ GOOD | **14%** | ⭐ MARGINAL | **5%** |
| **AVGO** | Broadcom | ⭐ MARGINAL | **9%** | ⭐⭐⭐ STRONG | **19%** |
| **SLV** | Silver ETF | ✗ SKIP | **5%** | ✗ SKIP | **5%** |
| **GLD** | Gold ETF | ✗ SKIP | **5%** | ⭐⭐ GOOD | **11%** |
| **AAPL** | Apple | ⭐ MARGINAL | **11%** | ⭐ MARGINAL | **7%** |
| **MSFT** | Microsoft | ⭐⭐⭐ STRONG | **20%** | ⭐⭐ GOOD | **14%** |
| **TSM** | Taiwan Semiconductor | ⭐⭐ GOOD | **14%** | ⭐⭐ GOOD | **9%** |
| **META** | Meta / Facebook | ⭐⭐⭐ STRONG | **17%** | ⭐⭐ GOOD | **16%** |
| **TSLA** | Tesla | ⭐⭐⭐ STRONG | **20%** | ⭐⭐ GOOD | **13%** |
| **BAC** | Bank of America | ✗ SKIP | **5%** | ⭐ MARGINAL | **5%** |
| **CVX** | Chevron | ✗ SKIP | **5%** | ✗ SKIP | **5%** |
| **NFLX** | Netflix | ✗ SKIP | **5%** | ⭐⭐ GOOD | **12%** |
| **OXY** | Occidental Petroleum | ✗ SKIP | **5%** | ✗ SKIP | **5%** |
| **^FTSE** | FTSE 100 | ✗ SKIP | **5%** | ⭐ MARGINAL | **5%** |
| **XOM** | Exxon Mobil | ✗ SKIP | **5%** | ✗ SKIP | **5%** |
| **BTC-USD** | Bitcoin | ⭐⭐⭐ STRONG | **16%** | ✗ SKIP | **5%** |
| **BRK-B** | Berkshire Hathaway | ⭐ MARGINAL | **5%** | ⭐⭐ GOOD | **11%** |
| **WMT** | Walmart | ⭐⭐ GOOD | **15%** | ✗ SKIP | **5%** |
| **UNH** | UnitedHealth | ⭐⭐ GOOD | **11%** | ✗ SKIP | **5%** |
| **LLY** | Eli Lilly | ⭐ MARGINAL | **5%** | ⭐⭐⭐ STRONG | **20%** |
| **ORCL** | Oracle | ⭐ MARGINAL | **8%** | ✗ SKIP | **5%** |
| **JPM** | JP Morgan | ⭐ MARGINAL | **5%** | ⭐ MARGINAL | **6%** |
| **^VIX** | VIX | ✗ SKIP | **5%** | ⭐⭐ GOOD | **18%** |
| **DX-Y.NYB** | US Dollar Index | ⭐ MARGINAL | **9%** | ✗ SKIP | **5%** |
| **^TNX** | 10-Year Yield | ⭐⭐⭐ STRONG | **18%** | ✗ SKIP | **5%** |
| **XLI** | Industrials ETF | ⭐⭐ GOOD | **12%** | ✗ SKIP | **5%** |
| **MCD** | McDonald's | ✗ SKIP | **5%** | ⭐⭐ GOOD | **14%** |
| **SMH** | Semiconductors ETF | ⭐⭐ GOOD | **11%** | ✗ SKIP | **5%** |
| **ASML** | ASML | ⭐ MARGINAL | **7%** | ⭐ MARGINAL | **5%** |
| **SMCI** | Super Micro Computer | ⭐ MARGINAL | **5%** | ⭐ MARGINAL | **5%** |
| **^GDAXI** | DAX | ✗ SKIP | **5%** | ⭐ MARGINAL | **7%** |
| **^N225** | Nikkei 225 | ⭐⭐ GOOD | **12%** | ⭐ MARGINAL | **5%** |
| **AMZN** | Amazon | ⭐ MARGINAL | **7%** | ⭐ MARGINAL | **8%** |

---

## Important Observations

### Surprises from the data

**Gold (GLD) and Silver (SLV) — Signal A doesn't work:**
Both metals have *negative* Kelly in the ultra-low bucket with COV red. This seems counterintuitive
but reflects that when precious metals are extremely oversold and showing bearish momentum,
a 5-day mean reversion doesn't reliably follow. GLD Signal B (5–15th pct) does work — 11% rec.
SLV has no edge in either bucket at D5.

**TSLA Signal A is outstanding (20% cap):**
71.4% win rate, +4.31% EV, Kelly=58.1%. When TSLA is at its most oversold *and* COV fires red,
it mean-reverts powerfully within 5 days. This is your highest-edge single-name entry.

**META works in *both* signal buckets:**
Signal A: 17% rec. Signal B: 16% rec (2.32x reward:risk ratio). META has unusually asymmetric
wins vs losses in the 5–15th percentile zone.

**NFLX — skip Signal A, good Signal B:**
Signal A has negative edge. Signal B (5–15th pct) has 60% win, +1.01% EV → 12% rec.
The mid-range oversold entry is where Netflix mean-reverts, not the extreme level.

**NQ=F and MSFT are your two most reliable Signal A names:**
Both cap at 20% with Kelly >48%. When NASDAQ futures or MSFT hit ultra-low *and* COV fires,
the historical edge is near-maximum. These are your highest conviction entries.