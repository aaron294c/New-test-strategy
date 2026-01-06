"""
Gamma Wall Scanner API Endpoint
Runs the Python gamma scanner script and serves JSON data
"""

import subprocess
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import asyncio

# FIXED: Remove /api prefix - it will be added by main app
router = APIRouter(prefix="/gamma-data", tags=["Gamma Scanner"])

# Simple in-memory cache
_gamma_cache = {
    "data": None,
    "timestamp": None,
    "is_refreshing": False
}
CACHE_TTL_SECONDS = 300  # 5 minutes

# Path to the gamma scanner Python script
SCRIPT_DIR = Path(__file__).parent.parent.parent
GAMMA_SCRIPT_PATH = SCRIPT_DIR / "gamma_wall_scanner_script.py"
ENHANCED_SCANNER_PATH = SCRIPT_DIR / "Restoring" / "enhanced_gamma_scanner_weekly.py"
SCANNER_JSON_CACHE_PATH = SCRIPT_DIR / "cache" / "gamma_walls_data.json"
# Use the same interpreter that is running FastAPI (works on Windows & POSIX)
PYTHON_EXECUTABLE = os.getenv("PYTHON_EXECUTABLE") or sys.executable or "python3"


class GammaDataResponse(BaseModel):
    level_data: List[str]
    last_update: str
    market_regime: str
    current_vix: float
    regime_adjustment_enabled: bool


def _build_example_response() -> GammaDataResponse:
    """Return example gamma data for fallback and the /example route."""
    return GammaDataResponse(
        level_data=[
            "SPX:7000.0,7000.0,6450.0,7400.0,6369.50,6999.00,7000.00,7000.00,5724.09,25.0,1.1,0.0,3.0,7000.00,7000.00,6212.12,7156.38,6054.74,7313.76,6470.00,7210.00,66.7,70.6,86.6,80.0,63.7,65.9,13,30,83,-150.4,157.2,-0.2,0.0,-11.1,8.4;",
            "QQQ(NDX):600.0,600.0,600.0,655.0,570.30,635.27,600.00,600.00,260.80,28.6,1.0,0.0,3.0,600.00,600.00,554.06,651.51,537.82,667.75,620.00,630.00,68.6,67.2,55.6,50.6,48.6,54.6,13,27,83,-410.0,244.5,-14.4,9.2,-0.9,1.5;",
            "AAPL:270.0,280.0,270.0,285.0,253.27,289.64,270.00,280.00,216.77,35.5,1.1,0.0,3.0,270.00,280.00,244.18,298.73,235.08,307.83,220.00,255.00,63.1,63.5,57.0,63.7,62.4,67.6,13,27,104,-38.4,116.9,-2.6,7.3,-7.6,32.6;",
        ],
        last_update=datetime.now().strftime("%b %d, %I:%M%p").lower(),
        market_regime="Normal Volatility",
        current_vix=20.8,
        regime_adjustment_enabled=True,
    )


class GammaScriptOutput:
    """Parser for the Python script output"""

    def __init__(self, stdout: str):
        self.stdout = stdout
        self.level_data: List[str] = []
        self.last_update: str = ""
        self.market_regime: str = "Normal Volatility"
        self.current_vix: float = 15.5
        self.regime_adjustment_enabled: bool = True

    def parse(self) -> GammaDataResponse:
        """Parse the Pine Script formatted output"""
        lines = self.stdout.strip().split('\n')

        for line in lines:
            line = line.strip()

            # Extract level_data lines
            if line.startswith('var string level_data'):
                # Extract the quoted string
                start = line.find('"')
                end = line.rfind('"')
                if start != -1 and end != -1 and start < end:
                    data = line[start + 1:end]
                    self.level_data.append(data)

            # Extract metadata
            elif line.startswith('var string last_update'):
                start = line.find('"')
                end = line.rfind('"')
                if start != -1 and end != -1:
                    self.last_update = line[start + 1:end]

            elif line.startswith('var string market_regime'):
                start = line.find('"')
                end = line.rfind('"')
                if start != -1 and end != -1:
                    self.market_regime = line[start + 1:end]

            elif line.startswith('var float current_vix'):
                parts = line.split('=')
                if len(parts) > 1:
                    try:
                        self.current_vix = float(parts[1].strip())
                    except ValueError:
                        pass

            elif line.startswith('var bool regime_adjustment_enabled'):
                self.regime_adjustment_enabled = 'true' in line.lower()

        # Fallback for last_update if not found
        if not self.last_update:
            self.last_update = datetime.now().strftime("%b %d, %I:%M%p").lower()

        return GammaDataResponse(
            level_data=self.level_data,
            last_update=self.last_update,
            market_regime=self.market_regime,
            current_vix=self.current_vix,
            regime_adjustment_enabled=self.regime_adjustment_enabled,
        )


def run_gamma_scanner_script() -> str:
    """
    Execute the gamma scanner Python script and return its output
    """
    # Prefer the enhanced scanner (v8.x) when available; it also writes backend/cache/gamma_walls_data.json.
    script_path = ENHANCED_SCANNER_PATH if ENHANCED_SCANNER_PATH.exists() else GAMMA_SCRIPT_PATH

    if not script_path.exists():
        raise FileNotFoundError(
            f"Gamma scanner script not found at {script_path}"
        )

    try:
        # yfinance writes cookie/session caches via platformdirs (often under ~/.cache).
        # In some deployments those locations can be read-only; force a writable cache dir.
        cache_home = SCRIPT_DIR / "cache" / ".xdg_cache"
        cache_home.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env.setdefault("XDG_CACHE_HOME", str(cache_home))

        result = subprocess.run(
            [PYTHON_EXECUTABLE, str(script_path)],
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
            check=True,
            env=env,
        )
        return result.stdout
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail=f"Python interpreter not found at '{PYTHON_EXECUTABLE}'. "
                   f"Set PYTHON_EXECUTABLE env var to a valid python executable."
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="Gamma scanner script timed out after 2 minutes"
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gamma scanner script failed: {e.stderr}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run gamma scanner: {str(e)}"
        )

def _read_scanner_json_cache() -> Optional[dict]:
    """
    Read the enhanced scanner JSON output (backend/cache/gamma_walls_data.json).
    Returns None if missing or invalid.
    """
    if not SCANNER_JSON_CACHE_PATH.exists():
        return None

    try:
        with open(SCANNER_JSON_CACHE_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to read scanner JSON cache: {e}")
        return None


def _safe_float(x, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _convert_scanner_json_to_gamma_data_response(payload: dict) -> GammaDataResponse:
    """
    Convert enhanced scanner JSON format (gamma_walls_data.json) into the existing
    Pine-style 36-field `level_data` strings expected by the frontend parser.
    """
    symbols = payload.get("symbols") or {}
    last_update = payload.get("last_update") or datetime.now().strftime("%b %d, %I:%M%p").lower()
    market_regime = payload.get("market_regime") or "Normal Volatility"
    current_vix = _safe_float(payload.get("vix"), 15.5)

    level_data: List[str] = []

    for _, sym in symbols.items():
        symbol_name = str(sym.get("symbol") or "").strip()
        if not symbol_name:
            continue

        current_price = _safe_float(sym.get("current_price"), 0.0)
        if current_price <= 0:
            continue

        st_put = _safe_float(sym.get("st_put_wall"), 0.0)
        st_call = _safe_float(sym.get("st_call_wall"), 0.0)
        lt_put = _safe_float(sym.get("lt_put_wall"), 0.0)
        lt_call = _safe_float(sym.get("lt_call_wall"), 0.0)
        q_put = _safe_float(sym.get("q_put_wall"), 0.0)
        q_call = _safe_float(sym.get("q_call_wall"), 0.0)

        lower_1sd = _safe_float(sym.get("lower_1sd"), 0.0)
        upper_1sd = _safe_float(sym.get("upper_1sd"), 0.0)
        lower_2sd = _safe_float(sym.get("lower_2sd"), 0.0)
        upper_2sd = _safe_float(sym.get("upper_2sd"), 0.0)

        gamma_flip = _safe_float(sym.get("gamma_flip"), current_price)

        st_put_strength = _safe_float(sym.get("st_put_strength"), 0.0)
        st_call_strength = _safe_float(sym.get("st_call_strength"), 0.0)

        category = str(sym.get("category") or "").upper()
        # The enhanced JSON doesn't include per-symbol IV; approximate for downstream features.
        # Indices/ETFs: use VIX proxy; stocks: use a conservative default.
        iv_percent = max(5.0, min(300.0, current_vix)) if category in ("INDEX", "ETF") else 25.0

        # Derive 1.5SD from 1SD "move" if possible
        base_move = current_price - lower_1sd if lower_1sd > 0 else 0.0
        lower_1_5sd = current_price - base_move * 1.5 if base_move > 0 else 0.0
        upper_1_5sd = current_price + base_move * 1.5 if base_move > 0 else 0.0

        fields = [
            st_put,            # 0
            st_call,           # 1
            lt_put,            # 2
            lt_call,           # 3
            lower_1sd,         # 4
            upper_1sd,         # 5
            st_put,            # 6 duplicate
            st_call,           # 7 duplicate
            gamma_flip,        # 8
            iv_percent,        # 9 swing IV%
            2.0,               # 10 call/put ratio (unknown here)
            0.0,               # 11 trend
            3.0,               # 12 activity score
            st_put,            # 13 duplicate
            st_call,           # 14 duplicate
            lower_1_5sd,       # 15
            upper_1_5sd,       # 16
            lower_2sd,         # 17
            upper_2sd,         # 18
            q_put,             # 19
            q_call,            # 20
            st_put_strength,   # 21
            st_call_strength,  # 22
            0.0,               # 23 lt_put_strength (not in JSON)
            0.0,               # 24 lt_call_strength (not in JSON)
            0.0,               # 25 q_put_strength (not in JSON)
            0.0,               # 26 q_call_strength (not in JSON)
            14,                # 27 st_dte (swing)
            30,                # 28 lt_dte (long)
            90,                # 29 q_dte (quarterly)
            0.0,               # 30 st_put_gex
            0.0,               # 31 st_call_gex
            0.0,               # 32 lt_put_gex
            0.0,               # 33 lt_call_gex
            0.0,               # 34 q_put_gex
            0.0,               # 35 q_call_gex
        ]

        formatted_fields: List[str] = []
        for i, v in enumerate(fields):
            if i >= 27 and i <= 29:
                formatted_fields.append(str(int(v)))
            elif i >= 30:
                formatted_fields.append(f"{float(v):.1f}")
            else:
                formatted_fields.append(f"{float(v):.1f}")

        level_data.append(f"{symbol_name}:{','.join(formatted_fields)};")

    return GammaDataResponse(
        level_data=level_data,
        last_update=last_update,
        market_regime=market_regime,
        current_vix=current_vix,
        regime_adjustment_enabled=True,
    )


def _is_cache_valid() -> bool:
    """Check if cached data is still valid."""
    if _gamma_cache["data"] is None or _gamma_cache["timestamp"] is None:
        return False

    age = datetime.now() - _gamma_cache["timestamp"]
    return age.total_seconds() < CACHE_TTL_SECONDS


def _refresh_cache_sync():
    """Refresh the cache synchronously (for background tasks)."""
    if _gamma_cache["is_refreshing"]:
        return  # Already refreshing

    try:
        _gamma_cache["is_refreshing"] = True
        # If the enhanced scanner JSON cache exists, prefer it (fast, deterministic).
        payload = _read_scanner_json_cache()
        if payload is not None:
            data = _convert_scanner_json_to_gamma_data_response(payload)
        else:
            stdout = run_gamma_scanner_script()
            parser = GammaScriptOutput(stdout)
            data = parser.parse()

        if data.level_data:
            _gamma_cache["data"] = data
            _gamma_cache["timestamp"] = datetime.now()
    except Exception as e:
        print(f"Cache refresh failed: {e}")
    finally:
        _gamma_cache["is_refreshing"] = False


@router.get("", response_model=GammaDataResponse)
async def get_gamma_data(force_refresh: bool = False, background_tasks: BackgroundTasks = None):
    """
    Get gamma wall scanner data with caching

    Query parameters:
    - force_refresh: Force a fresh run of the scanner (default: False)

    Returns JSON with level_data arrays and metadata.
    Uses cached data (5 min TTL) unless force_refresh=true.
    """
    # If force refresh, bypass cache
    if force_refresh:
        try:
            # Run the scanner (prefer enhanced) to produce fresh JSON + stdout.
            stdout = run_gamma_scanner_script()

            # Prefer the enhanced JSON cache if it was produced.
            payload = _read_scanner_json_cache()
            if payload is not None:
                data = _convert_scanner_json_to_gamma_data_response(payload)
            else:
                parser = GammaScriptOutput(stdout)
                data = parser.parse()

            if not data.level_data:
                raise ValueError("No gamma data found in script output")

            # Update cache
            _gamma_cache["data"] = data
            _gamma_cache["timestamp"] = datetime.now()

            return data

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch fresh data: {str(e)}"
            )

    # Check cache first
    if _is_cache_valid():
        # Schedule background refresh if cache is getting old (>60% of TTL)
        if background_tasks:
            cache_age = (datetime.now() - _gamma_cache["timestamp"]).total_seconds()
            if cache_age > CACHE_TTL_SECONDS * 0.6:
                background_tasks.add_task(_refresh_cache_sync)

        return _gamma_cache["data"]

    # Cache miss or expired - try to fetch fresh data
    try:
        payload = _read_scanner_json_cache()
        if payload is not None:
            data = _convert_scanner_json_to_gamma_data_response(payload)
        else:
            stdout = run_gamma_scanner_script()
            parser = GammaScriptOutput(stdout)
            data = parser.parse()

        if not data.level_data:
            raise ValueError("No gamma data found in script output")

        # Update cache
        _gamma_cache["data"] = data
        _gamma_cache["timestamp"] = datetime.now()

        return data

    except Exception as e:
        # If we have stale cache, return it with a warning
        if _gamma_cache["data"] is not None:
            print(f"Returning stale cache due to error: {e}")
            return _gamma_cache["data"]

        # No cache available, fall back to example
        return _build_example_response()


@router.get("/health")  # Changed from "/api/gamma-data/health"
async def gamma_endpoint_health():
    """Health check for gamma data endpoint"""
    script_exists = GAMMA_SCRIPT_PATH.exists()
    enhanced_exists = ENHANCED_SCANNER_PATH.exists()
    json_cache_exists = SCANNER_JSON_CACHE_PATH.exists()

    return {
        "status": "healthy" if (script_exists or enhanced_exists) else "degraded",
        "script_path": str(GAMMA_SCRIPT_PATH),
        "script_exists": script_exists,
        "enhanced_script_path": str(ENHANCED_SCANNER_PATH),
        "enhanced_script_exists": enhanced_exists,
        "json_cache_path": str(SCANNER_JSON_CACHE_PATH),
        "json_cache_exists": json_cache_exists,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/example")  # Changed from "/api/gamma-data/example"
async def get_example_data():
    """
    Get example gamma data for testing
    Returns hardcoded example data without running the Python script
    """
    return _build_example_response()


@router.get("/scanner-json")
async def get_scanner_json(force_refresh: bool = False):
    """
    Return the enhanced scanner JSON output (backend/cache/gamma_walls_data.json).
    This is the source of truth for proximity-filtered put walls and (when enabled) 7D max pain.
    """
    if force_refresh or not SCANNER_JSON_CACHE_PATH.exists():
        run_gamma_scanner_script()

    payload = _read_scanner_json_cache()
    if payload is None:
        raise HTTPException(
            status_code=404,
            detail=f"No scanner JSON cache found at {SCANNER_JSON_CACHE_PATH}. Run the enhanced scanner first."
        )

    return payload
