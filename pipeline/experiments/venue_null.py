"""Smooth-relabel null for venue lines (front vs slope, done at the data level).

For a two-type line (cafes vs fast food, izakaya vs Italian, ...) take the pooled
venues and ask: if the chance that a venue is type A only drifted smoothly across
the city (over ~ell km), would we still see a change this concentrated at the line?

  1. p(x) = smoothed share of type A among pooled venues near x (Gaussian, scale ell,
     done on a 250 m grid for speed).
  2. Each null draw relabels every pooled venue independently: A with prob p(x).
  3. Counts per area are recomputed with exactly the same counting rule as the app
     (Sydney: area + touching areas; Tokyo: 1 km walk radius), then the same
     share / ratio formula, rank-normal transform, median split and statistic.

Because the null data go through the same pipeline, discreteness, small counts,
uneven exposure and the overlap between walk circles are all reproduced."""
import json, sys
import numpy as np, pandas as pd
from scipy import sparse, ndimage
from scipy.spatial import cKDTree
from scipy.stats import norm, rankdata
sys.path.insert(0, "/home/claude/work")
from sharpness import Graph


def rz(v):
    v = pd.Series(v).fillna(pd.Series(v).median()).values
    return norm.ppf((rankdata(v) - 0.5) / len(v))


def smooth_p(xy, y, ell, cell=250.0):
    lo = xy.min(0) - 3 * ell
    ij = ((xy - lo) // cell).astype(int)
    shape = tuple(ij.max(0) + int(3 * ell / cell) + 2)
    A = np.zeros(shape); T = np.zeros(shape)
    np.add.at(A, (ij[:, 0], ij[:, 1]), y); np.add.at(T, (ij[:, 0], ij[:, 1]), 1)
    sA, sT = ndimage.gaussian_filter(A, ell / cell), ndimage.gaussian_filter(T, ell / cell)
    p = (sA[ij[:, 0], ij[:, 1]] + 1e-9) / (sT[ij[:, 0], ij[:, 1]] + 2e-9)
    return np.clip(p, 1e-4, 1 - 1e-4)


class VenueLine:
    """M: sparse (areas x pooled venues) counting matrix; y: 1 = type A.
    make(cA, cB) -> field, using the app's own formula for that line."""
    def __init__(self, G, M, xy, y, make):
        self.G, self.M, self.xy, self.y, self.make = G, M.tocsr(), xy, y.astype(float), make

    def field(self, y):
        cA = self.M @ y; cB = self.M @ (1 - y)
        return self.make(cA, cB)

    def test(self, ell_m, B=999, seed=0, y=None):
        rng = np.random.default_rng(seed)
        y = self.y if y is None else y
        f = self.field(y)
        p = smooth_p(self.xy, y, ell_m)
        Y = (rng.random((len(y), B)) < p[:, None]).astype(float)
        F = np.column_stack([self.make(self.M @ Y[:, b], self.M @ (1 - Y[:, b])) for b in range(B)])
        obs = self.G.stats(f[:, None])[:, 0]
        null = self.G.stats(F)
        pv = (1 + (null >= obs[:, None]).sum(1)) / (B + 1)
        return dict(p=pv, obs=obs, nullmean=null.mean(1), z=(obs - null.mean(1)) / null.std(1), f=f, pfit=p)


# ------------------------------------------------------------------ Tokyo
def tokyo():
    z = np.load("/home/claude/tokyo/out/tokyo_fields.npz"); v = np.load("/home/claude/tokyo/out/tokyo_venues.npz")
    rep = v["rep"]; n = len(rep)
    G = Graph(n, z["I"], z["J"], z["W"], rep=rep)
    def inc(xy):
        nb = cKDTree(xy).query_ball_point(rep, float(v["WALK"]))
        r = np.repeat(np.arange(n), [len(x) for x in nb]); c = np.concatenate([np.asarray(x, int) for x in nb])
        return sparse.csr_matrix((np.ones(len(r)), (r, c)), shape=(n, len(xy)))
    Mv, Mh = inc(v["vxy"]), inc(v["hxy"])
    food = Mv @ v["v_food"].astype(float)
    hp_all = Mh @ np.ones(len(v["hxy"]))
    ratio = lambda a, b: rz((a + 0.5) / (a + b + 1))
    out = {}
    def pooled(src, mA, mB, make, lid):
        M, xy = (Mv, v["vxy"]) if src == "v" else (Mh, v["hxy"])
        keep = mA | mB
        out[lid] = VenueLine(G, M[:, keep], xy[keep], mA[keep], make)
    pooled("v", v["v_cafe"], v["v_fast_food"], lambda a, b: rz((a + 0.5) / (food + 1)) - rz((b + 0.5) / (food + 1)), "the-latte-line")
    pooled("v", v["v_cafe"], v["v_izakaya_bar"], ratio, "coffee-vs-alcohol")
    pooled("v", v["v_ramen"], v["v_soba_udon"], ratio, "ramen-vs-soba")
    pooled("v", v["v_indie_cafe"], v["v_chain_cafe"], ratio, "the-indie-cafe-line")
    pooled("h", v["h_hp_late"], ~v["h_hp_late"], lambda a, b: rz((a + 0.5) / (2 * a + b + 1)), "the-late-night-line")
    pooled("h", v["h_hp_izakaya"], v["h_hp_italian"], ratio, "izakaya-vs-bistro")
    pooled("h", v["h_hp_bar"], v["h_hp_izakaya"], ratio, "bars-vs-izakaya")
    pooled("h", v["h_hp_yakiniku"], ~v["h_hp_yakiniku"], lambda a, b: rz((a + 0.5) / (hp_all + 1)), "the-yakiniku-line")
    # sanity: the rebuilt field must match the app's field
    F = dict(zip(z["ids"], z["F"].T))
    for lid, VL in out.items():
        r = np.corrcoef(VL.field(VL.y), F[lid])[0, 1]
        assert r > 0.999, (lid, r)
    return G, out


# ------------------------------------------------------------------ Sydney
def sydney():
    import geopandas as gpd
    t = pd.read_pickle("/home/claude/work/places.pkl")
    g = gpd.read_file("/home/claude/data/shp/SA2_2021_AUST_GDA2020.shp"); g = g[g.GCC_CODE21 == "1GSYD"].to_crs(7856).reset_index(drop=True)
    d = gpd.GeoDataFrame(t, geometry=gpd.points_from_xy(t.lon, t.lat), crs=4326).to_crs(7856)
    tt = d.t
    am, sh = tt.apply(lambda q: q.get("amenity")), tt.apply(lambda q: q.get("shop"))
    cu = lambda x: tt.apply(lambda q: x in [c.strip() for c in q.get("cuisine", "").split(";")]).values
    br = lambda nm: tt.apply(lambda q: nm in (q.get("brand", "") + "|" + q.get("name", "")).lower()).values
    food = am.isin(["cafe", "fast_food", "restaurant", "pub", "bar", "food_court", "ice_cream"]).values
    eats = am.isin(["fast_food", "restaurant", "food_court"]).values
    sup = sh.eq("supermarket").values
    j = gpd.sjoin(d[["geometry"]], g[["geometry"]], predicate="within")["index_right"]
    j = j[~j.index.duplicated()].reindex(d.index).values
    nb = gpd.sjoin(g[["geometry"]], g[["geometry"]], predicate="touches")
    A = sparse.csr_matrix((np.ones(len(nb)), (nb.index.values, nb.index_right.values)), shape=(len(g), len(g))) + sparse.eye(len(g))
    A.data[:] = 1
    ok = ~np.isnan(j.astype(float))
    P = sparse.csr_matrix((np.ones(ok.sum()), (j[ok].astype(int), np.where(ok)[0])), shape=(len(g), len(d)))
    R = (A @ P).tocsr()                                    # area + touching areas -> venue
    order = pd.read_csv("/home/claude/work/q_classic/areas.csv", dtype=str).SA2_CODE21.values
    pos = pd.Series(np.arange(len(g)), index=g.SA2_CODE21.values)[order].values
    R = R[pos]
    m = json.load(open("/home/claude/work/app_data.json"))["make"]
    rep = np.array(m["rep"], float); G = Graph(m["n"], m["I"], m["J"], m["L"], rep=rep)
    xy = np.column_stack([d.geometry.x, d.geometry.y])
    nfood, neats, nsup = R @ food.astype(float), R @ eats.astype(float), R @ sup.astype(float)
    out = {}
    def pooled(mA, mB, make, lid):
        keep = mA | mB; mA = mA & ~(mA & mB) if False else mA
        out[lid] = VenueLine(G, R[:, keep], xy[keep], mA[keep], make)
    sfood = lambda c: (c + 0.5) / (nfood + 5)
    seats = lambda c: (c + 0.5) / (neats + 5)
    ssup = lambda c: (c + 0.25) / (nsup + 1)
    pooled(am.eq("cafe").values, am.eq("fast_food").values, lambda a, b: rz(sfood(a)) - rz(sfood(b)), "the-latte-line")
    vi, th = cu("vietnamese"), cu("thai")
    pooled(vi & ~th, th & ~vi, lambda a, b: rz(seats(a)) - rz(seats(b)), "pho-vs-pad-thai")
    al, wo = br("aldi") & sup, br("woolworths") & sup
    pooled(al, wo & ~al, lambda a, b: rz(ssup(a)) - rz(ssup(b)), "the-aldi-line")
    bt = cu("bubble_tea") & eats
    pooled(bt, eats & ~bt, lambda a, b: rz(seats(a)), "the-bubble-tea-line")
    return G, out


if __name__ == "__main__":
    B = int(sys.argv[1]) if len(sys.argv) > 1 else 999
    rows = []
    for city, fn in [("Tokyo", tokyo), ("Sydney", sydney)]:
        G, VL = fn()
        for lid, L in VL.items():
            row = dict(city=city, id=lid, venues=len(L.y), share_A=round(L.y.mean(), 3))
            for ell in [2.0, 3.0, 5.0]:
                r = L.test(ell * 1000, B)
                row.update({f"jc_p_{ell:g}": r["p"][0], f"step_p_{ell:g}": r["p"][2], f"rd_p_{ell:g}": r["p"][3]})
                if ell == 3.0: row.update(jc=round(r["obs"][0], 2), jc_if_slope=round(r["nullmean"][0], 2), step_z=round(r["z"][2], 2))
            rows.append(row); print(row, flush=True)
    pd.DataFrame(rows).to_csv("/home/claude/work/venue_sharpness.csv", index=False)
