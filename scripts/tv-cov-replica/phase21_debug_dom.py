"""
Phase 21: debug the DOM — find ALL legend-like panels and their class names,
then scrape values per-pane. Previous probe only found 1 legend but chart
has 2 panes (original + replica).
"""
import asyncio, json
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

DEBUG_PROBE = r"""
  () => {
    // Find every element whose class attribute contains "legend" (case-insensitive)
    const all = Array.from(document.querySelectorAll('*'));
    const legends = all.filter(e => {
      const c = (e.className && e.className.baseVal) || e.className || '';
      return typeof c === 'string' && /legend/i.test(c);
    });
    // Group by top-level class token
    const by_class = {};
    for (const e of legends) {
      const c = e.className;
      const key = typeof c === 'string' ? c.split(/\s+/).find(x => /legend/i.test(x)) || c : String(c);
      if (!by_class[key]) by_class[key] = 0;
      by_class[key]++;
    }
    // Also find likely-pane containers by searching for widget/legend containers
    const pane_containers = all.filter(e => {
      const c = (e.className && e.className.baseVal) || e.className || '';
      return typeof c === 'string' && /pane/i.test(c);
    }).slice(0, 20).map(e => {
      const c = e.className;
      return typeof c === 'string' ? c.split(/\s+/)[0] : String(c);
    });
    return { by_class, legend_count: legends.length, pane_sample: pane_containers };
  }
"""

VALUES_PROBE = r"""
  () => {
    // Try broader selectors to pick up all legend panels
    const selectors = [
      '[class*="legend-l31H9iuA"]',
      '[class*="legendItem-"]',
      '[class*="legend__"]',
      '[data-name*="legend"]',
      '[data-name="legend-series-item"]',
    ];
    const legs = [];
    for (const sel of selectors) {
      const found = Array.from(document.querySelectorAll(sel))
        .filter(l => l.getBoundingClientRect().width > 0);
      legs.push({ selector: sel, count: found.length });
    }
    // Now grab per-pane: look at ancestor "pane" for each series-legend entry
    const items = Array.from(document.querySelectorAll('[data-name="legend-series-item"]'));
    const per_item = items.map(it => {
      let pane = it.closest('[class*="pane-"]') || it.closest('[class*="chart-container"]');
      const paneCls = pane ? (pane.className || '').slice(0, 120) : '';
      const title_el = it.querySelector('[class*="title-"]');
      const title = title_el ? title_el.innerText.trim() : '';
      const vals = Array.from(it.querySelectorAll('[class*="valueValue-"]'))
        .map(e => ({ title: e.getAttribute('title') || '', text: (e.innerText || '').trim().replace('\u2212','-') }));
      return { paneCls, title, vals };
    });
    return { legs, per_item };
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

        await page.screenshot(path=str(OUT/"phase21_loaded.png"), full_page=False)
        dbg = await page.evaluate(DEBUG_PROBE)
        print("[21] legend class counts:", json.dumps(dbg["by_class"], indent=2))
        print(f"[21] total legend-class elements: {dbg['legend_count']}")
        print(f"[21] pane class samples: {dbg['pane_sample'][:10]}")

        vals = await page.evaluate(VALUES_PROBE)
        print(f"\n[21] selector counts:")
        for s in vals["legs"]:
            print(f"  '{s['selector']}' → {s['count']}")
        print(f"\n[21] per-item ({len(vals['per_item'])} items):")
        for i, it in enumerate(vals["per_item"][:30]):
            print(f"  #{i} pane={it['paneCls'][:60]}")
            print(f"      title='{it['title']}'  vals={it['vals'][:5]}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
