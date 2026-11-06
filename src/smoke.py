"""Browser smoke test of the site (Playwright, Chromium).

    python -m src.smoke

Checks, at phone and desktop sizes: no JavaScript errors or failed requests while scrolling
the whole page; no horizontal overflow; the map caption follows rapid control clicks; a tap
on the map shows a tooltip (touch); the city search finds a municipality; the deep link
#cidade-<IBGE> opens the city view. Exits with status 1 on any failure.
"""
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from playwright.sync_api import sync_playwright

from src.screenshots import scroll_through, serve


def main() -> int:
    failures = []
    with serve() as url, sync_playwright() as p:
        browser = p.chromium.launch()
        for name, opts in (("phone", dict(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)),
                           ("desktop", dict(viewport={"width": 1440, "height": 900}))):
            ctx = browser.new_context(**opts)
            page = ctx.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
            page.on("console", lambda m: errors.append(f"console: {m.text}") if m.type == "error" else None)
            page.on("requestfailed", lambda r: errors.append(f"requestfailed: {r.url}"))
            page.goto(url, wait_until="networkidle")
            scroll_through(page, step=600, wait=100)
            page.wait_for_timeout(800)
            overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
            if overflow > 0:
                failures.append(f"{name}: horizontal overflow {overflow}px")

            # map controls: rapid clicks, final state must win
            page.locator("#map-controls").scroll_into_view_if_needed()
            page.wait_for_timeout(500)
            btn = lambda label: page.locator("#map-controls button", has_text=label).first
            for label in ("2014", "1º", "2018", "Proporção", "2022", "2º", "Pontos", "2026", "Vencedor"):
                btn(label).click()
            page.wait_for_timeout(1500)
            cap = page.locator("#map-caption").inner_text()
            if "2º turno de 2026" not in cap:
                failures.append(f"{name}: caption after rapid clicks is {cap!r}")

            # tap / hover on the map shows a tooltip
            box = page.locator("#mainmap").bounding_box()
            x, y = box["x"] + box["width"] * 0.62, box["y"] + box["height"] * 0.52
            if name == "phone":
                page.touchscreen.tap(x, y)
            else:
                page.mouse.move(x, y)
            page.wait_for_timeout(400)
            if not page.locator("#map-tip.on").count():
                failures.append(f"{name}: no tooltip after {'tap' if name == 'phone' else 'hover'} on the map")

            # city search
            page.locator("#city-input").scroll_into_view_if_needed()
            page.locator("#city-input").fill("campinas")
            page.wait_for_timeout(300)
            page.keyboard.press("Enter")
            page.wait_for_timeout(800)
            if "Campinas" not in page.locator("#city-out").inner_text():
                failures.append(f"{name}: city search did not show Campinas")
            page.locator("#city-input").fill("xqzwvk")
            page.wait_for_timeout(300)
            if "Nenhum" not in page.locator("#city-list").inner_text():
                failures.append(f"{name}: no feedback for a search without results")

            # deep link
            page.goto(url + "#cidade-3550308", wait_until="networkidle")
            page.wait_for_timeout(1500)
            if "São Paulo" not in page.locator("#city-out").inner_text():
                failures.append(f"{name}: deep link #cidade-3550308 did not open São Paulo")

            failures += [f"{name}: {e}" for e in errors]
            print(f"{name}: done, {len(errors)} JS/network errors")
            ctx.close()
        browser.close()
    for f in failures:
        print("FAIL", f)
    print("smoke test:", "OK" if not failures else f"{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
