import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "linetests"))  # library
"""Is the MSR line test calibrated for census-type maps?

H0 fields are built the way nature would: a stationary Gaussian random field on a 250 m
grid in real space (Gaussian covariance, length scale ell), AVERAGED over each real area
(so big outer areas are smoother than small inner ones, as in real data), plus optional
area-level noise, then rank-normal transformed.  The line test should say "line" ~5%."""
import sys, numpy as np
from scipy import ndimage
from scipy.stats import norm, rankdata
from shapely import contains_xy
from cities import load
from msr import LineTest

R, B = int(sys.argv[1]), int(sys.argv[2])
rng = np.random.default_rng(4)
rn = lambda x: norm.ppf((rankdata(x) - 0.5) / len(x))
for city in ["Sydney", "Tokyo"]:
    C = load(city); n = C["n"]
    x0, y0, x1, y1 = C["geom"].total_bounds; cell = 250.0
    gx, gy = np.meshgrid(np.arange(x0, x1, cell), np.arange(y0, y1, cell))
    owner = np.full(gx.shape, -1)
    for i, g in enumerate(C["geom"]):
        owner[contains_xy(g, gx, gy)] = i
    ok = owner >= 0; cnt = np.bincount(owner[ok], minlength=n)
    tests = {"app": LineTest(n, C["I"], C["J"], C["W"], app_style=True, seed=1), "canonical": LineTest(n, C["I"], C["J"], C["W"], seed=2)}
    for ell in [1, 3, 10, 25]:
        for noise in [0.0, 0.5]:
            rej = {k: 0 for k in tests}
            for r in range(R):
                z = ndimage.gaussian_filter(rng.standard_normal(gx.shape), ell * 1000 / cell / np.sqrt(2), mode="wrap")
                f = np.bincount(owner[ok], weights=z[ok], minlength=n) / np.maximum(cnt, 1)
                f = (f - f.mean()) / f.std() + noise * rng.standard_normal(n)
                f = rn(f)
                for k, T in tests.items(): rej[k] += T.test(f, B)[0] <= 0.05
            print(city, f"ell={ell}km noise={noise}", {k: round(v / R, 3) for k, v in rej.items()}, flush=True)
