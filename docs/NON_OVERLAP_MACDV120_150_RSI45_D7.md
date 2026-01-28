# Non-Overlapping Backtest: MACD-V 120–150 & RSI%≤45 (D7)

Run date: 2026-01-28

## What 'non-overlapping' means
- One active trade at a time per ticker.
- If a signal triggers on day t, you enter at that close and exit at close t+7.
- Any additional signals during the holding window are ignored.

## Results
Cell format: trades | win% | mean% | median%

| ticker | trades | win% | mean% | median% |
| --- | ---: | ---: | ---: | ---: |
| ALL | 283 | 66.1 | 1.09 | 1.11 |
| AAPL | 35 | 68.6 | 1.60 | 1.33 |
| NVDA | 29 | 72.4 | 2.60 | 2.95 |
| GOOGL | 22 | 50.0 | 0.62 | 0.33 |
| MSFT | 30 | 70.0 | 1.56 | 1.32 |
| META | 32 | 62.5 | 1.19 | 1.14 |
| QQQ | 43 | 72.1 | 0.74 | 1.56 |
| SPY | 43 | 65.1 | 0.26 | 0.60 |
| BRK-B | 22 | 54.5 | -0.06 | 0.14 |
| AMZN | 27 | 70.4 | 1.38 | 1.46 |

