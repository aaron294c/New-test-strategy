"""
Phase 20: scrape per-legend-panel values. If both the original CoV and my
replica are on the chart, they are separate legend panels. Capture each
panel independently so we don't alias "Correlation" across them.
"""
import asyncio, csv, json
from pathlib import Path
from playwright.async_api import async_playwright

COOKIE_FILE = Path("/tmp/tv_cookies.json")
CHART_URL   = "https://www.tradingview.com/chart/XgNLLOpn/?symbol=NASDAQ%3ANVDA"
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
        .filter(l => l.getBoundingClientRect().width>0);
    const out = [];
    for (const l of legs) {
      const name = (l.querySelector('[class*="title-l31H9iuA"]')?.innerText || '').trim();
      const vals = {};
      for (const e of l.querySelectorAll('[class*="valueValue-l31H9iuA"]')) {
        const t = e.getAttribute('title') || '';
        if (t) vals[t] = (e.innerText||'').trim().replace('\u2212','-');
      }
      out.push({name, vals});
    }
    return out;
  }
"""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"])
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080})
        await ctx.add_cookies(load_cookies())
        page = await ctx.new_page()
        await page.goto(CHART_URL, wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(25_000)
        for sel in ['button:has-text("Don\'t allow")',
                    'button:has-text("Got it")',
                    'button:has-text("Close")']:
            try:
                b = page.locator(sel).first
                if await b.count() > 0: await b.click(); await page.wait_for_timeout(300)
            except: pass

        await page.screenshot(path=str(OUT/"phase20_loaded.png"), full_page=False)
        legs = await page.evaluate(PROBE)
        print(f"[20] Found {len(legs)} legend panels:", flush=True)
        for i, l in enumerate(legs):
            print(f"  #{i} name='{l['name']}' keys={list(l['vals'].keys())}", flush=True)
            print(f"     sample vals={dict(list(l['vals'].items())[:6])}", flush=True)

        # Find original (whose name includes "CoV" but not "Replica"/"CoV*")
        # and replica (name includes "CoV Replica" or short "CoV*")
        def is_replica(name):
            return "Replica" in name or name.strip() == "CoV*"
        orig_idx = next((i for i, l in enumerate(legs)
                         if ("CoV" in l["name"] or "Coefficient" in str(l["vals"].keys()))
                         and not is_replica(l["name"])), None)
        rep_idx = next((i for i, l in enumerate(legs) if is_replica(l["name"])), None)
        print(f"[20] orig_idx={orig_idx} rep_idx={rep_idx}", flush=True)

        raw = []
        for x in range(80, 1860, 1):
            await page.mouse.move(x, 450)
            await page.wait_for_timeout(90)
            legs = await page.evaluate(PROBE)
            row = {"x": x}
            if orig_idx is not None and orig_idx < len(legs):
                ov = legs[orig_idx]["vals"]
                row["orig_cv"]    = ov.get("Coefficient of Variation Plot", "")
                row["orig_cvma"]  = ov.get("CV MA ", "") or ov.get("CV MA", "")
                row["orig_cc"]    = ov.get("Correlation", "")
            if rep_idx is not None and rep_idx < len(legs):
                rv = legs[rep_idx]["vals"]
                row["rep_cv"]     = rv.get("Coefficient of Variation Plot", "")
                row["rep_cvma"]   = rv.get("CV MA ", "") or rv.get("CV MA", "")
                row["rep_ccline"] = rv.get("CC Direction Line", "")
                row["rep_corr"]   = rv.get("Correlation", "")  # hidden dirMetric
            raw.append(row)

        # Dedupe by unique cv/cvma/cc combo
        bars = []; last = None
        for r in raw:
            key = (r.get("orig_cv",""), r.get("orig_cvma",""), r.get("orig_cc",""), r.get("rep_ccline",""))
            if not r.get("orig_cv"): continue
            if key != last:
                bars.append(r); last = key
        print(f"[20] raw={len(raw)}, deduped={len(bars)}", flush=True)

        csv_path = OUT/"phase20_both.csv"
        fields = ["x","orig_cv","orig_cvma","orig_cc","rep_cv","rep_cvma","rep_ccline","rep_corr"]
        with csv_path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for b in bars: w.writerow({k: b.get(k, "") for k in fields})
        print(f"[20] wrote {csv_path}", flush=True)

        # Stats
        try:
            diffs = []
            for b in bars:
                try:
                    o = float(b["orig_cc"]); r = float(b["rep_ccline"])
                    diffs.append(o - r)
                except: pass
            if diffs:
                import statistics
                print(f"[20] orig_cc vs rep_ccline: mean_diff={statistics.mean(diffs):+.3f}, "
                      f"stdev={statistics.stdev(diffs):.3f}, max|diff|={max(abs(d) for d in diffs):.3f}")
        except Exception as e:
            print(f"[20] stats error: {e}")

        print("\n[20] First 3 & last 3 bars:")
        for b in bars[:3] + bars[-3:]:
            print(f"  x={b['x']:>4} orig_cv={b.get('orig_cv'):>7} orig_cc={b.get('orig_cc'):>8} "
                  f"rep_ccline={b.get('rep_ccline'):>8} rep_corr={b.get('rep_corr','?'):>7}", flush=True)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
