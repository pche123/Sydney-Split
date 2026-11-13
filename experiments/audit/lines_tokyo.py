import os, sys; _H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [_H, os.path.dirname(_H), os.path.join(os.path.dirname(_H), "..")]  # experiments, repo root
from paths import SYD, TOK, RAW  # noqa: E402
"""Tokyo venue / HotPepper lines as data-level Line objects (app recipes reproduced)."""
import numpy as np, pandas as pd
from scipy import sparse
from scipy.spatial import cKDTree
from linetests.records import Line, rz, logit_surface, two_type_line
from linetests.msr import LineTest


def build():
    z = np.load(f"{TOK}/out/tokyo_fields.npz"); v = np.load(f"{TOK}/out/tokyo_venues.npz")
    rep = v["rep"]; n = len(rep); WALK = float(v["WALK"])
    T = LineTest(n, z["I"], z["J"], z["W"], seed=12)
    def inc(xy):
        nb = cKDTree(xy).query_ball_point(rep, WALK)
        r = np.repeat(np.arange(n), [len(x) for x in nb]); c = np.concatenate([np.asarray(x, int) for x in nb])
        return sparse.csr_matrix((np.ones(len(r)), (r, c)), shape=(n, len(xy)))
    Mv, Mh = inc(v["vxy"]), inc(v["hxy"])
    av, ah = cKDTree(rep).query(v["vxy"])[1], cKDTree(rep).query(v["hxy"])[1]
    food = Mv @ v["v_food"].astype(float); hp_all = Mh @ np.ones(len(ah))
    ratio = lambda a, b: rz((a + 0.5) / (a + b + 1))
    lines = {}
    def two(src, mA, mB, recipe, lid):
        M, area = (Mv, av) if src == "v" else (Mh, ah)
        keep = mA | mB
        lines[lid] = two_type_line(lid, area[keep], M[:, keep], mA[keep], recipe, n)
    two("v", v["v_cafe"], v["v_fast_food"], lambda a, b: rz((a + 0.5) / (food + 1)) - rz((b + 0.5) / (food + 1)), "the-latte-line")
    two("v", v["v_cafe"], v["v_izakaya_bar"], ratio, "coffee-vs-alcohol")
    two("v", v["v_ramen"], v["v_soba_udon"], ratio, "ramen-vs-soba")
    two("v", v["v_indie_cafe"], v["v_chain_cafe"], ratio, "the-indie-cafe-line")
    two("h", v["h_hp_late"], ~v["h_hp_late"], lambda a, b: rz((a + 0.5) / (2 * a + b + 1)), "the-late-night-line")
    two("h", v["h_hp_izakaya"], v["h_hp_italian"], ratio, "izakaya-vs-bistro")
    two("h", v["h_hp_bar"], v["h_hp_izakaya"], ratio, "bars-vs-izakaya")
    two("h", v["h_hp_yakiniku"], ~v["h_hp_yakiniku"], lambda a, b: rz((a + 0.5) / (hp_all + 1)), "the-yakiniku-line")

    # Price Line: mean of listing prices within 1 km (needs >= 5 priced listings, else NaN -> median)
    price = np.load(f"{TOK}/out/tokyo_price.npy")
    ok = np.isfinite(price); Mp = Mh[:, ok]; ap = ah[ok]; pr = price[ok]
    cnt = Mp @ np.ones(ok.sum())
    def recipe_price(vals):
        mean = (Mp @ vals) / np.maximum(cnt, 1)
        return rz(np.where(cnt >= 5, mean, np.nan))
    k = 0.2
    def est_price(vals):
        gm = vals.mean()
        N = np.bincount(ap, minlength=n)
        return [((np.bincount(ap, weights=vals, minlength=n) + k * gm) / (N + k), vals.var() / (N + k))]
    resid = pr - est_price(pr)[0][0][ap]
    def sim_price(S, rng): return S[0][ap] + rng.permutation(resid)
    lines["the-price-line"] = Line("the-price-line", pr, est_price, sim_price, recipe_price)
    F = dict(zip(z["ids"], z["F"].T))
    for lid, L in lines.items():
        r = np.corrcoef(L.field, F[lid])[0, 1]; assert r > 0.999, (lid, r)
    return T, lines
