# Data dictionary

## Raw inputs (`data/raw/`, not versioned)

| File | Origin | Columns used |
|---|---|---|
| `tse/votacao_candidato_munzona_<year>_BR.csv` | TSE, presidential votes by municipality and zone (Latin-1, `;`) | `ANO_ELEICAO`, `NR_TURNO`, `CD_ELEICAO`, `CD_CARGO`, `SG_UF`, `CD_MUNICIPIO`, `NM_MUNICIPIO`, `NR_ZONA`, `ST_VOTO_EM_TRANSITO`, `NR_CANDIDATO`, `NM_URNA_CANDIDATO`, `SG_PARTIDO`, `QT_VOTOS_NOMINAIS`, `QT_VOTOS_NOMINAIS_VALIDOS` (not in 2014), `NM_TIPO_DESTINACAO_VOTOS` |
| `tse/detalhe_votacao_munzona_<year>_BR.csv` | TSE, turnout detail by municipality and zone | `QT_APTOS`, `QT_COMPARECIMENTO`, `QT_ABSTENCOES`, `QT_ELEITORES_SECOES_NAO_INSTALADAS`, `QT_VOTOS`, `QT_TOTAL_VOTOS_VALIDOS`, `QT_VOTOS_NOMINAIS_VALIDOS`, `QT_VOTOS_BRANCOS`, `QT_TOTAL_VOTOS_NULOS`, `QT_VOTOS_NULOS`, `QT_VOTOS_NULOS_TECNICOS`, `QT_TOTAL_VOTOS_ANULADOS`, `QT_TOTAL_VOTOS_ANUL_SUBJUD`, `QT_VOTOS_ANULADOS_APU_SEP` plus the keys above |
| `tse/municipio_tse_ibge.zip` | TSE official code table | `CD_MUNICIPIO_TSE`, `CD_MUNICIPIO_IBGE`, `SG_UF`, `NM_MUNICIPIO_TSE` |
| `basedosdados/municipio.csv.gz` | Base dos Dados directory (cross-check only) | `id_municipio`, `id_municipio_tse` |
| `tse/official/*` | TSE totalization reports (PDF), 2026 results-portal JSON, 2014 section-level votes | validation only |
| `ibge/localidades_municipios.json` | IBGE localidades (`view=nivelado`) | `municipio-id`, `municipio-nome`, `UF-sigla`, `regiao-id`, `regiao-nome` |
| `ibge/sidra_4709_pop_2022.json` | Censo 2022 population | `D1C` (IBGE code), `V` |
| `ibge/sidra_6579_pop_est_2025.json` | 2025 population estimate (only for the municipality created after the census) | `D1C`, `V` |
| `ibge/sidra_10295_income_2022.json` | Censo 2022 household income per capita | `D1C`, `D2C` (13431 mean, 13534 median), `V` |
| `ibge/BR_Municipios_2025.zip` | IBGE municipal mesh 2025 (shapefile, SIRGAS 2000) | `CD_MUN`, geometry |

## Interim (`data/interim/`, not versioned)

* `municipalities.parquet`: one row per IBGE municipality. `cd_tse` (5-character TSE code), `cd_ibge`, `name` (IBGE), `uf`, `region_id`, `region`, `capital`, `population` (Censo 2022, or 2025 estimate), `pop_source`, `income_pc_mean`, `income_pc_median` (R$, Censo 2022).
* `elections.duckdb`: DuckDB database with every table below.

## Model tables (DuckDB)

* `stg_votes`: typed vote rows (year, round, municipality, zone, transit flag, candidate, votes).
* `stg_detail`: typed turnout rows.
* `camps`: `(year, nr_candidato, camp)` with camp `L` or `B`.
* `mun_results` (view `mun_br` without abroad): one row per election, round and municipality (or city abroad).

| Column | Meaning |
|---|---|
| `year`, `round` | election year, round (1 or 2) |
| `cd_tse`, `cd_ibge`, `name`, `uf`, `region_id`, `region` | identifiers (IBGE code is null abroad) |
| `abroad` | true for polling places abroad (UF `ZZ`) |
| `aptos` | electorate |
| `comparecimento` | turnout |
| `abstencoes` | abstention as published |
| `validos`, `brancos`, `nulos`, `anulados_apurados_separado` | votes by type (`nulos` includes technical nulls) |
| `camp_l`, `camp_b` | votes of the lulista and bolsonarista camps (2014: Dilma and Aécio) |
| `others` | votes of all other candidates |
| `top_other`, `top_other_nr` | votes and ballot number of the best-placed other candidate |
| `blank_null` | `brancos + nulos + anulados_apurados_separado` |
| `absent` | `aptos - comparecimento` |
| `share_l2` | `camp_l / (camp_l + camp_b)` |
| `pct_*_valid`, `pct_*_aptos` | shares of valid votes and of the electorate |
| `leader` | who came first: `L`, `B`, `O` (other candidate) or `tie` |
| `leader2` | which camp was ahead of the other: `L`, `B` or `tie` |

## Processed outputs (`data/processed/`)

One CSV per question table: `q1_national`, `q1_candidates`, `q2_municipal`, `q2_winners`, `q3_hist`, `q3_minority`, `q3_region`, `q3_state`, `q3_extremes`, `q4_*`, `q5_*`, `q6_*`, `q7_*`, plus `official_totals.csv`, `validation_summary.csv`, `validation_diffs.csv` and `quality_checks.csv`. Column names follow the model table; the header comment of each SQL file explains its question and measures.

## Site data (`docs/data/`)

| File | Content |
|---|---|
| `geo/municipios.topo.json` | TopoJSON, object `municipios`, geometry ids = IBGE codes, coordinates already projected (bbox `[0, 0, 1000, height]`) |
| `municipios.json` | `{fields, rows}` with `[id, name, uf, region, population]`, sorted by IBGE code |
| `results/<year>-<round>.json` | arrays aligned with `municipios.json` rows: `l`, `b`, `o`, `bn` (blank or null), `ab` (did not vote); first rounds also `ot`, `on` (best other candidate's votes and number). `null` = municipality did not exist |
| `dots/<year>-<round>.bin` | little-endian binary: `n` x Uint16, `n` y Uint16 (scaled to 0..65535 over the map box), `n` Uint8 camp (0 = L, 1 = B); counts in `dots/index.json` |
| `national.json` | national results (question 1) and every candidate |
| `stories.json` | aggregates used by the chapters (questions 2 to 7) |
| `facts.json` | every number quoted in the text: `{key: {value, kind, pt, en, desc}}` |
