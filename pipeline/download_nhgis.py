"""US 1990-2020 on fixed 2010 census tracts, from NHGIS time series tables (IPUMS API).

    IPUMS_KEY=<your key> python download_nhgis.py

Picks every NHGIS time series table that is standardized to 2010 units, available for census tracts, and about
persons, age, households or tenure; requests them for tracts, all years; waits; saves the zip to ~/Downloads.
The key is read from the environment only and never written anywhere.
"""
import os, sys, time, json, urllib.request

KEY = os.environ.get("IPUMS_KEY") or sys.exit("Set IPUMS_KEY first")
API = "https://api.ipums.org"; Q = "collection=nhgis&version=2"
WANT = ("tenure", "age", "household", "persons by sex", "total population", "housing units", "occupancy")

import urllib.error
def call(path, body=None):
    req = urllib.request.Request(f"{API}{path}", data=None if body is None else json.dumps(body).encode(),
                                 headers={"Authorization": KEY, "Content-Type": "application/json"},
                                 method="GET" if body is None else "POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r: return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{e.code}: {e.read().decode(errors='replace')[:2000]}")

tables, page = [], f"/metadata/time_series_tables?{Q}&pageSize=2500"
while page:
    d = call(page); tables += d.get("data", [])
    nxt = (d.get("links") or {}).get("nextPage"); page = nxt.replace(API, "") if nxt else None
pick = []
for t in tables:
    if not any(w in t.get("description", "").lower() for w in WANT): continue
    if "2010" not in str(t.get("geographicIntegration", "")).lower() and "standardized to 2010" not in json.dumps(t).lower(): continue
    levels = [g.get("name", g) if isinstance(g, dict) else g for g in t.get("geogLevels", [])]
    if levels and "tract" not in levels:
        try:
            d = call(f"/metadata/time_series_tables/{t['name']}?{Q}")
            levels = [g.get("name", g) if isinstance(g, dict) else g for g in d.get("geogLevels", [])]
        except RuntimeError: continue
    if "tract" in levels: pick.append(t["name"])
print(f"{len(tables)} time series tables; picked {len(pick)}:", ", ".join(pick))
if not pick: sys.exit("No tables matched; send this output to Claude.")
body = lambda names: {"timeSeriesTables": {n: {"geogLevels": ["tract"]} for n in names},
                      "timeSeriesTableLayout": "time_by_column_layout", "dataFormat": "csv_header",
                      "description": "Split: US tracts 1990-2020 standardized to 2010"}
try:
    ext = call(f"/extracts?{Q}", body(pick))
except RuntimeError as err:      # drop any table NHGIS rejects, then try once more
    msg = str(err); print("NHGIS said:", msg[:500]); bad = [n for n in pick if n in msg]
    pick = [n for n in pick if n not in bad] if bad else pick[:20]
    print("retrying with", len(pick), "tables"); ext = call(f"/extracts?{Q}", body(pick))
n = ext["number"]; print("extract", n, "submitted; waiting (usually 5-30 minutes) ...", flush=True)
while True:
    s = call(f"/extracts/{n}?{Q}")
    if s.get("status") == "completed": break
    if s.get("status") == "failed": sys.exit(f"extract failed: {s}")
    time.sleep(30)
url = s["downloadLinks"]["tableData"]["url"]; out = os.path.expanduser("~/Downloads/upload_us_nhgis.zip")
with urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": KEY}), timeout=600) as r, open(out, "wb") as f:
    f.write(r.read())
print("saved", out)
