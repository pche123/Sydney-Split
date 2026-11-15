"""Explore one city's Split data: a starter script for your own analysis.

    pip install pandas geopandas matplotlib numpy
    python explore_city.py kyoto                 # downloads the data from the site
    python explore_city.py kyoto --col uni_degree

What it does, step by step (each step prints something and/or saves a picture into ./split_<city>/):
  1. Loads the city's table (CSV) and map (GeoJSON) from the site, or from files next to this script.
  2. Data overview: columns by type, missing values, summary numbers.
  3. A map of one column (default: hi-vis jobs, or the first census column).
  4. Its distribution with few vs many histogram bins, plus a KDE: too many bins and you lose the shape.
  5. The same idea on the map: neighbour smoothing (each area averaged with the areas it touches, k times).
  6. Correlations between the census columns (a heat map).
  7. How two lines agree: a cross-table of which side each area is on.
  8. Moran's I, a quick check of "is there any geography at all?", against shuffled maps.

Data: please credit the original sources (ABS / e-Stat / ONS, and OpenStreetMap under ODbL) and cite
Cheema, P. (2026). Is that line real? Calibrated tests for informal urban divides. https://pche123.github.io/Sydney-Split/
HotPepper listings are not in the downloads (their terms don't allow it).
"""
import argparse, os, urllib.request
import numpy as np, pandas as pd, geopandas as gpd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SITE = "https://pche123.github.io/Sydney-Split/downloads"

ap = argparse.ArgumentParser()
ap.add_argument("city", help="e.g. sydney, tokyo, melbourne, kyoto, london, brighton")
ap.add_argument("--col", default=None, help="column to map (default: hivis_jobs if present)")
ap.add_argument("--smooth", type=int, default=3, help="neighbour smoothing steps for step 5")
a = ap.parse_args()
out = f"split_{a.city}"; os.makedirs(out, exist_ok=True)

# 1. load ------------------------------------------------------------------------------------------
def get(name):
    if not os.path.exists(name):
        print("downloading", name); urllib.request.urlretrieve(f"{SITE}/{name}", name)
    return name
tab = pd.read_csv(get(f"{a.city}_areas.csv"))
gdf = gpd.read_file(get(f"{a.city}_areas.geojson"))
print(f"\n{a.city}: {len(tab)} areas, {tab.shape[1]} columns")

# 2. overview --------------------------------------------------------------------------------------
kinds = {"side_": "line sides (1 = orange)", "score_": "line scores (+ = orange)", "count_": "venue counts"}
groups = {k: [c for c in tab if c.startswith(k)] for k in kinds}
census = [c for c in tab.select_dtypes("number") if not any(c.startswith(k) for k in kinds) and c not in ("population", "km2", "code")]
print("census shares:", ", ".join(census))
for k, v in groups.items(): print(f"{kinds[k]}: {len(v)} columns")
miss = tab[census].isna().mean().sort_values(ascending=False)
print("\nmissing values (share of areas):\n", miss[miss > 0].round(3).to_string() if (miss > 0).any() else "none")
print("\nsummary:\n", tab[census].describe().T[["mean", "std", "min", "max"]].round(3).to_string())

col = a.col or ("hivis_jobs" if "hivis_jobs" in tab else census[0])
geo = gdf.merge(tab[["area", col]], on="area", suffixes=("_geo", "")) if col not in gdf else gdf
print(f"\nmapping: {col}")

# 3. map -------------------------------------------------------------------------------------------
proj = geo.to_crs(geo.estimate_utm_crs()); proj["geometry"] = proj.geometry.make_valid()
ax = proj.plot(column=col, cmap="viridis", legend=True, figsize=(8, 8), missing_kwds={"color": "lightgrey"})
ax.set_axis_off(); ax.set_title(f"{a.city}: {col}"); plt.savefig(f"{out}/1_map_{col}.png", dpi=130, bbox_inches="tight"); plt.close()

# 4. histogram bins vs KDE -------------------------------------------------------------------------
v = tab[col].dropna().values
fig, axs = plt.subplots(1, 3, figsize=(13, 3.5))
for ax, bins in zip(axs[:2], [12, 200]):
    ax.hist(v, bins=bins, color="grey"); ax.set_title(f"{bins} bins")
xs = np.linspace(v.min(), v.max(), 300); bw = 1.06 * v.std() * len(v) ** -0.2     # Silverman's rule
kde = np.exp(-0.5 * ((xs[:, None] - v[None]) / bw) ** 2).sum(1) / (len(v) * bw * np.sqrt(2 * np.pi))
axs[2].plot(xs, kde, color="black"); axs[2].set_title(f"KDE (bandwidth {bw:.3g})")
fig.suptitle(f"{col}: too many bins hides the shape"); plt.savefig(f"{out}/2_distribution_{col}.png", dpi=130, bbox_inches="tight"); plt.close()

# 5. neighbour smoothing on the map ---------------------------------------------------------------
nb = gpd.sjoin(proj[["geometry"]].assign(geometry=proj.buffer(20)), proj[["geometry"]], predicate="intersects")   # 20 m slack: simplified shapes have hairline gaps
nb = nb[nb.index != nb.index_right]
x = proj[col].fillna(proj[col].median()).values.astype(float); xs_ = x.copy()
for _ in range(a.smooth):        # each area becomes the average of itself and its neighbours
    m = pd.Series(xs_[nb.index_right.values], index=nb.index).groupby(level=0).mean()
    xs_ = np.array([(xs_[i] + m.get(i, xs_[i])) / 2 for i in range(len(xs_))])
proj["smoothed"] = xs_
fig, axs = plt.subplots(1, 2, figsize=(14, 7))
for ax, c, t in [(axs[0], col, "raw"), (axs[1], "smoothed", f"smoothed ({a.smooth} neighbour steps)")]:
    proj.plot(column=c, cmap="viridis", ax=ax); ax.set_axis_off(); ax.set_title(t)
for ax, c in [(axs[0], col), (axs[1], "smoothed")]:          # draw the median split, the app's "line"
    hi = proj[c] > proj[c].median(); gpd.GeoSeries([proj[hi].buffer(25).union_all().buffer(-25)], crs=proj.crs).boundary.plot(ax=ax, color="black", linewidth=1)
plt.savefig(f"{out}/3_smoothing_{col}.png", dpi=130, bbox_inches="tight"); plt.close()
print(f"smoothing: {int(((x > np.median(x)) != (xs_ > np.median(xs_))).sum())} of {len(x)} areas change side after {a.smooth} steps")

# 6. correlations -----------------------------------------------------------------------------------
cc = tab[census].rank().corr()               # rank (Spearman) correlation: robust to skewed shares
fig, ax = plt.subplots(figsize=(10, 9)); im = ax.imshow(cc, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(census)), census, rotation=90, fontsize=7); ax.set_yticks(range(len(census)), census, fontsize=7)
plt.colorbar(im, shrink=0.7); ax.set_title("Rank correlation between census shares")
plt.savefig(f"{out}/4_correlations.png", dpi=130, bbox_inches="tight"); plt.close()
pairs = cc.where(np.triu(np.ones(cc.shape, bool), 1)).stack().dropna().sort_values()
print("\nmost opposite pair:", pairs.index[0], round(pairs.iloc[0], 2), "| most alike pair:", pairs.index[-1], round(pairs.iloc[-1], 2))

# 7. do two lines agree? ------------------------------------------------------------------------------
sides = groups["side_"]
if len(sides) >= 2:
    s1, s2 = sides[0], sides[1]
    ct = pd.crosstab(tab[s1], tab[s2]); agree = (tab[s1] == tab[s2]).mean()
    print(f"\n{s1} vs {s2}: same side in {max(agree, 1 - agree):.0%} of areas (50% = unrelated)\n{ct}")

# 8. Moran's I with a permutation check ----------------------------------------------------------------
i_, j_ = nb.index.values, nb.index_right.values
def moran(z):
    z = z - z.mean(); return len(z) / len(i_) * (z[i_] * z[j_]).sum() / (z ** 2).sum()
obs = moran(x); rng = np.random.default_rng(1); null = np.array([moran(rng.permutation(x)) for _ in range(999)])
p = (1 + (null >= obs).sum()) / 1000
print(f"\nMoran's I for {col}: {obs:.3f} (shuffled maps: about {null.mean():.3f}); p = {p:.3f}")
print("Note: almost every census map passes this. It says 'there is geography', not 'there is a line'.\n"
      "Telling a line from a smooth slope needs smooth random maps (see the paper), not shuffles.")
print(f"\npictures saved in ./{out}/")
