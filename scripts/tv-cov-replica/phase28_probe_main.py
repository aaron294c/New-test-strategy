"""
Phase 28: inspect main-pane legend DOM to find where OHLC values are rendered.
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
    // Focus on main pane (idx 0)
    const main = legs[0];
    if (!main) return { found: false };
    const allSpans = Array.from(main.querySelectorAll('*'));
    // Return first 60 descendants with their tag, class (first token), text, and title/data attributes
    const desc = allSpans.slice(0, 100).map(e => ({
      tag: e.tagName,
      cls: (typeof e.className === 'string' ? e.className.split(' ')[0] : ''),
      text: (e.innerText || '').trim().slice(0, 30),
      title: e.getAttribute('title') || '',
      dataName: e.getAttribute('data-name') || ''
    }));
    return { found: true, outerClass: main.className, desc };
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
        # Hover on a known-good pixel so OHLC renders
        await page.mouse.move(1200, 450)
        await page.wait_for_timeout(500)
        res = await page.evaluate(PROBE)
        print(json.dumps(res, indent=2))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
