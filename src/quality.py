"""Quality log: every check and cleaning decision made by the pipeline.

Each check stores the observed value and, when there is one, the expected value.
The log is written to project_docs/quality_log.md (human readable) and
data/processed/quality_checks.csv (machine readable). A failed check stops the
pipeline unless it is explicitly marked as explained.
"""
from __future__ import annotations

import csv
import datetime as dt
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config as C


class QualityLog:
    def __init__(self):
        self.items: list[dict] = []
        self.current = "General"

    def section(self, title: str):
        self.current = title
        self.items.append({"kind": "section", "section": title})

    def check(self, name: str, observed, expected=None, explained: str | None = None):
        ok = expected is None or observed == expected
        self.items.append({"kind": "check", "section": self.current, "name": name, "observed": observed,
                           "expected": expected, "ok": ok, "explained": explained})
        flag = "ok" if ok else ("EXPLAINED" if explained else "FAIL")
        print(f"  [{flag}] {name}: {observed}" + ("" if expected is None else f" (expected {expected})"))
        return ok

    def note(self, text: str):
        self.items.append({"kind": "note", "section": self.current, "text": text})
        print(f"  note: {text}")

    def table(self, title: str, header: list[str], rows: list[list]):
        self.items.append({"kind": "table", "section": self.current, "title": title, "header": header, "rows": rows})

    @property
    def failures(self):
        return [i for i in self.items if i["kind"] == "check" and not i["ok"] and not i["explained"]]

    def flush(self):
        C.PROJECT_DOCS.mkdir(parents=True, exist_ok=True)
        C.PROCESSED.mkdir(parents=True, exist_ok=True)
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        md = ["# Quality log", "",
              f"Written by the pipeline (`python run_all.py`) on {stamp}. Do not edit by hand.", "",
              "Status legend: **ok** = observed equals expected (or informational); "
              "**explained** = differs from expected for a documented reason; **FAIL** = unexplained.", ""]
        for it in self.items:
            if it["kind"] == "section":
                md += ["", f"## {it['section']}", ""]
            elif it["kind"] == "check":
                status = "ok" if it["ok"] else ("explained" if it["explained"] else "**FAIL**")
                exp = "" if it["expected"] is None else f" (expected {_fmt(it['expected'])})"
                line = f"* {status}: {it['name']}: {_fmt(it['observed'])}{exp}"
                if it["explained"]:
                    line += f". Why: {it['explained']}"
                md.append(line)
            elif it["kind"] == "note":
                md.append(f"* note: {it['text']}")
            elif it["kind"] == "table":
                md += ["", f"**{it['title']}**", "", "| " + " | ".join(it["header"]) + " |",
                       "|" + "---|" * len(it["header"])]
                md += ["| " + " | ".join(_fmt(c) for c in r) + " |" for r in it["rows"]]
                md.append("")
        (C.PROJECT_DOCS / "quality_log.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        with open(C.PROCESSED / "quality_checks.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["section", "check", "observed", "expected", "status", "explanation"])
            for it in self.items:
                if it["kind"] == "check":
                    status = "ok" if it["ok"] else ("explained" if it["explained"] else "FAIL")
                    w.writerow([it["section"], it["name"], it["observed"], it["expected"], status, it["explained"] or ""])


def _fmt(v):
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, int):
        return f"{v:,}"
    if isinstance(v, float):
        return f"{v:,.4f}"
    return str(v)
