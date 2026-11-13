"""What can be concluded from where overseas-born communities live?
1. Clustering: dissimilarity index D (share of a group that would have to move to be spread like everyone else).
2. Recency: share who arrived 2011+ (G10), and whether newer communities are more clustered.
3. Neighbours: which communities share suburbs (correlation of area shares).
"""
import sys, glob, re, json, numpy as np, pandas as pd
from scipy.stats import spearmanr
src = sys.argv[1]; key = "SA2_CODE_2021"
def load(t):
    x = None
    for f in sorted(glob.glob(f"{src}/2021Census_{t}*_NSW_SA2.csv")):
        d = pd.read_csv(f, dtype={key: str}).set_index(key); x = d if x is None else x.join(d, rsuffix="_d")
    return x
a = pd.read_csv("./q_classic/areas.csv", dtype=str).set_index("SA2_CODE21")
g09, g10 = load("G09").reindex(a.index), load("G10").reindex(a.index)
pop = g09["P_Tot_Tot"]

# G09 column -> G10 prefix(es)
MAP = {"China": "China", "India": "India", "England": "United_Kingdom", "Vietnam": "Vietnam", "Philippines": "Philippines",
       "New_Zealand": "New_Zealand", "Lebanon": "Lebanon", "Nepal": "Nepal", "Iraq": "Iraq", "Korea_South": "Korea",
       "Hong_Kong_SAR_Ch": "H", "Italy": "Italy", "South_Africa": "South_Africa", "Indonesia": "Indonesia", "Malaysia": "Malaysia",
       "Fiji": "Fiji", "Pakistan": "Pakistan", "Sri_Lanka": "Sri_Lanka", "Bangladesh": "Bangladesh", "Greece": "Greece",
       "Iran": "Iran", "Thailand": "Thailand", "USA": "U", "Ireland": "Ireland", "Egypt": "Egypt", "Afghanistan": "Afghanistan",
       "Japan": "Japan", "Taiwan": "Taiwan", "Germany": "Germany", "Croatia": "Croatia", "Singapore": "Singapore", "Canada": "Canada",
       "Poland": "Poland", "Netherlands": "Netherlands", "Nth_Macedonia": "North_Macedonia"}
def g10cols(c):
    p = MAP[c]
    if p == "H": pat = r"^(Hng_Kng|Hong_Kong)"
    elif p == "U": pat = r"^(USA|United_States)"
    elif p == "Korea": pat = r"^Korea"
    elif p == "China": pat = r"^China"
    else: pat = "^" + p + "_"
    return [k for k in g10.columns if re.match(pat, k)]
rows = []
for c in MAP:
    col = f"P_{c}_Tot"
    if col not in g09: continue
    n = g09[col].fillna(0); rest = (pop - n).clip(lower=0)
    D = 0.5 * (n / n.sum() - rest / rest.sum()).abs().sum()
    cs = g10cols(c)
    tot = [k for k in cs if k.endswith(("_Tot", "_Total"))]; ns = [k for k in cs if re.search(r"(_ns|arr_ns|_NS)$", k)]
    recent = [k for k in cs if re.search(r"(11_15|2011_2015|_2016|_2017|_2018|_2019|_2020|_2021)$", k)]
    T = g10[tot[0]].sum() - (g10[ns[0]].sum() if ns else 0) if tot else np.nan
    rec = g10[recent].sum().sum() / T if tot and recent else np.nan
    rows.append(dict(country=c, people=int(n.sum()), sydney_pct=round(n.sum() / pop.sum() * 100, 2), clustering_D=round(D, 3),
                     arrived_2011_plus=round(rec, 3) if rec == rec else None))
R = pd.DataFrame(rows).sort_values("clustering_D", ascending=False)
print(R.to_string(index=False))
ok = R.dropna()
rho, p = spearmanr(ok.arrived_2011_plus, ok.clustering_D)
print(f"\nNewer communities more clustered?  Spearman rho = {rho:.2f} (p = {p:.3f}, {len(ok)} countries)")
for drop in [["Iraq"], ["Iraq", "Afghanistan"]]:
    s = ok[~ok.country.isin(drop)]; r2, p2 = spearmanr(s.arrived_2011_plus, s.clustering_D)
    print(f"   without {drop}: rho = {r2:.2f} (p = {p2:.3f})")

# neighbours: which communities share suburbs (top-15 + Brazil)
top = ["China", "India", "England", "Vietnam", "Philippines", "New_Zealand", "Lebanon", "Nepal", "Iraq", "Korea_South",
       "Hong_Kong_SAR_Ch", "Italy", "South_Africa", "Indonesia", "Malaysia", "Brazil"]
S = pd.DataFrame({c: g09[f"P_{c}_Tot"] / pop for c in top}).fillna(0)
C = S.corr(method="spearman")
pairs = [(C.loc[i, j], i, j) for k, i in enumerate(top) for j in top[k + 1:]]
pairs.sort(reverse=True)
print("\nMost often share suburbs:"); [print(f"   {i} + {j}: {r:.2f}") for r, i, j in pairs[:8]]
print("Most often live apart:"); [print(f"   {i} + {j}: {r:.2f}") for r, i, j in pairs[-6:]]
R.to_csv("./heritage_clustering.csv", index=False)
C.round(2).to_csv("./heritage_cooccurrence.csv")
