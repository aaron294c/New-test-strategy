#!/usr/bin/env python3
"""
Send Telegram market snapshot messages.

Usage:
  python scripts/send_telegram_snapshots.py --type all
  python scripts/send_telegram_snapshots.py --type macro
  python scripts/send_telegram_snapshots.py --type mr
  python scripts/send_telegram_snapshots.py --type momentum

Called by GitHub Actions cron and can also be run manually.
Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Add backend to path when running from repo root or scripts/
_backend = Path(__file__).resolve().parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

# Load .env from repo root if env vars not already set
_env_file = Path(__file__).resolve().parent.parent / ".env"
if _env_file.exists():
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                _k = _k.strip()
                if _k not in os.environ:  # don't override real env vars
                    os.environ[_k] = _v.strip()


def _send(msg_type: str) -> None:
    from macro_rsi_calculator import fetch_all_macro_data, compute_live_swing_percentiles
    from telegram_bot import is_configured, split_and_send
    from telegram_formatters import (
        _load_swing_snapshot,
        format_macro_dashboard,
        format_mean_reversion,
        format_momentum,
    )

    if not is_configured():
        print("[send] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set. Messages will be skipped.")

    print("[send] Fetching macro RSI-MA data...")
    macro_data = fetch_all_macro_data()
    print(f"[send] Got data for {len(macro_data)} instruments.")

    swing_data = _load_swing_snapshot()
    print(f"[send] Loaded swing snapshot with {len(swing_data)} tickers.")

    # Overlay snapshot data with live RSI-MA percentiles from yfinance
    if msg_type in ("mr", "momentum", "all") and swing_data:
        print("[send] Computing live swing percentiles...")
        live = compute_live_swing_percentiles(swing_data)
        updated = 0
        for row in swing_data:
            ticker = row.get("ticker")
            ld = live.get(ticker, {})
            if ld.get("current_percentile") is not None:
                row["current_percentile"] = ld["current_percentile"]
                updated += 1
            if ld.get("price") is not None:
                row["current_price"] = ld["price"]
                row["price_change_pct"] = ld.get("price_chg_pct")
        print(f"[send] Updated live percentiles for {updated}/{len(swing_data)} tickers.")

    if msg_type in ("macro", "all"):
        print("[send] Sending macro dashboard...")
        msg = format_macro_dashboard(macro_data)
        split_and_send(msg)

    if msg_type in ("mr", "all"):
        print("[send] Sending mean reversion table...")
        msg = format_mean_reversion(swing_data, macro_data)
        split_and_send(msg)

    if msg_type in ("momentum", "all"):
        print("[send] Sending momentum table...")
        msg = format_momentum(swing_data, macro_data)
        split_and_send(msg)

    print("[send] Done.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Send Telegram market snapshots")
    parser.add_argument(
        "--type",
        choices=["all", "macro", "mr", "momentum"],
        default="all",
        help="Which snapshot(s) to send (default: all)",
    )
    args = parser.parse_args()
    _send(args.type)


if __name__ == "__main__":
    main()
