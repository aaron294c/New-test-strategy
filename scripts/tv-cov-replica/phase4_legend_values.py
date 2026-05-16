"""
Phase 4: dismiss cookie banner, dump the CoV legend's .valueTitle / .valueValue
spans directly (innerText returns only 'CoV' — the real per-plot values are in
those sub-spans and/or data-* attrs). Hover crosshair across several x positions
and re-scrape to confirm live updates.
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


PROBE = """
  () => {
    const legs = Array.from(document.querySelectorAll('[class*="legend-l31H9iuA"]'));
    const out = [];
    for (const l of legs) {
      const r = l.getBoundingClientRect();
      // Enumerate every descendant with a non-empty non-nested text
      const leaves = Array.from(l.querySelectorAll('*'))
        .filter(e => e.children.length === 0 && (e.innerText||'').trim().length > 0)
        .map(e => ({
          cls:  (typeof e.className==='string'?e.className:'').slice(0,80),
          text: (e.innerText||'').trim().slice(0,60),
          title: e.getAttribute('title') || e.getAttribute('data-name') || '',
          color: (e.style && e.style.color) || '',
        }));
      out.push({
        visible: r.width>0 && r.height>0,
        rect: {x:r.x|0, y:r.y|0, w:r.width|0, h:r.height|0},
        legendText: (l.innerText||'').replace(/\\s+/g,' ').slice(0,120),
        leaves,
      });
    }
    // Also try to scrape the right-axis price labels (last-value markers).
    const axisLabels = Array.from(document.querySelectorAll('[class*="priceAxisStub"], [class*="priceAxis"], canvas'))
      .map(c => ({
        tag: c.tagName,
        cls: (typeof c.className==='string'?c.className:'').slice(0,80),
        w: c.getBoundingClientRect().width|0,
        h: c.getBoundingClientRect().height|0,
      })).filter(c => c.w > 0);
    return {legends: out, axisLabels: axisLabels.slice(0, 20)};
  }
"""


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

        # Dismiss cookie banner if present
        try:
            btn = page.locator('button:has-text("Don\'t allow"), button:has-text("Accept all")').first
            if await btn.count() > 0:
                await btn.click()
                await page.wait_for_timeout(800)
                print("[4] cookie banner dismissed", flush=True)
        except Exception as e:
            print(f"[4] no cookie banner: {e}", flush=True)

        # Baseline probe (no hover)
        base = await page.evaluate(PROBE)
        (OUT / "phase4_baseline.json").write_text(json.dumps(base, indent=2))
        print(f"\n[4] baseline legends: {len(base['legends'])}", flush=True)
        for i, l in enumerate(base["legends"]):
            if not l["visible"]:
                continue
            print(f"  [{i}] VISIBLE {l['rect']}  text={l['legendText']!r}", flush=True)
            for leaf in l["leaves"][:25]:
                print(f"      {leaf['text']!r:18} title={leaf['title']!r:30} color={leaf['color']!r:12} cls={leaf['cls'][:30]}", flush=True)

        # Hover crosshair at several positions along the chart
        for i, x in enumerate([200, 500, 800, 1100, 1400]):
            await page.mouse.move(x, 500)
            await page.wait_for_timeout(450)
            probe = await page.evaluate(PROBE)
            for l in probe["legends"]:
                if not l["visible"]:
                    continue
                leafs = [lf for lf in l["leaves"] if lf["text"]]
                flat = " | ".join(f"{lf['text']}" for lf in leafs[:30])
                print(f"\n[4] hover x={x}: {flat[:300]}", flush=True)
            # also dump raw
            (OUT / f"phase4_hover_x{x}.json").write_text(json.dumps(probe, indent=2))

        await page.screenshot(path=str(OUT / "phase4_final.png"))
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
