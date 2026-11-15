"""Phase 2: cut the shops, cafes, bars, stations etc. for each city out of the big country OpenStreetMap files.

Run from your split_kit folder, after downloading the country files into data/phase2/_osm/:
    python ~/Downloads/cut_phase2_osm.py
Then zip the results (small) for upload:
    cd data && zip -rq ../upload/phase2_osm.zip phase2 -x "phase2/_osm/*"

One pass per country file, all of that country's cities at once (France and Germany take 20-40 minutes each).
The node index is kept on disk, not in memory, so it works on any machine. Safe to re-run: finished cities are skipped.
"""
import csv, os, sys, time
import osmium

ROOT = os.path.join("data", "phase2")
CITIES = {   # country file -> city: (W, S, E, N)
    "france": {"paris": (2.10, 48.72, 2.60, 49.00), "lyon": (4.75, 45.69, 4.98, 45.83), "marseille": (5.28, 43.20, 5.55, 43.42)},
    "germany": {"berlin": (13.08, 52.33, 13.77, 52.68), "munich": (11.36, 48.06, 11.72, 48.25), "hamburg": (9.73, 53.39, 10.33, 53.74)},
    "italy": {"rome": (12.30, 41.75, 12.65, 42.02), "milan": (9.04, 45.38, 9.28, 45.54)},
    "spain": {"madrid": (-3.84, 40.31, -3.52, 40.56), "barcelona": (2.05, 41.32, 2.25, 41.47)},
}
KEEP = ("amenity", "shop", "leisure", "tourism", "craft", "healthcare", "office", "club", "sport")


def wanted(tags):
    return any(k in tags for k in KEEP) or tags.get("railway") == "station" or tags.get("public_transport") == "station"


class H(osmium.SimpleHandler):
    def __init__(self, outs):
        super().__init__(); self.outs = outs; self.n = 0

    def emit(self, oid, lat, lon, tags):
        d = None
        for (W, S, E, N), w in self.outs:
            if W <= lon <= E and S <= lat <= N:
                d = d or repr({t.k: t.v for t in tags}); w.writerow([oid, round(lat, 7), round(lon, 7), d]); self.n += 1

    def node(self, n):
        if wanted(n.tags): self.emit(n.id, n.location.lat, n.location.lon, n.tags)

    def way(self, w):
        if not wanted(w.tags): return
        pts = [(nd.lat, nd.lon) for nd in w.nodes if nd.location.valid()]
        if pts: self.emit(w.id, sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts), w.tags)


for country, cities in CITIES.items():
    pbf = os.path.join(ROOT, "_osm", f"{country}-latest.osm.pbf")
    todo = {c: b for c, b in cities.items() if not os.path.exists(os.path.join(ROOT, c, "raw", "osm", "places.csv"))}
    if not todo: print(f"{country}: done already"); continue
    if not os.path.exists(pbf): print(f"{country}: {pbf} not found, skipped"); continue
    print(f"{country}: reading {os.path.getsize(pbf) >> 20} MB for {', '.join(todo)} ...", flush=True); t = time.time()
    files, outs = [], []
    for c, box in todo.items():
        os.makedirs(os.path.join(ROOT, c, "raw", "osm"), exist_ok=True)
        fh = open(os.path.join(ROOT, c, "raw", "osm", "places.csv.part"), "w", newline="", encoding="utf-8"); files.append((c, fh))
        wr = csv.writer(fh); wr.writerow(["osm_id", "lat", "lon", "tags"]); outs.append((box, wr))
    idx = os.path.join(ROOT, "_osm", f"{country}.nodes.idx")
    h = H(outs); h.apply_file(pbf, locations=True, idx=f"sparse_file_array,{idx}")
    for c, fh in files:
        fh.close(); os.replace(fh.name, fh.name[:-5])
    if os.path.exists(idx): os.remove(idx)
    print(f"{country}: {h.n:,} places in {(time.time() - t) / 60:.0f} minutes", flush=True)
print("\nDone. Now:  cd data && zip -rq ../upload/phase2_osm.zip phase2 -x \"phase2/_osm/*\"")
