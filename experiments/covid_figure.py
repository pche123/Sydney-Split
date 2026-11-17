"""Figure: weekly COVID-19 cases per 1,000 residents on each side of the Latte Line, Mar 2020 - Feb 2022.

    python experiments/covid_figure.py <covid folder>     (after covid_lines.py)
"""
import os, sys
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); CV = sys.argv[1]
S = pd.read_csv(f"{ROOT}/results/covid/suburbs.csv", dtype={"SA2_CODE21": str})
cs = pd.read_csv(f"{CV}/confirmed_cases_table1_location.csv", dtype=str); cs["date"] = pd.to_datetime(cs.notification_date); cs["poa"] = cs.postcode.str.extract(r"(\d{4})")[0]
cr = pd.read_excel(next(f for f in os.listdir(CV) if "POA_2021_SA2_2021" in f) and os.path.join(CV, next(f for f in os.listdir(CV) if "POA_2021_SA2_2021" in f)), dtype=str)
cr = cr[["POA_CODE_2021", "SA2_CODE_2021", "RATIO_FROM_TO"]].dropna(); cr.columns = ["poa", "sa2", "ratio"]; cr["ratio"] = cr.ratio.astype(float)
side = S.set_index("SA2_CODE21").cafe_side; popside = S.groupby("cafe_side")["pop"].sum()
cs["week"] = cs.date.dt.to_period("W").dt.start_time
w = cs.dropna(subset=["poa"]).groupby(["week", "poa"]).size().rename("n").reset_index().merge(cr, on="poa")
w = w[w.sa2.isin(side.index)]; w["side"] = w.sa2.map(side); w["c"] = w.n * w.ratio
t = w.groupby(["week", "side"]).c.sum().unstack().fillna(0); t = t.div(popside, axis=1) * 1000
fig, ax = plt.subplots(figsize=(9, 4.2), dpi=150)
ax.plot(t.index, t[False], color="#d8572a", lw=2, label="Fast-food side of the Latte Line")
ax.plot(t.index, t[True], color="#2a6fdb", lw=2, label="Café side")
ax.set_yscale("log"); ax.set_ylim(0.005, None); ax.set_ylabel("Cases per 1,000 residents per week (log scale)")
for a, b, lab, sh in [("2021-06-16", "2021-12-15", "Delta", "0.93"), ("2021-12-16", "2022-02-07", "Omicron", "0.85")]:
    ax.axvspan(pd.Timestamp(a), pd.Timestamp(b), color=sh, zorder=0); ax.text(pd.Timestamp(a) + (pd.Timestamp(b) - pd.Timestamp(a)) / 2, ax.get_ylim()[1] * 0.6, lab, ha="center", color="0.35")
ax.spines[["top", "right"]].set_visible(False); ax.legend(frameon=False, loc="upper left"); ax.set_xlim(pd.Timestamp("2020-03-01"), pd.Timestamp("2022-02-07"))
ax.set_title("Sydney's COVID-19 cases on each side of the Latte Line", loc="left", fontsize=12)
fig.text(0.01, 0.01, "NSW Health confirmed cases by postcode of residence (PCR), shared to suburbs by the ABS postcode–suburb correspondence; 2021 Census population.", fontsize=7, color="0.4")
fig.tight_layout(rect=(0, 0.03, 1, 1)); out = f"{ROOT}/results/covid/fig_covid_sides.png"; fig.savefig(out); print(out)
pk = t.loc["2021-06-01":"2021-12-15"]; print("Delta peak week per 1000:", pk.max().round(2).to_dict(), pk.idxmax().astype(str).to_dict())
