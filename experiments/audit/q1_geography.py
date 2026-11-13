import os, sys; _H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [_H, os.path.dirname(_H), os.path.join(os.path.dirname(_H), "..")]  # experiments, repo root
from paths import SYD, TOK, RAW  # noqa: E402
"""Q1: is there any geography?  Records re-drawn with NO spatial variation (flat surfaces at the
city-wide level), pushed through the app's recipe; p = how often a flat world gives a border
this short.  Census maps: shuffle area values."""
import numpy as np, pandas as pd
import lines_sydney, lines_tokyo, lines_chains
rows = []
for city, builds in [("Sydney", [lines_sydney.build, lines_chains.sydney]), ("Tokyo", [lines_tokyo.build, lines_chains.tokyo])]:
    for b in builds:
        T, L = b()
        for k, l in L.items():
            rng = np.random.default_rng(1); obs = T.cut(l.field + 1e-9 * rng.standard_normal(T.n))[0]
            flat = [np.full_like(s, np.average(s, weights=1 / v)) for s, v in zip(l.surfaces, l.svar)]
            null = np.array([T.cut(l.sim(flat, rng) + 1e-9 * rng.standard_normal(T.n))[0] for _ in range(499)])
            rows.append(dict(city=city, line=k, p_geography=(1 + (null <= obs).sum()) / 500)); print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv("q1_geography.csv", index=False)
