"""
Phase 27: rescrape — capture Close prices from main-pane legend alongside
CoV panes. Gives perfect per-bar alignment (o_cv, o_cc, close) for formula fitting.
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
    return legs.map(l => {
      const src = l.querySelector('[class*="mainTitle-"], [class*="title-l31H9iuA"]');
      const vals = {};
      // Indicator panes: valueValue has title attribute
      for (const e of l.querySelectorAll('[class*="valueValue-l31H9iuA"]')) {
        const t = e.getAttribute('title') || '';
        if (t) vals[t] = (e.innerText||'').trim().replace('\u2212','-');
      }
      // Main pane: walk valueItem containers; title is in sibling valueTitle
      const items = Array.from(l.querySelectorAll('[class*="valueItem-l31H9iuA"]'));
      const ohlc = {};
      for (const it of items) {
        const tEl = it.querySelector('[class*="valueTitle-l31H9iuA"]');
        const vEl = it.querySelector('[class*="valueValue-l31H9iuA"]');
        const t = tEl ? (tEl.innerText||'').trim() : '';
        const v = vEl ? (vEl.innerText||'').trim().replace('\u2212','-') : '';
        if (t && v && !(t in ohlc)) ohlc[t] = v;
      }
      return { srcName: src ? src.innerText.trim() : '', vals, ohlc };
    });
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

        # Hover once so main-pane OHLC values populate
        await page.mouse.move(1000, 450)
        await page.wait_for_timeout(500)
        init = await page.evaluate(PROBE)
        def srcnorm(s): return s.replace("\n", " ").strip()
        main_idx = None
        for i, l in enumerate(init):
            ohlc = l.get("ohlc", {})
            if "C" in ohlc or "Close" in ohlc:
                main_idx = i; break
        orig_idx = next((i for i, l in enumerate(init) if srcnorm(l["srcName"]) == "CoV"), None)
        rep_idx  = next((i for i, l in enumerate(init) if "CoV*" in srcnorm(l["srcName"]) or "Replica" in srcnorm(l["srcName"])), None)
        print(f"[27] main_idx={main_idx} orig_idx={orig_idx} rep_idx={rep_idx}")
        for i, l in enumerate(init):
            print(f"  init[#{i}] src='{srcnorm(l['srcName'])}' indicator_keys={list(l['vals'].keys())[:5]} ohlc={l.get('ohlc', {})}")

        raw = []
        for x in range(80, 1860, 1):
            await page.mouse.move(x, 450)
            await page.wait_for_timeout(90)
            legs = await page.evaluate(PROBE)
            row = {"x": x}
            if main_idx is not None and main_idx < len(legs):
                mv = legs[main_idx].get("ohlc", {})
                row["close"] = mv.get("C", "") or mv.get("Close", "")
                row["open"]  = mv.get("O", "") or mv.get("Open", "")
                row["high"]  = mv.get("H", "") or mv.get("High", "")
                row["low"]   = mv.get("L", "") or mv.get("Low", "")
            if orig_idx is not None and orig_idx < len(legs):
                ov = legs[orig_idx]["vals"]
                row["o_cv"]   = ov.get("Coefficient of Variation Plot", "")
                row["o_cvma"] = ov.get("CV MA ", "") or ov.get("CV MA", "")
                row["o_cc"]   = ov.get("CC Direction Line", "")
            if rep_idx is not None and rep_idx < len(legs):
                rv = legs[rep_idx]["vals"]
                row["r_cv"]   = rv.get("Coefficient of Variation Plot", "")
                row["r_cc"]   = rv.get("CC Direction Line", "")
            raw.append(row)

        bars = []; last = None
        for r in raw:
            key = (r.get("o_cv",""), r.get("o_cc",""), r.get("close",""))
            if not r.get("o_cv"): continue
            if key != last:
                bars.append(r); last = key
        print(f"[27] raw={len(raw)}, deduped={len(bars)}")

        csv_path = OUT/"phase27_with_close.csv"
        fields = ["x","close","open","high","low","o_cv","o_cvma","o_cc","r_cv","r_cc"]
        with csv_path.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            for b in bars: w.writerow({k: b.get(k, "") for k in fields})
        print(f"[27] wrote {csv_path}")
        print("\nLast 10 bars:")
        for b in bars[-10:]:
            print(f"  x={b['x']:>4} close={b.get('close',''):>8} o_cv={b.get('o_cv',''):>7} o_cc={b.get('o_cc',''):>8}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
