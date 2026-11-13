"""Put 2001-2021 Census time-series data onto today's (2021) suburbs.

Packs: 2011 pack -> 2001, 2006 (2011 boundaries); 2016 pack -> 2006 (preferred, checked); 2021 pack -> 2011, 2016, 2021 (native).
Counts are shared out by where people live (2021 small-area populations). Medians are population-weighted averages.
Output: timeline_counts.pkl  {year: DataFrame indexed by 2021 SA2 code}
"""
import os
RAW = os.environ.get("SPLIT_RAW", "../data")   # raw downloads (see README)
import re, numpy as np, pandas as pd, geopandas as gpd, pickle, glob
D = RAW; W = "."
P = {"2011": f"{D}/tsp2011/2011 Census TSP Statistical Areas Level 2 for NSW/NSW",
     "2016": f"{D}/tsp2016/2016 Census TSP Statistical Area 2 for NSW",
     "2021": f"{D}/tsp2021/2021 Census TSP Statistical Area 2 for NSW"}
KEY = {"2011": "region_id", "2016": "SA2_MAINCODE_2016", "2021": "SA2_CODE_2021"}
SHP = {"2011": (f"{D}/shp2011/SA2_2011_AUST.shp", "SA2_MAIN"), "2016": (f"{D}/shp2016/SA2_2016_AUST.shp", "SA2_MAIN16")}

def load_tables(pack, tables):
    out = None
    for t in tables:
        for f in sorted(glob.glob(f"{P[pack]}/*Census_{t}*NSW_SA2*.csv")):
            d = pd.read_csv(f, dtype={KEY[pack]: str}).set_index(KEY[pack]); out = d if out is None else out.join(d, rsuffix="_dup")
    return out

def col(df, prefix, yy):
    pat = re.compile(rf"^{prefix}.*?(C{yy}|C20{yy}|20{yy}|_{yy}_).*_P$")
    m = [c for c in df.columns if pat.match(c)]
    return m[0] if m else None

# variables: name -> {pack: prefix} (same prefix in all packs unless given)
COUNT_VARS = {
    "logistics": ("Tpt_post_ware", "ind"), "manufacturing": ("Manuf", "ind"), "construction": ("Constr", "ind"),
    "media_it": ("Inf_Medi_Tele", "ind"), "ind_total": ("Tot", "ind"),
    "professionals": ("Professionals", "occ"), "tradies": ("Tech_trad_wkrs", "occ"), "occ_total": ("Tot", "occ"),
}
COB = {  # display name -> prefix per pack (2011, 2016, 2021)
    "China": ("Chi_ex_SARs_Taiw", "China", "China"), "India": ("India",) * 3, "United Kingdom": ("Unitd_Kingdom",) * 3,
    "Vietnam": ("Vietnam",) * 3, "Philippines": ("Philippines",) * 3, "New Zealand": ("New_Zealand",) * 3, "Lebanon": ("Lebanon",) * 3,
    "Iraq": ("Iraq",) * 3, "South Korea": ("Kor_Repub_Sth", "Korea", "Korea"), "Hong Kong": ("Hon_Kon_SAR_Chi", "Hong_Kong", "Hong_Kong"),
    "Italy": ("Italy",) * 3, "South Africa": ("South_Africa",) * 3, "Indonesia": ("Indonesia",) * 3, "Malaysia": ("Malaysia",) * 3,
    "Fiji": ("Fiji",) * 3, "Sri Lanka": ("Sri_Lanka",) * 3, "Greece": ("Greece",) * 3, "Germany": ("Germany",) * 3,
    "Ireland": ("Ireland",) * 3, "USA": ("Unit_Sts_Amer",) * 3, "Egypt": ("Egypt",) * 3, "Croatia": ("Croatia",) * 3,
    "Japan": ("Japan",) * 3, "Thailand": ("Thailand",) * 3, "Singapore": ("Singapore",) * 3, "Poland": ("Poland",) * 3,
    "Netherlands": ("Netherlands",) * 3, "Canada": ("Canada",) * 3,
}
RELPAT = {"Buddhism": r"^bud", "Catholic": r"cath", "Anglican": r"ang", "Islam": r"^islam", "Hinduism": r"^hind",
          "Judaism": r"^juda", "No religion": r"(no_relig|sbosb|sb_osb)"}
REL = {"Buddhism": "Budh_Tot", "Catholic": "C_Cath_Tot", "Anglican": "C_Ang_Tot", "Uniting Church": "C_Uni_Ch_Tot",
       "Islam": "Islam_Tot", "Hinduism": "Hinduism_Tot", "Judaism": "Judaism_Tot"}

def pack_year_frame(pack, yy):
    ind = load_tables(pack, ["T33"] if pack == "2011" else ["T34"])
    occ = load_tables(pack, ["T34"] if pack == "2011" else ["T35"])
    cob = load_tables(pack, ["T08"]); rel = load_tables(pack, ["T12"]); med = load_tables(pack, ["T02"])
    out = pd.DataFrame(index=ind.index)
    for v, (pre, tab) in COUNT_VARS.items():
        src = ind if tab == "ind" else occ; c = col(src, pre + "_", yy)
        out[v] = src[c] if c else np.nan
    pi = {"2011": 0, "2016": 1, "2021": 2}[pack]
    for nm, prefs in COB.items():
        c = col(cob, prefs[pi], yy); out["born_" + nm] = cob[c] if c else np.nan
    tot = col(cob, "Tot", yy); out["persons"] = cob[tot] if tot else np.nan
    AGE = r"_(0_14|15_24|25_34|35_44|45_54|55_64|65_74|75_84|85ov|85_ov)$"
    for nm, pat in RELPAT.items():
        cs = [k for k in rel.columns if k.startswith(f"C{yy}_") and re.search(pat, k[4:], re.I)]
        tot = [k for k in cs if k.endswith("_Tot") and not k.endswith("Tot_Tot")]
        ages = [k for k in cs if re.search(AGE, k)]
        out["rel_" + nm] = rel[tot[0]] if tot else (rel[ages].sum(axis=1) if ages else np.nan)
    for v, pre in [("median_age", "Med_age_persns"), ("hh_size", "Average_hh_size")]:
        c = [k for k in med.columns if k.startswith(pre) and (f"C20{yy}" in k or f"C{yy}" in k)]; out[v] = med[c[0]] if c else np.nan
    return out

# crosswalk weights from 2021 SA1 populations
sa1 = gpd.read_file(f"{D}/shp_sa1/SA1_2021_AUST_GDA2020.shp"); sa1 = sa1[sa1.GCC_CODE21 == "1GSYD"].to_crs(7856)
pop1 = pd.read_csv(f"{W}/signals_sa1.csv", dtype={"SA1_CODE_2021": str}).set_index("SA1_CODE_2021")["population"]
sa1["pop"] = sa1.SA1_CODE21.map(pop1).fillna(0)
pts = gpd.GeoDataFrame(sa1[["SA2_CODE21", "pop"]], geometry=sa1.geometry.representative_point(), crs=7856)
def weights(pack):
    shp, code = SHP[pack]; old = gpd.read_file(shp).to_crs(7856)[[code, "geometry"]]
    j = gpd.sjoin(pts, old, predicate="within"); w = j.groupby([code, "SA2_CODE21"])["pop"].sum().reset_index().rename(columns={code: "old"})
    w["f_old"] = w["pop"] / w.groupby("old")["pop"].transform("sum")       # share of old area going to each new area (counts)
    w["f_new"] = w["pop"] / w.groupby("SA2_CODE21")["pop"].transform("sum")  # share of new area coming from each old area (medians)
    return w
def to2021(df, w):
    m = w.merge(df, left_on="old", right_index=True)
    cnt = [c for c in df.columns if c not in ("median_age", "hh_size")]
    out = m[cnt].mul(m.f_old, axis=0).groupby(m.SA2_CODE21).sum(min_count=1)
    for c in ("median_age", "hh_size"):
        out[c] = (m[c] * m.f_new).groupby(m.SA2_CODE21).sum(min_count=1)
    return out

w11, w16 = weights("2011"), weights("2016")
data = {"2001": to2021(pack_year_frame("2011", "01"), w11),
        "2006": to2021(pack_year_frame("2016", "06"), w16),
        "2011": pack_year_frame("2021", "11"), "2016": pack_year_frame("2021", "16"), "2021": pack_year_frame("2021", "21")}
check = {"2011_from_2011pack": to2021(pack_year_frame("2011", "11"), w11), "2016_from_2016pack": to2021(pack_year_frame("2016", "16"), w16),
         "2006_from_2011pack": to2021(pack_year_frame("2011", "06"), w11)}
pickle.dump(dict(data=data, check=check), open(f"{W}/timeline_counts.pkl", "wb"))
a = pd.read_csv(f"{W}/q_classic/areas.csv", dtype=str).SA2_CODE21
for y, d in data.items():
    d = d.reindex(a); miss = d.isna().mean()
    print(y, "missing share:", ", ".join(f"{k}={v:.0%}" for k, v in miss.items() if v > 0) or "none")
