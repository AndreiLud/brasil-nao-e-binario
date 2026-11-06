"""Screenshots of the site with Playwright (QA, README image and Open Graph image).

Usage:
    python -m src.screenshots qa      # full-page and per-section shots, phone and desktop
    python -m src.screenshots og      # docs/img/og.png (1200x630) and docs/img/hero.png
Serves docs/ on a local port while it runs.
"""
from __future__ import annotations

import contextlib
import http.server
import socketserver
import sys
import threading
from functools import partial
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from playwright.sync_api import sync_playwright

from src import config as C



@contextlib.contextmanager
def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    handler = partial(Quiet, directory=str(C.DOCS))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:  # any free port
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        try:
            yield f"http://127.0.0.1:{httpd.server_address[1]}/"
        finally:
            httpd.shutdown()


def scroll_through(page, step=500, wait=120):
    h = page.evaluate("document.body.scrollHeight")
    y = 0
    while y < h:
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(wait)
        y += step
        h = page.evaluate("document.body.scrollHeight")


def qa(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    with serve() as url, sync_playwright() as p:
        browser = p.chromium.launch()
        for name, vp, dpr in (("phone", {"width": 390, "height": 844}, 1), ("desktop", {"width": 1440, "height": 900}, 1)):
            page = browser.new_page(viewport=vp, device_scale_factor=dpr)
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.goto(url, wait_until="networkidle")
            scroll_through(page)
            page.wait_for_timeout(800)
            for sec in ("pergunta", "tres-eleicoes", "bolha", "em-2018", "em-2022", "em-2026", "sua-cidade", "metodo"):
                el = page.locator(f"#{sec}")
                el.scroll_into_view_if_needed()
                page.wait_for_timeout(500)
                el.screenshot(path=str(out / f"{name}-{sec}.png"))
            # map steps
            steps = page.locator("#scrolly .step")
            for i in range(steps.count()):
                steps.nth(i).scroll_into_view_if_needed()
                page.evaluate("window.scrollBy(0, -window.innerHeight*0.15)")
                page.wait_for_timeout(1400)
                page.screenshot(path=str(out / f"{name}-map-step{i}.png"))
            page.evaluate("window.scrollTo(0,0)")
            page.wait_for_timeout(300)
            page.screenshot(path=str(out / f"{name}-hero.png"))
            overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
            print(f"{name}: horizontal overflow {overflow}px; errors: {errors[:5]}")
            page.close()
        browser.close()


def og():
    """Render src/templates/og.html with facts into a temporary page, screenshot it, remove it."""
    from src.render import load_facts, render_text
    tmp = C.DOCS / "_og.html"
    tmp.write_text(render_text((C.TEMPLATES / "og.html").read_text(encoding="utf-8"), "pt", load_facts()), encoding="utf-8")
    try:
        with serve() as url, sync_playwright() as p:
            browser = p.chromium.launch()
            for name, vp in (("og.png", {"width": 1200, "height": 630}), ("hero.png", {"width": 1600, "height": 840})):
                page = browser.new_page(viewport=vp, device_scale_factor=1)
                page.goto(url + "_og.html", wait_until="networkidle")
                page.wait_for_selector("body[data-ready='1']", timeout=60000)
                page.wait_for_timeout(500)
                page.screenshot(path=str(C.DOCS / "img" / name))
                page.close()
            browser.close()
    finally:
        tmp.unlink(missing_ok=True)
    print("  wrote docs/img/og.png and docs/img/hero.png")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "qa"
    if what == "og":
        og()
    else:
        qa(Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/screens"))
