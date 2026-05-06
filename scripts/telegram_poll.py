#!/usr/bin/env python3
"""
Telegram command poller — on-demand snapshot delivery via long polling.

No public URL or webhook registration required.  Just run this script as
a persistent process and send commands to your bot in Telegram.

Commands:
  /update      — all three snapshots (macro + MR + momentum)
  /macro       — macro dashboard only
  /mr          — mean reversion table only
  /momentum    — momentum table only
  /help        — list available commands

Usage:
  python scripts/telegram_poll.py

Keep it running on any machine that has internet access and the .env file.
Ctrl-C to stop.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# ── path setup ──────────────────────────────────────────────────────────────
_root    = Path(__file__).resolve().parent.parent
_backend = _root / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

# Load .env from repo root
_env = _root / ".env"
if _env.exists():
    with open(_env) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                _k = _k.strip()
                if _k not in os.environ:
                    os.environ[_k] = _v.strip()

# ── constants ────────────────────────────────────────────────────────────────
_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN", "")
_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

_COMMANDS = {
    "/update":   ("all",      "all three snapshots"),
    "/macro":    ("macro",    "macro dashboard"),
    "/mr":       ("mr",       "mean reversion table"),
    "/momentum": ("momentum", "momentum table"),
    "/rsima4h":  ("rsima4h",  "RSI-MA 4H snapshot (SPY & QQQ)"),
    "/cov4h":    ("cov4h",    "COV 4H snapshot (SPY & QQQ)"),
}

_HELP_TEXT = (
    "<b>📊 Market Snapshot Bot</b>\n\n"
    "Available commands:\n"
    "  /update    — all three snapshots\n"
    "  /macro     — macro dashboard\n"
    "  /mr        — mean reversion table\n"
    "  /momentum  — momentum table\n"
    "  /guide     — column reference guide\n"
    "  /rsima4h   — RSI-MA half-day pct for SPY &amp; QQQ\n"
    "               (&lt;5 / &lt;10 / &lt;15 thresholds + backtest ref returns)\n"
    "  /cov4h     — COV dir_metric &amp; bar colour for SPY &amp; QQQ\n"
    "  /help      — this message"
)


# ── Telegram helpers ─────────────────────────────────────────────────────────

def _api_url(method: str) -> str:
    return f"https://api.telegram.org/bot{_TOKEN}/{method}"


def _get(method: str, params: dict | None = None) -> dict:
    url = _api_url(method)
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=35) as r:
        return json.loads(r.read())


def _send(chat_id: str, text: str, parse_mode: str = "HTML") -> None:
    payload = json.dumps({
        "chat_id":     chat_id,
        "text":        text,
        "parse_mode":  parse_mode,
        "disable_web_page_preview": True,
    }).encode()
    req = urllib.request.Request(
        _api_url("sendMessage"),
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            json.loads(r.read())
    except Exception as exc:
        print(f"[poll] send error: {exc}")


# ── Command handling ──────────────────────────────────────────────────────────

def _handle(chat_id: str, text: str) -> None:
    text = text.strip().lower().split()[0] if text.strip() else ""

    if text == "/help":
        _send(chat_id, _HELP_TEXT)
        return

    if text == "/guide":
        from telegram_formatters import get_guide_message
        _send(chat_id, get_guide_message())
        return

    if text not in _COMMANDS:
        return  # ignore unknown messages / non-commands

    msg_type, desc = _COMMANDS[text]

    # Acknowledge immediately so the user knows it's working
    _send(chat_id, f"⏳ Fetching <b>{desc}</b>…")

    try:
        from telegram_delivery import _deliver
        _deliver(chat_id, msg_type)
    except Exception as exc:
        _send(chat_id, f"❌ Error: {exc}")
        print(f"[poll] delivery error: {exc}")


# ── Main polling loop ─────────────────────────────────────────────────────────

def main() -> None:
    if not _TOKEN or not _CHAT_ID:
        print("[poll] ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set.")
        sys.exit(1)

    print(f"[poll] Starting long-poll loop for chat_id={_CHAT_ID}")
    print(f"[poll] Commands: {', '.join(_COMMANDS)}, /help")
    print("[poll] Ctrl-C to stop.\n")

    # Register command menu with Telegram on every startup
    try:
        from telegram_bot import set_bot_commands
        if set_bot_commands():
            print("[poll] ✓ Bot command menu registered with Telegram.")
        else:
            print("[poll] ⚠ set_bot_commands returned False — check token.")
    except Exception as _exc:
        print(f"[poll] ⚠ Could not register bot commands: {_exc}")

    offset: int | None = None

    while True:
        try:
            params: dict = {"timeout": 30, "allowed_updates": ["message"]}
            if offset is not None:
                params["offset"] = offset

            result = _get("getUpdates", params)
            updates = result.get("result", [])

            for update in updates:
                offset = update["update_id"] + 1

                message = update.get("message") or {}
                chat    = message.get("chat") or {}
                text    = (message.get("text") or "").strip()

                # Only respond to the configured chat
                if str(chat.get("id", "")) != _CHAT_ID:
                    continue

                if text:
                    print(f"[poll] Received: {text!r}")
                    _handle(_CHAT_ID, text)

        except KeyboardInterrupt:
            print("\n[poll] Stopped.")
            break
        except urllib.error.URLError as exc:
            print(f"[poll] Network error: {exc} — retrying in 10s")
            time.sleep(10)
        except Exception as exc:
            print(f"[poll] Unexpected error: {exc} — retrying in 5s")
            time.sleep(5)


if __name__ == "__main__":
    main()
