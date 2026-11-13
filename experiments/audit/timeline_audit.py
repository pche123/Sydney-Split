import os, sys; _H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [_H, os.path.dirname(_H), os.path.join(os.path.dirname(_H), "..")]  # experiments, repo root
from paths import SYD, TOK, RAW  # noqa: E402
"""Persistence test (same side in 2001 and 2021) redone with the landscape null."""
import sys, numpy as np
sys.argv = ["x"]
exec(open("timeline_export.py").read().split("out_lines = []")[0])
from cities import load
from linetests.landscape import MultiScaleNull
C = load("Sydney"); GPn = MultiScaleNull(C["geom"], C["I"], C["J"], C["W"])
rng = np.random.default_rng(3)
for lid, name, aw, bw, fa, fb, _ in LINES:
    def score(d): return rz(fa(d)) - (rz(fb(d)) if fb else 0)
    F = {y: score(data[y]) for y in ["2001", "2021"]}; s01 = F["2001"] > np.median(F["2001"]); s21 = F["2021"] > np.median(F["2021"])
    obs = max((s01 == s21).mean(), (s01 != s21).mean())
    par = GPn.fit(F["2021"]); Z = GPn.simulate(par, 999, rng)
    S = Z > np.median(Z, 0); a = (S == s01[:, None]).mean(0); null = np.maximum(a, 1 - a)
    print(f"{name}: same side {obs:.0%}; landscape null median {np.median(null):.0%} (95th pct {np.quantile(null, .95):.0%}); p = {(1 + (null >= obs).sum()) / 1000:.3f}", flush=True)
