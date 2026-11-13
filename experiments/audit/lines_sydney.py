import os, sys; _H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [_H, os.path.dirname(_H), os.path.join(os.path.dirname(_H), "..")]  # experiments, repo root
from paths import SYD, TOK, RAW  # noqa: E402
"""Sydney venue/licence lines as data-level Line objects (app recipes reproduced)."""
import json
import numpy as np, pandas as pd, geopandas as gpd
from scipy import sparse
from scipy.spatial import cKDTree
from linetests.records import Line, rz, logit_surface, lograte_surface, two_type_line
from linetests.msr import LineTest

PREM = f"{RAW}/premises-list-nov-2026.xlsx"


def build():
    g = gpd.read_file(f"{RAW}/shp/SA2_2021_AUST_GDA2020.shp"); g = g[g.GCC_CODE21 == "1GSYD"].to_crs(7856).reset_index(drop=True)
    popc = pd.read_csv(f"{SYD}/signals_sa2.csv", dtype={"SA2_CODE_2021": str}).set_index("SA2_CODE_2021")["population"]
    gpop = g.SA2_CODE21.map(popc).fillna(0).values.astype(float)
    order = pd.read_csv(f"{SYD}/q_classic/areas.csv", dtype=str).SA2_CODE21.values
    pos = pd.Series(np.arange(len(g)), index=g.SA2_CODE21.values)[order].values      # study area -> row in g
    m = json.load(open(f"{SYD}/app_data.json"))["make"]
    n = m["n"]; T = LineTest(n, m["I"], m["J"], np.array(m["L"]) * 1000, seed=11)
    nb = gpd.sjoin(g[["geometry"]], g[["geometry"]], predicate="touches")
    A = sparse.csr_matrix((np.ones(len(nb)), (nb.index.values, nb.index_right.values)), shape=(len(g), len(g))) + sparse.eye(len(g)); A.data[:] = 1
    Ring = A.tocsr()[pos]                                                    # study area x all areas
    study_of = -np.ones(len(g), int); study_of[pos] = np.arange(n)
    rep_all = np.column_stack([g.geometry.representative_point().x, g.geometry.representative_point().y])
    near_study = cKDTree(rep_all[pos]).query(rep_all)[1]                        # every area -> nearest study area (for surfaces)

    def to_area(gdf):
        j = gpd.sjoin(gdf[["geometry"]], g[["geometry"]], predicate="within")["index_right"]
        return j[~j.index.duplicated()].reindex(gdf.index).values

    # ---- OSM places
    t = pd.read_pickle(f"{SYD}/places.pkl")
    d = gpd.GeoDataFrame(t, geometry=gpd.points_from_xy(t.lon, t.lat), crs=4326).to_crs(7856)
    jd = to_area(d); ok = ~np.isnan(jd.astype(float)); d = d[ok]; jd = jd[ok].astype(int)
    tt = d.t
    am, sh = tt.apply(lambda q: q.get("amenity")).values, tt.apply(lambda q: q.get("shop")).values
    cu = lambda x: tt.apply(lambda q: x in [c.strip() for c in q.get("cuisine", "").split(";")]).values
    br = lambda nm: tt.apply(lambda q: nm in (q.get("brand", "") + "|" + q.get("name", "")).lower()).values
    food = np.isin(am, ["cafe", "fast_food", "restaurant", "pub", "bar", "food_court", "ice_cream"])
    eats = np.isin(am, ["fast_food", "restaurant", "food_court"]); sup = sh == "supermarket"
    P = sparse.csr_matrix((np.ones(len(jd)), (jd, np.arange(len(jd)))), shape=(len(g), len(jd)))
    R = (Ring @ P).tocsr()                                                   # study area x venue (app counting rule)
    nfood, neats, nsup = R @ food, R @ eats, R @ sup

    lines = {}
    def two_type(lid, mA, mB, recipe):
        keep = mA | mB
        lines[lid] = two_type_line(lid, near_study[jd[keep]], R[:, keep], mA[keep], recipe, n)
    sfood = lambda c: (c + 0.5) / (nfood + 5); seats = lambda c: (c + 0.5) / (neats + 5); ssup = lambda c: (c + 0.25) / (nsup + 1)
    two_type("the-latte-line", am == "cafe", am == "fast_food", lambda a, b: rz(sfood(a)) - rz(sfood(b)))
    vi, th = cu("vietnamese"), cu("thai")
    two_type("pho-vs-pad-thai", vi & ~th, th & ~vi, lambda a, b: rz(seats(a)) - rz(seats(b)))
    al, wo = br("aldi") & sup, br("woolworths") & sup
    two_type("the-aldi-line", al, wo & ~al, lambda a, b: rz(ssup(a)) - rz(ssup(b)))
    bt = cu("bubble_tea")                                   # any amenity tagged bubble tea (often cafes); denominator stays the real eateries count
    two_type("the-bubble-tea-line", bt, eats & ~bt, lambda a, b: rz(seats(a)))

    # ---- licensed premises (per-resident lines)
    p = pd.read_excel(PREM, header=3); p = p[(p.Status == "Current") & p.Latitude.notna()]
    p = gpd.GeoDataFrame(p, geometry=gpd.points_from_xy(p.Longitude, p.Latitude), crs=4326).to_crs(7856)
    jp = to_area(p); okp = ~np.isnan(jp.astype(float)); p = p[okp]; jp = jp[okp].astype(int)
    ringpop = np.clip(Ring @ gpop, 500, None)
    per1k = lambda c_all: (Ring @ c_all) / ringpop * 1000
    study_pop = gpop[pos]

    expo = np.bincount(near_study, weights=gpop, minlength=n)

    def counts_line(lid, mask):
        """premises per area ~ Poisson(pop x rate surface); areas outside the study set keep real counts.
        records = counts over all areas."""
        c_all = np.bincount(jp[mask], minlength=len(g)).astype(float)
        fixed = c_all.copy(); fixed[pos] = 0
        def estimate(c):                                   # study areas own their counts; outside counts go to nearest study area
            w = np.bincount(near_study, weights=c, minlength=n)
            return [(np.log((w + 0.5) / np.maximum(expo, 1.0)), 1 / (w + 0.5))]
        def simulate(S, rng):
            c = fixed.copy(); c[pos] = rng.poisson(study_pop * np.exp(S[0])); return c
        return c_all, estimate, simulate

    late = p["After 12am"].eq("Yes").values
    c, est, simf = counts_line("late", late)
    lines["the-late-night-line"] = Line("the-late-night-line", c, est, simf, lambda c: rz(per1k(c)))

    # pokies: records = (venues per area, machines per area); EGM venues ~ Poisson(pop x rate),
    # machines per venue = exp(area surface + a residual drawn from the real list)
    egm = p.EGMs.fillna(0).values; mk = egm > 0
    v_all = np.bincount(jp[mk], minlength=len(g)).astype(float)
    m_all = np.bincount(jp[mk], weights=egm[mk], minlength=len(g))
    lg = np.log(egm[mk]); gm = lg.mean()
    lmean_obs = np.bincount(near_study[jp[mk]], weights=lg, minlength=n)
    pool = lg - gm
    fv, fm = v_all.copy(), m_all.copy(); fv[pos] = 0; fm[pos] = 0
    def est_pok(rec):
        v, mm, lsum = rec
        w = np.bincount(near_study, weights=v, minlength=n)
        return [(np.log((w + 0.5) / np.maximum(expo, 1.0)), 1 / (w + 0.5)), ((lsum + 0.2 * gm) / (w + 0.2), lg.var() / (w + 0.2))]
    def sim_pok(S, rng):
        k = rng.poisson(study_pop * np.exp(S[0])); idx = np.repeat(np.arange(n), k)
        l = S[1][idx] + rng.choice(pool, len(idx))
        v = fv.copy(); v[pos] = k; mm = fm.copy(); mm[pos] = np.bincount(idx, weights=np.exp(l), minlength=n)
        # outside areas keep real venues; their log-machines go to the nearest study area for estimation
        out_l = np.bincount(near_study[jp[mk]][~np.isin(jp[mk], pos)], weights=lg[~np.isin(jp[mk], pos)], minlength=n)
        return v, mm, np.bincount(idx, weights=l, minlength=n) + out_l
    rec0 = (v_all, m_all, lmean_obs)
    lines["the-pokies-line"] = Line("the-pokies-line", rec0, est_pok, sim_pok, lambda rec: rz(per1k(rec[1])))

    # small bars per resident minus pubs' share of food: two record sources, rotated jointly
    sb = p["Licence type"].eq("Liquor - small bar licence").values
    c_sb, est_sb, sim_sb = counts_line("sb", sb)
    pub = am == "pub"; area_f = near_study[jd[food]]; Mf = R[:, food]; ypub = pub[food].astype(float)
    def est_small(rec): return est_sb(rec[0]) + [logit_surface(area_f, rec[1], n)]
    def sim_small(S, rng):
        return sim_sb([S[0]], rng), (rng.random(len(area_f)) < 1 / (1 + np.exp(-S[1][area_f]))).astype(float)
    lines["the-small-bar-line"] = Line("the-small-bar-line", (c_sb, ypub), est_small, sim_small,
                                       lambda rec: rz(per1k(rec[0])) - rz((Mf @ rec[1] + 0.5) / (nfood + 5)))
    return T, lines
