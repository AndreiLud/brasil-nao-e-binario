# Methodology

This file is rendered from `src/templates/methodology.md`; numbers come from `docs/data/facts.json`.

## Pipeline

`python run_all.py` runs, in order:

1. **Download** (`src/download.py`). Only the presidential member of each large TSE zip is extracted, through HTTP Range requests (the zip directory is read first, then only that member's bytes). If a server ignores Range requests, the whole zip is downloaded instead. Every file gets a sha256, size, source URL, server `Last-Modified` and retrieval time in `data/raw/manifest.json`.
2. **Crosswalk** (`src/crosswalk.py`). Official TSE table `municipio_tse_ibge`, checked against the Base dos Dados municipality directory (no disagreement on shared codes). Joined on codes only, never on names. IBGE region, UF, Censo 2022 population and income are attached.
3. **Staging and model** (`sql/00_staging.sql`, `sql/01_model.sql`). Raw CSVs are read as text (codes keep leading zeros) and cast explicitly. Zones, and the 2014 transit-vote sections, are summed into their municipality.
4. **Checks** (`src/checks.py`): election codes, nulls, duplicate keys, negative counts, ballot names of every camp candidate, municipality coverage, and the identity `camp_l + camp_b + others + blank_null + absent = aptos` in every row.
5. **Validation** (`src/validate.py`, `sql/v01_validation_totals.sql`, `src/official_totals.py`). See below.
6. **Questions** (`sql/q1_national.sql` to `sql/q7_context.sql`), one file per question. Tables are written to `data/processed/*.csv`.
7. **Site data** (`src/export.py`, `src/geo.py`): mesh, per-municipality results, dot layers, chapter aggregates.
8. **Facts** (`src/facts.py`): every number used in the text, with a description.
9. **Render** (`src/render.py`): page, READMEs and this file are rendered from templates; the renderer fails if a placeholder is unknown, if an em dash, en dash or spaced hyphen appears in the prose, or if a number in the prose is not a computed fact (or one of a short list of fixed values such as election years).
10. **Notebook** (`src/notebook.py`): builds and executes `notebooks/01_exploratory_analysis.ipynb`.

## Definitions

* **Electorate (aptos):** registered voters able to vote (`QT_APTOS`).
* **Did not vote (absent):** electorate minus turnout. It includes abstention and voters of sections that were not installed or not counted.
* **Blank or null:** blank votes, null votes (including technical nulls) and votes annulled and counted separately.
* **Camps:** lulista = PT candidate (Haddad 2018, Lula 2022 and 2026); bolsonarista = Jair Bolsonaro (2018, 2022), Flávio Bolsonaro (2026). In 2014 Dilma (PT) and Aécio (PSDB) take those two positions only as a baseline. Candidates are identified by ballot number and the ballot name is checked.
* **Two-camp share:** lulista votes divided by the votes of the two camps. In a runoff it equals the share of valid votes. In a first round it ignores the other candidates, which the maps say explicitly.
* **Leader:** the candidate who came first in a municipality. In the first rounds of 2014 and 2018 a third candidate came first in some municipalities (99 and 103); they are counted apart. For changes between elections, the comparison is between the two camps only.
* **Local minority:** in each municipality, the smaller of the two camps. Municipalities with an exact tie are left out of the minority counts.

## Validation

For each election and round, every scope (Brazil, each UF, abroad) and every item (electorate, turnout, abstention, valid, blank and null votes, each candidate) is compared with an official source:

* **2026:** the results-portal JSON files and the totalization report PDF (they agree with each other).
* **2018, 2022:** the totalization report PDFs (BR, each UF and abroad).
* **2014:** no independent official source was reachable (the 2014 report is not on the TSE file server, the 2014 portal is offline and `www.tse.jus.br` refused automated access). The municipal tables were compared with the section-level vote file, which comes from the same TSE database at a finer grain: this validates the aggregation, not the source.

Result: 3,625 cells compared, 0 unexplained differences. The only difference is the 2018 runoff abstention in ES and PR: the municipal turnout file counts voters of sections that were not counted as abstention, while the report keeps them apart (item 2.2.2). An outer join also lists cells that exist only on our side, so nothing is skipped silently. The municipal model is checked against the validated national totals.

An independent recomputation (separate code path, pandas on the raw CSVs) reproduced the headline facts; it found that vote changes between elections were computed without votes cast abroad, which was corrected (national changes now include abroad).

## Geography

* Mesh: IBGE Malha Municipal 2025, read straight from the zip. The two "Área Operacional" lagoons in Rio Grande do Sul are not municipalities and were dropped.
* Projection: Albers equal-area conic centred on Brazil (`lat1=-2, lat2=-22, lat0=-12, lon0=-54`), scaled to a 1000-unit-wide box, so the browser only scales coordinates.
* Simplification: `shapely.coverage_simplify` on the whole coverage, so shared borders are simplified once and neighbours never drift apart. TopoJSON with quantized, delta-encoded arcs.
* Boa Esperança do Norte (IBGE 5101837) was installed in 2025 with parts of Sorriso and Nova Ubiratã; 2026 is its first presidential election. Earlier presidential maps show its area hatched. No municipal comparison between 2022 and 2026 is published, and the city view warns that Sorriso and Nova Ubiratã cover a smaller area in 2026.
* Dot map: one dot per 1,000 votes of each camp; fractional dots are kept with probability equal to the fraction (so expected dots are proportional to votes), placed uniformly at random inside the simplified municipality with a fixed seed, and drawn in random order with slight transparency so neither color sits on top of the other.

## Associations (questions 6 and 7)

* Question 6 uses points of each municipality's electorate. By construction, the two candidates' gains add up to the third-candidate vote of round 1 plus the turnout change minus the change in blank and null votes, so both gains are mechanically larger where third candidates or turnout gains were larger. The site therefore reports the arithmetic, the correlations and the net gain (Lula's gain minus Flávio's), which varied from 3.7 points to 5.1 points across groups of municipalities. None of this identifies individual vote switching.
* Question 7 uses Censo 2022 median household income per capita, grouped in five bands cut at the 20th, 40th, 60th and 80th percentiles. Many municipalities have exactly one 2022 minimum wage as their median, so ties stay in the same band and bands have unequal sizes. Income and region are entangled; the association also holds inside regions (correlation −0.59).

## Known limitations

* Ecological fallacy: municipal data describe places, not people.
* Abstention includes outdated registrations.
* 2014 baseline compares different political movements.
* The TSE regenerates files from time to time; checksums in the manifest show whether a rerun used the same inputs.
