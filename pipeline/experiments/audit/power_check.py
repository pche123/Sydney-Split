import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "linetests"))  # library
"""Power: can the landscape test still find a real line?  Truth = multi-scale random landscape
+ a step of size delta (in SD units) across a realistic border (median split of another
smooth landscape), + area noise.  Compare old MSR (miscalibrated) and the landscape test."""
import sys, numpy as np
from scipy import ndimage
from shapely import contains_xy
from scipy.stats import norm, rankdata
from cities import load
from landscape import MultiScaleNull
from msr import LineTest
R = int(sys.argv[1]); rng = np.random.default_rng(8)
C = load("Sydney"); n = C["n"]; GPn = MultiScaleNull(C["geom"], C["I"], C["J"], C["W"]); T = LineTest(n, C["I"], C["J"], C["W"])
x0, y0, x1, y1 = C["geom"].total_bounds; cell = 250.0
gx, gy = np.meshgrid(np.arange(x0, x1, cell), np.arange(y0, y1, cell)); owner = np.full(gx.shape, -1)
for i, g in enumerate(C["geom"]): owner[contains_xy(g, gx, gy)] = i
ok = owner >= 0; cnt = np.bincount(owner[ok], minlength=n)
def landscape():
    z = sum(ndimage.gaussian_filter(rng.standard_normal(gx.shape), e * 1000 / cell / np.sqrt(2), mode="wrap") * e / 3 for e in (2, 8, 25))
    f = np.bincount(owner[ok], weights=z[ok], minlength=n) / np.maximum(cnt, 1); return (f - f.mean()) / f.std()
for delta in [0.0, 0.5, 1.0, 1.5]:
    rej = np.zeros(2)
    for r in range(R):
        b = landscape(); step = (b > np.median(b)).astype(float) - 0.5
        f = landscape() + delta * 2 * step + 0.3 * rng.standard_normal(n)
        rej += [T.test(f, 199)[0] <= 0.05, GPn.test(f, 199, seed=r)[0] <= 0.05]
    print(f"step {delta} SD: old MSR says line {rej[0]/R:.2f}, landscape test says line {rej[1]/R:.2f}", flush=True)
