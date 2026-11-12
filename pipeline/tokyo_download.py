"""Download every Tokyo Census file the timeline needs (2000, 2005, 2010, 2015) from e-Stat.

    pip install requests
    python tokyo_download.py tokyo_timeline

Makes tokyo_timeline/2000, .../2005 etc., one zip per table plus the boundary map.
Takes a few minutes. Zip the whole folder and upload it.
"""
import os, sys, time, requests

BASE = "https://www.e-stat.go.jp/gis/statmap-search/data"
TABLES = {  # small-area (町丁・字等) tables: population, age, household size, family type, tenure, building type, industry, occupation, economic type
    "2000": ["T000001", "T000002", "T000003", "T000004", "T000005", "T000006", "T000007", "T000008", "T000010", "T000011"],
    "2005": ["T000050", "T000051", "T000053", "T000054", "T000055", "T000056", "T000070", "T000149", "T000150"],
    "2010": ["T000572", "T000573", "T000574", "T000575", "T000576", "T000577", "T000587", "T000614", "T000615"],
    "2015": ["T000848", "T000849", "T000850", "T000851", "T000852", "T000853", "T000865", "T000866", "T000875"],
}

def get(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        print("  already have", os.path.basename(path)); return
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=120, headers={"User-Agent": "Mozilla/5.0"})
            if r.ok and len(r.content) > 500 and not r.content[:200].lstrip().lower().startswith(b"<!doctype"):
                open(path, "wb").write(r.content); print("  ok", os.path.basename(path), f"{len(r.content) // 1024} KB"); return
            print("  not available:", os.path.basename(path), r.status_code); return
        except requests.RequestException as e:
            print("  retry", os.path.basename(path), e); time.sleep(5)

out = sys.argv[1] if len(sys.argv) > 1 else "tokyo_timeline"
for year, codes in TABLES.items():
    d = os.path.join(out, year); os.makedirs(d, exist_ok=True); print(year)
    get(f"{BASE}?dlserveyId=A00200521{year}&code=13&coordSys=1&format=shape&downloadType=5", os.path.join(d, f"boundaries_{year}.zip"))
    for c in codes:
        get(f"{BASE}?statsId={c}&code=13&downloadType=2", os.path.join(d, f"{c}.zip"))
        time.sleep(1)
print("done ->", out)
