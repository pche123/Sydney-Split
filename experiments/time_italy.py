"""Time questions T1-T3 (HYPOTHESES.md) for Rome and Milan: census sections 1991, 2001, 2011 on the 2021 1 km cells.

    python experiments/time_italy.py <folder with dati-cpa_YYYY/ and R03_YY_WGS84/, R12_YY_WGS84/ unpacked>

Variables with the same definition in all three censuses: 65+ share (P27+P28+P29)/P1, living alone PF3/PF1.
Writes results/time/italy.csv (one row per city, variable, year) and italy_pairs.csv (side agreement between years).
"""
import glob, os, sys
import numpy as np, pandas as pd, geopandas as gpd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); IN = sys.argv[1]
OUT = os.path.join(ROOT, "results", "time"); os.makedirs(OUT, exist_ok=True)
CITY = {"rome": ("12", "058091"), "milan": ("03", "015146")}   # region, comune of the city proper (cells reach beyond it)
YEARS = {"1991": "91", "2001": "01", "2011": "11"}


def sections(reg, y):
    yy = YEARS[y]; key = f"SEZ{y}"
    shp = gpd.read_file(glob.glob(f"{IN}/**/R{reg}_{yy}_WGS84.shp", recursive=True)[0]).to_crs(3035)
    if y == "2011":
        d = pd.read_csv(glob.glob(f"{IN}/**/R{reg}_indicatori_2011_sezioni.csv", recursive=True)[0], sep=";", encoding="latin1")
    else:
        d = pd.read_excel(glob.glob(f"{IN}/**/R{reg}_DatiCPA_{y}.xls", recursive=True)[0], sheet_name=f"R{reg}_DatiCPA")
    on = [key] + (["ISOLATO"] if y == "1991" and "ISOLATO" in d and "ISOLATO" in shp else [])
    for c in on: shp[c] = pd.to_numeric(shp[c], errors="coerce"); d[c] = pd.to_numeric(d[c], errors="coerce")
    v = d[on + ["P1", "P27", "P28", "P29", "PF1", "PF3"]].apply(pd.to_numeric, errors="coerce").groupby(on).sum().reset_index()
    g = shp[on + ["geometry"]].dissolve(by=on).reset_index().merge(v, on=on, how="inner")
    return g


def to_cells(sec, cells):
    sec = sec.copy(); sec["sa"] = sec.area
    ov = gpd.overlay(sec, cells[["cid", "geometry"]], how="intersection", keep_geom_type=True); w = ov.area / ov.sa
    cols = ["P1", "P27", "P28", "P29", "PF1", "PF3"]
    return ov[cols].mul(w, axis=0).assign(cid=ov.cid).groupby("cid").sum().reindex(cells.cid).fillna(0)


rows, pairs, AREAS = [], [], []
for city, (reg, _) in CITY.items():
    cells = gpd.read_file(os.path.join(ROOT, "results", "phase2", "es_it", city, "areas.gpkg")).reset_index(names="cid")
    now = gpd.read_file(os.path.join(ROOT, "results", "phase2", "es_it", f"{city}_cells.gpkg"))   # 2021 fields (normal scores)
    c = cells.geometry.centroid; w = cells["pop"].values
    cx, cy = np.average(c.x, weights=w), np.average(c.y, weights=w); dist = np.hypot(c.x - cx, c.y - cy).values
    V = {}
    for y in YEARS:
        a = to_cells(sections(reg, y), cells)
        print(city, y, f"{a.P1.sum():,.0f} residents on the cells", flush=True)
        V[("grey", y)] = ((a.P27 + a.P28 + a.P29) / a.P1.clip(lower=1)).values
        V[("alone", y)] = (a.PF3 / a.PF1.clip(lower=1)).values
        rows += [dict(city=city, year=int(y), residents=float(a.P1.sum()))]
    V[("grey", "2021")] = now["the-grey-line"].values; V[("alone", "2021")] = now["the-living-alone-line"].values
    AREAS.append(pd.DataFrame({"city": city, "x": c.x.values, "y": c.y.values, "dist": dist,
                               **{f"{v}_{y}": np.asarray(V[(v, y)]) for (v, y) in V}}))
    for var in ("grey", "alone"):
        for y in ("1991", "2001", "2011", "2021"):
            rho = pd.Series(V[(var, y)]).corr(pd.Series(dist), method="spearman")
            rows.append(dict(city=city, var=var, year=int(y), rho_dist=rho))
        for y0, y1 in (("1991", "2001"), ("2001", "2011"), ("2011", "2021"), ("1991", "2021")):
            s0 = V[(var, y0)] > np.median(V[(var, y0)]); s1 = V[(var, y1)] > np.median(V[(var, y1)])
            pairs.append(dict(city=city, var=var, from_=int(y0), to=int(y1), agree=float((s0 == s1).mean()),
                              spearman=pd.Series(V[(var, y0)]).corr(pd.Series(V[(var, y1)]), method="spearman")))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "italy.csv"), index=False)
pd.concat(AREAS).to_csv(os.path.join(OUT, "italy_areas.csv.gz"), index=False)
pd.DataFrame(pairs).rename(columns={"from_": "from"}).to_csv(os.path.join(OUT, "italy_pairs.csv"), index=False)
print(pd.DataFrame(pairs).round(2).to_string())
print(pd.DataFrame([r for r in rows if "var" in r]).pivot_table(index=["city", "var"], columns="year", values="rho_dist").round(2))
