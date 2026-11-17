"""Phase 3 venues: download the OpenStreetMap country files and cut shops and cafés for each Phase 3 city. Any OS.

    python get_phase3_osm.py

Needs pyosmium (installed automatically with pip if missing). Downloads into <home>/Downloads/phase3_osm/, skips
files and cities already done, and writes <home>/Downloads/upload_phase3_osm.zip (small).
"""
import csv, os, subprocess, sys, time, urllib.request, zipfile
from pathlib import Path

try:
    import osmium
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "osmium"]); import osmium

HOME = Path.home() / "Downloads"; ROOT = HOME / "phase3_osm"; ROOT.mkdir(exist_ok=True)
GF = "https://download.geofabrik.de/"
FILES = {"netherlands": "europe/netherlands-latest.osm.pbf", "sweden": "europe/sweden-latest.osm.pbf",
         "denmark": "europe/denmark-latest.osm.pbf", "sudeste": "south-america/brazil/sudeste-latest.osm.pbf"}
CITIES = {"netherlands": {"amsterdam": (4.75, 52.30, 5.05, 52.43), "rotterdam": (4.40, 51.86, 4.60, 51.96),
                          "thehague": (4.20, 52.02, 4.40, 52.13), "utrecht": (5.03, 52.05, 5.18, 52.13)},
          "sweden": {"stockholm": (17.85, 59.25, 18.20, 59.40), "gothenburg": (11.85, 57.64, 12.10, 57.76), "malmo": (12.93, 55.53, 13.10, 55.63)},
          "denmark": {"copenhagen": (12.40, 55.60, 12.70, 55.75), "aarhus": (10.08, 56.10, 10.26, 56.21)},
          "sudeste": {"saopaulo": (-46.83, -24.01, -46.36, -23.36)}}
KEEP = ("amenity", "shop", "leisure", "tourism", "craft", "healthcare", "office", "club", "sport")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130 Safari/537.36"}


def wanted(tags):
    return any(k in tags for k in KEEP) or tags.get("railway") == "station" or tags.get("public_transport") == "station"


class H(osmium.SimpleHandler):
    def __init__(self, outs):
        super().__init__(); self.outs = outs

    def emit(self, oid, lat, lon, tags):
        d = None
        for (W, S, E, N), w in self.outs:
            if W <= lon <= E and S <= lat <= N:
                d = d or repr({t.k: t.v for t in tags}); w.writerow([oid, round(lat, 7), round(lon, 7), d])

    def node(self, n):
        if wanted(n.tags): self.emit(n.id, n.location.lat, n.location.lon, n.tags)

    def way(self, w):
        if not wanted(w.tags): return
        pts = [(nd.lat, nd.lon) for nd in w.nodes if nd.location.valid()]
        if pts: self.emit(w.id, sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts), w.tags)


for country, cities in CITIES.items():
    todo = {c: b for c, b in cities.items() if not (ROOT / c / "places.csv").exists()}
    if not todo: print(country, "done already"); continue
    pbf = ROOT / f"{country}-latest.osm.pbf"
    if not pbf.exists() or pbf.stat().st_size < 1_000_000:
        print("downloading", country, flush=True); tmp = pbf.with_suffix(".part")
        with urllib.request.urlopen(urllib.request.Request(GF + FILES[country], headers=UA), timeout=3600) as r, open(tmp, "wb") as f:
            while True:
                b = r.read(1 << 22)
                if not b: break
                f.write(b)
        tmp.replace(pbf)
    print(f"{country}: reading {pbf.stat().st_size >> 20} MB for {', '.join(todo)} ...", flush=True); t = time.time()
    files, outs = [], []
    for c, box in todo.items():
        (ROOT / c).mkdir(exist_ok=True); f = open(ROOT / c / "places.csv.part", "w", newline="", encoding="utf-8")
        w = csv.writer(f); w.writerow(["osm_id", "lat", "lon", "tags"]); files.append((c, f)); outs.append((box, w))
    idx = str(ROOT / f"{country}.nodecache")
    H(outs).apply_file(str(pbf), locations=True, idx=f"dense_file_array,{idx}" if os.name != "nt" else "flex_mem")
    for c, f in files:
        f.close(); os.replace(ROOT / c / "places.csv.part", ROOT / c / "places.csv")
        print(f"   {c}: {sum(1 for _ in open(ROOT / c / 'places.csv', encoding='utf-8')) - 1} places", flush=True)
    if os.path.exists(idx): os.remove(idx)
    print(f"{country}: {time.time() - t:.0f} s", flush=True)

zp = HOME / "upload_phase3_osm.zip"; zp.unlink(missing_ok=True)
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for p in ROOT.glob("*/places.csv"): z.write(p, p.relative_to(ROOT))
print(f"\nDONE: {zp} ({zp.stat().st_size >> 20} MB). Upload it.")
