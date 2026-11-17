"""COVID-19 cases and Sydney's lines (pre-registered in HYPOTHESES.md, "COVID-19 cases and Sydney's lines").

    python experiments/covid_lines.py <data folder> <work folder> <covid folder>

<covid folder> holds the NSW Health case table(s) and the ABS POA 2021 -> SA2 2021 correspondence (pipeline/get_covid.py).
Writes results/covid/{summary.json, suburbs.csv}. Descriptive and spatial: says where cases fell, not why.
"""
import glob, json, os, sys
import numpy as np, pandas as pd, geopandas as gpd
from scipy.stats import norm, rankdata, spearmanr

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
D, W_, CV = sys.argv[1:4]; CV = os.path.abspath(CV); OUT = os.path.join(ROOT, "results", "covid"); os.makedirs(OUT, exist_ok=True)
sys.path[:0] = [ROOT, W_]; os.chdir(W_)
from linetests.landscape import MultiScaleNull
from linetests.records import landscape_pars, landscape_draw
import lines_sydney
from cities import load

B = int(os.environ.get("COVID_B", 999)); rng = np.random.default_rng(2021)
C = load("Sydney"); I, J, W = C["I"], C["J"], C["W"]
codes = pd.read_csv(f"{W_}/q_classic/areas.csv", dtype=str).SA2_CODE21.values
G = gpd.read_file(f"{D}/shp/SA2_2021_AUST_GDA2020.shp").to_crs(7856).set_index("SA2_CODE21").loc[codes].reset_index()
S = pd.read_csv(f"{W_}/signals_sa2.csv", dtype={"SA2_CODE_2021": str}).set_index("SA2_CODE_2021").loc[codes]
pop = S.population.values.astype(float)
rz = lambda v: norm.ppf((rankdata(pd.Series(v).fillna(pd.Series(v).median()).values) - 0.5) / len(v))
split = lambda f: f > np.median(f)

# --- cases: postcode x date -> suburb x wave -------------------------------------------------------------------
f1 = sorted(glob.glob(f"{CV}/*table1_location.csv")) or sorted(glob.glob(f"{CV}/*table1*.csv"))
cs = pd.read_csv(f1[0], dtype=str)
cs["date"] = pd.to_datetime(cs.notification_date, errors="coerce")
cs["n"] = pd.to_numeric(cs.get("confirmed_cases_count", pd.Series(1, index=cs.index)), errors="coerce").fillna(1)
cs["poa"] = cs.postcode.str.extract(r"(\d{4})")[0]
WAVES = {"first": ("2020-03-01", "2020-12-31"), "delta": ("2021-06-16", "2021-12-15"), "omicron": ("2021-12-16", "2030-01-01")}
cf = [f for f in glob.glob(f"{CV}/*POA_2021_SA2_2021*") if f.lower().endswith((".csv", ".xlsx"))][0]
cr = pd.read_csv(cf, dtype=str) if cf.endswith(".csv") else pd.read_excel(cf, dtype=str)
pc = next(c for c in cr.columns if c.upper().startswith("POA_CODE")); sc = next(c for c in cr.columns if c.upper().startswith("SA2_CODE"))
rc = next(c for c in cr.columns if "RATIO" in c.upper())
cr = cr[[pc, sc, rc]].dropna(); cr.columns = ["poa", "sa2", "ratio"]; cr["poa"] = cr.poa.str.extract(r"(\d{4})")[0]; cr["ratio"] = cr.ratio.astype(float)
summary = {"source_rows": int(len(cs)), "cases_total": float(cs.n.sum()), "cases_no_postcode": float(cs.n[cs.poa.isna()].sum())}
R = {}
for w, (a, b) in WAVES.items():
    x = cs[(cs.date >= a) & (cs.date <= b) & cs.poa.notna()].groupby("poa").n.sum()
    m = cr.merge(x.rename("n"), left_on="poa", right_index=True); m["c"] = m.n * m.ratio
    got = m.groupby("sa2").c.sum().reindex(codes).fillna(0).values
    R[w] = got / pop * 1000
    summary[f"{w}_sydney_cases"] = float(got.sum())
    summary[f"{w}_nsw_cases_with_postcode"] = float(x.sum())

# --- lines ---------------------------------------------------------------------------------------------------
T, L = lines_sydney.build(); LT = L["the-latte-line"]; latte = LT.field; cafe = split(latte)
prof = rz(S.professionals.values); hivis = rz(S.works_transport_logistics.values) - prof   # high = hi-vis side
GPd = MultiScaleNull(C["geom"], I, J, W); pars = landscape_pars(GPd, LT)
print("simulating", B, "random Sydneys", flush=True)
SIM = [LT.remake(LT.simulate(landscape_draw(GPd, LT, pars, rng), rng)).field for _ in range(B)]
GN = MultiScaleNull(G.geometry, I, J, W, m=25)
_, _, _, hpar = GN.test(rz(hivis), 199, seed=7)
HSIM = GN.simulate(hpar, B, np.random.default_rng(7)).T
rho = lambda a, b: spearmanr(a, b).statistic
d = R["delta"]
r_l = rho(d, latte); null_l = np.array([rho(d, s) for s in SIM]); p_l = (1 + (null_l <= r_l).sum()) / (B + 1)          # V1: one-sided, negative
r_h = rho(d, hivis); null_h = np.array([rho(d, s) for s in HSIM]); p_h = (1 + (null_h >= r_h).sum()) / (B + 1)        # V2 companion: positive
ps = sorted([("V1", p_l), ("V2", p_h)], key=lambda t: t[1]); holm = {ps[0][0]: min(1, 2 * ps[0][1])}; holm[ps[1][0]] = max(holm[ps[0][0]], ps[1][1])
summary.update(V1=dict(rho_latte=r_l, p=p_l, p_holm=holm["V1"], null_mean=float(null_l.mean()), null_q025=float(np.quantile(null_l, .025)), null_q975=float(np.quantile(null_l, .975))),
               V2=dict(rho_hivis=r_h, p=p_h, p_holm=holm["V2"], holds=bool(abs(r_h) >= abs(r_l))))

# V3: councils of concern (exact boundaries, as claim 7)
CONCERN = {"Bayside", "Blacktown", "Burwood", "Campbelltown", "Canterbury-Bankstown", "Cumberland", "Fairfield", "Georges River",
           "Liverpool", "Parramatta", "Strathfield", "Penrith"}
lg = gpd.read_file(os.environ["LGA_SHP"]).to_crs(7856); lg["nm"] = lg.LGA_NAME21.str.replace(r" \(NSW\)", "", regex=True) if "LGA_NAME21" in lg else lg.ABB_NAME
ov = gpd.overlay(G[["SA2_CODE21", "geometry"]], lg[["nm", "geometry"]], how="intersection", keep_geom_type=True); ov["a"] = ov.area
council = pd.Series(codes).map(ov.sort_values("a").groupby("SA2_CODE21").nm.last()).values; concern = pd.Series(council).isin(CONCERN).values
cases = {w: R[w] * pop / 1000 for w in R}
def ratio(x, g):   # population-weighted rate in group g over the rest
    return (x[g].sum() / pop[g].sum()) / (x[~g].sum() / pop[~g].sum())
br = np.random.default_rng(5); idx = [br.integers(0, len(pop), len(pop)) for _ in range(1000)]
def ci(x, g): v = [ratio(x[i], g[i]) for i in idx]; return [float(np.quantile(v, .025)), float(np.quantile(v, .975))]
summary["V3"] = dict(ratio=ratio(cases["delta"], concern), ci=ci(cases["delta"], concern), concern_suburbs=int(concern.sum()))
summary["V4"] = {w: dict(ratio=ratio(cases[w], ~cafe), ci=ci(cases[w], ~cafe)) for w in R if cases[w].sum() > 0}
summary["V4"]["hivis_side"] = {w: ratio(cases[w], split(hivis)) for w in R if cases[w].sum() > 0}
hh = S.average_household_size.values.astype(float)
summary["V5"] = {side: dict(rho_household=rho(d[g], hh[g]), rho_hivis=rho(d[g], hivis[g]), n=int(g.sum())) for side, g in [("cafe", cafe), ("fastfood", ~cafe)]}
summary["delta_rate_per_1000"] = dict(sydney=float(cases["delta"].sum() / pop.sum() * 1000),
                                     fastfood=float(cases["delta"][~cafe].sum() / pop[~cafe].sum() * 1000), cafe=float(cases["delta"][cafe].sum() / pop[cafe].sum() * 1000),
                                     concern=float(cases["delta"][concern].sum() / pop[concern].sum() * 1000), rest=float(cases["delta"][~concern].sum() / pop[~concern].sum() * 1000))
pc_ = pd.DataFrame({"council": council, "pop": pop, **{f"{w}_cases": cases[w] for w in cases}}).groupby("council").sum()
pc_["delta_per_1000"] = pc_.delta_cases / pc_["pop"] * 1000; pc_ = pc_[pc_.index.isin(CONCERN)].sort_values("delta_per_1000", ascending=False)
summary["councils"] = {k: dict(pop=int(v["pop"]), delta_per_1000=round(float(v.delta_per_1000), 1)) for k, v in pc_.iterrows()}
pd.DataFrame({"SA2_CODE21": codes, "name": G.SA2_NAME21.values, "council": council, "concern": concern, "cafe_side": cafe, "pop": pop,
              **{f"{w}_per_1000": R[w] for w in R}, "latte": latte, "hivis": hivis}).to_csv(f"{OUT}/suburbs.csv", index=False)
json.dump(summary, open(f"{OUT}/summary.json", "w"), indent=1, default=float); print(json.dumps(summary, indent=1, default=float))
