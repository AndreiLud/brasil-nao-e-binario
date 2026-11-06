"""Validate our aggregation against the official TSE totals, cell by cell.

For every election and round, every scope (Brazil, each UF, abroad) and every item
(electorate, turnout, abstention, valid, blank and null votes, each candidate),
the difference between our sums and the official figure must be zero. Any
difference is written to data/processed/validation_diffs.csv and must either be
explained (documented below and in the quality log) or the pipeline stops.
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config as C
from src import official_totals
from src.quality import QualityLog

# Differences that are understood: (year, round, scope, item) -> (expected difference, explanation).
# A difference is accepted only if it is exactly the expected one.
KNOWN = {}
_SEP = ("The municipal turnout file counts voters of sections that were not counted ('seções não "
        "apuradas', item 2.2.2 of the totalization report) as abstention; the report keeps them apart, "
        "so its abstention is lower by exactly that number. Votes and turnout are identical.")
for scope, diff in (("ES", 334), ("PR", 335), ("BR", 669)):
    KNOWN[(2018, 2, scope, "abstencoes")] = (diff, _SEP)


def run(con: duckdb.DuckDBPyConnection, log: QualityLog) -> pd.DataFrame:
    log.section("Validation against official TSE totals")
    con.execute((C.SQL_DIR / "v01_validation_totals.sql").read_text())
    ours = con.sql("SELECT * FROM our_totals").df()
    official = official_totals.load_all()
    official.to_csv(C.PROCESSED / "official_totals.csv", index=False)

    cz = con.sql("SELECT year, round, count(*) AS n, count(*) FILTER (WHERE diff <> 0) AS bad "
                 "FROM consistency_zone GROUP BY ALL ORDER BY ALL").df()
    for r in cz.itertuples():
        log.check(f"{r.year} round {r.round}: municipality-zone rows where candidate votes differ from "
                  f"valid votes in the turnout table (of {r.n:,})", int(r.bad), expected=0)

    full = official.merge(ours, on=["year", "round", "scope", "item"], how="outer", suffixes=("_official", "_ours"),
                          indicator=True)
    # Cells only on our side: items the official source does not publish (e.g. 2014 electorate,
    # since only votes exist at section level). Listed, not silently dropped.
    ours_only = full[full["_merge"] == "right_only"]
    for (y, r), g in ours_only.groupby(["year", "round"]):
        srcs = official[(official.year == y) & (official["round"] == r)]["source"].unique()
        log.note(f"{y} round {r}: items with no official counterpart ({', '.join(srcs)}): "
                 f"{', '.join(sorted(g['item'].unique()))}")
    missing_ours = full[full["_merge"] == "left_only"]
    log.check("Official cells with no counterpart in our aggregation", len(missing_ours), expected=0)
    merged = full[full["_merge"] != "right_only"].copy()
    merged["value_ours"] = merged["value_ours"].fillna(0).astype("int64")
    merged["diff"] = merged["value_ours"] - merged["value_official"]
    diffs = merged[merged["diff"] != 0].copy()

    def explain(r):
        exp = KNOWN.get((r.year, r.round, r.scope, r.item))
        return exp[1] if exp and exp[0] == r.diff else ""
    diffs["explanation"] = [explain(r) for r in diffs.itertuples()]
    diffs.to_csv(C.PROCESSED / "validation_diffs.csv", index=False)

    summary = []
    for (year, rnd, source), g in merged.groupby(["year", "round", "source"]):
        d = diffs[(diffs["year"] == year) & (diffs["round"] == rnd) & (diffs["source"] == source)]
        unexplained = d[d["explanation"] == ""]
        scopes = g["scope"].nunique()
        expl = "; ".join(sorted({f"{r.scope} {r.item} {r.diff:+,}" for r in d.itertuples() if r.explanation}))
        log.check(f"{year} round {rnd} vs {source}: cells compared {len(g):,} across {scopes} scopes; "
                  f"cells with a difference", len(d), expected=0,
                  explained=(f"{expl}. {KNOWN.get((year, rnd, 'BR', 'abstencoes'), (0, ''))[1]}"
                             if len(d) and unexplained.empty else None))
        summary.append({"year": year, "round": rnd, "source": source, "scopes": scopes, "cells": len(g),
                        "cells_with_difference": len(d), "unexplained": len(unexplained),
                        "max_abs_difference": int(d["diff"].abs().max()) if len(d) else 0})
    # The two official 2026 sources must agree with each other too.
    o26 = official[official["year"] == 2026].pivot_table(index=["round", "scope", "item"], columns="source",
                                                         values="value", aggfunc="sum").dropna()
    log.check("2026: cells where the results-portal JSON and the report PDF disagree",
              int((o26["portal_json"] != o26["report_pdf"]).sum()), expected=0)
    log.note("2014: no independent official source was reachable (the 2014 totalization report is not on "
             "the TSE file server, the 2014 results portal is offline and www.tse.jus.br refused automated "
             "access). The 2014 check compares the municipal tables with the section-level vote file, which "
             "comes from the same TSE database at a finer grain: it validates the aggregation, not the source.")
    # The published national table must equal the validated totals.
    q1 = con.sql("""
        SELECT n.year, n.round,
               (n.aptos = o.aptos AND n.comparecimento = o.comparecimento AND n.validos = o.validos
                AND n.brancos = o.brancos AND n.nulos = o.nulos AND n.camp_l = cl.value AND n.camp_b = cb.value) AS ok
        FROM (SELECT year, round, sum(aptos) aptos, sum(comparecimento) comparecimento, sum(validos) validos,
                     sum(brancos) brancos, sum(nulos) nulos, sum(camp_l) camp_l, sum(camp_b) camp_b
              FROM mun_results GROUP BY ALL) n
        JOIN (PIVOT (SELECT * FROM our_totals WHERE scope = 'BR' AND NOT item LIKE 'cand_%')
              ON item USING sum(value)) o USING (year, round)
        JOIN camps c1 ON c1.year = n.year AND c1.camp = 'L'
        JOIN camps c2 ON c2.year = n.year AND c2.camp = 'B'
        JOIN our_totals cl ON cl.year = n.year AND cl.round = n.round AND cl.scope = 'BR' AND cl.item = 'cand_' || c1.nr_candidato
        JOIN our_totals cb ON cb.year = n.year AND cb.round = n.round AND cb.scope = 'BR' AND cb.item = 'cand_' || c2.nr_candidato
    """).df()
    log.check("Election rounds where the municipal model totals differ from the validated national totals",
              int((~q1["ok"]).sum()), expected=0)
    s = pd.DataFrame(summary)
    s.to_csv(C.PROCESSED / "validation_summary.csv", index=False)
    log.table("Validation summary", list(s.columns), s.values.tolist())
    return s
