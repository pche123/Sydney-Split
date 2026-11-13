"""Venue signals per SA2 from OSM places + NSW liquor licences.

Three kinds of signal, chosen so dense CBD areas don't win everything:
  share_*  : mix of venues (e.g. cafes as a share of all food venues), counted in the area plus its neighbours
  near_*   : distance (log km) from the area to the nearest outlet of a brand/type  -> catchment lines
  *_per_1k : per-resident rates for licensing data (late licences, pokies)
Usage: python build_poi.py <sa2_shp> <places.pkl> <premises.xlsx> <signals_sa2.csv> <out.csv>
"""
import sys, numpy as np, pandas as pd, geopandas as gpd
from scipy.spatial import cKDTree

shp, places, prem, census, out = sys.argv[1:6]
g = gpd.read_file(shp); g = g[g.GCC_CODE21 == "1GSYD"].to_crs(7856).reset_index(drop=True)
pop = pd.read_csv(census, dtype={"SA2_CODE_2021": str}).set_index("SA2_CODE_2021")["population"]
g["population"] = g.SA2_CODE21.map(pop)

d = pd.read_pickle(places)
d = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d.lon, d.lat), crs=4326).to_crs(7856)
t = d.t
def cuisine_has(x): return t.apply(lambda q: x in [c.strip() for c in q.get("cuisine", "").split(";")])
def brand_is(*names): return t.apply(lambda q: any(n.lower() in (q.get("brand", "") + "|" + q.get("name", "")).lower() for n in names))
am, sh = t.apply(lambda q: q.get("amenity")), t.apply(lambda q: q.get("shop"))

food = am.isin(["cafe", "fast_food", "restaurant", "pub", "bar", "food_court", "ice_cream"])
eats = am.isin(["fast_food", "restaurant", "food_court"])
supers = sh.eq("supermarket")
flags = {
    "cafe": am.eq("cafe"), "fast_food": am.eq("fast_food"), "pub": am.eq("pub"), "bar": am.eq("bar"),
    "bakery": sh.eq("bakery"), "butcher": sh.eq("butcher"), "liquor_shop": sh.eq("alcohol"), "convenience": sh.eq("convenience"),
    "gym": t.apply(lambda q: q.get("leisure") == "fitness_centre"),
}
cuis = ["thai", "vietnamese", "chinese", "japanese", "korean", "indian", "italian", "greek", "lebanese", "kebab",
        "pizza", "burger", "chicken", "sushi", "bubble_tea", "mexican", "fish_and_chips", "portuguese", "turkish", "nepalese", "seafood"]
for c in cuis: flags[f"cuisine_{c}"] = cuisine_has(c)
supbrand = {"aldi": brand_is("aldi"), "woolworths": brand_is("woolworths"), "coles": brand_is("coles"), "iga": brand_is("iga")}

# counts in each SA2
j = gpd.sjoin(d[["geometry"]], g[["geometry"]], predicate="within")["index_right"].reindex(d.index)
def count(mask): return pd.Series(mask.values, index=d.index)[mask.values].groupby(j[mask.values]).size().reindex(g.index, fill_value=0)
# neighbour smoothing: area + touching areas
nb = gpd.sjoin(g[["geometry"]], g[["geometry"]], predicate="touches")
NB = {i: set(nb.index_right[nb.index == i]) | {i} for i in g.index}
def ring(c): return pd.Series({i: c[list(NB[i])].sum() for i in g.index})

S = {}
nfood, neats, nsup = ring(count(food)), ring(count(eats)), ring(count(supers))
for k, m in flags.items():
    den = neats if k.startswith("cuisine_") else nfood
    S[f"share_{k}"] = (ring(count(m)) + 0.5) / (den + 5)            # light prior so tiny counts don't blow up
for k, m in supbrand.items():
    S[f"share_super_{k}"] = (ring(count(m & supers)) + 0.25) / (nsup + 1)
S["food_venues_per_1k"] = count(food) / g.population.clip(lower=100) * 1000

# nearest-outlet distances (catchments)
rep = np.column_stack([g.geometry.representative_point().x, g.geometry.representative_point().y])
xy = np.column_stack([d.geometry.x, d.geometry.y])
near = {"red_rooster": brand_is("red rooster"), "el_jannah": brand_is("el jannah"), "kfc": brand_is("kfc"),
        "mcdonalds": brand_is("mcdonald"), "oporto": brand_is("oporto"), "guzman": brand_is("guzman"),
        "nandos": brand_is("nando"), "starbucks": brand_is("starbucks"), "gloria_jeans": brand_is("gloria jean"),
        "messina": brand_is("messina"), "krispy_kreme": brand_is("krispy kreme"), "aldi": brand_is("aldi"),
        "dan_murphys": brand_is("dan murphy"), "f45": brand_is("f45"), "anytime_fitness": brand_is("anytime fitness"),
        "bubble_tea": flags["cuisine_bubble_tea"], "train_station": t.apply(lambda q: q.get("railway") == "station"),
        "gelato_or_ice_cream": am.eq("ice_cream")}
for k, m in near.items():
    if m.sum() == 0: continue
    dist, _ = cKDTree(xy[m.values]).query(rep)
    S[f"near_{k}"] = np.log1p(dist / 1000)
    print(f"near_{k}: {int(m.sum())} outlets")

# liquor licences
p = pd.read_excel(prem, header=3)
p = p[(p.Status == "Current") & p.Latitude.notna()]
p = gpd.GeoDataFrame(p, geometry=gpd.points_from_xy(p.Longitude, p.Latitude), crs=4326).to_crs(7856)
pj = gpd.sjoin(p, g[["geometry"]], predicate="within")
def per1k(mask, col=None):
    sub = pj[mask.loc[pj.index]]
    v = sub.groupby("index_right").size() if col is None else sub.groupby("index_right")[col].sum()
    return ring(v.reindex(g.index, fill_value=0)) / ring(g.population.fillna(0)).clip(lower=500) * 1000
S["late_licences_per_1k"] = per1k(p["After 12am"].eq("Yes"))
S["very_late_3am_per_1k"] = per1k(p["After 3am"].eq("Yes"))
S["pokies_per_1k"] = per1k(p.EGMs.fillna(0) > 0, "EGMs")
S["small_bars_per_1k"] = per1k(p["Licence type"].eq("Liquor - small bar licence"))
S["clubs_per_1k"] = per1k(p["Licence type"].eq("Liquor - club licence"))
late = p[p["After 12am"].eq("Yes") & p["Licence type"].isin(["Liquor - hotel licence", "Liquor - small bar licence", "Liquor - on-premises licence"])]
S["near_late_night_venue"] = np.log1p(cKDTree(np.column_stack([late.geometry.x, late.geometry.y])).query(rep)[0] / 1000)

o = pd.DataFrame(S); o.index = g.SA2_CODE21.values; o.index.name = "SA2_CODE_2021"
c = pd.read_csv(census, dtype={"SA2_CODE_2021": str}).set_index("SA2_CODE_2021")
allsig = c.join(o, how="inner")
allsig.to_csv(out)
print("venue signals", o.shape[1], "total signals", allsig.shape[1] - 1)
