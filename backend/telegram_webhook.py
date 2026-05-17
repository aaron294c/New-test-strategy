"""
Telegram Webhook — FastAPI router

Registers POST /telegram/webhook to receive Telegram bot updates.
Handles the /update command to trigger on-demand snapshot delivery.

Security: validates X-Telegram-Bot-Api-Secret-Token header against
TELEGRAM_WEBHOOK_SECRET env var (optional but recommended).
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/telegram", tags=["telegram"])

_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")


def _validate_secret(request: Request) -> bool:
    """Validate the Telegram webhook secret token header."""
    if not _WEBHOOK_SECRET:
        return True  # No secret set — skip validation (dev mode)
    header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    return header == _WEBHOOK_SECRET


async def _send_snapshots_async(chat_id: str) -> None:
    """Run snapshot delivery in a thread to avoid blocking the event loop."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _deliver_snapshots, chat_id)


def _deliver_snapshots(chat_id: str, msg_type: str = "all") -> None:
    """Fetch live data and send snapshot(s) to chat_id."""
    try:
        from telegram_delivery import _deliver
        _deliver(chat_id, msg_type)
    except Exception as exc:
        print(f"[webhook] Snapshot delivery error: {exc}")


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """
    Receives Telegram bot updates.
    Responds to /update command by triggering a full snapshot delivery.
    Always returns 200 quickly so Telegram doesn't retry.
    """
    if not _validate_secret(request):
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    try:
        body: dict[str, Any] = await request.json()
    except Exception:
        return JSONResponse({"ok": True})

    message = body.get("message") or body.get("edited_message") or {}
    text: str = (message.get("text") or "").strip().lower()
    chat: dict = message.get("chat") or {}
    chat_id: str = str(chat.get("id", "")) if chat else ""

    if text.startswith("/sizing") and chat_id:
        arg = text[len("/sizing"):].strip()
        from telegram_sizing_reference import handle_sizing_command
        from telegram_bot import send_messages
        msgs = handle_sizing_command(arg)
        background_tasks.add_task(send_messages, msgs, chat_id)
    elif text.startswith("/variants") and chat_id:
        arg = text[len("/variants"):].strip()
        from telegram_variance_reference import handle_variants_command
        from telegram_bot import send_messages
        msgs = handle_variants_command(arg)
        background_tasks.add_task(send_messages, msgs, chat_id)
    elif text.startswith("/guide") and chat_id:
        from telegram_formatters import get_guide_message
        from telegram_bot import send_message
        background_tasks.add_task(send_message, chat_id, get_guide_message())
    elif text.startswith("/help") and chat_id:
        from telegram_formatters import get_help_message
        from telegram_bot import send_message
        background_tasks.add_task(send_message, chat_id, get_help_message())
    else:
        cmd_map = {
            "/update":        "all",
            "/macro":         "macro",
            "/mr":            "mr",
            "/momentum":      "momentum",
            "/divergence":    "divergence",
            "/cov":           "cov",
            "/covgreen":   "covgreen",
            "/200sma":     "sma200",
            "/gammawalls": "gammawalls",
            "/maxpain":    "maxpain",
        }
        for cmd, msg_type in cmd_map.items():
            if text.startswith(cmd) and chat_id:
                background_tasks.add_task(_deliver_snapshots, chat_id, msg_type)
                break

    return JSONResponse({"ok": True})


@router.get("/status")
async def telegram_status() -> JSONResponse:
    """Health check — reports whether bot credentials are configured."""
    from telegram_bot import is_configured
    return JSONResponse({
        "configured": is_configured(),
        "webhook_secret_set": bool(_WEBHOOK_SECRET),
    })
