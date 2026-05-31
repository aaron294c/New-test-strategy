#!/usr/bin/env python3
"""
Precompute the fundamentals/valuation snapshot for the /value Telegram command.

Writes backend/static_snapshots/fundamentals/value.json so /value responds
instantly without re-fetching ~34 stocks on every request.

Usage:
  python scripts/compute_value_snapshot.py
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
_backend = _root / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from fundamentals_value import fetch_fundamentals, stock_universe  # noqa: E402


def main() -> None:
    out_dir = _backend / "static_snapshots" / "fundamentals"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "value.json"

    universe = stock_universe()
    print(f"[value] Computing fundamentals for {len(universe)} stocks...")

    stocks = {}
    for i, ticker in enumerate(universe, 1):
        print(f"[value]   ({i}/{len(universe)}) {ticker} ...", flush=True)
        rec = fetch_fundamentals(ticker)
        if rec.get("error"):
            print(f"[value]       ! {ticker}: {rec['error']}")
        stocks[ticker] = rec
        time.sleep(0.6)   # be polite to Yahoo between tickers

    snapshot = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "yfinance",
        "universe": universe,
        "stocks": stocks,
    }
    out_path.write_text(json.dumps(snapshot, indent=2, default=str))
    ok = sum(1 for r in stocks.values() if not r.get("error"))
    print(f"[value] Wrote {out_path} — {ok}/{len(universe)} stocks OK.")


if __name__ == "__main__":
    main()
