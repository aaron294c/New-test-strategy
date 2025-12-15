# Deployment

## Option A: Frontend + backend on Vercel (monorepo)

- This repo includes `vercel.json` to:
  - build the Vite app from `frontend/`
  - deploy the FastAPI app as a Serverless Function via `api/index.py`
- Note: the Python backend uses `numpy/pandas`, so cold-starts can be noticeable on serverless.
- “Automatically running” on Vercel means the function starts on-demand per request; you don’t run `uvicorn` yourself there.

### Vercel settings

- Import the repo into Vercel (project root = repo root).
- (Optional) Set env vars:
  - `ALLOWED_ORIGINS` (CORS), e.g. `https://YOUR-PROJECT.vercel.app`
  - `CACHE_DIR` (defaults to `/tmp/...` on Vercel)

## Option B (recommended): Frontend on Vercel, backend elsewhere

- Deploy `frontend/` to Vercel as a static Vite site.
- Deploy `backend/` to a long-running host (Render/Railway/Fly/etc) and run:
  - `uvicorn api:app --host 0.0.0.0 --port $PORT`
- In Vercel, set `VITE_API_URL` to your backend URL (e.g. `https://api.example.com`).

## Local dev

- Backend (uses uvicorn): `./start-backend.sh` (set `RELOAD=0` to disable reload; set `PORT=XXXX` to change port)
- Frontend: `npm -C frontend run dev`
