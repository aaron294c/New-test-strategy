"""
Phase 22: inspect each of the 3 legend-l31H9iuA elements individually —
find which are the two indicator panes (top=original, bottom=replica).
"""
import asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright

COOKIE_FILE = Path("/tmp/tv_cookies.json")
CHART_URL   = "https://www.tradingview.com/chart/XgNLLOpn/?symbol=NASDAQ%3ANVDA"
OUT         = Path("/tmp/tv-cov-out")
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
    return legs.map((l, i) => {
      const rect = l.getBoundingClientRect();
      // Find the pane this legend belongs to
      const pane = l.closest('tr[class*="pane"]') || l.closest('[class*="pane-"]') || l.parentElement;
      const paneHeight = pane ? pane.getBoundingClientRect().height : 0;
      const paneTop = pane ? pane.getBoundingClientRect().top : 0;
      // Collect all inner valueValue elements with their titles
      const vals = Array.from(l.querySelectorAll('[class*="valueValue-l31H9iuA"]'))
        .map(e => ({ title: e.getAttribute('title') || '', text: (e.innerText||'').trim().replace('\u2212','-') }));
      // Collect any "titleWrapper" or source name
      const srcEl = l.querySelector('[class*="mainTitle-"], [class*="title-l31H9iuA"]');
      const srcName = srcEl ? srcEl.innerText.trim() : '';
      return {
        idx: i, visible: rect.width > 0 && rect.height > 0,
        width: rect.width, height: rect.height,
        top: rect.top, bottom: rect.bottom,
        paneHeight, paneTop,
        srcName,
        valsCount: vals.length,
        vals: vals
      };
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

        await page.screenshot(path=str(OUT/"phase22_loaded.png"), full_page=False)
        legs = await page.evaluate(PROBE)
        for l in legs:
            print(f"\n[#{l['idx']}] visible={l['visible']} size={l['width']:.0f}x{l['height']:.0f} "
                  f"top={l['top']:.0f} bottom={l['bottom']:.0f}")
            print(f"      srcName='{l['srcName']}'")
            print(f"      vals ({l['valsCount']} items):")
            for v in l['vals']:
                print(f"        title='{v['title']}'  text='{v['text']}'")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
