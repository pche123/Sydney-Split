"""US city: census tracts merged into study areas, and every ACS 2019-2023 table summed to them.

    python pipeline/common/us_areas.py newyork <phase1 folder> work/newyork

Reads <phase1>/<city>/census/<TABLE>_<state+county>.json (api.census.gov) and <phase1>/_us_shapes/cb_2023_<state>_tract_500k.zip.
Keeps tracts in the city's counties whose centre lies inside its box (cities.py), with at least 100 people and 1,000
people per km² (as for Japan). Tracts are merged inside each county (each borough in New York) into areas of about
max(8000, population / 400) people. Writes areas.gpkg (code, name, borough, population, km2) and census/<TABLE>.csv
(one row per area, the table's estimate columns, summed: every table used is a count).
"""
import glob, json, os, sys, zipfile
import numpy as np, pandas as pd, geopandas as gpd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.cluster import AgglomerativeClustering

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cities import CITIES


def acs(path):
    d = json.load(open(path)); df = pd.DataFrame(d[1:], columns=d[0])
    est = [c for c in df.columns if c.endswith("E") and "_" in c]
    out = df[est].apply(pd.to_numeric, errors="coerce")
    out[out < 0] = np.nan                                    # ACS uses large negative codes for "not available"
    out.index = df.state + df.county + df.tract
    return out


def main(city, raw, out):
    c = CITIES[city]; os.makedirs(f"{out}/census", exist_ok=True)
    states = sorted({k[:2] for k in c["counties"]})
    g = pd.concat([gpd.read_file(f"zip://{raw}/_us_shapes/cb_2023_{s}_tract_500k.zip") for s in states])
    g = g[(g.STATEFP + g.COUNTYFP).isin(c["counties"])].copy()
    W, S_, E, N = c["bbox"]; rp = g.representative_point()
    g = g[(rp.x >= W) & (rp.x <= E) & (rp.y >= S_) & (rp.y <= N)].to_crs(c["crs"]).reset_index(drop=True)
    g["geoid"] = g.GEOID; g["county"] = g.STATEFP + g.COUNTYFP

    tables = {}
    for f in sorted(glob.glob(f"{raw}/{city}/census/*.json")):
        t = os.path.basename(f).split("_")[0]
        tables.setdefault(t, []).append(acs(f))
    T = {t: pd.concat(v) for t, v in tables.items()}
    g["population"] = g.geoid.map(T["B01001"]["B01001_001E"]).fillna(0)
    g["km2"] = g.area / 1e6
    keep = (g.population >= 100) & (g.population / g.km2 >= 1000)
    S = g[keep].reset_index(drop=True)
    target = max(8000, S.population.sum() / 400)

    buf = gpd.GeoDataFrame(geometry=S.buffer(5), crs=S.crs)
    pr = gpd.sjoin(buf, buf, predicate="intersects"); pr = pr[pr.index < pr.index_right]
    I0, J0 = pr.index.values, pr.index_right.values
    xy = np.column_stack([S.representative_point().x, S.representative_point().y])
    lab = np.full(len(S), -1); nxt = 0
    for _, idx in S.groupby("county").indices.items():
        idx = np.array(sorted(idx)); pos = {u: k for k, u in enumerate(idx)}
        m = np.isin(I0, idx) & np.isin(J0, idx)
        A = coo_matrix((np.ones(m.sum()), ([pos[i] for i in I0[m]], [pos[j] for j in J0[m]])), shape=(len(idx), len(idx)))
        A = ((A + A.T) > 0).astype(float)
        ncomp, comp = connected_components(A, directed=False)
        for k_ in range(ncomp):
            sub = np.where(comp == k_)[0]; k = int(max(1, round(S.population.values[idx[sub]].sum() / target)))
            if k >= len(sub): l = np.arange(len(sub))
            elif k == 1: l = np.zeros(len(sub), int)
            else: l = AgglomerativeClustering(n_clusters=k, connectivity=A.tocsr()[sub][:, sub], linkage="ward").fit_predict(xy[idx[sub]])
            for u in np.unique(l): lab[idx[sub[l == u]]] = nxt; nxt += 1
    S["aid"] = lab
    S[["geoid", "aid", "county", "population"]].to_csv(f"{out}/tract_area.csv", index=False)
    A_ = S.dissolve("aid", aggfunc={"population": "sum", "county": "first"}).reset_index()
    A_["borough"] = A_.county.map(c["counties"])
    A_["code"] = A_["aid"].astype(str)
    A_["name"] = A_.borough + " " + (A_.groupby("borough").cumcount() + 1).astype(str)   # replaced by place names in build_app if available
    A_["km2"] = A_.geometry.area / 1e6
    A_["density"] = A_.population / A_.km2
    A_[["code", "name", "borough", "population", "km2", "density", "geometry"]].to_file(f"{out}/areas.gpkg", driver="GPKG")
    amap = dict(zip(S["geoid"], S["aid"]))
    write_tables(T, amap, len(A_), out)
    print(f"{c['name']}: {len(g)} tracts in box, {len(S)} kept, {len(A_)} areas, median {int(A_.population.median()):,} people, "
          f"{int(A_.population.sum()):,} people in total, {len(T)} tables")


MEDIANS = {"B25064": ("B25003", "B25003_003E")}   # median gross rent: average of tract medians weighted by renting households


def write_tables(T, amap, n, out):
    for t, d in T.items():
        d = d.loc[d.index.isin(amap)]
        if t in MEDIANS:                               # a median can't be summed
            wt, wc = MEDIANS[t]; w = T[wt].reindex(d.index)[wc]
            num = d.mul(w, axis=0).groupby(d.index.map(amap)).sum(min_count=1)
            den = d.notna().mul(w, axis=0).groupby(d.index.map(amap)).sum()
            (num / den.where(den > 0)).reindex(range(n)).to_csv(f"{out}/census/{t}.csv", index_label="area")
        else:
            d.groupby(d.index.map(amap)).sum(min_count=1).reindex(range(n)).to_csv(f"{out}/census/{t}.csv", index_label="area")


if __name__ == "__main__":
    main(*sys.argv[1:4])
