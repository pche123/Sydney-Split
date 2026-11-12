"""Cut Tokyo's shops, cafes, restaurants, bars and stations out of an OSM file.

Same output format as sydney_places.csv (osm_id, lat, lon, tags).

    pip install osmium
    python tokyo_places.py kanto-latest.osm.pbf tokyo_places.csv

Takes about 5-10 minutes on a laptop.
"""
import csv, sys
import osmium

# Tokyo-to without the islands: 23 wards + Tama
W, E, S, N = 138.94, 139.93, 35.48, 35.90
KEEP = ("amenity", "shop", "leisure", "tourism", "craft")

def wanted(tags):
    if any(k in tags for k in KEEP):
        return True
    return tags.get("railway") == "station" or tags.get("public_transport") == "station"

class H(osmium.SimpleHandler):
    def __init__(self, w):
        super().__init__(); self.w = w; self.n = 0

    def emit(self, oid, lat, lon, tags):
        if W <= lon <= E and S <= lat <= N:
            d = {t.k: t.v for t in tags}
            self.w.writerow([oid, round(lat, 7), round(lon, 7), repr(d)]); self.n += 1

    def node(self, n):
        if wanted(n.tags):
            self.emit(n.id, n.location.lat, n.location.lon, n.tags)

    def way(self, w):
        if not wanted(w.tags):
            return
        pts = [(nd.lat, nd.lon) for nd in w.nodes if nd.location.valid()]
        if pts:
            lat = sum(p[0] for p in pts) / len(pts); lon = sum(p[1] for p in pts) / len(pts)
            self.emit(w.id, lat, lon, w.tags)

if __name__ == "__main__":
    src, out = sys.argv[1:3]
    with open(out, "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh); wr.writerow(["osm_id", "lat", "lon", "tags"])
        h = H(wr); h.apply_file(src, locations=True)
    print("kept", h.n, "places ->", out)
