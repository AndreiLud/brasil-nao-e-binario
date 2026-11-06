"""Data quality checks on the staged and modelled tables (logged to the quality log)."""
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config as C
from src.quality import QualityLog


def run(con, log: QualityLog):
    v = lambda sql: con.execute(sql).fetchone()[0]

    log.section("Raw TSE files: shape, nulls and keys")
    for y in C.YEARS:
        for r in C.ROUNDS:
            code = v(f"SELECT string_agg(DISTINCT cd_eleicao::VARCHAR, ',') FROM stg_votes WHERE year={y} AND round={r}")
            log.check(f"{y} round {r}: election code in vote file", int(code), expected=C.ELECTION_CODES[(y, r)])
    log.check("Vote rows with a cargo other than Presidente", v("SELECT count(*) FROM stg_votes WHERE cd_cargo <> 1"), expected=0)
    log.check("Turnout rows with a cargo other than Presidente", v("SELECT count(*) FROM stg_detail WHERE cd_cargo <> 1"), expected=0)
    for col in ("year", "round", "uf", "cd_tse", "zona", "nr_candidato", "votes"):
        log.check(f"Vote rows with NULL {col}", v(f"SELECT count(*) FROM stg_votes WHERE {col} IS NULL"), expected=0)
    for col in ("year", "round", "uf", "cd_tse", "zona", "aptos", "comparecimento", "abstencoes", "validos", "brancos", "nulos"):
        log.check(f"Turnout rows with NULL {col}", v(f"SELECT count(*) FROM stg_detail WHERE {col} IS NULL"), expected=0)
    log.check("Duplicated keys in vote file (year, round, municipality, zone, transit, candidate)",
              v("SELECT count(*) FROM (SELECT count(*) c FROM stg_votes GROUP BY year, round, cd_tse, zona, transit, "
                "nr_candidato HAVING c > 1)"), expected=0)
    log.check("Duplicated keys in turnout file (year, round, municipality, zone, transit)",
              v("SELECT count(*) FROM (SELECT count(*) c FROM stg_detail GROUP BY year, round, cd_tse, zona, transit "
                "HAVING c > 1)"), expected=0)
    log.check("Negative vote or turnout counts",
              v("SELECT (SELECT count(*) FROM stg_votes WHERE votes < 0) + (SELECT count(*) FROM stg_detail WHERE "
                "least(aptos, comparecimento, abstencoes, validos, brancos, nulos) < 0)"), expected=0)
    log.check("Vote rows (2018+) whose destination is not 'Válido'",
              v("SELECT count(*) FROM stg_votes WHERE year >= 2018 AND destination <> 'Válido'"), expected=0)
    log.check("Vote rows (2018+) where QT_VOTOS_NOMINAIS differs from QT_VOTOS_NOMINAIS_VALIDOS",
              v("SELECT count(*) FROM stg_votes WHERE year >= 2018 AND votes <> votes_valid_col"), expected=0)
    log.check("2014 transit-vote rows in the turnout file (summed into their municipality)",
              v("SELECT count(*) FROM stg_detail WHERE transit = 'S'"))
    log.note("2014 is the only year with 'voto em trânsito' rows (ST_VOTO_EM_TRANSITO = 'S'): voters who asked to "
             "vote in a capital city. Their sections belong to that municipality, so they are summed into it.")
    log.note("The 2014 vote file omits rows with zero votes (later years keep them). Missing candidate rows are "
             "treated as zero votes.")

    log.section("Camps and candidates")
    for (y, nr), expected in C.EXPECTED_BALLOT_NAMES.items():
        got = v(f"SELECT string_agg(DISTINCT nm_urna, '|') FROM stg_votes WHERE year={y} AND nr_candidato={nr}")
        log.check(f"{y}: ballot name of number {nr}", got, expected=expected)
    sql_camps = {(r[0], r[1]): r[2] for r in con.execute("SELECT year, nr_candidato, camp FROM camps").fetchall()}
    cfg_camps = {(y, nr): camp for y, d in C.CAMPS.items() for camp, nr in d.items()}
    log.check("Camp table in sql/01_model.sql matches src/config.py", sql_camps == cfg_camps, expected=True)
    for y in C.YEARS:
        n = v(f"SELECT count(DISTINCT nr_candidato) FROM stg_votes WHERE year={y} AND round=2")
        log.check(f"{y}: candidates in the runoff", n, expected=2)

    log.section("Municipalities and crosswalk")
    for y in C.YEARS:
        n = v(f"SELECT count(DISTINCT cd_tse) FROM mun_results WHERE year={y} AND NOT abroad")
        log.check(f"{y}: domestic municipalities", n, expected=5571 if y == 2026 else 5570)
        miss = v(f"SELECT count(*) FROM mun_results WHERE year={y} AND NOT abroad AND cd_ibge IS NULL")
        log.check(f"{y}: domestic municipalities without IBGE code after the crosswalk", miss, expected=0)
        ab = v(f"SELECT count(*) FROM mun_results WHERE year={y} AND round=2 AND abroad")
        log.check(f"{y}: cities abroad (kept in national totals, left out of maps)", ab)
    first = v(f"SELECT min(year) FROM mun_results WHERE cd_ibge = {C.NEW_MUNICIPALITY}")
    log.check("First election with Boa Esperança do Norte (MT) as a municipality", first, expected=2026)
    log.note("Boa Esperança do Norte (IBGE 5101837) was installed in 2025 with parts of Sorriso (5107925) and Nova "
             "Ubiratã (5106240); 2026 is its first presidential election. Maps before 2026 show its area hatched. "
             "No municipal comparison between 2022 and 2026 is published; the city view flags that Sorriso and "
             "Nova Ubiratã lost territory in 2025, so their 2026 results cover a smaller area than in earlier years.")

    log.section("Model consistency")
    log.check("Rows where the five categories do not add up to the electorate",
              v("SELECT count(*) FROM mun_results WHERE camp_l + camp_b + others + blank_null + absent <> aptos"),
              expected=0)
    log.check("Rows where turnout differs from valid + blank + null + annulled votes",
              v("SELECT count(*) FROM mun_results WHERE comparecimento <> validos + brancos + nulos + anulados_apurados_separado"),
              expected=0)
    log.check("Runoff rows with third-candidate votes", v("SELECT count(*) FROM mun_results WHERE round = 2 AND others <> 0"),
              expected=0)
    resid = con.execute("SELECT year, round, sum(aptos - comparecimento - abstencoes - aptos_secoes_nao_instaladas) "
                        "FROM mun_turnout GROUP BY ALL HAVING sum(aptos - comparecimento - abstencoes - "
                        "aptos_secoes_nao_instaladas) <> 0 ORDER BY ALL").fetchall()
    log.note("Electorate not split into turnout, abstention or non-installed sections in the turnout file: "
             + "; ".join(f"{y} round {r}: {n:,}" for y, r, n in resid)
             + ". In 2014 these are polling places abroad (and 4 voters in Brazil) with electorate but no recorded "
               "attendance or abstention. The site counts every non-attending voter as 'did not vote' "
               "(electorate minus turnout), so totals still add up to the electorate.")
