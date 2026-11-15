"""Which "urban rules" say more than the correlation table, and more than a smooth random city would?

    python experiments/rules.py <cities folder> [out folder]

Rules have the form  (A high/low) AND (B high/low)  =>  C high/low,  where high/low = top/bottom third of a city's areas.
Each rule is judged twice:
  1. Beyond correlation: its precision minus what a city with the same rank correlations between A, B and C, and nothing
     else, would give (Gaussian copula, simulated). Two-condition rules over correlated census shares mostly restate
     the correlation table; only the excess is new.
  2. Beyond chance in space: the same excess in 99 smooth random versions of the city. Each variable gets its own
     fitted multi-scale landscape (so neighbouring areas are alike, as in the real city), then the variables are mixed
     to have the real city's correlation matrix. Smooth maps have far fewer independent areas than areas, so this is
     what makes the p-values honest.
Rules are searched within each country, then checked city by city, and finally on cities they were not found in.
"""
import itertools, os, sys
import numpy as np, pandas as pd, geopandas as gpd
from scipy.stats import norm, rankdata
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.join(HERE, ".."), os.path.join(HERE, "..", "pipeline")]
from linetests.landscape import MultiScaleNull
from cities import CITIES

CI = sys.argv[1]; OUTD = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "results", "rules"); os.makedirs(OUTD, exist_ok=True)
DL = os.environ.get("SPLIT_DL", os.path.join(HERE, "..", "app", "public", "downloads"))   # per-area tables
V = ["age_65_plus", "kids_under_15", "living_alone", "detached_houses", "uni_degree", "professionals", "managers",
     "train_commute", "car_commute", "bike_commute", "walk_commute"]
LAB = {"age_65_plus": "over-65s", "kids_under_15": "children", "living_alone": "living alone", "detached_houses": "detached houses",
       "uni_degree": "degrees", "professionals": "professionals", "managers": "managers", "train_commute": "train commuting",
       "car_commute": "car commuting", "bike_commute": "cycling to work", "walk_commute": "walking to work"}
COUNTRY = {"au": ["melbourne", "brisbane", "perth", "adelaide"], "jp": ["osaka", "kyoto", "nagoya", "yokohama", "kobe", "fukuoka", "sapporo"],
           "uk": ["london", "manchester", "birmingham", "liverpool", "brighton"]}
if os.environ.get("SPLIT_COUNTRY"):   # e.g. '{"us": ["newyork", "chicago"]}' to score held-out cities with the same settings
    import json; COUNTRY = json.loads(os.environ["SPLIT_COUNTRY"])
NULL = 99; MIN_MATCH = 12; rng = np.random.default_rng(5)
rn = lambda x: norm.ppf((rankdata(x) - 0.5) / len(x))

# all candidate rules: (a, sa, b, sb, c, sc) with s = +1 high / -1 low
RULES = [(a, sa, b, sb, c, sc) for a, b in itertools.combinations(range(len(V)), 2) for c in range(len(V)) if c not in (a, b)
         for sa in (1, -1) for sb in (1, -1) for sc in (1, -1)]
Ra = np.array([r[0] for r in RULES]); Rb = np.array([r[2] for r in RULES]); Rc = np.array([r[4] for r in RULES])
Sa = np.array([r[1] for r in RULES]); Sb = np.array([r[3] for r in RULES]); Sc = np.array([r[5] for r in RULES])

def tercile_flags(Z):
    """Z: areas x vars (any scale) -> hi, lo boolean arrays by within-column thirds."""
    q1, q2 = np.quantile(Z, 1 / 3, axis=0), np.quantile(Z, 2 / 3, axis=0)
    return Z >= q2, Z <= q1

def precisions(Z):
    """precision and match count of every rule on one city (areas x vars)."""
    hi, lo = tercile_flags(Z)
    A = np.where(Sa[:, None] > 0, hi[:, Ra].T, lo[:, Ra].T); Bm = np.where(Sb[:, None] > 0, hi[:, Rb].T, lo[:, Rb].T); C = np.where(Sc[:, None] > 0, hi[:, Rc].T, lo[:, Rc].T)
    m = A & Bm; nm = m.sum(1); hit = (m & C).sum(1)
    return np.where(nm > 0, hit / np.maximum(nm, 1), np.nan), nm

def copula_expectation(R, ns=40000):
    """precision each rule would have in a city with correlation matrix R (of rank-normal scores) and nothing else."""
    Lc = np.linalg.cholesky(R + 1e-9 * np.eye(len(R))); Z = rng.standard_normal((ns, len(R))) @ Lc.T
    return precisions(Z)[0]

summ = []
for ctry, cities in COUNTRY.items():
    for city in cities:
        tab = pd.read_csv(os.path.join(DL, f"{city}_areas.csv"))
        if any(v not in tab for v in V): print("skip", city); continue
        ok = tab[V].notna().all(1).values
        X = np.column_stack([rn(tab[v].fillna(tab[v].median()).values) for v in V])
        R = np.corrcoef(X.T)
        prec, nm = precisions(X[ok]); expc = copula_expectation(R)
        # smooth random versions of the city with the same correlation matrix
        G = gpd.read_file(f"{CI}/{city}/areas.gpkg").to_crs(CITIES[city]["crs"]).reset_index(drop=True)
        z = np.load(f"{CI}/{city}/fields.npz"); MS = MultiScaleNull(G.geometry, z["I"], z["J"], z["W"], m=9 if len(G) > 600 else 25)
        sims = []
        for k, v in enumerate(V):
            par = MS.fit(X[:, k]); S = MS.simulate(par, NULL, rng); sims.append((S - S.mean(0)) / S.std(0))
        S = np.stack(sims, 2)                                    # areas x NULL x vars, independent smooth fields
        Lc = np.linalg.cholesky(R + 1e-9 * np.eye(len(V)))
        null_ex = []
        for b in range(NULL):
            Zb = S[:, b, :]; Zb = Zb @ np.linalg.inv(np.linalg.cholesky(np.corrcoef(Zb.T) + 1e-9 * np.eye(len(V)))).T @ Lc.T   # exact real correlations
            pb, nb = precisions(Zb[ok]); null_ex.append(pb - copula_expectation(np.corrcoef(Zb.T), ns=8000))
        null_ex = np.array(null_ex)
        ex = prec - expc
        p = (1 + (null_ex >= ex[None, :]).sum(0)) / (NULL + 1)
        df = pd.DataFrame({"city": city, "country": ctry, "rule": range(len(RULES)), "matches": nm, "precision": prec, "expected": expc,
                           "excess": ex, "p_space": p, "null_sd": null_ex.std(0)})
        df.to_csv(os.path.join(OUTD, f"rules_{city}.csv"), index=False)
        good = df[(df.matches >= MIN_MATCH)]
        print(f"{city:11s} areas={ok.sum():4d}  rules tested={len(good)}  median excess={good.excess.median():+.3f}  "
              f"excess>0.10: {(good.excess > 0.10).mean():.1%}  p_space<0.01: {(good.p_space < 0.01).mean():.1%}", flush=True)
        summ.append(df)

D = pd.concat(summ); D.to_csv(os.path.join(OUTD, "rules_all.csv"), index=False)
def name(i):
    a, sa, b, sb, c, sc = RULES[i]; hl = lambda s: "high" if s > 0 else "low"
    return f"{hl(sa)} {LAB[V[a]]} + {hl(sb)} {LAB[V[b]]} => {hl(sc)} {LAB[V[c]]}"
# discovery within country on all but one city, test on the held-out city and on other countries
D = D[D.matches >= MIN_MATCH]
agg = D.groupby(["country", "rule"]).agg(cities=("city", "nunique"), excess=("excess", "mean"), p_max=("p_space", "max")).reset_index()
top = agg[(agg.cities >= 3) & (agg.p_max <= 0.05)].sort_values("excess", ascending=False)
top["text"] = top.rule.map(name)
top.to_csv(os.path.join(OUTD, "rules_country_consistent.csv"), index=False)
print("\nRules beyond correlation AND beyond smooth chance in every city of a country (p <= 0.05 in each, >= 3 cities):")
for ctry in COUNTRY:
    t = top[top.country == ctry].head(6)
    print(f" {ctry}: {len(top[top.country == ctry])} rules")
    for _, r in t.iterrows(): print(f"   {r.excess:+.3f}  {r.text}")

# transfer: a country's consistent rules, tested in the other countries' cities (where >= MIN_MATCH areas match);
# a rule transfers to a city if it passes there (p_space <= 0.05) with a positive excess
rows = []
for src in COUNTRY:
    R = set(top[top.country == src].rule)
    for dst in COUNTRY:
        if dst == src: continue
        s = D[(D.country == dst) & D.rule.isin(R)]
        rows.append(dict(source=src, target=dst, tests=len(s), transfer_rate=((s.p_space <= 0.05) & (s.excess > 0)).mean() if len(s) else np.nan))
T = pd.DataFrame(rows); T.to_csv(os.path.join(OUTD, "transfer.csv"), index=False)
print("\nTransfer between countries:"); print(T.round(2).to_string(index=False))
