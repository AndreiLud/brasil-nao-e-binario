"""Browser smoke test of the site (Playwright, Chromium).

    python -m src.smoke

Checks both language versions (/ and /en/), at phone and desktop sizes: no JavaScript errors or failed requests while scrolling
the whole page; no horizontal overflow; the map caption follows rapid control clicks; a tap
on the map shows a tooltip (touch); the city search finds a municipality; the deep link
#cidade-<IBGE> opens the city view; the share button in the opening offers the networks and
copies the page address. Exits with status 1 on any failure.
"""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from playwright.sync_api import sync_playwright

from src.config import SITE_URL
from src.screenshots import scroll_through, serve


LANGS = {
    "pt": {"path": "", "clicks": ("2014", "1º", "2018", "Proporção", "2022", "2º", "Pontos", "2026", "Vencedor"),
           "caption": "2º turno de 2026", "nomatch": "Nenhum", "all": "Brasil inteiro",
           "copied": "Link copiado", "canon": SITE_URL},
    "en": {"path": "en/", "clicks": ("2014", "First", "2018", "Share", "2022", "Runoff", "Dots", "2026", "Winner"),
           "caption": "2026 runoff", "nomatch": "No municipality", "all": "All of Brazil",
           "copied": "Link copied", "canon": SITE_URL + "en/"},
}


def main() -> int:
    failures = []
    with serve() as root, sync_playwright() as p:
        browser = p.chromium.launch()
        runs = [(lang, vname, vopts) for lang in LANGS for vname, vopts in (
            ("phone", dict(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)),
            ("desktop", dict(viewport={"width": 1440, "height": 900})))]
        for lang, vname, opts in runs:
            L = LANGS[lang]
            url = root + L["path"]
            name = f"{lang}/{vname}"
            ctx = browser.new_context(**opts)
            ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin=root.rstrip("/"))
            page = ctx.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
            page.on("console", lambda m: errors.append(f"console: {m.text}") if m.type == "error" else None)
            page.on("requestfailed", lambda r: errors.append(f"requestfailed: {r.url}"))
            page.goto(url, wait_until="networkidle")

            # share button in the opening (headless Chromium has no native share sheet: the row of options opens)
            share = page.locator("#share-btn")
            if not share.is_visible():
                failures.append(f"{name}: share button not visible in the opening")
            else:
                share.click()
                page.wait_for_timeout(300)
                wa = page.locator('#share-menu [data-net="whatsapp"]')
                if not wa.is_visible() or quote(L["canon"], safe="") not in (wa.get_attribute("href") or ""):
                    failures.append(f"{name}: share options missing or not pointing to {L['canon']}")
                page.keyboard.press("Escape")
                page.wait_for_timeout(200)
                if wa.is_visible():
                    failures.append(f"{name}: Escape did not close the share options")
                share.click()
                page.locator('#share-menu [data-net="copy"]').click()
                page.wait_for_timeout(300)
                if L["copied"] not in share.inner_text():
                    failures.append(f"{name}: no confirmation after copying the link")
                if page.evaluate("navigator.clipboard.readText()") != L["canon"]:
                    failures.append(f"{name}: clipboard does not hold {L['canon']}")

            scroll_through(page, step=600, wait=100)
            page.wait_for_timeout(800)
            overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
            if overflow > 0:
                failures.append(f"{name}: horizontal overflow {overflow}px")

            # map controls: rapid clicks, final state must win
            page.locator("#map-controls").scroll_into_view_if_needed()
            page.wait_for_timeout(500)
            btn = lambda label: page.locator("#map-controls button", has_text=label).first
            for label in L["clicks"]:
                btn(label).click()
            page.wait_for_timeout(1500)
            cap = page.locator("#map-caption").inner_text()
            if L["caption"] not in cap:
                failures.append(f"{name}: caption after rapid clicks is {cap!r}")

            # tap / hover on the map shows a tooltip
            box = page.locator("#mainmap").bounding_box()
            x, y = box["x"] + box["width"] * 0.62, box["y"] + box["height"] * 0.52
            if vname == "phone":
                page.touchscreen.tap(x, y)
            else:
                page.mouse.move(x, y)
            page.wait_for_timeout(400)
            if not page.locator("#map-tip.on").count():
                failures.append(f"{name}: no tooltip after {'tap' if vname == 'phone' else 'hover'} on the map")

            # city search
            page.locator("#city-input").scroll_into_view_if_needed()
            page.locator("#city-input").fill("campinas")
            page.wait_for_timeout(300)
            page.keyboard.press("Enter")
            page.wait_for_timeout(800)
            if "Campinas" not in page.locator("#city-out").inner_text():
                failures.append(f"{name}: city search did not show Campinas")
            # going back to the national view: link under the city name, then the clear button, then a reload
            page.locator(".city-back").click()
            page.wait_for_timeout(600)
            if L["all"] not in page.locator("#city-out").inner_text() or "#cidade-" in page.url:
                failures.append(f"{name}: 'back to Brazil' did not reset the city view")
            page.locator("#city-input").fill("sobral")
            page.wait_for_timeout(300)
            page.keyboard.press("Enter")
            page.wait_for_timeout(800)
            page.locator(".city-clear").click()
            page.wait_for_timeout(600)
            if L["all"] not in page.locator("#city-out").inner_text() or "#cidade-" in page.url \
                    or page.locator("#city-input").input_value():
                failures.append(f"{name}: the clear button did not reset the city view")
            page.reload(wait_until="networkidle")
            page.locator("#city-input").scroll_into_view_if_needed()
            page.wait_for_timeout(1200)
            if L["all"] not in page.locator("#city-out").inner_text():
                failures.append(f"{name}: after clearing and reloading, a city is still shown")
            page.locator("#city-input").fill("xqzwvk")
            page.wait_for_timeout(300)
            if L["nomatch"] not in page.locator("#city-list").inner_text():
                failures.append(f"{name}: no feedback for a search without results")

            # deep link
            page.goto(url + "#cidade-3550308", wait_until="networkidle")
            page.wait_for_timeout(1500)
            if "São Paulo" not in page.locator("#city-out").inner_text():
                failures.append(f"{name}: deep link #cidade-3550308 did not open São Paulo")

            # language switch in the middle of the story keeps the reader in the same section
            page.goto(url, wait_until="networkidle")
            sec = page.locator("#em-2022")
            sec.scroll_into_view_if_needed()
            page.wait_for_timeout(600)
            page.mouse.wheel(0, -120)                 # scrolling up reveals the switch
            page.wait_for_timeout(500)
            other = page.locator(".lang-switch a[hreflang]")
            if not other.is_visible():
                failures.append(f"{name}: language switch not visible after scrolling up")
            else:
                other.click()
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(2500)
                want_en = lang == "pt"
                at_en = "/en/" in page.url
                top = page.evaluate("document.getElementById('em-2022').getBoundingClientRect().top")
                vh = page.evaluate("innerHeight")
                if at_en != want_en:
                    failures.append(f"{name}: switch went to {page.url}")
                if not (-page.evaluate("document.getElementById('em-2022').offsetHeight") < top < vh):
                    failures.append(f"{name}: after switching, section em-2022 is not in view (top={top:.0f})")
                if "s=" in page.url:
                    failures.append(f"{name}: position parameters left in the address bar")

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
