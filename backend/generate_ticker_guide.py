#!/usr/bin/env python3
"""
Generate per-ticker position sizing guide from cached backtest results.
Ordered by user-defined priority (primary → secondary → rest).
Output: docs/TICKER_POSITION_GUIDE.md
"""

from __future__ import annotations
import json
from pathlib import Path

_here = Path(__file__).resolve().parent
CACHE = _here / "cache" / "position_sizing_results.json"
OUT = _here.parent / "docs" / "TICKER_POSITION_GUIDE.md"

GUARDRAIL_MIN = 5.0
GUARDRAIL_MAX = 20.0

# User's trading tiers
PRIMARY = [
    ("NQ=F",    "NASDAQ Futures"),
    ("ES=F",    "S&P 500 Futures"),
    ("QQQ",     "NASDAQ ETF"),
    ("SPY",     "S&P 500 ETF"),
    ("GOOGL",   "Alphabet / Google"),
    ("NVDA",    "NVIDIA"),
    ("AVGO",    "Broadcom"),
    ("SLV",     "Silver ETF"),
    ("GLD",     "Gold ETF"),
    ("AAPL",    "Apple"),
    ("MSFT",    "Microsoft"),
    ("TSM",     "Taiwan Semiconductor"),
]

SECONDARY = [
    ("META",    "Meta / Facebook"),
    ("TSLA",    "Tesla"),
    ("BAC",     "Bank of America"),
    ("CVX",     "Chevron"),
    ("NFLX",    "Netflix"),
    ("OXY",     "Occidental Petroleum"),
    ("^FTSE",   "FTSE 100"),
    ("XOM",     "Exxon Mobil"),
    ("BTC-USD", "Bitcoin"),
]

REST = [
    ("BRK-B",    "Berkshire Hathaway"),
    ("WMT",      "Walmart"),
    ("UNH",      "UnitedHealth"),
    ("LLY",      "Eli Lilly"),
    ("ORCL",     "Oracle"),
    ("JPM",      "JP Morgan"),
    ("^VIX",     "VIX"),
    ("DX-Y.NYB", "US Dollar Index"),
    ("^TNX",     "10-Year Yield"),
    ("XLI",      "Industrials ETF"),
    ("MCD",      "McDonald's"),
    ("SMH",      "Semiconductors ETF"),
    ("ASML",     "ASML"),
    ("SMCI",     "Super Micro Computer"),
    ("^GDAXI",   "DAX"),
    ("^N225",    "Nikkei 225"),
    ("AMZN",     "Amazon"),
]


def rec(m: dict) -> tuple[float, str]:
    """Return (recommended_pct, rationale_string)."""
    if not m or m.get("n", 0) < 8:
        return GUARDRAIL_MIN, "insufficient data"
    ev = m.get("ev_pct", 0) or 0
    k = m.get("kelly_binary")
    if k is None or k <= 0 or ev <= 0:
        return GUARDRAIL_MIN, "no edge (Kelly ≤ 0)"
    half_k = k / 2.0
    clamped = max(GUARDRAIL_MIN, min(GUARDRAIL_MAX, half_k))
    note = "capped" if half_k > GUARDRAIL_MAX else ("floored" if half_k < GUARDRAIL_MIN else "")
    return clamped, note


def stars(m: dict) -> str:
    if not m or m.get("n", 0) < 8:
        return "✗ NO DATA"
    k = m.get("kelly_binary", 0) or 0
    ev = m.get("ev_pct", 0) or 0
    win = m.get("win_rate", 0) or 0
    if ev <= 0 or k <= 0:
        return "✗ SKIP"
    if k >= 30 and win >= 60:
        return "⭐⭐⭐ STRONG"
    if k >= 15 and win >= 52 and ev > 0:
        return "⭐⭐ GOOD"
    return "⭐ MARGINAL"


def signal_block(label: str, m: dict, prefix: str = "") -> list[str]:
    """Return formatted lines for one signal bucket."""
    lines = []
    rating = stars(m)
    lines.append(f"{prefix}**{label}** — {rating}")
    if not m or m.get("n", 0) < 8:
        lines.append(f"{prefix}  *Too few qualifying trades*")
        return lines
    k = m.get("kelly_binary")
    rec_pct, note = rec(m)
    ev = m["ev_pct"]
    win = m["win_rate"]
    loss = m["loss_rate"]
    aw = m["avg_win_pct"]
    al = m["avg_loss_pct"]
    rr = m.get("reward_risk_ratio", 0) or 0
    n = m["n"]
    lines.append(f"{prefix}  n={n} · win={win}% · loss={loss}%")
    lines.append(f"{prefix}  Avg win: **+{aw}%** | Avg loss: **{al}%** | RR: {rr:.2f}x")
    lines.append(f"{prefix}  Expected value: **{ev:+.3f}% per trade**")
    if k is not None and k > 0:
        half_k = k / 2.0
        note_str = f" ({note})" if note else ""
        lines.append(f"{prefix}  Kelly: {k:.1f}% → Half-Kelly: {half_k:.1f}%{note_str} → **Rec: {rec_pct:.0f}%**")
    else:
        k_str = f"{k:.1f}%" if k is not None else "n/a"
        lines.append(f"{prefix}  Kelly: {k_str} → **Rec: {rec_pct:.0f}% (floor)**")
    return lines


def ticker_section(ticker: str, name: str, data: dict) -> list[str]:
    lines = []
    lines.append(f"### {ticker} — {name}")
    lines.append("")

    a_data = data.get("ultra_low", {}).get("cov_confluence", {})
    b_data = data.get("low", {}).get("cov_confluence", {})

    rec_a, _ = rec(a_data)
    rec_b, _ = rec(b_data)

    # One-line summary
    a_stars = stars(a_data)
    b_stars = stars(b_data)
    lines.append(f"| | Signal A (<5th + COV) | Signal B (5–15th + COV) |")
    lines.append(f"|---|---|---|")
    lines.append(f"| Rating | {a_stars} | {b_stars} |")
    lines.append(f"| Win rate | {a_data.get('win_rate', '—')}% | {b_data.get('win_rate', '—')}% |")
    lines.append(f"| Avg win | +{a_data.get('avg_win_pct', '—')}% | +{b_data.get('avg_win_pct', '—')}% |")
    lines.append(f"| Avg loss | {a_data.get('avg_loss_pct', '—')}% | {b_data.get('avg_loss_pct', '—')}% |")
    lines.append(f"| EV per trade | {(a_data.get('ev_pct') or 0):+.3f}% | {(b_data.get('ev_pct') or 0):+.3f}% |")
    lines.append(f"| Kelly | {a_data.get('kelly_binary', '—')}% | {b_data.get('kelly_binary', '—')}% |")
    lines.append(f"| **Recommended size** | **{rec_a:.0f}%** | **{rec_b:.0f}%** |")
    lines.append("")

    # Key note if anything important to flag
    notes = []
    if rec_a == GUARDRAIL_MIN and stars(a_data) == "✗ SKIP":
        notes.append("Signal A has negative edge — use **floor sizing only**, don't size up.")
    if rec_b == GUARDRAIL_MIN and stars(b_data) == "✗ SKIP" and stars(a_data) != "✗ SKIP":
        notes.append("Signal B has negative edge — only trade Signal A entries for this name.")
    if stars(a_data) == "⭐⭐⭐ STRONG":
        notes.append("Signal A is **high conviction** — this is a core entry vehicle at this extreme.")
    if stars(b_data) == "⭐⭐⭐ STRONG":
        notes.append("Signal B also shows strong edge — the 5–15th bucket is tradeable for this name.")
    for note in notes:
        lines.append(f"> {note}")
    if notes:
        lines.append("")

    return lines


def build_md(results: dict) -> str:
    lines: list[str] = []
    a = lines.append

    a("# Per-Ticker Position Sizing Guide")
    a("")
    a("*All figures from backtested D5 returns, non-overlapping entries, RSI-MA + COV red confluence.*")
    a("*Half-Kelly sizing clamped to 5–20% guardrail. Max 3 simultaneous positions.*")
    a("")
    a("## Quick Legend")
    a("")
    a("| Rating | Meaning | Typical Recommended Size |")
    a("|--------|---------|--------------------------|")
    a("| ⭐⭐⭐ STRONG | Kelly ≥ 30%, win ≥ 60% | 15–20% |")
    a("| ⭐⭐ GOOD | Kelly ≥ 15%, win ≥ 52%, EV > 0 | 7–14% |")
    a("| ⭐ MARGINAL | Kelly > 0, EV > 0 | 5–7% |")
    a("| ✗ SKIP | Kelly ≤ 0 or EV ≤ 0 | 5% floor only |")
    a("")
    a("> **How to size with multiple signals open:** If Signal A on NQ=F fires (20%) and Signal B on MSFT fires (14%),")
    a("> that's 34% combined — within the 60% max (3 × 20%). Both are fine to run simultaneously.")
    a("")
    a("---")
    a("")

    # Primary
    a("## Tier 1 — Primary Trading Vehicles")
    a("*These are the names you are most likely to trade.*")
    a("")
    for ticker, name in PRIMARY:
        if ticker not in results:
            a(f"### {ticker} — {name}")
            a("*No data available.*")
            a("")
            continue
        lines.extend(ticker_section(ticker, name, results[ticker]))
        a("---")
        a("")

    # Secondary
    a("## Tier 2 — Secondary Trading Vehicles")
    a("*Less frequent. Trade only on high-conviction setups.*")
    a("")
    for ticker, name in SECONDARY:
        if ticker not in results:
            a(f"### {ticker} — {name}")
            a("*No data available.*")
            a("")
            continue
        lines.extend(ticker_section(ticker, name, results[ticker]))
        a("---")
        a("")

    # Rest
    a("## Tier 3 — Full Universe (Remaining Tickers)")
    a("")
    for ticker, name in REST:
        if ticker not in results:
            a(f"### {ticker} — {name}")
            a("*No data available.*")
            a("")
            continue
        lines.extend(ticker_section(ticker, name, results[ticker]))
        a("---")
        a("")

    # Summary table
    a("## Summary Table — All Tickers")
    a("")
    a("| Ticker | Name | A Rating | A Rec% | B Rating | B Rec% |")
    a("|--------|------|----------|--------|----------|--------|")

    all_tickers = PRIMARY + SECONDARY + REST
    for ticker, name in all_tickers:
        if ticker not in results:
            a(f"| {ticker} | {name} | — | — | — | — |")
            continue
        d = results[ticker]
        a_m = d.get("ultra_low", {}).get("cov_confluence", {})
        b_m = d.get("low", {}).get("cov_confluence", {})
        a_rec, _ = rec(a_m)
        b_rec, _ = rec(b_m)
        a(f"| **{ticker}** | {name} | {stars(a_m)} | **{a_rec:.0f}%** | {stars(b_m)} | **{b_rec:.0f}%** |")

    a("")
    a("---")
    a("")
    a("## Important Observations")
    a("")
    a("### Surprises from the data")
    a("")
    a("**Gold (GLD) and Silver (SLV) — Signal A doesn't work:**")
    a("Both metals have *negative* Kelly in the ultra-low bucket with COV red. This seems counterintuitive")
    a("but reflects that when precious metals are extremely oversold and showing bearish momentum,")
    a("a 5-day mean reversion doesn't reliably follow. GLD Signal B (5–15th pct) does work — 11% rec.")
    a("SLV has no edge in either bucket at D5.")
    a("")
    a("**TSLA Signal A is outstanding (20% cap):**")
    a("71.4% win rate, +4.31% EV, Kelly=58.1%. When TSLA is at its most oversold *and* COV fires red,")
    a("it mean-reverts powerfully within 5 days. This is your highest-edge single-name entry.")
    a("")
    a("**META works in *both* signal buckets:**")
    a("Signal A: 17% rec. Signal B: 16% rec (2.32x reward:risk ratio). META has unusually asymmetric")
    a("wins vs losses in the 5–15th percentile zone.")
    a("")
    a("**NFLX — skip Signal A, good Signal B:**")
    a("Signal A has negative edge. Signal B (5–15th pct) has 60% win, +1.01% EV → 12% rec.")
    a("The mid-range oversold entry is where Netflix mean-reverts, not the extreme level.")
    a("")
    a("**NQ=F and MSFT are your two most reliable Signal A names:**")
    a("Both cap at 20% with Kelly >48%. When NASDAQ futures or MSFT hit ultra-low *and* COV fires,")
    a("the historical edge is near-maximum. These are your highest conviction entries.")

    return "\n".join(lines)


def main() -> None:
    with open(CACHE) as f:
        results = json.load(f)

    md = build_md(results)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(md)
    print(f"Written → {OUT}")


if __name__ == "__main__":
    main()
