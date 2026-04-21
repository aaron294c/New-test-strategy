"""
Macro RSI-MA Calculator

Fetches OHLCV for all macro instruments defined in macro_instruments.py,
computes RSI-MA (14/14) and 252-bar percentile rank for each, and returns
a unified dict used by the Telegram formatters.

Result structure per key:
  {
    "key":        str,           # instrument key e.g. "XLK"
    "name":       str,           # display name
    "category":   str,           # e.g. "SECTOR"
    "price":      float | None,
    "rsi_ma":     float | None,  # raw RSI-MA value
    "percentile": float | None,  # 0-100
    "rsi_ma_prev": float | None, # previous day RSI-MA (for 1d delta)
    "price_chg_pct": float | None,
    "error":      str | None,
  }
"""

from __future__ import annotations

import time
from typing import Optional

import pandas as pd
import yfinance as yf

from macro_instruments import (
    MACRO_INSTRUMENTS,
    calculate_rsi_ma,
    compute_percentile,
    compute_bond_price_from_yield,
    compute_mmfi_series,
)
from ticker_utils import resolve_yahoo_symbol

# In-memory cache: {key: (data_dict, timestamp)}
_cache: dict[str, tuple[dict, float]] = {}
_CACHE_TTL = 300  # 5 minutes


def _is_fresh(key: str) -> bool:
    if key not in _cache:
        return False
    _, ts = _cache[key]
    return (time.time() - ts) < _CACHE_TTL


def _empty_result(key: str, name: str, category: str, error: str) -> dict:
    return {
        "key": key, "name": name, "category": category,
        "price": None, "rsi_ma": None, "percentile": None,
        "rsi_ma_prev": None, "price_chg_pct": None,
        "trend_label": "", "error": error,
    }


def _derive_trend_label(rsi_ma_series: pd.Series) -> str:
    """
    Derive a simple trend label from the RSI-MA direction.
    Used for macro instruments that don't have MACD-V data.
    Mirrors the macdv_trend_label values used by _trend_arrow().
    """
    if len(rsi_ma_series) < 6:
        return ""
    d1 = float(rsi_ma_series.iloc[-1]) - float(rsi_ma_series.iloc[-2])
    d5 = float(rsi_ma_series.iloc[-1]) - float(rsi_ma_series.iloc[-6])
    if d1 > 1.0 and d5 > 3.0:
        return "ACC"
    if d1 > 0.3:
        return "STR"
    if abs(d1) <= 0.3:
        return "FLAT"
    if d1 < -1.0 and d5 < -3.0:
        return "CRASH"
    return "DECEL"


def _compute_for_series(close: pd.Series, key: str, name: str, category: str) -> dict:
    """Shared computation: RSI-MA + percentile from a Close price series."""
    if close is None or len(close) < 30:
        return _empty_result(key, name, category, "insufficient history")

    rsi_ma_series = calculate_rsi_ma(close)
    percentile = compute_percentile(rsi_ma_series)
    rsi_ma_val = float(rsi_ma_series.iloc[-1]) if not rsi_ma_series.empty else None
    rsi_ma_prev = float(rsi_ma_series.iloc[-2]) if len(rsi_ma_series) >= 2 else None
    trend_label = _derive_trend_label(rsi_ma_series)

    price = float(close.iloc[-1])
    prev_price = float(close.iloc[-2]) if len(close) >= 2 else None
    price_chg = ((price - prev_price) / prev_price * 100) if prev_price else None

    return {
        "key": key, "name": name, "category": category,
        "price": price, "rsi_ma": rsi_ma_val, "percentile": percentile,
        "rsi_ma_prev": rsi_ma_prev, "price_chg_pct": price_chg,
        "trend_label": trend_label, "error": None,
    }


def _fetch_close(yf_symbol: str, period: str = "3y") -> pd.Series | None:
    """Fetch Close price series via yfinance. Returns None on failure."""
    try:
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period=period, auto_adjust=True)
        if hist.empty or "Close" not in hist.columns:
            return None
        close = hist["Close"].dropna()
        # yfinance occasionally returns duplicate timestamps for index tickers
        # (e.g. ^FTSE, ^N225) — keep the last occurrence per date
        if close.index.duplicated().any():
            close = close[~close.index.duplicated(keep="last")]
        return close if len(close) >= 30 else None
    except Exception as exc:
        print(f"[macro_rsi] fetch error for {yf_symbol}: {exc}")
        return None


def _fetch_mmfi(period: str = "3y") -> pd.Series | None:
    """Compute MMFI series from SPY and VIX."""
    try:
        spy_close = _fetch_close("SPY", period)
        vix_close = _fetch_close("^VIX", period)
        if spy_close is None or vix_close is None:
            return None
        return compute_mmfi_series(spy_close, vix_close)
    except Exception as exc:
        print(f"[macro_rsi] MMFI compute error: {exc}")
        return None


def compute_single(key: str) -> dict:
    """
    Compute RSI-MA data for a single instrument key.
    Uses in-memory cache with 5-minute TTL.
    """
    if _is_fresh(key):
        return _cache[key][0]

    cfg = MACRO_INSTRUMENTS.get(key)
    if cfg is None:
        return _empty_result(key, key, "UNKNOWN", "not in registry")

    name = cfg["name"]
    category = cfg["category"]
    derived = cfg.get("derived")

    try:
        if derived == "bond_price":
            # Fetch yield series, convert to bond price series
            close = _fetch_close(cfg["yf"])
            if close is None:
                result = _empty_result(key, name, category, "fetch failed")
            else:
                bond_price = compute_bond_price_from_yield(close)
                result = _compute_for_series(bond_price, key, name, category)
                # Override displayed price with bond price not yield
                if result["price"] is not None:
                    result["price"] = float(bond_price.iloc[-1])

        elif derived == "mmfi":
            mmfi = _fetch_mmfi()
            if mmfi is None:
                result = _empty_result(key, name, category, "MMFI compute failed")
            else:
                result = _compute_for_series(mmfi, key, name, category)

        else:
            close = _fetch_close(cfg["yf"])
            if close is None:
                result = _empty_result(key, name, category, "fetch failed")
            else:
                result = _compute_for_series(close, key, name, category)

    except Exception as exc:
        result = _empty_result(key, name, category, str(exc))

    _cache[key] = (result, time.time())
    return result


def fetch_all_macro_data(keys: Optional[list[str]] = None) -> dict[str, dict]:
    """
    Fetch and compute RSI-MA data for all (or specified) macro instruments.

    Returns a dict keyed by instrument key.  Each value matches the structure
    described in the module docstring.
    """
    target_keys = keys or list(MACRO_INSTRUMENTS.keys())
    results: dict[str, dict] = {}

    # Batch-fetch regular yfinance tickers to reduce HTTP round-trips
    regular_keys = [
        k for k in target_keys
        if MACRO_INSTRUMENTS.get(k, {}).get("yf") and not MACRO_INSTRUMENTS[k].get("derived")
    ]
    yf_symbols = [MACRO_INSTRUMENTS[k]["yf"] for k in regular_keys]

    batch_closes: dict[str, pd.Series] = {}
    if yf_symbols:
        try:
            raw = yf.download(
                yf_symbols,
                period="3y",
                auto_adjust=True,
                group_by="ticker",
                progress=False,
                threads=True,
            )
            # Handle single vs multi-ticker download structure.
            # yfinance returns a flat DataFrame for 1 ticker,
            # a MultiIndex DataFrame (ticker, field) for multiple tickers.
            if len(yf_symbols) == 1:
                sym = yf_symbols[0]
                if "Close" in raw.columns:
                    s = raw["Close"].dropna()
                    if len(s) >= 30:
                        batch_closes[sym] = s
            else:
                for sym in yf_symbols:
                    try:
                        # MultiIndex access: raw[sym]["Close"]
                        s = raw[sym]["Close"].dropna()
                        if len(s) >= 30:
                            batch_closes[sym] = s
                    except Exception:
                        pass
        except Exception as exc:
            print(f"[macro_rsi] batch download error: {exc}")

    # Process regular tickers
    for key in regular_keys:
        if _is_fresh(key):
            results[key] = _cache[key][0]
            continue
        cfg = MACRO_INSTRUMENTS[key]
        sym = cfg["yf"]
        close = batch_closes.get(sym)
        if close is None:
            close = _fetch_close(sym)
        if close is None:
            result = _empty_result(key, cfg["name"], cfg["category"], "fetch failed")
        else:
            result = _compute_for_series(close, key, cfg["name"], cfg["category"])
        _cache[key] = (result, time.time())
        results[key] = result

    # Process derived / special instruments
    special_keys = [k for k in target_keys if k not in regular_keys]
    for key in special_keys:
        results[key] = compute_single(key)

    return results


def compute_live_swing_percentiles(swing_data: list[dict]) -> dict[str, dict]:
    """
    Compute live RSI-MA(14/14) percentiles for swing framework tickers.

    Takes the swing snapshot rows, resolves yfinance symbols via ticker_utils,
    batch-downloads 3 years of history, computes 252-bar RSI-MA percentile.

    Returns {ticker: {"current_percentile": float|None, "price": float|None,
                       "price_chg_pct": float|None, "error": str|None}}
    """
    ticker_to_yf: dict[str, str] = {}
    for row in swing_data:
        ticker = row.get("ticker")
        if ticker:
            ticker_to_yf[ticker] = resolve_yahoo_symbol(ticker)

    if not ticker_to_yf:
        return {}

    yf_symbols = list(set(ticker_to_yf.values()))

    # Batch download to reduce HTTP round-trips
    batch_closes: dict[str, pd.Series] = {}
    try:
        if len(yf_symbols) == 1:
            raw = yf.download(yf_symbols[0], period="3y", auto_adjust=True, progress=False)
            if not raw.empty and "Close" in raw.columns:
                s = raw["Close"].dropna()
                if s.index.duplicated().any():
                    s = s[~s.index.duplicated(keep="last")]
                if len(s) >= 30:
                    batch_closes[yf_symbols[0]] = s
        else:
            raw = yf.download(
                yf_symbols, period="3y", auto_adjust=True,
                group_by="ticker", progress=False, threads=True,
            )
            for sym in yf_symbols:
                try:
                    s = raw[sym]["Close"].dropna()
                    if s.index.duplicated().any():
                        s = s[~s.index.duplicated(keep="last")]
                    if len(s) >= 30:
                        batch_closes[sym] = s
                except Exception:
                    pass
    except Exception as exc:
        print(f"[swing_live] batch download error: {exc}")

    # Lazy import to avoid a circular dependency at module load time.
    from cov_indicator import compute_cov

    results: dict[str, dict] = {}
    for ticker, yf_sym in ticker_to_yf.items():
        close = batch_closes.get(yf_sym)
        if close is None:
            close = _fetch_close(yf_sym)
        if close is None:
            results[ticker] = {
                "current_percentile": None, "price": None,
                "price_chg_pct": None,
                "rsi_ma": None,
                "cov_dir_metric": None, "cov_bar_color": None,
                "error": "fetch failed",
            }
            continue
        try:
            rsi_ma_series = calculate_rsi_ma(close)
            percentile = compute_percentile(rsi_ma_series)

            rsi_ma_last = None
            try:
                last = rsi_ma_series.dropna()
                if not last.empty:
                    rsi_ma_last = float(last.iloc[-1])
            except Exception:
                rsi_ma_last = None

            cov_dm = None
            cov_col = None
            try:
                cov_df = compute_cov(close)
                dm_series = cov_df["dir_metric"].dropna()
                if not dm_series.empty:
                    cov_dm = float(dm_series.iloc[-1])
                col_val = cov_df["bar_color"].iloc[-1]
                cov_col = col_val if isinstance(col_val, str) else None
            except Exception as exc:
                print(f"[swing_live] cov compute failed for {ticker}: {exc}")

            price = float(close.iloc[-1])
            prev_price = None
            for i in range(2, min(6, len(close) + 1)):
                candidate = float(close.iloc[-i])
                if candidate != price:
                    prev_price = candidate
                    break
            if prev_price is None and len(close) >= 2:
                prev_price = float(close.iloc[-2])
            price_chg = ((price - prev_price) / prev_price * 100) if prev_price else None

            results[ticker] = {
                "current_percentile": percentile,
                "price": price,
                "price_chg_pct": price_chg,
                "rsi_ma": rsi_ma_last,
                "cov_dir_metric": cov_dm,
                "cov_bar_color": cov_col,
                "error": None,
            }
        except Exception as exc:
            results[ticker] = {
                "current_percentile": None, "price": None,
                "price_chg_pct": None,
                "rsi_ma": None,
                "cov_dir_metric": None, "cov_bar_color": None,
                "error": str(exc),
            }

    return results
