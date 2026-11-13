"""Geostatistical ('random landscape') null for the line test.

H0: the map is a stationary Gaussian random field in REAL space, seen through the real
areas (each area's value is the average of the field over the area), plus independent
area-level noise.  Fit the field's length scale, covariance shape and noise share by
maximum likelihood on the rank-normal map, then simulate maps from the fitted model and
compare border lengths.  Unlike graph-based MSR this respects real distances and the
fact that large outer areas average away more detail than small inner ones."""
import numpy as np
from scipy.linalg import cho_factor, cho_solve, eigh
from scipy.stats import norm, rankdata
from shapely import contains_xy


def area_points(geom, m=25, cell=200.0, seed=0):
    """m points spread over each polygon (regular grid, subsampled) -> list of (m_i, 2)."""
    rng = np.random.default_rng(seed); out = []
    for g in geom:
        x0, y0, x1, y1 = g.bounds
        c = cell
        while True:
            gx, gy = np.meshgrid(np.arange(x0 + c / 2, x1, c), np.arange(y0 + c / 2, y1, c))
            inside = contains_xy(g, gx, gy)
            if inside.sum() >= m or c < 20: break
            c /= 2
        pts = np.column_stack([gx[inside], gy[inside]])
        if len(pts) == 0: p = g.representative_point(); pts = np.array([[p.x, p.y]])
        if len(pts) > m: pts = pts[rng.choice(len(pts), m, replace=False)]
        out.append(pts)
    return out


class GPNull:
    SHAPES = ("gauss", "matern32", "exp")

    def __init__(self, geom, I, J, W, ells_km=None, m=25, shapes=None):
        if shapes: self.SHAPES = shapes
        self.I, self.J, self.W = np.asarray(I), np.asarray(J), np.asarray(W, float)
        P = area_points(geom, m)
        self.n = len(P)
        self.pts = np.vstack(P); self.own = np.repeat(np.arange(self.n), [len(p) for p in P])
        self.cnt = np.bincount(self.own).astype(float)
        self.ells = np.geomspace(0.5, 60, 18) if ells_km is None else np.asarray(ells_km)
        keys = [(sh, e) for sh in self.SHAPES for e in self.ells]
        acc = {k: np.zeros((self.n, self.n)) for k in keys}
        npt = len(self.pts); w = 1 / self.cnt[self.own]
        from scipy import sparse
        Avg = sparse.csr_matrix((w, (self.own, np.arange(npt))), shape=(self.n, npt))
        for s0 in range(0, npt, 1500):                       # chunked: area-average of the kernel
            P = self.pts[s0:s0 + 1500]
            Dc = np.sqrt(((P[:, None, :] - self.pts[None, :, :]) ** 2).sum(-1))
            oc = self.own[s0:s0 + 1500]
            for (sh, e) in keys:
                r = Dc / (e * 1000)
                K = np.exp(-r ** 2 / 2) if sh == "gauss" else (1 + np.sqrt(3) * r) * np.exp(-np.sqrt(3) * r) if sh == "matern32" else np.exp(-r)
                acc[sh, e] += Avg[:, s0:s0 + 1500] @ (Avg @ K.T).T
        self.cov = {k: C / np.mean(np.diag(C)) for k, C in acc.items()}
        self.eig = {k: eigh(C) for k, C in self.cov.items()}

    @staticmethod
    def rn(x): return norm.ppf((rankdata(x) - 0.5) / len(x))

    def cut(self, F):
        F = F if F.ndim == 2 else F[:, None]
        S = F > np.median(F, 0)
        return ((S[self.I] != S[self.J]) * self.W[:, None]).sum(0) / (0.5 * self.W.sum())

    def fit(self, f):
        """profile likelihood over shape, ell and noise share tau (C = (1-tau) K + tau I, scaled)."""
        f = (f - f.mean()) / f.std(); n = len(f); best = None
        for (shape, ell), (w, U) in self.eig.items():
            w = np.clip(w, 0, None); c2 = (U.T @ f) ** 2
            for tau in np.linspace(0, 0.95, 20):
                lam = (1 - tau) * w + tau + 1e-9
                s2 = (c2 / lam).mean()                         # profiled variance
                nll = 0.5 * (n * np.log(s2) + np.log(lam).sum())
                if best is None or nll < best[0]: best = (nll, shape, ell, tau)
        return dict(shape=best[1], ell=best[2], tau=best[3])

    def simulate(self, par, B, rng):
        K = self.cov[par["shape"], par["ell"]]
        C = (1 - par["tau"]) * K + par["tau"] * np.eye(self.n)
        w, U = eigh(C); L = U * np.sqrt(np.clip(w, 0, None))
        return L @ rng.standard_normal((self.n, B))

    def test(self, f, B=499, seed=0, par=None):
        rng = np.random.default_rng(seed)
        par = self.fit(f) if par is None else par
        F = self.simulate(par, B, rng)
        F = np.apply_along_axis(self.rn, 0, F)
        obs = self.cut(self.rn(f))[0]; null = self.cut(F)
        return (1 + (null <= obs).sum()) / (B + 1), obs, null.mean(), par


class MultiScaleNull(GPNull):
    """Random-landscape null with a FLEXIBLE spectrum: the field is a sum of independent
    smooth fields at several length scales (Matern 3/2 at 0.7 ... 50 km) plus area noise,
    with the amount of each scale fitted by maximum likelihood.  This is the real-space
    analogue of what MSR tries to do (keep the spectrum, lose the layout), but it respects
    distances and area sizes, and the spectrum is estimated smoothly rather than per block."""
    SCALES = (0.7, 1.5, 3.0, 6.0, 12.0, 25.0, 50.0)

    def __init__(self, geom, I, J, W, m=25):
        super().__init__(geom, I, J, W, ells_km=self.SCALES, m=m, shapes=("matern32",))
        self.Ks = [self.cov["matern32", e] for e in self.SCALES] + [np.eye(self.n)]

    def fit(self, f, known_var=None, standardise=True):
        """known_var: per-area sampling variance of f that is NOT part of the landscape
        (e.g. binomial noise of an empirical logit). It is included in the likelihood but
        left out when simulating the latent landscape."""
        from scipy.optimize import minimize
        from scipy.linalg import cho_factor, cho_solve
        mu = f.mean(); sd = f.std() if standardise else 1.0
        f = (f - mu) / sd; Ks = self.Ks
        Dk = np.zeros(self.n) if known_var is None else np.asarray(known_var) / sd ** 2
        def nll(th):
            a = np.exp(th); C = sum(ai * K for ai, K in zip(a, Ks)) + np.diag(Dk) + 1e-8 * np.eye(self.n)
            try: cf = cho_factor(C, lower=True)
            except np.linalg.LinAlgError: return 1e10, np.zeros_like(th)
            al = cho_solve(cf, f); Ci = cho_solve(cf, np.eye(self.n))
            v = 2 * np.log(np.diag(cf[0])).sum() * 0.5 + 0.5 * f @ al
            g = np.array([ai * 0.5 * ((Ci * K).sum() - al @ K @ al) for ai, K in zip(a, Ks)])
            return v, g
        best = None
        for start in [np.full(len(Ks), np.log(1 / len(Ks))), np.r_[np.full(len(Ks) - 1, -4.0), np.log(0.9)], np.r_[-4, -4, -4, -2, -1, 0, -1, -2.0]]:
            r = minimize(nll, start, jac=True, method="L-BFGS-B", bounds=[(-12, 3)] * len(Ks))
            if best is None or r.fun < best.fun: best = r
        a = np.exp(best.x)
        return dict(weights=a, mu=mu, sd=sd, ell=float(np.exp((a[:-1] * np.log(self.SCALES)).sum() / a[:-1].sum())), tau=float(a[-1] / a.sum()))

    def simulate(self, par, B, rng):
        C = sum(ai * K for ai, K in zip(par["weights"], self.Ks))
        w, U = eigh(C); L = U * np.sqrt(np.clip(w, 0, None))
        return L @ rng.standard_normal((self.n, B))


def calibrated_map_test(GPn, f, B=999, R=100, Bin=199, seed=0):
    """landscape line test on a finished map + double-bootstrap calibration (refit inside)."""
    rng = np.random.default_rng(seed)
    p_raw, obs, nm, par = GPn.test(f, B, seed=seed)
    ps = np.array([GPn.test(GPn.simulate(par, 1, rng)[:, 0], Bin, seed=1000 + r)[0] for r in range(R)])
    return dict(p_raw=p_raw, p_cal=(1 + (ps <= p_raw).sum()) / (R + 1), size=(ps <= 0.05).mean(), cleanness=obs, null_mean=nm,
                ell_km=round(par["ell"], 1), noise_share=round(par["tau"], 2))


def step_test(GPn, f, B=499, seed=0, par=None):
    """'Is there an edge on top of the landscape?'  Fit the landscape, then measure how much a
    jump along the line (the median split) improves a generalised-least-squares fit that
    already allows for the landscape (chi-square-like t^2).  Null: maps simulated from the
    fitted landscape, each with its own median split, scored the same way."""
    rng = np.random.default_rng(seed)
    f = (f - f.mean()) / f.std()
    par = GPn.fit(f) if par is None else par
    C = sum(a * K for a, K in zip(par["weights"], GPn.Ks)) + 1e-8 * np.eye(GPn.n)
    Ci = np.linalg.inv(C); one = np.ones(GPn.n)
    def stat(F):
        F = F if F.ndim == 2 else F[:, None]
        S = (F > np.median(F, 0)).astype(float) - 0.5
        X1 = Ci @ one; out = np.empty(F.shape[1])
        for b in range(F.shape[1]):
            X = np.column_stack([one, S[:, b]]); A = X.T @ Ci @ X; beta = np.linalg.solve(A, X.T @ Ci @ F[:, b])
            out[b] = beta[1] ** 2 / np.linalg.inv(A)[1, 1]
        return out
    obs = stat(f)[0]; null = stat(GPn.simulate(par, B, rng))
    return (1 + (null >= obs).sum()) / (B + 1), obs, par


def edge_stat(GPn, par):
    C = sum(a * K for a, K in zip(par["weights"], GPn.Ks)) + 1e-8 * np.eye(GPn.n)
    Ci = np.linalg.inv(C); one = np.ones(GPn.n)
    def stat(F):
        F = F if F.ndim == 2 else F[:, None]
        F = (F - F.mean(0)) / F.std(0)
        S = (F > np.median(F, 0)).astype(float) - 0.5
        out = np.empty(F.shape[1])
        for b in range(F.shape[1]):
            X = np.column_stack([one, S[:, b]]); A = X.T @ Ci @ X; beta = np.linalg.solve(A, X.T @ Ci @ F[:, b])
            out[b] = beta[1] ** 2 / np.linalg.inv(A)[1, 1]
        return out
    return stat


def calibrated_edge_map(GPn, f, B=499, R=60, Bin=199, seed=0):
    rng = np.random.default_rng(seed)
    p_raw, obs, par = step_test(GPn, f, B, seed=seed)
    ps = np.array([step_test(GPn, GPn.simulate(par, 1, rng)[:, 0], Bin, seed=1000 + r)[0] for r in range(R)])
    return dict(p_raw=p_raw, p_cal=(1 + (ps <= p_raw).sum()) / (R + 1), size=(ps <= 0.05).mean(), edge=obs, ell_km=round(par["ell"], 1))
