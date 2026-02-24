#!/usr/bin/env python3
"""
Combined filter: MACD-V >= -50 (exclude bearish momentum only).
Compare against baseline (no filter).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import numpy as np
import pandas as pd
import yfinance as yf
import time
from datetime import datetime
from ticker_utils import resolve_yahoo_symbol

TICKERS = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "QQQ", "SPY",
    "GLD", "SLV", "TSLA", "NFLX", "BRK-B", "WMT", "UNH", "AVGO",
    "LLY", "TSM", "ORCL", "OXY", "XOM", "CVX", "JPM", "BAC",
    "ES=F", "NQ=F", "BTC-USD", "COST", "XLI",
    "CNX1.L", "CSP1.L", "IGLS.L",
]

HOLDING_PERIODS = [7, 14, 21]
PERCENTILE_BUCKETS = [
    (0, 5), (5, 10), (10, 15), (15, 20), (20, 25),
    (25, 30), (30, 35), (35, 40), (40, 45), (45, 50),
]
RSI_LENGTH = 14
MA_LENGTH = 14
LOOKBACK = 252
FAST, SLOW, SIGNAL, ATR_LEN = 12, 26, 9, 26


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
        except Exception as e:
            print(f"  Attempt {attempt+1} failed for {ticker}: {e}")
            time.sleep(1)
    return pd.DataFrame()


def generate_trades(percentile, macdv, close, filter_fn):
    """One-shot trades with arbitrary filter function."""
    trades = []
    n = len(close)
    for lo, hi in PERCENTILE_BUCKETS:
        in_bucket = False
        for i in range(n):
            pct = percentile.iloc[i]
            mv = macdv.iloc[i]
            if pd.isna(pct) or pd.isna(mv):
                in_bucket = False
                continue
            regime_ok = filter_fn(mv)
            in_range = (lo <= pct < hi)
            if regime_ok and in_range:
                if not in_bucket:
                    in_bucket = True
                    entry_price = close.iloc[i]
                    for hp in HOLDING_PERIODS:
                        exit_idx = i + hp
                        if exit_idx < n:
                            exit_price = close.iloc[exit_idx]
                            ret = (exit_price - entry_price) / entry_price * 100
                            trades.append({
                                'bucket': f"{lo}-{hi}",
                                'holding': hp,
                                'return_pct': ret,
                            })
            else:
                in_bucket = False
    return trades


def generate_baseline_trades(percentile, close):
    trades = []
    n = len(close)
    for lo, hi in PERCENTILE_BUCKETS:
        in_bucket = False
        for i in range(n):
            pct = percentile.iloc[i]
            if pd.isna(pct):
                in_bucket = False
                continue
            if lo <= pct < hi:
                if not in_bucket:
                    in_bucket = True
                    entry_price = close.iloc[i]
                    for hp in HOLDING_PERIODS:
                        exit_idx = i + hp
                        if exit_idx < n:
                            exit_price = close.iloc[exit_idx]
                            ret = (exit_price - entry_price) / entry_price * 100
                            trades.append({
                                'bucket': f"{lo}-{hi}",
                                'holding': hp,
                                'return_pct': ret,
                            })
            else:
                in_bucket = False
    return trades


def stats(rets):
    if not rets:
        return 0, 0, 0, 0
    n = len(rets)
    wr = sum(1 for r in rets if r > 0) / n * 100
    return n, wr, np.mean(rets), np.median(rets)


def run():
    print("=" * 100)
    print("COMBINED FILTER BACKTEST: MACD-V >= -50 (Exclude Bearish Momentum Only)")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tickers: {len(TICKERS)}")
    print("=" * 100)

    all_combined = []  # MACD-V >= -50
    all_baseline = []
    ticker_data = {}
    failed = []

    for ticker in TICKERS:
        print(f"  {ticker}...", end=" ", flush=True)
        data = fetch_data(ticker)
        if data.empty or len(data) < 300:
            print("SKIP")
            failed.append(ticker)
            continue

        close = data['Close']
        rsi_ma = calc_rsi_ma(close)
        pct = calc_percentile_rank(rsi_ma)
        macdv = calc_macdv(data)

        combined = generate_trades(pct, macdv, close, lambda mv: mv >= -50)
        baseline = generate_baseline_trades(pct, close)

        # Tag
        for t in combined:
            t['ticker'] = ticker
        for t in baseline:
            t['ticker'] = ticker

        all_combined.extend(combined)
        all_baseline.extend(baseline)

        c7 = [t['return_pct'] for t in combined if t['holding'] == 7]
        b7 = [t['return_pct'] for t in baseline if t['holding'] == 7]
        ticker_data[ticker] = {
            'combined_7d': stats(c7),
            'baseline_7d': stats(b7),
        }

        cn, cw, ca, cm = stats(c7)
        bn, bw, ba, bm = stats(b7)
        print(f"BL: {bn} trades {bw:.1f}% {ba:+.3f}% | Combined: {cn} trades {cw:.1f}% {ca:+.3f}%")

    # ── Aggregate tables ─────────────────────────────────────────────────

    for hp in HOLDING_PERIODS:
        print(f"\n{'='*100}")
        print(f"  {hp}-DAY HOLDING PERIOD — BUCKET BREAKDOWN")
        print(f"{'='*100}")
        print(f"  {'Bucket':<10} {'BL N':>7} {'BL Win%':>8} {'BL Avg':>9} {'BL Med':>9} │ {'Comb N':>7} {'Comb Win%':>9} {'Comb Avg':>9} {'Comb Med':>9} │ {'Δ Win':>7} {'Δ Avg':>8}")
        print(f"  {'─'*108}")

        for lo, hi in PERCENTILE_BUCKETS:
            bk = f"{lo}-{hi}"
            bl_rets = [t['return_pct'] for t in all_baseline if t['bucket'] == bk and t['holding'] == hp]
            co_rets = [t['return_pct'] for t in all_combined if t['bucket'] == bk and t['holding'] == hp]
            bn, bw, ba, bm = stats(bl_rets)
            cn, cw, ca, cm = stats(co_rets)
            dw = cw - bw if bn and cn else 0
            da = ca - ba if bn and cn else 0
            print(f"  {bk:<10} {bn:>7} {bw:>7.1f}% {ba:>8.3f}% {bm:>8.3f}% │ {cn:>7} {cw:>8.1f}% {ca:>8.3f}% {cm:>8.3f}% │ {dw:>+6.1f}pp {da:>+7.3f}%")

        # Totals
        bl_all = [t['return_pct'] for t in all_baseline if t['holding'] == hp]
        co_all = [t['return_pct'] for t in all_combined if t['holding'] == hp]
        bn, bw, ba, bm = stats(bl_all)
        cn, cw, ca, cm = stats(co_all)
        dw = cw - bw
        da = ca - ba
        print(f"  {'─'*108}")
        print(f"  {'TOTAL':<10} {bn:>7} {bw:>7.1f}% {ba:>8.3f}% {bm:>8.3f}% │ {cn:>7} {cw:>8.1f}% {ca:>8.3f}% {cm:>8.3f}% │ {dw:>+6.1f}pp {da:>+7.3f}%")

    # ── Per-ticker comparison ────────────────────────────────────────────

    print(f"\n{'='*100}")
    print(f"  PER-TICKER 7-DAY: Baseline vs Combined (MACD-V >= -50)")
    print(f"{'='*100}")
    print(f"  {'Ticker':<10} {'BL N':>7} {'BL Win%':>8} {'BL AvgR':>9} │ {'Comb N':>7} {'Comb Win%':>9} {'Comb AvgR':>10} │ {'Δ Win':>7} {'Δ AvgR':>8}")
    print(f"  {'─'*90}")

    for ticker in TICKERS:
        if ticker in failed:
            print(f"  {ticker:<10} FAILED")
            continue
        d = ticker_data[ticker]
        bn, bw, ba, bm = d['baseline_7d']
        cn, cw, ca, cm = d['combined_7d']
        dw = cw - bw if bn and cn else 0
        da = ca - ba if bn and cn else 0
        print(f"  {ticker:<10} {int(bn):>7} {bw:>7.1f}% {ba:>8.3f}% │ {int(cn):>7} {cw:>8.1f}% {ca:>9.3f}% │ {dw:>+6.1f}pp {da:>+7.3f}%")

    # Grand totals
    bl7 = [t['return_pct'] for t in all_baseline if t['holding'] == 7]
    co7 = [t['return_pct'] for t in all_combined if t['holding'] == 7]
    bn, bw, ba, bm = stats(bl7)
    cn, cw, ca, cm = stats(co7)
    print(f"  {'─'*90}")
    print(f"  {'TOTAL':<10} {int(bn):>7} {bw:>7.1f}% {ba:>8.3f}% │ {int(cn):>7} {cw:>8.1f}% {ca:>9.3f}% │ {cw-bw:>+6.1f}pp {ca-ba:>+7.3f}%")

    if failed:
        print(f"\n  Failed: {', '.join(failed)}")

    print(f"\n{'='*100}")
    print("  DONE")
    print(f"{'='*100}")


if __name__ == '__main__':
    run()
