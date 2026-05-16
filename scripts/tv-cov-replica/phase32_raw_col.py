"""
Phase 32: scrape EVERY pixel hover — don't dedupe. Extract raw CV Columns value
+ color at each x, so we can see exactly which bars fire columns and where.
"""
import asyncio, csv, json
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

PROBE = r"""
  () => {
    const legs = Array.from(document.querySelectorAll('[class*="legend-l31H9iuA"]'));
    const out = [];
    for (const l of legs) {
      const src = l.querySelector('[class*="mainTitle-"], [class*="title-l31H9iuA"]');
      const srcName = src ? src.innerText.trim() : '';
      const vals = {}, colors = {};
      for (const e of l.querySelectorAll('[class*="valueValue-l31H9iuA"]')) {
        const t = e.getAttribute('title') || '';
        if (!t) continue;
        vals[t]   = (e.innerText||'').trim().replace('\u2212','-');
        colors[t] = getComputedStyle(e).color;
      }
      out.push({ srcName, vals, colors });
    }
    return out;
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
        for sel in ['button:has-text("Don\'t allow")', 'button:has-text("Got it")']:
            try:
                b = page.locator(sel).first
                if await b.count() > 0: await b.click(); await page.wait_for_timeout(300)
            except: pass
        # Hover in middle pane (y=400 is roughly CoV pane)
        # Pane ranges (from phase30): CoV legend at y=281 → pane roughly 265-470
        #                             CoV* legend at y=645 → pane roughly 630-820
        await page.mouse.move(1000, 400)
        await page.wait_for_timeout(500)

        init = await page.evaluate(PROBE)
        def srcnorm(s): return s.replace("\n", " ").strip()
        orig_idx = next((i for i, l in enumerate(init) if srcnorm(l["srcName"]) == "CoV"), None)
        print(f"[32] orig_idx={orig_idx}")

        rows = []
        # Coarser stride to finish faster; focus in CoV pane
        for x in range(100, 1860, 3):
            await page.mouse.move(x, 400)
            await page.wait_for_timeout(60)
            legs = await page.evaluate(PROBE)
            if orig_idx is None or orig_idx >= len(legs): continue
            ov = legs[orig_idx]["vals"]
            oc = legs[orig_idx]["colors"]
            rows.append({
                "x": x,
                "o_cv":   ov.get("Coefficient of Variation Plot", ""),
                "o_cvma": ov.get("CV MA ", "") or ov.get("CV MA", ""),
                "o_cc":   ov.get("CC Direction Line", ""),
                "o_col":  ov.get("CV Columns", ""),
                "o_col_color": oc.get("CV Columns", ""),
            })

        # Look at unique column states
        states = {}
        for r in rows:
            key = (r["o_col"], r["o_col_color"])
            states.setdefault(key, []).append(r["x"])
        print(f"[32] total samples: {len(rows)}")
        print(f"[32] unique (col_value, col_color) states:")
        for (v, c), xs in sorted(states.items(), key=lambda kv: -len(kv[1])):
            print(f"  '{v}' | {c} → {len(xs)} samples (x range {min(xs)}..{max(xs)})")

        # Also filter and show rows where col is NOT ∅
        fires = [r for r in rows if r["o_col"] not in ("", "∅", "n/a")]
        print(f"\n[32] non-∅ firings: {len(fires)}")
        for r in fires[:30]:
            print(f"  x={r['x']:>4} o_cv={r['o_cv']:>6} o_cc={r['o_cc']:>7} col='{r['o_col']}' color={r['o_col_color']}")

        csv_path = OUT/"phase32_raw_col.csv"
        fields = ["x","o_cv","o_cvma","o_cc","o_col","o_col_color"]
        with csv_path.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            for r in rows: w.writerow(r)
        print(f"[32] wrote {csv_path}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
