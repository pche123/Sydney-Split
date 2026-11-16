"""More power by pooling: how often does pooling one line over k cities find a step that single cities miss?

    python experiments/pooled_power.py [k]

Uses the per-map p-values of the power study (results/phase1/stat_power_*.csv, border count, smooth background):
draws k cities at random from Los Angeles and Seattle maps with the same step, combines their p-values (Stouffer,
one-sided) and counts how often the pooled p is <= 0.05. 20,000 draws per step size.
"""
import os, sys
import numpy as np, pandas as pd
from scipy.stats import norm
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); rng = np.random.default_rng(0)
D = pd.concat([pd.read_csv(f"{ROOT}/results/phase1/stat_power_{c}.csv") for c in ["losangeles", "seattle_ranked"]])
D = D[D.background == "smooth"]
for k in ([int(sys.argv[1])] if len(sys.argv) > 1 else [1, 5, 11, 29]):
    out = []
    for j, g in D.groupby("jump"):
        p = np.clip(g["join"].values, 1e-3, 1 - 1e-3); z = norm.isf(p)
        Z = z[rng.integers(0, len(z), (20000, k))].sum(1) / np.sqrt(k)
        out.append(f"{j:.0f} SD: {np.mean(norm.sf(Z) <= 0.05):.0%}")
    print(f"k = {k:2d} cities: " + ", ".join(out))
