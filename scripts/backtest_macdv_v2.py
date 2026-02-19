"""
MACD-V Dislocation Backtest v2 - Multi-Method Analysis
========================================================
Strategy: BUY when MACD-V > threshold AND timeframe dislocation > threshold
Exit: SELL after 7 trading days
Period: 5 years (Feb 2021 - Feb 2026)

Three percentile methods tested:
  Method A: Stochastic %K based (price position in range)
  Method B: MACD-V rolling percentile rank (momentum percentile)
  Method C: Rate-of-Change rolling percentile rank

Sensitivity sweep across MACD-V [60, 80, 100, 120] and divergence [15, 20, 25, 30]
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import sys

warnings.filterwarnings('ignore')

TICKER_MAP = {
    'GOOGL': 'GOOGL', 'US10': '^TNX', 'AMZN': 'AMZN', 'AAPL': 'AAPL',
    'SPY': 'SPY', 'BAC': 'BAC', 'SLV': 'SLV', 'ES1': 'ES=F',
    'NQ1': 'NQ=F', 'QQQ': 'QQQ', 'JPM': 'JPM', 'NFLX': 'NFLX',
    'XOM': 'XOM', 'NVDA': 'NVDA', 'CSP1': '^GSPC', 'CNX1': '^NSEI',
    'GLD': 'GLD', 'OXY': 'OXY', 'AVGO': 'AVGO', 'BTCUSD': 'BTC-USD',
    'CVX': 'CVX', 'MSFT': 'MSFT', 'TSLA': 'TSLA', 'USDGBP': 'GBPUSD=X',
    'LLY': 'LLY', 'BRK-B': 'BRK-B', 'TSM': 'TSM', 'VIX': '^VIX',
    'COST': 'COST', 'WMT': 'WMT', 'UNH': 'UNH', 'IGLS': 'IGLS.L',
}


def calculate_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def calculate_atr(high, low, close, period):
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


def calculate_macdv(close, high, low, fast=12, slow=26, atr_period=26):
    ema_fast = calculate_ema(close, fast)
    ema_slow = calculate_ema(close, slow)
    macd_line = ema_fast - ema_slow
    atr = calculate_atr(high, low, close, atr_period)
    atr = atr.replace(0, np.nan)
    return (macd_line / atr) * 100


def stochastic_k(close, high, low, period):
    lowest = low.rolling(window=period, min_periods=period).min()
    highest = high.rolling(window=period, min_periods=period).max()
    denom = highest - lowest
    denom = denom.replace(0, np.nan)
    return (close - lowest) / denom * 100


def rolling_percentile_rank(series, window):
    """Rolling percentile rank: what % of the past N values are below the current value."""
    def pct_rank(x):
        if len(x) < 2:
            return 50.0
        current = x[-1]
        past = x[:-1]
        if np.isnan(current):
            return np.nan
        valid = past[~np.isnan(past)]
        if len(valid) == 0:
            return 50.0
        return (valid < current).sum() / len(valid) * 100
    return series.rolling(window=window, min_periods=max(30, window // 4)).apply(pct_rank, raw=True)


def prepare_ticker_data(name, yf_ticker, warmup_start, end_date):
    """Download and prepare data with all three percentile methods."""
    try:
        data = yf.download(yf_ticker, start=warmup_start, end=end_date,
                          progress=False, auto_adjust=True)
        if data.empty or len(data) < 200:
            return None, f"Insufficient data ({len(data)} bars)"

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        close = data['Close'].squeeze()
        high = data['High'].squeeze()
        low = data['Low'].squeeze()

        # --- MACD-V (daily standard) ---
        macdv = calculate_macdv(close, high, low, fast=12, slow=26, atr_period=26)

        # --- METHOD A: Stochastic-based divergence ---
        stoch_daily = stochastic_k(close, high, low, period=100)
        stoch_fast = stochastic_k(close, high, low, period=25)
        div_stoch = stoch_daily - stoch_fast

        # --- METHOD B: MACD-V percentile rank divergence ---
        # Daily MACD-V percentile (where current MACD-V sits in last 252 values)
        macdv_pctile_daily = rolling_percentile_rank(macdv, window=252)
        # Fast MACD-V (3,7 params on daily ≈ 12,26 on 4H)
        macdv_fast = calculate_macdv(close, high, low, fast=3, slow=7, atr_period=7)
        macdv_pctile_fast = rolling_percentile_rank(macdv_fast, window=252)
        div_macdv_pctile = macdv_pctile_daily - macdv_pctile_fast

        # --- METHOD C: Rate of Change percentile rank divergence ---
        roc_daily = close.pct_change(20) * 100  # 20-day ROC
        roc_fast = close.pct_change(5) * 100    # 5-day ROC (faster, ~4H proxy)
        roc_pctile_daily = rolling_percentile_rank(roc_daily, window=252)
        roc_pctile_fast = rolling_percentile_rank(roc_fast, window=252)
        div_roc = roc_pctile_daily - roc_pctile_fast

        # --- Forward returns ---
        fwd_7d = close.shift(-7) / close - 1

        result_df = pd.DataFrame({
            'close': close,
            'macdv': macdv,
            'div_A': div_stoch,
            'div_B': div_macdv_pctile,
            'div_C': div_roc,
            'stoch_daily': stoch_daily,
            'stoch_fast': stoch_fast,
            'macdv_pctile_daily': macdv_pctile_daily,
            'macdv_pctile_fast': macdv_pctile_fast,
            'roc_pctile_daily': roc_pctile_daily,
            'roc_pctile_fast': roc_pctile_fast,
            'fwd_7d': fwd_7d,
        }, index=data.index)

        return result_df, None

    except Exception as e:
        return None, str(e)


def extract_trades(df, bt_start, bt_end, macdv_thresh, div_thresh, div_col, hold_days=7):
    """Extract non-overlapping trades for given parameters."""
    valid_mask = (df.index >= pd.Timestamp(bt_start)) & \
                 (df.index <= pd.Timestamp(bt_end) - timedelta(days=hold_days + 5))

    signal = (df['macdv'] > macdv_thresh) & (df[div_col] > div_thresh) & valid_mask

    trades = []
    last_entry = None

    for dt in df.index[signal]:
        if last_entry is not None and (dt - last_entry).days < hold_days:
            continue
        ret = df.loc[dt, 'fwd_7d']
        if pd.isna(ret):
            continue
        trades.append({
            'entry_date': dt,
            'entry_price': float(df.loc[dt, 'close']),
            'macdv': float(df.loc[dt, 'macdv']),
            'divergence': float(df.loc[dt, div_col]),
            'return_7d': float(ret),
        })
        last_entry = dt

    return trades


def compute_stats(trades):
    if not trades:
        return None
    rets = np.array([t['return_7d'] for t in trades])
    wins = (rets > 0).sum()
    gp = rets[rets > 0].sum()
    gl = abs(rets[rets <= 0].sum())
    pf = gp / gl if gl > 0 else float('inf')
    return {
        'n': len(trades),
        'win_rate': wins / len(trades) * 100,
        'avg_ret': rets.mean() * 100,
        'med_ret': np.median(rets) * 100,
        'tot_ret': ((1 + rets).prod() - 1) * 100,
        'max_win': rets.max() * 100,
        'max_loss': rets.min() * 100,
        'pf': pf,
        'std': rets.std() * 100,
    }


def main():
    end_date = datetime(2026, 2, 13)
    start_date = datetime(2021, 2, 13)
    warmup_start = start_date - timedelta(days=500)

    print("=" * 110)
    print("MACD-V DISLOCATION BACKTEST v2 — MULTI-METHOD ANALYSIS")
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} (5 years)")
    print("=" * 110)
    print()
    print("Strategy: BUY when MACD-V > threshold AND daily-4H divergence > threshold")
    print("Exit:     SELL after 7 trading days | Non-overlapping trades")
    print()
    print("Percentile Methods:")
    print("  A: Stochastic %K divergence (daily K100 - fast K25)")
    print("  B: MACD-V rolling percentile rank divergence (daily vs fast MACD-V)")
    print("  C: Rate-of-Change percentile rank divergence (20d ROC vs 5d ROC)")
    print()

    # ============================================================
    # DOWNLOAD ALL DATA
    # ============================================================
    print("Downloading data...")
    ticker_data = {}
    for name, yf_ticker in TICKER_MAP.items():
        sys.stdout.write(f"  {name:<10} ")
        sys.stdout.flush()
        df, err = prepare_ticker_data(name, yf_ticker, warmup_start, end_date)
        if df is not None:
            ticker_data[name] = df
            sys.stdout.write(f"OK ({len(df)} bars)\n")
        else:
            sys.stdout.write(f"SKIP: {err}\n")

    print(f"\n  {len(ticker_data)} tickers loaded successfully\n")

    # ============================================================
    # COMPREHENSIVE SENSITIVITY SWEEP
    # ============================================================
    methods = {'A': 'div_A', 'B': 'div_B', 'C': 'div_C'}
    macdv_thresholds = [60, 80, 100, 120, 140]
    div_thresholds = [15, 20, 25, 30, 35, 40]

    print("=" * 110)
    print("FULL PARAMETER SWEEP — ALL METHODS POOLED ACROSS 32 TICKERS")
    print("=" * 110)

    for method_name, div_col in methods.items():
        print(f"\n--- Method {method_name}: {div_col} ---")
        print(f"{'MACD-V >':<12} {'Div >':<8} {'Trades':>8} {'Win%':>8} {'AvgRet':>9} {'MedRet':>9} "
              f"{'TotRet':>10} {'MaxWin':>9} {'MaxLoss':>9} {'PF':>7} {'Tickers':>8}")
        print("-" * 110)

        for mv in macdv_thresholds:
            for dv in div_thresholds:
                all_trades = []
                tickers_with_signals = 0
                for name, df in ticker_data.items():
                    trades = extract_trades(df, start_date, end_date, mv, dv, div_col)
                    if trades:
                        for t in trades:
                            t['ticker'] = name
                        all_trades.extend(trades)
                        tickers_with_signals += 1

                if len(all_trades) < 1:
                    continue

                stats = compute_stats(all_trades)
                if stats is None:
                    continue

                pf_str = f"{stats['pf']:.2f}" if stats['pf'] != float('inf') else "Inf"
                marker = " ***" if mv == 120 and dv == 30 else ""
                print(f"{mv:<12} {dv:<8} {stats['n']:>8} {stats['win_rate']:>7.1f}% "
                      f"{stats['avg_ret']:>+8.2f}% {stats['med_ret']:>+8.2f}% "
                      f"{stats['tot_ret']:>+9.2f}% {stats['max_win']:>+8.2f}% "
                      f"{stats['max_loss']:>+8.2f}% {pf_str:>7} {tickers_with_signals:>8}{marker}")

    # ============================================================
    # DETAILED RESULTS FOR USER'S EXACT CRITERIA (MACD-V>120, DIV>30)
    # ============================================================
    print(f"\n{'='*110}")
    print("DETAILED RESULTS: YOUR EXACT CRITERIA (MACD-V > 120, Divergence > 30)")
    print(f"{'='*110}")

    for method_name, div_col in methods.items():
        print(f"\n  Method {method_name}:")
        print(f"  {'Ticker':<10} {'Trades':>7} {'Win%':>7} {'AvgRet':>9} {'MedRet':>9} {'TotRet':>10} "
              f"{'MaxWin':>9} {'MaxLoss':>9} {'PF':>7}")
        print(f"  {'-'*85}")

        total_trades = 0
        for name, df in sorted(ticker_data.items()):
            trades = extract_trades(df, start_date, end_date, 120, 30, div_col)
            if not trades:
                continue
            total_trades += len(trades)
            stats = compute_stats(trades)
            pf_str = f"{stats['pf']:.2f}" if stats['pf'] != float('inf') else "Inf"
            print(f"  {name:<10} {stats['n']:>7} {stats['win_rate']:>6.1f}% "
                  f"{stats['avg_ret']:>+8.2f}% {stats['med_ret']:>+8.2f}% "
                  f"{stats['tot_ret']:>+9.2f}% {stats['max_win']:>+8.2f}% "
                  f"{stats['max_loss']:>+8.2f}% {pf_str:>7}")

        if total_trades == 0:
            print(f"  (No signals found with MACD-V > 120 AND {div_col} > 30)")

    # ============================================================
    # BEST PARAMETER COMBINATIONS
    # ============================================================
    print(f"\n{'='*110}")
    print("BEST PARAMETER COMBINATIONS (min 20 trades, sorted by avg return)")
    print(f"{'='*110}")

    best_combos = []
    for method_name, div_col in methods.items():
        for mv in macdv_thresholds:
            for dv in div_thresholds:
                all_trades = []
                for name, df in ticker_data.items():
                    trades = extract_trades(df, start_date, end_date, mv, dv, div_col)
                    all_trades.extend(trades)
                if len(all_trades) >= 20:
                    stats = compute_stats(all_trades)
                    best_combos.append({
                        'method': method_name,
                        'macdv_thresh': mv,
                        'div_thresh': dv,
                        **stats,
                    })

    best_combos.sort(key=lambda x: x['avg_ret'], reverse=True)

    print(f"{'Method':<8} {'MACD-V>':<9} {'Div>':<7} {'Trades':>8} {'Win%':>8} "
          f"{'AvgRet':>9} {'MedRet':>9} {'TotRet':>10} {'PF':>7}")
    print("-" * 85)
    for combo in best_combos[:20]:
        pf_str = f"{combo['pf']:.2f}" if combo['pf'] != float('inf') else "Inf"
        print(f"{combo['method']:<8} {combo['macdv_thresh']:<9} {combo['div_thresh']:<7} "
              f"{combo['n']:>8} {combo['win_rate']:>7.1f}% {combo['avg_ret']:>+8.2f}% "
              f"{combo['med_ret']:>+8.2f}% {combo['tot_ret']:>+9.2f}% {pf_str:>7}")

    # ============================================================
    # PER-TICKER ANALYSIS WITH BEST METHOD (Method B, MACD-V>80, Div>20)
    # Find the best combo with sufficient trades for per-ticker breakdown
    # ============================================================
    # Use a reasonable parameter set to show per-ticker results
    for target_mv, target_dv, target_method in [(100, 20, 'B'), (80, 20, 'B'), (80, 15, 'C'), (60, 15, 'C')]:
        div_col = methods[target_method]
        all_per_ticker = {}
        for name, df in ticker_data.items():
            trades = extract_trades(df, start_date, end_date, target_mv, target_dv, div_col)
            if trades:
                all_per_ticker[name] = trades

        if len(all_per_ticker) >= 10:
            print(f"\n{'='*110}")
            print(f"PER-TICKER BREAKDOWN: Method {target_method}, MACD-V>{target_mv}, Div>{target_dv}")
            print(f"{'='*110}")
            print(f"{'Ticker':<10} {'Trades':>7} {'Win%':>7} {'AvgRet':>9} {'MedRet':>9} "
                  f"{'TotRet':>10} {'MaxWin':>9} {'MaxLoss':>9} {'PF':>7} {'AvgMACV':>8}")
            print("-" * 100)

            all_combined = []
            for name in sorted(all_per_ticker.keys(),
                              key=lambda n: compute_stats(all_per_ticker[n])['avg_ret'],
                              reverse=True):
                trades = all_per_ticker[name]
                all_combined.extend(trades)
                stats = compute_stats(trades)
                avg_mv = np.mean([t['macdv'] for t in trades])
                pf_str = f"{stats['pf']:.2f}" if stats['pf'] != float('inf') else "Inf"
                print(f"{name:<10} {stats['n']:>7} {stats['win_rate']:>6.1f}% "
                      f"{stats['avg_ret']:>+8.2f}% {stats['med_ret']:>+8.2f}% "
                      f"{stats['tot_ret']:>+9.2f}% {stats['max_win']:>+8.2f}% "
                      f"{stats['max_loss']:>+8.2f}% {pf_str:>7} {avg_mv:>7.1f}")

            print("-" * 100)
            overall = compute_stats(all_combined)
            pf_str = f"{overall['pf']:.2f}" if overall['pf'] != float('inf') else "Inf"
            print(f"{'TOTAL':<10} {overall['n']:>7} {overall['win_rate']:>6.1f}% "
                  f"{overall['avg_ret']:>+8.2f}% {overall['med_ret']:>+8.2f}% "
                  f"{overall['tot_ret']:>+9.2f}% {overall['max_win']:>+8.2f}% "
                  f"{overall['max_loss']:>+8.2f}% {pf_str:>7}")

            # Year breakdown
            tdf = pd.DataFrame(all_combined)
            tdf['year'] = pd.to_datetime(tdf['entry_date']).dt.year
            print(f"\n  By Year:")
            print(f"  {'Year':<8} {'Trades':>8} {'Win%':>8} {'AvgRet':>9} {'MedRet':>9}")
            print(f"  {'-'*45}")
            for year in sorted(tdf['year'].unique()):
                ydf = tdf[tdf['year'] == year]
                wr = (ydf['return_7d'] > 0).mean() * 100
                ar = ydf['return_7d'].mean() * 100
                mr = ydf['return_7d'].median() * 100
                print(f"  {year:<8} {len(ydf):>8} {wr:>7.1f}% {ar:>+8.2f}% {mr:>+8.2f}%")

            break  # Only show one detailed breakdown

    # ============================================================
    # ADDITIONAL: Show what happens with MACD-V > 120 at ANY divergence
    # ============================================================
    print(f"\n{'='*110}")
    print("MACD-V > 120 ANALYSIS: What divergence thresholds work?")
    print("(Method B - MACD-V percentile rank divergence)")
    print(f"{'='*110}")

    div_col = 'div_B'
    for dv in [0, 5, 10, 15, 20, 25, 30, 35]:
        all_trades = []
        tickers_hit = 0
        for name, df in ticker_data.items():
            trades = extract_trades(df, start_date, end_date, 120, dv, div_col)
            if trades:
                tickers_hit += 1
                for t in trades:
                    t['ticker'] = name
                all_trades.extend(trades)

        if not all_trades:
            print(f"  MACD-V>120, Div>{dv:>3}: 0 trades")
            continue

        stats = compute_stats(all_trades)
        pf_str = f"{stats['pf']:.2f}" if stats['pf'] != float('inf') else "Inf"
        print(f"  MACD-V>120, Div>{dv:>3}: {stats['n']:>4} trades | "
              f"Win: {stats['win_rate']:>5.1f}% | Avg: {stats['avg_ret']:>+6.2f}% | "
              f"Med: {stats['med_ret']:>+6.2f}% | PF: {pf_str:>6} | Tickers: {tickers_hit}")

    # Show sample trades for MACD-V > 120, any divergence method B
    all_trades_120 = []
    for name, df in ticker_data.items():
        trades = extract_trades(df, start_date, end_date, 120, 0, 'div_B')
        for t in trades:
            t['ticker'] = name
        all_trades_120.extend(trades)

    if all_trades_120:
        print(f"\n  All trades where MACD-V > 120 (Method B, any divergence):")
        print(f"  {'Date':<12} {'Ticker':<10} {'Price':>10} {'MACDV':>8} {'Div':>8} {'7d Ret':>8} {'W/L':>5}")
        print(f"  {'-'*70}")
        for t in sorted(all_trades_120, key=lambda x: x['entry_date']):
            wl = "WIN" if t['return_7d'] > 0 else "LOSS"
            print(f"  {str(t['entry_date'])[:10]:<12} {t['ticker']:<10} "
                  f"{t['entry_price']:>10.2f} {t['macdv']:>7.1f} {t['divergence']:>+7.1f} "
                  f"{t['return_7d']*100:>+7.2f}% {wl:>5}")

    # ============================================================
    # ALSO SHOW: What if we ONLY use MACD-V > threshold (no divergence)?
    # ============================================================
    print(f"\n{'='*110}")
    print("BASELINE: MACD-V only (no divergence filter) — 7-day hold")
    print(f"{'='*110}")
    print(f"{'MACD-V >':<12} {'Trades':>8} {'Win%':>8} {'AvgRet':>9} {'MedRet':>9} {'PF':>7} {'Tickers':>8}")
    print("-" * 65)

    for mv in [60, 80, 100, 120, 140, 160]:
        all_trades = []
        tickers_hit = 0
        for name, df in ticker_data.items():
            trades = extract_trades(df, start_date, end_date, mv, -999, 'div_B')  # div>-999 = no filter
            if trades:
                tickers_hit += 1
                all_trades.extend(trades)
        if all_trades:
            stats = compute_stats(all_trades)
            pf_str = f"{stats['pf']:.2f}" if stats['pf'] != float('inf') else "Inf"
            print(f"{mv:<12} {stats['n']:>8} {stats['win_rate']:>7.1f}% "
                  f"{stats['avg_ret']:>+8.2f}% {stats['med_ret']:>+8.2f}% {pf_str:>7} {tickers_hit:>8}")

    print(f"\n{'='*110}")
    print("BACKTEST COMPLETE")
    print(f"{'='*110}")
    print()
    print("IMPORTANT CAVEATS:")
    print("1. 4H percentile is APPROXIMATED from daily data (no 5yr intraday data available)")
    print("2. Methods A/B/C are proxies for your framework's proprietary percentile calculation")
    print("3. MACD-V > 120 is a very high bar — signals are inherently rare per-ticker")
    print("4. Results do not account for slippage, commissions, or spread")
    print("5. Small sample sizes (especially at MACD-V>120) limit statistical confidence")


if __name__ == '__main__':
    main()
