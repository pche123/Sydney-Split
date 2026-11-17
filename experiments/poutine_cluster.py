"""C1 Poutine Line, allowing for clustering: fast-food places are grouped into 1 km squares and whole squares are resampled.

    python experiments/poutine_cluster.py <folder with phase2/<city>/raw/osm/places.csv>

Also reports the test with each chain counted once (a brand repeated many times is one decision, not many).
"""
import json, os, sys, re
import numpy as np, pandas as pd
from pyproj import Transformer
from scipy.stats import fisher_exact

import ast
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); IN = sys.argv[1]
POUTINE = r"poutin|casse-cro|casse cro|patate|belle province|ashton|lafleur|valentine|frite alors|smoke's"   # as in phase2_food.py


def load(city):
    P = pd.read_csv(f"{IN}/phase2/{city}/raw/osm/places.csv"); t = P.tags.map(ast.literal_eval)
    ff = t.map(lambda q: q.get("amenity") == "fast_food"); P, t = P[ff].reset_index(drop=True), t[ff].reset_index(drop=True)
    nm = t.map(lambda q: " | ".join(str(q.get(k, "")) for k in ("name", "brand", "operator")).lower())
    pou = t.map(lambda q: "poutine" in str(q.get("cuisine", "")).lower()) | nm.str.contains(POUTINE, regex=True)
    X, Y = Transformer.from_crs(4326, 3347, always_xy=True).transform(P.lon.values, P.lat.values)
    return pd.DataFrame({"cell": [f"{int(x // 1000)}_{int(y // 1000)}" for x, y in zip(X, Y)], "pou": pou.values,
                         "name": t.map(lambda q: str(q.get("brand") or q.get("name") or "").strip().lower()).values})


g, o = load("gatineau"), load("ottawa")
diff = g.pou.mean() - o.pou.mean()
rng = np.random.default_rng(7); gc, oc = g.groupby("cell").pou.agg(["sum", "count"]), o.groupby("cell").pou.agg(["sum", "count"])
B = 20000; d = np.empty(B)
for b in range(B):
    a = gc.iloc[rng.integers(0, len(gc), len(gc))].sum(); c = oc.iloc[rng.integers(0, len(oc), len(oc))].sum()
    d[b] = a["sum"] / a["count"] - c["sum"] / c["count"]
# chains once: each distinct name counts once per side
gu, ou = g.drop_duplicates("name"), o.drop_duplicates("name")
_, p_names = fisher_exact([[gu.pou.sum(), (~gu.pou).sum()], [ou.pou.sum(), (~ou.pou).sum()]], alternative="greater")
out = dict(share_gatineau=g.pou.mean(), share_ottawa=o.pou.mean(), cells_gatineau=len(gc), cells_ottawa=len(oc),
           diff=diff, ci95=[float(np.quantile(d, 0.025)), float(np.quantile(d, 0.975))], p_cluster=float((1 + (d <= 0).sum()) / (B + 1)),
           names_gatineau=[int(gu.pou.sum()), len(gu)], names_ottawa=[int(ou.pou.sum()), len(ou)], p_distinct_names=float(p_names))
json.dump(out, open(os.path.join(ROOT, "results", "phase2", "food", "poutine_cluster.json"), "w"), indent=1); print(out)
