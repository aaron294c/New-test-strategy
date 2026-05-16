"""
Phase 15: reverse-engineer the CC formula by grid-searching candidate
(input signal) × (lookback) × (correlation mode) × (smoothing) combinations
against the scraped NVDA per-bar CC values.

Known:
  - plot = ccOffset + ccScale * (1 - dirMetric) with offset=-4.6, scale=2.1
  - dirMetric is bounded roughly in [-1, 1] (observed plot in [-4.6, -0.4])
  - CV formula already validated: 100 * stdev(close,5) / |mean(close,5)| * 2
"""
import csv, json, math, urllib.request
from pathlib import Path

OUT = Path("/tmp/tv-cov-out")

def yahoo(symbol="NVDA", days=365):
    import time, datetime
    end=int(time.time()); start=end-days*86400
    url=(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?"
         f"period1={start}&period2={end}&interval=1d")
    req=urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    j=json.loads(urllib.request.urlopen(req, timeout=20).read())
    r=j["chart"]["result"][0]
    return [(datetime.date.fromtimestamp(t).isoformat(), c)
            for t,c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"])
            if c is not None]

def sma(x,n):
    o=[None]*len(x)
    for i in range(n-1,len(x)):
        w=x[i-n+1:i+1]
        if any(v is None for v in w): continue
        o[i]=sum(w)/n
    return o

def stdv(x,n):
    o=[None]*len(x)
    for i in range(n-1,len(x)):
        w=x[i-n+1:i+1]
        if any(v is None for v in w): continue
        m=sum(w)/n
        o[i]=math.sqrt(sum((v-m)**2 for v in w)/n)
    return o

def ema(x,n):
    a=2/(n+1); o=[None]*len(x); s=None
    for i,v in enumerate(x):
        if v is None: o[i]=s; continue
        s = v if s is None else a*v+(1-a)*s
        o[i]=s
    return o

def rma(x,n):
    """Wilder's smoothing."""
    a=1/n; o=[None]*len(x); s=None
    for i,v in enumerate(x):
        if v is None: o[i]=s; continue
        s = v if s is None else a*v+(1-a)*s
        o[i]=s
    return o

def pearson_xy(a, b, L):
    """rolling Pearson r of series a vs series b over last L points."""
    o=[None]*len(a)
    for i in range(L-1, len(a)):
        xs=a[i-L+1:i+1]; ys=b[i-L+1:i+1]
        if any(v is None for v in xs) or any(v is None for v in ys): continue
        mx=sum(xs)/L; my=sum(ys)/L
        num=sum((x-mx)*(y-my) for x,y in zip(xs,ys))
        dx=math.sqrt(sum((x-mx)**2 for x in xs))
        dy=math.sqrt(sum((y-my)**2 for y in ys))
        o[i] = num/(dx*dy) if dx*dy>1e-12 else None
    return o

def pearson_t(series, L):
    """rolling Pearson r of series vs bar_index over last L points."""
    xs=list(range(L)); mx=sum(xs)/L
    dx=math.sqrt(sum((a-mx)**2 for a in xs))
    o=[None]*len(series)
    for i in range(L-1, len(series)):
        y=series[i-L+1:i+1]
        if any(v is None for v in y): continue
        my=sum(y)/L
        num=sum((a-mx)*(b-my) for a,b in zip(xs,y))
        dy=math.sqrt(sum((b-my)**2 for b in y))
        o[i]=num/(dx*dy) if dx*dy>1e-12 else None
    return o

def corr_coef(a,b):
    xs=[(x,y) for x,y in zip(a,b) if x is not None and y is not None]
    if len(xs)<5: return float("nan")
    mx=sum(x for x,_ in xs)/len(xs); my=sum(y for _,y in xs)/len(xs)
    num=sum((x-mx)*(y-my) for x,y in xs)
    dx=math.sqrt(sum((x-mx)**2 for x,_ in xs))
    dy=math.sqrt(sum((y-my)**2 for _,y in xs))
    return num/(dx*dy) if dx*dy>1e-12 else float("nan")

def affine(obs, com):
    xs=[(c,s) for c,s in zip(com,obs) if c is not None and s is not None]
    if len(xs)<5: return None,None,None
    mc=sum(c for c,_ in xs)/len(xs); ms=sum(s for _,s in xs)/len(xs)
    var=sum((c-mc)**2 for c,_ in xs); cov=sum((c-mc)*(s-ms) for c,s in xs)
    a=cov/var if var>1e-12 else 0; b=ms-a*mc
    rms=math.sqrt(sum((s-(a*c+b))**2 for c,s in xs)/len(xs))
    return a,b,rms


def load_scraped():
    bars=[]
    with (OUT/"phase14_nvda.csv").open() as f:
        for r in csv.DictReader(f):
            try:
                bars.append({
                    "cv":float(r["cv"]),
                    "cv_ma":float(r["cv_ma"]),
                    "cc":float(r["cc"]),
                })
            except: pass
    return bars


def derive_dirMetric_target(cc_obs, offset=-4.6, scale=2.1):
    """Invert plot = offset + scale*(1 - dirMetric) → dirMetric = 1 - (plot-offset)/scale."""
    return [1 - (p - offset)/scale for p in cc_obs]


def main():
    bars = load_scraped()
    N = len(bars)
    cv_obs = [b["cv"] for b in bars]
    cc_obs = [b["cc"] for b in bars]
    dir_obs = derive_dirMetric_target(cc_obs)
    print(f"[15] scraped bars: N={N}")
    print(f"[15] observed CC range: [{min(cc_obs):.3f}, {max(cc_obs):.3f}]")
    print(f"[15] inverted dirMetric range: [{min(dir_obs):.3f}, {max(dir_obs):.3f}]")

    closes=[c for _,c in yahoo("NVDA", 365)]
    print(f"[15] NVDA closes fetched: {len(closes)}")

    # Align: assume scraped bars are the LAST N trading days
    Ctail = closes[-N:]
    # verify CV recomputes correctly with our known formula
    cv_pred_full = []
    m = sma(closes, 5); s = stdv(closes, 5)
    for mm, ss in zip(m, s):
        if mm is None or ss is None: cv_pred_full.append(None)
        else: cv_pred_full.append(100.0 * ss / abs(mm) * 2.0)
    cv_pred = cv_pred_full[-N:]
    cv_r = corr_coef(cv_obs, cv_pred)
    a,b,rms = affine(cv_obs, cv_pred)
    print(f"[15] CV sanity: r={cv_r:+.4f}  fit={a:+.3f}*x{b:+.3f}  rms={rms:.3f}")

    # Build a library of candidate input signals
    def log_ret(c):
        return [None]+[math.log(c[i]/c[i-1]) for i in range(1,len(c))]
    def abs_diff(c):
        return [None]+[c[i]-c[i-1] for i in range(1,len(c))]
    def pct_ret(c):
        return [None]+[(c[i]-c[i-1])/c[i-1] for i in range(1,len(c))]

    rets_log = log_ret(closes)
    rets_abs = abs_diff(closes)
    rets_pct = pct_ret(closes)
    cv_full  = cv_pred_full

    # also compute CV at different lengths & CV on log-returns
    def cv_series_len(src, L, scale=2.0):
        m=sma(src,L); s=stdv(src,L)
        return [100*ss/abs(mm)*scale if (mm and ss) else None for mm,ss in zip(m,s)]
    cv3  = cv_series_len(closes,3)
    cv7  = cv_series_len(closes,7)
    cv10 = cv_series_len(closes,10)
    cv20 = cv_series_len(closes,20)
    cv_raw1 = cv_series_len(closes,5,1.0)          # CV without *2 scale
    cv_ma5  = ema(cv_full, 5)
    sma20   = sma(closes, 20)
    sma50   = sma(closes, 50)
    close_minus_sma20 = [None if (c is None or s is None) else c-s for c,s in zip(closes,sma20)]

    inputs = {
        "close":     closes,
        "log_ret":   rets_log,
        "abs_ret":   rets_abs,
        "pct_ret":   rets_pct,
        "cv":        cv_full,
        "cv_len3":   cv3,
        "cv_len7":   cv7,
        "cv_len10":  cv10,
        "cv_len20":  cv20,
        "cv_raw":    cv_raw1,
        "cv_ma":     cv_ma5,
        "close-sma20": close_minus_sma20,
    }

    # Modes: "raw" = r; "adj_k1" = sign(r)*sqrt(max(0, 1-(1-r²)(n-1)/(n-2)))
    # "fisher_tanh" = tanh(0.5 ln((1+r)/(1-r)))  (identity with r, but we also
    #                 test tanh(scaled)). We'll also test |r|*sign(r) power laws.
    def adj_k1(r, n):
        if r is None or n<=2: return r
        return (1 if r>=0 else -1)*math.sqrt(max(0, 1 - (1-r*r)*(n-1)/(n-2)))

    def atanh(r):
        if r is None: return None
        r = max(-0.9999, min(0.9999, r))
        return 0.5*math.log((1+r)/(1-r))

    # Search — correlating input vs bar_index
    print("\n[15] ==== corr(input, bar_index) search ====")
    results=[]
    for sname, sig in inputs.items():
        for L in list(range(3,31)):
            rs = pearson_t(sig, L)
            for mode in ("raw", "adj"):
                if mode=="raw":
                    ser = rs
                else:
                    ser = [adj_k1(v, L) if v is not None else None for v in rs]
                for smooth in ("none","ema3","ema5","ema7","ema10","ema14",
                               "sma3","sma5","sma7","sma10","rma3","rma5"):
                    if smooth=="none": sm=ser
                    elif smooth.startswith("ema"): sm=ema(ser, int(smooth[3:]))
                    elif smooth.startswith("sma"): sm=sma([v if v is not None else 0 for v in ser], int(smooth[3:]))
                    elif smooth.startswith("rma"): sm=rma(ser, int(smooth[3:]))
                    tail=sm[-N:]
                    if len(tail)!=N: continue
                    r = corr_coef(dir_obs, tail)
                    if r==r:
                        a,b,rms=affine(dir_obs, tail)
                        results.append((r, sname, L, mode, smooth, a, b, rms))

    # Also search corr(input_a, input_b) cross-correlations
    print("[15] ==== corr(A, B) cross search ====")
    cross = [
        ("close","cv",closes,cv_full),
        ("log_ret","cv",rets_log,cv_full),
        ("close","log_ret",closes,rets_log),
        ("cv","cv_ma",cv_full,ema(cv_full,5)),
        ("cv","close",cv_full,closes),
        ("cv","sma20",cv_full,sma20),
        ("abs_ret","cv",rets_abs,cv_full),
        ("pct_ret","cv",rets_pct,cv_full),
    ]
    for an, bn, av, bv in cross:
        for L in list(range(3,31)):
            rs = pearson_xy(av, bv, L)
            for mode in ("raw","adj"):
                if mode=="raw": ser=rs
                else: ser=[adj_k1(v,L) if v is not None else None for v in rs]
                for smooth in ("none","ema3","ema5","ema7","ema10"):
                    if smooth=="none": sm=ser
                    else: sm=ema(ser,int(smooth[3:]))
                    tail=sm[-N:]
                    if len(tail)!=N: continue
                    r=corr_coef(dir_obs, tail)
                    if r==r:
                        a,b,rms=affine(dir_obs, tail)
                        results.append((r, f"{an}~{bn}", L, mode, smooth, a, b, rms))

    results.sort(key=lambda t:-t[0])
    print("\n[15] Top 30 CC formula candidates (higher r = better morphology match):")
    for r, sname, L, mode, smooth, a, b, rms in results[:30]:
        print(f"  r={r:+.4f}  {sname:14} L={L:<2} {mode:3} {smooth:6}  "
              f"dir={a:+.3f}*x{b:+.3f}  rms={rms:.3f}")

    # Also check best fit on plot VALUE (not just shape): use observed cc_obs directly
    print("\n[15] Best candidates re-scored directly against scraped CC plot values:")
    rescored=[]
    for r, sname, L, mode, smooth, a, b, rms in results[:100]:
        # reconstruct dirMetric series and map to plot
        # (re-run a bit quickly)
        if "~" in sname:
            an,bn = sname.split("~")
            libA = {"close":closes,"cv":cv_full,"log_ret":rets_log,"abs_ret":rets_abs,"pct_ret":rets_pct}
            libB = {"cv":cv_full,"log_ret":rets_log,"cv_ma":ema(cv_full,5),"close":closes,"sma20":sma20}
            av = libA[an]; bv = libB[bn]
            rs = pearson_xy(av, bv, L)
        else:
            rs = pearson_t(inputs[sname], L)
        if mode=="adj":
            ser=[adj_k1(v,L) if v is not None else None for v in rs]
        else:
            ser=rs
        if smooth=="none": sm=ser
        elif smooth.startswith("ema"): sm=ema(ser,int(smooth[3:]))
        elif smooth.startswith("sma"): sm=sma([v if v is not None else 0 for v in ser], int(smooth[3:]))
        elif smooth.startswith("rma"): sm=rma(ser,int(smooth[3:]))
        pred_dir = sm[-N:]
        pred_cc  = [None if v is None else -4.6 + 2.1*(1-v) for v in pred_dir]
        rp = corr_coef(cc_obs, pred_cc)
        ap,bp,rmsp = affine(cc_obs, pred_cc)
        if rp==rp and ap is not None:
            last_pred = pred_cc[-1]
            rescored.append((rp, rmsp, sname, L, mode, smooth, last_pred))
    rescored.sort(key=lambda t:(-t[0], t[1]))
    print("  (goal: CC at last bar ≈ -2.40)")
    for rp, rmsp, sname, L, mode, smooth, last_pred in rescored[:20]:
        last_str = f"{last_pred:+.3f}" if last_pred is not None else "None"
        print(f"  r={rp:+.4f}  rms={rmsp:.3f}  {sname:14} L={L:<2} {mode:3} {smooth:6}  last_cc={last_str}")


if __name__ == "__main__":
    main()
