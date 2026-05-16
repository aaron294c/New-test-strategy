"""
Phase 14: scrape fresh per-bar (cv, cv_ma, cc) for NVDA from the TV chart
using injected session cookies. Assumes the saved layout is already showing
NVDA; if not, we set symbol via the ticker search panel.
"""
import asyncio, csv, json
from pathlib import Path
from playwright.async_api import async_playwright

COOKIE_FILE = Path("/tmp/tv_cookies.json")
CHART_URL   = "https://www.tradingview.com/chart/XgNLLOpn/?symbol=NASDAQ%3ANVDA"
OUT         = Path("/tmp/tv-cov-out"); OUT.mkdir(exist_ok=True)
SAMESITE    = {"no_restriction": "None", "lax": "Lax", "strict": "Strict", None: "Lax"}

def load_cookies():
    raw = json.loads(COOKIE_FILE.read_text()); res=[]
    for c in raw:
        pc={"name":c["name"],"value":c["value"],"domain":c["domain"],
            "path":c.get("path","/"),"secure":bool(c.get("secure",False)),
            "httpOnly":bool(c.get("httpOnly",False)),
            "sameSite":SAMESITE.get(c.get("sameSite"),"Lax")}
        if "expirationDate" in c: pc["expires"]=int(c["expirationDate"])
        res.append(pc)
    return res

PROBE = r"""
  () => {
    const legs = Array.from(document.querySelectorAll('[class*="legend-l31H9iuA"]'))
        .filter(l => l.getBoundingClientRect().width>0);
    const v = {};
    for (const l of legs)
      for (const e of l.querySelectorAll('[class*="valueValue-l31H9iuA"]')) {
        const t = e.getAttribute('title') || '';
        if (t) v[t] = (e.innerText||'').trim().replace('\u2212','-');
      }
    return v;
  }
"""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage"])
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width":1920,"height":1080})
        await ctx.add_cookies(load_cookies())
        page = await ctx.new_page()
        await page.goto(CHART_URL, wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(25_000)
        await page.screenshot(path=str(OUT/"phase14_loaded.png"), full_page=False)
        # dismiss popups
        for sel in ['button:has-text("Don\'t allow")',
                    'button:has-text("Got it")',
                    'button:has-text("Close")']:
            try:
                b = page.locator(sel).first
                if await b.count()>0: await b.click(); await page.wait_for_timeout(300)
            except: pass

        # quick snapshot of what's in the legend (to confirm NVDA + CoV present)
        leg = await page.evaluate(PROBE)
        print(f"[14] legend keys at load: {list(leg.keys())[:10]}", flush=True)
        print(f"[14] sample values: {dict(list(leg.items())[:6])}", flush=True)

        raw = []
        for x in range(80, 1860, 1):
            await page.mouse.move(x, 450)
            await page.wait_for_timeout(90)
            v = await page.evaluate(PROBE)
            raw.append((x,
                        v.get("Coefficient of Variation Plot",""),
                        v.get("CV MA ","") or v.get("CV MA",""),
                        v.get("Correlation","")))

        # Dedupe consecutive triples → one bar per unique (cv, cv_ma, cc)
        bars = []
        last = None
        for x, cv, mm, cc in raw:
            if not cv: continue
            t = (cv, mm, cc)
            if t != last:
                bars.append({"x": x, "cv": cv, "cv_ma": mm, "cc": cc})
                last = t
        print(f"[14] raw samples: {len(raw)}, deduped bars: {len(bars)}", flush=True)

        csv_path = OUT/"phase14_nvda.csv"
        with csv_path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["x","cv","cv_ma","cc"])
            w.writeheader(); w.writerows(bars)
        print(f"[14] wrote {csv_path}", flush=True)
        for b in bars[:5] + bars[-5:]:
            print(f"  x={b['x']:4} cv={b['cv']:>8} cv_ma={b['cv_ma']:>8} cc={b['cc']:>8}",
                  flush=True)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
