"""Download the site's third-party assets (pinned versions) into docs/vendor and docs/fonts.

Nothing is loaded from a CDN at runtime. Each file's sha256 is written to
docs/vendor/MANIFEST.json; a later run fails if a pinned file changes upstream.
"""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config as C

JSD = "https://cdn.jsdelivr.net/npm"
# d3 modules concatenated in dependency order into one UMD bundle (smaller than d3.min.js).
D3_MODULES = [("d3-array", "3.2.4"), ("d3-color", "3.1.0"), ("d3-interpolate", "3.0.1"), ("d3-dispatch", "3.0.1"),
              ("d3-timer", "3.0.1"), ("d3-ease", "3.0.1"), ("d3-selection", "3.0.0"), ("d3-transition", "3.0.1"),
              ("d3-format", "3.1.2"), ("d3-time", "3.1.0"), ("d3-time-format", "4.1.0"), ("d3-scale", "4.0.2"),
              ("d3-path", "3.1.0"), ("d3-shape", "3.2.0"), ("d3-geo", "3.1.1"), ("d3-quadtree", "3.0.1")]
FILES = {
    "vendor/topojson-client.min.js": f"{JSD}/topojson-client@3.1.0/dist/topojson-client.min.js",
    "vendor/scrollama.min.js": f"{JSD}/scrollama@3.2.0/build/scrollama.min.js",
    "vendor/LICENSE-d3.txt": f"{JSD}/d3@7.9.0/LICENSE",
    "vendor/LICENSE-topojson-client.txt": f"{JSD}/topojson-client@3.1.0/LICENSE",
    "vendor/LICENSE-scrollama.txt": f"{JSD}/scrollama@3.2.0/LICENSE",
    "fonts/fraunces-latin-opsz-normal.woff2": f"{JSD}/@fontsource-variable/fraunces@5.3.0/files/fraunces-latin-opsz-normal.woff2",
    "fonts/fraunces-latin-opsz-italic.woff2": f"{JSD}/@fontsource-variable/fraunces@5.3.0/files/fraunces-latin-opsz-italic.woff2",
    "fonts/inter-latin-wght-normal.woff2": f"{JSD}/@fontsource-variable/inter@5.3.0/files/inter-latin-wght-normal.woff2",
    "fonts/LICENSE-Fraunces-OFL.txt": f"{JSD}/@fontsource-variable/fraunces@5.3.0/LICENSE",
    "fonts/LICENSE-Inter-OFL.txt": f"{JSD}/@fontsource-variable/inter@5.3.0/LICENSE",
}


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "brasil-nao-e-binario-pipeline/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def main():
    man_path = C.DOCS / "vendor" / "MANIFEST.json"
    old = json.loads(man_path.read_text()) if man_path.exists() else {}
    man = {}
    # d3 custom bundle
    parts = []
    for name, ver in D3_MODULES:
        url = f"{JSD}/{name}@{ver}/dist/{name}.min.js"
        body = get(url)
        parts.append(f"// {name}@{ver} ({url})\n".encode() + body.strip() + b"\n")
        man[f"{name}@{ver}"] = {"url": url, "sha256": hashlib.sha256(body).hexdigest()}
    bundle = b"// d3 modules, ISC License, Copyright 2010-2023 Mike Bostock (see LICENSE-d3.txt)\n" + b"".join(parts)
    out = C.DOCS / "vendor" / "d3-custom.min.js"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bundle)
    for rel, url in FILES.items():
        body = get(url)
        p = C.DOCS / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body)
        man[rel] = {"url": url, "sha256": hashlib.sha256(body).hexdigest()}
    changed = [k for k in man if k in old and old[k]["sha256"] != man[k]["sha256"]]
    if changed:
        raise SystemExit(f"pinned assets changed upstream: {changed}")
    man_path.write_text(json.dumps(man, indent=1))
    print(f"  vendored {len(man)} files; d3 bundle {len(bundle):,} bytes")


if __name__ == "__main__":
    main()
