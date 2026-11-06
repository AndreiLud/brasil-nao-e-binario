"""Build the municipality reference table (TSE code <-> IBGE code + IBGE attributes).

Inputs (data/raw):
  tse/municipio_tse_ibge.zip           official TSE <-> IBGE code table (primary)
  basedosdados/municipio.csv.gz        Base dos Dados directory (independent cross-check)
  ibge/localidades_municipios.json     IBGE names, UF and region
  ibge/sidra_4709_pop_2022.json        Censo 2022 population
  ibge/sidra_6579_pop_est_2025.json    2025 population estimate (only used for the
                                       municipality created after the census)
  ibge/sidra_10295_income_2022.json    Censo 2022 household income per capita (mean, median)

Output: data/interim/municipalities.parquet, one row per IBGE municipality (5571).
Checks are appended to the quality log.
"""
from __future__ import annotations

import gzip
import io
import json
import sys
import zipfile
from pathlib import Path

import pandas as pd

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config as C
from src.quality import QualityLog


def read_tse_crosswalk() -> pd.DataFrame:
    with zipfile.ZipFile(C.RAW / "tse" / "municipio_tse_ibge.zip") as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        raw = z.read(name).decode("latin-1")
    df = pd.read_csv(io.StringIO(raw), sep=";", dtype=str)
    df = df.rename(columns={"CD_MUNICIPIO_TSE": "cd_tse", "CD_MUNICIPIO_IBGE": "cd_ibge",
                            "SG_UF": "uf", "NM_MUNICIPIO_TSE": "nm_tse"})
    df["cd_tse"] = df["cd_tse"].str.zfill(5)
    df["cd_ibge"] = df["cd_ibge"].astype(int)
    return df[["cd_tse", "cd_ibge", "uf", "nm_tse"]]


def read_bd_crosswalk() -> pd.DataFrame:
    with gzip.open(C.RAW / "basedosdados" / "municipio.csv.gz", "rt", encoding="utf-8") as f:
        df = pd.read_csv(f, dtype=str, usecols=["id_municipio", "id_municipio_tse"])
    df["cd_tse"] = df["id_municipio_tse"].str.zfill(5)
    df["cd_ibge"] = df["id_municipio"].astype(int)
    return df[["cd_tse", "cd_ibge"]]


def read_sidra(path: Path, value_name: str, var: str | None = None) -> pd.DataFrame:
    rows = json.loads(path.read_text(encoding="utf-8"))
    df = pd.DataFrame(rows)
    if var is not None:
        df = df[df["D2C"] == var]
    df = df[["D1C", "V"]].rename(columns={"D1C": "cd_ibge", "V": value_name})
    df["cd_ibge"] = df["cd_ibge"].astype(int)
    df[value_name] = pd.to_numeric(df[value_name], errors="coerce")
    return df


def build(log: QualityLog) -> pd.DataFrame:
    log.section("Municipality crosswalk (TSE <-> IBGE)")
    tse = read_tse_crosswalk()
    log.check("TSE crosswalk rows", len(tse), expected=5571)
    log.check("TSE crosswalk duplicated TSE codes", int(tse["cd_tse"].duplicated().sum()), expected=0)
    log.check("TSE crosswalk duplicated IBGE codes", int(tse["cd_ibge"].duplicated().sum()), expected=0)
    log.check("TSE crosswalk rows with a missing code", int(tse[["cd_tse", "cd_ibge"]].isna().any(axis=1).sum()), expected=0)

    bd = read_bd_crosswalk()
    both = tse.merge(bd, on="cd_ibge", how="outer", suffixes=("_tse", "_bd"), indicator=True)
    disagree = both[(both["_merge"] == "both") & (both["cd_tse_tse"] != both["cd_tse_bd"])]
    only_tse = both[both["_merge"] == "left_only"]["cd_ibge"].tolist()
    only_bd = both[both["_merge"] == "right_only"]["cd_ibge"].tolist()
    log.check("Codes that disagree between TSE table and Base dos Dados", len(disagree), expected=0)
    log.note(f"IBGE codes only in the TSE table: {only_tse} (Base dos Dados snapshot is from 2023-12, "
             f"before Boa Esperança do Norte was installed). Only in Base dos Dados: {only_bd}.")

    loc = pd.DataFrame(json.loads((C.RAW / "ibge" / "localidades_municipios.json").read_text(encoding="utf-8")))
    loc = loc.rename(columns={"municipio-id": "cd_ibge", "municipio-nome": "name", "UF-sigla": "uf_ibge",
                              "regiao-id": "region_id", "regiao-nome": "region"})
    loc = loc[["cd_ibge", "name", "uf_ibge", "region_id", "region"]]
    log.check("IBGE localidades rows", len(loc), expected=5571)

    pop22 = read_sidra(C.RAW / "ibge" / "sidra_4709_pop_2022.json", "pop_2022")
    pop25 = read_sidra(C.RAW / "ibge" / "sidra_6579_pop_est_2025.json", "pop_est_2025")
    inc = read_sidra(C.RAW / "ibge" / "sidra_10295_income_2022.json", "income_pc_mean", "13431")
    med = read_sidra(C.RAW / "ibge" / "sidra_10295_income_2022.json", "income_pc_median", "13534")
    log.check("Censo 2022 population rows", len(pop22), expected=5570)
    log.check("Censo 2022 income rows (median)", len(med), expected=5570)

    df = (tse.merge(loc, on="cd_ibge", how="left", validate="1:1")
             .merge(pop22, on="cd_ibge", how="left", validate="1:1")
             .merge(pop25, on="cd_ibge", how="left", validate="1:1")
             .merge(inc, on="cd_ibge", how="left", validate="1:1")
             .merge(med, on="cd_ibge", how="left", validate="1:1"))
    log.check("Crosswalk rows without IBGE attributes", int(df["name"].isna().sum()), expected=0)
    log.check("UF disagreement between TSE table and IBGE", int((df["uf"] != df["uf_ibge"]).sum()), expected=0)
    # Population used for size classes: Censo 2022; the one municipality created
    # afterwards gets the 2025 IBGE estimate and is flagged.
    df["pop_source"] = "censo_2022"
    miss = df["pop_2022"].isna()
    df.loc[miss, "pop_source"] = "estimativa_2025"
    df["population"] = df["pop_2022"].fillna(df["pop_est_2025"]).astype("Int64")
    log.note("Municipalities without Censo 2022 population (2025 estimate used): "
             + ", ".join(f"{r.name} ({r.uf}, {r.cd_ibge})" for r in df[miss].itertuples()))
    log.note("Municipalities without Censo 2022 income (left empty, excluded from income analysis): "
             + ", ".join(f"{r.name} ({r.uf})" for r in df[df["income_pc_median"].isna()].itertuples()))
    df["capital"] = df["cd_ibge"].isin(CAPITALS)
    out = df[["cd_tse", "cd_ibge", "name", "uf", "region_id", "region", "capital", "population", "pop_source",
              "income_pc_mean", "income_pc_median"]]
    C.INTERIM.mkdir(parents=True, exist_ok=True)
    out.to_parquet(C.INTERIM / "municipalities.parquet", index=False)
    return out


# State capitals (IBGE codes), used only for labels and examples.
CAPITALS = [1200401, 2704302, 1600303, 1302603, 2927408, 2304400, 5300108, 3205309, 5208707,
            2111300, 5103403, 5002704, 3106200, 1501402, 2507507, 4106902, 2611606, 2211001,
            3304557, 2408102, 4314902, 1100205, 1400100, 4205407, 3550308, 2800308, 1721000]


if __name__ == "__main__":
    lg = QualityLog()
    build(lg)
    lg.flush()
