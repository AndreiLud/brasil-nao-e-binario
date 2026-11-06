"""Render the site page, the READMEs and the notebook text from templates + facts.json.

Templates use {{fact_key}}. Every number in the prose therefore comes from
docs/data/facts.json, which the pipeline computes. After rendering, three checks run:
  1. no placeholder is left and every key exists;
  2. no em dash, en dash or spaced hyphen is used as punctuation in the prose;
  3. every number that appears in the visible text of the page and the READMEs is
     either a rendered fact or in a short list of fixed values (years, dates, the
     30%/40% thresholds that define the measures, "100 pessoas", map scale labels).
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config as C

PLACEHOLDER = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")
# Numbers allowed in prose without being facts: election years, election dates, the
# thresholds that define a measure, the size/income band limits and the "100 people" unit.
ALLOWED_NUMBERS = {
    # election years and dates
    "2013", "2014", "2018", "2022", "2023", "2025", "2026", "1º", "2º", "4", "25", "4/10", "25/10",
    # small ordinals and list numbers
    "0", "1", "2", "3", "5", "6", "7", "8", "9", "10",
    # thresholds and band limits that define a measure (not results)
    "0%", "10%", "20%", "30%", "40%", "50%", "60%", "70%", "80%", "90%", "100%", "20", "40", "60", "80",
    "100", "50", "200", "1.000", "10.000", "50.000", "100.000", "200.000", "1 milhão", "1.000.000",
    "1,000", "10,000", "50,000", "100,000", "200,000", "1 million", "1,000,000",
    # identifiers: SIDRA tables, IBGE code of the new municipality, report item, map box, image size
    "4709", "10295", "5101837", "2.2.2", "1000", "1200", "630",
    # software versions in the READMEs
    "1.5.6", "2.0", "3.12", "7.9.0", "3.1.0", "3.2.0", "5.3.0",
}


def load_facts():
    facts = json.loads((C.SITE_DATA / "facts.json").read_text(encoding="utf-8"))
    # configuration values usable in templates (not numbers)
    for key, val in (("cfg_site_url", C.SITE_URL), ("cfg_repo_url", C.REPO_URL)):
        facts[key] = {"value": val, "kind": "text", "pt": val, "en": val, "desc": "configuration"}
    return facts


def render_text(tpl: str, lang: str, facts: dict) -> str:
    def sub(m):
        key = m.group(1)
        if key not in facts:
            raise KeyError(f"unknown fact in template: {key}")
        return facts[key][lang]
    return PLACEHOLDER.sub(sub, tpl)


def visible_text(page: str) -> str:
    page = re.sub(r"<(script|style)\b.*?</\1>", " ", page, flags=re.S | re.I)
    page = re.sub(r"<!--.*?-->", " ", page, flags=re.S)
    page = re.sub(r"<[^>]+>", " ", page)
    return html.unescape(page)


def markdown_prose(md: str) -> str:
    md = re.sub(r"```.*?```", " ", md, flags=re.S)       # code blocks
    md = re.sub(r"`[^`]*`", " ", md)                     # inline code
    md = re.sub(r"\]\([^)]*\)", "]", md)                 # link targets
    md = re.sub(r"!\[[^\]]*\]", " ", md)                 # image alt
    md = re.sub(r"https?://\S+", " ", md)
    return md


def dash_problems(text: str) -> list[str]:
    bad = []
    for pat, label in (("—", "em dash"), ("–", "en dash"), (" - ", "spaced hyphen")):
        for m in re.finditer(re.escape(pat), text):
            bad.append(f"{label}: …{text[max(0, m.start() - 40):m.end() + 40]}…".replace("\n", " "))
    # hyphen used as a list marker in prose
    for m in re.finditer(r"(?m)^\s*-\s", text):
        bad.append(f"hyphen bullet: …{text[m.start():m.start() + 60]}…".replace("\n", " "))
    return bad


NUM = re.compile(r"(?<![A-Za-z_\d])[−+]?\d[\d.,]*(?:\s?(?:milhões|milhão|million|mil|thousand|pontos|points|%))?")


def number_problems(text: str, facts: dict, lang: str) -> list[str]:
    allowed = set(ALLOWED_NUMBERS)
    for f in facts.values():
        allowed.add(f[lang])
        for tok in NUM.findall(f[lang]):
            allowed.add(tok.strip())
    bad = []
    for m in NUM.finditer(text):
        tok = m.group(0).strip().rstrip(".,")
        if tok in allowed or tok.rstrip("%") in allowed:
            continue
        core = re.match(r"[−+]?\d[\d.,]*", tok).group(0).rstrip(".,")
        if core in allowed:
            continue
        bad.append(f"{tok!r} in …{text[max(0, m.start() - 50):m.end() + 30]}…".replace("\n", " "))
    return bad


def render_file(src: Path, dst: Path, lang: str, facts: dict, kind: str) -> list[str]:
    tpl = src.read_text(encoding="utf-8")
    out = render_text(tpl, lang, facts)
    if PLACEHOLDER.search(out):
        raise ValueError(f"unrendered placeholder in {dst}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(out, encoding="utf-8")
    prose = visible_text(out) if kind == "html" else markdown_prose(out)
    problems = [f"{dst.name}: {p}" for p in dash_problems(prose)]
    problems += [f"{dst.name}: number not in facts: {p}" for p in number_problems(prose, facts, lang)]
    return problems


def main(strict: bool = True):
    facts = load_facts()
    jobs = [
        (C.TEMPLATES / "index.html", C.DOCS / "index.html", "pt", "html"),
        (C.TEMPLATES / "README.md", C.ROOT / "README.md", "en", "md"),
        (C.TEMPLATES / "README.pt-BR.md", C.ROOT / "README.pt-BR.md", "pt", "md"),
        (C.TEMPLATES / "methodology.md", C.PROJECT_DOCS / "methodology.md", "en", "md"),
    ]
    problems = []
    for src, dst, lang, kind in jobs:
        if not src.exists():
            print(f"  skip {src.relative_to(C.ROOT)} (no template)")
            continue
        problems += render_file(src, dst, lang, facts, kind)
        print(f"  rendered {dst.relative_to(C.ROOT)}")
    if problems:
        print("  Text problems found:")
        for p in problems:
            print("   ", p)
        if strict:
            raise SystemExit("render: fix the templates (see problems above)")
    return problems


if __name__ == "__main__":
    main(strict="--lenient" not in sys.argv)
