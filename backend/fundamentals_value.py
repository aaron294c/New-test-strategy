"""
Fundamentals / valuation engine for the /value Telegram command.

Source: yfinance (no API key; Yahoo's free fundamentals).
Why yfinance and not Alpha Vantage / Polygon:
  - Alpha Vantage free tier = 25 requests/day; the stock subset alone is ~34
    names and the full fundamental set needs income+balance+cashflow per name,
    which blows the daily quota many times over. It cannot drive this breadth.
  - One yfinance Ticker exposes .info + annual & quarterly income / balance /
    cashflow with generous limits, enough to compute every requested metric.
  - Limitation: Yahoo returns ~5 fiscal years of statements, so genuine
    7yr / 10yr-ago snapshots are not available from free data and surface as
    N/A. Averages are computed over the available window and labelled as such.
    True 10yr depth requires a premium feed (future enhancement).

Metrics computed (current + per fiscal year + quarterly):
  - ROE                     = Net Income / Stockholders Equity
  - ROIC                    = NOPAT / Invested Capital   (NOPAT = EBIT x (1 - tax))
  - Unlevered FCF / share   = (FCF + after-tax interest) / diluted shares
  - P/E                     = year-end price / Diluted EPS
  - EPS                     = Diluted EPS
  - Book value / share      = Stockholders Equity / shares
  - Debt / Equity           = Total Debt / Stockholders Equity
  - Debt / Assets           = Total Debt / Total Assets
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional

import yfinance as yf

from macdv_calculator import SWING_FRAMEWORK_TICKERS

# ── Universe classification ───────────────────────────────────────────────────
# Everything in SWING_FRAMEWORK_TICKERS that is NOT an individual equity.
# Excludes ETFs, indices, futures, FX, commodities (gold/silver), crypto, vol.
_NON_STOCK = {
    "SMH", "SOXX", "XLI", "QQQ", "SPY",          # ETFs
    "GLD", "SLV",                                  # commodity ETFs
    "BTC-USD",                                     # crypto
    "DX-Y.NYB",                                    # US dollar index
}


def is_stock(ticker: str) -> bool:
    """True for individual equities only (the /value universe)."""
    t = (ticker or "").upper()
    if not t:
        return False
    if t.startswith("^"):           # ^VIX, ^TNX, ^N225, ^GDAXI, ^FTSE
        return False
    if t.endswith("=F"):            # ES=F, NQ=F futures
        return False
    if t.endswith("=X"):            # FX pairs
        return False
    if t.endswith("-USD"):          # crypto
        return False
    if t in _NON_STOCK:
        return False
    return True


def stock_universe() -> list[str]:
    """The individual-equity subset of the swing framework universe."""
    return [t for t in SWING_FRAMEWORK_TICKERS if is_stock(t)]


# ── safe numeric helpers ──────────────────────────────────────────────────────
def _num(v) -> Optional[float]:
    try:
        if v is None:
            return None
        f = float(v)
        if f != f:          # NaN
            return None
        return f
    except (TypeError, ValueError):
        return None


def _row(df, *names):
    """First matching row from a yfinance statement DataFrame, or None series."""
    if df is None or getattr(df, "empty", True):
        return None
    for n in names:
        if n in df.index:
            return df.loc[n]
    return None


def _at(series, col):
    if series is None:
        return None
    try:
        return _num(series.get(col))
    except Exception:
        return None


def _safe_div(a, b):
    a, b = _num(a), _num(b)
    if a is None or b in (None, 0):
        return None
    return a / b


def _retry_df(getter, tries: int = 4, delay: float = 1.2):
    """
    yfinance statement endpoints intermittently return an empty frame under
    rapid sequential access. Retry until a non-empty frame comes back.
    """
    last = None
    for i in range(tries):
        try:
            df = getter()
        except Exception:
            df = None
        last = df
        if df is not None and not getattr(df, "empty", True):
            return df
        time.sleep(delay * (i + 1))
    return last


# ── per-period metric computation ─────────────────────────────────────────────
def _period_metrics(col, income, balance, cashflow, price=None) -> dict:
    """Compute the metric set for one statement column (a fiscal period)."""
    net_income = _at(_row(income, "Net Income", "Net Income Common Stockholders"), col)
    ebit       = _at(_row(income, "EBIT", "Operating Income"), col)
    pretax     = _at(_row(income, "Pretax Income"), col)
    tax        = _at(_row(income, "Tax Provision"), col)
    diluted_eps = _at(_row(income, "Diluted EPS", "Basic EPS"), col)
    interest   = _at(_row(income, "Interest Expense", "Interest Expense Non Operating"), col)
    shares     = (_at(_row(income, "Diluted Average Shares", "Basic Average Shares"), col)
                  or _at(_row(balance, "Ordinary Shares Number", "Share Issued"), col))

    equity     = _at(_row(balance, "Stockholders Equity", "Common Stock Equity"), col)
    assets     = _at(_row(balance, "Total Assets"), col)
    debt       = _at(_row(balance, "Total Debt"), col)
    invested   = _at(_row(balance, "Invested Capital"), col)

    revenue    = _at(_row(income, "Total Revenue", "Operating Revenue"), col)

    ocf        = _at(_row(cashflow, "Operating Cash Flow", "Cash Flow From Continuing Operating Activities"), col)
    capex      = _at(_row(cashflow, "Capital Expenditure"), col)
    fcf        = _at(_row(cashflow, "Free Cash Flow"), col)
    if fcf is None and ocf is not None and capex is not None:
        fcf = ocf + capex          # capex is reported negative

    # tax rate (clamped to a sane band)
    tax_rate = _safe_div(tax, pretax)
    if tax_rate is not None:
        tax_rate = max(0.0, min(tax_rate, 0.5))

    nopat = None
    if ebit is not None and tax_rate is not None:
        nopat = ebit * (1.0 - tax_rate)

    if invested is None and equity is not None and debt is not None:
        invested = equity + debt

    # unlevered FCF = FCF + after-tax interest expense
    ufcf = None
    if fcf is not None:
        add = (interest * (1.0 - (tax_rate or 0.0))) if interest is not None else 0.0
        ufcf = fcf + add

    return {
        "roe":         _safe_div(net_income, equity),
        "roic":        _safe_div(nopat, invested),
        "eps":         diluted_eps,
        "pe":          _safe_div(price, diluted_eps) if price is not None else None,
        "book_value":  _safe_div(equity, shares),
        "fcf_ps":      _safe_div(fcf, shares),
        "ufcf_ps":     _safe_div(ufcf, shares),
        "lfcf_margin": _safe_div(fcf, revenue),     # levered FCF / revenue
        "ufcf_margin": _safe_div(ufcf, revenue),    # unlevered FCF / revenue
        "debt_equity": _safe_div(debt, equity),
        "debt_assets": _safe_div(debt, assets),
    }


_METRIC_KEYS = ["roe", "roic", "ufcf_ps", "fcf_ps", "lfcf_margin", "ufcf_margin",
                "pe", "eps", "book_value", "debt_equity", "debt_assets"]


def _year_end_price(hist, year_ts) -> Optional[float]:
    """Closest close on/before a fiscal period end date."""
    if hist is None or getattr(hist, "empty", True):
        return None
    try:
        import pandas as pd  # noqa
        cutoff = year_ts
        sub = hist.loc[:cutoff]
        if len(sub):
            return _num(sub["Close"].iloc[-1])
        return _num(hist["Close"].iloc[0])
    except Exception:
        return None


def _avg(vals) -> Optional[float]:
    nums = [v for v in vals if v is not None]
    if not nums:
        return None
    return sum(nums) / len(nums)


def _epoch_to_iso(ts) -> Optional[str]:
    """Yahoo epoch-seconds (or datetime/Timestamp) → ISO date string, or None."""
    if ts is None:
        return None
    try:
        # numeric epoch seconds
        if isinstance(ts, (int, float)) and not isinstance(ts, bool):
            return datetime.fromtimestamp(float(ts), tz=timezone.utc).date().isoformat()
        # pandas Timestamp / datetime
        if hasattr(ts, "isoformat"):
            return str(ts)[:10]
    except (ValueError, OverflowError, OSError):
        return None
    return None


def fetch_fundamentals(ticker: str) -> dict:
    """
    Fetch + compute the full valuation record for one stock.
    Returns {"ticker","name","price","currency","current","annual","quarterly",
             "years","averages","as_of","error"} — error set on failure.
    """
    rec: dict = {"ticker": ticker, "name": ticker, "error": None}
    try:
        t = yf.Ticker(ticker)
        info = {}
        try:
            info = t.info or {}
        except Exception:
            info = {}

        rec["name"] = info.get("shortName") or info.get("longName") or ticker
        rec["currency"] = info.get("financialCurrency") or info.get("currency") or "USD"
        rec["price_currency"] = info.get("currency") or "USD"  # marketCap/price denom
        rec["market_cap"] = _num(info.get("marketCap"))
        price = _num(info.get("currentPrice")) or _num(info.get("regularMarketPrice"))

        # Earnings-cycle tracking so /value can detect when a fresh report lands.
        # fetched_at      = when THIS record was pulled (staleness reference point);
        # most_recent_quarter = period end of the last statement we have;
        # next_earnings   = Yahoo's earnings date — note this flips to the *last*
        #                   report once a company reports, so staleness is judged as
        #                   "an earnings date falls between fetched_at and today".
        rec["fetched_at"] = datetime.now(timezone.utc).date().isoformat()
        rec["most_recent_quarter"] = _epoch_to_iso(info.get("mostRecentQuarter"))
        rec["next_earnings"] = _epoch_to_iso(
            info.get("earningsTimestamp")
            or info.get("earningsTimestampStart")
        )

        income = _retry_df(lambda: t.financials)
        balance = _retry_df(lambda: t.balance_sheet)
        cashflow = _retry_df(lambda: t.cashflow)
        q_income = _retry_df(lambda: t.quarterly_financials, tries=2)
        q_balance = _retry_df(lambda: t.quarterly_balance_sheet, tries=2)
        q_cashflow = _retry_df(lambda: t.quarterly_cashflow, tries=2)

        try:
            hist = t.history(period="11y", interval="1mo", auto_adjust=False)
            # statement dates are tz-naive; drop tz so date slicing aligns
            if hist is not None and not getattr(hist, "empty", True):
                try:
                    hist.index = hist.index.tz_localize(None)
                except (TypeError, AttributeError):
                    pass
        except Exception:
            hist = None
        if price is None and hist is not None and not getattr(hist, "empty", True):
            price = _num(hist["Close"].iloc[-1])
        rec["price"] = price

        # current snapshot — prefer live .info ratios, fall back to latest annual
        current = {
            "roe":         _num(info.get("returnOnEquity")),
            "roic":        None,
            "eps":         _num(info.get("trailingEps")),
            "pe":          _num(info.get("trailingPE")),
            "book_value":  _num(info.get("bookValue")),
            "fcf_ps":      None,
            "ufcf_ps":     None,
            "debt_equity": (_num(info.get("debtToEquity")) / 100.0
                            if _num(info.get("debtToEquity")) is not None else None),
            "debt_assets": None,
        }

        # annual history
        annual: dict[str, dict] = {}
        years: list[str] = []
        if income is not None and not getattr(income, "empty", True):
            for col in income.columns:
                yr = str(getattr(col, "year", str(col))[:4]) if not hasattr(col, "year") else str(col.year)
                px = _year_end_price(hist, col)
                m = _period_metrics(col, income, balance, cashflow, price=px)
                annual[yr] = m
                years.append(yr)

        # fill current gaps from most recent annual
        if years:
            latest = annual[years[0]]
            for k in _METRIC_KEYS:
                if current.get(k) is None and latest.get(k) is not None:
                    current[k] = latest[k]

        # quarterly history (most recent up to 6)
        quarterly: dict[str, dict] = {}
        if q_income is not None and not getattr(q_income, "empty", True):
            for col in list(q_income.columns)[:6]:
                try:
                    label = f"{col.year}Q{((col.month - 1) // 3) + 1}"
                except Exception:
                    label = str(col)[:10]
                px = _year_end_price(hist, col)
                quarterly[label] = _period_metrics(col, q_income, q_balance, q_cashflow, price=px)

        # averages over available annual window
        averages = {k: _avg([annual[y].get(k) for y in years]) for k in _METRIC_KEYS} if years else {}

        # point-in-time snapshots: N years ago (None when outside available window)
        def _years_ago(n: int) -> Optional[dict]:
            if n < len(years):
                return annual[years[n]]
            return None

        as_of = {
            "2yr": _years_ago(2),
            "5yr": _years_ago(5),
            "7yr": _years_ago(7),
            "10yr": _years_ago(10),
        }

        rec.update({
            "current": current,
            "annual": annual,
            "quarterly": quarterly,
            "years": years,
            "averages": averages,
            "as_of": as_of,
        })
        # Normalise market cap to USD so ranking is apples-to-apples across
        # KRW (005930.KS, 000660.KS) / TWD (TSM) / USD listings.
        mc = rec.get("market_cap")
        if mc is not None:
            rec["market_cap_usd"] = mc * _usd_rate(rec.get("price_currency") or "USD")

        if not years and current.get("pe") is None and current.get("roe") is None:
            rec["error"] = "no fundamental data returned"
        return rec
    except Exception as exc:  # noqa
        rec["error"] = str(exc)
        return rec


_FX_CACHE: dict[str, float] = {"USD": 1.0}


def _usd_rate(currency: str) -> float:
    """How many USD per 1 unit of `currency` (e.g. KRW→~0.00073). 1.0 on failure."""
    ccy = (currency or "USD").upper()
    if ccy in _FX_CACHE:
        return _FX_CACHE[ccy]
    rate = 1.0
    try:
        h = yf.Ticker(f"{ccy}USD=X").history(period="5d")
        if h is not None and not getattr(h, "empty", True):
            r = _num(h["Close"].dropna().iloc[-1])
            if r and r > 0:
                rate = r
    except Exception:
        rate = 1.0
    _FX_CACHE[ccy] = rate
    return rate


def fetch_all(tickers: Optional[list[str]] = None) -> dict:
    """Fetch fundamentals for the stock universe; returns a snapshot dict."""
    tickers = tickers or stock_universe()
    stocks = {}
    for t in tickers:
        stocks[t] = fetch_fundamentals(t)   # market_cap_usd normalised inside
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "yfinance",
        "universe": tickers,
        "stocks": stocks,
    }
