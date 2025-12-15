"""
Vercel Serverless entrypoint.

Exposes the FastAPI `app` defined in `backend/api.py`.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"

# Backend modules (e.g. `enhanced_backtester.py`) live in `backend/` and are
# imported as top-level modules in `backend/api.py`, so we need `backend/` on
# `sys.path` when importing that file.
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

backend_api_path = BACKEND_DIR / "api.py"
spec = importlib.util.spec_from_file_location("backend_api", backend_api_path)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load backend API module from {backend_api_path}")

backend_api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend_api)

app = backend_api.app

