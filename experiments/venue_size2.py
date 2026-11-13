import os, sys; _H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [_H, os.path.dirname(_H), os.path.join(os.path.dirname(_H), "..")]  # experiments, repo root
from paths import SYD, TOK, RAW  # noqa: E402
import numpy as np
from venue_null import tokyo, sydney, smooth_p
rng = np.random.default_rng(12)
for city, fn in [("Tokyo", tokyo), ("Sydney", sydney)]:
    G, VL = fn()
    for lid, L in VL.items():
        out = []
        for truth, test in [(5000, 3000), (3000, 2000), (3000, 3000)]:
            p0 = smooth_p(L.xy, L.y, truth); rej = np.zeros(4)
            for r in range(100):
                y = (rng.random(len(p0)) < p0).astype(float)
                rej += L.test(test, 99, seed=r, y=y)["p"] <= 0.05
            out.append(f"truth {truth/1000:g}km/test {test/1000:g}km: JC {rej[0]/100:.2f} STEP {rej[2]/100:.2f} RD {rej[3]/100:.2f}")
        print(city, lid, " | ".join(out), flush=True)
