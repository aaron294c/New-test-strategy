"""
Phase 26: scan for correct alignment between phase23 ground truth (84 bars) and
NVDA price history. Try daily, weekly, 4h, 1h bars and find the 84-bar window
with highest CV morphology correlation. Then use that alignment to fit CC formulas.
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

def compute_cv_logret(closes, cvLen=20):
    logret = [None]*len(closes)
    for i in range(1, len(closes)):
        if closes[i] > 0 and closes[i-1] > 0:
            logret[i] = math.log(closes[i]/closes[i-1])
    cv = [None]*len(closes)
    for i in range(cvLen, len(closes)):
        w = logret[i-cvLen+1:i+1]
        if any(v is None for v in w): continue
        m = sum(w)/cvLen
        v = sum((x-m)**2 for x in w)/cvLen
        sd = math.sqrt(v)
        cv[i] = (sd/abs(m))*100 if abs(m) > 1e-12 else None
    return cv

def main():
    bars = []
    with (OUT/"phase23_both_panes.csv").open() as f_csv:
        for r in csv.DictReader(f_csv):
            b = {"o_cv": f(r["o_cv"]), "o_cvma": f(r["o_cvma"]), "o_cc": f(r["o_cc"])}
            if all(v is not None for v in b.values()): bars.append(b)
    N = len(bars)
    o_cv = [b["o_cv"] for b in bars]
    o_cc = [b["o_cc"] for b in bars]
    print(f"[26] target: N={N} o_cv range=[{min(o_cv):.2f},{max(o_cv):.2f}] o_cc=[{min(o_cc):.2f},{max(o_cc):.2f}]")

    # Try multiple timeframes
    tf_configs = [
        ("1d",  "2y",  None),
        ("1wk", "5y",  None),
        ("5d",  "5y",  None),
        ("1h",  "60d", None),
    ]
    best = None
    t = yf.Ticker('NVDA')
    for interval, period, _ in tf_configs:
        try:
            h = t.history(period=period, interval=interval)
        except Exception as e:
            print(f"[26] {interval}/{period}: ERROR {e}")
            continue
        closes = [float(c) for c in h['Close'].tolist()]
        dates = [str(d)[:16] for d in h.index.tolist()]
        if len(closes) < N + 25: continue
        cv_calc = compute_cv_logret(closes, cvLen=20)
        valid0 = next((i for i, v in enumerate(cv_calc) if v is not None), None)
        if valid0 is None: continue
        # Scan all 84-bar windows
        best_r = -2; best_start = None
        for start in range(valid0, len(closes) - N + 1):
            win = cv_calc[start:start+N]
            if any(v is None for v in win): continue
            r = corr_coef(win, o_cv)
            if r > best_r:
                best_r = r; best_start = start
        print(f"[26] interval={interval} bars={len(closes)} best_shape_r={best_r:+.3f} start={best_start} window={dates[best_start] if best_start else '?'}..{dates[best_start+N-1] if best_start else '?'}")
        if best and best[0] >= best_r: continue
        best = (best_r, interval, period, closes, dates, best_start)

    if best is None:
        print("[26] no alignment found")
        return

    r_align, interval, period, closes, dates, best_start = best
    print(f"\n[26] Using interval={interval}, CV morphology r={r_align:+.3f}")

    # Build price span with 30 bars lookback buffer
    lookback_buffer = 30
    span_start = max(0, best_start - lookback_buffer)
    price_span = closes[span_start:best_start+N]
    logret_span = [None]
    for i in range(1, len(price_span)):
        logret_span.append(math.log(price_span[i]/price_span[i-1]) if price_span[i-1]>0 else None)
    logp = [math.log(p) if p>0 else None for p in price_span]
    gt_offset = best_start - span_start
    dir_obs = [1 - (p - (-4.6))/2.1 for p in o_cc]

    # Also compute cv on span
    cv_span = compute_cv_logret(price_span, cvLen=20)
    cvma_span = ema(cv_span, 13)
    diff_span = [(c-m) if (c is not None and m is not None) else None for c, m in zip(cv_span, cvma_span)]

    results = []
    def add_test(name, signal):
        if len(signal) != len(price_span): return
        aligned = signal[gt_offset:gt_offset+N]
        r_fit = corr_coef(dir_obs, aligned)
        if r_fit != r_fit: return
        vals_valid = [v for v in aligned if v is not None]
        if not vals_valid: return
        rng = max(vals_valid) - min(vals_valid)
        results.append((name, r_fit, rng, aligned[-1] if aligned else None))

    for L in range(3, 25):
        r_cp_t = pearson_t(price_span, L)
        r_lp_t = pearson_t(logp, L)
        r_lr_t = pearson_t(logret_span, L)
        r_cv_t = pearson_t(cv_span, L)
        r_diff_t = pearson_t(diff_span, L)
        add_test(f"corr(close,t,L={L})", r_cp_t)
        add_test(f"corr(logclose,t,L={L})", r_lp_t)
        add_test(f"corr(logret,t,L={L})", r_lr_t)
        add_test(f"corr(cv,t,L={L})", r_cv_t)
        add_test(f"corr(cv-cvma,t,L={L})", r_diff_t)
        for sm in (3, 5, 7):
            add_test(f"corr(close,t,L={L})-ema{sm}", ema(r_cp_t, sm))
            add_test(f"corr(logclose,t,L={L})-ema{sm}", ema(r_lp_t, sm))
            add_test(f"corr(cv,t,L={L})-ema{sm}", ema(r_cv_t, sm))

    results.sort(key=lambda t: -(abs(t[1])))
    print(f"\n[26] Top 30 by |r_fit|:")
    for name, r_fit, rng, last in results[:30]:
        print(f"  r_fit={r_fit:+.3f} rng={rng:.2f} last={last:+.3f}  {name}")


if __name__ == "__main__":
    main()
