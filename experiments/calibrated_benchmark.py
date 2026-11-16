"""False alarms of the calibrated (double-bootstrap) landscape test, the version every verdict uses.

    python experiments/calibrated_benchmark.py <city> <cities folder> <n_maps> <seed> [out.csv]

The null benchmark (null_benchmark.py) scores the single-fit test, which is quick but plugs in the fitted smoothness
and so can be too eager. Here each map with no line gets calibrated_map_test exactly as the app runs it (B=199, R=40, Bin=99; R=200 when p < 0.1).
Maps are drawn exactly as in null_benchmark.py's "stationary" scenario (random mix of landscape scales).
"""
import os, sys, time
import numpy as np, pandas as pd, geopandas as gpd
from scipy.stats import norm, rankdata
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.join(HERE, ".."), os.path.join(HERE, "..", "pipeline")]
from linetests.landscape import MultiScaleNull, calibrated_map_test
from cities import CITIES

city, CI, N, seed = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
OUT = sys.argv[5] if len(sys.argv) > 5 else os.path.join(HERE, "..", "results", "phase1", f"calibrated_benchmark_{city}_{seed}.csv")
G = gpd.read_file(f"{CI}/{city}/areas.gpkg").to_crs(CITIES[city]["crs"]).reset_index(drop=True)
z = np.load(f"{CI}/{city}/fields.npz"); I, J, W = z["I"], z["J"], z["W"]
MS = MultiScaleNull(G.geometry, I, J, W, m=25 if len(G) < 600 else 9)
rng = np.random.default_rng(seed); rn = lambda v: norm.ppf((rankdata(v) - 0.5) / len(v))
rows = pd.read_csv(OUT).to_dict("records") if os.path.exists(OUT) else []
for k in range(len(rows), N):
    a = rng.dirichlet(np.ones(len(MS.Ks)) * 0.7); a[-1] *= 0.3
    f = rn(MS.simulate({"weights": a}, 1, rng)[:, 0])
    t = time.time(); sd = int(rng.integers(1e9)); r = calibrated_map_test(MS, f, B=199, R=40, Bin=99, seed=sd); R_ = 40
    if r["p_cal"] < 0.1:   # as the app does (calibrate.py): close calls get 200 refits before a verdict
        r = calibrated_map_test(MS, f, B=199, R=200, Bin=99, seed=sd); R_ = 200
    rows.append(dict(city=city, rep=k, p_raw=r["p_raw"], p_cal=r["p_cal"], R=R_)); pd.DataFrame(rows).to_csv(OUT, index=False)
    d = pd.DataFrame(rows)
    print(f"{city} map {k + 1}/{N} ({time.time() - t:.0f}s): false alarms raw {(d.p_raw <= 0.05).mean():.2f}, calibrated {(d.p_cal <= 0.05).mean():.2f}", flush=True)
