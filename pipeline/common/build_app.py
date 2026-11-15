"""Build one city's app data (same format as Sydney / Tokyo) from what prepare_upload.py produced.

    python pipeline/common/build_app.py melbourne work/melbourne app/data/melbourne.json

The same core lines are built for every city where the data allows (Hi-Vis, Factory, Latte, Drink out vs in,
Train vs Car, ...), plus the city's own chain wars. Each line is tested against random smooth landscapes
(MultiScaleNull, one fit, 199 draws) and corrected (Holm) within its group. Record-based maps also get an
"any geography at all?" check (Moran's I against shuffled areas). Heritage and Timeline are left empty here.
"""
import ast, base64, glob, json, os, re, sys
import numpy as np, pandas as pd, geopandas as gpd
from scipy.spatial import cKDTree
from scipy.stats import norm, rankdata
from shapely.ops import linemerge
from shapely.geometry import MultiLineString
from shapely import contains_xy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, ".."), os.path.join(HERE, "..", ".."), os.path.join(HERE, "..", "tokyo")]
from cities import CITIES, DATA_NOTES
from linetests.landscape import MultiScaleNull

city, W_, OUT = sys.argv[1:4]
C = CITIES[city]; CO = C["country"]; CRS = C["crs"]; rng = np.random.default_rng(7); B = 199


def rz(v):
    v = pd.Series(np.asarray(v, float)); v = v.fillna(v.median()).values
    return norm.ppf((rankdata(v) - 0.5) / len(v))


# ------------------------------------------------------------------ areas
G = gpd.read_file(f"{W_}/areas.gpkg").to_crs(CRS).reset_index(drop=True)
n = len(G)
km2 = G.area / 1e6

# ------------------------------------------------------------------ census indicators, same names in every country
S = pd.DataFrame(index=range(n))
def put(k, num, den):
    S[k] = (np.asarray(num, float) / np.where(np.asarray(den, float) > 0, np.asarray(den, float), np.nan))

if CO == "au":
    key = G.code.astype(str)
    def T(t):
        df = None
        for f in sorted(glob.glob(f"{W_}/census/2021_{t}*.csv")):
            d = pd.read_csv(f, dtype={"SA2_CODE_2021": str}).set_index("SA2_CODE_2021")
            df = d if df is None else df.join(d, rsuffix="_dup")
        return df.reindex(key)
    g01, g34, g35, g36, g37, g49, g54, g60, g62 = (T(t) for t in ["G01", "G34", "G35", "G36", "G37", "G49", "G54", "G60", "G62"])
    pop = g01.Tot_P_P
    put("age_65_plus", g01[["Age_65_74_yr_P", "Age_75_84_yr_P", "Age_85ov_P"]].sum(1), pop)
    put("kids_under_15", g01[["Age_0_4_yr_P", "Age_5_14_yr_P"]].sum(1), pop)
    put("age_20_39", g01[["Age_20_24_yr_P", "Age_25_34_yr_P"]].sum(1), pop)
    put("living_alone", g35.Num_Psns_UR_1_Total, g35.Total_Total)
    put("big_households", g35.Num_Psns_UR_6mo_Total, g35.Total_Total)
    put("no_car", g34.Num_MVs_per_dweling_0_MVs, g34.Total_dwelings)
    put("detached_houses", g36.OPDs_Separate_house_Dwellings, g36.OPDs_Tot_OPDs_Dwellings)
    put("apartments", g36.OPDs_Flt_apart_Tot_Dwgs, g36.OPDs_Tot_OPDs_Dwellings)
    put("renters", g37.R_RE_Agt_Total, g37.Total_Total)
    put("owners", g37[["O_OR_Total", "O_MTG_Total"]].sum(1), g37.Total_Total)
    put("uni_degree", g49[["P_PGrad_Deg_Total", "P_GradDip_and_GradCert_Total", "P_BachDeg_Total"]].sum(1), pop)
    tot = g60.P_Tot_Tot
    put("managers", g60.P_Tot_Managers, tot); put("professionals", g60.P_Tot_Professionals, tot)
    put("laptop_jobs", g60.P_Tot_Managers + g60.P_Tot_Professionals, tot)
    put("hivis_jobs", g60.P_Tot_Mach_oper_drivers + g60.P_Tot_Labourers, tot)
    put("tradies", g60.P_Tot_TechnicTrades_W, tot)
    it = g54.P_Tot_Tot
    put("ind_manufacturing", g54.P_Manufact_Tot, it); put("ind_construction", g54.P_Constru_Tot, it)
    put("ind_it", g54.P_Info_media_teleco_Tot, it); put("ind_finance", g54.P_Fin_Insur_Tot, it)
    put("ind_hospitality", g54.P_Accom_food_Tot, it); put("ind_health", g54.P_HlthCare_SocAs_Tot, it)
    workers = (g62.Tot_P - g62.Did_not_go_to_work_P - g62.Method_travel_to_work_ns_P)
    put("train_commute", g62.One_method_Train_P + g62.Two_methods_Train_Tot_P + g62.Three_meth_Tr_2_oth_meth_P, workers)
    put("car_commute", g62.One_method_Car_as_driver_P, workers)
    put("bike_commute", g62.One_method_Bicycle_P, workers)
    put("walk_commute", g62.One_method_Walked_only_P, workers)
    put("work_from_home", g62.Worked_home_P, workers)
    POP = pop.fillna(0).values

elif CO == "jp":
    ua = pd.read_csv(f"{W_}/unit_area.csv", dtype={"U": str})
    amap = dict(zip(ua.U, ua.area))
    def T(t):
        d = pd.read_csv(f"{W_}/census/{t}.csv", dtype={"KEY_CODE": str}).set_index("KEY_CODE")
        d = d.apply(pd.to_numeric, errors="coerce").fillna(0)
        d["aid"] = d.index.map(amap); return d.dropna(subset=["aid"]).groupby("aid").sum().reindex(G["area"].values).fillna(0)
    pop_, age, hsz, fam, ten, bld, ind, occ = (T(t) for t in ["T001081", "T001082", "T001083", "T001084", "T001085", "T001086", "T001103", "T001104"])
    POP = pop_["人口総数"].values
    at = age["総数、年齢「不詳」含む"]
    put("age_65_plus", age["総数６５歳以上"], at); put("kids_under_15", age["総数１５歳未満"], at)
    put("age_20_39", age[["総数２０～２４歳", "総数２５～２９歳", "総数３０～３４歳", "総数３５～３９歳"]].sum(1), at)
    put("living_alone", hsz["世帯人員１人"], hsz["一般世帯数（世帯人員６人以上含む）"])
    put("families_with_kids", fam["１８歳未満世帯員のいる一般世帯総数"], fam["一般世帯総数"])
    put("owners", ten["持ち家"], ten["住宅に住む一般世帯"]); put("renters", ten["民営借家"], ten["住宅に住む一般世帯"])
    put("detached_houses", bld["一戸建"], bld["主世帯数"]); put("apartments", bld["共同住宅"], bld["主世帯数"])
    put("towers", bld["共同住宅１１階建以上"], bld["主世帯数"])
    o = occ["総数"]; oc = occ.columns
    put("managers", occ[oc[1]], o); put("professionals", occ[oc[2]], o)
    put("laptop_jobs", occ[oc[1]] + occ[oc[2]], o)
    put("hivis_jobs", occ[[oc[8], oc[9], oc[10], oc[11]]].sum(1), o)
    put("tradies", occ[oc[10]], o)
    w = ind["総数"]
    for k, c in [("ind_it", "Ｇ情報通信業"), ("ind_manufacturing", "Ｅ製造業"), ("ind_finance", "Ｊ金融業、保険業"),
                 ("ind_hospitality", "Ｍ宿泊業、飲食サービス業"), ("ind_health", "Ｐ医療、福祉"), ("ind_construction", "Ｄ建設業")]:
        put(k, ind[c], w)

else:   # uk
    key = G.code.astype(str)
    def T(t):
        f = f"{W_}/census/{t}.csv"
        if not os.path.exists(f): return None
        return pd.read_csv(f).set_index("geography code").reindex(key)
    def col(d, *words):
        for c in d.columns:
            if all(w.lower() in c.lower() for w in words): return d[c]
        raise KeyError(words)
    ts001, ts003, ts007, ts044, ts045, ts054 = T("ts001"), T("ts003"), T("ts007a"), T("ts044"), T("ts045"), T("ts054")
    ts060, ts061, ts063, ts067 = T("ts060"), T("ts061"), T("ts063"), T("ts067")
    POP = col(ts001, "Total").fillna(0).values
    at = col(ts007, "Total")
    put("age_65_plus", ts007[[c for c in ts007.columns if re.search(r"Aged (6[5-9]|[7-8]\d)", c)]].sum(1), at)
    put("kids_under_15", ts007[[c for c in ts007.columns if re.search(r"Aged (4 years and under|5 to 9|10 to 14)", c)]].sum(1), at)
    put("age_20_39", ts007[[c for c in ts007.columns if re.search(r"Aged (2\d|3\d) to", c)]].sum(1), at)
    ht = col(ts003, "Total")
    put("living_alone", col(ts003, "One person household;"), ht)
    put("families_with_kids", ts003[[c for c in ts003.columns if "ependent children" in c and "All children non-dependent" not in c and "No children" not in c]].sum(1), ht)
    a = col(ts044, "Total"); put("detached_houses", col(ts044, "Detached") , a)
    put("apartments", col(ts044, "purpose-built block of flats"), a)
    c45 = col(ts045, "Total"); put("no_car", col(ts045, "No cars"), c45)
    t54 = col(ts054, "Total"); put("owners", col(ts054, "Owned;") if any("Owned;" in c for c in ts054.columns) else col(ts054, "Owned"), t54)
    put("renters", col(ts054, "Private rented;") if any("Private rented;" in c for c in ts054.columns) else col(ts054, "Private rented"), t54)
    if ts067 is not None: put("uni_degree", col(ts067, "Level 4"), col(ts067, "Total"))
    if ts063 is not None:
        o = col(ts063, "Total"); c1, c2 = col(ts063, "1. Managers"), col(ts063, "2. Professional")
        put("managers", c1, o); put("professionals", c2, o); put("laptop_jobs", c1 + c2, o)
        put("hivis_jobs", col(ts063, "8. Process") + col(ts063, "9. Elementary"), o); put("tradies", col(ts063, "5. Skilled trades"), o)
    if ts060 is not None:
        it = col(ts060, "Total")
        put("ind_manufacturing", col(ts060, "C: Manufacturing"), it); put("ind_construction", col(ts060, "F: Construction"), it)
        put("ind_it", col(ts060, "J: Information"), it); put("ind_finance", col(ts060, "K: Financial"), it)
        put("ind_hospitality", col(ts060, "I: Accommodation"), it); put("ind_health", col(ts060, "Q: Human health"), it)
    if ts061 is not None:
        wk = col(ts061, "Total") - col(ts061, "Work mainly at or from home")
        put("train_commute", col(ts061, "Underground") + col(ts061, "Train"), wk); put("car_commute", col(ts061, "Driving a car"), wk)
        put("bike_commute", col(ts061, "Bicycle"), wk); put("walk_commute", col(ts061, "On foot"), wk)
        put("work_from_home", col(ts061, "Work mainly at or from home"), col(ts061, "Total"))
S["density"] = POP / km2.values
POP = np.asarray(POP, float)

# ------------------------------------------------------------------ venues (OSM for every city, plus licences / gambling / HotPepper)
P = pd.read_csv(f"{W_}/raw/osm/places.csv"); P["t"] = P.tags.map(ast.literal_eval)
pg = gpd.GeoDataFrame(P, geometry=gpd.points_from_xy(P.lon, P.lat), crs=4326).to_crs(CRS)
am = P.t.map(lambda q: q.get("amenity")); sh = P.t.map(lambda q: q.get("shop"))
txt = P.t.map(lambda q: "|".join(str(q.get(k, "")) for k in ("brand", "name", "brand:en", "name:en", "operator")).lower())
FLAG = {"food": am.isin(["restaurant", "fast_food", "cafe", "food_court"]), "cafe": am.eq("cafe"), "fast_food": am.eq("fast_food"),
        "pub_bar": am.isin(["pub", "bar", "biergarten"]), "bottle_shop": sh.isin(["alcohol", "wine"]), "gym": P.t.map(lambda q: q.get("leisure") == "fitness_centre"),
        "station": P.t.map(lambda q: q.get("railway") == "station" or q.get("public_transport") == "station")}
BRANDS = {
    "au": {"Woolworths": (r"woolworths", ["supermarket"]), "Coles": (r"^coles$|\|coles\||^coles\|", ["supermarket"]), "Aldi": (r"aldi", ["supermarket"]),
           "McDonald's": (r"mcdonald", ["fast_food"]), "KFC": (r"\bkfc\b", ["fast_food"]), "Hungry Jack's": (r"hungry jack", ["fast_food"]),
           "Nando's": (r"nando", ["restaurant", "fast_food"]), "Grill'd": (r"grill'd", ["restaurant", "fast_food"])},
    "jp": {"7-Eleven": (r"7-eleven|セブン-イレブン|セブンイレブン|seven-eleven", ["convenience"]), "FamilyMart": (r"familymart|ファミリーマート", ["convenience"]),
           "Lawson": (r"lawson|ローソン", ["convenience"]), "Matsuya": (r"^松屋|\|松屋|matsuya", ["fast_food", "restaurant"]),
           "Yoshinoya": (r"吉野家|yoshinoya", ["fast_food", "restaurant"]), "Sukiya": (r"すき家|sukiya", ["fast_food", "restaurant"]),
           "Starbucks": (r"starbucks|スターバックス", ["cafe"]), "Doutor": (r"doutor|ドトール", ["cafe"]),
           "Saizeriya": (r"サイゼリヤ|saizeriya", ["restaurant", "fast_food"]), "Gusto": (r"ガスト|\bgusto\b", ["restaurant", "fast_food"]),
           "McDonald's": (r"mcdonald|マクドナルド", ["fast_food"]), "Gyoza no Ohsho": (r"餃子の王将|ohsho", ["restaurant", "fast_food"])},
    "uk": {"Greggs": (r"greggs", ["fast_food", "cafe", "bakery"]), "Pret": (r"pret a manger|\bpret\b", ["cafe", "fast_food"]),
           "Costa": (r"\bcosta\b", ["cafe"]), "Starbucks": (r"starbucks", ["cafe"]), "Tesco": (r"tesco", ["supermarket", "convenience"]),
           "Sainsbury's": (r"sainsbury", ["supermarket", "convenience"]), "Waitrose": (r"waitrose", ["supermarket", "convenience"]),
           "Lidl & Aldi": (r"\blidl\b|\baldi\b", ["supermarket"]), "Wetherspoon": (r"wetherspoon|\bjd wetherspoon", ["pub", "bar"]),
           "McDonald's": (r"mcdonald", ["fast_food"]), "KFC": (r"\bkfc\b", ["fast_food"])},
}[CO]
kind = am.where(am.notna(), sh)
for b, (pat, kinds) in BRANDS.items():
    FLAG["brand:" + b] = txt.str.contains(pat, regex=True) & kind.isin(kinds)

V = pd.read_csv(f"{W_}/venues.csv")
V = V[V.lat.notna()].reset_index(drop=True)
vg = gpd.GeoDataFrame(V, geometry=gpd.points_from_xy(V.lon, V.lat), crs=4326).to_crs(CRS)
if CO == "uk":
    FLAG_V = {"fsa_pub": vg.kind.eq("food:Pub/bar/nightclub"), "fsa_takeaway": vg.kind.eq("food:Takeaway/sandwich shop"),
              "fsa_restaurant": vg.kind.eq("food:Restaurant/Cafe/Canteen"), "betting": vg.kind.eq("gaming:betting shop"),
              "arcade": vg.kind.isin(["gaming:adult gaming centre"])}
elif C.get("licences") == "vic":
    FLAG_V = {"lic_on": vg.kind.eq("on") & vg.source.eq("vic_licence"), "lic_off": vg.kind.eq("off") & vg.source.eq("vic_licence")}
else:
    FLAG_V = {}
GB = G[["geometry"]].copy(); GB["geometry"] = G.buffer(150)
def counts(gdf, flags):
    j = gpd.sjoin(gdf[["geometry"]], GB, predicate="within")
    out = {}
    for k, m in flags.items():
        m = np.asarray(m, bool); jj = j[m[j.index.values]] if len(j) else j
        out[k] = np.bincount(jj.index_right.values, minlength=n).astype(float) if len(jj) else np.zeros(n)
    return out
CNT = counts(pg, FLAG); CNT.update(counts(vg, FLAG_V))

HPd = None
if CO == "jp" and glob.glob(f"{W_}/raw/venues/hotpepper.csv"):
    h = pd.read_csv(f"{W_}/raw/venues/hotpepper.csv", low_memory=False, dtype={"sub_genre": str})
    h = gpd.GeoDataFrame(h, geometry=gpd.points_from_xy(h.lng, h.lat), crs=4326).to_crs(CRS)
    dr = pd.read_csv(f"{W_}/raw/venues/hotpepper_drinks.csv") if os.path.exists(f"{W_}/raw/venues/hotpepper_drinks.csv") else pd.DataFrame(columns=["filter", "id"])
    gc = h.genre_code
    HF = {"hp_all": np.ones(len(h), bool), "hp_late": h.midnight.eq("営業している").values, "hp_izakaya": gc.eq("G001").values,
          "hp_italian": gc.eq("G006").values, "hp_bar": gc.isin(["G012", "G002"]).values, "hp_yakiniku": gc.eq("G008").values,
          "hp_ramen": gc.eq("G013").values}
    for f_ in ["sake", "wine", "shochu", "cocktail", "free_drink"]:
        HF["hp_" + f_] = h.id.isin(set(dr[dr["filter"] == f_].id)).values
    CNT.update(counts(h, HF)); HPd = h


def logit_ratio(a, b): return np.log((CNT[a] + 0.5) / (CNT[b] + 0.5))
def logit_share(a, tot): return np.log((CNT[a] + 0.5) / (np.maximum(CNT[tot] - CNT[a], 0) + 0.5))
def lograte(a): return np.log((CNT[a] + 0.5) / np.maximum(POP, 1))

# ------------------------------------------------------------------ border graph
buf = gpd.GeoDataFrame(geometry=G.buffer(5), crs=CRS)
pr = gpd.sjoin(buf, buf, predicate="intersects"); pr = pr[pr.index < pr.index_right]
I, J = pr.index.values, pr.index_right.values
W = np.array([G.geometry[i].boundary.intersection(G.geometry[j].boundary).length for i, j in zip(I, J)])
k = W >= 50; I, J, W = I[k], J[k], W[k]
print(f"{C['name']}: {n} areas, {len(I)} borders", flush=True)
GN = MultiScaleNull(G.geometry, I, J, W, m=25 if n < 600 else 9)
rep = np.column_stack([G.representative_point().x, G.representative_point().y])


def cut(f):
    s = f > np.median(f); return ((s[I] != s[J]) * W).sum() / (0.5 * W.sum()), s


def moran_p(f, R=199):
    f = (f - f.mean()) / (f.std() + 1e-12)
    def mi(x): return (W * x[I] * x[J]).sum()
    obs = mi(f); null = np.array([mi(rng.permutation(f)) for _ in range(R)])
    return (1 + (null >= obs).sum()) / (R + 1)


def field(A, Bp, off):
    return np.log(cKDTree(Bp).query(rep)[0] + off) - np.log(cKDTree(A).query(rep)[0] + off)


def swap_p(A, Bp, off, R=199):
    obs = cut(field(A, Bp, off))[0]; Pp = np.vstack([A, Bp]); na = len(A); res = []
    for _ in range(R):
        p = rng.permutation(len(Pp)); res.append(cut(field(Pp[p[:na]], Pp[p[na:]], off))[0])
    return (1 + (np.array(res) <= obs).sum()) / (R + 1)


# ------------------------------------------------------------------ plain words for the census indicators
LBL = {"age_65_plus": ("Aged 65+", "more over-65s", "fewer over-65s"), "kids_under_15": ("Kids", "more kids", "fewer kids"),
       "age_20_39": ("Aged 20-39", "more people in their 20s and 30s", "fewer people in their 20s and 30s"),
       "living_alone": ("Living alone", "more people living alone", "fewer people living alone"),
       "families_with_kids": ("Families with kids", "more families with kids", "fewer families with kids"),
       "big_households": ("Households of 6+", "more households of 6+", "fewer households of 6+"),
       "no_car": ("No car", "more households without a car", "fewer households without a car"),
       "detached_houses": ("Detached houses", "more detached houses", "fewer detached houses"),
       "apartments": ("Flats & apartments", "more flats & apartments", "fewer flats & apartments"),
       "towers": ("Homes in 11+ floor blocks", "more homes in tall blocks", "fewer homes in tall blocks"),
       "renters": ("Private renters", "more private renters", "fewer private renters"), "owners": ("Home owners", "more home owners", "fewer home owners"),
       "uni_degree": ("University graduates", "more university graduates", "fewer university graduates"),
       "managers": ("Managers", "more managers", "fewer managers"), "professionals": ("Professionals", "more professionals", "fewer professionals"),
       "laptop_jobs": ("Managers & professionals", "more managers & professionals", "fewer managers & professionals"),
       "hivis_jobs": ("Hi-vis jobs", "more hi-vis jobs", "fewer hi-vis jobs"), "tradies": ("Trades", "more tradies", "fewer tradies"),
       "ind_manufacturing": ("Manufacturing", "more factory workers", "fewer factory workers"),
       "ind_construction": ("Construction", "more construction workers", "fewer construction workers"),
       "ind_it": ("IT & media", "more IT & media workers", "fewer IT & media workers"), "ind_finance": ("Finance", "more finance workers", "fewer finance workers"),
       "ind_hospitality": ("Hospitality", "more hospitality workers", "fewer hospitality workers"),
       "ind_health": ("Health & care", "more health & care workers", "fewer health & care workers"),
       "train_commute": ("Train commuters", "more people commuting by train", "fewer people commuting by train"),
       "car_commute": ("Car commuters", "more people driving to work", "fewer people driving to work"),
       "bike_commute": ("Bike commuters", "more people cycling to work", "fewer people cycling to work"),
       "walk_commute": ("Walk to work", "more people walking to work", "fewer people walking to work"),
       "work_from_home": ("Work from home", "more people working from home", "fewer people working from home"),
       "density": ("Density", "more people per km²", "fewer people per km²")}
census = [c for c in LBL if c in S and S[c].notna().sum() > n * 0.8]
Z = np.column_stack([rz(S[c]) for c in census])
def has(*cs): return all(c in census for c in cs)
def chips(s, used):
    eff = Z[s].mean(0) - Z[~s].mean(0); keep = [k for k in range(len(census)) if census[k] not in used]
    hi = sorted(keep, key=lambda k: -eff[k])[:5]; lo = sorted(keep, key=lambda k: eff[k])[:5]
    return [LBL[census[k]][1] for k in hi if eff[k] > 0.15], [LBL[census[k]][1] for k in lo if eff[k] < -0.15]

# ------------------------------------------------------------------ the lines
L = []   # id, name, group, kind, spec, orange, blue, used-census
if has("hivis_jobs", "laptop_jobs"):
    L.append(("the-hi-vis-line", "The Hi-Vis Line", "Work", "census", rz(S.hivis_jobs) - rz(S.laptop_jobs), "More driving, machine & labouring jobs", "More managers & professionals",
              ["hivis_jobs", "laptop_jobs", "managers", "professionals", "tradies"]))
if has("ind_manufacturing"):
    L.append(("the-factory-line", "The Factory Line", "Work", "census", rz(S.ind_manufacturing), "More factory workers", "Fewer factory workers", ["ind_manufacturing", "hivis_jobs"]))
if has("ind_it", "ind_construction"):
    L.append(("the-laptop-vs-hard-hat-line", "The Laptop vs Hard Hat Line", "Work", "census", rz(S.ind_it) - rz(S.ind_construction), "More IT & media workers, fewer builders", "More builders, fewer IT & media workers", ["ind_it", "ind_construction", "tradies"]))
if has("uni_degree"):
    L.append(("the-degree-line", "The Degree Line", "Work", "census", rz(S.uni_degree), "More university graduates", "Fewer university graduates", ["uni_degree", "laptop_jobs", "professionals", "managers"]))
if has("age_65_plus"):
    L.append(("the-grey-line", "The Grey Line", "Homes", "census", rz(S.age_65_plus), "More over-65s", "Fewer over-65s", ["age_65_plus", "age_20_39", "kids_under_15"]))
if has("living_alone"):
    fam = "families_with_kids" if has("families_with_kids") else "kids_under_15"
    L.append(("the-living-alone-line", "The Living Alone Line", "Homes", "census", rz(S.living_alone) - rz(S[fam]), "More people living alone", "More families with kids", ["living_alone", fam, "kids_under_15"]))
if has("apartments", "detached_houses"):
    L.append(("flats-vs-houses", "Flats vs Houses", "Homes", "census", rz(S.apartments) - rz(S.detached_houses), "More flats & apartments", "More detached houses", ["apartments", "detached_houses", "towers"]))
if has("renters", "owners"):
    L.append(("the-renters-line", "The Renters Line", "Homes", "census", rz(S.renters) - rz(S.owners), "More private renters", "More home owners", ["renters", "owners"]))
if has("train_commute", "car_commute"):
    L.append(("train-vs-car", "Train vs Car", "Around", "census", rz(S.train_commute) - rz(S.car_commute), "More people commute by train", "More people drive to work", ["train_commute", "car_commute"]))
if has("no_car"):
    L.append(("the-no-car-line", "The No-Car Line", "Around", "census", rz(S.no_car), "More households without a car", "Fewer households without a car", ["no_car", "car_commute"]))
if has("bike_commute"):
    L.append(("the-bicycle-line", "The Bicycle Line", "Around", "census", rz(S.bike_commute), "More people cycle to work", "Fewer people cycle to work", ["bike_commute"]))
# venue lines
L.append(("the-latte-line", "The Latte Line", "Food", "records", logit_ratio("cafe", "fast_food"), "More cafés, less fast food", "More fast food, fewer cafés", []))
L.append(("coffee-vs-alcohol", "Coffee vs Alcohol", "Food", "records", logit_ratio("cafe", "pub_bar"), "Cafés outnumber pubs & bars more than usual", "Pubs & bars outnumber cafés", []))
if "lic_on" in CNT:
    L.append(("drink-out-vs-drink-in", "Drink Out vs Drink In", "Night", "records", logit_ratio("lic_on", "lic_off"), "More pubs, bars & restaurants with a licence", "More bottle shops for the licences there are", []))
else:
    L.append(("drink-out-vs-drink-in", "Drink Out vs Drink In", "Night", "records", logit_ratio("pub_bar", "bottle_shop"), "More pubs & bars than bottle shops", "More bottle shops than pubs & bars", []))
if CO == "uk":
    L.append(("the-chicken-shop-line", "The Takeaway Line", "Food", "records", logit_ratio("fsa_takeaway", "fsa_restaurant"), "More takeaways than sit-down places", "More restaurants & cafés than takeaways", []))
    L.append(("the-betting-shop-line", "The Betting Shop Line", "Night", "records", lograte("betting"), "More betting shops per person", "Fewer betting shops per person", []))
    L.append(("the-pub-line", "The Pub Line", "Night", "records", lograte("fsa_pub"), "More pubs & bars per person", "Fewer pubs & bars per person", []))
if HPd is not None:
    L.append(("the-late-night-line", "The Late-Night Line", "Night", "records", logit_share("hp_late", "hp_all"), "More places open past midnight", "More places close before midnight", []))
    if CNT["hp_sake"].sum() > 100 and CNT["hp_wine"].sum() > 100:
        L.append(("wine-vs-sake", "Wine vs Sake", "Night", "records", logit_ratio("hp_wine", "hp_sake"), "More places known for their wine list", "More places known for their sake list", []))
    L.append(("izakaya-vs-bistro", "Izakaya vs Italian & French", "Night", "records", logit_ratio("hp_izakaya", "hp_italian"), "Izakaya outnumber Italian & French more than usual", "Italian & French hold their own", []))
    L.append(("bars-vs-izakaya", "Bars vs Izakaya", "Night", "records", logit_ratio("hp_bar", "hp_izakaya"), "Bars & bals are a bigger share of the night out", "Izakaya are a bigger share", []))
CHAINS = {"au": [("woolies-vs-coles", "Woolies vs Coles", "Woolworths", "Coles"), ("maccas-vs-kfc", "Maccas vs KFC", "McDonald's", "KFC"),
                 ("maccas-vs-hungry-jacks", "Maccas vs Hungry Jack's", "McDonald's", "Hungry Jack's"), ("nandos-vs-grilld", "Nando's vs Grill'd", "Nando's", "Grill'd")],
          "jp": [("konbini-wars", "Konbini Wars: 7-Eleven vs FamilyMart", "7-Eleven", "FamilyMart"), ("lawson-vs-familymart", "Lawson vs FamilyMart", "Lawson", "FamilyMart"),
                 ("gyudon-wars", "Gyudon Wars: Matsuya vs Yoshinoya", "Matsuya", "Yoshinoya"), ("sukiya-vs-yoshinoya", "Sukiya vs Yoshinoya", "Sukiya", "Yoshinoya"),
                 ("starbucks-vs-doutor", "Starbucks vs Doutor", "Starbucks", "Doutor"), ("saizeriya-vs-gusto", "Saizeriya vs Gusto", "Saizeriya", "Gusto")],
          "uk": [("greggs-vs-pret", "Greggs vs Pret", "Greggs", "Pret"), ("costa-vs-starbucks", "Costa vs Starbucks", "Costa", "Starbucks"),
                 ("waitrose-vs-lidl-aldi", "Waitrose vs Lidl & Aldi", "Waitrose", "Lidl & Aldi"), ("tesco-vs-sainsburys", "Tesco vs Sainsbury's", "Tesco", "Sainsbury's"),
                 ("maccas-vs-kfc", "McDonald's vs KFC", "McDonald's", "KFC")]}[CO]
inmap = G.geometry.union_all().buffer(300)
PTS = {}
for b in BRANDS:
    xy = np.column_stack([pg.geometry.x, pg.geometry.y])[np.asarray(FLAG["brand:" + b], bool)]
    PTS[b] = xy[contains_xy(inmap, xy[:, 0], xy[:, 1])] if len(xy) else xy
OFF = 50.0 if CO == "jp" else 200.0
for lid, nm, a_, b_ in CHAINS:
    if len(PTS[a_]) >= 15 and len(PTS[b_]) >= 15:
        L.append((lid, nm, "Chains", "chain", (a_, b_), f"A {a_} is closer", f"A {b_} is closer", []))

# ------------------------------------------------------------------ run the tests
names_short = None
lines, FIELDS = [], {}
for lid, nm, grp, kind_, spec, aw, bw, used in L:
    if kind_ == "chain":
        A, Bp = PTS[spec[0]], PTS[spec[1]]; f = field(A, Bp, OFF); p = swap_p(A, Bp, OFF); pgeo = None; stores = [len(A), len(Bp)]
    else:
        f = np.nan_to_num(np.asarray(spec, float)); f = f + 1e-9 * rng.normal(size=n)
        p = GN.test(rz(f), B, seed=11)[0]; pgeo = None if kind_ == "census" else moran_p(f); stores = [None, None]
    c, s = cut(f)
    more, less = chips(s, used)
    lines.append(dict(id=lid, name=nm, group=grp, a=aw, b=bw, p_line=float(p), p_geo=None if pgeo is None else round(float(pgeo), 3), kind=kind_,
                      more=more, less=less, side=s.astype(int).tolist(), n_a=int(s.sum()), n_b=int((~s).sum()), stores=stores, f=f))
    print(f"  {nm:40s} p={p:.3f}" + ("" if pgeo is None else f"  geography p={pgeo:.3f}"), flush=True)


def holm(p):
    p = np.asarray(p, float); o = np.argsort(p); m = len(p); out = np.empty(m); run = 0
    for r, i in enumerate(o): run = max(run, (m - r) * p[i]); out[i] = min(1, run)
    return out


for grp in {l["group"] for l in lines}:
    ids = [k for k, l in enumerate(lines) if l["group"] == grp]
    for k, q in zip(ids, holm([lines[k]["p_line"] for k in ids])): lines[k]["p"] = round(float(q), 3)
for l in lines:
    geo = l["kind"] == "census" or (l["kind"] == "chain") or (l["p_geo"] is not None and l["p_geo"] <= 0.05)
    l["tier"] = "line" if l["p"] <= 0.05 else ("gentle" if geo and l["kind"] != "chain" else "chance")
    l["p_edge"] = None; l["p_old"] = None

# ------------------------------------------------------------------ names and labels
def short_au(nm): return re.split(r" - | \(", nm)[0]
if CO == "au":
    G["short"] = G.name.map(short_au)
    d0 = G.short.duplicated(keep=False); G.loc[d0, "short"] = G.name[d0]       # "South Yarra - North" rather than "South Yarra 2"
elif CO == "jp":
    from romaji import place
    U = gpd.read_file(f"{W_}/units.gpkg")
    ua2 = pd.read_csv(f"{W_}/unit_area.csv", dtype={"U": str})
    top = ua2.loc[ua2.groupby("area").population.idxmax()].set_index("area")
    def ward(cn):
        m = re.match(r".*?市(.+区)$", cn); w = m.group(1) if m else cn
        return place(re.sub(r"[区市]$", "", w))
    G["short"] = [place(top.NAME.get(a, "")) for a in G["area"]]
    if city == "kyoto":   # Kyoto's small areas are old school districts with very long names: use a station inside instead
        import unicodedata
        rail = P.t.map(lambda q: q.get("railway") == "station").values
        st = pg[rail].copy()
        st["nm"] = st.t.map(lambda q: q.get("name:en") or (place(q.get("name", "")) if q.get("name") else ""))
        st["nm"] = st.nm.map(lambda x: unicodedata.normalize("NFKD", re.split(r"[・(（]", x)[0]).encode("ascii", "ignore").decode().strip())
        st = st[st.nm.str.len() > 0]; jst = gpd.sjoin(st[["nm", "geometry"]], G[["geometry"]], predicate="within").groupby("index_right").nm.first()
        G["short"] = [re.sub(r" Station$", "", jst[i]) if i in jst.index else place(str(top.NAME.get(a, ""))[:2]) for i, a in enumerate(G["area"])]
    G["ward"] = [ward(top.CITY_NAME.get(a, "")) for a in G["area"]]
    G["jp"] = [str(top.CITY_NAME.get(a, "")) + str(top.NAME.get(a, "")) for a in G["area"]]
else:
    st = pg[P.t.map(lambda q: q.get("railway") in ("station", "halt") or q.get("station") == "subway").values].copy(); st["nm"] = st.t.map(lambda q: q.get("name", ""))
    st = st[st.nm.str.len() > 0]
    j = gpd.sjoin(st[["nm", "geometry"]], G[["geometry"]], predicate="within")
    first = j.groupby("index_right").nm.first()
    d_, ix = cKDTree(np.column_stack([st.geometry.x, st.geometry.y])).query(rep)
    near = st.nm.values[ix]
    def clean(x): return re.sub(r" (Underground|Rail|Railway|Overground|DLR|Tram|Tramstop|Metrolink|Bus)? ?([Ss]tation|[Ss]top)$", "", x)
    G["short"] = [clean(first[i]) if i in first.index else ("Near " + clean(near[i]) if d_[i] < 3000 else G.name[i]) for i in range(n)]
dup = G.short.duplicated(keep=False)
if CO == "jp": G.loc[dup, "short"] = G.short[dup] + " (" + G.ward[dup] + ")"
elif CO == "uk": G.loc[dup, "short"] = G.short[dup] + " (" + G.borough[dup] + ")"
dup = G.short.duplicated(keep=False)
G.loc[dup, "short"] = G.short[dup] + " " + G[dup].groupby("short").cumcount().add(1).astype(str)
if CO == "au": G["label_name"] = G.name
elif CO == "jp": G["label_name"] = G.short + ", " + G.ward + " · " + G.jp + " area"
else: G["label_name"] = G.short + ", " + G.borough + " · " + G.name

busy = CNT["food"] + CNT["pub_bar"]
order = np.argsort(-busy)
span = max(np.ptp(rep[:, 0]), np.ptp(rep[:, 1]))
tier = np.full(n, 3); placed = []
for want, gap, t_ in [(10, 0.09, 1), (35, 0.045, 2)]:      # busiest places first, spread out so names don't pile up in the centre
    k_ = 0
    for i in order:
        if tier[i] < 3: continue
        if all(np.hypot(*(rep[i] - rep[j])) > gap * span for j in placed): tier[i] = t_; placed.append(i); k_ += 1
        if k_ >= want: break
labels = [dict(i=int(i), t=re.split(r" - | \(", G.short[i])[0] if CO != "au" else G.short[i].replace(" - ", " "), tier=int(tier[i])) for i in order]
for l in lines:
    f = l.pop("f"); idx = np.where(busy >= (5 if l["kind"] == "records" else 0))[0]
    if len(idx) < 8: idx = np.arange(n)
    l["ex_a"] = [G.short[i] for i in idx[np.argsort(-f[idx])][:4]]; l["ex_b"] = [G.short[i] for i in idx[np.argsort(f[idx])][:4]]
    FIELDS[l["id"]] = f
    l.pop("kind"); l.pop("p_line")

# ------------------------------------------------------------------ geometry to the 1000-wide map
minx, miny, maxx, maxy = G.total_bounds; SC = 1000 / (maxx - minx); Hh = (maxy - miny) * SC
Pf = lambda x, y: f"{(x - minx) * SC:.1f},{(maxy - y) * SC:.1f}"
def path(geom):
    gt = geom.geom_type
    if gt == "Polygon": return "".join("M" + "L".join(Pf(x, y) for x, y in r.coords) + "Z" for r in [geom.exterior, *geom.interiors])
    if gt == "MultiPolygon": return "".join(path(g) for g in geom.geoms)
    if gt == "LineString": return "M" + "L".join(Pf(x, y) for x, y in geom.coords)
    if gt in ("MultiLineString", "GeometryCollection"): return "".join(path(g) for g in geom.geoms if g.geom_type in ("LineString", "MultiLineString", "Polygon", "MultiPolygon"))
    return ""
TOL = 0.6 / SC
def cut_path(side):
    seg = G[side].geometry.union_all().boundary.intersection(G[~side].geometry.union_all().boundary); flat = []
    for g in getattr(seg, "geoms", [seg]):
        if g.geom_type in ("LineString", "MultiLineString"): flat += list(getattr(g, "geoms", [g]))
    return path(linemerge(MultiLineString(flat)).simplify(TOL)) if flat else ""
for l in lines: l["cut"] = cut_path(np.array(l["side"], bool))
ref = np.array(next((l["side"] for l in lines if l["id"] == "the-latte-line"), lines[0]["side"]), bool)
for l in lines:
    a_ = (np.array(l["side"], bool) == ref).mean(); l["latte_agree"] = round(float(max(a_, 1 - a_)), 2)
Gs = G.geometry.simplify(TOL, preserve_topology=True)
areas = [dict(name=G.label_name[i], short=G.short[i], d=path(Gs[i]), cx=round((rep[i, 0] - minx) * SC, 1), cy=round((maxy - rep[i, 1]) * SC, 1),
              pop=int(POP[i])) for i in range(n)]
empty = []
hull = G.geometry.union_all().convex_hull.buffer(500)
gp_ = f"{W_}/dropped.gpkg" if CO == "au" else f"{W_}/units.gpkg" if CO == "jp" else None
if gp_ and os.path.exists(gp_):
    E = gpd.read_file(gp_).to_crs(CRS)
    if CO == "jp": E = E[~E.study.astype(bool)]
    E = E[E.representative_point().within(hull)]
    if len(E):
        E = E.dissolve().explode(index_parts=False); E["geometry"] = E.geometry.intersection(hull).simplify(TOL)
        empty = [dict(name="Few residents", d=path(g)) for g in E.geometry if not g.is_empty]

# ------------------------------------------------------------------ Make your own
sig = {c: S[c].values for c in census}
for k_, (a, b) in {"share_cafe": ("cafe", "food"), "share_fast_food": ("fast_food", "food")}.items():
    sig[k_] = np.where(CNT[b] >= 3, CNT[a] / np.maximum(CNT[b], 1), np.nan)
sig["pubs_per_10k"] = CNT["pub_bar"] / np.maximum(POP, 1) * 1e4
sig["bottle_per_10k"] = CNT["bottle_shop"] / np.maximum(POP, 1) * 1e4
sig["gyms_per_10k"] = CNT["gym"] / np.maximum(POP, 1) * 1e4
if CO == "uk":
    sig["betting_per_10k"] = CNT["betting"] / np.maximum(POP, 1) * 1e4; sig["takeaways_per_10k"] = CNT["fsa_takeaway"] / np.maximum(POP, 1) * 1e4
if HPd is not None:
    for k_ in ["hp_late", "hp_izakaya", "hp_italian", "hp_bar", "hp_sake", "hp_wine", "hp_free_drink"]:
        sig[k_ + "_share"] = np.where(CNT["hp_all"] >= 5, CNT[k_] / np.maximum(CNT["hp_all"], 1), np.nan)
VL = {"share_cafe": ("Cafés", "Food & shops", "more cafés", "fewer cafés"), "share_fast_food": ("Fast food", "Food & shops", "more fast food", "less fast food"),
      "pubs_per_10k": ("Pubs & bars per person", "After dark", "more pubs & bars", "fewer pubs & bars"),
      "bottle_per_10k": ("Bottle shops per person", "After dark", "more bottle shops", "fewer bottle shops"),
      "gyms_per_10k": ("Gyms per person", "Food & shops", "more gyms", "fewer gyms"),
      "betting_per_10k": ("Betting shops per person", "After dark", "more betting shops", "fewer betting shops"),
      "takeaways_per_10k": ("Takeaways per person", "Food & shops", "more takeaways", "fewer takeaways"),
      "hp_late_share": ("Open past midnight", "After dark", "more places open past midnight", "fewer places open past midnight"),
      "hp_izakaya_share": ("Izakaya", "After dark", "more izakaya", "fewer izakaya"), "hp_italian_share": ("Italian & French", "After dark", "more Italian & French", "less Italian & French"),
      "hp_bar_share": ("Bars & bals", "After dark", "more bars", "fewer bars"), "hp_sake_share": ("Good sake list", "After dark", "more places with a good sake list", "fewer places with a good sake list"),
      "hp_wine_share": ("Good wine list", "After dark", "more places with a good wine list", "fewer places with a good wine list"),
      "hp_free_drink_share": ("All-you-can-drink", "After dark", "more all-you-can-drink deals", "fewer all-you-can-drink deals")}
CG = {"train_commute": "Getting around", "car_commute": "Getting around", "bike_commute": "Getting around", "walk_commute": "Getting around", "work_from_home": "Getting around",
      "no_car": "Getting around", "uni_degree": "People", "age_65_plus": "People", "age_20_39": "People", "kids_under_15": "People", "living_alone": "People",
      "families_with_kids": "People", "big_households": "People", "density": "People", "owners": "Homes", "renters": "Homes", "detached_houses": "Homes",
      "apartments": "Homes", "towers": "Homes"}
signals = []
for c_, v in sig.items():
    if c_ in LBL: lab_, mo, le = LBL[c_]; grp = CG.get(c_, "Work")
    else: lab_, grp, mo, le = VL[c_]
    signals.append(dict(id=c_, label=lab_, more=mo, less=le, group=grp, v=[None if not np.isfinite(x) else round(float(x), 5) for x in np.asarray(v, float)]))
Ad = np.zeros((n, n)); Ad[I, J] = 1; Ad[J, I] = 1; Mc = np.eye(n) - 1 / n
vals, vecs = np.linalg.eigh(Mc @ Ad @ Mc); vecs = vecs[:, np.argsort(vals)[::-1]]
eig = base64.b64encode(vecs.astype(np.float32).tobytes(order="C")).decode()
def lp(g):
    if g.geom_type == "LineString": return "M" + "L".join(Pf(x, y) for x, y in g.coords)
    if hasattr(g, "geoms"): return "".join(lp(q) for q in g.geoms)
    return ""
ep = []
for i, j in zip(I, J):
    seg = G.geometry[i].boundary.intersection(G.geometry[j].boundary)
    parts = [q for q in getattr(seg, "geoms", [seg]) if q.geom_type in ("LineString", "MultiLineString")]
    try: seg = linemerge(parts) if parts else seg
    except Exception: pass
    ep.append(lp(seg.simplify(TOL)))
brands = [dict(name=k_, n=int(len(v)), xy=[[round(float(x)), round(float(y))] for x, y in v],
               vb=[[round(float((x - minx) * SC), 1), round(float((maxy - y) * SC), 1)] for x, y in v]) for k_, v in PTS.items() if len(v) >= 8]
make = dict(signals=signals, I=I.tolist(), J=J.tolist(), L=[round(float(x) / 1000, 3) for x in W], eig=eig, n=n,
            pop=[int(p) for p in POP], ep=ep, rep=[[round(float(x)), round(float(y))] for x, y in rep], brands=brands)

SRC = {"au": "ABS 2021 Census (GCP DataPack, SA2) · ABS ASGS 2021 boundaries · © OpenStreetMap contributors (Nov 2026)",
       "jp": "Japan 2020 Census small-area data (e-Stat) · © OpenStreetMap contributors (Nov 2026) · Restaurant listings Powered by ホットペッパー Webサービス (Nov 2026)",
       "uk": "ONS Census 2021 (Nomis bulk tables) · ONS 2021 boundaries · Food Standards Agency ratings · Gambling Commission register · © OpenStreetMap contributors (Nov 2026)"}[CO]
if C.get("licences") == "vic": SRC += " · Victorian liquor licences (data.vic.gov.au)"
HIVIS = ('<div class="box"><h3>What does "hi-vis" mean?</h3><p style="margin:0">Hi-vis is Australian slang for the bright, high-visibility vests '
         'worn on building sites, roads, warehouses and delivery routes.</p><p class="small">Here it means driving, machine and labouring jobs, compared with '
         'managers and professionals. It describes jobs, not people.</p></div>')
DATA = dict(w=1000, h=round(Hh, 1), areas=areas, empty=empty, lines=lines, labels=labels,
            meta=dict(sources=SRC, areas=n, notes=DATA_NOTES.get(city, []), explain={"the-hi-vis-line": HIVIS},
                      **({"hp_credit": "Powered by ホットペッパー Webサービス", "hp_url": "https://webservice.recruit.co.jp/"} if CO == "jp" else {})),
            split={}, heritage=[], timeline=dict(years=[], lines=[], groups=[]), make=make)
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
json.dump(DATA, open(OUT, "w"), separators=(",", ":"), ensure_ascii=False)
print("written", OUT, round(os.path.getsize(OUT) / 1e6, 2), "MB", flush=True)
