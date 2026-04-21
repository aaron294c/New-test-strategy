# RSI-MA + CoV Confluence Backtest

- Universe size: **31**
- Symbols with ≥10 confluence events: **31**
- Symbols below event floor: **0**
- Entry trigger: RSI-MA percentile ≤ 5.0%
- Confluence (B): Fisher-z dir_metric ≤ −1.3 on the entry bar
- A = RSI-MA only, B = RSI-MA + red CoV bar

| symbol | events_A | events_B | wr_D5_A | wr_D5_B | wr_D21_A | wr_D21_B | med_D21_A | med_D21_B | medDD_A | medDD_B | status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| AAPL | 49 | 33 | 49.0 | 60.6 | 59.2 | 66.7 | +0.91 | +3.12 | -6.40 | -5.52 | ok |
| MSFT | 53 | 28 | 56.6 | 64.3 | 49.1 | 57.1 | -0.06 | +1.68 | -6.09 | -3.80 | ok |
| NVDA | 43 | 20 | 76.7 | 80.0 | 76.7 | 80.0 | +5.76 | +3.44 | -9.39 | -9.39 | ok |
| GOOGL | 52 | 26 | 71.2 | 69.2 | 57.7 | 61.5 | +2.66 | +5.02 | -5.31 | -4.79 | ok |
| AMZN | 51 | 34 | 60.8 | 58.8 | 68.6 | 67.6 | +2.16 | +2.41 | -5.48 | -5.57 | ok |
| META | 49 | 26 | 53.1 | 57.7 | 55.1 | 57.7 | +2.87 | +4.37 | -10.37 | -10.37 | ok |
| QQQ | 44 | 23 | 65.9 | 69.6 | 70.5 | 65.2 | +2.54 | +1.61 | -4.48 | -4.48 | ok |
| SPY | 44 | 29 | 72.7 | 75.9 | 79.5 | 82.8 | +2.62 | +2.51 | -2.62 | -3.11 | ok |
| GLD | 43 | 22 | 55.8 | 31.8 | 79.1 | 68.2 | +3.06 | +2.87 | -3.03 | -2.95 | ok |
| SLV | 45 | 23 | 57.8 | 56.5 | 71.1 | 65.2 | +3.93 | +3.75 | -5.61 | -4.71 | ok |
| TSLA | 47 | 32 | 48.9 | 56.2 | 44.7 | 53.1 | -3.48 | +0.14 | -14.34 | -15.02 | ok |
| NFLX | 44 | 27 | 47.7 | 48.1 | 54.5 | 48.1 | +0.79 | -0.68 | -9.46 | -9.54 | ok |
| BRK-B | 57 | 30 | 61.4 | 53.3 | 66.7 | 66.7 | +1.94 | +1.77 | -3.06 | -4.13 | ok |
| WMT | 46 | 25 | 56.5 | 56.0 | 69.6 | 60.0 | +3.32 | +1.24 | -3.61 | -5.36 | ok |
| UNH | 54 | 40 | 48.1 | 45.0 | 51.9 | 50.0 | +1.05 | +0.57 | -6.70 | -5.68 | ok |
| AVGO | 44 | 25 | 63.6 | 68.0 | 81.8 | 80.0 | +9.33 | +8.34 | -7.99 | -7.85 | ok |
| LLY | 57 | 28 | 50.9 | 60.7 | 84.2 | 75.0 | +6.15 | +6.61 | -7.24 | -9.01 | ok |
| TSM | 52 | 34 | 65.4 | 61.8 | 67.3 | 70.6 | +5.07 | +5.86 | -6.94 | -6.86 | ok |
| ORCL | 56 | 38 | 53.6 | 63.2 | 62.5 | 68.4 | +5.71 | +6.12 | -10.67 | -8.24 | ok |
| OXY | 49 | 32 | 65.3 | 59.4 | 49.0 | 43.8 | -0.26 | -2.33 | -7.63 | -7.92 | ok |
| XOM | 49 | 27 | 65.3 | 66.7 | 63.3 | 74.1 | +1.42 | +1.61 | -5.20 | -5.55 | ok |
| CVX | 61 | 35 | 45.9 | 45.7 | 57.4 | 54.3 | +1.10 | +0.52 | -5.50 | -5.10 | ok |
| JPM | 41 | 28 | 56.1 | 57.1 | 53.7 | 53.6 | +0.33 | +1.59 | -4.47 | -4.09 | ok |
| BAC | 54 | 41 | 50.0 | 51.2 | 68.5 | 68.3 | +4.36 | +4.18 | -5.86 | -5.86 | ok |
| ES=F | 42 | 29 | 71.4 | 75.9 | 76.2 | 79.3 | +2.84 | +3.19 | -3.13 | -3.42 | ok |
| NQ=F | 43 | 22 | 58.1 | 59.1 | 72.1 | 63.6 | +2.15 | +1.27 | -4.39 | -4.53 | ok |
| BTC-USD | 90 | 54 | 64.4 | 61.1 | 54.4 | 53.7 | +1.92 | +0.89 | -9.13 | -9.74 | ok |
| ^VIX | 40 | 18 | 35.0 | 33.3 | 22.5 | 22.2 | -7.25 | -6.73 | -23.55 | -22.85 | ok |
| DX-Y.NYB | 59 | 30 | 62.7 | 60.0 | 49.2 | 56.7 | -0.10 | +0.91 | -1.94 | -1.72 | ok |
| ^TNX | 54 | 32 | 51.9 | 53.1 | 51.9 | 53.1 | +0.31 | +0.65 | -6.44 | -5.73 | ok |
| XLI | 42 | 30 | 64.3 | 63.3 | 64.3 | 56.7 | +2.16 | +0.70 | -3.54 | -3.56 | ok |

Per-ticker JSON: `backend/cache/{TICKER}_cov_confluence.json`

## Winners (CoV red-bar filter helps)

Score = mean(ΔWR_D5, ΔWR_D21) + Δmedian_D21. Higher = filter improved outcomes.

| rank | symbol | kept% | ΔWR_D5 | ΔWR_D21 | Δmed_D21 | score | notes |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | AAPL | 67% | +11.6 | +7.5 | +2.21 | +11.76 | mega-cap tech |
| 2 | TSLA | 68% | +7.3 | +8.4 | +3.62 | +11.50 | turns negative D21 (−3.48 → +0.14) into positive |
| 3 | MSFT | 53% | +7.7 | +8.1 | +1.74 | +9.62 | flips D21 winrate from 49% → 57% |
| 4 | ORCL | 68% | +9.6 | +5.9 | +0.41 | +8.16 | mega-cap tech |
| 5 | XOM | 55% | +1.4 | +10.8 | +0.19 | +6.28 | energy mega-cap |
| 6 | META | 53% | +4.6 | +2.6 | +1.50 | +5.11 | mega-cap tech |
| 7 | ES=F | 69% | +4.4 | +3.1 | +0.36 | +4.13 | S&P 500 futures |
| 8 | DX-Y.NYB | 51% | −2.7 | +7.5 | +1.01 | +3.41 | dollar index — long-horizon improvement |
| 9 | GOOGL | 50% | −1.9 | +3.8 | +2.36 | +3.32 | mega-cap tech |
| 10 | SPY | 66% | +3.1 | +3.2 | −0.11 | +3.06 | broad equity ETF |
| 11 | JPM | 68% | +1.0 | −0.1 | +1.26 | +1.74 | large-cap bank |
| 12 | ^TNX | 59% | +1.3 | +1.3 | +0.34 | +1.62 | 10Y Treasury yield |

**Pattern across the top 12**:
- **6 are mega-cap tech** (AAPL, MSFT, ORCL, META, GOOGL, TSLA) — i.e. names dominated by 5-day momentum + frequent vol-driven dips
- **3 are broad-market equity proxies** (SPY, ES=F, JPM)
- **3 are macro / rates / energy** (XOM, DX-Y.NYB, ^TNX)

The standouts:
- **TSLA** is the biggest single rescue: median D21 swings from −3.48% to +0.14% — the filter removes the trades where TSLA was crashing but volatility was *contracting* (i.e. the slow, no-bounce sell-off), keeping only the high-vol capitulation entries.
- **AAPL** D5 winrate jumps +11.6 pts (49% → 60.6%) on 67% of original events kept — best evidence that the filter is selecting *better* trades, not just fewer.
- **XOM** gains +10.8 pts at D21 — energy mean-reverts well after vol spikes.

## Losers (filter hurts)

GLD (−17.6 score, D5 winrate collapses 55.8 → 31.8), OXY, WMT, XLI, NQ=F, NFLX, BRK-B, SLV, BTC-USD, UNH, CVX. **Commodities and defensives consistently fall in this bucket** — for these names, RSI-MA dips already coincide with high vol, so the red-bar filter is redundant or actively throws away the calmer, more reliable mean-reversion setups.

## Takeaway

The CoV red-bar confluence is a **regime/asset-class filter, not a universal improver**. Apply it to **growth equities and broad-market indices**; do not apply it to **commodity-linked or defensive names**. A practical rule would be a per-ticker switch in your live signal layer: enable confluence for the 12 top-ranked symbols, disable for the rest.

## D5 performance — all 31 symbols (set B = RSI-MA + CoV red bar)

Sorted by best D5 median return. `eB` = number of B-set events over the 5-year window (≈ ÷5 for per-year). `wr` = winrate %, `med` = median % return, `ret/day` = `med5_B / 5`.

| sym | eB | wr5_A | wr5_B | ΔWR | med5_A | med5_B | Δmed | ret/day |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| NVDA | 20 | 76.7 | 80.0 | +3.3 | +3.43 | +3.45 | +0.02 | +0.690% |
| AVGO | 25 | 63.6 | 68.0 | +4.4 | +3.02 | +3.07 | +0.05 | +0.614% |
| SLV | 23 | 57.8 | 56.5 | −1.3 | +1.46 | +2.48 | +1.02 | +0.495% |
| GOOGL | 26 | 71.2 | 69.2 | −1.9 | +1.90 | +2.16 | +0.26 | +0.432% |
| QQQ | 23 | 65.9 | 69.6 | +3.7 | +0.99 | +2.10 | +1.11 | +0.420% |
| ORCL | 38 | 53.6 | 63.2 | +9.6 | +0.39 | +2.04 | +1.64 | +0.408% |
| TSM | 34 | 65.4 | 61.8 | −3.6 | +1.57 | +1.85 | +0.29 | +0.371% |
| TSLA | 32 | 48.9 | 56.2 | +7.3 | −0.14 | +1.85 | +2.00 | +0.371% |
| BTC-USD | 54 | 64.4 | 61.1 | −3.3 | +1.55 | +1.58 | +0.03 | +0.316% |
| NQ=F | 22 | 58.1 | 59.1 | +1.0 | +0.66 | +1.54 | +0.88 | +0.308% |
| LLY | 28 | 50.9 | 60.7 | +9.8 | +0.38 | +1.52 | +1.15 | +0.305% |
| AMZN | 34 | 60.8 | 58.8 | −2.0 | +1.36 | +1.44 | +0.09 | +0.289% |
| XOM | 27 | 65.3 | 66.7 | +1.4 | +1.42 | +1.42 | +0.00 | +0.284% |
| OXY | 32 | 65.3 | 59.4 | −5.9 | +1.47 | +1.37 | −0.10 | +0.274% |
| AAPL | 33 | 49.0 | 60.6 | +11.6 | −0.14 | +1.36 | +1.50 | +0.272% |
| SPY | 29 | 72.7 | 75.9 | +3.1 | +0.96 | +0.96 | −0.00 | +0.191% |
| META | 26 | 53.1 | 57.7 | +4.6 | +0.58 | +0.90 | +0.32 | +0.181% |
| MSFT | 28 | 56.6 | 64.3 | +7.7 | +0.40 | +0.89 | +0.49 | +0.179% |
| ES=F | 29 | 71.4 | 75.9 | +4.4 | +0.89 | +0.89 | +0.00 | +0.178% |
| XLI | 30 | 64.3 | 63.3 | −1.0 | +0.73 | +0.60 | −0.13 | +0.121% |
| WMT | 25 | 56.5 | 56.0 | −0.5 | +0.58 | +0.46 | −0.12 | +0.092% |
| JPM | 28 | 56.1 | 57.1 | +1.0 | +0.59 | +0.45 | −0.14 | +0.091% |
| BRK-B | 30 | 61.4 | 53.3 | −8.1 | +0.82 | +0.39 | −0.43 | +0.078% |
| DX-Y.NYB | 30 | 62.7 | 60.0 | −2.7 | +0.40 | +0.35 | −0.05 | +0.070% |
| BAC | 41 | 50.0 | 51.2 | +1.2 | +0.07 | +0.19 | +0.13 | +0.039% |
| ^TNX | 32 | 51.9 | 53.1 | +1.3 | +0.08 | +0.11 | +0.03 | +0.022% |
| CVX | 35 | 45.9 | 45.7 | −0.2 | −0.55 | −0.07 | +0.48 | −0.014% |
| UNH | 40 | 48.1 | 45.0 | −3.1 | −0.08 | −0.45 | −0.38 | −0.091% |
| NFLX | 27 | 47.7 | 48.1 | +0.4 | −0.55 | −0.48 | +0.07 | −0.096% |
| GLD | 22 | 55.8 | 31.8 | −24.0 | +0.48 | −0.77 | −1.25 | −0.155% |
| ^VIX | 18 | 35.0 | 33.3 | −1.7 | −2.20 | −2.46 | −0.26 | −0.493% |

### D5 notable shifts vs the D21 ranking

- **NVDA and AVGO are the D5 winners** (3%+ in 5 days, ~0.6%/day) — but they barely move from the no-filter case (Δmed ≈ 0). The filter doesn't help them at D5; it's just that they were already great.
- **QQQ jumps from forgettable to strong** at D5 (+0.99% → +2.10%, +1.11pt), even though the D21-based "winners" list had QQQ as a slight loser. **D5-only QQQ is a clear win** with the filter.
- **AAPL flips sign** (−0.14% → +1.36%) — the biggest signal-quality lift in the table at D5.
- **TSLA flips sign** too (−0.14% → +1.85%) and is best traded short (D5 exit) per the earlier note.
- **GLD remains the worst case** — winrate craters 24 pts, return goes negative.

## Frequency of setups

Universe-wide over the 5-year window: **1,554 RSI-MA-only setups → 921 with CoV red-bar confluence** (kept 59.3%, dropped 40.7%). Per-symbol that's roughly **9–11 setups/year (A) → 5–7 setups/year (B)** — a setup roughly every 7–10 weeks instead of monthly.

## Settings used (locked for all 31 backtests)

- RSI length 14, MA (EMA) length 14, percentile lookback 252 trading days
- Entry trigger: percentile_rank(RSI-MA) ≤ 5.0
- CoV: cv_len=5, var_scale=2.0, var_shift=0.0, ema_len=5, source=close
- Correlation: cc_lookback=5, **corr_mode=Fisher**, **sig_thresh=1.3** (≈ |Pearson r| ≥ 0.862)
- Universe: `SWING_FRAMEWORK_TICKERS` from `backend/macdv_calculator.py:341` (31 symbols), 5y daily via yfinance
- Entry rule for set B: `percentile ≤ 5` AND `dir_metric ≤ −1.3` on the entry bar (red column present)

## Reproducing

```
cd /workspaces/New-test-strategy/backend
python cov_confluence_backtest.py
```

Outputs: `backend/cache/{TICKER}_cov_confluence.json` (per-ticker A/B side-by-side) and this file (`docs/cov_confluence_summary.md`).
