"""Phase 3 analysis: line tests, change over time, sister cities, figures (questions Q1-Q5 in HYPOTHESES.md).

    python experiments/phase3_analysis.py

Reads results/phase3/<city>_cells.csv.gz (experiments/phase3_build.py) and the Phase 2 cells and time files.
Writes results/phase3/{tests,slopes,change,sisters}.csv and figures in results/phase3/fig_*.png.
"""
import glob, os, sys
import numpy as np, pandas as pd, geopandas as gpd
from scipy.stats import norm, rankdata, binomtest
from shapely.geometry import box

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path[:0] = [ROOT]
from linetests.landscape import MultiScaleNull
R = os.path.join(ROOT, "results"); OUT = os.path.join(R, "phase3")
COUNTRY = {"amsterdam": "Netherlands", "rotterdam": "Netherlands", "thehague": "Netherlands", "utrecht": "Netherlands",
           "stockholm": "Sweden", "gothenburg": "Sweden", "malmo": "Sweden", "copenhagen": "Denmark", "aarhus": "Denmark",
           "saopaulo": "Brazil"}
NAME = {"thehague": "The Hague", "saopaulo": "São Paulo", "malmo": "Malmö", "losangeles": "Los Angeles", "newyork": "New York",
        "sanfrancisco": "San Francisco"}
nm = lambda c: NAME.get(c, c.capitalize())
rz = lambda v: norm.ppf((rankdata(v) - 0.5) / len(v))
sp = lambda a, b: pd.Series(a).corr(pd.Series(b), method="spearman")


def load(city):
    d = pd.read_csv(os.path.join(OUT, f"{city}_cells.csv.gz"))
    V = {}
    for c in d.columns:
        if c.startswith("num_"):
            var, y = c[4:].rsplit("_", 1); den = d[f"den_{var}_{y}"]
            s = (d[c] / den.where(den > 0)).values
            if np.isfinite(s).mean() > 0.8: V[(var, int(y))] = s
    w = d.ref_pop.values; cx, cy = np.average(d.x + 500, weights=w), np.average(d.y + 500, weights=w)
    return d, V, np.asarray(np.hypot(d.x + 500 - cx, d.y + 500 - cy))   # plain array: Series labels would misalign masked correlations


def neighbours(x, y):
    key = {(a, b): i for i, (a, b) in enumerate(zip(x, y))}
    E = [(i, key[(a + dx, b + dy)]) for i, (a, b) in enumerate(zip(x, y)) for dx, dy in ((1000, 0), (0, 1000)) if (a + dx, b + dy) in key]
    E = np.array(E); return E[:, 0], E[:, 1]


tests, slopes, change = [], [], []
for city in COUNTRY:
    d, V, dist = load(city); I, J = neighbours(d.x.values, d.y.values)
    GN = MultiScaleNull(gpd.GeoSeries([box(a, b, a + 1000, b + 1000) for a, b in zip(d.x, d.y)]), I, J, np.full(len(I), 1000.0), m=9)
    for var in sorted({v for v, _ in V}):
        ys = sorted(y for v, y in V if v == var)
        for y in ys:
            f = V[(var, y)]; ok = np.isfinite(f); slopes.append(dict(city=city, var=var, year=y, slope=sp(f[ok], dist[ok]), cells=int(ok.sum())))
        f = V[(var, ys[-1])]; f = np.where(np.isfinite(f), f, np.nanmedian(f))
        p, obs, nmn, par = GN.test(rz(f + 1e-9 * np.random.default_rng(0).normal(size=len(f))), 199, seed=3)
        tests.append(dict(country=COUNTRY[city], city=city, line=var, year=ys[-1], p=p, cells=len(d), ell_km=par["ell"]))
        if len(ys) > 1:                                   # did it move? block bootstrap of the slope change (5 km squares)
            a, b = V[(var, ys[0])], V[(var, ys[-1])]; ok = np.isfinite(a) & np.isfinite(b)
            blk = (d.x // 5000).astype(str) + "_" + (d.y // 5000).astype(str); groups = [np.flatnonzero((blk == g_).values & ok) for g_ in blk.unique()]
            groups = [g_ for g_ in groups if len(g_)]; obs_c = sp(b[ok], dist[ok]) - sp(a[ok], dist[ok]); rng = np.random.default_rng(11); bs = []
            for _ in range(2000):
                idx = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
                bs.append(sp(b[idx], dist[idx]) - sp(a[idx], dist[idx]))
            bs = np.array(bs)
            change.append(dict(country=COUNTRY[city], city=city, var=var, years=f"{ys[0]}-{ys[-1]}", change=obs_c, per_decade=obs_c / (ys[-1] - ys[0]) * 10,
                               ci_low=np.quantile(bs, .025), ci_high=np.quantile(bs, .975), p=min(1, 2 * min((bs <= 0).mean(), (bs >= 0).mean()) + 1 / 2001)))
    print(city, "done", flush=True)
T = pd.DataFrame(tests)
T["p_holm"] = T.groupby("city").p.transform(lambda s: np.minimum(1, np.maximum.accumulate((s.sort_values() * (len(s) - np.arange(len(s)))).values))[np.argsort(np.argsort(s.values))])
S, C = pd.DataFrame(slopes), pd.DataFrame(change)
m = len(C); C = C.sort_values("p").reset_index(drop=True); C["p_holm"] = np.minimum(1, np.maximum.accumulate(C.p * (m - np.arange(m))))
for n_, df in (("tests", T), ("slopes", S), ("change", C)): df.to_csv(os.path.join(OUT, f"{n_}.csv"), index=False)

# ---------------- Q1: age moves outward, with the 13 Phase 2 cities ----------------
P2 = pd.read_csv(os.path.join(R, "time", "change_test.csv")); P2 = P2[P2["var"] == "grey"][["country", "city", "change"]]
age = pd.concat([P2, C[C["var"] == "grey"][["country", "city", "change"]]])
q1 = binomtest(int((age.change > 0).sum()), len(age), 0.5)
# ---------------- Q2, Q3 ----------------
hous = C[C["var"].isin(["renters", "alone", "hhsize"])]; q2 = (hous.per_decade.abs() < 0.1).mean()
q3 = S[(S["var"] == "alone")].slope.lt(0).mean()
# ---------------- Q4 ----------------
q4 = (T.p_holm <= 0.05).mean()

# ---------------- Q5: sister cities from slope profiles (grey, alone, renters; latest year) ----------------
prof = {}
def add(city, country, fields, dist):
    prof[city] = dict(country=country, **{k: sp(v, dist) for k, v in fields.items()})
for c in ("amsterdam", "rotterdam", "thehague", "utrecht"):
    d, V, dist = load(c); add(c, "Netherlands", {"grey": V[("grey", 2023)], "alone": V[("alone", 2023)], "renters": V[("renters", 2023)]}, dist)
for folder, country, cities in (("germany", "Germany", ("berlin", "munich", "hamburg")), ("es_it", "Spain", ("madrid", "barcelona"))):
    for c in cities:
        g = gpd.read_file(os.path.join(R, "phase2", folder, f"{c}_cells.gpkg")); ce = g.geometry.centroid
        dist = np.hypot(ce.x - np.average(ce.x, weights=g["pop"]), ce.y - np.average(ce.y, weights=g["pop"]))
        add(c, country, {"grey": g["the-grey-line"], "alone": g["the-living-alone-line"], "renters": g["the-renters-line"]}, dist)
for c in ("toronto", "ottawa", "montreal", "calgary", "edmonton"):
    g = gpd.read_file(os.path.join(R, "phase2", "canada", f"{c}_cells.gpkg")); ce = g.geometry.centroid
    dist = np.hypot(ce.x - np.average(ce.x, weights=g["pop"]), ce.y - np.average(ce.y, weights=g["pop"]))
    add(c, "Canada", {"grey": g["the-grey-line"], "alone": g["the-living-alone-line"], "renters": g["the-renters-line"]}, dist)
U = pd.read_csv(os.path.join(R, "time", "us_areas.csv.gz"))
for c, u in U.groupby("city"):
    add(c, "United States", {"grey": u.grey_2020, "alone": u.alone_2020, "renters": u.renters_2020}, u.dist)
P = pd.DataFrame(prof).T; X = P[["grey", "alone", "renters"]].astype(float).values; D = np.linalg.norm(X[:, None] - X[None], axis=2); np.fill_diagonal(D, np.inf)
nearest = D.argmin(1); same = (P.country.values[nearest] == P.country.values).mean()
rng = np.random.default_rng(5); perm = [ (lambda lab: (lab[nearest] == lab).mean())(rng.permutation(P.country.values)) for _ in range(9999)]
q5p = (1 + sum(x >= same for x in perm)) / 10000
P["sister"] = [P.index[j] for j in nearest]; P["distance"] = D.min(1); P.to_csv(os.path.join(OUT, "sisters.csv"))

summary = dict(Q1=f"age slope rose in {int((age.change > 0).sum())} of {len(age)} cities, sign test p = {q1.pvalue:.2g}",
               Q2=f"{q2:.0%} of {len(hous)} housing city-variables changed < 0.1 per decade",
               Q3=f"living alone slope negative in {q3:.0%} of Dutch city-years",
               Q4=f"{(T.p_holm <= 0.05).sum()} of {len(T)} lines pass after Holm ({q4:.0%})",
               Q5=f"nearest sister in same country for {same:.0%} of {len(P)} cities, permutation p = {q5p:.3f}")
pd.Series(summary).to_csv(os.path.join(OUT, "summary.csv"))
print(T.round(3).to_string()); print(C.round(3).to_string()); print(P.round(2).to_string()); print(summary)

# ---------------- figures ----------------
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, networkx as nx
COL = {"Netherlands": "#e8743b", "Germany": "#2f6db3", "Spain": "#c8a23a", "Canada": "#c0392b", "United States": "#5b6770",
       "Sweden": "#1f9e89", "Denmark": "#8e5ea2", "Brazil": "#2e8b57", "Italy": "#7a9a3a"}
G = nx.Graph()
for c in P.index: G.add_node(c)
for i, c in enumerate(P.index):
    for j in np.argsort(D[i])[:2]: G.add_edge(c, P.index[j], w=1 / (D[i, j] + 1e-6))
pos = nx.spring_layout(G, seed=4, weight="w", k=0.6)
fig, ax = plt.subplots(figsize=(9, 7))
nx.draw_networkx_edges(G, pos, ax=ax, alpha=.35)
nx.draw_networkx_nodes(G, pos, ax=ax, node_color=[COL[P.country[c]] for c in G], node_size=420)
nx.draw_networkx_labels(G, pos, {c: nm(c) for c in G}, ax=ax, font_size=8)
for k, v in COL.items():
    if k in set(P.country): ax.scatter([], [], c=v, label=k, s=60)
ax.legend(frameon=False, loc="upper left", fontsize=8); ax.set_axis_off()
ax.set_title("Sister cities: each city joined to the two cities whose old-age, living-alone\nand renting slopes are most like its own", fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_sisters.png"), dpi=160); plt.close(fig)

A = pd.concat([pd.read_csv(os.path.join(R, "time", "change_test.csv")).query("var == 'grey'")[["city", "slope_first", "slope_last", "years"]],
               S[S["var"] == "grey"].groupby("city").apply(lambda s: pd.Series({"slope_first": s.sort_values("year").slope.iloc[0],
                   "slope_last": s.sort_values("year").slope.iloc[-1], "years": f"{s.year.min()}-{s.year.max()}"})).reset_index()])
A = A[A.slope_first != A.slope_last].sort_values("slope_last")
fig, ax = plt.subplots(figsize=(8, 0.33 * len(A) + 1))
for k, r in enumerate(A.itertuples()):
    ax.annotate("", (r.slope_last, k), (r.slope_first, k), arrowprops=dict(arrowstyle="->", color="#c0392b" if r.slope_last > r.slope_first else "#2f6db3", lw=1.6))
    ax.text(-1.45, k, f"{nm(r.city)} ({r.years})", va="center", ha="left", fontsize=8)
ax.axvline(0, color="#999", lw=.8); ax.set_xlim(-1.5, 0.95); ax.set_ylim(-1, len(A)); ax.set_yticks([])
ax.set_xlabel("← over-65s concentrated in the centre        over-65s concentrated at the edge →")
ax.set_title("Where older residents live, first census to last (arrows)", fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_age_front.png"), dpi=160); plt.close(fig)

fig, axs = plt.subplots(2, 2, figsize=(9, 8))
for row, (city, y0, y1) in enumerate((("amsterdam", 2011, 2023), ("saopaulo", 2010, 2022))):
    d, V, _ = load(city)
    for col, y in enumerate((y0, y1)):
        ax = axs[row, col]; v = V[("grey", y)]
        sc = ax.scatter(d.x + 500, d.y + 500, c=rankdata(np.nan_to_num(v, nan=np.nanmedian(v))) / len(v), cmap="RdBu_r", s=55 if city == "amsterdam" else 5, marker="s")
        ax.set_aspect("equal"); ax.set_axis_off(); ax.set_title(f"{nm(city)} {y}: share {'60' if city == 'saopaulo' else '65'}+ (rank)", fontsize=10)
fig.colorbar(sc, ax=axs, shrink=.6, label="older (red) ↔ younger (blue), ranked within each map")
fig.savefig(os.path.join(OUT, "fig_age_maps.png"), dpi=150, bbox_inches="tight"); plt.close(fig)
print("figures written")
