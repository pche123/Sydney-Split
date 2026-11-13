import os, sys; _H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [_H, os.path.dirname(_H), os.path.join(os.path.dirname(_H), "..")]  # experiments, repo root
from paths import SYD, TOK, RAW  # noqa: E402
"""Chain-vs-chain ('which is closer') lines as data-level Line objects, both cities.
Records = brand label of each pooled store; recipe = log distance ratio at each area's centre."""
import json
import numpy as np
from scipy.spatial import cKDTree
from linetests.records import two_type_line, Line, logit_surface
from linetests.msr import LineTest


def chain_line(name, rep, A, B, off, n):
    P = np.vstack([A, B]); y = np.r_[np.ones(len(A)), np.zeros(len(B))]
    area = cKDTree(rep).query(P)[1]
    def recipe(y):
        a, b = P[y > 0.5], P[y < 0.5]
        if len(a) == 0 or len(b) == 0: return np.zeros(n)
        return np.log(cKDTree(b).query(rep)[0] + off) - np.log(cKDTree(a).query(rep)[0] + off)
    def simulate(S, rng): return (rng.random(len(area)) < 1 / (1 + np.exp(-S[0][area]))).astype(float)
    return Line(name, y, lambda y: [logit_surface(area, y, n)], simulate, recipe)


def sydney():
    m = json.load(open(f"{SYD}/app_data.json"))["make"]; n = m["n"]; rep = np.array(m["rep"], float)
    T = LineTest(n, m["I"], m["J"], np.array(m["L"]) * 1000, seed=21)
    P = {b["name"]: np.array(b["xy"], float) for b in m["brands"]}
    L = {"the-red-rooster-line": chain_line("the-red-rooster-line", rep, P["Red Rooster"], P["Messina"], 200.0, n),
         "the-charcoal-chook-line": chain_line("the-charcoal-chook-line", rep, P["El Jannah"], P["Starbucks"], 200.0, n)}
    return T, L


def tokyo():
    z = np.load(f"{TOK}/out/tokyo_fields.npz"); c = np.load(f"{TOK}/out/tokyo_chains.npz")
    rep = z["rep"]; n = len(rep); T = LineTest(n, z["I"], z["J"], z["W"], seed=22)
    konbini = np.vstack([c[k] for k in ["7-Eleven", "FamilyMart", "Lawson", "Ministop"]])
    spec = {"my-basket-vs-the-konbini": (c["My_Basket"], konbini), "konbini-wars": (c["7-Eleven"], c["FamilyMart"]),
            "gyudon-wars": (c["Matsuya"], c["Yoshinoya"]), "starbucks-vs-doutor": (c["Starbucks"], c["Doutor"]),
            "ramen-wars": (c["Iekei_ramen"], c["Hakata_tonkotsu_ramen"]), "shrines-vs-temples": (c["Shinto_shrines"], c["Buddhist_temples"])}
    L = {k: chain_line(k, rep, a, b, 50.0, n) for k, (a, b) in spec.items()}
    F = dict(zip(z["ids"], z["F"].T))
    for k, l in L.items(): assert np.corrcoef(l.field, F[k])[0, 1] > 0.999, k
    return T, L
