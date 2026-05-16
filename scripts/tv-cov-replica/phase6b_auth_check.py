"""Quick auth/chart-access probe."""
import asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright

COOKIE_FILE = Path("/tmp/tv_cookies.json")
OUT = Path("/tmp/tv-cov-out"); OUT.mkdir(exist_ok=True)
SAMESITE = {"no_restriction": "None", "lax": "Lax", "strict": "Strict", None: "Lax"}

def load_cookies():
    raw = json.loads(COOKIE_FILE.read_text())
    res = []
    for c in raw:
        pc = {"name": c["name"], "value": c["value"], "domain": c["domain"],
              "path": c.get("path", "/"), "secure": bool(c.get("secure", False)),
              "httpOnly": bool(c.get("httpOnly", False)),
              "sameSite": SAMESITE.get(c.get("sameSite"), "Lax")}
        if "expirationDate" in c: pc["expires"] = int(c["expirationDate"])
        res.append(pc)
    return res

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox","--disable-dev-shm-usage"])
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080})
        await ctx.add_cookies(load_cookies())
        page = await ctx.new_page()

        for url in ["https://www.tradingview.com/",
                    "https://www.tradingview.com/chart/",
                    "https://www.tradingview.com/chart/XgNLLOpn/"]:
            await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            await page.wait_for_timeout(6000)
            t = await page.title()
            u = page.url
            print(f"{url}\n  → title: {t}\n  → final: {u}\n", flush=True)

        # Check auth state explicitly
        auth = await page.evaluate("""
          () => {
            const u = document.querySelector('[class*="username"], [class*="tv-header__user-menu"]');
            const m = document.body.innerText.match(/aaron\\d+\\w*/i);
            return {hasUserMenu: !!u, match: m ? m[0] : null};
          }""")
        print(f"auth probe: {auth}", flush=True)
        await page.screenshot(path=str(OUT / "phase6b_final.png"))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
