"""
Phase 3: reconnect with the user's layout (CoV pane maximised per user). Do NOT
change symbol. Probe EVERY legend (including hidden 0x0) + every pane container
to find which pane is now dominant and whether the CoV legend has real values.
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
        await page.wait_for_timeout(12_000)

        title = await page.title()
        print(f"[3] title: {title}", flush=True)
        await page.screenshot(path=str(OUT / "phase3_initial.png"), full_page=False)

        # Dump every legend (visible AND hidden), and every pane container.
        info = await page.evaluate(
            """
            () => {
              const legends = Array.from(document.querySelectorAll('[class*="legend-l31H9iuA"]'));
              const legData = legends.map(l => {
                const r = l.getBoundingClientRect();
                const sources = Array.from(l.querySelectorAll('[class*="sourcesWrapper"], [class*="source-"], [class*="item-l31H9iuA"]'));
                const valueCells = Array.from(l.querySelectorAll('[class*="valueItem"], [class*="valueTitle-l31H9iuA"], [class*="valueValue-l31H9iuA"]'));
                return {
                  rect: {x:r.x|0, y:r.y|0, w:r.width|0, h:r.height|0},
                  visible: r.width > 0 && r.height > 0,
                  text: (l.innerText||'').replace(/\\s+/g,' ').slice(0,400),
                  html: l.outerHTML.slice(0, 800),
                  sourceCount: sources.length,
                  valueCellCount: valueCells.length,
                };
              });

              // pane containers: TV uses .chart-container + inner pane wrappers
              const paneSel = '[class*="pane-"], [class*="paneWrapper"], [data-name="pane"], [class*="chart-gui-wrapper"]';
              const panes = Array.from(document.querySelectorAll(paneSel)).map(p => {
                const r = p.getBoundingClientRect();
                return {
                  tag: p.tagName,
                  cls: (typeof p.className==='string'?p.className:'').slice(0,120),
                  rect: {x:r.x|0, y:r.y|0, w:r.width|0, h:r.height|0},
                };
              }).filter(p => p.rect.w > 100 && p.rect.h > 30);

              return {legends: legData, panes};
            }
            """
        )
        (OUT / "phase3_probe.json").write_text(json.dumps(info, indent=2))
        print(f"\n[3] total legends: {len(info['legends'])}", flush=True)
        for i, l in enumerate(info["legends"]):
            r = l["rect"]
            flag = "VIS" if l["visible"] else "hid"
            print(f"  [{i}] {flag} ({r['x']},{r['y']} {r['w']}x{r['h']}) srcs={l['sourceCount']} vals={l['valueCellCount']}", flush=True)
            print(f"       text = {l['text'][:280]}", flush=True)

        print(f"\n[3] pane containers > 100x30: {len(info['panes'])}", flush=True)
        for i, p_ in enumerate(info["panes"][:20]):
            r = p_["rect"]
            print(f"  [{i}] <{p_['tag']}> .{p_['cls'][:45]} ({r['x']},{r['y']} {r['w']}x{r['h']})", flush=True)

        # Hover the approximate CoV pane center (likely bottom half if maximised).
        # Try a few rows to force legend updates.
        for y in (300, 540, 780, 900):
            await page.mouse.move(960, y)
            await page.wait_for_timeout(400)
            post = await page.evaluate(
                """
                () => Array.from(document.querySelectorAll('[class*="legend-l31H9iuA"]'))
                     .map(l => {
                       const r = l.getBoundingClientRect();
                       return {y:r.y|0, w:r.width|0, h:r.height|0,
                               text:(l.innerText||'').replace(/\\s+/g,' ').slice(0,280)};
                     })
                """
            )
            print(f"\n[3] after hover y={y}:", flush=True)
            for pp in post:
                print(f"  y={pp['y']} {pp['w']}x{pp['h']}: {pp['text']}", flush=True)

        await page.screenshot(path=str(OUT / "phase3_after_hover.png"), full_page=False)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
