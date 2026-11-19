"""Suburb twins: for every area in every city, the most similar areas in other cities.

    python experiments/suburb_twins.py <Sydney signals_sa2.csv> <Sydney areas list with SA2_CODE21, app order>

Each area is described by where it sits within its own city on eight lines (Hi-Vis, Degree, Grey, Living Alone,
Flats vs Houses, Renters, Train vs Car, Latte), each as a within-city normal score. Twins are nearest neighbours in that
space, at most one per other city, needing at least six lines in common. Each twin also carries how many of the
shared lines put both areas on the same side (above or below their own city's middle). Sydney's census lines come from its SA2 signals with the same definitions.
Writes app/public/twins/<city>.json: {area index: [[city, area index, lines on the same side, lines shared], ...]} (top 3 cities).
"""
import glob, json, os, sys
import numpy as np, pandas as pd
from scipy.stats import norm, rankdata
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FEAT = ["the-hi-vis-line", "the-degree-line", "the-grey-line", "the-living-alone-line", "flats-vs-houses", "the-renters-line", "train-vs-car", "the-latte-line"]
def rz(v):
    v = np.asarray(v, float); out = np.full(len(v), np.nan); ok = np.isfinite(v)
    out[ok] = norm.ppf((rankdata(v[ok]) - 0.5) / ok.sum()); return out
X, who = [], []
for f in sorted(glob.glob(os.path.join(ROOT, "app", "data", "*.json"))):
    c = os.path.basename(f)[:-5]; d = json.load(open(f))
    if "lines" not in d or c == "singapore": continue
    L = {l["id"]: l["f"] for l in d["lines"] if l.get("f")}; n = len(d["areas"])
    if c == "sydney":
        S = pd.read_csv(sys.argv[1], dtype={"SA2_CODE_2021": str}).set_index("SA2_CODE_2021").loc[pd.read_csv(sys.argv[2], dtype=str).SA2_CODE21]; g = lambda k: S[k].astype(float).values
        L.update({"the-hi-vis-line": rz(g("labourers") + g("drivers_operators")) - rz(g("managers") + g("professionals")),
                  "the-degree-line": g("university_degree"), "the-grey-line": g("retirees_65plus"),
                  "the-living-alone-line": rz(g("living_alone")) - rz(g("kids_0_14")),
                  "flats-vs-houses": rz(g("apartments")) - rz(g("detached_houses")),
                  "the-renters-line": rz(g("renting_private")) - rz(g("owned_outright") + g("mortgaged")),
                  "train-vs-car": rz(g("train_commute")) - rz(g("drive_to_work"))})
    M = np.column_stack([rz(L[k]) if k in L and len(L[k]) == n else np.full(n, np.nan) for k in FEAT])
    X.append(M); who += [(c, i) for i in range(n)]
X = np.vstack(X); city = np.array([w[0] for w in who]); idx = np.array([w[1] for w in who])
out = {}
for c in np.unique(city):
    me = np.flatnonzero(city == c); other = np.flatnonzero(city != c); res = {}
    for i in me:
        both = np.isfinite(X[i]) & np.isfinite(X[other])
        k = both.sum(1); dd = np.where(both, X[other] - X[i], 0.0); dist = np.sqrt((dd ** 2).sum(1) / np.maximum(k, 1))
        dist[k < 6] = np.inf
        if not np.isfinite(dist).any(): continue
        order = np.argsort(dist); seen, best = set(), []
        fin = np.isfinite(dist).sum()
        for j in order:
            if not np.isfinite(dist[j]): break
            cj = city[other[j]]
            if cj in seen: continue
            seen.add(cj); o = other[j]; ok = np.isfinite(X[i]) & np.isfinite(X[o])
            same = int((np.sign(X[i][ok]) == np.sign(X[o][ok])).sum())
            best.append([cj, int(idx[o]), same, int(ok.sum())])
            if len(best) == 3: break
        res[int(idx[i])] = best
    out[c] = res
    json.dump(res, open(os.path.join(ROOT, "app", "public", "twins", f"{c}.json"), "w"), separators=(",", ":"))
    print(c, len(res), "areas with twins")
