"""Do lines pass more often inside one New York borough than across the whole city? (hypothesis 17)

    python experiments/borough_test.py <phase1 work folder> [out.csv]

Every census line is tested with the same single-fit landscape test (199 draws, no Holm correction) on the whole city
and on each borough alone (its own areas, borders and fitted landscape). Rivers and bridges are real borders between
boroughs, so a city-wide test mixes five separate landscapes.
"""
import json, os, sys
import numpy as np, pandas as pd, geopandas as gpd
from scipy.stats import norm, rankdata
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.join(HERE, ".."), os.path.join(HERE, "..", "pipeline")]
from linetests.landscape import MultiScaleNull
from cities import CITIES

WK = sys.argv[1]; OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "results", "phase1", "borough_newyork.csv")
city = "newyork"; C = CITIES[city]
G = gpd.read_file(f"{WK}/{city}/areas.gpkg").to_crs(C["crs"]).reset_index(drop=True)
z = np.load(f"{WK}/{city}/fields.npz"); I, J, W = z["I"], z["J"], z["W"]
rz = lambda v: norm.ppf((rankdata(v) - 0.5) / len(v))
rows = []
units = [("New York City", np.arange(len(G)))] + [(b, np.where(G.borough.values == b)[0]) for b in sorted(G.borough.unique())]
for name, idx in units:
    pos = -np.ones(len(G), int); pos[idx] = np.arange(len(idx))
    m = (pos[I] >= 0) & (pos[J] >= 0)
    if len(idx) < 30 or m.sum() < 30: print("skip", name, len(idx)); continue
    GN = MultiScaleNull(G.geometry.iloc[idx].reset_index(drop=True), pos[I[m]], pos[J[m]], W[m], m=25)
    for lid, kind, f in zip(z["ids"], z["kinds"], z["F"].T):
        if kind != "census": continue
        p = GN.test(rz(f[idx]), 199, seed=11)[0]
        rows.append(dict(unit=name, line=lid, areas=len(idx), p=p)); print(f"{name:15s} {lid:30s} areas={len(idx):3d} p={p:.3f}", flush=True)
pd.DataFrame(rows).to_csv(OUT, index=False)
