"""
Kelly Criterion Analyzer for RSI-MA Strategy Universe

Three modes:
  historical_kelly(tickers, lookback=2000)
    → Kelly on full history (stable long-run baseline, asset-level returns)

  dynamic_kelly(tickers, lookback=252)
    → Kelly on last 252 bars (matches RSI-MA percentile window, asset-level)
    → Segments Kelly by RSI-MA percentile bucket

  strategy_kelly(tickers, horizon=5)
    → Kelly on STRATEGY trade returns, not asset returns.
    → For each RSI-MA percentile bucket, finds first-entry events when
      percentile drops INTO that bucket, extracts D5 log returns, and
      computes Kelly on that trade P&L distribution.
    → D5 is the standard reference post-low-percentile entry.
    → This is the correct Kelly for a mean-reversion RSI-MA strategy:
      the underlying asset Kelly says "deleverage" at low percentile
      entries (negative momentum), but the strategy Kelly accounts for
      the actual trade edge at those entries.
"""

from __future__ import annotations

import math
import os
import sys
import warnings
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore", category=FutureWarning)

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from macro_instruments import calculate_rsi_ma, compute_percentile  # noqa: E402


ANNUAL_DAYS = 252

# RSI-MA percentile buckets for regime analysis
PERCENTILE_BUCKETS = [
    (0, 5,   "🔴 <5th"),
    (5, 15,  "🟠 5-15th"),
    (15, 30, "🟡 15-30th"),
    (30, 50, "⚪ 30-50th"),
    (50, 70, "🟢 50-70th"),
    (70, 85, "💚 70-85th"),
    (85, 95, "🔵 85-95th"),
    (95, 100,"💎 >95th"),
]


@dataclass
class KellyResult:
    ticker: str
    optimal_kelly: Optional[float]   # f* = μ / σ²
    half_kelly: Optional[float]
    annualized_return: Optional[float]
    annualized_vol: Optional[float]
    max_growth: Optional[float]      # g(f*) = μ²/(2σ²)
    regime: str                      # "LONG" | "SHORT" | "NEUTRAL"
    error: Optional[str] = None
    bucket_kelly: dict[str, Optional[float]] = field(default_factory=dict)


def _compute_kelly(log_returns: pd.Series) -> tuple[float, float, float]:
    """Return (annualized_mu, annualized_sigma, optimal_f)."""
    n = len(log_returns)
    if n < 20:
        return float("nan"), float("nan"), float("nan")
    mu = log_returns.mean() * ANNUAL_DAYS
    sigma = log_returns.std() * math.sqrt(ANNUAL_DAYS)
    if sigma == 0:
        return mu, sigma, float("nan")
    f_star = mu / (sigma ** 2)
    return mu, sigma, f_star


def _download(tickers: list[str], days: int) -> dict[str, pd.Series]:
    """Download Close price series for all tickers in one batch."""
    period = f"{max(days + 100, 500)}d"
    raw = yf.download(
        tickers,
        period=period,
        progress=False,
        auto_adjust=True,
        threads=True,
    )
    result: dict[str, pd.Series] = {}
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"]
        for t in tickers:
            if t in close.columns:
                s = close[t].dropna()
                result[t] = s
    else:
        # Single ticker
        if "Close" in raw.columns:
            result[tickers[0]] = raw["Close"].dropna()
    return result


def historical_kelly(
    tickers: list[str],
    lookback: int = 2000,
) -> list[KellyResult]:
    """
    Compute Kelly over a long historical window.

    Returns a list sorted descending by optimal_kelly.
    """
    price_data = _download(tickers, lookback)
    results: list[KellyResult] = []

    for ticker in tickers:
        if ticker not in price_data:
            results.append(KellyResult(ticker=ticker, optimal_kelly=None, half_kelly=None,
                                        annualized_return=None, annualized_vol=None,
                                        max_growth=None, regime="N/A", error="download failed"))
            continue

        close = price_data[ticker]
        if len(close) < lookback:
            window = close
        else:
            window = close.iloc[-lookback:]

        log_ret = np.log(window / window.shift(1)).dropna()
        mu, sigma, f_star = _compute_kelly(log_ret)

        if math.isnan(f_star):
            results.append(KellyResult(ticker=ticker, optimal_kelly=None, half_kelly=None,
                                        annualized_return=None, annualized_vol=None,
                                        max_growth=None, regime="N/A", error="insufficient data"))
            continue

        max_growth = mu ** 2 / (2 * sigma ** 2) if sigma > 0 else None
        regime = "LONG" if f_star > 0 else ("SHORT" if f_star < 0 else "NEUTRAL")
        results.append(KellyResult(
            ticker=ticker,
            optimal_kelly=round(f_star, 3),
            half_kelly=round(f_star / 2, 3),
            annualized_return=round(mu * 100, 2),
            annualized_vol=round(sigma * 100, 2),
            max_growth=round(max_growth * 100, 2) if max_growth else None,
            regime=regime,
        ))

    results.sort(key=lambda r: (r.optimal_kelly or -999), reverse=True)
    return results


def dynamic_kelly(
    tickers: list[str],
    lookback: int = 252,
    rsi_ma_lookback: int = 252,
) -> list[KellyResult]:
    """
    Compute Kelly over the recent `lookback` bars (regime-aware).

    Also computes per-RSI-MA-percentile-bucket Kelly for each ticker,
    showing how leverage should vary across momentum regimes.

    Returns sorted descending by current optimal_kelly.
    """
    download_days = max(lookback, rsi_ma_lookback) + 200
    price_data = _download(tickers, download_days)
    results: list[KellyResult] = []

    for ticker in tickers:
        if ticker not in price_data:
            results.append(KellyResult(ticker=ticker, optimal_kelly=None, half_kelly=None,
                                        annualized_return=None, annualized_vol=None,
                                        max_growth=None, regime="N/A", error="download failed"))
            continue

        close = price_data[ticker]
        if len(close) < 60:
            results.append(KellyResult(ticker=ticker, optimal_kelly=None, half_kelly=None,
                                        annualized_return=None, annualized_vol=None,
                                        max_growth=None, regime="N/A", error="insufficient data"))
            continue

        # Current window Kelly (last `lookback` bars)
        window_close = close.iloc[-lookback:] if len(close) >= lookback else close
        log_ret = np.log(window_close / window_close.shift(1)).dropna()
        mu, sigma, f_star = _compute_kelly(log_ret)

        if math.isnan(f_star):
            results.append(KellyResult(ticker=ticker, optimal_kelly=None, half_kelly=None,
                                        annualized_return=None, annualized_vol=None,
                                        max_growth=None, regime="N/A", error="insufficient data"))
            continue

        max_growth = mu ** 2 / (2 * sigma ** 2) if sigma > 0 else None
        regime = "LONG" if f_star > 0 else ("SHORT" if f_star < 0 else "NEUTRAL")

        # RSI-MA percentile bucket Kelly
        # Build RSI-MA series and rolling percentile for full history
        full_log_ret = np.log(close / close.shift(1)).dropna()
        rsi_ma_series = calculate_rsi_ma(close)

        rolling_pct = rsi_ma_series.rolling(rsi_ma_lookback, min_periods=rsi_ma_lookback).rank(pct=True) * 100

        # Build aligned DataFrame
        df = pd.DataFrame({
            "close": close,
            "log_ret": np.log(close / close.shift(1)),
            "rsi_pct": rolling_pct,
        }).dropna()

        bucket_kelly: dict[str, Optional[float]] = {}
        for lo, hi, label in PERCENTILE_BUCKETS:
            mask = (df["rsi_pct"] >= lo) & (df["rsi_pct"] < hi)
            bucket_rets = df.loc[mask, "log_ret"]
            if len(bucket_rets) < 20:
                bucket_kelly[label] = None
                continue
            b_mu, b_sigma, b_f = _compute_kelly(bucket_rets)
            bucket_kelly[label] = round(b_f, 3) if not math.isnan(b_f) else None

        results.append(KellyResult(
            ticker=ticker,
            optimal_kelly=round(f_star, 3),
            half_kelly=round(f_star / 2, 3),
            annualized_return=round(mu * 100, 2),
            annualized_vol=round(sigma * 100, 2),
            max_growth=round(max_growth * 100, 2) if max_growth else None,
            regime=regime,
            bucket_kelly=bucket_kelly,
        ))

    results.sort(key=lambda r: (r.optimal_kelly or -999), reverse=True)
    return results


# ---------------------------------------------------------------------------
# Telegram formatters
# ---------------------------------------------------------------------------

def _kelly_bar(f: float, max_abs: float = 5.0) -> str:
    """Simple ASCII bar ████░░░░ scaled to max_abs leverage."""
    if f <= 0:
        return "🔴 short/flat"
    filled = min(int(f / max_abs * 8), 8)
    return "█" * filled + "░" * (8 - filled)


def format_historical_kelly(results: list[KellyResult], title: str = "Historical") -> str:
    longs  = [r for r in results if r.optimal_kelly and r.optimal_kelly > 0]
    shorts = [r for r in results if r.optimal_kelly and r.optimal_kelly < 0]
    errors = [r for r in results if r.error]

    lines = [
        f"<b>📐 KELLY — {title.upper()}</b>",
        "<i>Long-run edge ranked by ½-Kelly</i>",
        "",
        "<pre>",
        f"{'Ticker':<7} {'½-Kelly':>7}  {'Ret%':>6}  {'Vol%':>5}",
        "─" * 30,
    ]

    if not longs:
        lines.append("  (none in long regime)")
    for r in longs:
        hk  = r.half_kelly or 0.0
        ret = r.annualized_return or 0.0
        vol = r.annualized_vol or 0.0
        lines.append(f"{r.ticker:<7} {f'+{hk:.1f}x':>7}  {f'{ret:+.0f}%':>6}  {f'{vol:.0f}%':>5}")

    if shorts:
        lines.append("─" * 30)
        for r in sorted(shorts, key=lambda x: x.optimal_kelly, reverse=True):
            hk  = r.half_kelly or 0.0
            ret = r.annualized_return or 0.0
            vol = r.annualized_vol or 0.0
            lines.append(f"{r.ticker:<7} {f'{hk:+.1f}x':>7}  {f'{ret:+.0f}%':>6}  {f'{vol:.0f}%':>5}")

    lines.append("</pre>")

    if errors:
        lines += ["", f"<i>⚠️ No data: {', '.join(r.ticker for r in errors)}</i>"]

    lines += [
        "",
        "<b>KEY</b>",
        "½-Kelly = recommended position size",
        "  +2.0x = size 2× your normal allocation",
        "  +0.5x = half your normal allocation",
        "Ret% = annualised return · Vol% = annualised vol",
        "Above divider = LONG edge · Below = short/avoid",
        "<i>⚠️ Raw Kelly overestimates — apply ¼ to ½ of value if uncertain</i>",
    ]

    return "\n".join(lines)


def format_dynamic_kelly(results: list[KellyResult]) -> str:
    valid = [r for r in results if not r.error and r.optimal_kelly is not None]
    longs  = [r for r in valid if r.optimal_kelly >= 0]
    shorts = [r for r in valid if r.optimal_kelly < 0]

    lines = [
        "<b>⚡ KELLY — DYNAMIC (252-day)</b>",
        "<i>Ranked by ½-Kelly · use this to size positions</i>",
        "",
        "<pre>",
        f"{'Ticker':<7} {'½-Kelly':>7}  {'Ret%':>6}  {'Vol%':>5}",
        "─" * 30,
    ]

    for r in longs:
        hk = r.half_kelly or 0.0
        ret = r.annualized_return or 0.0
        vol = r.annualized_vol or 0.0
        lines.append(f"{r.ticker:<7} {f'+{hk:.1f}x':>7}  {f'{ret:+.0f}%':>6}  {f'{vol:.0f}%':>5}")

    if shorts:
        lines.append("─" * 30)
        for r in shorts:
            hk = r.half_kelly or 0.0
            ret = r.annualized_return or 0.0
            vol = r.annualized_vol or 0.0
            lines.append(f"{r.ticker:<7} {f'{hk:+.1f}x':>7}  {f'{ret:+.0f}%':>6}  {f'{vol:.0f}%':>5}")

    lines += [
        "</pre>",
        "",
        "<b>KEY</b>",
        "½-Kelly = recommended position size",
        "  e.g. +2.0x = size 2× your normal allocation",
        "  e.g. +0.5x = size at half your normal allocation",
        "Ret% = annualised return over last 252 days",
        "Vol% = annualised volatility over last 252 days",
        "Above divider = LONG edge · Below = short/avoid",
        "",
        "<i>⚠️ Raw Kelly overestimates — apply ¼ to ½ of the value shown if in doubt</i>",
    ]

    return "\n".join(lines)


def format_percentile_kelly(results: list[KellyResult]) -> str:
    """
    Show universe-average ½-Kelly at each RSI-MA percentile bucket with a
    plain action label — no per-ticker detail, just the regime sizing guide.
    """
    bucket_labels = [label for _, _, label in PERCENTILE_BUCKETS]

    bucket_averages: dict[str, list[float]] = {lbl: [] for lbl in bucket_labels}
    for r in results:
        if not r.bucket_kelly:
            continue
        for lbl in bucket_labels:
            v = r.bucket_kelly.get(lbl)
            if v is not None:
                bucket_averages[lbl].append(v)

    lines = [
        "<b>🎯 SIZE BY RSI-MA REGIME (dynamic Kelly)</b>",
        "<i>Universe avg ½-Kelly when RSI-MA is at each percentile</i>",
        "<i>Tells you when to size up or down relative to your base</i>",
        "",
    ]

    for lbl in bucket_labels:
        vals = bucket_averages[lbl]
        if not vals:
            lines.append(f"{lbl}  —  no data")
            continue
        avg_f  = sum(vals) / len(vals)   # universe avg full Kelly
        avg_hk = avg_f / 2               # half-Kelly
        sign   = "+" if avg_hk >= 0 else ""

        if avg_hk >= 1.5:
            action = "▲▲ SIZE UP"
        elif avg_hk >= 0.5:
            action = "▲  normal+"
        elif avg_hk >= 0.0:
            action = "=  base"
        else:
            action = "▼▼ REDUCE"

        lines.append(f"{lbl}   ½K={sign}{avg_hk:.1f}x   {action}")

    lines += [
        "",
        "<i>Low %ile = oversold RSI-MA = mean-reversion entry zone.</i>",
        "<i>Use /kelly_strategy for trade-level Kelly at each bucket</i>",
        "<i>(often higher at low %ile due to mean-reversion edge).</i>",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Strategy Kelly — trade P&L at each percentile bucket, D5 reference horizon
# ---------------------------------------------------------------------------

@dataclass
class StrategyKellyResult:
    ticker: str
    bucket_results: dict[str, dict]  # label → {kelly, half_kelly, mu, sigma, n_trades, win_rate}
    overall_kelly: Optional[float]   # across all entry buckets combined
    error: Optional[str] = None


def _find_entry_events(
    pct_series: pd.Series,
    close: pd.Series,
    lo: float,
    hi: float,
    horizon: int = 5,
) -> list[float]:
    """
    Return list of D{horizon} log-returns for first-entry events into [lo, hi) bucket.

    'First entry' = bar where percentile crosses into [lo, hi) from above or outside.
    We skip re-entries within 2*horizon bars of the previous entry to avoid overlapping trades.
    """
    aligned = pd.DataFrame({"pct": pct_series, "close": close}).dropna()
    pct_arr   = aligned["pct"].to_numpy()
    close_arr = aligned["close"].to_numpy()
    n = len(aligned)

    in_bucket = (pct_arr >= lo) & (pct_arr < hi)
    prev_in   = np.empty(n, dtype=bool)
    prev_in[0] = False
    prev_in[1:] = in_bucket[:-1]
    crossover = in_bucket & ~prev_in

    trade_returns: list[float] = []
    last_entry_i = -999

    for pos in range(n):
        if not crossover[pos]:
            continue
        if pos - last_entry_i < 2 * horizon:
            continue
        exit_pos = pos + horizon
        if exit_pos >= n:
            break
        entry_price = close_arr[pos]
        exit_price  = close_arr[exit_pos]
        if entry_price > 0 and exit_price > 0:
            trade_returns.append(math.log(exit_price / entry_price))
        last_entry_i = pos

    return trade_returns


def strategy_kelly(
    tickers: list[str],
    horizon: int = 5,
    rsi_ma_lookback: int = 252,
    download_days: int = 2500,
) -> list[StrategyKellyResult]:
    """
    Compute Kelly on strategy trade returns (D{horizon}) per RSI-MA percentile bucket.

    This is the correct Kelly for a mean-reversion RSI-MA strategy because:
    - Asset-level Kelly at low-percentile entries is negative (negative momentum)
    - Strategy-level Kelly accounts for the ACTUAL trade edge from those entries
    - D5 is the standard measurement horizon post-low-percentile entry
    """
    price_data = _download(tickers, download_days)
    results: list[StrategyKellyResult] = []

    for ticker in tickers:
        if ticker not in price_data:
            results.append(StrategyKellyResult(ticker=ticker, bucket_results={},
                                                overall_kelly=None, error="download failed"))
            continue

        close = price_data[ticker]
        if len(close) < rsi_ma_lookback + horizon + 20:
            results.append(StrategyKellyResult(ticker=ticker, bucket_results={},
                                                overall_kelly=None, error="insufficient data"))
            continue

        rsi_ma_series = calculate_rsi_ma(close)
        rolling_pct = rsi_ma_series.rolling(rsi_ma_lookback, min_periods=rsi_ma_lookback).rank(pct=True) * 100

        bucket_results: dict[str, dict] = {}
        all_trade_returns: list[float] = []

        for lo, hi, label in PERCENTILE_BUCKETS:
            trade_rets = _find_entry_events(rolling_pct, close, lo, hi, horizon)
            all_trade_returns.extend(trade_rets)

            if len(trade_rets) < 5:
                bucket_results[label] = {
                    "kelly": None, "half_kelly": None,
                    "mu_pct": None, "sigma_pct": None,
                    "n_trades": len(trade_rets), "win_rate": None,
                }
                continue

            arr = np.array(trade_rets)
            mu    = arr.mean()
            sigma = arr.std()
            f_star = (mu / (sigma ** 2)) if sigma > 0 else float("nan")
            win_rate = float((arr > 0).sum() / len(arr) * 100)

            bucket_results[label] = {
                "kelly":     round(f_star, 3) if not math.isnan(f_star) else None,
                "half_kelly": round(f_star / 2, 3) if not math.isnan(f_star) else None,
                "mu_pct":    round(mu * 100, 2),
                "sigma_pct": round(sigma * 100, 2),
                "n_trades":  len(trade_rets),
                "win_rate":  round(win_rate, 1),
            }

        # Overall Kelly across all entry events
        if len(all_trade_returns) >= 10:
            arr_all = np.array(all_trade_returns)
            mu_all    = arr_all.mean()
            sig_all   = arr_all.std()
            overall_f = (mu_all / (sig_all ** 2)) if sig_all > 0 else None
        else:
            overall_f = None

        results.append(StrategyKellyResult(
            ticker=ticker,
            bucket_results=bucket_results,
            overall_kelly=round(overall_f, 3) if overall_f and not math.isnan(overall_f) else None,
        ))

    results.sort(key=lambda r: (r.overall_kelly or -999), reverse=True)
    return results


def format_strategy_kelly(results: list[StrategyKellyResult], horizon: int = 5) -> str:
    """
    Format strategy Kelly results — how leverage should vary per RSI-MA percentile bucket.

    This is the key output: it shows whether low-percentile entries (mean reversion buys)
    historically warranted MORE or LESS leverage based on the actual D{horizon} trade P&L.
    """
    bucket_labels = [label for _, _, label in PERCENTILE_BUCKETS]

    lines = [
        f"<b>📊 STRATEGY KELLY — D{horizon} TRADE RETURNS BY RSI-MA BUCKET</b>",
        f"<i>Kelly computed on actual trade P&L (entry→D{horizon}), not raw asset returns.</i>",
        f"<i>Pos Kelly = lever up at that percentile | Neg = reduce/skip</i>",
        "",
        "<b>── Universe Average per Bucket ──</b>",
    ]

    # Universe-level averages per bucket
    for lbl in bucket_labels:
        kellys   = [r.bucket_results.get(lbl, {}).get("kelly") for r in results if r.bucket_results.get(lbl, {}).get("kelly") is not None]
        mus      = [r.bucket_results.get(lbl, {}).get("mu_pct") for r in results if r.bucket_results.get(lbl, {}).get("mu_pct") is not None]
        wins     = [r.bucket_results.get(lbl, {}).get("win_rate") for r in results if r.bucket_results.get(lbl, {}).get("win_rate") is not None]
        if not kellys:
            lines.append(f"  {lbl:<14}  no data")
            continue
        avg_k   = sum(kellys) / len(kellys)
        avg_mu  = sum(mus) / len(mus) if mus else 0.0
        avg_win = sum(wins) / len(wins) if wins else 0.0
        sign = "+" if avg_k >= 0 else ""
        direction = "▲ leverage" if avg_k > 0.5 else ("▼ reduce" if avg_k < 0 else "= neutral")
        lines.append(
            f"  {lbl:<14}  f*={sign}{avg_k:.2f}x  μ={avg_mu:+.2f}%  win={avg_win:.0f}%  {direction}"
        )

    lines += ["", "<b>── Per-Ticker Ranking (overall Kelly, strategy entries) ──</b>"]
    for r in results:
        if r.error or r.overall_kelly is None:
            continue
        sign = "+" if r.overall_kelly >= 0 else ""
        lines.append(f"  <b>{r.ticker:<8}</b>  f*={sign}{r.overall_kelly:.2f}x (all buckets combined)")

    lines += ["", "<b>── Low Percentile Focus (<15th) ──</b>",
              "<i>This is where your RSI-MA mean-reversion entries happen</i>"]
    low_bucket_labels = ["🔴 <5th", "🟠 5-15th"]
    low_rows = []
    for r in results:
        if r.error:
            continue
        vals = []
        for lbl in low_bucket_labels:
            v = r.bucket_results.get(lbl, {}).get("kelly")
            if v is not None:
                vals.append(v)
        if vals:
            avg = sum(vals) / len(vals)
            mu_vals = [r.bucket_results.get(lbl, {}).get("mu_pct") for lbl in low_bucket_labels
                       if r.bucket_results.get(lbl, {}).get("mu_pct") is not None]
            n_trades = sum(r.bucket_results.get(lbl, {}).get("n_trades", 0) for lbl in low_bucket_labels)
            low_rows.append((r.ticker, avg, sum(mu_vals) / len(mu_vals) if mu_vals else 0, n_trades))

    low_rows.sort(key=lambda x: x[1], reverse=True)
    for ticker, avg_k, avg_mu, n in low_rows:
        sign = "+" if avg_k >= 0 else ""
        lines.append(f"  <b>{ticker:<8}</b>  f*={sign}{avg_k:.2f}x  μ={avg_mu:+.2f}%  n={n} trades")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Convenience runner
# ---------------------------------------------------------------------------

def run_full_analysis(
    tickers: list[str],
    hist_lookback: int = 2000,
    dyn_lookback: int = 252,
    strategy_horizon: int = 5,
) -> dict:
    """Run historical, dynamic, and strategy Kelly. Return all results."""
    print(f"[kelly] Historical Kelly ({hist_lookback}-day)...")
    hist = historical_kelly(tickers, lookback=hist_lookback)

    print(f"[kelly] Dynamic Kelly ({dyn_lookback}-day) with RSI-MA percentile buckets...")
    dyn = dynamic_kelly(tickers, lookback=dyn_lookback, rsi_ma_lookback=252)

    print(f"[kelly] Strategy Kelly — D{strategy_horizon} trade returns per percentile bucket...")
    strat = strategy_kelly(tickers, horizon=strategy_horizon)

    return {"historical": hist, "dynamic": dyn, "strategy": strat}


if __name__ == "__main__":
    import argparse
    from macdv_calculator import SWING_FRAMEWORK_TICKERS
    from telegram_bot import split_and_send, is_configured

    parser = argparse.ArgumentParser(description="Kelly Criterion Analyzer")
    parser.add_argument("--mode", choices=["all", "historical", "dynamic", "strategy"],
                        default="all", help="Which analysis to run")
    parser.add_argument("--horizon", type=int, default=5, help="D-horizon for strategy Kelly (default 5)")
    parser.add_argument("--hist-lookback", type=int, default=2000)
    parser.add_argument("--dyn-lookback",  type=int, default=252)
    parser.add_argument("--no-telegram", action="store_true", help="Print only, don't send")
    args = parser.parse_args()

    res = run_full_analysis(
        SWING_FRAMEWORK_TICKERS,
        hist_lookback=args.hist_lookback,
        dyn_lookback=args.dyn_lookback,
        strategy_horizon=args.horizon,
    )

    msgs = []

    if args.mode in ("all", "historical"):
        msgs.append(format_historical_kelly(res["historical"], title=f"Historical ({args.hist_lookback}-day)"))

    if args.mode in ("all", "dynamic"):
        msgs.append(format_dynamic_kelly(res["dynamic"]))
        msgs.append(format_percentile_kelly(res["dynamic"]))

    if args.mode in ("all", "strategy"):
        msgs.append(format_strategy_kelly(res["strategy"], horizon=args.horizon))

    for msg in msgs:
        print("\n" + "=" * 60)
        print(msg)

    if not args.no_telegram and is_configured():
        for msg in msgs:
            split_and_send(msg)
        print("[kelly] Sent to Telegram.")
    elif args.no_telegram:
        print("[kelly] --no-telegram flag set, output to stdout only.")
    else:
        print("[kelly] Telegram not configured — output to stdout only.")
