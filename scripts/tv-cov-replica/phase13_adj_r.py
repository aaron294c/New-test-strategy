"""
Phase 13: retry CC with 'Adjusted r' mode. Standard formulas:
  adj_r² = 1 - (1-r²)(n-1)/(n-2)        (k=1 predictor)
  adj_r  = sign(r) * sqrt(max(0, adj_r²))
Also try alternate k, and use R_Squared_Length=10 (not CC_Lookback=5).
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
    return [c for t,c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]) if c is not None]

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
def affine(obs,com):
    xs=[(c,s) for c,s in zip(com,obs) if c is not None and s is not None]
    if len(xs)<5: return None,None,None
    mc=sum(c for c,_ in xs)/len(xs); ms=sum(s for _,s in xs)/len(xs)
    var=sum((c-mc)**2 for c,_ in xs); cov=sum((c-mc)*(s-ms) for c,s in xs)
    a=cov/var if var>1e-12 else 0; b=ms-a*mc
    rms=math.sqrt(sum((s-(a*c+b))**2 for c,s in xs)/len(xs))
    return a,b,rms
def pearson_x(series,L):
    o=[None]*len(series); xs=list(range(L)); mx=sum(xs)/L
    dx=math.sqrt(sum((a-mx)**2 for a in xs))
    for i in range(L-1,len(series)):
        y=series[i-L+1:i+1]; my=sum(y)/L
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
    N=len(scraped); cc_obs=[b["cc"] for b in scraped]
    closes=yahoo()
    print(f"[13] N={N} closes={len(closes)}", flush=True)

    results=[]
    # Test L (r-squared length) from 5..20
    for L in range(3, 25):
        rs = pearson_x(closes, L)
        # Four transforms
        tfs = {
            "r":        lambda r: r,
            "r2":       lambda r: r*r,
            "adj_r_k1": lambda r: (1 if r>=0 else -1)*math.sqrt(max(0, 1 - (1-r*r)*(L-1)/(L-2))) if L>2 else r,
            "adj_r_k2": lambda r: (1 if r>=0 else -1)*math.sqrt(max(0, 1 - (1-r*r)*(L-1)/(L-3))) if L>3 else r,
            "adj_r2_k1":lambda r: max(0, 1 - (1-r*r)*(L-1)/(L-2)) if L>2 else r*r,
            "abs_adj_r":lambda r: math.sqrt(max(0, 1 - (1-r*r)*(L-1)/(L-2))) if L>2 else abs(r),
            "sign_r2":  lambda r: (1 if r>=0 else -1)*r*r,
        }
        for tname, tf in tfs.items():
            ser = [tf(v) if v is not None else None for v in rs]
            for esm in (1, 2, 3, 5, 7, 10):
                sm = ema(ser, esm) if esm>1 else ser
                tail = sm[-N:]
                rc = corr(cc_obs, tail)
                a,b,rms = affine(cc_obs, tail)
                if rc==rc and a is not None:
                    results.append((rc, L, tname, esm, a, b, rms))
    results.sort(key=lambda t:-t[0])
    print("\n[13] Top 25 CC fits with adjusted-r family:")
    for rc,L,tn,esm,a,b,rms in results[:25]:
        print(f"  r={rc:+.4f} L={L:<2} {tn:10} ema={esm:<2}  {a:+6.3f}*x{b:+6.3f}  rms={rms:.3f}", flush=True)

    # Test: if L=10 and adj_r_k1, is the last-bar value near -3.01?
    print("\n[13] last-bar sanity for L=10, adj_r_k1, ema=1:")
    rs=pearson_x(closes,10)
    for v in rs[-5:]:
        if v is None: continue
        adj = (1 if v>=0 else -1)*math.sqrt(max(0, 1 - (1-v*v)*9/8))
        print(f"  r={v:+.4f}  adj_r={adj:+.4f}  *2.1-4.6={adj*2.1-4.6:+.3f}")


if __name__ == "__main__":
    main()
