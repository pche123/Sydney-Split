import os, sys; _H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [_H, os.path.dirname(_H), os.path.join(os.path.dirname(_H), "..")]  # experiments, repo root
from paths import SYD, TOK, RAW  # noqa: E402
"""Front vs slope: is a line a sharp edge, or just the middle of a smooth hill?

Everything runs on an area graph (n areas, edges I-J with weights W) and a field f
(one number per area, e.g. rank-normal "cafes minus fast food").  The line is the
median split of f.  The cleanness test already asks "is the border short?"; these
statistics ask a different question: "is the change concentrated AT the border?"

Null model: Moran spectral randomisation (MSR).  We express f in the eigenbasis of
M A M, then rotate the coefficients randomly inside blocks of neighbouring
eigenvectors.  That keeps how much smooth vs rough variation the field has (its
spatial spectrum) but scrambles the phases, i.e. it destroys any alignment of the
rough parts into one coherent edge.  A sharp front is exactly such an alignment, so
every statistic below is computed the same way on the real field and on each null
field (median split recomputed each time) and the p-value is the usual rank one.

Statistics (bigger = sharper):
  JC     jump concentration: mean |df| on cut edges / mean |df| on all edges
  HOYER  gradient sparsity of the edge differences (1 = all change on one edge)
  STEP   partial R^2 of the side indicator after the k smoothest eigenvectors
  RD     regression discontinuity at the border: jump c in f = a + b d + c [A] (+ slope change),
         using areas within h hops of the border, standardised by its OLS s.e.
  OMNI   min-p across the four, calibrated against the same null draws
"""
import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import dijkstra
from scipy.stats import norm, rankdata


class Graph:
    def __init__(self, n, I, J, W, k_smooth=10, block=12, seed=0, rep=None, rd_km=4.0):
        self.rep, self.rd_km = (None if rep is None else np.asarray(rep, float)), rd_km
        self.n, self.I, self.J = n, np.asarray(I), np.asarray(J)
        self.W = np.asarray(W, float)
        A = sparse.coo_matrix((np.r_[self.W, self.W], (np.r_[self.I, self.J], np.r_[self.J, self.I])), shape=(n, n)).toarray()
        M = np.eye(n) - 1.0 / n
        lam, V = np.linalg.eigh(M @ A @ M)
        order = np.argsort(-lam)                     # smooth (high Moran) -> rough
        V = V[:, order]
        # drop the constant direction (eigenvalue ~0 with all-equal entries)
        const = np.abs(V.T @ np.ones(n) / np.sqrt(n)) > 0.99
        self.V = V[:, ~const]
        self.block = block
        self.Q = np.linalg.qr(np.column_stack([np.ones(n), self.V[:, :k_smooth]]))[0]
        self.H = sparse.csr_matrix((np.ones(2 * len(self.I)), (np.r_[self.I, self.J], np.r_[self.J, self.I])), shape=(n, n))
        self.rng = np.random.default_rng(seed)

    # ---- null fields --------------------------------------------------------
    def msr(self, f, B, keep=0):
        """keep = number of smoothest eigenvectors held fixed (0 = classic MSR).
        keep > 0 is the 'conditional' null: the large-scale trend is kept exactly and only
        the finer detail is scrambled, so a plain ramp or hill counts as a slope."""
        f = (f - f.mean()) / f.std()
        c = self.V.T @ f
        out = np.empty((self.n, B))
        m = len(c)
        for b in range(B):
            cb = c.copy()
            for s in range(keep, m, self.block):
                e = min(m, s + self.block)
                Z = self.rng.standard_normal((e - s, e - s))
                Qr, R = np.linalg.qr(Z)
                Qr = Qr * np.sign(np.diag(R))
                cb[s:e] = Qr @ c[s:e]
            out[:, b] = self.V @ cb
        return out

    # ---- statistics (vectorised over columns of F) ----------------------------
    def stats(self, F, h=3):
        F = np.atleast_2d(F.T).T if F.ndim == 1 else F
        F = (F - F.mean(0)) / F.std(0)
        S = F > np.median(F, 0)
        D = np.abs(F[self.I] - F[self.J])
        w = self.W[:, None]
        cut = S[self.I] != S[self.J]
        jc = ((D * w * cut).sum(0) / (w * cut).sum(0)) / ((D * w).sum(0) / w.sum())
        l1, l2, m = D.sum(0), np.sqrt((D ** 2).sum(0)), D.shape[0]
        hoyer = (np.sqrt(m) - l1 / (l2 + 1e-12)) / (np.sqrt(m) - 1)
        Rf = F - self.Q @ (self.Q.T @ F)
        Rs = S - self.Q @ (self.Q.T @ S.astype(float))
        step = (Rf * Rs).sum(0) ** 2 / ((Rf ** 2).sum(0) * (Rs ** 2).sum(0) + 1e-12)
        rd = np.array([self._rd(F[:, b], S[:, b], cut[:, b], h) for b in range(F.shape[1])])
        return np.vstack([jc, hoyer, step, rd])

    def _rd(self, f, s, cut, h):
        if self.rep is not None:                       # metric version: signed km to the other side
            from scipy.spatial import cKDTree
            dA = cKDTree(self.rep[~s]).query(self.rep[s])[0]
            dB = cKDTree(self.rep[s]).query(self.rep[~s])[0]
            sd = np.empty(len(f)); sd[s] = dA / 2000; sd[~s] = -dB / 2000
            keep = np.abs(sd) <= self.rd_km
            x, y, a = sd[keep], f[keep], s[keep].astype(float)
            X = np.column_stack([np.ones_like(x), x, a, a * x, x ** 2, a * x ** 2])
            beta, *_ = np.linalg.lstsq(X, y, rcond=None)
            r = y - X @ beta
            cov = (r @ r / max(len(y) - 6, 1)) * np.linalg.pinv(X.T @ X)
            return beta[2] / np.sqrt(cov[2, 2] + 1e-12)
        border = np.unique(np.r_[self.I[cut], self.J[cut]])
        d = dijkstra(self.H, indices=border, unweighted=True, min_only=True)
        # border areas are at hop 0 on their own side; signed distance: A side +, B side -
        sd = np.where(s, d + 0.5, -(d + 0.5))
        keep = d <= h
        x, y, a = sd[keep], f[keep], s[keep].astype(float)
        X = np.column_stack([np.ones_like(x), x, a, a * x])
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        r = y - X @ beta
        dof = max(len(y) - 4, 1)
        cov = (r @ r / dof) * np.linalg.pinv(X.T @ X)
        return beta[2] / np.sqrt(cov[2, 2] + 1e-12)

    # ---- test -----------------------------------------------------------------
    def test(self, f, B=499, h=3, keep=0):
        obs = self.stats(f[:, None], h)[:, 0]
        null = self.stats(self.msr(f, B, keep), h)
        p = (1 + (null >= obs[:, None]).sum(1)) / (B + 1)
        # min-p omnibus: each null draw's own p-values from the remaining draws (rank based)
        rk = (B - rankdata(null, axis=1, method="max") + 1)       # how many null >= each null value
        pn = (1 + rk) / (B + 1)
        omni = (1 + (pn.min(0) <= p.min()).sum()) / (B + 1)
        z = (obs - null.mean(1)) / null.std(1)
        return dict(p=p, omni=omni, z=z, obs=obs)


def rank_normal(x):
    x = np.asarray(x, float).copy()
    x[~np.isfinite(x)] = np.nanmedian(x)
    return norm.ppf((rankdata(x) - 0.5) / len(x))


def width_km(f, s, rep, I, J):
    """Descriptive: how wide is the transition?  Fit f ~ a + b*tanh(d / w) over the
    signed distance d (km) from each area to the nearest area on the other side,
    and report the w that fits best (grid search).  Small w = a cliff, large = a ramp."""
    from scipy.spatial import cKDTree
    f = (f - f.mean()) / f.std()
    tA, tB = cKDTree(rep[s]), cKDTree(rep[~s])
    d = np.where(s, tB.query(rep)[0], -tA.query(rep)[0]) / 2000.0   # half-gap, km (rep in metres)
    best = None
    for w in np.geomspace(0.25, 40, 40):
        X = np.column_stack([np.ones_like(d), np.tanh(d / w)])
        beta, res, *_ = np.linalg.lstsq(X, f, rcond=None)
        sse = ((f - X @ beta) ** 2).sum()
        if best is None or sse < best[1]: best = (w, sse)
    return best[0]


class SmoothNull:
    """Parametric-bootstrap 'slope' null that respects real distances.

    H0: f = g(x, y) + e, where g is smooth at length scale ell (Gaussian-kernel ridge on
    area centroids, penalty chosen by GCV) and e is spatially correlated noise.  Null
    fields are g_hat + e*, with e* an MSR rotation of the residuals.  Because the
    kernel cannot bend faster than ~ell, a change much sharper than ell ends up in the
    residuals, where MSR scrambles it; a ramp or hill stays in g_hat and is reproduced
    by every null field, so it is (correctly) not called a front.  ell is the knob that
    defines 'sharp': 'this change happens over less than ~ell km'."""
    def __init__(self, G, rep, ell_m):
        self.G = G
        d2 = ((rep[:, None, :] - rep[None, :, :]) ** 2).sum(-1)
        K = np.exp(-d2 / (2 * ell_m ** 2))
        self.lam, self.U = np.linalg.eigh(K)
        self.lam = np.clip(self.lam, 0, None)

    def fit(self, f):
        c = self.U.T @ f
        n = len(f)
        best = None
        for a in np.geomspace(1e-3, 1e3, 40):          # GCV over the ridge penalty
            sh = self.lam / (self.lam + a)
            g = self.U @ (sh * c)
            gcv = n * ((f - g) ** 2).sum() / (n - sh.sum()) ** 2
            if best is None or gcv < best[0]: best = (gcv, g)
        return best[1]

    def test(self, f, B=499, h=3):
        G = self.G
        f = (f - f.mean()) / f.std()
        g = self.fit(f)
        e = f - g
        sd = e.std()
        E = G.msr(e, B) * sd                             # msr standardises; put the scale back
        null = G.stats(g[:, None] + E, h)
        obs = G.stats(f[:, None], h)[:, 0]
        p = (1 + (null >= obs[:, None]).sum(1)) / (B + 1)
        use = [0, 2, 3]                                  # JC, STEP, RD (HOYER is global, not about this line)
        rk = (B - rankdata(null[use], axis=1, method="max") + 1)
        pn = (1 + rk) / (B + 1)
        omni = (1 + (pn.min(0) <= p[use].min()).sum()) / (B + 1)
        z = (obs - null.mean(1)) / null.std(1)
        return dict(p=p, omni=omni, z=z, obs=obs, r2=1 - e.var() / f.var(), nullmean=null.mean(1))
