"""Parse the official TSE totals used to validate our aggregation.

Sources (all in data/raw/tse/official):
  2026  results-portal JSON (BR, 27 UFs, abroad), both rounds, and the
        totalization report PDF (second source, compared with the JSON)
  2022  totalization report PDF (BR, 27 UFs, abroad), both rounds
  2018  totalization report PDF (BR, 27 UFs, abroad), both rounds
  2014  no independent official source could be reached; the section-level vote
        file (same TSE database, finer grain) is aggregated as a second path

Output: a long table (year, round, source, scope, item, value) where scope is
'BR', a UF code or 'ZZ' (abroad) and item is one of aptos, comparecimento,
abstencoes, validos, brancos, nulos, anulados_apurados_separado or cand_<number>.
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config as C

OFFICIAL = C.RAW / "tse" / "official"
UF_NAMES = {"ACRE": "AC", "ALAGOAS": "AL", "AMAZONAS": "AM", "AMAPÁ": "AP", "BAHIA": "BA", "CEARÁ": "CE",
            "DISTRITO FEDERAL": "DF", "ESPÍRITO SANTO": "ES", "GOIÁS": "GO", "MARANHÃO": "MA",
            "MINAS GERAIS": "MG", "MATO GROSSO DO SUL": "MS", "MATO GROSSO": "MT", "PARÁ": "PA",
            "PARAÍBA": "PB", "PERNAMBUCO": "PE", "PIAUÍ": "PI", "PARANÁ": "PR", "RIO DE JANEIRO": "RJ",
            "RIO GRANDE DO NORTE": "RN", "RONDÔNIA": "RO", "RORAIMA": "RR", "RIO GRANDE DO SUL": "RS",
            "SANTA CATARINA": "SC", "SERGIPE": "SE", "SÃO PAULO": "SP", "TOCANTINS": "TO", "EXTERIOR": "ZZ"}


def _num(s: str) -> int:
    return int(s.replace(".", ""))


def _rows(year, rnd, source, scope, d):
    out = []
    for k, v in d.items():
        if k == "cand":
            out += [(year, rnd, source, scope, f"cand_{int(n)}", int(x)) for n, x in v.items()]
        elif v is not None:
            out.append((year, rnd, source, scope, k, int(v)))
    return out


def portal_2026() -> list[tuple]:
    rows = []
    for rnd in (1, 2):
        ele = C.ELECTION_CODES[(2026, rnd)]
        for f in sorted((OFFICIAL / "portal2026").glob(f"*-c0001-e{ele:06d}-u.json")):
            j = json.loads(f.read_text(encoding="utf-8"))
            scope = j["cdabr"].upper()
            e, v = j["e"], j["v"]
            cand = {k["n"]: int(k["vap"]) for c in j["carg"] for a in c["agr"] for p in a["par"] for k in p["cand"]}
            rows += _rows(2026, rnd, "portal_json", scope, {
                "aptos": e["te"], "comparecimento": e["c"], "abstencoes": e["a"], "validos": v["vv"],
                "brancos": v["vb"], "nulos": v["tvn"], "cand": cand})
    return rows


def _pdf_text(zip_path: Path, member_regex: str, layout: bool) -> dict[str, str]:
    out = {}
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            m = re.search(member_regex, name)
            if not m:
                continue
            reader = PdfReader(io.BytesIO(z.read(name)))
            pages = [p.extract_text(extraction_mode="layout") if layout else p.extract_text() for p in reader.pages]
            out[m.group(1)] = "\n----- page\n".join(pages)
    return out


def report_2022_2026(year: int) -> list[tuple]:
    """Parse the 2022/2026 report layout ('Resumo Geral (UF)' blocks)."""
    rows = []
    texts = _pdf_text(OFFICIAL / f"Relatorio_Resultado_Totalizacao_{year}_BR.zip", r"_T(\d)_PRESIDENTE\.pdf$", False)
    for rnd_s, txt in texts.items():
        lines = [l.strip() for l in txt.split("\n")]
        cur, data = None, {}
        for i, line in enumerate(lines):
            m = re.match(r"Resumo Geral \((.+)\)$", line)
            if m:
                cur = UF_NAMES[m.group(1)]
            elif line == "Resumo Geral do Brasil":
                cur = "BR"
            if cur is None:
                continue
            d = data.setdefault(cur, {"cand": {}})
            if (m := re.match(r"2\.2 Eleitorado apto a votar ([\d.]+)$", line)):
                d["aptos"] = _num(m.group(1))
            if (m := re.match(r"2\.3 Comparecimento ([\d.]+)$", line)):
                d["comparecimento"] = _num(m.group(1))
            if (m := re.match(r"2\.4 Abstenção\s+[\d,]+% ([\d.]+)$", line)):
                d["abstencoes"] = _num(m.group(1))
            if line.startswith("2.5.1 Total de votos"):
                nums, j = [], i + 1
                while len(nums) < 4 and j < i + 12:
                    if re.fullmatch(r"[\d.]+", lines[j]):
                        nums.append(_num(lines[j]))
                    j += 1
                d["votos_total"], d["validos"], d["brancos"], d["nulos"] = nums
            if (m := re.match(r"^([\d.]+) [\d,]+%.*?(\d+) - (.+?) Válido", line)):
                d["cand"][m.group(2)] = _num(m.group(1))
        for scope, d in data.items():
            d.pop("votos_total", None)
            rows += _rows(year, int(rnd_s), "report_pdf", scope, d)
    return rows


def report_2018() -> list[tuple]:
    """Parse the 2018 report layout (one 'Resultado de votação' page per UF)."""
    rows = []
    texts = _pdf_text(OFFICIAL / "Relatorio_Resultado_Totalizacao_2018_BR.zip", r"_T(\d)_PRESIDENTE\.pdf$", True)
    labels = [("validos", "Votos válidos"), ("brancos", "Votos em branco"), ("nulos", "Votos nulos"),
              ("anulados_apurados_separado", "Votos anulados e apurados em separado"),
              ("comparecimento", "Comparecimento"), ("abstencoes", "Abstenção")]
    for rnd_s, txt in texts.items():
        data, pending = {}, None
        for page in txt.split("----- page"):
            lines = [re.sub(r"\s+", " ", l).strip() for l in page.split("\n")]
            if any(l.startswith("Resumo Geral") for l in lines):
                pending = next((_num(m.group(1)) for l in lines
                                if (m := re.match(r"2\.2\. Eleitorado apto a votar ([\d.]+)$", l))), None)
                continue
            uf = next((m.group(1) for l in lines if (m := re.match(r"UF: ([A-Z]{2}) - (.+)$", l))), None)
            if uf is None:
                continue
            uf = uf.upper()
            d = data.setdefault(uf, {"cand": {}})
            if pending is not None:
                d["aptos"], pending = pending, None
            for l in lines:
                m = re.match(r"^\*?(\d+) - .+? ([\d.]+) (2º turno|Não eleito|Eleito|Não Eleito|Renúncia|"
                             r"Indeferido.*?|Cassado.*?) [\d,]+ [\d,]+$", l)
                if m:
                    d["cand"][m.group(1)] = _num(m.group(2))
                for key, lab in labels:
                    if (m := re.match(re.escape(lab) + r": ([\d.]+)", l)):
                        d[key] = _num(m.group(1))
        for scope, d in data.items():
            rows += _rows(2018, int(rnd_s), "report_pdf", scope, d)
    return rows


def sections_2014() -> list[tuple]:
    """Aggregate the 2014 section-level presidential votes by UF (second aggregation path).

    NR_VOTAVEL 95 = blank, 96 = null. The file is ~1 GB uncompressed, so it is streamed.
    """
    agg = defaultdict(int)
    with zipfile.ZipFile(OFFICIAL / "votacao_secao_2014_BR.zip") as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        with z.open(name) as raw:
            reader = csv.reader(io.TextIOWrapper(raw, encoding="latin-1", newline=""), delimiter=";")
            hdr = next(reader)
            ix = {h: i for i, h in enumerate(hdr)}
            it, iu, iv, iq = ix["NR_TURNO"], ix["SG_UF"], ix["NR_VOTAVEL"], ix["QT_VOTOS"]
            for r in reader:
                agg[(int(r[it]), r[iu], int(r[iv]))] += int(r[iq])
    rows = []
    for (rnd, uf, nr), v in agg.items():
        item = "brancos" if nr == 95 else "nulos" if nr == 96 else f"cand_{nr}"
        rows.append((2014, rnd, "sections_2014", uf, item, v))
    df = pd.DataFrame(rows, columns=["year", "round", "source", "scope", "item", "value"])
    br = df.groupby(["year", "round", "source", "item"], as_index=False)["value"].sum().assign(scope="BR")
    df = pd.concat([df, br])
    val = (df[df["item"].str.startswith("cand_")].groupby(["year", "round", "source", "scope"], as_index=False)["value"]
           .sum().assign(item="validos"))
    df = pd.concat([df, val])
    return list(df[["year", "round", "source", "scope", "item", "value"]].itertuples(index=False, name=None))


def load_all() -> pd.DataFrame:
    rows = portal_2026() + report_2022_2026(2026) + report_2022_2026(2022) + report_2018() + sections_2014()
    df = pd.DataFrame(rows, columns=["year", "round", "source", "scope", "item", "value"])
    df = df.groupby(["year", "round", "source", "scope", "item"], as_index=False)["value"].sum()
    return df


if __name__ == "__main__":
    out = load_all()
    print(out.groupby(["year", "round", "source"]).size())
