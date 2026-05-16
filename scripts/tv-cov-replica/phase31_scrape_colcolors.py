"""
Phase 31: scrape CV Columns value + color per bar from the original CoV pane.
Goal: reverse-engineer the EXACT condition that fires green/red/na columns.
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

# Probe returns, for each indicator legend (original + replica), the "CV Columns"
# value text AND its computed text color, plus main pane OHLC, plus o_cv/o_cc.
PROBE = r"""
  () => {
    const legs = Array.from(document.querySelectorAll('[class*="legend-l31H9iuA"]'));
    const out = [];
    for (const l of legs) {
      const src = l.querySelector('[class*="mainTitle-"], [class*="title-l31H9iuA"]');
      const srcName = src ? src.innerText.trim() : '';
      // Indicator-style values (have title attribute)
      const vals = {};
      const colors = {};
      for (const e of l.querySelectorAll('[class*="valueValue-l31H9iuA"]')) {
        const t = e.getAttribute('title') || '';
        if (!t) continue;
        vals[t]   = (e.innerText||'').trim().replace('\u2212','-');
        colors[t] = getComputedStyle(e).color;
      }
      // Main pane OHLC via valueItem pairs
      const ohlc = {};
      for (const it of l.querySelectorAll('[class*="valueItem-l31H9iuA"]')) {
        const tEl = it.querySelector('[class*="valueTitle-l31H9iuA"]');
        const vEl = it.querySelector('[class*="valueValue-l31H9iuA"]');
        const t = tEl ? (tEl.innerText||'').trim() : '';
        const v = vEl ? (vEl.innerText||'').trim().replace('\u2212','-') : '';
        if (t && v && !(t in ohlc)) ohlc[t] = v;
      }
      out.push({ srcName, vals, colors, ohlc });
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
        for sel in ['button:has-text("Don\'t allow")', 'button:has-text("Got it")', 'button:has-text("Close")']:
            try:
                b = page.locator(sel).first
                if await b.count() > 0: await b.click(); await page.wait_for_timeout(300)
            except: pass
        await page.mouse.move(1000, 450)
        await page.wait_for_timeout(500)

        init = await page.evaluate(PROBE)
        def srcnorm(s): return s.replace("\n", " ").strip()
        main_idx = next((i for i, l in enumerate(init) if "C" in l.get("ohlc",{}) or "Close" in l.get("ohlc",{})), None)
        orig_idx = next((i for i, l in enumerate(init) if srcnorm(l["srcName"]) == "CoV"), None)
        rep_idx  = next((i for i, l in enumerate(init) if "CoV*" in srcnorm(l["srcName"])), None)
        print(f"[31] main={main_idx} orig={orig_idx} rep={rep_idx}")
        for i, l in enumerate(init):
            print(f"  #{i} '{srcnorm(l['srcName'])}' keys={list(l['vals'].keys())}")
            for k, c in l.get("colors", {}).items():
                print(f"     {k!r}: color={c}")

        raw = []
        for x in range(80, 1860, 1):
            await page.mouse.move(x, 450)
            await page.wait_for_timeout(90)
            legs = await page.evaluate(PROBE)
            row = {"x": x}
            if main_idx is not None and main_idx < len(legs):
                mv = legs[main_idx].get("ohlc", {})
                row["close"] = mv.get("C", "") or mv.get("Close", "")
            if orig_idx is not None and orig_idx < len(legs):
                ov = legs[orig_idx]["vals"]
                oc = legs[orig_idx]["colors"]
                row["o_cv"]   = ov.get("Coefficient of Variation Plot", "")
                row["o_cvma"] = ov.get("CV MA ", "") or ov.get("CV MA", "")
                row["o_cc"]   = ov.get("CC Direction Line", "")
                row["o_col"]  = ov.get("CV Columns", "")
                row["o_col_color"] = oc.get("CV Columns", "")
                row["o_cc_color"]  = oc.get("CC Direction Line", "")
            raw.append(row)

        bars = []; last = None
        for r in raw:
            key = (r.get("o_cv",""), r.get("o_cc",""), r.get("close",""))
            if not r.get("o_cv"): continue
            if key != last:
                bars.append(r); last = key
        print(f"[31] raw={len(raw)}, deduped={len(bars)}")

        csv_path = OUT/"phase31_colors.csv"
        fields = ["x","close","o_cv","o_cvma","o_cc","o_col","o_col_color","o_cc_color"]
        with csv_path.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            for b in bars: w.writerow({k: b.get(k, "") for k in fields})
        print(f"[31] wrote {csv_path}")

        print("\n[31] sample last 15 bars (column value + color):")
        for b in bars[-15:]:
            print(f"  x={b['x']:>4} close={b.get('close',''):>7} o_cv={b.get('o_cv',''):>6} o_cc={b.get('o_cc',''):>7} | col='{b.get('o_col','')}' col_color={b.get('o_col_color','')}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
