"""
Phase 23: per-pane scraping — legend #1 is original CoV, legend #2 is my
replica CoV*. Capture CC values from both panes and write side-by-side CSV
so we can directly compare historical morphology bar-by-bar.
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
    const legs = Array.from(document.querySelectorAll('[class*="legend-l31H9iuA"]'));
    return legs.map(l => {
      const src = l.querySelector('[class*="mainTitle-"], [class*="title-l31H9iuA"]');
      const vals = {};
      for (const e of l.querySelectorAll('[class*="valueValue-l31H9iuA"]')) {
        const t = e.getAttribute('title') || '';
        if (t) vals[t] = (e.innerText||'').trim().replace('\u2212','-');
      }
      return { srcName: src ? src.innerText.trim() : '', vals };
    });
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
        for sel in ['button:has-text("Don\'t allow")', 'button:has-text("Got it")', 'button:has-text("Close")']:
            try:
                b = page.locator(sel).first
                if await b.count() > 0: await b.click(); await page.wait_for_timeout(300)
            except: pass

        init = await page.evaluate(PROBE)
        # Identify original vs replica by srcName: "CoV" = original, "CoV*" = replica
        def srcnorm(s): return s.replace("\n", " ").strip()
        orig_idx = next((i for i, l in enumerate(init) if srcnorm(l["srcName"]) == "CoV"), None)
        rep_idx  = next((i for i, l in enumerate(init) if "CoV*" in srcnorm(l["srcName"]) or "Replica" in srcnorm(l["srcName"])), None)
        print(f"[23] orig_idx={orig_idx} rep_idx={rep_idx}")
        for i, l in enumerate(init):
            print(f"  init[#{i}] src='{srcnorm(l['srcName'])}' keys={list(l['vals'].keys())[:5]}...")

        raw = []
        for x in range(80, 1860, 1):
            await page.mouse.move(x, 450)
            await page.wait_for_timeout(90)
            legs = await page.evaluate(PROBE)
            row = {"x": x}
            if orig_idx is not None and orig_idx < len(legs):
                ov = legs[orig_idx]["vals"]
                row["o_cv"]   = ov.get("Coefficient of Variation Plot", "")
                row["o_cvma"] = ov.get("CV MA ", "") or ov.get("CV MA", "")
                row["o_cc"]   = ov.get("CC Direction Line", "")
                row["o_corr"] = ov.get("Correlation", "")
            if rep_idx is not None and rep_idx < len(legs):
                rv = legs[rep_idx]["vals"]
                row["r_cv"]   = rv.get("Coefficient of Variation Plot", "")
                row["r_cvma"] = rv.get("CV MA ", "") or rv.get("CV MA", "")
                row["r_cc"]   = rv.get("CC Direction Line", "")
            raw.append(row)

        bars = []; last = None
        for r in raw:
            key = (r.get("o_cv",""), r.get("o_cc",""), r.get("r_cv",""), r.get("r_cc",""))
            if not r.get("o_cv"): continue
            if key != last:
                bars.append(r); last = key
        print(f"[23] raw={len(raw)}, deduped={len(bars)}")

        csv_path = OUT/"phase23_both_panes.csv"
        fields = ["x","o_cv","o_cvma","o_cc","o_corr","r_cv","r_cvma","r_cc"]
        with csv_path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for b in bars: w.writerow({k: b.get(k, "") for k in fields})
        print(f"[23] wrote {csv_path}")

        print("\nBar-by-bar (last 20 bars):")
        for b in bars[-20:]:
            print(f"  x={b['x']:>4} o_cv={b.get('o_cv',''):>7} o_cc={b.get('o_cc',''):>8} "
                  f"| r_cv={b.get('r_cv',''):>7} r_cc={b.get('r_cc',''):>8}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
