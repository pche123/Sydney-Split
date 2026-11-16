"""Score the pre-registered hypotheses (HYPOTHESES.md) on the held-out Phase 1 cities.

    python experiments/phase1_scoring.py <phase1 app folder> <phase1 per-area folder> [out.csv]

Reads the Phase 1 app files (lines, calibrated p, sharp stretches, chain p-values), results/phase1/* (benchmark,
statistic power, families, rules) and the Phase 0 results for comparisons. Writes one row per hypothesis:
verdict (held / failed / partly / not testable), the figure behind it, and a p-value where a test applies.
Where the table's criterion was loose, the exact rule used here is stated in the "rule" column.
"""
import glob, json, os, sys
import numpy as np, pandas as pd
from scipy.stats import binomtest, spearmanr
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
APP1, DL1 = sys.argv[1], sys.argv[2]
WORK1 = os.environ.get("SPLIT_WORK1", "/home/claude/work_p1")
OUT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "results", "phase1", "hypotheses.csv")
R1 = os.path.join(ROOT, "results", "phase1")
US = ["newyork", "losangeles", "chicago", "sanfrancisco", "washington", "austin", "seattle", "miami"]
NZ = ["auckland", "christchurch"]
P0 = {"au": ["melbourne", "brisbane", "perth", "adelaide"], "jp": ["osaka", "kyoto", "nagoya", "yokohama", "kobe", "fukuoka", "sapporo"],
      "uk": ["london", "manchester", "birmingham", "liverpool", "brighton"]}
FAM = {"Work and class": ["the-hi-vis-line", "the-degree-line", "the-laptop-vs-hard-hat-line", "the-factory-line"],
       "Inner city": ["flats-vs-houses", "the-renters-line", "the-living-alone-line", "train-vs-car", "the-no-car-line", "the-bicycle-line"],
       "Age": ["the-grey-line"], "Night out": ["coffee-vs-alcohol", "drink-out-vs-drink-in"]}
LINE_FAM = {l: f for f, ls in FAM.items() for l in ls}
V11 = ["age_65_plus", "kids_under_15", "living_alone", "detached_houses", "uni_degree", "professionals", "managers",
       "train_commute", "car_commute", "bike_commute", "walk_commute"]

app1 = {os.path.basename(f)[:-5]: json.load(open(f)) for f in sorted(glob.glob(f"{APP1}/*.json"))}
app0 = {c: json.load(open(f"{ROOT}/app/data/{c}.json")) for cs in P0.values() for c in cs}
rows = []
def add(h, verdict, figure, p=None, rule="", n=None):
    rows.append(dict(id=h, verdict=verdict, figure=figure, p=None if p is None else float(p), n=n, rule=rule))
def pct(x): return f"{100 * x:.0f}%"
def binp(k, n, p0, alt): return binomtest(int(k), int(n), p0, alternative=alt).pvalue
NA = "not testable"

# ---------------------------------------------------------------- A. false alarms on the new city shapes
nb = {c: pd.read_csv(f"{R1}/null_benchmark_{c}.csv") for c in ["seattle", "chicago"] if os.path.exists(f"{R1}/null_benchmark_{c}.csv")}
def rate(c, scen, col):
    d = nb[c][nb[c].scenario == scen]; k = int((d[col] <= 0.05).sum()); return k, len(d)
if nb:
    cs = list(nb)
    r = {c: rate(c, "stationary", "ms") for c in cs}
    worst = max(r, key=lambda c: r[c][0] / r[c][1])
    add(1, "held" if all(k / n < 0.08 for k, n in r.values()) else "failed", "; ".join(f"{c} {pct(k / n)} ({k}/{n})" for c, (k, n) in r.items()),
        binp(*r[worst], 0.05, "greater"), f"landscape test, smooth maps with no line; p tests excess over 5% in the worst city ({worst})")
    r = {(c, m): rate(c, "stationary", m) for c in cs for m in ["msr1", "msr2", "msr3"]}
    add(2, "held" if all(k / n > 0.25 for k, n in r.values()) else "failed",
        "; ".join(f"{c} {min(k / n for (c_, m), (k, n) in r.items() if c_ == c):.0%}–{max(k / n for (c_, m), (k, n) in r.items() if c_ == c):.0%}" for c in cs),
        max(binp(k, n, 0.05, "greater") for k, n in r.values()), "all three MSR forms > 25%; p tests excess over 5% (largest of the six)")
    g_msr = {(c, m): rate(c, "gradient", m) for c in cs for m in ["msr1", "msr2", "msr3"]}; g_ms = {c: rate(c, "gradient", "ms") for c in cs}
    ok = all(k / n > 0.70 for k, n in g_msr.values()) and all(k / n < 0.05 for k, n in g_ms.values())
    part = all(k / n < 0.05 for k, n in g_ms.values()) or all(k / n > 0.70 for k, n in g_msr.values())
    add(3, "held" if ok else "partly" if part else "failed",
        "; ".join(f"{c}: MSR {min(k / n for (c_, m), (k, n) in g_msr.items() if c_ == c):.0%}–{max(k / n for (c_, m), (k, n) in g_msr.items() if c_ == c):.0%}, ours {pct(g_ms[c][0] / g_ms[c][1])}" for c in cs),
        None, "gradient maps: every MSR form > 70% and ours < 5%")
    r = {c: rate(c, "nonstationary", "ms") for c in cs}
    vals = [k / n for k, n in r.values()]
    add(4, "held" if all(0.05 <= v <= 0.15 for v in vals) else "failed" if any(v > 0.15 for v in vals) else "partly",
        "; ".join(f"{c} {pct(k / n)}" for c, (k, n) in r.items()), max(binp(k, n, 0.05, "greater") for k, n in r.values()),
        "5–15% held; above 15% failed; below 5% partly (no weak spot seen)")
    allr = {"kyoto": (164, "results/null_benchmark_kyoto.csv"), "melbourne": (307, "results/null_benchmark_melbourne.csv")}
    pts = [(n_, (pd.read_csv(f"{ROOT}/{f}").query("scenario == 'stationary'").ms <= 0.05).mean()) for n_, f in allr.values()]
    pts += [(len(app1[c]["areas"]), k / n) for c, (k, n) in {c: rate(c, "stationary", "ms") for c in cs}.items()]
    rho, p_ = spearmanr([a for a, _ in pts], [b for _, b in pts])
    add(5, "held" if rho < 0 and p_ < 0.05 else "failed" if rho > 0 else "partly", ", ".join(f"{a} areas {pct(b)}" for a, b in sorted(pts)),
        p_, "Spearman over the four benchmarked cities; held needs a negative correlation with p < 0.05", n=len(pts))
    r = {(c, s): rate(c, s, "perm") for c in cs for s in ["stationary", "gradient", "nonstationary", "anisotropic"]}
    add(6, "held" if all(k / n > 0.95 for k, n in r.values()) else "failed", f"{min(k / n for k, n in r.values()):.0%}–{max(k / n for k, n in r.values()):.0%}",
        None, "shuffling areas, every no-line scenario")
else:
    for h in range(1, 7): add(h, NA, "benchmark not run yet")

# ---------------------------------------------------------------- B. which statistic (Seattle)
spf = f"{R1}/stat_power_seattle.csv"
if os.path.exists(spf):
    sp = pd.read_csv(spf); det = lambda bg, j, col: (sp[(sp.background == bg) & (sp.jump == j)][col] <= 0.05).mean()
    g3 = [det(bg, 3.0, c) for bg in ["smooth", "rough"] for c in ["geary", "moran"]]
    add(7, "held" if max(g3) < 0.10 else "failed", f"Geary and Moran at a 3 SD step: {min(g3):.0%}–{max(g3):.0%}", None, "Seattle; < 10% on both backgrounds")
    jr = [det("rough", j, "join") >= det("rough", j, "edge") for j in [2.0, 3.0]]
    add(8, "held" if all(jr) else "failed", "rough background: border " + ", ".join(f"{det('rough', j, 'join'):.0%}" for j in [2.0, 3.0])
        + " vs edge " + ", ".join(f"{det('rough', j, 'edge'):.0%}" for j in [2.0, 3.0]) + " (2 and 3 SD)", None, "Seattle; border count ≥ edge test at 2 and 3 SD")
else:
    add(7, NA, "power study not run yet"); add(8, NA, "power study not run yet")
la = f"{R1}/stat_power_losangeles.csv"
if os.path.exists(la):
    sp = pd.read_csv(la); det = lambda bg, j, col: (sp[(sp.background == bg) & (sp.jump == j)][col] <= 0.05).mean()
    e, j_ = det("smooth", 3.0, "edge"), det("smooth", 3.0, "join")
    add(9, "held" if e > j_ else "failed", f"Los Angeles, smooth background, 3 SD step: edge {pct(e)} vs border {pct(j_)}", rule="Los Angeles as the large low-density city")
else:
    add(9, NA, "power study in Los Angeles not run yet")
rk = f"{R1}/stat_power_seattle_ranked.csv"
if os.path.exists(rk):
    sp = pd.read_csv(rk); det = lambda bg, col: (sp[(sp.background == bg) & (sp.jump == 3.0)][col] <= 0.05).mean()
    pairs = [(bg, det(bg, "edge"), det(bg, "edge_ranked")) for bg in ("smooth", "rough")]
    add(10, "held" if all(r <= e / 2 for _, e, r in pairs) else "failed", "; ".join(f"{bg}: edge {pct(e)} standardised vs {pct(r)} ranked" for bg, e, r in pairs),
        rule="edge test at a 3 SD step, Seattle; held if ranking halves detection on both backgrounds (the sharpest-border test has too little power to judge)")
else:
    add(10, NA, "the ranked versions of the jump tests were not rerun")

# ---------------------------------------------------------------- C. which lines are real
def kind(l): return l.get("kind") or {"Chains": "chain", "Food": "records", "Night": "records"}.get(l["group"], "census")
def lines(apps, kinds=None): return [(c, l) for c, d in apps.items() for l in d["lines"] if kinds is None or kind(l) in kinds]
L1 = lines(app1); passes = [(c, l) for c, l in L1 if l.get("tier") == "line"]
cal_ok = all(d["meta"].get("calibrated") for d in app1.values())
add(11, "held" if len(passes) / len(L1) < 0.10 else "failed", f"{len(passes)} of {len(L1)} ({pct(len(passes) / len(L1))})",
    binp(len(passes), len(L1), 0.10, "less"), "p tests whether the pass rate is below 10%" + ("" if cal_ok else "; some cities not double-checked yet"), n=len(L1))
work = {c for c, l in passes if l["id"] in ("the-factory-line", "the-hi-vis-line")}
add(12, "held" if len(work) >= 2 else "failed", f"{len(work)} cities: {', '.join(sorted(work)) or 'none'}")
bike_c = [c for c in ["seattle", "sanfrancisco", "christchurch"] if c in app1]
bike = {c for c, l in passes if l["id"] == "the-bicycle-line"}
add(13, "held" if bike & set(bike_c) else "failed", f"passes in {', '.join(sorted(bike)) or 'no city'}; candidates tested: {', '.join(bike_c)}")
ah = {c for c, l in passes if l["id"] in ("the-grey-line", "the-living-alone-line", "the-renters-line")}
add(14, "held" if len(ah) <= 1 else "failed", f"{len(ah)} cities: {', '.join(sorted(ah)) or 'none'}")
ven = {c for c, l in passes if kind(l) == "records"}
add(15, "held" if len(ven) <= 2 else "failed", f"venue lines pass in {len(ven)} cities: {', '.join(sorted(ven)) or 'none'}")
us_rate = sum(1 for c, l in passes if c in US) / len([c for c in US if c in app1])
add(16, "held" if us_rate > 5 / 8 else "failed", f"{us_rate:.2f} passes per US city vs 0.63 per Japanese city")
bf = f"{R1}/borough_newyork.csv"
if os.path.exists(bf):
    from scipy.stats import fisher_exact
    b = pd.read_csv(bf); cw = b[b.unit == "New York City"]; bw = b[b.unit != "New York City"]
    k1, n1, k2, n2 = int((bw.p <= 0.05).sum()), len(bw), int((cw.p <= 0.05).sum()), len(cw)
    add(17, "held" if k1 / n1 > k2 / n2 else "failed", f"inside one borough {k1} of {n1} ({pct(k1 / n1)}); whole city {k2} of {n2} ({pct(k2 / n2)})",
        fisher_exact([[k1, n1 - k1], [k2, n2 - k2]], alternative="greater")[1], "same single-fit test, uncorrected; Fisher's exact test, one-sided")
else:
    add(17, NA, "within-borough tests for New York not run yet")
if "singapore" in app1:
    sgp = [l["name"] for c, l in passes if c == "singapore"]
    add(18, "held" if not sgp else "failed", f"{len(sgp)} passes" + (f": {', '.join(sgp)}" if sgp else ""))
else:
    add(18, NA, "Singapore not built")

# ---------------------------------------------------------------- D. sharp or gradual
Ls = [(c, l) for c, l in L1 if "sharp" in l]
if Ls:
    ns = sum(1 for _, l in Ls if len(l["sharp"]) > 0)
    add(19, "held" if 1 - ns / len(Ls) >= 0.90 else "failed", f"{len(Ls) - ns} of {len(Ls)} lines have none ({pct(1 - ns / len(Ls))})", n=len(Ls))
    sh = [l["sharp_share"] for _, l in Ls if len(l["sharp"]) > 0]
    add(20, "held" if sh and max(sh) < 0.15 else "failed" if sh else NA, f"{min(sh):.0%}–{max(sh):.0%} of the line" if sh else "no sharp stretches")
    Lu = [(c, l) for c, l in Ls if c in US]; nu = sum(1 for _, l in Lu if len(l["sharp"]) > 0)
    add(22, "held" if nu / len(Lu) > max(1 / 57, 2 / 119) else "failed", f"US {nu} of {len(Lu)} ({nu / len(Lu):.1%}) vs Australia 1.8%, Japan 1.7%")
else:
    for h in (19, 20, 22): add(h, NA, "sharp stretches not computed yet")
add(21, NA, "barrier check against OpenStreetMap roads and rail not run yet")

# ---------------------------------------------------------------- E. families
def corr_by_city(apps):
    out = []
    for c, d in apps.items():
        F = {l["id"]: np.asarray(l["f"], float) for l in d["lines"] if l.get("f") and (l["id"] in LINE_FAM or l["id"] == "the-latte-line")}
        ids = sorted(F)
        if len(ids) < 4: continue
        M = np.corrcoef(np.vstack([F[i] for i in ids])); out.append(pd.DataFrame(M, index=ids, columns=ids))
    return out
C1 = [m for m in corr_by_city({c: app1[c] for c in US if c in app1})]
if C1:
    ids = sorted(set().union(*[set(m.index) for m in C1]) - {"the-latte-line"})
    R = sum(m.reindex(index=ids, columns=ids).abs().fillna(0) for m in C1) / sum(m.reindex(index=ids, columns=ids).notna().astype(float) for m in C1)
    D = 1 - R.values; np.fill_diagonal(D, 0)
    cl = fcluster(linkage(squareform(D, checks=False), "average"), 4, "maxclust")
    match = 0
    for k in set(cl):
        mem = [ids[i] for i in range(len(ids)) if cl[i] == k]; fams = [LINE_FAM[m] for m in mem]
        match += max(fams.count(f) for f in set(fams))
    add(23, "held" if match / len(ids) >= 0.60 else "failed", f"{match} of {len(ids)} lines ({pct(match / len(ids))}) land in their Phase 0 family",
        rule="average of |r| between line scores over US cities, average linkage, 4 clusters; each cluster counted for its majority family")
    fam_r = lambda a, b: np.nanmean([R.loc[x, y] for x in FAM[a] for y in FAM[b] if x in R.index and y in R.index and x != y])
    lat = []
    for m in C1:
        if "the-latte-line" in m.index:
            lat.append({f: np.nanmean([abs(m.loc["the-latte-line", x]) for x in ls if x in m.index]) for f, ls in FAM.items()})
    if lat:
        lm = pd.DataFrame(lat).mean().sort_values(ascending=False)
        add(24, "held" if lm.iloc[0] - lm.iloc[1] < 0.10 else "failed", f"mean |r| with {lm.index[0]} {lm.iloc[0]:.2f}, {lm.index[1]} {lm.iloc[1]:.2f}",
            rule="held if its two closest families are within 0.10 of each other")
    between = {f: np.nanmean([fam_r(f, g) for g in FAM if g != f]) for f in FAM}
    add(26, "held" if min(between, key=between.get) == "Age" else "failed", ", ".join(f"{f} {v:.2f}" for f, v in sorted(between.items(), key=lambda x: x[1])),
        rule="mean |r| between a family's lines and other families' lines; lowest should be Age")
    within = {f: fam_r(f, f) for f in FAM if len([x for x in FAM[f] if x in R.index]) > 1}
    add(27, "held" if max(within, key=within.get) == "Inner city" else "failed", ", ".join(f"{f} {v:.2f}" for f, v in sorted(within.items(), key=lambda x: -x[1])),
        rule="mean |r| within each family; highest should be Inner city")
else:
    for h in (23, 24, 26, 27): add(h, NA, "line scores missing")
ff = f"{R1}/families.csv"
if os.path.exists(ff):
    fr = pd.read_csv(ff); fr = fr[fr.city.isin(US + NZ)]
    k = int((fr.p <= 0.05).sum())
    add(25, "held" if k / len(fr) <= 0.10 else "failed", f"{k} of {len(fr)} family tests pass ({pct(k / len(fr))})", binp(k, len(fr), 0.05, "greater"),
        "p tests excess over 5%", n=len(fr))
else:
    add(25, NA, "family tests not run yet")

# ---------------------------------------------------------------- F. change over time
for h in range(28, 33): add(h, NA, "earlier US survey periods and NZ 2013/2018 were not downloaded for this phase")

# ---------------------------------------------------------------- G. chains
ch = [(c, l) for c, l in L1 if l["group"] == "Chains" and c in US]
def tested(names): return [(c, l) for c, l in ch if l["name"] in names]
burg = tested(["McDonald's vs Burger King", "McDonald's vs Wendy's"])
if burg:
    cities_b = sorted({c for c, _ in burg}); mixed = sorted({c for c, l in burg if l.get("p_mixed", 1) <= 0.05})
    add(33, "held" if len(mixed) >= len(cities_b) / 2 else "failed", f"mixed in {len(mixed)} of {len(cities_b)} US cities with a burger pair ({', '.join(mixed) or 'none'})",
        rule="a city counts if any burger pair is mixed (p ≤ 0.05); no same-type supermarket pair is common to the US cities")
else:
    add(33, NA, "no burger pair has 15+ shops of each chain")
wf = tested(["Whole Foods vs Walmart"])
add(34, ("held" if sum(l["tier"] == "line" for _, l in wf) >= 2 else "partly" if len(wf) < 2 and all(l["tier"] == "line" for _, l in wf) else "failed") if wf else NA,
    f"Whole Foods vs Walmart passes in {sum(l['tier'] == 'line' for _, l in wf)} of {len(wf)} cities tested" if wf else "too few shops in every city")
neu = tested(["CVS vs Walgreens", "Starbucks vs Dunkin'"])
if neu:
    k = sum(1 for _, l in neu if l.get("p_own", 1) > 0.05 and l.get("p_mixed", 1) > 0.05)
    add(35, "held" if k / len(neu) >= 0.8 else "partly" if k / len(neu) >= 0.5 else "failed", f"{k} of {len(neu)} tests neutral",
        rule="neutral = neither split (own p ≤ 0.05) nor mixed; held if at least 80% are neutral")
else:
    add(35, NA, "too few shops")
def spacing_p(city, a, b, R=999):
    """Is each chain's own-shop spacing wider than if the pooled shops were relabelled at random? (one-sided)"""
    import ast, geopandas as gpd
    from scipy.spatial import cKDTree
    sys.path[:0] = [os.path.join(ROOT, "pipeline"), os.path.join(ROOT, "pipeline", "common")]
    from cities import CITIES; from brands import BRANDS_BY_COUNTRY
    C = CITIES[city]; W_ = os.path.join(WORK1, city)
    P = pd.read_csv(f"{W_}/raw/osm/places.csv"); P["t"] = P.tags.map(ast.literal_eval)
    pg = gpd.GeoDataFrame(P, geometry=gpd.points_from_xy(P.lon, P.lat), crs=4326).to_crs(C["crs"])
    am = P.t.map(lambda q: q.get("amenity")); sh = P.t.map(lambda q: q.get("shop")); kind = am.where(am.notna(), sh)
    txt = P.t.map(lambda q: "|".join(str(q.get(k, "")) for k in ("brand", "name", "brand:en", "name:en", "operator")).lower())
    G = gpd.read_file(f"{W_}/areas.gpkg").to_crs(C["crs"]); inmap = G.geometry.union_all().buffer(300)
    xy = np.column_stack([pg.geometry.x, pg.geometry.y]); keep = np.asarray(pg.within(inmap))
    def pts(bn):
        pat, kinds = BRANDS_BY_COUNTRY[C["country"]][bn]; return xy[keep & np.asarray(txt.str.contains(pat, regex=True) & kind.isin(kinds))]
    A, B = pts(a), pts(b); X = np.vstack([A, B]); na = len(A); rng = np.random.default_rng(1)
    def own(lab):
        out = []
        for m in (lab, ~lab):
            Q = X[m]; out.append(cKDTree(Q).query(Q, k=2)[0][:, 1].mean())
        return np.mean(out)
    lab = np.zeros(len(X), bool); lab[:na] = True; obs = own(lab)
    null = np.array([own(np.isin(np.arange(len(X)), rng.permutation(len(X))[:na])) for _ in range(R)])
    return (1 + (null >= obs).sum()) / (R + 1)
mixed_pairs = [(c, l) for c, l in ch if l.get("p_mixed", 1) <= 0.05]
if mixed_pairs:
    res = []
    for c, l in mixed_pairs:
        a, b = l["a"].replace("A ", "", 1).replace(" is closer", ""), l["b"].replace("A ", "", 1).replace(" is closer", "")
        res.append((c, l["name"], spacing_p(c, a, b)))
    k = sum(p_ <= 0.05 for _, _, p_ in res)
    add(36, "held" if k > len(res) / 2 else "partly" if k else "failed", f"own shops spaced out (p ≤ 0.05) in {k} of {len(res)} mixed pairs: "
        + "; ".join(f"{c} {n} p={p_:.3f}" for c, n, p_ in res), rule="mean distance to the nearest shop of the same chain, against random relabelling")
else:
    add(36, NA, "no mixed pairs to check")
prem = [(c, l) for c, l in wf if l["tier"] == "line"]
if prem:
    res = []
    for c, l in prem:
        L_ = {x["id"]: np.asarray(x["side"], bool) for x in app1[c]["lines"]}; s_ = np.asarray(l["side"], bool)
        best = max(((s_ == L_[k]).mean(), k) for k in ["the-degree-line", "the-laptop-vs-hard-hat-line"] if k in L_)
        res.append((c, best))
    add(37, "held" if all(b[0] >= 0.70 for _, b in res) else "failed", "; ".join(f"{c}: matches {b[1].replace('the-', '').replace('-line', '')} on {pct(b[0])}" for c, b in res),
        rule="premium side against the more-graduates or more-IT side")
else:
    add(37, NA, "no premium-vs-budget line passed, so nothing to compare")

# ---------------------------------------------------------------- H. rules
rf = sorted(glob.glob(f"{R1}/rules/rules_*.csv"))
rf = [f for f in rf if os.path.basename(f)[6:-4] in US]
if rf:
    D1 = pd.concat([pd.read_csv(f) for f in rf]); D1 = D1[D1.matches >= 12]
    D0 = pd.read_csv(f"{ROOT}/results/rules/rules_all.csv"); D0 = D0[D0.matches >= 12]
    pr = D1.groupby("city").p_space.apply(lambda p: (p <= 0.05).mean())
    add(38, "held" if pr.min() > 0.08 else "partly" if pr.median() > 0.08 else "failed", f"{pr.min():.0%}–{pr.max():.0%} by city, {(D1.p_space <= 0.05).mean():.0%} overall", n=len(pr))
    allp = pd.concat([D0.groupby("city").p_space.apply(lambda p: (p <= 0.05).mean()), pr])
    na = {c: len(json.load(open(f"{ROOT}/app/data/{c}.json"))["areas"]) for cs in P0.values() for c in cs}
    na.update({c: len(app1[c]["areas"]) for c in pr.index})
    rho, p_ = spearmanr([na[c] for c in allp.index], allp.values)
    add(39, "held" if rho > 0 and p_ < 0.05 else "failed", f"Spearman ρ = {rho:.2f} over {len(allp)} cities", p_, n=len(allp))
    cc0 = pd.read_csv(f"{ROOT}/results/rules/rules_country_consistent.csv")
    tr = lambda R_, D_: ((D_[D_.rule.isin(R_)].p_space <= 0.05) & (D_[D_.rule.isin(R_)].excess > 0)).mean() if len(D_[D_.rule.isin(R_)]) else np.nan
    t_au, t_uk = tr(set(cc0[cc0.country == "au"].rule), D1), tr(set(cc0[cc0.country == "uk"].rule), D1)
    add(40, "held" if max(t_au, t_uk) < 0.35 else "failed", f"Australian rules {pct(t_au)}, English rules {pct(t_uk)} of US tests")
    ccf = f"{R1}/rules/rules_country_consistent.csv"
    if os.path.exists(ccf):
        cc1 = pd.read_csv(ccf); Ru = set(cc1[cc1.country == "us"].rule)
        a_, j_ = tr(Ru, D0[D0.country == "au"]), tr(Ru, D0[D0.country == "jp"])
        add(41, "held" if a_ > j_ else "failed", f"{len(Ru)} US rules: {pct(a_)} into Australia, {pct(j_)} into Japan")
        into = {"jp": [tr(set(cc0[cc0.country == "au"].rule), D0[D0.country == "jp"]), tr(set(cc0[cc0.country == "uk"].rule), D0[D0.country == "jp"]), j_],
                "au": [tr(set(cc0[cc0.country == "uk"].rule), D0[D0.country == "au"]), a_],
                "uk": [tr(set(cc0[cc0.country == "au"].rule), D0[D0.country == "uk"]), tr(Ru, D0[D0.country == "uk"])],
                "us": [t_au, t_uk]}
        m_ = {k: np.nanmean(v) for k, v in into.items()}
        add(43, "held" if min(m_, key=m_.get) == "jp" else "failed", ", ".join(f"into {k.upper()} {pct(v)}" for k, v in sorted(m_.items(), key=lambda x: x[1])),
            rule="mean transfer rate of other countries' consistent rules into each country")
    else:
        add(41, NA, "US consistent rules not computed"); add(43, NA, "US consistent rules not computed")
    w = D1[D1.rule == 214]
    k = int(((w.p_space <= 0.05) & (w.excess > 0)).sum())
    add(44, "held" if len(w) and k >= len(w) / 2 else "failed", f"holds in {k} of {len(w)} US cities where at least 12 areas match")
else:
    for h in (38, 39, 40, 41, 43, 44): add(h, NA, "rules not run yet")
rnz = sorted(glob.glob(f"{R1}/rules_nz/rules_*.csv")); rnz = [f for f in rnz if os.path.basename(f)[6:-4] in NZ]
if rnz:
    Dn = pd.concat([pd.read_csv(f) for f in rnz]); Dn = Dn[Dn.matches >= 12]
    cc0 = pd.read_csv(f"{ROOT}/results/rules/rules_country_consistent.csv"); Ra = set(cc0[cc0.country == "au"].rule)
    sub = Dn[Dn.rule.isin(Ra)]; k = int(((sub.p_space <= 0.05) & (sub.excess > 0)).sum())
    add(42, "held" if len(sub) and k / len(sub) > 0.5 else "failed", f"Australian rules pass in {k} of {len(sub)} New Zealand tests ({pct(k / len(sub)) if len(sub) else '–'})")
else:
    add(42, NA, "New Zealand rules not run")

# ---------------------------------------------------------------- I. sister cities (fingerprints)
def fp(tab):
    t = tab[V11].dropna(); r = t.rank().corr().values; return r[np.triu_indices(len(V11), 1)]
FP, SIZE, CTRY = {}, {}, {}
for k, cs in P0.items():
    for c in cs:
        t = pd.read_csv(f"{ROOT}/app/public/downloads/{c}_areas.csv")
        if all(v in t for v in V11): FP[c] = fp(t); SIZE[c] = t.population.sum() if "population" in t else np.nan; CTRY[c] = k
for c in US + NZ:
    f = f"{DL1}/{c}_areas.csv"
    if os.path.exists(f):
        t = pd.read_csv(f)
        if all(v in t for v in V11): FP[c] = fp(t); SIZE[c] = sum(a.get("pop", 0) for a in app1[c]["areas"]) or np.nan; CTRY[c] = "nz" if c in NZ else "us"
dist = lambda a, b: float(np.sqrt(np.mean((FP[a] - FP[b]) ** 2)))
pairs = [(a, b) for i, a in enumerate(FP) for b in list(FP)[i + 1:]]
newc = [c for c in FP if CTRY[c] == "us"]
if newc:
    best = min((dist(c, s), c, s) for c in FP if CTRY[c] in ("us", "nz") for s in ["sapporo", "brighton"] if s in FP)
    add(46, "held" if best[0] < 0.25 else "failed", f"closest: {best[1]}–{best[2]} at {best[0]:.2f}")
    near = {c: min((dist(c, o), o) for o in FP if o != c)[1] for c in newc}
    k = sum(CTRY[o] == "us" for o in near.values())
    add(48, "held" if k > len(newc) / 2 else "failed", f"{k} of {len(newc)} US cities: " + ", ".join(f"{c}→{o}" for c, o in near.items()))
    sz = [(abs(np.log(SIZE[a]) - np.log(SIZE[b])), dist(a, b)) for a, b in pairs if np.isfinite(SIZE.get(a, np.nan)) and np.isfinite(SIZE.get(b, np.nan)) and SIZE[a] > 0 and SIZE[b] > 0]
    if len(sz) > 10:
        rho, p_ = spearmanr([x for x, _ in sz], [y for _, y in sz])
        add(45, "held" if rho > 0 and p_ < 0.05 else "failed", f"Spearman ρ = {rho:.2f} over {len(sz)} pairs", p_,
            "size difference (log population) against fingerprint distance; pairs share cities, so the p-value is optimistic", n=len(sz))
    else:
        add(45, NA, "city sizes missing")
else:
    for h in (45, 46, 48): add(h, NA, "fingerprints missing")
if "auckland" in FP:
    near = sorted((dist("auckland", o), o) for o in FP if o != "auckland" and CTRY[o] != "nz")
    add(47, "held" if CTRY[near[0][1]] == "au" else "failed", f"nearest: {near[0][1]} ({near[0][0]:.2f}), then {near[1][1]} ({near[1][0]:.2f})",
        rule="nearest city in another country; held if it is Australian")
else:
    add(47, NA, "Auckland fingerprint missing")

# ---------------------------------------------------------------- J. scale
TR = os.environ.get("SPLIT_TRACT_APPS", "/tmp/p1tract")
tc = [c for c in ["seattle", "austin", "washington", "sanfrancisco"] if os.path.exists(f"{TR}/{c}.json") and json.load(open(f"{TR}/{c}.json"))["meta"].get("calibrated")]
if tc:
    ch_, tot_, real_ = 0, 0, []
    for c in tc:
        A = {l["id"]: l["tier"] for l in app1[c]["lines"] if l["group"] != "Chains"}
        B = {l["id"]: l["tier"] for l in json.load(open(f"{TR}/{c}.json"))["lines"] if l["group"] != "Chains"}
        for k in A.keys() & B.keys():
            tot_ += 1; ch_ += A[k] != B[k]
            if A[k] == "line": real_.append((c, k, B[k]))
    add(49, "held" if ch_ / tot_ < 0.20 else "failed", f"{ch_} of {tot_} verdicts change at tract level ({pct(ch_ / tot_)}; {', '.join(tc)})")
    add(50, ("held" if all(t != "chance" for *_, t in real_) else "failed") if real_ else NA,
        "; ".join(f"{c} {k}: {t} at tract level" for c, k, t in real_) if real_ else "no census line passed in these cities at merged level")
    add(51, NA, "needs both levels in many cities; four cities are too few")
else:
    for h in (49, 50, 51): add(h, NA, "tract-level rebuild not finished")

# ---------------------------------------------------------------- K. new questions
add(52, NA, "income table (B19013) was not downloaded")
nc = {c: next((l["tier"] for l in app1[c]["lines"] if l["id"] == "the-no-car-line"), None) for c in ["newyork", "sanfrancisco", "washington"] if c in app1}
k = sum(t == "line" for t in nc.values())
add(53, "held" if k == len(nc) else "partly" if k else "failed", ", ".join(f"{c}: {t}" for c, t in nc.items()))
add(54, NA, "commute-time table was not downloaded")
ag = []
for c in US:
    if c not in app1: continue
    sig = {s["id"]: np.asarray([np.nan if v is None else v for v in s["v"]], float) for s in app1[c]["make"]["signals"]}
    if not all(k_ in sig for k_ in ["work_from_home", "uni_degree", "train_commute"]): continue
    side = lambda x: x > np.nanmedian(x)
    w_, d_, t_ = side(sig["work_from_home"]), side(sig["uni_degree"]), side(sig["train_commute"])
    ag.append(((w_ == d_).mean(), (w_ == t_).mean()))
if ag:
    dd, tt = np.mean([a for a, _ in ag]), np.mean([b for _, b in ag])
    add(55, "held" if dd > tt else "failed", f"work-from-home side matches Degree on {pct(dd)}, Train on {pct(tt)} of areas (mean over {len(ag)} cities)")
add(56, NA, "estate boundaries not available as a map layer")

# ---------------------------------------------------------------- added during Phase 1: pooling across cities
pf = os.path.join(ROOT, "results", "pooled_lines.csv")
if os.path.exists(pf):
    PL = pd.read_csv(pf).set_index("line")
    four = ["the-factory-line", "the-laptop-vs-hard-hat-line", "the-degree-line", "the-bicycle-line"]
    got = [(PL.loc[l, "name"], PL.loc[l, "p1_cities"], PL.loc[l, "p1_Z"], PL.loc[l, "p1_p_holm"]) for l in four if l in PL.index]
    k = sum(pp <= 0.05 for *_, pp in got)
    add(59, "held" if k == 4 else "partly" if k else "failed", "; ".join(f"{n} Z = {z:.1f} over {int(c)} cities" for n, c, z, _ in got),
        max(pp for *_, pp in got), "each line pooled over Phase 1 cities (Stouffer), Holm across lines; p shown is the largest of the four")
    hz = [(PL.loc[l, "name"], PL.loc[l, "p1_Z"]) for l in ["flats-vs-houses", "the-renters-line", "the-grey-line"] if l in PL.index]
    add(60, "held" if all(z <= 0 for _, z in hz) else "partly" if any(z <= 0 for _, z in hz) else "failed", "; ".join(f"{n} Z = {z:.1f}" for n, z in hz))
else:
    add(59, NA, "pooling not run yet"); add(60, NA, "pooling not run yet")

# ---------------------------------------------------------------- L. process
add(57, "partly", "one recorded deviation: US train commuting widened to include light rail (see HYPOTHESES.md)")
d = pd.DataFrame(rows).sort_values("id")
tested_ = d[d.verdict != NA]; fail = (tested_.verdict.isin(["failed", "partly"])).sum()
add(58, "held" if fail >= len(tested_) / 3 else "failed", f"{fail} of {len(tested_)} scored hypotheses failed or partly held")
d = pd.DataFrame(rows).sort_values("id"); os.makedirs(os.path.dirname(OUT), exist_ok=True); d.to_csv(OUT, index=False)
print(d.verdict.value_counts().to_string()); print(f"-> {OUT}")
