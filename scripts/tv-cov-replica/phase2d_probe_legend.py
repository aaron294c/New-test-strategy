"""
Phase 2d: close Data Window, find the CoV pane legend, probe its
structure & current values, and verify values update when we move the
crosshair across bars.
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
    res = []
    for c in raw:
        pc = {
            "name": c["name"], "value": c["value"], "domain": c["domain"],
            "path": c.get("path", "/"), "secure": bool(c.get("secure", False)),
            "httpOnly": bool(c.get("httpOnly", False)),
            "sameSite": SAMESITE.get(c.get("sameSite"), "Lax"),
        }
        if "expirationDate" in c:
            pc["expires"] = int(c["expirationDate"])
        res.append(pc)
    return res


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
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        await ctx.add_cookies(load_cookies())
        page = await ctx.new_page()
        await page.goto(CHART_URL, wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(10_000)
        await set_symbol(page, "SPY")
        # ensure DW is closed (Alt+D toggles)
        # no reliable way to check — skip. It defaults closed on fresh load.

        await page.screenshot(path=str(OUT / "phase2d_before.png"))

        # Probe every VISIBLE legend on the page and its values
        panes = await page.evaluate(
            """
            () => {
              const legs = document.querySelectorAll('[class*="legend-l31H9iuA"]');
              const out = [];
              for (const l of legs) {
                const r = l.getBoundingClientRect();
                if (r.width === 0 || r.height === 0) continue;
                // try to find the study title
                const title = l.querySelector('[class*="title-l31H9iuA"], [class*="titleWrapper"], [class*="source__title"], [class*="item-l31H9iuA"]');
                const values  = Array.from(l.querySelectorAll('[class*="valuesWrapper-l31H9iuA"], [class*="valuesAdditionalWrapper-l31H9iuA"]'));
                const parts = values.flatMap(v =>
                  Array.from(v.querySelectorAll('*')).filter(e => e.children.length === 0)
                    .map(e => ({
                      cls: (typeof e.className==='string'?e.className:'').slice(0,80),
                      title: e.getAttribute('title') || '',
                      text: (e.innerText||'').trim(),
                      color: (e.style && e.style.color) || '',
                    }))
                    .filter(x => x.text.length > 0 && x.text.length < 30)
                );
                out.push({
                  rect: {x: r.x|0, y: r.y|0, w: r.width|0, h: r.height|0},
                  titleText: title ? (title.innerText||'').trim().slice(0,200) : '',
                  text: (l.innerText||'').slice(0,400).replace(/\\s+/g,' '),
                  valueCount: parts.length,
                  values: parts.slice(0, 40),
                });
              }
              return out;
            }
            """
        )
        (OUT / "phase2d_panes.json").write_text(json.dumps(panes, indent=2))
        print(f"[2d] visible legends: {len(panes)}", flush=True)
        for i, p_ in enumerate(panes):
            r = p_["rect"]
            print(f"\n  [{i}] pane rect=({r['x']},{r['y']} {r['w']}x{r['h']}) title={p_['titleText'][:80]!r}", flush=True)
            print(f"      text = {p_['text'][:240]}", flush=True)
            print(f"      values ({p_['valueCount']}):", flush=True)
            for v in p_["values"][:15]:
                print(f"        {v['text']!r:20} title={v['title']!r} color={v['color']!r} cls={v['cls'][:35]}", flush=True)

        # Take a shot to visually confirm pane positions
        # Hover the chart center to populate values (simulate crosshair on last bar)
        await page.mouse.move(950, 540)
        await page.wait_for_timeout(500)
        await page.screenshot(path=str(OUT / "phase2d_hover_center.png"))

        # After hover, re-probe legend values
        post = await page.evaluate(
            """
            () => {
              const legs = document.querySelectorAll('[class*="legend-l31H9iuA"]');
              const out = [];
              for (const l of legs) {
                const r = l.getBoundingClientRect();
                if (r.width === 0 || r.height === 0) continue;
                out.push({
                  y: r.y|0,
                  text: (l.innerText||'').replace(/\\s+/g,' ').slice(0,350)
                });
              }
              return out;
            }
            """
        )
        print("\n[2d] after hover at (950,540):", flush=True)
        for p_ in post:
            print(f"  y={p_['y']}: {p_['text'][:260]}", flush=True)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
