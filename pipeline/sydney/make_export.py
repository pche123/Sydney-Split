"""Data for live in-browser features: Make your own line, Chain vs chain, smoothness slider."""
import os
RAW = os.environ.get("SPLIT_RAW", "../data")   # raw downloads (see README)
import json, base64, re, numpy as np, pandas as pd, geopandas as gpd
W = "."
src = open(f"{W}/export_app.py").read()
exec(open(f"{W}/labels.py").read())                                 # plain-English names: name / more / less
a = pd.read_csv(f"{W}/q_classic/areas.csv", dtype=str)
G = gpd.read_file(f"{RAW}/shp/SA2_2021_AUST_GDA2020.shp").to_crs(7856).set_index("SA2_CODE21").loc[a.SA2_CODE21].reset_index()
n = len(G)
sig = pd.read_csv(f"{W}/signals_all.csv", dtype={"SA2_CODE_2021": str}).set_index("SA2_CODE_2021").loc[a.SA2_CODE21].reset_index(drop=True)

def group(c):
    if c.startswith(("share_cuisine_", "share_super_", "share_cafe", "share_fast", "share_bakery", "share_butcher", "share_conv", "food_venues")): return "Food & shops"
    if c.startswith(("share_pub", "share_bar", "share_liquor", "late_", "very_late", "pokies", "small_bars", "clubs")): return "After dark"
    if c.startswith("share_gym"): return "Food & shops"
    if c.startswith(("works_", "managers", "professionals", "tradies", "labourers", "drivers", "care_service", "work_from")): return "Work"
    if c.endswith(("_commute", "_to_work")) or c in ("no_car", "three_plus_cars"): return "Getting around"
    if c in ("detached_houses", "townhouses", "apartments", "high_rise_9plus", "empty_dwellings", "owned_outright", "mortgaged", "renting_private",
             "social_housing", "four_plus_bedrooms", "median_rent_weekly", "median_mortgage_repay_monthly", "average_num_psns_per_bedroom"): return "Homes"
    return "People"
LABEL = {"median_age_persons": "median age", "median_tot_hhd_inc_weekly": "household income", "median_rent_weekly": "rent",
         "median_mortgage_repay_monthly": "mortgage repayments", "average_household_size": "household size", "average_num_psns_per_bedroom": "people per bedroom"}
signals = []
for c in sig.columns:
    if c == "population" or c.startswith("near_"): continue        # single-brand distances are geometry, not culture (fake-chain test)
    v = sig[c].astype(float)
    signals.append(dict(id=c, label=name(c), more=more(c), less=less(c), group=group(c), v=[None if np.isnan(x) else round(float(x), 5) for x in v]))

# border graph
pairs = gpd.sjoin(G[["geometry"]], G[["geometry"]], predicate="touches"); pairs = pairs[pairs.index < pairs.index_right]
E = np.array([e for e in [(i, j, G.geometry[i].boundary.intersection(G.geometry[j].boundary).length) for i, j in zip(pairs.index, pairs.index_right)] if e[2] >= 100])
I, J, L = E[:, 0].astype(int), E[:, 1].astype(int), E[:, 2]
# spatial basis for the chance test (Moran eigenvectors of the border graph, largest eigenvalue first)
Ad = np.zeros((n, n)); Ad[I, J] = 1; Ad[J, I] = 1; Mc = np.eye(n) - 1 / n
vals, vecs = np.linalg.eigh(Mc @ Ad @ Mc); vecs = vecs[:, np.argsort(vals)[::-1]].astype(np.float32)
eig = base64.b64encode(vecs.tobytes(order="C")).decode()

# stores (metres for maths, viewBox coords for drawing: same projection as the app)
Gs = G.copy(); Gs["geometry"] = Gs.geometry.simplify(70, preserve_topology=True)
minx, miny, maxx, maxy = Gs.total_bounds; S = 1000 / (maxx - minx)
d = pd.read_pickle(f"{W}/places.pkl"); d = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d.lon, d.lat), crs=4326).to_crs(7856)
inside = d.geometry.within(G.geometry.union_all().buffer(3000)); d = d[inside]
def brand(*nm): return d.t.apply(lambda q: any(x in (q.get("brand", "") + "|" + q.get("name", "")).lower() for x in nm)).values
BR = {"Red Rooster": ("red rooster",), "El Jannah": ("el jannah",), "KFC": ("kfc",), "McDonald's": ("mcdonald",), "Hungry Jack's": ("hungry jack",),
      "Oporto": ("oporto",), "Nando's": ("nando",), "Guzman y Gomez": ("guzman",), "Subway": ("subway",), "Domino's": ("domino",),
      "Starbucks": ("starbucks",), "Gloria Jean's": ("gloria jean",), "Messina": ("messina",), "Krispy Kreme": ("krispy kreme",),
      "Gong Cha": ("gong cha",), "Chatime": ("chatime",), "Boost Juice": ("boost juice",), "Grill'd": ("grill'd", "grilld"),
      "Aldi": ("aldi",), "Woolworths": ("woolworths",), "Coles": ("coles",), "IGA": ("iga",), "7-Eleven": ("7-eleven",),
      "Dan Murphy's": ("dan murphy",), "BWS": ("bws",), "Anytime Fitness": ("anytime fitness",), "F45": ("f45",)}
brands = []
for nm, keys in BR.items():
    m = brand(*keys)
    if nm == "IGA": m = m & d.t.apply(lambda q: q.get("shop") == "supermarket").values
    if m.sum() < 8: continue
    xs, ys = d.geometry.x.values[m], d.geometry.y.values[m]
    brands.append(dict(name=nm, n=int(m.sum()), xy=[[round(float(x)), round(float(y))] for x, y in zip(xs, ys)],
                       vb=[[round(float((x - minx) * S), 1), round(float((maxy - y) * S), 1)] for x, y in zip(xs, ys)]))
def P(x, y): return f"{(x - minx) * S:.1f},{(maxy - y) * S:.1f}"
def lp(g):
    if g.geom_type == "LineString": return "M" + "L".join(P(x, y) for x, y in g.coords)
    if hasattr(g, "geoms"): return "".join(lp(h) for h in g.geoms)
    return ""
from shapely.ops import linemerge
epaths = []
for i, j in zip(I, J):
    seg = G.geometry[i].boundary.intersection(G.geometry[j].boundary)
    parts = [h for h in getattr(seg, "geoms", [seg]) if h.geom_type in ("LineString", "MultiLineString")]
    try: seg = linemerge(parts) if parts else seg
    except Exception: pass
    epaths.append(lp(seg.simplify(30)))
rep = G.geometry.representative_point()
out = json.load(open(f"{W}/app_data.json"))
out["make"] = dict(signals=signals, I=I.tolist(), J=J.tolist(), L=[round(float(x) / 1000, 3) for x in L], eig=eig, n=n,
                   pop=[int(p) for p in sig.population.values], ep=epaths, rep=[[round(float(p.x)), round(float(p.y))] for p in rep], brands=brands)
json.dump(out, open(f"{W}/app_data.json", "w"), separators=(",", ":"))
print("signals", len(signals), "edges", len(I), "brands", [(b["name"], b["n"]) for b in brands])
print("app_data.json MB:", round(len(json.dumps(out, separators=(",", ":"))) / 1e6, 2))
# reference values to check the JavaScript later
from scipy.stats import norm, rankdata
def rz(v): v = pd.Series(v).fillna(pd.Series(v).median()).values; return norm.ppf((rankdata(v) - 0.5) / n)
f = rz(sig.share_cafe) - rz(sig.share_fast_food); s = f > np.median(f)
print("REF cafes-vs-fastfood cleanness:", round(((s[I] != s[J]) * L).sum() / (0.5 * L.sum()), 4))
