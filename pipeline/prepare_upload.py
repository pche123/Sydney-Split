"""Shrink the downloaded data (a few GB) into one small zip per city, ready to upload to Claude.

    pip install geopandas pyogrio scikit-learn scipy osmium openpyxl
    python pipeline/prepare_upload.py                 # every city that has a data/<city> folder
    python pipeline/prepare_upload.py osaka kyoto     # just these

What it does, per city:
  1. cuts its shops, cafes, bars, stations etc. out of the big OpenStreetMap file (one pass per file, all cities at once)
  2. picks the study areas and cuts every census table down to them (au_areas / jp_areas / uk_areas)
  3. makes one tidy venues file (licences, gaming, food businesses, OSM pubs and bottle shops)
  4. zips the results, plus the small files still needed later (HotPepper, older Japanese census years),
     into upload/<city>.zip
Every step is wrapped: if one fails it is logged in upload/<city>_log.txt (also inside the zip) and the rest go on.
Safe to re-run: finished steps are skipped.
"""
import contextlib, glob, io, os, shutil, sys, traceback, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "common"))
from cities import CITIES

RAW = os.environ.get("SPLIT_RAW", "data")
WORK, UP = "work", "upload"
cities = sys.argv[1:] or [c for c in CITIES if os.path.isdir(os.path.join(RAW, c)) and c not in ("sydney", "tokyo")]
os.makedirs(UP, exist_ok=True)
logs = {c: io.StringIO() for c in cities}


def step(city, name, fn):
    print(f"[{city}] {name}", flush=True)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            fn()
        logs[city].write(f"== {name}: ok\n{buf.getvalue()}\n")
        print("   ok", flush=True)
    except (Exception, SystemExit) as e:   # the helper scripts use SystemExit for "file missing"
        logs[city].write(f"== {name}: FAILED\n{buf.getvalue()}\n{traceback.format_exc()}\n")
        print(f"   FAILED ({e}); details in {UP}/{city}_log.txt", flush=True)


# ---------------------------------------------------------------- 1. OpenStreetMap, one pass per file
def osm_pass(pbf, group):
    import csv, osmium
    from osm_places import wanted

    class H(osmium.SimpleHandler):
        def __init__(self, outs):
            super().__init__(); self.outs = outs

        def emit(self, oid, lat, lon, tags):
            d = None
            for (W, S, E, N), w in self.outs:
                if W <= lon <= E and S <= lat <= N:
                    d = d or repr({t.k: t.v for t in tags})
                    w.writerow([oid, round(lat, 7), round(lon, 7), d])

        def node(self, n):
            if wanted(n.tags): self.emit(n.id, n.location.lat, n.location.lon, n.tags)

        def way(self, w):
            if not wanted(w.tags): return
            pts = [(nd.lat, nd.lon) for nd in w.nodes if nd.location.valid()]
            if pts: self.emit(w.id, sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts), w.tags)

    files, outs = [], []
    for c in group:
        os.makedirs(f"{RAW}/{c}/osm", exist_ok=True)
        fh = open(f"{RAW}/{c}/osm/places.csv.part", "w", newline="", encoding="utf-8"); files.append((c, fh))
        wr = csv.writer(fh); wr.writerow(["osm_id", "lat", "lon", "tags"]); outs.append((CITIES[c]["bbox"], wr))
    H(outs).apply_file(pbf, locations=True)
    for c, fh in files:
        fh.close(); os.replace(f"{RAW}/{c}/osm/places.csv.part", f"{RAW}/{c}/osm/places.csv")


groups = {}
for c in cities:
    if not os.path.exists(f"{RAW}/{c}/osm/places.csv"):
        groups.setdefault(f"{RAW}/_osm/{os.path.basename(CITIES[c]['osm'])}", []).append(c)
for pbf, group in groups.items():
    if not os.path.exists(pbf):
        for c in group: logs[c].write(f"== osm: FAILED, {pbf} not found\n")
        print("missing", pbf); continue
    print(f"OpenStreetMap: {os.path.basename(pbf)} -> {', '.join(group)} (5-15 minutes)", flush=True)
    try:
        osm_pass(pbf, group)
    except Exception:
        for c in group: logs[c].write(f"== osm: FAILED\n{traceback.format_exc()}\n")
        print("   FAILED; see the logs")

# ---------------------------------------------------------------- 2-4. areas, venues, zip
import au_areas, jp_areas, uk_areas, venues

for c in cities:
    cc, raw, out = CITIES[c], f"{RAW}/{c}", f"{WORK}/{c}"
    os.makedirs(out, exist_ok=True)
    if not os.path.exists(f"{out}/areas.gpkg"):
        if cc["country"] == "au":
            step(c, "areas + census", lambda: au_areas.main(c, raw, out))
        elif cc["country"] == "jp":
            step(c, "areas + census", lambda: jp_areas.main(c, f"{raw}/census/2020", out))
        else:
            step(c, "areas + census", lambda: uk_areas.main(c, raw, out))
    if not os.path.exists(f"{out}/venues.csv"):
        step(c, "venues", lambda: venues.main(c, raw, f"{out}/venues.csv"))

    keep = [f"{raw}/osm/places.csv"]
    keep += glob.glob(f"{raw}/venues/hotpepper*")                       # Japan: restaurants, raw JSON, drinks filters
    keep += glob.glob(f"{raw}/venues/sa_licences_*.xlsx") + glob.glob(f"{raw}/venues/vic_gaming*.xlsx")
    if cc["country"] == "jp":                                            # older census years, for the timeline
        keep += [z for z in glob.glob(f"{raw}/census/*/*.zip") if "/2020/" not in z.replace(os.sep, "/")]
    with open(f"{UP}/{c}_log.txt", "w") as fh:
        fh.write(logs[c].getvalue())
    zpath = f"{UP}/{c}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in glob.glob(f"{out}/**/*", recursive=True):
            if os.path.isfile(f): z.write(f, os.path.relpath(f, WORK))
        for f in keep:
            if os.path.isfile(f): z.write(f, os.path.join(c, "raw", os.path.relpath(f, raw)))
        z.write(f"{UP}/{c}_log.txt", f"{c}/log.txt")
    failed = "FAILED" in logs[c].getvalue()
    print(f"[{c}] -> {zpath} ({os.path.getsize(zpath) >> 20} MB){'  (some steps FAILED: send the zip anyway)' if failed else ''}", flush=True)

print(f"\nDone. Upload the files in {os.path.abspath(UP)}/ (one zip per city).")
