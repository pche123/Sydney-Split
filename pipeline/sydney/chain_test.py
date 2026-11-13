"""Is a brand's catchment line cleaner than a fake chain with the same number of stores placed on random real food venues?"""
import sys, numpy as np, pandas as pd, geopandas as gpd
from scipy.spatial import cKDTree
shp = sys.argv[1]
rng = np.random.default_rng(3)
a = pd.read_csv("q_classic/areas.csv", dtype=str)
G = gpd.read_file(shp).to_crs(7856).set_index("SA2_CODE21").loc[a.SA2_CODE21].reset_index()
pairs = gpd.sjoin(G[["geometry"]], G[["geometry"]], predicate="touches"); pairs = pairs[pairs.index < pairs.index_right]
E = []
for i, j in zip(pairs.index, pairs.index_right):
    L = G.geometry[i].boundary.intersection(G.geometry[j].boundary).length
    if L >= 100: E.append((i, j, L))
E = np.array(E); I, J, W = E[:, 0].astype(int), E[:, 1].astype(int), E[:, 2]
rep = np.column_stack([G.geometry.representative_point().x, G.geometry.representative_point().y])
d = pd.read_pickle("places.pkl"); d = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d.lon, d.lat), crs=4326).to_crs(7856)
xy = np.column_stack([d.geometry.x, d.geometry.y])
food = d.t.apply(lambda q: q.get("amenity") in ("cafe", "fast_food", "restaurant")).values
def cut(field):
    s = field > np.median(field); return ((s[I] != s[J]) * W).sum() / (0.5 * W.sum())
def brand(*n): return d.t.apply(lambda q: any(x in (q.get("brand", "") + "|" + q.get("name", "")).lower() for x in n)).values
brands = {"Red Rooster": brand("red rooster"), "El Jannah": brand("el jannah"), "KFC": brand("kfc"), "McDonald's": brand("mcdonald"),
          "Oporto": brand("oporto"), "Guzman y Gomez": brand("guzman"), "Nando's": brand("nando"), "Starbucks": brand("starbucks"),
          "Gloria Jean's": brand("gloria jean"), "Messina": brand("messina"), "Krispy Kreme": brand("krispy kreme"),
          "Aldi": brand("aldi"), "Dan Murphy's": brand("dan murphy"), "F45": brand("f45"), "Anytime Fitness": brand("anytime fitness")}
rows = []
fidx = np.where(food)[0]
for k, m in brands.items():
    nst = int(m.sum()); obs = cut(cKDTree(xy[m]).query(rep)[0])
    fake = np.array([cut(cKDTree(xy[rng.choice(fidx, nst, replace=False)]).query(rep)[0]) for _ in range(300)])
    rows.append(dict(brand=k, stores_in_osm=nst, line_cleanness=round(obs, 3), fake_chain_median=round(np.median(fake), 3),
                     p_vs_fake=round((1 + (fake <= obs).sum()) / 301, 3)))
R = pd.DataFrame(rows).sort_values("p_vs_fake"); print(R.to_string(index=False)); R.to_csv("brand_chain_test.csv", index=False)
