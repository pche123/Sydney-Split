"""Time questions T1-T3 for Berlin, Munich and Hamburg: Zensus 2011 (100 m grid) vs Zensus 2022, on the Phase 2 1 km cells.

    python experiments/time_germany.py <folder with the cut 2011 grid CSVs>

2011: 65+ = ALTER_KURZ 5 / persons; living alone = 1-person households / households;
renters = rented occupied dwellings / (owned + rented occupied). 2022: the Phase 2 fields (normal scores).
"""
import os, sys
import numpy as np, pandas as pd, geopandas as gpd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); IN = sys.argv[1]
OUT = os.path.join(ROOT, "results", "time"); os.makedirs(OUT, exist_ok=True)


def read(name, want):
    d = pd.read_csv(f"{IN}/{name}", sep=None, engine="python" if name.startswith("Bev") else "c", usecols=[0, 2, 3, 5]) \
        if False else pd.read_csv(f"{IN}/{name}", sep=";" if name.startswith("Bev") else ",", usecols=[0, 2, 3, 5], encoding="latin1")
    d.columns = ["id", "m", "c", "n"]; d["m"] = d.m.astype(str).str.strip().str.strip('"').str.strip()
    d["c"] = pd.to_numeric(d.c, errors="coerce"); d["n"] = pd.to_numeric(d.n, errors="coerce").fillna(0)
    d = d[d.apply(lambda r: (r.m, r.c) in want, axis=1)] if len(d) < 0 else d[[(m, c) in want for m, c in zip(d.m, d.c)]]
    y = d.id.str.extract(r"N(\d+)E")[0].astype(int) * 100; x = d.id.str.extract(r"E(\d+)")[0].astype(int) * 100
    d["x"] = (x // 1000) * 1000; d["y"] = (y // 1000) * 1000; d["k"] = list(zip(d.m, d.c))
    return d.groupby(["x", "y", "k"]).n.sum().unstack("k").fillna(0)


P = read("Bevoelkerung100M.csv", {("INSGESAMT", 0), ("ALTER_KURZ", 5)})
H = read("Haushalte100m.csv", {("INSGESAMT", 0), ("HHGROESS_KLASS", 1)})
Wn = read("Wohnungen100m.csv", {("NUTZUNG_DETAIL_HHGEN", 11), ("NUTZUNG_DETAIL_HHGEN", 21)})
V11 = pd.DataFrame({"grey": P[("ALTER_KURZ", 5)] / P[("INSGESAMT", 0)].clip(lower=1)}) \
    .join(pd.DataFrame({"alone": H[("HHGROESS_KLASS", 1)] / H[("INSGESAMT", 0)].clip(lower=1)}), how="outer") \
    .join(pd.DataFrame({"renters": Wn[("NUTZUNG_DETAIL_HHGEN", 21)] / (Wn[("NUTZUNG_DETAIL_HHGEN", 11)] + Wn[("NUTZUNG_DETAIL_HHGEN", 21)]).clip(lower=1)}), how="outer")
NOW = {"grey": "the-grey-line", "alone": "the-living-alone-line", "renters": "the-renters-line"}
rows, AREAS = [], []
for city in ("berlin", "munich", "hamburg"):
    g = gpd.read_file(os.path.join(ROOT, "results", "phase2", "germany", f"{city}_cells.gpkg"))
    b = g.bounds; key = list(zip(b.minx.round().astype(int), b.miny.round().astype(int)))
    old = V11.reindex(pd.MultiIndex.from_tuples(key, names=["x", "y"]))
    c = g.geometry.centroid; cx, cy = np.average(c.x, weights=g["pop"]), np.average(c.y, weights=g["pop"])
    dist = pd.Series(np.hypot(c.x - cx, c.y - cy).values)
    AREAS.append(pd.DataFrame({"city": city, "x": c.x.values, "y": c.y.values, "dist": dist.values,
                               **{f"{v}_2011": old[v].values for v in NOW}, **{f"{v}_2022": g[col].values for v, col in NOW.items()}}))
    for var, col in NOW.items():
        a = pd.Series(old[var].values); n = pd.Series(g[col].values); ok = a.notna()
        s0 = a[ok] > a[ok].median(); s1 = n[ok] > n[ok].median()
        rows.append(dict(city=city, var=var, cells=int(ok.sum()), agree_2011_2022=float((s0 == s1).mean()),
                         spearman=a[ok].corr(n[ok], method="spearman"),
                         rho_dist_2011=a[ok].corr(dist[ok], method="spearman"), rho_dist_2022=n[ok].corr(dist[ok], method="spearman")))
pd.concat(AREAS).to_csv(os.path.join(OUT, "germany_areas.csv.gz"), index=False)
R = pd.DataFrame(rows); R.to_csv(os.path.join(OUT, "germany.csv"), index=False); print(R.round(2).to_string())
