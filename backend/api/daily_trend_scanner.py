"""
Daily Trend Scanner (website port of the TradingView/Pine concept).

Computes:
- Pre-market High/Low (PMH/PML): 04:00-09:29 America/New_York
- Prior Day High/Low (PDH/PDL): previous trading day RTH 09:30-16:00 America/New_York
- Optional ORB High/Low: first N minutes of RTH (default 5)

Data source:
- yfinance intraday download (with pre/post when available)
- Synthetic sample fallback when live fetch fails
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ticker_utils import resolve_yahoo_symbol

NY_TZ = "America/New_York"

router = APIRouter()

_CACHE_TTL_SECONDS = int(os.getenv("DAILY_TREND_CACHE_TTL_SECONDS", "30"))
_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}


class DailyTrendBatchRequest(BaseModel):
    symbols: List[str] = Field(..., min_length=1, max_length=50)
    interval: str = Field("5m")
    days: int = Field(5, ge=1, le=30)
    orb_minutes: int = Field(5, ge=1, le=60)


def _cache_key(symbol: str, interval: str, days: int, orb_minutes: int, include_candles: bool) -> str:
    return f"{symbol.upper()}:{interval}:{days}:{orb_minutes}:{int(include_candles)}"


def _configure_yf_cache(dir_path: Path) -> None:
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        os.environ["YFINANCE_CACHE_DIR"] = str(dir_path)
        os.environ.setdefault("XDG_CACHE_HOME", str(dir_path))
        import yfinance.shared as yf_shared  # type: ignore

        if hasattr(yf_shared, "_CACHE_DIR"):
            yf_shared._CACHE_DIR = str(dir_path)
        if hasattr(yf, "set_tz_cache_location"):
            try:
                yf.set_tz_cache_location(str(dir_path))
            except Exception:
                pass
    except Exception:
        pass


def _download_intraday(symbol: str, *, interval: str, days: int) -> pd.DataFrame:
    cache_dir = Path("/tmp/yfinance_cache")
    _configure_yf_cache(cache_dir)

    yahoo_symbol = resolve_yahoo_symbol(symbol)
    period = f"{days}d"

    try:
        return yf.download(
            yahoo_symbol,
            period=period,
            interval=interval,
            prepost=True,
            progress=False,
            auto_adjust=False,
            threads=False,
        )
    except Exception as e:
        if "readonly" in str(e).lower() and "database" in str(e).lower():
            tmp_cache = Path(tempfile.mkdtemp(prefix="yf_cache_"))
            _configure_yf_cache(tmp_cache)
            return yf.download(
                yahoo_symbol,
                period=period,
                interval=interval,
                prepost=True,
                progress=False,
                auto_adjust=False,
                threads=False,
            )
        raise


def _ensure_ny_timezone(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    idx = df.index
    if not isinstance(idx, pd.DatetimeIndex):
        return df

    if idx.tz is None:
        # yfinance frequently returns tz-naive bars; assume exchange-local for US assets.
        df = df.copy()
        df.index = df.index.tz_localize(NY_TZ)
        return df

    df = df.copy()
    df.index = df.index.tz_convert(NY_TZ)
    return df


def _time_mins(ts: pd.Timestamp) -> int:
    return int(ts.hour) * 60 + int(ts.minute)


def _filter_session(df: pd.DataFrame, *, date_value: datetime.date, start_mins: int, end_mins: int) -> pd.DataFrame:
    if df.empty:
        return df
    mask_date = pd.Index(df.index.date) == date_value
    df_d = df.loc[mask_date]
    if df_d.empty:
        return df_d
    mins = df_d.index.map(_time_mins)
    return df_d.loc[(mins >= start_mins) & (mins < end_mins)]


def _as_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        if isinstance(value, (float, int, np.floating, np.integer)):
            val = float(value)
            if np.isnan(val):
                return None
            return val
        val = float(value)
        if np.isnan(val):
            return None
        return val
    except Exception:
        return None


def _generate_sample_intraday(*, days: int, interval: str) -> pd.DataFrame:
    # Minimal offline fallback: synthetic 5m-ish candles in NY time.
    ny_now = datetime.now(tz=pd.Timestamp.now(tz=NY_TZ).tz)
    end = ny_now.replace(second=0, microsecond=0)
    start = end - timedelta(days=days)

    freq = "5min"
    if interval.endswith("m"):
        try:
            mins = int(interval[:-1])
            freq = f"{mins}min"
        except Exception:
            freq = "5min"
    elif interval.endswith("h"):
        try:
            hours = int(interval[:-1])
            freq = f"{hours}H"
        except Exception:
            freq = "1H"

    idx = pd.date_range(start=start, end=end, freq=freq, tz=NY_TZ)
    if len(idx) < 10:
        idx = pd.date_range(end=end, periods=300, freq="5min", tz=NY_TZ)

    rng = np.random.default_rng(7)
    steps = rng.normal(loc=0.0, scale=0.15, size=len(idx)).cumsum()
    base = 100 + steps

    close = base
    open_ = np.concatenate([[base[0]], base[:-1]])
    spread = np.abs(rng.normal(loc=0.2, scale=0.1, size=len(idx)))
    high = np.maximum(open_, close) + spread
    low = np.minimum(open_, close) - spread
    volume = rng.integers(low=1000, high=20000, size=len(idx))

    df = pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=idx,
    )
    df.attrs["data_source"] = "sample_intraday"
    return df


def _extract_latest_dates(df: pd.DataFrame) -> Tuple[datetime.date, Optional[datetime.date]]:
    dates = list(pd.Index(df.index.date).unique())
    if not dates:
        raise ValueError("No dates in intraday series")
    current = dates[-1]
    prev = dates[-2] if len(dates) >= 2 else None
    return current, prev


def _compute_levels(
    df: pd.DataFrame,
    *,
    orb_minutes: int,
) -> Tuple[Dict[str, Optional[float]], Optional[float]]:
    current_date, prev_date = _extract_latest_dates(df)

    # Session windows in NY minutes.
    pre_start, pre_end = 4 * 60, 9 * 60 + 30  # 04:00-09:29
    rth_start, rth_end = 9 * 60 + 30, 16 * 60  # 09:30-15:59

    pm_df = _filter_session(df, date_value=current_date, start_mins=pre_start, end_mins=pre_end)

    pmh = _as_float(pm_df["High"].max()) if not pm_df.empty else None
    pml = _as_float(pm_df["Low"].min()) if not pm_df.empty else None

    pdh = pdl = prev_close = None
    if prev_date is not None:
        prev_rth = _filter_session(df, date_value=prev_date, start_mins=rth_start, end_mins=rth_end)
        prev_day = df.loc[pd.Index(df.index.date) == prev_date] if prev_rth.empty else prev_rth
        if not prev_day.empty:
            pdh = _as_float(prev_day["High"].max())
            pdl = _as_float(prev_day["Low"].min())
            prev_close = _as_float(prev_day["Close"].iloc[-1])

    # ORB: current day RTH open to open+orb_minutes.
    orb_df = _filter_session(
        df,
        date_value=current_date,
        start_mins=rth_start,
        end_mins=rth_start + int(orb_minutes),
    )
    orb_high = _as_float(orb_df["High"].max()) if not orb_df.empty else None
    orb_low = _as_float(orb_df["Low"].min()) if not orb_df.empty else None

    return (
        {
            "pmh": pmh,
            "pml": pml,
            "pdh": pdh,
            "pdl": pdl,
            "orb_high": orb_high,
            "orb_low": orb_low,
        },
        prev_close,
    )


def _df_to_candles(df: pd.DataFrame) -> List[Dict[str, Any]]:
    candles: List[Dict[str, Any]] = []
    if df.empty:
        return candles

    # Keep payload bounded.
    df2 = df.tail(2500)
    for ts, row in df2.iterrows():
        candles.append(
            {
                "time": ts.isoformat(),
                "open": _as_float(row.get("Open")),
                "high": _as_float(row.get("High")),
                "low": _as_float(row.get("Low")),
                "close": _as_float(row.get("Close")),
                "volume": _as_float(row.get("Volume")),
            }
        )
    return candles


def compute_daily_trend(
    symbol: str,
    *,
    interval: str,
    days: int,
    orb_minutes: int,
    include_candles: bool,
) -> Dict[str, Any]:
    key = _cache_key(symbol, interval, days, orb_minutes, include_candles)
    now = time.time()
    cached = _cache.get(key)
    if cached and (now - cached[0]) < _CACHE_TTL_SECONDS:
        return cached[1]

    try:
        df = _download_intraday(symbol, interval=interval, days=days)
        if df is None or df.empty:
            raise ValueError("Empty intraday dataset")
        data_source = "yfinance"
    except Exception as e:
        df = _generate_sample_intraday(days=days, interval=interval)
        df.attrs["fallback_reason"] = str(e)
        data_source = df.attrs.get("data_source", "sample_intraday")

    df = _ensure_ny_timezone(df)
    levels, prev_close = _compute_levels(df, orb_minutes=orb_minutes)

    price = _as_float(df["Close"].iloc[-1]) if not df.empty else None
    chg_pct = None
    if price is not None and prev_close not in (None, 0.0):
        chg_pct = (price - prev_close) / prev_close * 100.0

    payload: Dict[str, Any] = {
        "symbol": symbol.upper(),
        "as_of": datetime.now(tz=pd.Timestamp.now(tz=NY_TZ).tz).isoformat(),
        "timezone": NY_TZ,
        "interval": interval,
        "days": days,
        "data_source": data_source,
        "price": price,
        "prev_close": prev_close,
        "chg_pct": chg_pct,
        "levels": levels,
    }
    if include_candles:
        payload["candles"] = _df_to_candles(df)

    _cache[key] = (now, payload)
    return payload


@router.get("/api/daily-trend/{symbol}")
async def get_daily_trend(
    symbol: str,
    interval: str = "5m",
    days: int = 5,
    orb_minutes: int = 5,
    include_candles: bool = True,
):
    try:
        return await asyncio.to_thread(
            compute_daily_trend,
            symbol,
            interval=interval,
            days=days,
            orb_minutes=orb_minutes,
            include_candles=include_candles,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute daily trend for {symbol}: {e}")


@router.post("/api/daily-trend/batch")
async def get_daily_trend_batch(request: DailyTrendBatchRequest):
    async def _one(sym: str) -> Tuple[str, Dict[str, Any] | None, str | None]:
        try:
            data = await asyncio.to_thread(
                compute_daily_trend,
                sym,
                interval=request.interval,
                days=request.days,
                orb_minutes=request.orb_minutes,
                include_candles=False,
            )
            return sym, data, None
        except Exception as e:
            return sym, None, str(e)

    tasks = [_one(sym) for sym in request.symbols]
    results = await asyncio.gather(*tasks)

    data: Dict[str, Any] = {}
    errors: Dict[str, str] = {}
    for sym, payload, err in results:
        if payload is not None:
            data[sym.upper()] = payload
        else:
            errors[sym.upper()] = err or "Unknown error"

    return {
        "data": data,
        "errors": errors,
        "as_of": datetime.now(tz=pd.Timestamp.now(tz=NY_TZ).tz).isoformat(),
    }

