"""
Phase 24: comprehensive CC formula search using the 84-bar ground-truth
dataset from phase23 (both panes scraped). Previously only had 38-49 bars.
Try MANY candidate formulas; find one that explains the wide ±1 r swings.
"""
import csv, math
from pathlib import Path

OUT = Path("/tmp/tv-cov-out")

def ema(x, n):
    a = 2/(n+1); o = [None]*len(x); s = None
    for i, v in enumerate(x):
        if v is None: o[i] = s; continue
        s = v if s is None else a*v + (1-a)*s
        o[i] = s
    return o

def sma(x, n):
    o = [None]*len(x)
    for i in range(n-1, len(x)):
        w = x[i-n+1:i+1]
        if any(v is None for v in w): continue
        o[i] = sum(w)/n
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

def corr_coef(a, b):
    xs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(xs) < 5: return float("nan")
    mx = sum(x for x, _ in xs)/len(xs); my = sum(y for _, y in xs)/len(xs)
    num = sum((x-mx)*(y-my) for x, y in xs)
    dx = math.sqrt(sum((x-mx)**2 for x, _ in xs))
    dy = math.sqrt(sum((y-my)**2 for _, y in xs))
    return num/(dx*dy) if dx*dy > 1e-12 else float("nan")

def affine(obs, com):
    xs = [(c, s) for c, s in zip(com, obs) if c is not None and s is not None]
    if len(xs) < 5: return None, None, None
    mc = sum(c for c, _ in xs)/len(xs); ms = sum(s for _, s in xs)/len(xs)
    var = sum((c-mc)**2 for c, _ in xs); cov = sum((c-mc)*(s-ms) for c, s in xs)
    a = cov/var if var > 1e-12 else 0; b = ms - a*mc
    rms = math.sqrt(sum((s-(a*c+b))**2 for c, s in xs)/len(xs))
    return a, b, rms

def f(s):
    try: return float(s)
    except: return None


def main():
    bars = []
    with (OUT/"phase23_both_panes.csv").open() as f_csv:
        for r in csv.DictReader(f_csv):
            b = {"o_cv": f(r["o_cv"]), "o_cvma": f(r["o_cvma"]), "o_cc": f(r["o_cc"])}
            if all(v is not None for v in b.values()): bars.append(b)
    N = len(bars)
    cv   = [b["o_cv"] for b in bars]       # original CV = effectively cvPct
    cvma = [b["o_cvma"] for b in bars]
    cc   = [b["o_cc"] for b in bars]
    dir_obs = [1 - (p - (-4.6))/2.1 for p in cc]
    diff = [c-m for c, m in zip(cv, cvma)]
    ratio = [(c/m if m else 0) - 1 for c, m in zip(cv, cvma)]
    logcv = [math.log(v) if v and v > 0 else None for v in cv]
    loglike = [math.log(v + 1e-3) for v in cv]

    print(f"[24] bars={N}")
    print(f"[24] o_cc range=[{min(cc):+.2f},{max(cc):+.2f}]  dir range=[{min(dir_obs):+.3f},{max(dir_obs):+.3f}]")

    # Basic inputs to test for correlation vs time
    inputs = {
        "cv": cv,
        "cvma": cvma,
        "cv-cvma": diff,
        "cv/cvma-1": ratio,
        "log(cv)": logcv,
    }

    results = []
    # corr vs t, with smoothing variants
    for src_name, src_data in inputs.items():
        for L in range(3, 22):
            rs = pearson_t(src_data, L)
            for sm_name in ("none", "ema2", "ema3", "ema5", "sma3", "sma5"):
                if sm_name == "none": sm = rs
                elif sm_name.startswith("ema"): sm = ema(rs, int(sm_name[3:]))
                else: sm = sma([v if v is not None else 0 for v in rs], int(sm_name[3:]))
                if len(sm) != N: continue
                r_fit = corr_coef(dir_obs, sm)
                if r_fit == r_fit:
                    a, b, rms = affine(dir_obs, sm)
                    last = sm[-1]
                    last_cc = -4.6 + 2.1*(1 - (last if last is not None else 0))
                    # Range of prediction (want wide range near ±1)
                    vals_valid = [v for v in sm if v is not None]
                    sm_range = (max(vals_valid) - min(vals_valid)) if vals_valid else 0
                    results.append((f"{src_name}~t", L, sm_name, r_fit, rms, a, b, last_cc, sm_range))

    # Also try cv~cvma correlations
    for L in range(3, 22):
        rs = pearson_xy(cv, cvma, L)
        for sm_name in ("none", "ema3", "ema5"):
            if sm_name == "none": sm = rs
            else: sm = ema(rs, int(sm_name[3:]))
            if len(sm) != N: continue
            r_fit = corr_coef(dir_obs, sm)
            if r_fit == r_fit:
                a, b, rms = affine(dir_obs, sm)
                last = sm[-1]
                last_cc = -4.6 + 2.1*(1 - (last if last is not None else 0))
                vals_valid = [v for v in sm if v is not None]
                sm_range = (max(vals_valid) - min(vals_valid)) if vals_valid else 0
                results.append((f"cv~cvma", L, sm_name, r_fit, rms, a, b, last_cc, sm_range))

    # Sort by fit quality
    results.sort(key=lambda t: -t[3])
    print(f"\n[24] Top 25 candidates by morphology fit:")
    print(f"{'r_fit':>7} {'rms':>5} {'input':>12} L={'':>2} {'sm':>5}  {'slope':>6}  {'last':>7} {'range':>5}")
    for src, L, sm, r_fit, rms, a, b, last, rng in results[:25]:
        print(f"  {r_fit:+.3f} {rms:.3f} {src:>12} L={L:<2} {sm:>5}  a={a:+.3f}  last={last:+.2f} rng={rng:.2f}")

    # Also show the best with HIGHEST prediction range (so the prediction visually swings like the target)
    # Filter to r_fit >= 0.5 then sort by range
    good_fit = [r for r in results if r[3] >= 0.5]
    good_fit.sort(key=lambda t: -t[8])
    print(f"\n[24] Best wide-range candidates (r_fit>=0.5, max prediction range):")
    for src, L, sm, r_fit, rms, a, b, last, rng in good_fit[:15]:
        print(f"  r_fit={r_fit:+.3f} {src:>12} L={L:<2} {sm:>5}  a={a:+.3f}  last={last:+.2f} pred_range={rng:.2f} (target range=1.95)")


if __name__ == "__main__":
    main()
