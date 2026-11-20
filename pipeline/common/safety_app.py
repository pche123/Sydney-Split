"""Turn results/safety/<city>.json (from pipeline/get_safety.py) into the app's safety layer, and run the
pre-registered checks S1, S3 and S4 (HYPOTHESES.md, 20 Nov 2026). S2 is in experiments/safety_lines.py.

Usage: python pipeline/common/safety_app.py [city ...]
Writes app/public/safety/<city>.json and results/safety/findings.csv.
"""
import json, sys
from pathlib import Path

import geopandas as gpd
import numpy as np
from scipy.stats import spearmanr
from sklearn.cluster import KMeans

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))
from cities import CITIES  # noqa: E402

HAZ_SITES = {"flood": ["flood", "inland_flood"], "landslide": ["landslide"], "tsunami": ["tsunami", "storm_surge"]}
LAYERS = [  # id, group, name, kind, what the colour shows
    ("flood", "Hazards", "River flooding", "share", "Share of the land that a 1-in-100-year river flood would cover, from a global model (about 90 m detail) that ignores levees and flood walls"),
    ("landslide", "Hazards", "Landslides", "share", "Share of the land in an official landslide warning zone (土砂災害警戒区域)"),
    ("tsunami", "Hazards", "Tsunami", "share", "Share of the land the prefecture expects a maximum-class tsunami to flood (津波浸水想定)"),
    ("shelter_jp", "Getting help", "Evacuation sites", "rate", "Designated emergency evacuation sites per 1,000 residents"),
    ("assembly", "Getting help", "Assembly points", "rate", "Emergency assembly points per 1,000 residents"),
    ("hospital", "Getting help", "Hospitals", "count", "Hospitals in the area"),
    ("fire", "Getting help", "Fire stations", "count", "Fire stations in the area"),
    ("sight", "Explore", "Sights", "rate", "Museums, galleries, viewpoints, landmarks and historic sites per 1,000 residents"),
]

def svg_affine(c, A):
    """lon/lat -> the app's SVG coordinates: project to the city's CRS, then fit scale and offset on the area points."""
    D = json.load(open(ROOT / f"app/data/{c}.json", encoding="utf-8"))
    crs = CITIES[c]["crs"]; F = A.to_crs(crs); rp = F.geometry.representative_point()
    X, Y = rp.x.values, rp.y.values
    cx = np.array([a["cx"] for a in D["areas"]]); cy = np.array([a["cy"] for a in D["areas"]])
    # x_svg = s*(X - x0), y_svg = s*(y0 - Y): solve for s, x0, y0 by least squares
    M = np.zeros((2 * len(X), 3)); b = np.concatenate([cx, cy])
    M[: len(X), 0] = X; M[: len(X), 1] = -1; M[len(X):, 0] = -Y; M[len(X):, 2] = 1
    (s, sx0, sy0), *_ = np.linalg.lstsq(M, b, rcond=None)
    err = np.median(np.hypot(M[: len(X)] @ [s, sx0, sy0] - cx, M[len(X):] @ [s, sx0, sy0] - cy))
    def to_svg(lon, lat):
        P = gpd.GeoSeries(gpd.points_from_xy(lon, lat), crs=4326).to_crs(crs)
        return np.round(s * P.x.values - sx0, 1), np.round(sy0 - s * P.y.values, 1)
    return D, to_svg, err

MIN_POINTS = {"hospital": 10, "fire": 10}   # other point layers need 30 mapped points

RADIUS = {"hospital": 200.0, "fire": 100.0, "assembly": 50.0, "sight": 40.0}

def dedupe(P, crs):
    """Points of the same kind this close together are one place (a hospital mapped as several buildings); keep a named one."""
    if not P:
        return []
    from scipy.spatial import cKDTree
    G = gpd.GeoSeries(gpd.points_from_xy([p["lon"] for p in P], [p["lat"] for p in P]), crs=4326).to_crs(crs)
    xy = np.column_stack([G.x, G.y]); keep = []
    kinds = np.array([p["k"] for p in P])
    for k in np.unique(kinds):
        idx = np.where(kinds == k)[0]
        if k == "shelter_jp":                         # official list: already one row per site
            keep += idx.tolist(); continue
        tree = cKDTree(xy[idx]); done = np.zeros(len(idx), bool)
        order = sorted(range(len(idx)), key=lambda j: 0 if P[idx[j]].get("n") else 1)
        for j in order:
            if done[j]:
                continue
            grp = tree.query_ball_point(xy[idx[j]], RADIUS.get(k, 50.0)); done[grp] = True; keep.append(idx[j])
    return [P[i] for i in sorted(keep)]

def area_counts(P, A):
    if not P:
        return {}
    G = gpd.GeoDataFrame({"k": [p["k"] for p in P]}, geometry=gpd.points_from_xy([p["lon"] for p in P], [p["lat"] for p in P]), crs=4326)
    j = gpd.sjoin(G, A[["geometry"]].to_crs(4326), predicate="within", how="inner")
    j = j[~j.index.duplicated()]
    return {k: np.bincount(g["index_right"].values, minlength=len(A)) for k, g in j.groupby("k")}

def block_boot(v, side, xy, B=2000, k=20, seed=7):
    """Difference in mean (orange minus blue) with a spatial-block bootstrap 95% interval."""
    lab = KMeans(min(k, len(v) // 5), n_init=4, random_state=seed).fit_predict(xy)
    rng = np.random.default_rng(seed); blocks = [np.where(lab == g)[0] for g in np.unique(lab)]
    d0 = v[side].mean() - v[~side].mean(); ds = []
    for _ in range(B):
        idx = np.concatenate([blocks[i] for i in rng.integers(0, len(blocks), len(blocks))])
        s = side[idx]
        if s.all() or (~s).all():
            continue
        ds.append(v[idx][s].mean() - v[idx][~s].mean())
    lo, hi = np.percentile(ds, [2.5, 97.5])
    return float(d0), float(lo), float(hi)

def city(c, rows):
    R = json.load(open(ROOT / f"results/safety/{c}.json", encoding="utf-8"))
    A = gpd.read_file(ROOT / f"app/public/downloads/{c}_areas.geojson")
    D, to_svg, err = svg_affine(c, A)
    n = len(D["areas"]); assert R["n"] == n, (c, R["n"], n)
    pop = np.maximum(np.array(R["pop"], float), 1); land = np.array(R["land_km2"])
    xy = np.array([[a["cx"], a["cy"]] for a in D["areas"]])
    latte = next((l for l in D["lines"] if "latte" in l["id"]), None)
    out = dict(sources=R["sources"], layers=[], points={}, fit_px=round(float(err), 2))
    # points: merge duplicates (a hospital mapped as several buildings) within 150 m, then count per area
    P = dedupe(R["points"], CITIES[c]["crs"])
    counts = area_counts(P, A)
    if P:
        xs, ys = to_svg([p["lon"] for p in P], [p["lat"] for p in P])
        for p, x, y in zip(P, xs, ys):
            if not (-50 <= x <= 1050 and -50 <= y <= D["h"] + 50):
                continue
            rec = [float(x), float(y), p.get("n", "")]
            if p["k"] == "shelter_jp":
                rec.append("".join(sorted({k[0] for k in p.get("h", [])})))   # f l s e t r i v initials
            out["points"].setdefault(p["k"], []).append(rec)
    for lid, grp, name, kind, what in LAYERS:
        if kind == "share":
            if lid not in R["areas"]:
                continue
            v = np.array(R["areas"][lid], float)
        else:
            cnt = counts.get(lid)
            if cnt is None or cnt.sum() < MIN_POINTS.get(lid, 30):      # too sparsely mapped to say anything (e.g. assembly points outside Japan)
                continue
            cnt = cnt.astype(float); v = cnt / pop * 1000 if kind == "rate" else cnt
        if not np.any(v > 0):
            continue
        L = dict(id=lid, group=grp, name=name, kind=kind, what=what, v=[round(float(x), 4) for x in v])
        order = np.argsort(-v)[:5]
        L["top"] = [[D["areas"][i]["short"], round(float(v[i]), 3)] for i in order if v[i] > 0]
        if kind == "share":
            L["land_pct"] = round(float((v * land).sum() / land.sum() * 100), 1)
            L["people_pct"] = round(float((v * pop).sum() / pop.sum() * 100), 1)    # if people are spread evenly within each area
            L["areas_any"] = int((v > 0.01).sum())
        else:
            L["total"] = int(round(float((v * pop / 1000).sum()))) if kind == "rate" else int(v.sum())
        if latte is not None and kind != "count":
            side = np.array(latte["side"], bool)
            d0, lo, hi = block_boot(v, side, xy)
            L["latte"] = dict(a=round(float(v[side].mean()), 4), b=round(float(v[~side].mean()), 4), lo=round(lo, 4), hi=round(hi, 4))
            rows.append([c, f"S1/S4 {lid}: orange minus blue", round(d0, 4), round(lo, 4), round(hi, 4)])
        out["layers"].append(L)
    # S3: landslide share vs evacuation sites per 1,000 residents (Japan)
    if "landslide" in R["areas"] and "shelter_jp" in counts:
        ls = np.array(R["areas"]["landslide"]); rate = counts["shelter_jp"] / pop * 1000
        rho, p = spearmanr(ls, rate); rows.append([c, "S3 landslide share vs sites per 1,000 (Spearman)", round(float(rho), 3), round(float(p), 4), ""])
        out["s3"] = dict(rho=round(float(rho), 2), p=round(float(p), 4))
    dst = ROOT / f"app/public/safety/{c}.json"; dst.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(c, "fit", out["fit_px"], "px;", [l["id"] for l in out["layers"]], {k: len(v) for k, v in out["points"].items()})

if __name__ == "__main__":
    cs = sys.argv[1:] or sorted(p.stem for p in (ROOT / "results/safety").glob("*.json"))
    rows = []
    for c in cs:
        city(c, rows)
    import csv
    with open(ROOT / "results/safety/findings.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["city", "check", "value", "low_or_p", "high"]); w.writerows(rows)
