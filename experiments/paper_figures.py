"""The paper's four figures.

    python experiments/paper_figures.py <sydney work folder> <sydney data folder> [out folder]

1. The Latte Line as a slope (Sydney): café-vs-fast-food score by suburb, with the halfway line.
2. Held-out replication: each line's pooled evidence (Stouffer Z) in the first 18 cities vs the 11 held-out ones.
3. False alarms on maps with no line: shuffling, Moran spectral randomisation, our test (single fit and calibrated).
4. Power: how often a real step of a given size is detected, by statistic, in Los Angeles and Seattle.
"""
import json, os, sys
import numpy as np, pandas as pd, geopandas as gpd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
W_, D = sys.argv[1], sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "results", "figures")
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "font.family": "DejaVu Sans"})
ORANGE, BLUE, GREY, INK = "#d98e2b", "#3f77a3", "#b9b4a8", "#222222"
SLOPE = ["#a8571a", "#d98e2b", "#ecc189", "#efe9dc", "#a9c4dc", "#5e8fb8", "#2f5f87"]

# ---------------------------------------------------------------- 1. Latte Line slope map
app = json.load(open(f"{ROOT}/app/data/sydney.json")); latte = next(l for l in app["lines"] if l["id"] == "the-latte-line")
codes = pd.read_csv(f"{W_}/q_classic/areas.csv", dtype=str).SA2_CODE21.values
sa2 = gpd.read_file(f"{D}/shp/SA2_2021_AUST_GDA2020.shp").to_crs(7856)
G = sa2.set_index("SA2_CODE21").loc[codes].reset_index()
f = np.array(latte["f"]); rk = (pd.Series(f).rank().values - 1) / (len(f) - 1); G["bin"] = 6 - np.minimum(6, np.floor(rk * 7)).astype(int)
assert ((f > np.median(f)) == np.array(latte["side"], bool)).all()
ctx = sa2[(sa2.GCC_CODE21 == "1GSYD") & ~sa2.SA2_CODE21.isin(codes)]
fig, ax = plt.subplots(figsize=(6.4, 6.4))
ctx.plot(ax=ax, color="#e6e3dc", edgecolor="white", linewidth=0.2)
G.plot(ax=ax, column="bin", cmap=ListedColormap(SLOPE), norm=BoundaryNorm(np.arange(-0.5, 7.5), 7), edgecolor="white", linewidth=0.15)
side = np.array(latte["side"], bool); border = []
m = json.load(open(f"{W_}/app_data.json"))["make"]
for i, j in zip(m["I"], m["J"]):
    if side[i] != side[j]:
        b = G.geometry[i].boundary.intersection(G.geometry[j].boundary)
        if not b.is_empty: border.append(b)
gpd.GeoSeries(border, crs=7856).plot(ax=ax, color=INK, linewidth=0.9, linestyle=(0, (3, 2)))
x0, y0, x1, y1 = G.total_bounds; ax.set_xlim(x0 - 2000, x1 + 2000); ax.set_ylim(y0 - 2000, y1 + 2000); ax.set_axis_off()
for k, c in enumerate(SLOPE):
    ax.add_patch(plt.Rectangle((0.04 + k * 0.045, 0.06), 0.045, 0.022, transform=ax.transAxes, color=c, clip_on=False))
ax.text(0.04, 0.09, "more cafés", transform=ax.transAxes, fontsize=8, ha="left", va="bottom")
ax.text(0.355, 0.09, "more fast food", transform=ax.transAxes, fontsize=8, ha="right", va="bottom")
ax.plot([0.04, 0.09], [0.035, 0.035], transform=ax.transAxes, color=INK, linestyle=(0, (3, 2)), linewidth=0.9)
ax.text(0.10, 0.035, "halfway point (not an edge)", transform=ax.transAxes, fontsize=8, va="center")
ax.set_title("Sydney's Latte Line is a slope", loc="left", fontsize=12)
fig.savefig(f"{OUT}/fig1_latte_slope.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# ---------------------------------------------------------------- 2. held-out replication
P = pd.read_csv(f"{ROOT}/results/pooled_lines.csv")
P = P[(P.p0_cities >= 5) & (P.p1_cities >= 5)].copy()
fig, ax = plt.subplots(figsize=(6.2, 4.6))
crit = 1.645
ax.axhline(crit, color=GREY, lw=0.8, ls="--"); ax.axvline(crit, color=GREY, lw=0.8, ls="--")
ax.plot([-3, 6], [-3, 6], color=GREY, lw=0.6)
for r in P.itertuples():
    hi = r.line == "the-latte-line"; gen = r.line in ("the-factory-line", "the-laptop-vs-hard-hat-line", "the-degree-line", "the-bicycle-line")
    col = ORANGE if hi else (BLUE if gen else "#8a8a8a")
    ax.scatter(r.p0_Z, r.p1_Z, s=40 if (hi or gen) else 22, color=col, zorder=3)
    if hi or gen or abs(r.p1_Z) > 1.9:
        ax.annotate(r.name.replace("The ", "").replace(" Line", ""), (r.p0_Z, r.p1_Z), xytext=(5, 3), textcoords="offset points", fontsize=8, color=col)
ax.set_xlabel("Pooled evidence in the first 18 cities (Stouffer Z)"); ax.set_ylabel("Pooled evidence in the 11 held-out cities (Z)")
ax.text(-2.9, crit + 0.08, "one-sided p = 0.05", fontsize=7, color="#777", ha="left")
ax.set_title("Lines that looked general mostly failed to replicate", loc="left", fontsize=11)
ax.set_xlim(-3, 6); ax.set_ylim(-2, 4.2)
fig.savefig(f"{OUT}/fig2_replication.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# ---------------------------------------------------------------- 3. false alarms
rows = []
for c in ["seattle", "chicago"]:
    d = pd.read_csv(f"{ROOT}/results/phase1/null_benchmark_{c}.csv")
    for sc in ["stationary", "gradient", "nonstationary"]:
        g = d[d.scenario == sc]
        rows.append(dict(city=c, sc=sc, shuffle=(g.perm <= 0.05).mean(), msr=(g[["msr1", "msr2", "msr3"]] <= 0.05).mean().mean(), ours=(g.ms <= 0.05).mean()))
B = pd.DataFrame(rows)
cal = pd.concat([pd.read_csv(f"{ROOT}/results/phase1/calibrated_benchmark_chicago_{k}.csv") for k in (1, 2)])
pcol = "p_cal" if "p_cal" in cal else [c for c in cal.columns if "cal" in c][0]
cal_rate = (cal[pcol] <= 0.05).mean(); n_cal = len(cal)
fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.6), sharey=True)
for ax, c in zip(axes, ["seattle", "chicago"]):
    g = B[B.city == c]; x = np.arange(len(g)); w = 0.26
    ax.bar(x - w, g["shuffle"] * 100, w, color=GREY, label="shuffle areas")
    ax.bar(x, g["msr"] * 100, w, color=BLUE, label="Moran spectral randomisation")
    ax.bar(x + w, g["ours"] * 100, w, color=ORANGE, label="our test (quick, single fit)")
    if c == "chicago":
        ax.scatter([0 + w], [cal_rate * 100], marker="D", color=INK, zorder=4, s=28, label=f"our test, calibrated ({n_cal} maps)")
    ax.axhline(5, color=INK, lw=0.8, ls="--"); ax.set_xticks(x); ax.set_xticklabels(["smooth", "gradient", "uneven"]); ax.set_title(c.capitalize(), loc="left")
axes[0].set_ylabel("False alarms on maps with no line (%)"); axes[0].text(2.45, 7, "target 5%", fontsize=7, ha="right")
h1, l1 = axes[1].get_legend_handles_labels(); fig.legend(h1, l1, loc="lower center", ncol=2, frameon=False, fontsize=8, bbox_to_anchor=(0.5, -0.12))
fig.suptitle("Shuffles and MSR call lines that aren't there", x=0.07, y=1.04, ha="left", fontsize=11)
fig.savefig(f"{OUT}/fig3_false_alarms.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# ---------------------------------------------------------------- 4. power
fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.6), sharey=True)
for ax, (c, fn) in zip(axes, [("Los Angeles (401 areas)", "stat_power_losangeles.csv"), ("Seattle (100 areas)", "stat_power_seattle_ranked.csv")]):
    d = pd.read_csv(f"{ROOT}/results/phase1/{fn}")
    for stat, col, lab in [("join", BLUE, "border count"), ("edge", ORANGE, "edge test"), ("edge_ranked", GREY, "edge test on ranked data")]:
        for bg, ls in [("smooth", "-"), ("rough", ":")]:
            g = d[d.background == bg].groupby("jump")[stat].apply(lambda v: (v <= 0.05).mean() * 100)
            ax.plot(g.index, g.values, ls, color=col, marker="o", ms=3, label=f"{lab}, {bg} background")
    ax.axhline(5, color=INK, lw=0.6, ls="--"); ax.set_xlabel("Size of the real step across the border (SD)"); ax.set_title(c, loc="left"); ax.set_xticks([0, 1, 2, 3])
axes[0].set_ylabel("Detected (%)"); h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=3, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, -0.17))
fig.suptitle("Only big steps are visible", x=0.07, y=1.04, ha="left", fontsize=11)
fig.savefig(f"{OUT}/fig4_power.png", dpi=200, bbox_inches="tight"); plt.close(fig)
print("figures ->", OUT, f"(calibrated Chicago false alarms {cal_rate:.1%} of {n_cal})")
