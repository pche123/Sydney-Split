"""Exploratory (suggested by a reader, not pre-registered): Paris boulangeries (shop=bakery) vs pâtisseries (shop=pastry).

    python experiments/paris_bakeries.py <folder with phase2/paris/raw/osm/places.csv>

Viennoiserie (croissants, pains au chocolat) has no tag of its own in OpenStreetMap: it is sold in boulangeries.
Same cells, field and quick test as experiments/phase2_food.py.
"""
import ast, os, sys
import numpy as np, pandas as pd, geopandas as gpd
from pyproj import Transformer
from scipy.stats import norm, rankdata
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path[:0] = [ROOT]
from linetests.landscape import MultiScaleNull
P = pd.read_csv(f"{sys.argv[1]}/phase2/paris/raw/osm/places.csv"); sh = P.tags.map(lambda s: ast.literal_eval(s).get("shop"))
G = gpd.read_file(os.path.join(ROOT, "results", "phase2", "food", "paris", "areas.gpkg")); z = np.load(os.path.join(ROOT, "results", "phase2", "food", "paris", "fields.npz"))
X, Y = Transformer.from_crs(4326, 3035, always_xy=True).transform(P.lon.values, P.lat.values)
key = {(int(a), int(b)): i for i, (a, b) in enumerate(zip(G.x, G.y))}
idx = np.array([key.get((int(np.floor(a / 1000) * 1000), int(np.floor(b / 1000) * 1000)), -1) for a, b in zip(X, Y)])
k = idx >= 0; A = np.bincount(idx[k & (sh == "bakery").values], minlength=len(G)); B = np.bincount(idx[k & (sh == "pastry").values], minlength=len(G))
f = np.log((A + 0.5) / (B + 0.5)) + 1e-9 * np.random.default_rng(0).normal(size=len(G))
p = MultiScaleNull(G.geometry, z["I"], z["J"], z["W"], m=9).test(norm.ppf((rankdata(f) - 0.5) / len(f)), 199, seed=11)[0]
c = G.geometry.centroid; rho = pd.Series(f).corr(pd.Series(np.hypot(c.x - c.x.mean(), c.y - c.y.mean()).values), method="spearman")
print(f"boulangeries {A.sum()} vs patisseries {B.sum()} in {len(G)} cells: quick p = {p:.3f}, slope with distance rho = {rho:.2f}")
