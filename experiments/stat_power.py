"""Which statistic notices a real line, when all are judged against the same fitted landscape null?

    python experiments/stat_power.py <city> <cities folder> <n_maps> [out.csv]

Backgrounds (no line):
  smooth   2, 8 and 25 km fields on a 250 m grid, weighted towards the broad one, averaged over areas, + area noise 0.3
           (the design of the paper's first power study)
  rough    a random mix of 0.7-50 km fields + noise (often rough at the scale of a border)
Steps: the two sides of a realistic border (the median split of an independent smooth field) differ by `jump` SDs. Every test fits the landscape to the map it is
given, simulates B maps from the fit, and compares:
  join      border length of the median split (= Geary's C of the two-colour map; the line statistic)
  geary     Geary's C of the continuous map
  moran     Moran's I of the continuous map
  edge      the GLS jump test along the median split (Section 7)
  lgmax     largest local Geary contribution among the borders the line runs along, against the same in replays
"""
import os, sys, time
import numpy as np, pandas as pd, geopandas as gpd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.join(HERE, ".."), os.path.join(HERE, "..", "pipeline")]
from linetests.landscape import MultiScaleNull, edge_stat
from linetests.geary import join_count, geary_c, moran_i, _rn
from cities import CITIES

city, CI, NM = sys.argv[1], sys.argv[2], int(sys.argv[3])
OUT = sys.argv[4] if len(sys.argv) > 4 else os.path.join(HERE, "..", "results", f"stat_power_{city}.csv")
B = 199; rng = np.random.default_rng(21)
G = gpd.read_file(f"{CI}/{city}/areas.gpkg").to_crs(CITIES[city]["crs"]).reset_index(drop=True)
z = np.load(f"{CI}/{city}/fields.npz"); I, J, W = z["I"], z["J"], z["W"]
MS = MultiScaleNull(G.geometry, I, J, W)

from scipy import ndimage
from shapely import contains_xy
x0, y0, x1, y1 = G.total_bounds; cell = 250.0; n = len(G)
gx, gy = np.meshgrid(np.arange(x0, x1, cell), np.arange(y0, y1, cell)); owner = np.full(gx.shape, -1)
for i, g in enumerate(G.geometry): owner[contains_xy(g, gx, gy)] = i
okc = owner >= 0; cnt = np.bincount(owner[okc], minlength=n)
std = lambda x: (x - x.mean(0)) / x.std(0)
def grid_field(scales=(2, 8, 25)):
    zz = sum(ndimage.gaussian_filter(rng.standard_normal(gx.shape), e * 1000 / cell / np.sqrt(2), mode="wrap") * e / 3 for e in scales)
    return std(np.bincount(owner[okc], weights=zz[okc], minlength=n) / np.maximum(cnt, 1))
def background(kind):
    if kind == "smooth": return std(grid_field() + 0.3 * rng.standard_normal(n))
    a = rng.dirichlet(np.ones(len(MS.Ks)) * 0.7); a[-1] *= 0.3
    return std(MS.simulate({"weights": a}, 1, rng)[:, 0])
def make(kind, jump):
    f = background(kind)
    if jump == 0: return f
    b = grid_field(); return f + jump * ((b > np.median(b)) - 0.5)

def lgmax(F):
    F = std(F if F.ndim == 2 else F[:, None]); S = F > np.median(F, 0); out = np.empty(F.shape[1])
    for b in range(F.shape[1]):
        on = S[I, b] != S[J, b]; out[b] = np.max(np.abs(F[I[on], b] - F[J[on], b])) if on.any() else 0
    return out

def tests(f):
    # border statistics use ranks (only the median split matters); jump statistics use standardised values
    fr = _rn(f)[:, 0]; fs = std(f); par = MS.fit(fs); Fs = MS.simulate(par, B, rng); out = {}
    for nm, st, low, x in [("join", lambda F: join_count(F, I, J, W), True, fr), ("geary", lambda F: geary_c(F, I, J, W), True, fs),
                           ("moran", lambda F: moran_i(F, I, J, W), False, fs), ("lgmax", lgmax, False, fs)]:
        o = st(x[:, None])[0]; nl = st(Fs); out[nm] = (1 + ((nl <= o) if low else (nl >= o)).sum()) / (B + 1)
    es = edge_stat(MS, par); o = es(fs[:, None])[0]; nl = es(Fs); out["edge"] = (1 + (nl >= o).sum()) / (B + 1)
    # the same two jump tests on ranks (values and null maps both rank-normalised), to measure the ranking pitfall
    Fr = _rn(Fs)
    o = lgmax(fr[:, None])[0]; out["lgmax_ranked"] = (1 + (lgmax(Fr) >= o).sum()) / (B + 1)
    o = es(fr[:, None])[0]; out["edge_ranked"] = (1 + (es(Fr) >= o).sum()) / (B + 1)
    return out

rows = pd.read_csv(OUT).to_dict("records") if os.path.exists(OUT) else []
done = pd.DataFrame(rows).groupby(["background", "jump"]).size().to_dict() if rows else {}
for kind in ("smooth", "rough"):
    for jump in (0.0, 1.0, 2.0, 3.0):
        for k in range(done.get((kind, jump), 0), NM):
            t = time.time(); r = tests(make(kind, jump)); r.update(city=city, background=kind, jump=jump, rep=k); rows.append(r)
            if (k + 1) % 25 == 0 or k + 1 == NM:
                pd.DataFrame(rows).to_csv(OUT, index=False); d = pd.DataFrame(rows); d = d[(d.background == kind) & (d.jump == jump)]
                print(f"{kind:6s} jump={jump} {k + 1:4d} maps ({time.time() - t:.1f}s/map) reject@0.05: " +
                      " ".join(f"{c}={(d[c] <= 0.05).mean():.2f}" for c in ["join", "geary", "moran", "edge", "lgmax"] + [c for c in ["edge_ranked", "lgmax_ranked"] if c in d]), flush=True)
print("DONE", city)
