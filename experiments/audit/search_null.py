import os, sys; _H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [_H, os.path.dirname(_H), os.path.join(os.path.dirname(_H), "..")]  # experiments, repo root
from paths import SYD, TOK, RAW  # noqa: E402
"""Search-wide chance test for the Sydney census line search, redone with the landscape null.

The search scores every census signal and every 'A vs B' pair (1,596 candidates) and keeps
the cleanest.  To ask "could a search this big find a line this clean by chance?" we need
null worlds for ALL signals at once, keeping how the signals move together.

Joint landscape null: take principal components of the (rank-normal) signal matrix.  The
components are uncorrelated across areas; give each its own fitted multi-scale landscape
(how smooth it is in real space), simulate fresh components independently, rotate back to
signals, rerun the whole search and record the best score.  The search-wide p of a line is
the share of null searches whose best line is at least as clean.

Usage: python search_null.py <classic|quirky> <B>"""
import sys, json, itertools
import numpy as np, pandas as pd, geopandas as gpd
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components
from scipy.stats import norm, rankdata
from linetests.landscape import MultiScaleNull

mode, B = sys.argv[1], int(sys.argv[2])
CONTROL = "median_tot_hhd_inc_weekly"


def prepare():
    g = gpd.read_file(f"{RAW}/shp/SA2_2021_AUST_GDA2020.shp"); g = g[g.GCC_CODE21 == "1GSYD"].to_crs(7856)
    s = pd.read_csv(f"{SYD}/signals_sa2.csv", dtype={"SA2_CODE_2021": str}).set_index("SA2_CODE_2021")
    g = g.join(s, on="SA2_CODE21"); g["density"] = g.population / g.AREASQKM21
    g = g[(g.population >= 1000) & (g.density >= 300)].reset_index(drop=True)
    cbd = gpd.GeoSeries.from_xy([151.2093], [-33.8688], crs=4326).to_crs(7856).iloc[0]
    g["cbd_km"] = g.geometry.centroid.distance(cbd) / 1000
    pairs = gpd.sjoin(g[["geometry"]], g[["geometry"]], predicate="touches"); pairs = pairs[pairs.index < pairs.index_right]
    E = np.array([(i, j, g.geometry[i].boundary.intersection(g.geometry[j].boundary).length) for i, j in zip(pairs.index, pairs.index_right)])
    E = E[E[:, 2] >= 100]; n = len(g)
    A = sp.coo_matrix((np.ones(len(E)), (E[:, 0].astype(int), E[:, 1].astype(int))), shape=(n, n)); A = A + A.T
    _, lab = connected_components(A); keep = lab == np.bincount(lab).argmax()
    remap = -np.ones(n, int); remap[keep] = np.arange(keep.sum())
    E = E[keep[E[:, 0].astype(int)] & keep[E[:, 1].astype(int)]]
    g = g[keep].reset_index(drop=True); n = len(g)
    I, J, W = remap[E[:, 0].astype(int)], remap[E[:, 1].astype(int)], E[:, 2]
    base = [c for c in s.columns if c != "population"]
    X = g[base].astype(float); X = X.fillna(X.median())
    Z = np.column_stack([norm.ppf((rankdata(X[c]) - 0.5) / n) for c in base]); Z = (Z - Z.mean(0)) / Z.std(0)
    if mode == "quirky":
        D = np.column_stack([np.ones(n), np.log(g.cbd_km + 1), np.log(g.cbd_km + 1) ** 2, np.log(g.density), Z[:, base.index(CONTROL)]])
        Z = Z - D @ np.linalg.lstsq(D, Z, rcond=None)[0]; Z = Z / np.maximum(Z.std(0), 1e-9)
    cols = [c for c in base if not (mode == "quirky" and c == CONTROL)]
    Z = Z[:, [base.index(c) for c in cols]]
    return g, I, J, W, Z, cols


g, I, J, W, Z, cols = prepare(); n, p = Z.shape
cands = [(a, None) for a in range(p)] + list(itertools.combinations(range(p), 2))
Mmap = np.zeros((p, len(cands)))
for k, (a, b) in enumerate(cands):
    Mmap[a, k] = 1
    if b is not None: Mmap[b, k] = -1


def score(Zm):
    C = Zm @ Mmap; S = C > np.median(C, axis=0)
    return ((S[I] != S[J]) * W[:, None]).sum(0) / (0.5 * W.sum())


def name(k):
    a, b = cands[k]; return cols[a] if b is None else f"{cols[a]} vs {cols[b]}"


class JointNull:
    def __init__(self, GPn, Z):
        self.GPn = GPn; Zc = Z - Z.mean(0)
        U, s, Vt = np.linalg.svd(Zc, full_matrices=False)
        self.Y, self.Vt, self.mu = U * s, Vt, Z.mean(0)
        self.pars = [GPn.fit(self.Y[:, k]) if s[k] > 1e-6 else None for k in range(len(s))]

    def draw(self, rng):
        Y = np.column_stack([np.zeros(self.GPn.n) if q is None else q["sd"] * self.GPn.simulate(q, 1, rng)[:, 0] for q in self.pars])
        return Y @ self.Vt + self.mu


if __name__ == "__main__":
    GPn = MultiScaleNull(g.geometry, I, J, W)
    sc = score(Z)
    lb = pd.read_csv(f"{SYD}/q_{mode}/leaderboard.csv")
    rng = np.random.default_rng(31)
    JN = JointNull(GPn, Z)
    null_best = np.array([score(JN.draw(rng)).min() for _ in range(B)])
    out = []
    for nm in lb.line.head(15):
        k = [i for i in range(len(cands)) if name(i) == nm][0]
        out.append(dict(mode=mode, line=nm, score=round(sc[k], 3), p_search_msr=lb.set_index("line").p_chance[nm],
                        p_search_landscape=(1 + (null_best <= sc[k]).sum()) / (B + 1)))
        print(out[-1], flush=True)
    print("null best: median", np.median(null_best).round(3), "5%", np.quantile(null_best, 0.05).round(3), "observed best", sc.min().round(3))
    pd.DataFrame(out).to_csv(f"{SYD}/search_landscape_{mode}.csv", index=False)
    np.save(f"{SYD}/search_nullbest_{mode}.npy", null_best)
