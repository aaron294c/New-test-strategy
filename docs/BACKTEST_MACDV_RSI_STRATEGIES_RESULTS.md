# MACD-V + RSI-MA Strategy Backtest Results

Run date: 2026-01-28

## Data + assumptions

- Universe: `AAPL, NVDA, GOOGL, MSFT, META, QQQ, SPY, BRK-B, AMZN`
- Data: daily OHLC from Yahoo Finance via `yfinance` (auto-adjusted), ~10y lookback
- RSI-MA: RSI(14 Wilder) on `diff(log_returns(Close))`, then EMA(14), with rolling percentile rank (252 bars)
- MACD-V: `((EMA12(Close) - EMA26(Close)) / ATR26) * 100`, signal EMA(9), with the repo’s `macdv_trend` classification
- Backtest style: “event-style” (each signal day is an event); close-to-close returns; no slippage/fees; long-only
- Horizon handling: for each entry event and horizon `h ∈ {3,7,14,21}`, exit at the earliest of:
  - the strategy exit condition, or
  - `h` trading days after entry

## Caveats / likely flaws vs "Percentile Mapping" tab

- These results are **not** the same methodology as the Percentile Mapping tab (which measures *fixed forward returns* from a state). This document uses **dynamic exits**.
- Entries are **event-style** (every bar that meets the condition becomes an “event”), so events can be **clustered** during prolonged pullbacks (not a 1-position-at-a-time simulation).
- Execution is **same-day close-to-close** (implicitly assumes you can enter/exit at the signal close with no slippage).
- No fees/slippage/borrow/position sizing; long-only.
- MACD‑V uses the repo’s implementation (ATR via rolling mean, not Wilder/EMA ATR), which may differ from TradingView/Pine variants.

## Pullback strategy sweep (mapping-style fixed forward returns)

To mirror the Percentile Mapping tab more closely, run:
`YFINANCE_CACHE_DIR=/tmp/py-yfinance python scripts/sweep_pullback_macdv_rsi.py --pct-lookback 252 --period 10y --top 12`

Best aggregate D7 settings found (2026-01-28 run):
- `macdv_val >= 100` and `RSI-MA percentile <= 5` ⇒ D7 win rate ~67% and mean ~+1.65% (close-to-close forward return).

Metrics per row:
- `trades`: number of entry events that had enough forward data for that horizon
- `mean%`: mean return (percent)
- `median%`: median return (percent)
- `win_rate%`: percent of trades with return > 0

## Strategy 1: Pullback-in-trend

Entry: `macdv_trend == Bullish` AND `RSI-MA percentile <= 15`  
Exit: `RSI-MA percentile >= 50` OR `macdv_trend in {Neutral, Ranging}`

ticker, horizon, trades, mean%, median%, win_rate%
- AAPL, D3, 127, 0.136, 0.128, 50.4
- AAPL, D7, 127, 0.415, 0.018, 50.4
- AAPL, D14, 127, 0.642, 0.128, 51.2
- AAPL, D21, 127, 0.658, 0.128, 51.2
- NVDA, D3, 116, 0.676, 0.807, 56.0
- NVDA, D7, 116, 0.548, 0.557, 53.4
- NVDA, D14, 116, 0.717, 0.557, 52.6
- NVDA, D21, 116, 0.751, 0.557, 52.6
- GOOGL, D3, 124, 0.438, 0.151, 51.6
- GOOGL, D7, 123, 0.525, 0.141, 51.2
- GOOGL, D14, 123, 0.779, 1.308, 56.1
- GOOGL, D21, 123, 0.798, 1.312, 56.9
- MSFT, D3, 134, 0.075, 0.193, 55.2
- MSFT, D7, 134, 0.105, 0.379, 56.7
- MSFT, D14, 134, 0.186, 0.406, 57.5
- MSFT, D21, 134, 0.186, 0.406, 57.5
- META, D3, 122, 0.586, -0.064, 49.2
- META, D7, 122, 1.653, 0.853, 57.4
- META, D14, 122, 1.874, 1.011, 58.2
- META, D21, 122, 1.900, 1.011, 58.2
- QQQ, D3, 140, 0.576, 0.697, 65.0
- QQQ, D7, 140, 0.881, 1.259, 65.7
- QQQ, D14, 140, 0.893, 1.259, 65.0
- QQQ, D21, 140, 0.893, 1.259, 65.0
- SPY, D3, 135, 0.164, 0.291, 60.7
- SPY, D7, 135, 0.215, 0.450, 60.0
- SPY, D14, 135, 0.154, 0.291, 57.8
- SPY, D21, 135, 0.154, 0.291, 57.8
- BRK-B, D3, 117, -0.084, -0.129, 47.0
- BRK-B, D7, 117, 0.146, -0.112, 47.9
- BRK-B, D14, 117, 0.258, 0.081, 51.3
- BRK-B, D21, 117, 0.258, 0.081, 51.3
- AMZN, D3, 115, 0.205, 0.461, 53.0
- AMZN, D7, 115, 0.335, 0.802, 54.8
- AMZN, D14, 114, 0.507, 1.030, 56.1
- AMZN, D21, 114, 0.507, 1.030, 56.1

Aggregate (signal-weighted):
- ALL, D3, 1130, 0.308, 0.267, 54.5
- ALL, D7, 1129, 0.535, 0.450, 55.5
- ALL, D14, 1128, 0.663, 0.693, 56.4
- ALL, D21, 1128, 0.673, 0.703, 56.5

## Strategy 2: Range reversion

Entry: `macdv_trend == Ranging` AND `RSI-MA percentile <= 5`  
Exit: `RSI-MA percentile >= 75`

ticker, horizon, trades, mean%, median%, win_rate%
- AAPL, D3, 0, nan, nan, nan
- AAPL, D7, 0, nan, nan, nan
- AAPL, D14, 0, nan, nan, nan
- AAPL, D21, 0, nan, nan, nan
- NVDA, D3, 2, 6.307, 6.307, 100.0
- NVDA, D7, 2, 6.383, 6.383, 100.0
- NVDA, D14, 2, 10.073, 10.073, 100.0
- NVDA, D21, 2, 10.073, 10.073, 100.0
- GOOGL, D3, 5, -0.231, 0.649, 60.0
- GOOGL, D7, 5, -0.877, -1.270, 40.0
- GOOGL, D14, 5, -3.161, -2.676, 20.0
- GOOGL, D21, 5, -0.289, -2.676, 40.0
- MSFT, D3, 5, 1.020, 1.157, 80.0
- MSFT, D7, 5, 0.283, -0.845, 40.0
- MSFT, D14, 5, 0.350, 3.095, 60.0
- MSFT, D21, 5, 1.617, 3.095, 60.0
- META, D3, 3, 0.377, 2.341, 66.7
- META, D7, 3, 2.651, 6.426, 66.7
- META, D14, 3, 3.692, 6.426, 66.7
- META, D21, 3, 3.692, 6.426, 66.7
- QQQ, D3, 4, 0.963, 0.805, 50.0
- QQQ, D7, 3, 1.287, 0.950, 66.7
- QQQ, D14, 3, 2.519, 1.911, 100.0
- QQQ, D21, 3, 2.519, 1.911, 100.0
- SPY, D3, 4, -0.692, -1.090, 25.0
- SPY, D7, 4, -0.490, -1.023, 25.0
- SPY, D14, 4, 0.819, 0.326, 50.0
- SPY, D21, 4, 0.819, 0.326, 50.0
- BRK-B, D3, 9, 0.522, 0.727, 55.6
- BRK-B, D7, 8, 1.094, 1.897, 75.0
- BRK-B, D14, 8, -2.285, 1.825, 62.5
- BRK-B, D21, 8, -2.124, 1.773, 62.5
- AMZN, D3, 2, 1.983, 1.983, 100.0
- AMZN, D7, 2, 0.705, 0.705, 50.0
- AMZN, D14, 2, 3.349, 3.349, 100.0
- AMZN, D21, 2, 3.349, 3.349, 100.0

Aggregate (signal-weighted):
- ALL, D3, 34, 0.807, 0.942, 61.8
- ALL, D7, 32, 0.932, 0.696, 56.2
- ALL, D14, 32, 0.513, 1.871, 62.5
- ALL, D21, 32, 1.200, 2.083, 65.6
