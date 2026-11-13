"""Australian city: pick the study SA2s and cut every Census table down to them.

    python pipeline/common/au_areas.py melbourne data/melbourne work/melbourne

Reads what download.py fetched (zips are unpacked in place on first run) and writes:
  areas.gpkg            study SA2s: code, name, population, km2, density, geometry (metres, city CRS)
  dropped.gpkg          SA2s in the city left out (parks, airports, industrial, rural fringe) for the grey map layer
  census/2021_G*.csv    every General Community Profile table, study SA2s only, one file per table
  census/TSP_*.csv      every Time Series Profile table (2011/2016/2021 on 2021 SA2s)
Rule: inside the Greater Capital City area and the city box in cities.py, >= 1,000 residents and >= 300 people per km2.
(For Sydney this gives 304 SA2s; the published 300 also dropped 4 far-northern-beaches SA2s by hand.)
"""
import glob, os, re, sys, zipfile
import geopandas as gpd, pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cities import CITIES

MIN_POP, MIN_DENSITY = 1000, 300


def unzip_all(root):
    for z in glob.glob(f"{root}/**/*.zip", recursive=True):
        d = z[:-4]
        if not os.path.isdir(d):
            print("  unzip", os.path.relpath(z)); zipfile.ZipFile(z).extractall(d)


def find(root, pattern):
    hits = sorted(glob.glob(f"{root}/**/{pattern}", recursive=True))
    if not hits: raise SystemExit(f"nothing matching {pattern} under {root} (run download.py first)")
    return hits


def main(city, raw, out):
    c = CITIES[city]; os.makedirs(f"{out}/census", exist_ok=True)
    unzip_all(raw)
    shp = [p for p in find(raw, "SA2_2021_AUST*.shp")][0]
    g = gpd.read_file(shp)
    g = g[g.GCC_CODE21 == c["gccsa"]].to_crs(c["crs"])
    g["km2"] = g.area / 1e6
    g01 = pd.read_csv(find(raw, f"2021Census_G01_{c['state']}_SA2.csv")[0], dtype={"SA2_CODE_2021": str})
    pop = g01.set_index("SA2_CODE_2021").Tot_P_P
    g["population"] = g.SA2_CODE21.map(pop).fillna(0).astype(int)
    g["density"] = g.population / g.km2
    W, S, E, N = c["bbox"]   # also drop satellite towns outside the box (e.g. Central Coast, Blue Mountains for Sydney)
    cen = g.geometry.centroid.to_crs(4326)
    keep = (g.population >= MIN_POP) & (g.density >= MIN_DENSITY) & cen.x.between(W, E) & cen.y.between(S, N)
    a = g[keep].rename(columns={"SA2_CODE21": "code", "SA2_NAME21": "name"})[["code", "name", "population", "km2", "density", "geometry"]]
    a.to_file(f"{out}/areas.gpkg", driver="GPKG")
    g[~keep].rename(columns={"SA2_CODE21": "code", "SA2_NAME21": "name"})[["code", "name", "population", "geometry"]].to_file(
        f"{out}/dropped.gpkg", driver="GPKG")
    codes = set(a.code)
    print(f"{c['name']}: {len(a)} study SA2s, {a.population.sum():,} people ({(~keep).sum()} dropped)")

    for f in find(raw, f"2021Census_G*_{c['state']}_SA2.csv"):
        tag = re.search(r"_(G\w+?)_", os.path.basename(f)).group(1)
        t = pd.read_csv(f, dtype={"SA2_CODE_2021": str}); t[t.SA2_CODE_2021.isin(codes)].to_csv(f"{out}/census/2021_{tag}.csv", index=False)
    tsp = glob.glob(f"{raw}/**/2021Census_T*_{c['state']}_SA2.csv", recursive=True)
    for f in tsp:
        tag = re.search(r"_(T\w+?)_", os.path.basename(f)).group(1)
        t = pd.read_csv(f, dtype={"SA2_CODE_2021": str}); t[t.SA2_CODE_2021.isin(codes)].to_csv(f"{out}/census/TSP_{tag}.csv", index=False)
    print(f"  wrote {len(glob.glob(f'{out}/census/*.csv'))} tables -> {out}/census")


if __name__ == "__main__":
    main(*sys.argv[1:4])
