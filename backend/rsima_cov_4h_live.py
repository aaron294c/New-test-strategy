"""
Live RSI-MA and COV readings on half-day (TradingView 4H) bars for SPY & QQQ.

Used by Telegram commands /rsima4h and /cov4h.

Half-day definition:
  AM bar: 09:30–13:30 ET  (4 clock hours)
  PM bar: 13:30–16:00 ET  (2.5h — TV closes at session end)
  = exactly 2 bars per US trading day

Lookback: 504 bars = 252 trading days × 2 = 1 year.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Optional

import numpy as np
import pandas as pd
import yfinance as yf


_LOOKBACK = 504  # 1 trading year in half-day bars


# ── Hardcoded backtest reference returns (Strategy D: 4H RSI-MA + 4H COV red)
# Source: scripts/rsima_cov_4h_backtest.py  |  Period: ~2yr half-day data
_D_REF: Dict[str, Dict[int, Dict]] = {
    "SPY": {
        5:  {"n": 11, "D5_wr": 100.0, "D5_med": +1.70, "D21_wr": 100.0, "D21_med": +2.94},
        10: {"n": 20, "D5_wr": 100.0, "D5_med": +1.61, "D21_wr": 100.0, "D21_med": +3.29},
        15: {"n": 25, "D5_wr":  96.0, "D5_med": +1.54, "D21_wr": 100.0, "D21_med": +2.95},
    },
    "QQQ": {
        5:  {"n":  9, "D5_wr": 100.0, "D5_med": +1.61, "D21_wr": 100.0, "D21_med": +4.66},
        10: {"n": 22, "D5_wr": 100.0, "D5_med": +1.35, "D21_wr":  90.9, "D21_med": +3.31},
        15: {"n": 27, "D5_wr":  96.3, "D5_med": +1.35, "D21_wr":  85.2, "D21_med": +3.05},
    },
}


def _fetch_half_day(ticker: str, lookback_days: int = 730) -> pd.DataFrame:
    end   = datetime.now()
    start = end - timedelta(days=lookback_days)
    h1 = yf.Ticker(ticker).history(start=start, end=end, interval="1h")
    if h1.empty:
        raise ValueError(f"No 1H data for {ticker}")

    idx = pd.DatetimeIndex(h1.index)
    idx = (idx.tz_localize(None).tz_localize("UTC").tz_convert("America/New_York")
           if idx.tz is None else idx.tz_convert("America/New_York"))
    h1.index = idx

    h, m = idx.hour, idx.minute
    in_session = ((h > 9) | ((h == 9) & (m >= 30))) & (h < 16)
    h1 = h1[in_session].copy()

    idx2 = h1.index
    is_am = (idx2.hour < 13) | ((idx2.hour == 13) & (idx2.minute < 30))
    h1["_date"]    = idx2.date
    h1["_session"] = np.where(is_am, "AM", "PM")

    bars = (
        h1.groupby(["_date", "_session"], sort=True)
        .agg(Open=("Open", "first"), High=("High", "max"),
             Low=("Low", "min"), Close=("Close", "last"),
             Volume=("Volume", "sum"))
        .reset_index()
    )
    ts = (pd.to_datetime(bars["_date"].astype(str))
          + bars["_session"].map({"AM": pd.Timedelta("9h30m"),
                                  "PM": pd.Timedelta("13h30m")}))
    bars.index = ts.dt.tz_localize("America/New_York")
    return bars.drop(columns=["_date", "_session"]).sort_index()


def _calc_rsi_ma(close: pd.Series, rsi_len: int = 14, ma_len: int = 14) -> pd.Series:
    log_ret = np.log(close / close.shift(1)).fillna(0)
    delta   = log_ret.diff()
    gains   = delta.where(delta > 0, 0)
    losses  = -delta.where(delta < 0, 0)
    avg_g   = gains.ewm(alpha=1 / rsi_len, adjust=False).mean()
    avg_l   = losses.ewm(alpha=1 / rsi_len, adjust=False).mean()
    rs      = avg_g / avg_l
    rsi     = (100 - 100 / (1 + rs)).fillna(50)
    return rsi.ewm(span=ma_len, adjust=False).mean()


def _current_pct(series: pd.Series, lookback: int) -> float:
    """Rolling percentile rank of the last value."""
    vals = series.values.astype(float)
    if len(vals) < lookback:
        return float("nan")
    window = vals[-lookback:]
    current = window[-1]
    return float((window[:-1] < current).sum() / (lookback - 1) * 100)


def get_rsima_snapshot(tickers: list[str] | None = None) -> list[Dict]:
    """
    Return current half-day RSI-MA percentile for each ticker.

    Each dict contains:
      ticker, pct, bar_label ("AM" | "PM"), bar_time (str),
      thresholds (which of 5/10/15 are breached), ref (backtest reference data)
    """
    if tickers is None:
        tickers = ["SPY", "QQQ"]
    rows = []
    for t in tickers:
        try:
            h4   = _fetch_half_day(t)
            rsi  = _calc_rsi_ma(h4["Close"])
            pct  = _current_pct(rsi, _LOOKBACK)
            last = h4.index[-1]
            session = "AM" if last.hour < 13 else "PM"
            bar_time = last.strftime("%Y-%m-%d %H:%M ET")

            breached = [lvl for lvl in (5, 10, 15) if not np.isnan(pct) and pct <= lvl]
            ref = _D_REF.get(t, {})

            rows.append({
                "ticker":    t,
                "pct":       round(pct, 1) if not np.isnan(pct) else None,
                "session":   session,
                "bar_time":  bar_time,
                "breached":  breached,     # e.g. [5, 10] means <5th and <10th both met
                "ref":       ref,
            })
        except Exception as exc:
            rows.append({"ticker": t, "error": str(exc)})
    return rows


def get_cov_snapshot(tickers: list[str] | None = None) -> list[Dict]:
    """
    Return current half-day COV dir_metric and bar colour for each ticker.

    Each dict contains:
      ticker, dir_metric, bar_color ("red"|"green"|None), cv_plot, bar_time
    """
    from cov_indicator import compute_cov

    if tickers is None:
        tickers = ["SPY", "QQQ"]
    rows = []
    for t in tickers:
        try:
            h4      = _fetch_half_day(t)
            cov_df  = compute_cov(h4["Close"])
            last    = cov_df.iloc[-1]
            prev    = cov_df.iloc[-2] if len(cov_df) > 1 else None
            last_ts = h4.index[-1]
            session = "AM" if last_ts.hour < 13 else "PM"
            bar_time = last_ts.strftime("%Y-%m-%d %H:%M ET")

            prev_color = prev["bar_color"] if prev is not None else None
            just_turned_red = (last["bar_color"] == "red" and prev_color != "red")

            rows.append({
                "ticker":          t,
                "dir_metric":      round(float(last["dir_metric"]), 3)
                                   if not np.isnan(last["dir_metric"]) else None,
                "bar_color":       last["bar_color"],
                "cv_plot":         round(float(last["cv_plot"]), 2)
                                   if not np.isnan(last["cv_plot"]) else None,
                "just_turned_red": just_turned_red,
                "session":         session,
                "bar_time":        bar_time,
            })
        except Exception as exc:
            rows.append({"ticker": t, "error": str(exc)})
    return rows
