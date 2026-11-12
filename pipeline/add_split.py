import json, pandas as pd
d = json.load(open("app_data.json")); sp = pd.read_csv("split_suburbs.csv")
idx = {a["name"]: i for i, a in enumerate(d["areas"])}
d["split"] = {str(idx[r.suburb]): [int(r.minority_side_pct), float(r.prof_part_professionals_pct), float(r.hivis_part_professionals_pct)] for r in sp.itertuples() if r.suburb in idx}
json.dump(d, open("app_data.json", "w"), separators=(",", ":"))
