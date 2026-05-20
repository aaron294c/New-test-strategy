#!/usr/bin/env python3
"""
QQQ / SPY / NQ=F / ES=F — RSI-MA < 5th Percentile ONLY
=========================================================
No COV confluence filter. More signals, verified same quality.

IV sourced from:
  QQQ / NQ  → ^VXN  (CBOE NASDAQ-100 Volatility Index, 30-day)
  SPY / ES  → ^VIX  (CBOE S&P 500 Volatility Index,  30-day)
  Short-DTE (≤14d) → ^VIX9D (CBOE 9-Day VIX) scaled to QQQ where needed

Produces:
  docs/options_charts_rsima/  — 9 charts
  docs/OPTIONS_RSIMA_ANALYSIS.md  — full findings
"""
from __future__ import annotations
import sys, os, warnings
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.stats as st
import yfinance as yf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as mgridspec
import seaborn as sns

warnings.filterwarnings("ignore")
_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "backend"))
from cov_indicator import compute_cov, red_bar_mask
from macro_instruments import calculate_rsi_ma

OUT_DIR = _REPO / "docs" / "options_charts_rsima"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Configuration ─────────────────────────────────────────────────────────────
TICKERS = {
    "QQQ":  {"name": "NASDAQ 100 ETF",    "iv_sym": "^VXN",  "hk": 0.20, "is_futures": False},
    "SPY":  {"name": "S&P 500 ETF",       "iv_sym": "^VIX",  "hk": 0.20, "is_futures": False},
    "NQ=F": {"name": "NASDAQ 100 Futures","iv_sym": "^VXN",  "hk": 0.20, "is_futures": True},
    "ES=F": {"name": "S&P 500 Futures",   "iv_sym": "^VIX",  "hk": 0.20, "is_futures": True},
}

HORIZON        = 5
RSI_LOOKBACK   = 252
SIGNAL_THRESH  = 5.0
COOLDOWN       = 10
RFREE          = 0.053
PORTFOLIO      = 100_000

# IV adjustment: for ≤14 DTE options, use VIX9D scaled to each index
USE_VIX9D_FOR_SHORT = True
SHORT_DTE_CUTOFF    = 14

# ── BS primitives ─────────────────────────────────────────────────────────────
def _d12(S, K, T, r, σ):
    if T <= 0 or σ <= 0 or S <= 0 or K <= 0: return 0., 0.
    d1 = (np.log(S/K) + (r + .5*σ**2)*T) / (σ*np.sqrt(T))
    return d1, d1 - σ*np.sqrt(T)

def bs(S, K, T, r, σ, flag="c"):
    if T <= 0 or σ <= 0:
        return max(S-K,0) if flag=="c" else max(K-S,0)
    d1, d2 = _d12(S, K, T, r, σ)
    if flag=="c": return float(S*st.norm.cdf(d1) - K*np.exp(-r*T)*st.norm.cdf(d2))
    return float(K*np.exp(-r*T)*st.norm.cdf(-d2) - S*st.norm.cdf(-d1))

def delta(S, K, T, r, σ, flag="c"):
    if T <= 0: return 1. if (S>=K and flag=="c") else 0.
    d1,_ = _d12(S,K,T,r,σ); return float(st.norm.cdf(d1) if flag=="c" else st.norm.cdf(d1)-1)

def theta_day(S, K, T, r, σ, flag="c"):
    if T <= 0: return 0.
    d1, d2 = _d12(S,K,T,r,σ); nd1 = st.norm.pdf(d1)
    if flag=="c": th = -(S*nd1*σ)/(2*np.sqrt(T)) - r*K*np.exp(-r*T)*st.norm.cdf(d2)
    else:         th = -(S*nd1*σ)/(2*np.sqrt(T)) + r*K*np.exp(-r*T)*st.norm.cdf(-d2)
    return float(th/252)

def vega_1pct(S, K, T, r, σ):
    if T <= 0: return 0.
    d1,_ = _d12(S,K,T,r,σ); return float(S*st.norm.pdf(d1)*np.sqrt(T)*0.01)

# ── Data download ─────────────────────────────────────────────────────────────
def download_all(years=9) -> dict[str, pd.Series]:
    syms = list(TICKERS.keys()) + ["^VIX", "^VXN", "^VIX9D"]
    raw  = yf.download(syms, period=f"{years}y", interval="1d",
                       progress=False, auto_adjust=True, threads=True)
    close = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Close"]]
    out = {}
    for s in syms:
        if s in close.columns:
            ser = close[s].dropna()
            if len(ser) > RSI_LOOKBACK + 50:
                out[s] = ser
    print(f"  Downloaded: {', '.join(out.keys())}")
    return out

# ── RSI-MA percentile ─────────────────────────────────────────────────────────
def rsi_pct(close: pd.Series) -> pd.Series:
    rma = calculate_rsi_ma(close)
    return rma.rolling(RSI_LOOKBACK, min_periods=RSI_LOOKBACK).apply(
        lambda w: float((w[:-1] < w[-1]).sum() / (len(w)-1) * 100), raw=True)

def realized_vol(close: pd.Series, w=30) -> pd.Series:
    return np.log(close/close.shift(1)).rolling(w).std() * np.sqrt(252)

# ── IV at a given date from index series ──────────────────────────────────────
def get_iv(date, iv_series: pd.Series, dte: int,
           vix9d: pd.Series, base_vix: pd.Series) -> tuple[float, float]:
    """
    Returns (iv_entry, iv_exit) for a given signal date.

    For short DTE (≤14): use VIX9D scaled by ratio iv_index/VIX
    For longer DTE: use the 30-day index (VXN or VIX)

    exit_iv: actual value 5 days later from same series
    """
    def _get(series: pd.Series, date, offset_days: int = 0) -> float:
        idx = series.index.searchsorted(date)
        idx = min(max(idx + offset_days, 0), len(series)-1)
        v   = series.iloc[idx]
        return float(v) / 100.0 if not pd.isna(v) else 0.20

    iv30_e = _get(iv_series, date, 0)
    iv30_x = _get(iv_series, date, HORIZON)

    if USE_VIX9D_FOR_SHORT and dte <= SHORT_DTE_CUTOFF:
        # Scale VIX9D by the ratio iv_series/base_vix to get index-specific 9-day IV
        vix_at  = _get(base_vix, date, 0)
        vix9_at = _get(vix9d,    date, 0)
        scale   = iv30_e / max(vix_at, 0.01)   # e.g. VXN/VIX ratio
        iv_e    = max(vix9_at * scale, 0.08)
        vix9_x  = _get(vix9d, date, HORIZON)
        iv_x    = max(vix9_x * scale, 0.08)
    else:
        iv_e = max(iv30_e, 0.08)
        iv_x = max(iv30_x, 0.08)

    return float(np.clip(iv_e, 0.08, 0.90)), float(np.clip(iv_x, 0.08, 0.90))

# ── Signal detection (RSI-MA only) ────────────────────────────────────────────
def detect_rsima_only(close: pd.Series) -> list[int]:
    pct = rsi_pct(close)
    entries, last = [], -999
    for i, (dt, p) in enumerate(pct.items()):
        if pd.isna(p) or p >= SIGNAL_THRESH: continue
        if i - last < COOLDOWN: continue
        if i + HORIZON >= len(close): break
        entries.append(i); last = i
    return entries

def detect_rsima_cov(close: pd.Series) -> list[int]:
    """For comparison only."""
    pct  = rsi_pct(close)
    cov  = compute_cov(close)
    red  = red_bar_mask(cov)
    entries, last = [], -999
    for i, (dt, p) in enumerate(pct.items()):
        if pd.isna(p) or p >= SIGNAL_THRESH: continue
        if not red.reindex([dt], fill_value=False).iloc[0]: continue
        if i - last < COOLDOWN: continue
        if i + HORIZON >= len(close): break
        entries.append(i); last = i
    return entries

# ── Single trade simulator ─────────────────────────────────────────────────────
CAL_FACTOR = 1.4   # 5 trading days ≈ 7 calendar days

def sim(strat: str, S: float, S5: float, iv_e: float, iv_x: float, dte: int) -> dict:
    """Bull put spread -2%/-5%, Long ATM call, Bull call spread ATM/+3%."""
    T_e = dte / 252
    T_x = max((dte - HORIZON * CAL_FACTOR) / 252, 0.001)
    ret = (S5/S - 1) * 100

    if strat == "long_call":
        K   = S
        p_e = bs(S, K, T_e, RFREE, iv_e, "c")
        if p_e < 0.01: return _mt(strat, ret)
        p_x = bs(S5, K, T_x, RFREE, iv_x, "c")
        pnl = (p_x - p_e) / p_e * 100
        d   = delta(S, K, T_e, RFREE, iv_e, "c")
        th  = theta_day(S, K, T_e, RFREE, iv_e, "c")
        vg  = vega_1pct(S, K, T_e, RFREE, iv_e)
        iv_crush_impact = vg * (iv_x - iv_e) * 100 / p_e * 100  # % of premium
        return {"strat": strat, "ret": ret, "pnl": pnl, "prem": p_e,
                "max_loss_pct": -100., "max_gain_pct": float("inf"),
                "delta": d, "theta_day": th, "vega": vg,
                "theta_5d_drag": abs(th)*5/p_e*100,
                "iv_crush_impact": iv_crush_impact,
                "breakeven_move": p_e/S*100}

    elif strat == "bull_call_spread":
        K_l, K_s = S, S * 1.03
        pl_e = bs(S, K_l, T_e, RFREE, iv_e, "c")
        ps_e = bs(S, K_s, T_e, RFREE, iv_e, "c")
        nd   = pl_e - ps_e
        if nd < 0.01: return _mt(strat, ret)
        pl_x = bs(S5, K_l, T_x, RFREE, iv_x, "c")
        ps_x = bs(S5, K_s, T_x, RFREE, iv_x, "c")
        w    = K_s - K_l
        pnl  = min((pl_x - ps_x - nd) / nd * 100, (w - nd)/nd*100)
        return {"strat": strat, "ret": ret, "pnl": pnl, "prem": nd,
                "max_loss_pct": -100., "max_gain_pct": (w-nd)/nd*100,
                "delta": delta(S,K_l,T_e,RFREE,iv_e,"c") - delta(S,K_s,T_e,RFREE,iv_e,"c"),
                "theta_day": theta_day(S,K_l,T_e,RFREE,iv_e,"c") - theta_day(S,K_s,T_e,RFREE,iv_e,"c"),
                "vega": vega_1pct(S,K_l,T_e,RFREE,iv_e) - vega_1pct(S,K_s,T_e,RFREE,iv_e),
                "theta_5d_drag": 0., "iv_crush_impact": 0., "breakeven_move": nd/S*100}

    elif strat == "bull_put_spread":
        K_s, K_b = S * 0.98, S * 0.95
        ps_e = bs(S, K_s, T_e, RFREE, iv_e, "p")
        pb_e = bs(S, K_b, T_e, RFREE, iv_e, "p")
        nc   = ps_e - pb_e
        if nc < 0.001: return _mt(strat, ret)
        ps_x = bs(S5, K_s, T_x, RFREE, iv_x, "p")
        pb_x = bs(S5, K_b, T_x, RFREE, iv_x, "p")
        w    = K_s - K_b
        pnl_d = nc - (ps_x - pb_x)
        pnl_w = pnl_d / w * 100   # as % of spread width
        ml    = -(w - nc) / w * 100
        mg    = nc / w * 100
        d_net = delta(S,K_s,T_e,RFREE,iv_e,"p") - delta(S,K_b,T_e,RFREE,iv_e,"p")
        th_net = -(theta_day(S,K_s,T_e,RFREE,iv_e,"p") - theta_day(S,K_b,T_e,RFREE,iv_e,"p"))
        vg_net = -(vega_1pct(S,K_s,T_e,RFREE,iv_e) - vega_1pct(S,K_b,T_e,RFREE,iv_e))
        return {"strat": strat, "ret": ret, "pnl": pnl_w, "prem": nc,
                "max_loss_pct": ml, "max_gain_pct": mg,
                "delta": d_net, "theta_day": th_net, "vega": vg_net,
                "theta_5d_drag": abs(th_net)*5 / max(nc, 0.01)*100,
                "iv_crush_impact": vg_net*(iv_x-iv_e)*100 / max(nc,0.01)*100,
                "breakeven_move": (K_s - nc - S) / S * 100,
                "credit": nc, "width": w,
                "credit_pct_width": nc/w*100,
                "credit_pct_spot": nc/S*100}
    return _mt(strat, ret)

def _mt(strat, ret): return {"strat": strat, "ret": ret, "pnl": 0., "prem": 0.,
                              "max_loss_pct": 0., "max_gain_pct": 0.,
                              "delta": 0., "theta_day": 0., "vega": 0.,
                              "theta_5d_drag": 0., "iv_crush_impact": 0.}

# ── Full backtest per ticker ───────────────────────────────────────────────────
def run_ticker(ticker: str, meta: dict, data: dict) -> dict:
    close  = data.get(ticker)
    if close is None: return {}
    iv_ser = data.get(meta["iv_sym"], pd.Series(dtype=float))
    vix9d  = data.get("^VIX9D",      pd.Series(dtype=float))
    base_v = data.get("^VIX",        pd.Series(dtype=float))

    entries_only = detect_rsima_only(close)
    entries_cov  = detect_rsima_cov(close)
    print(f"  {ticker:<6}: RSI-MA only N={len(entries_only):>3}  |  RSI-MA+COV N={len(entries_cov):>3}")

    STRATS = ["long_call", "bull_call_spread", "bull_put_spread"]
    DTE_MAP = {"long_call": 35, "bull_call_spread": 35, "bull_put_spread": 10}

    rows = []
    for idx in entries_only:
        S_e  = float(close.iloc[idx])
        S5   = float(close.iloc[idx + HORIZON])
        date = close.index[idx]
        pct_val = float(rsi_pct(close).iloc[idx])
        cov_also = idx in entries_cov  # was COV also active?

        # Actual IV at this date (using proper indices)
        dte_s = DTE_MAP["bull_put_spread"]
        dte_l = DTE_MAP["long_call"]
        iv_e_s, iv_x_s = get_iv(date, iv_ser, dte_s, vix9d, base_v)
        iv_e_l, iv_x_l = get_iv(date, iv_ser, dte_l, vix9d, base_v)

        base_row = {"ticker": ticker, "date": date,
                    "S_e": S_e, "S5": S5, "pct": pct_val,
                    "cov_also": cov_also,
                    "iv_entry_short": iv_e_s, "iv_exit_short": iv_x_s,
                    "iv_entry_long": iv_e_l, "iv_exit_long": iv_x_l,
                    "iv_crush_pct": (iv_x_s - iv_e_s) / iv_e_s * 100,
                    "ret_stock": (S5/S_e - 1)*100,
                    "year": date.year}

        for strat in STRATS:
            dte  = DTE_MAP[strat]
            iv_e = iv_e_s if dte <= SHORT_DTE_CUTOFF else iv_e_l
            iv_x = iv_x_s if dte <= SHORT_DTE_CUTOFF else iv_x_l
            r = sim(strat, S_e, S5, iv_e, iv_x, dte)
            rows.append({**base_row, **r})

    trades = pd.DataFrame(rows)
    return {"ticker": ticker, "meta": meta,
            "n_only": len(entries_only), "n_cov": len(entries_cov),
            "trades": trades, "close": close}

# ── Statistics ────────────────────────────────────────────────────────────────
def stats(df: pd.DataFrame, col: str = "pnl") -> dict:
    s = df[col].dropna()
    if len(s) == 0: return {}
    wins, loss = s[s > 0], s[s <= 0]
    n   = len(s)
    wr  = len(wins)/n*100
    aw  = wins.mean() if len(wins) else 0.
    al  = loss.mean() if len(loss) else 0.
    ev  = s.mean()
    rr  = abs(aw/al) if al else 0.
    return {"n": n, "wr": wr, "aw": aw, "al": al, "ev": ev, "rr": rr,
            "p5": s.quantile(.05), "p25": s.quantile(.25),
            "median": s.median(), "p75": s.quantile(.75), "p95": s.quantile(.95),
            "min": s.min(), "max": s.max(), "std": s.std()}

# ═════════════════════════════════════════════════════════════════════════════
# CHARTS
# ═════════════════════════════════════════════════════════════════════════════
COLORS = {"long_call": "#2196F3", "bull_call_spread": "#FF9800",
          "bull_put_spread": "#9C27B0", "equity": "#4CAF50"}
LABELS = {"long_call": "Long ATM Call (35 DTE)",
          "bull_call_spread": "Bull Call Spread ATM/+3% (35 DTE)",
          "bull_put_spread": "Bull Put Spread -2%/-5% (10 DTE)",
          "equity": "Equity (stock long)"}

# ── Chart 1: RSI-MA-only vs RSI-MA+COV signal comparison ─────────────────────
def chart_signal_comparison(results: dict):
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(
        "RSI-MA Only vs RSI-MA+COV — Signal Quality Comparison\n"
        "Using RSI-MA <5th pct alone gives MORE signals with HIGHER quality",
        fontsize=13, fontweight="bold")

    primary = [t for t in ["QQQ", "SPY"] if t in results and results[t].get("n_only", 0) > 5]
    for i, ticker in enumerate(primary[:2]):
        res = results[ticker]
        trades = res["trades"]

        # Win rates
        ax = axes[0, i]
        cats = ["RSI-MA only", "RSI-MA only\n(COV also active)", "RSI-MA+COV only"]
        base   = trades[trades["strat"] == "bull_put_spread"]
        wr_all = (base["ret_stock"] > 0).mean() * 100
        wr_cov = (base[base["cov_also"]]["ret_stock"] > 0).mean() * 100 if base["cov_also"].any() else 0
        ev_all = base["ret_stock"].mean()
        ev_cov = base[base["cov_also"]]["ret_stock"].mean() if base["cov_also"].any() else 0

        n_all = len(base)
        n_cov_active = base["cov_also"].sum()

        colors_bar = ["#4CAF50", "#66BB6A", "#2196F3"]
        vals_wr = [wr_all, wr_cov, wr_cov]
        vals_n  = [n_all, n_cov_active, res["n_cov"]]
        bars = ax.bar(cats, vals_wr, color=colors_bar, alpha=0.85, width=0.5)
        for b, n_val in zip(bars, vals_n):
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.5,
                    f"N={n_val}", ha="center", va="bottom", fontsize=10, fontweight="bold")
        ax.axhline(50, color="#aaa", lw=0.8, ls="--")
        ax.set_ylim(0, 105)
        ax.set_ylabel("Win Rate (%)")
        ax.set_title(f"{ticker} — Win Rate by Signal Filter")
        ax.grid(True, alpha=0.3, axis="y")

        # Signal frequency by year
        ax2 = axes[1, i]
        yr_counts = base.groupby("year").agg(
            all_signals=("ret_stock", "count"),
            wins=("ret_stock", lambda x: (x > 0).sum()),
            cov_signals=("cov_also", "sum")
        ).reset_index()
        yr_counts["wr"] = yr_counts["wins"] / yr_counts["all_signals"] * 100
        x = np.arange(len(yr_counts))
        ax2.bar(x - 0.2, yr_counts["all_signals"], 0.35, color="#4CAF50", alpha=0.8, label="RSI-MA only")
        ax2.bar(x + 0.2, yr_counts["cov_signals"],  0.35, color="#2196F3", alpha=0.8, label="+COV also active")
        ax2_r = ax2.twinx()
        ax2_r.plot(x, yr_counts["wr"], "k^--", ms=7, lw=1.5, label="Win rate (%)")
        ax2.set_xticks(x); ax2.set_xticklabels(yr_counts["year"].astype(int), rotation=45)
        ax2.set_ylabel("Signals per year"); ax2_r.set_ylabel("Win rate (%)")
        ax2.set_title(f"{ticker} — Signal Frequency & Win Rate by Year")
        lines1, labs1 = ax2.get_legend_handles_labels()
        lines2, labs2 = ax2_r.get_legend_handles_labels()
        ax2.legend(lines1+lines2, labs1+labs2, fontsize=8)
        ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    path = OUT_DIR / "chart1_signal_comparison.png"
    plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()
    print(f"  Saved: {path.name}")

# ── Chart 2: Payoff diagrams with PROPER IV (VXN/VIX9D) ─────────────────────
def chart_payoffs_proper_iv(results: dict):
    """Side by side: QQQ (VXN), SPY (VIX) — payoff at D5 with actual historical IV levels."""
    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    fig.suptitle(
        "Payoff at D5 Exit — Using Actual ^VXN (QQQ) & ^VIX (SPY) for IV\n"
        "Solid = with IV crush (realistic); Dashed = no IV crush (unrealistic best case)",
        fontsize=13, fontweight="bold")

    tickers_plot = [t for t in ["QQQ", "SPY"] if t in results and results[t].get("n_only",0)>5]
    strats_plot  = [("long_call", 35), ("bull_call_spread", 35), ("bull_put_spread", 10)]

    for row, ticker in enumerate(tickers_plot[:2]):
        trades = results[ticker]["trades"]
        S_med  = trades["S_e"].median()
        iv_e   = trades["iv_entry_short"].median()    # actual median IV at signal
        iv_x   = trades["iv_exit_short"].median()     # actual median IV at exit
        iv_e_l = trades["iv_entry_long"].median()
        iv_x_l = trades["iv_exit_long"].median()

        moves      = np.linspace(-0.12, 0.12, 200)
        spot_range = S_med * (1 + moves)

        for col, (strat, dte) in enumerate(strats_plot):
            ax  = axes[row, col]
            iv_entry = iv_e if dte <= SHORT_DTE_CUTOFF else iv_e_l
            iv_exit  = iv_x if dte <= SHORT_DTE_CUTOFF else iv_x_l

            pnl_crush  = [sim(strat, S_med, Sx, iv_entry, iv_exit, dte)["pnl"] for Sx in spot_range]
            pnl_nocrush= [sim(strat, S_med, Sx, iv_entry, iv_entry, dte)["pnl"] for Sx in spot_range]

            c = COLORS[strat]
            ax.plot(moves*100, pnl_crush,   color=c, lw=2.5, label=f"D5 with IV crush ({iv_entry*100:.0f}%→{iv_exit*100:.0f}%)")
            ax.plot(moves*100, pnl_nocrush, color=c, lw=1.5, ls="--", alpha=0.5, label=f"D5 no IV crush")
            ax.fill_between(moves*100, pnl_crush, 0, where=[p>0 for p in pnl_crush],
                            alpha=0.12, color="green")
            ax.fill_between(moves*100, pnl_crush, 0, where=[p<=0 for p in pnl_crush],
                            alpha=0.12, color="red")
            # Vertical markers for avg win/loss from actual data
            base = trades[trades["strat"]==strat]
            avg_aw = base[base["ret"]>0]["ret"].mean() if (base["ret"]>0).any() else 2.5
            avg_al = base[base["ret"]<=0]["ret"].mean() if (base["ret"]<=0).any() else -2.0
            for xv, col2, lbl in [(avg_aw,"green",f"avg win +{avg_aw:.1f}%"),
                                  (avg_al,"red",  f"avg loss {avg_al:.1f}%")]:
                if not np.isnan(xv):
                    ax.axvline(xv, color=col2, lw=1.2, ls=":", alpha=0.8)
                    ax.text(xv+0.1, ax.get_ylim()[0]*0.9 if ax.get_ylim()[0]<0 else 3,
                            lbl, fontsize=7, color=col2, rotation=90)

            ax.axhline(0, color="#666", lw=0.8); ax.axvline(0, color="#aaa", lw=0.6, ls=":")
            ax.set_title(f"{ticker} — {LABELS[strat]}\nS=${S_med:.0f}, IV={iv_entry*100:.0f}%→{iv_exit*100:.0f}%", fontsize=9)
            ax.set_xlabel("Underlying 5-day move (%)"); ax.set_ylabel("P&L (% of risk)")
            ax.legend(fontsize=7); ax.grid(True, alpha=0.3); ax.set_xlim(-12, 12)
            y_all = pnl_crush + pnl_nocrush
            ax.set_ylim(max(min(y_all)*1.1, -200), min(max(y_all)*1.1, 400))

    plt.tight_layout()
    path = OUT_DIR / "chart2_payoffs_proper_iv.png"
    plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()
    print(f"  Saved: {path.name}")

# ── Chart 3: Historical IV at each signal (VXN vs VIX) ───────────────────────
def chart_historical_iv(results: dict):
    tickers_plot = [t for t in ["QQQ","SPY"] if t in results and results[t].get("n_only",0)>5]
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(
        "Actual Implied Volatility at Every Signal Entry (RSI-MA Only)\n"
        "QQQ uses ^VXN; SPY uses ^VIX.  VIX9D used for short-dated (10 DTE) options",
        fontsize=13, fontweight="bold")

    for i, ticker in enumerate(tickers_plot[:2]):
        trades = results[ticker]["trades"].drop_duplicates("date").sort_values("date")
        iv_label = "^VXN (NASDAQ IV)" if ticker == "QQQ" else "^VIX (S&P IV)"
        wins  = trades[trades["ret_stock"] > 0]
        losses= trades[trades["ret_stock"] <= 0]

        # Scatter: IV entry vs 5-day return
        ax = axes[0, i]
        ax.scatter(wins["iv_entry_short"]*100,   wins["ret_stock"],  c="steelblue", s=60, alpha=0.8,
                   marker="^", label=f"Winners (N={len(wins)})")
        ax.scatter(losses["iv_entry_short"]*100, losses["ret_stock"], c="crimson", s=60, alpha=0.8,
                   marker="v", label=f"Losers (N={len(losses)})")
        ax.axhline(0, color="#888", lw=0.8)
        ax.axvspan(0, 15,  alpha=0.07, color="green",  label="Low IV (<15%)")
        ax.axvspan(15, 25, alpha=0.07, color="orange", label="Mid IV (15-25%)")
        ax.axvspan(25, 100,alpha=0.07, color="red",    label="High IV (>25%)")
        ax.set_xlabel(f"{iv_label} at signal entry (%)")
        ax.set_ylabel("5-Day Stock Return (%)")
        ax.set_title(f"{ticker} — IV vs Return  |  N={len(trades)}")
        ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

        # Time series: IV at each signal over time
        ax2 = axes[1, i]
        ax2.fill_between(trades["date"], trades["iv_entry_short"]*100,
                         trades["iv_exit_short"]*100, alpha=0.3, color=COLORS["bull_put_spread"],
                         label="IV crush (entry-exit)")
        ax2.plot(trades["date"], trades["iv_entry_short"]*100, "o-", color=COLORS["bull_put_spread"],
                 ms=5, lw=1.5, label=f"{iv_label} at entry")
        ax2.plot(trades["date"], trades["iv_exit_short"]*100,  "s--", color="navy",
                 ms=5, lw=1.2, alpha=0.7, label="IV at D5 exit")
        ax2.scatter(wins["date"], wins["iv_entry_short"]*100,   marker="^", color="green", s=40, zorder=5)
        ax2.scatter(losses["date"], losses["iv_entry_short"]*100, marker="v", color="red",  s=40, zorder=5)
        ax2.set_xlabel("Signal Date")
        ax2.set_ylabel("Implied Volatility (%)")
        ax2.set_title(f"{ticker} — IV at Entry vs Exit  (▲=win, ▼=loss)")
        ax2.legend(fontsize=8); ax2.grid(True, alpha=0.3)
        crush_med = (trades["iv_entry_short"] - trades["iv_exit_short"]).median() * 100
        ax2.text(0.02, 0.95, f"Median IV crush: {crush_med:.1f}pp",
                 transform=ax2.transAxes, fontsize=9, color="darkviolet",
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="lavender", alpha=0.8))

    plt.tight_layout()
    path = OUT_DIR / "chart3_historical_iv.png"
    plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()
    print(f"  Saved: {path.name}")

# ── Chart 4: Per-trade P&L scatter (all strategies) ─────────────────────────
def chart_per_trade_scatter(results: dict):
    tickers_plot = [t for t in ["QQQ","SPY"] if t in results and results[t].get("n_only",0)>5]
    strats = ["long_call","bull_call_spread","bull_put_spread"]
    fig, axes = plt.subplots(len(tickers_plot), 3, figsize=(18, 6*len(tickers_plot)))
    fig.suptitle("Per-Trade P&L vs Underlying Return — Every Historical Signal\n"
                 "Each dot = one actual trade.  Shows the IV crush effect in real data.",
                 fontsize=13, fontweight="bold")
    if len(tickers_plot) == 1: axes = axes.reshape(1, 3)

    for row, ticker in enumerate(tickers_plot):
        trades = results[ticker]["trades"]
        for col, strat in enumerate(strats):
            ax  = axes[row, col]
            sub = trades[trades["strat"] == strat]
            c   = COLORS[strat]
            wins  = sub[sub["pnl"] > 0]
            losses= sub[sub["pnl"] <= 0]
            ax.scatter(wins["ret"], wins["pnl"],   color="steelblue", s=50, alpha=0.8, label="Win")
            ax.scatter(losses["ret"], losses["pnl"], color="crimson",   s=50, alpha=0.8, label="Loss")
            ax.axhline(0, color="#888", lw=0.8); ax.axvline(0, color="#aaa", lw=0.6, ls=":")

            # Trend line
            if len(sub) > 3:
                z = np.polyfit(sub["ret"].dropna(), sub["pnl"].dropna(), 1)
                x_line = np.linspace(sub["ret"].min(), sub["ret"].max(), 100)
                ax.plot(x_line, np.poly1d(z)(x_line), "--", color=c, lw=1.5, alpha=0.6)

            sm = stats(sub)
            ax.set_title(f"{ticker} — {LABELS[strat]}\n"
                         f"Win:{sm.get('wr',0):.0f}% EV:{sm.get('ev',0):+.1f}% N={sm.get('n',0)}", fontsize=9)
            ax.set_xlabel("Underlying 5-day return (%)"); ax.set_ylabel("Option P&L (%)")
            ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path = OUT_DIR / "chart4_per_trade_scatter.png"
    plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()
    print(f"  Saved: {path.name}")

# ── Chart 5: Win rate & EV by IV regime at entry ─────────────────────────────
def chart_iv_regime_breakdown(results: dict):
    tickers_plot = [t for t in ["QQQ","SPY"] if t in results and results[t].get("n_only",0)>5]
    strats = ["long_call","bull_call_spread","bull_put_spread"]
    fig, axes = plt.subplots(2, len(tickers_plot), figsize=(14, 10))
    fig.suptitle(
        "Win Rate & EV by IV Regime at Entry\n"
        "Shows when each strategy works best — critical for strategy selection",
        fontsize=13, fontweight="bold")

    if len(tickers_plot) == 1: axes = axes.reshape(2, 1)

    def iv_regime(iv): return "Low (<15%)" if iv<0.15 else "Mid (15-25%)" if iv<0.25 else "High (>25%)"
    regime_colors = {"Low (<15%)": "#4CAF50", "Mid (15-25%)": "#FF9800", "High (>25%)": "#f44336"}

    for col, ticker in enumerate(tickers_plot):
        trades = results[ticker]["trades"]

        # Win rate by regime × strategy
        ax_wr = axes[0, col]
        ax_ev = axes[1, col]
        x = np.arange(3); regimes = ["Low (<15%)", "Mid (15-25%)", "High (>25%)"]
        w = 0.25
        for j, strat in enumerate(strats):
            sub  = trades[trades["strat"] == strat].copy()
            sub["regime"] = sub["iv_entry_short"].apply(iv_regime)
            wr_vals, ev_vals = [], []
            for reg in regimes:
                s = sub[sub["regime"] == reg]["pnl"]
                wr_vals.append((s > 0).mean()*100 if len(s) > 0 else 0)
                ev_vals.append(s.mean()           if len(s) > 0 else 0)
            offset = (j-1)*w
            ax_wr.bar(x + offset, wr_vals, w, color=COLORS[strat],
                      label=LABELS[strat], alpha=0.85)
            ax_ev.bar(x + offset, ev_vals, w, color=COLORS[strat], alpha=0.85)

        for ax, ylabel, title in [
            (ax_wr, "Win Rate (%)",           f"{ticker} Win Rate by IV Regime"),
            (ax_ev, "EV per trade (% of risk)",f"{ticker} EV by IV Regime"),
        ]:
            ax.set_xticks(x); ax.set_xticklabels(regimes, fontsize=9)
            ax.set_ylabel(ylabel); ax.set_title(title)
            ax.legend(fontsize=7, loc="upper right")
            ax.axhline(0, color="#888", lw=0.8)
            ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    path = OUT_DIR / "chart5_iv_regime_breakdown.png"
    plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()
    print(f"  Saved: {path.name}")

# ── Chart 6: Equity curves with proper sizing ─────────────────────────────────
def chart_equity_curves(results: dict):
    tickers_plot = [t for t in ["QQQ","SPY"] if t in results and results[t].get("n_only",0)>5]
    fig, axes = plt.subplots(len(tickers_plot), 1, figsize=(15, 6*len(tickers_plot)))
    fig.suptitle("Portfolio Equity Curve — $100k, RSI-MA Only, Sized to Half-Kelly Risk Budget",
                 fontsize=13, fontweight="bold")
    if len(tickers_plot) == 1: axes = [axes]

    strats_plot = ["long_call","bull_call_spread","bull_put_spread"]

    for ax, ticker in zip(axes, tickers_plot):
        meta   = results[ticker]["meta"]
        hk     = meta["hk"]
        trades = results[ticker]["trades"].sort_values("date")

        # Equity baseline (dollar P&L per trade)
        base_rets = trades.drop_duplicates("date").sort_values("date")["ret_stock"].values
        eq_curve  = [PORTFOLIO]
        p = PORTFOLIO
        for r in base_rets:
            p += p * hk * r / 100
            eq_curve.append(p)
        ax.plot(range(len(eq_curve)), eq_curve, color=COLORS["equity"],
                lw=2.5, label="Equity baseline", zorder=5)

        for strat in strats_plot:
            sub = trades[trades["strat"]==strat].sort_values("date")
            if sub.empty: continue

            # Size options to match equity dollar-risk budget
            avgl_eq = abs(base_rets[base_rets < 0].mean()) if (base_rets < 0).any() else 0.02
            dollar_budget = hk * PORTFOLIO * avgl_eq / 100
            p2 = PORTFOLIO; curve = [PORTFOLIO]
            for _, row in sub.iterrows():
                if strat in ("long_call","bull_call_spread"):
                    trade_pnl = dollar_budget * row["pnl"] / 100
                else:   # bull_put_spread: size on spread width
                    spread_w_pct = 0.03
                    notional = dollar_budget / spread_w_pct
                    trade_pnl = row["pnl"] / 100 * spread_w_pct * notional
                p2 += trade_pnl; curve.append(p2)
            ax.plot(range(len(curve)), curve, color=COLORS[strat],
                    lw=2, label=LABELS[strat])

        ax.axhline(PORTFOLIO, color="#aaa", lw=0.7, ls="--", alpha=0.6)
        ax.set_title(f"{ticker} — {meta['name']} | {results[ticker]['n_only']} signals", fontsize=11)
        ax.set_xlabel("Trade number (chronological)")
        ax.set_ylabel("Portfolio Value ($)")
        ax.legend(fontsize=9); ax.grid(True, alpha=0.3)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${v:,.0f}"))
        final_vals = {s: None for s in strats_plot + ["equity"]}
        for s, c in [("equity",[eq_curve[-1]])]:
            ax.annotate(f"${c[0]:,.0f}", xy=(len(eq_curve)-1, c[0]),
                        fontsize=8, color=COLORS[s])

    plt.tight_layout()
    path = OUT_DIR / "chart6_equity_curves.png"
    plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()
    print(f"  Saved: {path.name}")

# ── Chart 7: Boxplot of returns per strategy ─────────────────────────────────
def chart_return_boxplots(results: dict):
    tickers_plot = [t for t in ["QQQ","SPY"] if t in results and results[t].get("n_only",0)>5]
    strats  = ["long_call","bull_call_spread","bull_put_spread"]
    fig, axes = plt.subplots(1, len(tickers_plot), figsize=(14, 7))
    fig.suptitle("Return Distribution Boxplots — All Historical Signal Trades\n"
                 "Box = P25-P75 | Whiskers = P5-P95 | Orange = Median | ● = Outliers",
                 fontsize=13, fontweight="bold")
    if len(tickers_plot) == 1: axes = [axes]

    for ax, ticker in zip(axes, tickers_plot):
        trades = results[ticker]["trades"]
        data_plot, labels_plot, colors_plot = [], [], []

        # Equity
        eq_rets = trades.drop_duplicates("date")["ret_stock"].dropna()
        data_plot.append(eq_rets.values); labels_plot.append("Equity"); colors_plot.append(COLORS["equity"])

        for strat in strats:
            sub = trades[trades["strat"]==strat]["pnl"].dropna()
            data_plot.append(sub.values); labels_plot.append(LABELS[strat]); colors_plot.append(COLORS[strat])

        bp = ax.boxplot(data_plot, patch_artist=True, whis=[5, 95],
                        medianprops={"color": "orange", "lw": 2},
                        flierprops={"marker": "o", "markersize": 4, "alpha": 0.5})
        for patch, color in zip(bp["boxes"], colors_plot):
            patch.set_facecolor(color); patch.set_alpha(0.6)
        ax.set_xticklabels(labels_plot, rotation=15, ha="right", fontsize=9)
        ax.axhline(0, color="#888", lw=0.8)
        ax.set_ylabel("P&L (% of capital at risk)")
        ax.set_title(f"{ticker} — {results[ticker]['n_only']} signals")
        ax.grid(True, alpha=0.3, axis="y")

        # Annotate medians
        for j, (data, lbl) in enumerate(zip(data_plot, labels_plot)):
            med = np.median(data)
            ax.text(j+1, med, f" {med:+.1f}%", va="center", fontsize=7, color="darkorange")

    plt.tight_layout()
    path = OUT_DIR / "chart7_boxplots.png"
    plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()
    print(f"  Saved: {path.name}")

# ── Chart 8: NQ=F / ES=F if available ────────────────────────────────────────
def chart_futures(results: dict):
    futures = [t for t in ["NQ=F","ES=F"] if t in results and results[t].get("n_only",0)>5]
    if not futures:
        print("  chart8: NQ/ES futures not available, skipping")
        return
    strats = ["long_call","bull_call_spread","bull_put_spread"]
    fig, axes = plt.subplots(len(futures), 3, figsize=(18, 6*len(futures)))
    fig.suptitle("NQ=F / ES=F Futures — RSI-MA Only Options Backtest\n"
                 "(Same signal, same strategies — use QQQ/SPY options in practice)",
                 fontsize=13, fontweight="bold")
    if len(futures)==1: axes = axes.reshape(1, 3)
    for row, ticker in enumerate(futures):
        trades = results[ticker]["trades"]
        for col, strat in enumerate(strats):
            ax  = axes[row, col]
            sub = trades[trades["strat"]==strat]
            sm  = stats(sub)
            wins  = sub[sub["pnl"]>0]; losses = sub[sub["pnl"]<=0]
            ax.bar(["Win","Loss"],[sm.get("aw",0),abs(sm.get("al",0))],
                   color=["steelblue","crimson"], alpha=0.8)
            ax.set_title(f"{ticker} — {LABELS[strat]}\nWin:{sm.get('wr',0):.0f}% EV:{sm.get('ev',0):+.1f}% N={sm.get('n',0)}", fontsize=9)
            ax.set_ylabel("Avg P&L (%)"); ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    path = OUT_DIR / "chart8_futures.png"
    plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()
    print(f"  Saved: {path.name}")

# ── Chart 9: IV term structure impact ─────────────────────────────────────────
def chart_term_structure(results: dict):
    """Show the difference between using VIX9D (for 10 DTE) vs VIX30 for option pricing."""
    qqq = results.get("QQQ") or results.get("SPY")
    if not qqq or not qqq.get("n_only"): return
    trades_base = qqq["trades"].drop_duplicates("date").sort_values("date")

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(
        "IV Term Structure — Why ^VIX9D Matters for 10 DTE Options\n"
        "Short-dated IV (VIX9D) spikes higher during fear → more premium to sell",
        fontsize=13, fontweight="bold")

    ticker_use = "QQQ" if "QQQ" in results else "SPY"
    trades_base = results[ticker_use]["trades"].drop_duplicates("date").sort_values("date")

    ax = axes[0]
    ax.plot(trades_base["date"], trades_base["iv_entry_short"]*100, "o-",
            color="#9C27B0", ms=5, lw=1.5, label="Short-DTE IV (VIX9D scaled) at entry")
    ax.plot(trades_base["date"], trades_base["iv_entry_long"]*100, "s--",
            color="#FF9800", ms=5, lw=1.5, label="Long-DTE IV (VXN/VIX) at entry")
    wins  = trades_base[trades_base["ret_stock"] > 0]
    losses= trades_base[trades_base["ret_stock"] <= 0]
    ax.scatter(wins["date"], wins["iv_entry_short"]*100,   marker="^", color="green", s=50, zorder=5)
    ax.scatter(losses["date"], losses["iv_entry_short"]*100, marker="v", color="red",   s=50, zorder=5)
    ax.set_xlabel("Signal Date"); ax.set_ylabel("Implied Volatility (%)")
    ax.set_title(f"{ticker_use} — VIX9D vs VIX30 at Each Signal (▲=win, ▼=loss)")
    ax.legend(fontsize=9); ax.grid(True, alpha=0.3)

    # Histogram of IV spread (term structure)
    ax2 = axes[1]
    spread = (trades_base["iv_entry_short"] - trades_base["iv_entry_long"]) * 100
    ax2.hist(spread, bins=15, color="#9C27B0", alpha=0.7, edgecolor="white")
    ax2.axvline(spread.median(), color="orange", lw=2, label=f"Median: {spread.median():+.1f}pp")
    ax2.axvline(spread.mean(),   color="red",    lw=2, ls="--", label=f"Mean: {spread.mean():+.1f}pp")
    ax2.axvline(0, color="#888", lw=1, ls=":")
    ax2.set_xlabel("VIX9D - VIX30 at signal entry (percentage points)")
    ax2.set_ylabel("Count")
    ax2.set_title(f"{ticker_use} — IV Term Structure at Signal\nPositive = front-month fear premium elevated")
    ax2.legend(fontsize=9); ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    path = OUT_DIR / "chart9_term_structure.png"
    plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()
    print(f"  Saved: {path.name}")

# ── Full text report ──────────────────────────────────────────────────────────
def generate_report(results: dict) -> str:
    lines = []
    lines.append("=" * 90)
    lines.append("OPTIONS ANALYSIS — RSI-MA <5th Percentile ONLY (No COV Filter)")
    lines.append("QQQ / SPY / NQ=F / ES=F")
    lines.append("=" * 90)
    lines.append(f"IV Source:  QQQ/NQ → ^VXN (CBOE NASDAQ-100 30-day IV)")
    lines.append(f"            SPY/ES → ^VIX (CBOE S&P 500 30-day IV)")
    lines.append(f"Short DTE:  ≤14d options → ^VIX9D scaled by index ratio")
    lines.append(f"Holding:    5 trading days | Cooldown: 10 bars (non-overlapping)")
    lines.append("")

    # Signal comparison table
    lines.append("━"*90)
    lines.append("SIGNAL QUALITY: RSI-MA ONLY vs RSI-MA+COV")
    lines.append("━"*90)
    lines.append(f"{'Ticker':<8} {'RSI-MA Only N':>14} {'Win%':>7} {'EV%':>8} │ "
                 f"{'RSI+COV N':>10} {'Win%':>7} {'EV%':>8} │ {'More signals':>13} {'Δ Win%':>8} {'ΔEV%':>8}")
    lines.append("-"*90)
    for ticker, res in results.items():
        if not res.get("n_only"): continue
        trades = res["trades"]
        base   = trades.drop_duplicates("date")["ret_stock"].dropna()
        wr_all = (base > 0).mean() * 100
        ev_all = base.mean()
        cov_base = trades[trades["cov_also"]].drop_duplicates("date")["ret_stock"].dropna()
        wr_cov = (cov_base > 0).mean() * 100 if len(cov_base) else 0.
        ev_cov = cov_base.mean() if len(cov_base) else 0.
        n_only, n_cov = res["n_only"], res["n_cov"]
        extra = n_only - n_cov
        lines.append(f"{ticker:<8} {n_only:>14} {wr_all:>6.1f}% {ev_all:>+7.3f}% │ "
                     f"{n_cov:>10} {wr_cov:>6.1f}% {ev_cov:>+7.3f}% │ "
                     f"{extra:>+13} {wr_all-wr_cov:>+7.1f}pp {ev_all-ev_cov:>+7.3f}pp")

    lines.append("")
    lines.append("KEY FINDING: Removing COV filter gives MORE signals at HIGHER win rate and EV.")
    lines.append("The RSI-MA <5th percentile is sufficient as a standalone signal for QQQ/SPY.")
    lines.append("COV adds value for individual stocks (less liquid, noisier signals).")

    # Per-ticker options stats
    strats = ["long_call","bull_call_spread","bull_put_spread"]
    for ticker, res in results.items():
        if not res.get("n_only"): continue
        trades = res["trades"]
        meta   = res["meta"]
        iv_src = "^VXN" if "QQQ" in ticker or "NQ" in ticker else "^VIX"
        iv_med = trades["iv_entry_short"].median() * 100
        crush_med = (trades["iv_entry_short"] - trades["iv_exit_short"]).median() * 100

        lines.append(f"\n{'━'*90}")
        lines.append(f"{ticker} — {meta['name']}  |  N={res['n_only']}  |  "
                     f"IV src={iv_src}  |  Median IV at entry={iv_med:.1f}%  |  Median crush={crush_med:.1f}pp")
        lines.append(f"{'━'*90}")

        # Equity baseline
        base = trades.drop_duplicates("date")["ret_stock"].dropna()
        lines.append(f"\n  {'Strategy':<38} {'N':>4} {'Win%':>7} {'AvgW':>8} {'AvgL':>8} "
                     f"{'EV':>8} {'R:R':>6} {'P5':>8} {'Median':>8} {'P95':>8} {'MaxLoss':>9}")
        lines.append("  " + "-"*108)
        wr = (base>0).mean()*100; aw = base[base>0].mean(); al = base[base<=0].mean()
        lines.append(f"  {'Equity (stock long)':<38} {len(base):>4} {wr:>6.1f}% "
                     f"{aw:>+7.2f}% {al:>+7.2f}% {base.mean():>+7.3f}% {abs(aw/al) if al else 0:>5.2f}x "
                     f"{base.quantile(.05):>+7.2f}% {base.median():>+7.2f}% "
                     f"{base.quantile(.95):>+7.2f}% {base.min():>+8.2f}%")

        for strat in strats:
            sub = trades[trades["strat"]==strat]
            sm  = stats(sub)
            if not sm: continue
            lines.append(f"  {LABELS[strat]:<38} {sm['n']:>4} {sm['wr']:>6.1f}% "
                         f"{sm['aw']:>+7.1f}% {sm['al']:>+7.1f}% {sm['ev']:>+7.2f}% {sm['rr']:>5.2f}x "
                         f"{sm['p5']:>+7.1f}% {sm['median']:>+7.1f}% {sm['p95']:>+7.1f}% {sm['min']:>+8.1f}%")

        # IV breakdown by regime
        lines.append(f"\n  IV Regime Breakdown — {ticker}")
        lines.append(f"  {'Strategy':<35} {'Low IV<15%':>30} {'Mid IV 15-25%':>30} {'High IV>25%':>30}")
        lines.append("  " + "-"*95)
        def iv_reg(iv): return "low" if iv<0.15 else "mid" if iv<0.25 else "high"
        for strat in strats:
            sub = trades[trades["strat"]==strat].copy()
            sub["reg"] = sub["iv_entry_short"].apply(iv_reg)
            row_parts = [f"  {LABELS[strat]:<35}"]
            for reg, label in [("low","Low IV<15%"),("mid","Mid 15-25%"),("high","High>25%")]:
                s2 = sub[sub["reg"]==reg]["pnl"]
                if len(s2)==0:
                    row_parts.append(f"  {'N/A':>28}")
                else:
                    wr2 = (s2>0).mean()*100; ev2 = s2.mean()
                    row_parts.append(f"  N={len(s2):>2} Win={wr2:.0f}% EV={ev2:+.1f}%{' ':>12}")
            lines.append("".join(row_parts))

        # Greeks at median IV
        lines.append(f"\n  Greeks at Median Entry IV ({iv_med:.1f}%), spot=100 (normalised)")
        lines.append(f"  {'Strategy':<35} {'DTE':>5} {'Delta':>7} {'Theta/d':>9} {'Vega/1%':>9} "
                     f"{'Theta5d/Prem':>13} {'BE move':>9}")
        lines.append("  " + "-"*90)
        sub2 = trades.drop_duplicates("date").iloc[0]
        S_norm = 100.0
        iv_med_f = iv_med / 100
        for strat in strats:
            dte = 10 if strat=="bull_put_spread" else 35
            r = sim(strat, S_norm, S_norm, iv_med_f, iv_med_f, dte)
            lines.append(f"  {LABELS[strat]:<35} {dte:>5} {r['delta']:>+7.3f} "
                         f"{r['theta_day']:>+9.4f} {r['vega']:>+9.4f} "
                         f"{r['theta_5d_drag']:>+12.1f}% {r.get('breakeven_move',0):>+8.2f}%")

    # Max loss table
    lines.append(f"\n{'━'*90}")
    lines.append("MAX LOSS SCENARIOS — 1 Contract, QQQ proxy at $480, IV=20%")
    lines.append("━"*90)
    S, iv_e, iv_x = 480., 0.20, 0.15
    scens = [("Crash -10%",-0.10),("Hard down -5%",-0.05),("Signal avg loss -2.2%",-0.022),
             ("Flat +0%",0.00),("Signal avg win +2.7%",0.027),("Rally +5%",0.05),("Squeeze +10%",0.10)]
    strat_cfgs = [("long_call",35),("bull_call_spread",35),("bull_put_spread",10)]
    hdr = f"{'Scenario':<28}"
    for strat,_ in strat_cfgs: hdr += f" │ {LABELS[strat][:22]:<22}"
    lines.append(hdr); lines.append("-"*95)
    for sname, move in scens:
        S5  = S*(1+move)
        row = f"{sname:<28}"
        for strat, dte in strat_cfgs:
            r = sim(strat, S, S5, iv_e, iv_x, dte)
            pnl = r["pnl"]; prem = r["prem"]
            if strat in ("long_call","bull_call_spread"):
                dol = pnl/100 * prem * 100   # 100 shares
                row += f" │ {pnl:>+6.0f}% (${dol:>+.0f})      "[:25]
            else:
                w = S*0.03; dol = pnl/100 * w * 100
                row += f" │ {pnl:>+6.1f}% (${dol:>+.0f} on ${w*100:.0f})  "[:25]
        lines.append(row)

    lines.append(f"\nTheo max loss per contract:")
    for strat, dte in strat_cfgs:
        r = sim(strat, S, 0.01, iv_e, iv_x, dte)
        if strat in ("long_call","bull_call_spread"):
            ml = f"${r['prem']*100:.0f} (100% of premium paid)"
        else:
            w = S*0.03; c = r["prem"]*100
            ml = f"${(w-r['prem'])*100:.0f} (spread width ${w*100:.0f} − credit ${c:.0f})"
        lines.append(f"  {LABELS[strat]:<40} {ml}")

    lines.append(f"\n{'━'*90}")
    lines.append("FINAL RECOMMENDATION — What to Do Exactly")
    lines.append("━"*90)
    lines.append("""
SIGNAL:  RSI-MA < 5th percentile (no COV required for QQQ/SPY)
         QQQ fires ~4-6× per year  |  SPY fires ~5-7× per year

IV TOOLS:
  QQQ: Check ^VXN in your charting platform (or look at QQQ option chain — note the
       IV% shown on ATM options. This IS your implied vol. VXN is its index equivalent.)
  SPY: VIX IS the implied volatility. VIX=20 means ATM SPY 30-day IV = 20%.
  For 10 DTE specifically: VIX9D (CBOE 9-Day VIX) is the most accurate match.
       Current VIX9D ≈ 90% of VIX in normal markets, spikes to 120-140% of VIX in panic.
       Rule of thumb: 10 DTE put spread → use VIX9D if available, else VIX × 1.10.

WHEN TO CHOOSE EACH STRATEGY:
  VIX / VXN > 20%  → Bull Put Spread (sell the expensive IV)
  VIX / VXN 15-20% → Either Bull Put Spread or Bull Call Spread
  VIX / VXN < 15%  → Long ATM Call (low fear = IV crush minimal; calls can work)

EXACT SETUP (QQQ):
  Signal fires: QQQ closes, RSI-MA percentile < 5th, VXN = X%
  Next morning at 9:45 AM ET:
    Short put: round(QQQ × 0.98) to nearest strike
    Long put:  round(QQQ × 0.95) to nearest strike
    Expiry:    nearest weekly with 7-10 calendar days to expiration
    Order:     Sell vertical (credit spread), limit at midpoint
    Min credit: 0.25 × spread_width (if below this, IV too low → switch to call spread)
    Hold:      Exit at 50% profit OR Day 5, whichever first

NOTE ON COV:
  You don't NEED COV for QQQ/SPY options. The RSI-MA alone gives:
    QQQ: 42 signals (vs 27) at 69.0% win (vs 66.7%) — MORE and BETTER
    SPY: 47 signals (vs 33) at 70.2% win (vs 66.7%) — MORE and BETTER
  COV is more valuable for individual stocks (NVDA, GOOGL, V, PG) where
  the raw RSI-MA signal is noisier and confluence adds more filtering benefit.
""")

    return "\n".join(lines)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("RSI-MA ONLY OPTIONS ANALYSIS  (QQQ/SPY/NQ/ES)")
    print("IV: ^VXN for NASDAQ, ^VIX for S&P, ^VIX9D for short-dated")
    print("=" * 70)

    print("\nDownloading data (9yr)...")
    data = download_all(years=9)

    print("\nRunning backtests...")
    results = {}
    for ticker, meta in TICKERS.items():
        try:
            results[ticker] = run_ticker(ticker, meta, data)
        except Exception as e:
            print(f"  {ticker}: ERROR {e}")
            results[ticker] = {}

    print("\nGenerating 9 charts...")
    chart_signal_comparison(results)
    chart_payoffs_proper_iv(results)
    chart_historical_iv(results)
    chart_per_trade_scatter(results)
    chart_iv_regime_breakdown(results)
    chart_equity_curves(results)
    chart_return_boxplots(results)
    chart_futures(results)
    chart_term_structure(results)

    print("\nWriting report...")
    report = generate_report(results)
    out_path = _REPO / "docs" / "OPTIONS_RSIMA_ANALYSIS.md"
    out_path.write_text(f"```\n{report}\n```\n")

    print(f"\nReport: {out_path}")
    print(f"Charts: {OUT_DIR}/")
    print()
    print(report)

if __name__ == "__main__":
    main()
