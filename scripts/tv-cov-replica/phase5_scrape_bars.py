"""
Phase 5: hover the crosshair across ~80 x positions to build a per-bar sample
of CV / CV MA / Correlation values. Also scrape the date shown at the chart's
bottom x-axis during each hover so we can align to bars.
"""
import asyncio
import csv
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
    const legs = Array.from(document.querySelectorAll('[class*="legend-l31H9iuA"]'))
                      .filter(l => l.getBoundingClientRect().width > 0);
    const wanted = ['CV Columns','CV Border','Coefficient of Variation Plot',
                    'CV MA Border','CV MA ','Correlation','CC Direction Line Border','CC Direction Line'];
    const vals = {};
    for (const l of legs) {
      for (const e of l.querySelectorAll('[class*="valueValue-l31H9iuA"]')) {
        const t = e.getAttribute('title') || '';
        if (!t) continue;
        vals[t] = (e.innerText||'').trim().replace('−','-');
      }
    }
    // scrape x-axis crosshair date tooltip (the small bubble near bottom)
    let xlabel = '';
    const dl = document.querySelector('[class*="dateMarker"], [class*="crosshair"], [class*="priceAxisStub"]');
    // Fallback: look for any element with text like "Wed 27 Aug '25"
    const re = /\\b(Sun|Mon|Tue|Wed|Thu|Fri|Sat)\\s+\\d{1,2}\\s+[A-Z][a-z]{2}\\s+'\\d{2}\\b/;
    for (const el of document.querySelectorAll('div,span')) {
      const t = (el.innerText||'').trim();
      if (re.test(t) && t.length < 30) { xlabel = t; break; }
    }
    return {vals, xlabel};
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

        try:
            btn = page.locator('button:has-text("Don\'t allow")').first
            if await btn.count() > 0:
                await btn.click()
                await page.wait_for_timeout(500)
        except Exception:
            pass

        # Sample across x: chart area ~60 → 1440 on 1920 wide screen
        xs = list(range(120, 1440, 18))  # ~73 samples
        rows = []
        for x in xs:
            await page.mouse.move(x, 450)
            await page.wait_for_timeout(120)
            r = await page.evaluate(PROBE)
            v = r["vals"]
            rows.append({
                "x": x,
                "date": r.get("xlabel", ""),
                "cv_plot": v.get("Coefficient of Variation Plot", ""),
                "cv_border": v.get("CV Border", ""),
                "cv_cols": v.get("CV Columns", ""),
                "cv_ma": v.get("CV MA ", "") or v.get("CV MA", ""),
                "cv_ma_border": v.get("CV MA Border", ""),
                "corr": v.get("Correlation", ""),
                "cc_dir": v.get("CC Direction Line", ""),
                "cc_dir_border": v.get("CC Direction Line Border", ""),
            })

        csv_path = OUT / "phase5_bars.csv"
        with csv_path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"[5] wrote {len(rows)} rows to {csv_path}", flush=True)
        # Print a summary
        for r in rows[::6]:
            print(f"  x={r['x']:4}  date={r['date']:20}  cv={r['cv_plot']:>8} cv_ma={r['cv_ma']:>8} corr={r['corr']:>8}", flush=True)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
