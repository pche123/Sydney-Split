"""Phase 2b, Spain and Italy (census part): Madrid, Barcelona, Rome and Milan on the 1 km grid used for Germany.

    python experiments/phase2_es_it.py <spain folder> <italy folder> [out folder]

<spain folder> holds C2021_Indicadores.csv and Seccionado_2021/SECC_CE_20210101.shp (INE, 2021 census sections).
<italy folder> holds SHP/R03_21_WGS84.shp, SHP/R12_21_WGS84.shp and R03/R12_indicatori_2021_sezioni.xlsx (ISTAT).
Sections are allocated to 1 km grid cells (ETRS89-LAEA) by area; cells with >= 1,000 residents, largest connected
piece, rook neighbours. Lines and the variable mapping are those committed in HYPOTHESES.md (Phase 2b) before testing.
Quick landscape test for every line; any line with quick p < 0.2 is queued for the calibrated test
(experiments/calibrate_checkpoint.py on the work folder written here).
Named borders (B1 Madrid north-south, B2 Barcelona's Diagonal): share of the city's cells whose side of each line's
median split matches their side of the border, against 999 simulated cities of the same smoothness; Holm across lines.
"""
import os, sys
import numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import box, LineString
from scipy.stats import norm, rankdata
from scipy.sparse.csgraph import connected_components
from scipy import sparse

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); sys.path[:0] = [ROOT]
from linetests.landscape import MultiScaleNull

ES, IT = sys.argv[1], sys.argv[2]
OUT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "results", "phase2", "es_it"); os.makedirs(OUT, exist_ok=True)
BOX = {"madrid": (-3.84, 40.31, -3.52, 40.56), "barcelona": (2.05, 41.32, 2.25, 41.47),
       "rome": (12.30, 41.75, 12.65, 42.02), "milan": (9.04, 45.38, 9.28, 45.54)}
rz = lambda v: norm.ppf((rankdata(v) - 0.5) / len(v))

def spain_sections():
    d = pd.read_csv(f"{ES}/C2021_Indicadores.csv", dtype={"ccaa": str, "cpro": str, "cmun": str, "dist": str, "secc": str})
    d["CUSEC"] = d.cpro + d.cmun + d.dist + d.secc
    num = lambda c: pd.to_numeric(d[c], errors="coerce").fillna(0)
    pop = num("t1_1"); p16 = pop * (1 - num("t4_1")); act = num("t12_1") * p16
    c = pd.DataFrame({"CUSEC": d.CUSEC, "pop": pop, "deg": num("t9_1") * p16, "p16": p16, "old": num("t4_3") * pop,
                      "rent": num("t20_2"), "ten": num("t20_1") + num("t20_2") + num("t20_3"), "alone": num("t22_1"),
                      "hh": num("t21_1"), "unemp": num("t10_1") * act, "act": act})
    g = gpd.read_file(f"{ES}/Seccionado_2021/SECC_CE_20210101.shp", columns=["CUSEC", "CMUN", "CPRO", "CDIS"])
    return g.merge(c, on="CUSEC", how="left").fillna(0)

def italy_sections(reg):
    d = pd.read_excel(f"{IT}/R{reg}_indicatori_2021_sezioni.xlsx")
    num = lambda c: pd.to_numeric(d[c], errors="coerce").fillna(0)
    c = pd.DataFrame({"SEZ21_ID": d.SEZ21_ID.astype("int64"), "pop": num("P1"), "old": num("P27") + num("P28") + num("P29"),
                      "work": num("IT10") + num("ST31"), "w1564": num("IT2") + num("ST23"), "alone": num("PF3"), "hh": num("PF1"),
                      "empty": num("A3"), "dw": num("A8")})
    g = gpd.read_file(f"{IT}/SHP/R{reg}_21_WGS84.shp", columns=["SEZ21_ID", "PRO_COM"])
    g["SEZ21_ID"] = g.SEZ21_ID.astype("int64")
    return g.merge(c, on="SEZ21_ID", how="left").fillna(0)

LINES = {"es": {"the-degree-line": ("deg", "p16"), "the-grey-line": ("old", "pop"), "the-renters-line": ("rent", "ten"),
                "the-living-alone-line": ("alone", "hh"), "the-jobless-line": ("unemp", "act")},
         "it": {"the-grey-line": ("old", "pop"), "the-living-alone-line": ("alone", "hh"), "the-jobless-line": ("w1564", "w1564"),
                "the-empty-homes-line": ("empty", "dw")}}

PRE = {"es": ["the-degree-line", "the-jobless-line", "the-renters-line", "the-grey-line"],   # Holm set, as pre-registered
       "it": ["the-jobless-line", "the-living-alone-line", "the-grey-line"]}

def to_cells(sec, bbox):
    sec = sec.to_crs(3035); sec = sec[sec.intersects(bbox)].copy(); sec["sa"] = sec.area
    x0, y0, x1, y1 = (np.floor(np.array(bbox.bounds) / 1000) * 1000).astype(int)
    grid = gpd.GeoDataFrame({"x": [x for x in range(x0, x1 + 1000, 1000) for y in range(y0, y1 + 1000, 1000)],
                             "y": [y for x in range(x0, x1 + 1000, 1000) for y in range(y0, y1 + 1000, 1000)]},
                            geometry=[box(x, y, x + 1000, y + 1000) for x in range(x0, x1 + 1000, 1000) for y in range(y0, y1 + 1000, 1000)], crs=3035)
    grid = grid[grid.intersects(bbox)]
    ov = gpd.overlay(sec, grid, how="intersection", keep_geom_type=True); w = ov.area / ov.sa
    cols = [c for c in sec.columns if c not in ("geometry", "sa", "PRO_COM", "SEZ21_ID") and pd.api.types.is_numeric_dtype(sec[c])]
    agg = ov[cols].mul(w, axis=0).assign(x=ov.x, y=ov.y).groupby(["x", "y"]).sum()
    ov["w_pop"] = w * ov["pop"]; keyc = [c for c in ("CDIS", "CMUN", "CPRO", "PRO_COM") if c in ov]
    lab = ov.sort_values("w_pop").groupby(["x", "y"])[keyc].last()   # where most of the cell's residents live
    return agg.join(lab).reset_index()

def neighbours(xy):
    key = {(x, y): i for i, (x, y) in enumerate(zip(xy.x, xy.y))}; I, J = [], []
    for i, (x, y) in enumerate(zip(xy.x, xy.y)):
        for dx, dy in [(1000, 0), (0, 1000)]:
            j = key.get((x + dx, y + dy))
            if j is not None: I.append(i); J.append(j)
    return np.array(I), np.array(J)

P = os.path.join(OUT, "tests.csv"); rows = pd.read_csv(P).to_dict("records") if os.path.exists(P) else []
have = lambda c, l: any(r["city"] == c and r["line"] == l for r in rows)
es_sec = spain_sections(); it_sec = {"rome": italy_sections("12"), "milan": italy_sections("03")}
for city, (w, s, e, n) in BOX.items():
    cc = "es" if city in ("madrid", "barcelona") else "it"
    bbox = gpd.GeoSeries([box(w, s, e, n)], crs=4326).to_crs(3035).iloc[0]
    xy = to_cells(es_sec if cc == "es" else it_sec[city], bbox)
    xy = xy[xy["pop"] >= 1000].reset_index(drop=True)
    I, J = neighbours(xy); A = sparse.coo_matrix((np.ones(len(I)), (I, J)), shape=(len(xy),) * 2)
    _, lab = connected_components(A, directed=False); xy = xy[lab == np.bincount(lab).argmax()].reset_index(drop=True)
    I, J = neighbours(xy); W = np.full(len(I), 1000.0)
    G = gpd.GeoDataFrame(xy, geometry=[box(x, y, x + 1000, y + 1000) for x, y in zip(xy.x, xy.y)], crs=3035)
    F = {}
    for lid, (a, b) in LINES[cc].items():
        v = (1 - xy["work"] / xy["w1564"].clip(lower=1)) if lid == "the-jobless-line" and cc == "it" else xy[a] / xy[b].clip(lower=1)
        F[lid] = rz(v.values)
    G.assign(**F).to_file(os.path.join(OUT, f"{city}_cells.gpkg"), driver="GPKG")
    wd = os.path.join(OUT, city); os.makedirs(wd, exist_ok=True)
    G[["x", "y", "pop", "geometry"]].to_file(os.path.join(wd, "areas.gpkg"), driver="GPKG")
    np.savez_compressed(os.path.join(wd, "fields.npz"), I=I, J=J, W=W, ids=np.array(list(F)), F=np.column_stack(list(F.values())))
    print(f"{city}: {len(G)} cells, {len(I)} shared borders, {int(xy['pop'].sum()):,} residents", flush=True)
    GN = MultiScaleNull(G.geometry, I, J, W, m=9)
    for lid, f in F.items():
        if have(city, lid): continue
        p, obs, nm, par = GN.test(f, 199, seed=3)
        rows.append(dict(country=cc, city=city, line=lid, stage="quick", p=p, cleanness=obs, null_mean=nm, ell_km=par["ell"], areas=len(G)))
        pd.DataFrame(rows).to_csv(P, index=False); print(f"  {lid:24s} quick p = {p:.3f}", flush=True)
    # named borders
    border = None
    if city == "madrid":
        inm = (xy.CPRO == "28") & (xy.CMUN == "079"); south = xy.CDIS.isin(["10", "11", "12", "13", "17", "18", "19"])
        border = ("B1 north-south", inm.values, south.values)
    if city == "barcelona":
        inm = (xy.CPRO == "08") & (xy.CMUN == "019")
        diag = gpd.GeoSeries([LineString([(2.1135, 41.3845), (2.1435, 41.3926), (2.1600, 41.3960), (2.1873, 41.4036), (2.2210, 41.4105)])], crs=4326).to_crs(3035).iloc[0]
        cx, cy = xy.x + 500, xy.y + 500
        # uphill = on the left of the avenue as it runs south-west to north-east
        side = np.array([np.sign((diag.coords[-1][0] - diag.coords[0][0]) * (yy - diag.coords[0][1]) - (diag.coords[-1][1] - diag.coords[0][1]) * (xx - diag.coords[0][0])) > 0 for xx, yy in zip(cx, cy)])
        border = ("B2 Diagonal", inm.values, side)
    if border and not os.path.exists(os.path.join(OUT, f"{city}_border.csv")):
        name, inside, sideb = border; rng = np.random.default_rng(2026); out = []
        for lid, f in F.items():
            par = GN.fit(f); Sm = GN.simulate(par, 999, rng)
            def match(v):
                s_ = v[inside] > np.median(v[inside]); t = sideb[inside]; return max((s_ == t).mean(), (s_ != t).mean())
            m = match(f); null = np.array([match(Sm[:, b]) for b in range(999)]); p = (1 + (null >= m).sum()) / 1000
            out.append(dict(border=name, line=lid, match=m, null_mean=null.mean(), p=p, cells=int(inside.sum()), border_side=int(sideb[inside].sum())))
            print(f"  {name}: {lid:24s} {m:.0%} match (random {null.mean():.0%}), p = {p:.3f}", flush=True)
        o = pd.DataFrame(out); reg = o.line.isin(PRE[cc]); o = pd.concat([o[reg].sort_values("p"), o[~reg]]); k = int(reg.sum())
        o["p_holm"] = list(np.minimum(1, np.maximum.accumulate([(k - i) * q for i, q in enumerate(o.p[:k])]))) + [np.nan] * (len(o) - k)
        o.to_csv(os.path.join(OUT, f"{city}_border.csv"), index=False)
print("->", OUT)
