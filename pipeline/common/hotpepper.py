"""Download every restaurant HotPepper Gourmet lists for a Japanese city's prefecture.

1. Free key: https://webservice.recruit.co.jp/register (email sign-up)
2. pip install requests
3. python pipeline/common/hotpepper.py osaka YOUR_KEY hotpepper.csv

Writes the flat CSV the Tokyo pipeline uses, plus hotpepper_raw.jsonl (every field of every shop, so nothing
is lost) and hotpepper_drinks.csv: for each drinks filter (sake / shochu / wine / cocktail / all-you-can-drink),
the shop ids HotPepper returns when that filter is switched on. The script checks each filter actually narrows
the results and says so if it does not, rather than writing a meaningless column.
Anything shown publicly from this data must carry "Powered by ホットペッパー Webサービス".
"""
import csv, json, os, sys, time
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cities import CITIES

city, KEY, OUT = sys.argv[1:4]
API = "https://webservice.recruit.co.jp/hotpepper"
DRINK_FILTERS = ["sake", "shochu", "wine", "cocktail", "free_drink"]


def call(path, **params):
    params.update(key=KEY, format="json")
    for attempt in range(5):
        try:
            r = requests.get(f"{API}/{path}/v1/", params=params, timeout=60)
            if r.ok:
                j = r.json()["results"]
                if "error" in j: raise SystemExit(f"API error: {j['error']}")
                return j
            print("  http", r.status_code, "retrying")
        except requests.RequestException as e:
            print("  retry:", e)
        time.sleep(5 * (attempt + 1))
    raise SystemExit("gave up")


def every(**q):
    start, total = 1, None
    while total is None or start <= total:
        j = call("gourmet", count=100, start=start, **q); total = int(j["results_available"])
        yield from j.get("shop", []); start += 100; time.sleep(1)


area_name = CITIES[city]["hotpepper"]
area = [a["code"] for a in call("large_area")["large_area"] if a["name"] == area_name]
assert area, f"could not find {area_name} in HotPepper's area list"
genres = call("genre")["genre"]
print(area_name, area[0], "| genres:", ", ".join(f"{g['code']} {g['name']}" for g in genres))

base = os.path.splitext(OUT)[0]
seen = set()
with open(OUT, "w", newline="", encoding="utf-8") as fh, open(base + "_raw.jsonl", "w", encoding="utf-8") as raw:
    w = csv.writer(fh)
    w.writerow(["id", "name", "lat", "lng", "genre_code", "genre", "sub_genre", "genre_catch", "catch", "budget",
                "budget_avg", "open", "midnight", "station", "address", "url"])
    for g in genres:   # one genre at a time keeps every query small
        n = 0
        for s in every(large_area=area[0], genre=g["code"]):
            n += 1
            if s["id"] in seen: continue
            seen.add(s["id"]); raw.write(json.dumps(s, ensure_ascii=False) + "\n")
            w.writerow([s["id"], s["name"], s["lat"], s["lng"], s["genre"]["code"], s["genre"]["name"],
                        (s.get("sub_genre") or {}).get("name", ""), s["genre"].get("catch", ""), s.get("catch", ""),
                        s["budget"].get("name", ""), s["budget"].get("average", ""), s.get("open", ""), s.get("midnight", ""),
                        s.get("station_name", ""), s.get("address", ""), s["urls"]["pc"]])
        print(f"{g['code']} {g['name']}: {n}", flush=True)
print("wrote", len(seen), "shops ->", OUT)

everyone = int(call("gourmet", large_area=area[0], count=1)["results_available"])
with open(base + "_drinks.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["filter", "id"])
    for f in DRINK_FILTERS:
        n = int(call("gourmet", large_area=area[0], count=1, **{f: 1})["results_available"])
        if n >= everyone:
            print(f"filter {f}: ignored by the API ({n} of {everyone}), skipped"); continue
        ids = {s["id"] for g in genres for s in every(large_area=area[0], genre=g["code"], **{f: 1})}
        w.writerows([f, i] for i in ids); print(f"filter {f}: {len(ids)} of {everyone} shops")
