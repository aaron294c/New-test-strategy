#!/usr/bin/env python3
"""
Options signal handler for Telegram — RSI-MA &lt;5th pct (no COV required for QQQ/SPY).

Commands:
  /options        — live scan: is there a bull-put-spread entry right now?
  /iv             — current VIX / VXN / VIX9D dashboard
  /optwatch       — current RSI-MA percentile levels + distance to signal
  /optbacktest    — full historical stats table (backtested 9yr)
  /optlog [n]     — last n logged option signals

All returned strings use Telegram HTML parse_mode. Use &lt; and &gt; for
literal angle-bracket characters — never bare < or > outside HTML tags.
"""
from __future__ import annotations

import json
import math
import sys
import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import scipy.stats as st
import yfinance as yf

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "backend"))

from macro_instruments import calculate_rsi_ma  # noqa: E402

# ── Verified backtest reference values ────────────────────────────────────────
# Source: scripts/options_rsima_only.py  42 QQQ / 47 SPY signals, 9yr, RSI-MA only

REF = {
    "QQQ": {
        "name": "NASDAQ 100 ETF", "iv_sym": "^VXN",
        "n_signals": 42, "signals_per_year": 4.7, "hk": 0.20,
        "eq_avg_loss_pct": 2.86, "eq_win_rate": 69.0, "eq_ev": 1.21,
        # Bull Put Spread -2%/-5% 10 DTE
        "bps_win_rate": 78.6, "bps_ev": 11.3,
        "bps_avg_win": 20.5, "bps_avg_loss": -22.2,
        "bps_p5": -36.8, "bps_p25": -5.2, "bps_median": 16.9,
        "bps_p75": 25.1, "bps_p95": 31.8, "bps_max_win": 33.0,
        # By IV regime
        "bps_wr_low": 50, "bps_wr_mid": 72, "bps_wr_high": 88,
        "bps_ev_mid": 6.6, "bps_ev_high": 18.2,
        # Bull Call Spread ATM/+3% 35 DTE
        "bcs_win_rate": 64.3, "bcs_ev": 14.6,
        "bcs_avg_win": 34.6, "bcs_avg_loss": -21.4,
        # Long ATM Call 35 DTE
        "lc_win_rate": 52.4, "lc_ev": 7.6,
    },
    "SPY": {
        "name": "S&P 500 ETF", "iv_sym": "^VIX",
        "n_signals": 47, "signals_per_year": 5.2, "hk": 0.20,
        "eq_avg_loss_pct": 2.43, "eq_win_rate": 70.2, "eq_ev": 0.88,
        # Bull Put Spread -2%/-5% 10 DTE
        "bps_win_rate": 89.4, "bps_ev": 12.4,
        "bps_avg_win": 17.8, "bps_avg_loss": -32.7,
        "bps_p5": -31.4, "bps_p25": 3.3, "bps_median": 15.9,
        "bps_p75": 26.8, "bps_p95": 33.1, "bps_max_win": 35.0,
        "bps_wr_low": 50, "bps_wr_mid": 93, "bps_wr_high": 88,
        "bps_ev_mid": 11.5, "bps_ev_high": 18.1,
        "bcs_win_rate": 66.0, "bcs_ev": 13.3,
        "bcs_avg_win": 29.8, "bcs_avg_loss": -18.8,
        "lc_win_rate": 51.1, "lc_ev": -0.55,    # NEGATIVE — avoid
    },
}

RSI_LOOKBACK   = 252
SIGNAL_THRESH  = 5.0
RFREE          = 0.053
LOG_PATH       = _ROOT / "docs" / "options_signal_log.json"
LOG_MD_PATH    = _ROOT / "docs" / "OPTIONS_SIGNAL_LOG.md"


# ── Black-Scholes ──────────────────────────────────────────────────────────────

def _bs_put(S, K, T, r, sigma):
    if T <= 0 or sigma <= 0: return max(K - S, 0)
    d1 = (math.log(S/K) + (r + .5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    return K*math.exp(-r*T)*st.norm.cdf(-d2) - S*st.norm.cdf(-d1)

def _bs_call(S, K, T, r, sigma):
    if T <= 0 or sigma <= 0: return max(S - K, 0)
    d1 = (math.log(S/K) + (r + .5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    return S*st.norm.cdf(d1) - K*math.exp(-r*T)*st.norm.cdf(d2)

def _bs_put_delta(S, K, T, r, sigma):
    if T <= 0: return -1.0 if S < K else 0.0
    d1 = (math.log(S/K) + (r + .5*sigma**2)*T) / (sigma*math.sqrt(T))
    return st.norm.cdf(d1) - 1.0


# ── Data helpers ───────────────────────────────────────────────────────────────

def _download(tickers: list[str], period: str = "18mo") -> dict[str, pd.Series]:
    raw = yf.download(tickers, period=period, interval="1d",
                      progress=False, auto_adjust=True, threads=True)
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"]
    else:
        close = raw[["Close"]]
        if tickers: close.columns = [tickers[0]]
    out = {}
    for t in tickers:
        if t in close.columns:
            s = close[t].dropna()
            if len(s) > 10: out[t] = s
    return out

def _rsi_ma_pct(close: pd.Series) -> Optional[float]:
    if len(close) < RSI_LOOKBACK + 30: return None
    rma = calculate_rsi_ma(close)
    window = rma.dropna().iloc[-RSI_LOOKBACK:]
    if len(window) < RSI_LOOKBACK: return None
    current = window.iloc[-1]
    below   = (window.iloc[:-1] < current).sum()
    return float(below / (len(window) - 1) * 100)

def _iv_level(ser: pd.Series) -> Optional[float]:
    if ser is None or ser.empty: return None
    return float(ser.dropna().iloc[-1])

def _nearest_friday(target_days: int = 10) -> datetime.date:
    today = datetime.date.today()
    best, best_diff = None, 9999
    for offset in range(5, 18):
        d = today + datetime.timedelta(days=offset)
        if d.weekday() == 4:
            diff = abs(offset - target_days)
            if diff < best_diff:
                best_diff = diff; best = d
    return best or (today + datetime.timedelta(days=10))

def _iv_regime(iv_pct: float) -> tuple[str, str]:
    if iv_pct < 15:
        return ("🟢 LOW (&lt;15%)", "Long ATM Call preferred — IV crush risk minimal")
    elif iv_pct < 20:
        return ("🟡 MID-LOW (15-20%)", "Bull Put Spread or Bull Call Spread — either works")
    elif iv_pct < 25:
        return ("🟠 MID (20-25%)", "Bull Put Spread ★★ — good premium, crush incoming")
    else:
        return ("🔴 HIGH (&gt;25%)", "Bull Put Spread ★★★ — sell expensive IV, best regime")


# ── Options pricing ────────────────────────────────────────────────────────────

def _price_bull_put_spread(S: float, iv: float, dte: int) -> dict:
    K_sell = round(S * 0.98); K_buy = round(S * 0.95)
    T      = dte / 252
    p_sell = _bs_put(S, K_sell, T, RFREE, iv)
    p_buy  = _bs_put(S, K_buy,  T, RFREE, iv)
    credit = p_sell - p_buy; width = K_sell - K_buy
    return {
        "K_sell": K_sell, "K_buy": K_buy,
        "credit": credit, "width": width,
        "max_loss": width - credit,
        "credit_pct_width": credit / width * 100 if width > 0 else 0,
        "breakeven": K_sell - credit,
        "breakeven_pct_from_spot": (K_sell - credit - S) / S * 100,
        "delta_short": _bs_put_delta(S, K_sell, T, RFREE, iv),
    }

def _price_bull_call_spread(S: float, iv: float, dte: int = 35) -> dict:
    K_buy = round(S); K_sell = round(S * 1.03)
    T     = dte / 252
    c_buy = _bs_call(S, K_buy,  T, RFREE, iv)
    c_sell= _bs_call(S, K_sell, T, RFREE, iv)
    debit = c_buy - c_sell; width = K_sell - K_buy
    return {
        "K_buy": K_buy, "K_sell": K_sell,
        "debit": debit, "width": width,
        "max_gain": width - debit,
        "debit_pct_width": debit / width * 100 if width > 0 else 0,
        "breakeven": K_buy + debit,
        "breakeven_pct_from_spot": debit / S * 100,
    }


# ── Signal log ─────────────────────────────────────────────────────────────────

def _log_signal(entry: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log: list = []
    if LOG_PATH.exists():
        try: log = json.loads(LOG_PATH.read_text())
        except Exception: log = []
    log.append(entry)
    LOG_PATH.write_text(json.dumps(log, indent=2, default=str))
    _rebuild_log_md(log)

def _rebuild_log_md(log: list) -> None:
    lines = [
        "# Options Signal Log — RSI-MA &lt;5th Pct (QQQ/SPY)",
        "", f"*Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} UTC*", "",
        "| Date | Ticker | Pct | VIX/VXN | Spot | Sell | Buy | DTE | Credit | Width | MaxLoss | Regime |",
        "|------|--------|-----|---------|------|------|-----|-----|--------|-------|---------|--------|",
    ]
    for e in reversed(log[-50:]):
        lines.append(
            f"| {e.get('date','?')} | {e.get('ticker','?')} | {e.get('pct','?'):.1f}th | "
            f"{e.get('iv','?'):.1f}% | ${e.get('spot','?'):.2f} | ${e.get('K_sell','?')} | "
            f"${e.get('K_buy','?')} | {e.get('dte','?')} | ${e.get('credit','?'):.2f} | "
            f"${e.get('width','?')} | ${e.get('max_loss','?'):.2f} | {e.get('regime','?')} |"
        )
    LOG_MD_PATH.write_text("\n".join(lines) + "\n")


# ── Message formatters ─────────────────────────────────────────────────────────

def _fmt_options_result(ticker: str, pct: float, spot: float,
                        iv: float, iv_sym: str, spread: dict,
                        bcs: dict, dte: int, expiry: datetime.date,
                        ref: dict, portfolio: int = 100_000) -> list[str]:
    """Full 6-message options signal output."""
    regime_label, regime_advice = _iv_regime(iv)

    if iv < 15:   primary = "⚠️ LOW IV — Consider Long ATM Call instead"; strategy = "long_call"
    elif iv < 20: primary = "Bull Put Spread OR Bull Call Spread"; strategy = "either"
    else:         primary = "Bull Put Spread ★★★"; strategy = "bull_put_spread"

    if pct < 1.0:   strength = "🔥 EXTREME (&lt;1st pct)"
    elif pct < 2.0: strength = "⚡ VERY STRONG (1-2nd pct)"
    elif pct < 3.0: strength = "💪 STRONG (2-3rd pct)"
    else:           strength = "✅ SIGNAL A (&lt;5th pct)"

    w   = spread["width"]; cr = spread["credit"]
    max_loss_d = spread["max_loss"] * 100

    # Dollar values at 1 contract
    avg_win_d  = ref["bps_avg_win"]  / 100 * w * 100
    avg_loss_d = ref["bps_avg_loss"] / 100 * w * 100
    median_d   = ref["bps_median"]   / 100 * w * 100
    p5_d       = ref["bps_p5"]       / 100 * w * 100
    p25_d      = ref["bps_p25"]      / 100 * w * 100
    p75_d      = ref["bps_p75"]      / 100 * w * 100
    p95_d      = ref["bps_p95"]      / 100 * w * 100
    max_win_d  = ref["bps_max_win"]  / 100 * w * 100

    # IV-regime win rate
    wr_regime = ref["bps_wr_high"] if iv >= 25 else ref["bps_wr_mid"] if iv >= 15 else ref["bps_wr_low"]
    ev_regime = ref["bps_ev_high"] if iv >= 25 else ref["bps_ev_mid"] if iv >= 15 else 0

    # Sizing
    dollar_budget = ref["hk"] * portfolio * ref["eq_avg_loss_pct"] / 100

    # ── MSG 1: Signal alert ────────────────────────────────────────────────────
    m1 = (
        f"🔔 <b>OPTIONS SIGNAL — {ticker}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 RSI-MA below 5th percentile\n"
        f"Percentile: <b>{pct:.1f}th</b>  {strength}\n"
        f"IV ({iv_sym}):  <b>{iv:.1f}%</b>  {regime_label}\n"
        f"\n"
        f"🎯 <b>Strategy:</b> {primary}\n"
        f"{regime_advice}\n"
        f"\n"
        f"Backtest: {ref['n_signals']} signals over 9yr "
        f"(~{ref['signals_per_year']:.1f}×/yr)\n"
        f"Equity win rate baseline: {ref['eq_win_rate']:.0f}%  EV: +{ref['eq_ev']:.2f}%"
    )

    # ── MSG 2: Exact spread setup ──────────────────────────────────────────────
    m2 = (
        f"🐂 <b>BULL PUT SPREAD SETUP — {ticker}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Spot price:  <code>${spot:.2f}</code>\n"
        f"Expiry:      <b>{expiry.strftime('%a %d %b %Y')}</b>  ({dte} DTE)\n"
        f"\n"
        f"LEG 1 → SELL put  <code>${spread['K_sell']}</code>  "
        f"({(spread['K_sell']/spot - 1)*100:+.1f}% from spot)\n"
        f"LEG 2 → BUY  put  <code>${spread['K_buy']}</code>  "
        f"({(spread['K_buy']/spot - 1)*100:+.1f}% from spot)\n"
        f"Width:             <code>${spread['width']}</code>\n"
        f"\n"
        f"Credit target:     <b>~${cr:.2f}</b>  ({spread['credit_pct_width']:.1f}% of width)\n"
        f"Min acceptable:    ${spread['width']*0.20:.2f}  (20% of width)\n"
        f"{'✅ Credit OK — proceed' if spread['credit_pct_width'] >= 20 else '⚠️ Credit thin — check live chain'}\n"
        f"\n"
        f"Breakeven at expiry:  <code>${spread['breakeven']:.2f}</code>  "
        f"({spread['breakeven_pct_from_spot']:+.1f}% from spot)\n"
        f"Short put delta:      {spread['delta_short']:.3f}  "
        f"(prob ITM at expiry ≈ {abs(spread['delta_short'])*100:.0f}%)"
    )

    # ── MSG 3: Expected outcomes ───────────────────────────────────────────────
    m3 = (
        f"📈 <b>EXPECTED OUTCOMES</b>  ({ref['n_signals']} backtested signals, 9yr)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Overall win rate:        <b>{ref['bps_win_rate']:.0f}%</b>\n"
        f"Win rate at IV {iv:.0f}%:     <b>{wr_regime:.0f}%</b>  ← current regime\n"
        f"EV at IV {iv:.0f}%:           <b>+{ev_regime:.1f}%</b> of width\n"
        f"\n"
        f"<b>Average win:</b>   +{ref['bps_avg_win']:.1f}%  = <b>+${avg_win_d:,.0f}</b>/contract\n"
        f"<b>Median win:</b>    +{ref['bps_median']:.1f}%  = <b>+${median_d:,.0f}</b>/contract\n"
        f"<b>Best 1-in-20:</b>  +{ref['bps_p95']:.1f}%  = <b>+${p95_d:,.0f}</b>/contract\n"
        f"<b>Max observed:</b>  +{ref['bps_max_win']:.1f}%  = <b>+${max_win_d:,.0f}</b>/contract\n"
        f"\n"
        f"<b>Average loss:</b>  {ref['bps_avg_loss']:.1f}%  = <b>${avg_loss_d:,.0f}</b>/contract\n"
        f"<b>Median loss:</b>   (see distribution below)\n"
        f"<b>Worst 1-in-20:</b> {ref['bps_p5']:.1f}%  = <b>${p5_d:,.0f}</b>/contract"
    )

    # ── MSG 4: Full return distribution ───────────────────────────────────────
    m4 = (
        f"📊 <b>RETURN DISTRIBUTION</b>  (% of spread width, per contract)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"          % of width   ${w} spread   on ${w*100} notional\n"
        f"P95 win:  +{ref['bps_p95']:>5.1f}%      +${p95_d:>6,.0f}       best 1-in-20\n"
        f"P75:      +{ref['bps_p75']:>5.1f}%      +${p75_d:>6,.0f}\n"
        f"Median:   +{ref['bps_median']:>5.1f}%      +${median_d:>6,.0f}       typical trade\n"
        f"P25:      {ref['bps_p25']:>+6.1f}%      ${p25_d:>+6,.0f}\n"
        f"P5 loss:  {ref['bps_p5']:>+6.1f}%      ${p5_d:>+6,.0f}       worst 1-in-20\n"
        f"\n"
        f"Max possible win:   +{ref['bps_max_win']:.1f}%  = +${max_win_d:,.0f}\n"
        f"  (keep full credit, both puts expire worthless)\n"
        f"Max possible loss:  −{(1 - cr/w)*100:.1f}%  = −${max_loss_d:,.0f}\n"
        f"  (spread fully in-the-money at expiry: width − credit)\n"
        f"\n"
        f"Equity comparison (holding stock):\n"
        f"  Win rate: {ref['eq_win_rate']:.0f}%   Avg EV: +{ref['eq_ev']:.2f}%\n"
        f"  Spread wins more often ({ref['bps_win_rate']:.0f}% vs {ref['eq_win_rate']:.0f}%) "
        f"by collecting IV premium"
    )

    # ── MSG 5: Risk scenarios ─────────────────────────────────────────────────
    T       = dte / 252
    iv_exit = (iv / 100) * 0.75    # fraction, with 25% IV crush
    scens = [
        ("Avg loss trade  (stock −2.2%)", spot * 0.978),
        ("Hard down       (stock −5%)",   spot * 0.950),
        ("⚠️ Flash crash  (stock −10%)",  spot * 0.900),
    ]
    risk_lines = []
    for label, S5 in scens:
        p_sell_x = _bs_put(S5, spread["K_sell"], max(T - 5/252, 0.001), RFREE, iv_exit)
        p_buy_x  = _bs_put(S5, spread["K_buy"],  max(T - 5/252, 0.001), RFREE, iv_exit)
        pnl_w    = (cr - (p_sell_x - p_buy_x)) / w * 100
        pnl_usd  = (cr - (p_sell_x - p_buy_x)) * 100
        risk_lines.append(f"  {label}: {pnl_w:+.1f}% (${pnl_usd:+,.0f})")

    m5 = (
        f"⚠️ <b>RISK SCENARIOS</b>  (IV crush −25%, 5 days held)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        + "\n".join(risk_lines) +
        f"\n\n"
        f"Theoretical max loss:  <b>−${max_loss_d:,.0f}</b> per contract\n"
        f"  = (${w} width − ${cr:.2f} credit) × 100 shares\n"
        f"\n"
        f"<b>Stop-loss rule:</b> Close if spread costs "
        f"${cr*2:.2f}+ to buy back (2× credit paid)"
    )

    # ── MSG 6: Sizing + exact order entry ────────────────────────────────────
    def _contracts(pf): return max(1, int(ref["hk"] * pf * ref["eq_avg_loss_pct"] / 100 / (spread["max_loss"] * 100)))
    m6 = (
        f"📐 <b>SIZING + HOW TO PLACE THE ORDER</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Risk budget</b> = {ref['hk']*100:.0f}% × portfolio × {ref['eq_avg_loss_pct']:.1f}% avg-loss\n"
        f"  $100k → budget ${ref['hk']*100_000*ref['eq_avg_loss_pct']/100:,.0f} → "
        f"<b>{_contracts(100_000)} contract(s)</b>\n"
        f"  $250k → budget ${ref['hk']*250_000*ref['eq_avg_loss_pct']/100:,.0f} → "
        f"<b>{_contracts(250_000)} contract(s)</b>\n"
        f"  $500k → budget ${ref['hk']*500_000*ref['eq_avg_loss_pct']/100:,.0f} → "
        f"<b>{_contracts(500_000)} contract(s)</b>\n"
        f"\n"
        f"<b>Exact order steps (tomorrow 9:45–10:00 AM ET):</b>\n"
        f"1. Open {ticker} options chain in your broker\n"
        f"2. Select expiry: <b>{expiry.strftime('%d %b %Y')}</b>\n"
        f"3. Choose order type: <b>Sell Vertical</b> (credit spread)\n"
        f"4. SELL ${spread['K_sell']} put  /  BUY ${spread['K_buy']} put\n"
        f"5. Enter as LIMIT at the <b>midpoint</b> of bid/ask\n"
        f"6. Confirm credit shown ≥ ${spread['width']*0.20:.2f} "
        f"(need ≥20% of ${spread['width']} width)\n"
        f"7. Max contracts: {_contracts(100_000)} (at $100k portfolio)\n"
        f"\n"
        f"<b>Trade management:</b>\n"
        f"  ✅ Take profit: close when spread costs ${cr*0.5:.2f} to buy back\n"
        f"     (50% of max profit captured)\n"
        f"  ⏰ Time exit: Day 5 close — {(datetime.date.today() + datetime.timedelta(days=7)).strftime('%d %b')}\n"
        f"  🛑 Stop loss: close if buy-back costs ${cr*2:.2f}+ (2× credit)\n"
        f"  📅 Earnings: check {ticker} has no earnings in next 7 days\n"
        f"\n"
        f"<b>Why it works at this signal:</b>\n"
        f"  1. {wr_regime:.0f}% historical win rate at IV={iv:.0f}% (elevated fear)\n"
        f"  2. IV crush adds profit as market recovers (you're short vega)\n"
        f"  3. Theta decays the put value every day you hold\n"
        f"  4. Breakeven at {spread['breakeven_pct_from_spot']:+.1f}% — stock can drop "
        f"further and you still profit"
    )

    parts = [m1, m2, m3, m4, m5, m6]

    # Alt strategy note when IV is low
    if strategy in ("long_call", "either"):
        m7 = (
            f"📞 <b>ALTERNATIVE: BULL CALL SPREAD</b>  (low IV env)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"BUY  ${bcs['K_buy']} call / SELL ${bcs['K_sell']} call — 35 DTE\n"
            f"Debit: ~${bcs['debit']:.2f}  ({bcs['debit_pct_width']:.1f}% of ${bcs['width']} width)\n"
            f"Max gain: ${bcs['max_gain']:.2f}  |  Breakeven: +{bcs['breakeven_pct_from_spot']:.1f}%\n"
            f"Backtest: {ref['bcs_win_rate']:.0f}% win  EV +{ref['bcs_ev']:.1f}%\n"
            f"(SPY long ATM call EV = {ref['lc_ev']:+.2f}% — "
            f"{'❌ avoid' if ref['lc_ev'] < 0 else '✓ ok'})"
        )
        parts.append(m7)
    return parts


def _fmt_watch_result(ticker: str, pct: float, spot: float,
                      iv: float, iv_sym: str, ref: dict) -> str:
    remaining = SIGNAL_THRESH - pct
    regime_label, _ = _iv_regime(iv)
    proximity  = max(0.0, min(1.0, (20.0 - pct) / 20.0))
    bar_filled = int(proximity * 10)
    bar        = "█" * bar_filled + "░" * (10 - bar_filled)
    return (
        f"<b>{ticker}</b> — {ref['name']}\n"
        f"  Percentile:  <b>{pct:.1f}th</b>  [{bar}]\n"
        f"  Need:        &lt;5th pct  (need {remaining:.1f}pp more)\n"
        f"  IV ({iv_sym}): {iv:.1f}%  {regime_label}\n"
        f"  Spot:        ${spot:.2f}\n"
        f"  Status:      🟡 WATCHING — not yet at signal"
    )


# ── Public command handlers ────────────────────────────────────────────────────

def handle_options_command(arg: str = "") -> list[str]:
    """/options [qqq|spy|both]"""
    arg     = arg.strip().lower()
    tickers = {"qqq": ["QQQ"], "spy": ["SPY"]}.get(arg, ["QQQ", "SPY"])

    syms = tickers + ["^VIX", "^VXN", "^VIX9D"]
    data = _download(syms, period="18mo")
    parts: list[str] = []
    signal_found = False

    for ticker in tickers:
        ref   = REF[ticker]
        close = data.get(ticker)
        if close is None or len(close) < RSI_LOOKBACK + 30:
            parts.append(f"❌ {ticker}: insufficient data"); continue
        spot = float(close.iloc[-1])
        pct  = _rsi_ma_pct(close)
        if pct is None:
            parts.append(f"❌ {ticker}: could not compute percentile"); continue

        iv_ser = data.get(ref["iv_sym"])
        iv     = _iv_level(iv_ser) or 20.0
        vix9d  = _iv_level(data.get("^VIX9D")) or iv
        vix30  = _iv_level(data.get("^VIX"))   or iv
        iv_short = iv * (vix9d / vix30) if vix30 > 0 else iv

        expiry = _nearest_friday(target_days=10)
        dte    = (expiry - datetime.date.today()).days

        iv_frac = iv_short / 100.0
        spread  = _price_bull_put_spread(spot, iv_frac, dte)
        bcs     = _price_bull_call_spread(spot, iv / 100.0)

        if pct < SIGNAL_THRESH:
            signal_found = True
            parts.extend(_fmt_options_result(
                ticker, pct, spot, iv_short, ref["iv_sym"],
                spread, bcs, dte, expiry, ref
            ))
            _log_signal({
                "date": datetime.date.today().isoformat(),
                "ticker": ticker, "pct": round(pct, 2),
                "spot": round(spot, 2), "iv": round(iv_short, 2),
                "K_sell": spread["K_sell"], "K_buy": spread["K_buy"],
                "dte": dte, "expiry": expiry.isoformat(),
                "credit": round(spread["credit"], 2),
                "width": spread["width"],
                "max_loss": round(spread["max_loss"], 2),
                "regime": _iv_regime(iv)[0], "status": "signal_active",
            })
        else:
            parts.append(_fmt_watch_result(ticker, pct, spot, iv_short, ref["iv_sym"], ref))
            parts.append(
                f"💡 <b>Hypothetical setup if {ticker} were at signal NOW:</b>\n"
                f"  Sell ${spread['K_sell']} put / Buy ${spread['K_buy']} put  ({dte} DTE)\n"
                f"  Credit ~${spread['credit']:.2f}  |  Width ${spread['width']}  |  "
                f"Max loss ${spread['max_loss']:.2f}/sh\n"
                f"  Credit/Width: {spread['credit_pct_width']:.1f}%  "
                f"{'✅' if spread['credit_pct_width'] >= 20 else '⚠️ thin — IV not elevated yet (normal at no-signal)'}"
            )

    if not signal_found and parts:
        parts.insert(0, "📭 <b>No active options signal right now.</b>\nCurrent status:")
    return parts or ["❌ Could not process /options."]


def handle_iv_command() -> list[str]:
    """/iv — VIX / VXN / VIX9D dashboard. Returns plain-text-safe HTML parts."""
    # Download separately to avoid yfinance aligning on shortest series
    iv_data  = _download(["^VIX", "^VXN", "^VIX9D"], period="2y")
    eq_data  = _download(["QQQ", "SPY"], period="18mo")

    vix   = _iv_level(iv_data.get("^VIX"))
    vxn   = _iv_level(iv_data.get("^VXN"))
    vix9d = _iv_level(iv_data.get("^VIX9D"))

    # 30-day stats for each
    def _ctx(ser, val):
        if ser is not None and len(ser) >= 30:
            s = ser.iloc[-30:]
            return f"{val:.1f}%  (30d avg {s.mean():.1f} / lo {s.min():.1f} / hi {s.max():.1f})"
        return f"{val:.1f}%" if val else "N/A"

    vix_ctx  = _ctx(iv_data.get("^VIX"),  vix  or 0)
    vxn_ctx  = _ctx(iv_data.get("^VXN"),  vxn  or 0)
    v9d_str  = f"{vix9d:.1f}%" if vix9d else "N/A"

    # Regime labels — plain text, no HTML entities in these strings
    def _regime_plain(iv_pct: float) -> str:
        if iv_pct < 15:   return "LOW (below 15%) — Long Call preferred"
        elif iv_pct < 20: return "MID-LOW (15-20%) — Either spread works"
        elif iv_pct < 25: return "MID (20-25%) — Bull Put Spread good"
        else:             return "HIGH (above 25%) — Bull Put Spread best"

    # Term structure note — plain text only
    term = ""
    if vix9d and vix:
        diff = vix9d - vix
        if   diff > 2:  term = f"VIX9D above VIX by {diff:.1f}pp — front-month fear elevated"
        elif diff < -2: term = f"VIX9D below VIX by {abs(diff):.1f}pp — normal contango"
        else:           term = f"VIX9D approx VIX ({vix9d:.1f}%) — normal term structure"

    # RSI-MA percentiles
    spy_pct = _rsi_ma_pct(eq_data.get("SPY")) if "SPY" in eq_data else None
    qqq_pct = _rsi_ma_pct(eq_data.get("QQQ")) if "QQQ" in eq_data else None

    def _pct_txt(t, p):
        if p is None: return f"{t} RSI-MA: n/a"
        icon = "SIGNAL ACTIVE" if p < 5 else "CLOSE" if p < 8 else "watching" if p < 15 else "normal"
        return f"{t}: {p:.1f}th pct ({icon})"

    # Build as separate small messages to avoid any single-message HTML rejection
    msg1 = (
        "<b>IV DASHBOARD</b>  "
        + datetime.datetime.now().strftime("%d %b %Y %H:%M") + " UTC\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "\n"
        "<b>S&amp;P 500 (SPY options)</b>\n"
        f"  VIX  30d:  <b>{vix_ctx}</b>\n"
        f"  VIX9D 9d:  <b>{v9d_str}</b>\n"
        f"  Regime:    {_regime_plain(vix or 20)}\n"
        "\n"
        "<b>NASDAQ 100 (QQQ options)</b>\n"
        f"  VXN  30d:  <b>{vxn_ctx}</b>\n"
        f"  Regime:    {_regime_plain(vxn or 20)}\n"
        "\n"
        "<b>Term structure</b>\n"
        f"  {term}\n"
        "  VIX9D matched to 10 DTE puts"
    )

    msg2 = (
        "<b>Strategy guide by IV level</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  Above 25%:  Bull Put Spread best (sell expensive IV)\n"
        "  20 to 25%:  Bull Put Spread good\n"
        "  15 to 20%:  Either spread works\n"
        "  Below 15%:  Long ATM Call preferred (low crush risk)\n"
        "\n"
        "<b>Historical context at signal entry</b>\n"
        "  Median VXN at QQQ signal: 24.2%  (MID 20-25%)\n"
        "  Median VIX at SPY signal: 21.7%  (MID 20-25%)\n"
        "  Median IV crush over 5-day hold: 3.2 to 3.4pp\n"
        "\n"
        "<b>RSI-MA signal watch</b>\n"
        f"  {_pct_txt('QQQ', qqq_pct)}\n"
        f"  {_pct_txt('SPY', spy_pct)}\n"
        "  Signal at below 5th pct  |  /options for full setup"
    )

    return [msg1, msg2]


def handle_optwatch_command() -> list[str]:
    """/optwatch — percentile status + hypothetical setup."""
    data   = _download(["QQQ", "SPY", "^VIX", "^VXN", "^VIX9D"], period="18mo")
    vix30  = _iv_level(data.get("^VIX")) or 20.0
    vix9d  = _iv_level(data.get("^VIX9D")) or vix30

    parts = [f"👁 <b>OPTIONS WATCH</b>  —  {datetime.date.today()}\n━━━━━━━━━━━━━━━━━━━━━━━━"]
    expiry = _nearest_friday(10)
    dte    = (expiry - datetime.date.today()).days

    for ticker in ["QQQ", "SPY"]:
        ref    = REF[ticker]
        close  = data.get(ticker)
        if close is None: continue
        spot   = float(close.iloc[-1])
        pct    = _rsi_ma_pct(close)
        if pct is None: continue

        iv_ser   = data.get("^VXN") if ticker == "QQQ" else data.get("^VIX")
        iv30     = _iv_level(iv_ser) or 20.0
        iv_short = iv30 * (vix9d / vix30) if vix30 > 0 else iv30
        regime_label, _ = _iv_regime(iv_short)
        spread   = _price_bull_put_spread(spot, iv_short / 100.0, dte)

        if pct < SIGNAL_THRESH:
            status_icon = "🔴"; status_text = "SIGNAL ACTIVE — /options for full setup"
        elif pct < 8:
            status_icon = "🟠"; status_text = f"CLOSE — {pct - SIGNAL_THRESH:.1f}pp above threshold"
        elif pct < 15:
            status_icon = "🟡"; status_text = f"WATCHING — {pct - SIGNAL_THRESH:.1f}pp from signal"
        else:
            status_icon = "⚪"; status_text = "Normal"

        filled = min(10, int((SIGNAL_THRESH / max(pct, 0.1)) * 10))
        bar    = "🟥" * filled + "⬜" * (10 - filled)

        parts.append(
            f"\n{status_icon} <b>{ticker}</b>  ({ref['name']})\n"
            f"  RSI-MA: <b>{pct:.1f}th pct</b>  {bar}\n"
            f"  Signal: &lt;5th pct  |  Gap: {max(0,pct-SIGNAL_THRESH):.1f}pp\n"
            f"  {status_text}\n"
            f"\n"
            f"  IV ({ref['iv_sym']}): <b>{iv_short:.1f}%</b>  {regime_label}\n"
            f"  Spot: ${spot:.2f}  |  Expiry: {expiry.strftime('%d %b')} ({dte}d)\n"
            f"\n"
            f"  📋 Setup if signal now:\n"
            f"     Sell ${spread['K_sell']} put / Buy ${spread['K_buy']} put\n"
            f"     Credit ~${spread['credit']:.2f}  |  Width ${spread['width']}\n"
            f"     Max loss: ${spread['max_loss']:.2f}/sh  "
            f"({'✅ ' if spread['credit_pct_width'] >= 20 else '⚠️ thin — '}credit {spread['credit_pct_width']:.1f}% of width)"
        )

    parts.append(
        f"\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📚 <b>Backtested reference</b>  (RSI-MA only, 9yr)\n"
        f"  QQQ: {REF['QQQ']['bps_win_rate']:.0f}% win  EV +{REF['QQQ']['bps_ev']:.1f}%  "
        f"(N={REF['QQQ']['n_signals']}, ~{REF['QQQ']['signals_per_year']:.1f}×/yr)\n"
        f"  SPY: {REF['SPY']['bps_win_rate']:.0f}% win  EV +{REF['SPY']['bps_ev']:.1f}%  "
        f"(N={REF['SPY']['n_signals']}, ~{REF['SPY']['signals_per_year']:.1f}×/yr)\n"
        f"  High IV (&gt;25%): {REF['QQQ']['bps_wr_high']:.0f}%/{REF['SPY']['bps_wr_high']:.0f}% win (QQQ/SPY)"
    )
    return parts


def handle_optwatch_brief() -> str:
    """
    Multi-line options + IV summary for /update daily snapshot.
    Shows VIX, VXN, VIX9D, and RSI-MA signal status.
    """
    try:
        iv_data = _download(["^VIX", "^VXN", "^VIX9D"], period="2y")
        eq_data = _download(["QQQ", "SPY"], period="18mo")

        vix   = _iv_level(iv_data.get("^VIX"))
        vxn   = _iv_level(iv_data.get("^VXN"))
        vix9d = _iv_level(iv_data.get("^VIX9D"))

        # 30d context
        def _30d(ser, val):
            if ser is not None and len(ser) >= 30:
                s = ser.iloc[-30:]
                return f"{val:.1f}%  (avg {s.mean():.1f} / hi {s.max():.1f})"
            return f"{val:.1f}%" if val else "n/a"

        vix_str  = _30d(iv_data.get("^VIX"),  vix  or 0)
        vxn_str  = _30d(iv_data.get("^VXN"),  vxn  or 0)
        v9d_str  = f"{vix9d:.1f}%" if vix9d else "n/a"

        # Regime
        def _regime_icon(iv_pct):
            if iv_pct < 15:   return "🟢 Low"
            elif iv_pct < 20: return "🟡 Mid-Low"
            elif iv_pct < 25: return "🟠 Mid"
            else:             return "🔴 High"

        # RSI-MA percentiles
        active = False
        pct_lines = []
        for ticker in ["QQQ", "SPY"]:
            close = eq_data.get(ticker)
            pct   = _rsi_ma_pct(close) if close is not None else None
            if pct is None:
                pct_lines.append(f"{ticker}: n/a")
                continue
            if pct < SIGNAL_THRESH:
                active = True
                icon = "🔴"
            elif pct < 8:
                icon = "🟠"
            elif pct < 15:
                icon = "🟡"
            else:
                icon = "⚪"
            pct_lines.append(f"{icon} {ticker} {pct:.1f}th pct")

        signal_line = "🔴 <b>OPTIONS SIGNAL ACTIVE — /options</b>" if active else "👁 <b>Options watch</b>"

        msg = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>Volatility  /  Options Watch</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"VIX  (S&amp;P 30d):   <b>{vix_str}</b>  {_regime_icon(vix or 20)}\n"
            f"VXN  (QQQ 30d):   <b>{vxn_str}</b>  {_regime_icon(vxn or 20)}\n"
            f"VIX9D (9-day):    <b>{v9d_str}</b>\n"
            f"\n"
            f"{signal_line}\n"
            f"  {pct_lines[0] if pct_lines else ''}"
            + (f"  |  {pct_lines[1]}" if len(pct_lines) > 1 else "") +
            f"\n"
            f"  Signal at below 5th pct  |  /iv for regime detail"
        )
        return msg
    except Exception as exc:
        return f"👁 Options watch: error ({exc})"


def handle_optbacktest_command() -> list[str]:
    """/optbacktest — full historical statistics table."""
    parts = []

    header = (
        f"📋 <b>OPTIONS BACKTEST REFERENCE</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Signal: RSI-MA &lt;5th pct (no COV filter)\n"
        f"Strategy: Bull Put Spread −2%/−5%, 10 DTE\n"
        f"IV source: ^VXN (QQQ)  ^VIX (SPY)\n"
        f"Period: 9 years  |  Cooldown: 10 bars"
    )
    parts.append(header)

    for ticker, ref in REF.items():
        w_example = 14   # $14 spread on QQQ
        msg = (
            f"\n<b>{ticker} — {ref['name']}</b>  (N={ref['n_signals']}, ~{ref['signals_per_year']:.1f}×/yr)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Bull Put Spread  −2%/−5%  10 DTE</b>\n"
            f"\n"
            f"Win rate (overall):    <b>{ref['bps_win_rate']:.0f}%</b>\n"
            f"Win rate IV 15-25%:   <b>{ref['bps_wr_mid']:.0f}%</b>\n"
            f"Win rate IV &gt;25%:     <b>{ref['bps_wr_high']:.0f}%</b>\n"
            f"EV per trade:          <b>+{ref['bps_ev']:.1f}%</b> of spread width\n"
            f"\n"
            f"<b>Return distribution</b>  (on ${w_example} wide spread)\n"
            f"  Max win:    +{ref['bps_max_win']:.1f}%  = +${ref['bps_max_win']/100*w_example*100:,.0f}/contract\n"
            f"  P95:        +{ref['bps_p95']:.1f}%  = +${ref['bps_p95']/100*w_example*100:,.0f}/contract\n"
            f"  P75:        +{ref['bps_p75']:.1f}%  = +${ref['bps_p75']/100*w_example*100:,.0f}/contract\n"
            f"  Median:     +{ref['bps_median']:.1f}%  = +${ref['bps_median']/100*w_example*100:,.0f}/contract\n"
            f"  Avg win:    +{ref['bps_avg_win']:.1f}%  = +${ref['bps_avg_win']/100*w_example*100:,.0f}/contract\n"
            f"  P25:        {ref['bps_p25']:+.1f}%\n"
            f"  Avg loss:   {ref['bps_avg_loss']:.1f}%  = ${ref['bps_avg_loss']/100*w_example*100:,.0f}/contract\n"
            f"  P5:         {ref['bps_p5']:.1f}%   = ${ref['bps_p5']/100*w_example*100:,.0f}/contract\n"
            f"\n"
            f"<b>vs equity baseline</b>\n"
            f"  Equity win rate: {ref['eq_win_rate']:.0f}%  EV: +{ref['eq_ev']:.2f}%\n"
            f"  Spread win rate: {ref['bps_win_rate']:.0f}%  (+{ref['bps_win_rate']-ref['eq_win_rate']:.0f}pp higher)\n"
            f"\n"
            f"<b>Other strategies on same signal</b>\n"
            f"  Bull Call Spread: {ref['bcs_win_rate']:.0f}% win  EV +{ref['bcs_ev']:.1f}%\n"
            f"  Long ATM Call:    {ref['lc_win_rate']:.0f}% win  EV {ref['lc_ev']:+.2f}%"
            + (f"  ❌ negative EV — avoid" if ref['lc_ev'] < 0 else "")
        )
        parts.append(msg)
    return parts


def handle_optlog_command(n: int = 10) -> list[str]:
    """/optlog [n] — show last n logged option signals."""
    if not LOG_PATH.exists():
        return ["📭 No option signals logged yet."]
    try:
        log = json.loads(LOG_PATH.read_text())
    except Exception:
        return ["❌ Could not read signal log."]
    if not log:
        return ["📭 No option signals logged yet."]

    recent = log[-n:][::-1]
    lines  = [f"📋 <b>Last {len(recent)} Option Signals</b>\n━━━━━━━━━━━━━━━━━━━━━━━━"]
    for e in recent:
        lines.append(
            f"\n<b>{e.get('date','?')}</b>  {e.get('ticker','?')}\n"
            f"  Pct: {e.get('pct','?'):.1f}th  |  IV: {e.get('iv','?'):.1f}%\n"
            f"  Spot: ${e.get('spot','?'):.2f}  |  Sell ${e.get('K_sell','?')} / Buy ${e.get('K_buy','?')}\n"
            f"  Credit: ${e.get('credit','?'):.2f}  |  Width: ${e.get('width','?')}  |  "
            f"Max loss: ${e.get('max_loss','?'):.2f}/sh\n"
            f"  Expiry: {e.get('expiry','?')} ({e.get('dte','?')} DTE)  |  {e.get('regime','?')}"
        )
    lines.append(f"\n<i>Full log: docs/OPTIONS_SIGNAL_LOG.md</i>")
    return ["\n".join(lines)]
