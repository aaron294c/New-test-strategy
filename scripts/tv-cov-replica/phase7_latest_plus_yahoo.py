"""
Phase 7: (a) read the CoV legend values for the LATEST bar (mouse parked off
chart) and a sweep across recent bars, (b) fetch SPY daily from Yahoo for the
same window, (c) evaluate several candidate CV / CC formulas against the
scraped values, report best fit. Pure-numpy, no sklearn / scipy needed.
"""
import asyncio, csv, json, math, urllib.request
from pathlib import Path
from playwright.async_api import async_playwright

COOKIE_FILE = Path("/tmp/tv_cookies.json")
CHART_URL   = "https://www.tradingview.com/chart/XgNLLOpn/"
OUT         = Path("/tmp/tv-cov-out"); OUT.mkdir(exist_ok=True)
SAMESITE    = {"no_restriction": "None", "lax": "Lax", "strict": "Strict", None: "Lax"}

def load_cookies():
    raw = json.loads(COOKIE_FILE.read_text()); res = []
    for c in raw:
        pc = {"name": c["name"], "value": c["value"], "domain": c["domain"],
              "path": c.get("path", "/"), "secure": bool(c.get("secure", False)),
              "httpOnly": bool(c.get("httpOnly", False)),
              "sameSite": SAMESITE.get(c.get("sameSite"), "Lax")}
        if "expirationDate" in c: pc["expires"] = int(c["expirationDate"])
        res.append(pc)
    return res

PROBE = r"""
  () => {
    const legs = Array.from(document.querySelectorAll('[class*="legend-l31H9iuA"]'))
        .filter(l => l.getBoundingClientRect().width > 0);
    const v = {};
    for (const l of legs)
      for (const e of l.querySelectorAll('[class*="valueValue-l31H9iuA"]')) {
        const t = e.getAttribute('title') || '';
        if (t) v[t] = (e.innerText||'').trim().replace('\u2212','-');
      }
    return v;
  }
"""


async def scrape():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage"])
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080})
        await ctx.add_cookies(load_cookies())
        page = await ctx.new_page()
        await page.goto(CHART_URL, wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(14_000)
        try:
            b = page.locator('button:has-text("Don\'t allow")').first
            if await b.count() > 0:
                await b.click(); await page.wait_for_timeout(400)
        except Exception: pass

        # Latest-bar: mouse in top bar
        await page.mouse.move(100, 20); await page.wait_for_timeout(800)
        latest = await page.evaluate(PROBE)
        # Sweep across bars
        sweep = []
        for x in range(1440, 120, -18):
            await page.mouse.move(x, 450); await page.wait_for_timeout(120)
            v = await page.evaluate(PROBE)
            sweep.append({"x": x,
                          "cv": v.get("Coefficient of Variation Plot",""),
                          "cv_ma": v.get("CV MA ","") or v.get("CV MA",""),
                          "cc": v.get("CC Direction Line","")})
        await browser.close()
        return latest, sweep


def yahoo_spy(days=3*365):
    import time
    end = int(time.time())
    start = end - days * 86400
    url = (f"https://query1.finance.yahoo.com/v7/finance/download/SPY?"
           f"period1={start}&period2={end}&interval=1d&events=history")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=20).read().decode()
    rows = [r.split(",") for r in data.strip().split("\n")[1:]]
    closes = [(r[0], float(r[4])) for r in rows if r[4] not in ("null","")]
    return closes  # list of (date, close)


def try_yahoo_v8():
    import time
    end = int(time.time())
    start = end - 3*365*86400
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/SPY?"
           f"period1={start}&period2={end}&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    j = json.loads(urllib.request.urlopen(req, timeout=20).read())
    r = j["chart"]["result"][0]
    ts  = r["timestamp"]
    cl  = r["indicators"]["quote"][0]["close"]
    import datetime
    return [(datetime.date.fromtimestamp(t).isoformat(), c)
            for t, c in zip(ts, cl) if c is not None]


# ── Candidate formulas ───────────────────────────────────────────────────────
def ema(x, n):
    a = 2.0 / (n + 1); out = [None]*len(x); m = None
    for i, v in enumerate(x):
        if v is None: out[i] = m; continue
        m = v if m is None else a*v + (1-a)*m
        out[i] = m
    return out

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

def log_ret(c):
    out = [None]; [out.append(math.log(c[i]/c[i-1])) for i in range(1,len(c))]
    return out

def super_smoother(x, period):
    a = math.exp(-math.sqrt(2)*math.pi/period)
    b = 2*a*math.cos(math.sqrt(2)*math.pi/period)
    c2, c3 = b, -a*a; c1 = 1 - c2 - c3
    out = [0.0]*len(x); prev1 = 0.0; prev2 = 0.0
    for i, v in enumerate(x):
        if v is None: out[i] = prev1; continue
        out[i] = c1*v + c2*prev1 + c3*prev2
        prev2, prev1 = prev1, out[i]
    return out

def high_pass(x, period):
    a = (math.cos(math.sqrt(2)*math.pi/period) + math.sin(math.sqrt(2)*math.pi/period) - 1) / math.cos(math.sqrt(2)*math.pi/period)
    out = [0.0]*len(x); prev1 = 0.0; prev2 = 0.0
    for i in range(len(x)):
        v  = x[i]  if x[i]  is not None else 0.0
        v1 = x[i-1] if i>=1 and x[i-1] is not None else 0.0
        v2 = x[i-2] if i>=2 and x[i-2] is not None else 0.0
        out[i] = ((1-a/2)**2)*(v - 2*v1 + v2) + 2*(1-a)*prev1 - ((1-a)**2)*prev2
        prev2, prev1 = prev1, out[i]
    return out


def cv_candidates(closes):
    rets = log_ret(closes)
    # fill None with 0 for filter stages
    rets0 = [0.0 if r is None else r for r in rets]
    smooth = super_smoother(rets0, 2)
    hp500  = high_pass(smooth,  500)
    hp50   = high_pass(smooth,  50)
    # v1: my current formula (SS(LP=2) → HP(500)), CV over 5
    m1 = sma(hp500, 5); s1 = stdev(hp500, 5)
    cv1 = [s/abs(m)*2 if (m is not None and s is not None and abs(m)>1e-12) else None for m,s in zip(m1,s1)]
    # v2: no HP, raw returns, 5-bar
    m2 = sma(rets, 5); s2 = stdev(rets, 5)
    cv2 = [s/abs(m)*2 if (m is not None and s is not None and abs(m)>1e-12) else None for m,s in zip(m2,s2)]
    # v3: HP=50
    m3 = sma(hp50, 5); s3 = stdev(hp50, 5)
    cv3 = [s/abs(m)*2 if (m is not None and s is not None and abs(m)>1e-12) else None for m,s in zip(m3,s3)]
    # v4: stdev/mean of |returns|
    absr = [abs(r) if r is not None else None for r in rets]
    m4 = sma(absr, 5); s4 = stdev(absr, 5)
    cv4 = [s/abs(m)*2 if (m is not None and s is not None and abs(m)>1e-12) else None for m,s in zip(m4,s4)]
    # v5: stdev(close)/mean(close) — rolling price
    m5 = sma(closes, 5); s5 = stdev(closes, 5)
    cv5 = [s/abs(m)*2 if (m is not None and s is not None and abs(m)>1e-12) else None for m,s in zip(m5,s5)]
    return {"v1_SS_HP500": cv1, "v2_raw_ret": cv2, "v3_SS_HP50": cv3,
            "v4_absret":    cv4, "v5_close":   cv5}


def cc_candidates(closes, lookback=5):
    # Pearson r(close, bar_index)
    r_vals = [None]*len(closes)
    for i in range(lookback-1, len(closes)):
        y = closes[i-lookback+1:i+1]
        x = list(range(lookback))
        mx = sum(x)/lookback; my = sum(y)/lookback
        num = sum((xi-mx)*(yi-my) for xi,yi in zip(x,y))
        dx = math.sqrt(sum((xi-mx)**2 for xi in x))
        dy = math.sqrt(sum((yi-my)**2 for yi in y))
        r_vals[i] = num/(dx*dy) if dx*dy > 1e-12 else None
    # Fisher z
    def fisher(r):
        if r is None: return None
        r = max(-0.9999, min(0.9999, r))
        return 0.5*math.log((1+r)/(1-r))
    z  = [fisher(r) for r in r_vals]
    ccA = [zi*2.1 - 4.6 if zi is not None else None for zi in z]   # Fisher × 2.1 − 4.6
    ccB = [ri*2.1 - 4.6 if ri is not None else None for ri in r_vals]  # raw r × 2.1 − 4.6
    ccC = [abs(ri)*(-2.1) - 2.5 if ri is not None else None for ri in r_vals]  # sign-flip
    return {"fisher_z": ccA, "raw_r": ccB, "abs_r_neg": ccC}, r_vals


def main():
    # (a) Scrape
    latest, sweep = asyncio.run(scrape())
    print(f"[7] latest (no-hover) legend: {latest}", flush=True)

    (OUT / "phase7_sweep.csv").write_text(
        "x,cv,cv_ma,cc\n" + "\n".join(f"{r['x']},{r['cv']},{r['cv_ma']},{r['cc']}" for r in sweep))
    # (b) SPY closes
    print("[7] fetching SPY daily from Yahoo…", flush=True)
    try:
        closes = try_yahoo_v8()
    except Exception as e:
        print(f"[7] yahoo v8 failed: {e}", flush=True)
        closes = yahoo_spy()
    print(f"[7] fetched {len(closes)} rows, latest={closes[-5:]}", flush=True)
    only_c = [c for _, c in closes]

    # (c) Candidate fits against LATEST scraped values
    scraped_cv    = float(latest.get("Coefficient of Variation Plot","nan"))
    scraped_cv_ma = float(latest.get("CV MA ","nan") or latest.get("CV MA","nan"))
    scraped_cc    = float(latest.get("CC Direction Line","nan"))
    print(f"[7] latest scraped — CV={scraped_cv}  CV_MA={scraped_cv_ma}  CC={scraped_cc}", flush=True)

    cvs = cv_candidates(only_c)
    for name, series in cvs.items():
        # take last 5 non-None for comparison
        tail = [v for v in series[-10:] if v is not None][-1:]
        latest_v = tail[0] if tail else float("nan")
        diff = abs(latest_v - scraped_cv) if latest_v==latest_v else float("nan")
        print(f"  CV {name:14} latest={latest_v:.4f}  |Δ|={diff:.4f}", flush=True)

    cc_map, r_vals = cc_candidates(only_c, 5)
    for name, series in cc_map.items():
        latest_v = series[-1] if series[-1] is not None else float("nan")
        diff = abs(latest_v - scraped_cc) if latest_v==latest_v else float("nan")
        print(f"  CC {name:14} latest={latest_v:.4f}  |Δ|={diff:.4f}", flush=True)
    print(f"[7] raw r for last bar: {r_vals[-1]}", flush=True)


if __name__ == "__main__":
    main()
