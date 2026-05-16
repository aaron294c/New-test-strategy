"""
Phase 16: fit CC formula using the SCRAPED CV series directly (no Yahoo
data), eliminating any data-source mismatch. Tests:
  - corr(cv_obs, bar_index, L) for various L
  - corr(cv_obs, cv_ma_obs, L)
  - various smoothings & modes

If morphology r jumps close to 1 here (vs 0.73 using Yahoo), the difference
was data-alignment noise, not formula error.
"""
import csv, math
from pathlib import Path

OUT = Path("/tmp/tv-cov-out")

def ema(x,n):
    a=2/(n+1); o=[None]*len(x); s=None
    for i,v in enumerate(x):
        if v is None: o[i]=s; continue
        s = v if s is None else a*v+(1-a)*s
        o[i]=s
    return o

def sma(x,n):
    o=[None]*len(x)
    for i in range(n-1,len(x)):
        w=x[i-n+1:i+1]
        if any(v is None for v in w): continue
        o[i]=sum(w)/n
    return o

def pearson_t(series, L):
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

def pearson_xy(a,b,L):
    o=[None]*len(a)
    for i in range(L-1,len(a)):
        xs=a[i-L+1:i+1]; ys=b[i-L+1:i+1]
        if any(v is None for v in xs) or any(v is None for v in ys): continue
        mx=sum(xs)/L; my=sum(ys)/L
        num=sum((x-mx)*(y-my) for x,y in zip(xs,ys))
        dx=math.sqrt(sum((x-mx)**2 for x in xs))
        dy=math.sqrt(sum((y-my)**2 for y in ys))
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

def adj_k1(r, n):
    if r is None or n<=2: return r
    return (1 if r>=0 else -1)*math.sqrt(max(0, 1 - (1-r*r)*(n-1)/(n-2)))


def main():
    bars=[]
    with (OUT/"phase14_nvda.csv").open() as f:
        for r in csv.DictReader(f):
            try: bars.append({"cv":float(r["cv"]),"cv_ma":float(r["cv_ma"]),"cc":float(r["cc"])})
            except: pass
    N=len(bars)
    cv_obs   = [b["cv"]    for b in bars]
    cvma_obs = [b["cv_ma"] for b in bars]
    cc_obs   = [b["cc"]    for b in bars]
    dir_obs  = [1 - (p - (-4.6))/2.1 for p in cc_obs]
    print(f"[16] bars={N}, CV range=[{min(cv_obs):.3f},{max(cv_obs):.3f}], CC range=[{min(cc_obs):.3f},{max(cc_obs):.3f}]")
    print(f"[16] dirMetric target range=[{min(dir_obs):.3f},{max(dir_obs):.3f}]")
    print(f"[16] last bar: CV={cv_obs[-1]} CV_MA={cvma_obs[-1]} CC={cc_obs[-1]}  dir_target={dir_obs[-1]:+.4f}")

    results=[]
    # corr(cv_obs, bar_index) — the most direct hypothesis
    for L in range(3, 31):
        rs = pearson_t(cv_obs, L)
        for mode in ("raw","adj"):
            if mode=="raw": ser=rs
            else: ser=[adj_k1(v,L) if v is not None else None for v in rs]
            for smooth in ("none","ema3","ema5","ema7","sma3","sma5","sma7"):
                if smooth=="none": sm=ser
                elif smooth.startswith("ema"): sm=ema(ser,int(smooth[3:]))
                else: sm=sma([v if v is not None else 0 for v in ser], int(smooth[3:]))
                if len(sm)!=N: continue
                r_fit=corr_coef(dir_obs, sm)
                if r_fit==r_fit:
                    a,b,rms=affine(dir_obs, sm)
                    last_pred = sm[-1]
                    last_cc_pred = -4.6 + 2.1*(1 - (last_pred if last_pred is not None else 0))
                    results.append(("cv_obs~t", L, mode, smooth, r_fit, rms, a, b, last_cc_pred))

    # corr(cv_obs, cv_ma_obs) cross
    for L in range(3, 31):
        rs = pearson_xy(cv_obs, cvma_obs, L)
        for mode in ("raw","adj"):
            if mode=="raw": ser=rs
            else: ser=[adj_k1(v,L) if v is not None else None for v in rs]
            for smooth in ("none","ema3","ema5","sma3","sma5"):
                if smooth=="none": sm=ser
                elif smooth.startswith("ema"): sm=ema(ser,int(smooth[3:]))
                else: sm=sma([v if v is not None else 0 for v in ser], int(smooth[3:]))
                if len(sm)!=N: continue
                r_fit=corr_coef(dir_obs, sm)
                if r_fit==r_fit:
                    a,b,rms=affine(dir_obs, sm)
                    last_pred = sm[-1]
                    last_cc_pred = -4.6 + 2.1*(1 - (last_pred if last_pred is not None else 0))
                    results.append(("cv_obs~cvma", L, mode, smooth, r_fit, rms, a, b, last_cc_pred))

    # also: corr(cv_obs - cv_ma_obs, bar_index) — detrended
    diff = [c-m for c,m in zip(cv_obs, cvma_obs)]
    for L in range(3, 31):
        rs = pearson_t(diff, L)
        for mode in ("raw","adj"):
            if mode=="raw": ser=rs
            else: ser=[adj_k1(v,L) if v is not None else None for v in rs]
            for smooth in ("none","ema3","ema5","sma3","sma5"):
                if smooth=="none": sm=ser
                elif smooth.startswith("ema"): sm=ema(ser,int(smooth[3:]))
                else: sm=sma([v if v is not None else 0 for v in ser], int(smooth[3:]))
                if len(sm)!=N: continue
                r_fit=corr_coef(dir_obs, sm)
                if r_fit==r_fit:
                    a,b,rms=affine(dir_obs, sm)
                    last_pred = sm[-1]
                    last_cc_pred = -4.6 + 2.1*(1 - (last_pred if last_pred is not None else 0))
                    results.append(("(cv-cvma)~t", L, mode, smooth, r_fit, rms, a, b, last_cc_pred))

    results.sort(key=lambda t:-t[4])
    print(f"\n[16] Top 30 candidates (morphology fit):")
    for src, L, mode, smooth, r_fit, rms, a, b, last_pred in results[:30]:
        print(f"  r={r_fit:+.4f} rms={rms:.3f}  {src:14} L={L:<2} {mode:3} {smooth:6}  "
              f"fit={a:+.3f}*x{b:+.3f}  last_cc_pred={last_pred:+.3f}")

    print("\n[16] Best-fits with last_cc close to -2.40:")
    close_last = sorted([r for r in results if abs(r[8] - (-2.40)) < 0.5], key=lambda t:-t[4])
    for src, L, mode, smooth, r_fit, rms, a, b, last_pred in close_last[:20]:
        print(f"  r={r_fit:+.4f}  {src:14} L={L:<2} {mode:3} {smooth:6}  last_cc_pred={last_pred:+.3f}")


if __name__ == "__main__":
    main()
