"""The calibrated test, checkpointed after every refit, for big cities on machines that restart.

    python experiments/calibrate_checkpoint.py <city> <work folder> <line,line,...> [R] [state.json]

Same procedure as linetests.landscape.calibrated_map_test (B = 199 draws, R refits of Bin = 99 draws, seed 3 as in
pipeline/common/calibrate.py), but each refit's p is saved as soon as it is done, so a restart loses at most one.
Prints the running calibrated p after each refit.
"""
import json, os, sys
import numpy as np, geopandas as gpd
from scipy.stats import norm, rankdata

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path[:0] = [ROOT, os.path.join(ROOT, "pipeline")]
from linetests.landscape import MultiScaleNull
from cities import CITIES

city, W_, lines = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
R = int(sys.argv[4]) if len(sys.argv) > 4 else 40
ST = sys.argv[5] if len(sys.argv) > 5 else os.path.join(ROOT, "results", f"calibrated_{city}_checkpoint.json")
state = json.load(open(ST)) if os.path.exists(ST) else {}
G = gpd.read_file(f"{W_}/areas.gpkg").to_crs(CITIES[city]["crs"]).reset_index(drop=True)
z = np.load(f"{W_}/fields.npz"); ids = list(z["ids"])
GN = MultiScaleNull(G.geometry, z["I"], z["J"], z["W"], m=25 if len(G) < 600 else 9)
rz = lambda v: norm.ppf((rankdata(v) - 0.5) / len(v))
save = lambda: json.dump(state, open(ST + ".tmp", "w")) or os.replace(ST + ".tmp", ST)
for lid in lines:
    f = rz(z["F"][:, ids.index(lid)]); s = state.setdefault(lid, {"ps": []})
    if "p_raw" not in s:
        p_raw, obs, nm, par = GN.test(f, 199, seed=3)
        s.update(p_raw=float(p_raw), par={"weights": [float(a) for a in par["weights"]], "mu": float(par["mu"]), "sd": float(par["sd"]),
                                          "ell": par["ell"], "tau": par["tau"]}); save()
        print(f"{city} {lid}: raw p {p_raw:.3f}", flush=True)
    par = dict(s["par"]); par["weights"] = np.array(par["weights"])
    while len(s["ps"]) < R:
        r = len(s["ps"]); rng = np.random.default_rng([3, r])
        fr = GN.simulate(par, 1, rng)[:, 0]
        s["ps"].append(float(GN.test(fr, 99, seed=1000 + r)[0])); save()
        ps = np.array(s["ps"]); print(f"{city} {lid}: refit {len(ps)}/{R}, calibrated p so far {(1 + (ps <= s['p_raw']).sum()) / (len(ps) + 1):.3f}", flush=True)
    ps = np.array(s["ps"]); s["p_cal"] = float((1 + (ps <= s["p_raw"]).sum()) / (R + 1)); save()
    print(f"{city} {lid}: raw {s['p_raw']:.3f} calibrated {s['p_cal']:.3f} (R = {R})", flush=True)
