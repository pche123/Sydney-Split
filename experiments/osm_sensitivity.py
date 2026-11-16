"""Is the Latte Line just a map of how well OpenStreetMap is filled in, or of density?

    python experiments/osm_sensitivity.py [out.csv]

For every city with a work folder and a download table: the Latte Line's score against (a) mapping intensity,
log food venues per km², and (b) log residents per km² (Spearman). Then the score with both taken out
(rank-normal residual of a linear fit on their ranks) is tested with the same quick landscape test as the original,
and both are pooled over cities (Stouffer). If the line survives with mapping intensity and density removed,
it is not an artefact of uneven mapping, and it is not just density.
"""
import os, sys, glob
import numpy as np, pandas as pd, geopandas as gpd
from scipy.stats import norm, rankdata, spearmanr

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path[:0] = [ROOT, os.path.join(ROOT, "pipeline")]
from linetests.landscape import MultiScaleNull
from cities import CITIES

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "results", "osm_sensitivity.csv")
rz = lambda v: norm.ppf((rankdata(v) - 0.5) / len(v))
WORK = {**{c: f"/home/claude/cities_in/cities/{c}" for c in os.listdir("/home/claude/cities_in/cities")},
        **{c: f"/home/claude/work_p1/{c}" for c in os.listdir("/home/claude/work_p1")}}
HELD = {"newyork", "losangeles", "chicago", "sanfrancisco", "washington", "austin", "seattle", "miami", "auckland", "christchurch", "singapore"}
done = pd.read_csv(OUT) if os.path.exists(OUT) else pd.DataFrame(columns=["city"]); rows = done.to_dict("records")
for c in sorted(WORK):
    w = WORK[c]; dl = f"{ROOT}/app/public/downloads/{c}_areas.csv"
    if c in set(done.city) or not (os.path.exists(f"{w}/fields.npz") and os.path.exists(dl)): continue
    z = np.load(f"{w}/fields.npz"); ids = list(z["ids"])
    if "the-latte-line" not in ids: continue
    d = pd.read_csv(dl); G = gpd.read_file(f"{w}/areas.gpkg").to_crs(CITIES[c]["crs"]).reset_index(drop=True)
    assert len(d) == len(G) == z["F"].shape[0], c
    f = rz(z["F"][:, ids.index("the-latte-line")]); km2 = np.maximum(d.km2.values, 1e-3)
    vd = np.log((d.count_food.values + 1) / km2); pdn = np.log(np.maximum(d.population.values, 1) / km2)
    X = np.column_stack([np.ones(len(f)), rz(vd), rz(pdn)]); beta = np.linalg.lstsq(X, f, rcond=None)[0]; res = rz(f - X @ beta)
    GN = MultiScaleNull(G.geometry, z["I"], z["J"], z["W"], m=25 if len(G) < 600 else 9)
    p_raw = GN.test(f, 199, seed=5)[0]; p_res = GN.test(res, 199, seed=5)[0]
    r = dict(city=c, country=CITIES[c]["country"], held_out=c in HELD, areas=len(f), rho_mapping=spearmanr(f, vd)[0], rho_density=spearmanr(f, pdn)[0],
             r2_removed=1 - np.var(f - X @ beta) / np.var(f), p_latte=p_raw, p_latte_without=p_res)
    rows.append(r); pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"{c:13s} rho(mapping) {r['rho_mapping']:+.2f}  rho(density) {r['rho_density']:+.2f}  p {p_raw:.3f} -> {p_res:.3f}", flush=True)
R = pd.DataFrame(rows)
for lab, g in [("all", R), ("held out", R[R.held_out]), ("first 18", R[~R.held_out])]:
    for col in ["p_latte", "p_latte_without"]:
        zs = norm.isf(np.clip(g[col].values, 1e-3, 1 - 1e-3)); Z = zs.sum() / np.sqrt(len(zs))
        print(f"{lab:9s} {col:16s} cities {len(g):2d}  Stouffer Z = {Z:.2f}  p = {norm.sf(Z):.4f}")
