"""The double-check: re-test every line of a city with the calibrated landscape test (double bootstrap), then update the app.

    python pipeline/common/calibrate.py melbourne work/melbourne app/data/melbourne.json [R]

Uses the fields build_app.py saved (fields.npz). Census and venue lines get calibrated_map_test (fit, simulate,
then R refits on simulated maps to calibrate the p-value). Chain wars keep their exact label-swap p-value.
Results go to results/calibrated_<city>.csv; the app file gets the calibrated, Holm-corrected p and verdict.
"""
import json, os, sys, time
import numpy as np, pandas as pd, geopandas as gpd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path[:0] = [os.path.join(HERE, ".."), ROOT]
from cities import CITIES
from linetests.landscape import MultiScaleNull, calibrated_map_test
from scipy.stats import norm, rankdata

city, W_, APP = sys.argv[1:4]; R = int(sys.argv[4]) if len(sys.argv) > 4 else 40
C = CITIES[city]
G = gpd.read_file(f"{W_}/areas.gpkg").to_crs(C["crs"]).reset_index(drop=True)
z = np.load(f"{W_}/fields.npz"); I, J, W = z["I"], z["J"], z["W"]
GN = MultiScaleNull(G.geometry, I, J, W, m=25 if len(G) < 600 else 9)
rz = lambda v: norm.ppf((rankdata(v) - 0.5) / len(v))
out = os.environ.get("CAL_OUT", f"{ROOT}/results/calibrated_{city}.csv"); rows = []   # CAL_OUT, CAL_ONLY: split one city across processes, then merge
done = set(pd.read_csv(out).line) if os.path.exists(out) else set()
if done: rows = pd.read_csv(out).to_dict("records")
R_FINE = 60 if city == "london" else 200   # London is 5x bigger, so it gets fewer refits. With R refits the smallest calibrated p is 1/(R+1); close calls get R_FINE so Holm can still pass them
ONLY = set(os.environ["CAL_ONLY"].split(",")) if os.environ.get("CAL_ONLY") else None
for lid, kind, f in zip(z["ids"], z["kinds"], z["F"].T):
    if kind == "chain" or (ONLY and lid not in ONLY): continue
    prev = next((r for r in rows if r["line"] == lid), None)
    if prev is not None and (prev["p_cal"] >= 0.1 or prev.get("R", R) >= R_FINE): continue
    for R_ in ([R] if prev is None else []) + [R_FINE]:
        t = time.time(); r = calibrated_map_test(GN, rz(f), B=199, R=R_, Bin=99, seed=3)
        r.update(line=lid, kind=kind, R=R_); rows = [q for q in rows if q["line"] != lid] + [r]; pd.DataFrame(rows).to_csv(out, index=False)
        print(f"{city} {lid:32s} raw {r['p_raw']:.3f} calibrated {r['p_cal']:.3f} R={R_} ({time.time() - t:.0f}s)", flush=True)
        if r["p_cal"] >= 0.1: break

# update the app: calibrated p, Holm within group, verdicts
d = json.load(open(APP)); cal = {r["line"]: r["p_cal"] for r in rows}
def holm(p):
    p = np.asarray(p, float); o = np.argsort(p); m = len(p); res = np.empty(m); run = 0
    for k, i in enumerate(o): run = max(run, (m - k) * p[i]); res[i] = min(1, run)
    return res
for grp in {l["group"] for l in d["lines"]} - {"Chains"}:     # chain wars keep their exact label-swap p (already corrected)
    ls = [l for l in d["lines"] if l["group"] == grp and l["id"] in cal]
    for l, q in zip(ls, holm([cal[l["id"]] for l in ls])):
        if not d["meta"].get("calibrated"): l["p_old"] = l["p"]
        l["p"] = round(float(q), 3)
        geo = l.get("p_geo") is None or l["p_geo"] <= 0.05
        l["tier"] = "line" if l["p"] <= 0.05 else ("gentle" if geo else "chance")
d["meta"]["calibrated"] = True
json.dump(d, open(APP, "w"), separators=(",", ":"), ensure_ascii=False)
print(city, "app updated:", sum(l["tier"] == "line" for l in d["lines"]), "real lines,", sum(l["tier"] == "gentle" for l in d["lines"]), "gentle")
