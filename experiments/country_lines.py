"""Country lines: which lines are real across one country's cities, and which set a country apart?

    python experiments/country_lines.py <phase1 app folder> [out folder]

Each city's own (uncorrected) p for a line, from the calibrated test. Within a country, Stouffer's method pools
the cities (one-sided, z_i = Φ⁻¹(1 − p_i)); Holm across that country's lines. A line is "distinct" to a country if
its city z-scores are higher there than in the other countries (one-sided Mann–Whitney, Holm across lines), or if
only that country measures it (chains, local job words). Sydney and Tokyo use a different line set and are left out.
Phase 0 countries (Australia, Japan, England) were the discovery cities, so their country lines are found, not confirmed.
"""
import glob, json, os, sys
import numpy as np, pandas as pd
from scipy.stats import norm, mannwhitneyu

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
from cities import CITIES

APP1 = sys.argv[1]; OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "results", "country_lines")
os.makedirs(OUT, exist_ok=True)
files = [f for f in glob.glob(f"{ROOT}/app/data/*.json") if os.path.basename(f)[:-5] not in ("sydney", "tokyo")] + glob.glob(f"{APP1}/*.json")
rows = []
for f in files:
    c = os.path.basename(f)[:-5]
    for l in json.load(open(f))["lines"]:
        if l.get("p_own") is None: continue
        p = min(max(l["p_own"], 1e-3), 1 - 1e-3)
        rows.append(dict(country=CITIES[c]["country"], city=c, line=l["id"], name=l["name"], group=l["group"], p=p, z=norm.isf(p), tier=l["tier"]))
D = pd.DataFrame(rows); D.to_csv(f"{OUT}/city_lines.csv", index=False)


def holm(p):
    p = np.asarray(p, float); o = np.argsort(p); m = len(p); r = np.empty(m); run = 0
    for k, i in enumerate(o): run = max(run, (m - k) * p[i]); r[i] = min(1, run)
    return r


out = []
for (ctry, lid), g in D.groupby(["country", "line"]):
    rest = D[(D.line == lid) & (D.country != ctry)]
    k = len(g); Z = g.z.sum() / np.sqrt(k)
    rec = dict(country=ctry, line=lid, name=g.name.iloc[0], group=g.group.iloc[0], cities=k, Z=Z, p=norm.sf(Z),
               real_in=int((g.tier == "line").sum()), mean_z=g.z.mean(), other_cities=len(rest),
               other_mean_z=rest.z.mean() if len(rest) else np.nan,
               p_distinct=mannwhitneyu(g.z, rest.z, alternative="greater").pvalue if len(rest) >= 2 and k >= 2 else np.nan,
               only_here=len(rest) == 0)
    out.append(rec)
R = pd.DataFrame(out)
for ctry in R.country.unique():
    m = (R.country == ctry) & (R.cities >= 2)
    if m.any(): R.loc[m, "p_holm"] = holm(R.loc[m, "p"])
    m2 = (R.country == ctry) & R.p_distinct.notna()
    if m2.any(): R.loc[m2, "p_distinct_holm"] = holm(R.loc[m2, "p_distinct"])


def verdict(r):
    if r.cities < 2: return "one city only"
    if r.p_holm <= 0.05: return "real across the country"
    if r.p <= 0.05: return "leaning"
    return "slope"


R["verdict"] = R.apply(verdict, axis=1)
R["distinct"] = R.only_here | (R.p_distinct_holm <= 0.05)
R = R.sort_values(["country", "p"]); R.to_csv(f"{OUT}/country_lines.csv", index=False)
pd.set_option("display.width", 200)
for ctry, g in R.groupby("country"):
    print(f"\n{ctry.upper()}  ({g.cities.max()} cities)")
    print(g[g.p <= 0.1][["name", "cities", "real_in", "Z", "p", "p_holm", "verdict", "other_mean_z", "p_distinct_holm", "only_here"]].round(3).to_string(index=False))
