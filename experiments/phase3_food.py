"""Phase 3 meme lines (pre-registered in HYPOTHESES.md): Latte / Snackbar vs Koffiebar / Fika (cafés vs fast food) in the
nine European cities and São Paulo, and Coffee vs Churrasco in São Paulo. Same 1 km cells and quick test as phase3_analysis.py.

    python experiments/phase3_food.py <folder with <city>/places.csv>
"""
import ast, os, sys
import numpy as np, pandas as pd, geopandas as gpd
from pyproj import Transformer
from scipy.stats import norm, rankdata
from shapely.geometry import box
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path[:0] = [ROOT]
from linetests.landscape import MultiScaleNull
OUT = os.path.join(ROOT, "results", "phase3")
NL, SE, DK = ["amsterdam", "rotterdam", "thehague", "utrecht"], ["stockholm", "gothenburg", "malmo"], ["copenhagen", "aarhus"]
CRS = {**{c: 28992 for c in NL}, **{c: 3006 for c in SE}, **{c: 3035 for c in DK}, "saopaulo": 31983}
NAME = {"thehague": "The Hague", "malmo": "Malmö", "saopaulo": "São Paulo"}
rz = lambda v: norm.ppf((rankdata(v) - 0.5) / len(v))
rows = []
for city in NL + SE + DK + ["saopaulo"]:
    d = pd.read_csv(os.path.join(OUT, f"{city}_cells.csv.gz"))
    P = pd.read_csv(f"{sys.argv[1]}/{city}/places.csv"); T = P.tags.map(ast.literal_eval)
    g = lambda k: T.map(lambda t: str(t.get(k, "")).lower())
    am, cu, nm = g("amenity"), g("cuisine"), g("name")
    cafe, fast = (am == "cafe").values, (am == "fast_food").values
    churr = (am.isin(["restaurant", "fast_food"]) & (cu.str.contains("churrasco|steak_house|barbecue") | (cu.str.contains("brazilian") & nm.str.contains("churrasc")))).values
    X, Y = Transformer.from_crs(4326, CRS[city], always_xy=True).transform(P.lon.values, P.lat.values)
    key = {(a, b): i for i, (a, b) in enumerate(zip(d.x, d.y))}
    idx = np.array([key.get((int(np.floor(a / 1000) * 1000), int(np.floor(b / 1000) * 1000)), -1) for a, b in zip(X, Y)])
    cnt = lambda m: np.bincount(idx[m & (idx >= 0)], minlength=len(d))
    E = [(i, key[(a + dx, b + dy)]) for i, (a, b) in enumerate(zip(d.x, d.y)) for dx, dy in ((1000, 0), (0, 1000)) if (a + dx, b + dy) in key]
    I, J = np.array(E).T
    GN = MultiScaleNull(gpd.GeoSeries([box(a, b, a + 1000, b + 1000) for a, b in zip(d.x, d.y)]), I, J, np.full(len(I), 1000.0), m=9)
    w = d.ref_pop.values; dist = np.hypot(d.x - np.average(d.x, weights=w), d.y - np.average(d.y, weights=w))
    lines = [("Latte (cafés vs fast food)", cnt(cafe), cnt(fast))]
    if city == "saopaulo": lines.append(("Coffee vs Churrasco", cnt(cafe), cnt(churr)))
    for line, A, B in lines:
        f = np.log((A + 0.5) / (B + 0.5)) + 1e-9 * np.random.default_rng(0).normal(size=len(d))
        p = GN.test(rz(f), 199, seed=11)[0]
        rho = pd.Series(f).corr(pd.Series(dist), method="spearman")
        rows.append(dict(city=NAME.get(city, city.capitalize()), line=line, A=int(A.sum()), B=int(B.sum()), cells=len(d), p=p, slope_vs_distance=rho))
        print(rows[-1], flush=True)
R = pd.DataFrame(rows)
o = np.argsort(R.p.values); k = len(R); h = np.empty(k); run = 0
for i, ix in enumerate(o): run = max(run, min(1, (k - i) * R.p.values[ix])); h[ix] = run
R["holm_all"] = h
L = R[R.line.str.startswith("Latte") & (R.city != "São Paulo")]; Z = norm.isf(L.p.clip(1e-6, 1 - 1e-6)).sum() / np.sqrt(len(L))
print(R.round(3).to_string(index=False)); print(f"Latte pooled over 9 European cities: Stouffer Z = {Z:.2f}, p = {norm.sf(Z):.3g}")
R.to_csv(os.path.join(OUT, "food_lines.csv"), index=False)
