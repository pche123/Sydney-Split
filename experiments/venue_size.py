import os, sys; _H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [_H, os.path.dirname(_H), os.path.join(os.path.dirname(_H), "..")]  # experiments, repo root
from paths import SYD, TOK, RAW  # noqa: E402
import numpy as np, sys
from venue_null import tokyo, sydney, smooth_p
rng = np.random.default_rng(11)
for city, fn in [("Tokyo", tokyo), ("Sydney", sydney)]:
    G, VL = fn()
    for lid in list(VL)[: (4 if city == "Tokyo" else 4)]:
        L = VL[lid]; p0 = smooth_p(L.xy, L.y, 3000)
        # power: push the A-share up by delta on the 'A' side of an unrelated smooth border
        g = G.V[:, :15] @ (rng.standard_normal(15) / (1 + np.arange(15) / 4.0)); side = g > np.median(g)
        ven_side = (L.M.T @ side.astype(float)) > (L.M.T @ np.ones(len(side))) / 2     # venue mostly counted on that side
        res = {}
        for delta in [0.0, 0.5, 1.0]:
            lg = np.log(p0 / (1 - p0)) + delta * (ven_side - 0.5) * 2
            pt = 1 / (1 + np.exp(-lg)); rej = np.zeros(4)
            for r in range(100):
                y = (rng.random(len(pt)) < pt).astype(float)
                rej += L.test(3000, 99, seed=r, y=y)["p"] <= 0.05
            res[delta] = np.round(rej[[0, 2, 3]] / 100, 2)
        print(city, lid, "JC/STEP/RD rejection at logit step 0, 0.5, 1:", res, flush=True)
