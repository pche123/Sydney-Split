"""Why is the landscape test too eager in very large cities? Does fitting under-estimate the broadest scales?

    python experiments/scale_recovery.py <city> <cities folder> <n_maps> [out.csv]

Maps are drawn as in the benchmark (random mix of landscape scales, known weights). For each map we fit the landscape
and compare, under the true and the fitted weights:
  broad share  share of variance at the two broadest scales (25 and 50 km)
  null border  mean border length of the median split over 200 simulated maps, in units of its SD under the truth.
A positive border bias means the fitted null is rougher than the truth, so real maps look cleaner than they are:
the test calls lines too often.
"""
import os, sys
import numpy as np, pandas as pd, geopandas as gpd
from scipy.stats import norm, rankdata
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.join(HERE, ".."), os.path.join(HERE, "..", "pipeline")]
from linetests.landscape import MultiScaleNull
from cities import CITIES

city, CI, N = sys.argv[1], sys.argv[2], int(sys.argv[3])
OUT = sys.argv[4] if len(sys.argv) > 4 else os.path.join(HERE, "..", "results", "phase1", f"scale_recovery_{city}.csv")
G = gpd.read_file(f"{CI}/{city}/areas.gpkg").to_crs(CITIES[city]["crs"]).reset_index(drop=True)
z = np.load(f"{CI}/{city}/fields.npz"); I, J, W = z["I"], z["J"], z["W"]
MS = MultiScaleNull(G.geometry, I, J, W, m=25 if len(G) < 600 else 9)
rng = np.random.default_rng(42); rn = lambda v: norm.ppf((rankdata(v) - 0.5) / len(v))
def border(F): S = F > np.median(F, 0); return ((S[I] != S[J]) * W[:, None]).sum(0) / (0.5 * W.sum())
def broad(a): return a[-3:-1].sum() / a.sum()          # 25 and 50 km of (0.7 ... 50 km, noise)
rows = []
for k in range(N):
    a = rng.dirichlet(np.ones(len(MS.Ks)) * 0.7); a[-1] *= 0.3; a = a / a.sum()
    f = rn(MS.simulate({"weights": a}, 1, rng)[:, 0]); par = MS.fit(f); af = par["weights"] / par["weights"].sum()
    bt = border(MS.simulate({"weights": a}, 200, rng)); bf = border(MS.simulate({"weights": af}, 200, rng))
    rows.append(dict(city=city, rep=k, broad_true=broad(a), broad_fit=broad(af), border_true=bt.mean(), border_fit=bf.mean(),
                     bias_sd=(bf.mean() - bt.mean()) / bt.std(), obs_border=border(f[:, None])[0]))
    pd.DataFrame(rows).to_csv(OUT, index=False)
d = pd.DataFrame(rows)
print(f"{city}: broad-scale share true {d.broad_true.mean():.2f} vs fitted {d.broad_fit.mean():.2f}; "
      f"null border bias {d.bias_sd.mean():+.2f} SD (median {d.bias_sd.median():+.2f}); maps {len(d)}")
