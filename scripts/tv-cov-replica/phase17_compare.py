"""
Phase 17: Compare predicted CC (via best phase16 formula) vs actual CC
bar-by-bar. Identify WHERE morphology diverges to guide formula fixes.
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

def main():
    bars = []
    with (OUT/"phase14_nvda.csv").open() as f:
        for r in csv.DictReader(f):
            try: bars.append({"cv":float(r["cv"]),"cv_ma":float(r["cv_ma"]),"cc":float(r["cc"])})
            except: pass

    cv = [b["cv"] for b in bars]
    cvma = [b["cv_ma"] for b in bars]
    cc = [b["cc"] for b in bars]
    diff = [c-m for c, m in zip(cv, cvma)]

    # Best phase16 formula
    rRaw = pearson_t(diff, 13)
    rSmooth = ema(rRaw, 5)
    pred_cc = [(-4.6 + 2.1*(1 - v)) if v is not None else None for v in rSmooth]

    # Real dir metric implied by actual cc
    real_dir = [1 - (p-(-4.6))/2.1 for p in cc]

    print(f"{'bar':>3} {'cv':>6} {'cvma':>6} {'diff':>7} {'r_raw':>7} {'r_ema5':>7}  {'pred_cc':>8} {'real_cc':>8}  {'err':>7} {'real_dir':>8}")
    for i in range(len(bars)):
        pc = pred_cc[i]
        rr = rRaw[i]
        rs = rSmooth[i]
        pc_s = f"{pc:+.3f}" if pc is not None else "  none"
        rr_s = f"{rr:+.3f}" if rr is not None else "  none"
        rs_s = f"{rs:+.3f}" if rs is not None else "  none"
        err = (cc[i] - pc) if pc is not None else None
        err_s = f"{err:+.3f}" if err is not None else "  none"
        print(f"{i:>3} {cv[i]:>6.3f} {cvma[i]:>6.3f} {diff[i]:>+7.3f} {rr_s:>7} {rs_s:>7}  {pc_s:>8} {cc[i]:>+8.3f}  {err_s:>7} {real_dir[i]:>+8.3f}")

    # Stats
    errs = [cc[i] - pred_cc[i] for i in range(len(bars)) if pred_cc[i] is not None]
    if errs:
        me = sum(errs)/len(errs); rms = math.sqrt(sum(e*e for e in errs)/len(errs))
        print(f"\nMean err: {me:+.3f}, RMS: {rms:.3f}, max |err|: {max(abs(e) for e in errs):.3f}")


if __name__ == "__main__":
    main()
