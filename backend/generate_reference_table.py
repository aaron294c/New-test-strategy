#!/usr/bin/env python3
"""
Generate comprehensive metrics reference table for all tickers.
Outputs docs/SIGNAL_METRICS_REFERENCE.md
"""
from __future__ import annotations
import json
from pathlib import Path

_here = Path(__file__).resolve().parent
CACHE = _here / "cache" / "position_sizing_results.json"
OUT = _here.parent / "docs" / "SIGNAL_METRICS_REFERENCE.md"

GUARDRAIL_MIN = 5.0
GUARDRAIL_MAX = 20.0

# Old overlapping 5yr data for cross-reference (D5 and D21 win rates)
OLD_5YR = {
    'AAPL':    {'wr5': 60.6, 'wr21': 66.7, 'med21': 3.12},
    'MSFT':    {'wr5': 64.3, 'wr21': 57.1, 'med21': 1.68},
    'NVDA':    {'wr5': 80.0, 'wr21': 80.0, 'med21': 3.44},
    'GOOGL':   {'wr5': 69.2, 'wr21': 61.5, 'med21': 5.02},
    'AMZN':    {'wr5': 58.8, 'wr21': 67.6, 'med21': 2.41},
    'META':    {'wr5': 57.7, 'wr21': 57.7, 'med21': 4.37},
    'QQQ':     {'wr5': 69.6, 'wr21': 65.2, 'med21': 1.61},
    'SPY':     {'wr5': 75.9, 'wr21': 82.8, 'med21': 2.51},
    'GLD':     {'wr5': 31.8, 'wr21': 68.2, 'med21': 2.87},
    'SLV':     {'wr5': 56.5, 'wr21': 65.2, 'med21': 3.75},
    'TSLA':    {'wr5': 56.2, 'wr21': 53.1, 'med21': 0.14},
    'NFLX':    {'wr5': 48.1, 'wr21': 48.1, 'med21': -0.68},
    'BRK-B':   {'wr5': 53.3, 'wr21': 66.7, 'med21': 1.77},
    'WMT':     {'wr5': 56.0, 'wr21': 60.0, 'med21': 1.24},
    'UNH':     {'wr5': 45.0, 'wr21': 50.0, 'med21': 0.57},
    'AVGO':    {'wr5': 68.0, 'wr21': 80.0, 'med21': 8.34},
    'LLY':     {'wr5': 60.7, 'wr21': 75.0, 'med21': 6.61},
    'TSM':     {'wr5': 61.8, 'wr21': 70.6, 'med21': 5.86},
    'ORCL':    {'wr5': 63.2, 'wr21': 68.4, 'med21': 6.12},
    'OXY':     {'wr5': 59.4, 'wr21': 43.8, 'med21': -2.33},
    'XOM':     {'wr5': 66.7, 'wr21': 74.1, 'med21': 1.61},
    'CVX':     {'wr5': 45.7, 'wr21': 54.3, 'med21': 0.52},
    'JPM':     {'wr5': 57.1, 'wr21': 53.6, 'med21': 1.59},
    'BAC':     {'wr5': 51.2, 'wr21': 68.3, 'med21': 4.18},
    'ES=F':    {'wr5': 75.9, 'wr21': 79.3, 'med21': 3.19},
    'NQ=F':    {'wr5': 59.1, 'wr21': 63.6, 'med21': 1.27},
    'BTC-USD': {'wr5': 61.1, 'wr21': 53.7, 'med21': 0.89},
    'XLI':     {'wr5': 63.3, 'wr21': 56.7, 'med21': 0.70},
    'MCD':     {'wr5': None, 'wr21': None, 'med21': None},
    'SMH':     {'wr5': None, 'wr21': None, 'med21': None},
    'ASML':    {'wr5': None, 'wr21': None, 'med21': None},
    'SMCI':    {'wr5': None, 'wr21': None, 'med21': None},
}

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
    'GLD':     'Gold ETF (SPDR)',
    'SLV':     'Silver ETF (iShares)',
    'BTC-USD': 'Bitcoin',
    'SMH':     'VanEck Semiconductors ETF',
    'XLI':     'Industrials ETF (SPDR)',
    'MCD':     "McDonald's",
    'OXY':     'Occidental Petroleum',
    'XOM':     'Exxon Mobil',
    'CVX':     'Chevron',
    'ASML':    'ASML Holding',
    'SMCI':    'Super Micro Computer',
    '^TNX':    '10-Year Treasury Yield',
    '^VIX':    'CBOE Volatility Index',
    'DX-Y.NYB':'US Dollar Index',
    '^GDAXI':  'DAX (Germany)',
    '^FTSE':   'FTSE 100 (UK)',
    '^N225':   'Nikkei 225 (Japan)',
}

# Ordered by user priority — most actively traded first
ORDERED = [
    # Tier 1: Primary
    'NQ=F', 'ES=F', 'QQQ', 'SPY',
    'MSFT', 'NVDA', 'GOOGL', 'AAPL',
    'AVGO', 'TSM',
    # Tier 2: Now in play
    'META', 'TSLA',
    # Tier 3: Others the user mentioned
    'AMZN', 'LLY', 'WMT',
    'BRK-B', 'JPM', 'BAC',
    'NFLX', 'ORCL', 'UNH',
    'GLD', 'SLV',
    'BTC-USD',
    # Tier 4: Full universe remainder
    'SMH', 'XLI', 'MCD',
    'OXY', 'XOM', 'CVX',
    'ASML', 'SMCI',
    '^TNX', '^VIX', 'DX-Y.NYB',
    '^GDAXI', '^FTSE', '^N225',
]


def half_kelly_rec(m: dict) -> float:
    if not m or m.get('n', 0) < 8:
        return GUARDRAIL_MIN
    k = m.get('kelly_binary')
    ev = m.get('ev_pct', 0) or 0
    if k is None or k <= 0 or ev <= 0:
        return GUARDRAIL_MIN
    return max(GUARDRAIL_MIN, min(GUARDRAIL_MAX, k / 2.0))


def verdict(m: dict) -> str:
    if not m or m.get('n', 0) < 8:
        return '—'
    k = m.get('kelly_binary', 0) or 0
    ev = m.get('ev_pct', 0) or 0
    win = m.get('win_rate', 0) or 0
    if ev <= 0 or k <= 0:
        return '✗ skip'
    if k >= 30 and win >= 60:
        return '⭐⭐⭐'
    if k >= 15 and win >= 52:
        return '⭐⭐'
    return '⭐'


def fmt(v, decimals=1, sign=False, pct=True):
    if v is None:
        return '—'
    spec = f'{v:+.{decimals}f}' if sign else f'{v:.{decimals}f}'
    return spec + ('%' if pct else '')


def build_md(results: dict) -> str:
    lines = []
    a = lines.append

    a('# Signal Metrics Reference — Full Universe')
    a('')
    a('*Method: non-overlapping entries (10-bar cooldown), 9-year data window, D5 holding period.*')
    a('*Half-Kelly = Kelly ÷ 2, clamped to [5%, 20%] portfolio guardrail.*')
    a('*3 signals max open simultaneously.*')
    a('')

    # ── Methodology note ───────────────────────────────────────────────────
    a('## Why Two Different Numbers Exist')
    a('')
    a('| Method | Window | Entry rule | What it measures |')
    a('|--------|--------|------------|-----------------|')
    a('| Old (`cov_confluence_summary.md`) | 5 years | Every bar that fires (overlapping) | Peak-case: entering every day during a dip episode |')
    a('| **This document** | **9 years** | **First entry only, 10-day cooldown** | **Realistic: one entry per episode** |')
    a('')
    a('Neither is wrong — they measure different things. The 9-year non-overlapping figure is the')
    a('**conservative baseline** used for sizing. Where the 9-year is *higher* than the 5-year')
    a('(e.g. TSLA, META, NQ=F, MSFT), that means the signal is robust across multiple market regimes,')
    a('not just the 2019-2024 bull run. Where it is *lower* (NVDA, AVGO, LLY), the 5-year window')
    a('captured an exceptionally strong bull-market cycle that inflated those numbers.')
    a('')
    a('**Key finding:** TSLA and META are STRONGER in the 9-year non-overlapping test than in the')
    a('5-year overlapping test. These are genuinely robust signals across regimes.')
    a('')
    a('---')
    a('')

    # ── SIGNAL A TABLE ──────────────────────────────────────────────────────
    a('## Signal A — Ultra-Low Entry: RSI-MA < 5th Percentile + COV Red Bar')
    a('')
    a('*Entry fires when RSI-MA drops below the 5th percentile of its 252-day range AND the*')
    a('*COV indicator shows a red bar (Fisher-z correlation ≤ −1.3 = |r| ≥ 0.86).*')
    a('')
    a('| # | Ticker | Name | N | Win% | Avg Win | Loss% | Avg Loss | Net EV | Kelly | **½-Kelly Rec** | Verdict |')
    a('|---|--------|------|---|------|---------|-------|----------|--------|-------|-----------------|---------|')

    row = 0
    for ticker in ORDERED:
        if ticker not in results:
            continue
        m = results[ticker]['ultra_low']['cov_confluence']
        if m.get('n', 0) < 5:
            continue
        row += 1
        rec = half_kelly_rec(m)
        v = verdict(m)
        a(
            f'| {row} | **{ticker}** | {TICKER_NAMES.get(ticker, ticker)} '
            f'| {m["n"]} '
            f'| {fmt(m["win_rate"])} '
            f'| {fmt(m["avg_win_pct"], sign=True)} '
            f'| {fmt(m["loss_rate"])} '
            f'| {fmt(m["avg_loss_pct"], sign=True)} '
            f'| {fmt(m["ev_pct"], decimals=3, sign=True)} '
            f'| {fmt(m.get("kelly_binary"), sign=True)} '
            f'| **{rec:.0f}%** '
            f'| {v} |'
        )

    a('')
    a('---')
    a('')

    # ── SIGNAL B TABLE ──────────────────────────────────────────────────────
    a('## Signal B — Low Entry: RSI-MA 5th–15th Percentile + COV Red Bar')
    a('')
    a('*Moderate oversold zone — fires more frequently than Signal A (~2x per year per ticker more).*')
    a('')
    a('| # | Ticker | Name | N | Win% | Avg Win | Loss% | Avg Loss | Net EV | Kelly | **½-Kelly Rec** | Verdict |')
    a('|---|--------|------|---|------|---------|-------|----------|--------|-------|-----------------|---------|')

    row = 0
    for ticker in ORDERED:
        if ticker not in results:
            continue
        m = results[ticker]['low']['cov_confluence']
        if m.get('n', 0) < 5:
            continue
        row += 1
        rec = half_kelly_rec(m)
        v = verdict(m)
        a(
            f'| {row} | **{ticker}** | {TICKER_NAMES.get(ticker, ticker)} '
            f'| {m["n"]} '
            f'| {fmt(m["win_rate"])} '
            f'| {fmt(m["avg_win_pct"], sign=True)} '
            f'| {fmt(m["loss_rate"])} '
            f'| {fmt(m["avg_loss_pct"], sign=True)} '
            f'| {fmt(m["ev_pct"], decimals=3, sign=True)} '
            f'| {fmt(m.get("kelly_binary"), sign=True)} '
            f'| **{rec:.0f}%** '
            f'| {v} |'
        )

    a('')
    a('---')
    a('')

    # ── CROSS-REFERENCE: 5yr vs 9yr ─────────────────────────────────────────
    a('## Cross-Reference: Old 5-Year (Overlapping) vs This 9-Year (Non-Overlapping)')
    a('')
    a('*Signal A only. Δ = 9yr minus 5yr. Positive Δ means 9yr is stronger — more robust signal.*')
    a('')
    a('| Ticker | 5yr D5 win% | 9yr D5 win% | Δ | 5yr D21 win% | 5yr med D21 | Interpretation |')
    a('|--------|------------|------------|---|-------------|------------|----------------|')

    for ticker in ORDERED:
        if ticker not in results or ticker not in OLD_5YR:
            continue
        old = OLD_5YR[ticker]
        if old['wr5'] is None:
            continue
        nm = results[ticker]['ultra_low']['cov_confluence']
        if nm.get('n', 0) < 5:
            continue
        delta = nm['win_rate'] - old['wr5']
        if delta > 5:
            interp = '✅ Stronger over full decade'
        elif delta < -15:
            interp = '⚠️ Bull-market inflated — 5yr too optimistic'
        elif delta < -5:
            interp = 'Slightly lower — recent bull cycle helped'
        else:
            interp = 'Consistent across regimes'
        med21 = f"+{old['med21']:.2f}%" if old['med21'] and old['med21'] > 0 else (f"{old['med21']:.2f}%" if old['med21'] else '—')
        a(
            f'| **{ticker}** | {old["wr5"]:.1f}% | {nm["win_rate"]:.1f}% '
            f'| {delta:+.1f}pp '
            f'| {old["wr21"]:.1f}% '
            f'| {med21} '
            f'| {interp} |'
        )

    a('')
    a('---')
    a('')

    # ── D21 CONTEXT NOTE ────────────────────────────────────────────────────
    a('## D21 Context — The Strategy Gets Better the Longer You Hold')
    a('')
    a('The tables above measure D5 (5-day exit). The old backtest also computed D21 results.')
    a('These D21 figures are from the overlapping 5-year window (Signal A + COV red) for reference:')
    a('')
    a('| Ticker | D21 Win% | Median D21 Return | vs D5 Win% | Improvement |')
    a('|--------|---------|-------------------|-----------|-------------|')

    d21_pairs = [
        ('NQ=F',  63.6, 1.27,  59.1),
        ('ES=F',  79.3, 3.19,  75.9),
        ('QQQ',   65.2, 1.61,  69.6),
        ('SPY',   82.8, 2.51,  75.9),
        ('MSFT',  57.1, 1.68,  64.3),
        ('NVDA',  80.0, 3.44,  80.0),
        ('GOOGL', 61.5, 5.02,  69.2),
        ('AAPL',  66.7, 3.12,  60.6),
        ('AVGO',  80.0, 8.34,  68.0),
        ('TSM',   70.6, 5.86,  61.8),
        ('META',  57.7, 4.37,  57.7),
        ('TSLA',  53.1, 0.14,  56.2),
        ('AMZN',  67.6, 2.41,  58.8),
        ('LLY',   75.0, 6.61,  60.7),
        ('WMT',   60.0, 1.24,  56.0),
        ('BAC',   68.3, 4.18,  51.2),
        ('JPM',   53.6, 1.59,  57.1),
        ('GLD',   68.2, 2.87,  31.8),
        ('SLV',   65.2, 3.75,  56.5),
    ]
    for t, wr21, med21, wr5 in sorted(d21_pairs, key=lambda x: x[1], reverse=True):
        delta = wr21 - wr5
        sign = '+' if delta >= 0 else ''
        a(f'| **{t}** | {wr21:.1f}% | +{med21:.2f}% | {wr5:.1f}% | {sign}{delta:.1f}pp at 21 days |')

    a('')
    a('> **Gold (GLD)** is the most striking: 31.8% win at D5 → 68.2% win at D21. The signal fires correctly')
    a('> but gold takes 2–3 weeks to recover, not 5 days. If trading GLD, target D21 not D5.')
    a('')
    a('---')
    a('')

    # ── SIZING QUICK-REFERENCE ──────────────────────────────────────────────
    a('## Quick-Reference Sizing Card')
    a('')
    a('*For printing / desk use. Half-Kelly, 9-year non-overlapping data.*')
    a('')
    a('| Ticker | Signal A rec | Signal B rec | Notes |')
    a('|--------|-------------|-------------|-------|')

    notes_map = {
        'NQ=F':    '74% win A — highest Kelly in universe',
        'ES=F':    '70% win A — strong, also good at B',
        'MSFT':    '73% win A — 9yr stronger than 5yr (+8.7pp)',
        'META':    'Both signals strong — 9yr HIGHER than 5yr (+9.9pp)',
        'TSLA':    '71% win A — 9yr far HIGHER than 5yr (+15pp). Reconsider tier.',
        'NVDA':    'Good A — 5yr showed 80% (bull inflated), 9yr 57.6%',
        'AVGO':    'Flip: B stronger than A — 62% win B',
        'LLY':     'Flip: B very strong (68%), A weak. Use B only.',
        'GLD':     'A: skip. B: 11%. At D21, GLD is much better.',
        'SLV':     'No edge at D5 in either signal.',
        'BTC-USD': 'A strong (67%), B: skip — avg loss balloons at B',
        'NFLX':    'A: skip. B good (60% win, 12%).',
        'CVX':     'No edge — high win% but avg losses crush it.',
        'OXY':     'No edge in either bucket.',
        'XOM':     'Nearly zero EV at D5.',
        'BAC':     'A: skip. B barely above floor.',
    }

    for ticker in ORDERED:
        if ticker not in results:
            continue
        a_rec = half_kelly_rec(results[ticker]['ultra_low']['cov_confluence'])
        b_rec = half_kelly_rec(results[ticker]['low']['cov_confluence'])
        note = notes_map.get(ticker, '')
        a(f'| **{ticker}** | {a_rec:.0f}% | {b_rec:.0f}% | {note} |')

    a('')
    a('---')
    a('')
    a('## Definitions')
    a('')
    a('| Term | Formula | Meaning |')
    a('|------|---------|---------|')
    a('| Win% | trades ending >0 / total | Fraction of D5 exits above entry price |')
    a('| Avg Win | mean of positive returns | What you earn on average when you win |')
    a('| Loss% | 1 − Win% | Fraction of D5 exits below entry price |')
    a('| Avg Loss | mean of negative returns | What you lose on average when you lose (negative number) |')
    a('| Net EV | Win% × Avg Win + Loss% × Avg Loss | **Expected return per trade** — the number that matters |')
    a('| Kelly | (p×b − q) / b | Optimal fraction of bankroll per trade |')
    a('| Half-Kelly | Kelly ÷ 2 | Practical recommendation — reduces ruin risk vs full Kelly |')
    a('| Rec% | max(5, min(20, Half-Kelly)) | Half-Kelly clamped to portfolio guardrails |')

    return '\n'.join(lines)


def main():
    data = json.loads(CACHE.read_text())
    md = build_md(data)
    OUT.write_text(md)
    print(f'Written → {OUT}')
    lines = md.count('\n')
    print(f'Lines: {lines}')


if __name__ == '__main__':
    main()
