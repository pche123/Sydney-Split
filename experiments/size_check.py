import os, sys; _H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [_H, os.path.dirname(_H), os.path.join(os.path.dirname(_H), "..")]  # experiments, repo root
from paths import SYD, TOK, RAW  # noqa: E402
import json, numpy as np, sys
from sharpness import Graph, SmoothNull
m = json.load(open("app_data.json"))["make"]
rep = np.array(m["rep"], float); G = Graph(m["n"], m["I"], m["J"], m["L"], rep=rep); SN = SmoothNull(G, rep, 3000)
rng = np.random.default_rng(7); V = G.V; xy = (rep - rep.mean(0)) / rep.std(0)
cbd = np.hypot(*(rep - rep[np.argmax(rep[:, 0])]).T); cbd = (cbd - cbd.mean()) / cbd.std()
for kind in ["gp", "ramp", "cbd"]:
    for noise in [0.3, 1.0]:
        rej = np.zeros(5)
        for r in range(200):
            if kind == "gp": s = V[:, :40] @ (rng.standard_normal(40) / (1 + np.arange(40) / 6.0))
            elif kind == "ramp": t = rng.uniform(0, 6.3); s = xy @ [np.cos(t), np.sin(t)]
            else: s = cbd + 0.3 * rng.standard_normal() * xy[:, 0]
            f = s / s.std() + noise * rng.standard_normal(len(s))
            res = SN.test(f, 99); rej += np.r_[res["p"], res["omni"]] <= 0.05
        print(kind, noise, "JC STEP RD OMNI =", np.round(rej[[0, 2, 3, 4]] / 200, 3), flush=True)
