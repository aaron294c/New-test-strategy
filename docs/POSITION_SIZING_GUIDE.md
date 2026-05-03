# Position Sizing Guide — RSI-MA + COV Confluence Strategy

*Generated: 2026-05-03 · Universe: 38 tickers · D5 holding period*

## Signal Definitions

| Label | RSI-MA Percentile Condition | COV Condition | Strength |
|-------|-----------------------------|---------------|----------|
| **A — Ultra-Low** | < 5th percentile | Red bar (Fisher dir_metric ≤ −1.3) | Strongest |
| **B — Low** | 5th–15th percentile | Red bar (Fisher dir_metric ≤ −1.3) | Strong |

Both conditions fire **unconditionally** — no additional filters required.
COV red bar = coefficient-of-variation indicator with Fisher-z correlation ≤ −1.3,
indicating negative momentum confirmation with statistical significance.

---

## Signal A — Ultra-Low (<5th pct)

### Aggregate Statistics
*Median across 38 tickers with ≥ 8 qualifying trades*

| Metric | RSI-MA Only | RSI-MA + COV Red | Improvement |
|--------|-------------|-----------------|-------------|
| Sample trades (median) | 44 | 34 | — |
| Win rate | 58.8% | **57.8%** | -1.0pp |
| Loss rate | 41.2% | 42.2% | — |
| Avg win (D5) | +3.17% | **+3.22%** | +0.1pp |
| Avg loss (D5) | -3.18% | **-3.28%** | -0.1pp |
| Reward:Risk ratio | 1.02x | **1.06x** | — |
| Expected value D5 | +0.500% | **+0.600%** | +0.1pp |
| Binary Kelly (full) | — | **18.1%** | — |

### Position Sizing Recommendation

| Sizing Step | Value | Notes |
|-------------|-------|-------|
| Full Kelly | 18.1% | Theoretical optimal — too aggressive |
| **Half-Kelly** | **9.1%** | Standard practical recommendation |
| **Guardrail-capped** | **9.1%** | Half-Kelly clamped to [5%, 20%] |
| Max simultaneous trades | 3 | Per operational experience |
| Max total exposure | 27% | 9% × 3 positions |

> Half-Kelly falls within guardrails — no adjustment needed.

---

## Signal B — Low (5–15th pct)

### Aggregate Statistics
*Median across 38 tickers with ≥ 8 qualifying trades*

| Metric | RSI-MA Only | RSI-MA + COV Red | Improvement |
|--------|-------------|-----------------|-------------|
| Sample trades (median) | 84 | 44 | — |
| Win rate | 55.5% | **53.3%** | -2.2pp |
| Loss rate | 44.5% | 46.7% | — |
| Avg win (D5) | +3.00% | **+3.02%** | +0.0pp |
| Avg loss (D5) | -3.01% | **-3.23%** | -0.2pp |
| Reward:Risk ratio | 1.08x | **1.04x** | — |
| Expected value D5 | +0.250% | **+0.320%** | +0.1pp |
| Binary Kelly (full) | — | **9.5%** | — |

### Position Sizing Recommendation

| Sizing Step | Value | Notes |
|-------------|-------|-------|
| Full Kelly | 9.5% | Theoretical optimal — too aggressive |
| **Half-Kelly** | **4.8%** | Standard practical recommendation |
| **Guardrail-capped** | **5.0%** | Half-Kelly clamped to [5%, 20%] |
| Max simultaneous trades | 3 | Per operational experience |
| Max total exposure | 15% | 5% × 3 positions |

> **Note:** Half-Kelly (4.8%) is below the 5% floor. Minimum position of **5.0%** applied.

---

## Per-Ticker Detail

### A — Ultra-Low (<5th pct) — RSI-MA + COV Red (D5)

| Ticker | N | Win% | Avg Win | Avg Loss | EV | RR | Kelly | **Rec%** |
|--------|---|------|---------|----------|----|----|---------|----|
| ES=F | 30 | 70.0% | +2.00% | -1.86% | +0.847% | 1.08x | 42.2% | **20%** |
| MSFT | 37 | 73.0% | +3.46% | -3.11% | +1.681% | 1.11x | 48.6% | **20%** |
| NQ=F | 27 | 74.1% | +2.58% | -2.29% | +1.318% | 1.13x | 51.1% | **20%** |
| TSLA | 42 | 71.4% | +7.41% | -3.45% | +4.309% | 2.15x | 58.1% | **20%** |
| ^TNX | 36 | 66.7% | +5.28% | -4.79% | +1.925% | 1.10x | 36.4% | **18%** |
| META | 34 | 67.6% | +4.97% | -5.08% | +1.721% | 0.98x | 34.6% | **17%** |
| QQQ | 35 | 68.6% | +2.05% | -2.39% | +0.658% | 0.86x | 32.1% | **16%** |
| BTC-USD | 36 | 66.7% | +5.29% | -5.52% | +1.686% | 0.96x | 31.9% | **16%** |
| WMT | 34 | 55.9% | +3.13% | -1.80% | +0.953% | 1.74x | 30.5% | **15%** |
| GOOGL | 35 | 60.0% | +3.62% | -2.74% | +1.077% | 1.32x | 29.7% | **15%** |
| TSM | 34 | 61.8% | +4.02% | -3.55% | +1.129% | 1.13x | 28.1% | **14%** |
| NVDA | 33 | 57.6% | +4.90% | -3.53% | +1.326% | 1.39x | 27.0% | **14%** |
| XLI | 40 | 67.5% | +2.40% | -3.21% | +0.580% | 0.75x | 24.1% | **12%** |
| ^N225 | 40 | 60.0% | +3.30% | -2.98% | +0.793% | 1.11x | 24.0% | **12%** |
| SMH | 35 | 54.3% | +4.66% | -3.21% | +1.062% | 1.45x | 22.8% | **11%** |
| UNH | 38 | 57.9% | +3.24% | -2.80% | +0.699% | 1.16x | 21.6% | **11%** |
| AAPL | 29 | 51.7% | +3.53% | -2.24% | +0.748% | 1.58x | 21.2% | **11%** |
| SPY | 40 | 65.0% | +1.96% | -2.53% | +0.388% | 0.77x | 19.8% | **10%** |
| AVGO | 35 | 51.4% | +4.77% | -3.21% | +0.892% | 1.48x | 18.7% | **9%** |
| DX-Y.NYB | 29 | 51.7% | +0.84% | -0.59% | +0.147% | 1.41x | 17.5% | **9%** |
| ORCL | 40 | 50.0% | +3.70% | -2.59% | +0.555% | 1.43x | 15.0% | **8%** |
| AMZN | 30 | 63.3% | +3.67% | -4.86% | +0.540% | 0.75x | 14.7% | **7%** |
| ASML | 35 | 51.4% | +4.58% | -3.57% | +0.621% | 1.28x | 13.6% | **7%** |
| BAC | 35 | 42.9% | +1.96% | -3.37% | -1.086% | 0.58x | -55.4% | **5%** |
| BRK-B | 30 | 56.7% | +2.11% | -2.58% | +0.077% | 0.82x | 3.6% | **5%** |
| CVX | 30 | 56.7% | +1.91% | -5.88% | -1.466% | 0.32x | -76.8% | **5%** |
| GLD | 30 | 40.0% | +1.91% | -1.84% | -0.338% | 1.04x | -17.7% | **5%** |
| JPM | 34 | 58.8% | +2.68% | -3.35% | +0.194% | 0.80x | 7.2% | **5%** |
| LLY | 29 | 41.4% | +3.16% | -2.19% | +0.022% | 1.44x | 0.7% | **5%** |
| MCD | 29 | 55.2% | +2.49% | -3.56% | -0.219% | 0.70x | -8.8% | **5%** |
| NFLX | 30 | 43.3% | +3.20% | -3.53% | -0.612% | 0.91x | -19.1% | **5%** |
| OXY | 33 | 54.5% | +3.76% | -6.41% | -0.859% | 0.59x | -22.8% | **5%** |
| SLV | 26 | 46.2% | +2.46% | -3.79% | -0.905% | 0.65x | -36.8% | **5%** |
| SMCI | 36 | 50.0% | +7.86% | -6.55% | +0.654% | 1.20x | 8.3% | **5%** |
| XOM | 31 | 58.1% | +2.94% | -4.20% | -0.057% | 0.70x | -1.9% | **5%** |
| ^FTSE | 32 | 62.5% | +1.28% | -3.82% | -0.632% | 0.33x | -49.5% | **5%** |
| ^GDAXI | 33 | 60.6% | +1.70% | -3.21% | -0.233% | 0.53x | -13.7% | **5%** |
| ^VIX | 21 | 33.3% | +5.72% | -7.18% | -2.881% | 0.80x | -50.4% | **5%** |

### B — Low (5–15th pct) — RSI-MA + COV Red (D5)

| Ticker | N | Win% | Avg Win | Avg Loss | EV | RR | Kelly | **Rec%** |
|--------|---|------|---------|----------|----|----|---------|----|
| LLY | 47 | 68.1% | +4.81% | -3.77% | +2.069% | 1.27x | 43.0% | **20%** |
| AVGO | 45 | 62.2% | +4.55% | -2.90% | +1.737% | 1.57x | 38.1% | **19%** |
| ^VIX | 36 | 58.3% | +12.47% | -6.91% | +4.391% | 1.80x | 35.2% | **18%** |
| META | 49 | 53.1% | +4.87% | -2.10% | +1.601% | 2.32x | 32.9% | **16%** |
| MSFT | 44 | 56.8% | +3.29% | -2.17% | +0.931% | 1.51x | 28.3% | **14%** |
| MCD | 41 | 63.4% | +2.43% | -2.35% | +0.679% | 1.03x | 28.0% | **14%** |
| TSLA | 53 | 52.8% | +6.68% | -3.83% | +1.722% | 1.74x | 25.8% | **13%** |
| NFLX | 50 | 60.0% | +4.36% | -4.01% | +1.010% | 1.09x | 23.2% | **12%** |
| BRK-B | 47 | 61.7% | +1.75% | -1.83% | +0.379% | 0.96x | 21.7% | **11%** |
| GLD | 37 | 54.1% | +1.58% | -1.11% | +0.342% | 1.42x | 21.7% | **11%** |
| TSM | 39 | 61.5% | +3.22% | -3.64% | +0.578% | 0.88x | 18.0% | **9%** |
| AMZN | 43 | 51.2% | +5.12% | -3.59% | +0.864% | 1.42x | 16.9% | **8%** |
| ES=F | 43 | 55.8% | +2.55% | -2.26% | +0.422% | 1.13x | 16.6% | **8%** |
| QQQ | 48 | 60.4% | +2.61% | -2.93% | +0.418% | 0.89x | 16.0% | **8%** |
| AAPL | 52 | 55.8% | +3.92% | -3.68% | +0.561% | 1.07x | 14.3% | **7%** |
| ^GDAXI | 50 | 50.0% | +2.43% | -1.74% | +0.348% | 1.40x | 14.3% | **7%** |
| JPM | 50 | 58.0% | +3.09% | -3.32% | +0.400% | 0.93x | 12.9% | **6%** |
| GOOGL | 46 | 52.2% | +3.92% | -3.29% | +0.475% | 1.19x | 12.1% | **6%** |
| ASML | 43 | 46.5% | +5.07% | -3.87% | +0.292% | 1.31x | 5.7% | **5%** |
| BAC | 50 | 48.0% | +3.56% | -2.63% | +0.339% | 1.35x | 9.5% | **5%** |
| BTC-USD | 51 | 58.8% | +5.16% | -8.74% | -0.561% | 0.59x | -10.9% | **5%** |
| CVX | 40 | 52.5% | +2.18% | -4.37% | -0.927% | 0.50x | -42.4% | **5%** |
| DX-Y.NYB | 33 | 36.4% | +0.69% | -0.78% | -0.242% | 0.89x | -35.0% | **5%** |
| NQ=F | 36 | 52.8% | +2.94% | -2.69% | +0.280% | 1.09x | 9.5% | **5%** |
| NVDA | 44 | 50.0% | +5.63% | -5.40% | +0.117% | 1.04x | 2.1% | **5%** |
| ORCL | 42 | 52.4% | +2.27% | -3.94% | -0.686% | 0.58x | -30.2% | **5%** |
| OXY | 43 | 48.8% | +3.66% | -3.96% | -0.241% | 0.92x | -6.6% | **5%** |
| SLV | 45 | 44.4% | +2.05% | -2.24% | -0.331% | 0.92x | -16.1% | **5%** |
| SMCI | 45 | 46.7% | +7.76% | -6.63% | +0.081% | 1.17x | 1.1% | **5%** |
| SMH | 43 | 53.5% | +2.83% | -3.60% | -0.164% | 0.78x | -5.8% | **5%** |
| SPY | 46 | 54.3% | +2.28% | -2.27% | +0.203% | 1.00x | 8.9% | **5%** |
| UNH | 43 | 41.9% | +2.95% | -3.16% | -0.605% | 0.93x | -20.5% | **5%** |
| WMT | 43 | 58.1% | +1.81% | -2.83% | -0.135% | 0.64x | -7.4% | **5%** |
| XLI | 49 | 51.0% | +2.03% | -2.20% | -0.040% | 0.92x | -2.0% | **5%** |
| XOM | 43 | 55.8% | +2.96% | -4.06% | -0.143% | 0.73x | -4.8% | **5%** |
| ^FTSE | 51 | 49.0% | +1.72% | -1.48% | +0.089% | 1.16x | 5.2% | **5%** |
| ^N225 | 57 | 54.4% | +2.83% | -2.86% | +0.231% | 0.99x | 8.2% | **5%** |
| ^TNX | 41 | 43.9% | +3.78% | -3.60% | -0.358% | 1.05x | -9.5% | **5%** |

---

## Risk Guardrails

| Rule | Value | Why |
|------|-------|-----|
| Min position size | 5% | Below this, fees erode edge |
| Max position size | 20% | Concentration risk limit |
| Max simultaneous positions | 3 | Operational & correlation limit |
| Use half-Kelly, not full Kelly | ½ × f* | Full Kelly maximises geometric growth but is volatile; half-Kelly reduces drawdown by ~75% |
| Signal required for sizing up | Both RSI-MA pct AND COV red | Unsupported signals → floor sizing |

---

## Methodology

### Kelly Criterion (Binary Form)

```
f* = (p × b − q) / b

where:
  p = win probability  (fraction of D5 closes above entry)
  q = 1 − p           (loss probability)
  b = avg_win / |avg_loss|  (reward-to-risk ratio)
```

### Non-Overlapping Entry Logic

To prevent inflated statistics from correlated trades,
entries are blocked for 10 bars (10 trading days) after each signal.
This mirrors real-world constraints where you can't enter the same position twice.

### Expectancy Formula

```
EV = win_rate × avg_win + loss_rate × avg_loss

Positive EV = mathematical edge on each trade.
```
