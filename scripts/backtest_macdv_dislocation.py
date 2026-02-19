"""
MACD-V Dislocation Backtest
============================
Strategy: Buy when MACD-V > 120 AND daily-4H percentile divergence > 30 points
Exit: Sell after 7 trading days
Period: 5 years (Feb 2021 - Feb 2026)

Methodology Notes:
- MACD-V = (EMA12 - EMA26) / ATR(26) * 100  (standard Spiroglou definition)
- Daily percentile: Stochastic %K(100) - where price sits in its 100-day range
- 4H percentile approximation: Stochastic %K(25) on daily data - faster-reacting proxy
  (25 daily bars ≈ 100 4H bars for stocks with ~4 tradeable 4H bars/day)
- Divergence = Daily %K - Fast %K  (positive = 4H pulled back within daily trend)
- P85 significance threshold: divergence > 30 points
- Non-overlapping trades: minimum 7 days between entries
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import sys

warnings.filterwarnings('ignore')

# ============================================================
# TICKER MAPPING
# ============================================================
TICKER_MAP = {
    'GOOGL': 'GOOGL',
    'US10': '^TNX',
    'AMZN': 'AMZN',
    'AAPL': 'AAPL',
    'SPY': 'SPY',
    'BAC': 'BAC',
    'SLV': 'SLV',
    'ES1': 'ES=F',
    'NQ1': 'NQ=F',
    'QQQ': 'QQQ',
    'JPM': 'JPM',
    'NFLX': 'NFLX',
    'XOM': 'XOM',
    'NVDA': 'NVDA',
    'CSP1': '^GSPC',
    'CNX1': '^NSEI',
    'GLD': 'GLD',
    'OXY': 'OXY',
    'AVGO': 'AVGO',
    'BTCUSD': 'BTC-USD',
    'CVX': 'CVX',
    'MSFT': 'MSFT',
    'TSLA': 'TSLA',
    'USDGBP': 'GBPUSD=X',
    'LLY': 'LLY',
    'BRK-B': 'BRK-B',
    'TSM': 'TSM',
    'VIX': '^VIX',
    'COST': 'COST',
    'WMT': 'WMT',
    'UNH': 'UNH',
    'IGLS': 'IGLS.L',
}

# ============================================================
# INDICATOR CALCULATIONS
# ============================================================

def calculate_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def calculate_atr(high, low, close, period):
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


def calculate_macdv(close, high, low, fast=12, slow=26, atr_period=26):
    """MACD-V = (EMA_fast - EMA_slow) / ATR * 100"""
    ema_fast = calculate_ema(close, fast)
    ema_slow = calculate_ema(close, slow)
    macd_line = ema_fast - ema_slow
    atr = calculate_atr(high, low, close, atr_period)
    # Avoid division by zero
    atr = atr.replace(0, np.nan)
    macdv = (macd_line / atr) * 100
    return macdv


def stochastic_k(close, high, low, period):
    """Stochastic %K: (Close - LowestLow) / (HighestHigh - LowestLow) * 100"""
    lowest = low.rolling(window=period, min_periods=period).min()
    highest = high.rolling(window=period, min_periods=period).max()
    denom = highest - lowest
    denom = denom.replace(0, np.nan)
    k = (close - lowest) / denom * 100
    return k


# ============================================================
# BACKTESTING ENGINE
# ============================================================

def backtest_ticker(name, yf_ticker, start_date, end_date,
                    macdv_thresh=120, div_thresh=30, hold_days=7):
    """Backtest strategy for a single ticker."""
    try:
        # Extra lookback for indicator warmup
        warmup_start = start_date - timedelta(days=500)
        data = yf.download(yf_ticker, start=warmup_start, end=end_date,
                          progress=False, auto_adjust=True)

        if data.empty or len(data) < 200:
            return {'ticker': name, 'error': 'Insufficient data'}

        # Flatten MultiIndex columns if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        close = data['Close'].squeeze()
        high = data['High'].squeeze()
        low = data['Low'].squeeze()

        # --- MACD-V (daily, standard parameters) ---
        macdv = calculate_macdv(close, high, low, fast=12, slow=26, atr_period=26)

        # --- Percentile approximations ---
        # Daily percentile: Stochastic %K over 100 days
        daily_pctile = stochastic_k(close, high, low, period=100)

        # 4H approximation: Stochastic %K over 25 days (faster-reacting)
        fast_pctile = stochastic_k(close, high, low, period=25)

        # Divergence: daily - fast (positive = 4H pulled back relative to daily)
        divergence = daily_pctile - fast_pctile

        # --- Forward returns ---
        fwd_return = close.shift(-hold_days) / close - 1

        # --- Filter to backtest period ---
        bt_mask = data.index >= pd.Timestamp(start_date)
        # Ensure we have room for exit
        exit_mask = data.index <= pd.Timestamp(end_date) - timedelta(days=hold_days + 5)
        valid_mask = bt_mask & exit_mask

        # --- Entry signals ---
        signal = (macdv > macdv_thresh) & (divergence > div_thresh) & valid_mask

        # --- Extract non-overlapping trades ---
        trades = []
        last_entry = None

        for dt in data.index[signal]:
            if last_entry is not None and (dt - last_entry).days < hold_days:
                continue

            ret = fwd_return.loc[dt]
            if pd.isna(ret):
                continue

            trades.append({
                'entry_date': dt,
                'entry_price': float(close.loc[dt]),
                'exit_price': float(close.loc[dt] * (1 + ret)),
                'macdv': float(macdv.loc[dt]),
                'daily_pctile': float(daily_pctile.loc[dt]),
                'fast_pctile': float(fast_pctile.loc[dt]),
                'divergence': float(divergence.loc[dt]),
                'return_7d': float(ret),
            })
            last_entry = dt

        if len(trades) == 0:
            return {
                'ticker': name,
                'num_trades': 0,
                'win_rate': 0,
                'avg_return': 0,
                'median_return': 0,
                'total_return': 0,
                'max_win': 0,
                'max_loss': 0,
                'profit_factor': 0,
                'avg_macdv': 0,
                'avg_divergence': 0,
                'trades': [],
            }

        tdf = pd.DataFrame(trades)
        wins = (tdf['return_7d'] > 0).sum()
        losses = (tdf['return_7d'] <= 0).sum()

        gross_profit = tdf.loc[tdf['return_7d'] > 0, 'return_7d'].sum()
        gross_loss = abs(tdf.loc[tdf['return_7d'] <= 0, 'return_7d'].sum())
        pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        compounded = (1 + tdf['return_7d']).prod() - 1

        return {
            'ticker': name,
            'num_trades': len(trades),
            'win_rate': wins / len(trades) * 100,
            'avg_return': tdf['return_7d'].mean() * 100,
            'median_return': tdf['return_7d'].median() * 100,
            'total_return': compounded * 100,
            'max_win': tdf['return_7d'].max() * 100,
            'max_loss': tdf['return_7d'].min() * 100,
            'profit_factor': pf,
            'avg_macdv': tdf['macdv'].mean(),
            'avg_divergence': tdf['divergence'].mean(),
            'trades': trades,
        }

    except Exception as e:
        return {'ticker': name, 'error': str(e)}


# ============================================================
# SENSITIVITY ANALYSIS
# ============================================================

def run_sensitivity(all_trades, label=""):
    """Run parameter sensitivity on collected trade data."""
    if not all_trades:
        return

    df = pd.DataFrame(all_trades)

    print(f"\n{'='*90}")
    print(f"SENSITIVITY ANALYSIS {label}")
    print(f"{'='*90}")

    # Vary MACD-V threshold
    print(f"\n{'MACD-V Thresh':<15} {'Div Thresh':<12} {'Trades':>8} {'Win Rate':>10} {'Avg Ret':>10} {'Med Ret':>10} {'PF':>8}")
    print("-" * 75)

    for mv_thresh in [80, 100, 120, 140, 160]:
        for dv_thresh in [20, 30, 40, 50]:
            subset = df[(df['macdv'] > mv_thresh) & (df['divergence'] > dv_thresh)]
            if len(subset) < 3:
                continue
            wr = (subset['return_7d'] > 0).mean() * 100
            ar = subset['return_7d'].mean() * 100
            mr = subset['return_7d'].median() * 100
            gp = subset.loc[subset['return_7d'] > 0, 'return_7d'].sum()
            gl = abs(subset.loc[subset['return_7d'] <= 0, 'return_7d'].sum())
            pf = gp / gl if gl > 0 else float('inf')
            print(f">{mv_thresh:<14} >{dv_thresh:<11} {len(subset):>8} {wr:>9.1f}% {ar:>9.2f}% {mr:>9.2f}% {pf:>7.2f}")


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    end_date = datetime(2026, 2, 13)
    start_date = datetime(2021, 2, 13)

    print("=" * 100)
    print("MACD-V DISLOCATION BACKTEST")
    print(f"Strategy: BUY when MACD-V > 120 AND Daily-4H Percentile Divergence > 30")
    print(f"Exit: SELL after 7 trading days")
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} (5 years)")
    print("=" * 100)
    print()
    print("Methodology:")
    print("  - MACD-V = (EMA12 - EMA26) / ATR(26) * 100")
    print("  - Daily %ile = Stochastic %K(100) [price position in 100-day range]")
    print("  - 4H %ile proxy = Stochastic %K(25) [faster-reacting, ~4x daily resolution]")
    print("  - Divergence = Daily %ile - 4H %ile [positive = 4H pulled back]")
    print("  - Non-overlapping trades with 7-day minimum gap")
    print()

    results = []
    all_trades = []

    for name, yf_ticker in TICKER_MAP.items():
        sys.stdout.write(f"  Processing {name:<10} ({yf_ticker})... ")
        sys.stdout.flush()
        result = backtest_ticker(name, yf_ticker, start_date, end_date)
        if result:
            results.append(result)
            if 'error' not in result:
                all_trades.extend(result.get('trades', []))
                sys.stdout.write(f"{result['num_trades']} trades found\n")
            else:
                sys.stdout.write(f"ERROR: {result['error']}\n")
        else:
            sys.stdout.write("No result\n")

    # ============================================================
    # RESULTS TABLE
    # ============================================================
    print()
    print("=" * 130)
    print("INDIVIDUAL TICKER RESULTS")
    print("=" * 130)
    header = (f"{'Ticker':<10} {'Trades':>7} {'Win%':>7} {'AvgRet':>8} {'MedRet':>8} "
              f"{'TotRet':>10} {'MaxWin':>8} {'MaxLoss':>9} {'PF':>6} "
              f"{'AvgMACV':>8} {'AvgDiv':>8}")
    print(header)
    print("-" * 130)

    profitable_tickers = 0
    total_trades = 0
    tickers_with_trades = 0

    sorted_results = sorted(results, key=lambda x: x.get('avg_return', -999), reverse=True)

    for r in sorted_results:
        if 'error' in r:
            print(f"{r['ticker']:<10} ERROR: {r['error']}")
            continue

        if r['num_trades'] == 0:
            print(f"{r['ticker']:<10} {'0':>7}   --- no signals ---")
            continue

        tickers_with_trades += 1
        total_trades += r['num_trades']

        if r['avg_return'] > 0:
            profitable_tickers += 1

        pf_str = f"{r['profit_factor']:.2f}" if r['profit_factor'] != float('inf') else "Inf"

        print(f"{r['ticker']:<10} {r['num_trades']:>7} {r['win_rate']:>6.1f}% "
              f"{r['avg_return']:>7.2f}% {r['median_return']:>7.2f}% "
              f"{r['total_return']:>9.2f}% {r['max_win']:>7.2f}% "
              f"{r['max_loss']:>8.2f}% {pf_str:>6} "
              f"{r['avg_macdv']:>7.1f} {r['avg_divergence']:>7.1f}")

    # ============================================================
    # AGGREGATE SUMMARY
    # ============================================================
    print()
    print("=" * 130)
    print("AGGREGATE SUMMARY")
    print("=" * 130)

    if all_trades:
        all_rets = np.array([t['return_7d'] for t in all_trades])
        wins = (all_rets > 0).sum()
        losses = (all_rets <= 0).sum()

        gp = all_rets[all_rets > 0].sum()
        gl = abs(all_rets[all_rets <= 0].sum())
        pf = gp / gl if gl > 0 else float('inf')

        print(f"  Tickers analyzed:          {len(results)}")
        print(f"  Tickers with signals:      {tickers_with_trades}")
        print(f"  Tickers profitable (avg):  {profitable_tickers} / {tickers_with_trades} "
              f"({profitable_tickers/tickers_with_trades*100:.0f}%)" if tickers_with_trades > 0 else "")
        print(f"  Total trades:              {total_trades}")
        print(f"  Overall win rate:          {wins}/{len(all_rets)} = {wins/len(all_rets)*100:.1f}%")
        print(f"  Overall avg return/trade:  {all_rets.mean()*100:+.2f}%")
        print(f"  Overall median return:     {np.median(all_rets)*100:+.2f}%")
        print(f"  Std dev of returns:        {all_rets.std()*100:.2f}%")
        print(f"  Best single trade:         {all_rets.max()*100:+.2f}%")
        print(f"  Worst single trade:        {all_rets.min()*100:+.2f}%")
        print(f"  Profit factor:             {pf:.2f}")
        print(f"  Avg trades/ticker:         {total_trades/tickers_with_trades:.1f}" if tickers_with_trades > 0 else "")

        # Sharpe-like metric (annualized)
        if all_rets.std() > 0:
            trades_per_year = total_trades / 5
            sharpe_per_trade = all_rets.mean() / all_rets.std()
            ann_sharpe = sharpe_per_trade * np.sqrt(trades_per_year) if trades_per_year > 0 else 0
            print(f"  Sharpe (annualized est):   {ann_sharpe:.2f}")

        # Distribution of returns
        print(f"\n  Return Distribution:")
        print(f"    < -5%:    {(all_rets < -0.05).sum():>4} trades ({(all_rets < -0.05).mean()*100:.1f}%)")
        print(f"    -5% to 0: {((all_rets >= -0.05) & (all_rets <= 0)).sum():>4} trades ({((all_rets >= -0.05) & (all_rets <= 0)).mean()*100:.1f}%)")
        print(f"    0% to 2%: {((all_rets > 0) & (all_rets <= 0.02)).sum():>4} trades ({((all_rets > 0) & (all_rets <= 0.02)).mean()*100:.1f}%)")
        print(f"    2% to 5%: {((all_rets > 0.02) & (all_rets <= 0.05)).sum():>4} trades ({((all_rets > 0.02) & (all_rets <= 0.05)).mean()*100:.1f}%)")
        print(f"    > 5%:     {(all_rets > 0.05).sum():>4} trades ({(all_rets > 0.05).mean()*100:.1f}%)")
    else:
        print("  No trades generated across any ticker.")

    # ============================================================
    # SENSITIVITY ANALYSIS
    # ============================================================
    run_sensitivity(all_trades, "(All Tickers Pooled)")

    # ============================================================
    # TRADE LOG (sample)
    # ============================================================
    if all_trades:
        print(f"\n{'='*100}")
        print(f"SAMPLE TRADES (top 10 by return, bottom 10 by return)")
        print(f"{'='*100}")

        tdf = pd.DataFrame(all_trades)
        tdf = tdf.sort_values('return_7d', ascending=False)

        print(f"\n  TOP 10 WINNING TRADES:")
        print(f"  {'Date':<12} {'Ticker':<8} {'Entry':>10} {'Exit':>10} {'Return':>8} {'MACDV':>8} {'Div':>6}")
        print(f"  {'-'*70}")
        for _, row in tdf.head(10).iterrows():
            # Need ticker info - we stored entry_price but not ticker in trades
            # Let me find it from results
            print(f"  {str(row['entry_date'])[:10]:<12} "
                  f"{'':>8} "  # ticker not stored per trade, shown in context
                  f"{row['entry_price']:>10.2f} {row['exit_price']:>10.2f} "
                  f"{row['return_7d']*100:>+7.2f}% {row['macdv']:>7.1f} {row['divergence']:>5.1f}")

        print(f"\n  BOTTOM 10 LOSING TRADES:")
        print(f"  {'Date':<12} {'Ticker':<8} {'Entry':>10} {'Exit':>10} {'Return':>8} {'MACDV':>8} {'Div':>6}")
        print(f"  {'-'*70}")
        for _, row in tdf.tail(10).iterrows():
            print(f"  {str(row['entry_date'])[:10]:<12} "
                  f"{'':>8} "
                  f"{row['entry_price']:>10.2f} {row['exit_price']:>10.2f} "
                  f"{row['return_7d']*100:>+7.2f}% {row['macdv']:>7.1f} {row['divergence']:>5.1f}")

    # ============================================================
    # BY-YEAR BREAKDOWN
    # ============================================================
    if all_trades:
        print(f"\n{'='*90}")
        print("PERFORMANCE BY YEAR")
        print(f"{'='*90}")

        tdf = pd.DataFrame(all_trades)
        tdf['year'] = pd.to_datetime(tdf['entry_date']).dt.year

        print(f"  {'Year':<8} {'Trades':>8} {'Win Rate':>10} {'Avg Ret':>10} {'Med Ret':>10} {'Tot Ret':>10}")
        print(f"  {'-'*60}")

        for year in sorted(tdf['year'].unique()):
            ydf = tdf[tdf['year'] == year]
            wr = (ydf['return_7d'] > 0).mean() * 100
            ar = ydf['return_7d'].mean() * 100
            mr = ydf['return_7d'].median() * 100
            tr = ((1 + ydf['return_7d']).prod() - 1) * 100
            print(f"  {year:<8} {len(ydf):>8} {wr:>9.1f}% {ar:>9.2f}% {mr:>9.2f}% {tr:>9.2f}%")

    print(f"\n{'='*90}")
    print("BACKTEST COMPLETE")
    print(f"{'='*90}")


if __name__ == '__main__':
    main()
