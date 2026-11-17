"""Did a line move? Block bootstrap of the change in each centre-to-edge slope, allowing for neighbours being alike.

    python experiments/time_change_test.py

Slope = Spearman correlation of a variable with distance from the city centre. Change = slope(last census) - slope(first).
Areas are grouped into 5 km squares and whole squares are resampled (2,000 times), so the spread of the change reflects
spatial clustering. Two-sided p; Holm across every city and variable tested. Reads results/time/*_areas.csv.gz.
"""
import os
import numpy as np, pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); T = os.path.join(ROOT, "results", "time")
SPAN = {"us": ("1990", "2020"), "italy": ("1991", "2021"), "germany": ("2011", "2022")}
rk = lambda a: pd.Series(a).rank().values


def slope(v, d):
    return np.corrcoef(rk(v), rk(d))[0, 1]


rows = []
for country, (y0, y1) in SPAN.items():
    A = pd.read_csv(os.path.join(T, f"{country}_areas.csv.gz"))
    for city, C in A.groupby("city"):
        blk = (C.x // 5000).astype(int).astype(str) + "_" + (C.y // 5000).astype(int).astype(str)
        groups = [np.flatnonzero(blk.values == b) for b in blk.unique()]
        for var in sorted({c.rsplit("_", 1)[0] for c in C.columns if c.endswith("_" + y0)}):
            a, b, d = C[f"{var}_{y0}"].values, C[f"{var}_{y1}"].values, C.dist.values
            ok = np.isfinite(a) & np.isfinite(b); obs = slope(b[ok], d[ok]) - slope(a[ok], d[ok])
            rng = np.random.default_rng(11); bs = []
            for _ in range(2000):
                idx = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))]); idx = idx[ok[idx]]
                bs.append(slope(b[idx], d[idx]) - slope(a[idx], d[idx]))
            bs = np.array(bs); p = min(1.0, 2 * min((bs <= 0).mean(), (bs >= 0).mean()) + 1 / 2001)
            rows.append(dict(country=country, city=city, var=var, years=f"{y0}-{y1}", areas=int(ok.sum()), blocks=len(groups),
                             slope_first=slope(a[ok], d[ok]), slope_last=slope(b[ok], d[ok]), change=obs,
                             ci_low=np.quantile(bs, 0.025), ci_high=np.quantile(bs, 0.975), p=p))
R = pd.DataFrame(rows).sort_values("p").reset_index(drop=True)
m = len(R); R["p_holm"] = np.minimum(1, np.maximum.accumulate(R.p * (m - np.arange(m))))
R.to_csv(os.path.join(T, "change_test.csv"), index=False)
print(R.round(3).to_string())
