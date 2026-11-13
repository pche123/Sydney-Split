import os, sys; _H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [_H, os.path.dirname(_H), os.path.join(os.path.dirname(_H), "..")]  # experiments, repo root
from paths import SYD, TOK, RAW  # noqa: E402
"""Size of the data-level line test, for every venue / licence / price line in both cities.
random-layout: the world is one MSR rotation of the line's own estimated surfaces.
no-geography: flat surfaces. Both should give ~5% 'line' verdicts."""
import numpy as np, pandas as pd
from linetests.records import size_check
import lines_sydney, lines_tokyo
rows = []
for city, mod in [("Sydney", lines_sydney), ("Tokyo", lines_tokyo)]:
    T, L = mod.build()
    for k, l in L.items():
        a = size_check(T, l, R=200, B=99, seed=1); b = size_check(T, l, R=200, B=99, seed=2, nogeo=True)
        rows.append(dict(city=city, line=k, size_random_layout=a, size_no_geography=b)); print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv("audit_data_size.csv", index=False)
