"""
Phase 29: with aligned (close, o_cv, o_cc) from phase27, test user's hypothesis:
CC = correlation between PRICE and CV (and variations). If both rise together = green,
diverge = red. Also try corr(price, logret), corr(price, cv-cvma), etc.
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


def main():
    bars = []
    with (OUT/"phase27_with_close.csv").open() as fh:
        for r in csv.DictReader(fh):
            b = {
                "close": f(r["close"]),
                "o_cv":  f(r["o_cv"]),
                "o_cvma":f(r["o_cvma"]),
                "o_cc":  f(r["o_cc"]),
            }
            if all(v is not None for v in b.values()): bars.append(b)
    N = len(bars)
    close = [b["close"] for b in bars]
    o_cv  = [b["o_cv"] for b in bars]
    o_cvma= [b["o_cvma"] for b in bars]
    o_cc  = [b["o_cc"] for b in bars]
    dir_obs = [1 - (p - (-4.6))/2.1 for p in o_cc]  # dir_obs in [-1,+1]
    print(f"[29] N={N} close=[{min(close):.1f},{max(close):.1f}] o_cc=[{min(o_cc):+.2f},{max(o_cc):+.2f}]")

    # Build derived series
    logret = [None]
    for i in range(1, N):
        logret.append(math.log(close[i]/close[i-1]) if close[i-1]>0 and close[i]>0 else None)
    pctret = [None]
    for i in range(1, N):
        pctret.append((close[i]-close[i-1])/close[i-1] if close[i-1]>0 else None)
    diff = [c-m for c, m in zip(o_cv, o_cvma)]
    ratio = [(c/m if m else 0) - 1 for c, m in zip(o_cv, o_cvma)]
    logcv = [math.log(v) if v and v>0 else None for v in o_cv]
    logp = [math.log(p) if p>0 else None for p in close]

    # Candidate input pairs (x, y) for Pearson correlation
    pairs = [
        ("close", close), ("logclose", logp), ("logret", logret), ("pctret", pctret),
        ("cv", o_cv), ("cvma", o_cvma), ("cv-cvma", diff), ("cv/cvma-1", ratio),
        ("logcv", logcv),
    ]

    results = []
    # Same-series (vs time)
    for name, s in pairs:
        for L in range(3, 25):
            rs = pearson_t(s, L)
            for sm_name in ("none", "ema3", "ema5"):
                sm = rs if sm_name == "none" else ema(rs, int(sm_name[3:]))
                r_fit = corr_coef(dir_obs, sm)
                if r_fit != r_fit: continue
                vals = [v for v in sm if v is not None]
                if not vals: continue
                rng = max(vals) - min(vals)
                results.append((f"corr({name},t)", L, sm_name, r_fit, rng, sm[-1]))

    # Cross-pair correlations
    cross = [
        ("close","cv"), ("close","logcv"), ("close","cv-cvma"), ("close","cv/cvma-1"),
        ("logclose","cv"), ("logclose","cv-cvma"),
        ("logret","cv"), ("logret","cvma"), ("logret","cv-cvma"), ("logret","cv/cvma-1"),
        ("pctret","cv"), ("pctret","cv-cvma"),
        ("close","logret"), ("close","pctret"),
    ]
    series_map = dict(pairs)
    for an, bn in cross:
        a = series_map[an]; b = series_map[bn]
        for L in range(3, 25):
            rs = pearson_xy(a, b, L)
            for sm_name in ("none", "ema3", "ema5"):
                sm = rs if sm_name == "none" else ema(rs, int(sm_name[3:]))
                r_fit = corr_coef(dir_obs, sm)
                if r_fit != r_fit: continue
                vals = [v for v in sm if v is not None]
                if not vals: continue
                rng = max(vals) - min(vals)
                results.append((f"corr({an},{bn})", L, sm_name, r_fit, rng, sm[-1]))

    results.sort(key=lambda t: -abs(t[3]))
    print(f"\n[29] Top 30 by |r_fit|:")
    for name, L, sm, r_fit, rng, last in results[:30]:
        print(f"  r_fit={r_fit:+.3f} rng={rng:.2f} last={last:+.3f}  {name} L={L:<2} {sm}")

    # Filter to results with good fit AND wide prediction range (target dir range ~1.95)
    good = [r for r in results if abs(r[3]) >= 0.6]
    good.sort(key=lambda t: -t[4])
    print(f"\n[29] |r_fit|>=0.6, sorted by prediction range (target ~1.95):")
    for name, L, sm, r_fit, rng, last in good[:20]:
        print(f"  r_fit={r_fit:+.3f} rng={rng:.2f} last={last:+.3f}  {name} L={L:<2} {sm}")


if __name__ == "__main__":
    main()
