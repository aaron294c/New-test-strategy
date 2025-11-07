"""
Snapshot Manager - Single Source of Truth for All Calculations

Creates timestamped, immutable snapshots of market data and precomputed metrics.
Guarantees identical inputs across all views and tabs.
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
from dataclasses import dataclass, asdict


@dataclass
class SnapshotMetadata:
    """Metadata for a data snapshot"""
    snapshot_id: str  # e.g., "snapshot_2025-11-06T17:00:00Z"
    created_at: str   # ISO8601 timestamp
    data_start_date: str
    data_end_date: str
    tickers: List[str]
    parameters: Dict[str, Any]
    parameter_hash: str  # MD5 hash of parameters for cache keying

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CalculationParameters:
    """Centralized parameter settings - single source of truth"""

    # Lookback windows
    percentile_lookback: int = 500  # 500 periods for percentile mapping
    regime_lookback: int = 500      # 500 periods for regime detection (aligned)
    trade_lookback_days: int = 7    # 7 days for recent trade metrics

    # Percentile bin definitions
    entry_bins: List[str] = None    # ["0-5", "5-15"]
    exit_threshold: int = 50         # Exit at 50th percentile
    dead_zone_threshold: int = 50    # Strategy stops working above 50%

    # Stop loss formula
    stop_loss_method: str = "robust"  # "robust", "atr", or "fixed"
    atr_multiplier: float = 1.2
    std_multiplier: float = 2.0
    confidence_level: float = 0.95

    # Bootstrap settings
    bootstrap_iterations: int = 10000
    bootstrap_seed: int = 42          # Fixed seed for deterministic results
    bootstrap_confidence: float = 0.95
    block_size: int = 3               # Block size for serial correlation

    # Trade construction rules
    allow_overlapping_signals: bool = False
    allow_reentry_same_day: bool = False
    max_holding_days: int = 21
    min_holding_days: int = 1

    # Risk parameters
    risk_per_trade: float = 0.02      # 2% risk per trade
    max_positions: int = 5

    # Composite scoring weights
    expectancy_weight: float = 0.60
    confidence_weight: float = 0.25
    percentile_weight: float = 0.15

    def __post_init__(self):
        if self.entry_bins is None:
            self.entry_bins = ["0-5", "5-15"]

    def to_dict(self) -> Dict:
        d = asdict(self)
        return d

    def compute_hash(self) -> str:
        """Compute MD5 hash of parameters for cache keying"""
        param_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.md5(param_str.encode()).hexdigest()[:8]


class SnapshotManager:
    """Manages data snapshots and ensures single source of truth"""

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path(__file__).parent / "snapshots"
        self.data_dir.mkdir(exist_ok=True)
        self.cache_dir = self.data_dir / "cache"
        self.cache_dir.mkdir(exist_ok=True)

    def create_snapshot(
        self,
        raw_data: Dict[str, Any],
        parameters: CalculationParameters,
        tickers: List[str],
        data_start_date: str,
        data_end_date: str
    ) -> SnapshotMetadata:
        """Create a new immutable snapshot"""

        # Generate snapshot ID with timestamp
        now = datetime.now(timezone.utc)
        snapshot_id = f"snapshot_{now.strftime('%Y-%m-%dT%H:%M:%SZ')}"

        # Create metadata
        metadata = SnapshotMetadata(
            snapshot_id=snapshot_id,
            created_at=now.isoformat(),
            data_start_date=data_start_date,
            data_end_date=data_end_date,
            tickers=tickers,
            parameters=parameters.to_dict(),
            parameter_hash=parameters.compute_hash()
        )

        # Build complete snapshot
        snapshot = {
            "metadata": metadata.to_dict(),
            "data": raw_data
        }

        # Save snapshot to disk
        snapshot_file = self.data_dir / f"{snapshot_id}.json"
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot, f, indent=2)

        print(f"✓ Created snapshot: {snapshot_id}")
        print(f"  Parameters hash: {metadata.parameter_hash}")
        print(f"  Tickers: {len(tickers)}")
        print(f"  Saved to: {snapshot_file}")

        return metadata

    def load_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Load a snapshot by ID"""
        snapshot_file = self.data_dir / f"{snapshot_id}.json"

        if not snapshot_file.exists():
            return None

        with open(snapshot_file, 'r') as f:
            return json.load(f)

    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Get the most recent snapshot"""
        snapshots = sorted(self.data_dir.glob("snapshot_*.json"), reverse=True)

        if not snapshots:
            return None

        with open(snapshots[0], 'r') as f:
            return json.load(f)

    def list_snapshots(self) -> List[SnapshotMetadata]:
        """List all available snapshots"""
        snapshots = []

        for snapshot_file in sorted(self.data_dir.glob("snapshot_*.json")):
            with open(snapshot_file, 'r') as f:
                data = json.load(f)
                metadata = SnapshotMetadata(**data["metadata"])
                snapshots.append(metadata)

        return snapshots

    def get_cached_metrics(
        self,
        snapshot_id: str,
        parameter_hash: str,
        metric_type: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached computed metrics"""
        cache_key = f"{snapshot_id}_{parameter_hash}_{metric_type}"
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            with open(cache_file, 'r') as f:
                cached = json.load(f)
                print(f"✓ Cache hit: {metric_type} for {snapshot_id}")
                return cached

        return None

    def save_cached_metrics(
        self,
        snapshot_id: str,
        parameter_hash: str,
        metric_type: str,
        metrics: Dict[str, Any]
    ):
        """Save computed metrics to cache"""
        cache_key = f"{snapshot_id}_{parameter_hash}_{metric_type}"
        cache_file = self.cache_dir / f"{cache_key}.json"

        with open(cache_file, 'w') as f:
            json.dump(metrics, f, indent=2)

        print(f"✓ Cached: {metric_type} for {snapshot_id}")

    def clear_cache(self, snapshot_id: Optional[str] = None):
        """Clear cached metrics for a snapshot or all caches"""
        if snapshot_id:
            pattern = f"{snapshot_id}_*.json"
        else:
            pattern = "*.json"

        for cache_file in self.cache_dir.glob(pattern):
            cache_file.unlink()

        print(f"✓ Cleared cache: {pattern}")


class DeterministicRNG:
    """Deterministic random number generator for bootstrap"""

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)
        self.seed = seed

    def resample_indices(self, n: int, size: int) -> np.ndarray:
        """Generate deterministic bootstrap sample indices"""
        return self.rng.integers(0, n, size=size)

    def resample_blocks(self, n: int, block_size: int) -> List[int]:
        """Generate deterministic block bootstrap indices"""
        num_blocks = int(np.ceil(n / block_size))
        blocks = []

        for _ in range(num_blocks):
            block_start = self.rng.integers(0, max(1, n - block_size + 1))
            for offset in range(block_size):
                if block_start + offset < n:
                    blocks.append(block_start + offset)

        return blocks[:n]  # Ensure exact sample size

    def reset(self):
        """Reset RNG to initial seed"""
        self.rng = np.random.default_rng(self.seed)


def create_default_parameters() -> CalculationParameters:
    """Create default parameter set"""
    return CalculationParameters()


def parameters_to_display_string(params: CalculationParameters) -> str:
    """Format parameters for UI display"""
    return (
        f"Lookbacks: Percentile={params.percentile_lookback}d, "
        f"Regime={params.regime_lookback}d, Trades={params.trade_lookback_days}d | "
        f"Bins: Entry={','.join(params.entry_bins)}, Exit={params.exit_threshold}% | "
        f"Stop: {params.stop_loss_method} (ATR×{params.atr_multiplier}, σ×{params.std_multiplier}) | "
        f"Bootstrap: n={params.bootstrap_iterations}, seed={params.bootstrap_seed}"
    )


# Singleton instance
_default_manager = None

def get_snapshot_manager() -> SnapshotManager:
    """Get singleton snapshot manager"""
    global _default_manager
    if _default_manager is None:
        _default_manager = SnapshotManager()
    return _default_manager
