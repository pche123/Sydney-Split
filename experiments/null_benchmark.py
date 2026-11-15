"""Which null model tells a real line from a smooth map?  False alarms and power on real city shapes.

    python experiments/null_benchmark.py <city> <cities folder> <n_maps> [out.csv]

Maps WITHOUT a line (false alarms should be 5% at alpha = 0.05):
  stationary    a mix of smooth fields at several scales, averaged over the real areas (the landscape test's own family)
  gradient      a smooth centre-to-edge gradient plus smooth and rough noise (monocentric city; not in any null's family)
  nonstationary fine-grained near the centre, broad further out
  anisotropic   smooth field stretched 3x along one axis
Maps WITH a line (power): the stationary map plus a step of size delta (in field SDs) along a realistic border
(the median split of an independent smooth map).

Tests (all use the same line statistic: border length of the median split, shorter = cleaner):
  perm          shuffle areas
  msr1/2/3      Moran spectral randomisation, singleton / pair / triplet (Wagner & Dray 2015)
  msr12         rotations in blocks of 12 eigenvectors (the variant in the first draft)
  gp1           one smooth field (best of Gaussian / Matern 3/2 / exponential shapes and length scale) + noise, fitted by likelihood
  ms            the multi-scale landscape test (7 length scales + noise, one fit)
  womb          wombling-style: share of total edge contrast carried by the sharpest 10% of borders, against shuffles
"""
import os, sys, time
import numpy as np, pandas as pd, geopandas as gpd
from scipy.stats import norm, rankdata
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.join(HERE, ".."), os.path.join(HERE, "..", "pipeline")]
from linetests.msr import LineTest
from linetests.landscape import GPNull, MultiScaleNull
from cities import CITIES

city, CI, NM = sys.argv[1], sys.argv[2], int(sys.argv[3])
OUT = sys.argv[4] if len(sys.argv) > 4 else os.path.join(HERE, "..", "results", f"null_benchmark_{city}.csv")
B = 199
G = gpd.read_file(f"{CI}/{city}/areas.gpkg").to_crs(CITIES[city]["crs"]).reset_index(drop=True)
z = np.load(f"{CI}/{city}/fields.npz"); I, J, W = z["I"], z["J"], z["W"]
n = len(G); rng = np.random.default_rng(11)
rn = lambda x: norm.ppf((rankdata(x) - 0.5) / len(x))
XY = np.column_stack([G.geometry.representative_point().x, G.geometry.representative_point().y]) / 1000.0   # km
ctr = np.average(XY, axis=0, weights=G.geometry.area)

t0 = time.time()
MS = MultiScaleNull(G.geometry, I, J, W); GP1 = GPNull(G.geometry, I, J, W)
LT = {k: LineTest(n, I, J, W, block=k, seed=k) for k in (1, 2, 3, 12)}
print(f"{city}: {n} areas, setup {time.time() - t0:.0f}s", flush=True)

def matern32(D, ell): r = np.sqrt(3) * D / ell; return (1 + r) * np.exp(-r)
def field_from_cov(C, k=1):
    w, U = np.linalg.eigh(C); return (U * np.sqrt(np.clip(w, 0, None))) @ rng.standard_normal((n, k))
Dc = np.sqrt(((XY[:, None, :] - XY[None, :, :]) ** 2).sum(-1))
dist0 = np.sqrt(((XY - ctr) ** 2).sum(1))

def stationary():
    a = rng.dirichlet(np.ones(len(MS.Ks)) * 0.7); a[-1] *= 0.3       # random mix of scales, little pure noise
    return MS.simulate({"weights": a}, 1, rng)[:, 0]
def gradient():
    g = -dist0 / dist0.std()
    return g + 0.6 * field_from_cov(matern32(Dc, 4.0))[:, 0] + 0.4 * rng.standard_normal(n)
def nonstationary():
    w = np.exp(-dist0 / np.median(dist0))
    return w * field_from_cov(matern32(Dc, 1.0))[:, 0] + (1 - w) * field_from_cov(matern32(Dc, 15.0))[:, 0] + 0.2 * rng.standard_normal(n)
def anisotropic():
    th = rng.uniform(0, np.pi); R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
    Y = (XY - ctr) @ R.T; Y[:, 0] /= 3.0
    D = np.sqrt(((Y[:, None, :] - Y[None, :, :]) ** 2).sum(-1))
    return field_from_cov(matern32(D, 3.0))[:, 0] + 0.3 * rng.standard_normal(n)
def stepped(delta):
    def make():
        f = stationary(); side = MS.simulate({"weights": rng.dirichlet(np.ones(len(MS.Ks)))}, 1, rng)[:, 0]
        return f / f.std() + delta * (side > np.median(side))
    return make
SCEN = {"stationary": stationary, "gradient": gradient, "nonstationary": nonstationary, "anisotropic": anisotropic,
        "step0.5": stepped(0.5), "step1.0": stepped(1.0)}

def cut(F): return LT[1].cut(F)
def womb(F):
    F = F if F.ndim == 2 else F[:, None]; d = np.abs(F[I] - F[J]) * W[:, None]
    k = max(1, len(I) // 10); top = np.sort(d, 0)[-k:].sum(0); return top / d.sum(0)

def tests(f):
    f = rn(f); obs = cut(f)[0]; out = {}
    P = np.column_stack([rng.permutation(f) for _ in range(B)])
    out["perm"] = (1 + (cut(P) <= obs).sum()) / (B + 1)
    for k, lt in LT.items(): out[f"msr{k}"] = (1 + (lt.cut(lt.msr(f, B)) <= obs).sum()) / (B + 1)
    out["gp1"] = GP1.test(f, B, seed=int(rng.integers(1e9)))[0]
    out["ms"] = MS.test(f, B, seed=int(rng.integers(1e9)))[0]
    wo = womb(f)[0]; out["womb"] = (1 + (womb(P) >= wo).sum()) / (B + 1)
    return out

rows = []
if os.path.exists(OUT): rows = pd.read_csv(OUT).to_dict("records")
done = pd.DataFrame(rows).groupby("scenario").size().to_dict() if rows else {}
for sc, make in SCEN.items():
    for k in range(done.get(sc, 0), NM):
        t = time.time(); r = tests(make()); r.update(city=city, scenario=sc, rep=k); rows.append(r)
        if (k + 1) % 25 == 0 or k + 1 == NM:
            pd.DataFrame(rows).to_csv(OUT, index=False)
            d = pd.DataFrame(rows); d = d[d.scenario == sc]
            print(f"{sc:13s} {k + 1:4d} maps ({time.time() - t:.1f}s/map)  reject@0.05: " +
                  " ".join(f"{c}={(d[c] <= 0.05).mean():.2f}" for c in ["perm", "msr1", "msr2", "msr3", "msr12", "gp1", "ms", "womb"]), flush=True)
pd.DataFrame(rows).to_csv(OUT, index=False); print("DONE", city)
