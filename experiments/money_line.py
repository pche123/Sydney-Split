"""The Money Line: is rent a line, a slope or chance, and which existing line does it follow?

    python experiments/money_line.py <out.csv> city:app.json:workfolder [...]

Rent per area, ranked within the city (so price levels and inflation cancel out):
  Australia   2021 Census G02 median weekly rent (SA2)
  USA         ACS 2019-2023 median gross rent (B25064), averaged over tracts weighted by renting households
  NZ          Census 2023 weekly rent bands, grouped median (linear within the band holding the middle household)
Tested with the calibrated landscape test (app settings), and compared with each line's route
(share of areas on matching sides, orientation ignored).
"""
import json, os, sys
import numpy as np, pandas as pd, geopandas as gpd
from scipy.stats import norm, rankdata
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.join(HERE, ".."), os.path.join(HERE, "..", "pipeline")]
from linetests.landscape import MultiScaleNull, calibrated_map_test
from cities import CITIES

OUT = sys.argv[1]; rows = []
rn = lambda v: norm.ppf((rankdata(v) - 0.5) / len(v))
NZB = [("VAR_4_250", 0, 200), ("VAR_4_251", 200, 300), ("VAR_4_252", 300, 400), ("VAR_4_253", 400, 500), ("VAR_4_254", 500, 600),
       ("VAR_4_255", 600, 700), ("VAR_4_256", 700, 800), ("VAR_4_257", 800, 1000)]


def rent(city, wk, n):
    co = CITIES[city]["country"]
    if co == "au":
        G = gpd.read_file(f"{wk}/areas.gpkg"); g = pd.read_csv(f"{wk}/census/2021_G02.csv", dtype={"SA2_CODE_2021": str}).set_index("SA2_CODE_2021")
        return g.reindex(G.code.astype(str)).Median_rent_weekly.values.astype(float)
    if co == "us":
        return pd.read_csv(f"{wk}/census/B25064.csv", index_col=0).reindex(range(n)).B25064_001E.values.astype(float)
    if co == "nz":
        d = pd.read_csv(f"{wk}/census/nz.csv", index_col=0).reindex(range(n)); out = []
        for _, r in d.iterrows():
            c = np.array([r[b] for b, _, _ in NZB], float); tot = np.nansum(c)
            if not tot: out.append(np.nan); continue
            cum = np.nancumsum(c); k = int(np.searchsorted(cum, tot / 2)); lo, hi = NZB[k][1], NZB[k][2]
            prev = cum[k - 1] if k else 0; out.append(lo + (hi - lo) * (tot / 2 - prev) / max(c[k], 1e-9))
        return np.array(out)
    return None


for spec in sys.argv[2:]:
    city, appf, wk = spec.split(":")
    d = json.load(open(appf)); n = len(d["areas"])
    r = rent(city, wk, n)
    if r is None or np.isnan(r).mean() > 0.2: print("skip", city); continue
    r = np.where(np.isnan(r), np.nanmedian(r), r)
    G = gpd.read_file(f"{wk}/areas.gpkg").to_crs(CITIES[city]["crs"]).reset_index(drop=True)
    z = np.load(f"{wk}/fields.npz"); MS = MultiScaleNull(G.geometry, z["I"], z["J"], z["W"], m=9 if n > 600 else 25)
    res = calibrated_map_test(MS, rn(r), B=199, R=40, Bin=99, seed=7)
    s = r > np.median(r); match = {}
    for l in d["lines"]:
        if l["group"] == "Chains": continue
        m_ = (s == np.asarray(l["side"], bool)).mean(); match[l["name"]] = max(m_, 1 - m_)
    top = sorted(match.items(), key=lambda x: -x[1])[:3]
    rows.append(dict(city=city, country=CITIES[city]["country"], areas=n, p_raw=res["p_raw"], p_cal=res["p_cal"],
                     follows=top[0][0], match=round(top[0][1], 3), second=top[1][0], match2=round(top[1][1], 3),
                     latte_match=round(match.get("The Latte Line", np.nan), 3), hivis_match=round(match.get("The Hi-Vis Line", np.nan), 3)))
    print(f"{city:13s} Money Line p = {res['p_cal']:.3f} (raw {res['p_raw']:.3f}); follows {top[0][0]} ({top[0][1]:.0%}), "
          f"then {top[1][0]} ({top[1][1]:.0%})", flush=True)
    pd.DataFrame(rows).to_csv(OUT, index=False)
