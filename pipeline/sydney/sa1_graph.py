"""SA1 study area (inside the 300 urban SA2s) + shared-border graph."""
import os
RAW = os.environ.get("SPLIT_RAW", "../data")   # raw downloads (see README)
import numpy as np, pandas as pd, geopandas as gpd
a = pd.read_csv("./q_classic/areas.csv", dtype=str)
g = gpd.read_file(f"{RAW}/shp_sa1/SA1_2021_AUST_GDA2020.shp")
g = g[g.SA2_CODE21.isin(a.SA2_CODE21)].to_crs(7856)
s = pd.read_csv("./signals_sa1.csv", dtype={"SA1_CODE_2021": str}).set_index("SA1_CODE_2021")
g = g.join(s, on="SA1_CODE21"); g = g[g.population >= 50].reset_index(drop=True)
pairs = gpd.sjoin(g[["geometry"]], g[["geometry"]], predicate="touches"); pairs = pairs[pairs.index < pairs.index_right]
bd = g.geometry.boundary
E = []
for i, j in zip(pairs.index.values, pairs.index_right.values):
    L = bd[i].intersection(bd[j]).length
    if L >= 20: E.append((i, j, L))
E = np.array(E)
g.to_file("./sa1.gpkg"); np.save("./sa1_edges.npy", E)
print("SA1s", len(g), "edges", len(E), "people", int(g.population.sum()))
