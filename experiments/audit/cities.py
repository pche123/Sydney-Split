import os, sys; _H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [_H, os.path.dirname(_H), os.path.join(os.path.dirname(_H), "..")]  # experiments, repo root
from paths import SYD, TOK, RAW  # noqa: E402
"""Load Sydney and Tokyo as (graph, polygons, rep points) in the app's area order."""
import json
import numpy as np, pandas as pd, geopandas as gpd


def load(city):
    if city == "Sydney":
        a = pd.read_csv(f"{SYD}/q_classic/areas.csv", dtype=str)
        G = gpd.read_file(f"{RAW}/shp/SA2_2021_AUST_GDA2020.shp").to_crs(7856).set_index("SA2_CODE21").loc[a.SA2_CODE21].reset_index()
        m = json.load(open(f"{SYD}/app_data.json"))["make"]
        I, J = np.array(m["I"]), np.array(m["J"]); W = np.array(m["L"]) * 1000
        pop = np.array(m["pop"], float)
    else:
        G = gpd.read_file(f"{TOK}/out/tokyo_neigh.gpkg")
        z = np.load(f"{TOK}/out/tokyo_fields.npz")
        I, J, W = z["I"], z["J"], z["W"]; pop = z["pop"].astype(float)
    rp = G.geometry.representative_point()
    rep = np.column_stack([rp.x, rp.y])
    return dict(city=city, n=len(G), I=I, J=J, W=W, rep=rep, geom=G.geometry, pop=pop)
