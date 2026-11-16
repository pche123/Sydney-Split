"""Score the Phase 2 predictions (HYPOTHESES.md, P1-P20) with whatever European data is in.

    python experiments/phase2_scoring.py [phase 2 app folder] [out.csv]

Reads (when present): calibrated app files for the European cities (same format as every other city), and the
German census-grid tests (results/phase2/germany/tests.csv). Each prediction is scored by the rule written before the
data were opened; one that its data cannot reach yet is scored "not testable" with the reason, never dropped.
Pooled results use the calibrated pooling of experiments/pooled_calibration.py.
"""
import glob, json, os, sys
import numpy as np, pandas as pd
from scipy.stats import norm

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
APPS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "results", "phase2", "app")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "results", "phase2", "predictions.csv")
NA = "not testable"
C = pd.concat([pd.read_csv(f"{ROOT}/results/phase1/calibrated_benchmark_chicago_{k}.csv") for k in (1, 2)])
z0 = norm.isf(np.clip(C.p_cal.values, 1e-3, 1 - 1e-3)); rng = np.random.default_rng(11)
def pooled(ps):
    ps = np.clip(np.asarray(ps, float), 1e-3, 1 - 1e-3); k = len(ps); Z = norm.isf(ps).sum() / np.sqrt(k)
    S = z0[rng.integers(0, len(z0), (400_000, k))].sum(1) / np.sqrt(k); return Z, (1 + (S >= Z).sum()) / (len(S) + 1)
def holm(p):
    p = np.asarray(p, float); o = np.argsort(p); m = len(p); r = np.empty(m); run = 0
    for k, i in enumerate(o): run = max(run, (m - k) * p[i]); r[i] = min(1, run)
    return r

# lines from app files: (city, line id, group, own p, corrected p, tier, sharp share)
L = []
for f in sorted(glob.glob(f"{APPS}/*.json")):
    d = json.load(open(f)); c = os.path.basename(f)[:-5]
    for l in d["lines"]:
        L.append(dict(city=c, line=l["id"], group=l["group"], p_own=l.get("p_own"), p=l["p"], tier=l["tier"], sharp=bool(l.get("sharp"))))
# German grid lines: Holm within "Homes" per city; money separately
gpath = f"{ROOT}/results/phase2/germany/tests.csv"
if os.path.exists(gpath):
    g = pd.read_csv(gpath); best = g.sort_values("stage").groupby(["city", "line"]).last().reset_index()   # calibrated if run, else quick
    for c, gg in best.groupby("city"):
        homes = gg[gg.line != "money"]
        for (_, r), q in zip(homes.iterrows(), holm(homes.p)):
            L.append(dict(city=c, line=r.line, group="Homes", p_own=r.p, p=q, tier="line" if q <= 0.05 else "gentle", sharp=None))
        for _, r in gg[gg.line == "money"].iterrows():
            L.append(dict(city=c, line="money", group="Money", p_own=r.p, p=r.p, tier=None, sharp=None))
L = pd.DataFrame(L, columns=["city", "line", "group", "p_own", "p", "tier", "sharp"])
rows = []
def add(h, verdict, figure, rule=""): rows.append(dict(id=h, verdict=verdict, figure=figure, rule=rule))
cities = sorted(L.city.unique()); lines = L[L.group != "Money"]
add("P1", NA, "calibrated benchmark on Paris and Berlin not run yet")
add("P2", NA, "scale recovery on Paris and Berlin not run yet")
add("P3", NA, "MSR benchmark on European shapes not run yet")
add("P4", NA, "power study on a European city not run yet")
add("P5", NA, "power study on a European city not run yet")
if len(lines):
    share = (lines.tier == "line").mean()
    add("P6", "held" if share < 0.10 else "failed", f"{(lines.tier == 'line').sum()} of {len(lines)} lines pass ({share:.0%}) in {', '.join(cities)}", "< 10% pass after correction")
for pid, ids, rule in [("P7", ["the-latte-line"], "pooled p <= 0.05"), ("P8", ["the-factory-line", "the-laptop-vs-hard-hat-line", "the-degree-line", "the-bicycle-line"], "at most one pooled p <= 0.05 after Holm")]:
    sub = L[L.line.isin(ids) & L.p_own.notna()]
    if sub.city.nunique() < 3: add(pid, NA, f"needs >= 3 cities with these lines; have {sub.city.nunique()} (venue and work lines need the OpenStreetMap cut and the French, Italian and Spanish census)"); continue
    res = {l: pooled(g.p_own) for l, g in sub.groupby("line")}
    if pid == "P7": Z, p = res["the-latte-line"]; add(pid, "held" if p <= 0.05 else "failed", f"Z = {Z:.2f}, p = {p:.3f}", rule)
    else:
        ph = holm([v[1] for v in res.values()]); n = int((ph <= 0.05).sum()); add(pid, "held" if n <= 1 else "failed", f"{n} of {len(res)} pass", rule)
hs = L[L.line.isin(["flats-vs-houses", "the-renters-line", "the-grey-line"]) & L.p_own.notna()]
if hs.city.nunique() >= 2:
    zs = {l: norm.isf(np.clip(g.p_own, 1e-3, 1 - 1e-3)).sum() / np.sqrt(len(g)) for l, g in hs.groupby("line")}
    add("P9", "held" if all(v <= 1 for v in zs.values()) else ("partly" if sum(v <= 1 for v in zs.values()) >= 2 else "failed"),
        "; ".join(f"{k} Z = {v:.2f} over {hs[hs.line == k].city.nunique()} cities" for k, v in zs.items()), "pooled Z <= 1 for each")
else: add("P9", NA, "needs housing lines in >= 2 cities")
ven = L[L.group.isin(["Food", "Night", "Chains"])]
add("P10", NA if ven.empty else ("held" if ven[ven.tier == "line"].city.nunique() <= 2 else "failed"),
    "venue lines need the OpenStreetMap cut" if ven.empty else f"venue lines pass in {ven[ven.tier == 'line'].city.nunique()} cities", "<= 2 of 10 cities")
sh = L[L.sharp.notna()]
add("P11", NA if sh.empty else ("held" if 1 - sh.sharp.mean() >= 0.9 else "failed"), "sharp-stretch check not run on the grid cities" if sh.empty else f"{(~sh.sharp.astype(bool)).sum()} of {len(sh)} have none", ">= 90% no sharp stretch")
add("P12", NA if sh.empty else "pending", "needs sharp stretches")
mo = L[L.line == "money"]
if len(mo):
    ph = holm(mo.p_own); add("P13", "held" if (ph > 0.05).all() else "failed", f"{len(mo)} cities; lowest p {mo.p_own.min():.3f}, after Holm {ph.min():.3f}", "no city's Money Line passes after Holm across cities")
else: add("P13", NA, "no money variable yet")
add("P14", NA, "needs a Degree or manual-work line; the German grid has neither")
for pid in ["P15", "P16", "P17"]: add(pid, NA, "grammar needs the work and night-out families")
add("P18", NA, "rules need the full line set")
add("P19", "pending", "deviations so far: German areas are 1 km grid cells (no census tracts below districts at grid level); see HYPOTHESES.md")
add("P20", "pending", "scored once the phase is complete")
R = pd.DataFrame(rows); os.makedirs(os.path.dirname(OUT), exist_ok=True); R.to_csv(OUT, index=False)
print(R.to_string(index=False))
