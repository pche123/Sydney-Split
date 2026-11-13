"""English city: study areas (MSOA, or LSOA for small cities) and every Census 2021 bulk table cut down to them.

    python pipeline/common/uk_areas.py manchester data/manchester work/manchester

Writes areas.gpkg (code, name, borough, population, km2, density; metres, British National Grid) and
census/tsXXX.csv (one row per study area, the table's own column names). Every area in the city's councils
(cities.py) is kept. London has about 1,000 MSOAs, three times Sydney's count: fine for the tests, slower for the
landscape null. Brighton uses LSOAs because it has only about 37 MSOAs.
"""
import glob, os, sys, zipfile
import geopandas as gpd, pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cities import CITIES


def main(city, raw, out):
    c = CITIES[city]; os.makedirs(f"{out}/census", exist_ok=True)
    L = c["level"].upper()
    g = gpd.read_file(f"{raw}/boundaries/{c['level']}2021.geojson").to_crs(c["crs"])
    g["borough"] = g[f"{L}21NM"].str.rsplit(" ", n=1).str[0]
    g = g[g.borough.isin(c["lads"])]
    g["km2"] = g.area / 1e6
    codes = set(g[f"{L}21CD"])
    zips = glob.glob(f"{raw}/census/census2021-ts*.zip") or glob.glob(f"{raw}/../_uk_census/census2021-ts*.zip")
    for z in sorted(zips):
        t = os.path.basename(z)[11:-4]
        with zipfile.ZipFile(z) as zf:
            name = next(n for n in zf.namelist() if n.endswith(f"-{c['level']}.csv"))
            d = pd.read_csv(zf.open(name))
        d = d[d["geography code"].isin(codes)].drop(columns=["date"])
        d.to_csv(f"{out}/census/{t}.csv", index=False)
        if t == "ts001":
            tot = next(col for col in d.columns if "Total" in col)
            g["population"] = g[f"{L}21CD"].map(d.set_index("geography code")[tot])
    g["density"] = g.population / g.km2
    g.rename(columns={f"{L}21CD": "code", f"{L}21NM": "name"})[["code", "name", "borough", "population", "km2", "density", "geometry"]] \
        .to_file(f"{out}/areas.gpkg", driver="GPKG")
    print(f"{c['name']}: {len(g)} {L}s, {int(g.population.sum()):,} people, {len(glob.glob(f'{out}/census/*.csv'))} tables")


if __name__ == "__main__":
    main(*sys.argv[1:4])
