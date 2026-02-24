#!/usr/bin/env python3
"""
MACD-V Regime-Filtered Percentile Mapping Backtest

Classifies each trading day into regimes using MACD-V:
  - Excluded: MACD-V < -100 (no trades)
  - Mean-Reversion: -50 <= MACD-V <= 100
  - Bullish Momentum: MACD-V > 100

Entry: RSI-MA percentile falls into bucket (one-shot, first day only)
Holding periods: 7, 14, 21 trading days
Exit: at close of holding period (no stops, no targets)

Compares against baseline Percentile Mapping (no regime filter).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import numpy as np
import pandas as pd
import yfinance as yf
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from ticker_utils import resolve_yahoo_symbol

# ── Configuration ────────────────────────────────────────────────────────────

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
LOOKBACK = 252  # 1 trading year for percentile rank

# MACD-V params
FAST = 12
SLOW = 26
SIGNAL = 9
ATR_LEN = 26


# ── Indicator Calculations ───────────────────────────────────────────────────

def calc_rsi_ma(close: pd.Series) -> pd.Series:
    """RSI-MA: EMA(14) of RSI(14) on change-of-log-returns."""
    log_ret = np.log(close / close.shift(1)).fillna(0)
    delta = log_ret.diff()
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    avg_g = gains.ewm(alpha=1 / RSI_LENGTH, adjust=False).mean()
    avg_l = losses.ewm(alpha=1 / RSI_LENGTH, adjust=False).mean()
    rs = avg_g / avg_l
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(50)
    return rsi.ewm(span=MA_LENGTH, adjust=False).mean()


def calc_percentile_rank(series: pd.Series, window: int = LOOKBACK) -> pd.Series:
    """Rolling percentile rank within a lookback window."""
    def _rank(w):
        if len(w) < window:
            return np.nan
        cur = w.iloc[-1]
        return (w.iloc[:-1] < cur).sum() / (len(w) - 1) * 100
    return series.rolling(window=window, min_periods=window).apply(_rank)


def calc_macdv(df: pd.DataFrame) -> pd.Series:
    """MACD-V = (EMA_fast - EMA_slow) / ATR * 100."""
    close = df['Close']
    high = df['High']
    low = df['Low']

    fast_ma = close.ewm(span=FAST, adjust=False).mean()
    slow_ma = close.ewm(span=SLOW, adjust=False).mean()

    hl = high - low
    hc = (high - close.shift(1)).abs()
    lc = (low - close.shift(1)).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    atr = tr.rolling(window=ATR_LEN).mean()

    macdv = (fast_ma - slow_ma) / atr * 100
    return macdv


# ── Data Fetching ────────────────────────────────────────────────────────────

def fetch_data(ticker: str) -> pd.DataFrame:
    """Fetch 5y daily OHLC via yfinance."""
    yahoo = resolve_yahoo_symbol(ticker)
    for attempt in range(3):
        try:
            time.sleep(0.5)
            stock = yf.Ticker(yahoo)
            data = stock.history(period="5y", auto_adjust=True)
            if data.empty:
                data = yf.download(yahoo, period="5y", progress=False, auto_adjust=True)
            if not data.empty:
                # flatten multi-index columns from yf.download
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = [c[0] for c in data.columns]
                data = data.dropna()
                return data
        except Exception as e:
            print(f"  Attempt {attempt+1} failed for {ticker}: {e}")
            time.sleep(1)
    return pd.DataFrame()


# ── Trade Generation ─────────────────────────────────────────────────────────

def generate_trades(percentile: pd.Series, macdv: pd.Series, close: pd.Series,
                    regime: str) -> list:
    """
    Generate one-shot trades for a given regime.

    regime='mr'  → mean-reversion: -50 <= MACD-V <= 100
    regime='mom' → bullish momentum: MACD-V > 100

    Entry on FIRST day the percentile enters a bucket (no re-entry while
    the percentile stays in the same bucket).
    """
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

            # regime filter
            if regime == 'mr':
                regime_ok = (-50 <= mv <= 100)
            else:  # mom
                regime_ok = (mv > 100)

            in_range = (lo <= pct < hi)

            if regime_ok and in_range:
                if not in_bucket:
                    # first day entering this bucket under this regime
                    in_bucket = True
                    entry_idx = i
                    entry_price = close.iloc[i]
                    for hp in HOLDING_PERIODS:
                        exit_idx = i + hp
                        if exit_idx < n:
                            exit_price = close.iloc[exit_idx]
                            ret = (exit_price - entry_price) / entry_price * 100
                            trades.append({
                                'bucket': f"{lo}-{hi}",
                                'holding': hp,
                                'entry_date': close.index[i],
                                'entry_price': entry_price,
                                'exit_price': exit_price,
                                'return_pct': ret,
                                'regime': regime,
                                'macdv_at_entry': mv,
                                'pct_at_entry': pct,
                            })
            else:
                in_bucket = False

    return trades


def generate_baseline_trades(percentile: pd.Series, close: pd.Series) -> list:
    """
    Baseline: Percentile Mapping with NO regime filter (all days tradeable).
    Same one-shot entry rule, same buckets, same holding periods.
    """
    trades = []
    n = len(close)

    for lo, hi in PERCENTILE_BUCKETS:
        in_bucket = False
        for i in range(n):
            pct = percentile.iloc[i]
            if pd.isna(pct):
                in_bucket = False
                continue

            in_range = (lo <= pct < hi)
            if in_range:
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
                                'entry_date': close.index[i],
                                'entry_price': entry_price,
                                'exit_price': exit_price,
                                'return_pct': ret,
                                'regime': 'baseline',
                                'pct_at_entry': pct,
                            })
            else:
                in_bucket = False

    return trades


# ── Aggregation ──────────────────────────────────────────────────────────────

def aggregate(trades: list) -> pd.DataFrame:
    """Aggregate trades into stats per bucket × holding period."""
    if not trades:
        return pd.DataFrame()
    df = pd.DataFrame(trades)
    grouped = df.groupby(['bucket', 'holding'])['return_pct']

    stats = grouped.agg(
        n_trades='count',
        win_rate=lambda x: (x > 0).sum() / len(x) * 100 if len(x) > 0 else 0,
        avg_return='mean',
        median_return='median',
        std_return='std',
    ).reset_index()
    stats['std_return'] = stats['std_return'].fillna(0)
    return stats


# ── Main ─────────────────────────────────────────────────────────────────────

def run_backtest():
    print("=" * 90)
    print("MACD-V REGIME-FILTERED PERCENTILE MAPPING BACKTEST")
    print(f"Tickers: {len(TICKERS)} | Holding periods: {HOLDING_PERIODS}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 90)

    all_mr_trades = []
    all_mom_trades = []
    all_baseline_trades = []
    ticker_summaries = {}
    failed_tickers = []

    for ticker in TICKERS:
        print(f"\n{'─'*60}")
        print(f"Processing {ticker}...")

        data = fetch_data(ticker)
        if data.empty or len(data) < 300:
            print(f"  SKIP: insufficient data ({len(data) if not data.empty else 0} rows)")
            failed_tickers.append(ticker)
            continue

        close = data['Close']
        rsi_ma = calc_rsi_ma(close)
        pct_rank = calc_percentile_rank(rsi_ma)
        macdv = calc_macdv(data)

        # Regime counts
        valid = macdv.dropna()
        n_excluded = (valid < -100).sum()
        n_mr = ((valid >= -50) & (valid <= 100)).sum()
        n_mom = (valid > 100).sum()
        n_gap = len(valid) - n_excluded - n_mr - n_mom  # -100 to -50 gap (no trades either per strict rules, but also > -100)
        # Actually re-check: excluded is < -100, mr is -50..100, mom is >100
        # Gap is -100..-50 which is neither excluded nor tradeable
        n_gap_zone = ((valid >= -100) & (valid < -50)).sum()

        print(f"  Data: {len(data)} days | MACD-V valid: {len(valid)}")
        print(f"  Regimes: Excluded(<-100)={n_excluded} | MR(-50..100)={n_mr} | Mom(>100)={n_mom} | Gap(-100..-50)={n_gap_zone}")

        mr_trades = generate_trades(pct_rank, macdv, close, 'mr')
        mom_trades = generate_trades(pct_rank, macdv, close, 'mom')
        baseline_trades = generate_baseline_trades(pct_rank, close)

        print(f"  Trades: MR={len(mr_trades)//len(HOLDING_PERIODS) if mr_trades else 0} | Mom={len(mom_trades)//len(HOLDING_PERIODS) if mom_trades else 0} | Baseline={len(baseline_trades)//len(HOLDING_PERIODS) if baseline_trades else 0}")

        # Tag with ticker
        for t in mr_trades:
            t['ticker'] = ticker
        for t in mom_trades:
            t['ticker'] = ticker
        for t in baseline_trades:
            t['ticker'] = ticker

        all_mr_trades.extend(mr_trades)
        all_mom_trades.extend(mom_trades)
        all_baseline_trades.extend(baseline_trades)

        # Per-ticker summary for 7-day
        mr7 = [t for t in mr_trades if t['holding'] == 7]
        mom7 = [t for t in mom_trades if t['holding'] == 7]
        bl7 = [t for t in baseline_trades if t['holding'] == 7]

        def quick_stats(trades_list):
            if not trades_list:
                return {'n': 0, 'win_rate': 0, 'avg_ret': 0, 'med_ret': 0}
            rets = [t['return_pct'] for t in trades_list]
            return {
                'n': len(rets),
                'win_rate': round(sum(1 for r in rets if r > 0) / len(rets) * 100, 1),
                'avg_ret': round(np.mean(rets), 3),
                'med_ret': round(np.median(rets), 3),
            }

        ticker_summaries[ticker] = {
            'mr_7d': quick_stats(mr7),
            'mom_7d': quick_stats(mom7),
            'baseline_7d': quick_stats(bl7),
        }

    # ── Aggregate Results ────────────────────────────────────────────────────

    mr_stats = aggregate(all_mr_trades)
    mom_stats = aggregate(all_mom_trades)
    bl_stats = aggregate(all_baseline_trades)

    # ── Print Tables ─────────────────────────────────────────────────────────

    def print_table(title, df):
        print(f"\n{'='*90}")
        print(f"  {title}")
        print(f"{'='*90}")
        if df.empty:
            print("  No trades found.")
            return
        for hp in HOLDING_PERIODS:
            subset = df[df['holding'] == hp].copy()
            if subset.empty:
                continue
            print(f"\n  Holding Period: {hp} days")
            print(f"  {'Bucket':<10} {'Trades':>7} {'Win%':>8} {'AvgRet%':>9} {'MedRet%':>9} {'Std%':>8}")
            print(f"  {'─'*52}")
            for _, row in subset.iterrows():
                print(f"  {row['bucket']:<10} {int(row['n_trades']):>7} {row['win_rate']:>7.1f}% {row['avg_return']:>8.3f}% {row['median_return']:>8.3f}% {row['std_return']:>7.3f}%")
            # totals for this HP
            all_rets_hp = [t['return_pct'] for t in (all_mr_trades if 'Mean' in title else all_mom_trades if 'Bullish' in title else all_baseline_trades) if t['holding'] == hp]
            if all_rets_hp:
                n = len(all_rets_hp)
                wr = sum(1 for r in all_rets_hp if r > 0) / n * 100
                avg = np.mean(all_rets_hp)
                med = np.median(all_rets_hp)
                std = np.std(all_rets_hp)
                print(f"  {'─'*52}")
                print(f"  {'TOTAL':<10} {n:>7} {wr:>7.1f}% {avg:>8.3f}% {med:>8.3f}% {std:>7.3f}%")

    print_table("MEAN-REVERSION REGIME RESULTS (-50 ≤ MACD-V ≤ 100)", mr_stats)
    print_table("BULLISH MOMENTUM REGIME RESULTS (MACD-V > 100)", mom_stats)
    print_table("BASELINE (No Regime Filter) RESULTS", bl_stats)

    # ── Per-Ticker 7-Day Comparison ──────────────────────────────────────────

    print(f"\n{'='*90}")
    print(f"  PER-TICKER 7-DAY COMPARISON: Baseline vs Mean-Reversion vs Bullish Momentum")
    print(f"{'='*90}")
    print(f"  {'Ticker':<10} {'BL Trades':>9} {'BL Win%':>8} {'BL AvgR':>8} │ {'MR Trades':>9} {'MR Win%':>8} {'MR AvgR':>8} │ {'Mom Trades':>10} {'Mom Win%':>9} {'Mom AvgR':>9}")
    print(f"  {'─'*110}")

    for ticker in TICKERS:
        if ticker in failed_tickers:
            print(f"  {ticker:<10} {'FAILED':>9}")
            continue
        s = ticker_summaries.get(ticker)
        if not s:
            continue
        bl = s['baseline_7d']
        mr = s['mr_7d']
        mo = s['mom_7d']
        print(f"  {ticker:<10} {bl['n']:>9} {bl['win_rate']:>7.1f}% {bl['avg_ret']:>7.3f}% │ {mr['n']:>9} {mr['win_rate']:>7.1f}% {mr['avg_ret']:>7.3f}% │ {mo['n']:>10} {mo['win_rate']:>8.1f}% {mo['avg_ret']:>8.3f}%")

    # Aggregate totals
    bl_all7 = [t['return_pct'] for t in all_baseline_trades if t['holding'] == 7]
    mr_all7 = [t['return_pct'] for t in all_mr_trades if t['holding'] == 7]
    mom_all7 = [t['return_pct'] for t in all_mom_trades if t['holding'] == 7]

    def total_line(label, rets):
        if not rets:
            return f"  {label}: 0 trades"
        n = len(rets)
        wr = sum(1 for r in rets if r > 0) / n * 100
        avg = np.mean(rets)
        med = np.median(rets)
        return f"  {label}: {n} trades | Win: {wr:.1f}% | Avg: {avg:.3f}% | Med: {med:.3f}%"

    print(f"\n  {'─'*60}")
    print(total_line("BASELINE TOTAL (7d)", bl_all7))
    print(total_line("MEAN-REVERSION TOTAL (7d)", mr_all7))
    print(total_line("BULLISH MOMENTUM TOTAL (7d)", mom_all7))

    if mr_all7 and mom_all7:
        combined = mr_all7 + mom_all7
        n = len(combined)
        wr = sum(1 for r in combined if r > 0) / n * 100
        avg = np.mean(combined)
        med = np.median(combined)
        print(f"  COMBINED MR+MOM (7d): {n} trades | Win: {wr:.1f}% | Avg: {avg:.3f}% | Med: {med:.3f}%")

    # ── Per-Ticker Bucket-Level 7-Day Detail ─────────────────────────────────

    print(f"\n{'='*90}")
    print(f"  PER-TICKER BUCKET-LEVEL 7-DAY: Mean-Reversion Regime")
    print(f"{'='*90}")

    for ticker in TICKERS:
        if ticker in failed_tickers:
            continue
        t_trades = [t for t in all_mr_trades if t['ticker'] == ticker and t['holding'] == 7]
        if not t_trades:
            continue
        print(f"\n  {ticker}")
        print(f"  {'Bucket':<10} {'N':>5} {'Win%':>8} {'AvgR%':>9} {'MedR%':>9}")
        print(f"  {'─'*42}")
        for lo, hi in PERCENTILE_BUCKETS:
            bk = f"{lo}-{hi}"
            bk_trades = [t for t in t_trades if t['bucket'] == bk]
            if not bk_trades:
                continue
            rets = [t['return_pct'] for t in bk_trades]
            n = len(rets)
            wr = sum(1 for r in rets if r > 0) / n * 100
            avg = np.mean(rets)
            med = np.median(rets)
            print(f"  {bk:<10} {n:>5} {wr:>7.1f}% {avg:>8.3f}% {med:>8.3f}%")

    print(f"\n{'='*90}")
    print(f"  PER-TICKER BUCKET-LEVEL 7-DAY: Bullish Momentum Regime")
    print(f"{'='*90}")

    for ticker in TICKERS:
        if ticker in failed_tickers:
            continue
        t_trades = [t for t in all_mom_trades if t['ticker'] == ticker and t['holding'] == 7]
        if not t_trades:
            continue
        print(f"\n  {ticker}")
        print(f"  {'Bucket':<10} {'N':>5} {'Win%':>8} {'AvgR%':>9} {'MedR%':>9}")
        print(f"  {'─'*42}")
        for lo, hi in PERCENTILE_BUCKETS:
            bk = f"{lo}-{hi}"
            bk_trades = [t for t in t_trades if t['bucket'] == bk]
            if not bk_trades:
                continue
            rets = [t['return_pct'] for t in bk_trades]
            n = len(rets)
            wr = sum(1 for r in rets if r > 0) / n * 100
            avg = np.mean(rets)
            med = np.median(rets)
            print(f"  {bk:<10} {n:>5} {wr:>7.1f}% {avg:>8.3f}% {med:>8.3f}%")

    # ── Save JSON ────────────────────────────────────────────────────────────

    output = {
        'timestamp': datetime.now().isoformat(),
        'tickers_processed': [t for t in TICKERS if t not in failed_tickers],
        'tickers_failed': failed_tickers,
        'mr_aggregate': mr_stats.to_dict('records') if not mr_stats.empty else [],
        'mom_aggregate': mom_stats.to_dict('records') if not mom_stats.empty else [],
        'baseline_aggregate': bl_stats.to_dict('records') if not bl_stats.empty else [],
        'ticker_summaries_7d': ticker_summaries,
    }

    out_path = Path(__file__).parent / 'macdv_regime_backtest_results.json'
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n  Results saved to {out_path}")

    if failed_tickers:
        print(f"\n  FAILED TICKERS: {', '.join(failed_tickers)}")

    print(f"\n{'='*90}")
    print("  BACKTEST COMPLETE")
    print(f"{'='*90}")


if __name__ == '__main__':
    run_backtest()
