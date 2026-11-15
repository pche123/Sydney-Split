"""Usage: python pipeline/common/jp_extra.py <extras folder> <cities folder>
Turn the e-Stat 2020 small-area tables 2/13/17-2 into per-city census CSVs keyed like the others (muni + 4-digit 町)."""
import sys, os, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from cities import CITIES
EX, CI = sys.argv[1], sys.argv[2]   # folder with the e-Stat CSVs, folder with the city work folders
NAMES = {"h02": "X_foreign", "h13": "X_edu", "h17_02": "X_commute"}
def load(path):
    raw = pd.read_csv(path, encoding="cp932", header=None, dtype=str)
    hi = raw.index[raw.apply(lambda r: (r == "市区町村コード").any(), axis=1)][0]
    cols = []
    for j in range(raw.shape[1]):
        h = raw.iat[hi, j]
        if pd.isna(h) or h == "-":
            h = raw.iat[hi - 1, j]
        cols.append(str(h))
    d = raw.iloc[hi + 1:].copy(); d.columns = cols
    if "男女" in d.columns: d = d[d["男女"] == "総数"]
    code = d["町丁字コード"].astype(str)
    d = d[code.str.len() == 4]
    key = d["市区町村コード"].astype(str).str.zfill(5) + d["町丁字コード"]
    num = d.iloc[:, list(d.columns).index("字・丁目名") + 1:].apply(lambda s: pd.to_numeric(s, errors="coerce"))
    num = num.loc[:, ~num.columns.duplicated()]
    num.insert(0, "KEY_CODE", key.values)
    return num.groupby("KEY_CODE").sum().reset_index()
cache = {}
for c, C in CITIES.items():
    if C["country"] != "jp" or not os.path.isdir(f"{CI}/{c}"): continue
    pc = str(C["pref"]).zfill(2)
    for tab, nm in NAMES.items():
        f = [x for x in os.listdir(EX) if x.startswith(f"{tab}_{pc}_")]
        if not f: print("missing", c, tab); continue
        if f[0] not in cache: cache[f[0]] = load(f"{EX}/{f[0]}")
        d = cache[f[0]]; d.to_csv(f"{CI}/{c}/census/{nm}.csv", index=False)
        ua = pd.read_csv(f"{CI}/{c}/unit_area.csv", dtype={"U": str})
        print(c, nm, len(d), "rows; units matched", ua.U.isin(d.KEY_CODE).mean().round(3), list(d.columns)[1:6])
