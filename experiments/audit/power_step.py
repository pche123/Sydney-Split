import os, sys; _H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [_H, os.path.dirname(_H), os.path.join(os.path.dirname(_H), "..")]  # experiments, repo root
from paths import SYD, TOK, RAW  # noqa: E402
import sys, numpy as np
exec(open("power_check.py").read().split("for delta in")[0].replace("R = int(sys.argv[1])", "R = int(sys.argv[1])"))
from linetests.landscape import step_test
for delta in [0.0, 0.5, 1.0, 1.5]:
    rej = 0
    for r in range(R):
        b = landscape(); step = (b > np.median(b)).astype(float) - 0.5
        f = landscape() + delta * 2 * step + 0.3 * rng.standard_normal(n)
        rej += step_test(GPn, f, 199, seed=r)[0] <= 0.05
    print(f"step {delta} SD: edge test says line {rej/R:.2f}", flush=True)
