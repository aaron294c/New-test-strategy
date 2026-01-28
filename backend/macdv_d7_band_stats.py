"""
Cached MACD-V>120 × RSI-%ile band D7 statistics for Swing Framework.

Purpose:
- Precompute D7 forward-return stats (win rate, mean, median) for each ticker,
  conditional on:
    1) MACD-V value > macdv_lo (default 120)
    2) RSI-MA percentile being within a given RSI band (same buckets as MACD-V × RSI tab)
- Persist results to disk so the Live Market State table can "plug in" values
  without recomputing every page load.

Notes:
- This is *not* the same as the existing MACD-V tab (which uses 120–150). Here we use
  macdv_val > 120 with no upper cap (per user request).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

try:
    from enhanced_backtester import EnhancedPerformanceMatrixBacktester
    from macdv_calculator import MACDVCalculator
except ModuleNotFoundError:
    from backend.enhanced_backtester import EnhancedPerformanceMatrixBacktester  # type: ignore
    from backend.macdv_calculator import MACDVCalculator  # type: ignore


RSI_BANDS: List[Tuple[float, float, str]] = [
    (0, 5, "<5"),
    (5, 10, "5-10"),
    (10, 15, "10-15"),
    (15, 20, "15-20"),
    (20, 30, "20-30"),
    (30, 40, "30-40"),
    (40, 50, "40-50"),
    (50, 60, "50-60"),
    (60, 70, "60-70"),
    (70, 80, "70-80"),
    (80, 90, "80-90"),
    (90, 100, "90-100"),
]


def _stats(returns: List[float]) -> Dict[str, Any]:
    if not returns:
        return {"n": 0, "win_rate": None, "mean": None, "median": None}
    arr = np.asarray(returns, dtype=float)
    return {
        "n": int(arr.size),
        "win_rate": float((arr > 0).mean() * 100.0),
        "mean": float(arr.mean()),
        "median": float(np.median(arr)),
    }


def _macdv_val(data: pd.DataFrame) -> pd.Series:
    df = data.copy()
    df.columns = [str(c).lower() for c in df.columns]
    calc = MACDVCalculator(fast_length=12, slow_length=26, signal_length=9, atr_length=26)
    out = calc.calculate_macdv(df, source_col="close")
    return out["macdv_val"]


def _forward_returns(close: pd.Series, entry_mask: pd.Series, horizon: int) -> List[float]:
    closes = close.to_numpy(dtype=float)
    idxs = np.flatnonzero(entry_mask.to_numpy(dtype=bool))
    out: List[float] = []
    n = len(closes)
    for i in idxs:
        j = i + horizon
        if j >= n:
            continue
        entry_px = closes[i]
        exit_px = closes[j]
        if not np.isfinite(entry_px) or entry_px <= 0 or not np.isfinite(exit_px):
            continue
        out.append(float((exit_px / entry_px - 1.0) * 100.0))
    return out


_CACHE_DIR = Path(__file__).resolve().parent / "cache" / "macdv_d7_band_stats"

_mem_cache: Dict[str, Dict[str, Any]] = {}
_mem_cache_ts: Dict[str, datetime] = {}


def _is_fresh(ts: datetime | None, ttl_seconds: int) -> bool:
    if ts is None:
        return False
    return (datetime.now(timezone.utc) - ts).total_seconds() < ttl_seconds


def _cache_key(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:16]


def _cache_path(key: str) -> Path:
    return _CACHE_DIR / f"macdv_d7_band_stats_{key}.json"


def _read_disk_cache(path: Path, ttl_seconds: int) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        if not isinstance(payload, dict):
            return None
        ts_raw = payload.get("generated_at")
        if not isinstance(ts_raw, str):
            return None
        try:
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        except Exception:
            return None
        if not _is_fresh(ts.astimezone(timezone.utc), ttl_seconds):
            return None
        return payload
    except Exception:
        return None


def _write_disk_cache(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def compute_macdv_d7_band_stats(
    tickers: List[str],
    *,
    period: str = "10y",
    pct_lookback: int = 252,
    horizon: int = 7,
    macdv_lo: float = 120.0,
) -> Dict[str, Any]:
    universe = [t.strip().upper() for t in tickers if isinstance(t, str) and t.strip()]
    universe = sorted(set(universe))

    backtester = EnhancedPerformanceMatrixBacktester(
        tickers=universe,
        lookback_period=pct_lookback,
        rsi_length=14,
        ma_length=14,
        max_horizon=max(21, horizon),
    )

    band_labels = [label for _, _, label in RSI_BANDS]
    table: Dict[str, Dict[str, Dict[str, Any]]] = {}
    all_by_band: Dict[str, List[float]] = {label: [] for label in band_labels}

    for ticker in universe:
        data = backtester.fetch_data(ticker, period=period)
        if data is None or getattr(data, "empty", True):
            continue

        rsi_ma = backtester.calculate_rsi_ma_indicator(data)
        rsi_pct = backtester.calculate_percentile_ranks(rsi_ma)
        macdv = _macdv_val(data)

        work = data.copy()
        work["macdv_val"] = macdv
        work["rsi_pct"] = rsi_pct
        work = work.dropna(subset=["Close", "macdv_val", "rsi_pct"]).copy()
        work.reset_index(drop=True, inplace=True)
        if work.empty:
            continue

        close = work["Close"]
        macd_mask = (work["macdv_val"] > macdv_lo).fillna(False)

        table[ticker] = {}
        for rlo, rhi, label in RSI_BANDS:
            band_mask = (work["rsi_pct"] >= rlo) & (work["rsi_pct"] < rhi)
            entry = (macd_mask & band_mask).fillna(False)
            rets = _forward_returns(close, entry, horizon=horizon)
            table[ticker][label] = _stats(rets)
            all_by_band[label].extend(rets)

    table["ALL"] = {label: _stats(all_by_band[label]) for label in band_labels}

    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "params": {
            "tickers": universe,
            "period": period,
            "pct_lookback": pct_lookback,
            "horizon": horizon,
            "macdv_lo": macdv_lo,
            "rsi_bands": [{"min": rlo, "max": rhi, "label": label} for rlo, rhi, label in RSI_BANDS],
        },
        "table": table,
    }


def get_cached_macdv_d7_band_stats(
    tickers: List[str],
    *,
    period: str = "10y",
    pct_lookback: int = 252,
    horizon: int = 7,
    macdv_lo: float = 120.0,
    ttl_seconds: int = 7 * 24 * 3600,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    key_payload = {
        "tickers": sorted({t.strip().upper() for t in tickers if isinstance(t, str) and t.strip()}),
        "period": period,
        "pct_lookback": int(pct_lookback),
        "horizon": int(horizon),
        "macdv_lo": float(macdv_lo),
    }
    key = _cache_key(key_payload)

    if not force_refresh and key in _mem_cache and _is_fresh(_mem_cache_ts.get(key), min(300, ttl_seconds)):
        return _mem_cache[key]

    path = _cache_path(key)
    if not force_refresh:
        disk = _read_disk_cache(path, ttl_seconds=ttl_seconds)
        if disk is not None:
            _mem_cache[key] = disk
            _mem_cache_ts[key] = datetime.now(timezone.utc)
            return disk

    payload = compute_macdv_d7_band_stats(
        key_payload["tickers"],
        period=period,
        pct_lookback=pct_lookback,
        horizon=horizon,
        macdv_lo=macdv_lo,
    )
    _write_disk_cache(path, payload)
    _mem_cache[key] = payload
    _mem_cache_ts[key] = datetime.now(timezone.utc)
    return payload
