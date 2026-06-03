"""
/value command — fundamentals / valuation for the individual-equity subset of
the swing universe.

  /value           → overview table (current key ratios, every stock)
  /value <TICKER>  → full card: current vs 2yr / 5yr / 7yr / 10yr ago + window
                     average, for ROE, ROIC, UFCF/sh, FCF/sh, P/E, EPS, Book/sh,
                     Debt/Equity, Debt/Assets, plus latest quarter + YoY change.

Data: precomputed snapshot at static_snapshots/fundamentals/value.json
(refresh with `python scripts/compute_value_snapshot.py`). A single /value
<TICKER> falls back to a live yfinance fetch if the ticker isn't in the snapshot.
See fundamentals_value.py for the source rationale and the ~5yr history limit.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fundamentals_value import fetch_fundamentals, fetch_all, stock_universe, is_stock

_SNAPSHOT = Path(__file__).resolve().parent / "static_snapshots" / "fundamentals" / "value.json"

# metric key → (label, kind)  kind: pct | ratio | cur
_METRICS = [
    ("roe",         "ROE",        "pct"),
    ("roic",        "ROIC",       "pct"),
    ("lfcf_margin", "LevFCF%",    "pct"),
    ("ufcf_margin", "UnlvFCF%",   "pct"),
    ("ufcf_ps",     "uFCF/sh",    "cur"),
    ("fcf_ps",      "FCF/sh",     "cur"),
    ("pe",          "P/E",        "ratio"),
    ("eps",         "EPS",        "cur"),
    ("book_value",  "Book/sh",    "cur"),
    ("debt_equity", "Debt/Eq",    "ratio"),
    ("debt_assets", "Debt/Ast",   "ratio"),
]


# ── formatting ────────────────────────────────────────────────────────────────
def _fmt(val, kind: str) -> str:
    if val is None:
        return "—"
    try:
        v = float(val)
    except (TypeError, ValueError):
        return "—"
    if kind == "pct":
        return f"{v * 100:.1f}%"
    if kind == "ratio":
        return f"{v:.2f}"
    if kind == "cur":
        return f"{v:.2f}"
    return f"{v:.2f}"


def _live_prices(tickers: list[str]) -> dict:
    """
    Fast batch fetch of current prices so P/E and other price-derived ratios
    reflect the live market on every /value call — even when the heavy
    statement data is served from the cached snapshot. Returns {ticker: price}.
    """
    out: dict[str, float] = {}
    if not tickers:
        return out
    try:
        import yfinance as yf
        data = yf.download(
            tickers, period="2d", interval="1d",
            auto_adjust=False, progress=False, group_by="ticker", threads=True,
        )
    except Exception:
        return out
    for t in tickers:
        try:
            if len(tickers) == 1:
                close = data["Close"]
            else:
                close = data[t]["Close"]
            px = float(close.dropna().iloc[-1])
            if px == px and px > 0:
                out[t] = px
        except Exception:
            continue
    return out


def _overlay_live_prices(snap: dict) -> dict:
    """
    Recompute current P/E from a fresh price for each cached stock, in place.
    P/E = live price / trailing EPS. Leaves history/averages untouched.
    """
    stocks = snap.get("stocks", {})
    prices = _live_prices(list(stocks.keys()))
    if not prices:
        return snap
    for tkr, rec in stocks.items():
        px = prices.get(tkr)
        if px is None:
            continue
        rec["price"] = px
        rec["price_live"] = True
        cur = rec.get("current") or {}
        eps = cur.get("eps")
        if eps not in (None, 0):
            try:
                cur["pe"] = px / float(eps)
            except (TypeError, ValueError, ZeroDivisionError):
                pass
        rec["current"] = cur
    snap["price_overlay_at"] = datetime.now(timezone.utc).isoformat()
    return snap


def _load_snapshot() -> dict | None:
    if not _SNAPSHOT.exists():
        return None
    try:
        return json.loads(_SNAPSHOT.read_text())
    except Exception:
        return None


def _save_snapshot(snap: dict) -> bool:
    """Persist a freshly-fetched snapshot so subsequent /value reads are instant."""
    try:
        _SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        _SNAPSHOT.write_text(json.dumps(snap, indent=2, default=str))
        return True
    except Exception:
        return False


def refresh_overview() -> list[str]:
    """Re-fetch fundamentals for the whole stock universe live, persist, render."""
    snap = fetch_all()
    _save_snapshot(snap)
    ok = sum(1 for s in snap.get("stocks", {}).values() if not s.get("error"))
    total = len(snap.get("stocks", {}))
    msgs = _overview(snap)
    msgs.append(f"✅ <b>/value</b> data refreshed live — {ok}/{total} stocks updated.")
    return msgs


def _resolve(arg: str, snap: dict | None) -> str | None:
    """Map a user argument to a universe ticker."""
    a = (arg or "").strip().upper()
    if not a:
        return None
    candidates = (snap or {}).get("stocks", {}).keys() if snap else stock_universe()
    cand = list(candidates)
    if a in cand:
        return a
    # try common variants
    for c in cand:
        if c.split(".")[0] == a or c.replace("-", "") == a.replace("-", ""):
            return c
    return a if is_stock(a) else None


# ── overview ──────────────────────────────────────────────────────────────────
def _overview(snap: dict) -> list[str]:
    stocks = snap.get("stocks", {})
    gen = snap.get("generated_at", "")[:10]
    cols = ["Ticker", "P/E", "ROE", "ROIC", "EPS", "D/E"]

    rows = []
    for tkr in sorted(stocks):
        rec = stocks[tkr]
        cur = rec.get("current", {}) or {}
        rows.append([
            tkr,
            _fmt(cur.get("pe"), "ratio"),
            _fmt(cur.get("roe"), "pct"),
            _fmt(cur.get("roic"), "pct"),
            _fmt(cur.get("eps"), "cur"),
            _fmt(cur.get("debt_equity"), "ratio"),
        ])

    widths = [max(len(cols[j]), *(len(r[j]) for r in rows)) for j in range(len(cols))]

    def fmt(cells):
        return cells[0].ljust(widths[0]) + "  " + "  ".join(
            cells[j].rjust(widths[j]) for j in range(1, len(cells))
        )

    head = fmt(cols)
    body = "\n".join(fmt(r) for r in rows)
    msg = (
        f"<b>💰 Value — current ratios</b>  <i>(as of {gen})</i>\n"
        f"<pre>{head}\n{'-' * len(head)}\n{body}</pre>\n"
        "<i>Full history per stock: <b>/value &lt;TICKER&gt;</b> "
        "(e.g. /value AAPL) — current vs 2/5/7/10yr + average.</i>"
    )
    return [msg]


# ── single-ticker card ────────────────────────────────────────────────────────
def _card(rec: dict) -> str:
    name = rec.get("name", rec.get("ticker"))
    tkr = rec.get("ticker")
    cur = rec.get("current", {}) or {}
    avg = rec.get("averages", {}) or {}
    as_of = rec.get("as_of", {}) or {}
    years = rec.get("years", []) or []
    price = rec.get("price")
    ccy = rec.get("currency", "USD")

    if rec.get("error") and not years and not any(cur.values()):
        return f"<b>{tkr}</b> — <i>no fundamental data ({rec['error']}).</i>"

    cols = ["Metric", "Now", "2y", "5y", "7y", "10y", "Avg"]
    snaps = [
        ("Now", cur),
        ("2y", as_of.get("2yr")),
        ("5y", as_of.get("5yr")),
        ("7y", as_of.get("7yr")),
        ("10y", as_of.get("10yr")),
        ("Avg", avg),
    ]

    rows = []
    for key, label, kind in _METRICS:
        cells = [label]
        for _, src in snaps:
            cells.append(_fmt((src or {}).get(key), kind))
        rows.append(cells)

    widths = [max(len(cols[j]), *(len(r[j]) for r in rows)) for j in range(len(cols))]

    def fmt(cells):
        return cells[0].ljust(widths[0]) + "  " + "  ".join(
            cells[j].rjust(widths[j]) for j in range(1, len(cells))
        )

    head = fmt(cols)
    body = "\n".join(fmt(r) for r in rows)

    # YoY change line (latest annual vs prior annual)
    chg = ""
    annual = rec.get("annual", {}) or {}
    if len(years) >= 2:
        y0, y1 = years[0], years[1]
        a0, a1 = annual.get(y0, {}), annual.get(y1, {})

        def _delta(k):
            v0, v1 = a0.get(k), a1.get(k)
            if v0 is None or v1 is None:
                return "—"
            return f"{(v0 - v1) * 100:+.1f}pp" if k in ("roe", "roic") else f"{v0 - v1:+.2f}"

        chg = (f"\n<i>YoY ({y1}→{y0}): ROE {_delta('roe')} · EPS {_delta('eps')} · "
               f"P/E {_delta('pe')}</i>")

    span = f"{years[-1]}–{years[0]}" if years else "n/a"
    px = f"{price:.2f} {ccy}" if price is not None else "n/a"
    hdr = (
        f"<b>💰 {name}</b> ({tkr})\n"
        f"Price {px}  ·  history {span} ({len(years)}y)\n"
    )
    note = (
        "\n<i>ROE/ROIC/LevFCF%/UnlvFCF% are %; LevFCF%=FCF÷revenue, "
        "UnlvFCF%=(FCF+after-tax interest)÷revenue. P/E, Debt/Eq, Debt/Ast are "
        "ratios; EPS, *FCF/sh, Book/sh per share. P/E uses live price. Avg = mean "
        "over available window. 7y/10y show — when Yahoo doesn't return that far back.</i>"
    )
    return f"{hdr}<pre>{head}\n{'-' * len(head)}\n{body}</pre>{chg}{note}"


# ── entrypoint ────────────────────────────────────────────────────────────────
def handle_value_command(arg: str = "") -> list[str]:
    arg = (arg or "").strip()
    arg_l = arg.lower()

    # /value refresh  → re-fetch the whole universe live and persist the snapshot
    if arg_l in ("refresh", "update", "rebuild", "fetch"):
        return refresh_overview()

    snap = _load_snapshot()

    # /value (no arg) → cached overview (fast). /value live → fetch all live.
    if not arg or arg_l == "live":
        if arg_l == "live":
            return refresh_overview()
        if not snap:
            # no snapshot yet — build it live this once
            return refresh_overview()
        # Overlay LIVE prices so P/E reflects the current market on every call;
        # fundamentals (EPS, ROE, ROIC, book, debt) come from the cached statements.
        snap = _overlay_live_prices(snap)
        gen = snap.get("generated_at", "")[:10]
        live = snap.get("price_overlay_at") is not None
        msgs = _overview(snap)
        tag = ("P/E uses <b>live prices</b>; fundamentals as of "
               f"{gen}." if live else f"Cached {gen}.")
        msgs[0] += (f"\n<i>{tag} <b>/value refresh</b> re-fetches all statements · "
                    "<b>/value &lt;TICKER&gt;</b> is fully live.</i>")
        return msgs

    # /value <TICKER> → ALWAYS fetch live (single ticker is fast)
    tkr = _resolve(arg, snap)
    if not tkr:
        return [f"❓ <b>{arg}</b> isn't an individual stock in the universe. "
                "Try /value for the list."]

    rec = fetch_fundamentals(tkr)
    if rec.get("error") and snap and tkr in snap.get("stocks", {}):
        # live fetch failed — fall back to cached card so the user still gets data
        card = _card(snap["stocks"][tkr])
        return [card + "\n<i>⚠️ live fetch failed; showing cached values.</i>"]
    return [_card(rec)]
