import os, sys; _H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [_H, os.path.dirname(_H), os.path.join(os.path.dirname(_H), "..")]  # experiments, repo root
from paths import SYD, TOK, RAW  # noqa: E402
import sys, numpy as np, pandas as pd
from cities import load
from linetests.landscape import MultiScaleNull
from linetests.records import landscape_calibrated, dmsr_test
import lines_chains
rows = []
for city in ["Sydney", "Tokyo"]:
    C = load(city); GPn = MultiScaleNull(C["geom"], C["I"], C["J"], C["W"])
    T, L = getattr(lines_chains, city.lower())()
    for k, l in L.items():
        rng = np.random.default_rng(5); obs = T.cut(l.field)[0]
        perm = np.array([T.cut(l.recipe(rng.permutation(l.records)))[0] for _ in range(999)])
        r = landscape_calibrated(GPn, T, l, B=999, R=60, Bin=199, seed=7)
        r.update(city=city, line=k, p_perm=(1 + (perm <= obs).sum()) / 1000); rows.append(r); print(r, flush=True)
        pd.DataFrame(rows).to_csv("final_chains.csv", index=False)
