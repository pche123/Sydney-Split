"""Apply the front-vs-slope tests to the real Sydney and Tokyo lines."""
import json, sys
import numpy as np, pandas as pd
from sharpness import Graph, SmoothNull, rank_normal as rn, width_km

B = int(sys.argv[1]) if len(sys.argv) > 1 else 999
ELLS = [2.0, 3.0, 5.0]


def holm(p):
    p = np.asarray(p); o = np.argsort(p); m = len(p); out = np.empty(m); run = 0
    for r, i in enumerate(o):
        run = max(run, (m - r) * p[i]); out[i] = min(1, run)
    return out


def run(city, n, I, J, W, rep, fields, saved_side):
    G = Graph(n, I, J, W, rep=rep)
    nulls = {e: SmoothNull(G, rep, e * 1000) for e in ELLS}
    rows = []
    for (lid, name), f in fields.items():
        f = np.asarray(f, float)
        s = f > np.median(f)
        agree = np.nan
        if lid in saved_side:
            ss = np.asarray(saved_side[lid], bool); agree = max((ss == s).mean(), (ss != s).mean())
        row = dict(city=city, id=lid, line=name, agree_with_app=round(agree, 3), width_km=round(width_km(f, s, rep, I, J), 1))
        for e, SN in nulls.items():
            r = SN.test(f, B)
            row[f"step_p_{e:g}"] = r["p"][2]; row[f"jc_p_{e:g}"] = r["p"][0]; row[f"rd_p_{e:g}"] = r["p"][3]
            if e == 3.0:
                row["jc"] = round(r["obs"][0], 2); row["jc_if_slope"] = round(r["nullmean"][0], 2)
                row["smooth_r2"] = round(r["r2"], 2); row["step_z"] = round(r["z"][2], 2)
        rows.append(row); print(city, name, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items() if k not in ("city", "id", "line")}, flush=True)
    df = pd.DataFrame(rows)
    df["step_p_holm"] = holm(df["step_p_3"].values)
    return df


# ---------------- Sydney ----------------
d = json.load(open("app_data.json")); m = d["make"]
rep = np.array(m["rep"], float); n = m["n"]; I, J, L = map(np.array, (m["I"], m["J"], m["L"]))
S = {s["id"]: np.array(s["v"], float) for s in m["signals"]}
P = {b["name"]: np.array(b["xy"], float) for b in m["brands"]}
from scipy.spatial import cKDTree
def dist(b): return cKDTree(P[b]).query(rep)[0]
def chain(a, b, off=200.0): return np.log((dist(b) + off) / (dist(a) + off))   # + = a is closer
cbd_i = [l["i"] for l in d["labels"] if l["t"] == "CBD"][0]
cbd = np.hypot(*(rep - rep[cbd_i]).T)
Z = np.column_stack([np.ones(n), rn(cbd), rn(S["median_tot_hhd_inc_weekly"]), rn(S["apartments"])])
def resid(f): return f - Z @ np.linalg.lstsq(Z, f, rcond=None)[0]
diff = lambda a, b: rn(S[a]) - rn(S[b])
syd = {
 ("the-latte-line", "The Latte Line"): diff("share_cafe", "share_fast_food"),
 ("the-red-rooster-line", "The Red Rooster Line"): chain("Red Rooster", "Messina"),
 ("the-charcoal-chook-line", "The Charcoal Chook Line"): chain("El Jannah", "Starbucks"),
 ("the-aldi-line", "The Aldi Line"): diff("share_super_aldi", "share_super_woolworths"),
 ("the-pokies-line", "The Pokies Line"): rn(S["pokies_per_1k"]),
 ("the-late-night-line", "The Late Night Line"): rn(S["late_licences_per_1k"]),
 ("the-bubble-tea-line", "The Bubble Tea Line"): rn(S["share_cuisine_bubble_tea"]),
 ("pho-vs-pad-thai", "Pho vs Pad Thai"): diff("share_cuisine_vietnamese", "share_cuisine_thai"),
 ("the-small-bar-line", "The Small Bar Line"): diff("small_bars_per_1k", "share_pub"),
 ("the-hi-vis-line", "The Hi-Vis Line"): diff("works_transport_logistics", "professionals"),
 ("the-factory-line", "The Factory Line"): rn(S["works_manufacturing"]),
 ("the-laptop-vs-ute-line", "The Laptop vs Ute Line"): resid(diff("works_media_tech", "tradies")),
 ("the-tradie-belt", "The Tradie Belt"): resid(diff("average_household_size", "works_construction")),
 ("the-full-house-line", "The Full House Line"): resid(diff("average_household_size", "works_transport_logistics")),
 ("the-boomer-vs-builder-line", "The Boomer vs Builder Line"): resid(diff("median_age_persons", "works_construction")),
}
saved = {l["id"]: l["side"] for l in d["lines"]}
ds = run("Sydney", n, I, J, L, rep, {k: v + 1e-9 * np.random.default_rng(0).standard_normal(n) for k, v in syd.items()}, saved)

# ---------------- Tokyo ----------------
z = np.load("/home/claude/tokyo/out/tokyo_fields.npz")
dt = json.load(open("/home/claude/tokyo/app_data_tokyo.json"))
savedT = {l["id"]: l["side"] for l in dt["lines"]}
names = {l["id"]: l["name"] for l in dt["lines"]}
F = z["F"]
tok = {(lid, names.get(lid, lid)): F[:, k] for k, lid in enumerate(z["ids"])}
dk = run("Tokyo", len(z["pop"]), z["I"], z["J"], z["W"], z["rep"], tok, savedT)

out = pd.concat([ds, dk]); out.to_csv("sharpness_results.csv", index=False)
print(out[["city", "line", "agree_with_app", "width_km", "jc", "jc_if_slope", "step_z", "step_p_2", "step_p_3", "step_p_5", "step_p_holm", "jc_p_3", "smooth_r2"]].to_string())
