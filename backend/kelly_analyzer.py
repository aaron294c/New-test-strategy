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

  return_variance_matrix(tickers, lookback=252)
    → Annualized return covariance and correlation matrix with Ledoit-Wolf
      shrinkage across a universe of tickers.

  portfolio_kelly(tickers, lookback=252, fraction=0.5, max_total_leverage=3.0, long_only=True)
    → Multi-asset Kelly weights using w* = Σ^{-1} μ covariance formula.
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
    Explains why the asset-level percentile Kelly is misleading for a
    mean-reversion strategy, and points to /kelly_strategy instead.
    """
    return "\n".join([
        "<b>⚠️ REGIME SIZING — USE /kelly_strategy INSTEAD</b>",
        "",
        "The table above shows <b>asset momentum Kelly</b> — how much",
        "edge the asset itself has over the last 252 days.",
        "",
        "For sizing your <b>RSI-MA mean-reversion entries</b>, asset",
        "momentum Kelly gives the wrong answer at low percentiles:",
        "",
        "  🔴 &lt;5th %ile  → asset is falling → asset Kelly says REDUCE",
        "  💎 &gt;95th %ile → asset is rising  → asset Kelly says SIZE UP",
        "",
        "That's <b>backwards</b> for a mean-reversion strategy.",
        "You buy at low percentiles <i>because</i> they're oversold.",
        "",
        "👉 Use <b>/kelly_strategy</b> — it computes Kelly on actual",
        "D5 trade returns from entries at each percentile bucket.",
        "That correctly captures the mean-reversion edge and will",
        "typically show <b>higher</b> Kelly at low percentiles.",
    ])


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
    Three-section output:
      1. Universe average ½-Kelly per RSI-MA bucket (regime sizing guide)
      2. Entry zone focus: all tickers ranked by ½-Kelly at <15th %ile entries
      3. Overall ½-Kelly per ticker (all entry types combined)
    """
    bucket_labels   = [label for _, _, label in PERCENTILE_BUCKETS]
    low_labels      = ["🔴 <5th", "🟠 5-15th"]
    # Short text labels for <pre> table (no emoji alignment issues)
    short_labels    = ["<5th", "5-15th", "15-30th", "30-50th",
                       "50-70th", "70-85th", "85-95th", ">95th"]

    # ── 1. Universe averages ────────────────────────────────────────────────
    lines = [
        f"<b>📊 STRATEGY KELLY — D{horizon} ENTRIES</b>",
        f"<i>Kelly on actual trade P&L from RSI-MA entries (not raw asset returns).</i>",
        f"<i>Positive ½K = mean-reversion edge at that regime → size up.</i>",
        "",
        "<b>UNIVERSE AVERAGE — all tickers</b>",
        "<pre>",
        f"{'Regime':<8} {'½K':>5}  {'D5Ret':>6}  {'Win%':>5}  Action",
        "─" * 42,
    ]

    for lbl, short in zip(bucket_labels, short_labels):
        kellys = [r.bucket_results.get(lbl, {}).get("kelly")
                  for r in results if r.bucket_results.get(lbl, {}).get("kelly") is not None]
        mus    = [r.bucket_results.get(lbl, {}).get("mu_pct")
                  for r in results if r.bucket_results.get(lbl, {}).get("mu_pct") is not None]
        wins   = [r.bucket_results.get(lbl, {}).get("win_rate")
                  for r in results if r.bucket_results.get(lbl, {}).get("win_rate") is not None]
        if not kellys:
            lines.append(f"{short:<8}  n/a")
            continue
        avg_k   = sum(kellys) / len(kellys)
        avg_hk  = avg_k / 2
        avg_mu  = sum(mus)  / len(mus)  if mus  else 0.0
        avg_win = sum(wins) / len(wins) if wins else 0.0
        sign    = "+" if avg_hk >= 0 else ""
        action  = "▲▲ SIZE UP" if avg_hk >= 1.0 else ("▲ up" if avg_hk >= 0.3 else ("= base" if avg_hk >= 0 else "▼ reduce"))
        is_key  = " ★" if short in ("<5th", "5-15th") else ""
        lines.append(
            f"{short:<8} {f'{sign}{avg_hk:.1f}x':>5}  {f'{avg_mu:+.2f}%':>6}  {f'{avg_win:.0f}%':>5}  {action}{is_key}"
        )

    lines += [
        "</pre>",
        "<i>★ = your RSI-MA mean-reversion entry zone</i>",
        "<i>½K = half-Kelly · D5Ret = avg 5-day trade return · Win% = % profitable</i>",
    ]

    # ── 2. Entry zone focus: all tickers at <15th %ile ──────────────────────
    low_rows: list[tuple] = []
    for r in results:
        if r.error:
            continue
        f_vals, mu_vals, win_vals, n_total = [], [], [], 0
        for lbl in low_labels:
            b = r.bucket_results.get(lbl, {})
            if b.get("kelly") is not None:
                f_vals.append(b["kelly"])
            if b.get("mu_pct") is not None:
                mu_vals.append(b["mu_pct"])
            if b.get("win_rate") is not None:
                win_vals.append(b["win_rate"])
            n_total += b.get("n_trades", 0)
        if not f_vals:
            continue
        avg_f  = sum(f_vals)  / len(f_vals)
        avg_mu = sum(mu_vals) / len(mu_vals) if mu_vals else 0.0
        avg_win= sum(win_vals)/ len(win_vals) if win_vals else 0.0
        low_rows.append((r.ticker, avg_f / 2, avg_mu, avg_win, n_total))

    low_rows.sort(key=lambda x: x[1], reverse=True)

    lines += [
        "",
        "<b>ENTRY ZONE &lt;15th %ile — all tickers ranked</b>",
        "<i>When THIS ticker's RSI-MA drops below 15th %ile, size as shown.</i>",
        "<pre>",
        f"{'Ticker':<9} {'½K':>5}  {'D5Ret':>6}  {'Win%':>5}  {'N':>4}",
        "─" * 36,
    ]
    for ticker, hk, mu, win, n in low_rows:
        sign = "+" if hk >= 0 else ""
        lines.append(f"{ticker:<9} {f'{sign}{hk:.1f}x':>5}  {f'{mu:+.2f}%':>6}  {f'{win:.0f}%':>5}  {n:>4}")
    lines += [
        "</pre>",
        "<i>Negative ½K = no mean-reversion edge for this ticker at low %ile</i>",
    ]

    # ── 3. Overall Kelly per ticker (all entries combined) ───────────────────
    lines += [
        "",
        "<b>OVERALL KELLY — all entry types combined</b>",
        "<pre>",
        f"{'Ticker':<9} {'½K':>5}",
        "─" * 16,
    ]
    for r in results:
        if r.error or r.overall_kelly is None:
            continue
        hk   = r.overall_kelly / 2
        sign = "+" if hk >= 0 else ""
        lines.append(f"{r.ticker:<9} {f'{sign}{hk:.1f}x':>5}")
    lines += [
        "</pre>",
        "",
        "<i>⚠️ Raw Kelly overestimates risk — apply ¼ to ½ of ½K shown if uncertain.</i>",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Return variance matrix and portfolio Kelly
# ---------------------------------------------------------------------------

def return_variance_matrix(tickers, lookback=252):
    """
    Compute annualized return covariance and correlation matrix across tickers.

    Uses Ledoit-Wolf shrinkage if sklearn is available; falls back to manual
    diagonal shrinkage: (1-alpha)*Sigma + alpha*diag(Sigma) where
    alpha = min(0.5, p/n), p = num tickers, n = num observations.

    Filters to tickers with at least lookback//2 observations.

    Returns a dict with keys:
      cov_matrix      – pd.DataFrame, annualized shrunk covariance
      corr_matrix     – pd.DataFrame, correlation derived from cov_matrix
      mean_vector     – pd.Series, annualized mean log return per ticker
      vol_vector      – pd.Series, annualized vol in % per ticker
      tickers_valid   – list of tickers that passed the data filter
      n_obs           – int, number of common date observations used
      lookback        – int, lookback parameter passed in
      shrinkage_coeff – float, shrinkage coefficient applied
    """
    min_obs = lookback // 2
    price_data = _download(tickers, lookback + 100)

    # Build log-return DataFrame aligned on common dates
    ret_dict = {}
    for t in tickers:
        if t not in price_data:
            continue
        close = price_data[t]
        log_ret = np.log(close / close.shift(1)).dropna()
        if len(log_ret) >= min_obs:
            ret_dict[t] = log_ret

    if not ret_dict:
        return {"error": "No tickers with sufficient data"}

    returns_df = pd.DataFrame(ret_dict).dropna()

    # Use last lookback observations after alignment
    if len(returns_df) > lookback:
        returns_df = returns_df.iloc[-lookback:]

    n, p = returns_df.shape
    tickers_valid = list(returns_df.columns)

    # Attempt Ledoit-Wolf shrinkage via sklearn
    shrinkage_coeff = None
    try:
        from sklearn.covariance import LedoitWolf
        lw = LedoitWolf()
        lw.fit(returns_df.values)
        cov_raw = pd.DataFrame(
            lw.covariance_ * ANNUAL_DAYS,
            index=tickers_valid,
            columns=tickers_valid,
        )
        shrinkage_coeff = float(lw.shrinkage_)
    except Exception:
        # Manual diagonal shrinkage fallback
        sample_cov = returns_df.cov() * ANNUAL_DAYS
        alpha = min(0.5, p / n)
        diag_cov = np.diag(np.diag(sample_cov.values))
        cov_raw_values = (1 - alpha) * sample_cov.values + alpha * diag_cov
        cov_raw = pd.DataFrame(cov_raw_values, index=tickers_valid, columns=tickers_valid)
        shrinkage_coeff = alpha

    # Derive correlation matrix from shrunk covariance
    vols = np.sqrt(np.diag(cov_raw.values))
    outer_vols = np.outer(vols, vols)
    with np.errstate(invalid="ignore"):
        corr_values = np.where(outer_vols > 0, cov_raw.values / outer_vols, 0.0)
    corr_matrix = pd.DataFrame(corr_values, index=tickers_valid, columns=tickers_valid)

    # Mean vector (annualized) and vol vector (annualized, in %)
    mean_vector = returns_df.mean() * ANNUAL_DAYS
    vol_vector = vols * 100  # already annualized (sqrt of annual cov diagonal)
    vol_series = pd.Series(vol_vector, index=tickers_valid)

    return {
        "cov_matrix": cov_raw,
        "corr_matrix": corr_matrix,
        "mean_vector": mean_vector,
        "vol_vector": vol_series,
        "tickers_valid": tickers_valid,
        "n_obs": n,
        "lookback": lookback,
        "shrinkage_coeff": round(shrinkage_coeff, 4),
    }


def portfolio_kelly(tickers, lookback=252, fraction=0.5, max_total_leverage=3.0, long_only=True):
    """
    Compute multi-asset Kelly weights using the covariance matrix formula:
      w* = Σ^{-1} μ

    where μ is the annualized mean log-return vector and Σ is the annualized
    covariance matrix (Ledoit-Wolf shrunk).

    Parameters
    ----------
    tickers          : list of ticker symbols
    lookback         : int, lookback window for variance matrix (default 252)
    fraction         : float, fractional Kelly scaling (default 0.5 = half-Kelly)
    max_total_leverage : float, cap on sum(|weights|) (default 3.0)
    long_only        : bool, zero out negative weights (default True)

    Returns a dict with keys:
      weights         – pd.Series, final position weights (fraction-scaled, capped)
      kelly_raw       – pd.Series, unconstrained full-Kelly weights
      total_leverage  – float, sum of |final weights|
      n_positions     – int, number of non-zero positions
      tickers_valid   – list
      variance_matrix – dict returned by return_variance_matrix()
      params          – dict of parameters used

    On matrix inversion failure returns {"error": "Covariance matrix not invertible"}.
    """
    vm = return_variance_matrix(tickers, lookback=lookback)
    if "error" in vm:
        return {"error": vm["error"]}

    cov = vm["cov_matrix"].values
    mu = vm["mean_vector"].values
    tickers_valid = vm["tickers_valid"]
    p = len(tickers_valid)

    # Regularize covariance matrix
    eps = 1e-6 * np.trace(cov) / p
    cov_reg = cov + eps * np.eye(p)

    try:
        cov_inv = np.linalg.inv(cov_reg)
    except np.linalg.LinAlgError:
        return {"error": "Covariance matrix not invertible"}

    weights_raw = cov_inv @ mu
    kelly_raw = pd.Series(weights_raw, index=tickers_valid)

    # Apply fractional Kelly
    weights = weights_raw * fraction

    # Long-only constraint
    if long_only:
        weights = np.maximum(weights, 0.0)

    # Cap total leverage
    total_lev = float(np.sum(np.abs(weights)))
    if total_lev > max_total_leverage and total_lev > 0:
        weights = weights * (max_total_leverage / total_lev)

    weights_series = pd.Series(weights, index=tickers_valid)
    final_leverage = float(np.sum(np.abs(weights_series)))
    n_positions = int((weights_series != 0).sum())

    return {
        "weights": weights_series,
        "kelly_raw": kelly_raw,
        "total_leverage": round(final_leverage, 3),
        "n_positions": n_positions,
        "tickers_valid": tickers_valid,
        "variance_matrix": vm,
        "params": {
            "lookback": lookback,
            "fraction": fraction,
            "max_total_leverage": max_total_leverage,
            "long_only": long_only,
        },
    }


def format_variance_matrix(vm_result, top_n=20):
    """
    Format the return variance matrix for Telegram HTML output.

    Shows top top_n tickers by volatility, their annualized vol and mean return,
    and a high-correlation table (ρ > 0.60, top 3 peers per ticker).
    """
    if "error" in vm_result:
        return f"<b>Variance Matrix Error</b>\n{vm_result['error']}"

    lookback = vm_result["lookback"]
    n_obs = vm_result["n_obs"]
    shrinkage = vm_result["shrinkage_coeff"]
    shrinkage_pct = round(shrinkage * 100, 1)
    vol_vec = vm_result["vol_vector"]
    mean_vec = vm_result["mean_vector"]
    corr_matrix = vm_result["corr_matrix"]
    tickers_valid = vm_result["tickers_valid"]
    n_tickers = len(tickers_valid)

    # Select top_n tickers by descending volatility
    sorted_by_vol = vol_vec.sort_values(ascending=False)
    display_tickers = list(sorted_by_vol.index[:top_n])

    lines = [
        f"<b>📊 RETURN VARIANCE MATRIX — {lookback}-DAY</b>",
        f"<i>Shrinkage: {shrinkage_pct}% | n_obs: {n_obs} | tickers: {n_tickers}</i>",
        "",
        "<b>ANNUALIZED VOL &amp; RETURN</b>",
        "<pre>",
        f"{'Ticker':<7}  {'Vol%':>5}  {'Ret%':>6}",
        "─" * 22,
    ]

    for t in display_tickers:
        v = vol_vec.get(t, float("nan"))
        m = mean_vec.get(t, float("nan")) * 100  # convert to %
        v_str = f"{v:.0f}%" if not math.isnan(v) else "n/a"
        m_str = f"{m:+.0f}%" if not math.isnan(m) else "n/a"
        lines.append(f"{t:<7}  {v_str:>5}  {m_str:>6}")

    lines.append("</pre>")

    # High-correlation section
    corr_lines = []
    corr_sub = corr_matrix.loc[display_tickers, display_tickers]
    for t in display_tickers:
        row = corr_sub.loc[t].drop(labels=[t], errors="ignore")
        high_corr = row[row > 0.60].sort_values(ascending=False).head(3)
        if high_corr.empty:
            continue
        peers = " | ".join(f"ρ={rho:.2f} {peer}" for peer, rho in high_corr.items())
        corr_lines.append(f"{t:<7}  {peers}")

    if corr_lines:
        lines += [
            "",
            "<b>HIGH CORRELATIONS (ρ > 0.60)</b>",
            "<pre>",
        ]
        lines.extend(corr_lines)
        lines.append("</pre>")

    return "\n".join(lines)


def format_portfolio_kelly(pk_result):
    """
    Format multi-asset Kelly weights for Telegram HTML output.

    Shows positions sorted by weight descending, total leverage, and a
    stability warning.
    """
    if "error" in pk_result:
        return f"<b>Portfolio Kelly Error</b>\n{pk_result['error']}"

    weights = pk_result["weights"].sort_values(ascending=False)
    total_lev = pk_result["total_leverage"]
    n_pos = pk_result["n_positions"]
    params = pk_result["params"]
    fraction = params["fraction"]
    long_only = params["long_only"]

    lines = [
        "<b>🎯 PORTFOLIO KELLY — MULTI-ASSET</b>",
        "<i>Uses Σ⁻¹μ covariance matrix formula. Half-Kelly applied.</i>",
        "",
        "<pre>",
        f"{'Ticker':<7}  {'Weight':>7}  Action",
        "─" * 26,
    ]

    for ticker, w in weights.items():
        if w == 0.0:
            continue
        sign = "+" if w >= 0 else ""
        w_str = f"{sign}{w:.2f}x"
        if w >= 2.0:
            action = "▲▲ SIZE"
        elif w >= 0.5:
            action = "▲ up"
        elif w > 0:
            action = "= base"
        else:
            action = "▼ short"
        lines.append(f"{ticker:<7}  {w_str:>7}  {action}")

    lines += [
        "─" * 26,
        f"Total:   {total_lev:.1f}x leverage",
        f"{'Long' if long_only else 'Net'} positions: {n_pos}",
        "</pre>",
        "<i>⚠️ Matrix Kelly can be unstable — apply ¼ to ½ of shown values.</i>",
        "<i>Correlations reduce redundant positions vs single-asset Kelly.</i>",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Convenience runner
# ---------------------------------------------------------------------------

def run_full_analysis(
    tickers: list[str],
    hist_lookback: int = 2000,
    dyn_lookback: int = 252,
    strategy_horizon: int = 5,
    portfolio: bool = False,
) -> dict:
    """Run historical, dynamic, and strategy Kelly. Return all results."""
    print(f"[kelly] Historical Kelly ({hist_lookback}-day)...")
    hist = historical_kelly(tickers, lookback=hist_lookback)

    print(f"[kelly] Dynamic Kelly ({dyn_lookback}-day) with RSI-MA percentile buckets...")
    dyn = dynamic_kelly(tickers, lookback=dyn_lookback, rsi_ma_lookback=252)

    print(f"[kelly] Strategy Kelly — D{strategy_horizon} trade returns per percentile bucket...")
    strat = strategy_kelly(tickers, horizon=strategy_horizon)

    result = {"historical": hist, "dynamic": dyn, "strategy": strat}

    if portfolio:
        print("[kelly] Portfolio Kelly (variance matrix)...")
        pk = portfolio_kelly(tickers, lookback=dyn_lookback)
        result["portfolio"] = pk
        result["variance_matrix"] = pk.get("variance_matrix", {})

    return result


if __name__ == "__main__":
    import argparse
    from macdv_calculator import SWING_FRAMEWORK_TICKERS
    from telegram_bot import split_and_send, is_configured

    parser = argparse.ArgumentParser(description="Kelly Criterion Analyzer")
    parser.add_argument("--mode", choices=["all", "historical", "dynamic", "strategy", "portfolio"],
                        default="all", help="Which analysis to run")
    parser.add_argument("--horizon", type=int, default=5, help="D-horizon for strategy Kelly (default 5)")
    parser.add_argument("--hist-lookback", type=int, default=2000)
    parser.add_argument("--dyn-lookback",  type=int, default=252)
    parser.add_argument("--no-telegram", action="store_true", help="Print only, don't send")
    args = parser.parse_args()

    run_portfolio = args.mode in ("all", "portfolio")

    res = run_full_analysis(
        SWING_FRAMEWORK_TICKERS,
        hist_lookback=args.hist_lookback,
        dyn_lookback=args.dyn_lookback,
        strategy_horizon=args.horizon,
        portfolio=run_portfolio,
    )

    msgs = []

    if args.mode in ("all", "historical"):
        msgs.append(format_historical_kelly(res["historical"], title=f"Historical ({args.hist_lookback}-day)"))

    if args.mode in ("all", "dynamic"):
        msgs.append(format_dynamic_kelly(res["dynamic"]))
        msgs.append(format_percentile_kelly(res["dynamic"]))

    if args.mode in ("all", "strategy"):
        msgs.append(format_strategy_kelly(res["strategy"], horizon=args.horizon))

    if args.mode in ("all", "portfolio") and "variance_matrix" in res:
        msgs.append(format_variance_matrix(res["variance_matrix"]))
    if args.mode in ("all", "portfolio") and "portfolio" in res:
        msgs.append(format_portfolio_kelly(res["portfolio"]))

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
