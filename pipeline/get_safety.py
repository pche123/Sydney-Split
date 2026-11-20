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

def osm_points(bb):
    W, S, E, N = bb
    parts = "".join(f'nwr{q}({S},{W},{N},{E});' for q in OSM_KINDS.values())
    q = f"[out:json][timeout:600];({parts});out center tags;"
    for t in range(6):
        url = OVERPASS[t % len(OVERPASS)]
        try:
            r = requests.post(url, data={"data": q}, headers=UA, timeout=900); r.raise_for_status()
            els = r.json()["elements"]; break
        except Exception as e:  # noqa: BLE001
            log("  overpass retry", t + 1, url, e); time.sleep(30 * (t + 1))
    else:
        return []
    out = []
    for e in els:
        tg = e.get("tags", {}); lat = e.get("lat", e.get("center", {}).get("lat")); lon = e.get("lon", e.get("center", {}).get("lon"))
        if lat is None:
            continue
        if tg.get("emergency") == "assembly_point": k = "assembly"
        elif tg.get("amenity") == "hospital": k = "hospital"
        elif tg.get("amenity") == "fire_station": k = "fire"
        elif "tourism" in tg: k = "sight"
        else: k = "sight"   # historic sights count as sights
        nm = tg.get("name:en") or tg.get("name") or ""
        out.append(dict(k=k, n=nm[:60], lon=round(lon, 5), lat=round(lat, 5)))
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
                if pref not in found or y > found[pref][0]:
                    found[pref] = (y, KSJ + path)
    _links[code] = {p: u for p, (y, u) in found.items()}
    log(f"KSJ {code}: {len(_links[code])} prefectures, e.g.", list(_links[code].items())[:2])
    return _links[code]

PREFS = {"tokyo": ["13", "11", "14"], "yokohama": ["14", "13"], "osaka": ["27", "28"], "kyoto": ["26"], "nagoya": ["23"],
         "kobe": ["28", "27"], "fukuoka": ["40"], "sapporo": ["01"]}

def ksj_zones(code, prefs, frame):
    urls = ksj_links(code); parts = []
    for pref in prefs:
        if pref not in urls:
            log(f"  {code} {pref}: no file"); continue
        z = CACHE / os.path.basename(urls[pref])
        if not z.exists():
            get(urls[pref], z)
        with zipfile.ZipFile(z) as zf:
            members = [m for m in zf.namelist() if m.lower().endswith((".shp", ".geojson"))]
        for m in members:
            try:
                g = gpd.read_file(f"zip://{z}!{m}", bbox=tuple(frame.to_crs(4326).total_bounds))
            except Exception as e:  # noqa: BLE001
                log("  read fail", m, e); continue
            g = g[g.geometry.type.isin(["Polygon", "MultiPolygon"])]
            if len(g):
                if g.crs is None:
                    g = g.set_crs(6668)
                parts.append(g[["geometry"]].to_crs(frame.crs))
        log(f"  {code} {pref}: {sum(len(p) for p in parts)} polygons so far")
    if not parts:
        return None
    return pd.concat(parts).geometry.make_valid().union_all()

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
    pts = osm_points(bb); log("  OSM points:", len(pts), pd.Series([p["k"] for p in pts]).value_counts().to_dict() if pts else {})
    if pts:
        res["sources"].append("Assembly points, hospitals, fire stations and sights: © OpenStreetMap contributors")
    if c in PREFS:
        for code, key, label in (("A33", "landslide", "Landslide warning zones: MLIT National Land Numerical Information A33"),
                                 ("A40", "tsunami", "Tsunami inundation zones: MLIT National Land Numerical Information A40")):
            try:
                U = ksj_zones(code, PREFS[c], F)
                if U is not None:
                    res["areas"][key] = [round(float(g.intersection(U).area / max(a, 1)), 4) for g, a in zip(F.geometry, land)]
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
    for c in todo:
        try:
            city(c)
        except Exception as e:  # noqa: BLE001
            log(f"!! {c} failed: {e}")
