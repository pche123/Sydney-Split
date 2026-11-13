import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "linetests"))  # library
import sys, numpy as np, pandas as pd
from cities import load
from landscape import MultiScaleNull
from records import landscape_calibrated, dmsr_test
import lines_sydney, lines_tokyo
city = sys.argv[1]
C = load(city); GPn = MultiScaleNull(C["geom"], C["I"], C["J"], C["W"])
T, L = (lines_sydney if city == "Sydney" else lines_tokyo).build()
rows = []
for k, l in L.items():
    r = landscape_calibrated(GPn, T, l, B=999, R=100, Bin=199, seed=7)
    r.update(city=city, line=k, p_dmsr=dmsr_test(T, l, 999)[0]); rows.append(r); print(r, flush=True)
    pd.DataFrame(rows).to_csv(f"final_data_{city}.csv", index=False)
