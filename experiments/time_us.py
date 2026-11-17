"""Time questions T1-T3 for the eight Phase 1 US cities: NHGIS tracts standardized to 2010, 1990-2020.

    python experiments/time_us.py <folder with the two NHGIS csvs and US_tract_2010.dbf>

Tracts: 2010 tracts whose internal point lies in the city's Phase 1 box, >= 500 residents in 2010.
65+ = CW3 AR..AV / CL8; living alone = CS4AA / CM4AA; renters = CN1AB / (CN1AA + CN1AB).
"""
import glob, os, sys
import numpy as np, pandas as pd, geopandas as gpd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path[:0] = [os.path.join(ROOT, "pipeline")]
from cities import CITIES
IN = sys.argv[1]; OUT = os.path.join(ROOT, "results", "time"); os.makedirs(OUT, exist_ok=True)
Y = ("1990", "2000", "2010", "2020")
need = ["CL8AA", "CM4AA", "CS4AA", "CN1AA", "CN1AB"] + [f"CW3A{c}" for c in "RSTUV"]
cols = lambda f: [c for c in pd.read_csv(f, nrows=0, encoding="latin1").columns if c[:5] in need and c[5:] in Y]
D = None
for f in sorted(glob.glob(f"{IN}/nhgis*_tract.csv")):
    d = pd.read_csv(f, encoding="latin1", skiprows=[1], usecols=["GISJOIN"] + cols(f), low_memory=False)
    D = d if D is None else D.merge(d[["GISJOIN"] + [c for c in d.columns if c not in D.columns]], on="GISJOIN")
pts = gpd.read_file(f"{IN}/US_tract_2010.dbf", ignore_geometry=True)
pts["lat"] = pts.INTPTLAT10.astype(float); pts["lon"] = pts.INTPTLON10.astype(float)
D = D.merge(pts[["GISJOIN", "lat", "lon"]], on="GISJOIN")
rows, pairs, AREAS = [], [], []
for city, C in CITIES.items():
    if C.get("country") != "us": continue
    w, s, e, n = C["bbox"]; T = D[(D.lon.between(w, e)) & (D.lat.between(s, n)) & (D.CL8AA2010 >= 500)].reset_index(drop=True)
    g = gpd.GeoSeries(gpd.points_from_xy(T.lon, T.lat), crs=4326).to_crs(C["crs"])
    pop = T.CL8AA2010.values; cx, cy = np.average(g.x, weights=pop), np.average(g.y, weights=pop)
    dist = pd.Series(np.hypot(g.x - cx, g.y - cy))
    V = {}
    for y in Y:
        V[("grey", y)] = sum(T[f"CW3A{c}{y}"] for c in "RSTUV") / T[f"CL8AA{y}"].clip(lower=1)
        V[("alone", y)] = T[f"CS4AA{y}"] / T[f"CM4AA{y}"].clip(lower=1)
        V[("renters", y)] = T[f"CN1AB{y}"] / (T[f"CN1AA{y}"] + T[f"CN1AB{y}"]).clip(lower=1)
    AREAS.append(pd.DataFrame({"city": city, "x": g.x.values, "y": g.y.values, "dist": dist.values,
                               **{f"{v}_{y}": V[(v, y)].values for (v, y) in V}}))
    for var in ("grey", "alone", "renters"):
        for y in Y:
            rows.append(dict(city=city, var=var, year=int(y), tracts=len(T), rho_dist=V[(var, y)].corr(dist, method="spearman")))
        for y0, y1 in (("1990", "2000"), ("2000", "2010"), ("2010", "2020"), ("1990", "2020")):
            a, b = V[(var, y0)], V[(var, y1)]
            pairs.append(dict(city=city, var=var, **{"from": int(y0)}, to=int(y1), agree=float(((a > a.median()) == (b > b.median())).mean()),
                              spearman=a.corr(b, method="spearman")))
R, Pp = pd.DataFrame(rows), pd.DataFrame(pairs)
pd.concat(AREAS).to_csv(os.path.join(OUT, "us_areas.csv.gz"), index=False)
R.to_csv(os.path.join(OUT, "us.csv"), index=False); Pp.to_csv(os.path.join(OUT, "us_pairs.csv"), index=False)
print(R.pivot_table(index=["var", "city"], columns="year", values="rho_dist").round(2).to_string())
print(Pp.pivot_table(index=["var", "city"], columns=["from", "to"], values="agree").round(2).to_string())
print(R.groupby("city").tracts.first())
