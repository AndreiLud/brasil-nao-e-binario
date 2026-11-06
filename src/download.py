"""Download every raw input into data/raw and record it in data/raw/manifest.json.

Large TSE zips (400-660 MB) hold every office; only the presidential member is
needed, so it is extracted with HTTP Range requests (the zip central directory is
read first, then only the bytes of that member). If the server ever stops
honouring Range requests, the whole zip is downloaded instead.

Files that already exist are kept (use --force to refresh). Every file gets a
sha256 in the manifest so a later run can tell whether the TSE regenerated it.
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import io
import json
import shutil
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config as C

UA = {"User-Agent": "brasil-nao-e-binario-pipeline/1.0"}
MANIFEST = C.RAW / "manifest.json"


def _open(url: str, headers: dict | None = None, method: str = "GET", timeout: int = 180):
    h = dict(UA)
    h.update(headers or {})
    req = urllib.request.Request(url, headers=h, method=method)
    last = None
    for attempt in range(5):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:  # transient
            if isinstance(exc, urllib.error.HTTPError) and exc.code in (400, 403, 404):
                raise
            last = exc
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError(f"failed after retries: {url}: {last}")


class RangeFile(io.RawIOBase):
    """Seekable read-only file backed by HTTP Range requests."""

    def __init__(self, url: str):
        self.url, self.pos = url, 0
        with _open(url, {"Range": "bytes=0-0"}) as r:
            if r.status != 206:
                raise OSError("server ignored Range request")
            self.size = int(r.headers["Content-Range"].split("/")[-1])
            self.last_modified = r.headers.get("Last-Modified")

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos

    def readinto(self, b):
        n = min(len(b), self.size - self.pos)
        if n <= 0:
            return 0
        with _open(self.url, {"Range": f"bytes={self.pos}-{self.pos + n - 1}"}) as r:
            data = r.read()
        b[: len(data)] = data
        self.pos += len(data)
        return len(data)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}


def record(manifest: dict, path: Path, url: str, member: str | None, last_modified: str | None):
    manifest[str(path.relative_to(C.ROOT))] = {
        "url": url,
        "zip_member": member,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "server_last_modified": last_modified,
        "retrieved_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))


def fetch(url: str, dest: Path, manifest: dict, force: bool = False):
    if dest.exists() and not force:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with _open(url, timeout=600) as r, open(tmp, "wb") as f:
        lm = r.headers.get("Last-Modified")
        # Some IBGE endpoints gzip the body even when not asked to.
        src = gzip.GzipFile(fileobj=r) if r.headers.get("Content-Encoding") == "gzip" else r
        shutil.copyfileobj(src, f, 1 << 20)
    tmp.rename(dest)
    record(manifest, dest, url, None, lm)
    print(f"  downloaded {dest.relative_to(C.ROOT)} ({dest.stat().st_size:,} bytes)")


def fetch_member(url: str, member: str, dest: Path, manifest: dict, force: bool = False):
    if dest.exists() and not force:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        rf = RangeFile(url)
        zf = zipfile.ZipFile(io.BufferedReader(rf, buffer_size=1 << 20))
        lm = rf.last_modified
    except OSError:
        whole = dest.parent / Path(url).name
        fetch(url, whole, manifest, force)
        zf = zipfile.ZipFile(whole)
        lm = manifest[str(whole.relative_to(C.ROOT))]["server_last_modified"]
    with zf.open(member) as src, open(dest, "wb") as out:
        shutil.copyfileobj(src, out, 1 << 20)
    record(manifest, dest, url, member, lm)
    print(f"  extracted {member} -> {dest.relative_to(C.ROOT)} ({dest.stat().st_size:,} bytes)")


def main(force: bool = False):
    m = load_manifest()
    tse = C.RAW / "tse"
    print("TSE presidential votes and turnout by municipality and zone")
    for y in C.YEARS:
        url, member = C.TSE_VOTES[y]
        fetch_member(url, member, tse / member, m, force)
        url, member = C.TSE_DETAIL[y]
        fetch_member(url, member, tse / member, m, force)
    print("TSE <-> IBGE crosswalk")
    fetch(C.TSE_IBGE_CROSSWALK, tse / "municipio_tse_ibge.zip", m, force)
    fetch(C.BD_MUNICIPIO, C.RAW / "basedosdados" / "municipio.csv.gz", m, force)
    print("Official totals for validation")
    for y, url in C.TSE_TOTALIZATION_REPORT.items():
        fetch(url, tse / "official" / Path(url).name, m, force)
    for rnd, ele in ((1, C.ELECTION_CODES[(2026, 1)]), (2, C.ELECTION_CODES[(2026, 2)])):
        for abr in ["br", "zz"] + [u.lower() for u in C.UFS]:
            url = C.TSE_PORTAL_2026.format(ele=ele, abr=abr)
            fetch(url, tse / "official" / "portal2026" / Path(url).name, m, force)
    fetch(C.TSE_SECTION_2014, tse / "official" / "votacao_secao_2014_BR.zip", m, force)
    print("IBGE")
    ibge = C.RAW / "ibge"
    fetch(C.IBGE_LOCALIDADES, ibge / "localidades_municipios.json", m, force)
    fetch(C.SIDRA_POP_2022, ibge / "sidra_4709_pop_2022.json", m, force)
    fetch(C.SIDRA_POP_EST_2025, ibge / "sidra_6579_pop_est_2025.json", m, force)
    fetch(C.SIDRA_INCOME_2022, ibge / "sidra_10295_income_2022.json", m, force)
    fetch(C.IBGE_MESH_2025, ibge / "BR_Municipios_2025.zip", m, force)
    print("Downloads complete.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="re-download existing files")
    main(ap.parse_args().force)
