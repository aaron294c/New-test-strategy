---
name: "Telegram Bot on Render (Long-Poll + Instant Response)"
description: "Wire a Python Telegram bot to a FastAPI/Render deployment using long-polling (not webhooks). Covers: bot setup, HTML message formatting, 4096-char splitting, Render keep-alive, instant command response, setMyCommands, the delivery module pattern, and all common pitfalls. Use when adding a Telegram bot command interface to a Python web service deployed on Render."
---

# Telegram Bot on Render — Long-Poll + Instant Response

## What This Skill Does

Sets up a production Telegram bot that:
- **Runs via long-polling** inside a FastAPI background thread (no webhook infrastructure needed)
- **Responds instantly** to `/commands` — no Render idle sleep delay
- **Formats rich messages** in HTML with tables, pre-blocks, and auto-splitting at 4096 chars
- **Registers the `/` command menu** in Telegram via `setMyCommands`
- **Separates concerns cleanly** across three modules: `telegram_bot.py`, `telegram_formatters.py`, `telegram_delivery.py`

## Prerequisites

- Python 3.11+ FastAPI app deployed (or deployable) to Render
- A bot token from @BotFather
- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in Render environment variables

---

## Quick Start

### 1. Get a Bot Token
1. Message @BotFather on Telegram → `/newbot`
2. Copy the token → set as `TELEGRAM_BOT_TOKEN` in Render env vars
3. Add the bot to your channel/group → get the chat ID (negative number for channels)
4. Set `TELEGRAM_CHAT_ID` in Render env vars

### 2. Drop in the Three Core Modules
Copy the templates from `resources/templates/` into your backend:
- `telegram_bot.py` — raw HTTP send + `setMyCommands`
- `telegram_formatters.py` — message builders + snapshot loader
- `telegram_delivery.py` — orchestrates fetch → format → send

### 3. Wire the Poller into FastAPI Lifespan
See [docs/FASTAPI_INTEGRATION.md](docs/FASTAPI_INTEGRATION.md) for the exact lifespan pattern.

### 4. Configure Render
See [docs/RENDER_CONFIG.md](docs/RENDER_CONFIG.md) for the keep-alive pattern that prevents sleep.

---

## Architecture Overview

```
Telegram User
    │ types /command
    ▼
Telegram Server (getUpdates long-poll)
    │ HTTP GET with 30s timeout
    ▼
_telegram_poll_loop()          ← background thread in api.py
    │ parses text, looks up COMMANDS dict
    ▼
_deliver(chat_id, msg_type)    ← telegram_delivery.py
    │ fetch data → format → split_and_send
    ▼
Telegram User sees message     ← typically <5s end-to-end
```

**Key insight**: The bot is NOT a webhook receiver. It is a long-running background thread that polls Telegram's servers. This is simpler on Render because you don't need a public HTTPS endpoint wired to Telegram.

---

## Step-by-Step Guide

### Step 1: `telegram_bot.py` — The HTTP Layer

This module owns all raw Telegram API calls. Nothing else should call the Telegram API directly.

```python
# telegram_bot.py
import json, os, urllib.request, urllib.error
from typing import Optional

def send_message(text, chat_id=None, parse_mode="HTML", disable_web_page_preview=True):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    cid   = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not cid:
        return False
    payload = {"chat_id": cid, "text": text, "parse_mode": parse_mode,
               "disable_web_page_preview": disable_web_page_preview}
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()).get("ok", False)
    except Exception as e:
        print(f"[telegram] send_message error: {e}")
        return False

def split_and_send(text, chat_id=None, parse_mode="HTML", max_len=4096):
    """Split at newlines, respecting open <pre> blocks."""
    if len(text) <= max_len:
        return send_message(text, chat_id=chat_id, parse_mode=parse_mode)
    chunks, current, in_pre = [], "", False
    for line in text.split("\n"):
        s = line.strip()
        if s == "<pre>":    in_pre = True
        elif s == "</pre>": in_pre = False
        candidate = current + ("\n" if current else "") + line
        if len(candidate) > max_len:
            if current:
                if in_pre: current += "\n</pre>"
                chunks.append(current)
            current = ("<pre>\n" if in_pre else "") + line
        else:
            current = candidate
    if current: chunks.append(current)
    ok = True
    for chunk in chunks:
        if not send_message(chunk, chat_id=chat_id, parse_mode=parse_mode):
            ok = False
    return ok

def set_bot_commands():
    """Call once at startup — registers commands in the Telegram / menu."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token: return False
    commands = [
        {"command": "update",    "description": "Full snapshot"},
        {"command": "macro",     "description": "Macro dashboard"},
        {"command": "help",      "description": "List all commands"},
        # add your commands here
    ]
    payload = json.dumps({"commands": commands}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/setMyCommands",
        data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
            print("[telegram] setMyCommands:", result.get("ok"))
            return result.get("ok", False)
    except Exception as e:
        print(f"[telegram] set_bot_commands error: {e}")
        return False
```

**Why stdlib only?** No `requests`/`httpx` dependency. Keeps the module portable.

---

### Step 2: `telegram_delivery.py` — Fetch → Format → Send

This module is the **only** place that knows about both your data layer and the formatter layer. Keep formatters ignorant of data sources and data sources ignorant of Telegram.

```python
# telegram_delivery.py
def _deliver(chat_id: str, msg_type: str = "all") -> None:
    from your_data_module import fetch_data, load_snapshot
    from telegram_formatters import format_update, format_section_a, format_section_b
    from telegram_bot import split_and_send

    # Only fetch expensive live data when actually needed
    needs_live = msg_type in ("all", "section_a")
    live_data  = fetch_data() if needs_live else {}

    snapshot = load_snapshot()   # fast — reads local JSON

    # Overlay live data onto snapshot rows (your domain logic here)
    if needs_live and snapshot:
        _overlay_live(snapshot, live_data)

    # Dispatch
    if msg_type in ("all", "section_a"):
        split_and_send(format_section_a(snapshot, live_data), chat_id=chat_id)
    if msg_type in ("all", "section_b"):
        split_and_send(format_section_b(snapshot, live_data), chat_id=chat_id)
```

**Critical pattern**: `msg_type` gates which data is fetched. Fetching all data for a focused command (e.g. `/divergence`) wastes 10–30 seconds on Render free tier.

---

### Step 3: The Long-Poller in `api.py`

**THIS IS THE MOST IMPORTANT PART.** The poller owns the command→msg_type mapping. Any new command added to formatters or delivery **must also be added here** or it will silently be ignored.

```python
# Inside api.py

import threading
import time
import json
import urllib.request

# ── COMMAND MAP ─────────────────────────────────────────────────────────────
# Maps Telegram /command → msg_type string passed to _deliver()
COMMANDS = {
    "/update":    "all",
    "/macro":     "macro",
    "/mr":        "mr",
    "/momentum":  "momentum",
    "/divergence": "divergence",
    # Add new commands here AND in set_bot_commands() in telegram_bot.py
}

def _telegram_poll_loop():
    token    = os.getenv("TELEGRAM_BOT_TOKEN", "")
    offset   = 0
    if not token:
        print("[poller] No token — skipping.")
        return

    while True:
        try:
            url = (f"https://api.telegram.org/bot{token}/getUpdates"
                   f"?timeout=30&offset={offset}")
            with urllib.request.urlopen(url, timeout=35) as r:
                data    = json.loads(r.read())
                updates = data.get("result", [])

            for upd in updates:
                offset = upd["update_id"] + 1
                msg    = upd.get("message") or upd.get("channel_post", {})
                text   = (msg.get("text") or "").strip()
                cid    = str(msg.get("chat", {}).get("id", ""))
                if not text or not cid:
                    continue

                cmd = text.split()[0].split("@")[0].lower()  # strip @botname

                if cmd in COMMANDS:
                    threading.Thread(
                        target=_deliver,
                        args=(cid, COMMANDS[cmd]),
                        daemon=True,
                    ).start()
                elif cmd == "/help":
                    from telegram_formatters import get_help_message
                    split_and_send(get_help_message(), chat_id=cid)
                elif cmd == "/guide":
                    from telegram_formatters import get_guide_message
                    split_and_send(get_guide_message(), chat_id=cid)

        except Exception as e:
            print(f"[poller] error: {e}")
            time.sleep(5)


# ── FastAPI lifespan ─────────────────────────────────────────────────────────
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Register / menu on startup
    from telegram_bot import set_bot_commands
    set_bot_commands()
    # Start poller background thread
    t = threading.Thread(target=_telegram_poll_loop, daemon=True)
    t.start()
    yield   # app runs
    # (daemon thread dies automatically on shutdown)

app = FastAPI(lifespan=lifespan)
```

**Why `threading.Thread` per command?** The poller loop must not block waiting for `_deliver()` to finish (data fetch can take 10–30s). Spawning a daemon thread per command keeps the loop responsive.

---

### Step 4: Render Configuration (No Sleep)

See [docs/RENDER_CONFIG.md](docs/RENDER_CONFIG.md) for the full setup. Summary:

1. **Service type**: Web Service (not background worker) — you need an HTTP port for health checks
2. **Keep-alive endpoint**: Add a `GET /health` that returns `{"status": "ok"}`
3. **External ping**: Use UptimeRobot (free) or cron to hit `/health` every 5 minutes — this prevents Render free tier from spinning down your service
4. **Environment vars** (set in Render dashboard, not in code):
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

**The problem without keep-alive**: Render free tier sleeps after 15 minutes of no HTTP traffic. The long-poller thread is killed. First command after wakeup takes 30–60 seconds while the dyno restarts and the poller reconnects.

**With keep-alive pings every 5 min**: Dyno stays warm. Commands respond in <5 seconds.

---

### Step 5: Message Formatting Best Practices

Telegram HTML mode supports: `<b>`, `<i>`, `<code>`, `<pre>`, `<a>`, `<u>`, `<s>`. Nothing else.

```python
# Fixed-width tables: always wrap in <pre>
def format_table(rows):
    lines = ["<pre>"]
    lines.append(f"{'Ticker':<7} {'Pct':>6}  {'Signal'}")
    lines.append("─" * 28)
    for r in rows:
        lines.append(f"{r['ticker']:<7} {r['pct']:>5.1f}%  {r['signal']}")
    lines.append("</pre>")
    return "\n".join(lines)

# Always use split_and_send, never send_message directly for formatted output
split_and_send(format_table(rows), chat_id=chat_id)
```

**4096-char limit**: Telegram rejects messages longer than 4096 characters. `split_and_send` handles this by splitting at newlines and tracking open `<pre>` blocks so HTML tags are never unbalanced across chunks.

---

## Common Pitfalls (Learned the Hard Way)

### ❌ Pitfall 1: Webhook handler vs Poller — two separate code paths
**Problem**: You edit `telegram_webhook.py` to add a new command but it never works.  
**Cause**: On Render, the bot runs via `_telegram_poll_loop` in `api.py`, not the webhook handler. The webhook route is never hit unless you separately configure Telegram's `setWebhook`.  
**Fix**: Always add new commands to **both** `COMMANDS` dict in `api.py` **and** `set_bot_commands()` in `telegram_bot.py`.

### ❌ Pitfall 2: Static snapshot fields not persisted
**Problem**: You add a computed field to your API response but it's always `None` in Telegram.  
**Cause**: The static snapshot JSON on disk was written before your new field existed. The formatter reads from disk — the field isn't there.  
**Fix**: Recompute dynamic fields at snapshot load time, not at write time:
```python
def _load_snapshot():
    rows = json.load(open(snapshot_path))["market_state"]
    _enrich_dynamic_fields(rows)   # ← compute fresh every load
    return rows
```

### ❌ Pitfall 3: Fetching all data for focused commands
**Problem**: `/divergence` takes 45 seconds and times out.  
**Cause**: `_deliver()` always calls `fetch_all_macro_data()` even when divergence doesn't need it.  
**Fix**: Gate data fetching on `msg_type`:
```python
needs_macro = msg_type in ("all", "macro", "mr", "momentum")
macro_data  = fetch_macro() if needs_macro else {}
```

### ❌ Pitfall 4: Second-order fields stale after live overlay
**Problem**: Live RSI percentile is overlaid onto snapshot rows, but derived fields (D2nd = today - yesterday) are now wrong because `current_percentile` changed.  
**Fix**: Re-enrich after overlay:
```python
_overlay_live(snapshot, live)
_enrich_second_order(snapshot)   # ← must come AFTER live overlay
```

### ❌ Pitfall 5: Commands not appearing in the Telegram `/` menu
**Problem**: Users type `/` and don't see the bot's commands listed.  
**Cause**: `setMyCommands` was never called.  
**Fix**: Call `set_bot_commands()` in the FastAPI `lifespan` startup hook. It's idempotent — safe to call every deploy.

### ❌ Pitfall 6: Poll loop blocking on slow commands
**Problem**: While `/update` is running (30s), `/macro` command is queued and delayed.  
**Cause**: `_deliver()` called directly in the poll loop.  
**Fix**: Always spawn a daemon thread per command (shown in Step 3 above).

### ❌ Pitfall 7: Unbalanced HTML tags across message splits
**Problem**: Second chunk of a long table shows raw `</pre>` or table renders broken.  
**Cause**: Naive `text[:4096]` splitting cuts mid-block.  
**Fix**: Use `split_and_send` which closes `<pre>` before splitting and reopens it in the next chunk.

---

## Reference

- [FastAPI Integration Details](docs/FASTAPI_INTEGRATION.md)
- [Render Configuration](docs/RENDER_CONFIG.md)
- [Message Formatting Reference](docs/FORMATTING.md)
- [Template Files](resources/templates/)

---

## Transferring This Skill to a New Project

1. Copy `.claude/skills/telegram-render-bot/` into the new project's `.claude/skills/`
2. Copy `resources/templates/telegram_bot.py` → your backend
3. Copy `resources/templates/telegram_delivery.py` → your backend, adapt the data fetch calls
4. Wire `_telegram_poll_loop` + `set_bot_commands` into your FastAPI `lifespan`
5. Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` to Render env vars
6. Add UptimeRobot ping on `/health` every 5 minutes
