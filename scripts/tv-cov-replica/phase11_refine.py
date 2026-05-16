"""
Phase 11: refine the close-based CV recipe. Search bar-offset, normalization
(100, percent-scale, stdev type), and verify CV_MA = EMA5(CV). For CC, also
search bar-offset + L.
"""
import csv, json, math, urllib.request
from pathlib import Path

OUT = Path("/tmp/tv-cov-out")

def yahoo(symbol="SPY", days=3*365):
    import time, datetime
    end=int(time.time()); start=end-days*86400
    url=f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1={start}&period2={end}&interval=1d"
    req=urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    j=json.loads(urllib.request.urlopen(req, timeout=20).read())
    r=j["chart"]["result"][0]
    return [(datetime.date.fromtimestamp(t).isoformat(), c)
            for t,c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]) if c is not None]

def sma(x,n):
    o=[None]*len(x)
    for i in range(n-1,len(x)):
        o[i]=sum(x[i-n+1:i+1])/n
    return o

def stdv_pop(x,n):
    o=[None]*len(x)
    for i in range(n-1,len(x)):
        w=x[i-n+1:i+1]; m=sum(w)/n
        o[i]=math.sqrt(sum((v-m)**2 for v in w)/n)
    return o

def stdv_sam(x,n):
    o=[None]*len(x)
    for i in range(n-1,len(x)):
        w=x[i-n+1:i+1]; m=sum(w)/n
        o[i]=math.sqrt(sum((v-m)**2 for v in w)/(n-1))
    return o

def ema(x,n):
    a=2/(n+1); o=[None]*len(x); s=None
    for i,v in enumerate(x):
        if v is None: o[i]=s; continue
        s = v if s is None else a*v+(1-a)*s
        o[i]=s
    return o

def corr(a,b):
    xs=[(x,y) for x,y in zip(a,b) if x is not None and y is not None]
    if len(xs)<5: return float("nan")
    mx=sum(x for x,_ in xs)/len(xs); my=sum(y for _,y in xs)/len(xs)
    num=sum((x-mx)*(y-my) for x,y in xs)
    dx=math.sqrt(sum((x-mx)**2 for x,_ in xs))
    dy=math.sqrt(sum((y-my)**2 for _,y in xs))
    return num/(dx*dy) if dx*dy>1e-12 else float("nan")

def best_affine(obs, com):
    xs=[(c,s) for c,s in zip(com,obs) if c is not None and s is not None]
    if len(xs)<5: return None,None,None
    mc=sum(c for c,_ in xs)/len(xs); ms=sum(s for _,s in xs)/len(xs)
    var=sum((c-mc)**2 for c,_ in xs)
    cov=sum((c-mc)*(s-ms) for c,s in xs)
    a=cov/var if var>1e-12 else 0
    b=ms-a*mc
    rms=math.sqrt(sum((s-(a*c+b))**2 for c,s in xs)/len(xs))
    return a,b,rms

def pearson_x_bar(closes,L):
    o=[None]*len(closes); xs=list(range(L)); mx=sum(xs)/L
    dx=math.sqrt(sum((a-mx)**2 for a in xs))
    for i in range(L-1,len(closes)):
        y=closes[i-L+1:i+1]; my=sum(y)/L
        num=sum((a-mx)*(b-my) for a,b in zip(xs,y))
        dy=math.sqrt(sum((b-my)**2 for b in y))
        o[i]=num/(dx*dy) if dx*dy>1e-12 else None
    return o


def main():
    scraped=[]
    with (OUT/"phase9_bars.csv").open() as f:
        for r in csv.DictReader(f):
            try: scraped.append({"cv":float(r["cv"]),"cv_ma":float(r["cv_ma"]),"cc":float(r["cc"])})
            except: pass
    N=len(scraped)
    cv_obs   = [b["cv"]    for b in scraped]
    cvma_obs = [b["cv_ma"] for b in scraped]
    cc_obs   = [b["cc"]    for b in scraped]

    closes=[c for _,c in yahoo("SPY")]
    print(f"[11] scraped={N}, closes={len(closes)}", flush=True)

    # CV search: length × stdev type × bar offset
    print("\n[11] CV fit grid (close-based):")
    best=[]
    for stype, stfn in [("pop",stdv_pop),("sam",stdv_sam)]:
        for L in (3,4,5,6,7,10):
            m = sma(closes, L); s = stfn(closes, L)
            cv = [ss/abs(mm) if (mm and ss) else None for mm,ss in zip(m,s)]
            for off in range(-3,4):
                if off>=0: tail=cv[-(N+off) if off<=0 else len(cv)-off:][:N]
                else:      tail=cv[-(N-off):][:N]
                if len(tail)!=N: continue
                r=corr(cv_obs,tail)
                a,b,rms=best_affine(cv_obs,tail)
                if r==r and a is not None:
                    best.append((r,stype,L,off,a,b,rms))
    best.sort(key=lambda t:-t[0])
    for r,st,L,off,a,b,rms in best[:12]:
        print(f"  r={r:+.4f} stdev={st} L={L} off={off:+d}  cv={a:+.2f}*raw{b:+.3f}  rms={rms:.3f}", flush=True)

    # Verify CV_MA = EMA5(CV) using scraped
    print("\n[11] CV_MA structural test: corr(scraped_cv_ma, EMA5(scraped_cv)):")
    em = ema(cv_obs, 5)
    print(f"  corr = {corr(cvma_obs, em):+.4f}", flush=True)
    em3 = ema(cv_obs, 3); em7 = ema(cv_obs, 7); em10=ema(cv_obs,10)
    print(f"  EMA3 = {corr(cvma_obs, em3):+.4f}  EMA7 = {corr(cvma_obs, em7):+.4f}  EMA10 = {corr(cvma_obs, em10):+.4f}", flush=True)
    sm5 = sma(cv_obs, 5)
    print(f"  SMA5 = {corr(cvma_obs, sm5):+.4f}", flush=True)

    # CC search
    print("\n[11] CC fit grid (close-based):")
    cc_best=[]
    for L in (3,4,5,6,7,8,10,12,14):
        r_ser = pearson_x_bar(closes, L)
        for tname, tf in [("r",lambda r:r),
                          ("fisher", lambda r: 0.5*math.log((1+max(-0.9999,min(0.9999,r)))/(1-max(-0.9999,min(0.9999,r)))) if r is not None else None),
                          ("r2sign",lambda r: r*abs(r) if r is not None else None)]:
            ser = [tf(v) if v is not None else None for v in r_ser]
            for esm in (1,3,5,7,10):
                sm = ema(ser, esm) if esm>1 else ser
                for off in range(-3,4):
                    if off>=0: tail=sm[-(N+off) if off<=0 else len(sm)-off:][:N]
                    else:      tail=sm[-(N-off):][:N]
                    if len(tail)!=N: continue
                    rc=corr(cc_obs, tail)
                    a,b,rms=best_affine(cc_obs, tail)
                    if rc==rc and a is not None:
                        cc_best.append((rc,L,tname,esm,off,a,b,rms))
    cc_best.sort(key=lambda t:-t[0])
    for rc,L,tn,esm,off,a,b,rms in cc_best[:15]:
        print(f"  r={rc:+.4f} L={L:<2} tf={tn:7} ema={esm:<2} off={off:+d}  cc={a:+.3f}*x{b:+.3f}  rms={rms:.3f}", flush=True)


if __name__ == "__main__":
    main()
