"""Download table for the two original cities (Sydney, Tokyo), straight from their app data files.

    python pipeline/common/export_downloads.py sydney tokyo

Writes app/public/downloads/<city>_areas.csv (area names, every Make-your-own figure, side of each line) and
adds meta.download to the app data. HotPepper-based figures are left out (its terms don't allow passing them on).
"""
import json, os, sys
import pandas as pd

APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "app")
for city in sys.argv[1:]:
    f = f"{APP}/data/{city}.json"; d = json.load(open(f))
    t = pd.DataFrame({"area": [a["short"] for a in d["areas"]], "full_name": [a["name"] for a in d["areas"]],
                      "population": [p for p in d["make"]["pop"]]})
    for s in d["make"]["signals"]:
        if s["id"].startswith("hp_") or s["id"] == "dinner_price": continue
        t[s["id"]] = s["v"]
    for l in d["lines"]:
        if l["group"] != "Night" or city != "tokyo": t["side_" + l["id"]] = l["side"]
    os.makedirs(f"{APP}/public/downloads", exist_ok=True)
    t.to_csv(f"{APP}/public/downloads/{city}_areas.csv", index=False)
    d["meta"]["download"] = dict(csv=f"downloads/{city}_areas.csv", hotpepper=city == "tokyo")
    json.dump(d, open(f, "w"), separators=(",", ":"), ensure_ascii=False)
    print(city, t.shape)
