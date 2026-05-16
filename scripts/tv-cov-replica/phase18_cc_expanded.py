"""
Phase 18: expanded grid search — test negated correlations, linreg slopes,
short lookbacks, and Fisher transforms. Key insight from phase17: predicted
r has correct SIGN but ~57% of target magnitude.
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

def linreg_slope(series, L):
    # Slope of best-fit line; normalized by stdev of y to get dimensionless [-1,+1] if scaled
    xs = list(range(L)); mx = (L-1)/2
    denom = sum((x-mx)**2 for x in xs)
    o = [None]*len(series)
    for i in range(L-1, len(series)):
        y = series[i-L+1:i+1]
        if any(v is None for v in y): continue
        my = sum(y)/L
        num = sum((x-mx)*(b-my) for x, b in zip(xs, y))
        slope = num/denom if denom > 0 else 0
        sy = math.sqrt(sum((b-my)**2 for b in y)/L)
        o[i] = slope/(sy+1e-9) * math.sqrt(L)  # standardized slope
    return o

def fisher(r_series):
    o = [None]*len(r_series)
    for i, r in enumerate(r_series):
        if r is None: continue
        rc = max(-0.9999, min(0.9999, r))
        o[i] = 0.5 * math.log((1+rc)/(1-rc))
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


def main():
    bars = []
    with (OUT/"phase14_nvda.csv").open() as f:
        for r in csv.DictReader(f):
            try: bars.append({"cv":float(r["cv"]),"cv_ma":float(r["cv_ma"]),"cc":float(r["cc"])})
            except: pass
    N = len(bars)
    cv = [b["cv"] for b in bars]
    cvma = [b["cv_ma"] for b in bars]
    cc = [b["cc"] for b in bars]
    diff = [c-m for c, m in zip(cv, cvma)]
    dir_obs = [1 - (p - (-4.6))/2.1 for p in cc]

    inputs = {
        "cv": cv,
        "cvma": cvma,
        "cv-cvma": diff,
        "neg_cv": [-v for v in cv],
        "neg_diff": [-v for v in diff],
    }
    results = []
    for src_name, src_data in inputs.items():
        for L in range(3, 21):
            rs = pearson_t(src_data, L)
            for tr_name in ("raw", "fisher"):
                ser = rs if tr_name == "raw" else fisher(rs)
                for sm_name in ("none", "ema3", "ema5", "ema7", "ema10", "sma5"):
                    if sm_name == "none": sm = ser
                    elif sm_name.startswith("ema"): sm = ema(ser, int(sm_name[3:]))
                    else: sm = sma([v if v is not None else 0 for v in ser], int(sm_name[3:]))
                    if len(sm) != N: continue
                    r_fit = corr_coef(dir_obs, sm)
                    if r_fit == r_fit:
                        a, b, rms = affine(dir_obs, sm)
                        last = sm[-1]
                        last_cc = -4.6 + 2.1*(1 - (last if last is not None else 0))
                        results.append((src_name, "corr_t", L, tr_name, sm_name, r_fit, rms, a, b, last_cc))

    # Linreg slope also
    for src_name, src_data in inputs.items():
        for L in range(3, 21):
            rs = linreg_slope(src_data, L)
            # Normalize to [-1,+1] via tanh for mapping comparability
            rs_norm = [math.tanh(v) if v is not None else None for v in rs]
            for sm_name in ("none", "ema3", "ema5", "ema7"):
                if sm_name == "none": sm = rs_norm
                else: sm = ema(rs_norm, int(sm_name[3:]))
                if len(sm) != N: continue
                r_fit = corr_coef(dir_obs, sm)
                if r_fit == r_fit:
                    a, b, rms = affine(dir_obs, sm)
                    last = sm[-1]
                    last_cc = -4.6 + 2.1*(1 - (last if last is not None else 0))
                    results.append((src_name, "slope", L, "tanh", sm_name, r_fit, rms, a, b, last_cc))

    results.sort(key=lambda t: -t[5])
    print(f"[18] N={N}  dir_target range=[{min(dir_obs):+.3f},{max(dir_obs):+.3f}]")
    print(f"[18] Top 30 candidates (morphology fit):")
    print(f"{'r':>7} {'src':>10} {'op':>7} {'L':>3} {'tr':>6} {'sm':>5}  {'slope':>6}  {'last_cc':>8}")
    for src, op, L, tr, sm, r_fit, rms, a, b, last in results[:30]:
        print(f"  r={r_fit:+.3f} {src:>10} {op:>7} L={L:<2} {tr:>6} {sm:>5}  a={a:+.3f}  last_cc={last:+.2f}")


if __name__ == "__main__":
    main()
