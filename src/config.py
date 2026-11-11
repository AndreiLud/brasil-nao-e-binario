"""Project-wide constants: paths, source URLs, elections and camp definitions."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
REFERENCE = DATA / "reference"
SQL_DIR = ROOT / "sql"
DOCS = ROOT / "docs"
SITE_DATA = DOCS / "data"
PROJECT_DOCS = ROOT / "project_docs"
TEMPLATES = ROOT / "src" / "templates"
DB_PATH = INTERIM / "elections.duckdb"

YEARS = [2014, 2018, 2022, 2026]
ROUNDS = [1, 2]

# Fixed seed for every random step (dot-density map).
SEED = 20261025

TSE_CDN = "https://cdn.tse.jus.br/estatistica/sead/odsele"

# Presidential votes by municipality and zone. Only the national-scope member
# (<name>_BR.csv, cargo Presidente) is extracted from each zip.
TSE_VOTES = {
    y: (f"{TSE_CDN}/votacao_candidato_munzona/votacao_candidato_munzona_{y}.zip",
        f"votacao_candidato_munzona_{y}_BR.csv")
    for y in YEARS
}
# Turnout, abstention, blank and null votes by municipality and zone.
TSE_DETAIL = {
    y: (f"{TSE_CDN}/detalhe_votacao_munzona/detalhe_votacao_munzona_{y}.zip",
        f"detalhe_votacao_munzona_{y}_BR.csv")
    for y in YEARS
}
# Official TSE <-> IBGE municipality code table.
TSE_IBGE_CROSSWALK = f"{TSE_CDN}/municipio_tse_ibge/municipio_tse_ibge.zip"
# Independent copy of the crosswalk (Base dos Dados directory, public bucket).
BD_MUNICIPIO = ("https://storage.googleapis.com/basedosdados-public/one-click-download/"
                "br_bd_diretorios_brasil/municipio/municipio.csv.gz")

# Official totals used for validation.
TSE_TOTALIZATION_REPORT = {
    y: f"{TSE_CDN}/relatorio_resultado_totalizacao/Relatorio_Resultado_Totalizacao_{y}_BR.zip"
    for y in (2018, 2022, 2026)
}
TSE_PORTAL_2026 = "https://resultados.tse.jus.br/oficial/ele2026/{ele}/dados/{abr}/{abr}-c0001-e{ele:06d}-u.json"
# 2014 has no independent totalization source reachable; section-level votes are
# used as a second aggregation path (same TSE database, finer grain).
TSE_SECTION_2014 = f"{TSE_CDN}/votacao_secao/votacao_secao_2014_BR.zip"

# TSE election codes (CD_ELEICAO) observed in the files.
ELECTION_CODES = {(2014, 1): 143, (2014, 2): 144, (2018, 1): 295, (2018, 2): 296,
                  (2022, 1): 544, (2022, 2): 545, (2026, 1): 6257, (2026, 2): 6258}

UFS = ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA",
       "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"]

# IBGE sources.
IBGE_LOCALIDADES = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?view=nivelado"
SIDRA_POP_2022 = "https://apisidra.ibge.gov.br/values/t/4709/n6/all/v/93/p/2022/f/c/h/n"
SIDRA_POP_EST_2025 = "https://apisidra.ibge.gov.br/values/t/6579/n6/all/v/9324/p/2025/f/c/h/n"
SIDRA_INCOME_2022 = ("https://apisidra.ibge.gov.br/values/t/10295/n6/all/v/13431,13534/p/2022/"
                     "c2/6794/c86/95251/c58/95253/f/c/h/n")
IBGE_MESH_2025 = ("https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/"
                  "malhas_municipais/municipio_2025/Brasil/BR_Municipios_2025.zip")

# Camps. Candidates are identified by ballot number (NR_CANDIDATO) within each year.
# "L" = campo lulista, "B" = campo bolsonarista. In 2014 (baseline only) the two
# runoff candidates are mapped to the same columns but are labelled separately:
# Dilma (PT) on the "L" side and Aecio (PSDB), the non-PT runoff candidate, on the "B" side.
CAMPS = {
    2014: {"L": 13, "B": 45},
    2018: {"L": 13, "B": 17},
    2022: {"L": 13, "B": 22},
    2026: {"L": 13, "B": 22},
}
CANDIDATE_LABELS = {
    2014: {"L": "Dilma", "B": "Aécio"},
    2018: {"L": "Haddad", "B": "Jair Bolsonaro"},
    2022: {"L": "Lula", "B": "Jair Bolsonaro"},
    2026: {"L": "Lula", "B": "Flávio Bolsonaro"},
}
# Expected ballot names, checked during cleaning so a wrong number fails loudly.
EXPECTED_BALLOT_NAMES = {
    (2014, 13): "DILMA", (2014, 45): "AÉCIO NEVES",
    (2018, 13): "FERNANDO HADDAD", (2018, 17): "JAIR BOLSONARO",
    (2022, 13): "LULA", (2022, 22): "JAIR BOLSONARO",
    (2026, 13): "LULA", (2026, 22): "FLAVIO BOLSONARO",
}

# Municipality installed in 2025: Boa Esperanca do Norte (MT), formed from parts of
# Sorriso and Nova Ubirata. Used to build a comparable area for 2022 -> 2026.
NEW_MUNICIPALITY = 5101837
NEW_MUNICIPALITY_PARENTS = [5107925, 5106240]

REGIONS = {1: "Norte", 2: "Nordeste", 3: "Sudeste", 4: "Sul", 5: "Centro-Oeste"}

# Public address of the site and of the repository. Set them before publishing so the
# share preview (Open Graph image) uses an absolute URL, then run: python -m src.render
SITE_URL = "https://brasil-nao-e-binario.andreiludescher.com/"
# Earlier address (GitHub Pages, which still serves docs/). A page opened there sends the
# reader to the same path, query and hash under SITE_URL.
OLD_SITE_URL = "https://andreilud.github.io/brasil-nao-e-binario/"
REPO_URL = "https://github.com/AndreiLud/brasil-nao-e-binario"
