"""S2 (HYPOTHESES.md, 20 Nov 2026): is river-flood risk a line, or a slope? Same calibrated landscape test as every other map.

Usage: python experiments/safety_lines.py [city ...]   ->  results/safety/s2_flood_lines.csv
"""
import json, sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.stats import norm, rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "pipeline")]
from cities import CITIES  # noqa: E402
from linetests.landscape import MultiScaleNull, calibrated_map_test  # noqa: E402

rz = lambda v: norm.ppf((rankdata(v) - 0.5) / len(v))
OUT = ROOT / "results/safety/s2_flood_lines.csv"
done = pd.read_csv(OUT) if OUT.exists() else pd.DataFrame(columns=["city"])
rows = done.to_dict("records")
cities = sys.argv[1:] or sorted(p.stem for p in (ROOT / "results/safety").glob("*.json"))
for c in cities:
    if c in set(done.city):
        continue
    R = json.load(open(ROOT / f"results/safety/{c}.json", encoding="utf-8"))
    f = np.array(R["areas"].get("flood", []), float)
    if len(f) == 0 or (f > 0).mean() < 0.05:
        rows.append(dict(city=c, share_any=float((f > 0).mean()) if len(f) else 0, p=None, note="too little flood land to test"))
        pd.DataFrame(rows).to_csv(OUT, index=False); continue
    D = json.load(open(ROOT / f"app/data/{c}.json", encoding="utf-8")); mk = D["make"]
    A = gpd.read_file(ROOT / f"app/public/downloads/{c}_areas.geojson").to_crs(CITIES[c]["crs"])
    GN = MultiScaleNull(A.geometry, mk["I"], mk["J"], np.array(mk["L"]) * 1000, m=25)
    r = calibrated_map_test(GN, rz(f), B=199, R=40, Bin=99, seed=3); Rn = 40
    if r["p_cal"] < 0.1:
        r = calibrated_map_test(GN, rz(f), B=199, R=200, Bin=99, seed=3); Rn = 200
    rows.append(dict(city=c, share_any=round(float((f > 0).mean()), 3), p=round(float(r["p_cal"]), 3), p_raw=round(float(r["p_raw"]), 3),
                     cleanness=round(float(r["cleanness"]), 3), null_mean=round(float(r["null_mean"]), 3), ell_km=r["ell_km"], R=Rn))
    print(c, rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(OUT, index=False)
