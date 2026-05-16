"""
Phase 25: fetch NVDA daily bars, align to phase23 ground truth via CV match,
then test PRICE-based correlations against o_cc. The CV-only grid max r=0.44
so the original formula must involve price.
"""
import csv, math
from pathlib import Path
import yfinance as yf

OUT = Path("/tmp/tv-cov-out")

def ema(x, n):
    a = 2/(n+1); o = [None]*len(x); s = None
    for i, v in enumerate(x):
        if v is None: o[i] = s; continue
        s = v if s is None else a*v + (1-a)*s
        o[i] = s
    return o

def pearson_xy(a, b, L):
    o = [None]*len(a)
    for i in range(L-1, len(a)):
        xs = a[i-L+1:i+1]; ys = b[i-L+1:i+1]
        if any(v is None for v in xs) or any(v is None for v in ys): continue
        mx = sum(xs)/L; my = sum(ys)/L
        num = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
        dx = math.sqrt(sum((x-mx)**2 for x in xs))
        dy = math.sqrt(sum((y-my)**2 for y in ys))
        o[i] = num/(dx*dy) if dx*dy > 1e-12 else None
    return o

def pearson_t(series, L):
    xs = list(range(L)); mx = sum(xs)/L
    dx = math.sqrt(sum((a-mx)**2 for a in xs))
    o = [None]*len(series)
    for i in range(L-1, len(series)):
        y = series[i-L+1:i+1]
        if any(v is None for v in y): continue
        my = sum(y)/L
        num = sum((a-mx)*(b-my) for a, b in zip(xs, y))
        dy = math.sqrt(sum((b-my)**2 for b in y))
        o[i] = num/(dx*dy) if dx*dy > 1e-12 else None
    return o

def corr_coef(a, b):
    xs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(xs) < 5: return float("nan")
    mx = sum(x for x, _ in xs)/len(xs); my = sum(y for _, y in xs)/len(xs)
    num = sum((x-mx)*(y-my) for x, y in xs)
    dx = math.sqrt(sum((x-mx)**2 for x, _ in xs))
    dy = math.sqrt(sum((y-my)**2 for _, y in xs))
    return num/(dx*dy) if dx*dy > 1e-12 else float("nan")

def f(s):
    try: return float(s)
    except: return None


def compute_cv(closes, cvLen=20, maLen=13, varScale=1, mode="logret"):
    """Compute CV. mode:
       'logret' -> stdev(logret)/|mean(logret)|*100
       'close'  -> stdev(close)/|mean(close)|*100
       'ret'    -> stdev(pctret)/|mean(pctret)|*100
    """
    if mode == "logret":
        src = [None]*len(closes)
        for i in range(1, len(closes)):
            if closes[i] > 0 and closes[i-1] > 0:
                src[i] = math.log(closes[i]/closes[i-1])
    elif mode == "ret":
        src = [None]*len(closes)
        for i in range(1, len(closes)):
            if closes[i-1] > 0:
                src[i] = (closes[i]-closes[i-1])/closes[i-1]
    else:
        src = closes[:]
    cv = [None]*len(closes)
    for i in range(cvLen, len(closes)):
        w = src[i-cvLen+1:i+1]
        if any(v is None for v in w): continue
        m = sum(w)/cvLen
        v = sum((x-m)**2 for x in w)/cvLen
        sd = math.sqrt(v)
        cv[i] = (sd/abs(m))*100*varScale if abs(m) > 1e-12 else None
    cvma = ema(cv, maLen)
    return cv, cvma

def main():
    # Load phase23 ground truth
    bars = []
    with (OUT/"phase23_both_panes.csv").open() as f_csv:
        for r in csv.DictReader(f_csv):
            b = {"o_cv": f(r["o_cv"]), "o_cvma": f(r["o_cvma"]), "o_cc": f(r["o_cc"])}
            if all(v is not None for v in b.values()): bars.append(b)
    N = len(bars)
    o_cv = [b["o_cv"] for b in bars]
    o_cc = [b["o_cc"] for b in bars]
    dir_obs = [1 - (p - (-4.6))/2.1 for p in o_cc]
    print(f"[25] phase23 bars={N}, last o_cv={o_cv[-1]:.3f}, last o_cc={o_cc[-1]:.3f}")

    # Fetch NVDA daily
    t = yf.Ticker('NVDA')
    h = t.history(period='2y', interval='1d')
    closes = [float(c) for c in h['Close'].tolist()]
    dates  = [str(d)[:10] for d in h.index.tolist()]
    print(f"[25] NVDA bars={len(closes)}, first={dates[0]}, last={dates[-1]}")

    # Align by date: last N daily bars = last 84 visible bars on the chart.
    # User says CV morphology matches so this assumption is safe.
    best_start = len(closes) - N
    print(f"[25] aligned by date: start={best_start} ({dates[best_start]}..{dates[-1]})")
    # Check morphology correlation
    cv_calc, _ = compute_cv(closes, cvLen=20, maLen=13, varScale=1, mode="logret")
    calc_slice = cv_calc[best_start:best_start+N]
    r_shape = corr_coef(calc_slice, o_cv)
    print(f"[25] CV morphology correlation (sanity): {r_shape:+.3f}")

    print(f"[25] alignment check (last 5):")
    for i in range(N-5, N):
        print(f"  bar {i}: calc_cv={calc_slice[i]:.3f} vs o_cv={o_cv[i]:.3f} | o_cc={o_cc[i]:+.2f}")

    # Build aligned series of PRICE data for the 84 bars
    # We need lookback for price-based correlation, so expand start by up to 25 bars
    lookback_buffer = 30
    span_start = max(0, best_start - lookback_buffer)
    price_span = closes[span_start:best_start+N]
    logret_span = [None]
    for i in range(1, len(price_span)):
        logret_span.append(math.log(price_span[i]/price_span[i-1]) if price_span[i-1]>0 else None)
    # Index where the 84-bar ground truth starts within this span
    gt_offset = best_start - span_start

    # Candidate inputs for correlation (computed over the span):
    logp = [math.log(p) if p>0 else None for p in price_span]
    # Also CV on this span
    cv_span, cvma_span = compute_cv(price_span, cvLen=20, maLen=13, varScale=1)
    diff_span = [(c-m) if (c is not None and m is not None) else None for c, m in zip(cv_span, cvma_span)]

    # Test correlation of various inputs with bar_index, get the signal across span,
    # then extract the 84 aligned bars and fit vs o_cc.
    results = []

    def add_test(name, signal):
        # signal is aligned to price_span; extract the 84 bars
        if len(signal) != len(price_span): return
        aligned = signal[gt_offset:gt_offset+N]
        r_fit = corr_coef(dir_obs, aligned)
        vals_valid = [v for v in aligned if v is not None]
        if not vals_valid: return
        rng = max(vals_valid) - min(vals_valid)
        results.append((name, r_fit, rng, aligned[-1] if aligned else None))

    # PRICE-based correlations
    for L in range(3, 25):
        # Pearson r of close vs time
        r_cp_t = pearson_t(price_span, L)
        add_test(f"corr(close,t,L={L})", r_cp_t)
        # Pearson r of log(close) vs time
        r_lp_t = pearson_t(logp, L)
        add_test(f"corr(logclose,t,L={L})", r_lp_t)
        # Pearson r of logret vs time
        r_lr_t = pearson_t(logret_span, L)
        add_test(f"corr(logret,t,L={L})", r_lr_t)
        # Pearson r of close vs cv
        r_cp_cv = pearson_xy(price_span, cv_span, L)
        add_test(f"corr(close,cv,L={L})", r_cp_cv)
        # Pearson r of logret vs cv
        r_lr_cv = pearson_xy(logret_span, cv_span, L)
        add_test(f"corr(logret,cv,L={L})", r_lr_cv)
        # Pearson r of logret vs (cv-cvma)
        r_lr_diff = pearson_xy(logret_span, diff_span, L)
        add_test(f"corr(logret,cv-cvma,L={L})", r_lr_diff)
        # Pearson r of close vs (cv-cvma)
        r_cp_diff = pearson_xy(price_span, diff_span, L)
        add_test(f"corr(close,cv-cvma,L={L})", r_cp_diff)

        # Apply EMA smoothing on top
        for sm in (3, 5, 7):
            add_test(f"corr(close,t,L={L})-ema{sm}", ema(r_cp_t, sm))
            add_test(f"corr(logclose,t,L={L})-ema{sm}", ema(r_lp_t, sm))
            add_test(f"corr(close,cv,L={L})-ema{sm}", ema(r_cp_cv, sm))

    # Sort by |r_fit| (accept negative correlations too — we can flip sign)
    results.sort(key=lambda t: -(abs(t[1]) if t[1]==t[1] else 0))
    print(f"\n[25] Top 30 by |r_fit| (any direction):")
    for name, r_fit, rng, last in results[:30]:
        if r_fit == r_fit:
            print(f"  r_fit={r_fit:+.3f} rng={rng:.2f} last={last:+.3f}  {name}")

    # Top by r_fit AND wide range (close to target 1.95)
    ok = [r for r in results if r[1]==r[1] and abs(r[1])>=0.5]
    ok.sort(key=lambda t: -t[2])
    print(f"\n[25] r_fit>=0.5 sorted by range:")
    for name, r_fit, rng, last in ok[:20]:
        print(f"  r_fit={r_fit:+.3f} rng={rng:.2f} last={last:+.3f}  {name}")


if __name__ == "__main__":
    main()
