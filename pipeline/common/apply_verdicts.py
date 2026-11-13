"""Write the audited verdicts into an app's data file.  Usage: apply_verdicts.py <app.json> <verdicts.csv> <Sydney|Tokyo>"""
import sys, json, pandas as pd, numpy as np
app, vf, city = sys.argv[1:4]
d = json.load(open(app)); v = pd.read_csv(vf); v = v[v.city == city].set_index("name")
TIER = {"Real line": "line", "Real pattern, gentle": "gentle", "Could be chance": "chance"}
r3 = lambda x: None if pd.isna(x) else round(float(x), 3)
for l in d["lines"]:
    r = v.loc[l["name"]]
    l.setdefault("p_old", l["p"]); l["p"] = r3(r.p_corrected); l["tier"] = TIER[r.verdict]; l["p_geo"] = r3(r.p_geography); l["p_edge"] = r3(r.p_edge)
json.dump(d, open(app, "w"), separators=(",", ":"))
print(city, {t: sum(l["tier"] == t for l in d["lines"]) for t in TIER.values()})
