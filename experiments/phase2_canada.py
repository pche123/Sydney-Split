"""Canada census lines: Grey, Living Alone, Renters, Degree, Jobless on 1 km cells (mapping in HYPOTHESES.md).

    python experiments/phase2_canada.py <lda_000b21a_e.shp> <canada_small.csv.gz>

Writes results/phase2/canada/tests.csv, <city>_cells.gpkg and work folders (areas.gpkg, fields.npz) for calibration.
"""
import os, sys
import numpy as np, pandas as pd, geopandas as gpd
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from scipy.stats import norm, rankdata
from shapely.geometry import box

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path[:0] = [ROOT]
from linetests.landscape import MultiScaleNull

SHP, CSV = sys.argv[1], sys.argv[2]
OUT = os.path.join(ROOT, "results", "phase2", "canada"); os.makedirs(OUT, exist_ok=True)
BOX = {"toronto": (-79.64, 43.58, -79.11, 43.86), "ottawa": (-76.00, 45.20, -75.45, 45.55), "montreal": (-73.98, 45.40, -73.47, 45.71),
       "calgary": (-114.32, 50.84, -113.86, 51.21), "edmonton": (-113.72, 53.39, -113.27, 53.72)}
IDS = {1: "pop", 8: "age_tot", 24: "old", 50: "hh", 51: "alone", 1414: "ten", 1416: "rent", 1998: "p15", 2008: "deg", 2230: "unemp_rate"}
LINES = {"the-grey-line": ("old", "age_tot"), "the-living-alone-line": ("alone", "hh"), "the-renters-line": ("rent", "ten"),
         "the-degree-line": ("deg", "p15"), "the-jobless-line": ("unemp_w", "pop")}
rz = lambda v: norm.ppf((rankdata(v) - 0.5) / len(v))

V = pd.read_csv(CSV, dtype={"da": str}); V = V[V.cid.isin(IDS)]
V["value"] = pd.to_numeric(V.value, errors="coerce")
V = V.drop_duplicates(["da", "cid"]).pivot(index="da", columns="cid", values="value").rename(columns=IDS).fillna(0)
V["unemp_w"] = V.unemp_rate / 100 * V["pop"]          # population-weighted rate, so it can be shared between cells

DA = gpd.read_file(SHP, columns=["DAUID"])
rows = []
for city, bb in BOX.items():
    b = gpd.GeoSeries([box(*bb)], crs=4326).to_crs(DA.crs).iloc[0]
    sec = DA[DA.intersects(b)].merge(V, left_on="DAUID", right_index=True); sec["sa"] = sec.area
    x0, y0, x1, y1 = (np.floor(np.array(b.bounds) / 1000) * 1000).astype(int)
    xs = [(x, y) for x in range(x0, x1 + 1000, 1000) for y in range(y0, y1 + 1000, 1000)]
    grid = gpd.GeoDataFrame({"x": [a for a, _ in xs], "y": [c for _, c in xs]}, geometry=[box(a, c, a + 1000, c + 1000) for a, c in xs], crs=DA.crs)
    grid = grid[grid.intersects(b)]
    ov = gpd.overlay(sec, grid, how="intersection", keep_geom_type=True); w = ov.area / ov.sa
    cols = list(IDS.values())[:-1] + ["unemp_w"]
    xy = ov[cols].mul(w, axis=0).assign(x=ov.x, y=ov.y).groupby(["x", "y"]).sum().reset_index()
    xy = xy[xy["pop"] >= 1000].reset_index(drop=True)
    key = {(a, c): i for i, (a, c) in enumerate(zip(xy.x, xy.y))}
    nb = lambda: [(i, key[(a + dx, c + dy)]) for i, (a, c) in enumerate(zip(xy.x, xy.y)) for dx, dy in ((1000, 0), (0, 1000)) if (a + dx, c + dy) in key]
    E = np.array(nb()); _, lab = connected_components(sparse.coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), shape=(len(xy),) * 2), directed=False)
    xy = xy[lab == np.bincount(lab).argmax()].reset_index(drop=True); key = {(a, c): i for i, (a, c) in enumerate(zip(xy.x, xy.y))}
    E = np.array(nb()); I, J = E[:, 0], E[:, 1]; Wt = np.full(len(I), 1000.0)
    G = gpd.GeoDataFrame(xy, geometry=[box(a, c, a + 1000, c + 1000) for a, c in zip(xy.x, xy.y)], crs=DA.crs)
    F = {lid: rz((xy[a] / xy[d].clip(lower=1)).values + 1e-9 * np.random.default_rng(0).normal(size=len(xy))) for lid, (a, d) in LINES.items()}
    G.assign(**F).to_file(os.path.join(OUT, f"{city}_cells.gpkg"), driver="GPKG")
    wd = os.path.join(OUT, city); os.makedirs(wd, exist_ok=True)
    G[["x", "y", "pop", "geometry"]].to_file(os.path.join(wd, "areas.gpkg"), driver="GPKG")
    np.savez_compressed(os.path.join(wd, "fields.npz"), I=I, J=J, W=Wt, ids=np.array(list(F)), F=np.column_stack(list(F.values())))
    print(f"{city}: {len(G)} cells, {int(xy['pop'].sum()):,} residents", flush=True)
    GN = MultiScaleNull(G.geometry, I, J, Wt, m=9)
    c = G.geometry.centroid; dist = np.hypot(c.x - np.average(c.x, weights=xy["pop"]), c.y - np.average(c.y, weights=xy["pop"]))
    for lid, f in F.items():
        p, obs, nm, par = GN.test(f, 199, seed=3)
        rows.append(dict(city=city, line=lid, stage="quick", p=p, cleanness=obs, null_mean=nm, ell_km=par["ell"], cells=len(G),
                         rho_dist=pd.Series(f).corr(pd.Series(dist.values), method="spearman")))
        pd.DataFrame(rows).to_csv(os.path.join(OUT, "tests.csv"), index=False); print(f"  {lid:24s} quick p = {p:.3f}", flush=True)
