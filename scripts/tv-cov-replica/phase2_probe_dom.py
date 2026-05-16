"""
Phase 2: probe the Data Window + legend DOM to find stable selectors for
per-bar plot values of the CoV indicator.
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


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
        )
        await context.add_cookies(load_cookies())
        page = await context.new_page()
        print(f"[phase2] goto {CHART_URL}", flush=True)
        await page.goto(CHART_URL, wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(10_000)

        # open Data Window (TV keyboard shortcut: Alt+D)
        await page.keyboard.press("Alt+D")
        await page.wait_for_timeout(2_500)
        await page.screenshot(path=str(OUT / "phase2_after_alt_d.png"))
        print("[phase2] screenshot after Alt+D", flush=True)

        # probe 1: any element whose class contains Data-Window-ish keywords
        probe = await page.evaluate(
            """
            () => {
              const needles = ['data-window','dataWindow','legend','values','source__title','source-selector','seriesTitle'];
              const out = [];
              function walk(el, d=0){
                if (!el || d>25) return;
                const cls = typeof el.className === 'string' ? el.className : '';
                const id  = el.id || '';
                if (needles.some(n => (cls+id).toLowerCase().includes(n.toLowerCase()))) {
                  out.push({
                    tag: el.tagName,
                    id,
                    cls: cls.slice(0,180),
                    text: (el.innerText||'').slice(0,220).replace(/\\s+/g,' '),
                    w: el.getBoundingClientRect().width|0,
                    h: el.getBoundingClientRect().height|0,
                  });
                }
                for (const c of el.children||[]) walk(c, d+1);
              }
              walk(document.body);
              // de-dup by (cls,text)
              const seen = new Set(); const uniq = [];
              for (const m of out){ const k = m.cls+'|'+m.text; if(seen.has(k))continue; seen.add(k); uniq.push(m); }
              return uniq.slice(0,60);
            }
            """
        )
        (OUT / "phase2_probe.json").write_text(json.dumps(probe, indent=2))
        print(f"[phase2] probe hits: {len(probe)}", flush=True)
        for m in probe[:40]:
            print(f"  <{m['tag']}> .{m['cls'][:55]} [{m['w']}x{m['h']}] → {m['text'][:160]}", flush=True)

        # probe 2: elements mentioning CV / Correlation / Volatility of returns
        legend = await page.evaluate(
            """
            () => {
              const out = [];
              for (const el of document.querySelectorAll('*')) {
                const t = el.innerText || '';
                if (t.length < 3 || t.length > 600) continue;
                if (/\\bCV\\b|Correlation|Volatility of returns|CC Direction|R Squared|Coefficient of Variation/.test(t)) {
                  out.push({
                    tag: el.tagName,
                    cls: (typeof el.className==='string'?el.className:'').slice(0,140),
                    text: t.slice(0,300).replace(/\\s+/g,' '),
                  });
                }
              }
              const seen = new Set(); const uniq = [];
              for (const m of out){ if (seen.has(m.text)) continue; seen.add(m.text); uniq.push(m); }
              return uniq.slice(0,25);
            }
            """
        )
        (OUT / "phase2_legend.json").write_text(json.dumps(legend, indent=2))
        print(f"\n[phase2] legend hits: {len(legend)}", flush=True)
        for l in legend[:20]:
            print(f"  <{l['tag']}> .{l['cls'][:45]} → {l['text'][:200]}", flush=True)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
