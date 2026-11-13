import os, sys; _H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [_H, os.path.dirname(_H), os.path.join(os.path.dirname(_H), "..")]  # experiments, repo root
from paths import SYD, TOK, RAW  # noqa: E402
"""Does discreteness break the ORIGINAL cleanness test?  Venue labels drawn with a constant
chance (no geography at all), pushed through the app's counting + formula, then the usual
MSR cleanness test.  Should reject ~5%."""
import numpy as np
from venue_null import tokyo, sydney
rng = np.random.default_rng(5)
def clean(G, F):
    S = F > np.median(F, 0); w = G.W[:, None]
    return ((S[G.I] != S[G.J]) * w).sum(0) / (0.5 * G.W.sum())
for city, fn in [("Tokyo", tokyo), ("Sydney", sydney)]:
    G, VL = fn()
    for lid, L in VL.items():
        rej = 0
        for r in range(100):
            y = (rng.random(len(L.y)) < L.y.mean()).astype(float)
            f = L.field(y) + 1e-9 * rng.standard_normal(G.n)
            null = clean(G, G.msr(f, 199)); obs = clean(G, f[:, None])[0]
            rej += (1 + (null <= obs).sum()) / 200 <= 0.05
        print(city, lid, "false-positive rate:", rej / 100, flush=True)
