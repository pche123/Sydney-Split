import os, sys; _H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [_H, os.path.dirname(_H), os.path.join(os.path.dirname(_H), "..")]  # experiments, repo root
from paths import SYD, TOK, RAW  # noqa: E402
import sys, json, numpy as np, pandas as pd
from cities import load
from linetests.landscape import MultiScaleNull, calibrated_edge_map
from linetests.records import calibrated_edge_data
import lines_sydney, lines_tokyo, lines_chains
city = sys.argv[1]; rows = []
C = load(city); GPn = MultiScaleNull(C["geom"], C["I"], C["J"], C["W"])
def save(r): rows.append(r); print(r, flush=True); pd.DataFrame(rows).to_csv(f"final_edge_{city}.csv", index=False)
if city == "Sydney":
    sys.argv = ["x", "classic", "0"]; import search_null as S
    APP = {("classic", 0): "the-hi-vis-line", ("classic", 1): "the-factory-line", ("quirky", 2): "the-laptop-vs-ute-line",
           ("quirky", 0): "the-tradie-belt", ("quirky", 1): "the-full-house-line", ("quirky", 3): "the-boomer-vs-builder-line"}
    for mode in ["classic", "quirky"]:
        S.mode = mode; g, I, J, W, Z, cols = S.prepare(); lb = pd.read_csv(f"q_{mode}/leaderboard.csv")
        G2 = MultiScaleNull(g.geometry, I, J, W)
        for (md, k), lid in APP.items():
            if md != mode: continue
            parts = lb.line[k].split(" vs "); f = Z[:, cols.index(parts[0])] - (Z[:, cols.index(parts[1])] if len(parts) > 1 else 0)
            r = calibrated_edge_map(G2, f, R=40); r.update(city=city, line=lid, kind="census"); save(r)
    mods = [lines_sydney.build(), lines_chains.sydney()]
else:
    z = np.load(f"{TOK}/out/tokyo_fields.npz"); F = dict(zip(z["ids"], z["F"].T))
    for lid in ["the-hi-vis-line", "the-factory-line", "the-laptop-vs-hard-hat-line", "the-boomer-vs-builder-line", "the-degree-line",
                "train-vs-car", "the-bicycle-line", "the-living-alone-line", "the-tower-line", "the-grey-line"]:
        r = calibrated_edge_map(GPn, F[lid], R=40); r.update(city=city, line=lid, kind="census"); save(r)
    mods = [lines_tokyo.build(), lines_chains.tokyo()]
for T, L in mods:
    for k, l in L.items():
        r = calibrated_edge_data(GPn, l, R=30); r.update(city=city, line=k, kind="records"); save(r)
