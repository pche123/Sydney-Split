"""Bring already-built cities up to the current download format without rebuilding them (a rebuild would undo the double-check).

    python pipeline/common/enrich_downloads.py <cities work folder> [--json]

* CSV gets score_<line> columns (each line's continuous score, rank-normal: positive = orange side).
* GeoJSON gets every CSV column, not just name and population.
* Sydney and Tokyo get a GeoJSON too (SA2 boundaries / Tokyo neighbourhood file).
* With --json, each line in the app file also gets "f" (the score) for the smoothing slider.
"""
import glob, json, os, sys
import numpy as np, pandas as pd, geopandas as gpd
from scipy.stats import norm, rankdata

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
from cities import CITIES

CI = sys.argv[1]; DO_JSON = "--json" in sys.argv
DL = os.path.join(ROOT, "app", "public", "downloads")
rz = lambda v: norm.ppf((rankdata(v) - 0.5) / len(v))


def write_geojson(city, tab, geom):
    gj = gpd.GeoDataFrame(tab.drop(columns=[c for c in ["full_name"] if c in tab]), geometry=geom.values, crs=geom.crs).to_crs(4326)
    gj.to_file(os.path.join(DL, f"{city}_areas.geojson"), driver="GeoJSON", COORDINATE_PRECISION=5)


for city, C in CITIES.items():
    csv = os.path.join(DL, f"{city}_areas.csv"); app = os.path.join(ROOT, "app", "data", f"{city}.json")
    if not os.path.exists(csv) or not os.path.exists(app): continue
    tab = pd.read_csv(csv)
    if city in ("sydney", "tokyo"):
        if city == "tokyo":
            geom = gpd.read_file("/home/claude/tokyo/out/tokyo_neigh.gpkg").geometry
        else:
            sa2 = gpd.read_file("/home/claude/data/shp/SA2_2021_AUST_GDA2020.shp")
            sa2 = sa2[sa2.STE_NAME21 == "New South Wales"].set_index("SA2_NAME21")
            names = [a["name"] for a in json.load(open(app))["areas"]]
            geom = sa2.geometry.reindex(names)
            print("sydney: shapes found", int(geom.notna().sum()), "of", len(names))
        geom = geom.simplify(0.0001 if geom.crs.is_geographic else 15)
        write_geojson(city, tab, geom); print(city, "geojson written")
        if DO_JSON:
            d = json.load(open(app)); d["meta"].setdefault("download", {})["geojson"] = f"downloads/{city}_areas.geojson"
            json.dump(d, open(app, "w"), separators=(",", ":"), ensure_ascii=False)
        continue
    W = os.path.join(CI, city)
    if not os.path.exists(f"{W}/fields.npz"): continue
    z = np.load(f"{W}/fields.npz"); S = {str(i): np.round(rz(f), 2) for i, f in zip(z["ids"], z["F"].T)}
    for lid, v in S.items(): tab["score_" + lid] = v
    tab.to_csv(csv, index=False)
    G = gpd.read_file(f"{W}/areas.gpkg").to_crs(C["crs"]).reset_index(drop=True)
    write_geojson(city, tab, G.geometry.simplify(15))
    if DO_JSON:
        d = json.load(open(app))
        for l in d["lines"]:
            if l["id"] in S: l["f"] = [float(x) for x in S[l["id"]]]
        json.dump(d, open(app, "w"), separators=(",", ":"), ensure_ascii=False)
    print(city, "done", len(S), "scores", "(+json)" if DO_JSON else "")
