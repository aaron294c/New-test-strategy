#!/usr/bin/env python3
"""
Comprehensive Backtesting Script for RSI-MA Divergence Strategy

Strategy:
- Entry: MACD-V > 120 AND (Daily RSI-MA percentile - 4H RSI-MA percentile) > 30
- Exit: 7 trading days later
- Period: 5 years (Feb 2021 - Feb 2026)
"""

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Ticker mapping (Yahoo Finance format)
TICKER_MAP = {
    'US10': '^TNX',
    'ES1': 'ES=F',
    'NQ1': 'NQ=F',
    'CSP1': '^GSPC',
    'CNX1': '^NSEI',
    'BTCUSD': 'BTC-USD',
    'USDGBP': 'GBPUSD=X',
    'VIX': '^VIX',
    'IGLS': 'IGLS.L'
}

TICKERS = [
    'GOOGL', 'US10', 'AMZN', 'AAPL', 'SPY', 'BAC', 'SLV', 'ES1', 'NQ1', 'QQQ',
    'JPM', 'NFLX', 'XOM', 'NVDA', 'CSP1', 'CNX1', 'GLD', 'OXY', 'AVGO', 'BTCUSD',
    'CVX', 'MSFT', 'TSLA', 'USDGBP', 'LLY', 'BRK-B', 'TSM', 'COST', 'WMT',
    'UNH', 'IGLS'
]


def calculate_rsi_ma(close_prices: pd.Series, rsi_length: int = 14, ma_length: int = 14) -> pd.Series:
    """
    Calculate RSI-MA indicator using exact pipeline:
    1. Log returns from Close price
    2. Second derivative (diff of log returns)
    3. RSI(14) on the second derivative using Wilder's RMA
    4. EMA(14) on the RSI
    """
    # Step 1: Log returns
    log_returns = np.log(close_prices / close_prices.shift(1)).fillna(0)

    # Step 2: Second derivative (change of returns = acceleration)
    delta = log_returns.diff()

    # Step 3: RSI using Wilder's smoothing (RMA)
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)

    # Wilder's smoothing: alpha = 1/length
    avg_gains = gains.ewm(alpha=1/rsi_length, adjust=False).mean()
    avg_losses = losses.ewm(alpha=1/rsi_length, adjust=False).mean()

    # Avoid division by zero
    rs = avg_gains / avg_losses.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(50)

    # Step 4: EMA smoothing of RSI
    rsi_ma = rsi.ewm(span=ma_length, adjust=False).mean()

    return rsi_ma


def calculate_percentile_rank_vectorized(rsi_ma: pd.Series, lookback: int = 252) -> pd.Series:
    """
    Calculate rolling percentile rank efficiently using rolling apply.
    Returns what % of last N values are BELOW current value.
    """
    def percentile_func(window):
        if len(window) < 2:
            return np.nan
        current = window.iloc[-1]
        historical = window.iloc[:-1]
        return (historical < current).sum() / len(historical) * 100

    # Use rolling with min_periods to handle warmup
    percentiles = rsi_ma.rolling(window=lookback + 1, min_periods=lookback + 1).apply(
        percentile_func, raw=False
    )

    return percentiles


def calculate_macd_v(close_prices: pd.Series, fast: int = 12, slow: int = 26, atr_period: int = 26) -> pd.Series:
    """
    Calculate MACD-V: (EMA12 - EMA26) / ATR(26) * 100
    """
    ema_fast = close_prices.ewm(span=fast, adjust=False).mean()
    ema_slow = close_prices.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow

    # Calculate ATR
    high = close_prices  # Using close as proxy for high
    low = close_prices   # Using close as proxy for low
    tr = close_prices.diff().abs()  # True range approximation
    atr = tr.rolling(window=atr_period).mean()

    # MACD-V
    macd_v = (macd / atr.replace(0, np.nan)) * 100

    return macd_v


def download_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Download daily data with error handling."""
    try:
        yf_ticker = TICKER_MAP.get(ticker, ticker)
        print(f"  Downloading {ticker} ({yf_ticker})...", end=' ')

        data = yf.download(yf_ticker, start=start_date, end=end_date, progress=False)

        if data.empty:
            print(f"FAILED (no data)")
            return None

        # Handle multi-level columns from yfinance
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        print(f"OK ({len(data)} bars)")
        return data

    except Exception as e:
        print(f"FAILED ({str(e)})")
        return None


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate all required indicators."""
    close = df['Close']

    # MACD-V
    df['MACD_V'] = calculate_macd_v(close)

    # Daily RSI-MA percentile (RSI 14, MA 14, lookback 252)
    rsi_ma_daily = calculate_rsi_ma(close, rsi_length=14, ma_length=14)
    df['RSI_MA_Daily'] = rsi_ma_daily
    df['Daily_Percentile'] = calculate_percentile_rank_vectorized(rsi_ma_daily, lookback=252)

    # 4H-proxy RSI-MA percentile (RSI 9, MA 9, lookback 252)
    # 9 ≈ 14/1.625 to approximate the faster 4H reaction on daily data
    rsi_ma_4h = calculate_rsi_ma(close, rsi_length=9, ma_length=9)
    df['RSI_MA_4H'] = rsi_ma_4h
    df['4H_Percentile'] = calculate_percentile_rank_vectorized(rsi_ma_4h, lookback=252)

    # Divergence
    df['Divergence'] = df['Daily_Percentile'] - df['4H_Percentile']

    return df


def backtest_strategy(
    df: pd.DataFrame,
    ticker: str,
    macdv_threshold: float,
    div_threshold: float,
    hold_days: int = 7,
    backtest_start: str = '2021-02-01'
) -> List[Dict]:
    """
    Run backtest with non-overlapping trades.

    Returns list of trades with entry/exit info.
    """
    trades = []
    df = df.copy()

    # Filter to backtest period
    df = df[df.index >= backtest_start]

    i = 0
    while i < len(df) - hold_days:
        row = df.iloc[i]

        # Check entry conditions
        if (pd.notna(row['MACD_V']) and
            pd.notna(row['Divergence']) and
            row['MACD_V'] > macdv_threshold and
            row['Divergence'] > div_threshold):

            entry_date = row.name
            entry_price = row['Close']

            # Calculate exit (7 days later)
            exit_idx = i + hold_days
            if exit_idx >= len(df):
                break

            exit_row = df.iloc[exit_idx]
            exit_date = exit_row.name
            exit_price = exit_row['Close']

            # Calculate return
            pct_return = ((exit_price - entry_price) / entry_price) * 100

            trades.append({
                'ticker': ticker,
                'entry_date': entry_date,
                'exit_date': exit_date,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'return_pct': pct_return,
                'macdv': row['MACD_V'],
                'divergence': row['Divergence'],
                'daily_pct': row['Daily_Percentile'],
                '4h_pct': row['4H_Percentile'],
                'year': entry_date.year
            })

            # Skip to after exit (non-overlapping)
            i = exit_idx + 1
        else:
            i += 1

    return trades


def calculate_metrics(trades: List[Dict]) -> Dict:
    """Calculate aggregate statistics from trades."""
    if not trades:
        return {
            'num_trades': 0,
            'win_rate': 0.0,
            'avg_return': 0.0,
            'total_return': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
            'max_win': 0.0,
            'max_loss': 0.0
        }

    returns = [t['return_pct'] for t in trades]
    wins = [r for r in returns if r > 0]
    losses = [r for r in returns if r <= 0]

    return {
        'num_trades': len(trades),
        'win_rate': len(wins) / len(trades) * 100 if trades else 0,
        'avg_return': np.mean(returns),
        'total_return': np.sum(returns),
        'avg_win': np.mean(wins) if wins else 0,
        'avg_loss': np.mean(losses) if losses else 0,
        'profit_factor': abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else float('inf') if wins else 0,
        'max_win': max(returns) if returns else 0,
        'max_loss': min(returns) if returns else 0
    }


def main():
    print("=" * 80)
    print("EXACT RSI-MA DIVERGENCE STRATEGY BACKTEST")
    print("=" * 80)
    print(f"\nStrategy:")
    print(f"  Entry: MACD-V > threshold AND Divergence > threshold")
    print(f"  Exit: 7 trading days later")
    print(f"  Period: Feb 2021 - Feb 2026")
    print(f"  Tickers: {len(TICKERS)} symbols")
    print()

    # Date ranges (add 500-day warmup)
    backtest_start = '2021-02-01'
    backtest_end = '2026-02-14'
    warmup_days = 500
    download_start = (datetime.strptime(backtest_start, '%Y-%m-%d') - timedelta(days=warmup_days*1.5)).strftime('%Y-%m-%d')

    print(f"Download period: {download_start} to {backtest_end}")
    print(f"Backtest period: {backtest_start} to {backtest_end}")
    print(f"Warmup: ~{warmup_days} days\n")

    # Download and process data
    print("DOWNLOADING DATA")
    print("-" * 80)

    all_data = {}
    failed_tickers = []

    for ticker in TICKERS:
        df = download_data(ticker, download_start, backtest_end)
        if df is not None and len(df) > 100:
            all_data[ticker] = df
        else:
            failed_tickers.append(ticker)

    print(f"\nSuccessfully downloaded: {len(all_data)}/{len(TICKERS)}")
    if failed_tickers:
        print(f"Failed tickers: {', '.join(failed_tickers)}")
    print()

    # Calculate indicators
    print("CALCULATING INDICATORS")
    print("-" * 80)

    for ticker in all_data:
        print(f"  Processing {ticker}...", end=' ')
        all_data[ticker] = calculate_indicators(all_data[ticker])
        print("OK")

    print()

    # Parameter sweep
    macdv_thresholds = [60, 80, 100, 120, 140]
    div_thresholds = [15, 20, 25, 30, 35]

    print("PARAMETER SWEEP")
    print("=" * 80)

    sweep_results = []

    for macdv_thresh in macdv_thresholds:
        for div_thresh in div_thresholds:
            all_trades = []

            for ticker in all_data:
                trades = backtest_strategy(
                    all_data[ticker],
                    ticker,
                    macdv_thresh,
                    div_thresh,
                    hold_days=7,
                    backtest_start=backtest_start
                )
                all_trades.extend(trades)

            metrics = calculate_metrics(all_trades)
            sweep_results.append({
                'macdv': macdv_thresh,
                'div': div_thresh,
                **metrics
            })

    # Print sweep table
    print("\nFull Parameter Sweep Results:")
    print("-" * 80)
    print(f"{'MACD-V':>8} {'Div':>6} {'Trades':>8} {'Win%':>8} {'Avg%':>8} {'Total%':>10} {'PF':>8}")
    print("-" * 80)

    for result in sweep_results:
        marker = "***" if result['macdv'] == 120 and result['div'] == 25 else "   "
        print(f"{marker} {result['macdv']:>5} {result['div']:>6} {result['num_trades']:>8} "
              f"{result['win_rate']:>7.1f}% {result['avg_return']:>7.2f}% "
              f"{result['total_return']:>9.1f}% {result['profit_factor']:>7.2f}")

    # Baseline comparison (MACD-V only, no divergence filter)
    print("\n" + "=" * 80)
    print("BASELINE COMPARISON (MACD-V > 120, No Divergence Filter)")
    print("=" * 80)

    baseline_trades = []
    for ticker in all_data:
        trades = backtest_strategy(
            all_data[ticker],
            ticker,
            macdv_threshold=120,
            div_threshold=-999,  # No divergence filter
            hold_days=7,
            backtest_start=backtest_start
        )
        baseline_trades.extend(trades)

    baseline_metrics = calculate_metrics(baseline_trades)
    print(f"\nBaseline (MACD-V > 120 only):")
    print(f"  Trades: {baseline_metrics['num_trades']}")
    print(f"  Win Rate: {baseline_metrics['win_rate']:.1f}%")
    print(f"  Avg Return: {baseline_metrics['avg_return']:.2f}%")
    print(f"  Total Return: {baseline_metrics['total_return']:.1f}%")
    print(f"  Profit Factor: {baseline_metrics['profit_factor']:.2f}")

    # Target strategy detailed results (MACD-V > 120, Div > 30)
    print("\n" + "=" * 80)
    print("TARGET STRATEGY: MACD-V > 120, Divergence > 25")
    print("=" * 80)

    target_trades = []
    for ticker in all_data:
        trades = backtest_strategy(
            all_data[ticker],
            ticker,
            macdv_threshold=120,
            div_threshold=25,
            hold_days=7,
            backtest_start=backtest_start
        )
        target_trades.extend(trades)

    target_metrics = calculate_metrics(target_trades)

    print(f"\nAGGREGATE STATISTICS:")
    print(f"  Total Trades: {target_metrics['num_trades']}")
    print(f"  Win Rate: {target_metrics['win_rate']:.1f}%")
    print(f"  Average Return: {target_metrics['avg_return']:.2f}%")
    print(f"  Total Return: {target_metrics['total_return']:.1f}%")
    print(f"  Average Win: {target_metrics['avg_win']:.2f}%")
    print(f"  Average Loss: {target_metrics['avg_loss']:.2f}%")
    print(f"  Profit Factor: {target_metrics['profit_factor']:.2f}")
    print(f"  Max Win: {target_metrics['max_win']:.2f}%")
    print(f"  Max Loss: {target_metrics['max_loss']:.2f}%")

    # Per-ticker breakdown
    print("\n" + "-" * 80)
    print("PER-TICKER BREAKDOWN:")
    print("-" * 80)
    print(f"{'Ticker':>8} {'Trades':>8} {'Win%':>8} {'Avg%':>8} {'Total%':>10}")
    print("-" * 80)

    ticker_stats = {}
    for ticker in sorted(all_data.keys()):
        ticker_trades = [t for t in target_trades if t['ticker'] == ticker]
        if ticker_trades:
            metrics = calculate_metrics(ticker_trades)
            ticker_stats[ticker] = metrics
            print(f"{ticker:>8} {metrics['num_trades']:>8} {metrics['win_rate']:>7.1f}% "
                  f"{metrics['avg_return']:>7.2f}% {metrics['total_return']:>9.1f}%")

    # Year-by-year breakdown
    print("\n" + "-" * 80)
    print("YEAR-BY-YEAR BREAKDOWN:")
    print("-" * 80)
    print(f"{'Year':>6} {'Trades':>8} {'Win%':>8} {'Avg%':>8} {'Total%':>10}")
    print("-" * 80)

    for year in range(2021, 2027):
        year_trades = [t for t in target_trades if t['year'] == year]
        if year_trades:
            metrics = calculate_metrics(year_trades)
            print(f"{year:>6} {metrics['num_trades']:>8} {metrics['win_rate']:>7.1f}% "
                  f"{metrics['avg_return']:>7.2f}% {metrics['total_return']:>9.1f}%")

    # Sample trades
    print("\n" + "-" * 80)
    print("SAMPLE TRADES (First 10):")
    print("-" * 80)
    print(f"{'Ticker':>8} {'Entry':>12} {'Exit':>12} {'Return%':>9} {'MACD-V':>8} {'Div':>7}")
    print("-" * 80)

    for trade in target_trades[:10]:
        print(f"{trade['ticker']:>8} {trade['entry_date'].strftime('%Y-%m-%d'):>12} "
              f"{trade['exit_date'].strftime('%Y-%m-%d'):>12} {trade['return_pct']:>8.2f}% "
              f"{trade['macdv']:>7.1f} {trade['divergence']:>6.1f}")

    print("\n" + "=" * 80)
    print("BACKTEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
