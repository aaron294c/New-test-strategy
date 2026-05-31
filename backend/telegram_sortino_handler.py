"""
/sortino command — risk-adjusted rankings (EV / downside deviation) from
SIGNAL_METRICS_REFERENCE.md (DCA-cluster, D5).

Default view = COV-confirmed Signal A & B Sortino leaderboards.
Inline button toggles the no-COV variants (pct<5 and pct 5–10).
"""

from __future__ import annotations

from signal_metrics_doc import find_table, render

_SEL = ["Ticker", "EV%", "Win%", "Sortino", "Sharpe", "EV/|Loss|"]
_RENAME = {"EV/|Loss|": "EV/L"}

INTRO = (
    "<b>📐 Sortino — risk-adjusted edge</b>\n"
    "<i>Sortino = EV ÷ downside deviation (penalises only losses). "
    "Higher = more return per unit of downside. DCA-cluster, D5.</i>"
)


def sortino_menu_markup(active: str = "cov") -> dict:
    cov = ("✅ " if active == "cov" else "") + "COV-confirmed"
    nocov = ("✅ " if active == "nocov" else "") + "No-COV"
    return {
        "inline_keyboard": [[
            {"text": cov, "callback_data": "sortino:cov"},
            {"text": nocov, "callback_data": "sortino:nocov"},
        ]]
    }


def handle_sortino_cov() -> list[str]:
    a = find_table("Signal A", "risk views", deepest="Sortino-like")
    b = find_table("Signal B", "risk views", deepest="Sortino-like")
    return [
        INTRO,
        render(a, _SEL, rename=_RENAME,
               title="<b>Signal A · Sortino top 10</b> (pct&lt;5 + COV red)\n"),
        render(b, _SEL, rename=_RENAME,
               title="<b>Signal B · Sortino top 10</b> (pct 5–15 + COV red)\n",
               note="<i>Tap <b>No-COV</b> below for the variants without the COV filter.</i>"),
    ]


def handle_sortino_nocov() -> list[str]:
    a = find_table("pct < 5 (no COV)", deepest="Sortino-like")
    b = find_table("pct 5–10 (no COV)", deepest="Sortino-like")
    return [
        INTRO,
        render(a, _SEL, rename=_RENAME,
               title="<b>pct&lt;5 · Sortino top 10</b> (no COV filter)\n"),
        render(b, _SEL, rename=_RENAME,
               title="<b>pct 5–10 · Sortino top 10</b> (no COV filter)\n",
               note="<i>Tap <b>COV-confirmed</b> for the COV-red-bar versions.</i>"),
    ]
