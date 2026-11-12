"""Download every Tokyo restaurant listed on HotPepper Gourmet (all genres, incl. ラーメン G013).

1. Get a free key: https://webservice.recruit.co.jp/register  (email sign-up, key arrives by email)
2. pip install requests
3. python hotpepper_tokyo.py YOUR_KEY hotpepper_tokyo.csv

About 10-15 minutes (one request per second, 100 shops per request).
Anything shown publicly from this data must carry the credit "Powered by ホットペッパー Webサービス".
"""
import csv, sys, time, requests

KEY, OUT = sys.argv[1], sys.argv[2]
API = "https://webservice.recruit.co.jp/hotpepper"

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

tokyo = [a["code"] for a in call("large_area")["large_area"] if a["name"] == "東京"]
assert tokyo, "could not find Tokyo in the area list"
genres = call("genre")["genre"]
print("Tokyo code", tokyo[0], "| genres:", ", ".join(f"{g['code']} {g['name']}" for g in genres))

seen = set()
with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "name", "lat", "lng", "genre_code", "genre", "sub_genre", "genre_catch", "catch", "budget",
                "budget_avg", "open", "midnight", "station", "address", "url"])
    for g in genres:
        start, total = 1, None
        while total is None or start <= total:
            j = call("gourmet", large_area=tokyo[0], genre=g["code"], count=100, start=start)
            total = int(j["results_available"])
            for s in j.get("shop", []):
                if s["id"] in seen: continue
                seen.add(s["id"])
                w.writerow([s["id"], s["name"], s["lat"], s["lng"], s["genre"]["code"], s["genre"]["name"],
                            (s.get("sub_genre") or {}).get("name", ""), s["genre"].get("catch", ""), s.get("catch", ""),
                            s["budget"].get("name", ""), s["budget"].get("average", ""), s.get("open", ""), s.get("midnight", ""),
                            s.get("station_name", ""), s.get("address", ""), s["urls"]["pc"]])
            print(f"{g['code']} {g['name']}: {min(start + 99, total)}/{total}", flush=True)
            start += 100; time.sleep(1)
print("wrote", len(seen), "shops ->", OUT)
