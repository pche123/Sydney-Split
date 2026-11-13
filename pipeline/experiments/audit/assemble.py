"""One verdict table for every line in both cities.

line test p (Q2): calibrated landscape p (p_cal). Sydney census lines use the search-wide p
(the whole 1,596-candidate search re-run under the joint landscape null). Corrections:
Holm within each app group (Tokyo: as before; Sydney: Food, Night).
Verdicts:
  'Real line'            corrected line-test p <= 0.05
  'Real pattern, gentle' fails that, but the map clearly has geography (Q1 p <= 0.05;
                         census maps always do)
  'Could be chance'      neither
Edge (Q3) reported alongside: 'cliff' if calibrated edge p <= 0.05 after Holm across all lines."""
import json, numpy as np, pandas as pd


def holm(p):
    p = np.asarray(p, float); o = np.argsort(p); m = len(p); out = np.empty(m); run = 0
    for r, i in enumerate(o): run = max(run, (m - r) * p[i]); out[i] = min(1, run)
    return out


rows = []
for c in ["Sydney", "Tokyo"]:
    for f in [f"final_data_{c}.csv"]:
        d = pd.read_csv(f); rows += [dict(city=c, line=r.line, kind="records", p_line=r.p_cal, size=r.size) for r in d.itertuples()]
    d = pd.read_csv(f"final_census_{c}.csv"); rows += [dict(city=c, line=r.line, kind="census", p_line=r.p_cal, size=r.size, p_app=r.p_app) for r in d.itertuples()]
ch = pd.read_csv("final_chains.csv"); rows += [dict(city=r.city, line=r.line, kind="records", p_line=r.p_cal, size=r.size) for r in ch.itertuples()]
T = pd.DataFrame(rows)

# Sydney census: search-wide
APP = {"works_transport_logistics vs professionals": "the-hi-vis-line", "works_manufacturing": "the-factory-line",
       "works_media_tech vs tradies": "the-laptop-vs-ute-line", "average_household_size vs works_construction": "the-tradie-belt",
       "average_household_size vs works_transport_logistics": "the-full-house-line", "median_age_persons vs works_construction": "the-boomer-vs-builder-line"}
for m in ["classic", "quirky"]:
    s = pd.read_csv(f"search_landscape_{m}.csv")
    for r in s.itertuples():
        if r.line in APP:
            k = (T.city == "Sydney") & (T.line == APP[r.line]); T.loc[k, "p_search"] = r.p_search_landscape; T.loc[k, "p_app"] = r.p_search_msr

q1 = pd.read_csv("q1_geography.csv"); T = T.merge(q1, on=["city", "line"], how="left")
E = pd.concat([pd.read_csv(f) for f in ["final_edge_Sydney.csv", "final_edge_Tokyo_census.csv", "final_edge_Tokyo_records.csv"]])[["city", "line", "p_cal"]].rename(columns={"p_cal": "p_edge"})
T = T.merge(E, on=["city", "line"], how="left")

apps = {"Sydney": json.load(open("app_data.json")), "Tokyo": json.load(open("/home/claude/tokyo/app_data_tokyo.json"))}
meta = {(c, l["id"]): (l["name"], l["group"], l["p"]) for c, a in apps.items() for l in a["lines"]}
T["name"] = [meta[(c, l)][0] for c, l in zip(T.city, T.line)]
T["group"] = [meta[(c, l)][1] for c, l in zip(T.city, T.line)]
T["p_app"] = T.p_app.fillna(pd.Series([meta[(c, l)][2] for c, l in zip(T.city, T.line)], index=T.index))

T["p_corrected"] = np.nan
syd_search = (T.city == "Sydney") & T.p_search.notna()
T.loc[syd_search, "p_corrected"] = T.loc[syd_search, "p_search"]
for (c, g), idx in T[~syd_search].groupby(["city", "group"]).groups.items():
    T.loc[idx, "p_corrected"] = holm(T.loc[idx, "p_line"].values)
T["p_edge_holm"] = np.nan
ok = T.p_edge.notna(); T.loc[ok, "p_edge_holm"] = holm(T.loc[ok, "p_edge"].values)
geo = (T.kind == "census") | (T.p_geography <= 0.05)
T["verdict"] = np.where(T.p_corrected <= 0.05, "Real line", np.where(geo, "Real pattern, gentle", "Could be chance"))
T["edge"] = np.where(T.p_edge_holm <= 0.05, "cliff", "slope")
old = lambda p: "Beats chance" if p <= 0.05 else "Could be chance"
T["old_verdict"] = [old(p) for p in T.p_app]
cols = ["city", "group", "name", "kind", "p_app", "old_verdict", "p_line", "p_corrected", "p_geography", "p_edge", "verdict", "edge", "size"]
T = T[cols].sort_values(["city", "group", "p_corrected"])
T.to_csv("verdicts.csv", index=False)
with pd.option_context("display.width", 250, "display.max_rows", 100):
    print(T.round(3).to_string(index=False))
