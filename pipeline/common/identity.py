"""Add each city's "identity" to its app file: the country's lines (from experiments/country_lines.py) and its own.

    python pipeline/common/identity.py results/country_lines/country_lines.csv <app folder> [<app folder> ...]

Writes meta.identity. Display only: no verdict changes.
"""
import json, os, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, ".."))
from cities import CITIES

NAMES = {"au": "Australia", "jp": "Japan", "uk": "England", "us": "the US", "nz": "New Zealand", "sg": "Singapore"}
PHASE0 = {"au", "jp", "uk"}
R = pd.read_csv(sys.argv[1])
for folder in sys.argv[2:]:
    for fn in sorted(os.listdir(folder)):
        if not fn.endswith(".json"): continue
        c = fn[:-5]; ctry = CITIES[c]["country"]; path = os.path.join(folder, fn); d = json.load(open(path))
        g = R[R.country == ctry]
        rows = [dict(id=r.line, name=r.name, verdict=r.verdict, cities=int(r.cities), real_in=int(r.real_in),
                     p=None if pd.isna(r.p_holm) else round(float(r.p_holm), 3), only_here=bool(r.only_here))
                for r in g.itertuples() if r.verdict in ("real across the country", "leaning") or r.only_here]
        own = [l["name"] for l in d["lines"] if l["tier"] == "line"]
        country_real = set(g[g.verdict == "real across the country"].line)
        d["meta"]["identity"] = dict(country=NAMES[ctry], n_cities=int(g.cities.max()) if len(g) else 0, found_in=ctry in PHASE0,
                                    lines=rows, city_real=own,
                                    city_only=[l["name"] for l in d["lines"] if l["tier"] == "line" and l["id"] not in country_real])
        json.dump(d, open(path, "w"), separators=(",", ":"), ensure_ascii=False)
        print(c, ctry, len(rows), "country rows;", len(own), "real here")
