"""Curated 'fun lines': proper tests, profiles, labelled gallery.

Share/rate lines  -> Moran-band rotation null (keeps spatial smoothness), single pre-chosen line so no search correction.
Brand-vs-brand    -> label-swap null: shuffle which stores are A and which are B (same store locations),
                     i.e. "do these two chains really live in different parts of Sydney?"
"""
import sys, numpy as np, pandas as pd, geopandas as gpd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt, matplotlib.patheffects as pe
from scipy.spatial import cKDTree
from scipy.stats import norm, rankdata
shp = sys.argv[1]; rng = np.random.default_rng(5); NN = 499

a = pd.read_csv("q_classic/areas.csv", dtype=str)
G = gpd.read_file(shp).to_crs(7856).set_index("SA2_CODE21").loc[a.SA2_CODE21].reset_index()
sig = pd.read_csv("signals_all.csv", dtype={"SA2_CODE_2021": str}).set_index("SA2_CODE_2021").loc[a.SA2_CODE21].reset_index(drop=True)
n = len(G)
pairs = gpd.sjoin(G[["geometry"]], G[["geometry"]], predicate="touches"); pairs = pairs[pairs.index < pairs.index_right]
E = [(i, j, G.geometry[i].boundary.intersection(G.geometry[j].boundary).length) for i, j in zip(pairs.index, pairs.index_right)]
E = np.array([e for e in E if e[2] >= 100]); I, J, W = E[:, 0].astype(int), E[:, 1].astype(int), E[:, 2]
Ad = np.zeros((n, n)); Ad[I, J] = 1; Ad[J, I] = 1; M = np.eye(n) - 1 / n
vals, vecs = np.linalg.eigh(M @ Ad @ M); vecs = vecs[:, np.argsort(vals)[::-1]]
rep = np.column_stack([G.geometry.representative_point().x, G.geometry.representative_point().y])
hivis = np.load("q_classic/sides.npy")[:, 0]

def rz(v): v = pd.Series(v).fillna(pd.Series(v).median()).values; return norm.ppf((rankdata(v) - 0.5) / n)
Zall = np.column_stack([rz(sig[c]) for c in sig.columns if c != "population"]); allcols = [c for c in sig.columns if c != "population"]
def cut(f): s = f > np.median(f); return ((s[I] != s[J]) * W).sum() / (0.5 * W.sum()), s
def rot_null(f):
    f = (f - f.mean()) / f.std(); c = vecs.T @ f; out = []
    for _ in range(NN):
        cr = c.copy()
        for x in range(0, n, 12):
            y = min(x + 12, n); q, _ = np.linalg.qr(rng.normal(size=(y - x, y - x))); cr[x:y] = q @ c[x:y]
        out.append(cut(vecs @ cr)[0])
    return np.array(out)

d = pd.read_pickle("places.pkl"); d = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d.lon, d.lat), crs=4326).to_crs(7856)
xy = np.column_stack([d.geometry.x, d.geometry.y])
def brand(*nm): return d.t.apply(lambda q: any(x in (q.get("brand", "") + "|" + q.get("name", "")).lower() for x in nm)).values
def brand_field(mA, mB):
    return np.log(cKDTree(xy[mB]).query(rep)[0] + 200) - np.log(cKDTree(xy[mA]).query(rep)[0] + 200)  # >0: A is closer
def swap_null(mA, mB):
    idx = np.where(mA | mB)[0]; nA = mA.sum(); out = []
    for _ in range(NN):
        p = rng.permutation(idx); a_, b_ = np.zeros(len(d), bool), np.zeros(len(d), bool); a_[p[:nA]] = True; b_[p[nA:]] = True
        out.append(cut(brand_field(a_, b_))[0])
    return np.array(out)

LINES = [  # name, kind, spec, "A side" plain words, "B side" plain words
 ("The Latte Line", "share", ("share_cafe", "share_fast_food"), "more cafes in the food mix", "more fast food in the food mix"),
 ("The Red Rooster Line", "brand", (("red rooster",), ("messina",)), "a Red Rooster is closer than a Messina", "a Messina is closer than a Red Rooster"),
 ("The Charcoal Chook Line", "brand", (("el jannah",), ("starbucks",)), "an El Jannah is closer than a Starbucks", "a Starbucks is closer than an El Jannah"),
 ("The Aldi Line", "share", ("share_super_aldi", "share_super_woolworths"), "Aldi's share of supermarkets is higher", "Woolworths' share is higher"),
 ("The Pokies Line", "share", ("pokies_per_1k", None), "more poker machines per resident", "fewer"),
 ("The Late Night Line", "share", ("late_licences_per_1k", None), "more after-midnight liquor licences per resident", "fewer"),
 ("The Bubble Tea Line", "share", ("share_cuisine_bubble_tea", None), "bubble tea is a bigger part of the food mix", "smaller"),
 ("Pho vs Pad Thai", "share", ("share_cuisine_vietnamese", "share_cuisine_thai"), "Vietnamese outnumbers Thai", "Thai outnumbers Vietnamese"),
 ("The Small Bar Line", "share", ("small_bars_per_1k", "share_pub"), "small bars per resident outweigh pubs", "pubs dominate"),
]
names = G.SA2_NAME21.values
res, sides = [], []
for nm, kind, spec, aw, bw in LINES:
    if kind == "share":
        A, B = spec; f = rz(sig[A]) - (rz(sig[B]) if B else 0); null = rot_null(f); used = [A] + ([B] if B else [])
    else:
        mA, mB = brand(*spec[0]), brand(*spec[1]); f = brand_field(mA, mB); null = swap_null(mA, mB); used = []
    c, s = cut(f); p = (1 + (null <= c).sum()) / (NN + 1)
    agree = (s == hivis).mean(); agree = max(agree, 1 - agree)
    eff = Zall[s].mean(0) - Zall[~s].mean(0); keep = [k for k in range(len(allcols)) if allcols[k] not in used]
    hi = [allcols[k] for k in sorted(keep, key=lambda k: -eff[k])[:5]]; lo = [allcols[k] for k in sorted(keep, key=lambda k: eff[k])[:5]]
    cutE = np.where(s[I] != s[J])[0]; longest = cutE[np.argsort(-W[cutE])[:8]]
    route = sorted({names[I[e]].split(" - ")[0] for e in longest} | {names[J[e]].split(" - ")[0] for e in longest})
    res.append(dict(line=nm, side_A=aw, side_B=bw, cleanness=round(c, 3), null_median=round(np.median(null), 3), p=round(p, 3),
                    same_route_as_hivis=f"{agree:.0%}", A_side_also_more=", ".join(hi), A_side_also_less=", ".join(lo),
                    runs_past=", ".join(route), A_examples=", ".join(names[np.argsort(-f)[:4]]), B_examples=", ".join(names[np.argsort(f)[:4]])))
    sides.append(s); print(nm, "cleanness", round(c, 3), "p", round(p, 3), "Hi-Vis agreement", f"{agree:.0%}")
R = pd.DataFrame(res); R.to_csv("fun_lines_tested.csv", index=False)
np.save("fun_sides.npy", np.column_stack(sides))

# gallery with suburb labels
lab = ["Sydney (North)", "Bondi Beach", "Manly", "Chatswood - East", "Hornsby - East", "Castle Hill - East", "Rouse Hill",
       "Blacktown (East)", "Penrith", "Parramatta - South", "Auburn - Central", "Strathfield - East", "Newtown", "Hurstville - Central",
       "Bankstown - North", "Lakemba", "Cabramatta - Lansvale", "Liverpool - East", "Campbelltown", "Camden - Ellis Lane", "Cronulla",
       "Dee Why", "Ryde - East", "Mount Druitt", "Marrickville - North", "Randwick - North", "St Ives", "Sutherland"]
fig, axs = plt.subplots(3, 3, figsize=(19, 20))
for ax, (nm, kind, spec, aw, bw), s, r in zip(axs.flat, LINES, sides, res):
    G.plot(ax=ax, color=np.where(s, "#e07a3f", "#3f7fb5"), edgecolor="white", linewidth=0.15)
    A_, B_ = G[s].geometry.union_all(), G[~s].geometry.union_all()
    gpd.GeoSeries([A_.boundary.intersection(B_.boundary)], crs=7856).plot(ax=ax, color="#111", linewidth=1.3)
    for l in lab:
        m = G[G.SA2_NAME21.str.startswith(l)]
        if len(m):
            pt = m.geometry.iloc[0].representative_point()
            ax.text(pt.x, pt.y, l.split(" - ")[0].replace(" (North)", " CBD").replace(" (East)", ""), fontsize=7.5, ha="center",
                    path_effects=[pe.withStroke(linewidth=2, foreground="white")])
    verdict = "beats chance" if r["p"] <= 0.05 else "not beyond chance"
    ax.set_title(f"{nm}\norange: {aw}\nblue: {bw}\n[{verdict}, p={r['p']}; same route as Hi-Vis/Latte on {r['same_route_as_hivis']} of areas]", fontsize=10)
    ax.set_axis_off()
fig.suptitle("Sydney / Split: the fun lines, tested (OSM venues Nov 2026, NSW liquor licences Nov 2026, 300 urban SA2s)", fontsize=15)

