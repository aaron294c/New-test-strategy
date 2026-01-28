# Pullback Sweep (Top Result)

Run date: 2026-01-28

## Setup

- Universe: `AAPL, NVDA, GOOGL, MSFT, META, QQQ, SPY, BRK-B, AMZN`
- Price data: daily OHLC from Yahoo Finance via `yfinance` (auto-adjusted)
- History length requested from Yahoo: `period=10y`
- RSI-MA definition: RSI(14 Wilder) on `diff(log_returns(Close))`, then EMA(14)
- RSI-MA percentile rank:
  - Rolling percentile rank of RSI-MA
  - `pct_lookback = 252` bars (min periods 252)
- MACD-V definition (repo): `((EMA12(Close) - EMA26(Close)) / ATR(26)) * 100`, signal EMA(9)
- Backtest style for this sweep: **percentile-mapping-style fixed forward returns**
  - For each entry event, compute forward return at D3/D7/D14/D21 (close-to-close)
  - No “one position at a time” constraint; entry days are treated as independent events

Command:
`YFINANCE_CACHE_DIR=/tmp/py-yfinance python scripts/sweep_pullback_macdv_rsi.py --pct-lookback 252 --period 10y --top 1 --detail`

## Entry condition (top row)

- `macdv_val >= 100`
- `RSI-MA percentile <= 5`
- No extra filters: `rsi_cross=False hist_neg=False hist_rise=False not_risk=False`

## Aggregate results (signal-weighted)

Sample size (D7): `n=116` total events (sum across tickers below).

```
rsi_thr macdv_min rsi_cross hist_neg hist_rise not_risk D7_n D7_mean D7_median D7_win
5.000   100.000   False     False    False     False    116  1.651   1.486     67.241
```

## Per-ticker results (same entry condition)

```
ticker, horizon, trades, mean%, median%, win_rate%
AAPL, D3, 14, 1.563, 1.096, 64.3
AAPL, D7, 14, 2.064, 1.494, 64.3
AAPL, D14, 14, 1.227, 1.517, 57.1
AAPL, D21, 14, 2.105, -0.285, 50.0
NVDA, D3, 11, 3.235, 1.914, 72.7
NVDA, D7, 11, 4.817, 3.620, 72.7
NVDA, D14, 11, 8.335, 6.895, 72.7
NVDA, D21, 11, 9.567, 7.862, 81.8
GOOGL, D3, 16, 0.415, 0.926, 62.5
GOOGL, D7, 16, 1.074, 0.510, 56.2
GOOGL, D14, 16, 0.978, 1.272, 56.2
GOOGL, D21, 16, 1.383, -1.514, 43.8
MSFT, D3, 14, 0.476, 0.372, 64.3
MSFT, D7, 14, 1.451, 1.427, 71.4
MSFT, D14, 14, 0.003, 0.616, 50.0
MSFT, D21, 14, 0.600, 3.061, 57.1
META, D3, 6, -2.058, -2.538, 33.3
META, D7, 6, 2.556, 1.160, 50.0
META, D14, 6, -1.699, 0.642, 50.0
META, D21, 6, -2.950, -4.853, 33.3
QQQ, D3, 17, 0.922, 1.662, 70.6
QQQ, D7, 17, 1.600, 2.532, 70.6
QQQ, D14, 17, 2.107, 2.163, 70.6
QQQ, D21, 17, 2.381, 2.142, 70.6
SPY, D3, 14, 0.550, 1.266, 71.4
SPY, D7, 14, 1.170, 1.660, 71.4
SPY, D14, 14, 1.617, 2.180, 71.4
SPY, D21, 14, 2.854, 3.624, 85.7
BRK-B, D3, 14, -0.366, -0.284, 42.9
BRK-B, D7, 14, 0.865, 1.243, 71.4
BRK-B, D14, 14, 1.229, 2.208, 64.3
BRK-B, D21, 14, 0.234, 2.074, 57.1
AMZN, D3, 10, 0.314, 0.419, 60.0
AMZN, D7, 10, 0.105, 1.468, 70.0
AMZN, D14, 10, -0.569, -2.887, 40.0
AMZN, D21, 10, 2.296, 0.255, 50.0
```

