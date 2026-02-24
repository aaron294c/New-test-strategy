#!/usr/bin/env python3
"""
Generate momentum regime D7 lookup table from backtest results.
Output: backend/momentum_regime_d7_stats.json

For each ticker + RSI-MA percentile bucket, stores:
- win_rate, avg_return, median_return, n_trades
when MACD-V > 100 (bullish momentum regime), 7-day holding period.
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import numpy as np
import pandas as pd
import yfinance as yf
import time
from ticker_utils import resolve_yahoo_symbol

TICKERS = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "QQQ", "SPY",
    "GLD", "SLV", "TSLA", "NFLX", "BRK-B", "WMT", "UNH", "AVGO",
    "LLY", "TSM", "ORCL", "OXY", "XOM", "CVX", "JPM", "BAC",
    "ES=F", "NQ=F", "BTC-USD", "COST", "XLI",
    "CNX1.L", "CSP1.L", "IGLS.L",
]

RSI_LENGTH = 14
MA_LENGTH = 14
LOOKBACK = 252
FAST, SLOW, SIGNAL, ATR_LEN = 12, 26, 9, 26

# Percentile bucket ranges matching the live table's cohort ranges
BUCKET_RANGES = [
    (0, 5), (5, 10), (10, 15), (15, 20), (20, 25),
    (25, 30), (30, 35), (35, 40), (40, 45), (45, 50),
    (50, 55), (55, 60), (60, 65), (65, 70), (70, 75),
    (75, 80), (80, 85), (85, 90), (90, 95), (95, 100),
]


def calc_rsi_ma(close):
    log_ret = np.log(close / close.shift(1)).fillna(0)
    delta = log_ret.diff()
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    avg_g = gains.ewm(alpha=1/RSI_LENGTH, adjust=False).mean()
    avg_l = losses.ewm(alpha=1/RSI_LENGTH, adjust=False).mean()
    rs = avg_g / avg_l
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(50)
    return rsi.ewm(span=MA_LENGTH, adjust=False).mean()


def calc_percentile_rank(series, window=LOOKBACK):
    def _rank(w):
        if len(w) < window:
            return np.nan
        cur = w.iloc[-1]
        return (w.iloc[:-1] < cur).sum() / (len(w) - 1) * 100
    return series.rolling(window=window, min_periods=window).apply(_rank)


def calc_macdv(df):
    close, high, low = df['Close'], df['High'], df['Low']
    fast_ma = close.ewm(span=FAST, adjust=False).mean()
    slow_ma = close.ewm(span=SLOW, adjust=False).mean()
    hl = high - low
    hc = (high - close.shift(1)).abs()
    lc = (low - close.shift(1)).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    atr = tr.rolling(window=ATR_LEN).mean()
    return (fast_ma - slow_ma) / atr * 100


def fetch_data(ticker):
    yahoo = resolve_yahoo_symbol(ticker)
    for attempt in range(3):
        try:
            time.sleep(0.5)
            stock = yf.Ticker(yahoo)
            data = stock.history(period="5y", auto_adjust=True)
            if data.empty:
                data = yf.download(yahoo, period="5y", progress=False, auto_adjust=True)
            if not data.empty:
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = [c[0] for c in data.columns]
                return data.dropna()
        except Exception:
            time.sleep(1)
    return pd.DataFrame()


def bucket_label(pct):
    """Return the bucket label for a given percentile value."""
    for lo, hi in BUCKET_RANGES:
        if lo <= pct < hi:
            return f"{lo}-{hi}"
    if pct >= 100:
        return "95-100"
    return None


def main():
    lookup = {}

    for ticker in TICKERS:
        print(f"  {ticker}...", end=" ", flush=True)
        data = fetch_data(ticker)
        if data.empty or len(data) < 300:
            print("SKIP")
            continue

        close = data['Close']
        rsi_ma = calc_rsi_ma(close)
        pct = calc_percentile_rank(rsi_ma)
        macdv = calc_macdv(data)
        n = len(close)

        # Collect momentum trades (MACD-V > 100) with one-shot entry, 7-day HP
        ticker_trades = {}  # bucket -> list of returns

        for lo, hi in BUCKET_RANGES:
            bk = f"{lo}-{hi}"
            ticker_trades[bk] = []
            in_bucket = False
            for i in range(n):
                p = pct.iloc[i]
                mv = macdv.iloc[i]
                if pd.isna(p) or pd.isna(mv):
                    in_bucket = False
                    continue
                if mv > 100 and lo <= p < hi:
                    if not in_bucket:
                        in_bucket = True
                        exit_idx = i + 7
                        if exit_idx < n:
                            ret = (close.iloc[exit_idx] - close.iloc[i]) / close.iloc[i] * 100
                            ticker_trades[bk].append(ret)
                else:
                    in_bucket = False

        # Build stats per bucket
        ticker_stats = {}
        for bk, rets in ticker_trades.items():
            if not rets:
                continue
            ticker_stats[bk] = {
                "n": len(rets),
                "win_rate": round(sum(1 for r in rets if r > 0) / len(rets) * 100, 1),
                "avg_return": round(np.mean(rets), 3),
                "median_return": round(np.median(rets), 3),
            }

        # Also store overall ticker-level stats (all buckets combined)
        all_rets = [r for rets in ticker_trades.values() for r in rets]
        if all_rets:
            ticker_stats["_overall"] = {
                "n": len(all_rets),
                "win_rate": round(sum(1 for r in all_rets if r > 0) / len(all_rets) * 100, 1),
                "avg_return": round(np.mean(all_rets), 3),
                "median_return": round(np.median(all_rets), 3),
            }

        lookup[ticker] = ticker_stats
        overall = ticker_stats.get("_overall", {})
        print(f"n={overall.get('n', 0)} win={overall.get('win_rate', 0)}% avg={overall.get('avg_return', 0):.3f}%")

    out_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'momentum_regime_d7_stats.json')
    with open(out_path, 'w') as f:
        json.dump(lookup, f, indent=2)
    print(f"\nSaved to {out_path}")


if __name__ == '__main__':
    main()
