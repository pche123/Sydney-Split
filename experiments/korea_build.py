"""Build Seoul and Busan 1 km cells from the SGIS 2024 grid file (pre-registered in HYPOTHESES.md, "Korea").

    python experiments/korea_build.py <unzipped SGIS folder>

Writes results/phase3/{seoul,busan}_cells.csv.gz in the Phase 3 format (x, y = lower-left corner in EPSG 5179).
"""
import glob, os, sys
import numpy as np, pandas as pd, geopandas as gpd
from pyproj import Transformer
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); K = sys.argv[1]
BOX = {"seoul": (126.76, 37.42, 127.19, 37.71), "busan": (128.80, 35.00, 129.30, 35.40)}
tr = Transformer.from_crs(4326, 5179, always_xy=True)
AGE = [f"in_age_{i:03d}" for i in range(1, 22)]; OLD = [f"in_age_{i:03d}" for i in range(14, 22)]
HH = [f"ga_sd_{i:03d}" for i in range(1, 7)]; DW = [f"ho_gb_{i:03d}" for i in range(1, 7)]
want = set(AGE + HH + DW)
geo = pd.concat([gpd.read_file(f) for f in glob.glob(f"{K}/2. 경계/*/*_1K.shp")])
b = geo.geometry.bounds; geo = pd.DataFrame({"code": geo.GRID_CD.values, "x": b.minx.round().astype(int).values, "y": b.miny.round().astype(int).values})
rows = []
for f in glob.glob(f"{K}/1. 통계/[123]. */*_1K.csv"):
    d = pd.read_csv(f, encoding="cp949", dtype=str); d.columns = ["year", "code", "item", "value"]
    rows.append(d[d.item.isin(want)])
d = pd.concat(rows); d["v"] = pd.to_numeric(d.value, errors="coerce")
print("values not numeric (masked):", round(d.v.isna().mean(), 4), d.value[d.v.isna()].unique()[:5])
W = d.pivot_table(index="code", columns="item", values="v", aggfunc="sum").reindex(columns=sorted(want))
W = W.join(geo.set_index("code"), how="inner")
for city, (a, s, c, n) in BOX.items():
    (x0, x1), (y0, y1) = tr.transform([a, c], [s, n])
    C = W[(W.x >= min(x0, x1) - 1000) & (W.x <= max(x0, x1)) & (W.y >= min(y0, y1) - 1000) & (W.y <= max(y0, y1))].copy()
    C["pop"] = C[AGE].sum(axis=1, min_count=1); C = C[C["pop"] >= 1000]
    key = {(p, q): i for i, (p, q) in enumerate(zip(C.x, C.y))}; adj = {i: [] for i in range(len(C))}
    for i, (p, q) in enumerate(zip(C.x, C.y)):
        for dx, dy in ((1000, 0), (0, 1000), (-1000, 0), (0, -1000)):
            j = key.get((p + dx, q + dy))
            if j is not None: adj[i].append(j)
    seen, best = set(), []
    for s0 in range(len(C)):
        if s0 in seen: continue
        comp, st = [], [s0]; seen.add(s0)
        while st:
            u = st.pop(); comp.append(u)
            for v in adj[u]:
                if v not in seen: seen.add(v); st.append(v)
        if len(comp) > len(best): best = comp
    C = C.iloc[sorted(best)]
    out = pd.DataFrame({"x": C.x.values, "y": C.y.values, "ref_pop": C["pop"].values,
                        "num_grey_2024": C[OLD].sum(axis=1, min_count=1).values, "den_grey_2024": C["pop"].values,
                        "num_alone_2024": C["ga_sd_005"].values, "den_alone_2024": C[HH].sum(axis=1, min_count=1).values,
                        "num_apartment_2024": C["ho_gb_003"].values, "den_apartment_2024": C[DW].sum(axis=1, min_count=1).values})
    out.to_csv(os.path.join(ROOT, "results", "phase3", f"{city}_cells.csv.gz"), index=False)
    print(city, len(out), "cells", int(out.ref_pop.sum()), "residents", out.isna().mean().round(3).to_dict())
