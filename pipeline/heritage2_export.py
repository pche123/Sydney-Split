"""Heritage views for the app: birthplace (migrants), ancestry (self-identified, incl. Australian-born), religion.
Usage: python heritage2_export.py <gcp_sa2_dir> <app_data.json>"""
import sys, glob, re, json, numpy as np, pandas as pd
src, app = sys.argv[1:3]; key = "SA2_CODE_2021"
def load(t):
    x = None
    for f in sorted(glob.glob(f"{src}/2021Census_{t}*_NSW_SA2.csv")):
        d = pd.read_csv(f, dtype={key: str}).set_index(key); x = d if x is None else x.join(d, rsuffix="_d")
    return x
a = pd.read_csv("q_classic/areas.csv", dtype=str).set_index("SA2_CODE21")
g09, g08, g14, g10 = [load(t).reindex(a.index) for t in ("G09", "G08", "G14", "G10")]
pop = g09["P_Tot_Tot"].astype(float)
def short(n): return re.sub(r" \(NSW\)", "", n.split(" - ")[0])

def pretty(s):
    s = s.replace("_", " ")
    fix = {"Korea South": "South Korea", "Hong Kong SAR Ch": "Hong Kong", "Nth Macedonia": "North Macedonia", "USA": "USA",
           "Bosnia Herzegov": "Bosnia and Herzegovina", "SE Europe nfd": "South Eastern Europe", "Sth": "South"}
    for k, v in fix.items(): s = s.replace(k, v)
    return s

def entry(kind, name, n, extra=None):
    n = n.fillna(0).astype(float); city = n.sum() / pop.sum(); share = (n / pop).fillna(0)
    ok = n >= 100; top = share[ok].sort_values(ascending=False).head(3)
    rest = (pop - n).clip(lower=0); D = 0.5 * (n / n.sum() - rest / rest.sum()).abs().sum()
    e = dict(id=kind + "-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"), kind=kind, name=name,
             pct=round(city * 100, 2), people=int(n.sum()), lq=[round(float(s / city), 2) for s in share],
             peaks=[[short(a.SA2_NAME21[i]), round(float(share[i] * 100), 1), round(float(share[i] / city), 1)] for i in top.index],
             D=round(float(D), 3), _share=share)
    if extra: e.update(extra)
    return e

out = []
_v = pd.read_csv("heritage_clustering.csv")
VER = {r.country: (None if pd.isna(r.arrived_2011_plus) else float(r.arrived_2011_plus)) for r in _v.itertuples()}
VER.pop("England", None)  # arrival table only has United Kingdom, not England
# --- birthplace: every country with >= 2,000 Sydney residents
skip = {"Australia", "COB_NS", "Elsewhere", "Tot"}
for c in [c[2:-4] for c in g09.columns if c.startswith("P_") and c.endswith("_Tot")]:
    if c in skip or g09[f"P_{c}_Tot"].sum() < 2000: continue
    cols = [k for k in g10.columns if k.lower().startswith(c.lower()[:6])]
    tot = [k for k in cols if k.endswith(("_Tot", "_Total"))]; ns = [k for k in cols if re.search(r"(_ns|_NS)$", k)]
    rec = [k for k in cols if re.search(r"(11_15|2011_2015|_2016|_2017|_2018|_2019|_2020|_2021)$", k)]
    recent = None
    if tot and rec:
        T = g10[tot[0]].sum() - (g10[ns[0]].sum() if ns else 0)
        if T > 0: recent = round(float(g10[rec].sum().sum() / T), 3)
    out.append(entry("birth", pretty(c), g09[f"P_{c}_Tot"], dict(recent=VER.get(c))))
# --- ancestry (responses; people may give two)
ANC = {"Aust": "Australian", "Aust_Abor": "Aboriginal", "Sth_African": "South African", "NZ": "New Zealander", "Sri_Lankan": "Sri Lankan"}
for c in [c[:-9] for c in g08.columns if c.endswith("_Tot_resp")]:
    if c in ("Other", "Ancestry_NS", "Tot_P"): continue
    out.append(entry("ancestry", ANC.get(c, c.replace("_", " ")), g08[f"{c}_Tot_resp"]))
# --- religion
REL = {"Buddhism_P": "Buddhism", "Christianity_Catholic_P": "Catholic", "Christianity_Anglican_P": "Anglican",
       "Christianity_Eastrn_Orthdox_P": "Eastern Orthodox", "Christianity_Orintal_Orthdx_P": "Oriental Orthodox",
       "Christianity_Asyrin_Apstlic_P": "Assyrian Apostolic", "Christianity_Baptist_P": "Baptist", "Christianity_Pentecostal_P": "Pentecostal",
       "Christinty_Prsbytrin_Refrmd_P": "Presbyterian & Reformed", "Christianity_Uniting_Church_P": "Uniting Church",
       "Christinty_Jehvahs_Witnses_P": "Jehovah's Witnesses", "Christianity_Lattr_day_Snts_P": "Latter-day Saints",
       "Christianity_Tot_P": "Christianity (all)", "Hinduism_P": "Hinduism", "Islam_P": "Islam", "Judaism_P": "Judaism",
       "Othr_Rel_Sikhism_P": "Sikhism", "SB_OSB_NRA_NR_P": "No religion"}
for c, nm in REL.items(): out.append(entry("religion", nm, g14[c]))

# rank clustering and "shares suburbs with" within each kind
for kind in ("birth", "ancestry", "religion"):
    grp = [e for e in out if e["kind"] == kind]
    order = sorted(grp, key=lambda e: -e["D"])
    for r, e in enumerate(order): e["D_rank"], e["D_of"] = r + 1, len(grp)
    S = pd.DataFrame({e["name"]: e["_share"] for e in grp}); C = S.corr(method="spearman")
    for e in grp:
        nb = C[e["name"]].drop(e["name"])
        if kind == "religion": nb = nb.drop([k for k in ("Christianity (all)",) if k in nb.index and k != e["name"]])
        e["shares_with"] = list(nb.sort_values(ascending=False).index[:2])
for e in out: e.pop("_share")
out.sort(key=lambda e: (["birth", "ancestry", "religion"].index(e["kind"]), -e["people"]))
d = json.load(open(app)); d["heritage"] = out
json.dump(d, open(app, "w"), separators=(",", ":"))
for k in ("birth", "ancestry", "religion"): print(k, sum(e["kind"] == k for e in out), [e["name"] for e in out if e["kind"] == k][:8])
