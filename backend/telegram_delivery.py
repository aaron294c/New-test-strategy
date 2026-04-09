"""
Shared snapshot delivery logic used by both the webhook handler and the poller.

_deliver(chat_id, msg_type)  — fetches live data and sends snapshot(s).

msg_type: "all" | "macro" | "mr" | "momentum"
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow importing backend modules when called from scripts/
_here = Path(__file__).resolve().parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))


def _deliver(chat_id: str, msg_type: str = "all") -> None:
    """Fetch live data and send Telegram snapshot(s) to chat_id."""
    from macro_rsi_calculator import fetch_all_macro_data, compute_live_swing_percentiles
    from telegram_formatters import (
        _load_swing_snapshot,
        format_macro_dashboard,
        format_mean_reversion,
        format_momentum,
        format_divergence,
    )
    from telegram_bot import split_and_send

    print(f"[delivery] type={msg_type}  chat={chat_id}")

    macro_data  = fetch_all_macro_data()
    swing_data  = _load_swing_snapshot()

    # Overlay snapshot with live RSI-MA percentiles from yfinance
    if msg_type in ("all", "mr", "momentum"):
        live = compute_live_swing_percentiles(swing_data)
        for row in swing_data:
            ld = live.get(row.get("ticker", ""), {})
            if ld.get("current_percentile") is not None:
                row["current_percentile"] = ld["current_percentile"]
            if ld.get("price") is not None:
                row["current_price"]    = ld["price"]
                row["price_change_pct"] = ld.get("price_chg_pct")

    if msg_type in ("all", "macro"):
        split_and_send(format_macro_dashboard(macro_data), chat_id=chat_id)

    if msg_type in ("all", "mr"):
        split_and_send(format_mean_reversion(swing_data, macro_data), chat_id=chat_id)

    if msg_type in ("all", "momentum"):
        split_and_send(format_momentum(swing_data, macro_data), chat_id=chat_id)

    if msg_type == "divergence":
        split_and_send(format_divergence(swing_data, macro_data), chat_id=chat_id)

    print("[delivery] done.")
