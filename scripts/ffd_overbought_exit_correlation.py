"""
Does RSI-MA > 50th Percentile AND FFD > 65 Mark Tops / Good Exit Points?
========================================================================
The user's question: the entry-side "Signal A" confluence this session
validated is the OVERSOLD pairing (RSI-MA < 5th pct + low FFD = "FFD<40").
This script tests its OVERBOUGHT mirror as an EXIT/avoid-buying signal:

    RSI-MA percentile > 50th   AND   FFD-norm > 65

...evaluated overlapping/"ASAP" (every qualifying bar = a look — maximum
statistical power for a first read; matches the fastest-validated regime
from ffd_cov_confluence_replication.py). If this combination reliably
precedes price ROLLING OVER, forward returns from the signal bar should
run negative and "down %" should run high — i.e. it marks tops / is a good
place to trim or avoid fresh entries. If forward returns are flat or
positive, the combination carries no exit signal of its own.

Canonical functions only — no re-derivation:
    rolling_percentile / calculate_rsi_ma  -> backend/macro_instruments.py
    compute_ffd_norm / build_fd_weights    -> backend/ffd_indicator.py
    SWING_FRAMEWORK_TICKERS                -> backend/macdv_calculator.py

NOTE: this is a first-pass / single-regime read (overlapping only). Per the
noise-filtering discipline this session established (it's what separated
GOOGL/XLI as noise from the validated 16-name FFD<40 cohort), do NOT treat
any single-regime "it marks tops" finding here as confirmed -- a non-overlap
and/or DCA-cluster cross-check would be the natural follow-up before acting
on it. Results print to console / /tmp only; nothing is written into
docs/SIGNAL_METRICS_REFERENCE.md.
"""

import sys
import warnings
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from macro_instruments import calculate_rsi_ma                     # noqa: E402
from macdv_calculator import SWING_FRAMEWORK_TICKERS               # noqa: E402
from ffd_indicator import build_fd_weights, compute_ffd_norm       # noqa: E402

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
RSI_MA_LOOKBACK = 252
PCT_THRESH_HI   = 50.0     # RSI-MA percentile > 50th  (overbought mirror of "<5th")
FFD_THRESH_HI   = 65.0     # FFD-norm > 65             (overbought mirror of "<40")
HORIZONS        = [5, 10, 21]
MIN_TRADES      = 8

TICKERS = list(SWING_FRAMEWORK_TICKERS)

END_DATE   = datetime(2026, 6, 6)
START_DATE = END_DATE - timedelta(days=9 * 365 + 10)


# ---------------------------------------------------------------------------
# Reference percentile -- identical formula to every other script this session
# ---------------------------------------------------------------------------
def rolling_percentile(close):
    rsi_ma = calculate_rsi_ma(close)
    return rsi_ma.rolling(window=RSI_MA_LOOKBACK, min_periods=RSI_MA_LOOKBACK).apply(
        lambda w: float((w[:-1] < w[-1]).sum() / (len(w) - 1) * 100),
        raw=True,
    )


# ---------------------------------------------------------------------------
# Overlapping / ASAP signal extraction -- every qualifying bar = a look,
# forward returns captured at each horizon in HORIZONS
# ---------------------------------------------------------------------------
def find_overbought_signals(pct, ffd, close):
    aligned = pd.DataFrame({"pct": pct, "ffd": ffd, "close": close}).dropna()
    pcts, ffds, closes = (aligned["pct"].to_numpy(), aligned["ffd"].to_numpy(),
                          aligned["close"].to_numpy())
    n = len(aligned)
    max_h = max(HORIZONS)

    fwd = {h: [] for h in HORIZONS}
    for i in range(n - max_h):
        if not (pcts[i] > PCT_THRESH_HI and ffds[i] > FFD_THRESH_HI):
            continue
        entry = closes[i]
        if entry <= 0:
            continue
        for h in HORIZONS:
            exit_ = closes[i + h]
            if exit_ > 0:
                fwd[h].append((exit_ / entry - 1.0) * 100.0)
    return fwd


# ---------------------------------------------------------------------------
# Metrics -- "down %" / avg-down / avg-up frame the TOP-MARKING question
# directly: does price tend to fall (not rise) after the signal fires?
# ---------------------------------------------------------------------------
def stats_block(rets):
    if len(rets) < MIN_TRADES:
        return None
    rets = np.array(rets)
    down, up = rets[rets < 0], rets[rets >= 0]
    n = len(rets)
    return {
        "n": n,
        "ev": float(rets.mean()),
        "down_pct": 100.0 * len(down) / n,
        "avg_down": float(down.mean()) if len(down) else 0.0,
        "avg_up": float(up.mean()) if len(up) else 0.0,
    }


def fmt(b):
    if b is None:
        return "n<8 (insufficient)"
    return (f"n={b['n']:<4} EV={b['ev']:+5.2f}%  Down%={b['down_pct']:5.1f}%  "
            f"AvgDown={b['avg_down']:+5.2f}%  AvgUp={b['avg_up']:+5.2f}%")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    fd_weights = build_fd_weights()
    fd_warmup = len(fd_weights)

    sep = "=" * 118
    print(sep)
    print("DOES 'RSI-MA > 50th PCT + FFD > 65' MARK TOPS / GOOD EXIT POINTS?  (overlapping/ASAP, single-regime first read)")
    print(f"9-year window | every qualifying bar = a look | forward returns at D{HORIZONS} | "
          f"a TOP-MARKING signal should show NEGATIVE EV and HIGH Down%")
    print(sep)

    per_ticker = []
    for idx, ticker in enumerate(TICKERS, 1):
        try:
            raw = yf.download(ticker, start=START_DATE, end=END_DATE,
                              auto_adjust=True, progress=False)
            if raw.empty:
                print(f"  [{idx:2d}/{len(TICKERS)}] {ticker:<10} -- no data, skipped")
                continue
            close = raw["Close"].squeeze().dropna()
            if len(close) < RSI_MA_LOOKBACK + max(HORIZONS) + 20:
                print(f"  [{idx:2d}/{len(TICKERS)}] {ticker:<10} -- insufficient history, skipped")
                continue

            pct = rolling_percentile(close)
            ffd = compute_ffd_norm(close, fd_weights, fd_warmup)

            fwd = find_overbought_signals(pct, ffd, close)
            blocks = {h: stats_block(fwd[h]) for h in HORIZONS}
            per_ticker.append((ticker, blocks))

            n5 = blocks[HORIZONS[0]]["n"] if blocks[HORIZONS[0]] else 0
            print(f"  [{idx:2d}/{len(TICKERS)}] {ticker:<10} signals: n={n5:<4} "
                  f"(RSI-MA>{PCT_THRESH_HI:.0f} & FFD>{FFD_THRESH_HI:.0f})")
        except Exception as exc:
            print(f"  [{idx:2d}/{len(TICKERS)}] {ticker:<10} -- ERROR: {exc}")

    # ── Per-horizon summary tables ─────────────────────────────────────────
    for h in HORIZONS:
        print(f"\n{sep}")
        print(f"FORWARD D{h} RETURNS FROM SIGNAL BAR  (RSI-MA>{PCT_THRESH_HI:.0f} & FFD>{FFD_THRESH_HI:.0f})")
        print(sep)
        print(f"\n  {'Ticker':<10} | {'D' + str(h) + ' forward stats':<60}")
        print(f"  {'-'*10} | {'-'*60}")

        evs, downs = [], []
        neg_ev_count = 0
        for ticker, blocks in per_ticker:
            b = blocks[h]
            print(f"  {ticker:<10} | {fmt(b)}")
            if b is not None:
                evs.append(b["ev"])
                downs.append(b["down_pct"])
                if b["ev"] < 0:
                    neg_ev_count += 1

        if evs:
            arr_ev, arr_dn = np.array(evs), np.array(downs)
            n_cmp = len(evs)
            print(f"\n  -> Negative forward EV in {neg_ev_count}/{n_cmp} names "
                  f"({100*neg_ev_count/n_cmp:.0f}%)")
            print(f"  -> Mean forward EV = {arr_ev.mean():+.3f}%  (stdev {arr_ev.std():.3f})   "
                  f"|   Mean Down% = {arr_dn.mean():.1f}%  (stdev {arr_dn.std():.1f})")

    print(f"\n{sep}")
    print("INTERPRETATION")
    print("  TOP-MARKING evidence would look like: negative mean forward EV AND Down% meaningfully")
    print("  above 50% AND |AvgDown| > |AvgUp| -- i.e. price tends to fall, and falls harder than it")
    print("  rises, after the signal fires. If EV clusters near zero / positive, or Down% sits near")
    print("  50%, the combination carries no exit signal -- it's just 'price has been strong lately,'")
    print("  which is not the same as 'price is about to roll over.'")
    print("")
    print("  REMEMBER: this is ONE regime (overlapping/ASAP). This session's own track record showed")
    print("  GOOGL/XLI looked like genuine FFD<40 beneficiaries in 2 regimes but failed a 3rd-regime")
    print("  cross-check. Don't trust a single-regime 'marks tops' read here without the same")
    print("  non-overlap / DCA-cluster cross-validation before acting on it.")
    print(sep)


if __name__ == "__main__":
    main()
