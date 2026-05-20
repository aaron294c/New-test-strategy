#!/usr/bin/env python3
"""
Options signal handler for Telegram — RSI-MA <5th pct (no COV required for QQQ/SPY).

Commands:
  /options        — live scan: is there a bull-put-spread entry right now?
  /iv             — current VIX / VXN / VIX9D dashboard
  /optwatch       — current RSI-MA percentile levels + distance to signal

Pattern: follows the exact /sizing / /variants pattern.
  - Returns a list[str] (each element sent as a separate Telegram message)
  - Caller sends "⏳ …" first, then sends each returned string
  - NO webhooks, NO async, NO frameworks — pure stdlib + yfinance
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

# ── Verified backtest reference values (from OPTIONS_RSIMA_ANALYSIS.md) ───────
# 42 QQQ signals / 47 SPY signals over 9 years, bull put spread -2%/-5% 10 DTE

REF = {
    "QQQ": {
        "name": "NASDAQ 100 ETF", "iv_sym": "^VXN",
        "n_signals": 42, "hk": 0.20, "eq_avg_loss_pct": 2.86,
        "bps_win_rate": 78.6, "bps_ev": 11.3, "bps_avg_win": 20.5,
        "bps_avg_loss": -22.2, "bps_p5": -36.8, "bps_median": 16.9, "bps_p95": 31.8,
        "eq_win_rate": 69.0, "eq_ev": 1.21,
        # IV regime win rates
        "bps_wr_mid": 72, "bps_wr_high": 88,
        "bcs_win_rate": 64.3, "bcs_ev": 14.6,
        "lc_win_rate": 52.4, "lc_ev": 7.6,
    },
    "SPY": {
        "name": "S&P 500 ETF", "iv_sym": "^VIX",
        "n_signals": 47, "hk": 0.20, "eq_avg_loss_pct": 2.43,
        "bps_win_rate": 89.4, "bps_ev": 12.4, "bps_avg_win": 17.8,
        "bps_avg_loss": -32.7, "bps_p5": -31.4, "bps_median": 15.9, "bps_p95": 33.1,
        "eq_win_rate": 70.2, "eq_ev": 0.88,
        "bps_wr_mid": 93, "bps_wr_high": 88,
        "bcs_win_rate": 66.0, "bcs_ev": 13.3,
        "lc_win_rate": 51.1, "lc_ev": -0.55,   # NEGATIVE — do not use
    },
}

RSI_LOOKBACK   = 252
SIGNAL_THRESH  = 5.0
RFREE          = 0.053
LOG_PATH       = _ROOT / "docs" / "options_signal_log.json"
LOG_MD_PATH    = _ROOT / "docs" / "OPTIONS_SIGNAL_LOG.md"


# ── Black-Scholes helpers ──────────────────────────────────────────────────────

def _bs_put(S, K, T, r, sigma):
    if T <= 0 or sigma <= 0: return max(K - S, 0)
    d1 = (math.log(S/K) + (r + .5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    from scipy.stats import norm
    return K*math.exp(-r*T)*norm.cdf(-d2) - S*norm.cdf(-d1)

def _bs_call(S, K, T, r, sigma):
    if T <= 0 or sigma <= 0: return max(S - K, 0)
    d1 = (math.log(S/K) + (r + .5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    from scipy.stats import norm
    return S*norm.cdf(d1) - K*math.exp(-r*T)*norm.cdf(d2)

def _bs_put_delta(S, K, T, r, sigma):
    if T <= 0: return -1.0 if S < K else 0.0
    d1 = (math.log(S/K) + (r + .5*sigma**2)*T) / (sigma*math.sqrt(T))
    from scipy.stats import norm
    return norm.cdf(d1) - 1.0


# ── Data helpers ───────────────────────────────────────────────────────────────

def _download(tickers: list[str], period: str = "18mo") -> dict[str, pd.Series]:
    """Download close prices, returns {ticker: Series}."""
    raw = yf.download(tickers, period=period, interval="1d",
                      progress=False, auto_adjust=True, threads=True)
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"]
    else:
        close = raw[["Close"]]
        if tickers:
            close.columns = [tickers[0]]
    out = {}
    for t in tickers:
        if t in close.columns:
            s = close[t].dropna()
            if len(s) > 10:
                out[t] = s
    return out


def _rsi_ma_pct(close: pd.Series) -> Optional[float]:
    """Current RSI-MA percentile (0-100). None if not enough data."""
    if len(close) < RSI_LOOKBACK + 30:
        return None
    rma = calculate_rsi_ma(close)
    window = rma.dropna().iloc[-(RSI_LOOKBACK):]
    if len(window) < RSI_LOOKBACK:
        return None
    current = window.iloc[-1]
    below   = (window.iloc[:-1] < current).sum()
    return float(below / (len(window) - 1) * 100)


def _iv_level(ser: pd.Series) -> Optional[float]:
    """Latest value from a VIX-type series, as percentage (e.g. 21.3)."""
    if ser is None or ser.empty:
        return None
    return float(ser.dropna().iloc[-1])


def _nearest_friday(target_days: int = 10) -> datetime.date:
    """Return the Friday closest to `target_days` calendar days from today."""
    today = datetime.date.today()
    best  = None
    best_diff = 9999
    for offset in range(5, 18):
        d = today + datetime.timedelta(days=offset)
        if d.weekday() == 4:  # Friday
            diff = abs(offset - target_days)
            if diff < best_diff:
                best_diff = diff
                best = d
    return best or (today + datetime.timedelta(days=10))


def _iv_regime(iv_pct: float) -> tuple[str, str]:
    """Returns (label, strategy_advice)."""
    if iv_pct < 15:
        return ("🟢 LOW (<15%)", "Long ATM Call preferred (low crush risk). Put spread credit thin.")
    elif iv_pct < 20:
        return ("🟡 MID-LOW (15-20%)", "Bull Put Spread or Bull Call Spread. Either works.")
    elif iv_pct < 25:
        return ("🟠 MID (20-25%)", "Bull Put Spread ★★ — good premium, decent crush incoming.")
    else:
        return ("🔴 HIGH (>25%)", "Bull Put Spread ★★★ — sell expensive IV. Best regime for spread.")


# ── Options pricing for a spread ──────────────────────────────────────────────

def _price_bull_put_spread(S: float, iv: float, dte: int) -> dict:
    """Price a -2%/-5% bull put spread. Returns dict with credit, width, etc."""
    K_sell = round(S * 0.98)     # short put at -2%, rounded to $1
    K_buy  = round(S * 0.95)     # long put at -5%, rounded to $1
    T      = dte / 252
    p_sell = _bs_put(S, K_sell, T, RFREE, iv)
    p_buy  = _bs_put(S, K_buy,  T, RFREE, iv)
    credit = p_sell - p_buy
    width  = K_sell - K_buy
    d_sell = _bs_put_delta(S, K_sell, T, RFREE, iv)
    return {
        "K_sell": K_sell, "K_buy": K_buy, "T": T,
        "credit": credit, "width": width,
        "max_loss": width - credit,
        "credit_pct_width": credit / width * 100 if width > 0 else 0,
        "breakeven": K_sell - credit,
        "breakeven_pct_from_spot": (K_sell - credit - S) / S * 100,
        "delta_short": d_sell,
    }


def _price_bull_call_spread(S: float, iv: float, dte: int) -> dict:
    """Price an ATM/+3% bull call spread."""
    K_buy  = round(S)
    K_sell = round(S * 1.03)
    T      = dte / 252
    c_buy  = _bs_call(S, K_buy,  T, RFREE, iv)
    c_sell = _bs_call(S, K_sell, T, RFREE, iv)
    debit  = c_buy - c_sell
    width  = K_sell - K_buy
    return {
        "K_buy": K_buy, "K_sell": K_sell,
        "debit": debit, "width": width,
        "max_gain": width - debit,
        "debit_pct_width": debit / width * 100 if width > 0 else 0,
        "breakeven": K_buy + debit,
        "breakeven_pct_from_spot": debit / S * 100,
    }


# ── Signal log ────────────────────────────────────────────────────────────────

def _log_signal(entry: dict) -> None:
    """Append a signal entry to the JSON log and regenerate the MD file."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log: list = []
    if LOG_PATH.exists():
        try:
            log = json.loads(LOG_PATH.read_text())
        except Exception:
            log = []
    log.append(entry)
    LOG_PATH.write_text(json.dumps(log, indent=2, default=str))
    _rebuild_log_md(log)


def _rebuild_log_md(log: list) -> None:
    lines = [
        "# Options Signal Log — RSI-MA <5th Pct (QQQ/SPY)",
        "",
        f"*Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} UTC*",
        "",
        "| Date | Ticker | Pct | VIX/VXN | Spot | Setup | Credit | Width | Max Loss | Regime | Status |",
        "|------|--------|-----|---------|------|-------|--------|-------|----------|--------|--------|",
    ]
    for e in reversed(log[-50:]):   # show last 50, newest first
        setup = f"Sell ${e.get('K_sell','?')} / Buy ${e.get('K_buy','?')} {e.get('dte','?')} DTE"
        lines.append(
            f"| {e.get('date','?')} | {e.get('ticker','?')} | {e.get('pct','?'):.1f}th | "
            f"{e.get('iv','?'):.1f}% | ${e.get('spot','?'):.2f} | {setup} | "
            f"${e.get('credit','?'):.2f} | ${e.get('width','?')} | "
            f"${e.get('max_loss','?'):.2f} | {e.get('regime','?')} | {e.get('status','logged')} |"
        )
    LOG_MD_PATH.write_text("\n".join(lines) + "\n")


# ── Formatters ────────────────────────────────────────────────────────────────

def _fmt_options_result(ticker: str, pct: float, spot: float,
                        iv: float, iv_sym: str, spread: dict,
                        bcs: dict, dte: int, expiry: datetime.date,
                        ref: dict, portfolio: int = 100_000) -> list[str]:
    """Format the full options recommendation into Telegram message parts."""
    regime_label, regime_advice = _iv_regime(iv)

    # Determine primary strategy
    if iv < 15:
        primary  = "⚠️ LOW IV — Consider Long ATM Call instead"
        strategy = "long_call"
    elif iv < 20:
        primary  = "Bull Put Spread OR Bull Call Spread (either works)"
        strategy = "either"
    else:
        primary  = "Bull Put Spread ★★★"
        strategy = "bull_put_spread"

    # Signal strength
    if pct < 1.0:
        strength = "🔥 EXTREME (<1st pct)"
    elif pct < 2.0:
        strength = "⚡ VERY STRONG (1-2nd pct)"
    elif pct < 3.0:
        strength = "💪 STRONG (2-3rd pct)"
    else:
        strength = "✅ SIGNAL A (<5th pct)"

    # Dollar P&L examples from backtest (per 1 contract, 100 shares)
    w  = spread["width"]
    cr = spread["credit"]
    avg_win_d  = ref["bps_avg_win"]  / 100 * w * 100
    avg_loss_d = ref["bps_avg_loss"] / 100 * w * 100  # negative
    median_d   = ref["bps_median"]   / 100 * w * 100
    max_loss_d = spread["max_loss"]  * 100   # per contract

    # Sizing
    dollar_budget = ref["hk"] * portfolio * ref["eq_avg_loss_pct"] / 100
    contracts = max(1, int(dollar_budget / (spread["max_loss"] * 100)))

    # --- MESSAGE 1: Signal header ---
    m1 = (
        f"🔔 <b>OPTIONS SIGNAL — {ticker}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Signal:</b> RSI-MA below 5th percentile\n"
        f"Percentile:  <b>{pct:.1f}th</b>  {strength}\n"
        f"IV ({iv_sym}): <b>{iv:.1f}%</b>  {regime_label}\n"
        f"\n"
        f"🎯 <b>Primary:</b> {primary}\n"
        f"\n{regime_advice}"
    )

    # --- MESSAGE 2: Bull Put Spread setup ---
    m2 = (
        f"🐂 <b>BULL PUT SPREAD — {ticker}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Spot:        <code>${spot:.2f}</code>\n"
        f"📅 Expiry:   <b>{expiry.strftime('%a %d %b %Y')}</b> ({dte} DTE)\n"
        f"\n"
        f"SELL put:  <code>${spread['K_sell']}</code>  ({(spread['K_sell']/spot-1)*100:+.1f}% from spot)\n"
        f"BUY  put:  <code>${spread['K_buy']}</code>  ({(spread['K_buy']/spot-1)*100:+.1f}% from spot)\n"
        f"Width:     <code>${spread['width']}</code> spread\n"
        f"\n"
        f"Credit target:  <b>~${cr:.2f}</b>  ({spread['credit_pct_width']:.1f}% of width)\n"
        f"Min acceptable: ${spread['width']*0.20:.2f} (20% of width)\n"
        f"{'✅ Credit OK' if spread['credit_pct_width'] >= 20 else '⚠️ Low credit — consider skipping'}\n"
        f"\n"
        f"Breakeven at expiry: <code>${spread['breakeven']:.2f}</code>  "
        f"({spread['breakeven_pct_from_spot']:+.1f}% from spot)\n"
        f"Short put delta:    {spread['delta_short']:.3f}"
    )

    # --- MESSAGE 3: Expected outcomes ---
    wr_regime = ref["bps_wr_high"] if iv >= 25 else ref["bps_wr_mid"] if iv >= 15 else 50
    m3 = (
        f"📈 <b>EXPECTED OUTCOMES</b>  (backtested {ref['n_signals']} signals, 9yr)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Overall win rate:     <b>{ref['bps_win_rate']:.0f}%</b>\n"
        f"Win rate at IV {iv:.0f}%:  <b>{wr_regime:.0f}%</b>\n"
        f"EV per trade:         <b>+{ref['bps_ev']:.1f}%</b> of spread width\n"
        f"\n"
        f"Avg win:    +{ref['bps_avg_win']:.1f}% = <b>+${avg_win_d:,.0f}</b>/contract\n"
        f"Avg loss:   {ref['bps_avg_loss']:.1f}% = <b>${avg_loss_d:,.0f}</b>/contract\n"
        f"Median:     +{ref['bps_median']:.1f}% = <b>+${median_d:,.0f}</b>/contract\n"
        f"\n"
        f"P5  (worst 1-in-20): {ref['bps_p5']:.1f}%\n"
        f"P95 (best  1-in-20): +{ref['bps_p95']:.1f}%\n"
    )

    # --- MESSAGE 4: Risk scenarios ---
    # Based on actual max loss from spread
    scens = [
        ("Avg loss trade (stock -2.2%)", spot * 0.978, ""),
        ("Hard down   (stock -5%)",      spot * 0.950, ""),
        ("Flash crash (stock -10%)",     spot * 0.900, "⚠️"),
    ]
    risk_lines = []
    T = dte / 252
    iv_exit = (iv / 100) * 0.75   # iv is %, convert to fraction then apply 25% crush
    for label, S5, flag in scens:
        p_sell_x = _bs_put(S5, spread["K_sell"], max(T - 5/252, 0.001), RFREE, iv_exit)
        p_buy_x  = _bs_put(S5, spread["K_buy"],  max(T - 5/252, 0.001), RFREE, iv_exit)
        cost_close = p_sell_x - p_buy_x
        pnl_d = (cr - cost_close) / w * 100
        pnl_usd = (cr - cost_close) * 100
        risk_lines.append(f"{flag}{label}: {pnl_d:+.1f}% (${pnl_usd:+,.0f})")

    m4 = (
        f"⚠️ <b>RISK SCENARIOS</b>  (1 contract, IV crush -25%)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        + "\n".join(f"  {l}" for l in risk_lines) +
        f"\n\n"
        f"Max loss (theoretical):  <b>-${max_loss_d:,.0f}</b>  per contract\n"
        f"  = spread ${w} – credit ${cr:.2f} = ${spread['max_loss']:.2f} × 100 shares\n"
    )

    # --- MESSAGE 5: Sizing + management ---
    m5 = (
        f"📐 <b>SIZING</b>  (half-Kelly risk budget)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Formula: {ref['hk']*100:.0f}% (hK) × portfolio × {ref['eq_avg_loss_pct']:.1f}% (avg loss)\n"
        f"At $100k:   budget = <b>${ref['hk']*100_000*ref['eq_avg_loss_pct']/100:,.0f}</b> "
        f"→ <b>{max(1,int(ref['hk']*100_000*ref['eq_avg_loss_pct']/100/(spread['max_loss']*100))):d} contract(s)</b>\n"
        f"At $250k:   budget = <b>${ref['hk']*250_000*ref['eq_avg_loss_pct']/100:,.0f}</b> "
        f"→ <b>{max(1,int(ref['hk']*250_000*ref['eq_avg_loss_pct']/100/(spread['max_loss']*100))):d} contract(s)</b>\n"
        f"At $500k:   budget = <b>${ref['hk']*500_000*ref['eq_avg_loss_pct']/100:,.0f}</b> "
        f"→ <b>{max(1,int(ref['hk']*500_000*ref['eq_avg_loss_pct']/100/(spread['max_loss']*100))):d} contract(s)</b>\n"
        f"\n"
        f"⚙️ <b>MANAGEMENT</b>\n"
        f"  Entry:       Tomorrow 9:45–10:00 AM ET\n"
        f"  Take profit: Close at 50% of max profit\n"
        f"               (buy back spread for ${cr*0.5:.2f} or less)\n"
        f"  Time exit:   Day 5 regardless\n"
        f"  Stop loss:   Close if spread costs {cr*2:.2f}+ to close (2× credit)\n"
        f"  Earnings:    Check {ticker} earnings calendar — never hold through\n"
    )

    # --- Bull Call Spread as secondary (if IV < 20%) ---
    m6 = None
    if strategy in ("long_call", "either"):
        m6 = (
            f"📊 <b>BULL CALL SPREAD (Alt — lower IV)</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"BUY  call: <code>${bcs['K_buy']}</code> (ATM)  35 DTE\n"
            f"SELL call: <code>${bcs['K_sell']}</code> (+3%)  35 DTE\n"
            f"Debit: ~${bcs['debit']:.2f}  ({bcs['debit_pct_width']:.1f}% of ${bcs['width']} width)\n"
            f"Max gain: ${bcs['max_gain']:.2f}  Breakeven: +{bcs['breakeven_pct_from_spot']:.1f}%\n"
            f"\n"
            f"Backtest win rate: {ref['bcs_win_rate']:.0f}%  EV: +{ref['bcs_ev']:.1f}%\n"
            f"(Note: SPY long call EV = {ref['lc_ev']:+.2f}% — {'❌ avoid' if ref['lc_ev'] < 0 else '✓ ok'})"
        )

    parts = [m1, m2, m3, m4, m5]
    if m6:
        parts.append(m6)
    return parts


def _fmt_watch_result(ticker: str, pct: float, spot: float,
                      iv: float, iv_sym: str, ref: dict) -> str:
    """Format a 'not at signal yet, watching' status line."""
    remaining = SIGNAL_THRESH - pct
    regime_label, _ = _iv_regime(iv)
    # Bar fills toward right as pct drops toward 0 (closer to signal)
    proximity = max(0.0, min(1.0, (20.0 - pct) / 20.0))
    bar_filled = int(proximity * 10)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)
    return (
        f"<b>{ticker}</b> — {ref['name']}\n"
        f"  Percentile:  <b>{pct:.1f}th</b>  [{bar}]\n"
        f"  Need:        <5th pct  (need -{remaining:.1f}pp more)\n"
        f"  IV ({iv_sym}): {iv:.1f}%  {regime_label}\n"
        f"  Spot:        ${spot:.2f}\n"
        f"  Status:      🟡 WATCHING — not yet at signal"
    )


# ── Public command handlers ────────────────────────────────────────────────────

def handle_options_command(arg: str = "") -> list[str]:
    """
    /options [qqq|spy|both]
    Downloads live data, checks RSI-MA percentile, prices the spread, returns parts.
    """
    arg = arg.strip().lower()
    target = {"qqq": ["QQQ"], "spy": ["SPY"], "both": ["QQQ", "SPY"], "": ["QQQ", "SPY"]}
    tickers = target.get(arg, ["QQQ", "SPY"])

    # ── Download data ──────────────────────────────────────────────────────────
    syms = tickers + ["^VIX", "^VXN", "^VIX9D"]
    data = _download(syms, period="18mo")
    parts: list[str] = []
    signal_found = False

    for ticker in tickers:
        ref = REF[ticker]
        close = data.get(ticker)
        if close is None or len(close) < RSI_LOOKBACK + 30:
            parts.append(f"❌ {ticker}: insufficient data")
            continue

        spot = float(close.iloc[-1])
        pct  = _rsi_ma_pct(close)
        if pct is None:
            parts.append(f"❌ {ticker}: could not compute percentile")
            continue

        # Get IV
        iv_ser = data.get(ref["iv_sym"])
        iv     = _iv_level(iv_ser) or 20.0

        # VIX9D for short-dated options
        vix9d_ser = data.get("^VIX9D")
        vix_ser   = data.get("^VIX")
        vix9d     = _iv_level(vix9d_ser) or iv
        vix30     = _iv_level(vix_ser)   or iv
        # Scale VIX9D to this index
        iv_short = iv * (vix9d / vix30) if vix30 > 0 else iv

        # Find target expiry
        expiry = _nearest_friday(target_days=10)
        dte    = (expiry - datetime.date.today()).days

        # Price the spread using short-dated IV
        iv_frac  = iv_short / 100.0
        spread   = _price_bull_put_spread(spot, iv_frac, dte)
        bcs      = _price_bull_call_spread(spot, iv / 100.0, 35)

        if pct < SIGNAL_THRESH:
            # ── SIGNAL ACTIVE ─────────────────────────────────────────────────
            signal_found = True
            msg_parts = _fmt_options_result(
                ticker, pct, spot, iv_short, ref["iv_sym"],
                spread, bcs, dte, expiry, ref
            )
            parts.extend(msg_parts)

            # Log the signal
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
            # ── NO SIGNAL: watch status ────────────────────────────────────────
            watch_line = _fmt_watch_result(ticker, pct, spot, iv_short, ref["iv_sym"], ref)
            parts.append(watch_line)

            # Also show what the spread would look like right now (hypothetical)
            parts.append(
                f"💡 <b>Hypothetical setup if {ticker} were at signal NOW:</b>\n"
                f"  Sell ${spread['K_sell']} put / Buy ${spread['K_buy']} put  ({dte} DTE)\n"
                f"  Credit ~${spread['credit']:.2f}  |  Width ${spread['width']}  |  "
                f"Max loss ${spread['max_loss']:.2f}/sh\n"
                f"  Credit/Width: {spread['credit_pct_width']:.1f}%  "
                f"{'✅ OK' if spread['credit_pct_width'] >= 20 else '⚠️ thin'}"
            )

    if not signal_found and parts:
        parts.insert(0, "📭 <b>No active options signal right now.</b>\nCurrent status:")

    return parts or ["❌ Could not process /options — check logs."]


def handle_iv_command() -> list[str]:
    """
    /iv — Current VIX / VXN / VIX9D dashboard with context.
    """
    data = _download(["QQQ", "SPY", "^VIX", "^VXN", "^VIX9D"], period="6mo")
    vix   = _iv_level(data.get("^VIX"))
    vxn   = _iv_level(data.get("^VXN"))
    vix9d = _iv_level(data.get("^VIX9D"))

    spy_close = data.get("SPY")
    qqq_close = data.get("QQQ")
    spy_pct   = _rsi_ma_pct(spy_close) if spy_close is not None else None
    qqq_pct   = _rsi_ma_pct(qqq_close) if qqq_close is not None else None

    # IV context for 30-day history
    vix_ser = data.get("^VIX")
    if vix_ser is not None and len(vix_ser) >= 30:
        vix_30d_avg = vix_ser.iloc[-30:].mean()
        vix_30d_min = vix_ser.iloc[-30:].min()
        vix_30d_max = vix_ser.iloc[-30:].max()
        vix_context = f"{vix:.1f}  (30d: avg {vix_30d_avg:.1f} / min {vix_30d_min:.1f} / max {vix_30d_max:.1f})"
    else:
        vix_context = f"{vix:.1f}" if vix else "N/A"

    vxn_ser = data.get("^VXN")
    if vxn_ser is not None and len(vxn_ser) >= 30:
        vxn_30d_avg = vxn_ser.iloc[-30:].mean()
        vxn_context = f"{vxn:.1f}  (30d avg: {vxn_30d_avg:.1f})"
    else:
        vxn_context = f"{vxn:.1f}" if vxn else "N/A"

    vix_regime_l,   vix_adv   = _iv_regime(vix   or 20)
    vxn_regime_l,   vxn_adv   = _iv_regime(vxn   or 20)
    vix9d_regime_l, _         = _iv_regime(vix9d or 20)

    term_note = ""
    if vix9d and vix:
        diff = vix9d - vix
        if diff > 2:
            term_note = f"⚡ VIX9D > VIX by {diff:.1f}pp — front-month fear elevated, more put premium to sell"
        elif diff < -2:
            term_note = f"VIX9D < VIX by {abs(diff):.1f}pp — short-dated cheaper (contango)"
        else:
            term_note = f"VIX9D ≈ VIX — normal term structure"

    spy_line = f"SPY RSI-MA: <b>{spy_pct:.1f}th pct</b> {'🔴 SIGNAL ACTIVE' if spy_pct and spy_pct < 5 else '🟡 watching' if spy_pct and spy_pct < 10 else '⚪ normal'}" if spy_pct else "SPY RSI-MA: —"
    qqq_line = f"QQQ RSI-MA: <b>{qqq_pct:.1f}th pct</b> {'🔴 SIGNAL ACTIVE' if qqq_pct and qqq_pct < 5 else '🟡 watching' if qqq_pct and qqq_pct < 10 else '⚪ normal'}" if qqq_pct else "QQQ RSI-MA: —"

    msg = (
        f"📊 <b>IV DASHBOARD</b> — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} UTC\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"\n"
        f"<b>S&P 500 (SPY options)</b>\n"
        f"  VIX  (30d): <b>{vix_context}</b>\n"
        f"  VIX9D (9d): <b>{vix9d:.1f}%</b>  {vix9d_regime_l}\n"
        f"  → {vix_regime_l}\n"
        f"\n"
        f"<b>NASDAQ 100 (QQQ options)</b>\n"
        f"  VXN  (30d): <b>{vxn_context}</b>\n"
        f"  → {vxn_regime_l}\n"
        f"\n"
        f"<b>Term Structure</b>\n"
        f"  {term_note}\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Options Strategy Guide</b>\n"
        f"  VIX/VXN > 25%: 🐂 Bull Put Spread ★★★\n"
        f"  VIX/VXN 20-25%: 🐂 Bull Put Spread ★★\n"
        f"  VIX/VXN 15-20%: Both spreads work\n"
        f"  VIX/VXN < 15%: 📞 Long Call (low crush risk)\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>RSI-MA Signal Watch</b>\n"
        f"  {spy_line}\n"
        f"  {qqq_line}\n"
        f"  (Signal fires at <5th pct | /options for full setup)"
    )
    return [msg]


def handle_optwatch_command() -> list[str]:
    """
    /optwatch — Current RSI-MA pct + distance to signal + hypothetical setup.
    """
    data = _download(["QQQ", "SPY", "^VIX", "^VXN", "^VIX9D"], period="18mo")
    vix_ser   = data.get("^VIX")
    vxn_ser   = data.get("^VXN")
    vix9d_ser = data.get("^VIX9D")
    vix30 = _iv_level(vix_ser) or 20.0
    vix9d = _iv_level(vix9d_ser) or vix30

    parts = [f"👁 <b>OPTIONS WATCH — {datetime.date.today()}</b>\n━━━━━━━━━━━━━━━━━━━━━━━━"]

    expiry = _nearest_friday(10)
    dte    = (expiry - datetime.date.today()).days

    for ticker in ["QQQ", "SPY"]:
        ref   = REF[ticker]
        close = data.get(ticker)
        if close is None: continue
        spot  = float(close.iloc[-1])
        pct   = _rsi_ma_pct(close)
        if pct is None: continue

        iv_ser = vxn_ser if ticker == "QQQ" else vix_ser
        iv30   = _iv_level(iv_ser) or 20.0
        iv_short = iv30 * (vix9d / vix30) if vix30 > 0 else iv30
        iv_sym = ref["iv_sym"]

        spread = _price_bull_put_spread(spot, iv_short / 100.0, dte)
        bcs    = _price_bull_call_spread(spot, iv30 / 100.0, 35)
        regime_label, _ = _iv_regime(iv_short)

        if pct < SIGNAL_THRESH:
            status_icon = "🔴"
            status_text = "SIGNAL ACTIVE — run /options for full details"
        elif pct < 8:
            status_icon = "🟠"
            status_text = f"CLOSE — {pct - SIGNAL_THRESH:.1f}pp above threshold"
        elif pct < 15:
            status_icon = "🟡"
            status_text = f"WATCHING — {pct - SIGNAL_THRESH:.1f}pp above threshold"
        else:
            status_icon = "⚪"
            status_text = "Normal — no signal expected soon"

        # Progress bar toward signal
        filled = min(10, int((SIGNAL_THRESH / max(pct, 0.1)) * 10))
        bar = "🟥" * filled + "⬜" * (10 - filled)

        part = (
            f"\n{status_icon} <b>{ticker}</b>  ({ref['name']})\n"
            f"  RSI-MA: <b>{pct:.1f}th pct</b>  {bar}\n"
            f"  Signal: &lt;5th pct  |  Gap: {max(0,pct-SIGNAL_THRESH):.1f}pp\n"
            f"  Status: {status_text}\n"
            f"\n"
            f"  IV ({iv_sym}): <b>{iv_short:.1f}%</b>  {regime_label}\n"
            f"  Spot: ${spot:.2f}  |  Expiry: {expiry.strftime('%d %b')} ({dte}d)\n"
            f"\n"
            f"  📋 If signal now: Sell ${spread['K_sell']} / Buy ${spread['K_buy']} put\n"
            f"     Credit ~${spread['credit']:.2f}  |  Width ${spread['width']}\n"
            f"     Max loss: ${spread['max_loss']:.2f}/sh  "
            f"({'✅ ' if spread['credit_pct_width'] >= 20 else '⚠️ '}credit {spread['credit_pct_width']:.1f}% of width)"
        )
        parts.append(part)

    # Tail note
    ref_note = (
        f"\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📚 <b>Reference (backtested)</b>\n"
        f"  QQQ bull put: {REF['QQQ']['bps_win_rate']:.0f}% win  EV +{REF['QQQ']['bps_ev']:.1f}%  (N={REF['QQQ']['n_signals']})\n"
        f"  SPY bull put: {REF['SPY']['bps_win_rate']:.0f}% win  EV +{REF['SPY']['bps_ev']:.1f}%  (N={REF['SPY']['n_signals']})\n"
        f"  VIX>25%: {REF['QQQ']['bps_wr_high']:.0f}%/{REF['SPY']['bps_wr_high']:.0f}% win (QQQ/SPY)\n"
        f"  /options — full setup when signal active"
    )
    parts.append(ref_note)
    return parts


def handle_optlog_command(n: int = 10) -> list[str]:
    """
    /optlog [n] — show last n logged option signals.
    """
    if not LOG_PATH.exists():
        return ["📭 No option signals logged yet."]
    try:
        log = json.loads(LOG_PATH.read_text())
    except Exception:
        return ["❌ Could not read signal log."]
    if not log:
        return ["📭 No option signals logged yet."]

    recent = log[-n:][::-1]
    lines = [f"📋 <b>Last {min(n, len(recent))} Options Signals</b>\n━━━━━━━━━━━━━━━━━━━━━━━━"]
    for e in recent:
        lines.append(
            f"\n<b>{e.get('date','?')}</b>  {e.get('ticker','?')}\n"
            f"  Pct: {e.get('pct','?'):.1f}th  |  IV: {e.get('iv','?'):.1f}%\n"
            f"  Spot: ${e.get('spot','?'):.2f}  |  Setup: Sell ${e.get('K_sell','?')} / Buy ${e.get('K_buy','?')}\n"
            f"  Credit: ${e.get('credit','?'):.2f}  Width: ${e.get('width','?')}  "
            f"Max loss: ${e.get('max_loss','?'):.2f}\n"
            f"  Expiry: {e.get('expiry','?')}  DTE: {e.get('dte','?')}\n"
            f"  Regime: {e.get('regime','?')}"
        )
    lines.append(f"\n<i>Full log: docs/OPTIONS_SIGNAL_LOG.md</i>")
    return ["\n".join(lines)]
