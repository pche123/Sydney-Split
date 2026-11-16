"""Add to app/data/sydney.json: smooth scores (for the slope view), each venue line's own p, and the Latte Line claims.

    python pipeline/sydney/enrich_app.py <work folder>

Scores are attached only where they reproduce the app's sides exactly (≥ 97% of suburbs). Own p-values come from
results/final_data_Sydney.csv and results/final_chains.csv; the script checks that Holm within each group gives
back the published p. Claims: pipeline/sydney/latte_claims.json (tests in experiments/latte_claims.py).
"""
import json, os, sys
import numpy as np, pandas as pd
from scipy.stats import norm, rankdata

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."); W_ = sys.argv[1]
sys.path[:0] = [ROOT, W_]; os.chdir(W_)
import lines_sydney

P = os.path.join(ROOT, "app", "data", "sydney.json"); d = json.load(open(P)); byid = {l["id"]: l for l in d["lines"]}
rz = lambda v: norm.ppf((rankdata(pd.Series(v).fillna(pd.Series(v).median()).values) - 0.5) / len(v))

def attach(lid, f):
    s = np.array(byid[lid]["side"], bool); f = np.asarray(f, float); m = ((f > np.median(f)) == s).mean()
    if m < 0.5: f, m = -f, 1 - m
    if m >= 0.97: byid[lid]["f"] = [round(float(v), 4) for v in f]
    print(f"{lid}: score reproduces {m:.0%} of sides" + ("" if m >= 0.97 else " (not attached)"))

T, L = lines_sydney.build()
for k, l in L.items():
    if k in byid: attach(k, l.field)
a = pd.read_csv(f"{W_}/q_classic/areas.csv", dtype=str).SA2_CODE21.values
S = pd.read_csv(f"{W_}/signals_sa2.csv", dtype={"SA2_CODE_2021": str}).set_index("SA2_CODE_2021").loc[a]
for r in pd.read_csv(os.path.join(ROOT, "results", "final_census_Sydney.csv")).itertuples():
    cols = r.definition.split(" vs ")
    if all(c in S for c in cols): attach(r.line, rz(S[cols[0]].values) - (rz(S[cols[1]].values) if len(cols) > 1 else 0))

own = {}
for f in ["final_data_Sydney.csv", "final_chains.csv"]:
    r = pd.read_csv(os.path.join(ROOT, "results", f)); r = r[r.city == "Sydney"]; own.update(dict(zip(r.line, r.p_cal)))
for g in ["Food", "Night"]:
    ls = [l for l in d["lines"] if l["group"] == g]; ps = np.array([own[l["id"]] for l in ls]); m = len(ps); run = 0; h = np.empty(m)
    for k, i in enumerate(np.argsort(ps)): run = max(run, (m - k) * ps[i]); h[i] = min(1, run)
    for l, pv, hv in zip(ls, ps, h):
        assert abs(round(hv, 3) - l["p"]) <= 0.002, l["id"]
        l["p_own"], l["n_group"] = round(float(pv), 3), m
d["meta"]["claims"] = json.load(open(os.path.join(ROOT, "pipeline", "sydney", "latte_claims.json")))
json.dump(d, open(P, "w"), separators=(",", ":"), ensure_ascii=False)
print("updated", P)
