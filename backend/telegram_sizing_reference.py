"""
Telegram position sizing reference — /sizing command handler.

Data source: docs/SIGNAL_METRICS_REFERENCE.md  (single source of truth)

Sub-commands:
  /sizing          → index (how to use)
  /sizing a        → Signal A full table (5yr vs 9yr, all tickers)
  /sizing b        → Signal B full table
  /sizing rules    → position sizing rules & cap logic
  /sizing <ticker> → single-ticker deep-dive card  (e.g. /sizing tsla)
"""

from __future__ import annotations
import json
import re
from pathlib import Path

_here    = Path(__file__).resolve().parent
_MD_FILE = _here.parent / "docs" / "SIGNAL_METRICS_REFERENCE.md"
_J9      = _here / "cache" / "position_sizing_results.json"
_J5      = _here / "cache" / "position_sizing_5yr.json"

GUARDRAIL_MIN = 5.0
GUARDRAIL_MAX = 20.0
SINGLE_MAX    = 30.0
MIN_N         = 5

TICKER_NAMES = {
    'NQ=F':'NASDAQ Futures','ES=F':'S&P 500 Futures',
    'QQQ':'NASDAQ ETF','SPY':'S&P 500 ETF',
    'MSFT':'Microsoft','NVDA':'NVIDIA','GOOGL':'Google',
    'AAPL':'Apple','AVGO':'Broadcom','TSM':'Taiwan Semi',
    'META':'Meta','TSLA':'Tesla','AMZN':'Amazon',
    'LLY':'Eli Lilly','WMT':'Walmart','BRK-B':'Berkshire',
    'JPM':'JP Morgan','BAC':'Bank of America','NFLX':'Netflix',
    'ORCL':'Oracle','UNH':'UnitedHealth','GLD':'Gold ETF',
    'SLV':'Silver ETF','BTC-USD':'Bitcoin','SMH':'Semis ETF',
    'XLI':'Industrials','MCD':"McDonald's",'OXY':'Occidental',
    'XOM':'Exxon','CVX':'Chevron','ASML':'ASML',
    'SMCI':'Super Micro','^TNX':'10Y Yield','^VIX':'VIX',
    'DX-Y.NYB':'USD Index','^GDAXI':'DAX','^FTSE':'FTSE 100',
    '^N225':'Nikkei 225',
}

ALIASES: dict[str, str] = {
    'nasdaq':'NQ=F','nq':'NQ=F','nqf':'NQ=F',
    'sp500':'ES=F','esf':'ES=F','es':'ES=F','sp':'ES=F',
    'qqq':'QQQ','spy':'SPY',
    'msft':'MSFT','microsoft':'MSFT',
    'nvda':'NVDA','nvidia':'NVDA',
    'googl':'GOOGL','google':'GOOGL','goog':'GOOGL',
    'aapl':'AAPL','apple':'AAPL',
    'avgo':'AVGO','broadcom':'AVGO',
    'tsm':'TSM','taiwan':'TSM',
    'meta':'META','facebook':'META',
    'tsla':'TSLA','tesla':'TSLA',
    'amzn':'AMZN','amazon':'AMZN',
    'lly':'LLY','lilly':'LLY',
    'wmt':'WMT','walmart':'WMT',
    'brkb':'BRK-B','berkshire':'BRK-B',
    'jpm':'JPM','jpmorgan':'JPM',
    'bac':'BAC','bankofamerica':'BAC',
    'nflx':'NFLX','netflix':'NFLX',
    'orcl':'ORCL','oracle':'ORCL',
    'unh':'UNH',
    'gld':'GLD','gold':'GLD',
    'slv':'SLV','silver':'SLV',
    'btc':'BTC-USD','bitcoin':'BTC-USD',
    'smh':'SMH','xli':'XLI',
    'mcd':'MCD','mcdonalds':'MCD',
    'oxy':'OXY','xom':'XOM','exxon':'XOM',
    'cvx':'CVX','chevron':'CVX',
    'asml':'ASML','smci':'SMCI',
    'tnx':'^TNX','bonds':'^TNX','10y':'^TNX',
    'vix':'^VIX',
    'dxy':'DX-Y.NYB','dollar':'DX-Y.NYB',
    'dax':'^GDAXI','ftse':'^FTSE',
    'nikkei':'^N225','n225':'^N225',
}


# ── MD parser ────────────────────────────────────────────────────────────────

def _clean(s: str) -> str:
    return s.replace('**', '').replace('`', '').strip()


def _parse_md_section(section_header: str) -> list[dict]:
    """
    Parse one table section from the MD file.
    Returns list of row dicts keyed by column name.
    """
    if not _MD_FILE.exists():
        return []

    text = _MD_FILE.read_text()
    # Find the section
    idx = text.find(section_header)
    if idx == -1:
        return []

    rows: list[dict] = []
    in_table = False
    header_cells: list[str] = []

    for line in text[idx:].split('\n'):
        if not line.startswith('|'):
            if in_table and rows:
                break       # end of table
            continue
        cells = [_clean(c) for c in line.split('|')[1:-1]]
        # Skip separator rows
        if all(set(c) <= set('-:') for c in cells if c):
            continue
        if not header_cells:
            header_cells = [c.lower().replace(' ', '_') for c in cells]
            in_table = True
            continue
        if len(cells) == len(header_cells):
            rows.append(dict(zip(header_cells, cells)))

    return rows


def _get_tables() -> dict[str, list[dict]]:
    """Return parsed Signal A and Signal B table rows from the MD."""
    return {
        'a': _parse_md_section('## Signal A —'),
        'b': _parse_md_section('## Signal B —'),
    }


def _resolve_ticker(arg: str) -> str | None:
    """Map user input to canonical ticker symbol."""
    arg = arg.lower().strip().replace('-', '').replace('^', '').replace('=f', '')
    if arg in ALIASES:
        return ALIASES[arg]
    raw = arg.upper()
    for t in TICKER_NAMES:
        if t.upper().replace('^', '').replace('=f', '').replace('-', '') == raw:
            return t
    return None


# ── solo (uncapped) half-Kelly — computed from JSON, not in MD ───────────────

def _load_json() -> tuple[dict, dict]:
    r9 = json.loads(_J9.read_text()) if _J9.exists() else {}
    r5 = json.loads(_J5.read_text()) if _J5.exists() else {}
    return r9, r5


def _solo_size(ticker: str, bucket: str) -> str:
    """Return solo (uncapped, ≤30%) half-Kelly for a ticker from JSON cache."""
    r9, _ = _load_json()
    m = r9.get(ticker, {}).get(bucket, {}).get('cov_confluence', {})
    if not m or m.get('n', 0) < MIN_N:
        return '—'
    k  = m.get('kelly_binary')
    ev = m.get('ev_pct', 0) or 0
    if k is None or k <= 0 or ev <= 0:
        return '5%'
    raw = max(GUARDRAIL_MIN, k / 2.0)
    return f"{min(SINGLE_MAX, raw):.0f}%"


# ── Message builders ─────────────────────────────────────────────────────────

def msg_index() -> str:
    return (
        "<b>📐 POSITION SIZING REFERENCE</b>\n"
        "<i>RSI-MA + CoV Red Bar confluence · D5 hold · 5yr vs 9yr</i>\n"
        "\n"
        "<b>Commands:</b>\n"
        "  /sizing a        — Signal A table (all tickers)\n"
        "  /sizing b        — Signal B table (all tickers)\n"
        "  /sizing rules    — Sizing rules &amp; cap logic\n"
        "  /sizing &lt;ticker&gt; — Single ticker deep-dive\n"
        "\n"
        "<b>Examples:</b>\n"
        "  /sizing tsla  /sizing nq  /sizing avgo  /sizing lly\n"
        "\n"
        "<b>Signal definitions:</b>\n"
        "  <b>A</b> = RSI-MA &lt; 5th pct + CoV red bar  (ultra-low)\n"
        "  <b>B</b> = RSI-MA 5–15th pct + CoV red bar  (low)\n"
        "\n"
        "<b>Column guide:</b>\n"
        "  5yWin/9yWin  = D5 win rate %\n"
        "  EV           = net expected value per trade\n"
        "  ½K           = half-Kelly capped 20% (2–3 positions)\n"
        "  solo         = half-Kelly capped 30% (1 position only)\n"
        "  ★★★ ✗        = signal quality rating\n"
    )


def msg_rules() -> str:
    return (
        "<b>📏 POSITION SIZING RULES</b>\n"
        "\n"
        "<b>Positions open → which size to use:</b>\n"
        "<pre>"
        "Open  Column  Max total  Notes\n"
        "────  ──────  ─────────  ─────────────────────\n"
        "  1   solo      30%      Full math, uncapped\n"
        "  2   ½K        40%      Correlation discount\n"
        "  3   ½K        60%      Max gross exposure\n"
        "  —   floor      5%      No edge — do not size up"
        "</pre>\n"
        "\n"
        "<b>Why the 20% multi-position cap?</b>\n"
        "Signals fire on correlated assets simultaneously "
        "(TSLA, NQ=F, QQQ, MSFT all dip in the same selloff). "
        "3 positions at uncapped half-Kelly = ~79% gross exposure "
        "into one stress event. Cap limits this to 60% max.\n"
        "\n"
        "<b>Why 30% solo ceiling (not higher)?</b>\n"
        "Half-Kelly already discounts full Kelly by 50% for model "
        "uncertainty. 30% covers the estimation error range: if "
        "true win rate is 3–4pp below backtest, true half-Kelly "
        "still fits within 30%.\n"
        "\n"
        "<b>Tickers where solo &gt; 20% (Signal A, 9yr):</b>\n"
        "<pre>"
        "Ticker  Kelly   ½-K   mlt  solo\n"
        "──────  ──────  ────  ───  ────\n"
        "TSLA    58.1%  29.1%  20%   29%\n"
        "NQ=F    51.1%  25.6%  20%   26%\n"
        "MSFT    48.6%  24.3%  20%   24%\n"
        "ES=F    42.2%  21.1%  20%   21%\n"
        "LLY B   43.0%  21.5%  20%   22%"
        "</pre>\n"
        "\n"
        "<i>Kelly = binary Kelly = (p×b − q)/b\n"
        "where p=win%, q=1−p, b=avg_win/|avg_loss|\n"
        "EV = p×avg_win + q×avg_loss</i>"
    )


def msg_signal_table(signal: str) -> list[str]:
    """Build compact table messages for Signal A or B from the MD file."""
    tables = _get_tables()
    rows   = tables.get(signal.lower(), [])

    bucket = 'ultra_low' if signal.lower() == 'a' else 'low'
    sig_label   = 'A' if signal.lower() == 'a' else 'B'
    pct_label   = '&lt;5th pct' if signal.lower() == 'a' else '5–15th pct'

    header = (
        f"<b>📊 SIGNAL {sig_label} — {pct_label} + CoV Red</b>\n"
        f"<i>D5 · non-overlapping · 5yr vs 9yr</i>\n"
    )

    col_hdr  = f"{'Ticker':<10} {'5yWin':>5} {'5yEV':>7} {'5y½K':>5}  │ {'9yWin':>5} {'9yEV':>7} {'9y½K':>5} {'solo':>4}"
    divider  = "─" * len(col_hdr)

    lines: list[str] = []
    for r in rows:
        ticker = r.get('#', '') and r.get('ticker', r.get('#', ''))
        # The MD uses '# | ticker | name | ...' — find the ticker column
        # Try key names that might appear depending on MD structure
        ticker  = r.get('ticker', '')
        w5      = r.get('5yr_win%', '—')
        ev5     = r.get('5yr_ev',   '—')
        hk5     = r.get('5yr_½-kelly', '—')
        w9      = r.get('9yr_win%', '—')
        ev9     = r.get('9yr_ev',   '—')
        hk9     = r.get('9yr_½-kelly', '—')
        verdict = r.get('verdict', '')

        solo = _solo_size(ticker, bucket)
        lines.append(
            f"{ticker:<10} {w5:>5} {ev5:>7} {hk5:>5}  │ {w9:>5} {ev9:>7} {hk9:>5} {solo:>4}  {verdict}"
        )

    # Split into chunks of 15 rows per message
    chunk_size = 15
    messages: list[str] = []
    total_chunks = -(-len(lines) // chunk_size)
    for i in range(0, len(lines), chunk_size):
        chunk = lines[i:i + chunk_size]
        part  = f" ({i//chunk_size + 1}/{total_chunks})" if total_chunks > 1 else ""
        title = header if i == 0 else f"<b>Signal {sig_label} cont.{part}</b>\n"
        body  = "\n".join(chunk)
        messages.append(f"{title}<pre>{col_hdr}\n{divider}\n{body}</pre>")

    if not messages:
        messages = [f"{header}<i>No data found — ensure SIGNAL_METRICS_REFERENCE.md exists.</i>"]
    return messages


def msg_ticker(raw_arg: str) -> str:
    """Deep-dive card for a single ticker, sourced from MD + solo from JSON."""
    ticker = _resolve_ticker(raw_arg)
    if not ticker:
        return (
            f"<b>Unknown ticker:</b> <code>{raw_arg}</code>\n\n"
            "Try: /sizing tsla  /sizing nq  /sizing avgo  /sizing lly\n"
            "Or use /sizing a for the full Signal A table."
        )

    tables  = _get_tables()
    name    = TICKER_NAMES.get(ticker, ticker)
    lines   = [f"<b>🔍 {ticker} — {name}</b>"]

    for sig_key, sig_label, pct_label, bucket in [
        ('a', 'A', '&lt;5th pct + CoV red',  'ultra_low'),
        ('b', 'B', '5–15th pct + CoV red', 'low'),
    ]:
        rows = tables.get(sig_key, [])
        row  = next((r for r in rows if r.get('ticker', '').upper() == ticker.upper()), None)

        lines.append(f"\n<b>Signal {sig_label}</b>  <i>({pct_label})</i>")

        if not row:
            lines.append("  No data in reference file.")
        else:
            def g(r, *keys):
                for k in keys:
                    v = r.get(k)
                    if v and v != '—':
                        return v
                return '—'

            w5      = row.get('5yr_win%', '—')
            aw5     = row.get('5yr_avg_win', '—')
            al5     = row.get('5yr_avg_loss', '—')
            ev5     = row.get('5yr_ev', '—')
            hk5     = row.get('5yr_½-kelly', '—')
            n5      = row.get('5yr_n', '—')
            w9      = row.get('9yr_win%', '—')
            aw9     = row.get('9yr_avg_win', '—')
            al9     = row.get('9yr_avg_loss', '—')
            ev9     = row.get('9yr_ev', '—')
            hk9     = row.get('9yr_½-kelly', '—')
            n9      = row.get('9yr_n', '—')
            delta   = row.get('δ_½-kelly', '—')
            verdict = row.get('verdict', '')

            lines.append(f"  5yr: n={n5} · win={w5} · {aw5}/{al5} · EV={ev5} · ½K={hk5}")
            lines.append(f"  9yr: n={n9} · win={w9} · {aw9}/{al9} · EV={ev9} · ½K={hk9}")
            lines.append(f"  Δ ½-Kelly: {delta}")

        solo = _solo_size(ticker, bucket)
        hk_multi = hk9 if row else '—'
        lines.append(f"  → multi-pos: <b>{hk_multi}</b>  solo: <b>{solo}</b>  {row.get('verdict','') if row else ''}")

    lines.append(
        "\n<i>½K = half-Kelly capped 20% (2–3 positions open)\n"
        "solo = half-Kelly capped 30% (only 1 position open)</i>"
    )
    return "\n".join(lines)


# ── Public dispatch ──────────────────────────────────────────────────────────

def handle_sizing_command(arg: str) -> list[str]:
    """
    Dispatch /sizing sub-commands.
    Returns list of HTML messages to send in order.
    """
    arg = arg.strip()
    if not arg:
        return [msg_index()]
    if arg in ('a', 'signal_a', 'signala', 'signal a'):
        return msg_signal_table('a')
    if arg in ('b', 'signal_b', 'signalb', 'signal b'):
        return msg_signal_table('b')
    if arg in ('rules', 'rule', 'caps', 'cap', 'logic', 'sizing'):
        return [msg_rules()]
    return [msg_ticker(arg)]
