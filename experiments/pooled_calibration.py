"""Pooled p-values, calibrated against what pooling gives when no city has a line.

    python experiments/pooled_calibration.py

Stouffer's method assumes each city's p-value is uniform when there is no line. Ours are not quite: on 72 Chicago
maps with no line (results/phase1/calibrated_benchmark_chicago_*.csv) the calibrated p-values average z = +0.15, so
pooling k cities inflates false alarms (k = 11: 14% at the 5% level). Here each pooled Z is compared instead with
2,000,000 pools of k p-values drawn from those no-line maps; Holm then runs across lines as before. Applies to the
held-out pooling (results/pooled_lines.csv) and the country lines (results/country_lines/country_lines.csv).
"""
import os
import numpy as np, pandas as pd
from scipy.stats import norm

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
C = pd.concat([pd.read_csv(f"{ROOT}/results/phase1/calibrated_benchmark_chicago_{k}.csv") for k in (1, 2)])
z0 = norm.isf(np.clip(C.p_cal.values, 1e-3, 1 - 1e-3)); rng = np.random.default_rng(7); N = 2_000_000
_cache = {}
def emp(Z, k):
    if k not in _cache: _cache[k] = np.sort(z0[rng.integers(0, len(z0), (N, k))].sum(1) / np.sqrt(k))
    s = _cache[k]; return (1 + len(s) - np.searchsorted(s, Z, side="left")) / (len(s) + 1)
def holm(p):
    p = np.asarray(p, float); o = np.argsort(p); m = len(p); r = np.empty(m); run = 0
    for k, i in enumerate(o): run = max(run, (m - k) * p[i]); r[i] = min(1, run)
    return r

P = pd.read_csv(f"{ROOT}/results/pooled_lines.csv")
for tag in ["p0", "p1", "all"]:
    ok = P[f"{tag}_cities"] >= 3
    P.loc[ok, f"{tag}_p_emp"] = [emp(Z, int(k)) for Z, k in zip(P.loc[ok, f"{tag}_Z"], P.loc[ok, f"{tag}_cities"])]
    P.loc[ok, f"{tag}_p_emp_holm"] = holm(P.loc[ok, f"{tag}_p_emp"])
P.to_csv(f"{ROOT}/results/pooled_lines.csv", index=False)
print(P[["name", "p1_cities", "p1_Z", "p1_p_holm", "p1_p_emp", "p1_p_emp_holm"]].sort_values("p1_p_emp").head(6).round(4).to_string(index=False))

R = pd.read_csv(f"{ROOT}/results/country_lines/country_lines.csv")
for ctry in R.country.unique():
    m = (R.country == ctry) & (R.cities >= 2)
    R.loc[m, "p_emp"] = [emp(Z, int(k)) for Z, k in zip(R.loc[m, "Z"], R.loc[m, "cities"])]
    R.loc[m, "p_emp_holm"] = holm(R.loc[m, "p_emp"])
R["verdict_emp"] = np.where(R.cities < 2, "one city only", np.where(R.p_emp_holm <= 0.05, "real across the country", np.where(R.p_emp <= 0.05, "leaning", "slope")))
R.to_csv(f"{ROOT}/results/country_lines/country_lines.csv", index=False)
print(R[R.p <= 0.05][["country", "name", "cities", "Z", "p_holm", "p_emp", "p_emp_holm", "verdict_emp"]].round(4).to_string(index=False))
