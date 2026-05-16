"""
Phase 2c: click the CoV header/tab in the Data Window and dump the resulting
per-plot values so we know exactly which labels to read when scraping per-bar.
"""
import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright

COOKIE_FILE = Path("/tmp/tv_cookies.json")
CHART_URL = "https://www.tradingview.com/chart/XgNLLOpn/"
OUT = Path("/tmp/tv-cov-out")
OUT.mkdir(exist_ok=True)

SAMESITE = {"no_restriction": "None", "lax": "Lax", "strict": "Strict", None: "Lax"}


def load_cookies():
    raw = json.loads(COOKIE_FILE.read_text())
    out = []
    for c in raw:
        pc = {
            "name": c["name"], "value": c["value"], "domain": c["domain"],
            "path": c.get("path", "/"), "secure": bool(c.get("secure", False)),
            "httpOnly": bool(c.get("httpOnly", False)),
            "sameSite": SAMESITE.get(c.get("sameSite"), "Lax"),
        }
        if "expirationDate" in c:
            pc["expires"] = int(c["expirationDate"])
        out.append(pc)
    return out


async def set_symbol(page, symbol):
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(300)
    await page.keyboard.type(symbol, delay=40)
    await page.wait_for_timeout(800)
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(3_500)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        await context.add_cookies(load_cookies())
        page = await context.new_page()
        await page.goto(CHART_URL, wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(10_000)

        await set_symbol(page, "SPY")
        await page.keyboard.press("Alt+D")
        await page.wait_for_timeout(2_500)

        # Click the CoV header. Multiple could exist; pick the one inside the DW.
        clicked = await page.evaluate(
            """
            () => {
              const dw = document.querySelector('.chart-data-window');
              if (!dw) return {ok:false, reason:'no-dw'};
              const headers = dw.querySelectorAll('[class*="headerTitle-_gbYDtbd"]');
              for (const h of headers) {
                if ((h.innerText||'').trim() === 'CoV') {
                  // click the parent group so it toggles
                  const btn = h.closest('[class*="header"], [class*="item"], button, div');
                  (btn||h).click();
                  return {ok:true, clicked: btn?btn.tagName:h.tagName, text:h.innerText};
                }
              }
              return {ok:false, reason:'no-cov-header', count:headers.length};
            }
            """
        )
        print(f"[2c] click CoV: {clicked}", flush=True)
        await page.wait_for_timeout(1_500)
        await page.screenshot(path=str(OUT / "phase2c_cov_clicked.png"))

        # Dump all leaves again — should now show CoV plot rows
        values = await page.evaluate(
            """
            () => {
              const dw = document.querySelector('.chart-data-window');
              if (!dw) return [];
              const out = [];
              for (const el of dw.querySelectorAll('*')) {
                const t = (el.innerText||'').trim();
                if (!t || t.length > 120) continue;
                if (el.children.length > 0) continue;
                out.push({
                  tag: el.tagName,
                  cls: (typeof el.className==='string'?el.className:'').slice(0,100),
                  text: t,
                });
              }
              return out;
            }
            """
        )
        (OUT / "phase2c_values_leaves.json").write_text(json.dumps(values, indent=2))
        print(f"\n[2c] leaves after CoV click: {len(values)}", flush=True)
        for v in values[:80]:
            print(f"  <{v['tag']}> .{v['cls'][:38]} → {v['text']}", flush=True)

        # Also get raw innerText of the DW, unfiltered
        dw_text = await page.evaluate("() => (document.querySelector('.chart-data-window')||{}).innerText || ''")
        (OUT / "phase2c_dw_text.txt").write_text(dw_text or "")
        print(f"\n[2c] DW full innerText ({len(dw_text)} chars):", flush=True)
        print(dw_text, flush=True)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
