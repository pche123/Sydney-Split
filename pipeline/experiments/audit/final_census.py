import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "linetests"))  # library
import sys, json, numpy as np, pandas as pd
from landscape import MultiScaleNull, calibrated_map_test
city = sys.argv[1]; rows = []
if city == "Sydney":
    sys.argv = ["x", "classic", "0"]; import search_null as S
    APP = {("classic", 0): "the-hi-vis-line", ("classic", 1): "the-factory-line", ("quirky", 2): "the-laptop-vs-ute-line",
           ("quirky", 0): "the-tradie-belt", ("quirky", 1): "the-full-house-line", ("quirky", 3): "the-boomer-vs-builder-line"}
    for mode in ["classic", "quirky"]:
        S.mode = mode; g, I, J, W, Z, cols = S.prepare(); GPn = MultiScaleNull(g.geometry, I, J, W)
        lb = pd.read_csv(f"q_{mode}/leaderboard.csv")
        for (md, k), lid in APP.items():
            if md != mode: continue
            nm = lb.line[k]; parts = nm.split(" vs ")
            f = Z[:, cols.index(parts[0])] - (Z[:, cols.index(parts[1])] if len(parts) > 1 else 0)
            r = calibrated_map_test(GPn, f, seed=k); r.update(city=city, line=lid, definition=nm, p_app=lb.p_chance[k]); rows.append(r); print(r, flush=True)
else:
    from cities import load
    C = load("Tokyo"); GPn = MultiScaleNull(C["geom"], C["I"], C["J"], C["W"])
    z = np.load("/home/claude/tokyo/out/tokyo_fields.npz"); F = dict(zip(z["ids"], z["F"].T))
    app = {l["id"]: l["p"] for l in json.load(open("/home/claude/tokyo/app_data_tokyo.json"))["lines"]}
    for lid in ["the-hi-vis-line", "the-factory-line", "the-laptop-vs-hard-hat-line", "the-boomer-vs-builder-line", "the-degree-line",
                "train-vs-car", "the-bicycle-line", "the-living-alone-line", "the-tower-line", "the-grey-line"]:
        r = calibrated_map_test(GPn, F[lid], R=60, seed=1); r.update(city=city, line=lid, p_app=app[lid]); rows.append(r); print(r, flush=True)
pd.DataFrame(rows).to_csv(f"final_census_{city}.csv", index=False)
