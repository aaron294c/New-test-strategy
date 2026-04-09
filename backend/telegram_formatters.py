"""
Telegram Message Formatters — table-first design for easy vertical scanning.

format_macro_dashboard(macro_data)           → HTML string
format_mean_reversion(swing_data, macro_data) → HTML string
format_momentum(swing_data, macro_data)       → HTML string

All return HTML (Telegram parse_mode=HTML).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from macro_instruments import MACRO_INSTRUMENTS, CATEGORY_ORDER, CATEGORY_HEADERS

_SNAPSHOT_PATH = Path(__file__).parent / "static_snapshots" / "swing_framework" / "current-state-enriched.json"

# Empirical P85/P95 of |daily_pct[t] - daily_pct[t-1]| (~948 days per ticker)
_P85_2ND = {
    'AAPL': 25.10, 'MSFT': 26.69, 'NVDA': 25.90, 'GOOGL': 27.09,
    'TSLA': 23.90, 'NFLX': 25.10, 'AMZN': 27.49, 'BRK-B': 25.10,
    'AVGO': 27.09, 'SPY': 28.27, 'QQQ': 28.29, 'CNX1': 25.10,
    'CSP1': 26.69, 'BTCUSD': 25.48, 'ES1': 27.49, 'NQ1': 28.29,
    'VIX': 30.74, 'IGLS': 25.90, 'XOM': 27.49, 'CVX': 26.29,
    'OXY': 27.49, 'JPM': 23.51, 'BAC': 23.11, 'LLY': 24.70,
    'UNH': 23.51, 'TSM': 27.09, 'WMT': 23.90, 'COST': 25.10,
    'GLD': 25.90, 'SLV': 25.90, 'USDGBP': 26.69, 'US10': 26.75,
}
_P95_2ND = {
    'AAPL': 37.85, 'MSFT': 41.04, 'NVDA': 36.91, 'GOOGL': 38.65,
    'TSLA': 35.06, 'NFLX': 37.05, 'AMZN': 42.89, 'BRK-B': 37.45,
    'AVGO': 40.50, 'SPY': 36.65, 'QQQ': 39.30, 'CNX1': 36.65,
    'CSP1': 41.43, 'BTCUSD': 37.85, 'ES1': 37.47, 'NQ1': 39.04,
    'VIX': 42.23, 'IGLS': 37.71, 'XOM': 38.90, 'CVX': 38.25,
    'OXY': 42.63, 'JPM': 35.32, 'BAC': 37.31, 'LLY': 37.31,
    'UNH': 35.86, 'TSM': 39.96, 'WMT': 34.92, 'COST': 36.12,
    'GLD': 38.11, 'SLV': 37.17, 'USDGBP': 40.20, 'US10': 35.48,
}


def _enrich_second_order(rows: list[dict]) -> list[dict]:
    """Compute second-order divergence fields on a raw snapshot row list.

    The static snapshot has prev_midday_percentile baked in but second_order_*
    fields are never persisted, so we compute them fresh each time we load.
    """
    for row in rows:
        ticker   = row.get("ticker", "")
        cur_pct  = row.get("current_percentile")
        prev_pct = row.get("prev_midday_percentile")

        if cur_pct is None or prev_pct is None:
            row.setdefault("second_order_divergence_pct", None)
            row.setdefault("abs_second_order_divergence_pct", None)
            row.setdefault("second_order_dislocation_level", None)
            row.setdefault("second_order_dislocation_color", None)
            row.setdefault("second_order_p85_threshold", None)
            row.setdefault("second_order_p95_threshold", None)
            row.setdefault("second_order_thresholds_text", None)
            continue

        try:
            d2  = float(cur_pct) - float(prev_pct)
            ad2 = abs(d2)
        except (TypeError, ValueError):
            continue

        p85 = _P85_2ND.get(ticker, 26.0)
        p95 = _P95_2ND.get(ticker, 38.0)

        if ad2 <= p85:
            lvl, col = "Normal", "○"
        elif ad2 <= p95:
            lvl, col = "Significant (P85)", "⚠️"
        else:
            lvl, col = "Extreme (P95)", "⚡"

        row["second_order_divergence_pct"]     = d2
        row["abs_second_order_divergence_pct"] = ad2
        row["second_order_dislocation_level"]  = lvl
        row["second_order_dislocation_color"]  = col
        row["second_order_p85_threshold"]      = p85
        row["second_order_p95_threshold"]      = p95
        row["second_order_thresholds_text"]    = f"{p85:.1f}% | {p95:.1f}%"
    return rows


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_swing_snapshot() -> list[dict]:
    try:
        if not _SNAPSHOT_PATH.exists():
            return []
        with open(_SNAPSHOT_PATH) as f:
            data = json.load(f)
        rows = data.get("market_state", [])
        return _enrich_second_order(rows)
    except Exception as exc:
        print(f"[formatter] snapshot load error: {exc}")
        return []


def _pct_emoji(pct: Optional[float]) -> str:
    if pct is None: return ""
    if pct <= 5:    return "⚡"
    if pct <= 15:   return "🔵"
    if pct <= 20:   return "🟡"
    if pct >= 95:   return "💥"
    if pct >= 85:   return "🔴"
    return ""


def _zone_char(pct: Optional[float]) -> str:
    """Single-char zone indicator for table columns (no emoji width issues)."""
    if pct is None: return " "
    if pct <= 5:    return "!"
    if pct <= 15:   return "*"
    if pct <= 35:   return "."
    if pct >= 95:   return "X"
    if pct >= 85:   return "^"
    return " "


def _trend_arrow(label: Optional[str]) -> str:
    if not label:            return " → "
    t = label.upper()
    if "ACC" in t:   return " ↗↗"
    if "STR" in t:   return " ↗ "
    if "CRASH" in t: return " ↘↘"
    if "DECEL" in t: return " ↘ "
    if "FLAT" in t:  return " → "
    return " → "


def _fire(mv: Optional[float]) -> str:
    return "🔥" if mv is not None and abs(mv) >= 100 else "  "


def _fmt_price(price: Optional[float], unit: str) -> str:
    if price is None: return "—"
    if unit == "yield":   return f"{price:.2f}%"
    if unit == "fx":      return f"{price:.4f}"
    if unit == "index":   return f"{price:.2f}"
    if abs(price) >= 10000: return f"{price:,.0f}"
    if abs(price) >= 100:   return f"{price:.2f}"
    return f"{price:.3f}"


def _fmt_chg(chg: Optional[float]) -> str:
    if chg is None: return "    "
    return f"{chg:+.1f}%"


def _now_uk() -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%a %d %b %Y  %H:%M UTC")


def _wr_str(wr: Optional[float]) -> str:
    if wr is None: return " — "
    return f"{wr*100:.0f}%"


def _er_str(er: Optional[float]) -> str:
    if er is None: return "  — "
    return f"{er:+.1f}%"


def _rar_str(ra: Optional[float]) -> str:
    if ra is None: return "  — "
    return f"{ra:+.1f}%"


def _mv_str(mv: Optional[float]) -> str:
    if mv is None: return "    —"
    return f"{mv:+.0f}"


def _pct_str(p: Optional[float], width: int = 5) -> str:
    if p is None: return " —".rjust(width)
    return f"{p:.1f}%".rjust(width)


# ---------------------------------------------------------------------------
# Message 1 — Macro Dashboard
# ---------------------------------------------------------------------------

def format_macro_dashboard(macro_data: dict[str, dict]) -> str:
    lines: list[str] = []
    lines.append(f"<b>📊 MACRO DASHBOARD</b>")
    lines.append(f"<i>{_now_uk()}</i>")
    lines.append("")

    by_cat: dict[str, list[str]] = {c: [] for c in CATEGORY_ORDER}

    for key, cfg in MACRO_INSTRUMENTS.items():
        cat  = cfg["category"]
        d    = macro_data.get(key, {})
        if not d or (d.get("error") and d.get("price") is None):
            continue

        name    = cfg["name"]
        unit    = cfg.get("unit", "price")
        price_s = _fmt_price(d.get("price"), unit)
        pct     = d.get("percentile")
        pct_s   = f"{pct:.1f}%" if pct is not None else "—%"
        emoji   = _pct_emoji(pct)
        arrow   = _trend_arrow(d.get("trend_label")).strip()
        rsi_s   = f"{d['rsi_ma']:.1f}" if d.get("rsi_ma") is not None else "—"

        if unit == "yield":
            line = f"  {emoji} <b>{name:<14}</b> {price_s:>8}   RSI:{rsi_s:>5}  <code>P:{pct_s}</code>  {arrow}"
        else:
            chg_s = _fmt_chg(d.get("price_chg_pct"))
            line  = f"  {emoji} <b>{name:<14}</b> {price_s:>9}  {chg_s:>7}  RSI:{rsi_s:>5}  <code>P:{pct_s}</code>  {arrow}"

        by_cat.setdefault(cat, []).append(line)

    # Yield curve spread
    us10y = macro_data.get("US10Y", {}).get("price")
    us3m  = macro_data.get("US3M",  {}).get("price")
    spread_note = ""
    if us10y and us3m:
        sp   = us10y - us3m
        flag = "  ⚠ INVERTED" if sp < 0 else ""
        spread_note = f"  <i>10Y–3M Spread: {sp:+.2f}%{flag}</i>"

    for cat in CATEGORY_ORDER:
        rows = by_cat.get(cat, [])
        if not rows:
            continue
        lines.append(f"<b>{CATEGORY_HEADERS[cat]}</b>")
        lines.extend(rows)
        if cat == "TREASURY" and spread_note:
            lines.append(spread_note)
        lines.append("")

    # Ranked percentile table
    ranked = sorted(
        [(k, d) for k, d in macro_data.items() if d.get("percentile") is not None],
        key=lambda x: x[1]["percentile"],
    )
    lines.append("<b>── PERCENTILE RANKING (low → high) ──────────</b>")
    lines.append("<pre>")
    lines.append(f"{'Name':<16}  {'P%':>6}  {'RSI':>5}  {'Δ1d':>5}")
    lines.append("─" * 37)
    for key, d in ranked:
        name    = MACRO_INSTRUMENTS.get(key, {}).get("name", key)
        pct     = d.get("percentile", 0)
        rsi     = d.get("rsi_ma")
        rsi_p   = d.get("rsi_ma_prev")
        rsi_s   = f"{rsi:.1f}" if rsi is not None else "  —"
        d1_s    = f"{(rsi-rsi_p):+.1f}" if rsi is not None and rsi_p is not None else "  —"
        z       = _zone_char(pct)
        lines.append(f"{name:<16}  {pct:>5.1f}%{z}  {rsi_s:>5}  {d1_s:>5}")
    lines.append("</pre>")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Message 2 — Mean Reversion (stocks only, table format)
#
# Main row columns (each ticker):
#   Ticker | Daily% | 4H% | MACD-V | Direction | Win Rate | Exp Return
#
# Detail row (indent, each ticker):
#   Daily vs 4H divergence | Days in zone | Risk-adj return | Price change
# ---------------------------------------------------------------------------

_MR_HDR = f"{'Ticker':<7} {'Daily%':>7} {'4H%':>6} {'MACD-V':>7} {'Dir':<3}"
_MR_SEP = "─" * 35


def _mr_row(row: dict) -> str:
    ticker = row.get("ticker", "?")
    pct    = row.get("current_percentile", 0)
    four_h = row.get("four_h_percentile")
    macdv  = row.get("macdv_daily")
    trend  = row.get("macdv_trend_label", "")

    fh_s  = f"{four_h:.1f}%" if four_h is not None else "  —"
    mv_s  = f"{macdv:+.1f}" if macdv is not None else "  —"
    dir_s = _trend_arrow(trend).strip()

    return f"{ticker:<7} {pct:>6.1f}% {fh_s:>6} {mv_s:>7} {dir_s:<3}"


def _mr_detail(row: dict) -> str:
    """Indented second line: D-4H | D2nd | WR | ER | PriceChg."""
    pct    = row.get("current_percentile")
    four_h = row.get("four_h_percentile")
    le     = row.get("live_expectancy") or {}
    wr     = le.get("expected_win_rate")
    er     = le.get("expected_return_pct")
    chg    = row.get("price_change_pct")

    # First-order: Daily vs 4H
    if pct is not None and four_h is not None:
        div_s = f"D-4H:{pct - four_h:+.0f}pp"
    else:
        div_s = ""

    # Second-order: Daily Today vs Daily Yesterday
    d2 = row.get("second_order_divergence_pct")
    d2_lvl = row.get("second_order_dislocation_level") or ""
    if d2 is not None:
        icon = "⚡" if "Extreme" in d2_lvl else ("⚠" if "Significant" in d2_lvl else "")
        d2_s = f"D2nd:{d2:+.0f}pp{icon}"
    else:
        d2_s = ""

    wr_s  = f"WR:{wr*100:.0f}%" if wr is not None else ""
    er_s  = f"ER:{er:+.1f}%" if er is not None else ""
    chg_s = f"Chg:{chg:+.1f}%" if chg is not None else ""

    parts = [p for p in [div_s, d2_s, wr_s, er_s, chg_s] if p]
    return ("  " + "  ".join(parts)) if parts else ""


def format_mean_reversion(
    swing_data: Optional[list[dict]],
    macro_data: dict[str, dict],
    percentile_threshold: float = 35.0,
) -> str:
    if swing_data is None:
        swing_data = _load_swing_snapshot()

    lines: list[str] = []
    lines.append("<b>🔁 MEAN REVERSION</b>")
    lines.append(f"<i>{_now_uk()}  |  ≤{percentile_threshold:.0f}th percentile or dislocation</i>")
    lines.append("")
    extreme, low, moderate, disloc = [], [], [], []
    for row in swing_data:
        pct = row.get("current_percentile")
        if pct is None:
            continue
        abs_div = row.get("abs_divergence_pct")
        p85     = row.get("p85_threshold")
        is_dis  = abs_div is not None and p85 is not None and abs_div > p85
        if pct <= 5:
            extreme.append(row)
        elif pct <= 15:
            low.append(row)
        elif pct <= percentile_threshold:
            moderate.append(row)
        elif is_dis:
            disloc.append(row)

    for lst in (extreme, low, moderate, disloc):
        lst.sort(key=lambda r: r.get("current_percentile", 999))

    def _block(title: str, rows: list[dict]) -> None:
        if not rows:
            return
        lines.append(f"<b>{title}</b>")
        lines.append("<pre>")
        lines.append(_MR_HDR)
        lines.append(_MR_SEP)
        for row in rows:
            lines.append(_mr_row(row))
            detail = _mr_detail(row)
            if detail.strip():
                lines.append(detail)
            lines.append("")   # blank line between tickers
        lines.append("</pre>")
        lines.append("")

    _block("⚡ EXTREME OVERSOLD  (≤5th percentile)", extreme)
    _block("🔵 DEEPLY OVERSOLD  (5–15th percentile)", low)
    _block("🟡 OVERSOLD  (15–35th percentile)", moderate)
    _block("⚠ SIGNIFICANT DISLOCATION", disloc)

    if not extreme and not low and not moderate and not disloc:
        lines.append("<i>No mean reversion signals at this time.</i>")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Message 3 — Momentum (stocks only, table format)
# ---------------------------------------------------------------------------
# Table columns:
#   Ticker   MV       Tr   D%    Δ1d   Δ5d   WR   ER%
#    6        7        3    5     5     5     4    5   = ~40 chars
# ---------------------------------------------------------------------------

_MOM_HDR = f"{'Ticker':<7} {'MACD-V':>7} {'Dir':<4} {'Daily%':>7}"
_MOM_SEP = "─" * 30


def _mom_row(row: dict, show_fire: bool = True) -> str:
    ticker = row.get("ticker", "?")
    macdv  = row.get("macdv_daily", 0)
    pct    = row.get("current_percentile", 0)
    trend  = row.get("macdv_trend_label", "")

    fire_s = "🔥" if show_fire and abs(macdv) >= 100 else "  "
    dir_s  = _trend_arrow(trend).strip()

    return f"{fire_s}{ticker:<5} {macdv:>+7.1f} {dir_s:<4} {pct:>6.1f}%"


def _mom_detail(row: dict) -> str:
    """Indented second line: Δ1d | Δ5d | WR | ER | PriceChg."""
    d1  = row.get("macdv_delta_1d")
    d5  = row.get("macdv_delta_5d")
    le  = row.get("live_expectancy") or {}
    wr  = le.get("expected_win_rate")
    er  = le.get("expected_return_pct")
    chg = row.get("price_change_pct")

    d1_s  = f"Δ1d:{d1:+.1f}" if d1 is not None else ""
    d5_s  = f"Δ5d:{d5:+.1f}" if d5 is not None else ""
    wr_s  = f"WR:{wr*100:.0f}%" if wr is not None else ""
    er_s  = f"ER:{er:+.1f}%" if er is not None else ""
    chg_s = f"Chg:{chg:+.1f}%" if chg is not None else ""

    parts = [p for p in [d1_s, d5_s, wr_s, er_s, chg_s] if p]
    return ("  " + "  ".join(parts)) if parts else ""


def format_momentum(
    swing_data: Optional[list[dict]],
    macro_data: dict[str, dict],
) -> str:
    if swing_data is None:
        swing_data = _load_swing_snapshot()

    lines: list[str] = []
    lines.append("<b>🚀 MOMENTUM</b>")
    lines.append(f"<i>{_now_uk()}</i>")
    lines.append("")
    hot, building, fading = [], [], []
    for row in swing_data:
        macdv = row.get("macdv_daily")
        if macdv is None:
            continue
        d1 = row.get("macdv_delta_1d")
        if abs(macdv) >= 100:
            hot.append(row)
        elif d1 is not None and d1 > 0:
            building.append(row)
        elif d1 is not None and d1 < 0:
            fading.append(row)

    hot.sort(key=lambda r: abs(r.get("macdv_daily", 0)), reverse=True)
    building.sort(key=lambda r: r.get("macdv_delta_1d", 0), reverse=True)
    fading.sort(key=lambda r: r.get("macdv_delta_1d", 0))

    # Section A — Very Hot
    if hot:
        lines.append(f"<b>🔥 VERY HOT  (|MACD-V| ≥ 100)</b>")
        lines.append("<pre>")
        lines.append(_MOM_HDR)
        lines.append(_MOM_SEP)
        for row in hot:
            lines.append(_mom_row(row, show_fire=True))
            why = _mom_detail(row)
            if why:
                lines.append(why)
        lines.append("</pre>")
        lines.append("")

    # Section B — Building
    if building:
        lines.append("<b>📈 BUILDING MOMENTUM</b>")
        lines.append("<pre>")
        lines.append(_MOM_HDR)
        lines.append(_MOM_SEP)
        for row in building[:10]:
            lines.append(_mom_row(row, show_fire=False))
            why = _mom_detail(row)
            if why:
                lines.append(why)
        lines.append("</pre>")
        lines.append("")

    # Section C — Fading
    if fading:
        lines.append("<b>📉 FADING MOMENTUM</b>")
        lines.append("<pre>")
        lines.append(_MOM_HDR)
        lines.append(_MOM_SEP)
        for row in fading[:8]:
            lines.append(_mom_row(row, show_fire=False))
            why = _mom_detail(row)
            if why:
                lines.append(why)
        lines.append("</pre>")
        lines.append("")

    # Section D — Sector ETF summary
    sector_keys  = [k for k in MACRO_INSTRUMENTS if MACRO_INSTRUMENTS[k]["category"] == "SECTOR"]
    hot_s  = [(k, macro_data[k]) for k in sector_keys if k in macro_data and (macro_data[k].get("percentile") or 0) >= 70]
    weak_s = [(k, macro_data[k]) for k in sector_keys if k in macro_data and (macro_data[k].get("percentile") or 100) <= 30]
    hot_s.sort(key=lambda x: x[1].get("percentile", 0), reverse=True)
    weak_s.sort(key=lambda x: x[1].get("percentile", 100))

    if hot_s or weak_s:
        lines.append("<b>🏭 SECTOR ETF SUMMARY</b>")
        lines.append("<pre>")
        lines.append(f"{'Sector':<14}  {'P%':>6}  {'RSI':>5}  {'Tr':>3}")
        lines.append("─" * 32)
        for k, d in hot_s:
            name  = MACRO_INSTRUMENTS[k]["name"]
            pct   = d.get("percentile", 0)
            rsi_s = f"{d['rsi_ma']:.1f}" if d.get("rsi_ma") else "—"
            tr_s  = _trend_arrow(d.get("trend_label")).strip()
            lines.append(f"🔴{name:<13}  {pct:>5.1f}%  {rsi_s:>5}  {tr_s}")
        for k, d in weak_s:
            name  = MACRO_INSTRUMENTS[k]["name"]
            pct   = d.get("percentile", 0)
            rsi_s = f"{d['rsi_ma']:.1f}" if d.get("rsi_ma") else "—"
            tr_s  = _trend_arrow(d.get("trend_label")).strip()
            lines.append(f"📉{name:<13}  {pct:>5.1f}%  {rsi_s:>5}  {tr_s}")
        lines.append("</pre>")
        lines.append("")

    if not hot and not building and not fading:
        lines.append("<i>No significant momentum signals at this time.</i>")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# /help — command reference
# ---------------------------------------------------------------------------

def get_help_message() -> str:
    return (
        "<b>📡 AVAILABLE COMMANDS</b>\n"
        "\n"
        "<b>/update</b>  —  Full snapshot: macro + mean reversion + momentum\n"
        "<b>/macro</b>   —  Macro dashboard (indices, bonds, FX, commodities)\n"
        "<b>/mr</b>      —  Mean reversion table (oversold stocks ≤35th %ile)\n"
        "<b>/momentum</b> — Momentum table (MACD-V leaders and laggards)\n"
        "<b>/divergence</b> — Divergence analysis: 1st-order (Daily vs 4H) and\n"
        "               2nd-order (Daily today vs Daily yesterday) signals\n"
        "<b>/guide</b>   —  Column reference and metric explanations\n"
        "<b>/help</b>    —  This message\n"
        "\n"
        "<i>Snapshots are also sent automatically each morning.</i>"
    )


# ---------------------------------------------------------------------------
# /guide — column reference (sent only on demand)
# ---------------------------------------------------------------------------

def get_guide_message() -> str:
    return (
        "<b>📖 COLUMN GUIDE</b>\n"
        "\n"
        "<b>Daily% / 4H%</b>\n"
        "  RSI-MA percentile rank on daily / 4-hour bars\n"
        "  Uses 252-bar rolling window (≈1 trading year)\n"
        "  0% = lowest level seen  ·  100% = highest seen\n"
        "  ≤5% ⚡ extreme oversold  ·  ≤15% 🔵 deeply oversold\n"
        "  ≥85% 🔴 overbought  ·  ≥95% 💥 extreme overbought\n"
        "\n"
        "<b>MACD-V</b>\n"
        "  MACD-Velocity: momentum strength indicator\n"
        "  Negative = selling pressure  ·  Positive = buying pressure\n"
        "  |MACD-V| ≥ 100 = very high momentum 🔥\n"
        "\n"
        "<b>Dir (Direction of MACD-V)</b>\n"
        "  ↗↗ = accelerating up (rising 5+ days consistently)\n"
        "  ↗  = building upward (rising 1–3 days)\n"
        "  →  = flat / no clear direction\n"
        "  ↘  = fading / slowing (falling 1–3 days)\n"
        "  ↘↘ = accelerating down (falling 5+ days consistently)\n"
        "\n"
        "<b>WR / ER</b>\n"
        "  WR = Win Rate: historical success rate at similar Daily% setups\n"
        "  ER = Expected Return over next 7 days (from backtests)\n"
        "\n"
        "<b>D-4H</b>\n"
        "  Daily% minus 4H% — daily/intraday divergence\n"
        "  Positive = daily more oversold than intraday (confirmed setup)\n"
        "  Negative = intraday oversold but daily not yet confirming\n"
        "\n"
        "<b>Chg</b>\n"
        "  Today's closing price change vs previous close\n"
        "\n"
        "<b>Δ1d / Δ5d</b>\n"
        "  Change in MACD-V over last 1 / 5 days\n"
        "  Rising = momentum building  ·  Falling = momentum fading\n"
        "\n"
        "<b>D-4H (First-order divergence)</b>\n"
        "  Daily% minus 4H% — cross-timeframe dislocation\n"
        "  Thresholds are empirical P85/P95 of |Daily−4H| per ticker\n"
        "  ⚠ Significant (P85) = structural mispricing, watch for reversion\n"
        "  ⚡ Extreme (P95) = rare setup, historically strong mean-reversion\n"
        "\n"
        "<b>D2nd (Second-order divergence)</b>\n"
        "  Today's Daily% minus yesterday's Daily% — regime change signal\n"
        "  Thresholds are empirical P85/P95 of |day-over-day Δ%| per ticker\n"
        "  Typical P85 ≈ 24–31pp  ·  Typical P95 ≈ 35–43pp\n"
        "  Large positive (+) = accelerating upward regime shift\n"
        "  Large negative (−) = sharp pullback / snapback from yesterday\n"
        "  ⚠ Significant (P85) = uncommon regime shift — watch direction\n"
        "  ⚡ Extreme (P95) = very rare — historically precedes continuation or snap\n"
        "\n"
        "Use /divergence to see all tickers ranked by both layers."
    )


# ---------------------------------------------------------------------------
# /divergence — first-order and second-order divergence signals
# ---------------------------------------------------------------------------

_DIV_HDR = f"{'Ticker':<7} {'D-4H':>6} {'Dis1':>12}  {'D2nd':>6} {'Dis2':>12}"
_DIV_SEP = "─" * 48


def _div_row(row: dict) -> str:
    ticker = row.get("ticker", "?")

    # First-order (Daily vs 4H)
    d1   = row.get("divergence_pct")
    lvl1 = row.get("dislocation_level") or "—"
    d1_s = f"{d1:+.0f}pp" if d1 is not None else "  —"
    l1_s = "⚡Ext" if "Extreme" in lvl1 else ("⚠Sig" if "Significant" in lvl1 else "Norm")

    # Second-order (Daily Today vs Daily Yesterday)
    d2   = row.get("second_order_divergence_pct")
    lvl2 = row.get("second_order_dislocation_level") or "—"
    d2_s = f"{d2:+.0f}pp" if d2 is not None else "  —"
    l2_s = "⚡Ext" if "Extreme" in lvl2 else ("⚠Sig" if "Significant" in lvl2 else "Norm")

    return f"{ticker:<7} {d1_s:>6} {l1_s:>12}  {d2_s:>6} {l2_s:>12}"


def format_divergence(
    swing_data: Optional[list[dict]],
    macro_data: dict[str, dict],
) -> str:
    """Format /divergence message: first-order (Daily vs 4H) and second-order (Daily Today vs Yesterday)."""
    if swing_data is None:
        swing_data = _load_swing_snapshot()

    lines: list[str] = []
    lines.append("<b>📐 DIVERGENCE ANALYSIS</b>")
    lines.append(f"<i>{_now_uk()}</i>")
    lines.append("")
    lines.append(
        "<i>1st order: Daily vs 4H (cross-timeframe dislocation)\n"
        "2nd order: Daily today vs Daily yesterday (regime shift)</i>"
    )
    lines.append("")

    # Filter: at least one significant dislocation in either order
    sig1, sig2, both = [], [], []
    for row in swing_data:
        lvl1 = row.get("dislocation_level") or ""
        lvl2 = row.get("second_order_dislocation_level") or ""
        is_sig1 = "Significant" in lvl1 or "Extreme" in lvl1
        is_sig2 = "Significant" in lvl2 or "Extreme" in lvl2
        if is_sig1 and is_sig2:
            both.append(row)
        elif is_sig1:
            sig1.append(row)
        elif is_sig2:
            sig2.append(row)

    def _sort_key(r: dict) -> float:
        a1 = r.get("abs_divergence_pct") or 0
        a2 = r.get("abs_second_order_divergence_pct") or 0
        return a1 + a2

    for lst in (both, sig1, sig2):
        lst.sort(key=_sort_key, reverse=True)

    def _block(title: str, rows: list[dict]) -> None:
        if not rows:
            return
        lines.append(f"<b>{title}</b>")
        lines.append("<pre>")
        lines.append(_DIV_HDR)
        lines.append(_DIV_SEP)
        for row in rows:
            lines.append(_div_row(row))
        lines.append("</pre>")
        lines.append("")

    _block("🔴 BOTH ORDERS DISLOCATED", both)
    _block("🟡 1ST ORDER ONLY  (Daily vs 4H)", sig1)
    _block("🔵 2ND ORDER ONLY  (Daily Today vs Yesterday)", sig2)

    if not both and not sig1 and not sig2:
        lines.append("<i>No significant divergence or dislocation signals at this time.</i>")

    return "\n".join(lines)
