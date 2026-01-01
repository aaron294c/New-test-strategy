"""
Ticker/symbol normalization helpers.

The frontend uses "display tickers" (e.g., `CNX1`), but Yahoo Finance (yfinance)
often requires an exchange suffix (e.g., `CNX1.L` for London Stock Exchange).
"""

from __future__ import annotations


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
    "IGLS": "IGLS.L",
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

    return _YAHOO_ALIASES.get(sym, sym)

