"""S5 (HYPOTHESES.md, 20 Nov 2026): are people moving into hazard zones or out of them, and are the zones ageing faster?

Japan 2000-2020 (census small areas re-cut to today's areas) and Australia 2011-2021 (ABS time series, SA2s).
Usage: python experiments/safety_time.py  ->  results/safety/s5_time.csv
"""
import glob, json, re, sys, tempfile, zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.cluster import KMeans

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "pipeline")]
from cities import CITIES  # noqa: E402

KIT = Path("/home/claude/cities_in/cities")
AU = {"sydney": Path("/tmp/kit_syd"), "melbourne": KIT / "melbourne", "brisbane": KIT / "brisbane", "perth": KIT / "perth", "adelaide": KIT / "adelaide"}
JP = ["osaka", "kyoto", "nagoya", "kobe", "fukuoka", "sapporo", "yokohama"]
clean = lambda s: re.sub(r"[\s　]", "", str(s))

def jp_years(c):
    """{year: DataFrame(pop, p65)} on the app's areas."""
    W = KIT / c; crs = CITIES[c]["crs"]
    G = gpd.read_file(W / "areas.gpkg").to_crs(crs).reset_index(drop=True); n = len(G)
    out = {}
    for y in ["2000", "2005", "2010", "2015"]:
        tmp = tempfile.mkdtemp()
        for z in glob.glob(f"{W}/raw/census/{y}/*.zip"):
            zipfile.ZipFile(z).extractall(tmp)
        age = None
        for f in glob.glob(f"{tmp}/**/tbl*.txt", recursive=True):
            t = pd.read_csv(f, encoding="cp932", dtype=str); lab = [clean(x) for x in t.iloc[0]]; t = t.iloc[1:]
            cols = [c_ for c_ in t.columns if re.match(r"T\d+", c_)]; L = [lab[list(t.columns).index(c_)] for c_ in cols]
            if "６５歳以上" in "|".join(L) and "０～４歳" in "|".join(L):
                v = t[cols].apply(pd.to_numeric, errors="coerce").fillna(0); v.columns = L; v.index = t.KEY_CODE.astype(str).values
                age = pd.DataFrame({"pop": v.iloc[:, 0], "p65": v[[x for x in L if x == "総数６５歳以上"]].sum(1)}).groupby(level=0).first()
        shp = glob.glob(f"{tmp}/**/*.shp", recursive=True)[0]
        g = gpd.read_file(shp); g = g[g.KEY_CODE.astype(str).str.len() >= 9].to_crs(crs)
        g = g[g.geometry.intersects(G.geometry.union_all().buffer(200))].dissolve("KEY_CODE").reset_index()[["KEY_CODE", "geometry"]]
        g = g.merge(age, left_on=g.KEY_CODE.astype(str), right_index=True, how="left").fillna(0); g["a0"] = g.area
        Gi = G[["geometry"]].copy(); Gi["i"] = range(n)
        x = gpd.overlay(g, Gi, how="intersection", keep_geom_type=True); w = x.area / x.a0
        out[y] = x[["pop", "p65"]].mul(w, axis=0).groupby(x.i).sum().reindex(range(n)).fillna(0)
    d = pd.read_csv(ROOT / f"app/public/downloads/{c}_areas.csv")
    out["2020"] = pd.DataFrame({"pop": d.population.values, "p65": (d.population * d.age_65_plus).values})
    return out

def au_years(c):
    W = AU[c]; G = gpd.read_file(W / "areas.gpkg"); code = dict(zip(G.name, G.code.astype(str)))
    D = json.load(open(ROOT / f"app/data/{c}.json", encoding="utf-8"))
    codes = [code.get(a["short"]) or code.get(a["name"].split(",")[0]) for a in D["areas"]]
    T = {}
    for f in sorted(glob.glob(f"{W}/census/TSP_T0*.csv")):
        t = pd.read_csv(f, dtype={"SA2_CODE_2021": str}).set_index("SA2_CODE_2021"); T.update({k: t[k] for k in t.columns})
    T = pd.DataFrame(T)
    out = {}
    for y, cy in (("2011", "C11"), ("2016", "C16"), ("2021", "C21")):
        p = T[f"Tot_persons_{cy}_P"]; p65 = sum(T[f"{k}_{cy}_P"] for k in ("Age_65_74", "Age_75_84", "Age_85ov") if f"{k}_{cy}_P" in T)
        if isinstance(p65, int):
            p65 = sum(T[k] for k in T.columns if re.match(rf"Age_(6[5-9]|[7-9]\d|85)\w*_{cy}_P$", k))
        out[y] = pd.DataFrame({"pop": [p.get(k, np.nan) for k in codes], "p65": [p65.get(k, np.nan) for k in codes]})
    return out, sum(k is None for k in codes)

def growth(Y, s, idx=None):
    """Growth inside the zone (areas weighted by their share of land in it) and outside, first to last census."""
    ys = sorted(Y); a, b = Y[ys[0]], Y[ys[-1]]
    if idx is not None:
        a, b, s = a.iloc[idx], b.iloc[idx], s[idx]
    gi = (b["pop"] * s).sum() / max((a["pop"] * s).sum(), 1e-9) - 1; go = (b["pop"] * (1 - s)).sum() / max((a["pop"] * (1 - s)).sum(), 1e-9) - 1
    oi = (b["p65"] * s).sum() / max((b["pop"] * s).sum(), 1e-9) - (a["p65"] * s).sum() / max((a["pop"] * s).sum(), 1e-9)
    oo = (b["p65"] * (1 - s)).sum() / max((b["pop"] * (1 - s)).sum(), 1e-9) - (a["p65"] * (1 - s)).sum() / max((a["pop"] * (1 - s)).sum(), 1e-9)
    return gi, go, oi, oo

rows = []
for c in (sys.argv[1:] or JP + list(AU)):
    try:
        if c in AU:
            Y, miss = au_years(c)
        else:
            Y, miss = jp_years(c), 0
    except Exception as e:  # noqa: BLE001
        print("skip", c, e); continue
    ok = np.ones(len(next(iter(Y.values()))), bool)
    for y in Y:
        ok &= Y[y]["pop"].notna().values
    for y in Y:
        Y[y] = Y[y].reset_index(drop=True)
    R = json.load(open(ROOT / f"results/safety/{c}.json", encoding="utf-8"))
    D = json.load(open(ROOT / f"app/data/{c}.json", encoding="utf-8"))
    xy = np.array([[a["cx"], a["cy"]] for a in D["areas"]])
    lab = KMeans(20, n_init=4, random_state=7).fit_predict(xy); blocks = [np.where((lab == g) & ok)[0] for g in range(20)]
    rng = np.random.default_rng(7)
    for hz in ("flood", "tsunami", "landslide"):
        if hz not in R["areas"]:
            continue
        s = pd.Series(np.array(R["areas"][hz], float)).fillna(0)
        if (s[ok] > 0).sum() < 5:
            continue
        Yk = {y: v[ok].reset_index(drop=True) for y, v in Y.items()}; sk = s[ok].reset_index(drop=True).values
        gi, go, oi, oo = growth(Yk, sk)
        bs = []
        for _ in range(1000):
            idx = np.concatenate([blocks[i] for i in rng.integers(0, 20, 20)])
            ii = np.searchsorted(np.where(ok)[0], idx)
            r = growth(Yk, sk, ii); bs.append((r[0] - r[1], r[2] - r[3]))
        bs = np.array(bs); d1, d2 = gi - go, oi - oo
        z1 = d1 / bs[:, 0].std(); z2 = d2 / bs[:, 1].std()
        ys = sorted(Y)
        rows.append(dict(city=c, hazard=hz, years=f"{ys[0]}-{ys[-1]}", areas=int(ok.sum()), unmatched=miss,
                         growth_in=round(gi * 100, 1), growth_out=round(go * 100, 1), diff_pts=round(d1 * 100, 1),
                         lo=round(np.percentile(bs[:, 0], 2.5) * 100, 1), hi=round(np.percentile(bs[:, 0], 97.5) * 100, 1), z_growth=round(z1, 2),
                         ageing_in_pts=round(oi * 100, 1), ageing_out_pts=round(oo * 100, 1), z_ageing=round(z2, 2)))
        print(rows[-1], flush=True)
T = pd.DataFrame(rows); T.to_csv(ROOT / ("results/safety/s5_time.csv" if not sys.argv[1:] else "/tmp/s5_partial.csv"), index=False)
for hz, g in T.groupby("hazard"):
    zg = g.z_growth.sum() / np.sqrt(len(g)); za = g.z_ageing.sum() / np.sqrt(len(g))
    print(f"POOLED {hz}: {len(g)} cities, growth Z={zg:.2f} p={2 * norm.sf(abs(zg)):.3f}; ageing Z={za:.2f} p={2 * norm.sf(abs(za)):.3f}")
