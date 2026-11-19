"""Maps and fun correlations for the plain-language write-up (SYDNEY_SPLIT.md).

    python experiments/fun_figures.py <Sydney signals_sa2.csv>

Reads the app's city files (app/data/*.json: area outlines, each line's side and border) and results/covid/suburbs.csv.
Writes results/fun/*.png and results/fun/numbers.json (every number quoted in FOR_FRIENDS.md).
"""
import json, os, re, sys
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection, LineCollection
from scipy.stats import spearmanr
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); OUT = os.path.join(ROOT, "results", "fun"); os.makedirs(OUT, exist_ok=True)
A, B, E, INK = "#d98e2b", "#3f77a3", "#dcdcd6", "#15191d"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
def subpaths(d):
    out = []
    for part in re.split(r"(?=M)", d):
        pts = [tuple(map(float, p.split(","))) for p in re.findall(r"-?\d+\.?\d*,-?\d+\.?\d*", part)]
        if len(pts) > 1: out.append(pts)
    return out
C = {}
def city(c):
    if c not in C:
        d = json.load(open(os.path.join(ROOT, "app", "data", f"{c}.json")))
        d["_poly"] = [subpaths(a["d"]) for a in d["areas"]]; d["_empty"] = [p for e in d.get("empty", []) for p in subpaths(e["d"])]
        d["_L"] = {l["id"]: l for l in d["lines"]}; C[c] = d
    return C[c]
def draw(ax, c, lid, title=None, colors=None):
    d = city(c); l = d["_L"][lid]
    ax.add_collection(PolyCollection(d["_empty"], facecolors=E, edgecolors="white", linewidths=0.2))
    polys, fc = [], []
    for i, ps in enumerate(d["_poly"]):
        col = colors[i] if colors is not None else (A if l["side"][i] else B)
        for p in ps: polys.append(p); fc.append(col)
    ax.add_collection(PolyCollection(polys, facecolors=fc, edgecolors="white", linewidths=0.25))
    if colors is None and l.get("cut"):
        segs = subpaths(l["cut"]); ax.add_collection(LineCollection(segs, colors="white", linewidths=5)); ax.add_collection(LineCollection(segs, colors=INK, linewidths=2.4))
    allp = np.vstack([np.array(p) for ps in d["_poly"] for p in ps]); x0, y0 = allp.min(0); x1, y1 = allp.max(0)
    ax.set_xlim(x0 - 5, x1 + 5); ax.set_ylim(y1 + 5, y0 - 5); ax.set_aspect("equal"); ax.axis("off")
    if title: ax.set_title(title, fontsize=11, loc="left", fontweight="bold")
N = {}
S = city("sydney"); sig = pd.read_csv(sys.argv[1], dtype={"SA2_CODE_2021": str}).set_index("SA2_CODE_2021")
cov = pd.read_csv(os.path.join(ROOT, "results", "covid", "suburbs.csv"), dtype={"SA2_CODE21": str}); sig = sig.loc[cov.SA2_CODE21]
assert [a["name"] for a in S["areas"]] == list(cov.name)

# 1. six Sydney lines
six = [("the-latte-line", "The Latte Line", "cafés (orange) vs fast food (blue)"), ("the-hi-vis-line", "The Hi-Vis Line", "warehouse & labouring jobs (orange) vs office jobs"),
       ("the-red-rooster-line", "The Red Rooster Line", "a Red Rooster is nearer (orange) vs a Messina"), ("the-small-bar-line", "The Small Bar Line", "small bars (orange) vs pubs"),
       ("the-bubble-tea-line", "The Bubble Tea Line", "more bubble tea (orange)"), ("the-pokies-line", "The Pokies Line", "more poker machines per person (orange)")]
VER = {"line": "real line", "gentle": "real, but a slope", "chance": "could be chance"}
fig, axs = plt.subplots(2, 3, figsize=(15, 10.5), dpi=130)
for ax, (lid, nm, sub) in zip(axs.flat, six):
    draw(ax, "sydney", lid); ax.set_title(f"{nm}\n", fontsize=13, loc="left", fontweight="bold")
    ax.text(0, 1.0, f"{sub} · {VER[S['_L'][lid]['tier']]}", transform=ax.transAxes, fontsize=9.5, color="#555", va="bottom")
fig.suptitle("Six ways to cut Sydney in two", fontsize=18, fontweight="bold", x=0.02, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.96)); fig.savefig(os.path.join(OUT, "sydney_six_lines.png")); plt.close(fig)

# 2. which lines travel together (share of suburbs on the matching side)
ids = ["the-latte-line", "the-hi-vis-line", "the-factory-line", "the-laptop-vs-ute-line", "the-red-rooster-line", "the-small-bar-line", "the-late-night-line",
       "the-bubble-tea-line", "the-aldi-line", "the-pokies-line", "pho-vs-pad-thai", "the-full-house-line"]
lab = ["Cafés", "Hi-vis jobs", "Factory jobs", "Tech jobs (not tradies)", "Red Rooster nearer", "Small bars", "Late-night venues", "Bubble tea", "Aldi (not Woolies)", "Pokies", "Pho (not pad thai)", "Big households"]
sd = np.array([S["_L"][i]["side"] for i in ids], float); M = np.array([[np.mean(a == b) * 100 for b in sd] for a in sd])
fig, ax = plt.subplots(figsize=(10.5, 9), dpi=130)
im = ax.imshow(M, cmap="RdBu_r", vmin=0, vmax=100); ax.set_xticks(range(len(lab))); ax.set_yticks(range(len(lab)))
ax.set_xticklabels(lab, rotation=45, ha="right"); ax.set_yticklabels(lab)
for i in range(len(lab)):
    for j in range(len(lab)):
        ax.text(j, i, f"{M[i, j]:.0f}", ha="center", va="center", fontsize=8.5, color="white" if abs(M[i, j] - 50) > 25 else "black")
ax.set_title("Which Sydney lines travel together?\n% of suburbs on the same side of both lines (50 = unrelated, 0 = mirror images)", loc="left", fontsize=12)
fig.colorbar(im, ax=ax, shrink=0.7); fig.tight_layout(); fig.savefig(os.path.join(OUT, "sydney_line_family.png")); plt.close(fig)
N["agree"] = {f"{lab[i]}|{lab[j]}": round(float(M[i, j]), 1) for i in range(len(lab)) for j in range(i + 1, len(lab))}

# 3. cafés x jobs: four kinds of suburb
lat, hv = np.array(S["_L"]["the-latte-line"]["side"], bool), np.array(S["_L"]["the-hi-vis-line"]["side"], bool)
kinds = {(True, False): ("#b8661a", "Cafés + office jobs"), (False, True): ("#24557d", "Fast food + hi-vis jobs"),
         (True, True): ("#e9b86a", "Cafés + hi-vis jobs (latte tradies)"), (False, False): ("#8fb4d3", "Fast food + office jobs (laptop & nuggets)")}
cols = [kinds[(a, b)][0] for a, b in zip(lat, hv)]
fig, ax = plt.subplots(figsize=(9, 9.5), dpi=130); draw(ax, "sydney", "the-latte-line", colors=cols)
for k, (c, t) in kinds.items(): ax.scatter([], [], s=120, marker="s", color=c, label=f"{t} ({sum((lat == k[0]) & (hv == k[1]))})")
ax.legend(loc="lower left", frameon=False, fontsize=10); ax.set_title("Cafés vs jobs: four kinds of Sydney suburb", loc="left", fontsize=15, fontweight="bold")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "sydney_cafes_x_jobs.png")); plt.close(fig)
N["four_kinds"] = {t: int(sum((lat == k[0]) & (hv == k[1]))) for k, (c, t) in kinds.items()}
N["latte_tradies"] = sorted([a["short"] for a, x, y in zip(S["areas"], lat, hv) if x and y])[:12]
N["laptop_nuggets"] = sorted([a["short"] for a, x, y in zip(S["areas"], lat, hv) if (not x) and (not y)])[:12]

# 4. jokey correlations (Spearman across 300 suburbs)
f = lambda lid: np.array(S["_L"][lid]["f"], float); g = lambda k: sig[k].astype(float).values * 100   # signals are shares
pairs = [(f("the-latte-line"), g("university_degree"), "Cafés vs fast food (score)", "Uni graduates (% of residents)", "More cafés, more degrees"),
         (f("the-small-bar-line"), g("living_alone"), "Small bars vs pubs (score)", "Households of one person (%)", "Small bars where people live alone"),
         (f("the-bubble-tea-line"), g("uni_students"), "Bubble tea shops (score)", "Uni students (% of residents)", "Bubble tea and students: only a little"),
         (f("the-late-night-line"), g("young_adults_20_34"), "Venues licensed past midnight (score)", "People aged 20–34 (%)", "Late nights where the 20-somethings live"),
         (f("the-pokies-line"), g("retirees_65plus"), "Pokies per person (score)", "Over-65s (% of residents)", "Pokies and pensioners? Nope"),
         (cov.hivis.values, cov.delta_per_1000.values, "Hi-vis jobs (score)", "Delta COVID cases per 1,000", "COVID followed the hi-vis jobs")]
fig, axs = plt.subplots(2, 3, figsize=(15, 9.5), dpi=130); N["rho"] = {}
for ax, (x, y, xl, yl, t) in zip(axs.flat, pairs):
    ok = np.isfinite(x) & np.isfinite(y); r = spearmanr(x[ok], y[ok]).statistic; N["rho"][t] = round(float(r), 2)
    ax.scatter(x[ok], y[ok], s=14, color=A if r > 0 else B, alpha=0.7, edgecolor="none")
    ax.set_xlabel(xl); ax.set_ylabel(yl); ax.set_title(f"{t}\nρ = {r:+.2f}", loc="left", fontsize=11.5, fontweight="bold"); ax.spines[["top", "right"]].set_visible(False)
fig.suptitle("Fun correlations across Sydney's 300 suburbs (none of these is cause and effect)", fontsize=15, fontweight="bold", x=0.02, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig(os.path.join(OUT, "sydney_fun_correlations.png")); plt.close(fig)

# 5. the Latte Line around the world
cities = [("sydney", "Sydney"), ("melbourne", "Melbourne"), ("london", "London"), ("tokyo", "Tokyo"), ("newyork", "New York"), ("losangeles", "Los Angeles")]
fig, axs = plt.subplots(2, 3, figsize=(15, 10.5), dpi=130); N["latte_tier"] = {}
for ax, (c, nm) in zip(axs.flat, cities):
    draw(ax, c, "the-latte-line"); t = city(c)["_L"]["the-latte-line"]["tier"]; N["latte_tier"][nm] = t
    ax.set_title(f"{nm}\n", fontsize=13, loc="left", fontweight="bold"); ax.text(0, 1.0, f"cafés (orange) vs fast food · {VER[t]}", transform=ax.transAxes, fontsize=9.5, color="#555", va="bottom")
fig.suptitle("The Latte Line around the world", fontsize=18, fontweight="bold", x=0.02, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.96)); fig.savefig(os.path.join(OUT, "latte_around_the_world.png")); plt.close(fig)

# 6. the Hi-Vis Line around the world
cities2 = [("sydney", "Sydney"), ("melbourne", "Melbourne"), ("london", "London"), ("manchester", "Manchester"), ("osaka", "Osaka"), ("chicago", "Chicago")]
fig, axs = plt.subplots(2, 3, figsize=(15, 10.5), dpi=130); N["hivis_tier"] = {}
for ax, (c, nm) in zip(axs.flat, cities2):
    draw(ax, c, "the-hi-vis-line"); t = city(c)["_L"]["the-hi-vis-line"]["tier"]; N["hivis_tier"][nm] = t
    ax.set_title(f"{nm}\n", fontsize=13, loc="left", fontweight="bold"); ax.text(0, 1.0, f"hi-vis jobs (orange) vs office jobs · {VER[t]}", transform=ax.transAxes, fontsize=9.5, color="#555", va="bottom")
fig.suptitle("The Hi-Vis Line around the world", fontsize=18, fontweight="bold", x=0.02, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.96)); fig.savefig(os.path.join(OUT, "hivis_around_the_world.png")); plt.close(fig)

# 7. COVID Delta rates by suburb
r = cov.delta_per_1000.values; q = np.quantile(r, [0.2, 0.4, 0.6, 0.8]); pal = ["#fde0c5", "#f9b384", "#f07f4f", "#d1452c", "#8f1d1d"]
cols = [pal[int(np.searchsorted(q, v))] for v in r]
fig, ax = plt.subplots(figsize=(9, 9.5), dpi=130); draw(ax, "sydney", "the-latte-line", colors=cols)
segs = subpaths(S["_L"]["the-latte-line"]["cut"]); ax.add_collection(LineCollection(segs, colors="white", linewidths=5)); ax.add_collection(LineCollection(segs, colors=INK, linewidths=2.4))
edges = [0, *q, r.max()]
for k in range(5): ax.scatter([], [], s=120, marker="s", color=pal[k], label=f"{edges[k]:.0f}–{edges[k + 1]:.0f} cases per 1,000")
ax.legend(loc="lower left", frameon=False, title="Delta wave, Jun–Dec 2021", fontsize=9.5)
ax.set_title("Delta COVID cases by suburb, with the Latte Line", loc="left", fontsize=15, fontweight="bold")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "sydney_delta_map.png")); plt.close(fig)
json.dump(N, open(os.path.join(OUT, "numbers.json"), "w"), indent=1, ensure_ascii=False); print(json.dumps({k: N[k] for k in ("four_kinds", "rho", "latte_tier", "hivis_tier", "latte_tradies", "laptop_nuggets")}, indent=1, ensure_ascii=False))
