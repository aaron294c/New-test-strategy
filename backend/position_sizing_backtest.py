#!/usr/bin/env python3
"""
Position Sizing Backtest — RSI-MA + COV Confluence

Two entry conditions evaluated across the full swing universe (D5 horizon):
  A. "Ultra-low" — RSI-MA percentile < 5   AND COV red bar (Fisher ≤ −1.3)
  B. "Low"       — RSI-MA percentile 5–15  AND COV red bar (Fisher ≤ −1.3)

Computes win rate, avg win, avg loss, expectancy, binary Kelly, and position size.
Uses non-overlapping entries (2×horizon cooldown between signals) to avoid bias.

Outputs:
  backend/cache/position_sizing_results.json
  docs/POSITION_SIZING_GUIDE.md
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

_here = Path(__file__).resolve().parent
sys.path.insert(0, str(_here))

from cov_indicator import compute_cov, red_bar_mask  # noqa: E402
from macro_instruments import calculate_rsi_ma  # noqa: E402
from macdv_calculator import SWING_FRAMEWORK_TICKERS  # noqa: E402

UNIVERSE = list(SWING_FRAMEWORK_TICKERS)
HORIZON = 5
RSI_MA_LOOKBACK = 252
DOWNLOAD_DAYS = 2500
MIN_TRADES = 8

BUCKETS = [
    (0.0, 5.0, "ultra_low", "A — Ultra-Low (<5th pct)"),
    (5.0, 15.0, "low", "B — Low (5–15th pct)"),
]

GUARDRAIL_MIN = 5.0
GUARDRAIL_MAX = 20.0
MAX_POSITIONS = 3


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def download_all(tickers: list[str]) -> dict[str, pd.Series]:
    raw = yf.download(
        tickers,
        period=f"{DOWNLOAD_DAYS + 100}d",
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
                if len(s) >= RSI_MA_LOOKBACK + HORIZON + 20:
                    result[t] = s
    else:
        if "Close" in raw.columns:
            s = raw["Close"].dropna()
            if len(s) >= RSI_MA_LOOKBACK + HORIZON + 20:
                result[tickers[0]] = s
    return result


def rolling_percentile(close: pd.Series) -> pd.Series:
    rsi_ma = calculate_rsi_ma(close)
    return rsi_ma.rolling(
        window=RSI_MA_LOOKBACK, min_periods=RSI_MA_LOOKBACK
    ).apply(
        lambda w: float((w[:-1] < w[-1]).sum() / (len(w) - 1) * 100),
        raw=True,
    )


# ---------------------------------------------------------------------------
# Entry / trade extraction
# ---------------------------------------------------------------------------

def find_entries(
    pct: pd.Series,
    close: pd.Series,
    lo: float,
    hi: float,
    confluence_mask: Optional[pd.Series] = None,
) -> list[float]:
    """
    Non-overlapping D{HORIZON} simple returns (%) for entries where lo <= pct < hi.
    Cooldown: 2×HORIZON bars between entries to avoid overlapping trades.
    """
    aligned = pd.DataFrame({"pct": pct, "close": close}).dropna()
    cm = confluence_mask.reindex(aligned.index, fill_value=False) if confluence_mask is not None else None

    returns: list[float] = []
    last_i = -999

    for i, (date, row) in enumerate(aligned.iterrows()):
        p = row["pct"]
        if pd.isna(p) or not (lo <= p < hi):
            continue
        if i - last_i < 2 * HORIZON:
            continue
        if cm is not None and not bool(cm.loc[date]):
            continue
        if i + HORIZON >= len(aligned):
            break
        entry = aligned["close"].iloc[i]
        exit_ = aligned["close"].iloc[i + HORIZON]
        if entry > 0 and exit_ > 0:
            returns.append((exit_ / entry - 1.0) * 100.0)
        last_i = i

    return returns


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_metrics(returns: list[float]) -> dict:
    if not returns:
        return {"n": 0}
    arr = np.array(returns)
    wins = arr[arr > 0]
    losses = arr[arr <= 0]

    n = len(arr)
    win_rate = len(wins) / n
    loss_rate = 1.0 - win_rate
    avg_win = float(wins.mean()) if len(wins) else 0.0
    avg_loss = float(losses.mean()) if len(losses) else 0.0
    ev = win_rate * avg_win + loss_rate * avg_loss

    # Binary Kelly: f* = (p*b - q) / b,  b = avg_win / |avg_loss|
    if avg_win > 0 and avg_loss < 0:
        b = avg_win / abs(avg_loss)
        kelly_binary = (win_rate * b - loss_rate) / b * 100.0
    else:
        kelly_binary = None

    return {
        "n": n,
        "win_rate": round(win_rate * 100.0, 1),
        "loss_rate": round(loss_rate * 100.0, 1),
        "avg_win_pct": round(avg_win, 2),
        "avg_loss_pct": round(avg_loss, 2),
        "ev_pct": round(ev, 3),
        "kelly_binary": round(kelly_binary, 1) if kelly_binary is not None else None,
        "reward_risk_ratio": round(avg_win / abs(avg_loss), 2) if avg_loss < 0 else None,
    }


def recommend_size(m: dict) -> dict:
    if m.get("n", 0) < MIN_TRADES or m.get("ev_pct", 0) <= 0:
        return {"recommended_pct": GUARDRAIL_MIN, "rationale": "insufficient edge"}
    k = m.get("kelly_binary")
    if k is None or k <= 0:
        return {"recommended_pct": GUARDRAIL_MIN, "rationale": "Kelly non-positive"}
    half_k = k / 2.0
    clamped = max(GUARDRAIL_MIN, min(GUARDRAIL_MAX, half_k))
    return {
        "full_kelly_pct": round(k, 1),
        "half_kelly_pct": round(half_k, 1),
        "recommended_pct": round(clamped, 1),
        "rationale": "half-Kelly clamped to 5–20%",
    }


# ---------------------------------------------------------------------------
# Main analysis loop
# ---------------------------------------------------------------------------

def run_analysis() -> dict:
    print(f"Downloading {len(UNIVERSE)} tickers…")
    price_data = download_all(UNIVERSE)
    print(f"  Got data for {len(price_data)} tickers\n")

    results: dict[str, dict] = {}

    for ticker, close in price_data.items():
        print(f"  {ticker} ({len(close)} bars)…")
        try:
            pct = rolling_percentile(close)
            cov_df = compute_cov(close)
            red = red_bar_mask(cov_df).reindex(pct.index, fill_value=False)

            ticker_result: dict[str, dict] = {}
            for lo, hi, name, _ in BUCKETS:
                rets_uncond = find_entries(pct, close, lo, hi)
                rets_cov = find_entries(pct, close, lo, hi, confluence_mask=red)
                ticker_result[name] = {
                    "rsi_only": compute_metrics(rets_uncond),
                    "cov_confluence": compute_metrics(rets_cov),
                }
                print(
                    f"    {name}: rsi_only={len(rets_uncond)}  "
                    f"cov_red={len(rets_cov)}"
                )
            results[ticker] = ticker_result
        except Exception as exc:
            print(f"    ERROR: {exc}")

    return results


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def aggregate(results: dict, bucket: str, signal: str) -> dict:
    """Median of each metric across tickers that have ≥ MIN_TRADES."""
    rows = [
        results[t][bucket][signal]
        for t in results
        if bucket in results[t]
        and signal in results[t][bucket]
        and results[t][bucket][signal].get("n", 0) >= MIN_TRADES
    ]
    if not rows:
        return {"n_tickers": 0}

    def med(key: str):
        vals = [r[key] for r in rows if r.get(key) is not None]
        return round(float(np.median(vals)), 2) if vals else None

    return {
        "n_tickers": len(rows),
        "median_n_trades": med("n"),
        "median_win_rate": med("win_rate"),
        "median_loss_rate": med("loss_rate"),
        "median_avg_win": med("avg_win_pct"),
        "median_avg_loss": med("avg_loss_pct"),
        "median_ev": med("ev_pct"),
        "median_kelly_binary": med("kelly_binary"),
        "median_rr_ratio": med("reward_risk_ratio"),
    }


# ---------------------------------------------------------------------------
# MD generation
# ---------------------------------------------------------------------------

def _fmt(v, spec="{:.2f}", suffix=""):
    if v is None:
        return "—"
    return spec.format(v) + suffix


def build_md(results: dict) -> str:
    lines: list[str] = []
    a = lines.append

    a("# Position Sizing Guide — RSI-MA + COV Confluence Strategy")
    a("")
    a(f"*Generated: {pd.Timestamp.now().strftime('%Y-%m-%d')} · Universe: {len(results)} tickers · D5 holding period*")
    a("")
    a("## Signal Definitions")
    a("")
    a("| Label | RSI-MA Percentile Condition | COV Condition | Strength |")
    a("|-------|-----------------------------|---------------|----------|")
    a("| **A — Ultra-Low** | < 5th percentile | Red bar (Fisher dir_metric ≤ −1.3) | Strongest |")
    a("| **B — Low** | 5th–15th percentile | Red bar (Fisher dir_metric ≤ −1.3) | Strong |")
    a("")
    a("Both conditions fire **unconditionally** — no additional filters required.")
    a("COV red bar = coefficient-of-variation indicator with Fisher-z correlation ≤ −1.3,")
    a("indicating negative momentum confirmation with statistical significance.")
    a("")

    for lo, hi, bucket_name, label in BUCKETS:
        uncond = aggregate(results, bucket_name, "rsi_only")
        cov = aggregate(results, bucket_name, "cov_confluence")

        a(f"---")
        a(f"")
        a(f"## Signal {label}")
        a("")

        if cov.get("n_tickers", 0) == 0:
            a("*Insufficient data across universe.*")
            a("")
            continue

        a(f"### Aggregate Statistics")
        a(f"*Median across {cov['n_tickers']} tickers with ≥ {MIN_TRADES} qualifying trades*")
        a("")
        a("| Metric | RSI-MA Only | RSI-MA + COV Red | Improvement |")
        a("|--------|-------------|-----------------|-------------|")

        def delta(cov_val, uncond_val):
            if cov_val is None or uncond_val is None:
                return "—"
            d = cov_val - uncond_val
            return f"+{d:.1f}" if d >= 0 else f"{d:.1f}"

        a(f"| Sample trades (median) | {_fmt(uncond.get('median_n_trades'), '{:.0f}')} | {_fmt(cov.get('median_n_trades'), '{:.0f}')} | — |")
        a(f"| Win rate | {_fmt(uncond.get('median_win_rate'), '{:.1f}', '%')} | **{_fmt(cov.get('median_win_rate'), '{:.1f}', '%')}** | {delta(cov.get('median_win_rate'), uncond.get('median_win_rate'))}pp |")
        a(f"| Loss rate | {_fmt(uncond.get('median_loss_rate'), '{:.1f}', '%')} | {_fmt(cov.get('median_loss_rate'), '{:.1f}', '%')} | — |")
        a(f"| Avg win (D5) | +{_fmt(uncond.get('median_avg_win'), '{:.2f}', '%')} | **+{_fmt(cov.get('median_avg_win'), '{:.2f}', '%')}** | {delta(cov.get('median_avg_win'), uncond.get('median_avg_win'))}pp |")
        a(f"| Avg loss (D5) | {_fmt(uncond.get('median_avg_loss'), '{:.2f}', '%')} | **{_fmt(cov.get('median_avg_loss'), '{:.2f}', '%')}** | {delta(cov.get('median_avg_loss'), uncond.get('median_avg_loss'))}pp |")
        a(f"| Reward:Risk ratio | {_fmt(uncond.get('median_rr_ratio'), '{:.2f}', 'x')} | **{_fmt(cov.get('median_rr_ratio'), '{:.2f}', 'x')}** | — |")
        a(f"| Expected value D5 | {_fmt(uncond.get('median_ev'), '{:+.3f}', '%')} | **{_fmt(cov.get('median_ev'), '{:+.3f}', '%')}** | {delta(cov.get('median_ev'), uncond.get('median_ev'))}pp |")
        a(f"| Binary Kelly (full) | — | **{_fmt(cov.get('median_kelly_binary'), '{:.1f}', '%')}** | — |")
        a("")

        # Position sizing recommendation
        k = cov.get("median_kelly_binary")
        ev = cov.get("median_ev", 0) or 0
        win_rate = cov.get("median_win_rate", 0) or 0

        a("### Position Sizing Recommendation")
        a("")
        if k is not None and k > 0 and ev > 0:
            half_k = k / 2.0
            clamped = max(GUARDRAIL_MIN, min(GUARDRAIL_MAX, half_k))
            total_max_exposure = clamped * MAX_POSITIONS

            a(f"| Sizing Step | Value | Notes |")
            a(f"|-------------|-------|-------|")
            a(f"| Full Kelly | {k:.1f}% | Theoretical optimal — too aggressive |")
            a(f"| **Half-Kelly** | **{half_k:.1f}%** | Standard practical recommendation |")
            a(f"| **Guardrail-capped** | **{clamped:.1f}%** | Half-Kelly clamped to [5%, 20%] |")
            a(f"| Max simultaneous trades | {MAX_POSITIONS} | Per operational experience |")
            a(f"| Max total exposure | {total_max_exposure:.0f}% | {clamped:.0f}% × {MAX_POSITIONS} positions |")
            a("")
            if clamped < half_k:
                a(f"> **Note:** Half-Kelly ({half_k:.1f}%) exceeds the 20% guardrail cap. Recommended size is capped at **{clamped:.1f}%**.")
            elif clamped > half_k:
                a(f"> **Note:** Half-Kelly ({half_k:.1f}%) is below the 5% floor. Minimum position of **{clamped:.1f}%** applied.")
            else:
                a(f"> Half-Kelly falls within guardrails — no adjustment needed.")
            a("")
        else:
            a(f"> Insufficient edge (Kelly ≤ 0 or EV ≤ 0) — use minimum position size of {GUARDRAIL_MIN:.0f}%.")
            a("")

    # Per-ticker tables
    a("---")
    a("")
    a("## Per-Ticker Detail")
    a("")

    for _, _, bucket_name, label in BUCKETS:
        a(f"### {label} — RSI-MA + COV Red (D5)")
        a("")
        a("| Ticker | N | Win% | Avg Win | Avg Loss | EV | RR | Kelly | **Rec%** |")
        a("|--------|---|------|---------|----------|----|----|---------|----|")

        rows_for_sort = []
        for ticker in sorted(results.keys()):
            m = results[ticker].get(bucket_name, {}).get("cov_confluence", {})
            if m.get("n", 0) < MIN_TRADES:
                continue
            sz = recommend_size(m)
            rows_for_sort.append((ticker, m, sz))

        # Sort by recommended size descending
        rows_for_sort.sort(key=lambda x: x[2]["recommended_pct"], reverse=True)

        for ticker, m, sz in rows_for_sort:
            k_str = f"{m['kelly_binary']:.1f}%" if m.get("kelly_binary") is not None else "—"
            a(
                f"| {ticker} | {m['n']} | {m['win_rate']}% "
                f"| +{m['avg_win_pct']:.2f}% "
                f"| {m['avg_loss_pct']:.2f}% "
                f"| {m['ev_pct']:+.3f}% "
                f"| {m.get('reward_risk_ratio') or 0:.2f}x "
                f"| {k_str} "
                f"| **{sz['recommended_pct']:.0f}%** |"
            )
        a("")

    # Risk rules
    a("---")
    a("")
    a("## Risk Guardrails")
    a("")
    a("| Rule | Value | Why |")
    a("|------|-------|-----|")
    a(f"| Min position size | {GUARDRAIL_MIN:.0f}% | Below this, fees erode edge |")
    a(f"| Max position size | {GUARDRAIL_MAX:.0f}% | Concentration risk limit |")
    a(f"| Max simultaneous positions | {MAX_POSITIONS} | Operational & correlation limit |")
    a(f"| Use half-Kelly, not full Kelly | ½ × f* | Full Kelly maximises geometric growth but is volatile; half-Kelly reduces drawdown by ~75% |")
    a(f"| Signal required for sizing up | Both RSI-MA pct AND COV red | Unsupported signals → floor sizing |")
    a("")

    # Kelly explanation
    a("---")
    a("")
    a("## Methodology")
    a("")
    a("### Kelly Criterion (Binary Form)")
    a("")
    a("```")
    a("f* = (p × b − q) / b")
    a("")
    a("where:")
    a("  p = win probability  (fraction of D5 closes above entry)")
    a("  q = 1 − p           (loss probability)")
    a("  b = avg_win / |avg_loss|  (reward-to-risk ratio)")
    a("```")
    a("")
    a("### Non-Overlapping Entry Logic")
    a("")
    a("To prevent inflated statistics from correlated trades,")
    a(f"entries are blocked for {2*HORIZON} bars ({2*HORIZON} trading days) after each signal.")
    a("This mirrors real-world constraints where you can't enter the same position twice.")
    a("")
    a("### Expectancy Formula")
    a("")
    a("```")
    a("EV = win_rate × avg_win + loss_rate × avg_loss")
    a("")
    a("Positive EV = mathematical edge on each trade.")
    a("```")
    a("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    results = run_analysis()

    cache_path = _here / "cache" / "position_sizing_results.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nSaved raw results → {cache_path}")

    md = build_md(results)
    docs_dir = _here.parent / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    md_path = docs_dir / "POSITION_SIZING_GUIDE.md"
    md_path.write_text(md)
    print(f"Generated guide   → {md_path}")


if __name__ == "__main__":
    main()
