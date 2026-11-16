"""Phase 2, Germany (census part): Berlin, Munich and Hamburg from the Zensus 2022 1 km grid.

    python experiments/phase2_germany.py <z22data folder> <berlin_bezirke.geojson> [out folder]

Data: Zensus 2022 grid tables (Destatis, Datenlizenz Deutschland 2.0), read from the jslth/z22data mirror on GitHub,
which repackages Destatis's CSVs as parquet. Areas: 1 km grid cells with at least 1,000 residents (the density rule
used for US tracts) inside each city's box (pipeline/cut_phase2_osm.py), largest connected piece, rook neighbours.
Lines the grid allows (no jobs or education at grid level, no venues yet): the Grey, Living Alone, Flats vs Houses
and Renters Lines (group "Homes", Holm within it), and the Money Line (average net rent per m²).
Test: the same quick landscape test as everywhere, then the calibrated test (R = 40, then 200 for close calls) for
any line with quick p < 0.2; saved after every test. Berlin also gets the exploratory Wall question: does each
line's median split follow the 1961–89 border more than random Berlins of the same smoothness do?
"""
import os, sys
import numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import box, Polygon
from scipy.stats import norm, rankdata
from scipy.sparse.csgraph import connected_components
from scipy import sparse

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); sys.path[:0] = [ROOT]
from linetests.landscape import MultiScaleNull, calibrated_map_test

Z22, BEZ = sys.argv[1], sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "results", "phase2", "germany")
os.makedirs(OUT, exist_ok=True)
BOX = {"berlin": (13.08, 52.33, 13.77, 52.68), "munich": (11.36, 48.06, 11.72, 48.25), "hamburg": (9.73, 53.39, 10.33, 53.74)}
rz = lambda v: norm.ppf((rankdata(v) - 0.5) / len(v))
def tab(name):
    d = pd.read_parquet(f"{Z22}/z22_data_1km/{name}.parquet"); return d.set_index(["x", "y"]).value
pop = tab("population_0"); age65 = tab("age_from_65_0"); owner = tab("owner_occupier_0"); rent = tab("rent_avg_0")
hh = pd.concat({k: tab(f"household_size_group_{k}") for k in range(1, 7)}, axis=1).fillna(0)
dw = pd.concat({k: tab(f"dwelling_building_size_{k}") for k in range(1, 11)}, axis=1).fillna(0)
R_ = []
P = os.path.join(OUT, "tests.csv"); done = pd.read_csv(P) if os.path.exists(P) else pd.DataFrame(columns=["city", "line", "stage"])
rows = done.to_dict("records")
def have(c, l, st): return any(r["city"] == c and r["line"] == l and r["stage"] == st for r in rows)
def save(): pd.DataFrame(rows).to_csv(P, index=False)

for city, (w, s, e, n) in BOX.items():
    bb = gpd.GeoSeries([box(w, s, e, n)], crs=4326).to_crs(3035).iloc[0]
    xy = pop.index.to_frame(index=False); xy["pop"] = pop.values
    x0, y0, x1, y1 = bb.bounds; xy = xy[(xy["pop"] >= 1000) & xy.x.between(x0, x1) & xy.y.between(y0, y1)]
    xy = xy[gpd.points_from_xy(xy.x, xy.y).within(bb)].reset_index(drop=True)
    key = {(x, y): i for i, (x, y) in enumerate(zip(xy.x, xy.y))}
    I, J = [], []
    for i, (x, y) in enumerate(zip(xy.x, xy.y)):
        for dx, dy in [(1000, 0), (0, 1000)]:
            j = key.get((x + dx, y + dy))
            if j is not None: I.append(i); J.append(j)
    A = sparse.coo_matrix((np.ones(len(I)), (I, J)), shape=(len(xy),) * 2)
    _, lab = connected_components(A, directed=False); big = lab == np.bincount(lab).argmax()
    xy = xy[big].reset_index(drop=True); key = {(x, y): i for i, (x, y) in enumerate(zip(xy.x, xy.y))}
    I, J = [], []
    for i, (x, y) in enumerate(zip(xy.x, xy.y)):
        for dx, dy in [(1000, 0), (0, 1000)]:
            j = key.get((x + dx, y + dy))
            if j is not None: I.append(i); J.append(j)
    I, J = np.array(I), np.array(J); W = np.full(len(I), 1000.0)
    G = gpd.GeoDataFrame(xy, geometry=[box(x - 500, y - 500, x + 500, y + 500) for x, y in zip(xy.x, xy.y)], crs=3035)
    idx = list(zip(xy.x, xy.y))
    H = hh.reindex(idx).values; D = dw.reindex(idx).values
    F = {"the-grey-line": age65.reindex(idx).values, "the-living-alone-line": H[:, 0] / np.maximum(H.sum(1), 1),
         "flats-vs-houses": D[:, 6:9].sum(1) / np.maximum(D[:, :9].sum(1), 1), "the-renters-line": 100 - owner.reindex(idx).values,
         "money": rent.reindex(idx).values}
    F = {k: rz(pd.Series(v).fillna(pd.Series(v).median()).values) for k, v in F.items()}
    G.assign(**F).to_file(os.path.join(OUT, f"{city}_cells.gpkg"), driver="GPKG")
    wd = os.path.join(OUT, city); os.makedirs(wd, exist_ok=True)   # work folder for the checkpointed calibration
    G[["x", "y", "pop", "geometry"]].to_file(os.path.join(wd, "areas.gpkg"), driver="GPKG")
    np.savez_compressed(os.path.join(wd, "fields.npz"), I=I, J=J, W=W, ids=np.array(list(F)), F=np.column_stack(list(F.values())))
    print(f"{city}: {len(G)} cells, {len(I)} shared borders, {int(xy['pop'].sum()):,} residents", flush=True)
    GN = MultiScaleNull(G.geometry, I, J, W, m=9)
    for lid, f in F.items():
        if not have(city, lid, "quick"):
            p, obs, nm, par = GN.test(f, 199, seed=3)
            rows.append(dict(city=city, line=lid, stage="quick", p=p, cleanness=obs, null_mean=nm, ell_km=par["ell"], areas=len(G))); save()
            print(f"  {lid:24s} quick p = {p:.3f}", flush=True)
        pq = next(r["p"] for r in rows if r["city"] == city and r["line"] == lid and r["stage"] == "quick")
        if pq < 0.2 and not have(city, lid, "calibrated") and os.environ.get("DE_CALIBRATE") == "1":   # else: experiments/calibrate_checkpoint.py on the work folder
            r = calibrated_map_test(GN, f, B=199, R=40, Bin=99, seed=3); Rn = 40
            if r["p_cal"] < 0.1: r = calibrated_map_test(GN, f, B=199, R=200, Bin=99, seed=3); Rn = 200
            rows.append(dict(city=city, line=lid, stage="calibrated", p=r["p_cal"], cleanness=r["cleanness"], null_mean=r["null_mean"], ell_km=r["ell_km"], areas=len(G), R=Rn)); save()
            print(f"  {lid:24s} calibrated p = {r['p_cal']:.3f} (R = {Rn})", flush=True)
    if city == "berlin" and not os.path.exists(os.path.join(OUT, "berlin_wall.csv")):
        bz = gpd.read_file(BEZ).to_crs(3035)
        east_whole = {"Pankow", "Lichtenberg", "Marzahn-Hellersdorf", "Treptow-Köpenick"}
        wall = [(13.3979, 52.5547), (13.3895, 52.5352), (13.3830, 52.5330), (13.3718, 52.5277), (13.3755, 52.5205), (13.3777, 52.5163),
                (13.3765, 52.5096), (13.3904, 52.5075), (13.4137, 52.5072), (13.4260, 52.5050), (13.4300, 52.5060), (13.4457, 52.5016), (13.4620, 52.4940)]
        cut = gpd.GeoSeries([Polygon(wall + [(13.55, 52.49), (13.55, 52.57), (13.3979, 52.5547)])], crs=4326).to_crs(3035).iloc[0]
        split_b = bz[bz.name.isin(["Mitte", "Friedrichshain-Kreuzberg"])].union_all().intersection(cut)
        east_poly = bz[bz.name.isin(east_whole)].union_all().union(split_b)
        cen = G.geometry.centroid; east = cen.within(east_poly).values
        rng = np.random.default_rng(1989); wrows = []
        for lid, f in F.items():
            par = GN.fit(f); Sm = GN.simulate(par, 999, rng)
            side = f > np.median(f); m = max((side == east).mean(), (side != east).mean())
            null = np.array([max(((Sm[:, b] > np.median(Sm[:, b])) == east).mean(), ((Sm[:, b] > np.median(Sm[:, b])) != east).mean()) for b in range(999)])
            p = (1 + (null >= m).sum()) / 1000
            wrows.append(dict(line=lid, match=m, null_mean=null.mean(), p=p, east_cells=int(east.sum()), cells=len(east)))
            print(f"  Wall: {lid:24s} {m:.0%} of cells on the matching side (random Berlins {null.mean():.0%}), p = {p:.3f}", flush=True)
        pd.DataFrame(wrows).to_csv(os.path.join(OUT, "berlin_wall.csv"), index=False)
print("->", OUT)
