"""New Zealand city: Census 2023 SA2s as study areas (not merged: about 2,000-4,000 people each).

    python pipeline/common/nz_areas.py auckland <phase1 folder> work/auckland

Reads <phase1>/<city>/census/{individuals_layer0, individuals_layer2, households_layer0}.geojson (Stats NZ ArcGIS).
Keeps SA2s whose centre lies in the city's box with at least 100 people and 1,000 people per km² of land.
Stats NZ marks suppressed small counts with negative codes; they are counted as 0. Writes areas.gpkg and
census/nz.csv (2023 count columns of all three layers, one row per area).
"""
import glob, os, sys
import numpy as np, pandas as pd, geopandas as gpd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cities import CITIES


def main(city, raw, out):
    c = CITIES[city]; os.makedirs(f"{out}/census", exist_ok=True)
    d = f"{raw}/{city}/census"; key = "SA22023_V1_00"
    L = []                                    # every layer that has values (Stats NZ's clipped part 2 can come back empty)
    for f in sorted(glob.glob(f"{d}/*_layer*.geojson")):
        x = gpd.read_file(f)
        if x[key].notna().any(): L.append(x)
    g = L[0][[key, "SA22023_V1_00_NAME_ASCII", "LAND_AREA_SQ_KM", "geometry"]].copy()
    for x in L:
        v = [col for col in x.columns if col.startswith("VAR_") and col not in g.columns]
        if v: g = g.merge(pd.DataFrame(x[[key] + v]), on=key, how="left")
    v = [col for col in g.columns if col.startswith("VAR_")]
    g[v] = g[v].apply(pd.to_numeric, errors="coerce").clip(lower=0)
    W, S_, E, N = c["bbox"]; rp = g.representative_point()
    g = g[(rp.x >= W) & (rp.x <= E) & (rp.y >= S_) & (rp.y <= N)]
    g["population"] = g.VAR_1_3.fillna(0)
    g["km2"] = g.LAND_AREA_SQ_KM.where(g.LAND_AREA_SQ_KM > 0, np.nan)
    g = g[(g.population >= 100) & (g.population / g.km2 >= 1000)].to_crs(c["crs"]).reset_index(drop=True)
    g["code"] = g[key]; g["name"] = g.SA22023_V1_00_NAME_ASCII; g["borough"] = c["name"]; g["density"] = g.population / g.km2
    g[["code", "name", "borough", "population", "km2", "density", "geometry"]].to_file(f"{out}/areas.gpkg", driver="GPKG")
    g[v].to_csv(f"{out}/census/nz.csv", index_label="area")
    print(f"{c['name']}: {len(g)} SA2s kept, median {int(g.population.median()):,} people, {int(g.population.sum()):,} people in total")


if __name__ == "__main__":
    main(*sys.argv[1:4])
