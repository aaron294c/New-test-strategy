"""
Shared snapshot delivery logic used by both the webhook handler and the poller.

_deliver(chat_id, msg_type)  — fetches live data and sends snapshot(s).

msg_type: "all" | "macro" | "mr" | "momentum" | "divergence" | "cov"
          | "covgreen" | "sma200" | "riskdistances"
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
        _enrich_second_order,
        format_macro_dashboard,
        format_mean_reversion,
        format_momentum,
        format_divergence,
        format_cov_snapshot,
        format_cov_green_snapshot,
        format_sma200_snapshot,
        format_risk_distances,
    )
    from telegram_bot import split_and_send

    print(f"[delivery] type={msg_type}  chat={chat_id}")

    # Only fetch macro data when it's actually needed
    needs_macro = msg_type in ("all", "macro", "mr", "momentum")
    macro_data = fetch_all_macro_data() if needs_macro else {}

    swing_data = _load_swing_snapshot()

    # Overlay snapshot with live RSI-MA percentiles from yfinance
    needs_live = msg_type in ("all", "mr", "momentum", "divergence", "cov", "covgreen")
    if needs_live and swing_data:
        live = compute_live_swing_percentiles(swing_data)
        for row in swing_data:
            ld = live.get(row.get("ticker", ""), {})
            if ld.get("current_percentile") is not None:
                row["current_percentile"] = ld["current_percentile"]
            if ld.get("price") is not None:
                row["current_price"]    = ld["price"]
                row["price_change_pct"] = ld.get("price_chg_pct")
            if ld.get("rsi_ma") is not None:
                row["rsi_ma"] = ld["rsi_ma"]
            if ld.get("cov_dir_metric") is not None:
                row["cov_dir_metric"] = ld["cov_dir_metric"]
            if ld.get("cov_bar_color") is not None:
                row["cov_bar_color"] = ld["cov_bar_color"]
        # Re-enrich second-order after live percentile update
        _enrich_second_order(swing_data)

    if msg_type in ("all", "macro"):
        split_and_send(format_macro_dashboard(macro_data), chat_id=chat_id)

    if msg_type in ("all", "mr"):
        split_and_send(format_mean_reversion(swing_data, macro_data), chat_id=chat_id)

    if msg_type in ("all", "momentum"):
        split_and_send(format_momentum(swing_data, macro_data), chat_id=chat_id)

    if msg_type in ("all", "cov"):
        split_and_send(format_cov_snapshot(swing_data), chat_id=chat_id)

    if msg_type == "divergence":
        split_and_send(format_divergence(swing_data, macro_data), chat_id=chat_id)

    if msg_type == "covgreen":
        split_and_send(format_cov_green_snapshot(swing_data), chat_id=chat_id)

    if msg_type == "sma200":
        from macdv_calculator import SWING_FRAMEWORK_TICKERS
        split_and_send(format_sma200_snapshot(SWING_FRAMEWORK_TICKERS), chat_id=chat_id)

    if msg_type == "riskdistances":
        split_and_send(format_risk_distances(), chat_id=chat_id)

    print("[delivery] done.")
