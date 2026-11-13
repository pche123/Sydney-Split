import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "linetests"))  # library
"""Calibrate GPNull on the same random-landscape simulations that broke MSR."""
import sys, time, numpy as np
from scipy import ndimage
from shapely import contains_xy
from cities import load
from landscape import GPNull, MultiScaleNull
R, B = int(sys.argv[1]), int(sys.argv[2]); city = sys.argv[3]
rng = np.random.default_rng(4)
C = load(city); n = C["n"]
t = time.time(); GP = MultiScaleNull(C["geom"], C["I"], C["J"], C["W"], m=int(sys.argv[4])); print("cov built", round(time.time() - t), "s", flush=True)
x0, y0, x1, y1 = C["geom"].total_bounds; cell = 250.0
gx, gy = np.meshgrid(np.arange(x0, x1, cell), np.arange(y0, y1, cell))
owner = np.full(gx.shape, -1)
for i, g in enumerate(C["geom"]): owner[contains_xy(g, gx, gy)] = i
ok = owner >= 0; cnt = np.bincount(owner[ok], minlength=n)
CASES = [("mix", 0.2), ("mix", 0.0), (3, 0.0), (3, 0.2), (10, 0.2), (1, 0.2)] if len(sys.argv) > 5 else [(e, s) for e in [1, 3, 10, 25] for s in [0.0, 0.5]]
for ell, noise in CASES:
    if True:
        rej = 0; ells = []
        for r in range(R):
            if ell == "mix":
                z = sum(a * ndimage.gaussian_filter(rng.standard_normal(gx.shape), e * 1000 / cell / np.sqrt(2), mode="wrap") * e / 3 for e, a in [(2, 1.0), (8, 1.0), (25, 1.0)])
            else:
                z = ndimage.gaussian_filter(rng.standard_normal(gx.shape), ell * 1000 / cell / np.sqrt(2), mode="wrap")
            f = np.bincount(owner[ok], weights=z[ok], minlength=n) / np.maximum(cnt, 1)
            f = (f - f.mean()) / f.std() + noise * rng.standard_normal(n)
            p, obs, nm, par = GP.test(f, B, seed=r); rej += p <= 0.05; ells.append(par["ell"])
        print(city, f"ell={ell}km noise={noise}", "false-positive rate", round(rej / R, 3), "fitted ell median", round(float(np.median(ells)), 1), flush=True)
