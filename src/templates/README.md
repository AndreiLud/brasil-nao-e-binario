# Brazil is not binary

![Dot map of the 2026 Brazilian presidential runoff: one dot per 1,000 votes, violet for Lula and ochre for Flávio Bolsonaro, mixed across the country](docs/img/hero-en.png)

A data story about the Brazilian presidential elections of 2018, 2022 and 2026 (with 2014 as a baseline), built from official TSE and IBGE data, municipality by municipality. The "who won in each city" map draws a country split in two blocks. The votes say something else: both camps have voters everywhere, alongside people who voted for someone else, voted blank or null, or stayed home.

* **Site in English:** {{cfg_site_url}}en/
* **Site in Portuguese:** {{cfg_site_url}}
* **Versão em português deste README:** [README.pt-BR.md](README.pt-BR.md)

The site is bilingual. Both versions use the same data, charts and design, and a PT/EN switch at the top of each page links them.

## Key findings

All figures come from `docs/data/facts.json`, which the pipeline computes; this README is rendered from a template, so no number is typed by hand. 2026 runoff unless noted.

* **{{e2026r2_local_minority_votes}} people voted for the candidate who lost in their own municipality**, {{e2026r2_local_minority_vote_share}} of all valid votes.
* **The winner map hides a tie.** Lula led in {{e2026r2_led_by_l}} municipalities and Flávio Bolsonaro in {{e2026r2_led_by_b}}. {{e2026r2_l_share_of_votes_where_b_led}} of Lula's votes in Brazil came from municipalities that Flávio won, and {{e2026r2_b_share_of_votes_where_l_led}} of Flávio's from municipalities that Lula won.
* **The local loser rarely disappears.** It got more than 30% of the vote in {{e2026r2_n_minority_over_30}} municipalities and more than 10% in {{e2026r2_n_minority_over_10}} of {{n_mun_2026}}. In the most lulista municipality, {{e2026r2_most_l_name}}, Flávio got {{e2026r2_most_l_share_b}}; in the most bolsonarista, {{e2026r2_most_b_name}}, Lula got {{e2026r2_most_b_share_l}}.
* **Each camp has millions of votes where it loses.** Flávio got {{e2026r2_reg_ne_camp_b}} votes in the Northeast, more than in {{e2026r2_b_ne_states_n}} federative units of other regions combined. Lula got {{e2026r2_reg_s_camp_l}} in the South, more than in {{e2026r2_l_s_states_n}} units of other regions combined. In the North the two were {{e2026r2_reg_n_diff_int}} votes apart.
* **Against the thesis, shown with the same weight.** Region and income are strongly associated with the municipal vote. Lula led {{e2026r2_reg_ne_led_by_l}} of the {{e2026r2_reg_ne_municipalities}} Northeast municipalities; Flávio led {{e2026r2_reg_s_led_by_b}} of {{e2026r2_reg_s_municipalities}} in the South. The median lulista share was {{q7_income1_p50_l}} in the lowest income band and {{q7_income5_p50_l}} in the highest (correlation with log median income: {{q7_r_income_2026}}).
* **2018.** The runoff share of the candidate facing the PT (Aécio in 2014, Bolsonaro in 2018) grew in {{q4_n_b_grew}} of {{n_mun_2022}} municipalities: by {{q4_reg_se_delta_b_share}} in the Southeast, {{q4_reg_s_delta_b_share}} in the South and {{q4_reg_ne_delta_b_share}} in the Northeast.
* **2022.** Lula had {{q5_delta_l_votes}} more runoff votes than Haddad; the Southeast accounted for {{q5_se_share_of_l_gain}} of that gain inside Brazil.
* **2026 turnaround.** Flávio led the first round by {{q6_b_lead_r1}} votes and Lula won the runoff by {{q6_l_lead_r2}}. Between rounds Lula gained {{q6_delta_l_votes}} votes and Flávio {{q6_delta_b_votes}}; Lula gained more than Flávio in {{q6_n_l_gained_more}} municipalities and Flávio more than Lula in {{q6_n_b_gained_more}}.

## Questions

1. How did the national result evolve from 2018 to 2026, in both rounds, including abstention, blank and null votes?
2. How did each municipality vote in each election and round?
3. How mixed is the vote (distribution of municipal shares, municipalities where the local loser got more than 30% or 40%, absolute votes by region)?
4. Where and how much did the bolsonarista camp grow in 2018, compared with the non-PT side of 2014?
5. Where did the lulista camp regain ground in 2022?
6. How did the 2026 runoff turnaround happen, and how is it associated with third-candidate votes and turnout change?
7. How is the vote associated with municipality size, region and income?

Each question has one SQL file in `sql/` (`q1_national.sql` to `q7_context.sql`).

## Camps

To compare elections with different candidates, votes are grouped into two camps:

* **Lulista camp:** Fernando Haddad (2018), Lula (2022 and 2026).
* **Bolsonarista camp:** Jair Bolsonaro (2018 and 2022), Flávio Bolsonaro (2026).
* **2014** (Dilma Rousseff against Aécio Neves) is only a baseline and is always labelled with the candidates' names.

## Data sources

| Data | Source |
|---|---|
| Votes by candidate, municipality and zone | [TSE open data](https://dadosabertos.tse.jus.br/), `votacao_candidato_munzona_<year>.zip` (presidential member `_BR.csv`) |
| Turnout, abstention, blank and null votes | TSE, `detalhe_votacao_munzona_<year>.zip` |
| TSE to IBGE municipality codes | TSE, `municipio_tse_ibge.zip` (checked against the Base dos Dados municipality directory) |
| Official totals for validation | TSE totalization reports (2018, 2022, 2026) and the 2026 results portal |
| Municipal boundaries | IBGE, Malha Municipal 2025 |
| Region, UF | IBGE localidades API |
| Population, income | IBGE Censo 2022 (SIDRA tables 4709 and 10295) |

Exact URLs, file sizes, checksums and retrieval times are recorded in `data/raw/manifest.json` after a run.

## Method in short

* The TSE files are read with DuckDB and summed from zones to municipalities (`sql/00_staging.sql`, `sql/01_model.sql`).
* For every municipality and round, five groups add up exactly to the electorate: lulista camp, bolsonarista camp, other candidates, blank or null, and did not vote.
* Votes cast abroad count in national totals and are left out of maps.
* **Validation:** every national, state and abroad total of every round was compared cell by cell with the official TSE totals ({{validation_cells}} cells, {{validation_unexplained}} unexplained differences). See `project_docs/quality_log.md`.
* **Map:** the IBGE mesh is projected (Albers equal-area), simplified as a coverage so neighbours keep shared borders, and exported as TopoJSON. The dot map places one dot per {{dot_votes}} votes at a random spot inside its municipality, with a fixed seed.

Details, decisions and their reasons: [project_docs/methodology.md](project_docs/methodology.md). Column definitions: [project_docs/data_dictionary.md](project_docs/data_dictionary.md).

## Limitations

* Municipal data describe places, not people. No number here says how an individual voted (ecological fallacy). Associations with income, size, third candidates or turnout are not causal.
* Abstention includes outdated registrations (people who moved or died).
* The 2014 comparison measures the candidate who faced the PT in the runoff, not the same political movement.
* No independent official source for 2014 totals was reachable; 2014 was checked against the TSE section-level file, which comes from the same database.
* Boa Esperança do Norte (MT) was installed in 2025 with parts of Sorriso and Nova Ubiratã and had its first presidential election in 2026, so the 2026 results of those two municipalities cover a smaller area than in earlier years.

## Reproduce

Requirements: Python 3.12 and about 1 GB of free disk space. One command runs everything (downloads only what is missing):

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python run_all.py          # download, clean, validate, analyse, export, render
.venv/bin/python -m src.vendor       # optional: re-download pinned JS libraries and fonts
.venv/bin/python -m playwright install chromium
.venv/bin/python -m src.screenshots og   # optional: regenerate the share images (PT and EN)
.venv/bin/python -m src.smoke            # browser smoke test of both languages (JS errors, controls, search, deep link)
cd docs && python3 -m http.server 8000   # open http://localhost:8000 (Portuguese) or /en/ (English)
```

`make all`, `make serve` and `make screenshots` do the same. Versions are pinned in `requirements.txt`. DuckDB is pinned to version 1.5.6 on purpose: the 2.0 wheels require AVX instructions that some virtual machines do not have. Raw data are not versioned (`data/raw/` is ignored); `src/download.py` fetches them again and records checksums.

## Bilingual site

| Piece | Portuguese | English |
|---|---|---|
| Page | `docs/index.html` | `docs/en/index.html` |
| Template (all prose) | `src/templates/index.html` | `src/templates/index.en.html` |
| Numbers in the prose | `pt` text of each key in `docs/data/facts.json` | `en` text of the same key |
| Chart labels, legends, tooltips | `pt` block of `docs/js/i18n.js` | `en` block of `docs/js/i18n.js` |
| Share image | `docs/img/og.png` | `docs/img/og-en.png` |

* The JavaScript reads the language from `<html lang>` and formats numbers to match (`46,6 milhões` or `46.6 million`). The English page sets `data-base="../"` so it reads the same data files in `docs/data/`.
* To change the text, edit both templates and run `.venv/bin/python -m src.render`. The renderer refuses to write the pages if they lose structural parity (same element ids, scrollytelling steps and figures in both languages), if a number in the prose is not a computed fact, or if an em dash, en dash or spaced hyphen appears.
* Both pages declare each other with `hreflang` links, and each has its own Open Graph image and description.

## Repository structure

```
run_all.py            one command for the whole pipeline
wrangler.jsonc        Cloudflare Workers configuration (serves docs/)
requirements.txt      pinned Python dependencies
sql/                  one SQL file per question, plus staging, model and validation
src/                  download, crosswalk, checks, validation, geo, export, facts, render
src/templates/        page templates (index.html in Portuguese, index.en.html in English), share cards,
                      READMEs and methodology (numbers come from facts.json)
notebooks/            exploratory analysis with questions and takeaways (executed)
project_docs/         brief, data dictionary, quality log, methodology
data/raw, interim     not versioned
data/processed/       analysis tables (CSV), validation results
docs/                 the static site: Portuguese at the root, English in docs/en/
docs/js/i18n.js       chart and interface strings in both languages
```

## Publish

The site is the static folder `docs/`, served as is. `SITE_URL` and `REPO_URL` in `src/config.py` hold the public addresses (canonical links and share images need absolute URLs); after changing them, run `.venv/bin/python -m src.render`.

* **Cloudflare Workers:** `wrangler.jsonc` uploads `docs/` as static assets (no script runs) and declares the custom domains, whose DNS records and certificates Cloudflare creates on deploy. In the Cloudflare dashboard: **Workers & Pages → Create → Import a repository**, pick this repository, keep the name `brasil-nao-e-binario`, leave the build command empty and set the deploy command to `npx wrangler@4.158.0 deploy`. Every push to `main` publishes again.
* **GitHub Pages:** **Settings → Pages → Build and deployment → Source: Deploy from a branch → Branch: main, folder: /docs → Save.**

## Credits

Code: MIT License (see `LICENSE`). Data: Tribunal Superior Eleitoral (TSE) and Instituto Brasileiro de Geografia e Estatística (IBGE). Libraries: D3 (ISC), topojson-client (ISC), Scrollama (MIT). Fonts: Fraunces and Inter (SIL Open Font License). License files are in `docs/vendor` and `docs/fonts`.
