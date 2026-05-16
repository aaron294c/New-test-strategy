"""
Phase 12: deep search for the CC formula. Test Pearson correlation over many
input variants: filtered closes, ROC, momentum, CV itself vs bar_index, etc.
"""
import csv, json, math, urllib.request
from pathlib import Path

OUT = Path("/tmp/tv-cov-out")

def yahoo(symbol="SPY", days=3*365):
    import time, datetime
    end=int(time.time()); start=end-days*86400
    url=f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1={start}&period2={end}&interval=1d"
    j=json.loads(urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=20).read())
    r=j["chart"]["result"][0]
    return [(datetime.date.fromtimestamp(t).isoformat(), c)
            for t,c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]) if c is not None]

def sma(x,n):
    o=[None]*len(x)
    for i in range(n-1,len(x)): o[i]=sum(x[i-n+1:i+1])/n
    return o
def stdv(x,n):
    o=[None]*len(x)
    for i in range(n-1,len(x)):
        w=x[i-n+1:i+1]; m=sum(w)/n
        o[i]=math.sqrt(sum((v-m)**2 for v in w)/n)
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
def affine(obs, com):
    xs=[(c,s) for c,s in zip(com,obs) if c is not None and s is not None]
    if len(xs)<5: return None,None,None
    mc=sum(c for c,_ in xs)/len(xs); ms=sum(s for _,s in xs)/len(xs)
    var=sum((c-mc)**2 for c,_ in xs); cov=sum((c-mc)*(s-ms) for c,s in xs)
    a=cov/var if var>1e-12 else 0; b=ms-a*mc
    rms=math.sqrt(sum((s-(a*c+b))**2 for c,s in xs)/len(xs))
    return a,b,rms

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
        v=x[i] if x[i] is not None else 0.0
        v1=x[i-1] if i>=1 and x[i-1] is not None else 0.0
        v2=x[i-2] if i>=2 and x[i-2] is not None else 0.0
        o[i]=((1-a/2)**2)*(v-2*v1+v2)+2*(1-a)*p1-((1-a)**2)*p2
        p2,p1=p1,o[i]
    return o

def pearson_x(series,L):
    o=[None]*len(series); xs=list(range(L)); mx=sum(xs)/L
    dx=math.sqrt(sum((a-mx)**2 for a in xs))
    for i in range(L-1,len(series)):
        y=series[i-L+1:i+1]
        if any(v is None for v in y): continue
        my=sum(y)/L
        num=sum((a-mx)*(b-my) for a,b in zip(xs,y))
        dy=math.sqrt(sum((b-my)**2 for b in y))
        o[i]=num/(dx*dy) if dx*dy>1e-12 else None
    return o

def pearson_ab(a_ser, b_ser, L):
    o=[None]*len(a_ser)
    for i in range(L-1, len(a_ser)):
        a=a_ser[i-L+1:i+1]; b=b_ser[i-L+1:i+1]
        if any(v is None for v in a) or any(v is None for v in b): continue
        ma=sum(a)/L; mb=sum(b)/L
        num=sum((av-ma)*(bv-mb) for av,bv in zip(a,b))
        da=math.sqrt(sum((av-ma)**2 for av in a))
        db=math.sqrt(sum((bv-mb)**2 for bv in b))
        o[i]=num/(da*db) if da*db>1e-12 else None
    return o


def main():
    scraped=[]
    with (OUT/"phase9_bars.csv").open() as f:
        for r in csv.DictReader(f):
            try: scraped.append({"cv":float(r["cv"]),"cv_ma":float(r["cv_ma"]),"cc":float(r["cc"])})
            except: pass
    N=len(scraped); cc_obs=[b["cc"] for b in scraped]
    closes=[c for _,c in yahoo("SPY")]
    print(f"[12] N={N} closes={len(closes)}", flush=True)

    rets=[None]+[math.log(closes[i]/closes[i-1]) for i in range(1,len(closes))]
    rets0=[0.0 if r is None else r for r in rets]

    # Build input universe: different "direction signals"
    inputs = {
        "close":       closes,
        "SS2_close":   super_smoother(closes,2),
        "SS5_close":   super_smoother(closes,5),
        "SS10_close":  super_smoother(closes,10),
        "HP500_close": high_pass(closes, 500),
        "HP50_close":  high_pass(closes, 50),
        "BP_close":    high_pass(super_smoother(closes,2), 500),
        "BP_close_50": high_pass(super_smoother(closes,2), 50),
        "SMA5":        sma(closes,5),
        "SMA10":       sma(closes,10),
        "SMA20":       sma(closes,20),
        "ret":         rets,
        "SS5_ret":     super_smoother(rets0,5),
    }

    results=[]
    for sname, sig in inputs.items():
        for L in (3,4,5,6,7,8,10,12,14,20):
            r_ser = pearson_x(sig, L)
            for tname, tf in [("r", lambda r:r),
                              ("fisher", lambda r: 0.5*math.log((1+max(-0.9999,min(0.9999,r)))/(1-max(-0.9999,min(0.9999,r)))) if r is not None else None),
                              ("r*|r|", lambda r: r*abs(r) if r is not None else None),
                              ("-|r|",  lambda r: -abs(r) if r is not None else None)]:
                ser=[tf(v) if v is not None else None for v in r_ser]
                for esm in (1,3,5,7,10):
                    sm = ema(ser, esm) if esm>1 else ser
                    for off in range(-2,3):
                        if off==0: tail=sm[-N:]
                        elif off>0: tail=sm[-(N+off):-off]
                        else: tail=sm[-(N+off):] if (N+off)<=len(sm) else None
                        if not tail or len(tail)!=N: continue
                        rc=corr(cc_obs, tail)
                        a,b,rms=affine(cc_obs, tail)
                        if rc==rc and a is not None:
                            results.append((rc, sname, L, tname, esm, off, a, b, rms))
    results.sort(key=lambda t:-t[0])
    print("\n[12] Top 30 CC fits:")
    for rc,s,L,tn,esm,off,a,b,rms in results[:30]:
        print(f"  r={rc:+.4f} {s:12}/L{L:<2} {tn:7} ema={esm:<2} off={off:+d}  {a:+6.3f}*x{b:+6.3f}  rms={rms:.3f}", flush=True)


if __name__ == "__main__":
    main()
