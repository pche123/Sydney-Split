"""Fetch the safety-and-sights layer for every city and boil it down to one small file per city.

Runs on GitHub Actions (workflow "Fetch safety data"), because it needs the open internet:
    python pipeline/get_safety.py [city ...]          (default: every city with app/public/downloads/<city>_areas.geojson)

Sources
  - River flood: JRC / Copernicus CEMS global river flood hazard map v2.1, 1-in-100-year return period, ~90 m
    (https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard/), categorised depth, permanent water excluded.
  - Japan: MLIT National Land Numerical Information A33 (landslide warning zones) and A40 (tsunami inundation zones),
    and GSI designated emergency evacuation sites (指定緊急避難場所, national CSV, with the hazards each site is designated for).
  - Everywhere: OpenStreetMap (Overpass) assembly points, hospitals, fire stations and sights.

Output: results/safety/<city>.json with, per area (same order as the app's areas), the share of land in each hazard zone,
and the points (lon/lat) with their kind. results/safety/log.txt records what was found and what was not.
"""
import csv, io, json, os, re, sys, time, zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
from cities import CITIES  # noqa: E402

OUT = ROOT / "results" / "safety"; OUT.mkdir(parents=True, exist_ok=True)
CACHE = Path(os.environ.get("SAFETY_CACHE", "/tmp/safety_cache")); CACHE.mkdir(parents=True, exist_ok=True)
LOG = open(OUT / "log.txt", "a", encoding="utf-8")
UA = {"User-Agent": "Sydney-Split research (github.com/pche123/Sydney-Split)"}

def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.write(s + "\n"); LOG.flush()

def get(url, path=None, tries=4, **kw):
    for t in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=600, stream=bool(path), **kw)
            r.raise_for_status()
            if path:
                with open(path, "wb") as f:
                    for ch in r.iter_content(1 << 20):
                        f.write(ch)
                return path
            return r
        except Exception as e:  # noqa: BLE001
            log("  retry", t + 1, url, e); time.sleep(10 * (t + 1))
    raise RuntimeError(f"failed: {url}")

# ---------------------------------------------------------------- OpenStreetMap
OSM_KINDS = {
    "assembly": '["emergency"="assembly_point"]',
    "hospital": '["amenity"="hospital"]',
    "fire": '["amenity"="fire_station"]',
    "sight": '["tourism"~"^(attraction|museum|gallery|viewpoint|zoo|aquarium|theme_park)$"]',
    "heritage": '["historic"~"^(castle|monument|ruins|archaeological_site|fort|city_gate)$"]',
}
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
            "https://overpass.private.coffee/api/interpreter"]

GF = "https://download.geofabrik.de"
OSM_EXTRA = {"auckland": "australia-oceania/new-zealand", "christchurch": "australia-oceania/new-zealand",
             "austin": "north-america/us/texas", "chicago": "north-america/us/illinois", "miami": "north-america/us/florida",
             "newyork": "north-america/us/new-york", "seattle": "north-america/us/washington",
             "washington": "north-america/us/district-of-columbia", "losangeles": "north-america/us/california/socal",
             "sanfrancisco": "north-america/us/california/norcal", "singapore": "asia/malaysia-singapore-brunei"}
FILTER = ["nwr/emergency=assembly_point", "nwr/amenity=hospital,fire_station",
          "nwr/tourism=attraction,museum,gallery,viewpoint,zoo,aquarium,theme_park",
          "nwr/historic=castle,monument,ruins,archaeological_site,fort,city_gate"]

def osm_url(c):
    return CITIES.get(c, {}).get("osm") or f"{GF}/{OSM_EXTRA[c]}-latest.osm.pbf"

def osm_filtered(url):
    """Download a Geofabrik extract once, keep only the objects we map (as GeoJSON lines), then delete the big file."""
    import subprocess
    out = CACHE / (os.path.basename(url).replace(".osm.pbf", "") + "_safety.geojsonseq")
    if out.exists():
        return out
    pbf = CACHE / os.path.basename(url); flt = CACHE / ("f_" + os.path.basename(url))
    import subprocess as sp
    for t in range(4):
        r = sp.run(["curl", "-sSfL", "--retry", "3", "--max-redirs", "50", "-c", str(CACHE / "cj"), "-b", str(CACHE / "cj"),
                    "-A", UA["User-Agent"], "-o", str(pbf), url])
        if r.returncode == 0 and pbf.exists() and pbf.stat().st_size > 1e6:
            break
        log(f"  curl retry {t + 1} {url} rc={r.returncode}"); time.sleep(60 * (t + 1))
    else:
        raise RuntimeError(f"failed: {url}")
    log(f"  downloaded {pbf.name}: {pbf.stat().st_size / 1e6:.0f} MB")
    subprocess.run(["osmium", "tags-filter", "--overwrite", "-o", str(flt), str(pbf), *FILTER], check=True)
    pbf.unlink()
    subprocess.run(["osmium", "export", "--overwrite", "-f", "geojsonseq", "-o", str(out), str(flt)], check=True)
    flt.unlink()
    return out

def osm_points(c, bb):
    W, S, E, N = bb; out = []
    from shapely.geometry import shape
    with open(osm_filtered(osm_url(c)), encoding="utf-8") as f:
        for line in f:
            line = line.strip().lstrip("\x1e")
            if not line:
                continue
            ft = json.loads(line); tg = ft.get("properties", {})
            try:
                pt = shape(ft["geometry"]).representative_point()
            except Exception:  # noqa: BLE001
                continue
            if not (W <= pt.x <= E and S <= pt.y <= N):
                continue
            if tg.get("emergency") == "assembly_point": k = "assembly"
            elif tg.get("amenity") == "hospital": k = "hospital"
            elif tg.get("amenity") == "fire_station": k = "fire"
            elif tg.get("tourism") or tg.get("historic"): k = "sight"
            else: continue
            nm = tg.get("name:en") or tg.get("name") or ""
            out.append(dict(k=k, n=nm[:60], lon=round(pt.x, 5), lat=round(pt.y, 5)))
    return out

# ---------------------------------------------------------------- Japan: GSI evacuation sites
GSI_CSV = "https://hinanmap.gsi.go.jp/hinanjocp/defaultFtpData/csv/mergeFromCity_2.csv"
HAZ = [("flood", "洪水"), ("landslide", "崖崩れ"), ("storm_surge", "高潮"), ("earthquake", "地震"), ("tsunami", "津波"),
       ("fire", "大規模な火事"), ("inland_flood", "内水氾濫"), ("volcano", "火山")]
_gsi = None
def gsi_sites():
    global _gsi
    if _gsi is None:
        p = CACHE / "gsi_emergency.csv"
        if not p.exists():
            get(GSI_CSV, p)
        raw = p.read_bytes()
        for enc in ("utf-8-sig", "cp932"):
            try:
                txt = raw.decode(enc); break
            except UnicodeDecodeError:
                continue
        df = pd.read_csv(io.StringIO(txt), dtype=str).fillna("")
        cols = list(df.columns); log("GSI columns:", cols)
        c_lat = next(c for c in cols if "緯度" in c); c_lon = next(c for c in cols if "経度" in c)
        c_nm = next(c for c in cols if "名" in c and ("施設" in c or "場所" in c))
        hz = {k: next((c for c in cols if j in c), None) for k, j in HAZ}
        rows = []
        for _, r in df.iterrows():
            try:
                la, lo = float(r[c_lat]), float(r[c_lon])
            except ValueError:
                continue
            h = [k for k, c in hz.items() if c and str(r[c]).strip() not in ("", "0", "×", "-")]
            rows.append(dict(k="shelter_jp", n=r[c_nm][:60], lon=round(lo, 5), lat=round(la, 5), h=h))
        _gsi = pd.DataFrame(rows); log("GSI sites:", len(_gsi), "hazard columns:", hz)
    return _gsi

# ---------------------------------------------------------------- Japan: MLIT hazard zones (A33 landslide, A40 tsunami)
KSJ = "https://nlftp.mlit.go.jp/ksj/gml"
_links = {}
def ksj_links(code):
    """{pref: url of the newest zip} for a National Land Numerical Information item, read off its download pages."""
    if code in _links:
        return _links[code]
    idx = get("https://nlftp.mlit.go.jp/ksj/index.html").text
    pages = sorted(set(re.findall(rf'gml/datalist/KsjTmplt-{code}[^"\']*?\.html', idx)))
    if not pages:
        pages = [f"gml/datalist/KsjTmplt-{code}-v{v}.html" for v in ("2_1", "2_0", "1_4", "1_3")]
    found = {}
    for pg in pages:
        try:
            html = get(f"https://nlftp.mlit.go.jp/ksj/{pg}", tries=1).text
        except Exception:  # noqa: BLE001
            continue
        for path in re.findall(rf"(/data/{code}/[^'\"\s]+?\.zip)", html):
            m = re.search(rf"{code}-(\d\d)_(\d\d)", path)
            if m:
                y, pref = m.groups()
                found.setdefault(pref, set()).add((y, KSJ + path))
    _links[code] = {p: [u for y, u in sorted(v, reverse=True)] for p, v in found.items()}
    log(f"KSJ {code}: {len(_links[code])} prefectures, e.g.", list(_links[code].items())[:2])
    return _links[code]

PREFS = {"tokyo": ["13", "11", "14"], "yokohama": ["14", "13"], "osaka": ["27", "28"], "kyoto": ["26"], "nagoya": ["23"],
         "kobe": ["28", "27"], "fukuoka": ["40"], "sapporo": ["01"]}

def zone_share(zones, F, res=25.0):
    """Share of each area's land inside the union of the zone polygons, on a 25 m grid."""
    from rasterio.features import rasterize
    from rasterio.transform import from_origin
    minx, miny, maxx, maxy = F.total_bounds
    w, h = int((maxx - minx) / res) + 1, int((maxy - miny) / res) + 1
    tr = from_origin(minx, maxy, res, res)
    lab = rasterize(((g, i + 1) for i, g in enumerate(F.geometry)), out_shape=(h, w), transform=tr, fill=0, dtype="int32")
    z = rasterize(((g, 1) for g in zones if g is not None and not g.is_empty), out_shape=(h, w), transform=tr, fill=0, dtype="uint8")
    ok = lab > 0
    tot = np.bincount(lab[ok] - 1, minlength=len(F)); hit = np.bincount(lab[ok] - 1, weights=z[ok], minlength=len(F))
    return np.where(tot > 0, hit / np.maximum(tot, 1), 0.0)

def ksj_zones(code, prefs, frame):
    urls = ksj_links(code); parts = []
    bb = tuple(frame.to_crs(4326).total_bounds)
    PLANE = {"01": 12, "13": 9, "14": 9, "11": 9, "23": 7, "26": 6, "27": 6, "28": 5, "40": 2}
    for pref in prefs:
        if pref not in urls:
            log(f"  {code} {pref}: no file"); continue
        for url in urls[pref]:
            got = _ksj_one(code, pref, url, bb, frame, PLANE, parts)
            if got:
                break
    if not parts:
        return None
    return pd.concat(parts)

def _ksj_one(code, pref, url, bb, frame, PLANE, parts):
        z = CACHE / os.path.basename(url)
        if not z.exists():
            get(url, z)
        srcs = []                                   # (zip path, member); unpacks zips inside the zip
        with zipfile.ZipFile(z) as zf:
            names = zf.namelist()
            for m in names:
                if m.lower().endswith(".zip"):
                    inner = CACHE / (z.stem + "__" + os.path.basename(m))
                    inner.write_bytes(zf.read(m))
                    with zipfile.ZipFile(inner) as zi:
                        srcs += [(inner, x) for x in zi.namelist()]
                else:
                    srcs.append((z, m))
        log(f"  {code} {pref}: files {[m for _, m in srcs][:12]}")
        gj = [(zp, m) for zp, m in srcs if m.lower().endswith(".geojson")]
        members = gj or [(zp, m) for zp, m in srcs if m.lower().endswith(".shp")]   # one copy of each layer, not both
        if not members:                                # newest years ship only JPGIS GML; try GDAL on it
            members = [(zp, m) for zp, m in srcs if m.lower().endswith(".xml") and "META" not in m.upper()
                       and os.path.basename(m.replace("\\", "/")).startswith(code)]
        read_ok = False
        for zp, m in members:
            try:
                g = gpd.read_file(f"zip://{zp}!{m}")
            except Exception as e:  # noqa: BLE001
                log("  read fail", m, e); continue
            g = g[g.geometry.notna()]
            read_ok = read_ok or bool(g.geometry.type.isin(["Polygon", "MultiPolygon"]).any())
            if len(g) and abs(g.total_bounds[0]) > 180:     # plane rectangular coordinates without a .prj
                g = g.set_crs(6668 + PLANE.get(pref, 9), allow_override=True)
            elif g.crs is None:
                g = g.set_crs(6668)
            g = g[g.geometry.type.isin(["Polygon", "MultiPolygon"])].to_crs(4326).cx[bb[0]:bb[2], bb[1]:bb[3]]
            log(f"    {m}: {len(g)} polygons in frame")
            if len(g):
                parts.append(g.geometry.to_crs(frame.crs))
        return read_ok

# ---------------------------------------------------------------- JRC river flood, 1-in-100-year
JRC = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard/RP100/"
_tiles = None
def jrc_share(areas_ll, frame):
    """Share of each area's land inside the 1-in-100-year river flood zone (categorised depth >= 1)."""
    import rasterio
    from rasterio.features import rasterize
    from rasterio.windows import from_bounds
    global _tiles
    if _tiles is None:
        _tiles = sorted(set(re.findall(r"ID\d+_[NS]\d+_[EW]\d+_RP100_depth_reclass\.tif", get(JRC).text)))
        log("JRC tiles listed:", len(_tiles))
    W, S, E, N = areas_ll.total_bounds
    def corner(t):
        m = re.search(r"_([NS])(\d+)_([EW])(\d+)_", t)
        lat = int(m.group(2)) * (1 if m.group(1) == "N" else -1); lon = int(m.group(4)) * (1 if m.group(3) == "E" else -1)
        return lon, lat
    cand = [t for t in _tiles if (lambda c: c[0] - 10 <= W <= c[0] + 10 and c[1] - 10 <= N <= c[1] + 10)(corner(t))]
    flooded = np.zeros(len(areas_ll)); cells = np.zeros(len(areas_ll)); used = []
    for t in cand:
        p = CACHE / t
        try:
            src = rasterio.open(f"/vsicurl/{JRC}{t}")
        except Exception:  # noqa: BLE001
            if not p.exists():
                get(JRC + t, p)
            src = rasterio.open(p)
        with src:
            b = src.bounds
            if b.right <= W or b.left >= E or b.top <= S or b.bottom >= N:
                continue
            win = from_bounds(max(W, b.left), max(S, b.bottom), min(E, b.right), min(N, b.top), src.transform).round_offsets().round_lengths()
            a = src.read(1, window=win); tr = src.window_transform(win)
            lab = rasterize(((g, i + 1) for i, g in enumerate(areas_ll.geometry)), out_shape=a.shape, transform=tr, fill=0, dtype="int32")
            ok = lab > 0
            np.add.at(cells, lab[ok] - 1, 1)
            np.add.at(flooded, lab[ok] - 1, ((a[ok] >= 1) & (a[ok] <= 4)).astype(float))
            used.append(t)
    log("  JRC tiles used:", used)
    return np.where(cells > 0, flooded / np.maximum(cells, 1), 0.0)

# ---------------------------------------------------------------- one city
def city(c):
    log(f"=== {c}")
    A = gpd.read_file(ROOT / f"app/public/downloads/{c}_areas.geojson")
    if A.crs is None:
        A = A.set_crs(4326)
    crs = CITIES.get(c, {}).get("crs") or A.estimate_utm_crs()
    F = A.to_crs(crs); land = F.area.values
    pop = A["population"].values if "population" in A else np.ones(len(A))
    W, S, E, N = A.to_crs(4326).total_bounds; bb = (W - 0.01, S - 0.01, E + 0.01, N + 0.01)
    res = dict(city=c, n=len(A), sources=[], areas={}, points=[])
    try:
        res["areas"]["flood"] = [round(float(x), 4) for x in jrc_share(A.to_crs(4326), F)]
        res["sources"].append("River flood: JRC/Copernicus CEMS global river flood hazard map v2.1, 1-in-100-year return period (~90 m)")
    except Exception as e:  # noqa: BLE001
        log("  flood failed:", e)
    try:
        pts = osm_points(c, bb)
    except Exception as e:  # noqa: BLE001
        log("  OSM failed:", e); pts = []
    log_pts = pts; log("  OSM points:", len(pts), pd.Series([p["k"] for p in pts]).value_counts().to_dict() if pts else {})
    if pts:
        res["sources"].append("Assembly points, hospitals, fire stations and sights: © OpenStreetMap contributors")
    if c in PREFS:
        for code, key, label in (("A33", "landslide", "Landslide warning zones: MLIT National Land Numerical Information A33"),
                                 ("A40", "tsunami", "Tsunami inundation zones: MLIT National Land Numerical Information A40")):
            try:
                U = ksj_zones(code, PREFS[c], F)
                if U is not None:
                    res["areas"][key] = [round(float(x), 4) for x in zone_share(U, F)]
                    res["sources"].append(label)
            except Exception as e:  # noqa: BLE001
                log(f"  {code} failed:", e)
        try:
            G = gsi_sites()
            G = G[(G.lon >= bb[0]) & (G.lon <= bb[2]) & (G.lat >= bb[1]) & (G.lat <= bb[3])]
            pts += G.to_dict("records"); log("  GSI sites in frame:", len(G))
            res["sources"].append("Designated emergency evacuation sites: GSI (国土地理院) 指定緊急避難場所データ")
        except Exception as e:  # noqa: BLE001
            log("  GSI failed:", e)
    # points -> area index (points outside every area are kept for the map but not counted)
    if pts:
        P = gpd.GeoDataFrame(pts, geometry=gpd.points_from_xy([p["lon"] for p in pts], [p["lat"] for p in pts]), crs=4326).to_crs(crs)
        j = gpd.sjoin(P, F[["geometry"]], predicate="within", how="left")
        j = j[~j.index.duplicated()]
        P["a"] = j["index_right"].fillna(-1).astype(int).values
        for k in ("assembly", "hospital", "fire", "sight", "shelter_jp"):
            cnt = np.bincount(P.a[(P.k == k) & (P.a >= 0)], minlength=len(F))
            if cnt.sum():
                res["areas"][f"n_{k}"] = cnt.tolist()
        res["points"] = [{kk: v for kk, v in r.items() if kk != "geometry" and not (kk == "h" and not isinstance(v, list))}
                         for r in P.drop(columns="geometry").to_dict("records")]
    res["land_km2"] = [round(float(x) / 1e6, 3) for x in land]; res["pop"] = [int(x) for x in pop]
    json.dump(res, open(OUT / f"{c}.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    log(f"  wrote {c}: layers {list(res['areas'])}, {len(res['points'])} points")

if __name__ == "__main__":
    todo = sys.argv[1:] or sorted(p.name.replace("_areas.geojson", "") for p in (ROOT / "app/public/downloads").glob("*_areas.geojson"))
    todo = sorted(todo, key=lambda c: (osm_url(c), c))
    for i, c in enumerate(todo):
        try:
            city(c)
        except Exception as e:  # noqa: BLE001
            log(f"!! {c} failed: {e}")
        if i + 1 == len(todo) or osm_url(todo[i + 1]) != osm_url(c):
            for f in CACHE.glob("*_safety.geojsonseq"):
                f.unlink()
