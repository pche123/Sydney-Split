"""Korea (Seoul, Busan): line tests, centre-to-edge slopes and sister cities (K1-K4 in HYPOTHESES.md).

    python experiments/korea_analysis.py <Phase 1 cities folder with <city>/{areas.gpkg,fields.npz}>

Sisters use the two slopes every city has (Grey, Living Alone). Phase 1 cities enter with their app fields
(Grey = 65+ share; Living Alone = living alone minus families, same direction). Writes results/phase3/korea.json.
"""
import json, os, sys
import numpy as np, pandas as pd, geopandas as gpd
from scipy.stats import norm, rankdata
from shapely.geometry import box
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path[:0] = [ROOT]
from linetests.landscape import MultiScaleNull
OUT = os.path.join(ROOT, "results", "phase3"); P1 = sys.argv[1]
rz = lambda v: norm.ppf((rankdata(v) - 0.5) / len(v)); sp = lambda a, b: pd.Series(np.asarray(a)).corr(pd.Series(np.asarray(b)), method="spearman")
res = {"tests": [], "slopes": {}}
for city in ("seoul", "busan"):
    d = pd.read_csv(os.path.join(OUT, f"{city}_cells.csv.gz")); w = d.ref_pop.values
    dist = np.hypot(d.x + 500 - np.average(d.x + 500, weights=w), d.y + 500 - np.average(d.y + 500, weights=w))
    key = {(a, b): i for i, (a, b) in enumerate(zip(d.x, d.y))}
    I, J = np.array([(i, key[(a + dx, b + dy)]) for i, (a, b) in enumerate(zip(d.x, d.y)) for dx, dy in ((1000, 0), (0, 1000)) if (a + dx, b + dy) in key]).T
    GN = MultiScaleNull(gpd.GeoSeries([box(a, b, a + 1000, b + 1000) for a, b in zip(d.x, d.y)]), I, J, np.full(len(I), 1000.0), m=9)
    ps = []
    for var in ("grey", "alone", "apartment"):
        f = (d[f"num_{var}_2024"] / d[f"den_{var}_2024"].where(d[f"den_{var}_2024"] > 0)).values; ok = np.isfinite(f)
        res["slopes"][f"{city}_{var}"] = sp(f[ok], dist[ok])
        g = np.where(ok, f, np.nanmedian(f)) + 1e-9 * np.random.default_rng(0).normal(size=len(f))
        p, obs, nm, par = GN.test(rz(g), 199, seed=3); ps.append(p)
        res["tests"].append(dict(city=city, line=var, cells=len(d), missing=float(1 - ok.mean()), p=float(p), ell_km=float(par["ell"]), slope=res["slopes"][f"{city}_{var}"]))
    o = np.argsort(ps); run = 0
    for i, ix in enumerate(o):
        run = max(run, min(1, (len(ps) - i) * ps[ix])); res["tests"][-3 + ix]["p_holm"] = float(run)
# sisters on (grey, alone)
S = pd.read_csv(os.path.join(OUT, "sisters.csv"), index_col=0)[["country", "grey", "alone"]]
P1C = {"Japan": ["osaka", "nagoya", "kyoto", "kobe", "yokohama", "fukuoka", "sapporo"], "England": ["london", "manchester", "birmingham", "liverpool", "brighton"],
       "Australia": ["melbourne", "brisbane", "perth", "adelaide"]}
for country, cs in P1C.items():
    for c in cs:
        g = gpd.read_file(f"{P1}/{c}/areas.gpkg"); z = np.load(f"{P1}/{c}/fields.npz", allow_pickle=True); ids = list(z["ids"])
        ce = g.geometry.centroid; pw = g.population.astype(float).values if "population" in g else np.ones(len(g))
        dist = np.hypot(ce.x - np.average(ce.x, weights=pw), ce.y - np.average(ce.y, weights=pw))
        S.loc[c] = [country, sp(z["F"][:, ids.index("the-grey-line")], dist), sp(z["F"][:, ids.index("the-living-alone-line")], dist)]
for c in ("seoul", "busan"): S.loc[c] = ["Korea", res["slopes"][f"{c}_grey"], res["slopes"][f"{c}_alone"]]
X = S[["grey", "alone"]].astype(float).values; D = np.linalg.norm(X[:, None] - X[None], axis=2); np.fill_diagonal(D, np.inf)
near = D.argmin(1); S["sister"] = S.index.values[near]; S["distance"] = D.min(1)
res["sisters"] = {c: dict(sister=S.loc[c, "sister"], country=S.loc[S.loc[c, "sister"], "country"], distance=float(S.loc[c, "distance"]),
                          next3=list(S.index.values[np.argsort(D[list(S.index).index(c)])[:3]])) for c in ("seoul", "busan")}
lab = S.country.values; same = float((lab[near] == lab).mean()); rng = np.random.default_rng(5)
perm = [(lambda l: (l[near] == l).mean())(rng.permutation(lab)) for _ in range(9999)]
res["same_country_two_slopes"] = dict(share=same, n=len(S), p=float((1 + sum(x >= same for x in perm)) / 10000))
S.to_csv(os.path.join(OUT, "sisters_two_slopes.csv")); json.dump(res, open(os.path.join(OUT, "korea.json"), "w"), indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
