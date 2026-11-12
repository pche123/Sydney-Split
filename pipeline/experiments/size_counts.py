"""Size check with realistic count data: venue counts drawn from a smooth intensity
(no front at all), then turned into the same rank-normal difference fields we use."""
import json, numpy as np
from sharpness import Graph, SmoothNull, rank_normal as rn
def setup(city):
    if city == "Sydney":
        m = json.load(open("app_data.json"))["make"]; rep = np.array(m["rep"], float)
        return Graph(m["n"], m["I"], m["J"], m["L"], rep=rep), rep
    z = np.load("/home/claude/tokyo/out/tokyo_fields.npz"); rep = z["rep"]
    return Graph(len(rep), z["I"], z["J"], z["W"], rep=rep), rep
rng = np.random.default_rng(3)
for city in ["Sydney", "Tokyo"]:
    G, rep = setup(city); SN = SmoothNull(G, rep, 3000); n = len(rep)
    xy = (rep - rep.mean(0)) / rep.std(0); r0 = np.hypot(*xy.T)
    for mean_count in [2, 8, 30]:
        rej = np.zeros(5)
        for r in range(100):
            t = rng.uniform(0, 6.3)
            hill = -1.2 * r0 + 0.5 * (xy @ [np.cos(t), np.sin(t)])          # dense centre, tilted
            a = rng.poisson(mean_count * np.exp(hill + 0.6 * xy[:, 0]))
            b = rng.poisson(mean_count * np.exp(hill - 0.6 * xy[:, 0]))
            tot = a + b
            sa = np.where(tot > 0, a / np.maximum(tot, 1), np.nan)
            f = rn(sa)
            res = SN.test(f, 99); rej += np.r_[res["p"], res["omni"]] <= 0.05
        print(city, "mean count", mean_count, "JC STEP RD =", np.round(rej[[0, 2, 3]] / 100, 2), flush=True)
