"""
Phase 8: load the 73-bar scraped sweep (phase7_sweep.csv) + SPY Yahoo daily,
align bar-index to x-position affinely, and for each candidate formula compute
Pearson correlation with the scraped series. Highest-r candidate wins.

Key insight: we don't need exact pixel→bar mapping. If the chart shows N most
recent bars evenly, then x=120 → bar[N-1], x=1440 → bar[-1], with linear
interpolation. We search N to find best fit.
"""
import csv, json, math, urllib.request
from pathlib import Path

OUT = Path("/tmp/tv-cov-out")


def yahoo_v8():
    import time
    end = int(time.time()); start = end - 3*365*86400
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/SPY?"
           f"period1={start}&period2={end}&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    j = json.loads(urllib.request.urlopen(req, timeout=20).read())
    r = j["chart"]["result"][0]
    import datetime
    return [(datetime.date.fromtimestamp(t).isoformat(), c)
            for t, c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"])
            if c is not None]


def sma(x, n):
    out = [None]*len(x)
    for i in range(n-1, len(x)):
        w = x[i-n+1:i+1]
        if any(v is None for v in w): continue
        out[i] = sum(w)/n
    return out

def stdev(x, n):
    out = [None]*len(x)
    for i in range(n-1, len(x)):
        w = x[i-n+1:i+1]
        if any(v is None for v in w): continue
        m = sum(w)/n
        out[i] = math.sqrt(sum((v-m)**2 for v in w)/n)
    return out

def ema(x, n):
    a = 2/(n+1); out=[None]*len(x); s=None
    for i,v in enumerate(x):
        if v is None: out[i]=s; continue
        s = v if s is None else a*v + (1-a)*s
        out[i] = s
    return out

def log_ret(c):
    r=[None]
    for i in range(1,len(c)): r.append(math.log(c[i]/c[i-1]))
    return r

def super_smoother(x, period):
    a = math.exp(-math.sqrt(2)*math.pi/period)
    b = 2*a*math.cos(math.sqrt(2)*math.pi/period)
    c2,c3 = b,-a*a; c1 = 1-c2-c3
    out=[0.0]*len(x); p1=p2=0.0
    for i,v in enumerate(x):
        v = 0.0 if v is None else v
        out[i] = c1*v + c2*p1 + c3*p2
        p2,p1 = p1,out[i]
    return out

def high_pass(x, period):
    a = (math.cos(math.sqrt(2)*math.pi/period)+math.sin(math.sqrt(2)*math.pi/period)-1)/math.cos(math.sqrt(2)*math.pi/period)
    out=[0.0]*len(x); p1=p2=0.0
    for i in range(len(x)):
        v  = x[i]  if x[i]  is not None else 0.0
        v1 = x[i-1] if i>=1 and x[i-1] is not None else 0.0
        v2 = x[i-2] if i>=2 and x[i-2] is not None else 0.0
        out[i] = ((1-a/2)**2)*(v-2*v1+v2) + 2*(1-a)*p1 - ((1-a)**2)*p2
        p2,p1 = p1,out[i]
    return out


def cv_of(series, L, scale=2.0):
    m = sma(series, L); s = stdev(series, L)
    return [ss/abs(mm)*scale if (mm is not None and ss is not None and abs(mm)>1e-14) else None
            for mm,ss in zip(m,s)]


def corr_series(a, b):
    """Pearson r between two equal-length series, skipping Nones."""
    xs = [(x,y) for x,y in zip(a,b) if x is not None and y is not None
          and not (isinstance(x,float) and math.isnan(x))
          and not (isinstance(y,float) and math.isnan(y))]
    if len(xs) < 5: return float("nan")
    mx = sum(x for x,_ in xs)/len(xs); my = sum(y for _,y in xs)/len(xs)
    num = sum((x-mx)*(y-my) for x,y in xs)
    dx = math.sqrt(sum((x-mx)**2 for x,_ in xs))
    dy = math.sqrt(sum((y-my)**2 for _,y in xs))
    return num/(dx*dy) if dx*dy>1e-12 else float("nan")


def pearson_close(closes, lookback):
    out=[None]*len(closes)
    for i in range(lookback-1, len(closes)):
        y = closes[i-lookback+1:i+1]
        xs = list(range(lookback))
        mx=sum(xs)/lookback; my=sum(y)/lookback
        num=sum((a-mx)*(b-my) for a,b in zip(xs,y))
        dx=math.sqrt(sum((a-mx)**2 for a in xs))
        dy=math.sqrt(sum((b-my)**2 for b in y))
        out[i] = num/(dx*dy) if dx*dy>1e-12 else None
    return out


def fisher(r):
    if r is None: return None
    r=max(-0.9999,min(0.9999,r))
    return 0.5*math.log((1+r)/(1-r))


def load_sweep():
    rows=[]
    with (OUT/"phase7_sweep.csv").open() as f:
        for r in csv.DictReader(f):
            if not r["cv"]: continue
            rows.append({"x": int(r["x"]),
                         "cv": float(r["cv"]),
                         "cv_ma": float(r["cv_ma"]),
                         "cc": float(r["cc"])})
    rows.sort(key=lambda r: r["x"])  # ascending x
    return rows


def main():
    sweep = load_sweep()
    N = len(sweep)
    scraped_cv    = [r["cv"] for r in sweep]
    scraped_cv_ma = [r["cv_ma"] for r in sweep]
    scraped_cc    = [r["cc"] for r in sweep]
    print(f"[8] sweep rows: {N}", flush=True)

    closes = [c for _,c in yahoo_v8()]
    print(f"[8] SPY closes: {len(closes)}  tail={closes[-5:]}", flush=True)
    rets = log_ret(closes)

    # Pre-build filtered series variants
    rets0 = [0.0 if r is None else r for r in rets]
    close0 = closes
    variants_input = {
        "raw_ret":       rets,
        "SS2":           super_smoother(rets0, 2),
        "SS2_HP500":     high_pass(super_smoother(rets0,2), 500),
        "SS2_HP50":      high_pass(super_smoother(rets0,2), 50),
        "SS5":           super_smoother(rets0, 5),
        "SS5_HP500":     high_pass(super_smoother(rets0,5), 500),
        "abs_ret":       [abs(r) if r is not None else None for r in rets],
        "close":         close0,
        "ret_pct":       [100*r if r is not None else None for r in rets],
    }

    # Build CV candidates with different lengths
    cand_cv = {}
    for iname, iser in variants_input.items():
        for L in (3,5,7,10,14,20):
            cand_cv[f"{iname}@L{L}"] = cv_of(iser, L, 2.0)

    # Best candidates for CV sweep — match to last N bars of closes
    def tail(series, n): return series[-n:]
    results = []
    # Align: assume scraped covers the last K bars where K in some range
    for K in (N, N+1, N+2, N-1, N*2, int(N*1.5)):
        if K < 10 or K > len(closes): continue
        for name, ser in cand_cv.items():
            tail_v = tail(ser, K)
            # resample to N points from K via linear interp on x positions
            if None in tail_v: continue
            # tail_v has K values; scraped_cv has N values at x=sweep[i]['x']
            # Map each scraped index i to bar position: i→K-1-i? No, ascending x = ascending bar time
            idx = [int(round((K-1)*i/(N-1))) for i in range(N)]
            sampled = [tail_v[j] for j in idx]
            r = corr_series(sampled, scraped_cv)
            if not (r!=r):
                results.append((r, name, K, sampled[-1]))
    results.sort(reverse=True)
    print("\n[8] Top 15 CV matches (Pearson r of sweep vs candidate):")
    for r,name,K,last in results[:15]:
        print(f"  r={r:+.3f}  K={K}  last={last:.3f}  ← {name}", flush=True)

    # CC candidates
    print("\n[8] CC candidate search:")
    for Lb in (3,5,7,10,14):
        for src_name, src_ in [("close", closes),
                                 ("ret",   rets0),
                                 ("SS5",   super_smoother(rets0,5))]:
            rs = pearson_close(src_, Lb)
            for transform_name, tf in [("raw_r", lambda r:r),
                                       ("fisher", fisher),
                                       ("absr_neg", lambda r: -abs(r) if r is not None else None)]:
                ser = [tf(r)*2.1 - 4.6 if r is not None else None for r in rs]
                # Align tail of length N via same index mapping
                for K in (N, int(N*1.5), N*2):
                    if K > len(ser): continue
                    idx=[int(round((K-1)*i/(N-1))) for i in range(N)]
                    sampled=[ser[-K+j] for j in idx]
                    if any(s is None for s in sampled): continue
                    r=corr_series(sampled, scraped_cc)
                    if r==r and r>0.3:
                        results_cc = (r, f"{src_name}/L{Lb}/{transform_name}/K={K}", sampled[-1])
                        print(f"  r={r:+.3f}  last={sampled[-1]:+.3f}  ← {results_cc[1]}", flush=True)


if __name__ == "__main__":
    main()
