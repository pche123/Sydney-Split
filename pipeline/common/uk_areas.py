"""London: study MSOAs and every Census 2021 bulk table cut down to them.

    python pipeline/common/uk_areas.py london data/london work/london

Writes areas.gpkg (code, name, borough, population, km2, density; metres, British National Grid) and
census/tsXXX.csv (one row per study MSOA, the table's own column names). Every Greater London MSOA is kept
(about 1,000 of about 8,000 people each; London has no parks-only MSOAs to drop). That is three times
Sydney's area count: fine for the tests, a bit slower for the landscape null.
"""
import glob, os, sys, zipfile
import geopandas as gpd, pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cities import CITIES, LONDON_BOROUGHS


def main(city, raw, out):
    c = CITIES[city]; os.makedirs(f"{out}/census", exist_ok=True)
    g = gpd.read_file(f"{raw}/boundaries/msoa2021_london.geojson").to_crs(c["crs"])
    g["borough"] = g.MSOA21NM.str.rsplit(" ", n=1).str[0]
    g = g[g.borough.isin(LONDON_BOROUGHS)]
    g["km2"] = g.area / 1e6
    codes = set(g.MSOA21CD)
    for z in sorted(glob.glob(f"{raw}/census/census2021-ts*.zip")):
        t = os.path.basename(z)[11:-4]
        with zipfile.ZipFile(z) as zf:
            name = next(n for n in zf.namelist() if n.endswith("-msoa.csv"))
            d = pd.read_csv(zf.open(name))
        d = d[d["geography code"].isin(codes)].drop(columns=["date"])
        d.to_csv(f"{out}/census/{t}.csv", index=False)
        if t == "ts001":
            tot = next(col for col in d.columns if "Total" in col)
            g["population"] = g.MSOA21CD.map(d.set_index("geography code")[tot])
    g["density"] = g.population / g.km2
    g.rename(columns={"MSOA21CD": "code", "MSOA21NM": "name"})[["code", "name", "borough", "population", "km2", "density", "geometry"]] \
        .to_file(f"{out}/areas.gpkg", driver="GPKG")
    print(f"London: {len(g)} MSOAs, {int(g.population.sum()):,} people, {len(glob.glob(f'{out}/census/*.csv'))} tables")


if __name__ == "__main__":
    main(*sys.argv[1:4])
