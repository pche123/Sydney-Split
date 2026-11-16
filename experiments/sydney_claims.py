"""Test popular claims about Sydney's Latte Line (Wikipedia, press) against the data.

    python experiments/sydney_claims.py <data folder> <work folder> [out folder]

1. "The line is hardening": for each census year 2001-2021, how clean is the Hi-Vis and Factory border compared with
   random maps that are as smooth as *that year's* map? z = (border - mean of null) / sd of null; more negative = cleaner.
   Hardening = z falling steadily. Same harmonised counts, areas and borders as the app's timeline (timeline20.py).
2. "Above the line, homes cost over $1m": the Money Line (2021 median rent, mortgage repayment and household income
   by suburb), tested like any other line, and which route it follows (Latte, Hi-Vis, Factory, Train vs Car).
"""
import json, os, sys
import numpy as np, pandas as pd, geopandas as gpd
from scipy.stats import norm, rankdata, spearmanr
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); sys.path[:0] = [ROOT]
from linetests.landscape import MultiScaleNull, calibrated_map_test
CAL = os.environ.get("SYD_CAL") == "1"   # 1: p-values from the calibrated (double-bootstrap) test, as every verdict uses

D, W_ = sys.argv[1], sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "results", "sydney_claims")
os.makedirs(OUT, exist_ok=True)
a = pd.read_csv(f"{W_}/q_classic/areas.csv", dtype=str); codes = a.SA2_CODE21.values
G = gpd.read_file(f"{D}/shp/SA2_2021_AUST_GDA2020.shp").to_crs(7856).set_index("SA2_CODE21").loc[codes].reset_index()
pairs = gpd.sjoin(G[["geometry"]], G[["geometry"]], predicate="touches"); pairs = pairs[pairs.index < pairs.index_right]
E = np.array([e for e in [(i, j, G.geometry[i].boundary.intersection(G.geometry[j].boundary).length) for i, j in zip(pairs.index, pairs.index_right)] if e[2] >= 100])
I, J, Wt = E[:, 0].astype(int), E[:, 1].astype(int), E[:, 2]
GN = MultiScaleNull(G.geometry, I, J, Wt, m=25)
def rz(v): v = pd.Series(v).fillna(pd.Series(v).median()).values; return norm.ppf((rankdata(v) - 0.5) / len(v))
def border(f): s = f > np.median(f); return ((s[I] != s[J]) * Wt).sum() / (0.5 * Wt.sum())
rng = np.random.default_rng(11)
def judge(f, B=399):
    par = GN.fit(f); S = GN.simulate(par, B, rng)
    null = np.array([border(S[:, b]) for b in range(B)]); obs = border(f)
    p = (1 + (null <= obs).sum()) / (B + 1)
    if CAL:
        r = calibrated_map_test(GN, f, B=199, R=40, Bin=99, seed=7)
        if r["p_cal"] < 0.1 and os.environ.get("SYD_FINE", "1") == "1": r = calibrated_map_test(GN, f, B=199, R=200, Bin=99, seed=7)
        p = r["p_cal"]
    return obs, (obs - null.mean()) / null.std(), p

# ---------------------------------------------------------------- 1. hardening
sys.path.insert(0, os.path.join(ROOT, "pipeline", "sydney"))
def load(path, key): return pd.read_csv(path, dtype={key: str}).set_index(key)
# crosswalk exactly as timeline20.py: old suburbs' counts shared by where their (2021) residents live
sa1 = gpd.read_file(f"{D}/shp_sa1/SA1_2021_AUST_GDA2020.shp"); sa1 = sa1[sa1.GCC_CODE21 == "1GSYD"].to_crs(7856)
pop1 = pd.read_csv(f"{W_}/signals_sa1.csv", dtype={"SA1_CODE_2021": str}).set_index("SA1_CODE_2021")["population"]
sa1["pop"] = sa1.SA1_CODE21.map(pop1).fillna(0)
pts = gpd.GeoDataFrame(sa1[["SA1_CODE21", "SA2_CODE21", "pop"]], geometry=sa1.geometry.representative_point(), crs=7856)
def crosswalk(shp, code_col):
    old = gpd.read_file(shp).to_crs(7856)[[code_col, "geometry"]]
    j = gpd.sjoin(pts, old, predicate="within")
    w = j.groupby([code_col, "SA2_CODE21"])["pop"].sum().reset_index()
    w["frac"] = w["pop"] / w.groupby(code_col)["pop"].transform("sum")
    return w[[code_col, "SA2_CODE21", "frac"]].rename(columns={code_col: "old"})
def to2021(df, cw):
    m = cw.merge(df, left_on="old", right_index=True); return m[list(df.columns)].mul(m.frac, axis=0).groupby(m.SA2_CODE21).sum()
P11 = f"{D}/tsp2011/2011 Census TSP Statistical Areas Level 2 for NSW/NSW"; P16 = f"{D}/tsp2016/2016 Census TSP Statistical Area 2 for NSW"
P21 = f"{D}/tsp2021/2021 Census TSP Statistical Area 2 for NSW"
cw11 = crosswalk(f"{D}/shp2011/SA2_2011_AUST.shp", "SA2_MAIN"); cw16 = crosswalk(f"{D}/shp2016/SA2_2016_AUST.shp", "SA2_MAIN16")
ind11, occ11 = to2021(load(f"{P11}/2011Census_T33_NSW_SA2_short.csv", "region_id"), cw11), to2021(load(f"{P11}/2011Census_T34_NSW_SA2_short.csv", "region_id"), cw11)
ind21, occ21 = load(f"{P21}/2021Census_T34_NSW_SA2.csv", "SA2_CODE_2021"), load(f"{P21}/2021Census_T35_NSW_SA2.csv", "SA2_CODE_2021")
ind16, occ16 = to2021(load(f"{P16}/2016Census_T34_NSW_SA2.csv", "SA2_MAINCODE_2016"), cw16), to2021(load(f"{P16}/2016Census_T35_NSW_SA2.csv", "SA2_MAINCODE_2016"), cw16)
packs = {"2001": (ind11, occ11, "C01"), "2006": (ind16, occ16, "C06"), "2011": (ind21, occ21, "C11"), "2016": (ind21, occ21, "C16"), "2021": (ind21, occ21, "C21")}
HF = f"{OUT}/hardening{'_calibrated' if CAL else ''}.csv"
rows = pd.read_csv(HF).to_dict("records") if os.path.exists(HF) and os.environ.get("SYD_RESUME") == "1" else []
have = {(r["line"], str(r["year"])) for r in rows}
for y, (ind, occ, c) in packs.items():
    i, o = ind.reindex(codes), occ.reindex(codes)
    hv = rz((i[f"Tpt_post_ware_{c}_P"] / i[f"Tot_{c}_P"]).values) - rz((o[f"Professionals_{c}_P"] / o[f"Tot_{c}_P"]).values)
    fc = rz((i[f"Manuf_{c}_P"] / i[f"Tot_{c}_P"]).values) if f"Manuf_{c}_P" in i else None
    for name, f in [("Hi-Vis", hv), ("Factory", fc)]:
        if f is None or (name, y) in have: continue
        obs, z, p = judge(f); rows.append(dict(line=name, year=y, border=round(obs, 3), z=round(z, 2), p=round(p, 4)))
        pd.DataFrame(rows).to_csv(HF, index=False)   # saved after every map, so a restart loses at most one
        print(f"{name:8s} {y}: border {obs:.3f}  z = {z:+.2f}  p = {p:.4f}", flush=True)
H = pd.DataFrame(rows); H.to_csv(f"{OUT}/hardening{'_calibrated' if CAL else ''}.csv", index=False)
for name, g in H.groupby("line"):
    r, p = spearmanr(g.year.astype(int), g.z); print(f"{name}: trend in z over 2001-2021: Spearman {r:+.2f} (p = {p:.3f}; 5 points, descriptive)")

if os.environ.get("SYD_SKIP_MONEY") == "1": sys.exit(0)   # the Money Line is tested, calibrated, in experiments/latte_claims.py
# ---------------------------------------------------------------- 2. the Money Line
g02 = load(f"{D}/gcp_sa2/2021 Census GCP Statistical Area 2 for NSW/2021Census_G02_NSW_SA2.csv", "SA2_CODE_2021").reindex(codes)
app = json.load(open(f"{ROOT}/app/data/sydney.json")); geo = gpd.read_file(f"{W_}/sydney_sa2_300.geojson")
pos = {nm: k for k, nm in enumerate(a.SA2_NAME21 if "SA2_NAME21" in a else geo.set_index("id").loc[codes].name)}
names = [ar["name"] for ar in app["areas"]]; order = [pos.get(nm) for nm in names]
sides = {}
for l in app["lines"]:
    s = np.full(len(codes), np.nan); s[[o for o in order if o is not None]] = [v for v, o in zip(l["side"], order) if o is not None]; sides[l["name"]] = s
mrows = []
for col, nm in [("Median_rent_weekly", "rent"), ("Median_mortgage_repay_monthly", "mortgage"), ("Median_tot_hhd_inc_weekly", "household income")]:
    f = rz(g02[col].values.astype(float)); obs, z, p = judge(f)
    s = f > np.median(f); agree = {}
    for ln in ["The Latte Line", "The Hi-Vis Line", "The Factory Line", "Train vs Car", "The Laptop vs Ute Line"]:
        if ln in sides:
            ok = ~np.isnan(sides[ln]); m = (s[ok] == sides[ln][ok].astype(bool)).mean(); agree[ln] = round(max(m, 1 - m), 3)
    mrows.append(dict(money=nm, border=round(obs, 3), z=round(z, 2), p=round(p, 4), **{f"match {k}": v for k, v in agree.items()}))
    print(f"Money Line ({nm}): z = {z:+.2f}, p = {p:.4f}; route match: " + ", ".join(f"{k} {v:.0%}" for k, v in agree.items()), flush=True)
pd.DataFrame(mrows).to_csv(f"{OUT}/money_line{'_calibrated' if CAL else ''}.csv", index=False)
