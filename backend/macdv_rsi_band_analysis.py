"""
MACD-V 120–150 × RSI-MA percentile band analysis (fixed forward return horizon).

This module is intended to power a frontend tab that mirrors the markdown tables
we've been generating in docs, but as a live API response.

Definitions (consistent with existing backend):
- RSI-MA: RSI(14 Wilder) on diff(log returns), then EMA(14).
- RSI percentile: rolling percentile rank over `pct_lookback` bars.
- MACD-V: ((EMA12(Close)-EMA26(Close)) / ATR(26)) * 100 (repo implementation).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

try:
    from enhanced_backtester import EnhancedPerformanceMatrixBacktester
    from macdv_calculator import MACDVCalculator
except ModuleNotFoundError:
    from backend.enhanced_backtester import EnhancedPerformanceMatrixBacktester  # type: ignore
    from backend.macdv_calculator import MACDVCalculator  # type: ignore


DEFAULT_UNIVERSE = ["AAPL", "NVDA", "GOOGL", "MSFT", "META", "QQQ", "SPY", "BRK-B", "AMZN"]

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


@dataclass(frozen=True)
class ReturnStats:
    n: int
    win_rate: float
    mean: float
    median: float

    def to_dict(self) -> Dict:
        return {
            "n": int(self.n),
            "win_rate": float(self.win_rate) if np.isfinite(self.win_rate) else None,
            "mean": float(self.mean) if np.isfinite(self.mean) else None,
            "median": float(self.median) if np.isfinite(self.median) else None,
        }


def _stats(returns: List[float]) -> ReturnStats:
    if not returns:
        return ReturnStats(n=0, win_rate=float("nan"), mean=float("nan"), median=float("nan"))
    arr = np.asarray(returns, dtype=float)
    return ReturnStats(
        n=int(arr.size),
        win_rate=float((arr > 0).mean() * 100),
        mean=float(arr.mean()),
        median=float(np.median(arr)),
    )


def _macdv_val(data: pd.DataFrame) -> pd.Series:
    df = data.copy()
    df.columns = [c.lower() for c in df.columns]
    # Explicit defaults (requested): fast=12, slow=26, signal=9, atr=26
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


def _non_overlapping_entries(signal: np.ndarray, horizon: int) -> List[int]:
    idxs: List[int] = []
    i = 0
    n = int(signal.size)
    while i < n:
        if signal[i]:
            idxs.append(i)
            i += horizon + 1
        else:
            i += 1
    return idxs


def run_macdv_120_150_rsi_band_analysis(
    tickers: List[str] | None = None,
    period: str = "10y",
    pct_lookback: int = 252,
    horizon: int = 7,
    macdv_lo: float = 120.0,
    macdv_hi: float = 150.0,
    rsi_threshold_non_overlap: float = 45.0,
) -> Dict:
    universe = [t.strip().upper() for t in (tickers or DEFAULT_UNIVERSE) if t and t.strip()]
    if not universe:
        universe = DEFAULT_UNIVERSE[:]

    backtester = EnhancedPerformanceMatrixBacktester(
        tickers=universe,
        lookback_period=pct_lookback,
        rsi_length=14,
        ma_length=14,
        max_horizon=max(21, horizon),
    )

    band_labels = [label for _, _, label in RSI_BANDS]
    table: Dict[str, Dict[str, Dict]] = {}

    all_returns_by_band: Dict[str, List[float]] = {label: [] for label in band_labels}
    all_returns_lt50: List[float] = []
    all_returns_gte50: List[float] = []

    non_overlap_by_ticker: Dict[str, ReturnStats] = {}
    non_overlap_all: List[float] = []

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

        close = work["Close"]
        macd_mask = (work["macdv_val"] >= macdv_lo) & (work["macdv_val"] < macdv_hi)

        table[ticker] = {}
        for rlo, rhi, label in RSI_BANDS:
            band_mask = (work["rsi_pct"] >= rlo) & (work["rsi_pct"] < rhi)
            entry = (macd_mask & band_mask).fillna(False)
            rets = _forward_returns(close, entry, horizon=horizon)

            st = _stats(rets)
            table[ticker][label] = st.to_dict()

            all_returns_by_band[label].extend(rets)
            if rhi <= 50:
                all_returns_lt50.extend(rets)
            if rlo >= 50:
                all_returns_gte50.extend(rets)

        # Non-overlapping: MACD-V in band + RSI<=threshold, fixed exit at D7
        sig = (macd_mask & (work["rsi_pct"] <= rsi_threshold_non_overlap)).fillna(False).to_numpy(dtype=bool)
        entries = _non_overlapping_entries(sig, horizon=horizon)
        closes = close.to_numpy(dtype=float)
        rets_no: List[float] = []
        for i in entries:
            j = i + horizon
            if j >= len(closes):
                continue
            entry_px = closes[i]
            exit_px = closes[j]
            if not np.isfinite(entry_px) or entry_px <= 0 or not np.isfinite(exit_px):
                continue
            rets_no.append(float((exit_px / entry_px - 1.0) * 100.0))
        non_overlap_by_ticker[ticker] = _stats(rets_no)
        non_overlap_all.extend(rets_no)

    # ALL row
    table["ALL"] = {label: _stats(all_returns_by_band[label]).to_dict() for label in band_labels}

    summary = {
        "rsi_lt_50": _stats(all_returns_lt50).to_dict(),
        "rsi_gte_50": _stats(all_returns_gte50).to_dict(),
    }

    non_overlap = {
        "rule": f"MACD-V {macdv_lo:.0f}-{macdv_hi:.0f} & RSI%≤{rsi_threshold_non_overlap:.0f} (non-overlapping, exit D{horizon})",
        "horizon": horizon,
        "results": {"ALL": _stats(non_overlap_all).to_dict(), **{t: s.to_dict() for t, s in non_overlap_by_ticker.items()}},
    }

    return {
        "params": {
            "tickers": universe,
            "period": period,
            "pct_lookback": pct_lookback,
            "horizon": horizon,
            "macdv_params": {
                "fast_length": 12,
                "slow_length": 26,
                "signal_length": 9,
                "atr_length": 26,
            },
            "macdv_lo": macdv_lo,
            "macdv_hi": macdv_hi,
            "rsi_bands": [{"min": rlo, "max": rhi, "label": label} for rlo, rhi, label in RSI_BANDS],
            "rsi_threshold_non_overlap": rsi_threshold_non_overlap,
        },
        "summary": summary,
        "table": table,  # table[ticker][band_label] => ReturnStats dict
        "non_overlapping": non_overlap,
    }
