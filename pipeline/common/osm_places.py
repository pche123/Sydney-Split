"""Cut a city's shops, cafes, restaurants, bars, breweries and stations out of an OSM file.

    pip install osmium
    python pipeline/common/osm_places.py osaka kansai-latest.osm.pbf places.csv

Output columns: osm_id, lat, lon, tags (a Python dict literal), the same format Sydney and Tokyo use.
The bounding box comes from pipeline/cities.py. Ways (buildings drawn as shapes) are reduced to their centre.
"""
import csv, os, sys
import osmium

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cities import CITIES

KEEP = ("amenity", "shop", "leisure", "tourism", "craft", "healthcare", "office", "club", "sport")


def wanted(tags):
    if any(k in tags for k in KEEP): return True
    return tags.get("railway") == "station" or tags.get("public_transport") == "station"


class H(osmium.SimpleHandler):
    def __init__(self, w, box):
        super().__init__(); self.w, self.box, self.n = w, box, 0

    def emit(self, oid, lat, lon, tags):
        W, S, E, N = self.box
        if W <= lon <= E and S <= lat <= N:
            self.w.writerow([oid, round(lat, 7), round(lon, 7), repr({t.k: t.v for t in tags})]); self.n += 1

    def node(self, n):
        if wanted(n.tags): self.emit(n.id, n.location.lat, n.location.lon, n.tags)

    def way(self, w):
        if not wanted(w.tags): return
        pts = [(nd.lat, nd.lon) for nd in w.nodes if nd.location.valid()]
        if pts: self.emit(w.id, sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts), w.tags)


if __name__ == "__main__":
    city, src, out = sys.argv[1:4]
    with open(out, "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh); wr.writerow(["osm_id", "lat", "lon", "tags"])
        h = H(wr, CITIES[city]["bbox"]); h.apply_file(src, locations=True)
    print("kept", h.n, "places ->", out)
