"""
Phase 2b: switch chart to SPY daily, open Data Window, dump full structure
(text + per-row decomposition) so we know exactly how to read the CoV values.
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


async def set_symbol(page, symbol: str):
    # TV opens the symbol dialog on any keypress while chart is focused
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
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
        )
        await context.add_cookies(load_cookies())
        page = await context.new_page()
        await page.goto(CHART_URL, wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(10_000)

        # Ensure daily TF (press shortcut: D then Enter)
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(200)

        # Switch to SPY
        print("[2b] switching to SPY…", flush=True)
        await set_symbol(page, "SPY")

        # Open Data Window
        await page.keyboard.press("Alt+D")
        await page.wait_for_timeout(2_500)
        await page.screenshot(path=str(OUT / "phase2b_spy.png"))

        title = await page.title()
        print(f"[2b] title: {title}", flush=True)

        # Grab Data Window full HTML + text tree
        dw = await page.evaluate(
            """
            () => {
              const dw = document.querySelector('.chart-data-window');
              if (!dw) return null;
              // walk each direct child, decompose into (source label, rows[])
              const sections = [];
              for (const child of dw.children) {
                const label = child.querySelector('[class*="sourceTitle"], [class*="source__title"], [class*="title-"]');
                const rows  = child.querySelectorAll('[class*="values-"], [class*="row-"], [class*="item-"]');
                sections.push({
                  outerClass: (typeof child.className==='string'?child.className:'').slice(0,140),
                  label: label ? (label.innerText||'').trim() : null,
                  text:  (child.innerText||'').slice(0,1200).replace(/\\s+/g,' '),
                  rowCount: rows.length,
                });
              }
              return {
                rect: dw.getBoundingClientRect(),
                sectionsCount: dw.children.length,
                sections,
                fullText: (dw.innerText||'').replace(/\\s+/g,' ').slice(0,4000),
              };
            }
            """
        )
        (OUT / "phase2b_datawindow.json").write_text(json.dumps(dw, indent=2, default=str))
        if dw is None:
            print("[2b] NO .chart-data-window found!", flush=True)
            await browser.close()
            return
        print(f"[2b] DW sections: {dw['sectionsCount']}", flush=True)
        print(f"[2b] DW full text: {dw['fullText'][:1500]}", flush=True)
        print("", flush=True)
        for i, s in enumerate(dw["sections"]):
            print(f"  [{i}] rows={s['rowCount']} class={s['outerClass'][:60]}", flush=True)
            print(f"      label={s['label']!r}", flush=True)
            print(f"      text={s['text'][:300]}", flush=True)

        # Also dump every descendant with a numeric-looking text (value cells)
        values = await page.evaluate(
            """
            () => {
              const dw = document.querySelector('.chart-data-window');
              if (!dw) return [];
              const out = [];
              for (const el of dw.querySelectorAll('*')) {
                const t = (el.innerText||'').trim();
                if (!t || t.length > 80) continue;
                if (el.children.length > 0) continue; // leaf only
                out.push({
                  tag: el.tagName,
                  cls: (typeof el.className==='string'?el.className:'').slice(0,120),
                  text: t,
                });
              }
              return out;
            }
            """
        )
        (OUT / "phase2b_values_leaves.json").write_text(json.dumps(values, indent=2))
        print(f"\n[2b] leaf nodes: {len(values)} (first 60):", flush=True)
        for v in values[:60]:
            print(f"  <{v['tag']}> .{v['cls'][:40]} → {v['text']}", flush=True)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
