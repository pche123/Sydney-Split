import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "linetests"))  # library
"""Load Sydney and Tokyo as (graph, polygons, rep points) in the app's area order."""
import json
import numpy as np, pandas as pd, geopandas as gpd


def load(city):
    if city == "Sydney":
        a = pd.read_csv("/home/claude/work/q_classic/areas.csv", dtype=str)
        G = gpd.read_file("/home/claude/data/shp/SA2_2021_AUST_GDA2020.shp").to_crs(7856).set_index("SA2_CODE21").loc[a.SA2_CODE21].reset_index()
        m = json.load(open("/home/claude/work/app_data.json"))["make"]
        I, J = np.array(m["I"]), np.array(m["J"]); W = np.array(m["L"]) * 1000
        pop = np.array(m["pop"], float)
    else:
        G = gpd.read_file("/home/claude/tokyo/out/tokyo_neigh.gpkg")
        z = np.load("/home/claude/tokyo/out/tokyo_fields.npz")
        I, J, W = z["I"], z["J"], z["W"]; pop = z["pop"].astype(float)
    rp = G.geometry.representative_point()
    rep = np.column_stack([rp.x, rp.y])
    return dict(city=city, n=len(G), I=I, J=J, W=W, rep=rep, geom=G.geometry, pop=pop)
