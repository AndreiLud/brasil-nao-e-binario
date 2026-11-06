"""Export pre-aggregated data for the site (docs/data) and analysis tables (data/processed).

Site files (all small, loaded on demand by the page):
  geo/municipios.topo.json   projected, simplified mesh (ids = IBGE codes)
  municipios.json            names, UF, region, population (search + tooltips)
  results/<year>-<round>.json  per-municipality votes, in the order of municipios.json
  dots/<year>-<round>.bin    dot-density layer (Uint16 x, Uint16 y, Uint8 camp)
  dots/index.json            dot counts and votes per dot
  national.json              national results (Q1)
  stories.json               aggregates used by the chapters (Q3 to Q7)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config as C
from src import geo

ELECTIONS = [(y, r) for y in C.YEARS for r in C.ROUNDS]


def _dump(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def _records(df: pd.DataFrame, digits: int = 5):
    out = []
    for rec in df.to_dict(orient="records"):
        clean = {}
        for k, v in rec.items():
            if isinstance(v, (float, np.floating)):
                clean[k] = None if pd.isna(v) else round(float(v), digits)
            elif isinstance(v, (np.integer,)):
                clean[k] = int(v)
            elif v is pd.NA:
                clean[k] = None
            else:
                clean[k] = v
        out.append(clean)
    return out


def processed_tables(con):
    """Write every question table to data/processed as CSV (for the notebook and README)."""
    C.PROCESSED.mkdir(parents=True, exist_ok=True)
    tables = [r[0] for r in con.execute("SELECT table_name FROM information_schema.tables "
                                        "WHERE table_name LIKE 'q%' ORDER BY 1").fetchall()]
    for t in tables:
        con.sql(f"SELECT * FROM {t}").df().to_csv(C.PROCESSED / f"{t}.csv", index=False, float_format="%.6g")
    return tables


def site_data(con, log):
    out = C.SITE_DATA
    muni = con.sql("SELECT cd_ibge, name, uf, region_id, population FROM municipalities ORDER BY cd_ibge").df()
    order = muni["cd_ibge"].tolist()

    # Mesh
    codes, geoms = geo.read_mesh(log)
    proj, height, _ = geo.project(geoms)
    simp = geo.simplify(proj)
    topo = geo.to_topojson(codes, simp, height)
    _dump(topo, out / "geo" / "municipios.topo.json")
    missing = sorted(set(order) - set(int(c) for c in codes))
    log.check("Municipalities without a polygon in the mesh", len(missing), expected=0)
    extra = sorted(set(int(c) for c in codes) - set(order))
    log.check("Mesh polygons without a municipality", len(extra), expected=0)

    _dump({"fields": ["id", "name", "uf", "region", "population"],
           "rows": [[int(r.cd_ibge), r.name, r.uf, int(r.region_id), int(r.population)] for r in muni.itertuples()]},
          out / "municipios.json")

    # Results per election and round, aligned with municipios.json order.
    res = con.sql("SELECT year, round, cd_ibge, camp_l, camp_b, others, blank_null, absent, top_other, "
                  "top_other_nr FROM mun_br").df()
    dot_index = {"votes_per_dot": geo.DOT_VOTES, "width": geo.WIDTH, "height": round(height, 3), "files": {}}
    for y, r in ELECTIONS:
        d = res[(res.year == y) & (res["round"] == r)].set_index("cd_ibge").reindex(order)
        present = d["camp_l"].notna()
        cols = {}
        for c, k in (("camp_l", "l"), ("camp_b", "b"), ("others", "o"), ("blank_null", "bn"), ("absent", "ab"),
                     ("top_other", "ot"), ("top_other_nr", "on")):
            vals = [None if pd.isna(v) else int(v) for v in d[c]]
            if k in ("ot", "on") and not any(vals):
                continue  # runoffs have no third candidates
            cols[k] = vals
        _dump({"year": y, "round": r, **cols}, out / "results" / f"{y}-{r}.json")
        log.check(f"{y} round {r}: municipalities exported with results", int(present.sum()),
                  expected=5571 if y == 2026 else 5570)
        # Dots
        x, yy, camp = geo.dots(d[present].reset_index()[["cd_ibge", "camp_l", "camp_b"]],
                               codes, simp, seed=C.SEED + y * 10 + r)
        qx = np.round(x / geo.WIDTH * 65535).clip(0, 65535).astype("<u2")
        qy = np.round(yy / height * 65535).clip(0, 65535).astype("<u2")
        blob = qx.tobytes() + qy.tobytes() + camp.astype("u1").tobytes()
        p = out / "dots" / f"{y}-{r}.bin"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(blob)
        dot_index["files"][f"{y}-{r}"] = {"n": int(len(x)), "l": int((camp == 0).sum()), "b": int((camp == 1).sum())}
    _dump(dot_index, out / "dots" / "index.json")

    # National (Q1)
    nat = con.sql("SELECT * FROM q1_national ORDER BY year, round").df()
    cand = con.sql("SELECT year, round, nr_candidato, nm_urna, partido, camp, votes, pct_valid FROM q1_candidates").df()
    _dump({"national": _records(nat), "candidates": _records(cand)}, out / "national.json")

    # Chapter aggregates
    stories = {
        "winners": _records(con.sql("SELECT * FROM q2_winners").df()),
        "hist": _records(con.sql("SELECT * FROM q3_hist").df()),
        "minority": _records(con.sql("SELECT * FROM q3_minority").df()),
        "region": _records(con.sql("SELECT * FROM q3_region").df()),
        "state": _records(con.sql("SELECT * FROM q3_state").df()),
        "extremes": _records(con.sql("SELECT * FROM q3_extremes").df()),
        "rise2018": {"summary": _records(con.sql("SELECT * FROM q4_summary").df())[0],
                     "region": _records(con.sql("SELECT * FROM q4_region").df()),
                     "region_share": _records(con.sql("SELECT * FROM q4_region_share").df()),
                     "top": _records(con.sql("SELECT cd_ibge, name, uf, aptos_2018, b_share_2014_r2, b_share_2018_r2, "
                                             "delta_b_r2 FROM q4_top").df())},
        "recovery2022": {"summary": _records(con.sql("SELECT * FROM q5_summary").df())[0],
                         "region": _records(con.sql("SELECT * FROM q5_region").df()),
                         "top": _records(con.sql("SELECT cd_ibge, name, uf, aptos_2022, l_share_2018_r2, "
                                                 "l_share_2022_r2, delta_l_r2 FROM q5_top").df())},
        "turnaround2026": {"national": _records(con.sql("SELECT * FROM q6_national").df())[0],
                           "summary": _records(con.sql("SELECT * FROM q6_summary").df())[0],
                           "assoc": _records(con.sql("SELECT * FROM q6_assoc").df()),
                           "bins": _records(con.sql("SELECT * FROM q6_bins").df()),
                           "region": _records(con.sql("SELECT * FROM q6_region").df()),
                           "top_pts": _records(con.sql("SELECT cd_ibge, name, uf, aptos, gain_l_pts, gain_b_pts, "
                                                       "others_r1_pts, turnout_change_pts FROM q6_top_pts").df()),
                           "top_votes": _records(con.sql("SELECT cd_ibge, name, uf, aptos, delta_l_votes, "
                                                         "delta_b_votes FROM q6_top_votes").df())},
        "context": {"groups": _records(con.sql("SELECT * FROM q7_groups").df()),
                    "hist": _records(con.sql("SELECT * FROM q7_hist").df()),
                    "assoc": _records(con.sql("SELECT * FROM q7_assoc").df())},
    }
    _dump(stories, out / "stories.json")
    return dot_index
