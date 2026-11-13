"""Record-level line tests: simulate the records, not the map.

Every record-based line is a `Line` with four pieces:
  * records   what was observed (each venue's type, each area's licence count, ...);
  * estimate  records -> per-area latent surface(s) and their sampling variance;
  * simulate  surfaces -> fresh records;
  * recipe    records -> the line's map, using the app's own formula and counting rule.

The recommended test is `landscape_calibrated` (is it a line?) and `calibrated_edge_data`
(is it a cliff?): each null world draws a new latent landscape from a multi-scale model
fitted to the surface (landscape.MultiScaleNull), simulates records, and rebuilds the map,
with a double bootstrap on top.  `dmsr_test` (rotating the estimated surface with MSR)
is kept for comparison only: it is miscalibrated (see FINDINGS.md)."""
import numpy as np, pandas as pd
from scipy import sparse
from scipy.spatial import cKDTree
from scipy.stats import norm, rankdata
from .msr import LineTest


def rz(v):
    v = pd.Series(v).fillna(pd.Series(v).median()).values
    return norm.ppf((rankdata(v) - 0.5) / len(v))


class Line:
    """records : the data (whatever the simulator produces, e.g. a 0/1 label per venue)
    estimate(records) -> list of area surfaces
    simulate(surfaces, rng) -> records
    recipe(records) -> the line's map (the app's own formula)"""
    def __init__(self, name, records, estimate, simulate, recipe):
        self.name, self.records, self.estimate, self.simulate, self.recipe = name, records, estimate, simulate, recipe
        est = estimate(records)
        self.surfaces = [e[0] for e in est]; self.svar = [e[1] for e in est]; self.field = recipe(records)
    def sim(self, S, rng): return self.recipe(self.simulate(S, rng))
    def remake(self, records):
        return Line(self.name, records, self.estimate, self.simulate, self.recipe)


def dmsr_test(T, L, B=999, seed=0, return_null=False):
    rng = np.random.default_rng(seed)
    obs = T.cut(L.field + 1e-9 * rng.standard_normal(T.n))[0]
    null = np.empty(B)
    for b, Rs in enumerate(T.rotations(B)):
        S = [T.rotate(s, Rs) * s.std() + s.mean() for s in L.surfaces]
        f = L.sim(S, rng)
        null[b] = T.cut(f + 1e-9 * rng.standard_normal(T.n))[0]
    p = (1 + (null <= obs).sum()) / (B + 1)
    return (p, obs, null) if return_null else (p, obs, null.mean())


# ---------------------------------------------------------------- building blocks
def logit_surface(area, y, n, k=None):
    """empirical logit of the A-share per area (Haldane-Anscombe +0.5) and its textbook
    sampling variance 1/(a+.5) + 1/(b+.5); an area with no records gets variance 4 (no information)."""
    a = np.bincount(area, weights=y, minlength=n); N = np.bincount(area, minlength=n); b = N - a
    return np.log((a + 0.5) / (b + 0.5)), 1 / (a + 0.5) + 1 / (b + 0.5)


def lograte_surface(area, w, expo, n, k=None):
    """log rate per unit exposure with +0.5, sampling variance 1/(c+.5)."""
    c = np.bincount(area, weights=w, minlength=n)
    return np.log((c + 0.5) / np.maximum(expo, 1.0)), 1 / (c + 0.5)


def two_type_line(name, area, M, y, recipe, n):
    """two-type pool: label of each pooled unit ~ Bernoulli(logistic(surface[its area]))."""
    def simulate(S, rng):
        return (rng.random(len(area)) < 1 / (1 + np.exp(-S[0][area]))).astype(float)
    return Line(name, y.astype(float), lambda y: [logit_surface(area, y, n)], simulate, lambda y: recipe(M @ y, M @ (1 - y)))


def size_check(T, L, R=100, B=99, seed=0, nogeo=False):
    """How often does the test say 'line' when the world is a random-layout version of itself
    (one MSR rotation of the estimated surfaces), or has no geography at all (nogeo)?"""
    rng = np.random.default_rng(seed); rej = 0
    for r, Rs in enumerate(T.rotations(R)):
        S = [np.full_like(s, s.mean()) if nogeo else T.rotate(s, Rs) * s.std() + s.mean() for s in L.surfaces]
        L2 = L.remake(L.simulate(S, rng))
        rej += dmsr_test(T, L2, B, seed=r)[0] <= 0.05
    return rej / R


# ---------------------------------------------------------------- landscape (multi-scale GP) data-level null
def landscape_pars(GPn, L):
    return [GPn.fit(s, known_var=v) for s, v in zip(L.surfaces, L.svar)]


def landscape_draw(GPn, L, pars, rng):
    """one set of latent surfaces from the fitted landscapes; surfaces of the same line share
    innovations in proportion to their observed correlation."""
    Z = [GPn.simulate(p, 1, rng)[:, 0] for p in pars]
    if len(Z) == 2:
        r = np.corrcoef(L.surfaces[0], L.surfaces[1])[0, 1]
        Z[1] = r * Z[0] / Z[0].std() * Z[1].std() + np.sqrt(1 - r ** 2) * Z[1]
    return [p["mu"] + p["sd"] * z for p, z in zip(pars, Z)]


def landscape_test(GPn, T, L, B=999, seed=0, pars=None):
    rng = np.random.default_rng(seed)
    pars = landscape_pars(GPn, L) if pars is None else pars
    obs = T.cut(L.field + 1e-9 * rng.standard_normal(T.n))[0]
    null = np.array([T.cut(L.sim(landscape_draw(GPn, L, pars, rng), rng) + 1e-9 * rng.standard_normal(T.n))[0] for _ in range(B)])
    return (1 + (null <= obs).sum()) / (B + 1), obs, null.mean()


def landscape_size(GPn, T, L, R=100, B=99, seed=0):
    """truth = a fresh landscape from the line's own fitted model -> simulate records -> test."""
    rng = np.random.default_rng(seed); pars = landscape_pars(GPn, L); rej = 0
    for r in range(R):
        L2 = L.remake(L.simulate(landscape_draw(GPn, L, pars, rng), rng))
        rej += landscape_test(GPn, T, L2, B, seed=r)[0] <= 0.05
    return rej / R


def landscape_calibrated(GPn, T, L, B=999, R=100, Bin=199, seed=0):
    """raw landscape p, plus a double-bootstrap calibrated p: simulate R worlds from the fitted
    model, run the whole test (refit included) on each, and ask how often a world that has
    no line beyond the landscape gets a p this small.  Also returns the empirical size."""
    rng = np.random.default_rng(seed); pars = landscape_pars(GPn, L)
    p_raw, obs, nm = landscape_test(GPn, T, L, B, seed=seed, pars=pars)
    ps = []
    for r in range(R):
        L2 = L.remake(L.simulate(landscape_draw(GPn, L, pars, rng), rng))
        ps.append(landscape_test(GPn, T, L2, Bin, seed=1000 + r)[0])
    ps = np.array(ps)
    return dict(p_raw=p_raw, p_cal=(1 + (ps <= p_raw).sum()) / (R + 1), size=(ps <= 0.05).mean(),
                cleanness=obs, null_mean=nm, ell_km=[round(q["ell"], 1) for q in pars])


def edge_data_test(GPn, L, B=499, seed=0, lpars=None):
    """edge statistic (jump along the line on top of a landscape) with records-level null:
    covariance fitted once on the line's own map; null maps come from simulated records."""
    from .landscape import edge_stat
    rng = np.random.default_rng(seed)
    mpar = GPn.fit(L.field); stat = edge_stat(GPn, mpar)
    lpars = landscape_pars(GPn, L) if lpars is None else lpars
    obs = stat(L.field)[0]
    null = np.array([stat(L.sim(landscape_draw(GPn, L, lpars, rng), rng))[0] for _ in range(B)])
    return (1 + (null >= obs).sum()) / (B + 1), obs


def calibrated_edge_data(GPn, L, B=499, R=40, Bin=149, seed=0):
    rng = np.random.default_rng(seed); lp = landscape_pars(GPn, L)
    p_raw, obs = edge_data_test(GPn, L, B, seed, lpars=lp)
    ps = []
    for r in range(R):
        L2 = L.remake(L.simulate(landscape_draw(GPn, L, lp, rng), rng))
        ps.append(edge_data_test(GPn, L2, Bin, seed=1000 + r)[0])
    ps = np.array(ps)
    return dict(p_raw=p_raw, p_cal=(1 + (ps <= p_raw).sum()) / (R + 1), size=(ps <= 0.05).mean(), edge=obs)
