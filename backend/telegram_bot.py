"""
Telegram Bot — lightweight HTTP wrapper using stdlib only.

Reads config from environment:
  TELEGRAM_BOT_TOKEN  — from @BotFather
  TELEGRAM_CHAT_ID    — channel / group chat ID (negative for channels)
  TELEGRAM_WEBHOOK_SECRET — for validating incoming webhook requests
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional


def _token() -> str:
    t = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not t:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
    return t


def _chat_id() -> str:
    c = os.getenv("TELEGRAM_CHAT_ID", "")
    if not c:
        raise RuntimeError("TELEGRAM_CHAT_ID is not set")
    return c


def _api(method: str) -> str:
    return f"https://api.telegram.org/bot{_token()}/{method}"


def send_message(
    text: str,
    chat_id: Optional[str] = None,
    parse_mode: str = "HTML",
    disable_web_page_preview: bool = True,
) -> bool:
    """
    Send a single Telegram message.  Returns True on success.
    Silently returns False if the bot token / chat ID is not configured yet.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    cid = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
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
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            return bool(result.get("ok"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[telegram] HTTP {e.code}: {body}")
        return False
    except Exception as exc:
        print(f"[telegram] send_message error: {exc}")
        return False


def send_messages(
    texts: list[str],
    chat_id: Optional[str] = None,
    parse_mode: str = "HTML",
) -> bool:
    """Send multiple messages in order."""
    ok = True
    for t in texts:
        if not send_message(t, chat_id=chat_id, parse_mode=parse_mode):
            ok = False
    return ok


def split_and_send(
    text: str,
    chat_id: Optional[str] = None,
    parse_mode: str = "HTML",
    max_len: int = 4096,
) -> bool:
    """
    Split text at newlines to respect Telegram's 4096-char message limit.
    Handles <pre> blocks: closes them before a split and reopens in the next chunk
    so Telegram's HTML parser never sees unbalanced tags.
    """
    if len(text) <= max_len:
        return send_message(text, chat_id=chat_id, parse_mode=parse_mode)

    chunks: list[str] = []
    current = ""
    in_pre = False

    for line in text.split("\n"):
        stripped = line.strip()
        # Track <pre> block boundaries
        if stripped == "<pre>":
            in_pre = True
        elif stripped == "</pre>":
            in_pre = False

        candidate = current + ("\n" if current else "") + line
        if len(candidate) > max_len:
            if current:
                # Close any open <pre> block before ending this chunk
                if in_pre:
                    current += "\n</pre>"
                chunks.append(current)
            # Re-open <pre> at start of next chunk if we were inside one
            current = ("<pre>\n" if in_pre else "") + line
        else:
            current = candidate

    if current:
        chunks.append(current)

    return send_messages(chunks, chat_id=chat_id, parse_mode=parse_mode)


def is_configured() -> bool:
    """Return True if both token and chat ID are set."""
    return bool(os.getenv("TELEGRAM_BOT_TOKEN")) and bool(os.getenv("TELEGRAM_CHAT_ID"))


def set_bot_commands() -> bool:
    """
    Register the bot's command list with Telegram so they appear in the
    menu when users type '/'.  Safe to call on every startup — idempotent.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        return False

    commands = [
        {"command": "update",        "description": "Full snapshot: macro + mean reversion + momentum + CoV"},
        {"command": "macro",         "description": "Macro dashboard (indices, bonds, FX, commodities)"},
        {"command": "mr",            "description": "Mean reversion — live · non-overlapping · overlapping (buttons)"},
        {"command": "ffd",           "description": "Live FFD readings (0-100), ranked — ⭐ = names where FFD<40 is proven to add edge"},
        {"command": "value",         "description": "Fundamentals: ROE/ROIC/EPS/P/E/book/debt — overview or /value <TICKER> for 2/5/7/10yr history"},
        {"command": "sortino",       "description": "Risk-adjusted rankings — EV ÷ downside deviation (DCA-cluster, D5)"},
        {"command": "momentum",      "description": "Momentum table (MACD-V leaders and laggards)"},
        {"command": "divergence",    "description": "1st & 2nd order divergence/dislocation signals"},
        {"command": "cov",           "description": "CoV red-bar scan (Fisher-z ≤ −1.3) with RSI-MA context"},
        {"command": "covgreen",   "description": "CoV Green Exhaustion scan (Fisher-z ≥ +1.3, overextended)"},
        {"command": "200sma",     "description": "200-day SMA distances, ranked negative to positive"},
        {"command": "gammawalls",     "description": "Gamma put walls (ST/LT/Q) ranked by breach depth"},
        {"command": "maxpain",        "description": "Max pain levels ranked by price below max pain"},
        {"command": "kelly_hist",     "description": "Historical Kelly (2000-day): optimal leverage per ticker ranked"},
        {"command": "kelly_dyn",      "description": "Dynamic Kelly (252-day) + leverage by RSI-MA percentile bucket"},
        {"command": "kelly_strategy", "description": "Strategy Kelly: D5 trade returns per RSI-MA bucket — where to lever up"},
        {"command": "rsima4h",        "description": "RSI-MA half-day pct for SPY & QQQ — <5/<10/<15 thresholds + backtest ref returns"},
        {"command": "cov4h",          "description": "COV dir_metric & bar colour for SPY & QQQ half-day bars — red = entry condition"},
        {"command": "sizing",         "description": "Position sizing — /sizing a · /sizing b · /sizing var · /sizing <ticker>"},
        {"command": "variants",       "description": "Downside deviation batches EV-ranked — /variants 1·2·3·4 for specific batch"},
        {"command": "guide",          "description": "Column reference and metric explanations"},
        {"command": "options",        "description": "Options signal — bull put spread setup for QQQ & SPY (RSI-MA <5th pct)"},
        {"command": "iv",             "description": "IV dashboard — VIX / VXN / VIX9D with regime guide & strategy advice"},
        {"command": "optwatch",       "description": "Options watch — RSI-MA percentile progress toward signal threshold"},
        {"command": "optbacktest",    "description": "Full backtested stats: win%, avg win/loss, median, P5-P95 distribution"},
        {"command": "optlog",         "description": "Last 10 logged option signals (date, strikes, credit, max loss)"},
        {"command": "help",           "description": "List all available commands"},
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
