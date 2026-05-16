"""
Phase 6: hover crosshair across many x positions, at each one scrape the
crosshair date (anywhere in the DOM) + the CoV legend values. Probe the DOM
broadly for the date bubble since it has no stable class we've seen yet.
"""
import asyncio, csv, json, re
from pathlib import Path
from playwright.async_api import async_playwright

COOKIE_FILE = Path("/tmp/tv_cookies.json")
CHART_URL   = "https://www.tradingview.com/chart/XgNLLOpn/"
OUT         = Path("/tmp/tv-cov-out"); OUT.mkdir(exist_ok=True)
SAMESITE    = {"no_restriction": "None", "lax": "Lax", "strict": "Strict", None: "Lax"}

def load_cookies():
    raw = json.loads(COOKIE_FILE.read_text())
    res = []
    for c in raw:
        pc = {"name": c["name"], "value": c["value"], "domain": c["domain"],
              "path": c.get("path", "/"), "secure": bool(c.get("secure", False)),
              "httpOnly": bool(c.get("httpOnly", False)),
              "sameSite": SAMESITE.get(c.get("sameSite"), "Lax")}
        if "expirationDate" in c:
            pc["expires"] = int(c["expirationDate"])
        res.append(pc)
    return res


# Probe: pull CoV legend values + any text node matching a date pattern
PROBE = r"""
  () => {
    const legs = Array.from(document.querySelectorAll('[class*="legend-l31H9iuA"]'))
      .filter(l => l.getBoundingClientRect().width > 0);
    const vals = {};
    for (const l of legs) {
      for (const e of l.querySelectorAll('[class*="valueValue-l31H9iuA"]')) {
        const t = e.getAttribute('title') || '';
        if (!t) continue;
        vals[t] = (e.innerText || '').trim().replace('\u2212', '-');
      }
    }
    // Crosshair date/time bubble: search broad, capture anything date-like
    const dateRe = /^\s*(?:(?:Sun|Mon|Tue|Wed|Thu|Fri|Sat)\s+)?\d{1,2}\s+[A-Z][a-z]{2}\s+'?\d{2,4}\s*$/;
    const priceRe = /^-?\d+(\.\d+)?$/;
    const candidates = [];
    for (const el of document.querySelectorAll('div,span,td')) {
      if (el.children.length) continue;
      const t = (el.innerText || '').trim();
      if (!t || t.length > 30) continue;
      if (dateRe.test(t)) candidates.push({kind: 'date', text: t,
          cls: (typeof el.className==='string'?el.className:'').slice(0,60)});
    }
    return {vals, candidates: candidates.slice(0, 30)};
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
        await page.wait_for_timeout(20_000)
        await page.screenshot(path=str(OUT / "phase6_loaded.png"))
        print(f"[6] title: {await page.title()}", flush=True)

        try:
            btn = page.locator('button:has-text("Don\'t allow")').first
            if await btn.count() > 0:
                await btn.click(); await page.wait_for_timeout(400)
        except Exception:
            pass

        # First, find any date-shaped element and discover its class
        await page.mouse.move(800, 450)
        await page.wait_for_timeout(1500)
        initial = await page.evaluate(PROBE)
        print(f"[6] initial vals: {initial['vals']}", flush=True)
        print(f"[6] initial date candidates: {len(initial['candidates'])}", flush=True)
        for c in initial["candidates"][:10]:
            print(f"    kind={c['kind']}  text={c['text']!r}  cls={c['cls']!r}", flush=True)

        # Main sweep: 120..1440 every 12 px (≈110 samples) — denser than phase5
        xs = list(range(120, 1440, 12))
        rows = []
        last_date = ""
        for x in xs:
            await page.mouse.move(x, 450)
            await page.wait_for_timeout(140)
            r = await page.evaluate(PROBE)
            v = r["vals"]
            dates = [c["text"] for c in r["candidates"]]
            date = dates[0] if dates else ""
            if not date:
                date = last_date
            else:
                last_date = date
            rows.append({
                "x": x, "date": date,
                "cv_plot": v.get("Coefficient of Variation Plot", ""),
                "cv_ma":   v.get("CV MA ", "") or v.get("CV MA", ""),
                "corr":    v.get("Correlation", ""),
                "cc_dir":  v.get("CC Direction Line", ""),
            })

        csv_path = OUT / "phase6_dated.csv"
        with csv_path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        print(f"[6] wrote {len(rows)} rows → {csv_path}", flush=True)
        # print a thin slice
        for r in rows[::10]:
            print(f"  x={r['x']:4} date={r['date']:18} cv={r['cv_plot']:>8} cv_ma={r['cv_ma']:>8} corr={r['corr']:>8}", flush=True)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
