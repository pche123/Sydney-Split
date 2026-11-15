"""Phase 1 downloads: 8 US cities, Auckland, Christchurch and Singapore. No keys or logins needed.

Run from your split_kit folder:   python ~/Downloads/download_phase1.py
Then send Claude the one file it makes: upload/phase1.zip

What it fetches (all public, open-licence data):
  USA        American Community Survey 2019-2023 5-year estimates by census tract (api.census.gov, keyless; set the
             CENSUS_KEY environment variable to use your own key) + Census Bureau tract boundaries
  NZ         2023 Census totals by topic for individuals and households by SA2 (Stats NZ ArcGIS services, CC BY 4.0)
  Singapore  Census of Population 2020 subzone tables (SingStat Table Builder) + URA Master Plan 2019 subzones (data.gov.sg)
  Everywhere OpenStreetMap shops, cafes, bars, gyms and stations (Overpass API, ODbL)
Safe to re-run: anything already downloaded is skipped. Takes about 30-60 minutes, mostly OpenStreetMap.
"""
import io, json, os, sys, time, zipfile
import requests

UA = {"User-Agent": "Mozilla/5.0 (Macintosh) split-research/1.0 (pche123.github.io/Sydney-Split)"}
KEY = os.environ.get("CENSUS_KEY", "")
kit = os.getcwd()
if not os.path.isdir(os.path.join(kit, "data")) and os.path.isdir(os.path.join(kit, "..", "data")): kit = os.path.abspath(os.path.join(kit, ".."))
if not os.path.isdir(os.path.join(kit, "data")): sys.exit("Run this from inside your split_kit folder (the one with 'data' in it).")
ROOT = os.path.join(kit, "data", "phase1"); os.makedirs(ROOT, exist_ok=True)
LOG = open(os.path.join(ROOT, "log.txt"), "a")
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.write(s + "\n"); LOG.flush()

def get(url, params=None, tries=4, timeout=300, **kw):
    for k in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=timeout, **kw)
            if r.status_code == 200: return r
            log("  HTTP", r.status_code, url[:120], r.text[:200].replace("\n", " "))
        except Exception as e:
            log("  error", type(e).__name__, str(e)[:150])
        time.sleep(5 * (k + 1))
    return None

def save(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True); open(path, "wb").write(content)

def have(path, min_bytes=200): return os.path.exists(path) and os.path.getsize(path) >= min_bytes

# ---------------------------------------------------------------- cities: bbox (W, S, E, N) and census areas
US = {   # state FIPS -> county FIPS
    "newyork":      ((-74.26, 40.49, -73.70, 40.92), {"36": ["005", "047", "061", "081", "085"]}),   # Bronx, Brooklyn, Manhattan, Queens, Staten Island
    "losangeles":   ((-118.70, 33.70, -117.85, 34.35), {"06": ["037"]}),
    "chicago":      ((-88.00, 41.64, -87.52, 42.10), {"17": ["031"]}),
    "sanfrancisco": ((-122.52, 37.70, -122.15, 37.90), {"06": ["075", "001"]}),                     # San Francisco + Alameda (Oakland, Berkeley)
    "washington":   ((-77.17, 38.79, -76.90, 39.00), {"11": ["001"], "51": ["013", "510"]}),        # DC + Arlington + Alexandria
    "austin":       ((-97.95, 30.13, -97.55, 30.52), {"48": ["453"]}),
    "seattle":      ((-122.45, 47.48, -122.22, 47.74), {"53": ["033"]}),
    "miami":        ((-80.45, 25.55, -80.11, 25.98), {"12": ["086"]}),
}
NZ = {"auckland": (174.55, -37.10, 175.00, -36.70), "christchurch": (172.50, -43.62, 172.78, -43.42)}
SG = {"singapore": (103.60, 1.20, 104.05, 1.48)}

# ---------------------------------------------------------------- USA: ACS 5-year by tract + tract shapes
ACS_YEAR = "2023"
ACS_TABLES = ["B01001",   # age by sex
              "B11001",   # household type (living alone)
              "B11005",   # households with people under 18
              "B25024",   # units in structure (detached vs flats)
              "B25003",   # tenure (own vs rent)
              "B25044",   # vehicles available by tenure
              "B15003",   # educational attainment 25+
              "C24010",   # occupation by sex (civilian employed 16+)
              "C24030",   # industry by sex
              "B08301",   # means of transportation to work (incl. bicycle, walked, worked from home)
              "B05002",   # place of birth (foreign born)
              "B05006",   # country of birth for the foreign-born (heritage maps)
              "B25064"]   # median gross rent
US_FAILS = []
def is_table(content):
    try:
        j = json.loads(content); return isinstance(j, list) and len(j) > 1
    except Exception:
        return False
def acs_get(st, co, t):
    base = f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5"
    for p in ({"get": f"group({t})", "for": "tract:*", "in": [f"state:{st}", f"county:{co}"]},
              {"get": f"group({t})", "for": "tract:*", "in": f"state:{st} county:{co}"}):
        if KEY: p["key"] = KEY
        r = get(base, p, tries=2)
        if r is None: continue
        if is_table(r.content): return r.content
        log(f"  census answered, but not with data ({t} {st}{co}). It said:", r.text[:300].replace("\n", " "))
    return None
def us_city(city, counties):
    if len(US_FAILS) >= 3: log(f"  skipping {city} census tables: the census site keeps refusing (see messages above)"); return
    d = os.path.join(ROOT, city, "census")
    for st, cos in counties.items():
        for co in cos:
            for t in ACS_TABLES:
                path = os.path.join(d, f"{t}_{st}{co}.json")
                if have(path) and is_table(open(path, "rb").read()): continue
                c = acs_get(st, co, t)
                if c is None:
                    US_FAILS.append((city, t))
                    if len(US_FAILS) >= 3: log("  census site refusing repeatedly; moving on to the other cities"); return
                    continue
                save(path, c); log(f"  {city} {t} {st}{co}: {len(json.loads(c)) - 1} tracts")
                time.sleep(0.4)
    for st in counties:
        path = os.path.join(ROOT, "_us_shapes", f"cb_{ACS_YEAR}_{st}_tract_500k.zip")
        if have(path, 10000): continue
        r = get(f"https://www2.census.gov/geo/tiger/GENZ{ACS_YEAR}/shp/cb_{ACS_YEAR}_{st}_tract_500k.zip")
        if r is not None and r.content[:2] == b"PK": save(path, r.content); log(f"  tract shapes {st}: {len(r.content) >> 10} KB")
        elif r is not None: log(f"  tract shapes {st}: not a zip, got:", r.text[:200])

# ---------------------------------------------------------------- New Zealand: Stats NZ ArcGIS feature services (2013, 2018, 2023)
NZ_SERVICES = {"individuals": "2023_Census_totals_by_topic_for_individuals_by_SA2",
               "households": "2023_Census_totals_by_topic_for_households_by_SA2"}
NZ_BASE = "https://services2.arcgis.com/vKb0s8tBIA3bdocZ/arcgis/rest/services/{}/FeatureServer"
def nz_city(city, box):
    for kind, svc in NZ_SERVICES.items():
        base = NZ_BASE.format(svc)
        meta = get(base, {"f": "json"})
        if meta is None: log(f"  {city} {kind}: service not reachable"); continue
        save(os.path.join(ROOT, city, "census", f"{kind}_service.json"), meta.content)
        layers = meta.json().get("layers", [])
        clipped = [l for l in layers if "clipped" in l["name"].lower()] or layers
        for lay in clipped:
            path = os.path.join(ROOT, city, "census", f"{kind}_layer{lay['id']}.geojson")
            if have(path, 1000): continue
            fields = get(f"{base}/{lay['id']}", {"f": "json"})
            if fields is not None: save(os.path.join(ROOT, city, "census", f"{kind}_layer{lay['id']}_fields.json"), fields.content)
            feats, off = [], 0
            while True:
                r = get(f"{base}/{lay['id']}/query", {"where": "1=1", "geometry": ",".join(map(str, box)), "geometryType": "esriGeometryEnvelope",
                                                     "inSR": 4326, "spatialRel": "esriSpatialRelIntersects", "outFields": "*", "outSR": 4326,
                                                     "f": "geojson", "resultOffset": off, "resultRecordCount": 1000})
                if r is None: break
                try: fs = r.json().get("features", [])
                except Exception: log("  NZ answered, but not with data:", r.text[:200]); break
                feats += fs; off += len(fs)
                if len(fs) < 1000: break
            save(path, json.dumps({"type": "FeatureCollection", "features": feats}).encode())
            log(f"  {city} {kind} layer {lay['id']} ({lay['name'][:60]}): {len(feats)} SA2s")

# ---------------------------------------------------------------- Singapore: SingStat Census 2020 subzone tables + URA subzones
def sg_city(city, box):
    d = os.path.join(ROOT, city, "census")
    found = {}
    for kw in ["subzone", "Subzone"]:
        r = get("https://tablebuilder.singstat.gov.sg/api/table/resourceid", {"keyword": kw, "searchOption": "all"})
        if r is None: continue
        try:
            for rec in r.json().get("Data", {}).get("records", []):
                t = rec.get("title", "")
                if "2020" in t and "ubzone" in t: found[rec["id"]] = t
        except Exception as e:
            log("  singstat search parse error", e)
    log(f"  singapore: {len(found)} Census 2020 subzone tables found")
    save(os.path.join(d, "tables_index.json"), json.dumps(found, indent=1).encode())
    for tid, title in found.items():
        path = os.path.join(d, f"table_{tid}.json")
        if have(path): continue
        r = get(f"https://tablebuilder.singstat.gov.sg/api/table/tabledata/{tid}", {"limit": 5000})
        if r is not None: save(path, r.content); log(f"  singapore table {tid}: {title[:90]}")
        time.sleep(0.5)
    # fallback / extra: Census 2020 subzone tables republished on data.gov.sg
    for ds, nm in [("d_7f243956483d5901f237e6f87b096636", "dwelling_type"), ("d_e7ae90176a68945837ad67892b898466", "ethnic_group")]:
        path = os.path.join(d, f"datagovsg_{nm}.csv")
        if have(path): continue
        r = get(f"https://api-open.data.gov.sg/v1/public/api/datasets/{ds}/poll-download")
        try:
            g = get(r.json()["data"]["url"])
            if g is not None: save(path, g.content); log(f"  singapore {nm} (data.gov.sg): {len(g.content) >> 10} KB")
        except Exception as e:
            log(f"  singapore {nm} failed:", e)
        time.sleep(2)
    # URA Master Plan 2019 subzone boundaries (no sea) from data.gov.sg
    path = os.path.join(d, "subzones_mp2019.geojson")
    if not have(path, 10000):
        for ds in ["d_8594ae9ff96d0c708bc2af633048edfb"]:
            r = get(f"https://api-open.data.gov.sg/v1/public/api/datasets/{ds}/poll-download")
            try:
                url = r.json()["data"]["url"]; g = get(url)
                if g is not None: save(path, g.content); log(f"  singapore subzones: {len(g.content) >> 10} KB")
            except Exception as e:
                log("  singapore subzones failed:", e, (r.text[:200] if r is not None else ""))

# ---------------------------------------------------------------- OpenStreetMap via Overpass (places only, not the whole map)
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
SELECT = ['nwr["amenity"]', 'nwr["shop"]', 'nwr["leisure"="fitness_centre"]', 'nwr["railway"~"^(station|halt)$"]',
          'nwr["public_transport"="station"]', 'nwr["station"="subway"]']
def osm_city(city, box):
    import csv
    path = os.path.join(ROOT, city, "raw", "osm", "places.csv")
    if have(path, 10000): return
    W, S, E, N = box; nx = ny = 2 if (E - W) * (N - S) > 0.08 else 1      # big cities in 4 tiles
    rows, seen = [], set()
    for i in range(nx):
        for j in range(ny):
            w, e = W + (E - W) * i / nx, W + (E - W) * (i + 1) / nx; s, n = S + (N - S) * j / ny, S + (N - S) * (j + 1) / ny
            q = f"[out:json][timeout:900];(" + "".join(f"{x}({s},{w},{n},{e});" for x in SELECT) + ");out center tags;"
            for k in range(6):
                r = None
                try: r = requests.post(OVERPASS[k % 2], data={"data": q}, headers=UA, timeout=1000)
                except Exception as ex: log("  overpass error", str(ex)[:100])
                if r is not None and r.status_code == 200: break
                log(f"  overpass busy ({r.status_code if r is not None else 'no answer'}), waiting"); time.sleep(60 * (k + 1)); r = None
            if r is None: log(f"  {city}: OSM tile {i},{j} FAILED"); continue
            try: els = r.json().get("elements", [])
            except Exception: log(f"  {city}: OSM tile {i},{j} gave no data:", r.text[:200]); continue
            for el in els:
                key = (el["type"], el["id"])
                if key in seen: continue
                seen.add(key); c = el.get("center", el)
                if "lat" in c: rows.append([el["id"], round(c["lat"], 7), round(c["lon"], 7), repr(el.get("tags", {}))])
            time.sleep(10)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f); wr.writerow(["osm_id", "lat", "lon", "tags"]); wr.writerows(rows)
    log(f"  {city}: {len(rows)} OSM places")

# ---------------------------------------------------------------- run
def safely(fn, *a):
    try: fn(*a)
    except Exception as e:
        import traceback; log(f"  FAILED {fn.__name__}{a[:1]}: {type(e).__name__}: {e}"); LOG.write(traceback.format_exc())
for city, (box, counties) in US.items():
    log(f"=== {city}"); safely(us_city, city, counties); safely(osm_city, city, box)
for city, box in NZ.items():
    log(f"=== {city}"); safely(nz_city, city, box); safely(osm_city, city, box)
for city, box in SG.items():
    log(f"=== {city}"); safely(sg_city, city, box); safely(osm_city, city, box)
if US_FAILS:
    log("\nThe US census site refused the requests. Usually that means it wants a free key:")
    log("  1. get one (takes a minute, arrives by email): https://api.census.gov/data/key_signup.html")
    log("  2. then run:   CENSUS_KEY=paste-your-key-here python ~/Downloads/download_phase1.py")
    log("  Everything already downloaded is kept; only the missing parts are fetched.")

os.makedirs(os.path.join(kit, "upload"), exist_ok=True)
out = os.path.join(kit, "upload", "phase1.zip")
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for dp, _, fs in os.walk(ROOT):
        for f in fs: z.write(os.path.join(dp, f), os.path.relpath(os.path.join(dp, f), os.path.dirname(ROOT)))
log(f"\nDone. Send upload/phase1.zip ({os.path.getsize(out) >> 20} MB) to Claude.")
if sys.platform == "darwin": os.system(f'open "{os.path.dirname(out)}"')
