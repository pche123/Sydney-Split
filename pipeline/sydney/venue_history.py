"""Yearly venue counts per Sydney suburb from OpenStreetMap history (ohsome API).

Run on your own machine (needs internet; ~5-15 min):
    pip install requests
    python venue_history.py sydney_sa2_300.geojson venue_history.csv

Output: one row per suburb x year x venue type, with the count of OSM
features that existed on 1 January of that year.

Caveat: OSM coverage grew a lot after 2012, so raw counts rise everywhere.
That's why the script also counts "all_pois" (every shop/amenity) as a
mapping-effort baseline. The analysis uses shares, not raw counts.
"""
import json, sys, time, csv
import requests

URL = "https://api.ohsome.org/v1/elements/count/groupBy/boundary"
YEARS = "2012-01-01/2026-01-01/P1Y"
GEO = "(geometry:point or geometry:polygon)"

FILTERS = {
    "cafe": "amenity=cafe",
    "fast_food": "amenity=fast_food",
    "bar": "amenity in (bar, pub)",
    "red_rooster": 'brand="Red Rooster" or name="Red Rooster"',
    "messina": 'brand="Gelato Messina" or name~"Messina"',
    "mcdonalds": "brand=\"McDonald's\" or name=\"McDonald's\"",
    "aldi": "brand=ALDI or name=ALDI",
    "bubble_tea": "cuisine~bubble_tea",
    "all_pois": "amenity=* or shop=*",
}

def batches(feats, n=40):
    for i in range(0, len(feats), n):
        yield {"type": "FeatureCollection", "features": feats[i:i + n]}

def main(geojson, out):
    feats = json.load(open(geojson))["features"]
    for f in feats:  # ohsome uses the feature "id" to label each boundary
        f["id"] = f["properties"]["id"]
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["sa2", "year", "venue", "count"])
        for venue, flt in FILTERS.items():
            for k, fc in enumerate(batches(feats)):
                data = {"bpolys": json.dumps(fc), "time": YEARS,
                        "filter": f"({flt}) and {GEO}"}
                for attempt in range(5):
                    r = requests.post(URL, data=data, timeout=300)
                    if r.ok:
                        break
                    print("  retry", venue, k, r.status_code); time.sleep(10 * (attempt + 1))
                r.raise_for_status()
                for g in r.json()["groupByResult"]:
                    for res in g["result"]:
                        w.writerow([g["groupByObject"], res["timestamp"][:4], venue, int(res["value"])])
                print(venue, "batch", k + 1, "done", flush=True)
                time.sleep(1)
    print("wrote", out)

if __name__ == "__main__":
    main(*sys.argv[1:3])
