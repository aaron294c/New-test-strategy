# FastAPI Integration — Full Lifespan + Poller Pattern

## Complete api.py Structure

```python
"""
api.py — FastAPI app with embedded Telegram long-poller.

The poller runs as a daemon thread started in the FastAPI lifespan.
It survives for the lifetime of the process and dies with it.
"""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.request
from contextlib import asynccontextmanager

from fastapi import FastAPI


# ── Telegram command → delivery msg_type mapping ────────────────────────────
# CRITICAL: Every /command the bot should respond to MUST be in this dict.
# Webhook handler (if you have one) is irrelevant — the poller uses this.
# Also update set_bot_commands() in telegram_bot.py for the / menu.
COMMANDS: dict[str, str] = {
    "/update":     "all",
    "/macro":      "macro",
    "/section_a":  "section_a",
    "/section_b":  "section_b",
    # Add new commands here
}


def _deliver(chat_id: str, msg_type: str) -> None:
    """Import here to avoid circular imports at module load time."""
    from telegram_delivery import _deliver as deliver
    try:
        deliver(chat_id, msg_type)
    except Exception as e:
        print(f"[deliver] error for {msg_type}: {e}")


def _telegram_poll_loop() -> None:
    """
    Long-poll Telegram getUpdates in an infinite loop.

    - Uses 30-second long-poll timeout (Telegram server holds the connection
      open until an update arrives or timeout elapses).
    - urllib timeout is 35s to give Telegram's timeout room to fire first.
    - On any error, waits 5 seconds before retrying (avoids hammering).
    - Each command dispatched in its own daemon thread so slow commands
      (data fetch + format) don't block the poll loop.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("[poller] TELEGRAM_BOT_TOKEN not set — polling disabled.")
        return

    offset = 0
    print("[poller] Starting long-poll loop.")

    while True:
        try:
            url = (
                f"https://api.telegram.org/bot{token}/getUpdates"
                f"?timeout=30&offset={offset}&allowed_updates=[\"message\",\"channel_post\"]"
            )
            with urllib.request.urlopen(url, timeout=35) as resp:
                data    = json.loads(resp.read())
                updates = data.get("result", [])

            for upd in updates:
                offset = upd["update_id"] + 1
                # Handle both private messages and channel posts
                msg  = upd.get("message") or upd.get("channel_post") or {}
                text = (msg.get("text") or "").strip()
                cid  = str(msg.get("chat", {}).get("id", ""))

                if not text or not cid:
                    continue

                # Strip @botname suffix (e.g. /update@MyBot → /update)
                cmd = text.split()[0].split("@")[0].lower()

                if cmd in COMMANDS:
                    threading.Thread(
                        target=_deliver,
                        args=(cid, COMMANDS[cmd]),
                        daemon=True,
                    ).start()
                elif cmd == "/help":
                    from telegram_formatters import get_help_message
                    from telegram_bot import split_and_send
                    split_and_send(get_help_message(), chat_id=cid)
                elif cmd == "/guide":
                    from telegram_formatters import get_guide_message
                    from telegram_bot import split_and_send
                    split_and_send(get_guide_message(), chat_id=cid)
                # else: unknown command — silently ignore

        except Exception as exc:
            print(f"[poller] Error: {exc} — retrying in 5s")
            time.sleep(5)


# ── FastAPI lifespan ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Register commands in Telegram's / menu (idempotent)
    from telegram_bot import set_bot_commands
    set_bot_commands()

    # 2. Start the long-poll background thread
    t = threading.Thread(target=_telegram_poll_loop, daemon=True, name="tg-poller")
    t.start()
    print("[startup] Telegram poller thread started.")

    yield  # App is running

    # Daemon thread dies automatically when the process exits — no cleanup needed


app = FastAPI(lifespan=lifespan)


# ── Health check (required for Render keep-alive) ────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


# ── Your other routes go here ────────────────────────────────────────────────
# @app.get("/api/...")
# @app.post("/api/...")
```

## Why `daemon=True` on the Poller Thread

When FastAPI shuts down (SIGTERM from Render), daemon threads are killed
automatically without needing explicit cleanup. Non-daemon threads would prevent
clean shutdown.

## Why Per-Command `daemon=True` Threads

`_deliver()` can take 5–30 seconds (yfinance data fetch + computation).
If called directly in the poll loop, the loop is blocked during that time and
misses any commands typed while waiting. Spawning a daemon thread per command
keeps the poll loop at ~0ms latency.

## Import Pattern (Avoid Circular Imports)

Notice all formatter/delivery imports are deferred inside functions, not at
module top. This prevents circular import issues when `api.py` imports from
modules that import from other modules that may transitively import from `api.py`.

## Testing the Poller Locally

```bash
export TELEGRAM_BOT_TOKEN=your_token
export TELEGRAM_CHAT_ID=your_chat_id
uvicorn backend.api:app --reload
# Then send /help to the bot — you should see logs immediately
```
