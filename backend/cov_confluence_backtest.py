#!/usr/bin/env python3
"""
RSI-MA + CoV Confluence Backtest

For each ticker, compare two long-entry rule sets at the percentile<5 trigger:

  A. RSI-MA only          — every bar where percentile_rank(RSI-MA) <= threshold
  B. RSI-MA + CoV red     — A AND a red CoV bar (Fisher-z dir_metric <= -1.3)

Outputs:
  - backend/cache/{TICKER}_cov_confluence.json   (per-ticker side-by-side)
  - docs/cov_confluence_summary.md               (aggregate table across symbols)
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cov_indicator import compute_cov, red_bar_mask  # noqa: E402
from enhanced_backtester import EnhancedPerformanceMatrixBacktester  # noqa: E402
from macdv_calculator import SWING_FRAMEWORK_TICKERS  # noqa: E402


UNIVERSE: List[str] = list(SWING_FRAMEWORK_TICKERS)

THRESHOLD: float = 5.0
MIN_EVENTS: int = 10  # mirrors the floor at enhanced_backtester.py:843
CACHE_DIR = Path(__file__).resolve().parent / "cache"
DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"


def _winrate_at(events: List[Dict], day: int) -> Optional[float]:
    rets = [e["progression"][day]["cumulative_return_pct"]
            for e in events if day in e["progression"]]
    if not rets:
        return None
    return 100.0 * sum(1 for r in rets if r > 0) / len(rets)


def _median_at(events: List[Dict], day: int) -> Optional[float]:
    rets = [e["progression"][day]["cumulative_return_pct"]
            for e in events if day in e["progression"]]
    if not rets:
        return None
    return float(np.median(rets))


def _summarize_events(events: List[Dict]) -> Dict:
    if not events:
        return {
            "events": 0,
            "winrate_D5": None,
            "winrate_D10": None,
            "winrate_D21": None,
            "median_D5": None,
            "median_D10": None,
            "median_D21": None,
            "max_dd_p90": None,
            "median_dd": None,
        }
    drawdowns = [e["max_drawdown_pct"] for e in events]
    return {
        "events": len(events),
        "winrate_D5": _winrate_at(events, 5),
        "winrate_D10": _winrate_at(events, 10),
        "winrate_D21": _winrate_at(events, 21),
        "median_D5": _median_at(events, 5),
        "median_D10": _median_at(events, 10),
        "median_D21": _median_at(events, 21),
        "max_dd_p90": float(np.percentile(drawdowns, 90)),
        "median_dd": float(np.median(drawdowns)),
    }


def _fmt(value: Optional[float], spec: str = "{:+.2f}") -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    return spec.format(value)


def run_one(backtester: EnhancedPerformanceMatrixBacktester,
            ticker: str) -> Optional[Dict]:
    print(f"\n{'='*60}\n{ticker}\n{'='*60}")
    data = backtester.fetch_data(ticker)
    if data.empty or len(data) < backtester.lookback_period + 30:
        print(f"  insufficient data for {ticker} ({len(data)} bars) — skip")
        return None

    rsi_ma = backtester.calculate_rsi_ma_indicator(data)
    pct = backtester.calculate_percentile_ranks(rsi_ma)
    close = data["Close"]

    cov_df = compute_cov(close)
    red_mask = red_bar_mask(cov_df).reindex(pct.index, fill_value=False)

    events_a = backtester.find_entry_events_enhanced(pct, close, THRESHOLD)
    events_b = backtester.find_entry_events_enhanced(
        pct, close, THRESHOLD, confluence_mask=red_mask
    )

    summary_a = _summarize_events(events_a)
    summary_b = _summarize_events(events_b)

    status = "ok" if summary_b["events"] >= MIN_EVENTS else "insufficient_events"

    payload = {
        "ticker": ticker,
        "data_points": int(len(data)),
        "threshold": THRESHOLD,
        "cov_settings": {
            "cv_len": 5, "var_scale": 2.0, "ema_len": 5,
            "cc_lookback": 5, "corr_mode": "Fisher", "sig_thresh": 1.3,
        },
        "status": status,
        "rsi_ma_only": summary_a,
        "rsi_ma_plus_cov_red": summary_b,
        "red_bars_total": int(red_mask.sum()),
    }

    out_path = CACHE_DIR / f"{ticker}_cov_confluence.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"  wrote {out_path.name}  | A={summary_a['events']}  B={summary_b['events']}  ({status})")

    return payload


def write_summary(rows: List[Dict]) -> Path:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DOCS_DIR / "cov_confluence_summary.md"

    n_total = len(rows)
    n_pass = sum(1 for r in rows if r["status"] == "ok")
    n_fail = n_total - n_pass

    lines: List[str] = []
    lines.append("# RSI-MA + CoV Confluence Backtest")
    lines.append("")
    lines.append(f"- Universe size: **{n_total}**")
    lines.append(f"- Symbols with ≥{MIN_EVENTS} confluence events: **{n_pass}**")
    lines.append(f"- Symbols below event floor: **{n_fail}**")
    lines.append(f"- Entry trigger: RSI-MA percentile ≤ {THRESHOLD}%")
    lines.append("- Confluence (B): Fisher-z dir_metric ≤ −1.3 on the entry bar")
    lines.append("- A = RSI-MA only, B = RSI-MA + red CoV bar")
    lines.append("")
    lines.append("| symbol | events_A | events_B | wr_D5_A | wr_D5_B | wr_D21_A | wr_D21_B | med_D21_A | med_D21_B | medDD_A | medDD_B | status |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for r in rows:
        a = r["rsi_ma_only"]
        b = r["rsi_ma_plus_cov_red"]
        lines.append(
            "| {sym} | {ea} | {eb} | {wra5} | {wrb5} | {wra21} | {wrb21} | {ma21} | {mb21} | {dda} | {ddb} | {st} |".format(
                sym=r["ticker"],
                ea=a["events"], eb=b["events"],
                wra5=_fmt(a["winrate_D5"], "{:.1f}"),
                wrb5=_fmt(b["winrate_D5"], "{:.1f}"),
                wra21=_fmt(a["winrate_D21"], "{:.1f}"),
                wrb21=_fmt(b["winrate_D21"], "{:.1f}"),
                ma21=_fmt(a["median_D21"]),
                mb21=_fmt(b["median_D21"]),
                dda=_fmt(a["median_dd"]),
                ddb=_fmt(b["median_dd"]),
                st=r["status"],
            )
        )
    lines.append("")
    lines.append("Per-ticker JSON: `backend/cache/{TICKER}_cov_confluence.json`")
    out_path.write_text("\n".join(lines))
    print(f"\nWrote summary → {out_path}")
    return out_path


def main() -> None:
    backtester = EnhancedPerformanceMatrixBacktester(
        tickers=UNIVERSE,
        lookback_period=252,
        rsi_length=14,
        ma_length=14,
        max_horizon=21,
    )

    t0 = time.time()
    rows: List[Dict] = []
    for ticker in UNIVERSE:
        try:
            row = run_one(backtester, ticker)
            if row:
                rows.append(row)
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR on {ticker}: {e}")
            import traceback
            traceback.print_exc()

    write_summary(rows)
    print(f"\nDone in {time.time() - t0:.1f}s — {len(rows)} symbols completed")


if __name__ == "__main__":
    main()
