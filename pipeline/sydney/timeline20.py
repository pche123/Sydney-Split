"""20 years of the Hi-Vis Line (2001-2021) on today's suburbs.

Crosswalk: each 2021 SA1 (with its 2021 population) is placed in the old SA2 that contains it. An old suburb's counts are
shared among today's suburbs in proportion to where its (2021) residents live. Validated on years present in two packs.
"""
import os
RAW = os.environ.get("SPLIT_RAW", "../data")   # raw downloads (see README)
import numpy as np, pandas as pd, geopandas as gpd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.stats import norm, rankdata, pearsonr
D = RAW; W_ = "."
a = pd.read_csv(f"{W_}/q_classic/areas.csv", dtype=str)
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

def load(path, key):
    return pd.read_csv(path, dtype={key: str}).set_index(key)

def to2021(df, cw):
    m = cw.merge(df, left_on="old", right_index=True)
    cols = [c for c in df.columns]
    return m[cols].mul(m.frac, axis=0).groupby(m.SA2_CODE21).sum()

P11 = f"{D}/tsp2011/2011 Census TSP Statistical Areas Level 2 for NSW/NSW"
P16 = f"{D}/tsp2016/2016 Census TSP Statistical Area 2 for NSW"
P21 = f"{D}/tsp2021/2021 Census TSP Statistical Area 2 for NSW"
cw11 = crosswalk(f"{D}/shp2011/SA2_2011_AUST.shp", "SA2_MAIN"); cw16 = crosswalk(f"{D}/shp2016/SA2_2016_AUST.shp", "SA2_MAIN16")
ind11, occ11 = to2021(load(f"{P11}/2011Census_T33_NSW_SA2_short.csv", "region_id"), cw11), to2021(load(f"{P11}/2011Census_T34_NSW_SA2_short.csv", "region_id"), cw11)
ind16, occ16 = to2021(load(f"{P16}/2016Census_T34_NSW_SA2.csv", "SA2_MAINCODE_2016"), cw16), to2021(load(f"{P16}/2016Census_T35_NSW_SA2.csv", "SA2_MAINCODE_2016"), cw16)
ind21, occ21 = load(f"{P21}/2021Census_T34_NSW_SA2.csv", "SA2_CODE_2021"), load(f"{P21}/2021Census_T35_NSW_SA2.csv", "SA2_CODE_2021")

codes = a.SA2_CODE21.values
def shares(ind, occ, c):
    i, o = ind.reindex(codes), occ.reindex(codes)
    return (i[f"Tpt_post_ware_{c}_P"] / i[f"Tot_{c}_P"]).values, (o[f"Professionals_{c}_P"] / o[f"Tot_{c}_P"]).values
S = {"2001": shares(ind11, occ11, "C01"), "2006": shares(ind16, occ16, "C06"), "2011": shares(ind21, occ21, "C11"),
     "2016": shares(ind21, occ21, "C16"), "2021": shares(ind21, occ21, "C21")}
# validation on overlapping years
for y, (x, ref) in {"2006 (2011 pack vs 2016 pack)": (shares(ind11, occ11, "C06")[1], S["2006"][1]),
                    "2011 (2011 pack vs 2021 pack)": (shares(ind11, occ11, "C11")[1], S["2011"][1]),
                    "2016 (2016 pack vs 2021 pack)": (shares(ind16, occ16, "C16")[1], S["2016"][1])}.items():
    ok = ~np.isnan(x) & ~np.isnan(ref)
    print(f"crosswalk check {y}: professionals share r = {pearsonr(x[ok], ref[ok])[0]:.3f}, mean abs diff {np.abs(x[ok]-ref[ok]).mean()*100:.2f} pts")

# graph (same as app)
G = gpd.read_file(f"{D}/shp/SA2_2021_AUST_GDA2020.shp").to_crs(7856).set_index("SA2_CODE21").loc[codes].reset_index()
pairs = gpd.sjoin(G[["geometry"]], G[["geometry"]], predicate="touches"); pairs = pairs[pairs.index < pairs.index_right]
E = np.array([e for e in [(i, j, G.geometry[i].boundary.intersection(G.geometry[j].boundary).length) for i, j in zip(pairs.index, pairs.index_right)] if e[2] >= 100])
I, J, Wt = E[:, 0].astype(int), E[:, 1].astype(int), E[:, 2]
def rz(v): v = pd.Series(v).fillna(pd.Series(v).median()).values; return norm.ppf((rankdata(v) - 0.5) / len(v))
def moran(x): x = x - x.mean(); return (len(x) / len(I)) * (x[I] * x[J]).sum() / (x ** 2).sum()
side, rows = {}, []
for y, (logi, prof) in S.items():
    f = rz(logi) - rz(prof); s = f > np.median(f); side[y] = s
    rows.append(dict(year=y, sydney_professionals_pct=round(np.nanmean(prof) * 100, 1), sorting_moran=round(moran(f), 3),
                     line_cleanness=round(((s[I] != s[J]) * Wt).sum() / (0.5 * Wt.sum()), 3),
                     same_side_as_2001=f"{(s == side['2001']).mean():.0%}"))
R = pd.DataFrame(rows); print(R.to_string(index=False)); R.to_csv(f"{W_}/hivis_20yr.csv", index=False)
names = G.SA2_NAME21.values
moved_p = np.where(side["2001"] & ~side["2021"])[0]; moved_h = np.where(~side["2001"] & side["2021"])[0]
print(f"\n2001->2021 crossed to professional side ({len(moved_p)}):", ", ".join(names[moved_p]))
print(f"2001->2021 crossed to Hi-Vis side ({len(moved_h)}):", ", ".join(names[moved_h]))
np.save(f"{W_}/hivis_sides_2001_2021.npy", np.column_stack([side[y] for y in S]))

# one clear figure: two maps, 2001 and 2021, plus who crossed
fig, axs = plt.subplots(1, 2, figsize=(18, 9))
for ax, y in zip(axs, ["2001", "2021"]):
    col = np.where(side[y], "#f0a33a", "#4f87b3").astype(object)
    if y == "2021": col[moved_p] = "#9cc3e0"; col[moved_h] = "#f7cf8f"
    G.plot(ax=ax, color=col, edgecolor="white", linewidth=0.2)
    A_, B_ = G[side[y]].geometry.union_all(), G[~side[y]].geometry.union_all()
    gpd.GeoSeries([A_.boundary.intersection(B_.boundary)], crs=7856).plot(ax=ax, color="#111", linewidth=2)
    ax.set_title(y, fontsize=18, fontweight="bold"); ax.set_axis_off()
from matplotlib.patches import Patch
fig.legend(handles=[Patch(color="#f0a33a", label="Hi-Vis side"), Patch(color="#4f87b3", label="Professional side"),
                    Patch(color="#9cc3e0", label="Crossed to professional side since 2001"), Patch(color="#f7cf8f", label="Crossed to Hi-Vis side since 2001")],
           loc="lower center", ncol=4, fontsize=12, frameon=False)
fig.suptitle("The Hi-Vis Line, 20 years apart", fontsize=20)
plt.tight_layout(rect=(0, 0.06, 1, 0.95)); plt.savefig(f"{W_}/hivis_2001_2021.png", dpi=95)

# --- noise check: same year (2011), two different packs/boundaries. Any "crossing" here is pure measurement noise.
l_a, p_a = shares(ind11, occ11, "C11"); l_b, p_b = S["2011"]
sa = (rz(l_a) - rz(p_a)); sa = sa > np.median(sa); sb = (rz(l_b) - rz(p_b)); sb = sb > np.median(sb)
print(f"\nNOISE CHECK 2011 vs 2011 (different packs): {(sa != sb).sum()} suburbs 'cross' from measurement noise alone")
l_c, p_c = shares(ind16, occ16, "C16"); l_d, p_d = S["2016"]
sc_ = rz(l_c) - rz(p_c); sc_ = sc_ > np.median(sc_); sd = rz(l_d) - rz(p_d); sd = sd > np.median(sd)
print(f"NOISE CHECK 2016 vs 2016 (different packs): {(sc_ != sd).sum()} suburbs 'cross' from measurement noise alone")

# robust crossers: score change bigger than 95% of same-year (noise-only) differences
noise = np.abs((rz(l_a) - rz(p_a)) - (rz(l_b) - rz(p_b))); thr = np.quantile(noise, 0.95)
f01 = rz(S["2001"][0]) - rz(S["2001"][1]); f21 = rz(S["2021"][0]) - rz(S["2021"][1]); dlt = f21 - f01
rp = [names[i] for i in moved_p if abs(dlt[i]) > thr]; rh = [names[i] for i in moved_h if abs(dlt[i]) > thr]
print(f"\nNoise threshold (95%): {thr:.2f}. Robust crossers to professional side ({len(rp)}): {', '.join(rp)}")
print(f"Robust crossers to Hi-Vis side ({len(rh)}): {', '.join(rh)}")
pd.DataFrame({"suburb": names, "side_2001": np.where(side["2001"], "Hi-Vis", "Professional"), "side_2021": np.where(side["2021"], "Hi-Vis", "Professional"),
              "score_change": dlt.round(2), "beyond_noise": np.abs(dlt) > thr}).to_csv(f"{W_}/hivis_20yr_suburbs.csv", index=False)

# final figure: only crossings beyond noise are highlighted
rp_i = [i for i in moved_p if abs(dlt[i]) > thr]; rh_i = [i for i in moved_h if abs(dlt[i]) > thr]
fig, axs = plt.subplots(1, 2, figsize=(18, 9))
for ax, y in zip(axs, ["2001", "2021"]):
    col = np.where(side[y], "#f0a33a", "#4f87b3").astype(object)
    if y == "2021":
        col[rp_i] = "#1d4f7a"; col[rh_i] = "#b85f00"
    G.plot(ax=ax, color=col, edgecolor="white", linewidth=0.2)
    A_, B_ = G[side[y]].geometry.union_all(), G[~side[y]].geometry.union_all()
    gpd.GeoSeries([A_.boundary.intersection(B_.boundary)], crs=7856).plot(ax=ax, color="#111", linewidth=2)
    ax.set_title(y, fontsize=18, fontweight="bold"); ax.set_axis_off()
inner = [i for i in rp_i if G.geometry[i].representative_point().x > 325000 and G.geometry[i].representative_point().y > 6240000]
other = [i for i in rp_i + rh_i if i not in inner]
for i in other:
    p = G.geometry[i].representative_point()
    axs[1].annotate(names[i].split(" - ")[0], (p.x, p.y), xytext=(p.x + 9000, p.y + 3000), fontsize=10, arrowprops=dict(arrowstyle="-", color="#333", lw=0.8))
if inner:
    pts_ = [G.geometry[i].representative_point() for i in inner]; cx, cy = np.mean([p.x for p in pts_]), np.mean([p.y for p in pts_])
    axs[1].annotate("Inner south:\n" + ", ".join(names[i].split(" - ")[0] for i in inner), (cx, cy), xytext=(cx + 14000, cy + 9000), fontsize=10,
                    arrowprops=dict(arrowstyle="-", color="#333", lw=0.8))
fig.legend(handles=[Patch(color="#f0a33a", label="Hi-Vis side (more warehouse, driving & labouring jobs)"), Patch(color="#4f87b3", label="Professional side"),
                    Patch(color="#1d4f7a", label="Clearly moved to professional side"), Patch(color="#b85f00", label="Clearly moved to Hi-Vis side")],
           loc="lower center", ncol=2, fontsize=12, frameon=False)
fig.suptitle("The Hi-Vis Line, 20 years apart: 93% of suburbs stayed put", fontsize=20)
plt.tight_layout(rect=(0, 0.08, 1, 0.95)); plt.savefig(f"{W_}/hivis_2001_2021.png", dpi=95)

# --- Line persistence test: do 2001 and 2021 agree more than two maps with the same smoothness would by chance?
rng = np.random.default_rng(1)
Ad = np.zeros((len(G), len(G))); Ad[I, J] = 1; Ad[J, I] = 1; Mc = np.eye(len(G)) - 1 / len(G)
vals, vecs = np.linalg.eigh(Mc @ Ad @ Mc); vecs = vecs[:, np.argsort(vals)[::-1]]
f21c = (f21 - f21.mean()) / f21.std(); coef = vecs.T @ f21c
obs = (side["2001"] == side["2021"]).mean(); null = []
for _ in range(999):
    cr = coef.copy()
    for x0 in range(0, len(G), 12):
        x1 = min(x0 + 12, len(G)); q, _ = np.linalg.qr(rng.normal(size=(x1 - x0, x1 - x0))); cr[x0:x1] = q @ coef[x0:x1]
    s = vecs @ cr; s = s > np.median(s); a_ = (s == side["2001"]).mean(); null.append(max(a_, 1 - a_))
null = np.array(null)
print(f"\nPERSISTENCE: observed agreement {obs:.0%}; random smooth maps agree {np.median(null):.0%} on average "
      f"(95th pct {np.quantile(null, .95):.0%}); p = {(1 + (null >= obs).sum()) / 1000:.3f}")
