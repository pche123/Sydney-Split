"""Tokyo 2000-2020 on today's neighbourhoods.

Each year's smallest areas (丁目) are laid over the 2020 neighbourhoods and their counts shared out by area.
python tokyo_timeline.py <timeline folder with x2000..x2015> <raw2020 folder> <out folder>
"""
import sys, glob, re, numpy as np, pandas as pd, geopandas as gpd
from scipy.stats import norm, rankdata
tl, raw20, out = sys.argv[1:4]
CRS = 6677
units = gpd.read_file(f"{out}/tokyo_units.gpkg")
study = pd.read_csv(f"{out}/study_units.csv", dtype=str).U
units = units.set_index("U").loc[study].reset_index()[["U", "CITY_NAME", "NAME", "geometry"]]
clean = lambda s: re.sub(r"[\s　]", "", str(s))

def load_tables(folder):
    T = {}
    for f in glob.glob(f"{folder}/tbl*.txt"):
        t = pd.read_csv(f, encoding="cp932", dtype=str)
        lab = [clean(x) for x in t.iloc[0]]; t = t.iloc[1:]
        cols = [c for c in t.columns if re.match(r"T\d+", c)]; L = [lab[list(t.columns).index(c)] for c in cols]
        v = t[cols].apply(pd.to_numeric, errors="coerce").fillna(0); v.columns = L; v.index = t.KEY_CODE.values
        key = "|".join(L)
        if "職業" in L[0] or "専門的・技術的" in key: T["occ"] = v
        elif "６５歳以上" in key and "０～４歳" in key: T["age"] = v
        elif "世帯人員１人" in key: T["hsize"] = v
        elif "１１階建以上" in key: T["build"] = v
        elif "持ち家" in key: T["tenure"] = v
        elif L[0] == "人口総数": T["pop"] = v
    return T

def year_counts(shp, folder):
    g = gpd.read_file(shp); g = g[g.KEY_CODE.astype(str).str.len() >= 9]
    g = g.to_crs(CRS).dissolve("KEY_CODE").reset_index()[["KEY_CODE", "geometry"]]
    T = load_tables(folder); C = pd.DataFrame(index=g.KEY_CODE.astype(str))
    def col(tab, pat, first=False):
        v = T[tab];
        if first: return v.iloc[:, 0].groupby(level=0).first().reindex(C.index).fillna(0)
        cs = [c for c in v.columns if re.search(pat, c)]
        return v[cs].sum(1).groupby(level=0).first().reindex(C.index).fillna(0)
    C["pop"] = col("pop", "", True)
    C["workers"] = col("occ", "", True)
    C["laptop"] = col("occ", "専門的・技術的|管理的")
    C["hivis"] = col("occ", "運輸・通信|生産工程|輸送・機械|建設・採掘|運搬・清掃")
    C["age_all"] = col("age", "", True); C["age65"] = col("age", "^総数６５歳以上$")
    C["hh"] = col("hsize", "", True); C["alone"] = col("hsize", "世帯人員１人")
    C["homes"] = col("build", "", True); C["towers"] = col("build", "１１階建以上"); C["houses"] = col("build", "^一戸建$")
    C["hh_tenure"] = col("tenure", "", True); C["owners"] = col("tenure", "^持ち家$")
    g = g.merge(C, left_on=g.KEY_CODE.astype(str), right_index=True)
    g["a0"] = g.area
    x = gpd.overlay(g, units, how="intersection", keep_geom_type=True)
    f = x.area / x.a0
    num = [c for c in C.columns]
    agg = x[num].mul(f, axis=0).groupby(x.U).sum()
    return agg.reindex(units.U).fillna(0)

years = {2000: (glob.glob(f"{tl}/x2000/*.shp")[0], f"{tl}/x2000"), 2005: (glob.glob(f"{tl}/x2005/*.shp")[0], f"{tl}/x2005"),
         2010: (glob.glob(f"{tl}/x2010/*.shp")[0], f"{tl}/x2010"), 2015: (glob.glob(f"{tl}/x2015/*.shp")[0], f"{tl}/x2015"),
         2020: (f"{raw20}/r2ka13.shp", raw20)}
R = {}
for y, (shp, folder) in years.items():
    R[y] = year_counts(shp, folder); print(y, "people", int(R[y]["pop"].sum()), "workers", int(R[y].workers.sum()))
P = pd.concat(R, names=["year", "U"]); P.to_csv(f"{out}/timeline_counts.csv")

# ---- shares and the Hi-Vis score per year ----
def rz(v): return norm.ppf((rankdata(v) - 0.5) / len(v))
S = {}
for y in years:
    d = R[y]; sh = lambda a, b: (d[a] / d[b].replace(0, np.nan)).fillna(0)
    S[y] = pd.DataFrame({"hivis": sh("hivis", "workers"), "laptop": sh("laptop", "workers"), "age65": sh("age65", "age_all"),
                         "alone": sh("alone", "hh"), "towers": sh("towers", "homes"), "owners": sh("owners", "hh_tenure"), "pop": d["pop"]})
    S[y]["score"] = rz(S[y].hivis.values) - rz(S[y].laptop.values)
    S[y]["side"] = S[y].score > np.median(S[y].score)
W = pd.concat(S, names=["year", "U"]).reset_index(); W.to_csv(f"{out}/timeline_shares.csv", index=False)

# ---- persistence test against smoothness-matched random maps ----
E = np.load(f"{out}/edges.npy"); I, J = E[:, 0].astype(int), E[:, 1].astype(int); n = len(units)
Ad = np.zeros((n, n)); Ad[I, J] = 1; Ad[J, I] = 1; Mc = np.eye(n) - 1 / n
vals, vecs = np.linalg.eigh(Mc @ Ad @ Mc); vecs = vecs[:, np.argsort(vals)[::-1]]; rng = np.random.default_rng(11)
a, b = S[2000].side.values, S[2020].side.values; obs = (a == b).mean()
f = S[2000].score.values; f = (f - f.mean()) / f.std(); c = vecs.T @ f; null = []
for _ in range(499):
    cr = c.copy()
    for x in range(0, n, 12):
        yy = min(x + 12, n); q, _ = np.linalg.qr(rng.normal(size=(yy - x, yy - x))); cr[x:yy] = q @ c[x:yy]
    r = vecs @ cr; s = r > np.median(r); null.append(max((s == b).mean(), 1 - (s == b).mean()))
null = np.array(null); p = (1 + (null >= obs).sum()) / 500
print(f"Hi-Vis Line: {obs:.0%} of neighbourhoods on the same side 2000 -> 2020 (random maps: median {np.median(null):.0%}), p={p:.3f}")
ch = pd.DataFrame({"U": units.U, "name": units.CITY_NAME + units.NAME, "score2000": S[2000].score.values, "score2020": S[2020].score.values,
                   "side2000": a, "side2020": b, "pop2000": S[2000]["pop"].values, "pop2020": S[2020]["pop"].values,
                   "laptop2000": S[2000].laptop.values, "laptop2020": S[2020].laptop.values,
                   "hivis2000": S[2000].hivis.values, "hivis2020": S[2020].hivis.values})
ch["move"] = ch.score2020 - ch.score2000
ch.to_csv(f"{out}/hivis_2000_2020.csv", index=False)
big = ch[(ch.pop2000 > 1000) & (ch.pop2020 > 1000)]
print("biggest moves towards laptop jobs:"); print(big.nsmallest(10, "move")[["name", "laptop2000", "laptop2020", "pop2000", "pop2020"]].round(2).to_string(index=False))
print("biggest moves towards hi-vis jobs:"); print(big.nlargest(8, "move")[["name", "hivis2000", "hivis2020", "pop2000", "pop2020"]].round(2).to_string(index=False))
tot = {y: R[y].sum() for y in years}
print("Tokyo-wide trends (study area):")
for y in years:
    t = tot[y]; print(y, f"laptop jobs {t.laptop / t.workers:.1%}  hi-vis jobs {t.hivis / t.workers:.1%}  65+ {t.age65 / t.age_all:.1%}  living alone {t.alone / t.hh:.1%}  homes in 11+ floor blocks {t.towers / t.homes:.1%}  owners {t.owners / t.hh_tenure:.1%}")
for k in ["towers", "alone", "age65"]:
    a2, b2 = S[2000][k].values, S[2020][k].values
    print(k, "rank correlation 2000 vs 2020:", round(pd.Series(a2).corr(pd.Series(b2), method="spearman"), 2))
