"""
Snapshot API Endpoints - Single Source of Truth

New endpoints for snapshot-based data retrieval ensuring
consistency across all views.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
import json

from snapshot_manager import (
    SnapshotManager,
    CalculationParameters,
    SnapshotMetadata,
    DeterministicRNG,
    parameters_to_display_string,
    get_snapshot_manager
)
from deterministic_trade_engine import DeterministicTradeEngine, TradeSignal, Trade


router = APIRouter(prefix="/api/snapshot", tags=["snapshots"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateSnapshotRequest(BaseModel):
    """Request to create a new snapshot"""
    tickers: List[str] = Field(..., description="List of tickers to include")
    force_refresh: bool = Field(default=False, description="Force data refresh")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Override default parameters")


class SnapshotInfo(BaseModel):
    """Snapshot information for UI display"""
    snapshot_id: str
    created_at: str
    data_start_date: str
    data_end_date: str
    tickers: List[str]
    parameter_hash: str
    parameter_display: str  # Human-readable parameter string


class MetricsRequest(BaseModel):
    """Request for computed metrics"""
    snapshot_id: str = Field(..., description="Snapshot ID to use")
    metric_type: str = Field(..., description="Type of metric: expectancy, regime, composite")
    use_cache: bool = Field(default=True, description="Use cached results if available")


class TradeListRequest(BaseModel):
    """Request for trade list"""
    snapshot_id: str
    ticker: Optional[str] = Field(default=None, description="Filter by ticker")
    regime: Optional[str] = Field(default=None, description="Filter by regime")


class ParameterComparisonRequest(BaseModel):
    """Request to compare metrics across different parameter sets"""
    snapshot_id: str
    parameter_sets: List[Dict[str, Any]]


# ============================================================================
# Snapshot Creation and Management
# ============================================================================

@router.post("/create", response_model=SnapshotInfo)
async def create_snapshot(request: CreateSnapshotRequest):
    """
    Create a new data snapshot with specified parameters.

    This creates an immutable snapshot of market data and parameters
    that serves as the single source of truth for all calculations.
    """
    try:
        manager = get_snapshot_manager()

        # Load parameters
        if request.parameters:
            params = CalculationParameters(**request.parameters)
        else:
            params = CalculationParameters()

        # Import stock data (in production, fetch from data source)
        from stock_statistics import STOCK_METADATA
        from stock_statistics import (
            NVDA_4H_DATA, NVDA_DAILY_DATA,
            MSFT_4H_DATA, MSFT_DAILY_DATA,
            GOOGL_4H_DATA, GOOGL_DAILY_DATA,
            AAPL_4H_DATA, AAPL_DAILY_DATA,
            TSLA_4H_DATA, TSLA_DAILY_DATA,
            META_4H_DATA if 'META_4H_DATA' in dir() else None,
            AMZN_4H_DATA if 'AMZN_4H_DATA' in dir() else None,
            NFLX_4H_DATA, NFLX_DAILY_DATA
        )

        # Build raw data dictionary
        raw_data = {}
        data_sources = {
            "NVDA": (NVDA_4H_DATA, NVDA_DAILY_DATA),
            "MSFT": (MSFT_4H_DATA, MSFT_DAILY_DATA),
            "GOOGL": (GOOGL_4H_DATA, GOOGL_DAILY_DATA),
            "AAPL": (AAPL_4H_DATA, AAPL_DAILY_DATA),
            "TSLA": (TSLA_4H_DATA, TSLA_DAILY_DATA),
            "NFLX": (NFLX_4H_DATA, NFLX_DAILY_DATA)
        }

        for ticker in request.tickers:
            if ticker in data_sources:
                bins_4h, bins_daily = data_sources[ticker]
                raw_data[ticker] = {
                    "metadata": STOCK_METADATA.get(ticker, {}),
                    "bins_4h": bins_4h,
                    "bins_daily": bins_daily
                }

        # Determine data date range
        data_start = "2024-01-01"  # In production, calculate from actual data
        data_end = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Create snapshot
        metadata = manager.create_snapshot(
            raw_data=raw_data,
            parameters=params,
            tickers=request.tickers,
            data_start_date=data_start,
            data_end_date=data_end
        )

        return SnapshotInfo(
            snapshot_id=metadata.snapshot_id,
            created_at=metadata.created_at,
            data_start_date=metadata.data_start_date,
            data_end_date=metadata.data_end_date,
            tickers=metadata.tickers,
            parameter_hash=metadata.parameter_hash,
            parameter_display=parameters_to_display_string(params)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create snapshot: {str(e)}")


@router.get("/list", response_model=List[SnapshotInfo])
async def list_snapshots():
    """List all available snapshots"""
    try:
        manager = get_snapshot_manager()
        snapshots = manager.list_snapshots()

        return [
            SnapshotInfo(
                snapshot_id=s.snapshot_id,
                created_at=s.created_at,
                data_start_date=s.data_start_date,
                data_end_date=s.data_end_date,
                tickers=s.tickers,
                parameter_hash=s.parameter_hash,
                parameter_display=parameters_to_display_string(
                    CalculationParameters(**s.parameters)
                )
            )
            for s in snapshots
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list snapshots: {str(e)}")


@router.get("/latest", response_model=SnapshotInfo)
async def get_latest_snapshot():
    """Get the most recent snapshot"""
    try:
        manager = get_snapshot_manager()
        snapshot = manager.get_latest_snapshot()

        if not snapshot:
            raise HTTPException(status_code=404, detail="No snapshots found")

        metadata = snapshot["metadata"]
        params = CalculationParameters(**metadata["parameters"])

        return SnapshotInfo(
            snapshot_id=metadata["snapshot_id"],
            created_at=metadata["created_at"],
            data_start_date=metadata["data_start_date"],
            data_end_date=metadata["data_end_date"],
            tickers=metadata["tickers"],
            parameter_hash=metadata["parameter_hash"],
            parameter_display=parameters_to_display_string(params)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get latest snapshot: {str(e)}")


@router.get("/{snapshot_id}")
async def get_snapshot(snapshot_id: str):
    """Get complete snapshot data by ID"""
    try:
        manager = get_snapshot_manager()
        snapshot = manager.load_snapshot(snapshot_id)

        if not snapshot:
            raise HTTPException(status_code=404, detail=f"Snapshot {snapshot_id} not found")

        return snapshot

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load snapshot: {str(e)}")


# ============================================================================
# Deterministic Metrics Computation
# ============================================================================

@router.post("/metrics/compute")
async def compute_metrics(request: MetricsRequest):
    """
    Compute metrics from snapshot with deterministic bootstrap.

    Uses fixed RNG seed for reproducible results.
    Results are cached by (snapshot_id, parameter_hash, metric_type).
    """
    try:
        manager = get_snapshot_manager()

        # Check cache first
        if request.use_cache:
            snapshot = manager.load_snapshot(request.snapshot_id)
            if not snapshot:
                raise HTTPException(status_code=404, detail="Snapshot not found")

            param_hash = snapshot["metadata"]["parameter_hash"]
            cached = manager.get_cached_metrics(
                request.snapshot_id,
                param_hash,
                request.metric_type
            )

            if cached:
                return {
                    "cached": True,
                    "snapshot_id": request.snapshot_id,
                    "metric_type": request.metric_type,
                    "results": cached
                }

        # Compute fresh metrics
        snapshot = manager.load_snapshot(request.snapshot_id)
        if not snapshot:
            raise HTTPException(status_code=404, detail="Snapshot not found")

        params = CalculationParameters(**snapshot["metadata"]["parameters"])

        # Initialize deterministic RNG
        rng = DeterministicRNG(seed=params.bootstrap_seed)

        # Compute metrics based on type
        if request.metric_type == "expectancy":
            results = _compute_expectancy_metrics(snapshot, params, rng)
        elif request.metric_type == "regime":
            results = _compute_regime_metrics(snapshot, params, rng)
        elif request.metric_type == "composite":
            results = _compute_composite_metrics(snapshot, params, rng)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown metric type: {request.metric_type}")

        # Cache results
        manager.save_cached_metrics(
            request.snapshot_id,
            snapshot["metadata"]["parameter_hash"],
            request.metric_type,
            results
        )

        return {
            "cached": False,
            "snapshot_id": request.snapshot_id,
            "metric_type": request.metric_type,
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute metrics: {str(e)}")


@router.post("/trades/construct")
async def construct_trades(request: TradeListRequest):
    """
    Construct deterministic trade list from snapshot.

    Uses deterministic trade engine with strict rules:
    - No overlapping positions
    - No same-day re-entry
    - Chronological processing only
    """
    try:
        manager = get_snapshot_manager()
        snapshot = manager.load_snapshot(request.snapshot_id)

        if not snapshot:
            raise HTTPException(status_code=404, detail="Snapshot not found")

        params = CalculationParameters(**snapshot["metadata"]["parameters"])

        # Initialize trade engine
        engine = DeterministicTradeEngine(
            allow_overlapping=params.allow_overlapping_signals,
            allow_same_day_reentry=params.allow_reentry_same_day,
            max_holding_days=params.max_holding_days,
            exit_threshold_percentile=params.exit_threshold,
            dead_zone_threshold=params.dead_zone_threshold
        )

        # Extract signals from snapshot (placeholder - implement signal extraction)
        signals = []  # TODO: Extract from bin data

        # Construct trades
        trades = engine.construct_trades(
            signals=signals,
            price_data={},  # TODO: Extract from snapshot
            percentile_data={},  # TODO: Extract from snapshot
            stop_losses={}  # TODO: Calculate from snapshot
        )

        # Filter by ticker/regime if requested
        filtered_trades = trades
        if request.ticker:
            filtered_trades = [t for t in filtered_trades if t.ticker == request.ticker]
        if request.regime:
            filtered_trades = [t for t in filtered_trades if t.regime == request.regime]

        return {
            "snapshot_id": request.snapshot_id,
            "total_trades": len(filtered_trades),
            "trades": [t.to_dict() for t in filtered_trades]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to construct trades: {str(e)}")


# ============================================================================
# Parameter Comparison
# ============================================================================

@router.post("/compare")
async def compare_parameters(request: ParameterComparisonRequest):
    """
    Compare metrics across different parameter sets.

    Useful for sensitivity analysis and parameter optimization.
    """
    try:
        results = []

        for param_set in request.parameter_sets:
            params = CalculationParameters(**param_set)
            param_hash = params.compute_hash()

            # Check if metrics already computed
            manager = get_snapshot_manager()
            cached = manager.get_cached_metrics(
                request.snapshot_id,
                param_hash,
                "composite"
            )

            if cached:
                results.append({
                    "parameters": params.to_dict(),
                    "parameter_hash": param_hash,
                    "metrics": cached
                })

        return {
            "snapshot_id": request.snapshot_id,
            "comparisons": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare parameters: {str(e)}")


# ============================================================================
# Helper Functions
# ============================================================================

def _compute_expectancy_metrics(snapshot: Dict, params: CalculationParameters, rng: DeterministicRNG) -> Dict:
    """Compute expectancy metrics with deterministic bootstrap"""
    # TODO: Implement using deterministic RNG
    return {"placeholder": "expectancy metrics"}


def _compute_regime_metrics(snapshot: Dict, params: CalculationParameters, rng: DeterministicRNG) -> Dict:
    """Compute regime metrics with deterministic bootstrap"""
    # TODO: Implement using deterministic RNG
    return {"placeholder": "regime metrics"}


def _compute_composite_metrics(snapshot: Dict, params: CalculationParameters, rng: DeterministicRNG) -> Dict:
    """Compute composite metrics with deterministic bootstrap"""
    # TODO: Implement using deterministic RNG
    return {"placeholder": "composite metrics"}
