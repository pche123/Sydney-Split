"""Add (1) each line's sharp stretches and (2) family shared-border tests to every built city.

    python pipeline/common/sharp_and_families.py <cities work folder> [city ...]

(1) Sharp stretches (local Geary against the fitted landscape): for each line, the borders it runs along where the
    jump between the two sides is bigger than the landscape makes on that border (Benjamini-Hochberg, q = 0.10).
    Saved as line["sharp"] = indices into make.I/J, drawn thicker in the app.
(2) Families: lines of one family (work & class, inner city, night out) are tested for changing side on the same
    borders more than smooth maps with the same correlation would. Saved to meta["families"] and results/families.csv.
"""
import json, os, sys
import numpy as np, pandas as pd, geopandas as gpd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path[:0] = [os.path.join(HERE, ".."), ROOT]
from cities import CITIES
from linetests.landscape import MultiScaleNull
from linetests.geary import sharp_stretches, shared_border_test

FAMILIES = {"Work and class": ["the-hi-vis-line", "the-degree-line", "the-laptop-vs-hard-hat-line", "the-factory-line"],
            "Inner city": ["flats-vs-houses", "the-renters-line", "the-living-alone-line", "train-vs-car", "the-no-car-line", "the-bicycle-line"],
            "Night out": ["coffee-vs-alcohol", "drink-out-vs-drink-in"]}
CI = sys.argv[1]; only = sys.argv[2:]
rows = []
out_csv = os.path.join(ROOT, "results", "families.csv")
if os.path.exists(out_csv): rows = pd.read_csv(out_csv).to_dict("records")
for city in (only or [c for c in CITIES if os.path.exists(f"{CI}/{c}/fields.npz")]):
    app = os.path.join(ROOT, "app", "data", f"{city}.json")
    if not os.path.exists(app) or not os.path.exists(f"{CI}/{city}/fields.npz"): continue
    z = np.load(f"{CI}/{city}/fields.npz"); I, J, W = z["I"], z["J"], z["W"]
    G = gpd.read_file(f"{CI}/{city}/areas.gpkg").to_crs(CITIES[city]["crs"]).reset_index(drop=True)
    MS = MultiScaleNull(G.geometry, I, J, W, m=9 if len(G) > 600 else 25)
    F = {str(i): f for i, f in zip(z["ids"], z["F"].T)}; kinds = {str(i): k for i, k in zip(z["ids"], z["kinds"])}
    d = json.load(open(app)); nsharp = []
    for l in d["lines"]:
        if l["id"] not in F or kinds[l["id"]] == "chain": continue
        on, sharp, p = sharp_stretches(MS, F[l["id"]], I, J, W, B=199, seed=3)
        l["sharp"] = [int(e) for e in on[sharp]]; l["sharp_share"] = round(float(sharp.mean()), 3) if len(on) else 0.0
        nsharp.append((l["name"], len(l["sharp"]), len(on)))
    fam = []
    for name, ids in FAMILIES.items():
        ids = [i for i in ids if i in F]
        if len(ids) < 2: continue
        p, obs, nm = shared_border_test(MS, [F[i] for i in ids], I, J, W, B=199, seed=4)
        fam.append(dict(family=name, lines=ids, p=round(p, 3), shared=round(obs, 3), expected=round(nm, 3)))
        rows = [r for r in rows if not (r["city"] == city and r["family"] == name)] + [dict(city=city, family=name, n_lines=len(ids), p=p, shared=obs, expected=nm)]
    d["meta"]["families"] = fam
    json.dump(d, open(app, "w"), separators=(",", ":"), ensure_ascii=False)
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(city, "| sharp borders:", ", ".join(f"{n.replace('The ', '')} {k}/{m}" for n, k, m in nsharp[:6]), "...",
          "| families:", "; ".join(f"{f['family']} p={f['p']} ({f['shared']:.2f} vs {f['expected']:.2f})" for f in fam), flush=True)
