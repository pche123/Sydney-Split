"""Test what Wikipedia and the press say about Sydney's Latte Line against the data.

    python experiments/latte_claims.py <data folder> <work folder> [out folder]

Every claim gets one test and one verdict. The null for anything about the Latte Line itself is "a random Sydney
just as smooth": café and fast-food counts re-drawn from smooth landscapes fitted to the real ones (the same null
as the line's own test), so a claim only counts as supported if the real Latte Line does better than such cities.
Census lines (money, education, the Hi-Vis Line) use the calibrated landscape test.

The COVID-19 "LGAs of concern" are approximated by the ABS SA3 regions that make them up (SA2 names where an SA3
straddles two councils); the exact council boundaries would sharpen this.
Heritage is not scored against the line, on purpose.
"""
import json, os, sys
import numpy as np, pandas as pd, geopandas as gpd
from scipy.stats import norm, rankdata

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
D, W_ = sys.argv[1], sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "results", "latte_claims")
os.makedirs(OUT, exist_ok=True); sys.path[:0] = [ROOT, W_]; os.chdir(W_)
from linetests.landscape import MultiScaleNull, calibrated_map_test
from linetests.records import landscape_pars, landscape_draw
import lines_sydney
from cities import load

B = int(os.environ.get("CLAIMS_B", 999)); rng = np.random.default_rng(2021)
C = load("Sydney"); n = C["n"]; I, J, W = C["I"], C["J"], C["W"]
a = pd.read_csv(f"{W_}/q_classic/areas.csv", dtype=str); codes = a.SA2_CODE21.values
G = gpd.read_file(f"{D}/shp/SA2_2021_AUST_GDA2020.shp").to_crs(7856).set_index("SA2_CODE21").loc[codes].reset_index()
S = pd.read_csv(f"{W_}/signals_sa2.csv", dtype={"SA2_CODE_2021": str}).set_index("SA2_CODE_2021").loc[codes]
pop = S.population.values.astype(float)
rz = lambda v: norm.ppf((rankdata(pd.Series(v).fillna(pd.Series(v).median()).values) - 0.5) / len(v))
split = lambda f: f > np.median(f)

T, L = lines_sydney.build(); LT = L["the-latte-line"]; latte = LT.field; cafe = split(latte)
GPd = MultiScaleNull(C["geom"], I, J, W); pars = landscape_pars(GPd, LT)
print("simulating", B, "random Sydneys for the Latte Line", flush=True)
SIM = np.array([split(LT.remake(LT.simulate(landscape_draw(GPd, LT, pars, rng), rng)).field) for _ in range(B)])

def vs_null(stat_real, stat_fn):
    null = np.array([stat_fn(s) for s in SIM]); return (1 + (null >= stat_real).sum()) / (B + 1), null.mean()

GN = MultiScaleNull(G.geometry, I, J, W, m=25)
def census_p(f):
    r = calibrated_map_test(GN, f, B=199, R=40, Bin=99, seed=7)
    if r["p_cal"] < 0.1: r = calibrated_map_test(GN, f, B=199, R=200, Bin=99, seed=7)
    return r["p_cal"]
def match(x, y):   # share of areas on the matching side, direction as stated
    return float((x == y).mean())

prof = rz(S.professionals.values)
hivis = rz(S.works_transport_logistics.values) - prof; hv_prof = ~split(hivis)          # professional side of the Hi-Vis Line
rent, mort, inc = (S[c].values.astype(float) for c in ["median_rent_weekly", "median_mortgage_repay_monthly", "median_tot_hhd_inc_weekly"])
deg = S.university_degree.values.astype(float)
rows = []
def add(no, claim, source, test, figure, p, verdict):
    rows.append(dict(no=no, claim=claim, source=source, test=test, figure=figure, p=None if p is None else round(float(p), 4), verdict=verdict))
    print(f"{no:>2} {verdict:16s} {claim[:60]:60s} {figure}" + ("" if p is None else f"  p = {p:.4f}"), flush=True)

# 1. Route: north-east vs south-west, from the airport through Parramatta
x, y = C["rep"][:, 0], C["rep"][:, 1]
ap, pa = gpd.GeoSeries.from_xy([151.177, 151.003], [-33.946, -33.815], crs=4326).to_crs(7856)
cross = (pa.x - ap.x) * (y - ap.y) - (pa.y - ap.y) * (x - ap.x)     # >0: left of the airport->Parramatta heading (which points north-west), i.e. south-west
ne = cross < 0
m1 = match(cafe, ne); p1, nm1 = vs_null(m1, lambda s: match(s, ne))
add(1, "It divides north-east from south-west Sydney, running from the airport through Parramatta", "Wikipedia (unsourced)",
    "share of suburbs whose café side matches the north-east side of an airport-Parramatta line, vs random Sydneys",
    f"{m1:.0%} match (random Sydneys {nm1:.0%})", p1, "supported" if p1 <= 0.05 else "not supported")

# 2. Cafés vs fast food really is a pattern (the term "does not refer to any data")
add(2, "The Latte Line is a figure of speech, not something in the coffee data", "Wikipedia (unsourced)",
    "the Latte Line's own test: cafés vs fast-food places per suburb, against random Sydneys (Section 9)",
    "real pattern (p = 0.002 for any geography); border cleaner than random Sydneys on its own (p = 0.02), not after allowing for 6 food lines (0.12)",
    0.0198, "partly: the data has one")

# 3. Red Rooster
rr = json.load(open(f"{ROOT}/app/data/sydney.json")); rrl = {l["id"]: l for l in rr["lines"]}
add(3, "The Red Rooster Line marks where Red Rooster restaurants stop", "Twitter, 2016; Honi Soit 2017",
    "Red Rooster vs the nearest other chicken chain, against random store layouts", "cleaner than chance on its own (p = 0.03), not after correction (0.16)",
    0.033, "partly")

# 4. haves vs have-nots: money
res = {}
for nm, v in [("rent", rent), ("mortgage", mort), ("household income", inc)]:
    f = rz(v); res[nm] = (census_p(f), match(split(f), cafe), match(split(f), hv_prof))
fig = "; ".join(f"{k}: p = {v[0]:.2f}, matches Latte {v[1]:.0%}, Hi-Vis {v[2]:.0%}" for k, v in res.items())
add(4, "The line divides the haves from the have-nots", "Geoff Roberts, Greater Sydney Commission (SMH 2016)",
    "Money Lines (rent, mortgage, household income): is money a line, and whose route does it follow?", fig,
    min(v[0] for v in res.values()), "slope, not a line; follows work more than coffee")

# 5. $1m homes above the line
med = np.median(mort); ok = mort != med; hi = mort > med          # suburbs exactly at the median (rounded figures) left out
a5, b5 = hi[cafe & ok].mean(), (~hi[~cafe & ok]).mean()
add(5, "Homes above the line are almost always worth over $1m, below it under", "Wikipedia, refs 33-34",
    "mortgage repayments (2021 Census; sale prices are not in the census): above-median share on each side",
    f"café side {a5:.0%} above the city median; fast-food side {b5:.0%} below", None, "mostly, not almost always")

# 6. education
dg = split(deg); m6 = match(dg, cafe); p6, nm6 = vs_null(m6, lambda s: match(dg, s))
add(6, "School results depend on which side of the line you live", "Wikipedia, refs 27-28",
    "university-degree share (HSC and NAPLAN are not in the census): match with the café side, vs random Sydneys",
    f"{m6:.0%} match (random Sydneys {nm6:.0%})", p6, "supported (degrees)" if p6 <= 0.05 else "not supported")

# 7. COVID-19 LGAs of concern
geo = gpd.read_file(f"{D}/shp/SA2_2021_AUST_GDA2020.shp", ignore_geometry=True).set_index("SA2_CODE21").loc[codes]
SA3 = {"Botany", "Kogarah - Rockdale", "Hurstville", "Blacktown", "Blacktown - North", "Mount Druitt", "Campbelltown (NSW)", "Bankstown",
       "Canterbury", "Auburn", "Merrylands - Guildford", "Fairfield", "Liverpool", "Bringelly - Green Valley", "Parramatta", "Carlingford",
       "Penrith", "St Marys"}
NOT = {"Ashfield - North", "Ashfield - South", "Dulwich Hill - Lewisham", "Haberfield - Summer Hill"}   # Inner West Council
concern = (geo.SA3_NAME21.isin(SA3) | geo.SA3_NAME21.eq("Strathfield - Burwood - Ashfield")).values & ~geo.SA2_NAME21.isin(NOT).values
def bal(side_ff):   # balanced accuracy: concern areas on the fast-food side, others on the café side
    return 0.5 * (side_ff[concern].mean() + (~side_ff[~concern]).mean())
m7 = bal(~cafe); p7, nm7 = vs_null(m7, lambda s: bal(~s))
pop_ff = pop[concern & ~cafe].sum() / pop[concern].sum()
others = {k: bal(v) for k, v in [("Hi-Vis (work)", ~hv_prof), ("rent", ~split(rent)), ("income", ~split(inc))]}
nopen = concern & ~geo.SA3_NAME21.isin({"Penrith", "St Marys"}).values
add(7, "The 2021 lockdown 'LGAs of concern' were the Latte Line's other side", "Wikipedia, refs 52-55",
    "councils of concern (approximated by ABS SA3 regions) vs the fast-food side, balanced accuracy, vs random Sydneys",
    f"{pop_ff:.0%} of their residents on the fast-food side; balanced accuracy {m7:.0%} (random Sydneys {nm7:.0%}); "
    + ", ".join(f"{k} {v:.0%}" for k, v in others.items()) + f"; without Penrith {0.5 * ((~cafe)[nopen].mean() + cafe[~concern].mean()):.0%}", p7, "supported" if p7 <= 0.05 else "not supported")

# 8. hardening (from experiments/sydney_claims.py, census 2001-2021)
H = pd.read_csv(f"{ROOT}/results/sydney_claims/hardening.csv")
hv = H[H.line == "Hi-Vis"].set_index("year").z
add(8, "The line is hardening", "2023 report on poverty (ref 26)",
    "how much cleaner than random the Hi-Vis border is in each census, 2001-2021 (the venue data has no history)",
    "z = " + ", ".join(f"{v:+.1f} ({y})" for y, v in hv.items()) + ": a real line in every census, no steady hardening", None,
    "not supported to 2021")

# 9. breaking down: western chicken chains move east
add(9, "The line is breaking down as western chicken chains spread east", "refs 21-23",
    "the Charcoal Chook Line (charcoal-chicken shops vs other takeaways)", f"no line (p = {rrl['the-charcoal-chook-line']['p']:.2f})",
    rrl["the-charcoal-chook-line"]["p"], "consistent")

# 10. Melbourne
mel = json.load(open(f"{ROOT}/app/data/melbourne.json"))
add(10, "Melbourne's divide is much weaker than Sydney's, with no clear boundary", "Wikipedia (unsourced)",
    "real lines in each city under the same test", f"Sydney {sum(l['tier'] == 'line' for l in rr['lines'])} (Hi-Vis, Factory); Melbourne "
    f"{sum(l['tier'] == 'line' for l in mel['lines'])}", None, "supported")
pd.DataFrame(rows).to_csv(f"{OUT}/claims.csv", index=False)
print("->", f"{OUT}/claims.csv")
