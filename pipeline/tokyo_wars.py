"""Tokyo / Split: test the fun lines and chain wars.

Share lines   -> Moran spectral rotation null (same smoothness as the real map).
Chain vs chain-> label-swap null: same store locations, shuffled brand labels.
python tokyo_wars.py out/
"""
import sys, numpy as np, pandas as pd, geopandas as gpd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt, matplotlib.patheffects as pe
from scipy.spatial import cKDTree
from scipy.stats import norm, rankdata
from scipy.sparse.csgraph import connected_components
from scipy.sparse import coo_matrix
plt.rcParams["font.family"] = ["Noto Sans CJK JP", "IPAexGothic", "DejaVu Sans"]
out = sys.argv[1]; rng = np.random.default_rng(7); NN = 499

G = gpd.read_file(f"{out}/tokyo_units.gpkg")
G = G[(G.population >= 300) & (G.density >= 2000)].reset_index(drop=True)
pairs = gpd.sjoin(G[["geometry"]], G[["geometry"]], predicate="intersects"); pairs = pairs[pairs.index < pairs.index_right]
E = [(i, j, G.geometry[i].boundary.intersection(G.geometry[j].boundary).length) for i, j in zip(pairs.index, pairs.index_right)]
E = np.array([e for e in E if e[2] >= 50]); I, J = E[:, 0].astype(int), E[:, 1].astype(int)
nc, lab = connected_components(coo_matrix((np.ones(len(I)), (I, J)), shape=(len(G),) * 2), directed=False)
keep = np.where(lab == np.bincount(lab).argmax())[0]
G = G.iloc[keep].reset_index(drop=True); remap = -np.ones(len(lab), int); remap[keep] = np.arange(len(keep))
m = (remap[I] >= 0) & (remap[J] >= 0); I, J, W = remap[I[m]], remap[J[m]], E[m, 2]
n = len(G); print("study neighbourhoods", n, "borders", len(I), "people", int(G.population.sum()))
G[["U", "CITY_NAME", "NAME", "population"]].to_csv(f"{out}/study_units.csv", index=False)
np.save(f"{out}/edges.npy", np.column_stack([I, J, W]))
Ad = np.zeros((n, n)); Ad[I, J] = 1; Ad[J, I] = 1; Mc = np.eye(n) - 1 / n
vals, vecs = np.linalg.eigh(Mc @ Ad @ Mc); vecs = vecs[:, np.argsort(vals)[::-1]]
rep = np.column_stack([G.geometry.representative_point().x, G.geometry.representative_point().y])

def rz(v): v = pd.Series(v).fillna(pd.Series(v).median()).values; return norm.ppf((rankdata(v) - 0.5) / len(v))
census = ["age_65_plus", "age_20_39", "kids_under_15", "living_alone", "families_with_kids", "owners", "renters", "detached_houses",
          "towers_11_floors_plus", "managers", "professionals", "office_workers", "sales_workers", "service_workers", "factory_workers",
          "drivers", "builders", "cleaning_packing", "ind_it", "ind_manufacturing", "ind_finance", "ind_hospitality", "ind_health",
          "ind_construction", "ind_transport", "ind_retail", "self_employed", "density"]
Z = np.column_stack([rz(G[c]) for c in census])
def cut(f): s = f > np.median(f); return ((s[I] != s[J]) * W).sum() / (0.5 * W.sum()), s
def rot_null(f):
    f = (f - f.mean()) / f.std(); c = vecs.T @ f; res = []
    for _ in range(NN):
        cr = c.copy()
        for x in range(0, n, 12):
            y = min(x + 12, n); q, _ = np.linalg.qr(rng.normal(size=(y - x, y - x))); cr[x:y] = q @ c[x:y]
        res.append(cut(vecs @ cr)[0])
    return np.array(res)

V = pd.read_pickle(f"{out}/venues.pkl"); xy = V[["x", "y"]].values
V["chain_cafe"] = V.cafe & ~V.indie_cafe
def field(mA, mB, off=50.0): return np.log(cKDTree(xy[mB]).query(rep)[0] + off) - np.log(cKDTree(xy[mA]).query(rep)[0] + off)
def swap_null(mA, mB):
    idx = np.where(mA | mB)[0]; nA = int(mA.sum()); res = []
    for _ in range(NN):
        p = rng.permutation(idx); a, b = np.zeros(len(V), bool), np.zeros(len(V), bool); a[p[:nA]] = True; b[p[nA:]] = True
        res.append(cut(field(a, b))[0])
    return np.array(res)
def share(a, b=None): return rz(G[a]) - (rz(G[b]) if b else 0)
WALK = 700.0  # metres, about a 10-minute walk
_tree = cKDTree(xy)
_near = _tree.query_ball_point(rep, WALK)
def walk_count(col): v = V[col].values; return np.array([v[ix].sum() for ix in _near], float)
def walk_ratio(a, b): ca, cb = walk_count(a), walk_count(b); return rz((ca + 0.5) / (ca + cb + 1) + 1e-9 * rng.normal(size=n))

LINES = [  # name, family, kind, spec, orange side, blue side
 ("The Hi-Vis Line", "Census", "share", ("hivis_jobs", "laptop_jobs"), "more factory, driving, building and cleaning jobs", "more managers and professionals"),
 ("The Tower Line", "Census", "share", ("towers_11_floors_plus", "detached_houses"), "more homes in 11+ floor blocks", "more detached houses"),
 ("The Living Alone Line", "Census", "share", ("living_alone", "families_with_kids"), "more one-person homes", "more families with kids"),
 ("Coffee vs Alcohol", "Food", "walk", ("cafe", "izakaya_bar"), "within a 10-minute walk, cafés outnumber izakaya and bars more than usual", "izakaya and bars dominate more than usual"),
 ("Ramen vs Soba", "Food", "walk", ("ramen", "soba_udon"), "within a 10-minute walk, ramen outnumbers soba and udon more than usual", "soba and udon hold their own"),
 ("The Indie Café Line", "Food", "walk", ("indie_cafe", "chain_cafe"), "within a 10-minute walk, more cafés are independent", "more cafés are chains (Starbucks, Doutor, Tully's...)"),
 ("Konbini Wars: 7-Eleven vs FamilyMart", "Konbini", "brand", ("seven_eleven", "familymart"), "a 7-Eleven is closer", "a FamilyMart is closer"),
 ("Konbini Wars: Lawson vs 7-Eleven", "Konbini", "brand", ("lawson", "seven_eleven"), "a Lawson is closer", "a 7-Eleven is closer"),
 ("Konbini Wars: FamilyMart vs Lawson", "Konbini", "brand", ("familymart", "lawson"), "a FamilyMart is closer", "a Lawson is closer"),
 ("My Basket vs the konbini", "Konbini", "brand", ("my_basket", "konbini"), "a My Basket mini-supermarket is closer", "a konbini is closer"),
 ("Gyudon Wars: Matsuya vs Sukiya", "Chains", "brand", ("matsuya", "sukiya"), "a Matsuya is closer", "a Sukiya is closer"),
 ("Gyudon Wars: Yoshinoya vs Sukiya", "Chains", "brand", ("yoshinoya", "sukiya"), "a Yoshinoya is closer", "a Sukiya is closer"),
 ("Gyudon Wars: Matsuya vs Yoshinoya", "Chains", "brand", ("matsuya", "yoshinoya"), "a Matsuya is closer", "a Yoshinoya is closer"),
 ("Starbucks vs Doutor", "Chains", "brand", ("starbucks", "doutor"), "a Starbucks is closer", "a Doutor is closer"),
 ("Starbucks vs Komeda", "Chains", "brand", ("starbucks", "komeda"), "a Starbucks is closer", "a Komeda is closer"),
 ("Saizeriya vs Gusto", "Chains", "brand", ("saizeriya", "gusto"), "a Saizeriya is closer", "a Gusto is closer"),
 ("McDonald's vs Mos Burger", "Chains", "brand", ("mcdonalds", "mos_burger"), "a McDonald's is closer", "a Mos Burger is closer"),
 ("Ramen Wars: Iekei vs Hakata tonkotsu", "Ramen", "brand", ("iekei", "tonkotsu_hakata"), "an iekei (家系) shop is closer", "a Hakata tonkotsu shop is closer"),
 ("Ramen Wars: Jiro-style vs chūka soba", "Ramen", "brand", ("jiro", "chuka_soba"), "a Jiro-style shop is closer", "a classic chūka soba shop is closer"),
 ("Ramen Wars: Iekei vs chūka soba", "Ramen", "brand", ("iekei", "chuka_soba"), "an iekei shop is closer", "a classic chūka soba shop is closer"),
 ("CoCo Ichi vs Indian/Nepali curry", "Chains", "brand", ("coco_ichi", "indian_nepali"), "a CoCo Ichibanya is closer", "an Indian/Nepali curry house is closer"),
]
hv = None; rows, sides = [], []
nm_ = (G.CITY_NAME + G.NAME).values
for nm, fam, kind, spec, aw, bw in LINES:
    if kind == "share": f = share(*spec); null = rot_null(f); nA = nB = None
    elif kind == "walk": f = walk_ratio(*spec); null = rot_null(f); nA = nB = None
    else:
        mA, mB = V[spec[0]].values, V[spec[1]].values & ~V[spec[0]].values; f = field(mA, mB); null = swap_null(mA, mB); nA, nB = int(mA.sum()), int(mB.sum())
    c, s = cut(f); p = (1 + (null <= c).sum()) / (NN + 1)
    if hv is None: hv = s
    agree = max((s == hv).mean(), 1 - (s == hv).mean())
    eff = Z[s].mean(0) - Z[~s].mean(0); order = np.argsort(-np.abs(eff))[:4]
    rows.append(dict(line=nm, family=fam, test="label swap" if kind == "brand" else "smoothness-matched random maps",
                     stores_A=nA, stores_B=nB, cleanness=round(c, 3), random_median=round(float(np.median(null)), 3), p=round(p, 3),
                     same_route_as_hivis=round(float(agree), 2), orange=aw, blue=bw,
                     orange_side_census=", ".join(f"{'more' if eff[k] > 0 else 'fewer'} {census[k]} ({eff[k]:+.2f} sd)" for k in order),
                     orange_examples=", ".join(nm_[np.argsort(-f)[:5]]), blue_examples=", ".join(nm_[np.argsort(f)[:5]])))
    sides.append(s); print(f"{nm:42s} p={p:.3f} cleanness {c:.3f} (random {np.median(null):.3f})  Hi-Vis agreement {agree:.0%}")
R = pd.DataFrame(rows)
# Holm correction within each family, since we tried several pairings
R["p_holm_in_family"] = np.nan
for fam, grp in R.groupby("family"):
    ps = grp.p.values; o = np.argsort(ps); adj = np.maximum.accumulate([min(1, ps[k] * (len(ps) - r)) for r, k in enumerate(o)])
    R.loc[grp.index[o], "p_holm_in_family"] = np.round(adj, 3)
R["verdict"] = np.where(R.p_holm_in_family <= 0.05, "Beats chance", "Just for fun")
R.to_csv(f"{out}/tokyo_lines_tested.csv", index=False); np.save(f"{out}/tokyo_sides.npy", np.column_stack(sides))

LBL = {("新宿区", "西新宿"): "Shinjuku", ("渋谷区", "道玄坂"): "Shibuya", ("豊島区", "南池袋"): "Ikebukuro", ("中央区", "銀座"): "Ginza",
       ("台東区", "上野"): "Ueno", ("台東区", "浅草"): "Asakusa", ("世田谷区", "北沢"): "Shimokitazawa", ("杉並区", "高円寺南"): "Koenji",
       ("武蔵野市", "吉祥寺本町"): "Kichijoji", ("立川市", "曙町"): "Tachikawa", ("八王子市", "旭町"): "Hachioji", ("町田市", "原町田"): "Machida",
       ("大田区", "蒲田"): "Kamata", ("足立区", "千住"): "Kita-Senju", ("北区", "赤羽"): "Akabane", ("江東区", "豊洲"): "Toyosu",
       ("港区", "六本木"): "Roppongi", ("目黒区", "自由が丘"): "Jiyugaoka", ("江戸川区", "西葛西"): "Nishi-Kasai", ("墨田区", "錦糸"): "Kinshicho",
       ("練馬区", "練馬"): "Nerima", ("葛飾区", "金町"): "Kanamachi", ("府中市", "宮町"): "Fuchu", ("中野区", "中野"): "Nakano"}
fig, axs = plt.subplots(7, 3, figsize=(21, 40))
for ax, (nm, fam, kind, spec, aw, bw), s, (_, r) in zip(axs.flat, LINES, sides, R.iterrows()):
    G.plot(ax=ax, color=np.where(s, "#e07a3f", "#3f7fb5"), edgecolor="white", linewidth=0.08)
    for (ci, na), en in LBL.items():
        mm = G[(G.CITY_NAME == ci) & (G.NAME == na)]
        if len(mm):
            pt = mm.geometry.iloc[0].representative_point()
            ax.text(pt.x, pt.y, en, fontsize=7.5, ha="center", path_effects=[pe.withStroke(linewidth=2, foreground="white")])
    ax.set_title(f"{nm}  [{r.verdict}]\norange: {aw}\nblue: {bw}", fontsize=10); ax.set_axis_off()
fig.suptitle(f"Tokyo / Split: first pass ({n} neighbourhoods, Census 2020 + OpenStreetMap Nov 2026)", fontsize=16)
plt.tight_layout(rect=[0, 0, 1, 0.985]); plt.savefig(f"{out}/tokyo_gallery.png", dpi=80)
print(R[["line", "stores_A", "stores_B", "p", "p_holm_in_family", "verdict", "same_route_as_hivis"]].to_string(index=False))
