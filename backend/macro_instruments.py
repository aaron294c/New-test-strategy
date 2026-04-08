"""
Macro Instrument Registry

Defines every instrument fetched for the Telegram macro dashboard.
Each entry: yfinance symbol, display name, category, display unit.

Special entries:
  "derived": "bond_price"  — computed from yield via bond pricing formula
  "derived": "mmfi"        — computed from SPY + VIX interaction
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Current on-the-run 10Y coupon (update ~quarterly after each Treasury auction)
# At 4.42% yield a 4.125% coupon note prices ≈ 97.2
# ---------------------------------------------------------------------------
US10_BOND_COUPON = 4.125


# ---------------------------------------------------------------------------
# Instrument registry — order defines display order within each category
# ---------------------------------------------------------------------------
MACRO_INSTRUMENTS: dict[str, dict] = {
    # ── Volatility ──────────────────────────────────────────────────────────
    "VIX":    {"yf": "^VIX",      "name": "VIX",          "category": "VOLATILITY", "unit": "index"},
    "VVIX":   {"yf": "^VVIX",     "name": "VVIX",         "category": "VOLATILITY", "unit": "index"},
    "MOVE":   {"yf": "^MOVE",     "name": "MOVE (BondVol)","category": "VOLATILITY", "unit": "index"},

    # ── Treasury yields ─────────────────────────────────────────────────────
    "US3M":   {"yf": "^IRX",      "name": "3M Yield",     "category": "TREASURY",   "unit": "yield"},
    "US5Y":   {"yf": "^FVX",      "name": "5Y Yield",     "category": "TREASURY",   "unit": "yield"},
    "US10Y":  {"yf": "^TNX",      "name": "10Y Yield",    "category": "TREASURY",   "unit": "yield"},
    "US30Y":  {"yf": "^TYX",      "name": "30Y Yield",    "category": "TREASURY",   "unit": "yield"},
    # Bond price derived from ^TNX — tracks TradingView "US10" @ 97-99
    "US10P":  {"yf": "^TNX",      "name": "10Y Bond",     "category": "TREASURY",   "unit": "price", "derived": "bond_price"},

    # ── Credit ──────────────────────────────────────────────────────────────
    "HYG":    {"yf": "HYG",       "name": "HY Credit",    "category": "CREDIT",     "unit": "etf"},

    # ── Currencies ──────────────────────────────────────────────────────────
    "USDGBP": {"yf": "USDGBP=X",  "name": "USD/GBP",      "category": "CURRENCY",   "unit": "fx"},
    "GBPUSD": {"yf": "GBPUSD=X",  "name": "GBP/USD",      "category": "CURRENCY",   "unit": "fx"},
    "EURUSD": {"yf": "EURUSD=X",  "name": "EUR/USD",      "category": "CURRENCY",   "unit": "fx"},
    "USDJPY": {"yf": "USDJPY=X",  "name": "USD/JPY",      "category": "CURRENCY",   "unit": "fx"},
    "USDCNH": {"yf": "USDCNH=X",  "name": "USD/CNH",      "category": "CURRENCY",   "unit": "fx"},

    # ── Commodities ─────────────────────────────────────────────────────────
    "GOLD":   {"yf": "GC=F",      "name": "Gold",         "category": "COMMODITY",  "unit": "price"},
    "SILVER": {"yf": "SI=F",      "name": "Silver",       "category": "COMMODITY",  "unit": "price"},
    "USOIL":  {"yf": "CL=F",      "name": "USOIL/WTI",    "category": "COMMODITY",  "unit": "price"},

    # ── Crypto ──────────────────────────────────────────────────────────────
    "BTCUSD": {"yf": "BTC-USD",   "name": "Bitcoin",      "category": "CRYPTO",     "unit": "price"},

    # ── Breadth ─────────────────────────────────────────────────────────────
    "RSP":    {"yf": "RSP",       "name": "Equal-Wt S&P", "category": "BREADTH",    "unit": "etf"},

    # ── Sector ETFs ─────────────────────────────────────────────────────────
    "XLK":    {"yf": "XLK",       "name": "XLK Tech",     "category": "SECTOR",     "unit": "etf"},
    "XLF":    {"yf": "XLF",       "name": "XLF Fin",      "category": "SECTOR",     "unit": "etf"},
    "XLV":    {"yf": "XLV",       "name": "XLV Health",   "category": "SECTOR",     "unit": "etf"},
    "XLE":    {"yf": "XLE",       "name": "XLE Energy",   "category": "SECTOR",     "unit": "etf"},
    "XLP":    {"yf": "XLP",       "name": "XLP Staples",  "category": "SECTOR",     "unit": "etf"},
    "XLY":    {"yf": "XLY",       "name": "XLY Discret",  "category": "SECTOR",     "unit": "etf"},
    "XLRE":   {"yf": "XLRE",      "name": "XLRE RE",      "category": "SECTOR",     "unit": "etf"},
    "XLI":    {"yf": "XLI",       "name": "XLI Indust",   "category": "SECTOR",     "unit": "etf"},
    "XLU":    {"yf": "XLU",       "name": "XLU Utility",  "category": "SECTOR",     "unit": "etf"},
    "XLB":    {"yf": "XLB",       "name": "XLB Matls",    "category": "SECTOR",     "unit": "etf"},
    "XLC":    {"yf": "XLC",       "name": "XLC Comms",    "category": "SECTOR",     "unit": "etf"},

    # ── Global Indexes ───────────────────────────────────────────────────────
    "SPY":    {"yf": "SPY",       "name": "S&P 500",      "category": "INDEX",      "unit": "etf"},
    "QQQ":    {"yf": "QQQ",       "name": "Nasdaq",       "category": "INDEX",      "unit": "etf"},
    "DAX":    {"yf": "^GDAXI",    "name": "DAX",          "category": "INDEX",      "unit": "index"},
    "FTSE":   {"yf": "^FTSE",     "name": "FTSE 100",     "category": "INDEX",      "unit": "index"},
    "N225":   {"yf": "^N225",     "name": "Nikkei",       "category": "INDEX",      "unit": "index"},
}

# Category display order for the macro dashboard message
CATEGORY_ORDER = ["INDEX", "VOLATILITY", "TREASURY", "CREDIT", "CURRENCY", "SECTOR", "BREADTH", "COMMODITY", "CRYPTO"]

# Category headers for Telegram formatting
CATEGORY_HEADERS = {
    "VOLATILITY": "── VOLATILITY ──────────────────────────────",
    "TREASURY":   "── TREASURY ────────────────────────────────",
    "CREDIT":     "── CREDIT ──────────────────────────────────",
    "CURRENCY":   "── CURRENCIES (vs USD) ─────────────────────",
    "COMMODITY":  "── COMMODITIES ─────────────────────────────",
    "CRYPTO":     "── CRYPTO ──────────────────────────────────",
    "BREADTH":    "── BREADTH ─────────────────────────────────",
    "SECTOR":     "── SECTOR ETFs ──────────────────────────────",
    "INDEX":      "── GLOBAL INDEXES ──────────────────────────",
}


# ---------------------------------------------------------------------------
# Calculation helpers (same pipeline as enhanced_backtester.py)
# ---------------------------------------------------------------------------

def calculate_rsi_ma(close: pd.Series, rsi_length: int = 14, ma_length: int = 14) -> pd.Series:
    """
    RSI-MA indicator — identical to EnhancedPerformanceMatrixBacktester.calculate_rsi_ma_indicator.

    Pipeline:
      1. Log returns from Close
      2. Change of log returns (second derivative)
      3. RSI(14) using Wilder's smoothing (RMA)
      4. EMA(14) of RSI
    """
    log_returns = np.log(close / close.shift(1)).fillna(0)
    delta = log_returns.diff()

    gains = delta.where(delta > 0, 0.0)
    losses = -delta.where(delta < 0, 0.0)

    avg_gains = gains.ewm(alpha=1 / rsi_length, adjust=False).mean()
    avg_losses = losses.ewm(alpha=1 / rsi_length, adjust=False).mean()

    rs = avg_gains / avg_losses.replace(0, 1e-10)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(50)

    rsi_ma = rsi.ewm(span=ma_length, adjust=False).mean()
    return rsi_ma


def compute_percentile(series: pd.Series, lookback: int = 252) -> float | None:
    """Compute the current RSI-MA percentile using a 252-bar rolling window."""
    s = series.dropna()
    if len(s) < lookback:
        return None
    window = s.iloc[-lookback:]
    current = window.iloc[-1]
    below = (window.iloc[:-1] < current).sum()
    return float(below / (len(window) - 1) * 100)


def compute_bond_price_from_yield(yield_series: pd.Series, coupon: float = US10_BOND_COUPON, n: int = 20) -> pd.Series:
    """
    Convert a yield (%) series to a bond price series.

    Standard semi-annual bond pricing formula:
      P = C * [1 - (1+r)^-n] / r  +  100 * (1+r)^-n
    where C = coupon/2 (semi-annual cash coupon in $), r = yield/200,
    n = 20 semi-annual periods (10 years).

    At yield ~4.44% and coupon 4.125%  →  price ≈ 97.2 (matches TradingView US10)
    """
    c = coupon / 2         # semi-annual cash coupon per $100 face (e.g. 4.125/2 = 2.0625)
    r = yield_series / 200  # semi-annual yield as decimal (e.g. 4.44/200 = 0.0222)
    r_safe = r.replace(0.0, 1e-6)
    factor = (1 + r_safe) ** (-n)
    price = c * (1 - factor) / r_safe + 100 * factor
    return price


def compute_mmfi_series(spy_close: pd.Series, vix_close: pd.Series) -> pd.Series:
    """
    McClellan Market Facilitation Index daily series.

    Matches macro_risk_metrics.calculate_mmfi logic:
      MMFI = (SPY daily return % * 100) - (VIX daily change % * 10)
    A 50-day rolling mean is then used as the smoothed signal.
    """
    # Strip timezone info so different-tz series (New_York vs Chicago) align on date
    def _strip_tz(s: pd.Series) -> pd.Series:
        if s.index.tz is not None:
            return s.tz_localize(None)
        return s

    df = pd.DataFrame({"SPY": _strip_tz(spy_close), "VIX": _strip_tz(vix_close)}).dropna()
    spy_ret = df["SPY"].pct_change() * 100
    vix_chg = df["VIX"].pct_change() * 100
    raw = spy_ret - vix_chg * 0.1
    smoothed = raw.rolling(window=50, min_periods=10).mean()
    result = smoothed.dropna()
    if result.empty:
        return raw.dropna()  # fallback to unsmoothed if insufficient data
    return result
