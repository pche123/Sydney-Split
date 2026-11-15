"""Singapore: URA Master Plan 2019 subzones with Census 2020 residents by type of dwelling.

    python pipeline/common/sg_areas.py singapore <phase1 folder> work/singapore

Census 2020 subzone table (data.gov.sg): residents by dwelling type (HDB flats by size, condominiums and other
apartments, landed property). "-" means none. Subzones with fewer than 100 residents are left out. Ethnic group counts
are kept only for the Heritage tab, never for line tests.
"""
import os, sys
import numpy as np, pandas as pd, geopandas as gpd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cities import CITIES


def table(path):
    d = pd.read_csv(path, dtype=str); d = d[~d.Number.str.contains("Total")]
    d.index = d.Number.str.upper().str.strip(); d = d.drop(columns="Number")
    return d.replace("-", "0").apply(pd.to_numeric, errors="coerce")


def main(city, raw, out):
    c = CITIES[city]; os.makedirs(f"{out}/census", exist_ok=True); d = f"{raw}/{city}/census"
    g = gpd.read_file(f"{d}/subzones_mp2019.geojson").to_crs(c["crs"])
    g["key"] = g.SUBZONE_N.str.upper().str.strip()
    dw = table(f"{d}/datagovsg_dwelling_type.csv"); eth = table(f"{d}/datagovsg_ethnic_group.csv")
    miss = sorted(set(dw.index) - set(g.key))
    print(f"dwelling table: {len(dw)} subzones, {len(miss)} not on the map: {miss[:10]}")
    g = g.join(dw, on="key")
    g["population"] = g.Total.fillna(0)
    g = g[g.population >= 100].reset_index(drop=True)
    g["km2"] = g.geometry.area / 1e6; g["density"] = g.population / g.km2
    g["code"] = g.SUBZONE_C; g["name"] = g.SUBZONE_N.str.title(); g["borough"] = g.PLN_AREA_N.str.title()
    g[["code", "name", "borough", "population", "km2", "density", "geometry"]].to_file(f"{out}/areas.gpkg", driver="GPKG")
    g[dw.columns].to_csv(f"{out}/census/dwelling.csv", index_label="area")
    eth.reindex(g.key).reset_index(drop=True).to_csv(f"{out}/census/ethnic.csv", index_label="area")
    print(f"{c['name']}: {len(g)} subzones with residents, {int(g.population.sum()):,} residents "
          f"(table total {int(dw.Total.sum()):,})")


if __name__ == "__main__":
    main(*sys.argv[1:4])
