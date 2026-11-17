"""Calibrated check of the one Phase 3 line that passed its quick test: Aarhus grey (65+ share, 2021). R = 200 refits."""
import json, os, sys
import numpy as np, pandas as pd, geopandas as gpd
from scipy.stats import norm, rankdata
from shapely.geometry import box
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path[:0] = [ROOT]
from linetests.landscape import MultiScaleNull, calibrated_map_test
d = pd.read_csv(os.path.join(ROOT, "results", "phase3", "aarhus_cells.csv.gz"))
col = [c for c in d.columns if c.startswith("num_grey_")][-1]; f = (d[col] / d[col.replace("num_", "den_")]).values
f = np.where(np.isfinite(f), f, np.nanmedian(f)); f = norm.ppf((rankdata(f + 1e-9 * np.random.default_rng(0).normal(size=len(f))) - 0.5) / len(f))
key = {(a, b): i for i, (a, b) in enumerate(zip(d.x, d.y))}
I, J = np.array([(i, key[(a + dx, b + dy)]) for i, (a, b) in enumerate(zip(d.x, d.y)) for dx, dy in ((1000, 0), (0, 1000)) if (a + dx, b + dy) in key]).T
GN = MultiScaleNull(gpd.GeoSeries([box(a, b, a + 1000, b + 1000) for a, b in zip(d.x, d.y)]), I, J, np.full(len(I), 1000.0), m=9)
r = calibrated_map_test(GN, f, B=199, R=200, Bin=99, seed=3); print(r)
json.dump({k: (float(v) if isinstance(v, (float, np.floating)) else v) for k, v in r.items()}, open(os.path.join(ROOT, "results", "phase3", "aarhus_grey_calibrated.json"), "w"), indent=1)
