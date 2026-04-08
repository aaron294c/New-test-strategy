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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_swing_snapshot() -> list[dict]:
    try:
        if not _SNAPSHOT_PATH.exists():
            return []
        with open(_SNAPSHOT_PATH) as f:
            data = json.load(f)
        return data.get("market_state", [])
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
    """Indented second line: D-4H | WR | ER | PriceChg."""
    pct    = row.get("current_percentile")
    four_h = row.get("four_h_percentile")
    le     = row.get("live_expectancy") or {}
    wr     = le.get("expected_win_rate")
    er     = le.get("expected_return_pct")
    chg    = row.get("price_change_pct")

    # Compute D vs 4H live from current values
    if pct is not None and four_h is not None:
        div_s = f"D-4H:{pct - four_h:+.0f}pp"
    else:
        div_s = ""

    wr_s  = f"WR:{wr*100:.0f}%" if wr is not None else ""
    er_s  = f"ER:{er:+.1f}%" if er is not None else ""
    chg_s = f"Chg:{chg:+.1f}%" if chg is not None else ""

    parts = [p for p in [div_s, wr_s, er_s, chg_s] if p]
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
        "  Rising = momentum building  ·  Falling = momentum fading"
    )
