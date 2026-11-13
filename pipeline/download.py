"""Download every open data file a city needs, into one folder per city.

    pip install requests
    python pipeline/download.py melbourne                 # everything automatic for Melbourne
    python pipeline/download.py osaka --only census,osm   # just some parts
    python pipeline/download.py london --out D:/split_raw

Parts: census (tables, all years), boundaries, osm, venues (licences, gaming, hygiene ratings).
Files already on disk are skipped, so it is safe to re-run after a dropped connection.
Anything that needs a key, a form or a fee is printed at the end as a manual step (see DATA_SOURCES.md).
"""
import argparse, json, os, re, sys, time
import requests

sys.path.insert(0, os.path.dirname(__file__))
from cities import CITIES, LONDON_BOROUGHS

UA = {"User-Agent": "Mozilla/5.0 (split-lines data kit)"}
MANUAL = []


def get(url, path, min_bytes=500, **kw):
    """Fetch url to path unless it is already there. Returns True when the file is on disk."""
    if os.path.exists(path) and os.path.getsize(path) > min_bytes:
        print("  have", os.path.relpath(path)); return True
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for attempt in range(3):
        try:
            with requests.get(url, timeout=300, headers=UA, stream=True, **kw) as r:
                if not r.ok:
                    print("  missing", r.status_code, url); return False
                tmp = path + ".part"
                with open(tmp, "wb") as fh:
                    for chunk in r.iter_content(1 << 20): fh.write(chunk)
            head = open(tmp, "rb").read(300).lstrip().lower()
            if os.path.getsize(tmp) < min_bytes or head.startswith((b"<!doctype", b"<html")):
                os.remove(tmp); print("  not a data file:", url); return False
            os.replace(tmp, path); print("  ok", os.path.relpath(path), f"{os.path.getsize(path) >> 10} KB"); return True
        except requests.RequestException as e:
            print("  retry", e); time.sleep(10 * (attempt + 1))
    return False


def ckan_latest(portal, package, fmt=("xlsx", "csv")):
    """URL of the newest resource of a CKAN dataset (data.vic, data.nsw, data.gov.au all speak CKAN)."""
    r = requests.get(f"{portal}/api/3/action/package_show", params={"id": package}, headers=UA, timeout=60).json()
    res = [x for x in r["result"]["resources"] if (x.get("format") or "").lower() in fmt]
    res.sort(key=lambda x: x.get("last_modified") or x.get("created") or "", reverse=True)
    return res[0]["url"] if res else None


# ===================================================================== Australia
ABS = "https://www.abs.gov.au"
DATAPACK = f"{ABS}/census/find-census-data/datapacks/download"
ASGS = f"{ABS}/statistics/standards/australian-statistical-geography-standard-asgs/edition-3-july-2021-june-2026/access-and-downloads/digital-boundary-files"


def au(city, c, out, parts):
    st = c["state"]
    if "census" in parts:
        print("ABS Census DataPacks (SA2, short headers)")
        get(f"{DATAPACK}/2021_GCP_SA2_for_{st}_short-header.zip", f"{out}/census/2021_GCP_SA2_{st}.zip")
        get(f"{DATAPACK}/2021_GCP_SA1_for_{st}_short-header.zip", f"{out}/census/2021_GCP_SA1_{st}.zip")
        get(f"{DATAPACK}/2021_TSP_SA2_for_{st}_short-header.zip", f"{out}/census/2021_TSP_SA2_{st}.zip")   # 2011/2016/2021 on 2021 SA2s
        get(f"{DATAPACK}/2016_TSP_SA2_for_{st}_short-header.zip", f"{out}/census/2016_TSP_SA2_{st}.zip")   # 2006/2011/2016 on 2016 SA2s
        get(f"{DATAPACK}/2011_TSP_SA2_for_AUST_short-header.zip", f"{out}/census/2011_TSP_SA2_AUST.zip")   # 2001/2006/2011 (Australia-wide only)
    if "boundaries" in parts:
        print("ABS boundaries (ASGS 2021, and the old SA2 maps for the timeline)")
        for f in ["SA2_2021_AUST_SHP_GDA2020.zip", "SA1_2021_AUST_SHP_GDA2020.zip", "GCCSA_2021_AUST_SHP_GDA2020.zip",
                  "SAL_2021_AUST_GDA2020_SHP.zip", "LGA_2021_AUST_GDA2020_SHP.zip"]:
            get(f"{ASGS}/{f}", f"{out}/boundaries/{f}")
        get(f"{DATAPACK}/2016_SA2_shape.zip", f"{out}/boundaries/2016_SA2_shape.zip")
        get(f"{DATAPACK}/2011_SA2_shape.zip", f"{out}/boundaries/2011_SA2_shape.zip")
    if "venues" in parts:
        print("Liquor and gaming venues")
        lic = c.get("licences")
        if city == "sydney":
            u = ckan_latest("https://data.nsw.gov.au/data", "nsw-liquor-licence-premises-list")
            u and get(u, f"{out}/venues/nsw_premises_list{os.path.splitext(u)[1]}")
        elif lic == "vic":
            u = ckan_latest("https://discover.data.vic.gov.au", "victorian-liquor-licences-by-location")
            u and get(u, f"{out}/venues/vic_liquor_licences.xlsx")
            u = ckan_latest("https://discover.data.vic.gov.au", "current-gaming-expenditure-by-venue")
            u and get(u, f"{out}/venues/vic_gaming_by_venue.xlsx")
            u = ckan_latest("https://discover.data.vic.gov.au", "historical-gaming-expenditure-by-venue")
            u and get(u, f"{out}/venues/vic_gaming_by_venue_history.xlsx")
        elif lic == "qld":
            MANUAL.append("Brisbane licences: Queensland has no bulk list. Use OSM pubs/bars/bottle shops (automatic), "
                          "or search https://secure.olgr.qld.gov.au/forms/lls and save results, or ask OLGR for an extract "
                          "(RTI request). Gaming machine venue lists: https://www.publications.qld.gov.au search 'gaming machine sites'.")
        elif lic == "wa":
            MANUAL.append("Perth licences: WA sells the list (\"List of licensed premises, electronic format\", about $70) from "
                          "rgl@lgirs.wa.gov.au. Free alternative: OSM pubs/bars/bottle shops. WA has no pub or club pokies, "
                          "so there is no Pokies line for Perth (a real finding, not a gap).")


# ===================================================================== Japan
ESTAT = "https://www.e-stat.go.jp/gis/statmap-search/data"
JP_TABLES = {  # small-area (町丁・字等) tables by census year
    "2020": ["T001081", "T001082", "T001083", "T001084", "T001085", "T001086", "T001103", "T001104", "T001106"],
    "2015": ["T000848", "T000849", "T000850", "T000851", "T000852", "T000853", "T000865", "T000866", "T000875"],
    "2010": ["T000572", "T000573", "T000574", "T000575", "T000576", "T000577", "T000587", "T000614", "T000615"],
    "2005": ["T000050", "T000051", "T000053", "T000054", "T000055", "T000056", "T000070", "T000149", "T000150"],
    "2000": ["T000001", "T000002", "T000003", "T000004", "T000005", "T000006", "T000007", "T000008", "T000010", "T000011"],
}


def jp(city, c, out, parts):
    p = c["pref"]
    if "census" in parts or "boundaries" in parts:
        print(f"e-Stat small areas, prefecture {p}")
        for year, codes in JP_TABLES.items():
            if "boundaries" in parts:
                get(f"{ESTAT}?dlserveyId=A00200521{year}&code={p}&coordSys=1&format=shape&downloadType=5",
                    f"{out}/census/{year}/boundaries_{year}.zip")
            if "census" in parts:
                for t in codes:
                    get(f"{ESTAT}?statsId={t}&code={p}&downloadType=2", f"{out}/census/{year}/{t}.zip"); time.sleep(1)
        MANUAL.append(f"{c['name']} extra tables (foreign residents, degrees, commute mode) are not in the small-area "
                      "download. Get them from the e-Stat database (2020 Census, 町丁・字等 tables) by hand or with an "
                      "e-Stat API appId: https://www.e-stat.go.jp/api/ . The Tokyo versions were h02_13, h13_13, h17_02_13.")
    if "venues" in parts:
        MANUAL.append(f"{c['name']} restaurants: HotPepper needs a free key (https://webservice.recruit.co.jp/register). "
                      f"Then: python pipeline/common/hotpepper.py {city} YOUR_KEY {out}/venues/hotpepper.csv")


# ===================================================================== UK
NOMIS = "https://www.nomisweb.co.uk/output/census/2021"
UK_TABLES = {"ts001": "residents", "ts003": "household composition", "ts004": "country of birth", "ts007a": "age (5-year)",
             "ts017": "household size", "ts021": "ethnic group", "ts030": "religion", "ts044": "accommodation type",
             "ts045": "car or van availability", "ts054": "tenure", "ts058": "distance travelled to work",
             "ts059": "hours worked", "ts060": "industry", "ts061": "method of travel to work", "ts062": "NS-SeC",
             "ts063": "occupation", "ts066": "economic activity", "ts067": "highest qualification", "ts037": "general health"}
ONS_FS = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services"
MSOA = "Middle_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V3"
LSOA = "Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V5"


def arcgis_geojson(service, where, path):
    """Page through an ONS ArcGIS FeatureServer layer and save one GeoJSON."""
    if os.path.exists(path): print("  have", os.path.relpath(path)); return
    feats, off = [], 0
    while True:
        r = requests.get(f"{ONS_FS}/{service}/FeatureServer/0/query", headers=UA, timeout=300, params=dict(
            where=where, outFields="*", outSR=4326, f="geojson", resultOffset=off, resultRecordCount=2000)).json()
        feats += r.get("features", []); off += 2000
        if len(r.get("features", [])) < 2000: break
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump({"type": "FeatureCollection", "features": feats}, open(path, "w"))
    print("  ok", os.path.relpath(path), len(feats), "areas")


def uk(city, c, out, parts):
    if "census" in parts:
        print("Nomis Census 2021 bulk tables (every geography incl. MSOA and LSOA)")
        for t in UK_TABLES:
            get(f"{NOMIS}/census2021-{t}.zip", f"{out}/census/census2021-{t}.zip")
        MANUAL.append("London timeline (2011): Nomis 2011 bulk tables, https://www.nomisweb.co.uk/sources/census_2011_ks "
                      "(KS101EW population, KS605EW industry, KS608EW occupation) plus the MSOA 2011->2021 lookup on the "
                      "ONS Open Geography Portal. Optional; the 2021 tables are enough for the lines.")
    if "boundaries" in parts:
        print("ONS boundaries (MSOA and LSOA 2021, London only)")
        where = " OR ".join(f"MSOA21NM LIKE '{b} %'" for b in LONDON_BOROUGHS)
        arcgis_geojson(MSOA, where, f"{out}/boundaries/msoa2021_london.geojson")
        arcgis_geojson(LSOA, where.replace("MSOA21NM", "LSOA21NM"), f"{out}/boundaries/lsoa2021_london.geojson")
    if "venues" in parts:
        print("Food Standards Agency hygiene ratings (every food business, with type and location)")
        try:
            auths = requests.get("https://api.ratings.food.gov.uk/Authorities", timeout=120,
                                 headers={**UA, "x-api-version": "2", "accept": "application/json"}).json()["authorities"]
            for a in auths:
                if a.get("RegionName") == "London":
                    nm = re.sub(r"\W+", "_", a["Name"])
                    get(a["FileName"], f"{out}/venues/fsa/{a['LocalAuthorityIdCode']}_{nm}.xml")
        except Exception as e:
            MANUAL.append(f"FSA list failed ({e}). Download the London XML files by hand from https://ratings.food.gov.uk/open-data")
        print("Gambling Commission premises register")
        try:
            page = requests.get("https://www.gamblingcommission.gov.uk/public-register/premises/download", headers=UA, timeout=60).text
            href = re.search(r'href="([^"]+\.(?:xlsx|csv))"', page)
            href and get(requests.compat.urljoin("https://www.gamblingcommission.gov.uk/", href.group(1)),
                         f"{out}/venues/gambling_premises{os.path.splitext(href.group(1))[1]}")
            href or MANUAL.append("Gambling premises: download premises-licence-register.xlsx from "
                                  "https://www.gamblingcommission.gov.uk/public-register/premises/download")
        except requests.RequestException as e:
            MANUAL.append(f"Gambling premises download failed ({e}); get it by hand from the Gambling Commission public register.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("city", choices=sorted(CITIES))
    ap.add_argument("--out", default=os.environ.get("SPLIT_RAW", "data"))
    ap.add_argument("--only", default="census,boundaries,osm,venues")
    a = ap.parse_args()
    c, parts = CITIES[a.city], set(a.only.split(","))
    out = os.path.join(a.out, a.city)
    print(f"== {c['name']} -> {out}\n   study area: {c['study']}")
    {"au": au, "jp": jp, "uk": uk}[c["country"]](a.city, c, out, parts)
    if "osm" in parts:
        print("OpenStreetMap extract (Geofabrik)")
        pbf = f"{a.out}/_osm/{os.path.basename(c['osm'])}"   # shared: Melbourne, Brisbane and Perth use the same file
        if get(c["osm"], pbf):
            print(f"  next: python pipeline/common/osm_places.py {a.city} {pbf} {out}/osm/places.csv")
    if MANUAL:
        print("\nManual steps:"); [print(" -", m) for m in MANUAL]


if __name__ == "__main__":
    main()
