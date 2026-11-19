"""Exploratory follow-up to the COVID-19 study (not pre-registered): does the café divide add anything once the jobs
divide is known, and the other way round?

    python experiments/covid_partial.py <data folder> <work folder>     (after covid_lines.py)

Partial Spearman: rank-transform everything, regress out the control, correlate residuals. Null for the Latte partial:
the same statistic for 999 random Sydneys just as smooth (the claim-7 null); for the Hi-Vis partial, 999 landscapes
fitted to the Hi-Vis map. Writes results/covid/partial.json.
"""
import json, os, sys
import numpy as np, pandas as pd, geopandas as gpd
from scipy.stats import norm, rankdata
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
D, W_ = sys.argv[1:3]; sys.path[:0] = [ROOT, W_]; os.chdir(W_)
from linetests.landscape import MultiScaleNull
from linetests.records import landscape_pars, landscape_draw
import lines_sydney
from cities import load
B = 999; rng = np.random.default_rng(2021)
S = pd.read_csv(os.path.join(ROOT, "results", "covid", "suburbs.csv"), dtype={"SA2_CODE21": str})
r = lambda v: rankdata(v) / len(v)
def partial(y, x, z):
    Z = np.column_stack([np.ones(len(z)), r(z)])
    res = lambda v: r(v) - Z @ np.linalg.lstsq(Z, r(v), rcond=None)[0]
    a, b = res(y), res(x); return float(np.corrcoef(a, b)[0, 1])
d, latte, hivis = S.delta_per_1000.values, S.latte.values, S.hivis.values
C = load("Sydney"); I, J, W = C["I"], C["J"], C["W"]
T, L = lines_sydney.build(); LT = L["the-latte-line"]; assert np.allclose(LT.field, latte)
GPd = MultiScaleNull(C["geom"], I, J, W); pars = landscape_pars(GPd, LT)
SIM = [LT.remake(LT.simulate(landscape_draw(GPd, LT, pars, rng), rng)).field for _ in range(B)]
codes = S.SA2_CODE21.values
G = gpd.read_file(f"{D}/shp/SA2_2021_AUST_GDA2020.shp").to_crs(7856).set_index("SA2_CODE21").loc[codes].reset_index()
GN = MultiScaleNull(G.geometry, I, J, W, m=25)
rz = lambda v: norm.ppf((rankdata(v) - 0.5) / len(v))
_, _, _, hpar = GN.test(rz(hivis), 199, seed=7); HSIM = GN.simulate(hpar, B, np.random.default_rng(7)).T
pl = partial(d, latte, hivis); nl = np.array([partial(d, s, hivis) for s in SIM])
ph = partial(d, hivis, latte); nh = np.array([partial(d, s, latte) for s in HSIM])
out = dict(latte_given_hivis=dict(r=pl, p_one_sided_negative=float((1 + (nl <= pl).sum()) / (B + 1)), null_q=[float(np.quantile(nl, q)) for q in (.025, .975)]),
           hivis_given_latte=dict(r=ph, p_one_sided_positive=float((1 + (nh >= ph).sum()) / (B + 1)), null_q=[float(np.quantile(nh, q)) for q in (.025, .975)]),
           latte_hivis_spearman=float(pd.Series(latte).corr(pd.Series(hivis), method="spearman")))
json.dump(out, open(os.path.join(ROOT, "results", "covid", "partial.json"), "w"), indent=1); print(json.dumps(out, indent=1))
