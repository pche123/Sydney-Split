"""Build app_data_tokyo.json for the Tokyo / Split web app (same format as the Sydney app).

Neighbourhoods: the 1,402 study 町 are merged, inside each ward or city, into suburb-sized areas of about 30,000 people
(contiguous, by Ward clustering on location with a border-sharing constraint). Every line is re-tested on these areas.
python tokyo_app_export.py out hotpepper_tokyo.csv tplaces.pkl app_data_tokyo.json
"""
import sys, os, json, re, base64, numpy as np, pandas as pd, geopandas as gpd
from scipy.spatial import cKDTree
from scipy.stats import norm, rankdata
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.cluster import AgglomerativeClustering
from shapely.ops import linemerge
from shapely.geometry import MultiLineString
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from romaji import place, city
from ramen_styles import style, STYLES
out, hpfile, tpl, outfile = sys.argv[1:5]
CRS = 6677; NN = 499; rng = np.random.default_rng(21); TARGET = 30000

# ------------------------------------------------------------------ neighbourhoods
U = gpd.read_file(f"{out}/tokyo_units.gpkg"); st = pd.read_csv(f"{out}/study_units.csv", dtype=str).U
U = U.set_index("U").loc[st].reset_index()
E0 = np.load(f"{out}/edges.npy"); I0, J0, W0 = E0[:, 0].astype(int), E0[:, 1].astype(int), E0[:, 2]
xy0 = np.column_stack([U.geometry.representative_point().x, U.geometry.representative_point().y])
lab = np.full(len(U), -1); nxt = 0
for cname, idx in U.groupby("CITY_NAME").indices.items():
    idx = np.array(sorted(idx)); pos = {g: k for k, g in enumerate(idx)}
    m = np.isin(I0, idx) & np.isin(J0, idx)
    A = coo_matrix((np.ones(m.sum()), ([pos[i] for i in I0[m]], [pos[j] for j in J0[m]])), shape=(len(idx), len(idx)))
    A = ((A + A.T) > 0).astype(float)
    ncomp, comp = connected_components(A, directed=False)
    for c in range(ncomp):
        sub = np.where(comp == c)[0]; pop = U.population.values[idx[sub]].sum()
        k = int(max(1, round(pop / TARGET)))
        if k >= len(sub): l = np.arange(len(sub))
        elif k == 1: l = np.zeros(len(sub), int)
        else: l = AgglomerativeClustering(n_clusters=k, connectivity=A.tocsr()[sub][:, sub], linkage="ward").fit_predict(xy0[idx[sub]])
        for u in np.unique(l): lab[idx[sub[l == u]]] = nxt; nxt += 1
U["N"] = lab; n = nxt
print("neighbourhoods:", n, "median people", int(U.groupby("N").population.sum().median()))

shares = ["age_65_plus", "age_20_39", "kids_under_15", "living_alone", "families_with_kids", "owners", "renters", "detached_houses",
          "towers_11_floors_plus", "managers", "professionals", "office_workers", "sales_workers", "service_workers", "factory_workers",
          "drivers", "builders", "cleaning_packing", "hivis_jobs", "laptop_jobs", "ind_it", "ind_manufacturing", "ind_finance",
          "ind_hospitality", "ind_health", "ind_construction", "ind_transport", "ind_retail", "self_employed"]
w = U.population.clip(lower=1)
G = U.dissolve("N", aggfunc={"population": "sum", "CITY_NAME": "first"}).sort_index().reset_index()
for c in shares: G[c] = (U[c].fillna(U[c].median()) * w).groupby(U.N).sum().values / w.groupby(U.N).sum().values
G["density"] = G.population / (G.area / 1e6)
# ---- extra 2020 Census tables from e-Stat's file section: foreign residents, education, commuting
def estat(path, hdr):
    t = pd.read_csv(path, encoding="cp932", header=None, skiprows=hdr + 1, dtype=str)
    cols = pd.read_csv(path, encoding="cp932", header=None, skiprows=hdr, nrows=1, dtype=str).iloc[0].tolist()
    t.columns = [f"{c}_{k}" if cols.count(c) > 1 else c for k, c in enumerate(cols)]
    if "男女" in t: t = t[t["男女"] == "総数"]
    t = t[t["地域階層レベル"].isin(["2", "3"]) & (t["町丁字コード"].str.len() == 4)]
    t["U"] = t["市区町村コード"] + t["町丁字コード"]
    return t.set_index("U")
num = lambda x: pd.to_numeric(x, errors="coerce").fillna(0)
xdir = os.path.join(os.path.dirname(os.path.abspath(tpl)), "extra")
fo = estat(f"{xdir}/c919f8a5-h02_13.csv", 4); ed = estat(f"{xdir}/903ca4e4-h13_13.csv", 3); cm = estat(f"{xdir}/2e0e825e-h17_02_13.csv", 4)
X = pd.DataFrame(index=U.U)
X["pop_all"] = num(fo["総数"]).reindex(U.U).values; X["foreign"] = num(fo[fo.columns[-2]]).reindex(U.U).values
X["grads"] = (num(ed["卒業者"]) - num(ed["（卒業者）不詳"])).reindex(U.U).values; X["degree"] = (num(ed["（卒業者）大学"]) + num(ed["（卒業者）大学院"])).reindex(U.U).values
X["commuters"] = num(cm["総数"]).reindex(U.U).values
for k, c in [("train", "鉄道・電車"), ("car", "自家用車"), ("bike", "自転車"), ("walk", "徒歩のみ"), ("bus", "乗合バス")]: X[k] = num(cm[c]).reindex(U.U).values
X = X.fillna(0); XN = X.groupby(U.N.values).sum().sort_index()
G["foreign_residents"] = XN.foreign.values / XN.pop_all.replace(0, np.nan).values
G["uni_degree"] = XN.degree.values / XN.grads.replace(0, np.nan).values
for k in ["train", "car", "bike", "walk", "bus"]: G[k + "_commute"] = XN[k].values / XN.commuters.replace(0, np.nan).values
print("Tokyo-wide: foreign %.1f%%, degree %.1f%%, train %.1f%%, car %.1f%%" % (100 * XN.foreign.sum() / XN.pop_all.sum(), 100 * XN.degree.sum() / XN.grads.sum(),
      100 * XN.train.sum() / XN.commuters.sum(), 100 * XN.car.sum() / XN.commuters.sum()))
top = U.loc[U.groupby("N").population.idxmax()].set_index("N").sort_index()
G["jp"] = top.CITY_NAME.values + top.NAME.values
G["short"] = [place(x) for x in top.NAME.values]
dup = G.short.duplicated(keep=False)
G.loc[dup, "short"] = G.short[dup] + " (" + [city(c) for c in G.CITY_NAME[dup]] + ")"
dup = G.short.duplicated(keep=False)
G.loc[dup, "short"] = G.short[dup] + " " + G[dup].groupby("short").cumcount().add(1).astype(str)
G["name"] = G.short + ", " + pd.Series([city(c) for c in G.CITY_NAME]) + " · " + top.NAME.values + " area"
# border graph between neighbourhoods
ln = pd.DataFrame({"a": U.N.values[I0], "b": U.N.values[J0], "w": W0}); ln = ln[ln.a != ln.b]
ln[["a", "b"]] = np.sort(ln[["a", "b"]].values, 1); ln = ln.groupby(["a", "b"]).w.sum().reset_index(); ln = ln[ln.w >= 100]
I, J, W = ln.a.values.astype(int), ln.b.values.astype(int), ln.w.values
Ad = np.zeros((n, n)); Ad[I, J] = 1; Ad[J, I] = 1; Mc = np.eye(n) - 1 / n
vals, vecs = np.linalg.eigh(Mc @ Ad @ Mc); vecs = vecs[:, np.argsort(vals)[::-1]]
rep = np.column_stack([G.geometry.representative_point().x, G.geometry.representative_point().y])

def rz(v): v = pd.Series(v).fillna(pd.Series(v).median()).values; return norm.ppf((rankdata(v) - 0.5) / len(v))
def cut(f): s = f > np.median(f); return ((s[I] != s[J]) * W).sum() / (0.5 * W.sum()), s
def rot_null(f):
    f = (f - f.mean()) / f.std(); c = vecs.T @ f; res = []
    for _ in range(NN):
        cr = c.copy()
        for x in range(0, n, 12):
            y = min(x + 12, n); q, _ = np.linalg.qr(rng.normal(size=(y - x, y - x))); cr[x:y] = q @ c[x:y]
        res.append(cut(vecs @ cr)[0])
    return np.array(res)

# ------------------------------------------------------------------ venues (OSM, HotPepper, places of worship)
V = pd.read_pickle(f"{out}/venues.pkl"); T = pd.read_pickle(tpl)
V["shrine"] = T.t.map(lambda q: q.get("amenity") == "place_of_worship" and q.get("religion") == "shinto").values
V["temple"] = T.t.map(lambda q: q.get("amenity") == "place_of_worship" and q.get("religion") == "buddhist").values
V["church"] = T.t.map(lambda q: q.get("amenity") == "place_of_worship" and q.get("religion") == "christian").values
V["worship"] = V.shrine | V.temple | V.church
V["chain_cafe"] = V.cafe & ~V.indie_cafe
vg = gpd.GeoDataFrame(V, geometry=gpd.points_from_xy(V.x, V.y), crs=CRS)
jv = gpd.sjoin(vg[["geometry"]], G[["geometry"]], predicate="within")
WALK = 1000.0  # metres from each neighbourhood's centre, about a 12-15 minute walk
_nv = cKDTree(V[["x", "y"]].values).query_ball_point(rep, WALK)
def ncount(col): v = V[col].values; return np.array([v[ix].sum() for ix in _nv], float)
h = pd.read_csv(hpfile, low_memory=False, dtype={"sub_genre": str})
h = gpd.GeoDataFrame(h, geometry=gpd.points_from_xy(h.lng, h.lat), crs=4326).to_crs(CRS)
h["price"] = h.budget.fillna("").str.replace(",", "").str.extract(r"(\d+)～(\d+)円").astype(float).mean(axis=1)
h["late"] = h.midnight.eq("営業している"); gc = h.genre_code
HP = {"hp_all": np.ones(len(h), bool), "hp_late": h.late.values, "hp_izakaya": gc.eq("G001").values, "hp_italian": gc.eq("G006").values,
      "hp_bar": gc.isin(["G012", "G002"]).values, "hp_yakiniku": gc.eq("G008").values, "hp_korean": gc.eq("G017").values}
jh = gpd.sjoin(h[["geometry"]], G[["geometry"]], predicate="within")
_nh = cKDTree(np.column_stack([h.geometry.x, h.geometry.y])).query_ball_point(rep, WALK)
def hcount(m): return np.array([m[ix].sum() for ix in _nh], float)
C = {k: ncount(k) for k in ["food", "cafe", "fast_food", "izakaya_bar", "ramen", "soba_udon", "sushi", "curry", "indian_nepali", "yakiniku",
                             "indie_cafe", "chain_cafe", "konbini", "my_basket", "shrine", "temple", "church", "worship", "station"]}
C.update({k: hcount(m) for k, m in HP.items()})
_pv = h.price.values
price = np.array([np.nanmean(_pv[ix]) if np.isfinite(_pv[ix]).sum() >= 5 else np.nan for ix in _nh])
def ratio(a, b): return (C[a] + 0.5) / (C[a] + C[b] + 1)
def share(a, tot): return (C[a] + 0.5) / (C[tot] + 1)

# ------------------------------------------------------------------ plain words
LBL = {  # id: (label, more ..., fewer ...)
 "age_65_plus": ("Aged 65+", "more over-65s", "fewer over-65s"), "age_20_39": ("Aged 20-39", "more people in their 20s and 30s", "fewer people in their 20s and 30s"),
 "kids_under_15": ("Kids", "more kids", "fewer kids"), "living_alone": ("Living alone", "more people living alone", "fewer people living alone"),
 "families_with_kids": ("Families with kids", "more families with kids", "fewer families with kids"), "owners": ("Home owners", "more home owners", "fewer home owners"),
 "renters": ("Renters", "more renters", "fewer renters"), "detached_houses": ("Detached houses", "more detached houses", "fewer detached houses"),
 "towers_11_floors_plus": ("Homes in 11+ floor blocks", "more homes in tall blocks", "fewer homes in tall blocks"),
 "managers": ("Managers", "more managers", "fewer managers"), "professionals": ("Professionals", "more professionals", "fewer professionals"),
 "office_workers": ("Office workers", "more office workers", "fewer office workers"), "sales_workers": ("Sales workers", "more sales workers", "fewer sales workers"),
 "service_workers": ("Service workers", "more service workers", "fewer service workers"), "factory_workers": ("Factory workers", "more factory workers", "fewer factory workers"),
 "drivers": ("Drivers", "more drivers & machine operators", "fewer drivers & machine operators"), "builders": ("Builders", "more builders", "fewer builders"),
 "cleaning_packing": ("Cleaning & packing jobs", "more cleaning & packing jobs", "fewer cleaning & packing jobs"),
 "hivis_jobs": ("Hi-vis jobs", "more hi-vis jobs", "fewer hi-vis jobs"), "laptop_jobs": ("Managers & professionals", "more managers & professionals", "fewer managers & professionals"),
 "ind_it": ("IT workers", "more IT workers", "fewer IT workers"), "ind_manufacturing": ("Manufacturing", "more manufacturing workers", "fewer manufacturing workers"),
 "ind_finance": ("Finance workers", "more finance workers", "fewer finance workers"), "ind_hospitality": ("Hospitality workers", "more hospitality workers", "fewer hospitality workers"),
 "ind_health": ("Health & care workers", "more health & care workers", "fewer health & care workers"), "ind_construction": ("Construction", "more construction workers", "fewer construction workers"),
 "ind_transport": ("Transport & logistics", "more transport & logistics workers", "fewer transport & logistics workers"),
 "ind_retail": ("Retail & wholesale", "more retail & wholesale workers", "fewer retail & wholesale workers"),
 "self_employed": ("Self-employed", "more self-employed people", "fewer self-employed people"),
 "uni_degree": ("University graduates", "more university graduates", "fewer university graduates"),
 "train_commute": ("Train commuters", "more people commuting by train", "fewer people commuting by train"),
 "car_commute": ("Car commuters", "more people driving to work", "fewer people driving to work"),
 "bike_commute": ("Bike commuters", "more people cycling to work", "fewer people cycling to work"),
 "walk_commute": ("Walk to work", "more people walking to work", "fewer people walking to work"), "density": ("Density", "more people per km²", "fewer people per km²"),
}
census = list(LBL)
Z = np.column_stack([rz(G[c]) for c in census])
def chips(s, used):
    eff = Z[s].mean(0) - Z[~s].mean(0); keep = [k for k in range(len(census)) if census[k] not in used]
    hi = sorted(keep, key=lambda k: -eff[k])[:5]; lo = sorted(keep, key=lambda k: eff[k])[:5]
    return [LBL[census[k]][1] for k in hi if eff[k] > 0.15], [LBL[census[k]][1] for k in lo if eff[k] < -0.15]

# ------------------------------------------------------------------ chain points (shared with the Make tab)
minx, miny, maxx, maxy = G.total_bounds; S = 1000 / (maxx - minx); Hh = (maxy - miny) * S
oxy = V[["x", "y"]].values; hxy = np.column_stack([h.geometry.x, h.geometry.y])
ram_o = V.ramen.values; osty = np.full(len(V), None, object)
for k in STYLES: osty[V["ramen_" + k].values] = k
hp_r = (gc.eq("G013") | h.name.str.contains("ラーメン|らーめん|中華そば|つけ麺|家系", regex=True)).values
hsty = np.array([style(a, f"{b} {c}") if r else None for a, b, c, r in zip(h.name, h.genre_catch.fillna(""), h["catch"].fillna(""), hp_r)], object)
d_, ix = cKDTree(oxy[ram_o]).query(hxy[hp_r]); oi = np.where(ram_o)[0][ix]; same = d_ < 60
for hi_, o_ in zip(np.where(hp_r)[0][same], oi[same]):
    if osty[o_] is None and hsty[hi_] is not None: osty[o_] = hsty[hi_]
newh = np.where(hp_r)[0][~same]
rxy = np.vstack([oxy[ram_o], hxy[newh]]); rst = np.concatenate([osty[ram_o], hsty[newh]])
PTS = {"7-Eleven": oxy[V.seven_eleven.values], "FamilyMart": oxy[V.familymart.values], "Lawson": oxy[V.lawson.values], "Ministop": oxy[V.ministop.values],
       "My Basket": oxy[V.my_basket.values], "Starbucks": oxy[V.starbucks.values], "Doutor": oxy[V.doutor.values], "Tully's": oxy[V.tullys.values],
       "Komeda": oxy[V.komeda.values], "Matsuya": oxy[V.matsuya.values], "Sukiya": oxy[V.sukiya.values], "Yoshinoya": oxy[V.yoshinoya.values],
       "CoCo Ichibanya": oxy[V.coco_ichi.values], "Saizeriya": oxy[V.saizeriya.values], "Gusto": oxy[V.gusto.values], "McDonald's": oxy[V.mcdonalds.values],
       "Mos Burger": oxy[V.mos_burger.values], "Hidakaya": oxy[V.hidakaya.values],
       "Iekei ramen": rxy[rst == "iekei"], "Hakata tonkotsu ramen": rxy[rst == "tonkotsu"], "Jiro-style ramen": rxy[rst == "jiro"],
       "Classic shoyu ramen": rxy[rst == "shoyu_classic"], "Miso ramen": rxy[rst == "miso"], "Tsukemen": rxy[rst == "tsukemen"],
       "Shinto shrines": oxy[V.shrine.values], "Buddhist temples": oxy[V.temple.values], "Christian churches": oxy[V.church.values]}
np.savez(f"{out}/tokyo_chains.npz", **{k.replace(" ", "_").replace("'", ""): v for k, v in PTS.items()})
def field(A, B, off=50.0): return np.log(cKDTree(B).query(rep)[0] + off) - np.log(cKDTree(A).query(rep)[0] + off)
def swap_null(A, B):
    P = np.vstack([A, B]); na = len(A); res = []
    for _ in range(NN):
        p = rng.permutation(len(P)); res.append(cut(field(P[p[:na]], P[p[na:]]))[0])
    return np.array(res)

# ------------------------------------------------------------------ the lines
L = [  # id, name, group, kind, spec, orange, blue, used-census
 ("the-hi-vis-line", "The Hi-Vis Line", "Work", "share", (rz(G.hivis_jobs) - rz(G.laptop_jobs)), "More factory, driving, building & cleaning jobs", "More managers & professionals", ["hivis_jobs", "laptop_jobs", "managers", "professionals", "factory_workers", "drivers", "builders", "cleaning_packing"]),
 ("the-latte-line", "The Latte Line", "Food", "share", rz(share("cafe", "food")) - rz(share("fast_food", "food")), "More cafés, less fast food", "More fast food, fewer cafés", []),
 ("the-factory-line", "The Factory Line", "Work", "share", rz(G.factory_workers), "More factory workers", "Fewer factory workers", ["factory_workers", "ind_manufacturing", "hivis_jobs"]),
 ("the-laptop-vs-hard-hat-line", "The Laptop vs Hard Hat Line", "Work", "share", rz(G.ind_it) - rz(G.builders), "More IT workers, fewer builders", "More builders, fewer IT workers", ["ind_it", "builders", "ind_construction"]),
 ("the-boomer-vs-builder-line", "The Boomer vs Builder Line", "Work", "share", rz(G.age_65_plus) - rz(G.builders), "Older residents, fewer builders", "Younger residents, more builders", ["age_65_plus", "builders", "ind_construction", "age_20_39"]),
 ("the-degree-line", "The Degree Line", "Work", "share", rz(G.uni_degree), "More university graduates", "Fewer university graduates", ["uni_degree", "laptop_jobs", "professionals", "managers"]),
 ("train-vs-car", "Train vs Car", "Around", "share", rz(G.train_commute) - rz(G.car_commute), "More people commute by train", "More people drive to work", ["train_commute", "car_commute"]),
 ("the-bicycle-line", "The Bicycle Line", "Around", "share", rz(G.bike_commute), "More people cycle to work", "Fewer people cycle to work", ["bike_commute"]),
 ("the-living-alone-line", "The Living Alone Line", "Homes", "share", rz(G.living_alone) - rz(G.families_with_kids), "More people living alone", "More families with kids", ["living_alone", "families_with_kids", "kids_under_15"]),
 ("the-tower-line", "The Tower Line", "Homes", "share", rz(G.towers_11_floors_plus) - rz(G.detached_houses), "More homes in 11+ floor blocks", "More detached houses", ["towers_11_floors_plus", "detached_houses"]),
 ("the-grey-line", "The Grey Line", "Homes", "share", rz(G.age_65_plus), "More over-65s", "Fewer over-65s", ["age_65_plus", "age_20_39", "kids_under_15"]),
 ("coffee-vs-alcohol", "Coffee vs Alcohol", "Food", "share", rz(ratio("cafe", "izakaya_bar")), "Cafés outnumber izakaya & bars more than usual", "Izakaya & bars dominate", []),
 ("ramen-vs-soba", "Ramen vs Soba", "Food", "share", rz(ratio("ramen", "soba_udon")), "Ramen outnumbers soba & udon more than usual", "Soba & udon hold their own", []),
 ("the-indie-cafe-line", "The Indie Café Line", "Food", "share", rz(ratio("indie_cafe", "chain_cafe")), "More of the cafés are independent", "More of the cafés are chains", []),
 ("my-basket-vs-the-konbini", "My Basket vs the Konbini", "Chains", "chain", ("My Basket", None), "A My Basket mini-supermarket is closer", "A konbini is closer", []),
 ("konbini-wars", "Konbini Wars: 7-Eleven vs FamilyMart", "Chains", "chain", ("7-Eleven", "FamilyMart"), "A 7-Eleven is closer", "A FamilyMart is closer", []),
 ("gyudon-wars", "Gyudon Wars: Matsuya vs Yoshinoya", "Chains", "chain", ("Matsuya", "Yoshinoya"), "A Matsuya is closer", "A Yoshinoya is closer", []),
 ("starbucks-vs-doutor", "Starbucks vs Doutor", "Chains", "chain", ("Starbucks", "Doutor"), "A Starbucks is closer", "A Doutor is closer", []),
 ("ramen-wars", "Ramen Wars: Iekei vs Hakata", "Chains", "chain", ("Iekei ramen", "Hakata tonkotsu ramen"), "An iekei (Yokohama-style) ramen shop is closer", "A Hakata tonkotsu ramen shop is closer", []),
 ("the-price-line", "The Price Line", "Night", "share", rz(price), "Dinner costs more (HotPepper budget bands)", "Dinner costs less", []),
 ("the-late-night-line", "The Late-Night Line", "Night", "share", rz(ratio("hp_late", "hp_all")), "More places open past midnight", "More places close before midnight", []),
 ("izakaya-vs-bistro", "Izakaya vs Italian & French", "Night", "share", rz(ratio("hp_izakaya", "hp_italian")), "Izakaya outnumber Italian & French more than usual", "Italian & French hold their own", []),
 ("bars-vs-izakaya", "Bars vs Izakaya", "Night", "share", rz(ratio("hp_bar", "hp_izakaya")), "Bars & bals are a bigger share of the night out", "Izakaya are a bigger share", []),
 ("the-yakiniku-line", "The Yakiniku Line", "Night", "share", rz(share("hp_yakiniku", "hp_all")), "Yakiniku is a bigger share of the food", "Yakiniku is a smaller share", []),
 ("shrines-vs-temples", "Shrines vs Temples", "Worship", "chain", ("Shinto shrines", "Buddhist temples"), "A Shinto shrine is closer than a Buddhist temple", "A Buddhist temple is closer than a Shinto shrine", []),
]
P = lambda x, y: f"{(x - minx) * S:.1f},{(maxy - y) * S:.1f}"
def path(geom):
    gt = geom.geom_type
    if gt == "Polygon": return "".join("M" + "L".join(P(x, y) for x, y in r.coords) + "Z" for r in [geom.exterior, *geom.interiors])
    if gt == "MultiPolygon": return "".join(path(g) for g in geom.geoms)
    if gt == "LineString": return "M" + "L".join(P(x, y) for x, y in geom.coords)
    if gt in ("MultiLineString", "GeometryCollection"): return "".join(path(g) for g in geom.geoms if g.geom_type in ("LineString", "MultiLineString", "Polygon", "MultiPolygon"))
    return ""
def cut_path(side):
    seg = G[side].geometry.union_all().boundary.intersection(G[~side].geometry.union_all().boundary); flat = []
    for g in getattr(seg, "geoms", [seg]):
        if g.geom_type in ("LineString", "MultiLineString"): flat += list(getattr(g, "geoms", [g]))
    return path(linemerge(MultiLineString(flat)).simplify(30)) if flat else ""
short = G.short.values
busy = C["food"] >= 15
lines, fam_p, FIELDS = [], {}, {}
for lid, nm, grp, kind, spec, aw, bw, used in L:
    if kind == "share":
        f = np.nan_to_num(np.asarray(spec, float), nan=0.0) + 1e-9 * rng.normal(size=n); null = rot_null(f); na = nb = None; ok = busy if grp in ("Food", "Night") else np.ones(n, bool)
    else:
        A = PTS[spec[0]]; B = np.vstack([PTS[k] for k in ("7-Eleven", "FamilyMart", "Lawson", "Ministop")]) if spec[1] is None else PTS[spec[1]]
        f = field(A, B); null = swap_null(A, B); na, nb = len(A), len(B); ok = np.ones(n, bool)
    c, s = cut(f); p = (1 + (null <= c).sum()) / (NN + 1)
    FIELDS[lid] = (kind, np.asarray(f, float))
    more, less = chips(s, used)
    idx = np.where(ok)[0]
    lines.append(dict(id=lid, name=nm, group=grp, a=aw, b=bw, p=round(float(p), 3), more=more, less=less,
                      ex_a=[short[i] for i in idx[np.argsort(-f[idx])][:4]], ex_b=[short[i] for i in idx[np.argsort(f[idx])][:4]],
                      side=s.astype(int).tolist(), cut=cut_path(s), n_a=int(s.sum()), n_b=int((~s).sum()), stores=[na, nb]))
    print(f"{nm:42s} p={p:.3f} cleanness {c:.3f} (random {np.median(null):.3f})")
np.save(f"{out}/tokyo_price.npy", _pv)
np.savez(f"{out}/tokyo_venues.npz", vxy=V[["x", "y"]].values, hxy=np.column_stack([h.geometry.x, h.geometry.y]), rep=rep, WALK=WALK,
         **{"v_" + k: V[k].values.astype(bool) for k in ["food", "cafe", "fast_food", "izakaya_bar", "ramen", "soba_udon", "indie_cafe", "chain_cafe"]},
         **{"h_" + k: np.asarray(m, bool) for k, m in HP.items()})
np.savez(f"{out}/tokyo_fields.npz", I=I, J=J, W=W, rep=rep, pop=G.population.values, ids=np.array(list(FIELDS)),
         kinds=np.array([v[0] for v in FIELDS.values()]), F=np.column_stack([v[1] for v in FIELDS.values()]), names=np.array([l["name"] for l in lines]))
# correct for trying several match-ups within the chain wars and within the food/night lines
for grp in ["Chains", "Food", "Night", "Worship", "Work", "Homes", "Around"]:
    ids = [k for k, l in enumerate(lines) if l["group"] == grp]; ps = np.array([lines[k]["p"] for k in ids]); o = np.argsort(ps)
    adj = np.maximum.accumulate([min(1, ps[k] * (len(ps) - r)) for r, k in enumerate(o)])
    for r, k in enumerate(o): lines[ids[k]]["p"] = round(float(adj[r]), 3)
ref = np.array(lines[0]["side"], bool)
for l in lines:
    a_ = (np.array(l["side"], bool) == ref).mean(); l["latte_agree"] = round(float(max(a_, 1 - a_)), 2)
# shrines/temples vs age: correlation reported in the app
shr = np.log((C["shrine"] + 0.5) / (C["temple"] + 0.5))
worship_age = round(float(pd.Series(shr).corr(pd.Series(G.age_65_plus.values), method="spearman")), 2)
print("shrine-vs-temple balance vs share 65+ (Spearman):", worship_age, "| shrines", int(C["shrine"].sum()), "temples", int(C["temple"].sum()), "churches", int(C["church"].sum()))

# ------------------------------------------------------------------ map shapes, grey areas, labels
Gs = G.copy(); Gs["geometry"] = Gs.geometry.simplify(25, preserve_topology=True)
areas = [dict(name=G.name[i], short=G.short[i], d=path(Gs.geometry[i]), cx=round((rep[i, 0] - minx) * S, 1), cy=round((maxy - rep[i, 1]) * S, 1),
              pop=int(G.population[i])) for i in range(n)]
allU = gpd.read_file(f"{out}/tokyo_units.gpkg"); allU = allU[~allU.U.isin(st)]
hull = G.geometry.union_all().convex_hull
grey = allU[allU.geometry.representative_point().within(hull)].copy(); grey["geometry"] = grey.geometry.simplify(25, preserve_topology=True)
grey = grey.dissolve().explode(index_parts=False)
empty = [dict(name="Few residents", d=path(g)) for g in grey.geometry]
FAMOUS = {("新宿区", "西新宿"): "Shinjuku", ("渋谷区", "道玄坂"): "Shibuya", ("豊島区", "南池袋"): "Ikebukuro", ("中央区", "銀座"): "Ginza",
          ("台東区", "浅草"): "Asakusa", ("台東区", "上野"): "Ueno", ("世田谷区", "北沢"): "Shimokitazawa", ("杉並区", "高円寺南"): "Koenji",
          ("武蔵野市", "吉祥寺本町"): "Kichijoji", ("立川市", "曙町"): "Tachikawa", ("八王子市", "旭町"): "Hachioji", ("町田市", "原町田"): "Machida",
          ("大田区", "蒲田"): "Kamata", ("足立区", "千住"): "Kita-Senju", ("北区", "赤羽"): "Akabane", ("江東区", "豊洲"): "Toyosu",
          ("港区", "六本木"): "Roppongi", ("目黒区", "自由が丘"): "Jiyugaoka", ("江戸川区", "西葛西"): "Nishi-Kasai", ("墨田区", "錦糸"): "Kinshicho",
          ("練馬区", "練馬"): "Nerima", ("葛飾区", "金町"): "Kanamachi", ("府中市", "宮町"): "Fuchu", ("中野区", "中野"): "Nakano", ("多摩市", "落合"): "Tama Center"}
MORE = {("中央区", "日本橋"): "Nihonbashi", ("中央区", "月島"): "Tsukishima", ("港区", "台場"): "Odaiba", ("港区", "港南"): "Shinagawa",
        ("品川区", "東五反田"): "Gotanda", ("目黒区", "目黒"): "Meguro", ("渋谷区", "恵比寿"): "Ebisu", ("渋谷区", "神宮前"): "Harajuku",
        ("渋谷区", "代々木"): "Yoyogi", ("世田谷区", "三軒茶屋"): "Sangenjaya", ("世田谷区", "玉川"): "Futako-Tamagawa", ("杉並区", "上荻"): "Ogikubo",
        ("杉並区", "阿佐谷南"): "Asagaya", ("新宿区", "神楽坂"): "Kagurazaka", ("新宿区", "高田馬場"): "Takadanobaba", ("豊島区", "巣鴨"): "Sugamo",
        ("北区", "王子"): "Oji", ("荒川区", "西日暮里"): "Nippori", ("台東区", "谷中"): "Yanaka", ("墨田区", "押上"): "Oshiage", ("江東区", "亀戸"): "Kameido",
        ("江東区", "門前仲町"): "Monzen-Nakacho", ("葛飾区", "亀有"): "Kameari", ("足立区", "綾瀬"): "Ayase", ("板橋区", "高島平"): "Takashimadaira",
        ("練馬区", "光が丘"): "Hikarigaoka", ("三鷹市", "下連雀"): "Mitaka", ("調布市", "小島町"): "Chofu", ("国分寺市", "本町"): "Kokubunji",
        ("国立市", "中"): "Kunitachi", ("千代田区", "外神田"): "Akihabara", ("千代田区", "神田神保町"): "Jimbocho", ("文京区", "本郷"): "Hongo",
        ("品川区", "大井"): "Oimachi", ("大田区", "大森北"): "Omori", ("世田谷区", "成城"): "Seijo", ("板橋区", "成増"): "Narimasu",
        ("葛飾区", "柴又"): "Shibamata", ("江戸川区", "小岩"): "Koiwa", ("北区", "十条仲原"): "Jujo", ("中野区", "東中野"): "Higashi-Nakano"}
labels, used = [], set()
for tier, table in [(1, FAMOUS), (2, MORE)]:
    for (ci, na_), en in table.items():
        m = U[(U.CITY_NAME == ci) & (U.NAME == na_)]
        if len(m) and int(m.N.iloc[0]) not in used:
            labels.append(dict(i=int(m.N.iloc[0]), t=en, tier=tier)); used.add(int(m.N.iloc[0]))
for i in range(n):
    if i not in used: labels.append(dict(i=i, t=G.short[i].split(" (")[0], tier=3))
print("labels", len(labels))

# ------------------------------------------------------------------ timeline (2000-2020 on these neighbourhoods)
tc = pd.read_csv(f"{out}/timeline_counts.csv", dtype={"U": str}); tc["N"] = tc.U.map(dict(zip(U.U, U.N)))
YEARS = [2000, 2005, 2010, 2015, 2020]; Dy = {y: tc[tc.year == y].groupby("N").sum(numeric_only=True).reindex(range(n)).fillna(0) for y in YEARS}
def sh(d, a, b): return (d[a] / d[b].replace(0, np.nan)).fillna(0).values
TLD = [("hivis", "The Hi-Vis Line", "More factory, driving, building & cleaning jobs", "More managers & professionals",
        lambda d: rz(sh(d, "hivis", "workers")) - rz(sh(d, "laptop", "workers")), ("managers & professionals among workers", lambda d: d.laptop.sum() / d.workers.sum())),
       ("grey", "The Grey Line", "More over-65s", "Fewer over-65s", lambda d: rz(sh(d, "age65", "age_all")), ("aged 65+", lambda d: d.age65.sum() / d.age_all.sum())),
       ("alone", "The Living Alone Line", "More people living alone", "Fewer people living alone", lambda d: rz(sh(d, "alone", "hh")), ("households of one person", lambda d: d.alone.sum() / d.hh.sum())),
       ("tower", "The Tower Line", "More homes in 11+ floor blocks", "More detached houses", lambda d: rz(sh(d, "towers", "homes")) - rz(sh(d, "houses", "homes")), ("homes in 11+ floor blocks", lambda d: d.towers.sum() / d.homes.sum()))]
tl_lines = []
for lid, nm, aw, bw, fn, (sl, sfn) in TLD:
    F = {y: fn(Dy[y]) for y in YEARS}; sides = {y: F[y] > np.median(F[y]) for y in YEARS}
    dl = F[2020] - F[2000]; thr = np.quantile(np.abs(dl), 0.90)
    toA = [int(i) for i in np.where(~sides[2000] & sides[2020] & (np.abs(dl) > thr))[0]]
    toB = [int(i) for i in np.where(sides[2000] & ~sides[2020] & (np.abs(dl) > thr))[0]]
    f = (F[2020] - F[2020].mean()) / F[2020].std(); c = vecs.T @ f; obs = (sides[2000] == sides[2020]).mean(); null = []
    for _ in range(NN):
        cr = c.copy()
        for x in range(0, n, 12):
            y = min(x + 12, n); q, _ = np.linalg.qr(rng.normal(size=(y - x, y - x))); cr[x:y] = q @ c[x:y]
        r_ = vecs @ cr; r_ = r_ > np.median(r_); a_ = (r_ == sides[2000]).mean(); null.append(max(a_, 1 - a_))
    p = (1 + (np.array(null) >= obs).sum()) / (NN + 1)
    tl_lines.append(dict(id=lid, name=nm, a=aw, b=bw, stat_label=sl, stat=[round(float(sfn(Dy[y])) * 100, 1) for y in YEARS],
                         same_as_2001=[round(float((sides[y] == sides[2000]).mean()) * 100) for y in YEARS], sides=[sides[y].astype(int).tolist() for y in YEARS],
                         cuts=[cut_path(sides[y]) for y in YEARS], toA=toA, toB=toB, persist_p=round(float(p), 3), null_agree=round(float(np.median(null)) * 100)))
    print(f"timeline {nm}: same side 2000->2020 {tl_lines[-1]['same_as_2001'][-1]}% (random ~{tl_lines[-1]['null_agree']}%), p={p:.3f}, moved {len(toA)}+{len(toB)}")
groups = []
for kind, gid, nm, num, den in [("people", "aged-65", "Aged 65+", "age65", "age_all"), ("people", "living-alone", "Living alone (households)", "alone", "hh"),
                                ("homes", "towers", "Homes in 11+ floor blocks", "towers", "homes"), ("homes", "owners", "Home owners (households)", "owners", "hh_tenure"),
                                ("homes", "laptop", "Managers & professionals (workers)", "laptop", "workers"), ("homes", "hivis", "Hi-vis jobs (workers)", "hivis", "workers")]:
    pct, lq, Dv = [], [], []
    for y in YEARS:
        d = Dy[y]; a, b = d[num].values, d[den].values; cityv = a.sum() / b.sum(); s_ = np.where(b > 0, a / np.maximum(b, 1e-9), 0)
        pct.append(round(cityv * 100, 1)); lq.append([round(float(v), 2) for v in s_ / cityv]); rest = b - a
        Dv.append(round(float(0.5 * np.abs(a / a.sum() - rest / rest.sum()).sum()), 3))
    groups.append(dict(id=f"t-{gid}", kind=kind, name=nm, pct=pct, D=Dv, lq=lq))

# ------------------------------------------------------------------ Make your own
sig = {c: G[c].values for c in census}
for k, (a, b) in {"share_cafe": ("cafe", "food"), "share_fast_food": ("fast_food", "food"), "share_izakaya_bar": ("izakaya_bar", "food"),
                  "share_ramen": ("ramen", "food"), "share_soba_udon": ("soba_udon", "food"), "share_sushi": ("sushi", "food"), "share_curry": ("curry", "food"),
                  "share_indian_nepali": ("indian_nepali", "food"), "share_yakiniku": ("yakiniku", "food"), "share_indie_cafe": ("indie_cafe", "cafe"),
                  "hp_late_share": ("hp_late", "hp_all"), "hp_izakaya_share": ("hp_izakaya", "hp_all"), "hp_italian_share": ("hp_italian", "hp_all"),
                  "hp_bar_share": ("hp_bar", "hp_all"), "hp_korean_share": ("hp_korean", "hp_all")}.items():
    sig[k] = np.where(C[b] >= 3, C[a] / np.maximum(C[b], 1), np.nan)
sig["dinner_price"] = price
sig["konbini_per_1k"] = C["konbini"] / (np.pi * WALK ** 2 / 1e6)
sig["stations_per_km2"] = C["station"] / (np.pi * WALK ** 2 / 1e6)
VL = {"share_cafe": ("Cafés", "Food & shops"), "share_fast_food": ("Fast food", "Food & shops"), "share_izakaya_bar": ("Izakaya & bars", "After dark"),
      "share_ramen": ("Ramen shops", "Food & shops"), "share_soba_udon": ("Soba & udon shops", "Food & shops"), "share_sushi": ("Sushi places", "Food & shops"),
      "share_curry": ("Japanese curry places", "Food & shops"), "share_indian_nepali": ("Indian & Nepali restaurants", "Food & shops"), "share_yakiniku": ("Yakiniku places", "Food & shops"),
      "share_indie_cafe": ("Independent cafés", "Food & shops"), "hp_late_share": ("Open past midnight", "After dark"), "hp_izakaya_share": ("Izakaya (HotPepper)", "After dark"),
      "hp_italian_share": ("Italian & French restaurants", "After dark"), "hp_bar_share": ("Bars & bals", "After dark"), "hp_korean_share": ("Korean restaurants", "Food & shops"),
      "dinner_price": ("Dinner price", "After dark"), "konbini_per_1k": ("Konbini per km²", "Food & shops"), "worship_per_1k": ("Shrines, temples & churches per km²", "People"),
      "stations_per_km2": ("Stations per km²", "Getting around")}
CG = {"train_commute": "Getting around", "car_commute": "Getting around", "bike_commute": "Getting around", "walk_commute": "Getting around", "uni_degree": "People", "age_65_plus": "People", "age_20_39": "People", "kids_under_15": "People", "living_alone": "People", "families_with_kids": "People", "density": "People",
      "owners": "Homes", "renters": "Homes", "detached_houses": "Homes", "towers_11_floors_plus": "Homes"}
signals = []
for c, v in sig.items():
    if c in LBL: lab_, mo, le = LBL[c]; grp = CG.get(c, "Work")
    else:
        lab_, grp = VL[c]; mo, le = f"more {lab_.lower()}", f"fewer {lab_.lower()}"
    if c == "share_indie_cafe": mo, le = "more independent cafés", "more chain cafés"
    if c == "hp_late_share": mo, le = "more places open past midnight", "fewer places open past midnight"
    if c == "dinner_price": mo, le = "pricier dinners", "cheaper dinners"
    if c == "konbini_per_1k": mo, le = "more konbini nearby", "fewer konbini nearby"
    if c == "worship_per_1k": mo, le = "more shrines, temples & churches nearby", "fewer shrines, temples & churches nearby"
    if c == "stations_per_km2": mo, le = "more stations", "fewer stations"
    signals.append(dict(id=c, label=lab_, more=mo, less=le, group=grp, v=[None if (x is None or not np.isfinite(x)) else round(float(x), 5) for x in v]))
eig = base64.b64encode(vecs.astype(np.float32).tobytes(order="C")).decode()
def lp(g):
    if g.geom_type == "LineString": return "M" + "L".join(P(x, y) for x, y in g.coords)
    if hasattr(g, "geoms"): return "".join(lp(q) for q in g.geoms)
    return ""
ep = []
for i, j in zip(I, J):
    seg = G.geometry[i].boundary.intersection(G.geometry[j].boundary)
    parts = [q for q in getattr(seg, "geoms", [seg]) if q.geom_type in ("LineString", "MultiLineString")]
    try: seg = linemerge(parts) if parts else seg
    except Exception: pass
    ep.append(lp(seg.simplify(20)))
inmap = G.geometry.union_all().buffer(300)
from shapely import contains_xy
WORSHIP_KEYS = {"Shinto shrines", "Buddhist temples", "Christian churches"}
brands = [dict(name=k, n=int(len(v)), xy=[[round(float(x)), round(float(y))] for x, y in v],
               vb=[[round(float((x - minx) * S), 1), round(float((maxy - y) * S), 1)] for x, y in v]) for k, v in ((k, v[contains_xy(inmap, v[:, 0], v[:, 1])]) for k, v in PTS.items() if k not in WORSHIP_KEYS) if len(v) >= 8]
make = dict(signals=signals, I=I.tolist(), J=J.tolist(), L=[round(float(x) / 1000, 3) for x in W], eig=eig, n=n,
            pop=[int(p) for p in G.population.values], ep=ep, rep=[[round(float(x)), round(float(y))] for x, y in rep], brands=brands)
HIVIS = ('<div class="box"><h3>What does "hi-vis" mean?</h3><p style="margin:0">Hi-vis is Australian slang for the bright, high-visibility vests '
         'worn on building sites, roads, warehouses and delivery routes (作業用の反射ベスト).</p><p class="small">Here it means factory, driving, building, cleaning and '
         'packing jobs, compared with managers and professionals. It describes jobs, not people.</p></div>')
fr = G.foreign_residents.fillna(0).values; cityf = XN.foreign.sum() / XN.pop_all.sum(); lqf = fr / cityf
a_, b_ = XN.foreign.values, (XN.pop_all - XN.foreign).values; Dfor = float(0.5 * np.abs(a_ / a_.sum() - b_ / b_.sum()).sum())
top = np.argsort(-fr)[:6]
HER = [dict(id="foreign", kind="foreign", name="Foreign residents", pct=round(100 * cityf, 1), people=int(XN.foreign.sum()), lq=[round(float(v), 2) for v in lqf],
            peaks=[[G.short[i].split(" (")[0] + ", " + city(G.CITY_NAME[i]), round(100 * float(fr[i]), 1), round(float(lqf[i]), 1)] for i in top],
            D=round(Dfor, 3), recent=None, D_rank=None, D_of=None, shares_with=[])]
print("foreign residents:", HER[0]["pct"], "% ; D", HER[0]["D"], "; peaks", HER[0]["peaks"][:4])
DATA = dict(w=1000, h=round(Hh, 1), areas=areas, empty=empty, lines=lines, labels=labels,
            meta=dict(sources="Japan 2020 Census small-area data (e-Stat) · © OpenStreetMap contributors (venues, Nov 2026) · Restaurant listings Powered by ホットペッパー Webサービス (Nov 2026)",
                      areas=n, worship_age=worship_age, explain={k: HIVIS for k in ("the-hi-vis-line", "the-factory-line", "the-laptop-vs-hard-hat-line")}, hp_credit="Powered by ホットペッパー Webサービス", hp_url="https://webservice.recruit.co.jp/"),
            split={}, heritage=HER, timeline=dict(years=[str(y) for y in YEARS], lines=tl_lines, groups=groups), make=make)
json.dump(DATA, open(outfile, "w"), separators=(",", ":"), ensure_ascii=False)
G[["jp", "short", "name", "population"]].to_csv(f"{out}/neighbourhood_names.csv", index=False)
G[["population", "geometry"]].to_file(f"{out}/tokyo_neigh.gpkg")
print("written", outfile, round(os.path.getsize(outfile) / 1e6, 2), "MB")
