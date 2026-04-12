"""
telegram_delivery.py — Shared snapshot delivery logic.

_deliver(chat_id, msg_type) orchestrates: fetch data → format → send.

msg_type: "all" | "section_a" | "section_b" | ...
          Add new types here as you add commands.

IMPORTANT: Gate expensive data fetches on msg_type to keep focused
           commands (e.g. a single-section view) fast.
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

    # ── Lazy imports — avoid circular dependencies at module load time ────────
    # Replace these with your actual data/formatter modules:
    from your_data_module import fetch_live_data, load_static_snapshot
    from telegram_formatters import (
        format_section_a,
        format_section_b,
        format_all,
    )
    from telegram_bot import split_and_send

    print(f"[delivery] type={msg_type}  chat={chat_id}")

    # ── Gate expensive fetches on msg_type ────────────────────────────────────
    # Only fetch what the specific command actually needs.
    # Fetching everything for every command adds 10-30s on Render free tier.
    needs_live = msg_type in ("all", "section_a")
    live_data  = fetch_live_data() if needs_live else {}

    # Load static snapshot (fast — reads local JSON file)
    snapshot = load_static_snapshot()

    # ── Overlay live data onto snapshot ───────────────────────────────────────
    # (your domain logic — update snapshot rows with fresh live values)
    if needs_live and snapshot:
        for row in snapshot:
            ticker = row.get("ticker", "")
            ld = live_data.get(ticker, {})
            if ld.get("current_value") is not None:
                row["current_value"] = ld["current_value"]
        # CRITICAL: Re-enrich any derived fields AFTER live overlay.
        # Derived fields computed from snapshot fields become stale
        # when the underlying values are updated.
        # _enrich_derived_fields(snapshot)

    # ── Dispatch based on msg_type ────────────────────────────────────────────
    if msg_type == "all":
        split_and_send(format_all(snapshot, live_data), chat_id=chat_id)

    elif msg_type == "section_a":
        split_and_send(format_section_a(snapshot, live_data), chat_id=chat_id)

    elif msg_type == "section_b":
        # section_b doesn't need live_data — use cached snapshot only
        split_and_send(format_section_b(snapshot, {}), chat_id=chat_id)

    # Add new msg_type handlers here as you add commands.
    # Remember to also update COMMANDS in api.py and set_bot_commands() in telegram_bot.py.

    print("[delivery] done.")
