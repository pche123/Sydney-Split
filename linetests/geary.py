"""Classical spatial statistics, tested against the fitted landscape null instead of shuffles.

The line statistic is a join count. Split the map at its median into two colours s_i in {0, 1}. Geary's C of that
two-colour map is proportional to the weighted share of borders whose two sides differ:

    C(s) = (n - 1) / (2 W S0) * sum_ij w_ij (s_i - s_j)^2,     (s_i - s_j)^2 = 1[s_i != s_j]

so "border length of the median split" (linetests.msr.LineTest.cut) is Geary's C of the dichotomised map, i.e. the
black-white join count (Cliff & Ord). What this package adds is not the statistic but the null: smooth random
landscapes fitted to the map (linetests.landscape.MultiScaleNull) instead of shuffled or rotated areas.

Contents
  join_count, geary_c, moran_i          global statistics (columns of F are maps)
  local_geary                           per-border contributions w_ij (z_i - z_j)^2
  multivariate_geary                    Anselin (2019): mean of the univariate Gearys of several standardised maps
  null_test                             any global statistic against the fitted landscape null
  sharp_stretches                       which borders of a line change more steeply than the landscape predicts
  shared_border_test                    do several lines (a family) change side on the SAME borders more than smooth
                                        correlated maps would? (share of changing borders where >= 2 lines change)
"""
import numpy as np
from scipy.stats import norm, rankdata


def _rn(F):
    F = np.asarray(F, float); F = F if F.ndim == 2 else F[:, None]
    return np.column_stack([norm.ppf((rankdata(c) - 0.5) / len(c)) for c in F.T])


def join_count(F, I, J, W):
    """weighted share of borders where the median split changes side (= the line statistic). Lower = cleaner line."""
    F = np.asarray(F, float); F = F if F.ndim == 2 else F[:, None]
    S = F > np.median(F, 0)
    return ((S[I] != S[J]) * W[:, None]).sum(0) / W.sum()


def geary_c(F, I, J, W):
    """Geary's C on symmetric border weights (each border listed once). ~1 = no pattern, < 1 = neighbours alike."""
    F = np.asarray(F, float); F = F if F.ndim == 2 else F[:, None]; n = F.shape[0]
    Z = F - F.mean(0)
    num = (W[:, None] * (F[I] - F[J]) ** 2).sum(0) * 2          # both directions
    return (n - 1) * num / (2 * (2 * W.sum()) * (Z ** 2).sum(0))


def moran_i(F, I, J, W):
    F = np.asarray(F, float); F = F if F.ndim == 2 else F[:, None]; n = F.shape[0]
    Z = F - F.mean(0)
    num = 2 * (W[:, None] * Z[I] * Z[J]).sum(0)
    return n * num / ((2 * W.sum()) * (Z ** 2).sum(0))


def local_geary(f, I, J, W):
    """contribution of each border: w_ij (z_i - z_j)^2 on the standardised map."""
    z = (np.asarray(f, float) - np.mean(f)) / np.std(f)
    return W * (z[I] - z[J]) ** 2


def multivariate_geary(Z, I, J, W):
    """Anselin (2019) multivariate Geary: average of the univariate Gearys of the standardised columns. Additive in
    the variables (unlike multivariate Moran), so it can be summed over a family of lines."""
    Z = np.asarray(Z, float); Z = (Z - Z.mean(0)) / Z.std(0)
    return geary_c(Z, I, J, W).mean()


def null_test(GPn, f, stat, B=199, seed=0, lower_is_signal=True, par=None):
    """p-value of stat(f) against maps simulated from the landscape fitted to f (all maps rank-normalised)."""
    rng = np.random.default_rng(seed)
    f = _rn(f)[:, 0]; par = GPn.fit(f) if par is None else par
    Fs = _rn(GPn.simulate(par, B, rng)); obs = stat(f[:, None])[0]; null = stat(Fs)
    hit = (null <= obs) if lower_is_signal else (null >= obs)
    return (1 + hit.sum()) / (B + 1), obs, par


def _bh(p, q):
    p = np.asarray(p); o = np.argsort(p); m = len(p)
    ok = p[o] <= q * (np.arange(1, m + 1) / m); k = np.max(np.where(ok)[0]) + 1 if ok.any() else 0
    out = np.zeros(m, bool); out[o[:k]] = True; return out


def sharp_stretches(GPn, f, I, J, W, B=199, q=0.10, seed=0, par=None):
    """For the borders the line runs along (median split changes side), is the jump across each border bigger than
    the fitted landscape produces on that same border? Per-border p-values from the landscape replays, then
    Benjamini-Hochberg at level q among the line's borders. Returns (edge indices on the line, sharp flags, p)."""
    rng = np.random.default_rng(seed)
    # standardise, do NOT rank: ranking squeezes values together at the median, which is exactly where a line's
    # jump sits, and hides most of it (the line test itself only uses the median split, so ranking is harmless there)
    f = np.asarray(f, float); f = (f - f.mean()) / f.std(); par = GPn.fit(f) if par is None else par
    S = f > np.median(f); on = np.where(S[I] != S[J])[0]
    if len(on) == 0: return on, np.zeros(0, bool), np.zeros(0)
    obs = np.abs(f[I[on]] - f[J[on]])
    Fs = GPn.simulate(par, B, rng); Fs = (Fs - Fs.mean(0)) / Fs.std(0); null = np.abs(Fs[I[on]] - Fs[J[on]])
    p = (1 + (null >= obs[:, None]).sum(1)) / (B + 1)
    return on, _bh(p, q), p


def shared_border_test(Ms, Fs_list, I, J, W, B=199, seed=0):
    """Family test. Fs_list: k maps (areas). Statistic: share of border weight where at least two of the k median
    splits change side together. Null: each map gets its own fitted landscape (Ms: one MultiScaleNull per map, or
    one shared), simulated independently, then mixed to the observed correlation matrix (so the null keeps both
    each map's smoothness and how strongly the maps go together). A small p means the family's borders coincide
    more than their correlation and smoothness explain: one shared line rather than several overlapping slopes."""
    rng = np.random.default_rng(seed)
    X = _rn(np.column_stack(Fs_list)); k = X.shape[1]
    def stat(Xm):
        # of the borders where any of the family's lines changes side, the share (by length) where two or more do
        S = Xm > np.median(Xm, 0); ch = (S[I] != S[J]).sum(1)
        return (W * (ch >= 2)).sum() / max((W * (ch >= 1)).sum(), 1e-12)
    R = np.corrcoef(X.T); L = np.linalg.cholesky(R + 1e-9 * np.eye(k))
    sims = []
    for j in range(k):
        M = Ms[j] if isinstance(Ms, (list, tuple)) else Ms
        sims.append(M.simulate(M.fit(X[:, j]), B, rng))
    obs = stat(X); null = np.empty(B)
    for b in range(B):
        Zb = np.column_stack([s[:, b] for s in sims]); Zb = (Zb - Zb.mean(0)) / Zb.std(0)
        Lb = np.linalg.cholesky(np.corrcoef(Zb.T) + 1e-9 * np.eye(k)); Zb = Zb @ np.linalg.inv(Lb).T @ L.T
        null[b] = stat(Zb)
    return (1 + (null >= obs).sum()) / (B + 1), obs, float(null.mean())
