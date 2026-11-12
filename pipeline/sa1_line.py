"""Street-level (SA1) version of a line, raw and 'snapped' with a graph min-cut.

Snapped line: choose sides z_i in {0,1} to minimise
    sum_i w_i * |f_i - c| * [z_i disagrees with sign(f_i - c)]  +  lam * sum_(i,j) L_ij * [z_i != z_j]
(w_i = sqrt(population), L_ij = shared border in km). Solved exactly as an s-t min cut.
lam = 0 gives the raw split; larger lam gives a shorter, smoother line.
Usage: python sa1_line.py <A_signal> <B_signal> <name> <lam>
"""
import sys, numpy as np, pandas as pd, geopandas as gpd, networkx as nx
from scipy.stats import norm, rankdata
A, B, name, lam = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
g = gpd.read_file("sa1.gpkg"); E = np.load("sa1_edges.npy"); I, J, L = E[:, 0].astype(int), E[:, 1].astype(int), E[:, 2] / 1000
n = len(g)
def rz(v): v = pd.Series(v).fillna(pd.Series(v).median()).values; return norm.ppf((rankdata(v) - 0.5) / len(v))
f = rz(g[A]) - (rz(g[B]) if B != "-" else 0)
w = np.sqrt(g.population.values)
order = np.argsort(f); cw = np.cumsum(g.population.values[order]); c = f[order][np.searchsorted(cw, cw[-1] / 2)]  # population-weighted median
raw = f > c

def snap(lam):
    G = nx.DiGraph()
    for i in range(n):
        d = w[i] * abs(f[i] - c)
        if f[i] > c: G.add_edge("s", i, capacity=d)      # cost of putting i on side 0
        else: G.add_edge(i, "t", capacity=d)             # cost of putting i on side 1
    for i, j, l in zip(I, J, L):
        G.add_edge(i, j, capacity=lam * l); G.add_edge(j, i, capacity=lam * l)
    _, (S, _) = nx.minimum_cut(G, "s", "t")
    z = np.zeros(n, bool); z[[k for k in S if k != "s"]] = True
    return z

z = snap(lam) if lam > 0 else raw
def cutlen(s): return L[s[I] != s[J]].sum()
print(f"{name}: raw border {cutlen(raw):.0f} km, snapped (lam={lam}) border {cutlen(z):.0f} km, "
      f"areas changed by snapping {np.mean(z != raw):.1%}, people on high side {g.population.values[z].sum() / g.population.sum():.0%}")
np.save(f"sa1_side_{name}.npy", z); np.save(f"sa1_raw_{name}.npy", raw); np.save(f"sa1_score_{name}.npy", f)
