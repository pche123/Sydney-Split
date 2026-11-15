"""Pool each line's evidence across cities: is the Latte Line real *in general*, even where no single city can show it?

    python experiments/pooled_lines.py <phase1 app folder> [out.csv]

Uses each city's own (uncorrected) p-value for the line, from the calibrated landscape test where it was run
(the single-fit test for London). Stouffer's method: z_i = Φ⁻¹(1 − p_i), Z = Σ z_i / √k, one-sided. Cities are
separate places, so their tests are independent. Reported separately for Phase 0 (found), Phase 1 (held out)
and both, so Phase 1 can act as a replication of what Phase 0 suggests. Holm across lines within each column.
"""
import glob, json, os, sys
import numpy as np, pandas as pd
from scipy.stats import norm

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
APP1 = sys.argv[1]; OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "results", "pooled_lines.csv")
P0 = sorted(set(os.path.basename(f)[:-5] for f in glob.glob(f"{ROOT}/app/data/*.json")) - {"sydney", "tokyo"})
rows = []
for phase, folder, cities in [("0", f"{ROOT}/app/data", P0), ("1", APP1, sorted(os.path.basename(f)[:-5] for f in glob.glob(f"{APP1}/*.json")))]:
    for c in cities:
        for l in json.load(open(f"{folder}/{c}.json"))["lines"]:
            if l["group"] != "Chains" and l.get("p_own") is not None:
                rows.append(dict(phase=phase, city=c, line=l["id"], name=l["name"], p=min(max(l["p_own"], 1e-4), 1 - 1e-4)))
D = pd.DataFrame(rows)

def holm(p):
    p = np.asarray(p, float); o = np.argsort(p); m = len(p); r = np.empty(m); run = 0
    for k, i in enumerate(o): run = max(run, (m - k) * p[i]); r[i] = min(1, run)
    return r

out = []
for lid, g in D.groupby("line"):
    rec = dict(line=lid, name=g.name.iloc[0])
    for tag, sub in [("p0", g[g.phase == "0"]), ("p1", g[g.phase == "1"]), ("all", g)]:
        z = norm.isf(sub.p.values); k = len(z)
        rec[f"{tag}_cities"] = k
        rec[f"{tag}_Z"] = z.sum() / np.sqrt(k) if k else np.nan
        rec[f"{tag}_p"] = norm.sf(rec[f"{tag}_Z"]) if k else np.nan
        rec[f"{tag}_single_passes"] = int((sub.p <= 0.05).sum())
    out.append(rec)
R = pd.DataFrame(out)
for tag in ["p0", "p1", "all"]:
    ok = R[f"{tag}_p"].notna() & (R[f"{tag}_cities"] >= 3)
    R.loc[ok, f"{tag}_p_holm"] = holm(R.loc[ok, f"{tag}_p"])
R = R.sort_values("all_p"); os.makedirs(os.path.dirname(OUT), exist_ok=True); R.to_csv(OUT, index=False)
show = ["name", "p0_cities", "p0_p_holm", "p1_cities", "p1_p_holm", "all_cities", "all_Z", "all_p_holm"]
print(R[show].round(4).to_string(index=False))
