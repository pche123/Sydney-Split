"""Small app extras for Sydney: every suburb named when zoomed in, shops only inside the map, a 'what is hi-vis' note."""
import json, numpy as np, pandas as pd, geopandas as gpd
from shapely import contains_xy
d = json.load(open("app_data.json"))
used = {l["i"] for l in d["labels"]}
for l in d["labels"]: l["tier"] = 1
d["labels"] += [dict(i=i, t=a["short"], tier=2) for i, a in enumerate(d["areas"]) if i not in used]
a = pd.read_csv("q_classic/areas.csv", dtype=str)
G = gpd.read_file("data/shp/SA2_2021_AUST_GDA2020.shp").to_crs(7856).set_index("SA2_CODE21").loc[a.SA2_CODE21]
inmap = G.geometry.union_all().buffer(300)
for b in d["make"]["brands"]:
    xy = np.array(b["xy"]); keep = contains_xy(inmap, xy[:, 0], xy[:, 1])
    b["xy"] = [p for p, k in zip(b["xy"], keep) if k]; b["vb"] = [p for p, k in zip(b["vb"], keep) if k]; b["n"] = len(b["xy"])
HIVIS = ('<div class="box"><h3>What does "hi-vis" mean?</h3><p style="margin:0">Hi-vis is Australian slang for the bright, high-visibility vests '
         'worn on building sites, roads, warehouses and delivery routes.</p><p class="small">Here it means warehouse, delivery, driving and labouring jobs, '
         'compared with office and professional jobs. It describes jobs, not people.</p></div>')
d["meta"]["explain"] = {"the-hi-vis-line": HIVIS}
json.dump(d, open("app_data.json", "w"), separators=(",", ":"))
print("labels", len(d["labels"]), "brands", [(b["name"], b["n"]) for b in d["make"]["brands"]][:6])
