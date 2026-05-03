#!/usr/bin/env python3
"""
Generate side-by-side 5yr vs 9yr position sizing comparison.
Output: docs/SIGNAL_METRICS_REFERENCE.md  (replaces previous version)
"""
from __future__ import annotations
import json
from pathlib import Path

_here = Path(__file__).resolve().parent
OUT = _here.parent / "docs" / "SIGNAL_METRICS_REFERENCE.md"

RES_9YR = json.loads((_here / "cache" / "position_sizing_results.json").read_text())
RES_5YR = json.loads((_here / "cache" / "position_sizing_5yr.json").read_text())

MIN_TRADES = 5
GUARDRAIL_MIN = 5.0
GUARDRAIL_MAX = 20.0
SINGLE_POS_MAX = 30.0   # uncapped ceiling when only one position open

TICKER_NAMES = {
    'NQ=F':    'NASDAQ 100 Futures',
    'ES=F':    'S&P 500 Futures',
    'QQQ':     'NASDAQ 100 ETF',
    'SPY':     'S&P 500 ETF',
    'MSFT':    'Microsoft',
    'NVDA':    'NVIDIA',
    'GOOGL':   'Alphabet (Google)',
    'AAPL':    'Apple',
    'AVGO':    'Broadcom',
    'TSM':     'Taiwan Semiconductor',
    'META':    'Meta (Facebook)',
    'TSLA':    'Tesla',
    'AMZN':    'Amazon',
    'LLY':     'Eli Lilly',
    'WMT':     'Walmart',
    'BRK-B':   'Berkshire Hathaway',
    'JPM':     'JP Morgan Chase',
    'BAC':     'Bank of America',
    'NFLX':    'Netflix',
    'ORCL':    'Oracle',
    'UNH':     'UnitedHealth Group',
    'GLD':     'Gold ETF',
    'SLV':     'Silver ETF',
    'BTC-USD': 'Bitcoin',
    'SMH':     'Semiconductors ETF',
    'XLI':     'Industrials ETF',
    'MCD':     "McDonald's",
    'OXY':     'Occidental Petroleum',
    'XOM':     'Exxon Mobil',
    'CVX':     'Chevron',
    'ASML':    'ASML Holding',
    'SMCI':    'Super Micro Computer',
    '^TNX':    '10-Year Treasury Yield',
    '^VIX':    'VIX',
    'DX-Y.NYB':'US Dollar Index',
    '^GDAXI':  'DAX',
    '^FTSE':   'FTSE 100',
    '^N225':   'Nikkei 225',
}

ORDERED = [
    'NQ=F','ES=F','QQQ','SPY',
    'MSFT','NVDA','GOOGL','AAPL','AVGO','TSM',
    'META','TSLA',
    'AMZN','LLY','WMT',
    'BRK-B','JPM','BAC','NFLX','ORCL','UNH',
    'GLD','SLV','BTC-USD',
    'SMH','XLI','MCD','OXY','XOM','CVX',
    'ASML','SMCI','^TNX','^VIX','DX-Y.NYB','^GDAXI','^FTSE','^N225',
]


def half_kelly_raw(m: dict) -> float | None:
    """Uncapped half-Kelly — what the math actually says."""
    if not m or m.get('n', 0) < MIN_TRADES:
        return None
    k = m.get('kelly_binary')
    ev = m.get('ev_pct', 0) or 0
    if k is None or k <= 0 or ev <= 0:
        return None
    return max(GUARDRAIL_MIN, k / 2.0)


def half_kelly(m: dict) -> float:
    """Capped half-Kelly for multi-position use (hard 20% ceiling)."""
    raw = half_kelly_raw(m)
    if raw is None:
        return GUARDRAIL_MIN
    return min(GUARDRAIL_MAX, raw)


def single_pos_size(m: dict) -> float:
    """Sizing when this is the ONLY open position (up to 30% ceiling)."""
    raw = half_kelly_raw(m)
    if raw is None:
        return GUARDRAIL_MIN
    return min(SINGLE_POS_MAX, raw)


def verdict(m: dict) -> str:
    if not m or m.get('n', 0) < MIN_TRADES:
        return '—'
    k = m.get('kelly_binary', 0) or 0
    ev = m.get('ev_pct', 0) or 0
    win = m.get('win_rate', 0) or 0
    if ev <= 0 or k <= 0:
        return '✗'
    if k >= 30 and win >= 60:
        return '⭐⭐⭐'
    if k >= 15 and win >= 52:
        return '⭐⭐'
    return '⭐'


def delta_note(r5: float, r9: float) -> str:
    d = r9 - r5
    if d > 3:
        return f'↑ +{d:.0f}% (9yr stronger)'
    elif d < -3:
        return f'↓ {d:.0f}% (5yr stronger)'
    return f'≈ {d:+.0f}% (consistent)'


def fmt(v, dec=1, sign=False):
    if v is None:
        return '—'
    s = f'{v:+.{dec}f}' if sign else f'{v:.{dec}f}'
    return s + '%'


def build_md() -> str:
    lines = []
    a = lines.append

    a('# Signal Metrics Reference — 5-Year vs 9-Year Comparison')
    a('')
    a('*Both use non-overlapping entries (10-bar cooldown) and D5 holding period.*')
    a('*Half-Kelly clamped to [5%, 20%]. Max 3 simultaneous positions.*')
    a('')
    a('| Window | Bars | Entry rule | Purpose |')
    a('|--------|------|------------|---------|')
    a('| **5-year** | ~1,560 | Non-overlapping, first entry only | Recent regime — 2020–2025 |')
    a('| **9-year** | ~2,600 | Non-overlapping, first entry only | Full cycle — includes 2015–2019 |')
    a('')
    a('> **How to read the Δ column:** Positive = 9yr half-Kelly is higher (signal more robust')
    a('> across regimes). Negative = 5yr half-Kelly is higher (recent conditions favour it more).')
    a('')
    a('---')
    a('')

    for bucket_key, bucket_label, bucket_desc in [
        ('ultra_low', 'Signal A', 'RSI-MA < 5th Percentile + COV Red Bar'),
        ('low',       'Signal B', 'RSI-MA 5th–15th Percentile + COV Red Bar'),
    ]:
        a(f'## {bucket_label} — {bucket_desc}')
        a('')
        a('| # | Ticker | Name '
          '| 5yr N | 5yr Win% | 5yr Avg Win | 5yr Avg Loss | 5yr EV | 5yr ½-Kelly '
          '| 9yr N | 9yr Win% | 9yr Avg Win | 9yr Avg Loss | 9yr EV | 9yr ½-Kelly '
          '| Δ ½-Kelly | Verdict |')
        a('|---|--------|------'
          '|-------|---------|------------|-------------|--------|------------'
          '|-------|---------|------------|-------------|--------|------------'
          '|-----------|---------|')

        row = 0
        for ticker in ORDERED:
            m5 = RES_5YR.get(ticker, {}).get(bucket_key, {}).get('cov_confluence', {})
            m9 = RES_9YR.get(ticker, {}).get(bucket_key, {}).get('cov_confluence', {})
            if not m5 and not m9:
                continue

            hk5 = half_kelly(m5)
            hk9 = half_kelly(m9)
            delta = hk9 - hk5
            d_str = f'{delta:+.0f}%'
            v5 = verdict(m5)
            v9 = verdict(m9)
            row += 1

            # Highlight if directions differ (one is skip, other isn't)
            if v5 == '✗' and v9 != '✗':
                note = '🟢 9yr unlocks edge'
            elif v9 == '✗' and v5 != '✗':
                note = '🔴 9yr loses edge'
            elif v9 == '⭐⭐⭐' and v5 != '⭐⭐⭐':
                note = '🟢 9yr stronger'
            elif v5 == '⭐⭐⭐' and v9 != '⭐⭐⭐':
                note = '🔴 5yr stronger'
            else:
                note = v9

            a(
                f'| {row} | **{ticker}** | {TICKER_NAMES.get(ticker, ticker)} '
                f'| {m5.get("n","—")} | {fmt(m5.get("win_rate"))} '
                f'| {fmt(m5.get("avg_win_pct"), sign=True)} '
                f'| {fmt(m5.get("avg_loss_pct"), sign=True)} '
                f'| {fmt(m5.get("ev_pct"), dec=3, sign=True)} '
                f'| **{hk5:.0f}%** '
                f'| {m9.get("n","—")} | {fmt(m9.get("win_rate"))} '
                f'| {fmt(m9.get("avg_win_pct"), sign=True)} '
                f'| {fmt(m9.get("avg_loss_pct"), sign=True)} '
                f'| {fmt(m9.get("ev_pct"), dec=3, sign=True)} '
                f'| **{hk9:.0f}%** '
                f'| {d_str} | {note} |'
            )

        a('')
        a('---')
        a('')

    # ── Summary: where they agree vs diverge ──────────────────────────────
    a('## Summary — Where the Two Windows Agree vs Diverge (Signal A)')
    a('')
    a('| Category | Tickers | Implication |')
    a('|----------|---------|-------------|')

    stronger_9 = []
    stronger_5 = []
    consistent_pos = []
    consistent_skip = []
    flip_5skip_9ok = []
    flip_9skip_5ok = []

    for ticker in ORDERED:
        m5 = RES_5YR.get(ticker, {}).get('ultra_low', {}).get('cov_confluence', {})
        m9 = RES_9YR.get(ticker, {}).get('ultra_low', {}).get('cov_confluence', {})
        hk5, hk9 = half_kelly(m5), half_kelly(m9)
        v5, v9 = verdict(m5), verdict(m9)
        delta = hk9 - hk5
        if v5 == '✗' and v9 != '✗':
            flip_5skip_9ok.append(ticker)
        elif v9 == '✗' and v5 != '✗':
            flip_9skip_5ok.append(ticker)
        elif v5 == '✗' and v9 == '✗':
            consistent_skip.append(ticker)
        elif delta >= 4:
            stronger_9.append(f'{ticker}({delta:+.0f}%)')
        elif delta <= -4:
            stronger_5.append(f'{ticker}({delta:+.0f}%)')
        else:
            consistent_pos.append(ticker)

    a(f'| ⭐ Consistent positive (both windows agree, similar size) | {", ".join(consistent_pos)} | High confidence — trade these |')
    a(f'| 🟢 9yr meaningfully higher | {", ".join(stronger_9) or "—"} | Robust across cycles — favour 9yr sizing |')
    a(f'| 🔴 5yr meaningfully higher | {", ".join(stronger_5) or "—"} | Recent conditions better — be cautious on 9yr |')
    a(f'| 🟢 9yr finds edge, 5yr skips | {", ".join(flip_5skip_9ok) or "—"} | Longer horizon needed to see the edge |')
    a(f'| 🔴 9yr loses edge, 5yr has it | {", ".join(flip_9skip_5ok) or "—"} | Recent bull cycle only — treat with caution |')
    a(f'| ✗ Both windows say skip | {", ".join(consistent_skip) or "—"} | No D5 edge regardless of window — floor only |')
    a('')
    a('---')
    a('')

    # ── Quick sizing card ─────────────────────────────────────────────────
    a('## Quick Sizing Card — Both Windows')
    a('')
    a('*Signal A only. Use the more conservative of the two (lower ½-Kelly) unless you have*')
    a('*a strong view on which regime you are in.*')
    a('')
    a('| Ticker | Name | 5yr ½-K | 9yr ½-K | Conservative | Aggressive | Regime note |')
    a('|--------|------|---------|---------|-------------|-----------|-------------|')

    for ticker in ORDERED:
        m5 = RES_5YR.get(ticker, {}).get('ultra_low', {}).get('cov_confluence', {})
        m9 = RES_9YR.get(ticker, {}).get('ultra_low', {}).get('cov_confluence', {})
        hk5, hk9 = half_kelly(m5), half_kelly(m9)
        conservative = min(hk5, hk9)
        aggressive   = max(hk5, hk9)
        delta = hk9 - hk5
        if delta > 5:
            note = '9yr stronger — signal improves over longer cycle'
        elif delta < -5:
            note = '5yr stronger — recent conditions better for this trade'
        elif hk5 <= GUARDRAIL_MIN and hk9 <= GUARDRAIL_MIN:
            note = 'No edge in either window'
        else:
            note = 'Consistent'
        a(f'| **{ticker}** | {TICKER_NAMES.get(ticker,ticker)} '
          f'| {hk5:.0f}% | {hk9:.0f}% '
          f'| **{conservative:.0f}%** | {aggressive:.0f}% | {note} |')

    a('')
    a('---')
    a('')
    a('## Definitions')
    a('')
    a('| Term | Formula | Meaning |')
    a('|------|---------|---------|')
    a('| Win% | trades > 0 / total | % of D5 exits above entry |')
    a('| Avg Win | mean(winning returns) | Average gain when trade wins |')
    a('| Avg Loss | mean(losing returns) | Average loss when trade loses (negative number) |')
    a('| Net EV | Win% × Avg Win + Loss% × Avg Loss | Expected return per trade |')
    a('| Kelly | (p×b − q) / b | Theoretically optimal bet fraction |')
    a('| ½-Kelly | Kelly ÷ 2 | Practical sizing — reduces drawdown risk |')
    a('| Rec% | max(5%, min(20%, ½-Kelly)) | Guardrail-clamped portfolio allocation |')

    return '\n'.join(lines)


def main():
    md = build_md()
    OUT.write_text(md)
    print(f'Written → {OUT}  ({md.count(chr(10))} lines)')


if __name__ == '__main__':
    main()
