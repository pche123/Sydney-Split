"""Does a city's line follow a known border? (Paris: the Boulevard Périphérique; any city: any inside/outside split.)

    python experiments/border_match.py <areas.gpkg> <inside column> <line column> [line column ...]

The areas file holds one row per area: its polygon, a 0/1 column marking one side of the border (for Paris, IRIS
codes starting 751, i.e. the City of Paris inside the Périphérique), and one score column per line, plus
columns I, J, W are not needed: shared borders are rebuilt from the polygons. Each line's median split is compared
with the border (share of areas on the matching side), against 999 random cities just as smooth (the fitted
multi-scale landscape). Exploratory: reported either way, not a prediction. Berlin's Wall uses the same test inside
experiments/phase2_germany.py.
"""
import os, sys
import numpy as np, geopandas as gpd, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.join(HERE, "..")]
from linetests.landscape import MultiScaleNull

G = gpd.read_file(sys.argv[1]).reset_index(drop=True); inside = G[sys.argv[2]].astype(bool).values
pairs = gpd.sjoin(G[["geometry"]], G[["geometry"]], predicate="touches"); pairs = pairs[pairs.index < pairs.index_right]
E = [(i, j, G.geometry[i].boundary.intersection(G.geometry[j].boundary).length) for i, j in zip(pairs.index, pairs.index_right)]
E = np.array([e for e in E if e[2] > 0]); I, J, W = E[:, 0].astype(int), E[:, 1].astype(int), E[:, 2]
GN = MultiScaleNull(G.geometry, I, J, W, m=25 if len(G) < 600 else 9); rng = np.random.default_rng(1973)
match = lambda s: max((s == inside).mean(), (s != inside).mean())
for col in sys.argv[3:]:
    f = G[col].values.astype(float); f = (f - f.mean()) / f.std(); m = match(f > np.median(f))
    S = GN.simulate(GN.fit(f), 999, rng); null = np.array([match(S[:, b] > np.median(S[:, b])) for b in range(999)])
    print(f"{col:28s} {m:.0%} of areas on the matching side (random cities {null.mean():.0%}), p = {(1 + (null >= m).sum()) / 1000:.3f}")
