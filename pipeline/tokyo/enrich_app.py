"""Add to app/data/tokyo.json: smooth scores (for the slope view) and each line's own p next to the corrected one.

    python pipeline/tokyo/enrich_app.py <tokyo out folder>

Scores come from tokyo_fields.npz and are attached only where they reproduce the app's sides (≥ 97%). Own p-values
come from results/final_census_Tokyo.csv, final_data_Tokyo.csv and final_chains.csv; the script checks that Holm
within each group gives back the published p.
"""
import json, os, sys
import numpy as np, pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."); OUTD = sys.argv[1]
P = os.path.join(ROOT, "app", "data", "tokyo.json"); d = json.load(open(P)); byid = {l["id"]: l for l in d["lines"]}
z = np.load(os.path.join(OUTD, "tokyo_fields.npz"), allow_pickle=False)
for lid, f in zip(z["ids"], z["F"].T):
    if lid not in byid: continue
    s = np.array(byid[lid]["side"], bool); m = ((f > np.median(f)) == s).mean()
    if m < 0.5: f, m = -f, 1 - m
    if m >= 0.97: byid[lid]["f"] = [round(float(v), 4) for v in f]
    print(f"{lid}: score reproduces {m:.0%} of sides" + ("" if m >= 0.97 else " (not attached)"))
own = {}
for fn in ["final_census_Tokyo.csv", "final_data_Tokyo.csv", "final_chains.csv"]:
    r = pd.read_csv(os.path.join(ROOT, "results", fn)); r = r[r.city == "Tokyo"]; own.update(dict(zip(r.line, r.p_cal)))
for g in {l["group"] for l in d["lines"]}:
    ls = [l for l in d["lines"] if l["group"] == g]; ps = np.array([own[l["id"]] for l in ls]); m = len(ps); run = 0; h = np.empty(m)
    for k, i in enumerate(np.argsort(ps)): run = max(run, (m - k) * ps[i]); h[i] = min(1, run)
    for l, pv, hv in zip(ls, ps, h):
        assert abs(round(hv, 3) - l["p"]) <= 0.003, (l["id"], hv, l["p"])
        l["p_own"], l["n_group"] = round(float(pv), 3), m
json.dump(d, open(P, "w"), separators=(",", ":"), ensure_ascii=False)
print("updated", P)
