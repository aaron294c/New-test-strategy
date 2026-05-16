"""
Phase 1: log into TradingView with exported cookies, navigate to the CoV chart,
screenshot, and verify authentication.
"""
import asyncio
import json
import os
from pathlib import Path

from playwright.async_api import async_playwright

COOKIE_FILE = Path("/tmp/tv_cookies.json")
CHART_URL = "https://www.tradingview.com/chart/XgNLLOpn/"
OUT_DIR = Path("/tmp/tv-cov-out")
OUT_DIR.mkdir(exist_ok=True)

SAMESITE = {"no_restriction": "None", "lax": "Lax", "strict": "Strict", None: "Lax"}


def load_cookies():
    raw = json.loads(COOKIE_FILE.read_text())
    out = []
    for c in raw:
        pc = {
            "name": c["name"],
            "value": c["value"],
            "domain": c["domain"],
            "path": c.get("path", "/"),
            "secure": bool(c.get("secure", False)),
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
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
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

        print(f"[phase1] navigating → {CHART_URL}")
        await page.goto(CHART_URL, wait_until="domcontentloaded", timeout=60_000)
        # chart needs time to render
        await page.wait_for_timeout(8_000)

        # save screenshot + page title
        shot = OUT_DIR / "phase1_chart.png"
        await page.screenshot(path=str(shot), full_page=False)
        title = await page.title()
        url = page.url
        print(f"[phase1] title: {title}")
        print(f"[phase1] url:   {url}")
        print(f"[phase1] shot:  {shot} ({shot.stat().st_size} bytes)")

        # try to detect logged-in username via top-right avatar / data
        try:
            user_data = await page.evaluate(
                "() => (window.TradingView && window.TradingView.currentUser && "
                "window.TradingView.currentUser()) || null"
            )
            print(f"[phase1] currentUser(): {user_data}")
        except Exception as e:
            print(f"[phase1] currentUser() lookup failed: {e}")

        # html sanity check — look for our username in the page source
        html = await page.content()
        authed = "aaron294c" in html
        has_chart_canvas = "chart-container" in html or "chart-markup-table" in html
        print(f"[phase1] aaron294c in html: {authed}")
        print(f"[phase1] chart markup present: {has_chart_canvas}")

        await browser.close()
        return authed


if __name__ == "__main__":
    ok = asyncio.run(main())
    print(f"[phase1] AUTH_OK={ok}")
