"""
Gamma Wall Scanner API Endpoint
Runs the Python gamma scanner script and serves JSON data
"""

import subprocess
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Path to the gamma scanner Python script
SCRIPT_DIR = Path(__file__).parent.parent.parent
GAMMA_SCRIPT_PATH = SCRIPT_DIR / "gamma_wall_scanner_script.py"
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
    if not GAMMA_SCRIPT_PATH.exists():
        raise FileNotFoundError(
            f"Gamma scanner script not found at {GAMMA_SCRIPT_PATH}"
        )

    try:
        result = subprocess.run(
            [PYTHON_EXECUTABLE, str(GAMMA_SCRIPT_PATH)],
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
            check=True,
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


@router.get("/api/gamma-data", response_model=GammaDataResponse)
async def get_gamma_data(force_refresh: bool = False):
    """
    Get gamma wall scanner data

    Query parameters:
    - force_refresh: Force a fresh run of the scanner (default: False)

    Returns JSON with level_data arrays and metadata
    """
    try:
        # Run the scanner script
        stdout = run_gamma_scanner_script()

        # Parse the output
        parser = GammaScriptOutput(stdout)
        data = parser.parse()

        if not data.level_data:
            raise ValueError("No gamma data found in script output")

        return data

    except HTTPException:
        # If the caller explicitly asked for a fresh run, bubble up the failure
        if force_refresh:
            raise
        # Otherwise fall back to example data so the UI can still render
        return _build_example_response()
    except Exception as e:
        if force_refresh:
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error: {str(e)}"
            )
        # Graceful fallback when live fetch fails (e.g., no network)
        return _build_example_response()


@router.get("/api/gamma-data/health")
async def gamma_endpoint_health():
    """Health check for gamma data endpoint"""
    script_exists = GAMMA_SCRIPT_PATH.exists()

    return {
        "status": "healthy" if script_exists else "degraded",
        "script_path": str(GAMMA_SCRIPT_PATH),
        "script_exists": script_exists,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/api/gamma-data/example")
async def get_example_data():
    """
    Get example gamma data for testing
    Returns hardcoded example data without running the Python script
    """
    return _build_example_response()
