"""Quirky-line finder.

Candidates: every single signal and every "A vs B" pair (A minus B, rank-normal scale).
Mode 'classic': raw signals.  Mode 'quirky': signals first residualised on household income,
distance from the CBD and density, so lines that just redraw the money/inner-outer gradient drop out.

Line score = length of the border of a median split, relative to a random split (lower = cleaner line).
Chance test: rotate the (residual) signals jointly within bands of the Moran eigenbasis
(keeps spatial smoothness and cross-signal correlation), rerun the WHOLE search, record the best score.

Usage: python quirky.py <sa2_shp> <signals.csv> <outdir> <classic|quirky>
"""
import sys, os, itertools, json
import numpy as np, pandas as pd, geopandas as gpd
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components
from scipy.stats import norm, rankdata
from sklearn.metrics import adjusted_rand_score

shp, sig_csv, outdir, mode = sys.argv[1:5]
os.makedirs(outdir, exist_ok=True)
rng = np.random.default_rng(11)
NNULL, BAND = 199, 12
CONTROL = "median_tot_hhd_inc_weekly"
LOCKDOWN = {"train_commute", "bus_commute", "drive_to_work", "walk_to_work", "cycle_to_work", "work_from_home", "ute_truck_commute"}

g = gpd.read_file(shp); g = g[g.GCC_CODE21 == "1GSYD"].to_crs(7856)
s = pd.read_csv(sig_csv, dtype={"SA2_CODE_2021": str}).set_index("SA2_CODE_2021")
g = g.join(s, on="SA2_CODE21"); g["density"] = g.population / g.AREASQKM21
g = g[(g.population >= 1000) & (g.density >= 300)].reset_index(drop=True)
cbd = gpd.GeoSeries.from_xy([151.2093], [-33.8688], crs=4326).to_crs(7856).iloc[0]
g["cbd_km"] = g.geometry.centroid.distance(cbd) / 1000

pairs = gpd.sjoin(g[["geometry"]], g[["geometry"]], predicate="touches"); pairs = pairs[pairs.index < pairs.index_right]
E = []
for i, j in zip(pairs.index, pairs.index_right):
    L = g.geometry[i].boundary.intersection(g.geometry[j].boundary).length
    if L >= 100: E.append((i, j, L))
E = np.array(E); n = len(g)
A = sp.coo_matrix((np.ones(len(E)), (E[:, 0].astype(int), E[:, 1].astype(int))), shape=(n, n)); A = A + A.T
_, lab = connected_components(A); keep = lab == np.bincount(lab).argmax()
remap = -np.ones(n, int); remap[keep] = np.arange(keep.sum())
E = E[keep[E[:, 0].astype(int)] & keep[E[:, 1].astype(int)]]
g = g[keep].reset_index(drop=True); n = len(g)
I, J, W = remap[E[:, 0].astype(int)], remap[E[:, 1].astype(int)], E[:, 2]

base_cols = [c for c in s.columns if c != "population"]
X = g[base_cols].astype(float); X = X.fillna(X.median())
Z = np.column_stack([norm.ppf((rankdata(X[c]) - 0.5) / n) for c in base_cols])
Z = (Z - Z.mean(0)) / Z.std(0)
Zraw = Z.copy()
if mode == "quirky":
    D = np.column_stack([np.ones(n), np.log(g.cbd_km + 1), np.log(g.cbd_km + 1) ** 2, np.log(g.density),
                         Zraw[:, base_cols.index(CONTROL)]])
    Z = Z - D @ np.linalg.lstsq(D, Z, rcond=None)[0]
    Z = Z / np.maximum(Z.std(0), 1e-9)
cols = [c for c in base_cols if not (mode == "quirky" and c == CONTROL)]
Z = Z[:, [base_cols.index(c) for c in cols]]
p = len(cols)

# candidate map: column k of Z@Mmap is a candidate
cands = [(a, None) for a in range(p)] + list(itertools.combinations(range(p), 2))
Mmap = np.zeros((p, len(cands)))
for k, (a, b) in enumerate(cands):
    Mmap[a, k] = 1
    if b is not None: Mmap[b, k] = -1


def score(Zm):
    C = Zm @ Mmap
    S = C > np.median(C, axis=0)
    cut = ((S[I] != S[J]) * W[:, None]).sum(0)
    return cut / (0.5 * W.sum()), S, C


sc, S, C = score(Z)

# chance test
Ad = np.zeros((n, n)); Ad[I, J] = 1; Ad[J, I] = 1
Mc = np.eye(n) - 1 / n
vals, vecs = np.linalg.eigh(Mc @ Ad @ Mc); vecs = vecs[:, np.argsort(vals)[::-1]]
coef = vecs.T @ Z
null_best = []
for _ in range(NNULL):
    cr = coef.copy()
    for a in range(0, n, BAND):
        b = min(a + BAND, n); q, _ = np.linalg.qr(rng.normal(size=(b - a, b - a))); cr[a:b] = q @ coef[a:b]
    null_best.append(score(vecs @ cr)[0].min())
null_best = np.array(null_best)
pval = np.array([(1 + (null_best <= x).sum()) / (NNULL + 1) for x in sc])

# synergy: is a pair cleaner than both of its parts?
single = sc[:p]
synergy = np.array([np.nan if b is None else min(single[a], single[b]) - sc[k] for k, (a, b) in enumerate(cands)])


def name(k):
    a, b = cands[k]
    return cols[a] if b is None else f"{cols[a]} vs {cols[b]}"


# families: greedy dedupe by partition agreement
order = np.argsort(sc)
picked = []
for k in order:
    if len(picked) >= 40: break
    if any(abs(adjusted_rand_score(S[:, k], S[:, m])) > 0.35 for m in picked): continue
    picked.append(k)

names = g.SA2_NAME21.values
rows = []
for k in picked:
    side = S[:, k]
    eff = Zraw[side].mean(0) - Zraw[~side].mean(0)              # raw standardized difference, all signals
    top_hi = [base_cols[t] for t in np.argsort(-eff)[:6]]
    top_lo = [base_cols[t] for t in np.argsort(eff)[:6]]
    cutE = np.where(side[I] != side[J])[0]
    longest = cutE[np.argsort(-W[cutE])[:6]]
    route = sorted({names[I[e]] for e in longest} | {names[J[e]] for e in longest})
    hi_anchor = names[np.argsort(-C[:, k])[:4]]
    lo_anchor = names[np.argsort(C[:, k])[:4]]
    frac_lockdown = any(c in LOCKDOWN for c in name(k).split(" vs "))
    rows.append(dict(line=name(k), cut_vs_random=round(sc[k], 3), p_chance=round(pval[k], 3),
                     pair_synergy=None if np.isnan(synergy[k]) else round(synergy[k], 3),
                     lockdown_commute_signal=frac_lockdown,
                     higher_side_also_more=", ".join(top_hi), higher_side_also_less=", ".join(top_lo),
                     most_extreme_high=", ".join(hi_anchor), most_extreme_low=", ".join(lo_anchor),
                     runs_past=", ".join(route)))
R = pd.DataFrame(rows)
R.to_csv(os.path.join(outdir, "leaderboard.csv"), index=False)
np.save(os.path.join(outdir, "sides.npy"), S[:, picked])
g[["SA2_CODE21", "SA2_NAME21"]].to_csv(os.path.join(outdir, "areas.csv"), index=False)
json.dump(dict(mode=mode, areas=n, borders=len(W), signals=p, candidates=len(cands), null_draws=NNULL,
               best_observed=float(sc.min()), null_best_5pct=float(np.quantile(null_best, 0.05)),
               null_best_median=float(np.median(null_best)), n_beating_null=int((pval <= 0.05).sum())),
          open(os.path.join(outdir, "summary.json"), "w"), indent=1)
print(json.load(open(os.path.join(outdir, "summary.json"))))
pd.set_option("display.width", 250)
print(R.head(20)[["line", "cut_vs_random", "p_chance", "pair_synergy", "most_extreme_high", "most_extreme_low"]].to_string(max_colwidth=70))
