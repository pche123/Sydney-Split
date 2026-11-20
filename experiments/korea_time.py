"""K5-K7 (HYPOTHESES.md, 21 Nov 2026): Seoul and Busan over time, 2008-2025, from resident registration counts.

Input (from pipeline/get_korea_mois.py, workflow "Fetch Korea over time"): results/korea_time/mois_age5_<year>12.csv,
emd_<year>.parquet. Every year is shared by area onto the 2025 neighbourhoods so that all years sit on one map.
Output: results/korea_time/{coverage.csv, slopes.csv, k_results.json, panel.csv.gz}
Usage: python experiments/korea_time.py <folder with the downloads>
"""
import json, re, sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
IN = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "results/korea_time")
OUT = ROOT / "results/korea_time"; OUT.mkdir(parents=True, exist_ok=True)
CITY = {"seoul": ("11", (126.9779, 37.5663)), "busan": ("26", (129.0756, 35.1798))}   # City Hall
YEARS = list(range(2008, 2026))
num = lambda s: pd.to_numeric(s.astype(str).str.replace(",", ""), errors="coerce")

def bounds(y, sido):
    g = gpd.read_parquet(IN / f"emd_{y}.parquet")
    if g.geometry.name != "geometry":
        g = g.rename_geometry("geometry")
    g = g[g.sidocd.astype(str) == sido].reset_index(drop=True)
    return g.set_geometry(g.geometry.make_valid())

def read_year(y):
    d = pd.read_csv(IN / f"mois_age5_{y}12.csv", encoding="cp949", dtype=str)
    d["code"] = d["행정구역"].str.extract(r"\((\d{10})\)")[0]
    tot = [c for c in d.columns if re.match(rf"{y}년12월_계_총인구수", c)][0]
    old = [c for c in d.columns if (m := re.match(rf"{y}년12월_계_(\d+)(~\d+세| ?세 ?이상|세이상)", c)) and int(m.group(1)) >= 65]
    out = pd.DataFrame({"code": d.code, "name": d["행정구역"].str.strip(), "pop": num(d[tot]), "p65": sum(num(d[c]) for c in old)})
    return out, old

rows_cov, slopes, panel = [], [], {}
res = {}
for city, (sido, (lon, lat)) in CITY.items():
    B25 = bounds(2025, sido); n = len(B25)
    hall = gpd.GeoSeries(gpd.points_from_xy([lon], [lat]), crs=4326).to_crs(B25.crs).iloc[0]
    cen = B25.geometry.representative_point(); dist = np.asarray(cen.distance(hall)) / 1000
    P = np.zeros((len(YEARS), n)); O = np.zeros((len(YEARS), n))
    for k, y in enumerate(YEARS):
        T, oldcols = read_year(y)
        city_tot = T.loc[T.code == f"{sido}00000000", "pop"].iloc[0]
        dong = T[T.code.str.startswith(sido) & (T.code.str[5:] != "00000")].copy()
        B = bounds(y, sido); B["code"] = B.emdcd.astype(str)
        m = B.merge(dong, on="code", how="inner")
        unmatched = dong[~dong.code.isin(B.code)]
        # share each neighbourhood's people by area onto the 2025 map
        m["a0"] = m.geometry.area; G25 = B25[["geometry"]].copy(); G25["i"] = range(n)
        x = gpd.overlay(m[["code", "pop", "p65", "a0", "geometry"]], G25, how="intersection", keep_geom_type=True)
        w = x.geometry.area / x.a0
        P[k] = np.bincount(x.i, weights=x["pop"] * w, minlength=n); O[k] = np.bincount(x.i, weights=x["p65"] * w, minlength=n)
        rows_cov.append(dict(city=city, year=y, mois_city_total=int(city_tot), neighbourhood_rows=len(dong), matched_to_boundaries=len(m),
                             unmatched=len(unmatched), unmatched_people=int(unmatched["pop"].sum()),
                             people_on_2025_map=int(round(P[k].sum())), share_of_city_total=round(P[k].sum() / city_tot, 4),
                             age_columns_65plus="|".join(c.split("_")[-1] for c in oldcols)))
        print(rows_cov[-1], flush=True)
    S = O / np.maximum(P, 1)
    for k, y in enumerate(YEARS):
        slopes.append(dict(city=city, year=y, slope=spearmanr(S[k], dist).statistic, share65=O[k].sum() / P[k].sum()))
    # K5: change in the slope 2008 -> 2025, block bootstrap over 5 km squares
    xy = np.column_stack([cen.x, cen.y]); blk = pd.Series([f"{int(a // 5000)}_{int(b // 5000)}" for a, b in xy])
    groups = [np.flatnonzero(blk.values == g) for g in blk.unique()]; rng = np.random.default_rng(11)
    d0 = spearmanr(S[-1], dist).statistic - spearmanr(S[0], dist).statistic; bs = []
    for _ in range(2000):
        idx = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        bs.append(spearmanr(S[-1][idx], dist[idx]).statistic - spearmanr(S[0][idx], dist[idx]).statistic)
    bs = np.array(bs)
    k5 = dict(slope_2008=round(float(spearmanr(S[0], dist).statistic), 3), slope_2025=round(float(spearmanr(S[-1], dist).statistic), 3),
              change=round(float(d0), 3), ci=[round(float(np.quantile(bs, .025)), 3), round(float(np.quantile(bs, .975)), 3)],
              p=round(float(min(1, 2 * min((bs <= 0).mean(), (bs >= 0).mean()) + 1 / 2001)), 4))
    # K6: same side of the 65+ median in 2008 and 2025, against rotations of the 2025 map (as the app's timeline)
    I, J = [], []
    sj = gpd.sjoin(B25[["geometry"]], B25[["geometry"]], predicate="touches")
    I, J = sj.index.values, sj.index_right.values
    Ad = np.zeros((n, n)); Ad[I, J] = 1; Ad[J, I] = 1; Mc = np.eye(n) - 1 / n
    vals, vecs = np.linalg.eigh(Mc @ Ad @ Mc); vecs = vecs[:, np.argsort(vals)[::-1]]
    s0, s1 = S[0] > np.median(S[0]), S[-1] > np.median(S[-1]); obs = (s0 == s1).mean()
    f = (S[-1] - S[-1].mean()) / S[-1].std(); c = vecs.T @ f; null = []; rng = np.random.default_rng(7)
    for _ in range(999):
        cr = c.copy()
        for a in range(0, n, 12):
            b = min(a + 12, n); q, _ = np.linalg.qr(rng.normal(size=(b - a, b - a))); cr[a:b] = q @ c[a:b]
        r_ = vecs @ cr; r_ = r_ > np.median(r_); a_ = (r_ == s0).mean(); null.append(max(a_, 1 - a_))
    k6 = dict(same_side=round(float(obs), 3), random_median=round(float(np.median(null)), 3), p=round(float((1 + (np.array(null) >= obs).sum()) / 1000), 4))
    # K7: did the youngest neighbourhoods of 2008 age fastest?
    r7 = spearmanr(S[0], S[-1] - S[0])
    k7 = dict(rho=round(float(r7.statistic), 3), p=round(float(r7.pvalue), 4))
    res[city] = dict(neighbourhoods_2025=n, K5=k5, K6=k6, K7=k7, share65_2008=round(float(O[0].sum() / P[0].sum()), 4), share65_2025=round(float(O[-1].sum() / P[-1].sum()), 4))
    print(city, res[city], flush=True)
    panel[city] = pd.DataFrame({"code": B25.emdcd.astype(str), "name": B25.emdnm, "dist_km": dist.round(2),
                                **{f"pop_{y}": P[k].round(1) for k, y in enumerate(YEARS)}, **{f"p65_{y}": O[k].round(1) for k, y in enumerate(YEARS)}})
pd.DataFrame(rows_cov).to_csv(OUT / "coverage.csv", index=False)
pd.DataFrame(slopes).to_csv(OUT / "slopes.csv", index=False)
pd.concat(panel, names=["city"]).reset_index(level=0).to_csv(OUT / "panel.csv.gz", index=False)
json.dump(res, open(OUT / "k_results.json", "w"), indent=1, ensure_ascii=False)
