"""Line test (median split, short border) with the Moran spectral randomisation null.

Canonical choices (used for new cities):
  * eigenvectors of M A M with A the binary adjacency of areas sharing >= 100 m of border
  * the constant direction is removed before rotating
  * Haar-random rotations (QR with sign fix) inside blocks of 12 eigenvectors
The app's original code used the same idea but kept the constant vector in the rotation
and no sign fix; `app_style=True` reproduces that for comparison."""
import numpy as np


class LineTest:
    def __init__(self, n, I, J, W, block=12, app_style=False, seed=0):
        self.n, self.I, self.J, self.W = n, np.asarray(I), np.asarray(J), np.asarray(W, float)
        A = np.zeros((n, n)); A[self.I, self.J] = 1; A[self.J, self.I] = 1
        M = np.eye(n) - 1.0 / n
        lam, V = np.linalg.eigh(M @ A @ M)
        o = np.argsort(-lam); V, lam = V[:, o], lam[o]
        if not app_style:
            keep = np.abs(V.T @ np.ones(n)) / np.sqrt(n) < 0.99
            V, lam = V[:, keep], lam[keep]
        self.V, self.lam, self.block, self.app = V, lam, block, app_style
        self.rng = np.random.default_rng(seed)

    def cut(self, F):
        F = F if F.ndim == 2 else F[:, None]
        S = F > np.median(F, 0)
        return ((S[self.I] != S[self.J]) * self.W[:, None]).sum(0) / (0.5 * self.W.sum())

    def rotations(self, B):
        """Yield B lists of block rotation matrices (shared so several fields can be rotated jointly)."""
        m = self.V.shape[1]
        for _ in range(B):
            Rs = []
            for s in range(0, m, self.block):
                k = min(m, s + self.block) - s
                Q, R = np.linalg.qr(self.rng.standard_normal((k, k)))
                if not self.app: Q = Q * np.sign(np.diag(R))
                Rs.append(Q)
            yield Rs

    def rotate(self, f, Rs):
        f = (f - f.mean()) / f.std(); c = self.V.T @ f; out = c.copy()
        for k, Q in enumerate(Rs):
            s = k * self.block; out[s:s + len(Q)] = Q @ c[s:s + len(Q)]
        return self.V @ out

    def msr(self, f, B):
        return np.column_stack([self.rotate(f, Rs) for Rs in self.rotations(B)])

    def test(self, f, B=499):
        obs = self.cut(f)[0]; null = self.cut(self.msr(f, B))
        return (1 + (null <= obs).sum()) / (B + 1), obs, null
