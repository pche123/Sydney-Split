"""Timeline data for the app: lines and community maps for 2001, 2006, 2011, 2016, 2021 on today's suburbs."""
import os
RAW = os.environ.get("SPLIT_RAW", "../data")   # raw downloads (see README)
import json, pickle, re, numpy as np, pandas as pd, geopandas as gpd
from scipy.stats import norm, rankdata
W = "."; YEARS = ["2001", "2006", "2011", "2016", "2021"]
codes = pd.read_csv(f"{W}/q_classic/areas.csv", dtype=str).SA2_CODE21.values
pk = pickle.load(open(f"{W}/timeline_counts.pkl", "rb")); data = {y: pk["data"][y].reindex(codes) for y in YEARS}
chk = pk["check"]["2011_from_2011pack"].reindex(codes)
G = gpd.read_file(f"{RAW}/shp/SA2_2021_AUST_GDA2020.shp").to_crs(7856).set_index("SA2_CODE21").loc[codes].reset_index()
n = len(G)
# same projection as the app
Gs = G.copy(); Gs["geometry"] = Gs.geometry.simplify(70, preserve_topology=True)
minx, miny, maxx, maxy = Gs.total_bounds; S = 1000 / (maxx - minx)
def P(x, y): return f"{(x - minx) * S:.1f},{(maxy - y) * S:.1f}"
def path(geom):
    gt = geom.geom_type
    if gt == "LineString": return "M" + "L".join(P(x, y) for x, y in geom.coords)
    if gt in ("MultiLineString", "GeometryCollection"): return "".join(path(g) for g in geom.geoms if g.geom_type in ("LineString", "MultiLineString"))
    return ""
from shapely.ops import linemerge
from shapely.geometry import MultiLineString
def cut_path(side):
    A_, B_ = G[side].geometry.union_all(), G[~side].geometry.union_all(); seg = A_.boundary.intersection(B_.boundary)
    flat = []
    for g in getattr(seg, "geoms", [seg]):
        if g.geom_type in ("LineString", "MultiLineString"): flat += list(getattr(g, "geoms", [g]))
    return path(linemerge(MultiLineString(flat)).simplify(40)) if flat else ""

pairs = gpd.sjoin(G[["geometry"]], G[["geometry"]], predicate="touches"); pairs = pairs[pairs.index < pairs.index_right]
E = np.array([e for e in [(i, j, G.geometry[i].boundary.intersection(G.geometry[j].boundary).length) for i, j in zip(pairs.index, pairs.index_right)] if e[2] >= 100])
I, J = E[:, 0].astype(int), E[:, 1].astype(int)
Ad = np.zeros((n, n)); Ad[I, J] = 1; Ad[J, I] = 1; Mc = np.eye(n) - 1 / n
vals, vecs = np.linalg.eigh(Mc @ Ad @ Mc); vecs = vecs[:, np.argsort(vals)[::-1]]
rng = np.random.default_rng(2)
def rz(v): v = pd.Series(v).fillna(pd.Series(v).median()).values; return norm.ppf((rankdata(v) - 0.5) / len(v))

def r(d, num, den): return (d[num] / d[den].replace(0, np.nan)).values
LINES = [  # id, name, orange words, blue words, A(d), B(d) or None, Sydney-wide stat (label, fn)
 ("hivis", "The Hi-Vis Line", "More warehouse, delivery & labouring jobs", "More office & professional jobs",
  lambda d: r(d, "logistics", "ind_total"), lambda d: r(d, "professionals", "occ_total"), ("professionals among workers", lambda d: d.professionals.sum() / d.occ_total.sum())),
 ("factory", "The Factory Line", "More factory workers", "Fewer factory workers",
  lambda d: r(d, "manufacturing", "ind_total"), None, ("factory workers among workers", lambda d: d.manufacturing.sum() / d.ind_total.sum())),
 ("laptop", "The Laptop vs Ute Line", "More tech & media workers, fewer tradies", "More tradies, fewer tech & media workers",
  lambda d: r(d, "media_it", "ind_total"), lambda d: r(d, "tradies", "occ_total"), ("tradies among workers", lambda d: d.tradies.sum() / d.occ_total.sum())),
 ("boomer", "The Boomer vs Builder Line", "Older residents, fewer builders", "Younger residents, more builders",
  lambda d: d.median_age.values, lambda d: r(d, "construction", "ind_total"), ("builders among workers", lambda d: d.construction.sum() / d.ind_total.sum())),
]
out_lines = []
for lid, name, aw, bw, fa, fb, (stat_label, stat) in LINES:
    def score(d): return rz(fa(d)) - (rz(fb(d)) if fb else 0)
    F = {y: score(data[y]) for y in YEARS}; sides = {y: F[y] > np.median(F[y]) for y in YEARS}
    noise = np.abs(score(chk) - F["2011"]); thr = np.quantile(noise, 0.95)        # same year, two packs = measurement noise
    dl = F["2021"] - F["2001"]
    toA = [int(i) for i in np.where(~sides["2001"] & sides["2021"] & (np.abs(dl) > thr))[0]]
    toB = [int(i) for i in np.where(sides["2001"] & ~sides["2021"] & (np.abs(dl) > thr))[0]]
    # persistence test 2001 vs 2021 (random maps with the same smoothness)
    f = (F["2021"] - F["2021"].mean()) / F["2021"].std(); c = vecs.T @ f; obs = (sides["2001"] == sides["2021"]).mean(); null = []
    for _ in range(499):
        cr = c.copy()
        for x0 in range(0, n, 12):
            x1 = min(x0 + 12, n); q, _ = np.linalg.qr(rng.normal(size=(x1 - x0, x1 - x0))); cr[x0:x1] = q @ c[x0:x1]
        s = vecs @ cr; s = s > np.median(s); a_ = (s == sides["2001"]).mean(); null.append(max(a_, 1 - a_))
    p = (1 + (np.array(null) >= obs).sum()) / 500
    out_lines.append(dict(id=lid, name=name, a=aw, b=bw, stat_label=stat_label,
                          stat=[round(float(stat(data[y])) * 100, 1) for y in YEARS],
                          same_as_2001=[round(float((sides[y] == sides["2001"]).mean()) * 100) for y in YEARS],
                          sides=[sides[y].astype(int).tolist() for y in YEARS], cuts=[cut_path(sides[y]) for y in YEARS],
                          toA=toA, toB=toB, persist_p=round(float(p), 3), null_agree=round(float(np.median(null)) * 100)))
    print(f"{name}: same side as 2001 in 2021 {out_lines[-1]['same_as_2001'][-1]}% (random maps ~{out_lines[-1]['null_agree']}%, p={p:.3f}); "
          f"clearly moved: {len(toA)} to orange, {len(toB)} to blue; {stat_label} {out_lines[-1]['stat']}")

groups = []
for kind, cols in [("birth", [c for c in data["2021"].columns if c.startswith("born_")]),
                   ("religion", [c for c in data["2021"].columns if c.startswith("rel_") and c != "rel_total"])]:
    for c in cols:
        nm = c.split("_", 1)[1]; pct, lq, Dv = [], [], []
        for y in YEARS:
            d = data[y]; nn = d[c].fillna(0).values; pop = d.persons.fillna(0).values
            city = nn.sum() / pop.sum(); share = np.where(pop > 0, nn / np.maximum(pop, 1), 0)
            pct.append(round(city * 100, 2)); lq.append([round(float(v), 1) for v in share / city])
            rest = pop - nn; Dv.append(round(float(0.5 * np.abs(nn / nn.sum() - rest / rest.sum()).sum()), 3))
        groups.append(dict(id=f"t-{kind}-{re.sub('[^a-z]+', '-', nm.lower())}", kind=kind, name=nm, pct=pct, D=Dv, lq=lq))
groups.sort(key=lambda g: (g["kind"] != "birth", -g["pct"][-1]))
for g in groups[:6] + [g for g in groups if g["kind"] == "religion"]:
    print(f"  {g['kind']:8s} {g['name']:15s} % of Sydney {g['pct']}  clustering {g['D']}")
d = json.load(open(f"{W}/app_data.json")); d["timeline"] = dict(years=YEARS, lines=out_lines, groups=groups)
json.dump(d, open(f"{W}/app_data.json", "w"), separators=(",", ":"))
print("app_data.json bytes:", len(json.dumps(d, separators=(",", ":"))))
