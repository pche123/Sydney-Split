"""The Chippy Line (pre-registered in HYPOTHESES.md): chippies vs cafés in England's five test cities.

    python experiments/chippy_line.py <folder with cities/<city>/{areas.gpkg,fields.npz,raw/osm/places.csv}>
"""
import ast, os, sys
import numpy as np, pandas as pd, geopandas as gpd
from scipy.stats import norm, rankdata, spearmanr
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path[:0] = [ROOT]
from linetests.landscape import MultiScaleNull
rz = lambda v: norm.ppf((rankdata(v) - 0.5) / len(v))
rows = []
for city in ["london", "manchester", "birmingham", "liverpool", "brighton"]:
    d = f"{sys.argv[1]}/cities/{city}"
    G = gpd.read_file(f"{d}/areas.gpkg"); z = np.load(f"{d}/fields.npz", allow_pickle=True)
    P = pd.read_csv(f"{d}/raw/osm/places.csv"); T = P.tags.map(ast.literal_eval)
    am = T.map(lambda t: t.get("amenity", "")); cu = T.map(lambda t: t.get("cuisine", "").lower()); nm = T.map(lambda t: t.get("name", "").lower())
    chip = am.isin(["fast_food", "restaurant"]) & (cu.str.contains("fish_and_chips") | nm.str.contains("chip") | nm.str.contains("fish bar") | nm.str.contains("fish & chips"))
    cafe = am == "cafe"
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(P.lon, P.lat), crs=4326).to_crs(G.crs)
    j = gpd.sjoin(pts, G[["geometry"]], predicate="within", how="left")["index_right"]
    j = j[~j.index.duplicated()].reindex(P.index)
    A = np.bincount(j[chip & j.notna()].astype(int), minlength=len(G)); B = np.bincount(j[cafe & j.notna()].astype(int), minlength=len(G))
    f = np.log((A + 0.5) / (B + 0.5)) + 1e-9 * np.random.default_rng(0).normal(size=len(G))
    p = MultiScaleNull(G.geometry, z["I"], z["J"], z["W"], m=9).test(rz(f), 199, seed=11)[0]
    lat = z["F"][:, list(z["ids"]).index("the-latte-line")]
    r = spearmanr(f, lat).statistic
    rows.append(dict(city=city, chippies=int(A.sum()), cafes=int(B.sum()), chips_per_cafe=A.sum() / B.sum(), p=p, rho_latte=r))
R = pd.DataFrame(rows); o = np.argsort(R.p.values); k = len(R); h = np.empty(k); run = 0
for i, ix in enumerate(o): run = max(run, min(1, (k - i) * R.p.values[ix])); h[ix] = run
R["holm"] = h; Z = norm.isf(R.p.clip(1e-6, 1 - 1e-6)).sum() / np.sqrt(k)
print(R.round(3).to_string(index=False)); print(f"pooled Stouffer Z = {Z:.2f}, p = {norm.sf(Z):.3g}")
os.makedirs(os.path.join(ROOT, "results", "chippy"), exist_ok=True); R.to_csv(os.path.join(ROOT, "results", "chippy", "chippy_line.csv"), index=False)
