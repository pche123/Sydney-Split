"""Tokyo / Split with HotPepper listings: Ramen Wars (OSM + HotPepper merged) and HotPepper lines.

python tokyo_hp.py out hotpepper_tokyo.csv
"""
import sys, os, re, numpy as np, pandas as pd, geopandas as gpd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt, matplotlib.patheffects as pe
from scipy.spatial import cKDTree
from scipy.stats import norm, rankdata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ramen_styles import style, STYLES
plt.rcParams["font.family"] = ["Noto Sans CJK JP", "DejaVu Sans"]
out, hpfile = sys.argv[1:3]; rng = np.random.default_rng(13); NN = 499; CRS = 6677

G = gpd.read_file(f"{out}/tokyo_units.gpkg"); st = pd.read_csv(f"{out}/study_units.csv", dtype=str).U
G = G.set_index("U").loc[st].reset_index(); n = len(G)
E = np.load(f"{out}/edges.npy"); I, J, W = E[:, 0].astype(int), E[:, 1].astype(int), E[:, 2]
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
census = ["age_65_plus", "age_20_39", "living_alone", "families_with_kids", "owners", "renters", "detached_houses", "towers_11_floors_plus",
          "managers", "professionals", "office_workers", "service_workers", "factory_workers", "drivers", "builders", "ind_it",
          "ind_hospitality", "self_employed", "density"]
Z = np.column_stack([rz(G[c]) for c in census]); names = (G.CITY_NAME + G.NAME).values

# ---------------- HotPepper ----------------
h = pd.read_csv(hpfile, low_memory=False, dtype={"sub_genre": str})
h = gpd.GeoDataFrame(h, geometry=gpd.points_from_xy(h.lng, h.lat), crs=4326).to_crs(CRS)
hxy = np.column_stack([h.geometry.x, h.geometry.y])
band = h.budget.fillna("").str.replace(",", "").str.extract(r"(\d+)～(\d+)円").astype(float)
h["price"] = band.mean(1)                                             # dinner budget band midpoint, yen
h["late"] = h.midnight.eq("営業している")
gc = h.genre_code
H = {"izakaya": gc.eq("G001"), "italian_french": gc.eq("G006"), "bar": gc.isin(["G012", "G002"]), "yakiniku": gc.eq("G008"),
     "cafe": gc.eq("G014"), "korean": gc.eq("G017"), "all": pd.Series(True, index=h.index)}
near = cKDTree(hxy).query_ball_point(rep, 1000.0)                     # about a 12-15 minute walk
def wcount(m): v = m.values; return np.array([v[ix].sum() for ix in near], float)
def wratio(a, b): ca, cb = wcount(a), wcount(b); return rz((ca + 0.5) / (ca + cb + 1) + 1e-9 * rng.normal(size=n))
late_share = rz((wcount(H["all"] & h.late) + 0.5) / (wcount(H["all"]) + 1) + 1e-9 * rng.normal(size=n))
pv = h.price.values
med_price = np.array([np.nanmedian(pv[ix]) if np.isfinite(pv[ix]).sum() >= 5 else np.nan for ix in near])
LINES = [
 ("The Late-Night Line", late_share, "within a 15-minute walk, more restaurants and bars stay open past midnight", "more places close before midnight"),
 ("The Price Line", rz(med_price), "the typical dinner nearby costs more (HotPepper budget bands)", "the typical dinner nearby is cheaper"),
 ("Izakaya vs Italian & French", wratio(H["izakaya"], H["italian_french"]), "izakaya outnumber Italian and French places more than usual", "Italian and French places hold their own"),
 ("Bars vs Izakaya", wratio(H["bar"], H["izakaya"]), "bars and bals are a bigger share of the night out", "izakaya are a bigger share"),
 ("The Yakiniku Line", wratio(H["yakiniku"], H["all"] & ~H["yakiniku"]), "yakiniku is a bigger share of the food nearby", "a smaller share"),
]
rows, sides = [], []
busy = wcount(H["all"]) >= 20                                          # examples only where there is enough to judge
for nm, f, aw, bw in LINES:
    null = rot_null(f); c, s = cut(f); p = (1 + (null <= c).sum()) / (NN + 1)
    eff = Z[s].mean(0) - Z[~s].mean(0); order = np.argsort(-np.abs(eff))[:4]
    rows.append(dict(line=nm, family="HotPepper", stores_A=None, stores_B=None, cleanness=round(c, 3), random_median=round(float(np.median(null)), 3), p=round(p, 3),
                     orange=aw, blue=bw, orange_side_census=", ".join(f"{'more' if eff[k] > 0 else 'fewer'} {census[k]} ({eff[k]:+.2f} sd)" for k in order),
                     orange_examples=", ".join(names[busy][np.argsort(-np.nan_to_num(f[busy], nan=-9))[:5]]), blue_examples=", ".join(names[busy][np.argsort(np.nan_to_num(f[busy], nan=9))[:5]])))
    sides.append(s); print(f"{nm:32s} p={p:.3f}")
print("price: median of neighbourhood medians", np.nanmedian(med_price), "yen; range", np.nanpercentile(med_price, [5, 95]))

# ---------------- Ramen Wars: OSM + HotPepper merged ----------------
V = pd.read_pickle(f"{out}/venues.pkl"); oxy = V[["x", "y"]].values
osm_style = np.full(len(V), None, object)
for k in STYLES: osm_style[V["ramen_" + k].values] = k
ram_o = V.ramen.values
hp_ram = (gc.eq("G013") | h.name.str.contains("ラーメン|らーめん|中華そば|つけ麺|家系", regex=True)).values
hp_style = np.array([style(nm_, f"{a} {b}") if r else None for nm_, a, b, r in zip(h.name, h.genre_catch.fillna(""), h["catch"].fillna(""), hp_ram)], object)
# a HotPepper shop within 60 m of an OSM ramen shop is the same shop: fill in its style if OSM had none
to = cKDTree(oxy[ram_o]); d, ix = to.query(hxy[hp_ram]); oidx = np.where(ram_o)[0][ix]
same = d < 60; new_hp = np.where(hp_ram)[0][~same]
for hi, oi in zip(np.where(hp_ram)[0][same], oidx[same]):
    if osm_style[oi] is None and hp_style[hi] is not None: osm_style[oi] = hp_style[hi]
rxy = np.vstack([oxy[ram_o], hxy[new_hp]]); rst = np.concatenate([osm_style[ram_o], hp_style[new_hp]])
print("ramen shops merged:", len(rxy), "| styled:", int(pd.notna(rst).sum()), pd.Series(rst).value_counts().to_dict())
def field(a, b, off=50.0): return np.log(cKDTree(rxy[b]).query(rep)[0] + off) - np.log(cKDTree(rxy[a]).query(rep)[0] + off)
def swap(a, b):
    idx = np.where(a | b)[0]; na = int(a.sum()); res = []
    for _ in range(NN):
        p_ = rng.permutation(idx); x, y = np.zeros(len(rst), bool), np.zeros(len(rst), bool); x[p_[:na]] = True; y[p_[na:]] = True
        res.append(cut(field(x, y))[0])
    return np.array(res)
isS = lambda k: np.array([v == k for v in rst])
RW = [("Ramen Wars: Iekei vs Hakata tonkotsu", "iekei", "tonkotsu"), ("Ramen Wars: Iekei vs classic shoyu", "iekei", "shoyu_classic"),
      ("Ramen Wars: Jiro-style vs classic shoyu", "jiro", "shoyu_classic"), ("Ramen Wars: Miso vs Hakata tonkotsu", "miso", "tonkotsu"),
      ("Ramen Wars: Tsukemen vs everything else", "tsukemen", None)]
NM = {"iekei": "an iekei (家系) shop", "tonkotsu": "a Hakata tonkotsu shop", "shoyu_classic": "a classic shoyu shop", "jiro": "a Jiro-style shop",
      "miso": "a miso ramen shop", "tsukemen": "a tsukemen shop", None: "another kind of ramen"}
for nm, a, b in RW:
    A = isS(a); B = ~A if b is None else isS(b)
    f = field(A, B); null = swap(A, B); c, s = cut(f); p = (1 + (null <= c).sum()) / (NN + 1)
    eff = Z[s].mean(0) - Z[~s].mean(0); order = np.argsort(-np.abs(eff))[:4]
    rows.append(dict(line=nm, family="Ramen", stores_A=int(A.sum()), stores_B=int(B.sum()), cleanness=round(c, 3), random_median=round(float(np.median(null)), 3),
                     p=round(p, 3), orange=f"{NM[a]} is closer", blue=f"{NM[b]} is closer",
                     orange_side_census=", ".join(f"{'more' if eff[k] > 0 else 'fewer'} {census[k]} ({eff[k]:+.2f} sd)" for k in order),
                     orange_examples=", ".join(names[np.argsort(-f)[:5]]), blue_examples=", ".join(names[np.argsort(f)[:5]])))
    sides.append(s); print(f"{nm:42s} {int(A.sum())} vs {int(B.sum())}  p={p:.3f}")
R = pd.DataFrame(rows); R["p_holm_in_family"] = np.nan
for fam, grp in R.groupby("family"):
    ps = grp.p.values; o = np.argsort(ps); adj = np.maximum.accumulate([min(1, ps[k] * (len(ps) - r)) for r, k in enumerate(o)])
    R.loc[grp.index[o], "p_holm_in_family"] = np.round(adj, 3)
R["verdict"] = np.where(R.p_holm_in_family <= 0.05, "Beats chance", "Could be chance")
R.to_csv(f"{out}/tokyo_hp_lines_tested.csv", index=False); np.save(f"{out}/tokyo_hp_sides.npy", np.column_stack(sides))
print(R[["line", "stores_A", "stores_B", "p", "p_holm_in_family", "verdict"]].to_string(index=False))

titles = [l[0] for l in LINES] + [r[0] for r in RW]; oranges = list(R.orange); blues = list(R.blue)
fig, axs = plt.subplots(4, 3, figsize=(21, 24))
for ax, s, t, o_, b_, v in zip(axs.flat, sides, titles, oranges, blues, R.verdict):
    G.plot(ax=ax, color=np.where(s, "#e07a3f", "#3f7fb5"), edgecolor="white", linewidth=0.08)
    ax.set_title(f"{t}  [{v}]\norange: {o_}\nblue: {b_}", fontsize=10); ax.set_axis_off()
for ax in list(axs.flat)[len(sides):]: ax.set_axis_off()
fig.suptitle("Tokyo / Split: HotPepper lines and Ramen Wars (restaurant listings Powered by ホットペッパー Webサービス)", fontsize=15)
plt.tight_layout(rect=[0, 0, 1, 0.98]); plt.savefig(f"{out}/tokyo_hp_gallery.png", dpi=80)
