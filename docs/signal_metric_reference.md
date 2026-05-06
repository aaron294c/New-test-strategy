# Signal Metric Reference — RSI-MA + COV (Half-Day / 4H)

Strategy **D**: 4H RSI-MA below threshold **AND** 4H COV red (dir_metric ≤ −1.3)  
Timeframe: TradingView 4H = 2 half-day bars per trading day (AM 09:30–13:30 ET, PM 13:30–16:00 ET)  
Lookback: 504 half-day bars = 1 trading year (252 days × 2 bars)  
Backtest period: ~2 years of half-day data (yfinance 1H limit)  
Forward horizons: D5 = 10 half-day bars (5 trading days), D21 = 42 half-day bars (21 trading days)

---

## SPY — Strategy D Reference Returns

| Threshold | Entries (2yr) | D5 Win% | D5 Median% | D21 Win% | D21 Median% |
|---|---:|---:|---:|---:|---:|
| **< 5th pct** | 11 | **100%** | **+1.70%** | **100%** | **+2.94%** |
| **< 10th pct** | 20 | **100%** | **+1.61%** | **100%** | **+3.29%** |
| **< 15th pct** | 25 | 96.0% | +1.54% | **100%** | +2.95% |

*Intraday confirmation (half-day bars from entry):*

| Threshold | n | 12h Win% | 24h Win% | 48h Win% |
|---|---:|---:|---:|---:|
| < 5th | 11 | 72.7% | 90.9% | 100% |
| < 10th | 20 | 60.0% | 90.0% | 100% |
| < 15th | 25 | 64.0% | 92.0% | 96.0% |

**Sweet spot: < 10th pct** — nearly doubles entries vs < 5th with no loss in D5/D21 win rate.

---

## QQQ — Strategy D Reference Returns

| Threshold | Entries (2yr) | D5 Win% | D5 Median% | D21 Win% | D21 Median% |
|---|---:|---:|---:|---:|---:|
| **< 5th pct** | 9 | **100%** | **+1.61%** | **100%** | **+4.66%** |
| **< 10th pct** | 22 | **100%** | **+1.35%** | 90.9% | +3.31% |
| **< 15th pct** | 27 | 96.3% | +1.35% | 85.2% | +3.05% |

*Intraday confirmation (half-day bars from entry):*

| Threshold | n | 12h Win% | 24h Win% | 48h Win% |
|---|---:|---:|---:|---:|
| < 5th | 9 | 55.6% | 100% | 100% |
| < 10th | 22 | 50.0% | 77.3% | 90.9% |
| < 15th | 27 | 51.9% | 77.8% | 85.2% |

**Sweet spot: < 5th pct** — 100% win rate D5 through D21 with highest median returns.  
< 10th is usable (100% D5) but D21 drops to 90.9%.

---

## How to Use

1. Summon `/rsima4h` on Telegram → see current half-day RSI-MA percentile for SPY & QQQ
2. Summon `/cov4h` on Telegram → see current half-day COV dir_metric and bar colour
3. **Both conditions must be met** (RSI-MA below threshold **AND** COV red) to match Strategy D
4. Use the tables above to set expectations for D5 and D21 returns

### Signal identification quick-ref

| Signal state | SPY action | QQQ action |
|---|---|---|
| RSI-MA <5th + COV red | High conviction buy | High conviction buy |
| RSI-MA <10th + COV red | Standard buy (SPY preferred) | Caution — D21 drops to 90.9% |
| RSI-MA <15th + COV red | Weak signal for SPY only | Not recommended for QQQ |
| RSI-MA in range, COV red | Watch — await RSI-MA confirmation | Watch |
| RSI-MA below threshold, COV neutral | Watch — await COV confirmation | Watch |

---

## Strategy C Reference (Daily RSI-MA + 4H COV red, daily forward returns)

For completeness — daily bars entry, daily forward returns.

### SPY — Strategy C

| Threshold | n | D5 Win% | D5 Med% | D21 Win% | D21 Med% |
|---|---:|---:|---:|---:|---:|
| < 5th | 11 | 100% | +2.61% | 100% | +4.29% |
| < 10th | 20 | 80% | +1.74% | 80% | +3.63% |
| < 15th | 31 | 80.6% | +1.45% | 77.4% | +2.94% |

### QQQ — Strategy C

| Threshold | n | D5 Win% | D5 Med% | D21 Win% | D21 Med% |
|---|---:|---:|---:|---:|---:|
| < 5th | 12 | 75% | +1.74% | 58.3% | +2.27% |
| < 10th | 18 | 77.8% | +1.49% | 72.2% | +3.33% |
| < 15th | 31 | 71.0% | +1.30% | 74.2% | +2.87% |

---

*Generated: 2026-05-06 | Script: `scripts/rsima_cov_4h_backtest.py`*
