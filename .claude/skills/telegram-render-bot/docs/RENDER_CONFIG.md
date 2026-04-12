# Render Configuration for Always-On Telegram Bot

## Service Type

Use **Web Service** (not Background Worker). You need an HTTP port open so UptimeRobot can ping it.

## render.yaml (if using Infrastructure as Code)

```yaml
services:
  - type: web
    name: my-app
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn backend.api:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: TELEGRAM_BOT_TOKEN
        sync: false          # set manually in dashboard — never commit tokens
      - key: TELEGRAM_CHAT_ID
        sync: false
    healthCheckPath: /health
```

## Health Check Endpoint

Add this to your FastAPI app:

```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

## Keep-Alive Setup (Prevents Sleep on Free Tier)

Render free tier sleeps after **15 minutes** of no inbound HTTP traffic.
When it wakes, the entire process restarts — including the poller thread.
The first command after wakeup takes 30–60 seconds.

**Fix**: UptimeRobot (free) pings your `/health` endpoint every 5 minutes.

1. Create account at uptimerobot.com
2. Add monitor: HTTP(S) → `https://your-app.onrender.com/health`
3. Set interval: **every 5 minutes**
4. That's it — your dyno stays warm

## Environment Variables (set in Render Dashboard)

| Variable | Example | Notes |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | `7123456789:AAFxxx...` | From @BotFather |
| `TELEGRAM_CHAT_ID` | `-1001234567890` | Negative for channels/groups |

**Never** put these in code or `.env` files committed to git.

## Paid Tier Alternative

On Render paid tier, set `sleepPolicy: never` in render.yaml — no UptimeRobot needed.

```yaml
    sleepPolicy: never
```
