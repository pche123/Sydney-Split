"""Calibrated border test for Madrid's north-south divide (B1): the single-fit p is checked against R refits.

    python experiments/border_calibrated.py [R]

Same match statistic and 999-draw single-fit p as experiments/phase2_es_it.py. Calibration as for the line test:
simulate a map from the fitted landscape, refit, recompute its border p (199 draws); the calibrated p is the share of
those refit p-values at or below the real one. Checkpointed after every refit.
"""
import json, os, sys
import numpy as np, geopandas as gpd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path[:0] = [ROOT]
from linetests.landscape import MultiScaleNull

R = int(sys.argv[1]) if len(sys.argv) > 1 else 200
D = os.path.join(ROOT, "results", "phase2", "es_it"); ST = os.path.join(D, "madrid_border_calibrated.json")
C = gpd.read_file(os.path.join(D, "madrid_cells.gpkg")); z = np.load(os.path.join(D, "madrid", "fields.npz"))
inside = ((C.CPRO.astype(str).str.zfill(2) == "28") & (C.CMUN.astype(str).str.zfill(3) == "079")).values
south = C.CDIS.astype(str).str.zfill(2).isin(["10", "11", "12", "13", "17", "18", "19"]).values
GN = MultiScaleNull(C.geometry, z["I"], z["J"], z["W"], m=25)


def match(v):
    s = v[inside] > np.median(v[inside]); t = south[inside]; return max((s == t).mean(), (s != t).mean())


def border_p(f, B, rng):
    S = GN.simulate(GN.fit(f), B, rng); return (1 + sum(match(S[:, b]) >= match(f) for b in range(B))) / (B + 1)


state = json.load(open(ST)) if os.path.exists(ST) else {}
for lid in ("the-degree-line", "the-jobless-line"):
    f = C[lid].values.astype(float); s = state.setdefault(lid, {"ps": []})
    if "p_raw" not in s:
        s["p_raw"] = float(border_p(f, 999, np.random.default_rng(2026))); s["match"] = float(match(f))
    par = GN.fit(f)
    while len(s["ps"]) < R:
        r = len(s["ps"]); rng = np.random.default_rng([5, r])
        s["ps"].append(float(border_p(GN.simulate(par, 1, rng)[:, 0], 199, rng)))
        json.dump(state, open(ST, "w"))
        if r % 20 == 19: print(lid, r + 1, "refits", flush=True)
    ps = np.array(s["ps"][:R]); s["p_cal"] = float((1 + (ps <= s["p_raw"]).sum()) / (R + 1)); s["size_at_05"] = float((ps <= 0.05).mean())
    json.dump(state, open(ST, "w"))
    print(f"{lid}: match {s['match']:.0%}, single-fit p {s['p_raw']:.3f}, calibrated p {s['p_cal']:.3f} (R = {R}); "
          f"refit maps with no border called significant {s['size_at_05']:.0%} of the time", flush=True)
