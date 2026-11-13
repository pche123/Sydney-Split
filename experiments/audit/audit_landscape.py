import os, sys; _H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [_H, os.path.dirname(_H), os.path.join(os.path.dirname(_H), "..")]  # experiments, repo root
from paths import SYD, TOK, RAW  # noqa: E402
"""Size of the landscape data-level test for every venue / licence / price line (one city per run)."""
import sys, numpy as np, pandas as pd
from cities import load
from linetests.landscape import MultiScaleNull
from linetests.records import landscape_size
import lines_sydney, lines_tokyo
city = sys.argv[1]; R = int(sys.argv[2])
C = load(city); GPn = MultiScaleNull(C["geom"], C["I"], C["J"], C["W"])
T, L = (lines_sydney if city == "Sydney" else lines_tokyo).build()
rows = []
for k, l in L.items():
    rows.append(dict(city=city, line=k, size=landscape_size(GPn, T, l, R=R, B=99, seed=3))); print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv(f"audit_landscape_{city}.csv", index=False)
