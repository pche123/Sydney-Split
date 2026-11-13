import os, sys; _H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [_H, os.path.dirname(_H), os.path.join(os.path.dirname(_H), "..")]  # experiments, repo root
from paths import SYD, TOK, RAW  # noqa: E402
"""Data-level nulls for the CLEANNESS test of venue lines.

perm : relabel pooled venues completely at random (H0: type has no geography at all)
dmsr : 'data-level MSR'. Estimate each area's underlying A-share (shrunk logit, nearest-area
       assignment), randomise that surface with MSR (same smoothness, scrambled layout),
       draw venue labels from it, and push them through the app's counting + formula.
       H0: the type preference surface is no more line-like than a random surface with the
       same smoothness. This is the venue-data version of the original test."""
import sys, numpy as np, pandas as pd
from scipy.spatial import cKDTree
from venue_null import tokyo, sydney
def clean(G, F):
    S = F > np.median(F, 0); w = G.W[:, None]
    return ((S[G.I] != S[G.J]) * w).sum(0) / (0.5 * G.W.sum())

class CleanNull:
    def __init__(self, G, L):
        self.G, self.L = G, L
        self.area = cKDTree(G.rep).query(L.xy)[1]
        self.N = np.bincount(self.area, minlength=G.n).astype(float)
    def surface(self, y, k=5.0):
        a = np.bincount(self.area, weights=y, minlength=self.G.n); pbar = y.mean()
        p = (a + k * pbar) / (self.N + k); return np.log(p / (1 - p))
    def draws(self, y, B, kind, rng):
        if kind == "perm":
            return np.column_stack([rng.permutation(y) for _ in range(B)])
        lg = self.surface(y); mu, sd = lg.mean(), lg.std()
        R = self.G.msr(lg, B) * sd + mu
        P = 1 / (1 + np.exp(-R[self.area]))                      # venues x B
        return (rng.random(P.shape) < P).astype(float)
    def test(self, B=999, kind="dmsr", y=None, seed=0):
        rng = np.random.default_rng(seed); y = self.L.y if y is None else y
        f = self.L.field(y) + 1e-9 * rng.standard_normal(self.G.n); obs = clean(self.G, f[:, None])[0]
        Y = self.draws(y, B, kind, rng)
        F = np.column_stack([self.L.field(Y[:, b]) for b in range(B)]) + 1e-9 * rng.standard_normal((self.G.n, B))
        null = clean(self.G, F)
        return (1 + (null <= obs).sum()) / (B + 1), obs, null.mean()

if __name__ == "__main__":
    mode = sys.argv[1]
    rng = np.random.default_rng(9); rows = []
    for city, fn in [("Tokyo", tokyo), ("Sydney", sydney)]:
        G, VL = fn()
        for lid, L in VL.items():
            C = CleanNull(G, L)
            if mode == "size":
                rej = 0
                for r in range(60):
                    y = (rng.random(len(L.y)) < L.y.mean()).astype(float)
                    rej += C.test(99, "dmsr", y=y, seed=r)[0] <= 0.05
                print(city, lid, "dmsr false-positive rate (no geography):", round(rej / 60, 2), flush=True)
            else:
                pp, obs, _ = C.test(999, "perm"); pd_, _, nm = C.test(999, "dmsr")
                rows.append(dict(city=city, id=lid, cleanness=round(obs, 3), dmsr_null_mean=round(nm, 3), p_perm=pp, p_dmsr=pd_)); print(rows[-1], flush=True)
    if rows: pd.DataFrame(rows).to_csv("venue_cleanness.csv", index=False)
