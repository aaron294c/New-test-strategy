"""
/mr command — mean-reversion views with an inline-button chooser.

Three views:
  • Live oversold table       (existing snapshot path — handled in the poller via _deliver "mr")
  • Non-overlapping backtest  (Signal A & B — first-entry-only, from SIGNAL_METRICS_REFERENCE.md)
  • Overlapping (DCA-cluster) (scale-in across the oversold streak — same doc)

The menu uses Telegram inline keyboard buttons; taps come back as callback_query
and are routed by scripts/telegram_poll.py.
"""

from __future__ import annotations

from signal_metrics_doc import find_table, render

MENU_TEXT = (
    "<b>📉 Mean Reversion — choose a view</b>\n\n"
    "• <b>Live</b> — current oversold table (RSI-MA ≤35th %ile, live data)\n"
    "• <b>Non-overlapping</b> — backtest EV/Win/Kelly, first-entry-only (5yr vs 9yr)\n"
    "• <b>Overlapping</b> — DCA-cluster: scale-in across the whole oversold streak (D5)\n\n"
    "<i>Tap a button below.</i>"
)


def mr_menu_markup() -> dict:
    """Inline keyboard for the /mr chooser."""
    return {
        "inline_keyboard": [
            [
                {"text": "📊 Live oversold", "callback_data": "mr:live"},
            ],
            [
                {"text": "🔹 Non-overlapping", "callback_data": "mr:nonoverlap"},
                {"text": "🔸 Overlapping", "callback_data": "mr:overlap"},
            ],
        ]
    }


# ── Non-overlapping (Signal A & B) ────────────────────────────────────────────
def handle_mr_nonoverlap() -> list[str]:
    sel = ["Ticker", "9yr Win%", "9yr EV", "9yr ½-Kelly", "5yr ½-Kelly"]
    rename = {"9yr Win%": "Win%", "9yr EV": "EV", "9yr ½-Kelly": "9y½K", "5yr ½-Kelly": "5y½K"}
    a = find_table(deepest="Signal A — RSI-MA < 5th Percentile + COV Red Bar")
    b = find_table(deepest="Signal B — RSI-MA 5th–15th Percentile + COV Red Bar")
    return [
        render(a, sel, rename=rename,
               title="<b>🔹 Non-overlapping · Signal A</b> (pct&lt;5 + COV red, D5)\n",
               note="<i>½K = half-Kelly. 9yr window = full cycle; 5yr = recent regime.</i>"),
        render(b, sel, rename=rename,
               title="<b>🔹 Non-overlapping · Signal B</b> (pct 5–15 + COV red, D5)\n",
               note="<i>First-entry-only. Use /sizing a · /sizing b for the full 5yr/9yr detail.</i>"),
    ]


# ── Overlapping (DCA-cluster) ─────────────────────────────────────────────────
def handle_mr_overlap() -> list[str]:
    sel = ["Ticker", "N", "EV", "Win%", "Avg Loss", "Median"]
    a = find_table("Signal A", "DCA-blended", deepest="Full universe")
    b = find_table("Signal B", "DCA-blended", deepest="Full universe")
    return [
        render(a, sel,
               title="<b>🔸 Overlapping (DCA-cluster) · Signal A</b> (pct&lt;5 + COV red, D5)\n",
               note="<i>One blended entry per oversold cluster. N = clusters. Sorted by EV.</i>"),
        render(b, sel,
               title="<b>🔸 Overlapping (DCA-cluster) · Signal B</b> (pct 5–15 + COV red, D5)\n",
               note="<i>Scale-in across the streak. See /sortino for risk-adjusted ranks.</i>"),
    ]
