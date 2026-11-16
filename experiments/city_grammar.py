"""Does a city have a "grammar" beyond smoothness and correlation?

    python experiments/city_grammar.py <out folder> city:app.json:workfolder [city:app.json:workfolder ...]

Alphabet: each area gets a 4-letter word, its side on each family axis (Work and class, Inner city, Age, Night out).
An axis is the first principal component of the family's line scores in that city (Age: the Grey Line), signed so
the first listed line loads positively; the side is above or below the city's median.
Grammar strength: mutual information between the words of neighbouring areas, weighted by shared border length.
Baseline (GRAMMAR_NULL): "mixed", 99 simulated cities in which every line gets its own fitted multi-scale landscape and
the lines are mixed to their real correlation matrix (as for the rules); or "factor", the stronger one, in which the
lines' principal components each get their own landscape and are recombined, so lines that share a broad gradient
share it in the simulations too. The grammar is real only if it beats the baseline.
Shared grammar: the excess of each word pair over the baseline, compared between cities (correlation).
"""
import json, os, sys
import numpy as np, pandas as pd, geopandas as gpd
from scipy.stats import norm, rankdata
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.join(HERE, ".."), os.path.join(HERE, "..", "pipeline")]
from linetests.landscape import MultiScaleNull
from cities import CITIES

FAM = {"W": ["the-hi-vis-line", "the-degree-line", "the-laptop-vs-hard-hat-line", "the-factory-line"],
       "I": ["flats-vs-houses", "the-renters-line", "the-living-alone-line", "train-vs-car", "the-no-car-line", "the-bicycle-line"],
       "A": ["the-grey-line"], "N": ["coffee-vs-alcohol", "drink-out-vs-drink-in"]}
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True); NULL = 99
KIND = os.environ.get("GRAMMAR_NULL", "mixed")   # mixed: same-spot correlation only; factor: shared spatial structure kept
rn = lambda v: norm.ppf((rankdata(v) - 0.5) / len(v))


def axes(X, ids):
    """areas x lines (rank-normal) -> areas x 4 family axes (or fewer if a family is missing)."""
    out, names = [], []
    for k, ls in FAM.items():
        cols = [ids.index(l) for l in ls if l in ids]
        if not cols: continue
        Z = X[:, cols]
        if Z.shape[1] == 1: a = Z[:, 0]
        else:
            Zc = Z - Z.mean(0); u, s, vt = np.linalg.svd(Zc, full_matrices=False); v = vt[0] * np.sign(vt[0][0] or 1); a = Zc @ v
        out.append(a); names.append(k)
    return np.column_stack(out), names


def words(A):
    S = (A > np.median(A, 0)).astype(int); return S @ (2 ** np.arange(S.shape[1]))


def pair_table(w, I, J, W, K):
    T = np.zeros((K, K)); np.add.at(T, (w[I], w[J]), W); np.add.at(T, (w[J], w[I]), W); return T / T.sum()


def mi(T):
    p = T.sum(1); q = T.sum(0); nz = T > 0; return float((T[nz] * np.log(T[nz] / np.outer(p, q)[nz])).sum())


rows, excess = [], {}
rng = np.random.default_rng(3)
for spec in sys.argv[2:]:
    city, appf, wk = spec.split(":")
    d = json.load(open(appf)); C = CITIES[city]
    F = {l["id"]: np.asarray(l["f"], float) for l in d["lines"] if l.get("f") and any(l["id"] in v for v in FAM.values())}
    ids = sorted(F)
    if len(ids) < 4: print("skip", city); continue
    X = np.column_stack([rn(F[i]) for i in ids])
    G = gpd.read_file(f"{wk}/areas.gpkg").to_crs(C["crs"]).reset_index(drop=True)
    z = np.load(f"{wk}/fields.npz"); I, J, W = z["I"], z["J"], z["W"]
    if len(G) != X.shape[0]: print("skip (area mismatch)", city, len(G), X.shape[0]); continue
    A, names = axes(X, ids); K = 2 ** len(names)
    w = words(A); T = pair_table(w, I, J, W, K); obs = mi(T)
    MS = MultiScaleNull(G.geometry, I, J, W, m=9 if len(G) > 600 else 25)
    if KIND == "factor":   # lines = uncorrelated factors (principal components) x loadings; each factor keeps its own smoothness
        Xc = X - X.mean(0); U, sv, Vt = np.linalg.svd(Xc, full_matrices=False); Fa = U * sv
        sims = []
        for k in range(Fa.shape[1]):
            par = MS.fit(Fa[:, k]); S_ = MS.simulate(par, NULL, rng); sims.append((S_ - S_.mean(0)) / S_.std(0) * Fa[:, k].std())
        S = np.stack(sims, 2)                                   # areas x NULL x factors
        make = lambda b: S[:, b, :] @ Vt
    else:                  # independent smooth field per line, mixed to the observed correlation at the same spot
        R = np.corrcoef(X.T); Lc = np.linalg.cholesky(R + 1e-9 * np.eye(len(ids)))
        sims = []
        for k in range(len(ids)):
            par = MS.fit(X[:, k]); S_ = MS.simulate(par, NULL, rng); sims.append((S_ - S_.mean(0)) / S_.std(0))
        S = np.stack(sims, 2)
        make = lambda b: np.linalg.solve(np.linalg.cholesky(np.corrcoef(S[:, b, :].T) + 1e-9 * np.eye(len(ids))), S[:, b, :].T).T @ Lc.T
    nulls, Ts = [], []
    for b in range(NULL):
        Ab, _ = axes(make(b), ids); Tb = pair_table(words(Ab), I, J, W, K); nulls.append(mi(Tb)); Ts.append(Tb)
    nulls = np.array(nulls); Tn = np.mean(Ts, 0)
    p = (1 + (nulls >= obs).sum()) / (NULL + 1); zsc = (obs - nulls.mean()) / nulls.std()
    rows.append(dict(city=city, country=C["country"], areas=len(G), letters="".join(names), mi=obs, null_mean=nulls.mean(), null_sd=nulls.std(), z=zsc, p=p))
    if len(names) == 4: excess[city] = (T - Tn)[np.triu_indices(K)]
    print(f"{city:13s} {''.join(names)}  MI {obs:.3f} vs smooth+correlated {nulls.mean():.3f} ± {nulls.std():.3f}  z = {zsc:+.2f}  p = {p:.3f}", flush=True)

D = pd.DataFrame(rows); D.to_csv(f"{OUT}/grammar_strength.csv", index=False)
cs = sorted(excess)
if len(cs) > 2:
    M = pd.DataFrame(np.corrcoef(np.vstack([excess[c] for c in cs])), index=cs, columns=cs); M.to_csv(f"{OUT}/grammar_similarity.csv")
    ct = {c: CITIES[c]["country"] for c in cs}
    within = [M.loc[a, b] for i, a in enumerate(cs) for b in cs[i + 1:] if ct[a] == ct[b]]
    across = [M.loc[a, b] for i, a in enumerate(cs) for b in cs[i + 1:] if ct[a] != ct[b]]
    print(f"\nshared grammar: excess word-pair patterns correlate r = {np.mean(within):.2f} within a country, {np.mean(across):.2f} across countries")
