"""
/ffd command — live FFD-normalized (0-100) readings across the swing universe.

  /ffd   →  ranked table of all 50 SWING_FRAMEWORK_TICKERS, lowest (most
            "oversold-regime") FFD readings first — i.e. closest to / below
            the 30-40 zone this project's backtests treat as the confluence
            signal. Each ticker in the empirically-validated 16-name cohort
            (see docs/SIGNAL_METRICS_REFERENCE.md, "FFD < 40 as a Confluence
            Gate") is marked with a star so the reading carries its proven
            context at a glance.

Data: live yfinance fetch via macro_rsi_calculator.compute_live_ffd_values
(3y daily history per ticker, batch-downloaded). No caching — every call is
a fresh read, since FFD is meant to describe the *current* regime.
"""

from __future__ import annotations

from datetime import datetime, timezone

from macdv_calculator import SWING_FRAMEWORK_TICKERS
from ffd_indicator import FFD_CONFLUENCE_MAX

# The 16 names where this session's cross-methodology testing (non-overlap +
# ASAP + DCA-cluster regimes) showed FFD<40 reliably raises EV / Sortino on
# top of Signal A. GOOGL and XLI were in the original 18-name candidate list
# but were dropped after their Sortino *worsened* under FFD<40 — flagging them
# as noise rather than genuine beneficiaries. Keep this list in sync with the
# "FFD < 40 as a Confluence Gate" section of docs/SIGNAL_METRICS_REFERENCE.md.
PROVEN_COHORT = {
    "TSLA", "AAPL", "WMT", "ORCL", "NQ=F", "UNH", "LLY", "BRK-B",
    "PG", "V", "MSFT", "ES=F", "OXY", "JNJ", "AVGO", "^VIX",
}

_STAR = "⭐"


def _now_uk() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def handle_ffd_command(arg: str = "") -> list[str]:
    from macro_rsi_calculator import compute_live_ffd_values

    tickers = list(SWING_FRAMEWORK_TICKERS)
    live = compute_live_ffd_values(tickers)

    rows: list[tuple[str, float, float]] = []
    failed: list[str] = []
    for ticker in tickers:
        rec = live.get(ticker) or {}
        ffd, price = rec.get("ffd"), rec.get("price")
        if ffd is None or price is None:
            failed.append(ticker)
            continue
        rows.append((ticker, ffd, price))

    # Lowest FFD first — closest to / below the 30-40 confluence zone surfaces first.
    rows.sort(key=lambda r: r[1])

    lines: list[str] = []
    lines.append("<b>\U0001f4c9 FFD — LIVE FRACTIONAL-DIFF READINGS (0-100)</b>")
    lines.append(f"<i>{_now_uk()}</i>")
    lines.append(f"<i>Ranked lowest → highest · &lt;{FFD_CONFLUENCE_MAX:.0f} = the project's "
                 f"validated confluence zone</i>")
    lines.append("")

    if not rows:
        lines.append("<i>No data available — live fetch failed for all tickers.</i>")
        return ["\n".join(lines)]

    below = sum(1 for r in rows if r[1] < FFD_CONFLUENCE_MAX)
    lines.append(f"<b>{below} below {FFD_CONFLUENCE_MAX:.0f} · {len(rows) - below} above</b>")
    lines.append("<pre>")
    lines.append(f"{'Ticker':<8} {'FFD':>6} {'Price':>10}")
    lines.append("─" * 28)
    for ticker, ffd, price in rows:
        price_s = f"{price:,.2f}" if price < 10_000 else f"{price:,.0f}"
        flag = " ⬇" if ffd < FFD_CONFLUENCE_MAX else ""
        star = f" {_STAR}" if ticker in PROVEN_COHORT else ""
        lines.append(f"{ticker:<8} {ffd:>6.1f} {price_s:>10}{flag}{star}")
    lines.append("</pre>")
    lines.append("")
    lines.append(f"<i>⬇ below {FFD_CONFLUENCE_MAX:.0f} (confluence zone)</i>")
    lines.append(
        f"<i>{_STAR} = one of the <b>16 names</b> where FFD&lt;{FFD_CONFLUENCE_MAX:.0f} is "
        f"empirically shown — across 3 independent trade-counting regimes "
        f"(non-overlap, overlapping/ASAP, DCA-cluster) — to raise EV / Sortino "
        f"on top of Signal A. See docs/SIGNAL_METRICS_REFERENCE.md, "
        f"“FFD &lt; 40 as a Confluence Gate.” This mark appears "
        f"<b>only</b> on those 16 — for every other ticker, a low FFD reading "
        f"has <b>not</b> been validated as edge-additive (it may be neutral "
        f"or noise).</i>"
    )
    if failed:
        lines.append("")
        lines.append(f"<i>No live data for: {', '.join(failed)}</i>")

    return ["\n".join(lines)]
