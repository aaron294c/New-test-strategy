"""
telegram_bot.py — Telegram HTTP layer (stdlib only, no dependencies).

Reads config from environment:
  TELEGRAM_BOT_TOKEN  — from @BotFather
  TELEGRAM_CHAT_ID    — channel / group chat ID (negative for channels)
"""

import json
import os
import urllib.error
import urllib.request
from typing import Optional


def send_message(
    text: str,
    chat_id: Optional[str] = None,
    parse_mode: str = "HTML",
    disable_web_page_preview: bool = True,
) -> bool:
    """Send a single Telegram message. Returns True on success."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    cid   = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not cid:
        print("[telegram] Bot token or chat ID not set — skipping send.")
        return False

    payload = {
        "chat_id": cid,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": disable_web_page_preview,
    }
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return bool(json.loads(resp.read()).get("ok"))
    except urllib.error.HTTPError as e:
        print(f"[telegram] HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}")
        return False
    except Exception as exc:
        print(f"[telegram] send_message error: {exc}")
        return False


def split_and_send(
    text: str,
    chat_id: Optional[str] = None,
    parse_mode: str = "HTML",
    max_len: int = 4096,
) -> bool:
    """
    Split text at newlines to respect Telegram's 4096-char message limit.
    Handles <pre> blocks: closes them before a split and reopens in the next
    chunk so Telegram's HTML parser never sees unbalanced tags.
    """
    if len(text) <= max_len:
        return send_message(text, chat_id=chat_id, parse_mode=parse_mode)

    chunks: list[str] = []
    current = ""
    in_pre  = False

    for line in text.split("\n"):
        stripped = line.strip()
        if stripped == "<pre>":    in_pre = True
        elif stripped == "</pre>": in_pre = False

        candidate = current + ("\n" if current else "") + line
        if len(candidate) > max_len:
            if current:
                if in_pre:
                    current += "\n</pre>"
                chunks.append(current)
            current = ("<pre>\n" if in_pre else "") + line
        else:
            current = candidate

    if current:
        chunks.append(current)

    ok = True
    for chunk in chunks:
        if not send_message(chunk, chat_id=chat_id, parse_mode=parse_mode):
            ok = False
    return ok


def is_configured() -> bool:
    """Return True if both token and chat ID are set."""
    return bool(os.getenv("TELEGRAM_BOT_TOKEN")) and bool(os.getenv("TELEGRAM_CHAT_ID"))


def set_bot_commands() -> bool:
    """
    Register the bot's command list with Telegram so they appear in the
    menu when users type '/'.  Safe to call on every startup — idempotent.

    IMPORTANT: Keep this in sync with the COMMANDS dict in api.py.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        return False

    # ── Edit this list to match your bot's commands ──────────────────────────
    commands = [
        {"command": "update",  "description": "Full snapshot"},
        {"command": "macro",   "description": "Macro dashboard"},
        {"command": "help",    "description": "List all available commands"},
        # Add more commands here
    ]

    payload = json.dumps({"commands": commands}).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/setMyCommands",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                print("[telegram] Bot commands registered successfully.")
                return True
            print(f"[telegram] setMyCommands failed: {result}")
            return False
    except Exception as exc:
        print(f"[telegram] set_bot_commands error: {exc}")
        return False
