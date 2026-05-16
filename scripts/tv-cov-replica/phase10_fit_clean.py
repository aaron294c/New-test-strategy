"""
Phase 10: take the 474 deduped per-bar scraped values + SPY Yahoo closes,
align them tail-to-tail (scraped bar[-1] ↔ closes[-1]) and test candidate
CV / CC formulas via Pearson correlation AND best-fit (scale,offset).
"""
import csv, json, math, urllib.request
from pathlib import Path

OUT = Path("/tmp/tv-cov-out")


def yahoo(symbol="SPY", days=3*365):
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

def log_ret(c):
    r=[None]+[math.log(c[i]/c[i-1]) for i in range(1,len(c))]
    return r

def super_smoother(x,p):
    a=math.exp(-math.sqrt(2)*math.pi/p); b=2*a*math.cos(math.sqrt(2)*math.pi/p)
    c2,c3=b,-a*a; c1=1-c2-c3
    o=[0.0]*len(x); p1=p2=0.0
    for i,v in enumerate(x):
        v=0.0 if v is None else v
        o[i]=c1*v+c2*p1+c3*p2; p2,p1=p1,o[i]
    return o

def high_pass(x,p):
    a=(math.cos(math.sqrt(2)*math.pi/p)+math.sin(math.sqrt(2)*math.pi/p)-1)/math.cos(math.sqrt(2)*math.pi/p)
    o=[0.0]*len(x); p1=p2=0.0
    for i in range(len(x)):
        v=x[i] or 0.0 if x[i] is not None else 0.0
        v1=x[i-1] if i>=1 and x[i-1] is not None else 0.0
        v2=x[i-2] if i>=2 and x[i-2] is not None else 0.0
        o[i]=((1-a/2)**2)*(v-2*v1+v2)+2*(1-a)*p1-((1-a)**2)*p2
        p2,p1=p1,o[i]
    return o

def cv_series(sig, L, scale=2.0):
    m=sma(sig,L); s=stdv(sig,L)
    return [ss/abs(mm)*scale if (mm is not None and ss is not None and abs(mm)>1e-14) else None
            for mm,ss in zip(m,s)]

def pearson_x_bar(closes, L):
    """corr(close, bar_index) over trailing L bars."""
    o=[None]*len(closes)
    xs=list(range(L)); mx=sum(xs)/L
    dx=math.sqrt(sum((a-mx)**2 for a in xs))
    for i in range(L-1,len(closes)):
        y=closes[i-L+1:i+1]; my=sum(y)/L
        num=sum((a-mx)*(b-my) for a,b in zip(xs,y))
        dy=math.sqrt(sum((b-my)**2 for b in y))
        o[i]=num/(dx*dy) if dx*dy>1e-12 else None
    return o

def fisher(r):
    if r is None: return None
    r=max(-0.9999,min(0.9999,r))
    return 0.5*math.log((1+r)/(1-r))


def corr_coef(a,b):
    xs=[(x,y) for x,y in zip(a,b) if x is not None and y is not None]
    if len(xs)<5: return float("nan")
    mx=sum(x for x,_ in xs)/len(xs); my=sum(y for _,y in xs)/len(xs)
    num=sum((x-mx)*(y-my) for x,y in xs)
    dx=math.sqrt(sum((x-mx)**2 for x,_ in xs))
    dy=math.sqrt(sum((y-my)**2 for _,y in xs))
    return num/(dx*dy) if dx*dy>1e-12 else float("nan")

def best_affine(scraped, computed):
    """Return (a,b,resid_rms) for scraped ≈ a*computed + b."""
    xs=[(c,s) for c,s in zip(computed,scraped) if c is not None and s is not None]
    if len(xs)<5: return (None,None,None)
    mc=sum(c for c,_ in xs)/len(xs); ms=sum(s for _,s in xs)/len(xs)
    var_c=sum((c-mc)**2 for c,_ in xs)
    cov=sum((c-mc)*(s-ms) for c,s in xs)
    a = cov/var_c if var_c>1e-12 else 0
    b = ms - a*mc
    resid=math.sqrt(sum((s-(a*c+b))**2 for c,s in xs)/len(xs))
    return (a,b,resid)


def main():
    # load scraped bars (ascending x = ascending time)
    scraped=[]
    with (OUT/"phase9_bars.csv").open() as f:
        for r in csv.DictReader(f):
            try:
                scraped.append({"cv":float(r["cv"]), "cv_ma":float(r["cv_ma"]), "cc":float(r["cc"])})
            except ValueError: pass
    N=len(scraped)
    print(f"[10] scraped bars: {N}", flush=True)

    closes=[c for _,c in yahoo("SPY")]
    print(f"[10] SPY closes: {len(closes)}", flush=True)

    # Align tail-to-tail
    Ctail = closes[-N:]
    cv_obs = [b["cv"] for b in scraped]
    cc_obs = [b["cc"] for b in scraped]
    cvma_obs=[b["cv_ma"] for b in scraped]

    # Build signal variants (computed on FULL closes, then tail-sliced)
    rets = log_ret(closes)
    rets0 = [0.0 if r is None else r for r in rets]
    sigs = {
        "ret":     rets,
        "absret":  [abs(r) if r is not None else None for r in rets],
        "close":   closes,
        "SS2":     super_smoother(rets0,2),
        "SS5":     super_smoother(rets0,5),
        "SS2_HP500": high_pass(super_smoother(rets0,2), 500),
        "SS2_HP50":  high_pass(super_smoother(rets0,2), 50),
        "SS2_HP20":  high_pass(super_smoother(rets0,2), 20),
        "SS5_HP500": high_pass(super_smoother(rets0,5), 500),
        "SS5_HP50":  high_pass(super_smoother(rets0,5), 50),
        "HP500":     high_pass(rets0, 500),
        "HP50":      high_pass(rets0, 50),
    }

    cv_results=[]
    for sname, sig in sigs.items():
        for L in (3,5,7,10,14,20):
            ser = cv_series(sig, L, 2.0)
            tail = ser[-N:]
            r = corr_coef(cv_obs, tail)
            a,b,res = best_affine(cv_obs, tail)
            if r==r and a is not None:
                cv_results.append((r, sname, L, a, b, res))
    cv_results.sort(key=lambda t:-t[0])
    print("\n[10] Top 20 CV fits (Pearson r):")
    for r, s, L, a, b, res in cv_results[:20]:
        print(f"  r={r:+.3f}  {s:10}@L{L:<3}  affine cv_obs={a:+.3f}*x+{b:+.3f}  rms={res:.3f}", flush=True)

    print("\n[10] Top CC fits:")
    cc_results=[]
    for sname, sig in [("close",closes), ("SS5",super_smoother(rets0,5)),
                       ("SS2",super_smoother(rets0,2)), ("ret",rets0)]:
        for L in (3,5,7,10,14,20):
            rs = pearson_x_bar(sig, L)
            for tname, tf in [("r",lambda r:r),
                              ("fisher",fisher),
                              ("r2",lambda r: r*r if r is not None else None),
                              ("absr",lambda r: abs(r) if r is not None else None)]:
                ser = [tf(r) if r is not None else None for r in rs]
                # optional post-smoothing
                for esm in (1,5,10):
                    sm = ema(ser, esm) if esm>1 else ser
                    tail = sm[-N:]
                    r_corr = corr_coef(cc_obs, tail)
                    a,b,res = best_affine(cc_obs, tail)
                    if r_corr==r_corr and a is not None:
                        cc_results.append((r_corr, sname, L, tname, esm, a, b, res))
    cc_results.sort(key=lambda t:-t[0])
    for r, s, L, tn, esm, a, b, res in cc_results[:15]:
        print(f"  r={r:+.3f}  {s:6}/L{L:<3} {tn:7} ema={esm:<2}  cc_obs={a:+.3f}*x+{b:+.3f}  rms={res:.3f}", flush=True)


if __name__ == "__main__":
    main()
