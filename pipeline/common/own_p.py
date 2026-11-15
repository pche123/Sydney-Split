"""Store each line's own p-value next to the group-corrected one, so the app can show both honestly.

    python pipeline/common/own_p.py <cities folder> melbourne [brisbane ...]

The app's `p` is Holm-corrected within a line's group, which can cap at 1 even when the line's own p is not near 1.
This adds, per line:
  p_own    the line's own p (calibrated landscape test for census/record lines; label-swap test for chain wars)
  n_group  how many lines were corrected together
  p_mixed  chain wars only: p for the opposite question, "are the two chains more mixed together than chance?"
"""
import ast, json, os, sys
import numpy as np, pandas as pd, geopandas as gpd
from scipy.spatial import cKDTree
from shapely import contains_xy

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
sys.path[:0] = [os.path.join(HERE, ".."), HERE, ROOT]
from cities import CITIES
from brands import BRANDS_BY_COUNTRY

R = 999


def chain_tests(city, W_, d):
    C = CITIES[city]; CO = C["country"]; rng = np.random.default_rng(7)
    G = gpd.read_file(f"{W_}/areas.gpkg").to_crs(C["crs"]).reset_index(drop=True)
    z = np.load(f"{W_}/fields.npz"); I, J, W = z["I"], z["J"], z["W"]
    rep = np.column_stack([G.representative_point().x, G.representative_point().y])
    P = pd.read_csv(f"{W_}/raw/osm/places.csv"); P["t"] = P.tags.map(ast.literal_eval)
    pg = gpd.GeoDataFrame(P, geometry=gpd.points_from_xy(P.lon, P.lat), crs=4326).to_crs(C["crs"])
    am = P.t.map(lambda q: q.get("amenity")); sh = P.t.map(lambda q: q.get("shop")); kind = am.where(am.notna(), sh)
    txt = P.t.map(lambda q: "|".join(str(q.get(k, "")) for k in ("brand", "name", "brand:en", "name:en", "operator")).lower())
    inmap = G.geometry.union_all().buffer(300); OFF = 50.0 if CO == "jp" else 200.0
    xy_all = np.column_stack([pg.geometry.x, pg.geometry.y])

    def pts(b):
        pat, kinds = BRANDS_BY_COUNTRY[CO][b]
        xy = xy_all[np.asarray(txt.str.contains(pat, regex=True) & kind.isin(kinds), bool)]
        return xy[contains_xy(inmap, xy[:, 0], xy[:, 1])] if len(xy) else xy

    def border(A, Bp):
        f = np.log(cKDTree(Bp).query(rep)[0] + OFF) - np.log(cKDTree(A).query(rep)[0] + OFF)
        s = f > np.median(f); return ((s[I] != s[J]) * W).sum() / (0.5 * W.sum())

    out = {}
    for l in d["lines"]:
        if l["group"] != "Chains": continue
        a, b = l["a"].replace("A ", "", 1).replace(" is closer", ""), l["b"].replace("A ", "", 1).replace(" is closer", "")
        A, Bp = pts(a), pts(b); obs = border(A, Bp); Pp = np.vstack([A, Bp]); na = len(A)
        null = np.array([border(*np.split(Pp[rng.permutation(len(Pp))], [na])) for _ in range(R)])
        out[l["id"]] = ((1 + (null <= obs).sum()) / (R + 1), (1 + (null >= obs).sum()) / (R + 1), len(A), len(Bp))
    return out


if __name__ == "__main__":
    base = sys.argv[1]
    for city in sys.argv[2:]:
        app = os.path.join(ROOT, "app", "data", f"{city}.json"); d = json.load(open(app))
        calf = os.path.join(ROOT, "results", f"calibrated_{city}.csv")
        if d["meta"].get("calibrated"):
            cal = dict(pd.read_csv(calf)[["line", "p_cal"]].values)
        else:   # not double-checked yet: the shown p comes from build_app's first pass, so repeat that exact test
            from linetests.landscape import MultiScaleNull
            from scipy.stats import norm, rankdata
            W_ = os.path.join(base, city); C = CITIES[city]
            G = gpd.read_file(f"{W_}/areas.gpkg").to_crs(C["crs"]).reset_index(drop=True); z = np.load(f"{W_}/fields.npz")
            GN = MultiScaleNull(G.geometry, z["I"], z["J"], z["W"], m=25 if len(G) < 600 else 9)
            rz = lambda v: norm.ppf((rankdata(v) - 0.5) / len(v))
            cal = {lid: GN.test(rz(f), 199, seed=11)[0] for lid, k, f in zip(z["ids"], z["kinds"], z["F"].T) if k != "chain"}
        ch = chain_tests(city, os.path.join(base, city), d)
        size = pd.Series([l["group"] for l in d["lines"]]).value_counts()
        for l in d["lines"]:
            l["n_group"] = int(size[l["group"]])
            if l["id"] in ch:
                ps, pm, na, nb = ch[l["id"]]; l["p_own"] = round(float(ps), 3); l["p_mixed"] = round(float(pm), 3)
            elif l["id"] in cal:
                l["p_own"] = round(float(cal[l["id"]]), 3)
        json.dump(d, open(app, "w"), separators=(",", ":"), ensure_ascii=False)
        print(city, " | ".join(f"{l['name']}: own {l.get('p_own')} / corrected {l['p']}" + (f" / mixed {l['p_mixed']}" if "p_mixed" in l else "")
                               for l in d["lines"]), flush=True)
