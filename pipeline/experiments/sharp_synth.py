"""Synthetic size/power check for the sharpness tests on the real Sydney graph."""
import json, sys, time
import numpy as np
from sharpness import Graph, SmoothNull

m = json.load(open("app_data.json"))["make"]
n, I, J, L = m["n"], np.array(m["I"]), np.array(m["J"]), np.array(m["L"])
rep = np.array(m["rep"], float)
G = Graph(n, I, J, L)
SN = SmoothNull(G, rep, ELL * 1000) if False else None
rng = np.random.default_rng(1)
B, R = int(sys.argv[1]) if len(sys.argv) > 1 else 99, int(sys.argv[2]) if len(sys.argv) > 2 else 100
ELL = float(sys.argv[4]) if len(sys.argv) > 4 else 0
KEEP = int(sys.argv[3]) if len(sys.argv) > 3 else 0
names = ["JC", "HOYER", "STEP", "RD", "OMNI"]
V = G.V
SN = SmoothNull(G, rep, ELL * 1000) if ELL else None
xy = (rep - rep.mean(0)) / rep.std(0)
cbd = np.hypot(*(rep - rep[np.argmax(rep[:, 0])]).T)          # distance from the eastern-most area, a stand-in for the CBD
cbd = (cbd - cbd.mean()) / cbd.std()


def smooth(kind):
    if kind == "gp":          # random smooth field: power decays over the 40 smoothest eigenvectors
        a = rng.standard_normal(40) / (1 + np.arange(40) / 6.0)
        return V[:, :40] @ a
    if kind == "ramp":        # a plain linear trend in a random direction
        t = rng.uniform(0, 2 * np.pi)
        return xy @ np.array([np.cos(t), np.sin(t)])
    if kind == "cbd":         # distance-from-centre hill, like most "inner vs outer" patterns
        return cbd + 0.3 * rng.standard_normal() * xy[:, 0]


def front():
    # a real-looking border: the median split of another random smooth field
    g = V[:, :15] @ (rng.standard_normal(15) / (1 + np.arange(15) / 4.0))
    return (g > np.median(g)).astype(float) - 0.5


rows = []
t0 = time.time()
for kind in ["gp", "ramp", "cbd"]:
    for noise in [0.3, 1.0]:
        for delta in [0.0, 0.5, 1.0, 2.0]:
            rej = np.zeros(5)
            for r in range(R):
                s = smooth(kind); s = s / s.std()
                f = s + delta * front() * 2 + noise * rng.standard_normal(n)
                res = SN.test(f, B) if ELL else G.test(f, B, keep=KEEP)
                rej += np.r_[res["p"], res["omni"]] <= 0.05
            rows.append((kind, noise, delta, *(rej / R)))
            print(f"{kind:5s} noise={noise:.1f} step={delta:.1f}  " + "  ".join(f"{a}={b:.2f}" for a, b in zip(names, rej / R)), f"[{time.time()-t0:.0f}s]", flush=True)
np.save(f"sharp_synth_k{KEEP}_l{ELL:g}.npy", np.array(rows, dtype=object))
