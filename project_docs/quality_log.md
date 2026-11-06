# Quality log

Written by the pipeline (`python run_all.py`) on 2026-11-06 04:48 UTC. Do not edit by hand.

Status legend: **ok** = observed equals expected (or informational); **explained** = differs from expected for a documented reason; **FAIL** = unexplained.


## Municipality crosswalk (TSE <-> IBGE)

* ok: TSE crosswalk rows: 5,571 (expected 5,571)
* ok: TSE crosswalk duplicated TSE codes: 0 (expected 0)
* ok: TSE crosswalk duplicated IBGE codes: 0 (expected 0)
* ok: TSE crosswalk rows with a missing code: 0 (expected 0)
* ok: Codes that disagree between TSE table and Base dos Dados: 0 (expected 0)
* note: IBGE codes only in the TSE table: [5101837] (Base dos Dados snapshot is from 2023-12, before Boa Esperança do Norte was installed). Only in Base dos Dados: [].
* ok: IBGE localidades rows: 5,571 (expected 5,571)
* ok: Censo 2022 population rows: 5,570 (expected 5,570)
* ok: Censo 2022 income rows (median): 5,570 (expected 5,570)
* ok: Crosswalk rows without IBGE attributes: 0 (expected 0)
* ok: UF disagreement between TSE table and IBGE: 0 (expected 0)
* note: Municipalities without Censo 2022 population (2025 estimate used): Boa Esperança do Norte (MT, 5101837)
* note: Municipalities without Censo 2022 income (left empty, excluded from income analysis): Boa Esperança do Norte (MT)

## Raw TSE files: shape, nulls and keys

* ok: 2014 round 1: election code in vote file: 143 (expected 143)
* ok: 2014 round 2: election code in vote file: 144 (expected 144)
* ok: 2018 round 1: election code in vote file: 295 (expected 295)
* ok: 2018 round 2: election code in vote file: 296 (expected 296)
* ok: 2022 round 1: election code in vote file: 544 (expected 544)
* ok: 2022 round 2: election code in vote file: 545 (expected 545)
* ok: 2026 round 1: election code in vote file: 6,257 (expected 6,257)
* ok: 2026 round 2: election code in vote file: 6,258 (expected 6,258)
* ok: Vote rows with a cargo other than Presidente: 0 (expected 0)
* ok: Turnout rows with a cargo other than Presidente: 0 (expected 0)
* ok: Vote rows with NULL year: 0 (expected 0)
* ok: Vote rows with NULL round: 0 (expected 0)
* ok: Vote rows with NULL uf: 0 (expected 0)
* ok: Vote rows with NULL cd_tse: 0 (expected 0)
* ok: Vote rows with NULL zona: 0 (expected 0)
* ok: Vote rows with NULL nr_candidato: 0 (expected 0)
* ok: Vote rows with NULL votes: 0 (expected 0)
* ok: Turnout rows with NULL year: 0 (expected 0)
* ok: Turnout rows with NULL round: 0 (expected 0)
* ok: Turnout rows with NULL uf: 0 (expected 0)
* ok: Turnout rows with NULL cd_tse: 0 (expected 0)
* ok: Turnout rows with NULL zona: 0 (expected 0)
* ok: Turnout rows with NULL aptos: 0 (expected 0)
* ok: Turnout rows with NULL comparecimento: 0 (expected 0)
* ok: Turnout rows with NULL abstencoes: 0 (expected 0)
* ok: Turnout rows with NULL validos: 0 (expected 0)
* ok: Turnout rows with NULL brancos: 0 (expected 0)
* ok: Turnout rows with NULL nulos: 0 (expected 0)
* ok: Duplicated keys in vote file (year, round, municipality, zone, transit, candidate): 0 (expected 0)
* ok: Duplicated keys in turnout file (year, round, municipality, zone, transit): 0 (expected 0)
* ok: Negative vote or turnout counts: 0 (expected 0)
* ok: Vote rows (2018+) whose destination is not 'Válido': 0 (expected 0)
* ok: Vote rows (2018+) where QT_VOTOS_NOMINAIS differs from QT_VOTOS_NOMINAIS_VALIDOS: 0 (expected 0)
* ok: 2014 transit-vote rows in the turnout file (summed into their municipality): 230
* note: 2014 is the only year with 'voto em trânsito' rows (ST_VOTO_EM_TRANSITO = 'S'): voters who asked to vote in a capital city. Their sections belong to that municipality, so they are summed into it.
* note: The 2014 vote file omits rows with zero votes (later years keep them). Missing candidate rows are treated as zero votes.

## Camps and candidates

* ok: 2014: ballot name of number 13: DILMA (expected DILMA)
* ok: 2014: ballot name of number 45: AÉCIO NEVES (expected AÉCIO NEVES)
* ok: 2018: ballot name of number 13: FERNANDO HADDAD (expected FERNANDO HADDAD)
* ok: 2018: ballot name of number 17: JAIR BOLSONARO (expected JAIR BOLSONARO)
* ok: 2022: ballot name of number 13: LULA (expected LULA)
* ok: 2022: ballot name of number 22: JAIR BOLSONARO (expected JAIR BOLSONARO)
* ok: 2026: ballot name of number 13: LULA (expected LULA)
* ok: 2026: ballot name of number 22: FLAVIO BOLSONARO (expected FLAVIO BOLSONARO)
* ok: Camp table in sql/01_model.sql matches src/config.py: True (expected True)
* ok: 2014: candidates in the runoff: 2 (expected 2)
* ok: 2018: candidates in the runoff: 2 (expected 2)
* ok: 2022: candidates in the runoff: 2 (expected 2)
* ok: 2026: candidates in the runoff: 2 (expected 2)

## Municipalities and crosswalk

* ok: 2014: domestic municipalities: 5,570 (expected 5,570)
* ok: 2014: domestic municipalities without IBGE code after the crosswalk: 0 (expected 0)
* ok: 2014: cities abroad (kept in national totals, left out of maps): 168
* ok: 2018: domestic municipalities: 5,570 (expected 5,570)
* ok: 2018: domestic municipalities without IBGE code after the crosswalk: 0 (expected 0)
* ok: 2018: cities abroad (kept in national totals, left out of maps): 171
* ok: 2022: domestic municipalities: 5,570 (expected 5,570)
* ok: 2022: domestic municipalities without IBGE code after the crosswalk: 0 (expected 0)
* ok: 2022: cities abroad (kept in national totals, left out of maps): 181
* ok: 2026: domestic municipalities: 5,571 (expected 5,571)
* ok: 2026: domestic municipalities without IBGE code after the crosswalk: 0 (expected 0)
* ok: 2026: cities abroad (kept in national totals, left out of maps): 186
* ok: First election with Boa Esperança do Norte (MT) as a municipality: 2,026 (expected 2,026)
* note: Boa Esperança do Norte (IBGE 5101837) was installed in 2025 with parts of Sorriso (5107925) and Nova Ubiratã (5106240); 2026 is its first presidential election. Maps before 2026 show its area hatched. No municipal comparison between 2022 and 2026 is published; the city view flags that Sorriso and Nova Ubiratã lost territory in 2025, so their 2026 results cover a smaller area than in earlier years.

## Model consistency

* ok: Rows where the five categories do not add up to the electorate: 0 (expected 0)
* ok: Rows where turnout differs from valid + blank + null + annulled votes: 0 (expected 0)
* ok: Runoff rows with third-candidate votes: 0 (expected 0)
* note: Electorate not split into turnout, abstention or non-installed sections in the turnout file: 2014 round 1: 688; 2014 round 2: 688. In 2014 these are polling places abroad (and 4 voters in Brazil) with electorate but no recorded attendance or abstention. The site counts every non-attending voter as 'did not vote' (electorate minus turnout), so totals still add up to the electorate.

## Validation against official TSE totals

* ok: 2014 round 1: municipality-zone rows where candidate votes differ from valid votes in the turnout table (of 6,548): 0 (expected 0)
* ok: 2014 round 2: municipality-zone rows where candidate votes differ from valid votes in the turnout table (of 6,548): 0 (expected 0)
* ok: 2018 round 1: municipality-zone rows where candidate votes differ from valid votes in the turnout table (of 6,273): 0 (expected 0)
* ok: 2018 round 2: municipality-zone rows where candidate votes differ from valid votes in the turnout table (of 6,273): 0 (expected 0)
* ok: 2022 round 1: municipality-zone rows where candidate votes differ from valid votes in the turnout table (of 6,283): 0 (expected 0)
* ok: 2022 round 2: municipality-zone rows where candidate votes differ from valid votes in the turnout table (of 6,283): 0 (expected 0)
* ok: 2026 round 1: municipality-zone rows where candidate votes differ from valid votes in the turnout table (of 6,292): 0 (expected 0)
* ok: 2026 round 2: municipality-zone rows where candidate votes differ from valid votes in the turnout table (of 6,292): 0 (expected 0)
* note: 2014 round 1: items with no official counterpart (sections_2014): abstencoes, anulados_apurados_separado, aptos, comparecimento
* note: 2014 round 2: items with no official counterpart (sections_2014): abstencoes, anulados_apurados_separado, aptos, comparecimento
* note: 2022 round 1: items with no official counterpart (report_pdf): anulados_apurados_separado
* note: 2022 round 2: items with no official counterpart (report_pdf): anulados_apurados_separado
* note: 2026 round 1: items with no official counterpart (portal_json, report_pdf): anulados_apurados_separado
* note: 2026 round 2: items with no official counterpart (portal_json, report_pdf): anulados_apurados_separado
* ok: Official cells with no counterpart in our aggregation: 0 (expected 0)
* ok: 2014 round 1 vs sections_2014: cells compared 406 across 29 scopes; cells with a difference: 0 (expected 0)
* ok: 2014 round 2 vs sections_2014: cells compared 145 across 29 scopes; cells with a difference: 0 (expected 0)
* ok: 2018 round 1 vs report_pdf: cells compared 580 across 29 scopes; cells with a difference: 0 (expected 0)
* explained: 2018 round 2 vs report_pdf: cells compared 261 across 29 scopes; cells with a difference: 3 (expected 0). Why: BR abstencoes +669.0; ES abstencoes +334.0; PR abstencoes +335.0. The municipal turnout file counts voters of sections that were not counted ('seções não apuradas', item 2.2.2 of the totalization report) as abstention; the report keeps them apart, so its abstention is lower by exactly that number. Votes and turnout are identical.
* ok: 2022 round 1 vs report_pdf: cells compared 493 across 29 scopes; cells with a difference: 0 (expected 0)
* ok: 2022 round 2 vs report_pdf: cells compared 232 across 29 scopes; cells with a difference: 0 (expected 0)
* ok: 2026 round 1 vs portal_json: cells compared 522 across 29 scopes; cells with a difference: 0 (expected 0)
* ok: 2026 round 1 vs report_pdf: cells compared 522 across 29 scopes; cells with a difference: 0 (expected 0)
* ok: 2026 round 2 vs portal_json: cells compared 232 across 29 scopes; cells with a difference: 0 (expected 0)
* ok: 2026 round 2 vs report_pdf: cells compared 232 across 29 scopes; cells with a difference: 0 (expected 0)
* ok: 2026: cells where the results-portal JSON and the report PDF disagree: 0 (expected 0)
* note: 2014: no independent official source was reachable (the 2014 totalization report is not on the TSE file server, the 2014 results portal is offline and www.tse.jus.br refused automated access). The 2014 check compares the municipal tables with the section-level vote file, which comes from the same TSE database at a finer grain: it validates the aggregation, not the source.
* ok: Election rounds where the municipal model totals differ from the validated national totals: 0 (expected 0)

**Validation summary**

| year | round | source | scopes | cells | cells_with_difference | unexplained | max_abs_difference |
|---|---|---|---|---|---|---|---|
| 2,014 | 1 | sections_2014 | 29 | 406 | 0 | 0 | 0 |
| 2,014 | 2 | sections_2014 | 29 | 145 | 0 | 0 | 0 |
| 2,018 | 1 | report_pdf | 29 | 580 | 0 | 0 | 0 |
| 2,018 | 2 | report_pdf | 29 | 261 | 3 | 0 | 669 |
| 2,022 | 1 | report_pdf | 29 | 493 | 0 | 0 | 0 |
| 2,022 | 2 | report_pdf | 29 | 232 | 0 | 0 | 0 |
| 2,026 | 1 | portal_json | 29 | 522 | 0 | 0 | 0 |
| 2,026 | 1 | report_pdf | 29 | 522 | 0 | 0 | 0 |
| 2,026 | 2 | portal_json | 29 | 232 | 0 | 0 | 0 |
| 2,026 | 2 | report_pdf | 29 | 232 | 0 | 0 | 0 |

* ok: IBGE 2025 mesh features: 5,573
* note: Dropped from the mesh: 4300001 and 4300002 ('Área Operacional' of Lagoa Mirim and Lagoa dos Patos, water bodies without voters). They show as background on the map.
* ok: Municipalities without a polygon in the mesh: 0 (expected 0)
* ok: Mesh polygons without a municipality: 0 (expected 0)
* ok: 2014 round 1: municipalities exported with results: 5,570 (expected 5,570)
* ok: 2014 round 2: municipalities exported with results: 5,570 (expected 5,570)
* ok: 2018 round 1: municipalities exported with results: 5,570 (expected 5,570)
* ok: 2018 round 2: municipalities exported with results: 5,570 (expected 5,570)
* ok: 2022 round 1: municipalities exported with results: 5,570 (expected 5,570)
* ok: 2022 round 2: municipalities exported with results: 5,570 (expected 5,570)
* ok: 2026 round 1: municipalities exported with results: 5,571 (expected 5,571)
* ok: 2026 round 2: municipalities exported with results: 5,571 (expected 5,571)
