"""
Ticker/symbol normalization helpers.

The frontend uses "display tickers" (e.g., `CNX1`), but Yahoo Finance (yfinance)
often requires an exchange suffix (e.g., `CNX1.L` for London Stock Exchange).
"""

from __future__ import annotations

import re


_YAHOO_ALIASES: dict[str, str] = {
    # Indices
    "SPX": "^SPX",
    "NDX": "^NDX",
    "VIX": "^VIX",
    "RUT": "^RUT",
    "DJI": "^DJI",
    "GDAXI": "^GDAXI",
    "FTSE": "^FTSE",
    # London Stock Exchange (Yahoo suffix: .L)
    "CNX1": "CNX1.L",
    "CSP1": "CSP1.L",
    "IGLS": "IGLS.L",
    # Crypto
    "BTCUSD": "BTC-USD",
    # Currency Pairs (FX)
    "USDGBP": "USDGBP=X",
    # Treasury Yields
    "US10": "^TNX",
}


def resolve_yahoo_symbol(symbol: str) -> str:
    """
    Convert a user/display ticker into the correct Yahoo Finance symbol.

    Examples:
      - CNX1 -> CNX1.L
      - LON:CNX1 -> CNX1.L
      - CNX1.L -> CNX1.L
    """
    if not symbol:
        return symbol

    raw = symbol.strip()
    if not raw:
        return raw

    sym = raw.upper()

    # TradingView-style exchange prefixes.
    if ":" in sym:
        prefix, rest = sym.split(":", 1)
        if prefix in {"LON", "LSE"} and rest:
            base = rest.strip().upper()
            return base if base.endswith(".L") else f"{base}.L"

    # Common share-class tickers are written with a dot (e.g., BRK.B) but Yahoo
    # expects a dash (e.g., BRK-B). Keep this narrowly-scoped to avoid
    # interfering with exchange suffixes like `.L`, `.F`, etc.
    if re.fullmatch(r"[A-Z0-9]+\.[ABC]", sym):
        sym = sym.replace(".", "-", 1)

    return _YAHOO_ALIASES.get(sym, sym)
