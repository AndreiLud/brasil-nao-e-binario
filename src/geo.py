"""Municipal mesh for the site and the dot-density layers.

1. Reads the IBGE 2025 municipal mesh (SIRGAS 2000) straight from the zip.
2. Projects it to an Albers equal-area conic centred on Brazil (areas on screen are
   proportional to areas on the ground), scaled to a 1000-unit-wide box with y down,
   so the browser only has to scale it (no projection math at runtime).
3. Simplifies it as a coverage (shared borders are simplified once, so neighbours
   never drift apart) and writes TopoJSON with integer (quantized) coordinates.
4. Builds the dot-density layers: one dot per DOT_VOTES votes of each camp, placed
   uniformly at random inside the (simplified) municipality, with a fixed seed.
   Fractional dots are kept with probability equal to the fraction, so the expected
   number of dots is exactly proportional to the votes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pyogrio
import shapely

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config as C

MESH_SHP = "/vsizip/data/raw/ibge/BR_Municipios_2025.zip/BR_Municipios_2025.shp"
# Albers equal-area conic parameters for Brazil (degrees).
LAT1, LAT2, LAT0, LON0 = -2.0, -22.0, -12.0, -54.0
WIDTH = 1000.0
SIMPLIFY_TOLERANCE = 0.35      # in projected units (1 unit ~ 1 px on a 1000 px wide map)
QUANTIZATION = 20000           # TopoJSON grid (per axis)
DOT_VOTES = 1000               # votes per dot


def albers(lon: np.ndarray, lat: np.ndarray):
    p1, p2, p0 = np.radians([LAT1, LAT2, LAT0])
    n = (np.sin(p1) + np.sin(p2)) / 2
    c = np.cos(p1) ** 2 + 2 * n * np.sin(p1)
    rho0 = np.sqrt(c - 2 * n * np.sin(p0)) / n
    phi, lam = np.radians(lat), np.radians(lon - LON0)
    rho = np.sqrt(c - 2 * n * np.sin(phi)) / n
    theta = n * lam
    return rho * np.sin(theta), rho0 - rho * np.cos(theta)


def read_mesh(log=None):
    _, _, wkb, fields = pyogrio.raw.read(MESH_SHP, columns=["CD_MUN", "NM_MUN"])
    codes = np.array([int(c) for c in fields[0]])
    geoms = shapely.from_wkb(wkb)
    keep = ~np.isin(codes, [4300001, 4300002])  # 'Área Operacional' lagoons, not municipalities
    if log:
        log.check("IBGE 2025 mesh features", int(len(codes)))
        log.note("Dropped from the mesh: 4300001 and 4300002 ('Área Operacional' of Lagoa Mirim and "
                 "Lagoa dos Patos, water bodies without voters). They show as background on the map.")
    return codes[keep], geoms[keep]


def project(geoms):
    def fn(coords):
        x, y = albers(coords[:, 0], coords[:, 1])
        return np.column_stack([x, y])
    proj = shapely.transform(geoms, fn)
    xmin, ymin, xmax, ymax = shapely.total_bounds(proj)
    k = WIDTH / (xmax - xmin)
    height = (ymax - ymin) * k

    def fit(coords):  # scale to WIDTH, y pointing down
        return np.column_stack([(coords[:, 0] - xmin) * k, (ymax - coords[:, 1]) * k])
    return shapely.transform(proj, fit), height, dict(xmin=xmin, ymax=ymax, k=k)


def simplify(geoms, tolerance=SIMPLIFY_TOLERANCE):
    out = shapely.coverage_simplify(geoms, tolerance, simplify_boundary=True)
    out = shapely.make_valid(out)
    return out


def to_topojson(codes, geoms, height):
    """Build TopoJSON with the `topojson` package (shared arcs) and quantized coords."""
    import topojson as tp
    features = [{"type": "Feature", "id": int(c), "properties": {}, "geometry": shapely.geometry.mapping(g)}
                for c, g in zip(codes, geoms)]
    topo = tp.Topology({"type": "FeatureCollection", "features": features}, object_name="municipios",
                       prequantize=False, topology=True, presimplify=False, toposimplify=False,
                       shared_coords=False)
    topo = topo.topoquantize(QUANTIZATION)
    d = topo.to_dict()
    for geo, c in zip(d["objects"]["municipios"]["geometries"], codes):
        geo["id"] = int(c)
        geo.pop("properties", None)
    d["bbox"] = [0, 0, WIDTH, round(height, 3)]
    return d


def dots(results, codes, geoms, seed=C.SEED, per_dot=DOT_VOTES):
    """results: DataFrame with cd_ibge, camp_l, camp_b for one election/round.

    Returns (x, y, camp) arrays in projected units, shuffled so draw order is random.
    """
    rng = np.random.default_rng(seed)
    by_code = dict(zip(codes, geoms))
    xs, ys, cs = [], [], []
    for r in results.itertuples():
        g = by_code.get(r.cd_ibge)
        if g is None:
            continue
        for camp, votes in ((0, r.camp_l), (1, r.camp_b)):
            exact = votes / per_dot
            n = int(exact) + int(rng.random() < exact - int(exact))
            if n == 0:
                continue
            x, y = sample_in(g, n, rng)
            xs.append(x), ys.append(y), cs.append(np.full(n, camp, dtype=np.uint8))
    x, y, c = np.concatenate(xs), np.concatenate(ys), np.concatenate(cs)
    order = rng.permutation(len(x))
    return x[order], y[order], c[order]


def sample_in(geom, n, rng):
    xmin, ymin, xmax, ymax = geom.bounds
    shapely.prepare(geom)
    got_x, got_y, have = [], [], 0
    while have < n:
        m = max(64, int((n - have) * 2.5))
        px = rng.uniform(xmin, xmax, m)
        py = rng.uniform(ymin, ymax, m)
        inside = shapely.contains_xy(geom, px, py)
        got_x.append(px[inside]), got_y.append(py[inside])
        have += int(inside.sum())
        if m > 10_000_000:
            raise RuntimeError("could not place dots")
    return np.concatenate(got_x)[:n], np.concatenate(got_y)[:n]
