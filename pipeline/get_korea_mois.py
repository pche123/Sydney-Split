"""Download resident registration counts by neighbourhood and ten-year age band (MOIS, jumin.mois.go.kr), December of each
year, for every administrative neighbourhood in Korea; and the matching neighbourhood boundaries (github.com/vuski/admdongkor).
Runs on GitHub Actions (workflow "Fetch Korea over time"). Output: results/korea_time/mois_age_<year>12.csv, emd_<year>.parquet
"""
import os, subprocess, sys, time
from pathlib import Path
import requests

OUT = Path("results/korea_time"); OUT.mkdir(parents=True, exist_ok=True)
S = requests.Session(); S.headers["User-Agent"] = "Mozilla/5.0 (Sydney-Split research, github.com/pche123/Sydney-Split)"
S.get("https://jumin.mois.go.kr/ageStatMonth.do", timeout=60)
for y in range(2008, 2026):
    f = OUT / f"mois_age_{y}12.csv"
    if f.exists() and f.stat().st_size > 10000:
        continue
    form = dict(sltOrgType="1", sltOrgLvl1="1000000000", sltOrgLvl2="1000000000", gender="gender", sum="sum", sltUndefType="",
                searchYearStart=str(y), searchMonthStart="12", searchYearEnd=str(y), searchMonthEnd="12",
                sltOrderType="1", sltOrderValue="ASC", sltArgTypes="10", sltArgTypeA="0", sltArgTypeB="100", category="month")
    for t in range(4):
        try:
            r = S.post("https://jumin.mois.go.kr/downloadCsvAge.do?searchYearMonth=month&xlsStats=3", data=form, timeout=300)
            print(y, r.status_code, r.headers.get("content-type"), len(r.content), flush=True)
            if r.ok and len(r.content) > 10000:
                f.write_bytes(r.content); break
        except Exception as e:  # noqa: BLE001
            print(y, "retry", e, flush=True)
        time.sleep(20 * (t + 1))
    time.sleep(5)

# boundaries: the last file of each year
subprocess.run("GIT_LFS_SKIP_SMUDGE=1 git clone -q --depth 1 --filter=blob:none --no-checkout https://github.com/vuski/admdongkor /tmp/adm", shell=True, check=True)
names = subprocess.run("git -C /tmp/adm ls-tree -r --name-only HEAD parquet/", shell=True, capture_output=True, text=True).stdout.split()
import geopandas as gpd
for y in range(2008, 2026):
    c = sorted(n for n in names if n.startswith(f"parquet/emd_{y}"))
    if not c:
        print("no boundary for", y); continue
    subprocess.run(["git", "-C", "/tmp/adm", "checkout", "-q", "HEAD", "--", c[-1]], check=True)
    g = gpd.read_parquet(f"/tmp/adm/{c[-1]}")
    g = g[g.sidocd.astype(str).str[:2].isin(["11", "26", "28", "41"])]
    g.to_parquet(OUT / f"emd_{y}.parquet"); print("boundary", y, c[-1], len(g), flush=True)
